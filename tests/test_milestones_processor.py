import contextlib
import io
import unittest
from datetime import datetime

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

    def test_comprehensive_summary_only_prints_notable_categories(self):
        current_year = datetime.now().year
        milestone_dfs = {
            "Multi-HR Games": pd.DataFrame(
                [{"Date": f"{current_year}-04-03", "Player": "Power Bat", "Team": "HOM"}]
            ),
            "Quality Starts": pd.DataFrame(
                [{"Date": f"{current_year}-04-04", "Player": "Routine Starter", "Team": "AWY"}]
            ),
            "3+ Hit Games": pd.DataFrame(
                [{"Date": f"{current_year}-04-05", "Player": "Three Hit Bat", "Team": "HOM"}]
            ),
            "Saves": pd.DataFrame(
                [{"Date": f"{current_year}-04-06", "Player": "Routine Closer", "Team": "AWY"}]
            ),
        }

        output = io.StringIO()
        with contextlib.redirect_stdout(output):
            MilestonesProcessor([]).print_comprehensive_summary(milestone_dfs)

        text = output.getvalue()
        self.assertIn("OVERALL NOTABLE TOTALS", text)
        self.assertIn("NOTABLE EVENTS FROM", text)
        self.assertIn("Multi-HR Games: 1", text)
        self.assertIn(f"Total {current_year} notable events: 1", text)
        self.assertIn("Routine/stat-tracking categories hidden from report: 3 categories, 3 events", text)
        self.assertNotIn("Quality Starts:", text)
        self.assertNotIn("3+ Hit Games:", text)
        self.assertNotIn("Saves:", text)


if __name__ == "__main__":
    unittest.main()
