"""
Defensive Statistics and Lineup Analysis Tracker
Captures putouts, assists, fielding %, lineup positions, substitutions
"""

import re
import unicodedata
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

    @staticmethod
    def _to_int(value):
        try:
            return int(value or 0)
        except (TypeError, ValueError):
            return 0

    @staticmethod
    def _normalize_text(value):
        text = str(value or "").replace('\u00a0', ' ')
        text = unicodedata.normalize('NFKD', text)
        return re.sub(r'\s+', ' ', text).strip()

    def _side_has_error_footer(self, game, side):
        return bool((game.get("footer_summary", {}).get(side, {}) or {}).get("E"))

    def _build_name_to_player(self, game, side):
        name_to_player = {}
        for section in ("batting", "pitching"):
            for player in game.get(section, {}).get(side, []) or []:
                player_id = player.get("player_id")
                player_name = player.get("name", "")
                if not player_id or not player_name:
                    continue
                normalized_name = self._normalize_text(player_name)
                if normalized_name:
                    name_to_player[normalized_name] = (player_id, normalized_name)
        return name_to_player

    def _iter_known_error_entries(self, error_str, name_to_player):
        entries = []
        used_spans = []
        for name, (player_id, display_name) in sorted(
            name_to_player.items(),
            key=lambda item: len(item[0]),
            reverse=True,
        ):
            pattern = re.compile(
                rf'(?<!\w){re.escape(name)}\s*(?P<count>\d+)?\s*(?:\(\d*\))?',
                re.IGNORECASE,
            )
            for match in pattern.finditer(error_str):
                span = match.span()
                if any(span[0] < used[1] and used[0] < span[1] for used in used_spans):
                    continue
                count_match = match.group('count')
                error_count = self._to_int(count_match) if count_match else 1
                entries.append((span[0], player_id, display_name, error_count))
                used_spans.append(span)
        return sorted(entries, key=lambda entry: entry[0])
    
    def process_game_defense_lineup(self, game):
        """Extract defensive and lineup data from a game."""
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
                putouts = self._to_int(player.get("PO", 0))
                assists = self._to_int(player.get("A", 0))
                
                # FIXED: Always count the game for defense tracking, even if PO/A are 0
                # This ensures all players appear in defensive stats
                self.player_defense[player_id]["games"] += 1
                self.player_defense[player_id]["putouts"] += putouts
                self.player_defense[player_id]["assists"] += assists
                if not self._side_has_error_footer(game, side):
                    self.player_defense[player_id]["errors"] += self._to_int(player.get("E", 0))
                
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
        self.process_play_error_data(game)
    
    def process_error_data(self, game):
        """Extract error data from footer summary."""
        footer = game.get("footer_summary", {})
        
        for side in ["home", "away"]:
            error_str = footer.get(side, {}).get("E", "")
            if not error_str:
                continue
            
            error_str = self._normalize_text(error_str)
            name_to_player = self._build_name_to_player(game, side)
            
            # Process each error
            for _, player_id, name, error_count in self._iter_known_error_entries(error_str, name_to_player):
                if player_id:
                    if self.player_defense[player_id]["name"] == "":
                        self.player_defense[player_id]["name"] = name
                    self.player_defense[player_id]["errors"] += error_count

    def process_play_error_data(self, game):
        """Backfill individual API errors from play text for older cached games."""
        target_sides = []
        for side in ["home", "away"]:
            if self._side_has_error_footer(game, side):
                continue
            row_error_total = sum(
                self._to_int(player.get("E", 0))
                for player in game.get("batting", {}).get(side, []) or []
            )
            if row_error_total:
                continue
            line = game.get("linescore", {}).get(side, {}) or {}
            team_errors = self._to_int(line.get("E", line.get("errors", 0)))
            if team_errors:
                target_sides.append(side)

        if not target_sides:
            return

        basic = game.get("basic_info", {}) or {}
        side_by_code = {
            basic.get("home_team_code"): "home",
            basic.get("away_team_code"): "away",
        }
        names_by_side = {side: self._build_name_to_player(game, side) for side in target_sides}
        credited = set()

        for play in game.get("play_by_play", []) or []:
            description = self._normalize_text(play.get("description", ""))
            if "error by" not in description.lower():
                continue

            side = side_by_code.get(play.get("pitching_team"))
            if not side:
                half = str(play.get("half", "")).lower()
                side = "home" if half == "top" else "away" if half == "bottom" else ""
            if side not in names_by_side:
                continue

            for name, (player_id, display_name) in sorted(
                names_by_side[side].items(),
                key=lambda item: len(item[0]),
                reverse=True,
            ):
                pattern = re.compile(
                    rf'\berror by\b[^.;]*?(?<!\w){re.escape(name)}(?!\w)',
                    re.IGNORECASE,
                )
                if not pattern.search(description):
                    continue
                key = (id(play), player_id)
                if key in credited:
                    continue
                if self.player_defense[player_id]["name"] == "":
                    self.player_defense[player_id]["name"] = display_name
                self.player_defense[player_id]["errors"] += 1
                credited.add(key)
    
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
