import unittest
import json
import tempfile
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

from baseball_processor.main import (
    _load_games_from_cache,
    _cache_game_quality_score,
    _find_api_cache_for_game_id,
    process_html_file,
    _should_deploy_to_surge,
    _should_download_bref_backups,
    _should_refresh_all_time_leaders,
    _should_update_debuts,
)


def make_args(**overrides):
    values = {
        "from_cache_only": False,
        "from_db": False,
        "quick_stats": False,
        "website_only": False,
        "skip_debut_update": False,
        "deploy": False,
        "no_deploy": False,
        "surge_domain": None,
    }
    values.update(overrides)
    return SimpleNamespace(**values)


class NetworkReferenceUpdateTests(unittest.TestCase):
    def test_cache_only_skips_network_reference_updates(self):
        args = make_args(from_cache_only=True)

        self.assertFalse(_should_refresh_all_time_leaders(args))
        self.assertFalse(_should_update_debuts(args))
        self.assertFalse(_should_download_bref_backups(args))

    def test_quick_stats_skips_network_reference_updates(self):
        args = make_args(quick_stats=True)

        self.assertFalse(_should_refresh_all_time_leaders(args))
        self.assertFalse(_should_update_debuts(args))
        self.assertFalse(_should_download_bref_backups(args))

    def test_db_only_skips_network_reference_updates(self):
        args = make_args(from_db=True)

        self.assertFalse(_should_refresh_all_time_leaders(args))
        self.assertFalse(_should_update_debuts(args))
        self.assertFalse(_should_download_bref_backups(args))

    def test_regular_runs_refresh_network_references(self):
        args = make_args()

        self.assertTrue(_should_refresh_all_time_leaders(args))
        self.assertTrue(_should_update_debuts(args))
        self.assertTrue(_should_download_bref_backups(args))

    def test_cache_loader_dedupes_game_id_aliases_and_keeps_richer_record(self):
        sparse_game = {
            "game_id": "game-1",
            "basic_info": {"game_type": "spring", "source": "pdf"},
            "batting": {"away": [], "home": []},
            "pitching": {"away": [], "home": []},
        }
        rich_game = {
            "game_id": "game-1",
            "basic_info": {"game_type": "spring", "source": "mlb"},
            "batting": {"away": [{"name": "Batter", "player_id": "p1"}], "home": []},
            "pitching": {"away": [], "home": [{"name": "Pitcher", "player_id": "p2"}]},
        }

        with tempfile.TemporaryDirectory() as tmpdir:
            cache_dir = Path(tmpdir)
            (cache_dir / "sparse.json").write_text(json.dumps(sparse_game), encoding="utf-8")
            (cache_dir / "rich.json").write_text(json.dumps(rich_game), encoding="utf-8")

            games, spring_count, duplicates_skipped = _load_games_from_cache(cache_dir)

        self.assertEqual(1, len(games))
        self.assertEqual(1, spring_count)
        self.assertEqual(1, duplicates_skipped)
        self.assertEqual("mlb", games[0]["basic_info"]["source"])
        self.assertEqual(1, len(games[0]["batting"]["away"]))

    def test_cache_loader_merges_duplicate_alias_enrichment_and_extra_rows(self):
        stats_rich_game = {
            "game_id": "game-1",
            "source": "mlb",
            "basic_info": {"game_type": "spring", "source": "mlb"},
            "batting": {
                "away": [
                    {"name": "Common Batter", "player_id": "common000bat", "AB": 2, "H": 1},
                    {"name": "Extra Batter", "player_id": "extra01", "AB": 1, "H": 1},
                ],
                "home": [],
            },
            "pitching": {"away": [], "home": []},
            "raw_plays": [
                {"inning": 1, "half": "top", "batter": "Common Batter", "description": "Common Batter singles.", "away_score": 0, "home_score": 0}
            ],
        }
        enriched_game = {
            "game_id": "game-1",
            "source": "mlb",
            "basic_info": {"game_type": "spring", "source": "mlb", "duration": "2:35"},
            "batting": {
                "away": [
                    {"name": "Common Batter", "player_id": "commonba01", "AB": 2, "H": 1, "SB": 1},
                ],
                "home": [],
            },
            "pitching": {"away": [], "home": []},
            "pitch_data": {"pitcher-1": {"totalPitches": 10}},
            "lineups": {"away": [{"name": "Common Batter"}], "home": []},
            "pitcher_decisions": {"winning_pitcher": "Pitcher One"},
            "umpires": {"HP": "Umpire One"},
        }

        with tempfile.TemporaryDirectory() as tmpdir:
            cache_dir = Path(tmpdir)
            (cache_dir / "stats.json").write_text(json.dumps(stats_rich_game), encoding="utf-8")
            (cache_dir / "enriched.json").write_text(json.dumps(enriched_game), encoding="utf-8")

            games, _, duplicates_skipped = _load_games_from_cache(cache_dir)

        self.assertEqual(1, duplicates_skipped)
        game = games[0]
        self.assertEqual("2:35", game["basic_info"]["duration"])
        self.assertEqual({"pitcher-1": {"totalPitches": 10}}, game["pitch_data"])
        self.assertEqual({"winning_pitcher": "Pitcher One"}, game["pitcher_decisions"])
        self.assertEqual(2, len(game["batting"]["away"]))
        common = next(player for player in game["batting"]["away"] if player["name"] == "Common Batter")
        self.assertEqual("commonba01", common["player_id"])
        self.assertEqual(1, common["SB"])

    def test_cache_loader_skips_zero_pa_batting_placeholders_when_merging(self):
        api_game = {
            "game_id": "game-1",
            "source": "mlb",
            "basic_info": {"game_type": "regular", "source": "mlb"},
            "batting": {"away": [{"name": "Real Batter", "player_id": "b1", "AB": 4, "H": 1}], "home": []},
            "pitching": {"away": [{"name": "Pitcher", "player_id": "p1"}], "home": []},
        }
        bref_game = {
            "game_id": "game-1",
            "source": "bref",
            "basic_info": {"game_type": "regular", "source": "bref"},
            "batting": {
                "away": [
                    {"name": "Real Batter", "player_id": "b1", "AB": 4, "H": 1},
                    {"name": "Pitcher", "player_id": "p1", "position": "P", "AB": 0, "H": 0},
                ],
                "home": [],
            },
            "pitching": {"away": [{"name": "Pitcher", "player_id": "p1"}], "home": []},
            "footer_summary": {"away": {"HR": "Real Batter (1)"}, "home": {}},
            "milestone_stats": {"win_games": [{"player": "Pitcher"}]},
        }

        with tempfile.TemporaryDirectory() as tmpdir:
            cache_dir = Path(tmpdir)
            (cache_dir / "api.json").write_text(json.dumps(api_game), encoding="utf-8")
            (cache_dir / "bref.json").write_text(json.dumps(bref_game), encoding="utf-8")

            games, _, duplicates_skipped = _load_games_from_cache(cache_dir)

        self.assertEqual(1, duplicates_skipped)
        game = games[0]
        self.assertEqual(1, len(game["batting"]["away"]))
        self.assertEqual({"away": {"HR": "Real Batter (1)"}, "home": {}}, game["footer_summary"])
        self.assertEqual([{"player": "Pitcher"}], game["milestone_stats"]["win_games"])

    def test_cache_loader_merges_unique_play_events_without_duplicate_noise(self):
        api_game = {
            "game_id": "game-1",
            "source": "mlb",
            "basic_info": {"game_type": "spring", "source": "mlb"},
            "batting": {"away": [{"name": "Batter One", "player_id": "b1", "AB": 1}], "home": []},
            "pitching": {"away": [], "home": []},
            "raw_plays": [
                {"inning": 1, "half": "top", "batter": "Batter One", "description": "Batter One grounds out.", "away_score": 0, "home_score": 0},
            ],
        }
        pdf_game = {
            "game_id": "game-1",
            "source": "pdf",
            "basic_info": {"game_type": "spring", "source": "pdf"},
            "batting": {"away": [], "home": []},
            "pitching": {"away": [], "home": []},
            "raw_plays": [
                {"inning": 1, "half": "top", "batter": "Batter One", "description": "Batter One grounds out. 1 out", "away_score": 0, "home_score": 0},
                {"inning": 1, "half": "top", "batter": "Batter Two", "description": "Batter Two singles.", "away_score": 0, "home_score": 0},
            ],
        }

        with tempfile.TemporaryDirectory() as tmpdir:
            cache_dir = Path(tmpdir)
            (cache_dir / "api.json").write_text(json.dumps(api_game), encoding="utf-8")
            (cache_dir / "pdf.json").write_text(json.dumps(pdf_game), encoding="utf-8")

            games, _, duplicates_skipped = _load_games_from_cache(cache_dir)

        self.assertEqual(1, duplicates_skipped)
        self.assertEqual(2, len(games[0]["raw_plays"]))
        self.assertEqual("Batter Two", games[0]["raw_plays"][1]["batter"])

    def test_cache_loader_ignores_zero_pa_pitcher_batting_placeholders_for_quality(self):
        bref_game = {
            "game_id": "game-1",
            "source": "bref",
            "basic_info": {"game_type": "regular", "source": "bref"},
            "batting": {
                "away": [
                    {"name": "Real Batter", "player_id": "b1", "AB": 4, "H": 1},
                    {"name": "Pitcher Placeholder", "player_id": "p1", "position": "P", "AB": 0, "H": 0},
                ],
                "home": [],
            },
            "pitching": {"away": [{"name": "Pitcher Placeholder", "player_id": "p1"}], "home": []},
            "footer_summary": {"away": {"HR": "Real Batter (1)"}, "home": {}},
            "milestone_stats": {"win_games": [{"player": "Pitcher Placeholder"}]},
        }
        api_game = {
            "game_id": "game-1",
            "source": "mlb",
            "basic_info": {"game_type": "regular", "source": "mlb"},
            "batting": {
                "away": [
                    {"name": "Real Batter", "player_id": "b1", "PA": 4, "AB": 4, "H": 1, "HR": 1},
                ],
                "home": [],
            },
            "pitching": {"away": [{"name": "Pitcher Placeholder", "player_id": "p1"}], "home": []},
        }

        self.assertGreater(_cache_game_quality_score(api_game), _cache_game_quality_score(bref_game))

        with tempfile.TemporaryDirectory() as tmpdir:
            cache_dir = Path(tmpdir)
            (cache_dir / "bref.json").write_text(json.dumps(bref_game), encoding="utf-8")
            (cache_dir / "api.json").write_text(json.dumps(api_game), encoding="utf-8")

            games, _, duplicates_skipped = _load_games_from_cache(cache_dir)

        self.assertEqual(1, duplicates_skipped)
        self.assertEqual("mlb", games[0]["source"])

    def test_find_api_cache_by_internal_game_id_not_filename(self):
        api_game = {
            "game_id": "LAN202502200",
            "source": "mlb",
            "basic_info": {"source": "mlb", "game_type": "spring"},
        }
        bref_game = {
            "game_id": "LAN202502200",
            "source": "bref",
            "basic_info": {"source": "bref", "game_type": "spring"},
        }

        with tempfile.TemporaryDirectory() as tmpdir:
            cache_dir = Path(tmpdir)
            api_path = cache_dir / "MLAD202502200.json"
            bref_path = cache_dir / "Chicago_Cubs_vs_Los_Angeles_Dodgers.json"
            api_path.write_text(json.dumps(api_game), encoding="utf-8")
            bref_path.write_text(json.dumps(bref_game), encoding="utf-8")

            found_path, found_game = _find_api_cache_for_game_id(
                "LAN202502200",
                cache_dir,
                exclude_path=bref_path,
            )

        self.assertEqual(api_path, found_path)
        self.assertEqual(api_game, found_game)

    def test_process_html_file_uses_api_cache_without_writing_html_cache_alias(self):
        api_game = {
            "game_id": "LAN202502200",
            "source": "mlb",
            "basic_info": {
                "source": "mlb",
                "game_type": "spring",
                "away_team": "Chicago Cubs",
                "home_team": "Los Angeles Dodgers",
                "away_score": 0,
                "home_score": 0,
            },
            "batting": {"away": [], "home": []},
            "pitching": {"away": [], "home": []},
            "milestone_stats": {"already_processed": [{"player": "Existing"}]},
        }
        bref_game = {
            "game_id": "LAN202502200",
            "source": "bref",
            "basic_info": {"source": "bref", "game_type": "spring"},
        }

        with tempfile.TemporaryDirectory() as tmpdir:
            tmp_path = Path(tmpdir)
            cache_dir = tmp_path / "cache"
            cache_dir.mkdir()
            html_path = tmp_path / "Chicago Cubs vs Los Angeles Dodgers.html"
            html_path.write_text("<html></html>", encoding="utf-8")
            api_path = cache_dir / "MLAD202502200.json"
            api_path.write_text(json.dumps(api_game), encoding="utf-8")

            with patch("baseball_processor.main.CACHE_DIR", cache_dir), patch(
                "baseball_processor.main.parse_baseball_reference_boxscore",
                return_value=bref_game,
            ):
                result = process_html_file(str(html_path))

            html_cache_path = cache_dir / "Chicago_Cubs_vs_Los_Angeles_Dodgers.json"

        self.assertEqual(api_game, result)
        self.assertFalse(html_cache_path.exists())

    def test_auto_deploys_when_domain_is_configured(self):
        args = make_args()

        self.assertTrue(_should_deploy_to_surge(args, "mlb-processor.surge.sh"))

    def test_no_deploy_overrides_configured_domain_and_explicit_deploy(self):
        args = make_args(deploy=True, no_deploy=True)

        self.assertFalse(_should_deploy_to_surge(args, "mlb-processor.surge.sh"))

    def test_explicit_deploy_without_configured_domain_still_attempts_deploy(self):
        args = make_args(deploy=True)

        self.assertTrue(_should_deploy_to_surge(args, None))


if __name__ == "__main__":
    unittest.main()
