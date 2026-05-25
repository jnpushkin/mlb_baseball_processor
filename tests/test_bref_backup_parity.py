import csv
import json
import tempfile
import unittest
from pathlib import Path

from baseball_processor.reports.bref_backup_parity import (
    _compare_metadata,
    clear_issues_csv,
    find_bref_html_for_game,
    load_api_cache_games,
    write_issues_csv,
)
from baseball_processor.scrapers.download_bref import expected_html_filename


class BrefBackupParityTests(unittest.TestCase):
    def test_find_bref_html_uses_expected_backup_filename(self):
        game = {
            "basic_info": {
                "away_team_code": "CWS",
                "home_team_code": "SF",
                "date_yyyymmdd": "20260522",
            }
        }

        with tempfile.TemporaryDirectory() as tmpdir:
            html_dir = Path(tmpdir)
            expected = html_dir / expected_html_filename("CWS", "SF", "20260522")
            expected.write_text("<html></html>", encoding="utf-8")

            self.assertEqual(expected, find_bref_html_for_game(game, html_dir))

    def test_load_api_cache_games_keeps_only_api_regular_games(self):
        api_game = {
            "game_id": "SFN202605220",
            "source": "mlb",
            "basic_info": {"source": "mlb", "game_type": "regular", "date_yyyymmdd": "20260522"},
        }
        bref_game = {
            "game_id": "SFN202605210",
            "source": "bref",
            "basic_info": {"source": "bref", "game_type": "regular", "date_yyyymmdd": "20260521"},
        }
        spring_game = {
            "game_id": "ARI202502210",
            "source": "mlb",
            "basic_info": {"source": "mlb", "game_type": "spring", "date_yyyymmdd": "20250221"},
        }

        with tempfile.TemporaryDirectory() as tmpdir:
            cache_dir = Path(tmpdir)
            (cache_dir / "api.json").write_text(json.dumps(api_game), encoding="utf-8")
            (cache_dir / "bref.json").write_text(json.dumps(bref_game), encoding="utf-8")
            (cache_dir / "spring.json").write_text(json.dumps(spring_game), encoding="utf-8")

            records = load_api_cache_games(cache_dir, recent_days=None)

        self.assertEqual(1, len(records))
        self.assertEqual("SFN202605220", records[0][1]["game_id"])

    def test_compare_metadata_reports_score_mismatch(self):
        api_game = {
            "game_id": "SFN202605220",
            "basic_info": {
                "date_yyyymmdd": "20260522",
                "away_team_code": "CWS",
                "home_team_code": "SF",
                "away_score_value": 9,
                "home_score_value": 4,
                "venue": "Oracle Park",
                "game_type": "regular",
            },
        }
        bref_game = {
            "basic_info": {
                "date_yyyymmdd": "20260522",
                "away_team_code": "CWS",
                "home_team_code": "SF",
                "away_score_value": 8,
                "home_score_value": 4,
                "venue": "Oracle Park",
                "game_type": "regular",
            },
        }

        issues = _compare_metadata(api_game, bref_game, Path("api.json"), Path("backup.html"))

        self.assertEqual(1, len(issues))
        self.assertEqual("away_score_value", issues[0]["field"])

    def test_write_issues_csv_writes_report_rows(self):
        issue = {
            "kind": "metadata_mismatch",
            "game_id": "SFN202605220",
            "field": "away_score_value",
            "side": "",
            "player": "",
            "api_source": "mlb",
            "other_source": "bref_html",
            "api_value": 9,
            "other_value": 8,
            "api_file": "api.json",
            "other_file": "backup.html",
            "message": "Score mismatch",
        }

        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "report.csv"
            write_issues_csv([issue], output_path)
            with output_path.open(encoding="utf-8") as handle:
                rows = list(csv.DictReader(handle))

        self.assertEqual(1, len(rows))
        self.assertEqual("SFN202605220", rows[0]["game_id"])
        self.assertEqual("Score mismatch", rows[0]["message"])

    def test_clear_issues_csv_removes_stale_report(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "report.csv"
            output_path.write_text("stale", encoding="utf-8")

            clear_issues_csv(output_path)

            self.assertFalse(output_path.exists())


if __name__ == "__main__":
    unittest.main()
