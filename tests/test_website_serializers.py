import unittest

import pandas as pd

from baseball_processor.website.serializers import DataSerializer


class FakeSituationTracker:
    def create_risp_dataframe(self, min_ab=5):
        return pd.DataFrame(
            [
                {
                    "Player ID": "player-1",
                    "Name": "Power Bat",
                    "RISP AB": 6,
                    "RISP H": 3,
                    "RISP AVG": 0.5,
                    "RISP HR": 1,
                }
            ]
        )

    def create_two_out_dataframe(self, min_ab=5):
        return pd.DataFrame(
            [
                {
                    "Player ID": "player-2",
                    "Name": "Two Out Bat",
                    "2-Out AB": 5,
                    "2-Out H": 2,
                    "2-Out AVG": 0.4,
                    "2-Out HR": 1,
                }
            ]
        )

    def create_clutch_situations_dataframe(self, min_ab=3):
        return pd.DataFrame(
            [
                {
                    "Player ID": "player-3",
                    "Name": "Clutch Bat",
                    "RISP+2Out AB": 3,
                    "RISP+2Out H": 2,
                    "RISP+2Out AVG": 0.667,
                    "RISP+2Out HR": 0,
                }
            ]
        )

    def create_bases_loaded_dataframe(self):
        return pd.DataFrame(
            [
                {
                    "Player ID": "player-4",
                    "Name": "Slam Bat",
                    "Grand Slams": 1,
                }
            ]
        )

    def create_late_close_dataframe(self, min_ab=5):
        return pd.DataFrame(
            [
                {
                    "Player ID": "player-5",
                    "Name": "Late Bat",
                    "Late/Close AB": 5,
                    "Late/Close H": 1,
                    "Late/Close AVG": 0.2,
                    "Late/Close HR": 1,
                }
            ]
        )


class FakeSaberTracker:
    def create_wpa_dataframe(self):
        return pd.DataFrame(
            [
                {
                    "Player ID": "player-1",
                    "Name": "Power Bat",
                    "Games": 2,
                    "Total WPA": 0.777,
                    "Avg WPA": 0.3885,
                    "Positive WPA": 1.234,
                    "Negative WPA": -0.457,
                    "Best Game WPA": 0.5,
                    "Best Game ID": "HOM202604300",
                    "Worst Game WPA": -0.1,
                    "Worst Game ID": "AWY202605010",
                }
            ]
        )


class FakeDefenseTracker:
    def create_defensive_leaders_dataframe(self, min_games=1):
        return pd.DataFrame(
            [
                {
                    "Player ID": "player-1",
                    "Name": "Glove Star",
                    "Games": 3,
                    "PO": 10,
                    "A": 4,
                    "E": 1,
                    "TC": 15,
                    "Fielding %": 0.933,
                    "Positions": "SS, 2B",
                }
            ]
        )

    def create_lineup_analysis_dataframe(self, min_games=1):
        return pd.DataFrame(
            [
                {
                    "Player ID": "player-1",
                    "Name": "Glove Star",
                    "Games": 3,
                    "Most Common Spot": 2,
                    "Times in Spot": 2,
                    "Pinch Hits": 1,
                }
            ]
        )

    def create_lineup_position_matrix(self):
        return pd.DataFrame(
            [{"#1": 1, "#2": 2, "#3": 0, "#4": 0, "#5": 0, "#6": 0, "#7": 0, "#8": 0, "#9": 0}],
            index=["Glove Star"],
        )


class FakeWeatherTracker:
    def get_summary_stats(self):
        return {
            "highest_wind_speed": "20 mph",
            "day_games": 2,
            "wind_directions": {
                "Centerfield": 1,
                "Left Field": 1,
            },
        }


