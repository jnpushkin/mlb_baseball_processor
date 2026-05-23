"""
Data serializers for converting DataFrames to JSON format for website.
Complete version with all stats fields and game-by-game data.
"""
import json
from collections import defaultdict
from datetime import datetime
from pathlib import Path
import pandas as pd

from ..engines.all_time_passing_engine import AllTimePassingEngine, find_passings_reverse_lookup, load_gamelogs_cache


def _format_date(date_str):
    """Convert YYYYMMDD to (formatted, sortable) tuple."""
    if not date_str or len(str(date_str)) < 8:
        return "", ""
    d = str(date_str)
    return f"{d[4:6]}/{d[6:8]}/{d[0:4]}", f"{d[0:4]}-{d[4:6]}-{d[6:8]}"


def load_career_firsts_cache():
    """Load the career firsts cache from disk."""
    # Find project root
    current = Path(__file__).resolve()
    project_root = None
    for parent in [current] + list(current.parents):
        if (parent / '.project_root').exists() or (parent / 'baseball_processor').is_dir():
            project_root = parent
            break

    if not project_root:
        project_root = Path.cwd()

    cache_file = project_root / 'cache' / 'career_firsts' / 'career_firsts.json'
    if cache_file.exists():
        try:
            with open(cache_file, 'r') as f:
                return json.load(f)
        except (json.JSONDecodeError, IOError):
            return {}
    return {}


def find_witnessed_career_firsts(raw_games, career_firsts_cache):
    """
    Find career firsts AND career milestones that were witnessed at attended games.

    Returns:
        - witnessed_firsts: List of witnessed firsts/milestones with full details
        - firsts_by_game: Dict mapping game_id to list of firsts/milestones in that game
        - firsts_by_player: Dict mapping player_id to list of firsts/milestones witnessed
    """
    witnessed_firsts = []
    firsts_by_game = {}
    firsts_by_player = {}

    # Build set of attended game IDs (only match on game_id, not date)
    attended_games = {}
    for game in raw_games:
        basic_info = game.get('basic_info', {})
        date_str = basic_info.get('date_yyyymmdd', '')
        home_code = basic_info.get('home_team_code', '')
        game_id = game.get('game_id', f"{home_code}{date_str}0")

        if game_id:
            attended_games[game_id] = {
                'game_id': game_id,
                'home_team': basic_info.get('home_team', ''),
                'away_team': basic_info.get('away_team', ''),
                'venue': basic_info.get('venue', ''),
                'date': basic_info.get('date', ''),
            }

    # Build player name lookup from games
    player_names = {}
    for game in raw_games:
        for side in ['away', 'home']:
            for batter in game.get('batting', {}).get(side, []):
                if batter.get('player_id') and batter.get('name'):
                    player_names[batter['player_id']] = batter['name']
            for pitcher in game.get('pitching', {}).get(side, []):
                if pitcher.get('player_id') and pitcher.get('name'):
                    player_names[pitcher['player_id']] = pitcher['name']

    def add_record(record, game_id_key):
        """Helper to add a record to all indexes."""
        witnessed_firsts.append(record)
        gid = record.get('game_id', game_id_key)
        if gid not in firsts_by_game:
            firsts_by_game[gid] = []
        firsts_by_game[gid].append(record)
        pid = record.get('player_id')
        if pid not in firsts_by_player:
            firsts_by_player[pid] = []
        firsts_by_player[pid].append(record)

    def find_attended_game(game_id):
        """Find attended game, trying M-prefix and doubleheader variants.

        Cached games can be in either MLB API format (M-prefixed, e.g.
        'MSF202604190') or BREF format ('SFN202604190'). Career-firsts
        milestones from the MLB API path always emit M-prefixed IDs, so we
        also try the bare form for lookup compatibility with BREF games.
        """
        if not game_id or len(game_id) < 11:
            return None

        # Build candidates: original + with/without M prefix
        candidates = [game_id]
        if game_id.startswith('M') and len(game_id) >= 12:
            candidates.append(game_id[1:])
        else:
            candidates.append('M' + game_id)

        for cand in candidates:
            # Exact match
            if cand in attended_games:
                return attended_games[cand]
            # Only allow '1'/'2' → '0' fallback (BREF sometimes stores DH games
            # with '0' suffix). NOT '0' → '1'/'2': that direction risks matching
            # the wrong game of a doubleheader for ambiguous single-game IDs.
            base, last_char = cand[:-1], cand[-1]
            if last_char in ('1', '2'):
                if (base + '0') in attended_games:
                    return attended_games[base + '0']

        return None

    # Check each player's career firsts and milestones
    for player_id, data in career_firsts_cache.items():
        player_name = player_names.get(player_id, player_id)

        # Check batting firsts
        for stat, first_info in data.get('batting_firsts', {}).items():
            date = first_info.get('date', '')
            first_game_id = first_info.get('game_id', '')
            game = find_attended_game(first_game_id)
            if game:
                add_record({
                    'player_id': player_id,
                    'player_name': player_name,
                    'milestone': first_info.get('milestone', ''),
                    'stat': stat,
                    'date': date,
                    'date_display': game.get('date', date),
                    'game_id': game.get('game_id', first_game_id),
                    'opponent': first_info.get('opponent', ''),
                    'venue': game.get('venue', ''),
                    'type': 'batting',
                    'category': 'first',
                    'year': first_info.get('year', ''),
                }, first_game_id)

        # Check pitching firsts
        for stat, first_info in data.get('pitching_firsts', {}).items():
            date = first_info.get('date', '')
            first_game_id = first_info.get('game_id', '')
            game = find_attended_game(first_game_id)
            if game:
                add_record({
                    'player_id': player_id,
                    'player_name': player_name,
                    'milestone': first_info.get('milestone', ''),
                    'stat': stat,
                    'date': date,
                    'date_display': game.get('date', date),
                    'game_id': game.get('game_id', first_game_id),
                    'opponent': first_info.get('opponent', ''),
                    'venue': game.get('venue', ''),
                    'type': 'pitching',
                    'category': 'first',
                    'year': first_info.get('year', ''),
                }, first_game_id)

        # Check batting milestones (e.g., 100th HR, 500th hit)
        for stat, milestones_list in data.get('batting_milestones', {}).items():
            for milestone_info in milestones_list:
                date = milestone_info.get('date', '')
                milestone_game_id = milestone_info.get('game_id', '')
                game = find_attended_game(milestone_game_id)
                if game:
                    add_record({
                        'player_id': player_id,
                        'player_name': player_name,
                        'milestone': milestone_info.get('milestone', ''),
                        'milestone_number': milestone_info.get('number', 0),
                        'stat': stat,
                        'date': date,
                        'date_display': game.get('date', date),
                        'game_id': game.get('game_id', milestone_game_id),
                        'opponent': milestone_info.get('opponent', ''),
                        'venue': game.get('venue', ''),
                        'type': 'batting',
                        'category': 'milestone',
                        'year': milestone_info.get('year', ''),
                        'career_total_after': milestone_info.get('career_total_after', 0),
                    }, milestone_game_id)

        # Check pitching milestones
        for stat, milestones_list in data.get('pitching_milestones', {}).items():
            for milestone_info in milestones_list:
                date = milestone_info.get('date', '')
                milestone_game_id = milestone_info.get('game_id', '')
                game = find_attended_game(milestone_game_id)
                if game:
                    add_record({
                        'player_id': player_id,
                        'player_name': player_name,
                        'milestone': milestone_info.get('milestone', ''),
                        'milestone_number': milestone_info.get('number', 0),
                        'stat': stat,
                        'date': date,
                        'date_display': game.get('date', date),
                        'game_id': game.get('game_id', milestone_game_id),
                        'opponent': milestone_info.get('opponent', ''),
                        'venue': game.get('venue', ''),
                        'type': 'pitching',
                        'category': 'milestone',
                        'year': milestone_info.get('year', ''),
                        'career_total_after': milestone_info.get('career_total_after', 0),
                    }, milestone_game_id)

    # Deduplicate: pitchers who bat can have same milestone in both batting and pitching
    # Keep pitching version for pitchers (more relevant), batting for position players
    seen = {}
    for record in witnessed_firsts:
        key = (record.get('player_id'), record.get('milestone'), record.get('game_id'))
        if key not in seen:
            seen[key] = record
        else:
            # If we already have this milestone, prefer pitching type for game-based milestones
            existing = seen[key]
            if record.get('type') == 'pitching' and 'Game' in record.get('milestone', ''):
                seen[key] = record

    witnessed_firsts = list(seen.values())

    # Rebuild by_game and by_player dicts after deduplication
    firsts_by_game = {}
    firsts_by_player = {}
    for record in witnessed_firsts:
        gid = record.get('game_id')
        if gid:
            if gid not in firsts_by_game:
                firsts_by_game[gid] = []
            firsts_by_game[gid].append(record)
        pid = record.get('player_id')
        if pid:
            if pid not in firsts_by_player:
                firsts_by_player[pid] = []
            firsts_by_player[pid].append(record)

    # Sort witnessed firsts by date (most recent first), then by milestone importance
    def sort_key(x):
        date = x.get('date', '')
        # Prioritize milestones by number (higher = more important)
        milestone_num = x.get('milestone_number', 0)
        return (date, milestone_num)

    witnessed_firsts.sort(key=sort_key, reverse=True)

    return witnessed_firsts, firsts_by_game, firsts_by_player


def find_witnessed_career_lasts(raw_games, career_firsts_cache):
    """Career-LAST stat events that happened at attended games.

    Mirror of find_witnessed_career_firsts but for the other end of careers.
    Only retired players contribute (active players' "last hit" still moves).
    """
    attended_games = {}
    for game in raw_games:
        basic_info = game.get('basic_info', {})
        date_str = basic_info.get('date_yyyymmdd', '')
        home_code = basic_info.get('home_team_code', '')
        game_id = game.get('game_id', f"{home_code}{date_str}0")
        if game_id:
            attended_games[game_id] = {
                'home_team': basic_info.get('home_team', ''),
                'away_team': basic_info.get('away_team', ''),
                'venue': basic_info.get('venue', ''),
                'date': basic_info.get('date', ''),
            }

    player_names = {}
    for game in raw_games:
        for side in ('away', 'home'):
            for batter in game.get('batting', {}).get(side, []):
                if batter.get('player_id') and batter.get('name'):
                    player_names[batter['player_id']] = batter['name']
            for pitcher in game.get('pitching', {}).get(side, []):
                if pitcher.get('player_id') and pitcher.get('name'):
                    player_names[pitcher['player_id']] = pitcher['name']

    def find_attended_game(game_id):
        if not game_id or len(game_id) < 11:
            return None
        candidates = [game_id]
        if game_id.startswith('M') and len(game_id) >= 12:
            candidates.append(game_id[1:])
        else:
            candidates.append('M' + game_id)
        for cand in candidates:
            if cand in attended_games:
                return attended_games[cand]
            base, last_char = cand[:-1], cand[-1]
            if last_char in ('1', '2') and (base + '0') in attended_games:
                return attended_games[base + '0']
        return None

    witnessed = []
    for player_id, data in (career_firsts_cache or {}).items():
        if not data.get('is_retired'):
            continue
        player_name = player_names.get(player_id, data.get('player_name', player_id))
        for last_type, type_label in (('batting_lasts', 'batting'), ('pitching_lasts', 'pitching')):
            for stat, last_info in (data.get(last_type) or {}).items():
                game_id = last_info.get('game_id', '')
                attended = find_attended_game(game_id)
                if not attended:
                    continue
                witnessed.append({
                    'player_id': player_id,
                    'player_name': player_name,
                    'milestone': last_info.get('milestone', ''),
                    'stat': stat,
                    'date': last_info.get('date', ''),
                    'date_display': _format_yyyymmdd(last_info.get('date', '')),
                    'game_id': game_id,
                    'opponent': last_info.get('opponent', ''),
                    'venue': attended.get('venue', ''),
                    'year': last_info.get('year'),
                    'value': last_info.get('value_in_game'),
                    'type': type_label,
                })

    witnessed.sort(key=lambda r: (r.get('date') or '', r.get('player_name') or ''), reverse=True)
    return witnessed


def _format_yyyymmdd(date_str):
    if not date_str or len(date_str) != 8 or not date_str.isdigit():
        return date_str or ''
    return f"{date_str[4:6]}/{date_str[6:8]}/{date_str[0:4]}"


