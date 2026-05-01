import unittest

from baseball_processor.parsers.play_by_play_parser import extract_play_features


class PlayByPlayParserTests(unittest.TestCase):
    def test_non_home_run_scores_word_counts_rbi(self):
        features = extract_play_features("Line drive single. Fast Runner Scores.")

        self.assertTrue(features["run_scored"])
        self.assertEqual(1, features["rbi"])

    def test_explicit_rbi_count_still_wins(self):
        features = extract_play_features(
            "Doubles on a sharp line drive. Fast Runner Scores; Other Runner Scores. 2 RBI."
        )

        self.assertTrue(features["run_scored"])
        self.assertEqual(2, features["rbi"])


if __name__ == "__main__":
    unittest.main()
