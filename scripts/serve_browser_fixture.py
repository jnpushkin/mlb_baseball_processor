"""Synthetic browser regression site; contains no personal archive or live API writes."""

import sys
from functools import partial
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from baseball_processor.website.bundle import build_site

root = Path(__file__).resolve().parents[1] / ".browser-fixture"
games = []
rows = []
for index, year in enumerate((2026, 2025, 2024)):
    gid = f"TEST{year}"
    games.append(
        {
            "gameId": gid,
            "date": f"09/14/{year}",
            "gameType": "regular",
            "homeTeam": "BAL",
            "awayTeam": "SF",
            "venue": "Oriole Park at Camden Yards",
            "source": "mlb",
            "score": "SF 5 - 4 BAL",
            "attendance": 30000,
            "gameLength": "2:39",
            "firstSeenPlayerIds": ["jose"] if index == 0 else [],
            "playByPlay": [],
            "pitchData": {},
            "hitData": [],
            "lineups": {},
            "linescore": {},
            "keyPlays": [],
            "decisions": {},
        }
    )
    rows.append(
        {
            "gameId": gid,
            "date": f"09/14/{year}",
            "dateSort": f"{year}-09-14",
            "gameType": "regular",
            "playerId": "jose",
            "name": "José Ramírez",
            "team": "SF",
            "opponent": "BAL",
            "pa": 4,
            "ab": 4,
            "h": 3,
            "hr": 1,
            "r": 1,
            "rbi": 2,
            "sb": 0,
            "cs": 0,
            "bb": 0,
            "so": 0,
            "doubles": 0,
            "triples": 0,
            "hbp": 0,
            "gidp": 0,
        }
    )
data = {
    "games": games,
    "generatedAt": "Test fixture",
    "players": [{"playerId": "jose", "name": "José Ramírez", "team": "SF", "games": 3, "hr": 3}],
    "pitchers": [],
    "playerGames": rows,
    "pitcherGames": [],
    "playersWithoutStats": [],
    "teams": [{"team": "SF", "games": 3}, {"team": "BAL", "games": 3}],
    "stadiums": [],
    "stadiumAliases": {},
    "companionData": {"companions": {}, "gameCompanions": {}},
    "divisionChecklist": {},
    "debuts": [],
    "finalGames": [],
    "milestones": [],
    "allMilestones": [],
    "careerFirsts": [],
    "careerLasts": [],
    "careerFirstsByGame": {},
    "careerFirstsByPlayer": {},
    "allTimePassings": [],
    "allTimePassingsByGame": {},
    "awardChecklists": {"metadata": {"available": True}, "groups": [], "completionSets": []},
    "allStarChecklists": {},
    "firstRoundDraftPicks": {},
    "playerBios": {},
    "umpireLog": [],
    "jerseyLog": {},
    "ncaaCrossRef": {},
}
build_site(data, root / "index.html")
if "--build-only" not in sys.argv:
    ThreadingHTTPServer(("127.0.0.1", 8769), partial(SimpleHTTPRequestHandler, directory=str(root))).serve_forever()
