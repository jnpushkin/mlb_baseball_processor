import re
import unicodedata
import os
import pandas as pd
from datetime import datetime
from .constants import _GID_SPLIT_RE, _GID_DATE_RE
from .log import warn


def safe_get_int(data: dict, key: str, default: int = 0) -> int:
    """Safely extract integer from dictionary."""
    try:
        value = data.get(key, default)
        return int(value) if value is not None else default
    except (ValueError, TypeError):
        return default


def safe_get_str(data: dict, key: str, default: str = "") -> str:
    """Safely extract string from dictionary."""
    value = data.get(key, default)
    return str(value) if value is not None else default


def _parse_gid_date(gid: str):
    """Parse date from game ID."""
    if not gid:
        return None
    gid = gid.strip()
    m = _GID_DATE_RE.match(gid)
    if m:
        try:
            return datetime.strptime(m.group(1), "%Y%m%d").date()
        except ValueError:
            return None
    elif len(gid) >= 11 and gid[3:11].isdigit():
        try:
            return datetime.strptime(gid[3:11], "%Y%m%d").date()
        except ValueError:
            return None
    return None

def create_bbref_hyperlink(player_id):
    """Create a Baseball-Reference hyperlink for a player ID."""
    if not player_id or player_id == "UNKNOWN":
        return player_id
    
    first_letter = player_id[0].lower()
    url = f"https://www.baseball-reference.com/players/{first_letter}/{player_id}.shtml"
    hyperlink = f'=HYPERLINK("{url}", "{player_id}")'
    
    return hyperlink

def add_player_hyperlinks(df, column_name="Player ID"):
    """Add Baseball-Reference hyperlinks to a Player ID column."""
    if column_name in df.columns:
        df = df.copy()
        df[column_name] = df[column_name].apply(create_bbref_hyperlink)
    return df

def sort_join_gameids_by_date(cell_value, sep_out=", ", dedupe=True):
    """Sort GameIDs inside a string/list by embedded date (YYYYMMDD) and return as a joined string."""
    if cell_value is None:
        return ""
    if isinstance(cell_value, (list, tuple, set)):
        raw_ids = [str(x).strip() for x in cell_value if x and str(x).strip()]
    else:
        raw_ids = [s.strip() for s in _GID_SPLIT_RE.split(str(cell_value)) if s.strip()]

    sortable = []
    for idx, gid in enumerate(raw_ids):
        d = _parse_gid_date(gid)
        sort_key = (d or datetime.max.date(), idx)
        sortable.append((sort_key, gid))

    sortable.sort(key=lambda t: t[0])

    seen = set()
    result = []
    for _, gid in sortable:
        if not dedupe or gid not in seen:
            result.append(gid)
            if dedupe:
                seen.add(gid)

    return sep_out.join(result)

def ensure_sorted_gameids(df):
    """Ensure any DataFrame with a 'GameIDs' column has it sorted chronologically."""
    try:
        import pandas as pd
        if hasattr(df, "columns") and "GameIDs" in df.columns:
            df = df.copy()
            df["GameIDs"] = df["GameIDs"].apply(sort_join_gameids_by_date)
        return df
    except Exception:
        return df

def join_sorted_gameids(ids_iterable):
    """Join GameIDs into a comma-separated string in chronological order."""
    return sort_join_gameids_by_date(list(ids_iterable))

def normalize_name(name):
    """Normalize name to ASCII for reliable matching (e.g., Urías → Urias)."""
    return unicodedata.normalize("NFKD", name).encode("ASCII", "ignore").decode("utf-8").strip().lower()

# Team code mappings - centralized for consistency
# NOTE: Keep this minimal - we want original codes (FLA, ATH, LAA, etc.) to display in game logs
# Normalization for tracking purposes happens separately in serializers.py and react_app.py
_TEAM_CODE_ALIASES = {
    # Only include non-standard codes that should always be converted
    "Tampa Bay Devil Rays": "TB",  # This is a name, not a code
    "ATH": "OAK",  # Athletics (renamed/relocated) -> Oakland Athletics
}

