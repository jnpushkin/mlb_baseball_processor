import baseball_processor.scrapers.career_firsts_scraper as career_firsts_scraper


def test_get_mlb_id_from_register_accepts_dotted_bref_ids():
    old_cache = career_firsts_scraper._register_to_mlb_id_cache
    old_cache_loaded = career_firsts_scraper._register_cache_loaded
    old_load = career_firsts_scraper._load_register_cache
    old_save = career_firsts_scraper._save_register_cache
    old_fetch_url = career_firsts_scraper.fetch_url
    career_firsts_scraper._register_to_mlb_id_cache = {}
    career_firsts_scraper._register_cache_loaded = True
    career_firsts_scraper._load_register_cache = lambda: None
    career_firsts_scraper._save_register_cache = lambda: None
    career_firsts_scraper.fetch_url = lambda *_args, **_kwargs: """
        <a href="/players/gl.fcgi?id=dicker.01&amp;t=b&amp;year=2012">Batting Game Log</a>
    """

    try:
        assert career_firsts_scraper.get_mlb_id_from_register("dickra000ra") == "dicker.01"
    finally:
        career_firsts_scraper._register_to_mlb_id_cache = old_cache
        career_firsts_scraper._register_cache_loaded = old_cache_loaded
        career_firsts_scraper._load_register_cache = old_load
        career_firsts_scraper._save_register_cache = old_save
        career_firsts_scraper.fetch_url = old_fetch_url
