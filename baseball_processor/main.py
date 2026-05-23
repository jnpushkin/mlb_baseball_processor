import os
import json
import argparse
import logging
import re
import copy
import pandas as pd
from pathlib import Path
from datetime import datetime, timedelta

from .excel.workbook_generator import generate_excel_workbook
from .parsers.html_parser import parse_baseball_reference_boxscore
from .utils.constants import BASE_DIR, DEFAULT_INPUT_DIR, REFERENCES_DIR, HOF_FILE, CACHE_DIR
from .utils.helpers import load_mlb_debuts
from .utils.globals import UmpireTracker
from .utils.log import info, warn, error, debug, set_verbosity, set_use_emoji, configure_file_logging
from .website import generate_website_from_data
from .reports.quick_stats import generate_quick_stats_report, print_quick_stats_report
from .exporters.csv_exporter import export_all_to_csv, export_raw_games_to_csv

# Surge deployment configuration file
SURGE_CONFIG_FILE = BASE_DIR / '.surge-domain'


def load_surge_domain() -> str | None:
    """Load saved Surge domain from config file."""
    if SURGE_CONFIG_FILE.exists():
        return SURGE_CONFIG_FILE.read_text().strip()
    return None


def save_surge_domain(domain: str):
    """Save Surge domain to config file for future runs."""
    SURGE_CONFIG_FILE.write_text(domain)


def deploy_to_surge(html_path: str, domain: str | None = None) -> bool:
    """
    Deploy the generated HTML website to Surge.

    Args:
        html_path: Path to the HTML file to deploy
        domain: Surge domain (e.g., 'mlb-passport.surge.sh')

    Returns:
        True if deployment succeeded, False otherwise
    """
    import shutil
    import subprocess
    import tempfile

    # Check if surge is installed
    if not shutil.which('surge'):
        warn("❌ Surge is not installed. Install with: npm install -g surge")
        return False

    # Load domain from config if not provided
    if not domain:
        domain = load_surge_domain()

    if not domain:
        warn("❌ No Surge domain specified. Use --surge-domain to set one.")
        warn("   Example: --surge-domain mlb-passport.surge.sh")
        return False

    # Ensure domain ends with .surge.sh if no TLD
    if '.' not in domain:
        domain = f"{domain}.surge.sh"

    # Save domain for future runs
    save_surge_domain(domain)

    info(f"🚀 Deploying to Surge: {domain}")

    # Create temp directory with the HTML file as index.html and data.json
    with tempfile.TemporaryDirectory() as temp_dir:
        # Copy HTML to temp dir as index.html
        temp_html = os.path.join(temp_dir, 'index.html')
        shutil.copy(html_path, temp_html)

        # Copy data.json if it exists alongside the HTML file
        data_json = os.path.join(os.path.dirname(html_path), 'data.json')
        if os.path.exists(data_json):
            shutil.copy(data_json, os.path.join(temp_dir, 'data.json'))

        try:
            # Run surge deployment
            result = subprocess.run(
                ['surge', temp_dir, domain],
                capture_output=True,
                text=True,
                timeout=120
            )

            if result.returncode == 0:
                info(f"✅ Deployed successfully to: https://{domain}")
                return True
            else:
                warn(f"❌ Surge deployment failed: {result.stderr}")
                return False

        except subprocess.TimeoutExpired:
            warn("❌ Surge deployment timed out")
            return False
        except Exception as e:
            warn(f"❌ Surge deployment error: {e}")
            return False


def _configured_surge_domain(args) -> str | None:
    return args.surge_domain or load_surge_domain()


def _should_deploy_to_surge(args, configured_domain: str | None = None) -> bool:
    if args.no_deploy:
        return False
    if configured_domain is None:
        configured_domain = _configured_surge_domain(args)
    return bool(args.deploy or configured_domain)


def _log_surge_deploy_mode(args) -> None:
    if args.excel_only or args.quick_stats:
        return

    configured_domain = _configured_surge_domain(args)
    if args.no_deploy and (args.deploy or configured_domain):
        info("🚫 Surge deploy mode: disabled for this run (--no-deploy)")
    elif args.deploy:
        info("🚀 Surge deploy mode: explicit deploy requested")
    elif configured_domain:
        info(f"🚀 Surge deploy mode: auto-deploy enabled ({configured_domain})")


def _maybe_deploy_to_surge(html_path: str, args) -> bool:
    configured_domain = _configured_surge_domain(args)
    if args.no_deploy:
        if args.deploy or configured_domain:
            info("🚫 Skipping Surge deployment for this run (--no-deploy)")
        return False

    if not _should_deploy_to_surge(args, configured_domain):
        return False

    if not args.deploy and configured_domain:
        info(f"🚀 Auto-deploying to configured Surge domain: {configured_domain}")
    return deploy_to_surge(html_path, configured_domain)


def _print_game_summary(game_data):
    """Print a 'New This Game' summary highlighting notable aspects."""
    bi = game_data.get('basic_info', {})
    game_id = game_data.get('game_id', '')
    highlights = []

    # Pitch superlatives
    pd = game_data.get('pitch_data', {})
    if pd:
        max_velo = max((p.get('maxSpeed', 0) or 0 for p in pd.values()), default=0)
        if max_velo > 0:
            pitcher = next((p['name'] for p in pd.values() if p.get('maxSpeed') == max_velo), '')
            highlights.append(f"Fastest pitch: {max_velo} mph ({pitcher})")

    # Exit velo superlatives
    hd = game_data.get('hit_data', {})
    if hd:
        max_ev = max((h.get('maxExitVelo', 0) or 0 for h in hd.values()), default=0)
        if max_ev > 0:
            batter = next((h['name'] for h in hd.values() if h.get('maxExitVelo') == max_ev), '')
            highlights.append(f"Hardest hit: {max_ev} mph ({batter})")

    # Milestones
    ms = game_data.get('milestone_stats', {})
    for key, events in ms.items():
        if isinstance(events, list) and events:
            for e in events:
                highlights.append(f"Milestone: {e.get('player', '')} — {key.replace('_', ' ').title()}")

    # ABS challenges
    abs_data = game_data.get('abs_challenges', {})
    if abs_data:
        reviews = abs_data.get('reviews', [])
        if reviews:
            for r in reviews:
                result = 'Overturned' if r.get('overturned') else 'Upheld'
                highlights.append(f"ABS Challenge: {result} — {r.get('originalCall', 'call')} ({r.get('batter', '')} vs {r.get('pitcher', '')})")

    if highlights:
        info(f"  📝 New This Game:")
        for h in highlights[:8]:
            info(f"     • {h}")


def _refresh_all_time_leaders_if_stale(max_age_days=7):
    """Refresh all-time leaders from BREF if data is older than max_age_days."""
    import subprocess
    leaders_dir = REFERENCES_DIR / "all_time_leaders"
    if not leaders_dir.exists():
        return

    # Check the newest file's modification time
    newest_mtime = 0
    for f in leaders_dir.glob("*.json"):
        mtime = os.path.getmtime(f)
        if mtime > newest_mtime:
            newest_mtime = mtime

    if newest_mtime == 0:
        return

    age_days = (datetime.now().timestamp() - newest_mtime) / 86400
    if age_days <= max_age_days:
        return

    info(f"🔄 Updating all-time leaders (last updated {age_days:.0f} days ago)...")
    try:
        result = subprocess.run(
            ['python3', '-m', 'baseball_processor.scrapers.all_time_leaders_scraper', '--source', 'api'],
            timeout=120
        )
        if result.returncode == 0:
            info("  ✅ All-time leaders updated")
        else:
            warn(f"  ⚠️ All-time leaders update failed (exit code {result.returncode})")
    except subprocess.TimeoutExpired:
        warn("  ⚠️ All-time leaders update timed out")
    except Exception as e:
        warn(f"  ⚠️ All-time leaders update error: {e}")


def _refresh_drafts(args):
    """Ensure MLB draft picks (1965..current) are cached.

    Past seasons are immutable, so the network cost is one HTTP per season
    on first run and just the current-year refresh thereafter.
    """
    if _should_skip_network_reference_updates(args):
        return
    try:
        from .scrapers.draft_scraper import update_drafts
        update_drafts(verbose=True)
    except Exception as e:
        warn(f"  ⚠️ Draft refresh skipped: {e}")


