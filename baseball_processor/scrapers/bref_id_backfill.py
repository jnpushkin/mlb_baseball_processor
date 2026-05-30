"""
Backfill provisional MLB-style Baseball-Reference player IDs in cached games.

Usage:
    python3 -m baseball_processor.scrapers.bref_id_backfill --dry-run
    python3 -m baseball_processor.scrapers.bref_id_backfill --player "Gage Jump"
    python3 -m baseball_processor.scrapers.bref_id_backfill --max-suffix 99
"""

import argparse
import json
from collections import defaultdict
from pathlib import Path

import baseball_processor.parsers.mlb_api_parser as mlb_api_parser
from baseball_processor.parsers.mlb_api_parser import (
    is_mlb_bref_id,
    resolve_bref_mlb_id_exhaustive_by_name,
)

CACHE_DIR = Path(__file__).parent.parent.parent / "cache"
ID_FIELDS = ("player_id", "bref_id")
PLAYER_SECTIONS = ("batting", "pitching")
SKIP_CACHE_NAMES = ("career_", "draft", "player_bios", "all_time", "known_")
PLAYER_BIOS_FILE = "player_bios.json"


def _normalize_name(name: str) -> str:
    return mlb_api_parser._normalize_bref_lookup_name(name)


def _is_game_cache_file(path: Path) -> bool:
    return path.suffix == ".json" and not any(part in path.name for part in SKIP_CACHE_NAMES)


def iter_game_cache_files(cache_dir: Path = CACHE_DIR):
    for path in sorted(cache_dir.glob("*.json")):
        if _is_game_cache_file(path):
            yield path


def iter_rewrite_cache_files(cache_dir: Path = CACHE_DIR):
    for path in sorted(cache_dir.rglob("*.json")):
        yield path


def iter_player_rows(game: dict):
    for section_name in PLAYER_SECTIONS:
        section = game.get(section_name, {})
        if not isinstance(section, dict):
            continue
        for side in ("away", "home"):
            rows = section.get(side, [])
            if not isinstance(rows, list):
                continue
            for row in rows:
                if isinstance(row, dict) and row.get("name"):
                    yield row


def id_needs_backfill(player_id: str) -> bool:
    player_id = str(player_id or "").strip()
    return bool(player_id and not is_mlb_bref_id(player_id))


def collect_backfill_candidates(game: dict, player_name: str = "") -> dict[str, set[str]]:
    target_name = _normalize_name(player_name)
    candidates = defaultdict(set)
    for row in iter_player_rows(game):
        name = str(row.get("name") or "").strip()
        if not name:
            continue
        if target_name and _normalize_name(name) != target_name:
            continue
        for field in ID_FIELDS:
            player_id = str(row.get(field) or "").strip()
            if id_needs_backfill(player_id):
                candidates[name].add(player_id)
    return dict(candidates)


def collect_bio_backfill_candidates(bios: dict, player_name: str = "") -> dict[str, set[str]]:
    target_name = _normalize_name(player_name)
    candidates = defaultdict(set)
    for player_id, bio in (bios or {}).items():
        if not isinstance(bio, dict):
            continue
        name = str(bio.get("name") or "").strip()
        if not name:
            continue
        if target_name and _normalize_name(name) != target_name:
            continue
        if id_needs_backfill(player_id):
            candidates[name].add(str(player_id))
    return dict(candidates)


