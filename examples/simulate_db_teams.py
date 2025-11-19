"""
Interactive team selection and game simulation from database.

Allows users to:
1. Select two teams from baseball_teams.db
2. Choose number of games to simulate
3. Run simulations and view results
"""

import sys
from pathlib import Path
from typing import Optional

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from batted_ball.database.team_loader import TeamLoader
from batted_ball.game_simulation import GameSimulator


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

    # Display matchup
    display_header("Matchup")
    print(f"\n  Away: {away_team.name} ({away_season})")
    print(f"  Home: {home_team.name} ({home_season})")
    print(f"  Games: {num_games}")
    print()

    # Confirm before running
    confirm = input("Start simulation? (y/n): ").strip().lower()
    if confirm != 'y':
        print("\n❌ Simulation cancelled.")
        return

    # Run simulations
    display_header(f"Simulating {num_games} Game{'s' if num_games > 1 else ''}")
    print()

    away_wins = 0
    home_wins = 0
    total_away_runs = 0
    total_home_runs = 0

    # Determine verbosity based on number of games
    verbose = num_games <= 3

    for i in range(num_games):
        if num_games > 1:
            print(f"\nGame {i+1}/{num_games}:")
            print("-" * 50)

        # Create simulator
        sim = GameSimulator(away_team, home_team, verbose=verbose)

        # Simulate game
        final_state = sim.simulate_game(num_innings=9)

        # Track results
        total_away_runs += final_state.away_score
        total_home_runs += final_state.home_score

        if final_state.away_score > final_state.home_score:
            away_wins += 1
            winner = away_team.name
        else:
            home_wins += 1
            winner = home_team.name

        # Display score
        print(f"\nFinal Score:")
        print(f"  {away_team.name}: {final_state.away_score}")
        print(f"  {home_team.name}: {final_state.home_score}")
        print(f"  Winner: {winner}")

    # Display summary
    display_header("Series Results")
    print(f"\n  {away_team.name} ({away_season}):")
    print(f"    Wins: {away_wins}")
    print(f"    Total Runs: {total_away_runs}")
    print(f"    Avg Runs/Game: {total_away_runs/num_games:.2f}")

    print(f"\n  {home_team.name} ({home_season}):")
    print(f"    Wins: {home_wins}")
    print(f"    Total Runs: {total_home_runs}")
    print(f"    Avg Runs/Game: {total_home_runs/num_games:.2f}")

    print(f"\n  Series Winner: ", end="")
    if away_wins > home_wins:
        print(f"{away_team.name} ({away_wins}-{home_wins})")
    elif home_wins > away_wins:
        print(f"{home_team.name} ({home_wins}-{away_wins})")
    else:
        print(f"TIED ({away_wins}-{home_wins})")

    print("\n" + "=" * 70)


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
