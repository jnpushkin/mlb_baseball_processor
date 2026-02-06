# Claude Code Instructions

## Python
Always use `python3` instead of `python` for all commands.

## Project Structure
- `baseball_processor/` - Main Python package (run with `python3 -m baseball_processor`)
- `Current Season Games/` - Input HTML files from Baseball Reference
- `cache/` - Cached parsed game data and career firsts
- `mlb_references/` - Reference data (debuts, Hall of Fame, etc.)
- `docs/` - Generated website files

## Running the Processor
```bash
python3 -m baseball_processor                    # Process games and generate website
python3 -m baseball_processor --website-only     # Skip Excel generation
python3 -m baseball_processor --quick-stats      # Just print summary stats
```

## Deployment
Website auto-deploys to: https://mlb-processor.surge.sh

## Scraping Career Firsts
```bash
python3 -m baseball_processor.scrapers.career_firsts_scraper --delay 3.1
./scrape_career_firsts_batch.sh  # Batch mode with retry on rate limits
```

**Important:** Baseball Reference rate limits aggressively. Use 3.1+ second delays between requests. On 429 errors, wait 15 minutes before retrying.

## Scraping All-Time Leaders
```bash
python3 -m baseball_processor.scrapers.all_time_leaders_scraper              # All 18 stats
python3 -m baseball_processor.scrapers.all_time_leaders_scraper --type batting
python3 -m baseball_processor.scrapers.all_time_leaders_scraper --stat SV    # Just saves
```

Creates JSON files in `mlb_references/all_time_leaders/` for detecting when players pass others on all-time lists. Tracks top 200 for each stat.

## Key Files
- `baseball_processor/engines/milestone_engine.py` - Milestone detection (41 types)
- `baseball_processor/engines/all_time_passing_engine.py` - All-time list passing detection
- `baseball_processor/parsers/html_parser.py` - HTML parsing
- `baseball_processor/website/react_app.py` - Website generation (React-based)
- `baseball_processor/scrapers/career_firsts_scraper.py` - Career milestone scraper
- `baseball_processor/scrapers/all_time_leaders_scraper.py` - All-time leaderboard scraper

## Architecture Notes
- Milestone detection uses tiered elif pattern (only highest tier reported per category)
- Career milestones track every 100 (e.g., Hit #100, #200, #300... up to #4000)
- Website uses React components embedded in Python strings
- Sports-Reference sites (Baseball-Reference, Basketball-Reference) hide tables in HTML comments for lazy loading - must extract and parse them with BeautifulSoup Comment class

## Error Handling
When encountering repeated errors or discovering project-specific quirks:
- Update this CLAUDE.md file with the finding
- Add to "Do NOT" section if it's a common mistake
- Add to "Architecture Notes" if it's a structural insight

## Do NOT
- Create duplicate nested directories like `baseball_processor/baseball_processor/`
- Use `python` command (always `python3`)
- Scrape Baseball Reference faster than 3.1s between requests
