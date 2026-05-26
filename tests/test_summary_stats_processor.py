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
