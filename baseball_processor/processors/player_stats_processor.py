import pandas as pd
from collections import defaultdict
from ..excel.generators import ExcelGeneratorUtils
from ..utils.helpers import standardize_team_code, normalize_name, join_sorted_gameids, unify_team_code, safe_get_int, safe_get_str
from ..utils.stat_utils import StatUtils, extract_extra_batting_stats
from .base_processor import BaseProcessor


class PlayerStatsProcessor(BaseProcessor):
    """Handle player statistics processing with improved organization and error handling."""

    # Game type mapping
    GAME_TYPES = ['spring', 'regular', 'postseason']

    def __init__(self, games):
        super().__init__(games)

    def _get_game_type(self, game):
        """Get normalized game type from game data."""
        game_type = game.get("basic_info", {}).get("game_type", "regular")
        # Normalize to our standard types
        if game_type in ("spring", "spring_training"):
            return "spring"
        elif game_type in ("postseason", "playoff", "P"):
            return "postseason"
        else:
            return "regular"

    def process_all_player_stats(self):
        """Process all player statistics and return DataFrames."""
        print("👥 Processing player statistics...")

        # Initialize tracking
        all_players = {}  # player_id -> {name, teams, game_ids, positions}
        players_with_stats = set()  # player_ids who have meaningful stats

        # Hitters tracking - total and per game type
        hit_tot = defaultdict(lambda: defaultdict(int))
        hit_team = defaultdict(set)
        hit_games = defaultdict(set)
        # Per game type tracking for hitters
        hit_by_type = {gt: defaultdict(lambda: defaultdict(int)) for gt in self.GAME_TYPES}
        hit_games_by_type = {gt: defaultdict(set) for gt in self.GAME_TYPES}
        hit_team_by_type = {gt: defaultdict(set) for gt in self.GAME_TYPES}

        # Pitchers tracking - total and per game type
        pit_tot = defaultdict(lambda: defaultdict(int))
        pit_team = defaultdict(set)
        pit_games = defaultdict(set)
        # Per game type tracking for pitchers
        pit_by_type = {gt: defaultdict(lambda: defaultdict(int)) for gt in self.GAME_TYPES}
        pit_games_by_type = {gt: defaultdict(set) for gt in self.GAME_TYPES}
        pit_team_by_type = {gt: defaultdict(set) for gt in self.GAME_TYPES}

        # Process each game
        for game in self.games:
            game_type = self._get_game_type(game)
            self._process_game_stats(game, all_players, players_with_stats,
                                   hit_tot, hit_team, hit_games,
                                   pit_tot, pit_team, pit_games,
                                   hit_by_type, hit_games_by_type, hit_team_by_type,
                                   pit_by_type, pit_games_by_type, pit_team_by_type,
                                   game_type)

        # Create DataFrames
        hitters = self._create_hitters_dataframe(hit_tot, hit_team, hit_games, players_with_stats,
                                                  hit_by_type, hit_games_by_type, hit_team_by_type)
        pitchers = self._create_pitchers_dataframe(pit_tot, pit_team, pit_games,
                                                    pit_by_type, pit_games_by_type, pit_team_by_type)
        players_without_stats_df = self._create_no_stats_dataframe(all_players, players_with_stats)

        print(f"   ✅ Processed {len(hitters)} hitters, {len(pitchers)} pitchers, "
              f"{len(players_without_stats_df)} players without stats, tracking {len(all_players)} total players")

        return hitters, pitchers, players_without_stats_df, all_players
    
    def _process_game_stats(self, game, all_players, players_with_stats,
                           hit_tot, hit_team, hit_games, pit_tot, pit_team, pit_games,
                           hit_by_type, hit_games_by_type, hit_team_by_type,
                           pit_by_type, pit_games_by_type, pit_team_by_type,
                           game_type):
        """Process statistics for a single game."""
        basic_info = game.get("basic_info", {})
        game_id = game.get("game_id", "UNKNOWN")
        name_to_id = {}

        # Precompute play-by-play extras once per game; both _process_batting_stats
        # (which credits them per-player) and the footer-skip decision below
        # depend on it.
        pbp_extras = extract_extra_batting_stats(game)
        pbp_has_xbh = any(
            (s.get('HR') or 0) or (s.get('2B') or 0) or (s.get('3B') or 0)
            or (s.get('SB') or 0) or (s.get('CS') or 0)
            or (s.get('HBP') or 0) or (s.get('GIDP') or 0)
            for s in pbp_extras.values()
        )

        # Process batting and pitching stats
        for side in ("home", "away"):
            team_code = unify_team_code(basic_info.get(f"{side}_team_code", ""))

            # Process batting stats
            self._process_batting_stats(game, side, team_code, game_id, all_players,
                                      players_with_stats, hit_tot, hit_team, hit_games, name_to_id,
                                      hit_by_type, hit_games_by_type, hit_team_by_type, game_type,
                                      pbp_extras=pbp_extras)

            # Process pitching stats
            self._process_pitching_stats(game, side, team_code, game_id, all_players,
                                       players_with_stats, pit_tot, pit_team, pit_games,
                                       pit_by_type, pit_games_by_type, pit_team_by_type, game_type)

        # Footer-summary fallback for extra-base stats — skipped when the
        # play-by-play already supplied them (otherwise we'd double-count
        # 2B/3B/SB/etc. for BREF games, which have both sources populated).
        if not pbp_has_xbh:
            self._process_footer_stats(game, name_to_id, hit_tot, players_with_stats,
                                       hit_by_type, game_type)
    
    def _process_batting_stats(self, game, side, team_code, game_id, all_players,
                            players_with_stats, hit_tot, hit_team, hit_games, name_to_id,
                            hit_by_type, hit_games_by_type, hit_team_by_type, game_type,
                            pbp_extras=None):
        """Process batting statistics for one side of a game."""
        if pbp_extras is None:
            pbp_extras = extract_extra_batting_stats(game)

        for player in game.get("batting", {}).get(side, []):
            player_id = safe_get_str(player, "player_id", "")
            if not player_id:
                continue

            name = safe_get_str(player, "name", "")
            position = safe_get_str(player, "position", "")
            name_to_id[name] = player_id

            # ✅ Always track player, regardless of stats
            self._track_player(player_id, name, team_code, game_id, position, all_players)

            # BREF box scores list relief pitchers in the batting table even
            # when they never came to the plate (the row exists for the
            # substitution record). Skip them as hitters — otherwise the
            # Hitters tab fills up with pitchers showing G>0 and zeros across
            # every batting column. A real two-way appearance always has PA>0.
            if position == "P" and safe_get_int(player, "PA", 0) == 0 and safe_get_int(player, "AB", 0) == 0:
                continue

            # Initialize stats if first time seeing this player
            if player_id not in hit_tot:
                hit_tot[player_id]["Name"] = name
            if player_id not in hit_by_type[game_type]:
                hit_by_type[game_type][player_id]["Name"] = name

            hit_team[player_id].add(team_code)
            hit_team_by_type[game_type][player_id].add(team_code)

            # Track total games
            if game_id not in hit_games[player_id]:
                hit_games[player_id].add(game_id)
                hit_tot[player_id]["G"] += 1

            # Track games by type
            if game_id not in hit_games_by_type[game_type][player_id]:
                hit_games_by_type[game_type][player_id].add(game_id)
                hit_by_type[game_type][player_id]["G"] += 1

            # Process individual stats
            has_meaningful_stats = False
            for stat in ("AB", "R", "H", "RBI", "BB", "SO", "PA"):
                value = safe_get_int(player, stat, 0)
                hit_tot[player_id][stat] += value
                hit_by_type[game_type][player_id][stat] += value
                if value > 0:
                    has_meaningful_stats = True

            # Process extra-base hit stats. Prefer play-by-play counts (the
            # complete source for BREF games) and fall back to the per-player
            # batting row (MLB API populates these directly there).
            extras = pbp_extras.get(player_id, {}) or {}
            pbp_has_xbh = bool(extras.get('HR') or extras.get('2B') or extras.get('3B'))
            for stat in ("HR", "2B", "3B", "SB", "CS", "HBP", "GIDP", "GDP"):
                if pbp_has_xbh and stat in extras:
                    value = int(extras.get(stat, 0))
                elif stat == 'GDP':
                    value = safe_get_int(player, stat, 0)
                else:
                    value = int(extras.get(stat, 0)) if extras.get(stat) else safe_get_int(player, stat, 0)
                if value > 0:
                    stat_key = "GIDP" if stat == "GDP" else stat
                    hit_tot[player_id][stat_key] += value
                    hit_by_type[game_type][player_id][stat_key] += value
                    has_meaningful_stats = True

            if has_meaningful_stats and game_type in ('regular', 'postseason'):
                players_with_stats.add(player_id)

    def _process_pitching_stats(self, game, side, team_code, game_id, all_players,
                               players_with_stats, pit_tot, pit_team, pit_games,
                               pit_by_type, pit_games_by_type, pit_team_by_type, game_type):
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

            # Initialize pitcher stats (total)
            if player_id not in pit_tot:
                pit_tot[player_id]["Name"] = name
                pit_tot[player_id]["GS"] = 0

            # Initialize pitcher stats (by type)
            if player_id not in pit_by_type[game_type]:
                pit_by_type[game_type][player_id]["Name"] = name
                pit_by_type[game_type][player_id]["GS"] = 0

            pit_team[player_id].add(team_code)
            pit_team_by_type[game_type][player_id].add(team_code)
            pit_games[player_id].add(game_id)
            pit_games_by_type[game_type][player_id].add(game_id)
            pit_tot[player_id]["G"] += 1
            pit_by_type[game_type][player_id]["G"] += 1

            # Track game starts
            if player_id == starter_id:
                pit_tot[player_id]["GS"] += 1
                pit_by_type[game_type][player_id]["GS"] += 1

            # Process IP (convert to outs for easier calculation)
            ip = pitcher.get("IP", "0")
            try:
                outs = StatUtils.ip_to_outs(ip)
                if outs is not None:
                    pit_tot[player_id]["Outs"] += outs
                    pit_by_type[game_type][player_id]["Outs"] += outs
            except (ValueError, TypeError):
                outs = 0

            # Process other pitching stats
            has_meaningful_stats = False
            for stat in ("H", "R", "ER", "BB", "SO", "HR"):
                value = safe_get_int(pitcher, stat, 0)
                pit_tot[player_id][stat] += value
                pit_by_type[game_type][player_id][stat] += value
                if value > 0:
                    has_meaningful_stats = True

            # Track decisions
            if pitcher.get("win"):
                pit_tot[player_id]["W"] += 1
                pit_by_type[game_type][player_id]["W"] += 1
                has_meaningful_stats = True
            if pitcher.get("loss"):
                pit_tot[player_id]["L"] += 1
                pit_by_type[game_type][player_id]["L"] += 1
                has_meaningful_stats = True
            if pitcher.get("save"):
                pit_tot[player_id]["SV"] += 1
                pit_by_type[game_type][player_id]["SV"] += 1
                has_meaningful_stats = True

            if (has_meaningful_stats or outs > 0) and game_type in ('regular', 'postseason'):
                players_with_stats.add(player_id)
    
    def _process_footer_stats(self, game, name_to_id, hit_tot, players_with_stats,
                               hit_by_type, game_type):
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

                        # Also track by game type
                        if stat not in hit_by_type[game_type][player_id]:
                            hit_by_type[game_type][player_id][stat] = 0
                        hit_by_type[game_type][player_id][stat] += count

                        if count > 0 and game_type in ('regular', 'postseason'):
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
    
    def _create_hitters_dataframe(self, hit_tot, hit_team, hit_games, players_with_stats,
                                    hit_by_type, hit_games_by_type, hit_team_by_type):
        """Create the hitters DataFrame with per-game-type breakdowns."""
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

            row = {
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
            }

            # Add per-game-type stats
            for gt in self.GAME_TYPES:
                gt_stats = hit_by_type[gt].get(player_id, {})
                gt_ab = gt_stats.get("AB", 0)
                gt_hits = gt_stats.get("H", 0)
                gt_avg = round(gt_hits / gt_ab, 3) if gt_ab > 0 else 0.000
                gt_doubles = gt_stats.get("2B", 0)
                gt_triples = gt_stats.get("3B", 0)
                gt_homers = gt_stats.get("HR", 0)
                gt_pa = gt_stats.get("PA", 0)
                gt_teams = hit_team_by_type[gt].get(player_id, set())

                row[f"{gt}_G"] = gt_stats.get("G", 0)
                row[f"{gt}_AB"] = gt_ab
                row[f"{gt}_PA"] = gt_pa
                row[f"{gt}_H"] = gt_hits
                row[f"{gt}_AVG"] = gt_avg
                row[f"{gt}_R"] = gt_stats.get("R", 0)
                row[f"{gt}_RBI"] = gt_stats.get("RBI", 0)
                row[f"{gt}_HR"] = gt_homers
                row[f"{gt}_2B"] = gt_doubles
                row[f"{gt}_3B"] = gt_triples
                row[f"{gt}_BB"] = gt_stats.get("BB", 0)
                row[f"{gt}_SO"] = gt_stats.get("SO", 0)
                row[f"{gt}_SB"] = gt_stats.get("SB", 0)
                row[f"{gt}_Team"] = ", ".join(sorted(gt_teams)) if gt_teams else ""

            hitter_rows.append(row)

        hitters_df = pd.DataFrame(hitter_rows)

        if not hitters_df.empty:
            stat_cols = ["AB", "H", "RBI", "R", "HR", "2B", "3B", "SB", "BB", "SO", "HBP", "CS", "GIDP"]
            hitters_df = hitters_df.loc[~(hitters_df[stat_cols] == 0).all(axis=1)].reset_index(drop=True)
            hitters_df = hitters_df.sort_values("G", ascending=False).reset_index(drop=True)

        return hitters_df
    
    def _create_pitchers_dataframe(self, pit_tot, pit_team, pit_games,
                                     pit_by_type, pit_games_by_type, pit_team_by_type):
        """Create the pitchers DataFrame with per-game-type breakdowns."""
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

            row = {
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
            }

            # Add per-game-type stats
            for gt in self.GAME_TYPES:
                gt_stats = pit_by_type[gt].get(player_id, {})
                gt_outs = gt_stats.get("Outs", 0)
                gt_er = gt_stats.get("ER", 0)
                gt_era = round(gt_er * 9 / (gt_outs / 3), 2) if gt_outs > 0 else None
                gt_ip = StatUtils.outs_to_baseball_ip(gt_outs)
                gt_teams = pit_team_by_type[gt].get(player_id, set())

                row[f"{gt}_G"] = gt_stats.get("G", 0)
                row[f"{gt}_GS"] = gt_stats.get("GS", 0)
                row[f"{gt}_W"] = gt_stats.get("W", 0)
                row[f"{gt}_L"] = gt_stats.get("L", 0)
                row[f"{gt}_SV"] = gt_stats.get("SV", 0)
                row[f"{gt}_IP"] = gt_ip
                row[f"{gt}_ERA"] = gt_era
                row[f"{gt}_H"] = gt_stats.get("H", 0)
                row[f"{gt}_ER"] = gt_er
                row[f"{gt}_BB"] = gt_stats.get("BB", 0)
                row[f"{gt}_SO"] = gt_stats.get("SO", 0)
                row[f"{gt}_Team"] = ", ".join(sorted(gt_teams)) if gt_teams else ""

            pitcher_rows.append(row)

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
