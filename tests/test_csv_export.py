#!/usr/bin/env python
"""
Test script to verify CSV export functionality.

This script:
1. Creates a test database with sample data
2. Tests the CSV exporter
3. Validates output files
"""

import sys
from pathlib import Path
import sqlite3

# Direct imports to avoid numpy dependencies
sys.path.insert(0, str(Path(__file__).parent / 'batted_ball' / 'database'))

from csv_exporter import CSVExporter
from db_schema import DatabaseSchema


def create_test_database():
    """Create a minimal test database with sample data."""
    print("Creating test database...")

    db_path = Path("test_csv_export.db")
    if db_path.exists():
        db_path.unlink()

    conn = DatabaseSchema.initialize_database(db_path)
    cursor = conn.cursor()

    # Add a test team
    cursor.execute("""
        INSERT INTO teams (team_name, team_abbr, season, league, division)
        VALUES ('Test Yankees', 'TEST', 2024, 'AL', 'East')
    """)
    team_id = cursor.lastrowid

    # Add test pitcher
    cursor.execute("""
        INSERT INTO pitchers (
            player_name, velocity, command, stamina, movement, repertoire,
            era, whip, k_per_9, bb_per_9, innings_pitched, avg_fastball_velo,
            season, games_pitched, hand
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        "Test Pitcher", 75000, 70000, 65000, 60000, 55000,
        3.50, 1.20, 9.5, 2.8, 180.0, 94.5,
        2024, 32, "R"
    ))
    pitcher_id = cursor.lastrowid

    # Add test hitter
    cursor.execute("""
        INSERT INTO hitters (
            player_name, contact, power, discipline, speed,
            batting_avg, on_base_pct, slugging_pct, ops,
            home_runs, stolen_bases, strikeouts, walks,
            avg_exit_velo, max_exit_velo, sprint_speed,
            season, games_played, at_bats, position, hand
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        "Test Hitter", 72000, 68000, 64000, 70000,
        0.285, 0.350, 0.475, 0.825,
        28, 15, 145, 65,
        89.5, 112.3, 28.5,
        2024, 150, 550, "CF", "L"
    ))
    hitter_id = cursor.lastrowid

    # Link to team
    cursor.execute("""
        INSERT INTO team_rosters (team_id, pitcher_id, is_starter)
        VALUES (?, ?, 1)
    """, (team_id, pitcher_id))

    cursor.execute("""
        INSERT INTO team_rosters (team_id, hitter_id, batting_order)
        VALUES (?, ?, 1)
    """, (team_id, hitter_id))

    conn.commit()
    conn.close()

    print(f"✓ Created test database: {db_path}")
    return db_path


def test_csv_export(db_path):
    """Test CSV export functionality."""
    print(f"\nTesting CSV export...")

    output_dir = Path("test_csv_output")

    # Clean up old test output
    if output_dir.exists():
        import shutil
        shutil.rmtree(output_dir)

    # Export
    exporter = CSVExporter(str(db_path))
    created_files = exporter.export_all(str(output_dir), verbose=True)

    # Verify files
    print(f"\n{'='*70}")
    print("Validating CSV files...")
    print(f"{'='*70}\n")

    expected_files = [
        "teams.csv",
        "pitchers.csv",
        "hitters.csv",
        "team_rosters.csv",
        "teams_full.csv"
    ]

    all_valid = True
    for filename in expected_files:
        file_path = output_dir / filename
        if file_path.exists():
            size = file_path.stat().st_size

            # Check if file has content (header + at least 1 row)
            with open(file_path, 'r') as f:
                lines = f.readlines()
                num_lines = len(lines)

            if num_lines >= 2:  # Header + data
                print(f"  ✓ {filename:25s} {size:6d} bytes, {num_lines-1:2d} data rows")
            else:
                print(f"  ✗ {filename:25s} {size:6d} bytes, {num_lines-1:2d} data rows (EMPTY)")
                all_valid = False
        else:
            print(f"  ✗ {filename:25s} MISSING")
            all_valid = False

    print(f"\n{'='*70}")
    if all_valid:
        print("✓ All CSV files validated successfully!")
    else:
        print("✗ Some CSV files failed validation")
    print(f"{'='*70}\n")

    return all_valid


def test_single_team_export(db_path):
    """Test single team export."""
    print("\nTesting single team export...")

    output_file = Path("test_csv_output") / "test_team.csv"

    exporter = CSVExporter(str(db_path))
    num_players = exporter.export_team_summary(
        team_name="Test Yankees",
        season=2024,
        output_path=output_file
    )

    if num_players > 0:
        print(f"  ✓ Exported {num_players} players to {output_file}")

        # Verify content
        with open(output_file, 'r') as f:
            lines = f.readlines()
            print(f"  ✓ File has {len(lines)-1} data rows")

        return True
    else:
        print(f"  ✗ Failed to export team")
        return False


def cleanup():
    """Clean up test files."""
    print("\nCleaning up test files...")

    test_files = [
        Path("test_csv_export.db"),
        Path("test_csv_output"),
    ]

    import shutil
    for path in test_files:
        if path.exists():
            if path.is_dir():
                shutil.rmtree(path)
            else:
                path.unlink()
            print(f"  ✓ Removed {path}")


def main():
    print("\n" + "="*70)
    print("CSV Export Test Suite")
    print("="*70 + "\n")

    try:
        # Create test database
        db_path = create_test_database()

        # Test full export
        test1 = test_csv_export(db_path)

        # Test single team export
        test2 = test_single_team_export(db_path)

        # Summary
        print("\n" + "="*70)
        print("Test Summary")
        print("="*70)
        print(f"  Full export:        {'✓ PASS' if test1 else '✗ FAIL'}")
        print(f"  Single team export: {'✓ PASS' if test2 else '✗ FAIL'}")
        print("="*70 + "\n")

        if test1 and test2:
            print("✓ All tests passed!")
            print("\nYou can now inspect the test output:")
            print("  - test_csv_output/teams_full.csv")
            print("  - test_csv_output/pitchers.csv")
            print("  - test_csv_output/hitters.csv")
            print("\nTo clean up test files, run:")
            print("  rm -rf test_csv_export.db test_csv_output/")
            return 0
        else:
            print("✗ Some tests failed")
            return 1

    except Exception as e:
        print(f"\n✗ Error during testing: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
