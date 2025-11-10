"""
Simple test script for relay throw mechanics (no pytest required).

Tests that verify:
1. Relay throws are triggered for distances > 200 feet
2. Appropriate cut-off men are selected
3. Two-stage throw timing is calculated correctly
"""

import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from batted_ball import (
    FieldLayout, FieldPosition,
    Fielder, create_average_fielder, create_elite_fielder,
    simulate_relay_throw, determine_cutoff_man,
    RELAY_THROW_THRESHOLD
)
from batted_ball.attributes import FielderAttributes


def test_cutoff_man_selection():
    """Test that appropriate cut-off men are selected."""
    print("\n=== Testing Cut-off Man Selection ===")

    # Left field to home
    cutoff = determine_cutoff_man('left_field', 'home')
    assert cutoff == 'shortstop', f"LF to home should use SS, got {cutoff}"
    print("✓ Left field to home uses shortstop")

    # Center field to home
    cutoff = determine_cutoff_man('center_field', 'home')
    assert cutoff == 'shortstop', f"CF to home should use SS, got {cutoff}"
    print("✓ Center field to home uses shortstop")

    # Right field to home
    cutoff = determine_cutoff_man('right_field', 'home')
    assert cutoff == 'second_base', f"RF to home should use 2B, got {cutoff}"
    print("✓ Right field to home uses second baseman")

    # Any outfield to third
    for of in ['left_field', 'center_field', 'right_field']:
        cutoff = determine_cutoff_man(of, 'third')
        assert cutoff == 'shortstop', f"{of} to third should use SS, got {cutoff}"
    print("✓ All outfielders to third use shortstop")

    print("✅ All cutoff man selection tests passed!")


def test_relay_threshold():
    """Test that relay throws are triggered based on distance."""
    print("\n=== Testing Relay Distance Threshold ===")

    field_layout = FieldLayout()
    center_fielder = create_average_fielder("Test CF", "center_field")
    shortstop = create_average_fielder("Test SS", "shortstop")

    # Short throw (should NOT relay) - position within 200 ft of home
    shallow_position = FieldPosition(0, 180, 0)
    home_pos = field_layout.get_base_position('home')
    distance = shallow_position.horizontal_distance_to(home_pos)
    print(f"Shallow CF position: {distance:.1f} ft from home")

    result = simulate_relay_throw(
        center_fielder, shortstop, shallow_position, 'home', field_layout
    )

    assert not result.is_relay, f"Short throw ({distance:.1f} ft) should not use relay"
    print(f"✓ Short throw ({distance:.1f} ft) does NOT use relay")

    # Deep throw (should relay)
    deep_position = FieldPosition(0, 380, 0)
    distance = deep_position.horizontal_distance_to(home_pos)
    print(f"Deep CF position: {distance:.1f} ft from home")

    result = simulate_relay_throw(
        center_fielder, shortstop, deep_position, 'home', field_layout
    )

    assert result.is_relay, "Deep throw should use relay"
    assert result.cutoff_position == "shortstop"
    print(f"✓ Deep throw ({distance:.1f} ft) USES relay via {result.cutoff_position}")

    # Force relay
    force_relay_position = FieldPosition(0, 180, 0)
    result = simulate_relay_throw(
        center_fielder, shortstop, force_relay_position, 'home', field_layout,
        force_relay=True
    )
    assert result.is_relay, "Force relay should trigger relay"
    print("✓ Force relay flag works")

    print("✅ All relay threshold tests passed!")


