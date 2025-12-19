import re
import pandas as pd
from datetime import datetime
from ..excel.generators import ExcelGeneratorUtils
from ..utils.helpers import standardize_team_code, join_sorted_gameids, unify_team_code, safe_get_int, safe_get_str
from ..utils.stat_utils import StatUtils
from .base_processor import BaseProcessor

class MilestonesProcessor(BaseProcessor):
    def __init__(self, games):
        super().__init__(games)
        
    def process_all_milestones(self):
        """Process all milestones and special events."""
        print("🏆 Processing milestones and special events...")
        
        # Initialize milestone tracking
        milestone_tabs = self._initialize_milestone_tabs()
        
        # Process each game for milestones using existing engines
        for game in self.games:
            try:
                # Extract results that were already processed during parsing
                self._extract_game_milestones(game, milestone_tabs)
                
            except Exception as e:
                game_id = self.get_game_id(game)
                print(f"   ⚠️ Error processing milestones for game {game_id}: {e}")
                continue
        
        # Process consecutive home runs
        b2b_data = self._detect_consecutive_home_runs()
        
        # Convert milestone lists to DataFrames
        milestone_dfs = self._create_milestone_dataframes(milestone_tabs)

        # Enhance milestones with complete stat lines
        milestone_dfs = integrate_practical_enhancements(milestone_dfs, self.games)

        # --- Combine "Complete Games" and "Shutouts" into one tab---
        try:
            cg_df = milestone_dfs.get("Complete Games", pd.DataFrame()).copy()
            sh_df = milestone_dfs.get("Shutouts", pd.DataFrame()).copy()

            if not cg_df.empty or not sh_df.empty:
                # Flags
                if not cg_df.empty:
                    cg_df["CG"] = True
                if not sh_df.empty:
                    sh_df["SHO"] = True

                # Updated merge keys for enhanced DataFrames (no "Score" column)
                merge_keys = ["Date", "Player", "Team", "Opponent", "GameID"]
                
                # Get all pitching stat columns that exist in both DataFrames
                common_pitching_cols = []
                if not cg_df.empty and not sh_df.empty:
                    common_pitching_cols = [col for col in ["IP", "H", "R", "ER", "BB", "K", "Pitches", "WHIP", "Decision", "Home/Away"] 
                                        if col in cg_df.columns and col in sh_df.columns]
                
                # Build column lists for merge
                all_merge_cols = merge_keys + common_pitching_cols
                
                left_df = cg_df[[c for c in cg_df.columns if c in all_merge_cols + ["CG"]]].copy() if not cg_df.empty else pd.DataFrame(columns=all_merge_cols + ["CG"])
                right_df = sh_df[[c for c in sh_df.columns if c in all_merge_cols + ["SHO"]]].copy() if not sh_df.empty else pd.DataFrame(columns=all_merge_cols + ["SHO"])

                combined = pd.merge(left_df, right_df, on=all_merge_cols, how="outer")
                combined["CG"] = (
                    combined.get("CG", pd.Series(index=combined.index, dtype="boolean"))
                    .astype("boolean")
                    .fillna(False)
                )
                combined["SHO"] = (
                    combined.get("SHO", pd.Series(index=combined.index, dtype="boolean"))
                    .astype("boolean")
                    .fillna(False)
                )

                # Sort by date if possible
                if "Date" in combined.columns:
                    _tmp = pd.to_datetime(combined["Date"], errors="coerce", format="%m/%d/%Y")
                    if _tmp.notna().any():
                        combined = combined.assign(_sort=_tmp).sort_values("_sort").drop(columns=["_sort"])

                milestone_dfs["Complete Games & Shutouts"] = combined.reset_index(drop=True)
                milestone_dfs["Complete Games"] = pd.DataFrame()
                milestone_dfs["Shutouts"] = pd.DataFrame()
        except Exception as e:
            print(f"   ⚠️ Could not combine Complete Games & Shutouts: {e}")

        if not b2b_data[0].empty:
            milestone_dfs["Consecutive HR Instances"] = b2b_data[0]
        
        # Add triple play detection
        triple_play_df = self._detect_triple_plays()
        if not triple_play_df.empty:
            milestone_dfs["Triple Plays"] = triple_play_df

        # Add 3-pitch innings
        three_pitch_df = self._detect_three_pitch_innings()
        if not three_pitch_df.empty:
            milestone_dfs["3 Pitch Innings"] = three_pitch_df

        # Add 3-strikeout innings
        three_ko_df = self._detect_three_strikeout_innings()
        if not three_ko_df.empty:
            milestone_dfs["3 Strikeout Innings"] = three_ko_df

        # Add immaculate innings
        immaculate_df = self._detect_immaculate_innings()
        if not immaculate_df.empty:
            milestone_dfs["Immaculate Innings"] = immaculate_df

        # Extract game IDs for different types
        b2b_game_ids = list(b2b_data[1]["GameID"].unique()) if len(b2b_data[1]) > 0 else []
        b2b2b_game_ids = list(b2b_data[2]["GameID"].unique()) if len(b2b_data[2]) > 0 else []
        b2b2b2b_game_ids = list(b2b_data[3]["GameID"].unique()) if len(b2b_data[3]) > 0 else []

        # Count total milestones
        total_milestones = sum(len(df) for df in milestone_dfs.values() if not df.empty)
        print(f"   ✅ Processed {total_milestones} milestone events across {len([df for df in milestone_dfs.values() if not df.empty])} categories")

        return milestone_dfs, b2b_game_ids, b2b2b_game_ids, b2b2b2b_game_ids, b2b_data[1], b2b_data[2], b2b_data[3], triple_play_df
    
    def _process_inside_park_hrs(self, game, milestone_tabs, basic_info, max_innings):
        """Process inside-the-park home runs from play-by-play data."""
        try:
            for play in game.get("play_by_play", []):
                if play.get("inside_the_park_hr"):
                    batter = play.get("batter", "Unknown")
                    team = standardize_team_code(play.get("batting_team", ""))
                    opponent = standardize_team_code(play.get("pitching_team", ""))
                    inning = play.get("inning", "")
                    half = play.get("half", "").title()
                    pitcher = play.get("pitcher", "Unknown")
                    rbi = play.get("rbi", 1)  # Get the corrected RBI count
                    
                    # Build detail string
                    detail = f"{half} {inning}"
                    if rbi > 1:
                        detail += f" ({rbi} RBI)"
                    if pitcher != "Unknown":
                        detail += f" off {pitcher}"
                    
                    inside_park_item = {
                        "player": batter,
                        "team_code": team,
                        "opponent_code": opponent,
                        "game_id": game.get("game_id", ""),
                        "rbi": rbi,
                        "inning": inning,
                        "half": half,
                        "pitcher": pitcher
                    }
                    
                    self._add_milestone(milestone_tabs, "Inside-the-Park HRs", basic_info, 
                                    inside_park_item, detail, max_innings)
                                    
        except Exception as e:
            print(f"   ⚠️ Error processing inside-the-park HRs: {e}")

    def _initialize_milestone_tabs(self):
        """Initialize empty milestone tracking dictionaries."""
        return {
            "Walk-Offs": [],
            "4+ Hit Games": [],
            "5+ RBI Games": [], 
            "Grand Slams": [],
            "Multi-HR Games": [],
            "Cycles": [],
            "10+ K Games": [],
            "Shutouts": [],
            "Complete Games": [],
            "Quality Starts": [],
            "No-Hitters": [],
            "Leadoff HRs": [],
            "Inside-the-Park HRs": [],
            "Pinch Hit HRs": [],
            "3 Strikeout Innings": [],
            "Immaculate Innings": []
        }
    
    def _extract_game_milestones(self, game, milestone_tabs):
        """Extract milestone data from a processed game."""
        basic_info = game.get("basic_info", {})
        milestones = game.get("milestone_stats", {})
        special_events = game.get("special_events", {})
        linescore = game.get("linescore", {})
        
        # Calculate max innings for score display
        max_innings = self._calculate_max_innings(linescore)
        
        # Process milestone stats from MilestoneEngine
        milestone_mapping = [
            ("four_hit_games", "4+ Hit Games", lambda x: f"{x.get('hits', 0)} H"),
            ("five_rbi_games", "5+ RBI Games", lambda x: f"{x.get('rbi', 0)} RBI"),
            ("grand_slams", "Grand Slams", lambda x: f"{x.get('half', '').title()} {x.get('inning', '')} - Grand Slam"),
            ("multi_hr_games", "Multi-HR Games", lambda x: f"{x.get('home_runs', 0)} HR"),
            ("cycles", "Cycles", lambda x: "Cycle"),
            ("ten_k_games", "10+ K Games", lambda x: f"{x.get('strikeouts', 0)} K"),
            ("shutouts", "Shutouts", lambda x: f"{x.get('innings_pitched', '')} IP, {x.get('hits', 0)} H, {x.get('runs', 0)} R, {x.get('walks', 0)} BB, {x.get('strikeouts', 0)} K, {x.get('pitch_count', '?')} pitches"),
            ("complete_games", "Complete Games", lambda x: f"{x.get('innings_pitched', '')} IP, {x.get('hits', 0)} H, {x.get('runs', 0)} R, {x.get('walks', 0)} BB, {x.get('strikeouts', 0)} K, {x.get('pitch_count', '?')} pitches"),
            ("no_hitters", "No-Hitters", lambda x: f"{x.get('innings_pitched', '')} IP, {x.get('walks', 0)} BB, {x.get('strikeouts', 0)} K, {x.get('pitch_count', '?')} pitches"),
            ("quality_starts", "Quality Starts", lambda x: f"{x.get('innings_pitched', '')} IP, {x.get('earned_runs', 0)} ER, {x.get('hits', 0)} H, {x.get('walks', 0)} BB, {x.get('strikeouts', 0)} K, {x.get('pitch_count', '?')} pitches"),
        ]
        
        for key, tab, detail_func in milestone_mapping:
            for item in milestones.get(key, []):
                try:
                    self._add_milestone(milestone_tabs, tab, basic_info, item, detail_func(item), max_innings)
                except Exception as e:
                    print(f"   ⚠️ Error adding {tab} milestone: {e}")
        
        # Process special events from SpecialEventsEngine
        self._process_special_events(special_events, milestone_tabs, basic_info, max_innings)
    
        # Process inside-the-park home runs from play-by-play
        self._process_inside_park_hrs(game, milestone_tabs, basic_info, max_innings)

    def _process_special_events(self, special_events, milestone_tabs, basic_info, max_innings):
        """Process special events from SpecialEventsEngine."""
        try:
            # Walk-offs
            walkoff = special_events.get("walkoff")
            if walkoff:
                self._add_milestone(milestone_tabs, "Walk-Offs", basic_info, walkoff, 
                                  walkoff.get("description", "Walk-off"), max_innings)
            
            # Leadoff home runs
            for leadoff_hr in special_events.get("leadoff_hrs", []):
                pitcher = leadoff_hr.get("pitcher", "")
                half = leadoff_hr.get("half", "").title()
                inning = "1st"

                detail = f"{half} {inning}"
                if pitcher:
                    detail += f" (off {pitcher})"

                self._add_milestone(milestone_tabs, "Leadoff HRs", basic_info, leadoff_hr, detail, max_innings)
            
            # Grand slams from special events
            for grand_slam in special_events.get("grand_slams", []):
                half = grand_slam.get('half', '').title()
                inning = grand_slam.get('inning', '')
                pitcher = grand_slam.get('pitcher', '')

                if pitcher:
                    detail = f"{half} {inning} (off {pitcher})"
                else:
                    detail = f"{half} {inning}"

                self._add_milestone(milestone_tabs, "Grand Slams", basic_info, grand_slam, detail, max_innings)
             
            # Pinch hit home runs  
            for pinch_hr in special_events.get("pinch_hit_hrs", []):
                hrs = pinch_hr.get('home_runs', 1)
                rbi = pinch_hr.get('rbi', 0) 
                pitcher = pinch_hr.get('pitcher', '')
                inning = pinch_hr.get('inning', '')
                half = pinch_hr.get('half', '')
                replaced_player = pinch_hr.get('replaced_player', 'Unknown')
                
                # Build inning string
                inning_str = ""
                if half and inning:
                    inning_str = f"{half.title()} {inning}"
                elif inning:
                    inning_str = f"Inning {inning}"
                
                # Build detail string with inning, RBI, and pitcher
                detail_parts = [f"Pinch Hit HR ({hrs} HR, {rbi} RBI)"]
                
                if inning_str:
                    detail_parts.append(f"in {inning_str}")
                
                if pitcher:
                    detail_parts.append(f"off {pitcher}")
                
                detail = " ".join(detail_parts)
                
                # CUSTOM: Add pinch hit HR with special columns instead of using generic _add_milestone
                player = pinch_hr.get("player", "Unknown")
                team_code = unify_team_code(
                    pinch_hr.get("team_code", "") or safe_get_str(basic_info, "home_team_code", "")
                )
                opponent_code = unify_team_code(
                    pinch_hr.get("opponent_code", "") or safe_get_str(basic_info, "away_team_code", "")
                )
                score = self._create_score_string(basic_info, max_innings)
                
                milestone_tabs["Pinch Hit HRs"].append({
                    "Date": safe_get_str(basic_info, "date_yyyymmdd", ""),
                    "Player": player,
                    "Team": team_code,
                    "Opponent": opponent_code,
                    "Score": score,
                    "Detail": detail,
                    "Replaced Player": replaced_player,  # ← PRESERVE THIS SPECIAL FIELD
                    "GameID": pinch_hr.get("game_id", safe_get_str(basic_info, "game_id", ""))
                })
       
        except Exception as e:
            print(f"   ⚠️ Error processing special events: {e}")
    
    
    def _process_footer_multi_hr(self, game, milestone_tabs, basic_info, max_innings):
        """Process multi-HR games from footer data as backup."""
        try:
            footer_summary = game.get("footer_summary", {})
            game_id = safe_get_str(game, "game_id", "UNKNOWN")
            
            for side in ("home", "away"):
                side_data = footer_summary.get(side, {})
                if not isinstance(side_data, dict):
                    continue
                
                hr_blob = side_data.get("HR", "")
                if not hr_blob:
                    continue
                
                team_code = unify_team_code(basic_info.get(f"{side}_team_code", ""))
                opponent_code = unify_team_code(
                    basic_info.get("home_team_code" if side == "away" else "away_team_code", "")
                )
                
                # Extract multi-HR players from footer
                for name, count in ExcelGeneratorUtils.extract_stat_counts(hr_blob):
                    if count >= 2:
                        milestone_item = {
                            "player": name,
                            "team_code": team_code,
                            "opponent_code": opponent_code,
                            "game_id": game_id
                        }
                        self._add_milestone(milestone_tabs, "Multi-HR Games", basic_info, 
                                          milestone_item, f"{count} HR", max_innings)
                        
        except Exception as e:
            print(f"   ⚠️ Error processing footer multi-HR: {e}")
    
    def _add_milestone(self, milestone_tabs, tab, basic_info, item, detail, max_innings):
        """Add a milestone event to the appropriate tab."""
        try:
            # Get player name from various possible sources
            player = (item.get("player") or item.get("batter") or 
                    safe_get_str(item, "name", "Unknown"))
            
            # Get team codes
            team_code = unify_team_code(
                item.get("team_code", "") or safe_get_str(basic_info, "home_team_code", "")
            )
            opponent_code = unify_team_code(
                item.get("opponent_code", "") or safe_get_str(basic_info, "away_team_code", "")
            )
            
            # Create score string
            score = self._create_score_string(basic_info, max_innings)
            
            # Base milestone record
            milestone_record = {
                "Date": safe_get_str(basic_info, "date_yyyymmdd", ""),
                "Player": player,
                "Team": team_code,
                "Opponent": opponent_code,
                "Score": score,
                "Detail": detail,
                "GameID": item.get("game_id", safe_get_str(basic_info, "game_id", ""))
            }
            
            # CONSISTENT APPROACH: All hitting milestones preserve complete stat lines
            if tab in ["Multi-HR Games", "4+ Hit Games", "5+ RBI Games", "Cycles", "Grand Slams"]:
                # Add complete batting stats from the milestone item (with footer data)
                batting_stats = {
                    "HR": item.get("home_runs", 0),
                    "2B": item.get("doubles", 0), 
                    "3B": item.get("triples", 0),
                    "H": item.get("hits", 0),
                    "R": item.get("runs", 0),
                    "RBI": item.get("rbi", 0),
                    "AB": item.get("ab", 0),
                    "BB": item.get("bb", 0),
                    "SO": item.get("so", 0)
                }
                milestone_record.update(batting_stats)
                    
            elif tab in ["10+ K Games", "Complete Games", "Shutouts", "Quality Starts", "No-Hitters"]:
                # Add pitching stats for pitching milestones
                pitching_stats = {
                    "IP": item.get("innings_pitched", "0.0"),
                    "H": item.get("hits", 0),
                    "R": item.get("runs_allowed", 0),
                    "ER": item.get("earned_runs", 0), 
                    "BB": item.get("walks_allowed", 0),
                    "SO": item.get("strikeouts", 0),
                    "Decision": item.get("decision", ""),
                    "Pitches": item.get("pitch_count", 0)
                }
                # Only add meaningful stats for pitching
                for stat_name, stat_value in pitching_stats.items():
                    if stat_value or stat_name == "Decision":
                        milestone_record[stat_name] = stat_value
            
            # Append the complete record
            milestone_tabs[tab].append(milestone_record)
            
        except Exception as e:
            print(f"   ⚠️ Error adding milestone to {tab}: {e}")

    def _create_score_string(self, basic_info, max_innings):
        """Create standardized score string for milestones."""
        try:
            return ExcelGeneratorUtils.format_score_string(basic_info, max_innings)
        except Exception:
            # Fallback to basic format
            away_code = safe_get_str(basic_info, "away_team_code", "UNK")
            home_code = safe_get_str(basic_info, "home_team_code", "UNK")
            away_score = safe_get_int(basic_info, "away_score_value", 0)
            home_score = safe_get_int(basic_info, "home_score_value", 0)
            return f"{away_code} {away_score} – {home_score} {home_code}"
    
    def _calculate_max_innings(self, linescore):
        """Calculate maximum innings played in the game."""
        try:
            innings_home = len(linescore.get('home', {}).get('innings', []))
            innings_away = len(linescore.get('away', {}).get('innings', []))
            return max(innings_home, innings_away, 9)
        except Exception:
            return 9
      
    def _detect_three_pitch_innings(self):
        """Detect 3-pitch innings."""
        try:
            three_pitch_innings = []
            
            for game in self.games:
                basic_info = self.get_basic_info(game)
                date = safe_get_str(basic_info, "date_yyyymmdd", "")
                game_id = self.get_game_id(game)
                
                # Track half-inning data
                half_inning_tracker = {}

                for play in game.get("play_by_play", []):
                    if not isinstance(play, dict):
                        continue
                        
                    inning = safe_get_int(play, "inning", 0)
                    half = safe_get_str(play, "half", "")
                    pitching_team = safe_get_str(play, "pitching_team", "")
                    batting_team = safe_get_str(play, "batting_team", "")
                    
                    if not all([inning, half, pitching_team]):
                        continue
                    
                    key = (inning, half, pitching_team)
                    if key not in half_inning_tracker:
                        half_inning_tracker[key] = {
                            "pitches": 0,
                            "outs": 0,
                            "plays": [],
                            "pitcher": safe_get_str(play, "pitcher", "Unknown"),
                            "team": pitching_team,
                            "opponent": batting_team,
                        }

                    pitch_count = safe_get_int(play, "pitch_count", 0)
                    if pitch_count > 0:
                        half_inning_tracker[key]["pitches"] += pitch_count

                    description = safe_get_str(play, "description", "").lower()
                    if any(keyword in description for keyword in 
                           ["flyball", "groundout", "lineout", "popfly", "strikeout", "double play", "triple play"]):
                        half_inning_tracker[key]["outs"] += 1

                    cleaned_desc = self._clean_play_description(description)
                    half_inning_tracker[key]["plays"].append(cleaned_desc)
                    

                # Check for 3-pitch innings
                for (inning, half, team), result in half_inning_tracker.items():
                    if result["pitches"] == 3 and result["outs"] == 3:
                        three_pitch_innings.append({
                            "Date": date,
                            "Player": result["pitcher"],
                            "Team": unify_team_code(standardize_team_code(result["team"])),
                            "Opponent": unify_team_code(standardize_team_code(result["opponent"])),
                            "Inning": f"{half.capitalize()} {inning}",
                            "Pitches": result["pitches"],
                            "Outs": result["outs"],
                            "Plays": " | ".join(result["plays"]),
                            "GameID": game_id
                        })

            if three_pitch_innings:
                df_3pi = pd.DataFrame(three_pitch_innings)
                df_3pi = ExcelGeneratorUtils.finalize_date_column(df_3pi, col="Date", in_format="%Y%m%d")
                return df_3pi
            else:
                return pd.DataFrame()
                
        except Exception as e:
            print(f"   ⚠️ Error detecting 3-pitch innings: {e}")
            return pd.DataFrame()

    def _detect_three_strikeout_innings(self):
        """Detect innings where a single pitcher strikes out all 3 batters consecutively."""
        try:
            three_strikeout_innings = []
            
            for game in self.games:
                basic_info = self.get_basic_info(game)
                date = safe_get_str(basic_info, "date_yyyymmdd", "")
                game_id = self.get_game_id(game)
                
                # Track by individual pitcher within each half-inning
                pitcher_tracker = {}

                for play in game.get("play_by_play", []):
                    if not isinstance(play, dict):
                        continue
                        
                    inning = safe_get_int(play, "inning", 0)
                    half = safe_get_str(play, "half", "")
                    pitching_team = safe_get_str(play, "pitching_team", "")
                    batting_team = safe_get_str(play, "batting_team", "")
                    pitcher_name = safe_get_str(play, "pitcher", "Unknown")
                    batter_name = safe_get_str(play, "batter", "Unknown")  # ADD: Get batter name
                    
                    if not all([inning, half, pitching_team, pitcher_name]):
                        continue
                    
                    # Key tracks individual pitcher in specific half-inning
                    key = (inning, half, pitching_team, pitcher_name)
                    if key not in pitcher_tracker:
                        pitcher_tracker[key] = {
                            "strikeouts": 0,
                            "swinging_strikeouts": 0,
                            "looking_strikeouts": 0,
                            "batters_struck_out": [],  # ADD: Track batter names
                            "non_strikeout_outs": 0,
                            "total_batters_faced": 0,
                            "total_pitches": 0,
                            "plays": [],
                            "pitcher": pitcher_name,
                            "team": pitching_team,
                            "opponent": batting_team,
                        }

                    # Count every plate appearance for this pitcher
                    pitcher_tracker[key]["total_batters_faced"] += 1

                    # ✅ ADD: Track pitch count for this plate appearance
                    pitch_count = safe_get_int(play, "pitch_count", 0)
                    if pitch_count > 0:
                        pitcher_tracker[key]["total_pitches"] += pitch_count

                    # Track strikeouts vs other types of outs
                    description = safe_get_str(play, "description", "").lower()
                    
                    if play.get("strikeout", False) or "struck out" in description or "strikeout" in description:
                        pitcher_tracker[key]["strikeouts"] += 1
                        pitcher_tracker[key]["batters_struck_out"].append(batter_name)  # ADD: Track batter name
                        
                        # ✅ ADD: Categorize swinging vs looking strikeouts
                        if any(keyword in description for keyword in [
                            "swinging", "swing", "missed", "whiff", "swung"
                        ]):
                            pitcher_tracker[key]["swinging_strikeouts"] += 1
                        elif any(keyword in description for keyword in [
                            "looking", "called", "watched", "took", "frozen"
                        ]):
                            pitcher_tracker[key]["looking_strikeouts"] += 1
                        else:
                            # If we can't determine, assume swinging (most common)
                            pitcher_tracker[key]["swinging_strikeouts"] += 1
                    elif any(keyword in description for keyword in 
                            ["flyball", "groundout", "lineout", "popfly", "double play", "triple play"]):
                        # This pitcher allowed a non-strikeout out - disqualifies the inning
                        if "double play" in description:
                            pitcher_tracker[key]["non_strikeout_outs"] += 2
                        elif "triple play" in description:
                            pitcher_tracker[key]["non_strikeout_outs"] += 3
                        else:
                            pitcher_tracker[key]["non_strikeout_outs"] += 1

                    cleaned_desc = self._clean_play_description(description)
                    pitcher_tracker[key]["plays"].append(cleaned_desc)

                # Check for perfect 3-strikeout innings by individual pitchers
                for (inning, half, team, pitcher), result in pitcher_tracker.items():
                    # Must have exactly 3 strikeouts, zero non-strikeout outs, and exactly 3 batters faced
                    # This means pure "3-up, 3-down" on strikeouts - no walks, hits, or other baserunners
                    if (result["strikeouts"] == 3 and 
                        result["non_strikeout_outs"] == 0 and
                        result["total_batters_faced"] == 3):
                        
                        # ADD: Format batter names and create breakdown
                        batters_formatted = " | ".join(result["batters_struck_out"][:3])
                        ko_breakdown = f"Swinging: {result['swinging_strikeouts']}, Looking: {result['looking_strikeouts']}"
                        
                        three_strikeout_innings.append({
                            "Date": date,
                            "Player": result["pitcher"],
                            "Team": unify_team_code(standardize_team_code(result["team"])),
                            "Opponent": unify_team_code(standardize_team_code(result["opponent"])),
                            "Inning": f"{half.capitalize()} {inning}",
                            "Batters Struck Out": batters_formatted,  # ADD: New column
                            "Strikeout Breakdown": ko_breakdown,     # ADD: New column  
                            "Swinging K": result["swinging_strikeouts"],
                            "Looking K": result["looking_strikeouts"],
                            "BF": result["total_batters_faced"],
                            "Pitches": result["total_pitches"],
                            "Plays": " | ".join(result["plays"][:3]),
                            "GameID": game_id,
                            "_sort_date": date,
                            "_sort_inning": inning,
                            "_sort_half": 0 if half.lower() == "top" else 1
                        })

            if three_strikeout_innings:
                # ✅ CRITICAL: Sort by date FIRST, then by game and inning order
                three_strikeout_innings.sort(key=lambda x: (
                    x.get("_sort_date", ""),     # Date first (YYYYMMDD format)
                    x["GameID"],                 # Then GameID
                    x.get("_sort_inning", 0),    # Then inning number
                    x.get("_sort_half", 0)       # Then half (top=0, bottom=1)
                ))
                
                # Convert dates but preserve the chronological order within games
                for record in three_strikeout_innings:
                    try:
                        date_str = record.get("_sort_date", "")
                        if date_str:
                            date_obj = datetime.strptime(date_str, "%Y%m%d")
                            record["Date"] = date_obj.strftime("%m/%d/%Y")
                        else:
                            record["Date"] = ""
                    except:
                        record["Date"] = record.get("_sort_date", "")
                    
                    # Remove sorting fields
                    record.pop("_sort_date", None)
                    record.pop("_sort_inning", None)
                    record.pop("_sort_half", None)
                
                # Create DataFrame WITHOUT calling finalize_date_column (which re-sorts)
                df_3ko = pd.DataFrame(three_strikeout_innings)
                return df_3ko
            else:
                return pd.DataFrame()
                
        except Exception as e:
            print(f"   ⚠️ Error detecting 3-strikeout innings: {e}")
            return pd.DataFrame()
        
    def _clean_play_description(self, description):
        """Clean up play descriptions for better readability."""
        if not description:
            return "Unknown"
        
        # Convert to title case and clean common patterns
        cleaned = description.strip()
        
        # Handle common play types
        play_mappings = {
            'flyball': 'Flyball',
            'lineout': 'Lineout', 
            'groundout': 'Groundout',
            'popfly': 'Pop Fly',
            'strikeout': 'Strikeout',
            'double play': 'Double Play',
            'triple play': 'Triple Play'
        }
        
        for old, new in play_mappings.items():
            if cleaned.startswith(old):
                cleaned = cleaned.replace(old, new, 1)
                break
        
        def capitalize_name(match):
            """Capitalize player names properly."""
            full_match = match.group(0)
            initial = match.group(1).upper()  # Capitalize the initial
            last_name = match.group(2).title()  # Title case the last name
            return f"{initial}. {last_name}"
        
        # Replace patterns like "a. slater" with "A. Slater"
        cleaned = re.sub(r'\b([a-z])\.\s*([a-z][a-z\-\']+)\b', capitalize_name, cleaned, flags=re.IGNORECASE)
        
        # Pattern for "First Last" names that might be all lowercase
        def capitalize_full_name(match):
            """Capitalize full names like 'john smith' -> 'John Smith'."""
            return match.group(0).title()
        
        # Look for sequences that look like "firstname lastname" 
        # (lowercase letters, space, lowercase letters - but avoid position codes like "1b", "cf")
        cleaned = re.sub(r'\b(?![0-9][a-z]\b)([a-z]{3,})\s+([a-z]{3,})\b', capitalize_full_name, cleaned)

        # Clean up position abbreviations (more comprehensive)
        position_patterns = [
            (r'\bcf\b', 'CF'),
            (r'\blf\b', 'LF'), 
            (r'\brf\b', 'RF'),
            (r'\bss\b', 'SS'),
            (r'\b1b\b', '1B'),
            (r'\b2b\b', '2B'),
            (r'\b3b\b', '3B'),
            (r'\bc\b', 'C'),
            (r'\bp\b', 'P')
        ]
        
        for pattern, replacement in position_patterns:
            cleaned = re.sub(pattern, replacement, cleaned, flags=re.IGNORECASE)
        
        # Capitalize first letter if not already done
        if cleaned and not cleaned[0].isupper():
            cleaned = cleaned[0].upper() + cleaned[1:]
        
        return cleaned

    def _detect_immaculate_innings(self):
        """Detect immaculate innings (3 strikeouts on exactly 9 pitches)."""
        try:
            immaculate_innings = []
            
            for game in self.games:
                basic_info = self.get_basic_info(game)
                date = safe_get_str(basic_info, "date_yyyymmdd", "")
                game_id = self.get_game_id(game)
                
                pitcher_tracker = {}

                for play in game.get("play_by_play", []):
                    if not isinstance(play, dict):
                        continue
                        
                    inning = safe_get_int(play, "inning", 0)
                    half = safe_get_str(play, "half", "")
                    pitching_team = safe_get_str(play, "pitching_team", "")
                    batting_team = safe_get_str(play, "batting_team", "")
                    pitcher_name = safe_get_str(play, "pitcher", "Unknown")
                    batter_name = safe_get_str(play, "batter", "Unknown")  # ADD: Get batter name
                    
                    if not all([inning, half, pitching_team, pitcher_name]):
                        continue
                    
                    key = (inning, half, pitching_team, pitcher_name)
                    if key not in pitcher_tracker:
                        pitcher_tracker[key] = {
                            "pitches": 0,
                            "strikeouts": 0,
                            "swinging_strikeouts": 0,  # ADD: Track swinging strikeouts
                            "looking_strikeouts": 0,   # ADD: Track looking strikeouts  
                            "batters_struck_out": [],  # ADD: Track batter names
                            "total_batters_faced": 0,
                            "non_strikeout_outs": 0,
                            "plays": [],
                            "pitcher": pitcher_name,
                            "team": pitching_team,
                            "opponent": batting_team,
                        }

                    pitch_count = safe_get_int(play, "pitch_count", 0)
                    if pitch_count > 0:
                        pitcher_tracker[key]["pitches"] += pitch_count

                    pitcher_tracker[key]["total_batters_faced"] += 1

                    description = safe_get_str(play, "description", "").lower()
                    
                    if play.get("strikeout", False) or "struck out" in description or "strikeout" in description:
                        pitcher_tracker[key]["strikeouts"] += 1
                        pitcher_tracker[key]["batters_struck_out"].append(batter_name)  # ADD: Track batter name
                        
                        # ADD: Categorize swinging vs looking strikeouts
                        if any(keyword in description for keyword in [
                            "swinging", "swing", "missed", "whiff", "swung"
                        ]):
                            pitcher_tracker[key]["swinging_strikeouts"] += 1
                        elif any(keyword in description for keyword in [
                            "looking", "called", "watched", "took", "frozen"
                        ]):
                            pitcher_tracker[key]["looking_strikeouts"] += 1
                        else:
                            # If we can't determine, assume swinging (most common)
                            pitcher_tracker[key]["swinging_strikeouts"] += 1
                    elif any(keyword in description for keyword in 
                            ["flyball", "groundout", "lineout", "popfly", "double play", "triple play"]):
                        pitcher_tracker[key]["non_strikeout_outs"] += 1

                    cleaned_desc = self._clean_play_description(description)
                    pitcher_tracker[key]["plays"].append(cleaned_desc)

                # Check for immaculate innings (exactly 9 pitches, 3 strikeouts, 3 batters, 0 other outs)
                for (inning, half, team, pitcher), result in pitcher_tracker.items():
                    if (result["pitches"] == 9 and 
                        result["strikeouts"] == 3 and 
                        result["total_batters_faced"] == 3 and
                        result["non_strikeout_outs"] == 0):
                        
                        # ADD: Format batter names
                        batters_formatted = " | ".join(result["batters_struck_out"][:3])
                        
                        immaculate_innings.append({
                            "Date": date,
                            "Player": result["pitcher"],
                            "Team": unify_team_code(standardize_team_code(result["team"])),
                            "Opponent": unify_team_code(standardize_team_code(result["opponent"])),
                            "Inning": f"{half.capitalize()} {inning}",
                            "Batters Struck Out": batters_formatted,  # ADD: New column
                            "Pitches": result["pitches"],
                            "Strikeouts": result["strikeouts"],
                            "Plays": " | ".join(result["plays"][:3]),
                            "GameID": game_id,
                            "_sort_inning": inning,
                            "_sort_half": 0 if half.lower() == "top" else 1
                        })

            if immaculate_innings:
                # Sort by game, then by inning order
                immaculate_innings.sort(key=lambda x: (
                    x["GameID"], 
                    x.get("_sort_inning", 0),
                    x.get("_sort_half", 0)
                ))
                
                # Remove sorting fields
                for record in immaculate_innings:
                    record.pop("_sort_inning", None)
                    record.pop("_sort_half", None)
                
                df_immac = pd.DataFrame(immaculate_innings)
                df_immac = ExcelGeneratorUtils.finalize_date_column(df_immac, col="Date", in_format="%Y%m%d")
                return df_immac
            else:
                return pd.DataFrame()
                
        except Exception as e:
            print(f"   ⚠️ Error detecting immaculate innings: {e}")
            return pd.DataFrame()
        
    def _detect_triple_plays(self):
        """Detect triple plays from play descriptions."""
        triple_plays = []
        for game in self.games:
            basic_info = self.get_basic_info(game)
            date = safe_get_str(basic_info, "date_yyyymmdd", "")
            game_id = self.get_game_id(game)
            for play in game.get("play_by_play", []):
                desc = safe_get_str(play, "description", "").lower()
                if "triple play" in desc:
                    inning = play.get("inning", "")
                    half = play.get("half", "")
                    team = safe_get_str(play, "fielding_team", "")
                    opp_team = safe_get_str(play, "batting_team", "")
                    batter = safe_get_str(play, "batter", "")
                    pitcher = safe_get_str(play, "pitcher", "")
                    triple_plays.append({
                        "Date": date,
                        "Inning": f"{half.title()} {inning}",
                        "Team": team,
                        "Opponent": opp_team,
                        "Batter": batter,
                        "Pitcher": pitcher,
                        "Description": play.get("description", ""),
                        "GameID": game_id
                    })
        if triple_plays:
            df_triple = pd.DataFrame(triple_plays)
            df_triple = ExcelGeneratorUtils.finalize_date_column(df_triple, col="Date", in_format="%Y%m%d")
            return df_triple
        else:
            return pd.DataFrame()
    
    def _detect_consecutive_home_runs(self):
        """Detect consecutive home run sequences."""
        try:
            b2b_rows = []
            total_b2b_events = 0
            longest_hr_chain = 0

            for game in self.games:
                game_id = self.get_game_id(game)
                basic_info = self.get_basic_info(game)
                date = safe_get_str(basic_info, "date_yyyymmdd", "")
                all_plays = game.get("raw_plays", [])
                
                if not all_plays:
                    continue

                home_team = safe_get_str(basic_info, "home_team", "")
                away_team = safe_get_str(basic_info, "away_team", "")

                current_team = None
                current_inning = None
                current_half = None
                hr_chain = []

                for play in all_plays:
                    desc = safe_get_str(play, "description", "").lower()
                    event_is_hr = any(keyword in desc for keyword in ["homered", "home run"])
                    team = safe_get_str(play, "batting_team", "")
                    inning = safe_get_int(play, "inning", 0)
                    half = safe_get_str(play, "half", "")
                    batter = safe_get_str(play, "batter", "Unknown")
                    pitcher = safe_get_str(play, "pitcher", "Unknown")

                    # Apply team code standardization
                    team_code = unify_team_code(standardize_team_code(team))
                    opp_name = home_team if team == away_team else away_team
                    opp_code = unify_team_code(standardize_team_code(opp_name))

                    is_same_context = (
                        team == current_team and
                        inning == current_inning and
                        half == current_half
                    )

                    if event_is_hr:
                        if is_same_context:
                            hr_chain.append((batter, pitcher, team_code, opp_code))
                        else:
                            if len(hr_chain) >= 2:
                                total_b2b_events += 1
                                longest_hr_chain = max(longest_hr_chain, len(hr_chain))
                                b2b_rows.append({
                                    "Date": date,
                                    "Team": hr_chain[0][2],
                                    "Opponent": hr_chain[0][3],
                                    "Inning": f"{current_half.title()} {current_inning}" if current_half and current_inning else "Unknown",
                                    "Players": ", ".join(p[0] for p in hr_chain),
                                    "Pitchers": ", ".join(set(p[1] for p in hr_chain)),
                                    "HR Count": len(hr_chain),
                                    "GameID": game_id
                                })
                            hr_chain = [(batter, pitcher, team_code, opp_code)]
                            current_team = team
                            current_inning = inning
                            current_half = half
                    else:
                        if len(hr_chain) >= 2:
                            total_b2b_events += 1
                            longest_hr_chain = max(longest_hr_chain, len(hr_chain))
                            b2b_rows.append({
                                "Date": date,
                                "Team": hr_chain[0][2],
                                "Opponent": hr_chain[0][3],
                                "Inning": f"{current_half.title()} {current_inning}" if current_half and current_inning else "Unknown",
                                "Players": ", ".join(p[0] for p in hr_chain),
                                "Pitchers": ", ".join(set(p[1] for p in hr_chain)),
                                "HR Count": len(hr_chain),
                                "GameID": game_id
                            })
                        hr_chain = []

                # Check final chain
                if len(hr_chain) >= 2:
                    total_b2b_events += 1
                    longest_hr_chain = max(longest_hr_chain, len(hr_chain))
                    b2b_rows.append({
                        "Date": date,
                        "Team": hr_chain[0][2],
                        "Opponent": hr_chain[0][3],
                        "Inning": f"{current_half.title()} {current_inning}" if current_half and current_inning else "Unknown",
                        "Players": ", ".join(p[0] for p in hr_chain),
                        "Pitchers": ", ".join(set(p[1] for p in hr_chain)),
                        "HR Count": len(hr_chain),
                        "GameID": game_id
                    })

            # Create DataFrames
            df_b2b2b = self.create_dataframe(b2b_rows)
            
            # Format dates properly
            if not df_b2b2b.empty:
                df_b2b2b = ExcelGeneratorUtils.finalize_date_column(df_b2b2b, col="Date", in_format="%Y%m%d")
            
            b2b_only_df = df_b2b2b[df_b2b2b["HR Count"] == 2] if not df_b2b2b.empty else pd.DataFrame()
            b2b2b_only_df = df_b2b2b[df_b2b2b["HR Count"] == 3] if not df_b2b2b.empty else pd.DataFrame()
            b2b2b2b_only_df = df_b2b2b[df_b2b2b["HR Count"] == 4] if not df_b2b2b.empty else pd.DataFrame()

            return df_b2b2b, b2b_only_df, b2b2b_only_df, b2b2b2b_only_df
            
        except Exception as e:
            print(f"   ⚠️ Error detecting consecutive home runs: {e}")
            return pd.DataFrame(), pd.DataFrame(), pd.DataFrame()
    
    def _clean_play_description(self, description):
        """Clean up play descriptions for better readability with proper name capitalization."""
        if not description:
            return "Unknown"
        
        # Convert to clean string
        cleaned = description.strip()
        
        import unicodedata
        cleaned = cleaned.replace('\xa0', ' ')
        cleaned = unicodedata.normalize('NFKD', cleaned)
        cleaned = re.sub(r'\s+', ' ', cleaned)
        
        # Handle common play types
        play_mappings = {
            'flyball': 'Flyball',
            'lineout': 'Lineout', 
            'groundout': 'Groundout',
            'popfly': 'Pop Fly',
            'strikeout': 'Strikeout',
            'double play': 'Double Play',
            'triple play': 'Triple Play'
        }
        
        for old, new in play_mappings.items():
            if cleaned.lower().startswith(old):
                cleaned = cleaned.replace(old, new, 1)
                break
        
        # Pattern for "first_initial. last_name" (like "a. slater", "d. romo")
        def capitalize_name(match):
            """Capitalize player names properly."""
            initial = match.group(1).upper()
            last_name = match.group(2).title()
            return f"{initial}. {last_name}"
        
        # Replace patterns like "a. slater" with "A. Slater"
        cleaned = re.sub(r'\b([a-z])\.\s*([a-z][a-z\-\']+)\b', capitalize_name, cleaned, flags=re.IGNORECASE)
        
        # Pattern for "First Last" names that might be all lowercase
        def capitalize_full_name(match):
            """Capitalize full names like 'john smith' -> 'John Smith'."""
            return match.group(0).title()
        
        # Look for sequences that look like "firstname lastname" 
        # (lowercase letters, space, lowercase letters - but avoid position codes like "1b", "cf")
        cleaned = re.sub(r'\b(?![0-9][a-z]\b)([a-z]{3,})\s+([a-z]{3,})\b', capitalize_full_name, cleaned)
        
        # ✅ IMPROVED: Position abbreviations with better boundary detection
        position_patterns = [
            (r'\bcf\b', 'CF'),
            (r'\blf\b', 'LF'), 
            (r'\brf\b', 'RF'),
            (r'\bss\b', 'SS'),
            (r'\b1b\b', '1B'),
            (r'\b2b\b', '2B'),
            (r'\b3b\b', '3B'),
            (r'\bc\b(?![a-z])', 'C'),  # Don't replace 'c' in middle of words
            (r'\bp\b(?![a-z])', 'P')   # Don't replace 'p' in middle of words
        ]
        
        for pattern, replacement in position_patterns:
            cleaned = re.sub(pattern, replacement, cleaned, flags=re.IGNORECASE)
        
        # Capitalize first letter if not already done
        if cleaned and not cleaned[0].isupper():
            cleaned = cleaned[0].upper() + cleaned[1:]
        
        return cleaned
    
    def _create_milestone_dataframes(self, milestone_tabs):
        """Convert milestone lists to formatted DataFrames with support for special columns."""
        milestone_dfs = {}
        
        # Standard columns for most milestones
        standard_cols = ["Date", "Player", "Team", "Opponent", "Score", "Detail", "GameID"]
        
        for tab, rows in milestone_tabs.items():
            try:
                if not rows:
                    milestone_dfs[tab] = pd.DataFrame()
                    continue
                
                # CRITICAL FIX: Don't restrict columns - use ALL columns that exist in the data
                if rows:
                    # Get all unique keys from all rows
                    all_keys = set()
                    for row in rows:
                        all_keys.update(row.keys())
                    
                    
                    # Create DataFrame with ALL columns that exist in the data
                    df = pd.DataFrame(rows)
                    
                    # Optional: Reorder columns to put standard ones first, then stats
                    available_standard = [col for col in standard_cols if col in df.columns]
                    stat_columns = [col for col in df.columns if col not in standard_cols]
                    
                    if available_standard:
                        final_cols = available_standard + sorted(stat_columns)
                        df = df[final_cols]
                    
                else:
                    df = pd.DataFrame(columns=standard_cols)
                
                if not df.empty:
                    # Convert dates safely
                    df = ExcelGeneratorUtils.finalize_date_column(df, col="Date", in_format="%Y%m%d")
                
                milestone_dfs[tab] = df
                    
            except Exception as e:
                print(f"   ⚠️ Error creating DataFrame for {tab}: {e}")
                milestone_dfs[tab] = pd.DataFrame()
                
        return milestone_dfs

    def print_comprehensive_summary(self, milestone_dfs, previous_run_file=None, days_back=7):
        """Print comprehensive summary combining new vs previous and recent additions."""
        from datetime import datetime, timedelta
        import os
        
        print("\n" + "="*60)
        print("RUN SUMMARY REPORT")
        print("="*60)
        
        # Section 1: New vs Previous Run Comparison
        if previous_run_file and os.path.exists(previous_run_file):
            print(f"\nNEW ITEMS vs PREVIOUS RUN:")
            print("-" * 30)
            
            total_new_vs_previous = 0
            
            for category, df in milestone_dfs.items():
                if df.empty:
                    continue
                    
                try:
                    previous_df = pd.read_excel(previous_run_file, sheet_name=category)
                    new_count = len(df) - len(previous_df)
                    
                    if new_count > 0:
                        print(f"\n{category}: +{new_count} new items")
                        new_items = df.tail(new_count)
                        
                        for _, row in new_items.iterrows():
                            # Handle both 'Player' (singular) and 'Players' (plural, for consecutive HRs)
                            player = row.get('Player', row.get('Players', 'Unknown'))
                            date = row.get('Date', 'Unknown')
                            team = row.get('Team', '')
                            opponent = row.get('Opponent', '')

                            if category in ["3 Strikeout Innings", "Immaculate Innings"]:
                                inning = row.get('Inning', '')
                                batters = row.get('Batters Struck Out', '')
                                print(f"   • {player} ({team} vs {opponent}) - {date} {inning}")
                                if batters:
                                    print(f"     Struck out: {batters}")
                            else:
                                print(f"   • {player} ({team}) - {date}")
                        
                        total_new_vs_previous += new_count
                    elif new_count == 0:
                        print(f"{category}: No new items")
                        
                except Exception as e:
                    print(f"{category}: Unable to compare (file may not exist yet)")
            
            if total_new_vs_previous > 0:
                print(f"\nTotal new items since last run: {total_new_vs_previous}")
            else:
                print(f"\nNo new items since last run")
        
        # Section 2: Overall Totals
        print(f"\n\nOVERALL TOTALS:")
        print("-" * 30)
        
        categories_with_data = []
        grand_total = 0
        
        for category, df in milestone_dfs.items():
            if not df.empty:
                count = len(df)
                categories_with_data.append((category, count))
                grand_total += count
                print(f"{category}: {count}")
        
        print(f"\nTotal milestone events: {grand_total}")
        print(f"Categories with data: {len(categories_with_data)}")
        
        # Section 3: 2025 Events (moved to end)
        cutoff_date = datetime(2025, 1, 1)  # All events from 2025
        
        print(f"\n\nEVENTS FROM 2025:")
        print("-" * 30)
        
        total_2025 = 0
        events_2025_by_category = {}
        
        for category, df in milestone_dfs.items():
            if df.empty:
                continue
                
            try:
                df_copy = df.copy()
                df_copy['Date'] = pd.to_datetime(df_copy['Date'])
                events_2025 = df_copy[df_copy['Date'] >= cutoff_date]
                
                if not events_2025.empty:
                    events_2025_by_category[category] = events_2025
                    total_2025 += len(events_2025)
            except:
                continue
        
        if events_2025_by_category:
            for category, events_2025 in events_2025_by_category.items():
                print(f"\n{category} ({len(events_2025)} in 2025):")
                
                for _, row in events_2025.iterrows():
                    # Handle both 'Player' (singular) and 'Players' (plural, for consecutive HRs)
                    player = row.get('Player', row.get('Players', 'Unknown'))
                    date = row['Date'].strftime('%m/%d/%Y')
                    team = row.get('Team', '')
                    opponent = row.get('Opponent', '')

                    if category in ["3 Strikeout Innings", "Immaculate Innings"]:
                        inning = row.get('Inning', '')
                        batters = row.get('Batters Struck Out', '')
                        pitches = row.get('Pitches', '')
                        
                        print(f"   • {player} ({team} vs {opponent}) - {date} {inning}")
                        if batters:
                            print(f"     Struck out: {batters}")
                        if pitches and category == "Immaculate Innings":
                            print(f"     Pitches: {pitches}")
                    else:
                        print(f"   • {player} ({team}) - {date}")
            
            print(f"\nTotal 2025 events: {total_2025}")
        else:
            print("No events found in 2025")
        
        print("="*60)

    def save_run_metadata(self, milestone_dfs, output_file_path):
        """Save metadata about this run for future comparison."""
        import json
        from datetime import datetime
        
        metadata = {
            "run_date": datetime.now().isoformat(),
            "output_file": output_file_path,
            "totals_by_category": {}
        }
        
        for category, df in milestone_dfs.items():
            metadata["totals_by_category"][category] = len(df) if not df.empty else 0
        
        # Save to a metadata file
        metadata_file = output_file_path.replace('.xlsx', '_metadata.json')
        try:
            with open(metadata_file, 'w') as f:
                json.dump(metadata, f, indent=2)
            print(f"Saved run metadata to: {metadata_file}")
        except Exception as e:
            print(f"Could not save metadata: {e}")

    def print_quick_summary(self, milestone_dfs):
        """Print a quick summary for regular runs."""
        print("\n" + "="*40)
        print("PROCESSING COMPLETE")
        print("="*40)
        
        non_empty_categories = []
        total_items = 0
        
        for category, df in milestone_dfs.items():
            if not df.empty:
                count = len(df)
                non_empty_categories.append((category, count))
                total_items += count
        
        if non_empty_categories:
            print("Categories with data:")
            for category, count in non_empty_categories:
                print(f"  {category}: {count}")
            
            print(f"\nTotal milestone events: {total_items}")
            
            # Highlight strikeout innings specifically
            strikeout_categories = [cat for cat, count in non_empty_categories 
                                if "Strikeout" in cat or "Immaculate" in cat]
            if strikeout_categories:
                print("\nStrikeout milestone highlights:")
                for category in strikeout_categories:
                    df = milestone_dfs[category]
                    if not df.empty:
                        latest = df.iloc[-1]
                        player = latest.get('Player', 'Unknown')
                        date = latest.get('Date', 'Unknown')
                        print(f"  Latest {category}: {player} - {date}")
        else:
            print("No milestone events found in this run")
        
        print("="*40)
        
        return milestone_dfs


