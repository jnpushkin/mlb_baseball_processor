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
python3 -m baseball_processor --website-only --skip-ncaa-player-refresh  # Skip cross-project refresh
```

### Auto-enrichment Pipeline
When processing a new BREF HTML file, the processor automatically:
1. Parses the HTML (BREF box score)
2. Fetches MLB API data (pitch velocity/spin, exit velocity, jersey numbers, umpires, ABS challenges)
3. Scrapes career milestones from BREF for all players in the game
4. Updates gamelogs for all-time leaders who appeared in the game
5. Refreshes all-time leaders if data is >7 days old
6. Runs milestone engine for game milestones
7. Exports MLB shared player data for NCAA/MiLB cross-project linking
8. Refreshes the NCAA processor's shared player export from local caches
9. Generates website and deploys to Surge

## Deployment
Website auto-deploys to: https://mlb-processor.surge.sh as part of `python3 -m baseball_processor` / `--website-only`.

The current schema-v2 output is a **complete compiled release**: `MLB Game Passport - BREF.html`, `data.json`, content-hashed `data-index-*.json`, per-game and section `data-*.json` files, `assets/` (compiled JavaScript, CSS, and Leaflet images), `sw.js`, and `release.json`. The HTML loads its specific hashed index, then fetches section libraries and individual game details on demand. `release.json` is the authoritative file list with SHA-256 checksums. Old sidecars may remain locally but are not dependencies of the current build.

Install the pinned Node build tools once with `npm ci` (Node 22 or newer). Normal website generation invokes the compiler. For a quick UI-only rebuild from the existing serialized archive, run `npm run build:website`.

### Validate and deploy
```bash
python3 -m baseball_processor.website.release
python3 -c 'import sys; from baseball_processor.main import deploy_to_surge; sys.exit(0 if deploy_to_surge("MLB Game Passport - BREF.html", "mlb-processor.surge.sh") else 1)'
```
The deploy helper validates the manifest, stages exactly its files, and supplies both `index.html` and the named HTML shell. Use this same command if automatic deployment fails. **Do not deploy the project root or copy only HTML/JSON:** the compiled assets and service worker must ship together with their hashed data dependencies. The legacy deployment fallback remains only for older bundles without `release.json`.

Releases retain two previous hashed indexes and all their data dependencies in `release.json.previousIndexes` so already-open tabs keep working. To restore an older locally available release during a repair, use `npm run build:website -- --retain-index data-index-<hash>.json`. Retention is bounded; the runtime also refreshes the stable `data.json` pointer on a missing hashed file and retries once. Never cache stable release pointers ahead of the network or merge an old in-flight section response into a newer index. Verify deployment transitions, not just a fresh-page load.

### Frontend checks
```bash
python3 -m pip install -r requirements-dev.txt
npm ci
python3 -m ruff check baseball_processor/jobs.py baseball_processor/website/bundle.py baseball_processor/website/release.py scripts/rebuild_website.py scripts/serve_browser_fixture.py tests/test_passport_v2.py
python3 -m pytest -q
npx playwright install chromium
npm run test:browser
python3 -m baseball_processor.website.release .browser-fixture
```
Browser tests use an isolated synthetic archive on port 8769; they do not add real games or publish the archive. The CI workflow checks Python regressions, browser journeys, and the fixture release manifest. `frontend/runtime.js`, `frontend/sw.js`, and `frontend/build.mjs` are source files; generated root assets and `sw.js` are ignored.
Before pushing website changes, run the lint, Python, browser, and fixture-release checks in `.github/workflows/website.yml`; passing tests alone does not establish that CI passes. After pushing a CI repair, verify the new GitHub Actions run succeeds before reporting the repair complete.

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

### Awards
```bash
python3 -m baseball_processor.scrapers.awards_scraper
python3 -m baseball_processor.scrapers.awards_scraper --page mlb-relievers-of-the-month
python3 -m baseball_processor --update-awards --website-only
```
`mlb_references/awards.json` auto-refreshes when >7 days old during normal website-capable processor runs. Use `--skip-awards-update` to keep runs local, or `--update-awards` to force a refresh even in cache-only mode.

### All-Star Rosters
```bash
python3 -m baseball_processor.scrapers.all_star_scraper --year 2026 --merge
python3 -m baseball_processor --update-all-stars --all-star-year 2026 --website-only
```
`mlb_references/all_star_participants.json` auto-refreshes the current All-Star year when stale (>7 days), missing, or still a zero-entry pre-roster stub during normal website-capable runs. Use `--skip-all-stars-update` to keep runs local, or `--update-all-stars` to force a selected-year refresh even in cache-only mode.

### Splash Hits / McCovey Cove
```bash
python3 -m baseball_processor.scrapers.splash_hits_scraper
python3 -m baseball_processor --update-splash-hits --website-only
```
`mlb_references/splash_hits_all_lines.csv` and `mlb_references/other_mccovey_cove_hr.csv` auto-refresh from the Giants MLB.com Splash Hits page when >1 day old during normal network-capable processor runs. Use `--skip-splash-hits-update` for local/debug runs, or `--update-splash-hits` to force the refresh even in cache-only mode. The MLB.com page stores the lists inside `__NEXT_DATA__` WYSIWYG slots; the scraper normalizes page quirks such as visitor rows with an extra `SF` token before the pitcher and the historical `7/820/18` date typo.

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

### BREF ID Backfill
```bash
python3 -m baseball_processor.scrapers.bref_id_backfill --dry-run
python3 -m baseball_processor.scrapers.bref_id_backfill --player "Gage Jump"
python3 -m baseball_processor.scrapers.bref_id_backfill --max-suffix 99
```
Explicit repair job for fresh debut/player IDs. It scans cached game JSON for register/MLB-placeholder IDs, validates published BREF pages by name, then walks the BREF suffixes until the first 404 to infer the next MLB-style BREF ID. This is intentionally not part of the hot parser path. It paces BREF player-page requests at 3.2s and stops on 429.

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
- Website output is a static React app (10 primary tabs with grouped subtabs) assembled from `website/react_chunks/` and compiled by esbuild/Tailwind into hashed local assets. `react_chunks/passport.jsx` owns the shared route, scope, home, recap, planner, comparisons, and health UI.
- Website-capable MLB runs write `data/shared_players.json`, then call the sibling NCAA processor's `python3 -m baseball_processor --refresh-shared-players` cache-only command before serialization. This keeps the Players > College tab current. Use `--skip-ncaa-player-refresh` or `MLB_PROCESSOR_SKIP_NCAA_REFRESH=1` only for local/debug runs.
- All-time passing detection distinguishes "tied" vs "passed" events
- Game deduplication by date+teams (prevents BREF + API duplicates)
- Sports-Reference sites hide tables in HTML comments - must extract with BeautifulSoup Comment class
- Baseball-Reference award pages use mixed table shapes: standard `data-stat` rows, matrix grids (Gold Glove/Silver Slugger/monthly awards), and malformed nested `<tr>` title tables. Use `awards_scraper` parsing helpers instead of assuming normal tbody rows.
- Awards are loaded from `mlb_references/awards.json` during website serialization. Normal website-capable processor runs refresh that file when stale before generating `award-data.json`; cache-only and quick-stats runs stay local unless `--update-awards` is passed.
- MLB API game IDs start with 'M' prefix (e.g., MSF202603230), BREF IDs don't (e.g., SFN202603230)
- Spring training games excluded from cumulative stat badges but included in game log
- Player bios cached in `cache/player_bios.json` (fetched from MLB API)
- MLB draft API `roundPickNumber` is unreliable in some historical payloads (notably 2002 phase/regular round merges). Use `draft_scraper` normalization for within-round slots, preserve `rawRound` for supplemental labels, and keep all draft records for players drafted multiple times.
- Downloaded BREF HTML backups for API-sourced games should short-circuit to the existing API cache by inferring the BREF-style game ID from the backup filename. Do not reparse those backups just to rediscover the game ID.
- A date/team matchup is not a unique BREF backup identity because doubleheaders share both. Match local backups to API games using the BREF canonical game ID in the HTML, and give Game 2 a distinct filename so the downloader cannot skip or overwrite it.
- API pinch-hit home runs must be derived by matching normalized pinch-hitter substitutions to that player's first subsequent plate appearance; HTML-only substitution parsing is unavailable for API-sourced caches.
- The MLB.com Splash Hits page contains source typos and can encounter both provisional register IDs and later canonical BREF IDs for the same player. Repair known page typos in the scraper and prefer canonical MLB BREF IDs when resolving rows.
- Signature-HR reference matching cannot use date plus player appearance alone: a player can appear in both games of a doubleheader. Require a positive HR total in the specific game, use the reference pitcher against HR play-by-play when available, and suppress the reference with a warning if it still maps to multiple game IDs.
- The shared React `DataTable` supplies a default mobile card for every table; specialized story views can still pass `mobileCard` for custom hierarchy. Keep the desktop table hidden below the `sm` breakpoint instead of reintroducing horizontally scrolling phone tables.
- Global dark-mode CSS recognizes specific light-gradient utility fragments. Reuse the supported `from-blue-50 ... to-indigo-50` collection-header pattern or add a matching override in `website/templates.py`; an unrecognized pale gradient can leave light text on a light background.
- Individual defensive errors are source-specific: BREF games credit them from `footer_summary[*].E`, while MLB API games expose per-player `stats.fielding.errors` in the boxscore. The defensive tracker should use the BREF footer when present, otherwise row-level API `E`, with play-by-play text only as a fallback for older API caches. BREF footer names can have 3+ tokens (e.g., `Jung Hoo Lee`), so avoid fixed first/last-name regexes.
- Website IP display should keep outs as the canonical value for UI calculations and use the shared React helpers (`formatOutsAsIP`, `baseballIPToOuts`, `formatHistoricalStatValue`) for display/sort/filter boundaries. Avoid accumulating IP as normal decimal innings in React; it leaks values like `#.6667` instead of baseball notation (`#.2`).
- Stolen bases and caught stealing are runner-owned events. For BREF games, credit SB/CS from the batting row `Details`/direct row stats via `parse_batting_detail_counts`; play-by-play descriptions happen during another batter's plate appearance and can miscredit the current `batter`.
- In the situational hitting tracker, any home run with bases loaded is a grand slam even when play-by-play text says only "homered" instead of "grand slam"; the website Bases Loaded grand-slam table should aggregate from the canonical Grand Slams milestone data so it stays consistent with the Milestones tab.
- Website game durations pass through Excel fractions of a day. Round to total integer minutes before formatting hours/minutes; truncating fractional hours and minutes can turn 1:55 into 1:54.
- Website date filters must compare normalized date-only values. Mixing `new Date('MM/DD/YYYY')` with `new Date('YYYY-MM-DD')` mixes local and UTC midnight and can exclude the inclusive end date in Pacific time.
- A successful add-game cache write does not establish successful processing or deployment. Propagate processor exit status and deployment results before reporting "added and deployed" in the local server UI.

