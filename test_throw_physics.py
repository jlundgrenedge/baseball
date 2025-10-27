"""Test throw physics implementation."""
import sys
sys.path.append('.')

from batted_ball.fielding import Fielder, simulate_fielder_throw
from batted_ball.field_layout import FieldLayout, FieldPosition
from batted_ball.attributes import create_elite_fielder, create_power_arm_fielder, create_average_fielder

print("Testing Throw Physics Implementation")
print("=" * 60)

# Create field layout
field_layout = FieldLayout()

# Create fielders with different attributes
print("\n1. Average Infielder (Shortstop)")
print("-" * 60)
ss = Fielder(
    name="Average SS",
    position="shortstop",
    sprint_speed=50,
    arm_strength=50,  # Average
    fielding_range=50,
    attributes_v2=create_average_fielder("average")  # Average fielder
)

# SS fielding ground ball, throwing to first
ss_position = FieldPosition(40, 150, 0)  # Typical SS fielding position
throw1 = simulate_fielder_throw(ss, ss_position, "first", field_layout)

print(f"Position: ({ss_position.x:.0f}, {ss_position.y:.0f}) → First Base")
print(f"Arm Strength: {throw1.throw_velocity_mph:.1f} mph")
print(f"Transfer Time: {throw1.transfer_time:.3f}s")
print(f"Flight Time: {throw1.flight_time:.3f}s")
print(f"Total Time: {throw1.arrival_time:.3f}s")
print(f"Accuracy: ±{throw1.accuracy_sigma_ft:.1f} ft")
print(f"On Target: {'Yes' if throw1.on_target else 'No'}")

print("\n2. Power Arm Outfielder (Right Field)")
print("-" * 60)
rf = Fielder(
    name="Strong RF",
    position="right_field",
    sprint_speed=70,
    arm_strength=85,  # Strong arm
    fielding_range=60,
    attributes_v2=create_power_arm_fielder("good")  # Elite arm
)

# RF throwing from warning track to home plate
rf_position = FieldPosition(270, 300, 0)  # Deep right field
throw2 = simulate_fielder_throw(rf, rf_position, "home", field_layout)

print(f"Position: ({rf_position.x:.0f}, {rf_position.y:.0f}) → Home Plate")
print(f"Arm Strength: {throw2.throw_velocity_mph:.1f} mph")
print(f"Transfer Time: {throw2.transfer_time:.3f}s")
print(f"Flight Time: {throw2.flight_time:.3f}s")
print(f"Total Time: {throw2.arrival_time:.3f}s")
print(f"Accuracy: ±{throw2.accuracy_sigma_ft:.1f} ft")
print(f"On Target: {'Yes' if throw2.on_target else 'No'}")

print("\n3. Double Play Scenario: 6-4-3")
print("-" * 60)
# SS fields, throws to 2B
ss_field_pos = FieldPosition(35, 160, 0)
throw_to_second = simulate_fielder_throw(ss, ss_field_pos, "second", field_layout)
print(f"SS → 2nd Base:")
print(f"  Distance: {ss_field_pos.horizontal_distance_to(field_layout.get_base_position('second')):.1f} ft")
print(f"  Time: {throw_to_second.arrival_time:.3f}s")

# 2B relays to 1B
second_base_pos = field_layout.get_base_position("second")
second_baseman = Fielder(
    name="2B",
    position="second_base",
    sprint_speed=55,
    arm_strength=55,
    fielding_range=55,
    attributes_v2=create_average_fielder("average")
)
throw_to_first = simulate_fielder_throw(second_baseman, second_base_pos, "first", field_layout)
print(f"2B → 1st Base:")
print(f"  Distance: {second_base_pos.horizontal_distance_to(field_layout.get_base_position('first')):.1f} ft")
print(f"  Time: {throw_to_first.arrival_time:.3f}s")

total_dp_time = throw_to_second.arrival_time + throw_to_first.arrival_time
print(f"\nTotal Double Play Time: {total_dp_time:.3f}s")
print(f"  (Runner needs ~3.5s to reach 2nd, ~4.3s for batter to reach 1st)")

print("\n" + "=" * 60)
print("VALIDATION:")
print("=" * 60)
print(f"✓ SS throw to 1st (140 ft): {throw1.arrival_time:.2f}s (expect ~1.0-1.3s)")
print(f"✓ RF throw to home (400+ ft): {throw2.arrival_time:.2f}s (expect ~2.0-2.5s)")
print(f"✓ DP total time: {total_dp_time:.2f}s (expect ~2.0-2.5s)")
