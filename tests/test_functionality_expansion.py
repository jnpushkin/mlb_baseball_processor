import json
import subprocess
from pathlib import Path

from baseball_processor.utils.event_model import normalize_events
from baseball_processor.utils.team_identity import normalize_website_teams
from baseball_processor.processors.situational_hitting_tracker import SituationalHittingTracker
from baseball_processor.website.analysis_data import game_story
from baseball_processor.website.react_chunks.browser_utils import CODE
from baseball_processor.website.serializers import DataSerializer
from baseball_processor.processors.player_stats_processor import PlayerStatsProcessor


def game(plays):
    return {"game_id": "one", "basic_info": {"home_team_code": "BAL", "away_team_code": "WAS",
            "date_yyyymmdd": "20260626", "away_score_value": 0, "home_score_value": 1},
            "batting": {"away": [{"player_id": "jose", "name": "José Test", "AB": 3, "PA": 5,
                                  "H": 1, "BB": 1, "SF": 0, "SH": 1}], "home": []},
            "pitching": {"home": [{"player_id": "pitcher", "name": "A.J. Pitcher"}]},
            "raw_plays": plays}


def test_walk_and_double_play_are_not_hit_or_ab_confusions():
    g = game([{"inning": 1, "half": "top", "batter": "Jose Test", "pitcher": "AJ Pitcher",
               "outs": 1, "runners_on_base": "-2-", "score": "0-0", "description": d}
              for d in ("Intentional Walk", "Ground Ball Double Play: SS-2B-1B", "Single to CF")])
    events = normalize_events(g)
    assert [e["isAB"] for e in events] == [False, True, True]
    assert [e["isHit"] for e in events] == [False, False, True]
    assert all(e["batterId"] == "jose" and e["pitcherId"] == "pitcher" for e in events)
    tracker = SituationalHittingTracker()
    tracker.process_game_situations(g)
    assert tracker.player_situations["jose"]["risp_ab"] == 2
    assert tracker.player_situations["jose"]["risp_hits"] == 1


def test_api_state_is_before_play_and_missing_bases_remain_unknown():
    plays = [{"inning": 1, "half": "top", "event_type": "field_out", "away_score": 0,
              "home_score": 0, "outs_before": n} for n in (1, 2, 3)]
    events = normalize_events(game(plays))
    assert [e["outsBefore"] for e in events] == [0, 1, 2]
    assert [e["outsAfter"] for e in events] == [1, 2, 3]
    assert all(e["basesBefore"] is None for e in events)
    assert all(e["scoreBefore"] == [0, 0] for e in events)


def test_ambiguous_names_do_not_resolve_arbitrarily():
    g = game([{"batter": "Jose Test", "half": "top", "description": "Single"}])
    g["batting"]["away"].append({"player_id": "different", "name": "José Test"})
    assert normalize_events(g)[0]["batterId"] == ""


def test_sacrifices_survive_serialization_and_obp_excludes_bunts():
    g = game([])
    rows = DataSerializer()._serialize_player_games([g])
    assert rows[0]["sf"] == 0 and rows[0]["sh"] == 1
    hitters, *_ = PlayerStatsProcessor([g]).process_all_player_stats()
    assert hitters.iloc[0]["OBP"] == .5


def test_display_normalization_preserves_source_ids_and_historical_franchises():
    value = normalize_website_teams({"homeTeam": "NYN", "gameId": "NYN202606260",
                                     "team": "OAK, WAS", "score": "NYN 8 - 2 WAS"})
    assert value == {"homeTeam": "NYM", "gameId": "NYN202606260", "team": "OAK, WSH", "score": "NYM 8 - 2 WSH"}


def test_inning_story_reconciles_scores_and_rejects_incomplete_lines():
    g = {"gameId": "one", "date": "06/26/2026", "homeTeam": "BAL", "awayTeam": "WSH",
         "linescore": {"away": {"runs": 2, "innings": [2, 0]}, "home": {"runs": 3, "innings": [0, 3]}}}
    story = game_story(g)
    assert story["complete"] and story["comeback"] == 2 and story["leadChanges"] == 1
    g["linescore"]["away"]["innings"] = [1, 0]
    assert game_story(g)["comeback"] is None