- Shared date-only, search-normalization, and distinct-player-count helpers live in `website/react_chunks/browser_utils.py`; their behavior is exercised in Node through `tests/test_audit_regressions.py`.
- Use the shared `Modal` component in `website/react_chunks/dialog.py` for overlays. It provides accessible naming, Escape dismissal, focus trapping/restoration, body scroll locking, and nested-dialog ordering. Game arrow navigation is passed through its `onPrevious` / `onNext` props.
- The add-game server reports `saved`, `processed`, and `deployed` separately and reuses cached games on retries. Build subprocesses must use `check=True`; processing failures must exit nonzero. Deployment validates the required JSON manifests and referenced sidecars before uploading.

## Local Website Review
```bash
python3 -m baseball_processor --from-cache-only --skip-debut-update --website-only --no-deploy --no-emoji
python3 -m http.server 8765
```
Open `http://127.0.0.1:8765/MLB%20Game%20Passport%20-%20BREF.html`. Keep every `release.json` dependency beside the HTML file, including `assets/` and the hashed index. Validate the release before preview or deployment.

## Website Structure (10 tabs)
1. **Dashboard** - Overview stats, charts, trends
2. **Games** - Game log with detail modals (box score, lineups, play-by-play, context)
3. **Players** - Stats | Recognition | Background | Tools groups
4. **Milestones** - Game Milestones | All-Time Passings (with career firsts)
5. **Venues** - Map & Tables | Calendar
6. **Progress** - Division Checklist | Badges | Matchups
7. **Special** - Records | Debuts | Final Games | Signature HRs
8. **Frivolities** - Jersey Numbers | Draft Picks | Origins | Birthdays | Home/Away | Scorigami | Umpires
9. **Companions** - Game companion tracking
10. **Orioles** - Team-specific dashboard

