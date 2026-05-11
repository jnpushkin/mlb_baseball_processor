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

from ..utils.http import create_retry_session, get_with_retry

_session = create_retry_session()


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
                response = get_with_retry(_session, url, headers=headers, timeout=timeout)

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

    from bs4 import Comment as _Comment
    soup = BeautifulSoup(html, 'html.parser')

    # Collect tables from main soup + any tables hidden inside HTML comments.
    # Don't mutate the tree — parse comments into a separate soup.
    candidate_tables = list(soup.find_all('table'))
    for c in soup.find_all(string=lambda t: isinstance(t, _Comment)):
        if '<table' in str(c):
            candidate_tables.extend(BeautifulSoup(str(c), 'html.parser').find_all('table'))

    # Return earliest year across all standard batting/pitching tables —
    # matters for two-way / role-switched players (e.g., OF→P) whose
    # batting and pitching tables report different first years.
    target_ids = {
        'players_standard_batting', 'players_standard_pitching',
        'batting_standard', 'pitching_standard',
    }
    earliest = None
    for table in candidate_tables:
        if table.get('id') not in target_ids:
            continue
        tbody = table.find('tbody')
        if not tbody:
            continue
        for row in tbody.find_all('tr'):
            cls = row.get('class', [])
            if 'thead' in cls or 'spacer' in cls:
                continue
            year_cell = (row.find('th', {'data-stat': 'year_id'})
                         or row.find('th', {'data-stat': 'year_ID'})
                         or row.find('td', {'data-stat': 'year_id'})
                         or row.find('td', {'data-stat': 'year_ID'}))
            if not year_cell:
                continue
            try:
                year = int(year_cell.get_text(strip=True)[:4])
            except ValueError:
                continue
            if earliest is None or year < earliest:
                earliest = year
            break  # first row in this table's tbody is the earliest
    return earliest


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
        'BFP': ['p_bfp', 'BF'],
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

        # Parse the Decision column for W/L/SV. BREF codes:
        #   W(x-y)=win, L(x-y)=loss, S(n)/SV(n)=save,
        #   BW(x-y)=blown save + win, BL(x-y)=blown save + loss,
        #   BS(n)=blown save (no W/L), H(n)/HLD(n)=hold (no W/L)
        dec_cell = row.find('td', {'data-stat': 'p_game_decision'})
        if not dec_cell:
            dec_cell = row.find('td', {'data-stat': 'Dec'})
        if not dec_cell:
            dec_cell = row.find('td', {'data-stat': 'dec'})
        if dec_cell:
            prefix = dec_cell.get_text(strip=True).upper().split('(')[0]
            if 'W' in prefix:
                game['W'] = 1
            elif 'L' in prefix and 'HLD' not in prefix:
                game['L'] = 1
            elif prefix in ('S', 'SV'):
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

        # Skip "announced but never pitched" appearances (IP=0 AND BFP=0).
        # BREF's standard page excludes these from career G; we must too.
        if game.get('date') and (game.get('IP', 0) > 0 or game.get('BFP', 0) > 0):
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
    pre_year_batting = {}
    pre_year_pitching = {}

    for year in range(debut_year, current_year + 1):
        # Snapshot totals before processing current year (for incremental baseline)
        if year == current_year:
            pre_year_batting = batting_totals.copy()
            pre_year_pitching = pitching_totals.copy()
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

    # Store final career totals and prior-year baseline for incremental updates
    result['career_totals'] = {
        'batting': {k: v for k, v in batting_totals.items() if v > 0},
        'pitching': {k: v for k, v in pitching_totals.items() if v > 0},
    }
    # Baseline = totals at end of previous year (for incremental updates to start from)
    result['last_full_year'] = current_year - 1
    result['career_totals_baseline'] = {
        'batting': {k: v for k, v in pre_year_batting.items() if v > 0},
        'pitching': {k: v for k, v in pre_year_pitching.items() if v > 0},
    }

    # Clean up empty milestone lists
    result['batting_milestones'] = {k: v for k, v in result['batting_milestones'].items() if v}
    result['pitching_milestones'] = {k: v for k, v in result['pitching_milestones'].items() if v}

    return result


# --- MLB API-based career firsts (real-time, no BREF lag) ---

def _mlb_game_id_from_split(game: dict, dh_dates: set = None) -> str:
    """Build a BREF-format game ID from an MLB API gameLog split.

    Format: {bref_home_code}{YYYYMMDD}{suffix}. Suffix uses the correct
    '1'/'2' for doubleheader games when known, '0' for single games. DH
    detection requires dh_dates — the set of dates where the player appeared
    in both games of a DH (gameLog shows gameNumber=1 and 2 for the same
    date). Without that context, gameNumber=2 still maps to '2' (safe),
    gameNumber=1 defaults to '0'.
    """
    from ..parsers.mlb_api_parser import TEAM_ID_TO_CODE
    from .download_bref import BREF_TEAM_CODES
    date = game.get('date', '')
    if not date or len(date) < 10:
        return str(game.get('game', {}).get('gamePk', ''))
    yyyymmdd = date.replace('-', '')
    if game.get('isHome'):
        team_id = game.get('team', {}).get('id')
    else:
        team_id = game.get('opponent', {}).get('id')
    mlb_code = TEAM_ID_TO_CODE.get(team_id, 'UNK')
    bref_code = BREF_TEAM_CODES.get(mlb_code, mlb_code)
    game_num = game.get('game', {}).get('gameNumber', 1)
    if game_num == 2:
        suffix = '2'
    elif dh_dates and date in dh_dates:
        suffix = '1'
    else:
        suffix = '0'
    return f"{bref_code}{yyyymmdd}{suffix}"


_SCHEDULE_CACHE = {}  # year -> {gamePk: (date_iso, doubleHeader_flag)}
_SCHEDULE_LOCKS = {}  # year -> per-year Lock
_SCHEDULE_LOCKS_MUTEX = None  # lazily created


def _get_season_dh_map(year: str, session) -> dict:
    """Return {gamePk: (date_iso, doubleHeader)} for a season, fetching once.

    Thread-safe: per-year lock ensures only one worker fetches a given season;
    other workers block briefly, then read from cache on wake. After the
    first hit for a season, all subsequent lookups are O(1).
    """
    import threading
    global _SCHEDULE_LOCKS_MUTEX
    if year in _SCHEDULE_CACHE:
        return _SCHEDULE_CACHE[year]
    if _SCHEDULE_LOCKS_MUTEX is None:
        _SCHEDULE_LOCKS_MUTEX = threading.Lock()
    with _SCHEDULE_LOCKS_MUTEX:
        if year not in _SCHEDULE_LOCKS:
            _SCHEDULE_LOCKS[year] = threading.Lock()
        lock = _SCHEDULE_LOCKS[year]
    with lock:
        if year in _SCHEDULE_CACHE:
            return _SCHEDULE_CACHE[year]
        url = (f"https://statsapi.mlb.com/api/v1/schedule"
               f"?sportId=1&season={year}&gameType=R")
        try:
            r = session.get(url, timeout=20)
            if r.status_code != 200:
                _SCHEDULE_CACHE[year] = {}
                return {}
            m = {}
            for day in r.json().get('dates', []):
                date_iso = day.get('date', '')
                for game in day.get('games', []):
                    pk = game.get('gamePk')
                    if pk:
                        m[pk] = (date_iso, game.get('doubleHeader', 'N'))
            _SCHEDULE_CACHE[year] = m
            return m
        except Exception:
            _SCHEDULE_CACHE[year] = {}
            return {}


def _build_dh_dates(batting_games: list, pitching_games: list, session=None) -> set:
    """Identify dates that are doubleheaders (for the player's games).

    Uses globally-cached MLB schedule per season. Handles "scheduled DH,
    game 2 rained out" (still flagged Y/S) and "player in only one DH
    game" cases. Falls back to gameNumber=2 heuristic if schedule fetch
    for a season fails.
    """
    import requests
    seasons_pks = {}  # year -> set of pks
    for g in batting_games + pitching_games:
        d = g.get('date', '')
        pk = g.get('game', {}).get('gamePk')
        if d and len(d) >= 4 and pk:
            seasons_pks.setdefault(d[:4], set()).add(pk)

    if not seasons_pks:
        return set()

    sess = session or requests.Session()
    dh_dates = set()
    for year, pks in seasons_pks.items():
        dh_map = _get_season_dh_map(year, sess)
        if not dh_map:
            # Per-season fallback: gameNumber=2 heuristic
            for g in batting_games + pitching_games:
                d = g.get('date', '')
                if d and d[:4] == year and g.get('game', {}).get('gameNumber') == 2:
                    dh_dates.add(d)
            continue
        for pk in pks:
            if pk in dh_map:
                date_iso, dh = dh_map[pk]
                if dh != 'N':
                    dh_dates.add(date_iso)
    return dh_dates
    dh_dates = set()
    for g in batting_games + pitching_games:
        if g.get('game', {}).get('gameNumber') == 2:
            d = g.get('date', '')
            if d:
                dh_dates.add(d)
    return dh_dates


