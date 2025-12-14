"""
Data serializers for converting DataFrames to JSON format for website.
Complete version with all stats fields and game-by-game data.
"""
import pandas as pd

class DataSerializer:
    """Convert baseball DataFrames to JSON-serializable format."""
    
    def serialize_all_data(self, data):
        """Convert all data structures to JSON format."""
        print("   🔄 Serializing data for website...")
        
        # Store reference to data for use in other methods
        self.data = data
        
        # Get the raw games for game-by-game breakdown
        raw_games = data.get('_raw_games', [])
        json_data = {
            "summary": self._serialize_summary(data.get('summary_rows', [])),
            "milestones": self._serialize_milestones(data.get('milestones', {})),
            "players": self._serialize_players(data.get('hitters')),
            "pitchers": self._serialize_pitchers(data.get('pitchers')),
            "playersWithoutStats": self._serialize_players_without_stats(data.get('players_without_stats')),
            "teams": self._serialize_teams(data.get('team_records')),
            "games": self._serialize_games(data.get('game_log'), data.get('_raw_games', [])),
            "stadiums": self._serialize_stadiums(data.get('stadiums')),
            "orioles": self._serialize_orioles(data.get('ori_stads')),
            "debuts": self._serialize_debuts(data.get('mlb_debut_rows', [])),
            "finalGames": self._serialize_final_games(data.get('final_game_rows', [])),
            "signatureHRs": self._serialize_signature_hrs(data.get('df_splash')),
            "matchupMatrix": self._serialize_matchup_matrix(data.get('df_matchups')),
            "playerGames": self._serialize_player_games(raw_games),
            "pitcherGames": self._serialize_pitcher_games(raw_games),
        }
        
        counts = [
            f"Summary: {len(json_data['summary'])}",
            f"Milestones: {len(json_data['milestones'])}",
            f"Players: {len(json_data['players'])}",
            f"Pitchers: {len(json_data['pitchers'])}",
            f"Games: {len(json_data['games'])}",
            f"PlayerGames: {len(json_data['playerGames'])}",
            f"PitcherGames: {len(json_data['pitcherGames'])}",
        ]
        print(f"      {', '.join(counts)}")
        
        return json_data
    
    def _serialize_summary(self, summary_rows):
        """Convert summary statistics to JSON."""
        if not summary_rows:
            return []
        
        return [
            {
                "record": str(row.get("Record", "")),
                "value": str(row.get("Value", "")),
                "detail": str(row.get("Detail", "")),
                "score": str(row.get("Score", "")),
                "gameIds": str(row.get("GameIDs", ""))
            }
            for row in summary_rows
        ]
    
    def _serialize_milestones(self, milestones_dict):
        """Convert all milestone DataFrames to combined JSON list."""
        all_milestones = []
        
        if not milestones_dict:
            return all_milestones
        
        for milestone_type, df in milestones_dict.items():
            if df is None or df.empty:
                continue
            
            df_sorted = df.copy()
            df_sorted['_date_sort'] = pd.to_datetime(df_sorted['Date'], errors='coerce')
            df_sorted = df_sorted.sort_values('_date_sort', ascending=False)
            
            for _, row in df_sorted.iterrows():
                milestone = {
                    "type": milestone_type,
                    "date": str(row.get("Date", "")),
                    "player": str(row.get("Player", "")),
                    "playerId": str(row.get("Player ID", "")) if "Player ID" in row else "",
                    "team": str(row.get("Team", "")),
                    "opponent": str(row.get("Opponent", "")),
                    "gameId": str(row.get("GameID", ""))
                }
                
                if milestone_type == "Consecutive HR Instances":
                    players = str(row.get("Players", ""))
                    hr_count = int(row.get("HR Count", 0)) if pd.notna(row.get("HR Count")) else 0
                    inning = str(row.get("Inning", ""))
                    milestone.update({
                        "player": players,
                        "detail": f"{hr_count} consecutive HRs in {inning}: {players}"
                    })
                
                elif milestone_type in ["Multi-HR Games", "4+ Hit Games", "5+ RBI Games", "Cycles"]:
                    hr = int(row.get("HR", 0)) if pd.notna(row.get("HR")) else 0
                    h = int(row.get("H", 0)) if pd.notna(row.get("H")) else 0
                    rbi = int(row.get("RBI", 0)) if pd.notna(row.get("RBI")) else 0
                    doubles = int(row.get("2B", 0)) if pd.notna(row.get("2B")) else 0
                    triples = int(row.get("3B", 0)) if pd.notna(row.get("3B")) else 0
                    milestone.update({
                        "hr": hr, "h": h, "rbi": rbi, "2b": doubles, "3b": triples,
                        "detail": f"{h} H ({doubles} 2B, {triples} 3B, {hr} HR), {rbi} RBI"
                    })
                    
                elif milestone_type in ["10+ K Games", "Quality Starts", "Complete Games & Shutouts", "No-Hitters"]:
                    ip = str(row.get("IP", "0.0"))
                    so = int(row.get("SO", 0)) if pd.notna(row.get("SO")) else 0
                    h = int(row.get("H", 0)) if pd.notna(row.get("H")) else 0
                    er = int(row.get("ER", 0)) if pd.notna(row.get("ER")) else 0
                    bb = int(row.get("BB", 0)) if pd.notna(row.get("BB")) else 0
                    milestone.update({
                        "ip": ip, "so": so, "h": h, "er": er, "bb": bb,
                        "detail": f"{ip} IP, {h} H, {er} ER, {bb} BB, {so} SO"
                    })
                    
                elif milestone_type in ["3 Strikeout Innings", "Immaculate Innings"]:
                    inning = str(row.get("Inning", ""))
                    batters = str(row.get("Batters Struck Out", ""))
                    milestone.update({
                        "inning": inning, "batters": batters,
                        "detail": f"{inning} - {batters}"
                    })
                
                elif "Detail" in row and pd.notna(row.get("Detail")):
                    milestone["detail"] = str(row.get("Detail", ""))
                else:
                    milestone["detail"] = ""
                
                if pd.notna(row.get('_date_sort')):
                    milestone['_dateSort'] = row['_date_sort'].strftime('%Y-%m-%d')
                
                all_milestones.append(milestone)
        
        all_milestones.sort(key=lambda x: x.get('_dateSort', ''), reverse=True)
        return all_milestones
    
    def _serialize_players(self, df):
        """Convert ALL hitters DataFrame to JSON with complete stats and date range."""
        if df is None or df.empty:
            return []
        
        players = []
        for _, row in df.iterrows():
            try:
                game_ids = str(row.get("GameIDs", ""))
                first_date, last_date = self._extract_date_range_from_gameids(game_ids)
                
                players.append({
                    "name": str(row.get("Name", "")),
                    "playerId": str(row.get("Player ID", "")),
                    "team": str(row.get("Team", "")),
                    "games": int(row.get("G", 0)),
                    "ab": int(row.get("AB", 0)),
                    "pa": int(row.get("PA", 0)),
                    "h": int(row.get("H", 0)),
                    "avg": f"{float(row.get('AVG', 0)):.3f}",
                    "r": int(row.get("R", 0)),
                    "rbi": int(row.get("RBI", 0)),
                    "hr": int(row.get("HR", 0)),
                    "doubles": int(row.get("2B", 0)),
                    "triples": int(row.get("3B", 0)),
                    "sb": int(row.get("SB", 0)),
                    "cs": int(row.get("CS", 0)),
                    "bb": int(row.get("BB", 0)),
                    "so": int(row.get("SO", 0)),
                    "hbp": int(row.get("HBP", 0)),
                    "gidp": int(row.get("GIDP", 0)),
                    "tb": int(row.get("TB", 0)),
                    "xbh": int(row.get("XBH", 0)),
                    "obp": f"{float(row.get('OBP', 0)):.3f}",
                    "slg": f"{float(row.get('SLG', 0)):.3f}",
                    "ops": f"{float(row.get('OPS', 0)):.3f}",
                    "firstGame": first_date,
                    "lastGame": last_date,
                })
            except:
                continue
        return players
    
    def _serialize_pitchers(self, df):
        """Convert ALL pitchers DataFrame to JSON with complete stats and date range."""
        if df is None or df.empty:
            return []
        
        pitchers = []
        for _, row in df.iterrows():
            try:
                era = row.get("ERA")
                whip = row.get("WHIP")
                game_ids = str(row.get("GameIDs", ""))
                first_date, last_date = self._extract_date_range_from_gameids(game_ids)
                
                pitchers.append({
                    "name": str(row.get("Name", "")),
                    "playerId": str(row.get("Player ID", "")),
                    "team": str(row.get("Team", "")),
                    "games": int(row.get("G", 0)),
                    "gameStarts": int(row.get("GS", 0)),
                    "wins": int(row.get("W", 0)),
                    "losses": int(row.get("L", 0)),
                    "saves": int(row.get("SV", 0)),
                    "ip": str(row.get("IP", "0.0")),
                    "era": f"{float(era):.2f}" if era is not None and pd.notna(era) else "N/A",
                    "whip": f"{float(whip):.3f}" if whip is not None and pd.notna(whip) else "N/A",
                    "h": int(row.get("H", 0)),
                    "r": int(row.get("R", 0)),
                    "er": int(row.get("ER", 0)),
                    "bb": int(row.get("BB", 0)),
                    "so": int(row.get("SO", 0)),
                    "hr": int(row.get("HR", 0)),
                    "firstGame": first_date,
                    "lastGame": last_date,
                })
            except:
                continue
        return pitchers
    
    def _serialize_player_games(self, games):
        """Create game-by-game hitting records with footer stats merged in."""
        player_games = []
        
        for game in games:
            try:
                # Extract extra stats from play-by-play
                extra_stats = self._extract_extra_batting_stats(game)
                
                basic_info = game.get('basic_info', {})
                game_id = game.get('game_id', '')
                date_str = basic_info.get('date_yyyymmdd', '')
                
                # Initialize with defaults FIRST
                formatted_date = ''
                sortable_date = ''
                
                # Try to format if we have a valid date
                if date_str and len(date_str) == 8 and date_str.isdigit():
                    formatted_date = f"{date_str[4:6]}/{date_str[6:8]}/{date_str[0:4]}"
                    sortable_date = f"{date_str[0:4]}-{date_str[4:6]}-{date_str[6:8]}"
                elif game_id and len(game_id) >= 11:
                    # Fallback: extract from game_id (e.g., "BAL201904040")
                    date_str = game_id[3:11]
                    if len(date_str) == 8 and date_str.isdigit():
                        formatted_date = f"{date_str[4:6]}/{date_str[6:8]}/{date_str[0:4]}"
                        sortable_date = f"{date_str[0:4]}-{date_str[4:6]}-{date_str[6:8]}"
                
                for side in ['home', 'away']:
                    team = basic_info.get(f'{side}_team_code', '')
                    opponent = basic_info.get('away_team_code' if side == 'home' else 'home_team_code', '')
                    
                    for player in game.get('batting', {}).get(side, []):
                        player_id = player.get('player_id', '')
                        if not player_id:
                            continue
                        
                        ab = int(player.get('AB', 0))
                        pa = int(player.get('PA', 0))
                        if ab == 0 and pa == 0:
                            continue
                        
                        # Get extra stats for this player by ID
                        player_extra = extra_stats.get(player_id, {})
                        
                        player_games.append({
                            'date': formatted_date,
                            'dateSort': sortable_date,
                            'playerId': player_id,
                            'name': str(player.get('name', '')),
                            'team': team,
                            'opponent': opponent,
                            'gameId': game_id,
                            'ab': ab,
                            'pa': pa,
                            'h': int(player.get('H', 0)),
                            'r': int(player.get('R', 0)),
                            'rbi': int(player.get('RBI', 0)),
                            'hr': player_extra.get('HR', 0),
                            'doubles': player_extra.get('2B', 0),
                            'triples': player_extra.get('3B', 0),
                            'sb': max(int(player.get('SB', 0)), player_extra.get('SB', 0)),
                            'cs': max(int(player.get('CS', 0)), player_extra.get('CS', 0)),
                            'bb': int(player.get('BB', 0)),
                            'so': int(player.get('SO', 0)),
                            'hbp': player_extra.get('HBP', 0),
                            'gidp': player_extra.get('GIDP', 0),
                        })
            except Exception as e:
                print(f"   ⚠️ Error serializing player game: {e}")
                continue
        
        return player_games

    def _extract_extra_batting_stats(self, game):
        """Extract 2B, 3B, HR, SB, CS, HBP, GIDP from play-by-play data."""
        player_stats = {}
        
        plays = game.get('play_by_play', [])
        
        # Build player_id lookup from batting
        player_name_to_id = {}
        for side in ['home', 'away']:
            for player in game.get('batting', {}).get(side, []):
                name = player.get('name', '').replace('\u00a0', ' ')
                player_id = player.get('player_id', '')
                if player_id:
                    player_name_to_id[name] = player_id
        
        for play in plays:
            batter = play.get('batter', '').replace('\u00a0', ' ')
            player_id = player_name_to_id.get(batter)
            
            if not player_id:
                continue
            
            if player_id not in player_stats:
                player_stats[player_id] = {
                    '2B': 0, '3B': 0, 'HR': 0, 'SB': 0, 'CS': 0, 
                    'HBP': 0, 'GIDP': 0
                }
            
            # Count extra base hits from play-by-play
            if play.get('double'): 
                player_stats[player_id]['2B'] += 1
            if play.get('triple'): 
                player_stats[player_id]['3B'] += 1
            if play.get('home_run'): 
                player_stats[player_id]['HR'] += 1
            if play.get('hit_by_pitch'): 
                player_stats[player_id]['HBP'] += 1
            if play.get('double_play'): 
                player_stats[player_id]['GIDP'] += 1
            
            # Check description for SB/CS (they're not always in the main flags)
            desc = play.get('description', '').lower()
            if 'steals' in desc or 'stolen base' in desc:
                player_stats[player_id]['SB'] += 1
            if 'caught stealing' in desc or play.get('Details') == 'CS':
                player_stats[player_id]['CS'] += 1
        
        return player_stats    
    
    def _serialize_pitcher_games(self, games):
        """Create game-by-game pitching records."""
        pitcher_games = []
        
        for game in games:
            try:
                basic_info = game.get('basic_info', {})
                game_id = game.get('game_id', '')
                date_str = basic_info.get('date_yyyymmdd', '')
                
                # Initialize with defaults FIRST
                formatted_date = ''
                sortable_date = ''
                
                # Try to format if we have a valid date
                if date_str and len(date_str) == 8 and date_str.isdigit():
                    formatted_date = f"{date_str[4:6]}/{date_str[6:8]}/{date_str[0:4]}"
                    sortable_date = f"{date_str[0:4]}-{date_str[4:6]}-{date_str[6:8]}"
                elif game_id and len(game_id) >= 11:
                    # Fallback: extract from game_id
                    date_str = game_id[3:11]
                    if len(date_str) == 8 and date_str.isdigit():
                        formatted_date = f"{date_str[4:6]}/{date_str[6:8]}/{date_str[0:4]}"
                        sortable_date = f"{date_str[0:4]}-{date_str[4:6]}-{date_str[6:8]}"
                
                for side in ['home', 'away']:
                    team = basic_info.get(f'{side}_team_code', '')
                    opponent = basic_info.get('away_team_code' if side == 'home' else 'home_team_code', '')
                    
                    for pitcher in game.get('pitching', {}).get(side, []):
                        player_id = pitcher.get('player_id', '')
                        if not player_id:
                            continue
                        
                        ip_str = str(pitcher.get('IP', '0'))
                        if ip_str == '0' or ip_str == '0.0':
                            continue
                        
                        # Convert IP to outs for accurate aggregation
                        try:
                            if '.' in ip_str:
                                parts = ip_str.split('.')
                                outs = int(parts[0]) * 3 + int(parts[1])
                            else:
                                outs = int(float(ip_str) * 3)
                        except:
                            outs = 0
                        
                        if outs == 0:
                            continue
                        
                        pitcher_games.append({
                            'date': formatted_date,
                            'dateSort': sortable_date,
                            'playerId': player_id,
                            'name': str(pitcher.get('name', '')),
                            'team': team,
                            'opponent': opponent,
                            'gameId': game_id,
                            'outs': outs,
                            'h': int(pitcher.get('H', 0)),
                            'r': int(pitcher.get('R', 0)),
                            'er': int(pitcher.get('ER', 0)),
                            'bb': int(pitcher.get('BB', 0)),
                            'so': int(pitcher.get('SO', 0)),
                            'hr': int(pitcher.get('HR', 0)),
                            'wins': 1 if pitcher.get('win') else 0,
                            'losses': 1 if pitcher.get('loss') else 0,
                            'saves': 1 if pitcher.get('save') else 0,
                            'gameStarts': 1 if pitcher == game.get('pitching', {}).get(side, [{}])[0] else 0,
                        })
            except Exception as e:
                print(f"   ⚠️ Error serializing pitcher game: {e}")
                continue
        
        return pitcher_games
    
    def _extract_date_range_from_gameids(self, game_ids_str):
        """Extract first and last game dates from comma-separated GameIDs."""
        try:
            if not game_ids_str or game_ids_str == '':
                return '', ''
            
            game_ids = [gid.strip() for gid in game_ids_str.split(',') if gid.strip()]
            if not game_ids:
                return '', ''
            
            first_game = game_ids[0]
            last_game = game_ids[-1]
            
            def extract_date(game_id):
                if len(game_id) >= 11:
                    date_str = game_id[3:11]
                    return f"{date_str[4:6]}/{date_str[6:8]}/{date_str[0:4]}"
                return ''
            
            return extract_date(first_game), extract_date(last_game)
        except:
            return '', ''
    
    def _serialize_players_without_stats(self, df):
        """Convert players without stats DataFrame to JSON."""
        if df is None or df.empty:
            return []
        
        players = []
        for _, row in df.iterrows():
            try:
                players.append({
                    "name": str(row.get("Name", "")),
                    "playerId": str(row.get("Player ID", "")),
                    "teams": str(row.get("Team(s)", "")),
                    "games": int(row.get("Games", 0)),
                    "positions": str(row.get("Position(s)", "")),
                })
            except:
                continue
        return players
    
    def _serialize_teams(self, df):
        """Convert team records DataFrame to JSON."""
        if df is None or df.empty:
            return []
        
        teams = []
        for _, row in df.iterrows():
            try:
                teams.append({
                    "team": str(row.get("Team", "")),
                    "games": int(row.get("Games", 0)),
                    "record": str(row.get("Record", "0-0")),
                    "runs": int(row.get("Runs Scored", 0)) if pd.notna(row.get("Runs Scored")) else 0,
                    "runsAllowed": int(row.get("Runs Allowed", 0)) if pd.notna(row.get("Runs Allowed")) else 0,
                    "diff": str(row.get("Run Differential", "0")),
                    "homeRecord": str(row.get("Home Record", "")),
                    "awayRecord": str(row.get("Away Record", "")),
                    "oneRunGames": str(row.get("1-Run Games", "")),
                    "blowouts": str(row.get("Blowouts (5+)", "")),
                })
            except:
                continue
        return teams
    
    def _serialize_games(self, df, raw_games=None):
        """Convert ALL games from game log with enhanced details."""
        if df is None or df.empty:
            return []
        
        # Use provided raw_games or try to get from stored data
        if raw_games is None:
            raw_games = getattr(self, 'data', {}).get('_raw_games', [])
        
        raw_games_by_id = {g.get('game_id', ''): g for g in raw_games}
        
        games = []
        for _, row in df.iterrows():
            try:
                date_val = row.get("Date")
                if hasattr(date_val, 'strftime'):
                    date_str = date_val.strftime("%m/%d/%Y")
                else:
                    date_str = str(date_val)
                
                game_id = str(row.get("GameID", ""))
                if game_id.startswith('=HYPERLINK'):
                    import re
                    match = re.search(r'"([^"]+)"\)$', game_id)
                    if match:
                        game_id = match.group(1)
                
                game_obj = {
                    "date": date_str,
                    "startTime": str(row.get("Start Time", "")),
                    "awayTeam": str(row.get("Away Team", "")),
                    "homeTeam": str(row.get("Home Team", "")),
                    "score": str(row.get("Score", "")),
                    "venue": str(row.get("Venue", "")),
                    "attendance": int(row.get("Attendance", 0)) if pd.notna(row.get("Attendance")) else 0,
                    "gameLength": self._format_game_length(row.get("Game Length", "")),
                    "gameId": game_id
                }
                
                # Add enhanced details from raw game data if available
                raw_game = raw_games_by_id.get(game_id)
                if raw_game:
                    game_obj.update(self._extract_game_details(raw_game))
                
                games.append(game_obj)
            except:
                continue
        return games
    
    def _extract_game_details(self, raw_game):
        """Extract detailed information from raw game data."""
        details = {}
        
        # Weather info
        basic_info = raw_game.get('basic_info', {})
        if basic_info.get('weather'):
            details['weather'] = str(basic_info.get('weather', ''))
        if basic_info.get('temperature_f'):
            details['temperature'] = int(basic_info.get('temperature_f', 0))
        
        # Umpires
        umpires = raw_game.get('umpires', {})
        if umpires:
            details['umpires'] = {
                'hp': str(umpires.get('HP', '')),
                '1b': str(umpires.get('1B', '')),
                '2b': str(umpires.get('2B', '')),
                '3b': str(umpires.get('3B', '')),
                'lf': str(umpires.get('LF', '')),
                'rf': str(umpires.get('RF', ''))
            }
        
        # Linescore (inning by inning)
        linescore = raw_game.get('linescore', {})
        if linescore:
            details['linescore'] = {
                'away': {
                    'innings': linescore.get('away', {}).get('innings', []),
                    'runs': linescore.get('away', {}).get('R', 0),
                    'hits': linescore.get('away', {}).get('H', 0),
                    'errors': linescore.get('away', {}).get('E', 0)
                },
                'home': {
                    'innings': linescore.get('home', {}).get('innings', []),
                    'runs': linescore.get('home', {}).get('R', 0),
                    'hits': linescore.get('home', {}).get('H', 0),
                    'errors': linescore.get('home', {}).get('E', 0)
                }
            }
        
        # Key plays/moments from play-by-play
        key_plays = []
        for play in raw_game.get('play_by_play', []):
            # Home runs
            if play.get('home_run'):
                key_plays.append({
                    'type': 'home_run',
                    'inning': f"{play.get('half', '').title()} {play.get('inning', '')}",
                    'batter': play.get('batter', ''),
                    'pitcher': play.get('pitcher', ''),
                    'description': play.get('description', ''),
                    'rbi': play.get('rbi', 1)
                })
            # Grand slams
            elif play.get('grand_slam'):
                key_plays.append({
                    'type': 'grand_slam',
                    'inning': f"{play.get('half', '').title()} {play.get('inning', '')}",
                    'batter': play.get('batter', ''),
                    'pitcher': play.get('pitcher', ''),
                    'description': play.get('description', '')
                })
        
        if key_plays:
            details['keyPlays'] = key_plays[:10]  # Limit to 10 most important
        
        # Pitcher decisions
        decisions = raw_game.get('pitcher_decisions', {})
        if decisions:
            details['decisions'] = {
                'winner': str(decisions.get('winning_pitcher', '')),
                'loser': str(decisions.get('losing_pitcher', '')),
                'save': str(decisions.get('save_pitcher', ''))
            }
        
        # Starting lineups
        lineups = raw_game.get('lineups', {})
        if lineups and (lineups.get('away') or lineups.get('home')):
            details['lineups'] = {
                'away': [
                    {
                        'slot': p.get('slot', 0),
                        'name': p.get('name', ''),
                        'playerId': p.get('player_id', ''),
                        'position': p.get('pos', '')
                    }
                    for p in lineups.get('away', [])
                ],
                'home': [
                    {
                        'slot': p.get('slot', 0),
                        'name': p.get('name', ''),
                        'playerId': p.get('player_id', ''),
                        'position': p.get('pos', '')
                    }
                    for p in lineups.get('home', [])
                ]
            }
        
        # Substitutions
        substitutions = raw_game.get('substitutions', [])
        if substitutions:
            details['substitutions'] = [
                {
                    'type': sub.get('type', 'substitution'),
                    'inning': sub.get('inning', 0),
                    'half': sub.get('half', ''),
                    'playerIn': sub.get('player_in', ''),
                    'playerOut': sub.get('player_out', ''),
                    'position': sub.get('pos', ''),
                    'text': sub.get('raw', '') or sub.get('text', '')
                }
                for sub in substitutions
            ]
        
        # Play-by-play (limit to key plays or make it toggleable)
        play_by_play = raw_game.get('play_by_play', [])
        if play_by_play:
            details['playByPlay'] = [
                {
                    'inning': play.get('inning', 0),
                    'half': play.get('half', ''),
                    'batter': play.get('batter', ''),
                    'batterId': play.get('batter_id', ''),
                    'pitcher': play.get('pitcher', ''),
                    'pitcherId': play.get('pitcher_id', ''),
                    'description': play.get('description', ''),
                    'outs': play.get('outs'),
                    'score': play.get('score', ''),
                    'pitchCount': play.get('pitch_count', 0),
                    'battingTeam': play.get('batting_team', ''),
                    'isHomeRun': play.get('home_run', False),
                    'isStrikeout': play.get('strikeout', False),
                    'isWalk': play.get('walk', False)
                }
                for play in play_by_play[:200]  # Limit to prevent huge data
            ]

        return details
    
    def _format_game_length(self, game_length):
        """Format game length from Excel time format to readable string.
        
        Args:
            game_length: Can be a decimal (Excel format), string like "2:39", or empty
            
        Returns:
            str: Formatted time like "2:39" or empty string
        """
        if not game_length or pd.isna(game_length):
            return ""
        
        # If it's already a string in correct format (HH:MM), return it
        if isinstance(game_length, str):
            if ':' in game_length:
                return game_length
            # Try to parse if it's a decimal string
            try:
                game_length = float(game_length)
            except ValueError:
                return game_length
        
        # If it's a decimal (Excel stores time as fraction of a day)
        if isinstance(game_length, (int, float)):
            try:
                # Convert fraction of day to hours
                total_hours = game_length * 24
                hours = int(total_hours)
                minutes = int((total_hours - hours) * 60)
                return f"{hours}:{minutes:02d}"
            except:
                return ""
        
        return str(game_length)
    
    def _serialize_stadiums(self, df):
        """Convert stadiums DataFrame to JSON."""
        if df is None or df.empty:
            return []
        
        stadiums = []
        for _, row in df.iterrows():
            try:
                stadiums.append({
                    "stadium": str(row.get("Stadium", "")),
                    "games": int(row.get("Games", 0)),
                    "firstVisit": str(row.get("First Visit", "")),
                    "lastVisit": str(row.get("Last Visit", "")),
                    "span": str(row.get("Span", "")),
                    "avgAttendance": str(row.get("Avg Attendance", "")),
                    "highAttendance": str(row.get("High Attendance", "")),
                    "lowAttendance": str(row.get("Low Attendance", "")),
                    "homeRunsSeen": int(row.get("Home Runs Seen", 0)) if pd.notna(row.get("Home Runs Seen")) else 0,
                    "hitsSeen": int(row.get("Hits Seen", 0)) if pd.notna(row.get("Hits Seen")) else 0,
                    "strikeoutsSeen": int(row.get("Strikeouts Seen", 0)) if pd.notna(row.get("Strikeouts Seen")) else 0,
                    "teamsSeen": int(row.get("Teams Seen", 0)) if pd.notna(row.get("Teams Seen")) else 0,
                    "homeTeamRecord": str(row.get("Home Team Record", "")),
                })
            except:
                continue
        return stadiums
    
    def _serialize_orioles(self, df):
        """Convert Orioles stadium records to JSON."""
        if df is None or df.empty:
            return []
        
        orioles = []
        for _, row in df.iterrows():
            try:
                orioles.append({
                    "stadium": str(row.get("Stadium", "")),
                    "games": int(row.get("Games", 0)),
                    "record": str(row.get("Orioles Record", "")),
                    "firstVisit": str(row.get("First Visit", "")),
                    "lastVisit": str(row.get("Last Visit", "")),
                    "runsScored": int(row.get("Runs Scored", 0)) if pd.notna(row.get("Runs Scored")) else 0,
                    "runsAllowed": int(row.get("Runs Allowed", 0)) if pd.notna(row.get("Runs Allowed")) else 0,
                    "runDiff": str(row.get("Run Differential", "")),
                    "homeRunsHit": int(row.get("Home Runs Hit", 0)) if pd.notna(row.get("Home Runs Hit")) else 0,
                    "oneRunGames": str(row.get("1-Run Games", "")),
                })
            except:
                continue
        return orioles
    
    def _serialize_debuts(self, debut_rows):
        """Convert MLB debuts to JSON."""
        if not debut_rows:
            return []
        
        debuts = []
        for row in debut_rows:
            try:
                date_str = str(row.get("Date", ""))
                if len(date_str) == 8:
                    formatted_date = f"{date_str[4:6]}/{date_str[6:8]}/{date_str[0:4]}"
                else:
                    formatted_date = date_str
                
                debuts.append({
                    "date": formatted_date,
                    "player": str(row.get("Player", "")),
                    "playerId": str(row.get("PlayerID", "")),
                    "team": str(row.get("Team", "")),
                    "opponent": str(row.get("Opponent", "")),
                    "position": str(row.get("Position", "")),
                    "ab": int(row.get("AB", 0)) if "AB" in row else 0,
                    "h": int(row.get("H", 0)) if "H" in row else 0,
                    "r": int(row.get("R", 0)) if "R" in row else 0,
                    "hr": int(row.get("HR", 0)) if "HR" in row else 0,
                    "rbi": int(row.get("RBI", 0)) if "RBI" in row else 0,
                    "bb": int(row.get("BB", 0)) if "BB" in row else 0,
                    "so": int(row.get("SO", 0)) if "SO" in row else 0,
                    "ip": str(row.get("IP", "")) if "IP" in row else "",
                    "h_p": int(row.get("H_P", 0)) if "H_P" in row else 0,
                    "r_p": int(row.get("R_P", 0)) if "R_P" in row else 0,
                    "er": int(row.get("ER", 0)) if "ER" in row else 0,
                    "bb_p": int(row.get("BB_P", 0)) if "BB_P" in row else 0,
                    "so_p": int(row.get("SO_P", 0)) if "SO_P" in row else 0,
                    "decision": str(row.get("Decision", "")) if "Decision" in row else "",
                    "gameId": str(row.get("GameID", "")),
                })
            except:
                continue
        return debuts
    
    def _serialize_final_games(self, final_rows):
        """Convert final MLB games to JSON."""
        if not final_rows:
            return []
        
        finals = []
        for row in final_rows:
            try:
                date_str = str(row.get("Date", ""))
                if len(date_str) == 8:
                    formatted_date = f"{date_str[4:6]}/{date_str[6:8]}/{date_str[0:4]}"
                else:
                    formatted_date = date_str
                
                finals.append({
                    "date": formatted_date,
                    "player": str(row.get("Player", "")),
                    "playerId": str(row.get("PlayerID", "")),
                    "team": str(row.get("Team", "")),
                    "position": str(row.get("Position", "")),
                    "ab": int(row.get("AB", 0)) if "AB" in row else 0,
                    "h": int(row.get("H", 0)) if "H" in row else 0,
                    "r": int(row.get("R", 0)) if "R" in row else 0,
                    "hr": int(row.get("HR", 0)) if "HR" in row else 0,
                    "rbi": int(row.get("RBI", 0)) if "RBI" in row else 0,
                    "bb": int(row.get("BB", 0)) if "BB" in row else 0,
                    "so": int(row.get("SO", 0)) if "SO" in row else 0,
                    "ip": str(row.get("IP", "")) if "IP" in row else "",
                    "h_p": int(row.get("H_P", 0)) if "H_P" in row else 0,
                    "r_p": int(row.get("R_P", 0)) if "R_P" in row else 0,
                    "er": int(row.get("ER", 0)) if "ER" in row else 0,
                    "bb_p": int(row.get("BB_P", 0)) if "BB_P" in row else 0,
                    "so_p": int(row.get("SO_P", 0)) if "SO_P" in row else 0,
                    "decision": str(row.get("Decision", "")) if "Decision" in row else "",
                    "gameId": str(row.get("GameID", "")),
                })
            except:
                continue
        return finals
    
    def _serialize_signature_hrs(self, df):
        """Convert signature home runs DataFrame to JSON."""
        if df is None or df.empty:
            return []
        
        hrs = []
        for _, row in df.iterrows():
            try:
                date_val = row.get("Date")
                if hasattr(date_val, 'strftime'):
                    date_str = date_val.strftime("%m/%d/%Y")
                else:
                    date_str = str(date_val)
                    if len(date_str) == 8 and date_str.isdigit():
                        date_str = f"{date_str[4:6]}/{date_str[6:8]}/{date_str[0:4]}"
                
                hrs.append({
                    "date": date_str,
                    "player": str(row.get("Player", "")),
                    "team": str(row.get("Team", "")),
                    "opponent": str(row.get("Opponent", "")),
                    "pitcher": str(row.get("Pitcher", "")),
                    "signatureNumber": str(row.get("Signature HR Number", "")),
                    "gameId": str(row.get("GameID", "")),
                })
            except:
                continue
        return hrs
    
    def _serialize_matchup_matrix(self, df):
        """Convert matchup matrix to JSON."""
        if df is None or df.empty:
            return {"teams": [], "matrix": []}
        
        teams = df.index.tolist()
        matrix = []
        
        for team in teams:
            row_data = {"team": team}
            for opponent in teams:
                value = df.loc[team, opponent]
                if value == "X":
                    row_data[opponent] = "X"
                else:
                    row_data[opponent] = int(value) if pd.notna(value) and value != "" else 0
            matrix.append(row_data)
        
        return {"teams": teams, "matrix": matrix}