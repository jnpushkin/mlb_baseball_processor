import os
import pandas as pd
from collections import defaultdict, Counter
from datetime import datetime, timedelta
from pathlib import Path
from xlsxwriter.utility import xl_col_to_name
import calendar

from .generators import ExcelGeneratorUtils
from .formatters import create_workbook_theme, format_sheet_comprehensively, format_milestone_sheet_specifically
from ..processors.game_log_processor import GameLogProcessor
from ..processors.player_stats_processor import PlayerStatsProcessor
from ..processors.milestones_processor import MilestonesProcessor
from ..processors.signature_home_runs_processor import SignatureHomeRunsProcessor
from ..processors.stadium_records_processor import StadiumRecordsProcessor, EnhancedTeamRecordsProcessor
from ..processors.summary_stats_processor import SummaryStatsProcessor
from ..processors.weather_timing_tracker import WeatherTimingTracker
from ..processors.sabermetrics_tracker import SabermetricsTracker
from ..processors.situational_hitting_tracker import SituationalHittingTracker
from ..processors.defensive_lineup_tracker import DefensiveLineupTracker
from ..utils.constants import BIOFILE_PATH, REGISTER_DIR
from ..utils.helpers import load_final_game_dates, load_id_mapping, standardize_team_code, join_sorted_gameids, ensure_sorted_gameids
from ..utils.stat_utils import StatUtils
from ..utils.log import info, warn, debug

# Constants
GAMEID_WIDTH = 15
DATE_COLUMN_WIDTH = 12
PLAYER_COLUMN_WIDTH = 20
DEFAULT_COLUMN_WIDTH = 12
SUMMARY_DETAIL_WIDTH = 60
SUMMARY_SCORE_WIDTH = 25

# Enhanced HOF Columns
ENHANCED_HOF_COLUMNS = [
    'Name', 'Year Inducted', 'Position(s)', 'Teams in Games', 'Games Seen',
    'First Game', 'Last Game', 'Span',
    'AB', 'H', 'HR', 'RBI', 'AVG',      # Hitting stats
    'IP', 'W', 'L', 'ERA', 'SO_P',      # Pitching stats
    'Milestones Achieved', 'GameIDs'
]

def safe_write_sheet(xl, df, sheet_name, formatter_func=None, **kwargs):
    """Safely write sheet with error handling."""
    try:
        if df is None or df.empty:
            print(f"   ⚠️ Skipping empty sheet: {sheet_name}")
            return False
            
        df.to_excel(xl, sheet_name=sheet_name, index=False)
        
        if formatter_func:
            formatter_func(xl, df, sheet_name, **kwargs)
            
        print(f"   ✅ Successfully wrote {sheet_name} ({len(df)} rows)")
        return True
        
    except Exception as e:
        print(f"   ❌ Error writing {sheet_name}: {e}")
        return False

def apply_column_number_formatting(worksheet, df, format_specs, workbook, colors):
    """Apply number formatting while preserving alternating row colors."""
    for col_name, (num_format, alignment) in format_specs.items():
        if col_name not in df.columns:
            continue
            
        col_idx = df.columns.get_loc(col_name)
        for row in range(1, len(df) + 1):
            try:
                cell_value = df.iloc[row-1][col_name]
                if pd.notna(cell_value):
                    is_even_row = row % 2 == 1
                    bg_color = colors['white'] if is_even_row else colors['light_gray']
                    
                    fmt = workbook.add_format({
                        "num_format": num_format,
                        "align": alignment,
                        "border": 1,
                        "bg_color": bg_color
                    })
                    
                    if col_name in ["First Visit", "Last Visit", "First Game", "Last Game"]:
                        worksheet.write_string(row, col_idx, str(cell_value), fmt)
                    else:
                        try:
                            if isinstance(cell_value, str):
                                clean_value = cell_value.strip().replace(',', '')
                                numeric_value = float(clean_value) if '.' in clean_value else int(clean_value)
                            else:
                                numeric_value = float(cell_value)
                            worksheet.write_number(row, col_idx, numeric_value, fmt)
                        except (ValueError, TypeError):
                            worksheet.write_string(row, col_idx, str(cell_value), fmt)
            except Exception as e:
                print(f"   ⚠️ Error formatting {col_name} row {row}: {e}")

def fix_single_gameid_column(worksheet, df, workbook, colors, width=GAMEID_WIDTH):
    """Apply formatting to single GameID columns (not GameIDs plural)."""
    if "GameID" not in df.columns:
        return
        
    gameid_col = df.columns.get_loc("GameID")
    worksheet.set_column(gameid_col, gameid_col, width)
    
    # Add hyperlinks with alternating colors
    for row_idx in range(len(df)):
        try:
            game_id_val = df.iloc[row_idx]["GameID"]
            
            # Handle hyperlink formulas
            if str(game_id_val).startswith('=HYPERLINK'):
                import re
                match = re.search(r'"([^"]+)"\)$', str(game_id_val))
                game_id = match.group(1) if match else str(game_id_val)
            else:
                game_id = str(game_id_val)
            
            if game_id and game_id != "UNKNOWN":
                url = f"https://www.baseball-reference.com/boxes/{game_id[:3]}/{game_id}.shtml"
                
                excel_row = row_idx + 1
                bg_color = colors['white'] if excel_row % 2 == 1 else colors['light_gray']
                hyperlink_format = workbook.add_format({
                    'font_color': 'blue',
                    'underline': True,
                    'align': 'center',
                    'border': 1,
                    'bg_color': bg_color
                })
                
                worksheet.write_url(excel_row, gameid_col, url, hyperlink_format, string=game_id)
        except Exception as e:
            print(f"   ⚠️ Error adding GameID hyperlink row {row_idx}: {e}")

def apply_advanced_stat_formatting(worksheet, df, stat_columns, workbook, colors):
    """Apply 3-decimal formatting to advanced stats (AVG, OBP, SLG, OPS)."""
    for col_name in stat_columns:
        if col_name not in df.columns:
            continue
            
        col_idx = df.columns.get_loc(col_name)
        for row in range(1, len(df) + 1):
            try:
                cell_value = df.iloc[row-1][col_name]
                if pd.notna(cell_value) and isinstance(cell_value, (int, float)):
                    is_even_row = row % 2 == 1
                    bg_color = colors['white'] if is_even_row else colors['light_gray']
                    
                    fmt = workbook.add_format({
                        "num_format": "0.000",
                        "align": "center",
                        "bg_color": bg_color,
                        "border": 1
                    })
                    
                    worksheet.write_number(row, col_idx, float(cell_value), fmt)
            except Exception as e:
                print(f"   ⚠️ Error formatting {col_name} row {row}: {e}")

