"""
All-Time Passing Engine
=======================
Detects when players pass other players on MLB all-time leaderboards.
For example: "Craig Kimbrel moved to 7th on the all-time saves list, passing Dennis Eckersley"
"""

import json
from pathlib import Path
from typing import Optional


def get_project_root() -> Path:
    """Get the project root directory."""
    current = Path(__file__).resolve()
    for parent in [current] + list(current.parents):
        if (parent / '.project_root').exists():
            return parent
        if (parent / 'baseball_processor').is_dir():
            return parent
    return Path.cwd()


def get_leaderboards_dir() -> Path:
    """Get the directory containing all-time leaders JSON files."""
    return get_project_root() / 'mlb_references' / 'all_time_leaders'


# Stat key mapping from career_firsts format to leaderboard files
# career_firsts uses stats like 'H', 'HR', etc. in batting_milestones/pitching_milestones
BATTING_STAT_TO_FILE = {
    'H': 'batting_hits.json',
    'HR': 'batting_home_runs.json',
    'RBI': 'batting_rbi.json',
    'R': 'batting_runs.json',
    '2B': 'batting_doubles.json',
    '3B': 'batting_triples.json',
    'SB': 'batting_stolen_bases.json',
    'BB': 'batting_walks.json',
    'TB': 'batting_total_bases.json',
    'G': 'batting_games.json',
}

PITCHING_STAT_TO_FILE = {
    'SV': 'pitching_saves.json',
    'W': 'pitching_wins.json',
    'SO': 'pitching_strikeouts.json',
    'IP': 'pitching_innings.json',
    'G': 'pitching_games.json',
    'GS': 'pitching_games_started.json',
    'CG': 'pitching_complete_games.json',
    'SHO': 'pitching_shutouts.json',
}

# Human-readable stat names for display
STAT_DISPLAY_NAMES = {
    'H': 'Hits',
    'HR': 'Home Runs',
    'RBI': 'RBIs',
    'R': 'Runs',
    '2B': 'Doubles',
    '3B': 'Triples',
    'SB': 'Stolen Bases',
    'BB': 'Walks',
    'TB': 'Total Bases',
    'G': 'Games',
    'SV': 'Saves',
    'W': 'Wins',
    'SO': 'Strikeouts',
    'IP': 'Innings Pitched',
    'GS': 'Games Started',
    'CG': 'Complete Games',
    'SHO': 'Shutouts',
}


