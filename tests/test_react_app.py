import unittest

from baseball_processor.website.react_app import ReactComponents
from baseball_processor.website.templates import HTMLTemplate


class ReactAppTests(unittest.TestCase):
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
