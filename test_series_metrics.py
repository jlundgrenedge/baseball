#!/usr/bin/env python
"""
Test script for enhanced series metrics.

This script runs a small series between test teams to demonstrate
the new comprehensive statistics output.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from batted_ball import GameSimulator, create_test_team, SeriesMetrics


def main():
    """Run a test series and display enhanced metrics"""
    print("\n" + "="*80)
    print("SERIES METRICS TEST")
    print("="*80)

    # Create test teams
    print("\nCreating test teams...")
    home_team = create_test_team("Test Yankees", team_quality="elite")
    away_team = create_test_team("Test Red Sox", team_quality="good")

    # Number of games for test
    num_games = 5
    print(f"Simulating {num_games} game series...")

    # Initialize series metrics
    series_metrics = SeriesMetrics(
        away_team_name=away_team.name,
        home_team_name=home_team.name
    )

    # Simulate games
    for i in range(num_games):
        print(f"\n  Game {i+1}/{num_games}...", end="", flush=True)

        # Create simulator (verbose=False for cleaner output)
        sim = GameSimulator(away_team, home_team, verbose=False)

        # Simulate game
        final_state = sim.simulate_game(num_innings=9)

        # Update series metrics
        series_metrics.update_from_game(final_state)

        # Display score
        print(f" Final: {away_team.name} {final_state.away_score} - {home_team.name} {final_state.home_score}")

    # Display comprehensive series summary
    print("\n" + "="*80)
    series_metrics.print_summary()

    print("\n✅ Test complete!")
    print("\nThis demonstrates the new comprehensive series statistics including:")
    print("  - Advanced sabermetrics (wOBA, ISO, BABIP, etc.)")
    print("  - Pitching metrics (ERA, WHIP, K/9, BB/9)")
    print("  - Fielding statistics")
    print("  - MLB realism benchmarks with pass/fail indicators")
    print("  - Run distribution analysis")
    print()


if __name__ == "__main__":
    main()
