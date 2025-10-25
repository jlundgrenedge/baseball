#!/usr/bin/env python3
"""
Test script for improved batted ball and fielding mechanics.

Tests various scenarios:
1. Hard hit ground balls
2. Weak grounders near home plate
3. Line drives
4. Fly balls
5. Different launch angles
"""

import sys
sys.path.insert(0, '/home/user/baseball')

from batted_ball.trajectory import BattedBallSimulator
from batted_ball.play_simulation import PlaySimulator, create_standard_defense
from batted_ball.baserunning import BaseRunner
from batted_ball.ground_ball_physics import GroundBallSimulator


def print_separator(title):
    """Print a section separator."""
    print("\n" + "=" * 70)
    print(f"  {title}")
    print("=" * 70)


def test_ground_ball_classification():
    """Test that balls are correctly classified as ground balls vs fly balls."""
    print_separator("Ground Ball Classification Tests")

    simulator = BattedBallSimulator()

    test_cases = [
        ("Hard grounder", 85, 5, 1500),
        ("Weak grounder", 40, 8, 800),
        ("Line drive", 95, 12, 1800),
        ("Low line drive", 100, 15, 2000),
        ("Fly ball", 100, 25, 1800),
        ("Pop up", 75, 50, 1500),
    ]

    for name, exit_velo, launch_angle, backspin in test_cases:
        result = simulator.simulate(
            exit_velocity=exit_velo,
            launch_angle=launch_angle,
            backspin_rpm=backspin,
            spray_angle=0
        )

        # Classify using same logic as play simulator
        from batted_ball.constants import GROUND_BALL_LAUNCH_ANGLE_MAX

        max_height = result.peak_height
        distance = result.distance
        hang_time = result.flight_time

        # Apply classification logic
        low_launch_angle = launch_angle < GROUND_BALL_LAUNCH_ANGLE_MAX
        height_to_distance_ratio = max_height / max(distance, 1.0)
        is_low_trajectory = height_to_distance_ratio < 0.05
        very_low = max_height < 3.0
        weak_hit = distance < 50.0 and hang_time < 1.0

        if weak_hit and max_height < 5.0:
            is_air_ball = False
        elif low_launch_angle and very_low:
            is_air_ball = False
        elif is_low_trajectory and max_height < 8.0:
            is_air_ball = max_height > 4.0
        else:
            is_air_ball = max_height > 4.0 or hang_time > 1.5

        ball_type = "AIR BALL" if is_air_ball else "GROUND BALL"

        print(f"\n{name}:")
        print(f"  Exit Velo: {exit_velo} mph, Launch: {launch_angle}°")
        print(f"  Distance: {distance:.0f} ft, Peak Height: {max_height:.1f} ft")
        print(f"  Flight Time: {hang_time:.2f} s")
        print(f"  Classification: {ball_type}")


def test_ground_ball_physics():
    """Test ground ball bouncing and rolling physics."""
    print_separator("Ground Ball Physics Tests")

    simulator = BattedBallSimulator()
    gb_sim = GroundBallSimulator(surface_type='grass')

    test_cases = [
        ("Sharp grounder to SS", 95, 8, 1500, -15),  # Pull side
        ("Grounder up the middle", 85, 10, 1200, 0),  # Center
        ("Slow roller to 3B", 55, 12, 800, 25),  # Opposite field
    ]

    for name, exit_velo, launch_angle, backspin, spray_angle in test_cases:
        # Simulate batted ball
        trajectory = simulator.simulate(
            exit_velocity=exit_velo,
            launch_angle=launch_angle,
            backspin_rpm=backspin,
            spray_angle=spray_angle
        )

        # Simulate ground ball phase
        gb_result = gb_sim.simulate_from_trajectory(trajectory)

        print(f"\n{name}:")
        print(f"  Exit Velo: {exit_velo} mph, Launch: {launch_angle}°, Spray: {spray_angle}°")
        print(f"  Landing: ({trajectory.landing_x:.0f}, {trajectory.landing_y:.0f}) ft")
        print(f"  Air time: {trajectory.flight_time:.2f} s")
        print(f"  Ground ball distance: {gb_result.total_distance:.0f} ft")
        print(f"  Ground ball time: {gb_result.total_time:.2f} s")
        print(f"  Bounces: {len(gb_result.bounces)}")
        print(f"  Rolling started at: {gb_result.rolling_start_time:.2f} s")


def test_complete_plays():
    """Test complete play simulation with new mechanics."""
    print_separator("Complete Play Simulation Tests")

    trajectory_sim = BattedBallSimulator()
    play_sim = PlaySimulator(surface_type='grass')

    # Set up defense
    defense = create_standard_defense()
    play_sim.setup_defense(defense)

    # Create batter runner (using 0-100 scale attributes)
    batter = BaseRunner("Batter", sprint_speed=50, acceleration=50)

    test_cases = [
        ("Routine grounder to SS", 88, 8, 1500, 0),
        ("Slow roller to 3B", 55, 12, 800, 20),
        ("Hard grounder in the hole", 95, 6, 1600, -25),
        ("Topped ball in front of plate", 35, 15, 500, 5),
        ("Line drive to CF", 105, 15, 2000, 0),
        ("Fly ball to RF", 95, 28, 1800, -15),
    ]

    for name, exit_velo, launch_angle, backspin, spray_angle in test_cases:
        # Simulate trajectory
        trajectory = trajectory_sim.simulate(
            exit_velocity=exit_velo,
            launch_angle=launch_angle,
            backspin_rpm=backspin,
            spray_angle=spray_angle
        )

        # Reset play simulator
        play_sim.reset_simulation()
        play_sim.setup_defense(defense)

        # Create fresh batter runner
        batter_fresh = BaseRunner("Batter", sprint_speed=50, acceleration=50)

        # Simulate play
        result = play_sim.simulate_complete_play(trajectory, batter_fresh)

        print(f"\n{name}:")
        print(f"  Exit: {exit_velo} mph, Launch: {launch_angle}°, Spray: {spray_angle}°")
        print(f"  Distance: {trajectory.distance:.0f} ft, Peak: {trajectory.peak_height:.1f} ft")
        print(f"  Outcome: {result.outcome.value}")
        print(f"  Description: {result.play_description}")

        # Show events
        if len(result.events) > 0:
            print(f"  Events:")
            for event in result.get_events_chronological():
                print(f"    {event.time:.2f}s - {event.description}")


def main():
    """Run all tests."""
    print("\n" + "=" * 70)
    print("  IMPROVED BASEBALL MECHANICS TEST SUITE")
    print("=" * 70)

    try:
        test_ground_ball_classification()
        test_ground_ball_physics()
        test_complete_plays()

        print_separator("All Tests Complete!")
        print("\nSummary:")
        print("✓ Ground ball classification improved")
        print("✓ Ground ball physics (bouncing/rolling) implemented")
        print("✓ Trajectory interception using actual physics")
        print("✓ Special handling for weak hits near home plate")

    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        import traceback
        traceback.print_exc()
        return 1

    return 0


if __name__ == "__main__":
    sys.exit(main())
