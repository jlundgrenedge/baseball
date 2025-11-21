"""
Database schema for MLB teams and players.

Tables:
- teams: MLB team information
- pitchers: Pitcher statistics and attributes
- hitters: Hitter statistics and attributes
- team_rosters: Links players to teams
"""

import sqlite3
from typing import Optional
from pathlib import Path


class DatabaseSchema:
    """Manages database schema creation and migrations."""

    # Schema version for future migrations
    # v1: Initial schema with v1 attributes
    # v2: Added v2 offensive attributes (VISION, PUTAWAY_SKILL, NIBBLING_TENDENCY)
    #     and defensive attributes (REACTION_TIME, TOP_SPRINT_SPEED, ROUTE_EFFICIENCY, etc.)
    SCHEMA_VERSION = 2

    @staticmethod
    def create_tables(conn: sqlite3.Connection) -> None:
        """Create all database tables."""
        cursor = conn.cursor()

        # Teams table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS teams (
                team_id INTEGER PRIMARY KEY AUTOINCREMENT,
                team_name TEXT NOT NULL UNIQUE,
                team_abbr TEXT NOT NULL,
                season INTEGER NOT NULL,
                league TEXT,
                division TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # Pitchers table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS pitchers (
                pitcher_id INTEGER PRIMARY KEY AUTOINCREMENT,
                player_name TEXT NOT NULL,
                mlb_id INTEGER UNIQUE,

                -- Game attributes v1 (0-100,000 scale)
                velocity INTEGER NOT NULL,
                command INTEGER NOT NULL,
                stamina INTEGER NOT NULL,
                movement INTEGER,
                repertoire INTEGER,

                -- Game attributes v2 (Phase 2A/2B additions)
                putaway_skill INTEGER,        -- v2: Finishing ability (0-100k) from K/9
                nibbling_tendency REAL,       -- v2: Control strategy (0.0-1.0) from BB/9

                -- MLB statistics (source data)
                era REAL,
                whip REAL,
                strikeouts INTEGER,
                walks INTEGER,
                innings_pitched REAL,
                avg_fastball_velo REAL,
                k_per_9 REAL,
                bb_per_9 REAL,

                -- Metadata
                season INTEGER NOT NULL,
                games_pitched INTEGER,
                hand TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # Hitters table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS hitters (
                hitter_id INTEGER PRIMARY KEY AUTOINCREMENT,
                player_name TEXT NOT NULL,
                mlb_id INTEGER UNIQUE,

                -- Game attributes v1 (0-100,000 scale)
                contact INTEGER NOT NULL,
                power INTEGER NOT NULL,
                discipline INTEGER NOT NULL,
                speed INTEGER NOT NULL,

                -- Game attributes v2 offensive (Phase 2A addition)
                vision INTEGER,                    -- v2: Contact frequency (0-100k) from K%

                -- Game attributes v2 defensive (0-100,000 scale) - CRITICAL for BABIP tuning
                reaction_time INTEGER,             -- First movement delay from OAA/jump
                top_sprint_speed INTEGER,          -- Running speed from sprint speed
                route_efficiency INTEGER,          -- Path optimization from OAA/DRS
                arm_strength INTEGER,              -- Throw velocity from Statcast
                arm_accuracy INTEGER,              -- Throw precision from residual DRS
                fielding_secure INTEGER,           -- Catch success from fielding %

                -- Position and defensive role
                primary_position TEXT,             -- C, 1B, 2B, SS, 3B, LF, CF, RF

                -- MLB statistics (source data)
                batting_avg REAL,
                on_base_pct REAL,
                slugging_pct REAL,
                ops REAL,
                home_runs INTEGER,
                stolen_bases INTEGER,
                strikeouts INTEGER,
                walks INTEGER,
                avg_exit_velo REAL,
                max_exit_velo REAL,
                barrel_pct REAL,
                sprint_speed REAL,

                -- MLB defensive metrics (source data for attributes)
                oaa REAL,                          -- Outs Above Average (Statcast)
                drs REAL,                          -- Defensive Runs Saved (FanGraphs)
                arm_strength_mph REAL,             -- Throw velocity (Statcast)
                fielding_pct REAL,                 -- Traditional fielding percentage
                jump REAL,                         -- Outfielder first step (Statcast)

                -- Metadata
                season INTEGER NOT NULL,
                games_played INTEGER,
                at_bats INTEGER,
                position TEXT,                     -- Keep for backwards compatibility
                hand TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # Team rosters (links players to teams)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS team_rosters (
                roster_id INTEGER PRIMARY KEY AUTOINCREMENT,
                team_id INTEGER NOT NULL,
                pitcher_id INTEGER,
                hitter_id INTEGER,
                batting_order INTEGER,
                is_starter INTEGER DEFAULT 0,
                FOREIGN KEY (team_id) REFERENCES teams(team_id),
                FOREIGN KEY (pitcher_id) REFERENCES pitchers(pitcher_id),
                FOREIGN KEY (hitter_id) REFERENCES hitters(hitter_id),
                CHECK ((pitcher_id IS NOT NULL AND hitter_id IS NULL) OR
                       (pitcher_id IS NULL AND hitter_id IS NOT NULL))
            )
        """)

        # Create indices for performance
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_teams_name
            ON teams(team_name)
        """)

        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_teams_season
            ON teams(season)
        """)

        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_pitchers_mlb_id
            ON pitchers(mlb_id)
        """)

        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_hitters_mlb_id
            ON hitters(mlb_id)
        """)

        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_roster_team
            ON team_rosters(team_id)
        """)

        # Metadata table for schema version
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS metadata (
                key TEXT PRIMARY KEY,
                value TEXT NOT NULL
            )
        """)

        # Set schema version
        cursor.execute("""
            INSERT OR REPLACE INTO metadata (key, value)
            VALUES ('schema_version', ?)
        """, (str(DatabaseSchema.SCHEMA_VERSION),))

        conn.commit()

    @staticmethod
    def get_schema_version(conn: sqlite3.Connection) -> int:
        """Get current schema version."""
        cursor = conn.cursor()
        try:
            cursor.execute("SELECT value FROM metadata WHERE key = 'schema_version'")
            result = cursor.fetchone()
            return int(result[0]) if result else 0
        except sqlite3.OperationalError:
            return 0

    @staticmethod
    def initialize_database(db_path: Path) -> sqlite3.Connection:
        """Initialize database with schema."""
        conn = sqlite3.connect(str(db_path))
        conn.row_factory = sqlite3.Row  # Enable column access by name
        DatabaseSchema.create_tables(conn)
        return conn


if __name__ == "__main__":
    # Test schema creation
    test_db = Path("test_baseball.db")
    conn = DatabaseSchema.initialize_database(test_db)
    print(f"Database created at {test_db}")
    print(f"Schema version: {DatabaseSchema.get_schema_version(conn)}")
    conn.close()
