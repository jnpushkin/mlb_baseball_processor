"""
Baseball-Reference Awards Scraper
=================================
Scrapes Baseball-Reference award winner pages into one normalized JSON file.

Usage:
    python3 -m baseball_processor.scrapers.awards_scraper
    python3 -m baseball_processor.scrapers.awards_scraper --page mvp --page cya
    python3 -m baseball_processor.scrapers.awards_scraper --list-pages

The output defaults to mlb_references/awards.json.
"""

from __future__ import annotations

import argparse
import csv
import json
import re
import sys
import time
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from urllib.parse import urljoin

try:
    from bs4 import BeautifulSoup, Comment, Tag
except ImportError as e:
    print(f"Missing required package: {e}")
    print("Install with: pip install beautifulsoup4")
    sys.exit(1)

from ..utils.constants import REFERENCES_DIR
from ..utils.http import create_retry_session, get_with_retry


BASE_URL = "https://www.baseball-reference.com"
AWARDS_INDEX_URL = f"{BASE_URL}/awards/"
DEFAULT_DELAY_SECONDS = 3.2

PLAYER_HREF_RE = re.compile(r"^/players/[a-z]/([^/]+)\.shtml$")
MANAGER_HREF_RE = re.compile(r"^/managers/([^/.]+)\.shtml$")
TEAM_HREF_RE = re.compile(r"^/teams/([^/]+)/(\d{4})\.shtml$")
YEAR_RE = re.compile(r"\b(18|19|20)\d{2}\b")
LEAGUE_RE = re.compile(r"\b(AL|NL|ML|MLB|FL|AA|PL|UA)\b")
POSITION_CODES = {
    "P",
    "SP",
    "RP",
    "C",
    "1B",
    "2B",
    "3B",
    "SS",
    "LF",
    "CF",
    "RF",
    "OF",
    "DH",
    "UT",
    "UTILITY",
}


@dataclass(frozen=True)
class AwardPage:
    key: str
    path: str
    award: str
    label: str
    default_league: str = ""
    selection_column: str = ""

    @property
    def url(self) -> str:
        return urljoin(BASE_URL, self.path)