def process_all_game_data(games, debut_entries, hof_df):
    """Process all game data and return structured results."""
    print(f"📊 Processing {len(games)} games for analysis...")
    
    try:
        # Core data processing
        game_log = GameLogProcessor.create_game_log_dataframe(games)
        
        # Player statistics
        player_processor = PlayerStatsProcessor(games)
        hitters, pitchers, players_without_stats_df, all_players = player_processor.process_all_player_stats()
        
        # Initialize enhanced trackers
        print("🔄 Initializing enhanced tracking systems...")
        weather_tracker = WeatherTimingTracker()
        saber_tracker = SabermetricsTracker()
        situation_tracker = SituationalHittingTracker()
        defense_tracker = DefensiveLineupTracker()
        
        # Process each game through enhanced trackers
        print("📊 Processing enhanced statistics...")
        for game in games:
            weather_tracker.process_weather(game)
            weather_tracker.process_timing(game)
            saber_tracker.process_player_sabermetrics(game)
            situation_tracker.process_game_situations(game)
            defense_tracker.process_game_defense_lineup(game)
        print("✅ Enhanced statistics processing complete!")

        # Milestones and special events
        milestone_processor = MilestonesProcessor(games)
        milestones, b2b_game_ids, b2b2b_game_ids, b2b2b2b_gameids, b2b_only_df, b2b2b_only_df, b2b2b2b_only_df, triple_play_df = milestone_processor.process_all_milestones()
        
        # DEBUG: Check 10+ K Games
        debug(f"\n10+ K GAMES DEBUG:")
        ten_k_df = milestones.get("10+ K Games", pd.DataFrame())
        debug(f"   Rows in 10+ K Games: {len(ten_k_df)}")
        if len(ten_k_df) > 0:
            debug(f"   Sample: {ten_k_df.head(1).to_dict('records')}")
        else:
            # Check if raw data exists
            sample_game = games[0] if games else {}
            milestone_stats = sample_game.get("milestone_stats", {})
            ten_k_raw = milestone_stats.get("ten_k_games", [])
            debug(f"   Raw ten_k_games in first game: {len(ten_k_raw)}")
            debug(f"   Sample game has milestone_stats: {'milestone_stats' in sample_game}")

        # Stadium and team records
        stadium_processor = StadiumRecordsProcessor(games)
        stadiums, ori_stads, basic_team_records = stadium_processor.process_stadium_and_team_records()
        
        enhanced_team_processor = EnhancedTeamRecordsProcessor(games)
        team_records = enhanced_team_processor.process_enhanced_team_records()
        
        # Signature home runs
        signature_processor = SignatureHomeRunsProcessor(games)
        df_splash = signature_processor.process_signature_home_runs()
        
        # Summary statistics
        summary_processor = SummaryStatsProcessor(
            games, all_players, b2b_only_df, b2b2b_only_df, b2b2b2b_only_df, triple_play_df, hitters, pitchers, milestones,
            weather_tracker=weather_tracker,
            saber_tracker=saber_tracker,
            situation_tracker=situation_tracker
        )
        summary_rows, df_matchups = summary_processor.process_summary_statistics()
        
        # Debut and final game detection
        mlb_debut_rows, final_game_rows = process_career_milestones(games, debut_entries, all_players)
        
        return {
            'game_log': game_log,
            'hitters': hitters,
            'pitchers': pitchers,
            'players_without_stats': players_without_stats_df,
            'all_players': all_players,
            'milestones': milestones,
            'milestone_processor': milestone_processor,
            'stadiums': stadiums,
            'ori_stads': ori_stads,
            'team_records': team_records,
            'df_splash': df_splash,
            'summary_rows': summary_rows,
            'df_matchups': df_matchups,
            'mlb_debut_rows': mlb_debut_rows,
            'final_game_rows': final_game_rows,
            'b2b_only_df': b2b_only_df,
            'b2b2b_only_df': b2b2b_only_df,
            'b2b2b2b_only_df': b2b2b2b_only_df,
            'triple_play_df': triple_play_df,
            'weather_tracker': weather_tracker,
            'saber_tracker': saber_tracker,
            'situation_tracker': situation_tracker,
            'defense_tracker': defense_tracker
        }
        
    except Exception as e:
        print(f"❌ Error processing game data: {e}")
        raise

def process_career_milestones(games, debut_entries, all_players):
    """Process MLB debuts and final games."""
    try:
        # Load reference data
        biofile_path = BIOFILE_PATH
        register_dir = REGISTER_DIR
        final_game_dates = load_final_game_dates(biofile_path)
        bbref_to_retro, retro_to_bbref = load_id_mapping(register_dir)
        
        # Process debuts
        mlb_debut_rows = []
        for game in games:
            debut_matches = check_mlb_debuts(game, debut_entries)
            mlb_debut_rows.extend(debut_matches)
        
        # Process final games
        final_game_rows = check_final_mlb_games(all_players, games, final_game_dates, bbref_to_retro)
        
        return mlb_debut_rows, final_game_rows
        
    except Exception as e:
        print(f"❌ Error processing career milestones: {e}")
        return [], []

def create_enhanced_hof_dataframe(hof_df, hitters, pitchers, all_players, milestones):
    """Create enhanced HOF DataFrame with actual positions, stats, and achievements."""
    try:
        # Build lookup of PlayerID → GameIDs from BOTH hitters and pitchers
        hitter_lookup = hitters[['Player ID', 'GameIDs']].rename(columns={'Player ID': 'PlayerID'})
        pitcher_lookup = pitchers[['Player ID', 'GameIDs']].rename(columns={'Player ID': 'PlayerID'})
        combined_lookup = pd.concat([hitter_lookup, pitcher_lookup], ignore_index=True)

        # Filter HOF list to those in our dataset
        hof_seen = hof_df[hof_df['PlayerID'].isin(combined_lookup['PlayerID'])].copy()

        enhanced_hof_rows = []
        
        for _, hof_player in hof_seen.iterrows():
            player_id = hof_player['PlayerID']
            player_name = hof_player['Name']
            
            # Get game IDs
            player_games = combined_lookup[combined_lookup['PlayerID'] == player_id]['GameIDs'].iloc[0] if not combined_lookup[combined_lookup['PlayerID'] == player_id].empty else ""
            game_count = len(player_games.split(',')) if player_games.strip() else 0
            
            # Initialize row data
            row = {
                'Name': player_name,
                'Year Inducted': hof_player.get('Year', ''),
                'Position(s)': '',
                'Teams in Games': '',
                'Games Seen': game_count,
            }
            
            # Get actual positions from player tracking data
            if player_id in all_players:
                positions = all_players[player_id].get('positions', set())
                if positions:
                    # Sort positions logically
                    position_order = ['P', 'C', '1B', '2B', 'SS', '3B', 'LF', 'CF', 'RF', 'DH', 'PH', 'PR']
                    sorted_positions = sorted(positions, key=lambda x: position_order.index(x) if x in position_order else 999)
                    row['Position(s)'] = ', '.join(sorted_positions)
                
                # Get teams they played for in your games
                teams = all_players[player_id].get('teams', set())
                if teams:
                    row['Teams in Games'] = ', '.join(sorted(teams))
            
            # Add hitting stats if available
            hitting_data = hitters[hitters['Player ID'] == player_id]
            if not hitting_data.empty:
                hit_stats = hitting_data.iloc[0]
                row.update({
                    'AB': hit_stats.get('AB', ''),
                    'H': hit_stats.get('H', ''),
                    'HR': hit_stats.get('HR', ''),
                    'RBI': hit_stats.get('RBI', ''),
                    'AVG': hit_stats.get('AVG', '')
                })
            else:
                row.update({'AB': '', 'H': '', 'HR': '', 'RBI': '', 'AVG': ''})
            
            # Add pitching stats if available
            pitching_data = pitchers[pitchers['Player ID'] == player_id]
            if not pitching_data.empty:
                pitch_stats = pitching_data.iloc[0]
                row.update({
                    'IP': pitch_stats.get('IP', ''),
                    'W': pitch_stats.get('W', ''),
                    'L': pitch_stats.get('L', ''),
                    'ERA': pitch_stats.get('ERA', ''),
                    'SO_P': pitch_stats.get('SO', '')
                })
            else:
                row.update({'IP': '', 'W': '', 'L': '', 'ERA': '', 'SO_P': ''})
            
            # Add milestone achievements
            achieved_milestones = []
            for milestone_name, milestone_df in milestones.items():
                if milestone_df.empty or 'Player' not in milestone_df.columns:
                    continue
                
                player_in_milestone = milestone_df[
                    milestone_df['Player'].str.contains(player_name, case=False, na=False, regex=False)
                ]
                
                if not player_in_milestone.empty:
                    achieved_milestones.append(milestone_name)
            
            row['Milestones Achieved'] = ', '.join(achieved_milestones) if achieved_milestones else ''
            
            # Add game span information
            if player_games.strip():
                game_list = [g.strip() for g in player_games.split(',') if g.strip()]
                if len(game_list) > 1:
                    row['First Game'] = game_list[0]
                    row['Last Game'] = game_list[-1]
                    span = calculate_game_span(game_list[0], game_list[-1])
                    row['Span'] = span
                else:
                    row['First Game'] = game_list[0] if game_list else ''
                    row['Last Game'] = row['First Game']
                    row['Span'] = 'Single game'
            else:
                row['First Game'] = ''
                row['Last Game'] = ''
                row['Span'] = ''
            
            row['GameIDs'] = player_games
            enhanced_hof_rows.append(row)
        
        # Create enhanced DataFrame
        enhanced_hof_df = pd.DataFrame(enhanced_hof_rows)
        
        # Sort by Games Seen (desc), then Year Inducted (asc)
        if not enhanced_hof_df.empty:
            enhanced_hof_df = enhanced_hof_df.sort_values(
                ['Games Seen', 'Year Inducted'], 
                ascending=[False, True]
            ).reset_index(drop=True)
        
        return enhanced_hof_df
        
    except Exception as e:
        print(f"❌ Error creating enhanced HOF DataFrame: {e}")
        return pd.DataFrame()

def calculate_game_span(first_game_id, last_game_id):
    """Calculate span between two game IDs."""
    try:
        # Extract dates from game IDs (format: TEAMYYYYMMDD#)
        first_date_str = first_game_id[3:11]
        last_date_str = last_game_id[3:11]
        
        first_date = datetime.strptime(first_date_str, "%Y%m%d")
        last_date = datetime.strptime(last_date_str, "%Y%m%d")
        
        if first_date == last_date:
            return "Same day"
        
        # Calculate years, months, days
        years = last_date.year - first_date.year
        months = last_date.month - first_date.month  
        days = last_date.day - first_date.day
        
        # Adjust for negative days/months
        if days < 0:
            months -= 1
            if last_date.month == 1:
                days += calendar.monthrange(last_date.year - 1, 12)[1]
            else:
                days += calendar.monthrange(last_date.year, last_date.month - 1)[1]
        
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
        
        return ", ".join(span_parts) if span_parts else "Same day"
        
    except Exception as e:
        return "Unknown span"

