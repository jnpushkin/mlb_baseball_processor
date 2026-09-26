"""Resolve game uniforms without treating a roster's tribute number as permanent."""

import re


def game_jersey(player, game, side):
    """Return (number, context); withhold an unsupported post-Rivera #42.

    Historical Stats API boxscores and dated rosters can both retain a stray 42
    on ordinary game dates. A person's primaryNumber is current, not historical,
    so it is not a safe fallback. Keep raw cache values intact for investigation.
    """
    info = game.get("basic_info", {})
    date = str(info.get("date_yyyymmdd", ""))
    game_type = (info.get("game_type") or "regular").lower()
    # MLB's league-wide observance began in 2009. Do not infer tributes in
    # spring/exhibition games or in April 2020 (the season had not started).
    # https://www.mlb.com/robinson-training-complex/jackie-robinson-day
    scheduled_tribute = (
        len(date) == 8 and date.isdigit() and date >= "20090415"
        and date[4:] == "0415" and date[:4] != "2020"
        and game_type == "regular"
    )
    # Delayed/team-specific observances require a game-specific cited record.
    tribute = game.get("uniform_tributes", {}).get(side, {})
    verified_tribute = tribute.get("type") == "jackie_robinson_day" and bool(tribute.get("source"))
    if scheduled_tribute or verified_tribute:
        return "42", "jackie-robinson-day"

    raw = player.get("jersey_number")
    number = str(raw).strip() if raw is not None else ""
    if not re.fullmatch(r"[0-9]{1,2}", number):
        return "", ""
    number = "00" if number == "00" else str(int(number))
    # Rivera was the last grandfathered wearer, retiring in 2013. Preserve
    # earlier wearers; do not invent a replacement number for later bad data.
    # https://www.mlb.com/news/mariano-rivera-is-last-player-to-wear-no-42-c303033550
    if number == "42" and (not re.fullmatch(r"[0-9]{8}", date) or date >= "20140101"):
        return "", ""
    return number, "regular"