class PracticalMilestoneEnhancer:
    """Enhance milestone tabs with useful information without over-complication."""
    
    def __init__(self, games):
        self.games = games
    
    def enhance_quality_starts(self, basic_qs_data):
        """Add complete pitching line to Quality Starts, removing Detail column."""
        if basic_qs_data is None or basic_qs_data.empty:
            return pd.DataFrame()
        
        enhanced_records = []
        
        for _, record in basic_qs_data.iterrows():
            game_id = record.get("GameID", "")
            player_name = record.get("Player", "")
            team_code = record.get("Team", "")
            
            game = self._get_game_by_id(game_id)
            if not game:
                enhanced_records.append(record.to_dict())
                continue
            
            pitching_stats = self._get_pitcher_stats(game, player_name)
            
            enhanced = {
                "Date": record.get("Date"),
                "Player": player_name,
                "Team": team_code,
                "Opponent": record.get("Opponent"),
                "Home/Away": self._determine_home_away(game, team_code),
                "IP": self._format_ip_with_decimal(pitching_stats.get("IP", "6.0")),
                "H": pitching_stats.get("H", 0),
                "R": pitching_stats.get("R", 0), 
                "ER": pitching_stats.get("ER", 0),
                "BB": pitching_stats.get("BB", 0),
                "SO": pitching_stats.get("SO", 0),
                "Pitches": pitching_stats.get("Pit", 0) or 0,
                "WHIP": self._calculate_whip(pitching_stats),
                "Decision": pitching_stats.get("decision", "ND"),
                "GameID": game_id
            }
            
            enhanced_records.append(enhanced)
        
        return pd.DataFrame(enhanced_records)
    
    def enhance_multi_hr_games(self, basic_data):
        """Add complete hitting line to Multi-HR games, removing Detail column."""
        if basic_data is None or basic_data.empty:
            return pd.DataFrame()
        
        enhanced_records = []
        
        for _, record in basic_data.iterrows():
            game_id = record.get("GameID", "")
            player_name = record.get("Player", "")
            team_code = record.get("Team", "")
            
            game = self._get_game_by_id(game_id)
            if not game:
                enhanced_records.append(record.to_dict())
                continue
            
            # Start with base info (no Detail column)
            enhanced = {
                "Date": record.get("Date"),
                "Player": player_name,
                "Team": team_code,
                "Opponent": record.get("Opponent"),
                "Home/Away": self._determine_home_away(game, team_code),
                "GameID": game_id
            }
            
            # Get complete hitting stats - prefer preserved footer stats, fallback to box score
            if any(stat in record and record[stat] > 0 for stat in ["HR", "2B", "3B"]):
                enhanced.update({
                    "AB": record.get("AB", 0),
                    "H": record.get("H", 0), 
                    "R": record.get("R", 0),
                    "RBI": record.get("RBI", 0),
                    "HR": record.get("HR", 0),
                    "2B": record.get("2B", 0),
                    "3B": record.get("3B", 0),
                    "BB": record.get("BB", 0),
                    "SO": record.get("SO", 0)
                })
            else:
                # Fallback to box score lookup
                print(f"   ⚠️ Using box score lookup for {player_name}")
                hitting_stats = self._get_hitter_stats(game, player_name)
                enhanced.update({
                    "AB": hitting_stats.get("AB", 0),
                    "H": hitting_stats.get("H", 0),
                    "R": hitting_stats.get("R", 0),
                    "RBI": hitting_stats.get("RBI", 0),
                    "HR": hitting_stats.get("HR", 0),
                    "2B": hitting_stats.get("2B", 0),
                    "3B": hitting_stats.get("3B", 0),
                    "BB": hitting_stats.get("BB", 0),
                    "SO": hitting_stats.get("SO", 0)
                })
            
            enhanced_records.append(enhanced)
        
        return pd.DataFrame(enhanced_records)

    def enhance_four_hit_games(self, basic_data):
        """Add complete hitting line to 4+ Hit games, removing Detail column."""
        if basic_data is None or basic_data.empty:
            return pd.DataFrame()
        
        enhanced_records = []
        
        for _, record in basic_data.iterrows():
            game_id = record.get("GameID", "")
            player_name = record.get("Player", "")
            team_code = record.get("Team", "")
            
            game = self._get_game_by_id(game_id)
            if not game:
                enhanced_records.append(record.to_dict())
                continue
            
            enhanced = {
                "Date": record.get("Date"),
                "Player": player_name,
                "Team": team_code,
                "Opponent": record.get("Opponent"),
                "Home/Away": self._determine_home_away(game, team_code),
                "GameID": game_id
            }
            
            # Get complete hitting stats
            if any(stat in record and record[stat] > 0 for stat in ["HR", "2B", "3B", "H"]):
                # Use preserved stats
                enhanced.update({
                    "AB": record.get("AB", 0),
                    "H": record.get("H", 0),
                    "R": record.get("R", 0),
                    "RBI": record.get("RBI", 0),
                    "HR": record.get("HR", 0),
                    "2B": record.get("2B", 0),
                    "3B": record.get("3B", 0),
                    "BB": record.get("BB", 0),
                    "SO": record.get("SO", 0)
                })
            else:
                # Box score lookup
                hitting_stats = self._get_hitter_stats(game, player_name)
                enhanced.update({
                    "AB": hitting_stats.get("AB", 0),
                    "H": hitting_stats.get("H", 0),
                    "R": hitting_stats.get("R", 0),
                    "RBI": hitting_stats.get("RBI", 0),
                    "HR": hitting_stats.get("HR", 0),
                    "2B": hitting_stats.get("2B", 0),
                    "3B": hitting_stats.get("3B", 0),
                    "BB": hitting_stats.get("BB", 0),
                    "SO": hitting_stats.get("SO", 0)
                })
            
            enhanced_records.append(enhanced)
        
        return pd.DataFrame(enhanced_records)

    def enhance_five_rbi_games(self, basic_data):
        """Add complete hitting line to 5+ RBI games, removing Detail column."""
        if basic_data is None or basic_data.empty:
            return pd.DataFrame()
        
        enhanced_records = []
        
        for _, record in basic_data.iterrows():
            game_id = record.get("GameID", "")
            player_name = record.get("Player", "")
            team_code = record.get("Team", "")
            
            game = self._get_game_by_id(game_id)
            if not game:
                enhanced_records.append(record.to_dict())
                continue
            
            enhanced = {
                "Date": record.get("Date"),
                "Player": player_name,
                "Team": team_code,
                "Opponent": record.get("Opponent"),
                "Home/Away": self._determine_home_away(game, team_code),
                "GameID": game_id
            }
            
            # Get complete hitting stats
            if any(stat in record and record[stat] > 0 for stat in ["HR", "2B", "3B", "RBI"]):
                # Use preserved stats
                enhanced.update({
                    "AB": record.get("AB", 0),
                    "H": record.get("H", 0),
                    "R": record.get("R", 0),
                    "RBI": record.get("RBI", 0),
                    "HR": record.get("HR", 0),
                    "2B": record.get("2B", 0),
                    "3B": record.get("3B", 0),
                    "BB": record.get("BB", 0),
                    "SO": record.get("SO", 0)
                })
            else:
                # Box score lookup
                hitting_stats = self._get_hitter_stats(game, player_name)
                enhanced.update({
                    "AB": hitting_stats.get("AB", 0),
                    "H": hitting_stats.get("H", 0),
                    "R": hitting_stats.get("R", 0),
                    "RBI": hitting_stats.get("RBI", 0),
                    "HR": hitting_stats.get("HR", 0),
                    "2B": hitting_stats.get("2B", 0),
                    "3B": hitting_stats.get("3B", 0),
                    "BB": hitting_stats.get("BB", 0),
                    "SO": hitting_stats.get("SO", 0)
                })
            
            enhanced_records.append(enhanced)
        
        return pd.DataFrame(enhanced_records)

    def enhance_cycles(self, basic_data):
        """Add complete hitting line to Cycles, removing Detail column."""
        if basic_data is None or basic_data.empty:
            return pd.DataFrame()
        
        enhanced_records = []
        
        for _, record in basic_data.iterrows():
            game_id = record.get("GameID", "")
            player_name = record.get("Player", "")
            team_code = record.get("Team", "")
            
            game = self._get_game_by_id(game_id)
            if not game:
                enhanced_records.append(record.to_dict())
                continue
            
            enhanced = {
                "Date": record.get("Date"),
                "Player": player_name,
                "Team": team_code,
                "Opponent": record.get("Opponent"),
                "Home/Away": self._determine_home_away(game, team_code),
                "GameID": game_id
            }
            
            # Always show complete cycle breakdown
            if any(stat in record and record[stat] > 0 for stat in ["HR", "2B", "3B"]):
                # Use preserved stats
                hits = record.get("H", 0)
                doubles = record.get("2B", 0)
                triples = record.get("3B", 0)
                home_runs = record.get("HR", 0)
                singles = hits - doubles - triples - home_runs
                
                enhanced.update({
                    "AB": record.get("AB", 0),
                    "H": hits,
                    "Singles": singles,
                    "2B": doubles,
                    "3B": triples, 
                    "HR": home_runs,
                    "R": record.get("R", 0),
                    "RBI": record.get("RBI", 0),
                    "BB": record.get("BB", 0),
                    "SO": record.get("SO", 0)
                })
            else:
                # Box score lookup
                hitting_stats = self._get_hitter_stats(game, player_name)
                hits = hitting_stats.get("H", 0)
                doubles = hitting_stats.get("2B", 0)
                triples = hitting_stats.get("3B", 0)
                home_runs = hitting_stats.get("HR", 0)
                singles = hits - doubles - triples - home_runs
                
                enhanced.update({
                    "AB": hitting_stats.get("AB", 0),
                    "H": hits,
                    "Singles": singles,
                    "2B": doubles,
                    "3B": triples,
                    "HR": home_runs,
                    "R": hitting_stats.get("R", 0),
                    "RBI": hitting_stats.get("RBI", 0),
                    "BB": hitting_stats.get("BB", 0),
                    "SO": hitting_stats.get("SO", 0)
                })
            
            enhanced_records.append(enhanced)
        
        return pd.DataFrame(enhanced_records)
    
    def enhance_ten_k_games(self, basic_data):
        """Add complete pitching line to 10+ K games, removing Detail column."""
        return self.enhance_quality_starts(basic_data)  # Same format

    def enhance_shutouts(self, basic_data):
        """Add complete pitching line to Shutouts, removing Detail column."""
        return self.enhance_quality_starts(basic_data)  # Same format

    def enhance_complete_games(self, basic_data):
        """Add complete pitching line to Complete Games, removing Detail column.""" 
        return self.enhance_quality_starts(basic_data)  # Same format

    def enhance_no_hitters(self, basic_data):
        """Add complete pitching line to No-Hitters, removing Detail column."""
        return self.enhance_quality_starts(basic_data)  # Same format
    
    def enhance_grand_slams(self, basic_data):
        """Add hitting context to Grand Slams, keeping some Detail info."""
        if basic_data is None or basic_data.empty:
            return pd.DataFrame()
        
        enhanced_records = []
        
        for _, record in basic_data.iterrows():
            game_id = record.get("GameID", "")
            player_name = record.get("Player", "")
            team_code = record.get("Team", "")
            
            # Get game for home/away context
            game = self._get_game_by_id(game_id)
            
            # Extract inning and pitcher from Detail field if available
            detail = record.get("Detail", "")
            inning_info = self._extract_inning_from_detail(detail)
            pitcher_info = self._extract_pitcher_from_detail(detail)
            
            enhanced = {
                "Date": record.get("Date"),
                "Player": player_name,
                "Team": team_code,
                "Opponent": record.get("Opponent"),
                "Home/Away": self._determine_home_away(game, team_code),
                "Inning": inning_info,
                "Pitcher": pitcher_info,
                "GameID": game_id
            }
            
            # Check if we have preserved stats from _add_milestone (using standardized keys)
            if any(stat in record and record[stat] > 0 for stat in ["HR", "2B", "3B", "H", "RBI"]):
                # Use preserved footer stats
                enhanced.update({
                    "AB": record.get("AB", 0) if record.get("AB", 0) > 0 else 0,
                    "H": record.get("H", 0) if record.get("H", 0) > 0 else 0,
                    "R": record.get("R", 0) if record.get("R", 0) > 0 else 0,
                    "RBI": record.get("RBI", 0),
                    "HR": record.get("HR", 0)
                })
            else:
                # Fallback to box score lookup
                hitting_stats = self._get_hitter_stats(game, player_name) if game else {}
                enhanced.update({
                    "AB": hitting_stats.get("AB", 0) if hitting_stats.get("AB", 0) > 0 else 0,
                    "H": hitting_stats.get("H", 0) if hitting_stats.get("H", 0) > 0 else 0,
                    "R": hitting_stats.get("R", 0) if hitting_stats.get("R", 0) > 0 else 0,
                    "RBI": hitting_stats.get("RBI", 0),
                    "HR": hitting_stats.get("HR", 0)
                })
            
            enhanced_records.append(enhanced)
        
        return pd.DataFrame(enhanced_records)
    
    # Helper methods
    def _get_game_by_id(self, game_id):
        """Find game by ID."""
        return next((g for g in self.games if g.get("game_id") == game_id), None)
    
    def _get_pitcher_stats(self, game, player_name):
        """Get complete pitching stats for a player in a game."""
        for side in ["home", "away"]:
            for pitcher in game.get("pitching", {}).get(side, []):
                if pitcher.get("name", "") == player_name:
                    return pitcher
        return {}
    
    def _get_hitter_stats(self, game, player_name):
        """Get complete hitting stats for a player in a game."""
        for side in ["home", "away"]:
            for hitter in game.get("batting", {}).get(side, []):
                if hitter.get("name", "") == player_name:
                    # Calculate singles
                    hits = hitter.get("H", 0)
                    doubles = hitter.get("2B", 0)
                    triples = hitter.get("3B", 0)
                    home_runs = hitter.get("HR", 0)
                    singles = hits - doubles - triples - home_runs
                    
                    stats = dict(hitter)
                    stats["singles"] = singles
                    return stats
        return {}
    
    def _format_ip_with_decimal(self, ip_value):
        """Format IP to always show decimal (7.0, 6.2, etc.)."""
        try:
            if isinstance(ip_value, str):
                if "." in ip_value:
                    return ip_value
                else:
                    return f"{ip_value}.0"
            elif isinstance(ip_value, (int, float)):
                whole = int(ip_value)
                fractional = ip_value - whole
                
                if abs(fractional - 0.33) < 0.05:
                    return f"{whole}.1"
                elif abs(fractional - 0.67) < 0.05:
                    return f"{whole}.2"
                elif fractional < 0.05:
                    return f"{whole}.0"
                else:
                    return f"{ip_value:.1f}"
            else:
                return str(ip_value)
        except Exception as e:
            print(f"   ⚠️ Error formatting IP '{ip_value}': {e}")
            return str(ip_value)

    def _calculate_whip(self, pitching_stats):
        """Calculate WHIP from pitching stats."""
        try:
            ip = pitching_stats.get("IP", "0")
            hits = pitching_stats.get("H", 0)
            walks = pitching_stats.get("BB", 0)
            
            if isinstance(ip, str):
                outs = StatUtils.ip_to_outs(ip)
                if outs is not None:
                    ip_decimal = outs / 3.0
                else:
                    return 0.00
            else:
                ip_decimal = float(ip)
            
            if ip_decimal > 0:
                whip = round((hits + walks) / ip_decimal, 2)
                return whip
            else:
                return 0.00
                
        except Exception as e:
            return 0.00

    def _determine_home_away(self, game, team_code):
        """Determine if team was home or away in the game."""
        if not game:
            return "Unknown"
        
        basic_info = game.get("basic_info", {})
        home_team = unify_team_code(basic_info.get("home_team_code", ""))
        away_team = unify_team_code(basic_info.get("away_team_code", ""))
        
        if team_code == home_team:
            return "Home"
        elif team_code == away_team:
            return "Away"
        else:
            return "Unknown"

    def _extract_inning_from_detail(self, detail):
        """Extract inning information from Detail field."""
        if not detail:
            return "Unknown"
        
        import re
        
        # Try "Bottom/Top N" pattern
        match = re.search(r'(bottom|top)\s+(\d+)', str(detail).lower())
        if match:
            half = match.group(1).title()
            inning = match.group(2)
            return f"{half} {inning}"
        
        # Try "Nth inning" pattern
        match = re.search(r'(\d+)(?:st|nd|rd|th)?\s+inn', str(detail).lower())
        if match:
            return f"Inning {match.group(1)}"
        
        return "Unknown"
    
    def _extract_pitcher_from_detail(self, detail):
        """Extract pitcher name from Detail field."""
        if not detail:
            return "Unknown"
        
        import re
        
        # Look for "off [Pitcher Name]" pattern, but stop at parentheses or commas
        match = re.search(r'off\s+([^,;()]+)', str(detail))
        if match:
            pitcher_name = match.group(1).strip()
            # Remove any trailing punctuation
            pitcher_name = re.sub(r'[.,;)]+$', '', pitcher_name)
            return pitcher_name
        
        return "Unknown"
    
