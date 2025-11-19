#!/usr/bin/env python
"""
Simulate MLB matchups using teams loaded from database.

This script demonstrates how to:
1. Load real MLB teams from the database
2. Run game simulations between them
3. Display realistic game results

Usage:
    python examples/simulate_mlb_matchup.py "New York Yankees" "Los Angeles Dodgers" 2024
    python examples/simulate_mlb_matchup.py "Boston Red Sox" "New York Yankees" 2024 --games 10
"""

import argparse
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from batted_ball.database import TeamLoader
from batted_ball.game_simulation import GameSimulator


def simulate_matchup(
    home_team_name: str,
    away_team_name: str,
    season: int = 2024,
    num_games: int = 1,
    verbose: bool = True,
    db_path: str = "baseball_teams.db"
):
    """
    Simulate a matchup between two MLB teams.

    Parameters
    ----------
    home_team_name : str
        Home team name (e.g., 'New York Yankees')
    away_team_name : str
        Away team name (e.g., 'Los Angeles Dodgers')
    season : int
        Season year
    num_games : int
        Number of games to simulate
    verbose : bool
        Print detailed play-by-play
    db_path : str
        Database file path
    """
    print("\n" + "="*70)
    print(f"MLB Matchup Simulation - {season} Season")
    print("="*70)

    # Load teams from database
    loader = TeamLoader(db_path)

    print(f"\nLoading teams...")
    home_team = loader.load_team(home_team_name, season=season)
    away_team = loader.load_team(away_team_name, season=season)

    if not home_team or not away_team:
        print("\n✗ Error: Could not load one or both teams")
        print("\nAvailable teams:")
        for team in loader.list_available_teams(season=season):
            print(f"  - {team}")
        loader.close()
        return

    loader.close()

    # Simulate games
    print(f"\n{'='*70}")
    print(f"Simulating {num_games} game(s)...")
    print(f"Home: {home_team.name}")
    print(f"Away: {away_team.name}")
    print(f"{'='*70}\n")

    home_wins = 0
    away_wins = 0
    total_home_runs = 0
    total_away_runs = 0

    for game_num in range(num_games):
        if num_games > 1:
            print(f"\n--- Game {game_num + 1}/{num_games} ---")

        # Create simulator
        sim = GameSimulator(
            away_team=away_team,
            home_team=home_team,
            verbose=verbose and num_games == 1  # Only verbose for single games
        )

        # Simulate game
        result = sim.simulate_game(num_innings=9)

        # Track results
        total_home_runs += result.home_score
        total_away_runs += result.away_score

        if result.home_score > result.away_score:
            home_wins += 1
            winner = home_team.name
        else:
            away_wins += 1
            winner = away_team.name

        # Print result
        print(f"\nFinal Score:")
        print(f"  {away_team.name}: {result.away_score}")
        print(f"  {home_team.name}: {result.home_score}")
        if num_games > 1:
            print(f"  Winner: {winner}")

    # Summary for multiple games
    if num_games > 1:
        print(f"\n{'='*70}")
        print(f"Series Summary ({num_games} games)")
        print(f"{'='*70}")
        print(f"{away_team.name}: {away_wins} wins ({away_wins/num_games*100:.1f}%)")
        print(f"{home_team.name}: {home_wins} wins ({home_wins/num_games*100:.1f}%)")
        print(f"\nAverage Score:")
        print(f"  {away_team.name}: {total_away_runs/num_games:.1f} runs/game")
        print(f"  {home_team.name}: {total_home_runs/num_games:.1f} runs/game")
        print(f"{'='*70}\n")


def main():
    parser = argparse.ArgumentParser(
        description="Simulate MLB matchups using teams from database",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s "New York Yankees" "Los Angeles Dodgers" 2024
  %(prog)s "Boston Red Sox" "New York Yankees" 2024 --games 10
  %(prog)s "Houston Astros" "Atlanta Braves" 2024 --quiet --games 100
        """
    )

    parser.add_argument(
        'home_team',
        help='Home team name (e.g., "New York Yankees")'
    )

    parser.add_argument(
        'away_team',
        help='Away team name (e.g., "Los Angeles Dodgers")'
    )

    parser.add_argument(
        'season',
        type=int,
        nargs='?',
        default=2024,
        help='Season year (default: 2024)'
    )

    parser.add_argument(
        '--games',
        type=int,
        default=1,
        help='Number of games to simulate (default: 1)'
    )

    parser.add_argument(
        '--quiet',
        action='store_true',
        help='Disable verbose play-by-play output'
    )

    parser.add_argument(
        '--db',
        default='baseball_teams.db',
        help='Database file path (default: baseball_teams.db)'
    )

    args = parser.parse_args()

    simulate_matchup(
        home_team_name=args.home_team,
        away_team_name=args.away_team,
        season=args.season,
        num_games=args.games,
        verbose=not args.quiet,
        db_path=args.db
    )

    return 0


if __name__ == "__main__":
    sys.exit(main())