def test_browser_scores_aliases_rates_and_scope():
    root = Path(__file__).resolve().parents[1]
    foundation = (root / "baseball_processor/website/react_chunks/core_foundation.py").read_text()
    aggregation = foundation[foundation.index("const hasHitterGameStats"):foundation.index("const exportToJSON")]
    passport = (root / "baseball_processor/website/react_chunks/passport.jsx").read_text()
    scope = passport[passport.index("const scopeGames"):passport.index("const passportMetrics")]
    source = CODE + "\n" + aggregation + "\n" + scope
    checks = """
      const assert=require('node:assert/strict');
      const g={homeTeam:'WSH',awayTeam:'BAL',score:'BAL 8 - 2 WAS (11)',linescore:{away:{runs:8},home:{runs:2}},venue:'AT&T Park',_venueKey:'Oracle Park'};
      assert.deepEqual(gameScores(g),{awayScore:8,homeScore:2});
      assert.equal(scopeGames([g],{venue:'Oracle Park'}).length,1);
      assert.equal(scopeGames([g],{venue:'Oracle Park',venueMode:'era'}).length,0);
      assert.equal(sameTeam('OAK','ATH'),false); assert.equal(sameTeam('OAK','ATH',true),true);
      const r=aggregateHitterStats([{playerId:'one',pa:5,ab:3,h:1,bb:1,sf:0,sh:1,r:0,rbi:0}])[0];
      assert.equal(r.obp,'0.500');assert.equal(r.bbPct,'20.0');assert.equal(r.sbPct,null);
    """
    result = subprocess.run(["node", "-e", source + checks], capture_output=True, text=True)
    assert result.returncode == 0, result.stderr


def test_backup_parity_matches_names_without_losing_newer_matching_behavior():
    from baseball_processor.reports.bref_backup_parity import _matching_row
    assert _matching_row({"name": "José O’Neill-Smith"}, [{"name": "Jose Oneill Smith"}], set()) is not None


def test_bref_combined_runner_events_preserve_plate_appearance():
    from baseball_processor.utils.event_model import event_type
    cases = {
        "Double Play: Strikeout Swinging, A. Runner Caught Stealing 2B": "strikeout_double_play",
        "Strikeout Swinging, A. Runner Steals 2B": "strikeout",
        "Walk, A. Runner Caught Stealing 3B": "walk",
        "Reached on Interference on C": "catcher_interf",
        "Flyball: CF/Sacrifice Fly; A. Runner Scores": "sac_fly",
        "Groundout: P-1B/Sacrifice Bunt": "sac_bunt",
        "Reached on E6": "field_error",
        "Pitcher A picks off B at 2nd": "runner_event",
    }
    for description, expected in cases.items():
        assert event_type({"description": description}) == expected


def test_career_scope_backup_calendar_and_matchup_contracts():
    root = Path(__file__).resolve().parents[1]
    insights = (root / "baseball_processor/website/react_chunks/insights.jsx").read_text()
    passport = (root / "baseball_processor/website/react_chunks/passport.jsx").read_text()
    source = CODE + "\n" + "\n".join([
        insights[insights.index("const analysisRate"):insights.index("const openAnalysis")],
        insights[insights.index("const matchupRows"):insights.index("const AnalysisPlays")],
        insights[insights.index("const careerShareRows"):insights.index("const AnalysisCareer")],
        insights[insights.index("const escapeCalendar"):insights.index("const AnalysisTrips")],
        passport[passport.index("const validatePassportBackup"):passport.index("const usePersonal")],
    ])
    checks = r"""
    const assert=require('node:assert/strict');
    const games=[{gameId:'regular',date:'09/21/2026',gameType:'regular'},{gameId:'spring',date:'03/21/2026',gameType:'spring'}];
    const data={playerGames:[{playerId:'one',gameId:'regular',date:'09/21/2026',h:3},{playerId:'one',gameId:'spring',h:10}],careerContext:{one:{cacheRefreshedAt:'2026-04-01',totals:{hitting:{hits:100}}}}};
    assert.equal(careerShareRows(data,games,'h')[0].witnessed,3);
    assert.equal(careerShareRows(data,games,'h')[0].share,null);
    data.careerContext.one.cacheRefreshedAt='2026-09-21';
    assert.equal(careerShareRows(data,games,'h')[0].share,'3.00');
    const e={isPA:true,isAB:true,isHit:true,batterId:'a',pitcherId:'b',gameId:'g'};
    const rows=matchupRows([e,{...e,isPA:false},{...e,batterId:''}]);
    assert.equal(rows[0].pa,1);assert.equal(rows[0].avg,'1.000');
    const backup={schemaVersion:1,journal:{g:{ticketCost:'0',rating:'5',currency:'USD'}},itinerary:[{gamePk:1,date:'2026-09-21',venue:'Park',matchup:'A @ B'}]};
    assert.equal(validatePassportBackup(backup),backup);
    assert.throws(()=>validatePassportBackup({...backup,journal:{g:{ticketCost:'-1'}}}));
    assert.throws(()=>validatePassportBackup({...backup,itinerary:[{...backup.itinerary[0],date:'bad'}]}));
    const calendar=calendarForGames([{gameId:'g',date:'09/21/2026',venue:'A, B',matchup:'A @ B'}]);
    assert.ok(calendar.includes('DTSTART;VALUE=DATE:20260921'));
    assert.ok(calendar.includes('LOCATION:A\\, B'));
    """
    result = subprocess.run(["node", "-e", source + checks], capture_output=True, text=True)
    assert result.returncode == 0, result.stderr


