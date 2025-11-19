#!/usr/bin/env python
"""
Team Database Manager - CLI tool for managing MLB team database.

Usage:
    python manage_teams.py add NYY 2024                # Add Yankees 2024
    python manage_teams.py list                        # List all teams
    python manage_teams.py list --season 2024          # List teams for 2024
    python manage_teams.py delete "New York Yankees" 2024  # Delete a team
    python manage_teams.py add-multiple 2024 NYY LAD BOS  # Add multiple teams
"""

import argparse
import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent))

from batted_ball.database import TeamDatabase, PybaseballFetcher


def add_team(db: TeamDatabase, team_abbr: str, season: int, min_innings: float, min_at_bats: int, overwrite: bool):
    """Add a team to the database."""
    try:
        num_p, num_h = db.fetch_and_store_team(
            team_abbr,
            season=season,
            min_pitcher_innings=min_innings,
            min_hitter_at_bats=min_at_bats,
            overwrite=overwrite
        )

        if num_p > 0 or num_h > 0:
            print(f"✓ Successfully added {team_abbr} ({season})")
            print(f"  {num_p} pitchers, {num_h} hitters")
            return True
        else:
            print(f"✗ Failed to add {team_abbr} ({season}) - no data found")
            return False
    except Exception as e:
        print(f"✗ Error adding {team_abbr}: {e}")
        return False


def list_teams(db: TeamDatabase, season: int = None):
    """List all teams in database."""
    teams = db.list_teams(season=season)

    if not teams:
        print("No teams in database")
        return

    print(f"\nTeams in database: {len(teams)}")
    print("="*70)

    current_season = None
    for team in teams:
        if team['season'] != current_season:
            current_season = team['season']
            print(f"\n{current_season} Season:")
            print("-"*70)

        print(f"  {team['team_name']:30s} ({team['team_abbr']})")

    print()


def delete_team(db: TeamDatabase, team_name: str, season: int):
    """Delete a team from database."""
    if db.delete_team(team_name, season):
        print(f"✓ Deleted {team_name} ({season})")
    else:
        print(f"✗ Team not found: {team_name} ({season})")


def show_available_teams():
    """Show all available MLB team abbreviations."""
    teams = PybaseballFetcher.get_available_teams()
    print("\nAvailable MLB Teams:")
    print("="*70)

    # Group by division (approximate)
    al_east = ['BAL', 'BOS', 'NYY', 'TB', 'TOR']
    al_central = ['CHW', 'CLE', 'DET', 'KC', 'MIN']
    al_west = ['HOU', 'LAA', 'OAK', 'SEA', 'TEX']
    nl_east = ['ATL', 'MIA', 'NYM', 'PHI', 'WSH']
    nl_central = ['CHC', 'CIN', 'MIL', 'PIT', 'STL']
    nl_west = ['ARI', 'COL', 'LAD', 'SD', 'SF']

    divisions = [
        ("AL East", al_east),
        ("AL Central", al_central),
        ("AL West", al_west),
        ("NL East", nl_east),
        ("NL Central", nl_central),
        ("NL West", nl_west),
    ]

    for div_name, div_teams in divisions:
        print(f"\n{div_name}:")
        for abbr in div_teams:
            name = PybaseballFetcher.get_team_name(abbr)
            print(f"  {abbr:4s} - {name}")

    print()


def main():
    parser = argparse.ArgumentParser(
        description="Manage MLB team database for baseball simulations",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s add NYY 2024                      Add Yankees 2024
  %(prog)s add LAD 2023 --overwrite          Add Dodgers 2023, overwrite if exists
  %(prog)s add-multiple 2024 NYY LAD BOS     Add multiple teams for 2024
  %(prog)s list                              List all teams
  %(prog)s list --season 2024                List only 2024 teams
  %(prog)s delete "New York Yankees" 2024    Delete Yankees 2024
  %(prog)s show-teams                        Show available team abbreviations
        """
    )

    parser.add_argument(
        'command',
        choices=['add', 'list', 'delete', 'show-teams', 'add-multiple'],
        help='Command to execute'
    )

    parser.add_argument(
        'args',
        nargs='*',
        help='Command arguments (team abbreviation, season, etc.)'
    )

    parser.add_argument(
        '--db',
        default='baseball_teams.db',
        help='Database file path (default: baseball_teams.db)'
    )

    parser.add_argument(
        '--season',
        type=int,
        help='Season year (for filtering)'
    )

    parser.add_argument(
        '--min-innings',
        type=float,
        default=20.0,
        help='Minimum innings pitched for pitchers (default: 20.0)'
    )

    parser.add_argument(
        '--min-at-bats',
        type=int,
        default=50,
        help='Minimum at-bats for hitters (default: 50)'
    )

    parser.add_argument(
        '--overwrite',
        action='store_true',
        help='Overwrite existing team data'
    )

    args = parser.parse_args()

    # Handle show-teams command (doesn't need database)
    if args.command == 'show-teams':
        show_available_teams()
        return 0

    # Open database
    db = TeamDatabase(args.db)

    try:
        if args.command == 'add':
            if len(args.args) < 2:
                print("Error: add requires team abbreviation and season")
                print("Example: manage_teams.py add NYY 2024")
                return 1

            team_abbr = args.args[0].upper()
            season = int(args.args[1])

            add_team(db, team_abbr, season, args.min_innings, args.min_at_bats, args.overwrite)

        elif args.command == 'add-multiple':
            if len(args.args) < 2:
                print("Error: add-multiple requires season and team abbreviations")
                print("Example: manage_teams.py add-multiple 2024 NYY LAD BOS")
                return 1

            season = int(args.args[0])
            team_abbrs = [t.upper() for t in args.args[1:]]

            print(f"\nAdding {len(team_abbrs)} teams for {season} season...")
            print("="*70)

            success_count = 0
            for team_abbr in team_abbrs:
                if add_team(db, team_abbr, season, args.min_innings, args.min_at_bats, args.overwrite):
                    success_count += 1
                print()  # Blank line between teams

            print("="*70)
            print(f"Successfully added {success_count}/{len(team_abbrs)} teams")

        elif args.command == 'list':
            list_teams(db, season=args.season)

        elif args.command == 'delete':
            if len(args.args) < 2:
                print("Error: delete requires team name and season")
                print('Example: manage_teams.py delete "New York Yankees" 2024')
                return 1

            team_name = args.args[0]
            season = int(args.args[1])

            delete_team(db, team_name, season)

        return 0

    finally:
        db.close()


if __name__ == "__main__":
    sys.exit(main())
