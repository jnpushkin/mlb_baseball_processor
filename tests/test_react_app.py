import subprocess
import unittest
from pathlib import Path

from baseball_processor.website.react_app import ReactComponents
from baseball_processor.website.react_chunks.browser_utils import CODE as BROWSER_UTILS
from baseball_processor.website.templates import HTMLTemplate


class ReactAppTests(unittest.TestCase):
    def test_record_book_classification_units_search_and_chronology(self):
        source = (Path(__file__).resolve().parents[1] / "baseball_processor/website/react_chunks/special_features.jsx").read_text()
        helpers = source.split("const SpecialHeader =")[0]
        checks = r"""
        const assert = require('node:assert/strict');
        const data = {games:[
            {gameId:'G1',date:'04/15/2018',homeTeam:'LAD',awayTeam:'ARI',venue:'Estadio Alfredo Harp Helú'},
            {gameId:'G2',date:'09/25/2026',homeTeam:'SF',awayTeam:'LAD',venue:'Oracle Park'}
        ], summary:[
            {record:'Most Combined Runs',value:'27',gameIds:'G1,G2,G2,MISSING',detail:'José Ramírez'},
            {record:'Shortest Game by Time',value:'1:53',gameIds:'G2'},
            {record:'Total Hits Across All Games',value:'4851'},
            {record:'Average Attendance',value:'30,939'},
            {record:'1-Run Games',value:'75',gameIds:'G1'},
            {record:'Fewest Combined Walks',value:'0',gameIds:'G1'},
            {record:'Most Clutch Single Game (WPA)',value:'0.738',gameIds:'G1'}
        ]};
        const before = JSON.stringify(data);
        const book = buildSpecialRecordBook(data);
        const get = name => book.find(r => r.record === name);
        const tied = get('Most Combined Runs');
        assert.deepEqual(tied.linkedGames.map(g=>g.gameId),['G2','G1']);
        assert.equal(tied.firstDate,'04/15/2018');
        assert.equal(tied.latestDate,'09/25/2026');
        for (const query of ['jose','harp helu','oracle','2018','lad','27']) assert.ok(tied.searchText.includes(query));
        assert.deepEqual(get('Shortest Game by Time').metric,{value:'1h 53m',unit:'game time'});
        assert.deepEqual(get('Total Hits Across All Games').metric,{value:'4,851',unit:'hits'});
        assert.equal(get('Total Hits Across All Games').kind,'summary');
        assert.equal(get('Average Attendance').kind,'summary');
        assert.equal(get('1-Run Games').kind,'occurrences');
        assert.equal(get('Fewest Combined Walks').metric.value,'0');
        assert.equal(get('Most Clutch Single Game (WPA)').metric.value,'0.738');
        assert.equal(sortSpecialRecords(book,'recent')[0].latestDate,'09/25/2026');
        assert.equal(sortSpecialRecords(book,'oldest')[0].firstDate,'04/15/2018');
        assert.equal(sortSpecialRecords(book,'oldest').at(-1).firstDate,'');
        assert.equal(JSON.stringify(data),before);
        assert.deepEqual(buildSpecialRecordBook({}),[]);
        """
        result = subprocess.run(["node", "-e", BROWSER_UTILS + helpers + checks], capture_output=True, text=True)
        self.assertEqual(0, result.returncode, result.stdout + result.stderr)

    def test_special_moments_preserve_doubleheaders_and_multiple_landmark_homers(self):
        source = (Path(__file__).resolve().parents[1] / "baseball_processor/website/react_chunks/special_features.jsx").read_text()
        helpers = source.split("const SpecialHeader =")[0]
        checks = r"""
        const assert = require('node:assert/strict');
        const games = [
          {gameId:'GAME1',date:'09/21/2026'},
          {gameId:'GAME2',date:'09/21/2026'},
          {gameId:'OLD',date:'09/21/2004'},
        ];
        const debut = {playerId:'same',player:'Same Player',gameId:'GAME1'};
        const hr = {playerId:'same',player:'Same Player',gameId:'GAME2',signatureNumber:'Splash Hit #10'};
        const data = {games,debuts:[debut,debut],finalGames:[{...debut,gameId:'OLD'}],
          signatureHRs:[hr,hr,{...hr,signatureNumber:'Splash Hit #11'}]};
        const moments = buildSpecialMoments(data);
        assert.equal(moments.length,4);
        assert.equal(moments.at(-1).kind,'final');
        assert.equal(moments[0].date,'09/21/2026');
        assert.equal(moments.find(m=>m.kind==='debut').game.gameId,'GAME1');
        assert.ok(moments.filter(m=>m.kind==='homer').every(m=>m.game.gameId==='GAME2'));
        assert.deepEqual(specialRecordGames({gameIds:'GAME2, GAME2, UNKNOWN'},games).map(g=>g.gameId),['GAME2']);
        assert.deepEqual(buildSpecialMoments({}),[]);
        assert.equal(specialRecords({summary:[{record:'Hits Leaders'},{record:'No-Hitters',value:'0'}]}).length,1);
        """
        result = subprocess.run(["node", "-e", BROWSER_UTILS + helpers + checks], capture_output=True, text=True)
        self.assertEqual(0, result.returncode, result.stdout + result.stderr)

    def test_app_code_starts_with_shared_react_bindings(self):
        code = ReactComponents.get_app_code()

        self.assertTrue(code.startswith("const { useState"))

    def test_template_pins_babel_standalone_to_classic_runtime_version(self):
        html = HTMLTemplate.create_full_page({})

        self.assertIn("https://unpkg.com/@babel/standalone@7.28.5/babel.min.js", html)
        self.assertNotIn("https://unpkg.com/@babel/standalone/babel.min.js", html)

    def test_react_app_uses_baseball_ip_formatting_helpers(self):
        code = ReactComponents.get_app_code()

        self.assertIn("const formatOutsAsIP", code)
        self.assertIn("const baseballIPToOuts", code)
        self.assertIn("formatHistoricalStatValue(passing.new_value, passing.stat)", code)
        self.assertIn("baseballIPToOuts(p.ip) >= minIP * 3", code)
        self.assertNotIn("t.value += (pg.outs || 0) / 3", code)
        self.assertNotIn("playerInfo[pid].IP += (pg.outs || 0) / 3", code)

    def test_react_hitter_aggregation_ignores_game_only_rows(self):
        code = ReactComponents.get_app_code()

        self.assertIn("const hasHitterGameStats", code)
        self.assertIn("if (!hasHitterGameStats(game)) return;", code)

    def test_leaderboards_match_hitters_tab_game_type_scope(self):
        code = ReactComponents.get_app_code()

        self.assertIn("const [gameTypeFilter, setGameTypeFilter] = useState(scopeType||'regular');", code)
        self.assertIn("return aggregateHitterStats(filteredGames);", code)
        self.assertIn("return aggregatePitcherStats(filteredGames);", code)
        self.assertNotIn("if (!useFiltered || (!startDate && !endDate)) return data.players || [];", code)
        self.assertNotIn("if (!useFiltered || (!startDate && !endDate)) return data.pitchers || [];", code)

    def test_players_tab_includes_uva_alumni_tracker(self):
        code = ReactComponents.get_app_code()

        self.assertIn("const UvaPlayersView", code)
        self.assertIn("{ id: 'uva', label: 'UVA' }", code)
        self.assertIn("data.uvaPlayersSeen || []", code)
        self.assertIn("Virginia Cavaliers in the Majors", code)
        self.assertIn("requestGameDetails(row[gameIdKey])", code)
        self.assertIn("Default order: games seen, most to least.", code)
        self.assertIn("{ key: 'games', label: 'Games Seen' }", code)
        self.assertNotIn("{ key: 'role', label: 'Role' }", code)


if __name__ == "__main__":
    unittest.main()
