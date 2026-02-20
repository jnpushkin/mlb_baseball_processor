"""
MLB Gameday PDF Parser
======================
Parses play-by-play data from MLB Gameday PDF exports.

Usage:
    from baseball_processor.parsers.mlb_pdf_parser import parse_mlb_pdf

    # Parse a PDF file
    game_data = parse_mlb_pdf("/path/to/gameday.pdf")

    # Parse and save to cache
    game_data = parse_mlb_pdf("/path/to/gameday.pdf", save_to_cache=True)
"""

import re
import json
from pathlib import Path
from datetime import datetime
from typing import Optional

# Try to import PDF libraries
try:
    import fitz  # PyMuPDF
    HAS_PYMUPDF = True
except ImportError:
    HAS_PYMUPDF = False

try:
    import pdfplumber
    HAS_PDFPLUMBER = True
except ImportError:
    HAS_PDFPLUMBER = False


# Team code mapping
TEAM_NAME_TO_CODE = {
    'orioles': 'BAL', 'baltimore': 'BAL',
    'red sox': 'BOS', 'boston': 'BOS',
    'yankees': 'NYY', 'new york yankees': 'NYY',
    'rays': 'TB', 'tampa bay': 'TB',
    'blue jays': 'TOR', 'toronto': 'TOR',
    'white sox': 'CWS', 'chicago white sox': 'CWS',
    'guardians': 'CLE', 'indians': 'CLE', 'cleveland': 'CLE',
    'tigers': 'DET', 'detroit': 'DET',
    'royals': 'KC', 'kansas city': 'KC',
    'twins': 'MIN', 'minnesota': 'MIN',
    'astros': 'HOU', 'houston': 'HOU',
    'angels': 'LAA', 'los angeles angels': 'LAA',
    'athletics': 'ATH', 'oakland': 'OAK', "a's": 'ATH',
    'mariners': 'SEA', 'seattle': 'SEA',
    'rangers': 'TEX', 'texas': 'TEX',
    'braves': 'ATL', 'atlanta': 'ATL',
    'marlins': 'MIA', 'miami': 'MIA', 'florida': 'FLA',
    'mets': 'NYM', 'new york mets': 'NYM',
    'phillies': 'PHI', 'philadelphia': 'PHI',
    'nationals': 'WSH', 'washington': 'WSH',
    'cubs': 'CHC', 'chicago cubs': 'CHC',
    'reds': 'CIN', 'cincinnati': 'CIN',
    'brewers': 'MIL', 'milwaukee': 'MIL',
    'pirates': 'PIT', 'pittsburgh': 'PIT',
    'cardinals': 'STL', 'st. louis': 'STL',
    'diamondbacks': 'ARI', 'd-backs': 'ARI', 'arizona': 'ARI',
    'rockies': 'COL', 'colorado': 'COL',
    'dodgers': 'LAD', 'los angeles dodgers': 'LAD',
    'padres': 'SD', 'san diego': 'SD',
    'giants': 'SF', 'san francisco': 'SF',
}


def get_team_code(team_name: str) -> str:
    """Convert team name to code."""
    name_lower = team_name.lower().strip()
    for key, code in TEAM_NAME_TO_CODE.items():
        if key in name_lower:
            return code
    return team_name[:3].upper()


def extract_text_from_pdf(pdf_path: str) -> str:
    """Extract text content from a PDF file."""
    if HAS_PYMUPDF:
        doc = fitz.open(pdf_path)
        text = ""
        for page in doc:
            text += page.get_text()
        doc.close()
        return text
    elif HAS_PDFPLUMBER:
        with pdfplumber.open(pdf_path) as pdf:
            text = ""
            for page in pdf.pages:
                text += page.extract_text() or ""
        return text
    else:
        raise ImportError(
            "No PDF library available. Install PyMuPDF (pip install pymupdf) "
            "or pdfplumber (pip install pdfplumber)"
        )


def parse_game_info_from_url(url: str) -> dict:
    """Extract game info from the MLB Gameday URL."""
    # URL format: https://www.mlb.com/gameday/twins-vs-orioles/2010/03/26/277331/final/summary/all
    match = re.search(r'/gameday/([^/]+)/(\d{4})/(\d{2})/(\d{2})/(\d+)/', url)
    if match:
        teams_slug = match.group(1)
        year = match.group(2)
        month = match.group(3)
        day = match.group(4)
        game_pk = match.group(5)

        # Parse teams from slug (e.g., "twins-vs-orioles")
        teams_match = re.match(r'([^-]+(?:-[^-]+)*)-vs-([^/]+)', teams_slug)
        if teams_match:
            away_team = teams_match.group(1).replace('-', ' ')
            home_team = teams_match.group(2).replace('-', ' ')
        else:
            away_team = 'Unknown'
            home_team = 'Unknown'

        return {
            'away_team_name': away_team.title(),
            'home_team_name': home_team.title(),
            'date': f"{year}-{month}-{day}",
            'game_pk': int(game_pk),
        }
    return {}


