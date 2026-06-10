"""Compare API cache records against local BREF HTML backups.

The API cache remains the source of truth. This report parses BREF backups in
memory and flags differences in fields that affect the website or milestone
counts, without writing competing BREF cache JSON files.
"""

from __future__ import annotations

import argparse
import contextlib
import copy
import csv
import io
import json
import re
import unicodedata
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any

from ..engines.milestone_engine import MilestoneEngine
from ..engines.special_events_engine import SpecialEventsEngine
from ..parsers.html_parser import parse_baseball_reference_boxscore
from ..parsers.mlb_api_parser import normalize_api_batting_rows
from ..processors.milestones_processor import MilestonesProcessor
from ..scrapers.download_bref import HTML_DIR, TEAM_FULL_NAMES, expected_html_filename
from ..utils.constants import BASE_DIR, CACHE_DIR, STADIUM_ALIASES
from ..utils.helpers import unify_team_code


REPORT_DIR = BASE_DIR / "reports"
DEFAULT_REPORT_PATH = REPORT_DIR / "api_bref_discrepancies.csv"

SKIP_CACHE_PATTERNS = ("career_firsts", "career_gamelogs", "player_bios", "career_highs")
METADATA_FIELDS = (
    "date_yyyymmdd",
    "away_team_code",
    "home_team_code",
    "away_score_value",
    "home_score_value",
    "venue",
    "game_type",
)
BATTING_FIELDS = ("AB", "H", "R", "RBI", "BB", "SO")
PITCHING_FIELDS = ("IP", "H", "R", "ER", "BB", "SO", "HR")
MILESTONE_CATEGORIES = (
    "Walk-Offs",
    "Grand Slams",
    "Leadoff HRs",
    "Pinch Hit HRs",
    "3+ HR Games",
    "Multi-HR Games",
    "5+ Hit Games",
    "4+ Hit Games",
    "6+ RBI Games",
    "5+ RBI Games",
    "4+ RBI Games",
    "Multi-SB Games",
    "Golden Sombreros",
    "4+ Run Games",
    "8+ Total Bases",
    "Wins",
    "Saves",
    "Complete Games & Shutouts",
    "Two-Hitters",
    "12+ K Games",
    "10+ K Games",
    "Immaculate Innings",
    "3 Strikeout Innings",
    "Consecutive HR Instances",
)


def is_api_game(game: dict[str, Any]) -> bool:
    basic = game.get("basic_info") if isinstance(game.get("basic_info"), dict) else {}
    source = str(game.get("source") or basic.get("source") or "").lower()
    return source == "mlb" or source.startswith("mlb_")


def find_bref_html_for_game(game: dict[str, Any], html_dir: Path = HTML_DIR) -> Path | None:
    basic = game.get("basic_info", {})
    away = basic.get("away_team_code", "")
    home = basic.get("home_team_code", "")
    date_str = basic.get("date_yyyymmdd", "")
    if not away or not home or len(date_str) != 8:
        return None

    expected = Path(html_dir) / expected_html_filename(away, home, date_str)
    if expected.exists():
        return expected

    year = int(date_str[:4])
    month = int(date_str[4:6])
    day = int(date_str[6:8])
    month_name = datetime(year, month, day).strftime("%B")
    away_name = TEAM_FULL_NAMES.get(away, away)
    home_name = TEAM_FULL_NAMES.get(home, home)

    for path in Path(html_dir).glob(f"*{month_name}*{day}*{year}*.html"):
        name = path.name
        if away_name in name and home_name in name:
            return path
        if away in name and home in name:
            return path
    return None