# MLB API field -> our stat key mapping (G handled separately via combined gamelogs)
_API_BATTING_MAP = {
    'hits': 'H', 'homeRuns': 'HR', 'rbi': 'RBI', 'doubles': '2B',
    'triples': '3B', 'baseOnBalls': 'BB', 'stolenBases': 'SB',
    'runs': 'R', 'totalBases': 'TB',
}
_API_PITCHING_MAP = {
    'wins': 'W', 'saves': 'SV', 'strikeOuts': 'SO', 'inningsPitched': 'IP',
    'gamesStarted': 'GS', 'completeGames': 'CG', 'shutouts': 'SHO',
}


def _extend_career_firsts_mlb_api(mlb_id: int, player_id: str, player_name: str,
                                   baseline: dict, current_year: int,
                                   verbose: bool, session) -> dict | None:
    """Extend a cached career-firsts entry by fetching only the new years.

    Returns a fresh result dict in the same shape as ``find_career_firsts_mlb_api``.
    Returns None on parse-time issues so the caller can fall back to a full
    scrape. Does not handle network errors (those propagate).
    """
    last_full_year = baseline.get('last_full_year')
    if not isinstance(last_full_year, int):
        return None
    years_to_fetch = list(range(last_full_year + 1, current_year + 1))

    label = player_name or player_id

    if not years_to_fetch:
        # Cache already covers through current_year — just refresh scraped_at.
        if verbose:
            print(f"  ⚡ MLB API career firsts for {label} (cached, no new years)")
        refreshed = json.loads(json.dumps(baseline))  # deep copy via json round-trip
        refreshed['player_id'] = player_id
        refreshed['scraped_at'] = datetime.now().isoformat()
        return refreshed

    if verbose:
        years_label = (str(years_to_fetch[0]) if len(years_to_fetch) == 1
                       else f"{years_to_fetch[0]}-{years_to_fetch[-1]}")
        print(f"  ⚡ MLB API career firsts for {label} (mlb_id={mlb_id}, incremental {years_label})...")

    batting_games = _fetch_api_gamelogs_for_years(session, mlb_id, 'hitting', years_to_fetch)
    pitching_games = _fetch_api_gamelogs_for_years(session, mlb_id, 'pitching', years_to_fetch)

    if verbose:
        print(f"    +Batting games: {len(batting_games)}, +Pitching games: {len(pitching_games)}")

    # Retirement check. If the player just crossed into "retired" territory
    # AND we don't have cached lasts to extend, we can't compute lasts from
    # the incremental fetch alone (their final HR may be from a year we
    # didn't refetch). Bail to trigger a full re-scrape.
    new_max_year = max(
        (int((g.get('date') or '0000')[:4]) for g in batting_games + pitching_games),
        default=0,
    )
    baseline_max_year = baseline.get('max_game_year') or 0
    max_game_year_now = max(new_max_year, baseline_max_year)
    is_retired_now = max_game_year_now > 0 and max_game_year_now < (current_year - 1)
    baseline_had_lasts = bool(baseline.get('batting_lasts') or baseline.get('pitching_lasts'))
    if is_retired_now and not baseline_had_lasts:
        if verbose:
            print(f"    ↩ Newly retired (last game {max_game_year_now}); falling back to full fetch for lasts.")
        return None

    base_batting = dict(baseline.get('career_totals_baseline', {}).get('batting', {})) or {}
    base_pitching = dict(baseline.get('career_totals_baseline', {}).get('pitching', {})) or {}

    # Running totals seeded from the cached baseline (= totals through end of last_full_year).
    batting_totals = {stat: int(base_batting.get(stat, 0)) for stat in BATTING_MILESTONES.keys()}
    pitching_totals = {stat: int(base_pitching.get(stat, 0)) for stat in PITCHING_MILESTONES.keys()}

    # Keep only cached milestones from years <= last_full_year — current/recent
    # years get re-derived from the fresh fetch.
    def _keep_immutable(ms_list):
        return [m for m in ms_list if isinstance(m.get('year'), int) and m['year'] <= last_full_year]

    cached_batting_ms = baseline.get('batting_milestones', {}) or {}
    cached_pitching_ms = baseline.get('pitching_milestones', {}) or {}

    new_batting_milestones = {stat: list(_keep_immutable(cached_batting_ms.get(stat, []))) for stat in BATTING_MILESTONES}
    new_pitching_milestones = {stat: list(_keep_immutable(cached_pitching_ms.get(stat, []))) for stat in PITCHING_MILESTONES}

    batting_milestones_reached = {stat: {m['number'] for m in new_batting_milestones[stat] if 'number' in m}
                                  for stat in BATTING_MILESTONES}
    pitching_milestones_reached = {stat: {m['number'] for m in new_pitching_milestones[stat] if 'number' in m}
                                   for stat in PITCHING_MILESTONES}

    # Firsts are immutable too; keep cached, re-discover any missing from fetched games.
    cached_batting_firsts = {k: v for k, v in (baseline.get('batting_firsts') or {}).items()
                              if isinstance(v, dict) and isinstance(v.get('year'), int) and v['year'] <= last_full_year}
    cached_pitching_firsts = {k: v for k, v in (baseline.get('pitching_firsts') or {}).items()
                               if isinstance(v, dict) and isinstance(v.get('year'), int) and v['year'] <= last_full_year}

    batting_needed = set(BATTING_FIRSTS.keys()) - set(cached_batting_firsts.keys())
    pitching_needed = set(PITCHING_FIRSTS.keys()) - set(cached_pitching_firsts.keys())

    new_batting_firsts = dict(cached_batting_firsts)
    new_pitching_firsts = dict(cached_pitching_firsts)

    # Lasts ride alongside firsts: cached entries are immutable history;
    # walks below may overwrite for stats that recurred in the new years.
    new_batting_lasts = dict(baseline.get('batting_lasts') or {})
    new_pitching_lasts = dict(baseline.get('pitching_lasts') or {})

    # Combined chronological list across fetched years for the G milestone.
    dh_dates = _build_dh_dates(batting_games, pitching_games, session=session)
    seen_pks = set()
    combined_games_chrono = []
    for game in sorted(batting_games + pitching_games, key=lambda g: g.get('date', '')):
        pk = game.get('game', {}).get('gamePk')
        if pk and pk not in seen_pks:
            seen_pks.add(pk)
            combined_games_chrono.append((
                game.get('date', ''),
                _mlb_game_id_from_split(game, dh_dates),
                game.get('opponent', {}).get('name', ''),
            ))

    g_total = batting_totals.get('G', 0)
    g_milestones_reached = set(batting_milestones_reached.get('G', set()))
    pre_year_g = g_total  # default — only updated if a current_year game appears

    pre_year_g_locked = False
    for date_str, game_id, opponent in combined_games_chrono:
        year = int(date_str[:4]) if date_str else 0
        if year == current_year and not pre_year_g_locked:
            pre_year_g = g_total
            pre_year_g_locked = True
        old_g = g_total
        g_total += 1
        for threshold in BATTING_MILESTONES['G']:
            if old_g < threshold <= g_total and threshold not in g_milestones_reached:
                g_milestones_reached.add(threshold)
                new_batting_milestones.setdefault('G', []).append({
                    'number': threshold,
                    'date': date_str.replace('-', ''),
                    'game_id': game_id,
                    'opponent': opponent,
                    'year': year,
                    'milestone': f"Career Game #{threshold}",
                    'career_total_after': g_total,
                })
                if verbose:
                    print(f"    ⭐ Career Game #{threshold}: {date_str}")
    batting_totals['G'] = g_total

    # Walk fetched batting games for non-G stats and firsts.
    pre_year_batting_nonG = {}  # snapshot at start of current_year, non-G stats only
    pre_year_batting_locked = False
    for game in batting_games:
        stat_data = game.get('stat', {})
        date_str = game.get('date', '')
        year = int(date_str[:4]) if date_str else 0
        opponent = game.get('opponent', {}).get('name', '')
        game_id = _mlb_game_id_from_split(game, dh_dates)

        if year == current_year and not pre_year_batting_locked:
            pre_year_batting_nonG = {k: v for k, v in batting_totals.items() if k != 'G'}
            pre_year_batting_locked = True

        for api_field, our_stat in _API_BATTING_MAP.items():
            val = stat_data.get(api_field, 0)
            if not val or val <= 0:
                continue
            if our_stat in batting_needed:
                new_batting_firsts[our_stat] = {
                    'date': date_str.replace('-', ''),
                    'game_id': game_id,
                    'opponent': opponent,
                    'year': year,
                    'milestone': BATTING_FIRSTS[our_stat],
                }
                batting_needed.discard(our_stat)
            stat_name = STAT_NAMES.get(our_stat, our_stat)
            new_batting_lasts[our_stat] = {
                'date': date_str.replace('-', ''),
                'game_id': game_id,
                'opponent': opponent,
                'year': year,
                'milestone': f"Final Career {stat_name}",
                'value_in_game': val,
            }

        for stat_key in BATTING_MILESTONES:
            if stat_key == 'G':
                continue
            api_field = next((k for k, v in _API_BATTING_MAP.items() if v == stat_key), None)
            game_value = stat_data.get(api_field, 0) if api_field else 0
            if game_value > 0:
                old_total = batting_totals[stat_key]
                batting_totals[stat_key] += game_value
                new_total = batting_totals[stat_key]
                for threshold in BATTING_MILESTONES[stat_key]:
                    if old_total < threshold <= new_total and threshold not in batting_milestones_reached[stat_key]:
                        batting_milestones_reached[stat_key].add(threshold)
                        stat_name = STAT_NAMES.get(stat_key, stat_key)
                        new_batting_milestones.setdefault(stat_key, []).append({
                            'number': threshold,
                            'date': date_str.replace('-', ''),
                            'game_id': game_id,
                            'opponent': opponent,
                            'year': year,
                            'milestone': f"Career {stat_name} #{threshold}",
                            'career_total_after': new_total,
                        })
                        if verbose:
                            print(f"    ⭐ Career {stat_name} #{threshold}: {date_str}")

    # Walk fetched pitching games (G = pitching appearances).
    pre_year_pitching_snap = {}
    pre_year_pitching_locked = False
    for game in pitching_games:
        stat_data = game.get('stat', {})
        date_str = game.get('date', '')
        year = int(date_str[:4]) if date_str else 0
        opponent = game.get('opponent', {}).get('name', '')
        game_id = _mlb_game_id_from_split(game, dh_dates)

        if year == current_year and not pre_year_pitching_locked:
            pre_year_pitching_snap = pitching_totals.copy()
            pre_year_pitching_locked = True

        for api_field, our_stat in _API_PITCHING_MAP.items():
            if our_stat == 'G':
                continue
            val = stat_data.get(api_field, 0)
            if our_stat == 'IP':
                val = parse_ip(str(val))
            if not val or val <= 0:
                continue
            if our_stat in pitching_needed:
                new_pitching_firsts[our_stat] = {
                    'date': date_str.replace('-', ''),
                    'game_id': game_id,
                    'opponent': opponent,
                    'year': year,
                    'milestone': PITCHING_FIRSTS[our_stat],
                }
                pitching_needed.discard(our_stat)
            stat_name = STAT_NAMES.get(our_stat, our_stat)
            new_pitching_lasts[our_stat] = {
                'date': date_str.replace('-', ''),
                'game_id': game_id,
                'opponent': opponent,
                'year': year,
                'milestone': f"Final Career {stat_name}",
                'value_in_game': val,
            }

        pitching_totals['G'] = pitching_totals.get('G', 0) + 1
        for stat_key in PITCHING_MILESTONES:
            if stat_key == 'G':
                game_value = 1
            else:
                api_field = next((k for k, v in _API_PITCHING_MAP.items() if v == stat_key), None)
                if api_field and stat_key == 'IP':
                    game_value = parse_ip(str(stat_data.get(api_field, '0')))
                else:
                    game_value = stat_data.get(api_field, 0) if api_field else 0
            if game_value > 0:
                if stat_key != 'G':
                    old_total = pitching_totals[stat_key]
                    pitching_totals[stat_key] += game_value
                    new_total = pitching_totals[stat_key]
                else:
                    old_total = pitching_totals['G'] - 1
                    new_total = pitching_totals['G']
                for threshold in PITCHING_MILESTONES[stat_key]:
                    if old_total < threshold <= new_total and threshold not in pitching_milestones_reached[stat_key]:
                        pitching_milestones_reached[stat_key].add(threshold)
                        stat_name = STAT_NAMES.get(stat_key, stat_key)
                        milestone_label = f"Career Pitching {stat_name} #{threshold}" if stat_key == 'G' else f"Career {stat_name} #{threshold}"
                        new_pitching_milestones.setdefault(stat_key, []).append({
                            'number': threshold,
                            'date': date_str.replace('-', ''),
                            'game_id': game_id,
                            'opponent': opponent,
                            'year': year,
                            'milestone': milestone_label,
                            'career_total_after': new_total,
                        })
                        if verbose:
                            human = f"Pitching Game #{threshold}" if stat_key == 'G' else f"{stat_name} #{threshold}"
                            print(f"    ⭐ Career {human}: {date_str}")

    # Sort milestones by date so cached-old + freshly-found land in chronological order.
    for stat in new_batting_milestones:
        new_batting_milestones[stat].sort(key=lambda m: m.get('date', ''))
    for stat in new_pitching_milestones:
        new_pitching_milestones[stat].sort(key=lambda m: m.get('date', ''))

    # New baseline = totals at end of (current_year - 1) = right before the
    # first current_year game we walked. If no current_year games appeared,
    # the baseline is just our running totals.
    if pre_year_batting_locked:
        new_baseline_batting = {**pre_year_batting_nonG, 'G': pre_year_g}
    else:
        new_baseline_batting = dict(batting_totals)
    new_baseline_batting = {k: v for k, v in new_baseline_batting.items() if v > 0}

    if pre_year_pitching_locked:
        new_baseline_pitching = dict(pre_year_pitching_snap)
    else:
        new_baseline_pitching = dict(pitching_totals)
    new_baseline_pitching = {k: v for k, v in new_baseline_pitching.items() if v > 0}

    # Final retirement gate (mirrors the full path): drop lasts for active
    # players and remove the G "final game" slot — already covered elsewhere.
    if not is_retired_now:
        new_batting_lasts = {}
        new_pitching_lasts = {}
    new_batting_lasts.pop('G', None)
    new_pitching_lasts.pop('G', None)

    return {
        'player_id': player_id,
        'batting_firsts': new_batting_firsts,
        'pitching_firsts': new_pitching_firsts,
        'batting_milestones': {k: v for k, v in new_batting_milestones.items() if v},
        'pitching_milestones': {k: v for k, v in new_pitching_milestones.items() if v},
        'batting_lasts': new_batting_lasts,
        'pitching_lasts': new_pitching_lasts,
        'max_game_year': max_game_year_now,
        'is_retired': is_retired_now,
        'career_totals': {
            'batting': {k: v for k, v in batting_totals.items() if v > 0},
            'pitching': {k: v for k, v in pitching_totals.items() if v > 0},
        },
        'last_full_year': current_year - 1,
        'career_totals_baseline': {
            'batting': new_baseline_batting,
            'pitching': new_baseline_pitching,
        },
        'scraped_at': datetime.now().isoformat(),
    }


