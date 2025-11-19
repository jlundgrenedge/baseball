"""
CSV export functionality for MLB team database.

Exports database tables to CSV files for easy sharing with AI systems
or external analysis tools.
"""

import csv
import sqlite3
from pathlib import Path
from typing import Optional, List
import pandas as pd


class CSVExporter:
    """
    Export database tables to CSV files.

    Usage:
        exporter = CSVExporter("baseball_teams.db")
        exporter.export_all("exports/")
        # Creates: teams.csv, pitchers.csv, hitters.csv, team_rosters.csv
    """

    def __init__(self, db_path: str = "baseball_teams.db"):
        """
        Initialize CSV exporter.

        Parameters
        ----------
        db_path : str
            Path to SQLite database
        """
        self.db_path = Path(db_path)
        if not self.db_path.exists():
            raise FileNotFoundError(f"Database not found: {db_path}")

    def export_all(self, output_dir: str = "csv_exports", verbose: bool = True) -> List[Path]:
        """
        Export all database tables to CSV files.

        Parameters
        ----------
        output_dir : str
            Directory to write CSV files to (created if doesn't exist)
        verbose : bool
            Print progress messages

        Returns
        -------
        list of Path
            Paths to created CSV files
        """
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)

        created_files = []

        if verbose:
            print(f"\n{'='*70}")
            print(f"Exporting database to CSV: {self.db_path}")
            print(f"Output directory: {output_path.absolute()}")
            print(f"{'='*70}\n")

        # Export each table
        tables = [
            ('teams', self.export_teams),
            ('pitchers', self.export_pitchers),
            ('hitters', self.export_hitters),
            ('team_rosters', self.export_team_rosters),
        ]

        for table_name, export_func in tables:
            csv_path = output_path / f"{table_name}.csv"
            num_rows = export_func(csv_path)
            created_files.append(csv_path)

            if verbose:
                print(f"  ✓ {table_name:20s} → {csv_path.name:25s} ({num_rows:4d} rows)")

        # Export combined team views
        csv_path = output_path / "teams_full.csv"
        num_rows = self.export_teams_full(csv_path)
        created_files.append(csv_path)
        if verbose:
            print(f"  ✓ {'teams_full':20s} → {csv_path.name:25s} ({num_rows:4d} rows)")

        if verbose:
            print(f"\n{'='*70}")
            print(f"Exported {len(created_files)} CSV files to {output_path.absolute()}")
            print(f"{'='*70}\n")

        return created_files

    def export_teams(self, output_path: Path) -> int:
        """Export teams table to CSV."""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row

        cursor = conn.cursor()
        cursor.execute("SELECT * FROM teams ORDER BY season DESC, team_name")
        rows = cursor.fetchall()

        if rows:
            with open(output_path, 'w', newline='', encoding='utf-8') as f:
                writer = csv.DictWriter(f, fieldnames=rows[0].keys())
                writer.writeheader()
                for row in rows:
                    writer.writerow(dict(row))

        conn.close()
        return len(rows)

    def export_pitchers(self, output_path: Path) -> int:
        """Export pitchers table to CSV."""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row

        cursor = conn.cursor()
        cursor.execute("""
            SELECT
                p.*,
                t.team_name,
                t.team_abbr,
                r.is_starter
            FROM pitchers p
            LEFT JOIN team_rosters r ON p.pitcher_id = r.pitcher_id
            LEFT JOIN teams t ON r.team_id = t.team_id
            ORDER BY p.season DESC, t.team_name, p.innings_pitched DESC
        """)
        rows = cursor.fetchall()

        if rows:
            with open(output_path, 'w', newline='', encoding='utf-8') as f:
                writer = csv.DictWriter(f, fieldnames=rows[0].keys())
                writer.writeheader()
                for row in rows:
                    writer.writerow(dict(row))

        conn.close()
        return len(rows)

    def export_hitters(self, output_path: Path) -> int:
        """Export hitters table to CSV."""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row

        cursor = conn.cursor()
        cursor.execute("""
            SELECT
                h.*,
                t.team_name,
                t.team_abbr,
                r.batting_order
            FROM hitters h
            LEFT JOIN team_rosters r ON h.hitter_id = r.hitter_id
            LEFT JOIN teams t ON r.team_id = t.team_id
            ORDER BY h.season DESC, t.team_name, r.batting_order
        """)
        rows = cursor.fetchall()

        if rows:
            with open(output_path, 'w', newline='', encoding='utf-8') as f:
                writer = csv.DictWriter(f, fieldnames=rows[0].keys())
                writer.writeheader()
                for row in rows:
                    writer.writerow(dict(row))

        conn.close()
        return len(rows)

    def export_team_rosters(self, output_path: Path) -> int:
        """Export team_rosters table to CSV."""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row

        cursor = conn.cursor()
        cursor.execute("""
            SELECT
                r.*,
                t.team_name,
                t.team_abbr,
                t.season,
                COALESCE(p.player_name, h.player_name) as player_name,
                CASE
                    WHEN p.pitcher_id IS NOT NULL THEN 'Pitcher'
                    WHEN h.hitter_id IS NOT NULL THEN 'Hitter'
                END as player_type
            FROM team_rosters r
            JOIN teams t ON r.team_id = t.team_id
            LEFT JOIN pitchers p ON r.pitcher_id = p.pitcher_id
            LEFT JOIN hitters h ON r.hitter_id = h.hitter_id
            ORDER BY t.season DESC, t.team_name, r.batting_order
        """)
        rows = cursor.fetchall()

        if rows:
            with open(output_path, 'w', newline='', encoding='utf-8') as f:
                writer = csv.DictWriter(f, fieldnames=rows[0].keys())
                writer.writeheader()
                for row in rows:
                    writer.writerow(dict(row))

        conn.close()
        return len(rows)

    def export_teams_full(self, output_path: Path) -> int:
        """
        Export comprehensive team view with all player attributes.

        This creates a denormalized view perfect for AI ingestion.
        Each row contains team info + player attributes.
        """
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row

        cursor = conn.cursor()

        # Get all data in one comprehensive query
        cursor.execute("""
            SELECT
                t.team_name,
                t.team_abbr,
                t.season,
                t.league,
                t.division,
                'Pitcher' as player_type,
                p.player_name,
                p.velocity as attribute_velocity,
                p.command as attribute_command,
                p.stamina as attribute_stamina,
                p.movement as attribute_movement,
                p.repertoire as attribute_repertoire,
                NULL as attribute_contact,
                NULL as attribute_power,
                NULL as attribute_discipline,
                NULL as attribute_speed,
                p.era,
                p.whip,
                p.k_per_9,
                p.bb_per_9,
                p.innings_pitched,
                p.games_pitched,
                p.avg_fastball_velo,
                NULL as batting_avg,
                NULL as on_base_pct,
                NULL as slugging_pct,
                NULL as ops,
                NULL as home_runs,
                NULL as stolen_bases,
                p.strikeouts,
                p.walks,
                NULL as avg_exit_velo,
                NULL as max_exit_velo,
                NULL as barrel_pct,
                NULL as sprint_speed,
                NULL as at_bats,
                NULL as batting_order,
                r.is_starter,
                p.hand,
                p.position
            FROM pitchers p
            JOIN team_rosters r ON p.pitcher_id = r.pitcher_id
            JOIN teams t ON r.team_id = t.team_id

            UNION ALL

            SELECT
                t.team_name,
                t.team_abbr,
                t.season,
                t.league,
                t.division,
                'Hitter' as player_type,
                h.player_name,
                NULL as attribute_velocity,
                NULL as attribute_command,
                NULL as attribute_stamina,
                NULL as attribute_movement,
                NULL as attribute_repertoire,
                h.contact as attribute_contact,
                h.power as attribute_power,
                h.discipline as attribute_discipline,
                h.speed as attribute_speed,
                NULL as era,
                NULL as whip,
                NULL as k_per_9,
                NULL as bb_per_9,
                NULL as innings_pitched,
                NULL as games_pitched,
                NULL as avg_fastball_velo,
                h.batting_avg,
                h.on_base_pct,
                h.slugging_pct,
                h.ops,
                h.home_runs,
                h.stolen_bases,
                h.strikeouts,
                h.walks,
                h.avg_exit_velo,
                h.max_exit_velo,
                h.barrel_pct,
                h.sprint_speed,
                h.at_bats,
                r.batting_order,
                NULL as is_starter,
                h.hand,
                h.position
            FROM hitters h
            JOIN team_rosters r ON h.hitter_id = r.hitter_id
            JOIN teams t ON r.team_id = t.team_id

            ORDER BY season DESC, team_name, player_type DESC, batting_order
        """)
        rows = cursor.fetchall()

        if rows:
            with open(output_path, 'w', newline='', encoding='utf-8') as f:
                writer = csv.DictWriter(f, fieldnames=rows[0].keys())
                writer.writeheader()
                for row in rows:
                    writer.writerow(dict(row))

        conn.close()
        return len(rows)

    def export_team_summary(self, team_name: str, season: int, output_path: Path) -> int:
        """
        Export a single team's full roster to CSV.

        Parameters
        ----------
        team_name : str
            Team name (e.g., 'New York Yankees')
        season : int
            Season year
        output_path : Path
            Output CSV file path

        Returns
        -------
        int
            Number of players exported
        """
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row

        cursor = conn.cursor()

        # Get team ID
        cursor.execute(
            "SELECT team_id FROM teams WHERE team_name = ? AND season = ?",
            (team_name, season)
        )
        team_row = cursor.fetchone()
        if not team_row:
            conn.close()
            return 0

        team_id = team_row[0]

        # Get all players
        cursor.execute("""
            SELECT
                t.team_name,
                t.team_abbr,
                t.season,
                CASE
                    WHEN p.pitcher_id IS NOT NULL THEN 'Pitcher'
                    WHEN h.hitter_id IS NOT NULL THEN 'Hitter'
                END as player_type,
                COALESCE(p.player_name, h.player_name) as player_name,
                p.velocity,
                p.command,
                p.stamina,
                p.movement,
                p.repertoire,
                h.contact,
                h.power,
                h.discipline,
                h.speed,
                p.era,
                p.whip,
                p.k_per_9,
                p.bb_per_9,
                p.innings_pitched,
                h.batting_avg,
                h.on_base_pct,
                h.slugging_pct,
                h.ops,
                h.home_runs,
                h.avg_exit_velo,
                h.sprint_speed,
                r.batting_order,
                r.is_starter
            FROM team_rosters r
            JOIN teams t ON r.team_id = t.team_id
            LEFT JOIN pitchers p ON r.pitcher_id = p.pitcher_id
            LEFT JOIN hitters h ON r.hitter_id = h.hitter_id
            WHERE t.team_id = ?
            ORDER BY
                CASE WHEN p.pitcher_id IS NOT NULL THEN 1 ELSE 2 END,
                r.batting_order,
                p.innings_pitched DESC
        """, (team_id,))

        rows = cursor.fetchall()

        if rows:
            with open(output_path, 'w', newline='', encoding='utf-8') as f:
                writer = csv.DictWriter(f, fieldnames=rows[0].keys())
                writer.writeheader()
                for row in rows:
                    writer.writerow(dict(row))

        conn.close()
        return len(rows)


if __name__ == "__main__":
    # Test CSV export
    import sys

    if len(sys.argv) > 1:
        db_path = sys.argv[1]
    else:
        db_path = "baseball_teams.db"

    try:
        exporter = CSVExporter(db_path)
        exporter.export_all("csv_exports", verbose=True)
        print("\n✓ Export complete!")
    except FileNotFoundError as e:
        print(f"Error: {e}")
        sys.exit(1)