def find_all_time_passings(witnessed_firsts: list, career_firsts_cache: dict, raw_games: list = None) -> tuple[list, dict]:
    """
    Find all-time list passings for witnessed career milestones.

    Uses two approaches:
    1. Check witnessed milestones against leaderboards (original approach)
    2. Reverse lookup: For each player on leaderboards, check if you attended
       games where they climbed the list (catches more passings)

    Args:
        witnessed_firsts: List of witnessed career milestones
        career_firsts_cache: Full career firsts cache with career_totals
        raw_games: List of raw game dicts (for reverse lookup)

    Returns:
        Tuple of:
        - all_passings: List of all passing events
        - passings_by_game: Dict mapping game_id to list of passings
    """
    all_passings = []
    passings_by_game = {}

    # Initialize the engine (loads leaderboard JSON files)
    try:
        engine = AllTimePassingEngine()
    except Exception as e:
        print(f"      Warning: Could not initialize AllTimePassingEngine: {e}")
        return all_passings, passings_by_game

    # Check if we have any leaderboards loaded
    if not engine.leaderboards:
        # No leaderboard files available yet - that's OK, just return empty
        return all_passings, passings_by_game

    # Reverse lookup from leaderboards (uses gamelogs cache if available)
    if raw_games:
        gamelogs_cache = load_gamelogs_cache()
        reverse_passings = find_passings_reverse_lookup(engine, raw_games, career_firsts_cache, gamelogs_cache)
        all_passings.extend(reverse_passings)

    # Deduplicate: A player can only pass another player ONCE per stat
    # First sort by date ascending so we process earliest occurrences first
    all_passings.sort(key=lambda x: (x.get('date', ''), x.get('new_rank', 999)))

    seen_passings = set()  # (player_id, stat, passed_player_id, tied_or_passed) tuples
    seen_games = set()  # (player_id, stat, game_id) to avoid duplicate game entries
    unique_passings = []

    for p in all_passings:
        game_key = (p.get('player_id', ''), p.get('stat', ''), p.get('game_id', ''))
        if game_key in seen_games:
            continue

        # Filter passed_players: allow both "tied" and "passed" events for the same player
        filtered_passed = []
        for passed in p.get('passed_players', []):
            is_tied = passed.get('value', 0) == p.get('new_value', 0)
            passing_key = (p.get('player_id', ''), p.get('stat', ''), passed.get('player_id', ''), 'tied' if is_tied else 'passed')
            if passing_key not in seen_passings:
                seen_passings.add(passing_key)
                filtered_passed.append(passed)

        # Only include this passing if there are still players being passed for the first time
        if filtered_passed:
            p = p.copy()
            p['passed_players'] = filtered_passed
            p['total_passed'] = len(filtered_passed)
            unique_passings.append(p)
            seen_games.add(game_key)

    # Sort by date descending for display (most recent first), then by rank
    unique_passings.sort(key=lambda x: (x.get('date', ''), -x.get('new_rank', 999)), reverse=True)

    # Index by game
    for passing in unique_passings:
        game_id = passing.get('game_id', '')
        if game_id:
            if game_id not in passings_by_game:
                passings_by_game[game_id] = []
            passings_by_game[game_id].append(passing)

    return unique_passings, passings_by_game


