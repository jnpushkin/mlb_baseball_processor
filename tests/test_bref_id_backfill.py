import json
import tempfile
import unittest
from pathlib import Path

import baseball_processor.scrapers.bref_id_backfill as bref_id_backfill


class BrefIdBackfillTests(unittest.TestCase):
    def test_collect_backfill_candidates_finds_register_ids(self):
        game = {
            "batting": {
                "away": [{"name": "Gage Jump", "player_id": "jump--000gag"}],
                "home": [{"name": "Existing Player", "player_id": "troutmi01"}],
            },
            "pitching": {
                "away": [],
                "home": [{"name": "Fresh Pitcher", "player_id": "mlb_123"}],
            },
        }

        candidates = bref_id_backfill.collect_backfill_candidates(game)

        self.assertEqual({"jump--000gag"}, candidates["Gage Jump"])
        self.assertEqual({"mlb_123"}, candidates["Fresh Pitcher"])
        self.assertNotIn("Existing Player", candidates)

    def test_collect_bio_backfill_candidates_finds_bio_keys(self):
        bios = {
            "jump--000gag": {"name": "Gage Jump"},
            "troutmi01": {"name": "Mike Trout"},
        }

        candidates = bref_id_backfill.collect_bio_backfill_candidates(bios)

        self.assertEqual({"jump--000gag"}, candidates["Gage Jump"])
        self.assertNotIn("Mike Trout", candidates)

    def test_replace_id_references_updates_values_and_keys(self):
        game = {
            "batting": {"away": [{"name": "Gage Jump", "player_id": "jump--000gag"}]},
            "hit_data": {"jump--000gag": {"player_id": "jump--000gag", "exit_velocity": 101.2}},
        }

        updated, changed = bref_id_backfill.replace_id_references(
            game,
            {"jump--000gag": "jumpga01"},
        )

        self.assertEqual(3, changed)
        self.assertEqual("jumpga01", updated["batting"]["away"][0]["player_id"])
        self.assertIn("jumpga01", updated["hit_data"])
        self.assertEqual("jumpga01", updated["hit_data"]["jumpga01"]["player_id"])

    def test_dump_json_preserving_style_keeps_compact_files_compact(self):
        dumped = bref_id_backfill.dump_json_preserving_style({"a": {"b": 1}}, '{"a": {"b": 0}}\n')

        self.assertEqual('{"a": {"b": 1}}\n', dumped)

    def test_dump_json_preserving_style_keeps_pretty_files_pretty(self):
        dumped = bref_id_backfill.dump_json_preserving_style({"a": {"b": 1}}, '{\n  "a": {}\n}\n')

        self.assertTrue(dumped.startswith('{\n  "a": {\n'))

    def test_run_backfills_cache_files_with_resolved_id(self):
        old_resolver = bref_id_backfill.resolve_bref_mlb_id_exhaustive_by_name
        bref_id_backfill.resolve_bref_mlb_id_exhaustive_by_name = lambda name, max_suffix: (
            ("jumpga01", "first_404") if name == "Gage Jump" else (None, "not_found")
        )
        try:
            with tempfile.TemporaryDirectory() as tmpdir:
                cache_dir = Path(tmpdir)
                game_path = cache_dir / "game.json"
                bio_path = cache_dir / "player_bios.json"
                firsts_dir = cache_dir / "career_firsts"
                firsts_dir.mkdir()
                firsts_path = firsts_dir / "career_firsts.json"
                game_path.write_text(
                    json.dumps({
                        "batting": {"away": [{"name": "Gage Jump", "player_id": "jump--000gag"}]},
                        "pitching": {"away": [], "home": []},
                    }),
                    encoding="utf-8",
                )
                bio_path.write_text(
                    json.dumps({"jump--000gag": {"name": "Gage Jump"}}),
                    encoding="utf-8",
                )
                firsts_path.write_text(
                    json.dumps({"jump--000gag": {"player_id": "jump--000gag"}}),
                    encoding="utf-8",
                )

                result = bref_id_backfill.run(cache_dir=cache_dir, verbose=False)

                updated = json.loads(game_path.read_text(encoding="utf-8"))
                updated_bios = json.loads(bio_path.read_text(encoding="utf-8"))
                updated_firsts = json.loads(firsts_path.read_text(encoding="utf-8"))
                self.assertEqual(1, result["resolved"])
                self.assertEqual("jumpga01", updated["batting"]["away"][0]["player_id"])
                self.assertIn("jumpga01", updated_bios)
                self.assertNotIn("jump--000gag", updated_bios)
                self.assertIn("jumpga01", updated_firsts)
                self.assertEqual("jumpga01", updated_firsts["jumpga01"]["player_id"])
        finally:
            bref_id_backfill.resolve_bref_mlb_id_exhaustive_by_name = old_resolver


if __name__ == "__main__":
    unittest.main()
