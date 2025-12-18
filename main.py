import os
import sys
import json
import argparse
import traceback
import re
import pandas as pd
from pathlib import Path
from datetime import datetime, timedelta

from .excel.workbook_generator import generate_excel_workbook
from .parsers.html_parser import parse_baseball_reference_boxscore
from .utils.constants import BASE_DIR, DEFAULT_INPUT_DIR, REFERENCES_DIR, HOF_FILE, CACHE_DIR
from .utils.helpers import load_mlb_debuts
from .utils.globals import UmpireTracker
from .utils.log import info, warn, error, set_verbosity, set_use_emoji, configure_file_logging
from .website import generate_website_from_data
from .reports.quick_stats import generate_quick_stats_report, print_quick_stats_report
from .exporters.csv_exporter import export_all_to_csv, export_raw_games_to_csv

def process_html_file(file_path, index=None, total=None):
    """Process a single Baseball-Reference HTML file, with filename-based caching."""
    try:
        if index is not None and total is not None:
            info(f"📄 Processing file {index} of {total}: {os.path.basename(file_path)}")
        else:
            info(f"Processing {file_path}...")

        # Use the filename (without path and extension) as the cache key
        filename = os.path.basename(file_path)
        filename_no_ext = os.path.splitext(filename)[0]
        
        # Clean filename to make it safe for filesystem (remove special chars)
        safe_filename = re.sub(r'[^\w\-_]', '_', filename_no_ext)
        
        # Check cache using filename as key
        cache_path = CACHE_DIR / f"{safe_filename}.json"
        
        if cache_path.exists():
            html_mtime = os.path.getmtime(file_path)
            json_mtime = os.path.getmtime(cache_path)
            
            if html_mtime <= json_mtime:
                # Cache is up to date - use it!
                info("  ✅ Using cached data")
                with open(cache_path, 'r', encoding='utf-8') as f:
                    cached_data = json.load(f)
                    
                    # Optionally show what game this is
                    game_id = cached_data.get("game_id", "Unknown")
                    info(f"     Game ID: {game_id}")
                    
                    return cached_data
            else:
                info("  🔄 Cache outdated, re-parsing...")
        else:
            info("  🆕 No cache found, parsing HTML...")

        # Parse the HTML
        with open(file_path, 'r', encoding='utf-8') as file:
            html_content = file.read()

        game_data = parse_baseball_reference_boxscore(html_content)
        game_id = game_data.get("game_id", "UNKNOWN")

        info(f"  📊 Parsed game: {game_id}")
        
        # Save to cache using filename as key
        with open(cache_path, 'w', encoding='utf-8') as f:
            json.dump(game_data, f, indent=2)
        info("  💾 Saved to cache")

        return game_data

    except Exception as e:
        error_msg = str(e)
        warn(f"❌ Error processing {file_path}: {error_msg}")
        traceback.print_exc()
        # Return a special dict to indicate failure
        return {"_error": True, "file": file_path, "error": error_msg}
  
def process_directory_or_file(input_path, umpire_tracker):
    """Process HTML files from directory or single file."""
    all_games_data = []
    games_missing_umpires = []
    failed_files = []

    if os.path.isfile(input_path):
        if input_path.endswith('.html'):
            game_data = process_html_file(input_path)
            if game_data:
                # Check if this is an error result
                if game_data.get("_error"):
                    failed_files.append(game_data)
                else:
                    game_id = game_data.get("game_id", "UNKNOWN")
                    if not game_data.get("umpires"):
                        games_missing_umpires.append(game_id)
                    else:
                        for pos, name in game_data.get("umpires", {}).items():
                            umpire_tracker.record_umpire(name, pos, game_id)
                    all_games_data.append(game_data)
        else:
            warn(f"❌ File must be an HTML file: {input_path}")
    elif os.path.isdir(input_path):
        html_files = [f for f in os.listdir(input_path) if f.endswith('.html')]
        info(f"Found {len(html_files)} HTML files in {input_path}")
        
        total = len(html_files)

        for idx, filename in enumerate(html_files, start=1):
            file_path = os.path.join(input_path, filename)
            game_data = process_html_file(file_path, idx, total)
            if game_data:
                # Check if this is an error result
                if game_data.get("_error"):
                    failed_files.append(game_data)
                else:
                    game_id = game_data.get("game_id", "UNKNOWN")
                    if not game_data.get("umpires"):
                        games_missing_umpires.append(game_id)
                    else:
                        for pos, name in game_data.get("umpires", {}).items():
                            umpire_tracker.record_umpire(name, pos, game_id)
                    all_games_data.append(game_data)
    else:
        warn(f"❌ Invalid path: {input_path}")
        return []
    
    info(f"✅ Successfully processed {len(all_games_data)} games")
    
    # Report failed files
    if failed_files:
        warn(f"\n❌ Failed to process {len(failed_files)} file(s):")
        for failed in failed_files:
            file_name = os.path.basename(failed["file"])
            error_msg = failed["error"]
            warn(f"   • {file_name}")
            warn(f"     Error: {error_msg}")
        warn(f"\n💡 Tip: Check these files for corruption or formatting issues")
    
        # Save detailed report
        output_dir = os.path.dirname(input_path) if os.path.isfile(input_path) else input_path
        save_failed_files_report(failed_files, output_dir)

    # Report umpire data status
    if games_missing_umpires:
        warn(f"\n⚠️ Missing umpire data in {len(games_missing_umpires)} game(s):")
        for gid in games_missing_umpires:
            warn(f"   • {gid}")
    else:
        info("✅ All games include umpire data.")
    
    return all_games_data

