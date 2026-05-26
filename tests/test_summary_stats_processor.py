import pandas as pd

from baseball_processor.processors.summary_stats_processor import SummaryStatsProcessor


def make_processor():
    return SummaryStatsProcessor(
        games=[],
        all_players=[],
        b2b_only_df=pd.DataFrame(),
        b2b2b_only_df=pd.DataFrame(),
        b2b2b2b_only_df=pd.DataFrame(),
        triple_play_df=pd.DataFrame(),
        hitters_df=pd.DataFrame(),
        pitchers_df=pd.DataFrame(),
        milestones={},
    )


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
