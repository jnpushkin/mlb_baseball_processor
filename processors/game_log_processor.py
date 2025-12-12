import pandas as pd
import re
from ..excel.generators import ExcelGeneratorUtils
from ..utils.helpers import join_sorted_gameids

class GameLogProcessor:
    """Handle game log creation."""
    
    @staticmethod
    def create_game_log_dataframe(games):
        """Create the game log DataFrame."""
        print("📊 Creating game log...")
        
        def to_excel_time(val):
            try:
                if isinstance(val, str) and ":" in val:
                    h, m = map(int, val.strip().split(":"))
                    return (h * 60 + m) / (24 * 60)
            except Exception:
                pass
            return None
        
        game_log_data = []
        
        for g in games:
            b = g["basic_info"]
            
            # Calculate innings
            linescore = g.get("linescore", {})
            innings_home = len(linescore.get('home', {}).get('innings', []))
            innings_away = len(linescore.get('away', {}).get('innings', []))
            max_innings = max(innings_home, innings_away)
            
            # Create score string
            away_code_raw = b.get('away_team_code', '')
            home_code_raw = b.get('home_team_code', '')

            away_code = ExcelGeneratorUtils.unify_team_code(away_code_raw)
            home_code = ExcelGeneratorUtils.unify_team_code(home_code_raw)
            away_score = ExcelGeneratorUtils.safe_get_int(b, 'away_score_value', 0)
            home_score = ExcelGeneratorUtils.safe_get_int(b, 'home_score_value', 0)
            
            score_str = f"{away_code} {away_score} - {home_score} {home_code}"
            if max_innings != 9:
                score_str += f" ({max_innings})"
            
            # Clean start time
            start_time = b.get("start_time", "")
            clean_start_time = re.sub(r'\s*\(?local.*?\)?', '', start_time, flags=re.IGNORECASE).strip()
            
            game_log_data.append({
                "Date": b.get("date_yyyymmdd", ""),
                "Start Time": clean_start_time,
                "Away Team": away_code,
                "Home Team": home_code,
                "Score": score_str,
                "Venue": b.get("venue", ""),
                "Attendance": ExcelGeneratorUtils.safe_get_int(b, "attendance_value"),
                "Game Length": b.get("duration", ""),
                "Temperature": b.get("temperature_f"),
                "Weather": b.get("weather", ""),
                "Doubleheader": b.get("doubleheader", "0"),
                "HP Umpire": g.get("umpires", {}).get("HP", ""),
                "GameID": g.get("game_id", "")
            })
        
        # Create DataFrame
        game_log = pd.DataFrame(game_log_data)
        
        # Format columns
        game_log["Date"] = pd.to_datetime(game_log["Date"], format="%Y%m%d")
        game_log["Game Length"] = game_log["Game Length"].apply(to_excel_time)
        game_log = game_log.sort_values("Date").reset_index(drop=True)
        
        if "GameID" in game_log.columns:
            game_log["GameID"] = (
                '=HYPERLINK("https://www.baseball-reference.com/boxes/' +
                game_log["GameID"].str[:3] + "/" +
                game_log["GameID"] + '.shtml", "' +
                game_log["GameID"] + '")'
            )
        print(f"   ✅ Created game log with {len(game_log)} games")
        return game_log