DEFAULT_AWARD_PAGES: tuple[AwardPage, ...] = (
    AwardPage("mvp", "/awards/mvp.shtml", "Most Valuable Player", "Most Valuable Player MVP Awards"),
    AwardPage("cya", "/awards/cya.shtml", "Cy Young", "Cy Young Awards"),
    AwardPage("roy", "/awards/roy.shtml", "Rookie of the Year", "Rookie of the Year"),
    AwardPage("reliever", "/awards/reliever.shtml", "Reliever of the Year", "Reliever/Rolaids Relief Awards"),
    AwardPage("postmvp", "/awards/postmvp.shtml", "Postseason MVP", "Postseason MVP Awards"),
    AwardPage("asmvp", "/awards/asmvp.shtml", "All-Star Game MVP", "All-Star Game MVP"),
    AwardPage("mlb-players-of-the-month", "/awards/mlb-players-of-the-month.shtml", "Player of the Month", "Players of the Month"),
    AwardPage("mlb-players-of-the-week", "/awards/mlb-players-of-the-week.shtml", "Player of the Week", "Players of the Week"),
    AwardPage("mlb-pitchers-of-the-month", "/awards/mlb-pitchers-of-the-month.shtml", "Pitcher of the Month", "Pitchers of the Month"),
    AwardPage("mlb-rookies-of-the-month", "/awards/mlb-rookies-of-the-month.shtml", "Rookie of the Month", "Rookies of the Month"),
    AwardPage("mlb-relievers-of-the-month", "/awards/mlb-relievers-of-the-month.shtml", "Reliever of the Month", "Relievers of the Month"),
    AwardPage("manage", "/awards/manage.shtml", "Manager of the Year", "Manager of the Year Awards"),
    AwardPage("delivery", "/awards/delivery.shtml", "Delivery Man of the Year", "Delivery Man of the Year"),
    AwardPage("comeback_player", "/awards/comeback_player.shtml", "Comeback Player of the Year", "Comeback Player of the Year"),
    AwardPage("edgar_martinez", "/awards/edgar_martinez.shtml", "Edgar Martinez Award", "Edgar Martinez Outstanding Designated Hitter"),
    AwardPage("batting-titles", "/awards/batting-titles.shtml", "Batting Title", "Batting Champions"),
    AwardPage("pitching-era-titles", "/awards/pitching-era-titles.shtml", "ERA Title", "Pitching ERA Champions"),
    AwardPage("triple_crowns", "/awards/triple_crowns.shtml", "Triple Crown", "Triple Crown Winners"),
    AwardPage("gold_glove_nl", "/awards/gold_glove_nl.shtml", "Gold Glove", "National League Gold Glove Awards", default_league="NL"),
    AwardPage("gold_glove_al", "/awards/gold_glove_al.shtml", "Gold Glove", "American League Gold Glove Awards", default_league="AL"),
    AwardPage("platinum", "/awards/platinum.shtml", "Platinum Glove", "Platinum Gloves"),
    AwardPage("silver_slugger_nl", "/awards/silver_slugger_nl.shtml", "Silver Slugger", "National League Silver Slugger Awards", default_league="NL"),
    AwardPage("silver_slugger_al", "/awards/silver_slugger_al.shtml", "Silver Slugger", "American League Silver Slugger Awards", default_league="AL"),
    AwardPage("all_mlb", "/awards/all_mlb.shtml", "All-MLB Team", "All-MLB Teams", selection_column="Team"),
    AwardPage("tsn", "/awards/tsn.shtml", "The Sporting News Award", "The Sporting News Awards"),
    AwardPage("hank_aaron", "/awards/hank_aaron.shtml", "Hank Aaron Award", "Hank Aaron Award"),
    AwardPage("branch_rickey", "/awards/branch_rickey.shtml", "Branch Rickey Award", "Branch Rickey Award"),
    AwardPage("hutch", "/awards/hutch.shtml", "Hutch Award", "Hutch Award"),
    AwardPage("gehrig", "/awards/gehrig.shtml", "Lou Gehrig Memorial Award", "Lou Gehrig Memorial Award"),
    AwardPage("ruth", "/awards/ruth.shtml", "Babe Ruth Award", "Babe Ruth Award"),
    AwardPage("clemente", "/awards/clemente.shtml", "Roberto Clemente Award", "Roberto Clemente Award"),
    AwardPage("wilson_def_player", "/awards/wilson_def_player.shtml", "Wilson Defensive Player of the Year", "Wilson Defensive Player of the Year"),
    AwardPage("heart_and_hustle", "/awards/heart_and_hustle.shtml", "Heart and Hustle Award", "Heart and Hustle Award"),
)

AWARD_PAGES_BY_KEY = {page.key: page for page in DEFAULT_AWARD_PAGES}


def clean_text(value: Any) -> str:
    """Normalize Baseball-Reference table text."""
    if value is None:
        return ""
    return re.sub(r"\s+", " ", str(value).replace("\xa0", " ")).strip()


def slug_header(value: str, fallback: str) -> str:
    text = clean_text(value).lower()
    if not text:
        return fallback
    text = re.sub(r"[^a-z0-9]+", "_", text).strip("_")
    return text or fallback


def make_unique_headers(headers: list[dict[str, str]]) -> list[dict[str, str]]:
    counts: dict[str, int] = {}
    unique = []
    for idx, header in enumerate(headers):
        base_key = header["key"] or f"col_{idx}"
        counts[base_key] = counts.get(base_key, 0) + 1
        key = base_key if counts[base_key] == 1 else f"{base_key}_{counts[base_key]}"
        unique.append({**header, "key": key})
    return unique


def extract_headers(table: Tag) -> list[dict[str, str]]:
    thead = table.find("thead")
    header_row = None
    if thead:
        rows = thead.find_all("tr")
        if rows:
            header_row = rows[-1]
    if not header_row:
        first_row = table.find("tr")
        if first_row and first_row.find_all("th"):
            header_row = first_row
    if not header_row:
        return []

    headers = []
    for idx, cell in enumerate(header_row.find_all(["th", "td"], recursive=False)):
        label = clean_text(cell.get_text(" ", strip=True))
        data_stat = clean_text(cell.get("data-stat", ""))
        key = data_stat or slug_header(label, f"col_{idx}")
        headers.append({
            "key": key,
            "label": label,
            "data_stat": data_stat,
        })
    return make_unique_headers(headers)


