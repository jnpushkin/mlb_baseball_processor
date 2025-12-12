import re
from pathlib import Path
import os

# === Directory and File Path Configuration ===
# Resolve project root as:
# 1) MLB_TRACKER_DIR env var (if set)
# 2) otherwise, the repository root (derived from this file location)
_ENV_BASE = os.environ.get("MLB_TRACKER_DIR")
BASE_DIR = Path(_ENV_BASE).expanduser() if _ENV_BASE else Path(__file__).resolve().parent.parent.parent

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
    'Detroit Tigers': 'DET',
    'Houston Astros': 'HOU',
    'Kansas City Royals': 'KCA',
    "Los Angeles Angels of Anaheim": "ANA",
    "Los Angeles Angels": "ANA",
    'Minnesota Twins': 'MIN',
    'New York Yankees': 'NYA',
    'Oakland Athletics': 'OAK',
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