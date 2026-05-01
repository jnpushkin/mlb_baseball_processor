import unittest

import pandas as pd

from baseball_processor.website.parity import collect_website_data_parity_issues


class FakeWeatherTracker:
    def get_summary_stats(self):
        return {
            "day_games": 2,
            "wind_directions": {"out": 1, "in": 1},
        }


class FakeSaberTracker:
    def create_wpa_dataframe(self):
        return pd.DataFrame([{"Name": "Player A", "Total WPA": 0.5}])


class EmptySituationTracker:
    def create_risp_dataframe(self, min_ab=5):
        return pd.DataFrame()

    def create_two_out_dataframe(self, min_ab=5):
        return pd.DataFrame()

    def create_clutch_situations_dataframe(self, min_ab=3):
        return pd.DataFrame()

    def create_bases_loaded_dataframe(self):
        return pd.DataFrame()

    def create_late_close_dataframe(self, min_ab=5):
        return pd.DataFrame()


class NonEmptySituationTracker:
    def create_risp_dataframe(self, min_ab=5):
        return pd.DataFrame([{"Name": "A"}])

    def create_two_out_dataframe(self, min_ab=5):
        return pd.DataFrame([{"Name": "B"}])

    def create_clutch_situations_dataframe(self, min_ab=3):
        return pd.DataFrame([{"Name": "C"}])

    def create_bases_loaded_dataframe(self):
        return pd.DataFrame([{"Name": "D"}])

    def create_late_close_dataframe(self, min_ab=5):
        return pd.DataFrame([{"Name": "E"}])


class EmptyDefenseTracker:
    def create_defensive_leaders_dataframe(self, min_games=1):
        return pd.DataFrame()

    def create_lineup_analysis_dataframe(self, min_games=1):
        return pd.DataFrame()

    def create_lineup_position_matrix(self):
        return pd.DataFrame()


class NonEmptyDefenseTracker:
    def create_defensive_leaders_dataframe(self, min_games=1):
        return pd.DataFrame([{"Name": "Glove A"}])

    def create_lineup_analysis_dataframe(self, min_games=1):
        return pd.DataFrame([{"Name": "Lineup A"}])

    def create_lineup_position_matrix(self):
        return pd.DataFrame([{"#1": 1}], index=["Matrix A"])


class WebsiteParityTests(unittest.TestCase):
    def test_detects_core_count_mismatch(self):
        processed_data = {
            "summary_rows": [{"Record": "Games"}, {"Record": "Runs"}],
            "hitters": pd.DataFrame([{"Name": "A"}, {"Name": "B"}]),
            "milestones": {
                "Multi-HR Games": pd.DataFrame([{"Player": "A"}]),
                "3 Pitch Innings": pd.DataFrame([{"Player": "B"}]),
            },
        }
        json_data = {
            "summary": [{"record": "Games"}],
            "players": [{"name": "A"}],
            "milestones": [{"type": "Multi-HR Games"}],
        }

        issues = collect_website_data_parity_issues(
            processed_data,
            json_data,
            excluded_milestone_types={"3 Pitch Innings"},
            include_feature_gaps=False,
        )

        datasets = {issue["dataset"] for issue in issues}
        self.assertEqual({"Summary", "Hitters"}, datasets)

    def test_detects_excel_only_feature_gaps(self):
        processed_data = {
            "weather_tracker": FakeWeatherTracker(),
            "saber_tracker": FakeSaberTracker(),
            "situation_tracker": EmptySituationTracker(),
            "defense_tracker": EmptyDefenseTracker(),
        }
        json_data = {}

        issues = collect_website_data_parity_issues(processed_data, json_data)

        gaps = {
            issue["dataset"]: issue
            for issue in issues
            if issue["kind"] == "missing_website_dataset"
        }
        self.assertEqual(3, gaps["Weather & Timing"]["sourceCount"])
        self.assertEqual(1, gaps["WPA Leaders"]["sourceCount"])

    def test_situational_tables_are_not_reported_when_serialized(self):
        processed_data = {
            "situation_tracker": NonEmptySituationTracker(),
        }
        json_data = {
            "rispPerformance": [{"name": "A"}],
            "twoOutPerformance": [{"name": "B"}],
            "rispTwoOutPerformance": [{"name": "C"}],
            "basesLoaded": [{"name": "D"}],
            "lateClose": [{"name": "E"}],
        }

        issues = collect_website_data_parity_issues(processed_data, json_data)

        datasets = {issue["dataset"] for issue in issues}
        self.assertNotIn("RISP Performance", datasets)
        self.assertNotIn("2-Out Performance", datasets)
        self.assertNotIn("RISP + 2 Outs", datasets)
        self.assertNotIn("Bases Loaded", datasets)
        self.assertNotIn("Late & Close", datasets)

    def test_wpa_leaders_are_not_reported_when_serialized(self):
        processed_data = {
            "saber_tracker": FakeSaberTracker(),
        }
        json_data = {
            "wpaLeaders": [{"name": "Player A", "totalWpa": "0.500"}],
        }

        issues = collect_website_data_parity_issues(processed_data, json_data)

        datasets = {issue["dataset"] for issue in issues}
        self.assertNotIn("WPA Leaders", datasets)

    def test_defensive_and_lineup_tables_are_not_reported_when_serialized(self):
        processed_data = {
            "defense_tracker": NonEmptyDefenseTracker(),
        }
        json_data = {
            "defensiveLeaders": [{"name": "Glove A"}],
            "lineupAnalysis": [{"name": "Lineup A"}],
            "lineupMatrix": [{"name": "Matrix A"}],
        }

        issues = collect_website_data_parity_issues(processed_data, json_data)

        datasets = {issue["dataset"] for issue in issues}
        self.assertNotIn("Defensive Leaders", datasets)
        self.assertNotIn("Lineup Analysis", datasets)
        self.assertNotIn("Lineup Matrix", datasets)

    def test_weather_timing_is_not_reported_when_serialized(self):
        processed_data = {
            "weather_tracker": FakeWeatherTracker(),
        }
        json_data = {
            "weatherTiming": [
                {"statistic": "Day Games", "value": "2"},
                {"statistic": "Out", "value": "1"},
                {"statistic": "In", "value": "1"},
            ],
        }

        issues = collect_website_data_parity_issues(processed_data, json_data)

        datasets = {issue["dataset"] for issue in issues}
        self.assertNotIn("Weather & Timing", datasets)


if __name__ == "__main__":
    unittest.main()
