# Functionality release — September 21, 2026

This release follows the functionality audit in `functionality_audit_20260921.md`. It adds a shared event model, corrects the confirmed statistical/filtering issues, and delivers the analysis, personal-context, and planning portions of the roadmap. The final section distinguishes the deeper capabilities that still need additional data or server integration.

## Statistical and identity corrections

- Modern team abbreviations are normalized at publication and display boundaries. Source game/player IDs remain unchanged. Browse offers explicit team-at-the-time versus franchise grouping.
- Game outcomes use numeric linescores. The 121-game Orioles archive now reconciles to **66–55, 647 runs scored, 605 allowed**.
- OBP uses AB + BB + HBP + SF; sacrifice bunts are excluded. SF/SH survive both aggregate and per-game serialization. Luis Arraez's June 26, 2026 line now yields .500 OBP.
- The normalized event model distinguishes plate appearances, AB, hits, walks, sacrifices, interference, strikeout/steal combinations, and runner-only events. It resolves player identities within the game's actual rosters and preserves uncertainty.
- BREF pre-play scores are batting-team first and are converted to away/home order. Legacy API post-play outs are no longer treated as pre-play outs. Out-of-order supplemental plays in two old spring-training feeds do not inherit final scores.
- Explorer applies its Games opponent filter. Physical park filters include naming eras: Oracle Park includes 108 games across Oracle/AT&T names.
- Planner venue matching uses explicit park identities, accent folding and aliases. **April 28, 2024, HOU 8–2 COL at Alfredo Harp Helú Stadium** is recognized as a visit to Estadio Alfredo Harp Helu. The real archive's unvisited reference list drops from 20 to 19. Every recorded venue resolves against the park reference, and old/new Yankee Stadium remain distinct.
- The retained parity normalization fixes were integrated without replacing newer main-branch backup/doubleheader handling.

## New and expanded tools

**Dashboard → Discover** contains:

1. Play explorer: batter, pitcher, event, outs and situation filters; scoring plays, extra-base hits and grand slams; CSV/JSON exports and exact-play links.
2. Witnessed batter–pitcher matchups: PA, AB, H, HR, BB, K, AVG, games and individual encounters, with identity/state coverage.
3. Shared games: co-appearances for teammates or opponents, with source games; separate from actual head-to-head encounters.
4. Game stories: ranked winning comebacks, lead changes, scoreless stretches, margins and run totals, with half-inning timelines.
5. Career share: regular-season hits, HR, SB, pitching starts and strikeouts; dated cache references, withheld stale percentages, and on-demand MLB career verification.
6. Pitch arsenals: measured pitch-type counts/shares and appearance-level velocity history.
7. Personal milestones: chronological games, parks, teams and player appearances; first sightings with a new team; record return gaps and upcoming park milestones.
8. Then & now: player ages/debut context, retrospective season awards, and on-demand standings through the preceding day.
9. Trips: private journal grouping, currency-separated ticket totals, ratings, game-date calendars and private exports.
10. Player journeys: 95 linked players across the available NCAA/MiLB/MLB appearance archives, joined by shared IDs.
11. Archive trivia with links to answer evidence.

**Players → Explorer** gains compound AND/OR conditions, selected columns, saved/shareable queries, first/return-visit and pitching-role filters, and presets including 8+ K/no-walk starts, 3+ hits/a steal, and one-run games with 4+ HR. Added rates include ISO, BABIP, K%, BB%, SB%, K/9 and BB/9.

**Dashboard → Next visit** supports a date range, ranked and explained goal/park/franchise matches, probable pitchers, a private itinerary and calendar export. Roster membership is explicitly a possibility, not confirmation of an appearance.

**Dashboard → Journal** gains trip name, rating, ticket cost and currency. Existing backups remain compatible; itinerary data is included. Validation precedes imports, and private data stays out of the public build.

**Dashboard → Data health** gains affected-game lists, normalized-event coverage, provenance and changed-field details, with exports for targeted local review.

## Verification

- Full Python suite: **245 passed, 2 skipped, 17 subtests passed**.
- Browser suite: **16 passed**, covering lazy loading, routes/Back, offline recaps, phone layouts, compound-query reloads, exact-play links, career-share rescoping, co-appearances, private backup imports, itineraries, and Mexico City venue aliases.
- Release manifest: **362 files**, checked for existence, SHA-256 integrity, and declared data dependencies.
- Current archive: **296 games, 22,984 events, 22,363 classified PA**. Both player identities resolve for **22,358 PA**. Five PA have unresolved identities; 3,834 lack reliable pre-play bases; five lack reliable pre-play scores. Missing state stays unknown.
- All 296 story timelines reconcile with final linescores. No normalized play reports negative runs scored.
- Whole-archive batting AB/H/BB/K reconciliation found only one duplicate zero-stat Shohei Ohtani two-way box-score row; actual batting totals reconcile.
- Real-browser review verified historical standings, an MLB career-total refresh, desktop/dark and phone layouts, and the corrected 19-park unvisited list.
- Cache-only regeneration used no BREF scraping. The normal shared-player export refresh ran; private browser journals were not read into the public bundle.

## Remaining deeper work

These are not presented as finished capabilities:

- Full pitch-location, swing-result, spray and contact-quality distributions require additional event-level enrichment. The new arsenal tool uses existing measured summaries.
- Data Health exports a repair list; it does not yet enqueue authenticated repair jobs on the local add-game server.
- Planner rankings use checked current rosters, probable pitchers, pinned goals and park/franchise gaps. They do not guarantee future participation or batch-refresh every historical collection entry.
- Career references and sibling appearance histories have their own refresh schedules. Live verification is available per player; the archive does not pretend all references are current.
- Stories use half-inning linescores. They are not pitch-level win-probability or leverage reconstructions. Existing specialty milestone/record views remain the source for those named events.

## Open-tab deployment repair

The 09:42 release remained open in the browser after the 11:02 deployment. Its hashed index and section URLs had been removed from the published bundle, producing 404s across Games, Players, Awards and Milestones. A fresh-load check of the current manifest did not cover this transition.

The loader now refreshes the stable index on an expired file, retries against the current paths, coalesces simultaneous refreshes and rejects late responses from the old release. Compatible loaded sections remain available; changed sections reload. The same recovery covers direct game links, saved-game downloads and expired boot indexes. Recovery preserves the route and browser storage; a browser regression also verifies that an unsaved journal draft remains mounted. Stable release pointers bypass the service-worker cache.

Bundles retain two earlier indexes and their complete data graphs, with checksums and dependency validation. This deployment explicitly restores the 09:42 index so existing tabs running the original loader can retry successfully.

Validation: **247 Python tests passed, 2 skipped, 17 subtests passed; 22 browser tests passed**, including four expired-section journeys, an expired boot index and the unsaved-draft case. Nine runtime/service-worker regressions run through the Python CI suite. Ruff and the fixture release validator passed. The rebuilt production manifest contains **681 files**, including the restored legacy dependencies.

Post-deploy verification: all 681 live files returned HTTP 200 with matching SHA-256 checksums. The live browser loaded Awards and all ten primary tabs without section errors. The original user tab was left open.

## Personalized ballpark goals

Journal and its dependent Trips tool have been removed. Old Journal links redirect to Next Visit. Private backup import/export now lives in Saved Views and preserves legacy notes/images without displaying the retired editor.

Next Visit now tracks three permanent goals across the 30 current MLB home ballparks:

- Orioles in every ballpark: **24/30**, six remaining.
- Orioles in every ballpark with Dad: **16/30**, fourteen remaining.
- Every ballpark with Dad, any teams: **23/30**, seven remaining.

Each goal has missing and completed parks, with qualifying first-visit links. Historical, international and spring training venues appear separately. Orioles-with-Dad completion requires a qualifying shared game; separate Orioles and Dad visits do not combine into completion. Stadium renames share physical identity, including Rate Field/Guaranteed Rate Field and Daikin Park/Minute Maid Park, verified against the MLB 2026 teams/venue API.

Schedule recommendations prioritize remaining park goals, support focusing on a goal and planning with/without Dad, and save that companion choice in the private itinerary. Saving a planned visit does not affect completion. Existing generic player/team/collection goals remain in a collapsed watchlist.

Validation includes 23 passing browser journeys, the Python/Node regression suite, release checksums/dependencies, and a visual review using the full local archive. New regression cases cover same-game Dad/Orioles matching, historical-versus-current venues, renamed parks, goal-specific recommendations, private itinerary imports, retired links, and phone layout.

## Companion corrections and browser editor

The May 28, 2016 Orioles game at Progressive Field already listed Dad, but its companion ID contained a nonbreaking space and a spreadsheet `.00` suffix. A later canonical blank row hid the join failure. The September 14, 2026 Orioles game at Citi Field had a blank companion entry; Dad has been added following the user's correction. The same ID repair recovered Charles's May 5, 2019 Cleveland record. Duplicate rows were merged without dropping companion names; the original CSV was backed up.

The corrected live totals are **24/30 Orioles parks**, **18/30 Orioles parks with Dad**, and **24/30 parks with Dad**. Dad now has 85 recorded games. Companion joins and automatic CSV synchronization share ID normalization that preserves API/BREF prefixes and doubleheader numbers.

The authenticated local manager now includes a responsive companion editor: search games, filter those without companions, select names or add a new name, and save/publish. Each edit writes the authoritative source with a recoverable backup, refreshes companion summaries, rebuilds the complete website and publishes it. Jobs share the add-game queue, report save/build/publish outcomes separately, survive browser disconnects, and reject stale revisions. Unsaved choices are protected when changing games. Links appear in Companions and Next Visit; phone access uses the existing explicit LAN mode.

Verification: **254 Python tests passed, 2 skipped, 17 subtests passed; 25 browser tests passed**. The new editor tests exercise authenticated requests, validation, normalization, backup preservation, serial jobs, failed builds, successful UI publishing, conflict handling and phone layout. The final layout and doubleheader labels were followed by 11 passing server tests and both passing editor browser tests. Ruff passed, and the production release's 366 files passed dependency/checksum validation. A real editor save completed through production deployment, the published HTML/assets/indexes/companion data matched local hashes, and a fresh live browser showed the corrected three goal totals.
