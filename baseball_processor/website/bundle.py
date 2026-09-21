"""Versioned, demand-loaded website data and a compiled frontend."""

import hashlib
import json
import subprocess
import tempfile
from collections import defaultdict
from datetime import datetime
from pathlib import Path

from .react_app import ReactComponents
from .templates import HTMLTemplate

SCHEMA_VERSION = 2
ROOT = Path(__file__).resolve().parents[2]
DETAIL_FIELDS = {
    "hitData",
    "playByPlay",
    "pitchData",
    "lineups",
    "substitutions",
    "absChallenges",
    "_detailPlayerGames",
    "_detailPitcherGames",
    "_detailCareerFirsts",
    "_detailPassings",
    "_detailMilestones",
}
COVERAGE_KEYS = ("pitchData", "hitData", "playByPlay", "lineups", "temperature", "attendance")


def game_coverage(game):
    coverage = {key: bool(game.get(key)) for key in COVERAGE_KEYS}
    for key, measurement in [("pitchData", "maxSpeed"), ("hitData", "maxExitVelo")]:
        rows = game.get(key) or {}
        rows = rows.values() if isinstance(rows, dict) else rows
        coverage[key] = any(
            isinstance(row, dict) and isinstance(row.get(measurement), (int, float)) and row[measurement] > 0
            for row in rows
        )
    coverage["lineups"] = any((game.get("lineups") or {}).values())
    return coverage


def encode(value):
    return json.dumps(value, ensure_ascii=False, separators=(",", ":")).encode()


def search_events(data):
    """Compact, complete event search loaded only when someone searches."""
    results = []
    for key, kind in [
        ("milestones", "milestone"),
        ("careerFirsts", "career"),
        ("careerLasts", "last"),
        ("allTimePassings", "history"),
    ]:
        rows = (data.get("allMilestones") or data.get(key, [])) if key == "milestones" else data.get(key, [])
        for row in rows:
            label = row.get("player") or row.get("player_name") or row.get("type") or "Career event"
            description = row.get("type") or row.get("milestone") or row.get("stat_name") or ""
            date = row.get("date_display") or row.get("date") or ""
            results.append(
                {
                    "type": kind,
                    "label": label,
                    "sub": f"{description} · {date}",
                    "searchText": " ".join(
                        str(row.get(k) or "") for k in ("description", "detail", "venue", "team", "opponent")
                    ),
                    "tab": "milestones",
                    "subtab": "history" if kind == "history" else "milestones",
                    "searchValue": label,
                    "gameId": row.get("gameId") or row.get("game_id"),
                }
            )
    return results