def parse_linescore(text: str, away_code: str, home_code: str) -> dict:
    """Parse the linescore from PDF text."""
    # Format:
    # 1 2 3 4 5 6 7 8 9 R H E
    # MIN 0 1 0 0 3 0 0 0 0 4 9 0
    # BAL 0 0 0 0 2 0 1 0 0 3 6 2
    # Note: "x" appears when home team doesn't bat in 9th

    away_r, away_h, away_e = 0, 0, 0
    home_r, home_h, home_e = 0, 0, 0
    away_innings = []
    home_innings = []

    # Try to match team linescore lines with team code at start
    # Flexible pattern for team codes (2-3 chars), allow 'x' for innings not played
    away_pattern = rf'^{away_code}\s+([\d\sx]+)$'
    home_pattern = rf'^{home_code}\s+([\d\sx]+)$'

    def parse_linescore_values(values_str):
        """Parse linescore values, treating 'x' as 0."""
        parts = values_str.split()
        numbers = []
        for p in parts:
            if p.lower() == 'x':
                numbers.append(0)  # x means didn't bat
            else:
                try:
                    numbers.append(int(p))
                except ValueError:
                    pass
        return numbers

    lines = text.split('\n')
    for line in lines:
        line = line.strip()

        # Try away team
        away_match = re.match(away_pattern, line, re.IGNORECASE)
        if away_match:
            numbers = parse_linescore_values(away_match.group(1))
            if len(numbers) >= 12:  # 9 innings + R + H + E
                away_innings = numbers[:-3]
                away_r, away_h, away_e = numbers[-3], numbers[-2], numbers[-1]
            continue

        # Try home team
        home_match = re.match(home_pattern, line, re.IGNORECASE)
        if home_match:
            numbers = parse_linescore_values(home_match.group(1))
            if len(numbers) >= 12:  # 9 innings + R + H + E
                home_innings = numbers[:-3]
                home_r, home_h, home_e = numbers[-3], numbers[-2], numbers[-1]
            continue

    return {
        'away': {'R': away_r, 'H': away_h, 'E': away_e, 'runs_by_inning': away_innings},
        'home': {'R': home_r, 'H': home_h, 'E': home_e, 'runs_by_inning': home_innings},
    }


def parse_pitcher_decisions(text: str) -> dict:
    """Parse winning, losing, and save pitchers."""
    decisions = {}

    # W: Baker, S with record
    win_match = re.search(r'W:\s*([^0-9\n]+?)(?:\s*\n|\s+\d)', text)
    if win_match:
        decisions['W'] = win_match.group(1).strip()

    # L: Tillman with record
    loss_match = re.search(r'L:\s*([^0-9\n]+?)(?:\s*\n|\s+\d)', text)
    if loss_match:
        decisions['L'] = loss_match.group(1).strip()

    # S: Crain (save)
    save_match = re.search(r'S:\s*([^0-9\n]+?)(?:\s*\n|\s+\d)', text)
    if save_match:
        decisions['SV'] = save_match.group(1).strip()

    return decisions


