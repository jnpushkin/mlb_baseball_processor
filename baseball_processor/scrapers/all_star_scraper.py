"""
Baseball-Reference All-Star Participant Scraper
==============================================
Scrapes Baseball-Reference All-Star Game roster tables into one normalized
JSON file for website checklists.

Usage:
    python3 -m baseball_processor.scrapers.all_star_scraper
    python3 -m baseball_processor.scrapers.all_star_scraper --year 2025
    python3 -m baseball_processor.scrapers.all_star_scraper --list-games

The output defaults to mlb_references/all_star_participants.json.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
import time
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
from .awards_scraper import PLAYER_HREF_RE, clean_text, enrich_entry_names


BASE_URL = "https://www.baseball-reference.com"
ALL_STAR_INDEX_URL = f"{BASE_URL}/allstar/"
DEFAULT_DELAY_SECONDS = 3.2
ALL_STAR_GAME_HREF_RE = re.compile(r"^/allstar/(\d{4})-allstar-game(?:-(\d+))?\.shtml$")


def game_key(year: int, game_number: int) -> str:
    return f"{year}-{game_number}" if game_number > 1 else str(year)


def game_label(year: int, game_number: int) -> str:
    return f"{year} All-Star Game {game_number}" if game_number > 1 else f"{year} All-Star Game"


def parse_game_href(href: str) -> dict[str, Any] | None:
    match = ALL_STAR_GAME_HREF_RE.match(href)
    if not match:
        return None
    year = int(match.group(1))
    game_number = int(match.group(2) or 1)
    return {
        "year": year,
        "gameNumber": game_number,
        "gameKey": game_key(year, game_number),
        "label": game_label(year, game_number),
        "path": href,
        "url": urljoin(BASE_URL, href),
    }


def parse_all_star_index(html: str) -> list[dict[str, Any]]:
    soup = BeautifulSoup(html, "html.parser")
    games: list[dict[str, Any]] = []
    seen = set()
    for link in soup.find_all("a", href=True):
        game = parse_game_href(link["href"])
        if not game or game["gameKey"] in seen:
            continue
        seen.add(game["gameKey"])
        games.append(game)
    return games


def fetch_url(session, url: str) -> str:
    headers = {
        "User-Agent": (
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
            "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        ),
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.9",
    }
    response = get_with_retry(session, url, headers=headers, timeout=30)
    response.encoding = "utf-8"
    if response.status_code == 429:
        raise RuntimeError("Baseball-Reference returned HTTP 429. Wait at least 15 minutes before retrying.")
    response.raise_for_status()
    return response.text


def soup_with_comment_tables(html: str) -> BeautifulSoup:
    soup = BeautifulSoup(html, "html.parser")
    for comment in soup.find_all(string=lambda text: isinstance(text, Comment)):
        if "<table" in comment:
            soup.append(BeautifulSoup(comment, "html.parser"))
    return soup


def table_caption(table: Tag) -> str:
    caption = table.find("caption")
    return clean_text(caption.get_text(" ", strip=True)) if caption else ""


def roster_league_from_caption(caption: str) -> str:
    if caption == "AL All-Stars":
        return "AL"
    if caption == "NL All-Stars":
        return "NL"
    return ""


def player_link_from_cell(cell: Tag) -> dict[str, str] | None:
    link = cell.find("a", href=True)
    if not link:
        return None
    match = PLAYER_HREF_RE.match(link["href"])
    if not match:
        return None
    return {
        "player_id": match.group(1),
        "name": clean_text(link.get_text(" ", strip=True)),
        "source_url": urljoin(BASE_URL, link["href"]),
    }


def parse_roster_table(table: Tag, game: dict[str, Any]) -> list[dict[str, Any]]:
    caption = table_caption(table)
    league = roster_league_from_caption(caption)
    if not league:
        return []

    rows = table.find_all("tr", recursive=False)
    section = "starter"
    participants: list[dict[str, Any]] = []
    seen_players = set()
    roster_order = 0

    for row in rows:
        cells = row.find_all(["th", "td"], recursive=False)
        if len(cells) < 2:
            continue

        marker = clean_text(cells[1].get_text(" ", strip=True))
        if cells[1].find("strong"):
            if marker == "Manager":
                section = "manager"
            elif marker == "Reserves":
                section = "reserve"
            continue

        player = player_link_from_cell(cells[1])
        if not player:
            continue
        if section == "manager":
            continue

        player_id = player["player_id"]
        if player_id in seen_players:
            continue
        seen_players.add(player_id)

        batting_order = clean_text(cells[0].get_text(" ", strip=True))
        position = clean_text(cells[2].get_text(" ", strip=True)) if len(cells) > 2 else ""
        roster_order += 1
        selection = "Reserve" if section == "reserve" else "Starting Pitcher" if position == "P" and not batting_order else "Starter"
        participants.append({
            "year": game["year"],
            "game_number": game["gameNumber"],
            "game_key": game["gameKey"],
            "game_label": game["label"],
            "league": league,
            "name": player["name"],
            "entity_type": "player",
            "entity_id": player_id,
            "player_id": player_id,
            "position": position,
            "selection": selection,
            "batting_order": batting_order,
            "roster_order": roster_order,
            "source_url": player["source_url"],
            "game_url": game["url"],
        })

    return participants


def parse_all_star_game_html(html: str, game: dict[str, Any]) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    soup = soup_with_comment_tables(html)
    participants: list[dict[str, Any]] = []
    table_summaries: list[dict[str, Any]] = []
    for table in soup.find_all("table"):
        caption = table_caption(table)
        if caption not in {"AL All-Stars", "NL All-Stars"}:
            continue
        before = len(participants)
        participants.extend(parse_roster_table(table, game))
        table_summaries.append({
            "caption": caption,
            "entries": len(participants) - before,
        })
    return participants, table_summaries


def sort_participants(participants: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return sorted(
        participants,
        key=lambda row: (
            -(row.get("year") or 0),
            -(row.get("game_number") or 0),
            row.get("league", ""),
            row.get("selection", ""),
            row.get("position", ""),
            row.get("name", ""),
        ),
    )


def selected_games(games: list[dict[str, Any]], years: list[int] | None, game_keys: list[str] | None) -> list[dict[str, Any]]:
    selected = games
    if years:
        year_set = set(years)
        selected = [game for game in selected if game["year"] in year_set]
    if game_keys:
        key_set = set(game_keys)
        selected = [game for game in selected if game["gameKey"] in key_set]
    return selected


def scrape_all_star_participants(
    years: list[int] | None = None,
    game_keys: list[str] | None = None,
    delay: float = DEFAULT_DELAY_SECONDS,
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    session = create_retry_session()
    print(f"Fetching {ALL_STAR_INDEX_URL}...")
    index_html = fetch_url(session, ALL_STAR_INDEX_URL)
    games = selected_games(parse_all_star_index(index_html), years, game_keys)

    all_participants: list[dict[str, Any]] = []
    game_summaries: list[dict[str, Any]] = []
    for idx, game in enumerate(games):
        if idx > 0 and delay > 0:
            time.sleep(delay)
        print(f"Fetching {game['url']}...")
        html = fetch_url(session, game["url"])
        participants, tables = parse_all_star_game_html(html, game)
        all_participants.extend(participants)
        game_summaries.append({
            "key": game["gameKey"],
            "label": game["label"],
            "year": game["year"],
            "gameNumber": game["gameNumber"],
            "url": game["url"],
            "entries": len(participants),
            "tables": tables,
        })
        print(f"  Found {len(participants)} All-Star participant entries")

    return sort_participants(enrich_entry_names(all_participants)), game_summaries


def write_all_star_file(participants: list[dict[str, Any]], game_summaries: list[dict[str, Any]], output_path: Path) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "metadata": {
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "source": "Baseball-Reference All-Star Game roster tables",
            "source_index_url": ALL_STAR_INDEX_URL,
            "entry_count": len(participants),
            "games": game_summaries,
        },
        "participants": participants,
    }
    output_path.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Scrape Baseball-Reference All-Star participants into mlb_references/all_star_participants.json")
    parser.add_argument("--year", action="append", type=int, dest="years", help="All-Star year to scrape; can be passed multiple times")
    parser.add_argument("--game-key", action="append", dest="game_keys", help="Specific game key to scrape, e.g. 2025 or 1962-2")
    parser.add_argument("--delay", type=float, default=DEFAULT_DELAY_SECONDS, help="Delay between Baseball-Reference requests")
    parser.add_argument("--output", type=Path, default=REFERENCES_DIR / "all_star_participants.json", help="Output JSON path")
    parser.add_argument("--list-games", action="store_true", help="List All-Star game keys from the BRef index and exit")
    args = parser.parse_args(argv)

    if args.list_games:
        session = create_retry_session()
        index_html = fetch_url(session, ALL_STAR_INDEX_URL)
        for game in parse_all_star_index(index_html):
            print(f"{game['gameKey']}: {game['label']} ({game['path']})")
        return 0

    participants, game_summaries = scrape_all_star_participants(args.years, args.game_keys, args.delay)
    write_all_star_file(participants, game_summaries, args.output)
    print(f"\nSaved {len(participants)} All-Star participant entries to {args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
