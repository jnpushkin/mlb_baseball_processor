"""
All-Time Leaders Scraper
========================
Scrapes Baseball-Reference career leaderboards for major batting and pitching stats.
Outputs JSON files to mlb_references/all_time_leaders/ for use in detecting when
players pass others on all-time lists.

Usage:
    python3 -m baseball_processor.scrapers.all_time_leaders_scraper
    python3 -m baseball_processor.scrapers.all_time_leaders_scraper --stat saves
    python3 -m baseball_processor.scrapers.all_time_leaders_scraper --type pitching

Requirements:
    pip install requests beautifulsoup4
"""

import argparse
import json
import os
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import Optional

try:
    from bs4 import BeautifulSoup, Comment
except ImportError as e:
    print(f"Missing required package: {e}")
    print("Install with: pip install beautifulsoup4")
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


# All-time leaderboard configurations
# Maps our stat key to Baseball Reference URL path and column name
BATTING_STATS = {
    'H': {
        'url_path': 'leaders/H_career.shtml',
        'stat_name': 'Hits',
        'column': 'H',
    },
    'HR': {
        'url_path': 'leaders/HR_career.shtml',
        'stat_name': 'Home Runs',
        'column': 'HR',
    },
    'RBI': {
        'url_path': 'leaders/RBI_career.shtml',
        'stat_name': 'RBIs',
        'column': 'RBI',
    },
    'R': {
        'url_path': 'leaders/R_career.shtml',
        'stat_name': 'Runs',
        'column': 'R',
    },
    '2B': {
        'url_path': 'leaders/2B_career.shtml',
        'stat_name': 'Doubles',
        'column': '2B',
    },
    '3B': {
        'url_path': 'leaders/3B_career.shtml',
        'stat_name': 'Triples',
        'column': '3B',
    },
    'SB': {
        'url_path': 'leaders/SB_career.shtml',
        'stat_name': 'Stolen Bases',
        'column': 'SB',
    },
    'BB': {
        'url_path': 'leaders/BB_career.shtml',
        'stat_name': 'Walks',
        'column': 'BB',
    },
    'TB': {
        'url_path': 'leaders/TB_career.shtml',
        'stat_name': 'Total Bases',
        'column': 'TB',
    },
    'G': {
        'url_path': 'leaders/G_career.shtml',
        'stat_name': 'Games',
        'column': 'G',
    },
}

PITCHING_STATS = {
    'SV': {
        'url_path': 'leaders/SV_career.shtml',
        'stat_name': 'Saves',
        'column': 'SV',
    },
    'W': {
        'url_path': 'leaders/W_career.shtml',
        'stat_name': 'Wins',
        'column': 'W',
    },
    'SO': {
        'url_path': 'leaders/SO_p_career.shtml',
        'stat_name': 'Strikeouts',
        'column': 'SO',
    },
    'IP': {
        'url_path': 'leaders/IP_career.shtml',
        'stat_name': 'Innings Pitched',
        'column': 'IP',
    },
    'G_pitch': {
        'url_path': 'leaders/G_p_career.shtml',
        'stat_name': 'Games (Pitching)',
        'column': 'G',
    },
    'GS': {
        'url_path': 'leaders/GS_career.shtml',
        'stat_name': 'Games Started',
        'column': 'GS',
    },
    'CG': {
        'url_path': 'leaders/CG_career.shtml',
        'stat_name': 'Complete Games',
        'column': 'CG',
    },
    'SHO': {
        'url_path': 'leaders/SHO_career.shtml',
        'stat_name': 'Shutouts',
        'column': 'SHO',
    },
}

# Map stat keys to output filenames
STAT_TO_FILENAME = {
    # Batting
    'H': 'batting_hits.json',
    'HR': 'batting_home_runs.json',
    'RBI': 'batting_rbi.json',
    'R': 'batting_runs.json',
    '2B': 'batting_doubles.json',
    '3B': 'batting_triples.json',
    'SB': 'batting_stolen_bases.json',
    'BB': 'batting_walks.json',
    'TB': 'batting_total_bases.json',
    'G': 'batting_games.json',
    # Pitching
    'SV': 'pitching_saves.json',
    'W': 'pitching_wins.json',
    'SO': 'pitching_strikeouts.json',
    'IP': 'pitching_innings.json',
    'G_pitch': 'pitching_games.json',
    'GS': 'pitching_games_started.json',
    'CG': 'pitching_complete_games.json',
    'SHO': 'pitching_shutouts.json',
}


