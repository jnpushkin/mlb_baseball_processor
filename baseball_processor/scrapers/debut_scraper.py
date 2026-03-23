"""
MLB Debuts Scraper
==================
Scrapes MLB debut data from Baseball-Reference and saves to CSV format
compatible with the baseball_processor debut tracking system.

Usage:
    python -m baseball_processor.scrapers.debut_scraper 2025
    python -m baseball_processor.scrapers.debut_scraper 2025 --output /path/to/output/

Requirements:
    pip install requests beautifulsoup4 pandas
"""

import argparse
import os
import sys
import time
from pathlib import Path
from datetime import datetime

try:
    from bs4 import BeautifulSoup
    import pandas as pd
except ImportError as e:
    print(f"Missing required package: {e}")
    print("Install with: pip install beautifulsoup4 pandas")
    sys.exit(1)

# Try to import cloudscraper for Cloudflare bypass, fall back to requests
try:
    import cloudscraper
    HAS_CLOUDSCRAPER = True
except ImportError:
    import requests
    HAS_CLOUDSCRAPER = False

from ..utils.http import create_retry_session, get_with_retry

_session = create_retry_session()


def scrape_debuts(year: int, verbose: bool = True) -> pd.DataFrame:
    """
    Scrape MLB debut data from Baseball-Reference for a given year.

    Args:
        year: The year to scrape (e.g., 2025)
        verbose: Whether to print progress messages

    Returns:
        DataFrame with debut data
    """
    url = f"https://www.baseball-reference.com/leagues/majors/{year}-debuts.shtml"

    if verbose:
        print(f"Fetching {url}...")
        if HAS_CLOUDSCRAPER:
            print("Using cloudscraper for Cloudflare bypass...")
        else:
            print("Note: Install 'cloudscraper' for better success: pip install cloudscraper")

    try:
        if HAS_CLOUDSCRAPER:
            # Use cloudscraper to bypass Cloudflare
            scraper = cloudscraper.create_scraper(
                browser={
                    'browser': 'chrome',
                    'platform': 'darwin',
                    'desktop': True
                }
            )
            response = scraper.get(url, timeout=30)
        else:
            # Fallback to regular requests with headers
            headers = {
                "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
                "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
                "Accept-Language": "en-US,en;q=0.5",
                "Accept-Encoding": "gzip, deflate, br",
                "Connection": "keep-alive",
                "Upgrade-Insecure-Requests": "1",
            }
            response = get_with_retry(_session, url, headers=headers, timeout=30)

        response.raise_for_status()

    except Exception as e:
        print(f"Error fetching data: {e}")
        print("\nNote: Baseball-Reference may block automated requests.")
        if not HAS_CLOUDSCRAPER:
            print("Try installing cloudscraper: pip install cloudscraper")
        print("\nAlternative approach: Download the CSV manually from:")
        print(f"  1. Go to: {url}")
        print(f"  2. Click 'Share & Export' -> 'Get table as CSV'")
        print(f"  3. Save as '{year} MLB Debuts.csv' in mlb_references folder")
        return pd.DataFrame()

    if verbose:
        print("Parsing HTML...")

    soup = BeautifulSoup(response.text, "html.parser")

    # Find the debuts table (typically has id "misc_bio")
    table = soup.find("table", {"id": "misc_bio"})
    if not table:
        # Try alternate table IDs
        table = soup.find("table", class_="sortable")

    if not table:
        print("Could not find debuts table on page")
        return pd.DataFrame()

    # Parse table headers
    headers_row = table.find("thead")
    if headers_row:
        header_cells = headers_row.find_all("th")
        columns = [th.get_text(strip=True) for th in header_cells]
    else:
        # Default columns if header not found
        columns = [
            "Rk", "Name", "Age", "Debut", "Last Game", "Pos", "Tm", "WAR",
            "Ht", "Wt", "B", "T", "Birthdate", "Birthplace", "Draft/Signing",
            "Schools", "High School", "Given Name", "Name-additional"
        ]

    # Parse table rows
    rows = []
    tbody = table.find("tbody")
    if tbody:
        for tr in tbody.find_all("tr"):
            # Skip header rows or spacer rows
            if tr.get("class") and "thead" in tr.get("class"):
                continue

            cells = tr.find_all(["th", "td"])
            if not cells:
                continue

            row_data = {}
            for i, cell in enumerate(cells):
                if i < len(columns):
                    col_name = columns[i]

                    # Get text content
                    text = cell.get_text(strip=True)

                    # For Name column, also extract player ID from link
                    if col_name == "Name":
                        link = cell.find("a")
                        if link and link.get("href"):
                            href = link.get("href")
                            # Extract player ID from URL like "/players/a/abelmi01.shtml"
                            if "/players/" in href:
                                player_id = href.split("/")[-1].replace(".shtml", "")
                                row_data["Name-additional"] = player_id

                    row_data[col_name] = text

            if row_data:
                rows.append(row_data)

    if verbose:
        print(f"Found {len(rows)} debut entries")

    df = pd.DataFrame(rows)

    # Ensure Name-additional column exists
    if "Name-additional" not in df.columns:
        df["Name-additional"] = ""

    return df


