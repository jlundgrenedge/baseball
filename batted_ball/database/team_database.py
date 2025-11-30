"""
Database operations for storing and retrieving MLB teams and players.

Provides a high-level interface for:
- Storing teams fetched from pybaseball
- Converting stats to game attributes
- Loading teams for simulations
- Updating player statistics
"""

import sqlite3
from pathlib import Path
from typing import List, Dict, Optional, Tuple
import pandas as pd
import numpy as np

from .db_schema import DatabaseSchema
from .stats_converter import StatsConverter
from .pybaseball_fetcher import PybaseballFetcher


def clean_value(value):
    """Convert pandas NaN/None to Python None for database storage."""
    if pd.isna(value):
        return None
    if isinstance(value, (np.integer, np.floating)):
        if np.isnan(value):
            return None
        return int(value) if isinstance(value, np.integer) else float(value)
    return value


class TeamDatabase:
    """
    Main database interface for team and player management.

    Usage:
        db = TeamDatabase("baseball.db")
        db.fetch_and_store_team("NYY", season=2024)
        team = db.load_team_for_simulation("New York Yankees", season=2024)
    """

    def __init__(self, db_path: str = "baseball_teams.db"):
        """
        Initialize database connection.

        Parameters
        ----------
        db_path : str
            Path to SQLite database file
        """
        self.db_path = Path(db_path)
        self.conn = DatabaseSchema.initialize_database(self.db_path)
        self.converter = StatsConverter()

    def close(self):
        """Close database connection."""
        if self.conn:
            self.conn.close()

    def __enter__(self):
        """Context manager support."""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager cleanup."""
        self.close()

    def fetch_and_store_team(
        self,
        team_abbr: str,
        season: int = 2024,
        min_pitcher_innings: float = 20.0,
        min_hitter_at_bats: int = 50,
        overwrite: bool = False,
        export_csv: bool = True,
        csv_output_dir: str = "csv_exports"
    ) -> Tuple[int, int]:
        """
        Fetch team data from pybaseball and store in database.

        Parameters
        ----------
        team_abbr : str
            Team abbreviation (e.g., 'NYY')
        season : int
            Season year
        min_pitcher_innings : float
            Minimum innings for pitchers
        min_hitter_at_bats : int
            Minimum at-bats for hitters
        overwrite : bool
            If True, delete existing team data for this team/season
        export_csv : bool
            If True, automatically export database to CSV after storing (default: True)
        csv_output_dir : str
            Directory for CSV exports (default: 'csv_exports')

        Returns
        -------
        tuple of (num_pitchers, num_hitters)
            Number of players stored
        """
        print(f"\n{'='*60}")
        print(f"Fetching and storing {team_abbr} ({season})")
        print(f"{'='*60}")

        # Fetch data
        fetcher = PybaseballFetcher(season=season)
        team_name = fetcher.get_team_name(team_abbr)
        pitchers_df, hitters_df = fetcher.get_team_roster(
            team_abbr,
            min_pitcher_innings=min_pitcher_innings,
            min_hitter_at_bats=min_hitter_at_bats
        )

        if len(pitchers_df) == 0 and len(hitters_df) == 0:
            print(f"Warning: No data found for {team_abbr} ({season})")
            return 0, 0

        # Check if team exists
        cursor = self.conn.cursor()
        cursor.execute(
            "SELECT team_id FROM teams WHERE team_name = ? AND season = ?",
            (team_name, season)
        )
        existing_team = cursor.fetchone()

        if existing_team and overwrite:
            print(f"  Deleting existing data for {team_name} ({season})...")
            team_id = existing_team[0]
            cursor.execute("DELETE FROM team_rosters WHERE team_id = ?", (team_id,))
            cursor.execute("DELETE FROM teams WHERE team_id = ?", (team_id,))
            self.conn.commit()
            existing_team = None

        # Create or get team
        if existing_team:
            team_id = existing_team[0]
            print(f"  Using existing team (ID: {team_id})")
        else:
            cursor.execute("""
                INSERT INTO teams (team_name, team_abbr, season, league, division)
                VALUES (?, ?, ?, ?, ?)
            """, (team_name, team_abbr, season, None, None))
            team_id = cursor.lastrowid
            print(f"  Created new team (ID: {team_id})")

        # Store pitchers
        num_pitchers = 0
        print(f"\n  Storing {len(pitchers_df)} pitchers...")
        for _, row in pitchers_df.iterrows():
            pitcher_id = self._store_pitcher(row, season)
            if pitcher_id:
                # Link to team
                cursor.execute("""
                    INSERT INTO team_rosters (team_id, pitcher_id, is_starter)
                    VALUES (?, ?, ?)
                """, (team_id, pitcher_id, int(row.get('games_started', 0) > 0)))
                num_pitchers += 1

        # Store hitters
        num_hitters = 0
        print(f"  Storing {len(hitters_df)} hitters...")
        for idx, row in hitters_df.iterrows():
            hitter_id = self._store_hitter(row, season)
            if hitter_id:
                # Link to team (batting order = order in dataframe)
                cursor.execute("""
                    INSERT INTO team_rosters (team_id, hitter_id, batting_order)
                    VALUES (?, ?, ?)
                """, (team_id, hitter_id, idx + 1))
                num_hitters += 1

        self.conn.commit()

        print(f"\n  ✓ Stored {num_pitchers} pitchers and {num_hitters} hitters")
        print(f"{'='*60}\n")

        # Auto-export to CSV if requested
        if export_csv and (num_pitchers > 0 or num_hitters > 0):
            try:
                from .csv_exporter import CSVExporter
                exporter = CSVExporter(str(self.db_path))
                exporter.export_all(csv_output_dir, verbose=True)
            except Exception as e:
                print(f"  Warning: CSV export failed: {e}")

        return num_pitchers, num_hitters

    def _store_pitcher(self, stats: pd.Series, season: int) -> Optional[int]:
        """Store a pitcher in the database (v2: includes PUTAWAY_SKILL, NIBBLING_TENDENCY)."""
        # Convert stats to attributes using v2 method
        attrs = self.converter.mlb_stats_to_pitcher_attributes_v2(
            era=clean_value(stats.get('era')),
            whip=clean_value(stats.get('whip')),
            k_per_9=clean_value(stats.get('k_per_9')),
            bb_per_9=clean_value(stats.get('bb_per_9')),
            avg_fastball_velo=clean_value(stats.get('avg_fastball_velo')),
            innings_pitched=clean_value(stats.get('innings_pitched')),
            games_pitched=clean_value(stats.get('games_pitched')),
        )

        cursor = self.conn.cursor()

        # Check if pitcher exists
        cursor.execute(
            "SELECT pitcher_id FROM pitchers WHERE player_name = ? AND season = ?",
            (stats.get('player_name'), season)
        )
        existing = cursor.fetchone()

        if existing:
            # Update existing
            pitcher_id = existing[0]
            cursor.execute("""
                UPDATE pitchers SET
                    velocity = ?, command = ?, stamina = ?, movement = ?, repertoire = ?,
                    putaway_skill = ?, nibbling_tendency = ?,
                    era = ?, whip = ?, strikeouts = ?, walks = ?,
                    innings_pitched = ?, avg_fastball_velo = ?, k_per_9 = ?, bb_per_9 = ?,
                    games_pitched = ?, updated_at = CURRENT_TIMESTAMP
                WHERE pitcher_id = ?
            """, (
                attrs['velocity'], attrs['command'], attrs['stamina'],
                attrs['movement'], attrs['repertoire'],
                attrs.get('putaway_skill'), attrs.get('nibbling_tendency'),  # v2 attributes
                clean_value(stats.get('era')), clean_value(stats.get('whip')),
                clean_value(stats.get('strikeouts')), clean_value(stats.get('walks')),
                clean_value(stats.get('innings_pitched')),
                clean_value(stats.get('avg_fastball_velo')), clean_value(stats.get('k_per_9')),
                clean_value(stats.get('bb_per_9')), clean_value(stats.get('games_pitched')),
                pitcher_id
            ))
        else:
            # Insert new
            cursor.execute("""
                INSERT INTO pitchers (
                    player_name, velocity, command, stamina, movement, repertoire,
                    putaway_skill, nibbling_tendency,
                    era, whip, strikeouts, walks, innings_pitched,
                    avg_fastball_velo, k_per_9, bb_per_9, season, games_pitched
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                stats.get('player_name'), attrs['velocity'], attrs['command'],
                attrs['stamina'], attrs['movement'], attrs['repertoire'],
                attrs.get('putaway_skill'), attrs.get('nibbling_tendency'),  # v2 attributes
                clean_value(stats.get('era')), clean_value(stats.get('whip')),
                clean_value(stats.get('strikeouts')), clean_value(stats.get('walks')),
                clean_value(stats.get('innings_pitched')),
                clean_value(stats.get('avg_fastball_velo')), clean_value(stats.get('k_per_9')),
                clean_value(stats.get('bb_per_9')), season, clean_value(stats.get('games_pitched'))
            ))
            pitcher_id = cursor.lastrowid

        return pitcher_id

    def _store_hitter(self, stats: pd.Series, season: int) -> Optional[int]:
        """Store a hitter in the database (v2: includes VISION + defensive attributes)."""
        # Convert offensive stats to attributes using v2 method (includes VISION)
        attrs = self.converter.mlb_stats_to_hitter_attributes_v2(
            batting_avg=clean_value(stats.get('batting_avg')),
            on_base_pct=clean_value(stats.get('on_base_pct')),
            slugging_pct=clean_value(stats.get('slugging_pct')),
            ops=clean_value(stats.get('ops')),
            home_runs=clean_value(stats.get('home_runs')),
            strikeouts=clean_value(stats.get('strikeouts')),
            walks=clean_value(stats.get('walks')),
            at_bats=clean_value(stats.get('at_bats')),
            avg_exit_velo=clean_value(stats.get('avg_exit_velo')),
            max_exit_velo=clean_value(stats.get('max_exit_velo')),
            barrel_pct=clean_value(stats.get('barrel_pct')),
            sprint_speed=clean_value(stats.get('sprint_speed')),
            stolen_bases=clean_value(stats.get('stolen_bases')),
        )

        # Convert defensive metrics to attributes (v2: CRITICAL for BABIP tuning)
        position = clean_value(stats.get('primary_position', 'LF'))  # Default to LF if missing
        if position is None or position == '':
            position = 'LF'  # Fallback default

        defensive_attrs = self.converter.mlb_stats_to_defensive_attributes(
            position=position,
            oaa=clean_value(stats.get('oaa')),
            sprint_speed=clean_value(stats.get('sprint_speed')),
            arm_strength_mph=clean_value(stats.get('arm_strength_mph')),
            drs=clean_value(stats.get('drs')),
            jump=clean_value(stats.get('jump')),
            jump_reaction=clean_value(stats.get('jump_reaction')),  # v3: Jump Reaction component
            jump_burst=clean_value(stats.get('jump_burst')),        # v3: Jump Burst component
            jump_route=clean_value(stats.get('jump_route')),        # v3: Jump Route component
            fielding_pct=clean_value(stats.get('fielding_pct')),
            back_oaa=clean_value(stats.get('back_oaa')),            # v3: Directional OAA going back
            in_oaa=clean_value(stats.get('in_oaa')),                # v3: Directional OAA coming in
            catch_5star_pct=clean_value(stats.get('catch_5star_pct')),    # v3: Catch probability 5-star
            catch_34star_pct=clean_value(stats.get('catch_34star_pct')),  # v3: Catch probability 3-4 star
        )

        cursor = self.conn.cursor()

        # Check if hitter exists
        cursor.execute(
            "SELECT hitter_id FROM hitters WHERE player_name = ? AND season = ?",
            (stats.get('player_name'), season)
        )
        existing = cursor.fetchone()

        if existing:
            # Update existing
            hitter_id = existing[0]
            cursor.execute("""
                UPDATE hitters SET
                    contact = ?, power = ?, discipline = ?, speed = ?,
                    vision = ?, attack_angle_control = ?,
                    reaction_time = ?, top_sprint_speed = ?, route_efficiency = ?,
                    arm_strength = ?, arm_accuracy = ?, fielding_secure = ?, 
                    jump_attr = ?, burst_attr = ?, range_back_attr = ?, range_in_attr = ?,
                    catch_elite_attr = ?, catch_difficult_attr = ?,
                    primary_position = ?,
                    batting_avg = ?, on_base_pct = ?, slugging_pct = ?, ops = ?,
                    home_runs = ?, stolen_bases = ?, strikeouts = ?, walks = ?,
                    avg_exit_velo = ?, max_exit_velo = ?, barrel_pct = ?,
                    sprint_speed = ?, games_played = ?, at_bats = ?,
                    oaa = ?, drs = ?, arm_strength_mph = ?, fielding_pct = ?, jump = ?, jump_oaa = ?,
                    jump_reaction = ?, jump_burst = ?, jump_route = ?,
                    back_oaa = ?, in_oaa = ?,
                    catch_5star_pct = ?, catch_34star_pct = ?,
                    bat_speed = ?, swing_length = ?, squared_up_rate = ?, hard_swing_rate = ?,
                    updated_at = CURRENT_TIMESTAMP
                WHERE hitter_id = ?
            """, (
                attrs['contact'], attrs['power'], attrs['discipline'], attrs['speed'],
                attrs.get('vision'),  # v2 offensive attribute
                attrs.get('attack_angle_control'),  # v2 Phase 2C - CRITICAL for HR generation
                defensive_attrs.get('reaction_time'), defensive_attrs.get('top_sprint_speed'),  # v2 defensive
                defensive_attrs.get('route_efficiency'), defensive_attrs.get('arm_strength'),
                defensive_attrs.get('arm_accuracy'), defensive_attrs.get('fielding_secure'),
                defensive_attrs.get('jump'),  # v3 jump attribute (0-100k)
                defensive_attrs.get('burst'),  # v3 burst attribute (0-100k)
                defensive_attrs.get('range_back'),  # v3 directional ability going back (0-100k)
                defensive_attrs.get('range_in'),    # v3 directional ability coming in (0-100k)
                defensive_attrs.get('catch_elite'),     # v3 catch elite plays (0-100k)
                defensive_attrs.get('catch_difficult'), # v3 catch difficult plays (0-100k)
                position,  # primary_position
                clean_value(stats.get('batting_avg')), clean_value(stats.get('on_base_pct')),
                clean_value(stats.get('slugging_pct')), clean_value(stats.get('ops')),
                clean_value(stats.get('home_runs')), clean_value(stats.get('stolen_bases')),
                clean_value(stats.get('strikeouts')), clean_value(stats.get('walks')),
                clean_value(stats.get('avg_exit_velo')), clean_value(stats.get('max_exit_velo')),
                clean_value(stats.get('barrel_pct')), clean_value(stats.get('sprint_speed')),
                clean_value(stats.get('games_played')), clean_value(stats.get('at_bats')),
                clean_value(stats.get('oaa')), clean_value(stats.get('drs')),  # defensive source data
                clean_value(stats.get('arm_strength_mph')), clean_value(stats.get('fielding_pct')),
                clean_value(stats.get('jump')),  # raw source data
                clean_value(stats.get('jump_oaa')),  # jump OAA (outfielders)
                clean_value(stats.get('jump_reaction')), clean_value(stats.get('jump_burst')),  # jump components
                clean_value(stats.get('jump_route')),
                clean_value(stats.get('back_oaa')), clean_value(stats.get('in_oaa')),  # directional OAA source
                clean_value(stats.get('catch_5star_pct')), clean_value(stats.get('catch_34star_pct')),  # catch prob source
                clean_value(stats.get('bat_speed')), clean_value(stats.get('swing_length')),  # bat tracking data
                clean_value(stats.get('squared_up_rate')), clean_value(stats.get('hard_swing_rate')),  # bat tracking data
                hitter_id
            ))
        else:
            # Insert new
            cursor.execute("""
                INSERT INTO hitters (
                    player_name, contact, power, discipline, speed,
                    vision, attack_angle_control,
                    reaction_time, top_sprint_speed, route_efficiency,
                    arm_strength, arm_accuracy, fielding_secure, 
                    jump_attr, burst_attr, range_back_attr, range_in_attr,
                    catch_elite_attr, catch_difficult_attr,
                    primary_position,
                    batting_avg, on_base_pct, slugging_pct, ops,
                    home_runs, stolen_bases, strikeouts, walks,
                    avg_exit_velo, max_exit_velo, barrel_pct, sprint_speed,
                    season, games_played, at_bats,
                    oaa, drs, arm_strength_mph, fielding_pct, jump, jump_oaa,
                    jump_reaction, jump_burst, jump_route, back_oaa, in_oaa,
                    catch_5star_pct, catch_34star_pct,
                    bat_speed, swing_length, squared_up_rate, hard_swing_rate
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                stats.get('player_name'), attrs['contact'], attrs['power'],
                attrs['discipline'], attrs['speed'],
                attrs.get('vision'),  # v2 offensive attribute
                attrs.get('attack_angle_control'),  # v2 Phase 2C - CRITICAL for HR generation
                defensive_attrs.get('reaction_time'), defensive_attrs.get('top_sprint_speed'),  # v2 defensive
                defensive_attrs.get('route_efficiency'), defensive_attrs.get('arm_strength'),
                defensive_attrs.get('arm_accuracy'), defensive_attrs.get('fielding_secure'),
                defensive_attrs.get('jump'),  # v3 jump attribute (0-100k)
                defensive_attrs.get('burst'),  # v3 burst attribute (0-100k)
                defensive_attrs.get('range_back'),  # v3 directional ability going back (0-100k)
                defensive_attrs.get('range_in'),    # v3 directional ability coming in (0-100k)
                defensive_attrs.get('catch_elite'),     # v3 catch elite plays (0-100k)
                defensive_attrs.get('catch_difficult'), # v3 catch difficult plays (0-100k)
                position,  # primary_position
                clean_value(stats.get('batting_avg')), clean_value(stats.get('on_base_pct')),
                clean_value(stats.get('slugging_pct')), clean_value(stats.get('ops')),
                clean_value(stats.get('home_runs')), clean_value(stats.get('stolen_bases')),
                clean_value(stats.get('strikeouts')), clean_value(stats.get('walks')),
                clean_value(stats.get('avg_exit_velo')), clean_value(stats.get('max_exit_velo')),
                clean_value(stats.get('barrel_pct')), clean_value(stats.get('sprint_speed')),
                season, clean_value(stats.get('games_played')), clean_value(stats.get('at_bats')),
                clean_value(stats.get('oaa')), clean_value(stats.get('drs')),  # defensive source data
                clean_value(stats.get('arm_strength_mph')), clean_value(stats.get('fielding_pct')),
                clean_value(stats.get('jump')),  # raw source data
                clean_value(stats.get('jump_oaa')),  # jump OAA (outfielders)
                clean_value(stats.get('jump_reaction')), clean_value(stats.get('jump_burst')),  # jump components
                clean_value(stats.get('jump_route')),
                clean_value(stats.get('back_oaa')), clean_value(stats.get('in_oaa')),  # directional OAA source
                clean_value(stats.get('catch_5star_pct')), clean_value(stats.get('catch_34star_pct')),  # catch prob source
                clean_value(stats.get('bat_speed')), clean_value(stats.get('swing_length')),  # bat tracking data
                clean_value(stats.get('squared_up_rate')), clean_value(stats.get('hard_swing_rate'))  # bat tracking data
            ))
            hitter_id = cursor.lastrowid

        return hitter_id

    def get_team_data(self, team_name: str, season: int) -> Optional[Dict]:
        """
        Get team data including all pitchers and hitters.

        Parameters
        ----------
        team_name : str
            Team name (e.g., 'New York Yankees')
        season : int
            Season year

        Returns
        -------
        dict or None
            Dictionary with keys: team_info, pitchers, hitters
        """
        cursor = self.conn.cursor()

        # Get team
        cursor.execute(
            "SELECT * FROM teams WHERE team_name = ? AND season = ?",
            (team_name, season)
        )
        team_row = cursor.fetchone()
        if not team_row:
            return None

        team_id = team_row['team_id']

        # Get pitchers with is_starter flag from team_rosters
        cursor.execute("""
            SELECT p.*, r.is_starter FROM pitchers p
            JOIN team_rosters r ON p.pitcher_id = r.pitcher_id
            WHERE r.team_id = ?
            ORDER BY r.is_starter DESC, p.innings_pitched DESC
        """, (team_id,))
        pitchers = [dict(row) for row in cursor.fetchall()]

        # Get hitters
        cursor.execute("""
            SELECT h.*, r.batting_order FROM hitters h
            JOIN team_rosters r ON h.hitter_id = r.hitter_id
            WHERE r.team_id = ?
            ORDER BY r.batting_order
        """, (team_id,))
        hitters = [dict(row) for row in cursor.fetchall()]

        return {
            'team_info': dict(team_row),
            'pitchers': pitchers,
            'hitters': hitters
        }

    def list_teams(self, season: Optional[int] = None) -> List[Dict]:
        """
        List all teams in database.

        Parameters
        ----------
        season : int, optional
            Filter by season

        Returns
        -------
        list of dict
            Team information dictionaries
        """
        cursor = self.conn.cursor()

        if season:
            cursor.execute(
                "SELECT * FROM teams WHERE season = ? ORDER BY team_name",
                (season,)
            )
        else:
            cursor.execute("SELECT * FROM teams ORDER BY season DESC, team_name")

        return [dict(row) for row in cursor.fetchall()]

    def delete_team(self, team_name: str, season: int) -> bool:
        """
        Delete a team and all associated players.

        Parameters
        ----------
        team_name : str
            Team name
        season : int
            Season year

        Returns
        -------
        bool
            True if deleted, False if not found
        """
        cursor = self.conn.cursor()

        cursor.execute(
            "SELECT team_id FROM teams WHERE team_name = ? AND season = ?",
            (team_name, season)
        )
        team = cursor.fetchone()

        if not team:
            return False

        team_id = team[0]

        # Delete roster entries
        cursor.execute("DELETE FROM team_rosters WHERE team_id = ?", (team_id,))

        # Delete team
        cursor.execute("DELETE FROM teams WHERE team_id = ?", (team_id,))

        self.conn.commit()
        return True


if __name__ == "__main__":
    # Test database operations
    print("=== Team Database Test ===\n")

    # Create database
    db = TeamDatabase("test_baseball.db")

    # Fetch and store a team (if pybaseball is working)
    try:
        num_p, num_h = db.fetch_and_store_team("NYY", season=2024, min_pitcher_innings=10, min_hitter_at_bats=30)
        print(f"Stored {num_p} pitchers and {num_h} hitters")
    except Exception as e:
        print(f"Could not fetch data: {e}")

    # List teams
    print("\nTeams in database:")
    teams = db.list_teams()
    for team in teams:
        print(f"  {team['team_name']} ({team['season']})")

    # Get team data
    if teams:
        team_data = db.get_team_data(teams[0]['team_name'], teams[0]['season'])
        if team_data:
            print(f"\n{team_data['team_info']['team_name']} roster:")
            print(f"  Pitchers: {len(team_data['pitchers'])}")
            print(f"  Hitters: {len(team_data['hitters'])}")

            if team_data['pitchers']:
                print("\n  Sample pitcher:")
                p = team_data['pitchers'][0]
                print(f"    {p['player_name']}")
                print(f"    Velocity: {p['velocity']:,} / 100,000")
                print(f"    Command:  {p['command']:,} / 100,000")
                print(f"    ERA: {p['era']:.2f}" if p['era'] else "    ERA: N/A")

            if team_data['hitters']:
                print("\n  Sample hitter:")
                h = team_data['hitters'][0]
                print(f"    {h['player_name']}")
                print(f"    Contact:    {h['contact']:,} / 100,000")
                print(f"    Power:      {h['power']:,} / 100,000")
                print(f"    AVG: {h['batting_avg']:.3f}" if h['batting_avg'] else "    AVG: N/A")

    db.close()
    print("\nTest complete!")