def find_career_firsts_mlb_api(mlb_id: int, player_id: str, player_name: str = '',
                                verbose: bool = True, session=None,
                                baseline: dict | None = None) -> dict:
    """Find career firsts and milestones using MLB API game logs (instant, no BREF needed).

    G (total games) is tracked by merging batting + pitching gamelogs into
    one chronological list of unique games, so a player who bats and pitches
    in the same game counts it once. G milestones go in batting_milestones.

    Args:
        mlb_id: MLB Stats API player ID (integer)
        player_id: BREF-style player ID (for cache key compatibility)
        player_name: Display name (for logging)
        verbose: Print progress
        session: Optional requests Session.
        baseline: Optional cached entry from a prior scrape. When provided,
            past milestones (which never change) are reused and only the years
            after ``baseline['last_full_year']`` are fetched from the API.
            ~5-10x fewer HTTP calls per veteran player.

    Returns:
        Same dict structure as find_career_firsts() for cache compatibility.
    """
    if session is None:
        session = _session
    current_year = datetime.now().year

    # Fast path: extend a cached entry by fetching only the new years.
    # `max_game_year` was added with the career-lasts work — legacy entries
    # without it can't reliably tell active from retired, so they fall through
    # to a full fetch on first encounter (one-time backfill).
    if baseline and isinstance(baseline.get('last_full_year'), int) \
            and isinstance(baseline.get('career_totals_baseline'), dict) \
            and isinstance(baseline.get('max_game_year'), int):
        result = _extend_career_firsts_mlb_api(
            mlb_id, player_id, player_name, baseline,
            current_year=current_year, verbose=verbose, session=session,
        )
        if result is not None:
            return result
        # If the incremental path returned None (cache too stale or schema
        # mismatch), fall through to a full re-scrape.

    if verbose:
        label = player_name or player_id
        print(f"  ⚡ MLB API career firsts for {label} (mlb_id={mlb_id})...")

    result = {
        'player_id': player_id,
        'batting_firsts': {},
        'pitching_firsts': {},
        'batting_milestones': {},
        'pitching_milestones': {},
        'batting_lasts': {},
        'pitching_lasts': {},
        'career_totals': {},
        'scraped_at': datetime.now().isoformat(),
    }

    batting_games = _fetch_api_gamelogs(session, mlb_id, 'hitting')
    pitching_games = _fetch_api_gamelogs(session, mlb_id, 'pitching')

    if verbose:
        print(f"    Batting games: {len(batting_games)}, Pitching games: {len(pitching_games)}")

    # batting.G = "total career games played" (= MLB hitting.G), tracked via
    # union of batting + pitching gamelogs by gamePk so two-way players (Ohtani)
    # count each game once and pure pitchers get total appearances. Pitching.G
    # is tracked separately later as pitching appearances.
    # Build a chronological sequence of unique games for G tracking.
    dh_dates = _build_dh_dates(batting_games, pitching_games, session=session)
    seen_pks = set()
    combined_games_chrono = []  # (date_str, mlb_game_id, opponent_name)
    for game in sorted(batting_games + pitching_games, key=lambda g: g.get('date', '')):
        pk = game.get('game', {}).get('gamePk')
        if pk and pk not in seen_pks:
            seen_pks.add(pk)
            combined_games_chrono.append((
                game.get('date', ''),
                _mlb_game_id_from_split(game, dh_dates),
                game.get('opponent', {}).get('name', ''),
            ))

    g_total = 0
    g_milestones_reached = set()
    pre_year_g = 0

    # --- Process batting stats ---
    batting_needed = set(BATTING_FIRSTS.keys())
    batting_totals = {stat: 0 for stat in BATTING_MILESTONES.keys()}
    batting_milestones_reached = {stat: set() for stat in BATTING_MILESTONES.keys()}
    for stat in BATTING_MILESTONES:
        result['batting_milestones'][stat] = []
    pre_year_batting = {}

    # Track G milestones from the combined chronological list (single source of
    # truth for "Career Game #N" in batting context = total MLB games)
    for date_str, game_id, opponent in combined_games_chrono:
        year = int(date_str[:4]) if date_str else 0
        if year == current_year and pre_year_g == 0 and g_total > 0:
            pre_year_g = g_total
        old_g = g_total
        g_total += 1
        for threshold in BATTING_MILESTONES['G']:
            if old_g < threshold <= g_total and threshold not in g_milestones_reached:
                g_milestones_reached.add(threshold)
                result['batting_milestones']['G'].append({
                    'number': threshold,
                    'date': date_str.replace('-', ''),
                    'game_id': game_id,
                    'opponent': opponent,
                    'year': year,
                    'milestone': f"Career Game #{threshold}",
                    'career_total_after': g_total,
                })
                if verbose:
                    print(f"    ⭐ Career Game #{threshold}: {date_str}")
    batting_totals['G'] = g_total

    for game in batting_games:
        stat_data = game.get('stat', {})
        date_str = game.get('date', '')
        year = int(date_str[:4]) if date_str else 0
        opponent = game.get('opponent', {}).get('name', '')
        game_id = _mlb_game_id_from_split(game, dh_dates)

        if year == current_year and not pre_year_batting:
            pre_year_batting = {k: v for k, v in batting_totals.items() if k != 'G'}

        # Check firsts + record "last" sighting (overwrites each pass so the
        # final iteration leaves the latest game for each stat in place).
        for api_field, our_stat in _API_BATTING_MAP.items():
            val = stat_data.get(api_field, 0)
            if not val or val <= 0:
                continue
            if our_stat in batting_needed:
                result['batting_firsts'][our_stat] = {
                    'date': date_str.replace('-', ''),
                    'game_id': game_id,
                    'opponent': opponent,
                    'year': year,
                    'milestone': BATTING_FIRSTS[our_stat],
                }
                batting_needed.discard(our_stat)
            stat_name = STAT_NAMES.get(our_stat, our_stat)
            result['batting_lasts'][our_stat] = {
                'date': date_str.replace('-', ''),
                'game_id': game_id,
                'opponent': opponent,
                'year': year,
                'milestone': f"Final Career {stat_name}",
                'value_in_game': val,
            }

        # Update running totals and check milestones for non-G stats
        for stat_key in BATTING_MILESTONES:
            if stat_key == 'G':
                continue
            api_field = next((k for k, v in _API_BATTING_MAP.items() if v == stat_key), None)
            game_value = stat_data.get(api_field, 0) if api_field else 0

            if game_value > 0:
                old_total = batting_totals[stat_key]
                batting_totals[stat_key] += game_value
                new_total = batting_totals[stat_key]

                for threshold in BATTING_MILESTONES[stat_key]:
                    if old_total < threshold <= new_total and threshold not in batting_milestones_reached[stat_key]:
                        batting_milestones_reached[stat_key].add(threshold)
                        stat_name = STAT_NAMES.get(stat_key, stat_key)
                        result['batting_milestones'][stat_key].append({
                            'number': threshold,
                            'date': date_str.replace('-', ''),
                            'game_id': game_id,
                            'opponent': opponent,
                            'year': year,
                            'milestone': f"Career {stat_name} #{threshold}",
                            'career_total_after': new_total,
                        })
                        if verbose:
                            print(f"    ⭐ Career {stat_name} #{threshold}: {date_str}")

    # --- Process pitching stats (G tracks pitching appearances separately) ---
    pitching_needed = set(PITCHING_FIRSTS.keys())
    pitching_totals = {stat: 0 for stat in PITCHING_MILESTONES.keys()}
    pitching_milestones_reached = {stat: set() for stat in PITCHING_MILESTONES.keys()}
    for stat in PITCHING_MILESTONES:
        result['pitching_milestones'][stat] = []
    pre_year_pitching = {}

    for game in pitching_games:
        stat_data = game.get('stat', {})
        date_str = game.get('date', '')
        year = int(date_str[:4]) if date_str else 0
        opponent = game.get('opponent', {}).get('name', '')
        game_id = _mlb_game_id_from_split(game, dh_dates)

        if year == current_year and not pre_year_pitching:
            pre_year_pitching = pitching_totals.copy()

        # Check firsts + record "last" sighting (overwrites each pass).
        # G last (career final pitching appearance) is already covered by
        # the Final Games view — skip it here to avoid duplication.
        for api_field, our_stat in _API_PITCHING_MAP.items():
            if our_stat == 'G':
                continue
            val = stat_data.get(api_field, 0)
            if our_stat == 'IP':
                val = parse_ip(str(val))
            if not val or val <= 0:
                continue
            if our_stat in pitching_needed:
                result['pitching_firsts'][our_stat] = {
                    'date': date_str.replace('-', ''),
                    'game_id': game_id,
                    'opponent': opponent,
                    'year': year,
                    'milestone': PITCHING_FIRSTS[our_stat],
                }
                pitching_needed.discard(our_stat)
            stat_name = STAT_NAMES.get(our_stat, our_stat)
            result['pitching_lasts'][our_stat] = {
                'date': date_str.replace('-', ''),
                'game_id': game_id,
                'opponent': opponent,
                'year': year,
                'milestone': f"Final Career {stat_name}",
                'value_in_game': val,
            }

        # Update running totals (G = pitching appearances)
        pitching_totals['G'] = pitching_totals.get('G', 0) + 1
        for stat_key in PITCHING_MILESTONES:
            if stat_key == 'G':
                game_value = 1
            else:
                api_field = next((k for k, v in _API_PITCHING_MAP.items() if v == stat_key), None)
                if api_field and stat_key == 'IP':
                    game_value = parse_ip(str(stat_data.get(api_field, '0')))
                else:
                    game_value = stat_data.get(api_field, 0) if api_field else 0

            if game_value > 0:
                if stat_key != 'G':
                    old_total = pitching_totals[stat_key]
                    pitching_totals[stat_key] += game_value
                    new_total = pitching_totals[stat_key]
                else:
                    old_total = pitching_totals['G'] - 1
                    new_total = pitching_totals['G']

                for threshold in PITCHING_MILESTONES[stat_key]:
                    if old_total < threshold <= new_total and threshold not in pitching_milestones_reached[stat_key]:
                        pitching_milestones_reached[stat_key].add(threshold)
                        stat_name = STAT_NAMES.get(stat_key, stat_key)
                        milestone_label = f"Career Pitching {stat_name} #{threshold}" if stat_key == 'G' else f"Career {stat_name} #{threshold}"
                        result['pitching_milestones'][stat_key].append({
                            'number': threshold,
                            'date': date_str.replace('-', ''),
                            'game_id': game_id,
                            'opponent': opponent,
                            'year': year,
                            'milestone': milestone_label,
                            'career_total_after': new_total,
                        })
                        if verbose:
                            label = f"Pitching Game #{threshold}" if stat_key == 'G' else f"{stat_name} #{threshold}"
                            print(f"    ⭐ Career {label}: {date_str}")

    # Store totals and baseline. batting.G = games with PA; pitching.G = pitching
    # appearances (each tracked in its own per-game loop above).
    result['career_totals'] = {
        'batting': {k: v for k, v in batting_totals.items() if v > 0},
        'pitching': {k: v for k, v in pitching_totals.items() if v > 0},
    }
    result['last_full_year'] = current_year - 1
    pre_year_batting_final = pre_year_batting.copy() if pre_year_batting else {}
    pre_year_batting_final['G'] = pre_year_g
    result['career_totals_baseline'] = {
        'batting': {k: v for k, v in pre_year_batting_final.items() if v > 0},
        'pitching': {k: v for k, v in pre_year_pitching.items() if v > 0},
    }

    # Retirement gate for career-lasts. A player who's missed a full season
    # is treated as retired — their stat lasts are now stable history. Players
    # with any games last year or this year are still active and their "last"
    # values would shift, so we drop them.
    last_batting_year = max((int((g.get('date') or '0000')[:4]) for g in batting_games), default=0)
    last_pitching_year = max((int((g.get('date') or '0000')[:4]) for g in pitching_games), default=0)
    max_game_year = max(last_batting_year, last_pitching_year)
    result['max_game_year'] = max_game_year
    is_retired = max_game_year > 0 and max_game_year < (current_year - 1)
    result['is_retired'] = is_retired

    # Drop G (already covered by Final Games tab) and clear lasts for active players.
    result['batting_lasts'].pop('G', None)
    result['pitching_lasts'].pop('G', None)
    if not is_retired:
        result['batting_lasts'] = {}
        result['pitching_lasts'] = {}

    # Clean up empty lists
    result['batting_milestones'] = {k: v for k, v in result['batting_milestones'].items() if v}
    result['pitching_milestones'] = {k: v for k, v in result['pitching_milestones'].items() if v}

    return result


