import contextlib
import io
import unittest

from baseball_processor.processors.player_stats_processor import PlayerStatsProcessor


class PlayerStatsProcessorTests(unittest.TestCase):
    def test_bref_details_credit_stolen_bases_to_runner_not_plate_batter(self):
        game = {
            "game_id": "HOM202606280",
            "basic_info": {
                "date_yyyymmdd": "20260628",
                "away_team_code": "AWY",
                "home_team_code": "HOM",
                "game_type": "regular",
            },
            "batting": {
                "home": [
                    {
                        "name": "Speed Runner",
                        "player_id": "runner01",
                        "position": "CF",
                        "AB": 4,
                        "PA": 4,
                        "R": 2,
                        "H": 2,
                        "RBI": 0,
                        "BB": 0,
                        "SO": 0,
                        "Details": "2B,3\u00b7SB",
                    },
                    {
                        "name": "Plate Hitter",
                        "player_id": "hitter01",
                        "position": "SS",
                        "AB": 4,
                        "PA": 4,
                        "R": 0,
                        "H": 1,
                        "RBI": 0,
                        "BB": 0,
                        "SO": 0,
                    },
                ],
                "away": [],
            },
            "pitching": {
                "home": [{"name": "Home Pitcher", "player_id": "pitch01", "IP": "1.0"}],
                "away": [],
            },
            "play_by_play": [
                {
                    "batter": "Plate Hitter",
                    "description": "Speed Runner steals 2B.",
                }
            ],
        }

        with contextlib.redirect_stdout(io.StringIO()):
            hitters, *_ = PlayerStatsProcessor([game]).process_all_player_stats()

        by_player = {row["Player ID"]: row for row in hitters.to_dict("records")}
        self.assertEqual(3, by_player["runner01"]["SB"])
        self.assertEqual(0, by_player["hitter01"]["SB"])
        self.assertEqual(3, by_player["runner01"]["regular_SB"])

    def test_hitters_keep_plate_appearance_only_rows_but_drop_game_only_rows(self):
        game = {
            "game_id": "HOM202606290",
            "basic_info": {
                "date_yyyymmdd": "20260629",
                "away_team_code": "AWY",
                "home_team_code": "HOM",
                "game_type": "regular",
            },
            "batting": {
                "home": [
                    {
                        "name": "Pitcher Batted",
                        "player_id": "batpit01",
                        "position": "P",
                        "AB": 0,
                        "PA": 1,
                        "R": 0,
                        "H": 0,
                        "RBI": 0,
                        "BB": 0,
                        "SO": 0,
                    },
                    {
                        "name": "Game Only Pitcher",
                        "player_id": "gamepit01",
                        "position": "P",
                        "AB": 0,
                        "PA": 0,
                        "R": 0,
                        "H": 0,
                        "RBI": 0,
                        "BB": 0,
                        "SO": 0,
                    },
                    {
                        "name": "Defensive Sub",
                        "player_id": "defsub01",
                        "position": "CF",
                        "AB": 0,
                        "PA": 0,
                        "R": 0,
                        "H": 0,
                        "RBI": 0,
                        "BB": 0,
                        "SO": 0,
                    },
                ],
                "away": [],
            },
            "pitching": {
                "home": [{"name": "Home Pitcher", "player_id": "homepit01", "IP": "1.0"}],
                "away": [],
            },
        }

        with contextlib.redirect_stdout(io.StringIO()):
            hitters, *_ = PlayerStatsProcessor([game]).process_all_player_stats()

        by_player = {row["Player ID"]: row for row in hitters.to_dict("records")}
        self.assertIn("batpit01", by_player)
        self.assertEqual(1, by_player["batpit01"]["PA"])
        self.assertNotIn("gamepit01", by_player)
        self.assertNotIn("defsub01", by_player)


if __name__ == "__main__":
    unittest.main()
