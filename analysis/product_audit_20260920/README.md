# MLB Game Passport: product and engineering audit

Implementation update, September 21, 2026: the complete audit delivery is implemented and live. See the [full delivery and verification](full-delivery.md) and dedicated [design and aesthetic audit](design-audit.md). All 355 release files, the release manifest, and the deployed index were verified against local hashes. The [first-delivery log](implementation.md) is retained as history. Findings below describe the original audit baseline, not the current site's unresolved backlog.

Audit date: September 20, 2026. Build reviewed: September 20, 2026 at 7:22 PM.

The highest-value next step is to make the existing depth easier to navigate, more consistent, and faster to open. The app already contains the raw material for a distinctive personal baseball archive: attended games, player histories, milestones, stadium quests, companions, and unusual collections. The next product layer should connect those facts into personal stories and useful next actions.

## Scope and evidence

- Browsed all ten primary sections, with focused checks of game details, player timelines, awards, milestones, stadiums, division progress, records, signature home runs, jersey numbers, draft picks, and umpires. Sampled wide and narrow layouts and light/dark mode. This was a broad audit with representative interaction checks, not exhaustive testing of every subview or device.
- Reviewed the React assembly, shared components, serializers, website loader, deployment flow, add-game server, and test organization.
- The generated HTML exactly matches the current source template. The live HTML, main JSON, award JSON, and all manifest-listed sidecars match local files. All 32 JSON requests returned HTTP 200.
- `python3 -m pytest -q`: **210 passed, 2 skipped, 9 subtests passed**. Ruff is not installed in the active Python environment, so lint was not run successfully. No product runtime exception surfaced in the sampled browser flows; Babel and Tailwind reported production-build warnings.
- Used isolated reproductions for processor-failure reporting, duration conversion, and Pacific-time date comparisons. Did not add games, refresh reference sources, or deploy changes.
- Current archive: **296 games** (286 regular season, 2 postseason, 8 spring), **2,655 distinct player IDs** across hitters, pitchers, and players without stats.

## Prioritized backlog

Effort is a relative estimate for implementation and verification: S is a contained fix, M spans several components, L changes a workflow or the loading architecture. Priority reflects user impact, not a promise about delivery dates.

| Priority | Work | Why it matters | Effort |
| --- | --- | --- | --- |
| P1 | Repair duration conversion and date boundaries | Displayed facts and filtered results can be wrong | S |
| P1 | Report add, build, and deploy outcomes accurately | The add-game UI can claim success after failure | S–M |
| P1 | Establish shared metric definitions and visible scope | Counts and records disagree between sections | M |
| P1 | Load the dashboard first; fetch details on demand | Every visit currently waits on the entire archive | L |
| P1 | Fix destination links, route history, and modal behavior | Core exploration loses context or opens the wrong section | M |
| P2 | Finish mobile sorting, detail access, and filter layout | Cards are readable, but important controls disappear | M |
| P2 | Make search tolerant, ranked, and comprehensive | Ordinary player-name queries can return no result | S–M |
| P2 | Add shared season/game-type context and saved views | Repeated filtering makes ordinary questions cumbersome | M–L |
| P2 | Consolidate visual hierarchy and collection discovery | Similar concepts and controls are spread across many sections | M |
| P2 | Add browser workflow checks and deployment validation | Existing tests miss the confirmed interaction failures | M |
| P3 | Build season recaps, personal memories, and next-game planning | These turn the archive into a more useful personal product | M–L each |

## Confirmed correctness and reliability findings

### 1. Duration conversion loses a minute

The dashboard shows the July 31, 2024 game as **1:54**, while the record book shows **1:55**. The June 28, 2021 game is **4:18** on the dashboard and **4:19** in the record book. This is reproducible through the serializer: converting Excel fractions `115 / 1440` and `259 / 1440` produces `1:54` and `4:18` respectively. Floating-point fractions are truncated twice.

Use integer minutes as the canonical website value, or round the total minutes once before splitting into hours and minutes. Acceptance: source duration, game recap, dashboard, records, and exports agree for these cases and minute rollover boundaries.

Evidence: [duration formatter](/Users/jeremypushkin/mlb_processor/baseball_processor/website/serializers.py:3155), [Excel conversion in the game log](/Users/jeremypushkin/mlb_processor/baseball_processor/processors/game_log_processor.py:18).

### 2. Date-only filters mix local and UTC dates

The generic table compares `new Date(row.date)` for an `MM/DD/YYYY` value against `new Date(endDate)` for an ISO date input. In `America/Los_Angeles`, September 14 midnight becomes `07:00Z` for the row and `00:00Z` for the end date. The current comparison excludes that day's game. This was reproduced in an isolated JavaScript process with that timezone; the browser session did not reproduce it under its own environment.