class AllTimePassingEngine:
    """
    Engine to detect when players pass others on all-time leaderboards.

    Usage:
        engine = AllTimePassingEngine()
        passings = engine.check_for_passings(
            player_id='kimbrcr01',
            player_name='Craig Kimbrel',
            stat='SV',
            stat_type='pitching',
            new_value=400,
            game_id='CHN202405150',
            date='2024-05-15'
        )
    """

    def __init__(self):
        self.leaderboards = {}
        self._load_leaderboards()

    def _load_leaderboards(self):
        """Load all available leaderboard JSON files."""
        leaderboards_dir = get_leaderboards_dir()

        if not leaderboards_dir.exists():
            return

        for json_file in leaderboards_dir.glob('*.json'):
            try:
                with open(json_file, 'r') as f:
                    data = json.load(f)

                stat_key = data.get('stat')
                if stat_key:
                    self.leaderboards[stat_key] = data
            except (json.JSONDecodeError, IOError) as e:
                print(f"Warning: Could not load {json_file}: {e}")

    def get_leaderboard(self, stat: str, stat_type: str = 'batting') -> Optional[dict]:
        """
        Get leaderboard for a specific stat.

        Args:
            stat: Stat key (e.g., 'HR', 'SV')
            stat_type: 'batting' or 'pitching'

        Returns:
            Leaderboard dict or None
        """
        # Direct lookup
        if stat in self.leaderboards:
            return self.leaderboards[stat]

        # Try with pitching suffix for games
        if stat == 'G' and stat_type == 'pitching':
            return self.leaderboards.get('G_pitch')

        return None

    def check_for_passings(
        self,
        player_id: str,
        player_name: str,
        stat: str,
        stat_type: str,
        new_value: int,
        game_id: str = '',
        date: str = '',
        venue: str = ''
    ) -> list[dict]:
        """
        Check if a player passed anyone on the all-time list for this stat.

        Args:
            player_id: Baseball Reference player ID (e.g., 'kimbrcr01')
            player_name: Player's display name
            stat: Stat key (e.g., 'HR', 'SV')
            stat_type: 'batting' or 'pitching'
            new_value: The player's new career total after this game
            game_id: BREF game ID (optional)
            date: Date in YYYYMMDD format (optional)
            venue: Venue name (optional)

        Returns:
            List of passing events, each with:
            - player_id, player_name: The player who passed
            - stat, stat_name: The statistic
            - new_value: Their new career total
            - new_rank: Their new rank on the list
            - passed_players: List of players passed (name, value, previous_rank)
            - game_id, date, venue: Game context
        """
        leaderboard = self.get_leaderboard(stat, stat_type)
        if not leaderboard:
            return []

        leaders = leaderboard.get('leaders', [])
        if not leaders:
            return []

        passings = []
        passed_players = []
        new_rank = None

        # Find players who were passed
        for leader in leaders:
            leader_value = leader.get('value', 0)
            leader_id = leader.get('player_id', '')
            leader_rank = leader.get('rank', 0)

            # Skip if this is the same player
            if leader_id == player_id:
                continue

            # Check if player's new value equals or exceeds this leader's value
            # Note: For IP, values can be floats like 5941.1
            if new_value >= leader_value:
                is_tied = (new_value == leader_value)
                passed_players.append({
                    'player_id': leader_id,
                    'name': leader.get('name', 'Unknown'),
                    'value': leader_value,
                    'previous_rank': leader_rank,
                    'tied': is_tied,
                })

        if passed_players:
            # Calculate new rank (count how many are still ahead)
            ahead_count = sum(1 for l in leaders if l.get('value', 0) > new_value and l.get('player_id') != player_id)
            new_rank = ahead_count + 1

            # Only include if rank is in top 200 (or within leaderboard range)
            if new_rank <= len(leaders):
                # Get the player(s) who were actually passed (immediate predecessors)
                # Sort passed players by their rank (highest rank = closest to player)
                passed_players.sort(key=lambda x: x['previous_rank'], reverse=True)

                # Take the most recently passed player(s) - those with highest ranks
                # Usually just 1, but could be multiple if they were tied
                immediate_passed = []
                if passed_players:
                    highest_rank = passed_players[0]['previous_rank']
                    immediate_passed = [p for p in passed_players if p['previous_rank'] >= highest_rank - 1]

                stat_name = STAT_DISPLAY_NAMES.get(stat, stat)

                passings.append({
                    'player_id': player_id,
                    'player_name': player_name,
                    'stat': stat,
                    'stat_name': stat_name,
                    'stat_type': stat_type,
                    'new_value': new_value,
                    'new_rank': new_rank,
                    'passed_players': immediate_passed,
                    'total_passed': len(passed_players),
                    'game_id': game_id,
                    'date': date,
                    'venue': venue,
                })

        return passings

    def find_current_rank(self, player_id: str, stat: str, stat_type: str = 'batting') -> Optional[dict]:
        """
        Find a player's current rank on a leaderboard.

        Returns:
            Dict with rank, value if found, else None
        """
        leaderboard = self.get_leaderboard(stat, stat_type)
        if not leaderboard:
            return None

        for leader in leaderboard.get('leaders', []):
            if leader.get('player_id') == player_id:
                return {
                    'rank': leader.get('rank'),
                    'value': leader.get('value'),
                    'name': leader.get('name'),
                }

        return None

    def get_players_in_range(self, stat: str, stat_type: str, min_value: int, max_value: int) -> list[dict]:
        """
        Get all players within a value range for a stat.

        Useful for finding who a player might pass soon.
        """
        leaderboard = self.get_leaderboard(stat, stat_type)
        if not leaderboard:
            return []

        return [
            leader for leader in leaderboard.get('leaders', [])
            if min_value <= leader.get('value', 0) <= max_value
        ]


