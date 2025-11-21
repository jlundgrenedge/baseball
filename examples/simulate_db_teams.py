"""
Interactive team selection and game simulation from database.

Allows users to:
1. Select two teams from baseball_teams.db
2. Choose number of games to simulate
3. Run simulations and view results
"""

import sys
from pathlib import Path
from typing import Optional, List
from datetime import datetime
from dataclasses import dataclass, field

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from batted_ball.database.team_loader import TeamLoader
from batted_ball.game_simulation import GameSimulator
from batted_ball.series_metrics import SeriesMetrics


# Map team abbreviations to their home ballpark
TEAM_BALLPARKS = {
    'CHC': 'wrigley',           # Chicago Cubs - Wrigley Field
    'CIN': 'great_american',    # Cincinnati Reds - Great American Ball Park
    'MIL': 'generic',           # Milwaukee Brewers - American Family Field (not in system yet)
    'PIT': 'generic',           # Pittsburgh Pirates - PNC Park (not in system yet)
    'STL': 'generic',           # St. Louis Cardinals - Busch Stadium (not in system yet)
    'ATL': 'generic',           # Atlanta Braves - Truist Park (not in system yet)
    'NYY': 'yankee',            # New York Yankees - Yankee Stadium
    'BOS': 'fenway',            # Boston Red Sox - Fenway Park
    'LAD': 'dodger',            # Los Angeles Dodgers - Dodger Stadium
    'SF': 'oracle',             # San Francisco Giants - Oracle Park
    'COL': 'coors',             # Colorado Rockies - Coors Field
    'HOU': 'minute_maid',       # Houston Astros - Minute Maid Park
    'SD': 'petco',              # San Diego Padres - Petco Park
    # Add more as needed - defaults to 'generic' if not found
}


def get_team_ballpark(team_name: str, team_abbr: str = None) -> str:
    """
    Get the home ballpark for a team.
    
    Parameters
    ----------
    team_name : str
        Full team name (e.g., "Chicago Cubs")
    team_abbr : str, optional
        Team abbreviation (e.g., "CHC")
    
    Returns
    -------
    str
        Ballpark name for simulation (e.g., "wrigley")
    """
    # If abbreviation provided, use direct lookup
    if team_abbr and team_abbr.upper() in TEAM_BALLPARKS:
        return TEAM_BALLPARKS[team_abbr.upper()]
    
    # Try to extract abbreviation from team name
    team_lower = team_name.lower()
    
    # Simple team name to abbreviation mapping
    name_to_abbr = {
        'cubs': 'CHC',
        'reds': 'CIN', 
        'brewers': 'MIL',
        'pirates': 'PIT',
        'cardinals': 'STL',
        'braves': 'ATL',
        'yankees': 'NYY',
        'red sox': 'BOS',
        'dodgers': 'LAD',
        'giants': 'SF',
        'rockies': 'COL',
        'diamondbacks': 'ARI',
        'padres': 'SD',
    }
    
    for key, abbr in name_to_abbr.items():
        if key in team_lower:
            return TEAM_BALLPARKS.get(abbr, 'generic')
    
    # Default to generic ballpark
    return 'generic'


def clear_screen():
    """Clear the console screen."""
    import os
    os.system('cls' if os.name == 'nt' else 'clear')


def display_header(title: str):
    """Display a formatted header."""
    print("\n" + "=" * 70)
    print(f"  {title}")
    print("=" * 70)


def select_team(loader: TeamLoader, prompt: str) -> Optional[tuple]:
    """
    Display team list and let user select one.

    Returns
    -------
    tuple or None
        (team_name, season) or None if cancelled
    """
    teams = loader.db.list_teams()

    if not teams:
        print("\n❌ No teams found in database!")
        print("\nTo add teams, use:")
        print("  python -m batted_ball.database.team_database")
        print("  or run examples/simulate_mlb_teams.py")
        return None

    # Group teams by season
    seasons = {}
    for team in teams:
        season = team['season']
        if season not in seasons:
            seasons[season] = []
        seasons[season].append(team)

    while True:
        display_header(prompt)
        print("\nAvailable teams:\n")

        # Display teams grouped by season
        idx = 1
        team_map = {}
        for season in sorted(seasons.keys(), reverse=True):
            print(f"\n  {season} Season:")
            for team in sorted(seasons[season], key=lambda t: t['team_name']):
                print(f"    {idx}. {team['team_name']}")
                team_map[idx] = (team['team_name'], team['season'])
                idx += 1

        print(f"\n    0. Cancel")
        print()

        try:
            choice = input("Enter team number: ").strip()

            if choice == '0':
                return None

            choice_num = int(choice)
            if choice_num in team_map:
                return team_map[choice_num]
            else:
                print(f"\n❌ Invalid choice. Please enter 1-{len(team_map)} or 0 to cancel.")
                input("\nPress Enter to continue...")
        except (ValueError, KeyboardInterrupt):
            print("\n❌ Invalid input.")
            input("\nPress Enter to continue...")