## Website and Add-Game Invariants
- Add-game POST requests return durable job IDs. Job progress is stored in `cache/add_game_jobs.json`; saved, processed, and deployed stages must remain distinct. Interrupted jobs become retryable failures after restart.
- The initial index deliberately omits full statistics, milestones, awards, biographies, draft data, and play-by-play. Add every new section dependency to `passportKeysForRoute`; retain navigation entries before their library has loaded.
- Individual game payloads contain `_detailPlayerGames`, `_detailPitcherGames`, `_detailMilestones`, `_detailCareerFirsts`, and `_detailPassings`. Game dialogs must work from a copied URL and from an explicitly saved offline recap without global libraries.
- Route changes close entity dialogs themselves. Do not call a history-based close handler after navigating to a new section: that undoes the navigation. Subtab state must also reset when Back returns to a route with no explicit subtab.
- Shared Browse filters scope the home/recap, games, milestone views, and player stat views. Historical collection sections show a lifetime label. Record Book statistics exclude spring training and must say so.
- Private journal text, images, goals, and saved views stay in browser storage and private exports. They must never enter the public serialized archive. Import merges must preserve existing notes and images, validate all entries before writes, and report storage failures.
- First-seen IDs in the release are recomputed chronologically from canonical batting, pitching, and no-stat identities. Do not reuse old cached placeholder first-seen IDs, which can inflate recap totals.
- Pitch and exit-velocity coverage require a positive measurement; a nonempty object containing only pitch totals is not velocity coverage. Game change fingerprints exclude packaging fields so a frontend rebuild is not reported as a source correction.

