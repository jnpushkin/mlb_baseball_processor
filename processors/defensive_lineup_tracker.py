"""
Defensive Statistics and Lineup Analysis Tracker
Captures putouts, assists, fielding %, lineup positions, substitutions
"""

import pandas as pd
from collections import defaultdict

class DefensiveLineupTracker:
    """Track defensive statistics and lineup information."""
    
    def __init__(self):
        # Defensive stats by player
        self.player_defense = defaultdict(lambda: {
            "name": "",
            "games": 0,
            "putouts": 0,
            "assists": 0,
            "errors": 0,
            "positions": set(),
            "innings_by_position": defaultdict(int)
        })
        
        # Lineup tracking
        self.player_lineup = defaultdict(lambda: {
            "name": "",
            "games": 0,
            "lineup_positions": defaultdict(int),  # How many times in each spot 1-9
            "starter_count": 0,
            "pinch_hit_count": 0,
            "defensive_sub_count": 0
        })
        
        # Substitution tracking
        self.substitutions = []
        
        # Best fielding plays
        self.double_plays = []
        self.triple_plays = []
    
    def process_game_defense_lineup(self, game):
        """Extract defensive and lineup data from a game."""
        game_id = game.get("game_id", "")
        basic_info = game.get("basic_info", {})
        
        # Process batting stats for lineup and defensive positions
        for side in ["home", "away"]:
            for player in game.get("batting", {}).get(side, []):
                player_id = player.get("player_id")
                player_name = player.get("name", "Unknown")
                
                if not player_id:
                    continue
                
                # Update player info
                if self.player_defense[player_id]["name"] == "":
                    self.player_defense[player_id]["name"] = player_name
                if self.player_lineup[player_id]["name"] == "":
                    self.player_lineup[player_id]["name"] = player_name
                
                # Track defensive stats (PO, A, E)
                putouts = player.get("PO", 0)
                assists = player.get("A", 0)
                
                # FIXED: Always count the game for defense tracking, even if PO/A are 0
                # This ensures all players appear in defensive stats
                self.player_defense[player_id]["games"] += 1
                self.player_defense[player_id]["putouts"] += putouts
                self.player_defense[player_id]["assists"] += assists
                
                # Track position
                position = player.get("position", "")
                starter_pos = player.get("starter_pos", "")
                
                if position:
                    self.player_defense[player_id]["positions"].add(position)
                if starter_pos:
                    self.player_defense[player_id]["positions"].add(starter_pos)
                
                # Track lineup information
                lineup_slot = player.get("lineup_slot")
                is_starter = player.get("is_starter", False)
                
                if lineup_slot:
                    self.player_lineup[player_id]["games"] += 1
                    self.player_lineup[player_id]["lineup_positions"][lineup_slot] += 1
                    
                    if is_starter:
                        self.player_lineup[player_id]["starter_count"] += 1
                
                # Track pinch hitting (AB > 0 but not a starter)
                if not is_starter and player.get("AB", 0) > 0:
                    self.player_lineup[player_id]["pinch_hit_count"] += 1
        
        # Process errors from footer
        self.process_error_data(game)
    
    def process_error_data(self, game):
        """Extract error data from footer summary."""
        game_id = game.get("game_id", "")
        footer = game.get("footer_summary", {})
        
        for side in ["home", "away"]:
            error_str = footer.get(side, {}).get("E", "")
            if not error_str:
                continue
            
            # CRITICAL FIX: Replace non-breaking spaces with regular spaces
            import unicodedata
            error_str = error_str.replace('\u00a0', ' ')
            error_str = unicodedata.normalize('NFKD', error_str)
            
            # Parse errors with correct format understanding:
            # "PlayerName" = 1 error
            # "PlayerName (10)" = 1 error (10 is season total)
            # "PlayerName 2 (10)" = 2 errors THIS game (10 is season total)
            import re
            
            # Pattern to match "FirstName LastName [error_count] (season_total)"
            # Examples: 
            #   "Brandon Crawford ()" → 1 error
            #   "Jake Cronenworth (7)" → 1 error (7th of season)
            #   "Anthony Volpe 2 (15)" → 2 errors this game (15th of season)
            pattern = r'([A-Z][a-z]+(?:\s+[A-Z][a-z]+(?:\s+(?:Jr\.|Sr\.|III|II|IV))?)?)\s*(\d+)?\s*(?:\(\d*\))?'
            matches = re.findall(pattern, error_str)
            
            # Map player names to IDs from batting lineup
            name_to_id = {}
            for player in game.get("batting", {}).get(side, []):
                player_id = player.get("player_id")
                player_name = player.get("name", "")
                if player_id and player_name:
                    # Also normalize the name from batting
                    normalized_name = player_name.replace('\u00a0', ' ')
                    normalized_name = unicodedata.normalize('NFKD', normalized_name)
                    name_to_id[normalized_name] = player_id
                    name_to_id[player_name] = player_id  # Keep original too
            
            # Also check pitching for pitcher errors
            for player in game.get("pitching", {}).get(side, []):
                player_id = player.get("player_id")
                player_name = player.get("name", "")
                if player_id and player_name:
                    normalized_name = player_name.replace('\u00a0', ' ')
                    normalized_name = unicodedata.normalize('NFKD', normalized_name)
                    name_to_id[normalized_name] = player_id
                    name_to_id[player_name] = player_id
            
            # Process each error
            for name_match, count_match in matches:
                name = name_match.strip()
                # CRITICAL FIX: count_match is the number BEFORE parentheses (errors THIS game)
                # Empty = 1 error, "2" = 2 errors in this game
                error_count = int(count_match) if count_match else 1
                
                # Find matching player ID
                player_id = name_to_id.get(name)
                
                if player_id:
                    if self.player_defense[player_id]["name"] == "":
                        self.player_defense[player_id]["name"] = name
                    self.player_defense[player_id]["errors"] += error_count
    
    def create_defensive_leaders_dataframe(self, min_games=1):
        """Create DataFrame of defensive leaders."""
        rows = []
        for player_id, stats in self.player_defense.items():
            if stats["games"] >= min_games:
                total_chances = stats["putouts"] + stats["assists"] + stats["errors"]
                
                # Calculate fielding percentage
                if total_chances > 0:
                    fielding_pct = (stats["putouts"] + stats["assists"]) / total_chances
                else:
                    fielding_pct = 1.000 if stats["errors"] == 0 else 0.000
                
                row = {
                    "Player ID": player_id,
                    "Name": stats["name"],
                    "Games": stats["games"],
                    "PO": stats["putouts"],
                    "A": stats["assists"],
                    "E": stats["errors"],
                    "TC": total_chances,
                    "Fielding %": round(fielding_pct, 3),
                    "Positions": ", ".join(sorted(stats["positions"]))
                }
                rows.append(row)
        
        df = pd.DataFrame(rows)
        if not df.empty:
            # Sort by games first (to show most active players), then by total chances
            df = df.sort_values(["Games", "TC"], ascending=[False, False])
        return df
    
    def create_lineup_analysis_dataframe(self, min_games=1):
        """Create DataFrame showing lineup position patterns."""
        rows = []
        for player_id, stats in self.player_lineup.items():
            if stats["games"] >= min_games:
                # Find most common lineup position
                if stats["lineup_positions"]:
                    most_common_spot = max(stats["lineup_positions"].items(), key=lambda x: x[1])
                    most_common_position = most_common_spot[0]
                    times_in_spot = most_common_spot[1]
                else:
                    most_common_position = "N/A"
                    times_in_spot = 0
                
                row = {
                    "Player ID": player_id,
                    "Name": stats["name"],
                    "Games": stats["games"],
                    "Most Common Spot": most_common_position,
                    "Times in Spot": times_in_spot,
                    "Pinch Hits": stats["pinch_hit_count"]
                }
                rows.append(row)
        
        df = pd.DataFrame(rows)
        if not df.empty:
            df = df.sort_values("Games", ascending=False)
        return df
    
    def create_lineup_position_matrix(self):
        """Create a matrix showing which players bat in which lineup positions."""
        # Collect all players and positions
        player_names = []
        position_data = []
        
        for player_id, stats in self.player_lineup.items():
            if stats["games"] >= 1:  # FIXED: Show all players, not just those with 3+ games
                player_names.append(stats["name"])
                
                # Create row with count for each lineup position 1-9
                row = {}
                for pos in range(1, 10):
                    row[f"#{pos}"] = stats["lineup_positions"].get(pos, 0)
                position_data.append(row)
        
        if position_data:
            df = pd.DataFrame(position_data, index=player_names)
            # Sort by total games (sum across all positions)
            df['Total'] = df.sum(axis=1)
            df = df.sort_values('Total', ascending=False)
            df = df.drop('Total', axis=1)
            return df
        else:
            return pd.DataFrame()
    
    def get_defensive_specialists(self):
        """Identify defensive specialists (high PO+A, low AB)."""
        specialists = []
        for player_id, def_stats in self.player_defense.items():
            if def_stats["games"] >= 3:
                total_chances = def_stats["putouts"] + def_stats["assists"]
                if total_chances > 10:  # Minimum threshold
                    specialists.append({
                        "player_id": player_id,
                        "name": def_stats["name"],
                        "putouts": def_stats["putouts"],
                        "assists": def_stats["assists"],
                        "total_chances": total_chances,
                        "positions": ", ".join(sorted(def_stats["positions"]))
                    })
        
        specialists_sorted = sorted(specialists, key=lambda x: x["total_chances"], reverse=True)
        return specialists_sorted[:10]
    
    def get_lineup_versatility_leaders(self):
        """Find players who batted in the most different lineup positions."""
        versatile = []
        for player_id, stats in self.player_lineup.items():
            versatility = len(stats["lineup_positions"])
            if versatility > 1:  # Batted in multiple spots
                versatile.append({
                    "player_id": player_id,
                    "name": stats["name"],
                    "lineup_positions_used": versatility,
                    "games": stats["games"],
                    "positions": dict(stats["lineup_positions"])
                })
        
        versatile_sorted = sorted(versatile, key=lambda x: x["lineup_positions_used"], reverse=True)
        return versatile_sorted[:10]
    
    def get_summary_stats(self):
        """Return summary statistics."""
        total_putouts = sum(stats["putouts"] for stats in self.player_defense.values())
        total_assists = sum(stats["assists"] for stats in self.player_defense.values())
        total_errors = sum(stats["errors"] for stats in self.player_defense.values())
        
        defensive_specialists = self.get_defensive_specialists()
        lineup_versatility = self.get_lineup_versatility_leaders()
        
        return {
            "total_putouts": total_putouts,
            "total_assists": total_assists,
            "total_errors": total_errors,
            "defensive_specialists": defensive_specialists[:5],
            "lineup_versatility_leaders": lineup_versatility[:5],
            "players_tracked": len(self.player_defense)
        }