_TEAM_NAME_TO_CODE = {
    'Los Angeles Angels': 'LAA', 'Baltimore Orioles': 'BAL', 'Boston Red Sox': 'BOS',
    'Chicago White Sox': 'CWS', 'Cleveland Guardians': 'CLE', 'Cleveland Indians': 'CLE',
    'Detroit Tigers': 'DET', 'Houston Astros': 'HOU', 'Kansas City Royals': 'KC',
    'Minnesota Twins': 'MIN', 'New York Yankees': 'NYY', 'Oakland Athletics': 'OAK',
    'Seattle Mariners': 'SEA', 'Tampa Bay Rays': 'TB', 'Texas Rangers': 'TEX',
    'Toronto Blue Jays': 'TOR', 'Arizona Diamondbacks': 'ARI', 'Atlanta Braves': 'ATL',
    'Chicago Cubs': 'CHC', 'Cincinnati Reds': 'CIN', 'Colorado Rockies': 'COL',
    'Miami Marlins': 'MIA', 'Los Angeles Dodgers': 'LAD', 'Milwaukee Brewers': 'MIL',
    'Washington Nationals': 'WSH', 'New York Mets': 'NYM', 'Philadelphia Phillies': 'PHI',
    'Pittsburgh Pirates': 'PIT', 'San Diego Padres': 'SD', 'San Francisco Giants': 'SF',
    'St. Louis Cardinals': 'STL', 'Florida Marlins': 'MIA', 'Tampa Bay Devil Rays': 'TB',
    'Athletics': 'ATH'
}


def unify_team_code(code: str) -> str:
    """Map old team codes to their modern equivalents.

    Use this when you have a team code (e.g., 'FLA') and want the modern equivalent ('MIA').
    """
    if not code:
        return code
    return _TEAM_CODE_ALIASES.get(code, code)


def standardize_team_code(team_name):
    """Convert full team names to standard 2-3 letter codes used in baseball stats.

    Use this when you have a full team name (e.g., 'Baltimore Orioles') and want the code ('BAL').
    """
    if not isinstance(team_name, str) or not team_name.strip():
        return ""

    team_name = team_name.strip()

    if team_name in _TEAM_NAME_TO_CODE:
        return _TEAM_NAME_TO_CODE[team_name]

    for full_name, code in _TEAM_NAME_TO_CODE.items():
        if full_name in team_name or team_name in full_name:
            return code

    return team_name


def _normalize_team_code_for_counts(code: str) -> str:
    """Normalize team codes for aggregation counts (e.g., ATH and OAK are the same)."""
    if code in ("ATH", "OAK"):
        return "OAK"
    return code

def normalize_umpire_name(name):
    """Normalize umpire names."""
    parts = name.strip().split()
    return " ".join(part.replace(".", "") for part in parts)

def load_id_mapping(people_dir):
    """Loads all people-*.csv files and returns BBRef ↔ Retrosheet mapping"""
    people_files = []
    for root, _, files in os.walk(people_dir):
        for f in files:
            if f.startswith("people-") and f.endswith(".csv"):
                people_files.append(os.path.join(root, f))

    if not people_files:
        raise ValueError(f"No people-*.csv files found in {people_dir}")

    df_all = pd.concat([pd.read_csv(f, low_memory=False) for f in people_files], ignore_index=True)
    df_clean = df_all[["key_bbref", "key_retro"]].dropna().drop_duplicates()

    bbref_to_retro = dict(zip(df_clean["key_bbref"], df_clean["key_retro"]))
    retro_to_bbref = dict(zip(df_clean["key_retro"], df_clean["key_bbref"]))

    return bbref_to_retro, retro_to_bbref

