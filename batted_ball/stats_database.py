"""
Statistics Database Module

Provides SQLite-based persistence for player and team statistics across
season simulations. Supports accumulating stats across multiple simulation
runs and querying historical data.

Database Schema:
- seasons: Season metadata and simulation parameters
- games: Individual game records
- player_batting_games: Per-game batting statistics
- player_pitching_games: Per-game pitching statistics
- team_game_stats: Per-game team totals
- season_batting: Accumulated batting totals per player per season
- season_pitching: Accumulated pitching totals per player per season
- season_team_stats: Accumulated team totals per season
"""

import sqlite3
from dataclasses import dataclass
from datetime import date, datetime
from pathlib import Path
from typing import List, Dict, Optional, Tuple, Any
import json

from .scorekeeper import (
    GameLog, PlayerGameBatting, PlayerGamePitching,
    PlayNotation, InningLog
)


# Default database path
DEFAULT_DB_PATH = Path(__file__).parent.parent / "saved_stats" / "season_stats.db"


@dataclass
class SeasonRecord:
    """Metadata for a simulation season."""
    season_id: int
    year: int
    start_date: date
    description: str
    total_games: int
    is_complete: bool


class StatsDatabase:
    """
    SQLite database for persisting simulation statistics.
    
    Provides methods for:
    - Recording game results and player stats
    - Querying accumulated season statistics
    - Generating leaderboards and reports
    
    Usage:
        db = StatsDatabase()
        
        # Start a new season simulation
        season_id = db.start_season(2025, "Regular season simulation")
        
        # After each game
        db.record_game(season_id, game_log)
        
        # Query stats
        leaders = db.get_batting_leaders(season_id, "home_runs", limit=10)
    """
    
    def __init__(self, db_path: Path = None):
        """
        Initialize the stats database.
        
        Parameters
        ----------
        db_path : Path, optional
            Path to SQLite database file. Defaults to saved_stats/season_stats.db
        """
        self.db_path = db_path or DEFAULT_DB_PATH
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        
        self._conn: Optional[sqlite3.Connection] = None
        self._init_database()
    
    def _get_connection(self) -> sqlite3.Connection:
        """Get or create database connection."""
        if self._conn is None:
            self._conn = sqlite3.connect(self.db_path)
            self._conn.row_factory = sqlite3.Row
        return self._conn
    
    def _init_database(self):
        """Initialize database schema if needed."""
        conn = self._get_connection()
        cursor = conn.cursor()
        
        # Create seasons table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS seasons (
                season_id INTEGER PRIMARY KEY AUTOINCREMENT,
                year INTEGER NOT NULL,
                start_date TEXT NOT NULL,
                end_date TEXT,
                description TEXT,
                total_games INTEGER DEFAULT 0,
                is_complete INTEGER DEFAULT 0,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Create games table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS games (
                game_id INTEGER PRIMARY KEY AUTOINCREMENT,
                season_id INTEGER NOT NULL,
                game_date TEXT NOT NULL,
                away_team TEXT NOT NULL,
                home_team TEXT NOT NULL,
                away_score INTEGER NOT NULL,
                home_score INTEGER NOT NULL,
                innings INTEGER NOT NULL,
                away_hits INTEGER NOT NULL,
                home_hits INTEGER NOT NULL,
                away_errors INTEGER NOT NULL,
                home_errors INTEGER NOT NULL,
                line_score_away TEXT,
                line_score_home TEXT,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (season_id) REFERENCES seasons(season_id)
            )
        """)
        
        # Create player batting games table (box score lines)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS player_batting_games (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                game_id INTEGER NOT NULL,
                season_id INTEGER NOT NULL,
                player_id TEXT NOT NULL,
                player_name TEXT NOT NULL,
                team TEXT NOT NULL,
                position TEXT,
                batting_order INTEGER,
                
                -- Counting stats
                plate_appearances INTEGER DEFAULT 0,
                at_bats INTEGER DEFAULT 0,
                runs INTEGER DEFAULT 0,
                hits INTEGER DEFAULT 0,
                doubles INTEGER DEFAULT 0,
                triples INTEGER DEFAULT 0,
                home_runs INTEGER DEFAULT 0,
                rbi INTEGER DEFAULT 0,
                walks INTEGER DEFAULT 0,
                strikeouts INTEGER DEFAULT 0,
                hit_by_pitch INTEGER DEFAULT 0,
                sacrifice_flies INTEGER DEFAULT 0,
                sacrifice_bunts INTEGER DEFAULT 0,
                stolen_bases INTEGER DEFAULT 0,
                caught_stealing INTEGER DEFAULT 0,
                gidp INTEGER DEFAULT 0,
                
                -- Physics data (JSON array of values)
                exit_velocities TEXT,
                launch_angles TEXT,
                
                FOREIGN KEY (game_id) REFERENCES games(game_id),
                FOREIGN KEY (season_id) REFERENCES seasons(season_id)
            )
        """)
        
        # Create player pitching games table (box score lines)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS player_pitching_games (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                game_id INTEGER NOT NULL,
                season_id INTEGER NOT NULL,
                player_id TEXT NOT NULL,
                player_name TEXT NOT NULL,
                team TEXT NOT NULL,
                
                -- Counting stats (outs_recorded for precision)
                outs_recorded INTEGER DEFAULT 0,
                hits_allowed INTEGER DEFAULT 0,
                runs_allowed INTEGER DEFAULT 0,
                earned_runs INTEGER DEFAULT 0,
                walks INTEGER DEFAULT 0,
                strikeouts INTEGER DEFAULT 0,
                home_runs_allowed INTEGER DEFAULT 0,
                hit_batters INTEGER DEFAULT 0,
                batters_faced INTEGER DEFAULT 0,
                pitches INTEGER DEFAULT 0,
                
                -- Batted ball types
                ground_balls INTEGER DEFAULT 0,
                fly_balls INTEGER DEFAULT 0,
                line_drives INTEGER DEFAULT 0,
                
                -- Decision
                win INTEGER DEFAULT 0,
                loss INTEGER DEFAULT 0,
                save INTEGER DEFAULT 0,
                hold INTEGER DEFAULT 0,
                blown_save INTEGER DEFAULT 0,
                
                FOREIGN KEY (game_id) REFERENCES games(game_id),
                FOREIGN KEY (season_id) REFERENCES seasons(season_id)
            )
        """)
        
        # Create team game stats table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS team_game_stats (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                game_id INTEGER NOT NULL,
                season_id INTEGER NOT NULL,
                team TEXT NOT NULL,
                is_home INTEGER NOT NULL,
                
                -- Results
                runs INTEGER DEFAULT 0,
                hits INTEGER DEFAULT 0,
                errors INTEGER DEFAULT 0,
                left_on_base INTEGER DEFAULT 0,
                
                -- Batting
                at_bats INTEGER DEFAULT 0,
                doubles INTEGER DEFAULT 0,
                triples INTEGER DEFAULT 0,
                home_runs INTEGER DEFAULT 0,
                walks INTEGER DEFAULT 0,
                strikeouts INTEGER DEFAULT 0,
                stolen_bases INTEGER DEFAULT 0,
                
                -- Pitching
                innings_pitched_outs INTEGER DEFAULT 0,
                earned_runs_allowed INTEGER DEFAULT 0,
                
                FOREIGN KEY (game_id) REFERENCES games(game_id),
                FOREIGN KEY (season_id) REFERENCES seasons(season_id)
            )
        """)
        
        # Create accumulated season batting stats (materialized for performance)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS season_batting (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                season_id INTEGER NOT NULL,
                player_id TEXT NOT NULL,
                player_name TEXT NOT NULL,
                team TEXT NOT NULL,
                
                -- Accumulated counting stats
                games INTEGER DEFAULT 0,
                plate_appearances INTEGER DEFAULT 0,
                at_bats INTEGER DEFAULT 0,
                runs INTEGER DEFAULT 0,
                hits INTEGER DEFAULT 0,
                doubles INTEGER DEFAULT 0,
                triples INTEGER DEFAULT 0,
                home_runs INTEGER DEFAULT 0,
                rbi INTEGER DEFAULT 0,
                walks INTEGER DEFAULT 0,
                strikeouts INTEGER DEFAULT 0,
                hit_by_pitch INTEGER DEFAULT 0,
                sacrifice_flies INTEGER DEFAULT 0,
                sacrifice_bunts INTEGER DEFAULT 0,
                stolen_bases INTEGER DEFAULT 0,
                caught_stealing INTEGER DEFAULT 0,
                gidp INTEGER DEFAULT 0,
                
                -- Physics aggregates
                total_exit_velocity REAL DEFAULT 0,
                total_launch_angle REAL DEFAULT 0,
                batted_balls INTEGER DEFAULT 0,
                hard_hit_count INTEGER DEFAULT 0,
                
                UNIQUE(season_id, player_id),
                FOREIGN KEY (season_id) REFERENCES seasons(season_id)
            )
        """)
        
        # Create accumulated season pitching stats
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS season_pitching (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                season_id INTEGER NOT NULL,
                player_id TEXT NOT NULL,
                player_name TEXT NOT NULL,
                team TEXT NOT NULL,
                
                -- Accumulated counting stats
                games INTEGER DEFAULT 0,
                games_started INTEGER DEFAULT 0,
                outs_recorded INTEGER DEFAULT 0,
                hits_allowed INTEGER DEFAULT 0,
                runs_allowed INTEGER DEFAULT 0,
                earned_runs INTEGER DEFAULT 0,
                walks INTEGER DEFAULT 0,
                strikeouts INTEGER DEFAULT 0,
                home_runs_allowed INTEGER DEFAULT 0,
                hit_batters INTEGER DEFAULT 0,
                batters_faced INTEGER DEFAULT 0,
                pitches INTEGER DEFAULT 0,
                
                -- Batted ball aggregates
                ground_balls INTEGER DEFAULT 0,
                fly_balls INTEGER DEFAULT 0,
                line_drives INTEGER DEFAULT 0,
                
                -- Wins/Losses
                wins INTEGER DEFAULT 0,
                losses INTEGER DEFAULT 0,
                saves INTEGER DEFAULT 0,
                holds INTEGER DEFAULT 0,
                blown_saves INTEGER DEFAULT 0,
                
                UNIQUE(season_id, player_id),
                FOREIGN KEY (season_id) REFERENCES seasons(season_id)
            )
        """)
        
        # Create team standings table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS team_standings (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                season_id INTEGER NOT NULL,
                team TEXT NOT NULL,
                
                wins INTEGER DEFAULT 0,
                losses INTEGER DEFAULT 0,
                runs_scored INTEGER DEFAULT 0,
                runs_allowed INTEGER DEFAULT 0,
                
                UNIQUE(season_id, team),
                FOREIGN KEY (season_id) REFERENCES seasons(season_id)
            )
        """)
        
        # Create indexes for common queries
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_batting_games_season ON player_batting_games(season_id)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_batting_games_player ON player_batting_games(player_id)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_pitching_games_season ON player_pitching_games(season_id)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_pitching_games_player ON player_pitching_games(player_id)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_games_season ON games(season_id)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_season_batting_season ON season_batting(season_id)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_season_pitching_season ON season_pitching(season_id)")
        
        conn.commit()

    def list_seasons(self, year: int = None) -> List[Dict]:
        """
        List all seasons in the database.
        
        Parameters
        ----------
        year : int, optional
            Filter by year
        
        Returns
        -------
        list of dict
            Season records with id, year, games, description, etc.
        """
        conn = self._get_connection()
        cursor = conn.cursor()
        
        if year:
            cursor.execute("""
                SELECT season_id, year, start_date, end_date, description,
                       total_games, is_complete, created_at
                FROM seasons
                WHERE year = ?
                ORDER BY created_at DESC
            """, (year,))
        else:
            cursor.execute("""
                SELECT season_id, year, start_date, end_date, description,
                       total_games, is_complete, created_at
                FROM seasons
                ORDER BY year DESC, created_at DESC
            """)
        
        return [dict(row) for row in cursor.fetchall()]

    def get_season_info(self, season_id: int) -> Optional[Dict]:
        """
        Get info about a specific season.
        
        Parameters
        ----------
        season_id : int
            The season ID
        
        Returns
        -------
        dict or None
            Season info including game count
        """
        conn = self._get_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT s.season_id, s.year, s.start_date, s.end_date, 
                   s.description, s.is_complete, s.created_at,
                   COUNT(g.game_id) as games_played,
                   COALESCE(SUM(g.away_score + g.home_score), 0) as total_runs
            FROM seasons s
            LEFT JOIN games g ON s.season_id = g.season_id
            WHERE s.season_id = ?
            GROUP BY s.season_id
        """, (season_id,))
        
        row = cursor.fetchone()
        return dict(row) if row else None

    def get_last_simulated_date(self, season_id: int) -> Optional[date]:
        """
        Get the last date that was simulated for a season.
        
        Parameters
        ----------
        season_id : int
            The season to check
        
        Returns
        -------
        date or None
            The last game date, or None if no games
        """
        conn = self._get_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT MAX(game_date) as last_date
            FROM games
            WHERE season_id = ?
        """, (season_id,))
        
        row = cursor.fetchone()
        if row and row['last_date']:
            return date.fromisoformat(row['last_date'])
        return None

    def get_simulated_dates(self, season_id: int) -> set:
        """
        Get all dates that have been simulated for a season.
        
        Parameters
        ----------
        season_id : int
            The season to check
        
        Returns
        -------
        set
            Set of dates that have games recorded
        """
        conn = self._get_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT DISTINCT game_date
            FROM games
            WHERE season_id = ?
        """, (season_id,))
        
        return {date.fromisoformat(row['game_date']) for row in cursor.fetchall()}

    def get_simulated_matchups(self, season_id: int, game_date: date) -> set:
        """
        Get matchups already simulated for a specific date.
        
        Parameters
        ----------
        season_id : int
            The season to check
        game_date : date
            The date to check
        
        Returns
        -------
        set
            Set of (away_team, home_team) tuples already simulated
        """
        conn = self._get_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT away_team, home_team
            FROM games
            WHERE season_id = ? AND game_date = ?
        """, (season_id, game_date.isoformat()))
        
        return {(row['away_team'], row['home_team']) for row in cursor.fetchall()}

    def delete_season(self, season_id: int) -> bool:
        """
        Delete a season and all its data.
        
        Parameters
        ----------
        season_id : int
            The season to delete
        
        Returns
        -------
        bool
            True if deleted
        """
        conn = self._get_connection()
        cursor = conn.cursor()
        
        # Delete in order due to foreign keys
        cursor.execute("DELETE FROM season_pitching WHERE season_id = ?", (season_id,))
        cursor.execute("DELETE FROM season_batting WHERE season_id = ?", (season_id,))
        cursor.execute("DELETE FROM player_pitching_games WHERE season_id = ?", (season_id,))
        cursor.execute("DELETE FROM player_batting_games WHERE season_id = ?", (season_id,))
        cursor.execute("DELETE FROM games WHERE season_id = ?", (season_id,))
        cursor.execute("DELETE FROM seasons WHERE season_id = ?", (season_id,))
        
        conn.commit()
        return cursor.rowcount > 0

    def start_season(self, year: int, description: str = "") -> int:
        """
        Start a new season simulation.
        
        Parameters
        ----------
        year : int
            The season year (e.g., 2025)
        description : str
            Optional description of this simulation run
        
        Returns
        -------
        int
            The season_id for this simulation
        """
        conn = self._get_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            INSERT INTO seasons (year, start_date, description)
            VALUES (?, ?, ?)
        """, (year, date.today().isoformat(), description))
        
        conn.commit()
        return cursor.lastrowid
    
    def get_or_create_season(self, year: int, description: str = "") -> int:
        """
        Get existing season or create new one.
        
        This allows accumulating stats across multiple simulation runs
        for the same season year.
        
        Parameters
        ----------
        year : int
            The season year
        description : str
            Description (only used if creating new)
        
        Returns
        -------
        int
            The season_id
        """
        conn = self._get_connection()
        cursor = conn.cursor()
        
        # Look for existing incomplete season
        cursor.execute("""
            SELECT season_id FROM seasons
            WHERE year = ? AND is_complete = 0
            ORDER BY created_at DESC
            LIMIT 1
        """, (year,))
        
        row = cursor.fetchone()
        if row:
            return row['season_id']
        
        # Create new season
        return self.start_season(year, description)
    
    def record_game(self, season_id: int, game_log: GameLog) -> int:
        """
        Record a complete game to the database.
        
        Parameters
        ----------
        season_id : int
            The season this game belongs to
        game_log : GameLog
            Complete game data from Scorekeeper
        
        Returns
        -------
        int
            The game_id
        """
        conn = self._get_connection()
        cursor = conn.cursor()
        
        # Insert game record
        cursor.execute("""
            INSERT INTO games (
                season_id, game_date, away_team, home_team,
                away_score, home_score, innings,
                away_hits, home_hits, away_errors, home_errors,
                line_score_away, line_score_home
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            season_id,
            game_log.game_date.isoformat(),
            game_log.away_team,
            game_log.home_team,
            game_log.away_score,
            game_log.home_score,
            len(game_log.away_line),
            game_log.away_hits,
            game_log.home_hits,
            game_log.away_errors,
            game_log.home_errors,
            json.dumps(game_log.away_line),
            json.dumps(game_log.home_line),
        ))
        
        game_id = cursor.lastrowid
        
        # Insert batting stats
        for stats in game_log.away_batting + game_log.home_batting:
            self._insert_batting_game(cursor, game_id, season_id, stats)
            self._update_season_batting(cursor, season_id, stats)
        
        # Insert pitching stats
        for stats in game_log.away_pitching + game_log.home_pitching:
            self._insert_pitching_game(cursor, game_id, season_id, stats)
            self._update_season_pitching(cursor, season_id, stats)
        
        # Update team standings
        self._update_standings(cursor, season_id, game_log)
        
        # Update season game count
        cursor.execute("""
            UPDATE seasons SET total_games = total_games + 1
            WHERE season_id = ?
        """, (season_id,))
        
        conn.commit()
        return game_id
    
    def record_game_from_dicts(
        self,
        season_id: int,
        game_date: date,
        away_team: str,
        home_team: str,
        away_score: int,
        home_score: int,
        away_batting: List[Dict[str, Any]],
        home_batting: List[Dict[str, Any]],
        away_pitching: List[Dict[str, Any]],
        home_pitching: List[Dict[str, Any]],
    ) -> int:
        """
        Record a game from dict-based player stats (for parallel processing).
        
        Parameters
        ----------
        season_id : int
            The season this game belongs to
        game_date : date
            Date of the game
        away_team, home_team : str
            Team abbreviations
        away_score, home_score : int
            Final scores
        away_batting, home_batting : List[Dict]
            List of batting stat dicts
        away_pitching, home_pitching : List[Dict]
            List of pitching stat dicts
        
        Returns
        -------
        int
            The game_id
        """
        conn = self._get_connection()
        cursor = conn.cursor()
        
        # Calculate team totals
        away_hits = sum(b.get('hits', 0) for b in away_batting)
        home_hits = sum(b.get('hits', 0) for b in home_batting)
        
        # Insert game record
        cursor.execute("""
            INSERT INTO games (
                season_id, game_date, away_team, home_team,
                away_score, home_score, innings,
                away_hits, home_hits, away_errors, home_errors,
                line_score_away, line_score_home
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            season_id,
            game_date.isoformat(),
            away_team,
            home_team,
            away_score,
            home_score,
            9,  # Assume 9 innings
            away_hits,
            home_hits,
            0, 0,  # Errors not tracked in dicts
            '[]', '[]',  # No line score available
        ))
        
        game_id = cursor.lastrowid
        
        # Insert batting stats
        for stats in away_batting + home_batting:
            self._insert_batting_game_dict(cursor, game_id, season_id, stats)
            self._update_season_batting_dict(cursor, season_id, stats)
        
        # Insert pitching stats
        for stats in away_pitching + home_pitching:
            self._insert_pitching_game_dict(cursor, game_id, season_id, stats)
            self._update_season_pitching_dict(cursor, season_id, stats)
        
        # Update team standings
        away_win = 1 if away_score > home_score else 0
        home_win = 1 if home_score > away_score else 0
        
        cursor.execute("""
            INSERT INTO team_standings (season_id, team, wins, losses, runs_scored, runs_allowed)
            VALUES (?, ?, ?, ?, ?, ?)
            ON CONFLICT(season_id, team) DO UPDATE SET
                wins = wins + excluded.wins,
                losses = losses + excluded.losses,
                runs_scored = runs_scored + excluded.runs_scored,
                runs_allowed = runs_allowed + excluded.runs_allowed
        """, (season_id, away_team, away_win, home_win, away_score, home_score))
        
        cursor.execute("""
            INSERT INTO team_standings (season_id, team, wins, losses, runs_scored, runs_allowed)
            VALUES (?, ?, ?, ?, ?, ?)
            ON CONFLICT(season_id, team) DO UPDATE SET
                wins = wins + excluded.wins,
                losses = losses + excluded.losses,
                runs_scored = runs_scored + excluded.runs_scored,
                runs_allowed = runs_allowed + excluded.runs_allowed
        """, (season_id, home_team, home_win, away_win, home_score, away_score))
        
        # Update season game count
        cursor.execute("""
            UPDATE seasons SET total_games = total_games + 1
            WHERE season_id = ?
        """, (season_id,))
        
        conn.commit()
        return game_id
    
    def _insert_batting_game(self, cursor: sqlite3.Cursor, game_id: int,
                              season_id: int, stats: PlayerGameBatting):
        """Insert a player's batting line for a game."""
        cursor.execute("""
            INSERT INTO player_batting_games (
                game_id, season_id, player_id, player_name, team, position, batting_order,
                plate_appearances, at_bats, runs, hits, doubles, triples, home_runs,
                rbi, walks, strikeouts, hit_by_pitch, sacrifice_flies, sacrifice_bunts,
                stolen_bases, caught_stealing, gidp, exit_velocities, launch_angles
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            game_id, season_id, stats.player_id, stats.player_name, stats.team,
            stats.position, stats.batting_order,
            stats.plate_appearances, stats.at_bats, stats.runs, stats.hits,
            stats.doubles, stats.triples, stats.home_runs, stats.rbi,
            stats.walks, stats.strikeouts, stats.hit_by_pitch,
            stats.sacrifice_flies, stats.sacrifice_bunts,
            stats.stolen_bases, stats.caught_stealing, stats.gidp,
            json.dumps(stats.exit_velocities),
            json.dumps(stats.launch_angles),
        ))
    
    def _update_season_batting(self, cursor: sqlite3.Cursor, season_id: int,
                                stats: PlayerGameBatting):
        """Update accumulated season batting stats."""
        # Calculate physics aggregates
        total_ev = sum(stats.exit_velocities) if stats.exit_velocities else 0
        total_la = sum(stats.launch_angles) if stats.launch_angles else 0
        batted_balls = len(stats.exit_velocities)
        hard_hits = sum(1 for ev in stats.exit_velocities if ev >= 95.0)
        
        cursor.execute("""
            INSERT INTO season_batting (
                season_id, player_id, player_name, team,
                games, plate_appearances, at_bats, runs, hits,
                doubles, triples, home_runs, rbi, walks, strikeouts,
                hit_by_pitch, sacrifice_flies, sacrifice_bunts,
                stolen_bases, caught_stealing, gidp,
                total_exit_velocity, total_launch_angle, batted_balls, hard_hit_count
            ) VALUES (?, ?, ?, ?, 1, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(season_id, player_id) DO UPDATE SET
                games = games + 1,
                plate_appearances = plate_appearances + excluded.plate_appearances,
                at_bats = at_bats + excluded.at_bats,
                runs = runs + excluded.runs,
                hits = hits + excluded.hits,
                doubles = doubles + excluded.doubles,
                triples = triples + excluded.triples,
                home_runs = home_runs + excluded.home_runs,
                rbi = rbi + excluded.rbi,
                walks = walks + excluded.walks,
                strikeouts = strikeouts + excluded.strikeouts,
                hit_by_pitch = hit_by_pitch + excluded.hit_by_pitch,
                sacrifice_flies = sacrifice_flies + excluded.sacrifice_flies,
                sacrifice_bunts = sacrifice_bunts + excluded.sacrifice_bunts,
                stolen_bases = stolen_bases + excluded.stolen_bases,
                caught_stealing = caught_stealing + excluded.caught_stealing,
                gidp = gidp + excluded.gidp,
                total_exit_velocity = total_exit_velocity + excluded.total_exit_velocity,
                total_launch_angle = total_launch_angle + excluded.total_launch_angle,
                batted_balls = batted_balls + excluded.batted_balls,
                hard_hit_count = hard_hit_count + excluded.hard_hit_count
        """, (
            season_id, stats.player_id, stats.player_name, stats.team,
            stats.plate_appearances, stats.at_bats, stats.runs, stats.hits,
            stats.doubles, stats.triples, stats.home_runs, stats.rbi,
            stats.walks, stats.strikeouts, stats.hit_by_pitch,
            stats.sacrifice_flies, stats.sacrifice_bunts,
            stats.stolen_bases, stats.caught_stealing, stats.gidp,
            total_ev, total_la, batted_balls, hard_hits,
        ))
    
    def _insert_pitching_game(self, cursor: sqlite3.Cursor, game_id: int,
                               season_id: int, stats: PlayerGamePitching):
        """Insert a pitcher's game line."""
        cursor.execute("""
            INSERT INTO player_pitching_games (
                game_id, season_id, player_id, player_name, team,
                outs_recorded, hits_allowed, runs_allowed, earned_runs,
                walks, strikeouts, home_runs_allowed, hit_batters,
                pitches, ground_balls, fly_balls, line_drives,
                batters_faced, win, loss, save, hold, blown_save
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            game_id, season_id, stats.player_id, stats.player_name, stats.team,
            stats.outs_recorded, stats.hits_allowed, stats.runs_allowed, stats.earned_runs,
            stats.walks, stats.strikeouts, stats.home_runs_allowed, stats.hit_batters,
            stats.pitches, stats.ground_balls, stats.fly_balls, stats.line_drives,
            stats.batters_faced,
            1 if stats.win else 0,
            1 if stats.loss else 0,
            1 if stats.save else 0,
            1 if stats.hold else 0,
            1 if stats.blown_save else 0,
        ))
    
    def _update_season_pitching(self, cursor: sqlite3.Cursor, season_id: int,
                                 stats: PlayerGamePitching):
        """Update accumulated season pitching stats."""
        cursor.execute("""
            INSERT INTO season_pitching (
                season_id, player_id, player_name, team,
                games, outs_recorded, hits_allowed, runs_allowed, earned_runs,
                walks, strikeouts, home_runs_allowed, hit_batters, batters_faced,
                pitches, ground_balls, fly_balls, line_drives,
                wins, losses, saves, holds, blown_saves
            ) VALUES (?, ?, ?, ?, 1, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(season_id, player_id) DO UPDATE SET
                games = games + 1,
                outs_recorded = outs_recorded + excluded.outs_recorded,
                hits_allowed = hits_allowed + excluded.hits_allowed,
                runs_allowed = runs_allowed + excluded.runs_allowed,
                earned_runs = earned_runs + excluded.earned_runs,
                walks = walks + excluded.walks,
                strikeouts = strikeouts + excluded.strikeouts,
                home_runs_allowed = home_runs_allowed + excluded.home_runs_allowed,
                hit_batters = hit_batters + excluded.hit_batters,
                batters_faced = batters_faced + excluded.batters_faced,
                pitches = pitches + excluded.pitches,
                ground_balls = ground_balls + excluded.ground_balls,
                fly_balls = fly_balls + excluded.fly_balls,
                line_drives = line_drives + excluded.line_drives,
                wins = wins + excluded.wins,
                losses = losses + excluded.losses,
                saves = saves + excluded.saves,
                holds = holds + excluded.holds,
                blown_saves = blown_saves + excluded.blown_saves
        """, (
            season_id, stats.player_id, stats.player_name, stats.team,
            stats.outs_recorded, stats.hits_allowed, stats.runs_allowed, stats.earned_runs,
            stats.walks, stats.strikeouts, stats.home_runs_allowed, stats.hit_batters,
            stats.batters_faced, stats.pitches,
            stats.ground_balls, stats.fly_balls, stats.line_drives,
            1 if stats.win else 0,
            1 if stats.loss else 0,
            1 if stats.save else 0,
            1 if stats.hold else 0,
            1 if stats.blown_save else 0,
        ))
    
    def _insert_batting_game_dict(self, cursor: sqlite3.Cursor, game_id: int,
                                   season_id: int, stats: Dict[str, Any]):
        """Insert a player's batting line from a dict."""
        cursor.execute("""
            INSERT INTO player_batting_games (
                game_id, season_id, player_id, player_name, team, position, batting_order,
                plate_appearances, at_bats, runs, hits, doubles, triples, home_runs,
                rbi, walks, strikeouts, hit_by_pitch, sacrifice_flies, sacrifice_bunts,
                stolen_bases, caught_stealing, gidp, exit_velocities, launch_angles
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            game_id, season_id, 
            stats.get('player_id', ''),
            stats.get('player_name', ''),
            stats.get('team', ''),
            stats.get('position', ''),
            stats.get('batting_order', 0),
            stats.get('plate_appearances', 0),
            stats.get('at_bats', 0),
            stats.get('runs', 0),
            stats.get('hits', 0),
            stats.get('doubles', 0),
            stats.get('triples', 0),
            stats.get('home_runs', 0),
            stats.get('rbi', 0),
            stats.get('walks', 0),
            stats.get('strikeouts', 0),
            stats.get('hit_by_pitch', 0),
            stats.get('sacrifice_flies', 0),
            stats.get('sacrifice_bunts', 0),
            stats.get('stolen_bases', 0),
            stats.get('caught_stealing', 0),
            stats.get('gidp', 0),
            json.dumps(stats.get('exit_velocities', [])),
            json.dumps(stats.get('launch_angles', [])),
        ))
    
    def _update_season_batting_dict(self, cursor: sqlite3.Cursor, season_id: int,
                                     stats: Dict[str, Any]):
        """Update accumulated season batting stats from a dict."""
        exit_velocities = stats.get('exit_velocities', [])
        launch_angles = stats.get('launch_angles', [])
        
        total_ev = sum(exit_velocities) if exit_velocities else 0
        total_la = sum(launch_angles) if launch_angles else 0
        batted_balls = len(exit_velocities)
        hard_hits = sum(1 for ev in exit_velocities if ev >= 95.0)
        
        cursor.execute("""
            INSERT INTO season_batting (
                season_id, player_id, player_name, team,
                games, plate_appearances, at_bats, runs, hits,
                doubles, triples, home_runs, rbi, walks, strikeouts,
                hit_by_pitch, sacrifice_flies, sacrifice_bunts,
                stolen_bases, caught_stealing, gidp,
                total_exit_velocity, total_launch_angle, batted_balls, hard_hit_count
            ) VALUES (?, ?, ?, ?, 1, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(season_id, player_id) DO UPDATE SET
                games = games + 1,
                plate_appearances = plate_appearances + excluded.plate_appearances,
                at_bats = at_bats + excluded.at_bats,
                runs = runs + excluded.runs,
                hits = hits + excluded.hits,
                doubles = doubles + excluded.doubles,
                triples = triples + excluded.triples,
                home_runs = home_runs + excluded.home_runs,
                rbi = rbi + excluded.rbi,
                walks = walks + excluded.walks,
                strikeouts = strikeouts + excluded.strikeouts,
                hit_by_pitch = hit_by_pitch + excluded.hit_by_pitch,
                sacrifice_flies = sacrifice_flies + excluded.sacrifice_flies,
                sacrifice_bunts = sacrifice_bunts + excluded.sacrifice_bunts,
                stolen_bases = stolen_bases + excluded.stolen_bases,
                caught_stealing = caught_stealing + excluded.caught_stealing,
                gidp = gidp + excluded.gidp,
                total_exit_velocity = total_exit_velocity + excluded.total_exit_velocity,
                total_launch_angle = total_launch_angle + excluded.total_launch_angle,
                batted_balls = batted_balls + excluded.batted_balls,
                hard_hit_count = hard_hit_count + excluded.hard_hit_count
        """, (
            season_id,
            stats.get('player_id', ''),
            stats.get('player_name', ''),
            stats.get('team', ''),
            stats.get('plate_appearances', 0),
            stats.get('at_bats', 0),
            stats.get('runs', 0),
            stats.get('hits', 0),
            stats.get('doubles', 0),
            stats.get('triples', 0),
            stats.get('home_runs', 0),
            stats.get('rbi', 0),
            stats.get('walks', 0),
            stats.get('strikeouts', 0),
            stats.get('hit_by_pitch', 0),
            stats.get('sacrifice_flies', 0),
            stats.get('sacrifice_bunts', 0),
            stats.get('stolen_bases', 0),
            stats.get('caught_stealing', 0),
            stats.get('gidp', 0),
            total_ev,
            total_la,
            batted_balls,
            hard_hits,
        ))
    
    def _insert_pitching_game_dict(self, cursor: sqlite3.Cursor, game_id: int,
                                    season_id: int, stats: Dict[str, Any]):
        """Insert a pitcher's game line from a dict."""
        cursor.execute("""
            INSERT INTO player_pitching_games (
                game_id, season_id, player_id, player_name, team,
                outs_recorded, hits_allowed, runs_allowed, earned_runs,
                walks, strikeouts, home_runs_allowed, hit_batters,
                pitches, ground_balls, fly_balls, line_drives,
                batters_faced, win, loss, save, hold, blown_save
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            game_id, season_id,
            stats.get('player_id', ''),
            stats.get('player_name', ''),
            stats.get('team', ''),
            stats.get('outs_recorded', 0),
            stats.get('hits_allowed', 0),
            stats.get('runs_allowed', 0),
            stats.get('earned_runs', 0),
            stats.get('walks', 0),
            stats.get('strikeouts', 0),
            stats.get('home_runs_allowed', 0),
            stats.get('hit_batters', 0),
            stats.get('pitches', 0),
            stats.get('ground_balls', 0),
            stats.get('fly_balls', 0),
            stats.get('line_drives', 0),
            stats.get('batters_faced', 0),
            1 if stats.get('win') else 0,
            1 if stats.get('loss') else 0,
            1 if stats.get('save') else 0,
            1 if stats.get('hold') else 0,
            1 if stats.get('blown_save') else 0,
        ))
    
    def _update_season_pitching_dict(self, cursor: sqlite3.Cursor, season_id: int,
                                      stats: Dict[str, Any]):
        """Update accumulated season pitching stats from a dict."""
        cursor.execute("""
            INSERT INTO season_pitching (
                season_id, player_id, player_name, team,
                games, outs_recorded, hits_allowed, runs_allowed, earned_runs,
                walks, strikeouts, home_runs_allowed, hit_batters, batters_faced,
                pitches, ground_balls, fly_balls, line_drives,
                wins, losses, saves, holds, blown_saves
            ) VALUES (?, ?, ?, ?, 1, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(season_id, player_id) DO UPDATE SET
                games = games + 1,
                outs_recorded = outs_recorded + excluded.outs_recorded,
                hits_allowed = hits_allowed + excluded.hits_allowed,
                runs_allowed = runs_allowed + excluded.runs_allowed,
                earned_runs = earned_runs + excluded.earned_runs,
                walks = walks + excluded.walks,
                strikeouts = strikeouts + excluded.strikeouts,
                home_runs_allowed = home_runs_allowed + excluded.home_runs_allowed,
                hit_batters = hit_batters + excluded.hit_batters,
                batters_faced = batters_faced + excluded.batters_faced,
                pitches = pitches + excluded.pitches,
                ground_balls = ground_balls + excluded.ground_balls,
                fly_balls = fly_balls + excluded.fly_balls,
                line_drives = line_drives + excluded.line_drives,
                wins = wins + excluded.wins,
                losses = losses + excluded.losses,
                saves = saves + excluded.saves,
                holds = holds + excluded.holds,
                blown_saves = blown_saves + excluded.blown_saves
        """, (
            season_id,
            stats.get('player_id', ''),
            stats.get('player_name', ''),
            stats.get('team', ''),
            stats.get('outs_recorded', 0),
            stats.get('hits_allowed', 0),
            stats.get('runs_allowed', 0),
            stats.get('earned_runs', 0),
            stats.get('walks', 0),
            stats.get('strikeouts', 0),
            stats.get('home_runs_allowed', 0),
            stats.get('hit_batters', 0),
            stats.get('batters_faced', 0),
            stats.get('pitches', 0),
            stats.get('ground_balls', 0),
            stats.get('fly_balls', 0),
            stats.get('line_drives', 0),
            1 if stats.get('win') else 0,
            1 if stats.get('loss') else 0,
            1 if stats.get('save') else 0,
            1 if stats.get('hold') else 0,
            1 if stats.get('blown_save') else 0,
        ))
    
    def _insert_pitching_game(self, cursor: sqlite3.Cursor, game_id: int,
                               season_id: int, stats: PlayerGamePitching):
        """Insert a player's pitching line for a game."""
        cursor.execute("""
            INSERT INTO player_pitching_games (
                game_id, season_id, player_id, player_name, team,
                outs_recorded, hits_allowed, runs_allowed, earned_runs,
                walks, strikeouts, home_runs_allowed, hit_batters, batters_faced, pitches,
                ground_balls, fly_balls, line_drives,
                win, loss, save, hold, blown_save
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            game_id, season_id, stats.player_id, stats.player_name, stats.team,
            stats.outs_recorded, stats.hits_allowed, stats.runs_allowed, stats.earned_runs,
            stats.walks, stats.strikeouts, stats.home_runs_allowed, stats.hit_batters,
            stats.batters_faced, stats.pitches,
            stats.ground_balls, stats.fly_balls, stats.line_drives,
            1 if stats.win else 0,
            1 if stats.loss else 0,
            1 if stats.save else 0,
            1 if stats.hold else 0,
            1 if stats.blown_save else 0,
        ))
    
    def _update_season_pitching(self, cursor: sqlite3.Cursor, season_id: int,
                                 stats: PlayerGamePitching):
        """Update accumulated season pitching stats."""
        cursor.execute("""
            INSERT INTO season_pitching (
                season_id, player_id, player_name, team,
                games, outs_recorded, hits_allowed, runs_allowed, earned_runs,
                walks, strikeouts, home_runs_allowed, hit_batters, batters_faced, pitches,
                ground_balls, fly_balls, line_drives,
                wins, losses, saves, holds, blown_saves
            ) VALUES (?, ?, ?, ?, 1, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(season_id, player_id) DO UPDATE SET
                games = games + 1,
                outs_recorded = outs_recorded + excluded.outs_recorded,
                hits_allowed = hits_allowed + excluded.hits_allowed,
                runs_allowed = runs_allowed + excluded.runs_allowed,
                earned_runs = earned_runs + excluded.earned_runs,
                walks = walks + excluded.walks,
                strikeouts = strikeouts + excluded.strikeouts,
                home_runs_allowed = home_runs_allowed + excluded.home_runs_allowed,
                hit_batters = hit_batters + excluded.hit_batters,
                batters_faced = batters_faced + excluded.batters_faced,
                pitches = pitches + excluded.pitches,
                ground_balls = ground_balls + excluded.ground_balls,
                fly_balls = fly_balls + excluded.fly_balls,
                line_drives = line_drives + excluded.line_drives,
                wins = wins + excluded.wins,
                losses = losses + excluded.losses,
                saves = saves + excluded.saves,
                holds = holds + excluded.holds,
                blown_saves = blown_saves + excluded.blown_saves
        """, (
            season_id, stats.player_id, stats.player_name, stats.team,
            stats.outs_recorded, stats.hits_allowed, stats.runs_allowed, stats.earned_runs,
            stats.walks, stats.strikeouts, stats.home_runs_allowed, stats.hit_batters,
            stats.batters_faced, stats.pitches,
            stats.ground_balls, stats.fly_balls, stats.line_drives,
            1 if stats.win else 0,
            1 if stats.loss else 0,
            1 if stats.save else 0,
            1 if stats.hold else 0,
            1 if stats.blown_save else 0,
        ))
    
    def _update_standings(self, cursor: sqlite3.Cursor, season_id: int, game_log: GameLog):
        """Update team standings from game result."""
        # Determine winner
        away_win = 1 if game_log.away_score > game_log.home_score else 0
        home_win = 1 if game_log.home_score > game_log.away_score else 0
        
        # Update away team
        cursor.execute("""
            INSERT INTO team_standings (season_id, team, wins, losses, runs_scored, runs_allowed)
            VALUES (?, ?, ?, ?, ?, ?)
            ON CONFLICT(season_id, team) DO UPDATE SET
                wins = wins + excluded.wins,
                losses = losses + excluded.losses,
                runs_scored = runs_scored + excluded.runs_scored,
                runs_allowed = runs_allowed + excluded.runs_allowed
        """, (
            season_id, game_log.away_team,
            away_win, home_win,
            game_log.away_score, game_log.home_score,
        ))
        
        # Update home team
        cursor.execute("""
            INSERT INTO team_standings (season_id, team, wins, losses, runs_scored, runs_allowed)
            VALUES (?, ?, ?, ?, ?, ?)
            ON CONFLICT(season_id, team) DO UPDATE SET
                wins = wins + excluded.wins,
                losses = losses + excluded.losses,
                runs_scored = runs_scored + excluded.runs_scored,
                runs_allowed = runs_allowed + excluded.runs_allowed
        """, (
            season_id, game_log.home_team,
            home_win, away_win,
            game_log.home_score, game_log.away_score,
        ))
    
    def complete_season(self, season_id: int):
        """Mark a season as complete."""
        conn = self._get_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            UPDATE seasons SET is_complete = 1, end_date = ?
            WHERE season_id = ?
        """, (date.today().isoformat(), season_id))
        
        conn.commit()
    
    # ========== Query Methods ==========
    
    def get_batting_leaders(self, season_id: int, stat: str, limit: int = 10,
                            min_pa: int = 0) -> List[Dict]:
        """
        Get batting leaderboard for a statistic.
        
        Parameters
        ----------
        season_id : int
            Season to query
        stat : str
            Statistic name (e.g., 'home_runs', 'hits', 'batting_avg')
        limit : int
            Number of results to return
        min_pa : int
            Minimum plate appearances to qualify
        
        Returns
        -------
        List[Dict]
            List of player records with stats
        """
        conn = self._get_connection()
        cursor = conn.cursor()
        
        # Handle calculated stats
        if stat == 'batting_avg':
            order_expr = "CAST(hits AS REAL) / NULLIF(at_bats, 0)"
        elif stat == 'on_base_pct':
            order_expr = "CAST(hits + walks + hit_by_pitch AS REAL) / NULLIF(at_bats + walks + hit_by_pitch + sacrifice_flies, 0)"
        elif stat == 'slugging_pct':
            order_expr = """CAST(
                (hits - doubles - triples - home_runs) + 
                2 * doubles + 3 * triples + 4 * home_runs
            AS REAL) / NULLIF(at_bats, 0)"""
        elif stat == 'ops':
            order_expr = """(
                CAST(hits + walks + hit_by_pitch AS REAL) / NULLIF(at_bats + walks + hit_by_pitch + sacrifice_flies, 0) +
                CAST(
                    (hits - doubles - triples - home_runs) + 
                    2 * doubles + 3 * triples + 4 * home_runs
                AS REAL) / NULLIF(at_bats, 0)
            )"""
        elif stat == 'avg_exit_velocity':
            order_expr = "total_exit_velocity / NULLIF(batted_balls, 0)"
        elif stat == 'hard_hit_pct':
            order_expr = "CAST(hard_hit_count AS REAL) / NULLIF(batted_balls, 0) * 100"
        else:
            order_expr = stat
        
        cursor.execute(f"""
            SELECT 
                player_name, team, games, plate_appearances, at_bats,
                runs, hits, doubles, triples, home_runs, rbi,
                walks, strikeouts, stolen_bases,
                ROUND(CAST(hits AS REAL) / NULLIF(at_bats, 0), 3) as batting_avg,
                ROUND(CAST(hits + walks + hit_by_pitch AS REAL) / 
                      NULLIF(at_bats + walks + hit_by_pitch + sacrifice_flies, 0), 3) as on_base_pct,
                ROUND(CAST(
                    (hits - doubles - triples - home_runs) + 
                    2 * doubles + 3 * triples + 4 * home_runs
                AS REAL) / NULLIF(at_bats, 0), 3) as slugging_pct,
                ROUND(total_exit_velocity / NULLIF(batted_balls, 0), 1) as avg_exit_velocity,
                ROUND(CAST(hard_hit_count AS REAL) / NULLIF(batted_balls, 0) * 100, 1) as hard_hit_pct
            FROM season_batting
            WHERE season_id = ? AND plate_appearances >= ?
            ORDER BY {order_expr} DESC
            LIMIT ?
        """, (season_id, min_pa, limit))
        
        return [dict(row) for row in cursor.fetchall()]
    
    def get_pitching_leaders(self, season_id: int, stat: str, limit: int = 10,
                              min_ip: float = 0) -> List[Dict]:
        """
        Get pitching leaderboard for a statistic.
        
        Parameters
        ----------
        season_id : int
            Season to query
        stat : str
            Statistic name (e.g., 'wins', 'strikeouts', 'era')
        limit : int
            Number of results
        min_ip : float
            Minimum innings pitched to qualify
        
        Returns
        -------
        List[Dict]
            List of pitcher records with stats
        """
        conn = self._get_connection()
        cursor = conn.cursor()
        
        min_outs = int(min_ip * 3)
        
        # Handle calculated stats (lower is better for ERA, WHIP)
        ascending = stat in ['era', 'whip', 'bb_per_9']
        order_dir = "ASC" if ascending else "DESC"
        
        if stat == 'era':
            order_expr = "9.0 * earned_runs / NULLIF(CAST(outs_recorded AS REAL) / 3, 0)"
        elif stat == 'whip':
            order_expr = "(walks + hits_allowed) / NULLIF(CAST(outs_recorded AS REAL) / 3, 0)"
        elif stat == 'k_per_9':
            order_expr = "9.0 * strikeouts / NULLIF(CAST(outs_recorded AS REAL) / 3, 0)"
        elif stat == 'bb_per_9':
            order_expr = "9.0 * walks / NULLIF(CAST(outs_recorded AS REAL) / 3, 0)"
        elif stat == 'innings_pitched':
            order_expr = "outs_recorded"
        else:
            order_expr = stat
        
        cursor.execute(f"""
            SELECT 
                player_name, team, games, wins, losses, saves,
                outs_recorded,
                CAST(outs_recorded / 3 AS TEXT) || '.' || CAST(outs_recorded % 3 AS TEXT) as innings_pitched,
                hits_allowed, runs_allowed, earned_runs, walks, strikeouts, home_runs_allowed,
                ROUND(9.0 * earned_runs / NULLIF(CAST(outs_recorded AS REAL) / 3, 0), 2) as era,
                ROUND((walks + hits_allowed) / NULLIF(CAST(outs_recorded AS REAL) / 3, 0), 2) as whip,
                ROUND(9.0 * strikeouts / NULLIF(CAST(outs_recorded AS REAL) / 3, 0), 1) as k_per_9
            FROM season_pitching
            WHERE season_id = ? AND outs_recorded >= ?
            ORDER BY {order_expr} {order_dir}
            LIMIT ?
        """, (season_id, min_outs, limit))
        
        return [dict(row) for row in cursor.fetchall()]
    
    def get_team_standings(self, season_id: int) -> List[Dict]:
        """
        Get team standings for a season.
        
        Returns
        -------
        List[Dict]
            List of team records with wins, losses, run differential
        """
        conn = self._get_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT 
                team,
                wins,
                losses,
                ROUND(CAST(wins AS REAL) / NULLIF(wins + losses, 0), 3) as win_pct,
                runs_scored,
                runs_allowed,
                runs_scored - runs_allowed as run_diff
            FROM team_standings
            WHERE season_id = ?
            ORDER BY wins DESC, run_diff DESC
        """, (season_id,))
        
        return [dict(row) for row in cursor.fetchall()]
    
    def get_player_game_log(self, season_id: int, player_id: str,
                            is_batting: bool = True) -> List[Dict]:
        """
        Get game-by-game log for a player.
        
        Parameters
        ----------
        season_id : int
            Season to query
        player_id : str
            Player identifier
        is_batting : bool
            True for batting log, False for pitching log
        
        Returns
        -------
        List[Dict]
            List of game records
        """
        conn = self._get_connection()
        cursor = conn.cursor()
        
        if is_batting:
            cursor.execute("""
                SELECT 
                    g.game_date,
                    CASE WHEN pbg.team = g.away_team THEN '@' || g.home_team 
                         ELSE 'vs' || g.away_team END as opponent,
                    pbg.at_bats, pbg.runs, pbg.hits, pbg.doubles, pbg.triples,
                    pbg.home_runs, pbg.rbi, pbg.walks, pbg.strikeouts
                FROM player_batting_games pbg
                JOIN games g ON pbg.game_id = g.game_id
                WHERE pbg.season_id = ? AND pbg.player_id = ?
                ORDER BY g.game_date
            """, (season_id, player_id))
        else:
            cursor.execute("""
                SELECT 
                    g.game_date,
                    CASE WHEN ppg.team = g.away_team THEN '@' || g.home_team 
                         ELSE 'vs' || g.away_team END as opponent,
                    ppg.outs_recorded,
                    ppg.hits_allowed, ppg.runs_allowed, ppg.earned_runs,
                    ppg.walks, ppg.strikeouts, ppg.home_runs_allowed,
                    ppg.win, ppg.loss, ppg.save
                FROM player_pitching_games ppg
                JOIN games g ON ppg.game_id = g.game_id
                WHERE ppg.season_id = ? AND ppg.player_id = ?
                ORDER BY g.game_date
            """, (season_id, player_id))
        
        return [dict(row) for row in cursor.fetchall()]
    
    def get_season_summary(self, season_id: int) -> Dict:
        """
        Get summary statistics for a season.
        
        Returns
        -------
        Dict
            Summary with game count, total runs, leader highlights, etc.
        """
        conn = self._get_connection()
        cursor = conn.cursor()
        
        # Basic season info
        cursor.execute("""
            SELECT year, total_games, is_complete, start_date, end_date
            FROM seasons WHERE season_id = ?
        """, (season_id,))
        season = dict(cursor.fetchone())
        
        # Total runs
        cursor.execute("""
            SELECT 
                SUM(away_score + home_score) as total_runs,
                AVG(away_score + home_score) as avg_runs_per_game,
                SUM(away_hits + home_hits) as total_hits
            FROM games WHERE season_id = ?
        """, (season_id,))
        game_totals = dict(cursor.fetchone())
        
        # HR leader
        hr_leader = self.get_batting_leaders(season_id, 'home_runs', limit=1)
        
        # ERA leader
        era_leader = self.get_pitching_leaders(season_id, 'era', limit=1, min_ip=10)
        
        return {
            **season,
            **game_totals,
            'hr_leader': hr_leader[0] if hr_leader else None,
            'era_leader': era_leader[0] if era_leader else None,
        }
    
    def export_batting_to_csv(self, season_id: int, filepath: str, min_pa: int = 1) -> int:
        """
        Export batting statistics to CSV file.
        
        Parameters
        ----------
        season_id : int
            Season to export
        filepath : str
            Output file path
        min_pa : int
            Minimum plate appearances to include
        
        Returns
        -------
        int
            Number of rows exported
        """
        import csv
        
        conn = self._get_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT 
                player_name, team, games, plate_appearances, at_bats,
                runs, hits, doubles, triples, home_runs, rbi,
                walks, strikeouts, hit_by_pitch, sacrifice_flies, sacrifice_bunts,
                stolen_bases, caught_stealing, gidp,
                CASE WHEN at_bats > 0 THEN ROUND(CAST(hits AS FLOAT) / at_bats, 3) ELSE 0 END as batting_avg,
                CASE WHEN (at_bats + walks + hit_by_pitch + sacrifice_flies) > 0 
                    THEN ROUND(CAST(hits + walks + hit_by_pitch AS FLOAT) / (at_bats + walks + hit_by_pitch + sacrifice_flies), 3) 
                    ELSE 0 END as obp,
                CASE WHEN at_bats > 0 
                    THEN ROUND(CAST((hits - doubles - triples - home_runs) + 2*doubles + 3*triples + 4*home_runs AS FLOAT) / at_bats, 3)
                    ELSE 0 END as slg,
                CASE WHEN batted_balls > 0 THEN ROUND(total_exit_velocity / batted_balls, 1) ELSE 0 END as avg_exit_velo,
                CASE WHEN batted_balls > 0 THEN ROUND(100.0 * hard_hit_count / batted_balls, 1) ELSE 0 END as hard_hit_pct
            FROM season_batting
            WHERE season_id = ? AND plate_appearances >= ?
            ORDER BY hits DESC
        """, (season_id, min_pa))
        
        rows = cursor.fetchall()
        
        with open(filepath, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            # Header
            writer.writerow([
                'Player', 'Team', 'G', 'PA', 'AB', 'R', 'H', '2B', '3B', 'HR', 'RBI',
                'BB', 'SO', 'HBP', 'SF', 'SH', 'SB', 'CS', 'GIDP', 'AVG', 'OBP', 'SLG',
                'AvgEV', 'HardHit%'
            ])
            for row in rows:
                writer.writerow(row)
        
        return len(rows)
    
    def export_pitching_to_csv(self, season_id: int, filepath: str, min_ip: float = 0) -> int:
        """
        Export pitching statistics to CSV file.
        
        Parameters
        ----------
        season_id : int
            Season to export
        filepath : str
            Output file path
        min_ip : float
            Minimum innings pitched to include
        
        Returns
        -------
        int
            Number of rows exported
        """
        import csv
        
        conn = self._get_connection()
        cursor = conn.cursor()
        
        min_outs = int(min_ip * 3)
        
        cursor.execute("""
            SELECT 
                player_name, team, games, 
                outs_recorded / 3 || '.' || outs_recorded % 3 as ip,
                hits_allowed, runs_allowed, earned_runs, walks, strikeouts,
                home_runs_allowed, hit_batters, batters_faced,
                wins, losses, saves, holds, blown_saves,
                CASE WHEN outs_recorded > 0 
                    THEN ROUND(9.0 * earned_runs / (outs_recorded / 3.0), 2) 
                    ELSE 0 END as era,
                CASE WHEN outs_recorded > 0 
                    THEN ROUND((walks + hits_allowed) / (outs_recorded / 3.0), 2) 
                    ELSE 0 END as whip,
                CASE WHEN outs_recorded > 0 
                    THEN ROUND(9.0 * strikeouts / (outs_recorded / 3.0), 1) 
                    ELSE 0 END as k_per_9,
                CASE WHEN outs_recorded > 0 
                    THEN ROUND(9.0 * walks / (outs_recorded / 3.0), 1) 
                    ELSE 0 END as bb_per_9
            FROM season_pitching
            WHERE season_id = ? AND outs_recorded >= ?
            ORDER BY wins DESC, era ASC
        """, (season_id, min_outs))
        
        rows = cursor.fetchall()
        
        with open(filepath, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            # Header
            writer.writerow([
                'Player', 'Team', 'G', 'IP', 'H', 'R', 'ER', 'BB', 'SO',
                'HR', 'HBP', 'BF', 'W', 'L', 'SV', 'HLD', 'BS',
                'ERA', 'WHIP', 'K/9', 'BB/9'
            ])
            for row in rows:
                writer.writerow(row)
        
        return len(rows)
    
    def export_to_html(self, season_id: int, filepath: str, min_pa: int = 10, min_ip: float = 5.0) -> None:
        """
        Export season statistics to an HTML report.
        
        Parameters
        ----------
        season_id : int
            Season to export
        filepath : str
            Output HTML file path
        min_pa : int
            Minimum plate appearances for batting
        min_ip : float
            Minimum innings pitched for pitching
        """
        # Get season info
        info = self.get_season_info(season_id)
        summary = self.get_season_summary(season_id)
        
        # Get leaders
        batting_leaders = self.get_batting_leaders(season_id, 'hits', limit=50, min_pa=min_pa)
        pitching_leaders = self.get_pitching_leaders(season_id, 'wins', limit=50, min_ip=min_ip)
        hr_leaders = self.get_batting_leaders(season_id, 'home_runs', limit=10, min_pa=1)
        era_leaders = self.get_pitching_leaders(season_id, 'era', limit=10, min_ip=min_ip)
        
        html = f"""<!DOCTYPE html>
<html>
<head>
    <title>{info['year']} Season Statistics</title>
    <style>
        body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; margin: 20px; background: #f5f5f5; }}
        .container {{ max-width: 1200px; margin: 0 auto; }}
        h1 {{ color: #1a365d; border-bottom: 3px solid #c53030; padding-bottom: 10px; }}
        h2 {{ color: #2d3748; margin-top: 30px; }}
        .summary {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(150px, 1fr)); gap: 15px; margin: 20px 0; }}
        .stat-box {{ background: white; padding: 15px; border-radius: 8px; box-shadow: 0 1px 3px rgba(0,0,0,0.1); text-align: center; }}
        .stat-box .value {{ font-size: 24px; font-weight: bold; color: #c53030; }}
        .stat-box .label {{ font-size: 12px; color: #718096; text-transform: uppercase; }}
        table {{ width: 100%; border-collapse: collapse; background: white; box-shadow: 0 1px 3px rgba(0,0,0,0.1); border-radius: 8px; overflow: hidden; margin-bottom: 30px; }}
        th {{ background: #1a365d; color: white; padding: 12px 8px; text-align: left; font-size: 12px; }}
        td {{ padding: 10px 8px; border-bottom: 1px solid #e2e8f0; font-size: 13px; }}
        tr:hover {{ background: #f7fafc; }}
        tr:nth-child(even) {{ background: #f8f9fa; }}
        .number {{ text-align: right; font-family: 'Consolas', monospace; }}
        .leader-card {{ background: linear-gradient(135deg, #1a365d 0%, #2d3748 100%); color: white; padding: 20px; border-radius: 8px; margin: 10px 0; }}
        .leader-card h3 {{ margin: 0 0 10px 0; font-size: 14px; opacity: 0.8; }}
        .leader-card .name {{ font-size: 20px; font-weight: bold; }}
        .leader-card .stat {{ font-size: 32px; font-weight: bold; color: #f6e05e; }}
        .leaders-grid {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 15px; }}
        footer {{ text-align: center; margin-top: 40px; color: #718096; font-size: 12px; }}
    </style>
</head>
<body>
    <div class="container">
        <h1>⚾ {info['year']} Season Statistics</h1>
        <p><em>{info['description'] or 'Simulation Results'}</em></p>
        
        <div class="summary">
            <div class="stat-box">
                <div class="value">{info['games_played']}</div>
                <div class="label">Games Played</div>
            </div>
            <div class="stat-box">
                <div class="value">{summary['total_runs'] or 0:,}</div>
                <div class="label">Total Runs</div>
            </div>
            <div class="stat-box">
                <div class="value">{summary['avg_runs_per_game'] or 0:.1f}</div>
                <div class="label">Runs/Game</div>
            </div>
            <div class="stat-box">
                <div class="value">{summary['total_hits'] or 0:,}</div>
                <div class="label">Total Hits</div>
            </div>
        </div>
        
        <h2>🏆 League Leaders</h2>
        <div class="leaders-grid">
"""
        
        if hr_leaders:
            hr = hr_leaders[0]
            html += f"""            <div class="leader-card">
                <h3>Home Run Leader</h3>
                <div class="name">{hr['player_name']}</div>
                <div class="stat">{hr['home_runs']} HR</div>
            </div>
"""
        
        if era_leaders:
            era = era_leaders[0]
            html += f"""            <div class="leader-card">
                <h3>ERA Leader</h3>
                <div class="name">{era['player_name']}</div>
                <div class="stat">{era['era']:.2f} ERA</div>
            </div>
"""
        
        # Hits leader
        if batting_leaders:
            hits = batting_leaders[0]
            html += f"""            <div class="leader-card">
                <h3>Hits Leader</h3>
                <div class="name">{hits['player_name']}</div>
                <div class="stat">{hits['hits']} H</div>
            </div>
"""
        
        # Wins leader
        if pitching_leaders:
            wins = pitching_leaders[0]
            html += f"""            <div class="leader-card">
                <h3>Wins Leader</h3>
                <div class="name">{wins['player_name']}</div>
                <div class="stat">{wins['wins']} W</div>
            </div>
"""
        
        html += """        </div>
        
        <h2>🏏 Batting Statistics</h2>
        <table>
            <tr>
                <th>Player</th><th>Team</th><th class="number">G</th><th class="number">PA</th>
                <th class="number">AB</th><th class="number">H</th><th class="number">2B</th>
                <th class="number">3B</th><th class="number">HR</th><th class="number">RBI</th>
                <th class="number">R</th><th class="number">BB</th><th class="number">SO</th>
                <th class="number">AVG</th><th class="number">OBP</th><th class="number">SLG</th>
            </tr>
"""
        
        for b in batting_leaders:
            avg = b['hits'] / b['at_bats'] if b['at_bats'] > 0 else 0
            obp_num = b['hits'] + b['walks'] + b.get('hit_by_pitch', 0)
            obp_den = b['at_bats'] + b['walks'] + b.get('hit_by_pitch', 0) + b.get('sacrifice_flies', 0)
            obp = obp_num / obp_den if obp_den > 0 else 0
            singles = b['hits'] - b['doubles'] - b['triples'] - b['home_runs']
            tb = singles + 2*b['doubles'] + 3*b['triples'] + 4*b['home_runs']
            slg = tb / b['at_bats'] if b['at_bats'] > 0 else 0
            
            html += f"""            <tr>
                <td>{b['player_name']}</td><td>{b['team']}</td>
                <td class="number">{b['games']}</td><td class="number">{b['plate_appearances']}</td>
                <td class="number">{b['at_bats']}</td><td class="number">{b['hits']}</td>
                <td class="number">{b['doubles']}</td><td class="number">{b['triples']}</td>
                <td class="number">{b['home_runs']}</td><td class="number">{b['rbi']}</td>
                <td class="number">{b['runs']}</td><td class="number">{b['walks']}</td>
                <td class="number">{b['strikeouts']}</td>
                <td class="number">{avg:.3f}</td><td class="number">{obp:.3f}</td><td class="number">{slg:.3f}</td>
            </tr>
"""
        
        html += """        </table>
        
        <h2>⚾ Pitching Statistics</h2>
        <table>
            <tr>
                <th>Player</th><th>Team</th><th class="number">G</th><th class="number">IP</th>
                <th class="number">W</th><th class="number">L</th><th class="number">SV</th>
                <th class="number">H</th><th class="number">R</th><th class="number">ER</th>
                <th class="number">BB</th><th class="number">SO</th><th class="number">HR</th>
                <th class="number">ERA</th><th class="number">WHIP</th><th class="number">K/9</th>
            </tr>
"""
        
        for p in pitching_leaders:
            outs = p['outs_recorded']
            ip_full = outs // 3
            ip_partial = outs % 3
            ip_str = f"{ip_full}.{ip_partial}"
            ip_float = outs / 3.0
            era = 9.0 * p['earned_runs'] / ip_float if ip_float > 0 else 0
            whip = (p['walks'] + p['hits_allowed']) / ip_float if ip_float > 0 else 0
            k9 = 9.0 * p['strikeouts'] / ip_float if ip_float > 0 else 0
            
            html += f"""            <tr>
                <td>{p['player_name']}</td><td>{p['team']}</td>
                <td class="number">{p['games']}</td><td class="number">{ip_str}</td>
                <td class="number">{p['wins']}</td><td class="number">{p['losses']}</td>
                <td class="number">{p['saves']}</td>
                <td class="number">{p['hits_allowed']}</td><td class="number">{p['runs_allowed']}</td>
                <td class="number">{p['earned_runs']}</td><td class="number">{p['walks']}</td>
                <td class="number">{p['strikeouts']}</td><td class="number">{p['home_runs_allowed']}</td>
                <td class="number">{era:.2f}</td><td class="number">{whip:.2f}</td><td class="number">{k9:.1f}</td>
            </tr>
"""
        
        html += f"""        </table>
        
        <footer>
            Generated by Baseball Physics Simulator | {info['year']} Season
        </footer>
    </div>
</body>
</html>
"""
        
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(html)
    
    def close(self):
        """Close database connection."""
        if self._conn:
            self._conn.close()
            self._conn = None
    
    def __enter__(self):
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()