def _fetch_api_gamelogs_for_years(session, mlb_id: int, group: str, years: list[int]) -> list:
    """Fetch game logs for an explicit set of years (skips yearByYear discovery).

    Used by the incremental path — when we already know the player's
    cached baseline year, we don't need to ask the API which seasons exist.
    Empty responses for years the player wasn't active are tolerated.
    """
    splits = []
    for year in sorted(set(years)):
        url = (
            f"https://statsapi.mlb.com/api/v1/people/{mlb_id}/stats"
            f"?stats=gameLog&group={group}&season={year}&gameType=R&sportId=1"
        )
        last_exc = None
        for _ in range(3):
            try:
                resp = get_with_retry(session, url, timeout=15)
                if resp.status_code == 200:
                    for stat_group in resp.json().get('stats', []):
                        splits.extend(stat_group.get('splits', []))
                    last_exc = None
                    break
                last_exc = Exception(f"HTTP {resp.status_code}")
            except Exception as e:
                last_exc = e
        if last_exc is not None:
            raise RuntimeError(f"gameLog {group} {year} for {mlb_id} failed: {last_exc}")
    splits.sort(key=lambda s: s.get('date', ''))
    return splits


def _fetch_api_gamelogs(session, mlb_id: int, group: str) -> list:
    """Fetch all career game logs from MLB API for a player.

    Args:
        session: requests session
        mlb_id: MLB API player ID
        group: 'hitting' or 'pitching'

    Returns:
        List of game split dicts sorted by date, across all seasons.
    """
    current_year = datetime.now().year
    all_splits = []

    # Fetch all seasons at once with yearByYear.
    # Filter to regular-season MLB only — without gameType=R&sportId=1 the API
    # returns minor-league and postseason rows that skew our running totals.
    url = f"https://statsapi.mlb.com/api/v1/people/{mlb_id}/stats?stats=yearByYear&group={group}&gameType=R&sportId=1"
    try:
        resp = get_with_retry(session, url, timeout=15)
        if resp.status_code != 200:
            return []
        years_data = resp.json()
        seasons = set()
        for stat_group in years_data.get('stats', []):
            for split in stat_group.get('splits', []):
                season = split.get('season')
                if season:
                    seasons.add(int(season))
    except Exception:
        # Fallback: just try recent years
        seasons = set(range(max(2015, current_year - 20), current_year + 1))

    # Fetch game logs per season. A silent skip here corrupts career totals
    # (we'd undercount by a whole season's stats), so a hard failure must
    # propagate to the caller — better an errored player than wrong data.
    for year in sorted(seasons):
        url = f"https://statsapi.mlb.com/api/v1/people/{mlb_id}/stats?stats=gameLog&group={group}&season={year}&gameType=R&sportId=1"
        last_exc = None
        for attempt in range(3):
            try:
                resp = get_with_retry(session, url, timeout=15)
                if resp.status_code == 200:
                    for stat_group in resp.json().get('stats', []):
                        all_splits.extend(stat_group.get('splits', []))
                    last_exc = None
                    break
                last_exc = Exception(f"HTTP {resp.status_code}")
            except Exception as e:
                last_exc = e
        if last_exc is not None:
            raise RuntimeError(f"gameLog {group} {year} for {mlb_id} failed: {last_exc}")

    # Sort by date
    all_splits.sort(key=lambda s: s.get('date', ''))
    return all_splits


