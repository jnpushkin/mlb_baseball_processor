"""
Career Firsts Scraper
=====================
Scrapes Baseball-Reference game logs to identify when players achieved
career firsts (first hit, first HR, first RBI, etc.) and checks if any
were witnessed at attended games.

Usage:
    python -m baseball_processor.scrapers.career_firsts_scraper
    python -m baseball_processor.scrapers.career_firsts_scraper --player raleica01
    python -m baseball_processor.scrapers.career_firsts_scraper --refresh

Requirements:
    pip install requests beautifulsoup4 pandas
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
    from bs4 import BeautifulSoup
    import pandas as pd
except ImportError as e:
    print(f"Missing required package: {e}")
    print("Install with: pip install beautifulsoup4 pandas")
    sys.exit(1)

# Try to import cloudscraper for Cloudflare bypass, fall back to requests
import requests

try:
    import cloudscraper
    HAS_CLOUDSCRAPER = True
except ImportError:
    HAS_CLOUDSCRAPER = False


def parse_ip(ip_str: str) -> float:
    """
    Convert baseball IP notation to decimal innings.
    In baseball: 6.1 = 6⅓ innings, 6.2 = 6⅔ innings
    """
    try:
        ip = float(ip_str)
        whole = int(ip)
        fraction = ip - whole
        # Convert .1 -> 1/3, .2 -> 2/3
        if abs(fraction - 0.1) < 0.01:
            return whole + 1/3
        elif abs(fraction - 0.2) < 0.01:
            return whole + 2/3
        else:
            return ip  # Already decimal or whole number
    except (ValueError, TypeError):
        return 0.0


# Career first milestones to track
BATTING_FIRSTS = {
    'H': 'First Career Hit',
    'HR': 'First Career Home Run',
    'RBI': 'First Career RBI',
    '2B': 'First Career Double',
    '3B': 'First Career Triple',
    'BB': 'First Career Walk',
    'SB': 'First Career Stolen Base',
    'R': 'First Career Run Scored',
}

PITCHING_FIRSTS = {
    'W': 'First Career Win',
    'SV': 'First Career Save',
    'SO': 'First Career Strikeout',
    'IP': 'First Career Inning Pitched',
    'GS': 'First Career Start',
    'CG': 'First Career Complete Game',
    'SHO': 'First Career Shutout',
}

# Career milestone thresholds to track (granular - every 100 for most stats)
BATTING_MILESTONES = {
    'H': sorted(set([10, 25, 50] + list(range(100, 4100, 100)))),  # 10, 25, 50, 100, 200... 4000
    'HR': sorted(set([10, 25, 50, 75] + list(range(100, 900, 100)))),  # 10, 25, 50, 75, 100, 200... 800
    'RBI': sorted(set([10, 25, 50] + list(range(100, 2100, 100)))),  # 10, 25, 50, 100, 200... 2000
    '2B': sorted(set([10, 25, 50] + list(range(100, 800, 100)))),  # 10, 25, 50, 100, 200... 700
    '3B': sorted(set([10, 25, 50, 75] + list(range(100, 300, 100)))),  # 10, 25, 50, 75, 100, 200
    'SB': sorted(set([10, 25, 50] + list(range(100, 900, 100)))),  # 10, 25, 50, 100, 200... 800
    'BB': sorted(set([10, 25, 50] + list(range(100, 2600, 100)))),  # 10, 25, 50, 100, 200... 2500
    'R': sorted(set([10, 25, 50] + list(range(100, 2400, 100)))),  # 10, 25, 50, 100, 200... 2300
    'TB': sorted(set([10, 25, 50, 100, 250] + list(range(500, 6500, 500)))),  # 10, 25, 50, 100, 250, 500, 1000... 6000
    'G': sorted(set([10, 25, 50, 100, 250] + list(range(500, 3500, 500)))),  # 10, 25, 50, 100, 250, 500, 1000... 3000
}

PITCHING_MILESTONES = {
    'W': sorted(set([10, 25, 50, 75] + list(range(100, 400, 100)))),  # 10, 25, 50, 75, 100, 200, 300
    'SV': sorted(set([10, 25, 50] + list(range(100, 700, 100)))),  # 10, 25, 50, 100, 200... 600
    'SO': sorted(set([10, 25, 50, 100, 250] + list(range(500, 4000, 500)))),  # 10, 25, 50, 100, 250, 500, 1000... 3500
    'IP': sorted(set([10, 25, 50, 100, 250] + list(range(500, 4000, 500)))),  # 10, 25, 50, 100, 250, 500, 1000... 3500
    'G': sorted(set([10, 25, 50, 100, 250] + list(range(500, 1500, 500)))),  # 10, 25, 50, 100, 250, 500, 1000
    'GS': sorted(set([10, 25, 50] + list(range(100, 600, 100)))),  # 10, 25, 50, 100, 200... 500
    'CG': sorted(set([10, 25, 50, 75] + list(range(100, 200, 100)))),  # 10, 25, 50, 75, 100
    'SHO': sorted(set([10, 25, 50, 75] + list(range(100, 200, 100)))),  # 10, 25, 50, 75, 100
}

# Milestone display names
STAT_NAMES = {
    'H': 'Hit', 'HR': 'Home Run', 'RBI': 'RBI', '2B': 'Double', '3B': 'Triple',
    'BB': 'Walk', 'SB': 'Stolen Base', 'R': 'Run', 'TB': 'Total Base', 'G': 'Game',
    'W': 'Win', 'SV': 'Save', 'SO': 'Strikeout', 'IP': 'Inning Pitched',
    'GS': 'Start', 'CG': 'Complete Game', 'SHO': 'Shutout',
}


def get_project_root() -> Path:
    """Get the project root directory."""
    # Check for .project_root marker file
    current = Path(__file__).resolve()
    for parent in [current] + list(current.parents):
        if (parent / '.project_root').exists():
            return parent
        if (parent / 'baseball_processor').is_dir():
            return parent
    return Path.cwd()


def get_cache_path() -> Path:
    """Get the cache directory path."""
    return get_project_root() / 'cache' / 'career_firsts'


def get_gamelogs_cache_path() -> Path:
    """Get the career gamelogs cache file path."""
    return get_project_root() / 'cache' / 'career_gamelogs.json'


def load_gamelogs_cache() -> dict:
    """Load the career gamelogs cache (cumulative totals per game)."""
    cache_file = get_gamelogs_cache_path()
    if cache_file.exists():
        with open(cache_file, 'r', encoding='utf-8') as f:
            return json.load(f)
    return {}


def save_gamelogs_cache(cache: dict):
    """Save the career gamelogs cache to disk."""
    cache_file = get_gamelogs_cache_path()
    with open(cache_file, 'w', encoding='utf-8') as f:
        json.dump(cache, f, ensure_ascii=False)
    print(f"  Saved gamelogs cache: {cache_file}")


def load_all_time_leaders() -> dict:
    """Load all-time leaders from JSON files.

    Returns dict mapping player_id -> {name, stats: [{stat, rank, value}], type}
    """
    leaders_dir = get_project_root() / 'mlb_references' / 'all_time_leaders'
    all_leaders = {}

    if not leaders_dir.exists():
        return all_leaders

    for json_file in leaders_dir.glob('*.json'):
        try:
            with open(json_file) as f:
                data = json.load(f)
                stat = data.get('stat', '')
                stat_type = data.get('type', '')
                for leader in data.get('leaders', []):
                    pid = leader.get('player_id', '')
                    if not pid:
                        continue
                    if pid not in all_leaders:
                        all_leaders[pid] = {
                            'name': leader.get('name', ''),
                            'stats': [],
                            'type': stat_type
                        }
                    all_leaders[pid]['stats'].append({
                        'stat': stat,
                        'rank': leader.get('rank', 0),
                        'value': leader.get('value', 0)
                    })
        except Exception:
            pass

    return all_leaders


def get_all_time_players_to_scrape() -> dict:
    """Get players on all-time lists that the user has seen at games."""
    all_leaders = load_all_time_leaders()

    # Find players seen at games
    cache_dir = get_project_root() / 'cache'
    players_seen = set()

    for cache_file in cache_dir.glob('*.json'):
        if cache_file.name in ['career_firsts.json', 'career_gamelogs.json']:
            continue
        try:
            with open(cache_file) as f:
                game = json.load(f)
                for team in ['away', 'home']:
                    for batter in game.get('batting', {}).get(team, []):
                        if batter.get('player_id'):
                            players_seen.add(batter['player_id'])
                    for pitcher in game.get('pitching', {}).get(team, []):
                        if pitcher.get('player_id'):
                            players_seen.add(pitcher['player_id'])
        except Exception:
            pass

    # Return overlap
    return {pid: all_leaders[pid] for pid in players_seen if pid in all_leaders}


def load_career_firsts_cache() -> dict:
    """Load the career firsts cache from disk."""
    cache_file = get_cache_path() / 'career_firsts.json'
    if cache_file.exists():
        with open(cache_file, 'r') as f:
            return json.load(f)
    return {}


def save_career_firsts_cache(cache: dict):
    """Save the career firsts cache to disk."""
    cache_path = get_cache_path()
    cache_path.mkdir(parents=True, exist_ok=True)
    cache_file = cache_path / 'career_firsts.json'
    with open(cache_file, 'w', encoding='utf-8') as f:
        json.dump(cache, f, indent=2, ensure_ascii=False)


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


class RateLimitError(Exception):
    """Raised when Baseball-Reference rate limits us."""
    pass


class NotFoundError(Exception):
    """Raised when a player page is not found (legitimate 404)."""
    pass


# Cache for register ID -> MLB ID mappings (loaded from disk on first use)
_register_to_mlb_id_cache = {}
_register_cache_loaded = False
_REGISTER_CACHE_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'cache', 'register_id_cache.json')


def _load_register_cache():
    """Load register ID -> MLB ID cache from disk."""
    global _register_to_mlb_id_cache, _register_cache_loaded
    if _register_cache_loaded:
        return
    _register_cache_loaded = True
    try:
        if os.path.exists(_REGISTER_CACHE_PATH):
            with open(_REGISTER_CACHE_PATH, 'r') as f:
                _register_to_mlb_id_cache.update(json.load(f))
    except (json.JSONDecodeError, OSError):
        pass


def _save_register_cache():
    """Persist register ID -> MLB ID cache to disk."""
    try:
        os.makedirs(os.path.dirname(_REGISTER_CACHE_PATH), exist_ok=True)
        tmp = _REGISTER_CACHE_PATH + '.tmp'
        with open(tmp, 'w') as f:
            json.dump(_register_to_mlb_id_cache, f, indent=2)
        os.replace(tmp, _REGISTER_CACHE_PATH)
    except OSError:
        pass


def is_register_format_id(player_id: str) -> bool:
    """
    Check if a player ID is in Baseball Reference register format.

    Register format: 6 chars + "000" + 3 chars (e.g., "workma000gag")
    MLB format: typically ends with 2-digit number (e.g., "workmga01")
    """
    if not player_id or len(player_id) < 10:
        return False
    # Register format has "000" in the middle (positions 6-8)
    return player_id[6:9] == "000"


def get_mlb_id_from_register(register_id: str, scraper=None) -> Optional[str]:
    """
    Fetch the MLB-format ID from a player's register page.

    The register page contains links to game logs using the MLB-format ID.
    Returns None if the ID cannot be found.
    """
    _load_register_cache()
    if register_id in _register_to_mlb_id_cache:
        return _register_to_mlb_id_cache[register_id]

    # Create a scraper if not provided (needed to bypass Cloudflare)
    if scraper is None and HAS_CLOUDSCRAPER:
        scraper = cloudscraper.create_scraper()

    url = f"https://www.baseball-reference.com/register/player.fcgi?id={register_id}"
    try:
        html = fetch_url(url, scraper)
    except (NotFoundError, RateLimitError):
        return None
    if not html:
        return None

    soup = BeautifulSoup(html, 'html.parser')

    # Look for game log links which use the MLB-format ID
    # Pattern: /players/gl.fcgi?id=XXXXXX&t=b&year=YYYY
    # Note: & may be encoded as &amp; in HTML
    import re
    for link in soup.find_all('a', href=True):
        href = link['href']
        # Match MLB-format IDs (letters followed by 2 digits, e.g., workmga01)
        match = re.search(r'/players/gl\.fcgi\?id=([a-z]+\d{2})(?:&|&amp;)', href)
        if match:
            mlb_id = match.group(1)
            _register_to_mlb_id_cache[register_id] = mlb_id
            _save_register_cache()
            return mlb_id

    return None


def resolve_player_id(player_id: str, scraper=None) -> str:
    """
    Resolve a player ID to the MLB-format ID if needed.

    If the ID is in register format, attempts to fetch the MLB-format ID.
    Returns the original ID if resolution fails or ID is already in MLB format.
    """
    if not is_register_format_id(player_id):
        return player_id

    mlb_id = get_mlb_id_from_register(player_id, scraper)
    if mlb_id:
        return mlb_id

    return player_id


def fetch_url(url: str, scraper=None, timeout: int = 30, max_retries: int = 3) -> Optional[str]:
    """
    Fetch a URL with appropriate headers and retry logic for connection errors.

    Raises:
        RateLimitError: When rate limited (429, 403, or suspected blocking)
        NotFoundError: When page genuinely doesn't exist (404)
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
                response = requests.get(url, headers=headers, timeout=timeout)

            # Check for rate limiting
            if response.status_code == 429:
                raise RateLimitError("Rate limited (429 Too Many Requests)")

            if response.status_code == 403:
                # Check if it's Cloudflare blocking us
                if 'cloudflare' in response.text.lower() or 'captcha' in response.text.lower():
                    raise RateLimitError("Blocked by Cloudflare/CAPTCHA (403)")
                raise RateLimitError("Access forbidden (403) - likely rate limited")

            if response.status_code == 404:
                raise NotFoundError(f"Page not found: {url}")

            if response.status_code == 503:
                raise RateLimitError("Service unavailable (503) - server overloaded or blocking")

            response.raise_for_status()

            # Check response content for rate limit messages
            content = response.text
            rate_limit_indicators = [
                'rate limit',
                'too many requests',
                'slow down',
                'blocked',
                'captcha',
                'please wait',
                'access denied'
            ]
            content_lower = content.lower()
            for indicator in rate_limit_indicators:
                if indicator in content_lower and len(content) < 5000:  # Small page = likely error
                    raise RateLimitError(f"Rate limit detected in response: '{indicator}'")

            return content

        except RateLimitError:
            raise
        except NotFoundError:
            raise
        except Exception as e:
            last_error = e
            error_str = str(e).lower()
            # Check if the error message indicates rate limiting
            if '429' in error_str or '403' in error_str or 'forbidden' in error_str:
                raise RateLimitError(f"Rate limited: {e}")

            # Connection errors - retry with backoff
            if attempt < max_retries - 1:
                wait_time = (attempt + 1) * 5  # 5, 10, 15 seconds
                print(f"    Connection error, retrying in {wait_time}s... (attempt {attempt + 1}/{max_retries})")
                time.sleep(wait_time)
            else:
                print(f"  Error fetching {url}: {e}")
                return None

    return None


