"""Behavioral regressions found in the September product audit."""
import json
import os
import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

from baseball_processor import server
from baseball_processor.main import _maybe_deploy_to_surge
from baseball_processor.website.react_chunks.browser_utils import CODE
from baseball_processor.website.serializers import DataSerializer
from baseball_processor.utils.jerseys import game_jersey


class JerseyNumberTests(unittest.TestCase):
    @staticmethod
    def game(date, player_id='pederjo01', number='42', game_type='regular'):
        player = {'name': 'Test Player', 'player_id': player_id, 'jersey_number': number}
        return {'game_id': f'SFN{date}0',
                'basic_info': {'date_yyyymmdd': date, 'game_type': game_type, 'home_team_code': 'SF'},
                'batting': {'home': [player]}, 'pitching': {'home': [dict(player)]},
                'lineups': {'home': [dict(player)]}}

    def test_bad_42_is_withheld_in_collection_and_lineup_without_mutating_source(self):
        serializer = DataSerializer()
        for date, player_id in [('20180526', 'iannech01'), ('20190702', 'givenmy01'),
                                ('20190703', 'givenmy01'), ('20230408', 'pederjo01')]:
            with self.subTest(date=date):
                game = self.game(date, player_id)
                self.assertEqual(serializer._serialize_jersey_log([game]), {})
                self.assertEqual(serializer._extract_game_details(game)['lineups']['home'][0]['jerseyNumber'], '')
                self.assertEqual(game['batting']['home'][0]['jersey_number'], '42')

    def test_rivera_and_earlier_wearers_remain(self):
        serializer = DataSerializer()
        games = [self.game('20130911', 'riverma01'), self.game('20080822', 'riverma01'),
                 self.game('20030501', 'vaughmo01')]
        entries = serializer._serialize_jersey_log(games)['42']
        self.assertEqual([(p['playerId'], p['date']) for p in entries],
                         [('vaughmo01', '05/01/2003'), ('riverma01', '08/22/2008')])
        self.assertTrue(all(p['uniformContext'] == 'regular' for p in entries))

    def test_tribute_overrides_usual_number_for_actual_game_and_lineup(self):
        serializer = DataSerializer()
        for date in ('20160415', '20180415'):
            game = self.game(date, number='31')
            log = serializer._serialize_jersey_log([game])
            self.assertEqual(list(log), ['42'])
            self.assertEqual(len(log['42']), 1)  # Batting + pitching is one sighting.
            self.assertEqual(log['42'][0]['uniformContext'], 'jackie-robinson-day')
            self.assertEqual(serializer._extract_game_details(game)['lineups']['home'][0]['jerseyNumber'], '42')
        for date, game_type in [('20080415', 'regular'), ('20200415', 'regular'),
                                ('20260415', 'spring'), ('20260415', 'exhibition')]:
            game = self.game(date, number='31', game_type=game_type)
            self.assertEqual(game_jersey(game['batting']['home'][0], game, 'home'), ('31', 'regular'))

    def test_delayed_tribute_requires_citation_and_only_applies_to_specified_side(self):
        game = self.game('20260416')
        player = game['batting']['home'][0]
        game['uniform_tributes'] = {'home': {'type': 'jackie_robinson_day'}}
        self.assertEqual(game_jersey(player, game, 'home'), ('', ''))
        game['uniform_tributes']['home']['source'] = 'https://example.test/game-observance'
        self.assertEqual(game_jersey(player, game, 'home'), ('42', 'jackie-robinson-day'))
        self.assertEqual(game_jersey(player, game, 'away'), ('', ''))

    def test_regular_sighting_survives_earlier_spring_game_and_number_zero(self):
        games = [self.game('20260601', number='0'), self.game('20260301', number=0, game_type='spring'),
                 self.game('20260401', number=0), self.game('20260501', number='00')]
        log = DataSerializer()._serialize_jersey_log(games)
        self.assertEqual([p['date'] for p in log['0']], ['03/01/2026', '04/01/2026'])
        self.assertEqual(len(log['00']), 1)


