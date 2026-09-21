"""Join companion records without losing names to spreadsheet ID formatting."""

import re


def normalize_companion_game_id(value):
    """Repair whitespace/zero decimals while preserving source IDs and game numbers."""
    text = str(value or "").strip()
    compact = re.sub(r"\s+", "", text).upper()
    match = re.fullmatch(r"([A-Z]{2,4}\d{9})(?:\.0+)?", compact)
    return match.group(1) if match else text


def companion_map(rows):
    """Merge duplicate rows; a later blank row must not erase known companions."""
    result = {}
    for row in rows:
        game_id = normalize_companion_game_id(row.get("GameID", ""))
        names = str(row.get("Companions") or "").strip()
        if not game_id or not names or names.lower() == "nan":
            continue
        companions = result.setdefault(game_id, [])
        for name in names.split("|"):
            name = name.strip()
            if name and name not in companions:
                companions.append(name)
    return result
