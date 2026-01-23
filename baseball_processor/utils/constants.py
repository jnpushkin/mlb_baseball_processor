import re
from pathlib import Path
import os

# === Directory and File Path Configuration ===
# Resolve project root as:
# 1) MLB_TRACKER_DIR env var (if set)
# 2) otherwise, the repository root (derived from this file location)
def _find_project_root():
    """Find the project root directory by looking for .project_root marker file.
    
    Searches upward from this file's location until finding .project_root,
    falls back to MLB_TRACKER_DIR environment variable, or uses parent.parent.parent
    as last resort.
    
    Returns:
        Path: Project root directory
    """
    # Method 1: Check environment variable first (highest priority)
    env_base = os.environ.get("MLB_TRACKER_DIR")
    if env_base:
        path = Path(env_base).expanduser()
        if path.exists():
            return path
    
    # Method 2: Look for .project_root marker file (recommended)
    current = Path(__file__).resolve()
    for parent in [current] + list(current.parents):
        marker = parent / ".project_root"
        if marker.exists():
            return parent
    
    # Method 3: Fall back to parent.parent.parent (legacy behavior)
    return Path(__file__).resolve().parent.parent.parent


# Set BASE_DIR using the robust finder
BASE_DIR = _find_project_root()

# Validate that BASE_DIR looks correct (has expected subdirectories)
_EXPECTED_DIRS = ["cache", "mlb_references", "baseball_processor"]
if not all((BASE_DIR / dirname).exists() for dirname in _EXPECTED_DIRS if dirname != "cache"):
    import warnings
    warnings.warn(
        f"BASE_DIR may be incorrect: {BASE_DIR}\n"
        f"Expected to find: {_EXPECTED_DIRS}\n"
        f"Consider creating a .project_root marker file or setting MLB_TRACKER_DIR environment variable",
        RuntimeWarning
    )

CACHE_DIR = BASE_DIR / "cache"
CACHE_DIR.mkdir(parents=True, exist_ok=True)
REFERENCES_DIR = BASE_DIR / "mlb_references"
RETROSHEET_DIR = BASE_DIR / "retrosheet-master"
REGISTER_DIR = BASE_DIR / "register-master"

# Reference data files
SPLASH_HITS_FILE = REFERENCES_DIR / "splash_hits_all_lines.csv"
MCCOVEY_COVE_FILE = REFERENCES_DIR / "other_mccovey_cove_hr.csv"
EUTAW_FILE = REFERENCES_DIR / "Eutaw_Street_Homeruns.csv"
POOL_HR_FILE = REFERENCES_DIR / "Chase_Field_Pool_HRs.csv"
HOF_FILE = REFERENCES_DIR / "HOF.csv"
BIOFILE_PATH = RETROSHEET_DIR / "reference" / "biofile0.csv"

# Default input directory
DEFAULT_INPUT_DIR = BASE_DIR / "Current Season Games"

# === BASEBALL CONSTANTS ===
BASEBALL_POSITIONS = ["HP", "1B", "2B", "3B", "LF", "RF"]

# Common stat columns
BATTING_STATS = ["AB", "H", "R", "RBI", "HR", "2B", "3B", "BB", "SO", "SB", "CS"]
PITCHING_STATS = ["IP", "H", "R", "ER", "BB", "SO", "HR"]

# Date formats for parsing
DATE_FORMATS = ["%m/%d/%Y", "%m/%d/%y", "%Y-%m-%d", "%B %d, %Y", "%b %d, %Y"]

# Excel column sets
MILESTONE_BASE_COLUMNS = ["Date", "Player", "Team", "Opponent", "Score", "Detail", "GameID"]
PLAYER_BASE_COLUMNS = ["Player", "Player ID", "Team", "Opponent"]

# Excel number formats
DECIMAL_2_CENTER = ("0.00", "center")
DECIMAL_3_CENTER = ("0.000", "center")
INTEGER_CENTER = ("0", "center")
COMMA_NUMBER = ("#,##0", "center")
DATE_CENTER = ("mm/dd/yyyy", "center")

