"""
MLB.com Splash Hits Scraper
===========================
Refreshes the local Oracle Park Splash Hits and McCovey Cove reference CSVs
from the San Francisco Giants' official MLB.com page.

Usage:
    python3 -m baseball_processor.scrapers.splash_hits_scraper
"""

from __future__ import annotations

import argparse
import csv
import json
import math
import re
import tempfile
import unicodedata
from dataclasses import dataclass
from datetime import date, datetime
from pathlib import Path
from typing import Any

import pandas as pd
from bs4 import BeautifulSoup

from ..utils.constants import (
    CACHE_DIR,
    MCCOVEY_COVE_FILE,
    REFERENCES_DIR,
    REGISTER_DIR,
    SPLASH_HITS_FILE,
)
from ..utils.http import create_retry_session, get_with_retry


SOURCE_URL = "https://www.mlb.com/giants/ballpark/splash-hits"

GIANTS_COLUMNS = [
    "Splash Hit Number",
    "Player",
    "Date",
    "Opponent",
    "Pitcher",
    "Notes",
    "PlayerID",
]
VISITOR_COLUMNS = [
    "Splash Hit Number",
    "Player",
    "Team",
    "Date",
    "Pitcher",
    "PlayerID",
    "Date_yyyymmdd",
]

DATE_RE = re.compile(r"\b(?:\d{1,2}/\d{1,2}/\d{4}|\d{1,2}/\d{1,2}/\d{2})\b")
NEXT_DATA_RE = re.compile(
    r'<script[^>]+id=["\']__NEXT_DATA__["\'][^>]*>(.*?)</script>',
    re.DOTALL,
)
VALID_VISITOR_TEAM_CODES = {
    "ARI",
    "ATL",
    "AZ",
    "BAL",
    "BOS",
    "CHC",
    "CIN",
    "CLE",
    "COL",
    "CWS",
    "FLA",
    "HOU",
    "KC",
    "LA",
    "LAD",
    "MIA",
    "MIL",
    "NYM",
    "PHI",
    "PIT",
    "SD",
    "STL",
    "TEX",
    "TOR",
    "WAS",
    "WSH",
}
TEAM_CODE_TO_NAME = {
    "ARI": "Arizona Diamondbacks",
    "ATL": "Atlanta Braves",
    "AZ": "Arizona Diamondbacks",
    "BAL": "Baltimore Orioles",
    "BOS": "Boston Red Sox",
    "CHC": "Chicago Cubs",
    "CIN": "Cincinnati Reds",
    "CLE": "Cleveland Guardians",
    "COL": "Colorado Rockies",
    "CWS": "Chicago White Sox",
    "FLA": "Florida Marlins",
    "HOU": "Houston Astros",
    "KC": "Kansas City Royals",
    "LA": "Los Angeles Dodgers",
    "LAD": "Los Angeles Dodgers",
    "MIA": "Miami Marlins",
    "MIL": "Milwaukee Brewers",
    "NYM": "New York Mets",
    "PHI": "Philadelphia Phillies",
    "PIT": "Pittsburgh Pirates",
    "SD": "San Diego Padres",
    "STL": "St. Louis Cardinals",
    "TEX": "Texas Rangers",
    "TOR": "Toronto Blue Jays",
    "WAS": "Washington Nationals",
    "WSH": "Washington Nationals",
}


@dataclass(frozen=True)
class UpdateResult:
    giants_count: int
    visitors_count: int
    giants_newest_number: int
    visitors_newest_number: int
    unresolved_player_ids: tuple[str, ...]
    source_url: str = SOURCE_URL


def clean_text(value: Any) -> str:
    text = "" if value is None else str(value)
    text = text.replace("\xa0", " ")
    return re.sub(r"\s+", " ", text).strip()


def normalize_name(value: str) -> str:
    text = unicodedata.normalize("NFKD", str(value or ""))
    text = text.encode("ASCII", "ignore").decode("utf-8").lower()
    text = text.replace("*", "")
    return re.sub(r"[^a-z0-9]+", "", text)


