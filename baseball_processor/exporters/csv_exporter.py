"""CSV export functionality for MLB Game Tracker.

This module provides functions to export processed game data to CSV format,
which is useful for importing into spreadsheet applications or data analysis tools.
"""

from __future__ import annotations

import csv
from pathlib import Path
from typing import Dict, Any, List, Optional, Union
import pandas as pd

from ..utils.log import info, warn


def export_to_csv(
    df: pd.DataFrame,
    output_path: Union[str, Path],
    include_index: bool = False
) -> Path:
    """Export a DataFrame to CSV.

    Args:
        df: DataFrame to export.
        output_path: Path for the output CSV file.
        include_index: Whether to include the DataFrame index.

    Returns:
        Path to the created CSV file.
    """
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    df.to_csv(output_path, index=include_index, encoding='utf-8-sig')
    info(f"Exported {len(df)} rows to {output_path}")

    return output_path


def export_all_to_csv(
    processed_data: Dict[str, Any],
    output_dir: Union[str, Path],
    prefix: str = "mlb_tracker"
) -> Dict[str, Path]:
    """Export all processed data to CSV files.

    Args:
        processed_data: Dictionary containing processed DataFrames and data.
        output_dir: Directory for output CSV files.
        prefix: Prefix for output filenames.

    Returns:
        Dictionary mapping data type to output file path.
    """
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    exported_files = {}

    # Map of data keys to export configurations
    export_configs = {
        'hitters': ('players', 'Player batting statistics'),
        'pitchers': ('pitchers', 'Player pitching statistics'),
        'game_log': ('games', 'Game log'),
        'stadiums': ('stadiums', 'Stadium records'),
        'team_records': ('teams', 'Team records'),
    }

    for data_key, (file_suffix, description) in export_configs.items():
        df = processed_data.get(data_key)
        if df is not None and isinstance(df, pd.DataFrame) and not df.empty:
            output_path = output_dir / f"{prefix}_{file_suffix}.csv"
            export_to_csv(df, output_path)
            exported_files[data_key] = output_path
            info(f"  Exported {description}: {output_path.name}")

    # Export milestones
    milestones = processed_data.get('milestones', {})
    if milestones:
        for milestone_type, df in milestones.items():
            if df is not None and isinstance(df, pd.DataFrame) and not df.empty:
                safe_name = milestone_type.lower().replace(' ', '_').replace('+', 'plus')
                output_path = output_dir / f"{prefix}_milestone_{safe_name}.csv"
                export_to_csv(df, output_path)
                exported_files[f'milestone_{safe_name}'] = output_path

    # Export summary rows as CSV
    summary_rows = processed_data.get('summary_rows', [])
    if summary_rows:
        summary_df = pd.DataFrame(summary_rows)
        output_path = output_dir / f"{prefix}_summary.csv"
        export_to_csv(summary_df, output_path)
        exported_files['summary'] = output_path

    info(f"Exported {len(exported_files)} CSV files to {output_dir}")
    return exported_files


def export_raw_games_to_csv(
    games: List[Dict[str, Any]],
    output_path: Union[str, Path]
) -> Path:
    """Export raw game data to a flat CSV.

    This creates a denormalized view of all games with key statistics.

    Args:
        games: List of parsed game data dictionaries.
        output_path: Path for the output CSV file.

    Returns:
        Path to the created CSV file.
    """
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    rows = []
    for game in games:
        basic = game.get('basic_info', {})
        linescore = game.get('linescore', {})

        row = {
            'game_id': game.get('game_id', ''),
            'date': basic.get('date_yyyymmdd', ''),
            'away_team': basic.get('away_team', ''),
            'home_team': basic.get('home_team', ''),
            'away_score': basic.get('away_score_value', 0),
            'home_score': basic.get('home_score_value', 0),
            'venue': basic.get('venue', ''),
            'attendance': basic.get('attendance_value', 0),
            'duration': basic.get('duration', ''),
            'weather': basic.get('weather', ''),
            'temperature_f': basic.get('temperature_f', ''),
            'away_hits': linescore.get('away', {}).get('H', 0),
            'home_hits': linescore.get('home', {}).get('H', 0),
            'away_errors': linescore.get('away', {}).get('E', 0),
            'home_errors': linescore.get('home', {}).get('E', 0),
            'innings': len(linescore.get('away', {}).get('innings', [])),
            'doubleheader': game.get('doubleheader', '0'),
            'winning_pitcher': game.get('pitcher_decisions', {}).get('winning_pitcher', ''),
            'losing_pitcher': game.get('pitcher_decisions', {}).get('losing_pitcher', ''),
            'save_pitcher': game.get('pitcher_decisions', {}).get('save_pitcher', ''),
        }
        rows.append(row)

    df = pd.DataFrame(rows)
    df.to_csv(output_path, index=False, encoding='utf-8-sig')
    info(f"Exported {len(rows)} games to {output_path}")

    return output_path
