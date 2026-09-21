# First delivery: correctness and everyday usability

Implemented September 20, 2026 against the existing workspace, preserving its earlier changes. This is a historical first-delivery log. The remaining work described below has since shipped; see the [complete delivery](full-delivery.md) and [design audit](design-audit.md).

## Delivered

- Duration serialization rounds once to whole minutes; the dashboard now agrees with source durations of 1:55 and 4:19.
- Date filters compare normalized calendar dates with inclusive endpoints. Start and end inputs have accessible labels.
- Dashboard and header share a distinct player count across hitters, pitchers, and players without stats: 2,659 in the current cached rebuild. The dashboard distinguishes game milestones and explains spring opponents and game-condition scope. Clickable statistic cards are real buttons.
- Dashboard links open Debuts, Final Games, Game Milestones, or All-Time Passings explicitly rather than relying on the previous subtab.
- Search matches accents and punctuation consistently, presents recent game matches first, supports arrow-key selection and Enter, and transfers a broad player query to both hitter and pitcher tables. Player search results select the correct statistics view.
- All ten popup boundaries use the shared dialog component: player, pitcher, game, badge, calendar, matchup, companion, birthday, scorigami, and player-game list. It provides an accessible name, Escape dismissal, focus trapping and restoration, scroll locking, and nested-dialog ordering. Main-navigation arrows apply only within its tab list; game arrows are handled by the active dialog.
- The add-game server reports saved, built, and deployed outcomes separately. Failed processing never uploads stale artifacts. Cached games remain available for retry without refetching. The UI shows persistent errors, a Retry action, network-failure feedback, and a rebuild option for saved games.
- Processor failures now exit nonzero. Failed uploads propagate failure, and deployment refuses missing HTML, data.json, award manifests when required, or referenced JSON chunks.

## Verification

- Full suite: **223 passed, 2 skipped, 17 subtests passed**. After the final error-message wording adjustment, the focused add-game/regression suite passed again: **18 passed, 8 subtests passed**.
- JavaScript behavior tests execute the production helpers in Node, covering Pacific/UTC/Tokyo date boundaries, accented and punctuated names, game ordering without source mutation, and deduplicated player counts.
- Mocked backend tests cover parse failure, build failure, build timeout, upload failure, cache-preserving retries, and refusal to upload incomplete bundles. No test added a real game or performed a real test upload.
- Cache-only website generation completed, including the NCAA shared-player refresh from local caches.
- Browser checks on the generated site confirmed accent-insensitive search, arrow/Enter selection, both player-table query handoffs, same-day filtering, exact dashboard destinations, Escape dismissal, focus trapping, focus restoration to the original game button, and mobile dark-mode layout without horizontal overflow.
- A separate local add-game fixture exercised the actual page and HTTP handler: simulated build failure displayed an actionable error and retained the game; Retry succeeded using the saved cache. API fetching and deployment were mocked.
- Browser logs contained the existing Babel warning about compiling a script larger than 500 KB; no application runtime exceptions were observed in the checked flows.

## Live deployment

Published to https://mlb-processor.surge.sh/. Verified all 33 deployed files (HTML plus 32 JSON files): HTTP 200 and byte-identical to the local bundle. The live dashboard shows the shared player count, and an unaccented name query returns José Ramírez.

## Remaining from the audit

This delivery does not implement a persistent background-job queue, reconnectable progress, full search-results routes, team/venue aliases, browser Back/Forward improvements, mobile sorting/filter redesign, lazy data loading, build-time JavaScript compilation, or the proposed recap/memory/planning features. Those remain separate follow-up work. Add-game processing is still synchronous and retains its five-minute build timeout.
