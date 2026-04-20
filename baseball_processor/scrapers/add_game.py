"""
Add a game to the processor via MLB API.

Interactive mode (default):
    python3 -m baseball_processor.scrapers.add_game

Direct mode:
    python3 -m baseball_processor.scrapers.add_game --date 2026-04-07 --teams PHI SF
    python3 -m baseball_processor.scrapers.add_game --gamepk 823235
"""

import argparse
import json
import subprocess
import sys
from datetime import datetime, timedelta
from pathlib import Path

from ..parsers.mlb_api_parser import parse_mlb_game
from ..utils.http import create_retry_session, get_with_retry

CACHE_DIR = Path(__file__).parent.parent.parent / 'cache'
PROJECT_DIR = Path(__file__).parent.parent.parent
MLB_API_BASE = 'https://statsapi.mlb.com/api/v1'

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
    """Fetch MLB schedule for a given date."""
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


def is_game_cached(game_pk):
    """Check if a game is already in the cache."""
    skip = ('career', 'player_bios')
    for f in CACHE_DIR.glob('*.json'):
        if f.name.startswith(skip):
            continue
        try:
            d = json.load(open(f))
            if d.get('mlb_game_pk') == game_pk:
                return f.name
        except:
            continue
    return None


def fetch_and_save_game(game_pk, force=False):
    """Fetch a game from the API and save to cache. Returns game_data or None."""
    cached = is_game_cached(game_pk)
    if cached and not force:
        print(f"  Already cached: {cached}")
        return None

    print(f"  Fetching game {game_pk} from MLB API...")
    game_data = parse_mlb_game(game_pk, verbose=True)
    if not game_data:
        print("  Failed to parse game")
        return None

    game_id = game_data.get('game_id', '')
    basic = game_data.get('basic_info', {})

    cache_path = CACHE_DIR / f"{game_id}.json"
    temp = cache_path.with_suffix('.tmp')
    with open(temp, 'w') as f:
        json.dump(game_data, f, indent=2)
    temp.replace(cache_path)

    print(f"  {basic.get('away_team')} @ {basic.get('home_team')}")
    print(f"  {basic.get('date')} at {basic.get('venue')}")
    print(f"  Score: {basic.get('away_score')} - {basic.get('home_score')}")
    print(f"  Saved to cache")

    # Run enrichment pipeline
    from ..main import _fetch_missing_bios_for_game, _update_gamelogs_for_game
    try:
        _fetch_missing_bios_for_game(game_data)
    except Exception as e:
        print(f"  ⚠️ Bio fetch skipped: {e}")

    game_type = basic.get('game_type', 'regular')
    if game_type in ('regular', 'postseason'):
        # Use MLB API for career firsts (instant, no BREF rate limits)
        try:
            from .career_firsts_scraper import update_career_firsts_from_api
            update_career_firsts_from_api(game_data, verbose=True)
        except Exception as e:
            print(f"  ⚠️ Career firsts (API) skipped: {e}")
        try:
            _update_gamelogs_for_game(cache_path)
        except Exception as e:
            print(f"  ⚠️ Gamelog update skipped: {e}")

    return game_data


def run_processor(website_only=True):
    """Run the main processor to rebuild the website."""
    print("\nProcessing and deploying website...")
    cmd = ['python3', '-m', 'baseball_processor']
    if website_only:
        cmd.append('--website-only')
    result = subprocess.run(cmd, cwd=str(PROJECT_DIR))
    return result.returncode == 0


def display_games(games, date_str):
    """Display games for a date, marking cached ones."""
    print(f"\n  Games on {date_str}:")
    for i, g in enumerate(games, 1):
        cached = is_game_cached(g['gamePk'])
        cache_mark = ' [cached]' if cached else ''
        gtype = f" [{g['gameType']}]" if g['gameType'] != 'R' else ''
        status = g['status']
        if status == 'Final':
            print(f"  {i}. {g['away_name']} @ {g['home_name']} - {g['venue']}{gtype}{cache_mark}")
        else:
            print(f"  {i}. {g['away_name']} @ {g['home_name']} - {g['venue']} [{status}]{gtype}{cache_mark}")
    return games


