import re
from datetime import datetime
from bs4 import BeautifulSoup, Comment

from ..utils.constants import RETROSHEET_CODES, LABEL_MAP
from ..utils.helpers import standardize_team_code, normalize_name, normalize_umpire_name
from ..engines.milestone_engine import MilestoneEngine
from ..engines.special_events_engine import SpecialEventsEngine
from .stats_parser import extract_batting_stats, extract_pitching_stats, assign_pitcher_decisions
from .play_by_play_parser import extract_play_by_play, extract_play_features

def parse_baseball_reference_boxscore(html_content):
    """Parse a Baseball-Reference.com box score HTML file into game_data dict."""
    soup = BeautifulSoup(html_content, 'html.parser')
    umpires = extract_umpires(soup)
    game_data = {
        'basic_info': {},
        'batting': {'away': [], 'home': []},
        'pitching': {'away': [], 'home': []},
        'linescore': {},
        'lineups': {'away': [], 'home': []},
        'substitutions': [],
        'play_by_play': [],
        'pitcher_decisions': {},
        'special_events': {
            'walkoff': None, 'immaculate_innings': [], 'leadoff_hrs': [],
            'grand_slams': [], 'pinch_hit_hrs': [], 'no_hitters': [], 'complete_games': []
        },
        'milestone_stats': {
            'multi_hr_games': [], 'cycles': [], 'four_hit_games': [],
            'five_rbi_games': [], 'ten_k_games': [], 'shutouts': [],
            'complete_games': [], 'perfect_games': []
        },
        'umpires': umpires,
    }
    

    # Extract meta text safely
    scorebox_meta = soup.select_one(".scorebox_meta")
    meta_text = scorebox_meta.get_text(separator=" ", strip=True).lower() if scorebox_meta else ""
   
    if "first game of doubleheader" in meta_text:
        game_data["doubleheader"] = "1"
    elif "second game of doubleheader" in meta_text:
        game_data["doubleheader"] = "2"
    elif "doubleheader" in meta_text:
        game_data["doubleheader"] = "1"
    else:
        game_data["doubleheader"] = "0"

    game_data['basic_info'] = extract_basic_info(soup)    
    game_data["basic_info"]["doubleheader"] = game_data["doubleheader"]
    away = game_data['basic_info'].get('away_team', '')
    home = game_data['basic_info'].get('home_team', '')
    game_data['basic_info']['away_team_code'] = standardize_team_code(away)
    game_data['basic_info']['home_team_code'] = standardize_team_code(home)

    if away:
        game_data['batting']['away'] = extract_batting_stats(soup, away, is_home=False)
        game_data['pitching']['away'] = extract_pitching_stats(soup, away, is_home=False)
    if home:
        game_data['batting']['home'] = extract_batting_stats(soup, home, is_home=True)
        game_data['pitching']['home'] = extract_pitching_stats(soup, home, is_home=True)

    # Starting lineups (batting order + starting defensive positions)
    # BBRef typically hides this in an HTML comment block under a div with id="div_lineups".
    try:
        game_data['lineups'] = extract_lineups(soup, away_team=away, home_team=home)
        _attach_lineup_metadata(game_data)
    except Exception:
        # Lineups are a "nice to have"; avoid failing the entire parse.
        pass

    game_data['linescore'] = extract_linescore(soup)
    plate_appearances, raw_plays, substitutions = extract_play_by_play(soup, away, home)
    game_data["play_by_play"] = plate_appearances
    game_data["raw_plays"] = raw_plays
    game_data["substitutions"] = substitutions
    for play in game_data['play_by_play']:
        play.update(extract_play_features(play.get('description', '')))
    
    # Fix inside-the-park HR RBI counting
    for play in game_data['play_by_play']:
        if play.get('inside_the_park_hr'):
            desc = play.get('description', '')
            # Count "Name Scores" patterns (semicolon-separated)
            additional_runners = len([p for p in desc.split(';') if ' Scores' in p])
            
            # Batter (1) + additional runners = total RBIs
            correct_rbi = 1 + additional_runners
            
            if correct_rbi != play.get('rbi', 0):
                play['rbi'] = correct_rbi

    assign_pitcher_decisions(game_data)
    game_data['game_id'] = generate_retrosheet_game_id(game_data)
    game_data['footer_summary'] = extract_footer_sections(soup, home, away)
    SpecialEventsEngine(game_data, soup).detect()
    MilestoneEngine(game_data).process()

    return game_data

