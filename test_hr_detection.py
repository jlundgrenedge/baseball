"""Test home run detection directly."""
import sys
sys.path.append('.')

from batted_ball import BattedBallSimulator, create_standard_environment
import numpy as np

# Create simulator
sim = BattedBallSimulator()

print("Testing Home Run Detection")
print("=" * 60)

# Test several potential home run scenarios
test_cases = [
    ("Routine HR", 105, 28, 0, 2200),
    ("Line drive HR", 108, 22, 0, 1800),
    ("Pull side HR", 102, 30, 25, 2400),
    ("Barely over", 98, 26, 0, 2000),
    ("Deep fly", 95, 32, 0, 2300),
]

for name, exit_v, launch_a, spray_a, backspin in test_cases:
    result = sim.simulate(
        exit_velocity=exit_v,
        launch_angle=launch_a,
        spray_angle=spray_a,
        backspin_rpm=backspin
    )
    
    distance = result.distance
    peak = result.peak_height
    
    # Check if it would be HR by our logic
    if spray_a == 0:
        fence = 400
    elif abs(spray_a) < 25:
        fence = 380
    else:
        fence = 360
    
    is_hr_by_distance = distance >= fence - 5
    is_hr_by_height = peak >= 30
    is_hr = is_hr_by_distance and is_hr_by_height
    
    print(f"\n{name}:")
    print(f"  Exit: {exit_v} mph, Launch: {launch_a}°, Spray: {spray_a}°")
    print(f"  Distance: {distance:.1f} ft (fence: {fence} ft)")
    print(f"  Peak height: {peak:.1f} ft")
    print(f"  Would be HR: {is_hr} (dist: {is_hr_by_distance}, height: {is_hr_by_height})")
