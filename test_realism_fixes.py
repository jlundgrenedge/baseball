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
        series.add_game(result)

        print(f" {result.away_score}-{result.home_score}")

    print()
    print("=" * 80)
    print("SERIES STATISTICS")
    print("=" * 80)
    print()

    # Print comprehensive summary
    print(series.get_summary_report())

    print()
    print("=" * 80)
    print("KEY METRICS COMPARISON")
    print("=" * 80)
    print()

    # Get MLB realism benchmarks
    benchmarks = series.get_mlb_realism_benchmarks()

    passing = 0
    warning = 0
    failing = 0

    for metric_name, (value, status, expected_range) in benchmarks.items():
        if status == '✓':
            passing += 1
        elif status == '⚠️':
            warning += 1
        else:
            failing += 1

    total = passing + warning + failing
    print(f"OVERALL RESULTS: {passing}/{total} metrics passing")
    print(f"  ✓ Passing: {passing}")
    print(f"  ⚠️ Warnings: {warning}")
    print(f"  🚨 Failing: {failing}")
    print()

    # Highlight specific fixes
    print("SPECIFIC FIX VALIDATION:")
    print()

    # Get batting metrics
    combined_batting = series.batting_metrics
    total_balls_in_play = combined_batting.ground_balls + combined_batting.line_drives + combined_batting.fly_balls

    if total_balls_in_play > 0:
        gb_pct = combined_batting.ground_balls / total_balls_in_play
        ld_pct = combined_batting.line_drives / total_balls_in_play
        fb_pct = combined_batting.fly_balls / total_balls_in_play

        print(f"1. Batted Ball Distribution:")
        print(f"   Ground Balls: {gb_pct:.1%} (target: ~45%)")
        print(f"   Line Drives:  {ld_pct:.1%} (target: ~21%)")
        print(f"   Fly Balls:    {fb_pct:.1%} (target: ~34%)")
        print()

    total_pa = combined_batting.plate_appearances
    if total_pa > 0:
        k_rate = combined_batting.strikeouts / total_pa
        bb_rate = combined_batting.walks / total_pa

        print(f"2. Plate Discipline:")
        print(f"   K Rate:  {k_rate:.1%} (target: ~22%)")
        print(f"   BB Rate: {bb_rate:.1%} (target: ~8.5%)")
        print()

    total_batted_balls = combined_batting.batted_balls
    if total_batted_balls > 0:
        hard_hit_rate = combined_batting.hard_hit_balls / total_batted_balls

        print(f"3. Power Metrics:")
        print(f"   Hard Hit Rate: {hard_hit_rate:.1%} (target: ~40%)")
        print(f"   HR/FB Rate: {combined_batting.get_hr_fb_rate():.1%} (target: ~12.5%)")
        print(f"   ISO: {combined_batting.get_iso():.3f} (target: ~0.150)")
        print()

    print("=" * 80)
    print("TEST COMPLETE")
    print("=" * 80)

if __name__ == "__main__":
    main()
