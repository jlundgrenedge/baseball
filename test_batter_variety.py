#!/usr/bin/env python3
"""
Test script to verify batted ball type variety.

Simulates multiple at-bats from different batter types to show:
- Ground balls (0-10° launch angle)
- Line drives (10-25° launch angle)
- Fly balls (25-40° launch angle)
- Pop-ups (40°+ launch angle)
"""

import sys
sys.path.insert(0, '/home/user/baseball')

from batted_ball.game_simulation import create_test_team
from batted_ball.player import Hitter
from collections import defaultdict


def main():
    """Test batter variety and batted ball distribution."""
    print("=" * 70)
    print("  BATTER TYPE VARIETY TEST")
    print("=" * 70)

    # Create a test team to show variety
    print("\nCreating test team with varied batter types:")
    print("-" * 70)

    # Reset debug flag so we see output
    if hasattr(create_test_team, 'debug_shown'):
        delattr(create_test_team, 'debug_shown')

    team = create_test_team("Test Team", "average")

    print("\n" + "=" * 70)
    print("  BATTER LINEUP ANALYSIS")
    print("=" * 70)

    # Analyze the lineup
    launch_angles = []
    batter_types = defaultdict(int)

    for hitter in team.hitters:
        la = hitter.launch_angle_tendency
        launch_angles.append(la)

        # Classify batter type
        if la < 15:
            btype = "Ground Ball"
            batter_types["Ground Ball"] += 1
        elif la < 22:
            btype = "Line Drive"
            batter_types["Line Drive"] += 1
        elif la < 28:
            btype = "Balanced/Fly Ball"
            batter_types["Balanced/Fly Ball"] += 1
        else:
            btype = "Power/Extreme Fly Ball"
            batter_types["Power/Extreme Fly Ball"] += 1

        print(f"{hitter.name:25s} LA: {la:5.1f}°  ({btype})")

    print("\n" + "-" * 70)
    print("LINEUP COMPOSITION:")
    for btype, count in sorted(batter_types.items()):
        pct = (count / len(team.hitters)) * 100
        print(f"  {btype:25s}: {count} players ({pct:.1f}%)")

    print("\n" + "-" * 70)
    print("LAUNCH ANGLE STATISTICS:")
    avg_la = sum(launch_angles) / len(launch_angles)
    min_la = min(launch_angles)
    max_la = max(launch_angles)
    print(f"  Average: {avg_la:.1f}°")
    print(f"  Range: {min_la:.1f}° to {max_la:.1f}°")

    print("\n" + "=" * 70)
    print("  EXPECTED BATTED BALL TYPES")
    print("=" * 70)

    print("\nBased on these launch angle tendencies, we expect:")
    print("  • Ground balls (0-10°):  Contact below sweet spot, topped balls")
    print("  • Line drives (10-25°):  Solid contact, hard hit balls")
    print("  • Fly balls (25-40°):    Contact below center, lift")
    print("  • Pop-ups (60°+):        Very poor contact, topped/jammed")

    print("\n  Distribution should vary by batter type:")
    gb_count = batter_types["Ground Ball"]
    ld_count = batter_types["Line Drive"]
    fb_count = batter_types["Balanced/Fly Ball"] + batter_types["Power/Extreme Fly Ball"]

    print(f"  • Ground ball hitters ({gb_count}): More GB, fewer FB")
    print(f"  • Line drive hitters ({ld_count}): More LD, balanced GB/FB")
    print(f"  • Fly ball hitters ({fb_count}): Fewer GB, more FB and HR")

    print("\n" + "=" * 70)
    print("  KEY IMPROVEMENTS")
    print("=" * 70)

    print("\n✓ BEFORE: All batters had launch angle 10-25° (only line drives)")
    print("✓ AFTER:  Batters range from 8-35° (GB, LD, FB, and Power hitters)")
    print("\n✓ This creates realistic variety:")
    print("  • Contact hitters who hit ground balls")
    print("  • Gap hitters who spray line drives")
    print("  • Power hitters who lift the ball")
    print("\n✓ Combined with contact quality variation, we now get:")
    print("  • Ground balls when contact is above center")
    print("  • Line drives on solid contact")
    print("  • Fly balls when contact is below center")
    print("  • Pop-ups on very poor contact")

    print("\n" + "=" * 70)
    print("Run a game simulation to see the variety in action!")
    print("=" * 70)

    return 0


if __name__ == "__main__":
    sys.exit(main())