def write_main_data_sheets(xl, data, workbook, colors):
    """Write the main data sheets (Game Log, Hitters, Pitchers, etc.)."""
    try:
        # Game Log
        game_log = ensure_sorted_gameids(data['game_log'])
        if safe_write_sheet(xl, game_log, "Game Log", format_sheet_comprehensively, 
                           workbook=workbook, colors=colors, sheet_type="game_log", exclude_cols=[]):
            
            # Apply specific Game Log formatting
            ws_game_log = xl.sheets["Game Log"]
            
            # Handle Date column specially (it's datetime objects)
            if "Date" in game_log.columns:
                date_col = game_log.columns.get_loc("Date")
                ws_game_log.set_column(date_col, date_col, DATE_COLUMN_WIDTH)
                
                for row_idx in range(len(game_log)):
                    excel_row = row_idx + 1
                    date_value = game_log.iloc[row_idx]["Date"]
                    
                    is_even_row = excel_row % 2 == 1
                    bg_color = colors['white'] if is_even_row else colors['light_gray']
                    
                    date_fmt = workbook.add_format({
                        "num_format": "mm/dd/yyyy",
                        "align": "center",
                        "bg_color": bg_color,
                        "border": 1
                    })
                    
                    if hasattr(date_value, 'strftime'):
                        ws_game_log.write_datetime(excel_row, date_col, date_value, date_fmt)

            # Game Length formatting
            if "Game Length" in game_log.columns:
                time_formats = {"Game Length": ("h:mm", "center")}
                apply_column_number_formatting(ws_game_log, game_log, time_formats, workbook, colors)
            fix_single_gameid_column(ws_game_log, game_log, workbook, colors)

        # Hitters
        hitters = data['hitters'].sort_values("AB", ascending=False)
        hitters = ensure_sorted_gameids(hitters)
        if safe_write_sheet(xl, hitters, "Hitters", format_sheet_comprehensively,
                           workbook=workbook, colors=colors, sheet_type="stats", exclude_cols=[""]):
            
            ws_hit = xl.sheets["Hitters"]
            apply_advanced_stat_formatting(ws_hit, hitters, ["AVG", "OBP", "SLG", "OPS"], workbook, colors)

        # Pitchers
        pitchers = ensure_sorted_gameids(data['pitchers'])
        if safe_write_sheet(xl, pitchers, "Pitchers", format_sheet_comprehensively,
                           workbook=workbook, colors=colors, sheet_type="stats", exclude_cols=[""]):
            
            ws_pitch = xl.sheets["Pitchers"]
            pitcher_formats = {
                "ERA": ("0.00", "center"),
                "IP": ("0.0", "center"),
                "WHIP": ("0.000", "center")
            }
            apply_column_number_formatting(ws_pitch, pitchers, pitcher_formats, workbook, colors)

        # Players Without Stats
        if not data['players_without_stats'].empty:
            players_without_stats = ensure_sorted_gameids(data['players_without_stats'])
            safe_write_sheet(xl, players_without_stats, "Players without Stats", format_sheet_comprehensively,
                           workbook=workbook, colors=colors, sheet_type="default", exclude_cols=[""])

    except Exception as e:
        print(f"❌ Error writing main data sheets: {e}")

def write_career_milestone_sheets(xl, data, workbook, colors):
    """Write MLB Debuts and Final Games sheets."""
    try:
        # MLB Debuts
        if data['mlb_debut_rows']:
            df_debuts = pd.DataFrame(data['mlb_debut_rows'])
            df_debuts["Date"] = pd.to_datetime(df_debuts["Date"], format="%Y%m%d")
            df_debuts = df_debuts.sort_values("Date").reset_index(drop=True)

            # Smart column ordering
            base_cols = ["Date", "Player", "PlayerID", "Team", "Opponent", "Position"]
            batting_cols = ["AB", "H", "R", "RBI", "HR", "2B", "3B", "BB", "SO"]
            pitching_cols = ["IP", "H_P", "R_P", "ER", "BB_P", "SO_P", "Decision"]
            
            final_cols = [c for c in base_cols if c in df_debuts.columns]
            final_cols.extend([c for c in batting_cols if c in df_debuts.columns])
            final_cols.extend([c for c in pitching_cols if c in df_debuts.columns])
            if "GameID" in df_debuts.columns:
                final_cols.append("GameID")

            df_debuts = df_debuts[final_cols]
            df_debuts = ensure_sorted_gameids(df_debuts)
            
            if safe_write_sheet(xl, df_debuts, "MLB Debuts", format_sheet_comprehensively,
                               workbook=workbook, colors=colors, sheet_type="default", exclude_cols=[""]):
                
                ws_debuts = xl.sheets["MLB Debuts"]
                fix_single_gameid_column(ws_debuts, df_debuts, workbook, colors)
                
                # IP formatting if present
                if "IP" in df_debuts.columns:
                    ip_formats = {"IP": ("0.0", "center")}
                    apply_column_number_formatting(ws_debuts, df_debuts, ip_formats, workbook, colors)

        # Final MLB Games
        if data['final_game_rows']:
            df_finals = pd.DataFrame(data['final_game_rows'])
            df_finals["Date"] = pd.to_datetime(df_finals["Date"], format="%Y%m%d")
            df_finals = df_finals.sort_values("Date").reset_index(drop=True)
            df_finals["Date"] = df_finals["Date"].dt.strftime("%m/%d/%Y")

            # Same column ordering logic as debuts
            base_cols = ["Date", "Player", "PlayerID", "Team", "Position"]
            batting_cols = ["AB", "H", "R", "RBI", "HR", "2B", "3B", "BB", "SO"]
            pitching_cols = ["IP", "H_P", "R_P", "ER", "BB_P", "SO_P", "Decision"]
            
            final_cols = [c for c in base_cols if c in df_finals.columns]
            final_cols.extend([c for c in batting_cols if c in df_finals.columns])
            final_cols.extend([c for c in pitching_cols if c in df_finals.columns])
            if "GameID" in df_finals.columns:
                final_cols.append("GameID")

            df_finals = df_finals[final_cols]
            df_finals = ensure_sorted_gameids(df_finals)
            
            if safe_write_sheet(xl, df_finals, "Final MLB Games", format_sheet_comprehensively,
                               workbook=workbook, colors=colors, sheet_type="default", exclude_cols=[""]):
                
                ws_finals = xl.sheets["Final MLB Games"]
                fix_single_gameid_column(ws_finals, df_finals, workbook, colors)
                
                # IP formatting if present
                if "IP" in df_finals.columns:
                    ip_formats = {"IP": ("0.0", "center")}
                    apply_column_number_formatting(ws_finals, df_finals, ip_formats, workbook, colors)

    except Exception as e:
        print(f"❌ Error writing career milestone sheets: {e}")