def iter_table_rows(table: Tag):
    """Yield body rows, including BRef title tables with nested malformed <tr> tags."""
    section = table.find("tbody") or table
    direct_rows = section.find_all("tr", recursive=False)
    if (
        len(direct_rows) == 1
        and direct_rows[0].find("tr")
        and len(direct_rows[0].find_all(["th", "td"], recursive=False)) > 0
    ):
        row = direct_rows[0]
        while row:
            yield row
            row = row.find("tr", recursive=False)
        return

    for row in direct_rows:
        yield row


def row_cells(row: Tag) -> list[Tag]:
    return row.find_all(["th", "td"], recursive=False)


def parse_year_league(value: str, previous_year: int | None = None) -> tuple[int | None, str]:
    text = clean_text(value)
    year_match = YEAR_RE.search(text)
    year = int(year_match.group(0)) if year_match else previous_year
    remainder = YEAR_RE.sub(" ", text)
    league_match = LEAGUE_RE.search(remainder)
    league = league_match.group(1) if league_match else ""
    return year, league


def person_links(cell: Tag) -> list[dict[str, str]]:
    people = []
    seen = set()
    for link in cell.find_all("a"):
        href = link.get("href", "")
        entity_type = ""
        entity_id = ""
        player_match = PLAYER_HREF_RE.match(href)
        manager_match = MANAGER_HREF_RE.match(href)
        if player_match:
            entity_type = "player"
            entity_id = player_match.group(1)
        elif manager_match:
            entity_type = "manager"
            entity_id = manager_match.group(1)
        else:
            continue

        dedupe_key = (entity_type, entity_id)
        if dedupe_key in seen:
            continue
        seen.add(dedupe_key)

        name = clean_text(link.get_text(" ", strip=True))
        title_name = name_from_title(link.get("title", ""))
        if title_name:
            name = title_name

        people.append({
            "entity_type": entity_type,
            "entity_id": entity_id,
            "name": name,
            "href": href,
            "source_url": urljoin(BASE_URL, href),
        })
    return people


def name_from_title(title: str) -> str:
    text = clean_text(title)
    if not text or "," not in text:
        return ""
    candidate = clean_text(text.split(",", 1)[0])
    if not candidate or len(candidate.split()) < 2:
        return ""
    if re.search(r"[\d%]", candidate):
        return ""
    if re.fullmatch(r"[A-Z]{2,3}", candidate):
        return ""
    return candidate


def first_team_id(cell: Tag) -> str:
    desc = cell.find(class_="desc")
    if desc:
        return clean_text(desc.get_text(" ", strip=True))

    for link in cell.find_all("a"):
        href = link.get("href", "")
        match = TEAM_HREF_RE.match(href)
        if match:
            return match.group(1)

    text = clean_text(cell.get_text(" ", strip=True))
    if "·" in text:
        team = clean_text(text.rsplit("·", 1)[1]).split(" ")[0]
        return team

    for token in text.split():
        normalized = token.strip("(),")
        if re.fullmatch(r"[A-Z0-9]{2,3}|2tm|TOT", normalized):
            return normalized
    return ""


def infer_position(header: dict[str, str], cell: Tag, person_name: str) -> str:
    first_link = cell.find("a")
    if first_link:
        prefix_parts = []
        for sibling in first_link.previous_siblings:
            prefix_parts.append(clean_text(getattr(sibling, "get_text", lambda *_: sibling)(" ", strip=True) if isinstance(sibling, Tag) else sibling))
        prefix = clean_text(" ".join(reversed(prefix_parts)))
        for token in prefix.split():
            if token.upper() in POSITION_CODES:
                return "UT" if token.upper() == "UTILITY" else token.upper()

    text = clean_text(cell.get_text(" ", strip=True))
    if person_name and text.startswith(person_name):
        text = clean_text(text[len(person_name):])
    tokens = text.split()
    if tokens and tokens[0].upper() in POSITION_CODES:
        return "UT" if tokens[0].upper() == "UTILITY" else tokens[0].upper()

    header_candidates = [
        header.get("label", ""),
        header.get("data_stat", ""),
        header.get("key", "").split("_", 1)[0],
    ]
    for candidate in header_candidates:
        normalized = clean_text(candidate).upper()
        if normalized in POSITION_CODES:
            return "UT" if normalized == "UTILITY" else normalized
    return ""


