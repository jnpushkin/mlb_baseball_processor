import unittest

from baseball_processor.excel.workbook_generator import (
    _api_debut_entries_from_player_bios,
    check_mlb_debuts,
)


class MlbDebutDetectionTests(unittest.TestCase):
    def test_builds_api_debut_entries_from_player_bios(self):
        games = [
            {
                "game_id": "ATH202605260",
                "basic_info": {
                    "date_yyyymmdd": "20260526",
                    "home_team_code": "ATH",
                    "away_team_code": "SEA",
                },
                "batting": {"home": [], "away": []},
                "pitching": {
                    "home": [{"name": "Gage Jump", "player_id": "jump--000gag"}],
                    "away": [],
                },
            }
        ]
        bios = {
            "jump--000gag": {
                "name": "Gage Jump",
                "debutDate": "2026-05-26",
            }
        }

        entries = _api_debut_entries_from_player_bios(games, bios)

        self.assertEqual(
            [
                {
                    "Player": "Gage Jump",
                    "PlayerID": "jump--000gag",
                    "Team": "ATH",
                    "DebutDate": "2026-05-26",
                    "DebutYear": "2026",
                    "Source": "MLB API",
                }
            ],
            entries,
        )

    def test_matches_fresh_debut_when_reference_team_is_pending(self):
        game = {
            "game_id": "ATH202605260",
            "basic_info": {
                "date_yyyymmdd": "20260526",
                "home_team": "Athletics",
                "away_team": "Seattle Mariners",
            },
            "batting": {"home": [], "away": []},
            "pitching": {
                "home": [
                    {
                        "name": "Gage Jump",
                        "player_id": "jump--000gag",
                        "IP": "5.0",
                        "H": 9,
                        "R": 4,
                        "ER": 4,
                        "BB": 1,
                        "SO": 5,
                        "decision": "L",
                    }
                ],
                "away": [],
            },
        }
        entries = [
            {
                "Player": "Gage Jump",
                "PlayerID": "jumpga01",
                "Team": "",
                "DebutDate": "2026-05-26",
                "DebutYear": "2026",
            }
        ]

        matches = check_mlb_debuts(game, entries)

        self.assertEqual(1, len(matches))
        self.assertEqual("Gage Jump", matches[0]["Player"])
        self.assertEqual("ATH", matches[0]["Team"])
        self.assertEqual("P", matches[0]["Position"])
        self.assertEqual("5.0", matches[0]["IP"])
        self.assertEqual(5, matches[0]["SO_P"])

    def test_matches_fresh_api_player_by_name_and_team_when_bref_id_is_pending(self):
        game = {
            "game_id": "SFN202605220",
            "basic_info": {
                "date_yyyymmdd": "20260522",
                "home_team": "San Francisco Giants",
                "away_team": "Chicago White Sox",
            },
            "batting": {
                "home": [
                    {
                        "name": "Victor Bericoto",
                        "player_id": "berico000vic",
                        "bref_id": "berico000vic",
                        "position": "RF",
                        "AB": 1,
                        "PA": 1,
                        "H": 0,
                        "R": 0,
                        "RBI": 0,
                        "HR": 0,
                        "2B": 0,
                        "3B": 0,
                        "BB": 0,
                        "SO": 1,
                    }
                ],
                "away": [],
            },
            "pitching": {"home": [], "away": []},
        }
        entries = [
            {
                "Player": "Victor Bericoto",
                "PlayerID": "bericvi01",
                "Team": "SFG",
                "DebutDate": "2026-05-22",
                "DebutYear": "2026",
            }
        ]

        matches = check_mlb_debuts(game, entries)

        self.assertEqual(1, len(matches))
        self.assertEqual("Victor Bericoto", matches[0]["Player"])
        self.assertEqual("bericvi01", matches[0]["PlayerID"])
        self.assertEqual("SF", matches[0]["Team"])
        self.assertEqual("RF", matches[0]["Position"])
        self.assertEqual(1, matches[0]["AB"])

    def test_name_fallback_still_requires_matching_team(self):
        game = {
            "game_id": "SFN202605220",
            "basic_info": {
                "date_yyyymmdd": "20260522",
                "home_team": "San Francisco Giants",
                "away_team": "Chicago White Sox",
            },
            "batting": {
                "home": [{"name": "Victor Bericoto", "player_id": "berico000vic", "AB": 1, "PA": 1}],
                "away": [],
            },
            "pitching": {"home": [], "away": []},
        }
        entries = [
            {
                "Player": "Victor Bericoto",
                "PlayerID": "bericvi01",
                "Team": "CHW",
                "DebutDate": "2026-05-22",
                "DebutYear": "2026",
            }
        ]

        self.assertEqual([], check_mlb_debuts(game, entries))


if __name__ == "__main__":
    unittest.main()
