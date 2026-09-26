# Records design and functionality audit

Reviewed September 26, 2026 against deployed commit `d693b88`, the live Records page, and its published data files. Archive: 299 games, including 8 spring-training games; 69 displayed summary entries, including 36 record categories.

## Assessment

The current page is a useful improvement, but its structure is still too complicated. It mixes personal records, occurrence counts, and lifetime summaries. The redesign added another navigation layer and large cards before resolving inconsistencies in the underlying summaries.

Keep the game context, readable values, explicit ties, search, and keyboard-accessible dialogs. Simplify the information architecture and correct the data before adding more decorative treatments or controls.

## Confirmed findings

### 1. Inclusive milestone counts omit higher tiers — high priority

Comparison with the published non-spring player/pitcher game rows:

| Displayed category | Displayed performances | Qualifying performances | Missing from the count |
| --- | ---: | ---: | --- |
| 4+ Hit Games | 36 | 40 | Four five-hit performances |
| 5+ RBI Games | 9 | 12 | Three performances with 6–8 RBI |
| 10+ K Games | 18 | 24 | Six performances with 12+ strikeouts |

The milestone engine intentionally stores only the highest tier per performance. The summary processor counts individual tier sheets as if they were inclusive. For example, Wilmer Flores and Rafael Devers each appear in the eight-RBI record but are absent from the 5+ RBI count. These expected totals are derived from the site's published game rows, not a separate audit of source box scores.

Source: `baseball_processor/engines/milestone_engine.py` tiered detection and `baseball_processor/processors/summary_stats_processor.py` hitting/pitching milestone summaries.

### 2. Scope and drilldown are inconsistent — high priority

- Game extrema exclude spring training, while the Multi-HR summary includes the February 22, 2025 spring game. It displays 31 performances; the non-spring game rows contain 30.
- Quality Starts displays 237 performances without game links. The processor deliberately omits links when a pitching category exceeds 50 occurrences; the new paginated dialog removes the original reason for that restriction.
- “10+ Run Innings” gets the generic unit “games.” Units should describe the counted entity precisely.

Use one explicit scope and one underlying set of qualifying performances to produce each value, holder list, and linked-game count. Default to regular season plus postseason, with spring training clearly separate.

### 3. Too much space before the record list — high priority

At a 1280 × 720 desktop viewport, the first ordinary record card began approximately 938 pixels down the document. At a 390 × 844 phone viewport it began approximately 1,404 pixels down. The spotlight is visible earlier, but browsing the record collection requires considerable scrolling.

The page stacks app navigation, Special navigation, a large title panel, four view buttons, a large spotlight, and a filter panel. The two blue panels compete for attention. Repeated category labels, explanatory text, borders, and action labels make the record cards feel repetitive.

The intended two-line descriptions are ineffective in the live layout. “Most Combined Walks” rendered about 182 pixels of description text and a 467-pixel card. The default mobile document measured roughly 14,230 pixels tall. No horizontal overflow was observed in that phone-width check.

### 4. Search changes context unexpectedly — medium priority

- Typing a search automatically selects Everything. Clearing the text leaves Everything selected instead of restoring Records.
- A Camden search can display the Most Combined Walks card with Oracle Park as its prominent game context: the search matches an older holder, while the card always features the latest holder.
- Clear filters also resets ordering and the selected view.

Search should preserve the selected scope and show which holder matched. Broadening a search should be an explicit choice.

### 5. Record details separate facts from their games — medium priority

The dialog lists games, but supporting record notes are separate and sometimes collapsed. A game row should show the relevant player/team and achievement alongside its date, opponent, and venue.

Opening a game closes the record dialog. Closing the game returns to the list, losing the record's related-game search and selection context. The game has a shareable URL; the selected record does not.

### 6. Essential record categories and history are missing — medium priority

The page includes pitches thrown and pitchers used but lacks individual-game records for hits, home runs, and pitching strikeouts. Published non-spring rows already support five hits, Wilmer Flores's three home runs, and Yusei Kikuchi's 13 strikeouts.

Only current extrema and their ties are stored. The latest-holder spotlight cannot establish whether that game broke a record or tied one. There are no runners-up, record progressions, or explanations of how close other games came.

### 7. The data model constrains the design

Record categories and units are inferred from English titles. Details and game IDs are separate flat strings; their positions cannot safely be assumed to match. New titles fall back to a generic coverage category.

Use stable record IDs, explicit category/unit/direction/scope, and structured holders containing game ID, player/team, value, and achievement context. Keep participant counts separate from unique-game counts. This supports trustworthy filtering, rankings, history, and navigation.

## Recommended design

1. A compact “Personal records” heading with a clear scope line.
2. One small recent-record callout, labeled “New record” or “Tied record” only when history establishes that distinction.
3. Four category choices: Games, Batting, Pitching, Ballpark. Search and sort share one compact toolbar; advanced scope filters are secondary.
4. Compact record rows with label, value, holder, date, and tie count. On phones, use short stacked cards. Keep large cards for a few featured achievements.
5. A record detail panel that pairs every achievement with its game, offers top-five performances and history, and preserves context when opening and returning from a game. Make selected records linkable.
6. Move occurrence counts to Milestones and lifetime totals/averages to Dashboard. Retain the information without requiring an Everything view inside Records.

Highest-value future filters are season, team, ballpark, and companion. “Orioles games,” “With Dad,” and “Orioles with Dad” directly connect records to the user's interests. Filtering must recompute the record from qualifying games, rather than merely finding lifetime record holders whose text matches.

## Suggested delivery order

1. Correct threshold counts, game-type scope, units, and missing game links; add regression checks against actual qualifying performance rows.
2. Reduce navigation and vertical space; fix ineffective text clipping and search behavior.
3. Introduce structured holders, missing individual records, and return-to-record navigation.
4. Add top-five lists, historical progression, shareable record links, and personal scope filters.

The initial audit changed documentation only. Existing automated tests from the prior implementation did not cover these scenarios.

## Implementation following approval

The approved follow-up implements the four-category record book, compact rows, recomputed personal and advanced game scopes, structured holders, top-five rankings (including ties), record progression, shareable record links, and returning from a game without losing record context. It preserves all 36 prior record values and adds six individual records, for 42 categories. Totals and averages move to Dashboard; occurrence counts move to Milestones.

Threshold counts now include higher tiers and share the same eligible performances as their game links: 40 four-plus-hit performances, 12 five-plus-RBI performances, 30 multi-HR performances, and 24 ten-plus-strikeout performances. Quality Starts has links to 182 games containing 236 eligible performances; its prior 237 count included spring training.

WPA is explicitly limited to the saved lifetime record because full per-game WPA data is unavailable. It does not offer misleading scoped rankings or historical progression. Other records report how many games in the selected scope have the relevant data.

Regression coverage now includes threshold inclusion, spring exclusions, duplicate performances, doubleheaders, missing data, fifth-place ties, scoped recalculation, chronology, shared links, return navigation, and responsive layouts. The implementation retains outs as the innings-pitched representation and separates event/performance counts from unique-game counts.