class DurationTests(unittest.TestCase):
    def test_excel_minutes_survive_round_trip(self):
        serializer = DataSerializer.__new__(DataSerializer)
        for minutes in (115, 259, 179, 180, 181):
            with self.subTest(minutes=minutes):
                expected = f'{minutes // 60}:{minutes % 60:02}'
                self.assertEqual(serializer._format_game_length(minutes / 1440), expected)
                self.assertEqual(serializer._format_game_length(str(minutes / 1440)), expected)

    def test_strings_and_missing_values(self):
        serializer = DataSerializer.__new__(DataSerializer)
        for value, expected in [('2:39', '2:39'), (None, ''), (float('nan'), '')]:
            self.assertEqual(serializer._format_game_length(value), expected)


@unittest.skipUnless(shutil.which('node'), 'Node is required for JavaScript behavior tests')
class BrowserUtilityTests(unittest.TestCase):
    def run_js(self, assertions, timezone='America/Los_Angeles'):
        subprocess.run(['node', '-e', "const assert = require('node:assert/strict');\n" + CODE + '\n' + assertions],
                       env={**os.environ, 'TZ': timezone}, check=True, capture_output=True, text=True)

    def test_date_range_includes_both_endpoints_in_all_timezones(self):
        for timezone in ('America/Los_Angeles', 'UTC', 'Asia/Tokyo'):
            with self.subTest(timezone=timezone):
                self.run_js("""
                    assert.equal(toSortableDate('2026-09-14'), '20260914');
                    assert.equal(toSortableDate('9/14/2026'), '20260914');
                    assert.equal(isDateInRange('09/14/2026', '2026-09-14', '2026-09-14'), true);
                    assert.equal(isDateInRange('09/13/2026', '2026-09-14', ''), false);
                    assert.equal(isDateInRange('09/15/2026', '', '2026-09-14'), false);
                    assert.equal(isDateInRange('', '2026-09-14', ''), false);
                """, timezone)

    def test_search_normalizes_names_and_orders_games_newest_first(self):
        self.run_js("""
            const data = {
                players: [{playerId: 'jose', name: 'José Ramírez', games: 3}],
                pitchers: [{playerId: 'jose', name: 'José Ramírez', games: 1}, {playerId: 'aj', name: 'A.J. Puk', games: 1}],
                games: Array.from({length: 8}, (_, i) => ({gameId: 'g' + i, date: `09/${10 + i}/2026`, homeTeam: 'SF', awayTeam: 'BAL'}))
            };
            const names = getGlobalSearchResults(data, 'Jose Ramirez');
            assert.equal(names.items[0].id, 'jose');
            assert.equal(names.totalPlayers, 1);
            assert.equal(getGlobalSearchResults(data, 'AJ Puk').items[0].id, 'aj');
            const games = getGlobalSearchResults(data, '2026').items;
            assert.deepEqual(games.map(g => g.id), ['g7', 'g6', 'g5', 'g4', 'g3']);
            assert.equal(data.games[0].gameId, 'g0'); // Search does not mutate source order.
        """)

    def test_players_seen_counts_pitchers_and_no_stat_players_once(self):
        self.run_js("""
            assert.equal(countPlayersSeen({players: [{playerId: 'a'}, {playerId: 'b'}],
                pitchers: [{playerId: 'b'}, {playerId: 'c'}], playersWithoutStats: [{playerId: 'd'}, {}]}), 4);
            assert.equal(countPlayersSeen({}), 0);
        """)