def test_relay_timing():
    """Test that relay throw timing is calculated correctly."""
    print("\n=== Testing Relay Throw Timing ===")

    field_layout = FieldLayout()

    # Create fielders with specific attributes (using 0-100,000 scale)
    cf_attrs = FielderAttributes(
        TOP_SPRINT_SPEED=75000,
        ARM_STRENGTH=70000,
        REACTION_TIME=60000,
        ROUTE_EFFICIENCY=65000,
        TRANSFER_TIME=55000,
        ARM_ACCURACY=60000,
        AGILITY=65000
    )
    center_fielder = Fielder("Test CF", "center_field", cf_attrs)

    ss_attrs = FielderAttributes(
        TOP_SPRINT_SPEED=70000,
        ARM_STRENGTH=75000,
        REACTION_TIME=65000,
        ROUTE_EFFICIENCY=70000,
        TRANSFER_TIME=70000,
        ARM_ACCURACY=70000,
        AGILITY=70000
    )
    shortstop = Fielder("Test SS", "shortstop", ss_attrs)

    deep_position = FieldPosition(0, 380, 0)

    result = simulate_relay_throw(
        center_fielder, shortstop, deep_position, 'home', field_layout
    )

    assert result.is_relay
    print(f"CF arm strength: {cf_attrs.get_arm_strength_mph():.1f} mph")
    print(f"SS arm strength: {ss_attrs.get_arm_strength_mph():.1f} mph")
    print(f"First throw time: {result.first_throw.arrival_time:.2f}s")
    print(f"Relay handling: {result.relay_handling_time:.2f}s")
    print(f"Second throw time: {result.second_throw.arrival_time:.2f}s")
    print(f"Total relay time: {result.total_arrival_time:.2f}s")

    # Verify structure
    assert result.first_throw is not None
    assert result.second_throw is not None
    assert 0.2 <= result.relay_handling_time <= 0.4, \
        f"Relay handling should be 0.2-0.4s, got {result.relay_handling_time:.2f}s"

    # Verify total time calculation
    expected_time = (
        result.first_throw.arrival_time +
        result.relay_handling_time +
        result.second_throw.arrival_time
    )
    assert abs(result.total_arrival_time - expected_time) < 0.01

    print("✓ Relay timing structure is correct")
    print("✅ All timing tests passed!")


def test_realistic_scenarios():
    """Test realistic relay throw scenarios."""
    print("\n=== Testing Realistic Relay Scenarios ===")

    field_layout = FieldLayout()

    # Deep left field to home
    lf = create_average_fielder("LF", "left_field")
    ss = create_average_fielder("SS", "shortstop")
    deep_lf = FieldPosition(-220, 270, 0)
    home_pos = field_layout.get_base_position('home')
    distance = deep_lf.horizontal_distance_to(home_pos)

    result = simulate_relay_throw(lf, ss, deep_lf, 'home', field_layout)

    print(f"\nDeep LF to home ({distance:.1f} ft):")
    print(f"  Uses relay: {result.is_relay}")
    print(f"  Cutoff man: {result.cutoff_position}")
    print(f"  Total time: {result.total_arrival_time:.2f}s")

    assert result.is_relay
    assert result.cutoff_position == 'shortstop'
    assert 2.5 <= result.total_arrival_time <= 5.0, \
        f"Should take 2.5-5.0s, got {result.total_arrival_time:.2f}s"

    # Deep right field to third
    rf = create_average_fielder("RF", "right_field")
    deep_rf = FieldPosition(220, 260, 0)
    third_pos = field_layout.get_base_position('third')
    distance = deep_rf.horizontal_distance_to(third_pos)

    result = simulate_relay_throw(rf, ss, deep_rf, 'third', field_layout)

    print(f"\nDeep RF to third ({distance:.1f} ft):")
    print(f"  Uses relay: {result.is_relay}")
    print(f"  Cutoff man: {result.cutoff_position}")
    print(f"  Total time: {result.total_arrival_time:.2f}s")

    assert result.is_relay
    assert result.cutoff_position == 'shortstop'
    assert 2.5 <= result.total_arrival_time <= 5.0

    print("\n✅ All realistic scenario tests passed!")


def test_threshold_value():
    """Verify the relay threshold is 200 feet as specified."""
    print("\n=== Testing Relay Threshold Value ===")
    print(f"RELAY_THROW_THRESHOLD = {RELAY_THROW_THRESHOLD:.1f} feet")
    assert RELAY_THROW_THRESHOLD == 200.0, "Threshold should be 200 feet"
    print("✅ Threshold value is correct!")


def main():
    """Run all tests."""
    print("=" * 60)
    print("RELAY THROW MECHANICS TEST SUITE")
    print("=" * 60)

    try:
        test_threshold_value()
        test_cutoff_man_selection()
        test_relay_threshold()
        test_relay_timing()
        test_realistic_scenarios()

        print("\n" + "=" * 60)
        print("✅ ALL TESTS PASSED!")
        print("=" * 60)
        return 0

    except AssertionError as e:
        print("\n" + "=" * 60)
        print(f"❌ TEST FAILED: {e}")
        print("=" * 60)
        return 1
    except Exception as e:
        print("\n" + "=" * 60)
        print(f"❌ ERROR: {e}")
        import traceback
        traceback.print_exc()
        print("=" * 60)
        return 1


if __name__ == "__main__":
    exit(main())
