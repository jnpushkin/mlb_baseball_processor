"""
Download BREF HTML box scores for API-sourced games that are >24 hours old.

Usage:
    python3 -m baseball_processor.scrapers.download_bref           # Download missing HTMLs
    python3 -m baseball_processor.scrapers.download_bref --all     # Check all API games, not just recent
    python3 -m baseball_processor.scrapers.download_bref --dry-run # Preview without downloading
"""

import argparse
import json
import re
import time
from datetime import datetime, timedelta
from pathlib import Path

from ..utils.http import create_retry_session, get_with_retry

CACHE_DIR = Path(__file__).parent.parent.parent / 'cache'
HTML_DIR = Path(__file__).parent.parent.parent / 'Current Season Games'

# BREF team code mapping (MLB API codes -> BREF codes used in URLs)
BREF_TEAM_CODES = {
    'ARI': 'ARI', 'ATL': 'ATL', 'BAL': 'BAL', 'BOS': 'BOS',
    'CHC': 'CHN', 'CHW': 'CHA', 'CIN': 'CIN', 'CLE': 'CLE',
    'COL': 'COL', 'DET': 'DET', 'HOU': 'HOU', 'KC': 'KCA',
    'LAA': 'ANA', 'LAD': 'LAN', 'MIA': 'MIA', 'MIL': 'MIL',
    'MIN': 'MIN', 'NYM': 'NYN', 'NYY': 'NYA', 'OAK': 'OAK',
    'ATH': 'ATH', 'PHI': 'PHI', 'PIT': 'PIT', 'SD': 'SDN',
    'SF': 'SFN', 'SEA': 'SEA', 'STL': 'SLN', 'TB': 'TBA',
    'TEX': 'TEX', 'TOR': 'TOR', 'WSH': 'WAS',
}

# Full team names for HTML filename
TEAM_FULL_NAMES = {
    'ARI': 'Arizona Diamondbacks', 'ATL': 'Atlanta Braves', 'BAL': 'Baltimore Orioles',
    'BOS': 'Boston Red Sox', 'CHC': 'Chicago Cubs', 'CHW': 'Chicago White Sox',
    'CIN': 'Cincinnati Reds', 'CLE': 'Cleveland Guardians', 'COL': 'Colorado Rockies',
    'DET': 'Detroit Tigers', 'HOU': 'Houston Astros', 'KC': 'Kansas City Royals',
    'LAA': 'Los Angeles Angels', 'LAD': 'Los Angeles Dodgers', 'MIA': 'Miami Marlins',
    'MIL': 'Milwaukee Brewers', 'MIN': 'Minnesota Twins', 'NYM': 'New York Mets',
    'NYY': 'New York Yankees', 'OAK': 'Athletics', 'ATH': 'Athletics',
    'PHI': 'Philadelphia Phillies', 'PIT': 'Pittsburgh Pirates',
    'SD': 'San Diego Padres', 'SF': 'San Francisco Giants', 'SEA': 'Seattle Mariners',
    'STL': 'St. Louis Cardinals', 'TB': 'Tampa Bay Rays', 'TEX': 'Texas Rangers',
    'TOR': 'Toronto Blue Jays', 'WSH': 'Washington Nationals',
}

MONTH_NAMES = {
    1: 'January', 2: 'February', 3: 'March', 4: 'April', 5: 'May', 6: 'June',
    7: 'July', 8: 'August', 9: 'September', 10: 'October', 11: 'November', 12: 'December',
}


def bref_game_id(api_game_id):
    """Convert API game ID (MBAL202604120) to BREF game ID (BAL202604120)."""
    if api_game_id.startswith('M'):
        return api_game_id[1:]
    return api_game_id


def bref_url(game_id):
    """Build BREF box score URL from game ID."""
    team_code = game_id[:3]
    return f'https://www.baseball-reference.com/boxes/{team_code}/{game_id}.shtml'


def expected_html_filename(away_team, home_team, date_str):
    """Build expected HTML filename matching BREF download format.

    Args:
        away_team: Away team code (e.g., 'SF')
        home_team: Home team code (e.g., 'BAL')
        date_str: Date as YYYYMMDD
    """
    away_name = TEAM_FULL_NAMES.get(away_team, away_team)
    home_name = TEAM_FULL_NAMES.get(home_team, home_team)

    year = int(date_str[:4])
    month = int(date_str[4:6])
    day = int(date_str[6:8])
    month_name = MONTH_NAMES.get(month, str(month))

    return f"{away_name} vs {home_name} Box Score_ {month_name} {day}, {year} _ Baseball-Reference.com.html"


