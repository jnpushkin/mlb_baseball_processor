from baseball_processor.scrapers.awards_scraper import (
    AWARD_PAGES_BY_KEY,
    enrich_entry_names,
    parse_awards_html,
)


def test_parse_standard_award_table_extracts_bref_id_and_stats():
    html = """
    <table id="mvp">
      <thead>
        <tr>
          <th data-stat="year_ID">Year</th>
          <th data-stat="lg_ID">Lg</th>
          <th data-stat="player">Name</th>
          <th data-stat="team_ID">Tm</th>
          <th data-stat="WAR">WAR</th>
        </tr>
      </thead>
      <tbody>
        <tr>
          <th data-stat="year_ID">2025</th>
          <td data-stat="lg_ID"><a href="/leagues/AL/2025.shtml">AL</a></td>
          <td data-stat="player"><a href="/players/j/judgeaa01.shtml">Aaron Judge</a></td>
          <td data-stat="team_ID"><a href="/teams/NYY/2025.shtml">NYY</a></td>
          <td data-stat="WAR">9.6</td>
        </tr>
      </tbody>
    </table>
    """

    entries, tables = parse_awards_html(html, AWARD_PAGES_BY_KEY["mvp"])

    assert len(entries) == 1
    assert tables[0]["entries"] == 1
    assert entries[0]["award"] == "Most Valuable Player"
    assert entries[0]["year"] == 2025
    assert entries[0]["league"] == "AL"
    assert entries[0]["player_id"] == "judgeaa01"
    assert entries[0]["team"] == "NYY"
    assert entries[0]["stats"]["WAR"] == "9.6"


def test_parse_position_grid_table_creates_one_entry_per_player_cell():
    html = """
    <table id="award_grid">
      <caption>List of Gold Glove Winners Table</caption>
      <thead>
        <tr>
          <th>Year</th>
          <th>P</th>
          <th>OF</th>
          <th>Team</th>
        </tr>
      </thead>
      <tbody>
        <tr>
          <td><a href="/leagues/NL/2025.shtml">2025 NL</a></td>
          <td><span><a href="/players/w/webblo01.shtml" title="Logan Webb, SFG 34 GS">Webb</a> · <span class="desc">SFG</span></span></td>
          <td><span>LF <a href="/players/h/happia01.shtml">Happ</a> · <span class="desc">CHC</span></span></td>
          <td><a href="/teams/CHC/2025.shtml">Chicago Cubs</a></td>
        </tr>
      </tbody>
    </table>
    """

    entries, _ = parse_awards_html(html, AWARD_PAGES_BY_KEY["gold_glove_nl"])

    assert [entry["player_id"] for entry in entries] == ["webblo01", "happia01"]
    assert entries[0]["name"] == "Logan Webb"
    assert entries[0]["position"] == "P"
    assert entries[1]["award_detail"] == "OF"
    assert entries[1]["position"] == "LF"
    assert entries[1]["team"] == "CHC"


def test_parse_malformed_titleist_table_uses_nested_rows_without_duplicates():
    html = """
    <table id="titleist">
      <thead>
        <tr><th>Year</th><th>League</th><th>Batting Champ</th><th></th></tr>
      </thead>
      <tbody>
        <tr>
          <td>2025</td>
          <td><a href="/leagues/AL/2025.shtml">AL</a></td>
          <td><a href="/players/j/judgeaa01.shtml">Aaron Judge</a></td>
          <td>NYY 152 G .331/.457/.688</td>
          <tr>
            <td></td>
            <td><a href="/leagues/NL/2025.shtml">NL</a></td>
            <td><a href="/players/t/turnetr01.shtml">Trea Turner</a></td>
            <td>PHI 141 G .304/.355/.457</td>
          </tr>
        </tr>
      </tbody>
    </table>
    """

    entries, _ = parse_awards_html(html, AWARD_PAGES_BY_KEY["batting-titles"])

    assert len(entries) == 2
    assert [entry["year"] for entry in entries] == [2025, 2025]
    assert [entry["league"] for entry in entries] == ["AL", "NL"]
    assert [entry["player_id"] for entry in entries] == ["judgeaa01", "turnetr01"]


