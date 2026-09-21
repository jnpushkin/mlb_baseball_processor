# Functionality audit and expansion roadmap

Reviewed September 21, 2026 against main at `cf4a3c2e54e99e99e574fa1b9e9a63c324163e08`, the current generated archive, and the live website. This is the original audit and proposed backlog. Subsequent implementation and verification are recorded in [the release report](functionality_release_20260921.md).

The best next investment is a reliable shared statistical/event model, followed by tools that answer questions across games. Much of the necessary data is already collected. Adding more isolated leaderboards would deliver less value than connecting games, players, moments, and career context.

## What already exists

The site already includes player profiles and timelines; hitting/pitching leaders; WPA; RISP, two-out, and late/close splits; defensive statistics; batting-order analysis; six Statcast leaderboards; a six-dataset stat explorer; career firsts/lasts/highs; all-time passings; awards and All-Star checklists; draft, jersey, origins, birthdays, umpire and ABS data; scorigami; home/away and inning analysis; venue and matchup progress; recaps; comparison views; a private journal; saved views/goals; an initial schedule planner; offline game recaps; and Data Health.

Walk-offs, immaculate innings, grand slams, pinch-hit home runs, biggest comeback, and many other rare events already have detection or record-book coverage. These should be connected and made easier to explore, not presented as entirely new features.

## Fix before expanding

### 1. Team identity affects results, not just labels — high priority

The live Orioles opponent tables display `NYN`, `NYA`, `SFN`, `LAN`, and other source-style codes. The shared tracking normalizer deliberately returns these codes, and display components print them directly.

There is also a confirmed calculation error. For `WAS201407070`, the game has `homeTeam: WSH`, score text `BAL 8 - 2 WAS (11)`, and numeric linescore BAL 8, Washington 2. The Orioles score parser interprets the unmatched `WAS` label as evidence to swap the scores. The live Orioles summary therefore shows **65–56, 641 runs scored, 611 allowed**. The numeric linescores and existing team summary agree on **66–55, 647 scored, 605 allowed**. This is the same 121-game population.

That parser also disagrees with the linescores for three other Washington home games if applied across the archive; only the Orioles game contributes to this particular dashboard.

Recommended change: separate immutable source IDs, franchise identity, era-specific team identity, and display abbreviation. Use numeric scores for results everywhere. Display NYM consistently while retaining source IDs such as `NYN202609140`. Treat OAK/ATH and MON/Washington as explicit historical/franchise grouping choices. The retained normalization branch addresses parity-report matching, but does not solve all these website issues.

Evidence: [Orioles parsing and aggregation](/Users/jeremypushkin/mlb_processor/baseball_processor/website/react_chunks/game_details.py:617), [tracking normalizer](/Users/jeremypushkin/mlb_processor/baseball_processor/website/react_chunks/dashboard.py:1896).

### 2. Correct rate denominators and event classification — high priority