def _is_missing(value: Any) -> bool:
    if value is None:
        return True
    if isinstance(value, float) and math.isnan(value):
        return True
    text = str(value).strip()
    return not text or text.lower() in {"nan", "none", "null"}


def parse_date(value: str) -> date:
    text = clean_text(value)
    for fmt in ("%m/%d/%Y", "%m/%d/%y"):
        try:
            parsed = datetime.strptime(text, fmt).date()
            if parsed.year < 1940:
                parsed = parsed.replace(year=parsed.year + 100)
            return parsed
        except ValueError:
            continue
    raise ValueError(f"Could not parse date: {value!r}")


def format_giants_date(parsed: date) -> str:
    return f"{parsed.month}/{parsed.day}/{parsed.strftime('%y')}"


def format_iso_date(parsed: date) -> str:
    return parsed.strftime("%Y-%m-%d")


def format_yyyymmdd(parsed: date) -> str:
    return parsed.strftime("%Y%m%d")


def _repair_known_page_typos(row_text: str) -> str:
    # The MLB.com visitor list currently renders this row as "7/820/18".
    repaired = row_text.replace("7/820/18", "7/8/2018")
    # Same visitor list has Carlos Gonzalez as "Carlos, Gonzales".
    return repaired.replace("Carlos, Gonzales", "Carlos Gonzalez")


def _extract_next_data(html: str) -> dict[str, Any]:
    match = NEXT_DATA_RE.search(html)
    if not match:
        soup = BeautifulSoup(html, "html.parser")
        script = soup.find("script", id="__NEXT_DATA__")
        if script and script.string:
            return json.loads(script.string)
        raise ValueError("Could not find __NEXT_DATA__ on MLB Splash Hits page")
    return json.loads(match.group(1))


def _extract_main_column_slots(next_data: dict[str, Any]) -> list[dict[str, Any]]:
    try:
        return next_data["props"]["pageProps"]["page"]["slots"]["Left Rail"][0]["slots"]["Main Column"]
    except (KeyError, IndexError, TypeError) as exc:
        raise ValueError("Could not find Splash Hits page content slots") from exc


def _find_wysiwyg_after_heading(slots: list[dict[str, Any]], heading_text: str) -> str:
    normalized_heading = clean_text(heading_text).lower()
    heading_seen = False
    for slot in slots:
        slot_heading = clean_text(slot.get("headingText", "")).lower()
        if slot_heading == normalized_heading:
            heading_seen = True
            continue
        if heading_seen and slot.get("type") == "wysiwyg" and slot.get("text"):
            return str(slot["text"])
    raise ValueError(f"Could not find WYSIWYG content after heading {heading_text!r}")


def _paragraph_rows(wysiwyg_html: str) -> list[tuple[str, str]]:
    soup = BeautifulSoup(wysiwyg_html, "html.parser")
    rows: list[tuple[str, str]] = []
    for paragraph in soup.find_all("p"):
        notes = " ".join(
            clean_text(note.get_text(" ", strip=True))
            for note in paragraph.find_all("em")
        )
        for note in paragraph.find_all("em"):
            note.decompose()
        row_text = clean_text(paragraph.get_text(" ", strip=True))
        if row_text:
            rows.append((_repair_known_page_typos(row_text), notes))
    return rows


def _split_number_and_rest(row_text: str) -> tuple[int, str]:
    match = re.match(r"^\s*(\d+)\s+(.+?)\s*$", row_text)
    if not match:
        raise ValueError(f"Could not parse row number: {row_text!r}")
    return int(match.group(1)), match.group(2)


def parse_giants_row(row_text: str, notes: str = "") -> dict[str, Any]:
    number, rest = _split_number_and_rest(row_text)
    date_match = DATE_RE.search(rest)
    if not date_match:
        raise ValueError(f"Could not parse Giants Splash Hit date: {row_text!r}")

    player = clean_text(rest[:date_match.start()])
    parsed_date = parse_date(date_match.group(0))
    suffix = clean_text(rest[date_match.end():])
    try:
        opponent, pitcher = suffix.split(" ", 1)
    except ValueError as exc:
        raise ValueError(f"Could not parse Giants Splash Hit opponent/pitcher: {row_text!r}") from exc

    return {
        "Splash Hit Number": number,
        "Player": player,
        "Date": format_giants_date(parsed_date),
        "Opponent": opponent.strip(","),
        "Pitcher": clean_text(pitcher),
        "Notes": clean_text(notes),
        "PlayerID": "",
    }


