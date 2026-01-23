"""Quick statistics report generator.

This module generates a quick summary report of attendance statistics,
useful for getting a fast overview without generating the full Excel workbook.
"""

from __future__ import annotations

from collections import Counter, defaultdict
from datetime import datetime
from typing import Dict, Any, List, Optional
import statistics

from ..utils.log import info


def generate_quick_stats_report(games: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Generate a quick statistics report from game data.

    Args:
        games: List of parsed game data dictionaries.

    Returns:
        Dictionary containing summary statistics.
    """
    if not games:
        return {"error": "No games to analyze"}

    # Basic counts
    total_games = len(games)

    # Team tracking
    teams_seen = Counter()
    home_teams = Counter()
    venues = Counter()
    years = Counter()

    # Score tracking
    wins = 0
    losses = 0
    total_runs_scored = 0
    total_runs_allowed = 0
    home_runs_seen = 0
    extra_inning_games = 0
    shutouts_seen = 0

    # Attendance tracking
    attendances = []

    # Player tracking
    players_seen = set()
    pitchers_seen = set()

    for game in games:
        basic = game.get('basic_info', {})
        linescore = game.get('linescore', {})

        # Teams and venues
        away_team = basic.get('away_team', 'Unknown')
        home_team = basic.get('home_team', 'Unknown')
        teams_seen[away_team] += 1
        teams_seen[home_team] += 1
        home_teams[home_team] += 1
        venues[basic.get('venue', 'Unknown')] += 1

        # Year
        date_str = basic.get('date_yyyymmdd', '')
        if len(date_str) >= 4:
            years[date_str[:4]] += 1

        # Scores
        away_score = basic.get('away_score_value', 0) or 0
        home_score = basic.get('home_score_value', 0) or 0
        total_runs_scored += away_score + home_score
        total_runs_allowed += away_score + home_score  # Same as scored for attendance

        # Win/loss (assuming user roots for home team in most cases - can be customized)
        if home_score > away_score:
            wins += 1
        elif away_score > home_score:
            losses += 1

        # Shutouts
        if away_score == 0 or home_score == 0:
            shutouts_seen += 1

        # Extra innings
        innings = len(linescore.get('away', {}).get('innings', []))
        if innings > 9:
            extra_inning_games += 1

        # Attendance
        attendance = basic.get('attendance_value', 0)
        if attendance:
            attendances.append(attendance)

        # Players
        for side in ['home', 'away']:
            for player in game.get('batting', {}).get(side, []):
                player_id = player.get('player_id')
                if player_id and player_id != 'UNKNOWN':
                    players_seen.add(player_id)
                # Count home runs
                hr = player.get('HR', 0) or 0
                home_runs_seen += hr

            for pitcher in game.get('pitching', {}).get(side, []):
                pitcher_id = pitcher.get('player_id')
                if pitcher_id and pitcher_id != 'UNKNOWN':
                    pitchers_seen.add(pitcher_id)

    # Calculate attendance statistics
    attendance_stats = {}
    if attendances:
        attendance_stats = {
            'total': sum(attendances),
            'average': round(statistics.mean(attendances)),
            'median': round(statistics.median(attendances)),
            'highest': max(attendances),
            'lowest': min(attendances),
            'games_with_data': len(attendances)
        }

    # Build report
    report = {
        'generated_at': datetime.now().isoformat(),
        'total_games': total_games,
        'record': {
            'wins': wins,
            'losses': losses,
            'win_percentage': round(wins / total_games * 100, 1) if total_games > 0 else 0
        },
        'scoring': {
            'total_runs_seen': total_runs_scored,
            'average_runs_per_game': round(total_runs_scored / total_games, 2) if total_games > 0 else 0,
            'home_runs_seen': home_runs_seen,
            'shutouts_seen': shutouts_seen,
            'extra_inning_games': extra_inning_games
        },
        'attendance': attendance_stats,
        'teams': {
            'unique_teams_seen': len(teams_seen),
            'most_seen': teams_seen.most_common(5),
            'home_teams': home_teams.most_common(5)
        },
        'venues': {
            'unique_venues': len(venues),
            'most_visited': venues.most_common(5)
        },
        'years': {
            'years_covered': sorted(years.keys()),
            'games_by_year': dict(sorted(years.items()))
        },
        'players': {
            'unique_batters_seen': len(players_seen),
            'unique_pitchers_seen': len(pitchers_seen),
            'total_unique_players': len(players_seen | pitchers_seen)
        }
    }

    return report


def print_quick_stats_report(report: Dict[str, Any]) -> None:
    """Print a formatted quick stats report to console.

    Args:
        report: Report dictionary from generate_quick_stats_report().
    """
    if 'error' in report:
        info(f"Error: {report['error']}")
        return

    info("\n" + "=" * 60)
    info("MLB GAME TRACKER - QUICK STATS REPORT")
    info("=" * 60)

    info(f"\nTotal Games Attended: {report['total_games']}")

    # Record
    record = report['record']
    info(f"Record (Home Team): {record['wins']}-{record['losses']} ({record['win_percentage']}%)")

    # Scoring
    scoring = report['scoring']
    info(f"\nScoring:")
    info(f"  Total Runs Seen: {scoring['total_runs_seen']}")
    info(f"  Average per Game: {scoring['average_runs_per_game']}")
    info(f"  Home Runs Seen: {scoring['home_runs_seen']}")
    info(f"  Shutouts Witnessed: {scoring['shutouts_seen']}")
    info(f"  Extra Inning Games: {scoring['extra_inning_games']}")

    # Attendance
    if report['attendance']:
        att = report['attendance']
        info(f"\nAttendance:")
        info(f"  Average: {att['average']:,}")
        info(f"  Highest: {att['highest']:,}")
        info(f"  Lowest: {att['lowest']:,}")
        info(f"  Total: {att['total']:,}")

    # Teams
    teams = report['teams']
    info(f"\nTeams:")
    info(f"  Unique Teams Seen: {teams['unique_teams_seen']}")
    info(f"  Most Seen:")
    for team, count in teams['most_seen'][:5]:
        info(f"    {team}: {count} games")

    # Venues
    venues = report['venues']
    info(f"\nVenues:")
    info(f"  Unique Venues: {venues['unique_venues']}")
    info(f"  Most Visited:")
    for venue, count in venues['most_visited'][:5]:
        info(f"    {venue}: {count} games")

    # Players
    players = report['players']
    info(f"\nPlayers:")
    info(f"  Unique Batters: {players['unique_batters_seen']}")
    info(f"  Unique Pitchers: {players['unique_pitchers_seen']}")
    info(f"  Total Unique: {players['total_unique_players']}")

    # Years
    years = report['years']
    info(f"\nYears: {', '.join(years['years_covered'])}")
    for year, count in years['games_by_year'].items():
        info(f"  {year}: {count} games")

    info("\n" + "=" * 60)