def _refresh_career_firsts_for_games(games_data, args):
    """Run the MLB API career-firsts refresh across every attended game.

    The TTL cache makes this essentially free after the first pass —
    same-day reruns skip entirely. The point of running it from main is to
    backfill schema changes (e.g., the retirement / career-lasts fields)
    without forcing the user to re-add every game.
    """
    if _should_skip_network_reference_updates(args):
        return
    try:
        from .scrapers.career_firsts_scraper import update_career_firsts_from_api
    except Exception as e:
        warn(f"  ⚠️ Career-firsts refresh skipped (import): {e}")
        return
    refreshed_games = 0
    for game in games_data or []:
        bi = game.get('basic_info') or {}
        if bi.get('game_type') == 'spring':
            continue
        try:
            update_career_firsts_from_api(game, verbose=False)
            refreshed_games += 1
        except Exception as e:
            warn(f"  ⚠️ Career firsts refresh failed for {game.get('game_id', '?')}: {e}")
    if refreshed_games:
        info(f"  ⚡ Career firsts: refreshed across {refreshed_games} games (TTL-cached players skipped)")


def _should_skip_network_reference_updates(args):
    """Return True for modes that should be reproducible from local data only."""
    return args.from_cache_only or args.from_db or args.quick_stats


def _should_refresh_all_time_leaders(args):
    return not args.website_only and not _should_skip_network_reference_updates(args)


def _should_update_debuts(args):
    return not args.skip_debut_update and not _should_skip_network_reference_updates(args)


def _should_download_bref_backups(args):
    return not _should_skip_network_reference_updates(args)


def _maybe_download_bref_backups(args):
    if not _should_download_bref_backups(args):
        info("Skipping BREF HTML backup fetch in local-only mode")
        return

    # Fetch any missing BREF HTML backups for API-sourced games (>24h old).
    # Idempotent: skips games that already have HTML. Safe to run every pipeline.
    try:
        from .scrapers.download_bref import run as download_bref_run
        download_bref_run(verbose=True)
    except Exception as e:
        warn(f"⚠️ BREF HTML backup skipped: {e}")


# BREF team codes that themselves start with 'M'; cached game IDs beginning
# with one of these are already in BREF form and must not have a leading 'M'
# stripped when normalizing for companions.csv lookup.
_BREF_M_TEAM_CODES = {'MIA', 'MIL', 'MIN', 'MON'}


def _bref_game_id(game_id):
    if game_id.startswith('M') and game_id[:3] not in _BREF_M_TEAM_CODES:
        return game_id[1:]
    return game_id


def _sync_companions_csv(games_data):
    """Append rows for any attended games not yet listed in companions.csv.

    New rows have an empty Companions field so the user can fill them in
    later. Existing rows are never modified or reordered. Spring training
    games are skipped (companions tracking is for attended regular/post games).
    """
    import csv as _csv

    csv_path = BASE_DIR / "companions.csv"
    if not csv_path.exists():
        return

    existing_ids = set()
    try:
        with open(csv_path, 'r', encoding='utf-8', newline='') as f:
            reader = _csv.reader(f)
            for i, row in enumerate(reader):
                if not row:
                    continue
                first = (row[0] or '').strip()
                if not first or first.startswith('#') or first == 'GameID':
                    continue
                existing_ids.add(first)
    except Exception as e:
        warn(f"      ⚠️  Could not read companions.csv for sync: {e}")
        return

    new_rows = []
    seen_in_batch = set()
    for game in games_data:
        bi = game.get('basic_info') or {}
        game_id = (game.get('game_id') or bi.get('game_id') or '').strip()
        if not game_id:
            continue
        game_id = _bref_game_id(game_id)
        if game_id in existing_ids or game_id in seen_in_batch:
            continue
        if bi.get('game_type') == 'spring':
            continue
        date_yyyymmdd = (bi.get('date_yyyymmdd') or '').strip()
        if len(date_yyyymmdd) != 8 or not date_yyyymmdd.isdigit():
            continue
        date_str = f"{date_yyyymmdd[4:6]}/{date_yyyymmdd[6:8]}/{date_yyyymmdd[:4]}"
        away = (bi.get('away_team_code') or '').strip()
        home = (bi.get('home_team_code') or '').strip()
        matchup = f"{away} @ {home}" if away and home else ''
        venue = (bi.get('venue') or bi.get('stadium') or '').strip()
        new_rows.append((date_yyyymmdd, game_id, date_str, matchup, venue))
        seen_in_batch.add(game_id)

    if not new_rows:
        return

    new_rows.sort(key=lambda r: (r[0], r[1]))

    needs_leading_newline = False
    try:
        with open(csv_path, 'rb') as f:
            f.seek(0, 2)
            if f.tell() > 0:
                f.seek(-1, 2)
                if f.read(1) != b'\n':
                    needs_leading_newline = True
    except Exception:
        pass

    try:
        with open(csv_path, 'a', encoding='utf-8', newline='') as f:
            if needs_leading_newline:
                f.write('\n')
            writer = _csv.writer(f, lineterminator='\n')
            for _, gid, date_str, matchup, venue in new_rows:
                writer.writerow([gid, '', date_str, matchup, venue])
    except Exception as e:
        warn(f"      ⚠️  Could not append to companions.csv: {e}")
        return

    suffix = '' if len(new_rows) == 1 else 's'
    info(f"      📝 companions.csv: added {len(new_rows)} new game{suffix} (Companions field blank — fill in to track)")


def _count_milestone_events(game):
    return sum(
        len(events)
        for events in game.get('milestone_stats', {}).values()
        if isinstance(events, list)
    )


def _has_meaningful_batting_line(player):
    """Return True when a batting row represents an actual plate/running line."""
    for stat in ['PA', 'AB', 'R', 'H', 'RBI', 'BB', 'SO', 'HBP', 'SF', 'SH', 'SB', 'CS', '2B', '3B', 'HR']:
        try:
            if int(player.get(stat, 0) or 0) != 0:
                return True
        except (TypeError, ValueError):
            continue
    return False


def _count_meaningful_lines(game):
    batting_count = sum(
        1
        for side in ['away', 'home']
        for player in game.get('batting', {}).get(side, []) or []
        if _has_meaningful_batting_line(player)
    )
    pitching_count = sum(
        len(game.get('pitching', {}).get(side, []) or [])
        for side in ['away', 'home']
    )
    return batting_count + pitching_count


def _count_enrichment_fields(game):
    return sum(
        1
        for key in ['pitch_data', 'hit_data', 'lineups', 'umpires', 'pitcher_decisions']
        if game.get(key)
    )


def _cache_game_quality_score(game):
    line_count = _count_meaningful_lines(game)
    play_count = len(game.get('play_by_play', []) or game.get('plays', []) or [])
    source = game.get('source') or game.get('basic_info', {}).get('source') or ''
    source_score = {'mlb': 2, 'bref': 1, 'pdf': 0}.get(source, 1)
    return (
        line_count,
        source_score,
        _count_enrichment_fields(game),
        play_count,
        _count_milestone_events(game),
        1 if game.get('footer_summary') else 0,
    )


def _has_cache_value(value):
    if value is None:
        return False
    if isinstance(value, str):
        return value.strip() not in ('', 'N/A', 'None', 'null')
    if isinstance(value, (list, tuple, set, dict)):
        return bool(value)
    return True


def _merge_missing_values(base, incoming):
    """Merge missing nested values from incoming into base without clobbering base."""
    if not isinstance(base, dict) or not isinstance(incoming, dict):
        return base

    for key, value in incoming.items():
        if not _has_cache_value(value):
            continue

        if key not in base or not _has_cache_value(base.get(key)):
            base[key] = copy.deepcopy(value)
        elif isinstance(base.get(key), dict) and isinstance(value, dict):
            _merge_missing_values(base[key], value)

    return base


def _stable_json_signature(value):
    return json.dumps(value, sort_keys=True, default=str)


def _normalize_cache_name(name):
    normalized = str(name or '').replace('\u00a0', ' ').strip().lower()
    return re.sub(r'\s+', ' ', normalized)


