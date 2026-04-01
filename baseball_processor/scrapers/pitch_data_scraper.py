"""
Pitch Data Scraper
==================
Enriches cached BREF game data with pitch-level data from the MLB Stats API.
Fetches velocity, pitch types, and spin rates for each pitcher.

Usage:
    python3 -m baseball_processor.scrapers.pitch_data_scraper
    python3 -m baseball_processor.scrapers.pitch_data_scraper --delay 1.0
    python3 -m baseball_processor.scrapers.pitch_data_scraper --dry-run
    python3 -m baseball_processor.scrapers.pitch_data_scraper --force
"""

import argparse
import json
import time
from pathlib import Path

from ..parsers.mlb_api_parser import TEAM_ID_TO_CODE, parse_pitch_data, parse_hit_data
from ..utils.helpers import normalize_name as _normalize_name
from ..utils.http import create_retry_session, get_with_retry

# Reverse mapping: BREF team code -> MLB API team ID
CODE_TO_MLB_ID = {v: k for k, v in TEAM_ID_TO_CODE.items()}
CODE_TO_MLB_ID['OAK'] = 133  # Historical Oakland code (ATH is the current one)

CACHE_DIR = Path(__file__).parent.parent.parent / 'cache'
MLB_API_BASE = "https://statsapi.mlb.com/api/v1"


def find_game_pk(schedule_games, home_code, away_code, doubleheader='0'):
    """Find gamePk from a pre-fetched schedule for a specific matchup."""
    home_id = CODE_TO_MLB_ID.get(home_code)
    away_id = CODE_TO_MLB_ID.get(away_code)
    if not home_id or not away_id:
        return None

    for sg in schedule_games:
        sg_home = sg.get('teams', {}).get('home', {}).get('team', {}).get('id')
        sg_away = sg.get('teams', {}).get('away', {}).get('team', {}).get('id')
        if sg_home == home_id and sg_away == away_id:
            if doubleheader in ('1', '2'):
                if sg.get('gameNumber') == int(doubleheader):
                    return sg['gamePk']
            else:
                return sg['gamePk']
    return None



def _remap_hit_data_keys(hit_data, game):
    """Replace mlb_* keys with BREF IDs by matching batter names."""
    name_to_bref = {}
    for side in ('away', 'home'):
        for p in game.get('batting', {}).get(side, []):
            name = _normalize_name(p.get('name', ''))
            pid = p.get('player_id', '')
            if name and pid and not pid.startswith('mlb_'):
                name_to_bref[name] = pid

    remapped = {}
    for key, hdata in hit_data.items():
        norm_name = _normalize_name(hdata.get('name', ''))
        if key.startswith('mlb_') and norm_name in name_to_bref:
            new_key = name_to_bref[norm_name]
            hdata['player_id'] = new_key
            remapped[new_key] = hdata
        else:
            remapped[key] = hdata
    return remapped


def remap_pitch_data_keys(pitch_data, game):
    """Replace mlb_* keys with BREF IDs by matching pitcher names."""
    name_to_bref = {}
    for side in ('away', 'home'):
        for p in game.get('pitching', {}).get(side, []):
            name = _normalize_name(p.get('name', ''))
            pid = p.get('player_id', '')
            if name and pid and not pid.startswith('mlb_'):
                name_to_bref[name] = pid

    remapped = {}
    for key, pdata in pitch_data.items():
        pitcher_name = _normalize_name(pdata.get('name', ''))
        if key.startswith('mlb_') and pitcher_name in name_to_bref:
            new_key = name_to_bref[pitcher_name]
            pdata['player_id'] = new_key
            remapped[new_key] = pdata
        else:
            remapped[key] = pdata
    return remapped


