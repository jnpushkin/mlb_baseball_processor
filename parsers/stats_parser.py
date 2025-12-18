import re
from bs4 import BeautifulSoup, Comment
from ..utils.constants import LABEL_MAP
from ..utils.log import warn

def get_team_defensive_innings(game_data, team_side):
    """Return the number of innings the team pitched based on linescore and opponent's innings played."""
    linescore = game_data.get("linescore", {})

    if team_side == "home":
        opponent = "away"
    else:
        opponent = "home"

    opponent_innings = linescore.get(opponent, {}).get("innings", [])

    return len(opponent_innings)
    
def extract_batting_stats(soup, team_name, is_home=False):
    """Extract full batting statistics for the specified team."""
    batting_table = find_team_table(soup, team_name, "batting")

    if not batting_table:
        warn(f"Could not find batting table for {team_name}")
        return []

    players_stats = []
    thead = batting_table.find('thead')
    tbody = batting_table.find('tbody')

    if not tbody or not thead:
        return []

    # Get actual stat column names from header
    header_cells = thead.find_all("tr")[-1].find_all("th")
    header_names = [cell.get_text(strip=True) for cell in header_cells]

    # Find index of "Pos" column (based on text or data-stat)
    pos_index = None
    for i, cell in enumerate(header_cells):
        if cell.get("data-stat") == "pos" or cell.get_text(strip=True) == "Pos":
            pos_index = i
            break

    for row in tbody.find_all('tr'):
        if 'spacer' in row.get('class', []):
            continue

        player_data = {}
        cells = row.find_all(["th", "td"])

        if len(cells) < 2:
            continue

        player_cell = cells[0]
        player_link = player_cell.find('a')
        if player_link:
            player_data['name'] = player_link.text
            player_data['player_id'] = player_link['href'].split('/')[-1].replace('.shtml', '')
        else:
            player_data['name'] = player_cell.get_text(strip=True)
            player_data['player_id'] = "UNKNOWN"

        # Extract position from the player name cell
        position_text = player_cell.get_text(strip=True).replace(player_data['name'], '').strip()
        if position_text:
            player_data['position'] = position_text
        else:
            player_data['position'] = ""

        # Fill remaining stats
        for idx, header in enumerate(header_names[1:], start=1):  # skip player cell
            if idx < len(cells):
                text = cells[idx].get_text(strip=True)
                if text == "":
                    player_data[header] = 0
                else:
                    try:
                        player_data[header] = int(text)
                    except ValueError:
                        try:
                            player_data[header] = float(text)
                        except ValueError:
                            player_data[header] = text  # fallback as string

        players_stats.append(player_data)

    return players_stats

def extract_pitching_stats(soup, team_name, is_home=False):
    """Extract pitching statistics for the specified team."""
    pitching_table = find_team_table(soup, team_name, "pitching")
    
    if not pitching_table:
        warn(f"Could not find pitching table for {team_name}")
        return []
    
    pitchers_stats = []
    tbody = pitching_table.find('tbody')
    
    if not tbody:
        return []
        
    for row in tbody.find_all('tr'):
        pitcher_data = {}
        cells = row.find_all(['th', 'td'])
        
        if len(cells) < 5:
            continue
            
        pitcher_cell = cells[0]
        pitcher_link = pitcher_cell.find('a')
        if pitcher_link:
            pitcher_data['name'] = pitcher_link.text
            pitcher_data['player_id'] = pitcher_link['href'].split('/')[-1].replace('.shtml', '')
            
            txt = pitcher_cell.get_text(" ", strip=True)
            dec_match = re.search(r',\s*([A-Za-z]{1,2})\s*\(', txt)
            if not dec_match:
                dec_match = re.search(r'\(\s*([A-Za-z]{1,2})\s*,', txt)

            if dec_match:
                code = dec_match.group(1).upper()
                if code.startswith('S'):
                    code = 'S'

                pitcher_data['decision'] = code
                pitcher_data['win'] = code == 'W'
                pitcher_data['loss'] = code == 'L'
                pitcher_data['save'] = code == 'S'
            
            stat_columns = [
                'IP', 'H', 'R', 'ER', 'BB', 'SO', 'HR',
                'ERA', 'BF', 'Pit', 'Str',
                'Ctct', 'StS', 'StL',
                'GB', 'FB', 'LD', 'Unk',
                'GSc', 'IR', 'IS',
                'WPA', 'aLI', 'cWPA', 'acLI', 'RE24'
            ]
            for i, column in enumerate(stat_columns, 1):
                if i < len(cells):
                    value = cells[i].text.strip()
                    if column == 'IP':
                        pitcher_data[column] = value
                    elif value.isdigit() or value == "":
                        pitcher_data[column] = int(value) if value else 0
                    else:
                        pitcher_data[column] = value
            
            pitchers_stats.append(pitcher_data)
    
    return pitchers_stats