def _split_visitor_player_team(prefix: str) -> tuple[str, str]:
    text = clean_text(prefix)
    for code in sorted(VALID_VISITOR_TEAM_CODES, key=len, reverse=True):
        code_match = re.search(rf"(?:,\s*|\s+)({re.escape(code)})$", text)
        if code_match:
            player = clean_text(text[:code_match.start()].rstrip(" ,"))
            return player, code
    raise ValueError(f"Could not parse visitor player/team: {prefix!r}")


def parse_visitor_row(row_text: str) -> dict[str, Any]:
    number, rest = _split_number_and_rest(row_text)
    date_match = DATE_RE.search(rest)
    if not date_match:
        raise ValueError(f"Could not parse visitor McCovey Cove date: {row_text!r}")

    player_team = clean_text(rest[:date_match.start()])
    player, team_code = _split_visitor_player_team(player_team)
    parsed_date = parse_date(date_match.group(0))
    pitcher = clean_text(rest[date_match.end():])
    if pitcher.startswith("SF "):
        pitcher = clean_text(pitcher[3:])

    return {
        "Splash Hit Number": number,
        "Player": player,
        "Team": TEAM_CODE_TO_NAME.get(team_code, team_code),
        "Date": format_iso_date(parsed_date),
        "Pitcher": pitcher,
        "PlayerID": "",
        "Date_yyyymmdd": format_yyyymmdd(parsed_date),
    }


def parse_splash_hits_page(html: str) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    next_data = _extract_next_data(html)
    slots = _extract_main_column_slots(next_data)
    giants_html = _find_wysiwyg_after_heading(slots, "Splash Hits")
    visitors_html = _find_wysiwyg_after_heading(slots, "Other Home Runs into McCovey Cove")

    giants_rows = [
        parse_giants_row(row_text, notes)
        for row_text, notes in _paragraph_rows(giants_html)
    ]
    visitor_rows = [
        parse_visitor_row(row_text)
        for row_text, _notes in _paragraph_rows(visitors_html)
    ]

    giants_rows.sort(key=lambda row: int(row["Splash Hit Number"]))
    visitor_rows.sort(key=lambda row: int(row["Splash Hit Number"]))
    return giants_rows, visitor_rows


def fetch_splash_hits_page(url: str = SOURCE_URL) -> str:
    session = create_retry_session(retries=3, backoff_factor=1)
    response = get_with_retry(
        session,
        url,
        headers={
            "User-Agent": (
                "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0 Safari/537.36"
            )
        },
    )
    response.raise_for_status()
    return response.text


def _iter_json_dicts(value: Any):
    if isinstance(value, dict):
        yield value
        for child in value.values():
            yield from _iter_json_dicts(child)
    elif isinstance(value, list):
        for child in value:
            yield from _iter_json_dicts(child)


