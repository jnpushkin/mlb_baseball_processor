# Duplicate Cache Alias Review

Generated: 2026-04-30

## Summary

- Duplicate exact `game_id` groups reviewed: 12
- Duplicate cache files involved: 24
- Truly identical aliases archived after review: 5
- Non-identical groups now merged at loader level: 7
- Current loader impact after archive: cache-only loading reports 261 games with 7 duplicate aliases merged/skipped.
- Loader update after review: duplicate scoring now counts meaningful batting lines only, so zero-PA placeholders no longer make a BREF/PDF-style alias look richer than an API alias. When aliases differ, the loader keeps the better canonical record and merges missing enrichment, milestone, and unique play-by-play details from the other alias.

## Recommendation

The five identical short aliases were moved to `analysis/duplicate_cache_alias_review_20260430/archived_cache_aliases/`. Keep that archive until the next local generation and website review look stable, then the archived copies can be deleted later if desired. The seven non-identical aliases remain in cache, but cache-only loading now merges them into one in-memory game per `game_id`.

## Archived Truly Identical Aliases

These files were normalized-identical to the kept file. Archiving the short alias should not change current generated outputs.

| Game ID | Keep | Archived | Reason |
| --- | --- | --- | --- |
| `SFN202604210` | `Los_Angeles_Dodgers_vs_San_Francisco_Giants_Box_Score__April_21__2026___Baseball-Reference_com.json` | `SFN202604210.json` | Normalized JSON hash is identical. |
| `SFN202604220` | `Los_Angeles_Dodgers_vs_San_Francisco_Giants_Box_Score__April_22__2026___Baseball-Reference_com.json` | `SFN202604220.json` | Normalized JSON hash is identical. |
| `SFN202604230` | `Los_Angeles_Dodgers_vs_San_Francisco_Giants_Box_Score__April_23__2026___Baseball-Reference_com.json` | `SFN202604230.json` | Normalized JSON hash is identical. |
| `SFN202604240` | `Miami_Marlins_vs_San_Francisco_Giants_Box_Score__April_24__2026___Baseball-Reference_com.json` | `SFN202604240.json` | Normalized JSON hash is identical. |
| `SFN202604250` | `Miami_Marlins_vs_San_Francisco_Giants_Box_Score__April_25__2026___Baseball-Reference_com.json` | `SFN202604250.json` | Normalized JSON hash is identical. |

## Merged At Loader Level

These pairs carry unique information in each source. They are intentionally kept on disk for traceability, then merged in memory during cache loading.

| Game ID | Files | Why Keep Both |
| --- | --- | --- |
| `ARI202502210` | `Colorado_Rockies_vs_Arizona_Diamondbacks_Spring_Training__Friday__February_21__2025.json`; `MARI202502210.json` | Keeps the API/enrichment record. The descriptive alias has one extra zero-PA starter placeholder (`Ronaiker Palma`), which is not merged as a batting line. |
| `ATH202604190` | `CWS_vs_Athletics_Box_Score__April_19__2026___Baseball-Reference_com.json`; `MATH202604190.json` | Keeps the API batting/pitching rows, skips the BREF-shaped zero-PA batting placeholders, and merges BREF footer/milestone detail. |
| `BAL201003260` | `MBAL201003260.json`; `Minnesota_Twins_vs_Baltimore_Orioles_Spring_Training__Friday__March_26__2010.json` | Keeps the API batting/pitching rows and merges the PDF-only play-by-play event. |
| `BAL201003270` | `MBAL201003270.json`; `Boston_Red_Sox_vs_Baltimore_Orioles_Spring_Training__Saturday__March_27__2010.json` | Keeps the API batting/pitching rows and merges the PDF-only play-by-play event. |
| `CIN202502220` | `Cleveland_Guardians_vs_Cincinnati_Reds_Spring_Training__Saturday__February_22__2025.json`; `MCIN202502220.json` | Keeps the API/enrichment record. The descriptive alias has one extra zero-PA starter placeholder (`Leo Balcazar`), which is not merged as a batting line. |
| `LAN202502200` | `Chicago_Cubs_vs_Los_Angeles_Dodgers_Spring_Training__Thursday__February_20__2025.json`; `MLAD202502200.json` | Same batting/pitching rows by name and stat line; merged record preserves MLB enrichment fields from the short `M...` alias. |
| `SEA202502230` | `Arizona_Diamondbacks_vs_Seattle_Mariners_Spring_Training__Sunday__February_23__2025.json`; `MSEA202502230.json` | Same batting/pitching rows by name and stat line; merged record preserves MLB enrichment fields from the short `M...` alias. |

## Practical Next Step

Implemented source-selection/merge behavior for the seven non-identical groups. The active rule is:

- prefer API normalized stat fields for common players,
- preserve meaningful source-only player rows and footer-derived milestone details,
- skip zero-PA batting placeholders when they only appear in the secondary alias,
- preserve MLB enrichment fields from short `M...` aliases when their descriptive alias has better or equal row coverage,
- merge unique play-by-play events by stable inning/half/batter/score/description signature.
- when a BREF HTML backup is processed after an API cache exists, use the API cache by internal `game_id` and do not write a new HTML-keyed JSON alias.

Validation run:

```bash
scripts/check.sh
python3 -m baseball_processor.reports.source_parity --checks metadata
```

Future optional cleanup: if this stays stable after normal website generation, write canonical merged cache files and archive the redundant aliases. The current in-memory merge avoids changing source cache files while still protecting generated outputs.