The situational tracker identifies events using description substrings. A direct isolated reproduction produced `RISP AB=1` for a walk and `RISP H=1` for a ground-ball double play. A real cached example includes Bryce Harper's ninth-inning intentional walk with a runner on second on July 7, 2014. Walks must not increase AB. See [MLB's at-bat definition](https://www.mlb.com/glossary/standard-stats/at-bat).

The shared React hitter aggregation and Python player aggregation divide OBP's numerator by all PA. Sacrifice bunts should be excluded from that denominator. See [MLB's OBP definition](https://www.mlb.com/glossary/standard-stats/on-base-percentage). A current cached example is Luis Arraez on June 26, 2026: 3 AB, 1 H, 1 BB, 1 SH, 5 PA. The current aggregation computes .400; the appropriate OBP for that line is .500. The website's player-game rows omit SF/SH, so the fix needs to carry those fields through serialization as well as change the formula. OPS inherits OBP errors.

Before adding new splits, normalize PA versus non-PA events, AB eligibility, hit types, outs before/after, bases before/after, and score before/after. BREF raw plays and MLB API raw plays currently expose different fields and semantics. In particular, some API rows called `outs_before` contain the final out count; the first lineout in `NYA202606030` has 1. Do not blindly treat that label as pre-play state.

Evidence: [situational classification](/Users/jeremypushkin/mlb_processor/baseball_processor/processors/situational_hitting_tracker.py:103), [React rate calculation](/Users/jeremypushkin/mlb_processor/baseball_processor/website/react_chunks/core_foundation.py:128), [Python rate calculation](/Users/jeremypushkin/mlb_processor/baseball_processor/processors/player_stats_processor.py:366), [API play parsing](/Users/jeremypushkin/mlb_processor/baseball_processor/parsers/mlb_api_parser.py:1529).

### 3. Make filter behavior consistent — medium priority

In the live Explorer, selecting Games and opponent WSH leaves **296 of 296 games**, including BAL @ NYM. There are only 16 games involving WSH in the archive. The Games dataset does not apply the visible opponent control. Define its meaning for Games/Teams, or disable it with an explanation when no team perspective is selected.

Shared venue filters also match raw names while park totals use canonical identities. Selecting Oracle Park returns its 101 named games and excludes 7 AT&T Park games at the same physical park. Offer a default physical-park filter with an optional historical-name/era filter. Apply the same distinction to Compare and saved views.

Evidence: [Explorer filters](/Users/jeremypushkin/mlb_processor/baseball_processor/website/react_chunks/explorer.py:54), [shared scope](/Users/jeremypushkin/mlb_processor/baseball_processor/website/react_chunks/passport.jsx:65).

## Available data and constraints

Counts were measured from `data.json` and its current manifest-referenced libraries/game files, avoiding stale generated files.

| Resource | Current availability | Implication |
| --- | --- | --- |
| Games | 296: 286 regular, 2 postseason, 8 spring | Every result needs explicit game-type scope. |
| Player-game rows | 6,175 batting; 2,499 pitching | Many useful rates and compound queries need no new network source. |
| Play-by-play | 22,984 serialized events across 296 games | Presence does not establish complete or consistently defined event data. |
| Play identities | Both batter and pitcher IDs on 3,834 events; some present in 51 games; every row covered in 48 | Resolve older names against that game's participants, preserve unresolved cases, and report coverage before publishing head-to-head rates. |
| Pitch measurements | 276 games | Existing per-pitcher totals/type counts support pitch-mix comparisons; they do not supply full location or swing-result distributions. |
| Exit-velocity measurements | 221 games | Player-game summaries support personal extremes. Full contact distributions need individual batted balls. |
| Career totals cache | 2,366 entries contain `career_totals_api` out of 2,454 cache entries | A useful starting point for career-share features, after freshness and identity checks; not proof of complete current career coverage. |

The serialized play model omits base state and play-level WPA. No new win-probability chart, leverage metric, or situational rate should silently infer these from incomplete fields. Missing measurements should remain missing, rather than zero.

## Recommended features

Effort is relative: Small means mostly existing-data calculations/UI; Medium requires a shared model or several connected views; Large includes substantial enrichment or new persistence. These are scope assessments, not delivery-time promises.

| Priority | Addition | What it would answer or enable | Data / effort |
| --- | --- | --- | --- |
| 1 | **Cross-game play explorer** | Find every grand slam, two-out extra-base hit, pinch-hit appearance, or scoring play in a selected set of games. Open the exact inning/play. Save and export results. | Existing raw plays plus normalized events and identities. Medium. |
| 2 | **Batter vs. pitcher history witnessed** | “Which hitters have I seen face Logan Webb most?” PA, AB, hits, HR, BB, K and the individual encounters. Also show player pairs who appeared in the same games as a separate concept. | Same event foundation; never infer a matchup from mere co-appearance. Medium. |
| 3 | **Compound stat queries** | “Starts with 8+ K and no walks,” “3+ hits and a stolen base,” “one-run games with 4+ HR.” Add multiple conditions, custom columns, saved query definitions and shareable URLs. | Extend existing Explorer, rather than add another table product. Small–Medium. |
| 4 | **Career share and career-stage context** | Percentage of a player's career hits, HR, starts or innings personally witnessed; age and career stage at each visit; first seen before an award-winning season; then-versus-now totals. | Existing career cache is promising; require as-of dates, matching season types, fresh denominators and stable IDs. Medium. |
| 5 | **Ranked game stories and timelines** | All comeback wins, blown leads, late lead changes, walk-off types, and longest scoreless stretches. An inning timeline explains why a game ranks highly. | Start with linescore-based measures and label their resolution; play-level changes need normalized events. Existing record-book maxima become entry points. Medium. |
| 6 | **More useful rate stats and splits** | ISO, hitter K%/BB%, SB success%, pitcher K/9 and BB/9; ahead/tied/behind performance and starter/reliever or first/return-visit splits. | Most counts already exist. Expose denominators/minimums. BABIP needs SF; pitcher K% needs batters faced; repair the foundation first. Small–Medium. |
| 7 | **Ranked multi-goal visit planner** | Rank games across a date range by missing players, teams, parks and collections; explain each match; group a multi-park trip and export an itinerary/calendar. | Extend current roster lookup and single-date planner. Batch/cache schedule and roster reads; distinguish probable pitchers/confirmed lineups from merely rostered players. Medium. |
| 8 | **Personal milestone feed** | “Your 100th game at this park,” “first time seeing this player with a new team,” “your longest gap between visits,” and next achievable personal marks. | Build on existing badges, first-seen IDs and recap; make progression chronological and backfill-safe. Small–Medium. |
| 9 | **Pitch arsenal and contact profiles** | Pitch-mix share across attended starts; velocity trends by pitcher; ultimately pitch location, contact quality and spray views. | Pitch-type counts exist. Pitch-level velocity/location/swing and individual contact data require enrichment and separate coverage denominators. Medium for mix; Large for full profiles. |
| 10 | **Historical game context** | Team records/standings entering that day, where players were in their careers, and which participants later won awards that season. | Awards/bios provide a start. Historical standings and season-to-date lines need a verified dated source/cache. Separate information known that day from later outcomes. Medium–Large. |
| 11 | **Actionable Data Health** | Click a coverage count to see affected games/players; inspect old/new values and provenance; queue a targeted repair on the local server. | Extend current summary, parity reports and add-game jobs. Public static site should link to repair guidance; privileged repairs belong to the local server. Medium. |
| 12 | **Trips and richer journal records** | Group games into road trips; record ticket cost, personal rating, seat notes and ticket images; recap a trip with optional cost totals. | Extend existing private journal and backup schema. Keep personal fields out of public exports unless explicitly selected. Medium. |
| 13 | **Unified NCAA/MiLB/MLB player journey** | “I saw this player in college, then the minors, then MLB,” with chronological appearances and links across projects. | Existing cross-reference is the starting point; requires sibling appearance histories, compatible IDs and deduplication, not merely a school affiliation. Medium–Large. |
| 14 | **Personal baseball trivia** | Generate questions from the archive: first player seen, most-watched pitcher, games shared by two players, venue/score challenges. Every answer links to evidence. | Existing normalized archive. Optional fun extension after the analysis tools. Small–Medium. |

The situational processor already has an unused `create_score_splits_dataframe` method for ahead/behind/tied statistics. That is a concrete low-cost extension after its event classification and pre-play score handling are repaired.

## Proposed delivery order and acceptance criteria

1. **Statistical foundation:** modern display codes, explicit historical grouping, canonical numeric scores, AB/OBP corrections, normalized event state, consistent filters. Acceptance: the Orioles record reconciles to 66–55; NYM is displayed while source IDs survive; the walk/double-play/sacrifice examples compute correctly; active filters either affect the selected dataset or clearly state why they cannot.
2. **Analysis release:** compound queries and added rates, then play explorer, head-to-head history and ranked game timelines. Acceptance: every result drills into its source games/plays; rates show denominators and coverage; unknown identities/events never become false zeroes; queries survive navigation and reload.
3. **Personal context release:** career share, personal milestones, historical context, and cross-level journeys. Acceptance: numerator/denominator use the same scope; reference freshness is visible; historical and retrospective statements are distinguished.
4. **Planning and memories release:** ranked date-range planner and trip journal. Acceptance: explain goal matches, show roster/lineup timestamps, preserve existing private backups, and keep personal data out of the public build.

Data Health should grow alongside each release so users can inspect the new fields' coverage and provenance.

## Features to defer

- League-relative rarity scores, expected wins, park-adjusted ratings, WAR, wRC+, or xwOBA calculated from the attended sample alone. These need proper external baselines/models and source attribution. A percentile within the personal archive can be useful if labeled that way.
- A generic conversational “ask my stats” interface before structured queries and definitions are reliable. The query engine should be the foundation for any later natural-language interface.
- Accounts/social feeds/cloud sync as the next default project. They add meaningful operational scope; the current backup system can support the nearer-term personal features.

## Verification and limits

The original audit pass used source inspection, full current-index/library/event scans, direct formula reproductions, real cached game examples, and targeted live browser checks of Orioles, Players/Statcast, and Explorer. It did not rerun the entire previous visual audit, the full test suite, or automated browser suite. No game data was re-scraped, no application fix was applied, and nothing was deployed. Proposed external enrichment sources have not been exhaustively tested; those items include a discovery step.
