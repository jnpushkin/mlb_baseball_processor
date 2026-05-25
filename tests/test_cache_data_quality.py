import contextlib
import io
import re
import unittest
from collections import Counter
from datetime import datetime

from baseball_processor.main import _load_games_from_cache
from baseball_processor.processors.milestones_processor import MilestonesProcessor
from baseball_processor.utils.constants import CACHE_DIR


ALLOWED_GAME_TYPES = {"regular", "postseason", "spring", "allstar"}
ALLOWED_SOURCES = {"mlb", "bref", "pdf"}
FALSE_ATTENDANCE_GAME_IDS = {"SFN202604120"}
SENTINEL_GAME_IDS = {
    "BOS202505241",
    "BOS202505242",
    "SFN202604260",
    "SFN202605220",
}


class CacheDataQualityTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        with contextlib.redirect_stdout(io.StringIO()):
            cls.games, cls.spring_count, cls.duplicates_skipped = _load_games_from_cache(CACHE_DIR)
        if not cls.games:
            raise unittest.SkipTest("Cache fixtures are not available")
        cls.games_by_id = {game.get("game_id"): game for game in cls.games}

    def test_cache_loader_returns_unique_attended_games(self):
        game_ids = [game.get("game_id") for game in self.games]

        self.assertGreaterEqual(len(game_ids), 250)
        self.assertEqual(len(game_ids), len(set(game_ids)))
        self.assertTrue(SENTINEL_GAME_IDS.issubset(set(game_ids)))
        self.assertTrue(FALSE_ATTENDANCE_GAME_IDS.isdisjoint(set(game_ids)))

    def test_loaded_games_have_required_metadata(self):
        issues = []
        for game in self.games:
            game_id = game.get("game_id")
            basic = game.get("basic_info") or {}
            source = game.get("source") or basic.get("source")
            date_text = str(basic.get("date_yyyymmdd") or "")

            if not game_id:
                issues.append((game_id, "missing game_id"))
            if source not in ALLOWED_SOURCES:
                issues.append((game_id, f"bad source {source!r}"))
            if basic.get("source") and basic.get("source") != source:
                issues.append((game_id, f"source mismatch {source!r}/{basic.get('source')!r}"))
            if not re.fullmatch(r"\d{8}", date_text):
                issues.append((game_id, f"bad date {date_text!r}"))
            else:
                try:
                    datetime.strptime(date_text, "%Y%m%d")
                except ValueError:
                    issues.append((game_id, f"invalid date {date_text!r}"))

            away = basic.get("away_team_code")
            home = basic.get("home_team_code")
            if not away or not home:
                issues.append((game_id, "missing team code"))
            elif away == home:
                issues.append((game_id, f"same team code {home!r}"))
            if not basic.get("venue"):
                issues.append((game_id, "missing venue"))
            if basic.get("game_type") not in ALLOWED_GAME_TYPES:
                issues.append((game_id, f"bad game_type {basic.get('game_type')!r}"))

            for score_field in ("away_score_value", "home_score_value"):
                score = basic.get(score_field)
                if not isinstance(score, int) or score < 0:
                    issues.append((game_id, f"bad {score_field}: {score!r}"))

        self.assertEqual([], issues)

    def test_non_pdf_games_have_box_score_player_rows_with_ids(self):
        issues = []
        for game in self.games:
            source = game.get("source") or (game.get("basic_info") or {}).get("source")
            if source == "pdf":
                continue

            for table_name in ("batting", "pitching"):
                table = game.get(table_name) or {}
                for side in ("away", "home"):
                    rows = table.get(side) or []
                    if not rows:
                        issues.append((game.get("game_id"), table_name, side, "missing rows"))
                    for row in rows:
                        if not row.get("name") or not row.get("player_id"):
                            issues.append(
                                (
                                    game.get("game_id"),
                                    table_name,
                                    side,
                                    row.get("name"),
                                    row.get("player_id"),
                                )
                            )

        self.assertEqual([], issues)

    def test_play_by_play_events_are_unique_and_end_at_final_score(self):
        issues = []
        for game in self.games:
            game_id = game.get("game_id")
            basic = game.get("basic_info") or {}
            source = game.get("source") or basic.get("source")
            raw_plays = [play for play in (game.get("raw_plays") or []) if isinstance(play, dict)]

            if source in {"mlb", "bref"} and basic.get("game_type") != "spring" and not raw_plays:
                issues.append((game_id, "missing raw play data"))
                continue

            play_keys = [
                (
                    play.get("inning"),
                    play.get("half"),
                    play.get("batter"),
                    play.get("pitcher"),
                    play.get("event"),
                    play.get("description"),
                )
                for play in raw_plays
            ]
            duplicate_keys = [key for key, count in Counter(play_keys).items() if count > 1]
            if duplicate_keys:
                issues.append((game_id, "duplicate play events", duplicate_keys[:3]))

            if basic.get("game_type") == "spring":
                continue

            scored_plays = [
                play
                for play in raw_plays
                if isinstance(play.get("away_score"), int) and isinstance(play.get("home_score"), int)
            ]
            if scored_plays:
                last_play = scored_plays[-1]
                final_score = (basic.get("away_score_value"), basic.get("home_score_value"))
                play_score = (last_play.get("away_score"), last_play.get("home_score"))
                if play_score != final_score:
                    issues.append((game_id, "play-by-play final score mismatch", play_score, final_score))

        self.assertEqual([], issues)

    def test_known_api_priority_game_does_not_include_pitcher_batting_placeholder(self):
        game = self.games_by_id["SFN202604260"]

        away_batters = {row.get("name") for row in game.get("batting", {}).get("away", [])}
        away_pitchers = {row.get("name") for row in game.get("pitching", {}).get("away", [])}

        self.assertNotIn("Max Meyer", away_batters)
        self.assertIn("Max Meyer", away_pitchers)

    def test_processed_milestones_exclude_removed_categories(self):
        with contextlib.redirect_stdout(io.StringIO()):
            milestones, *_ = MilestonesProcessor(self.games).process_all_milestones()

        self.assertNotIn("Scoreless Relief", milestones)
        self.assertNotIn("scoreless_relief", milestones)
        self.assertEqual(22, len(milestones["Multi-SB Games"]))


if __name__ == "__main__":
    unittest.main()
