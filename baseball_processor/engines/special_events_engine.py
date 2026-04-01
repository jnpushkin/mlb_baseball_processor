import re
import logging
import unicodedata
from ..utils.stat_utils import StatUtils
from ..utils.helpers import standardize_team_code
from ..utils.log import debug, warn

def extract_substitutions_from_html(soup):
    """Extract ALL substitution types from HTML comment blocks."""
    import re
    from bs4 import Comment, BeautifulSoup

    debug("Searching for substitutions in HTML comment blocks...")

    substitutions = []

    pbp_div = soup.find('div', id='all_play_by_play') or soup.find('div', id='play_by_play')
    if not pbp_div:
        debug("No play-by-play div found")
        return []

    comments = pbp_div.find_all(string=lambda t: isinstance(t, Comment))
    debug(f"Found {len(comments)} comment blocks")
    
    for i, comment in enumerate(comments):
        comment_text = str(comment).lower()
        
        if 'pinch' in comment_text or 'moves from' in comment_text:
            debug(f"Comment {i} contains substitution info")
            
            try:
                comment_soup = BeautifulSoup(comment, 'html.parser')
                substitution_rows = comment_soup.find_all('tr', class_='ingame_substitution')
                
                if not substitution_rows:
                    all_rows = comment_soup.find_all('tr')
                    substitution_rows = [row for row in all_rows if 'pinch' in row.get_text().lower() or 'moves from' in row.get_text().lower()]
                
                debug(f"   Found {len(substitution_rows)} substitution rows in comment")
                
                for sub_row in substitution_rows:
                    divs = sub_row.find_all('div')
                    for div in divs:
                        div_text = div.get_text(strip=True)
                        
                        # Type 1: Initial pinch hit substitution
                        if 'pinch hits for' in div_text.lower():
                            debug(f"🔄 Found pinch hit: '{div_text}'")
                            
                            match = re.search(r'([^,\n]+?)\s+pinch hits for\s+([^,\(\n]+)', div_text, re.IGNORECASE)
                            if match:
                                pinch_hitter = match.group(1).strip().replace('&nbsp;', ' ')
                                replaced_player = match.group(2).strip().replace('&nbsp;', ' ')
                                
                                pinch_hitter = re.sub(r'\s+', ' ', pinch_hitter)
                                replaced_player = re.sub(r'\s+', ' ', replaced_player)
                                
                                # Try to extract inning from the substitution text/context
                                actual_inning = 7  # Default fallback
                                    
                                # Look for inning indicators in the div text or surrounding context
                                inning_patterns = [
                                    r'(?:top|bottom)\s*(\d+)',
                                    r'(\d+)(?:st|nd|rd|th)\s*inning',
                                    r'inning\s*(\d+)',
                                    r't(\d+)|b(\d+)'  # shorthand like t4, b6
                                ]

                                for pattern in inning_patterns:
                                    match = re.search(pattern, div_text.lower())
                                    if match:
                                        # Handle the t4/b6 pattern which has two groups
                                        if match.group(1):
                                            actual_inning = int(match.group(1))
                                        elif len(match.groups()) > 1 and match.group(2):
                                            actual_inning = int(match.group(2))
                                        break

                                # Try to extract inning from the parent row's csk attribute
                                try:
                                    # Find the parent <tr class="ingame_substitution"> row
                                    parent_row = div.find_parent('tr', class_='ingame_substitution')
                                    if parent_row:
                                        # Look for th with csk attribute
                                        th = parent_row.find('th', attrs={'data-stat': 'inning'})
                                        if th and th.get('csk'):
                                            csk_value = float(th.get('csk'))
                                            pass
                                    
                                    # Fallback: search for inning context in nearby HTML
                                    for prev_element in div.find_all_previous():
                                        if hasattr(prev_element, 'name') and prev_element.name == 'tr':
                                            # Look for inning data
                                            th = prev_element.find('th', attrs={'data-stat': 'inning'})
                                            if th and th.string:
                                                inning_text = th.string.strip().lower()
                                                if inning_text.startswith(('t', 'b')):
                                                    try:
                                                        inning_num = int(inning_text[1:])
                                                        actual_inning = inning_num
                                                        break
                                                    except (ValueError, IndexError):
                                                        pass

                                except Exception as e:
                                    debug(f"   ⚠️ Could not extract inning from HTML structure: {e}")

                                debug(f"   🔍 Extracted inning {actual_inning} for {pinch_hitter}")

                                substitutions.append({
                                    'type': 'pinch_hit',
                                    'pinch_hitter': pinch_hitter,
                                    'replaced_player': replaced_player,
                                    'inning': actual_inning,
                                    'text': div_text
                                })
                                
                                debug(f"✅ Extracted pinch hit: {pinch_hitter} replaces {replaced_player}")
                        
                        # Type 2: Pinch hitter moves to defensive position (NO LONGER PINCH HITTING)
                        elif 'moves from PH to' in div_text:
                            debug(f"🔄 Found PH→defense move: '{div_text}'")
                            
                            match = re.search(r'([^,\n]+?)\s+moves from PH to\s+([A-Z0-9]+)', div_text, re.IGNORECASE)
                            if match:
                                player_name = match.group(1).strip().replace('&nbsp;', ' ')
                                new_position = match.group(2).strip()
                                
                                player_name = re.sub(r'\s+', ' ', player_name)
                                
                                substitutions.append({
                                    'type': 'ph_to_defense',
                                    'player_name': player_name,
                                    'new_position': new_position,
                                    'inning': 10,  # Usually happens in extra innings
                                    'text': div_text
                                })
                                
                                debug(f"✅ Extracted PH→defense: {player_name} moves to {new_position}")
                
            except Exception as e:
                debug(f"   ❌ Error parsing comment {i}: {e}")
                continue
    
    debug(f"📊 Total substitutions found: {len(substitutions)}")
    return substitutions