def get_player_debut_year(player_id: str, scraper=None) -> Optional[int]:
    """
    Get a player's debut year from their main page.

    Raises:
        RateLimitError: If rate limited by the server
    """
    # Resolve register-format IDs to MLB-format IDs
    resolved_id = resolve_player_id(player_id, scraper)

    url = f"https://www.baseball-reference.com/players/{resolved_id[0]}/{resolved_id}.shtml"
    try:
        html = fetch_url(url, scraper)
    except NotFoundError:
        return None  # Player doesn't exist
    if not html:
        return None

    soup = BeautifulSoup(html, 'html.parser')

    # Look for debut info in the bio section
    # Try to find the first year in the batting or pitching table
    # BREF uses different table IDs - try multiple variants
    table_ids = [
        'players_standard_batting', 'players_standard_pitching',
        'batting_standard', 'pitching_standard',
    ]
    for table_id in table_ids:
        table = soup.find('table', {'id': table_id})
        if table:
            tbody = table.find('tbody')
            if tbody:
                # Find first non-header row
                for row in tbody.find_all('tr'):
                    if 'thead' in row.get('class', []) or 'spacer' in row.get('class', []):
                        continue
                    # Try both year_ID and year_id (BREF uses lowercase)
                    year_cell = row.find('th', {'data-stat': 'year_id'})
                    if not year_cell:
                        year_cell = row.find('th', {'data-stat': 'year_ID'})
                    if not year_cell:
                        year_cell = row.find('td', {'data-stat': 'year_id'})
                    if not year_cell:
                        year_cell = row.find('td', {'data-stat': 'year_ID'})
                    if year_cell:
                        year_text = year_cell.get_text(strip=True)
                        # Handle cases like "2011" or links
                        try:
                            return int(year_text[:4])
                        except ValueError:
                            pass

    return None