class PlayerIdResolver:
    def __init__(
        self,
        references_dir: Path = REFERENCES_DIR,
        cache_dir: Path = CACHE_DIR,
        register_dir: Path = REGISTER_DIR,
    ):
        self.references_dir = Path(references_dir)
        self.cache_dir = Path(cache_dir)
        self.register_dir = Path(register_dir)
        self._records_by_name: dict[str, list[dict[str, Any]]] = {}
        self._load_existing_signature_csvs()
        self._load_reference_jsons()
        self._load_game_cache()
        self._load_register()

    def resolve(self, player_name: str, event_date: str | None = None) -> str:
        key = normalize_name(player_name)
        candidates = self._records_by_name.get(key, [])
        if not candidates:
            return ""

        year = None
        if event_date:
            try:
                if re.match(r"^\d{4}-\d{2}-\d{2}$", str(event_date)):
                    year = datetime.strptime(str(event_date), "%Y-%m-%d").year
                else:
                    year = parse_date(str(event_date)).year
            except ValueError:
                year = None

        if year is not None:
            dated_active = [
                candidate for candidate in candidates
                if (
                    candidate.get("first_year") is not None
                    or candidate.get("last_year") is not None
                )
                and self._candidate_active_in_year(candidate, year)
            ]
            if dated_active:
                candidates = dated_active
            else:
                active = [
                    candidate for candidate in candidates
                    if self._candidate_active_in_year(candidate, year)
                ]
                if active:
                    candidates = active

        csv_candidates = [
            candidate for candidate in candidates
            if str(candidate.get("source", "")).endswith(".csv")
        ]
        if csv_candidates:
            candidates = csv_candidates

        dated_candidates = [
            candidate for candidate in candidates
            if candidate.get("first_year") is not None or candidate.get("last_year") is not None
        ]
        if dated_candidates:
            candidates = dated_candidates

        ids = []
        for candidate in candidates:
            player_id = str(candidate.get("player_id", "")).strip()
            if player_id and player_id not in ids:
                ids.append(player_id)

        return ids[0] if len(ids) == 1 else ""

    def add(self, name: str, player_id: Any, first_year: Any = None, last_year: Any = None, source: str = "") -> None:
        if _is_missing(name) or _is_missing(player_id):
            return
        player_id_text = str(player_id).strip()
        if player_id_text.lower() == "nan":
            return
        key = normalize_name(str(name))
        if not key:
            return
        record = {
            "player_id": player_id_text,
            "first_year": self._coerce_year(first_year),
            "last_year": self._coerce_year(last_year),
            "source": source,
        }
        existing = self._records_by_name.setdefault(key, [])
        if record not in existing:
            existing.append(record)

    @staticmethod
    def _coerce_year(value: Any) -> int | None:
        if _is_missing(value):
            return None
        try:
            return int(float(value))
        except (TypeError, ValueError):
            return None

    @staticmethod
    def _candidate_active_in_year(candidate: dict[str, Any], year: int) -> bool:
        first = candidate.get("first_year")
        last = candidate.get("last_year")
        if first is None and last is None:
            return True
        if first is not None and year < first:
            return False
        if last is not None and year > last:
            return False
        return True

    def _load_existing_signature_csvs(self) -> None:
        for path in (self.references_dir / SPLASH_HITS_FILE.name, self.references_dir / MCCOVEY_COVE_FILE.name):
            if not path.exists():
                continue
            try:
                df = pd.read_csv(path)
            except Exception:
                continue
            if "Player" not in df.columns or "PlayerID" not in df.columns:
                continue
            for _, row in df.iterrows():
                self.add(row.get("Player"), row.get("PlayerID"), source=path.name)

    def _load_reference_jsons(self) -> None:
        for path in (
            self.references_dir / "awards.json",
            self.references_dir / "all_star_participants.json",
        ):
            if not path.exists():
                continue
            try:
                payload = json.loads(path.read_text(encoding="utf-8"))
            except Exception:
                continue
            for obj in _iter_json_dicts(payload):
                name = obj.get("name") or obj.get("Name") or obj.get("player")
                player_id = obj.get("player_id") or obj.get("entity_id") or obj.get("PlayerID")
                self.add(name, player_id, source=path.name)

    def _load_game_cache(self) -> None:
        if not self.cache_dir.exists():
            return
        skip_patterns = {"career_firsts", "career_gamelogs", "player_bios", "career_highs"}
        for path in self.cache_dir.glob("*.json"):
            if any(pattern in path.name for pattern in skip_patterns):
                continue
            try:
                payload = json.loads(path.read_text(encoding="utf-8"))
            except Exception:
                continue
            if not isinstance(payload, dict):
                continue
            for section_name in ("batting", "pitching"):
                section = payload.get(section_name, {})
                if not isinstance(section, dict):
                    continue
                for side in ("away", "home"):
                    for row in section.get(side, []) or []:
                        if isinstance(row, dict):
                            self.add(row.get("name"), row.get("player_id"), source=path.name)

    def _load_register(self) -> None:
        data_dir = self.register_dir / "data"
        if not data_dir.exists():
            return
        for path in data_dir.glob("people-*.csv"):
            try:
                df = pd.read_csv(path, low_memory=False)
            except Exception:
                continue
            if "key_bbref" not in df.columns:
                continue
            for _, row in df.iterrows():
                player_id = row.get("key_bbref")
                if _is_missing(player_id):
                    continue
                first = row.get("mlb_played_first")
                last = row.get("mlb_played_last")
                first_name = clean_text(row.get("name_first", ""))
                last_name = clean_text(row.get("name_last", ""))
                given_name = clean_text(row.get("name_given", ""))
                full_name = clean_text(f"{first_name} {last_name}")
                self.add(full_name, player_id, first, last, source=path.name)
                if given_name and normalize_name(given_name) != normalize_name(full_name):
                    self.add(given_name, player_id, first, last, source=path.name)