def get_project_root() -> Path:
    """Get the project root directory."""
    current = Path(__file__).resolve()
    for parent in [current] + list(current.parents):
        if (parent / '.project_root').exists():
            return parent
        if (parent / 'baseball_processor').is_dir():
            return parent
    return Path.cwd()


def get_output_dir() -> Path:
    """Get the output directory for all-time leaders JSON files."""
    return get_project_root() / 'mlb_references' / 'all_time_leaders'


class RateLimitError(Exception):
    """Raised when Baseball-Reference rate limits us."""
    pass


def create_scraper():
    """Create an HTTP scraper (cloudscraper or requests)."""
    if HAS_CLOUDSCRAPER:
        return cloudscraper.create_scraper(
            browser={
                'browser': 'chrome',
                'platform': 'darwin',
                'desktop': True
            }
        )
    return None


def fetch_url(url: str, scraper=None, timeout: int = 30, max_retries: int = 3) -> Optional[str]:
    """
    Fetch a URL with appropriate headers and retry logic.

    Raises:
        RateLimitError: When rate limited (429, 403, or suspected blocking)
    """
    last_error = None

    for attempt in range(max_retries):
        try:
            if scraper and HAS_CLOUDSCRAPER:
                response = scraper.get(url, timeout=timeout)
            else:
                headers = {
                    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36",
                    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
                    "Accept-Language": "en-US,en;q=0.5",
                }
                response = get_with_retry(_session, url, headers=headers, timeout=timeout)

            if response.status_code == 429:
                raise RateLimitError("Rate limited (429 Too Many Requests)")

            if response.status_code == 403:
                if 'cloudflare' in response.text.lower() or 'captcha' in response.text.lower():
                    raise RateLimitError("Blocked by Cloudflare/CAPTCHA (403)")
                raise RateLimitError("Access forbidden (403) - likely rate limited")

            if response.status_code == 503:
                raise RateLimitError("Service unavailable (503)")

            response.raise_for_status()

            content = response.text
            rate_limit_indicators = [
                'rate limit', 'too many requests', 'slow down',
                'blocked', 'captcha', 'please wait', 'access denied'
            ]
            content_lower = content.lower()
            for indicator in rate_limit_indicators:
                if indicator in content_lower and len(content) < 5000:
                    raise RateLimitError(f"Rate limit detected: '{indicator}'")

            return content

        except RateLimitError:
            raise
        except Exception as e:
            last_error = e
            error_str = str(e).lower()
            if '429' in error_str or '403' in error_str or 'forbidden' in error_str:
                raise RateLimitError(f"Rate limited: {e}")

            if attempt < max_retries - 1:
                wait_time = (attempt + 1) * 5
                print(f"    Connection error, retrying in {wait_time}s... ({attempt + 1}/{max_retries})")
                time.sleep(wait_time)
            else:
                print(f"  Error fetching {url}: {e}")
                return None

    return None