def process_downloaded_csv(input_file: str, year: int = None, output_dir: str = None) -> str:
    """
    Process a manually downloaded CSV from Baseball-Reference and save it
    in the correct format for the baseball_processor.

    Baseball-Reference CSV export includes all the columns we need.
    Simply download the CSV from their site and run through this function.

    Args:
        input_file: Path to downloaded CSV file
        year: Year for output filename (inferred from data if not provided)
        output_dir: Output directory (default: mlb_references)

    Returns:
        Path to saved file
    """
    print(f"Processing {input_file}...")

    df = pd.read_csv(input_file)

    print(f"Loaded {len(df)} entries")

    # If year not provided, try to infer from debut dates
    if year is None:
        try:
            # Try to get year from first debut date
            sample_debut = str(df["Debut"].iloc[0])
            # Dates are like "May 18" - we need the year from filename or user
            print("Warning: Year not specified. Please provide the year parameter.")
            year = datetime.now().year
        except Exception:
            year = datetime.now().year

    return save_debuts_csv(df, year, output_dir)


def save_debuts_csv(df: pd.DataFrame, year: int, output_dir: str = None) -> str:
    """
    Save debut DataFrame to CSV in the expected format.

    Args:
        df: DataFrame with debut data
        year: Year for filename
        output_dir: Directory to save file (default: mlb_references)

    Returns:
        Path to saved file
    """
    if output_dir is None:
        # Default to mlb_references folder
        script_dir = Path(__file__).parent.parent.parent
        output_dir = script_dir / "mlb_references"
    else:
        output_dir = Path(output_dir)

    output_dir.mkdir(parents=True, exist_ok=True)

    filename = f"{year} MLB Debuts.csv"
    filepath = output_dir / filename

    # Ensure columns are in the right order
    expected_columns = [
        "Rk", "Name", "Age", "Debut", "Last Game", "Pos", "Tm", "WAR",
        "Ht", "Wt", "B", "T", "Birthdate", "Birthplace", "Draft/Signing",
        "Schools", "High School", "Given Name", "Name-additional"
    ]

    # Add missing columns with empty values
    for col in expected_columns:
        if col not in df.columns:
            df[col] = ""

    # Reorder columns
    df = df[[col for col in expected_columns if col in df.columns]]

    df.to_csv(filepath, index=False)

    return str(filepath)


def scrape_multiple_years(start_year: int, end_year: int, output_dir: str = None,
                          delay: float = 2.0, verbose: bool = True):
    """
    Scrape debut data for multiple years.

    Args:
        start_year: First year to scrape
        end_year: Last year to scrape (inclusive)
        output_dir: Directory to save files
        delay: Seconds to wait between requests (be nice to the server)
        verbose: Whether to print progress
    """
    for year in range(start_year, end_year + 1):
        if verbose:
            print(f"\n{'='*50}")
            print(f"Scraping {year} debuts...")
            print(f"{'='*50}")

        df = scrape_debuts(year, verbose=verbose)

        if df.empty:
            print(f"No data found for {year}, skipping")
            continue

        filepath = save_debuts_csv(df, year, output_dir)
        print(f"Saved: {filepath}")

        # Be nice to the server
        if year < end_year:
            if verbose:
                print(f"Waiting {delay}s before next request...")
            time.sleep(delay)


def main():
    parser = argparse.ArgumentParser(
        description="Scrape MLB debut data from Baseball-Reference",
        epilog="""
Examples:
    # Scrape 2025 debuts (may be blocked by site)
    python -m baseball_processor.scrapers.debut_scraper 2025

    # Process manually downloaded CSV (recommended approach)
    python -m baseball_processor.scrapers.debut_scraper 2026 --from-csv ~/Downloads/debuts.csv

    # Scrape range of years
    python -m baseball_processor.scrapers.debut_scraper 2020 2025

    # Scrape to specific directory
    python -m baseball_processor.scrapers.debut_scraper 2025 --output ./data/

Manual Download Instructions (if scraping is blocked):
    1. Go to: https://www.baseball-reference.com/leagues/majors/YEAR-debuts.shtml
    2. Click "Share & Export" button above the table
    3. Select "Get table as CSV"
    4. Save the file and run: --from-csv /path/to/file.csv
        """
    )

    parser.add_argument(
        "year",
        type=int,
        help="Year for the debut data (e.g., 2025)"
    )

    parser.add_argument(
        "end_year",
        type=int,
        nargs="?",
        default=None,
        help="End year for range (optional, e.g., '2020 2025' scrapes 2020-2025)"
    )

    parser.add_argument(
        "--from-csv", "-f",
        type=str,
        default=None,
        dest="from_csv",
        help="Process a manually downloaded CSV file instead of scraping"
    )

    parser.add_argument(
        "--output", "-o",
        type=str,
        default=None,
        help="Output directory (default: mlb_references folder)"
    )

    parser.add_argument(
        "--delay", "-d",
        type=float,
        default=2.0,
        help="Delay between requests in seconds (default: 2.0)"
    )

    parser.add_argument(
        "--quiet", "-q",
        action="store_true",
        help="Suppress progress messages"
    )

    args = parser.parse_args()

    verbose = not args.quiet

    # If processing from CSV, use that instead of scraping
    if args.from_csv:
        if not os.path.exists(args.from_csv):
            print(f"Error: File not found: {args.from_csv}")
            sys.exit(1)

        filepath = process_downloaded_csv(args.from_csv, args.year, args.output)
        print(f"\nSaved: {filepath}")
        return

    if args.end_year:
        # Scrape range of years
        scrape_multiple_years(
            args.year,
            args.end_year,
            args.output,
            args.delay,
            verbose
        )
    else:
        # Scrape single year
        df = scrape_debuts(args.year, verbose=verbose)

        if df.empty:
            print("No data found")
            sys.exit(1)

        filepath = save_debuts_csv(df, args.year, args.output)
        print(f"\nSaved: {filepath}")
        print(f"Total entries: {len(df)}")


if __name__ == "__main__":
    main()
