import tempfile
import unittest
from pathlib import Path

from baseball_processor.db.database import Database


def make_game(**basic_overrides):
    basic_info = {
        "date": "04/30/2026",
        "date_yyyymmdd": "20260430",
        "away_team": "Away",
        "home_team": "Home",
        "away_team_code": "AWY",
        "home_team_code": "HOM",
        "away_score": 3,
        "home_score": 4,
        "venue": "Old Park",
        "game_type": "regular",
        "source": "bref",
    }
    basic_info.update(basic_overrides)
    return {
        "game_id": "game-1",
        "basic_info": basic_info,
        "batting": {"away": [], "home": []},
        "pitching": {"away": [], "home": []},
    }


class DatabaseTests(unittest.TestCase):
    def test_upsert_refreshes_game_metadata(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            db = Database(Path(tmpdir) / "baseball.db")

            db.upsert_game(make_game(venue="Old Park", source="bref"))
            db.upsert_game(
                make_game(
                    date="05/01/2026",
                    date_yyyymmdd="20260501",
                    venue="New Park",
                    game_type="spring",
                    source="mlb",
                    away_score=5,
                    home_score=6,
                )
            )

            with db._connect() as conn:
                row = conn.execute(
                    """
                    SELECT date, date_yyyymmdd, venue, game_type, source, away_score, home_score
                    FROM games WHERE game_id = ?
                    """,
                    ("game-1",),
                ).fetchone()

            self.assertEqual("05/01/2026", row["date"])
            self.assertEqual("20260501", row["date_yyyymmdd"])
            self.assertEqual("New Park", row["venue"])
            self.assertEqual("spring", row["game_type"])
            self.assertEqual("mlb", row["source"])
            self.assertEqual(5, row["away_score"])
            self.assertEqual(6, row["home_score"])

    def test_multiple_batters_without_player_ids_are_preserved(self):
        game = make_game()
        game["batting"]["home"] = [
            {"name": "First Missing", "AB": 1},
            {"name": "Second Missing", "AB": 1},
        ]

        with tempfile.TemporaryDirectory() as tmpdir:
            db = Database(Path(tmpdir) / "baseball.db")
            db.upsert_game(game)

            with db._connect() as conn:
                count = conn.execute("SELECT COUNT(*) FROM batting_lines").fetchone()[0]

            self.assertEqual(2, count)


if __name__ == "__main__":
    unittest.main()