def scrape_leaderboard(stat_key: str, config: dict, scraper=None, top_n: int = 200, verbose: bool = True) -> dict:
    """
    Scrape a single career leaderboard from Baseball Reference.

    Args:
        stat_key: The stat key (e.g., 'HR', 'SV')
        config: Dict with url_path, stat_name, column
        scraper: HTTP scraper instance
        top_n: Number of leaders to include (default 200)
        verbose: Print progress

    Returns:
        Dict with leaderboard data
    """
    url = f"https://www.baseball-reference.com/{config['url_path']}"

    if verbose:
        print(f"  Scraping {config['stat_name']} leaderboard...")

    html = fetch_url(url, scraper)
    if not html:
        print(f"    Failed to fetch {url}")
        return {}

    soup = BeautifulSoup(html, 'html.parser')

    # Baseball Reference often hides tables in HTML comments for lazy loading
    # Look for commented-out tables and parse them
    comments = soup.find_all(string=lambda text: isinstance(text, Comment))
    for comment in comments:
        if 'table' in comment and ('leaders' in comment or config['column'] in comment):
            comment_soup = BeautifulSoup(comment, 'html.parser')
            table = comment_soup.find('table')
            if table:
                soup = comment_soup
                break

    # Find the leaderboard table - try specific ID patterns first
    table = soup.find('table', {'id': lambda x: x and 'leader' in x.lower()}) or \
            soup.find('table', class_='stats_table') or \
            soup.find('table')

    if not table:
        print(f"    Could not find leaderboard table for {stat_key}")
        return {}

    leaders = []
    last_rank = 0  # Track last valid rank for handling ties

    # Get all rows (skip header row)
    all_rows = table.find_all('tr')
    data_rows = all_rows[1:] if all_rows else []  # Skip header row

    for row in data_rows:
        row_class = row.get('class', [])
        if 'thead' in row_class or 'spacer' in row_class:
            continue

        cells = row.find_all('td')
        if len(cells) < 3:
            continue

        # BREF leaderboard structure:
        # td[0]: rank (e.g., "1.") - may be empty for ties
        # td[1]: player name with link
        # td[2]: stat value

        # Get rank from first cell (handle ties where cell is empty)
        rank_text = cells[0].get_text(strip=True)
        try:
            rank = int(rank_text.replace('.', '').replace(',', ''))
            last_rank = rank
        except (ValueError, AttributeError):
            # Empty rank cell means tied with previous player
            if last_rank > 0:
                rank = last_rank
            else:
                continue

        # Stop after top_n
        if rank > top_n:
            break

        # Get player name and ID from second cell
        player_cell = cells[1]
        player_name = ""
        player_id = ""

        link = player_cell.find('a')
        if link:
            player_name = link.get_text(strip=True)
            href = link.get('href', '')
            # Extract player_id from href like /players/r/riverma01.shtml
            if '/players/' in href:
                player_id = href.split('/')[-1].replace('.shtml', '')
        else:
            player_name = player_cell.get_text(strip=True)

        # Clean up player name (remove years in parentheses, HOF markers like +)
        if '(' in player_name:
            player_name = player_name.split('(')[0].strip()
        player_name = player_name.rstrip('+*')

        # Get stat value from third cell
        stat_text = cells[2].get_text(strip=True).replace(',', '')
        try:
            # Handle IP which can be like "5941.1"
            stat_value = float(stat_text) if '.' in stat_text else int(stat_text)
        except ValueError:
            continue

        # Only add if we have valid data
        if player_name and stat_value > 0:
            leaders.append({
                'rank': rank,
                'player_id': player_id,
                'name': player_name,
                'value': stat_value,
            })

    if verbose:
        print(f"    Found {len(leaders)} leaders")

    stat_type = 'batting' if stat_key in BATTING_STATS else 'pitching'

    return {
        'stat': stat_key,
        'stat_name': config['stat_name'],
        'type': stat_type,
        'last_updated': datetime.now().strftime('%Y-%m-%d'),
        'leaders': leaders,
    }


def save_leaderboard(stat_key: str, data: dict, verbose: bool = True):
    """Save leaderboard data to JSON file."""
    output_dir = get_output_dir()
    output_dir.mkdir(parents=True, exist_ok=True)

    filename = STAT_TO_FILENAME.get(stat_key, f'{stat_key.lower()}.json')
    filepath = output_dir / filename

    with open(filepath, 'w') as f:
        json.dump(data, f, indent=2)

    if verbose:
        print(f"    Saved to {filepath}")


