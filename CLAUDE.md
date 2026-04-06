# Claude Code Instructions

## Python
Always use `python3` instead of `python` for all commands.

## Project Structure
- `baseball_processor/` - Main Python package (run with `python3 -m baseball_processor`)
- `Current Season Games/` - Input HTML files from Baseball Reference
- `cache/` - Cached parsed game data, career firsts, career gamelogs, player bios
- `mlb_references/` - Reference data (debuts, Hall of Fame, all-time leaders, etc.)

## Running the Processor
```bash
python3 -m baseball_processor                    # Process games and generate website
python3 -m baseball_processor --website-only     # Skip Excel generation
python3 -m baseball_processor --quick-stats      # Just print summary stats
```

### Auto-enrichment Pipeline
When processing a new BREF HTML file, the processor automatically:
1. Parses the HTML (BREF box score)
2. Fetches MLB API data (pitch velocity/spin, exit velocity, jersey numbers, umpires, ABS challenges)
3. Scrapes career milestones from BREF for all players in the game
4. Updates gamelogs for all-time leaders who appeared in the game
5. Refreshes all-time leaders if data is >7 days old
6. Runs milestone engine for game milestones
7. Generates website and deploys to Surge

## Deployment
Website auto-deploys to: https://mlb-processor.surge.sh

## Scraping

### Career Firsts
```bash
python3 -m baseball_processor.scrapers.career_firsts_scraper --delay 3.1
python3 -m baseball_processor.scrapers.career_firsts_scraper --player webblo01
python3 -m baseball_processor.scrapers.career_firsts_scraper --all-time-leaders --refresh  # Full gamelogs for leaders
```

### All-Time Leaders
```bash
python3 -m baseball_processor.scrapers.all_time_leaders_scraper              # All 18 stats
python3 -m baseball_processor.scrapers.all_time_leaders_scraper --type batting
python3 -m baseball_processor.scrapers.all_time_leaders_scraper --stat SV    # Just saves
```
Auto-refreshed when >7 days old during processor runs.

### Pitch Data / Exit Velo / ABS Challenges
```bash
python3 -m baseball_processor.scrapers.pitch_data_scraper              # Enrich all cached games
python3 -m baseball_processor.scrapers.pitch_data_scraper --force      # Re-fetch all
python3 -m baseball_processor.scrapers.pitch_data_scraper --dry-run    # Preview
python3 -m baseball_processor.scrapers.pitch_data_scraper --savant-abs # Backfill ABS data from Savant (2025+)
```
Fetches from MLB Stats API: pitch velocity/spin/type, exit velocity/launch angle/distance, jersey numbers.
ABS challenge data sourced from Baseball Savant gamefeed API (more complete than Stats API).

**Important:** Baseball Reference rate limits aggressively. Use 3.1+ second delays between requests. On 429 errors, wait 15 minutes before retrying. MLB Stats API has no rate limit.

## Key Files
- `baseball_processor/main.py` - Main pipeline, auto-enrichment, career scraping triggers
- `baseball_processor/engines/milestone_engine.py` - Milestone detection (26 types)
- `baseball_processor/engines/all_time_passing_engine.py` - All-time list passing detection
- `baseball_processor/parsers/html_parser.py` - BREF HTML parsing
- `baseball_processor/parsers/mlb_api_parser.py` - MLB Stats API parsing (pitch data, hit data, umpires, ABS, lineups)
- `baseball_processor/website/react_app.py` - Website generation (React, ~8000 lines)
- `baseball_processor/website/serializers.py` - Data serialization to JSON
- `baseball_processor/scrapers/career_firsts_scraper.py` - Career milestone scraper
- `baseball_processor/scrapers/all_time_leaders_scraper.py` - All-time leaderboard scraper
- `baseball_processor/scrapers/pitch_data_scraper.py` - MLB API enrichment scraper

## Architecture Notes
- Milestone detection uses tiered pattern (only highest tier reported per category)
- Career milestones track every 100 (e.g., Hit #100, #200, #300... up to #4000)
- Website is a single-file React app (10 tabs, 21 subtabs) embedded in Python strings
- All-time passing detection distinguishes "tied" vs "passed" events
- Game deduplication by date+teams (prevents BREF + API duplicates)
- Sports-Reference sites hide tables in HTML comments - must extract with BeautifulSoup Comment class
- MLB API game IDs start with 'M' prefix (e.g., MSF202603230), BREF IDs don't (e.g., SFN202603230)
- Spring training games excluded from cumulative stat badges but included in game log
- Player bios cached in `cache/player_bios.json` (fetched from MLB API)

## Website Structure (10 tabs)
1. **Dashboard** - Overview stats, charts, trends
2. **Games** - Game log with detail modals (box score, lineups, play-by-play, context)
3. **Players** - Hitters | Pitchers | No Stats | College | Leaderboards
4. **Milestones** - Game Milestones | All-Time Passings (with career firsts)
5. **Venues** - Map & Tables | Calendar
6. **Progress** - Division Checklist | Badges | Matchups
7. **Special** - Records | Debuts | Final Games | Signature HRs
8. **Frivolities** - Jersey Numbers | Origins | Birthdays | Scorigami | Umpires
9. **Companions** - Game companion tracking
10. **Orioles** - Team-specific dashboard

## Error Handling
When encountering repeated errors or discovering project-specific quirks:
- Update this CLAUDE.md file with the finding
- Add to "Do NOT" section if it's a common mistake
- Add to "Architecture Notes" if it's a structural insight

## Do NOT
- Create duplicate nested directories like `baseball_processor/baseball_processor/`
- Use `python` command (always `python3`)
- Scrape Baseball Reference faster than 3.1s between requests
- Remove milestone types from MILESTONE_KEYS without also adding them to ALL_DETECTION_KEYS (causes KeyError)
- Assume game IDs have the same format for BREF vs API games (different prefixes)