def extract_basic_info(soup):
    """Extract basic game information like teams, date, location, etc."""
    info = {}

    # Get teams from title using a more flexible pattern
    title_tag = soup.find('title')
    title = title_tag.text if title_tag else ''
    teams_match = re.search(r'(.+?) vs (.+?)(?=[:|]| Box Score)', title)
    if teams_match:
        info['away_team'] = teams_match.group(1).strip().split(',')[-1].strip()
        info['home_team'] = teams_match.group(2).strip()
    else:
        print("⚠️ Could not extract teams from title:", title)

    scorebox_meta = soup.select_one('.scorebox_meta')
    if scorebox_meta:
        first_div = scorebox_meta.find('div')
        date_text = first_div.text if first_div else ''
        info['date'] = date_text

        date_match = re.search(r'([A-Za-z]+)\s+(\d+),\s+(\d{4})', date_text)
        if date_match:
            month_name = date_match.group(1)
            day = date_match.group(2)
            year = date_match.group(3)

            month_dict = {
                'January': '01', 'February': '02', 'March': '03', 'April': '04',
                'May': '05', 'June': '06', 'July': '07', 'August': '08',
                'September': '09', 'October': '10', 'November': '11', 'December': '12'
            }

            if month_name in month_dict:
                month_num = month_dict[month_name]
                day_formatted = day.zfill(2)
                info['date_yyyymmdd'] = f"{year}{month_num}{day_formatted}"

        for div in scorebox_meta.find_all('div'):
            if 'Attendance' in div.text:
                attendance_text = div.text.replace('Attendance', '').strip(':').strip()
                info['attendance'] = attendance_text
                attendance_value = re.sub(r'[^\d]', '', attendance_text)
                if attendance_value:
                    info['attendance_value'] = int(attendance_value)
            if 'Venue' in div.text:
                match = re.search(r"Venue\s*:\s*(.+)", div.text)
                if match:
                    info['venue'] = match.group(1).strip()
            if 'Game Duration' in div.text or 'Time of Game' in div.text:
                duration_text = div.text
                for prefix in ['Game Duration', 'Time of Game']:
                    duration_text = duration_text.replace(prefix, '').strip(':').strip()
                info['duration'] = duration_text
            if 'Start Time' in div.text:
                info['start_time'] = div.text.replace('Start Time', '').strip(':').strip()
            
            # Basic weather check (without temperature)
            if 'Weather' in div.text:
                weather_text = div.get_text(" ", strip=True)
                info['weather'] = weather_text.replace('Weather', '').strip(':').strip()

    # *** NEW: Also check commented sections for detailed weather ***
    comments = soup.find_all(string=lambda text: isinstance(text, Comment))
    for comment in comments:
        try:
            comment_soup = BeautifulSoup(comment, "html.parser")
            
            # Look for weather information in commented sections
            for div in comment_soup.find_all("div"):
                div_text = div.get_text(" ", strip=True)
                
                if 'Start Time Weather:' in div_text:
                    weather_text = div_text.replace('Start Time Weather:', '').strip()
                    info['weather'] = weather_text
                    
                    # Extract temperature with better regex
                    temp_patterns = [
                        r'(\d+)\s*°\s*F\b',           # "60° F"
                        r'(\d+)\s*degrees?\s*F\b',    # "60 degrees F"
                        r'(\d+)\s*°F\b',              # "60°F"
                        r'(\d+)\s*F\b',               # "60F"
                    ]
                    
                    for pattern in temp_patterns:
                        m = re.search(pattern, weather_text, flags=re.IGNORECASE)
                        if m:
                            try:
                                temp_val = int(m.group(1))
                                info['temperature_f'] = temp_val
                                break
                            except Exception as e:
                                print(f"❌ Error converting temperature: {e}")
                    
                    if 'temperature_f' not in info:
                        print(f"❌ No temperature found in weather: '{weather_text}'")
                        
        except Exception as e:
            # Skip malformed comments
            continue

    # Extract scores
    scorebox = soup.select_one('.scorebox')
    if scorebox:
        score_divs = scorebox.select('.scores .score')
        if len(score_divs) >= 2:
            info['away_score'] = score_divs[0].text
            info['home_score'] = score_divs[1].text
            try:
                info['away_score_value'] = int(info['away_score'])
                info['home_score_value'] = int(info['home_score'])
            except (ValueError, TypeError):
                pass

    return info