def test_parse_triple_crown_player_header_as_grid_table():
    html = """
    <table id="triple_crowns_b">
      <caption>Batting Triple Crowns Table</caption>
      <thead><tr><th>Year Lg</th><th>Player</th><th>Team/(BA, HR, RBI)</th></tr></thead>
      <tbody>
        <tr>
          <td><a href="/leagues/AL/2012.shtml">2012 AL</a></td>
          <td><a href="/players/c/cabremi01.shtml">Miguel Cabrera</a></td>
          <td>DET .330, 44 HR, 139 RBI</td>
        </tr>
      </tbody>
    </table>
    """

    entries, _ = parse_awards_html(html, AWARD_PAGES_BY_KEY["triple_crowns"])

    assert len(entries) == 1
    assert entries[0]["year"] == 2012
    assert entries[0]["league"] == "AL"
    assert entries[0]["award_detail"] == "Batting Triple Crowns"


def test_parse_multi_winner_cell_ignores_non_person_links():
    html = """
    <table id="tsn">
      <thead>
        <tr>
          <th>Year</th>
          <th>Major League Player of the Year</th>
          <th>AL TSN Pitcher of the Year</th>
        </tr>
      </thead>
      <tr>
        <td>2024</td>
        <td><a href="/players/o/ohtansh01.shtml">Shohei Ohtani</a></td>
        <td>
          <a href="/players/c/claseem01.shtml">Emmanuel Clase</a> (reliever)
          <a href="/players/gl.fcgi?id=claseem01&t=p&year=2024">games</a>
          <a href="/players/s/skubata01.shtml">Tarik Skubal</a> (starter)
        </td>
      </tr>
    </table>
    """

    entries, _ = parse_awards_html(html, AWARD_PAGES_BY_KEY["tsn"])

    assert [entry["player_id"] for entry in entries] == ["ohtansh01", "claseem01", "skubata01"]
    assert entries[1]["award_detail"] == "AL TSN Pitcher of the Year"
    assert entries[2]["notes"] == "Emmanuel Clase (reliever) games Tarik Skubal (starter)"


def test_title_stats_do_not_replace_display_name():
    html = """
    <table id="award_grid">
      <thead><tr><th>Year</th><th>OF</th></tr></thead>
      <tbody>
        <tr>
          <td>2025 AL</td>
          <td>CF <a href="/players/r/rafaece01.shtml" title="BOS 148 GS 0.980%, 5 E">Rafaela</a> · <span class="desc">BOS</span></td>
        </tr>
      </tbody>
    </table>
    """

    entries, _ = parse_awards_html(html, AWARD_PAGES_BY_KEY["gold_glove_al"])

    assert entries[0]["name"] == "Rafaela"
    assert entries[0]["position"] == "CF"


def test_parse_dotted_bref_player_id():
    html = """
    <table id="branch_rickey">
      <thead><tr><th>Year</th><th>Branch Rickey Award Winner</th></tr></thead>
      <tbody>
        <tr>
          <td>2012</td>
          <td><a href="/players/d/dicker.01.shtml">R.A. Dickey</a></td>
        </tr>
      </tbody>
    </table>
    """

    entries, _ = parse_awards_html(html, AWARD_PAGES_BY_KEY["branch_rickey"])

    assert len(entries) == 1
    assert entries[0]["year"] == 2012
    assert entries[0]["name"] == "R.A. Dickey"
    assert entries[0]["player_id"] == "dicker.01"


def test_enrich_entry_names_uses_local_debut_reference(tmp_path):
    (tmp_path / "2025 MLB Debuts.csv").write_text(
        "Name,Name-additional\nCeddanne Rafaela,rafaece01\n",
        encoding="utf-8",
    )
    entries = [{
        "entity_type": "player",
        "entity_id": "rafaece01",
        "player_id": "rafaece01",
        "name": "Rafaela",
    }]

    enriched = enrich_entry_names(entries, references_dir=tmp_path)

    assert enriched[0]["name"] == "Ceddanne Rafaela"
