"""Base processor class with common functionality for all processors."""

import pandas as pd
from ..utils.helpers import ensure_sorted_gameids


class BaseProcessor:
    """Base class for game data processors."""
    
    def __init__(self, games):
        """Initialize processor with game data.
        
        Args:
            games: List of game data dictionaries
        """
        self.games = games
        self.game_count = len(games)
    
    def create_dataframe(self, rows, columns=None):
        """Create a DataFrame from rows with optional column ordering.
        
        Args:
            rows: List of dictionaries to convert to DataFrame
            columns: Optional list of columns in desired order
            
        Returns:
            pandas.DataFrame with sorted GameIDs if present
        """
        if not rows:
            return pd.DataFrame()
        
        df = pd.DataFrame(rows)
        
        # Apply column ordering if specified
        if columns:
            # Only include columns that exist in the DataFrame
            existing_cols = [col for col in columns if col in df.columns]
            # Add any columns that weren't in the specified list
            remaining_cols = [col for col in df.columns if col not in existing_cols]
            df = df[existing_cols + remaining_cols]
        
        # Sort GameIDs if present
        df = ensure_sorted_gameids(df)
        
        return df
    
    def get_basic_info(self, game):
        """Extract basic info from game data safely.
        
        Args:
            game: Game data dictionary
            
        Returns:
            dict: Basic info with common fields
        """
        return game.get("basic_info", {})
    
    def get_game_id(self, game):
        """Extract game ID safely.
        
        Args:
            game: Game data dictionary
            
        Returns:
            str: Game ID or "UNKNOWN"
        """
        return game.get("game_id", "UNKNOWN")
    
    def get_team_code(self, game, side):
        """Get team code for home or away team.
        
        Args:
            game: Game data dictionary
            side: "home" or "away"
            
        Returns:
            str: Team code
        """
        basic_info = self.get_basic_info(game)
        return basic_info.get(f"{side}_team_code", "")
    
    def get_team_name(self, game, side):
        """Get team name for home or away team.
        
        Args:
            game: Game data dictionary
            side: "home" or "away"
            
        Returns:
            str: Team name
        """
        basic_info = self.get_basic_info(game)
        return basic_info.get(f"{side}_team", "")