def scrape_batting_game_log(player_id: str, year: int, scraper=None) -> list[dict]:
    """
    Scrape a player's batting game log for a specific year.

    Raises:
        RateLimitError: If rate limited by the server
    """
    # Resolve register-format IDs to MLB-format IDs
    resolved_id = resolve_player_id(player_id, scraper)

    url = f"https://www.baseball-reference.com/players/gl.fcgi?id={resolved_id}&t=b&year={year}"
    try:
        html = fetch_url(url, scraper)
    except NotFoundError:
        return []  # No data for this year
    if not html:
        return []

    soup = BeautifulSoup(html, 'html.parser')

    # Find the batting game log table - try multiple possible IDs
    table = soup.find('table', {'id': 'batting_gamelogs'})
    if not table:
        table = soup.find('table', {'id': 'batting_gamelogs_sh'})
    if not table:
        table = soup.find('table', {'id': 'players_standard_batting'})
    if not table:
        # Look for any stats table with batting data
        for t in soup.find_all('table', class_='stats_table'):
            # Check if this table has batting columns (with b_ prefix)
            if t.find('td', {'data-stat': 'b_h'}) or t.find('td', {'data-stat': 'H'}):
                table = t
                break

    if not table:
        return []

    games = []
    tbody = table.find('tbody')
    if not tbody:
        return []

    # Map our stat names to possible BREF data-stat values
    BATTING_STAT_MAP = {
        'H': ['b_h', 'H'],
        'HR': ['b_hr', 'HR'],
        'RBI': ['b_rbi', 'RBI'],
        '2B': ['b_doubles', '2B'],
        '3B': ['b_triples', '3B'],
        'BB': ['b_bb', 'BB'],
        'SB': ['b_sb', 'SB'],
        'R': ['b_r', 'R'],
        'AB': ['b_ab', 'AB'],
        'TB': ['b_tb', 'TB'],  # Total bases
    }

    for row in tbody.find_all('tr'):
        # Skip header rows and spacer rows
        row_class = row.get('class', [])
        if 'thead' in row_class or 'spacer' in row_class:
            continue
        if row.find('th', {'scope': 'col'}):
            continue

        game = {}

        # Get date - try multiple possible data-stat values
        date_cell = row.find(['td', 'th'], {'data-stat': 'date_game'})
        if not date_cell:
            date_cell = row.find(['td', 'th'], {'data-stat': 'date'})
        if date_cell:
            game['date'] = date_cell.get_text(strip=True)
            # Also try to get the actual link for full date
            link = date_cell.find('a')
            if link and link.get('href'):
                # Extract date from href like /boxes/SEA/SEA202107200.shtml
                href = link.get('href')
                if '/boxes/' in href:
                    game_id = href.split('/')[-1].replace('.shtml', '')
                    # Game ID format: TEAMYYYYMMDD0
                    if len(game_id) >= 11:
                        game['game_id'] = game_id
                        game['date_full'] = game_id[3:11]  # YYYYMMDD

        # Get opponent - try multiple possible data-stat values
        opp_cell = row.find('td', {'data-stat': 'opp_ID'})
        if not opp_cell:
            opp_cell = row.find('td', {'data-stat': 'opp_name_abbr'})
        if opp_cell:
            game['opponent'] = opp_cell.get_text(strip=True).replace('@', '')

        # Get batting stats using the stat map
        for stat, possible_attrs in BATTING_STAT_MAP.items():
            for attr in possible_attrs:
                stat_cell = row.find('td', {'data-stat': attr})
                if stat_cell:
                    try:
                        game[stat] = int(stat_cell.get_text(strip=True) or 0)
                    except ValueError:
                        game[stat] = 0
                    break

        if game.get('date'):
            games.append(game)

    return games


def scrape_pitching_game_log(player_id: str, year: int, scraper=None) -> list[dict]:
    """
    Scrape a player's pitching game log for a specific year.

    Raises:
        RateLimitError: If rate limited by the server
    """
    # Resolve register-format IDs to MLB-format IDs
    resolved_id = resolve_player_id(player_id, scraper)

    url = f"https://www.baseball-reference.com/players/gl.fcgi?id={resolved_id}&t=p&year={year}"
    try:
        html = fetch_url(url, scraper)
    except NotFoundError:
        return []  # No data for this year
    if not html:
        return []

    soup = BeautifulSoup(html, 'html.parser')

    # Find the pitching game log table - try multiple possible IDs
    table = soup.find('table', {'id': 'pitching_gamelogs'})
    if not table:
        table = soup.find('table', {'id': 'pitching_gamelogs_sh'})
    if not table:
        table = soup.find('table', {'id': 'players_standard_pitching'})
    if not table:
        # Look for any stats table with pitching data
        for t in soup.find_all('table', class_='stats_table'):
            if t.find('td', {'data-stat': 'p_ip'}) or t.find('td', {'data-stat': 'IP'}):
                table = t
                break

    if not table:
        return []

    games = []
    tbody = table.find('tbody')
    if not tbody:
        return []

    # Map our stat names to possible BREF data-stat values
    PITCHING_STAT_MAP = {
        'W': ['p_w', 'W'],
        'L': ['p_l', 'L'],
        'SV': ['p_sv', 'SV'],
        'SO': ['p_so', 'SO'],
        'IP': ['p_ip', 'IP'],
        'GS': ['p_gs', 'GS'],
        'CG': ['p_cg', 'CG'],
        'SHO': ['p_sho', 'SHO'],
        'H': ['p_h', 'H'],
        'R': ['p_r', 'R'],
        'ER': ['p_er', 'ER'],
        'BB': ['p_bb', 'BB'],
    }

    for row in tbody.find_all('tr'):
        row_class = row.get('class', [])
        if 'thead' in row_class or 'spacer' in row_class:
            continue

        game = {}

        # Get date - try multiple possible data-stat values
        date_cell = row.find(['td', 'th'], {'data-stat': 'date_game'})
        if not date_cell:
            date_cell = row.find(['td', 'th'], {'data-stat': 'date'})
        if date_cell:
            game['date'] = date_cell.get_text(strip=True)
            link = date_cell.find('a')
            if link and link.get('href'):
                href = link.get('href')
                if '/boxes/' in href:
                    game_id = href.split('/')[-1].replace('.shtml', '')
                    if len(game_id) >= 11:
                        game['game_id'] = game_id
                        game['date_full'] = game_id[3:11]

        # Get opponent - try multiple possible data-stat values
        opp_cell = row.find('td', {'data-stat': 'opp_ID'})
        if not opp_cell:
            opp_cell = row.find('td', {'data-stat': 'opp_name_abbr'})
        if opp_cell:
            game['opponent'] = opp_cell.get_text(strip=True).replace('@', '')

        # Get pitching stats using the stat map
        for stat, possible_attrs in PITCHING_STAT_MAP.items():
            for attr in possible_attrs:
                stat_cell = row.find('td', {'data-stat': attr})
                if stat_cell:
                    text = stat_cell.get_text(strip=True) or '0'
                    try:
                        # Handle IP which uses baseball notation (6.1 = 6⅓ innings)
                        if stat == 'IP':
                            game[stat] = parse_ip(text)
                        else:
                            game[stat] = int(text) if text else 0
                    except ValueError:
                        game[stat] = 0
                    break

        # Parse the Decision column for W/L/SV
        # BREF uses different data-stat names depending on the table format:
        # - p_game_decision: "W(1-0)", "L(0-1)", "S(1)", "SV(1)" (standard pitching table)
        # - Dec: same format (game log table)
        dec_cell = row.find('td', {'data-stat': 'p_game_decision'})
        if not dec_cell:
            dec_cell = row.find('td', {'data-stat': 'Dec'})
        if not dec_cell:
            dec_cell = row.find('td', {'data-stat': 'dec'})
        if dec_cell:
            dec_text = dec_cell.get_text(strip=True).upper()
            if dec_text.startswith('W'):
                game['W'] = 1
            elif dec_text.startswith('L'):
                game['L'] = 1
            elif dec_text.startswith('S'):
                game['SV'] = 1

        # Parse the game span column for GS, CG, SHO
        # BREF uses different data-stat names:
        # - p_player_game_span: "GS-7" (game start, 7 innings), "CG", "SHO" (standard pitching table)
        # - Inngs: same format (game log table)
        span_cell = row.find('td', {'data-stat': 'p_player_game_span'})
        if not span_cell:
            span_cell = row.find('td', {'data-stat': 'Inngs'})
        if not span_cell:
            span_cell = row.find('td', {'data-stat': 'inngs'})
        if span_cell:
            span_text = span_cell.get_text(strip=True).upper()
            # Check for game start (GS-X format or just GS)
            if 'GS' in span_text:
                game['GS'] = 1
            # Check for shutout (SHO) - implies complete game too
            if span_text == 'SHO':
                game['SHO'] = 1
                game['CG'] = 1
                game['GS'] = 1  # Shutouts are always starts
            # Check for complete game (CG)
            elif span_text == 'CG':
                game['CG'] = 1
                game['GS'] = 1  # Complete games are always starts

        # Fallback: check for GS in dedicated column if not found
        if game.get('GS', 0) == 0:
            gs_cell = row.find('td', {'data-stat': 'GS'})
            if not gs_cell:
                gs_cell = row.find('td', {'data-stat': 'p_gs'})
            if gs_cell:
                gs_text = gs_cell.get_text(strip=True)
                game['GS'] = 1 if gs_text == '1' or gs_text == '*' else 0

        if game.get('date'):
            games.append(game)

    return games


