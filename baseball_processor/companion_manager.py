"""Authoritative companion editing for the authenticated local manager."""

import csv
import hashlib
import io
import json
from pathlib import Path

from .utils.companions import companion_map, normalize_companion_game_id


class CompanionConflict(ValueError):
    pass


def read_records(root):
    root = Path(root)
    archive = json.loads((root / "data.json").read_text())
    path = root / "companions.csv"
    content = path.read_bytes() if path.exists() else b""
    rows = list(csv.DictReader(io.StringIO(content.decode("utf-8-sig")))) if content else []
    mapping = companion_map(rows)
    games = [
        {
            **{key: game.get(key, "") for key in ("gameId", "date", "homeTeam", "awayTeam", "venue")},
            "companions": mapping.get(normalize_companion_game_id(game["gameId"]), []),
            "gameNumber": int(game["gameId"][-1]) if game["gameId"][-1] in ("1", "2") else None,
        }
        for game in archive["games"]
    ]
    return {
        "games": games,
        "names": sorted({name for names in mapping.values() for name in names}),
        "revision": hashlib.sha256(content).hexdigest(),
    }


def validate_edit(root, payload):
    if not isinstance(payload, dict):
        raise ValueError("Invalid edit")
    records = read_records(root)
    if payload.get("revision") != records["revision"]:
        raise CompanionConflict("Companions changed in another edit. Reload the game list before saving.")
    if not any(game["gameId"] == payload.get("gameId") for game in records["games"]):
        raise ValueError("Choose a game from the attended archive")
    names = payload.get("companions")
    if not isinstance(names, list) or len(names) > 30:
        raise ValueError("Choose up to 30 companions")
    if any(
        not isinstance(name, str)
        or not name.strip()
        or len(name) > 60
        or "|" in name
        or any(ord(char) < 32 for char in name)
        for name in names
    ):
        raise ValueError("Names must be 1–60 characters without separators or control characters")
    canonical = {name.casefold(): name for name in records["names"]}
    cleaned = {}
    for name in names:
        name = name.strip()
        cleaned.setdefault(name.casefold(), canonical.get(name.casefold(), name))
    return {**payload, "companions": list(cleaned.values())}


def save_edit(root, payload):
    """Recheck queued edits, then atomically persist without dropping other games."""
    root = Path(root)
    payload = validate_edit(root, payload)
    path = root / "companions.csv"
    content = path.read_bytes() if path.exists() else b""
    reader = csv.DictReader(io.StringIO(content.decode("utf-8-sig")))
    rows = list(reader)
    fields = list(dict.fromkeys([*(reader.fieldnames or []), "GameID", "Companions", "Date", "Matchup", "Venue"]))
    mapping = companion_map(rows)
    merged = {}
    for row in rows:
        game_id = normalize_companion_game_id(row["GameID"])
        merged.setdefault(game_id, {**row, "GameID": game_id})
    game = next(g for g in read_records(root)["games"] if g["gameId"] == payload["gameId"])
    game_id = normalize_companion_game_id(game["gameId"])
    mapping[game_id] = payload["companions"]
    merged.setdefault(
        game_id,
        {
            "GameID": game_id,
            "Date": game["date"],
            "Matchup": f"{game['awayTeam']} @ {game['homeTeam']}",
            "Venue": game["venue"],
        },
    )
    for key, row in merged.items():
        row["Companions"] = "|".join(mapping.get(key, []))
    # A content-addressed backup allows a mistaken selection to be recovered.
    backup = root / "cache" / "companion_backups" / f"{hashlib.sha256(content).hexdigest()}.csv"
    backup.parent.mkdir(parents=True, exist_ok=True)
    if not backup.exists():
        backup.write_bytes(content)
    temp = path.with_suffix(".csv.tmp")
    with temp.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, lineterminator="\n")
        writer.writeheader()
        writer.writerows(merged.values())
    if (path.read_bytes() if path.exists() else b"") != content:
        temp.unlink()
        raise CompanionConflict("Companion records changed while saving. Reload and retry.")
    temp.replace(path)
    return game_id