def league_from_detail(detail: str) -> str:
    text = clean_text(detail)
    match = re.match(r"^(AL|NL|ML|MLB)\b", text)
    return match.group(1) if match else ""


def table_caption(table: Tag) -> str:
    caption = table.find("caption")
    return clean_text(caption.get_text(" ", strip=True)) if caption else ""


def is_context_header(header: dict[str, str], page: AwardPage) -> bool:
    label = clean_text(header["label"])
    key = header["key"]
    if page.selection_column and label == page.selection_column:
        return True
    return label in {"Year", "Year Lg", "League", "Lg", "Month", "Week Ending"} or key in {
        "year",
        "year_ID",
        "lg_ID",
        "month",
        "week_ending",
    }


def has_standard_player_column(headers: list[dict[str, str]]) -> bool:
    return any(header["data_stat"] == "player" for header in headers)


def parse_awards_html(html: str, page: AwardPage) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    soup = BeautifulSoup(html, "html.parser")
    for comment in soup.find_all(string=lambda text: isinstance(text, Comment)):
        if "<table" in comment:
            soup.append(BeautifulSoup(comment, "html.parser"))

    entries: list[dict[str, Any]] = []
    table_summaries: list[dict[str, Any]] = []
    for table in soup.find_all("table"):
        headers = extract_headers(table)
        if not headers:
            continue

        before_count = len(entries)
        if has_standard_player_column(headers):
            entries.extend(parse_standard_table(table, headers, page))
        else:
            entries.extend(parse_grid_table(table, headers, page))

        table_summaries.append({
            "table_id": table.get("id", ""),
            "caption": table_caption(table),
            "entries": len(entries) - before_count,
        })

    return entries, table_summaries


def parse_standard_table(table: Tag, headers: list[dict[str, str]], page: AwardPage) -> list[dict[str, Any]]:
    entries = []
    for row in iter_table_rows(table):
        cells = row_cells(row)
        if not cells or "thead" in row.get("class", []):
            continue

        row_data: dict[str, str] = {}
        row_cell_by_key: dict[str, Tag] = {}
        for idx, cell in enumerate(cells[:len(headers)]):
            key = headers[idx]["key"]
            row_data[key] = clean_text(cell.get_text(" ", strip=True))
            row_cell_by_key[key] = cell

        player_cell = row_cell_by_key.get("player")
        if not player_cell:
            continue

        people = person_links(player_cell)
        if not people:
            continue

        year, parsed_league = parse_year_league(row_data.get("year_ID") or row_data.get("year") or "")
        league = row_data.get("lg_ID", "") or parsed_league or page.default_league
        team = row_data.get("team_ID", "") or first_team_id(row_cell_by_key.get("team_ID", player_cell))
        stats = {
            key: value
            for key, value in row_data.items()
            if value
            and key
            not in {"year_ID", "year", "lg_ID", "player", "team_ID", "Voting", "voting"}
        }

        for person in people:
            entries.append(build_entry(
                page=page,
                table=table,
                person=person,
                year=year,
                league=league,
                award_detail=page.award,
                team=team,
                position=infer_position({"label": "", "key": "", "data_stat": ""}, player_cell, person["name"]),
                notes="",
                stats=stats,
            ))
    return entries


