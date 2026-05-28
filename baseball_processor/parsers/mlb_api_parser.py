"""
MLB.com API Parser
==================
Fetches box score data from MLB Stats API for games not available on Baseball Reference
(primarily spring training games).

Usage:
    from baseball_processor.parsers.mlb_api_parser import parse_mlb_game

    # From URL
    game_data = parse_mlb_game("https://www.mlb.com/gameday/red-sox-vs-orioles/2010/03/27/277494/final/box")

    # From game ID
    game_data = parse_mlb_game(277494)
"""

import re
import requests
import html
import unicodedata
from datetime import datetime
from typing import Optional, Union

from ..engines.milestone_engine import MilestoneEngine
from ..engines.special_events_engine import SpecialEventsEngine
from ..utils.http import create_retry_session, get_with_retry

_session = create_retry_session()

# Try to import cloudscraper for bypassing Cloudflare
try:
    import cloudscraper
    HAS_CLOUDSCRAPER = True
except ImportError:
    HAS_CLOUDSCRAPER = False

# Try to import baseball_id for player ID mapping
try:
    from baseball_id import Lookup
    HAS_BASEBALL_ID = True
except ImportError:
    HAS_BASEBALL_ID = False
    print("Warning: baseball_id not installed. Run 'pip install baseball_id' for BREF ID mapping.")


# Cache for MLB ID to BREF ID mapping
_mlb_to_bref_cache = {}

# Chadwick Register data (MLB ID -> BREF ID mapping)
_chadwick_mlb_to_bref = {}
_chadwick_loaded = False


def _normalized_person_name(person):
    """Return a normalized full name from a Stats API person object."""
    return re.sub(r"\s+", " ", str((person or {}).get('fullName', '') or '')).strip().lower()


def _person_id(person):
    """Return a Stats API person id as a string, or blank if absent."""
    person_id = (person or {}).get('id')
    return str(person_id) if person_id is not None else ''


def infer_abs_challenger_type(matchup, review_details):
    """Infer whether an ABS challenger was the batter, pitcher, or catcher."""
    review_details = review_details or {}
    explicit_type = str(
        review_details.get('challengerType')
        or review_details.get('challengingPlayerType')
        or review_details.get('challengePlayerType')
        or review_details.get('playerType')
        or ''
    ).strip().lower()
    if explicit_type in {'batter', 'pitcher', 'catcher'}:
        return explicit_type

    matchup = matchup or {}
    challenger = review_details.get('player', {}) or {}
    batter = matchup.get('batter', {}) or {}
    pitcher = matchup.get('pitcher', {}) or {}
    challenger_id = _person_id(challenger)
    if challenger_id and challenger_id == _person_id(batter):
        return 'batter'
    if challenger_id and challenger_id == _person_id(pitcher):
        return 'pitcher'

    challenger_name = _normalized_person_name(challenger)
    if challenger_name and challenger_name == _normalized_person_name(batter):
        return 'batter'
    if challenger_name and challenger_name == _normalized_person_name(pitcher):
        return 'pitcher'

    return 'catcher'