class DataSerializer:
    """Convert baseball DataFrames to JSON-serializable format."""
    
    def serialize_all_data(self, data):
        """Convert all data structures to JSON format."""
        print("   🔄 Serializing data for website...")

        # Store reference to data for use in other methods
        self.data = data

        # Get the raw games for game-by-game breakdown
        raw_games = data.get('_raw_games', [])

        # Load career firsts and find witnessed ones
        career_firsts_cache = load_career_firsts_cache()
        witnessed_firsts, firsts_by_game, firsts_by_player = find_witnessed_career_firsts(
            raw_games, career_firsts_cache
        )
        self._firsts_by_game = firsts_by_game
        self._firsts_by_player = firsts_by_player

        # Career-lasts: same cache, retired players only.
        witnessed_lasts = find_witnessed_career_lasts(raw_games, career_firsts_cache)

        # Find all-time list passings from witnessed milestones
        all_time_passings, passings_by_game = find_all_time_passings(
            witnessed_firsts, career_firsts_cache, raw_games
        )

        # Count games by type
        game_type_counts = {'regular': 0, 'postseason': 0, 'spring': 0, 'allstar': 0}
        for game in raw_games:
            game_type = game.get('basic_info', {}).get('game_type', 'regular')
            if game_type in game_type_counts:
                game_type_counts[game_type] += 1
            else:
                game_type_counts['regular'] += 1

        # Load NCAA cross-reference data if available
        ncaa_cross_ref = {}
        try:
            from ..exporters.shared_players import load_ncaa_processor_export, build_ncaa_cross_reference
            ncaa_export = load_ncaa_processor_export()
            if ncaa_export:
                ncaa_cross_ref = build_ncaa_cross_reference(ncaa_export)
        except Exception as e:
            print(f"      Note: NCAA cross-reference not available: {e}")

        json_data = {
            "summary": self._serialize_summary(data.get('summary_rows', [])),
            "milestones": self._serialize_milestones(data.get('milestones', {})),
            "players": self._serialize_players(data.get('hitters')),
            "pitchers": self._serialize_pitchers(data.get('pitchers')),
            "playersWithoutStats": self._serialize_players_without_stats(data.get('players_without_stats')),
            "hallOfFamers": self._serialize_hall_of_famers(data.get('hofers_seen')),
            "rispPerformance": self._serialize_situational_table(
                self._call_tracker_dataframe(data.get('situation_tracker'), 'create_risp_dataframe', min_ab=5),
                {
                    "Player ID": "playerId",
                    "Name": "name",
                    "RISP AB": "ab",
                    "RISP H": "h",
                    "RISP AVG": "avg",
                    "RISP HR": "hr",
                },
                rate_fields={"avg": 3},
            ),
            "twoOutPerformance": self._serialize_situational_table(
                self._call_tracker_dataframe(data.get('situation_tracker'), 'create_two_out_dataframe', min_ab=5),
                {
                    "Player ID": "playerId",
                    "Name": "name",
                    "2-Out AB": "ab",
                    "2-Out H": "h",
                    "2-Out AVG": "avg",
                    "2-Out HR": "hr",
                },
                rate_fields={"avg": 3},
            ),
            "rispTwoOutPerformance": self._serialize_situational_table(
                self._call_tracker_dataframe(data.get('situation_tracker'), 'create_clutch_situations_dataframe', min_ab=3),
                {
                    "Player ID": "playerId",
                    "Name": "name",
                    "RISP+2Out AB": "ab",
                    "RISP+2Out H": "h",
                    "RISP+2Out AVG": "avg",
                    "RISP+2Out HR": "hr",
                },
                rate_fields={"avg": 3},
            ),
            "basesLoaded": self._serialize_situational_table(
                self._call_tracker_dataframe(data.get('situation_tracker'), 'create_bases_loaded_dataframe'),
                {
                    "Player ID": "playerId",
                    "Name": "name",
                    "Grand Slams": "grandSlams",
                },
            ),
            "lateClose": self._serialize_situational_table(
                self._call_tracker_dataframe(data.get('situation_tracker'), 'create_late_close_dataframe', min_ab=5),
                {
                    "Player ID": "playerId",
                    "Name": "name",
                    "Late/Close AB": "ab",
                    "Late/Close H": "h",
                    "Late/Close AVG": "avg",
                    "Late/Close HR": "hr",
                },
                rate_fields={"avg": 3},
            ),
            "wpaLeaders": self._serialize_situational_table(
                self._call_tracker_dataframe(data.get('saber_tracker'), 'create_wpa_dataframe'),
                {
                    "Player ID": "playerId",
                    "Name": "name",
                    "Games": "games",
                    "Total WPA": "totalWpa",
                    "Avg WPA": "avgWpa",
                    "Positive WPA": "positiveWpa",
                    "Negative WPA": "negativeWpa",
                    "Best Game WPA": "bestGameWpa",
                    "Best Game ID": "bestGameId",
                    "Worst Game WPA": "worstGameWpa",
                    "Worst Game ID": "worstGameId",
                },
                rate_fields={
                    "totalWpa": 3,
                    "avgWpa": 3,
                    "positiveWpa": 3,
                    "negativeWpa": 3,
                    "bestGameWpa": 3,
                    "worstGameWpa": 3,
                },
            ),
            "defensiveLeaders": self._serialize_situational_table(
                self._call_tracker_dataframe(data.get('defense_tracker'), 'create_defensive_leaders_dataframe', min_games=1),
                {
                    "Player ID": "playerId",
                    "Name": "name",
                    "Games": "games",
                    "PO": "putouts",
                    "A": "assists",
                    "E": "errors",
                    "TC": "totalChances",
                    "Fielding %": "fieldingPct",
                    "Positions": "positions",
                },
                rate_fields={"fieldingPct": 3},
            ),
            "lineupAnalysis": self._serialize_situational_table(
                self._call_tracker_dataframe(data.get('defense_tracker'), 'create_lineup_analysis_dataframe', min_games=1),
                {
                    "Player ID": "playerId",
                    "Name": "name",
                    "Games": "games",
                    "Most Common Spot": "mostCommonSpot",
                    "Times in Spot": "timesInSpot",
                    "Pinch Hits": "pinchHits",
                },
            ),
            "lineupMatrix": self._serialize_lineup_matrix(
                self._call_tracker_dataframe(data.get('defense_tracker'), 'create_lineup_position_matrix'),
                self._call_tracker_dataframe(data.get('defense_tracker'), 'create_lineup_analysis_dataframe', min_games=1),
            ),
            "weatherTiming": self._serialize_weather_timing(data.get('weather_tracker')),
            "teams": self._serialize_teams(data.get('team_records')),
            "games": self._serialize_games(data.get('game_log'), data.get('_raw_games', [])),
            "stadiums": self._serialize_stadiums(data.get('stadiums')),
            "orioles": self._serialize_orioles(data.get('ori_stads')),
            "debuts": self._serialize_debuts(data.get('mlb_debut_rows', [])),
            "finalGames": self._serialize_final_games(data.get('final_game_rows', [])),
            "signatureHRs": self._serialize_signature_hrs(data.get('df_splash')),
            "matchupMatrix": self._serialize_matchup_matrix(data.get('df_matchups')),
            "playerGames": self._serialize_player_games(raw_games),
            "pitcherGames": self._serialize_pitcher_games(raw_games),
            "divisionChecklist": self._serialize_division_checklist(),
            "companionData": self._serialize_companions(),
            "careerFirsts": witnessed_firsts,
            "careerLasts": witnessed_lasts,
            "careerFirstsByGame": firsts_by_game,
            "careerFirstsByPlayer": firsts_by_player,
            "allTimePassings": all_time_passings,
            "allTimePassingsByGame": passings_by_game,
            "gameTypeCounts": game_type_counts,
            "ncaaCrossRef": ncaa_cross_ref,
            "absPlayerStats": self._serialize_abs_player_stats(raw_games),
            "umpireLog": self._serialize_umpire_log(raw_games),
            "jerseyLog": self._serialize_jersey_log(raw_games),
            "firstRoundDraftPicks": self._serialize_first_round_draft_picks(raw_games),
            "playerBios": self._load_player_bios(),
            "generatedAt": datetime.now().strftime("%B %d, %Y at %I:%M %p"),
        }

        # Annotate player/pitcher games with career/season high flags
        self._annotate_career_highs(json_data)

        counts = [
            f"Summary: {len(json_data['summary'])}",
            f"Milestones: {len(json_data['milestones'])}",
            f"Players: {len(json_data['players'])}",
            f"Pitchers: {len(json_data['pitchers'])}",
            f"HallOfFamers: {len(json_data['hallOfFamers'])}",
            f"Situational: {sum(len(json_data[key]) for key in ['rispPerformance', 'twoOutPerformance', 'rispTwoOutPerformance', 'basesLoaded', 'lateClose'])}",
            f"WPA: {len(json_data['wpaLeaders'])}",
            f"Defense/Lineup: {sum(len(json_data[key]) for key in ['defensiveLeaders', 'lineupAnalysis', 'lineupMatrix'])}",
            f"WeatherTiming: {len(json_data['weatherTiming'])}",
            f"Games: {len(json_data['games'])}",
            f"PlayerGames: {len(json_data['playerGames'])}",
            f"PitcherGames: {len(json_data['pitcherGames'])}",
            f"CareerFirsts: {len(witnessed_firsts)}",
            f"AllTimePassings: {len(all_time_passings)}",
        ]
        print(f"      {', '.join(counts)}")

        return json_data
    
    def _serialize_summary(self, summary_rows):
        """Convert summary statistics to JSON."""
        if not summary_rows:
            return []
        
        return [
            {
                "record": str(row.get("Record", "")),
                "value": str(row.get("Value", "")),
                "detail": str(row.get("Detail", "")),
                "score": str(row.get("Score", "")),
                "gameIds": str(row.get("GameIDs", ""))
            }
            for row in summary_rows
        ]
    
    # Milestone types to exclude from website (trivial/removed)
    EXCLUDED_MILESTONE_TYPES = {
        # Batting - too common or low tier
        '3+ Hit Games', '4+ Walk Games', 'Perfect Batting Games',
        '3+ Run Games', '4+ Run Games', '2+ XBH Games', '8+ Total Bases',
        'Multi-2B Games',
        # Pitching - routine occurrences
        '8+ K Games', 'Saves', 'Wins', 'Efficient Starts',
        'No-Walk Starts', 'High K Low BB',
        '7-Inning Shutouts', 'Dominant Starts', '3 Pitch Innings',
    }

    def _serialize_milestones(self, milestones_dict):
        """Convert all milestone DataFrames to combined JSON list."""
        all_milestones = []

        if not milestones_dict:
            return all_milestones

        for milestone_type, df in milestones_dict.items():
            if df is None or df.empty:
                continue
            if milestone_type in self.EXCLUDED_MILESTONE_TYPES:
                continue
            
            df_sorted = df.copy()
            df_sorted['_date_sort'] = pd.to_datetime(df_sorted['Date'], errors='coerce')
            df_sorted = df_sorted.sort_values('_date_sort', ascending=False)
            
            for _, row in df_sorted.iterrows():
                milestone = {
                    "type": milestone_type,
                    "date": str(row.get("Date", "")),
                    "player": str(row.get("Player", "")),
                    "playerId": str(row.get("Player ID", "")) if "Player ID" in row else "",
                    "team": str(row.get("Team", "")),
                    "opponent": str(row.get("Opponent", "")),
                    "gameId": str(row.get("GameID", ""))
                }
                
                # Batting milestones
                batting_types = [
                    "3+ HR Games", "Multi-HR Games", "Cycles",
                    "5+ Hit Games", "4+ Hit Games", "3+ Hit Games",
                    "6+ RBI Games", "5+ RBI Games", "4+ RBI Games",
                    "Multi-2B Games", "Multi-3B Games", "Multi-SB Games",
                    "4+ Walk Games", "Perfect Batting Games", "Golden Sombreros",
                    "4+ Run Games", "3+ Run Games", "2+ XBH Games", "8+ Total Bases"
                ]

                # Pitching milestones
                pitching_types = [
                    "Complete Games", "Shutouts", "No-Hitters", "Perfect Games",
                    "Quality Starts", "15+ K Games", "12+ K Games", "10+ K Games", "8+ K Games",
                    "Maddux Games", "7-Inning Shutouts", "Low-Hit CG",
                    "One-Hitters", "Two-Hitters", "CGSO No Walks", "High K Low BB",
                    "Saves", "Wins", "Efficient Starts", "Dominant Starts",
                    "No-Walk Starts", "Complete Games & Shutouts"
                ]

                if milestone_type == "Consecutive HR Instances":
                    players = str(row.get("Players", ""))
                    hr_count = int(row.get("HR Count", 0)) if pd.notna(row.get("HR Count")) else 0
                    inning = str(row.get("Inning", ""))
                    milestone.update({
                        "player": players,
                        "detail": f"{hr_count} consecutive HRs in {inning}: {players}"
                    })

                elif milestone_type in batting_types:
                    hr = int(row.get("HR", 0)) if pd.notna(row.get("HR")) else 0
                    h = int(row.get("H", 0)) if pd.notna(row.get("H")) else 0
                    rbi = int(row.get("RBI", 0)) if pd.notna(row.get("RBI")) else 0
                    doubles = int(row.get("2B", 0)) if pd.notna(row.get("2B")) else 0
                    triples = int(row.get("3B", 0)) if pd.notna(row.get("3B")) else 0
                    runs = int(row.get("R", 0)) if pd.notna(row.get("R")) else 0
                    bb = int(row.get("BB", 0)) if pd.notna(row.get("BB")) else 0
                    sb = int(row.get("SB", 0)) if pd.notna(row.get("SB")) else 0
                    milestone.update({
                        "hr": hr, "h": h, "rbi": rbi, "2b": doubles, "3b": triples,
                        "r": runs, "bb": bb, "sb": sb
                    })
                    # Use Detail column if present, otherwise construct detail
                    if "Detail" in row and pd.notna(row.get("Detail")):
                        milestone["detail"] = str(row.get("Detail", ""))
                    else:
                        milestone["detail"] = f"{h} H ({doubles} 2B, {triples} 3B, {hr} HR), {rbi} RBI"

                elif milestone_type in pitching_types:
                    ip = str(row.get("IP", "0.0"))
                    so = int(row.get("SO", 0)) if pd.notna(row.get("SO")) else 0
                    h = int(row.get("H", 0)) if pd.notna(row.get("H")) else 0
                    er = int(row.get("ER", 0)) if pd.notna(row.get("ER")) else 0
                    bb = int(row.get("BB", 0)) if pd.notna(row.get("BB")) else 0
                    r = int(row.get("R", 0)) if pd.notna(row.get("R")) else 0
                    pitches = row.get("Pitches", "?")
                    milestone.update({
                        "ip": ip, "so": so, "h": h, "er": er, "bb": bb, "r": r, "pitches": pitches
                    })
                    # Use Detail column if present, otherwise construct detail
                    if "Detail" in row and pd.notna(row.get("Detail")):
                        milestone["detail"] = str(row.get("Detail", ""))
                    else:
                        milestone["detail"] = f"{ip} IP, {h} H, {er} ER, {bb} BB, {so} SO"

                elif milestone_type in ["3 Strikeout Innings", "Immaculate Innings"]:
                    inning = str(row.get("Inning", ""))
                    batters = str(row.get("Batters Struck Out", ""))
                    milestone.update({
                        "inning": inning, "batters": batters,
                        "detail": f"{inning} - {batters}"
                    })

                elif "Detail" in row and pd.notna(row.get("Detail")):
                    milestone["detail"] = str(row.get("Detail", ""))
                else:
                    milestone["detail"] = ""
                
                if pd.notna(row.get('_date_sort')):
                    milestone['_dateSort'] = row['_date_sort'].strftime('%Y-%m-%d')
                
                all_milestones.append(milestone)
        
        all_milestones.sort(key=lambda x: x.get('_dateSort', ''), reverse=True)
        return all_milestones
    
    def _serialize_players(self, df):
        """Convert ALL hitters DataFrame to JSON with complete stats and date range."""
        if df is None or df.empty:
            return []

        players = []
        for _, row in df.iterrows():
            try:
                game_ids = str(row.get("GameIDs", ""))
                first_date, last_date = self._extract_date_range_from_gameids(game_ids)

                player_data = {
                    "name": str(row.get("Name", "")),
                    "playerId": str(row.get("Player ID", "")),
                    "team": str(row.get("Team", "")),
                    "games": int(row.get("G", 0)),
                    "ab": int(row.get("AB", 0)),
                    "pa": int(row.get("PA", 0)),
                    "h": int(row.get("H", 0)),
                    "avg": f"{float(row.get('AVG', 0)):.3f}",
                    "r": int(row.get("R", 0)),
                    "rbi": int(row.get("RBI", 0)),
                    "hr": int(row.get("HR", 0)),
                    "doubles": int(row.get("2B", 0)),
                    "triples": int(row.get("3B", 0)),
                    "sb": int(row.get("SB", 0)),
                    "cs": int(row.get("CS", 0)),
                    "bb": int(row.get("BB", 0)),
                    "so": int(row.get("SO", 0)),
                    "hbp": int(row.get("HBP", 0)),
                    "gidp": int(row.get("GIDP", 0)),
                    "tb": int(row.get("TB", 0)),
                    "xbh": int(row.get("XBH", 0)),
                    "obp": f"{float(row.get('OBP', 0)):.3f}",
                    "slg": f"{float(row.get('SLG', 0)):.3f}",
                    "ops": f"{float(row.get('OPS', 0)):.3f}",
                    "firstGame": first_date,
                    "lastGame": last_date,
                }

                # Add per-game-type stats
                for gt in ['spring', 'regular', 'postseason']:
                    gt_g = int(row.get(f"{gt}_G", 0)) if f"{gt}_G" in row else 0
                    gt_ab = int(row.get(f"{gt}_AB", 0)) if f"{gt}_AB" in row else 0
                    gt_pa = int(row.get(f"{gt}_PA", 0)) if f"{gt}_PA" in row else 0
                    gt_h = int(row.get(f"{gt}_H", 0)) if f"{gt}_H" in row else 0
                    gt_avg = float(row.get(f"{gt}_AVG", 0)) if f"{gt}_AVG" in row else 0.0
                    gt_team = str(row.get(f"{gt}_Team", "")) if f"{gt}_Team" in row else ""

                    player_data[f"{gt}Games"] = gt_g
                    player_data[f"{gt}Ab"] = gt_ab
                    player_data[f"{gt}Pa"] = gt_pa
                    player_data[f"{gt}H"] = gt_h
                    player_data[f"{gt}Avg"] = f"{gt_avg:.3f}"
                    player_data[f"{gt}R"] = int(row.get(f"{gt}_R", 0)) if f"{gt}_R" in row else 0
                    player_data[f"{gt}Rbi"] = int(row.get(f"{gt}_RBI", 0)) if f"{gt}_RBI" in row else 0
                    player_data[f"{gt}Hr"] = int(row.get(f"{gt}_HR", 0)) if f"{gt}_HR" in row else 0
                    player_data[f"{gt}Doubles"] = int(row.get(f"{gt}_2B", 0)) if f"{gt}_2B" in row else 0
                    player_data[f"{gt}Triples"] = int(row.get(f"{gt}_3B", 0)) if f"{gt}_3B" in row else 0
                    player_data[f"{gt}Bb"] = int(row.get(f"{gt}_BB", 0)) if f"{gt}_BB" in row else 0
                    player_data[f"{gt}So"] = int(row.get(f"{gt}_SO", 0)) if f"{gt}_SO" in row else 0
                    player_data[f"{gt}Sb"] = int(row.get(f"{gt}_SB", 0)) if f"{gt}_SB" in row else 0
                    player_data[f"{gt}Team"] = gt_team

                players.append(player_data)
            except (KeyError, TypeError, ValueError) as e:
                # Log error but continue processing other players
                print(f"   Warning: Could not serialize player data: {e}")
                continue
        return players

    def _call_tracker_dataframe(self, tracker, method_name, *args, **kwargs):
        """Call an optional tracker method and return an empty DataFrame on failure."""
        if tracker is None:
            return pd.DataFrame()

        method = getattr(tracker, method_name, None)
        if method is None:
            return pd.DataFrame()

        try:
            return method(*args, **kwargs)
        except Exception as e:
            print(f"   Warning: Could not serialize tracker data from {method_name}: {e}")
            return pd.DataFrame()

    def _serialize_situational_table(self, df, field_map, rate_fields=None):
        """Convert situational hitting DataFrames to compact website rows."""
        if df is None or df.empty:
            return []

        rate_fields = rate_fields or {}

        def clean_value(value, output_key):
            if value is None or pd.isna(value):
                return ""
            if hasattr(value, "item"):
                value = value.item()
            if output_key in rate_fields:
                return f"{float(value):.{rate_fields[output_key]}f}"
            if isinstance(value, float) and value.is_integer():
                return int(value)
            return value

        rows = []
        for _, row in df.iterrows():
            try:
                rows.append({
                    output_key: clean_value(row.get(input_key, ""), output_key)
                    for input_key, output_key in field_map.items()
                })
            except (KeyError, TypeError, ValueError) as e:
                print(f"   Warning: Could not serialize situational hitting row: {e}")
                continue
        return rows

    def _serialize_lineup_matrix(self, matrix_df, lineup_df=None):
        """Convert the lineup position matrix to website rows."""
        if matrix_df is None or matrix_df.empty:
            return []

        player_id_by_name = {}
        if lineup_df is not None and not lineup_df.empty:
            for _, row in lineup_df.iterrows():
                name = row.get("Name", "")
                player_id = row.get("Player ID", "")
                if name and player_id and not pd.isna(name) and not pd.isna(player_id):
                    player_id_by_name[str(name)] = str(player_id)

        rows = []
        for player_name, row in matrix_df.iterrows():
            try:
                name = str(player_name)
                matrix_row = {
                    "name": name,
                    "playerId": player_id_by_name.get(name, ""),
                }
                total = 0
                for spot in range(1, 10):
                    value = row.get(f"#{spot}", 0)
                    count = int(value) if pd.notna(value) else 0
                    matrix_row[f"spot{spot}"] = count
                    total += count
                matrix_row["total"] = total
                rows.append(matrix_row)
            except (KeyError, TypeError, ValueError) as e:
                print(f"   Warning: Could not serialize lineup matrix row: {e}")
                continue
        return rows

    def _serialize_weather_timing(self, weather_tracker):
        """Flatten weather and timing summary stats for the website."""
        if weather_tracker is None:
            return []

        try:
            stats = weather_tracker.get_summary_stats()
        except Exception as e:
            print(f"   Warning: Could not serialize weather/timing data: {e}")
            return []

        def label(value):
            return str(value).replace("_", " ").title()

        rows = []
        for key, value in stats.items():
            category = label(key)
            if isinstance(value, dict):
                for sub_key, sub_value in value.items():
                    rows.append({
                        "category": category,
                        "statistic": label(sub_key),
                        "value": str(sub_value),
                    })
            else:
                rows.append({
                    "category": "Weather & Timing",
                    "statistic": category,
                    "value": str(value),
                })
        return rows

    def _serialize_hall_of_famers(self, df):
        """Convert enhanced Hall of Famers DataFrame to JSON."""
        if df is None or df.empty:
            return []

        def as_text(value):
            if value is None or pd.isna(value):
                return ""
            return str(value)

        def as_int(value):
            if value is None or pd.isna(value) or value == "":
                return 0
            return int(float(value))

        def as_decimal(value, digits):
            if value is None or pd.isna(value) or value == "":
                return ""
            return f"{float(value):.{digits}f}"

        hofers = []
        for _, row in df.iterrows():
            try:
                game_ids = as_text(row.get("GameIDs", ""))
                player_id = row.get("Player ID", "")
                if player_id is None or pd.isna(player_id) or player_id == "":
                    player_id = row.get("PlayerID", "")
                hofers.append({
                    "name": as_text(row.get("Name", "")),
                    "playerId": as_text(player_id),
                    "yearInducted": as_text(row.get("Year Inducted", "")),
                    "positions": as_text(row.get("Position(s)", "")),
                    "teams": as_text(row.get("Teams in Games", "")),
                    "gamesSeen": as_int(row.get("Games Seen", 0)),
                    "firstGame": as_text(row.get("First Game", "")),
                    "lastGame": as_text(row.get("Last Game", "")),
                    "span": as_text(row.get("Span", "")),
                    "ab": as_int(row.get("AB", 0)),
                    "h": as_int(row.get("H", 0)),
                    "hr": as_int(row.get("HR", 0)),
                    "rbi": as_int(row.get("RBI", 0)),
                    "avg": as_decimal(row.get("AVG", ""), 3),
                    "ip": as_text(row.get("IP", "")),
                    "wins": as_int(row.get("W", 0)),
                    "losses": as_int(row.get("L", 0)),
                    "era": as_decimal(row.get("ERA", ""), 2),
                    "pitchingSo": as_int(row.get("SO_P", 0)),
                    "milestones": as_text(row.get("Milestones Achieved", "")),
                    "gameIds": game_ids,
                })
            except (KeyError, TypeError, ValueError) as e:
                print(f"   Warning: Could not serialize Hall of Famer data: {e}")
                continue
        return hofers

    def _serialize_pitchers(self, df):
        """Convert ALL pitchers DataFrame to JSON with complete stats and date range."""
        if df is None or df.empty:
            return []

        pitchers = []
        for _, row in df.iterrows():
            try:
                era = row.get("ERA")
                whip = row.get("WHIP")
                game_ids = str(row.get("GameIDs", ""))
                first_date, last_date = self._extract_date_range_from_gameids(game_ids)

                pitcher_data = {
                    "name": str(row.get("Name", "")),
                    "playerId": str(row.get("Player ID", "")),
                    "team": str(row.get("Team", "")),
                    "games": int(row.get("G", 0)),
                    "gameStarts": int(row.get("GS", 0)),
                    "wins": int(row.get("W", 0)),
                    "losses": int(row.get("L", 0)),
                    "saves": int(row.get("SV", 0)),
                    "ip": str(row.get("IP", "0.0")),
                    "era": f"{float(era):.2f}" if era is not None and pd.notna(era) else "N/A",
                    "whip": f"{float(whip):.3f}" if whip is not None and pd.notna(whip) else "N/A",
                    "h": int(row.get("H", 0)),
                    "r": int(row.get("R", 0)),
                    "er": int(row.get("ER", 0)),
                    "bb": int(row.get("BB", 0)),
                    "so": int(row.get("SO", 0)),
                    "hr": int(row.get("HR", 0)),
                    "firstGame": first_date,
                    "lastGame": last_date,
                }

                # Add per-game-type stats
                for gt in ['spring', 'regular', 'postseason']:
                    gt_g = int(row.get(f"{gt}_G", 0)) if f"{gt}_G" in row else 0
                    gt_era = row.get(f"{gt}_ERA")
                    gt_team = str(row.get(f"{gt}_Team", "")) if f"{gt}_Team" in row else ""

                    pitcher_data[f"{gt}Games"] = gt_g
                    pitcher_data[f"{gt}Gs"] = int(row.get(f"{gt}_GS", 0)) if f"{gt}_GS" in row else 0
                    pitcher_data[f"{gt}W"] = int(row.get(f"{gt}_W", 0)) if f"{gt}_W" in row else 0
                    pitcher_data[f"{gt}L"] = int(row.get(f"{gt}_L", 0)) if f"{gt}_L" in row else 0
                    pitcher_data[f"{gt}Sv"] = int(row.get(f"{gt}_SV", 0)) if f"{gt}_SV" in row else 0
                    pitcher_data[f"{gt}Ip"] = str(row.get(f"{gt}_IP", "0.0")) if f"{gt}_IP" in row else "0.0"
                    pitcher_data[f"{gt}Era"] = f"{float(gt_era):.2f}" if gt_era is not None and pd.notna(gt_era) else "N/A"
                    pitcher_data[f"{gt}H"] = int(row.get(f"{gt}_H", 0)) if f"{gt}_H" in row else 0
                    pitcher_data[f"{gt}Er"] = int(row.get(f"{gt}_ER", 0)) if f"{gt}_ER" in row else 0
                    pitcher_data[f"{gt}Bb"] = int(row.get(f"{gt}_BB", 0)) if f"{gt}_BB" in row else 0
                    pitcher_data[f"{gt}So"] = int(row.get(f"{gt}_SO", 0)) if f"{gt}_SO" in row else 0
                    pitcher_data[f"{gt}Team"] = gt_team

                pitchers.append(pitcher_data)
            except (KeyError, TypeError, ValueError) as e:
                # Log error but continue processing other pitchers
                print(f"   Warning: Could not serialize pitcher data: {e}")
                continue
        return pitchers
    
    # Team code normalization (ATH->OAK, etc.)
    TEAM_ALIASES = {'FLA': 'MIA', 'FLO': 'MIA', 'MON': 'WAS'}

    def _normalize_team(self, code):
        return self.TEAM_ALIASES.get(code, code) if code else code

    def _serialize_player_games(self, games):
        """Create game-by-game hitting records with footer stats merged in."""
        player_games = []
        
        for game in games:
            try:
                # Extract extra stats from play-by-play
                extra_stats = self._extract_extra_batting_stats(game)
                
                basic_info = game.get('basic_info', {})
                game_id = game.get('game_id', '')
                date_str = basic_info.get('date_yyyymmdd', '')
                
                # Initialize with defaults FIRST
                formatted_date = ''
                sortable_date = ''
                
                # Try to format if we have a valid date
                if date_str and len(date_str) == 8 and date_str.isdigit():
                    formatted_date = f"{date_str[4:6]}/{date_str[6:8]}/{date_str[0:4]}"
                    sortable_date = f"{date_str[0:4]}-{date_str[4:6]}-{date_str[6:8]}"
                elif game_id and len(game_id) >= 11:
                    # Fallback: extract from game_id (e.g., "BAL201904040")
                    date_str = game_id[3:11]
                    if len(date_str) == 8 and date_str.isdigit():
                        formatted_date = f"{date_str[4:6]}/{date_str[6:8]}/{date_str[0:4]}"
                        sortable_date = f"{date_str[0:4]}-{date_str[4:6]}-{date_str[6:8]}"
                
                # Two-way players (Ohtani) appear in BREF batting rows twice —
                # once as DH/hitter, once listed under P (pitcher) with 0 stats.
                # Track seen (side, player_id) to dedupe, keeping the row with
                # the larger PA count (the real batting appearance).
                game_seen = {}  # (side, player_id) → index into player_games

                for side in ['home', 'away']:
                    team = self._normalize_team(basic_info.get(f'{side}_team_code', ''))
                    opponent = self._normalize_team(basic_info.get('away_team_code' if side == 'home' else 'home_team_code', ''))

                    for player in game.get('batting', {}).get(side, []):
                        player_id = player.get('player_id', '')
                        if not player_id:
                            continue
                        # Skip the P-line duplicate if we already have a DH/position
                        # line with actual PAs for this player.
                        prior_idx = game_seen.get((side, player_id))
                        if prior_idx is not None:
                            prior = player_games[prior_idx]
                            prior_pa = prior.get('pa', 0)
                            this_pa = int(player.get('PA', 0))
                            if prior_pa >= this_pa:
                                continue  # keep existing richer row
                            player_games.pop(prior_idx)
                            # Rebuild index offsets for any other entries after
                            # (none currently — we only track per-game, and pop
                            # invalidates only this game's indexes)
                            game_seen = {k: v for k, v in game_seen.items() if v < prior_idx}
                        
                        ab = int(player.get('AB', 0))
                        pa = int(player.get('PA', 0))
                        
                        # Get extra stats for this player by ID (from play-by-play),
                        # falling back to batting data (MLB API stores 2B/3B/HR directly)
                        player_extra = extra_stats.get(player_id, {})
                        if not player_extra.get('HR') and not player_extra.get('2B') and not player_extra.get('3B'):
                            player_extra = {
                                'HR': int(player.get('HR', 0)),
                                '2B': int(player.get('2B', 0)),
                                '3B': int(player.get('3B', 0)),
                                'SB': player_extra.get('SB', int(player.get('SB', 0))),
                                'CS': player_extra.get('CS', int(player.get('CS', 0))),
                                'HBP': int(player.get('HBP', 0)),
                                'GIDP': int(player.get('GDP', 0)),
                            }

                        # Parse SB/CS from Details column (e.g., "2·SB", "SB,CS", "2B,SB")
                        details_sb = 0
                        details_cs = 0
                        details = player.get('Details', '')
                        if isinstance(details, str) and details:
                            for item in details.split(','):
                                item = item.strip()
                                if item == 'SB':
                                    details_sb += 1
                                elif '·' in item and item.endswith('SB'):
                                    try:
                                        details_sb += int(item.split('·')[0])
                                    except ValueError:
                                        details_sb += 1
                                elif item == 'CS':
                                    details_cs += 1
                                elif '·' in item and item.endswith('CS'):
                                    try:
                                        details_cs += int(item.split('·')[0])
                                    except ValueError:
                                        details_cs += 1

                        sb = max(int(player.get('SB', 0)), player_extra.get('SB', 0), details_sb)
                        cs = max(int(player.get('CS', 0)), player_extra.get('CS', 0), details_cs)

                        player_games.append({
                            'date': formatted_date,
                            'dateSort': sortable_date,
                            'playerId': player_id,
                            'name': str(player.get('name', '')),
                            'team': team,
                            'opponent': opponent,
                            'gameId': game_id,
                            'gameType': basic_info.get('game_type', 'regular'),
                            'ab': ab,
                            'pa': pa,
                            'h': int(player.get('H', 0)),
                            'r': int(player.get('R', 0)),
                            'rbi': int(player.get('RBI', 0)),
                            'hr': player_extra.get('HR', 0),
                            'doubles': player_extra.get('2B', 0),
                            'triples': player_extra.get('3B', 0),
                            'sb': sb,
                            'cs': cs,
                            'bb': int(player.get('BB', 0)),
                            'so': int(player.get('SO', 0)),
                            'hbp': player_extra.get('HBP', 0),
                            'gidp': player_extra.get('GIDP', 0),
                        })
                        game_seen[(side, player_id)] = len(player_games) - 1
                        # Add hit data (exit velo) if available
                        hit_info = game.get('hit_data', {}).get(player_id, {})
                        if hit_info:
                            player_games[-1]['maxExitVelo'] = hit_info.get('maxExitVelo')
                            player_games[-1]['avgExitVelo'] = hit_info.get('avgExitVelo')
                            player_games[-1]['maxDistance'] = hit_info.get('maxDistance')
            except Exception as e:
                print(f"   ⚠️ Error serializing player game: {e}")
                continue
        
        return player_games

    def _extract_extra_batting_stats(self, game):
        """Extract 2B, 3B, HR, SB, CS, HBP, GIDP from play-by-play data.

        Thin wrapper around the shared helper so playerGames totals (here)
        always match the aggregated player totals computed in
        ``PlayerStatsProcessor`` \u2014 both call the same extractor.
        """
        from ..utils.stat_utils import extract_extra_batting_stats
        return extract_extra_batting_stats(game)

    
    def _serialize_pitcher_games(self, games):
        """Create game-by-game pitching records."""
        pitcher_games = []
        
        for game in games:
            try:
                basic_info = game.get('basic_info', {})
                game_id = game.get('game_id', '')
                date_str = basic_info.get('date_yyyymmdd', '')
                
                # Initialize with defaults FIRST
                formatted_date = ''
                sortable_date = ''
                
                # Try to format if we have a valid date
                if date_str and len(date_str) == 8 and date_str.isdigit():
                    formatted_date = f"{date_str[4:6]}/{date_str[6:8]}/{date_str[0:4]}"
                    sortable_date = f"{date_str[0:4]}-{date_str[4:6]}-{date_str[6:8]}"
                elif game_id and len(game_id) >= 11:
                    # Fallback: extract from game_id
                    date_str = game_id[3:11]
                    if len(date_str) == 8 and date_str.isdigit():
                        formatted_date = f"{date_str[4:6]}/{date_str[6:8]}/{date_str[0:4]}"
                        sortable_date = f"{date_str[0:4]}-{date_str[4:6]}-{date_str[6:8]}"
                
                for side in ['home', 'away']:
                    team = self._normalize_team(basic_info.get(f'{side}_team_code', ''))
                    opponent = self._normalize_team(basic_info.get('away_team_code' if side == 'home' else 'home_team_code', ''))

                    for p_idx, pitcher in enumerate(game.get('pitching', {}).get(side, [])):
                        player_id = pitcher.get('player_id', '')
                        if not player_id:
                            continue
                        
                        ip_str = str(pitcher.get('IP', '0'))
                        if ip_str == '0' or ip_str == '0.0':
                            continue
                        
                        # Convert IP to outs for accurate aggregation
                        try:
                            if '.' in ip_str:
                                parts = ip_str.split('.')
                                outs = int(parts[0]) * 3 + int(parts[1])
                            else:
                                outs = int(float(ip_str) * 3)
                        except (ValueError, TypeError):
                            outs = 0
                        
                        if outs == 0:
                            continue
                        
                        pitcher_games.append({
                            'date': formatted_date,
                            'dateSort': sortable_date,
                            'playerId': player_id,
                            'name': str(pitcher.get('name', '')),
                            'team': team,
                            'opponent': opponent,
                            'gameId': game_id,
                            'gameType': basic_info.get('game_type', 'regular'),
                            'order': p_idx,
                            'outs': outs,
                            'h': int(pitcher.get('H', 0)),
                            'r': int(pitcher.get('R', 0)),
                            'er': int(pitcher.get('ER', 0)),
                            'bb': int(pitcher.get('BB', 0)),
                            'so': int(pitcher.get('SO', 0)),
                            'hr': int(pitcher.get('HR', 0)),
                            'wins': 1 if pitcher.get('win') else 0,
                            'losses': 1 if pitcher.get('loss') else 0,
                            'saves': 1 if pitcher.get('save') else 0,
                            'gameStarts': 1 if pitcher.get('player_id') == game.get('pitching', {}).get(side, [{}])[0].get('player_id') else 0,
                        })
                        # Add pitch data if available
                        pitch_info = game.get('pitch_data', {}).get(player_id, {})
                        if pitch_info:
                            pitcher_games[-1]['maxSpeed'] = pitch_info.get('maxSpeed')
                            pitcher_games[-1]['avgSpeed'] = pitch_info.get('avgSpeed')
                            pitcher_games[-1]['minSpeed'] = pitch_info.get('minSpeed')
                            pitcher_games[-1]['avgSpinRate'] = pitch_info.get('avgSpinRate')
                            pitcher_games[-1]['minSpinRate'] = pitch_info.get('minSpinRate')
                            pitcher_games[-1]['totalPitches'] = pitch_info.get('totalPitches', 0)
            except Exception as e:
                print(f"   ⚠️ Error serializing pitcher game: {e}")
                continue
        
        return pitcher_games
    
    def _extract_date_range_from_gameids(self, game_ids_str):
        """Extract first and last game dates from comma-separated GameIDs."""
        try:
            if not game_ids_str or game_ids_str == '':
                return '', ''
            
            game_ids = [gid.strip() for gid in game_ids_str.split(',') if gid.strip()]
            if not game_ids:
                return '', ''
            
            first_game = game_ids[0]
            last_game = game_ids[-1]
            
            def extract_date(game_id):
                if len(game_id) >= 11:
                    date_str = game_id[3:11]
                    return f"{date_str[4:6]}/{date_str[6:8]}/{date_str[0:4]}"
                return ''
            
            return extract_date(first_game), extract_date(last_game)
        except (IndexError, ValueError, TypeError, AttributeError):
            return '', ''
    
    def _serialize_players_without_stats(self, df):
        """Convert players without stats DataFrame to JSON."""
        if df is None or df.empty:
            return []
        
        players = []
        for _, row in df.iterrows():
            try:
                players.append({
                    "name": str(row.get("Name", "")),
                    "playerId": str(row.get("Player ID", "")),
                    "teams": str(row.get("Team(s)", "")),
                    "games": int(row.get("Games", 0)),
                    "positions": str(row.get("Position(s)", "")),
                    "gameIds": str(row.get("GameIDs", "")),
                })
            except (KeyError, TypeError, ValueError) as e:
                print(f"   Warning: Could not serialize player without stats: {e}")
                continue
        return players

    def _serialize_teams(self, df):
        """Convert team records DataFrame to JSON."""
        if df is None or df.empty:
            return []
        
        teams = []
        for _, row in df.iterrows():
            try:
                teams.append({
                    "team": str(row.get("Team", "")),
                    "games": int(row.get("Games", 0)),
                    "record": str(row.get("Record", "0-0")),
                    "runs": int(row.get("Runs Scored", 0)) if pd.notna(row.get("Runs Scored")) else 0,
                    "runsAllowed": int(row.get("Runs Allowed", 0)) if pd.notna(row.get("Runs Allowed")) else 0,
                    "diff": str(row.get("Run Differential", "0")),
                    "homeRecord": str(row.get("Home Record", "")),
                    "awayRecord": str(row.get("Away Record", "")),
                    "oneRunGames": str(row.get("1-Run Games", "")),
                    "blowouts": str(row.get("Blowouts (5+)", "")),
                })
            except (KeyError, TypeError, ValueError) as e:
                print(f"   Warning: Could not serialize team data: {e}")
                continue
        return teams
    
    def _serialize_games(self, df, raw_games=None):
        """Convert ALL games from game log with enhanced details."""
        if df is None or df.empty:
            return []

        # Use provided raw_games or try to get from stored data
        if raw_games is None:
            raw_games = getattr(self, 'data', {}).get('_raw_games', [])

        raw_games_by_id = {g.get('game_id', ''): g for g in raw_games}

        # Compute first-time-seen players per game by walking attended games
        # in chronological order. Includes batters, pitchers, and substitutions.
        first_seen_by_game = {}  # game_id → set of player_ids seeing the user for the 1st time
        seen_players = set()

        def _players_in_game(g):
            pids = set()
            for side in ('home', 'away'):
                for b in (g.get('batting', {}).get(side) or []):
                    pid = b.get('player_id')
                    if pid:
                        pids.add(pid)
                for p in (g.get('pitching', {}).get(side) or []):
                    pid = p.get('player_id')
                    if pid:
                        pids.add(pid)
            # Substitutions — cover any schema variant we've used
            subs = g.get('substitutions') or []
            if isinstance(subs, list):
                for s in subs:
                    pid = s.get('player_id') or s.get('in_player_id') or s.get('sub_player_id')
                    if pid:
                        pids.add(pid)
            elif isinstance(subs, dict):
                for side_subs in subs.values():
                    for s in (side_subs or []):
                        pid = s.get('player_id') or s.get('in_player_id')
                        if pid:
                            pids.add(pid)
            return pids

        def _game_date_key(g):
            return g.get('basic_info', {}).get('date_yyyymmdd', '') or ''

        for raw in sorted(raw_games, key=_game_date_key):
            gid = raw.get('game_id', '')
            if not gid:
                continue
            pids = _players_in_game(raw)
            new_pids = pids - seen_players
            first_seen_by_game[gid] = new_pids
            seen_players |= pids
        
        games = []
        for _, row in df.iterrows():
            try:
                date_val = row.get("Date")
                if hasattr(date_val, 'strftime'):
                    date_str = date_val.strftime("%m/%d/%Y")
                else:
                    date_str = str(date_val)
                
                game_id = str(row.get("GameID", ""))
                if game_id.startswith('=HYPERLINK'):
                    import re
                    match = re.search(r'"([^"]+)"\)$', game_id)
                    if match:
                        game_id = match.group(1)
                
                game_obj = {
                    "date": date_str,
                    "startTime": str(row.get("Start Time", "")),
                    "awayTeam": str(row.get("Away Team", "")),
                    "homeTeam": str(row.get("Home Team", "")),
                    "score": str(row.get("Score", "")),
                    "venue": str(row.get("Venue", "")),
                    "attendance": int(row.get("Attendance", 0)) if pd.notna(row.get("Attendance")) else 0,
                    "gameLength": self._format_game_length(row.get("Game Length", "")),
                    "gameId": game_id
                }
                
                # Add enhanced details from raw game data if available
                raw_game = raw_games_by_id.get(game_id)
                if raw_game:
                    game_obj.update(self._extract_game_details(raw_game))
                    # First-time-seen players (in chronological attended-game order)
                    fs = first_seen_by_game.get(game_id, set())
                    if fs:
                        game_obj['firstSeenPlayerIds'] = sorted(fs)
                    # Override team codes from raw data (more accurate than DataFrame)
                    bi = raw_game.get('basic_info', {})
                    if bi.get('away_team_code'):
                        game_obj['awayTeam'] = bi['away_team_code']
                        if bi['away_team_code'] == 'ATH' and 'OAK' in game_obj['score']:
                            game_obj['score'] = game_obj['score'].replace('OAK', 'ATH')
                    if bi.get('home_team_code'):
                        game_obj['homeTeam'] = bi['home_team_code']
                        if bi['home_team_code'] == 'ATH' and 'OAK' in game_obj['score']:
                            game_obj['score'] = game_obj['score'].replace('OAK', 'ATH')
                
                games.append(game_obj)
            except (KeyError, TypeError, ValueError) as e:
                print(f"   Warning: Could not serialize game data: {e}")
                continue
        return games
    
    def _extract_game_details(self, raw_game):
        """Extract detailed information from raw game data."""
        details = {}

        # Game type and source
        basic_info = raw_game.get('basic_info', {})
        details['gameType'] = basic_info.get('game_type', 'regular')
        details['source'] = basic_info.get('source', 'bref')

        # MLB game pk (for linking to MLB.com box scores)
        if raw_game.get('mlb_game_pk'):
            details['mlbGamePk'] = raw_game.get('mlb_game_pk')

        # Venue details (for spring training stadiums)
        if basic_info.get('venue_city'):
            details['venueCity'] = basic_info.get('venue_city')
        if basic_info.get('venue_state'):
            details['venueState'] = basic_info.get('venue_state')
        if basic_info.get('venue_latitude') and basic_info.get('venue_longitude'):
            details['venueCoords'] = {
                'lat': basic_info['venue_latitude'],
                'lon': basic_info['venue_longitude']
            }

        # No-hitter / perfect game flags
        flags = raw_game.get('flags', {})
        if flags.get('no_hitter') or flags.get('perfect_game'):
            details['flags'] = flags

        # Weather info
        if basic_info.get('weather'):
            details['weather'] = str(basic_info.get('weather', ''))
        if basic_info.get('temperature_f'):
            details['temperature'] = int(basic_info.get('temperature_f', 0))
        
        # Umpires
        umpires = raw_game.get('umpires', {})
        if umpires:
            details['umpires'] = {
                'hp': str(umpires.get('HP', '')),
                '1b': str(umpires.get('1B', '')),
                '2b': str(umpires.get('2B', '')),
                '3b': str(umpires.get('3B', '')),
                'lf': str(umpires.get('LF', '')),
                'rf': str(umpires.get('RF', ''))
            }
        
        # Linescore (inning by inning)
        linescore = raw_game.get('linescore', {})
        if linescore:
            details['linescore'] = {
                'away': {
                    'innings': linescore.get('away', {}).get('innings', []),
                    'runs': linescore.get('away', {}).get('R', 0),
                    'hits': linescore.get('away', {}).get('H', 0),
                    'errors': linescore.get('away', {}).get('E', 0)
                },
                'home': {
                    'innings': linescore.get('home', {}).get('innings', []),
                    'runs': linescore.get('home', {}).get('R', 0),
                    'hits': linescore.get('home', {}).get('H', 0),
                    'errors': linescore.get('home', {}).get('E', 0)
                }
            }
        
        # Key plays/moments from play-by-play
        key_plays = []
        for play in raw_game.get('play_by_play', []):
            # Home runs
            if play.get('home_run'):
                key_plays.append({
                    'type': 'home_run',
                    'inning': f"{play.get('half', '').title()} {play.get('inning', '')}",
                    'batter': play.get('batter', ''),
                    'pitcher': play.get('pitcher', ''),
                    'description': play.get('description', ''),
                    'rbi': play.get('rbi', 1)
                })
            # Grand slams
            elif play.get('grand_slam'):
                key_plays.append({
                    'type': 'grand_slam',
                    'inning': f"{play.get('half', '').title()} {play.get('inning', '')}",
                    'batter': play.get('batter', ''),
                    'pitcher': play.get('pitcher', ''),
                    'description': play.get('description', '')
                })
        
        if key_plays:
            details['keyPlays'] = key_plays[:10]  # Limit to 10 most important
        
        # Pitcher decisions
        decisions = raw_game.get('pitcher_decisions', {})
        if decisions:
            details['decisions'] = {
                'winner': str(decisions.get('winning_pitcher', '')),
                'loser': str(decisions.get('losing_pitcher', '')),
                'save': str(decisions.get('save_pitcher', ''))
            }
        
        # Starting lineups
        lineups = raw_game.get('lineups', {})
        if lineups and (lineups.get('away') or lineups.get('home')):
            details['lineups'] = {
                'away': [
                    {
                        'slot': p.get('slot', 0),
                        'name': p.get('name', ''),
                        'playerId': p.get('player_id', ''),
                        'position': p.get('pos', ''),
                        'jerseyNumber': p.get('jersey_number', '')
                    }
                    for p in lineups.get('away', [])
                ],
                'home': [
                    {
                        'slot': p.get('slot', 0),
                        'name': p.get('name', ''),
                        'playerId': p.get('player_id', ''),
                        'position': p.get('pos', ''),
                        'jerseyNumber': p.get('jersey_number', '')
                    }
                    for p in lineups.get('home', [])
                ]
            }
        
        # Substitutions
        substitutions = raw_game.get('substitutions', [])
        if substitutions:
            details['substitutions'] = [
                {
                    'type': sub.get('type', 'substitution'),
                    'inning': sub.get('inning', 0),
                    'half': sub.get('half', ''),
                    'playerIn': sub.get('player_in', ''),
                    'playerOut': sub.get('player_out', ''),
                    'position': sub.get('pos', ''),
                    'text': sub.get('raw', '') or sub.get('text', '')
                }
                for sub in substitutions
            ]
        
        # Play-by-play - use raw_plays to get ALL events including steals
        raw_plays = raw_game.get('raw_plays', [])
        if raw_plays:
            pbp_list = []
            for play in raw_plays[:300]:
                event_type = play.get('event_type', '')
                desc_lower = play.get('description', '').lower()
                # Score: BREF uses 'score' string, MLB API has away_score/home_score
                score = play.get('score', '')
                if not score and (play.get('away_score') is not None or play.get('home_score') is not None):
                    score = f"{play.get('away_score', 0)}-{play.get('home_score', 0)}"
                pbp_list.append({
                    'inning': play.get('inning', 0),
                    'half': play.get('half', ''),
                    'batter': play.get('batter', ''),
                    'batterId': play.get('batter_id', ''),
                    'pitcher': play.get('pitcher', ''),
                    'pitcherId': play.get('pitcher_id', ''),
                    'description': play.get('description', ''),
                    'outs': play.get('outs') if play.get('outs') is not None else play.get('outs_before'),
                    'score': score,
                    'pitchCount': play.get('pitch_count', 0),
                    'battingTeam': play.get('batting_team', ''),
                    'isHomeRun': play.get('home_run', False) or event_type == 'home_run',
                    'isStrikeout': play.get('strikeout', False) or event_type == 'strikeout',
                    'isWalk': play.get('walk', False) or event_type == 'walk',
                    'isStolenBase': 'steals' in desc_lower or 'stolen base' in desc_lower,
                    'isCaughtStealing': 'caught stealing' in desc_lower
                })
            details['playByPlay'] = pbp_list

        # Pitch data (per-pitcher summaries from MLB API)
        pitch_data = raw_game.get('pitch_data', {})
        if pitch_data:
            details['pitchData'] = {
                pid: {
                    'name': pdata.get('name', ''),
                    'totalPitches': pdata.get('totalPitches', 0),
                    'avgSpeed': pdata.get('avgSpeed'),
                    'maxSpeed': pdata.get('maxSpeed'),
                    'avgSpinRate': pdata.get('avgSpinRate'),
                    'pitchTypes': pdata.get('pitchTypes', {}),
                    'pitchTypeNames': pdata.get('pitchTypeNames', {}),
                }
                for pid, pdata in pitch_data.items()
                if pdata.get('totalPitches', 0) > 0
            }

        # Hit data (per-batter exit velo summaries from MLB API)
        hit_data = raw_game.get('hit_data', {})
        if hit_data:
            details['hitData'] = {
                pid: {
                    'name': hdata.get('name', ''),
                    'battedBalls': hdata.get('battedBalls', 0),
                    'maxExitVelo': hdata.get('maxExitVelo'),
                    'avgExitVelo': hdata.get('avgExitVelo'),
                    'maxDistance': hdata.get('maxDistance'),
                    'maxExitVeloDistance': hdata.get('maxExitVeloDistance'),
                    'maxExitVeloResult': hdata.get('maxExitVeloResult', ''),
                    'maxExitVeloDescription': hdata.get('maxExitVeloDescription', ''),
                    'maxExitVeloInning': hdata.get('maxExitVeloInning'),
                    'maxExitVeloHalf': hdata.get('maxExitVeloHalf', ''),
                    'maxExitVeloTrajectory': hdata.get('maxExitVeloTrajectory', ''),
                    'trajectories': hdata.get('trajectories', {}),
                }
                for pid, hdata in hit_data.items()
                if hdata.get('battedBalls', 0) > 0
            }

        # ABS challenges
        abs_data = raw_game.get('abs_challenges')
        if abs_data:
            details['absChallenges'] = abs_data

        return details

    def _format_game_length(self, game_length):
        """Format game length from Excel time format to readable string.
        
        Args:
            game_length: Can be a decimal (Excel format), string like "2:39", or empty
            
        Returns:
            str: Formatted time like "2:39" or empty string
        """
        if not game_length or pd.isna(game_length):
            return ""
        
        # If it's already a string in correct format (HH:MM), return it
        if isinstance(game_length, str):
            if ':' in game_length:
                return game_length
            # Try to parse if it's a decimal string
            try:
                game_length = float(game_length)
            except ValueError:
                return game_length
        
        # If it's a decimal (Excel stores time as fraction of a day)
        if isinstance(game_length, (int, float)):
            try:
                # Convert fraction of day to hours
                total_hours = game_length * 24
                hours = int(total_hours)
                minutes = int((total_hours - hours) * 60)
                return f"{hours}:{minutes:02d}"
            except Exception:
                return ""
        
        return str(game_length)
    
    def _serialize_stadiums(self, df):
        """Convert stadiums DataFrame to JSON."""
        if df is None or df.empty:
            return []
        
        stadiums = []
        for _, row in df.iterrows():
            try:
                stadiums.append({
                    "stadium": str(row.get("Stadium", "")),
                    "games": int(row.get("Games", 0)),
                    "firstVisit": str(row.get("First Visit", "")),
                    "lastVisit": str(row.get("Last Visit", "")),
                    "span": str(row.get("Span", "")),
                    "avgAttendance": str(row.get("Avg Attendance", "")),
                    "highAttendance": str(row.get("High Attendance", "")),
                    "lowAttendance": str(row.get("Low Attendance", "")),
                    "homeRunsSeen": int(row.get("Home Runs Seen", 0)) if pd.notna(row.get("Home Runs Seen")) else 0,
                    "hitsSeen": int(row.get("Hits Seen", 0)) if pd.notna(row.get("Hits Seen")) else 0,
                    "strikeoutsSeen": int(row.get("Strikeouts Seen", 0)) if pd.notna(row.get("Strikeouts Seen")) else 0,
                    "teamsSeen": int(row.get("Teams Seen", 0)) if pd.notna(row.get("Teams Seen")) else 0,
                    "homeTeamRecord": str(row.get("Home Team Record", "")),
                })
            except (KeyError, TypeError, ValueError) as e:
                print(f"   Warning: Could not serialize stadium data: {e}")
                continue
        return stadiums
    
    def _serialize_orioles(self, df):
        """Convert Orioles stadium records to JSON."""
        if df is None or df.empty:
            return []
        
        orioles = []
        for _, row in df.iterrows():
            try:
                orioles.append({
                    "stadium": str(row.get("Stadium", "")),
                    "games": int(row.get("Games", 0)),
                    "record": str(row.get("Orioles Record", "")),
                    "firstVisit": str(row.get("First Visit", "")),
                    "lastVisit": str(row.get("Last Visit", "")),
                    "runsScored": int(row.get("Runs Scored", 0)) if pd.notna(row.get("Runs Scored")) else 0,
                    "runsAllowed": int(row.get("Runs Allowed", 0)) if pd.notna(row.get("Runs Allowed")) else 0,
                    "runDiff": str(row.get("Run Differential", "")),
                    "homeRunsHit": int(row.get("Home Runs Hit", 0)) if pd.notna(row.get("Home Runs Hit")) else 0,
                    "oneRunGames": str(row.get("1-Run Games", "")),
                })
            except (KeyError, TypeError, ValueError) as e:
                print(f"   Warning: Could not serialize Orioles data: {e}")
                continue
        return orioles
    
    def _serialize_debuts(self, debut_rows):
        """Convert MLB debuts to JSON."""
        if not debut_rows:
            return []
        
        debuts = []
        for row in debut_rows:
            try:
                date_str = str(row.get("Date", ""))
                if len(date_str) == 8:
                    formatted_date = f"{date_str[4:6]}/{date_str[6:8]}/{date_str[0:4]}"
                else:
                    formatted_date = date_str
                
                debuts.append({
                    "date": formatted_date,
                    "player": str(row.get("Player", "")),
                    "playerId": str(row.get("PlayerID", "")),
                    "team": str(row.get("Team", "")),
                    "opponent": str(row.get("Opponent", "")),
                    "position": str(row.get("Position", "")),
                    "ab": int(row.get("AB", 0)) if "AB" in row else 0,
                    "h": int(row.get("H", 0)) if "H" in row else 0,
                    "r": int(row.get("R", 0)) if "R" in row else 0,
                    "hr": int(row.get("HR", 0)) if "HR" in row else 0,
                    "rbi": int(row.get("RBI", 0)) if "RBI" in row else 0,
                    "bb": int(row.get("BB", 0)) if "BB" in row else 0,
                    "so": int(row.get("SO", 0)) if "SO" in row else 0,
                    "ip": str(row.get("IP", "")) if "IP" in row else "",
                    "h_p": int(row.get("H_P", 0)) if "H_P" in row else 0,
                    "r_p": int(row.get("R_P", 0)) if "R_P" in row else 0,
                    "er": int(row.get("ER", 0)) if "ER" in row else 0,
                    "bb_p": int(row.get("BB_P", 0)) if "BB_P" in row else 0,
                    "so_p": int(row.get("SO_P", 0)) if "SO_P" in row else 0,
                    "decision": str(row.get("Decision", "")) if "Decision" in row else "",
                    "gameId": str(row.get("GameID", "")),
                })
            except (KeyError, TypeError, ValueError) as e:
                print(f"   Warning: Could not serialize debut data: {e}")
                continue
        return debuts
    
    def _serialize_final_games(self, final_rows):
        """Convert final MLB games to JSON."""
        if not final_rows:
            return []
        
        finals = []
        for row in final_rows:
            try:
                date_str = str(row.get("Date", ""))
                if len(date_str) == 8:
                    formatted_date = f"{date_str[4:6]}/{date_str[6:8]}/{date_str[0:4]}"
                else:
                    formatted_date = date_str
                
                finals.append({
                    "date": formatted_date,
                    "player": str(row.get("Player", "")),
                    "playerId": str(row.get("PlayerID", "")),
                    "team": str(row.get("Team", "")),
                    "position": str(row.get("Position", "")),
                    "ab": int(row.get("AB", 0)) if "AB" in row else 0,
                    "h": int(row.get("H", 0)) if "H" in row else 0,
                    "r": int(row.get("R", 0)) if "R" in row else 0,
                    "hr": int(row.get("HR", 0)) if "HR" in row else 0,
                    "rbi": int(row.get("RBI", 0)) if "RBI" in row else 0,
                    "bb": int(row.get("BB", 0)) if "BB" in row else 0,
                    "so": int(row.get("SO", 0)) if "SO" in row else 0,
                    "ip": str(row.get("IP", "")) if "IP" in row else "",
                    "h_p": int(row.get("H_P", 0)) if "H_P" in row else 0,
                    "r_p": int(row.get("R_P", 0)) if "R_P" in row else 0,
                    "er": int(row.get("ER", 0)) if "ER" in row else 0,
                    "bb_p": int(row.get("BB_P", 0)) if "BB_P" in row else 0,
                    "so_p": int(row.get("SO_P", 0)) if "SO_P" in row else 0,
                    "decision": str(row.get("Decision", "")) if "Decision" in row else "",
                    "gameId": str(row.get("GameID", "")),
                })
            except (KeyError, TypeError, ValueError) as e:
                print(f"   Warning: Could not serialize final game data: {e}")
                continue
        return finals
    
    def _serialize_signature_hrs(self, df):
        """Convert signature home runs DataFrame to JSON."""
        if df is None or df.empty:
            return []
        
        hrs = []
        for _, row in df.iterrows():
            try:
                date_val = row.get("Date")
                if hasattr(date_val, 'strftime'):
                    date_str = date_val.strftime("%m/%d/%Y")
                else:
                    date_str = str(date_val)
                    if len(date_str) == 8 and date_str.isdigit():
                        date_str = f"{date_str[4:6]}/{date_str[6:8]}/{date_str[0:4]}"
                
                hrs.append({
                    "date": date_str,
                    "player": str(row.get("Player", "")),
                    "team": str(row.get("Team", "")),
                    "opponent": str(row.get("Opponent", "")),
                    "pitcher": str(row.get("Pitcher", "")),
                    "signatureNumber": str(row.get("Signature HR Number", "")),
                    "gameId": str(row.get("GameID", "")),
                })
            except (KeyError, TypeError, ValueError) as e:
                print(f"   Warning: Could not serialize signature HR data: {e}")
                continue
        return hrs
    
    def _serialize_matchup_matrix(self, df):
        """Convert matchup matrix to JSON."""
        if df is None or df.empty:
            return {"teams": [], "matrix": []}
        
        teams = df.index.tolist()
        matrix = []
        
        for team in teams:
            row_data = {"team": team}
            for opponent in teams:
                value = df.loc[team, opponent]
                if value == "X":
                    row_data[opponent] = "X"
                else:
                    row_data[opponent] = int(value) if pd.notna(value) and value != "" else 0
            matrix.append(row_data)
        
        return {"teams": teams, "matrix": matrix}

    def _serialize_division_checklist(self):
        """Serialize division checklist data - teams and stadiums seen per division."""
        from ..utils.constants import (
            MLB_DIVISIONS, TEAM_TO_DIVISION, TEAM_TO_LEAGUE,
            CODE_TO_TEAM, CURRENT_STADIUMS, STADIUM_ALIASES, RETROSHEET_CODES
        )

        game_log = self.data.get('game_log')
        if game_log is None or game_log.empty:
            return {}

        # Track teams seen and stadiums visited
        teams_seen = set()
        stadiums_visited = set()
        team_visit_counts = {}
        stadium_visit_counts = {}

        # Build set of all valid team codes from divisions
        all_division_teams = set()
        for teams in MLB_DIVISIONS.values():
            all_division_teams.update(teams)

        # Team code aliases - map common abbreviations to Retrosheet codes
        TEAM_CODE_ALIASES = {
            # Relocated/renamed teams
            # ATH is kept separate from OAK — different era/city
            'FLA': 'MIA',  # Florida Marlins -> Miami Marlins
            'FLO': 'MIA',  # Florida Marlins alternate code
            'MON': 'WAS',  # Montreal Expos -> Washington Nationals
            # Common abbreviations -> Retrosheet codes
            'NYY': 'NYA',  # New York Yankees
            'NYM': 'NYN',  # New York Mets
            'SF': 'SFN',   # San Francisco Giants
            'LAD': 'LAN',  # Los Angeles Dodgers
            'SD': 'SDN',   # San Diego Padres
            'STL': 'SLN',  # St. Louis Cardinals
            'TB': 'TBA',   # Tampa Bay Rays
            'KC': 'KCA',   # Kansas City Royals
            'CWS': 'CHA',  # Chicago White Sox
            'CHC': 'CHN',  # Chicago Cubs
            'WSH': 'WAS',  # Washington Nationals
            'LAA': 'ANA',  # Los Angeles Angels
            'CAL': 'ANA',  # California Angels
        }

        def normalize_team_code(code):
            """Normalize team code to canonical form."""
            if not code:
                return code
            return TEAM_CODE_ALIASES.get(code, code)

        # Build reverse stadium lookup (alias -> canonical name)
        stadium_alias_lookup = {}
        for canonical, aliases in STADIUM_ALIASES.items():
            stadium_alias_lookup[canonical.lower()] = canonical
            for alias in aliases:
                stadium_alias_lookup[alias.lower()] = canonical

        def normalize_stadium(venue):
            """Normalize stadium name to canonical form."""
            if not venue:
                return venue
            venue_lower = venue.lower()
            return stadium_alias_lookup.get(venue_lower, venue)

        # Process each game
        for _, row in game_log.iterrows():
            # Game log already has team codes (e.g., "NYA", "BAL"), not full names
            away_code = normalize_team_code(str(row.get('Away Team', '')))
            home_code = normalize_team_code(str(row.get('Home Team', '')))
            venue = str(row.get('Venue', ''))

            # Track teams seen (validate against division teams)
            if away_code and away_code in all_division_teams:
                teams_seen.add(away_code)
                team_visit_counts[away_code] = team_visit_counts.get(away_code, 0) + 1
            if home_code and home_code in all_division_teams:
                teams_seen.add(home_code)
                team_visit_counts[home_code] = team_visit_counts.get(home_code, 0) + 1

            if venue:
                normalized_venue = normalize_stadium(venue)
                stadiums_visited.add(normalized_venue)
                stadium_visit_counts[normalized_venue] = stadium_visit_counts.get(normalized_venue, 0) + 1

        # Build checklist for each division
        checklist = {}
        all_mlb_teams = []

        for div_name, team_codes in MLB_DIVISIONS.items():
            teams_data = []
            for code in sorted(team_codes):
                team_name = CODE_TO_TEAM.get(code, code)
                home_stadium = CURRENT_STADIUMS.get(code, '')
                normalized_home = normalize_stadium(home_stadium)

                team_data = {
                    'teamCode': code,
                    'teamName': team_name,
                    'seen': code in teams_seen,
                    'visitCount': team_visit_counts.get(code, 0),
                    'homeStadium': home_stadium,
                    'stadiumVisited': normalized_home in stadiums_visited if normalized_home else False,
                    'stadiumVisitCount': stadium_visit_counts.get(normalized_home, 0) if normalized_home else 0,
                    'division': div_name,
                    'league': 'AL' if div_name.startswith('AL') else 'NL'
                }
                teams_data.append(team_data)
                all_mlb_teams.append(team_data)

            checklist[div_name] = {
                'teams': teams_data,
                'teamsSeen': sum(1 for t in teams_data if t['seen']),
                'totalTeams': len(teams_data),
                'stadiumsVisited': sum(1 for t in teams_data if t['stadiumVisited']),
                'totalStadiums': len(teams_data),
                'league': 'AL' if div_name.startswith('AL') else 'NL'
            }

        # Add league-level aggregation
        for league in ['AL', 'NL']:
            league_teams = [t for t in all_mlb_teams if t['league'] == league]
            checklist[league] = {
                'teams': sorted(league_teams, key=lambda x: x['teamName']),
                'teamsSeen': sum(1 for t in league_teams if t['seen']),
                'totalTeams': len(league_teams),
                'stadiumsVisited': sum(1 for t in league_teams if t['stadiumVisited']),
                'totalStadiums': len(league_teams),
                'league': league
            }

        # Add "All MLB" aggregation
        checklist['All MLB'] = {
            'teams': sorted(all_mlb_teams, key=lambda x: x['teamName']),
            'teamsSeen': sum(1 for t in all_mlb_teams if t['seen']),
            'totalTeams': len(all_mlb_teams),
            'stadiumsVisited': sum(1 for t in all_mlb_teams if t['stadiumVisited']),
            'totalStadiums': len(all_mlb_teams)
        }

        return checklist

    def _serialize_companions(self):
        """Serialize companion data - who you attended games with."""
        from ..utils.constants import BASE_DIR, STADIUM_ALIASES
        import os

        # Stadium normalizer - maps old names to current names
        def normalize_stadium(venue):
            if not venue:
                return venue
            # Check if this venue is an alias for another stadium
            for current_name, aliases in STADIUM_ALIASES.items():
                if venue in aliases or venue == current_name:
                    return current_name
            return venue

        companions_file = BASE_DIR / "companions.csv"
        if not companions_file.exists():
            return {"companions": {}, "gameCompanions": {}}

        # Load companions data
        try:
            df_companions = pd.read_csv(companions_file, comment='#')
            if df_companions.empty or 'GameID' not in df_companions.columns:
                return {"companions": {}, "gameCompanions": {}}
        except Exception as e:
            print(f"      Warning: Could not load companions.csv: {e}")
            return {"companions": {}, "gameCompanions": {}}

        # Build game -> companions mapping
        game_companions = {}
        for _, row in df_companions.iterrows():
            game_id = str(row['GameID']).strip()
            companions_str = str(row.get('Companions', '')).strip()
            if companions_str and companions_str != 'nan':
                companions_list = [c.strip() for c in companions_str.split('|') if c.strip()]
                if companions_list:
                    game_companions[game_id] = companions_list

        if not game_companions:
            return {"companions": {}, "gameCompanions": {}}

        # Get game data for enrichment
        game_log = self.data.get('game_log')
        if game_log is None or game_log.empty:
            return {"companions": {}, "gameCompanions": game_companions}

        # Helper to extract plain game ID from hyperlink formula
        import re
        def extract_game_id(value):
            if not value:
                return ''
            value = str(value).strip()
            # Check if it's a HYPERLINK formula: =HYPERLINK("...", "BAL199506240")
            match = re.search(r'HYPERLINK\([^,]+,\s*"([^"]+)"\)', value)
            if match:
                return match.group(1)
            return value

        # Build stats per companion
        companion_stats = {}

        for _, game_row in game_log.iterrows():
            raw_game_id = game_row.get('GameID', '')
            game_id = extract_game_id(raw_game_id)
            if game_id not in game_companions:
                continue

            companions = game_companions[game_id]
            venue = str(game_row.get('Venue', '')).strip()
            # Handle both 'Home Team' and 'Home' column names
            home_team = str(game_row.get('Home Team', game_row.get('Home', ''))).strip()
            away_team = str(game_row.get('Away Team', game_row.get('Away', ''))).strip()
            date = str(game_row.get('Date', '')).strip()

            # Normalize stadium name (e.g., AT&T Park -> Oracle Park)
            normalized_venue = normalize_stadium(venue)

            for companion in companions:
                if companion not in companion_stats:
                    companion_stats[companion] = {
                        "name": companion,
                        "totalGames": 0,
                        "stadiums": set(),
                        "stadiumsList": [],
                        "teams": {},
                        "oriolesGames": 0,
                        "oriolesStadiums": set(),
                        "games": []
                    }

                stats = companion_stats[companion]
                stats["totalGames"] += 1
                stats["stadiums"].add(normalized_venue)

                # Track teams seen
                for team in [home_team, away_team]:
                    if team:
                        stats["teams"][team] = stats["teams"].get(team, 0) + 1

                # Track Orioles games specifically
                if home_team == 'BAL' or away_team == 'BAL':
                    stats["oriolesGames"] += 1
                    stats["oriolesStadiums"].add(normalized_venue)

                # Format date consistently as MM/DD/YYYY
                formatted_date = date
                if hasattr(game_row.get('Date'), 'strftime'):
                    formatted_date = game_row.get('Date').strftime("%m/%d/%Y")
                elif date and '-' in date:
                    # Handle "2025-09-28 00:00:00" or "2025-09-28" format
                    date_part = date.split(' ')[0]
                    parts = date_part.split('-')
                    if len(parts) == 3:
                        formatted_date = f"{parts[1]}/{parts[2]}/{parts[0]}"

                stats["games"].append({
                    "gameId": game_id,
                    "date": formatted_date,
                    "venue": venue,
                    "homeTeam": home_team,
                    "awayTeam": away_team
                })

        # Convert sets to lists and finalize
        result = {}
        for name, stats in companion_stats.items():
            result[name] = {
                "name": name,
                "totalGames": stats["totalGames"],
                "uniqueStadiums": len(stats["stadiums"]),
                "stadiumsList": sorted(list(stats["stadiums"])),
                "teams": stats["teams"],
                "oriolesGames": stats["oriolesGames"],
                "oriolesStadiums": len(stats["oriolesStadiums"]),
                "oriolesStadiumsList": sorted(list(stats["oriolesStadiums"])),
                "games": sorted(stats["games"], key=lambda x: (
                    # Convert MM/DD/YYYY to YYYYMMDD for proper chronological sort
                    (lambda d: f"{d[2]}{d[0].zfill(2)}{d[1].zfill(2)}" if len(d) == 3 else "")
                    (x.get("date", "").split("/"))
                ), reverse=True)
            }

        return {
            "companions": result,
            "gameCompanions": game_companions
        }

    def _annotate_career_highs(self, json_data):
        """Annotate playerGames and pitcherGames with career/season high flags."""
        from pathlib import Path
        cache_path = Path(__file__).parent.parent.parent / 'cache' / 'career_highs.json'
        if not cache_path.exists():
            return
        try:
            with cache_path.open("r", encoding="utf-8") as handle:
                highs_cache = json.load(handle)
        except (json.JSONDecodeError, IOError):
            return
        if not highs_cache:
            return

        # Mapping from serialized field names to API stat names
        hitting_map = {
            'h': 'hits', 'hr': 'homeRuns', 'rbi': 'rbi', 'r': 'runs',
            'bb': 'baseOnBalls', 'sb': 'stolenBases', 'doubles': 'doubles',
            'triples': 'triples', 'so': 'strikeOuts',
        }
        # Display names for the flags
        hitting_display = {
            'hits': 'H', 'homeRuns': 'HR', 'rbi': 'RBI', 'runs': 'R',
            'baseOnBalls': 'BB', 'stolenBases': 'SB', 'doubles': '2B',
            'triples': '3B', 'strikeOuts': 'K',
        }
        pitching_map = {
            'so': 'strikeOuts', 'h': 'hits', 'er': 'earnedRuns',
            'bb': 'baseOnBalls', 'hr': 'homeRuns',
        }
        pitching_display = {
            'strikeOuts': 'K', 'hits': 'H', 'earnedRuns': 'ER',
            'baseOnBalls': 'BB', 'homeRuns': 'HR',
        }

        # Flag only CLEAR career highs — strict val > c_high. Ties to a
        # player's career high are intentionally suppressed (they're noisier
        # than they're worth, and the cache can't reliably tell whether a
        # tied game set the high or matched it after the fact).
        annotated = 0
        for pg in json_data.get('playerGames', []):
            pid = pg.get('playerId', '')
            player_data = highs_cache.get(pid)
            if not player_data:
                continue

            career = player_data.get('career_highs', {})
            career_high_stats = []

            for field, api_key in hitting_map.items():
                val = pg.get(field, 0) or 0
                if val <= 0:
                    continue
                c_high = career.get(api_key)
                if c_high is None or c_high <= 0:
                    continue
                if val > c_high:
                    career_high_stats.append(hitting_display.get(api_key, api_key))

            # totalBases
            tb = (pg.get('h', 0) - pg.get('doubles', 0) - pg.get('triples', 0) - pg.get('hr', 0)) + \
                 pg.get('doubles', 0) * 2 + pg.get('triples', 0) * 3 + pg.get('hr', 0) * 4
            if tb > 0:
                c_tb = career.get('totalBases')
                if c_tb is not None and c_tb > 0 and tb > c_tb:
                    career_high_stats.append('TB')

            if career_high_stats:
                pg['careerHighs'] = career_high_stats
                annotated += 1

        # Pitching
        for pg in json_data.get('pitcherGames', []):
            pid = pg.get('playerId', '')
            player_data = highs_cache.get(pid)
            if not player_data:
                continue

            career = player_data.get('career_highs_pitching', {})
            if not career:
                continue

            career_high_stats = []

            for field, api_key in pitching_map.items():
                val = pg.get(field, 0) or 0
                if val <= 0:
                    continue
                # Only flag strikeouts on the pitching side — H/ER/BB/HR
                # allowed are bad outcomes and don't deserve a career-high.
                if api_key != 'strikeOuts':
                    continue
                c_high = career.get(api_key)
                if c_high is None or c_high <= 0:
                    continue
                if val > c_high:
                    career_high_stats.append(pitching_display.get(api_key, api_key))

            # IP
            outs = pg.get('outs', 0)
            if outs > 0:
                ip_numeric = outs / 3
                c_ip = career.get('inningsPitched')
                if c_ip:
                    parts = str(c_ip).split('.')
                    c_ip_num = int(parts[0]) + (int(parts[1]) / 3 if len(parts) > 1 else 0)
                    if c_ip_num > 0 and ip_numeric > c_ip_num:
                        career_high_stats.append('IP')

            if career_high_stats:
                pg['careerHighs'] = career_high_stats
                annotated += 1

        if annotated > 0:
            print(f"      Career/season highs: annotated {annotated} player-games")

    def _load_player_bios(self):
        """Load cached player biographical data."""
        from pathlib import Path
        bio_path = Path(__file__).parent.parent.parent / 'cache' / 'player_bios.json'
        if bio_path.exists():
            try:
                with open(bio_path, 'r') as f:
                    return json.load(f)
            except (json.JSONDecodeError, IOError):
                pass
        return {}

    def _serialize_abs_player_stats(self, raw_games):
        """Build player-level ABS challenge statistics from all games."""
        player_stats = {}  # name -> ABS challenge totals by player and role

        # Build MLB API ID -> name lookup from player bios
        bios = self._load_player_bios()
        mlb_id_to_name = {}
        for bref_id, bio in bios.items():
            if bio.get('mlbApiId'):
                mlb_id_to_name[str(bio['mlbApiId'])] = bio.get('name', '')

        for game in raw_games:
            abs_data = game.get('abs_challenges') or {}
            reviews = abs_data.get('reviews', [])
            if not reviews:
                continue
            game_id = game.get('game_id', '')
            bi = game.get('basic_info', {})
            date = bi.get('date_yyyymmdd', '')

            for review in reviews:
                # Track the challenger
                challenger_type = review.get('challengerType', '')
                if not challenger_type:
                    challenger_type = 'batter' if review.get('isBatterChallenge', review.get('is_batter', False)) else 'catcher'
                challenger_name = review.get('challengePlayer', '')
                if not challenger_name:
                    cpid = review.get('challengingPlayerId', '')
                    challenger_name = mlb_id_to_name.get(cpid, '')
                if not challenger_name:
                    if challenger_type == 'batter':
                        challenger_name = review.get('batter', '')
                    elif challenger_type == 'pitcher':
                        challenger_name = review.get('pitcher', '')
                    else:
                        challenger_name = review.get('batter', '') + ' (catcher)'

                if not challenger_name:
                    continue

                if challenger_name not in player_stats:
                    player_stats[challenger_name] = {
                        'name': challenger_name,
                        'challenges': 0,
                        'overturned': 0,
                        'upheld': 0,
                        'asBatter': 0,
                        'asCatcher': 0,
                        'asPitcher': 0,
                        'batterOverturned': 0,
                        'batterUpheld': 0,
                        'catcherOverturned': 0,
                        'catcherUpheld': 0,
                        'pitcherOverturned': 0,
                        'pitcherUpheld': 0,
                        'edgeDistances': [],
                        'gameIds': set(),
                    }
                ps = player_stats[challenger_name]
                ps['challenges'] += 1
                overturned = bool(review.get('overturned'))
                if overturned:
                    ps['overturned'] += 1
                else:
                    ps['upheld'] += 1
                if challenger_type == 'batter':
                    ps['asBatter'] += 1
                    ps['batterOverturned' if overturned else 'batterUpheld'] += 1
                elif challenger_type == 'pitcher':
                    ps['asPitcher'] += 1
                    ps['pitcherOverturned' if overturned else 'pitcherUpheld'] += 1
                else:
                    ps['asCatcher'] += 1
                    ps['catcherOverturned' if overturned else 'catcherUpheld'] += 1
                if review.get('edgeDistance') is not None:
                    ps['edgeDistances'].append(review['edgeDistance'])
                if game_id:
                    ps['gameIds'].add(game_id)

        # Convert to list and compute derived stats
        result = []
        for ps in player_stats.values():
            avg_edge = round(sum(ps['edgeDistances']) / len(ps['edgeDistances']), 3) if ps['edgeDistances'] else None
            batter_rate = round(ps['batterOverturned'] / ps['asBatter'] * 100) if ps['asBatter'] > 0 else None
            catcher_rate = round(ps['catcherOverturned'] / ps['asCatcher'] * 100) if ps['asCatcher'] > 0 else None
            pitcher_rate = round(ps['pitcherOverturned'] / ps['asPitcher'] * 100) if ps['asPitcher'] > 0 else None
            result.append({
                'name': ps['name'],
                'challenges': ps['challenges'],
                'overturned': ps['overturned'],
                'upheld': ps['upheld'],
                'successRate': round(ps['overturned'] / ps['challenges'] * 100) if ps['challenges'] > 0 else 0,
                'asBatter': ps['asBatter'],
                'asCatcher': ps['asCatcher'],
                'asPitcher': ps['asPitcher'],
                'batterOverturned': ps['batterOverturned'],
                'batterUpheld': ps['batterUpheld'],
                'batterSuccessRate': batter_rate,
                'catcherOverturned': ps['catcherOverturned'],
                'catcherUpheld': ps['catcherUpheld'],
                'catcherSuccessRate': catcher_rate,
                'pitcherOverturned': ps['pitcherOverturned'],
                'pitcherUpheld': ps['pitcherUpheld'],
                'pitcherSuccessRate': pitcher_rate,
                'avgEdgeDistance': avg_edge,
                'games': len(ps['gameIds']),
            })

        result.sort(key=lambda x: x['challenges'], reverse=True)
        return result

    def _serialize_umpire_log(self, raw_games):
        """Build umpire tracking data: how many times each umpire has been seen."""
        umpire_stats = {}  # name -> {games, positions, firstSeen, lastSeen, gameIds}

        for game in raw_games:
            umpires = game.get('umpires', {})
            if not umpires:
                continue
            game_id = game.get('game_id', '')
            bi = game.get('basic_info', {})
            date = bi.get('date_yyyymmdd', '')

            for pos, name in umpires.items():
                if not name:
                    continue
                if name not in umpire_stats:
                    umpire_stats[name] = {
                        'name': name,
                        'games': 0,
                        'positions': {},
                        'firstSeen': date,
                        'lastSeen': date,
                        'gameIds': [],
                        'absChallenges': 0,
                        'absOverturned': 0,
                        'absUpheld': 0,
                    }
                umpire_stats[name]['games'] += 1
                existing_ids = {g['gameId'] if isinstance(g, dict) else g for g in umpire_stats[name]['gameIds']}
                if game_id and game_id not in existing_ids:
                    umpire_stats[name]['gameIds'].append({'gameId': game_id, 'position': pos})
                umpire_stats[name]['positions'][pos] = umpire_stats[name]['positions'].get(pos, 0) + 1
                if date and date < umpire_stats[name]['firstSeen']:
                    umpire_stats[name]['firstSeen'] = date
                if date and date > umpire_stats[name]['lastSeen']:
                    umpire_stats[name]['lastSeen'] = date

            # Track ABS challenges against HP umpire
            hp_umpire = umpires.get('HP', '')
            abs_data = game.get('abs_challenges', {})
            if hp_umpire and abs_data and hp_umpire in umpire_stats:
                reviews = abs_data.get('reviews', [])
                if reviews:
                    # Savant-sourced reviews are authoritative
                    umpire_stats[hp_umpire]['absChallenges'] += len(reviews)
                    umpire_stats[hp_umpire]['absOverturned'] += sum(1 for r in reviews if r.get('overturned'))
                    umpire_stats[hp_umpire]['absUpheld'] += sum(1 for r in reviews if not r.get('overturned'))
                else:
                    # Fallback for old cached data: use summary totals
                    for side in ('away', 'home'):
                        sd = abs_data.get(side, {})
                        successful = sd.get('usedSuccessful', 0) or 0
                        failed = sd.get('usedFailed', 0) or 0
                        umpire_stats[hp_umpire]['absChallenges'] += successful + failed
                        umpire_stats[hp_umpire]['absOverturned'] += successful
                        umpire_stats[hp_umpire]['absUpheld'] += failed

        # Format dates
        for u in umpire_stats.values():
            for field in ['firstSeen', 'lastSeen']:
                d = u[field]
                if d and len(d) == 8:
                    u[field] = f"{d[4:6]}/{d[6:8]}/{d[0:4]}"

        return sorted(umpire_stats.values(), key=lambda x: x['games'], reverse=True)

    def _serialize_first_round_draft_picks(self, raw_games):
        """Build draft-pick collection (first-round grid + by-round grid).

        Cross-references attended players against the cached MLB draft index.
        BREF-parsed games don't populate mlb_id on player rows, so we fall
        back to a bref_id -> mlb_id lookup via the Chadwick Register. Without
        that fallback, anyone seen only in older BREF games (e.g., Heston
        Kjerstad) silently drops out.
        """
        try:
            from ..scrapers.draft_scraper import load_index as _load_draft_index
        except Exception:
            return self._empty_draft_payload()

        try:
            draft_index = _load_draft_index() or {}
        except Exception:
            draft_index = {}

        if not draft_index:
            return self._empty_draft_payload()

        bref_to_mlb = self._load_bref_to_mlb_map()

        # Collect attended players once, regardless of how many games they appeared in.
        seen = {}  # mlb_id (str) -> meta
        for game in raw_games:
            bi = game.get('basic_info', {}) or {}
            game_id = game.get('game_id', '')
            date_yyyymmdd = bi.get('date_yyyymmdd', '') or ''
            display_date = ''
            if len(date_yyyymmdd) == 8:
                display_date = f"{date_yyyymmdd[4:6]}/{date_yyyymmdd[6:8]}/{date_yyyymmdd[0:4]}"

            for side in ('home', 'away'):
                team_code = bi.get(f'{side}_team_code', '') or ''
                for section in ('batting', 'pitching'):
                    for p in game.get(section, {}).get(side, []) or []:
                        mlb_id = p.get('mlb_id')
                        if not mlb_id:
                            # BREF games don't carry mlb_id — fall back to
                            # bref_id via Chadwick Register.
                            bref_id = p.get('player_id') or ''
                            mlb_id = bref_to_mlb.get(bref_id)
                            if not mlb_id:
                                continue
                        key = str(mlb_id)
                        if key in seen:
                            seen[key]['teams'].add(team_code)
                            continue
                        seen[key] = {
                            'name': p.get('name', ''),
                            'teams': {team_code} if team_code else set(),
                            'firstGameId': game_id,
                            'firstGameDate': display_date,
                            'firstGameDateSort': date_yyyymmdd,
                        }

        # Intersect with the draft index.
        by_pick = {}        # roundPick (round 1 only) -> [player records]
        by_round = {}       # round number -> [player records]
        years_covered = set()

        for mlb_id_str, meta in seen.items():
            pick = draft_index.get(mlb_id_str)
            if not pick:
                continue
            round_num = pick.get('round')
            round_pick = pick.get('roundPick')
            if not isinstance(round_num, int) or not isinstance(round_pick, int):
                continue

            record = {
                'mlbId': pick.get('mlb_id'),
                'name': pick.get('fullName') or meta['name'],
                'year': pick.get('year'),
                'round': round_num,
                'roundPick': round_pick,
                'overallPick': pick.get('overallPick'),
                'draftTeam': pick.get('teamAbbrev') or pick.get('team') or '',
                'school': pick.get('school') or '',
                'schoolClass': pick.get('schoolClass') or '',
                'signingBonus': pick.get('signingBonus') or '',
                'attendedAs': sorted(meta['teams']),
                'firstGameId': meta['firstGameId'],
                'firstGameDate': meta['firstGameDate'],
            }

            if round_num == 1:
                by_pick.setdefault(round_pick, []).append(record)
            by_round.setdefault(round_num, []).append(record)
            years_covered.add(pick.get('year'))

        # Sort entries within each bucket: round 1 grid by draft year desc;
        # by-round buckets by (round pick asc, year desc) so the lowest pick
        # in each round bubbles to the top.
        for pnum in by_pick:
            by_pick[pnum].sort(key=lambda r: -(r.get('year') or 0))
        for rnum in by_round:
            by_round[rnum].sort(key=lambda r: (r.get('roundPick') or 99, -(r.get('year') or 0)))

        # First-round grid sizing: most years cap at 30; comp-era years stretch
        # to 35-ish. Snap to the actual max present in the index.
        max_first_round_pick = 0
        for pick in draft_index.values():
            if pick.get('round') == 1:
                rp = pick.get('roundPick') or 0
                if rp > max_first_round_pick:
                    max_first_round_pick = rp
        if max_first_round_pick < 30:
            max_first_round_pick = 30

        # Rounds grid: bound to the user's deepest round seen (so we don't
        # render dozens of empty cells from 1970s drafts the user hasn't
        # touched), but always show at least 50 — the typical pre-2021 depth
        # — so the "every round" challenge is visible.
        user_max_round = max(by_round.keys()) if by_round else 0
        max_round = max(50, user_max_round)

        picks_seen = sum(1 for p in range(1, max_first_round_pick + 1) if by_pick.get(p))
        rounds_seen = sum(1 for r in range(1, max_round + 1) if by_round.get(r))
        players_seen = sum(len(v) for v in by_round.values())
        first_round_player_count = sum(len(v) for v in by_pick.values())

        return {
            "byPick": {str(k): v for k, v in by_pick.items()},
            "byRound": {str(k): v for k, v in by_round.items()},
            "totalPicks": max_first_round_pick,
            "totalRounds": max_round,
            "picksSeen": picks_seen,
            "roundsSeen": rounds_seen,
            "playersSeen": players_seen,
            "firstRoundPlayersSeen": first_round_player_count,
            "yearsCovered": sorted(y for y in years_covered if y),
        }

    def _empty_draft_payload(self):
        return {
            "byPick": {}, "byRound": {},
            "totalPicks": 0, "totalRounds": 0,
            "picksSeen": 0, "roundsSeen": 0,
            "playersSeen": 0, "firstRoundPlayersSeen": 0,
            "yearsCovered": [],
        }

    def _load_bref_to_mlb_map(self):
        """Build {bref_id: mlb_id} from the Chadwick Register CSVs.

        Cached on the instance — same source the career-firsts backfill uses.
        Returns an empty dict if the register isn't on disk.
        """
        cached = getattr(self, '_bref_to_mlb_cache', None)
        if cached is not None:
            return cached
        import csv as _csv
        from ..utils.constants import BASE_DIR
        register_dir = BASE_DIR / 'register-master' / 'data'
        mapping = {}
        if register_dir.is_dir():
            for csv_path in sorted(register_dir.glob('people-*.csv')):
                try:
                    with open(csv_path, 'r', encoding='utf-8', errors='replace') as f:
                        reader = _csv.DictReader(f)
                        for row in reader:
                            mlbam = (row.get('key_mlbam') or '').strip()
                            if not mlbam:
                                continue
                            try:
                                mlb_id = int(mlbam)
                            except ValueError:
                                continue
                            for field in ('key_bbref', 'key_bbref_minors'):
                                bref = (row.get(field) or '').strip()
                                if bref:
                                    mapping[bref] = mlb_id
                except Exception:
                    continue
        self._bref_to_mlb_cache = mapping
        return mapping

    def _serialize_jersey_log(self, raw_games):
        """Build jersey number collection: track every number 00-99 seen."""
        # number -> [{name, team, gameId, date}]
        jersey_data = {}

        for game in raw_games:
            game_id = game.get('game_id', '')
            bi = game.get('basic_info', {})
            game_type = (bi.get('game_type') or 'regular').lower()
            date = bi.get('date_yyyymmdd', '')
            formatted_date = ''
            if date and len(date) == 8:
                formatted_date = f"{date[4:6]}/{date[6:8]}/{date[0:4]}"

            for side in ['away', 'home']:
                team = bi.get(f'{side}_team_code', '')
                for section in ['batting', 'pitching']:
                    for player in game.get(section, {}).get(side, []):
                        jersey = player.get('jersey_number', '')
                        if not jersey:
                            continue
                        name = player.get('name', '')
                        player_id = player.get('player_id', '')

                        if jersey not in jersey_data:
                            jersey_data[jersey] = []

                        # Only add first sighting per player per number
                        if not any(e['playerId'] == player_id for e in jersey_data[jersey]):
                            jersey_data[jersey].append({
                                'name': name,
                                'playerId': player_id,
                                'team': team,
                                'gameId': game_id,
                                'date': formatted_date,
                                'gameType': game_type,
                            })

        return jersey_data