def save_failed_files_report(failed_files, output_dir):
    """Save a report of failed files for later investigation."""
    if not failed_files:
        return
    
    report_path = os.path.join(output_dir, "failed_files_report.txt")
    with open(report_path, 'w') as f:
        f.write("Failed Files Report\n")
        f.write("=" * 60 + "\n\n")
        f.write(f"Total failed: {len(failed_files)}\n")
        f.write(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
        
        for i, failed in enumerate(failed_files, 1):
            f.write(f"{i}. {failed['file']}\n")
            f.write(f"   Error: {failed['error']}\n\n")
    
    info(f"📝 Failed files report saved to: {report_path}")

def main():
    parser = argparse.ArgumentParser(
        description="Combined Baseball Game Processor - Parse HTML box scores and generate Excel workbook"
    )
    parser.add_argument(
        'input_path',
        nargs='?',
        default=DEFAULT_INPUT_DIR,
        help='Directory containing HTML files or single HTML file'
    )
    parser.add_argument(
        '--output-excel',
        default=str(BASE_DIR / 'MLB Game Passport - BREF.xlsx'),
        help='Excel output filename'
    )
    parser.add_argument(
        '--save-json',
        action='store_true',
        help='Save intermediate JSON data file'
    )
    parser.add_argument(
        '--from-cache-only',
        action='store_true',
        help='Load all games from cached JSON files instead of reprocessing HTML'
    )
    parser.add_argument(
        '--excel-only',
        action='store_true',
        help='Generate only Excel workbook, skip website generation'
    )
    parser.add_argument(
        '--website-only',
        action='store_true',
        help='Generate only website, skip Excel workbook (processes data but does not write Excel)'
    )
    parser.add_argument(
        '--verbose',
        action='store_true',
        help='Enable extra debug output'
    )
    parser.add_argument(
        '--no-emoji',
        action='store_true',
        help='Disable emoji in console output'
    )
    parser.add_argument(
        '--log-file',
        type=str,
        default=None,
        help='Path to log file for detailed logging (creates timestamped log if no path given)'
    )
    parser.add_argument(
        '--parallel',
        action='store_true',
        help='Use parallel processing for faster parsing (recommended for 50+ games)'
    )
    parser.add_argument(
        '--workers',
        type=int,
        default=None,
        help='Number of worker processes for parallel mode (default: CPU count - 1)'
    )
    parser.add_argument(
        '--export-csv',
        type=str,
        default=None,
        help='Export all data to CSV files in the specified directory'
    )
    parser.add_argument(
        '--quick-stats',
        action='store_true',
        help='Print quick statistics summary without generating full reports'
    )

    args = parser.parse_args()

    # Configure logging
    set_verbosity(args.verbose)
    set_use_emoji(not args.no_emoji)

    # Enable file logging if requested
    if args.log_file is not None:
        log_path = configure_file_logging(args.log_file if args.log_file else None)
        info(f"📝 Logging to: {log_path}")
    
    # Validate conflicting flags
    if args.excel_only and args.website_only:
        warn("❌ Error: Cannot use both --excel-only and --website-only flags")
        return

    if not os.path.exists(args.input_path) and not args.from_cache_only:
        warn(f"❌ Input path does not exist: {args.input_path}")
        return

    info("⚾️ Starting Baseball Game Processor...")
    info(f"📂 Input: {args.input_path}")
    
    # Create a fresh umpire tracker for this run
    umpire_tracker = UmpireTracker()
    
    if not args.website_only:
        info(f"📊 Output Excel: {args.output_excel}")
        args.output_excel = os.path.expanduser(args.output_excel)
        info(f"▶ Excel will be written to: {os.path.abspath(args.output_excel)}")
    info(f"▶ Current working directory: {os.getcwd()}")

    # Step 1: Load static references
    debut_entries = load_mlb_debuts(REFERENCES_DIR)
    hof_df = pd.read_csv(HOF_FILE)
    if "Name-additional" in hof_df.columns:
        hof_df.rename(columns={"Name-additional": "PlayerID"}, inplace=True)

    # Step 2: Load game data
    if args.from_cache_only:
        info("📦 Loading games from cache only...")
        games_data = []
        for file in CACHE_DIR.glob("*.json"):
            with open(file, 'r', encoding='utf-8') as f:
                games_data.append(json.load(f))
    elif args.parallel:
        # Use parallel processing
        from .utils.parallel import process_files_parallel, default_progress_callback

        html_files = []
        if os.path.isfile(args.input_path) and args.input_path.endswith('.html'):
            html_files = [args.input_path]
        elif os.path.isdir(args.input_path):
            html_files = [
                os.path.join(args.input_path, f)
                for f in os.listdir(args.input_path)
                if f.endswith('.html')
            ]

        if html_files:
            games_data, failed_files = process_files_parallel(
                html_files,
                max_workers=args.workers,
                progress_callback=default_progress_callback if args.verbose else None
            )

            # Process umpire data from successful games
            for game_data in games_data:
                game_id = game_data.get("game_id", "UNKNOWN")
                if game_data.get("umpires"):
                    for pos, name in game_data.get("umpires", {}).items():
                        umpire_tracker.record_umpire(name, pos, game_id)

            if failed_files:
                warn(f"\n❌ Failed to process {len(failed_files)} file(s)")
                save_failed_files_report(failed_files, args.input_path)
        else:
            games_data = []
    else:
        games_data = process_directory_or_file(args.input_path, umpire_tracker)

    if not games_data:
        warn("❌ No games data to process. Exiting.")
        return

    # Quick stats mode - just print summary and exit
    if args.quick_stats:
        info("\n📊 Generating quick statistics report...")
        report = generate_quick_stats_report(games_data)
        print_quick_stats_report(report)
        return

    # Step 3: Save intermediate JSON (optional)
    if args.save_json:
        json_output = os.path.join(os.path.dirname(args.output_excel), "all_games_data.json")
        with open(json_output, 'w', encoding='utf-8') as json_file:
            json.dump(games_data, json_file, indent=2)
        info(f"💾 JSON data saved to {json_output}")

    # Step 4: Generate outputs based on flags
    try:
        if args.website_only:
            # Process data but don't write Excel file
            info("\n🌐 Website-only mode: Processing data without writing Excel...")
            
            processed_data = generate_excel_workbook(
                games_data, 
                args.output_excel,  # Still pass the path (needed for html naming)
                debut_entries, 
                hof_df,
                umpire_tracker,  # Pass the tracker
                write_file=False  # Skip Excel writing
            )
            
            # Generate website
            html_path = args.output_excel.replace('.xlsx', '.html')
            processed_data['_raw_games'] = games_data 
            generate_website_from_data(processed_data, html_path)
            
            info("\n🎉 Processing complete!")
            info(f"✅ Website: {os.path.abspath(html_path)}")
            
        elif args.excel_only:
            # Generate only Excel
            info("\n📊 Excel-only mode: Skipping website generation...")
            
            # Clean up any existing file to prevent duplicates
            if os.path.exists(args.output_excel):
                info(f"🗑️ Removing existing file: {args.output_excel}")
                os.remove(args.output_excel)
            
            processed_data = generate_excel_workbook(
                games_data, 
                args.output_excel,  # Still pass the path (needed for html naming)
                debut_entries, 
                hof_df,
                umpire_tracker,  # Pass the tracker
                write_file=True 
            )
            
            info("\n🎉 Processing complete!")
            info(f"📊 Excel: {os.path.abspath(args.output_excel)}")
            if args.save_json:
                info(f"📄 JSON: {json_output}")
        
        else:
            # Generate both (default behavior)
            info("\n📊 Generating both Excel and website...")
            
            # Clean up any existing file to prevent duplicates
            if os.path.exists(args.output_excel):
                info(f"🗑️ Removing existing file: {args.output_excel}")
                os.remove(args.output_excel)
            
            processed_data = generate_excel_workbook(
                games_data, 
                args.output_excel,  # Still pass the path (needed for html naming)
                debut_entries, 
                hof_df,
                umpire_tracker,  # Pass the tracker
                write_file=True 
            )
            
            info("\n📊 Excel complete, generating website...")
            
            html_path = args.output_excel.replace('.xlsx', '.html')
            processed_data['_raw_games'] = games_data 
            generate_website_from_data(processed_data, html_path)
            
            info("\n🎉 Processing complete!")
            info(f"📊 Excel: {os.path.abspath(args.output_excel)}")
            info(f"✅ Website: {os.path.abspath(html_path)}")
            if args.save_json:
                info(f"📄 JSON: {json_output}")

        # Export to CSV if requested
        if args.export_csv:
            info(f"\n📄 Exporting to CSV...")
            csv_dir = Path(args.export_csv)
            export_all_to_csv(processed_data, csv_dir)
            export_raw_games_to_csv(games_data, csv_dir / "mlb_tracker_raw_games.csv")
            info(f"✅ CSV files exported to: {csv_dir}")

    except Exception as e:
        error(f"❌ Error during processing: {str(e)}", exc_info=True)



if __name__ == '__main__':
    main()