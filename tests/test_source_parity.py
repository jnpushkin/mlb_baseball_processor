import json
import tempfile
import unittest
from pathlib import Path

from baseball_processor.reports.source_parity import (
    CacheGameRecord,
    backfill_missing_source_labels,
    collect_batting_parity_issues,
    collect_metadata_parity_issues,
    collect_pitching_parity_issues,
    infer_source_label,
)


def make_record(name, game_id, source, batting=None, pitching=None, **basic_overrides):
    basic_info = {
        "date_yyyymmdd": "20260430",
        "away_team": "Away Club",
        "home_team": "Home Club",
        "away_team_code": "AWY",
        "home_team_code": "HME",
        "away_score_value": 4,
        "home_score_value": 3,
        "venue": "Example Park",
        "game_type": "regular",
    }
    basic_info.update(basic_overrides)
    if source is not None:
        basic_info["source"] = source

    game = {
        "game_id": game_id,
        "source": source,
        "basic_info": basic_info,
    }
    if batting is not None:
        game["batting"] = batting
    if pitching is not None:
        game["pitching"] = pitching

    return CacheGameRecord(cache_file=Path(name), game=game)


class SourceParityTests(unittest.TestCase):
    def test_metadata_parity_detects_mismatch_and_missing_source(self):
        api_record = make_record("api.json", "HME202604300", "mlb")
        bref_record = make_record(
            "bref.json",
            "HME202604300",
            None,
            home_score_value=5,
        )

        issues = collect_metadata_parity_issues([api_record, bref_record])

        issue_keys = {(issue["kind"], issue["field"]) for issue in issues}
        self.assertIn(("metadata_mismatch", "home_score_value"), issue_keys)
        self.assertIn(("missing_source_label", "source"), issue_keys)

    def test_metadata_parity_ignores_games_without_api_pair(self):
        first_bref = make_record("one.json", "HME202604300", "bref")
        second_bref = make_record("two.json", "HME202604300", "pdf")

        issues = collect_metadata_parity_issues([first_bref, second_bref])

        self.assertEqual([], issues)

    def test_batting_parity_detects_stat_mismatch_and_missing_field(self):
        api_record = make_record(
            "api.json",
            "HME202604300",
            "mlb",
            batting={
                "away": [
                    {
                        "name": "Player A",
                        "player_id": "player-a",
                        "team": "AWY",
                        "AB": 4,
                        "H": 2,
                        "R": 1,
                        "RBI": 1,
                        "BB": 0,
                        "SO": 1,
                        "SB": 1,
                        "2B": 1,
                        "3B": 0,
                        "HR": 0,
                    }
                ],
                "home": [],
            },
        )
        bref_record = make_record(
            "bref.json",
            "HME202604300",
            "bref",
            batting={
                "away": [
                    {
                        "name": "Player A",
                        "player_id": "player-a",
                        "team": "AWY",
                        "AB": 4,
                        "H": 1,
                        "R": 1,
                        "RBI": 1,
                        "BB": 0,
                        "SO": 1,
                        "2B": 1,
                        "3B": 0,
                        "HR": 0,
                    }
                ],
                "home": [],
            },
        )

        issues = collect_batting_parity_issues([api_record, bref_record])

        issue_keys = {(issue["kind"], issue["field"]) for issue in issues}
        self.assertIn(("batting_mismatch", "H"), issue_keys)
        self.assertIn(("missing_batting_field", "SB"), issue_keys)

    def test_pitching_parity_detects_stat_mismatch_and_missing_pitch_count(self):
        api_record = make_record(
            "api.json",
            "HME202604300",
            "mlb",
            pitching={
                "away": [
                    {
                        "name": "Pitcher A",
                        "player_id": "pitcher-a",
                        "team": "AWY",
                        "IP": "5.0",
                        "H": 4,
                        "R": 2,
                        "ER": 2,
                        "BB": 1,
                        "SO": 6,
                        "HR": 1,
                        "decision": "W",
                        "pitches": 84,
                        "strikes": 55,
                        "batters_faced": 21,
                    }
                ],
                "home": [],
            },
        )
        bref_record = make_record(
            "bref.json",
            "HME202604300",
            "bref",
            pitching={
                "away": [
                    {
                        "name": "Pitcher A",
                        "player_id": "pitcher-a",
                        "team": "AWY",
                        "IP": "5",
                        "H": 4,
                        "R": 2,
                        "ER": 1,
                        "BB": 1,
                        "SO": 6,
                        "HR": 1,
                        "decision": "W",
                        "strikes": 55,
                        "batters_faced": 21,
                    }
                ],
                "home": [],
            },
        )

        issues = collect_pitching_parity_issues([api_record, bref_record])

        issue_keys = {(issue["kind"], issue["field"]) for issue in issues}
        self.assertIn(("pitching_mismatch", "ER"), issue_keys)
        self.assertIn(("missing_pitching_field", "pitches"), issue_keys)

    def test_source_label_inference_and_backfill_for_bref_cache(self):
        record = make_record(
            "Team_vs_Team_Box_Score__April_30__2026___Baseball-Reference_com.json",
            "HME202604300",
            None,
        )

        self.assertEqual("bref", infer_source_label(record))

        with tempfile.TemporaryDirectory() as tmpdir:
            cache_file = Path(tmpdir) / record.cache_file.name
            cache_file.write_text(json.dumps(record.game), encoding="utf-8")

            dry_run = backfill_missing_source_labels(Path(tmpdir), dry_run=True)
            self.assertEqual(1, dry_run["would_update"])
            self.assertFalse(json.loads(cache_file.read_text(encoding="utf-8")).get("source"))

            applied = backfill_missing_source_labels(Path(tmpdir), dry_run=False)
            updated_game = json.loads(cache_file.read_text(encoding="utf-8"))

        self.assertEqual(1, applied["updated"])
        self.assertEqual("bref", updated_game["source"])
        self.assertEqual("bref", updated_game["basic_info"]["source"])


if __name__ == "__main__":
    unittest.main()
