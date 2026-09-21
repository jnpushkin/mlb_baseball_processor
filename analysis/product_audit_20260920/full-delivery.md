# Complete audit delivery

Implementation completed September 21, 2026. This delivery addresses the remaining product, usability, design, loading, and feature work identified in the original audit. The first delivery's correctness fixes remain in place.

See the dedicated [design and aesthetic audit](design-audit.md), [original findings](README.md), and [first-delivery record](implementation.md).

## What changed

### A coherent browsing experience

- A new home page centers the latest game, changes since the last visit, nearby collection completions, anniversary memories, and recent games. Detailed analysis is expandable.
- Shared season, game-type, team, venue, companion, and home/away scope applies to supported views. Lifetime sections and the record book state their own populations explicitly.
- Named saved views restore shared filters and saved table preferences. Player, collection, team, and ballpark goals can be pinned.
- Sections, subtabs, query scope, players, and games have URL-backed navigation. Copied game links load directly. Back returns from a game to a player and then to the previous search, and restores default subtabs correctly.
- Search normalizes accents and aliases, supports keyboard selection, offers complete paginated results by type, and includes milestone events and feature destinations.
- Player names consistently open internal profiles, with external source links separately available.

### Design, mobile, and accessibility

- A clear recent-game hero, shared panels and controls, more legible supporting text, consistent focus states, improved dark themes, and stronger Orioles contrast.
- Collapsible filters and compact phone navigation reduce the space before useful results.
- Mobile sort controls, all-stat/detail disclosures, player pagination, and umpire cards preserve the functionality of desktop tables.
- Shared dialogs provide accessible titles, focus containment, Escape dismissal, and return focus. Table sorting uses keyboard-operable controls with sort state.
- Reduced-motion styling and recap print styles are included.

### Personal features

- **Recap:** scoped games, first-seen players and parks, home-run highlights, record-breaking performances, memorable events, and companion highlights; shareable URLs and browser print/Save as PDF.
- **Journal:** private notes, seat/section, companions, favorite moments, and local PNG/JPEG/WebP photos. Text is stored in the browser and photos in IndexedDB. Explicit save feedback, export, validated import, and merge behavior protect existing entries.
- **Collections:** one landing page for 191 award collection sets plus links to venue, All-Star, jersey, and draft trackers; visible progress and pinned goals.
- **Next Visit:** goal pins, missing teams/parks, collection candidates, on-demand active MLB roster checks, and date-based schedule matching. Ambiguous names expose candidate IDs; a roster or schedule match is not described as a guaranteed appearance.
- **Compare:** seasons, venues, and companion groups with matching game-type scope, sample sizes, rates, and attendance coverage.
- **Offline:** explicitly save game recaps and the application shell/index, reopen saved games without the server, and remove saved copies. Unsaved sections show an actionable unavailable state.
- **Data Health:** source counts, reference refresh dates, measured enrichment coverage, noncanonical identity counts, metric definitions, and changed game records. Updated data may reflect enrichment or correction; the app does not label every change as an official scoring correction.

Private journal entries, photos, saved views, and goal pins are device/browser-local and are not included in the public site deployment. Export is the portable backup; this delivery does not add account-based synchronization. Journal companion edits are personal annotations and do not rewrite the shared source archive.

### Loading and release architecture

- React and CSS compile during generation. The published page no longer compiles Babel or Tailwind in the visitor's browser.
- A lean game/dashboard index loads first. Individual game details and section libraries load on demand, with section-specific loading and retry/reload controls.
- Schema version 2 uses content-hashed data and assets. Each game detail includes the information needed for a cold direct link or saved offline recap.
- A release manifest lists all required files with sizes and SHA-256 hashes. Deployment validates and stages the complete manifest, including Leaflet images, the service worker, compiled assets, and every JSON dependency.
- Add-game processing uses persistent jobs, a single background worker, duplicate-active-job protection, polling/reconnection, and interruption recovery. The interface distinguishes saved, processed, and deployed outcomes.
- Dependency versions, focused Python checks, a synthetic browser fixture, eight Playwright journeys, and a GitHub Actions workflow are checked in.