def get_num_games() -> Optional[int]:
    """
    Get number of games to simulate from user.

    Returns
    -------
    int or None
        Number of games, or None if cancelled
    """
    while True:
        display_header("Select Number of Games")
        print("\nHow many games would you like to simulate?")
        print("\n  Recommendations:")
        print("    1-10   : Quick test (~10-60 seconds)")
        print("    11-50  : Small series (~1-5 minutes)")
        print("    51-162 : Full season (~5-30 minutes)")
        print("\n  0. Cancel")
        print()

        try:
            choice = input("Enter number of games (1-500): ").strip()

            if choice == '0':
                return None

            num_games = int(choice)
            if 1 <= num_games <= 500:
                return num_games
            else:
                print("\n❌ Please enter a number between 1 and 500.")
                input("\nPress Enter to continue...")
        except (ValueError, KeyboardInterrupt):
            print("\n❌ Invalid input.")
            input("\nPress Enter to continue...")


def simulate_games(away_team_info: tuple, home_team_info: tuple, num_games: int):
    """
    Load teams from database and simulate games.

    Parameters
    ----------
    away_team_info : tuple
        (team_name, season) for away team
    home_team_info : tuple
        (team_name, season) for home team
    num_games : int
        Number of games to simulate
    """
    away_name, away_season = away_team_info
    home_name, home_season = home_team_info

    display_header("Loading Teams")

    # Load teams from database
    print(f"\nLoading {away_name} ({away_season})...")
    loader = TeamLoader()
    away_team = loader.load_team(away_name, away_season)

    if not away_team:
        print(f"\n❌ Failed to load {away_name}")
        loader.close()
        return

    print(f"\nLoading {home_name} ({home_season})...")
    home_team = loader.load_team(home_name, home_season)

    if not home_team:
        print(f"\n❌ Failed to load {home_name}")
        loader.close()
        return

    loader.close()

    # Get team abbreviations from database for ballpark lookup
    import sqlite3
    conn = sqlite3.connect('baseball_teams.db')
    cursor = conn.cursor()
    cursor.execute("SELECT team_abbr FROM teams WHERE team_name = ? AND season = ?", (home_name, home_season))
    home_abbr_row = cursor.fetchone()
    home_abbr = home_abbr_row[0] if home_abbr_row else None
    conn.close()

    # Determine home team's ballpark for simulation
    home_ballpark = get_team_ballpark(home_name, home_abbr)

    # Display matchup
    display_header("Matchup")
    print(f"\n  Away: {away_team.name} ({away_season})")
    print(f"  Home: {home_team.name} ({home_season})")
    print(f"  Ballpark: {home_ballpark.title()} (home field)")
    print(f"  Games: {num_games}")
    print(f"  Wind: Enabled (randomized per game)")
    print()

    # Confirm before running
    confirm = input("Start simulation? (y/n): ").strip().lower()
    if confirm != 'y':
        print("\n❌ Simulation cancelled.")
        return

    # Create log file for game output
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    safe_away = away_name.replace(" ", "_")
    safe_home = home_name.replace(" ", "_")
    log_filename = f"game_log_{safe_away}_vs_{safe_home}_{timestamp}.txt"
    log_path = Path("game_logs") / log_filename

    # Create game_logs directory if it doesn't exist
    log_path.parent.mkdir(exist_ok=True)

    # Run simulations
    display_header(f"Simulating {num_games} Game{'s' if num_games > 1 else ''}")
    print(f"\n📝 Game log will be saved to: {log_path}")
    print()

    # Initialize series metrics tracker
    series_metrics = SeriesMetrics(
        away_team_name=away_team.name,
        home_team_name=home_team.name
    )

    # Determine verbosity based on number of games
    # For 1-3 games: show in console
    # For 4+ games: only save to log file
    show_in_console = num_games <= 3

    # Open the log file for the entire series
    with open(log_path, 'w', encoding='utf-8') as log_file:
        # Write header to log file
        log_file.write(f"{'='*80}\n")
        log_file.write(f"GAME SERIES LOG\n")
        log_file.write(f"{'='*80}\n")
        log_file.write(f"Away Team: {away_team.name} ({away_season})\n")
        log_file.write(f"Home Team: {home_team.name} ({home_season})\n")
        log_file.write(f"Number of Games: {num_games}\n")
        log_file.write(f"Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        log_file.write(f"{'='*80}\n\n")
        log_file.flush()

        for i in range(num_games):
            if num_games > 1:
                print(f"\nGame {i+1}/{num_games}:")
                print("-" * 50)

            # Write game separator to log file
            log_file.write(f"\n\n{'#'*80}\n")
            log_file.write(f"# GAME {i+1} of {num_games}\n")
            log_file.write(f"{'#'*80}\n\n")
            log_file.flush()

            # Create simulator with verbose=True and EXHAUSTIVE metrics (level 3)
            # This provides maximum detail for tuning and analysis
            # Uses home team's ballpark and enables wind effects
            sim = GameSimulator(
                away_team, 
                home_team, 
                verbose=True, 
                debug_metrics=3,
                ballpark=home_ballpark,  # Home team's ballpark
                wind_enabled=True  # Randomized wind per game
            )

            # Capture stdout to write to log file
            import io
            import sys
            old_stdout = sys.stdout
            captured_output = io.StringIO()

            # If we want console output, use a Tee to write to both
            if show_in_console:
                class Tee:
                    def __init__(self, *streams):
                        self.streams = streams
                    def write(self, data):
                        for stream in self.streams:
                            stream.write(data)
                    def flush(self):
                        for stream in self.streams:
                            stream.flush()

                sys.stdout = Tee(old_stdout, captured_output)
            else:
                # Only capture, don't show in console
                sys.stdout = captured_output

            try:
                # Simulate game with home team's ballpark and wind effects
                final_state = sim.simulate_game(num_innings=9)
            finally:
                # Restore stdout
                sys.stdout = old_stdout

                # Write captured output to log file
                game_output = captured_output.getvalue()
                log_file.write(game_output)
                log_file.flush()

            # Update series metrics from game state
            series_metrics.update_from_game(final_state)

            # Determine winner for display
            if final_state.away_score > final_state.home_score:
                winner = away_team.name
            else:
                winner = home_team.name

            # Display score summary (always shown)
            print(f"\nFinal Score:")
            print(f"  {away_team.name}: {final_state.away_score}")
            print(f"  {home_team.name}: {final_state.home_score}")
            print(f"  Winner: {winner}")

        # Write comprehensive series summary to log file
        # Capture the print output from series_metrics
        import io
        import sys
        old_stdout = sys.stdout
        summary_output = io.StringIO()
        sys.stdout = summary_output

        try:
            series_metrics.print_summary()
        finally:
            sys.stdout = old_stdout

        # Write to log file
        log_file.write(summary_output.getvalue())
        log_file.flush()

    # Display comprehensive summary to console
    series_metrics.print_summary()
    print(f"\n✅ Complete game log saved to: {log_path}")
    print(f"   File size: {log_path.stat().st_size / 1024:.1f} KB")


def main():
    """Main interactive loop."""
    # Check if database exists
    db_path = Path("baseball_teams.db")
    if not db_path.exists():
        display_header("Database Not Found")
        print(f"\n❌ Database file '{db_path}' not found!")
        print("\nTo create the database and add teams:")
        print("  1. Run: python examples/simulate_mlb_teams.py")
        print("  2. Or manually run: python -m batted_ball.database.team_database")
        print("\nThis will fetch MLB team data and populate the database.")
        print()
        input("Press Enter to exit...")
        return

    loader = TeamLoader()

    try:
        while True:
            clear_screen()
            display_header("Baseball Team Simulation")
            print("\nSimulate games between teams stored in the database.")
            print()

            # Select away team
            away_info = select_team(loader, "Select Away Team")
            if not away_info:
                break

            clear_screen()
            print(f"\n✓ Away Team: {away_info[0]} ({away_info[1]})")

            # Select home team
            home_info = select_team(loader, "Select Home Team")
            if not home_info:
                continue

            clear_screen()
            print(f"\n✓ Away Team: {away_info[0]} ({away_info[1]})")
            print(f"✓ Home Team: {home_info[0]} ({home_info[1]})")

            # Get number of games
            num_games = get_num_games()
            if not num_games:
                continue

            # Simulate games
            simulate_games(away_info, home_info, num_games)

            # Ask to continue
            print()
            choice = input("Simulate another series? (y/n): ").strip().lower()
            if choice != 'y':
                break

    except KeyboardInterrupt:
        print("\n\n❌ Interrupted by user.")

    finally:
        loader.close()
        print("\nThank you for using the Baseball Team Simulator!")
        print()


if __name__ == "__main__":
    main()