def find_all_time_passings_for_milestone(
    engine: AllTimePassingEngine,
    milestone: dict,
    career_totals: dict
) -> list[dict]:
    """
    Check if a career milestone also represents passing someone on the all-time list.

    Args:
        engine: AllTimePassingEngine instance
        milestone: Milestone dict from career_firsts (has stat, milestone_number, game_id, etc.)
        career_totals: Player's career totals dict (batting/pitching -> stat -> value)

    Returns:
        List of passing events
    """
    stat = milestone.get('stat', '')
    stat_type = milestone.get('type', 'batting')

    # Get the career total for this stat after the milestone
    if stat_type == 'batting':
        totals = career_totals.get('batting', {})
    else:
        totals = career_totals.get('pitching', {})

    # The milestone_number IS the value reached (e.g., 400th save means career total is now 400)
    # For "first" milestones, use career_total_after if available
    career_value = milestone.get('career_total_after') or milestone.get('milestone_number', 0)

    if not career_value:
        return []

    return engine.check_for_passings(
        player_id=milestone.get('player_id', ''),
        player_name=milestone.get('player_name', ''),
        stat=stat,
        stat_type=stat_type,
        new_value=career_value,
        game_id=milestone.get('game_id', ''),
        date=milestone.get('date', ''),
        venue=milestone.get('venue', '')
    )


def load_gamelogs_cache() -> dict:
    """Load the gamelogs cache with accurate career totals per game."""
    cache_file = get_project_root() / 'cache' / 'career_gamelogs.json'
    if cache_file.exists():
        try:
            with open(cache_file, 'r') as f:
                return json.load(f)
        except Exception:
            pass
    return {}


def filter_passed_players_by_date(
    passed_leaders: list[dict],
    game_date: str,
    stat_key: str,
    stat_type: str,
    gamelogs_cache: dict
) -> list[dict]:
    """
    Filter passed players to only include those who had reached their leaderboard
    value BY the game date. This excludes players who accumulated their total AFTER
    the passer did (e.g., Yu Darvish reaching 2075 K's after CC Sabathia did).

    Args:
        passed_leaders: List of players who were "passed" based on current leaderboard
        game_date: Date of the game in YYYYMMDD format
        stat_key: Stat being checked (e.g., 'SO', 'HR')
        stat_type: 'batting' or 'pitching'
        gamelogs_cache: Cache of player gamelogs with career totals per game

    Returns:
        Filtered list of passed players
    """
    if not game_date or not gamelogs_cache:
        return passed_leaders

    filtered = []
    for leader in passed_leaders:
        leader_id = leader.get('player_id', '')
        leader_value = leader.get('value', 0)

        # Check if we have gamelogs for this player
        player_gamelogs = gamelogs_cache.get(leader_id, {}).get('gamelogs', {})

        if not player_gamelogs:
            # No gamelogs - include by default (we can't verify)
            filtered.append(leader)
            continue

        # Find the player's career total at or before the game date
        # Gamelogs have game_id format like TEX201205270 (team + date + seq)
        career_at_date = 0
        for gid, gdata in player_gamelogs.items():
            if len(gid) >= 11:
                gl_date = gid[3:11]  # Extract YYYYMMDD
                if gl_date <= game_date:
                    # Get their cumulative total at this game
                    if stat_type == 'batting':
                        val = gdata.get('batting', {}).get(stat_key, 0)
                    else:
                        val = gdata.get('pitching', {}).get(stat_key, 0)
                    if val > career_at_date:
                        career_at_date = val

        # Only include if they had reached their leaderboard value by the game date
        if career_at_date >= leader_value:
            filtered.append(leader)
        # else: they reached their total AFTER the game, exclude them

    return filtered


