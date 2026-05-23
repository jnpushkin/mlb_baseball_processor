#!/bin/bash
# MLB Debut Data Updater
#
# This script updates MLB debut data from Baseball-Reference.
# Can be run manually or scheduled via cron.
#
# Usage:
#   ./update_debuts.sh           # Update current year
#   ./update_debuts.sh 2026      # Update specific year
#
# Cron example (update daily at 6 AM):
#   0 6 * * * /path/to/update_debuts.sh >> /path/to/debut_update.log 2>&1
#
# Cron example (update every Monday at 8 AM):
#   0 8 * * 1 /path/to/update_debuts.sh >> /path/to/debut_update.log 2>&1

set -e

# Get the directory where this script is located
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"

# Year to update (default: current year)
YEAR="${1:-$(date +%Y)}"

echo "=========================================="
echo "MLB Debut Updater - $(date)"
echo "=========================================="
echo "Project: $PROJECT_DIR"
echo "Year: $YEAR"
echo ""

cd "$PROJECT_DIR"

# Run the scraper
PYTHONPATH="$PROJECT_DIR" python3 -c "
from baseball_processor.scrapers.debut_scraper import scrape_debuts, save_debuts_csv
from pathlib import Path

year = $YEAR
output_dir = Path('$PROJECT_DIR') / 'mlb_references'

print(f'Fetching {year} debuts...')
df = scrape_debuts(year, verbose=True)

if not df.empty:
    filepath = save_debuts_csv(df, year, str(output_dir))
    print(f'\\nSuccess! Saved {len(df)} entries to:')
    print(f'  {filepath}')
else:
    print('\\nNo data fetched.')
    exit(1)
"

echo ""
echo "Update complete!"
