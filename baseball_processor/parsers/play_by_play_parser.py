import re
from bs4 import BeautifulSoup, Comment
from ..utils.log import debug

def extract_play_by_play(soup, away_team, home_team):
    """Parse the play-by-play table.

    Returns:
        (plate_appearances, raw_plays, substitutions)

    substitutions is a list of structured in-game substitution events derived from
    BBRef rows like `<tr class="ingame_substitution">...`.
    """
    plate_appearances = []
    raw_plays = []
    substitutions = []

    def apply_sub(name: str) -> str:
        # Currently unused: BBRef already shows the active player names after subs.
        return name

    def _parse_substitution_text(text: str) -> dict:
        """Best-effort parse of BBRef substitution strings."""
        t = (text or '').strip()
        out = {"raw": t, "type": "substitution"}

        # Strip trailing batting order info: "batting 9th", "batting 1st", etc.
        clean = re.sub(r'\s+batting\s+\d+\w*\s*$', '', t, flags=re.IGNORECASE).strip()

        # Position move: "A moves from X to Y"
        m = re.match(r'^(.+?)\s+moves from\s+(.+?)\s+to\s+(.+?)\s*$', clean, flags=re.IGNORECASE)
        if m:
            out.update({"type": "position_change", "player_in": m.group(1).strip(), "player_out": "",
                        "pos": m.group(3).strip(), "pos_from": m.group(2).strip()})
            return out

        # Pitching change: "A replaces B pitching" or "A replaces B (POS) pitching and ..."
        m = re.match(r'^(.+?)\s+replaces\s+(.+?)\s+pitching(?:\s+and\s+.*)?$', clean, flags=re.IGNORECASE)
        if m:
            out.update({"type": "pitching_change", "player_in": m.group(1).strip(), "player_out": m.group(2).strip()})
            return out

        # Defensive sub: "A replaces B (POS) playing CF" or "A replaces B at SS"
        m = re.match(r'^(.+?)\s+replaces\s+(.+?)\s+(?:at|playing)\s+(.+?)$', clean, flags=re.IGNORECASE)
        if m:
            out.update({"type": "defensive_sub", "player_in": m.group(1).strip(),
                        "player_out": m.group(2).strip(), "pos": m.group(3).strip()})
            return out

        # Generic replaces: "A replaces B"
        m = re.match(r'^(.+?)\s+replaces\s+(.+?)$', clean, flags=re.IGNORECASE)
        if m:
            out.update({"type": "substitution", "player_in": m.group(1).strip(), "player_out": m.group(2).strip()})
            return out

        # Pinch hit: "A pinch hits for B (POS)"
        m = re.match(r'^(.+?)\s+pinch hits for\s+(.+?)$', clean, flags=re.IGNORECASE)
        if m:
            out.update({"type": "pinch_hit", "player_in": m.group(1).strip(), "player_out": m.group(2).strip()})
            return out

        # Pinch run: "A pinch runs for B"
        m = re.match(r'^(.+?)\s+pinch runs for\s+(.+?)$', clean, flags=re.IGNORECASE)
        if m:
            out.update({"type": "pinch_run", "player_in": m.group(1).strip(), "player_out": m.group(2).strip()})
            return out

        return out

    pbp_div = soup.find('div', id='all_play_by_play') or soup.find('div', id='play_by_play')
    if not pbp_div:
        return [], [], []

    pbp_table = None
    for c in pbp_div.find_all(string=lambda t: isinstance(t, Comment)):
        maybe = BeautifulSoup(c, 'html.parser').find('table', id='play_by_play')
        if maybe:
            pbp_table = maybe
            break
    else:
        pbp_table = pbp_div.find('table', id='play_by_play')
        if not pbp_table:
            return [], [], []

    headers = [th.get_text(strip=True) for th in pbp_table.find('thead').find_all('th')]
    idx = lambda name, default=None: headers.index(name) if name in headers else default
    inning_idx = idx('Inning', 0)
    score_idx = idx('Score')
    outs_idx = idx('Out')
    runners_idx = idx('RoB')
    batter_idx = idx('Batter')
    pitcher_idx = idx('Pitcher')
    pitch_count_idx = idx('Pit(cnt)')
    desc_idx = next((i for i, h in enumerate(headers)
                     if h in ('Play Description', 'Play', 'Detail')), None)

    current_pa = None
    current_inning = 0
    current_half = 'top'

    for row in pbp_table.find('tbody').find_all('tr'):
        # In-game substitutions appear as their own rows in the PBP table.
        # Example: <tr class="ingame_substitution"> ... "X replaces Y pitching" ...
        if 'ingame_substitution' in (row.get('class') or []):
            cells = row.find_all(['th', 'td'])
            sub_texts = []
            for cell in reversed(cells):
                # Check for multiple <div> children (each is a separate sub)
                divs = cell.find_all('div')
                if divs:
                    sub_texts = [d.get_text(' ', strip=True) for d in divs if d.get_text(strip=True)]
                else:
                    t = cell.get_text(' ', strip=True)
                    if t:
                        sub_texts = [t]
                if sub_texts:
                    break

            for sub_text in sub_texts:
                if not sub_text:
                    continue
                sub = _parse_substitution_text(sub_text)
                sub.update({
                    "inning": current_inning,
                    "half": current_half,
                    "batting_team": away_team if current_half == 'top' else home_team,
                    "pitching_team": home_team if current_half == 'top' else away_team,
                })
                substitutions.append(sub)
            continue
        cells = row.find_all(['th', 'td'])
        if (not cells or desc_idx is None or inning_idx is None
                or inning_idx >= len(cells) or desc_idx >= len(cells)):
            continue

        raw_inn = cells[inning_idx].get_text(strip=True).lower()
        half = 'top' if raw_inn.startswith(('t', 'top')) else 'bottom'
        inning = int(re.search(r'\d+', raw_inn).group()) if re.search(r'\d+', raw_inn) else 0

        current_inning = inning
        current_half = half

        play = {
            'inning': inning,
            'half': half,
            'batting_team': away_team if half == 'top' else home_team,
            'pitching_team': home_team if half == 'top' else away_team,
            'description': cells[desc_idx].get_text(' ', strip=True)
        }

        # Extract player information
        if batter_idx is not None and batter_idx < len(cells):
            td = cells[batter_idx]
            name = td.get_text(' ', strip=True)
            if name:
                play['batter'] = apply_sub(name)
                link = td.find('a', href=lambda h: h and '/players/' in h)
                if link:
                    play['batter_id'] = link['href'].split('/')[-1].replace('.shtml', '')

        if pitcher_idx is not None and pitcher_idx < len(cells):
            td = cells[pitcher_idx]
            name = td.get_text(' ', strip=True)
            if name:
                play['pitcher'] = apply_sub(name)
                link = td.find('a', href=lambda h: h and '/players/' in h)
                if link:
                    play['pitcher_id'] = link['href'].split('/')[-1].replace('.shtml', '')

        if score_idx is not None and score_idx < len(cells):
            play['score'] = cells[score_idx].get_text(strip=True)
        if outs_idx is not None and outs_idx < len(cells):
            o = cells[outs_idx].get_text(strip=True)
            play['outs'] = int(o) if o.isdigit() else None
        if runners_idx is not None and runners_idx < len(cells):
            play['runners_on_base'] = cells[runners_idx].get_text(strip=True)

        if pitch_count_idx is not None and pitch_count_idx < len(cells):
            pitch_text = cells[pitch_count_idx].get_text(strip=True)
            match = re.match(r'(\d+),', pitch_text)
            if match:
                play['pitch_count'] = int(match.group(1))

        raw_plays.append(play)

        key = (play.get('batter'), inning, half)
        if current_pa and (key != (current_pa['batter'], current_pa['inning'], current_pa['half'])):
            plate_appearances.append(current_pa)
            current_pa = None

        if not current_pa:
            current_pa = {
                'batter': play.get('batter'),
                'pitcher': play.get('pitcher'),
                'inning': inning,
                'half': half,
                'batting_team': play['batting_team'],
                'pitching_team': play['pitching_team'],
                'pitch_count': 0,
                'description': '',
                'outs': None
            }

        # Only add pitch count if this play involves the batter
        # (not baserunning events like steals which happen during the at-bat)
        description = play.get('description', '').lower()
        is_baserunning_only = any(keyword in description for keyword in [
            'steals', 'stolen base', 'caught stealing', 'pickoff', 'picked off',
            'balk', 'wild pitch', 'passed ball'
        ]) and not any(keyword in description for keyword in [
            'singled', 'doubled', 'tripled', 'homered', 'walked', 'struck out',
            'grounded', 'flied', 'lined', 'popped', 'fouled'
        ])
        
        if not is_baserunning_only:
            current_pa['pitch_count'] += play.get('pitch_count', 0)
        
        current_pa['description'] = play.get('description', '')
        current_pa['pitcher'] = play.get('pitcher')
        current_pa['outs'] = play.get('outs')

    if current_pa:
        plate_appearances.append(current_pa)

    return plate_appearances, raw_plays, substitutions