def load_final_game_dates(biofile_path):
    df = pd.read_csv(biofile_path)
    df["last_p"] = pd.to_datetime(df["last_p"], format="%Y%m%d", errors="coerce")
    return dict(zip(df["id"], df["last_p"]))

def load_mlb_debuts(csv_folder_path):
    debut_entries = []
    for file in os.listdir(csv_folder_path):
        if not (file.endswith(".csv") and "MLB Debuts" in file):
            continue

        # ─── extract the year from "2013 MLB Debuts.csv" → "2013" ───
        year = os.path.splitext(file)[0][:4]

        path = os.path.join(csv_folder_path, file)
        try:
            df = pd.read_csv(path)
        except Exception as e:
            warn(f"❌ Failed to read {file}: {e}")
            continue

        required = {"Name", "Debut", "Tm", "Name-additional"}
        if not required.issubset(df.columns):
            warn(f"⚠️ Skipping {file} — missing expected columns: {list(df.columns)}")
            continue

        for _, row in df.iterrows():
            raw_md = str(row["Debut"]).strip()
            # Build a full "YYYY Month DD" string, then parse it:
            try:
                dt = datetime.strptime(f"{year} {raw_md}", "%Y %b %d")
            except ValueError:
                # Fallback if month name is full ("May" vs. "M")
                dt = datetime.strptime(f"{year} {raw_md}", "%Y %B %d")

            debut_entries.append({
                "Player":     row["Name"],
                "PlayerID":   row["Name-additional"],
                "Team":       row["Tm"],
                "DebutDate":  dt.strftime("%Y-%m-%d"),
                "DebutYear":  year
            })

    if not debut_entries:
        warn("⚠️ No debut data loaded from CSVs.")
    return debut_entries

def _parse_duration_to_minutes(duration_text):
    """Convert duration string to minutes."""
    if not duration_text:
        return None
    
    match = re.search(r'(\d+):(\d+)', duration_text)
    if match:
        hours = int(match.group(1))
        minutes = int(match.group(2))
        return hours * 60 + minutes
    
    hours_match = re.search(r'(\d+)\s*hour', duration_text, re.IGNORECASE)
    minutes_match = re.search(r'(\d+)\s*min', duration_text, re.IGNORECASE)
    
    hours = int(hours_match.group(1)) if hours_match else 0
    minutes = int(minutes_match.group(1)) if minutes_match else 0
    
    if hours > 0 or minutes > 0:
        return hours * 60 + minutes
    
    return None

def parse_date_from_game_id(game_id):
    """Extract date from a Retrosheet-style game ID.
    
    Args:
        game_id: Game ID like "BAL202505130" or "SFN202507110"
        
    Returns:
        datetime.date object or None if parsing fails
        
    Examples:
        >>> parse_date_from_game_id("BAL202505130")
        datetime.date(2025, 5, 13)
        >>> parse_date_from_game_id("INVALID")
        None
    """
    return _parse_gid_date(game_id)


def format_game_id_as_date(game_id, date_format="%m/%d/%Y"):
    """Convert game ID to formatted date string.
    
    Args:
        game_id: Game ID like "BAL202505130"
        date_format: strftime format string (default: MM/DD/YYYY)
        
    Returns:
        str: Formatted date or empty string if parsing fails
        
    Examples:
        >>> format_game_id_as_date("BAL202505130")
        "05/13/2025"
        >>> format_game_id_as_date("BAL202505130", "%Y-%m-%d")
        "2025-05-13"
    """
    date_obj = parse_date_from_game_id(game_id)
    if date_obj:
        return date_obj.strftime(date_format)
    return ""


def get_year_from_game_id(game_id):
    """Extract year from game ID.
    
    Args:
        game_id: Game ID like "BAL202505130"
        
    Returns:
        int: Year or None if parsing fails
        
    Examples:
        >>> get_year_from_game_id("BAL202505130")
        2025
    """
    date_obj = parse_date_from_game_id(game_id)
    if date_obj:
        return date_obj.year
    return None