def _player_id_is_better(candidate, current):
    candidate = str(candidate or '').strip()
    current = str(current or '').strip()
    if not candidate:
        return False
    if not current:
        return True
    if current.startswith('mlb_') and not candidate.startswith('mlb_'):
        return True
    if '000' in current and '000' not in candidate:
        return True
    return False


def _merge_player_row(existing_row, incoming_row, prefer_incoming=False):
    primary = incoming_row if prefer_incoming else existing_row
    secondary = existing_row if prefer_incoming else incoming_row
    merged = copy.deepcopy(primary)
    _merge_missing_values(merged, secondary)

    if not prefer_incoming and _player_id_is_better(incoming_row.get('player_id'), existing_row.get('player_id')):
        merged['player_id'] = incoming_row.get('player_id')
    if not prefer_incoming and _player_id_is_better(incoming_row.get('bref_id'), existing_row.get('bref_id')):
        merged['bref_id'] = incoming_row.get('bref_id')

    existing_row.clear()
    existing_row.update(merged)


def _merge_player_section(base, incoming, section_name, incoming_source):
    section = base.setdefault(section_name, {})
    incoming_section = incoming.get(section_name, {})
    if not isinstance(section, dict) or not isinstance(incoming_section, dict):
        return

    base_source = base.get('source') or base.get('basic_info', {}).get('source') or ''
    prefer_incoming_common = incoming_source == 'mlb' and base_source != 'mlb'

    for side in ['away', 'home']:
        rows = section.setdefault(side, [])
        incoming_rows = incoming_section.get(side, []) or []

        by_id = {
            str(row.get('player_id')): row
            for row in rows
            if row.get('player_id')
        }
        by_name = {
            _normalize_cache_name(row.get('name')): row
            for row in rows
            if row.get('name')
        }

        for incoming_row in incoming_rows:
            match = None
            player_id = incoming_row.get('player_id')
            if player_id:
                match = by_id.get(str(player_id))
            if match is None and incoming_row.get('name'):
                match = by_name.get(_normalize_cache_name(incoming_row.get('name')))

            if match is not None:
                _merge_player_row(match, incoming_row, prefer_incoming_common)
                if match.get('player_id'):
                    by_id[str(match.get('player_id'))] = match
                if match.get('name'):
                    by_name[_normalize_cache_name(match.get('name'))] = match
                continue

            if section_name == 'batting' and not _has_meaningful_batting_line(incoming_row):
                continue

            copied = copy.deepcopy(incoming_row)
            rows.append(copied)
            if copied.get('player_id'):
                by_id[str(copied.get('player_id'))] = copied
            if copied.get('name'):
                by_name[_normalize_cache_name(copied.get('name'))] = copied


def _play_signature(play):
    description = _normalize_cache_name(play.get('description', ''))
    description = re.sub(r'\.?\s*\d+\s+outs?$', '', description)
    description = re.sub(r'[^a-z0-9]+', ' ', description).strip()
    return (
        play.get('inning'),
        str(play.get('half', '')).lower(),
        _normalize_cache_name(play.get('batter', '')),
        play.get('away_score'),
        play.get('home_score'),
        description,
    )


def _is_probable_plate_appearance(play):
    event_type = _normalize_cache_name(play.get('event_type') or play.get('event'))
    if event_type in {
        'single', 'double', 'triple', 'home run', 'walk', 'intent walk',
        'hit by pitch', 'strikeout', 'field out', 'force out',
        'grounded into double play', 'double play', 'triple play',
        'fielders choice', 'fielders choice out', 'sacrifice fly',
        'sacrifice bunt', 'catcher interference', 'field error',
        'fielders choice error',
    }:
        return True

    description = _normalize_cache_name(play.get('description', ''))
    if not description:
        return False
    if re.match(
        r'^(wild pitch|passed ball|stolen base|caught stealing|pickoff|balk|'
        r'defensive indifference|mound visit)',
        description,
    ):
        return False
    return bool(re.search(
        r'(single|double|triple|home run|homer|walk|hit by pitch|'
        r'strikeout|strikes out|called out on strikes|ground|line|fly|flies|'
        r'pop|pops|force out|fielder.?s choice|reaches on|sacrifice|'
        r'catcher interference|interference|double play|triple play)',
        description,
    ))


def _play_batter_slot(play):
    return (
        play.get('inning'),
        str(play.get('half', '')).lower(),
        _normalize_cache_name(play.get('batter', '')),
    )


def _merge_play_list(base, incoming, key):
    incoming_plays = incoming.get(key) or []
    if not incoming_plays:
        return

    base_plays = base.get(key)
    if not base_plays:
        base[key] = copy.deepcopy(incoming_plays)
        return

    seen = {_play_signature(play) for play in base_plays}
    remaining_base_pa_slots = {}
    for play in base_plays:
        if _is_probable_plate_appearance(play):
            slot = _play_batter_slot(play)
            remaining_base_pa_slots[slot] = remaining_base_pa_slots.get(slot, 0) + 1

    for play in incoming_plays:
        if _is_probable_plate_appearance(play):
            slot = _play_batter_slot(play)
            if remaining_base_pa_slots.get(slot, 0) > 0:
                remaining_base_pa_slots[slot] -= 1
                continue

        signature = _play_signature(play)
        if signature not in seen:
            base_plays.append(copy.deepcopy(play))
            seen.add(signature)


def _merge_milestone_stats(base, incoming):
    incoming_stats = incoming.get('milestone_stats')
    if not isinstance(incoming_stats, dict):
        return

    base_stats = base.setdefault('milestone_stats', {})
    if not isinstance(base_stats, dict):
        base['milestone_stats'] = copy.deepcopy(incoming_stats)
        return

    for category, incoming_events in incoming_stats.items():
        if not _has_cache_value(incoming_events):
            continue

        if category not in base_stats or not _has_cache_value(base_stats.get(category)):
            base_stats[category] = copy.deepcopy(incoming_events)
            continue

        if isinstance(base_stats[category], list) and isinstance(incoming_events, list):
            seen = {_stable_json_signature(event) for event in base_stats[category]}
            for event in incoming_events:
                signature = _stable_json_signature(event)
                if signature not in seen:
                    base_stats[category].append(copy.deepcopy(event))
                    seen.add(signature)
        elif isinstance(base_stats[category], dict) and isinstance(incoming_events, dict):
            _merge_missing_values(base_stats[category], incoming_events)


def _merge_generic_list(base, incoming, key):
    incoming_values = incoming.get(key) or []
    if not incoming_values:
        return
    if not isinstance(incoming_values, list):
        if isinstance(incoming_values, dict) and isinstance(base.get(key), dict):
            _merge_missing_values(base[key], incoming_values)
        elif key not in base or not _has_cache_value(base.get(key)):
            base[key] = copy.deepcopy(incoming_values)
        return

    base_values = base.get(key)
    if not base_values:
        base[key] = copy.deepcopy(incoming_values)
        return
    if not isinstance(base_values, list):
        return

    seen = {_stable_json_signature(value) for value in base_values}
    for value in incoming_values:
        signature = _stable_json_signature(value)
        if signature not in seen:
            base_values.append(copy.deepcopy(value))
            seen.add(signature)


def _merge_cache_game_records(primary, secondary):
    """Merge two cache aliases for the same game_id, keeping primary as canonical."""
    merged = copy.deepcopy(primary)
    incoming_source = secondary.get('source') or secondary.get('basic_info', {}).get('source') or ''

    _merge_missing_values(merged, secondary)
    if isinstance(merged.get('basic_info'), dict) and isinstance(secondary.get('basic_info'), dict):
        _merge_missing_values(merged['basic_info'], secondary['basic_info'])

    _merge_player_section(merged, secondary, 'batting', incoming_source)
    _merge_player_section(merged, secondary, 'pitching', incoming_source)
    _merge_milestone_stats(merged, secondary)

    for key in ['raw_plays', 'play_by_play', 'plays']:
        _merge_play_list(merged, secondary, key)

    for key in ['substitutions', 'special_events', 'abs_challenges']:
        _merge_generic_list(merged, secondary, key)

    return merged