_API_CAREER_FIRSTS_TTL_SECONDS = 6 * 3600


def update_career_firsts_from_api(game_data: dict, verbose: bool = True, force: bool = False) -> int:
    """Update career firsts cache for all players in a game using MLB API.

    This is the fast path called from add_game — no BREF scraping needed.
    Only updates players who have an mlb_id. Merges results into the
    existing career_firsts.json cache without deleting existing BREF data.

    Skips per-player API hits when the cached entry's ``scraped_at`` is
    within ``_API_CAREER_FIRSTS_TTL_SECONDS`` (6 hours) — an active
    player's milestone counts can't change without a new MLB game, and
    same-day re-runs are the common case. Pass ``force=True`` to bypass.

    Returns number of players whose cache entry was created or refreshed.
    """
    cache_path = get_project_root() / 'cache' / 'career_firsts' / 'career_firsts.json'
    cache = {}
    if cache_path.exists():
        try:
            with open(cache_path, 'r') as f:
                cache = json.load(f)
        except (json.JSONDecodeError, IOError):
            pass

    # Build a bref-id -> mlb-id fallback for BREF-parsed games (where the
    # player rows don't carry mlb_id). Lazy-loaded once and cached.
    _bref_map = None

    def _resolve_mlb_id(pid):
        nonlocal _bref_map
        if _bref_map is None:
            _bref_map = _build_bref_to_mlb_map()
        return _bref_map.get(pid)

    # Collect players with mlb_ids from the game
    players = {}  # player_id -> (mlb_id, name)
    for side in ('home', 'away'):
        for p in game_data.get('batting', {}).get(side, []):
            pid = p.get('player_id', '')
            if not pid:
                continue
            mlb_id = p.get('mlb_id') or _resolve_mlb_id(pid)
            if mlb_id:
                players[pid] = (mlb_id, p.get('name', ''))
        for p in game_data.get('pitching', {}).get(side, []):
            pid = p.get('player_id', '')
            if not pid:
                continue
            mlb_id = p.get('mlb_id') or _resolve_mlb_id(pid)
            if mlb_id:
                players[pid] = (mlb_id, p.get('name', ''))

    if not players:
        return 0

    now = datetime.now()

    def _is_fresh(entry):
        if force or not isinstance(entry, dict):
            return False
        # Legacy entries missing the retirement bookkeeping need a fresh fetch
        # so career_lasts can be computed for any player who's retired.
        if 'is_retired' not in entry or 'max_game_year' not in entry:
            return False
        scraped_at = entry.get('scraped_at')
        if not scraped_at:
            return False
        try:
            return (now - datetime.fromisoformat(scraped_at)).total_seconds() < _API_CAREER_FIRSTS_TTL_SECONDS
        except (ValueError, TypeError):
            return False

    fresh_skipped = sum(1 for pid in players if _is_fresh(cache.get(pid)))
    to_fetch = len(players) - fresh_skipped

    if verbose:
        if to_fetch == 0:
            print(f"  ⏭️  Career firsts: all {len(players)} players cached fresh (<6h)")
        else:
            extra = f" ({fresh_skipped} cached fresh)" if fresh_skipped else ""
            print(f"  ⚡ Updating career firsts via MLB API for {to_fetch} players{extra}...")

    updated = 0
    for pid, (mlb_id, name) in players.items():
        if _is_fresh(cache.get(pid)):
            continue
        try:
            api_result = find_career_firsts_mlb_api(
                mlb_id, pid, name, verbose=verbose,
                baseline=cache.get(pid),
            )

            if pid in cache:
                existing = cache[pid]
                # Additive merge: add new firsts/milestones from API
                # but never overwrite existing BREF data
                for first_type in ('batting_firsts', 'pitching_firsts'):
                    for stat, data in api_result.get(first_type, {}).items():
                        if stat not in existing.get(first_type, {}):
                            existing.setdefault(first_type, {})[stat] = data
                # Replace milestone lists with API data (API has full career,
                # correct G tracking via combined gamelogs)
                for ms_type in ('batting_milestones', 'pitching_milestones'):
                    for stat, ms_list in api_result.get(ms_type, {}).items():
                        existing.setdefault(ms_type, {})[stat] = ms_list
                # Replace lasts wholesale — the API walk has authoritative
                # final-game-with-stat info for retired players, and active
                # players just get an empty dict.
                existing['batting_lasts'] = api_result.get('batting_lasts', {}) or {}
                existing['pitching_lasts'] = api_result.get('pitching_lasts', {}) or {}
                existing['max_game_year'] = api_result.get('max_game_year') or 0
                existing['is_retired'] = bool(api_result.get('is_retired'))
                # Update totals and timestamp
                existing['career_totals'] = api_result['career_totals']
                existing['career_totals_baseline'] = api_result.get('career_totals_baseline', {})
                existing['last_full_year'] = api_result.get('last_full_year')
                existing['scraped_at'] = api_result['scraped_at']
            else:
                cache[pid] = api_result

            updated += 1
        except Exception as e:
            if verbose:
                print(f"    ⚠️ Failed for {name or pid}: {e}")

    # Save cache
    if updated > 0:
        cache_path.parent.mkdir(parents=True, exist_ok=True)
        with open(cache_path, 'w') as f:
            json.dump(cache, f, ensure_ascii=False)
        if verbose:
            print(f"  ✅ Updated {updated} players via MLB API ({len(cache)} total in cache)")

    return updated


