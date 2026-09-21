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
        from ..utils.event_model import normalize_events

        for play in normalize_events(game):
            if not play['isAB'] or not play['batterId']:
                continue
            stats = self.player_situations[play['batterId']]
            stats['name'] = play['batter']
            bases, outs, diff = play['basesBefore'], play['outsBefore'], play['scoreDiff']
            risp = bases is not None and any(b in bases for b in (2, 3))
            situations = []
            if risp:
                situations.append('risp')
            if outs == 2:
                situations.append('two_outs')
            if risp and outs == 2:
                situations.append('risp_2out')
            if bases == [1, 2, 3]:
                situations.append('bases_loaded')
                if play['isHomeRun']:
                    stats['bases_loaded_grand_slams'] += 1
            if play['inning'] >= 7 and diff is not None and abs(diff) <= 3:
                situations.append('late_close')
            for prefix in situations:
                stats[prefix + '_ab'] += 1
                stats[prefix + '_hits'] += int(play['isHit'])
                stats[prefix + '_hr'] += int(play['isHomeRun'])
            if diff is not None:
                prefix = 'ahead' if diff > 0 else 'behind' if diff < 0 else 'tied'
                stats[prefix + '_ab'] += 1
                stats[prefix + '_hits'] += int(play['isHit'])

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
        """Create DataFrame of bases loaded home runs (grand slams)."""
        rows = []
        for player_id, stats in self.player_situations.items():
            # Only include players who hit a home run with bases loaded
            if stats["bases_loaded_hr"] > 0:
                grand_slams = max(stats["bases_loaded_grand_slams"], stats["bases_loaded_hr"])
                row = {
                    "Player ID": player_id,
                    "Name": stats["name"],
                    "Grand Slams": grand_slams
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