Compare normalized date-only strings, using the same approach as the player filters. Acceptance: inclusive start/end boundaries work in Pacific time, UTC, and a timezone east of UTC; same-day ranges and doubleheaders retain every qualifying game.

Evidence: [generic table date filtering](/Users/jeremypushkin/mlb_processor/baseball_processor/website/react_chunks/journeys.py:499).

### 3. Add-game success does not establish that processing or deployment succeeded

`add_game()` ignores the return code from `subprocess.run()`. An isolated reproduction with a processor exit code of 1 returned `(True, 'AUDIT_TEST')`. The page turns that result into “Game added and deployed!” Deployment failure also needs explicit propagation from the main pipeline, where the boolean deployment result is currently ignored at the call site.

First separate **saved**, **processed**, and **deployed** outcomes. Then give the long operation a job ID and progress states so a phone can reconnect or retry without uncertainty. The HTTP server currently runs the operation synchronously despite a comment describing a thread. A fetch failure only removes the spinner without presenting an error.

Acceptance: failed processing and failed deployment produce distinct actionable messages; a successful cache write is preserved and can be retried; success is reported only for verified completed stages.

Evidence: [processor invocation](/Users/jeremypushkin/mlb_processor/baseball_processor/server.py:117), [success toast](/Users/jeremypushkin/mlb_processor/baseball_processor/server.py:245), [synchronous handler](/Users/jeremypushkin/mlb_processor/baseball_processor/server.py:292), [deployment call](/Users/jeremypushkin/mlb_processor/baseball_processor/main.py:2333).

### 4. Metric labels hide different populations

The header says **2,655 players seen**, but the dashboard “Players” card says **1,583** because it counts hitters only. Average attendance is **30,509** on the dashboard and **30,927** in Records: the dashboard includes all games with attendance, while the record summary describes 288 games. The dashboard shows **543 milestones**, while the curated milestone view shows **1,671 events** after including career events and all-time movement. These numbers need explicit definitions even where both calculations are intentional.

The dashboard's 31 teams also includes the non-MLB spring opponent MTY; Progress correctly describes 30 MLB teams. Present “MLB teams” separately from all opponents instead of leaving the distinction implicit.

Create shared selectors or serialized summaries for unique players, game scope, event counts, and attendance coverage. Display a concise scope such as “All attended games” or “Regular season + postseason,” and a definition on demand. Acceptance: the same label means the same population everywhere; different populations have different labels.

Evidence: [dashboard player count](/Users/jeremypushkin/mlb_processor/baseball_processor/website/react_chunks/tables.py:604), [header union](/Users/jeremypushkin/mlb_processor/baseball_processor/website/react_chunks/player_views.py:334), [dashboard conditions](/Users/jeremypushkin/mlb_processor/baseball_processor/website/react_chunks/tables.py:310).

## Navigation, usability, and accessibility

### 5. Make every exploration path land precisely

- Clicking **View all** in **Recent MLB Debuts** opened **Special → Records**, not Debuts. The Final Games shortcut uses the same generic destination. Send explicit tab and subtab intents.
- Main tab changes use `history.replaceState`, so they do not create a useful Back trail. Game and player identity are not encoded in their detail URLs. Add routes for individual entities and appropriate push/replace behavior, with filter and scroll restoration.
- Player names open the local timeline in some contexts but Baseball Reference in the main player table. Use names consistently for internal profiles and a separately labeled source action for external pages.
- Several useful summary items, including Recent Games rows, are informational rather than direct entry points. Make the game itself the consistent drill-down target.

Acceptance: search → player → game → Back restores the player and then the search; opening a copied game URL opens that game; each dashboard shortcut lands in its named view.

Evidence: [dashboard shortcuts](/Users/jeremypushkin/mlb_processor/baseball_processor/website/react_chunks/tables.py:731), [history updates](/Users/jeremypushkin/mlb_processor/baseball_processor/website/react_chunks/player_views.py:66), [player links](/Users/jeremypushkin/mlb_processor/baseball_processor/website/react_chunks/core_foundation.py:282).

### 6. Use one accessible dialog implementation

Opening game details left focus on the underlying **Open** button. Its dialog had neither `aria-label` nor `aria-labelledby`. Escape left the player timeline open. The global shortcut dispatches `closeModals`, but a source search found no listener for it. Sortable table headers are clickable `<th>` elements without keyboard button controls or sort announcements.

Use shared dialog behavior for initial focus, focus containment, return focus, Escape, an accessible title, and background scroll handling. Scope arrow-key shortcuts to the relevant navigation control; the current global tab shortcut runs broadly whenever focus is outside a form field. Add explicit labels to date inputs and filters, and make sort controls keyboard operable.

