"""Type definitions for MLB Game Tracker.

This module defines TypedDicts and type aliases for the core data structures
used throughout the application. Using these types improves IDE support,
catches bugs early, and serves as documentation.
"""

from __future__ import annotations

from typing import TypedDict, Optional, List, Dict, Any, Union
from datetime import datetime


class PlayerBattingStats(TypedDict, total=False):
    """Batting statistics for a player in a single game."""
    name: str
    player_id: str
    position: str
    AB: int
    R: int
    H: int
    RBI: int
    BB: int
    SO: int
    PA: int
    HR: int
    SB: int
    CS: int
    HBP: int
    GIDP: int
    lineup_slot: Optional[int]
    starter_pos: Optional[str]
    is_starter: Optional[bool]


class PlayerPitchingStats(TypedDict, total=False):
    """Pitching statistics for a player in a single game."""
    name: str
    player_id: str
    IP: str
    H: int
    R: int
    ER: int
    BB: int
    SO: int
    HR: int
    ERA: float
    BF: int
    Pit: int
    Str: int
    decision: Optional[str]
    win: bool
    loss: bool
    save: bool


class BasicGameInfo(TypedDict, total=False):
    """Basic information about a game."""
    away_team: str
    home_team: str
    away_team_code: str
    home_team_code: str
    date: str
    date_yyyymmdd: str
    venue: str
    attendance: str
    attendance_value: int
    away_score: str
    home_score: str
    away_score_value: int
    home_score_value: int
    start_time: str
    duration: str
    weather: str
    temperature_f: int
    doubleheader: str


class LinescoreTeam(TypedDict):
    """Linescore data for one team."""
    innings: List[str]
    R: int
    H: int
    E: int


class Linescore(TypedDict):
    """Complete linescore for a game."""
    away: LinescoreTeam
    home: LinescoreTeam


class LineupEntry(TypedDict):
    """A player's lineup entry."""
    slot: int
    name: str
    player_id: str
    pos: str


class PlayByPlayEntry(TypedDict, total=False):
    """A single play-by-play entry."""
    inning: int
    half: str
    batter: str
    batter_id: str
    pitcher: str
    pitcher_id: str
    description: str
    outs: int
    score: str
    pitch_count: int
    batting_team: str
    home_run: bool
    strikeout: bool
    walk: bool
    double: bool
    triple: bool
    rbi: int
    hit_by_pitch: bool
    double_play: bool
    grand_slam: bool
    inside_the_park_hr: bool


class PitcherDecisions(TypedDict, total=False):
    """Pitcher decisions for a game."""
    winning_pitcher: Optional[str]
    winning_pitcher_id: Optional[str]
    losing_pitcher: Optional[str]
    losing_pitcher_id: Optional[str]
    save_pitcher: Optional[str]
    save_pitcher_id: Optional[str]


class SpecialEvents(TypedDict, total=False):
    """Special events detected in a game."""
    walkoff: Optional[Dict[str, Any]]
    immaculate_innings: List[Dict[str, Any]]
    leadoff_hrs: List[Dict[str, Any]]
    grand_slams: List[Dict[str, Any]]
    pinch_hit_hrs: List[Dict[str, Any]]
    no_hitters: List[Dict[str, Any]]
    complete_games: List[Dict[str, Any]]


class MilestoneStats(TypedDict, total=False):
    """Milestone statistics detected in a game."""
    multi_hr_games: List[Dict[str, Any]]
    cycles: List[Dict[str, Any]]
    four_hit_games: List[Dict[str, Any]]
    five_rbi_games: List[Dict[str, Any]]
    ten_k_games: List[Dict[str, Any]]
    shutouts: List[Dict[str, Any]]
    complete_games: List[Dict[str, Any]]
    perfect_games: List[Dict[str, Any]]


class Umpires(TypedDict, total=False):
    """Umpire assignments for a game."""
    HP: str
    FirstBase: str
    SecondBase: str
    ThirdBase: str
    LF: str
    RF: str


class Substitution(TypedDict, total=False):
    """A substitution made during the game."""
    type: str
    inning: int
    half: str
    player_in: str
    player_out: str
    pos: str
    raw: str
    text: str


class GameData(TypedDict, total=False):
    """Complete parsed game data structure."""
    game_id: str
    doubleheader: str
    basic_info: BasicGameInfo
    batting: Dict[str, List[PlayerBattingStats]]
    pitching: Dict[str, List[PlayerPitchingStats]]
    linescore: Linescore
    lineups: Dict[str, List[LineupEntry]]
    substitutions: List[Substitution]
    play_by_play: List[PlayByPlayEntry]
    raw_plays: List[PlayByPlayEntry]
    pitcher_decisions: PitcherDecisions
    special_events: SpecialEvents
    milestone_stats: MilestoneStats
    umpires: Dict[str, str]
    footer_summary: Dict[str, Dict[str, str]]


# Type aliases for common patterns
GameList = List[GameData]
TeamSide = str  # "home" or "away"
PlayerID = str
GameID = str
DateString = str  # Format: "YYYYMMDD"


# Aggregated statistics types
class AggregatedHitterStats(TypedDict, total=False):
    """Aggregated hitting statistics across multiple games."""
    Name: str
    PlayerID: str  # Using "Player ID" in DataFrames
    Team: str
    G: int
    AB: int
    PA: int
    H: int
    R: int
    RBI: int
    HR: int
    doubles: int  # "2B" in DataFrames
    triples: int  # "3B" in DataFrames
    SB: int
    CS: int
    BB: int
    SO: int
    HBP: int
    GIDP: int
    TB: int
    XBH: int
    AVG: float
    OBP: float
    SLG: float
    OPS: float
    GameIDs: str


class AggregatedPitcherStats(TypedDict, total=False):
    """Aggregated pitching statistics across multiple games."""
    Name: str
    PlayerID: str  # Using "Player ID" in DataFrames
    Team: str
    G: int
    GS: int
    W: int
    L: int
    SV: int
    IP: str
    H: int
    R: int
    ER: int
    BB: int
    SO: int
    HR: int
    ERA: float
    WHIP: float
    GameIDs: str


# Summary row type
class SummaryRow(TypedDict, total=False):
    """A row in the summary statistics."""
    Record: str
    Value: Union[int, str, float]
    Detail: str
    Score: str
    GameIDs: str
