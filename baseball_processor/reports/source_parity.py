"""Offline source parity checks for normalized cached games."""

from __future__ import annotations

import argparse
import csv
import json
import re
import unicodedata
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from ..utils.constants import CACHE_DIR, STADIUM_ALIASES
from ..utils.helpers import standardize_team_code, unify_team_code


SKIP_CACHE_PATTERNS = ("career_firsts", "career_gamelogs", "player_bios")

METADATA_FIELDS = (
    "date_yyyymmdd",
    "away_team",
    "home_team",
    "away_team_code",
    "home_team_code",
    "away_score_value",
    "home_score_value",
    "venue",
    "game_type",
)

BATTING_FIELDS = (
    "player_id",
    "team",
    "AB",
    "H",
    "R",
    "RBI",
    "BB",
    "SO",
    "SB",
    "2B",
    "3B",
    "HR",
)

BATTING_FIELD_ALIASES = {
    "player_id": ("player_id", "Player ID", "playerId"),
    "team": ("team", "Team", "team_code", "Team Code"),
    "AB": ("AB",),
    "H": ("H",),
    "R": ("R",),
    "RBI": ("RBI",),
    "BB": ("BB",),
    "SO": ("SO", "K"),
    "SB": ("SB",),
    "2B": ("2B", "doubles"),
    "3B": ("3B", "triples"),
    "HR": ("HR", "homeRuns"),
}

PITCHING_FIELDS = (
    "player_id",
    "team",
    "IP",
    "H",
    "R",
    "ER",
    "BB",
    "SO",
    "HR",
    "decision",
    "pitches",
    "strikes",
    "batters_faced",
)

PITCHING_FIELD_ALIASES = {
    "player_id": ("player_id", "Player ID", "playerId"),
    "team": ("team", "Team", "team_code", "Team Code"),
    "IP": ("IP", "inningsPitched"),
    "H": ("H", "hits"),
    "R": ("R", "runs"),
    "ER": ("ER", "earnedRuns"),
    "BB": ("BB", "baseOnBalls"),
    "SO": ("SO", "K", "strikeOuts"),
    "HR": ("HR", "homeRuns"),
    "decision": ("decision", "Decision"),
    "pitches": ("pitches", "Pitches", "numberOfPitches"),
    "strikes": ("strikes", "Strikes"),
    "batters_faced": ("batters_faced", "BF", "battersFaced"),
}


@dataclass(frozen=True)
class CacheGameRecord:
    cache_file: Path
    game: dict[str, Any]

    @property
    def game_id(self) -> str:
        return str(self.game.get("game_id") or "")

    @property
    def basic_info(self) -> dict[str, Any]:
        basic = self.game.get("basic_info")
        return basic if isinstance(basic, dict) else {}

    @property
    def source(self) -> str:
        return canonical_source(self.game)


def canonical_source(game: dict[str, Any]) -> str:
    basic = game.get("basic_info") if isinstance(game.get("basic_info"), dict) else {}
    source = game.get("source") or basic.get("source") or ""
    return str(source).strip().lower()


def is_api_source(source: str) -> bool:
    return source == "mlb" or source.startswith("mlb_")


def load_cache_game_records(cache_dir: Path = CACHE_DIR) -> list[CacheGameRecord]:
    records = []
    for cache_file in sorted(Path(cache_dir).glob("*.json")):
        if any(pattern in cache_file.name for pattern in SKIP_CACHE_PATTERNS):
            continue

        try:
            with cache_file.open("r", encoding="utf-8") as handle:
                game = json.load(handle)
        except (json.JSONDecodeError, OSError):
            continue

        if isinstance(game, dict) and isinstance(game.get("basic_info"), dict):
            records.append(CacheGameRecord(cache_file=cache_file, game=game))

    return records


def infer_source_label(record: CacheGameRecord) -> str | None:
    if record.source:
        return record.source

    filename = record.cache_file.name.lower()
    if "baseball-reference" in filename or "box_score" in filename:
        return "bref"
    if "spring_training" in filename and record.game.get("source") == "pdf":
        return "pdf"
    return None


