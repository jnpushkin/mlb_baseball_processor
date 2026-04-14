"""
Scrape career game logs from MLB API to compute per-season and career highs.

Usage:
    python3 -m baseball_processor.scrapers.career_highs_scraper                # Scrape all players
    python3 -m baseball_processor.scrapers.career_highs_scraper --player adamewi01
    python3 -m baseball_processor.scrapers.career_highs_scraper --refresh      # Current season only
    python3 -m baseball_processor.scrapers.career_highs_scraper --verbose
"""

import argparse
import csv
import json
import time
from datetime import datetime
from pathlib import Path

from ..utils.http import create_retry_session, get_with_retry

CACHE_DIR = Path(__file__).parent.parent.parent / 'cache'
CACHE_FILE = CACHE_DIR / 'career_highs.json'
REGISTER_DIR = Path(__file__).parent.parent.parent / 'register-master' / 'data'
MLB_API_BASE = 'https://statsapi.mlb.com/api/v1'

HITTING_STATS = ['hits', 'homeRuns', 'rbi', 'runs', 'baseOnBalls', 'stolenBases',
                 'doubles', 'triples', 'totalBases', 'strikeOuts']
PITCHING_STATS = ['strikeOuts', 'inningsPitched', 'hits', 'earnedRuns',
                  'baseOnBalls', 'homeRuns']

# Map API stat names to short display names
STAT_DISPLAY = {
    'hits': 'H', 'homeRuns': 'HR', 'rbi': 'RBI', 'runs': 'R',
    'baseOnBalls': 'BB', 'stolenBases': 'SB', 'doubles': '2B',
    'triples': '3B', 'totalBases': 'TB', 'strikeOuts': 'K',
    'inningsPitched': 'IP', 'earnedRuns': 'ER',
}

# Career milestone thresholds (matching career_firsts_scraper.py)
BATTING_MILESTONES = {
    'hits': sorted(set([10, 25, 50] + list(range(100, 4100, 100)))),
    'homeRuns': sorted(set([10, 25, 50, 75] + list(range(100, 900, 100)))),
    'rbi': sorted(set([10, 25, 50] + list(range(100, 2100, 100)))),
    'doubles': sorted(set([10, 25, 50] + list(range(100, 800, 100)))),
    'triples': sorted(set([10, 25, 50, 75] + list(range(100, 300, 100)))),
    'stolenBases': sorted(set([10, 25, 50] + list(range(100, 900, 100)))),
    'baseOnBalls': sorted(set([10, 25, 50] + list(range(100, 2600, 100)))),
    'runs': sorted(set([10, 25, 50] + list(range(100, 2400, 100)))),
    'totalBases': sorted(set([10, 25, 50, 100, 250] + list(range(500, 6500, 500)))),
    'gamesPlayed': sorted(set([10, 25, 50, 100, 250] + list(range(500, 3500, 500)))),
}
PITCHING_MILESTONES = {
    'wins': sorted(set([10, 25, 50, 75] + list(range(100, 400, 100)))),
    'saves': sorted(set([10, 25, 50] + list(range(100, 700, 100)))),
    'strikeOuts': sorted(set([10, 25, 50, 100, 250] + list(range(500, 4000, 500)))),
    'gamesPitched': sorted(set([10, 25, 50, 100, 250] + list(range(500, 1500, 500)))),
    'gamesStarted': sorted(set([10, 25, 50] + list(range(100, 600, 100)))),
    'completeGames': sorted(set([10, 25, 50, 75, 100])),
    'shutouts': sorted(set([10, 25, 50, 75, 100])),
}
# IP milestones need special handling (stored as "123.1" format)
PITCHING_IP_MILESTONES = sorted(set([10, 25, 50, 100, 250] + list(range(500, 4000, 500))))

MILESTONE_DISPLAY = {
    'hits': 'Hit', 'homeRuns': 'Home Run', 'rbi': 'RBI', 'doubles': 'Double',
    'triples': 'Triple', 'stolenBases': 'Stolen Base', 'baseOnBalls': 'Walk',
    'runs': 'Run Scored', 'totalBases': 'Total Base', 'gamesPlayed': 'Game',
    'wins': 'Win', 'saves': 'Save', 'strikeOuts': 'Strikeout',
    'inningsPitched': 'Inning Pitched', 'gamesPitched': 'Game Pitched',
    'gamesStarted': 'Start', 'completeGames': 'Complete Game', 'shutouts': 'Shutout',
}