# === TEAM MAPPINGS ===
RETROSHEET_CODES = {
    'Florida Marlins': 'FLO',
    'Miami Marlins': 'MIA',
    'Anaheim Angels': 'ANA',
    'Baltimore Orioles': 'BAL',
    'Boston Red Sox': 'BOS',
    'Chicago White Sox': 'CHA',
    'Cleveland Indians': 'CLE',
    'Cleveland Guardians': 'CLE',
    'Detroit Tigers': 'DET',
    'Houston Astros': 'HOU',
    'Kansas City Royals': 'KCA',
    "Los Angeles Angels of Anaheim": "ANA",
    "Los Angeles Angels": "ANA",
    'Minnesota Twins': 'MIN',
    'New York Yankees': 'NYA',
    'Oakland Athletics': 'OAK',
    'Athletics': 'ATH',
    'Seattle Mariners': 'SEA',
    'Tampa Bay Devil Rays': 'TBA',
    'Tampa Bay Rays': 'TBA',
    'Texas Rangers': 'TEX',
    'Toronto Blue Jays': 'TOR',
    'Arizona Diamondbacks': 'ARI',
    'Atlanta Braves': 'ATL',
    'Chicago Cubs': 'CHN',
    'Cincinnati Reds': 'CIN',
    'Colorado Rockies': 'COL',
    'Los Angeles Dodgers': 'LAN',
    'San Diego Padres': 'SDN',
    'Milwaukee Brewers': 'MIL',
    'New York Mets': 'NYN',
    'Philadelphia Phillies': 'PHI',
    'Pittsburgh Pirates': 'PIT',
    'San Francisco Giants': 'SFN',
    'St. Louis Cardinals': 'SLN',
    'Washington Nationals': 'WAS',
}

# === MLB DIVISIONS (2013-present, after Houston moved to AL) ===
MLB_DIVISIONS = {
    'AL East': ['BAL', 'BOS', 'NYA', 'TBA', 'TOR'],
    'AL Central': ['CHA', 'CLE', 'DET', 'KCA', 'MIN'],
    'AL West': ['ANA', 'HOU', 'OAK', 'SEA', 'TEX'],
    'NL East': ['ATL', 'MIA', 'NYN', 'PHI', 'WAS'],
    'NL Central': ['CHN', 'CIN', 'MIL', 'PIT', 'SLN'],
    'NL West': ['ARI', 'COL', 'LAN', 'SDN', 'SFN'],
}

# Reverse lookup: team code to division
TEAM_TO_DIVISION = {}
for _div, _teams in MLB_DIVISIONS.items():
    for _team in _teams:
        TEAM_TO_DIVISION[_team] = _div

# Reverse lookup: team code to league (AL or NL)
TEAM_TO_LEAGUE = {}
for _div, _teams in MLB_DIVISIONS.items():
    _league = 'AL' if _div.startswith('AL') else 'NL'
    for _team in _teams:
        TEAM_TO_LEAGUE[_team] = _league

# Reverse of RETROSHEET_CODES: code to full team name
CODE_TO_TEAM = {v: k for k, v in RETROSHEET_CODES.items() if k not in ['Florida Marlins', 'Anaheim Angels', 'Tampa Bay Devil Rays', 'Cleveland Indians', 'Los Angeles Angels of Anaheim']}

# Current home stadiums for each team
CURRENT_STADIUMS = {
    'BAL': 'Oriole Park at Camden Yards',
    'BOS': 'Fenway Park',
    'NYA': 'Yankee Stadium',
    'TBA': 'Tropicana Field',
    'TOR': 'Rogers Centre',
    'CHA': 'Guaranteed Rate Field',
    'CLE': 'Progressive Field',
    'DET': 'Comerica Park',
    'KCA': 'Kauffman Stadium',
    'MIN': 'Target Field',
    'ANA': 'Angel Stadium',
    'HOU': 'Minute Maid Park',
    'OAK': 'Oakland Coliseum',
    'SEA': 'T-Mobile Park',
    'TEX': 'Globe Life Field',
    'ATL': 'Truist Park',
    'MIA': 'loanDepot park',
    'NYN': 'Citi Field',
    'PHI': 'Citizens Bank Park',
    'WAS': 'Nationals Park',
    'CHN': 'Wrigley Field',
    'CIN': 'Great American Ball Park',
    'MIL': 'American Family Field',
    'PIT': 'PNC Park',
    'SLN': 'Busch Stadium',
    'ARI': 'Chase Field',
    'COL': 'Coors Field',
    'LAN': 'Dodger Stadium',
    'SDN': 'Petco Park',
    'SFN': 'Oracle Park',
}

