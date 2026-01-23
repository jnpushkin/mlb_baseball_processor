"""Parallel processing utilities for MLB Game Tracker.

This module provides multiprocessing support for parsing multiple game files
concurrently, which can significantly speed up processing for large collections.
"""

from __future__ import annotations

import os
import json
import re
from concurrent.futures import ProcessPoolExecutor, as_completed
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple, Callable

from .constants import CACHE_DIR
from .log import info, warn, debug


def _parse_single_file(args: Tuple[str, Path]) -> Tuple[str, Optional[Dict[str, Any]], Optional[str]]:
    """Parse a single HTML file (worker function for multiprocessing).

    Args:
        args: Tuple of (file_path, cache_dir)

    Returns:
        Tuple of (file_path, game_data or None, error_message or None)
    """
    file_path, cache_dir = args

    try:
        # Import here to avoid pickling issues
        from ..parsers.html_parser import parse_baseball_reference_boxscore

        filename = os.path.basename(file_path)
        filename_no_ext = os.path.splitext(filename)[0]
        safe_filename = re.sub(r'[^\w\-_]', '_', filename_no_ext)
        cache_path = cache_dir / f"{safe_filename}.json"

        # Check cache
        if cache_path.exists():
            html_mtime = os.path.getmtime(file_path)
            json_mtime = os.path.getmtime(cache_path)

            if html_mtime <= json_mtime:
                with open(cache_path, 'r', encoding='utf-8') as f:
                    return (file_path, json.load(f), None)

        # Parse the HTML
        with open(file_path, 'r', encoding='utf-8') as file:
            html_content = file.read()

        game_data = parse_baseball_reference_boxscore(html_content)

        # Save to cache
        with open(cache_path, 'w', encoding='utf-8') as f:
            json.dump(game_data, f, indent=2)

        return (file_path, game_data, None)

    except Exception as e:
        return (file_path, None, str(e))


def process_files_parallel(
    file_paths: List[str],
    max_workers: Optional[int] = None,
    progress_callback: Optional[Callable[[int, int, str], None]] = None
) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
    """Process multiple HTML files in parallel.

    Args:
        file_paths: List of paths to HTML files.
        max_workers: Maximum number of worker processes. Defaults to CPU count.
        progress_callback: Optional callback function(completed, total, filename)

    Returns:
        Tuple of (successful_games, failed_files)
    """
    if max_workers is None:
        # Use CPU count - 1 to leave one core free, minimum 1
        max_workers = max(1, (os.cpu_count() or 2) - 1)

    total = len(file_paths)
    successful_games = []
    failed_files = []

    # Prepare arguments for worker function
    args_list = [(fp, CACHE_DIR) for fp in file_paths]

    info(f"Processing {total} files with {max_workers} workers...")

    with ProcessPoolExecutor(max_workers=max_workers) as executor:
        # Submit all tasks
        future_to_path = {
            executor.submit(_parse_single_file, args): args[0]
            for args in args_list
        }

        completed = 0
        for future in as_completed(future_to_path):
            file_path = future_to_path[future]
            completed += 1

            try:
                path, game_data, error = future.result()

                if error:
                    failed_files.append({"file": path, "error": error})
                    if progress_callback:
                        progress_callback(completed, total, f"FAILED: {os.path.basename(path)}")
                elif game_data:
                    successful_games.append(game_data)
                    if progress_callback:
                        progress_callback(completed, total, os.path.basename(path))

            except Exception as e:
                failed_files.append({"file": file_path, "error": str(e)})
                if progress_callback:
                    progress_callback(completed, total, f"ERROR: {os.path.basename(file_path)}")

    return successful_games, failed_files


def default_progress_callback(completed: int, total: int, filename: str) -> None:
    """Default progress callback that prints progress."""
    percent = (completed / total) * 100
    info(f"  [{completed}/{total}] ({percent:.1f}%) {filename}")
