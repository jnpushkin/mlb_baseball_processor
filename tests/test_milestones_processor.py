import contextlib
import io
import unittest

import pandas as pd

from baseball_processor.main import _load_games_from_cache
from baseball_processor.processors.milestones_processor import MilestonesProcessor
from baseball_processor.processors.milestones_processor import integrate_practical_enhancements
from baseball_processor.utils.constants import CACHE_DIR


class MilestonesProcessorTests(unittest.TestCase):
    def test_multi_sb_enhancement_preserves_stolen_bases(self):
        milestone_dfs = {
            "Multi-SB Games": pd.DataFrame(
                [
                    {
                        "Date": "20260430",
                        "Player": "Speed Runner",
                        "Player ID": "player-1",
                        "Team": "HOM",
                        "Opponent": "AWY",
                        "GameID": "game-1",
                        "SB": 2,
                    }
                ]
            )
        }
        games = [
            {
                "game_id": "game-1",
                "basic_info": {
                    "home_team_code": "HOM",
                    "away_team_code": "AWY",
                },
                "batting": {
                    "home": [{"name": "Speed Runner", "player_id": "player-1", "SB": 2}],
                    "away": [],
                },
            }
        ]

        enhanced = integrate_practical_enhancements(milestone_dfs, games)

        self.assertEqual(2, enhanced["Multi-SB Games"].iloc[0]["SB"])

    def test_cache_backfill_preserves_multi_sb_category_count(self):
        games, _, _ = _load_games_from_cache(CACHE_DIR)
        if not games:
            self.skipTest("Cache fixtures are not available")

        with contextlib.redirect_stdout(io.StringIO()):
            milestones, *_ = MilestonesProcessor(games).process_all_milestones()

        self.assertEqual(21, len(milestones["Multi-SB Games"]))


if __name__ == "__main__":
    unittest.main()