## Error Handling
When encountering repeated errors or discovering project-specific quirks:
- Update this AGENTS.md file with the finding
- Add to "Do NOT" section if it's a common mistake
- Add to "Architecture Notes" if it's a structural insight

### Analysis and identity invariants (2026-09-21)
- Team display abbreviations, franchise grouping, historical team identity, and source game IDs serve different purposes. The checklist `normalizeTeamCode` returns source-style codes such as `NYN`; do not reuse its output directly for modern display labels. Preserve source IDs used by caches and links.
- Calculate outcomes with `gameScores` and numeric linescores. Parsing display strings can reverse results when labels differ (`WSH` vs `WAS`); `WAS201407070` must remain an Orioles 8–2 win.
- Use `utils/event_model.py` for PA/AB eligibility and event state. Walks, sacrifices, runner-only events and catcher interference are not AB; a strikeout with a simultaneous steal remains an AB/K. Never infer hits from the word "double" inside "double play".
- BREF pre-play scores are **batting-team first**, so reverse bottom-half scores into canonical away/home order. Legacy MLB API `outs_before` is actually post-play outs. Old Gameday supplemental plays can be appended out of order; withhold inferred state for that tail instead of inheriting the final score.
- Resolve play identities against the same game's participants and side, retaining unresolved/ambiguous cases. Head-to-head rates require actual PA events with both IDs; co-appearances are a separate feature.
- OBP uses `(H + BB + HBP) / (AB + BB + HBP + SF)`; SH is excluded. Carry SF/SH through both aggregated and per-game rows.
- New analysis libraries must be declared in `passportKeysForRoute`. Career-share numerators are regular-season only; withhold stale/undersized denominators and recalculate verified percentages when Browse scope changes. Sibling appearance journeys use stable cross-project IDs, never names alone.
- Physical-park filtering uses `_venueKey`; era filtering deliberately uses the original venue name. Modern display aliases do not imply merging historical franchises such as OAK/ATH or MON/WSH.
- The planner must use `venueIdentity` for visited parks, pinned park goals, and schedule recommendations. Exact display-name comparison mislabels Alfredo Harp Helú Stadium / Estadio Alfredo Harp Helu as unvisited. Fold accents and explicit aliases, preserving separate physical parks (e.g. the old and new Yankee Stadium).
- Next Visit has three fixed lifetime goals: Orioles at all 30 current MLB home parks, Orioles with Dad at those parks, and any teams with Dad at those parks. The shared Orioles/Dad goal requires both on the same attended game, never an intersection of two independently visited-park sets. Use `_companions` / `companionData.gameCompanions` for Dad; former, international and spring parks are separate from the 30-park denominator. Planned itineraries do not count as attendance.
- Journal and its dependent Trips tool are retired. Old journal links redirect to Next Visit. Private backups live in Saved Views; keep legacy notes/images compatible in backups without reintroducing their UI or deleting existing browser data.
- Trip costs, ratings and itinerary entries remain private browser data and private backups. Validate imports before writing; never serialize them into the public archive.

## Do NOT
- Create duplicate nested directories like `baseball_processor/baseball_processor/`
- Use `python` command (always `python3`)
- Scrape Baseball Reference faster than 3.1s between requests
- Remove milestone types from MILESTONE_KEYS without also adding them to ALL_DETECTION_KEYS (causes KeyError)
- Assume game IDs have the same format for BREF vs API games (different prefixes)
- Put unbounded BREF suffix/page walks in normal processing; use `bref_id_backfill` for explicit paced repairs
- Accumulate or sort innings pitched in React as ordinary decimal innings; use outs/baseball-IP helpers instead
- Credit SB/CS from play-by-play `batter` text; use BREF batting `Details` or direct MLB API row stats instead