def _find_api_cache_for_game_id(game_id, cache_dir=CACHE_DIR, exclude_path=None):
    """Find an API-sourced cache record by internal game_id, not just filename."""
    if not game_id:
        return None, None

    exclude = Path(exclude_path).resolve() if exclude_path else None
    searched = set()
    candidate_names = [f"{game_id}.json", f"M{game_id}.json"]

    def try_path(path):
        resolved = path.resolve()
        if resolved in searched or (exclude and resolved == exclude):
            return None, None
        searched.add(resolved)
        if not path.exists():
            return None, None
        try:
            with open(path, 'r', encoding='utf-8') as f:
                game = json.load(f)
        except (json.JSONDecodeError, IOError):
            return None, None
        source = game.get('source') or game.get('basic_info', {}).get('source')
        if source == 'mlb' and game.get('game_id') == game_id:
            return path, game
        return None, None

    for name in candidate_names:
        found_path, found_game = try_path(cache_dir / name)
        if found_game:
            return found_path, found_game

    skip_patterns = ['career_firsts', 'career_gamelogs', 'player_bios', 'career_highs']
    for path in sorted(cache_dir.glob("*.json")):
        if any(pattern in path.name for pattern in skip_patterns):
            continue
        found_path, found_game = try_path(path)
        if found_game:
            return found_path, found_game

    return None, None


def _load_games_from_cache(cache_dir=CACHE_DIR):
    """Load cache games, deduping exact game_id aliases while merging useful data."""
    games_by_id = {}
    games_without_id = []
    duplicates_skipped = 0
    skip_patterns = ['career_firsts', 'career_gamelogs']

    for file in sorted(cache_dir.glob("*.json")):
        if any(pattern in str(file) for pattern in skip_patterns):
            continue
        with open(file, 'r', encoding='utf-8') as f:
            game = json.load(f)
        if not isinstance(game, dict) or 'basic_info' not in game:
            continue

        bi = game['basic_info']
        if 'game_type' not in bi:
            bi['game_type'] = 'regular'
            bi['source'] = bi.get('source', 'bref')

        game_id = game.get('game_id')
        if not game_id:
            games_without_id.append(game)
            continue

        existing = games_by_id.get(game_id)
        if existing is None:
            games_by_id[game_id] = game
            continue

        duplicates_skipped += 1
        if _cache_game_quality_score(game) > _cache_game_quality_score(existing):
            games_by_id[game_id] = _merge_cache_game_records(game, existing)
        else:
            games_by_id[game_id] = _merge_cache_game_records(existing, game)

    games_data = list(games_by_id.values()) + games_without_id
    spring_count = sum(
        1 for game in games_data
        if game.get('basic_info', {}).get('game_type') == 'spring'
    )
    return games_data, spring_count, duplicates_skipped


def _update_gamelogs_for_game(cache_path):
    """Update gamelogs cache for all-time leaders who appeared in this game.

    Only scrapes the current year's gamelog and appends to existing data,
    rather than re-scraping entire careers.
    """
    try:
        from .scrapers.career_firsts_scraper import (
            get_players_from_game_file, load_all_time_leaders,
            scrape_batting_game_log, scrape_pitching_game_log,
            create_scraper, load_gamelogs_cache, save_gamelogs_cache
        )
        import time as _time

        player_ids, _ = get_players_from_game_file(cache_path)
        if not player_ids:
            return

        # Check which players are on all-time lists
        all_time_players = load_all_time_leaders()
        leaders_in_game = player_ids & set(all_time_players.keys())
        if not leaders_in_game:
            return

        # Get game year
        with open(cache_path) as f:
            game = json.load(f)
        game_date = game.get('basic_info', {}).get('date_yyyymmdd', '')
        if not game_date:
            return
        game_year = int(game_date[:4])

        # Only refresh players whose gamelogs don't include this game
        gc = load_gamelogs_cache()
        stale = set()
        for pid in leaders_in_game:
            existing = gc.get(pid, {}).get('gamelogs', {})
            game_id = game.get('game_id', '')
            if game_id not in existing:
                stale.add(pid)

        if not stale:
            return

        info(f"     Updating gamelogs for {len(stale)} all-time leaders (year {game_year})...")
        scraper = create_scraper()
        updated = 0

        for idx, pid in enumerate(stale, 1):
            pname = all_time_players[pid].get('name', pid)
            info(f"       [{idx}/{len(stale)}] {pname}...")
            try:
                existing = gc.get(pid, {}).get('gamelogs', {})
                stat_type = all_time_players[pid].get('type', 'batting')

                # If no existing gamelogs, need full career scrape
                if not existing:
                    from .scrapers.career_firsts_scraper import find_career_firsts as _find_firsts
                    info(f"       Full scrape for new player: {pname}")
                    firsts = _find_firsts(pid, scraper, verbose=False, store_gamelogs=True)
                    if firsts.get('gamelogs'):
                        gc[pid] = {'name': all_time_players[pid].get('name', pid), 'gamelogs': firsts['gamelogs']}
                        updated += 1
                    continue

                # Get the last known cumulative totals from existing data
                prev_totals = {}
                sorted_games = sorted(existing.keys(), key=lambda g: g[3:11] if len(g) >= 11 else '')
                for gid in reversed(sorted_games):
                    data = existing[gid]
                    if stat_type == 'batting' and data.get('batting'):
                        prev_totals = data['batting'].copy()
                        break
                    elif stat_type == 'pitching' and data.get('pitching'):
                        prev_totals = data['pitching'].copy()
                        break

                # Scrape current year's gamelog only (incremental update)
                _time.sleep(3.1)
                if stat_type == 'batting':
                    games_data = scrape_batting_game_log(pid, game_year, scraper)
                else:
                    games_data = scrape_pitching_game_log(pid, game_year, scraper)

                if not games_data:
                    continue

                # Build cumulative totals from this year
                cumulative = prev_totals.copy()
                for g in games_data:
                    gid = g.get('game_id', '')
                    if not gid or gid in existing:
                        continue
                    # Accumulate stats
                    for stat_key in g:
                        if stat_key in ('game_id', 'date', 'date_full', 'opponent', 'team'):
                            continue
                        val = g.get(stat_key, 0)
                        if isinstance(val, (int, float)) and val > 0:
                            cumulative[stat_key] = cumulative.get(stat_key, 0) + val

                    # Special: G (games) always +1
                    cumulative['G'] = cumulative.get('G', 0) + 1

                    if gid not in existing:
                        if pid not in gc:
                            gc[pid] = {'name': all_time_players[pid].get('name', pid), 'gamelogs': {}}
                        gc[pid]['gamelogs'][gid] = {stat_type: cumulative.copy()}

                updated += 1
            except Exception:
                pass

        if updated > 0:
            save_gamelogs_cache(gc)
            info(f"     ✅ Updated {updated} players")
    except Exception:
        pass  # Don't fail the pipeline for gamelog updates


COUNTRY_NORMALIZE = {
    'Republic of Korea': 'South Korea', 'Korea, Republic of': 'South Korea',
    'VEN': 'Venezuela', 'DOM': 'Dominican Republic', 'D.R.': 'Dominican Republic',
    'PR': 'Puerto Rico', 'CAN': 'Canada', 'MEX': 'Mexico', 'CUB': 'Cuba',
    'JPN': 'Japan', 'COL': 'Colombia', 'PAN': 'Panama', 'NIC': 'Nicaragua',
    'AUS': 'Australia', 'BRA': 'Brazil', 'GER': 'Germany', 'NED': 'Netherlands',
    'TWN': 'Taiwan', 'Curaçao': 'Curacao',
}