def build_site(data, output_file):
    output_file = Path(output_file)
    directory = output_file.parent
    directory.mkdir(parents=True, exist_ok=True)
    files = {}

    def write(name, content):
        (directory / name).write_bytes(content)
        files[name] = {"sha256": hashlib.sha256(content).hexdigest(), "bytes": len(content)}
        return name

    def hashed(label, value):
        content = encode(value)
        name = f"data-{label}-{hashlib.sha256(content).hexdigest()[:16]}.json"
        return write(name, content)

    players_by_game = defaultdict(set)
    totals = defaultdict(lambda: defaultdict(float))
    for key in ("playerGames", "pitcherGames"):
        for row in data.get(key, []):
            gid = row.get("gameId")
            players_by_game[gid].add(row.get("playerId"))
            fields = ("h", "r", "hr", "rbi", "sb", "bb", "ab") if key == "playerGames" else ("so", "outs")
            for stat in fields:
                totals[gid][stat] += float(row.get(stat) or 0)
    for row in data.get("playersWithoutStats", []):
        for gid in str(row.get("gameIds", "")).split(","):
            if gid.strip():
                players_by_game[gid.strip()].add(row.get("playerId"))
    # Historical caches can retain placeholder IDs in their precomputed firsts.
    # Use the same canonical identities as the header and all scope metrics.
    first_seen = {}
    seen_players = set()

    def chronology(game):
        try:
            day = datetime.strptime(game.get("date", ""), "%m/%d/%Y").strftime("%Y%m%d")
        except ValueError:
            day = str(game.get("date", "")).replace("-", "")
        return day, game["gameId"]

    for game in sorted(data.get("games", []), key=chronology):
        ids = {p for p in players_by_game[game["gameId"]] if p}
        first_seen[game["gameId"]] = sorted(ids - seen_players)
        seen_players.update(ids)
    games = []
    game_files = {}
    game_versions = {}
    for game in data.get("games", []):
        gid = game["gameId"]
        detail = {
            **game,
            "firstSeenPlayerIds": first_seen[gid],
            "_detailPlayerGames": [r for r in data.get("playerGames", []) if r.get("gameId") == gid],
            "_detailPitcherGames": [r for r in data.get("pitcherGames", []) if r.get("gameId") == gid],
            "_detailMilestones": [r for r in data.get("milestones", []) if r.get("gameId") == gid],
            "_detailCareerFirsts": data.get("careerFirstsByGame", {}).get(gid, []),
            "_detailPassings": data.get("allTimePassingsByGame", {}).get(gid, []),
        }
        game_files[gid] = hashed("game", detail)
        facts = {k: v for k, v in game.items() if not k.startswith("_") and k != "firstSeenPlayerIds"}
        facts["batting"] = detail["_detailPlayerGames"]
        facts["pitching"] = detail["_detailPitcherGames"]
        game_versions[gid] = hashlib.sha256(json.dumps(facts, sort_keys=True, ensure_ascii=False).encode()).hexdigest()[
            :16
        ]
        lean = {k: v for k, v in game.items() if k not in DETAIL_FIELDS}
        lean["firstSeenPlayerIds"] = first_seen[gid]
        lean["_companions"] = data.get("companionData", {}).get("gameCompanions", {}).get(gid, [])
        lean["_venueKey"] = data.get("stadiumAliases", {}).get(game.get("venue"), game.get("venue"))
        lean["_players"] = sorted(p for p in players_by_game[gid] if p)
        lean["_totals"] = dict(totals[gid])
        lean["_coverage"] = game_coverage(game)
        games.append(lean)
    libraries = {
        k: hashed(k, v) for k, v in data.items() if k not in ("games", "generatedAt", "homeAwayGames", "searchEvents")
    }
    libraries["searchEvents"] = hashed("searchEvents", search_events(data))
    libraries["homeAwayGames"] = hashed(
        "homeAwayGames",
        [
            {**g, "playByPlay": source.get("playByPlay", [])}
            for g, source in zip(games, data.get("games", []), strict=False)
        ],
    )
    small_keys = (
        "teams",
        "stadiums",
        "stadiumAliases",
        "gameTypeCounts",
        "divisionChecklist",
        "companionData",
        "debuts",
        "finalGames",
    )
    index = {k: data.get(k) for k in small_keys}
    fields = ("playerId", "name", "team", "games", "avg", "hr", "era", "so")
    for key in ("players", "pitchers", "playersWithoutStats"):
        index[key] = [{k: p[k] for k in fields if k in p} for p in data.get(key, [])]
    index.update(
        games=games,
        generatedAt=data.get("generatedAt"),
        __schemaVersion=SCHEMA_VERSION,
        __libraries=libraries,
        __gameFiles=game_files,
        __gameVersions=game_versions,
        __collectionSets=data.get("awardChecklists", {}).get("completionSets", []),
        __moments=(data.get("careerFirsts") or [])[-24:],
        __health={
            "games": len(games),
            "coverage": {k: sum(g["_coverage"][k] for g in games) for k in COVERAGE_KEYS},
            "unresolvedPlayers": sum(
                bool(__import__("re").search(r"\d{3}", p.get("playerId", ""))) for p in data.get("players", [])
            ),
            "sources": dict(
                (source, sum(g.get("source") == source for g in games))
                for source in sorted({g.get("source", "unknown") for g in games})
            ),
            "referenceRefreshes": {
                k: data.get(k, {}).get("metadata", {}).get("generatedAt")
                for k in ("awardChecklists", "allStarChecklists")
            },
        },
    )
    try:
        previous = json.loads((directory / "data.json").read_text())
        old_games = previous.get("__gameVersions", {})
        index["__health"]["corrections"] = [
            gid for gid, ref in game_versions.items() if gid in old_games and old_games[gid] != ref
        ]
    except (OSError, ValueError):
        index["__health"]["corrections"] = []
    index_path = hashed("index", index)
    write("data.json", encode(index))
    with tempfile.TemporaryDirectory(prefix="mlb-frontend-") as temp:
        source = Path(temp) / "app.jsx"
        source.write_text((ROOT / "frontend/runtime.js").read_text() + "\n" + ReactComponents.get_app_code())
        built = subprocess.run(
            ["node", str(ROOT / "frontend/build.mjs"), str(source), str(directory.resolve())],
            cwd=ROOT,
            check=True,
            capture_output=True,
            text=True,
        )
        assets = json.loads(built.stdout)
    for name in assets.values():
        content = (directory / name).read_bytes()
        files[name] = {"sha256": hashlib.sha256(content).hexdigest(), "bytes": len(content)}
    html = HTMLTemplate.create_compiled_page(index_path, assets)
    write(output_file.name, html.encode())
    # A versioned app shell and explicitly saved games work without a connection.
    shell = [output_file.name, index_path, *assets.values()]
    sw = (
        (ROOT / "frontend/sw.js")
        .read_text()
        .replace("__SHELL__", json.dumps(shell))
        .replace("__VERSION__", hashlib.sha256(html.encode()).hexdigest()[:16])
    )
    write("sw.js", sw.encode())
    manifest = {"schemaVersion": SCHEMA_VERSION, "index": index_path, "html": output_file.name, "files": files}
    (directory / "release.json").write_bytes(encode(manifest))
    return output_file
