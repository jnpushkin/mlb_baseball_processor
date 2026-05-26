import re
import logging
from collections import defaultdict, Counter
from datetime import datetime
import pandas as pd
from ..excel.generators import ExcelGeneratorUtils
from ..utils.helpers import standardize_team_code, join_sorted_gameids, _normalize_team_code_for_counts, _parse_duration_to_minutes, unify_team_code
from ..utils.log import debug
from .base_processor import BaseProcessor


class SummaryStatsProcessor(BaseProcessor):
    """Handle summary statistics processing with improved organization."""

    def __init__(self, games, all_players, b2b_only_df, b2b2b_only_df, b2b2b2b_only_df, triple_play_df, hitters_df, pitchers_df, milestones, weather_tracker=None, saber_tracker=None, situation_tracker=None):
        super().__init__(games)
        self.all_players = all_players
        # Store enhanced trackers
        self.weather_tracker = weather_tracker
        self.saber_tracker = saber_tracker
        self.situation_tracker = situation_tracker
        self.b2b_only_df = b2b_only_df
        self.b2b2b_only_df = b2b2b_only_df
        self.b2b2b2b_only_df = b2b2b2b_only_df
        self.triple_play_df = triple_play_df
        self.milestones = milestones
        # Initialize all counters
        self.count_1_0 = 0
        self.games_1_0 = []
        self.games_1_0_details = []
        self.games_1_0_scores = []
        self.extra_innings = 0
        self.games_extra_innings = []
        self.extra_inning_details = []
        self.extra_inning_scores = []
        self.most_runs = 0
        self.most_runs_gameids = []
        self.most_runs_teams = []
        self.most_runs_in_inning = 0
        self.most_runs_inning_gameids = []
        self.most_runs_inning_scores = []
        self.most_runs_inning_details = []
        self.most_combined_runs = 0
        self.most_combined_runs_gameids = []
        self.ten_plus_run_games = 0
        self.games_10_plus = []
        self.fifteen_plus_run_games = 0
        self.games_15_plus = []
        self.ten_plus_run_innings = 0
        self.ten_plus_run_inning_details = []
        self.ten_plus_run_inning_gameids = []
        self.twenty_plus_hit_games = 0
        self.games_20_plus_hits = []
        self.twenty_plus_hit_details = []
        self.twenty_plus_hit_scores = []
        self.one_run_games = 0            
        self.games_one_run = []           
        self.one_run_details = []
        self.one_run_scores = []
        self.biggest_victory_margin = 0
        self.biggest_victory_gameids = []
        self.biggest_victory_scores = []
        self.biggest_victory_winners = []
        self.biggest_victory_details = []
        self.inside_park_hrs = 0
        self.inside_park_hr_details = []
        self.inside_park_hr_gameids = []
        self.most_hr = 0
        self.most_hr_gameids = []
        self.most_hr_teams = []
        self.most_combined_hr = 0
        self.most_combined_hr_gameids = []
        self.most_hits = 0
        self.most_hits_gameids = []
        self.most_hits_teams = []
        self.most_combined_hits = 0
        self.most_combined_hits_gameids = []
        self.most_bb = 0
        self.most_bb_gameids = []
        self.most_bb_teams = []
        self.most_combined_bb = 0
        self.most_combined_bb_gameids = []
        self.fewest_bb = float('inf')
        self.fewest_bb_gameids = []
        self.fewest_bb_teams = []
        self.fewest_combined_bb = float('inf')
        self.fewest_combined_bb_gameids = []
        self.most_ks = 0
        self.most_ks_gameids = []
        self.most_ks_teams = []
        self.most_combined_ks = 0
        self.most_combined_ks_gameids = []
        self.fewest_strikeouts = float('inf')
        self.fewest_strikeouts_gameids = []
        self.most_pitches_single_game = 0
        self.most_pitches_pitcher_gameids = []
        self.most_pitches_pitcher_names = []
        self.most_pitches_pitcher_teams = []
        self.most_pitches_pitcher_dates = []
        self.most_pitches_pitcher_scores = []
        self.most_pitches_pitcher_statlines = []
        self.total_hits = 0
        self.total_hr = 0
        self.total_ks = 0
        self.total_runs = 0
        self.total_sb = 0
        self.most_rbi = 0
        self.most_rbi_gameids = []
        self.most_rbi_players = []
        self.most_sb_player = 0
        self.most_sb_player_labels = []
        self.most_sb_player_gameids = []
        self.most_sb_team = 0
        self.most_sb_team_labels = []
        self.most_sb_team_gameids = []
        self.most_sb_combined = 0
        self.most_sb_combined_gameids = []
        self.both_teams_10_runs = 0
        self.games_both_10_plus = []
        self.both_teams_10_details = []
        self.both_teams_10_scores = []
        self.winning_pitchers_seen = set()
        self.players_with_hit = set()
        self.players_with_hr = set()
        self.pitchers_with_loss = set()
        self.pitchers_with_save = set() 
        self.fewest_hits = float('inf')
        self.fewest_hits_gameids = []
        self.fewest_hits_teams = []
        self.fewest_combined_hits = float('inf')
        self.fewest_combined_hits_gameids = []
        self.all_temperatures = []
        self.coldest_temp = float('inf')
        self.coldest_temp_gameids = []
        self.coldest_temp_scores = []
        self.hottest_temp = float('-inf')
        self.hottest_temp_gameids = []
        self.hottest_temp_scores = []
        self.most_pitchers_used = 0
        self.most_pitchers_used_gameids = []
        self.most_pitchers_used_scores = []
        self.most_pitchers_used_details = []
        self.fewest_pitchers_used = float('inf')
        self.fewest_pitchers_used_gameids = []
        self.fewest_pitchers_used_scores = []
        self.fewest_pitchers_used_details = []
        self.longest_innings = 0
        self.longest_innings_gameids = []
        self.longest_innings_scores = []
        self.longest_time_min = 0            # minutes
        self.longest_time_gameids = []
        self.longest_time_scores = []
        self.shortest_time_min = float('inf')  # minutes
        self.shortest_time_gameids = []
        self.shortest_time_scores = []
        self.highest_attendance = 0
        self.highest_attendance_gameids = []
        self.highest_attendance_scores = []
        self.lowest_attendance = float('inf')
        self.lowest_attendance_gameids = []
        self.lowest_attendance_scores = []
        self.all_attendance_values = []
        self.hitters_df = hitters_df
        self.pitchers_df = pitchers_df
        
    def process_summary_statistics(self):
        """Process all summary statistics and build the summary stats DataFrame."""
        print("📊 Processing summary statistics...")

        # Records exclude spring training, but the matchup matrix still wants
        # to count attended spring matchups — keep the unfiltered list around
        # for that one analysis.
        self._all_games_with_spring = list(self.games)
        self.games = [g for g in self.games if g.get('basic_info', {}).get('game_type', 'regular') != 'spring']

        # Process each game
        for game in self.games:
            self._process_game_statistics(game)

        self._calculate_unique_achievements()
        
        # Track biggest comeback across all games
        self.biggest_comeback = {
            "deficit": 0,
            "date": None,
            "winner": None,
            "opponent": None,
            "final_score": None,
            "game_id": None,
            "deficit_inning": None,
            "score_at_deficit": None,
            "half": None,
            "half_inning_label": None
        }

        for game in self.games:
            try:
                comeback_info = self._get_biggest_comeback_from_linescore(game)
                basic_info = game.get("basic_info", {})
                game_id = game.get("game_id", "")

                # Extract deficit from the comeback_info dictionary
                deficit = comeback_info.get("deficit", 0) if isinstance(comeback_info, dict) else 0

                if deficit > self.biggest_comeback["deficit"]:
                    if basic_info.get("home_score_value", 0) > basic_info.get("away_score_value", 0):
                        winner = basic_info.get("home_team", "")
                        opponent = basic_info.get("away_team", "")
                    else:
                        winner = basic_info.get("away_team", "")
                        opponent = basic_info.get("home_team", "")

                    # Create score strings using standardized team codes
                    away_team_code = unify_team_code(basic_info.get('away_team_code', ''))
                    home_team_code = unify_team_code(basic_info.get('home_team_code', ''))
                    score_at_deficit = f"{away_team_code} {comeback_info.get('away_score_at_deficit', 0)} - {comeback_info.get('home_score_at_deficit', 0)} {home_team_code}"
                    final_score = f"{away_team_code} {basic_info.get('away_score_value', 0)} - {basic_info.get('home_score_value', 0)} {home_team_code}"

                    self.biggest_comeback = {
                        "deficit": deficit,
                        "date": basic_info.get("date"),
                        "winner": winner,
                        "opponent": opponent,
                        "final_score": final_score,  # ← NOW USES STANDARDIZED CODES
                        "game_id": game_id,
                        "deficit_inning": comeback_info.get("inning", 0),
                        "score_at_deficit": score_at_deficit,
                        "half": comeback_info.get("half", ""),
                        "half_inning_label": comeback_info.get("half_inning_label", "")
                    }
            except Exception as e:
                print(f"   ⚠️ Error processing comeback for game {game.get('game_id', 'UNKNOWN')}: {e}")
                continue

        # Process matchup analysis first
        df_matchups = self._process_matchup_analysis()

        # Now pass it into _build_summary_rows
        summary_rows = self._build_summary_rows(df_matchups)

        print(f"   ✅ Processed {len(summary_rows)} summary statistics")
        return summary_rows, df_matchups
    
    def _process_game_statistics(self, game):
        """Process statistics for a single game."""
        try:
            game_id = game.get("game_id", "")
            basic_info = game["basic_info"]
            linescore = game.get("linescore", {})
            
            # Process inning-by-inning statistics
            self._process_inning_statistics(game, game_id, basic_info)
            
            # Process game totals
            self._process_game_totals(game, game_id, basic_info, linescore)
            
            # Process home runs
            self._process_home_run_statistics(game, game_id, basic_info)
            
            # Process strikeouts
            self._process_strikeout_statistics(game, game_id, basic_info)
            
            # Process pitching walks (BB)
            self._process_walk_statistics(game, game_id, basic_info)
            
            # Process RBIs
            self._process_rbi_statistics(game, game_id)
            
            # Process stolen bases
            self._process_stolen_base_statistics(game, game_id, basic_info)
            
            #Process Attendance Statistics
            self._process_attendance_statistics(game, game_id, basic_info)

            # Track winning pitchers
            self._track_winning_pitchers(game)

            # Process inside-the-park HRs
            for play in game.get("play_by_play", []):
                if play.get("inside_the_park_hr"):
                    self.inside_park_hrs += 1
                    detail = self._format_inside_park_hr_detail(play)
                    self.inside_park_hr_details.append(detail)
                    self.inside_park_hr_gameids.append(game_id)
            
            # Track most pitchers used
            home_pitchers = game.get("pitching", {}).get("home", [])
            away_pitchers = game.get("pitching", {}).get("away", [])
            total_pitchers = len(home_pitchers) + len(away_pitchers)

            # Build detail string with team breakdowns and names
            home_names = [p.get("name", "Unknown") for p in home_pitchers]
            away_names = [p.get("name", "Unknown") for p in away_pitchers]
            home_code = basic_info.get("home_team_code", "HOME")
            away_code = basic_info.get("away_team_code", "AWAY")

            detail = f"{away_code} ({len(away_pitchers)}): {', '.join(away_names)}; {home_code} ({len(home_pitchers)}): {', '.join(home_names)}"

            if total_pitchers > self.most_pitchers_used:
                self.most_pitchers_used = total_pitchers
                self.most_pitchers_used_gameids = [game_id]
                self.most_pitchers_used_scores = [self._create_score_string(basic_info)]
                self.most_pitchers_used_details = [detail]
            elif total_pitchers == self.most_pitchers_used:
                self.most_pitchers_used_gameids.append(game_id)
                self.most_pitchers_used_scores.append(self._create_score_string(basic_info))
                self.most_pitchers_used_details.append(detail)
            # Track fewest pitchers used
            if total_pitchers < self.fewest_pitchers_used:
                self.fewest_pitchers_used = total_pitchers
                self.fewest_pitchers_used_gameids = [game_id]
                self.fewest_pitchers_used_scores = [self._create_score_string(basic_info)]
                self.fewest_pitchers_used_details = [detail]  # Use the same detail string we built above
            elif total_pitchers == self.fewest_pitchers_used:
                self.fewest_pitchers_used_gameids.append(game_id)
                self.fewest_pitchers_used_scores.append(self._create_score_string(basic_info))
                self.fewest_pitchers_used_details.append(detail)
                
        except Exception as e:
            print(f"   ⚠️ Error processing game statistics for {game_id}: {e}")
   
    def _process_inning_statistics(self, game, game_id, basic_info):
        """Process inning-by-inning run statistics."""
        for side in ("home", "away"):
            team_code = basic_info.get(f"{side}_team_code")
            innings = game.get("linescore", {}).get(side, {}).get("innings", [])
            
            for idx, val in enumerate(innings):
                try:
                    runs = int(val)
                except Exception:
                    continue
                
                # Track most runs in a single inning
                if runs > self.most_runs_in_inning:
                    self.most_runs_in_inning = runs
                    self.most_runs_inning_gameids = [game_id]
                    self.most_runs_inning_details = [f"{team_code} ({runs}) in {idx+1}"]
                    self.most_runs_inning_scores = [self._create_score_string(basic_info)]
                elif runs == self.most_runs_in_inning:
                    self.most_runs_inning_gameids.append(game_id)
                    self.most_runs_inning_details.append(f"{team_code} ({runs}) in {idx+1}")
                    self.most_runs_inning_scores.append(self._create_score_string(basic_info))
                
                # Track 10+ run innings
                if runs >= 10:
                    self.ten_plus_run_innings += 1

                    home_code = standardize_team_code(basic_info.get("home_team", ""))
                    away_code = standardize_team_code(basic_info.get("away_team", ""))

                    half = "Top" if team_code == away_code else "Bottom"
                    inning_number = idx + 1

                    if team_code == home_code:
                        detail = f"{home_code} v. {away_code}; ({runs} runs) in {half} {inning_number}"
                    else:
                        detail = f"{away_code} v. {home_code}; ({runs} runs) in {half} {inning_number}"

                    self.ten_plus_run_inning_details.append(detail)
                    self.ten_plus_run_inning_gameids.append(game_id)
    
    def _get_biggest_comeback_from_linescore(self, game):
        """Get comeback info including deficit, inning half, and score at max deficit."""
        linescore = game.get("linescore")
        if not linescore:
            return {
                "deficit": 0,
                "inning": 0,
                "half": "top",
                "half_inning_label": "Top 1",
                "away_score_at_deficit": 0,
                "home_score_at_deficit": 0
            }

        basic_info = game.get("basic_info", {})
        away_total = basic_info.get("away_score_value", 0)
        home_total = basic_info.get("home_score_value", 0)

        # Determine which team won
        winner = "home" if home_total > away_total else "away"

        away_innings = [int(x) for x in linescore.get("away", {}).get("innings", []) if str(x).isdigit()]
        home_innings = [int(x) for x in linescore.get("home", {}).get("innings", []) if str(x).isdigit()]
        num_innings = max(len(away_innings), len(home_innings))

        running_away = 0
        running_home = 0

        max_deficit_info = {
            "deficit": 0,
            "inning": 0,
            "half": "top",
            "half_inning_label": "Top 1",
            "away_score_at_deficit": 0,
            "home_score_at_deficit": 0
        }

        for i in range(num_innings):
            inning_num = i + 1

            # Top half: away team bats
            if i < len(away_innings):
                running_away += away_innings[i]

            deficit_top = running_home - running_away if winner == "away" else running_away - running_home
            if deficit_top > max_deficit_info["deficit"]:
                max_deficit_info = {
                    "deficit": deficit_top,
                    "inning": inning_num,
                    "half": "top",
                    "half_inning_label": f"Top {inning_num}",
                    "away_score_at_deficit": running_away,
                    "home_score_at_deficit": running_home
                }

            # Bottom half: home team bats
            if i < len(home_innings):
                running_home += home_innings[i]

            deficit_bot = running_away - running_home if winner == "home" else running_home - running_away
            if deficit_bot > max_deficit_info["deficit"]:
                max_deficit_info = {
                    "deficit": deficit_bot,
                    "inning": inning_num,
                    "half": "bottom",
                    "half_inning_label": f"Bottom {inning_num}",
                    "away_score_at_deficit": running_away,
                    "home_score_at_deficit": running_home
                }

        return max_deficit_info

    def _process_game_totals(self, game, game_id, basic_info, linescore):
        """Process game total statistics (runs, hits, etc.)."""
        away = linescore.get("away", {})
        home = linescore.get("home", {})
        away_r = away.get("R", 0)
        home_r = home.get("R", 0)
        away_h = away.get("H", 0)
        home_h = home.get("H", 0)
        
        # Track runs
        if away_r >= 10 and home_r >= 10:
            self.both_teams_10_runs += 1
            self.games_both_10_plus.append(game_id)
            self.both_teams_10_details.append(self._format_both_teams_10_detail(basic_info, linescore))
            self.both_teams_10_scores.append(self._create_score_string(basic_info))
        
        self.total_runs += away_r + home_r
        combined_runs = away_r + home_r
        team_runs = max(away_r, home_r)
        team_run_code = basic_info["away_team_code"] if away_r > home_r else basic_info["home_team_code"]

        # Track 1-run games
        if abs(away_r - home_r) == 1:
            self.one_run_games += 1
            self.games_one_run.append(game_id)
            self.one_run_details.append(self._format_game_run_hit_detail(basic_info, linescore))
            self.one_run_scores.append(self._create_score_string(basic_info))

        # Track biggest victory (largest run margin)
        margin = abs(away_r - home_r)
        winner_code = basic_info["away_team_code"] if away_r > home_r else basic_info["home_team_code"]

        if margin > self.biggest_victory_margin:
            self.biggest_victory_margin = margin
            self.biggest_victory_gameids = [game_id]
            self.biggest_victory_scores = [self._create_score_string(basic_info)]
            self.biggest_victory_winners = [winner_code]
            self.biggest_victory_details = [
                self._format_biggest_victory_detail(basic_info, linescore, winner_code, margin)
            ]
        elif margin == self.biggest_victory_margin:
            self.biggest_victory_gameids.append(game_id)
            self.biggest_victory_scores.append(self._create_score_string(basic_info))
            self.biggest_victory_winners.append(winner_code)
            self.biggest_victory_details.append(
                self._format_biggest_victory_detail(basic_info, linescore, winner_code, margin)
            )

        # Track most runs by one team
        if team_runs > self.most_runs:
            self.most_runs = team_runs
            self.most_runs_gameids = [game_id]
            self.most_runs_teams = [team_run_code]
        elif team_runs == self.most_runs:
            self.most_runs_gameids.append(game_id)
            self.most_runs_teams.append(team_run_code)
        
        # Track most combined runs
        if combined_runs > self.most_combined_runs:
            self.most_combined_runs = combined_runs
            self.most_combined_runs_gameids = [game_id]
        elif combined_runs == self.most_combined_runs:
            self.most_combined_runs_gameids.append(game_id)
        
        # Track special run thresholds
        if away_r >= 10 or home_r >= 10:
            self.ten_plus_run_games += 1
            self.games_10_plus.append(game_id)
        
        if away_r >= 15:
            self.fifteen_plus_run_games += 1
            self.games_15_plus.append(game_id)
        if home_r >= 15:
            self.fifteen_plus_run_games += 1
            self.games_15_plus.append(game_id)
        
        # Track 1-0 games
        if (away_r == 1 and home_r == 0) or (home_r == 1 and away_r == 0):
            self.count_1_0 += 1
            self.games_1_0.append(game_id)
            self.games_1_0_details.append(self._format_game_run_hit_detail(basic_info, linescore))
            self.games_1_0_scores.append(self._create_score_string(basic_info))
        
        # Track extra inning games
        if len(home.get("innings", [])) > 9 or len(away.get("innings", [])) > 9:
            self.extra_innings += 1
            self.games_extra_innings.append(game_id)
            self.extra_inning_details.append(self._format_extra_inning_detail(basic_info, linescore))
            self.extra_inning_scores.append(self._create_score_string(basic_info))
        
        # Track hits
        self.total_hits += away_h + home_h
        combined_hits = away_h + home_h
        team_hits = max(away_h, home_h)
        team_hits_code = basic_info["away_team_code"] if away_h > home_h else basic_info["home_team_code"]
        
        # Track fewest hits by one team
        for hits, team_code in [(away_h, basic_info.get("away_team_code")),
                                (home_h, basic_info.get("home_team_code"))]:
            if hits < self.fewest_hits:
                self.fewest_hits = hits
                self.fewest_hits_gameids = [game_id]
                self.fewest_hits_teams = [team_code]
            elif hits == self.fewest_hits:
                self.fewest_hits_gameids.append(game_id)
                self.fewest_hits_teams.append(team_code)

        # Track fewest combined hits
        if combined_hits < self.fewest_combined_hits:
            self.fewest_combined_hits = combined_hits
            self.fewest_combined_hits_gameids = [game_id]
        elif combined_hits == self.fewest_combined_hits:
            self.fewest_combined_hits_gameids.append(game_id)

        # Track 20+ hit games
        if away_h >= 20 or home_h >= 20:
            self.twenty_plus_hit_games += 1
            self.games_20_plus_hits.append(game_id)
            self.twenty_plus_hit_details.append(self._format_twenty_hit_detail(basic_info, linescore))
            self.twenty_plus_hit_scores.append(self._create_score_string(basic_info))
        
        # Track most hits by one team
        if team_hits > self.most_hits:
            self.most_hits = team_hits
            self.most_hits_gameids = [game_id]
            self.most_hits_teams = [team_hits_code]
        elif team_hits == self.most_hits:
            self.most_hits_gameids.append(game_id)
            self.most_hits_teams.append(team_hits_code)
        
        # Track most combined hits
        if combined_hits > self.most_combined_hits:
            self.most_combined_hits = combined_hits
            self.most_combined_hits_gameids = [game_id]
        elif combined_hits == self.most_combined_hits:
            self.most_combined_hits_gameids.append(game_id)

        # --- Environment / length tracking ---

        # Longest game by innings
        try:
            innings_home = len(linescore.get("home", {}).get("innings", []))
            innings_away = len(linescore.get("away", {}).get("innings", []))
            max_innings = max(innings_home, innings_away)
        except Exception:
            max_innings = None

        if isinstance(max_innings, int):
            if max_innings > self.longest_innings:
                self.longest_innings = max_innings
                self.longest_innings_gameids = [game_id]
                self.longest_innings_scores = [self._create_score_string(basic_info)]
            elif max_innings == self.longest_innings:
                self.longest_innings_gameids.append(game_id)
                self.longest_innings_scores.append(self._create_score_string(basic_info))

        # Longest / Shortest game by time
        duration_text = basic_info.get("duration", "")
        duration_min = _parse_duration_to_minutes(duration_text)
        if isinstance(duration_min, int):
            if duration_min > self.longest_time_min:
                self.longest_time_min = duration_min
                self.longest_time_gameids = [game_id]
                self.longest_time_scores = [self._create_score_string(basic_info)]
            elif duration_min == self.longest_time_min:
                self.longest_time_gameids.append(game_id)
                self.longest_time_scores.append(self._create_score_string(basic_info))

            if duration_min < self.shortest_time_min:
                self.shortest_time_min = duration_min
                self.shortest_time_gameids = [game_id]
                self.shortest_time_scores = [self._create_score_string(basic_info)]
            elif duration_min == self.shortest_time_min:
                self.shortest_time_gameids.append(game_id)
                self.shortest_time_scores.append(self._create_score_string(basic_info))

        # --- Temperature tracking ---
        temp = basic_info.get("temperature_f")
        if isinstance(temp, int):
            self.all_temperatures.append(temp)

            if temp < self.coldest_temp:
                self.coldest_temp = temp
                self.coldest_temp_gameids = [game_id]
                self.coldest_temp_scores = [self._create_score_string(basic_info)]
            elif temp == self.coldest_temp:
                self.coldest_temp_gameids.append(game_id)
                self.coldest_temp_scores.append(self._create_score_string(basic_info))

            if temp > self.hottest_temp:
                self.hottest_temp = temp
                self.hottest_temp_gameids = [game_id]
                self.hottest_temp_scores = [self._create_score_string(basic_info)]
            elif temp == self.hottest_temp:
                self.hottest_temp_gameids.append(game_id)
                self.hottest_temp_scores.append(self._create_score_string(basic_info))
                
        # --- update: most pitches by a single pitcher (per game) ---
        self._update_most_pitches_single_game(game, game_id, basic_info)
                

    def _calculate_unique_achievements(self):
        """Calculate unique player achievements from the processed DataFrames."""
        try:
            debug("🔍 Calculating unique achievements from DataFrames...")
            debug(f"🔍 Hitters DataFrame has {len(self.hitters_df)} players")
            debug(f"🔍 Pitchers DataFrame has {len(self.pitchers_df)} pitchers")
            
            # Track unique players with hits and HRs from hitters DataFrame
            hits_found = 0
            hrs_found = 0
            
            for _, player in self.hitters_df.iterrows():
                player_id = player.get("Player ID")
                player_name = player.get("Name", "Unknown")
                
                if not player_id:
                    continue
                    
                hits = player.get("H", 0)
                home_runs = player.get("HR", 0)
                
                # Convert to int if needed
                try:
                    hits = int(hits) if hits != "" else 0
                    home_runs = int(home_runs) if home_runs != "" else 0
                except (ValueError, TypeError):
                    hits = 0
                    home_runs = 0
                
                if hits > 0:
                    self.players_with_hit.add(player_id)
                    hits_found += 1
                    
                if home_runs > 0:
                    self.players_with_hr.add(player_id)
                    hrs_found += 1
            
            debug(f"🔍 From hitters DataFrame: {hits_found} players with hits, {hrs_found} players with HRs")
            
            # Track unique pitchers with losses and saves from pitchers DataFrame
            losses_found = 0
            saves_found = 0
            
            for _, pitcher in self.pitchers_df.iterrows():
                player_id = pitcher.get("Player ID")
                player_name = pitcher.get("Name", "Unknown")
                
                if not player_id:
                    continue
                    
                losses = pitcher.get("L", 0)
                saves = pitcher.get("SV", 0)
                
                try:
                    losses = int(losses) if losses != "" else 0
                    saves = int(saves) if saves != "" else 0
                except (ValueError, TypeError):
                    losses = 0
                    saves = 0
                
                if losses > 0:
                    self.pitchers_with_loss.add(player_id)
                    losses_found += 1
                    
                if saves > 0:
                    self.pitchers_with_save.add(player_id)
                    saves_found += 1
            
            debug(f"🔍 From pitchers DataFrame: {losses_found} pitchers with losses, {saves_found} pitchers with saves")

            debug("🔍 FINAL unique achievements:")
            debug(f"   Players with a Hit: {len(self.players_with_hit)}")
            debug(f"   Players with a HR: {len(self.players_with_hr)}")
            debug(f"   Pitchers with a Loss: {len(self.pitchers_with_loss)}")
            debug(f"   Pitchers with a Save: {len(self.pitchers_with_save)}")
                    
        except Exception as e:
            print(f"   ⚠️ Error calculating unique achievements: {e}")
            logging.exception("Error details:")

    def _process_attendance_statistics(self, game, game_id, basic_info):
        """Process attendance statistics."""
        attendance = basic_info.get("attendance_value")
        
        if isinstance(attendance, int) and attendance > 0:
            self.all_attendance_values.append(attendance)
            # Track highest attendance
            if attendance > self.highest_attendance:
                self.highest_attendance = attendance
                self.highest_attendance_gameids = [game_id]
                self.highest_attendance_scores = [self._create_score_string(basic_info)]
            elif attendance == self.highest_attendance:
                self.highest_attendance_gameids.append(game_id)
                self.highest_attendance_scores.append(self._create_score_string(basic_info))
            
            # Track lowest attendance
            if attendance < self.lowest_attendance:
                self.lowest_attendance = attendance
                self.lowest_attendance_gameids = [game_id]
                self.lowest_attendance_scores = [self._create_score_string(basic_info)]
            elif attendance == self.lowest_attendance:
                self.lowest_attendance_gameids.append(game_id)
                self.lowest_attendance_scores.append(self._create_score_string(basic_info))

    def _process_home_run_statistics(self, game, game_id, basic_info):
        """Process home run statistics."""
        hr_home, _ = self._team_hr_breakdown(game, "home")
        hr_away, _ = self._team_hr_breakdown(game, "away")
        
        self.total_hr += hr_home + hr_away
        combined_hr = hr_home + hr_away
        team_hr = max(hr_home, hr_away)
        team_hr_code = basic_info["away_team_code"] if hr_away > hr_home else basic_info["home_team_code"]
        
        # Track most HRs by one team
        if team_hr > self.most_hr:
            self.most_hr = team_hr
            self.most_hr_gameids = [game_id]
            self.most_hr_teams = [team_hr_code]
        elif team_hr == self.most_hr:
            self.most_hr_gameids.append(game_id)
            self.most_hr_teams.append(team_hr_code)
        
        # Track most combined HRs
        if combined_hr > self.most_combined_hr:
            self.most_combined_hr = combined_hr
            self.most_combined_hr_gameids = [game_id]
        elif combined_hr == self.most_combined_hr:
            self.most_combined_hr_gameids.append(game_id)
    
    def _process_strikeout_statistics(self, game, game_id, basic_info):
        """Process strikeout statistics."""
        team_ks_totals = []
        
        for side in ("home", "away"):
            team_ks = sum(p.get("SO", 0) for p in game.get("pitching", {}).get(side, []))
            self.total_ks += team_ks
            team_code = basic_info.get(f"{side}_team_code", side.upper())
            team_ks_totals.append((team_ks, team_code))
            
            # Track most strikeouts by one team
            if team_ks > self.most_ks:
                self.most_ks = team_ks
                self.most_ks_gameids = [game_id]
                self.most_ks_teams = [team_code]
            elif team_ks == self.most_ks:
                self.most_ks_gameids.append(game_id)
                self.most_ks_teams.append(team_code)
        
        # Track most combined strikeouts
        combined_ks = sum(ks for ks, _ in team_ks_totals)
        if combined_ks > self.most_combined_ks:
            self.most_combined_ks = combined_ks
            self.most_combined_ks_gameids = [game_id]
        elif combined_ks == self.most_combined_ks:
            self.most_combined_ks_gameids.append(game_id)

        # Track fewest combined strikeouts
        if combined_ks < self.fewest_strikeouts:
            self.fewest_strikeouts = combined_ks
            self.fewest_strikeouts_gameids = [game_id]
        elif combined_ks == self.fewest_strikeouts:
            self.fewest_strikeouts_gameids.append(game_id)

    
    def _process_walk_statistics(self, game, game_id, basic_info):
        """Process pitching walks (BB) team and combined records."""
        team_bb_totals = []
        for side in ("home", "away"):
            team_bb = sum(p.get("BB", 0) for p in game.get("pitching", {}).get(side, []))
            team_code = basic_info.get(f"{side}_team_code", side.upper())
            team_bb_totals.append((team_bb, team_code))

            if team_bb > self.most_bb:
                self.most_bb = team_bb
                self.most_bb_gameids = [game_id]
                self.most_bb_teams = [team_code]
            elif team_bb == self.most_bb:
                self.most_bb_gameids.append(game_id)
                self.most_bb_teams.append(team_code)

            if team_bb < self.fewest_bb:
                self.fewest_bb = team_bb
                self.fewest_bb_gameids = [game_id]
                self.fewest_bb_teams = [team_code]
            elif team_bb == self.fewest_bb:
                self.fewest_bb_gameids.append(game_id)
                self.fewest_bb_teams.append(team_code)

        combined_bb = sum(bb for bb, _ in team_bb_totals)
        if combined_bb > self.most_combined_bb:
            self.most_combined_bb = combined_bb
            self.most_combined_bb_gameids = [game_id]
        elif combined_bb == self.most_combined_bb:
            self.most_combined_bb_gameids.append(game_id)

        if combined_bb < self.fewest_combined_bb:
            self.fewest_combined_bb = combined_bb
            self.fewest_combined_bb_gameids = [game_id]
        elif combined_bb == self.fewest_combined_bb:
            self.fewest_combined_bb_gameids.append(game_id)

    def _process_rbi_statistics(self, game, game_id):
        """Process RBI statistics."""
        for side in ("home", "away"):
            for player in game.get("batting", {}).get(side, []):
                rbi = player.get("RBI", 0)
                if rbi > self.most_rbi:
                    self.most_rbi = rbi
                    self.most_rbi_gameids = [game_id]
                    self.most_rbi_players = [f"{player.get('name', 'Unknown')} ({rbi})"]
                elif rbi == self.most_rbi and rbi > 0:
                    self.most_rbi_gameids.append(game_id)
                    self.most_rbi_players.append(f"{player.get('name', 'Unknown')} ({rbi})")
    
    def _process_stolen_base_statistics(self, game, game_id, basic_info):
        """Process stolen base statistics."""
        seen_player_game = set()
        sb_team_totals = {}
        
        for side in ("home", "away"):
            team_code = basic_info.get(f"{side}_team_code", side.upper())
            
            # Process individual player SBs from batting box
            for player in game.get("batting", {}).get(side, []):
                sb = player.get("SB", 0)
                if sb > 0 and (player["player_id"], game_id) not in seen_player_game:
                    if sb > self.most_sb_player:
                        self.most_sb_player = sb
                        self.most_sb_player_labels = [f"{player['name']} ({sb})"]
                        self.most_sb_player_gameids = [game_id]
                    elif sb == self.most_sb_player:
                        self.most_sb_player_labels.append(f"{player['name']} ({sb})")
                        self.most_sb_player_gameids.append(game_id)
                    seen_player_game.add((player["player_id"], game_id))
            
            # Process SBs from footer summary
            footer_blob = game.get("footer_summary", {}).get(side, {}).get("SB", "")
            for name, count in ExcelGeneratorUtils.extract_stat_counts(footer_blob):
                label_key = (name, game_id)
                if label_key not in seen_player_game:
                    if count > self.most_sb_player:
                        self.most_sb_player = count
                        self.most_sb_player_labels = [f"{name} ({count})"]
                        self.most_sb_player_gameids = [game_id]
                    elif count == self.most_sb_player:
                        self.most_sb_player_labels.append(f"{name} ({count})")
                        self.most_sb_player_gameids.append(game_id)
                    seen_player_game.add(label_key)
            
            # Calculate team SB totals
            sb_box = sum(p.get("SB", 0) for p in game.get("batting", {}).get(side, []))
            sb_footer = sum(n for _, n in ExcelGeneratorUtils.extract_stat_counts(footer_blob))
            sb_total = max(sb_box, sb_footer)
            
            sb_team_totals[team_code] = sb_total
            self.total_sb += sb_total

            # Track most SBs by one team
            if sb_total > self.most_sb_team:
                self.most_sb_team = sb_total
                self.most_sb_team_labels = [team_code]
                self.most_sb_team_gameids = [game_id]
            elif sb_total == self.most_sb_team and sb_total > 0:
                self.most_sb_team_labels.append(team_code)
                self.most_sb_team_gameids.append(game_id)
        
        # Track most combined SBs
        sb_combined_total = sum(sb_team_totals.values())
        if sb_combined_total > self.most_sb_combined:
            self.most_sb_combined = sb_combined_total
            self.most_sb_combined_gameids = [game_id]
        elif sb_combined_total == self.most_sb_combined and sb_combined_total > 0:
            self.most_sb_combined_gameids.append(game_id)
    
    def _track_winning_pitchers(self, game):
        """Track unique winning pitchers."""
        pitch_decision = game.get("pitcher_decisions", {})
        winner_id = pitch_decision.get("winning_pitcher_id")
        if winner_id:
            self.winning_pitchers_seen.add(winner_id)
    

    def _get_stat_leaders(self, df, stat_column, num_leaders=5, ascending=False):
        """Get top N players for a given statistic."""
        if df.empty or stat_column not in df.columns:
            return []
        
        df_copy = df.copy()
        df_copy[stat_column] = pd.to_numeric(df_copy[stat_column], errors='coerce').fillna(0)
        
        if not ascending:
            df_copy = df_copy[df_copy[stat_column] > 0]
        
        if df_copy.empty:
            return []
        
        df_sorted = df_copy.sort_values(stat_column, ascending=ascending).head(num_leaders)
        
        # Define formatting rules for different stat types
        decimal_stats = {
            'AVG': 3, 'OBP': 3, 'OPS': 3, 'ERA': 2, 'WHIP': 3, 'SLG': 3, 'IP': 1
        }
        
        leaders = []
        for _, player in df_sorted.iterrows():
            name = player.get("Name", "Unknown")
            stat_value = player.get(stat_column, 0)
            
            if stat_column in decimal_stats:
                decimal_places = decimal_stats[stat_column]
                formatted_value = f"{stat_value:.{decimal_places}f}"
            elif isinstance(stat_value, float) and stat_value.is_integer():
                formatted_value = str(int(stat_value))
            else:
                formatted_value = str(stat_value)
            
            leaders.append(f"{name} ({formatted_value})")
        
        return leaders

    def _add_stat_leaders_to_summary(self, summary_rows):
        """Add statistical leaders to the summary rows."""
        
        # Hitting Leaders
        hitting_stats = [
            ("H", "Hits Leaders"),
            ("R", "Runs Leaders"), 
            ("HR", "Home Run Leaders"),
            ("RBI", "RBI Leaders"),
            ("2B", "Doubles Leaders"),
            ("3B", "Triples Leaders"),
            ("SB", "Stolen Base Leaders"),
            ("BB", "Walks Leaders (Hitting)")
        ]
        
        for stat_col, record_name in hitting_stats:
            leaders = self._get_stat_leaders(self.hitters_df, stat_col)
            if leaders:
                summary_rows.append({
                    "Record": record_name,
                    "Value": "",
                    "Detail": "; ".join(leaders),
                    "Score": "",
                    "GameIDs": ""
                })
        
        # Batting Average Leaders (minimum plate appearances)
        if "AVG" in self.hitters_df.columns and "AB" in self.hitters_df.columns:
            # Filter players with at least 10 at-bats to avoid small sample sizes
            df_qualified = self.hitters_df.copy()
            df_qualified["AB"] = pd.to_numeric(df_qualified["AB"], errors='coerce').fillna(0)
            df_qualified["AVG"] = pd.to_numeric(df_qualified["AVG"], errors='coerce').fillna(0)
            
            qualified_hitters = df_qualified[df_qualified["AB"] >= 10]
            if not qualified_hitters.empty:
                avg_leaders = self._get_stat_leaders(qualified_hitters, "AVG")
                if avg_leaders:
                    summary_rows.append({
                        "Record": "Batting Average Leaders (min. 10 AB)",
                        "Value": "",
                        "Detail": "; ".join(avg_leaders),
                        "Score": "",
                        "GameIDs": ""
                    })
        
        # Pitching Leaders
        pitching_stats = [
            ("W", "Wins Leaders"),
            ("SO", "Strikeout Leaders (Pitching)"),
            ("SV", "Save Leaders"),
            ("IP", "Innings Pitched Leaders"),
            ("H", "Fewest Hits Allowed Leaders"),
            ("BB", "Fewest Walks Allowed Leaders")
        ]
        
        for stat_col, record_name in pitching_stats:
            # For "fewest" stats, use ascending order
            ascending = stat_col in ["H", "BB", "ERA", "WHIP"]
            leaders = self._get_stat_leaders(self.pitchers_df, stat_col, ascending=ascending)
            if leaders:
                summary_rows.append({
                    "Record": record_name,
                    "Value": "",
                    "Detail": "; ".join(leaders),
                    "Score": "",
                    "GameIDs": ""
                })
        
        # ERA Leaders (minimum innings pitched)
        if "ERA" in self.pitchers_df.columns and "IP" in self.pitchers_df.columns:
            # Filter pitchers with at least 10 innings pitched
            df_qualified = self.pitchers_df.copy()
            df_qualified["IP"] = pd.to_numeric(df_qualified["IP"], errors='coerce').fillna(0)
            df_qualified["ERA"] = pd.to_numeric(df_qualified["ERA"], errors='coerce').fillna(999)
            
            qualified_pitchers = df_qualified[df_qualified["IP"] >= 10]
            if not qualified_pitchers.empty:
                era_leaders = self._get_stat_leaders(qualified_pitchers, "ERA", ascending=True)
                if era_leaders:
                    summary_rows.append({
                        "Record": "ERA Leaders (min. 10 IP)",
                        "Value": "",
                        "Detail": "; ".join(era_leaders),
                        "Score": "",
                        "GameIDs": ""
                    })
        
        return summary_rows

    # Modified _build_summary_rows method - add this at the end of the existing method
    def _build_summary_rows_with_leaders(self, df_matchups):
        """Build the summary statistics rows including stat leaders."""
        
        # Get all the existing summary rows (your current implementation)
        summary_rows = self._build_summary_rows(df_matchups)
        
        # Add stat leaders
        summary_rows = self._add_stat_leaders_to_summary(summary_rows)
        
        return summary_rows

    def _create_score_string(self, basic_info):
        """Create a standardized score string."""
        return ExcelGeneratorUtils.format_score_string(basic_info, 9)

    def _clean_event_text(self, value):
        return re.sub(r"\s+", " ", str(value or "").replace("\xa0", " ")).strip()

    def _ordinal(self, value):
        try:
            number = int(value)
        except (TypeError, ValueError):
            return ""
        if number <= 0:
            return ""
        if 10 <= number % 100 <= 20:
            suffix = "th"
        else:
            suffix = {1: "st", 2: "nd", 3: "rd"}.get(number % 10, "th")
        return f"{number}{suffix}"

    def _run_value_label(self, rbi):
        try:
            runs = int(rbi)
        except (TypeError, ValueError):
            runs = 0
        if runs == 1:
            return "solo"
        if runs == 4:
            return "grand slam"
        if runs > 1:
            return f"{runs}-run"
        return ""

    def _extract_contact_detail(self, description):
        text = self._clean_event_text(description)
        match = re.search(r"\(([^)]*)\)", text)
        return self._clean_event_text(match.group(1)) if match else ""

    def _format_inside_park_hr_detail(self, play):
        batter = self._clean_event_text(play.get("batter")) or "Unknown"
        half = self._clean_event_text(play.get("half")).title()
        inning = self._clean_event_text(play.get("inning"))
        inning_label = f"{half} {inning}".strip()

        outs = play.get("outs_before", play.get("outs"))
        outs_label = ""
        try:
            out_count = int(outs)
            outs_label = f"{out_count} {'out' if out_count == 1 else 'outs'}"
        except (TypeError, ValueError):
            pass

        context = ", ".join(part for part in (inning_label, outs_label) if part)
        prefix = f"{batter} - {context}: " if context else f"{batter} - "

        run_label = self._run_value_label(play.get("rbi"))
        event_label = "inside-the-park HR"
        if run_label == "grand slam":
            event_label = "inside-the-park grand slam"
        elif run_label:
            event_label = f"{run_label} {event_label}"

        detail = f"{prefix}{event_label}"
        pitcher = self._clean_event_text(play.get("pitcher"))
        if pitcher and pitcher != "Unknown":
            detail += f" off {pitcher}"

        pitch_number = play.get("pitch_number") or play.get("pitch_count")
        pitch_label = self._ordinal(pitch_number)
        if pitch_label:
            detail += f" ({pitch_label} pitch)"

        contact = self._extract_contact_detail(play.get("description", ""))
        if contact:
            detail += f" - {contact}"
        return detail

    def _format_both_teams_10_detail(self, basic_info, linescore):
        return self._format_game_run_hit_detail(basic_info, linescore)

    def _format_game_run_hit_detail(self, basic_info, linescore):
        away = linescore.get("away", {})
        home = linescore.get("home", {})
        away_code = unify_team_code(basic_info.get("away_team_code", ""))
        home_code = unify_team_code(basic_info.get("home_team_code", ""))
        away_r = int(away.get("R", 0) or 0)
        home_r = int(home.get("R", 0) or 0)
        away_h = int(away.get("H", 0) or 0)
        home_h = int(home.get("H", 0) or 0)

        innings_played = max(
            len(away.get("innings", []) or []),
            len(home.get("innings", []) or []),
        )
        innings_label = f" in {innings_played} innings" if innings_played > 9 else ""
        total_runs = away_r + home_r
        total_hits = away_h + home_h
        run_word = "run" if total_runs == 1 else "runs"
        hit_word = "hit" if total_hits == 1 else "hits"
        hit_context = f", {total_hits} {hit_word}" if total_hits else ""
        return f"{away_code} {away_r}, {home_code} {home_r}{innings_label} ({total_runs} {run_word}{hit_context})"

    def _format_extra_inning_detail(self, basic_info, linescore):
        return self._format_game_run_hit_detail(basic_info, linescore)

    def _format_twenty_hit_detail(self, basic_info, linescore):
        away = linescore.get("away", {})
        home = linescore.get("home", {})
        away_code = unify_team_code(basic_info.get("away_team_code", ""))
        home_code = unify_team_code(basic_info.get("home_team_code", ""))
        away_h = int(away.get("H", 0) or 0)
        home_h = int(home.get("H", 0) or 0)
        teams = []
        if away_h >= 20:
            teams.append(f"{away_code} {away_h} H")
        if home_h >= 20:
            teams.append(f"{home_code} {home_h} H")
        total_hits = away_h + home_h
        return f"{', '.join(teams)} ({total_hits} combined hits) - {self._format_game_run_hit_detail(basic_info, linescore)}"

    def _format_biggest_victory_detail(self, basic_info, linescore, winner_code, margin):
        return f"{winner_code} by {margin} - {self._format_game_run_hit_detail(basic_info, linescore)}"

    def _update_most_pitches_single_game(self, game: dict, game_id: str, basic_info: dict):
        """
        Find the maximum pitch count thrown by any single pitcher in this game and
        update the 'most pitches' record if exceeded or tied.
        """
        import re

        def _safe_int(x):
            if isinstance(x, int):
                return x
            if isinstance(x, str):
                s = x.strip()
                if s.isdigit():
                    return int(s)
                m = re.search(r"\d+", s)
                if m:
                    try:
                        return int(m.group(0))
                    except Exception:
                        pass
            return None

        def _get_pitch_count(prow: dict):
            for k in ("pitches", "Pitches", "Pit", "NP", "pitch_count", "P"):
                if k in prow:
                    val = _safe_int(prow.get(k))
                    if isinstance(val, int):
                        return val
            for v in prow.values():
                if isinstance(v, str):
                    m = re.search(r"(\d+)\s*pitches", v, flags=re.IGNORECASE)
                    if m:
                        return _safe_int(m.group(1))
            return None

        def _get_pitcher_name(prow: dict):
            for k in ("pitcher", "Pitcher", "name", "Name", "player_name", "Player"):
                if k in prow and isinstance(prow[k], str) and prow[k].strip():
                    return prow[k].strip()
            player = prow.get("player") if isinstance(prow.get("player"), dict) else None
            if player and isinstance(player.get("name"), str):
                return player["name"].strip()
            return "Unknown"

        def _get_statline(prow: dict) -> str:
            def first_of(*keys, default=None):
                for k in keys:
                    if k in prow and prow[k] not in (None, ""):
                        return prow[k]
                return default

            ip = first_of("IP", "Ip", "ip")
            if ip is None:
                ipouts = first_of("IPouts", "ipouts")
                if isinstance(ipouts, int):
                    ip = f"{ipouts // 3}.{ipouts % 3}"
            ip_str = str(ip) if ip not in (None, "") else "0.0"

            h  = _safe_int(first_of("H", "Hits", "h")) or 0
            r  = _safe_int(first_of("R", "Runs", "r")) or 0
            bb = _safe_int(first_of("BB", "Walks", "Bb")) or 0
            so = _safe_int(first_of("SO", "Strikeouts", "K", "So")) or 0

            return f"{ip_str} IP, {h} H, {r} R, {bb} BB, {so} K"

        def _iter_pitchers():
            pitching = game.get("pitching", {})
            if isinstance(pitching, dict):
                for side in ("away", "home"):
                    team_code = basic_info.get(f"{side}_team_code") or side.upper()
                    rows = pitching.get(side, [])
                    if isinstance(rows, list):
                        for prow in rows:
                            yield team_code, prow
            if isinstance(pitching, list):
                for prow in pitching:
                    yield (basic_info.get("away_team_code") or "AWY"), prow

        # --- main logic ---
        max_pitcher = None
        max_pitches = None
        max_team = None
        max_statline = None

        for team_code, prow in _iter_pitchers():
            pc = _get_pitch_count(prow)
            if isinstance(pc, int):
                if (max_pitches is None) or (pc > max_pitches):
                    max_pitches = pc
                    max_pitcher = _get_pitcher_name(prow)
                    max_team = team_code
                    max_statline = _get_statline(prow)

        if isinstance(max_pitches, int):
            score_str = self._create_score_string(basic_info)
            date_ymd = basic_info.get("date_yyyymmdd", "")
            if max_pitches > self.most_pitches_single_game:
                self.most_pitches_single_game = max_pitches
                self.most_pitches_pitcher_gameids = [game_id]
                self.most_pitches_pitcher_names = [max_pitcher]
                self.most_pitches_pitcher_teams = [max_team]
                self.most_pitches_pitcher_dates = [date_ymd]
                self.most_pitches_pitcher_scores = [score_str]
                self.most_pitches_pitcher_statlines = [max_statline or ""]
            elif max_pitches == self.most_pitches_single_game:
                self.most_pitches_pitcher_gameids.append(game_id)
                self.most_pitches_pitcher_names.append(max_pitcher)
                self.most_pitches_pitcher_teams.append(max_team)
                self.most_pitches_pitcher_dates.append(date_ymd)
                self.most_pitches_pitcher_scores.append(score_str)
                self.most_pitches_pitcher_statlines.append(max_statline or "")
    
    def _build_summary_rows(self, df_matchups):
        """Build the summary statistics rows."""
        summary_rows = []
        
        # Helper functions
        def game_id_sort_key(game_id):
            gid = str(game_id or "")
            date_part = gid[3:11] if len(gid) >= 11 and gid[3:11].isdigit() else gid
            return (date_part, gid)

        def sorted_context_rows(ids, details, scores):
            rows = [
                (str(gid), str(detail), str(score))
                for gid, detail, score in zip(ids, details, scores)
                if str(gid or "").strip()
            ]
            return sorted(rows, key=lambda row: game_id_sort_key(row[0]))

        def join_gameids_in_order(ids):
            return ", ".join(str(gid).strip() for gid in ids if str(gid or "").strip())

        def sort_gameids_in_context_order(ids):
            id_list = list(ids or [])
            rows = sorted_context_rows(id_list, [""] * len(id_list), [""] * len(id_list))
            return join_gameids_in_order(row[0] for row in rows)

        def group_games_by_value(value, label, ids, teams=None, stat_key="R"):
            grouped = []
            for idx, gid in enumerate(ids):
                game = next(g for g in self.games if g["game_id"] == gid)
                basic_info = game["basic_info"]
                team = teams[idx] if teams else None
                detail = (
                    self._format_single_team_record_detail(game, team, stat_key, value, label)
                    if team else self._make_combined_detail(game, stat_key)
                )
                grouped.append({
                    "Detail": detail,
                    "Score": self._create_score_string(basic_info),
                    "GameIDs": gid
                })
            return grouped
        
        # Single team records
        for value, label, ids, teams, stat_key in [
            (self.most_bb, "Most Walks by One Team", self.most_bb_gameids, self.most_bb_teams, "BB"),
            (self.most_runs, "Most Runs by One Team", self.most_runs_gameids, self.most_runs_teams, "R"),
            (self.most_hr, "Most HRs by One Team", self.most_hr_gameids, self.most_hr_teams, "HR"),
            (self.most_hits, "Most Hits by One Team", self.most_hits_gameids, self.most_hits_teams, "H"),
            (self.most_ks, "Most Pitching Strikeouts by One Team", self.most_ks_gameids, self.most_ks_teams, "SO"),
            (self.most_sb_team, "Most SBs by One Team", self.most_sb_team_gameids, self.most_sb_team_labels, "SB"),
        ]:
            rows = group_games_by_value(value, label, ids, teams, stat_key=stat_key)
            summary_rows.append({
                "Record": label,
                "Value": value,
                "Detail": "; ".join(r["Detail"] for r in rows),
                "Score": "; ".join(r["Score"] for r in rows),
                "GameIDs": ", ".join(r["GameIDs"] for r in rows)  # Keep same order as Detail/Score
            })
        
        # --- Most pitches by one pitcher (per game): Detail = pitcher + stat line, Score column has score ---
        if self.most_pitches_single_game > 0 and self.most_pitches_pitcher_gameids:
            # Build "Name — <stat line>" details
            details = []
            for name, stat in zip(self.most_pitches_pitcher_names, self.most_pitches_pitcher_statlines):
                details.append(f"{name} — {stat}")
            rows = sorted_context_rows(
                self.most_pitches_pitcher_gameids,
                details,
                self.most_pitches_pitcher_scores,
            )

            summary_rows.append({
                "Record": "Most Pitches by One Pitcher",
                "Value": self.most_pitches_single_game,
                "Detail": "; ".join(row[1] for row in rows),
                "Score": "; ".join(row[2] for row in rows),
                "GameIDs": join_gameids_in_order(row[0] for row in rows)
            })

        # Most Pitchers Used
        if self.most_pitchers_used > 0:
            rows = sorted_context_rows(
                self.most_pitchers_used_gameids,
                self.most_pitchers_used_details,
                self.most_pitchers_used_scores,
            )
            summary_rows.append({
                "Record": "Most Pitchers Used",
                "Value": self.most_pitchers_used,
                "Detail": "; ".join(row[1] for row in rows),
                "Score": "; ".join(row[2] for row in rows),
                "GameIDs": join_gameids_in_order(row[0] for row in rows)
            })

        # Fewest Pitchers Used
        if self.fewest_pitchers_used != float('inf') and self.fewest_pitchers_used_gameids:
            rows = sorted_context_rows(
                self.fewest_pitchers_used_gameids,
                self.fewest_pitchers_used_details,
                self.fewest_pitchers_used_scores,
            )
            summary_rows.append({
                "Record": "Fewest Pitchers Used",
                "Value": self.fewest_pitchers_used,
                "Detail": "; ".join(row[1] for row in rows),
                "Score": "; ".join(row[2] for row in rows),
                "GameIDs": join_gameids_in_order(row[0] for row in rows)
            })

        # Add most runs in a single inning
        if self.most_runs_in_inning:
            inning_rows = []
            for gid, detail, score in zip(
                self.most_runs_inning_gameids,
                self.most_runs_inning_details,
                self.most_runs_inning_scores,
            ):
                game = next((g for g in self.games if g["game_id"] == gid), None)
                if game:
                    detail = self._format_single_inning_runs_detail(
                        game, detail, self.most_runs_in_inning
                    )
                inning_rows.append((gid, detail, score))

            summary_rows.append({
                "Record": "Most Runs in a Single Inning",
                "Value": self.most_runs_in_inning,
                "Detail": "; ".join(row[1] for row in inning_rows),
                "Score": "; ".join(row[2] for row in inning_rows),
                "GameIDs": ", ".join(row[0] for row in inning_rows)
            })
        
        # Combined team records
        for value, label, ids, stat_key in [
            (self.most_combined_runs, "Most Combined Runs", self.most_combined_runs_gameids, "R"),
            (self.most_combined_hr, "Most Combined HRs", self.most_combined_hr_gameids, "HR"),
            (self.most_combined_hits, "Most Combined Hits", self.most_combined_hits_gameids, "H"),
            (self.most_combined_ks, "Most Combined Pitching Strikeouts", self.most_combined_ks_gameids, "SO"),
            (self.most_sb_combined, "Most Combined SBs in a Game", self.most_sb_combined_gameids, "SB"),
            (self.most_combined_bb, "Most Combined Walks", self.most_combined_bb_gameids, "BB"),
        ]:
            rows = group_games_by_value(value, label, ids, stat_key=stat_key)
            summary_rows.append({
                "Record": label,
                "Value": value,
                "Detail": "; ".join(r["Detail"] for r in rows),
                "Score": "; ".join(r["Score"] for r in rows),
                "GameIDs": ", ".join(r["GameIDs"] for r in rows)
            })

        # Fewest combined strikeouts
        if self.fewest_strikeouts != float('inf'):
            rows = group_games_by_value(
                self.fewest_strikeouts,
                "Fewest Combined Strikeouts",
                self.fewest_strikeouts_gameids,
                stat_key="SO"
            )
            summary_rows.append({
                "Record": "Fewest Combined Strikeouts",
                "Value": self.fewest_strikeouts,
                "Detail": "; ".join(r["Detail"] for r in rows),
                "Score": "; ".join(r["Score"] for r in rows),
                "GameIDs": ", ".join(r["GameIDs"] for r in rows)
            })

        # Fewest hits by one team
        if self.fewest_hits != float('inf'):
            rows = []
            for gid, team_code in zip(self.fewest_hits_gameids, self.fewest_hits_teams):
                game = next(g for g in self.games if g["game_id"] == gid)
                score = self._create_score_string(game["basic_info"])
                detail = f"{team_code} ({self.fewest_hits} H)"
                rows.append({
                    "Detail": detail,
                    "Score": score,
                    "GameIDs": gid
                })

            summary_rows.append({
                "Record": "Fewest Hits by One Team",
                "Value": self.fewest_hits,
                "Detail": "; ".join(r["Detail"] for r in rows),
                "Score": "; ".join(r["Score"] for r in rows),
                "GameIDs": ", ".join(r["GameIDs"] for r in rows)
            })

        # Fewest combined hits
        if self.fewest_combined_hits != float('inf'):
            rows = group_games_by_value(
                self.fewest_combined_hits,
                "Fewest Combined Hits",
                self.fewest_combined_hits_gameids,
                stat_key="H"
            )
            summary_rows.append({
                "Record": "Fewest Combined Hits",
                "Value": self.fewest_combined_hits,
                "Detail": "; ".join(r["Detail"] for r in rows),
                "Score": "; ".join(r["Score"] for r in rows),
                "GameIDs": ", ".join(r["GameIDs"] for r in rows)
            })

        # Inside-the-Park HRs
        if self.inside_park_hrs > 0:
            scores = []
            for gid in self.inside_park_hr_gameids:
                try:
                    game = next(g for g in self.games if g["game_id"] == gid)
                    scores.append(self._create_score_string(game["basic_info"]))
                except Exception:
                    scores.append("")
            rows = sorted_context_rows(self.inside_park_hr_gameids, self.inside_park_hr_details, scores)
            
            summary_rows.append({
                "Record": "Inside-the-Park Home Runs",
                "Value": self.inside_park_hrs,
                "Detail": "; ".join(row[1] for row in rows),
                "Score": "; ".join(row[2] for row in rows),
                "GameIDs": join_gameids_in_order(row[0] for row in rows)
            })

        # Most RBIs in a Game
        if self.most_rbi_gameids:
            rows = []
            for gid, label in zip(self.most_rbi_gameids, self.most_rbi_players):
                game = next(g for g in self.games if g["game_id"] == gid)
                basic_info = game["basic_info"]
                rows.append((gid, label, self._create_score_string(basic_info)))
            rows = sorted(rows, key=lambda row: game_id_sort_key(row[0]))
            summary_rows.append({
                "Record": "Most RBIs in a Game",
                "Value": self.most_rbi,
                "Detail": "; ".join(row[1] for row in rows),
                "Score": "; ".join(row[2] for row in rows),
                "GameIDs": join_gameids_in_order(row[0] for row in rows)
            })
        
        # Most SBs by One Player
        if self.most_sb_player_gameids:
            rows = []
            for gid, label in zip(self.most_sb_player_gameids, self.most_sb_player_labels):
                game = next(g for g in self.games if g["game_id"] == gid)
                basic_info = game["basic_info"]
                rows.append((gid, label, self._create_score_string(basic_info)))
            rows = sorted(rows, key=lambda row: game_id_sort_key(row[0]))
            
            summary_rows.append({
                "Record": "Most SBs by One Player",
                "Value": self.most_sb_player,
                "Detail": "; ".join(row[1] for row in rows),
                "Score": "; ".join(row[2] for row in rows),
                "GameIDs": join_gameids_in_order(row[0] for row in rows)
            })
        
        # Most teams seen for any player (treat ATH and OAK as the same team)
        team_counts = {
            pid: len({ _normalize_team_code_for_counts(code) for code in info["teams"] })
            for pid, info in self.all_players.items()
        }

        if team_counts:
            max_teams = max(team_counts.values())
            most_teams_players = []
            for pid, count in team_counts.items():
                if count == max_teams:
                    name = self.all_players[pid]["name"]
                    # Normalize codes and de-duplicate for display
                    team_list = sorted({ _normalize_team_code_for_counts(code) for code in self.all_players[pid]["teams"] })
                    most_teams_players.append((pid, name, team_list))

            summary_rows.append({
                "Record": "Most Teams Seen for a Player",
                "Value": max_teams,
                "Detail": "; ".join(f"{name} ({', '.join(teams)})" for _, name, teams in most_teams_players),
                "Score": "",
                "GameIDs": ""
            })
        
        # Biggest comeback
        if getattr(self, "biggest_comeback", {}).get("date") and self.biggest_comeback.get("deficit", 0) > 0:
            bc = self.biggest_comeback

            # Abbreviate team names for display
            home_code = standardize_team_code(bc.get("winner", ""))
            away_code = standardize_team_code(bc.get("opponent", ""))

            score_line = bc.get("score_at_deficit", "")
            inning_label = bc.get("half_inning_label", f"Inning {bc.get('deficit_inning', '')}")
            summary_rows.append({
                "Record": "Biggest Comeback",
                "Value": f'{bc["deficit"]} runs',
                "Detail": f'{home_code} came back vs {away_code}: down {bc["deficit"]} after {inning_label} ({score_line})',
                "Score": bc["final_score"],
                "GameIDs": bc.get("game_id", "")
            })

        # Simple tallies that always appear
        games_1_0_rows = sorted_context_rows(self.games_1_0, self.games_1_0_details, self.games_1_0_scores)
        extra_inning_rows = sorted_context_rows(
            self.games_extra_innings, self.extra_inning_details, self.extra_inning_scores
        )
        both_teams_10_rows = sorted_context_rows(
            self.games_both_10_plus, self.both_teams_10_details, self.both_teams_10_scores
        )
        twenty_hit_rows = sorted_context_rows(
            self.games_20_plus_hits, self.twenty_plus_hit_details, self.twenty_plus_hit_scores
        )
        one_run_rows = sorted_context_rows(self.games_one_run, self.one_run_details, self.one_run_scores)
        biggest_victory_rows = sorted_context_rows(
            self.biggest_victory_gameids, self.biggest_victory_details, self.biggest_victory_scores
        )
        ten_plus_run_inning_rows = sorted_context_rows(
            self.ten_plus_run_inning_gameids,
            self.ten_plus_run_inning_details,
            [""] * len(self.ten_plus_run_inning_details),
        )

        summary_rows.extend([
            {
                "Record": "1-0 Games",
                "Value": self.count_1_0,
                "Detail": "; ".join(row[1] for row in games_1_0_rows),
                "Score": "; ".join(row[2] for row in games_1_0_rows),
                "GameIDs": ", ".join(row[0] for row in games_1_0_rows)
            },
            {
                "Record": "Extra Inning Games",
                "Value": self.extra_innings,
                "Detail": "; ".join(row[1] for row in extra_inning_rows),
                "Score": "; ".join(row[2] for row in extra_inning_rows),
                "GameIDs": ", ".join(row[0] for row in extra_inning_rows)
            },
            {
                "Record": "Both Teams 10+ Runs",
                "Value": self.both_teams_10_runs,
                "Detail": "; ".join(row[1] for row in both_teams_10_rows),
                "Score": "; ".join(row[2] for row in both_teams_10_rows),
                "GameIDs": ", ".join(row[0] for row in both_teams_10_rows)
            },
            {
                "Record": "20+ Hit Games by One Team",
                "Value": self.twenty_plus_hit_games,
                "Detail": "; ".join(row[1] for row in twenty_hit_rows),
                "Score": "; ".join(row[2] for row in twenty_hit_rows),
                "GameIDs": ", ".join(row[0] for row in twenty_hit_rows)
            },
            {
                "Record": "10+ Run Innings",
                "Value": self.ten_plus_run_innings,
                "Detail": "; ".join(row[1] for row in ten_plus_run_inning_rows),
                "Score": "",
                "GameIDs": join_gameids_in_order(row[0] for row in ten_plus_run_inning_rows)
            }
        ])

        # Add consecutive HR events with full details (players, inning)
        def _build_consec_hr_rows(df, streak_len):
            rows = []
            for _, row in df.iterrows():
                players = str(row.get("Players", ""))
                inning = str(row.get("Inning", ""))
                hr_count = int(row.get("HR Count", 0)) if pd.notna(row.get("HR Count")) else streak_len
                game_id = str(row.get("GameID", ""))
                summary_detail = row.get("Summary Detail", "")
                detail = str(summary_detail).strip() if pd.notna(summary_detail) else ""
                if not detail:
                    row_detail = row.get("Detail", "")
                    detail = str(row_detail).strip() if pd.notna(row_detail) else ""
                if not detail:
                    detail = f"{inning}: {players}" if inning and players else players or f"{hr_count} consecutive HRs"
                # Try to get score from game data
                try:
                    game = next(g for g in self.games if g["game_id"] == game_id)
                    score = self._create_score_string(game["basic_info"])
                except (StopIteration, KeyError):
                    score = ""
                rows.append((game_id, detail, score))
            return sorted(rows, key=lambda row: game_id_sort_key(row[0]))

        if len(self.b2b_only_df) > 0:
            rows = _build_consec_hr_rows(self.b2b_only_df, 2)
            summary_rows.append({
                "Record": "Back-to-Back HR Events",
                "Value": len(self.b2b_only_df),
                "Detail": "; ".join(row[1] for row in rows),
                "Score": "; ".join(row[2] for row in rows),
                "GameIDs": join_gameids_in_order(row[0] for row in rows)
            })

        if len(self.b2b2b_only_df) > 0:
            rows = _build_consec_hr_rows(self.b2b2b_only_df, 3)
            summary_rows.append({
                "Record": "Back-to-Back-to-Back HR Events",
                "Value": len(self.b2b2b_only_df),
                "Detail": "; ".join(row[1] for row in rows),
                "Score": "; ".join(row[2] for row in rows),
                "GameIDs": join_gameids_in_order(row[0] for row in rows)
            })

        if len(self.b2b2b2b_only_df) > 0:
            rows = _build_consec_hr_rows(self.b2b2b2b_only_df, 4)
            summary_rows.append({
                "Record": "Back-to-Back-to-Back-to-Back HR Events",
                "Value": len(self.b2b2b2b_only_df),
                "Detail": "; ".join(row[1] for row in rows),
                "Score": "; ".join(row[2] for row in rows),
                "GameIDs": join_gameids_in_order(row[0] for row in rows)
            })

        # Player and total statistics
        summary_rows.extend([
            {
                "Record": "Unique Pitchers with a Win",
                "Value": len(self.winning_pitchers_seen),
                "Detail": "",
                "Score": "",
                "GameIDs": ""
            },
            {
                "Record": "Unique Pitchers with a Loss",
                "Value": len(self.pitchers_with_loss),
                "Detail": "",
                "Score": "",
                "GameIDs": ""
            },
            {
                "Record": "Unique Pitchers with a Save",
                "Value": len(self.pitchers_with_save),
                "Detail": "",
                "Score": "",
                "GameIDs": ""
            },
            {
                "Record": "Unique Players with a Hit",
                "Value": len(self.players_with_hit),
                "Detail": "",
                "Score": "",
                "GameIDs": ""
            },
            {
                "Record": "Unique Players with a Home Run", 
                "Value": len(self.players_with_hr),
                "Detail": "",
                "Score": "",
                "GameIDs": ""
            },
            {
                "Record": "Total Hits Across All Games",
                "Value": self.total_hits,
                "Detail": "",
                "Score": "",
                "GameIDs": ""
            },
            {
                "Record": "Total Home Runs Across All Games",
                "Value": self.total_hr,
                "Detail": "",
                "Score": "",
                "GameIDs": ""
            },
            {
                "Record": "Total Runs Across All Games",
                "Value": self.total_runs,
                "Detail": "",
                "Score": "",
                "GameIDs": ""
            },
            {
                "Record": "Total Strikeouts Across All Games",
                "Value": self.total_ks,
                "Detail": "",
                "Score": "",
                "GameIDs": ""
            },
            {
                "Record": "Total Stolen Bases Across All Games",
                "Value": self.total_sb,
                "Detail": "",
                "Score": "",
                "GameIDs": ""
            }
        ])

        summary_rows.append({
            "Record": "1-Run Games",
            "Value": self.one_run_games,
            "Detail": "; ".join(row[1] for row in one_run_rows),
            "Score": "; ".join(row[2] for row in one_run_rows),
            "GameIDs": ", ".join(row[0] for row in one_run_rows)
        })

        if self.biggest_victory_margin > 0:
            summary_rows.append({
                "Record": "Biggest Victory",
                "Value": self.biggest_victory_margin,
                "Detail": "; ".join(row[1] for row in biggest_victory_rows),
                "Score": "; ".join(row[2] for row in biggest_victory_rows),
                "GameIDs": ", ".join(row[0] for row in biggest_victory_rows)
            })

        # Add percent of possible matchups seen (with exact count)
        seen_pairs = set()
        teams = df_matchups.index.tolist()

        for i, team_a in enumerate(teams):
            for j, team_b in enumerate(teams):
                if i >= j:
                    continue  # Skip duplicates and self-matchups
                val = df_matchups.loc[team_a, team_b]
                if isinstance(val, (int, float)) and val > 0:
                    seen_pairs.add(frozenset([team_a, team_b]))

        num_seen = len(seen_pairs)
        num_possible = len(teams) * (len(teams) - 1) // 2
        percent_seen = num_seen / num_possible if num_possible else 0

        summary_rows.append({
            "Record": "Percent of Possible Matchups Seen",
            "Value": f"{num_seen} / {num_possible} ({percent_seen:.2%})",
            "Detail": "",
            "Score": "",
            "GameIDs": ""
        })

        # Fewest Combined Walks
        if self.fewest_combined_bb != float('inf'):
            rows = group_games_by_value(
                self.fewest_combined_bb,
                "Fewest Combined Walks",
                self.fewest_combined_bb_gameids,
                stat_key="BB"
            )
            if rows:
                summary_rows.append({
                    "Record": "Fewest Combined Walks",
                    "Value": self.fewest_combined_bb,
                    "Detail": "; ".join(r["Detail"] for r in rows),
                    "Score": "; ".join(r["Score"] for r in rows),
                    "GameIDs": ", ".join(r["GameIDs"] for r in rows)
                })

        # --- Game Environment summary rows ---
        if self.coldest_temp != float('inf') and self.coldest_temp_gameids:
            rows = sorted_context_rows(
                self.coldest_temp_gameids,
                [""] * len(self.coldest_temp_gameids),
                self.coldest_temp_scores,
            )
            summary_rows.append({
                "Record": "Coldest Game",
                "Value": f"{self.coldest_temp}°F",
                "Detail": "",
                "Score": "; ".join(row[2] for row in rows),
                "GameIDs": join_gameids_in_order(row[0] for row in rows)
            })

        if self.hottest_temp != float('-inf') and self.hottest_temp_gameids:
            rows = sorted_context_rows(
                self.hottest_temp_gameids,
                [""] * len(self.hottest_temp_gameids),
                self.hottest_temp_scores,
            )
            summary_rows.append({
                "Record": "Hottest Game",
                "Value": f"{self.hottest_temp}°F",
                "Detail": "",
                "Score": "; ".join(row[2] for row in rows),
                "GameIDs": join_gameids_in_order(row[0] for row in rows)
            })
        if self.all_temperatures:
            avg_temp = round(sum(self.all_temperatures) / len(self.all_temperatures))
            summary_rows.append({
                "Record": "Average Temperature",
                "Value": f"{avg_temp}°F",
                "Detail": f"Based on {len(self.all_temperatures)} games with temperature data",
                "Score": "",
                "GameIDs": ""
            })

        if self.longest_innings > 0 and self.longest_innings_gameids:
            rows = sorted_context_rows(
                self.longest_innings_gameids,
                [""] * len(self.longest_innings_gameids),
                self.longest_innings_scores,
            )
            summary_rows.append({
                "Record": "Longest Game by Innings",
                "Value": self.longest_innings,
                "Detail": "",
                "Score": "; ".join(row[2] for row in rows),
                "GameIDs": join_gameids_in_order(row[0] for row in rows)
            })

        if self.longest_time_min > 0 and self.longest_time_gameids:
            hours = self.longest_time_min // 60
            mins = self.longest_time_min % 60
            rows = sorted_context_rows(
                self.longest_time_gameids,
                [""] * len(self.longest_time_gameids),
                self.longest_time_scores,
            )
            summary_rows.append({
                "Record": "Longest Game by Time",
                "Value": f"{hours}:{mins:02d}",
                "Detail": "",
                "Score": "; ".join(row[2] for row in rows),
                "GameIDs": join_gameids_in_order(row[0] for row in rows)
            })

        if self.shortest_time_min != float('inf') and self.shortest_time_gameids:
            hours = self.shortest_time_min // 60
            mins = self.shortest_time_min % 60
            rows = sorted_context_rows(
                self.shortest_time_gameids,
                [""] * len(self.shortest_time_gameids),
                self.shortest_time_scores,
            )
            summary_rows.append({
                "Record": "Shortest Game by Time",
                "Value": f"{hours}:{mins:02d}",
                "Detail": "",
                "Score": "; ".join(row[2] for row in rows),
                "GameIDs": join_gameids_in_order(row[0] for row in rows)
            })

        # Average attendance
        if self.all_attendance_values:
            avg_attendance = round(sum(self.all_attendance_values) / len(self.all_attendance_values))
            summary_rows.append({
                "Record": "Average Attendance",
                "Value": f"{avg_attendance:,}",  # Format with commas
                "Detail": f"Based on {len(self.all_attendance_values)} games with attendance data",
                "Score": "",
                "GameIDs": ""
            })

        # Highest attendance
        if self.highest_attendance > 0 and self.highest_attendance_gameids:
            rows = sorted_context_rows(
                self.highest_attendance_gameids,
                [""] * len(self.highest_attendance_gameids),
                self.highest_attendance_scores,
            )
            summary_rows.append({
                "Record": "Highest Attendance",
                "Value": f"{self.highest_attendance:,}",  # Format with commas
                "Detail": "",
                "Score": "; ".join(row[2] for row in rows),
                "GameIDs": join_gameids_in_order(row[0] for row in rows)
            })
        
        # Lowest attendance  
        if self.lowest_attendance != float('inf') and self.lowest_attendance_gameids:
            rows = sorted_context_rows(
                self.lowest_attendance_gameids,
                [""] * len(self.lowest_attendance_gameids),
                self.lowest_attendance_scores,
            )
            summary_rows.append({
                "Record": "Lowest Attendance",
                "Value": f"{self.lowest_attendance:,}",  # Format with commas
                "Detail": "",
                "Score": "; ".join(row[2] for row in rows),
                "GameIDs": join_gameids_in_order(row[0] for row in rows)
            })

        # Individual Hitting Milestones
        hitting_milestones = [
            ("4+ Hit Games", "4+ Hit Games"),
            ("5+ RBI Games", "5+ RBI Games"), 
            ("Multi-HR Games", "Multi-HR Games"),
            ("Cycles", "Cycles"),
        ]

        for record_name, milestone_key in hitting_milestones:
            milestone_df = self.milestones.get(milestone_key, pd.DataFrame())
            milestone_count = len(milestone_df) if not milestone_df.empty else 0
            
            # Only add if count > 0 (exclude empty milestones)
            if milestone_count > 0:
                milestone_game_ids = ""
                if "GameID" in milestone_df.columns:
                    unique_game_ids = sorted(milestone_df["GameID"].unique())
                    milestone_game_ids = join_sorted_gameids(unique_game_ids)
                
                milestone_detail = f"{milestone_count} instances across dataset"
                if "Player" in milestone_df.columns:
                    unique_players = len(milestone_df["Player"].unique())
                    milestone_detail = f"{milestone_count} instances by {unique_players} different players"
                
                summary_rows.append({
                    "Record": record_name,
                    "Value": milestone_count,
                    "Detail": milestone_detail,
                    "Score": "",
                    "GameIDs": milestone_game_ids
                })

        # Individual Pitching Milestones - FIXED with proper variable isolation
        pitching_milestones = [
            ("10+ K Games", "10+ K Games"),
            ("Complete Games", "Complete Games"),
            ("Shutouts", "Shutouts"),
            ("Quality Starts", "Quality Starts"),
            ("No-Hitters", "No-Hitters"),
        ]

        # Handle Complete Games & Shutouts from combined sheet
        cg_shutouts_df = self.milestones.get("Complete Games & Shutouts", pd.DataFrame())

        for record_name, milestone_key in pitching_milestones:
            # FIXED: Declare fresh variables for each iteration
            pitch_count = 0
            pitch_game_ids = ""
            pitch_detail = ""
            
            if record_name == "Complete Games" and not cg_shutouts_df.empty:
                if "CG" in cg_shutouts_df.columns:
                    cg_records = cg_shutouts_df[cg_shutouts_df["CG"].astype(bool)]
                    pitch_count = len(cg_records)
                    if pitch_count > 0 and "GameID" in cg_records.columns:
                        unique_ids = sorted(cg_records["GameID"].unique())
                        pitch_game_ids = join_sorted_gameids(unique_ids)
                        
            elif record_name == "Shutouts" and not cg_shutouts_df.empty:
                if "SHO" in cg_shutouts_df.columns:
                    sho_records = cg_shutouts_df[cg_shutouts_df["SHO"].astype(bool)]
                    pitch_count = len(sho_records)
                    if pitch_count > 0 and "GameID" in sho_records.columns:
                        unique_ids = sorted(sho_records["GameID"].unique())
                        pitch_game_ids = join_sorted_gameids(unique_ids)
                        
            else:
                # Regular milestone processing
                milestone_df = self.milestones.get(milestone_key, pd.DataFrame())
                pitch_count = len(milestone_df) if not milestone_df.empty else 0
                
                if pitch_count > 0 and not milestone_df.empty and "GameID" in milestone_df.columns:
                    unique_ids = sorted(milestone_df["GameID"].unique())
                    
                    # FIXED: Special handling for high-volume milestones like Quality Starts
                    if pitch_count > 50:  # For very common milestones
                        pitch_game_ids = ""  # Don't show Game IDs - too many
                        if "Player" in milestone_df.columns:
                            unique_players = len(milestone_df["Player"].unique())
                            pitch_detail = f"{pitch_count} instances by {unique_players} different player{'s' if unique_players != 1 else ''}"
                        else:
                            pitch_detail = f"{pitch_count} instances across dataset (Game IDs omitted due to volume)"
                    else:
                        pitch_game_ids = join_sorted_gameids(unique_ids)
                        if "Player" in milestone_df.columns:
                            unique_players = len(milestone_df["Player"].unique())
                            pitch_detail = f"{pitch_count} instances by {unique_players} different player{'s' if unique_players != 1 else ''}"
                        else:
                            pitch_detail = f"{pitch_count} instances across dataset"
                else:
                    pitch_detail = f"{pitch_count} instances across dataset"
            
            # FIXED: Only add if count > 0 (this prevents "No-Hitters: 0" from appearing)
            if pitch_count > 0:
                if not pitch_detail:  # Set default detail if not set above
                    pitch_detail = f"{pitch_count} instances across dataset"
                    
                summary_rows.append({
                    "Record": record_name,
                    "Value": pitch_count,
                    "Detail": pitch_detail,
                    "Score": "",
                    "GameIDs": pitch_game_ids
                })
        
        # Statistical Leaders Section
        print("   📈 Adding statistical leaders...")
        
        # Hitting Leaders
        hitting_stats = [
            ("H", "Hits Leaders"),
            ("R", "Runs Leaders"), 
            ("HR", "Home Run Leaders"),
            ("RBI", "RBI Leaders"),
            ("2B", "Doubles Leaders"),
            ("3B", "Triples Leaders"),
            ("SB", "Stolen Base Leaders"),
            ("BB", "Walks Leaders (Hitting)"),
        ]
        
        for stat_col, record_name in hitting_stats:
            leaders = self._get_stat_leaders(self.hitters_df, stat_col)
            if leaders:
                summary_rows.append({
                    "Record": record_name,
                    "Value": "",
                    "Detail": "; ".join(leaders),
                    "Score": "",
                    "GameIDs": ""
                })
        
        # Batting Average Leaders (minimum plate appearances)
        if "AVG" in self.hitters_df.columns and "AB" in self.hitters_df.columns:
            df_qualified = self.hitters_df.copy()
            df_qualified["AB"] = pd.to_numeric(df_qualified["AB"], errors='coerce').fillna(0)
            df_qualified["AVG"] = pd.to_numeric(df_qualified["AVG"], errors='coerce').fillna(0)
            
            qualified_hitters = df_qualified[df_qualified["AB"] >= 10]
            if not qualified_hitters.empty:
                avg_leaders = self._get_stat_leaders(qualified_hitters, "AVG")
                if avg_leaders:
                    summary_rows.append({
                        "Record": "Batting Average Leaders (min. 10 AB)",
                        "Value": "",
                        "Detail": "; ".join(avg_leaders),
                        "Score": "",
                        "GameIDs": ""
                    })
        
        # OBP Leaders (minimum plate appearances)
        if "OBP" in self.hitters_df.columns and "AB" in self.hitters_df.columns:
            df_qualified = self.hitters_df.copy()
            df_qualified["AB"] = pd.to_numeric(df_qualified["AB"], errors='coerce').fillna(0)
            df_qualified["OBP"] = pd.to_numeric(df_qualified["OBP"], errors='coerce').fillna(0)
            
            qualified_hitters = df_qualified[df_qualified["AB"] >= 10]
            if not qualified_hitters.empty:
                obp_leaders = self._get_stat_leaders(qualified_hitters, "OBP")
                if obp_leaders:
                    summary_rows.append({
                        "Record": "On-Base Percentage Leaders (min. 10 AB)",
                        "Value": "",
                        "Detail": "; ".join(obp_leaders),
                        "Score": "",
                        "GameIDs": ""
                    })
        
        # OPS Leaders (minimum plate appearances)
        if "OPS" in self.hitters_df.columns and "AB" in self.hitters_df.columns:
            df_qualified = self.hitters_df.copy()
            df_qualified["AB"] = pd.to_numeric(df_qualified["AB"], errors='coerce').fillna(0)
            df_qualified["OPS"] = pd.to_numeric(df_qualified["OPS"], errors='coerce').fillna(0)
            
            qualified_hitters = df_qualified[df_qualified["AB"] >= 10]
            if not qualified_hitters.empty:
                ops_leaders = self._get_stat_leaders(qualified_hitters, "OPS")
                if ops_leaders:
                    summary_rows.append({
                        "Record": "OPS Leaders (min. 10 AB)",
                        "Value": "",
                        "Detail": "; ".join(ops_leaders),
                        "Score": "",
                        "GameIDs": ""
                    })
        
        # Pitching Leaders
        pitching_stats = [
            ("W", "Wins Leaders"),
            ("SO", "Strikeout Leaders (Pitching)"),
            ("SV", "Save Leaders"),
            ("IP", "Innings Pitched Leaders")
        ]
        
        for stat_col, record_name in pitching_stats:
            leaders = self._get_stat_leaders(self.pitchers_df, stat_col)
            if leaders:
                summary_rows.append({
                    "Record": record_name,
                    "Value": "",
                    "Detail": "; ".join(leaders),
                    "Score": "",
                    "GameIDs": ""
                })
        
        # ERA Leaders (minimum innings pitched)
        if "ERA" in self.pitchers_df.columns and "IP" in self.pitchers_df.columns:
            df_qualified = self.pitchers_df.copy()
            df_qualified["IP"] = pd.to_numeric(df_qualified["IP"], errors='coerce').fillna(0)
            df_qualified["ERA"] = pd.to_numeric(df_qualified["ERA"], errors='coerce').fillna(999)
            
            qualified_pitchers = df_qualified[df_qualified["IP"] >= 10]
            if not qualified_pitchers.empty:
                era_leaders = self._get_stat_leaders(qualified_pitchers, "ERA", ascending=True)
                if era_leaders:
                    summary_rows.append({
                        "Record": "ERA Leaders (min. 10 IP)",
                        "Value": "",
                        "Detail": "; ".join(era_leaders),
                        "Score": "",
                        "GameIDs": ""
                    })
        
        print(f"   ✅ Added statistical leaders")

        # Add enhanced statistics if trackers are available
        if self.weather_tracker:
            weather_stats = self.weather_tracker.get_summary_stats()
            
            summary_rows.extend([
                {
                    "Record": "Highest Wind Speed",
                    "Value": weather_stats["highest_wind_speed"],
                    "Detail": f"{len(self.weather_tracker.highest_wind_games)} games",
                    "Score": "",
                    "GameIDs": sort_gameids_in_context_order(self.weather_tracker.highest_wind_games)
                },
                {
                    "Record": "Average Wind Speed",
                    "Value": weather_stats.get("average_wind_speed", "N/A"),
                    "Detail": f"Based on {len(self.weather_tracker.wind_conditions)} games with wind data",
                    "Score": "",
                    "GameIDs": ""
                },
                {
                    "Record": "Day Games vs Night Games",
                    "Value": f"{weather_stats['day_games']} day / {weather_stats['night_games']} night",
                    "Detail": "",
                    "Score": "",
                    "GameIDs": ""
                },
                {
                    "Record": "Earliest Start Time",
                    "Value": weather_stats["earliest_start"],
                    "Detail": "",
                    "Score": "",
                    "GameIDs": sort_gameids_in_context_order(self.weather_tracker.earliest_start_games) if self.weather_tracker.earliest_start_games else ""
                },
                {
                    "Record": "Latest Start Time",
                    "Value": weather_stats["latest_start"],
                    "Detail": "",
                    "Score": "",
                    "GameIDs": sort_gameids_in_context_order(self.weather_tracker.latest_start_games) if self.weather_tracker.latest_start_games else ""
                },
                {
                    "Record": "Games with Precipitation",
                    "Value": weather_stats["precipitation_games"],
                    "Detail": "",
                    "Score": "",
                    "GameIDs": sort_gameids_in_context_order(self.weather_tracker.precipitation_games)
                },
                {
                    "Record": "Weekend vs Weekday Games",
                    "Value": f"{weather_stats['weekend_games']} weekend / {weather_stats['weekday_games']} weekday",
                    "Detail": "",
                    "Score": "",
                    "GameIDs": ""
                }
            ])
        
        if self.saber_tracker:
            saber_stats = self.saber_tracker.get_summary_stats()
            
            # Most Clutch Single Game
            most_clutch = saber_stats.get("most_clutch_single_game")
            if most_clutch:
                summary_rows.append({
                    "Record": "Most Clutch Single Game (WPA)",
                    "Value": f"{most_clutch['wpa']:.3f}",
                    "Detail": f"{most_clutch['name']} ({most_clutch['team']} vs {most_clutch['opponent']}) on {most_clutch['date']}",
                    "Score": "",
                    "GameIDs": most_clutch['game_id']
                })
            
            # Top WPA Leaders
            wpa_leaders = saber_stats["wpa_leaders"][:3]
            if wpa_leaders:
                leader_detail = "; ".join([
                    f"{p['name']} ({p['total_wpa']:.3f} total, {p['avg_wpa']:.3f} avg)"
                    for p in wpa_leaders
                ])
                summary_rows.append({
                    "Record": "Career WPA Leaders (Top 3)",
                    "Value": "",
                    "Detail": leader_detail,
                    "Score": "",
                    "GameIDs": ""
                })
        
        if self.situation_tracker:
            situation_stats = self.situation_tracker.get_summary_stats()
            
            summary_rows.extend([
                {
                    "Record": "Players with RISP Opportunities",
                    "Value": situation_stats["players_with_risp_opportunities"],
                    "Detail": "Minimum 5 AB with runners in scoring position",
                    "Score": "",
                    "GameIDs": ""
                },
                {
                    "Record": "Players with Bases Loaded Opportunities",
                    "Value": situation_stats["players_with_bases_loaded_opportunities"],
                    "Detail": "At least 1 AB with bases loaded",
                    "Score": "",
                    "GameIDs": ""
                }
            ])

        return summary_rows
    
    def _safe_int(self, value):
        try:
            return int(value or 0)
        except (TypeError, ValueError):
            return 0

    def _team_side_from_code(self, basic_info, team_code):
        target = unify_team_code(team_code or "")
        for side in ("away", "home"):
            if unify_team_code(basic_info.get(f"{side}_team_code", "")) == target:
                return side
        return ""

    def _side_opponent(self, side):
        return "home" if side == "away" else "away"

    def _team_line_stats(self, game, side):
        line = game.get("linescore", {}).get(side, {})
        return {
            "runs": self._safe_int(line.get("R", 0)),
            "hits": self._safe_int(line.get("H", 0)),
        }

    def _format_player_counts(self, player_counts):
        return [
            f"{name} ({count})" if count > 1 else name
            for name, count in player_counts
        ]

    def _team_hr_breakdown(self, game, side):
        footer_blob = game.get("footer_summary", {}).get(side, {}).get("HR", "")
        footer_counts = ExcelGeneratorUtils.extract_stat_counts(footer_blob)
        footer_total = sum(count for _, count in footer_counts)

        box_counts = [
            (player.get("name", "Unknown"), self._safe_int(player.get("HR", 0)))
            for player in game.get("batting", {}).get(side, [])
            if self._safe_int(player.get("HR", 0)) > 0
        ]
        box_total = sum(count for _, count in box_counts)

        if footer_counts:
            return max(footer_total, box_total), self._format_player_counts(footer_counts)
        return box_total, self._format_player_counts(box_counts)

    def _team_sb_breakdown(self, game, side):
        footer_blob = game.get("footer_summary", {}).get(side, {}).get("SB", "")
        footer_counts = ExcelGeneratorUtils.extract_stat_counts(footer_blob)
        footer_total = sum(count for _, count in footer_counts)

        box_counts = [
            (player.get("name", "Unknown"), self._safe_int(player.get("SB", 0)))
            for player in game.get("batting", {}).get(side, [])
            if self._safe_int(player.get("SB", 0)) > 0
        ]
        box_total = sum(count for _, count in box_counts)

        if footer_counts:
            return max(footer_total, box_total), self._format_player_counts(footer_counts)
        return box_total, self._format_player_counts(box_counts)

    def _format_team_big_inning(self, game, side):
        innings = game.get("linescore", {}).get(side, {}).get("innings", []) or []
        runs_by_inning = [self._safe_int(value) for value in innings]
        if not runs_by_inning:
            return ""

        max_runs = max(runs_by_inning)
        if max_runs <= 0:
            return ""

        inning = runs_by_inning.index(max_runs) + 1
        half = "Top" if side == "away" else "Bottom"
        run_word = "run" if max_runs == 1 else "runs"
        return f"{max_runs} {run_word} in {half} {inning}"

    def _format_single_team_record_detail(self, game, team_code, stat_key, value, label):
        basic_info = game["basic_info"]
        side = self._team_side_from_code(basic_info, team_code)
        code = unify_team_code(team_code or "")
        game_context = self._format_game_run_hit_detail(basic_info, game.get("linescore", {}))
        if not side:
            return f"{code} {value} {stat_key} - {game_context}"

        team_line = self._team_line_stats(game, side)
        opp_side = self._side_opponent(side)
        opp_code = unify_team_code(basic_info.get(f"{opp_side}_team_code", ""))

        if stat_key == "R":
            detail = f"{code} scored {value} runs"
            if team_line["hits"]:
                detail += f" on {team_line['hits']} hits"
            big_inning = self._format_team_big_inning(game, side)
            if big_inning:
                detail += f", including {big_inning}"
            return f"{detail} - {game_context}"

        if stat_key == "H":
            return f"{code} had {value} hits and {team_line['runs']} runs - {game_context}"

        if stat_key == "HR":
            _, players = self._team_hr_breakdown(game, side)
            players_text = f": {', '.join(players)}" if players else ""
            return f"{code} hit {value} HR{players_text} - {game_context}"

        if stat_key == "SO":
            return f"{code} pitchers struck out {value} {opp_code} hitters - {game_context}"

        if stat_key == "BB":
            return f"{code} pitchers issued {value} walks - {game_context}"

        if stat_key == "SB":
            _, players = self._team_sb_breakdown(game, side)
            players_text = f": {', '.join(players)}" if players else ""
            return f"{code} stole {value} bases{players_text} - {game_context}"

        return f"{code} {value} {label} - {game_context}"

    def _format_single_inning_runs_detail(self, game, detail, value):
        match = re.match(r"([^ ]+) \((\d+)\) in (\d+)", str(detail or ""))
        if not match:
            return detail

        team_code = match.group(1)
        inning = int(match.group(3))
        basic_info = game["basic_info"]
        side = self._team_side_from_code(basic_info, team_code)
        half = "Top" if side == "away" else "Bottom"
        team_line = self._team_line_stats(game, side) if side else {"runs": 0, "hits": 0}
        game_context = self._format_game_run_hit_detail(basic_info, game.get("linescore", {}))
        hit_context = f" on {team_line['hits']} hits" if team_line["hits"] else ""
        return (
            f"{unify_team_code(team_code)} scored {value} runs in {half} {inning}, "
            f"{team_line['runs']} runs{hit_context} for the game - {game_context}"
        )

    def _make_combined_detail(self, game, stat_key):
        """Create combined detail string for team statistics."""
        basic_info = game['basic_info']
        a_code = basic_info['away_team_code']
        h_code = basic_info['home_team_code']
        
        if stat_key == "HR":
            hr_a, players_a = self._team_hr_breakdown(game, "away")
            hr_h, players_h = self._team_hr_breakdown(game, "home")
            
            # Build detail string with team totals and player names
            detail_parts = []
            if hr_a > 0:
                if players_a:
                    players_str = ", ".join(players_a)
                    detail_parts.append(f"{a_code} {hr_a} HR: {players_str}")
                else:
                    detail_parts.append(f"{a_code} {hr_a} HR")
            
            if hr_h > 0:
                if players_h:
                    players_str = ", ".join(players_h)
                    detail_parts.append(f"{h_code} {hr_h} HR: {players_str}")
                else:
                    detail_parts.append(f"{h_code} {hr_h} HR")
            
            combined_hr = hr_a + hr_h
            hr_label = "HR" if combined_hr == 1 else "HRs"
            return f"{combined_hr} combined {hr_label} - {' / '.join(detail_parts)} - {self._format_game_run_hit_detail(basic_info, game.get('linescore', {}))}"
        
        elif stat_key == "H":
            a_val = game["linescore"]["away"].get("H", 0)
            h_val = game["linescore"]["home"].get("H", 0)
            innings_played = max(
                len(game.get("linescore", {}).get("away", {}).get("innings", []) or []),
                len(game.get("linescore", {}).get("home", {}).get("innings", []) or []),
            )
            innings_label = f" ({innings_played} innings)" if innings_played > 9 else ""
            total = self._safe_int(a_val) + self._safe_int(h_val)
            return f"{total} total hits: {a_code} {a_val} H, {h_code} {h_val} H{innings_label}"
        elif stat_key == "SO":
            a_val = sum(p.get("SO", 0) for p in game["pitching"]["away"])
            h_val = sum(p.get("SO", 0) for p in game["pitching"]["home"])
        elif stat_key == "BB":
            a_val = sum(p.get("BB", 0) for p in game.get("pitching", {}).get("away", []))
            h_val = sum(p.get("BB", 0) for p in game.get("pitching", {}).get("home", []))
        elif stat_key == "SB":
            fs = game.get("footer_summary", {})
            raw_a = fs.get("away", {}).get("SB", "")
            raw_h = fs.get("home", {}).get("SB", "")
            
            def parse_sb(blob):
                return sum(int(n) for n in re.findall(r"\((\d+)\)", blob)) or len(blob.split(";")) if blob else 0
            
            sb_a = parse_sb(raw_a)
            sb_h = parse_sb(raw_h)
            a_val, h_val = sb_a, sb_h
        else:  # "R"
            a_val = game["linescore"]["away"].get("R", 0)
            h_val = game["linescore"]["home"].get("R", 0)
            return self._format_game_run_hit_detail(basic_info, game.get("linescore", {}))

        labels = {
            "R": "runs",
            "H": "hits",
            "SO": "strikeouts",
            "BB": "walks",
            "SB": "stolen bases",
        }
        label = labels.get(stat_key, stat_key)
        total = self._safe_int(a_val) + self._safe_int(h_val)
        return (
            f"{total} combined {label} - {a_code} {a_val}, {h_code} {h_val} - "
            f"{self._format_game_run_hit_detail(basic_info, game.get('linescore', {}))}"
        )
    
    def _process_matchup_analysis(self):
        """Process matchup analysis and create matchup matrix."""
        team_name_map = {
            "Florida Marlins": "Miami Marlins",
            "Cleveland Indians": "Cleveland Guardians",
            "Tampa Bay Devil Rays": "Tampa Bay Rays",
            "Los Angeles Angels of Anaheim": "Los Angeles Angels",
            "Athletics": "Oakland Athletics",
        }

        def parse_game_date(game):
            raw = game.get("basic_info", {}).get("date")
            try:
                return datetime.strptime(raw, "%A, %B %d, %Y")
            except Exception:
                try:
                    return datetime.strptime(raw, "%B %d, %Y")
                except Exception:
                    return datetime.min

        # Include spring training matchups — the user has attended those
        # games, so the pairings count. The mlb_team_codes intersection below
        # still drops non-MLB clubs (e.g. Diablos Rojos / MTY).
        source_games = getattr(self, '_all_games_with_spring', self.games)
        sorted_games = sorted(source_games, key=parse_game_date)

        first_seen_matchups = {}
        normalized_teams = set()
        matchup_counts = defaultdict(int)

        for game in sorted_games:
            info = game.get("basic_info", {})
            home = team_name_map.get(info.get("home_team", ""), info.get("home_team", ""))
            away = team_name_map.get(info.get("away_team", ""), info.get("away_team", ""))
            date_str = info.get("date")
            date_obj = parse_game_date(game)

            if home and away and home != away:
                matchup = tuple(sorted((home, away)))
                normalized_teams.update([home, away])
                if matchup not in first_seen_matchups:
                    first_seen_matchups[matchup] = (date_obj, date_str)
                matchup_counts[matchup] += 1

        # Standard MLB team codes (30 current teams)
        mlb_team_codes = {
            'LAA', 'BAL', 'BOS', 'CWS', 'CLE', 'DET', 'HOU', 'KC',
            'MIN', 'NYY', 'OAK', 'SEA', 'TB', 'TEX', 'TOR',
            'ARI', 'ATL', 'CHC', 'CIN', 'COL', 'MIA', 'LAD', 'MIL',
            'WAS', 'NYM', 'PHI', 'PIT', 'SD', 'SF', 'STL',
            'ATH',  # Athletics alternate code
        }
        all_codes = {standardize_team_code(name) for name in normalized_teams}
        # Also unify ATH -> OAK
        all_codes = {unify_team_code(c) for c in all_codes}
        team_list = sorted(all_codes & mlb_team_codes)

        # Precompute a mapping from standardized code -> one representative full name
        code_to_name = {}
        for full_name in normalized_teams:
            code = unify_team_code(standardize_team_code(full_name))
            code_to_name.setdefault(code, full_name)

        # Rebuild matchup_counts with unified codes
        unified_matchup_counts = defaultdict(int)
        for (name_a, name_b), count in matchup_counts.items():
            code_a = unify_team_code(standardize_team_code(name_a))
            code_b = unify_team_code(standardize_team_code(name_b))
            key = tuple(sorted((code_a, code_b)))
            unified_matchup_counts[key] += count

        matchup_data = []
        for row_code in team_list:
            row = {}
            for col_code in team_list:
                if row_code == col_code:
                    row[col_code] = "X"
                else:
                    key = tuple(sorted((row_code, col_code)))
                    row[col_code] = unified_matchup_counts.get(key, "")
            matchup_data.append(row)

        df_matchups = pd.DataFrame(matchup_data, index=team_list)
        df_matchups.index.name = "Team"
        return df_matchups                            