## Correctness fixes found during implementation

- Canonical first-seen IDs now derive chronologically from normalized appearances. Legacy cached aliases had inflated recap totals; the recap now agrees with the union of hitters, pitchers, and appearances without statistics.
- Velocity coverage requires an actual positive measurement, rather than a nonempty object whose values may be absent.
- Direct and offline game dialogs use their own detail payload instead of assuming the global milestone library is already loaded.
- Venue, jersey, and umpire links inside game details no longer undo their navigation by subsequently closing the previous route.
- Back navigation resets default grouped subtabs, rather than leaving stale component state visible.
- “Since last visit” compares known game IDs, so newly added historical games count as additions.
- Backup validation happens before mutations. Conflicting imported notes preserve existing entries, images merge without duplicating identical files, and invalid backups leave stored memories intact.

Current archive: **296 games, 2,659 canonical players, 39 parks, and 639 home runs across all game types**. Regular-season/postseason records intentionally cover 288 games and 624 home runs. Data Health shows 245 BREF games and 51 MLB API games; 276 games have pitch velocity and 221 have exit velocity. The 77 register/placeholder batting identities are a review population, including legitimate prospects, not 77 proven errors.

## Performance evidence

The original audit measured **3,161,315 compressed bytes of JSON** before startup, excluding its HTML and external runtime libraries. The new initial HTML, index, compiled JavaScript, and CSS total **485,725 bytes when locally gzip-compressed**:

| Initial resource | Raw bytes | Local gzip bytes |
| --- | ---: | ---: |
| HTML | 16,648 | 3,885 |
| Index | 1,013,877 | 175,444 |
| JavaScript | 1,066,275 | 287,053 |
| CSS | 130,572 | 19,343 |

This is a payload-size comparison, not a measured speed multiplier. Compression settings and actual network transfer may differ. Team logos, map tiles, service-worker installation, and optional section/detail requests are outside this initial-resource subtotal. Detailed data remains available and may still be substantial when an advanced section is opened.

## Verification

- Full Python suite: **229 passed, 2 skipped, 17 subtests passed**.
- Focused post-fix regression suite: **25 passed, 8 subtests passed**.
- Ruff passed for the six new Python modules/scripts/tests; Prettier passed for new frontend and browser-test files.
- Normal cache-only website generation succeeded, including the sibling NCAA shared-player refresh from local caches.
- Local release validation passed for **355 files**, schema 2.
- Manual browser review covered all ten primary tabs on desktop and phone, representative light/dark views, search/player/game/Back, copied game links, shared scope, saved views, mobile sorting/full statistics, and keyboard dialogs.
- A synthetic fixture verified note persistence, image upload/save, successful import/export, conflict preservation, invalid-backup rejection, goal roster lookup, and schedule retrieval.
- With the fixture server stopped, an explicitly saved game reopened with its box score. An unsaved game showed Retry/Close. A failed section loaded successfully after restarting the server and selecting Retry.
- Python integration coverage exercises the actual add-game HTTP handler's 202 response, protected job endpoint, duplicate work handling, worker failures, and interrupted-job recovery.

The eight Playwright tests and CI workflow are authored and syntax-checked. Their key journeys were exercised manually through the browser, but the automated Playwright suite and hosted CI workflow have **not** been executed in this session. This report does not represent them as passing. No real game was added solely to test the job flow, and no intentionally failing production deployment was performed.

## Release status

Published to [MLB Game Passport](https://mlb-processor.surge.sh/) on September 21, 2026. **All 355 manifest-listed files returned successfully and matched local byte sizes and SHA-256 hashes.** The release manifest and deployed `index.html` also matched the local release. The machine-readable [verification record](live-verification.json) includes the UTC timestamp, manifest digest, and complete file list.

Live browser verification confirmed the redesigned dashboard and archive totals, a game recap with box scores and milestones, the same game after a direct reload, the Data Health view, and light/dark rendering. No error-level console entries appeared during those live checks. The previous live bundle was retained in a temporary local rollback directory before deployment.