def _load_chadwick_register():
    """Load Chadwick Register data for MLB ID -> BREF ID mapping."""
    global _chadwick_mlb_to_bref, _chadwick_loaded
    if _chadwick_loaded:
        return

    import csv
    from pathlib import Path

    # Find register data directory
    register_dir = Path(__file__).parent.parent.parent / 'register-master' / 'data'
    if not register_dir.exists():
        _chadwick_loaded = True
        return

    # Load all people CSV files
    for csv_file in register_dir.glob('people-*.csv'):
        try:
            with open(csv_file, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    mlb_id = row.get('key_mlbam', '').strip()
                    bref_id = row.get('key_bbref', '').strip()
                    bref_minors = row.get('key_bbref_minors', '').strip()

                    if mlb_id:
                        try:
                            mlb_id_int = int(mlb_id)
                            # Prefer MLB BREF ID, fall back to minors
                            if bref_id:
                                _chadwick_mlb_to_bref[mlb_id_int] = bref_id
                            elif bref_minors:
                                _chadwick_mlb_to_bref[mlb_id_int] = bref_minors
                        except ValueError:
                            pass
        except (IOError, csv.Error):
            continue

    _chadwick_loaded = True


def get_bref_id_from_chadwick(mlb_id: int) -> Optional[str]:
    """Look up BREF ID from Chadwick Register by MLB ID."""
    _load_chadwick_register()
    return _chadwick_mlb_to_bref.get(mlb_id)

# Cache for name to BREF ID mapping (fallback for newer players)
# Key: (name, team) or just name; Value: bref_id
_name_team_to_bref_cache = {}  # (name, team) -> bref_id
_name_to_bref_cache = {}  # name -> bref_id (fallback if team doesn't match)
_name_cache_loaded = False


def _load_name_to_bref_cache():
    """Load name->bref_id mappings from existing cache files."""
    global _name_team_to_bref_cache, _name_to_bref_cache, _name_cache_loaded
    if _name_cache_loaded:
        return

    import json
    from pathlib import Path

    # Find cache directory
    cache_dir = Path(__file__).parent.parent.parent / 'cache'
    if not cache_dir.exists():
        _name_cache_loaded = True
        return

    # Scan all game cache files for player name -> bref_id mappings
    for cache_file in cache_dir.glob('*.json'):
        if 'career_firsts' in str(cache_file) or 'career_gamelogs' in str(cache_file):
            continue
        try:
            with open(cache_file, 'r') as f:
                game = json.load(f)

            basic_info = game.get('basic_info', {})
            away_team = basic_info.get('away_team_code', '')
            home_team = basic_info.get('home_team_code', '')

            # Extract from batting and pitching
            for side, team in [('away', away_team), ('home', home_team)]:
                for player in game.get('batting', {}).get(side, []):
                    name = player.get('name', '').lower().strip()
                    player_id = player.get('player_id', '')
                    # Only use BREF-style IDs (not mlb_ prefixed)
                    if name and player_id and not player_id.startswith('mlb_'):
                        _name_to_bref_cache[name] = player_id
                        if team:
                            _name_team_to_bref_cache[(name, team)] = player_id

                for player in game.get('pitching', {}).get(side, []):
                    name = player.get('name', '').lower().strip()
                    player_id = player.get('player_id', '')
                    if name and player_id and not player_id.startswith('mlb_'):
                        _name_to_bref_cache[name] = player_id
                        if team:
                            _name_team_to_bref_cache[(name, team)] = player_id
        except (json.JSONDecodeError, IOError, KeyError):
            continue

    _name_cache_loaded = True


# Cache for validated constructed IDs: (name, team, year) -> bref_id
_constructed_id_cache = {}
_validated_mlb_bref_id_cache = {}
_provisional_mlb_bref_id_cache = {}
_provisional_mlb_bref_ids = set()
_bref_player_page_cache = {}

# Cache for register ID -> MLB ID mappings (resolved via register page)
_register_to_mlb_cache = {}
_register_resolution_attempted = set()  # Track IDs we've already tried to resolve


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


def is_mlb_bref_id(player_id: str) -> bool:
    """Return True for regular MLB B-Ref player IDs such as troutmi01."""
    player_id = str(player_id or "").strip()
    return bool(player_id and not player_id.startswith("mlb_") and not is_register_format_id(player_id))


def _normalize_bref_lookup_name(name: str) -> str:
    normalized = unicodedata.normalize("NFKD", str(name or ""))
    normalized = normalized.encode("ASCII", "ignore").decode("utf-8")
    normalized = re.sub(r"\b(jr|sr|ii|iii|iv|v)\.?\b", "", normalized, flags=re.IGNORECASE)
    normalized = re.sub(r"[^a-zA-Z]+", " ", normalized)
    return re.sub(r"\s+", " ", normalized).strip().lower()


def _bref_name_parts(name: str) -> tuple[str, str]:
    normalized = _normalize_bref_lookup_name(name)
    parts = normalized.split()
    if len(parts) < 2:
        return "", ""
    first_name = parts[0]
    last_name = "".join(parts[1:])
    return first_name, last_name


def construct_bref_mlb_id_candidates(name: str, max_suffix: int = 20) -> list[str]:
    """Generate regular MLB B-Ref ID candidates for a player name."""
    first_name, last_name = _bref_name_parts(name)
    if len(first_name) < 2 or len(last_name) < 2:
        return []
    stem = f"{last_name[:5]}{first_name[:2]}"
    return [f"{stem}{suffix:02d}" for suffix in range(1, max_suffix + 1)]


def _used_mlb_bref_suffixes_for_stem(stem: str) -> set[int]:
    suffixes = set()
    _load_chadwick_register()
    known_ids = set(_chadwick_mlb_to_bref.values())
    known_ids.update(str(v) for v in _name_to_bref_cache.values())
    known_ids.update(str(v) for v in _name_team_to_bref_cache.values())
    known_ids.update(str(v) for v in _mlb_to_bref_cache.values())
    known_ids.update(str(v) for v in _validated_mlb_bref_id_cache.values())
    known_ids.update(str(v) for v in _provisional_mlb_bref_id_cache.values())

    for player_id in known_ids:
        if not is_mlb_bref_id(player_id) or not str(player_id).startswith(stem):
            continue
        suffix = str(player_id)[len(stem):]
        if len(suffix) == 2 and suffix.isdigit():
            suffixes.add(int(suffix))
    return suffixes


def _fetch_bref_player_page(candidate_id: str) -> tuple[Optional[int], str]:
    """Fetch and cache a B-Ref player page candidate."""
    if not candidate_id:
        return None, ""
    if candidate_id in _bref_player_page_cache:
        return _bref_player_page_cache[candidate_id]

    try:
        url = f"https://www.baseball-reference.com/players/{candidate_id[0]}/{candidate_id}.shtml"
        if HAS_CLOUDSCRAPER:
            scraper = cloudscraper.create_scraper()
            response = scraper.get(url, timeout=15)
        else:
            headers = {
                "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36",
                "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            }
            response = get_with_retry(_session, url, headers=headers, timeout=15)
        response.encoding = "utf-8"
        result = (response.status_code, response.text if response.status_code == 200 else "")
        _bref_player_page_cache[candidate_id] = result
        return result
    except Exception:
        return None, ""


def construct_provisional_bref_mlb_id(name: str, max_suffix: int = 99) -> Optional[str]:
    """Construct the likely MLB B-Ref ID before its page is published."""
    lookup_name = _normalize_bref_lookup_name(name)
    if not lookup_name:
        return None
    if lookup_name in _provisional_mlb_bref_id_cache:
        return _provisional_mlb_bref_id_cache[lookup_name]

    candidates = construct_bref_mlb_id_candidates(name, max_suffix=max_suffix)
    if not candidates:
        return None

    for candidate in candidates:
        status_code, _html = _fetch_bref_player_page(candidate)
        if status_code == 404:
            _provisional_mlb_bref_id_cache[lookup_name] = candidate
            _provisional_mlb_bref_ids.add(candidate)
            return candidate
        if status_code == 200:
            continue
        break

    stem = candidates[0][:-2]
    used_suffixes = _used_mlb_bref_suffixes_for_stem(stem)
    for candidate in candidates:
        suffix = int(candidate[-2:])
        if suffix not in used_suffixes:
            _provisional_mlb_bref_id_cache[lookup_name] = candidate
            _provisional_mlb_bref_ids.add(candidate)
            return candidate
    candidate = candidates[0]
    _provisional_mlb_bref_id_cache[lookup_name] = candidate
    _provisional_mlb_bref_ids.add(candidate)
    return candidate


def _bref_candidate_matches_name(candidate_id: str, expected_name: str) -> bool:
    """Fetch a candidate B-Ref page and confirm its H1 matches the player name."""
    try:
        status_code, page_html = _fetch_bref_player_page(candidate_id)
        if status_code != 200:
            return False
        match = re.search(r"<h1[^>]*>(.*?)</h1>", page_html, re.IGNORECASE | re.DOTALL)
        if not match:
            return False
        page_name = re.sub(r"<[^>]+>", " ", match.group(1))
        page_name = html.unescape(page_name)
        return _normalize_bref_lookup_name(page_name) == _normalize_bref_lookup_name(expected_name)
    except Exception:
        return False


def resolve_bref_mlb_id_by_name(name: str, max_suffix: int = 20) -> Optional[str]:
    """Resolve a regular MLB B-Ref ID by generating and validating candidates."""
    lookup_name = _normalize_bref_lookup_name(name)
    if not lookup_name:
        return None
    if lookup_name in _validated_mlb_bref_id_cache:
        return _validated_mlb_bref_id_cache[lookup_name]

    for candidate_id in construct_bref_mlb_id_candidates(name, max_suffix=max_suffix):
        if _bref_candidate_matches_name(candidate_id, name):
            _validated_mlb_bref_id_cache[lookup_name] = candidate_id
            return candidate_id

    _validated_mlb_bref_id_cache[lookup_name] = None
    return None


def resolve_register_id(register_id: str, use_cache_only: bool = False) -> Optional[str]:
    """
    Resolve a register-format ID to MLB-format ID.

    Args:
        register_id: Register-format BREF ID (e.g., "workma000gag")
        use_cache_only: If True, only check cache, don't make HTTP requests

    Returns:
        MLB-format ID if found, None otherwise
    """
    # Check cache first
    if register_id in _register_to_mlb_cache:
        return _register_to_mlb_cache[register_id]

    if use_cache_only:
        return None

    # Don't retry failed resolutions
    if register_id in _register_resolution_attempted:
        return None

    _register_resolution_attempted.add(register_id)

    # Try to fetch from register page (use cloudscraper to bypass Cloudflare)
    try:
        url = f"https://www.baseball-reference.com/register/player.fcgi?id={register_id}"

        if HAS_CLOUDSCRAPER:
            scraper = cloudscraper.create_scraper()
            response = scraper.get(url, timeout=15)
        else:
            headers = {
                "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36",
                "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            }
            response = get_with_retry(_session, url, headers=headers, timeout=15)

        if response.status_code != 200:
            return None

        # Look for game log links which use MLB-format ID
        # Pattern: /players/gl.fcgi?id=XXXXXX&t=b&year=YYYY
        match = re.search(r'/players/gl\.fcgi\?id=([a-z]+\d{2})(?:&|&amp;)', response.text)
        if match:
            mlb_id = match.group(1)
            _register_to_mlb_cache[register_id] = mlb_id
            return mlb_id

    except Exception as e:
        # Silently fail - we'll just use the register ID
        pass

    return None


def resolve_player_ids_in_game(game_data: dict, verbose: bool = False) -> dict:
    """
    Resolve any register-format player IDs in a parsed game to MLB-format IDs.

    This updates the game data in place and returns it.
    """
    resolved_count = 0

    # Collect all register-format IDs first
    register_ids = set()

    for side in ['away', 'home']:
        for player in game_data.get('batting', {}).get(side, []):
            pid = player.get('player_id', '')
            if is_register_format_id(pid):
                register_ids.add(pid)

        for player in game_data.get('pitching', {}).get(side, []):
            pid = player.get('player_id', '')
            if is_register_format_id(pid):
                register_ids.add(pid)

    if not register_ids:
        return game_data

    if verbose:
        print(f"  Resolving {len(register_ids)} register-format player IDs...")

    # Resolve each register ID
    id_map = {}
    for reg_id in register_ids:
        mlb_id = resolve_register_id(reg_id)
        if mlb_id:
            id_map[reg_id] = mlb_id
            resolved_count += 1

    if verbose and resolved_count > 0:
        print(f"  Resolved {resolved_count}/{len(register_ids)} IDs to MLB format")

    # Update all player IDs in the game data
    if id_map:
        for side in ['away', 'home']:
            for player in game_data.get('batting', {}).get(side, []):
                old_id = player.get('player_id', '')
                if old_id in id_map:
                    player['player_id'] = id_map[old_id]
                    player['bref_id'] = id_map[old_id]
                    player['register_id'] = old_id  # Keep original for reference

            for player in game_data.get('pitching', {}).get(side, []):
                old_id = player.get('player_id', '')
                if old_id in id_map:
                    player['player_id'] = id_map[old_id]
                    player['bref_id'] = id_map[old_id]
                    player['register_id'] = old_id

        # Also update play-by-play and substitutions
        for play in game_data.get('play_by_play', []):
            if play.get('batter_id') in id_map:
                play['batter_id'] = id_map[play['batter_id']]
            if play.get('pitcher_id') in id_map:
                play['pitcher_id'] = id_map[play['pitcher_id']]

        for sub in game_data.get('substitutions', []):
            if sub.get('player_id') in id_map:
                sub['player_id'] = id_map[sub['player_id']]

    return game_data


def construct_bref_register_id(name: str, team: str = None, year: int = None, mlb_id: int = None) -> Optional[str]:
    """
    Construct a Baseball Reference register ID (minor league format) from a player name.

    Format: {last_name[:6]}{number:03d}{first_name[:3]}
    Example: "Wyatt Lunsford-Shenkman" -> "lunsfo000wya"

    Args:
        name: Player's full name
        team: Team code (for caching/validation)
        year: Game year (for caching/validation)
        mlb_id: MLB player ID (for additional validation)

    Note: This assumes the player is the first with this name pattern (000).
    Returns constructed ID only for players we haven't seen in MLB regular season.
    """
    if not name or ' ' not in name:
        return None

    # Check if we've already constructed an ID for this player+team+year combo
    cache_key = (name.lower().strip(), team, year)
    if cache_key in _constructed_id_cache:
        return _constructed_id_cache[cache_key]

    parts = name.strip().split()
    if len(parts) < 2:
        return None

    first_name = parts[0].lower()
    # Last name is everything after first name, handle hyphenated names
    last_name = ''.join(parts[1:]).lower()
    # Remove hyphens and other non-alpha characters for the ID
    last_name_clean = ''.join(c for c in last_name if c.isalpha())
    first_name_clean = ''.join(c for c in first_name if c.isalpha())

    if len(last_name_clean) < 3 or len(first_name_clean) < 2:
        return None

    # Construct ID: first 6 of last name + 000 + first 3 of first name
    bref_id = f"{last_name_clean[:6]}000{first_name_clean[:3]}"

    # Cache this construction with team/year context
    _constructed_id_cache[cache_key] = bref_id

    return bref_id


def get_bref_id_by_name(name: str, team: str = None, year: int = None, mlb_id: int = None) -> Optional[str]:
    """
    Get BREF ID by player name, with multiple fallback strategies.

    Args:
        name: Player's full name
        team: Team code for disambiguation
        year: Game year for context
        mlb_id: MLB player ID for caching

    Returns:
        BREF ID if found/constructed, None otherwise
    """
    _load_name_to_bref_cache()
    name_lower = name.lower().strip()

    fallback_id = None

    # Try name+team first for better accuracy
    if team:
        result = _name_team_to_bref_cache.get((name_lower, team))
        if result:
            if is_mlb_bref_id(result):
                return result
            fallback_id = result

    # Fall back to name-only from cache
    result = _name_to_bref_cache.get(name_lower)
    if result:
        if is_mlb_bref_id(result):
            return result
        fallback_id = fallback_id or result

    # Try the regular MLB B-Ref ID shape before falling back to register IDs.
    bref_id = resolve_bref_mlb_id_by_name(name)
    if bref_id:
        if mlb_id:
            _mlb_to_bref_cache[mlb_id] = bref_id
        return bref_id

    provisional_id = construct_provisional_bref_mlb_id(name)
    if provisional_id:
        return provisional_id

    if fallback_id:
        return fallback_id

    # Last resort: construct minor league register ID format
    # Only do this for players not found in regular season cache
    return construct_bref_register_id(name, team=team, year=year, mlb_id=mlb_id)


def get_bref_id(mlb_id: int, name: str = None) -> Optional[str]:
    """
    Map an MLB player ID to a Baseball-Reference ID.

    Lookup order:
    1. Local cache
    2. Chadwick Register (authoritative MLB ID -> BREF ID mapping)
    3. baseball_id package
    4. Name-based fallback

    Args:
        mlb_id: MLB player ID
        name: Player name (for fallback lookup)

    Returns None if mapping not found.
    """
    # Check MLB ID cache first
    if mlb_id in _mlb_to_bref_cache:
        cached = _mlb_to_bref_cache[mlb_id]
        if cached and is_mlb_bref_id(cached):
            return cached

    # Try Chadwick Register (most authoritative source)
    bref_id = get_bref_id_from_chadwick(mlb_id)
    if bref_id:
        _mlb_to_bref_cache[mlb_id] = bref_id
        return bref_id

    # Try baseball_id package
    if HAS_BASEBALL_ID:
        try:
            result = Lookup.from_mlb_ids([mlb_id])
            if not result.empty and 'bref_id' in result.columns:
                bref_id = result.iloc[0]['bref_id']
                if bref_id and not (isinstance(bref_id, float) and str(bref_id) == 'nan'):
                    _mlb_to_bref_cache[mlb_id] = bref_id
                    return bref_id
        except Exception:
            pass

    # Fallback: try name-based lookup from existing cache
    if name:
        bref_id = get_bref_id_by_name(name)
        if bref_id:
            if bref_id not in _provisional_mlb_bref_ids:
                _mlb_to_bref_cache[mlb_id] = bref_id
            return bref_id

    _mlb_to_bref_cache[mlb_id] = None
    return None


def batch_get_bref_ids(mlb_ids: list) -> dict:
    """
    Batch map MLB player IDs to BREF IDs.
    More efficient than individual lookups.

    Returns dict of {mlb_id: bref_id} (bref_id may be None if not found)
    """
    if not HAS_BASEBALL_ID:
        return {mid: None for mid in mlb_ids}

    # Check cache first
    result = {}
    uncached = []
    for mid in mlb_ids:
        if mid in _mlb_to_bref_cache:
            result[mid] = _mlb_to_bref_cache[mid]
        else:
            uncached.append(mid)

    # Batch lookup uncached IDs
    if uncached:
        try:
            lookup_result = Lookup.from_mlb_ids(uncached)
            for _, row in lookup_result.iterrows():
                mlb_id = int(row.get('mlb_id', 0))
                bref_id = row.get('bref_id')
                if bref_id and not (isinstance(bref_id, float) and str(bref_id) == 'nan'):
                    _mlb_to_bref_cache[mlb_id] = bref_id
                    result[mlb_id] = bref_id
                else:
                    _mlb_to_bref_cache[mlb_id] = None
                    result[mlb_id] = None
        except Exception:
            for mid in uncached:
                result[mid] = None

    return result


# MLB Stats API base URL
MLB_API_BASE = "https://statsapi.mlb.com/api/v1.1"

# Game type mapping
GAME_TYPE_MAP = {
    'S': 'spring',
    'R': 'regular',
    'P': 'postseason',
    'F': 'postseason',  # Wild Card, Division, League Championship, World Series
    'D': 'postseason',
    'L': 'postseason',
    'W': 'postseason',
    'A': 'allstar',
    'E': 'spring',  # Group exhibition games with spring training
}

# Team code mapping (MLB team IDs to standard abbreviations)
TEAM_ID_TO_CODE = {
    108: 'LAA', 109: 'ARI', 110: 'BAL', 111: 'BOS', 112: 'CHC',
    113: 'CIN', 114: 'CLE', 115: 'COL', 116: 'DET', 117: 'HOU',
    118: 'KC', 119: 'LAD', 120: 'WSH', 121: 'NYM', 133: 'ATH',
    134: 'PIT', 135: 'SD', 136: 'SEA', 137: 'SF', 138: 'STL',
    139: 'TB', 140: 'TEX', 141: 'TOR', 142: 'MIN', 143: 'PHI',
    144: 'ATL', 145: 'CWS', 146: 'MIA', 147: 'NYY', 158: 'MIL',
}


def extract_game_id(url_or_id: Union[str, int]) -> int:
    """Extract game ID from MLB.com URL or return ID directly."""
    if isinstance(url_or_id, int):
        return url_or_id

    # Try to extract from URL patterns
    # https://www.mlb.com/gameday/red-sox-vs-orioles/2010/03/27/277494/final/box
    # https://www.mlb.com/gameday/277494
    match = re.search(r'/(\d{5,7})(?:/|$)', str(url_or_id))
    if match:
        return int(match.group(1))

    # Maybe it's just a number as string
    try:
        return int(url_or_id)
    except ValueError:
        raise ValueError(f"Could not extract game ID from: {url_or_id}")


def fetch_game_data(game_pk: int) -> dict:
    """Fetch game data from MLB Stats API."""
    # Get live feed for game metadata
    feed_url = f"{MLB_API_BASE}/game/{game_pk}/feed/live"
    feed_response = get_with_retry(_session, feed_url, timeout=30)
    feed_response.raise_for_status()
    feed_data = feed_response.json()

    # Get boxscore for detailed stats
    box_url = f"https://statsapi.mlb.com/api/v1/game/{game_pk}/boxscore"
    box_response = get_with_retry(_session, box_url, timeout=30)
    box_response.raise_for_status()
    box_data = box_response.json()

    return {
        'feed': feed_data,
        'boxscore': box_data,
    }


def parse_basic_info(feed_data: dict, box_data: dict) -> dict:
    """Parse basic game information."""
    game_data = feed_data.get('gameData', {})

    # Date/time info
    dt = game_data.get('datetime', {})
    official_date = dt.get('officialDate', '')

    # Parse date for formatted display
    try:
        date_obj = datetime.strptime(official_date, '%Y-%m-%d')
        formatted_date = date_obj.strftime('%A, %B %d, %Y')  # "Saturday, March 27, 2010"
        date_yyyymmdd = date_obj.strftime('%Y%m%d')
    except Exception:
        formatted_date = official_date
        date_yyyymmdd = official_date.replace('-', '')

    # Teams
    teams = game_data.get('teams', {})
    away_team = teams.get('away', {})
    home_team = teams.get('home', {})

    # Get team codes
    away_id = away_team.get('id')
    home_id = home_team.get('id')
    away_code = TEAM_ID_TO_CODE.get(away_id, away_team.get('abbreviation', 'UNK'))
    home_code = TEAM_ID_TO_CODE.get(home_id, home_team.get('abbreviation', 'UNK'))

    # Venue
    venue = game_data.get('venue', {})
    venue_name = venue.get('name', '')
    venue_location = venue.get('location', {})
    venue_city = venue_location.get('city', '')
    venue_state = venue_location.get('stateAbbrev', '')

    # Score from linescore
    linescore = feed_data.get('liveData', {}).get('linescore', {})
    away_score = linescore.get('teams', {}).get('away', {}).get('runs', 0)
    home_score = linescore.get('teams', {}).get('home', {}).get('runs', 0)

    # Game type
    game_info = game_data.get('game', {})
    game_type_code = game_info.get('type', 'R')
    game_type = GAME_TYPE_MAP.get(game_type_code, 'regular')

    # Weather (may not be available for spring training)
    weather = game_data.get('weather', {})
    weather_str = ''
    if weather:
        temp = weather.get('temp', '')
        condition = weather.get('condition', '')
        wind = weather.get('wind', '')
        if temp:
            weather_str = f"{temp}°F"
            if condition:
                weather_str += f", {condition}"
            if wind:
                weather_str += f", Wind: {wind}"

    # Attendance and duration
    game_info_data = game_data.get('gameInfo', {})
    attendance = game_info_data.get('attendance')
    duration_minutes = game_info_data.get('gameDurationMinutes')
    duration_str = ''
    if duration_minutes:
        duration_str = f"{duration_minutes // 60}:{duration_minutes % 60:02d}"

    # Venue coordinates
    coords = venue_location.get('defaultCoordinates', {})

    return {
        'away_team': away_team.get('name', ''),
        'home_team': home_team.get('name', ''),
        'date': formatted_date,
        'date_yyyymmdd': date_yyyymmdd,
        'start_time': dt.get('time', '') + ' ' + dt.get('ampm', ''),
        'attendance': f"{attendance:,}" if attendance else '',
        'attendance_value': attendance or 0,
        'venue': venue_name,
        'venue_city': venue_city,
        'venue_state': venue_state,
        'venue_latitude': coords.get('latitude'),
        'venue_longitude': coords.get('longitude'),
        'duration': duration_str,
        'weather': weather_str,
        'temperature_f': int(weather.get('temp', 0)) if weather.get('temp') else None,
        'away_score': str(away_score),
        'home_score': str(home_score),
        'away_score_value': away_score,
        'home_score_value': home_score,
        'doubleheader': '0' if game_info.get('doubleHeader', 'N') == 'N' else game_info.get('doubleHeader', '0'),
        'game_number': game_info.get('gameNumber', 1),
        'away_team_code': away_code,
        'home_team_code': home_code,
        'game_type': game_type,
        'game_type_code': game_type_code,
        'source': 'mlb',
    }


def _has_game_batting_activity(stats: dict) -> bool:
    """Return True for players who contributed as batters or baserunners."""
    for key in (
        'plateAppearances', 'atBats', 'runs', 'hits', 'rbi', 'baseOnBalls',
        'strikeOuts', 'stolenBases', 'caughtStealing', 'hitByPitch',
        'sacFlies', 'sacBunts', 'doubles', 'triples', 'homeRuns',
        'groundIntoDoublePlay',
    ):
        try:
            if int(stats.get(key, 0) or 0) > 0:
                return True
        except (TypeError, ValueError):
            continue
    return False


def parse_batting(box_data: dict, side: str, bref_id_map: dict = None, game_year: int = None) -> list:
    """Parse batting stats for a team."""
    team_data = box_data.get('teams', {}).get(side, {})
    players = team_data.get('players', {})
    batters = team_data.get('batters', [])
    batting_order = team_data.get('battingOrder', [])

    # Get team code for name disambiguation
    team_id = team_data.get('team', {}).get('id')
    team_code = TEAM_ID_TO_CODE.get(team_id, '')

    if bref_id_map is None:
        bref_id_map = {}

    result = []
    starter_slot = 0

    for batter_id in batters:
        player_key = f'ID{batter_id}'
        player = players.get(player_key, {})

        if not player:
            continue

        person = player.get('person', {})
        stats = player.get('stats', {}).get('batting', {})
        position = player.get('position', {})

        mlb_id = person.get('id')

        # Determine if starter using gameStatus (not battingOrder which is final order)
        game_status = player.get('gameStatus', {})
        is_starter = not game_status.get('isSubstitute', False) and starter_slot < 9
        if is_starter:
            starter_slot += 1
            lineup_slot = starter_slot
        else:
            lineup_slot = None

        # Use BREF ID if available, otherwise try name-based lookup, then fall back to mlb_ prefix
        player_name = person.get('fullName', '')
        bref_id = bref_id_map.get(mlb_id)
        if player_name and (not bref_id or not is_mlb_bref_id(bref_id)):
            name_bref_id = get_bref_id_by_name(player_name, team=team_code, year=game_year, mlb_id=mlb_id)
            if name_bref_id and (not bref_id or is_mlb_bref_id(name_bref_id)):
                bref_id = name_bref_id
        player_id = bref_id if bref_id else f"mlb_{mlb_id}"

        batter_data = {
            'name': player_name,
            'player_id': player_id,
            'mlb_id': mlb_id,
            'bref_id': bref_id,  # Store BREF ID separately too
            'jersey_number': player.get('jerseyNumber', ''),
            'position': position.get('abbreviation', ''),
            'AB': stats.get('atBats', 0),
            'R': stats.get('runs', 0),
            'H': stats.get('hits', 0),
            'RBI': stats.get('rbi', 0),
            'BB': stats.get('baseOnBalls', 0),
            'SO': stats.get('strikeOuts', 0),
            'PA': stats.get('plateAppearances', 0),
            'HR': stats.get('homeRuns', 0),
            '2B': stats.get('doubles', 0),
            '3B': stats.get('triples', 0),
            'SB': stats.get('stolenBases', 0),
            'CS': stats.get('caughtStealing', 0),
            'HBP': stats.get('hitByPitch', 0),
            'SF': stats.get('sacFlies', 0),
            'SH': stats.get('sacBunts', 0),
            'GDP': stats.get('groundIntoDoublePlay', 0),
            'TB': stats.get('totalBases', 0),
            'lineup_slot': lineup_slot if is_starter else None,
            'is_starter': is_starter,
        }

        # Include no-PA baserunners too; pinch runners can score/steal without
        # getting a plate appearance, and those stats drive milestone detection.
        if is_starter or _has_game_batting_activity(stats):
            result.append(batter_data)

    return result


def normalize_api_batting_rows(game_data: dict) -> dict:
    """Backfill no-PA baserunners into cached API batting rows.

    Older API caches were created before parse_batting kept pinch runners who
    scored or stole without a plate appearance. The play-by-play runner
    movements are enough to restore those rows for processing.
    """
    batting = game_data.setdefault('batting', {})
    basic = game_data.get('basic_info', {})
    side_by_code = {
        basic.get('away_team_code'): 'away',
        basic.get('home_team_code'): 'home',
    }
    existing_aliases = set()
    for side in ('away', 'home'):
        for player in batting.get(side, []) or []:
            for key in ('player_id', 'bref_id', 'register_id'):
                if player.get(key):
                    existing_aliases.add((side, str(player.get(key))))
            if player.get('mlb_id'):
                existing_aliases.add((side, f"mlb_{player.get('mlb_id')}"))
            if player.get('name'):
                existing_aliases.add((side, f"name:{str(player.get('name')).casefold()}"))
    runner_rows = {}

    for play in game_data.get('play_by_play', []) or []:
        side = side_by_code.get(play.get('batting_team'))
        if not side:
            half = str(play.get('half', '')).lower()
            side = 'away' if half == 'top' else 'home' if half == 'bottom' else ''
        if side not in ('away', 'home'):
            continue

        for runner in play.get('runners', []) or []:
            player_id = runner.get('player_id')
            name = runner.get('name', '')
            if not player_id:
                continue
            if (side, str(player_id)) in existing_aliases or (side, f"name:{str(name).casefold()}") in existing_aliases:
                continue

            key = (side, player_id)
            row = runner_rows.setdefault(key, {
                'name': name,
                'player_id': player_id,
                'position': 'PR',
                'AB': 0,
                'R': 0,
                'H': 0,
                'RBI': 0,
                'BB': 0,
                'SO': 0,
                'PA': 0,
                'HR': 0,
                '2B': 0,
                '3B': 0,
                'SB': 0,
                'CS': 0,
                'HBP': 0,
                'SF': 0,
                'SH': 0,
                'GDP': 0,
                'TB': 0,
                'lineup_slot': None,
                'is_starter': False,
            })
            event = str(runner.get('event', '')).lower()
            if 'stolen base' in event:
                row['SB'] += 1
            if 'caught stealing' in event:
                row['CS'] += 1
            if runner.get('end') == 'score' and not runner.get('is_out'):
                row['R'] += 1

    for (side, player_id), row in runner_rows.items():
        if row['R'] or row['SB'] or row['CS']:
            batting.setdefault(side, []).append(row)
            existing_aliases.add((side, str(player_id)))
            if row.get('name'):
                existing_aliases.add((side, f"name:{str(row.get('name')).casefold()}"))

    return game_data


def parse_pitching(box_data: dict, side: str, bref_id_map: dict = None, game_year: int = None) -> list:
    """Parse pitching stats for a team."""
    team_data = box_data.get('teams', {}).get(side, {})
    players = team_data.get('players', {})
    pitchers = team_data.get('pitchers', [])

    # Get team code for name disambiguation
    team_id = team_data.get('team', {}).get('id')
    team_code = TEAM_ID_TO_CODE.get(team_id, '')

    if bref_id_map is None:
        bref_id_map = {}

    result = []

    for pitcher_id in pitchers:
        player_key = f'ID{pitcher_id}'
        player = players.get(player_key, {})

        if not player:
            continue

        person = player.get('person', {})
        stats = player.get('stats', {}).get('pitching', {})

        if not stats:
            continue

        mlb_id = person.get('id')
        player_name = person.get('fullName', '')

        # Use BREF ID if available, otherwise try name-based lookup, then fall back to mlb_ prefix
        bref_id = bref_id_map.get(mlb_id)
        if player_name and (not bref_id or not is_mlb_bref_id(bref_id)):
            name_bref_id = get_bref_id_by_name(player_name, team=team_code, year=game_year, mlb_id=mlb_id)
            if name_bref_id and (not bref_id or is_mlb_bref_id(name_bref_id)):
                bref_id = name_bref_id
        player_id = bref_id if bref_id else f"mlb_{mlb_id}"

        pitcher_data = {
            'name': player_name,
            'player_id': player_id,
            'mlb_id': mlb_id,
            'bref_id': bref_id,
            'jersey_number': player.get('jerseyNumber', ''),
            'IP': stats.get('inningsPitched', '0'),
            'H': stats.get('hits', 0),
            'R': stats.get('runs', 0),
            'ER': stats.get('earnedRuns', 0),
            'BB': stats.get('baseOnBalls', 0),
            'SO': stats.get('strikeOuts', 0),
            'HR': stats.get('homeRuns', 0),
            'BF': stats.get('battersFaced', 0),
            'Pit': stats.get('pitchesThrown', 0) or stats.get('numberOfPitches', 0),
            'Str': stats.get('strikes', 0),
            'W': stats.get('wins', 0),
            'L': stats.get('losses', 0),
            'SV': stats.get('saves', 0),
            'HLD': stats.get('holds', 0),
            'BS': stats.get('blownSaves', 0),
            'HBP': stats.get('hitBatsmen', 0),
            'WP': stats.get('wildPitches', 0),
            'BK': stats.get('balks', 0),
            'GS': stats.get('gamesStarted', 0),
        }

        result.append(pitcher_data)

    return result


def parse_umpires(box_data: dict) -> dict:
    """Parse umpire assignments from boxscore officials."""
    type_map = {
        'Home Plate': 'HP', 'First Base': '1B', 'Second Base': '2B',
        'Third Base': '3B', 'Left Field': 'LF', 'Right Field': 'RF',
    }
    umpires = {}
    for official in box_data.get('officials', []):
        pos = type_map.get(official.get('officialType', ''))
        if pos:
            umpires[pos] = official.get('official', {}).get('fullName', '')
    return umpires


def parse_pitch_data(feed_data: dict, bref_id_map: dict = None) -> dict:
    """Extract per-pitcher pitch data from play-by-play events."""
    if bref_id_map is None:
        bref_id_map = {}

    pitcher_pitches = {}  # keyed by mlb_id
    all_plays = feed_data.get('liveData', {}).get('plays', {}).get('allPlays', [])

    for play in all_plays:
        matchup = play.get('matchup', {})
        pitcher_mlb_id = matchup.get('pitcher', {}).get('id')
        pitcher_name = matchup.get('pitcher', {}).get('fullName', '')
        batter_name = matchup.get('batter', {}).get('fullName', '')
        inning = play.get('about', {}).get('inning', 0)

        if not pitcher_mlb_id:
            continue

        if pitcher_mlb_id not in pitcher_pitches:
            pitcher_pitches[pitcher_mlb_id] = {
                'name': pitcher_name,
                'player_id': bref_id_map.get(pitcher_mlb_id, f'mlb_{pitcher_mlb_id}'),
                'pitches': [],
            }

        for event in play.get('playEvents', []):
            if not event.get('isPitch'):
                continue
            details = event.get('details', {})
            pitch_data = event.get('pitchData', {})
            pitch_type = details.get('type', {})
            breaks = pitch_data.get('breaks', {})

            pitcher_pitches[pitcher_mlb_id]['pitches'].append({
                'inning': inning,
                'batter': batter_name,
                'speed': pitch_data.get('startSpeed'),
                'type': pitch_type.get('code', '') if isinstance(pitch_type, dict) else '',
                'typeName': pitch_type.get('description', '') if isinstance(pitch_type, dict) else '',
                'spinRate': breaks.get('spinRate'),
                'call': details.get('description', ''),
            })

    # Build summaries
    result = {}
    for mlb_id, pdata in pitcher_pitches.items():
        pitches = pdata['pitches']
        speeds = [p['speed'] for p in pitches if p.get('speed')]
        spins = [p['spinRate'] for p in pitches if p.get('spinRate')]
        type_counts = {}
        type_names = {}
        for p in pitches:
            if p.get('type'):
                type_counts[p['type']] = type_counts.get(p['type'], 0) + 1
                type_names[p['type']] = p.get('typeName', p['type'])

        result[pdata['player_id']] = {
            'name': pdata['name'],
            'player_id': pdata['player_id'],
            'totalPitches': len(pitches),
            'avgSpeed': round(sum(speeds) / len(speeds), 1) if speeds else None,
            'maxSpeed': round(max(speeds), 1) if speeds else None,
            'minSpeed': round(min(speeds), 1) if speeds else None,
            'avgSpinRate': round(sum(spins) / len(spins)) if spins else None,
            'minSpinRate': round(min(spins)) if spins else None,
            'pitchTypes': type_counts,
            'pitchTypeNames': type_names,
        }

    return result


def parse_hit_data(feed_data: dict, bref_id_map: dict = None) -> dict:
    """Extract per-batter hit data (exit velo, launch angle, distance) from play-by-play."""
    if bref_id_map is None:
        bref_id_map = {}

    batter_hits = {}  # keyed by mlb_id
    all_plays = feed_data.get('liveData', {}).get('plays', {}).get('allPlays', [])

    for play in all_plays:
        matchup = play.get('matchup', {})
        batter_mlb_id = matchup.get('batter', {}).get('id')
        batter_name = matchup.get('batter', {}).get('fullName', '')

        if not batter_mlb_id:
            continue

        for event in play.get('playEvents', []):
            hit_data = event.get('hitData', {})
            if not hit_data or not hit_data.get('launchSpeed'):
                continue

            if batter_mlb_id not in batter_hits:
                batter_hits[batter_mlb_id] = {
                    'name': batter_name,
                    'player_id': bref_id_map.get(batter_mlb_id, f'mlb_{batter_mlb_id}'),
                    'batted_balls': [],
                }

            play_result = play.get('result', {})
            play_about = play.get('about', {})
            batter_hits[batter_mlb_id]['batted_balls'].append({
                'speed': hit_data.get('launchSpeed'),
                'angle': hit_data.get('launchAngle'),
                'distance': hit_data.get('totalDistance'),
                'trajectory': hit_data.get('trajectory', ''),
                'hardness': hit_data.get('hardness', ''),
                'result': play_result.get('event') or '',
                'description': play_result.get('description') or '',
                'inning': play_about.get('inning'),
                'half': play_about.get('halfInning', ''),
            })

    # Build summaries
    result = {}
    for mlb_id, bdata in batter_hits.items():
        balls = bdata['batted_balls']
        speeds = [b['speed'] for b in balls if b.get('speed')]
        distances = [b['distance'] for b in balls if b.get('distance')]
        trajectories = {}
        for b in balls:
            t = b.get('trajectory', '')
            if t:
                trajectories[t] = trajectories.get(t, 0) + 1

        hardest = max(balls, key=lambda b: b.get('speed') or 0) if balls else {}
        result[bdata['player_id']] = {
            'name': bdata['name'],
            'player_id': bdata['player_id'],
            'battedBalls': len(balls),
            'maxExitVelo': round(max(speeds), 1) if speeds else None,
            'avgExitVelo': round(sum(speeds) / len(speeds), 1) if speeds else None,
            'maxDistance': round(max(distances)) if distances else None,
            'maxExitVeloDistance': round(hardest.get('distance')) if hardest.get('distance') else None,
            'maxExitVeloResult': hardest.get('result') or '',
            'maxExitVeloDescription': hardest.get('description') or '',
            'maxExitVeloInning': hardest.get('inning'),
            'maxExitVeloHalf': hardest.get('half') or '',
            'maxExitVeloTrajectory': hardest.get('trajectory') or '',
            'trajectories': trajectories,
        }

    return result


def parse_linescore(feed_data: dict) -> dict:
    """Parse inning-by-inning linescore."""
    linescore = feed_data.get('liveData', {}).get('linescore', {})
    innings = linescore.get('innings', [])

    away_runs = []
    home_runs = []

    for inning in innings:
        away_runs.append(inning.get('away', {}).get('runs', 0))
        home_runs.append(inning.get('home', {}).get('runs', 0))

    teams = linescore.get('teams', {})

    return {
        'away': {
            'innings': [str(r) for r in away_runs],
            'R': teams.get('away', {}).get('runs', 0),
            'H': teams.get('away', {}).get('hits', 0),
            'E': teams.get('away', {}).get('errors', 0),
        },
        'home': {
            'innings': [str(r) for r in home_runs],
            'R': teams.get('home', {}).get('runs', 0),
            'H': teams.get('home', {}).get('hits', 0),
            'E': teams.get('home', {}).get('errors', 0),
        },
    }


def parse_substitutions(feed_data: dict, bref_id_map: dict = None) -> list:
    """Parse substitutions from play-by-play data."""
    if bref_id_map is None:
        bref_id_map = {}

    plays = feed_data.get('liveData', {}).get('plays', {})
    all_plays = plays.get('allPlays', [])

    substitutions = []

    for play in all_plays:
        play_events = play.get('playEvents', [])
        about = play.get('about', {})
        inning = about.get('inning', 0)
        half_inning = about.get('halfInning', '')

        for pe in play_events:
            if pe.get('type') != 'action':
                continue

            details = pe.get('details', {})
            event_type = details.get('eventType', '')

            # Check for substitution events
            if event_type in ['pitching_substitution', 'offensive_substitution',
                              'defensive_substitution', 'defensive_switch']:
                description = details.get('description', '')

                # Try to extract player info
                player = pe.get('player', {})
                mlb_id = player.get('id')
                bref_id = bref_id_map.get(mlb_id) if mlb_id else None

                substitutions.append({
                    'inning': inning,
                    'half': half_inning,
                    'type': event_type,
                    'description': description,
                    'player_id': bref_id or (f"mlb_{mlb_id}" if mlb_id else None),
                    'mlb_id': mlb_id,
                })

    return substitutions


def parse_play_by_play(feed_data: dict, bref_id_map: dict = None) -> list:
    """Parse play-by-play events from the API."""
    if bref_id_map is None:
        bref_id_map = {}

    plays = feed_data.get('liveData', {}).get('plays', {})
    all_plays = plays.get('allPlays', [])

    # Derive team codes for pitching_team / batting_team fields (half-inning
    # based). Several downstream detectors (3-K innings, immaculate innings,
    # etc.) require these to identify the pitcher's team.
    teams = feed_data.get('gameData', {}).get('teams', {})
    away_team_id = teams.get('away', {}).get('id')
    home_team_id = teams.get('home', {}).get('id')
    away_code = TEAM_ID_TO_CODE.get(away_team_id, teams.get('away', {}).get('abbreviation', ''))
    home_code = TEAM_ID_TO_CODE.get(home_team_id, teams.get('home', {}).get('abbreviation', ''))

    play_by_play = []

    for play in all_plays:
        result = play.get('result', {})
        about = play.get('about', {})
        matchup = play.get('matchup', {})

        event_type = result.get('eventType', '')
        if not event_type:
            continue
        description = result.get('description', '')
        is_grand_slam = 'grand slam' in description.lower()
        is_home_run = event_type == 'home_run' or is_grand_slam

        half = about.get('halfInning', '')
        # Top of inning: away bats, home pitches. Bottom: reverse.
        if half == 'top':
            batting_team = away_code
            pitching_team = home_code
        else:
            batting_team = home_code
            pitching_team = away_code

        # Get batter and pitcher info
        batter = matchup.get('batter', {})
        pitcher = matchup.get('pitcher', {})
        batter_mlb_id = batter.get('id')
        pitcher_mlb_id = pitcher.get('id')

        # Get BREF IDs with full fallback chain
        batter_name = batter.get('fullName', '')
        pitcher_name = pitcher.get('fullName', '')
        batter_bref = bref_id_map.get(batter_mlb_id)
        pitcher_bref = bref_id_map.get(pitcher_mlb_id)

        # Try Chadwick/name fallback if not in map
        if not batter_bref and batter_mlb_id:
            batter_bref = get_bref_id_from_chadwick(batter_mlb_id)
        if not pitcher_bref and pitcher_mlb_id:
            pitcher_bref = get_bref_id_from_chadwick(pitcher_mlb_id)

        play_data = {
            'inning': about.get('inning', 0),
            'half': half,
            'batting_team': batting_team,
            'pitching_team': pitching_team,
            'outs_before': play.get('count', {}).get('outs', 0),
            'event': result.get('event', ''),
            'event_type': event_type,
            'description': description,
            'home_run': is_home_run,
            'grand_slam': is_grand_slam,
            'rbi': result.get('rbi', 0),
            'is_scoring_play': about.get('isScoringPlay', False),
            'run_scored': about.get('isScoringPlay', False),
            'away_score': result.get('awayScore', 0),
            'home_score': result.get('homeScore', 0),
            'batter': batter_name,
            'batter_id': batter_bref or (f"mlb_{batter_mlb_id}" if batter_mlb_id else None),
            'pitcher': pitcher_name,
            'pitcher_id': pitcher_bref or (f"mlb_{pitcher_mlb_id}" if pitcher_mlb_id else None),
        }

        pitch_events = [event for event in play.get('playEvents', []) if event.get('isPitch')]
        if pitch_events:
            last_pitch = pitch_events[-1]
            pitch_details = last_pitch.get('details', {})
            pitch_type = pitch_details.get('type', {})
            pitch_data = last_pitch.get('pitchData', {})
            pitch_count = last_pitch.get('count') or play.get('count') or {}
            pitch_number = last_pitch.get('pitchNumber') or len(pitch_events)

            play_data['pitch_count'] = len(pitch_events)
            play_data['pitch_number'] = pitch_number
            play_data['pitch_count_at_play'] = f"{pitch_count.get('balls', 0)}-{pitch_count.get('strikes', 0)}"
            play_data['pitch_call'] = pitch_details.get('description', '')
            if isinstance(pitch_type, dict):
                play_data['pitch_type'] = pitch_type.get('description', '')
                play_data['pitch_type_code'] = pitch_type.get('code', '')
            if pitch_data.get('startSpeed') is not None:
                play_data['pitch_speed'] = pitch_data.get('startSpeed')

        # Add runner movement if available
        runners = play.get('runners', [])
        if runners:
            play_data['runners'] = []
            for runner in runners:
                movement = runner.get('movement', {})
                details = runner.get('details', {})
                runner_info = details.get('runner', {})
                runner_mlb_id = runner_info.get('id')

                runner_bref = bref_id_map.get(runner_mlb_id)
                if not runner_bref and runner_mlb_id:
                    runner_bref = get_bref_id_from_chadwick(runner_mlb_id)

                play_data['runners'].append({
                    'name': runner_info.get('fullName', ''),
                    'player_id': runner_bref or (f"mlb_{runner_mlb_id}" if runner_mlb_id else None),
                    'start': movement.get('start'),
                    'end': movement.get('end'),
                    'is_out': movement.get('isOut', False),
                    'event': details.get('event', ''),
                })

        play_by_play.append(play_data)

    return play_by_play


def generate_game_id(basic_info: dict, game_pk: int) -> str:
    """Generate a BREF-format game ID: {bref_home_code}{YYYYMMDD}{suffix}.

    Using BREF's 3-letter codes (SFN, CHA, LAN, etc.) so API-sourced games
    have the same ID format as BREF-sourced games — milestones, attended-game
    lookups, and dedup all work uniformly. BREF prevents collisions by
    deduping on date+teams.
    """
    from ..scrapers.download_bref import BREF_TEAM_CODES
    mlb_code = basic_info.get('home_team_code', 'UNK')
    home_code = BREF_TEAM_CODES.get(mlb_code, mlb_code)
    date = basic_info.get('date_yyyymmdd', '')
    doubleheader = basic_info.get('doubleheader', '0')
    is_dh = doubleheader not in ('0', 'N', '')
    if is_dh:
        game_num = basic_info.get('game_number', 1)
        suffix = '2' if int(game_num) == 2 else '1'
    else:
        suffix = '0'
    return f"{home_code}{date}{suffix}"


def parse_mlb_game(url_or_id: Union[str, int], verbose: bool = False, map_player_ids: bool = True) -> dict:
    """
    Parse an MLB game from MLB.com/Stats API.

    Args:
        url_or_id: MLB.com gameday URL or game ID (gamePk)
        verbose: Print progress messages
        map_player_ids: Attempt to map MLB IDs to BREF IDs (requires baseball_id package)

    Returns:
        Game data dict compatible with BREF parser output
    """
    game_pk = extract_game_id(url_or_id)

    if verbose:
        print(f"Fetching game {game_pk} from MLB Stats API...")

    # Fetch data from API
    data = fetch_game_data(game_pk)
    feed_data = data['feed']
    box_data = data['boxscore']

    # Parse components
    basic_info = parse_basic_info(feed_data, box_data)

    if verbose:
        print(f"  {basic_info['away_team']} @ {basic_info['home_team']}")
        print(f"  {basic_info['date']} at {basic_info['venue']}")
        print(f"  Game type: {basic_info['game_type']}")

    # Collect all MLB player IDs for batch lookup
    bref_id_map = {}
    if map_player_ids:
        all_mlb_ids = set()
        for side in ['away', 'home']:
            team_data = box_data.get('teams', {}).get(side, {})
            players = team_data.get('players', {})
            for player_key, player in players.items():
                mlb_id = player.get('person', {}).get('id')
                if mlb_id:
                    all_mlb_ids.add(mlb_id)

        if all_mlb_ids:
            if verbose:
                print(f"  Mapping {len(all_mlb_ids)} player IDs to BREF...")
            # Use Chadwick register + get_bref_id for each player (works without baseball_id)
            for mlb_id in all_mlb_ids:
                bref_id = get_bref_id(mlb_id)
                if bref_id:
                    bref_id_map[mlb_id] = bref_id
            # Also try batch lookup via baseball_id if available
            if HAS_BASEBALL_ID:
                unmapped = [mid for mid in all_mlb_ids if mid not in bref_id_map or not bref_id_map[mid]]
                if unmapped:
                    extra = batch_get_bref_ids(unmapped)
                    for mid, bid in extra.items():
                        if bid:
                            bref_id_map[mid] = bid
            mapped_count = sum(1 for v in bref_id_map.values() if v)
            if verbose:
                print(f"  Mapped {mapped_count}/{len(all_mlb_ids)} players to BREF IDs")

    # Extract year for player ID disambiguation
    game_year = None
    date_str = basic_info.get('date_yyyymmdd', '')
    if date_str and len(date_str) >= 4:
        try:
            game_year = int(date_str[:4])
        except ValueError:
            pass

    batting = {
        'away': parse_batting(box_data, 'away', bref_id_map, game_year),
        'home': parse_batting(box_data, 'home', bref_id_map, game_year),
    }

    pitching = {
        'away': parse_pitching(box_data, 'away', bref_id_map, game_year),
        'home': parse_pitching(box_data, 'home', bref_id_map, game_year),
    }

    linescore = parse_linescore(feed_data)
    umpires = parse_umpires(box_data)
    pitch_data = parse_pitch_data(feed_data, bref_id_map)
    hit_data = parse_hit_data(feed_data, bref_id_map)

    # No-hitter / perfect game flags
    flags = feed_data.get('gameData', {}).get('flags', {})
    game_flags = {
        'no_hitter': flags.get('noHitter', False) or flags.get('homeTeamNoHitter', False) or flags.get('awayTeamNoHitter', False),
        'perfect_game': flags.get('perfectGame', False) or flags.get('homeTeamPerfectGame', False) or flags.get('awayTeamPerfectGame', False),
    }

    # ABS challenges
    abs_raw = feed_data.get('gameData', {}).get('absChallenges', {})
    abs_challenges = None
    if abs_raw.get('hasChallenges'):
        abs_challenges = {
            'away': abs_raw.get('away', {}),
            'home': abs_raw.get('home', {}),
        }
        # Parse individual review details from play-by-play
        reviews = []
        all_plays = feed_data.get('liveData', {}).get('plays', {}).get('allPlays', [])
        for play in all_plays:
            matchup = play.get('matchup', {})
            for ev in play.get('playEvents', []):
                r = ev.get('reviewDetails')
                if r:
                    details = ev.get('details', {})
                    call = details.get('call', {})
                    pitch_type = details.get('type', {})
                    count = ev.get('count', {})
                    challenge_player = r.get('player', {}) or {}
                    batter = matchup.get('batter', {}) or {}
                    pitcher = matchup.get('pitcher', {}) or {}
                    # Determine which team challenged
                    challenge_team_id = r.get('challengeTeamId')
                    away_id = feed_data.get('gameData', {}).get('teams', {}).get('away', {}).get('id')
                    is_away_challenge = challenge_team_id == away_id
                    reviews.append({
                        'overturned': r.get('isOverturned', False),
                        'batter': batter.get('fullName', ''),
                        'batterId': _person_id(batter),
                        'pitcher': pitcher.get('fullName', ''),
                        'pitcherId': _person_id(pitcher),
                        'challengerType': infer_abs_challenger_type(matchup, r),
                        'challengePlayer': challenge_player.get('fullName', ''),
                        'challengeTeam': 'away' if is_away_challenge else 'home',
                        'challengingPlayerId': _person_id(challenge_player),
                        'originalCall': call.get('description', ''),
                        'pitchType': pitch_type.get('description', '') if isinstance(pitch_type, dict) else '',
                        'count': f"{count.get('balls', 0)}-{count.get('strikes', 0)}",
                        'inning': play.get('about', {}).get('inning', 0),
                        'half': play.get('about', {}).get('halfInning', ''),
                    })
        abs_challenges['reviews'] = reviews

    # Parse play-by-play and substitutions
    substitutions = parse_substitutions(feed_data, bref_id_map)
    play_by_play = parse_play_by_play(feed_data, bref_id_map)

    if verbose:
        print(f"  Parsed {len(play_by_play)} plays, {len(substitutions)} substitutions")

    game_id = generate_game_id(basic_info, game_pk)

    # Build lineups from batting starters
    lineups = {'away': [], 'home': []}
    for side in ['away', 'home']:
        for batter in batting[side]:
            if batter.get('is_starter') and batter.get('lineup_slot'):
                lineups[side].append({
                    'slot': batter['lineup_slot'],
                    'name': batter['name'],
                    'player_id': batter['player_id'],
                    'pos': batter['position'],
                    'jersey_number': batter.get('jersey_number', ''),
                })
        lineups[side].sort(key=lambda x: x['slot'])

    # Add starting pitchers to lineups
    for side in ['away', 'home']:
        if pitching[side]:
            sp = pitching[side][0]  # First pitcher is the starter
            lineups[side].append({
                'slot': 0,
                'name': sp['name'],
                'player_id': sp['player_id'],
                'pos': 'P',
                'jersey_number': sp.get('jersey_number', ''),
            })

    # Normalize substitution format to match BREF parser output
    normalized_subs = []
    for sub in substitutions:
        desc = sub.get('description', '')
        # Parse "Pitching Change: X replaces Y." or "Offensive Sub: X replaces Y."
        player_in = ''
        player_out = ''
        replace_match = re.search(r'(?:Pitching Change:|Offensive Substitution:|Defensive Sub:)?\s*(.+?)\s+replaces\s+(.+?)\.?$', desc)
        if replace_match:
            player_in = replace_match.group(1).strip()
            player_out = replace_match.group(2).strip()
        elif 'pinch' in desc.lower():
            ph_match = re.search(r'(.+?)\s+(?:pinch [hb])', desc)
            if ph_match:
                player_in = ph_match.group(1).strip()

        normalized_subs.append({
            'raw': desc,
            'type': sub.get('type', 'substitution'),
            'player_in': player_in,
            'player_out': player_out,
            'inning': sub.get('inning', 0),
            'half': sub.get('half', ''),
            'player_id': sub.get('player_id', ''),
        })

    # Parse pitcher decisions from live feed
    decisions = feed_data.get('liveData', {}).get('decisions', {})
    pitcher_decisions = {}
    decision_mlb_ids = {}
    if decisions:
        for role, key in [('winner', 'winning_pitcher'), ('loser', 'losing_pitcher'), ('save', 'save_pitcher')]:
            player = decisions.get(role, {})
            if player:
                mlb_id = player.get('id')
                name = player.get('fullName', '')
                bref_id = bref_id_map.get(mlb_id, '')
                pitcher_decisions[key] = name
                pitcher_decisions[f'{key}_id'] = bref_id or f'mlb_{mlb_id}'
                decision_mlb_ids[role] = mlb_id

    # Set win/loss/save flags on individual pitcher data
    for side in ['away', 'home']:
        for pitcher in pitching[side]:
            mlb_id = pitcher.get('mlb_id')
            is_winner = mlb_id == decision_mlb_ids.get('winner')
            is_loser = mlb_id == decision_mlb_ids.get('loser')
            is_save = mlb_id == decision_mlb_ids.get('save')
            pitcher['win'] = is_winner
            pitcher['loss'] = is_loser
            pitcher['save'] = is_save
            if is_winner:
                pitcher['decision'] = 'W'
            elif is_loser:
                pitcher['decision'] = 'L'
            elif is_save:
                pitcher['decision'] = 'S'

    game_data = {
        'basic_info': basic_info,
        'batting': batting,
        'pitching': pitching,
        'linescore': linescore,
        'game_id': game_id,
        'mlb_game_pk': game_pk,
        'source': 'mlb',
        # Parsed fields
        'lineups': lineups,
        'substitutions': normalized_subs,
        'play_by_play': play_by_play,
        'pitcher_decisions': pitcher_decisions,
        'special_events': {},
        'milestone_stats': {},
        'umpires': umpires,
        'flags': game_flags,
        'abs_challenges': abs_challenges,
        'pitch_data': pitch_data,
        'hit_data': hit_data,
        'doubleheader': basic_info.get('doubleheader', 'N'),
        'raw_plays': play_by_play,
        'footer_summary': {},
    }

    # Resolve any register-format player IDs to MLB-format IDs
    game_data = resolve_player_ids_in_game(game_data, verbose=verbose)
    normalize_api_batting_rows(game_data)
    SpecialEventsEngine(game_data).detect()
    MilestoneEngine(game_data).process()

    return game_data


def update_cached_games_with_resolved_ids(cache_dir: str = None, verbose: bool = False) -> dict:
    """
    Update existing cached games to resolve register-format IDs to MLB-format IDs.

    Args:
        cache_dir: Path to cache directory (defaults to project cache/)
        verbose: Print progress messages

    Returns:
        Dict with counts: {'scanned': N, 'updated': N, 'resolved': N}
    """
    import json
    from pathlib import Path

    if cache_dir is None:
        cache_dir = Path(__file__).parent.parent.parent / 'cache'
    else:
        cache_dir = Path(cache_dir)

    if not cache_dir.exists():
        print(f"Cache directory not found: {cache_dir}")
        return {'scanned': 0, 'updated': 0, 'resolved': 0}

    stats = {'scanned': 0, 'updated': 0, 'resolved': 0}

    # Find all JSON cache files (excluding career_firsts subdirectory)
    cache_files = [f for f in cache_dir.glob("*.json") if f.is_file()]

    print(f"Scanning {len(cache_files)} cached games for register-format IDs...")

    for cache_file in cache_files:
        stats['scanned'] += 1

        try:
            with open(cache_file, 'r') as f:
                game_data = json.load(f)

            # Only process MLB API games (source: 'mlb')
            if game_data.get('basic_info', {}).get('source') != 'mlb' and game_data.get('source') != 'mlb':
                continue

            # Check if this game has register-format IDs
            has_register_ids = False
            for side in ['away', 'home']:
                for player in game_data.get('batting', {}).get(side, []):
                    if is_register_format_id(player.get('player_id', '')):
                        has_register_ids = True
                        break
                if has_register_ids:
                    break

            if not has_register_ids:
                continue

            if verbose:
                print(f"  Processing: {cache_file.name}")

            # Resolve IDs
            original_data = json.dumps(game_data)
            game_data = resolve_player_ids_in_game(game_data, verbose=verbose)
            new_data = json.dumps(game_data)

            # Only write if something changed
            if original_data != new_data:
                with open(cache_file, 'w') as f:
                    json.dump(game_data, f, indent=2)
                stats['updated'] += 1

                # Count resolved IDs
                for side in ['away', 'home']:
                    for player in game_data.get('batting', {}).get(side, []):
                        if player.get('register_id'):
                            stats['resolved'] += 1
                    for player in game_data.get('pitching', {}).get(side, []):
                        if player.get('register_id'):
                            stats['resolved'] += 1

        except (json.JSONDecodeError, IOError) as e:
            if verbose:
                print(f"  Error processing {cache_file.name}: {e}")
            continue

    print(f"\nResults: Scanned {stats['scanned']} files, updated {stats['updated']} files, resolved {stats['resolved']} player IDs")
    return stats


if __name__ == '__main__':
    import argparse
    import json

    parser = argparse.ArgumentParser(description='Parse MLB.com game box scores')
    parser.add_argument('game', nargs='?', help='MLB.com URL or game ID')
    parser.add_argument('--verbose', '-v', action='store_true', help='Verbose output')
    parser.add_argument('--json', '-j', action='store_true', help='Output as JSON')
    parser.add_argument('--update-cache', action='store_true',
                        help='Update existing cached games to resolve register-format player IDs')

    args = parser.parse_args()

    if args.update_cache:
        update_cached_games_with_resolved_ids(verbose=args.verbose)
    elif args.game:
        game_data = parse_mlb_game(args.game, verbose=args.verbose)

        if args.json:
            print(json.dumps(game_data, indent=2))
        else:
            bi = game_data['basic_info']
            print(f"\n{'='*60}")
            print(f"{bi['away_team']} ({bi['away_score']}) @ {bi['home_team']} ({bi['home_score']})")
            print(f"{bi['date']}")
            print(f"{bi['venue']}, {bi.get('venue_city', '')}, {bi.get('venue_state', '')}")
            print(f"Game Type: {bi['game_type'].upper()}")
            print(f"Game ID: {game_data['game_id']}")
            print(f"{'='*60}")

            print(f"\n{bi['away_team']} Batting:")
            for b in game_data['batting']['away'][:5]:
                print(f"  {b['name']}: {b['H']}-{b['AB']}, {b['R']} R, {b['RBI']} RBI")

            print(f"\n{bi['home_team']} Batting:")
            for b in game_data['batting']['home'][:5]:
                print(f"  {b['name']}: {b['H']}-{b['AB']}, {b['R']} R, {b['RBI']} RBI")
    else:
        parser.print_help()
