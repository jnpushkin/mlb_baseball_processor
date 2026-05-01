import json
import unittest
from pathlib import Path

from baseball_processor.engines.milestone_engine import MilestoneEngine


class MilestoneEngineTests(unittest.TestCase):
    def test_multi_steal_games_use_batter_stolen_bases(self):
        game_data = {
            "game_id": "test-game",
            "basic_info": {
                "date_yyyymmdd": "20260430",
                "home_team": "Home",
                "away_team": "Away",
                "home_team_code": "HOM",
                "away_team_code": "AWY",
                "home_score_value": 4,
                "away_score_value": 3,
            },
            "batting": {
                "home": [
                    {
                        "player_id": "player-1",
                        "name": "Speed Runner",
                        "AB": 4,
                        "R": 1,
                        "H": 2,
                        "RBI": 0,
                        "BB": 0,
                        "SO": 0,
                        "SB": 2,
                    }
                ],
                "away": [],
            },
        }

        MilestoneEngine(game_data).process_batting_milestones()

        multi_steal_games = game_data["milestone_stats"]["multi_steal_games"]
        self.assertEqual(1, len(multi_steal_games))
        self.assertEqual("player-1", multi_steal_games[0]["player_id"])
        self.assertEqual(2, multi_steal_games[0]["sb"])

    def test_representative_cache_records_process_without_errors(self):
        cache_dir = Path(__file__).resolve().parents[1] / "cache"
        representative_files = {
            "api_regular": "SFN202604210.json",
            "legacy_bref_regular": "Boston_Red_Sox_vs_Baltimore_Orioles_Box_Score__June_24__1995___Baseball-Reference_com.json",
            "api_spring": "MBAL201003260.json",
            "pdf_spring": "Minnesota_Twins_vs_Baltimore_Orioles_Spring_Training__Friday__March_26__2010.json",
            "postseason": "2014_American_League_Division_Series__ALDS__Game_3__Baltimore_Orioles_vs_Detroit_Tigers__October_5__2014___Baseball-Reference_com.json",
        }

        for label, filename in representative_files.items():
            path = cache_dir / filename
            if not path.exists():
                self.skipTest(f"Representative cache fixture missing: {filename}")

            with self.subTest(label=label):
                with path.open("r", encoding="utf-8") as handle:
                    game_data = json.load(handle)

                result = MilestoneEngine(game_data).process()
                milestone_stats = result.get("milestone_stats", {})

                for key in MilestoneEngine.MILESTONE_KEYS:
                    self.assertIn(key, milestone_stats)
                    self.assertIsInstance(milestone_stats[key], list)


if __name__ == "__main__":
    unittest.main()