def test_bref_score_is_batting_team_first_and_normalized_to_away_home():
    g = game([{"inning": 1, "half": "top", "score": "0-0", "description": "Home Run"},
              {"inning": 1, "half": "bottom", "score": "0-1", "description": "Single"},
              {"inning": 1, "half": "bottom", "score": "2-1", "description": "Walk"}])
    plays = normalize_events(g)
    assert plays[0]["scoreAfter"] == [1, 0]
    assert plays[1]["scoreBefore"] == [1, 0]
    assert plays[1]["scoreDiff"] == -1
    assert plays[2]["scoreDiff"] == 1


def test_out_of_order_supplemental_api_events_do_not_inherit_final_score():
    g = game([{"inning": 9, "half": "bottom", "event_type": "field_out", "away_score": 4, "home_score": 3, "outs_before": 3},
              {"inning": 2, "half": "top", "event_type": "caught_stealing_2b", "away_score": 1, "home_score": 0},
              {"inning": 8, "half": "bottom", "event_type": "single", "away_score": 4, "home_score": 3}])
    events = normalize_events(g)
    assert all(e["scoreBefore"] is None and e["runs"] is None and e["outsBefore"] is None for e in events[1:])


def test_planner_park_identity_matches_accents_and_explicit_aliases():
    from baseball_processor.website.react_chunks.dashboard import CODE as DASHBOARD
    from baseball_processor.utils.constants import STADIUM_ALIASES
    references = DASHBOARD[DASHBOARD.index('const ALL_MLB_STADIUMS ='):DASHBOARD.index('// Build lookup maps')]
    aliases = {name: canonical for canonical, names in STADIUM_ALIASES.items() for name in [canonical, *names]}
    source = CODE + references + '\nconst aliases=' + json.dumps(aliases) + ';\n'
    checks = r'''
    const assert=require('node:assert/strict');
    const id=n=>venueIdentity(n,aliases,ALL_MLB_STADIUMS);
    assert.equal(id('Alfredo Harp Helú Stadium'),id('Estadio Alfredo Harp Helu'));
    assert.equal(id('Estadio Alfredo Harp Helú'),'stadium:harp_helu');
    assert.equal(id('AT&T Park'),id('Oracle Park'));
    assert.equal(id('Raley Field'),id('Sutter Health Park'));
    assert.notEqual(id('Yankee Stadium II'),id('Yankee Stadium'));
    const visited=new Set([id('Alfredo Harp Helú Stadium')]);
    const unvisited=ALL_MLB_STADIUMS.filter(s=>s.current&&!visited.has(id(s.name)));
    assert.ok(!unvisited.some(s=>s.id==='harp_helu'));
    '''
    result = subprocess.run(['node', '-e', source + checks], capture_output=True, text=True)
    assert result.returncode == 0, result.stderr
