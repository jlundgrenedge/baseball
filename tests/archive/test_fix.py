#!/usr/bin/env python3
"""Quick test to verify ground ball rate and exit velocity fixes."""

import sys
import numpy as np
from batted_ball.game_simulation import create_test_team, GameSimulator

def main():
    print("Testing ground ball rate and exit velocity fixes...")
    print("="*80)

    # Create two average teams
    home = create_test_team("Cubs", "average")
    away = create_test_team("Brewers", "average")

    print("\n--- Team Created ---")
    print(f"Sample hitter attributes:")
    for i, hitter in enumerate(home.hitters[:3]):
        bat_speed = hitter.attributes.get_bat_speed_mph()
        attack_angle = hitter.attributes.get_attack_angle_mean_deg()
        print(f"  Hitter {i+1}: Bat speed: {bat_speed:.1f} mph, Attack angle: {attack_angle:.1f}°")

    print(f"\n--- Running 3 games to test statistics ---")

    all_launch_angles = []
    all_exit_velos = []
    ground_balls = 0
    line_drives = 0
    fly_balls = 0
    total_batted_balls = 0
    total_doubles = 0
    total_triples = 0
    total_home_runs = 0

    for game_num in range(1, 4):
        print(f"\n--- Game {game_num} ---")
        sim = GameSimulator(away, home, verbose=False)
        result = sim.simulate_game(num_innings=9)

        print(f"Final Score: {away.name} {result.away_score} - {home.name} {result.home_score}")

        # Collect statistics from play-by-play
        for event in sim.play_by_play:
            physics = event.physics_data

            # Debug: Check what's in physics_data
            if game_num == 1 and total_batted_balls < 3:
                print(f"  Event: {event.outcome}, Physics keys: {physics.keys() if physics else 'None'}")

            if physics and 'launch_angle_deg' in physics and 'exit_velocity_mph' in physics:
                la = physics['launch_angle_deg']
                ev = physics['exit_velocity_mph']

                all_launch_angles.append(la)
                all_exit_velos.append(ev)
                total_batted_balls += 1

                # Classify by launch angle
                if la < 10:
                    ground_balls += 1
                elif la < 25:
                    line_drives += 1
                else:
                    fly_balls += 1

            # Track extra-base hits
            if event.outcome == 'double':
                total_doubles += 1
            elif event.outcome == 'triple':
                total_triples += 1
            elif event.outcome == 'home_run':
                total_home_runs += 1

    print("\n" + "="*80)
    print("AGGREGATE STATISTICS (3 games):")
    print("="*80)

    if total_batted_balls > 0:
        avg_la = np.mean(all_launch_angles)
        avg_ev = np.mean(all_exit_velos)
        gb_pct = (ground_balls / total_batted_balls) * 100
        ld_pct = (line_drives / total_batted_balls) * 100
        fb_pct = (fly_balls / total_batted_balls) * 100

        print(f"\nBatted Ball Distribution:")
        print(f"  Total batted balls: {total_batted_balls}")
        print(f"  Ground balls: {ground_balls} ({gb_pct:.1f}%)")
        print(f"  Line drives: {line_drives} ({ld_pct:.1f}%)")
        print(f"  Fly balls: {fly_balls} ({fb_pct:.1f}%)")

        print(f"\nAverages:")
        print(f"  Launch angle: {avg_la:.1f}° (MLB avg: ~12-13°)")
        print(f"  Exit velocity: {avg_ev:.1f} mph (MLB avg: ~88-89 mph)")

        print(f"\nExtra-Base Hits:")
        print(f"  Doubles: {total_doubles}")
        print(f"  Triples: {total_triples}")
        print(f"  Home runs: {total_home_runs}")

        print("\n" + "="*80)
        print("EXPECTED MLB RANGES:")
        print("="*80)
        print("  Ground ball rate: 43-45%")
        print("  Line drive rate: 20-24%")
        print("  Fly ball rate: 33-38%")
        print("  Launch angle: 12-13°")
        print("  Exit velocity: 88-89 mph")
        print("="*80)

        # Check if within reasonable ranges
        success = True
        if gb_pct < 35 or gb_pct > 55:
            print(f"\n⚠ WARNING: Ground ball rate ({gb_pct:.1f}%) outside expected range (35-55%)")
            success = False
        if avg_la < 8 or avg_la > 18:
            print(f"\n⚠ WARNING: Launch angle ({avg_la:.1f}°) outside expected range (8-18°)")
            success = False
        if avg_ev < 75 or avg_ev > 95:
            print(f"\n⚠ WARNING: Exit velocity ({avg_ev:.1f} mph) outside expected range (75-95 mph)")
            success = False
        if total_home_runs == 0 and total_batted_balls > 100:
            print(f"\n⚠ WARNING: No home runs in {total_batted_balls} batted balls (expected ~1-3)")
            success = False

        if success:
            print("\n✓ All statistics within realistic ranges!")

    else:
        print("\nNo batted ball data collected!")
        return 1

    return 0

if __name__ == "__main__":
    sys.exit(main())
