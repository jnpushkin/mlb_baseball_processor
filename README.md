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
- Interactive calendar heatmaps showing attendance patterns
- Team matchup matrices
- Stadium mapping and visit statistics
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
├── utils/               # Utility functions and helpers
│   ├── constants.py
│   ├── globals.py
│   ├── helpers.py
│   ├── log.py
│   └── stat_utils.py
├── website/             # Website generation
│   ├── generator.py
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

## Usage

1. Place Baseball Reference HTML files for games you've attended in the designated input directory
2. Run the processor:
```bash
python main.py
```
3. Generated outputs:
   - Excel reports in the output directory
   - Website files for hosting/viewing

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