Acceptance: a keyboard-only user can search, open details, traverse them, close them, and resume from the triggering control. Screen readers can identify the dialog, filter boundaries, and current sort.

Evidence: [game dialog](/Users/jeremypushkin/mlb_processor/baseball_processor/website/react_chunks/core.py:831), [global shortcuts](/Users/jeremypushkin/mlb_processor/baseball_processor/website/react_chunks/player_views.py:124), [player dialog and sorting](/Users/jeremypushkin/mlb_processor/baseball_processor/website/react_chunks/journeys.py:194).

### 7. Complete the mobile interaction model

The card layouts and phone navigation selector are useful improvements already present. Their remaining gaps are concrete:

- On a narrow phone layout, the first game **Open** action appeared more than 1,000 CSS pixels below the current viewport top after the stats banner and filter stack. Show a compact game summary, search, and a collapsible Filters button before the results; move lifetime totals into an optional summary.
- Hitter/pitcher cards hide the desktop headers that provide sorting. Add **Sort by** and direction controls outside the table, shared by both layouts.
- Hitter cards display eight selected metrics, and generic cards take only six detail columns. Provide **More stats/details** so mobile preserves access to the complete row.
- The umpire tracker still renders a wide scrolling table on phones. Adapt custom tables as well as the shared `DataTable`.
- Large player lists render every row/card inside nested scroll containers. Paginate or virtualize them, and reduce competing scroll regions.

Acceptance: game search and the first result are readily visible on a typical phone; users can sort by HR, IP, or date and reach every stat without switching to desktop.

Evidence: [player cards and full-list rendering](/Users/jeremypushkin/mlb_processor/baseball_processor/website/react_chunks/journeys.py:156), [generic mobile field limit](/Users/jeremypushkin/mlb_processor/baseball_processor/website/react_chunks/journeys.py:562), [umpire table](/Users/jeremypushkin/mlb_processor/baseball_processor/website/react_chunks/badges.py:119).

### 8. Search should recognize how people actually type

**Jose Ramirez** returned no results; **José Ramírez** returned the player. Searching **2026** returned only the first five chronological games, beginning March 23, without a way to see all game matches. The broader search already covers several entity types, so these are focused improvements to an existing capability.

Normalize accents, punctuation, Unicode forms, and common team/venue aliases. Rank exact entity matches first and recent games above older partial matches. Add result groups with “See all,” arrow/Enter selection, and searchable feature names such as “splash hits” or “umpires.” Preserve queries in a results route.

Evidence: [search implementation](/Users/jeremypushkin/mlb_processor/baseball_processor/website/react_chunks/player_views.py:153).

## Design and information architecture

The current light and dark themes provide a usable foundation. The collection headers, latest-game recap, team marks, missing-item views, and personal-record categories are worth extending. Most design effort should go into hierarchy and interaction consistency.

1. **Build the home page around three questions:** what happened last time, what changed in my collection, and what am I close to completing? Keep lifetime totals compact and move detailed charts into an expandable analysis area. Offer a season switcher and an obvious way to continue exploring.
2. **Create a collection hub.** Awards are under Players, stadium completion under Venues/Progress, and jerseys/draft picks under Frivolities. A hub can show pinned goals, nearest completions, and recent additions while preserving the detailed existing sections. Navigation currently requires knowing the difference among Milestones, Special, Progress, and Frivolities.
3. **Standardize shared components.** Use one style for page headers, section navigation, filter bars, metric cards, empty states, source links, and details buttons. A compact badge should have a consistent purpose; color should distinguish a small number of meanings. Existing supported dark-mode treatments should become semantic component styles rather than more utility-class exceptions.
4. **Increase readability.** Many secondary labels are 10–11px with light gray text. Raise useful supporting text toward 12–14px, keep critical labels legible in both themes, and preserve tabular alignment for numeric comparisons. Keep decorative accents quieter than the result or primary action.
5. **Explain the baseball meaning.** Expand abbreviations on demand, distinguish MLB firsts from firsts witnessed, and explain whether an award collection means “ever saw this winner” or “saw them in the award season.” Move implementation language, such as exact record-matching descriptions, into source details.
6. **Give summaries a visible context.** A shared season/game-type control should scope supported views; sections that intentionally show lifetime data should state that. Preserve per-table controls for detailed queries, and offer named saved views such as “2026 Giants games” or “Orioles road games with Dad.”

## Performance and architecture

### 9. Split data by when it is needed

The current HTML plus JSON files occupy **31.14 MiB uncompressed** across 33 files. The 32 live JSON responses transferred **3,161,315 bytes compressed** in this check, excluding HTML, libraries, images, fonts, and map tiles. This is not a claim that visitors download 31 MiB over the network.

