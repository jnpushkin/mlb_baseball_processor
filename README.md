# MLB Baseball Processor

A comprehensive personal baseball attendance tracker that processes game data from Baseball Reference and generates detailed statistics, visualizations, and interactive web reports.

## Overview

This project processes Baseball Reference HTML files for games you've attended and generates:
- Detailed Excel reports with attendance statistics and milestones
- Interactive website with visualizations and analytics
- Player milestone tracking (achievements witnessed at games)
- Stadium records and attendance patterns
- Comprehensive game logs and statistics

## Features

### Data Processing
- **Game Log Processing**: Extracts and analyzes game data from Baseball Reference HTML files
- **Player Statistics**: Tracks individual player performance across attended games
- **Milestone Detection**: Identifies significant player achievements (career milestones, records, etc.)
- **Signature Home Runs**: Special tracking for memorable home runs
- **Stadium Records**: Attendance patterns and statistics by venue

### Excel Reports
- Comprehensive attendance summaries
- Player statistics breakdowns
- Milestone achievements
- Game-by-game logs with formatting
- Stadium visit tracking

### Website Generation
- Interactive calendar showing all months (March-October)
- Team matchup matrices
- Division checklist (track teams/stadiums by division)
- Badges and achievements system
- Companions tracking (games attended with others)
- Team-specific dashboards (e.g., Orioles with streaks, opponent breakdowns)
- Smart insights and analytics
- Statistical leaders and trends
- Responsive design for mobile and desktop

## Project Structure

```
mlb_baseball_processor/
├── engines/              # Core processing engines
│   ├── game_log_processor.py
│   ├── milestone_engine.py
│   └── special_events_engine.py
├── excel/               # Excel generation and formatting
│   ├── generators.py
│   ├── formatters.py
│   └── workbook_generator.py
├── parsers/             # HTML and data parsers
│   ├── html_parser.py
│   ├── play_by_play_parser.py
│   └── stats_parser.py
├── processors/          # Specialized stat processors
│   ├── game_log_processor.py
│   ├── milestones_processor.py
│   ├── player_stats_processor.py
│   ├── signature_home_runs_processor.py
│   ├── stadium_records_processor.py
│   └── summary_stats_processor.py
├── scrapers/            # Web scrapers for external data
│   ├── career_firsts_scraper.py  # Career firsts & milestones
│   └── debut_scraper.py          # MLB debut data
├── utils/               # Utility functions and helpers
│   ├── constants.py
│   ├── globals.py
│   ├── helpers.py
│   ├── log.py
│   └── stat_utils.py
├── website/             # Website generation
│   ├── generator.py
│   ├── react_app.py
│   ├── react_chunks/    # Ordered React source chunks assembled into the static app
│   ├── serializers.py
│   └── templates.py
└── main.py             # Main entry point
```

## Requirements

- Python 3.8+
- Required packages:
  - BeautifulSoup4 (HTML parsing)
  - openpyxl (Excel generation)
  - Additional dependencies (see `requirements.txt`)

## Installation

1. Clone the repository:
```bash
git clone https://github.com/jnpushkin/mlb_baseball_processor.git
cd mlb_baseball_processor
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

## Testing

Preferred test command after installing requirements:
```bash
python3 -m pytest
```

Local quality gate:
```bash
scripts/check.sh
```

No-extra-install fallback:
```bash
python3 -m unittest discover -s tests
```

## Usage

1. Place Baseball Reference HTML files for games you've attended in the input directory (e.g., `Current Season Games/`)
2. Run the processor:
```bash
python3 -m baseball_processor "Current Season Games"
```
3. Generated outputs:
   - Excel workbook: `MLB Game Passport - BREF.xlsx`
   - Interactive website: `MLB Game Passport - BREF.html`
   - Website data payload: `data.json`

The website shell and `data.json` are intentionally generated at the project root by default so local review and auto-deploy can serve them together. Temporary workbooks, logs, and generated payloads are ignored by Git unless they are intentional fixtures.

For local website review, serve the project root and open the generated HTML:
```bash
python3 -m http.server 8765
```
Then visit `http://127.0.0.1:8765/MLB%20Game%20Passport%20-%20BREF.html`.