def parse_grid_table(table: Tag, headers: list[dict[str, str]], page: AwardPage) -> list[dict[str, Any]]:
    entries = []
    last_year: int | None = None
    caption = table_caption(table)
    for row in iter_table_rows(table):
        cells = row_cells(row)
        if not cells or "thead" in row.get("class", []):
            continue

        row_context: dict[str, Any] = {
            "league": page.default_league,
            "month": "",
            "week_ending": "",
            "selection": "",
        }
        for idx, cell in enumerate(cells[:len(headers)]):
            header = headers[idx]
            label = clean_text(header["label"])
            value = clean_text(cell.get_text(" ", strip=True))
            if label in {"Year", "Year Lg"} or header["key"] in {"year", "year_ID"}:
                year, parsed_league = parse_year_league(value, last_year)
                if year:
                    last_year = year
                    row_context["year"] = year
                if parsed_league:
                    row_context["league"] = parsed_league
            elif label in {"League", "Lg"} or header["key"] == "lg_ID":
                row_context["league"] = value or row_context["league"]
            elif label == "Month" or header["key"] == "month":
                row_context["month"] = value
            elif label == "Week Ending" or header["key"] == "week_ending":
                row_context["week_ending"] = value
            elif page.selection_column and label == page.selection_column:
                row_context["selection"] = value

        if "year" not in row_context and last_year:
            row_context["year"] = last_year

        for idx, cell in enumerate(cells[:len(headers)]):
            header = headers[idx]
            if is_context_header(header, page):
                continue

            people = person_links(cell)
            if not people:
                continue

            detail = award_detail_for_cell(page, header, caption)
            detail_league = league_from_detail(detail)
            league = detail_league or row_context.get("league", "") or page.default_league
            team = first_team_id(cell)
            notes = clean_text(cell.get_text(" ", strip=True))

            for person in people:
                entries.append(build_entry(
                    page=page,
                    table=table,
                    person=person,
                    year=row_context.get("year"),
                    league=league,
                    award_detail=detail,
                    team=team,
                    position=infer_position(header, cell, person["name"]),
                    month=row_context.get("month", ""),
                    week_ending=row_context.get("week_ending", ""),
                    selection=row_context.get("selection", ""),
                    notes=notes,
                    stats={},
                ))
    return entries


def award_detail_for_cell(page: AwardPage, header: dict[str, str], caption: str) -> str:
    label = clean_text(header["label"])
    key = clean_text(header["data_stat"] or header["key"])
    if label and label not in {"Player", "Name"}:
        return label
    if caption:
        caption = re.sub(r"\s+Table$", "", caption)
        return caption
    return page.award if not key.startswith("col_") else ""


def build_entry(
    *,
    page: AwardPage,
    table: Tag,
    person: dict[str, str],
    year: int | None,
    league: str,
    award_detail: str,
    team: str = "",
    position: str = "",
    month: str = "",
    week_ending: str = "",
    selection: str = "",
    notes: str = "",
    stats: dict[str, str] | None = None,
) -> dict[str, Any]:
    entry: dict[str, Any] = {
        "award": page.award,
        "award_key": page.key,
        "award_detail": clean_text(award_detail),
        "year": year,
        "league": clean_text(league),
        "name": person["name"],
        "entity_type": person["entity_type"],
        "entity_id": person["entity_id"],
        "team": clean_text(team),
        "position": clean_text(position),
        "month": clean_text(month),
        "week_ending": clean_text(week_ending),
        "selection": clean_text(selection),
        "notes": clean_text(notes),
        "stats": stats or {},
        "source_page": page.url,
        "source_table": table.get("id", ""),
        "source_url": person["source_url"],
    }
    if person["entity_type"] == "player":
        entry["player_id"] = person["entity_id"]
    elif person["entity_type"] == "manager":
        entry["manager_id"] = person["entity_id"]
    return entry