def _fetch_missing_bios_for_game(game_data):
    """Fetch player bios from MLB API for any players not yet in the cache."""
    import json
    from pathlib import Path
    from .utils.http import create_retry_session, get_with_retry

    bio_path = Path(__file__).parent.parent / 'cache' / 'player_bios.json'
    bios = {}
    if bio_path.exists():
        try:
            with open(bio_path, 'r') as f:
                bios = json.load(f)
        except (json.JSONDecodeError, IOError):
            pass

    # Collect all player IDs and names from the game
    player_names = {}
    for side in ('home', 'away'):
        for p in game_data.get('batting', {}).get(side, []):
            pid = p.get('player_id', '')
            if pid and pid not in bios:
                player_names[pid] = p.get('name', '')
        for p in game_data.get('pitching', {}).get(side, []):
            pid = p.get('player_id', '')
            if pid and pid not in bios:
                player_names[pid] = p.get('name', '')

    if not player_names:
        return

    info(f"  🪪 Fetching bios for {len(player_names)} new players...")
    session = create_retry_session()
    found = 0

    for pid, name in player_names.items():
        if not name:
            continue
        try:
            resp = get_with_retry(
                session,
                f'https://statsapi.mlb.com/api/v1/people/search?names={name.replace(" ", "%20")}&sportIds=1,11,12,13,14,15,16',
                timeout=10
            )
            if resp.status_code == 200:
                people = resp.json().get('people', [])
                if people:
                    p = people[0]
                    country = p.get('birthCountry', '')
                    bios[pid] = {
                        'name': p.get('fullName', name),
                        'birthDate': p.get('birthDate', ''),
                        'birthCity': p.get('birthCity', ''),
                        'birthState': p.get('birthStateProvince', ''),
                        'birthCountry': COUNTRY_NORMALIZE.get(country, country),
                        'height': p.get('height', ''),
                        'weight': p.get('weight', 0),
                        'bats': p.get('batSide', {}).get('code', ''),
                        'throws': p.get('pitchHand', {}).get('code', ''),
                        'debutDate': p.get('mlbDebutDate', ''),
                    }
                    found += 1
        except Exception:
            pass

    if found > 0:
        with open(bio_path, 'w') as f:
            json.dump(bios, f, ensure_ascii=False)
        info(f"  ✅ Fetched {found} new player bios ({len(bios)} total)")


def _scrape_career_firsts_for_game(cache_path):
    """Scrape/update career milestones for all players in a newly parsed game.

    Skips players whose cached career data is already fresh through this game's
    date. add_game's MLB API path records scraped_at at the moment it runs, so
    any game added via add_game (even historical ones) gets full career data
    captured — a subsequent BREF HTML backup run would just overwrite with the
    same info. Only re-scrape if cached scraped_at is earlier than the game's
    date (i.e., the player's career data doesn't yet include this game).
    """
    from datetime import datetime
    import json as _json
    from .scrapers.career_firsts_scraper import (
        get_players_from_game_file, scrape_career_firsts_for_players,
        get_cache_path,
    )
    info("  🔍 Checking career milestones for players in this game...")
    player_ids, player_names = get_players_from_game_file(cache_path)
    if not player_ids:
        return
    valid_ids = {pid for pid in player_ids if not (len(pid) >= 10 and any(c.isdigit() for c in pid[5:9]))}
    if not valid_ids:
        return

    # Determine this game's date (for the "scraped_at >= game_date" gate)
    import json as __json
    try:
        with open(cache_path) as f:
            _game = __json.load(f)
        _date_str = (_game.get('basic_info', {}).get('date_yyyymmdd') or '')
        game_date = datetime.strptime(_date_str, '%Y%m%d') if len(_date_str) == 8 else None
    except (IOError, ValueError):
        game_date = None

    cf_path = get_cache_path() / 'career_firsts.json'
    cache_data = {}
    if cf_path.exists():
        try:
            with open(cf_path) as f:
                cache_data = _json.load(f)
        except (IOError, ValueError):
            pass

    stale_ids = set()
    for pid in valid_ids:
        entry = cache_data.get(pid) or {}
        scraped_at = entry.get('scraped_at') or ''
        try:
            when = datetime.fromisoformat(scraped_at)
        except ValueError:
            when = None
        # Stale if: never scraped, or scraped before this game's date
        if not when or (game_date and when < game_date):
            stale_ids.add(pid)
    if not stale_ids:
        info(f"     ✅ All {len(valid_ids)} players fresh through game date — skipping BREF scrape")
        return
    info(f"     Refreshing BREF career data for {len(stale_ids)} stale players "
         f"(skipping {len(valid_ids) - len(stale_ids)} fresh ones)...")
    cache = scrape_career_firsts_for_players(
        stale_ids,
        refresh=True,
        delay=3.1,
        verbose=True,
        player_names={pid: player_names.get(pid) for pid in stale_ids if pid in player_names},
    )
    if cache:
        info(f"  ✅ Updated career milestones ({len(cache)} players in cache)")


def _fetch_abs_from_savant(game_data, game_pk, session):
    """Fetch ABS challenge data from Baseball Savant gamefeed API."""
    try:
        from .scrapers.pitch_data_scraper import fetch_savant_abs
        challenges = fetch_savant_abs(session, game_pk)
        if challenges is not None and len(challenges) > 0:
            game_data['abs_challenges'] = {'reviews': challenges}
            info(f"     ⚖️ ABS challenges: {len(challenges)} (from Savant)")
    except Exception:
        pass


def _enrich_with_api_data(game_data):
    """Enrich a BREF-parsed game with MLB API data (pitch speeds, jersey numbers)."""
    import time
    from .parsers.mlb_api_parser import parse_pitch_data, parse_hit_data, parse_umpires, TEAM_ID_TO_CODE
    from .utils.http import create_retry_session, get_with_retry
    from .scrapers.pitch_data_scraper import CODE_TO_MLB_ID, find_game_pk, remap_pitch_data_keys

    bi = game_data.get('basic_info', {})
    date = bi.get('date_yyyymmdd', '')
    home_code = bi.get('home_team_code', '')
    away_code = bi.get('away_team_code', '')
    if not date or home_code not in CODE_TO_MLB_ID or away_code not in CODE_TO_MLB_ID:
        return

    session = create_retry_session()
    fd = f"{date[:4]}-{date[4:6]}-{date[6:8]}"

    # Get schedule to find gamePk
    resp = get_with_retry(session, f"https://statsapi.mlb.com/api/v1/schedule?date={fd}&sportId=1", timeout=15)
    if resp.status_code != 200:
        return
    dates = resp.json().get('dates', [])
    schedule_games = dates[0].get('games', []) if dates else []
    dh = game_data.get('doubleheader', '0')
    game_pk = find_game_pk(schedule_games, home_code, away_code, dh)
    if not game_pk:
        return

    game_data['mlb_game_pk'] = game_pk

    # Fetch live feed for pitch data
    feed_resp = get_with_retry(session, f"https://statsapi.mlb.com/api/v1.1/game/{game_pk}/feed/live", timeout=30)
    if feed_resp.status_code == 200:
        feed_data = feed_resp.json()
        pitch_data = parse_pitch_data(feed_data, {})
        if pitch_data:
            game_data['pitch_data'] = remap_pitch_data_keys(pitch_data, game_data)
            info(f"     📊 Pitch data: {len(game_data['pitch_data'])} pitchers")
        hit_data = parse_hit_data(feed_data, {})
        if hit_data:
            # Remap keys by name matching (same as pitch data)
            from .utils.helpers import normalize_name as _normalize_name
            name_to_bref = {}
            for side in ('away', 'home'):
                for p in game_data.get('batting', {}).get(side, []):
                    name = _normalize_name(p.get('name', ''))
                    pid = p.get('player_id', '')
                    if name and pid and not pid.startswith('mlb_'):
                        name_to_bref[name] = pid
            remapped_hits = {}
            for key, hdata in hit_data.items():
                norm_name = _normalize_name(hdata.get('name', ''))
                new_key = name_to_bref.get(norm_name, key)
                hdata['player_id'] = new_key
                remapped_hits[new_key] = hdata
            game_data['hit_data'] = remapped_hits
            info(f"     🏏 Hit data: {len(remapped_hits)} batters")

        # ABS challenges - fetch from Baseball Savant gamefeed (most complete source)
        _fetch_abs_from_savant(game_data, game_pk, session)

    # Fetch boxscore for jersey numbers
    box_resp = get_with_retry(session, f"https://statsapi.mlb.com/api/v1/game/{game_pk}/boxscore", timeout=15)
    if box_resp.status_code == 200:
        box = box_resp.json()
        jersey_map = {}
        for side_key in ['away', 'home']:
            team = box.get('teams', {}).get(side_key, {})
            for pid_str, player in team.get('players', {}).items():
                name = player.get('person', {}).get('fullName', '')
                jersey = player.get('jerseyNumber', '')
                if name and jersey:
                    jersey_map[name.lower()] = jersey

        updated = 0
        for side in ['away', 'home']:
            for p in game_data.get('batting', {}).get(side, []):
                j = jersey_map.get(p.get('name', '').lower(), '')
                if j:
                    p['jersey_number'] = j
                    updated += 1
            for p in game_data.get('pitching', {}).get(side, []):
                j = jersey_map.get(p.get('name', '').lower(), '')
                if j:
                    p['jersey_number'] = j
                    updated += 1
        if updated:
            info(f"     🔢 Jersey numbers: {updated} players")

        # Also grab umpires from API if BREF didn't have them
        if not game_data.get('umpires') or not any(game_data.get('umpires', {}).values()):
            game_data['umpires'] = parse_umpires(box)