def find_career_firsts(player_id: str, scraper=None, verbose: bool = True, store_gamelogs: bool = False) -> dict:
    """
    Find all career firsts AND career milestones for a player by scanning their game logs.

    Args:
        player_id: The Baseball Reference player ID
        scraper: HTTP scraper to use (cloudscraper instance)
        verbose: Print progress messages
        store_gamelogs: If True, store cumulative totals for every game (for all-time passing detection)

    Returns dict with structure:
    {
        'player_id': str,
        'batting_firsts': {
            'H': {'date': 'YYYYMMDD', 'game_id': str, 'opponent': str, 'milestone': str},
            ...
        },
        'pitching_firsts': {...},
        'batting_milestones': {
            'H': [
                {'number': 100, 'date': 'YYYYMMDD', 'game_id': str, ...},
                {'number': 500, ...},
            ],
            ...
        },
        'pitching_milestones': {...},
        'career_totals': {'H': 1234, 'HR': 56, ...},
        'gamelogs': {  # Only if store_gamelogs=True
            'GAMEID123': {'batting': {'H': 150, 'HR': 10, ...}, 'pitching': {...}},
            ...
        }
    }
    """
    if verbose:
        print(f"  Finding career firsts & milestones for {player_id}...")

    result = {
        'player_id': player_id,
        'batting_firsts': {},
        'pitching_firsts': {},
        'batting_milestones': {},
        'pitching_milestones': {},
        'career_totals': {},
        'scraped_at': datetime.now().isoformat(),
    }

    # If storing gamelogs, initialize the dict to store cumulative totals per game
    if store_gamelogs:
        result['gamelogs'] = {}

    # Get debut year
    debut_year = get_player_debut_year(player_id, scraper)
    if not debut_year:
        # Try common recent years
        debut_year = 2015

    current_year = datetime.now().year

    # Track which firsts we still need to find
    batting_needed = set(BATTING_FIRSTS.keys())
    pitching_needed = set(PITCHING_FIRSTS.keys())

    # Running totals for milestone tracking
    batting_totals = {stat: 0 for stat in BATTING_MILESTONES.keys()}
    pitching_totals = {stat: 0 for stat in PITCHING_MILESTONES.keys()}

    # Track which milestones we've already recorded
    batting_milestones_reached = {stat: set() for stat in BATTING_MILESTONES.keys()}
    pitching_milestones_reached = {stat: set() for stat in PITCHING_MILESTONES.keys()}

    # Initialize milestone lists
    for stat in BATTING_MILESTONES.keys():
        result['batting_milestones'][stat] = []
    for stat in PITCHING_MILESTONES.keys():
        result['pitching_milestones'][stat] = []

    # Scan years from debut to present
    has_pitching_data = None  # Unknown until we check

    for year in range(debut_year, current_year + 1):
        # Batting game log
        time.sleep(3.05)  # BREF rate limit: 20 requests/minute = 3+ seconds between
        games = scrape_batting_game_log(player_id, year, scraper)

        for game in games:
            # Check for firsts
            for stat in list(batting_needed):
                if game.get(stat, 0) > 0:
                    result['batting_firsts'][stat] = {
                        'date': game.get('date_full', game.get('date', '')),
                        'game_id': game.get('game_id', ''),
                        'opponent': game.get('opponent', ''),
                        'year': year,
                        'milestone': BATTING_FIRSTS[stat],
                    }
                    batting_needed.discard(stat)
                    if verbose:
                        print(f"    Found {BATTING_FIRSTS[stat]}: {game.get('date', '')}")

            # Update running totals and check for milestones
            # Special handling for G (games) - each game is +1
            batting_totals['G'] = batting_totals.get('G', 0) + 1

            for stat in BATTING_MILESTONES.keys():
                if stat == 'G':
                    game_value = 1  # Each game is 1
                else:
                    game_value = game.get(stat, 0)

                if game_value > 0:
                    if stat != 'G':  # G already incremented above
                        old_total = batting_totals[stat]
                        batting_totals[stat] += game_value
                        new_total = batting_totals[stat]
                    else:
                        old_total = batting_totals['G'] - 1
                        new_total = batting_totals['G']

                    # Check if we crossed any milestone thresholds
                    for threshold in BATTING_MILESTONES[stat]:
                        if old_total < threshold <= new_total:
                            if threshold not in batting_milestones_reached[stat]:
                                batting_milestones_reached[stat].add(threshold)
                                stat_name = STAT_NAMES.get(stat, stat)
                                milestone_name = f"Career {stat_name} #{threshold}"
                                result['batting_milestones'][stat].append({
                                    'number': threshold,
                                    'date': game.get('date_full', game.get('date', '')),
                                    'game_id': game.get('game_id', ''),
                                    'opponent': game.get('opponent', ''),
                                    'year': year,
                                    'milestone': milestone_name,
                                    'career_total_after': new_total,
                                })
                                if verbose:
                                    print(f"    Found {milestone_name}: {game.get('date', '')}")

            # Store gamelog if requested
            if store_gamelogs:
                game_id = game.get('game_id', '')
                if game_id:
                    if game_id not in result['gamelogs']:
                        result['gamelogs'][game_id] = {'batting': {}, 'pitching': {}}
                    result['gamelogs'][game_id]['batting'] = batting_totals.copy()

        # Pitching game log (only if player has pitched)
        if has_pitching_data is None or has_pitching_data:
            time.sleep(3.05)  # BREF rate limit
            games = scrape_pitching_game_log(player_id, year, scraper)

            if games:
                has_pitching_data = True
                for game in games:
                    # Check for firsts
                    for stat in list(pitching_needed):
                        value = game.get(stat, 0)
                        if (stat == 'IP' and value > 0) or (stat != 'IP' and value > 0):
                            result['pitching_firsts'][stat] = {
                                'date': game.get('date_full', game.get('date', '')),
                                'game_id': game.get('game_id', ''),
                                'opponent': game.get('opponent', ''),
                                'year': year,
                                'milestone': PITCHING_FIRSTS[stat],
                            }
                            pitching_needed.discard(stat)
                            if verbose:
                                print(f"    Found {PITCHING_FIRSTS[stat]}: {game.get('date', '')}")

                    # Update running totals and check for milestones
                    # Each pitching game is G+1
                    pitching_totals['G'] = pitching_totals.get('G', 0) + 1

                    for stat in PITCHING_MILESTONES.keys():
                        if stat == 'G':
                            game_value = 1  # Each game is 1
                        else:
                            game_value = game.get(stat, 0)

                        if game_value > 0:
                            if stat != 'G':  # G already incremented above
                                old_total = pitching_totals[stat]
                                pitching_totals[stat] += game_value
                                new_total = pitching_totals[stat]
                            else:
                                old_total = pitching_totals['G'] - 1
                                new_total = pitching_totals['G']

                            # Check if we crossed any milestone thresholds
                            for threshold in PITCHING_MILESTONES[stat]:
                                if old_total < threshold <= new_total:
                                    if threshold not in pitching_milestones_reached[stat]:
                                        pitching_milestones_reached[stat].add(threshold)
                                        stat_name = STAT_NAMES.get(stat, stat)
                                        milestone_name = f"Career {stat_name} #{threshold}"
                                        result['pitching_milestones'][stat].append({
                                            'number': threshold,
                                            'date': game.get('date_full', game.get('date', '')),
                                            'game_id': game.get('game_id', ''),
                                            'opponent': game.get('opponent', ''),
                                            'year': year,
                                            'milestone': milestone_name,
                                            'career_total_after': new_total,
                                        })
                                        if verbose:
                                            print(f"    Found {milestone_name}: {game.get('date', '')}")

                    # Store gamelog if requested
                    if store_gamelogs:
                        game_id = game.get('game_id', '')
                        if game_id:
                            if game_id not in result['gamelogs']:
                                result['gamelogs'][game_id] = {'batting': {}, 'pitching': {}}
                            result['gamelogs'][game_id]['pitching'] = pitching_totals.copy()

            elif year == debut_year:
                # No pitching data in debut year - likely not a pitcher
                has_pitching_data = False
                pitching_needed.clear()

    # Store final career totals
    result['career_totals'] = {
        'batting': {k: v for k, v in batting_totals.items() if v > 0},
        'pitching': {k: v for k, v in pitching_totals.items() if v > 0},
    }

    # Clean up empty milestone lists
    result['batting_milestones'] = {k: v for k, v in result['batting_milestones'].items() if v}
    result['pitching_milestones'] = {k: v for k, v in result['pitching_milestones'].items() if v}

    return result


