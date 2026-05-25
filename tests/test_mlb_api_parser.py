import unittest

from baseball_processor.parsers.mlb_api_parser import (
    normalize_api_batting_rows,
    parse_batting,
    parse_play_by_play,
)


class MlbApiParserTests(unittest.TestCase):
    def test_parse_batting_keeps_no_pa_baserunner_stats(self):
        box_data = {
            "teams": {
                "home": {
                    "team": {"id": 137},
                    "batters": [1, 2],
                    "players": {
                        "ID1": {
                            "person": {"id": 1, "fullName": "Speed Runner"},
                            "stats": {
                                "batting": {
                                    "gamesPlayed": 1,
                                    "plateAppearances": 0,
                                    "atBats": 0,
                                    "runs": 1,
                                    "hits": 0,
                                    "rbi": 0,
                                    "stolenBases": 2,
                                    "caughtStealing": 0,
                                }
                            },
                            "gameStatus": {"isSubstitute": True},
                            "position": {"abbreviation": "PR"},
                        },
                        "ID2": {
                            "person": {"id": 2, "fullName": "Defense Only"},
                            "stats": {
                                "batting": {
                                    "gamesPlayed": 1,
                                    "plateAppearances": 0,
                                    "atBats": 0,
                                    "runs": 0,
                                    "hits": 0,
                                    "rbi": 0,
                                    "stolenBases": 0,
                                    "caughtStealing": 0,
                                }
                            },
                            "gameStatus": {"isSubstitute": True},
                            "position": {"abbreviation": "LF"},
                        },
                    },
                }
            }
        }

        rows = parse_batting(box_data, "home", bref_id_map={1: "runner01", 2: "defens01"})

        self.assertEqual(1, len(rows))
        self.assertEqual("Speed Runner", rows[0]["name"])
        self.assertEqual(0, rows[0]["PA"])
        self.assertEqual(1, rows[0]["R"])
        self.assertEqual(2, rows[0]["SB"])

    def test_parse_play_by_play_marks_scoring_plays_for_walkoffs(self):
        feed_data = {
            "gameData": {
                "teams": {
                    "away": {"id": 145, "abbreviation": "CWS"},
                    "home": {"id": 137, "abbreviation": "SF"},
                }
            },
            "liveData": {
                "plays": {
                    "allPlays": [
                        {
                            "result": {
                                "eventType": "single",
                                "event": "Single",
                                "description": "Walkoff Batter singles on a line drive to center field. Winning Runner scores.",
                                "rbi": 1,
                                "awayScore": 4,
                                "homeScore": 5,
                            },
                            "about": {
                                "inning": 9,
                                "halfInning": "bottom",
                                "isScoringPlay": True,
                            },
                            "count": {"outs": 2},
                            "matchup": {
                                "batter": {"id": 10, "fullName": "Walkoff Batter"},
                                "pitcher": {"id": 20, "fullName": "Away Pitcher"},
                            },
                        }
                    ]
                }
            },
        }

        plays = parse_play_by_play(feed_data, bref_id_map={10: "batter01", 20: "pitch01"})

        self.assertEqual(1, len(plays))
        self.assertTrue(plays[0]["run_scored"])
        self.assertEqual("bottom", plays[0]["half"])

    def test_normalize_api_batting_rows_restores_cached_runner_only_player(self):
        game = {
            "basic_info": {"home_team_code": "MIA", "away_team_code": "BAL"},
            "source": "mlb",
            "batting": {"home": [], "away": []},
            "play_by_play": [
                {
                    "half": "bottom",
                    "batting_team": "MIA",
                    "runners": [
                        {
                            "name": "Speed Runner",
                            "player_id": "runner01",
                            "event": "Stolen Base 2B",
                            "start": "1B",
                            "end": "2B",
                            "is_out": False,
                        },
                        {
                            "name": "Speed Runner",
                            "player_id": "runner01",
                            "event": "Error",
                            "start": "3B",
                            "end": "score",
                            "is_out": False,
                        },
                    ],
                },
                {
                    "half": "bottom",
                    "batting_team": "MIA",
                    "runners": [
                        {
                            "name": "Speed Runner",
                            "player_id": "runner01",
                            "event": "Stolen Base 3B",
                            "start": "2B",
                            "end": "3B",
                            "is_out": False,
                        }
                    ],
                },
            ],
        }

        normalize_api_batting_rows(game)

        rows = game["batting"]["home"]
        self.assertEqual(1, len(rows))
        self.assertEqual("Speed Runner", rows[0]["name"])
        self.assertEqual(2, rows[0]["SB"])
        self.assertEqual(1, rows[0]["R"])

    def test_normalize_api_batting_rows_does_not_duplicate_register_aliases(self):
        game = {
            "basic_info": {"home_team_code": "ATH", "away_team_code": "CWS"},
            "source": "mlb",
            "batting": {
                "away": [
                    {
                        "name": "Munetaka Murakami",
                        "player_id": "murakmu01",
                        "bref_id": "murakmu01",
                        "register_id": "muraka000mun",
                        "AB": 5,
                        "R": 1,
                        "H": 1,
                        "RBI": 2,
                        "BB": 0,
                        "SO": 2,
                        "SB": 0,
                        "CS": 0,
                    }
                ],
                "home": [],
            },
            "play_by_play": [
                {
                    "half": "top",
                    "batting_team": "CWS",
                    "runners": [
                        {
                            "name": "Munetaka Murakami",
                            "player_id": "muraka000mun",
                            "event": "Scores",
                            "start": "3B",
                            "end": "score",
                            "is_out": False,
                        }
                    ],
                }
            ],
        }

        normalize_api_batting_rows(game)

        rows = game["batting"]["away"]
        self.assertEqual(1, len(rows))
        self.assertEqual("murakmu01", rows[0]["player_id"])
        self.assertEqual(1, rows[0]["R"])


if __name__ == "__main__":
    unittest.main()
