"""
Add a game to the processor via MLB API (no BREF HTML needed).

Usage:
    python3 -m baseball_processor.scrapers.add_game --date 2026-04-07 --teams PHI SF
    python3 -m baseball_processor.scrapers.add_game --gamepk 823235
    python3 -m baseball_processor.scrapers.add_game --date 2026-04-07  # Lists all games that day
"""

import argparse
import json
import re
from datetime import datetime
from pathlib import Path

from ..parsers.mlb_api_parser import parse_mlb_game
from ..utils.http import create_retry_session, get_with_retry

CACHE_DIR = Path(__file__).parent.parent.parent / 'cache'
MLB_API_BASE = 'https://statsapi.mlb.com/api/v1'

# Team code aliases (common abbreviations -> MLB API team names)
TEAM_ALIASES = {
    'ARI': 'Arizona', 'ATL': 'Atlanta', 'BAL': 'Baltimore', 'BOS': 'Boston',
    'CHC': 'Cubs', 'CHW': 'White Sox', 'CIN': 'Cincinnati', 'CLE': 'Cleveland',
    'COL': 'Colorado', 'DET': 'Detroit', 'HOU': 'Houston', 'KC': 'Kansas City',
    'LAA': 'Angels', 'LAD': 'Dodgers', 'MIA': 'Miami', 'MIL': 'Milwaukee',
    'MIN': 'Minnesota', 'NYM': 'Mets', 'NYY': 'Yankees', 'OAK': 'Athletics',
    'ATH': 'Athletics', 'PHI': 'Philadelphia', 'PIT': 'Pittsburgh', 'SD': 'San Diego',
    'SF': 'San Francisco', 'SEA': 'Seattle', 'STL': 'St. Louis', 'TB': 'Tampa Bay',
    'TEX': 'Texas', 'TOR': 'Toronto', 'WSH': 'Washington',
}


def fetch_schedule(session, date_str):
    """Fetch MLB schedule for a given date. Returns list of games."""
    url = f'{MLB_API_BASE}/schedule?date={date_str}&sportId=1&hydrate=team'
    resp = get_with_retry(session, url, timeout=30)
    if resp.status_code != 200:
        return []
    data = resp.json()
    games = []
    for date in data.get('dates', []):
        for game in date.get('games', []):
            away = game.get('teams', {}).get('away', {}).get('team', {})
            home = game.get('teams', {}).get('home', {}).get('team', {})
            status = game.get('status', {}).get('detailedState', '')
            games.append({
                'gamePk': game['gamePk'],
                'away_name': away.get('name', ''),
                'away_abbr': away.get('abbreviation', ''),
                'home_name': home.get('name', ''),
                'home_abbr': home.get('abbreviation', ''),
                'status': status,
                'venue': game.get('venue', {}).get('name', ''),
                'gameType': game.get('gameType', 'R'),
            })
    return games


def match_team(query, games):
    """Match a team code/name against schedule games."""
    q = query.upper().strip()
    alias = TEAM_ALIASES.get(q, q).lower()
    for g in games:
        if (q == g['away_abbr'].upper() or q == g['home_abbr'].upper()
                or alias in g['away_name'].lower() or alias in g['home_name'].lower()):
            return True, g
    return False, None


def game_cache_path(game_data):
    """Generate cache filename from game data (same format as main.py for API games)."""
    game_id = game_data.get('game_id', '')
    return CACHE_DIR / f"{game_id}.json"