class SpecialEventsEngine:
    def __init__(self, game_data, soup=None):
        self.game_data = game_data
        self.soup = soup
        self.basic = game_data.get("basic_info", {})
        self.home_team = self.basic.get("home_team", "")
        self.away_team = self.basic.get("away_team", "")
        self.home_score = self.basic.get("home_score_value", 0)
        self.away_score = self.basic.get("away_score_value", 0)
        self.game_id = game_data.get("game_id", "")
        self.game_date = self.basic.get("date_yyyymmdd", "")
        self.final_score = f"{self.basic.get('away_team_code')} {self.basic.get('away_score_value')} – {self.basic.get('home_score_value')} {self.basic.get('home_team_code')}"

        self.special_events = game_data.setdefault("special_events", {
            'walkoff': None,
            'immaculate_innings': [],
            'leadoff_hrs': [],
            'grand_slams': [],
            'pinch_hit_hrs': [],
        })

        # Build name-to-player-ID lookup from batting/pitching rosters
        self._name_to_id = {}
        for side in ('home', 'away'):
            for player in game_data.get('batting', {}).get(side, []):
                name = player.get('name', '').strip()
                pid = player.get('player_id', '')
                if name and pid:
                    self._name_to_id[name] = pid
                    self._name_to_id[self._normalize_name_for_comparison(name)] = pid
            for player in game_data.get('pitching', {}).get(side, []):
                name = player.get('name', '').strip()
                pid = player.get('player_id', '')
                if name and pid:
                    self._name_to_id[name] = pid
                    self._name_to_id[self._normalize_name_for_comparison(name)] = pid

    def _normalize_name_for_comparison(self, name):
        """Normalize name for comparison by removing accents and standardizing."""
        if not name:
            return ""

        normalized = unicodedata.normalize('NFD', name)
        ascii_name = ''.join(char for char in normalized if unicodedata.category(char) != 'Mn')

        return ascii_name.strip().lower()

    def _resolve_player_id(self, name):
        """Resolve a player name to their BREF player ID."""
        if not name:
            return ""
        # Try exact match first, then normalized
        return self._name_to_id.get(name, "") or self._name_to_id.get(self._normalize_name_for_comparison(name), "")

    def get_footer_stat_count(self, player_name, team_type, stat_type):
        """Get stat count for player from footer data."""
        footer_summary = self.game_data.get("footer_summary", {})
        stat_blob = footer_summary.get(team_type, {}).get(stat_type, "")
        
        if stat_blob:
            from ..excel.generators import ExcelGeneratorUtils
            player_name_normalized = self._normalize_name_for_comparison(player_name)
            
            for name, count in ExcelGeneratorUtils.extract_stat_counts(stat_blob):
                footer_name_normalized = self._normalize_name_for_comparison(name)
                if footer_name_normalized == player_name_normalized:
                    return count
        return 0

    def get_footer_prioritized_player_stats(self, player_name, team_type):
        """Get complete player stats with footer data prioritized over box score."""
        # Find player in batting data
        player_box_stats = None
        for player in self.game_data.get('batting', {}).get(team_type, []):
            if player.get('name', '') == player_name:
                player_box_stats = player
                break
        
        if not player_box_stats:
            return {}
        
        # Start with box score stats
        stats = dict(player_box_stats)
        
        # Override with footer stats where available
        for stat_key in ['HR', '2B', '3B']:
            footer_count = self.get_footer_stat_count(player_name, team_type, stat_key)
            if footer_count > 0:
                stats[stat_key] = footer_count
        
        return stats

    def detect(self):
        self.detect_walkoff()
        self.detect_leadoff_home_runs()
        self.detect_grand_slams()
        
        # Always use HTML-based detection (soup should always be available)
        if self.soup:
            self.detect_pinch_hit_hrs_from_html()
        else:
            debug("⚠️ No HTML soup available - pinch hit detection skipped")
        
        return self.game_data

    def detect_walkoff(self):
        if self.home_score > self.away_score:
            plays = self.game_data.get("play_by_play", [])
            last_play = plays[-1] if plays else None
            if last_play and last_play.get("half") == "bottom" and (last_play.get("run_scored", False) or last_play.get("home_run", False)):
                batter_name = last_play.get("batter", "Unknown")
                self.special_events["walkoff"] = {
                    "batter": batter_name,
                    "batter_id": last_play.get("batter_id", "") or self._resolve_player_id(batter_name),
                    "team": last_play.get("batting_team", ""),
                    "team_code": self.basic.get("home_team_code", ""),
                    "opposing_team": self.away_team,
                    "opponent_code": self.basic.get("away_team_code", ""),
                    "description": last_play.get("description", ""),
                    "inning": last_play.get("inning", 0),
                    "play_type": self.determine_play_type(last_play),
                    "game_id": self.game_id,
                    "game_date": self.game_date,
                    "final_score": self.final_score
                }

    def detect_leadoff_home_runs(self):
        plays = self.game_data.get("play_by_play", [])
        for i, play in enumerate(plays):
            inning = play.get("inning", 0)
            half = play.get("half", "")
            if inning == 1:
                is_first = (
                    (half == "top" and i == 0) or
                    (half == "bottom" and all(p.get("half") != "bottom" for p in plays[:i]))
                )
                if is_first and play.get("home_run", False):
                    team = play.get("batting_team", "")
                    team_code = self.basic.get("away_team_code" if half == "top" else "home_team_code")
                    opp_team = self.home_team if team == self.away_team else self.away_team
                    opp_code = self.basic.get("home_team_code" if half == "top" else "away_team_code")
                    leadoff_batter = play.get("batter", "Unknown")
                    self.special_events["leadoff_hrs"].append({
                        "batter": leadoff_batter,
                        "batter_id": play.get("batter_id", "") or self._resolve_player_id(leadoff_batter),
                        "team": team,
                        "team_code": team_code,
                        "opposing_team": opp_team,
                        "opponent_code": opp_code,
                        "half": half,
                        "description": play.get("description", ""),
                        "pitcher": play.get("pitcher", ""),
                        "game_id": self.game_id,
                        "game_date": self.game_date,
                        "final_score": self.final_score
                    })

    def detect_grand_slams(self):
        fs = self.game_data.get("footer_summary", {})
        for side in ("home", "away"):
            hr_blob = fs.get(side, {}).get("HR", "")
            for entry in hr_blob.split(";"):
                if "3 on" not in entry:
                    continue  # skip non-GS entries

                # Normalize
                entry = unicodedata.normalize("NFKD", entry).strip()

                # Step 1: Get player name before the parentheses
                name_match = re.match(r"^(.*?)\s+\d+\s+\(", entry) or re.match(r"^(.*?)\s*\(", entry)
                if not name_match:
                    continue
                batter = name_match.group(1).strip()

                # Step 2: Extract content inside parentheses
                paren_match = re.search(r"\((.+)\)", entry, re.DOTALL)
                if not paren_match:
                    continue
                hr_detail = paren_match.group(1)

                # Step 3: Chunk the HR detail string into individual HR descriptions
                chunks = re.split(r";\s*|\s*(?=\d+\s+off|\boff\b)", hr_detail)
                chunks = [chunk.strip() for chunk in chunks if chunk.strip()]

                pitcher = None
                for chunk in chunks:
                    if "3 on" not in chunk:
                        continue  # skip non-GS HRs

                    # Update pitcher if 'off ...' is present
                    pitcher_match = re.search(r"off ([^,]+)", chunk)
                    if pitcher_match:
                        pitcher = pitcher_match.group(1).strip()

                    inning_match = re.search(r"(\d+)(?:st|nd|rd|th) inn", chunk)
                    if not inning_match:
                        continue

                    inning = inning_match.group(1)
                    matched_half = "Top" if side == "away" else "Bottom"

                    # ADDED: Get complete batting stats using footer-prioritized lookup
                    enhanced_stats = self.get_footer_prioritized_player_stats(batter, side)
                    
                    # Extract specific stats with Grand Slam minimums
                    home_runs = enhanced_stats.get('HR', 1)  # At least 1 for the grand slam
                    doubles = enhanced_stats.get('2B', 0)
                    triples = enhanced_stats.get('3B', 0)
                    hits = enhanced_stats.get('H', 1)        # At least 1 for the grand slam
                    runs = enhanced_stats.get('R', 0)
                    rbi = enhanced_stats.get('RBI', 4)       # At least 4 for the grand slam
                    ab = enhanced_stats.get('AB', 1)         # At least 1 AB
                    bb = enhanced_stats.get('BB', 0)
                    so = enhanced_stats.get('SO', 0)

                    self.special_events["grand_slams"].append({
                        "player": batter,
                        "player_id": self._resolve_player_id(batter),
                        "team": self.home_team if side == "home" else self.away_team,
                        "team_code": self.basic.get(f"{side}_team_code", ""),
                        "opposing_team": self.away_team if side == "home" else self.home_team,
                        "opponent_code": self.basic.get("away_team_code" if side == "home" else "home_team_code"),
                        "description": "Grand Slam",
                        "pitcher": pitcher or "Unknown",
                        "game_id": self.game_id,
                        "game_date": self.game_date,
                        "final_score": self.final_score,
                        "half": matched_half,
                        "inning": inning,
                        # ADDED: Complete batting stats with footer-prioritized data
                        "home_runs": home_runs,
                        "doubles": doubles, 
                        "triples": triples,
                        "hits": hits,
                        "runs": runs,
                        "rbi": rbi,
                        "ab": ab,
                        "bb": bb,
                        "so": so
                    })

    def detect_pinch_hit_hrs_from_html(self):
        """Detect pinch hit home runs with chronological substitution processing."""
        try:
            if not self.soup:
                debug("❌ No HTML soup available for substitution parsing")
                return
            
            # Extract ALL substitution types from HTML
            substitutions = extract_substitutions_from_html(self.soup)
            
            for i, sub in enumerate(substitutions):
                debug(f"   Sub {i+1}: {sub.get('type')} - {sub.get('pinch_hitter', sub.get('player_name', 'Unknown'))} in inning {sub.get('inning')}")
            
            if not substitutions:
                debug("❌ No substitutions found in HTML")
                return
            
            # Use the name-to-ID lookup built in __init__
            name_to_id = self._name_to_id
            debug(f"🔍 Using name-to-ID lookup with {len(name_to_id)} entries")
            
            # Track active pinch hitters by player ID
            pinch_hitters_by_id = {}
            
            # Process play-by-play inning by inning, applying substitutions as we go
            max_inning = max((play.get('inning', 0) for play in self.game_data.get("play_by_play", [])), default=9)
            
            for current_inning in range(1, max_inning + 1):
                debug(f"📍 Processing inning {current_inning}")
                
                # STEP 1: Apply any substitutions that happen at the start of this inning
                inning_substitutions = [sub for sub in substitutions if sub.get('inning', 0) == current_inning]
                
                for sub in inning_substitutions:
                    sub_type = sub.get('type', '')
                    
                    if sub_type == 'pinch_hit':
                        # Player enters as pinch hitter
                        pinch_hitter_name = sub['pinch_hitter']
                        
                        # Find actual player ID
                        player_id = None
                        for name_variant, actual_id in name_to_id.items():
                            if name_variant.lower() == pinch_hitter_name.lower():
                                player_id = actual_id
                                break
                        
                        if player_id:
                            pinch_hitters_by_id[player_id] = {
                                'active': True,
                                'inning': current_inning,
                                'player_name': pinch_hitter_name,
                                'replaced_player': sub['replaced_player']
                            }
                            debug(f"🔄 ACTIVATED pinch hitter: {pinch_hitter_name} (ID: {player_id})")
                    
                    elif sub_type == 'ph_to_defense':
                        # Player moves from PH to defensive position
                        player_name = sub['player_name']
                        
                        for player_id, info in pinch_hitters_by_id.items():
                            if info['player_name'].lower() == player_name.lower() and info['active']:
                                info['active'] = False
                                debug(f"🔄 DEACTIVATED pinch hitter: {player_name} (moved to {sub['new_position']})")
                                break
                
                # STEP 2: Check this inning's plays for home runs by active pinch hitters
                inning_plays = [play for play in self.game_data.get("play_by_play", []) if play.get('inning', 0) == current_inning]
                debug(f"   📊 {len(inning_plays)} plays in this inning")
                debug(f"   👤 Active pinch hitters: {[(pid, info['player_name']) for pid, info in pinch_hitters_by_id.items() if info['active']]}")
                
                for play in inning_plays:
                    batter_name = play.get('batter', '').strip()
                    
                    # ROBUST name resolution - try multiple strategies
                    actual_player_id = None
                    
                    # Method 1: Exact match
                    if batter_name in name_to_id:
                        actual_player_id = name_to_id[batter_name]
                    
                    # Method 2: Normalized match
                    if not actual_player_id:
                        normalized_batter = batter_name.replace('&nbsp;', ' ').replace('\xa0', ' ').strip()
                        if normalized_batter in name_to_id:
                            actual_player_id = name_to_id[normalized_batter]
                    
                    # Method 3: Case-insensitive match
                    if not actual_player_id:
                        for name_variant, player_id in name_to_id.items():
                            if name_variant.lower() == batter_name.lower():
                                actual_player_id = player_id
                                break
                    
                    # Method 4: Unicode normalization
                    if not actual_player_id:
                        normalized_batter = unicodedata.normalize('NFKD', batter_name).strip()
                        
                        for name_variant, player_id in name_to_id.items():
                            normalized_variant = unicodedata.normalize('NFKD', name_variant).strip()
                            if normalized_variant == normalized_batter:
                                actual_player_id = player_id
                                break
                    
                    if play.get('home_run', False):
                        
                        # Show all name matching attempts
                        if actual_player_id:
                            debug(f"   ✅ Resolved player ID: {actual_player_id}")
                        else:
                            debug(f"   ❌ Could not resolve player ID for '{batter_name}'")
                            debug(f"   📝 Available names in lookup: {list(name_to_id.keys())}")
                        
                        debug(f"🏠 Home run by '{batter_name}' (ID: {actual_player_id}) in inning {current_inning}")
                        
                        if actual_player_id and actual_player_id in pinch_hitters_by_id:
                            pinch_info = pinch_hitters_by_id[actual_player_id]
                            debug(f"   📋 Pinch hitter status: active={pinch_info['active']}, entered inning {pinch_info['inning']}")
                            
                            if pinch_info['active']:
                                debug(f"🎯 PINCH HIT HR CONFIRMED: {batter_name} (ID: {actual_player_id})")
                                
                                # Extract RBI from the play features (already calculated)
                                play_rbi = play.get('rbi', 1)  # Default to 1 if not calculated
                                
                                # Determine team info  
                                batting_team = play.get('batting_team', '')
                                side = 'away' if batting_team == self.basic.get('away_team') else 'home'
                                
                                self.special_events['pinch_hit_hrs'].append({
                                    'player': batter_name,
                                    'player_id': actual_player_id,
                                    'team': self.basic.get(f'{side}_team', ''),
                                    'team_code': self.basic.get(f'{side}_team_code', ''),
                                    'opposing_team': self.basic.get('away_team' if side == 'home' else 'home_team', ''),
                                    'opponent_code': self.basic.get('home_team_code' if side == 'away' else 'away_team_code', ''),
                                    'inning': current_inning,
                                    'half': play.get('half', ''),
                                    'description': play.get('description', ''),
                                    'pitcher': play.get('pitcher', ''),
                                    'game_id': self.game_id,
                                    'game_date': self.game_date,
                                    'final_score': self.final_score,
                                    'is_home_game': side == 'home',
                                    'replaced_player': pinch_info['replaced_player'],
                                    # Add the missing fields using the play's calculated RBI
                                    'home_runs': 1,
                                    'rbi': play_rbi
                                })
                                
                                # Deactivate after pinch hit HR
                                pinch_info['active'] = False
                                debug(f"✅ Added pinch hit HR and deactivated {batter_name}")
                                
                            else:
                                debug(f"   ⚠️ Former pinch hitter {batter_name} but no longer active")
                        else:
                            debug(f"   ℹ️ Regular HR by {batter_name} (not a tracked pinch hitter)")
                    
                    # Deactivate pinch hitters after any plate appearance
                    elif actual_player_id and actual_player_id in pinch_hitters_by_id:
                        pinch_info = pinch_hitters_by_id[actual_player_id]
                        if pinch_info['active']:
                            description = play.get('description', '').lower()
                            debug(f"   🔍 Non-HR play by active pinch hitter {batter_name}: '{description}'")
                            
                            # Comprehensive plate appearance keywords (any PA result should deactivate)
                            pa_keywords = [
                                # Hits
                                'single', 'double', 'triple', 'hit',
                                # Outs 
                                'out', 'fly', 'ground', 'pop', 'line', 'strike', 'caught', 'force',
                                # Walks and HBP
                                'walk', 'walked', 'ball', 'hit by pitch', 'hbp', 'plunk',
                                # Sacrifices
                                'sacrifice', 'sac fly', 'sac bunt', 'bunt',
                                # Errors and other ways to reach
                                'error', 'reach', 'safe', 'interference', 'obstruct',
                                # Fielder's choice
                                'fielder', 'choice'
                            ]
                            
                            matched_keyword = None
                            for keyword in pa_keywords:
                                if keyword in description:
                                    matched_keyword = keyword
                                    break
                            
                            if matched_keyword:
                                pinch_info['active'] = False
                                debug(f"🔥 Deactivated {batter_name} after completing pinch hit PA (matched: '{matched_keyword}')")
                            else:
                                debug(f"   🔍 No deactivation keywords found in: '{description}'")
                                debug(f"   🔍 Looking for: {pa_keywords}")
                    else:
                        # Debug: show all plate appearances
                        if batter_name:
                            description = play.get('description', '')
                            debug(f"   📝 Regular play by {batter_name}: '{description}'")
                
                # End of inning summary
                debug(f"🔚 End of inning {current_inning} summary:")
                for pid, info in pinch_hitters_by_id.items():
                    status = "ACTIVE" if info['active'] else "inactive"
                    debug(f"   {info['player_name']}: {status} (entered inning {info['inning']})")
            
            debug(f"🔍 Final result: Found {len(self.special_events.get('pinch_hit_hrs', []))} pinch hit HRs")
            
        except Exception as e:
            debug(f"Exception in pinch hit detection: {e}")
            logging.exception("Error details:")

    def determine_play_type(self, play):
        if play.get("home_run", False):
            return "Home Run"
        elif play.get("triple", False):
            return "Triple"
        elif play.get("double", False):
            return "Double"
        elif play.get("single", False):
            return "Single"
        elif play.get("walk", False):
            return "Walk"
        elif play.get("hit_by_pitch", False):
            return "Hit By Pitch"
        elif play.get("error", False):
            return "Error"
        elif play.get("fielders_choice", False):
            return "Fielder's Choice"
        elif play.get("sacrifice", False):
            return "Sacrifice"
        elif play.get("strikeout", False):
            return "Strikeout"
        else:
            return "Other"