class DataSerializerTests(unittest.TestCase):
    def test_serialize_milestones_includes_multiple_categories(self):
        milestones = {
            "Multi-HR Games": pd.DataFrame(
                [
                    {
                        "Date": "2026-04-30",
                        "Player": "Power Bat",
                        "Team": "HOM",
                        "Opponent": "AWY",
                        "GameID": "game-1",
                        "HR": 2,
                        "H": 3,
                        "RBI": 4,
                    }
                ]
            ),
            "Quality Starts": pd.DataFrame(
                [
                    {
                        "Date": "2026-04-29",
                        "Player": "Ace Starter",
                        "Team": "AWY",
                        "Opponent": "HOM",
                        "GameID": "game-2",
                        "IP": "6.0",
                        "SO": 7,
                        "H": 3,
                        "ER": 1,
                        "BB": 1,
                    }
                ]
            ),
            "4+ RBI Games": pd.DataFrame(
                [
                    {
                        "Date": "2026-04-28",
                        "Player": "Strong Day",
                        "Team": "HOM",
                        "Opponent": "AWY",
                        "GameID": "game-3",
                        "H": 2,
                        "RBI": 4,
                    }
                ]
            ),
        }

        serialized = DataSerializer()._serialize_milestones(milestones)

        self.assertEqual(["Multi-HR Games", "Quality Starts"], [m["type"] for m in serialized])

    def test_serialize_milestones_can_include_routine_categories(self):
        milestones = {
            "4+ RBI Games": pd.DataFrame(
                [
                    {
                        "Date": "2026-04-28",
                        "Player": "Strong Day",
                        "Team": "HOM",
                        "Opponent": "AWY",
                        "GameID": "game-3",
                        "H": 2,
                        "RBI": 4,
                    }
                ]
            ),
            "5+ RBI Games": pd.DataFrame(
                [
                    {
                        "Date": "2026-04-29",
                        "Player": "Huge Day",
                        "Team": "HOM",
                        "Opponent": "AWY",
                        "GameID": "game-4",
                        "H": 3,
                        "RBI": 5,
                    }
                ]
            ),
        }

        serialized = DataSerializer()._serialize_milestones(milestones, include_excluded=True)

        self.assertEqual(["5+ RBI Games", "4+ RBI Games"], [m["type"] for m in serialized])
        self.assertFalse(serialized[0]["routine"])
        self.assertTrue(serialized[1]["routine"])

    def test_serialize_run_milestones_show_run_total(self):
        milestones = {
            "4+ Run Games": pd.DataFrame(
                [
                    {
                        "Date": "2026-05-05",
                        "Player": "Fast Scorer",
                        "Team": "HOM",
                        "Opponent": "AWY",
                        "GameID": "game-5",
                        "H": 2,
                        "R": 4,
                        "RBI": 2,
                        "2B": 1,
                        "3B": 0,
                        "HR": 0,
                        "Detail": "2 H (1 2B, 0 3B, 0 HR), 2 RBI",
                    }
                ]
            )
        }

        serialized = DataSerializer()._serialize_milestones(milestones, include_excluded=True)

        self.assertEqual("4 R - 2 H (1 2B, 0 3B, 0 HR), 2 RBI", serialized[0]["detail"])
        self.assertEqual(4, serialized[0]["r"])

    def test_serialize_consecutive_hr_milestones_preserves_context(self):
        milestones = {
            "Consecutive HR Instances": pd.DataFrame(
                [
                    {
                        "Date": "2004-05-27",
                        "Team": "BAL",
                        "Opponent": "NYY",
                        "GameID": "BAL200405270",
                        "Inning": "Bottom 3",
                        "Players": "Miguel Tejada, Rafael Palmeiro",
                        "Pitchers": "Jose Contreras",
                        "HR Count": 2,
                        "Score Swing": "BAL 0-0 -> 3-0",
                        "Detail": "Bottom 3, 2 outs: Miguel Tejada 2-run HR, Rafael Palmeiro solo HR - off Jose Contreras - BAL 0-0 -> 3-0",
                    }
                ]
            )
        }

        serialized = DataSerializer()._serialize_milestones(milestones)

        self.assertEqual("Consecutive HR Instances", serialized[0]["type"])
        self.assertEqual("Miguel Tejada, Rafael Palmeiro", serialized[0]["player"])
        self.assertEqual(2, serialized[0]["hrCount"])
        self.assertEqual("Jose Contreras", serialized[0]["pitchers"])
        self.assertEqual("BAL 0-0 -> 3-0", serialized[0]["scoreSwing"])
        self.assertIn("2-run HR", serialized[0]["detail"])

    def test_serialize_hall_of_famers_preserves_ids_and_stats(self):
        df = pd.DataFrame(
            [
                {
                    "Name": "Legend Player",
                    "Player ID": "legend01",
                    "Year Inducted": 2030,
                    "Position(s)": "RF",
                    "Teams in Games": "HOM",
                    "Games Seen": 2,
                    "First Game": "HOM202604300",
                    "Last Game": "AWY202605010",
                    "Span": "1 day",
                    "AB": 8,
                    "H": 4,
                    "HR": 1,
                    "RBI": 5,
                    "AVG": 0.5,
                    "IP": "",
                    "W": "",
                    "L": "",
                    "ERA": "",
                    "SO_P": "",
                    "Milestones Achieved": "Multi-HR Games",
                    "GameIDs": "HOM202604300, AWY202605010",
                }
            ]
        )

        serialized = DataSerializer()._serialize_hall_of_famers(df)

        self.assertEqual(1, len(serialized))
        self.assertEqual("legend01", serialized[0]["playerId"])
        self.assertEqual("0.500", serialized[0]["avg"])
        self.assertEqual(0, serialized[0]["wins"])
        self.assertEqual("Multi-HR Games", serialized[0]["milestones"])

    def test_serialize_all_data_includes_situational_tables(self):
        processed_data = {
            "summary_rows": [],
            "milestones": {},
            "situation_tracker": FakeSituationTracker(),
            "_raw_games": [],
        }

        serialized = DataSerializer().serialize_all_data(processed_data)

        self.assertEqual(1, len(serialized["rispPerformance"]))
        self.assertEqual("player-1", serialized["rispPerformance"][0]["playerId"])
        self.assertEqual("0.500", serialized["rispPerformance"][0]["avg"])
        self.assertEqual(1, len(serialized["twoOutPerformance"]))
        self.assertEqual(1, len(serialized["rispTwoOutPerformance"]))
        self.assertEqual(1, len(serialized["basesLoaded"]))
        self.assertEqual(1, len(serialized["lateClose"]))

    def test_extract_game_details_marks_api_grand_slam_key_play(self):
        raw_game = {
            "basic_info": {"game_type": "regular", "source": "mlb"},
            "play_by_play": [
                {
                    "inning": 5,
                    "half": "bottom",
                    "event_type": "home_run",
                    "description": "Power Bat hits a grand slam (7) to left field. Runner A scores. Runner B scores. Runner C scores.",
                    "rbi": 4,
                    "batter": "Power Bat",
                    "pitcher": "Away Pitcher",
                }
            ],
        }

        details = DataSerializer()._extract_game_details(raw_game)

        self.assertEqual("grand_slam", details["keyPlays"][0]["type"])
        self.assertEqual("Power Bat", details["keyPlays"][0]["batter"])
        self.assertEqual(4, details["keyPlays"][0]["rbi"])

    def test_serialize_all_data_includes_wpa_leaders(self):
        processed_data = {
            "summary_rows": [],
            "milestones": {},
            "saber_tracker": FakeSaberTracker(),
            "_raw_games": [],
        }

        serialized = DataSerializer().serialize_all_data(processed_data)

        self.assertEqual(1, len(serialized["wpaLeaders"]))
        leader = serialized["wpaLeaders"][0]
        self.assertEqual("player-1", leader["playerId"])
        self.assertEqual("0.777", leader["totalWpa"])
        self.assertEqual("0.389", leader["avgWpa"])
        self.assertEqual("HOM202604300", leader["bestGameId"])

    def test_serialize_all_data_includes_defensive_and_lineup_tables(self):
        processed_data = {
            "summary_rows": [],
            "milestones": {},
            "defense_tracker": FakeDefenseTracker(),
            "_raw_games": [],
        }

        serialized = DataSerializer().serialize_all_data(processed_data)

        self.assertEqual(1, len(serialized["defensiveLeaders"]))
        self.assertEqual("player-1", serialized["defensiveLeaders"][0]["playerId"])
        self.assertEqual("0.933", serialized["defensiveLeaders"][0]["fieldingPct"])
        self.assertEqual(1, len(serialized["lineupAnalysis"]))
        self.assertEqual(1, len(serialized["lineupMatrix"]))
        self.assertEqual(2, serialized["lineupMatrix"][0]["spot2"])
        self.assertEqual(3, serialized["lineupMatrix"][0]["total"])

    def test_serialize_all_data_includes_weather_timing(self):
        processed_data = {
            "summary_rows": [],
            "milestones": {},
            "weather_tracker": FakeWeatherTracker(),
            "_raw_games": [],
        }

        serialized = DataSerializer().serialize_all_data(processed_data)

        self.assertEqual(4, len(serialized["weatherTiming"]))
        self.assertIn(
            {"category": "Weather & Timing", "statistic": "Highest Wind Speed", "value": "20 mph"},
            serialized["weatherTiming"],
        )
        self.assertIn(
            {"category": "Wind Directions", "statistic": "Centerfield", "value": "1"},
            serialized["weatherTiming"],
        )

    def test_serialize_abs_player_stats_includes_role_success_rates(self):
        raw_games = [
            {
                "game_id": "HOM202604300",
                "abs_challenges": {
                    "reviews": [
                        {"challengePlayer": "Two-Way Challenger", "challengerType": "batter", "overturned": True},
                        {"challengePlayer": "Two-Way Challenger", "challengerType": "batter", "overturned": False},
                        {"challengePlayer": "Two-Way Challenger", "challengerType": "catcher", "overturned": True},
                        {"challengePlayer": "Two-Way Challenger", "challengerType": "catcher", "overturned": True},
                        {"challengePlayer": "Two-Way Challenger", "challengerType": "catcher", "overturned": False},
                        {"challengePlayer": "Pitcher Challenger", "challengerType": "pitcher", "overturned": True},
                    ]
                },
            }
        ]

        serialized = DataSerializer()._serialize_abs_player_stats(raw_games)
        by_name = {player["name"]: player for player in serialized}

        two_way = by_name["Two-Way Challenger"]
        self.assertEqual(5, two_way["challenges"])
        self.assertEqual(60, two_way["successRate"])
        self.assertEqual(2, two_way["asBatter"])
        self.assertEqual(1, two_way["batterOverturned"])
        self.assertEqual(1, two_way["batterUpheld"])
        self.assertEqual(50, two_way["batterSuccessRate"])
        self.assertEqual(3, two_way["asCatcher"])
        self.assertEqual(2, two_way["catcherOverturned"])
        self.assertEqual(1, two_way["catcherUpheld"])
        self.assertEqual(67, two_way["catcherSuccessRate"])
        self.assertIsNone(two_way["pitcherSuccessRate"])

        pitcher = by_name["Pitcher Challenger"]
        self.assertEqual(1, pitcher["asPitcher"])
        self.assertEqual(1, pitcher["pitcherOverturned"])
        self.assertEqual(0, pitcher["pitcherUpheld"])
        self.assertEqual(100, pitcher["pitcherSuccessRate"])

    def test_serialize_all_data_snapshot_counts(self):
        raw_games = [
            {
                "game_id": "HOM202604300",
                "basic_info": {
                    "date_yyyymmdd": "20260430",
                    "away_team_code": "AWY",
                    "home_team_code": "HOM",
                    "away_score_value": 3,
                    "home_score_value": 4,
                    "venue": "Example Park",
                    "game_type": "regular",
                    "source": "mlb",
                },
                "batting": {
                    "away": [
                        {
                            "name": "Power Bat",
                            "player_id": "player-1",
                            "team": "AWY",
                            "AB": 4,
                            "H": 2,
                            "R": 1,
                            "RBI": 3,
                            "BB": 0,
                            "SO": 1,
                            "HR": 2,
                        }
                    ],
                    "home": [],
                },
                "pitching": {
                    "away": [],
                    "home": [
                        {
                            "name": "Ace Starter",
                            "player_id": "pitcher-1",
                            "team": "HOM",
                            "IP": "6.0",
                            "H": 3,
                            "R": 1,
                            "ER": 1,
                            "BB": 1,
                            "SO": 7,
                            "HR": 0,
                        }
                    ],
                },
            }
        ]
        processed_data = {
            "summary_rows": [{"Record": "Games", "Value": "1", "Detail": "", "Score": "", "GameIDs": "HOM202604300"}],
            "milestones": {
                "Multi-HR Games": pd.DataFrame(
                    [
                        {
                            "Date": "2026-04-30",
                            "Player": "Power Bat",
                            "Player ID": "player-1",
                            "Team": "AWY",
                            "Opponent": "HOM",
                            "GameID": "HOM202604300",
                            "HR": 2,
                            "H": 2,
                            "RBI": 3,
                        }
                    ]
                ),
                "3 Pitch Innings": pd.DataFrame([{"Date": "2026-04-30", "Player": "Routine", "GameID": "HOM202604300"}]),
            },
            "hitters": pd.DataFrame(
                [
                    {
                        "Name": "Power Bat",
                        "Player ID": "player-1",
                        "Team": "AWY",
                        "G": 1,
                        "AB": 4,
                        "PA": 4,
                        "H": 2,
                        "AVG": 0.5,
                        "R": 1,
                        "RBI": 3,
                        "HR": 2,
                        "GameIDs": "HOM202604300",
                    }
                ]
            ),
            "pitchers": pd.DataFrame(
                [
                    {
                        "Name": "Ace Starter",
                        "Player ID": "pitcher-1",
                        "Team": "HOM",
                        "G": 1,
                        "GS": 1,
                        "IP": "6.0",
                        "H": 3,
                        "R": 1,
                        "ER": 1,
                        "BB": 1,
                        "SO": 7,
                        "HR": 0,
                        "GameIDs": "HOM202604300",
                    }
                ]
            ),
            "hofers_seen": pd.DataFrame(
                [
                    {
                        "Name": "Power Bat",
                        "Player ID": "player-1",
                        "Year Inducted": 2035,
                        "Position(s)": "RF",
                        "Teams in Games": "AWY",
                        "Games Seen": 1,
                        "First Game": "HOM202604300",
                        "Last Game": "HOM202604300",
                        "Span": "Single game",
                        "AB": 4,
                        "H": 2,
                        "HR": 2,
                        "RBI": 3,
                        "AVG": 0.5,
                        "IP": "",
                        "W": "",
                        "L": "",
                        "ERA": "",
                        "SO_P": "",
                        "Milestones Achieved": "Multi-HR Games",
                        "GameIDs": "HOM202604300",
                    }
                ]
            ),
            "game_log": pd.DataFrame(
                [
                    {
                        "Date": "04/30/2026",
                        "Away Team": "AWY",
                        "Home Team": "HOM",
                        "Score": "AWY 3 - 4 HOM",
                        "Venue": "Example Park",
                        "Attendance": 10000,
                        "Game Length": "2:30",
                        "GameID": "HOM202604300",
                    }
                ]
            ),
            "_raw_games": raw_games,
        }

        serialized = DataSerializer().serialize_all_data(processed_data)
        snapshot_counts = {
            "summary": len(serialized["summary"]),
            "milestones": len(serialized["milestones"]),
            "players": len(serialized["players"]),
            "pitchers": len(serialized["pitchers"]),
            "hallOfFamers": len(serialized["hallOfFamers"]),
            "games": len(serialized["games"]),
            "playerGames": len(serialized["playerGames"]),
            "pitcherGames": len(serialized["pitcherGames"]),
        }

        self.assertEqual(
            {
                "summary": 1,
                "milestones": 1,
                "players": 1,
                "pitchers": 1,
                "hallOfFamers": 1,
                "games": 1,
                "playerGames": 1,
                "pitcherGames": 1,
            },
            snapshot_counts,
        )
        self.assertEqual(["Multi-HR Games"], [m["type"] for m in serialized["milestones"]])
        self.assertEqual({"regular": 1, "postseason": 0, "spring": 0, "allstar": 0}, serialized["gameTypeCounts"])


if __name__ == "__main__":
    unittest.main()
