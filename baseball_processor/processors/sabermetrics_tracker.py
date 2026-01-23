"""
Sabermetrics Tracker
Captures WPA (Win Probability Added), aLI (Leverage Index), RE24, and other advanced stats
"""

import pandas as pd
from collections import defaultdict

class SabermetricsTracker:
    """Track advanced sabermetric statistics."""
    
    def __init__(self):
        # WPA (Win Probability Added) tracking
        self.highest_wpa_game = []  # Single game performances
        self.lowest_wpa_game = []
        self.highest_wpa_cumulative = []  # Career totals
        
        # Leverage Index tracking
        self.highest_ali_games = []  # Highest pressure situations
        
        # RE24 (Run Expectancy) tracking
        self.highest_re24_games = []
        
        # Player cumulative stats
        self.player_wpa = defaultdict(lambda: {
            "name": "",
            "total_wpa": 0.0,
            "games": 0,
            "positive_wpa": 0.0,
            "negative_wpa": 0.0,
            "best_game": None,
            "worst_game": None
        })
        
        self.player_ali = defaultdict(lambda: {
            "name": "",
            "total_ali": 0.0,
            "games": 0,
            "clutch_situations": 0
        })
        
        self.player_re24 = defaultdict(lambda: {
            "name": "",
            "total_re24": 0.0,
            "games": 0
        })
        
    def process_player_sabermetrics(self, game):
        """Extract sabermetric data from batting stats."""
        game_id = game.get("game_id", "")
        basic_info = game.get("basic_info", {})
        date = basic_info.get("date_yyyymmdd", "")
        
        for side in ["home", "away"]:
            team_code = basic_info.get(f"{side}_team_code", "")
            
            for player in game.get("batting", {}).get(side, []):
                player_id = player.get("player_id")
                player_name = player.get("name", "Unknown")
                
                if not player_id:
                    continue
                
                # Extract WPA stats
                wpa = self._safe_float(player.get("WPA", 0))
                wpa_plus = self._safe_float(player.get("WPA+", 0))
                wpa_minus = self._safe_float(player.get("WPA-", 0))
                
                # Extract aLI stats
                ali = self._safe_float(player.get("aLI", 0))
                acli = self._safe_float(player.get("acLI", 0))
                
                # Extract RE24
                re24 = self._safe_float(player.get("RE24", 0))
                
                # Update player WPA tracking
                if wpa != 0:
                    self.player_wpa[player_id]["name"] = player_name
                    self.player_wpa[player_id]["total_wpa"] += wpa
                    self.player_wpa[player_id]["games"] += 1
                    self.player_wpa[player_id]["positive_wpa"] += wpa_plus
                    self.player_wpa[player_id]["negative_wpa"] += wpa_minus
                    
                    # Track best/worst single games
                    best_game = self.player_wpa[player_id]["best_game"]
                    if best_game is None or wpa > best_game["wpa"]:
                        self.player_wpa[player_id]["best_game"] = {
                            "wpa": wpa,
                            "game_id": game_id,
                            "date": date,
                            "team": team_code,
                            "opponent": basic_info.get("away_team_code" if side == "home" else "home_team_code", "")
                        }
                    
                    worst_game = self.player_wpa[player_id]["worst_game"]
                    if worst_game is None or wpa < worst_game["wpa"]:
                        self.player_wpa[player_id]["worst_game"] = {
                            "wpa": wpa,
                            "game_id": game_id,
                            "date": date,
                            "team": team_code,
                            "opponent": basic_info.get("away_team_code" if side == "home" else "home_team_code", "")
                        }
                
                # Update aLI tracking
                if ali > 0:
                    self.player_ali[player_id]["name"] = player_name
                    self.player_ali[player_id]["total_ali"] += ali
                    self.player_ali[player_id]["games"] += 1
                    
                    # Count high-leverage situations (aLI > 1.5)
                    if ali > 1.5:
                        self.player_ali[player_id]["clutch_situations"] += 1
                
                # Update RE24 tracking
                if re24 != 0:
                    self.player_re24[player_id]["name"] = player_name
                    self.player_re24[player_id]["total_re24"] += re24
                    self.player_re24[player_id]["games"] += 1
    
    def get_wpa_leaders(self, top_n=10):
        """Get top WPA performers."""
        players = []
        for player_id, stats in self.player_wpa.items():
            if stats["games"] > 0:
                players.append({
                    "player_id": player_id,
                    "name": stats["name"],
                    "total_wpa": stats["total_wpa"],
                    "games": stats["games"],
                    "avg_wpa": stats["total_wpa"] / stats["games"],
                    "positive_wpa": stats["positive_wpa"],
                    "negative_wpa": stats["negative_wpa"],
                    "best_game_wpa": stats["best_game"]["wpa"] if stats["best_game"] else 0,
                    "best_game_id": stats["best_game"]["game_id"] if stats["best_game"] else "",
                    "worst_game_wpa": stats["worst_game"]["wpa"] if stats["worst_game"] else 0,
                    "worst_game_id": stats["worst_game"]["game_id"] if stats["worst_game"] else ""
                })
        
        # Sort by total WPA
        players_sorted = sorted(players, key=lambda x: x["total_wpa"], reverse=True)
        return players_sorted[:top_n]
    
    def get_clutch_performers(self, top_n=10):
        """Get players who performed in highest leverage situations."""
        players = []
        for player_id, stats in self.player_ali.items():
            if stats["games"] > 0:
                players.append({
                    "player_id": player_id,
                    "name": stats["name"],
                    "total_ali": stats["total_ali"],
                    "avg_ali": stats["total_ali"] / stats["games"],
                    "clutch_situations": stats["clutch_situations"],
                    "games": stats["games"]
                })
        
        # Sort by average leverage index
        players_sorted = sorted(players, key=lambda x: x["avg_ali"], reverse=True)
        return players_sorted[:top_n]
    
    def get_re24_leaders(self, top_n=10):
        """Get top RE24 performers."""
        players = []
        for player_id, stats in self.player_re24.items():
            if stats["games"] > 0:
                players.append({
                    "player_id": player_id,
                    "name": stats["name"],
                    "total_re24": stats["total_re24"],
                    "games": stats["games"],
                    "avg_re24": stats["total_re24"] / stats["games"]
                })
        
        # Sort by total RE24
        players_sorted = sorted(players, key=lambda x: x["total_re24"], reverse=True)
        return players_sorted[:top_n]
    
    def get_most_clutch_single_game(self):
        """Find the single most clutch performance (highest WPA in a game)."""
        best_game = None
        for player_id, stats in self.player_wpa.items():
            if stats["best_game"]:
                if best_game is None or stats["best_game"]["wpa"] > best_game["wpa"]:
                    best_game = {
                        "player_id": player_id,
                        "name": stats["name"],
                        "wpa": stats["best_game"]["wpa"],
                        "game_id": stats["best_game"]["game_id"],
                        "date": stats["best_game"]["date"],
                        "team": stats["best_game"]["team"],
                        "opponent": stats["best_game"]["opponent"]
                    }
        return best_game
    
    def get_summary_stats(self):
        """Return summary statistics."""
        wpa_leaders = self.get_wpa_leaders(5)
        clutch_performers = self.get_clutch_performers(5)
        re24_leaders = self.get_re24_leaders(5)
        most_clutch_game = self.get_most_clutch_single_game()
        
        return {
            "wpa_leaders": wpa_leaders,
            "clutch_performers": clutch_performers,
            "re24_leaders": re24_leaders,
            "most_clutch_single_game": most_clutch_game,
            "total_players_tracked": len(self.player_wpa)
        }
    
    def create_wpa_dataframe(self):
        """Create a DataFrame with all WPA stats."""
        rows = []
        for player_id, stats in self.player_wpa.items():
            if stats["games"] > 0:
                row = {
                    "Player ID": player_id,
                    "Name": stats["name"],
                    "Games": stats["games"],
                    "Total WPA": round(stats["total_wpa"], 3),
                    "Avg WPA": round(stats["total_wpa"] / stats["games"], 3),
                    "Positive WPA": round(stats["positive_wpa"], 3),
                    "Negative WPA": round(stats["negative_wpa"], 3),
                    "Best Game WPA": round(stats["best_game"]["wpa"], 3) if stats["best_game"] else 0,
                    "Best Game ID": stats["best_game"]["game_id"] if stats["best_game"] else "",
                    "Worst Game WPA": round(stats["worst_game"]["wpa"], 3) if stats["worst_game"] else 0,
                    "Worst Game ID": stats["worst_game"]["game_id"] if stats["worst_game"] else ""
                }
                rows.append(row)
        
        df = pd.DataFrame(rows)
        if not df.empty:
            df = df.sort_values("Total WPA", ascending=False)
        return df
    
    def create_clutch_dataframe(self):
        """Create a DataFrame with leverage index stats."""
        rows = []
        for player_id, stats in self.player_ali.items():
            if stats["games"] > 0:
                row = {
                    "Player ID": player_id,
                    "Name": stats["name"],
                    "Games": stats["games"],
                    "Total aLI": round(stats["total_ali"], 2),
                    "Avg aLI": round(stats["total_ali"] / stats["games"], 2),
                    "High Leverage PA": stats["clutch_situations"]
                }
                rows.append(row)
        
        df = pd.DataFrame(rows)
        if not df.empty:
            df = df.sort_values("Avg aLI", ascending=False)
        return df
    
    def _safe_float(self, value):
        """Safely convert value to float."""
        try:
            if isinstance(value, str):
                # Handle percentage strings like "0.18%"
                value = value.replace('%', '')
            return float(value)
        except (ValueError, TypeError):
            return 0.0