# --- Bulk API backfill with BREF discrepancy gate ---

def _build_bref_to_mlb_map() -> dict:
    """Load Chadwick Bureau Register CSVs and return {bref_id: mlb_id}.

    Indexes both key_bbref (major-league ID) and key_bbref_minors (register ID),
    so players with BR register-format IDs (e.g., 'urbaez000fra') resolve too.
    """
    import csv as _csv
    register_dir = get_project_root() / 'register-master' / 'data'
    mapping = {}
    if not register_dir.is_dir():
        return mapping
    for csv_path in sorted(register_dir.glob('people-*.csv')):
        with open(csv_path, 'r', encoding='utf-8', errors='replace') as f:
            reader = _csv.DictReader(f)
            for row in reader:
                mlbam = (row.get('key_mlbam') or '').strip()
                if not mlbam:
                    continue
                try:
                    mlb_id = int(mlbam)
                except ValueError:
                    continue
                for field in ('key_bbref', 'key_bbref_minors'):
                    bref = (row.get(field) or '').strip()
                    if bref and bref not in mapping:
                        mapping[bref] = mlb_id
    return mapping


_MLB_ROSTER_CACHE = {}

def _get_mlb_all_players(session) -> list:
    """Fetch a deduped list of all MLB players across recent seasons, cached."""
    if _MLB_ROSTER_CACHE:
        return _MLB_ROSTER_CACHE['people']
    people_by_id = {}
    for year in (2024, 2025, 2026):
        try:
            url = f"https://statsapi.mlb.com/api/v1/sports/1/players?season={year}&activeSwitch=all"
            r = session.get(url, timeout=15)
            if r.status_code != 200:
                continue
            for p in r.json().get('people', []):
                if p.get('id'):
                    people_by_id[p['id']] = p
        except Exception:
            continue
    _MLB_ROSTER_CACHE['people'] = list(people_by_id.values())
    return _MLB_ROSTER_CACHE['people']


def _parse_bref_id(bref_id: str) -> Optional[tuple]:
    """Extract (last_prefix, first_prefix) from a BREF ID.

    Handles both formats:
      standard:  'susacda01'    → ('susac', 'da')
      register:  'urbaez000fra' → ('urbaez', 'fra')
      register:  'alcant002ism' → ('alcant', 'ism')
    """
    import re
    # Standard: letters + 2 letters + digits at end (e.g. 'susacda01')
    m = re.match(r'^([a-záéíóúñ\-]+)([a-záéíóúñ]{2})\d+$', bref_id.lower())
    if m:
        return m.group(1), m.group(2)
    # Register: letters + 0s (+ digits) + letters (e.g. 'urbaez000fra')
    m = re.match(r'^([a-záéíóúñ\-]+?)0+\d*([a-záéíóúñ]+)$', bref_id.lower())
    if m:
        return m.group(1), m.group(2)
    return None


def _search_mlb_api_by_bref_id(session, bref_id: str) -> Optional[int]:
    """Fallback: resolve an MLB ID for a BREF ID not in Chadwick.

    Parses the BREF ID into name-prefix guesses and matches against the full
    MLB roster (2024-2026, active + inactive). Returns mlb_id only when
    exactly one player matches.
    """
    import unicodedata
    parsed = _parse_bref_id(bref_id)
    if not parsed:
        return None
    last_prefix, first_prefix = parsed

    def ascii_lower(s):
        return ''.join(c for c in unicodedata.normalize('NFD', (s or '').lower())
                       if unicodedata.category(c) != 'Mn').replace('-', '').replace(' ', '')

    last_q = ascii_lower(last_prefix)
    first_q = ascii_lower(first_prefix)
    if not last_q or not first_q:
        return None

    people = _get_mlb_all_players(session)
    candidates = []
    for p in people:
        last = ascii_lower(p.get('lastName'))
        first = ascii_lower(p.get('firstName'))
        if last.startswith(last_q) and first.startswith(first_q):
            candidates.append(p.get('id'))
    return candidates[0] if len(candidates) == 1 else None


def _compare_baseline(bref_entry: dict, api_result: dict, ip_tolerance: float = 0.05) -> list:
    """Compare BREF's end-of-last-full-year baseline vs API's baseline.

    Both baselines should represent career totals through end of the same year
    (BREF last_full_year=2025, API baseline captured just before first 2026 game).
    If the player has no current-year games yet, API's career_totals IS the
    end-of-last-year snapshot, so fall back to that.

    Only compares stats present in BOTH sides. Returns list of diffs.
    """
    def _api_baseline(ar):
        bl = ar.get('career_totals_baseline') or {}
        if bl.get('batting') or bl.get('pitching'):
            return bl
        return ar.get('career_totals', {})

    bref_bl = bref_entry.get('career_totals_baseline') or bref_entry.get('career_totals', {})
    api_bl = _api_baseline(api_result)

    diffs = []
    for group in ('batting', 'pitching'):
        b = (bref_bl or {}).get(group, {}) or {}
        a = (api_bl or {}).get(group, {}) or {}
        shared = set(b.keys()) & set(a.keys())
        for stat in sorted(shared):
            bv, av = b[stat], a[stat]
            if stat == 'IP':
                if abs((bv or 0) - (av or 0)) > ip_tolerance:
                    diffs.append({'group': group, 'stat': stat, 'bref': bv, 'api': av})
            else:
                if bv != av:
                    diffs.append({'group': group, 'stat': stat, 'bref': bv, 'api': av})
    return diffs