def parse_play_by_play(text: str, away_code: str, home_code: str) -> tuple:
    """Parse play-by-play and substitutions from PDF text."""
    plays = []
    substitutions = []

    # Split into lines
    lines = text.split('\n')

    current_inning = 0
    current_half = ''
    current_event_type = None
    current_description_lines = []
    away_score = 0
    home_score = 0

    # Event type patterns
    event_types = [
        'Flyout', 'Groundout', 'Lineout', 'Pop Out', 'Strikeout',
        'Single', 'Double', 'Triple', 'Home Run', 'Walk',
        'Forceout', 'Grounded Into DP', 'Field Error', 'Fielders Choice',
        'Sac Fly', 'Sac Bunt', 'Hit By Pitch', 'Caught Stealing 2B',
        'Caught Stealing 3B', 'Caught Stealing Home', 'Stolen Base 2B',
        'Stolen Base 3B', 'Wild Pitch', 'Passed Ball', 'Balk',
        'Defensive Indifference', 'Intent Walk',
    ]

    substitution_types = [
        'Pitching Substitution', 'Pitching Change',
        'Defensive Sub', 'Defensive Substitution',
        'Offensive Substitution', 'Defensive Switch',
    ]

    def save_current_play():
        nonlocal current_event_type, current_description_lines
        if current_event_type and current_description_lines:
            description = ' '.join(current_description_lines).strip()

            # Check if it's a substitution
            is_sub = any(sub_type.lower() in current_event_type.lower()
                        for sub_type in substitution_types)

            if is_sub:
                # Parse substitution
                sub_data = {
                    'inning': current_inning,
                    'half': current_half,
                    'type': current_event_type,
                    'description': description,
                }
                substitutions.append(sub_data)
            else:
                # Parse play
                play_data = {
                    'inning': current_inning,
                    'half': current_half,
                    'event': current_event_type,
                    'event_type': current_event_type.lower().replace(' ', '_'),
                    'description': description,
                    'away_score': away_score,
                    'home_score': home_score,
                    'is_scoring_play': False,
                }

                # Check for scoring plays
                score_match = re.search(rf'{away_code}\s+(\d+),\s*{home_code}\s+(\d+)', description)
                if score_match:
                    new_away = int(score_match.group(1))
                    new_home = int(score_match.group(2))
                    if new_away != away_score or new_home != home_score:
                        play_data['is_scoring_play'] = True
                        play_data['away_score'] = new_away
                        play_data['home_score'] = new_home

                # Extract batter name (first name in description for most plays)
                batter_match = re.match(r'^([A-Z][a-z]+(?:\s+[A-Z][a-z\'-]+)+)', description)
                if batter_match:
                    play_data['batter'] = batter_match.group(1)

                plays.append(play_data)

        current_event_type = None
        current_description_lines = []

    i = 0
    while i < len(lines):
        line = lines[i].strip()

        # Check for inning header
        inning_match = re.match(r'^(Top|Bottom)\s+(\d+)(st|nd|rd|th)$', line)
        if inning_match:
            save_current_play()
            current_half = inning_match.group(1).lower()
            current_inning = int(inning_match.group(2))
            i += 1
            continue

        # Check for event type
        event_found = False
        for event_type in event_types + substitution_types:
            if line == event_type or line.startswith(event_type + ':'):
                save_current_play()
                current_event_type = event_type
                event_found = True
                break

        if event_found:
            i += 1
            continue

        # Check for score updates in their own line
        score_line_match = re.match(rf'^{away_code}\s+(\d+),?\s*{home_code}\s+(\d+)$', line)
        if score_line_match:
            away_score = int(score_line_match.group(1))
            home_score = int(score_line_match.group(2))
            i += 1
            continue

        # Skip header/footer lines
        if any(skip in line for skip in ['FINAL', 'Gameday', 'mlb.com', 'https://',
                                          'Key Moments', 'Scoring', 'Video', 'Strikeouts',
                                          'Lead Changes', 'Win Proba', 'Wrap', 'Summary',
                                          'Box', 'Home Runs', 'ERA', 'W:', 'L:', 'S:']):
            i += 1
            continue

        # Skip page numbers and timestamps
        if re.match(r'^\d+/\d+/\d+', line) or re.match(r'^\d+/\d+$', line):
            i += 1
            continue

        # Skip empty lines
        if not line:
            i += 1
            continue

        # Skip team abbreviations and scores at top
        if re.match(r'^[A-Z]{2,3}$', line) or re.match(r'^\d+\s*-\s*\d+$', line):
            i += 1
            continue

        # Skip innings header numbers
        if re.match(r'^[0-9\s]+$', line) and len(line) > 5:
            i += 1
            continue

        # Add to current description
        if current_event_type:
            current_description_lines.append(line)

        i += 1

    # Save final play
    save_current_play()

    return plays, substitutions