### Command Line Options

| Option | Description |
|--------|-------------|
| `--output-excel FILE` | Custom Excel filename |
| `--save-json` | Save intermediate JSON data |
| `--from-cache-only` | Load from cache (skip HTML parsing) |
| `--excel-only` | Generate only Excel |
| `--website-only` | Generate only website |
| `--verbose` | Enable debug output |
| `--parallel` | Use parallel processing for faster parsing |
| `--export-csv DIR` | Export all data to CSV files |
| `--deploy` | Deploy website to Surge after generation |
| `--scrape-career-firsts` | Scrape career firsts for players in processed games |

### Companions Tracking

Create a `companions.csv` file to track who you attended games with:
```csv
GameID,Companions
BAL202505130,Dad
SFN202507110,Dad|Mom
```

### Career Firsts Scraper

Scrape Baseball Reference to find career firsts (first hit, first HR, etc.) and career milestones (100th HR, 3000th hit, etc.) for players in your attended games.

**Standalone Usage:**
```bash
# Scrape career firsts for all players in your games
python -m baseball_processor.scrapers.career_firsts_scraper

# Scrape a specific player
python -m baseball_processor.scrapers.career_firsts_scraper --player troutmi01

# Scrape players from a specific game file
python -m baseball_processor.scrapers.career_firsts_scraper --game "Game_Box_Score.json"

# Refresh only players from 2025 games
python -m baseball_processor.scrapers.career_firsts_scraper --refresh-year 2025

# Re-scrape only batting data (preserves pitching data)
python -m baseball_processor.scrapers.career_firsts_scraper --refresh-batting

# Re-scrape only pitching data (preserves batting data)
python -m baseball_processor.scrapers.career_firsts_scraper --refresh-pitching

# Check for career firsts you witnessed
python -m baseball_processor.scrapers.career_firsts_scraper --check-witnessed
```

**Career Firsts Scraper Options:**

| Option | Description |
|--------|-------------|
| `--player ID` | Scrape a specific player by Baseball Reference ID |
| `--game FILE` | Scrape players from a specific cached game JSON file |
| `--refresh` | Force refresh cached data |
| `--refresh-year YEAR` | Refresh only players from games in a specific year |
| `--refresh-batting` | Re-scrape only batting data for all cached players |
| `--refresh-pitching` | Re-scrape only pitching data for all cached players |
| `--check-witnessed` | Check for career firsts witnessed at attended games |
| `--delay SECONDS` | Delay between requests (default: 3.05s) |
| `--quiet` | Suppress progress messages |

**Tracked Batting Milestones:**
- Firsts: Hit, Home Run, RBI, Double, Triple, Walk, Stolen Base, Run
- Thresholds: Hits (100-4000), HRs (10-800), RBIs (100-2000), Doubles (50-700), Triples (25-200), SBs (50-800), Walks (100-2000), Runs (100-2000)

**Tracked Pitching Milestones:**
- Firsts: Win, Save, Strikeout, Inning Pitched, Start, Complete Game, Shutout
- Thresholds: Wins (25-350), Saves (25-600), Strikeouts (100-3500), Innings Pitched (100-3500), Starts (50-500), Complete Games (10-100), Shutouts (10-100)

## Technologies

- **Python**: Core processing and data analysis
- **BeautifulSoup4**: HTML parsing from Baseball Reference
- **openpyxl**: Excel report generation
- **React**: Interactive website frontend (for visualization components)

## Data Source

Game data is sourced from [Baseball Reference](https://www.baseball-reference.com/), which provides comprehensive statistics and play-by-play information for MLB games.

## Features in Development

- Enhanced milestone detection algorithms
- Additional visualization types
- Historical trend analysis
- Advanced statistical insights

## Author

Personal project by Jeremy Pushkin

## License

This project is for personal use. Baseball data is property of MLB and Baseball Reference.