def _merge_api_into_existing(existing: dict, api_result: dict) -> None:
    """Merge an API result into an existing BREF-era cache entry in place.

    Firsts: additive (don't overwrite). Milestones / totals / baseline / year: replaced.
    """
    for first_type in ('batting_firsts', 'pitching_firsts'):
        for stat, data in api_result.get(first_type, {}).items():
            if stat not in existing.get(first_type, {}):
                existing.setdefault(first_type, {})[stat] = data
    for ms_type in ('batting_milestones', 'pitching_milestones'):
        for stat, ms_list in api_result.get(ms_type, {}).items():
            existing.setdefault(ms_type, {})[stat] = ms_list
    existing['career_totals'] = api_result['career_totals']
    existing['career_totals_baseline'] = api_result.get('career_totals_baseline', {})
    existing['last_full_year'] = api_result.get('last_full_year')
    existing['scraped_at'] = api_result['scraped_at']


def run_api_backfill(limit: Optional[int] = None, verbose: bool = True,
                     workers: int = 8, checkpoint_every: int = 50,
                     force_all: bool = False) -> None:
    """Backfill career_firsts cache using MLB API for stale (BREF-era) entries.

    Only merges an entry when the API baseline exactly matches the existing
    BREF baseline (shared stats only). Mismatches are appended to
    cache/career_firsts/api_vs_bref_review.json for manual review, and the
    existing BREF data is left untouched. Players with no Chadwick mapping
    go to unmapped_bref_ids.json.

    Resumable: re-running skips entries already on the 2026-04 API path.
    """
    import threading
    from concurrent.futures import ThreadPoolExecutor, as_completed
    import requests

    cf_dir = get_project_root() / 'cache' / 'career_firsts'
    cache_path = cf_dir / 'career_firsts.json'
    review_path = cf_dir / 'api_vs_bref_review.json'
    unmapped_path = cf_dir / 'unmapped_bref_ids.json'

    if not cache_path.exists():
        print("❌ Cache not found; nothing to backfill.")
        return

    with open(cache_path, 'r') as f:
        cache = json.load(f)

    # Target = anything not already scraped via the API path in 2026.
    # force_all=True → re-process every player (use after parser or filter fixes).
    if force_all:
        target_pids = list(cache.keys())
    else:
        target_pids = [
            pid for pid, d in cache.items()
            if not (d.get('scraped_at', '') or '').startswith('2026')
        ]
    if not target_pids:
        print("✅ All entries already on API path.")
        return
    if limit:
        target_pids = target_pids[:limit]

    if verbose:
        print(f"Building Chadwick bref → mlbam map...")
    bref_to_mlb = _build_bref_to_mlb_map()
    if verbose:
        print(f"  Loaded {len(bref_to_mlb):,} mappings")

    # Load prior review/unmapped lists and dedupe by pid on rerun
    def _load_list(p):
        if p.exists():
            try:
                with open(p, 'r') as f:
                    return json.load(f)
            except (json.JSONDecodeError, IOError):
                return []
        return []

    review = [r for r in _load_list(review_path) if r.get('player_id') not in set(target_pids)]
    unmapped = [u for u in _load_list(unmapped_path) if u.get('player_id') not in set(target_pids)]

    # Per-thread session (requests.Session isn't thread-safe)
    _tl = threading.local()
    def _session_for_thread():
        s = getattr(_tl, 'session', None)
        if s is None:
            s = requests.Session()
            s.headers.update({'User-Agent': 'mlb_processor/1.0'})
            _tl.session = s
        return s

    def _worker(pid):
        mlb_id = bref_to_mlb.get(pid)
        if not mlb_id:
            # Fallback: try MLB API name search from the BREF ID
            mlb_id = _search_mlb_api_by_bref_id(_session_for_thread(), pid)
            if not mlb_id:
                return (pid, None, 'unmapped')
        try:
            api_result = find_career_firsts_mlb_api(
                mlb_id, pid, verbose=False, session=_session_for_thread()
            )
            return (pid, api_result, 'ok')
        except Exception as e:
            return (pid, None, f'error: {e}')

    merged = 0
    flagged = 0
    errored = 0
    unmapped_count = 0
    processed = 0

    def _save_checkpoint():
        with open(cache_path, 'w') as f:
            json.dump(cache, f, ensure_ascii=False)
        with open(review_path, 'w') as f:
            json.dump(review, f, indent=2)
        with open(unmapped_path, 'w') as f:
            json.dump(unmapped, f, indent=2)

    if verbose:
        print(f"Processing {len(target_pids):,} players across {workers} workers...")

    with ThreadPoolExecutor(max_workers=workers) as ex:
        futures = {ex.submit(_worker, pid): pid for pid in target_pids}
        for fut in as_completed(futures):
            pid, api_result, status = fut.result()
            processed += 1
            existing = cache.get(pid, {})

            if status == 'unmapped':
                unmapped.append({'player_id': pid})
                unmapped_count += 1
                if verbose:
                    print(f"[{processed}/{len(target_pids)}] {pid}: no MLB ID")
            elif status.startswith('error'):
                errored += 1
                if verbose:
                    print(f"[{processed}/{len(target_pids)}] {pid}: {status}")
            else:
                # force_all: trust filtered API as authoritative, always merge.
                # Still record any baseline mismatches in review for reference.
                diffs = _compare_baseline(existing, api_result)
                if diffs and not force_all:
                    flagged += 1
                    review.append({
                        'player_id': pid,
                        'mlb_id': bref_to_mlb.get(pid),
                        'bref_scraped_at': existing.get('scraped_at'),
                        'api_scraped_at': api_result.get('scraped_at'),
                        'diffs': diffs,
                    })
                    if verbose:
                        summary = ', '.join(
                            f"{d['group']}.{d['stat']}={d['bref']}→{d['api']}"
                            for d in diffs[:4]
                        )
                        print(f"[{processed}/{len(target_pids)}] {pid}: ⚠️ MISMATCH — {summary}")
                else:
                    if diffs and force_all:
                        # Log the overwrite for posterity
                        review.append({
                            'player_id': pid,
                            'mlb_id': bref_to_mlb.get(pid),
                            'bref_scraped_at': existing.get('scraped_at'),
                            'api_scraped_at': api_result.get('scraped_at'),
                            'diffs': diffs,
                            'action': 'overwritten_force_all',
                        })
                    if force_all:
                        # Full replacement — additive merge would preserve stale
                        # game_ids in firsts (which never get re-checked otherwise)
                        api_result['player_id'] = pid
                        cache[pid] = api_result
                    else:
                        _merge_api_into_existing(existing, api_result)
                        cache[pid] = existing
                    merged += 1
                    if verbose and processed % 25 == 0:
                        print(f"[{processed}/{len(target_pids)}] {pid}: ✅ matched & merged")

            if processed % checkpoint_every == 0:
                _save_checkpoint()
                if verbose:
                    print(f"  💾 Checkpoint — merged={merged} flagged={flagged} "
                          f"unmapped={unmapped_count} errored={errored}")

    _save_checkpoint()
    print(f"\n✅ Backfill complete")
    print(f"   Merged: {merged}")
    print(f"   Flagged for review: {flagged} → {review_path}")
    print(f"   Unmapped: {unmapped_count} → {unmapped_path}")
    print(f"   Errored: {errored}")


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


def find_witnessed_lasts(career_firsts_cache: dict, attended_games: dict) -> list[dict]:
    """Find career-LAST stat events that were witnessed at attended games.

    Mirror of find_witnessed_firsts for the other end of careers. Only
    retired players have populated lasts (active players' "last hit" is
    just their most recent and would shift, so we don't emit it).
    """
    witnessed = []

    for player_id, data in career_firsts_cache.items():
        player_name = data.get('player_name', player_id)
        if not data.get('is_retired'):
            continue

        for last_type, type_label in (('batting_lasts', 'batting'), ('pitching_lasts', 'pitching')):
            for stat, last_info in (data.get(last_type) or {}).items():
                game_id = last_info.get('game_id', '')
                if not game_id:
                    continue
                game = attended_games.get(game_id)
                if not game:
                    continue
                witnessed.append({
                    'player_id': player_id,
                    'player_name': player_name,
                    'milestone': last_info.get('milestone', ''),
                    'stat': stat,
                    'date': last_info.get('date', ''),
                    'game_id': game_id,
                    'opponent': last_info.get('opponent', ''),
                    'venue': game.get('venue', ''),
                    'year': last_info.get('year'),
                    'value': last_info.get('value_in_game'),
                    'type': type_label,
                    'category': 'last',
                })

    return witnessed


