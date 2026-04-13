"""
Compare cached BREF box scores against MLB API to detect scoring changes.

Usage:
    python3 -m baseball_processor.scrapers.scoring_check              # Check all games
    python3 -m baseball_processor.scrapers.scoring_check --recent 30  # Last 30 days only
    python3 -m baseball_processor.scrapers.scoring_check --game SFN202604070  # Specific game
    python3 -m baseball_processor.scrapers.scoring_check --verbose    # Show all comparisons
"""

import argparse
import json
import time
import unicodedata
from datetime import datetime, timedelta
from pathlib import Path

from ..utils.http import create_retry_session, get_with_retry

CACHE_DIR = Path(__file__).parent.parent.parent / 'cache'
MLB_API_BASE = 'https://statsapi.mlb.com/api/v1'

PITCHING_STATS = ['IP', 'H', 'R', 'ER', 'BB', 'SO', 'HR']
BATTING_STATS = ['AB', 'H', 'R', 'RBI', 'HR', 'BB', 'SO']

# MLB API field name mapping (API name -> our name)
API_PITCHING_MAP = {
    'inningsPitched': 'IP', 'hits': 'H', 'runs': 'R', 'earnedRuns': 'ER',
    'baseOnBalls': 'BB', 'strikeOuts': 'SO', 'homeRuns': 'HR',
}
API_BATTING_MAP = {
    'atBats': 'AB', 'hits': 'H', 'runs': 'R', 'rbi': 'RBI',
    'homeRuns': 'HR', 'baseOnBalls': 'BB', 'strikeOuts': 'SO',
}


def normalize_name(name):
    """Normalize player name for fuzzy matching."""
    name = unicodedata.normalize('NFKD', name or '')
    name = ''.join(c for c in name if not unicodedata.combining(c))
    return name.lower().strip().replace('.', '').replace("'", '').replace('-', ' ')


def parse_ip(ip_val):
    """Normalize IP to string like '5.1' for comparison."""
    if ip_val is None:
        return '0.0'
    s = str(ip_val).strip()
    # BREF sometimes stores as "5" instead of "5.0"
    if '.' not in s:
        s += '.0'
    return s


def fetch_boxscore(session, game_pk):
    """Fetch boxscore from MLB API."""
    url = f'{MLB_API_BASE}/game/{game_pk}/boxscore'
    resp = get_with_retry(session, url, timeout=30)
    if resp.status_code != 200:
        return None
    return resp.json()


def extract_api_players(boxscore, side):
    """Extract pitchers and batters from API boxscore for one side."""
    team = boxscore.get('teams', {}).get(side, {})
    players = team.get('players', {})

    pitchers = []
    batters = []
    for pid, pdata in players.items():
        name = pdata.get('person', {}).get('fullName', '')
        stats = pdata.get('stats', {})

        pitch_stats = stats.get('pitching', {})
        if pitch_stats and pitch_stats.get('inningsPitched'):
            row = {'name': name}
            for api_key, our_key in API_PITCHING_MAP.items():
                val = pitch_stats.get(api_key)
                if our_key == 'IP':
                    row[our_key] = str(val) if val else '0.0'
                else:
                    row[our_key] = int(val) if val is not None else 0
            pitchers.append(row)

        bat_stats = stats.get('batting', {})
        if bat_stats and (bat_stats.get('atBats', 0) > 0 or bat_stats.get('runs', 0) > 0
                          or bat_stats.get('baseOnBalls', 0) > 0 or bat_stats.get('hits', 0) > 0):
            row = {'name': name}
            for api_key, our_key in API_BATTING_MAP.items():
                row[our_key] = int(bat_stats.get(api_key, 0) or 0)
            batters.append(row)

    return pitchers, batters


def match_players(cached_list, api_list):
    """Match cached players to API players by name. Returns list of (cached, api) pairs."""
    api_remaining = list(range(len(api_list)))
    matches = []

    for cached in cached_list:
        cn = normalize_name(cached.get('name', ''))
        best_idx = None
        for i in api_remaining:
            an = normalize_name(api_list[i].get('name', ''))
            # Exact match or last-name match
            if cn == an or cn.split()[-1:] == an.split()[-1:]:
                best_idx = i
                if cn == an:
                    break  # Prefer exact
        if best_idx is not None:
            matches.append((cached, api_list[best_idx]))
            api_remaining.remove(best_idx)
        else:
            matches.append((cached, None))

    return matches


def compare_stats(cached, api, stat_keys, ip_mode=False):
    """Compare stat values between cached and API. Returns list of (stat, cached_val, api_val).

    Skips stats where cached value is None (BREF omits column entirely, e.g. HR when no HRs in game).
    """
    diffs = []
    for stat in stat_keys:
        cached_raw = cached.get(stat)
        if cached_raw is None:
            continue  # Column not in BREF table — can't compare
        if ip_mode and stat == 'IP':
            cv = parse_ip(cached_raw)
            av = parse_ip(api.get(stat)) if api else '0.0'
        else:
            cv = int(cached_raw or 0)
            av = int(api.get(stat, 0) or 0) if api else 0
        if cv != av:
            diffs.append((stat, cv, av))
    return diffs


