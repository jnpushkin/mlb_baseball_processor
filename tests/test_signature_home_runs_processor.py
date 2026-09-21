import unittest
from unittest.mock import patch

import pandas as pd

from baseball_processor.processors.signature_home_runs_processor import SignatureHomeRunsProcessor


class SignatureHomeRunsProcessorTests(unittest.TestCase):
    @staticmethod
    def _game(game_id, home_runs, pitcher=None):
        plays = []
        if home_runs and pitcher:
            plays.append({
                "inning": 7,
                "half": "top",
                "event_type": "home_run",
                "home_run": True,
                "batter": "Lars Nootbaar",
                "batter_id": "nootbla01",
                "pitcher": pitcher,
            })
        return {
            "game_id": game_id,
            "basic_info": {
                "date_yyyymmdd": "20260829",
                "venue": "Oracle Park",
            },
            "batting": {
                "away": [{
                    "name": "Lars Nootbaar",
                    "player_id": "nootbla01",
                    "HR": home_runs,
                }],
                "home": [],
            },
            "play_by_play": plays,
        }

    def test_splash_hit_matches_only_doubleheader_game_where_player_homered(self):
        game_one = self._game("SFN202608291", 1, "Ryan Walker")
        game_two = self._game("SFN202608292", 0)
        references = {
            "splash_visitors": pd.DataFrame([{
                "SplashNumber": 69,
                "Player": "Lars Nootbaar",
                "PlayerID": "nootbla01",
                "Team": "Arizona Diamondbacks",
                "Date": "2026-08-29",
                "Date_yyyymmdd": "20260829",
                "Pitcher": "Ryan Walker",
            }]),
        }
        processor = SignatureHomeRunsProcessor([game_one, game_two])

        first_matches = processor._check_splash_hits(game_one, "20260829", game_one["game_id"], references)
        second_matches = processor._check_splash_hits(game_two, "20260829", game_two["game_id"], references)

        self.assertEqual(["SFN202608291"], [match["GameID"] for match in first_matches])
        self.assertEqual([], second_matches)

    def test_reference_pitcher_disambiguates_when_player_homered_in_both_games(self):
        correct_game = self._game("SFN202608291", 1, "Ryan Walker")
        other_game = self._game("SFN202608292", 1, "Other Pitcher")
        processor = SignatureHomeRunsProcessor([correct_game, other_game])

        self.assertTrue(processor._player_homered_in_game(correct_game, "nootbla01", "Ryan Walker"))
        self.assertFalse(processor._player_homered_in_game(other_game, "nootbla01", "Ryan Walker"))

    def test_suppresses_reference_when_both_games_remain_ambiguous(self):
        game_one = self._game("SFN202608291", 1, "Ryan Walker")
        game_two = self._game("SFN202608292", 1, "Ryan Walker")
        references = {
            "splash_visitors": pd.DataFrame([{
                "SplashNumber": 69,
                "Player": "Lars Nootbaar",
                "PlayerID": "nootbla01",
                "Team": "Arizona Diamondbacks",
                "Date": "2026-08-29",
                "Date_yyyymmdd": "20260829",
                "Pitcher": "Ryan Walker",
            }]),
        }
        processor = SignatureHomeRunsProcessor([game_one, game_two])

        with patch.object(processor, "_load_reference_data", return_value=references):
            result = processor.process_signature_home_runs()

        self.assertTrue(result.empty)

    def test_legacy_bref_details_and_name_only_pbp_confirm_home_run(self):
        game = {
            "game_id": "BAL201309110",
            "basic_info": {"date_yyyymmdd": "20130911", "venue": "Oriole Park at Camden Yards"},
            "batting": {
                "away": [{
                    "name": "Curtis Granderson",
                    "player_id": "grandcu01",
                    "HR": None,
                    "Details": "HR,3B",
                }],
                "home": [],
            },
            "play_by_play": [{
                "home_run": True,
                "batter": "Curtis\u00a0Granderson",
                "batter_id": None,
                "pitcher": "Scott\u00a0Feldman",
            }],
        }

        processor = SignatureHomeRunsProcessor([game])

        self.assertTrue(processor._player_homered_in_game(game, "grandcu01", "Scott Feldman"))


if __name__ == "__main__":
    unittest.main()