def html_exists(away_team, home_team, date_str):
    """Check if a BREF HTML file already exists for this game."""
    expected = expected_html_filename(away_team, home_team, date_str)
    if (HTML_DIR / expected).exists():
        return True

    # Also check with fuzzy matching (date variations)
    year = int(date_str[:4])
    month = int(date_str[4:6])
    day = int(date_str[6:8])
    month_name = MONTH_NAMES.get(month, '')

    # Search for any file matching the teams and date
    pattern = f"*{month_name}*{day}*{year}*"
    away_name = TEAM_FULL_NAMES.get(away_team, away_team)
    home_name = TEAM_FULL_NAMES.get(home_team, home_team)
    for f in HTML_DIR.glob(pattern):
        fname = f.name
        if away_name in fname and home_name in fname:
            return True
        # Check with just last word of team name
        if away_team in fname and home_team in fname:
            return True

    return False


def run(all_games: bool = False, dry_run: bool = False, delay: float = 3.2,
        verbose: bool = True) -> dict:
    """Download missing BREF HTMLs for API-sourced games. Programmatic entry.

    Returns summary dict: {downloaded, errors, skipped_existing, found}.
    """
    min_age = timedelta(hours=24)
    now = datetime.now()
    cutoff_date = (now - timedelta(days=30)).strftime('%Y%m%d') if not all_games else '00000000'

    # Find API-sourced games needing HTML download
    to_download = []
    skip_patterns = ['career_firsts', 'career_gamelogs', 'player_bios', 'career_highs']

    for cache_file in sorted(CACHE_DIR.glob('*.json')):
        if any(p in cache_file.name for p in skip_patterns):
            continue
        try:
            game = json.load(open(cache_file))
        except (json.JSONDecodeError, IOError):
            continue

        source = game.get('basic_info', {}).get('source', game.get('source', 'bref'))
        if source != 'mlb':
            continue

        bi = game.get('basic_info', {})
        date_str = bi.get('date_yyyymmdd', '')
        if not date_str or date_str < cutoff_date:
            continue

        # Check age
        try:
            game_date = datetime.strptime(date_str, '%Y%m%d')
            if now - game_date < min_age:
                continue  # Too recent
        except ValueError:
            continue

        game_id = game.get('game_id', '')
        away = bi.get('away_team_code', '')
        home = bi.get('home_team_code', '')
        game_type = bi.get('game_type', 'regular')

        # Skip spring training / exhibition
        if game_type not in ('regular', 'postseason'):
            continue

        # Check if HTML already exists
        if html_exists(away, home, date_str):
            continue

        bref_gid = bref_game_id(game_id)
        to_download.append({
            'game_id': bref_gid,
            'api_game_id': game_id,
            'away': away,
            'home': home,
            'date': date_str,
            'url': bref_url(bref_gid),
            'filename': expected_html_filename(away, home, date_str),
        })

    if not to_download:
        if verbose:
            print("No BREF HTMLs to download. All API games already have HTML backups.")
        return {'downloaded': 0, 'errors': 0, 'found': 0}

    if verbose:
        print(f"Found {len(to_download)} game(s) needing BREF HTML download:\n")
        for g in to_download:
            print(f"  {g['api_game_id']} ({g['date'][:4]}-{g['date'][4:6]}-{g['date'][6:]}) {g['away']} @ {g['home']}")

    if dry_run:
        if verbose:
            print("\n(dry run — no downloads)")
        return {'downloaded': 0, 'errors': 0, 'found': len(to_download)}

    session = create_retry_session()
    downloaded = 0
    errors = 0

    if verbose:
        print()
    for i, g in enumerate(to_download, 1):
        if verbose:
            print(f"[{i}/{len(to_download)}] Downloading {g['game_id']}...", end=' ')

        resp = get_with_retry(session, g['url'], timeout=30, headers={
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7)'
        })

        if resp.status_code == 200:
            out_path = HTML_DIR / g['filename']
            out_path.write_text(resp.text, encoding='utf-8')
            if verbose:
                print(f"OK -> {g['filename'][:60]}")
            downloaded += 1
        elif resp.status_code == 429:
            if verbose:
                print(f"RATE LIMITED (429). Stopping — wait 15 min and retry.")
            break
        else:
            if verbose:
                print(f"FAILED ({resp.status_code})")
            errors += 1

        if i < len(to_download):
            time.sleep(delay)

    if verbose:
        print(f"\nDone: {downloaded} downloaded, {errors} errors")
    return {'downloaded': downloaded, 'errors': errors, 'found': len(to_download)}


def main():
    parser = argparse.ArgumentParser(description='Download BREF HTMLs for API-sourced games')
    parser.add_argument('--all', action='store_true', help='Check all API games, not just last 30 days')
    parser.add_argument('--dry-run', action='store_true', help='Preview without downloading')
    parser.add_argument('--delay', type=float, default=3.2, help='Delay between BREF requests (default: 3.2s)')
    args = parser.parse_args()
    run(all_games=args.all, dry_run=args.dry_run, delay=args.delay)


if __name__ == '__main__':
    main()
