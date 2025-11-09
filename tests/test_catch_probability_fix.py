#!/usr/bin/env python3
"""
Test to verify that catch probability is realistic for fielders arriving late.

This tests the fix for the bug where fielders with negative time margins
(arriving after the ball) had unrealistically high catch probabilities.
"""

import sys
sys.path.insert(0, '/home/user/baseball')

from batted_ball.fielding import Fielder
from batted_ball.field_layout import FieldPosition
from batted_ball.attributes import create_average_fielder

# Create an average fielder
attributes = create_average_fielder()
fielder = Fielder(
    name="Test Fielder",
    position="left_field",
    attributes=attributes,
    current_position=FieldPosition(0, 0, 0)
)

print("Testing catch probability for different time margins:")
print("=" * 60)

test_cases = [
    (0.5, "Fielder arrives 0.5s early (routine)"),
    (0.0, "Fielder arrives exactly on time (routine)"),
    (-0.05, "Fielder 0.05s late (diving catch possible)"),
    (-0.10, "Fielder 0.10s late (difficult diving catch)"),
    (-0.21, "Fielder 0.21s late (YOUR CASE - should be low!)"),
    (-0.30, "Fielder 0.30s late (extremely difficult)"),
    (-0.50, "Fielder 0.50s late (nearly impossible)"),
    (-0.70, "Fielder 0.70s late (ball rolled away)"),
]

ball_position = FieldPosition(100, 250, 0)  # Typical outfield position

for time_margin, description in test_cases:
    # Calculate ball arrival time based on margin
    # time_margin = ball_arrival_time - fielder_time
    # If fielder takes 3.0s and margin is -0.21, then ball arrives at 2.79s
    fielder_time = 3.0
    ball_arrival_time = fielder_time + time_margin

    # Calculate catch probability
    catch_prob = fielder.calculate_catch_probability(ball_position, ball_arrival_time)

    print(f"\nMargin: {time_margin:+.2f}s - {description}")
    print(f"  Catch probability: {catch_prob:.1%}")

    # Highlight the critical case
    if time_margin == -0.21:
        print(f"  👉 THIS WAS THE BUG! Should be LOW (< 35%), not HIGH (> 70%)")
        if catch_prob < 0.35:
            print(f"  ✅ FIXED! Probability is now realistic.")
        else:
            print(f"  ❌ STILL BROKEN! Probability is too high.")

print("\n" + "=" * 60)
print("Expected behavior:")
print("  • Margin ≥ 0.0s: 90%+ (routine catches)")
print("  • Margin -0.15 to 0.0s: 60-70% (diving catches)")
print("  • Margin -0.35 to -0.15s: 25-35% (spectacular plays)")
print("  • Margin < -0.35s: < 10% (nearly impossible)")