# Stadium aliases for matching variations
STADIUM_ALIASES = {
    'Oriole Park at Camden Yards': ['Camden Yards', 'Oriole Park'],
    'Guaranteed Rate Field': ['U.S. Cellular Field', 'Comiskey Park II', 'New Comiskey Park'],
    'Progressive Field': ['Jacobs Field', 'The Jake'],
    'Target Field': [],
    'Angel Stadium': ['Angel Stadium of Anaheim', 'Edison International Field'],
    'Minute Maid Park': ['Enron Field', 'Astros Field'],
    'Oakland Coliseum': ['O.co Coliseum', 'RingCentral Coliseum', 'McAfee Coliseum', 'Network Associates Coliseum', 'Oakland-Alameda County Coliseum'],
    'T-Mobile Park': ['Safeco Field'],
    'Globe Life Field': [],
    'Truist Park': ['SunTrust Park'],
    'loanDepot park': ['Marlins Park', 'LoanDepot Park'],
    'Citi Field': [],
    'Citizens Bank Park': [],
    'Nationals Park': [],
    'American Family Field': ['Miller Park'],
    'Great American Ball Park': [],
    'Oracle Park': ['AT&T Park', 'SBC Park', 'Pacific Bell Park'],
    'Petco Park': [],
    'Dodger Stadium': [],
    'Coors Field': [],
    'Chase Field': ['Bank One Ballpark'],
    'Busch Stadium': ['Busch Stadium III', 'New Busch Stadium'],
    'PNC Park': [],
    'Wrigley Field': [],
    'Fenway Park': [],
    'Yankee Stadium': ['New Yankee Stadium', 'Yankee Stadium III'],
    'Tropicana Field': [],
    'Rogers Centre': ['SkyDome'],
    'Comerica Park': [],
    'Kauffman Stadium': [],
}

# Milestone thresholds for badges
MILESTONE_COUNTS = [1, 5, 10, 15, 20, 25, 30, 35, 40, 45, 50, 75, 100, 150, 200]
GAME_MILESTONES = [1, 10, 25, 50, 75, 100, 150, 200, 250, 300, 400, 500, 750, 1000]

TEAM_ALIAS = {
    "Tampa Bay Devil Rays": "TB",
}

STADIUM_ALIAS = {
    "AT&T Park": "Oracle Park",
    "O.co Coliseum": "Oakland Coliseum",
    "RingCentral Coliseum": "Oakland Coliseum",
}

# Stat label normalization mapping
LABEL_MAP = {
    "Home Runs": "HR",
    "HR": "HR",
    "2B": "2B",
    "3B": "3B",
    "TB": "TB",
    "RBI": "RBI",
    "SF": "SF",
    "HBP": "HBP",
    "SB": "SB",
    "Stolen Bases": "SB",
    "CS": "CS",
    "Caught Stealing": "CS"
}

# === REGEX PATTERNS ===
_GID_SPLIT_RE = re.compile(r"[,\s]+")
_GID_DATE_RE = re.compile(r"^[A-Za-z]{3}(\d{8})[A-Za-z0-9]*$")

# === EXCEL COLOR SCHEME ===
EXCEL_COLORS = {
    'primary_blue': '#1B365D',
    'secondary_blue': '#4A90A4', 
    'light_blue': '#E8F4F8',
    'accent_green': '#2E7D32',
    'light_green': '#E8F5E8',
    'warning_orange': '#F57C00',
    'light_orange': '#FFF3E0',
    'error_red': '#C62828',
    'light_red': '#FFEBEE',
    'neutral_gray': '#757575',
    'light_gray': '#F5F5F5',
    'white': '#FFFFFF'
}