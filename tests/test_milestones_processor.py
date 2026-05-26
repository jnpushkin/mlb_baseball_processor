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
    def test_inside_the_park_milestone_detail_includes_play_context(self):
        processor = MilestonesProcessor([])

        detail = processor._format_inside_park_hr_detail(
            {
                "inning": 9,
                "half": "bottom",
                "outs_before": 1,
                "rbi": 3,
                "pitcher": "Jordan Romano",
                "pitch_count": 1,
                "description": "Inside-the-park Home Run (Fly Ball to Deep CF-RF); C. Schmitt Scores",
            }
        )

        self.assertEqual(
            "Bottom 9, 1 out: 3-run inside-the-park HR off Jordan Romano (1st pitch) - Fly Ball to Deep CF-RF",
            detail,
        )

    def test_walkoff_milestone_detail_includes_pitcher_and_pitch_context(self):
        processor = MilestonesProcessor([])

        detail = processor._format_walkoff_detail(
            {
                "inning": 9,
                "half": "bottom",
                "play_type": "Single",
                "pitcher": "Away Closer",
                "pitch_number": 4,
                "pitch_count_at_play": "2-1",
                "description": "Winning Runner scores.",
            }
        )

        self.assertEqual(
            "Bottom 9: walk-off single off Away Closer (4th pitch, 2-1) - Winning Runner scores.",
            detail,
        )

    def test_walkoff_milestone_detail_infers_missing_play_type(self):
        processor = MilestonesProcessor([])

        detail = processor._format_walkoff_detail(
            {
                "inning": 12,
                "half": "bottom",
                "pitcher": "Justin Lawrence",
                "description": "Jesus Rodriguez singles on a line drive to right fielder Ryan O'Hearn. Heliot Ramos scores.",
            }
        )

        self.assertEqual(
            "Bottom 12: walk-off single off Justin Lawrence - Jesus Rodriguez singles on a line drive to right fielder Ryan O'Hearn. Heliot Ramos scores.",
            detail,
        )

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

        self.assertEqual(22, len(milestones["Multi-SB Games"]))

    def test_api_play_by_play_grand_slam_becomes_milestone(self):
        game = {
            "game_id": "HOM202605240",
            "basic_info": {
                "date_yyyymmdd": "20260524",
                "away_team": "Away Team",
                "home_team": "Home Team",
                "away_team_code": "AWY",
                "home_team_code": "HOM",
                "away_score_value": 5,
                "home_score_value": 8,
            },
            "linescore": {
                "away": {"innings": ["0", "0", "0", "0", "5"], "R": 5},
                "home": {"innings": ["0", "0", "0", "0", "8"], "R": 8},
            },
            "batting": {
                "home": [
                    {
                        "name": "Power Bat",
                        "player_id": "power01",
                        "AB": 4,
                        "H": 2,
                        "R": 1,
                        "RBI": 5,
                        "HR": 1,
                    }
                ],
                "away": [],
            },
            "pitching": {"home": [], "away": [{"name": "Away Pitcher", "player_id": "pitch01"}]},
            "play_by_play": [
                {
                    "inning": 5,
                    "half": "bottom",
                    "batting_team": "HOM",
                    "pitching_team": "AWY",
                    "event_type": "home_run",
                    "description": "Power Bat hits a grand slam (7) to left field. Runner A scores. Runner B scores. Runner C scores.",
                    "rbi": 4,
                    "batter": "Power Bat",
                    "batter_id": "power01",
                    "pitcher": "Away Pitcher",
                    "pitcher_id": "pitch01",
                }
            ],
            "special_events": {},
            "milestone_stats": {},
        }

        with contextlib.redirect_stdout(io.StringIO()):
            milestones, *_ = MilestonesProcessor([game]).process_all_milestones()

        grand_slams = milestones["Grand Slams"]
        self.assertEqual(1, len(grand_slams))
        row = grand_slams.iloc[0]
        self.assertEqual("Power Bat", row["Player"])
        self.assertEqual("Bottom 5", row["Inning"])
        self.assertEqual("Away Pitcher", row["Pitcher"])
        self.assertEqual(5, row["RBI"])
        self.assertEqual(1, row["HR"])

    def test_api_event_type_home_run_becomes_leadoff_hr(self):
        game = {
            "game_id": "SFN202605240",
            "source": "mlb",
            "basic_info": {
                "date_yyyymmdd": "20260524",
                "away_team": "Chicago White Sox",
                "home_team": "San Francisco Giants",
                "away_team_code": "CWS",
                "home_team_code": "SF",
                "away_score_value": 5,
                "home_score_value": 8,
            },
            "linescore": {
                "away": {"innings": ["1", "0", "0", "1", "3", "0", "0", "0", "0"], "R": 5},
                "home": {"innings": ["2", "0", "2", "0", "0", "4", "0", "0"], "R": 8},
            },
            "batting": {
                "away": [
                    {
                        "name": "Chase Meidroth",
                        "player_id": "meidrch01",
                        "AB": 5,
                        "H": 1,
                        "R": 1,
                        "RBI": 1,
                        "HR": 1,
                    }
                ],
                "home": [],
            },
            "pitching": {
                "home": [{"name": "Robbie Ray", "player_id": "rayro02"}],
                "away": [],
            },
            "play_by_play": [
                {
                    "inning": 1,
                    "half": "top",
                    "batting_team": "CWS",
                    "pitching_team": "SF",
                    "event_type": "home_run",
                    "batter": "Chase Meidroth",
                    "batter_id": "meidrch01",
                    "pitcher": "Robbie Ray",
                    "pitcher_id": "rayro02",
                    "description": "Chase Meidroth homers (4) on a fly ball to left center field.",
                    "rbi": 1,
                    "outs_before": 0,
                    "pitch_count": 8,
                    "pitch_number": 8,
                    "pitch_count_at_play": "3-2",
                    "pitch_type": "Four-Seam Fastball",
                    "pitch_speed": 93.6,
                }
            ],
            "special_events": {},
            "milestone_stats": {},
        }

        with contextlib.redirect_stdout(io.StringIO()):
            milestones, *_ = MilestonesProcessor([game]).process_all_milestones()

        leadoff_hrs = milestones["Leadoff HRs"]
        self.assertEqual(1, len(leadoff_hrs))
        row = leadoff_hrs.iloc[0]
        self.assertEqual("Chase Meidroth", row["Player"])
        self.assertEqual("CWS", row["Team"])
        self.assertEqual("SF", row["Opponent"])
        self.assertEqual(
            "Top 1st (off Robbie Ray) - 8th pitch, 3-2, Four-Seam Fastball, 93.6 mph",
            row["Detail"],
        )

    def test_cached_leadoff_hr_refreshes_pitch_context_from_play(self):
        game = {
            "game_id": "HOM202605250",
            "source": "bref",
            "basic_info": {
                "date_yyyymmdd": "20260525",
                "away_team": "Away Team",
                "home_team": "Home Team",
                "away_team_code": "AWY",
                "home_team_code": "HOM",
                "away_score_value": 1,
                "home_score_value": 4,
            },
            "linescore": {
                "away": {"innings": ["1", "0", "0", "0", "0", "0", "0", "0", "0"], "R": 1},
                "home": {"innings": ["1", "0", "0", "0", "0", "0", "3", "0"], "R": 4},
            },
            "batting": {
                "away": [{"name": "First Batter", "player_id": "first01", "AB": 4, "H": 1, "HR": 1}],
                "home": [],
            },
            "pitching": {
                "home": [{"name": "Home Pitcher", "player_id": "pitch01"}],
                "away": [],
            },
            "play_by_play": [
                {
                    "inning": 1,
                    "half": "top",
                    "batting_team": "AWY",
                    "pitching_team": "HOM",
                    "home_run": True,
                    "batter": "First Batter",
                    "batter_id": "first01",
                    "pitcher": "Home Pitcher",
                    "description": "Home Run (Fly Ball to Deep RF)",
                    "pitch_count": 3,
                }
            ],
            "special_events": {
                "leadoff_hrs": [
                    {
                        "batter": "First Batter",
                        "batter_id": "first01",
                        "team": "Away Team",
                        "team_code": "AWY",
                        "opposing_team": "Home Team",
                        "opponent_code": "HOM",
                        "half": "top",
                        "pitcher": "Home Pitcher",
                    }
                ]
            },
            "milestone_stats": {},
        }

        with contextlib.redirect_stdout(io.StringIO()):
            milestones, *_ = MilestonesProcessor([game]).process_all_milestones()

        row = milestones["Leadoff HRs"].iloc[0]
        self.assertEqual("Top 1st (off Home Pitcher) - 3rd pitch", row["Detail"])

    def test_bref_footer_multi_homer_recomputes_total_bases(self):
        game = {
            "game_id": "HOM202605240",
            "source": "bref",
            "basic_info": {
                "date_yyyymmdd": "20260524",
                "away_team": "Away Team",
                "home_team": "Home Team",
                "away_team_code": "AWY",
                "home_team_code": "HOM",
                "away_score_value": 1,
                "home_score_value": 4,
            },
            "batting": {
                "home": [
                    {
                        "name": "Power Bat",
                        "player_id": "power01",
                        "AB": 4,
                        "H": 2,
                        "R": 2,
                        "RBI": 2,
                        "HR": None,
                        "2B": None,
                        "3B": None,
                    }
                ],
                "away": [],
            },
            "pitching": {"home": [], "away": []},
            "footer_summary": {
                "home": {
                    "HR": "Power Bat 2 (2, 1 off Away Pitcher, 1st inn, 0 on, 0 outs, 1 off Away Pitcher, 3rd inn, 0 on, 0 outs).",
                    "TB": "Power Bat 8.",
                },
                "away": {},
            },
            "milestone_stats": {},
        }

        with contextlib.redirect_stdout(io.StringIO()):
            milestones, *_ = MilestonesProcessor([game]).process_all_milestones()

        self.assertEqual(1, len(milestones["Multi-HR Games"]))
        self.assertEqual(1, len(milestones["8+ Total Bases"]))
        row = milestones["8+ Total Bases"].iloc[0]
        self.assertEqual("Power Bat", row["Player"])
        self.assertEqual(2, row["HR"])
        self.assertEqual(2, row["H"])

    def test_consecutive_home_runs_include_game_context(self):
        game = {
            "game_id": "BAL200405270",
            "source": "bref",
            "basic_info": {
                "date_yyyymmdd": "20040527",
                "away_team": "New York Yankees",
                "home_team": "Baltimore Orioles",
                "away_team_code": "NYY",
                "home_team_code": "BAL",
                "away_score_value": 18,
                "home_score_value": 5,
            },
            "linescore": {
                "away": {"innings": ["0", "0", "0", "3", "0", "8", "2", "0", "5"], "R": 18},
                "home": {"innings": ["0", "0", "3", "0", "0", "0", "0", "1", "1"], "R": 5},
            },
            "raw_plays": [
                {
                    "inning": 3,
                    "half": "bottom",
                    "batting_team": "Baltimore Orioles",
                    "pitching_team": "New York Yankees",
                    "batter": "Miguel\xa0Tejada",
                    "pitcher": "Jose Contreras",
                    "outs": 2,
                    "description": "Home Run (Fly Ball to Deep LF); M. Mora Scores",
                    "score": "0-0",
                    "pitch_count": 2,
                },
                {
                    "inning": 3,
                    "half": "bottom",
                    "batting_team": "Baltimore Orioles",
                    "pitching_team": "New York Yankees",
                    "batter": "Rafael Palmeiro",
                    "pitcher": "Jose Contreras",
                    "outs": 2,
                    "description": "Home Run (Fly Ball to Deep RF)",
                    "score": "2-0",
                    "pitch_count": 4,
                },
                {
                    "inning": 3,
                    "half": "bottom",
                    "batting_team": "Baltimore Orioles",
                    "pitching_team": "New York Yankees",
                    "batter": "Javy Lopez",
                    "pitcher": "Jose Contreras",
                    "outs": 2,
                    "description": "Groundout: SS-1B",
                },
            ],
            "play_by_play": [],
            "special_events": {},
            "milestone_stats": {},
        }

        with contextlib.redirect_stdout(io.StringIO()):
            milestones, _, _, _, b2b_only_df, *_ = MilestonesProcessor([game]).process_all_milestones()

        row = b2b_only_df.iloc[0]
        expected_detail = (
            "Bottom 3, 2 outs: Miguel Tejada 2-run HR (2nd pitch), "
            "Rafael Palmeiro solo HR (4th pitch) - off Jose Contreras - BAL 0-0 -> 3-0"
        )
        self.assertEqual(expected_detail, row["Detail"])
        self.assertEqual(f"05/27/2004 vs NYY - {expected_detail}", row["Summary Detail"])
        self.assertEqual("BAL 0-0 -> 3-0", row["Score Swing"])
        self.assertEqual(expected_detail, milestones["Consecutive HR Instances"].iloc[0]["Detail"])

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
