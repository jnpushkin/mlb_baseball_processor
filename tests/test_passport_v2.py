import json
import shutil
import subprocess
import tempfile
import threading
import unittest
from http.server import ThreadingHTTPServer
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch
from urllib.error import HTTPError
from urllib.request import Request, urlopen

from baseball_processor import server
from baseball_processor.jobs import JobStore
from baseball_processor.website.bundle import build_site
from baseball_processor.website.react_chunks.browser_utils import CODE
from baseball_processor.website.release import validate_release


class JobQueueTests(unittest.TestCase):
    def test_http_submit_returns_job_and_reconnect_requires_token(self):
        job = {"id": "fixture-job", "state": "running", "stage": "build", "saved": True}
        store = SimpleNamespace(
            submit=lambda pk: {**job, "gamePk": pk}, get=lambda id: job if id == job["id"] else None
        )
        http = ThreadingHTTPServer(("127.0.0.1", 0), server.Handler)
        thread = threading.Thread(target=http.serve_forever, daemon=True)
        root = f"http://127.0.0.1:{http.server_port}"
        with (
            patch.object(server, "_server_token", "test-token"),
            patch.object(server, "get_job_store", return_value=store),
        ):
            thread.start()
            try:
                request = Request(
                    root + "/api/add?gamePk=42", method="POST", headers={"X-Add-Game-Token": "test-token"}
                )
                with urlopen(request, timeout=2) as response:
                    self.assertEqual(202, response.status)
                    self.assertEqual(42, json.load(response)["gamePk"])
                with self.assertRaises(HTTPError) as denied:
                    urlopen(root + "/api/jobs/fixture-job", timeout=2)
                self.assertEqual(403, denied.exception.code)
                with urlopen(
                    Request(root + "/api/jobs/fixture-job", headers={"X-Add-Game-Token": "test-token"}), timeout=2
                ) as response:
                    self.assertEqual(job, json.load(response))
            finally:
                http.shutdown()
                http.server_close()
                thread.join(timeout=2)

    def test_duplicate_submit_reconnect_and_completed_stages(self):
        with tempfile.TemporaryDirectory() as directory:
            started = threading.Event()
            finish = threading.Event()

            def operation(pk, on_progress):
                on_progress({"saved": True, "stage": "build"})
                started.set()
                finish.wait(5)
                return {"ok": True, "saved": True, "processed": True, "deployed": True, "stage": "complete"}

            store = JobStore(Path(directory) / "jobs.json", operation)
            try:
                job = store.submit(123)
                self.assertTrue(started.wait(2))
                self.assertEqual(job["id"], store.submit(123)["id"])
                self.assertTrue(store.get(job["id"])["saved"])
                self.assertEqual("build", json.loads(store.path.read_text())[job["id"]]["stage"])
                finish.set()
                store.executor.shutdown(wait=True)
                self.assertEqual("complete", store.get(job["id"])["state"])
            finally:
                finish.set()
                store.executor.shutdown(wait=True)

    def test_interrupted_work_is_recoverable_after_restart(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "jobs.json"
            path.write_text(
                json.dumps({"one": {"id": "one", "gamePk": 7, "state": "running", "saved": True, "stage": "build"}})
            )
            store = JobStore(path, lambda *a, **kw: {"ok": False, "message": "Failed"})
            try:
                self.assertEqual("failed", store.get("one")["state"])
                self.assertTrue(store.get("one")["saved"])
                self.assertIn("restarted", store.get("one")["message"])
                self.assertIsNone(store.get("unknown"))
            finally:
                store.executor.shutdown(wait=True)

    def test_worker_exception_does_not_leave_job_running(self):
        with tempfile.TemporaryDirectory() as directory:

            def operation(*a, **kw):
                raise RuntimeError("test failure")

            store = JobStore(Path(directory) / "jobs.json", operation)
            job = store.submit(1)
            store.executor.shutdown(wait=True)
            self.assertEqual("failed", store.get(job["id"])["state"])
            self.assertIn("test failure", store.get(job["id"])["message"])


class BundleTests(unittest.TestCase):
    def fake_compile(self, args, **kwargs):
        directory = Path(args[-1])
        (directory / "assets").mkdir(exist_ok=True)
        (directory / "assets/app-test.js").write_text("compiled javascript")
        (directory / "assets/app-test.css").write_text("compiled css")
        return SimpleNamespace(stdout=json.dumps({"js": "assets/app-test.js", "css": "assets/app-test.css"}))

    def test_retained_release_dependencies_are_complete_and_bounded(self):
        with (
            tempfile.TemporaryDirectory() as directory,
            patch("baseball_processor.website.bundle.subprocess.run", side_effect=self.fake_compile),
        ):
            root = Path(directory)
            indexes = []
            for version in range(4):
                build_site({"games": [], "milestones": [{"type": str(version)}]}, root / "site.html")
                manifest = validate_release(root)
                self.assertEqual(list(reversed(indexes[-2:])), manifest["previousIndexes"])
                indexes.append(manifest["index"])
            self.assertNotIn(indexes[0], manifest["files"])
            # Identical rebuilds do not evict a prior release.
            build_site({"games": [], "milestones": [{"type": "3"}]}, root / "site.html")
            self.assertEqual(manifest["previousIndexes"], validate_release(root)["previousIndexes"])
            # An explicitly retained older release can restore an already-open tab.
            build_site({"games": [], "milestones": [{"type": "4"}]}, root / "site.html", retain_indexes=[indexes[0]])
            manifest = validate_release(root)
            self.assertEqual([indexes[0], indexes[-1]], manifest["previousIndexes"])
            old = json.loads((root / indexes[0]).read_text())
            dependency = old["__libraries"]["milestones"]
            del manifest["files"][dependency]
            (root / "release.json").write_text(json.dumps(manifest))
            with self.assertRaisesRegex(ValueError, "Untracked data dependency"):
                validate_release(root)
            (root / dependency).write_text("corrupted old file")
            with self.assertRaisesRegex(ValueError, "Invalid retained data file"):
                build_site({"games": [], "milestones": [{"type": "5"}]}, root / "site.html", retain_indexes=[indexes[0]])

    def test_index_is_small_and_game_is_self_contained(self):
        game = {
            "gameId": "test1",
            "date": "09/14/2026",
            "gameType": "regular",
            "source": "mlb",
            "venue": "Old park name",
            "playByPlay": [{"description": "x" * 10000}],
            "hitData": [{"x": 1}],
            "pitchData": {"pitch": 1},
        }
        player = {"gameId": "test1", "playerId": "one", "h": 2, "hr": 1}
        data = {
            "games": [game],
            "players": [{"playerId": "one", "name": "One"}],
            "pitchers": [],
            "playersWithoutStats": [{"playerId": "two", "name": "Two", "gameIds": "test1"}],
            "playerGames": [player],
            "pitcherGames": [],
            "stadiumAliases": {"Old park name": "Park"},
            "companionData": {"gameCompanions": {"test1": ["Dad"]}},
            "generatedAt": "test",
        }
        with (
            tempfile.TemporaryDirectory() as directory,
            patch("baseball_processor.website.bundle.subprocess.run", side_effect=self.fake_compile),
        ):
            root = Path(directory)
            build_site(data, root / "site.html")
            manifest = validate_release(root)
            index = json.loads((root / manifest["index"]).read_text())
            self.assertNotIn("playByPlay", index["games"][0])
            self.assertNotIn("hitData", index["games"][0])
            self.assertEqual(["one", "two"], index["games"][0]["_players"])
            self.assertEqual(["one", "two"], index["games"][0]["firstSeenPlayerIds"])
            self.assertEqual("Park", index["games"][0]["_venueKey"])
            self.assertEqual(["Dad"], index["games"][0]["_companions"])
            detail = json.loads((root / index["__gameFiles"]["test1"]).read_text())
            self.assertEqual([player], detail["_detailPlayerGames"])
            self.assertEqual([], detail["_detailMilestones"])
            self.assertEqual(game["playByPlay"], detail["playByPlay"])
            html = (root / "site.html").read_text()
            self.assertNotIn("text/babel", html)
            self.assertNotIn("unpkg.com", html)
            original = index["__gameFiles"]["test1"]
            build_site(data, root / "site.html")
            self.assertEqual(original, json.loads((root / "data.json").read_text())["__gameFiles"]["test1"])
            self.assertEqual([], json.loads((root / "data.json").read_text())["__health"]["corrections"])
            player["h"] = 3
            build_site(data, root / "site.html")
            updated = json.loads((root / "data.json").read_text())
            self.assertEqual(["test1"], updated["__health"]["corrections"])
            original = updated["__gameFiles"]["test1"]
            (root / original).write_text("{}")
            with self.assertRaisesRegex(ValueError, "changed after build"):
                validate_release(root)


@unittest.skipUnless(shutil.which("node"), "Node needed for production JS helpers")
class PassportSelectionTests(unittest.TestCase):
    def test_ballpark_goals_require_matching_games_and_normalize_physical_parks(self):
        root = Path(__file__).resolve().parents[1]
        source = (root / "baseball_processor/website/react_chunks/passport.jsx").read_text().split("const usePersonal =")[0]
        checks = r"""
        const stadiums=[
          {id:'oracle',name:'Oracle Park',aliases:['AT&T Park'],current:true,team:'SF'},
          {id:'camden',name:'Camden Yards',current:true,team:'BAL'},
          {id:'fenway',name:'Fenway Park',current:true,team:'BOS'},
          {id:'newyankee',name:'Yankee Stadium',aliases:['Yankee Stadium III'],current:true,team:'NYY'},
          {id:'oldyankee',name:'Old Yankee Stadium',aliases:['Yankee Stadium II'],current:false,team:'NYY'},
          {id:'rate',name:'Rate Field',aliases:['U.S. Cellular Field','Guaranteed Rate Field'],current:true,team:'CHW'},
          {id:'mexico',name:'Estadio Alfredo Harp Helu',aliases:['Alfredo Harp Helú Stadium'],current:true,international:true,team:'INT'},
          {id:'spring',name:'Spring Park',current:true,springTraining:true,team:'ST'}];
        const games=[
          {gameId:'alone',venue:'AT&T Park',homeTeam:'SF',awayTeam:'BAL'},
          {gameId:'dad',venue:'Oracle Park',homeTeam:'SF',awayTeam:'LAD',_companions:['Dad']},
          {gameId:'both',venue:'Camden Yards',homeTeam:'Baltimore Orioles',awayTeam:'TB',_companions:['Dad']},
          {gameId:'repeat',venue:'Camden Yards',homeTeam:'BAL',awayTeam:'TB',_companions:['Dad']},
          {gameId:'old',venue:'Yankee Stadium II',homeTeam:'NYY',awayTeam:'BAL',_companions:['Dad']},
          {gameId:'mexico',venue:'Alfredo Harp Helú Stadium',homeTeam:'BAL',awayTeam:'HOU',_companions:['Dad']},
          {gameId:'rate',venue:'U.S. Cellular Field',homeTeam:'CHW',awayTeam:'BAL'}];
        const data={games,companionData:{gameCompanions:{rate:['Dad']}}};
        const progress=ballparkGoalProgress(data,stadiums);
        assert.deepEqual(progress.map(g=>g.parks.length),[5,5,5]);
        assert.deepEqual(progress.map(g=>g.completed.length),[3,2,3]);
        assert.ok(progress[1].missing.some(p=>p.id==='oracle')); // Two separate games cannot complete the shared goal.
        assert.ok(progress.every(g=>g.missing.some(p=>p.id==='newyankee')));
        assert.deepEqual(progress.map(g=>g.otherParks.length),[2,2,2]);
        """
        checks += r"""
        const identity=name=>venueIdentity(name,{},stadiums);
        const schedule=(park,orioles=true)=>({venue:{name:park},teams:{home:{team:{id:111,name:'Boston Red Sox'}},away:{team:{id:orioles?110:137,name:orioles?'Baltimore Orioles':'San Francisco Giants'}}}});
        const matches=(park,orioles=true,dad=true,focus='all')=>ballparkScheduleMatches(schedule(park,orioles),progress,identity,dad,focus).map(g=>g.id);
        assert.deepEqual(matches('Fenway Park'),['orioles','orioles-dad','dad']);
        assert.deepEqual(matches('Oracle Park'),['orioles-dad']);
        assert.deepEqual(matches('Fenway Park',false),['dad']);
        assert.deepEqual(matches('Fenway Park',true,false),['orioles']);
        assert.deepEqual(matches('Fenway Park',true,true,'orioles-dad'),['orioles-dad']);
        assert.deepEqual(matches('Guaranteed Rate Field'),[]);
        assert.deepEqual(matches('Unknown Park'),[]);
        assert.deepEqual(matches('Old Yankee Stadium'),[]);
        assert.equal(progress[0].completed.length,3); // Recommendations do not change completion.
        assert.doesNotThrow(()=>validatePassportBackup({schemaVersion:1,itinerary:[]}));
        assert.throws(()=>validatePassportBackup({schemaVersion:1,itinerary:[{gamePk:1,matchup:'A @ B',date:'2026-09-21',venue:'Park',withDad:'yes'}]}));
        """
        result = subprocess.run(["node", "-e", CODE + "\n" + source + "\nconst assert=require('node:assert/strict');\n" + checks], capture_output=True, text=True)
        self.assertEqual(0, result.returncode, result.stderr)

    def test_release_runtime_recovery(self):
        root = Path(__file__).resolve().parents[1]
        result = subprocess.run(
            ["node", "--test", "tests/frontend/runtime.test.mjs"], cwd=root, capture_output=True, text=True
        )
        self.assertEqual(0, result.returncode, result.stdout + result.stderr)

    def test_scope_metrics_alias_search_and_exact_rank(self):
        source = (
            (Path(__file__).resolve().parents[1] / "baseball_processor/website/react_chunks/passport.jsx")
            .read_text()
            .split("const usePersonal =")[0]
        )
        checks = r"""
        const games=[{gameId:'one',date:'09/14/2026',gameType:'regular',homeTeam:'SF',awayTeam:'BAL',venue:'Oracle Park',_venueKey:'Oracle Park',_players:['a','b'],_companions:['Dad'],attendance:100,_totals:{hr:2}},
                     {gameId:'two',date:'09/14/2025',gameType:'spring',homeTeam:'BAL',awayTeam:'SF',venue:'AT&T Park',_venueKey:'Oracle Park',_players:['b','c'],attendance:null,_totals:{hr:1}}];
        assert.equal(scopeGames(games,{year:'2026',type:'regular',team:'BAL',side:'away',companion:'Dad'}).length,1);
        assert.equal(scopeGames(games,{team:'BAL',side:'home',companion:'Dad'}).length,0);
        const metrics=passportMetrics(games);
        assert.equal(metrics.players,3);assert.equal(metrics.parks,1);assert.equal(metrics.averageAttendance,100);assert.equal(metrics.attendanceCoverage,1);
        const data={games,players:[{playerId:'b',name:'Jose Ramirez Jr.'},{playerId:'a',name:'José Ramírez'}],pitchers:[],stadiumAliases:{'AT&T Park':'Oracle Park'}};
        assert.equal(passportSearch(data,'jose ramirez')[0].id,'a');
        assert.equal(passportSearch(data,'Baltimore')[0].id,'one');
        assert.ok(passportSearch(data,'splash hits').some(r=>r.subtab==='splash'));
        assert.equal(passportSearch(data,'AT&T Park').filter(r=>r.type==='game').length,2);
        assert.ok(!passportKeysForRoute({tab:'dashboard'}).length);
        assert.ok(passportKeysForRoute({tab:'players',subtab:'awards'}).includes('awardChecklists'));
        assert.ok(!passportKeysForRoute({tab:'players',subtab:'hitters'}).includes('awardChecklists'));
        assert.ok(passportKeysForRoute({tab:'trivia',subtab:'drafts'}).includes('firstRoundDraftPicks'));
        const events=Array.from({length:30},(_,i)=>({type:'milestone',label:'José Ramírez',sub:'Home run '+i}));
        assert.equal(passportSearch({...data,searchEvents:events},'home run').filter(r=>r.type==='milestone').length,30);
        assert.ok(passportSearch(data,'lifetime totals').some(r=>r.subtab==='totals'));
        assert.deepEqual(passportKeysForRoute({tab:'special',subtab:'records'}),['recordBook']);
        assert.deepEqual(passportKeysForRoute({tab:'milestones',subtab:'counts'}),['summary']);
        assert.ok(passportKeysForRoute({tab:'dashboard',subtab:'search'}).includes('searchEvents'));
        const backup={schemaVersion:1,journal:{one:{notes:'test'}},goals:[{id:'1',name:'A park',kind:'ballpark'}],views:[{name:'2026',route:{year:'2026'},tables:{dt_test:'{}'}}]};
        assert.equal(validatePassportBackup(backup),backup);
        assert.throws(()=>validatePassportBackup({...backup,goals:[{id:'1',name:'X',kind:'wrong'}]}));
        assert.throws(()=>validatePassportBackup({...backup,images:[{gameId:'one',images:['https://invalid.example/image']}] }));
        assert.throws(()=>validatePassportBackup({...backup,views:[{name:'unsafe',route:{},tables:{baseballDarkMode:'true'}}]}));
        """
        result = subprocess.run(
            [
                "node",
                "-e",
                "const assert=require('node:assert/strict');const TEAM_CODE_TO_NAME={BAL:'Baltimore Orioles',SF:'San Francisco Giants'};\n"
                + CODE
                + "\n"
                + source
                + "\n"
                + checks,
            ],
            capture_output=True,
            text=True,
        )
        self.assertEqual(0, result.returncode, result.stderr)
