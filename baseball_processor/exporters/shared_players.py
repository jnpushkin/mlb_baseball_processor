"""
Cross-project player export/import for linking MLB and NCAA processor websites.

Generates a shared_players.json with player IDs, summary stats, and website URLs
that the NCAA processor can read to build cross-reference tabs.
"""

import json
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any, Optional


def generate_shared_export(
    processed_data: Dict[str, Any],
    website_url: str = "https://mlb-passport.surge.sh",
    output_dir: Optional[Path] = None,
) -> Path:
    """
    Generate shared_players.json for cross-project linking.

    Args:
        processed_data: The processed data dict from generate_excel_workbook
        website_url: URL of the generated website
        output_dir: Output directory (default: project data/ dir)

    Returns:
        Path to generated JSON file
    """
    if output_dir is None:
        from ..utils.constants import BASE_DIR
        output_dir = BASE_DIR / 'data'

    output_dir.mkdir(parents=True, exist_ok=True)

    players = []

    # Get player data from raw games
    raw_games = processed_data.get('_raw_games', [])

    player_stats = {}
    for game in raw_games:
        basic_info = game.get('basic_info', {})

        for side in ['away', 'home']:
            team = basic_info.get(f'{side}_team', '')
            for batter in game.get('batting', {}).get(side, []):
                pid = batter.get('player_id', '')
                if not pid:
                    continue
                if pid not in player_stats:
                    player_stats[pid] = {
                        'name': batter.get('name', ''),
                        'bref_id': pid,
                        'teams': set(),
                        'G': 0, 'AB': 0, 'H': 0, 'R': 0, 'RBI': 0,
                        'HR': 0, 'BB': 0, 'SO': 0,
                    }
                player_stats[pid]['teams'].add(team)
                player_stats[pid]['G'] += 1
                for stat in ['AB', 'H', 'R', 'RBI', 'HR', 'BB', 'SO']:
                    try:
                        player_stats[pid][stat] += int(batter.get(stat, 0))
                    except (ValueError, TypeError):
                        pass

            for pitcher in game.get('pitching', {}).get(side, []):
                pid = pitcher.get('player_id', '')
                if not pid:
                    continue
                if pid not in player_stats:
                    player_stats[pid] = {
                        'name': pitcher.get('name', ''),
                        'bref_id': pid,
                        'teams': set(),
                        'G': 0, 'AB': 0, 'H': 0, 'R': 0, 'RBI': 0,
                        'HR': 0, 'BB': 0, 'SO': 0,
                    }
                player_stats[pid]['teams'].add(team)
                # Only count game if not already counted via batting
                player_stats[pid]['G'] = max(player_stats[pid]['G'], 1)

    for pid, stats in player_stats.items():
        ab = stats['AB']
        h = stats['H']
        avg = f".{int((h / ab) * 1000):03d}" if ab > 0 else '.000'

        players.append({
            'name': stats['name'],
            'bref_id': stats['bref_id'],
            'mlb_api_id': None,
            'levels': ['MLB'],
            'mlb_teams': sorted(stats['teams']),
            'mlb_stats': {
                'G': stats['G'], 'AB': ab, 'H': h, 'R': stats['R'],
                'RBI': stats['RBI'], 'HR': stats['HR'], 'BB': stats['BB'],
                'SO': stats['SO'], 'AVG': avg,
            },
        })

    players.sort(key=lambda p: p['mlb_stats'].get('G', 0), reverse=True)

    export = {
        'processor': 'mlb',
        'generated_at': datetime.now().isoformat(),
        'website_url': website_url,
        'player_count': len(players),
        'players': players,
    }

    output_path = output_dir / 'shared_players.json'
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(export, f, indent=2)

    print(f"Shared player export: {len(players)} players -> {output_path}")
    return output_path


def load_ncaa_processor_export(ncaa_data_dir: Optional[Path] = None) -> Optional[Dict]:
    """
    Load the NCAA processor's shared_players.json.

    Args:
        ncaa_data_dir: Path to NCAA processor's data directory
                      Default: ~/ncaa_baseball_processor/data/

    Returns:
        Parsed export dict, or None if not found
    """
    if ncaa_data_dir is None:
        ncaa_data_dir = Path.home() / 'ncaa_baseball_processor' / 'data'

    export_path = ncaa_data_dir / 'shared_players.json'

    if not export_path.exists():
        alt_path = Path.home() / 'ncaa_baseball_processor' / 'shared_players.json'
        if alt_path.exists():
            export_path = alt_path
        else:
            return None

    try:
        with open(export_path, 'r', encoding='utf-8') as f:
            data = json.load(f)

        if data.get('processor') != 'ncaa':
            return None

        print(f"NCAA processor export loaded: {data.get('player_count', 0)} players")
        return data
    except (json.JSONDecodeError, IOError) as e:
        print(f"Error loading NCAA processor export: {e}")
        return None


def _load_register_mapping() -> Dict[str, str]:
    """
    Load Chadwick Register to map key_bbref_minors -> key_bbref.

    This bridges NCAA bref IDs (minors format like 'kessay000seb')
    to MLB bref IDs (standard format like 'hendegu01').
    """
    from ..utils.constants import REGISTER_DIR
    mapping = {}  # key_bbref_minors -> key_bbref

    for csv_file in sorted(REGISTER_DIR.glob('data/people-*.csv')):
        try:
            import csv
            with open(csv_file, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    minors_id = row.get('key_bbref_minors', '').strip()
                    mlb_id = row.get('key_bbref', '').strip()
                    if minors_id and mlb_id:
                        mapping[minors_id] = mlb_id
        except Exception:
            continue

    return mapping


def build_ncaa_cross_reference(ncaa_export: Optional[Dict] = None) -> Dict[str, Any]:
    """
    Build a cross-reference dict from NCAA export, indexed by MLB bref_id.

    Uses the Chadwick Register to map NCAA minors bref IDs to MLB bref IDs,
    so the MLB processor can match players by their standard player_id.

    Returns:
        Dict mapping MLB bref_id -> {name, website_url, ncaa_stats, ncaa_teams, levels}
    """
    cross_ref = {}

    if not ncaa_export:
        return cross_ref

    # Load register mapping: minors bref_id -> MLB bref_id
    try:
        register_map = _load_register_mapping()
        print(f"      Loaded Chadwick Register: {len(register_map)} minors->MLB mappings")
    except Exception as e:
        print(f"      Warning: Could not load Chadwick Register: {e}")
        register_map = {}

    website_url = ncaa_export.get('website_url', '')

    for player in ncaa_export.get('players', []):
        ncaa_bref_id = player.get('bref_id', '')
        if not ncaa_bref_id:
            continue

        entry = {
            'name': player.get('name', ''),
            'website_url': website_url,
            'ncaa_stats': player.get('ncaa_stats', {}),
            'ncaa_teams': player.get('ncaa_teams', []),
            'pro_stats': player.get('pro_stats', {}),
            'levels': player.get('levels', []),
        }

        # Index by the NCAA bref_id (minors format) as fallback
        cross_ref[ncaa_bref_id] = entry

        # Also index by the MLB bref_id via register mapping
        mlb_bref_id = register_map.get(ncaa_bref_id)
        if mlb_bref_id:
            cross_ref[mlb_bref_id] = entry

    return cross_ref
