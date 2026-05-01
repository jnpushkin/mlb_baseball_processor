# MLB Processor Todo

## Website Parity With Excel Analysis

- [Done] Add a Hall of Fame view using the existing `HOFers Seen` Excel logic.
- [Done] Add situational hitting tables:
  - [Done] RISP Performance
  - [Done] 2-Out Performance
  - [Done] RISP + 2 Outs
  - [Done] Bases Loaded
  - [Done] Late & Close
- [Done] Add the full WPA Leaders table, not just summary WPA records.
- [Done] Add defensive and lineup aggregate views:
  - [Done] Defensive Leaders
  - [Done] Lineup Analysis
  - [Done] Lineup Matrix
- [Done] Add a compact Weather & Timing table for the website.
- [Done] Once these are available on the website, treat Excel as optional/export-only via `--website-only`.

## Data Quality Follow-Ups

- [Done] Add a website data parity check that compares key Excel-only processors against serialized website JSON.
- [Done] Add a no-network regression check for cache-only and quick-stats modes.
- [Done] Keep auto-deploy as the default when `.surge-domain` is configured, but support local-only runs.

## Source Parity And API Transition

- [Done] Define and document the canonical normalized game shape consumed by processors and the website.
- [Done] Add API-vs-BREF parity checks for game metadata: date, teams, venue, score, game type, and source label.
- [Done] Add API-vs-BREF parity checks for batter lines: player ID, team, `AB`, `H`, `R`, `RBI`, `BB`, `SO`, `SB`, `2B`, `3B`, `HR`.
- [Done] Add API-vs-BREF parity checks for pitcher lines: player ID, team, `IP`, `H`, `R`, `ER`, `BB`, `SO`, `HR`, decisions, and pitch-count fields.
- [Done] Add milestone-engine tests that consume representative API, BREF, PDF, spring, regular-season, and postseason cache records.
- [Done] Make source labels explicit for legacy cache records so future audits can distinguish BREF, MLB API, PDF, and manually imported games.
- [Done] Dedupe cache loading by exact `game_id`, keeping the richest record instead of counting alias cache files twice.
- [Done] Review duplicate cache aliases after loader-level dedupe.
- [Done] Archive the 5 truly identical duplicate cache aliases after one local `--no-deploy` generation check.
- [Done] Fix duplicate selection so zero-PA pitcher batting placeholders do not make BREF aliases beat API aliases.
- [Done] Merge or explicitly select canonical data for non-identical duplicate cache aliases, especially the MLB spring `M...` enrichment aliases.

## Security And Operations

- [Done] Require an explicit flag before binding the local add-game server to LAN.
- [Done] Add token-based protection for local add-game POST requests.
- [Done] Keep phone/LAN add-game convenience, but make the trusted mode visible in startup output.
- [Done] Keep automatic Surge deploys when `.surge-domain` is configured.
- [Done] Make startup/output clearly say when auto-deploy is enabled.
- [Done] Add a `--no-deploy` escape hatch for local-only audit/backfill runs.
- [Done] Avoid network-backed reference updates during any mode advertised as cache-only, quick-stats, or DB-only.

## Testing And Tooling

- [Done] Add a formal test runner dependency and document the preferred test command.
- [Done] Add golden fixture tests for representative games across source types.
- [Done] Add serializer snapshot tests for website JSON categories and counts.
- [Done] Add regression tests for milestone category counts after backfills.
- [Done] Add lint/format config and a lightweight pre-commit check.
- [Done] Add CI or a local one-command quality gate that runs syntax checks, unit tests, and cache-only smoke tests.

## Repository Hygiene

- [Done] Remove or clearly deprecate duplicate top-level packages (`excel`, `exporters`, `reports`, `scrapers`) that diverge from `baseball_processor`.
- [Done] Keep default website outputs at the project root for auto-update/deploy compatibility, while keeping disposable scratch artifacts ignored and cleaned up.
- [Done] Keep generated cache/output files out of source commits unless they are intentional fixtures.
- [Done] Add a short data-source map describing canonical cache, DB, website JSON, Excel, and deployed website roles.

## Frontend Maintainability

- [Done] Split the large single-file React app into smaller website modules or a small frontend build step.
- [Done] Keep the current static-site deployment behavior, but make local development and review easier.
- [Done] Add website views for Excel-only analysis tables before treating Excel as export-only.