def integrate_practical_enhancements(milestone_dfs, games):
    """Integrate practical enhancements into existing milestone DataFrames."""
    enhancer = PracticalMilestoneEnhancer(games)
    
    # Define which milestones to enhance and how
    enhancements = {
        "Quality Starts": enhancer.enhance_quality_starts,
        "Multi-HR Games": enhancer.enhance_multi_hr_games, 
        "4+ Hit Games": enhancer.enhance_four_hit_games,
        "5+ RBI Games": enhancer.enhance_five_rbi_games,
        "10+ K Games": enhancer.enhance_ten_k_games,
        "Shutouts": enhancer.enhance_shutouts,
        "Complete Games": enhancer.enhance_complete_games,
        "No-Hitters": enhancer.enhance_no_hitters,
        "Grand Slams": enhancer.enhance_grand_slams,
        "Cycles": enhancer.enhance_cycles,
    }
    
    enhanced_dfs = {}
    
    for milestone_type, df in milestone_dfs.items():
        if milestone_type in enhancements and not df.empty:
            try:
                enhanced_df = enhancements[milestone_type](df)
                enhanced_dfs[milestone_type] = enhanced_df
            except Exception as e:
                print(f"   ⚠️ Could not enhance {milestone_type}: {e}")
                enhanced_dfs[milestone_type] = df
        else:
            enhanced_dfs[milestone_type] = df
    
    return enhanced_dfs
