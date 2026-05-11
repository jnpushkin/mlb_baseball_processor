def extract_extra_batting_stats(game):
    """Per-player 2B/3B/HR/SB/CS/HBP/GIDP tallies from play-by-play.

    BREF and the MLB API store these in different places: the per-player
    batting row sometimes carries HR/2B/3B counts, but for BREF games the
    only complete source is the play-by-play. The serializer and the
    leaderboard aggregator both need to agree on the totals, so they share
    this single extraction path.

    Returns ``{player_id: {'2B': n, '3B': n, ...}}`` for players who appear
    in the play-by-play. Players with no play-by-play events get an empty
    dict — callers should fall back to direct player record fields.
    """
    plays = game.get('play_by_play', [])
    if not plays:
        return {}

    name_to_id = {}
    for side in ('home', 'away'):
        for p in game.get('batting', {}).get(side, []):
            name = p.get('name', '').replace(' ', ' ')
            pid = p.get('player_id', '')
            if pid:
                name_to_id[name] = pid

    out = {}
    for play in plays:
        batter = play.get('batter', '').replace(' ', ' ')
        pid = name_to_id.get(batter)
        if not pid:
            continue
        stats = out.setdefault(pid, {'2B': 0, '3B': 0, 'HR': 0, 'SB': 0, 'CS': 0, 'HBP': 0, 'GIDP': 0})
        event_type = play.get('event_type', '')
        desc_lower = (play.get('description', '') or '').lower()
        # Filter false positives baked into older cached plays: "Ground Ball
        # Double Play" and "Triple Play" descriptions used to set
        # `double`/`triple` True. The parser is fixed for new games, but the
        # cache still has the bad flag — drop it when the phrase shows up.
        if (play.get('double') or event_type == 'double') and 'double play' not in desc_lower:
            stats['2B'] += 1
        if (play.get('triple') or event_type == 'triple') and 'triple play' not in desc_lower:
            stats['3B'] += 1
        if play.get('home_run') or event_type == 'home_run':
            stats['HR'] += 1
        if play.get('hit_by_pitch') or event_type == 'hit_by_pitch':
            stats['HBP'] += 1
        if play.get('double_play') or event_type == 'grounded_into_double_play':
            stats['GIDP'] += 1
        desc = play.get('description', '').lower()
        if 'steals' in desc or 'stolen base' in desc:
            stats['SB'] += 1
        if 'caught stealing' in desc or play.get('Details') == 'CS':
            stats['CS'] += 1
    return out


class StatUtils:
    """Shared stat conversions and small helpers."""

    @staticmethod
    def ip_to_outs(ip):
        """Convert baseball IP string/number (e.g., '7.2') to outs (e.g., 23)."""
        try:
            s = str(ip)
            if "." in s:
                whole, frac = s.split(".")
                return int(whole) * 3 + int(frac)
            return int(float(s)) * 3
        except Exception:
            return None

    @staticmethod
    def outs_to_baseball_ip(outs):
        """Convert outs (int) back to baseball IP float notation (e.g., 23 -> 7.2)."""
        try:
            outs = int(outs)
            whole = outs // 3
            rem = outs % 3
            return float(f"{whole}.{rem}")
        except Exception:
            return 0.0

# Legacy functions for backwards compatibility
