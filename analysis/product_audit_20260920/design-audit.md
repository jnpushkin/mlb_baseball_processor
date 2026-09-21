# Full design and aesthetic audit

Reviewed September 20–21, 2026. This dedicated visual review extends the original sampled product audit. It covers all ten primary sections at desktop and phone widths, with additional light/dark theme and interaction checks. The implemented direction is a personal baseball passport: a clear recent-game story, readable statistical detail, and visible collection progress.

## Overall assessment

The original site had strong content but an uneven hierarchy. Dense totals, stacked filters, colorful panels, and nested navigation competed for attention. Several phone views preserved data presentation while losing sorting or complete detail access. Small, pale labels and inconsistent dark-mode treatments made the density more difficult to read.

The revised design gives the home page a clear starting point, uses compact contextual controls, and keeps detailed analysis available through progressive disclosure. Team marks and baseball-specific collections supply identity. A restrained navy recap, consistent panels, and clearer action states provide continuity across the existing sections.

This is a comprehensive design review of the product's primary surfaces, not a claim that every combination of filters, historical records, device, and assistive technology has been exhaustively tested.

## Findings and changes

| Area | Finding | Implemented response |
| --- | --- | --- |
| First impression | Lifetime totals dominated before the visitor could find a recent game or next action. | A navy latest-game hero shows teams, final score, date, venue, and direct recap/memory actions. Compact metrics follow it; detailed charts are expandable. |
| Information hierarchy | Collection-related tools were dispersed among Players, Progress, Venues, and Frivolities. | A collection hub presents pinned goals and completion progress, linking to existing detailed tools. Home surfaces nearly complete sets. |
| Navigation | Main tabs, grouped subtabs, and detail overlays did not reliably preserve context. | URL-backed sections, filters, entities, and search; working Back paths; active navigation states; a compact phone selector for passport tools. |
| Typography | Many useful labels were only 10–11px, with pale secondary text. | Supporting text generally moves to at least 12px, body text to 14px, and phone inputs to 16px. Secondary text and pagination use theme-aware colors. Numeric tables retain aligned, unwrapped values. |
| Color and contrast | Multiple light gradients and vivid headers competed; some colors failed visually in dark mode. | Shared semantic panel, input, button, and active-state styles; supported dark gradients; stronger secondary text and green/orange text; darker Orioles headers and readable metric cells. |
| Spacing and density | Long filter stacks pushed game results down the phone screen. | Collapsible filters and a compact scope bar put results earlier. Dense analysis is optional. Table pagination removes long nested vertical scrolling. |
| Tables and cards | Desktop header sorting vanished with phone cards; cards omitted less common statistics. | Visible sort/direction controls, complete-stat disclosures, 50-row player pagination, and umpire cards. Desktop tables keep intentional internal horizontal scrolling when necessary. |
| Buttons and states | Small targets, uneven focus treatments, and unclear saved/error feedback complicated interaction. | Shared buttons and inputs, larger touch targets, visible keyboard focus, explicit save confirmation, section retry/reload controls, and separate job outcome messages. |
| Dialogs | Overlays could leave keyboard focus behind them and did not close consistently. | Shared named dialogs with initial focus, containment, Escape, focus restoration, and scrolling behavior. |
| Empty and unavailable data | Missing optional payloads could hide a section or look like a complete absence of records. | Section-level loading/retry states, coverage explanations, and saved-offline/unavailable-game states. |
| Motion | Animation and interaction polish lacked a common reduced-motion treatment. | Shared reduced-motion CSS respects the operating-system preference. |
| Print and sharing | The archive lacked a concise personal summary suited to sharing. | A season recap with shareable scope and print styling for browser Save as PDF. |

## Surface-by-surface review

| Surface | Visual and usability checks | Result |
| --- | --- | --- |
| Dashboard | Recent-game hierarchy, action prominence, compact metrics, expandable analysis, tool navigation, dark theme | Revised hero and clearer section hierarchy; phone tool selector avoids a crowded second navigation row. |
| Games | Filter stack, result visibility, cards, detail dialog, score hierarchy | Compact filters, visible actions, complete detail access, and stable copied game URLs. |
| Players | Hitters/pitchers, awards, All-Stars, dense columns, phone sorting and full statistics | Paginated tables/cards with persistent controls; internal profiles remain the primary name destination. |
| Milestones | Event hierarchy, game context, filters, tabs | Shared scope and controls; URL-backed grouped navigation retains the selected view. |
| Venues | Map/table hierarchy, calendar/weather navigation, cards, dark surfaces | Existing map retained; Back restores the default map after leaving Weather. |
| Progress | Division checklist, badges, matchups, completion hierarchy | Existing trackers remain available; collection hub provides a common starting point and goals. |
| Special | Record summary, debuts, final games, signature home runs | Record scope explicitly states regular season plus postseason; cumulative metric grids adapt to phone widths. |
| Frivolities | Jersey numbers, draft/origin tools, grouped controls, umpire tracker | Responsive shared patterns; umpires now have phone cards and accessible sorting. |
| Companions | Summary cards, group comparison, filtering, phone layout | Existing shared records remain available alongside private journal companion fields and comparison tools. |
| Orioles | Orange header contrast, metric readability, cards, phone density | Darker orange treatment and stronger metric contrast preserve team identity. |

Additional new surfaces reviewed: Recap, Collections, Journal, Next Visit, Compare, Data Health, Saved Views, and search results. These use the same panel, control, empty-state, and mobile navigation conventions.

## Observed verification

- All ten primary sections were reviewed on desktop and in a phone-width sweep. In the final sweep, the browser's actual CSS viewport was 390px wide; document width was 384px in each primary section, with no page-level horizontal overflow or error boundary.
- Light-theme screenshots covered the primary sections and representative detail views. Dark-theme review covered the home page, dense player statistics, collections, comparisons, recap, and phone umpire cards. This was not a full Cartesian test of every subview in both themes.
- Mobile hitter sorting by HR produced the expected leader; full-stat expansion preserved access to omitted columns. Umpire cards included sorting controls.
- Keyboard review exercised dialog focus containment, Escape, and return focus. Search-to-player-to-game and Back navigation preserved the exploration trail.
- Phone result visibility improved after collapsing filters; in one 433px CSS-width check the first game action was at approximately y=676–716, within the initial viewport. This is a layout observation for that viewport, not a universal device guarantee.
- Desktop history checks confirmed that Back restored Stadium Map from Weather and Hitters from Pitchers.

## Practical limits and future measurement

No formal WCAG certification, screen-reader session, physical iOS/Android test, or throttled-device performance benchmark was performed. Contrast was improved through theme tokens and visual inspection; every rendered color pairing has not been instrumentally certified. Print styling is implemented, but printer-specific pagination has not been exhaustively checked.

The remaining design opportunities are evidence-gathering tasks: observe a first-time visitor finding a specific game and collection, test VoiceOver/NVDA and real touch devices, and measure first useful content under a representative mobile connection. Those checks should guide subsequent polish; they do not conceal known unfinished items in this implementation.

See [complete delivery and verification](full-delivery.md) for the functional changes and release evidence, and [the original audit](README.md) for the baseline findings.
