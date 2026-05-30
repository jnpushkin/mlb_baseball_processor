import unittest

import baseball_processor.parsers.mlb_api_parser as mlb_api_parser
from baseball_processor.parsers.mlb_api_parser import (
    construct_bref_mlb_id_candidates,
    construct_provisional_bref_mlb_id,
    get_bref_id_by_name,
    infer_abs_challenger_type,
    normalize_api_batting_rows,
    parse_batting,
    parse_play_by_play,
    resolve_bref_mlb_id_exhaustive_by_name,
    resolve_bref_mlb_id_by_name,
)


class MlbApiParserTests(unittest.TestCase):
    def test_construct_bref_mlb_id_candidates_uses_regular_bref_shape(self):
        self.assertEqual(
            ["jumpga01", "jumpga02", "jumpga03"],
            construct_bref_mlb_id_candidates("Gage Jump", max_suffix=3),
        )
        self.assertEqual(
            ["fernajo01"],
            construct_bref_mlb_id_candidates("José Fernández", max_suffix=1),
        )

    def test_resolve_register_id_accepts_dotted_bref_ids(self):
        old_cache = mlb_api_parser._register_to_mlb_cache
        old_attempted = mlb_api_parser._register_resolution_attempted
        old_has_cloudscraper = mlb_api_parser.HAS_CLOUDSCRAPER
        old_get_with_retry = mlb_api_parser.get_with_retry
        mlb_api_parser._register_to_mlb_cache = {}
        mlb_api_parser._register_resolution_attempted = set()
        mlb_api_parser.HAS_CLOUDSCRAPER = False

        html = '<a href="/players/gl.fcgi?id=dicker.01&amp;t=b&amp;year=2012">Batting Game Log</a>'
        mlb_api_parser.get_with_retry = lambda *_args, **_kwargs: type(
            "Response",
            (),
            {"status_code": 200, "text": html},
        )()
        try:
            self.assertEqual("dicker.01", mlb_api_parser.resolve_register_id("dickra000ra"))
        finally:
            mlb_api_parser._register_to_mlb_cache = old_cache
            mlb_api_parser._register_resolution_attempted = old_attempted
            mlb_api_parser.HAS_CLOUDSCRAPER = old_has_cloudscraper
            mlb_api_parser.get_with_retry = old_get_with_retry

    def test_resolve_bref_mlb_id_by_name_validates_suffix_candidate(self):
        old_cache = mlb_api_parser._validated_mlb_bref_id_cache
        old_chadwick = mlb_api_parser._chadwick_mlb_to_bref
        old_chadwick_loaded = mlb_api_parser._chadwick_loaded
        old_fetcher = mlb_api_parser._fetch_bref_player_page
        old_page_cache = mlb_api_parser._bref_player_page_cache
        mlb_api_parser._validated_mlb_bref_id_cache = {}
        mlb_api_parser._chadwick_mlb_to_bref = {1: "jumpga01"}
        mlb_api_parser._chadwick_loaded = True
        mlb_api_parser._fetch_bref_player_page = lambda candidate_id: (
            (200, "<h1>Gage Jump</h1>") if candidate_id == "jumpga02" else (200, "<h1>Other Player</h1>")
        )
        mlb_api_parser._bref_player_page_cache = {}
        try:
            self.assertEqual("jumpga02", resolve_bref_mlb_id_by_name("Gage Jump", max_suffix=3))
        finally:
            mlb_api_parser._validated_mlb_bref_id_cache = old_cache
            mlb_api_parser._chadwick_mlb_to_bref = old_chadwick
            mlb_api_parser._chadwick_loaded = old_chadwick_loaded
            mlb_api_parser._fetch_bref_player_page = old_fetcher
            mlb_api_parser._bref_player_page_cache = old_page_cache

    def test_name_lookup_prefers_validated_mlb_bref_id_over_register_cache(self):
        old_loaded = mlb_api_parser._name_cache_loaded
        old_name_cache = mlb_api_parser._name_to_bref_cache
        old_team_cache = mlb_api_parser._name_team_to_bref_cache
        old_validated_cache = mlb_api_parser._validated_mlb_bref_id_cache
        old_chadwick = mlb_api_parser._chadwick_mlb_to_bref
        old_chadwick_loaded = mlb_api_parser._chadwick_loaded
        old_fetcher = mlb_api_parser._fetch_bref_player_page
        old_page_cache = mlb_api_parser._bref_player_page_cache
        mlb_api_parser._name_cache_loaded = True
        mlb_api_parser._name_to_bref_cache = {"gage jump": "jump--000gag"}
        mlb_api_parser._name_team_to_bref_cache = {}
        mlb_api_parser._validated_mlb_bref_id_cache = {}
        mlb_api_parser._chadwick_mlb_to_bref = {}
        mlb_api_parser._chadwick_loaded = True
        mlb_api_parser._fetch_bref_player_page = lambda candidate_id: (
            (200, "<h1>Gage Jump</h1>") if candidate_id == "jumpga01" else (404, "")
        )
        mlb_api_parser._bref_player_page_cache = {}
        try:
            self.assertEqual("jumpga01", get_bref_id_by_name("Gage Jump", mlb_id=695611))
        finally:
            mlb_api_parser._name_cache_loaded = old_loaded
            mlb_api_parser._name_to_bref_cache = old_name_cache
            mlb_api_parser._name_team_to_bref_cache = old_team_cache
            mlb_api_parser._validated_mlb_bref_id_cache = old_validated_cache
            mlb_api_parser._chadwick_mlb_to_bref = old_chadwick
            mlb_api_parser._chadwick_loaded = old_chadwick_loaded
            mlb_api_parser._fetch_bref_player_page = old_fetcher
            mlb_api_parser._bref_player_page_cache = old_page_cache

    def test_name_lookup_uses_provisional_mlb_bref_id_before_page_exists(self):
        old_loaded = mlb_api_parser._name_cache_loaded
        old_name_cache = mlb_api_parser._name_to_bref_cache
        old_team_cache = mlb_api_parser._name_team_to_bref_cache
        old_validated_cache = mlb_api_parser._validated_mlb_bref_id_cache
        old_chadwick = mlb_api_parser._chadwick_mlb_to_bref
        old_chadwick_loaded = mlb_api_parser._chadwick_loaded
        old_mlb_cache = mlb_api_parser._mlb_to_bref_cache
        old_provisional_cache = mlb_api_parser._provisional_mlb_bref_id_cache
        old_provisional = mlb_api_parser._provisional_mlb_bref_ids
        old_matcher = mlb_api_parser._bref_candidate_matches_name
        old_fetcher = mlb_api_parser._fetch_bref_player_page
        old_page_cache = mlb_api_parser._bref_player_page_cache
        mlb_api_parser._name_cache_loaded = True
        mlb_api_parser._name_to_bref_cache = {"gage jump": "jump--000gag"}
        mlb_api_parser._name_team_to_bref_cache = {}
        mlb_api_parser._validated_mlb_bref_id_cache = {}
        mlb_api_parser._chadwick_mlb_to_bref = {}
        mlb_api_parser._chadwick_loaded = True
        mlb_api_parser._mlb_to_bref_cache = {}
        mlb_api_parser._provisional_mlb_bref_id_cache = {}
        mlb_api_parser._provisional_mlb_bref_ids = set()
        mlb_api_parser._bref_candidate_matches_name = lambda _candidate_id, _name: False
        mlb_api_parser._fetch_bref_player_page = lambda candidate_id: (
            (404, "") if candidate_id == "jumpga01" else (200, "")
        )
        mlb_api_parser._bref_player_page_cache = {}
        try:
            self.assertEqual("jumpga01", get_bref_id_by_name("Gage Jump", mlb_id=695611))
            self.assertIn("jumpga01", mlb_api_parser._provisional_mlb_bref_ids)
        finally:
            mlb_api_parser._name_cache_loaded = old_loaded
            mlb_api_parser._name_to_bref_cache = old_name_cache
            mlb_api_parser._name_team_to_bref_cache = old_team_cache
            mlb_api_parser._validated_mlb_bref_id_cache = old_validated_cache
            mlb_api_parser._chadwick_mlb_to_bref = old_chadwick
            mlb_api_parser._chadwick_loaded = old_chadwick_loaded
            mlb_api_parser._mlb_to_bref_cache = old_mlb_cache
            mlb_api_parser._provisional_mlb_bref_id_cache = old_provisional_cache
            mlb_api_parser._provisional_mlb_bref_ids = old_provisional
            mlb_api_parser._bref_candidate_matches_name = old_matcher
            mlb_api_parser._fetch_bref_player_page = old_fetcher
            mlb_api_parser._bref_player_page_cache = old_page_cache

    def test_provisional_bref_id_uses_first_live_404_suffix(self):
        old_chadwick = mlb_api_parser._chadwick_mlb_to_bref
        old_chadwick_loaded = mlb_api_parser._chadwick_loaded
        old_name_cache = mlb_api_parser._name_to_bref_cache
        old_team_cache = mlb_api_parser._name_team_to_bref_cache
        old_mlb_cache = mlb_api_parser._mlb_to_bref_cache
        old_provisional_cache = mlb_api_parser._provisional_mlb_bref_id_cache
        old_provisional = mlb_api_parser._provisional_mlb_bref_ids
        old_fetcher = mlb_api_parser._fetch_bref_player_page
        mlb_api_parser._chadwick_mlb_to_bref = {}
        mlb_api_parser._chadwick_loaded = True
        mlb_api_parser._name_to_bref_cache = {}
        mlb_api_parser._name_team_to_bref_cache = {}
        mlb_api_parser._mlb_to_bref_cache = {}
        mlb_api_parser._provisional_mlb_bref_id_cache = {}
        mlb_api_parser._provisional_mlb_bref_ids = set()
        mlb_api_parser._fetch_bref_player_page = lambda candidate_id: (
            (200, "") if candidate_id == "jumpga01" else (404, "")
        )
        try:
            self.assertEqual("jumpga02", construct_provisional_bref_mlb_id("Gage Jump", max_suffix=3))
        finally:
            mlb_api_parser._chadwick_mlb_to_bref = old_chadwick
            mlb_api_parser._chadwick_loaded = old_chadwick_loaded
            mlb_api_parser._name_to_bref_cache = old_name_cache
            mlb_api_parser._name_team_to_bref_cache = old_team_cache
            mlb_api_parser._mlb_to_bref_cache = old_mlb_cache
            mlb_api_parser._provisional_mlb_bref_id_cache = old_provisional_cache
            mlb_api_parser._provisional_mlb_bref_ids = old_provisional
            mlb_api_parser._fetch_bref_player_page = old_fetcher

    def test_provisional_bref_id_falls_back_to_known_suffixes_when_live_check_is_ambiguous(self):
        old_chadwick = mlb_api_parser._chadwick_mlb_to_bref
        old_chadwick_loaded = mlb_api_parser._chadwick_loaded
        old_name_cache = mlb_api_parser._name_to_bref_cache
        old_team_cache = mlb_api_parser._name_team_to_bref_cache
        old_mlb_cache = mlb_api_parser._mlb_to_bref_cache
        old_validated_cache = mlb_api_parser._validated_mlb_bref_id_cache
        old_provisional_cache = mlb_api_parser._provisional_mlb_bref_id_cache
        old_provisional = mlb_api_parser._provisional_mlb_bref_ids
        old_fetcher = mlb_api_parser._fetch_bref_player_page
        mlb_api_parser._chadwick_mlb_to_bref = {1: "jumpga01"}
        mlb_api_parser._chadwick_loaded = True
        mlb_api_parser._name_to_bref_cache = {}
        mlb_api_parser._name_team_to_bref_cache = {}
        mlb_api_parser._mlb_to_bref_cache = {}
        mlb_api_parser._validated_mlb_bref_id_cache = {}
        mlb_api_parser._provisional_mlb_bref_id_cache = {}
        mlb_api_parser._provisional_mlb_bref_ids = set()
        mlb_api_parser._fetch_bref_player_page = lambda _candidate_id: (None, "")
        try:
            self.assertEqual("jumpga02", construct_provisional_bref_mlb_id("Gage Jump", max_suffix=3))
        finally:
            mlb_api_parser._chadwick_mlb_to_bref = old_chadwick
            mlb_api_parser._chadwick_loaded = old_chadwick_loaded
            mlb_api_parser._name_to_bref_cache = old_name_cache
            mlb_api_parser._name_team_to_bref_cache = old_team_cache
            mlb_api_parser._mlb_to_bref_cache = old_mlb_cache
            mlb_api_parser._validated_mlb_bref_id_cache = old_validated_cache
            mlb_api_parser._provisional_mlb_bref_id_cache = old_provisional_cache
            mlb_api_parser._provisional_mlb_bref_ids = old_provisional
            mlb_api_parser._fetch_bref_player_page = old_fetcher

    def test_provisional_bref_id_starts_live_check_at_known_next_suffix(self):
        old_chadwick = mlb_api_parser._chadwick_mlb_to_bref
        old_chadwick_loaded = mlb_api_parser._chadwick_loaded
        old_name_cache = mlb_api_parser._name_to_bref_cache
        old_team_cache = mlb_api_parser._name_team_to_bref_cache
        old_mlb_cache = mlb_api_parser._mlb_to_bref_cache
        old_provisional_cache = mlb_api_parser._provisional_mlb_bref_id_cache
        old_provisional = mlb_api_parser._provisional_mlb_bref_ids
        old_fetcher = mlb_api_parser._fetch_bref_player_page
        calls = []
        mlb_api_parser._chadwick_mlb_to_bref = {1: "jumpga01", 2: "jumpga02"}
        mlb_api_parser._chadwick_loaded = True
        mlb_api_parser._name_to_bref_cache = {}
        mlb_api_parser._name_team_to_bref_cache = {}
        mlb_api_parser._mlb_to_bref_cache = {}
        mlb_api_parser._provisional_mlb_bref_id_cache = {}
        mlb_api_parser._provisional_mlb_bref_ids = set()
        mlb_api_parser._fetch_bref_player_page = lambda candidate_id: calls.append(candidate_id) or (404, "")
        try:
            self.assertEqual("jumpga03", construct_provisional_bref_mlb_id("Gage Jump", max_suffix=5))
            self.assertEqual(["jumpga03"], calls)
        finally:
            mlb_api_parser._chadwick_mlb_to_bref = old_chadwick
            mlb_api_parser._chadwick_loaded = old_chadwick_loaded
            mlb_api_parser._name_to_bref_cache = old_name_cache
            mlb_api_parser._name_team_to_bref_cache = old_team_cache
            mlb_api_parser._mlb_to_bref_cache = old_mlb_cache
            mlb_api_parser._provisional_mlb_bref_id_cache = old_provisional_cache
            mlb_api_parser._provisional_mlb_bref_ids = old_provisional
            mlb_api_parser._fetch_bref_player_page = old_fetcher

    def test_provisional_bref_id_does_not_guess_after_probe_limit_hits_existing_pages(self):
        old_chadwick = mlb_api_parser._chadwick_mlb_to_bref
        old_chadwick_loaded = mlb_api_parser._chadwick_loaded
        old_name_cache = mlb_api_parser._name_to_bref_cache
        old_team_cache = mlb_api_parser._name_team_to_bref_cache
        old_mlb_cache = mlb_api_parser._mlb_to_bref_cache
        old_provisional_cache = mlb_api_parser._provisional_mlb_bref_id_cache
        old_provisional = mlb_api_parser._provisional_mlb_bref_ids
        old_fetcher = mlb_api_parser._fetch_bref_player_page
        calls = []
        mlb_api_parser._chadwick_mlb_to_bref = {}
        mlb_api_parser._chadwick_loaded = True
        mlb_api_parser._name_to_bref_cache = {}
        mlb_api_parser._name_team_to_bref_cache = {}
        mlb_api_parser._mlb_to_bref_cache = {}
        mlb_api_parser._provisional_mlb_bref_id_cache = {}
        mlb_api_parser._provisional_mlb_bref_ids = set()
        mlb_api_parser._fetch_bref_player_page = lambda candidate_id: calls.append(candidate_id) or (200, "")
        try:
            self.assertIsNone(
                construct_provisional_bref_mlb_id("Gage Jump", max_suffix=5, live_probe_limit=2)
            )
            self.assertEqual(["jumpga01", "jumpga02"], calls)
        finally:
            mlb_api_parser._chadwick_mlb_to_bref = old_chadwick
            mlb_api_parser._chadwick_loaded = old_chadwick_loaded
            mlb_api_parser._name_to_bref_cache = old_name_cache
            mlb_api_parser._name_team_to_bref_cache = old_team_cache
            mlb_api_parser._mlb_to_bref_cache = old_mlb_cache
            mlb_api_parser._provisional_mlb_bref_id_cache = old_provisional_cache
            mlb_api_parser._provisional_mlb_bref_ids = old_provisional
            mlb_api_parser._fetch_bref_player_page = old_fetcher

    def test_exhaustive_bref_id_walk_continues_until_first_404(self):
        old_chadwick = mlb_api_parser._chadwick_mlb_to_bref
        old_chadwick_loaded = mlb_api_parser._chadwick_loaded
        old_name_cache = mlb_api_parser._name_to_bref_cache
        old_team_cache = mlb_api_parser._name_team_to_bref_cache
        old_mlb_cache = mlb_api_parser._mlb_to_bref_cache
        old_validated_cache = mlb_api_parser._validated_mlb_bref_id_cache
        old_provisional_cache = mlb_api_parser._provisional_mlb_bref_id_cache
        old_provisional = mlb_api_parser._provisional_mlb_bref_ids
        old_fetcher = mlb_api_parser._fetch_bref_player_page
        calls = []
        mlb_api_parser._chadwick_mlb_to_bref = {}
        mlb_api_parser._chadwick_loaded = True
        mlb_api_parser._name_to_bref_cache = {}
        mlb_api_parser._name_team_to_bref_cache = {}
        mlb_api_parser._mlb_to_bref_cache = {}
        mlb_api_parser._validated_mlb_bref_id_cache = {}
        mlb_api_parser._provisional_mlb_bref_id_cache = {}
        mlb_api_parser._provisional_mlb_bref_ids = set()

        def fake_fetch(candidate_id):
            calls.append(candidate_id)
            if candidate_id in {"jumpga01", "jumpga02", "jumpga03"}:
                return 200, "<h1>Other Player</h1>"
            return 404, ""

        mlb_api_parser._fetch_bref_player_page = fake_fetch
        try:
            self.assertEqual(
                ("jumpga04", "first_404"),
                resolve_bref_mlb_id_exhaustive_by_name("Gage Jump", max_suffix=5),
            )
            self.assertIn("jumpga04", mlb_api_parser._provisional_mlb_bref_ids)
            self.assertEqual("jumpga04", calls[-1])
        finally:
            mlb_api_parser._chadwick_mlb_to_bref = old_chadwick
            mlb_api_parser._chadwick_loaded = old_chadwick_loaded
            mlb_api_parser._name_to_bref_cache = old_name_cache
            mlb_api_parser._name_team_to_bref_cache = old_team_cache
            mlb_api_parser._mlb_to_bref_cache = old_mlb_cache
            mlb_api_parser._validated_mlb_bref_id_cache = old_validated_cache
            mlb_api_parser._provisional_mlb_bref_id_cache = old_provisional_cache
            mlb_api_parser._provisional_mlb_bref_ids = old_provisional
            mlb_api_parser._fetch_bref_player_page = old_fetcher

    def test_infer_abs_challenger_type_from_review_player(self):
        matchup = {
            "batter": {"id": 10, "fullName": "Casey Schmitt"},
            "pitcher": {"id": 20, "fullName": "Grant Taylor"},
        }

        self.assertEqual(
            "batter",
            infer_abs_challenger_type(matchup, {"player": {"id": 10, "fullName": "Casey Schmitt"}}),
        )
        self.assertEqual(
            "pitcher",
            infer_abs_challenger_type(matchup, {"player": {"fullName": "Grant Taylor"}}),
        )
        self.assertEqual(
            "catcher",
            infer_abs_challenger_type(matchup, {"player": {"id": 30, "fullName": "Edgar Quero"}}),
        )

    def test_parse_batting_keeps_no_pa_baserunner_stats(self):
        box_data = {
            "teams": {
                "home": {
                    "team": {"id": 137},
                    "batters": [1, 2],
                    "players": {
                        "ID1": {
                            "person": {"id": 1, "fullName": "Speed Runner"},
                            "stats": {
                                "batting": {
                                    "gamesPlayed": 1,
                                    "plateAppearances": 0,
                                    "atBats": 0,
                                    "runs": 1,
                                    "hits": 0,
                                    "rbi": 0,
                                    "stolenBases": 2,
                                    "caughtStealing": 0,
                                }
                            },
                            "gameStatus": {"isSubstitute": True},
                            "position": {"abbreviation": "PR"},
                        },
                        "ID2": {
                            "person": {"id": 2, "fullName": "Defense Only"},
                            "stats": {
                                "batting": {
                                    "gamesPlayed": 1,
                                    "plateAppearances": 0,
                                    "atBats": 0,
                                    "runs": 0,
                                    "hits": 0,
                                    "rbi": 0,
                                    "stolenBases": 0,
                                    "caughtStealing": 0,
                                }
                            },
                            "gameStatus": {"isSubstitute": True},
                            "position": {"abbreviation": "LF"},
                        },
                    },
                }
            }
        }

        rows = parse_batting(box_data, "home", bref_id_map={1: "runner01", 2: "defens01"})

        self.assertEqual(1, len(rows))
        self.assertEqual("Speed Runner", rows[0]["name"])
        self.assertEqual(0, rows[0]["PA"])
        self.assertEqual(1, rows[0]["R"])
        self.assertEqual(2, rows[0]["SB"])

    def test_parse_play_by_play_marks_scoring_plays_for_walkoffs(self):
        feed_data = {
            "gameData": {
                "teams": {
                    "away": {"id": 145, "abbreviation": "CWS"},
                    "home": {"id": 137, "abbreviation": "SF"},
                }
            },
            "liveData": {
                "plays": {
                    "allPlays": [
                        {
                            "result": {
                                "eventType": "single",
                                "event": "Single",
                                "description": "Walkoff Batter singles on a line drive to center field. Winning Runner scores.",
                                "rbi": 1,
                                "awayScore": 4,
                                "homeScore": 5,
                            },
                            "about": {
                                "inning": 9,
                                "halfInning": "bottom",
                                "isScoringPlay": True,
                            },
                            "count": {"outs": 2},
                            "matchup": {
                                "batter": {"id": 10, "fullName": "Walkoff Batter"},
                                "pitcher": {"id": 20, "fullName": "Away Pitcher"},
                            },
                        }
                    ]
                }
            },
        }

        plays = parse_play_by_play(feed_data, bref_id_map={10: "batter01", 20: "pitch01"})

        self.assertEqual(1, len(plays))
        self.assertTrue(plays[0]["run_scored"])
        self.assertEqual("bottom", plays[0]["half"])

    def test_parse_play_by_play_keeps_terminal_pitch_context(self):
        feed_data = {
            "gameData": {
                "teams": {
                    "away": {"id": 145, "abbreviation": "CWS"},
                    "home": {"id": 137, "abbreviation": "SF"},
                }
            },
            "liveData": {
                "plays": {
                    "allPlays": [
                        {
                            "result": {
                                "eventType": "home_run",
                                "event": "Home Run",
                                "description": "Leadoff Batter homers on a fly ball.",
                                "rbi": 1,
                                "awayScore": 1,
                                "homeScore": 0,
                            },
                            "about": {
                                "inning": 1,
                                "halfInning": "top",
                                "isScoringPlay": True,
                            },
                            "count": {"balls": 1, "strikes": 0, "outs": 0},
                            "matchup": {
                                "batter": {"id": 10, "fullName": "Leadoff Batter"},
                                "pitcher": {"id": 20, "fullName": "Home Pitcher"},
                            },
                            "playEvents": [
                                {
                                    "isPitch": True,
                                    "pitchNumber": 1,
                                    "details": {
                                        "description": "Ball",
                                        "type": {"code": "FF", "description": "Four-Seam Fastball"},
                                    },
                                    "count": {"balls": 1, "strikes": 0, "outs": 0},
                                    "pitchData": {"startSpeed": 93.2},
                                },
                                {
                                    "isPitch": True,
                                    "pitchNumber": 2,
                                    "details": {
                                        "description": "In play, run(s)",
                                        "type": {"code": "SL", "description": "Slider"},
                                    },
                                    "count": {"balls": 1, "strikes": 0, "outs": 0},
                                    "pitchData": {"startSpeed": 84.7},
                                },
                            ],
                        }
                    ]
                }
            },
        }

        plays = parse_play_by_play(feed_data, bref_id_map={10: "batter01", 20: "pitch01"})

        self.assertEqual(1, len(plays))
        self.assertEqual(2, plays[0]["pitch_count"])
        self.assertEqual(2, plays[0]["pitch_number"])
        self.assertEqual("1-0", plays[0]["pitch_count_at_play"])
        self.assertEqual("Slider", plays[0]["pitch_type"])
        self.assertEqual("SL", plays[0]["pitch_type_code"])
        self.assertEqual(84.7, plays[0]["pitch_speed"])

    def test_normalize_api_batting_rows_restores_cached_runner_only_player(self):
        game = {
            "basic_info": {"home_team_code": "MIA", "away_team_code": "BAL"},
            "source": "mlb",
            "batting": {"home": [], "away": []},
            "play_by_play": [
                {
                    "half": "bottom",
                    "batting_team": "MIA",
                    "runners": [
                        {
                            "name": "Speed Runner",
                            "player_id": "runner01",
                            "event": "Stolen Base 2B",
                            "start": "1B",
                            "end": "2B",
                            "is_out": False,
                        },
                        {
                            "name": "Speed Runner",
                            "player_id": "runner01",
                            "event": "Error",
                            "start": "3B",
                            "end": "score",
                            "is_out": False,
                        },
                    ],
                },
                {
                    "half": "bottom",
                    "batting_team": "MIA",
                    "runners": [
                        {
                            "name": "Speed Runner",
                            "player_id": "runner01",
                            "event": "Stolen Base 3B",
                            "start": "2B",
                            "end": "3B",
                            "is_out": False,
                        }
                    ],
                },
            ],
        }

        normalize_api_batting_rows(game)

        rows = game["batting"]["home"]
        self.assertEqual(1, len(rows))
        self.assertEqual("Speed Runner", rows[0]["name"])
        self.assertEqual(2, rows[0]["SB"])
        self.assertEqual(1, rows[0]["R"])

    def test_normalize_api_batting_rows_does_not_duplicate_register_aliases(self):
        game = {
            "basic_info": {"home_team_code": "ATH", "away_team_code": "CWS"},
            "source": "mlb",
            "batting": {
                "away": [
                    {
                        "name": "Munetaka Murakami",
                        "player_id": "murakmu01",
                        "bref_id": "murakmu01",
                        "register_id": "muraka000mun",
                        "AB": 5,
                        "R": 1,
                        "H": 1,
                        "RBI": 2,
                        "BB": 0,
                        "SO": 2,
                        "SB": 0,
                        "CS": 0,
                    }
                ],
                "home": [],
            },
            "play_by_play": [
                {
                    "half": "top",
                    "batting_team": "CWS",
                    "runners": [
                        {
                            "name": "Munetaka Murakami",
                            "player_id": "muraka000mun",
                            "event": "Scores",
                            "start": "3B",
                            "end": "score",
                            "is_out": False,
                        }
                    ],
                }
            ],
        }

        normalize_api_batting_rows(game)

        rows = game["batting"]["away"]
        self.assertEqual(1, len(rows))
        self.assertEqual("murakmu01", rows[0]["player_id"])
        self.assertEqual(1, rows[0]["R"])


if __name__ == "__main__":
    unittest.main()
