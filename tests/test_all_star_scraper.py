from baseball_processor.scrapers.all_star_scraper import (
    parse_all_star_game_html,
    parse_all_star_index,
)


def test_parse_all_star_index_finds_numbered_games():
    html = """
    <a href="/allstar/1962-allstar-game-2.shtml">1962 Game 2</a>
    <a href="/allstar/1962-allstar-game-1.shtml">1962 Game 1</a>
    <a href="/allstar/2025-allstar-game.shtml">2025</a>
    <a href="/allstar/2025-allstar-game.shtml">July 15th</a>
    """

    games = parse_all_star_index(html)

    assert [game["gameKey"] for game in games] == ["1962-2", "1962", "2025"]
    assert games[0]["label"] == "1962 All-Star Game 2"
    assert games[1]["label"] == "1962 All-Star Game"


def test_parse_all_star_roster_tables_skip_managers_and_dedupe_starter_pitchers():
    game = {
        "year": 2025,
        "gameNumber": 1,
        "gameKey": "2025",
        "label": "2025 All-Star Game",
        "url": "https://www.baseball-reference.com/allstar/2025-allstar-game.shtml",
    }
    html = """
    <table>
      <caption>AL All-Stars</caption>
      <tr><td>1</td><td><a href="/players/t/torregl01.shtml">Gleyber Torres</a></td><td>2B</td></tr>
      <tr><td></td><td><a href="/players/d/dicker.01.shtml">R.A. Dickey</a></td><td>P</td></tr>
      <tr><td></td><td><strong>Manager</strong></td><td></td></tr>
      <tr><td></td><td><a href="/managers/booneaa01.shtml">Aaron Boone</a></td><td></td></tr>
      <tr><td></td><td><strong>Reserves</strong></td><td></td></tr>
      <tr><td></td><td><a href="/players/d/dicker.01.shtml">R.A. Dickey</a></td><td>P</td></tr>
      <tr><td></td><td><a href="/players/r/ramirjo01.shtml">José Ramírez</a></td><td>3B</td></tr>
    </table>
    <table>
      <caption>NL All-Stars Table</caption>
      <tr><td><a href="/players/o/ohtansh01.shtml">Shohei Ohtani</a></td></tr>
    </table>
    """

    participants, tables = parse_all_star_game_html(html, game)

    assert [participant["player_id"] for participant in participants] == ["torregl01", "dicker.01", "ramirjo01"]
    assert [participant["selection"] for participant in participants] == ["Starter", "Starting Pitcher", "Reserve"]
    assert participants[1]["position"] == "P"
    assert participants[1]["league"] == "AL"
    assert tables == [{"caption": "AL All-Stars", "entries": 3}]
