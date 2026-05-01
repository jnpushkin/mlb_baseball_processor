"""
SQLite database manager for MLB Baseball Processor.

Provides CRUD operations for games, player stats, and milestones.
"""

import json
import sqlite3
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple
from contextlib import contextmanager

from .schema import SCHEMA_SQL, SCHEMA_VERSION


class Database:
    """SQLite database manager."""

    def __init__(self, db_path: Optional[Path] = None):
        if db_path is None:
            from ..utils.constants import BASE_DIR
            db_path = BASE_DIR / "baseball.db"
        self.db_path = db_path
        self._init_db()

    def _init_db(self):
        """Create tables if they don't exist."""
        with self._connect() as conn:
            conn.executescript(SCHEMA_SQL)
            existing = conn.execute("SELECT version FROM schema_version").fetchone()
            if not existing:
                conn.execute("INSERT INTO schema_version (version) VALUES (?)", (SCHEMA_VERSION,))
            conn.commit()

    @contextmanager
    def _connect(self):
        """Context manager for database connections."""
        conn = sqlite3.connect(str(self.db_path))
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA journal_mode=WAL")
        conn.execute("PRAGMA foreign_keys=ON")
        try:
            yield conn
        finally:
            conn.close()

    def game_exists(self, game_id: str) -> bool:
        """Check if a game already exists in the database."""
        with self._connect() as conn:
            row = conn.execute("SELECT 1 FROM games WHERE game_id = ?", (game_id,)).fetchone()
            return row is not None

    def upsert_game(self, game_data: Dict[str, Any]) -> int:
        """Insert or update a game and its associated player stats."""
        basic_info = game_data.get('basic_info', {})
        game_id = game_data.get('game_id', '')

        date = basic_info.get('date', '')
        date_yyyymmdd = basic_info.get('date_yyyymmdd', '')
        away_team = basic_info.get('away_team', '')
        home_team = basic_info.get('home_team', '')
        away_code = basic_info.get('away_team_code', '')
        home_code = basic_info.get('home_team_code', '')
        game_type = basic_info.get('game_type', 'regular')
        source = basic_info.get('source', 'bref')

        with self._connect() as conn:
            conn.execute("""
                INSERT INTO games (game_id, date, date_yyyymmdd, away_team, home_team,
                    away_team_code, home_team_code, away_score, home_score, venue,
                    game_type, source, raw_json, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, datetime('now'))
                ON CONFLICT(game_id) DO UPDATE SET
                    date=excluded.date,
                    date_yyyymmdd=excluded.date_yyyymmdd,
                    away_team=excluded.away_team,
                    home_team=excluded.home_team,
                    away_team_code=excluded.away_team_code,
                    home_team_code=excluded.home_team_code,
                    away_score=excluded.away_score, home_score=excluded.home_score,
                    venue=excluded.venue,
                    game_type=excluded.game_type,
                    source=excluded.source,
                    raw_json=excluded.raw_json, updated_at=datetime('now')
            """, (
                game_id, date, date_yyyymmdd, away_team, home_team,
                away_code, home_code,
                basic_info.get('away_score'), basic_info.get('home_score'),
                basic_info.get('venue', ''), game_type, source,
                json.dumps(game_data),
            ))

            db_id = conn.execute("SELECT id FROM games WHERE game_id = ?", (game_id,)).fetchone()['id']

            # Clear existing lines for re-processing
            conn.execute("DELETE FROM batting_lines WHERE game_id = ?", (db_id,))
            conn.execute("DELETE FROM pitching_lines WHERE game_id = ?", (db_id,))

            # Insert batting lines
            for side in ['away', 'home']:
                team = basic_info.get(f'{side}_team', '')
                for batter in game_data.get('batting', {}).get(side, []):
                    pid = batter.get('player_id') or None
                    name = batter.get('name', '')
                    if not name:
                        continue
                    conn.execute("""
                        INSERT INTO batting_lines
                        (game_id, player_id, player_name, team, side,
                         ab, r, h, rbi, bb, so, pa, hr, doubles, triples, sb, cs, hbp, gidp)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """, (
                        db_id, pid, name, team, side,
                        batter.get('AB', 0), batter.get('R', 0), batter.get('H', 0),
                        batter.get('RBI', 0), batter.get('BB', 0), batter.get('SO', 0),
                        batter.get('PA', 0), batter.get('HR', 0),
                        batter.get('2B', 0), batter.get('3B', 0),
                        batter.get('SB', 0), batter.get('CS', 0),
                        batter.get('HBP', 0), batter.get('GIDP', 0),
                    ))

            # Insert pitching lines
            for side in ['away', 'home']:
                team = basic_info.get(f'{side}_team', '')
                for idx, pitcher in enumerate(game_data.get('pitching', {}).get(side, [])):
                    pid = pitcher.get('player_id') or None
                    name = pitcher.get('name', '')
                    if not name:
                        continue
                    conn.execute("""
                        INSERT INTO pitching_lines
                        (game_id, player_id, player_name, team, side, pitcher_order,
                         ip, h, r, er, bb, so, hr, wins, losses, saves, game_starts)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """, (
                        db_id, pid, name, team, side, idx,
                        str(pitcher.get('IP', '0.0')),
                        pitcher.get('H', 0), pitcher.get('R', 0), pitcher.get('ER', 0),
                        pitcher.get('BB', 0), pitcher.get('SO', 0), pitcher.get('HR', 0),
                        pitcher.get('W', 0), pitcher.get('L', 0), pitcher.get('SV', 0),
                        1 if idx == 0 else 0,
                    ))

            conn.commit()
            return db_id

    def get_all_games(self, game_type: Optional[str] = None) -> List[Dict[str, Any]]:
        """Load all games from database as original JSON format."""
        with self._connect() as conn:
            if game_type:
                rows = conn.execute(
                    "SELECT raw_json FROM games WHERE game_type = ? ORDER BY date_yyyymmdd",
                    (game_type,)
                ).fetchall()
            else:
                rows = conn.execute(
                    "SELECT raw_json FROM games ORDER BY date_yyyymmdd"
                ).fetchall()

            games = []
            for row in rows:
                if row['raw_json']:
                    games.append(json.loads(row['raw_json']))
            return games

    def get_game_count(self, game_type: Optional[str] = None) -> int:
        """Get count of games in database."""
        with self._connect() as conn:
            if game_type:
                row = conn.execute("SELECT COUNT(*) as cnt FROM games WHERE game_type = ?", (game_type,)).fetchone()
            else:
                row = conn.execute("SELECT COUNT(*) as cnt FROM games").fetchone()
            return row['cnt']

    def migrate_from_cache(self, cache_dir: Path) -> Tuple[int, int]:
        """Import games from JSON cache directory into database."""
        if not cache_dir.exists():
            print(f"Cache directory not found: {cache_dir}")
            return (0, 0)

        json_files = list(cache_dir.glob("*.json"))
        skip_patterns = ['career_firsts', 'career_gamelogs']
        json_files = [f for f in json_files if not any(p in str(f) for p in skip_patterns)]

        print(f"Migrating {len(json_files)} games from {cache_dir}...")

        imported = 0
        errors = 0

        with self._connect() as conn:
            conn.execute(
                "INSERT INTO processing_runs (source, notes) VALUES (?, ?)",
                ('migrate', f"Migrating cache from {cache_dir}")
            )
            run_id = conn.execute("SELECT last_insert_rowid()").fetchone()[0]
            conn.commit()

        for json_file in json_files:
            try:
                with open(json_file, 'r', encoding='utf-8') as f:
                    game_data = json.load(f)
                if not isinstance(game_data, dict) or 'basic_info' not in game_data:
                    continue
                self.upsert_game(game_data)
                imported += 1
                if imported % 50 == 0:
                    print(f"  Migrated {imported}/{len(json_files)}...")
            except Exception as e:
                print(f"  Error migrating {json_file.name}: {e}")
                errors += 1

        with self._connect() as conn:
            conn.execute(
                "UPDATE processing_runs SET completed_at=datetime('now'), games_processed=?, errors=? WHERE id=?",
                (imported, errors, run_id)
            )
            conn.commit()

        print(f"Migration complete: {imported} imported, {errors} errors")
        return (imported, errors)

    def get_stats(self) -> Dict[str, int]:
        """Get database statistics."""
        with self._connect() as conn:
            stats = {}
            for table in ['games', 'batting_lines', 'pitching_lines', 'milestones', 'career_firsts']:
                row = conn.execute(f"SELECT COUNT(*) as cnt FROM {table}").fetchone()
                stats[table] = row['cnt']
            for gt in ['regular', 'spring', 'postseason']:
                row = conn.execute("SELECT COUNT(*) as cnt FROM games WHERE game_type = ?", (gt,)).fetchone()
                stats[f'games_{gt}'] = row['cnt']
            return stats
