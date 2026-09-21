import unittest

from baseball_processor.engines.special_events_engine import SpecialEventsEngine


class SpecialEventsEngineTests(unittest.TestCase):
    def test_detects_api_pinch_hit_home_run_from_normalized_substitution(self):
        game = {
            "game_id": "SFN202608291",
            "basic_info": {
                "date_yyyymmdd": "20260829",
                "away_team": "Arizona Diamondbacks",
                "away_team_code": "ARI",
                "home_team": "San Francisco Giants",
                "home_team_code": "SF",
                "away_score_value": 7,
                "home_score_value": 1,
            },
            "batting": {
                "away": [{"name": "Lars Nootbaar", "player_id": "nootbla01"}],
                "home": [],
            },
            "pitching": {"away": [], "home": []},
            "substitutions": [{
                "raw": "Offensive Substitution: Pinch-hitter Lars Nootbaar replaces Jose Fernandez.",
                "type": "offensive_substitution",
                "player_in": "Pinch-hitter Lars Nootbaar",
                "player_out": "Jose Fernandez",
                "player_id": "nootbla01",
                "inning": 7,
                "half": "top",
            }],
            "play_by_play": [{
                "inning": 7,
                "half": "top",
                "event_type": "home_run",
                "home_run": True,
                "description": "Lars Nootbaar hits a grand slam.",
                "batter": "Lars Nootbaar",
                "batter_id": "nootbla01",
                "pitcher": "Ryan Walker",
                "rbi": 4,
            }],
            "special_events": {},
        }

        engine = SpecialEventsEngine(game)
        engine.detect_pinch_hit_hrs_from_substitutions()
        engine.detect_pinch_hit_hrs_from_substitutions()

        events = game["special_events"]["pinch_hit_hrs"]
        self.assertEqual(1, len(events))
        self.assertEqual("Lars Nootbaar", events[0]["player"])
        self.assertEqual("Jose Fernandez", events[0]["replaced_player"])
        self.assertEqual(4, events[0]["rbi"])
        self.assertEqual("ARI", events[0]["team_code"])

    def test_does_not_credit_home_run_after_non_hr_pinch_hit_plate_appearance(self):
        game = {
            "basic_info": {},
            "batting": {"away": [{"name": "Pinch Hitter", "player_id": "hitter01"}], "home": []},
            "pitching": {"away": [], "home": []},
            "substitutions": [{
                "raw": "Offensive Substitution: Pinch-hitter Pinch Hitter replaces Starter.",
                "player_in": "Pinch-hitter Pinch Hitter",
                "player_out": "Starter",
                "player_id": "hitter01",
                "inning": 8,
                "half": "top",
            }],
            "play_by_play": [
                {"inning": 8, "half": "top", "event_type": "single", "batter": "Pinch Hitter", "batter_id": "hitter01"},
                {"inning": 8, "half": "top", "event_type": "home_run", "batter": "Pinch Hitter", "batter_id": "hitter01"},
            ],
            "special_events": {},
        }

        SpecialEventsEngine(game).detect_pinch_hit_hrs_from_substitutions()

        self.assertEqual([], game["special_events"]["pinch_hit_hrs"])


if __name__ == "__main__":
    unittest.main()