def main():
    parser = argparse.ArgumentParser(description='Add a game via MLB API')
    parser.add_argument('--date', type=str, help='Game date (YYYY-MM-DD)')
    parser.add_argument('--teams', nargs='*', help='Team codes (e.g., PHI SF)')
    parser.add_argument('--gamepk', type=int, help='MLB game PK (direct)')
    parser.add_argument('--verbose', '-v', action='store_true')
    parser.add_argument('--force', action='store_true', help='Overwrite existing cache')
    args = parser.parse_args()

    if not args.date and not args.gamepk:
        parser.error("Provide --date or --gamepk")

    session = create_retry_session()
    game_pk = args.gamepk

    if not game_pk:
        # Look up game by date (+ optional team filter)
        games = fetch_schedule(session, args.date)
        if not games:
            print(f"No games found on {args.date}")
            return

        if args.teams:
            # Filter to matching games
            matched = []
            for team_code in args.teams:
                for g in games:
                    found, _ = match_team(team_code, [g])
                    if found and g not in matched:
                        matched.append(g)

            # Find games where both teams match (if 2 teams given)
            if len(args.teams) >= 2:
                both = []
                for g in matched:
                    t1, _ = match_team(args.teams[0], [g])
                    t2, _ = match_team(args.teams[1], [g])
                    if t1 and t2:
                        both.append(g)
                if both:
                    matched = both

            if len(matched) == 1:
                game_pk = matched[0]['gamePk']
                g = matched[0]
                print(f"Found: {g['away_name']} @ {g['home_name']} (pk={game_pk})")
            elif len(matched) > 1:
                print(f"Multiple matches on {args.date}:")
                for i, g in enumerate(matched, 1):
                    print(f"  {i}. {g['away_name']} @ {g['home_name']} [{g['status']}] (pk={g['gamePk']})")
                try:
                    choice = int(input("Select game number: ")) - 1
                    game_pk = matched[choice]['gamePk']
                except (ValueError, IndexError):
                    print("Invalid selection")
                    return
            else:
                print(f"No matching games on {args.date} for teams: {args.teams}")
                print(f"\nAll games on {args.date}:")
                for g in games:
                    print(f"  {g['away_abbr']} @ {g['home_abbr']} - {g['away_name']} @ {g['home_name']} [{g['status']}] (pk={g['gamePk']})")
                return
        else:
            # No team specified — show all games and let user pick
            print(f"Games on {args.date}:")
            for i, g in enumerate(games, 1):
                gtype = f" [{g['gameType']}]" if g['gameType'] != 'R' else ''
                print(f"  {i}. {g['away_name']} @ {g['home_name']}{gtype} - {g['venue']} [{g['status']}]")
            if len(games) == 1:
                game_pk = games[0]['gamePk']
                print(f"\nOnly one game — using pk={game_pk}")
            else:
                try:
                    choice = int(input("\nSelect game number: ")) - 1
                    game_pk = games[choice]['gamePk']
                except (ValueError, IndexError):
                    print("Invalid selection")
                    return

    # Check if already cached
    # We need to parse first to get the game_id for cache path, but check by gamePk first
    existing = None
    for f in CACHE_DIR.glob('*.json'):
        if f.name.startswith(('career', 'player_bios')):
            continue
        try:
            d = json.load(open(f))
            if d.get('mlb_game_pk') == game_pk:
                existing = f
                break
        except:
            continue

    if existing and not args.force:
        print(f"Game already cached: {existing.name}")
        print(f"Use --force to overwrite")
        return

    # Parse the game
    print(f"\nFetching game {game_pk} from MLB API...")
    game_data = parse_mlb_game(game_pk, verbose=True)

    if not game_data:
        print("Failed to parse game")
        return

    game_id = game_data.get('game_id', '')
    basic = game_data.get('basic_info', {})
    print(f"\n  Game ID: {game_id}")
    print(f"  {basic.get('away_team')} @ {basic.get('home_team')}")
    print(f"  {basic.get('date')} at {basic.get('venue')}")
    print(f"  Score: {basic.get('away_score')} - {basic.get('home_score')}")

    # Save to cache
    cache_path = CACHE_DIR / f"{game_id}.json"
    temp = cache_path.with_suffix('.tmp')
    with open(temp, 'w') as f:
        json.dump(game_data, f, indent=2)
    temp.replace(cache_path)

    print(f"\n  Saved to: {cache_path}")
    print(f"\nRun 'python3 -m baseball_processor' to process this game into the website.")


if __name__ == '__main__':
    main()