def write_stadium_sheets(xl, data, workbook, colors):
    """Write stadium-related sheets."""
    try:
        # Stadiums
        stadiums = ensure_sorted_gameids(data['stadiums'])
        if safe_write_sheet(xl, stadiums, "Stadiums", format_sheet_comprehensively,
                           workbook=workbook, colors=colors, sheet_type="default", exclude_cols=[""]):
            
            ws_stadiums = xl.sheets["Stadiums"]
            stadium_formats = {
                "First Visit": ("mm/dd/yyyy", "center"),
                "Last Visit": ("mm/dd/yyyy", "center"), 
                "Avg Attendance": ("#,##0", "center"),
                "High Attendance": ("#,##0", "center"),
                "Low Attendance": ("#,##0", "center"),
                "Home Runs Seen": ("#,##0", "center"),
                "Hits Seen": ("#,##0", "center"),
                "Strikeouts Seen": ("#,##0", "center"),
                "HRs per Game": ("0.0", "center"),
                "Hits per Game": ("0.0", "center"),
                "Ks per Game": ("0.0", "center")
            }
            apply_column_number_formatting(ws_stadiums, stadiums, stadium_formats, workbook, colors)

        # Enhanced Orioles
        ori_stads = ensure_sorted_gameids(data['ori_stads'])
        if safe_write_sheet(xl, ori_stads, "Orioles", format_sheet_comprehensively,
                           workbook=workbook, colors=colors, sheet_type="default", exclude_cols=[""]):
            
            ws_ori = xl.sheets["Orioles"]
            orioles_formats = {
                "First Visit": ("mm/dd/yyyy", "center"),
                "Last Visit": ("mm/dd/yyyy", "center"),
                "Avg Attendance": ("#,##0", "center"),
                "High Attendance": ("#,##0", "center"), 
                "Low Attendance": ("#,##0", "center"),
                "Runs Scored": ("#,##0", "center"),
                "Runs Allowed": ("#,##0", "center"),
                "Home Runs Hit": ("#,##0", "center"),
                "Hits": ("#,##0", "center"),
                "Strikeouts by O's": ("#,##0", "center"),
                "Runs/Game": ("0.0", "center"),
                "Runs Allowed/Game": ("0.0", "center"),
                "HRs/Game": ("0.0", "center"),
                "Hits/Game": ("0.0", "center"),
                "Run Diff/Game": ("0.0", "center"),
                "Run Differential": ("+0;-0;0", "center")
            }
            apply_column_number_formatting(ws_ori, ori_stads, orioles_formats, workbook, colors)

        # Enhanced Team Records
        if not data['team_records'].empty:
            team_records = ensure_sorted_gameids(data['team_records'])
            if safe_write_sheet(xl, team_records, "Team Records", format_sheet_comprehensively,
                               workbook=workbook, colors=colors, sheet_type="default", exclude_cols=[""]):
                
                ws_team = xl.sheets["Team Records"]
                team_formats = {
                    "Runs/Game": ("0.00", "center"),
                    "Runs Allowed/Game": ("0.00", "center"), 
                    "Run Diff/Game": ("0.00", "center"),
                    "Games": ("0", "center"),
                    "Runs Scored": ("#,##0", "center"),
                    "Runs Allowed": ("#,##0", "center"), 
                    "Run Differential": ("0", "center"),
                    "Team Hits": ("#,##0", "center"),
                    "Team HRs": ("0", "center"),
                    "Team SBs": ("0", "center"),
                    "First Game": ("mm/dd/yyyy", "center"),
                    "Last Game": ("mm/dd/yyyy", "center")
                }
                apply_column_number_formatting(ws_team, team_records, team_formats, workbook, colors)

    except Exception as e:
        print(f"❌ Error writing stadium sheets: {e}")

def write_milestone_sheets(xl, data, workbook, colors):
    """Write all milestone sheets."""
    try:
        milestone_order = [
            "Game Log", "Walk-Offs", "Leadoff HRs", "Grand Slams", "4+ Hit Games",
            "5+ RBI Games", "Multi-HR Games", "Pinch Hit HRs", "Consecutive HR Instances", 
            "3 Pitch Innings", "3 Strikeout Innings", "Immaculate Innings",
            "10+ K Games", "Complete Games & Shutouts", "Quality Starts",
            "Cycles", "No-Hitters", "Inside-the-Park HRs"
        ]
        
        milestones = data['milestones']
        sheets_written = 0
        
        for tab in milestone_order:
            if tab in milestones:
                frame = milestones[tab]
                sheet = tab[:31]  # Excel sheet name limit
                frame = ensure_sorted_gameids(frame)
                
                if safe_write_sheet(xl, frame, sheet):
                    if not frame.empty:
                        format_milestone_sheet_specifically(xl, frame, sheet, workbook, colors, exclude_cols=[""])
                        sheets_written += 1
                    else:
                        xl.sheets[sheet].hide()
        
        print(f"   ✅ Wrote {sheets_written} milestone sheets")
        
    except Exception as e:
        print(f"❌ Error writing milestone sheets: {e}")

def write_enhanced_stats_sheets(xl, data, workbook, colors):
    """Write enhanced statistics sheets."""
    try:
        print("📊 Adding enhanced statistics tabs...")
        
        # Get trackers from data
        weather_tracker = data.get('weather_tracker')
        saber_tracker = data.get('saber_tracker')
        situation_tracker = data.get('situation_tracker')
        defense_tracker = data.get('defense_tracker')
        
        if not all([weather_tracker, saber_tracker, situation_tracker, defense_tracker]):
            print("   ⚠️ Enhanced trackers not found in data, skipping enhanced sheets")
            return
        
        # 1. Weather & Timing Summary
        weather_stats = weather_tracker.get_summary_stats()
        weather_rows = []
        for key, value in weather_stats.items():
            if isinstance(value, dict):
                for sub_key, sub_value in value.items():
                    weather_rows.append({
                        "Statistic": f"{key} - {sub_key}".replace('_', ' ').title(),
                        "Value": str(sub_value)
                    })
            else:
                weather_rows.append({
                    "Statistic": key.replace('_', ' ').title(),
                    "Value": str(value)
                })
        df_weather = pd.DataFrame(weather_rows)
        if not df_weather.empty:
            safe_write_sheet(xl, df_weather, "Weather & Timing", format_sheet_comprehensively,
                           workbook=workbook, colors=colors, sheet_type="default", exclude_cols=[])
        
        # 2. WPA Leaders
        df_wpa = saber_tracker.create_wpa_dataframe()
        if not df_wpa.empty:
            safe_write_sheet(xl, df_wpa, "WPA Leaders", format_sheet_comprehensively,
                           workbook=workbook, colors=colors, sheet_type="stats", exclude_cols=[])
            
            ws_wpa = xl.sheets["WPA Leaders"]
            wpa_int_formats = {
                "Games": ("0", "center")
            }
            apply_column_number_formatting(ws_wpa, df_wpa, wpa_int_formats, workbook, colors)
            apply_advanced_stat_formatting(ws_wpa, df_wpa, ["Total WPA", "Avg WPA", "Positive WPA", "Negative WPA", "Best Game WPA", "Worst Game WPA"], workbook, colors)
        
        # 3. RISP Performance (with debug)
        df_risp = situation_tracker.create_risp_dataframe(min_ab=5)
        debug(f"\nRISP Debug: {len(df_risp)} rows (min_ab=5)")
        risp_any = sum(1 for s in situation_tracker.player_situations.values() if s['risp_ab'] > 0)
        debug(f"   Players with ANY RISP AB: {risp_any}")
        
        if not df_risp.empty:
            safe_write_sheet(xl, df_risp, "RISP Performance", format_sheet_comprehensively,
                           workbook=workbook, colors=colors, sheet_type="stats", exclude_cols=[])
            
            ws_risp = xl.sheets["RISP Performance"]
            risp_int_formats = {
                "RISP AB": ("0", "center"),
                "RISP H": ("0", "center"),
                "RISP HR": ("0", "center"),
                "RISP RBI": ("0", "center")
            }
            apply_column_number_formatting(ws_risp, df_risp, risp_int_formats, workbook, colors)
            apply_advanced_stat_formatting(ws_risp, df_risp, ["RISP AVG"], workbook, colors)
        else:
            debug(f"   RISP Performance tab is EMPTY (no players with 5+ RISP AB)")

        # 4. 2-Out Performance
        df_two_out = situation_tracker.create_two_out_dataframe(min_ab=5)
        if not df_two_out.empty:
            safe_write_sheet(xl, df_two_out, "2-Out Performance", format_sheet_comprehensively,
                           workbook=workbook, colors=colors, sheet_type="stats", exclude_cols=[])
            
            ws_two_out = xl.sheets["2-Out Performance"]
            two_out_int_formats = {
                "2-Out AB": ("0", "center"),
                "2-Out H": ("0", "center"),
                "2-Out HR": ("0", "center")
            }
            apply_column_number_formatting(ws_two_out, df_two_out, two_out_int_formats, workbook, colors)
            apply_advanced_stat_formatting(ws_two_out, df_two_out, ["2-Out AVG"], workbook, colors)
        
        # 5. RISP + 2 Outs (with debug)
        df_risp_2out = situation_tracker.create_clutch_situations_dataframe(min_ab=3)
        debug(f"RISP+2Out Debug: {len(df_risp_2out)} rows (min_ab=3)")
        risp_2out_any = sum(1 for s in situation_tracker.player_situations.values() if s['risp_2out_ab'] > 0)
        debug(f"   Players with ANY RISP+2Out AB: {risp_2out_any}")
        
        if not df_risp_2out.empty:
            safe_write_sheet(xl, df_risp_2out, "RISP + 2 Outs", format_sheet_comprehensively,
                           workbook=workbook, colors=colors, sheet_type="stats", exclude_cols=[])
            
            ws_risp_2out = xl.sheets["RISP + 2 Outs"]
            risp_2out_int_formats = {
                "RISP+2Out AB": ("0", "center"),
                "RISP+2Out H": ("0", "center"),
                "RISP+2Out HR": ("0", "center")
            }
            apply_column_number_formatting(ws_risp_2out, df_risp_2out, risp_2out_int_formats, workbook, colors)
            apply_advanced_stat_formatting(ws_risp_2out, df_risp_2out, ["RISP+2Out AVG"], workbook, colors)
        else:
            debug(f"   RISP+2Out tab is EMPTY (no players with 3+ RISP+2Out AB)")
        
        # 6. Bases Loaded (with debug)
        df_bases_loaded = situation_tracker.create_bases_loaded_dataframe()
        debug(f"Bases Loaded Debug: {len(df_bases_loaded)} rows")
        bases_any = sum(1 for s in situation_tracker.player_situations.values() if s['bases_loaded_ab'] > 0)
        debug(f"   Players with ANY bases loaded AB: {bases_any}")
        
        if not df_bases_loaded.empty:
            safe_write_sheet(xl, df_bases_loaded, "Bases Loaded", format_sheet_comprehensively,
                           workbook=workbook, colors=colors, sheet_type="stats", exclude_cols=[])
            
            ws_bases = xl.sheets["Bases Loaded"]
            bases_int_formats = {
                "Bases Loaded AB": ("0", "center"),
                "Bases Loaded H": ("0", "center"),
                "Bases Loaded HR": ("0", "center"),
                "Grand Slams": ("0", "center")
            }
            apply_column_number_formatting(ws_bases, df_bases_loaded, bases_int_formats, workbook, colors)
            apply_advanced_stat_formatting(ws_bases, df_bases_loaded, ["Bases Loaded AVG"], workbook, colors)
        else:
            debug(f"   Bases Loaded tab is EMPTY (no bases loaded opportunities)")
        
        # 7. Late & Close
        df_late_close = situation_tracker.create_late_close_dataframe(min_ab=5)
        if not df_late_close.empty:
            safe_write_sheet(xl, df_late_close, "Late & Close", format_sheet_comprehensively,
                           workbook=workbook, colors=colors, sheet_type="stats", exclude_cols=[])
            
            ws_late = xl.sheets["Late & Close"]
            late_int_formats = {
                "Late/Close AB": ("0", "center"),
                "Late/Close H": ("0", "center"),
                "Late/Close HR": ("0", "center")
            }
            apply_column_number_formatting(ws_late, df_late_close, late_int_formats, workbook, colors)
            apply_advanced_stat_formatting(ws_late, df_late_close, ["Late/Close AVG"], workbook, colors)
        
        # 9. Defensive Leaders
        df_defense = defense_tracker.create_defensive_leaders_dataframe(min_games=1)
        if not df_defense.empty:
            safe_write_sheet(xl, df_defense, "Defensive Leaders", format_sheet_comprehensively,
                           workbook=workbook, colors=colors, sheet_type="stats", exclude_cols=[])
            
            ws_defense = xl.sheets["Defensive Leaders"]
            defense_int_formats = {
                "Games": ("0", "center"),
                "PO": ("0", "center"),
                "A": ("0", "center"),
                "E": ("0", "center"),
                "TC": ("0", "center")
            }
            apply_column_number_formatting(ws_defense, df_defense, defense_int_formats, workbook, colors)
            apply_advanced_stat_formatting(ws_defense, df_defense, ["Fielding %"], workbook, colors)
        
        # 10. Lineup Analysis
        df_lineup = defense_tracker.create_lineup_analysis_dataframe(min_games=1)
        if not df_lineup.empty:
            safe_write_sheet(xl, df_lineup, "Lineup Analysis", format_sheet_comprehensively,
                           workbook=workbook, colors=colors, sheet_type="stats", exclude_cols=[])
            
            ws_lineup = xl.sheets["Lineup Analysis"]
            lineup_int_formats = {
                "Games": ("0", "center"),
                "Most Common Spot": ("0", "center"),
                "Times in Spot": ("0", "center"),
                "Pinch Hits": ("0", "center"),
                "Lineup Versatility": ("0", "center")
            }
            apply_column_number_formatting(ws_lineup, df_lineup, lineup_int_formats, workbook, colors)
        
        # 11. Lineup Position Matrix
        df_lineup_matrix = defense_tracker.create_lineup_position_matrix()
        if not df_lineup_matrix.empty:
            df_lineup_matrix.to_excel(xl, sheet_name="Lineup Matrix")
            ws_lineup_matrix = xl.sheets["Lineup Matrix"]
            
            # Apply conditional formatting to show lineup patterns
            if len(df_lineup_matrix) > 0:
                cell_range = f"B2:{xl_col_to_name(len(df_lineup_matrix.columns))}{len(df_lineup_matrix) + 1}"
                ws_lineup_matrix.conditional_format(cell_range, {
                    "type": "2_color_scale",
                    "min_type": "num",
                    "min_value": 1,
                    "min_color": "#C6EFCE",
                    "max_type": "max",
                    "max_color": "#66BB6A"
                })
        
        print("✅ Enhanced statistics tabs added!")
        
    except Exception as e:
        print(f"❌ Error writing enhanced stats sheets: {e}")

