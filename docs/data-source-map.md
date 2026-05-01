# Data Source Map

This project has several data surfaces. The important rule is that processors
should consume normalized game records, while outputs should be treated as
generated views of those records.

## Canonical Inputs

| Surface | Role | Notes |
| --- | --- | --- |
| `cache/*.json` | Primary local game store | Canonical normalized game records for cache-only processing. MLB API records are preferred when duplicate `game_id` aliases exist. |
| `baseball_processor/db/` | Optional structured store | SQLite-backed copy of cache records. Useful for queries and future app workflows, but should not diverge from normalized cache shape. |
| `Current Season Games/` | New source files | Input drop zone for HTML/PDF/API-derived imports before normalization and caching. |
| `mlb_references/` | Reference data | Debuts, Hall of Fame, all-time leaders, register mappings, and other lookup data. |

## Generated Outputs

| Surface | Role | Notes |
| --- | --- | --- |
| `MLB Game Passport - BREF.xlsx` | Excel export | Rich workbook view. Treat as export-only unless a worksheet has not yet been added to the website. |
| `MLB Game Passport - BREF.html` | Local website shell | Static HTML wrapper that loads `data.json`. |
| `data.json` | Website payload | Serialized version of processed data. This should match processed row counts for shared datasets. |
| Surge deployment | Public/static website | Deployed copy of the generated HTML and JSON when `.surge-domain` is configured and `--no-deploy` is not used. |
| `analysis/` | Audit and backfill reports | Local review artifacts. Keep useful reports here instead of mixing them with source modules. |

The default website files stay at the project root on purpose because the static app fetches `data.json` beside the HTML file, and the current local review/deploy flow depends on that pairing.
The generated React source is assembled from `baseball_processor/website/react_chunks/` by `baseball_processor/website/react_app.py`; there is no separate frontend build step.

## Source Priority

1. Prefer an MLB API cache record when it has the same `game_id` as a BREF/PDF alias and comparable or richer data.
2. Keep BREF records as useful historical backups and source-comparison references.
3. Keep PDF/manual records explicit, but expect thinner stat coverage.
4. Do not treat generated Excel, HTML, or `data.json` as the source of truth.

## Local Checks

- `scripts/check.sh` runs syntax checks, unit tests, and a cache-only quick-stats smoke test.
- `python3 -m baseball_processor.reports.source_parity --checks all` compares local API/non-API cache aliases without network access.
- `python3 -m baseball_processor --quick-stats --from-cache-only --skip-debut-update --no-emoji` verifies the current cache can produce the expected local summary.