def build_bref_url(game_id):
    """Build Baseball Reference box score URL from game ID."""
    if not game_id or len(game_id) < 4:
        return ''
    team_code = game_id[:3]
    return f'https://www.baseball-reference.com/boxes/{team_code}/{game_id}.shtml'


def main():
    parser = argparse.ArgumentParser(description='Check for scoring changes between BREF cache and MLB API')
    parser.add_argument('--recent', type=int, metavar='DAYS', help='Only check games from last N days')
    parser.add_argument('--game', type=str, metavar='GAME_ID', help='Check specific game by ID (e.g., SFN202604070)')
    parser.add_argument('--delay', type=float, default=0.3, help='Delay between API requests (default: 0.3s)')
    parser.add_argument('--verbose', '-v', action='store_true', help='Show all games checked, not just mismatches')
    args = parser.parse_args()

    session = create_retry_session()
    cutoff_date = None
    if args.recent:
        cutoff_date = (datetime.now() - timedelta(days=args.recent)).strftime('%Y%m%d')

    # Load all cached games
    games = []
    skip_patterns = ['career_firsts', 'career_gamelogs', 'player_bios']
    for cache_file in sorted(CACHE_DIR.glob('*.json')):
        if any(p in cache_file.name for p in skip_patterns):
            continue
        try:
            game = json.load(open(cache_file))
        except (json.JSONDecodeError, IOError):
            continue

        game_id = game.get('game_id', '')
        game_pk = game.get('mlb_game_pk')
        if not game_pk:
            continue

        # Filter by specific game
        if args.game and game_id != args.game:
            continue

        # Filter by date
        date_str = game.get('basic_info', {}).get('date_yyyymmdd', '')
        if cutoff_date and date_str < cutoff_date:
            continue

        games.append((cache_file, game, game_id, game_pk, date_str))

    if not games:
        print('No games to check.')
        return

    print(f'Checking {len(games)} game(s) against MLB API...\n')

    mismatched_games = []
    checked = 0

    for cache_file, game, game_id, game_pk, date_str in games:
        checked += 1
        basic = game.get('basic_info', {})
        away = basic.get('away_team_code', '?')
        home = basic.get('home_team_code', '?')
        # Format date for display
        date_display = date_str
        if len(date_str) == 8:
            date_display = f'{date_str[4:6]}/{date_str[6:]}/{date_str[:4]}'

        if args.verbose:
            print(f'[{checked}/{len(games)}] {game_id} ({away} @ {home}, {date_display})')

        boxscore = fetch_boxscore(session, game_pk)
        if not boxscore:
            if args.verbose:
                print(f'  Could not fetch boxscore (pk={game_pk})')
            continue

        game_diffs = []

        for side, label in [('away', away), ('home', home)]:
            api_pitchers, api_batters = extract_api_players(boxscore, side)

            # Compare pitching
            cached_pitchers = game.get('pitching', {}).get(side, [])
            pitcher_matches = match_players(cached_pitchers, api_pitchers)
            for cached_p, api_p in pitcher_matches:
                diffs = compare_stats(cached_p, api_p, PITCHING_STATS, ip_mode=True)
                if diffs:
                    game_diffs.append(('PITCHING', cached_p.get('name', '?'), label, diffs))

            # Compare batting
            cached_batters = game.get('batting', {}).get(side, [])
            batter_matches = match_players(cached_batters, api_batters)
            for cached_b, api_b in batter_matches:
                diffs = compare_stats(cached_b, api_b, BATTING_STATS)
                if diffs:
                    game_diffs.append(('BATTING', cached_b.get('name', '?'), label, diffs))

        if game_diffs:
            if not args.verbose:
                print(f'{game_id} ({away} @ {home}, {date_display})')
            for dtype, name, team, diffs in game_diffs:
                print(f'  {dtype} MISMATCH: {name} ({team})')
                for stat, cv, av in diffs:
                    print(f'    {stat}: {cv} (BREF) -> {av} (API)')
            print()
            mismatched_games.append((game_id, date_display, away, home))
        elif args.verbose:
            print(f'  OK')

        if args.delay > 0:
            time.sleep(args.delay)

    # Summary
    print('=' * 50)
    if mismatched_games:
        print(f'{len(mismatched_games)} of {checked} games have scoring changes:\n')
        for game_id, date_display, away, home in mismatched_games:
            print(f'  {game_id} ({date_display}) - {away} @ {home}')
            url = build_bref_url(game_id)
            if url:
                print(f'    -> Re-download: {url}')
        print()
    else:
        print(f'All {checked} games match the MLB API. No scoring changes detected.')


if __name__ == '__main__':
    main()