def write_analysis_sheets(xl, data, games, workbook, colors, umpire_tracker):
    """Write analysis sheets (Matchup Matrix, Scorigami, Calendar, Summary)."""
    try:
        # Signature HRs
        if not data['df_splash'].empty:
            df_splash = ensure_sorted_gameids(data['df_splash'])
            safe_write_sheet(xl, df_splash, "Signature Home Runs", format_sheet_comprehensively,
                           workbook=workbook, colors=colors, sheet_type="default", exclude_cols=[""])

        # Umpires
        write_umpires_sheet(xl, workbook, colors, umpire_tracker)
        
        # Matchup Matrix
        write_matchup_matrix(xl, data['df_matchups'], workbook, colors)
        
        # Scorigami Chart
        write_scorigami_chart(xl, games, workbook)
        
        # Calendar Grid
        write_calendar_grid(xl, data['game_log'], workbook)
        
        # Summary Stats
        write_summary_stats_sheet(xl, data['summary_rows'], workbook, colors)
        
    except Exception as e:
        print(f"❌ Error writing analysis sheets: {e}")

def write_umpires_sheet(xl, workbook, colors, umpire_tracker):
    """Write the Umpires sheet."""
    try:
        positions = ["HP", "1B", "2B", "3B", "LF", "RF"]
        umpire_rows = []

        for umpire, counts in umpire_tracker.get_counter().items():
            row = {"Umpire": umpire}
            total = 0
            all_game_ids = set()

            for pos in positions:
                pos_data = counts.get(pos, {})
                count = pos_data.get("count", 0)
                game_ids = pos_data.get("game_ids", set())
                row[pos] = count
                total += count
                all_game_ids.update(game_ids)

            if total == 0:
                continue

            row["Total"] = total
            row["GameIDs"] = join_sorted_gameids(sorted(all_game_ids))
            umpire_rows.append(row)

        if umpire_rows:
            df_umpires = pd.DataFrame(umpire_rows).sort_values(by=["Total", "Umpire"], ascending=[False, True])
            df_umpires = ensure_sorted_gameids(df_umpires)
            safe_write_sheet(xl, df_umpires, "Umpires", format_sheet_comprehensively,
                           workbook=workbook, colors=colors, sheet_type="default", exclude_cols=[""])
        else:
            print("   ⚠️ No umpire data available")
            
    except Exception as e:
        print(f"❌ Error writing umpires sheet: {e}")

def write_matchup_matrix(xl, df_matchups, workbook, colors):
    """Write the Matchup Matrix sheet."""
    try:
        df_matchups = ensure_sorted_gameids(df_matchups)
        df_matchups.to_excel(xl, sheet_name="Matchup Matrix")
        ws_matchups = xl.sheets["Matchup Matrix"]

        rows, cols = df_matchups.shape
        cell_range = f"B2:{xl_col_to_name(cols)}{rows + 1}"

        # Conditional formatting for seen matchups
        ws_matchups.conditional_format(cell_range, {
            "type": "2_color_scale",
            "min_type": "num",
            "min_value": 1,
            "min_color": "#C6EFCE",
            "max_type": "max",
            "max_color": "#66BB6A"
        })
        
        # Format diagonal cells
        gray_format = workbook.add_format({
            "bg_color": "#D9D9D9",
            "align": "center",
            "valign": "vcenter",
        })

        for i in range(rows):
            ws_matchups.write(i + 1, i + 1, "X", gray_format)

        # Add percent coverage row
        percent_row = rows + 1
        percent_fmt = workbook.add_format({
            "num_format": '[>=1]0%;[>=0.1]0.0%;0.00%',
            "bold": True,
            "align": "center",
            "valign": "vcenter"
        })

        for col_idx, team in enumerate(df_matchups.columns, start=1):
            col_letter = xl_col_to_name(col_idx)
            formula = f'=COUNTIF({col_letter}2:{col_letter}{rows + 1}, ">0") / {rows}'
            ws_matchups.write_formula(percent_row, col_idx, formula, percent_fmt)

        ws_matchups.write(percent_row, 0, "Percent Seen", percent_fmt)
        ws_matchups.freeze_panes(1, 1)
        
    except Exception as e:
        print(f"❌ Error writing matchup matrix: {e}")

