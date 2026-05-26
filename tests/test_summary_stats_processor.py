import pandas as pd

from baseball_processor.processors.summary_stats_processor import SummaryStatsProcessor


def make_processor():
    return SummaryStatsProcessor(
        games=[],
        all_players={},
        b2b_only_df=pd.DataFrame(),
        b2b2b_only_df=pd.DataFrame(),
        b2b2b2b_only_df=pd.DataFrame(),
        triple_play_df=pd.DataFrame(),
        hitters_df=pd.DataFrame(),
        pitchers_df=pd.DataFrame(),
        milestones={},
    )


def make_summary_game(game_id, away, home, date_yyyymmdd, away_score, home_score):
    return {
        "game_id": game_id,
        "basic_info": {
            "away_team_code": away,
            "home_team_code": home,
            "date_yyyymmdd": date_yyyymmdd,
            "away_score_value": away_score,
            "home_score_value": home_score,
        },
        "linescore": {
            "away": {"R": away_score, "H": 0, "innings": ["0"] * 9},
            "home": {"R": home_score, "H": 0, "innings": ["0"] * 9},
        },
    }


def summary_row(processor, record):
    rows = processor._build_summary_rows(pd.DataFrame())
    return next(row for row in rows if row["Record"] == record)


def test_formats_inside_the_park_home_run_detail_with_play_context():
    processor = make_processor()

    detail = processor._format_inside_park_hr_detail(
        {
            "batter": "Patrick\xa0Bailey",
            "pitcher": "Jordan\xa0Romano",
            "inning": 9,
            "half": "bottom",
            "outs": 1,
            "rbi": 3,
            "pitch_count": 1,
            "description": "Inside-the-park Home Run (Fly Ball to Deep CF-RF); C.\xa0Schmitt Scores; B.\xa0Wisely Scores",
        }
    )

    assert detail == (
        "Patrick Bailey - Bottom 9, 1 out: 3-run inside-the-park HR "
        "off Jordan Romano (1st pitch) - Fly Ball to Deep CF-RF"
    )


def test_formats_both_teams_10_plus_detail_with_score_context():
    processor = make_processor()

    detail = processor._format_both_teams_10_detail(
        {"away_team_code": "DET", "home_team_code": "BAL"},
        {
            "away": {"R": 10, "H": 12, "innings": ["0"] * 10},
            "home": {"R": 11, "H": 17, "innings": ["0"] * 10},
        },
    )

    assert detail == "DET 10, BAL 11 in 10 innings (21 runs, 29 hits)"


def test_formats_twenty_hit_detail_with_combined_score_context():
    processor = make_processor()

    detail = processor._format_twenty_hit_detail(
        {"away_team_code": "OAK", "home_team_code": "BAL"},
        {
            "away": {"R": 2, "H": 8, "innings": ["0"] * 9},
            "home": {"R": 18, "H": 20, "innings": ["0"] * 9},
        },
    )

    assert detail == "BAL 20 H (28 combined hits) - OAK 2, BAL 18 (20 runs, 28 hits)"


def test_formats_biggest_victory_detail_with_margin_and_score_context():
    processor = make_processor()

    detail = processor._format_biggest_victory_detail(
        {"away_team_code": "OAK", "home_team_code": "BAL"},
        {
            "away": {"R": 2, "H": 8, "innings": ["0"] * 9},
            "home": {"R": 18, "H": 20, "innings": ["0"] * 9},
        },
        "BAL",
        16,
    )

    assert detail == "BAL by 16 - OAK 2, BAL 18 (20 runs, 28 hits)"


def test_formats_single_team_run_extreme_with_game_context():
    processor = make_processor()
    game = {
        "basic_info": {"away_team_code": "BAL", "home_team_code": "BOS"},
        "linescore": {
            "away": {"R": 5, "H": 14, "innings": ["0"] * 9},
            "home": {"R": 19, "H": 20, "innings": ["0", "0", "0", "0", "0", "0", "0", "13", "6"]},
        },
    }

    detail = processor._format_single_team_record_detail(
        game, "BOS", "R", 19, "Most Runs by One Team"
    )

    assert detail == (
        "BOS scored 19 runs on 20 hits, including 13 runs in Bottom 8 - "
        "BAL 5, BOS 19 (24 runs, 34 hits)"
    )


