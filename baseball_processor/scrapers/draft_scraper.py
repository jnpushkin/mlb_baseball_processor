"""MLB draft scraper.

Pulls /api/v1/draft/{year} once per season and caches the raw response under
cache/drafts/{year}.json. Builds a flat mlb_id -> pick index used by the
first-round-pick collection view.

Past seasons are immutable (we skip them if cached); the current season's
draft picks can shift in the days right after the draft, so the current year
is always refetched.
"""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path

import requests

from ..utils.constants import CACHE_DIR
from ..utils.http import get_with_retry
from ..utils.log import info, warn

DRAFT_CACHE_DIR = Path(CACHE_DIR) / 'drafts'
DRAFT_INDEX_FILE = DRAFT_CACHE_DIR / 'index.json'

# The amateur draft started in 1965. Earlier seasons return an empty payload
# and aren't worth refetching repeatedly.
EARLIEST_DRAFT_YEAR = 1965

_session = requests.Session()
_session.headers.update({'User-Agent': 'mlb_processor/1.0'})


def _draft_url(year: int) -> str:
    return f'https://statsapi.mlb.com/api/v1/draft/{year}'


def _fetch_draft_year(year: int) -> dict | None:
    """Hit the MLB API for one season's draft. Returns the raw dict or None."""
    try:
        resp = get_with_retry(_session, _draft_url(year), timeout=20)
    except Exception as e:
        warn(f"      ⚠️  Draft {year} fetch failed: {e}")
        return None
    if resp.status_code != 200:
        warn(f"      ⚠️  Draft {year} HTTP {resp.status_code}")
        return None
    try:
        return resp.json()
    except ValueError:
        return None


def _cache_path(year: int) -> Path:
    return DRAFT_CACHE_DIR / f'{year}.json'


def _extract_picks(payload: dict, year: int) -> list[dict]:
    """Pull every numeric-round pick out of one season's payload.

    The MLB API groups picks by ``round`` string — usually "1", "2", … but
    also supplemental codes like "CB-A". We keep only the numeric rounds so
    callers can group by integer round; supplemental picks are dropped (their
    parent draft year is still represented).
    """
    picks = []
    for round_block in payload.get('drafts', {}).get('rounds', []) or []:
        raw_round = round_block.get('round')
        try:
            round_num = int(str(raw_round))
        except (TypeError, ValueError):
            continue
        for pick in round_block.get('picks', []) or []:
            person = pick.get('person') or {}
            mlb_id = person.get('id')
            if not mlb_id:
                continue
            round_pick = pick.get('roundPickNumber')
            if not isinstance(round_pick, int) or round_pick < 1:
                continue
            # Round 1 had at most ~40 picks even in compensation-heavy years.
            # Anything higher is the API mistagging a phase-2/supplemental
            # pick as round 1 (e.g., 1969 phase 2, 2002 sup).
            if round_num == 1 and round_pick > 40:
                continue
            team = pick.get('team') or {}
            school = pick.get('school') or {}
            picks.append({
                'mlb_id': int(mlb_id),
                'year': year,
                'round': round_num,
                'roundPick': round_pick,
                'overallPick': pick.get('pickNumber'),
                'fullName': person.get('fullName') or '',
                'team': team.get('name') or team.get('abbreviation') or '',
                'teamAbbrev': team.get('abbreviation') or '',
                'school': school.get('name') or '',
                'schoolClass': pick.get('schoolClass') or '',
                'signingBonus': pick.get('signingBonus'),
            })
    return picks


def update_drafts(years: list[int] | None = None, verbose: bool = True) -> int:
    """Ensure each year in ``years`` (default: 1965..current) is cached.

    Past years are skipped if already on disk; the current season is always
    refetched in case picks were added or revised. Returns the number of
    seasons newly fetched.
    """
    if years is None:
        current = datetime.now().year
        years = list(range(EARLIEST_DRAFT_YEAR, current + 1))

    DRAFT_CACHE_DIR.mkdir(parents=True, exist_ok=True)
    current_year = datetime.now().year

    fetched = 0
    skipped_cached = 0
    failed = []
    for year in years:
        path = _cache_path(year)
        if path.exists() and year != current_year:
            skipped_cached += 1
            continue
        payload = _fetch_draft_year(year)
        if payload is None:
            failed.append(year)
            continue
        path.write_text(json.dumps(payload))
        fetched += 1

    if verbose:
        msg = f"  📋 Draft cache: fetched {fetched}, kept {skipped_cached}"
        if failed:
            msg += f", failed {failed}"
        info(msg)

    rebuild_index(verbose=verbose)
    return fetched


def rebuild_index(verbose: bool = True) -> dict:
    """Walk every cached season and produce mlb_id -> pick dict.

    The index is what the serializer reads; it lets us answer "did the user
    see pick #N from any year" in O(1) once the player set is in memory.
    """
    DRAFT_CACHE_DIR.mkdir(parents=True, exist_ok=True)
    index = {}
    years_loaded = 0
    for path in sorted(DRAFT_CACHE_DIR.glob('*.json')):
        if path.name == 'index.json':
            continue
        try:
            year = int(path.stem)
        except ValueError:
            continue
        try:
            payload = json.loads(path.read_text())
        except Exception as e:
            warn(f"      ⚠️  Could not read {path.name}: {e}")
            continue
        for pick in _extract_picks(payload, year):
            # Keep the earliest (lowest round, lowest pick) entry if a player
            # somehow appears twice — shouldn't happen since you're only
            # drafted once, but defensive against API hiccups.
            key = str(pick['mlb_id'])
            prior = index.get(key)
            if prior is None or (pick['round'], pick['roundPick']) < (prior['round'], prior['roundPick']):
                index[key] = pick
        years_loaded += 1

    DRAFT_INDEX_FILE.write_text(json.dumps(index))
    if verbose:
        round_1 = sum(1 for p in index.values() if p.get('round') == 1)
        info(f"  📋 Draft index: {len(index):,} picks ({round_1:,} in round 1) across {years_loaded} seasons")
    return index


def load_index() -> dict:
    """Return the mlb_id -> first-round-pick index, building it if missing."""
    if DRAFT_INDEX_FILE.exists():
        try:
            return json.loads(DRAFT_INDEX_FILE.read_text())
        except Exception:
            pass
    return rebuild_index(verbose=False)


if __name__ == '__main__':
    import argparse
    p = argparse.ArgumentParser(description='Cache MLB draft picks (strict round 1)')
    p.add_argument('--year', type=int, help='Just refresh this year')
    p.add_argument('--rebuild-index', action='store_true', help='Rebuild the mlb_id -> pick index from cached payloads (no network)')
    args = p.parse_args()
    if args.rebuild_index:
        rebuild_index()
    elif args.year:
        update_drafts(years=[args.year])
    else:
        update_drafts()