def _incremental_update(player_id, existing, scraper, years, verbose=False):
    """Update career data by only scraping specific years.

    Args:
        player_id: BREF player ID
        existing: Existing cached career data (modified in place)
        scraper: HTTP scraper
        years: List of years to scrape
        verbose: Print details

    Modifies `existing` in place with updated totals and any new milestones.
    """
    # Choose starting totals to avoid double-counting
    baseline = existing.get('career_totals_baseline', {})
    last_full_year = existing.get('last_full_year', 0)
    first_scrape_year = years[0] if years else 0

    if baseline and last_full_year and last_full_year >= first_scrape_year - 1:
        # Baseline covers through year before our scrape range — use it
        bat_ct = baseline.get('batting', {})
        pit_ct = baseline.get('pitching', {})
    else:
        # No baseline — career_totals doesn't include any of the years we're scraping
        # (caller verified this before calling us)
        ct = existing.get('career_totals', {})
        bat_ct = ct.get('batting', ct) if isinstance(ct.get('batting'), dict) else ct
        pit_ct = ct.get('pitching', ct) if isinstance(ct.get('pitching'), dict) else ct

    batting_totals = {stat: (bat_ct.get(stat) or 0) for stat in BATTING_MILESTONES.keys()}
    pitching_totals = {stat: (pit_ct.get(stat) or 0) for stat in PITCHING_MILESTONES.keys()}

    # Track already-reached milestones so we don't duplicate
    batting_milestones_reached = {stat: set() for stat in BATTING_MILESTONES.keys()}
    for stat, milestones in existing.get('batting_milestones', {}).items():
        for m in milestones:
            batting_milestones_reached.setdefault(stat, set()).add(m.get('number', 0))
    pitching_milestones_reached = {stat: set() for stat in PITCHING_MILESTONES.keys()}
    for stat, milestones in existing.get('pitching_milestones', {}).items():
        for m in milestones:
            pitching_milestones_reached.setdefault(stat, set()).add(m.get('number', 0))

    new_milestones = 0

    for year in years:
        # Scrape batting for this year
        time.sleep(3.05)
        games = scrape_batting_game_log(player_id, year, scraper)

        for game in games:
            batting_totals['G'] = batting_totals.get('G', 0) + 1
            for stat in BATTING_MILESTONES.keys():
                game_value = 1 if stat == 'G' else game.get(stat, 0)
                if game_value > 0:
                    if stat != 'G':
                        old_total = batting_totals[stat]
                        batting_totals[stat] += game_value
                        new_total = batting_totals[stat]
                    else:
                        old_total = batting_totals['G'] - 1
                        new_total = batting_totals['G']
                    for threshold in BATTING_MILESTONES[stat]:
                        if old_total < threshold <= new_total and threshold not in batting_milestones_reached.get(stat, set()):
                            batting_milestones_reached.setdefault(stat, set()).add(threshold)
                            stat_name = STAT_NAMES.get(stat, stat)
                            existing.setdefault('batting_milestones', {}).setdefault(stat, []).append({
                                'number': threshold,
                                'date': game.get('date_full', game.get('date', '')),
                                'game_id': game.get('game_id', ''),
                                'opponent': game.get('opponent', ''),
                                'year': year,
                                'milestone': f"Career {stat_name} #{threshold}",
                            })
                            new_milestones += 1
                            if verbose:
                                print(f"    New milestone: Career {stat_name} #{threshold}")

        # Scrape pitching for this year
        time.sleep(3.05)
        pgames = scrape_pitching_game_log(player_id, year, scraper)
        for game in pgames:
            pitching_totals['G_P'] = pitching_totals.get('G_P', 0) + 1
            for stat in PITCHING_MILESTONES.keys():
                game_value = 1 if stat == 'G_P' else game.get(stat, 0)
                if game_value > 0:
                    if stat != 'G_P':
                        old_total = pitching_totals[stat]
                        pitching_totals[stat] += game_value
                        new_total = pitching_totals[stat]
                    else:
                        old_total = pitching_totals['G_P'] - 1
                        new_total = pitching_totals['G_P']
                    for threshold in PITCHING_MILESTONES[stat]:
                        if old_total < threshold <= new_total and threshold not in pitching_milestones_reached.get(stat, set()):
                            pitching_milestones_reached.setdefault(stat, set()).add(threshold)
                            stat_name = STAT_NAMES.get(stat, stat)
                            existing.setdefault('pitching_milestones', {}).setdefault(stat, []).append({
                                'number': threshold,
                                'date': game.get('date_full', game.get('date', '')),
                                'game_id': game.get('game_id', ''),
                                'opponent': game.get('opponent', ''),
                                'year': year,
                                'milestone': f"Career {stat_name} #{threshold}",
                            })
                            new_milestones += 1

    # Update career totals (same nested format as find_career_firsts)
    existing['career_totals'] = {
        'batting': {k: v for k, v in batting_totals.items() if v > 0},
        'pitching': {k: v for k, v in pitching_totals.items() if v > 0},
    }
    # Preserve baseline for future incremental updates
    # Baseline = totals at end of year before the first year we scraped
    if baseline:
        existing['career_totals_baseline'] = baseline
        existing['last_full_year'] = last_full_year
    if verbose and new_milestones:
        print(f"    {new_milestones} new milestone(s) found")


def scrape_career_firsts_for_players(
    player_ids: set[str],
    refresh: bool = False,
    delay: float = 3.05,
    verbose: bool = True,
    player_names: dict[str, str] = None,
    detail_verbose: bool = False
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

    current_year = datetime.now().year

    for i, player_id in enumerate(sorted(player_ids), 1):
        name = player_names.get(player_id, player_id)
        display_name = f"{name} ({player_id})" if name != player_id else player_id

        if not refresh and player_id in cache:
            if verbose:
                print(f"[{i}/{total}] {display_name}: cached, skipping")
            continue

        # Incremental update: if already cached, only scrape years we don't have
        existing = cache.get(player_id)
        if refresh and existing and existing.get('career_totals'):
            scraped_at = existing.get('scraped_at', '')
            scraped_year = int(scraped_at[:4]) if scraped_at and len(scraped_at) >= 4 else 0

            if existing.get('career_totals_baseline') and existing.get('last_full_year'):
                # Has baseline — use it (safe even if scraped in current year)
                start_year = existing['last_full_year'] + 1
            elif scraped_year > 0 and scraped_year < current_year:
                # No baseline but scraped in a prior year — career_totals is safe to use
                # Scrape from scraped_year (to catch rest of that season) through current year
                start_year = scraped_year
            else:
                # Scraped in current year with no baseline — can't safely do incremental
                start_year = 0

            if start_year > 0:
                years_to_scrape = list(range(start_year, current_year + 1))
                if verbose:
                    print(f"[{i}/{total}] {display_name}: incremental update ({start_year}-{current_year}, {len(years_to_scrape)} yr)...")
                try:
                    _incremental_update(player_id, existing, scraper, years_to_scrape, detail_verbose)
                    existing['scraped_at'] = datetime.now().isoformat()
                    cache[player_id] = existing
                    save_career_firsts_cache(cache)
                    consecutive_errors = 0
                    if i < total:
                        time.sleep(delay)
                    continue
                except Exception as e:
                    import traceback
                    if verbose:
                        print(f"    Incremental failed: {e}")
                        traceback.print_exc()
                        print(f"    Falling back to full scrape...")

        if verbose:
            reason = "not in cache" if not existing else "no career_totals" if not existing.get('career_totals') else "scraped this year, no baseline"
            print(f"[{i}/{total}] Scraping {display_name} (full — {reason})...")

        try:
            firsts = find_career_firsts(player_id, scraper, detail_verbose)
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

    parser.add_argument(
        '--api-backfill',
        action='store_true',
        dest='api_backfill',
        help="Backfill career firsts via MLB API for stale BREF-era entries. "
             "Only merges when API baseline matches existing BREF baseline; "
             "mismatches go to cache/career_firsts/api_vs_bref_review.json for review."
    )

    parser.add_argument(
        '--limit',
        type=int,
        default=None,
        help="Limit number of players processed (useful for testing --api-backfill)"
    )

    parser.add_argument(
        '--workers',
        type=int,
        default=8,
        help="Parallel workers for --api-backfill (default: 8)"
    )

    parser.add_argument(
        '--force-all',
        action='store_true',
        dest='force_all',
        help="With --api-backfill, re-process ALL players (not just stale) and "
             "unconditionally overwrite career_totals with filtered API values"
    )

    args = parser.parse_args()
    verbose = not args.quiet

    if args.api_backfill:
        run_api_backfill(limit=args.limit, verbose=verbose, workers=args.workers,
                         force_all=args.force_all)
        return

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