def get_players_from_games(games_dir: Path, year: int = None) -> tuple[set[str], dict[str, str]]:
    """Extract all unique player IDs and names from cached game data.

    Args:
        games_dir: Path to games directory (unused, kept for compatibility)
        year: Optional year to filter games by (e.g., 2025 for only 2025 games)

    Returns:
        Tuple of (player_ids set, player_names dict mapping id -> name)
    """
    player_ids = set()
    player_names = {}
    cache_dir = get_project_root() / 'cache'

    if not cache_dir.exists():
        print(f"Cache directory not found: {cache_dir}")
        return player_ids, player_names

    for json_file in cache_dir.glob('*.json'):
        if json_file.name == 'career_firsts.json':
            continue
        try:
            with open(json_file, 'r') as f:
                game_data = json.load(f)

            # Filter by year if specified
            if year:
                basic_info = game_data.get('basic_info', {})
                date_str = basic_info.get('date_yyyymmdd', '')
                if date_str and not date_str.startswith(str(year)):
                    continue

            # Extract batting player IDs and names
            for side in ['away', 'home']:
                batters = game_data.get('batting', {}).get(side, [])
                for batter in batters:
                    if batter.get('player_id'):
                        player_ids.add(batter['player_id'])
                        if batter.get('name'):
                            player_names[batter['player_id']] = batter['name']

            # Extract pitching player IDs and names
            for side in ['away', 'home']:
                pitchers = game_data.get('pitching', {}).get(side, [])
                for pitcher in pitchers:
                    if pitcher.get('player_id'):
                        player_ids.add(pitcher['player_id'])
                        if pitcher.get('name'):
                            player_names[pitcher['player_id']] = pitcher['name']

        except (json.JSONDecodeError, KeyError):
            continue

    return player_ids, player_names


def get_players_from_game_file(game_file: Path) -> tuple[set[str], dict[str, str]]:
    """Extract player IDs and names from a single cached game file.

    Args:
        game_file: Path to a cached game JSON file

    Returns:
        Tuple of (player_ids set, player_names dict mapping id -> name)
    """
    player_ids = set()
    player_names = {}

    try:
        with open(game_file, 'r') as f:
            game_data = json.load(f)

        # Extract batting player IDs and names
        for side in ['away', 'home']:
            batters = game_data.get('batting', {}).get(side, [])
            for batter in batters:
                if batter.get('player_id'):
                    player_ids.add(batter['player_id'])
                    if batter.get('name'):
                        player_names[batter['player_id']] = batter['name']

        # Extract pitching player IDs and names
        for side in ['away', 'home']:
            pitchers = game_data.get('pitching', {}).get(side, [])
            for pitcher in pitchers:
                if pitcher.get('player_id'):
                    player_ids.add(pitcher['player_id'])
                    if pitcher.get('name'):
                        player_names[pitcher['player_id']] = pitcher['name']

    except (json.JSONDecodeError, KeyError, FileNotFoundError) as e:
        print(f"Error reading game file {game_file}: {e}")

    return player_ids, player_names


def scrape_for_game(game_file: Path, delay: float = 3.05, verbose: bool = True) -> dict:
    """
    Scrape career firsts for all players in a specific game.
    Only scrapes players not already in the cache.

    Args:
        game_file: Path to a cached game JSON file
        delay: Delay between requests in seconds
        verbose: Print progress

    Returns:
        Updated cache dictionary
    """
    if not game_file.exists():
        print(f"Game file not found: {game_file}")
        return {}

    if verbose:
        print(f"Extracting players from: {game_file.name}")

    player_ids, player_names = get_players_from_game_file(game_file)

    if not player_ids:
        print("No players found in game file.")
        return {}

    if verbose:
        print(f"Found {len(player_ids)} players in game\n")

    # Scrape career firsts (will skip already-cached players)
    cache = scrape_career_firsts_for_players(
        player_ids,
        refresh=False,  # Don't re-scrape cached players
        delay=delay,
        verbose=verbose,
        player_names=player_names
    )

    return cache


def get_attended_game_dates() -> dict[str, dict]:
    """Get all attended game dates and their details from cache."""
    games = {}
    cache_dir = get_project_root() / 'cache'

    for json_file in cache_dir.glob('*.json'):
        if json_file.name == 'career_firsts.json':
            continue
        try:
            with open(json_file, 'r') as f:
                game_data = json.load(f)

            basic_info = game_data.get('basic_info', {})
            date_str = basic_info.get('date_yyyymmdd', '')

            # Use actual game_id from data, not constructed one
            game_id = game_data.get('game_id', '')
            if not game_id:
                # Fallback to constructing it
                home_code = basic_info.get('home_team_code', '')
                game_id = f"{home_code}{date_str}0"

            if game_id:
                game_info = {
                    'game_id': game_id,
                    'home_team': basic_info.get('home_team', ''),
                    'away_team': basic_info.get('away_team', ''),
                    'venue': basic_info.get('venue', ''),
                    'date': basic_info.get('date', ''),
                }

                # Store by game_id for matching
                games[game_id] = game_info

        except (json.JSONDecodeError, KeyError):
            continue

    return games


def find_witnessed_firsts(career_firsts_cache: dict, attended_games: dict) -> list[dict]:
    """Find career firsts and milestones that were witnessed at attended games.

    Only matches on game_id (not date) to avoid false positives from
    games at different venues on the same date.
    """
    witnessed = []

    for player_id, data in career_firsts_cache.items():
        player_name = data.get('player_name', player_id)

        # Check batting firsts
        for stat, first_info in data.get('batting_firsts', {}).items():
            date = first_info.get('date', '')
            game_id = first_info.get('game_id', '')

            # Only match by game_id (not date) to avoid false positives
            game = attended_games.get(game_id)
            if game:
                witnessed.append({
                    'player_id': player_id,
                    'player_name': player_name,
                    'milestone': first_info.get('milestone', ''),
                    'date': date,
                    'game_id': game_id,
                    'opponent': first_info.get('opponent', ''),
                    'venue': game.get('venue', ''),
                    'type': 'batting',
                    'category': 'first',
                })

        # Check pitching firsts
        for stat, first_info in data.get('pitching_firsts', {}).items():
            date = first_info.get('date', '')
            game_id = first_info.get('game_id', '')

            game = attended_games.get(game_id)
            if game:
                witnessed.append({
                    'player_id': player_id,
                    'player_name': player_name,
                    'milestone': first_info.get('milestone', ''),
                    'date': date,
                    'game_id': game_id,
                    'opponent': first_info.get('opponent', ''),
                    'venue': game.get('venue', ''),
                    'type': 'pitching',
                    'category': 'first',
                })

        # Check batting milestones (e.g., 100th HR, 500th hit)
        for stat, milestones_list in data.get('batting_milestones', {}).items():
            for milestone_info in milestones_list:
                date = milestone_info.get('date', '')
                game_id = milestone_info.get('game_id', '')

                game = attended_games.get(game_id)
                if game:
                    witnessed.append({
                        'player_id': player_id,
                        'player_name': player_name,
                        'milestone': milestone_info.get('milestone', ''),
                        'date': date,
                        'game_id': game_id,
                        'opponent': milestone_info.get('opponent', ''),
                        'venue': game.get('venue', ''),
                        'type': 'batting',
                        'category': 'milestone',
                    })

        # Check pitching milestones
        for stat, milestones_list in data.get('pitching_milestones', {}).items():
            for milestone_info in milestones_list:
                date = milestone_info.get('date', '')
                game_id = milestone_info.get('game_id', '')

                game = attended_games.get(game_id)
                if game:
                    witnessed.append({
                        'player_id': player_id,
                        'player_name': player_name,
                        'milestone': milestone_info.get('milestone', ''),
                        'date': date,
                        'game_id': game_id,
                        'opponent': milestone_info.get('opponent', ''),
                        'venue': game.get('venue', ''),
                        'type': 'pitching',
                        'category': 'milestone',
                    })

    return witnessed


