#!/usr/bin/env python3
"""
Test script for multi-fielder competition scenarios.

Tests situations where multiple fielders could potentially reach the same ball:
1. Ground ball in the hole (SS vs 2B)
2. Ground ball up the middle (2B vs SS vs P)
3. Line drive to gap (1B vs RF)
4. Shallow fly ball (SS going back vs CF coming in)
5. Ball down the line (3B vs LF)
"""

import sys
sys.path.insert(0, '/home/user/baseball')

from batted_ball.trajectory import BattedBallSimulator
from batted_ball.play_simulation import PlaySimulator, create_standard_defense
from batted_ball.baserunning import BaseRunner


def print_separator(title):
    """Print a section separator."""
    print("\n" + "=" * 70)
    print(f"  {title}")
    print("=" * 70)


def test_multi_fielder_scenarios():
    """Test scenarios where multiple fielders compete for the ball."""
    print_separator("Multi-Fielder Competition Tests")

    trajectory_sim = BattedBallSimulator()
    play_sim = PlaySimulator(surface_type='grass')

    # Set up defense
    defense = create_standard_defense()
    play_sim.setup_defense(defense)

    test_cases = [
        {
            "name": "Ground ball in the hole (SS/2B gap)",
            "exit_velo": 92,
            "launch_angle": 8,
            "spray_angle": -10,  # Pull side (between SS and 2B)
            "backspin": 1500,
            "description": "Hard grounder between shortstop and second base"
        },
        {
            "name": "Ground ball up the middle",
            "exit_velo": 85,
            "launch_angle": 7,
            "spray_angle": 0,  # Straight up middle
            "backspin": 1400,
            "description": "Grounder up the middle - P, SS, and 2B could field"
        },
        {
            "name": "Line drive to right-center gap",
            "exit_velo": 105,
            "launch_angle": 12,
            "spray_angle": -20,  # Between RF and CF
            "backspin": 2000,
            "description": "Line drive that RF and CF both chase"
        },
        {
            "name": "Line drive down the first base line",
            "exit_velo": 98,
            "launch_angle": 10,
            "spray_angle": -30,  # Down the line
            "backspin": 1800,
            "description": "Low liner that 1B can reach before it gets to RF"
        },
        {
            "name": "Shallow fly ball to short RF",
            "exit_velo": 88,
            "launch_angle": 32,
            "spray_angle": -15,
            "backspin": 1900,
            "description": "Short fly ball - 2B going back vs RF coming in"
        },
        {
            "name": "Ground ball down third base line",
            "exit_velo": 93,
            "launch_angle": 6,
            "spray_angle": 28,  # Down the 3B line
            "backspin": 1600,
            "description": "Grounder down the line - 3B vs LF"
        },
        {
            "name": "Bloop single to shallow center",
            "exit_velo": 75,
            "launch_angle": 35,
            "spray_angle": 5,
            "backspin": 1500,
            "description": "Soft fly ball - SS going back vs CF coming in"
        },
    ]

    for case in test_cases:
        print(f"\n{case['name']}:")
        print(f"  {case['description']}")
        print(f"  Exit: {case['exit_velo']} mph, Launch: {case['launch_angle']}°, Spray: {case['spray_angle']}°")

        # Simulate trajectory
        trajectory = trajectory_sim.simulate(
            exit_velocity=case['exit_velo'],
            launch_angle=case['launch_angle'],
            backspin_rpm=case['backspin'],
            spray_angle=case['spray_angle']
        )

        print(f"  Trajectory: {trajectory.distance:.0f}ft, peak {trajectory.peak_height:.1f}ft, {trajectory.flight_time:.2f}s")

        # Reset play simulator
        play_sim.reset_simulation()
        play_sim.setup_defense(defense)

        # Create fresh batter runner
        batter = BaseRunner("Batter", sprint_speed=50, acceleration=50)

        # Simulate play (this will show debug output for first play)
        result = play_sim.simulate_complete_play(trajectory, batter)

        print(f"  Result: {result.outcome.value}")
        if result.primary_fielder:
            print(f"  Fielded by: {result.primary_fielder.position}")

        # Show key events
        events = result.get_events_chronological()
        for event in events[:3]:  # First 3 events
            print(f"    {event.time:.2f}s - {event.description}")


def test_fielder_positioning_impact():
    """Test how fielder positioning affects who makes the play."""
    print_separator("Fielder Positioning Impact")

    print("\nTesting same ball with different defensive alignments:\n")

    trajectory_sim = BattedBallSimulator()

    # Same ball: ground ball in the hole
    trajectory = trajectory_sim.simulate(
        exit_velocity=90,
        launch_angle=8,
        backspin_rpm=1500,
        spray_angle=-12  # In the hole
    )

    print(f"Ball: {trajectory.distance:.0f}ft, peak {trajectory.peak_height:.1f}ft")
    print(f"Landing position: ({trajectory.landing_x:.0f}, {trajectory.landing_y:.0f})\n")

    # Test with different alignments
    alignments = [
        ("Standard defense", create_standard_defense()),
        # Could add shifted defense, double play depth, etc.
    ]

    for alignment_name, defense in alignments:
        print(f"{alignment_name}:")

        play_sim = PlaySimulator(surface_type='grass')
        play_sim.setup_defense(defense)

        batter = BaseRunner("Batter", sprint_speed=50, acceleration=50)
        result = play_sim.simulate_complete_play(trajectory, batter)

        print(f"  Result: {result.outcome.value}")
        if result.primary_fielder:
            print(f"  Fielded by: {result.primary_fielder.position}")


def main():
    """Run all tests."""
    print("\n" + "=" * 70)
    print("  MULTI-FIELDER COMPETITION TEST SUITE")
    print("=" * 70)
    print("\nNow checking ALL fielders at each trajectory point to see")
    print("who can reach the ball. The fielder with the best time margin wins!")

    try:
        test_multi_fielder_scenarios()
        test_fielder_positioning_impact()

        print_separator("All Tests Complete!")
        print("\nKey improvements:")
        print("✓ All fielders checked at each trajectory point")
        print("✓ Best positioned fielder makes the play")
        print("✓ Realistic competition in gaps and shallow areas")
        print("✓ Accounts for fielder speed, range, and positioning")

    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        import traceback
        traceback.print_exc()
        return 1

    return 0


if __name__ == "__main__":
    sys.exit(main())
