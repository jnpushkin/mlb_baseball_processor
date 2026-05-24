import unittest

from baseball_processor.excel.workbook_generator import check_mlb_debuts


class MlbDebutDetectionTests(unittest.TestCase):
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
