"""
Situational Hitting Tracker
Analyzes performance with runners in scoring position, 2 outs, bases loaded, etc.
"""

import pandas as pd
from collections import defaultdict
from ..utils.log import debug

class SituationalHittingTracker:
    """Track hitting performance in different game situations."""
    
    def __init__(self):
        # Player situation tracking
        self.player_situations = defaultdict(lambda: {
            "name": "",
            # RISP (Runners in Scoring Position - 2nd or 3rd base)
            "risp_ab": 0,
            "risp_hits": 0,
            "risp_hr": 0,
            "risp_rbi": 0,
            
            # 2 outs
            "two_outs_ab": 0,
            "two_outs_hits": 0,
            "two_outs_hr": 0,
            "two_outs_rbi": 0,
            
            # RISP with 2 outs (most clutch)
            "risp_2out_ab": 0,
            "risp_2out_hits": 0,
            "risp_2out_hr": 0,
            "risp_2out_rbi": 0,
            
            # Bases loaded
            "bases_loaded_ab": 0,
            "bases_loaded_hits": 0,
            "bases_loaded_hr": 0,
            "bases_loaded_grand_slams": 0,
            
            # Late & close situations (7th+ inning, score within 3)
            "late_close_ab": 0,
            "late_close_hits": 0,
            "late_close_hr": 0,
            
            # Ahead/behind/tied
            "ahead_ab": 0,
            "ahead_hits": 0,
            "behind_ab": 0,
            "behind_hits": 0,
            "tied_ab": 0,
            "tied_hits": 0
        })
        
        # Game-level tracking
        self.best_risp_games = []
        self.best_clutch_hits = []
    
    def process_game_situations(self, game):
        """Extract situational data from play-by-play."""
        game_id = game.get("game_id", "")
        basic_info = game.get("basic_info", {})
        # CRITICAL FIX: Use raw_plays which has runners_on_base and score data
        play_by_play = game.get("raw_plays", [])
        
        if not play_by_play:
            return
        
        # CRITICAL FIX: Build name-to-ID mapping from batting lineup
        name_to_id = {}
        for side in ["home", "away"]:
            for player in game.get("batting", {}).get(side, []):
                player_id = player.get("player_id")
                player_name = player.get("name", "")
                if player_id and player_name:
                    # Normalize the name (handle non-breaking spaces)
                    import unicodedata
                    normalized_name = player_name.replace('\u00a0', ' ')
                    normalized_name = unicodedata.normalize('NFKD', normalized_name)
                    name_to_id[normalized_name] = player_id
                    name_to_id[player_name] = player_id  # Keep original too
        
        for play in play_by_play:
            if not isinstance(play, dict):
                continue
            
            # Get batter name and look up ID
            batter_name = play.get("batter", "")
            if not batter_name:
                continue
            
            # Normalize batter name from play-by-play
            import unicodedata
            batter_name_normalized = batter_name.replace('\u00a0', ' ')
            batter_name_normalized = unicodedata.normalize('NFKD', batter_name_normalized)
            
            # Look up player ID
            batter_id = name_to_id.get(batter_name_normalized) or name_to_id.get(batter_name)
            
            if not batter_id:
                continue  # Skip if we can't find the player ID
            
            # Extract play context
            outs = play.get("outs", 0)
            runners = play.get("runners_on_base", "---")
            score = play.get("score", "0-0")
            inning = play.get("inning", 1)
            description = play.get("description", "").lower()
            
            # Initialize player if needed
            if self.player_situations[batter_id]["name"] == "":
                self.player_situations[batter_id]["name"] = batter_name_normalized
            
            # Determine if this is a plate appearance (not a stolen base, etc.)
            is_pa = any(keyword in description for keyword in [
                'single', 'double', 'triple', 'home', 'walk', 'strikeout', 
                'groundout', 'flyball', 'lineout', 'popfly', 'hit by pitch'
            ])
            
            if not is_pa:
                continue
            
            # Determine if ball was put in play for a hit
            is_hit = any(keyword in description for keyword in [
                'single', 'double', 'triple', 'home run', 'homered'
            ])
            
            is_hr = any(keyword in description for keyword in [
                'home run', 'homered', 'grand slam'
            ])
            
            # Parse score to determine ahead/behind/tied
            score_parts = score.split('-')
            if len(score_parts) == 2:
                try:
                    batting_team = play.get("batting_team", "")
                    home_team = basic_info.get("home_team", "")
                    
                    # Determine which score is for batting team
                    if batting_team == home_team:
                        team_score = int(score_parts[1])
                        opp_score = int(score_parts[0])
                    else:
                        team_score = int(score_parts[0])
                        opp_score = int(score_parts[1])
                    
                    score_diff = team_score - opp_score
                except:
                    score_diff = 0
            else:
                score_diff = 0
            
            # Analyze runners situation
            has_runner_2nd = '2' in runners
            has_runner_3rd = '3' in runners
            risp = has_runner_2nd or has_runner_3rd
            bases_loaded = '1' in runners and '2' in runners and '3' in runners
            
            # DEBUG: Print first 5 RISP situations to see what's happening
            if risp and not hasattr(self, '_debug_count'):
                self._debug_count = 0
            if risp and self._debug_count < 5:
                debug(f"RISP situation: runners='{runners}', batter={batter_name_normalized}, is_pa={is_pa}")
                self._debug_count += 1
            
            # Track RISP situations
            if risp:
                self.player_situations[batter_id]["risp_ab"] += 1
                if is_hit:
                    self.player_situations[batter_id]["risp_hits"] += 1
                if is_hr:
                    self.player_situations[batter_id]["risp_hr"] += 1
                # RBI tracking would need additional data
            
            # Track 2-out situations
            if outs == 2:
                self.player_situations[batter_id]["two_outs_ab"] += 1
                if is_hit:
                    self.player_situations[batter_id]["two_outs_hits"] += 1
                if is_hr:
                    self.player_situations[batter_id]["two_outs_hr"] += 1
            
            # Track RISP with 2 outs (most clutch!)
            if risp and outs == 2:
                self.player_situations[batter_id]["risp_2out_ab"] += 1
                if is_hit:
                    self.player_situations[batter_id]["risp_2out_hits"] += 1
                if is_hr:
                    self.player_situations[batter_id]["risp_2out_hr"] += 1
            
            # Track bases loaded
            if bases_loaded:
                self.player_situations[batter_id]["bases_loaded_ab"] += 1
                if is_hit:
                    self.player_situations[batter_id]["bases_loaded_hits"] += 1
                if is_hr or 'grand slam' in description:
                    self.player_situations[batter_id]["bases_loaded_hr"] += 1
                    if 'grand slam' in description:
                        self.player_situations[batter_id]["bases_loaded_grand_slams"] += 1
            
            # Track late & close (7th+ inning, within 3 runs)
            if inning >= 7 and abs(score_diff) <= 3:
                self.player_situations[batter_id]["late_close_ab"] += 1
                if is_hit:
                    self.player_situations[batter_id]["late_close_hits"] += 1
                if is_hr:
                    self.player_situations[batter_id]["late_close_hr"] += 1
            
            # Track ahead/behind/tied
            if score_diff > 0:  # Team is ahead
                self.player_situations[batter_id]["ahead_ab"] += 1
                if is_hit:
                    self.player_situations[batter_id]["ahead_hits"] += 1
            elif score_diff < 0:  # Team is behind
                self.player_situations[batter_id]["behind_ab"] += 1
                if is_hit:
                    self.player_situations[batter_id]["behind_hits"] += 1
            else:  # Tied game
                self.player_situations[batter_id]["tied_ab"] += 1
                if is_hit:
                    self.player_situations[batter_id]["tied_hits"] += 1
    
    def create_risp_dataframe(self, min_ab=5):
        """Create DataFrame of RISP performance."""
        rows = []
        for player_id, stats in self.player_situations.items():
            if stats["risp_ab"] >= min_ab:
                avg = stats["risp_hits"] / stats["risp_ab"] if stats["risp_ab"] > 0 else 0
                row = {
                    "Player ID": player_id,
                    "Name": stats["name"],
                    "RISP AB": stats["risp_ab"],
                    "RISP H": stats["risp_hits"],
                    "RISP AVG": round(avg, 3),
                    "RISP HR": stats["risp_hr"]
                }
                rows.append(row)
        
        df = pd.DataFrame(rows)
        if not df.empty:
            df = df.sort_values("RISP AVG", ascending=False)
        return df
    
    def create_two_out_dataframe(self, min_ab=5):
        """Create DataFrame of 2-out performance."""
        rows = []
        for player_id, stats in self.player_situations.items():
            if stats["two_outs_ab"] >= min_ab:
                avg = stats["two_outs_hits"] / stats["two_outs_ab"] if stats["two_outs_ab"] > 0 else 0
                row = {
                    "Player ID": player_id,
                    "Name": stats["name"],
                    "2-Out AB": stats["two_outs_ab"],
                    "2-Out H": stats["two_outs_hits"],
                    "2-Out AVG": round(avg, 3),
                    "2-Out HR": stats["two_outs_hr"]
                }
                rows.append(row)
        
        df = pd.DataFrame(rows)
        if not df.empty:
            df = df.sort_values("2-Out AVG", ascending=False)
        return df
    
    def create_clutch_situations_dataframe(self, min_ab=3):
        """Create DataFrame of most clutch situations (RISP + 2 outs)."""
        rows = []
        for player_id, stats in self.player_situations.items():
            if stats["risp_2out_ab"] >= min_ab:
                avg = stats["risp_2out_hits"] / stats["risp_2out_ab"] if stats["risp_2out_ab"] > 0 else 0
                row = {
                    "Player ID": player_id,
                    "Name": stats["name"],
                    "RISP+2Out AB": stats["risp_2out_ab"],
                    "RISP+2Out H": stats["risp_2out_hits"],
                    "RISP+2Out AVG": round(avg, 3),
                    "RISP+2Out HR": stats["risp_2out_hr"]
                }
                rows.append(row)
        
        df = pd.DataFrame(rows)
        if not df.empty:
            df = df.sort_values("RISP+2Out AVG", ascending=False)
        return df
    
    def create_bases_loaded_dataframe(self):
        """Create DataFrame of bases loaded HOME RUNS only (Grand Slams)."""
        rows = []
        for player_id, stats in self.player_situations.items():
            # Only include players who hit a home run with bases loaded
            if stats["bases_loaded_hr"] > 0:
                row = {
                    "Player ID": player_id,
                    "Name": stats["name"],
                    "Grand Slams": stats["bases_loaded_grand_slams"]
                }
                rows.append(row)
        
        df = pd.DataFrame(rows)
        if not df.empty:
            df = df.sort_values("Grand Slams", ascending=False)
        return df
    
    def create_late_close_dataframe(self, min_ab=5):
        """Create DataFrame of late & close performance."""
        rows = []
        for player_id, stats in self.player_situations.items():
            if stats["late_close_ab"] >= min_ab:
                avg = stats["late_close_hits"] / stats["late_close_ab"] if stats["late_close_ab"] > 0 else 0
                row = {
                    "Player ID": player_id,
                    "Name": stats["name"],
                    "Late/Close AB": stats["late_close_ab"],
                    "Late/Close H": stats["late_close_hits"],
                    "Late/Close AVG": round(avg, 3),
                    "Late/Close HR": stats["late_close_hr"]
                }
                rows.append(row)
        
        df = pd.DataFrame(rows)
        if not df.empty:
            df = df.sort_values("Late/Close AVG", ascending=False)
        return df
    
    def create_score_splits_dataframe(self, min_ab=10):
        """Create DataFrame showing performance when ahead/behind/tied."""
        rows = []
        for player_id, stats in self.player_situations.items():
            total_ab = stats["ahead_ab"] + stats["behind_ab"] + stats["tied_ab"]
            if total_ab >= min_ab:
                ahead_avg = stats["ahead_hits"] / stats["ahead_ab"] if stats["ahead_ab"] > 0 else 0
                behind_avg = stats["behind_hits"] / stats["behind_ab"] if stats["behind_ab"] > 0 else 0
                tied_avg = stats["tied_hits"] / stats["tied_ab"] if stats["tied_ab"] > 0 else 0
                
                row = {
                    "Player ID": player_id,
                    "Name": stats["name"],
                    "Ahead AB": stats["ahead_ab"],
                    "Ahead AVG": round(ahead_avg, 3),
                    "Behind AB": stats["behind_ab"],
                    "Behind AVG": round(behind_avg, 3),
                    "Tied AB": stats["tied_ab"],
                    "Tied AVG": round(tied_avg, 3)
                }
                rows.append(row)
        
        df = pd.DataFrame(rows)
        return df
    
    def get_summary_stats(self):
        """Return summary statistics."""
        # Count players with significant situational ABs
        risp_count = sum(1 for stats in self.player_situations.values() if stats["risp_ab"] >= 5)
        clutch_count = sum(1 for stats in self.player_situations.values() if stats["risp_2out_ab"] >= 3)
        bases_loaded_count = sum(1 for stats in self.player_situations.values() if stats["bases_loaded_ab"] > 0)
        
        return {
            "players_with_risp_opportunities": risp_count,
            "players_with_clutch_opportunities": clutch_count,
            "players_with_bases_loaded_opportunities": bases_loaded_count,
            "total_players_tracked": len(self.player_situations)
        }