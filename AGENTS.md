# Codex Instructions

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
Website auto-deploys to: https://mlb-processor.surge.sh as part of `python3 -m baseball_processor` / `--website-only`.

The output is **two files** — `MLB Game Passport - BREF.html` and `data.json` (the React app fetches `data.json` next to itself at runtime). Both must be deployed together; deploying only the HTML produces a "Failed to Load Data: HTTP 404" error on the live site.

### Manual deploy fallback
If the auto-deploy step times out or fails, redeploy from the **project root** so the directory listing includes both files:

```bash
# from the project root (which contains the .html and data.json)
surge . mlb-processor.surge.sh
```

Surge expects the index file to be named `index.html`. Stage it in a temp dir if needed:

```bash
rm -rf /tmp/mlb-deploy && mkdir -p /tmp/mlb-deploy
cp "MLB Game Passport - BREF.html" /tmp/mlb-deploy/index.html
cp data.json /tmp/mlb-deploy/data.json
surge /tmp/mlb-deploy mlb-processor.surge.sh
```

**Do NOT** deploy a directory that contains only the HTML — `data.json` MUST be alongside it or the site 404s.

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

### Web Server (Add Games from Browser/Phone)
```bash
python3 -m baseball_processor.server              # Local-only on port 5555
python3 -m baseball_processor.server --port 8080   # Custom port
python3 -m baseball_processor.server --lan         # Allow phone access on same wifi
python3 -m baseball_processor.server --token abc   # Use a stable add-game token
```
Opens a web UI at the printed tokenized local URL. Use `--lan` for the printed phone URL. Browse dates, tap a game to add it, auto-processes and deploys.

### Add Game via MLB API
```bash
python3 -m baseball_processor.scrapers.add_game --date 2026-04-07 --teams PHI SF  # By date + teams
python3 -m baseball_processor.scrapers.add_game --gamepk 823235                   # By game PK
python3 -m baseball_processor.scrapers.add_game --date 2026-04-12                 # List all games on date
python3 -m baseball_processor.scrapers.add_game --date 2026-04-12 --teams SF BAL --force  # Overwrite existing
```
Adds a game directly from the MLB API — no BREF HTML needed. Instant, no rate limits. Output is identical to BREF-parsed games. Run the processor afterward to include in website.

### Download BREF HTML Backups
```bash
python3 -m baseball_processor.scrapers.download_bref           # Download missing HTMLs (last 30 days)
python3 -m baseball_processor.scrapers.download_bref --all     # Check all API-sourced games
python3 -m baseball_processor.scrapers.download_bref --dry-run # Preview without downloading
```
Automatically downloads BREF HTML box scores for API-sourced games that are >24 hours old and don't already have an HTML file. Respects BREF rate limits (3.2s between requests).

### Scoring Change Check
```bash
python3 -m baseball_processor.scrapers.scoring_check              # Check all games
python3 -m baseball_processor.scrapers.scoring_check --recent 30  # Last 30 days only
python3 -m baseball_processor.scrapers.scoring_check --game SFN202604070  # Specific game
python3 -m baseball_processor.scrapers.scoring_check --verbose    # Show all comparisons
```
Compares cached BREF box scores against MLB API boxscores to detect scoring changes. Prints re-download URLs for games with mismatches. Note: older games (pre-2019) may show false positives due to name matching differences between BREF and MLB API.

### Career Highs
```bash
python3 -m baseball_processor.scrapers.career_highs_scraper                # Scrape all players (~1.3 hr first run)
python3 -m baseball_processor.scrapers.career_highs_scraper --player adamewi01  # One player
python3 -m baseball_processor.scrapers.career_highs_scraper --refresh      # Re-scrape current season only
```
Fetches career game logs from MLB API to compute per-season and career highs for all players. Cached in `cache/career_highs.json`. Used by the serializer to annotate playerGames/pitcherGames with career/season high flags.

## Key Files
- `baseball_processor/main.py` - Main pipeline, auto-enrichment, career scraping triggers
- `baseball_processor/engines/milestone_engine.py` - Milestone detection (26 types)
- `baseball_processor/engines/all_time_passing_engine.py` - All-time list passing detection
- `baseball_processor/parsers/html_parser.py` - BREF HTML parsing
- `baseball_processor/parsers/mlb_api_parser.py` - MLB Stats API parsing (pitch data, hit data, umpires, ABS, lineups)
- `baseball_processor/website/react_app.py` - Assembles the generated React app from ordered chunks
- `baseball_processor/website/react_chunks/` - React source chunks for the generated static website
- `baseball_processor/website/serializers.py` - Data serialization to JSON
- `baseball_processor/scrapers/career_firsts_scraper.py` - Career milestone scraper
- `baseball_processor/scrapers/all_time_leaders_scraper.py` - All-time leaderboard scraper
- `baseball_processor/scrapers/pitch_data_scraper.py` - MLB API enrichment scraper
- `baseball_processor/scrapers/scoring_check.py` - BREF vs API scoring change detector
- `baseball_processor/scrapers/career_highs_scraper.py` - Career/season high detection via MLB API game logs
- `baseball_processor/scrapers/add_game.py` - Add games directly from MLB API (no BREF HTML needed)
- `baseball_processor/scrapers/download_bref.py` - Auto-download BREF HTML backups for API-sourced games

## Architecture Notes
- Milestone detection uses tiered pattern (only highest tier reported per category)
- Career milestones track every 100 (e.g., Hit #100, #200, #300... up to #4000)
- Website output is a static React app (10 tabs, 21 subtabs) assembled from `website/react_chunks/` and embedded into the generated HTML
- All-time passing detection distinguishes "tied" vs "passed" events
- Game deduplication by date+teams (prevents BREF + API duplicates)
- Sports-Reference sites hide tables in HTML comments - must extract with BeautifulSoup Comment class
- MLB API game IDs start with 'M' prefix (e.g., MSF202603230), BREF IDs don't (e.g., SFN202603230)
- Spring training games excluded from cumulative stat badges but included in game log
- Player bios cached in `cache/player_bios.json` (fetched from MLB API)

## Local Website Review
```bash
python3 -m baseball_processor --from-cache-only --skip-debut-update --website-only --no-deploy --no-emoji
python3 -m http.server 8765
```
Open `http://127.0.0.1:8765/MLB%20Game%20Passport%20-%20BREF.html`. Keep `data.json` beside the HTML file.

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
- Update this AGENTS.md file with the finding
- Add to "Do NOT" section if it's a common mistake
- Add to "Architecture Notes" if it's a structural insight

## Do NOT
- Create duplicate nested directories like `baseball_processor/baseball_processor/`
- Use `python` command (always `python3`)
- Scrape Baseball Reference faster than 3.1s between requests
- Remove milestone types from MILESTONE_KEYS without also adding them to ALL_DETECTION_KEYS (causes KeyError)
- Assume game IDs have the same format for BREF vs API games (different prefixes)