def backfill_missing_source_labels(cache_dir: Path = CACHE_DIR, dry_run: bool = True) -> dict[str, Any]:
    records = load_cache_game_records(cache_dir)
    candidates = []
    skipped = []

    for record in records:
        if record.source:
            continue

        inferred_source = infer_source_label(record)
        if inferred_source:
            candidates.append((record, inferred_source))
        else:
            skipped.append(str(record.cache_file))

    if not dry_run:
        for record, inferred_source in candidates:
            game = record.game
            basic = game.setdefault("basic_info", {})
            game["source"] = inferred_source
            basic["source"] = inferred_source
            with record.cache_file.open("w", encoding="utf-8") as handle:
                json.dump(game, handle, indent=2, ensure_ascii=False)
                handle.write("\n")

    return {
        "dry_run": dry_run,
        "updated": 0 if dry_run else len(candidates),
        "would_update": len(candidates),
        "skipped": skipped,
    }


def iter_api_other_pairs(records: list[CacheGameRecord]):
    by_game_id: dict[str, list[CacheGameRecord]] = {}
    for record in records:
        if not record.game_id:
            continue
        by_game_id.setdefault(record.game_id, []).append(record)

    for game_id, grouped in sorted(by_game_id.items()):
        if len(grouped) < 2:
            continue

        api_records = [record for record in grouped if is_api_source(record.source)]
        other_records = [record for record in grouped if not is_api_source(record.source)]
        if not api_records or not other_records:
            continue

        for api_record in api_records:
            for other_record in other_records:
                yield api_record, other_record


def _metadata_value(record: CacheGameRecord, field: str):
    return record.basic_info.get(field)


def _is_missing(value) -> bool:
    return value is None or str(value).strip() == ""


def _normalize_text(value):
    if _is_missing(value):
        return None
    text = unicodedata.normalize("NFKD", str(value))
    text = "".join(char for char in text if not unicodedata.combining(char))
    return re.sub(r"\s+", " ", text.strip()).lower()


def _normalize_team_code(value):
    if _is_missing(value):
        return None
    return unify_team_code(str(value).strip().upper())


def _normalize_team_name(value):
    if _is_missing(value):
        return None
    code = standardize_team_code(str(value).strip())
    normalized_code = _normalize_team_code(code)
    return normalized_code if normalized_code else _normalize_text(value)


def _normalize_stadium(value):
    normalized = _normalize_text(value)
    if normalized is None:
        return None
    for canonical, aliases in STADIUM_ALIASES.items():
        if normalized == _normalize_text(canonical):
            return _normalize_text(canonical)
        for alias in aliases:
            if normalized == _normalize_text(alias):
                return _normalize_text(canonical)
    return normalized


def _normalize_int(value):
    if _is_missing(value):
        return None
    try:
        return int(value)
    except (TypeError, ValueError):
        return _normalize_text(value)


def _normalize_metadata(field: str, value):
    if field.endswith("_score_value"):
        return _normalize_int(value)
    if field.endswith("_team_code"):
        return _normalize_team_code(value)
    if field in {"away_team", "home_team"}:
        return _normalize_team_name(value)
    if field == "venue":
        return _normalize_stadium(value)
    return _normalize_text(value)


def _normalize_name(value):
    text = _normalize_text(value)
    if text is None:
        return None
    text = text.replace(".", "").replace("'", "").replace("’", "").replace("-", " ")
    return re.sub(r"\s+", " ", text).strip()


def _row_field(row: dict[str, Any], field: str):
    for alias in BATTING_FIELD_ALIASES.get(field, (field,)):
        if alias in row:
            return True, row.get(alias)
    return False, None


def _pitching_row_field(row: dict[str, Any], field: str):
    for alias in PITCHING_FIELD_ALIASES.get(field, (field,)):
        if alias in row:
            return True, row.get(alias)
    return False, None


def _row_player_id(row: dict[str, Any]) -> str:
    present, value = _row_field(row, "player_id")
    if not present or _is_missing(value):
        return ""
    return str(value).strip().lower()


def _pitcher_player_id(row: dict[str, Any]) -> str:
    present, value = _pitching_row_field(row, "player_id")
    if not present or _is_missing(value):
        return ""
    return str(value).strip().lower()


def _row_name(row: dict[str, Any]) -> str:
    return _normalize_name(row.get("name") or row.get("Name") or "") or ""


def _normalize_batting_field(field: str, value):
    if field in {"AB", "H", "R", "RBI", "BB", "SO", "SB", "2B", "3B", "HR"}:
        return _normalize_int(value)
    if field == "team":
        return _normalize_team_code(value)
    if field == "player_id":
        return _normalize_text(value)
    return _normalize_text(value)


def _normalize_ip(value):
    if _is_missing(value):
        return None
    text = str(value).strip()
    if "." not in text:
        text = f"{text}.0"
    return text


