import pandas as pd
from collections import defaultdict
from ..excel.generators import ExcelGeneratorUtils
from ..utils.helpers import standardize_team_code, normalize_name, join_sorted_gameids, unify_team_code, safe_get_int, safe_get_str
from ..utils.stat_utils import StatUtils

class PlayerStatsProcessor:
    """Handle player statistics processing with improved organization and error handling."""
    
    def __init__(self, games):
        self.games = games
    
    def process_all_player_stats(self):
        """Process all player statistics and return DataFrames."""
        print("👥 Processing player statistics...")
        
        # Initialize tracking
        all_players = {}  # player_id -> {name, teams, game_ids, positions}
        players_with_stats = set()  # player_ids who have meaningful stats
        
        # Hitters tracking
        hit_tot = defaultdict(lambda: defaultdict(int))
        hit_team = defaultdict(set)
        hit_games = defaultdict(set)
        
        # Pitchers tracking
        pit_tot = defaultdict(lambda: defaultdict(int))
        pit_team = defaultdict(set)
        pit_games = defaultdict(set)
        
        # Process each game
        for game in self.games:
            self._process_game_stats(game, all_players, players_with_stats, 
                                   hit_tot, hit_team, hit_games, 
                                   pit_tot, pit_team, pit_games)
        
        # Create DataFrames
        hitters = self._create_hitters_dataframe(hit_tot, hit_team, hit_games, players_with_stats)
        pitchers = self._create_pitchers_dataframe(pit_tot, pit_team, pit_games)
        players_without_stats_df = self._create_no_stats_dataframe(all_players, players_with_stats)
        
        print(f"   ✅ Processed {len(hitters)} hitters, {len(pitchers)} pitchers, "
              f"{len(players_without_stats_df)} players without stats, tracking {len(all_players)} total players")
        
        return hitters, pitchers, players_without_stats_df, all_players
    
    def _process_game_stats(self, game, all_players, players_with_stats, 
                           hit_tot, hit_team, hit_games, pit_tot, pit_team, pit_games):
        """Process statistics for a single game."""
        basic_info = game.get("basic_info", {})
        game_id = game.get("game_id", "UNKNOWN")
        name_to_id = {}
        
        # Process batting and pitching stats
        for side in ("home", "away"):
            team_code = unify_team_code(basic_info.get(f"{side}_team_code", ""))
            
            # Process batting stats
            self._process_batting_stats(game, side, team_code, game_id, all_players, 
                                      players_with_stats, hit_tot, hit_team, hit_games, name_to_id)
            
            # Process pitching stats
            self._process_pitching_stats(game, side, team_code, game_id, all_players, 
                                       players_with_stats, pit_tot, pit_team, pit_games)
        
        # Process footer stats (XBH, SB, etc.)
        self._process_footer_stats(game, name_to_id, hit_tot, players_with_stats)
    
    def _process_batting_stats(self, game, side, team_code, game_id, all_players, 
                            players_with_stats, hit_tot, hit_team, hit_games, name_to_id):
        """Process batting statistics for one side of a game."""
        for player in game.get("batting", {}).get(side, []):
            player_id = safe_get_str(player, "player_id", "")
            if not player_id:
                continue

            name = safe_get_str(player, "name", "")
            position = safe_get_str(player, "position", "")
            name_to_id[name] = player_id

            # ✅ Always track player, regardless of stats
            self._track_player(player_id, name, team_code, game_id, position, all_players)

            # Initialize stats if first time seeing this player
            if player_id not in hit_tot:
                hit_tot[player_id]["Name"] = name

            hit_team[player_id].add(team_code)
            if game_id not in hit_games[player_id]:
                hit_games[player_id].add(game_id)
                hit_tot[player_id]["G"] += 1

            # Process individual stats
            has_meaningful_stats = False
            for stat in ("AB", "R", "H", "RBI", "BB", "SO", "PA"):
                value = safe_get_int(player, stat, 0)
                hit_tot[player_id][stat] += value
                if value > 0:
                    has_meaningful_stats = True

            if has_meaningful_stats:
                players_with_stats.add(player_id)
    
    def _process_pitching_stats(self, game, side, team_code, game_id, all_players, 
                               players_with_stats, pit_tot, pit_team, pit_games):
        """Process pitching statistics for one side of a game."""
        basic_info = game.get("basic_info", {})
        
        # Determine if this pitcher is a starter (first in the list)
        pitching_staff = game.get("pitching", {}).get(side, [])
        starter_id = pitching_staff[0].get("player_id") if pitching_staff else None
        
        for pitcher in pitching_staff:
            player_id = safe_get_str(pitcher, "player_id", "")
            if not player_id:
                continue
            
            name = safe_get_str(pitcher, "name", "")
            
            # Track player across all games
            self._track_player(player_id, name, team_code, game_id, "P", all_players)
            
            # Initialize pitcher stats
            if player_id not in pit_tot:
                pit_tot[player_id]["Name"] = name
                pit_tot[player_id]["GS"] = 0
            
            pit_team[player_id].add(team_code)
            pit_games[player_id].add(game_id)
            pit_tot[player_id]["G"] += 1
            
            # Track game starts
            if player_id == starter_id:
                pit_tot[player_id]["GS"] += 1
            
            # Process IP (convert to outs for easier calculation)
            ip = pitcher.get("IP", "0")
            try:
                outs = StatUtils.ip_to_outs(ip)
                if outs is not None:
                    pit_tot[player_id]["Outs"] += outs
            except (ValueError, TypeError):
                pass  # Skip invalid IP values
            
            # Process other pitching stats
            has_meaningful_stats = False
            for stat in ("H", "R", "ER", "BB", "SO", "HR"):
                value = safe_get_int(pitcher, stat, 0)
                pit_tot[player_id][stat] += value
                if value > 0:
                    has_meaningful_stats = True
            
            # Track decisions
            if pitcher.get("win"):
                pit_tot[player_id]["W"] += 1
                has_meaningful_stats = True
            if pitcher.get("loss"):
                pit_tot[player_id]["L"] += 1
                has_meaningful_stats = True
            if pitcher.get("save"):
                pit_tot[player_id]["SV"] += 1
                has_meaningful_stats = True
            
            if has_meaningful_stats or outs > 0:
                players_with_stats.add(player_id)
    
    def _process_footer_stats(self, game, name_to_id, hit_tot, players_with_stats):
        """Process footer statistics (XBH, SB, etc.)."""
        basic_info = game.get("basic_info", {})
        footer_summary = game.get("footer_summary", {})
        
        footer_keys = {
            "HR": ["HR", "Home Runs"],
            "2B": ["2B", "2b", "Doubles"],
            "3B": ["3B", "3b", "Triples"],
            "SB": ["SB", "Stolen Bases", "Baserunning SB"],
            "CS": ["CS", "Caught Stealing", "Baserunning CS"],
            "HBP": ["HBP", "Hit By Pitch"],
            "GIDP": ["GIDP", "Grounded into Double Play"]
        }
        
        normalized_name_to_id = {normalize_name(k): v for k, v in name_to_id.items()}

        for side in ("home", "away"):
            side_data = footer_summary.get(side, {})
            if not isinstance(side_data, dict):
                continue
            
            for stat, keys in footer_keys.items():
                for key in keys:
                    blob = side_data.get(key, "")
                    if not blob:
                        continue
                    
                    # Extract stat counts using utility function
                    for name, count in ExcelGeneratorUtils.extract_stat_counts(blob):
                        normalized = normalize_name(name)
                        normalized_map = {normalize_name(k): v for k, v in name_to_id.items()}
                        player_id = normalized_map.get(normalized)
                        if not player_id:
                            continue
                        
                        if stat not in hit_tot[player_id]:
                            hit_tot[player_id][stat] = 0
                        hit_tot[player_id][stat] += count
                        if count > 0:
                            players_with_stats.add(player_id)
    
    def _track_player(self, player_id, name, team_code, game_id, position, all_players):
        """Track a player across all games."""
        if player_id not in all_players:
            all_players[player_id] = {
                'name': name,
                'teams': set(),
                'game_ids': set(),
                'positions': set()
            }
        
        all_players[player_id]['teams'].add(team_code)
        all_players[player_id]['game_ids'].add(game_id)
        if position:
            all_players[player_id]['positions'].add(position)
    
    def _create_hitters_dataframe(self, hit_tot, hit_team, hit_games, players_with_stats):
        """Create the hitters DataFrame."""
        hitter_rows = []

        for player_id, stats in hit_tot.items():
            if stats["G"] == 0:
                continue

            ab = stats.get("AB", 0)
            hits = stats.get("H", 0)
            avg = round(hits / ab, 3) if ab > 0 else 0.000

            pa = stats.get("PA", 0)
            doubles = stats.get("2B", 0)
            triples = stats.get("3B", 0)
            homers = stats.get("HR", 0)
            singles = hits - doubles - triples - homers
            total_bases = singles + 2 * doubles + 3 * triples + 4 * homers
            xbh = doubles + triples + homers

            obp = ((hits + stats.get("BB", 0) + stats.get("HBP", 0)) / pa) if pa > 0 else 0.000
            slg = (total_bases / ab) if ab > 0 else 0.000
            ops = obp + slg

            hitter_rows.append({
                "Name": stats["Name"],
                "Player ID": player_id,
                "Team": ", ".join(sorted(hit_team.get(player_id, []))),
                "G": stats.get("G", 0),
                "AB": ab,
                "H": hits,
                "AVG": avg,
                "R": stats.get("R", 0),
                "RBI": stats.get("RBI", 0),
                "HR": homers,
                "2B": doubles,
                "3B": triples,
                "SB": stats.get("SB", 0),
                "CS": stats.get("CS", 0),
                "BB": stats.get("BB", 0),
                "HBP": stats.get("HBP", 0),
                "GIDP": stats.get("GIDP", 0),
                "SO": stats.get("SO", 0),
                "PA": pa,
                "TB": total_bases,
                "XBH": xbh,
                "OBP": round(obp, 3),
                "SLG": round(slg, 3),
                "OPS": round(ops, 3),
                "GameIDs": join_sorted_gameids(sorted(hit_games.get(player_id, [])))
            })

        hitters_df = pd.DataFrame(hitter_rows)

        if not hitters_df.empty:
            stat_cols = ["AB", "H", "RBI", "R", "HR", "2B", "3B", "SB", "BB", "SO", "HBP", "CS", "GIDP"]
            hitters_df = hitters_df.loc[~(hitters_df[stat_cols] == 0).all(axis=1)].reset_index(drop=True)
            hitters_df = hitters_df.sort_values("G", ascending=False).reset_index(drop=True)

        return hitters_df
    
    def _create_pitchers_dataframe(self, pit_tot, pit_team, pit_games):
        """Create the pitchers DataFrame."""
        pitcher_rows = []
        
        for player_id, stats in pit_tot.items():
            outs = stats.get("Outs", 0)
            
            # Calculate ERA safely
            er = stats.get("ER", 0)
            era = round(er * 9 / (outs / 3), 2) if outs > 0 else None
            
            # Calculate WHIP (Walks + Hits per Inning Pitched)
            walks = stats.get("BB", 0)
            hits = stats.get("H", 0)
            innings_pitched = outs / 3 if outs > 0 else 0
            whip = round((walks + hits) / innings_pitched, 3) if innings_pitched > 0 else None

            # Convert outs back to baseball IP format
            baseball_ip = StatUtils.outs_to_baseball_ip(outs)
            
            pitcher_rows.append({
                "Name": stats["Name"],
                "Player ID": player_id,
                "Team": ", ".join(sorted(pit_team.get(player_id, []))),
                "G": stats["G"],
                "GS": stats.get("GS", 0),
                "W": stats.get("W", 0),
                "L": stats.get("L", 0),
                "SV": stats.get("SV", 0),
                "IP": baseball_ip,
                "ERA": era,
                "WHIP": whip,
                "H": stats.get("H", 0),
                "R": stats.get("R", 0),
                "ER": stats.get("ER", 0),
                "BB": stats.get("BB", 0),
                "SO": stats.get("SO", 0),
                "HR": stats.get("HR", 0),
                "GameIDs": join_sorted_gameids(sorted(pit_games.get(player_id, [])))
            })
        
        pitchers_df = pd.DataFrame(pitcher_rows).sort_values("IP", ascending=False).reset_index(drop=True)
        return pitchers_df
    
    def _create_no_stats_dataframe(self, all_players, players_with_stats):
        """Create DataFrame for players without meaningful stats."""
        no_stats_rows = []

        for player_id, info in all_players.items():
            if player_id not in players_with_stats:
                no_stats_rows.append({
                    "Name": info['name'],
                    "Player ID": player_id,
                    "Team(s)": ", ".join(sorted([t for t in info['teams'] if t])),
                    "Games": len(info['game_ids']),
                    "Position(s)": ", ".join(sorted(info['positions'])) if info['positions'] else "",
                    "GameIDs": join_sorted_gameids(sorted(info['game_ids']))
                })

        # If there are no such players, return an empty DF with the expected schema.
        columns = ["Name", "Player ID", "Team(s)", "Games", "Position(s)", "GameIDs"]
        df = pd.DataFrame(no_stats_rows, columns=columns)
        if df.empty:
            return df

        return df.sort_values(["Player ID"]).reset_index(drop=True)
