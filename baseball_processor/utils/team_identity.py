"""Display aliases without rewriting historical identities or source IDs."""

DISPLAY_ALIASES = {
    "NYN": "NYM", "NYA": "NYY", "SFN": "SF", "LAN": "LAD",
    "SDN": "SD", "SLN": "STL", "CHN": "CHC", "CHA": "CWS",
    "CHW": "CWS", "KCA": "KC", "TBA": "TB", "WAS": "WSH",
    "WSN": "WSH", "FLO": "FLA", "ANA": "LAA",
}


def display_team(code):
    if not isinstance(code, str):
        return code
    return ", ".join(DISPLAY_ALIASES.get(s.strip(), s.strip()) for s in code.split(","))


def normalize_website_teams(value, key=""):
    """Normalize known team fields/text tokens, never identifiers or names."""
    if isinstance(value, list):
        return [normalize_website_teams(v, key) for v in value]
    if isinstance(value, dict):
        return {k: normalize_website_teams(v, k) for k, v in value.items()}
    if isinstance(value, str):
        if key in {"team", "teamCode", "homeTeam", "awayTeam", "opponent", "battingTeam",
                   "springTeam", "regularTeam", "postseasonTeam", "teams"}:
            return display_team(value)
        if key in {"score", "detail", "description"}:
            import re
            return re.sub(r"\b(?:" + "|".join(DISPLAY_ALIASES) + r")\b",
                          lambda m: DISPLAY_ALIASES[m[0]], value)
    return value
