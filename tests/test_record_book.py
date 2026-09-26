"""Records must be recomputable from real candidate games, not summary maxima."""
import json
import subprocess
from pathlib import Path

import pandas as pd

from baseball_processor.processors.summary_stats_processor import SummaryStatsProcessor
from baseball_processor.website.react_chunks.browser_utils import CODE as BROWSER_UTILS
from baseball_processor.website.react_chunks.core_foundation import CODE as FOUNDATION
from baseball_processor.website.record_book import build_record_book, repair_summary_counts


def game(id_, kind='regular', date='04/01/2026', runs=(2, 3)):
    return dict(gameId=id_, date=date, gameType=kind, homeTeam='BAL', awayTeam='SF', venue='Camden',
                linescore={side: dict(runs=r, hits=r+1, innings=[r]) for side, r in zip(('away', 'home'), runs, strict=True)})


def test_inclusive_counts_share_performances_and_eligible_game_links():
    data = dict(games=[game('G1'), game('G2'), game('SPRING', 'spring')],
                playerGames=[dict(gameId='G1', playerId='A', name='A', h=5, rbi=8, hr=3),
                             dict(gameId='G1', playerId='B', name='B', h=4, rbi=5, hr=2),
                             dict(gameId='G2', playerId='A', name='A', h=4, rbi=5, hr=2),
                             dict(gameId='SPRING', playerId='C', name='C', h=6, rbi=9, hr=4)],
                pitcherGames=[dict(gameId='G1', playerId='D', name='D', so=15),
                              dict(gameId='G2', playerId='D', name='D', so=12)],
                allMilestones=[dict(type='Quality Starts', gameId='G1', playerId=f'p{i}', player=f'P{i}') for i in range(55)],
                summary=[dict(record=n, value='0', gameIds='') for n in ('4+ Hit Games', '5+ RBI Games', 'Multi-HR Games', '10+ K Games', 'Quality Starts')])
    data['playerGames'].append(dict(data['playerGames'][0]))
    repair_summary_counts(data)
    result = {r['record']: r for r in data['summary']}
    for label in ('4+ Hit Games', '5+ RBI Games', 'Multi-HR Games'):
        assert result[label]['value'] == '3'
        assert result[label]['gameIds'] == 'G1, G2'
        assert len(result[label]['performances']) == 3
    assert result['10+ K Games']['value'] == '2'
    assert result['Quality Starts']['value'] == '55'
    assert result['Quality Starts']['gameIds'] == 'G1'


def test_raw_summary_tiers_are_inclusive_without_mutating_detectors():
    processor = SummaryStatsProcessor.__new__(SummaryStatsProcessor)
    processor.games = [dict(game_id='G1'), dict(game_id='G2'), dict(game_id='S', basic_info={'game_type':'spring'})]
    processor.milestones = {
        '4+ Hit Games': pd.DataFrame([dict(GameID='G1', Player='A')]),
        '5+ Hit Games': pd.DataFrame([dict(GameID='G2', Player='B'), dict(GameID='S', Player='C')]),
        '10+ K Games': pd.DataFrame([dict(GameID='G1', Player='D')]),
        '12+ K Games': pd.DataFrame([dict(GameID='G2', Player='D')]),
        '15+ K Games': pd.DataFrame([dict(GameID='G2', Player='D')]),
    }
    result = processor._inclusive_summary_milestones()
    assert result['4+ Hit Games']['GameID'].tolist() == ['G1', 'G2']
    assert result['10+ K Games']['GameID'].tolist() == ['G1', 'G2']
    assert len(processor.milestones['5+ Hit Games']) == 2