def write_summary_stats_sheet(xl, summary_rows, workbook, colors):
    """Write the Summary Stats sheet with section headers."""
    try:
        # Updated section breaks to match improved organization
        section_breaks = {
            "🟩 Game Format and Rarity": "1-0 Games",
            "🟠 Individual Hitting Milestones": "4+ Hit Games", 
            "🟤 Individual Pitching Milestones": "10+ K Games",
            "🟣 Home Run Streaks": "Back-to-Back HR Events",
            "🔵 Single-Team Offensive Records": "Most Runs by One Team",
            "🔴 Single-Team Pitching Records": "Most Pitching Strikeouts by One Team",
            "🧢 Individual Game Leaders": "Most RBIs in a Game",
            "⚫️ Combined Game Totals": "Most Combined Runs",
            "⚪️ Dataset Cumulative Totals": "Total Hits Across All Games",
            "📊 Statistical Leaders": "Hits Leaders",
            "🟡 Player Tracking and Coverage": "Most Teams Seen for a Player",
            "🟪 Game Environment": "Average Attendance",
        }
        
        # Create expanded summary with section headers
        expanded_summary_rows = create_summary_with_sections(summary_rows, section_breaks)
        
        # Create DataFrame for Excel
        df_summary = pd.DataFrame(expanded_summary_rows)
        df_summary_for_excel = df_summary.drop(columns=["_is_section_header"], errors='ignore')
        df_summary_for_excel = ensure_sorted_gameids(df_summary_for_excel)
        
        if safe_write_sheet(xl, df_summary_for_excel, "Summary Stats", format_sheet_comprehensively,
                           workbook=workbook, colors=colors, sheet_type="summary", exclude_cols=[""]):
            
            # Apply Summary Stats specific formatting
            ws_summary = xl.sheets["Summary Stats"]
            apply_summary_stats_formatting(ws_summary, df_summary_for_excel, expanded_summary_rows, workbook, colors)
        
    except Exception as e:
        print(f"❌ Error writing summary stats: {e}")


def create_summary_with_sections(summary_rows, section_breaks):
    """Create summary rows with section headers inserted."""
    
    # Organization that matches write_summary_stats_sheet exactly
    summary_order = [
        # 🟩 Game Format and Rarity - Basic game characteristics
        "1-0 Games", "1-Run Games", "Extra Inning Games", "Both Teams 10+ Runs",
        "Biggest Victory", "Biggest Comeback", "Longest Game by Innings", 
        "Longest Game by Time", "Shortest Game by Time",
        
        # 🟠 Individual Hitting Milestones - Individual player achievements
        "4+ Hit Games", "5+ RBI Games", "Multi-HR Games", "Cycles",
        "Inside-the-Park Home Runs",
        
        # 🟤 Individual Pitching Milestones - Individual pitcher achievements
        "10+ K Games", "Complete Games", "Shutouts", "Quality Starts", "No-Hitters",
        
        # 🟣 Home Run Streaks - Consecutive HR sequences
        "Back-to-Back HR Events", "Back-to-Back-to-Back HR Events", 
        "Back-to-Back-to-Back-to-Back HR Events",
        
        # 🔵 Single-Team Offensive Records - One team's hitting/scoring
        "Most Runs by One Team", "Most Hits by One Team", "Most HRs by One Team",
        "20+ Hit Games by One Team", "Most Runs in a Single Inning", "10+ Run Innings",
        "Most SBs by One Team", "Fewest Hits by One Team",
        
        # 🔴 Single-Team Pitching Records - One team's pitching
        "Most Pitching Strikeouts by One Team", "Most Walks by One Team", 
        "Most Pitchers Used", "Fewest Pitchers Used",
        
        # 🧢 Individual Game Leaders - Single-game individual records
        "Most RBIs in a Game", "Most SBs by One Player", "Most Pitches by One Pitcher",
        
        # ⚫️ Combined Game Totals - Both teams combined in single games
        "Most Combined Runs", "Most Combined Hits", "Most Combined HRs",
        "Most Combined Pitching Strikeouts", "Most Combined SBs in a Game", 
        "Most Combined Walks", "Fewest Combined Strikeouts", "Fewest Combined Hits", "Fewest Combined Walks",
        
        # ⚪️ Dataset Cumulative Totals - Overall totals across all games
        "Total Hits Across All Games", "Total Home Runs Across All Games",
        "Total Runs Across All Games", "Total Strikeouts Across All Games", 
        "Total Stolen Bases Across All Games",
        
        # 📊 Statistical Leaders - Top performers in major statistical categories
        "Hits Leaders", "Runs Leaders", "Home Run Leaders", "RBI Leaders",
        "Doubles Leaders", "Triples Leaders", "Stolen Base Leaders", "Walks Leaders (Hitting)",
        "Batting Average Leaders (min. 10 AB)", "On-Base Percentage Leaders (min. 10 AB)", 
        "OPS Leaders (min. 10 AB)", "Wins Leaders", "Strikeout Leaders (Pitching)", 
        "Save Leaders", "Innings Pitched Leaders", "ERA Leaders (min. 10 IP)",

        # 🟡 Player Tracking and Coverage - Unique counts and matchup coverage
        "Most Teams Seen for a Player", "Unique Players with a Hit",
        "Unique Players with a Home Run", "Unique Pitchers with a Win", 
        "Unique Pitchers with a Loss", "Unique Pitchers with a Save",
        "Percent of Possible Matchups Seen",
        
        # 🟪 Game Environment - Attendance and weather conditions
        "Average Attendance", "Highest Attendance", "Lowest Attendance", "Average Temperature",
        "Coldest Game", "Hottest Game"
    ]
    
    record_rank = {record: i for i, record in enumerate(summary_order)}
    
    summary_rows_sorted = sorted(
        summary_rows,
        key=lambda row: record_rank.get(row["Record"], len(summary_order))
    )

    # Insert section headers using the provided section_breaks parameter
    expanded_summary_rows = []
    added_headers = set()

    for row in summary_rows_sorted:
        record = row["Record"]
        
        # Insert section header before first record of that section
        for section_name, first_record in section_breaks.items():
            if record == first_record and section_name not in added_headers:
                expanded_summary_rows.append({
                    "Record": section_name,
                    "Value": "",
                    "Detail": "",
                    "Score": "",
                    "GameIDs": "",
                    "_is_section_header": True
                })
                added_headers.add(section_name)
        
        row["_is_section_header"] = False
        expanded_summary_rows.append(row)
    
    return expanded_summary_rows

