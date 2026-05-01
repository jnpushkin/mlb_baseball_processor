import json
import unittest
from pathlib import Path


GOLDEN_FIXTURES = {
    "api_regular": {
        "file": "SFN202604210.json",
        "source": "mlb",
        "date": "20260421",
        "away": "LAD",
        "home": "SF",
        "score": (1, 3),
        "batting_rows": {"away": 12, "home": 9},
        "pitching_rows": {"away": 2, "home": 6},
    },
    "legacy_bref_regular": {
        "file": "Boston_Red_Sox_vs_Baltimore_Orioles_Box_Score__June_24__1995___Baseball-Reference_com.json",
        "source": "bref",
        "date": "19950624",
        "away": "BOS",
        "home": "BAL",
        "score": (6, 5),
        "batting_rows": {"away": 14, "home": 16},
        "pitching_rows": {"away": 3, "home": 5},
    },
    "api_spring": {
        "file": "MBAL201003260.json",
        "source": "mlb",
        "date": "20100326",
        "away": "MIN",
        "home": "BAL",
        "score": (4, 3),
        "batting_rows": {"away": 14, "home": 16},
        "pitching_rows": {"away": 4, "home": 3},
    },
    "pdf_spring": {
        "file": "Minnesota_Twins_vs_Baltimore_Orioles_Spring_Training__Friday__March_26__2010.json",
        "source": "pdf",
        "date": "20100326",
        "away": "MIN",
        "home": "BAL",
        "score": (4, 3),
        "batting_rows": {"away": 0, "home": 0},
        "pitching_rows": {"away": 0, "home": 0},
    },
    "postseason_bref": {
        "file": "2014_American_League_Division_Series__ALDS__Game_3__Baltimore_Orioles_vs_Detroit_Tigers__October_5__2014___Baseball-Reference_com.json",
        "source": "bref",
        "date": "20141005",
        "away": "BAL",
        "home": "DET",
        "score": (2, 1),
        "batting_rows": {"away": 13, "home": 15},
        "pitching_rows": {"away": 3, "home": 2},
    },
}


class GoldenCacheFixtureTests(unittest.TestCase):
    def test_representative_cache_records_keep_expected_shape(self):
        cache_dir = Path(__file__).resolve().parents[1] / "cache"

        for label, expected in GOLDEN_FIXTURES.items():
            with self.subTest(label=label):
                path = cache_dir / expected["file"]
                if not path.exists():
                    self.skipTest(f"Golden cache fixture missing: {expected['file']}")

                with path.open("r", encoding="utf-8") as handle:
                    game = json.load(handle)
                basic = game.get("basic_info", {})

                self.assertEqual(expected["source"], game.get("source") or basic.get("source"))
                self.assertEqual(expected["date"], basic.get("date_yyyymmdd"))
                self.assertEqual(expected["away"], basic.get("away_team_code"))
                self.assertEqual(expected["home"], basic.get("home_team_code"))
                self.assertEqual(expected["score"][0], basic.get("away_score_value"))
                self.assertEqual(expected["score"][1], basic.get("home_score_value"))
                self.assertEqual(
                    expected["batting_rows"],
                    {side: len(game.get("batting", {}).get(side, [])) for side in ("away", "home")},
                )
                self.assertEqual(
                    expected["pitching_rows"],
                    {side: len(game.get("pitching", {}).get(side, [])) for side in ("away", "home")},
                )


if __name__ == "__main__":
    unittest.main()
