# Source Parity Audit

Generated: 2026-04-30 14:01:06

## Summary

- Cache games scanned: 273
- Source groups: 6
- Duplicate date/team keys: 13
- Duplicate game IDs: 12
- Games whose stored milestone count differs from recompute: 240

## Source Groups

| Group | Games | Batters | Pitchers | Stored Milestones | Recomputed Milestones | Mismatched Games |
|---|---:|---:|---:|---:|---:|---:|
| legacy_bref_unknown | 231 | 6696 | 1915 | 418 | 1546 | 231 |
| mlb_regular | 12 | 243 | 81 | 54 | 60 | 2 |
| mlb_spring | 12 | 410 | 184 | 0 | 26 | 6 |
| pdf_spring | 2 | 0 | 0 | 0 | 0 | 0 |
| unknown_postseason | 2 | 54 | 12 | 14 | 14 | 0 |
| unknown_regular | 14 | 402 | 123 | 84 | 85 | 1 |

## Main Findings

- Found 13 duplicate date/team keys. These are the strongest practical source-parity risk because duplicate cache records can double-count games and milestones.
- Found 240 games where stored milestone counts differ from recomputation. Review `milestone_recompute_mismatches.csv` before treating cached milestone records as canonical.

## Missing Field Highlights

- `legacy_bref_unknown`: batting={'SB': 6696, '2B': 6696, '3B': 6696, 'HR': 6696}
- `unknown_postseason`: batting={'SB': 54, '2B': 54, '3B': 54, 'HR': 54}
- `unknown_regular`: batting={'SB': 402, '2B': 402, '3B': 402, 'HR': 402}

## Duplicate Date/Team Keys

| Date | Away | Home | Count | Game IDs | Groups |
|---|---|---|---:|---|---|
| 20100326 | MIN | BAL | 2 | BAL201003260, BAL201003260 | mlb_spring, pdf_spring |
| 20100327 | BOS | BAL | 2 | BAL201003270, BAL201003270 | pdf_spring, mlb_spring |
| 20250220 | CHC | LAD | 2 | LAN202502200, LAN202502200 | mlb_spring, mlb_spring |
| 20250221 | COL | ARI | 2 | ARI202502210, ARI202502210 | mlb_spring, mlb_spring |
| 20250222 | CLE | CIN | 2 | CIN202502220, CIN202502220 | mlb_spring, mlb_spring |
| 20250223 | ARI | SEA | 2 | SEA202502230, SEA202502230 | mlb_spring, mlb_spring |
| 20250524 | BAL | BOS | 2 | BOS202505241, BOS202505242 | legacy_bref_unknown, legacy_bref_unknown |
| 20260419 | CWS | ATH | 2 | ATH202604190, ATH202604190 | unknown_regular, mlb_regular |
| 20260421 | LAD | SF | 2 | SFN202604210, SFN202604210 | mlb_regular, mlb_regular |
| 20260422 | LAD | SF | 2 | SFN202604220, SFN202604220 | mlb_regular, mlb_regular |
| 20260423 | LAD | SF | 2 | SFN202604230, SFN202604230 | mlb_regular, mlb_regular |
| 20260424 | MIA | SF | 2 | SFN202604240, SFN202604240 | mlb_regular, mlb_regular |
| 20260425 | MIA | SF | 2 | SFN202604250, SFN202604250 | mlb_regular, mlb_regular |


## Refined Interpretation

- Exact duplicate `game_id` records are the clearest source-transition problem: 12 game IDs appear more than once in cache.
- Duplicate pair types: {('mlb_spring', 'mlb_spring'): 4, ('mlb_spring', 'pdf_spring'): 2, ('mlb_regular', 'unknown_regular'): 1, ('mlb_regular', 'mlb_regular'): 5}.
- The May 24, 2025 BOS doubleheader has duplicate date/team values but different game IDs, so it should not be collapsed by date/team alone.
- API-labeled rows have explicit batter `2B`, `3B`, `HR`, and `SB` fields; most legacy BREF/unknown rows do not. Legacy rows often rely on `footer_summary` and downstream fallback parsing instead. That is a normalization contract mismatch, not necessarily missing baseball data.
- Stored-vs-recomputed milestone counts are noisy because recomputation includes internal/low-tier detector categories that older cache files did not persist. Use that CSV as a backfill queue, not as proof that every legacy game is wrong.
- Implemented fix: cache-only loading now dedupes exact `game_id` aliases and keeps the richest record by batting/pitching row count, milestone count, play count, footer detail, and source quality. Do not delete cache files until the chosen records have been reviewed.
- After the loader fix, cache-only quick stats reports 261 games and skips 12 duplicate aliases.

## Duplicate Game ID Detail

- Detailed duplicate comparison: `duplicate_game_id_details.csv`

## Files

- Source summary: `source_group_summary.csv`
- Missing field detail: `missing_normalized_fields.csv`
- Milestone mismatches: `milestone_recompute_mismatches.csv`
- Duplicate date/team keys: `duplicate_date_team_keys.csv`
- Duplicate game IDs: `duplicate_game_ids.csv`
