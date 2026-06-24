import unittest

from baseball_processor.processors.defensive_lineup_tracker import DefensiveLineupTracker


class DefensiveLineupTrackerTests(unittest.TestCase):
    def _row_for(self, tracker, player_id):
        df = tracker.create_defensive_leaders_dataframe()
        rows = df[df["Player ID"] == player_id].to_dict("records")
        self.assertEqual(1, len(rows))
        return rows[0]

    def test_uses_api_row_level_fielding_errors_without_footer(self):
        tracker = DefensiveLineupTracker()
        game = {
            "batting": {
                "home": [
                    {
                        "player_id": "leeju01",
                        "name": "Jung Hoo Lee",
                        "position": "RF",
                        "PO": 4,
                        "A": 0,
                        "E": 1,
                    }
                ],
                "away": [],
            },
            "pitching": {"home": [], "away": []},
            "footer_summary": {},
        }

        tracker.process_game_defense_lineup(game)

        row = self._row_for(tracker, "leeju01")
        self.assertEqual(4, row["PO"])
        self.assertEqual(1, row["E"])
        self.assertEqual(5, row["TC"])
        self.assertEqual(0.8, row["Fielding %"])

    def test_bref_footer_matches_three_part_names_without_double_counting_row_error(self):
        tracker = DefensiveLineupTracker()
        game = {
            "batting": {
                "home": [
                    {
                        "player_id": "leeju01",
                        "name": "Jung Hoo Lee",
                        "position": "RF",
                        "PO": 4,
                        "A": 0,
                        "E": 1,
                    }
                ],
                "away": [],
            },
            "pitching": {"home": [], "away": []},
            "footer_summary": {"home": {"E": "Jung Hoo Lee (1)"}, "away": {}},
        }

        tracker.process_game_defense_lineup(game)

        row = self._row_for(tracker, "leeju01")
        self.assertEqual(1, row["E"])
        self.assertEqual(5, row["TC"])

    def test_backfills_cached_api_error_from_play_text(self):
        tracker = DefensiveLineupTracker()
        game = {
            "basic_info": {"home_team_code": "SF", "away_team_code": "ATH"},
            "linescore": {"home": {"E": 1}, "away": {"E": 0}},
            "batting": {
                "home": [
                    {
                        "player_id": "leeju01",
                        "name": "Jung Hoo Lee",
                        "position": "RF",
                        "PO": 4,
                        "A": 0,
                    }
                ],
                "away": [],
            },
            "pitching": {"home": [], "away": []},
            "footer_summary": {},
            "play_by_play": [
                {
                    "half": "top",
                    "pitching_team": "SF",
                    "description": "Colby Thomas reaches on a fielding error by right fielder Jung Hoo Lee. Colby Thomas to 2nd.",
                }
            ],
        }

        tracker.process_game_defense_lineup(game)

        row = self._row_for(tracker, "leeju01")
        self.assertEqual(1, row["E"])
        self.assertEqual(5, row["TC"])


if __name__ == "__main__":
    unittest.main()