def fetch_awards_page(session, page: AwardPage) -> str:
    headers = {
        "User-Agent": (
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
            "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        ),
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.9",
    }
    response = get_with_retry(session, page.url, headers=headers, timeout=30)
    response.encoding = "utf-8"
    if response.status_code == 429:
        raise RuntimeError("Baseball-Reference returned HTTP 429. Wait at least 15 minutes before retrying.")
    response.raise_for_status()
    return response.text


def scrape_awards(pages: list[AwardPage], delay: float = DEFAULT_DELAY_SECONDS) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    session = create_retry_session()
    all_entries: list[dict[str, Any]] = []
    page_summaries: list[dict[str, Any]] = []
    for idx, page in enumerate(pages):
        if idx > 0 and delay > 0:
            time.sleep(delay)
        print(f"Fetching {page.url}...")
        html = fetch_awards_page(session, page)
        entries, tables = parse_awards_html(html, page)
        all_entries.extend(entries)
        page_summaries.append({
            "key": page.key,
            "label": page.label,
            "url": page.url,
            "entries": len(entries),
            "tables": tables,
        })
        print(f"  Found {len(entries)} award entries")
    return sort_entries(enrich_entry_names(all_entries)), page_summaries


def name_looks_complete(name: str) -> bool:
    text = clean_text(name)
    return bool(text and " " in text and not re.search(r"[\d%]", text))


def load_local_player_name_index(references_dir: Path = REFERENCES_DIR) -> dict[str, str]:
    names: dict[str, str] = {}
    for csv_path in sorted(references_dir.glob("* MLB Debuts.csv")):
        try:
            with csv_path.open(newline="", encoding="utf-8") as handle:
                for row in csv.DictReader(handle):
                    player_id = clean_text(row.get("Name-additional", ""))
                    name = clean_text(row.get("Name", ""))
                    if player_id and name_looks_complete(name):
                        names[player_id] = name
        except OSError:
            continue

    hof_path = references_dir / "HOF.csv"
    if hof_path.exists():
        try:
            with hof_path.open(newline="", encoding="utf-8") as handle:
                for row in csv.DictReader(handle):
                    player_id = clean_text(row.get("Name-additional", ""))
                    name = clean_text(row.get("Name", ""))
                    if player_id and name_looks_complete(name):
                        names.setdefault(player_id, name)
        except OSError:
            pass
    return names


def enrich_entry_names(entries: list[dict[str, Any]], references_dir: Path = REFERENCES_DIR) -> list[dict[str, Any]]:
    name_index = load_local_player_name_index(references_dir)
    for entry in entries:
        if entry.get("entity_type") != "player":
            continue
        player_id = entry.get("player_id") or entry.get("entity_id")
        name = clean_text(entry.get("name", ""))
        if player_id and name_looks_complete(name):
            name_index.setdefault(player_id, name)

    enriched = []
    for entry in entries:
        if entry.get("entity_type") != "player":
            enriched.append(entry)
            continue
        player_id = entry.get("player_id") or entry.get("entity_id")
        if player_id and not name_looks_complete(entry.get("name", "")) and player_id in name_index:
            entry = {**entry, "name": name_index[player_id]}
        enriched.append(entry)
    return enriched


def sort_entries(entries: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return sorted(
        entries,
        key=lambda entry: (
            -(entry.get("year") or 0),
            entry.get("award", ""),
            entry.get("league", ""),
            entry.get("award_detail", ""),
            entry.get("selection", ""),
            entry.get("position", ""),
            entry.get("name", ""),
        ),
    )


def write_awards_file(entries: list[dict[str, Any]], page_summaries: list[dict[str, Any]], output_path: Path) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "metadata": {
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "source": "Baseball-Reference awards pages",
            "source_index_url": AWARDS_INDEX_URL,
            "entry_count": len(entries),
            "pages": page_summaries,
        },
        "awards": entries,
    }
    output_path.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def selected_pages(keys: list[str] | None) -> list[AwardPage]:
    if not keys:
        return list(DEFAULT_AWARD_PAGES)
    pages = []
    for key in keys:
        if key not in AWARD_PAGES_BY_KEY:
            valid = ", ".join(sorted(AWARD_PAGES_BY_KEY))
            raise SystemExit(f"Unknown award page '{key}'. Valid pages: {valid}")
        pages.append(AWARD_PAGES_BY_KEY[key])
    return pages


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Scrape Baseball-Reference awards into mlb_references/awards.json")
    parser.add_argument("--page", action="append", dest="pages", help="Award page key to scrape; can be passed multiple times")
    parser.add_argument("--delay", type=float, default=DEFAULT_DELAY_SECONDS, help="Delay between Baseball-Reference requests")
    parser.add_argument("--output", type=Path, default=REFERENCES_DIR / "awards.json", help="Output JSON path")
    parser.add_argument("--list-pages", action="store_true", help="List known award page keys and exit")
    args = parser.parse_args(argv)

    if args.list_pages:
        for page in DEFAULT_AWARD_PAGES:
            print(f"{page.key}: {page.label} ({page.path})")
        return 0

    pages = selected_pages(args.pages)
    entries, page_summaries = scrape_awards(pages, delay=args.delay)
    write_awards_file(entries, page_summaries, args.output)
    print(f"\nSaved {len(entries)} award entries to {args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