def scrape_career_firsts_for_players(
    player_ids: set[str],
    refresh: bool = False,
    delay: float = 3.05,
    verbose: bool = True,
    player_names: dict[str, str] = None
) -> dict:
    """
    Scrape career firsts for a set of players.

    Args:
        player_ids: Set of player IDs to scrape
        refresh: If True, re-scrape even if cached
        delay: Delay between requests in seconds (default 3.1 for BREF rate limit)
        verbose: Print progress
        player_names: Optional dict mapping player_id -> name for display

    Returns:
        Updated cache dictionary
    """
    cache = load_career_firsts_cache()
    scraper = create_scraper()
    player_names = player_names or {}

    total = len(player_ids)
    consecutive_errors = 0
    max_consecutive_errors = 3  # Stop after 3 consecutive errors (likely rate limited)

    for i, player_id in enumerate(sorted(player_ids), 1):
        name = player_names.get(player_id, player_id)
        display_name = f"{name} ({player_id})" if name != player_id else player_id

        if not refresh and player_id in cache:
            if verbose:
                print(f"[{i}/{total}] {display_name}: cached, skipping")
            continue

        if verbose:
            print(f"[{i}/{total}] Scraping {display_name}...")

        try:
            firsts = find_career_firsts(player_id, scraper, verbose)
            cache[player_id] = firsts

            # Save after each player in case of interruption
            save_career_firsts_cache(cache)

            # Reset error counter on success
            consecutive_errors = 0

            if i < total:
                time.sleep(delay)

        except RateLimitError as e:
            print(f"\n{'='*60}")
            print(f"⚠️  RATE LIMITED: {e}")
            print(f"{'='*60}")
            print(f"\nStopping scraper to avoid being blocked.")
            print(f"Progress saved: {len(cache)} players cached.")
            print(f"\nSuggestions:")
            print(f"  1. Wait 10-15 minutes before retrying")
            print(f"  2. Use a longer delay: --delay 5.0")
            print(f"  3. Run again later - cached players will be skipped")
            print(f"\nTo resume: python -m baseball_processor.scrapers.career_firsts_scraper")
            break

        except NotFoundError:
            # Player doesn't exist - skip but don't count as error
            if verbose:
                print(f"  Player not found, skipping")
            continue

        except Exception as e:
            consecutive_errors += 1
            print(f"  Error processing {player_id}: {e}")

            if consecutive_errors >= max_consecutive_errors:
                print(f"\n{'='*60}")
                print(f"⚠️  TOO MANY CONSECUTIVE ERRORS ({consecutive_errors})")
                print(f"{'='*60}")
                print(f"\nThis might indicate rate limiting or network issues.")
                print(f"Progress saved: {len(cache)} players cached.")
                print(f"\nTo resume: python -m baseball_processor.scrapers.career_firsts_scraper")
                break

            continue

    return cache


def refresh_pitching_only(delay: float = 3.05, verbose: bool = True) -> dict:
    """
    Re-scrape only pitching data for all cached players.
    Preserves existing batting data and only updates pitching firsts/milestones.

    This is useful when the pitching scraping logic has been fixed/improved.
    """
    cache = load_career_firsts_cache()

    if not cache:
        print("No cached data found. Run the full scraper first.")
        return cache

    # Find players who have pitched (have pitching_firsts or pitching career_totals)
    pitchers = []
    for player_id, data in cache.items():
        has_pitching = (
            data.get('pitching_firsts') or
            data.get('pitching_milestones') or
            data.get('career_totals', {}).get('pitching')
        )
        if has_pitching:
            pitchers.append((player_id, data.get('player_name', player_id)))

    if not pitchers:
        print("No pitchers found in cache.")
        return cache

    if verbose:
        print(f"Found {len(pitchers)} pitchers to refresh\n")

    # Set up scraper
    if HAS_CLOUDSCRAPER:
        scraper = cloudscraper.create_scraper()
    else:
        scraper = None

    consecutive_errors = 0
    max_consecutive_errors = 5

    for i, (player_id, player_name) in enumerate(pitchers, 1):
        if verbose:
            print(f"[{i}/{len(pitchers)}] Refreshing pitching for {player_name} ({player_id})...")

        try:
            # Get debut year from existing data or fetch it
            existing_data = cache.get(player_id, {})

            # Try to get debut year from first pitching data
            debut_year = None
            for stat_data in existing_data.get('pitching_firsts', {}).values():
                if stat_data.get('year'):
                    if debut_year is None or stat_data['year'] < debut_year:
                        debut_year = stat_data['year']

            if not debut_year:
                # Fetch from BREF
                time.sleep(delay)
                debut_year = get_player_debut_year(player_id, scraper)

            if not debut_year:
                debut_year = 2015  # Fallback

            current_year = datetime.now().year

            # Reset pitching data
            pitching_firsts = {}
            pitching_milestones = {stat: [] for stat in PITCHING_MILESTONES.keys()}
            pitching_totals = {stat: 0 for stat in PITCHING_MILESTONES.keys()}
            pitching_needed = set(PITCHING_FIRSTS.keys())
            pitching_milestones_reached = {stat: set() for stat in PITCHING_MILESTONES.keys()}

            # Scrape pitching game logs year by year
            for year in range(debut_year, current_year + 1):
                time.sleep(delay)
                games = scrape_pitching_game_log(player_id, year, scraper)

                if not games:
                    continue

                for game in games:
                    # Check for firsts
                    for stat in list(pitching_needed):
                        value = game.get(stat, 0)
                        if (stat == 'IP' and value > 0) or (stat != 'IP' and value > 0):
                            pitching_firsts[stat] = {
                                'date': game.get('date_full', game.get('date', '')),
                                'game_id': game.get('game_id', ''),
                                'opponent': game.get('opponent', ''),
                                'year': year,
                                'milestone': PITCHING_FIRSTS[stat],
                            }
                            pitching_needed.discard(stat)
                            if verbose:
                                print(f"    Found {PITCHING_FIRSTS[stat]}: {game.get('date', '')}")

                    # Update running totals and check for milestones
                    for stat in PITCHING_MILESTONES.keys():
                        game_value = game.get(stat, 0)
                        if game_value > 0:
                            old_total = pitching_totals[stat]
                            pitching_totals[stat] += game_value
                            new_total = pitching_totals[stat]

                            for threshold in PITCHING_MILESTONES[stat]:
                                if old_total < threshold <= new_total:
                                    if threshold not in pitching_milestones_reached[stat]:
                                        pitching_milestones_reached[stat].add(threshold)
                                        stat_name = STAT_NAMES.get(stat, stat)
                                        milestone_name = f"Career {stat_name} #{threshold}"
                                        pitching_milestones[stat].append({
                                            'number': threshold,
                                            'date': game.get('date_full', game.get('date', '')),
                                            'game_id': game.get('game_id', ''),
                                            'opponent': game.get('opponent', ''),
                                            'year': year,
                                            'milestone': milestone_name,
                                            'career_total_after': new_total,
                                        })
                                        if verbose:
                                            print(f"    Found {milestone_name}: {game.get('date', '')}")

            # Update cache - preserve batting data, update pitching
            cache[player_id]['pitching_firsts'] = pitching_firsts
            cache[player_id]['pitching_milestones'] = {k: v for k, v in pitching_milestones.items() if v}
            if 'career_totals' not in cache[player_id]:
                cache[player_id]['career_totals'] = {}
            cache[player_id]['career_totals']['pitching'] = {k: v for k, v in pitching_totals.items() if v > 0}

            # Save after each player
            save_career_firsts_cache(cache)
            consecutive_errors = 0

        except RateLimitError as e:
            print(f"\n{'='*60}")
            print(f"⚠️  RATE LIMITED: {e}")
            print(f"{'='*60}")
            print(f"\nProgress saved. Run again to resume.")
            break

        except Exception as e:
            consecutive_errors += 1
            print(f"  Error: {e}")
            if consecutive_errors >= max_consecutive_errors:
                print(f"\nToo many errors. Progress saved.")
                break

    return cache