def get_player_rbi_from_box(game, player_id=None, player_name=None):
    """Get a player's RBI total from the box score."""
    try:
        for side in ("home", "away"):
            for player in game.get("batting", {}).get(side, []):
                # Match by player_id first (more reliable)
                if player_id and player.get("player_id") == player_id:
                    return player.get("RBI", 0)
                # Fallback to name matching
                if player_name and player.get("name") == player_name:
                    return player.get("RBI", 0)
    except (KeyError, TypeError, AttributeError):
        # Game data structure is invalid or missing expected fields
        pass
    return None

def find_team_table(soup, team_name, stat_type):
    """Find the correct table for a team by trying different possible ID formats."""
    team_id = team_name.replace(' ', '').replace('.', '').replace("'", '')
    possible_ids = [f"{team_id}{stat_type}"]
    
    if ' ' in team_name:
        parts = team_name.split()
        camel_case = ''.join([p.capitalize() for p in parts])
        possible_ids.append(f"{camel_case}{stat_type}")
        if len(parts) >= 2:
            possible_ids.append(f"{parts[-1]}{stat_type}")
    
    comments = soup.find_all(string=lambda text: isinstance(text, Comment))
    
    for comment in comments:
        comment_soup = BeautifulSoup(comment, 'html.parser')
        for pid in possible_ids:
            table = comment_soup.find('table', {'id': pid})
            if table:
                return table
        
        tables = comment_soup.find_all('table')
        for table in tables:
            if table.has_attr('data-team') and team_name.lower() in table['data-team'].lower():
                return table
            
            parent_div = table.parent
            if parent_div and parent_div.name == 'div' and team_name.lower() in parent_div.text.lower():
                if stat_type in parent_div.text.lower() or stat_type in table.get('id', '').lower():
                    return table
    
    return None

def assign_pitcher_decisions(game_data):
    """Assign win/loss/save decisions using parsed pitching data and score context."""
    away_score = game_data["basic_info"].get("away_score_value")
    home_score = game_data["basic_info"].get("home_score_value")
    away_team = game_data["basic_info"].get("away_team")
    home_team = game_data["basic_info"].get("home_team")

    if None in (away_score, home_score, away_team, home_team):
        return

    pitching = game_data.get("pitching", {})
    win, win_id, lose, lose_id, sv, sv_id = None, None, None, None, None, None

    for side, staff in pitching.items():
        for p in staff:
            if p.get('win') and not win:
                win, win_id = p['name'], p.get('player_id')
            if p.get('loss') and not lose:
                lose, lose_id = p['name'], p.get('player_id')
            if p.get('save') and not sv:
                sv, sv_id = p['name'], p.get('player_id')

    game_data["pitcher_decisions"] = {
        "winning_pitcher": win,
        "winning_pitcher_id": win_id,
        "losing_pitcher": lose,
        "losing_pitcher_id": lose_id,
        "save_pitcher": sv,
        "save_pitcher_id": sv_id
    }
