import calendar
import logging
import re
import pandas as pd
from collections import defaultdict, Counter
from datetime import datetime
from ..excel.generators import ExcelGeneratorUtils
from ..utils.helpers import standardize_team_code, join_sorted_gameids, unify_team_code, safe_get_int, safe_get_str
from ..utils.constants import STADIUM_ALIASES
from .base_processor import BaseProcessor


class StadiumRecordsProcessor(BaseProcessor):
    """Handle stadium and team records processing with enhanced stadium information."""

    def __init__(self, games):
        super().__init__(games)
        
    def process_stadium_and_team_records(self):
        """Process stadium and team records for Stadiums, Orioles, and Team Records tabs."""
        print("🏟️ Processing stadium and team records...")
        
        # Initialize tracking dictionaries with enhanced data
        stadium_tracker = defaultdict(lambda: {
            "Games": 0, "IDs": [], "dates": [], "attendance": [], "durations": [],
            "temperatures": [], "teams": set(), "scores": [], "start_times": [],
            "home_wins": 0, "home_losses": 0, "total_hrs": 0, "total_hits": 0, "total_strikeouts": 0
        })
        
        # Initialize enhanced Orioles tracking
        orioles_tracker = defaultdict(lambda: {
            "Games": 0, "Wins": 0, "Losses": 0, "IDs": [],
            # Visit History
            "dates": [],
            # Attendance & Environment  
            "attendance": [], "temperatures": [],
            # Orioles Offensive Performance
            "orioles_runs": 0, "highest_scoring_game": {"runs": 0, "score": "", "game_id": ""},
            "orioles_hrs": 0, "orioles_hits": 0,
            # Orioles Pitching Performance
            "runs_allowed": 0, "orioles_strikeouts": 0,
            # Game Characteristics
            "one_run_games": 0, "one_run_wins": 0, "one_run_losses": 0,
            "blowout_games": 0, "blowout_wins": 0, "blowout_losses": 0,
            "extra_inning_games": 0, "extra_inning_wins": 0, "extra_inning_losses": 0,
            "walkoff_games": 0, "walkoff_wins": 0, "walkoff_losses": 0
        })
        
        team_tracker = defaultdict(lambda: {"Games": 0, "Wins": 0, "Losses": 0, "IDs": []})
        
        # Process each game
        for game in self.games:
            try:
                basic_info = game.get("basic_info", {})
                away_code = safe_get_str(basic_info, "away_team_code", "UNK")
                home_code = safe_get_str(basic_info, "home_team_code", "UNK")
                unified_away = unify_team_code(away_code)
                unified_home = unify_team_code(home_code)

                self._process_game_records_enhanced(game, stadium_tracker, orioles_tracker, team_tracker)
            except Exception as e:
                game_id = safe_get_str(game, "game_id", "UNKNOWN")
                logging.warning(f"Error processing records for game {game_id}: {e}")
                continue

        
        # Create DataFrames
        stadiums_df = self._create_enhanced_stadiums_dataframe(stadium_tracker)
        orioles_df = self._create_orioles_dataframe(orioles_tracker) 
        team_records_df = self._create_team_records_dataframe(team_tracker)
        
        print(f"   ✅ Processed {len(stadiums_df)} stadiums, {len(orioles_df)} Orioles venues, {len(team_records_df)} team records")
        
        return stadiums_df, orioles_df, team_records_df
    
    def _process_game_records_enhanced(self, game, stadium_tracker, orioles_tracker, team_tracker):
        """Process records for a single game with enhanced stadium data collection."""
        basic_info = game.get("basic_info", {})
        if not basic_info:
            return
            
        game_id = safe_get_str(game, "game_id", "UNKNOWN")
        
        # Get venue information
        raw_venue = safe_get_str(basic_info, "venue", "Unknown Venue")
        venue = self._unify_stadium_name(raw_venue)
        
        # Get team information
        away_team_code = safe_get_str(basic_info, "away_team_code", "UNK")
        home_team_code = safe_get_str(basic_info, "home_team_code", "UNK")
        away_score = safe_get_int(basic_info, "away_score_value", 0)
        home_score = safe_get_int(basic_info, "home_score_value", 0)
        
        # Unify team codes
        away_team_code = unify_team_code(away_team_code)
        home_team_code = unify_team_code(home_team_code)
        
        # Enhanced stadium tracking
        stadium_record = stadium_tracker[venue]
        stadium_record["Games"] += 1
        stadium_record["IDs"].append(game_id)
        
        # Collect additional stadium data
        # Date information
        date_str = safe_get_str(basic_info, "date_yyyymmdd", "")
        if date_str:
            try:
                game_date = datetime.strptime(date_str, "%Y%m%d")
                stadium_record["dates"].append(game_date)
            except Exception:
                pass
        
        # Attendance
        attendance = basic_info.get("attendance_value")
        if isinstance(attendance, int) and attendance > 0:
            stadium_record["attendance"].append(attendance)
        
        # Game duration
        duration = basic_info.get("duration", "")
        if duration:
            duration_min = self._parse_duration_to_minutes(duration)
            if duration_min:
                stadium_record["durations"].append(duration_min)
        
        # Temperature
        temp = basic_info.get("temperature_f")
        if isinstance(temp, int):
            stadium_record["temperatures"].append(temp)
        
        # Teams and scores
        stadium_record["teams"].update([away_team_code, home_team_code])
        stadium_record["scores"].append(f"{away_team_code} {away_score}-{home_score} {home_team_code}")
        
        # Home team record (wins/losses for the home team at this venue)
        if home_score > away_score:
            stadium_record["home_wins"] += 1
        elif away_score > home_score:
            stadium_record["home_losses"] += 1
        
        # Collect game statistics
        # Home runs - try footer first, then batting stats
        total_game_hrs = 0
        footer_summary = game.get("footer_summary", {})
        
        for side in ("home", "away"):
            # Try footer HR data first
            hr_blob = footer_summary.get(side, {}).get("HR", "")
            if hr_blob:
                # Parse HR counts from footer
                hr_count = sum(count for _, count in ExcelGeneratorUtils.extract_stat_counts(hr_blob))
                total_game_hrs += hr_count
            else:
                # Fallback to batting stats
                batting_hrs = sum(p.get("HR", 0) for p in game.get("batting", {}).get(side, []))
                total_game_hrs += batting_hrs
        
        stadium_record["total_hrs"] += total_game_hrs
        
        # Hits from linescore
        linescore = game.get("linescore", {})
        away_hits = linescore.get("away", {}).get("H", 0)
        home_hits = linescore.get("home", {}).get("H", 0)
        stadium_record["total_hits"] += (away_hits + home_hits)
        
        # Strikeouts from pitching stats
        total_game_ks = 0
        for side in ("home", "away"):
            team_ks = sum(p.get("SO", 0) for p in game.get("pitching", {}).get(side, []))
            total_game_ks += team_ks
        stadium_record["total_strikeouts"] += total_game_ks
        
        # Start times
        start_time = basic_info.get("start_time", "")
        if start_time:
            clean_time = re.sub(r'\s*\(?local.*?\)?', '', start_time, flags=re.IGNORECASE).strip()
            stadium_record["start_times"].append(clean_time)
        
        # Track Orioles-specific records (existing logic)
        self._track_orioles_records(orioles_tracker, venue, game_id, 
                                   away_team_code, home_team_code, away_score, home_score)
        
        # Track all team records (existing logic)
        self._track_team_records(team_tracker, game_id, 
                                away_team_code, home_team_code, away_score, home_score)
    
    def _create_enhanced_stadiums_dataframe(self, stadium_tracker):
        """Create enhanced stadiums DataFrame with additional statistics."""
        try:
            stadium_rows = []
            for stadium, data in stadium_tracker.items():
                row = {
                    "Stadium": stadium,
                    "Games": data["Games"]
                }
                
                # Date information
                if data["dates"]:
                    sorted_dates = sorted(data["dates"])
                    row["First Visit"] = sorted_dates[0].strftime("%m/%d/%Y")
                    row["Last Visit"] = sorted_dates[-1].strftime("%m/%d/%Y")
                    
                    if len(sorted_dates) > 1:
                        start_date = sorted_dates[0]
                        end_date = sorted_dates[-1]
                        
                        # Calculate years, months, and days properly
                        years = end_date.year - start_date.year
                        months = end_date.month - start_date.month
                        days = end_date.day - start_date.day
                        
                        # Adjust for negative days
                        if days < 0:
                            months -= 1
                            # Get days in the previous month
                            if end_date.month == 1:
                                prev_month_year = end_date.year - 1
                                prev_month = 12
                            else:
                                prev_month_year = end_date.year
                                prev_month = end_date.month - 1
                            
                            # Days in previous month
                            days_in_prev_month = calendar.monthrange(prev_month_year, prev_month)[1]
                            days += days_in_prev_month
                        
                        # Adjust for negative months
                        if months < 0:
                            years -= 1
                            months += 12
                        
                        # Build span string
                        span_parts = []
                        if years > 0:
                            span_parts.append(f"{years} year{'s' if years != 1 else ''}")
                        if months > 0:
                            span_parts.append(f"{months} month{'s' if months != 1 else ''}")
                        if days > 0:
                            span_parts.append(f"{days} day{'s' if days != 1 else ''}")
                        
                        # Handle case where all values are 0 (same date)
                        if not span_parts:
                            row["Span"] = "Same day"
                        else:
                            row["Span"] = ", ".join(span_parts)
                    else:
                        row["Span"] = "Single visit"
                else:
                    row["First Visit"] = "Unknown"
                    row["Last Visit"] = "Unknown"
                    row["Span"] = "Unknown"
                
                if data["attendance"]:
                    attendances = data["attendance"]
                    row["Avg Attendance"] = round(sum(attendances) / len(attendances))
                    row["High Attendance"] = max(attendances)
                    row["Low Attendance"] = min(attendances)
                else:
                    row["Avg Attendance"] = "N/A"
                    row["High Attendance"] = "N/A"
                    row["Low Attendance"] = "N/A"
                
                # Game duration statistics
                if data["durations"]:
                    durations = data["durations"]
                    avg_min = sum(durations) / len(durations)
                    avg_hours = int(avg_min // 60)
                    avg_mins = int(avg_min % 60)
                    
                    longest = max(durations)
                    longest_hours = int(longest // 60)
                    longest_mins = int(longest % 60)
                    
                    shortest = min(durations)
                    shortest_hours = int(shortest // 60)
                    shortest_mins = int(shortest % 60)
                    
                    row["Avg Duration"] = f"{avg_hours}:{avg_mins:02d}"
                    row["Longest Game"] = f"{longest_hours}:{longest_mins:02d}"
                    row["Shortest Game"] = f"{shortest_hours}:{shortest_mins:02d}"
                else:
                    row["Avg Duration"] = "N/A"
                    row["Longest Game"] = "N/A"
                    row["Shortest Game"] = "N/A"
                
                # Fixed: Temperature statistics with proper encoding
                if data["temperatures"]:
                    temps = data["temperatures"]
                    row["Avg Temp"] = f"{round(sum(temps) / len(temps))}°F"
                    row["High Temp"] = f"{max(temps)}°F"
                    row["Low Temp"] = f"{min(temps)}°F"
                else:
                    row["Avg Temp"] = "N/A"
                    row["High Temp"] = "N/A"
                    row["Low Temp"] = "N/A"
                
                # Team information and game statistics
                row["Teams Seen"] = len(data["teams"])
                
                # Home team record at this stadium
                total_decided_games = data["home_wins"] + data["home_losses"]
                if total_decided_games > 0:
                    home_win_pct = data["home_wins"] / total_decided_games
                    row["Home Team Record"] = f"{data['home_wins']}-{data['home_losses']} ({home_win_pct:.3f})"
                else:
                    row["Home Team Record"] = "0-0 (.000)"
                
                # Game statistics
                row["Home Runs Seen"] = data["total_hrs"]
                row["Hits Seen"] = data["total_hits"]
                row["Strikeouts Seen"] = data["total_strikeouts"]
                
                # Per-game averages for key stats
                if data["Games"] > 0:
                    row["HRs per Game"] = round(data["total_hrs"] / data["Games"], 1)
                    row["Hits per Game"] = round(data["total_hits"] / data["Games"], 1)
                    row["Ks per Game"] = round(data["total_strikeouts"] / data["Games"], 1)
                else:
                    row["HRs per Game"] = 0.0
                    row["Hits per Game"] = 0.0
                    row["Ks per Game"] = 0.0
                
                # Most common start time
                if data["start_times"]:
                    start_time_counts = Counter(data["start_times"])
                    most_common_time, count = start_time_counts.most_common(1)[0]
                    row["Most Common Start"] = f"{most_common_time} ({count}x)"
                else:
                    row["Most Common Start"] = "N/A"
                
                # GameIDs (keep existing)
                row["GameIDs"] = join_sorted_gameids(data["IDs"])
                
                stadium_rows.append(row)
            
            stadiums_df = pd.DataFrame(stadium_rows)
            if not stadiums_df.empty:
                stadiums_df = stadiums_df.sort_values("Games", ascending=False).reset_index(drop=True)
            
            return stadiums_df
            
        except Exception as e:
            print(f"   ⚠️ Error creating enhanced stadiums DataFrame: {e}")
            logging.exception("Error details:")
            return pd.DataFrame()  
   
    def _unify_stadium_name(self, venue_name):
        """Normalize stadium names to canonical form."""
        if not venue_name:
            return venue_name

        for canonical, aliases in STADIUM_ALIASES.items():
            if venue_name == canonical or venue_name in aliases:
                return canonical

        return venue_name
    
    def _track_orioles_records(self, orioles_tracker, venue, game_id, 
                          away_team_code, home_team_code, away_score, home_score):
        """Enhanced Orioles-specific records tracking."""
        
        # Only track if Orioles are playing
        if "BAL" not in (away_team_code, home_team_code):
            return
        
        try:
            # Get the full game data for this game_id
            game = next((g for g in self.games if g.get("game_id") == game_id), None)
            if not game:
                logging.debug(f"Could not find game data for {game_id}")
                return
                
            basic_info = game.get("basic_info", {})
            orioles_record = orioles_tracker[venue]
            
            # Basic tracking
            orioles_record["Games"] += 1
            orioles_record["IDs"].append(game_id)
            
            # Determine if Orioles are home or away and if they won
            orioles_is_away = away_team_code == "BAL"
            orioles_score = away_score if orioles_is_away else home_score
            opponent_score = home_score if orioles_is_away else away_score
            orioles_won = orioles_score > opponent_score
            
            if orioles_won:
                orioles_record["Wins"] += 1
            else:
                orioles_record["Losses"] += 1
            
            # Visit History
            date_str = safe_get_str(basic_info, "date_yyyymmdd", "")
            if date_str:
                try:
                    game_date = datetime.strptime(date_str, "%Y%m%d")
                    orioles_record["dates"].append(game_date)
                except Exception:
                    pass
            
            # Attendance & Environment
            attendance = basic_info.get("attendance_value")
            if isinstance(attendance, int) and attendance > 0:
                orioles_record["attendance"].append(attendance)
                
            temp = basic_info.get("temperature_f")
            if isinstance(temp, int):
                orioles_record["temperatures"].append(temp)
            
            # Orioles Offensive Performance
            orioles_record["orioles_runs"] += orioles_score
            
            # Track highest scoring game
            if orioles_score > orioles_record["highest_scoring_game"]["runs"]:
                score_string = f"BAL {orioles_score}-{opponent_score} {home_team_code if orioles_is_away else away_team_code}"
                orioles_record["highest_scoring_game"] = {
                    "runs": orioles_score,
                    "score": score_string,
                    "game_id": game_id
                }
            
            # Get Orioles offensive stats from batting data
            orioles_side = "away" if orioles_is_away else "home"
            
            # Home runs from footer or batting stats
            footer_summary = game.get("footer_summary", {})
            hr_blob = footer_summary.get(orioles_side, {}).get("HR", "")
            if hr_blob:
                hr_count = sum(count for _, count in ExcelGeneratorUtils.extract_stat_counts(hr_blob))
                orioles_record["orioles_hrs"] += hr_count
            else:
                batting_hrs = sum(p.get("HR", 0) for p in game.get("batting", {}).get(orioles_side, []))
                orioles_record["orioles_hrs"] += batting_hrs
            
            # Hits from linescore
            linescore = game.get("linescore", {})
            orioles_hits = linescore.get(orioles_side, {}).get("H", 0)
            orioles_record["orioles_hits"] += orioles_hits
            
            # Orioles Pitching Performance
            orioles_record["runs_allowed"] += opponent_score
            
            # Strikeouts by Orioles pitchers
            orioles_ks = sum(p.get("SO", 0) for p in game.get("pitching", {}).get(orioles_side, []))
            orioles_record["orioles_strikeouts"] += orioles_ks
            
            # Game Characteristics
            run_margin = abs(orioles_score - opponent_score)
            
            # 1-run games
            if run_margin == 1:
                orioles_record["one_run_games"] += 1
                if orioles_won:
                    orioles_record["one_run_wins"] += 1
                else:
                    orioles_record["one_run_losses"] += 1
            
            # Blowouts (5+ run margin)
            if run_margin >= 5:
                orioles_record["blowout_games"] += 1
                if orioles_won:
                    orioles_record["blowout_wins"] += 1
                else:
                    orioles_record["blowout_losses"] += 1
            
            # Extra inning games
            linescore = game.get("linescore", {})
            home_innings = len(linescore.get("home", {}).get("innings", []))
            away_innings = len(linescore.get("away", {}).get("innings", []))
            max_innings = max(home_innings, away_innings)
            
            if max_innings > 9:
                orioles_record["extra_inning_games"] += 1
                if orioles_won:
                    orioles_record["extra_inning_wins"] += 1
                else:
                    orioles_record["extra_inning_losses"] += 1
            
            # Walk-offs (check if this was a walkoff game)
            walkoff = game.get("special_events", {}).get("walkoff")
            if walkoff:
                orioles_record["walkoff_games"] += 1
                # Walkoffs only happen for home team wins
                if not orioles_is_away and orioles_won:
                    orioles_record["walkoff_wins"] += 1
                elif orioles_is_away and not orioles_won:
                    orioles_record["walkoff_losses"] += 1
                    
        except Exception as e:
            print(f"   ⚠️ Error tracking enhanced Orioles record: {e}")
            logging.exception("Error details:")

    def _track_team_records(self, team_tracker, game_id, 
                           away_team_code, home_team_code, away_score, home_score):
        """Track all team records."""
        try:
            # Determine winner
            away_won = away_score > home_score
            
            # Handle special team groupings
            away_group = self._get_team_group(away_team_code)
            home_group = self._get_team_group(home_team_code)
            
            # Track away team
            away_record = team_tracker[away_group]
            away_record["Games"] += 1
            away_record["IDs"].append(game_id)
            if away_won:
                away_record["Wins"] += 1
            else:
                away_record["Losses"] += 1
            
            # Track home team
            home_record = team_tracker[home_group]
            home_record["Games"] += 1
            home_record["IDs"].append(game_id)
            if not away_won:  # Home team won
                home_record["Wins"] += 1
            else:
                home_record["Losses"] += 1
                
        except Exception as e:
            print(f"   ⚠️ Error tracking team records: {e}")
    
    def _get_team_group(self, team_code):
        """Get team group for record tracking (handles special cases)."""
        # Group Florida/Miami Marlins together
        if team_code in {"FLA", "MIA"}:
            return "FLA/MIA"
        # Group Oakland Athletics (future name change)
        elif team_code in {"OAK", "ATH"}:
            return "ATH/OAK"
        else:
            return team_code
    
    def _create_orioles_dataframe(self, orioles_tracker):
        """Create enhanced Orioles stadiums DataFrame."""
        
        try:
            orioles_rows = []
            for stadium, data in orioles_tracker.items():
                
                if data["Games"] == 0:
                    continue
                
                row = {"Stadium": stadium, "Games": data["Games"]}
                
                # CONSOLIDATED: Combine all win-loss info into single column
                win_pct = round(data["Wins"] / data["Games"], 3) if data["Games"] > 0 else 0.000
                row["Orioles Record"] = f"{data['Wins']}-{data['Losses']} ({win_pct:.3f})"
                
                # Visit History
                if data["dates"]:
                    sorted_dates = sorted(data["dates"])
                    row["First Visit"] = sorted_dates[0].strftime("%m/%d/%Y")
                    row["Last Visit"] = sorted_dates[-1].strftime("%m/%d/%Y")
                    
                    if len(sorted_dates) > 1:
                        start_date = sorted_dates[0]
                        end_date = sorted_dates[-1]
                        
                        # Calculate years, months, and days properly
                        years = end_date.year - start_date.year
                        months = end_date.month - start_date.month
                        days = end_date.day - start_date.day
                        
                        # Adjust for negative days
                        if days < 0:
                            months -= 1
                            # Get days in the previous month
                            if end_date.month == 1:
                                prev_month_year = end_date.year - 1
                                prev_month = 12
                            else:
                                prev_month_year = end_date.year
                                prev_month = end_date.month - 1
                            
                            # Days in previous month
                            days_in_prev_month = calendar.monthrange(prev_month_year, prev_month)[1]
                            days += days_in_prev_month
                        
                        # Adjust for negative months
                        if months < 0:
                            years -= 1
                            months += 12
                        
                        # Build span string
                        span_parts = []
                        if years > 0:
                            span_parts.append(f"{years} year{'s' if years != 1 else ''}")
                        if months > 0:
                            span_parts.append(f"{months} month{'s' if months != 1 else ''}")
                        if days > 0:
                            span_parts.append(f"{days} day{'s' if days != 1 else ''}")
                        
                        # Handle case where all values are 0 (same date)
                        if not span_parts:
                            row["Visit Span"] = "Same day"
                        else:
                            row["Visit Span"] = ", ".join(span_parts)
                    else:
                        row["Visit Span"] = "Single visit"
                else:
                    row["First Visit"] = "Unknown"
                    row["Last Visit"] = "Unknown" 
                    row["Visit Span"] = "Unknown"
                
                # Attendance & Environment
                if data["attendance"]:
                    attendances = data["attendance"]
                    row["Avg Attendance"] = round(sum(attendances) / len(attendances))
                    row["High Attendance"] = max(attendances)
                    row["Low Attendance"] = min(attendances)
                else:
                    row["Avg Attendance"] = "N/A"
                    row["High Attendance"] = "N/A"
                    row["Low Attendance"] = "N/A"
                    
                if data["temperatures"]:
                    temps = data["temperatures"]
                    row["Avg Temp"] = f"{round(sum(temps) / len(temps))}°F"
                else:
                    row["Avg Temp"] = "N/A"
                
                # Orioles Offensive Performance
                row["Runs Scored"] = data["orioles_runs"]
                row["Runs/Game"] = round(data["orioles_runs"] / data["Games"], 1) if data["Games"] > 0 else 0.0
                
                if data["highest_scoring_game"]["runs"] > 0:
                    row["Highest Scoring"] = f"{data['highest_scoring_game']['runs']} ({data['highest_scoring_game']['score']})"
                else:
                    row["Highest Scoring"] = "N/A"
                
                row["Home Runs Hit"] = data["orioles_hrs"]
                row["HRs/Game"] = round(data["orioles_hrs"] / data["Games"], 1) if data["Games"] > 0 else 0.0
                
                row["Hits"] = data["orioles_hits"]
                row["Hits/Game"] = round(data["orioles_hits"] / data["Games"], 1) if data["Games"] > 0 else 0.0
                
                # Orioles Pitching Performance
                row["Runs Allowed"] = data["runs_allowed"]
                row["Runs Allowed/Game"] = round(data["runs_allowed"] / data["Games"], 1) if data["Games"] > 0 else 0.0
                row["Strikeouts by O's"] = data["orioles_strikeouts"]
                
                # Game Characteristics
                if data["one_run_games"] > 0:
                    one_run_pct = data["one_run_wins"] / data["one_run_games"]
                    row["1-Run Games"] = f"{data['one_run_wins']}-{data['one_run_losses']} ({one_run_pct:.3f})"
                else:
                    row["1-Run Games"] = "0-0"
                
                if data["blowout_games"] > 0:
                    blowout_pct = data["blowout_wins"] / data["blowout_games"]
                    row["Blowouts (5+)"] = f"{data['blowout_wins']}-{data['blowout_losses']} ({blowout_pct:.3f})"
                else:
                    row["Blowouts (5+)"] = "0-0"
                
                if data["extra_inning_games"] > 0:
                    extra_pct = data["extra_inning_wins"] / data["extra_inning_games"]
                    row["Extra Innings"] = f"{data['extra_inning_wins']}-{data['extra_inning_losses']} ({extra_pct:.3f})"
                else:
                    row["Extra Innings"] = "0-0"
                
                if data["walkoff_games"] > 0:
                    walkoff_pct = data["walkoff_wins"] / data["walkoff_games"] if data["walkoff_games"] > 0 else 0
                    row["Walk-offs"] = f"{data['walkoff_wins']}-{data['walkoff_losses']} ({walkoff_pct:.3f})"
                else:
                    row["Walk-offs"] = "0-0"
                
                # Advanced Analytics
                run_diff = data["orioles_runs"] - data["runs_allowed"]
                row["Run Differential"] = f"+{run_diff}" if run_diff > 0 else str(run_diff)
                row["Run Diff/Game"] = round(run_diff / data["Games"], 1) if data["Games"] > 0 else 0.0
                
                # GameIDs
                row["GameIDs"] = join_sorted_gameids(data["IDs"])
                
                orioles_rows.append(row)
            
            orioles_df = pd.DataFrame(orioles_rows)
            if not orioles_df.empty:
                orioles_df = orioles_df.sort_values("Games", ascending=False).reset_index(drop=True)
            return orioles_df
            
        except Exception as e:
            print(f"   ⚠️ Error creating enhanced Orioles DataFrame: {e}")
            logging.exception("Error details:")
            return pd.DataFrame()  
        
    def _create_team_records_dataframe(self, team_tracker):
        """Create the team records DataFrame."""
        try:
            # Normalize legacy team codes to modern ones before final aggregation
            normalized_teams = {}
            code_map = {
                "FLA": "MIA"  # Florida Marlins -> Miami Marlins
            }
            
            # Aggregate records with normalization
            for team_group, record in team_tracker.items():
                # Map old codes to new ones
                if team_group in code_map:
                    final_code = code_map[team_group]
                else:
                    final_code = team_group
                
                if final_code not in normalized_teams:
                    normalized_teams[final_code] = {
                        "Games": 0,
                        "Wins": 0,
                        "Losses": 0,
                        "IDs": []
                    }
                
                normalized_teams[final_code]["Games"] += record["Games"]
                normalized_teams[final_code]["Wins"] += record["Wins"]
                normalized_teams[final_code]["Losses"] += record["Losses"]
                normalized_teams[final_code]["IDs"].extend(record["IDs"])
            
            # Build final DataFrame
            team_rows = []
            for team_code, record in normalized_teams.items():
                if record["Games"] == 0:
                    continue
                    
                win_pct = round(record["Wins"] / record["Games"], 3) if record["Games"] > 0 else 0.000
                w_l_record = f"{record['Wins']}-{record['Losses']}"
                
                team_rows.append({
                    "Team": team_code,
                    "Games": record["Games"],
                    "Wins": record["Wins"],
                    "Losses": record["Losses"],
                    "Win%": win_pct,
                    "W-L": w_l_record,
                    "GameIDs": join_sorted_gameids(record["IDs"])
                })
            
            team_records_df = pd.DataFrame(team_rows)
            if not team_records_df.empty:
                team_records_df = team_records_df.sort_values("Games", ascending=False).reset_index(drop=True)
            
            return team_records_df
            
        except Exception as e:
            print(f"   ⚠️ Error creating team records DataFrame: {e}")
            return pd.DataFrame()

    def _parse_duration_to_minutes(self, duration_text):
        """Convert duration string to minutes."""
        if not duration_text:
            return None
        
        # Handle "2:37" format
        match = re.search(r'(\d+):(\d+)', duration_text)
        if match:
            hours = int(match.group(1))
            minutes = int(match.group(2))
            return hours * 60 + minutes
        
        # Handle "2 hours, 37 minutes" format
        hours_match = re.search(r'(\d+)\s*hour', duration_text, re.IGNORECASE)
        minutes_match = re.search(r'(\d+)\s*min', duration_text, re.IGNORECASE)
        
        hours = int(hours_match.group(1)) if hours_match else 0
        minutes = int(minutes_match.group(1)) if minutes_match else 0
        
        if hours > 0 or minutes > 0:
            return hours * 60 + minutes
        
        return None


class EnhancedTeamRecordsProcessor(BaseProcessor):
    """Enhanced team records processing with comprehensive statistics."""

    def __init__(self, games):
        super().__init__(games)

    def _normalize_team_code(self, team_code):
        """Normalize team codes to handle franchise moves and name changes."""
        if team_code in ("ATH", "OAK"):
            return "ATH/OAK"
        elif team_code in ("FLA", "MIA"):
            return "FLA/MIA"
        else:
            return team_code
        
    def process_enhanced_team_records(self):
        """Process comprehensive team records with detailed breakdowns."""
        print("🏆 Processing enhanced team records...")
        
        # Initialize enhanced tracking
        team_records = defaultdict(lambda: {
            # Basic Record
            "games": 0,
            "wins": 0,
            "losses": 0,
            "ties": 0,
            
            # Home/Away Split
            "home_games": 0,
            "home_wins": 0,
            "home_losses": 0,
            "away_games": 0,
            "away_wins": 0,
            "away_losses": 0,
            
            # Run Statistics
            "runs_scored": 0,
            "runs_allowed": 0,
            
            # Offensive Statistics
            "hits": 0,
            "home_runs": 0,
            "walks_taken": 0,  # BB by batters
            "strikeouts_by": 0,  # SO by batters
            "stolen_bases": 0,
            
            # Pitching Statistics  
            "walks_allowed": 0,  # BB by pitchers
            "strikeouts_for": 0,  # SO by pitchers
            "hits_allowed": 0,
            "home_runs_allowed": 0,
            
            # Game Situation Records
            "one_run_games": 0,
            "one_run_wins": 0,
            "blowout_games": 0,  # 5+ run margin
            "blowout_wins": 0,
            "extra_inning_games": 0,
            "extra_inning_wins": 0,
            "walkoff_games": 0,
            "walkoff_wins": 0,
            
            # Monthly Performance
            "monthly_record": defaultdict(lambda: {"wins": 0, "losses": 0}),
            
            # Head-to-Head Records
            "vs_teams": defaultdict(lambda: {"wins": 0, "losses": 0, "games": []}),
            
            # Streaks (current and longest)
            "current_streak": {"type": None, "count": 0},
            "longest_win_streak": 0,
            "longest_loss_streak": 0,
            
            # Game IDs for reference
            "game_ids": [],
            
            # First/Last games for span calculation
            "first_game_date": None,
            "last_game_date": None,
        })
        
        # Process games in chronological order for streak tracking
        sorted_games = self._sort_games_chronologically()
        
        for game in sorted_games:
            self._process_enhanced_game_record(game, team_records)
        
        # Calculate final statistics and streaks
        self._finalize_team_records(team_records)
        
        # Create comprehensive DataFrame
        team_records_df = self._create_enhanced_team_dataframe(team_records)
        
        print(f"   ✅ Enhanced team records processed for {len(team_records_df)} teams")
        return team_records_df
    
    def _sort_games_chronologically(self):
        """Sort games by date for proper streak calculation."""
        def parse_game_date(game):
            date_str = game.get("basic_info", {}).get("date_yyyymmdd", "")
            try:
                return datetime.strptime(date_str, "%Y%m%d")
            except Exception:
                return datetime.min
                
        return sorted(self.games, key=parse_game_date)
    
    def _process_enhanced_game_record(self, game, team_records):
        """Process a single game for enhanced team records."""
        try:
            basic_info = game.get("basic_info", {})
            game_id = game.get("game_id", "")
            
            # Get team info
            away_team_raw = unify_team_code(basic_info.get("away_team_code", ""))
            home_team_raw = unify_team_code(basic_info.get("home_team_code", ""))
            away_team = self._normalize_team_code(away_team_raw)
            home_team = self._normalize_team_code(home_team_raw)
            away_score = safe_get_int(basic_info, "away_score_value", 0)
            home_score = safe_get_int(basic_info, "home_score_value", 0)
            
            # Get game date for monthly tracking
            date_str = basic_info.get("date_yyyymmdd", "")
            try:
                game_date = datetime.strptime(date_str, "%Y%m%d")
                month_key = game_date.strftime("%Y-%m")
            except Exception:
                game_date = None
                month_key = "Unknown"
            
            # Determine winner and game characteristics
            away_won = away_score > home_score
            home_won = home_score > away_score
            is_tie = away_score == home_score
            run_margin = abs(away_score - home_score)
            is_one_run = run_margin == 1
            is_blowout = run_margin >= 5
            
            # Check for extra innings
            linescore = game.get("linescore", {})
            home_innings = len(linescore.get("home", {}).get("innings", []))
            away_innings = len(linescore.get("away", {}).get("innings", []))
            is_extra_innings = max(home_innings, away_innings) > 9
            
            # Check for walkoff
            is_walkoff = game.get("special_events", {}).get("walkoff") is not None
            
            # Get offensive/pitching statistics
            away_stats = self._extract_team_stats(game, "away")
            home_stats = self._extract_team_stats(game, "home")
            
            # Update records for both teams
            for team_code, is_home, won, stats in [
                (away_team, False, away_won, away_stats),
                (home_team, True, home_won, home_stats)
            ]:
                if not team_code:
                    continue
                    
                record = team_records[team_code]
                opponent = home_team if not is_home else away_team
                
                # Basic record
                record["games"] += 1
                record["game_ids"].append(game_id)
                
                if is_tie:
                    record["ties"] += 1
                elif won:
                    record["wins"] += 1
                else:
                    record["losses"] += 1
                
                # Home/Away split
                if is_home:
                    record["home_games"] += 1
                    if won:
                        record["home_wins"] += 1
                    elif not is_tie:
                        record["home_losses"] += 1
                else:
                    record["away_games"] += 1
                    if won:
                        record["away_wins"] += 1
                    elif not is_tie:
                        record["away_losses"] += 1
                
                # Run statistics
                team_runs = home_score if is_home else away_score
                opp_runs = away_score if is_home else home_score
                record["runs_scored"] += team_runs
                record["runs_allowed"] += opp_runs
                
                # Team statistics
                record["hits"] += stats["hits"]
                record["home_runs"] += stats["home_runs"]
                record["walks_taken"] += stats["walks_taken"]
                record["strikeouts_by"] += stats["strikeouts_by"]
                record["stolen_bases"] += stats["stolen_bases"]
                record["walks_allowed"] += stats["walks_allowed"]
                record["strikeouts_for"] += stats["strikeouts_for"]
                record["hits_allowed"] += stats["hits_allowed"]
                record["home_runs_allowed"] += stats["home_runs_allowed"]
                
                # Game situation tracking
                if is_one_run:
                    record["one_run_games"] += 1
                    if won:
                        record["one_run_wins"] += 1
                
                if is_blowout:
                    record["blowout_games"] += 1
                    if won:
                        record["blowout_wins"] += 1
                
                if is_extra_innings:
                    record["extra_inning_games"] += 1
                    if won:
                        record["extra_inning_wins"] += 1
                
                if is_walkoff:
                    record["walkoff_games"] += 1
                    if won and is_home:  # Only home team can win via walkoff
                        record["walkoff_wins"] += 1
                
                # Monthly record
                if not is_tie:
                    if won:
                        record["monthly_record"][month_key]["wins"] += 1
                    else:
                        record["monthly_record"][month_key]["losses"] += 1
                
                # Head-to-head record
                if opponent:
                    if won:
                        record["vs_teams"][opponent]["wins"] += 1
                    elif not is_tie:
                        record["vs_teams"][opponent]["losses"] += 1
                    record["vs_teams"][opponent]["games"].append(game_id)
                
                # Update streak tracking
                self._update_streak(record, won, is_tie)
                
                # Track date span
                if game_date:
                    if not record["first_game_date"] or game_date < record["first_game_date"]:
                        record["first_game_date"] = game_date
                    if not record["last_game_date"] or game_date > record["last_game_date"]:
                        record["last_game_date"] = game_date
                        
        except Exception as e:
            print(f"   ⚠️ Error processing enhanced game record: {e}")
    
    def _extract_team_stats(self, game, side):
        """Extract comprehensive statistics for one team in a game."""
        stats = {
            "hits": 0,
            "home_runs": 0,
            "walks_taken": 0,
            "strikeouts_by": 0,
            "stolen_bases": 0,
            "walks_allowed": 0,
            "strikeouts_for": 0,
            "hits_allowed": 0,
            "home_runs_allowed": 0
        }
        
        try:
            # Offensive stats from batting
            for player in game.get("batting", {}).get(side, []):
                stats["walks_taken"] += safe_get_int(player, "BB", 0)
                stats["strikeouts_by"] += safe_get_int(player, "SO", 0)
                stats["home_runs"] += safe_get_int(player, "HR", 0)
            
            # Get hits from linescore
            linescore = game.get("linescore", {})
            stats["hits"] = linescore.get(side, {}).get("H", 0)
            
            # Pitching stats (what this team's pitchers allowed)
            for pitcher in game.get("pitching", {}).get(side, []):
                stats["walks_allowed"] += safe_get_int(pitcher, "BB", 0)
                stats["strikeouts_for"] += safe_get_int(pitcher, "SO", 0)
                stats["hits_allowed"] += safe_get_int(pitcher, "H", 0)
                stats["home_runs_allowed"] += safe_get_int(pitcher, "HR", 0)
            
            # Stolen bases from footer summary
            footer_summary = game.get("footer_summary", {})
            sb_blob = footer_summary.get(side, {}).get("SB", "")
            if sb_blob:
                stats["stolen_bases"] = sum(count for _, count in ExcelGeneratorUtils.extract_stat_counts(sb_blob))
            
            # Home runs from footer (more accurate than box score)
            hr_blob = footer_summary.get(side, {}).get("HR", "")
            if hr_blob:
                hr_count = sum(count for _, count in ExcelGeneratorUtils.extract_stat_counts(hr_blob))
                if hr_count > stats["home_runs"]:
                    stats["home_runs"] = hr_count
                    
        except Exception as e:
            print(f"   ⚠️ Error extracting team stats: {e}")
        
        return stats
    
    def _update_streak(self, record, won, is_tie):
        """Update current and longest win/loss streaks."""
        if is_tie:
            # Ties break streaks
            record["current_streak"] = {"type": None, "count": 0}
            return
        
        current = record["current_streak"]
        
        if won:
            if current["type"] == "W":
                current["count"] += 1
            else:
                current = {"type": "W", "count": 1}
            
            # Update longest win streak
            if current["count"] > record["longest_win_streak"]:
                record["longest_win_streak"] = current["count"]
        else:
            if current["type"] == "L":
                current["count"] += 1
            else:
                current = {"type": "L", "count": 1}
            
            # Update longest loss streak  
            if current["count"] > record["longest_loss_streak"]:
                record["longest_loss_streak"] = current["count"]
        
        record["current_streak"] = current
    
    def _finalize_team_records(self, team_records):
        """Calculate final derived statistics."""
        for team_code, record in team_records.items():
            # Calculate additional rate stats
            games = record["games"]
            if games > 0:
                record["runs_per_game"] = round(record["runs_scored"] / games, 2)
                record["runs_allowed_per_game"] = round(record["runs_allowed"] / games, 2)
                record["run_differential"] = record["runs_scored"] - record["runs_allowed"]
                record["run_diff_per_game"] = round(record["run_differential"] / games, 2)
    
    def _create_enhanced_team_dataframe(self, team_records):
        """Create comprehensive team records DataFrame."""
        try:
            team_rows = []
            
            for team_code, record in team_records.items():
                if record["games"] == 0:
                    continue
                
                # Basic record
                games = record["games"]
                wins = record["wins"]
                losses = record["losses"]
                ties = record["ties"]
                win_pct = wins / (wins + losses) if (wins + losses) > 0 else 0.000
                
                # Home/Away records
                home_wins = record["home_wins"]
                home_losses = record["home_losses"]
                home_pct = home_wins / (home_wins + home_losses) if (home_wins + home_losses) > 0 else 0.000
                
                away_wins = record["away_wins"]
                away_losses = record["away_losses"]
                away_pct = away_wins / (away_wins + away_losses) if (away_wins + away_losses) > 0 else 0.000
                
                # One-run and blowout records
                one_run_wins = record["one_run_wins"]
                one_run_losses = record["one_run_games"] - one_run_wins
                one_run_pct = one_run_wins / record["one_run_games"] if record["one_run_games"] > 0 else 0.000
                
                blowout_wins = record["blowout_wins"]
                blowout_losses = record["blowout_games"] - blowout_wins
                blowout_pct = blowout_wins / record["blowout_games"] if record["blowout_games"] > 0 else 0.000
                
                # Extra innings record
                extra_wins = record["extra_inning_wins"]
                extra_losses = record["extra_inning_games"] - extra_wins
                extra_pct = extra_wins / record["extra_inning_games"] if record["extra_inning_games"] > 0 else 0.000
                
                # Walk-off record
                walkoff_wins = record["walkoff_wins"]
                walkoff_losses = record["walkoff_games"] - record["walkoff_wins"]
                walkoff_pct = walkoff_wins / record["walkoff_games"] if record["walkoff_games"] > 0 else 0.000

                # Current streak display
                current_streak = record["current_streak"]
                if current_streak["type"] and current_streak["count"] > 0:
                    streak_display = f"{current_streak['type']}{current_streak['count']}"
                else:
                    streak_display = "-"
                
                # Date span with proper years/months/days calculation
                first_date = record["first_game_date"]
                last_date = record["last_game_date"]
                if first_date and last_date and first_date != last_date:
                    # Calculate years, months, and days properly
                    years = last_date.year - first_date.year
                    months = last_date.month - first_date.month
                    days = last_date.day - first_date.day
                    
                    # Adjust for negative days
                    if days < 0:
                        months -= 1
                        # Get days in the previous month
                        if last_date.month == 1:
                            prev_month_year = last_date.year - 1
                            prev_month = 12
                        else:
                            prev_month_year = last_date.year
                            prev_month = last_date.month - 1
                        
                        # Days in previous month
                        days_in_prev_month = calendar.monthrange(prev_month_year, prev_month)[1]
                        days += days_in_prev_month
                    
                    # Adjust for negative months
                    if months < 0:
                        years -= 1
                        months += 12
                    
                    # Build span string
                    span_parts = []
                    if years > 0:
                        span_parts.append(f"{years} year{'s' if years != 1 else ''}")
                    if months > 0:
                        span_parts.append(f"{months} month{'s' if months != 1 else ''}")
                    if days > 0:
                        span_parts.append(f"{days} day{'s' if days != 1 else ''}")
                    
                    # Handle case where all values are 0 (same date)
                    if not span_parts:
                        span_display = "Same day"
                    else:
                        span_display = ", ".join(span_parts)
                        
                    first_display = first_date.strftime("%m/%d/%Y")
                    last_display = last_date.strftime("%m/%d/%Y")
                else:
                    span_display = "Single game"
                    first_display = first_date.strftime("%m/%d/%Y") if first_date else "Unknown"
                    last_display = first_display
                
                # Build comprehensive row
                row = {
                    "Team": team_code,
                    "Games": games,
                    "Record": f"{wins}-{losses} ({win_pct:.3f})",
                    
                    # Home/Away split
                    "Home Record": f"{home_wins}-{home_losses} ({home_pct:.3f})",
                    "Away Record": f"{away_wins}-{away_losses} ({away_pct:.3f})",
                    
                    # Run statistics
                    "Runs Scored": record["runs_scored"],
                    "Runs Allowed": record["runs_allowed"], 
                    "Run Differential": record["run_differential"],
                    "Runs/Game": record["runs_per_game"],
                    "Runs Allowed/Game": record["runs_allowed_per_game"],
                    
                    # Situational records
                    "1-Run Games": f"{one_run_wins}-{one_run_losses} ({one_run_pct:.3f})",
                    "Blowouts (5+)": f"{blowout_wins}-{blowout_losses} ({blowout_pct:.3f})",
                    "Extra Innings": f"{extra_wins}-{extra_losses} ({extra_pct:.3f})",
                    "Walk-offs": f"{walkoff_wins}-{walkoff_losses} ({walkoff_pct:.3f})",
                    
                    # Team statistics
                    "Team Hits": record["hits"],
                    "Team HRs": record["home_runs"],
                    "Team SBs": record["stolen_bases"],
                    "Walks Taken": record["walks_taken"],
                    "Strikeouts By": record["strikeouts_by"],
                    "Strikeouts For": record["strikeouts_for"],
                    "Walks Allowed": record["walks_allowed"],
                    
                    # Streak information
                    "Current Streak": streak_display,
                    "Longest Win Streak": record["longest_win_streak"],
                    "Longest Loss Streak": record["longest_loss_streak"],
                    
                    # Date span
                    "First Game": first_display,
                    "Last Game": last_display,
                    "Span": span_display,
                    
                    "GameIDs": join_sorted_gameids(record["game_ids"])
                }
                
                # Add games and win percentage for sorting
                row["_games_sort"] = games
                row["_win_pct_sort"] = win_pct
                
                team_rows.append(row)
            
            # Create DataFrame and sort by number of games (descending), then win percentage
            team_records_df = pd.DataFrame(team_rows)
            if not team_records_df.empty:
                team_records_df = team_records_df.sort_values(
                    ["_games_sort", "_win_pct_sort"], 
                    ascending=[False, False]
                ).reset_index(drop=True)
                
                # Remove the sorting columns
                team_records_df = team_records_df.drop(columns=["_games_sort", "_win_pct_sort"])
            
            return team_records_df
            
        except Exception as e:
            print(f"   ⚠️ Error creating enhanced team DataFrame: {e}")
            return pd.DataFrame()

    def _parse_duration_to_minutes(self, duration_text):
        """Convert duration string to minutes."""
        if not duration_text:
            return None
        
        # Handle "2:37" format
        match = re.search(r'(\d+):(\d+)', duration_text)
        if match:
            hours = int(match.group(1))
            minutes = int(match.group(2))
            return hours * 60 + minutes
        
        # Handle "2 hours, 37 minutes" format
        hours_match = re.search(r'(\d+)\s*hour', duration_text, re.IGNORECASE)
        minutes_match = re.search(r'(\d+)\s*min', duration_text, re.IGNORECASE)
        
        hours = int(hours_match.group(1)) if hours_match else 0
        minutes = int(minutes_match.group(1)) if minutes_match else 0
        
        if hours > 0 or minutes > 0:
            return hours * 60 + minutes
        
        return None