class AddGameOutcomeTests(unittest.TestCase):
    def setUp(self):
        directory = tempfile.TemporaryDirectory()
        self.addCleanup(directory.cleanup)
        self.root = Path(directory.name)
        for name in ('CACHE_DIR', 'PROJECT_DIR'):
            patcher = patch.object(server, name, self.root)
            patcher.start()
            self.addCleanup(patcher.stop)
        self.game = {'game_id': 'MTEST202609200', 'mlb_game_pk': 123}
        self.parser = self.start_patch('parse_mlb_game', return_value=self.game)
        self.build = self.start_patch('subprocess.run', return_value=SimpleNamespace(returncode=0))
        self.deploy = self.start_patch('deploy_to_surge', return_value=True)
        self.start_patch('load_surge_domain', return_value='example.surge.sh')

    def start_patch(self, name, **kwargs):
        patcher = patch('baseball_processor.server.' + name, **kwargs)
        result = patcher.start()
        self.addCleanup(patcher.stop)
        return result

    def test_success_requires_all_three_stages(self):
        result = server.add_game(123)
        self.assertTrue(all(result[k] for k in ('ok', 'saved', 'processed', 'deployed')))
        self.assertTrue(self.build.call_args.kwargs['check'])
        self.assertIn('--no-deploy', self.build.call_args.args[0])
        self.assertEqual(self.deploy.call_count, 1)
        self.assertFalse(server._processing)

    def test_failed_build_keeps_cache_and_never_deploys(self):
        self.build.side_effect = subprocess.CalledProcessError(1, ['processor'])
        result = server.add_game(123)
        self.assertTrue(result['saved'])
        self.assertFalse(result['ok'])
        self.assertFalse(result['processed'])
        self.assertEqual(result['stage'], 'build')
        self.deploy.assert_not_called()
        self.assertEqual(json.loads((self.root / 'MTEST202609200.json').read_text()), self.game)
        self.assertFalse(server._processing)

    def test_failed_deploy_can_retry_without_refetching_game(self):
        self.deploy.return_value = False
        failed = server.add_game(123)
        self.assertFalse(failed['ok'])
        self.assertTrue(failed['processed'])
        self.assertFalse(failed['deployed'])
        self.assertEqual(failed['stage'], 'deploy')
        self.deploy.return_value = True
        self.assertTrue(server.add_game(123)['ok'])
        self.parser.assert_called_once()

    def test_timeout_reports_saved_state_and_releases_processing_flag(self):
        self.build.side_effect = subprocess.TimeoutExpired(['processor'], 300)
        result = server.add_game(123)
        self.assertTrue(result['saved'])
        self.assertFalse(result['ok'])
        self.assertFalse(server._processing)
        self.deploy.assert_not_called()

    def test_parse_failure_does_not_build_or_create_cache(self):
        self.parser.return_value = None
        result = server.add_game(123)
        self.assertFalse(result['saved'])
        self.assertEqual(result['stage'], 'save')
        self.build.assert_not_called()
        self.assertEqual(list(self.root.iterdir()), [])


class DeploymentFailureTests(unittest.TestCase):
    def test_failed_upload_is_fatal_but_no_deploy_is_not(self):
        args = SimpleNamespace(no_deploy=False, deploy=False, surge_domain='example.surge.sh')
        with patch('baseball_processor.main.deploy_to_surge', return_value=False) as deploy:
            with self.assertRaisesRegex(RuntimeError, 'deployment failed'):
                _maybe_deploy_to_surge('site.html', args)
            args.no_deploy = True
            self.assertFalse(_maybe_deploy_to_surge('site.html', args))
            deploy.assert_called_once()

    def test_invalid_input_returns_nonzero_exit(self):
        result = subprocess.run(['python3', '-m', 'baseball_processor', '/nonexistent/audit-input', '--no-deploy'],
                                capture_output=True, text=True)
        self.assertNotEqual(result.returncode, 0)
        self.assertIn('Input path does not exist', result.stdout + result.stderr)

    def test_missing_data_or_referenced_chunk_never_uploads(self):
        from baseball_processor.main import deploy_to_surge
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            html = root / 'index.html'
            html.write_text('<html></html>')
            with patch('shutil.which', return_value='/usr/bin/surge'), patch('subprocess.run') as upload:
                self.assertFalse(deploy_to_surge(str(html), 'example.surge.sh'))
                (root / 'data.json').write_text(json.dumps({'__dataSidecars': [{'path': 'data-games-1.json'}]}))
                self.assertFalse(deploy_to_surge(str(html), 'example.surge.sh'))
                upload.assert_not_called()