def apply_summary_stats_formatting(ws_summary, df_summary_for_excel, expanded_summary_rows, workbook, colors):
    """Apply specific formatting with wrapping enabled but selective row heights."""
    try:
        # Column widths
        summary_column_widths = {
            "Record": 35,
            "Value": 18,
            "Detail": 100,
            "Score": 65,
        }
        
        # FIXED: Only set column widths, don't apply formatting to entire columns
        for col_idx, col_name in enumerate(df_summary_for_excel.columns):
            if col_name in summary_column_widths:
                width = summary_column_widths[col_name]
                ws_summary.set_column(col_idx, col_idx, width)

        # GameID header formatting
        if "GameIDs" in df_summary_for_excel.columns:
            gameid_col = df_summary_for_excel.columns.get_loc("GameIDs")
            header_format = workbook.add_format({
                'bold': True,
                'align': 'left',
                'valign': 'bottom',
                'bg_color': colors['primary_blue'],
                'font_color': 'white',  
                'border': 1,
            })
            ws_summary.write(0, gameid_col, "GameIDs", header_format)


        # Create formats
        wrap_format = workbook.add_format({
            'text_wrap': True,
            'valign': 'top',
            'align': 'left',
            'border': 1,
        })
        
        regular_format = workbook.add_format({
            'valign': 'vcenter',
            'align': 'center',
            'border': 1,
        })

        gameid_format = workbook.add_format({
            'valign': 'vcenter',
            'align': 'left', 
            'border': 1,
        })

        # FIXED: Apply formatting cell-by-cell, only to non-empty cells
        for row_idx in range(1, len(df_summary_for_excel) + 1):
            df_row_idx = row_idx - 1
            
            if df_row_idx < len(expanded_summary_rows):
                is_section_header = expanded_summary_rows[df_row_idx].get("_is_section_header", False)
                
                if is_section_header:
                    ws_summary.set_row(row_idx, 18)
                    
                    # Section header formatting
                    header_format_left = workbook.add_format({
                        "bold": True,
                        "bg_color": "#D9E1F2",
                        "align": "left",
                        "valign": "bottom",
                        "border": 1,
                    })
                    
                    section_text = expanded_summary_rows[df_row_idx]["Record"]
                    ws_summary.write(row_idx, 0, section_text, header_format_left)
                    for col_idx in range(1, len(df_summary_for_excel.columns)):
                        ws_summary.write(row_idx, col_idx, "", header_format_left)
                        
                else:
                    # Data row
                    if df_row_idx < len(df_summary_for_excel):
                        row_data = df_summary_for_excel.iloc[df_row_idx]
                        record_name = str(row_data.get("Record", ""))
                        detail_text = str(row_data.get("Detail", ""))
                        
                        # Check if row needs tall height
                        needs_tall_row = (
                            record_name in ["Most Pitchers Used", "Fewest Pitchers Used"] or
                            (len(detail_text) > 120 and detail_text.count(';') >= 2 and ':' in detail_text)
                        )
                        
                        if needs_tall_row:
                            ws_summary.set_row(row_idx, 30)
                        
                        # FIXED: Apply formatting only to cells with content
                        for col_idx, col_name in enumerate(df_summary_for_excel.columns):
                            cell_value = row_data[col_name]
                            
                            # Only format if cell has actual content
                            if pd.notna(cell_value) and str(cell_value).strip() != "":
                                cell_str = str(cell_value)
                                
                                if col_name in ["Detail", "Score"]:
                                    ws_summary.write(row_idx, col_idx, cell_str, wrap_format)
                                elif col_name == "GameIDs":
                                    ws_summary.write(row_idx, col_idx, cell_str, gameid_format)
                                else:
                                    ws_summary.write(row_idx, col_idx, cell_str, regular_format)
                            # FIXED: Empty cells get no formatting (no write operation = no border)

    except Exception as e:
        print(f"Error applying summary stats formatting: {e}")

def write_scorigami_chart(xl, games, workbook):
    """Write the Personal Scorigami chart."""
    try:
        # Count score combinations
        score_counts = Counter()
        for g in games:
            away = g["basic_info"].get("away_score_value", 0)
            home = g["basic_info"].get("home_score_value", 0)
            if away == home:
                continue  # skip ties
            winner = max(away, home)
            loser = min(away, home)
            score_counts[(loser, winner)] += 1

        # Build grid
        max_score = max(max(k) for k in score_counts) if score_counts else 20
        losers = list(range(max_score + 1))
        winners = list(range(max_score + 1))

        # Create worksheet
        scorigami_sheet = "Personal Scorigami"
        ws_scorigami = xl.book.add_worksheet(scorigami_sheet)
        xl.sheets[scorigami_sheet] = ws_scorigami

        # Formatting
        header_fmt = workbook.add_format({
            "bold": True,
            "align": "center",
            "valign": "vcenter",
            "bg_color": "#D9E1F2"
        })
        
        gray_fmt = workbook.add_format({
            "bg_color": "#D9D9D9",
            "align": "center",
            "valign": "vcenter"
        })

        # Write headers and data
        for j, w in enumerate(winners):
            ws_scorigami.write(0, j + 1, w, header_fmt)

        for i, l in enumerate(losers):
            ws_scorigami.write(i + 1, 0, l, header_fmt)
            for j, w in enumerate(winners):
                if l >= w:
                    ws_scorigami.write(i + 1, j + 1, "", gray_fmt)
                else:
                    val = score_counts.get((l, w), "")
                    ws_scorigami.write(i + 1, j + 1, val)

        ws_scorigami.write(0, 0, "L\\W", header_fmt)

        # Conditional formatting
        cell_range = f"B2:{xl_col_to_name(len(winners))}{len(losers)+1}"
        ws_scorigami.conditional_format(cell_range, {
            "type": "2_color_scale",
            "min_type": "num",
            "min_value": 1,
            "min_color": "#C6EFCE",
            "max_type": "max",
            "max_color": "#66BB6A"
        })

        # Set column widths and freeze
        for col in range(len(winners) + 1):
            ws_scorigami.set_column(col, col, 6)
        ws_scorigami.freeze_panes(1, 1)
        
    except Exception as e:
        print(f"❌ Error writing scorigami chart: {e}")

def write_calendar_grid(xl, game_log, workbook):
    """Write the Calendar Grid sheet."""
    try:
        if game_log.empty:
            return
            
        game_log["Month-Day"] = game_log["Date"].dt.strftime("%m-%d")

        # Build valid date range
        valid_mmdd = set()
        REFERENCE_YEAR = 2024
        start_date = datetime(REFERENCE_YEAR, 3, 25)
        end_date = datetime(REFERENCE_YEAR, 11, 1)
        curr = start_date
        while curr <= end_date:
            valid_mmdd.add(curr.strftime("%m-%d"))
            curr += timedelta(days=1)

        # Count games per date
        md_counts = game_log[game_log["Month-Day"].isin(valid_mmdd)]["Month-Day"].value_counts().to_dict()

        # Build calendar grid
        months = ["Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov"]
        month_nums = {"Mar": "03", "Apr": "04", "May": "05", "Jun": "06",
                     "Jul": "07", "Aug": "08", "Sep": "09", "Oct": "10", "Nov": "11"}

        calendar_rows = []
        for day in range(1, 32):
            row = {"Day": day}
            for month in months:
                mmdd = f"{month_nums[month]}-{day:02d}"
                if mmdd in valid_mmdd:
                    row[month] = md_counts.get(mmdd, "")
                else:
                    row[month] = "X"
            calendar_rows.append(row)

        df_calendar = pd.DataFrame(calendar_rows)
        
        if safe_write_sheet(xl, df_calendar, "Calendar Grid"):
            ws_cal = xl.sheets["Calendar Grid"]
            
            # Format invalid dates
            gray_fmt = workbook.add_format({
                "bg_color": "#D9D9D9",
                "align": "center",
                "valign": "vcenter"
            })

            for i in range(len(df_calendar)):
                for j in range(1, len(df_calendar.columns)):
                    val = df_calendar.iat[i, j]
                    if val == "X":
                        ws_cal.write(i + 1, j, val, gray_fmt)

            # Add conditional formatting
            heatmap_range = f"B2:{xl_col_to_name(len(df_calendar.columns) - 1)}{len(df_calendar) + 1}"
            ws_cal.conditional_format(heatmap_range, {
                "type": "2_color_scale",
                "min_type": "num",
                "min_value": 1,
                "min_color": "#C6EFCE",
                "max_type": "max",
                "max_color": "#66BB6A"
            })

            ws_cal.freeze_panes(1, 1)
            
    except Exception as e:
        print(f"❌ Error writing calendar grid: {e}")