def collect_cache_candidates(cache_dir: Path = CACHE_DIR, player_name: str = "") -> dict[str, set[str]]:
    candidates = defaultdict(set)
    for cache_file in iter_game_cache_files(cache_dir):
        try:
            game = json.loads(cache_file.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            continue
        for name, ids in collect_backfill_candidates(game, player_name=player_name).items():
            candidates[name].update(ids)

    bio_path = cache_dir / PLAYER_BIOS_FILE
    if bio_path.exists():
        try:
            bios = json.loads(bio_path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            bios = {}
        for name, ids in collect_bio_backfill_candidates(bios, player_name=player_name).items():
            candidates[name].update(ids)
    return dict(candidates)


def replace_id_references(value, replacements: dict[str, str]):
    """Recursively replace exact ID string values and dict keys."""
    if isinstance(value, dict):
        changed = 0
        updated = {}
        for key, item in value.items():
            new_key = replacements.get(key, key) if isinstance(key, str) else key
            new_item, item_changed = replace_id_references(item, replacements)
            changed += item_changed
            if new_key != key:
                changed += 1
            updated[new_key] = new_item
        return updated, changed

    if isinstance(value, list):
        changed = 0
        updated = []
        for item in value:
            new_item, item_changed = replace_id_references(item, replacements)
            changed += item_changed
            updated.append(new_item)
        return updated, changed

    if isinstance(value, str) and value in replacements:
        return replacements[value], 1

    return value, 0


def dump_json_preserving_style(value, original_text: str) -> str:
    stripped = original_text.lstrip()
    pretty = stripped.startswith("{\n") or stripped.startswith("[\n")
    if pretty:
        return json.dumps(value, indent=2, ensure_ascii=False) + "\n"
    return json.dumps(value, ensure_ascii=False) + "\n"


def resolve_replacements(candidates: dict[str, set[str]], max_suffix: int, verbose: bool = True) -> dict[str, str]:
    replacements = {}
    for index, (name, old_ids) in enumerate(sorted(candidates.items()), start=1):
        if verbose:
            print(f"[{index}/{len(candidates)}] Resolving {name}...", end=" ")
        new_id, source = resolve_bref_mlb_id_exhaustive_by_name(name, max_suffix=max_suffix)
        if not new_id:
            if verbose:
                print(f"no update ({source})")
            if source == "rate_limited":
                break
            continue
        for old_id in old_ids:
            if old_id != new_id:
                replacements[old_id] = new_id
        if verbose:
            old_text = ", ".join(sorted(old_ids))
            print(f"{old_text} -> {new_id} ({source})")
    return replacements


def apply_replacements(cache_dir: Path, replacements: dict[str, str], dry_run: bool = False) -> dict:
    files_changed = 0
    references_changed = 0

    for cache_file in iter_rewrite_cache_files(cache_dir):
        try:
            original_text = cache_file.read_text(encoding="utf-8")
            game = json.loads(original_text)
        except (OSError, json.JSONDecodeError):
            continue

        updated, changed = replace_id_references(game, replacements)
        if not changed:
            continue

        files_changed += 1
        references_changed += changed
        if not dry_run:
            cache_file.write_text(dump_json_preserving_style(updated, original_text), encoding="utf-8")

    return {"files_changed": files_changed, "references_changed": references_changed}


def run(
    cache_dir: Path = CACHE_DIR,
    player_name: str = "",
    max_suffix: int = 99,
    delay: float = 3.2,
    dry_run: bool = False,
    verbose: bool = True,
) -> dict:
    """Backfill cached register/MLB-placeholder IDs to MLB B-Ref IDs."""
    mlb_api_parser._BREF_PLAYER_PAGE_MIN_INTERVAL_SECONDS = delay
    candidates = collect_cache_candidates(cache_dir=cache_dir, player_name=player_name)
    if not candidates:
        if verbose:
            print("No cached player IDs need B-Ref ID backfill.")
        return {"candidates": 0, "resolved": 0, "files_changed": 0, "references_changed": 0}

    if verbose:
        print(f"Found {len(candidates)} player(s) with non-MLB-BRef IDs.\n")

    replacements = resolve_replacements(candidates, max_suffix=max_suffix, verbose=verbose)
    if not replacements:
        return {"candidates": len(candidates), "resolved": 0, "files_changed": 0, "references_changed": 0}

    result = apply_replacements(cache_dir, replacements, dry_run=dry_run)
    result.update({"candidates": len(candidates), "resolved": len(set(replacements.values()))})

    if verbose:
        mode = "would update" if dry_run else "updated"
        print(
            f"\nDone: {mode} {result['references_changed']} reference(s) "
            f"across {result['files_changed']} file(s)."
        )
    return result


def main():
    parser = argparse.ArgumentParser(description="Backfill cached player IDs to MLB-style B-Ref IDs")
    parser.add_argument("--cache-dir", type=Path, default=CACHE_DIR, help="Cache directory to scan")
    parser.add_argument("--player", default="", help="Only resolve one player name")
    parser.add_argument("--max-suffix", type=int, default=99, help="Maximum B-Ref suffix to probe")
    parser.add_argument("--delay", type=float, default=3.2, help="Delay between uncached B-Ref requests")
    parser.add_argument("--dry-run", action="store_true", help="Preview without writing cache files")
    args = parser.parse_args()

    run(
        cache_dir=args.cache_dir,
        player_name=args.player,
        max_suffix=args.max_suffix,
        delay=args.delay,
        dry_run=args.dry_run,
    )


if __name__ == "__main__":
    main()