def test_formats_single_team_hr_extreme_with_player_breakdown():
    processor = make_processor()
    game = {
        "basic_info": {"away_team_code": "ARI", "home_team_code": "SF"},
        "linescore": {
            "away": {"R": 5, "H": 10, "innings": ["0"] * 9},
            "home": {"R": 11, "H": 13, "innings": ["0"] * 9},
        },
        "batting": {"away": [], "home": []},
        "footer_summary": {
            "home": {"HR": "Rafael Devers 2 (2); Willy Adames (1); Matt Chapman (1); Jung Hoo Lee (1)."},
            "away": {},
        },
    }

    detail = processor._format_single_team_record_detail(
        game, "SF", "HR", 5, "Most HRs by One Team"
    )

    assert detail == (
        "SF hit 5 HR: Rafael Devers (2), Willy Adames, Matt Chapman, Jung Hoo Lee - "
        "ARI 5, SF 11 (16 runs, 23 hits)"
    )


def test_formats_combined_hr_extreme_with_score_context():
    processor = make_processor()
    game = {
        "basic_info": {"away_team_code": "STL", "home_team_code": "BAL"},
        "linescore": {
            "away": {"R": 5, "H": 9, "innings": ["0"] * 9},
            "home": {"R": 8, "H": 9, "innings": ["0"] * 9},
        },
        "batting": {"away": [], "home": []},
        "footer_summary": {
            "away": {"HR": "Stephen Piscotty 2 (2); Dexter Fowler (1); Yadier Molina (1)."},
            "home": {"HR": "Seth Smith (1); Trey Mancini (1); Mark Trumbo (1); Welington Castillo (1)."},
        },
    }

    detail = processor._make_combined_detail(game, "HR")

    assert detail == (
        "8 combined HRs - STL 4 HR: Stephen Piscotty (2), Dexter Fowler, Yadier Molina / "
        "BAL 4 HR: Seth Smith, Trey Mancini, Mark Trumbo, Welington Castillo - "
        "STL 5, BAL 8 (13 runs, 18 hits)"
    )


def test_formats_combined_hit_extreme_as_hit_totals_only():
    processor = make_processor()
    game = {
        "basic_info": {"away_team_code": "LAD", "home_team_code": "SF"},
        "linescore": {
            "away": {"R": 1, "H": 4, "innings": ["0"] * 10},
            "home": {"R": 5, "H": 3, "innings": ["0"] * 10},
        },
    }

    detail = processor._make_combined_detail(game, "H")

    assert detail == "7 total hits: LAD 4 H, SF 3 H (10 innings)"


def test_most_sb_player_summary_keeps_game_context_aligned_with_player_details():
    processor = make_processor()
    processor.games = [
        make_summary_game("BAL202506240", "TEX", "BAL", "20250624", 6, 5),
        make_summary_game("SFN202404090", "WAS", "SF", "20240409", 8, 1),
        make_summary_game("SFN202404080", "WAS", "SF", "20240408", 5, 3),
    ]
    processor.most_sb_player = 3
    processor.most_sb_player_gameids = [
        "BAL202506240",
        "SFN202404090",
        "SFN202404080",
    ]
    processor.most_sb_player_labels = [
        "Sam Haggerty (3)",
        "Trey Lipscomb (3)",
        "Jacob Young (3)",
    ]

    row = summary_row(processor, "Most SBs by One Player")

    assert row["Detail"] == "Jacob Young (3); Trey Lipscomb (3); Sam Haggerty (3)"
    assert row["Score"] == "WAS 5 – 3 SF; WAS 8 – 1 SF; TEX 6 – 5 BAL"
    assert row["GameIDs"] == "SFN202404080, SFN202404090, BAL202506240"