# Legacy functions (kept for now to avoid breaking existing functionality)
def check_mlb_debuts(game, debut_entries):
    """Fixed debut detection - captures defensive-only players."""
    debut_matches = []
    seen_ids = set()

    date_str = game.get("basic_info", {}).get("date_yyyymmdd")
    game_id = game.get("game_id", "")
    home_team = game.get("basic_info", {}).get("home_team", "")
    away_team = game.get("basic_info", {}).get("away_team", "")
    try:
        game_date = datetime.strptime(date_str, "%Y%m%d").date()
    except Exception:
        return []

    for entry in debut_entries:
        try:
            debut_date = datetime.strptime(entry["DebutDate"], "%Y-%m-%d").date()
        except Exception:
            continue

        if debut_date != game_date:
            continue

        pid = entry["PlayerID"]
        if pid in seen_ids:
            continue

        # Find player's actual role and team
        player_team = None
        opponent_team = None
        player_position = None
        batting_stats = {}
        pitching_stats = {}

        # Method 1: Check batting lineup
        for side in ("home", "away"):
            for player in game.get("batting", {}).get(side, []):
                if player.get("player_id") == pid:
                    player_team = home_team if side == "home" else away_team
                    opponent_team = away_team if side == "home" else home_team
                    player_position = player.get("position", "").strip()
                    
                    ab = player.get("AB", 0)
                    pa = player.get("PA", 0)
                    
                    if ab > 0 or pa > 0:
                        batting_stats = {
                            "AB": ab, "H": player.get("H", 0), "R": player.get("R", 0),
                            "RBI": player.get("RBI", 0), "HR": player.get("HR", 0),
                            "2B": player.get("2B", 0), "3B": player.get("3B", 0),
                            "BB": player.get("BB", 0), "SO": player.get("SO", 0)
                        }
                    break
            if player_team:
                break

        # Method 2: Check pitching
        for side in ("home", "away"):
            for player in game.get("pitching", {}).get(side, []):
                if player.get("player_id") == pid:
                    ip = player.get("IP", "0")
                    
                    try:
                        ip_outs = StatUtils.ip_to_outs(ip)
                        if ip_outs and ip_outs > 0:
                            if not player_team:
                                player_team = home_team if side == "home" else away_team
                                opponent_team = away_team if side == "home" else home_team
                            
                            if not player_position:
                                player_position = "P"
                            elif player_position != "P":
                                player_position = f"{player_position}/P"
                            
                            pitching_stats = {
                                "IP": f"{float(ip):.1f}",
                                "H_P": player.get("H", 0), "R_P": player.get("R", 0),
                                "ER": player.get("ER", 0), "BB_P": player.get("BB", 0),
                                "SO_P": player.get("SO", 0), "Decision": player.get("decision", "")
                            }
                            break
                    except:
                        continue

        # Create debut match if found
        if player_team:
            debut_match = {
                "Date": date_str,
                "Player": entry["Player"],
                "PlayerID": pid,
                "Team": standardize_team_code(player_team),
                "Opponent": standardize_team_code(opponent_team) if opponent_team != "Unknown" else opponent_team,
                "Position": player_position or "UNK",
                "GameID": game_id
            }
            
            if batting_stats:
                debut_match.update(batting_stats)
            if pitching_stats:
                debut_match.update(pitching_stats)
            if not batting_stats and not pitching_stats:
                debut_match["Notes"] = "Defensive role only"
            
            debut_matches.append(debut_match)
            seen_ids.add(pid)
            
    return debut_matches

def check_final_mlb_games(all_players, games, final_game_dates, bbref_to_retro):
    """Fixed final game detection with proper position identification."""
    final_game_rows = []
    
    for player_id, info in all_players.items():
        retro_id = bbref_to_retro.get(player_id)
        final_date = final_game_dates.get(retro_id)
        
        if not final_date:
            continue

        for game in games:
            game_date_str = game["basic_info"].get("date_yyyymmdd")
            try:
                game_date = datetime.strptime(game_date_str, "%Y%m%d")
            except Exception:
                continue

            if game["game_id"] in info["game_ids"] and game_date.date() == final_date.date():
                home_team = game["basic_info"].get("home_team", "")
                away_team = game["basic_info"].get("away_team", "")
                
                # Find player's actual position and stats
                player_team = None
                opponent_team = None
                player_position = None
                batting_stats = {}
                pitching_stats = {}
                
                # Check batting section
                for side in ("home", "away"):
                    for player in game.get("batting", {}).get(side, []):
                        if player.get("player_id") == player_id:
                            player_team = home_team if side == "home" else away_team
                            opponent_team = away_team if side == "home" else home_team
                            position_from_batting = player.get("position", "").strip()
                            if position_from_batting:
                                player_position = position_from_batting
                            
                            ab = player.get("AB", 0)
                            pa = player.get("PA", 0)
                            if ab > 0 or pa > 0:
                                batting_stats = {
                                    "AB": ab, "H": player.get("H", 0), "R": player.get("R", 0),
                                    "RBI": player.get("RBI", 0), "HR": player.get("HR", 0),
                                    "2B": player.get("2B", 0), "3B": player.get("3B", 0),
                                    "BB": player.get("BB", 0), "SO": player.get("SO", 0)
                                }
                            break

                # Check pitching section
                for side in ("home", "away"):
                    for player in game.get("pitching", {}).get(side, []):
                        if player.get("player_id") == player_id:
                            ip = player.get("IP", "0")
                            
                            try:
                                ip_outs = StatUtils.ip_to_outs(ip)
                                if ip_outs and ip_outs > 0:
                                    if not player_team:
                                        player_team = home_team if side == "home" else away_team
                                        opponent_team = away_team if side == "home" else home_team
                                    
                                    if not player_position:
                                        player_position = "P"
                                    elif player_position and player_position != "P":
                                        player_position = f"{player_position}/P"
                                    
                                    pitching_stats = {
                                        "IP": f"{float(ip):.1f}",
                                        "H_P": player.get("H", 0), "R_P": player.get("R", 0),
                                        "ER": player.get("ER", 0), "BB_P": player.get("BB", 0),
                                        "SO_P": player.get("SO", 0), "Decision": player.get("decision", "")
                                    }
                                    break
                            except:
                                continue

                if player_team:
                    final_match = {
                        "Date": game_date_str,
                        "Player": info["name"],
                        "PlayerID": player_id,
                        "Team": standardize_team_code(player_team),
                        "Position": player_position or "UNK",
                        "GameID": game["game_id"]
                    }
                    
                    if batting_stats:
                        final_match.update(batting_stats)
                    if pitching_stats:
                        final_match.update(pitching_stats)
                    if not batting_stats and not pitching_stats and player_position:
                        final_match["Notes"] = "Defensive role only"
                    
                    final_game_rows.append(final_match)
                break
    
    return final_game_rows

def generate_excel_workbook(games, output_file, debut_entries, hof_df, umpire_tracker, write_file=True):
    """
    Generate Excel workbook from parsed games data.
    
    Args:
        games: List of game data dictionaries
        output_file: Path to output Excel file (can be None if write_file=False)
        debut_entries: MLB debut reference data
        hof_df: Hall of Fame DataFrame
        umpire_tracker: UmpireTracker instance for recording umpire data
        write_file: If False, processes data but skips Excel file creation (default: True)
    
    Returns:
        dict: Processed data dictionary containing all DataFrames
    """
    print(f"🗂️ Processing {len(games)} games for analysis...")

    try:
        # Step 1: Process all game data (always do this)
        data = process_all_game_data(games, debut_entries, hof_df)
        
        # Step 2: Create Excel file (conditional)
        if write_file:
            if not output_file:
                raise ValueError("output_file must be provided when write_file=True")
            
            print(f"📊 Creating Excel workbook: {output_file}")
            create_excel_file(data, output_file, hof_df, games, umpire_tracker)
            print(f"✅ Excel workbook created successfully: {output_file}")
        else:
            print(f"⏭️  Skipping Excel file creation (write_file=False)")
        
        # Step 3: Show comprehensive milestone summary at the very end
        if 'milestone_processor' in data and 'milestones' in data:
            data['milestone_processor'].print_comprehensive_summary(data['milestones'])
        
        return data
        
    except Exception as e:
        print(f"❌ Failed to process game data: {e}")
        raise
    
def create_excel_file(data, output_file, hof_df, games, umpire_tracker):
    """Create the Excel file with all sheets."""
    with pd.ExcelWriter(output_file, engine="xlsxwriter", datetime_format="mm/dd/yyyy") as xl:
        workbook = xl.book
        formats, colors = create_workbook_theme(workbook)

        print("📝 Writing Excel sheets...")
        
        # Write main data sheets
        write_main_data_sheets(xl, data, workbook, colors)
        
        # Write career milestone sheets
        write_career_milestone_sheets(xl, data, workbook, colors)
        
        # Write enhanced HOF sheet
        write_enhanced_hof_sheet(xl, hof_df, data, workbook, colors)
        
        # Write stadium sheets
        write_stadium_sheets(xl, data, workbook, colors)
        
        # Write milestone sheets
        write_milestone_sheets(xl, data, workbook, colors)
        
        # Write enhanced statistics sheets
        write_enhanced_stats_sheets(xl, data, workbook, colors)

        # Write analysis sheets
        write_analysis_sheets(xl, data, games, workbook, colors, umpire_tracker)

def write_enhanced_hof_sheet(xl, hof_df, data, workbook, colors):
    """Write the enhanced Hall of Fame sheet."""
    try:
        enhanced_hof_df = create_enhanced_hof_dataframe(
            hof_df, data['hitters'], data['pitchers'], data['all_players'], data['milestones']
        )

        if not enhanced_hof_df.empty:
            # Reorder columns
            final_columns = [col for col in ENHANCED_HOF_COLUMNS if col in enhanced_hof_df.columns]
            enhanced_hof_df = enhanced_hof_df[final_columns]
            
            enhanced_hof_df = ensure_sorted_gameids(enhanced_hof_df)
            safe_write_sheet(xl, enhanced_hof_df, "HOFers Seen", format_sheet_comprehensively,
                           workbook=workbook, colors=colors, sheet_type="default", exclude_cols=[''])
        else:
            print("   ⚠️ No Hall of Famers found in dataset")
            
    except Exception as e:
        print(f"❌ Error writing enhanced HOF sheet: {e}")