def load_bref_to_mlb_map():
    """Build BREF ID -> MLB API ID mapping from Chadwick Register."""
    mapping = {}
    if not REGISTER_DIR.exists():
        print("Warning: Chadwick Register not found at", REGISTER_DIR)
        return mapping

    for csv_file in REGISTER_DIR.glob('people-*.csv'):
        try:
            with open(csv_file, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    mlb_id = row.get('key_mlbam', '').strip()
                    bref_id = row.get('key_bbref', '').strip()
                    bref_minors = row.get('key_bbref_minors', '').strip()
                    if mlb_id:
                        try:
                            mlb_int = int(mlb_id)
                            if bref_id:
                                mapping[bref_id] = mlb_int
                            if bref_minors:
                                mapping[bref_minors] = mlb_int
                        except ValueError:
                            pass
        except (IOError, csv.Error):
            continue
    return mapping


def load_cache():
    """Load existing career highs cache."""
    if CACHE_FILE.exists():
        try:
            return json.load(open(CACHE_FILE))
        except (json.JSONDecodeError, IOError):
            pass
    return {}


def save_cache(cache):
    """Save career highs cache atomically."""
    temp = CACHE_FILE.with_suffix('.tmp')
    with open(temp, 'w') as f:
        json.dump(cache, f, indent=2)
    temp.replace(CACHE_FILE)


def get_player_seasons(session, mlb_id, group='hitting'):
    """Get list of MLB seasons for a player via yearByYear."""
    url = f'{MLB_API_BASE}/people/{mlb_id}/stats?stats=yearByYear&group={group}'
    resp = get_with_retry(session, url, timeout=30)
    if resp.status_code != 200:
        return []
    data = resp.json()
    stats = data.get('stats', [])
    if not stats:
        return []
    # Get unique seasons (some appear multiple times for trades)
    seasons = sorted(set(int(s['season']) for s in stats[0].get('splits', [])
                         if s.get('sport', {}).get('abbreviation') == 'MLB'))
    return seasons


def fetch_season_highs(session, mlb_id, season, group='hitting'):
    """Fetch game log for one season, return max of each tracked stat."""
    url = f'{MLB_API_BASE}/people/{mlb_id}/stats?stats=gameLog&group={group}&season={season}'
    resp = get_with_retry(session, url, timeout=30)
    if resp.status_code != 200:
        return None
    data = resp.json()
    stats = data.get('stats', [])
    if not stats:
        return None
    splits = stats[0].get('splits', [])
    if not splits:
        return {}

    stat_keys = HITTING_STATS if group == 'hitting' else PITCHING_STATS
    highs = {}
    for key in stat_keys:
        values = []
        for split in splits:
            val = split.get('stat', {}).get(key)
            if val is not None:
                if key == 'inningsPitched':
                    # Convert "6.2" -> 6.67 for comparison, but store as string
                    try:
                        parts = str(val).split('.')
                        numeric = int(parts[0]) + (int(parts[1]) / 3 if len(parts) > 1 else 0)
                        values.append((numeric, str(val)))
                    except (ValueError, IndexError):
                        pass
                else:
                    values.append(int(val))

        if values:
            if key == 'inningsPitched':
                best = max(values, key=lambda x: x[0])
                highs[key] = best[1]  # Store display string
            else:
                highs[key] = max(values)

    return highs


def fetch_season_grand_slams(session, mlb_id, season):
    """Fetch playLog for one season, return list of grand slam events."""
    url = f'{MLB_API_BASE}/people/{mlb_id}/stats?stats=playLog&group=hitting&season={season}'
    resp = get_with_retry(session, url, timeout=30)
    if resp.status_code != 200:
        return []
    data = resp.json()
    stats = data.get('stats', [])
    if not stats:
        return []
    splits = stats[0].get('splits', [])

    grand_slams = []
    for s in splits:
        play = s.get('stat', {}).get('play', {})
        details = play.get('details', {})
        count = play.get('count', {})
        if (details.get('event') == 'home_run'
                and count.get('runnerOn1b') and count.get('runnerOn2b') and count.get('runnerOn3b')):
            grand_slams.append({
                'date': s.get('date', ''),
                'pitcher': s.get('pitcher', {}).get('fullName', ''),
                'opponent': s.get('opponent', {}).get('name', ''),
            })
    return grand_slams


def parse_ip_to_outs(ip_str):
    """Convert IP string like '6.2' to total outs (20)."""
    try:
        parts = str(ip_str).split('.')
        innings = int(parts[0])
        partial = int(parts[1]) if len(parts) > 1 else 0
        return innings * 3 + partial
    except (ValueError, IndexError):
        return 0


def fetch_career_milestones(session, mlb_id, seasons, group='hitting'):
    """Fetch game logs for all seasons and compute career milestone dates.

    Returns dict of milestone events: { "Hit #100": {"date": "2020-05-15", "game": "..."}, ... }
    """
    milestones_map = BATTING_MILESTONES if group == 'hitting' else PITCHING_MILESTONES
    ip_milestones = PITCHING_IP_MILESTONES if group == 'pitching' else []

    # Running career totals
    totals = {stat: 0 for stat in milestones_map}
    ip_total_outs = 0  # Track IP as outs for accurate counting
    reached = {stat: set() for stat in milestones_map}
    ip_reached = set()

    milestones = []

    for season in sorted(seasons):
        url = f'{MLB_API_BASE}/people/{mlb_id}/stats?stats=gameLog&group={group}&season={season}'
        resp = get_with_retry(session, url, timeout=30)
        if resp.status_code != 200:
            continue
        data = resp.json()
        stats = data.get('stats', [])
        if not stats:
            continue
        splits = stats[0].get('splits', [])

        for split in splits:
            stat = split.get('stat', {})
            date = split.get('date', '')
            opponent = split.get('opponent', {}).get('name', '')

            # Accumulate totals and check thresholds
            for stat_key, thresholds in milestones_map.items():
                val = stat.get(stat_key)
                if val is None:
                    continue
                val = int(val)
                prev = totals[stat_key]
                totals[stat_key] = prev + val

                for t in thresholds:
                    if t > totals[stat_key]:
                        break  # Thresholds are sorted, no need to check higher
                    if t not in reached[stat_key] and prev < t <= totals[stat_key]:
                        reached[stat_key].add(t)
                        display = MILESTONE_DISPLAY.get(stat_key, stat_key)
                        milestones.append({
                            'milestone': f'{display} #{t}',
                            'stat': stat_key,
                            'threshold': t,
                            'date': date,
                            'opponent': opponent,
                            'career_total': totals[stat_key],
                        })

            # IP milestones (special: convert to outs for counting)
            if group == 'pitching' and ip_milestones:
                ip_val = stat.get('inningsPitched')
                if ip_val is not None:
                    game_outs = parse_ip_to_outs(ip_val)
                    prev_outs = ip_total_outs
                    ip_total_outs += game_outs
                    prev_ip = prev_outs / 3
                    curr_ip = ip_total_outs / 3

                    for t in ip_milestones:
                        if t > curr_ip:
                            break
                        if t not in ip_reached and prev_ip < t <= curr_ip:
                            ip_reached.add(t)
                            milestones.append({
                                'milestone': f'Inning Pitched #{t}',
                                'stat': 'inningsPitched',
                                'threshold': t,
                                'date': date,
                                'opponent': opponent,
                                'career_total': round(curr_ip, 1),
                            })

    return milestones, {k: v for k, v in totals.items() if v > 0}


def compute_career_highs(season_highs, group='hitting'):
    """Compute career highs from all season highs."""
    stat_keys = HITTING_STATS if group == 'hitting' else PITCHING_STATS
    career = {}
    for key in stat_keys:
        values = []
        for season_data in season_highs.values():
            if not season_data:
                continue
            val = season_data.get(key)
            if val is not None:
                if key == 'inningsPitched':
                    parts = str(val).split('.')
                    numeric = int(parts[0]) + (int(parts[1]) / 3 if len(parts) > 1 else 0)
                    values.append((numeric, str(val)))
                else:
                    values.append(val)

        if values:
            if key == 'inningsPitched':
                best = max(values, key=lambda x: x[0])
                career[key] = best[1]
            else:
                career[key] = max(values)
    return career


def scrape_player(session, bref_id, mlb_id, name, cache, refresh=False, verbose=False):
    """Scrape career highs for one player. Returns True if data was fetched."""
    current_year = datetime.now().year
    existing = cache.get(bref_id, {})
    existing_seasons = existing.get('season_highs', {})
    last_scraped = existing.get('last_scraped_season', 0)

    # Determine which groups to scrape
    is_pitcher = existing.get('is_pitcher', None)

    fetched_any = False

    for group in ['hitting', 'pitching']:
        # Get player's MLB seasons for this group
        seasons = get_player_seasons(session, mlb_id, group)
        if not seasons:
            continue

        group_key = f'season_highs_{group}' if group == 'pitching' else 'season_highs'

        existing_group = existing.get(group_key, {})

        if group == 'pitching':
            is_pitcher = True

        seasons_to_fetch = []
        for s in seasons:
            s_str = str(s)
            if refresh:
                # Only fetch current season
                if s == current_year:
                    seasons_to_fetch.append(s)
            elif s_str not in existing_group:
                seasons_to_fetch.append(s)
            elif s == current_year and last_scraped < current_year:
                # Re-fetch current season if we haven't this year
                seasons_to_fetch.append(s)

        if not seasons_to_fetch:
            continue

        if verbose:
            print(f"    {group}: fetching {len(seasons_to_fetch)} season(s): {seasons_to_fetch}")

        for season in seasons_to_fetch:
            highs = fetch_season_highs(session, mlb_id, season, group)
            if highs is not None:
                existing_group[str(season)] = highs
                fetched_any = True

        # Store back
        existing[group_key] = existing_group

        # Recompute career highs for this group
        career_key = f'career_highs_{group}' if group == 'pitching' else 'career_highs'
        existing[career_key] = compute_career_highs(existing_group, group)

    # Grand slams (from playLog, only for hitters)
    existing_gs = existing.get('grand_slams', [])
    existing_gs_seasons = set()
    for gs in existing_gs:
        if gs.get('date'):
            existing_gs_seasons.add(gs['date'][:4])

    # Get hitting seasons (already fetched above or from cache)
    hitting_seasons = get_player_seasons(session, mlb_id, 'hitting') if fetched_any else []
    if not hitting_seasons:
        # Use seasons from existing cache
        hitting_seasons = [int(s) for s in existing.get('season_highs', {}).keys() if s.isdigit()]

    gs_seasons_to_fetch = []
    for s in hitting_seasons:
        s_str = str(s)
        if refresh:
            if s == current_year:
                gs_seasons_to_fetch.append(s)
        elif s_str not in existing_gs_seasons:
            gs_seasons_to_fetch.append(s)
        elif s == current_year:
            gs_seasons_to_fetch.append(s)

    if gs_seasons_to_fetch:
        if verbose:
            print(f"    grand slams: checking {len(gs_seasons_to_fetch)} season(s)")
        # Remove existing GS entries for seasons we're re-fetching
        refetch_years = set(str(s) for s in gs_seasons_to_fetch)
        existing_gs = [gs for gs in existing_gs if gs.get('date', '')[:4] not in refetch_years]
        for season in gs_seasons_to_fetch:
            new_gs = fetch_season_grand_slams(session, mlb_id, season)
            existing_gs.extend(new_gs)
            fetched_any = True
        existing_gs.sort(key=lambda x: x.get('date', ''))
        existing['grand_slams'] = existing_gs
        existing['career_grand_slams'] = len(existing_gs)

    # Career milestones (Hit #100, HR #200, etc.)
    # These require full career game logs processed in order, so we only compute
    # if missing or refresh requested. Uses gameLog (same endpoint as highs).
    needs_milestones = 'career_milestones' not in existing or refresh
    if needs_milestones and hitting_seasons:
        if verbose:
            print(f"    career milestones (hitting): computing from {len(hitting_seasons)} seasons")
        milestones, career_totals = fetch_career_milestones(session, mlb_id, hitting_seasons, 'hitting')
        existing['career_milestones'] = milestones
        existing['career_totals_api'] = {'hitting': career_totals}
        fetched_any = True

    pitching_seasons = [int(s) for s in existing.get('season_highs_pitching', {}).keys() if s.isdigit()]
    if needs_milestones and pitching_seasons:
        if verbose:
            print(f"    career milestones (pitching): computing from {len(pitching_seasons)} seasons")
        milestones, career_totals = fetch_career_milestones(session, mlb_id, pitching_seasons, 'pitching')
        existing.setdefault('career_milestones', []).extend(milestones)
        existing.setdefault('career_totals_api', {})['pitching'] = career_totals
        fetched_any = True

    if fetched_any or bref_id not in cache:
        existing['mlb_id'] = mlb_id
        existing['name'] = name
        existing['last_scraped_season'] = current_year
        existing['scraped_at'] = datetime.now().isoformat()
        if is_pitcher is not None:
            existing['is_pitcher'] = is_pitcher
        cache[bref_id] = existing

    return fetched_any


def main():
    parser = argparse.ArgumentParser(description='Scrape career highs from MLB API game logs')
    parser.add_argument('--player', type=str, metavar='BREF_ID', help='Scrape specific player')
    parser.add_argument('--refresh', action='store_true', help='Only re-scrape current season')
    parser.add_argument('--verbose', '-v', action='store_true', help='Verbose output')
    parser.add_argument('--save-every', type=int, default=50, help='Save cache every N players (default: 50)')
    args = parser.parse_args()

    # Load player list from data.json
    data_file = Path(__file__).parent.parent.parent / 'data.json'
    if not data_file.exists():
        print("Error: data.json not found. Run the processor first.")
        return

    data = json.load(open(data_file))

    # Build unique player set with names
    players = {}
    for pg in data.get('playerGames', []):
        pid = pg.get('playerId')
        if pid and pid not in players:
            players[pid] = pg.get('name', pid)
    for pg in data.get('pitcherGames', []):
        pid = pg.get('playerId')
        if pid and pid not in players:
            players[pid] = pg.get('name', pid)

    if args.player:
        if args.player not in players:
            players = {args.player: args.player}
        else:
            players = {args.player: players[args.player]}

    print(f"Loading Chadwick Register...")
    bref_to_mlb = load_bref_to_mlb_map()
    print(f"  {len(bref_to_mlb)} BREF -> MLB mappings loaded")

    cache = load_cache()
    print(f"Existing cache: {len(cache)} players")

    session = create_retry_session()
    total = len(players)
    scraped = 0
    skipped = 0
    no_mlb_id = 0
    errors = 0

    print(f"\nProcessing {total} players...")

    for i, (bref_id, name) in enumerate(players.items(), 1):
        mlb_id = bref_to_mlb.get(bref_id)
        if not mlb_id:
            no_mlb_id += 1
            if args.verbose:
                print(f"[{i}/{total}] {name} ({bref_id}): no MLB API ID, skipping")
            continue

        # Skip if fully cached and not refreshing
        existing = cache.get(bref_id, {})
        if not args.refresh and not args.player:
            if existing.get('last_scraped_season', 0) >= datetime.now().year:
                skipped += 1
                if args.verbose:
                    print(f"[{i}/{total}] {name}: cached, skipping")
                continue

        if args.verbose or i % 100 == 0 or i == 1:
            print(f"[{i}/{total}] {name} ({bref_id}, mlb={mlb_id})...")

        try:
            fetched = scrape_player(session, bref_id, mlb_id, name, cache,
                                    refresh=args.refresh, verbose=args.verbose)
            if fetched:
                scraped += 1
            else:
                skipped += 1
        except Exception as e:
            errors += 1
            if args.verbose:
                print(f"  Error: {e}")

        # Periodic save
        if i % args.save_every == 0:
            save_cache(cache)
            if not args.verbose:
                print(f"  [{i}/{total}] saved checkpoint ({scraped} scraped, {skipped} skipped, {no_mlb_id} no ID, {errors} errors)")

    save_cache(cache)
    print(f"\nDone! {scraped} scraped, {skipped} skipped, {no_mlb_id} no MLB ID, {errors} errors")
    print(f"Cache: {len(cache)} players saved to {CACHE_FILE}")


if __name__ == '__main__':
    main()
