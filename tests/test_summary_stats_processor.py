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