def refresh_batting_only(delay: float = 3.05, verbose: bool = True) -> dict:
    """
    Re-scrape only batting data for all cached players.
    Preserves existing pitching data and only updates batting firsts/milestones.

    This is useful when the batting scraping logic has been fixed/improved.
    """
    cache = load_career_firsts_cache()

    if not cache:
        print("No cached data found. Run the full scraper first.")
        return cache

    # Get all cached players (batters)
    batters = []
    for player_id, data in cache.items():
        has_batting = (
            data.get('batting_firsts') or
            data.get('batting_milestones') or
            data.get('career_totals', {}).get('batting')
        )
        if has_batting:
            batters.append((player_id, data.get('player_name', player_id)))

    if not batters:
        print("No batters found in cache.")
        return cache

    if verbose:
        print(f"Found {len(batters)} batters to refresh\n")

    # Set up scraper
    if HAS_CLOUDSCRAPER:
        scraper = cloudscraper.create_scraper()
    else:
        scraper = None

    consecutive_errors = 0
    max_consecutive_errors = 5

    for i, (player_id, player_name) in enumerate(batters, 1):
        if verbose:
            print(f"[{i}/{len(batters)}] Refreshing batting for {player_name} ({player_id})...")

        try:
            # Get debut year from existing data or fetch it
            existing_data = cache.get(player_id, {})

            # Try to get debut year from first batting data
            debut_year = None
            for stat_data in existing_data.get('batting_firsts', {}).values():
                if stat_data.get('year'):
                    if debut_year is None or stat_data['year'] < debut_year:
                        debut_year = stat_data['year']

            if not debut_year:
                # Fetch from BREF
                time.sleep(delay)
                debut_year = get_player_debut_year(player_id, scraper)

            if not debut_year:
                debut_year = 2015  # Fallback

            current_year = datetime.now().year

            # Reset batting data
            batting_firsts = {}
            batting_milestones = {stat: [] for stat in BATTING_MILESTONES.keys()}
            batting_totals = {stat: 0 for stat in BATTING_MILESTONES.keys()}
            batting_needed = set(BATTING_FIRSTS.keys())
            batting_milestones_reached = {stat: set() for stat in BATTING_MILESTONES.keys()}

            # Scrape batting game logs year by year
            for year in range(debut_year, current_year + 1):
                time.sleep(delay)
                games = scrape_batting_game_log(player_id, year, scraper)

                if not games:
                    continue

                for game in games:
                    # Check for firsts
                    for stat in list(batting_needed):
                        if game.get(stat, 0) > 0:
                            batting_firsts[stat] = {
                                'date': game.get('date_full', game.get('date', '')),
                                'game_id': game.get('game_id', ''),
                                'opponent': game.get('opponent', ''),
                                'year': year,
                                'milestone': BATTING_FIRSTS[stat],
                            }
                            batting_needed.discard(stat)
                            if verbose:
                                print(f"    Found {BATTING_FIRSTS[stat]}: {game.get('date', '')}")

                    # Update running totals and check for milestones
                    for stat in BATTING_MILESTONES.keys():
                        game_value = game.get(stat, 0)
                        if game_value > 0:
                            old_total = batting_totals[stat]
                            batting_totals[stat] += game_value
                            new_total = batting_totals[stat]

                            for threshold in BATTING_MILESTONES[stat]:
                                if old_total < threshold <= new_total:
                                    if threshold not in batting_milestones_reached[stat]:
                                        batting_milestones_reached[stat].add(threshold)
                                        stat_name = STAT_NAMES.get(stat, stat)
                                        milestone_name = f"Career {stat_name} #{threshold}"
                                        batting_milestones[stat].append({
                                            'number': threshold,
                                            'date': game.get('date_full', game.get('date', '')),
                                            'game_id': game.get('game_id', ''),
                                            'opponent': game.get('opponent', ''),
                                            'year': year,
                                            'milestone': milestone_name,
                                            'career_total_after': new_total,
                                        })
                                        if verbose:
                                            print(f"    Found {milestone_name}: {game.get('date', '')}")

            # Update cache - preserve pitching data, update batting
            cache[player_id]['batting_firsts'] = batting_firsts
            cache[player_id]['batting_milestones'] = {k: v for k, v in batting_milestones.items() if v}
            if 'career_totals' not in cache[player_id]:
                cache[player_id]['career_totals'] = {}
            cache[player_id]['career_totals']['batting'] = {k: v for k, v in batting_totals.items() if v > 0}

            # Save after each player
            save_career_firsts_cache(cache)
            consecutive_errors = 0

        except RateLimitError as e:
            print(f"\n{'='*60}")
            print(f"⚠️  RATE LIMITED: {e}")
            print(f"{'='*60}")
            print(f"\nProgress saved. Run again to resume.")
            break

        except Exception as e:
            consecutive_errors += 1
            print(f"  Error: {e}")
            if consecutive_errors >= max_consecutive_errors:
                print(f"\nToo many errors. Progress saved.")
                break

    return cache


