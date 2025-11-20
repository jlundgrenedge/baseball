#!/usr/bin/env python3
"""
Test script to validate MLB realism fixes from 2025-11-20.

Tests the following fixes:
1. Launch angle distribution (lowered attack angle means)
2. Strikeout rate (increased whiff probability impact)
3. Walk rate (reduced intentional ball rates)
4. Power metrics (increased collision efficiency)

Expected improvements:
- Batted ball distribution: 54% FB → ~34% FB, 12% GB → ~45% GB
- K%: 10.5% → ~22%
- BB%: 15% → ~8.5%
- Hard hit rate: 5.2% → ~40%
- HR/FB: 0.6% → ~12.5%
"""

import sys
sys.path.insert(0, '/home/user/baseball')

from batted_ball import GameSimulator
from batted_ball.game_simulation import create_test_team
from batted_ball.series_metrics import SeriesMetrics

def main():
    print("=" * 80)
    print("MLB REALISM VALIDATION TEST")
    print("Testing fixes from 2025-11-20")
    print("=" * 80)
    print()

    # Create two average teams
    print("Creating teams...")
    home_team = create_test_team("Home Team", team_quality="average")
    away_team = create_test_team("Away Team", team_quality="average")
    print(f"✓ Created {home_team.name} and {away_team.name}")
    print()

    # Simulate 10 games
    num_games = 10
    print(f"Simulating {num_games} games...")
    series = SeriesMetrics()

    for game_num in range(1, num_games + 1):
        print(f"  Game {game_num}/{num_games}...", end="", flush=True)

        # Alternate home/away
        if game_num % 2 == 0:
            sim = GameSimulator(home_team, away_team, verbose=False)
        else:
            sim = GameSimulator(away_team, home_team, verbose=False)

        result = sim.simulate_game(num_innings=9)
        series.update_from_game(result)

        print(f" {result.away_score}-{result.home_score}")

    print()
    print("=" * 80)
    print("SERIES STATISTICS")
    print("=" * 80)
    print()

    # Print comprehensive summary
    series.print_summary()

    print()
    print("=" * 80)
    print("PASS 2 VALIDATION SUMMARY")
    print("=" * 80)
    print()

    # Compute and access realism checks
    series.compute_realism_checks()

    # Count statuses
    ok_checks = [c for c in series.realism_checks if c.status == "OK"]
    warning_checks = [c for c in series.realism_checks if c.status == "WARNING"]
    critical_checks = [c for c in series.realism_checks if c.status == "CRITICAL"]

    total = len(series.realism_checks)
    passing = len(ok_checks)

    print(f"MLB REALISM SCORE: {passing}/{total} metrics passing")
    print(f"  ✓ OK: {passing}")
    print(f"  ⚠️ Warnings: {len(warning_checks)}")
    print(f"  🚨 Critical: {len(critical_checks)}")
    print()

    if passing >= 8:
        print("✓✓✓ SUCCESS! Pass 2 achieved target of 8-10/10 metrics passing!")
    elif passing >= 6:
        print("⚠️ PARTIAL SUCCESS: Significant improvement but below 8/10 target")
    else:
        print("🚨 NEEDS MORE WORK: Below 6/10 passing")

    print()
    print("=" * 80)
    print("TEST COMPLETE")
    print("=" * 80)

if __name__ == "__main__":
    main()
