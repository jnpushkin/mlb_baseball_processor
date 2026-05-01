# Normalized Game Shape

This is the canonical shape every parser should produce before data reaches
processors, Excel generation, or website serialization. MLB API data is the
preferred source when available, but API, BREF, PDF, and manual records should
all normalize into this same structure.

## Top-Level Contract

Every game record should be a dictionary with these top-level keys:

| Key | Required | Shape | Notes |
| --- | --- | --- | --- |
| `game_id` | Yes | string | Stable game identifier used for dedupe, cache aliases, processor links, and website drilldowns. |
| `source` | Preferred | string | Canonical source label such as `mlb`, `bref`, `pdf`, or `manual`. Also mirror this in `basic_info.source` when possible. |
| `basic_info` | Yes | object | Shared game metadata. See below. |
| `batting` | Yes | `{away: [], home: []}` | One row per batter/position player. Empty lists are better than missing keys. |
| `pitching` | Yes | `{away: [], home: []}` | One row per pitcher. Empty lists are better than missing keys. |
| `play_by_play` | Optional | list | Normalized play events. Keep `plays` as a legacy alias only when already present. |
| `lineups` | Optional | `{away: [], home: []}` | Starting lineup data when available. |
| `footer_summary` | Optional | `{away: {}, home: {}}` | Errors, doubles, triples, team totals, and source footer notes. |
| `milestone_stats` | Optional | object | Engine-generated milestone categories consumed by processors and website. |
| `pitch_data` | Optional | object/list | Pitch-level enrichment from MLB API. |
| `umpires` | Optional | list/object | Umpire names and positions. |
| `substitutions` | Optional | list | Normalized substitutions from play-by-play. |

## `basic_info`

Processors and serializers expect these fields to be stable across sources:

| Field | Required | Notes |
| --- | --- | --- |
| `date` | Yes | Display date. |
| `date_yyyymmdd` | Yes | Sortable date string. |
| `away_team`, `home_team` | Yes | Full team names when available. |
| `away_team_code`, `home_team_code` | Yes | Standardized team codes used for IDs and records. |
| `away_score_value`, `home_score_value` | Yes | Integer scores. |
| `venue` | Yes | Stadium/venue name. |
| `game_type` | Yes | One of `regular`, `postseason`, `spring`, `allstar` when known. |
| `game_type_code` | Preferred | Source-specific code such as `R`, `P`, `S`, or API game type. |
| `source` | Preferred | Same canonical source label as top-level `source`. |
| `game_pk` | Preferred for API | MLB API game primary key when available. |
| `attendance_value` | Optional | Integer attendance. |
| `start_time`, `duration`, `weather`, `temperature_f`, `wind` | Optional | Used by game log, stadium, weather, and timing views. |
| `doubleheader`, `game_number` | Optional | Needed for stable IDs on doubleheaders. |

## Batting Rows

Each row in `batting.away` and `batting.home` should include:

| Field Group | Fields |
| --- | --- |
| Identity | `name`, `player_id`, `team`, `team_code` |
| Role | `position`, `starter_pos`, `lineup_slot`, `is_starter` |
| Core batting | `AB`, `R`, `H`, `RBI`, `BB`, `SO`, `HBP`, `SF`, `SH`, `GIDP` |
| Extra-base/running | `2B`, `3B`, `HR`, `SB`, `CS`, `TB`, `XBH` |
| Fielding | `PO`, `A`, `E` |
| Advanced/source extras | `WPA`, `WPA+`, `WPA-`, `aLI`, `cWPA`, `acLI`, `RE24` when available |

Missing numeric stats should normalize to `0`, not missing values, so milestone
and website checks do not silently skip real events like stolen bases.

## Pitching Rows

Each row in `pitching.away` and `pitching.home` should include:

| Field Group | Fields |
| --- | --- |
| Identity | `name`, `player_id`, `team`, `team_code` |
| Core pitching | `IP`, `H`, `R`, `ER`, `BB`, `SO`, `HR` |
| Decisions | `decision`, `W`, `L`, `SV`, `BS`, `HLD` when available |
| Pitch counts | `pitches`, `strikes`, `batters_faced` when available |
| Advanced/source extras | `WPA`, `aLI`, `RE24` when available |

`IP` should preserve baseball innings semantics. If a parser stores it as a
string like `5.2`, downstream code must treat `.2` as two outs, not a decimal.

## Source Priority Rules

- If an API-sourced cache record and a BREF/PDF alias share the same `game_id`,
  load the richer normalized record and skip duplicate aliases.
- Do not overwrite API-sourced cache data with a later BREF parse unless the
  change is an explicit correction.
- Cache-only, DB-only, and quick-stats modes should not fetch network-backed
  reference data while building local reports.
- If a source lacks a field, keep the normalized key with an empty value or `0`
  when downstream processors depend on that key.

## Parity Check Targets

API-vs-BREF parity checks should compare these groups first:

- Metadata: date, teams, team codes, venue, score, game type, source label.
- Batter lines: player ID, team, `AB`, `H`, `R`, `RBI`, `BB`, `SO`, `SB`, `2B`, `3B`, `HR`.
- Pitcher lines: player ID, team, `IP`, `H`, `R`, `ER`, `BB`, `SO`, `HR`, decisions, pitch counts.
- Website payloads: processed row counts should match serialized JSON counts for shared datasets, and feature-only gaps should be visible.