def interactive_mode():
    """Interactive game selection with date navigation."""
    session = create_retry_session()
    current_date = datetime.now()  # Default to today

    print("Add Game — Interactive Mode")
    print("Commands: number to select, 'p' previous day, 'n' next day, 'd YYYY-MM-DD' jump to date, 'q' quit\n")

    while True:
        date_str = current_date.strftime('%Y-%m-%d')
        games = fetch_schedule(session, date_str)

        if not games:
            print(f"  No games on {date_str}")
        else:
            display_games(games, date_str)

        try:
            choice = input(f"\n  [{date_str}] > ").strip()
        except (EOFError, KeyboardInterrupt):
            print()
            return

        if not choice or choice.lower() == 'q':
            return
        elif choice.lower() == 'p':
            current_date -= timedelta(days=1)
        elif choice.lower() == 'n':
            current_date += timedelta(days=1)
        elif choice.lower().startswith('d '):
            try:
                current_date = datetime.strptime(choice[2:].strip(), '%Y-%m-%d')
            except ValueError:
                print("  Invalid date format. Use YYYY-MM-DD")
        elif choice.isdigit():
            idx = int(choice) - 1
            if 0 <= idx < len(games):
                g = games[idx]
                print(f"\n  Selected: {g['away_name']} @ {g['home_name']}")
                game_data = fetch_and_save_game(g['gamePk'])
                if game_data:
                    process = input("\n  Process and deploy? (Y/n) ").strip().lower()
                    if process != 'n':
                        run_processor()
                    print()
            else:
                print("  Invalid selection")
        else:
            print("  Unknown command")


def main():
    parser = argparse.ArgumentParser(description='Add a game via MLB API')
    parser.add_argument('--date', type=str, help='Game date (YYYY-MM-DD)')
    parser.add_argument('--teams', nargs='*', help='Team codes (e.g., PHI SF)')
    parser.add_argument('--gamepk', type=int, help='MLB game PK (direct)')
    parser.add_argument('--force', action='store_true', help='Overwrite existing cache')
    parser.add_argument('--no-process', action='store_true', help='Skip processing after adding')
    args = parser.parse_args()

    # Interactive mode if no args given
    if not args.date and not args.gamepk:
        interactive_mode()
        return

    session = create_retry_session()
    game_pk = args.gamepk

    if not game_pk:
        games = fetch_schedule(session, args.date)
        if not games:
            print(f"No games found on {args.date}")
            return

        if args.teams:
            matched = []
            for team_code in args.teams:
                q = team_code.upper()
                alias = TEAM_ALIASES.get(q, q).lower()
                for g in games:
                    if (q == g['away_abbr'].upper() or q == g['home_abbr'].upper()
                            or alias in g['away_name'].lower() or alias in g['home_name'].lower()):
                        if g not in matched:
                            matched.append(g)

            if len(args.teams) >= 2:
                both = [g for g in matched
                        if any(args.teams[0].upper() in (g['away_abbr'].upper(), g['home_abbr'].upper()) or TEAM_ALIASES.get(args.teams[0].upper(), '').lower() in g['away_name'].lower() + g['home_name'].lower() for _ in [1])
                        and any(args.teams[1].upper() in (g['away_abbr'].upper(), g['home_abbr'].upper()) or TEAM_ALIASES.get(args.teams[1].upper(), '').lower() in g['away_name'].lower() + g['home_name'].lower() for _ in [1])]
                if both:
                    matched = both

            if len(matched) == 1:
                game_pk = matched[0]['gamePk']
                print(f"Found: {matched[0]['away_name']} @ {matched[0]['home_name']}")
            elif len(matched) > 1:
                print(f"Multiple matches:")
                for i, g in enumerate(matched, 1):
                    print(f"  {i}. {g['away_name']} @ {g['home_name']}")
                try:
                    game_pk = matched[int(input("Select: ")) - 1]['gamePk']
                except (ValueError, IndexError):
                    return
            else:
                print(f"No matching games for {args.teams}")
                return
        else:
            display_games(games, args.date)
            if len(games) == 1:
                game_pk = games[0]['gamePk']
            else:
                try:
                    game_pk = games[int(input("\nSelect: ")) - 1]['gamePk']
                except (ValueError, IndexError):
                    return

    game_data = fetch_and_save_game(game_pk, force=args.force)
    if game_data and not args.no_process:
        run_processor()


if __name__ == '__main__':
    main()
