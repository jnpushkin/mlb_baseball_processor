"""Collection goals count seen winners and verified active MLB targets."""

import csv
import json
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone

import requests

from ..utils.constants import BASE_DIR, CACHE_DIR

ROSTER_FILE = CACHE_DIR / "collection_rosters.json"
API = "https://statsapi.mlb.com/api/v1"


def read_rosters(path=ROSTER_FILE):
    try:
        return json.loads(path.read_text())
    except (OSError, ValueError):
        return {}


def refresh_rosters(path=ROSTER_FILE, force=False):
    """Refresh all 30 rosters atomically; a partial response never replaces the cache."""
    now = datetime.now(timezone.utc)
    cached = read_rosters(path)
    if not force and cached.get("checkedAt", "").startswith(now.date().isoformat()):
        return cached

    def get(endpoint, params=None):
        response = requests.get(f"{API}/{endpoint}", params=params, timeout=30)
        response.raise_for_status()
        return response.json()

    teams = get("teams", {"sportId": 1, "season": now.year})["teams"]
    if len(teams) != 30:
        raise ValueError("Expected all 30 MLB teams; keeping the previous roster snapshot")

    def roster(team):
        rows = get(f"teams/{team['id']}/roster", {"rosterType": "active", "date": now.date().isoformat()})["roster"]
        if not rows:
            raise ValueError(f"Empty roster for {team['name']}; keeping the previous snapshot")
        return [
            (
                row["person"]["id"],
                {
                    "mlbId": row["person"]["id"],
                    "name": row["person"]["fullName"],
                    "team": team["name"],
                    "teamId": team["id"],
                },
            )
            for row in rows
            if row.get("status", {}).get("code") == "A"
        ]

    with ThreadPoolExecutor(max_workers=6) as executor:
        active = dict(item for rows in executor.map(roster, teams) for item in rows)
    players = {}
    for source in sorted((BASE_DIR / "register-master" / "data").glob("people-*.csv")):
        with source.open(encoding="utf-8") as handle:
            for row in csv.DictReader(handle):
                mlb_id = row.get("key_mlbam", "")
                if not mlb_id.isdigit() or int(mlb_id) not in active:
                    continue
                for key in ("key_bbref", "key_bbref_minors"):
                    if row.get(key):
                        players[row[key]] = active[int(mlb_id)]
    if not players:
        raise ValueError("No roster IDs could be matched; keeping the previous snapshot")
    payload = {
        "checkedAt": now.isoformat(),
        "source": API,
        "players": players,
        "activePlayers": len(active),
        "mappedPlayers": len({p["mlbId"] for p in players.values()}),
    }
    path.parent.mkdir(parents=True, exist_ok=True)
    temp = path.with_suffix(".tmp")
    temp.write_text(json.dumps(payload, ensure_ascii=False))
    temp.replace(path)
    return payload


def matches(item, group_key, criteria):
    def values(key, singular=None):
        value = criteria.get(key, criteria.get(singular, []) if singular else [])
        return {str(v) for v in (value if isinstance(value, list) else [value]) if v is not None}

    if criteria.get("awardKeys") and group_key not in criteria["awardKeys"]:
        return False
    for key in ("year", "gameKey"):
        if criteria.get(key) and str(item.get(key, "")) != str(criteria[key]):
            return False
    for plural, singular in (("leagues", "league"), ("selections", "selection"), ("positions", "position")):
        allowed = values(plural, singular)
        value = item.get(singular, item.get("awardDetail", "") if singular == "selection" else "")
        if allowed and str(value) not in allowed:
            return False
    return str(item.get("position", "")) not in values("excludePositions")


def apply_collection_goals(data, snapshot=None, now=None):
    """Preserve full historical counts; attach a separate attainable denominator."""
    snapshot = read_rosters() if snapshot is None else snapshot
    now = now or datetime.now(timezone.utc)
    try:
        age = (now - datetime.fromisoformat(snapshot.get("checkedAt", ""))).total_seconds()
        fresh = 0 <= age <= 7 * 86400
    except (TypeError, ValueError):
        fresh = False
    active = snapshot.get("players", {}) if fresh else {}
    for key in ("awardChecklists", "allStarChecklists"):
        payload = data.get(key)
        if not isinstance(payload, dict):
            continue
        payload.setdefault("metadata", {}).update(rosterAsOf=snapshot.get("checkedAt", ""), rosterFresh=fresh)
        for group in payload.get("groups", []):
            for item in group.get("items", []):
                item["goalEligible"] = bool(item.get("checked") or item.get("playerId") in active)
        for collection in payload.get("completionSets", []):
            items = {}
            for group in payload.get("groups", []):
                for item in group.get("items", []):
                    if item.get("playerId") and matches(item, group.get("awardKey"), collection.get("criteria", {})):
                        identity = item.get("id") or (
                            group.get("awardKey"),
                            item["playerId"],
                            item.get("year"),
                            item.get("league"),
                        )
                        items.setdefault(identity, item)
            seen = sum(bool(item.get("checked")) for item in items.values())
            targets = [item for item in items.values() if not item.get("checked") and item["playerId"] in active]
            people = {item["playerId"]: {"playerId": item["playerId"], **active[item["playerId"]]} for item in targets}
            collection.update(
                goalTotal=seen + len(targets),
                activeMissing=len(targets),
                activeMissingPlayers=len(people),
                activeTargets=sorted(people.values(), key=lambda p: p["name"]),
                excludedMissing=len(items) - seen - len(targets),
                goalAvailable=bool(people),
            )
    return data


if __name__ == "__main__":
    snapshot = refresh_rosters(force=True)
    print(f"Checked {snapshot['activePlayers']} active MLB players; matched {snapshot['mappedPlayers']} player IDs.")
