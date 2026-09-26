"""Synthetic browser regression site; contains no personal archive or live API writes."""

import os
import sys
from functools import partial
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from baseball_processor.website.analysis_data import game_story
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
            "venue": "Alfredo Harp Helú Stadium" if year == 2024 else "Oriole Park at Camden Yards",
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
    "pitcherGames": [{"gameId":"TEST2026","date":"09/14/2026","playerId":"pitcher","name":"Test Pitcher","team":"BAL","opponent":"SF","gameType":"regular","outs":9,"so":8,"bb":0,"gameStarts":1,"isStarter":True}],
    "playersWithoutStats": [],
    "teams": [{"team": "SF", "games": 3}, {"team": "BAL", "games": 3}],
    "stadiums": [],
    "stadiumAliases": {},
    "companionData": {"companions": {}, "gameCompanions": {}},
    "divisionChecklist": {},
    "debuts": [
        {"gameId": "TEST2024", "date": "09/14/2024", "playerId": "jose", "player": "José Ramírez",
         "team": "SF", "opponent": "BAL", "position": "3B", "ab": 4, "h": 3, "hr": 1, "rbi": 2},
        {"gameId": "TEST2026", "date": "09/14/2026", "playerId": "pitcher", "player": "Test Pitcher",
         "team": "BAL", "opponent": "SF", "position": "P", "ip": "3.0", "h_p": 1, "er": 0, "bb_p": 0, "so_p": 8},
    ],
    "finalGames": [{"gameId": "TEST2025", "date": "09/14/2025", "playerId": "retired",
                    "player": "Retired Player", "team": "SF", "position": "C", "ab": 3, "h": 1}],
    "signatureHRs": [{"gameId": "TEST2026", "date": "09/14/2026", "playerId": "jose", "player": "José Ramírez",
                      "team": "SF", "opponent": "BAL", "pitcher": "Test Pitcher", "signatureNumber": "Eutaw HR #1"}],
    "summary": [
        {"record": "Most Combined Runs", "value": "9", "detail": "Both tied games finished 5–4.",
         "gameIds": "TEST2026, TEST2025", "score": "SF 5 – 4 BAL; SF 5 – 4 BAL"},
        {"record": "Biggest Comeback", "value": "4 runs", "detail": "SF recovered from a four-run deficit.", "gameIds": "TEST2026"},
        {"record": "Coldest Game", "value": "45°F", "detail": "A chilly afternoon.", "gameIds": "TEST2024"},
    ],
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
    "jerseyLog": {
        "42": [
            {"playerId": "riverma01", "name": "Mariano Rivera", "team": "NYY", "gameId": "HISTORY",
             "date": "08/22/2008", "gameType": "regular", "uniformContext": "regular"},
            {"playerId": "jose", "name": "José Ramírez", "team": "CLE", "gameId": "TRIBUTE",
             "date": "04/15/2023", "gameType": "regular", "uniformContext": "jackie-robinson-day"},
        ],
        "0": [
            {"playerId": "jose", "name": "José Ramírez", "team": "CLE", "gameId": "SPRING",
             "date": "03/01/2023", "gameType": "spring", "uniformContext": "regular"},
            {"playerId": "jose", "name": "José Ramírez", "team": "CLE", "gameId": "TEST2024",
             "date": "09/14/2024", "gameType": "regular", "uniformContext": "regular"},
        ],
    },
    "ncaaCrossRef": {},
}
events = []
for g in games:
    g["linescore"] = {"away": {"runs": 5, "innings": [3, 2]}, "home": {"runs": 4, "innings": [4, 0]}}
    event = {"id": g["gameId"]+":0", "gameId": g["gameId"], "date": g["date"], "playIndex": 0,
             "inning": 1, "half": "top", "batterId": "jose", "batter": "José Ramírez",
             "pitcherId": "pitcher", "pitcher": "Test Pitcher", "isPA": True, "isAB": True,
             "isHit": True, "isHomeRun": False, "isWalk": False, "isStrikeout": False,
             "eventType": "single", "description": "Single to CF", "basesBefore": [],
             "scoreBefore": [0, 0], "scoreDiff": 0, "outsBefore": 0, "outs": 0}
    events.append(event)
    g["playByPlay"] = [event]
data.update({
    "playEvents": events, "gameStories": [game_story(g) for g in games],
    "pitchArsenal": [{"gameId": "TEST2026", "date": "09/14/2026", "playerId": "pitcher", "name": "Test Pitcher", "code": "FF", "pitchType": "Fastball", "count": 50, "avgSpeed": 94.5, "totalPitches": 80}],
    "careerContext": {"jose": {"mlbId": 123, "cacheRefreshedAt": "2010-01-01", "totals": {"hitting": {"hits": 2}}}},
    "playerJourneys": {"available": True, "players": [{"playerId": "jose", "name": "José Ramírez", "appearances": [{"date": "09/14/2024", "gameId": "TEST2024", "level": "MLB"}]}]},
    "analysisHealth": [{"gameId": "TEST2026", "date": "09/14/2026", "source": "mlb", "pa": 1, "plays": 1, "unknown": 0, "unresolved": 0, "missingBases": 0, "missingScore": 0}],
})
build_site(data, root / "index.html")
if "--build-only" not in sys.argv:
    port = int(os.environ.get("MLB_BROWSER_TEST_PORT", "8769"))
    ThreadingHTTPServer(("127.0.0.1", port), partial(SimpleHTTPRequestHandler, directory=str(root))).serve_forever()