def test_consecutive_hr_summary_preserves_duplicate_game_ids_per_event():
    processor = make_processor()
    processor.games = [
        make_summary_game("BAL200405270", "NYY", "BAL", "20040527", 18, 5),
        make_summary_game("BAL200808220", "NYY", "BAL", "20080822", 9, 4),
    ]
    processor.b2b_only_df = pd.DataFrame(
        [
            {"GameID": "BAL200808220", "Summary Detail": "Bottom 5: first pair"},
            {"GameID": "BAL200405270", "Summary Detail": "Bottom 3: early pair"},
            {"GameID": "BAL200808220", "Summary Detail": "Top 9: second pair"},
        ]
    )

    row = summary_row(processor, "Back-to-Back HR Events")

    assert row["Detail"] == "Bottom 3: early pair; Bottom 5: first pair; Top 9: second pair"
    assert row["Score"] == "NYY 18 – 5 BAL; NYY 9 – 4 BAL; NYY 9 – 4 BAL"
    assert row["GameIDs"] == "BAL200405270, BAL200808220, BAL200808220"


def test_environment_summary_keeps_scores_aligned_with_sorted_game_ids():
    processor = make_processor()
    processor.coldest_temp = 42
    processor.coldest_temp_gameids = ["BAL202506240", "SFN202404080"]
    processor.coldest_temp_scores = ["TEX 6 – 5 BAL", "WAS 5 – 3 SF"]

    row = summary_row(processor, "Coldest Game")

    assert row["Score"] == "WAS 5 – 3 SF; TEX 6 – 5 BAL"
    assert row["GameIDs"] == "SFN202404080, BAL202506240"


def test_weather_summary_sorts_game_ids_with_same_context_helper():
    class FakeWeatherTracker:
        highest_wind_games = ["BAL202506240", "SFN202404080"]
        earliest_start_games = ["BAL202506240", "SFN202404080"]
        latest_start_games = []
        precipitation_games = ["BAL202506240", "SFN202404080"]
        wind_conditions = [12, 18]

        def get_summary_stats(self):
            return {
                "highest_wind_speed": "18 mph",
                "average_wind_speed": "15 mph",
                "day_games": 1,
                "night_games": 1,
                "earliest_start": "12:05 PM",
                "latest_start": "N/A",
                "precipitation_games": 2,
                "weekend_games": 1,
                "weekday_games": 1,
            }

    processor = make_processor()
    processor.weather_tracker = FakeWeatherTracker()

    row = summary_row(processor, "Highest Wind Speed")

    assert row["GameIDs"] == "SFN202404080, BAL202506240"


def test_home_run_record_counts_multi_homer_players_from_footer():
    processor = make_processor()
    game = {
        "basic_info": {"away_team_code": "BAL", "home_team_code": "MIN"},
        "linescore": {
            "away": {"R": 15, "H": 17, "innings": ["0"] * 9},
            "home": {"R": 2, "H": 4, "innings": ["0"] * 9},
        },
        "batting": {
            "away": [
                {"name": "Austin Hays", "HR": 1},
                {"name": "Ramon Urias", "HR": 1},
                {"name": "Aaron Hicks", "HR": 1},
                {"name": "Adley Rutschman", "HR": 1},
                {"name": "Anthony Santander", "HR": 1},
            ],
            "home": [],
        },
        "footer_summary": {
            "away": {
                "HR": "Austin Hays (1); Ramon Urias (1); Aaron Hicks (1); "
                "Adley Rutschman (1); Anthony Santander 2 (2)."
            },
            "home": {},
        },
    }

    processor._process_home_run_statistics(game, "MIN202307090", game["basic_info"])

    assert processor.most_hr == 6
    assert processor.most_hr_teams == ["BAL"]
    assert processor.most_hr_gameids == ["MIN202307090"]