def find_passings_reverse_lookup(
    engine: AllTimePassingEngine,
    attended_games: list[dict],
    career_firsts_cache: dict,
    gamelogs_cache: dict = None
) -> list[dict]:
    """
    Reverse lookup: For each player on all-time lists, check if you attended
    games where they accumulated stats that passed others on the list.

    Uses three methods in order of preference:
    1. Gamelogs cache: Use accurate cumulative career totals from scraped game logs
    2. Direct match: Check if milestone games match attended games
    3. Interpolation: Estimate career totals for attended games between milestones (fallback)

    Args:
        engine: AllTimePassingEngine instance
        attended_games: List of raw game dicts from attended games
        career_firsts_cache: Full career firsts cache
        gamelogs_cache: Gamelogs cache with accurate career totals per game (optional)

    Returns:
        List of passing events
    """
    # Load gamelogs cache if not provided
    if gamelogs_cache is None:
        gamelogs_cache = load_gamelogs_cache()
    all_passings = []

    # Build lookup of attended games by game_id and by date
    attended_by_id = {}
    attended_by_date = {}
    for game in attended_games:
        game_id = game.get('game_id', '')
        if game_id:
            attended_by_id[game_id] = game
        date = game.get('basic_info', {}).get('date_yyyymmdd', '')
        if date:
            if date not in attended_by_date:
                attended_by_date[date] = []
            attended_by_date[date].append(game)

    # Build a set of player_ids in attended games for quick lookup
    players_in_attended = set()
    for game in attended_games:
        for side in ['home', 'away']:
            for batter in game.get('batting', {}).get(side, []):
                if batter.get('player_id'):
                    players_in_attended.add(batter['player_id'])
            for pitcher in game.get('pitching', {}).get(side, []):
                if pitcher.get('player_id'):
                    players_in_attended.add(pitcher['player_id'])

    # For each stat leaderboard
    for stat_key, leaderboard in engine.leaderboards.items():
        stat_name = leaderboard.get('stat_name', stat_key)
        stat_type = leaderboard.get('type', 'batting')
        leaders = leaderboard.get('leaders', [])

        if not leaders:
            continue

        # Get minimum value on leaderboard (for early exit)
        min_leaderboard_value = min(l['value'] for l in leaders)

        # Build sorted list of threshold values to check against
        threshold_values = sorted([l['value'] for l in leaders], reverse=True)
        value_to_leaders = {}
        for l in leaders:
            v = l['value']
            if v not in value_to_leaders:
                value_to_leaders[v] = []
            value_to_leaders[v].append(l)

        # For each player on the leaderboard
        for leader in leaders:
            player_id = leader.get('player_id', '')
            player_name = leader.get('name', '')
            current_value = leader.get('value', 0)

            if not player_id:
                continue

            # Quick check: did we ever see this player?
            if player_id not in players_in_attended:
                continue

            # Check if this player is in our career_firsts cache
            player_data = career_firsts_cache.get(player_id, {})
            if not player_data:
                continue

            # Get their milestone history for this stat
            if stat_type == 'batting':
                milestones = player_data.get('batting_milestones', {}).get(stat_key, [])
            else:
                milestones = player_data.get('pitching_milestones', {}).get(stat_key, [])

            if not milestones:
                continue

            # Sort milestones by date
            milestones = sorted(milestones, key=lambda m: m.get('date', ''))

            # METHOD 0: Use gamelogs cache if available (accurate data)
            player_gamelogs = gamelogs_cache.get(player_id, {}).get('gamelogs', {})
            if player_gamelogs:
                # Build chronological list of ALL games (not just attended)
                all_player_games = []
                for gid, gdata in player_gamelogs.items():
                    # Extract date from game_id (format: TEAMYYYYMMDD0)
                    if len(gid) >= 11:
                        game_date = gid[3:11]  # YYYYMMDD
                        if stat_type == 'batting':
                            career_val = gdata.get('batting', {}).get(stat_key, 0)
                        else:
                            career_val = gdata.get('pitching', {}).get(stat_key, 0)
                        all_player_games.append((game_date, gid, career_val))

                # Sort by date
                all_player_games.sort(key=lambda x: x[0])

                # Build index for quick lookup
                game_index = {gid: i for i, (_, gid, _) in enumerate(all_player_games)}

                # Check each attended game
                for game_id, game in attended_by_id.items():
                    if game_id not in game_index:
                        continue

                    idx = game_index[game_id]
                    _, _, career_after = all_player_games[idx]

                    if not career_after:
                        continue

                    # Get career total BEFORE this game (from previous game in full gamelog)
                    if idx > 0:
                        _, _, career_before = all_player_games[idx - 1]
                    else:
                        career_before = 0

                    # Only report if there was actual accumulation at this game
                    if career_after <= career_before:
                        continue

                    # Find who was passed or tied SPECIFICALLY at this game
                    passed_leaders = []
                    for v in threshold_values:
                        if career_before < v <= career_after:
                            # Standard detection: crossed or reached a threshold value
                            for l in value_to_leaders.get(v, []):
                                if l['player_id'] != player_id:
                                    # Mark as tied if player reached exactly this value, passed if exceeded
                                    is_tied = (career_after == v)
                                    passed_leaders.append({
                                        'player_id': l['player_id'],
                                        'name': l['name'],
                                        'value': l['value'],
                                        'previous_rank': l['rank'],
                                        'tied': is_tied,
                                    })
                        elif career_before == v and career_after > v:
                            # Surpass detection: was tied at this value, now moved ahead
                            for l in value_to_leaders.get(v, []):
                                if l['player_id'] != player_id:
                                    passed_leaders.append({
                                        'player_id': l['player_id'],
                                        'name': l['name'],
                                        'value': l['value'],
                                        'previous_rank': l['rank'],
                                        'tied': False,
                                    })

                    if passed_leaders and career_after >= min_leaderboard_value:
                        basic_info = game.get('basic_info', {})
                        date = basic_info.get('date_yyyymmdd', '')

                        # Filter out players who reached their total AFTER this game date
                        passed_leaders = filter_passed_players_by_date(
                            passed_leaders, date, stat_key, stat_type, gamelogs_cache
                        )
                        if not passed_leaders:
                            continue

                        passed_leaders.sort(key=lambda x: x['previous_rank'], reverse=True)

                        # Note: rank is approximate based on current leaderboard
                        ahead_count = sum(1 for l in leaders if l['value'] > career_after and l['player_id'] != player_id)
                        approx_rank = ahead_count + 1

                        all_passings.append({
                            'player_id': player_id,
                            'player_name': player_name,
                            'stat': stat_key,
                            'stat_name': stat_name,
                            'stat_type': stat_type,
                            'new_value': career_after,
                            'new_rank': approx_rank,  # Note: approximate, based on current leaderboard
                            'passed_players': passed_leaders[:5],
                            'total_passed': len(passed_leaders),
                            'game_id': game_id,
                            'date': date,
                            'date_display': basic_info.get('date', ''),
                            'venue': basic_info.get('venue', ''),
                            'milestone': f"Career {stat_name} #{int(career_after) if stat_key != 'IP' else career_after}",
                            'accurate': True,
                        })

                # If we used gamelogs, skip the other methods for this player/stat
                continue

            # METHOD 1: Check direct milestone game matches
            for i, milestone in enumerate(milestones):
                game_id = milestone.get('game_id', '')
                milestone_date = milestone.get('date', '')
                career_after = milestone.get('career_total_after', 0) or milestone.get('number', 0)

                if not career_after or career_after < min_leaderboard_value:
                    continue

                game = attended_by_id.get(game_id)
                if not game:
                    continue

                # Get career before
                if i > 0:
                    career_before = milestones[i-1].get('career_total_after', 0) or milestones[i-1].get('number', 0)
                else:
                    career_before = 0

                # Find who they passed or tied
                passed_leaders = []
                for v in threshold_values:
                    if career_before < v <= career_after:
                        for l in value_to_leaders.get(v, []):
                            if l['player_id'] != player_id:
                                is_tied = (career_after == v)
                                passed_leaders.append({
                                    'player_id': l['player_id'],
                                    'name': l['name'],
                                    'value': l['value'],
                                    'previous_rank': l['rank'],
                                    'tied': is_tied,
                                })
                    elif career_before == v and career_after > v:
                        for l in value_to_leaders.get(v, []):
                            if l['player_id'] != player_id:
                                passed_leaders.append({
                                    'player_id': l['player_id'],
                                    'name': l['name'],
                                    'value': l['value'],
                                    'previous_rank': l['rank'],
                                    'tied': False,
                                })

                if passed_leaders:
                    # Filter out players who reached their total AFTER this game date
                    passed_leaders = filter_passed_players_by_date(
                        passed_leaders, milestone_date, stat_key, stat_type, gamelogs_cache
                    )
                    if not passed_leaders:
                        continue

                    ahead_count = sum(1 for l in leaders if l['value'] > career_after and l['player_id'] != player_id)
                    new_rank = ahead_count + 1

                    basic_info = game.get('basic_info', {})
                    passed_leaders.sort(key=lambda x: x['previous_rank'], reverse=True)

                    all_passings.append({
                        'player_id': player_id,
                        'player_name': player_name,
                        'stat': stat_key,
                        'stat_name': stat_name,
                        'stat_type': stat_type,
                        'new_value': career_after,
                        'new_rank': new_rank,
                        'passed_players': passed_leaders[:5],
                        'total_passed': len(passed_leaders),
                        'game_id': game_id,
                        'date': milestone_date,
                        'date_display': basic_info.get('date', ''),
                        'venue': basic_info.get('venue', ''),
                        'milestone': milestone.get('milestone', f"Career {stat_name} #{career_after}"),
                    })

            # METHOD 2: Check actual game stats for games between milestones
            # For each pair of consecutive milestones, check if any attended games fall between
            # AND verify the player actually accumulated the stat in that game
            for i in range(len(milestones)):
                milestone = milestones[i]
                milestone_date = milestone.get('date', '')
                milestone_value = milestone.get('career_total_after', 0) or milestone.get('number', 0)

                if i + 1 < len(milestones):
                    next_milestone = milestones[i + 1]
                    next_date = next_milestone.get('date', '')
                    next_value = next_milestone.get('career_total_after', 0) or next_milestone.get('number', 0)
                else:
                    # After last milestone, use current career total
                    next_date = '99999999'  # Far future
                    next_value = current_value

                if not milestone_value or milestone_value < min_leaderboard_value:
                    continue

                # Check attended games with dates between these milestones
                for date, games in attended_by_date.items():
                    if not (milestone_date < date < next_date):
                        continue

                    # Check if player was in any of these games AND accumulated the stat
                    for game in games:
                        player_record = None
                        stat_in_game = 0

                        for side in ['home', 'away']:
                            if stat_type == 'batting':
                                players = game.get('batting', {}).get(side, [])
                            else:
                                players = game.get('pitching', {}).get(side, [])
                            for p in players:
                                if p.get('player_id') == player_id:
                                    player_record = p
                                    break
                            if player_record:
                                break

                        if not player_record:
                            continue

                        # Check actual game stats to see if player accumulated this stat
                        # Pitching stats
                        if stat_type == 'pitching':
                            if stat_key == 'SV':
                                # Check for save - use the 'save' boolean field
                                if player_record.get('save'):
                                    stat_in_game = 1
                                else:
                                    # Also check pitcher_decisions for save_pitcher_id
                                    decisions = game.get('pitcher_decisions', {})
                                    if decisions.get('save_pitcher_id') == player_id:
                                        stat_in_game = 1
                            elif stat_key == 'W':
                                # Check for win - use the 'win' boolean field
                                if player_record.get('win'):
                                    stat_in_game = 1
                                else:
                                    decisions = game.get('pitcher_decisions', {})
                                    if decisions.get('winning_pitcher_id') == player_id:
                                        stat_in_game = 1
                            elif stat_key == 'SO':
                                stat_in_game = int(player_record.get('SO', 0) or 0)
                            elif stat_key == 'IP':
                                # IP can be string like "6.1" or float
                                ip_val = player_record.get('IP', 0)
                                if isinstance(ip_val, str):
                                    try:
                                        stat_in_game = float(ip_val) if ip_val else 0
                                    except ValueError:
                                        stat_in_game = 0
                                else:
                                    stat_in_game = float(ip_val or 0)
                            elif stat_key in ('G', 'G_pitch'):
                                # Pitcher appeared in game
                                stat_in_game = 1
                            elif stat_key == 'GS':
                                # Check if this pitcher was the starter (first in pitching list)
                                first_pitcher = game.get('pitching', {}).get(side, [{}])[0] if side else None
                                if first_pitcher and first_pitcher.get('player_id') == player_id:
                                    stat_in_game = 1
                            elif stat_key == 'CG':
                                # Complete game - pitcher started and finished
                                # This is harder to detect without specific field
                                pass
                            elif stat_key == 'SHO':
                                # Shutout - even harder to detect
                                pass

                        # Batting stats
                        elif stat_type == 'batting':
                            if stat_key == 'HR':
                                stat_in_game = int(player_record.get('HR', 0) or 0)
                            elif stat_key == 'H':
                                stat_in_game = int(player_record.get('H', 0) or 0)
                            elif stat_key == 'RBI':
                                stat_in_game = int(player_record.get('RBI', 0) or 0)
                            elif stat_key == 'R':
                                stat_in_game = int(player_record.get('R', 0) or 0)
                            elif stat_key == '2B':
                                stat_in_game = int(player_record.get('2B', 0) or 0)
                            elif stat_key == '3B':
                                stat_in_game = int(player_record.get('3B', 0) or 0)
                            elif stat_key == 'SB':
                                stat_in_game = int(player_record.get('SB', 0) or 0)
                            elif stat_key == 'BB':
                                stat_in_game = int(player_record.get('BB', 0) or 0)
                            elif stat_key == 'TB':
                                # Total bases = 1*1B + 2*2B + 3*3B + 4*HR
                                h = int(player_record.get('H', 0) or 0)
                                doubles = int(player_record.get('2B', 0) or 0)
                                triples = int(player_record.get('3B', 0) or 0)
                                hr = int(player_record.get('HR', 0) or 0)
                                singles = h - doubles - triples - hr
                                stat_in_game = singles + 2*doubles + 3*triples + 4*hr
                            elif stat_key == 'G':
                                # Player appeared in game
                                stat_in_game = 1

                        # Skip if player didn't accumulate this stat in this game
                        if stat_in_game <= 0:
                            continue

                        # Estimate career total at this game using interpolation
                        # This gives us an approximate value for checking thresholds
                        try:
                            d1 = int(milestone_date)
                            d2 = int(next_date) if next_date != '99999999' else int(date) + 30
                            d = int(date)
                            if d2 > d1:
                                ratio = (d - d1) / (d2 - d1)
                                estimated_value = int(milestone_value + ratio * (next_value - milestone_value))
                            else:
                                estimated_value = milestone_value
                        except (ValueError, ZeroDivisionError):
                            estimated_value = milestone_value

                        # For single-event stats (SV, W, G, GS), ensure we're at least 1 past milestone
                        if stat_in_game == 1 and estimated_value <= milestone_value:
                            estimated_value = milestone_value + 1

                        # Check if this estimated value crosses any leaderboard thresholds
                        # that weren't already crossed at the previous milestone
                        passed_leaders = []
                        for v in threshold_values:
                            if milestone_value < v <= estimated_value:
                                for l in value_to_leaders.get(v, []):
                                    if l['player_id'] != player_id:
                                        is_tied = (estimated_value == v)
                                        passed_leaders.append({
                                            'player_id': l['player_id'],
                                            'name': l['name'],
                                            'value': l['value'],
                                            'previous_rank': l['rank'],
                                            'tied': is_tied,
                                        })
                            elif milestone_value == v and estimated_value > v:
                                for l in value_to_leaders.get(v, []):
                                    if l['player_id'] != player_id:
                                        passed_leaders.append({
                                            'player_id': l['player_id'],
                                            'name': l['name'],
                                            'value': l['value'],
                                            'previous_rank': l['rank'],
                                            'tied': False,
                                        })

                        if passed_leaders:
                            # Filter out players who reached their total AFTER this game date
                            passed_leaders = filter_passed_players_by_date(
                                passed_leaders, date, stat_key, stat_type, gamelogs_cache
                            )
                            if not passed_leaders:
                                continue

                            ahead_count = sum(1 for l in leaders if l['value'] > estimated_value and l['player_id'] != player_id)
                            new_rank = ahead_count + 1

                            basic_info = game.get('basic_info', {})
                            passed_leaders.sort(key=lambda x: x['previous_rank'], reverse=True)

                            all_passings.append({
                                'player_id': player_id,
                                'player_name': player_name,
                                'stat': stat_key,
                                'stat_name': stat_name,
                                'stat_type': stat_type,
                                'new_value': estimated_value,
                                'new_rank': new_rank,
                                'passed_players': passed_leaders[:5],
                                'total_passed': len(passed_leaders),
                                'game_id': game.get('game_id', ''),
                                'date': date,
                                'date_display': basic_info.get('date', ''),
                                'venue': basic_info.get('venue', ''),
                                'milestone': f"~{estimated_value:,} career {stat_name.lower()} (estimated)",
                                'estimated': True,
                                'stat_in_game': stat_in_game,  # How much they accumulated in this game
                            })

    # Sort by date ASCENDING first (so we process earliest occurrences first)
    all_passings.sort(key=lambda x: (x.get('date', ''), x.get('new_rank', 999)))

    # Deduplicate: A player can only pass another player ONCE per stat
    # Track (player_id, stat, passed_player_id) and keep only the first occurrence
    seen_passings = set()  # (player_id, stat, passed_player_id) tuples
    seen_games = set()  # (player_id, stat, game_id) to avoid duplicate game entries
    unique_passings = []

    for p in all_passings:
        game_key = (p['player_id'], p['stat'], p['game_id'])
        if game_key in seen_games:
            continue

        # Filter passed_players to only include players not yet passed
        filtered_passed = []
        for passed in p.get('passed_players', []):
            passing_key = (p['player_id'], p['stat'], passed['player_id'])
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

    # Now sort by date descending for display (most recent first)
    unique_passings.sort(key=lambda x: (x.get('date', ''), -x.get('new_rank', 999)), reverse=True)

    return unique_passings