def process_html_file(file_path, index=None, total=None):
    """Process a single Baseball-Reference HTML file, with filename-based caching."""
    try:
        if index is not None and total is not None:
            info(f"📄 Processing file {index} of {total}: {os.path.basename(file_path)}")
        else:
            info(f"Processing {file_path}...")

        # Use the filename (without path and extension) as the cache key
        filename = os.path.basename(file_path)
        filename_no_ext = os.path.splitext(filename)[0]
        
        # Clean filename to make it safe for filesystem (remove special chars)
        safe_filename = re.sub(r'[^\w\-_]', '_', filename_no_ext)
        
        # Check cache using filename as key
        cache_path = CACHE_DIR / f"{safe_filename}.json"
        
        if cache_path.exists():
            html_mtime = os.path.getmtime(file_path)
            json_mtime = os.path.getmtime(cache_path)
            
            if html_mtime <= json_mtime:
                # Cache is up to date - use it!
                info("  ✅ Using cached data")
                with open(cache_path, 'r', encoding='utf-8') as f:
                    cached_data = json.load(f)

                    # Optionally show what game this is
                    game_id = cached_data.get("game_id", "Unknown")
                    info(f"     Game ID: {game_id}")

                    # Enrich with API data if missing (only for newly cached games without pitch data)
                    # Skip if already enriched or if game is too old for pitch tracking
                    if not cached_data.get('pitch_data') and not cached_data.get('_api_enrichment_attempted'):
                        date_str = cached_data.get('basic_info', {}).get('date_yyyymmdd', '')
                        if date_str and date_str >= '20080101':
                            try:
                                _enrich_with_api_data(cached_data)
                                cached_data['_api_enrichment_attempted'] = True
                                with open(cache_path, 'w', encoding='utf-8') as fw:
                                    json.dump(cached_data, fw, indent=2)
                            except Exception:
                                cached_data['_api_enrichment_attempted'] = True

                    return cached_data
            else:
                info("  🔄 Cache outdated, re-parsing...")
        else:
            info("  🆕 No cache found, parsing HTML...")

        # Parse the HTML
        with open(file_path, 'r', encoding='utf-8') as file:
            html_content = file.read()

        game_data = parse_baseball_reference_boxscore(html_content)
        game_id = game_data.get("game_id", "UNKNOWN")

        info(f"  📊 Parsed game: {game_id}")

        # If this game was already added via the MLB API (add_game), the
        # API-sourced cache is the source of truth — don't let the BREF backup
        # create a competing JSON record. Use the API data instead, running
        # MilestoneEngine on it if needed.
        api_cache_path, api_data = _find_api_cache_for_game_id(game_id, CACHE_DIR, cache_path)
        if api_cache_path and api_data:
            try:
                info(f"  🌟 API-sourced cache exists ({api_cache_path.name}) — using it instead of BREF backup JSON")
                ms = api_data.get('milestone_stats')
                if not ms or (isinstance(ms, dict) and not any(ms.values())):
                    try:
                        from baseball_processor.engines.milestone_engine import MilestoneEngine
                        MilestoneEngine(api_data).process()
                        with open(api_cache_path, 'w', encoding='utf-8') as f:
                            json.dump(api_data, f, indent=2)
                    except Exception as e:
                        debug(f"  ⚠️ Milestone engine on API data skipped: {e}")
                return api_data
            except Exception as e:
                debug(f"  ⚠️ API cache check failed, falling back to BREF parse: {e}")

        # Enrich with MLB API data (pitch speeds, jersey numbers) if not already present
        if not game_data.get('pitch_data'):
            try:
                _enrich_with_api_data(game_data)
            except Exception as e:
                debug(f"  ⚠️ API enrichment skipped: {e}")

        # Save to cache atomically (write to temp, then rename)
        temp_cache = cache_path.with_suffix('.tmp')
        with open(temp_cache, 'w', encoding='utf-8') as f:
            json.dump(game_data, f, indent=2)
        temp_cache.replace(cache_path)
        info("  💾 Saved to cache")

        # Fetch bios for any new players in this game
        try:
            _fetch_missing_bios_for_game(game_data)
        except Exception as e:
            debug(f"  ⚠️ Bio fetch skipped: {e}")

        # Scrape career milestones for all players in this game (regular season only)
        game_type = game_data.get('basic_info', {}).get('game_type', 'regular')
        if game_type in ('regular', 'postseason'):
            try:
                _scrape_career_firsts_for_game(cache_path)
            except Exception as e:
                debug(f"  ⚠️ Career firsts scraping skipped: {e}")
            try:
                _update_gamelogs_for_game(cache_path)
            except Exception as e:
                debug(f"  ⚠️ Gamelogs update skipped: {e}")

        # Print "New This Game" summary
        _print_game_summary(game_data)

        return game_data

    except Exception as e:
        error_msg = str(e)
        warn(f"❌ Error processing {file_path}: {error_msg}")
        logging.exception("Error details:")
        # Return a special dict to indicate failure
        return {"_error": True, "file": file_path, "error": error_msg}
  
def process_directory_or_file(input_path, umpire_tracker):
    """Process HTML files from directory or single file."""
    all_games_data = []
    games_missing_umpires = []
    failed_files = []

    if os.path.isfile(input_path):
        if input_path.endswith('.html'):
            game_data = process_html_file(input_path)
            if game_data:
                # Check if this is an error result
                if game_data.get("_error"):
                    failed_files.append(game_data)
                else:
                    game_id = game_data.get("game_id", "UNKNOWN")
                    if not game_data.get("umpires"):
                        games_missing_umpires.append(game_id)
                    else:
                        for pos, name in game_data.get("umpires", {}).items():
                            umpire_tracker.record_umpire(name, pos, game_id)
                    all_games_data.append(game_data)
        else:
            warn(f"❌ File must be an HTML file: {input_path}")
    elif os.path.isdir(input_path):
        html_files = [f for f in os.listdir(input_path) if f.endswith('.html')]
        info(f"Found {len(html_files)} HTML files in {input_path}")
        
        total = len(html_files)

        for idx, filename in enumerate(html_files, start=1):
            file_path = os.path.join(input_path, filename)
            game_data = process_html_file(file_path, idx, total)
            if game_data:
                # Check if this is an error result
                if game_data.get("_error"):
                    failed_files.append(game_data)
                else:
                    game_id = game_data.get("game_id", "UNKNOWN")
                    if not game_data.get("umpires"):
                        games_missing_umpires.append(game_id)
                    else:
                        for pos, name in game_data.get("umpires", {}).items():
                            umpire_tracker.record_umpire(name, pos, game_id)
                    all_games_data.append(game_data)
    else:
        warn(f"❌ Invalid path: {input_path}")
        return []
    
    info(f"✅ Successfully processed {len(all_games_data)} games")
    
    # Report failed files
    if failed_files:
        warn(f"\n❌ Failed to process {len(failed_files)} file(s):")
        for failed in failed_files:
            file_name = os.path.basename(failed["file"])
            error_msg = failed["error"]
            warn(f"   • {file_name}")
            warn(f"     Error: {error_msg}")
        warn(f"\n💡 Tip: Check these files for corruption or formatting issues")
    
        # Save detailed report
        output_dir = os.path.dirname(input_path) if os.path.isfile(input_path) else input_path
        save_failed_files_report(failed_files, output_dir)

    # Report umpire data status
    if games_missing_umpires:
        warn(f"\n⚠️ Missing umpire data in {len(games_missing_umpires)} game(s):")
        for gid in games_missing_umpires:
            warn(f"   • {gid}")
    else:
        info("✅ All games include umpire data.")
    
    return all_games_data

