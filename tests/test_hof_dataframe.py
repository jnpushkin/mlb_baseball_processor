import unittest

import pandas as pd

from baseball_processor.excel.workbook_generator import create_enhanced_hof_dataframe


class HallOfFameDataFrameTests(unittest.TestCase):
    def test_enhanced_hof_dataframe_keeps_player_id_and_combines_game_ids(self):
        hof_df = pd.DataFrame([{"PlayerID": "legend01", "Name": "Legend Player", "Year": 2030}])
        hitters = pd.DataFrame(
            [
                {
                    "Player ID": "legend01",
                    "GameIDs": "HOM202604300",
                    "AB": 4,
                    "H": 2,
                    "HR": 1,
                    "RBI": 3,
                    "AVG": 0.500,
                }
            ]
        )
        pitchers = pd.DataFrame(
            [
                {
                    "Player ID": "legend01",
                    "GameIDs": "AWY202604290",
                    "IP": "1.0",
                    "W": 0,
                    "L": 0,
                    "ERA": 0.00,
                    "SO": 2,
                }
            ]
        )
        all_players = {
            "legend01": {
                "positions": {"RF", "P"},
                "teams": {"HOM", "AWY"},
            }
        }

        result = create_enhanced_hof_dataframe(hof_df, hitters, pitchers, all_players, {})

        self.assertEqual(1, len(result))
        row = result.iloc[0]
        self.assertEqual("legend01", row["Player ID"])
        self.assertEqual(2, row["Games Seen"])
        self.assertEqual("AWY202604290, HOM202604300", row["GameIDs"])
        self.assertEqual("P, RF", row["Position(s)"])


if __name__ == "__main__":
    unittest.main()