def main():
    parser = argparse.ArgumentParser(
        description="Scrape career firsts from Baseball-Reference",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
    # Scrape career firsts for all players in your games
    python -m baseball_processor.scrapers.career_firsts_scraper

    # Scrape a specific player
    python -m baseball_processor.scrapers.career_firsts_scraper --player troutmi01

    # Force refresh all cached data
    python -m baseball_processor.scrapers.career_firsts_scraper --refresh

    # Refresh only players from 2025 games (useful at start of new season)
    python -m baseball_processor.scrapers.career_firsts_scraper --refresh-year 2025

    # Re-scrape only pitching data for all pitchers (after fixing pitching logic)
    python -m baseball_processor.scrapers.career_firsts_scraper --refresh-pitching

    # Re-scrape only batting data for all batters (after fixing batting logic)
    python -m baseball_processor.scrapers.career_firsts_scraper --refresh-batting

    # Scrape career firsts for players in a specific game
    python -m baseball_processor.scrapers.career_firsts_scraper --game "Baltimore_Orioles_vs_Yankees_Box_Score.json"

    # Scrape full game logs for players on all-time lists (for accurate passing detection)
    python -m baseball_processor.scrapers.career_firsts_scraper --all-time-leaders

    # Check for witnessed firsts
    python -m baseball_processor.scrapers.career_firsts_scraper --check-witnessed
        """
    )

    parser.add_argument(
        '--player', '-p',
        type=str,
        help="Scrape a specific player by ID (e.g., raleica01)"
    )

    parser.add_argument(
        '--refresh', '-r',
        action='store_true',
        help="Refresh cached data even if already scraped"
    )

    parser.add_argument(
        '--check-witnessed', '-c',
        action='store_true',
        dest='check_witnessed',
        help="Check for career firsts witnessed at attended games"
    )

    parser.add_argument(
        '--delay', '-d',
        type=float,
        default=3.05,
        help="Delay between requests in seconds (default: 3.05 for BREF rate limit)"
    )

    parser.add_argument(
        '--quiet', '-q',
        action='store_true',
        help="Suppress progress messages"
    )

    parser.add_argument(
        '--refresh-year', '-y',
        type=int,
        dest='refresh_year',
        help="Refresh only players from games in a specific year (e.g., 2025)"
    )

    parser.add_argument(
        '--refresh-pitching',
        action='store_true',
        dest='refresh_pitching',
        help="Re-scrape only pitching data for all cached players (preserves batting data)"
    )

    parser.add_argument(
        '--refresh-batting',
        action='store_true',
        dest='refresh_batting',
        help="Re-scrape only batting data for all cached players (preserves pitching data)"
    )

    parser.add_argument(
        '--game', '-g',
        type=str,
        help="Scrape career firsts for players in a specific game file (path to cached JSON)"
    )

    parser.add_argument(
        '--all-time-leaders',
        action='store_true',
        dest='all_time_leaders',
        help="Scrape full game logs for players on all-time lists (for accurate passing detection)"
    )

    parser.add_argument(
        '--all-players',
        action='store_true',
        dest='all_players',
        help="Scrape full game logs for ALL players you've seen (comprehensive data)"
    )

    args = parser.parse_args()
    verbose = not args.quiet

    if args.check_witnessed:
        # Load cache and check for witnessed firsts
        cache = load_career_firsts_cache()
        attended = get_attended_game_dates()
        witnessed = find_witnessed_firsts(cache, attended)

        if witnessed:
            print(f"\n{'='*60}")
            print("CAREER FIRSTS YOU WITNESSED")
            print(f"{'='*60}\n")

            for w in sorted(witnessed, key=lambda x: x['date']):
                print(f"  {w['milestone']}")
                print(f"    Player: {w['player_name']}")
                print(f"    Date: {w['date']}")
                print(f"    Venue: {w['venue']}")
                print()
        else:
            print("No career firsts found in attended games (or cache is empty).")
            print("Run without --check-witnessed first to build the cache.")
        return

    if args.refresh_pitching:
        # Only refresh pitching data for cached pitchers
        if verbose:
            print("Refreshing pitching data for all cached pitchers...")
            print("(Batting data will be preserved)\n")
        cache = refresh_pitching_only(delay=args.delay, verbose=verbose)
        if verbose:
            print(f"\nRefreshed pitching data for pitchers in cache")
            print(f"Cache saved to: {get_cache_path() / 'career_firsts.json'}")
        return

    if args.refresh_batting:
        # Only refresh batting data for cached batters
        if verbose:
            print("Refreshing batting data for all cached batters...")
            print("(Pitching data will be preserved)\n")
        cache = refresh_batting_only(delay=args.delay, verbose=verbose)
        if verbose:
            print(f"\nRefreshed batting data for batters in cache")
            print(f"Cache saved to: {get_cache_path() / 'career_firsts.json'}")
        return

    if args.game:
        # Scrape career firsts for players in a specific game
        game_path = Path(args.game)
        if not game_path.is_absolute():
            # Try relative to cache directory
            cache_path = get_project_root() / 'cache' / args.game
            if cache_path.exists():
                game_path = cache_path
            else:
                game_path = Path(args.game).resolve()

        cache = scrape_for_game(game_path, delay=args.delay, verbose=verbose)
        if verbose and cache:
            print(f"\nCache saved to: {get_cache_path() / 'career_firsts.json'}")
        return

    if args.all_time_leaders:
        # Scrape full game logs for players on all-time lists
        if verbose:
            print("Scraping game logs for players on all-time lists...")
            print("(This enables accurate all-time passing detection)\n")

        players = get_all_time_players_to_scrape()
        if not players:
            print("No players found. Make sure mlb_references/all_time_leaders/ has data.")
            return

        print(f"Found {len(players)} players on all-time lists that you've seen")

        # Load existing caches
        career_cache = load_career_firsts_cache()
        gamelogs_cache = load_gamelogs_cache()

        # Filter to players not yet scraped for gamelogs
        if not args.refresh:
            players = {pid: info for pid, info in players.items()
                       if pid not in gamelogs_cache}
            print(f"Players needing scraping: {len(players)}")

        if not players:
            print("All players already scraped! Use --refresh to re-scrape.")
            return

        # Estimate time
        est_requests = len(players) * 25  # ~25 requests per player
        est_time_min = (est_requests * args.delay) / 60
        print(f"Estimated time: ~{est_time_min:.0f} minutes\n")

        scraper = create_scraper()
        consecutive_errors = 0
        max_consecutive_errors = 3

        for i, (player_id, player_info) in enumerate(sorted(players.items()), 1):
            name = player_info.get('name', player_id)
            if verbose:
                print(f"[{i}/{len(players)}] {name} ({player_id})")

            try:
                firsts = find_career_firsts(player_id, scraper, verbose=verbose, store_gamelogs=True)

                # Save to career_firsts cache
                career_cache[player_id] = {k: v for k, v in firsts.items() if k != 'gamelogs'}
                career_cache[player_id]['player_name'] = name
                save_career_firsts_cache(career_cache)

                # Save gamelogs to separate cache
                if firsts.get('gamelogs'):
                    gamelogs_cache[player_id] = {
                        'name': name,
                        'gamelogs': firsts['gamelogs']
                    }
                    save_gamelogs_cache(gamelogs_cache)

                consecutive_errors = 0

            except RateLimitError as e:
                print(f"\n{'='*60}")
                print(f"⚠️  RATE LIMITED: {e}")
                print(f"{'='*60}")
                print(f"\nProgress saved. Run again to resume.")
                break

            except Exception as e:
                consecutive_errors += 1
                print(f"  Error: {e}")
                if consecutive_errors >= max_consecutive_errors:
                    print(f"\nToo many errors. Progress saved.")
                    break

        if verbose:
            print(f"\nScraped {len(gamelogs_cache)} players with gamelogs")
            print(f"Gamelogs saved to: {get_gamelogs_cache_path()}")
        return

    if args.all_players:
        # Scrape full game logs for ALL players you've seen
        if verbose:
            print("Scraping game logs for ALL players you've seen...")
            print("(This provides comprehensive career data)\n")

        player_ids, player_names = get_players_from_games(get_project_root())
        if not player_ids:
            print("No players found. Run the main processor first to cache game data.")
            return

        print(f"Found {len(player_ids)} total players you've seen")

        # Load existing caches
        career_cache = load_career_firsts_cache()
        gamelogs_cache = load_gamelogs_cache()

        # Filter to players not yet scraped for gamelogs
        if not args.refresh:
            player_ids = {pid for pid in player_ids if pid not in gamelogs_cache}
            print(f"Players needing scraping: {len(player_ids)}")

        if not player_ids:
            print("All players already scraped! Use --refresh to re-scrape.")
            return

        # Estimate time
        est_requests = len(player_ids) * 25  # ~25 requests per player
        est_time_min = (est_requests * args.delay) / 60
        print(f"Estimated time: ~{est_time_min:.0f} minutes (~{est_time_min/60:.1f} hours)\n")

        scraper = create_scraper()
        consecutive_errors = 0
        max_consecutive_errors = 3
        player_list = sorted(player_ids)

        for i, player_id in enumerate(player_list, 1):
            name = player_names.get(player_id, player_id)
            if verbose:
                print(f"[{i}/{len(player_list)}] {name} ({player_id})")

            try:
                firsts = find_career_firsts(player_id, scraper, verbose=verbose, store_gamelogs=True)

                # Save to career_firsts cache
                career_cache[player_id] = {k: v for k, v in firsts.items() if k != 'gamelogs'}
                career_cache[player_id]['player_name'] = name
                save_career_firsts_cache(career_cache)

                # Save gamelogs to separate cache
                if firsts.get('gamelogs'):
                    gamelogs_cache[player_id] = {
                        'name': name,
                        'gamelogs': firsts['gamelogs']
                    }
                    save_gamelogs_cache(gamelogs_cache)

                consecutive_errors = 0

            except RateLimitError as e:
                print(f"\n{'='*60}")
                print(f"⚠️  RATE LIMITED: {e}")
                print(f"{'='*60}")
                print(f"\nProgress saved. Run again to resume.")
                break

            except Exception as e:
                consecutive_errors += 1
                print(f"  Error: {e}")
                if consecutive_errors >= max_consecutive_errors:
                    print(f"\nToo many errors. Progress saved.")
                    break

        if verbose:
            print(f"\nScraped {len(gamelogs_cache)} players with gamelogs")
            print(f"Gamelogs saved to: {get_gamelogs_cache_path()}")
        return

    if args.player:
        # Scrape single player
        player_ids = {args.player}
        player_names = {}
        refresh = args.refresh
    elif args.refresh_year:
        # Refresh only players from a specific year
        if verbose:
            print(f"Extracting player IDs from {args.refresh_year} games...")
        player_ids, player_names = get_players_from_games(get_project_root(), year=args.refresh_year)
        if verbose:
            print(f"Found {len(player_ids)} unique players from {args.refresh_year}\n")
        refresh = True  # Force refresh for year-specific updates
    else:
        # Get all players from attended games
        if verbose:
            print("Extracting player IDs from cached game data...")
        player_ids, player_names = get_players_from_games(get_project_root())
        if verbose:
            print(f"Found {len(player_ids)} unique players\n")
        refresh = args.refresh

    if not player_ids:
        print("No player IDs found. Run the main processor first to cache game data.")
        sys.exit(1)

    # Scrape career firsts
    cache = scrape_career_firsts_for_players(
        player_ids,
        refresh=refresh,
        delay=args.delay,
        verbose=verbose,
        player_names=player_names
    )

    if verbose:
        print(f"\nScraped {len(cache)} players total")
        print(f"Cache saved to: {get_cache_path() / 'career_firsts.json'}")

        # Show witnessed firsts if any
        attended = get_attended_game_dates()
        witnessed = find_witnessed_firsts(cache, attended)

        if witnessed:
            print(f"\n{'='*60}")
            print(f"CAREER FIRSTS YOU WITNESSED: {len(witnessed)}")
            print(f"{'='*60}\n")
            for w in sorted(witnessed, key=lambda x: x['date'])[:10]:
                print(f"  • {w['milestone']} - {w['player_name']} ({w['date']})")
            if len(witnessed) > 10:
                print(f"  ... and {len(witnessed) - 10} more")


if __name__ == "__main__":
    main()