def scrape_all_leaderboards(
    stat_type: str = 'all',
    specific_stat: str = None,
    delay: float = 3.1,
    top_n: int = 200,
    verbose: bool = True
) -> dict:
    """
    Scrape all requested leaderboards.

    Args:
        stat_type: 'all', 'batting', or 'pitching'
        specific_stat: Scrape only this stat (e.g., 'HR', 'SV')
        delay: Delay between requests (seconds)
        top_n: Number of leaders per stat
        verbose: Print progress

    Returns:
        Dict mapping stat key to leaderboard data
    """
    scraper = create_scraper()
    results = {}

    # Build list of stats to scrape
    stats_to_scrape = {}

    if specific_stat:
        if specific_stat in BATTING_STATS:
            stats_to_scrape[specific_stat] = ('batting', BATTING_STATS[specific_stat])
        elif specific_stat in PITCHING_STATS:
            stats_to_scrape[specific_stat] = ('pitching', PITCHING_STATS[specific_stat])
        else:
            print(f"Unknown stat: {specific_stat}")
            print(f"Available batting stats: {list(BATTING_STATS.keys())}")
            print(f"Available pitching stats: {list(PITCHING_STATS.keys())}")
            return {}
    else:
        if stat_type in ('all', 'batting'):
            for key, config in BATTING_STATS.items():
                stats_to_scrape[key] = ('batting', config)
        if stat_type in ('all', 'pitching'):
            for key, config in PITCHING_STATS.items():
                stats_to_scrape[key] = ('pitching', config)

    total = len(stats_to_scrape)

    for i, (stat_key, (stype, config)) in enumerate(stats_to_scrape.items(), 1):
        if verbose:
            print(f"\n[{i}/{total}] {config['stat_name']} ({stype})")

        try:
            data = scrape_leaderboard(stat_key, config, scraper, top_n, verbose)

            if data and data.get('leaders'):
                results[stat_key] = data
                save_leaderboard(stat_key, data, verbose)

            if i < total:
                if verbose:
                    print(f"    Waiting {delay}s...")
                time.sleep(delay)

        except RateLimitError as e:
            print(f"\n{'='*60}")
            print(f"RATE LIMITED: {e}")
            print(f"{'='*60}")
            print(f"\nProgress saved. Wait 10-15 minutes before retrying.")
            print(f"Completed {i-1}/{total} stats.")
            break

        except Exception as e:
            print(f"    Error scraping {stat_key}: {e}")
            continue

    return results


def main():
    parser = argparse.ArgumentParser(
        description="Scrape MLB all-time career leaderboards from Baseball Reference",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
    # Scrape all leaderboards (18 stats)
    python3 -m baseball_processor.scrapers.all_time_leaders_scraper

    # Scrape only batting stats
    python3 -m baseball_processor.scrapers.all_time_leaders_scraper --type batting

    # Scrape only pitching stats
    python3 -m baseball_processor.scrapers.all_time_leaders_scraper --type pitching

    # Scrape a specific stat
    python3 -m baseball_processor.scrapers.all_time_leaders_scraper --stat SV
    python3 -m baseball_processor.scrapers.all_time_leaders_scraper --stat HR

Available stats:
  Batting: H, HR, RBI, R, 2B, 3B, SB, BB, TB, G
  Pitching: SV, W, SO, IP, G_pitch, GS, CG, SHO
        """
    )

    parser.add_argument(
        '--type', '-t',
        choices=['all', 'batting', 'pitching'],
        default='all',
        help="Type of stats to scrape (default: all)"
    )

    parser.add_argument(
        '--stat', '-s',
        type=str,
        help="Scrape only this specific stat (e.g., HR, SV)"
    )

    parser.add_argument(
        '--delay', '-d',
        type=float,
        default=3.1,
        help="Delay between requests in seconds (default: 3.1)"
    )

    parser.add_argument(
        '--top', '-n',
        type=int,
        default=200,
        help="Number of leaders to include per stat (default: 200)"
    )

    parser.add_argument(
        '--quiet', '-q',
        action='store_true',
        help="Suppress progress messages"
    )

    args = parser.parse_args()
    verbose = not args.quiet

    if verbose:
        print("="*60)
        print("MLB All-Time Leaders Scraper")
        print("="*60)
        print(f"\nOutput directory: {get_output_dir()}")
        print(f"Delay between requests: {args.delay}s")
        print(f"Top N leaders: {args.top}")

    results = scrape_all_leaderboards(
        stat_type=args.type,
        specific_stat=args.stat,
        delay=args.delay,
        top_n=args.top,
        verbose=verbose
    )

    if verbose:
        print(f"\n{'='*60}")
        print(f"Scraping complete!")
        print(f"{'='*60}")
        print(f"Scraped {len(results)} leaderboards")

        total_leaders = sum(len(d.get('leaders', [])) for d in results.values())
        print(f"Total leaders: {total_leaders}")
        print(f"\nFiles saved to: {get_output_dir()}")


if __name__ == "__main__":
    main()