def _normalize_pitching_field(field: str, value):
    if field == "IP":
        return _normalize_ip(value)
    if field in {"H", "R", "ER", "BB", "SO", "HR", "pitches", "strikes", "batters_faced"}:
        return _normalize_int(value)
    if field == "team":
        return _normalize_team_code(value)
    if field == "player_id":
        return _normalize_text(value)
    return _normalize_text(value)


def compare_metadata_records(
    api_record: CacheGameRecord,
    other_record: CacheGameRecord,
) -> list[dict[str, Any]]:
    """Compare metadata fields for one API/non-API cache pair."""
    issues = []

    if not api_record.source:
        issues.append(_source_issue(api_record, other_record, "api"))
    if not other_record.source:
        issues.append(_source_issue(api_record, other_record, "other"))

    for field in METADATA_FIELDS:
        api_value = _metadata_value(api_record, field)
        other_value = _metadata_value(other_record, field)
        api_norm = _normalize_metadata(field, api_value)
        other_norm = _normalize_metadata(field, other_value)

        if api_norm is None or other_norm is None:
            if api_norm != other_norm:
                issues.append(
                    _metadata_issue(
                        api_record,
                        other_record,
                        kind="missing_metadata_field",
                        field=field,
                        api_value=api_value,
                        other_value=other_value,
                    )
                )
            continue

        if api_norm != other_norm:
            issues.append(
                _metadata_issue(
                    api_record,
                    other_record,
                    kind="metadata_mismatch",
                    field=field,
                    api_value=api_value,
                    other_value=other_value,
                )
            )

    return issues


def collect_metadata_parity_issues(records: list[CacheGameRecord]) -> list[dict[str, Any]]:
    """Compare API cache records against same-game non-API records."""
    issues = []
    for api_record, other_record in iter_api_other_pairs(records):
        issues.extend(compare_metadata_records(api_record, other_record))
    return issues


def compare_batting_records(
    api_record: CacheGameRecord,
    other_record: CacheGameRecord,
) -> list[dict[str, Any]]:
    issues = []
    for side in ("away", "home"):
        api_rows = api_record.game.get("batting", {}).get(side, []) or []
        other_rows = other_record.game.get("batting", {}).get(side, []) or []
        issues.extend(_compare_batting_side(api_record, other_record, side, api_rows, other_rows))
    return issues


def _compare_batting_side(api_record, other_record, side, api_rows, other_rows):
    issues = []
    matched_other_indexes = set()

    for api_row in api_rows:
        match_index = _find_matching_batter(api_row, other_rows, matched_other_indexes)
        if match_index is None:
            issues.append(
                _row_issue(
                    api_record,
                    other_record,
                    kind="missing_batter_row",
                    side=side,
                    player=api_row.get("name") or api_row.get("Name") or "",
                    field="row",
                    api_value="present",
                    other_value="missing",
                )
            )
            continue

        matched_other_indexes.add(match_index)
        other_row = other_rows[match_index]
        for field in BATTING_FIELDS:
            issues.extend(_compare_batting_field(api_record, other_record, side, api_row, other_row, field))

    for index, other_row in enumerate(other_rows):
        if index in matched_other_indexes:
            continue
        issues.append(
            _row_issue(
                api_record,
                other_record,
                kind="extra_batter_row",
                side=side,
                player=other_row.get("name") or other_row.get("Name") or "",
                field="row",
                api_value="missing",
                other_value="present",
            )
        )

    return issues


def _find_matching_batter(api_row, other_rows, matched_other_indexes):
    api_player_id = _row_player_id(api_row)
    if api_player_id:
        for index, other_row in enumerate(other_rows):
            if index in matched_other_indexes:
                continue
            if _row_player_id(other_row) == api_player_id:
                return index

    api_name = _row_name(api_row)
    if api_name:
        for index, other_row in enumerate(other_rows):
            if index in matched_other_indexes:
                continue
            if _row_name(other_row) == api_name:
                return index

    return None


def _compare_batting_field(api_record, other_record, side, api_row, other_row, field):
    api_present, api_value = _row_field(api_row, field)
    other_present, other_value = _row_field(other_row, field)
    api_norm = _normalize_batting_field(field, api_value)
    other_norm = _normalize_batting_field(field, other_value)
    player = api_row.get("name") or api_row.get("Name") or other_row.get("name") or other_row.get("Name") or ""

    if not api_present or not other_present:
        if api_present != other_present or api_norm != other_norm:
            return [
                _row_issue(
                    api_record,
                    other_record,
                    kind="missing_batting_field",
                    side=side,
                    player=player,
                    field=field,
                    api_value=api_value if api_present else "missing",
                    other_value=other_value if other_present else "missing",
                )
            ]
        return []

    if api_norm != other_norm:
        return [
            _row_issue(
                api_record,
                other_record,
                kind="batting_mismatch",
                side=side,
                player=player,
                field=field,
                api_value=api_value,
                other_value=other_value,
            )
        ]

    return []


