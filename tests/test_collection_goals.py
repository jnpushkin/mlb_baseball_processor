import json
import subprocess
from copy import deepcopy
from datetime import datetime, timezone
from unittest.mock import Mock, patch

import pytest

from baseball_processor.website.collection_goals import apply_collection_goals, matches, refresh_rosters
from baseball_processor.website.react_chunks.browser_utils import CODE

NOW = datetime(2026, 9, 21, tzinfo=timezone.utc)
SNAPSHOT = {"checkedAt": NOW.isoformat(), "players": {"active": {"name": "Active Winner", "mlbId": 1}}}


def archive():
    items = [
        {"id": "seen", "playerId": "seen-retired", "checked": True, "year": 1980},
        {"id": "old", "playerId": "retired", "checked": False, "year": 1900},
        {"id": "later", "playerId": "retired", "checked": False, "year": 2010},
        {"id": "active1", "playerId": "active", "checked": False, "year": 1994},
        {"id": "active2", "playerId": "active", "checked": False, "year": 2025},
    ]
    return {
        "awardChecklists": {
            "groups": [{"awardKey": "mvp", "items": items}],
            "completionSets": [
                {"id": "mixed", "total": 5, "seen": 1, "missing": 4, "criteria": {"awardKeys": ["mvp"]}},
                {"id": "ancient", "criteria": {"year": 1900}},
                {"id": "retired-only", "criteria": {"year": 2010}},
                {"id": "older-active", "criteria": {"year": 1994}},
            ],
        }
    }


def test_historical_and_retired_missing_players_do_not_inflate_goals():
    data = apply_collection_goals(archive(), SNAPSHOT, NOW)["awardChecklists"]
    mixed, ancient, retired, older_active = data["completionSets"]
    assert (mixed["total"], mixed["seen"], mixed["missing"]) == (5, 1, 4)
    assert (mixed["goalTotal"], mixed["activeMissing"], mixed["activeMissingPlayers"]) == (3, 2, 1)
    assert mixed["excludedMissing"] == 2
    assert mixed["activeTargets"] == [{"playerId": "active", "name": "Active Winner", "mlbId": 1}]
    assert not ancient["goalAvailable"]
    assert not retired["goalAvailable"]
    assert older_active["goalAvailable"]  # Award year is not a player's retirement date.
    assert data["groups"][0]["items"][0]["goalEligible"]  # Never lose an actual sighting.


@pytest.mark.parametrize("snapshot", [{}, {**SNAPSHOT, "checkedAt": "2020-01-01T00:00:00+00:00"}])
def test_unknown_or_stale_rosters_never_create_active_goals(snapshot):
    data = apply_collection_goals(archive(), snapshot, NOW)["awardChecklists"]
    assert not data["metadata"]["rosterFresh"]
    assert not any(s["goalAvailable"] for s in data["completionSets"])
    assert data["completionSets"][0]["goalTotal"] == 1


def test_all_star_and_award_criteria_remain_scoped():
    item = {"year": 2026, "gameKey": "2026-1", "league": "AL", "position": "P", "selection": "Reserve"}
    assert matches(item, "all_star", {"awardKeys": ["all_star"], "year": 2026, "leagues": ["AL"], "positions": ["P"]})
    for criteria in (
        {"year": 2025},
        {"excludePositions": ["P"]},
        {"gameKey": "2026-2"},
        {"selections": ["Starter"]},
        {"awardKeys": ["mvp"]},
    ):
        assert not matches(item, "all_star", criteria)
    data = archive()
    data["allStarChecklists"] = deepcopy(data["awardChecklists"])
    apply_collection_goals(data, SNAPSHOT, NOW)
    assert data["allStarChecklists"]["completionSets"][0]["activeMissing"] == 2


def test_incomplete_network_refresh_keeps_previous_snapshot(tmp_path):
    path = tmp_path / "rosters.json"
    path.write_text(json.dumps(SNAPSHOT))
    before = path.read_bytes()
    teams = [{"id": i, "name": f"Team {i}"} for i in range(30)]

    def response(url, **kwargs):
        return Mock(json=lambda: {"teams": teams} if url.endswith("/teams") else {"roster": []})

    with patch("baseball_processor.website.collection_goals.requests.get", side_effect=response):
        with pytest.raises(ValueError, match="Empty roster"):
            refresh_rosters(path, force=True)
    assert path.read_bytes() == before


def test_browser_freshness_and_scoped_members():
    script = (
        CODE
        + """
const assert = require('assert');
const now = Date.parse('2026-09-21T12:00:00Z');
assert.ok(hasFreshCollectionRosters({rosterFresh:true,rosterAsOf:'2026-09-21T00:00:00Z'},now));
assert.ok(!hasFreshCollectionRosters({rosterFresh:true,rosterAsOf:'2020-01-01'},now));
assert.ok(!hasFreshCollectionRosters({},now));
const set = attainableCollection({seen:1,total:10,goalTotal:3,activeMissing:2,activeTargets:[{name:'Active'}],members:[{checked:true},{goalEligible:true},{checked:false}]});
assert.equal(set.total,3);assert.equal(set.missing,2);assert.equal(set.members.length,2);
assert.deepEqual(set.nextMissing,['Active']);
"""
    )
    subprocess.run(["node", "-e", script], check=True)