def save_failed_files_report(failed_files, output_dir):
    """Save a report of failed files for later investigation."""
    if not failed_files:
        return
    
    report_path = os.path.join(output_dir, "failed_files_report.txt")
    with open(report_path, 'w') as f:
        f.write("Failed Files Report\n")
        f.write("=" * 60 + "\n\n")
        f.write(f"Total failed: {len(failed_files)}\n")
        f.write(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
        
        for i, failed in enumerate(failed_files, 1):
            f.write(f"{i}. {failed['file']}\n")
            f.write(f"   Error: {failed['error']}\n\n")
    
    info(f"📝 Failed files report saved to: {report_path}")

def main():
    parser = argparse.ArgumentParser(
        description="Combined Baseball Game Processor - Parse HTML box scores and generate Excel workbook"
    )
    parser.add_argument(
        'input_path',
        nargs='?',
        default=DEFAULT_INPUT_DIR,
        help='Directory containing HTML files or single HTML file'
    )
    parser.add_argument(
        '--output-excel',
        default=str(BASE_DIR / 'MLB Game Passport - BREF.xlsx'),
        help='Excel output filename'
    )
    parser.add_argument(
        '--save-json',
        action='store_true',
        help='Save intermediate JSON data file'
    )
    parser.add_argument(
        '--from-cache-only',
        action='store_true',
        help='Load all games from cached JSON files instead of reprocessing HTML'
    )
    parser.add_argument(
        '--excel-only',
        action='store_true',
        help='Generate only Excel workbook, skip website generation'
    )
    parser.add_argument(
        '--website-only',
        action='store_true',
        help='Generate only website, skip Excel workbook (processes data but does not write Excel)'
    )
    parser.add_argument(
        '--verbose',
        action='store_true',
        help='Enable extra debug output'
    )
    parser.add_argument(
        '--no-emoji',
        action='store_true',
        help='Disable emoji in console output'
    )
    parser.add_argument(
        '--log-file',
        type=str,
        default=None,
        help='Path to log file for detailed logging (creates timestamped log if no path given)'
    )
    parser.add_argument(
        '--parallel',
        action='store_true',
        help='Use parallel processing for faster parsing (recommended for 50+ games)'
    )
    parser.add_argument(
        '--workers',
        type=int,
        default=None,
        help='Number of worker processes for parallel mode (default: CPU count - 1)'
    )
    parser.add_argument(
        '--export-csv',
        type=str,
        default=None,
        help='Export all data to CSV files in the specified directory'
    )
    parser.add_argument(
        '--quick-stats',
        action='store_true',
        help='Print quick statistics summary without generating full reports'
    )
    parser.add_argument(
        '--skip-debut-update',
        action='store_true',
        help='Skip auto-updating MLB debut data from Baseball-Reference'
    )
    parser.add_argument(
        '--debut-year',
        type=int,
        default=None,
        help='Year to update debuts for (default: current year)'
    )
    parser.add_argument(
        '--deploy',
        action='store_true',
        help='Deploy website to Surge after generation'
    )
    parser.add_argument(
        '--no-deploy',
        action='store_true',
        help='Skip Surge deployment for this run, even if .surge-domain is configured'
    )
    parser.add_argument(
        '--surge-domain',
        type=str,
        default=None,
        help='Surge domain to deploy to (e.g., mlb-passport.surge.sh). Saved for future runs.'
    )
    parser.add_argument(
        '--scrape-career-firsts',
        action='store_true',
        dest='scrape_career_firsts',
        help='Scrape career firsts for players in processed games (skips already cached players)'
    )
    parser.add_argument(
        '--refresh-career-events',
        action='store_true',
        help='Maintenance: refresh career firsts/lasts via MLB API across all processed games'
    )
    parser.add_argument(
        '--export-players',
        action='store_true',
        help='Export shared player data for cross-project linking with NCAA processor'
    )
    parser.add_argument(
        '--migrate-cache',
        action='store_true',
        help='Migrate JSON cache files into SQLite database'
    )
    parser.add_argument(
        '--db-stats',
        action='store_true',
        help='Show database statistics and exit'
    )
    parser.add_argument(
        '--from-db',
        action='store_true',
        help='Load games from SQLite database instead of cache/HTML'
    )

    args = parser.parse_args()

    # Configure logging
    set_verbosity(args.verbose)
    set_use_emoji(not args.no_emoji)

    # Enable file logging if requested
    if args.log_file is not None:
        log_path = configure_file_logging(args.log_file if args.log_file else None)
        info(f"📝 Logging to: {log_path}")
    
    # Validate conflicting flags
    if args.excel_only and args.website_only:
        warn("❌ Error: Cannot use both --excel-only and --website-only flags")
        return

    # Handle database commands early
    if args.db_stats:
        from .db.database import Database
        db = Database()
        stats = db.get_stats()
        info("📊 Database Statistics:")
        for key, val in stats.items():
            info(f"  {key}: {val}")
        return

    if args.migrate_cache:
        from .db.database import Database
        db = Database()
        imported, errors = db.migrate_from_cache(CACHE_DIR)
        info(f"Migration complete: {imported} imported, {errors} errors")
        return

    if not os.path.exists(args.input_path) and not args.from_cache_only and not args.from_db:
        warn(f"❌ Input path does not exist: {args.input_path}")
        return

    info("⚾️ Starting Baseball Game Processor...")
    info(f"📂 Input: {args.input_path}")
    _log_surge_deploy_mode(args)

    # Refresh all-time leaders if stale (>7 days old)
    if _should_refresh_all_time_leaders(args):
        _refresh_all_time_leaders_if_stale()

    # Keep the MLB draft cache current — past years are immutable, only the
    # current season actually hits the network on repeat runs.
    _refresh_drafts(args)

    # Create a fresh umpire tracker for this run
    umpire_tracker = UmpireTracker()

    if not args.website_only:
        info(f"📊 Output Excel: {args.output_excel}")
        args.output_excel = os.path.expanduser(args.output_excel)
        info(f"▶ Excel will be written to: {os.path.abspath(args.output_excel)}")
    info(f"▶ Current working directory: {os.getcwd()}")

    # Step 0: Auto-update debuts (unless skipped)
    if _should_update_debuts(args):
        try:
            from .scrapers.debut_scraper import scrape_debuts, save_debuts_csv
            debut_year = args.debut_year or datetime.now().year
            info(f"🔄 Updating {debut_year} MLB debuts from Baseball-Reference...")

            df = scrape_debuts(debut_year, verbose=args.verbose)
            if not df.empty:
                filepath = save_debuts_csv(df, debut_year, REFERENCES_DIR)
                info(f"✅ Updated debuts: {filepath} ({len(df)} entries)")
            else:
                warn(f"⚠️ Could not fetch {debut_year} debuts, using cached data")
        except Exception as e:
            warn(f"⚠️ Failed to update debuts: {e}")
            info("   Continuing with existing debut data...")

    # Step 1: Load static references
    debut_entries = load_mlb_debuts(REFERENCES_DIR)
    hof_df = pd.read_csv(HOF_FILE)
    if "Name-additional" in hof_df.columns:
        hof_df.rename(columns={"Name-additional": "PlayerID"}, inplace=True)

    # Step 2: Load game data
    if args.from_db:
        info("🗄️ Loading games from database...")
        from .db.database import Database
        db = Database()
        games_data = db.get_all_games()
        spring_count = sum(1 for g in games_data if g.get('basic_info', {}).get('game_type') == 'spring')
        info(f"  Loaded {len(games_data)} games from database")
        if spring_count > 0:
            info(f"  Found {spring_count} spring training games")
    elif args.from_cache_only:
        info("📦 Loading games from cache only...")
        games_data, spring_count, duplicates_skipped = _load_games_from_cache(CACHE_DIR)
        if duplicates_skipped:
            info(f"  Merged {duplicates_skipped} duplicate cache alias(es)")
        if spring_count > 0:
            info(f"  Found {spring_count} spring training games")
    elif args.parallel:
        # Use parallel processing
        from .utils.parallel import process_files_parallel, default_progress_callback

        html_files = []
        if os.path.isfile(args.input_path) and args.input_path.endswith('.html'):
            html_files = [args.input_path]
        elif os.path.isdir(args.input_path):
            html_files = [
                os.path.join(args.input_path, f)
                for f in os.listdir(args.input_path)
                if f.endswith('.html')
            ]

        if html_files:
            games_data, failed_files = process_files_parallel(
                html_files,
                max_workers=args.workers,
                progress_callback=default_progress_callback if args.verbose else None
            )

            # Process umpire data from successful games
            for game_data in games_data:
                game_id = game_data.get("game_id", "UNKNOWN")
                if game_data.get("umpires"):
                    for pos, name in game_data.get("umpires", {}).items():
                        umpire_tracker.record_umpire(name, pos, game_id)

            if failed_files:
                warn(f"\n❌ Failed to process {len(failed_files)} file(s)")
                save_failed_files_report(failed_files, args.input_path)
        else:
            games_data = []
    else:
        games_data = process_directory_or_file(args.input_path, umpire_tracker)

    # Also load MLB API cached games (spring training, etc.) that don't have HTML files
    loaded_game_ids = {g.get('game_id') for g in games_data if g.get('game_id')}
    # Build date+teams index for deduplication (catches BREF vs API ID mismatches)
    loaded_game_keys = set()
    for g in games_data:
        bi = g.get('basic_info', {})
        date = bi.get('date_yyyymmdd', '')
        home = bi.get('home_team_code', '')
        away = bi.get('away_team_code', '')
        if date and home:
            loaded_game_keys.add(f"{date}_{away}_{home}")

    skip_patterns = ['career_firsts', 'career_gamelogs']
    spring_count = 0
    for cache_file in CACHE_DIR.glob("*.json"):
        if any(pattern in str(cache_file) for pattern in skip_patterns):
            continue
        try:
            with open(cache_file, 'r', encoding='utf-8') as f:
                cached_game = json.load(f)
            # Check if this is a valid game not already loaded
            if not isinstance(cached_game, dict) or 'basic_info' not in cached_game:
                continue
            game_id = cached_game.get('game_id')
            # Deduplicate by game ID and by date+teams
            bi = cached_game.get('basic_info', {})
            game_key = f"{bi.get('date_yyyymmdd', '')}_{bi.get('away_team_code', '')}_{bi.get('home_team_code', '')}"
            if game_id and game_id not in loaded_game_ids and game_key not in loaded_game_keys:
                # Only load MLB API spring training games (not regular BREF games)
                source = cached_game.get('source') or bi.get('source')
                game_type = bi.get('game_type')
                if source == 'mlb' or game_type == 'spring':
                    # Run milestone engine on API games (BREF games run it during parsing)
                    ms = cached_game.get('milestone_stats')
                    if not ms or (isinstance(ms, dict) and not any(ms.values())):
                        try:
                            from baseball_processor.engines.milestone_engine import MilestoneEngine
                            MilestoneEngine(cached_game).process()
                        except Exception:
                            pass
                    games_data.append(cached_game)
                    loaded_game_ids.add(game_id)
                    if game_type == 'spring':
                        spring_count += 1
        except (json.JSONDecodeError, IOError):
            continue
    if spring_count > 0:
        info(f"  Loaded {spring_count} spring training games from cache")

    if not games_data:
        warn("❌ No games data to process. Exiting.")
        return

    # Keep companions.csv in sync with the attended-games set so the user can
    # fill in companion names later. Skipped in quick-stats mode (no I/O).
    if not args.quick_stats:
        _sync_companions_csv(games_data)

    # Expensive maintenance path. Normal builds read the cached career-events
    # file; add_game refreshes only players from the newly added game.
    if args.refresh_career_events and not args.quick_stats:
        _refresh_career_firsts_for_games(games_data, args)

    # Quick stats mode - just print summary and exit
    if args.quick_stats:
        info("\n📊 Generating quick statistics report...")
        report = generate_quick_stats_report(games_data)
        print_quick_stats_report(report)
        return

    # Step 3: Save intermediate JSON (optional)
    if args.save_json:
        json_output = os.path.join(os.path.dirname(args.output_excel), "all_games_data.json")
        with open(json_output, 'w', encoding='utf-8') as json_file:
            json.dump(games_data, json_file, indent=2)
        info(f"💾 JSON data saved to {json_output}")

    # Step 4: Generate outputs based on flags
    try:
        if args.website_only:
            # Process data but don't write Excel file
            info("\n🌐 Website-only mode: Processing data without writing Excel...")
            
            processed_data = generate_excel_workbook(
                games_data, 
                args.output_excel,  # Still pass the path (needed for html naming)
                debut_entries, 
                hof_df,
                umpire_tracker,  # Pass the tracker
                write_file=False  # Skip Excel writing
            )
            
            # Generate website
            html_path = args.output_excel.replace('.xlsx', '.html')
            processed_data['_raw_games'] = games_data 
            generate_website_from_data(processed_data, html_path)
            
            info("\n🎉 Processing complete!")
            info(f"✅ Website: {os.path.abspath(html_path)}")

            _maybe_deploy_to_surge(html_path, args)
            _maybe_download_bref_backups(args)

        elif args.excel_only:
            # Generate only Excel
            info("\n📊 Excel-only mode: Skipping website generation...")

            processed_data = generate_excel_workbook(
                games_data, 
                args.output_excel,  # Still pass the path (needed for html naming)
                debut_entries, 
                hof_df,
                umpire_tracker,  # Pass the tracker
                write_file=True 
            )
            
            info("\n🎉 Processing complete!")
            info(f"📊 Excel: {os.path.abspath(args.output_excel)}")
            if args.save_json:
                info(f"📄 JSON: {json_output}")
        
        else:
            # Generate both (default behavior)
            info("\n📊 Generating both Excel and website...")

            processed_data = generate_excel_workbook(
                games_data, 
                args.output_excel,  # Still pass the path (needed for html naming)
                debut_entries, 
                hof_df,
                umpire_tracker,  # Pass the tracker
                write_file=True 
            )
            
            info("\n📊 Excel complete, generating website...")
            
            html_path = args.output_excel.replace('.xlsx', '.html')
            processed_data['_raw_games'] = games_data 
            generate_website_from_data(processed_data, html_path)
            
            info("\n🎉 Processing complete!")
            info(f"📊 Excel: {os.path.abspath(args.output_excel)}")
            info(f"✅ Website: {os.path.abspath(html_path)}")
            if args.save_json:
                info(f"📄 JSON: {json_output}")

            _maybe_deploy_to_surge(html_path, args)
            _maybe_download_bref_backups(args)

        # Export to CSV if requested
        if args.export_csv:
            info(f"\n📄 Exporting to CSV...")
            csv_dir = Path(args.export_csv)
            export_all_to_csv(processed_data, csv_dir)
            export_raw_games_to_csv(games_data, csv_dir / "mlb_tracker_raw_games.csv")
            info(f"✅ CSV files exported to: {csv_dir}")

        # Export shared players if requested
        if args.export_players:
            info(f"\n🔗 Exporting shared player data...")
            from .exporters.shared_players import generate_shared_export
            surge_domain = args.surge_domain or load_surge_domain()
            website_url = f"https://{surge_domain}" if surge_domain else "https://mlb-passport.surge.sh"
            export_path = generate_shared_export(processed_data, website_url=website_url)
            info(f"✅ Shared player export: {export_path}")

        # Scrape career firsts if requested
        if args.scrape_career_firsts:
            info(f"\n🔍 Scraping career firsts for players in processed games...")
            try:
                from .scrapers.career_firsts_scraper import (
                    get_players_from_games, scrape_career_firsts_for_players,
                    get_project_root, get_cache_path
                )

                # Get players from all processed games
                player_ids, player_names = get_players_from_games(get_project_root())

                if player_ids:
                    info(f"   Found {len(player_ids)} unique players")
                    info(f"   Scraping career firsts (cached players will be skipped)...")

                    cache = scrape_career_firsts_for_players(
                        player_ids,
                        refresh=False,  # Don't re-scrape cached players
                        delay=3.05,
                        verbose=args.verbose,
                        player_names=player_names
                    )

                    info(f"✅ Career firsts cache updated: {get_cache_path() / 'career_firsts.json'}")
                else:
                    warn("   No players found in games")
            except Exception as e:
                warn(f"⚠️ Career firsts scraping failed: {e}")
                info("   You can run it separately: python -m baseball_processor.scrapers.career_firsts_scraper")

    except Exception as e:
        import traceback
        traceback.print_exc()
        error(f"❌ Error during processing: {str(e)}", exc_info=True)



if __name__ == '__main__':
    main()