def collect_batting_parity_issues(records: list[CacheGameRecord]) -> list[dict[str, Any]]:
    issues = []
    for api_record, other_record in iter_api_other_pairs(records):
        issues.extend(compare_batting_records(api_record, other_record))
    return issues


def compare_pitching_records(
    api_record: CacheGameRecord,
    other_record: CacheGameRecord,
) -> list[dict[str, Any]]:
    issues = []
    for side in ("away", "home"):
        api_rows = api_record.game.get("pitching", {}).get(side, []) or []
        other_rows = other_record.game.get("pitching", {}).get(side, []) or []
        issues.extend(_compare_pitching_side(api_record, other_record, side, api_rows, other_rows))
    return issues


def _compare_pitching_side(api_record, other_record, side, api_rows, other_rows):
    issues = []
    matched_other_indexes = set()

    for api_row in api_rows:
        match_index = _find_matching_pitcher(api_row, other_rows, matched_other_indexes)
        if match_index is None:
            issues.append(
                _row_issue(
                    api_record,
                    other_record,
                    kind="missing_pitcher_row",
                    side=side,
                    player=api_row.get("name") or api_row.get("Name") or "",
                    field="row",
                    api_value="present",
                    other_value="missing",
                )
            )
            continue

        matched_other_indexes.add(match_index)
        other_row = other_rows[match_index]
        for field in PITCHING_FIELDS:
            issues.extend(_compare_pitching_field(api_record, other_record, side, api_row, other_row, field))

    for index, other_row in enumerate(other_rows):
        if index in matched_other_indexes:
            continue
        issues.append(
            _row_issue(
                api_record,
                other_record,
                kind="extra_pitcher_row",
                side=side,
                player=other_row.get("name") or other_row.get("Name") or "",
                field="row",
                api_value="missing",
                other_value="present",
            )
        )

    return issues


def _find_matching_pitcher(api_row, other_rows, matched_other_indexes):
    api_player_id = _pitcher_player_id(api_row)
    if api_player_id:
        for index, other_row in enumerate(other_rows):
            if index in matched_other_indexes:
                continue
            if _pitcher_player_id(other_row) == api_player_id:
                return index

    api_name = _row_name(api_row)
    if api_name:
        for index, other_row in enumerate(other_rows):
            if index in matched_other_indexes:
                continue
            if _row_name(other_row) == api_name:
                return index

    return None


def _compare_pitching_field(api_record, other_record, side, api_row, other_row, field):
    api_present, api_value = _pitching_row_field(api_row, field)
    other_present, other_value = _pitching_row_field(other_row, field)
    api_norm = _normalize_pitching_field(field, api_value)
    other_norm = _normalize_pitching_field(field, other_value)
    player = api_row.get("name") or api_row.get("Name") or other_row.get("name") or other_row.get("Name") or ""

    if not api_present or not other_present:
        if api_present != other_present or api_norm != other_norm:
            return [
                _row_issue(
                    api_record,
                    other_record,
                    kind="missing_pitching_field",
                    side=side,
                    player=player,
                    field=field,
                    api_value=api_value if api_present else "missing",
                    other_value=other_value if other_present else "missing",
                )
            ]
        return []

    if api_norm != other_norm:
        return [
            _row_issue(
                api_record,
                other_record,
                kind="pitching_mismatch",
                side=side,
                player=player,
                field=field,
                api_value=api_value,
                other_value=other_value,
            )
        ]

    return []


def collect_pitching_parity_issues(records: list[CacheGameRecord]) -> list[dict[str, Any]]:
    issues = []
    for api_record, other_record in iter_api_other_pairs(records):
        issues.extend(compare_pitching_records(api_record, other_record))
    return issues


def collect_source_parity_issues(records: list[CacheGameRecord], checks=("metadata", "batting", "pitching")):
    issues = []
    if "metadata" in checks:
        issues.extend(collect_metadata_parity_issues(records))
    if "batting" in checks:
        issues.extend(collect_batting_parity_issues(records))
    if "pitching" in checks:
        issues.extend(collect_pitching_parity_issues(records))
    return issues