def main():
    parser = argparse.ArgumentParser(description='Enrich cached games with MLB API pitch data')
    parser.add_argument('--delay', type=float, default=0.5, help='Delay between API requests (seconds)')
    parser.add_argument('--dry-run', action='store_true', help='Preview without fetching')
    parser.add_argument('--force', action='store_true', help='Re-fetch even if pitch_data exists')
    parser.add_argument('--verbose', '-v', action='store_true', help='Verbose output')
    args = parser.parse_args()

    session = create_retry_session()

    # Collect all games, grouped by date
    games_by_date = {}
    skip_patterns = ['career_firsts', 'career_gamelogs']

    for cache_file in sorted(CACHE_DIR.glob('*.json')):
        if any(p in cache_file.name for p in skip_patterns):
            continue
        try:
            with open(cache_file, 'r') as f:
                game = json.load(f)
        except (json.JSONDecodeError, IOError):
            continue

        # Skip MLB API games (already have pitch data)
        source = game.get('source') or game.get('basic_info', {}).get('source', 'bref')
        if source == 'mlb':
            continue

        # Skip if already has pitch_data
        if not args.force and game.get('pitch_data'):
            continue

        basic_info = game.get('basic_info', {})
        date = basic_info.get('date_yyyymmdd', '')
        if not date or len(date) != 8:
            continue

        games_by_date.setdefault(date, []).append((cache_file, game))

    total_games = sum(len(v) for v in games_by_date.values())
    print(f"Found {total_games} games across {len(games_by_date)} dates to process")

    if total_games == 0:
        print("Nothing to do. Use --force to re-fetch existing pitch data.")
        return

    processed = 0
    enriched = 0
    failed = 0
    no_match = 0
    schedule_cache = {}

    for date in sorted(games_by_date):
        formatted_date = f"{date[:4]}-{date[4:6]}-{date[6:8]}"

        # Fetch schedule for this date (cached per date)
        if date not in schedule_cache:
            if not args.dry_run:
                schedule_url = f"{MLB_API_BASE}/schedule?date={formatted_date}&sportId=1"
                try:
                    resp = get_with_retry(session, schedule_url, timeout=15)
                    if resp.status_code == 200:
                        dates = resp.json().get('dates', [])
                        schedule_cache[date] = dates[0].get('games', []) if dates else []
                    else:
                        print(f"  Failed schedule fetch for {formatted_date}: {resp.status_code}")
                        schedule_cache[date] = []
                except Exception as e:
                    print(f"  Schedule error for {formatted_date}: {e}")
                    schedule_cache[date] = []
                time.sleep(args.delay)
            else:
                schedule_cache[date] = []

        schedule_games = schedule_cache[date]

        for cache_file, game in games_by_date[date]:
            processed += 1
            basic_info = game['basic_info']
            home_code = basic_info.get('home_team_code', '')
            away_code = basic_info.get('away_team_code', '')
            dh = game.get('doubleheader', '0')
            game_id = game.get('game_id', '?')

            # Skip non-MLB teams
            if home_code not in CODE_TO_MLB_ID or away_code not in CODE_TO_MLB_ID:
                if args.verbose:
                    print(f"  [{processed}/{total_games}] Skipping {game_id}: unknown team {home_code} or {away_code}")
                continue

            if args.dry_run:
                game_pk = find_game_pk(schedule_games, home_code, away_code, dh) if schedule_games else '?'
                print(f"  [{processed}/{total_games}] {away_code}@{home_code} {formatted_date} -> gamePk={game_pk}")
                continue

            game_pk = find_game_pk(schedule_games, home_code, away_code, dh)
            if not game_pk:
                no_match += 1
                if args.verbose:
                    print(f"  [{processed}/{total_games}] No match: {away_code}@{home_code} {formatted_date}")
                continue

            # Fetch live feed
            try:
                feed_url = f"https://statsapi.mlb.com/api/v1.1/game/{game_pk}/feed/live"
                feed_resp = get_with_retry(session, feed_url, timeout=30)
                feed_resp.raise_for_status()
                feed_data = feed_resp.json()
                time.sleep(args.delay)

                # Extract pitch data (pass empty bref_id_map, remap after)
                pitch_data = parse_pitch_data(feed_data, {})

                # Extract hit data too
                hit_data = parse_hit_data(feed_data, {})
                if hit_data:
                    hit_data = _remap_hit_data_keys(hit_data, game)
                    game['hit_data'] = hit_data

                # ABS challenges
                abs_raw = feed_data.get('gameData', {}).get('absChallenges', {})
                if abs_raw.get('hasChallenges'):
                    abs_challenges = {'away': abs_raw.get('away', {}), 'home': abs_raw.get('home', {}), 'reviews': []}
                    away_id = feed_data.get('gameData', {}).get('teams', {}).get('away', {}).get('id')
                    for play in feed_data.get('liveData', {}).get('plays', {}).get('allPlays', []):
                        matchup = play.get('matchup', {})
                        for ev in play.get('playEvents', []):
                            r = ev.get('reviewDetails')
                            if r:
                                details = ev.get('details', {})
                                call = details.get('call', {})
                                pitch_type = details.get('type', {})
                                count = ev.get('count', {})
                                abs_challenges['reviews'].append({
                                    'overturned': r.get('isOverturned', False),
                                    'batter': matchup.get('batter', {}).get('fullName', ''),
                                    'pitcher': matchup.get('pitcher', {}).get('fullName', ''),
                                    'challengePlayer': r.get('player', {}).get('fullName', ''),
                                    'challengeTeam': 'away' if r.get('challengeTeamId') == away_id else 'home',
                                    'originalCall': call.get('description', ''),
                                    'pitchType': pitch_type.get('description', '') if isinstance(pitch_type, dict) else '',
                                    'count': f"{count.get('balls', 0)}-{count.get('strikes', 0)}",
                                    'inning': play.get('about', {}).get('inning', 0),
                                    'half': play.get('about', {}).get('halfInning', ''),
                                })
                    game['abs_challenges'] = abs_challenges

                if pitch_data:
                    # Remap mlb_* keys to BREF IDs
                    pitch_data = remap_pitch_data_keys(pitch_data, game)
                    game['pitch_data'] = pitch_data

                    # Also grab umpires if missing
                    if not game.get('umpires'):
                        from ..parsers.mlb_api_parser import parse_umpires
                        box_url = f"https://statsapi.mlb.com/api/v1/game/{game_pk}/boxscore"
                        box_resp = get_with_retry(session, box_url, timeout=15)
                        if box_resp.status_code == 200:
                            game['umpires'] = parse_umpires(box_resp.json())
                        time.sleep(args.delay)

                    with open(cache_file, 'w') as f:
                        json.dump(game, f, indent=2)
                    enriched += 1
                    pitchers = len(pitch_data)
                    max_velo = max((pd.get('maxSpeed', 0) or 0 for pd in pitch_data.values()), default=0)
                    print(f"  [{processed}/{total_games}] {game_id}: {pitchers} pitchers, max velo {max_velo} mph")
                else:
                    if args.verbose:
                        print(f"  [{processed}/{total_games}] {game_id}: no pitch data available")
            except Exception as e:
                failed += 1
                print(f"  [{processed}/{total_games}] {game_id}: ERROR: {e}")

    print(f"\nDone! Enriched {enriched}/{total_games} games ({failed} errors, {no_match} no match)")


if __name__ == '__main__':
    main()
