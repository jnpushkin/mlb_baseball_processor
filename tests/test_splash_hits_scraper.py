import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from baseball_processor.scrapers.splash_hits_scraper import (
    PlayerIdResolver,
    parse_splash_hits_page,
    update_splash_hits,
)


def sample_page(giants_html, visitors_html):
    payload = {
        "props": {
            "pageProps": {
                "page": {
                    "slots": {
                        "Left Rail": [
                            {
                                "slots": {
                                    "Main Column": [
                                        {"type": "heading", "headingText": "Splash Hits"},
                                        {"type": "wysiwyg", "text": giants_html},
                                        {"type": "heading", "headingText": "Other Home Runs into McCovey Cove"},
                                        {"type": "wysiwyg", "text": visitors_html},
                                    ]
                                }
                            }
                        ]
                    }
                }
            }
        }
    }
    return (
        '<html><body><script id="__NEXT_DATA__" type="application/json">'
        + json.dumps(payload)
        + "</script></body></html>"
    )


class SplashHitsScraperTests(unittest.TestCase):
    def test_parse_mlb_page_payload_and_known_row_quirks(self):
        html = sample_page(
            (
                "<p>109 Bryce Eldridge 7/9/2026 COL Ryan Feltner</p>"
                "<p>105 Heliot Ramos* 9/15/2024 SD Robert Suarez<br>"
                "<em>*First right-handed batter with a Splash Hit</em></p>"
            ),
            (
                "<p>67 Michael Busch, CHC 6/12/26 Erik Miller</p>"
                "<p>44 Rougned Odor,TEX 8/24/2018 Will Smith</p>"
                "<p>43 Matt Carpenter, STL 7/820/18 SF Ray Black</p>"
                "<p>29 Carlos, Gonzales, COL 4/11/2014 Madison Bumgarner</p>"
            ),
        )

        giants, visitors = parse_splash_hits_page(html)

        self.assertEqual(2, len(giants))
        self.assertEqual("7/9/26", giants[1]["Date"])
        self.assertEqual("Heliot Ramos*", giants[0]["Player"])
        self.assertEqual("*First right-handed batter with a Splash Hit", giants[0]["Notes"])

        self.assertEqual(4, len(visitors))
        self.assertEqual("Carlos Gonzalez", visitors[0]["Player"])
        self.assertEqual("Chicago Cubs", visitors[3]["Team"])
        self.assertEqual("2026-06-12", visitors[3]["Date"])
        self.assertEqual("Texas Rangers", visitors[2]["Team"])
        self.assertEqual("2018-07-08", visitors[1]["Date"])
        self.assertEqual("Ray Black", visitors[1]["Pitcher"])

    def test_player_id_resolver_uses_existing_csv_and_register_year(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            references = root / "refs"
            cache = root / "cache"
            register = root / "register"
            references.mkdir()
            cache.mkdir()
            (register / "data").mkdir(parents=True)

            (references / "splash_hits_all_lines.csv").write_text(
                "Splash Hit Number,Player,Date,Opponent,Pitcher,Notes,PlayerID\n"
                "106,Mike Yastrzemski,4/9/25,CIN,Emilio Pagan,,yastrmi01\n",
                encoding="utf-8",
            )
            (references / "other_mccovey_cove_hr.csv").write_text(
                "Splash Hit Number,Player,Team,Date,Pitcher,PlayerID,Date_yyyymmdd\n",
                encoding="utf-8",
            )
            (register / "data" / "people-e.csv").write_text(
                "key_bbref,name_first,name_last,name_given,mlb_played_first,mlb_played_last\n"
                "eldribr01,Bryce,Eldridge,Bryson Edward,2025,2026\n"
                "oldbr01,Bryce,Eldridge,Bryce Other,2000,2001\n",
                encoding="utf-8",
            )
            (register / "data" / "people-o.csv").write_text(
                "key_bbref,name_first,name_last,name_given,mlb_played_first,mlb_played_last\n"
                "ohtansh01,Shohei,Ohtani,Shohei,2018,2026\n",
                encoding="utf-8",
            )

            resolver = PlayerIdResolver(references, cache, register)
            resolver.add("Shohei Ohtani", "nottheright01", source="loose.json")

        self.assertEqual("yastrmi01", resolver.resolve("Mike Yastrzemski", "4/9/25"))
        self.assertEqual("eldribr01", resolver.resolve("Bryce Eldridge", "7/9/26"))
        self.assertEqual("ohtansh01", resolver.resolve("Shohei Ohtani", "7/11/25"))

    def test_update_writes_official_page_rows_with_resolved_ids(self):
        html = sample_page(
            "<p>109 Bryce Eldridge 7/9/2026 COL Ryan Feltner</p>",
            "<p>67 Michael Busch, CHC 6/12/26 Erik Miller</p>",
        )
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            refs = root / "refs"
            cache = root / "cache"
            register = root / "register"
            refs.mkdir()
            cache.mkdir()
            (register / "data").mkdir(parents=True)
            splash_path = refs / "splash_hits_all_lines.csv"
            cove_path = refs / "other_mccovey_cove_hr.csv"
            splash_path.write_text(
                "Splash Hit Number,Player,Date,Opponent,Pitcher,Notes,PlayerID\n",
                encoding="utf-8",
            )
            cove_path.write_text(
                "Splash Hit Number,Player,Team,Date,Pitcher,PlayerID,Date_yyyymmdd\n",
                encoding="utf-8",
            )
            (register / "data" / "people.csv").write_text("", encoding="utf-8")
            (register / "data" / "people-b.csv").write_text(
                "key_bbref,name_first,name_last,name_given,mlb_played_first,mlb_played_last\n"
                "buschmi02,Michael,Busch,Michael James,2023,2026\n",
                encoding="utf-8",
            )
            (register / "data" / "people-e.csv").write_text(
                "key_bbref,name_first,name_last,name_given,mlb_played_first,mlb_played_last\n"
                "eldribr01,Bryce,Eldridge,Bryson Edward,2025,2026\n",
                encoding="utf-8",
            )

            with patch(
                "baseball_processor.scrapers.splash_hits_scraper.fetch_splash_hits_page",
                return_value=html,
            ):
                result = update_splash_hits(
                    splash_hits_file=splash_path,
                    mccovey_cove_file=cove_path,
                    references_dir=refs,
                    cache_dir=cache,
                    register_dir=register,
                )

            splash_text = splash_path.read_text(encoding="utf-8")
            cove_text = cove_path.read_text(encoding="utf-8")

        self.assertEqual(1, result.giants_count)
        self.assertEqual(1, result.visitors_count)
        self.assertEqual((), result.unresolved_player_ids)
        self.assertIn("109,Bryce Eldridge,7/9/26,COL,Ryan Feltner,,eldribr01", splash_text)
        self.assertIn("67,Michael Busch,Chicago Cubs,2026-06-12,Erik Miller,buschmi02,20260612", cove_text)


if __name__ == "__main__":
    unittest.main()