def generate_source_parity_report(cache_dir: Path = CACHE_DIR, checks=("metadata", "batting", "pitching")) -> dict[str, Any]:
    records = load_cache_game_records(cache_dir)
    issues = collect_source_parity_issues(records, checks=checks)
    paired_game_ids = {
        issue["game_id"]
        for issue in issues
    }
    return {
        "records_checked": len(records),
        "paired_games_with_issues": len(paired_game_ids),
        "issues": issues,
    }


def _source_issue(api_record: CacheGameRecord, other_record: CacheGameRecord, side: str):
    record = api_record if side == "api" else other_record
    return {
        "kind": "missing_source_label",
        "game_id": api_record.game_id,
        "field": "source",
        "api_file": str(api_record.cache_file),
        "other_file": str(other_record.cache_file),
        "api_source": api_record.source,
        "other_source": other_record.source,
        "api_value": api_record.source,
        "other_value": other_record.source,
        "message": f"{record.cache_file.name} is missing a canonical source label.",
    }


def _row_issue(
    api_record: CacheGameRecord,
    other_record: CacheGameRecord,
    kind: str,
    side: str,
    player: str,
    field: str,
    api_value,
    other_value,
):
    return {
        "kind": kind,
        "game_id": api_record.game_id,
        "side": side,
        "player": player,
        "field": field,
        "api_file": str(api_record.cache_file),
        "other_file": str(other_record.cache_file),
        "api_source": api_record.source,
        "other_source": other_record.source,
        "api_value": api_value,
        "other_value": other_value,
        "message": (
            f"{api_record.game_id} {side} batter {player or '?'} {field}: "
            f"API has {api_value!r}, comparison cache has {other_value!r}."
        ),
    }


def _metadata_issue(
    api_record: CacheGameRecord,
    other_record: CacheGameRecord,
    kind: str,
    field: str,
    api_value,
    other_value,
):
    return {
        "kind": kind,
        "game_id": api_record.game_id,
        "field": field,
        "api_file": str(api_record.cache_file),
        "other_file": str(other_record.cache_file),
        "api_source": api_record.source,
        "other_source": other_record.source,
        "api_value": api_value,
        "other_value": other_value,
        "message": (
            f"{api_record.game_id} {field}: API has {api_value!r}, "
            f"comparison cache has {other_value!r}."
        ),
    }


def write_issues_csv(issues: list[dict[str, Any]], output_path: Path) -> None:
    fieldnames = [
        "kind",
        "game_id",
        "field",
        "side",
        "player",
        "api_source",
        "other_source",
        "api_value",
        "other_value",
        "api_file",
        "other_file",
        "message",
    ]
    with Path(output_path).open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        for issue in issues:
            writer.writerow({field: issue.get(field, "") for field in fieldnames})


def main() -> None:
    parser = argparse.ArgumentParser(description="Check cached API/BREF source parity offline.")
    parser.add_argument("--cache-dir", type=Path, default=CACHE_DIR, help="Cache directory to scan")
    parser.add_argument(
        "--checks",
        choices=("metadata", "batting", "pitching", "all"),
        default="all",
        help="Which offline parity checks to run",
    )
    parser.add_argument("--csv", type=Path, help="Optional CSV output path for issue detail")
    parser.add_argument(
        "--backfill-source-labels",
        action="store_true",
        help="Infer missing cache source labels and write them with --apply",
    )
    parser.add_argument(
        "--apply",
        action="store_true",
        help="Apply a requested cache backfill; otherwise backfills run as dry-runs",
    )
    args = parser.parse_args()

    if args.backfill_source_labels:
        result = backfill_missing_source_labels(args.cache_dir, dry_run=not args.apply)
        action = "Would update" if result["dry_run"] else "Updated"
        print(f"{action} {result['would_update']} cached game record(s) with inferred source labels.")
        if result["skipped"]:
            print(f"Skipped {len(result['skipped'])} unlabeled record(s) without a safe inference.")
        return

    checks = ("metadata", "batting", "pitching") if args.checks == "all" else (args.checks,)
    report = generate_source_parity_report(args.cache_dir, checks=checks)
    issues = report["issues"]

    print(f"Scanned {report['records_checked']} cached game record(s).")
    if not issues:
        print("No API-vs-non-API parity issues found.")
        return

    print(
        f"Found {len(issues)} parity issue(s) "
        f"across {report['paired_games_with_issues']} paired game(s)."
    )
    for issue in issues[:20]:
        print(f"- {issue['message']}")
    if len(issues) > 20:
        print(f"- ... {len(issues) - 20} more")

    if args.csv:
        write_issues_csv(issues, args.csv)
        print(f"Wrote issue detail to {args.csv}")


if __name__ == "__main__":
    main()
