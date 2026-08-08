import json

from baseball_processor.scrapers import draft_scraper


def _draft_pick(mlb_id, name, pick_number, round_pick_number, team="Test Team", school="Test School"):
    return {
        "pickNumber": pick_number,
        "roundPickNumber": round_pick_number,
        "person": {"id": mlb_id, "fullName": name},
        "team": {"name": team, "abbreviation": team[:3].upper()},
        "school": {"name": school},
    }


def _buck_2002_payload():
    round_23 = [_draft_pick(100001, "Stray Phase Pick", 557, 1)]
    for offset, overall_pick in enumerate(range(673, 701), start=1):
        name = "Travis Buck" if overall_pick == 700 else f"Round Pick {overall_pick}"
        mlb_id = 459941 if overall_pick == 700 else 200000 + overall_pick
        round_23.append(_draft_pick(mlb_id, name, overall_pick, 116 + offset))
    return {"drafts": {"rounds": [{"round": "23", "picks": round_23}]}}


def _buck_2005_payload():
    comp_round = []
    for offset, overall_pick in enumerate(range(31, 37), start=1):
        name = "Travis Buck" if overall_pick == 36 else f"Comp Pick {overall_pick}"
        mlb_id = 459941 if overall_pick == 36 else 300000 + overall_pick
        comp_round.append(_draft_pick(mlb_id, name, overall_pick, offset, team="Athletics", school="Arizona State"))
    return {
        "drafts": {
            "rounds": [
                {"round": "1", "picks": [_draft_pick(111111, "First Pick", 1, 1)]},
                {"round": "C-1", "picks": comp_round},
                {"round": "2", "picks": [_draft_pick(222222, "Second Rounder", 49, 1)]},
            ]
        }
    }


def test_extract_picks_normalizes_historical_round_pick_numbers():
    picks = draft_scraper._extract_picks(_buck_2002_payload(), 2002)

    buck = next(p for p in picks if p["fullName"] == "Travis Buck")

    assert buck["round"] == 23
    assert buck["roundPick"] == 28
    assert buck["apiRoundPick"] == 144
    assert buck["overallPick"] == 700


def test_extract_picks_keeps_first_round_supplemental_picks():
    picks = draft_scraper._extract_picks(_buck_2005_payload(), 2005)

    buck = next(p for p in picks if p["fullName"] == "Travis Buck")

    assert buck["round"] == 1
    assert buck["rawRound"] == "C-1"
    assert buck["roundPick"] == 36
    assert buck["blockPick"] == 6
    assert buck["firstRoundPick"] == 36
    assert buck["isFirstRoundBand"] is True
    assert buck["overallPick"] == 36


def test_extract_picks_skips_implausible_first_round_phase_picks():
    payload = {
        "drafts": {
            "rounds": [
                {
                    "round": "1",
                    "picks": [
                        _draft_pick(111111, "Legit First Rounder", 1, 1),
                        _draft_pick(222222, "Mislabeled Phase Pick", 671, 671),
                    ],
                }
            ]
        }
    }

    picks = draft_scraper._extract_picks(payload, 1969)

    assert [p["fullName"] for p in picks] == ["Legit First Rounder"]


def test_rebuild_index_preserves_multiple_drafts(tmp_path, monkeypatch):
    monkeypatch.setattr(draft_scraper, "DRAFT_CACHE_DIR", tmp_path)
    monkeypatch.setattr(draft_scraper, "DRAFT_INDEX_FILE", tmp_path / "index.json")
    (tmp_path / "2002.json").write_text(json.dumps(_buck_2002_payload()))
    (tmp_path / "2005.json").write_text(json.dumps(_buck_2005_payload()))

    index = draft_scraper.rebuild_index(verbose=False)

    buck = index["459941"]
    assert buck["overallPick"] == 36
    assert buck["rawRound"] == "C-1"
    assert len(buck["drafts"]) == 2
    assert [(p["year"], p["rawRound"], p["overallPick"]) for p in buck["drafts"]] == [
        (2002, "23", 700),
        (2005, "C-1", 36),
    ]