def extract_lineups(soup, away_team: str, home_team: str):
    """Extract starting lineups (batting order + positions) from BBRef.

    BBRef commonly includes a hidden comment block containing:
        <div id="div_lineups"> ... <table><caption>Team</caption> ...

    Returns:
        {"away": [...], "home": [...]} where each entry is:
            {"slot": int, "name": str, "player_id": str, "pos": str}
    """
    out = {"away": [], "home": []}

    away_norm = normalize_name(away_team)
    home_norm = normalize_name(home_team)

    # Search comment blocks for the lineups container.
    for comment in soup.find_all(string=lambda text: isinstance(text, Comment)):
        # BBRef sometimes embeds HTML fragments with escaped quotes inside comments.
        # Example: id=\"div_lineups\" instead of id="div_lineups".
        cleaned = str(comment)

        # Common escapes in BBRef comment blocks
        if '\\t' in cleaned:
            cleaned = cleaned.replace('\\t', '\t')
        if '\\n' in cleaned:
            cleaned = cleaned.replace('\\n', '\n')
        if '\\"' in cleaned:
            cleaned = cleaned.replace('\\"', '"')

        csoup = BeautifulSoup(cleaned, "html.parser")
        container = csoup.find(id="div_lineups")
        if not container:
            continue

        for table in container.find_all("table"):
            caption = table.find("caption")
            team_label = caption.get_text(" ", strip=True) if caption else ""
            team_norm = normalize_name(team_label)

            def _matches(caption_norm: str, team_norm: str) -> bool:
                if not caption_norm or not team_norm:
                    return False
                return caption_norm == team_norm or caption_norm in team_norm or team_norm in caption_norm

            if _matches(team_norm, away_norm):
                side = "away"
            elif _matches(team_norm, home_norm):
                side = "home"
            else:
                # If we can't match caption -> team, skip to avoid mis-labeling.
                continue

            rows = []
            for tr in table.find_all("tr"):
                tds = tr.find_all("td")
                if len(tds) < 3:
                    continue

                slot_text = tds[0].get_text(strip=True)
                slot = int(slot_text) if slot_text.isdigit() else None

                player_td = tds[1]
                link = player_td.find('a', href=lambda h: h and '/players/' in h)
                name = player_td.get_text(" ", strip=True)
                player_id = None
                if link and link.get('href'):
                    player_id = link['href'].split('/')[-1].replace('.shtml', '')

                pos = tds[2].get_text(strip=True)

                if slot is None or not name:
                    continue

                rows.append({
                    "slot": slot,
                    "name": name,
                    "player_id": player_id or "UNKNOWN",
                    "pos": pos,
                })

            if rows:
                out[side] = rows

        # We found the block; don't keep scanning.
        break

    return out


def _attach_lineup_metadata(game_data: dict) -> None:
    """Attach lineup_slot / starter_pos onto batting rows when possible."""
    lineups = (game_data or {}).get('lineups') or {}
    batting = (game_data or {}).get('batting') or {}

    for side in ("away", "home"):
        lineup_rows = lineups.get(side) or []
        if not lineup_rows:
            continue

        by_player_id = {r.get('player_id'): r for r in lineup_rows if r.get('player_id')}
        by_name = {normalize_name(r.get('name', '')): r for r in lineup_rows if r.get('name')}

        for b in batting.get(side, []) or []:
            pid = b.get('player_id')
            row = by_player_id.get(pid) if pid else None
            if not row:
                row = by_name.get(normalize_name(b.get('name', '')))

            if not row:
                continue

            b['lineup_slot'] = row.get('slot')
            b['starter_pos'] = row.get('pos')
            b['is_starter'] = True