def load_api_cache_games(cache_dir: Path = CACHE_DIR, recent_days: int | None = None) -> list[tuple[Path, dict[str, Any]]]:
    cutoff = None
    if recent_days is not None:
        cutoff = (datetime.now() - timedelta(days=recent_days)).strftime("%Y%m%d")

    records = []
    for cache_file in sorted(Path(cache_dir).glob("*.json")):
        if any(pattern in cache_file.name for pattern in SKIP_CACHE_PATTERNS):
            continue
        try:
            game = json.loads(cache_file.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            continue
        if not isinstance(game, dict) or not is_api_game(game):
            continue
        basic = game.get("basic_info", {})
        if basic.get("game_type", "regular") not in ("regular", "postseason"):
            continue
        if cutoff and str(basic.get("date_yyyymmdd", "")) < cutoff:
            continue
        records.append((cache_file, game))
    return records


def _prepare_api_game(game: dict[str, Any]) -> dict[str, Any]:
    prepared = copy.deepcopy(game)
    normalize_api_batting_rows(prepared)
    special_engine = SpecialEventsEngine(prepared)
    special_engine.detect_walkoff()
    if not prepared.get("special_events", {}).get("leadoff_hrs"):
        special_engine.detect_leadoff_home_runs()
    special_engine.detect_grand_slams()
    MilestoneEngine(prepared).process()
    return prepared


def _parse_bref_html(path: Path) -> dict[str, Any]:
    with contextlib.redirect_stdout(io.StringIO()):
        return parse_baseball_reference_boxscore(path.read_text(encoding="utf-8"))


def _normalize_text(value: Any) -> str:
    text = unicodedata.normalize("NFKD", str(value or ""))
    text = "".join(char for char in text if not unicodedata.combining(char))
    return re.sub(r"\s+", " ", text.strip()).casefold()


def _normalize_name(value: Any) -> str:
    text = _normalize_text(value)
    text = text.replace(".", "").replace("'", "").replace("’", "").replace("-", " ")
    return re.sub(r"\s+", " ", text).strip()


def _normalize_stadium(value: Any) -> str:
    normalized = _normalize_text(value)
    for canonical, aliases in STADIUM_ALIASES.items():
        if normalized == _normalize_text(canonical):
            return _normalize_text(canonical)
        for alias in aliases:
            if normalized == _normalize_text(alias):
                return _normalize_text(canonical)
    return normalized


def _normalize_team_code(value: Any) -> str:
    code = str(value or "").strip().upper()
    return unify_team_code(code) if code else ""


def _normalize_value(field: str, value: Any) -> Any:
    if field == "IP":
        text = str(value or "").strip()
        return f"{text}.0" if text and "." not in text else text
    if field.endswith("_team_code"):
        return _normalize_team_code(value)
    if field == "venue":
        return _normalize_stadium(value)
    if field.endswith("_score_value") or field in set(BATTING_FIELDS) | {"H", "R", "ER", "BB", "SO", "HR"}:
        try:
            return int(value or 0)
        except (TypeError, ValueError):
            return _normalize_text(value)
    return _normalize_text(value)


def _row_name(row: dict[str, Any]) -> str:
    return _normalize_name(row.get("name") or row.get("Name") or "")


def _row_id(row: dict[str, Any]) -> str:
    return _normalize_text(row.get("player_id") or row.get("Player ID") or row.get("playerId") or "")


def _matching_row(row: dict[str, Any], candidates: list[dict[str, Any]], used: set[int]) -> tuple[int, dict[str, Any]] | None:
    player_id = _row_id(row)
    name = _row_name(row)
    for index, candidate in enumerate(candidates):
        if index in used:
            continue
        if player_id and _row_id(candidate) == player_id:
            return index, candidate
    for index, candidate in enumerate(candidates):
        if index in used:
            continue
        if name and _row_name(candidate) == name:
            return index, candidate
    return None


def _has_batting_activity(row: dict[str, Any]) -> bool:
    return any(_normalize_value(field, row.get(field)) for field in ("AB", "H", "R", "RBI", "BB", "SO"))


def _issue(kind: str, game_id: str, field: str, api_value: Any, bref_value: Any,
           api_file: Path, bref_file: Path, side: str = "", player: str = "") -> dict[str, Any]:
    subject = f"{side} {player} ".strip()
    subject_text = f"{subject} " if subject else ""
    return {
        "kind": kind,
        "game_id": game_id,
        "field": field,
        "side": side,
        "player": player,
        "api_source": "mlb",
        "other_source": "bref_html",
        "api_value": api_value,
        "other_value": bref_value,
        "api_file": str(api_file),
        "other_file": str(bref_file),
        "message": f"{game_id} {subject_text}{field}: API has {api_value!r}, BREF backup has {bref_value!r}.",
    }


def _compare_metadata(api_game, bref_game, api_file: Path, bref_file: Path) -> list[dict[str, Any]]:
    issues = []
    game_id = api_game.get("game_id", "")
    api_basic = api_game.get("basic_info", {})
    bref_basic = bref_game.get("basic_info", {})
    for field in METADATA_FIELDS:
        api_value = api_basic.get(field)
        bref_value = bref_basic.get(field)
        if _normalize_value(field, api_value) != _normalize_value(field, bref_value):
            issues.append(_issue("metadata_mismatch", game_id, field, api_value, bref_value, api_file, bref_file))
    return issues


def _compare_rows(api_game, bref_game, api_file: Path, bref_file: Path, section: str,
                  fields: tuple[str, ...]) -> list[dict[str, Any]]:
    issues = []
    game_id = api_game.get("game_id", "")
    for side in ("away", "home"):
        api_rows = api_game.get(section, {}).get(side, []) or []
        bref_rows = bref_game.get(section, {}).get(side, []) or []
        used = set()

        for api_row in api_rows:
            match = _matching_row(api_row, bref_rows, used)
            if match is None:
                if section == "batting" and not _has_batting_activity(api_row):
                    continue
                issues.append(_issue(f"missing_{section}_row", game_id, "row", "present", "missing", api_file, bref_file, side, api_row.get("name", "")))
                continue

            index, bref_row = match
            used.add(index)
            for field in fields:
                api_value = api_row.get(field)
                bref_value = bref_row.get(field)
                if _normalize_value(field, api_value) != _normalize_value(field, bref_value):
                    issues.append(_issue(f"{section}_mismatch", game_id, field, api_value, bref_value, api_file, bref_file, side, api_row.get("name", "")))

        for index, bref_row in enumerate(bref_rows):
            if index in used:
                continue
            if section == "batting" and not _has_batting_activity(bref_row):
                continue
            issues.append(_issue(f"extra_{section}_row", game_id, "row", "missing", "present", api_file, bref_file, side, bref_row.get("name", "")))
    return issues


def _milestone_counts(game: dict[str, Any]) -> dict[str, int]:
    with contextlib.redirect_stdout(io.StringIO()):
        milestones, *_ = MilestonesProcessor([copy.deepcopy(game)]).process_all_milestones()
    counts = {}
    for category in MILESTONE_CATEGORIES:
        df = milestones.get(category)
        counts[category] = 0 if df is None or getattr(df, "empty", True) else len(df)
    return counts


def _compare_milestones(api_game, bref_game, api_file: Path, bref_file: Path) -> list[dict[str, Any]]:
    issues = []
    game_id = api_game.get("game_id", "")
    api_counts = _milestone_counts(api_game)
    bref_counts = _milestone_counts(bref_game)
    for category in MILESTONE_CATEGORIES:
        if api_counts.get(category, 0) != bref_counts.get(category, 0):
            issues.append(_issue("milestone_count_mismatch", game_id, category, api_counts.get(category, 0), bref_counts.get(category, 0), api_file, bref_file))
    return issues


def compare_api_game_to_bref_backup(api_file: Path, api_game: dict[str, Any], bref_file: Path) -> list[dict[str, Any]]:
    api_prepared = _prepare_api_game(api_game)
    bref_game = _parse_bref_html(bref_file)
    issues = []
    issues.extend(_compare_metadata(api_prepared, bref_game, api_file, bref_file))
    issues.extend(_compare_rows(api_prepared, bref_game, api_file, bref_file, "batting", BATTING_FIELDS))
    issues.extend(_compare_rows(api_prepared, bref_game, api_file, bref_file, "pitching", PITCHING_FIELDS))
    issues.extend(_compare_milestones(api_prepared, bref_game, api_file, bref_file))
    return issues


def generate_bref_backup_parity_report(cache_dir: Path = CACHE_DIR, html_dir: Path = HTML_DIR,
                                       recent_days: int | None = 45) -> dict[str, Any]:
    issues = []
    checked = 0
    missing_backups = []
    parse_errors = []

    for api_file, api_game in load_api_cache_games(cache_dir, recent_days=recent_days):
        bref_file = find_bref_html_for_game(api_game, html_dir)
        if not bref_file:
            missing_backups.append(str(api_file))
            continue
        checked += 1
        try:
            issues.extend(compare_api_game_to_bref_backup(api_file, api_game, bref_file))
        except Exception as exc:
            parse_errors.append({"api_file": str(api_file), "bref_file": str(bref_file), "error": str(exc)})

    return {
        "checked": checked,
        "missing_backups": missing_backups,
        "parse_errors": parse_errors,
        "issues": issues,
    }


def write_issues_csv(issues: list[dict[str, Any]], output_path: Path = DEFAULT_REPORT_PATH) -> None:
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
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        for issue in issues:
            writer.writerow({field: issue.get(field, "") for field in fieldnames})


def clear_issues_csv(output_path: Path = DEFAULT_REPORT_PATH) -> None:
    try:
        output_path.unlink()
    except FileNotFoundError:
        pass


def main() -> None:
    parser = argparse.ArgumentParser(description="Compare API cache records with local BREF HTML backups.")
    parser.add_argument("--cache-dir", type=Path, default=CACHE_DIR)
    parser.add_argument("--html-dir", type=Path, default=HTML_DIR)
    parser.add_argument("--recent-days", type=int, default=45, help="Only check API games newer than this many days; use 0 for all")
    parser.add_argument("--csv", type=Path, default=DEFAULT_REPORT_PATH)
    args = parser.parse_args()

    recent_days = None if args.recent_days == 0 else args.recent_days
    report = generate_bref_backup_parity_report(args.cache_dir, args.html_dir, recent_days=recent_days)
    print(f"Checked {report['checked']} API/BREF backup pair(s).")
    if report["missing_backups"]:
        print(f"Missing BREF backup for {len(report['missing_backups'])} API game(s).")
    if report["parse_errors"]:
        print(f"Could not parse/compare {len(report['parse_errors'])} pair(s).")
    if not report["issues"]:
        clear_issues_csv(args.csv)
        print("No API/BREF backup discrepancies found.")
        return

    print(f"Found {len(report['issues'])} API/BREF backup discrepancy/discrepancies.")
    for issue in report["issues"][:20]:
        print(f"- {issue['message']}")
    if len(report["issues"]) > 20:
        print(f"- ... {len(report['issues']) - 20} more")
    write_issues_csv(report["issues"], args.csv)
    print(f"Wrote discrepancy CSV to {args.csv}")


if __name__ == "__main__":
    main()