The material issue is the dependency chain: the main manifest loads all 27 core sidecars, then award data and its three sidecars, before initializing the app. Every fetch adds a timestamp and uses `no-store`. The client then parses the full archive and compiles the embedded React code with Babel. The 3.3 MB uncompressed All-Star payload and eight detailed game chunks are required even for a dashboard visit.

Proposed sequence:

1. Produce a compiled frontend and static CSS during generation/build; remove browser-side Babel and Tailwind compilation.
2. Load a small dashboard/game-index payload first.
3. Fetch a game's play-by-play/pitch detail when opened; fetch award, draft, biography, and All-Star libraries when their sections are used.
4. Use a versioned manifest and content-based asset names so unchanged files are reusable and related files belong to the same build.
5. Show section-specific loading, retry, and unavailable states. Currently a core sidecar failure aborts the whole load, while award failures are caught and can silently remove the feature.

Set a representative phone/network baseline before implementation, then measure first useful content, input responsiveness, and repeat visits. No throttled device performance benchmark was run in this audit.

Evidence: [external runtime libraries](/Users/jeremypushkin/mlb_processor/baseball_processor/website/templates.py:27), [eager loading and failure handling](/Users/jeremypushkin/mlb_processor/baseball_processor/website/templates.py:403), [sidecar generation](/Users/jeremypushkin/mlb_processor/baseball_processor/website/generator.py:116).

### 10. Add visibility into data quality and releases

The repository already has useful source-parity reports, normalized-game documentation, a staging directory for deployment, and substantial Python coverage. Build on that foundation with:

- A small data-health view: source, last successful refresh, missing enrichment, unresolved identities, and corrections since the last build. For example, hit data is present in 219 of 296 serialized games; communicate coverage rather than treating every record as equally measured. Presence alone is not a completeness assessment.
- Stable metric contracts and an explicit website data schema version. Separate baseball facts from presentation-specific formatting and derived summaries.
- Browser tests for the confirmed failures and a few complete journeys: search to player to game, mobile sorting, keyboard dialogs, route restoration, and section-load failures. Several current React tests assert source strings, which does not validate rendered behavior.
- An automated release check that validates every manifest-listed file, renders a representative page, and reports build/deploy status accurately. Pin the required development tools and make the check command reproducible in CI.

Avoid a wholesale rewrite as the first project. The highest-impact fixes can be delivered incrementally around the current Python pipeline and static deployment model.

## New features worth building

| Feature | Smallest useful version | Why it fits this app | Effort |
| --- | --- | --- | --- |
| Season recap | One season page with games, new players/parks, top moments, records broken, and companion highlights; a shareable summary | Reuses the archive and gives the dashboard a stronger personal story | M |
| Game journal | Notes, seat/section, favorite moment, photos or ticket image, and companion editing with durable local storage/export | Captures the part of attendance that box scores cannot recover | M–L |
| What should I see next? | A pinned goal list and eligible active players/teams for missing collections; later add schedule matching | Jerseys, award sets, matchups, and the Orioles stadium quest already supply goals | M initially, L with schedules |
| Saved views and watchlists | Save filters, pin players/collections, reopen a named view | Reduces repeat setup and makes the breadth manageable | M |
| On this day / since my last visit | One historical game or a concise list of new collection additions | Gives a useful reason to return between games | S–M |
| Personal comparisons | Compare seasons, ballparks, or companion subsets with matching scope and sample sizes | Makes the existing data answer richer personal questions | M |
| Offline recent games | Cache the app shell, game index, and explicitly saved recaps | Useful in ballparks; best built after versioned loading | M |

For a planner, distinguish attainable active-player goals from retired players or closed venues, and distinguish scheduled appearances from confirmed participation. For a journal, keep private memories separate from the fields intentionally exported to the public site. Those are product requirements for the proposed features, not evidence of a current incident.

## Recommended order of work

**First delivery: trust and everyday usability.** Fix duration/date bugs, player labels, add-game outcome reporting, accent-insensitive search, dashboard destinations, and shared dialog behavior. Add focused regression coverage for those failures.

**Second delivery: a cohesive browsing experience.** Add mobile sorting and full detail access, compress filter stacks, introduce reliable routes/Back behavior, and align game scope across views. Add a collection landing page without losing existing tools.

**Third delivery: faster loading and a more personal product.** Compile the frontend, implement versioned/on-demand data, then ship a season recap. Follow with the game journal and goal planner according to which would be used most often.

The strongest starting project is the first delivery: it fixes demonstrated problems immediately and establishes the consistency the larger features will need.
