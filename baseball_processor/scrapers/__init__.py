"""
Scrapers for fetching MLB data from external sources.
"""

from .debut_scraper import scrape_debuts, save_debuts_csv, scrape_multiple_years, process_downloaded_csv

__all__ = ["scrape_debuts", "save_debuts_csv", "scrape_multiple_years", "process_downloaded_csv"]