def test_candidates_preserve_ties_doubleheaders_zero_and_missing_data():
    games = [game('DH1'), game('DH2'), game('S', 'spring')]
    games[0].update(temperature=0, attendance=0, gameLength='1:53', startTime='12:07 p.m.')
    games[1].update(attendance=123, gameLength='bad')
    players = [dict(gameId='DH1', playerId=str(i), name=f'P{i}', team='SF', h=value, doubles=1, triples=0, hr=1, rbi=2)
               for i, value in enumerate([6, 5, 4, 3, 2, 2, 1])]
    players.append(dict(gameId='DH2', playerId='0', name='P0', team='SF', h=5, doubles=1, triples=0, hr=1, rbi=8))
    data = dict(games=games, playerGames=players, pitcherGames=[], summary=[])
    original = json.dumps(data)
    book = {r['id']: r for r in build_record_book(data)}
    assert len(book['player-hits']['candidates']) == 7  # Six from DH1 including cutoff ties; one from DH2.
    assert {r['gameId'] for r in book['player-hits']['candidates']} == {'DH1', 'DH2'}
    assert book['coldest']['candidates'][0]['value'] == 0
    assert len(book['coldest']['candidates']) == 1  # Missing temperature never becomes zero.
    assert book['lowest-attendance']['candidates'][0]['value'] == 123
    assert book['shortest-time']['candidates'][0]['value'] == 113
    assert book['earliest']['candidates'][0]['value'] == 727
    assert 'combined-hr' not in book  # Missing opponent boxscore is unknown.
    assert max(r['value'] for r in book['player-tb']['candidates']) == 10
    assert json.dumps(data) == original

    # Six tied leaders occupy the entire top five; the next distinct mark is
    # still needed to report the runner-up gap for this single-game scope.
    tied = [dict(gameId='DH1', playerId=str(i), name=f'P{i}', team='SF', h=5 if i < 6 else 4)
            for i in range(7)]
    tied_book = {r['id']: r for r in build_record_book(dict(games=games, playerGames=tied))}
    assert [r['value'] for r in tied_book['player-hits']['candidates']] == [5, 5, 5, 5, 5, 5, 4]


def test_record_scope_rankings_and_progression_recompute_from_candidates():
    source = (Path(__file__).resolve().parents[1] / 'baseball_processor/website/react_chunks/record_book.jsx').read_text().split('const RecordHolder =')[0]
    checks = r"""
const assert = require('node:assert/strict');
const games = [
 {gameId:'G1',date:'04/01/2024',homeTeam:'BAL',awayTeam:'SF',gameType:'regular',venue:'Camden',_companions:['Dad']},
 {gameId:'G2',date:'04/01/2025',homeTeam:'BAL',awayTeam:'SF',gameType:'regular',venue:'Camden',_companions:[]},
 {gameId:'G3',date:'04/01/2026',homeTeam:'NYM',awayTeam:'SF',gameType:'postseason',venue:'Citi',_companions:['Dad']},
 {gameId:'G4',date:'04/01/2026',homeTeam:'NYM',awayTeam:'SF',gameType:'postseason',venue:'Citi',_companions:['Dad']},
 {gameId:'S',date:'03/01/2026',homeTeam:'BAL',awayTeam:'SF',gameType:'spring',venue:'S',_companions:['Dad']}
];
const definition = {id:'hits',label:'Hits',direction:'max',format:'number',unit:'hits',candidates:[
 {gameId:'G1',value:3,holder:'A'}, {gameId:'G2',value:5,holder:'B'},
 {gameId:'G3',value:4,holder:'C'}, {gameId:'G4',value:5,holder:'D'}, {gameId:'S',value:8,holder:'E'}]};
const before=JSON.stringify(definition);
const all=rankRecordBook([definition],recordScopeGames(games,{}))[0];
assert.equal(all.value,5);assert.equal(all.holders.length,2);
assert.deepEqual(all.history.map(e=>e.type),['First witnessed','New record','Tied record']);
assert.deepEqual(all.ranked.map(r=>r.rank),[1,1,3,4]);
const dad=rankRecordBook([definition],recordScopeGames(games,{recordScope:'orioles-dad'}),true)[0];
assert.equal(dad.value,3);assert.equal(dad.holders[0].gameId,'G1');
assert.equal(rankRecordBook([definition],recordScopeGames(games,{recordScope:'dad',recordYear:'2025'}),true).length,0);
assert.equal(rankRecordBook([definition],recordScopeGames(games,{recordType:'spring'}),true)[0].value,8);
assert.equal(rankRecordBook([{...definition,coverage:'holders-only'}],games,true).length,0);
const minimum=rankRecordBook([{...definition,direction:'min'}],recordScopeGames(games,{}))[0];
assert.equal(minimum.value,3);assert.deepEqual(minimum.history.map(e=>e.type),['First witnessed']);
assert.equal(recordValue({format:'duration'},113),'1h 53m');
assert.equal(recordValue({format:'clock'},727),'12:07 PM');
assert.equal(recordValue({format:'outs'},20),'6.2');
assert.equal(JSON.stringify(definition),before);
"""
    ip_helper = 'const formatOutsAsIP =' + FOUNDATION.split('const formatOutsAsIP =', 1)[1].split('const decimalInningsToOuts', 1)[0]
    result = subprocess.run(['node', '-e', BROWSER_UTILS + ip_helper + source + checks], capture_output=True, text=True)
    assert result.returncode == 0, result.stderr
