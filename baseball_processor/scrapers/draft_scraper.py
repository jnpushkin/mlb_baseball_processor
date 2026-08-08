"""MLB draft scraper.

Pulls /api/v1/draft/{year} once per season and caches the raw response under
cache/drafts/{year}.json. Builds a flat mlb_id -> draft history index used by
the draft-pick collection view.

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
FIRST_ROUND_BAND_OVERALL_PICK_LIMIT = 100

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


def _parse_numeric_round(raw_round) -> int | None:
    try:
        round_num = int(str(raw_round))
    except (TypeError, ValueError):
        return None
    return round_num if round_num > 0 else None


def _normalized_round_pick_slots(raw_picks: list[dict]) -> list[int]:
    """Return fallback within-round slots for older odd MLB draft payloads.

    Some historical years have ``roundPickNumber`` values that do not reset
    inside a numeric round. In those cases, use the position inside each
    contiguous overall-pick run; 2002 round 23, for example, has one stray
    phase pick followed by the normal round run.
    """
    slots = []
    previous_overall = None
    slot = 0
    for index, pick in enumerate(raw_picks):
        overall = pick.get('pickNumber')
        if isinstance(overall, int):
            if previous_overall is None or overall != previous_overall + 1:
                slot = 1
            else:
                slot += 1
            previous_overall = overall
        else:
            slot = index + 1
            previous_overall = None
        slots.append(slot)
    return slots


def _round_pick_for_numeric_round(pick: dict, fallback_slot: int, block_size: int) -> int | None:
    api_round_pick = pick.get('roundPickNumber')
    if isinstance(api_round_pick, int) and 1 <= api_round_pick <= block_size:
        return api_round_pick
    return fallback_slot if fallback_slot >= 1 else None


def _draft_sort_key(pick: dict) -> tuple:
    overall = pick.get('overallPick')
    if not isinstance(overall, int) or overall < 1:
        overall = 99999
    year = pick.get('year')
    if not isinstance(year, int):
        year = 99999
    round_num = pick.get('round')
    if not isinstance(round_num, int):
        round_num = 999
    round_pick = pick.get('roundPick')
    if not isinstance(round_pick, int):
        round_pick = 999
    return (overall, round_num, round_pick, year)


def _player_identity_from_drafts(drafts: list[dict]) -> dict:
    primary = min(drafts, key=_draft_sort_key)
    entry = dict(primary)
    entry['primaryDraft'] = primary
    entry['drafts'] = sorted(drafts, key=lambda p: (p.get('year') or 0, p.get('overallPick') or 99999))
    return entry


def _extract_picks(payload: dict, year: int) -> list[dict]:
    """Pull displayable draft picks out of one season's payload.

    The MLB API groups picks by ``round`` string: usually "1", "2", ... but
    also supplemental codes like "C-1", "CB-A", and "PPI". Numeric rounds are
    kept as their integer round. Supplemental rounds before round 2 are grouped
    with round 1 so compensation picks such as "C-1" #36 can appear in the
    first-round collection.
    """
    picks = []
    in_first_round_band = True
    for round_block in payload.get('drafts', {}).get('rounds', []) or []:
        raw_round = round_block.get('round')
        raw_round_label = str(raw_round or '').strip()
        numeric_round = _parse_numeric_round(raw_round)
        if numeric_round and numeric_round > 1:
            in_first_round_band = False
        if numeric_round:
            round_num = numeric_round
        elif in_first_round_band:
            round_num = 1
        else:
            round_num = None

        raw_picks = round_block.get('picks', []) or []
        fallback_slots = _normalized_round_pick_slots(raw_picks)
        block_size = len(raw_picks)
        for index, pick in enumerate(raw_picks):
            person = pick.get('person') or {}
            mlb_id = person.get('id')
            if not mlb_id:
                continue
            overall_pick = pick.get('pickNumber')
            plausible_first_round_pick = (
                in_first_round_band
                and isinstance(overall_pick, int)
                and 1 <= overall_pick <= FIRST_ROUND_BAND_OVERALL_PICK_LIMIT
            )
            if in_first_round_band and isinstance(overall_pick, int) and overall_pick > FIRST_ROUND_BAND_OVERALL_PICK_LIMIT:
                continue
            first_round_pick = overall_pick if plausible_first_round_pick else None
            if numeric_round:
                round_pick = _round_pick_for_numeric_round(
                    pick,
                    fallback_slots[index] if index < len(fallback_slots) else index + 1,
                    block_size,
                )
            elif first_round_pick:
                round_pick = first_round_pick
            else:
                round_pick = None
            if round_num is not None and (not isinstance(round_pick, int) or round_pick < 1):
                continue
            team = pick.get('team') or {}
            school = pick.get('school') or {}
            picks.append({
                'mlb_id': int(mlb_id),
                'year': year,
                'round': round_num,
                'rawRound': raw_round_label,
                'roundLabel': raw_round_label,
                'roundPick': round_pick,
                'blockPick': pick.get('roundPickNumber'),
                'apiRoundPick': pick.get('roundPickNumber'),
                'firstRoundPick': first_round_pick,
                'isFirstRoundBand': bool(in_first_round_band),
                'overallPick': overall_pick,
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
    """Walk every cached season and produce mlb_id -> draft history dict.

    The index is what the serializer reads; it lets us answer "did the user
    see pick #N from any year" in O(1) once the player set is in memory, while
    preserving players who were drafted more than once.
    """
    DRAFT_CACHE_DIR.mkdir(parents=True, exist_ok=True)
    drafts_by_player = {}
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
            key = str(pick['mlb_id'])
            player_drafts = drafts_by_player.setdefault(key, [])
            identity = (pick.get('year'), pick.get('rawRound'), pick.get('overallPick'))
            if not any((p.get('year'), p.get('rawRound'), p.get('overallPick')) == identity for p in player_drafts):
                player_drafts.append(pick)
        years_loaded += 1

    index = {key: _player_identity_from_drafts(drafts) for key, drafts in drafts_by_player.items() if drafts}
    DRAFT_INDEX_FILE.write_text(json.dumps(index))
    if verbose:
        draft_count = sum(len(p.get('drafts') or [p]) for p in index.values())
        round_1 = sum(
            1
            for player in index.values()
            for pick in (player.get('drafts') or [player])
            if pick.get('isFirstRoundBand')
        )
        info(f"  📋 Draft index: {len(index):,} players, {draft_count:,} picks ({round_1:,} in first-round band) across {years_loaded} seasons")
    return index


def load_index() -> dict:
    """Return the mlb_id -> draft history index, building it if missing."""
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