def extract_linescore(soup):
    """Extract the linescore (inning-by-inning scoring)."""
    linescore_table = soup.select_one('table.linescore')
    if not linescore_table:
        return {}
    
    linescore_data = {
        'away': {'innings': [], 'R': 0, 'H': 0, 'E': 0},
        'home': {'innings': [], 'R': 0, 'H': 0, 'E': 0}
    }
    
    headers = linescore_table.select('thead th')
    inning_indices = []
    for i, header in enumerate(headers):
        if header.text.isdigit() or header.text in ['R', 'H', 'E']:
            inning_indices.append(i)
    
    rows = linescore_table.select('tbody tr')
    if len(rows) >= 2:
        for row_idx, team in enumerate(['away', 'home']):
            cells = rows[row_idx].select('td')
            for i, idx in enumerate(inning_indices):
                if idx < len(cells):
                    value = cells[idx].text.strip()
                    if i < len(inning_indices) - 3:
                        linescore_data[team]['innings'].append(value)
                    elif headers[idx].text == 'R':
                        linescore_data[team]['R'] = int(value)
                    elif headers[idx].text == 'H':
                        linescore_data[team]['H'] = int(value)
                    elif headers[idx].text == 'E':
                        linescore_data[team]['E'] = int(value)
    
    return linescore_data

def extract_footer_sections(soup, home_team, away_team):
    """Extract HR, RBI, TB, 2B, etc. from hidden HTML comment blocks under batting tables."""
    footers = {}
    for team_name, side in [(home_team, "home"), (away_team, "away")]:
        team_id = team_name.replace(" ", "").replace(".", "").replace("'", "")
        container_id = f"all_{team_id}batting"
        container = soup.find("div", id=container_id)
        if not container:
            continue

        comments = container.find_all(string=lambda text: isinstance(text, Comment))
        for comment in comments:
            comment_soup = BeautifulSoup(comment, "html.parser")
            footer_div = comment_soup.find("div", id=f"tfooter_{team_id}batting")
            if not footer_div:
                continue

            footer_data = {}
            for stat_div in footer_div.find_all("div"):
                if stat_div.find("div"):
                    continue
                text = stat_div.get_text(separator=" ", strip=True)
                if ':' not in text:
                    continue
                label, value = text.split(":", 1)
                raw = label.strip()
                key = LABEL_MAP.get(raw, raw)
                footer_data[key] = value.strip()

            footers[side] = footer_data
            break
    return footers

def extract_umpires(soup):
    """Extract umpire info from comment blocks like those used by Baseball-Reference."""
    pattern = r"([HP123LRFB]+)\s*-\s*([\w\s\.\']+?)(?=,|$)"

    for comment in soup.find_all(string=lambda text: isinstance(text, Comment)):
        if "Umpires:" in comment:
            comment_soup = BeautifulSoup(comment, "html.parser")
            for div in comment_soup.find_all("div"):
                if "Umpires:" in div.get_text():
                    text = div.get_text(" ", strip=True)
                    try:
                        _, umpire_str = text.split("Umpires:", 1)
                    except ValueError:
                        continue
                    matches = re.findall(pattern, umpire_str)
                    if matches:
                        return {pos: normalize_umpire_name(name) for pos, name in matches}
    return {}


def generate_retrosheet_game_id(game_data):
    date_str = game_data.get("basic_info", {}).get("date_yyyymmdd")
    home_name = game_data.get("home_team") or game_data.get("basic_info", {}).get("home_team")
    dh = game_data.get("doubleheader") or "0"

    # Special handling for post-2025 Athletics name change
    try:
        game_year = int(date_str[:4])
    except (TypeError, ValueError):
        game_year = 0

    if home_name == "Athletics":
        home_code = "ATH" if game_year >= 2025 else "OAK"
    else:
        home_code = RETROSHEET_CODES.get(home_name, home_name[:3].upper())

    return f"{home_code}{date_str}{dh}" if home_code and date_str else None