def parse_mlb_pdf(pdf_path: str, save_to_cache: bool = False, cache_dir: str = None) -> dict:
    """
    Parse an MLB Gameday PDF file.

    Args:
        pdf_path: Path to the PDF file
        save_to_cache: If True, save the parsed data to cache
        cache_dir: Directory to save cache files (default: ./cache)

    Returns:
        Game data dict compatible with other parsers
    """
    pdf_path = Path(pdf_path)
    if not pdf_path.exists():
        raise FileNotFoundError(f"PDF not found: {pdf_path}")

    # Extract text from PDF
    text = extract_text_from_pdf(str(pdf_path))

    # Find the URL in the text to extract game info
    url_match = re.search(r'https://www\.mlb\.com/gameday/[^\s]+', text)
    if url_match:
        url = url_match.group(0)
        game_info = parse_game_info_from_url(url)
    else:
        game_info = {}

    # Extract team codes
    away_code = get_team_code(game_info.get('away_team_name', ''))
    home_code = get_team_code(game_info.get('home_team_name', ''))

    # Parse linescore
    linescore = parse_linescore(text, away_code, home_code)

    # Parse pitcher decisions
    pitcher_decisions = parse_pitcher_decisions(text)

    # Parse play-by-play
    plays, substitutions = parse_play_by_play(text, away_code, home_code)

    # Build game data
    date_str = game_info.get('date', '')
    if date_str:
        try:
            date_obj = datetime.strptime(date_str, '%Y-%m-%d')
            formatted_date = date_obj.strftime('%A, %B %d, %Y')
            date_yyyymmdd = date_obj.strftime('%Y%m%d')
        except Exception:
            formatted_date = date_str
            date_yyyymmdd = date_str.replace('-', '')
    else:
        formatted_date = ''
        date_yyyymmdd = ''

    game_pk = game_info.get('game_pk', 0)
    game_id = f"M{home_code}{date_yyyymmdd}0"

    game_data = {
        'basic_info': {
            'away_team': game_info.get('away_team_name', ''),
            'home_team': game_info.get('home_team_name', ''),
            'date': formatted_date,
            'date_yyyymmdd': date_yyyymmdd,
            'start_time': '',
            'attendance': '',
            'attendance_value': 0,
            'venue': 'Ed Smith Stadium',  # Spring training default
            'venue_city': 'Sarasota',
            'venue_state': 'FL',
            'duration': '',
            'weather': '',
            'temperature_f': None,
            'away_score': str(linescore['away']['R']),
            'home_score': str(linescore['home']['R']),
            'away_score_value': linescore['away']['R'],
            'home_score_value': linescore['home']['R'],
            'doubleheader': 'N',
            'away_team_code': away_code,
            'home_team_code': home_code,
            'game_type': 'spring',
            'game_type_code': 'S',
            'source': 'pdf',
        },
        'batting': {'away': [], 'home': []},
        'pitching': {'away': [], 'home': []},
        'linescore': {
            'innings': len(linescore['away'].get('runs_by_inning', [])) or 9,
            'away': {
                'runs_by_inning': linescore['away'].get('runs_by_inning', []),
                'R': linescore['away']['R'],
                'H': linescore['away']['H'],
                'E': linescore['away']['E'],
            },
            'home': {
                'runs_by_inning': linescore['home'].get('runs_by_inning', []),
                'R': linescore['home']['R'],
                'H': linescore['home']['H'],
                'E': linescore['home']['E'],
            },
        },
        'game_id': game_id,
        'mlb_game_pk': game_pk,
        'source': 'pdf',
        'lineups': {'away': [], 'home': []},
        'substitutions': substitutions,
        'play_by_play': plays,
        'pitcher_decisions': pitcher_decisions,
        'special_events': {},
        'milestone_stats': {},
        'umpires': {},
        'doubleheader': 'N',
        'raw_plays': plays,
        'footer_summary': {},
    }

    # Save to cache if requested
    if save_to_cache:
        if cache_dir is None:
            cache_dir = Path(__file__).parent.parent.parent / 'cache'
        else:
            cache_dir = Path(cache_dir)

        cache_dir.mkdir(parents=True, exist_ok=True)

        # Generate filename
        away_name = game_info.get('away_team_name', 'Unknown').replace(' ', '_')
        home_name = game_info.get('home_team_name', 'Unknown').replace(' ', '_')
        cache_filename = f"{away_name}_vs_{home_name}_Spring_Training__{formatted_date.replace(', ', '__').replace(' ', '_')}.json"
        cache_path = cache_dir / cache_filename

        with open(cache_path, 'w') as f:
            json.dump(game_data, f, indent=2)

        print(f"Saved to cache: {cache_path}")

    return game_data


if __name__ == '__main__':
    import argparse

    parser = argparse.ArgumentParser(description='Parse MLB Gameday PDF files')
    parser.add_argument('pdf', help='Path to PDF file')
    parser.add_argument('--save', '-s', action='store_true', help='Save to cache')
    parser.add_argument('--json', '-j', action='store_true', help='Output as JSON')

    args = parser.parse_args()

    game_data = parse_mlb_pdf(args.pdf, save_to_cache=args.save)

    if args.json:
        print(json.dumps(game_data, indent=2))
    else:
        bi = game_data['basic_info']
        print(f"\n{'='*60}")
        print(f"{bi['away_team']} ({bi['away_score']}) @ {bi['home_team']} ({bi['home_score']})")
        print(f"{bi['date']}")
        print(f"Game ID: {game_data['game_id']}")
        print(f"{'='*60}")

        print(f"\nPlay-by-play: {len(game_data['play_by_play'])} plays")
        print(f"Substitutions: {len(game_data['substitutions'])}")

        # Show sample plays
        print("\nSample plays:")
        for play in game_data['play_by_play'][:5]:
            print(f"  {play['inning']} {play['half']}: {play['event']} - {play['description'][:50]}...")

        # Show scoring plays
        scoring = [p for p in game_data['play_by_play'] if p.get('is_scoring_play')]
        if scoring:
            print(f"\nScoring plays ({len(scoring)}):")
            for play in scoring:
                print(f"  {play['inning']} {play['half']}: {play['description'][:60]}...")
