#!/usr/bin/env python
"""
Export MLB team database to CSV files.

This standalone script converts the SQLite database to CSV format
for easy uploading to AI systems or external analysis.

Usage:
    python export_db_to_csv.py                           # Export default database
    python export_db_to_csv.py custom.db                 # Export custom database
    python export_db_to_csv.py --output my_exports/      # Custom output directory
    python export_db_to_csv.py --team "New York Yankees" 2024  # Export single team
"""

import argparse
import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent))

from batted_ball.database.csv_exporter import CSVExporter


def main():
    parser = argparse.ArgumentParser(
        description="Export MLB team database to CSV files",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s                                    Export default database to csv_exports/
  %(prog)s baseball_teams.db                  Export specific database
  %(prog)s --output my_exports/               Custom output directory
  %(prog)s --team "New York Yankees" 2024     Export single team to CSV

Output files:
  teams.csv         - Team metadata
  pitchers.csv      - All pitchers with attributes and MLB stats
  hitters.csv       - All hitters with attributes and MLB stats
  team_rosters.csv  - Player-team associations
  teams_full.csv    - Comprehensive denormalized view (best for AI)
        """
    )

    parser.add_argument(
        'database',
        nargs='?',
        default='baseball_teams.db',
        help='Database file to export (default: baseball_teams.db)'
    )

    parser.add_argument(
        '--output', '-o',
        default='csv_exports',
        help='Output directory for CSV files (default: csv_exports/)'
    )

    parser.add_argument(
        '--team',
        help='Export only a specific team (requires --season)'
    )

    parser.add_argument(
        '--season',
        type=int,
        help='Season for single team export'
    )

    parser.add_argument(
        '--quiet', '-q',
        action='store_true',
        help='Suppress progress messages'
    )

    args = parser.parse_args()

    # Validate arguments
    if args.team and not args.season:
        print("Error: --season is required when using --team")
        return 1

    # Check database exists
    db_path = Path(args.database)
    if not db_path.exists():
        print(f"Error: Database not found: {args.database}")
        print("\nAvailable databases in current directory:")
        for db_file in Path('.').glob('*.db'):
            print(f"  {db_file}")
        return 1

    try:
        exporter = CSVExporter(str(db_path))

        if args.team:
            # Export single team
            output_path = Path(args.output)
            output_path.mkdir(parents=True, exist_ok=True)

            # Create filename
            safe_name = args.team.replace(' ', '_').lower()
            csv_file = output_path / f"{safe_name}_{args.season}.csv"

            num_players = exporter.export_team_summary(args.team, args.season, csv_file)

            if num_players > 0:
                print(f"\n✓ Exported {args.team} ({args.season})")
                print(f"  {num_players} players → {csv_file}")
                print(f"\nFile: {csv_file.absolute()}")
            else:
                print(f"\nError: Team not found: {args.team} ({args.season})")
                return 1

        else:
            # Export all tables
            created_files = exporter.export_all(args.output, verbose=not args.quiet)

            if not args.quiet:
                print("\n✓ Export complete!")
                print(f"\nFiles created in: {Path(args.output).absolute()}")
                print("\nFor AI ingestion, use: teams_full.csv")
                print("  (Contains all player attributes in one denormalized file)")

        return 0

    except FileNotFoundError as e:
        print(f"Error: {e}")
        return 1
    except Exception as e:
        print(f"Error during export: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
