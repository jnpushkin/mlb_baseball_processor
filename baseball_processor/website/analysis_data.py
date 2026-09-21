"""Analysis libraries derived locally from the same games as the website."""

import json
from pathlib import Path

from ..utils.event_model import normalize_events
from ..utils.team_identity import display_team


def game_story(game):
    lines = game.get("linescore", {})
    a, h = lines.get("away", {}), lines.get("home", {})
    if not isinstance(a, dict) or not isinstance(h, dict):
        return None
    away, home = a.get("runs"), h.get("runs")
    if away is None or home is None:
        return None
    totals, last_leader, changes, streak, longest = [0, 0], None, 0, 0, 0
    timeline = []
    deficits = [0, 0]
    complete = True
    for inning in range(max(len(a.get("innings", [])), len(h.get("innings", [])))):
        for side, row in enumerate((a, h)):
            values = row.get("innings", [])
            if inning >= len(values) or str(values[inning]).strip().lower() in {"x", "", "-"}:
                continue
            try:
                runs = int(values[inning])
            except (TypeError, ValueError):
                complete = False
                continue
            totals[side] += runs
            leader = 0 if totals[0] > totals[1] else 1 if totals[1] > totals[0] else None
            if leader is not None:
                if last_leader is not None and leader != last_leader:
                    changes += 1
                last_leader = leader
            for who in (0, 1):
                deficits[who] = max(deficits[who], totals[1 - who] - totals[who])
            streak = streak + 1 if runs == 0 else 0
            longest = max(longest, streak)
            timeline.append({"inning": inning + 1, "half": "top" if side == 0 else "bottom",
                             "runs": runs, "away": totals[0], "home": totals[1]})
    complete = complete and totals == [int(away), int(home)] and bool(timeline)
    winner = 0 if away > home else 1 if home > away else None
    return {"gameId": game["gameId"], "date": game["date"], "venue": game.get("venue", ""),
            "gameType": game.get("gameType", "regular"), "score": game.get("score", ""),
            "matchup": f"{game.get('awayTeam')} @ {game.get('homeTeam')}",
            "comeback": deficits[winner] if complete and winner is not None else None,
            "leadChanges": changes if complete else None,
            "scorelessHalves": longest if complete else None,
            "margin": abs(away - home), "runs": away + home,
            "timeline": timeline, "complete": complete}


def build_analysis_data(raw_games, games, cache_dir):
    by_id = {g["gameId"]: g for g in games}
    events, arsenals, health = [], [], []
    for raw in raw_games:
        game = by_id.get(raw.get("game_id"))
        if not game:
            continue
        normalized = normalize_events(raw)
        meta = {k: game.get(k) for k in ("gameId", "date", "gameType", "venue")}
        for event in normalized:
            events.append({**meta, **event})
        # Keep detail identities/state in sync with the cross-game index.
        for i, play in enumerate(game.get("playByPlay", [])):
            if i < len(normalized):
                play.update(normalized[i])
                play["outs"] = normalized[i]["outsBefore"]
                score = normalized[i]["scoreBefore"]
                play["score"] = f"{score[0]}-{score[1]}" if score is not None else ""
        pa = [p for p in normalized if p["isPA"]]
        health.append({**meta, "source": raw.get("source", "bref"), "plays": len(normalized),
                       "pa": len(pa), "unknown": sum(p["eventType"] == "unknown" for p in normalized),
                       "unresolved": sum(not p["batterId"] or not p["pitcherId"] for p in pa),
                       "missingBases": sum(p["basesBefore"] is None for p in pa),
                       "missingScore": sum(p["scoreBefore"] is None for p in pa)})
        sides = {p.get("player_id"): side for side in ("home", "away") for p in raw.get("pitching", {}).get(side, [])}
        for pid, row in (raw.get("pitch_data") or {}).items():
            counts = row.get("pitchTypes") or {}
            if not counts:
                continue
            total = sum(n for n in counts.values() if isinstance(n, (int, float)))
            for code, count in counts.items():
                if not isinstance(count, (int, float)) or not count:
                    continue
                arsenals.append({**meta, "playerId": pid, "name": row.get("name", pid),
                                 "team": display_team(raw.get("basic_info", {}).get(sides.get(pid, "") + "_team_code", "")),
                                 "pitchType": row.get("pitchTypeNames", {}).get(code, code),
                                 "code": code, "count": count, "classifiedPitches": total,
                                 "avgSpeed": row.get("avgSpeed"), "totalPitches": row.get("totalPitches")})
    try:
        career = json.loads((Path(cache_dir) / "career_highs.json").read_text())
    except (OSError, ValueError):
        career = {}
    career_context = {pid: {"name": row.get("name", pid), "mlbId": row.get("mlb_id"),
                            "cacheRefreshedAt": row.get("scraped_at"), "totals": row.get("career_totals_api", {})}
                      for pid, row in career.items() if isinstance(row, dict) and row.get("career_totals_api")}
    return {"playEvents": events, "gameStories": [s for g in games if (s := game_story(g))],
            "pitchArsenal": arsenals, "careerContext": career_context, "analysisHealth": health}


def build_player_journeys(data, sibling_file=None):
    """Join published sibling appearances by mapped IDs; never by name alone."""
    path = Path(sibling_file or Path.home() / "ncaa_baseball_processor/web/public/data/site-data.json")
    try:
        sibling = json.loads(path.read_text())
    except (OSError, ValueError):
        return {"players": [], "available": False}
    mlb_ids = {p["playerId"] for key in ("playerGames", "pitcherGames") for p in data.get(key, [])}
    cross = data.get("ncaaCrossRef", {})
    resolved = {}
    for pid in mlb_ids:
        entry = cross.get(pid)
        if entry:
            for alias, candidate in cross.items():
                if candidate is entry or candidate.get("mlb_bref_id") == pid:
                    resolved[alias] = pid
    players, seen = {}, set()
    metadata = {g["game_id"]: g for g in sibling.get("unifiedGameLog", [])}
    for key in ("batterGames", "pitcherGames"):
        for row in sibling.get(key, []):
            pid = resolved.get(row.get("bref_id"))
            gid = row.get("game_id")
            if not pid or not gid or (pid, gid) in seen:
                continue
            seen.add((pid, gid))
            entry = players.setdefault(pid, {"playerId": pid, "name": row.get("Name", pid), "appearances": []})
            g = metadata.get(gid, {})
            entry["appearances"].append({"gameId": gid, "date": row.get("date", ""), "level": row.get("level", "Unknown"),
                                         "team": row.get("team", ""), "opponent": row.get("opponent", ""),
                                         "venue": g.get("venue", ""), "websiteUrl": cross.get(pid, {}).get("website_url", "")})
    for key in ("playerGames", "pitcherGames"):
        for row in data.get(key, []):
            pid, gid = row["playerId"], row["gameId"]
            if pid not in players or (pid, gid) in seen:
                continue
            seen.add((pid, gid))
            players[pid]["appearances"].append({"gameId": gid, "date": row["date"], "level": "MLB",
                                               "team": row.get("team", ""), "opponent": row.get("opponent", ""),
                                               "gameType": row.get("gameType", "regular")})
    return {"players": list(players.values()), "available": True,
            "generatedAt": data.get("ncaaCrossRefMeta", {}).get("generatedAt", ""),
            "source": "Published NCAA/minor-league appearance archive"}