def enrich_player_ids(
    rows: list[dict[str, Any]],
    resolver: PlayerIdResolver,
) -> list[str]:
    unresolved: list[str] = []
    for row in rows:
        player_id = resolver.resolve(row.get("Player", ""), row.get("Date"))
        row["PlayerID"] = player_id
        if not player_id:
            label = f"{row.get('Player', '')} ({row.get('Date', '')})"
            if label not in unresolved:
                unresolved.append(label)
    return unresolved


def _write_csv_atomic(path: Path, rows: list[dict[str, Any]], columns: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile(
        "w",
        encoding="utf-8",
        newline="",
        dir=path.parent,
        delete=False,
    ) as tmp:
        writer = csv.DictWriter(tmp, fieldnames=columns, lineterminator="\n")
        writer.writeheader()
        for row in rows:
            writer.writerow({column: row.get(column, "") for column in columns})
        tmp_path = Path(tmp.name)
    tmp_path.replace(path)


def update_splash_hits(
    source_url: str = SOURCE_URL,
    splash_hits_file: Path = SPLASH_HITS_FILE,
    mccovey_cove_file: Path = MCCOVEY_COVE_FILE,
    references_dir: Path = REFERENCES_DIR,
    cache_dir: Path = CACHE_DIR,
    register_dir: Path = REGISTER_DIR,
) -> UpdateResult:
    html = fetch_splash_hits_page(source_url)
    giants_rows, visitor_rows = parse_splash_hits_page(html)

    resolver = PlayerIdResolver(
        references_dir=references_dir,
        cache_dir=cache_dir,
        register_dir=register_dir,
    )
    unresolved = enrich_player_ids(giants_rows, resolver)
    unresolved.extend(enrich_player_ids(visitor_rows, resolver))

    _write_csv_atomic(Path(splash_hits_file), giants_rows, GIANTS_COLUMNS)
    _write_csv_atomic(Path(mccovey_cove_file), visitor_rows, VISITOR_COLUMNS)

    unresolved = sorted(set(unresolved))
    return UpdateResult(
        giants_count=len(giants_rows),
        visitors_count=len(visitor_rows),
        giants_newest_number=max((int(row["Splash Hit Number"]) for row in giants_rows), default=0),
        visitors_newest_number=max((int(row["Splash Hit Number"]) for row in visitor_rows), default=0),
        unresolved_player_ids=tuple(unresolved),
        source_url=source_url,
    )


def main() -> None:
    parser = argparse.ArgumentParser(description="Refresh MLB.com Giants Splash Hits reference CSVs")
    parser.add_argument("--source-url", default=SOURCE_URL, help="MLB.com Splash Hits source URL")
    args = parser.parse_args()

    result = update_splash_hits(source_url=args.source_url)
    print(
        "Updated Splash Hits: "
        f"{result.giants_count} Giants rows (latest #{result.giants_newest_number}), "
        f"{result.visitors_count} other Cove rows (latest #{result.visitors_newest_number})"
    )
    if result.unresolved_player_ids:
        print("Rows without PlayerID:")
        for label in result.unresolved_player_ids:
            print(f"  - {label}")


if __name__ == "__main__":
    main()
