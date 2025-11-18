#!/usr/bin/env python3
"""
Test script to verify the "Bystander Effect" fix in fielder assignment.

This script tests that fielders who can actually catch the ball
are assigned the play, rather than zone-based assignment that might
fail to make the play.
"""

import sys
from batted_ball.fielding import Fielder, FieldingSimulator
from batted_ball.field_layout import FieldLayout, FieldPosition
from batted_ball.attributes import create_average_fielder, create_elite_fielder

def test_fielder_assignment():
    """Test that fielder assignment prioritizes who can actually catch."""

    # Create field layout
    field_layout = FieldLayout()

    # Create fielding simulator
    sim = FieldingSimulator(field_layout)

    # Create fielders with different capabilities
    # First baseman: Elite speed/range (can reach shallow fly balls)
    first_base_attrs = create_elite_fielder("good")
    first_baseman = Fielder("First Baseman", "first_base", first_base_attrs)
    first_baseman.update_position(FieldPosition(63.64, 63.64, 0))  # Standard 1B position

    # Second baseman: Average fielder at standard position
    second_base_attrs = create_average_fielder("average")
    second_baseman = Fielder("Second Baseman", "second_base", second_base_attrs)
    second_baseman.update_position(FieldPosition(45, 120, 0))  # Standard 2B position

    # Shortstop: Average fielder
    ss_attrs = create_average_fielder("average")
    shortstop = Fielder("Shortstop", "shortstop", ss_attrs)
    shortstop.update_position(FieldPosition(-45, 120, 0))  # Standard SS position

    # Third baseman: Average fielder
    third_base_attrs = create_average_fielder("average")
    third_baseman = Fielder("Third Baseman", "third_base", third_base_attrs)
    third_baseman.update_position(FieldPosition(-63.64, 63.64, 0))  # Standard 3B position

    # Add fielders to simulator
    sim.add_fielder("first_base", first_baseman)
    sim.add_fielder("second_base", second_baseman)
    sim.add_fielder("shortstop", shortstop)
    sim.add_fielder("third_base", third_baseman)

    print("Testing Fielder Assignment Logic")
    print("=" * 60)
    print()

    # Test Case 1: Shallow fly ball between 1B and 2B
    # Ball lands at (80, 90) - closer to 2B zone but 1B can reach it faster
    ball_pos = FieldPosition(80, 90, 0)
    ball_arrival_time = 2.5  # Reasonable hang time for shallow fly

    print("Test Case 1: Shallow fly ball between 1B and 2B")
    print(f"  Ball position: ({ball_pos.x:.1f}, {ball_pos.y:.1f})")
    print(f"  Ball arrival time: {ball_arrival_time:.2f}s")
    print()

    # Calculate who can reach it
    for pos_name, fielder in sim.fielders.items():
        try:
            effective_time = fielder.calculate_effective_time_to_position(ball_pos)
            time_margin = ball_arrival_time - effective_time
            can_catch = time_margin >= -0.15
            print(f"  {pos_name:12s}: arrives in {effective_time:.2f}s (margin: {time_margin:+.2f}s) - {'CAN CATCH' if can_catch else 'TOO SLOW'}")
        except:
            print(f"  {pos_name:12s}: ERROR calculating time")

    print()

    # Determine responsible fielder
    assigned_fielder = sim.determine_responsible_fielder(ball_pos, ball_arrival_time)
    print(f"  ✓ ASSIGNED TO: {assigned_fielder}")
    print()

    # Verify the assigned fielder can actually make the play
    assigned = sim.fielders[assigned_fielder]
    assigned_time = assigned.calculate_effective_time_to_position(ball_pos)
    assigned_margin = ball_arrival_time - assigned_time

    if assigned_margin >= -0.15:
        print(f"  ✓ CORRECT: {assigned_fielder} can reach the ball (margin: {assigned_margin:+.2f}s)")
    else:
        print(f"  ✗ ERROR: {assigned_fielder} CANNOT reach the ball (margin: {assigned_margin:+.2f}s)")
        print("  This is the 'Bystander Effect' bug!")
        return False

    print()
    print("=" * 60)
    print("✅ Fielder assignment test PASSED!")
    print("The 'Bystander Effect' bug has been fixed.")
    return True

if __name__ == "__main__":
    success = test_fielder_assignment()
    sys.exit(0 if success else 1)
