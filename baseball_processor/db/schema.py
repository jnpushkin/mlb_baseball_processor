"""
SQLite database schema for MLB Baseball Processor.

Tables:
- games: Core game metadata (date, teams, scores, venue, game_type)
- batting_lines: Individual player batting lines per game
- pitching_lines: Individual player pitching lines per game
- milestones: Detected milestones (type, player, game reference)
- career_firsts: Career first events for players
- processing_runs: Audit trail of processing runs
"""

SCHEMA_VERSION = 1

SCHEMA_SQL = """
-- Processing run audit trail
CREATE TABLE IF NOT EXISTS processing_runs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    started_at TEXT NOT NULL DEFAULT (datetime('now')),
    completed_at TEXT,
    source TEXT NOT NULL,
    games_processed INTEGER DEFAULT 0,
    errors INTEGER DEFAULT 0,
    notes TEXT
);

-- Core game data
CREATE TABLE IF NOT EXISTS games (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    game_id TEXT UNIQUE NOT NULL,
    date TEXT NOT NULL,
    date_yyyymmdd TEXT,
    away_team TEXT NOT NULL,
    home_team TEXT NOT NULL,
    away_team_code TEXT,
    home_team_code TEXT,
    away_score INTEGER,
    home_score INTEGER,
    venue TEXT,
    game_type TEXT DEFAULT 'regular',
    source TEXT NOT NULL DEFAULT 'bref',
    raw_json TEXT,
    created_at TEXT NOT NULL DEFAULT (datetime('now')),
    updated_at TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE INDEX IF NOT EXISTS idx_games_date ON games(date_yyyymmdd);
CREATE INDEX IF NOT EXISTS idx_games_teams ON games(home_team_code, away_team_code);
CREATE INDEX IF NOT EXISTS idx_games_type ON games(game_type);

-- Player batting lines
CREATE TABLE IF NOT EXISTS batting_lines (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    game_id INTEGER NOT NULL REFERENCES games(id) ON DELETE CASCADE,
    player_id TEXT,
    player_name TEXT NOT NULL,
    team TEXT NOT NULL,
    side TEXT NOT NULL,
    ab INTEGER DEFAULT 0,
    r INTEGER DEFAULT 0,
    h INTEGER DEFAULT 0,
    rbi INTEGER DEFAULT 0,
    bb INTEGER DEFAULT 0,
    so INTEGER DEFAULT 0,
    pa INTEGER DEFAULT 0,
    hr INTEGER DEFAULT 0,
    doubles INTEGER DEFAULT 0,
    triples INTEGER DEFAULT 0,
    sb INTEGER DEFAULT 0,
    cs INTEGER DEFAULT 0,
    hbp INTEGER DEFAULT 0,
    gidp INTEGER DEFAULT 0,
    UNIQUE(game_id, player_id, side)
);

CREATE INDEX IF NOT EXISTS idx_batting_game ON batting_lines(game_id);
CREATE INDEX IF NOT EXISTS idx_batting_player ON batting_lines(player_id);

-- Player pitching lines
CREATE TABLE IF NOT EXISTS pitching_lines (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    game_id INTEGER NOT NULL REFERENCES games(id) ON DELETE CASCADE,
    player_id TEXT,
    player_name TEXT NOT NULL,
    team TEXT NOT NULL,
    side TEXT NOT NULL,
    pitcher_order INTEGER DEFAULT 0,
    ip TEXT DEFAULT '0.0',
    h INTEGER DEFAULT 0,
    r INTEGER DEFAULT 0,
    er INTEGER DEFAULT 0,
    bb INTEGER DEFAULT 0,
    so INTEGER DEFAULT 0,
    hr INTEGER DEFAULT 0,
    wins INTEGER DEFAULT 0,
    losses INTEGER DEFAULT 0,
    saves INTEGER DEFAULT 0,
    game_starts INTEGER DEFAULT 0,
    UNIQUE(game_id, player_id, side)
);

CREATE INDEX IF NOT EXISTS idx_pitching_game ON pitching_lines(game_id);
CREATE INDEX IF NOT EXISTS idx_pitching_player ON pitching_lines(player_id);

-- Detected milestones
CREATE TABLE IF NOT EXISTS milestones (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    game_id INTEGER NOT NULL REFERENCES games(id) ON DELETE CASCADE,
    milestone_type TEXT NOT NULL,
    player_name TEXT NOT NULL,
    player_id TEXT,
    team TEXT NOT NULL,
    opponent TEXT NOT NULL,
    details TEXT,
    UNIQUE(game_id, milestone_type, player_name)
);

CREATE INDEX IF NOT EXISTS idx_milestones_type ON milestones(milestone_type);
CREATE INDEX IF NOT EXISTS idx_milestones_game ON milestones(game_id);

-- Career firsts cache
CREATE TABLE IF NOT EXISTS career_firsts (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    player_id TEXT NOT NULL,
    player_name TEXT,
    event_type TEXT NOT NULL,
    game_id TEXT,
    date TEXT,
    details TEXT,
    UNIQUE(player_id, event_type)
);

CREATE INDEX IF NOT EXISTS idx_firsts_player ON career_firsts(player_id);

-- Schema version tracking
CREATE TABLE IF NOT EXISTS schema_version (
    version INTEGER PRIMARY KEY
);
"""