def extract_play_features(play_description):
    """Extract features from a play description for better milestone/event tracking."""
    features = {
        'hit': False, 'single': False, 'double': False, 'triple': False,
        'home_run': False, 'grand_slam': False, 'strikeout': False, 'walk': False,
        'hit_by_pitch': False, 'sacrifice': False, 'error': False,
        'fielders_choice': False, 'double_play': False, 'run_scored': False, 'rbi': 0
    }

    desc = play_description.lower()

    # Handle singles, doubles, triples first
    if re.search(r'(?<!\w)(singled|single)(?!\w)', desc):
        features['hit'] = True
        features['single'] = True
    # Guard against "double play" / "triple play" — both phrases contain a
    # standalone "double"/"triple" word that the boundary regex would
    # otherwise treat as a hit. Tested cases like "Ground Ball Double Play"
    # used to be tagged as a double, inflating leaderboard totals.
    if re.search(r'(?<!\w)(doubled|double)(?!\w)', desc) and 'double play' not in desc:
        features['hit'] = True
        features['double'] = True
    if re.search(r'(?<!\w)(tripled|triple)(?!\w)', desc) and 'triple play' not in desc:
        features['hit'] = True
        features['triple'] = True
    
    # Handle home runs
    if re.search(r'(?<!\w)(homered|home run)(?!\w)', desc):
        features['hit'] = True
        features['home_run'] = True
        features['run_scored'] = True

        if re.search(r'\binside[- ]the[- ]park(?:[- ](home run|hr))?\b', desc):
            features['inside_the_park_hr'] = True

        if 'grand slam' in desc:
            features['grand_slam'] = True
            features['rbi'] = 4
        else:
            # Start with 1 RBI (the batter scores on their own home run)
            features['rbi'] = 1
            
            # Look for explicit run counts first
            run_patterns = [
                (r'(\d+)[- ]run', lambda m: int(m.group(1))),  # "3-run home run"
                (r'two[- ]run', lambda m: 2),
                (r'three[- ]run', lambda m: 3),
                (r'four[- ]run', lambda m: 4),
                (r'solo', lambda m: 1),
            ]
            
            explicit_rbi = None
            for pattern, extractor in run_patterns:
                match = re.search(pattern, desc)
                if match:
                    explicit_rbi = extractor(match)
                    features['rbi'] = explicit_rbi
                    break
            
            # If no explicit count, count who scored
            if explicit_rbi is None:
                # Count semicolon-separated "Name Scores" entries
                # This handles "C. Schmitt Scores; B. Wisely Scores"
                scores_count = 0
                
                # Split by semicolon to handle each scoring event
                parts = play_description.split(';')
                for part in parts:
                    # Look for "Name Scores" pattern (case-sensitive for "Scores")
                    if re.search(r'[A-Z][\w\.\-\']+(?: [A-Z][\w\.\-\']+)*\s+Scores\b', part):
                        scores_count += 1
                        if features.get('inside_the_park_hr'):
                            debug(f"Found runner scoring: {part.strip()}")
                
                # Also check for lowercase "scored"
                scored_pattern = r'([A-Z][\w\.\-\']+(?: [A-Z][\w\.\-\']+)*)\s+scored\b'
                scored_matches = re.findall(scored_pattern, play_description)
                scores_count += len(scored_matches)
                
                # Add the additional runners to the batter's RBI
                features['rbi'] += scores_count
                
                if features.get('inside_the_park_hr'):
                    debug(f"Batter scores: 1 RBI")
                    debug(f"Additional runners: {scores_count}")
                    debug(f"Total RBIs: {features['rbi']}")
                
                # Fallback patterns
                if features['rbi'] == 1:  # Only if we haven't found other runners
                    if '3 on' in desc or 'bases loaded' in desc:
                        features['rbi'] = 4
                    elif '2 on' in desc:
                        features['rbi'] = 3
                    elif '1 on' in desc or 'runner on' in desc:
                        features['rbi'] = 2

    # Handle walks, strikeouts, etc.
    elif 'walked' in desc or 'walk' in desc:
        features['walk'] = True
    elif 'struck out' in desc or 'strikeout' in desc:
        features['strikeout'] = True
    elif 'hit by pitch' in desc or 'hbp' in desc:
        features['hit_by_pitch'] = True

    if 'sacrifice' in desc or 'sac bunt' in desc or 'sac fly' in desc:
        features['sacrifice'] = True
    if 'error' in desc:
        features['error'] = True
    if 'fielder\'s choice' in desc or 'fielders choice' in desc:
        features['fielders_choice'] = True
    if 'double play' in desc:
        features['double_play'] = True

    # For non-home run plays, check for RBIs and runs scored
    if not features['home_run']:
        if 'scores' in desc or 'scored' in desc:
            features['run_scored'] = True
            rbi_match = re.search(r'(\d+)\s*rbi', desc)
            if rbi_match:
                features['rbi'] = int(rbi_match.group(1))
            else:
                features['rbi'] = len(re.findall(r'\b(?:scores|scored)\b', desc))

    return features
