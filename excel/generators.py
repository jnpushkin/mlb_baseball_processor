import pandas as pd
import unicodedata
import re
from datetime import datetime



class ExcelGeneratorUtils:
    """Utility methods for Excel generation (will be moved to excel module later)."""

    @staticmethod
    def finalize_date_column(df, col='Date', in_format=None, out_format="%m/%d/%Y", sort=True):
        """Coerce df[col] to datetime, optionally with a given input format, drop invalids,
        sort by date, and format as out_format. Returns a new DataFrame (copy)."""
        import pandas as _pd
        if df is None or df.empty or col not in df.columns:
            return df
        df2 = df.copy()
        try:
            if in_format:
                df2[col] = _pd.to_datetime(df2[col], format=in_format, errors="coerce")
            else:
                df2[col] = _pd.to_datetime(df2[col], errors="coerce")
            df2 = df2.dropna(subset=[col])
            if sort:
                df2 = df2.sort_values(col).reset_index(drop=True)
            df2[col] = df2[col].dt.strftime(out_format)
            return df2
        except Exception:
            return df
    
    @staticmethod
    def unify_team_code(code: str) -> str:
        """Map old team codes to their modern equivalents."""
        team_aliases = {
            "Tampa Bay Devil Rays": "TB",
            "FLA": "MIA",
        }
        return team_aliases.get(code, code)
    
    @staticmethod
    def safe_get_int(data: dict, key: str, default: int = 0) -> int:
        """Safely extract integer from dictionary."""
        try:
            value = data.get(key, default)
            return int(value) if value is not None else default
        except (ValueError, TypeError):
            return default
    
    @staticmethod
    def safe_get_str(data: dict, key: str, default: str = "") -> str:
        """Safely extract string from dictionary."""
        value = data.get(key, default)
        return str(value) if value is not None else default
    
    @staticmethod
    def format_score_string(basic_info: dict, max_innings: int = 9) -> str:
        """Create standardized score string."""
        away_code = ExcelGeneratorUtils.unify_team_code(basic_info.get('away_team_code', 'UNK'))
        home_code = ExcelGeneratorUtils.unify_team_code(basic_info.get('home_team_code', 'UNK'))
        away_score = ExcelGeneratorUtils.safe_get_int(basic_info, 'away_score_value', 0)
        home_score = ExcelGeneratorUtils.safe_get_int(basic_info, 'home_score_value', 0)
        
        score_str = f"{away_code} {away_score} – {home_score} {home_code}"
        if max_innings != 9:
            score_str += f" ({max_innings})"
        return score_str
    
    @staticmethod
    def extract_stat_counts(blob: str):
        """Parse footer lines like 'Player Name 3 (10, off ...)' → [('Player Name', 3)]"""
        results = []
        if not blob:
            return results
        for part in blob.split(";"):
            part = unicodedata.normalize("NFKD", part.replace("\u00a0", " ")).strip() 
            if not part:
                continue
            match = re.match(r"(.+?)\s*(\d+)?\s*\(", part)
            if match:
                name = match.group(1).strip()
                count = int(match.group(2)) if match.group(2) else 1
                results.append((name, count))
        return results

