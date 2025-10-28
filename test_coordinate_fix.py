"""
Test coordinate system fixes for ground ball fielding.

This test verifies that:
1. Ground balls travel in the correct direction
2. Fielders move realistic distances (not 100+ feet)
3. Coordinate conversions are applied correctly throughout
"""

import sys
import numpy as np
from batted_ball.trajectory import BattedBallSimulator
from batted_ball.environment import create_standard_environment
from batted_ball.field_layout import create_standard_field, FieldPosition
from batted_ball.fielding import Fielder, create_average_fielder
from batted_ball.ground_ball_interception import GroundBallInterceptor


def test_ground_ball_up_middle():
    """Test ground ball straight up the middle."""
    print("\n" + "="*70)
    print("TEST 1: Ground ball up the middle")
    print("="*70)

    # Create simulator
    simulator = BattedBallSimulator()

    # Simulate ground ball up the middle
    # Launch angle ~5 degrees, spray angle 0 (straight center field)
    result = simulator.simulate(
        exit_velocity=75.0,  # mph
        launch_angle=5.0,    # degrees (low, ground ball)
        spray_angle=0.0,     # degrees (straight center)
        backspin_rpm=500,
        sidespin_rpm=0
    )

    print(f"\nBall landing position (field coords):")
    print(f"  X = {result.landing_x:.1f} ft (lateral, 0 = center)")
    print(f"  Y = {result.landing_y:.1f} ft (forward, toward CF)")
    print(f"  Distance from home: {result.distance:.1f} ft")

    # Create fielders
    field = create_standard_field()
    pitcher = create_average_fielder("Pitcher", "infield")
    pitcher.current_position = FieldPosition(0.0, 60.5, 0.0)  # Pitcher's mound

    fielders = {'pitcher': pitcher}

    # Test interception
    interceptor = GroundBallInterceptor('grass')
    interception = interceptor.find_best_interception(result, fielders)

    if interception.can_be_fielded:
        print(f"\nFielder movement:")
        print(f"  Fielder: {interception.fielding_position}")
        print(f"  From: ({pitcher.current_position.x:.1f}, {pitcher.current_position.y:.1f})")
        print(f"  To: ({interception.ball_position_at_interception.x:.1f}, {interception.ball_position_at_interception.y:.1f})")

        dx = interception.ball_position_at_interception.x - pitcher.current_position.x
        dy = interception.ball_position_at_interception.y - pitcher.current_position.y
        distance = np.sqrt(dx**2 + dy**2)

        print(f"  Distance traveled: {distance:.1f} ft")
        print(f"  Direction: ΔX={dx:.1f} ft, ΔY={dy:.1f} ft")

        # Validate
        if distance > 50:
            print(f"  ❌ FAIL: Fielder traveled too far ({distance:.1f} ft > 50 ft)")
            return False
        elif abs(dx) > 10 and abs(dy) < 20:
            print(f"  ❌ FAIL: Fielder moved too much laterally ({abs(dx):.1f} ft)")
            return False
        else:
            print(f"  ✓ PASS: Realistic fielder movement")
            return True
    else:
        print("  ❌ FAIL: Ball not fielded")
        return False


def test_ground_ball_to_left():
    """Test ground ball pulled to left field."""
    print("\n" + "="*70)
    print("TEST 2: Ground ball to left field (negative X)")
    print("="*70)

    simulator = BattedBallSimulator()

    # Ground ball pulled to left
    # NOTE: Positive spray angle = left field (pull for RHB)
    result = simulator.simulate(
        exit_velocity=85.0,
        launch_angle=5.0,
        spray_angle=25.0,  # POSITIVE = left field
        backspin_rpm=500,
        sidespin_rpm=0
    )

    print(f"\nBall landing position (field coords):")
    print(f"  X = {result.landing_x:.1f} ft (should be negative for left field)")
    print(f"  Y = {result.landing_y:.1f} ft")
    print(f"  Distance from home: {result.distance:.1f} ft")

    # Validate landing position
    if result.landing_x >= 0:
        print(f"  ❌ FAIL: Left field ball has positive X coordinate")
        return False
    else:
        print(f"  ✓ PASS: Left field ball correctly in negative X region")
        return True


def test_ground_ball_to_right():
    """Test ground ball to right field."""
    print("\n" + "="*70)
    print("TEST 3: Ground ball to right field (positive X)")
    print("="*70)

    simulator = BattedBallSimulator()

    # Ground ball to right
    # NOTE: Negative spray angle = right field (opposite for RHB)
    result = simulator.simulate(
        exit_velocity=85.0,
        launch_angle=5.0,
        spray_angle=-25.0,  # NEGATIVE = right field
        backspin_rpm=500,
        sidespin_rpm=0
    )

    print(f"\nBall landing position (field coords):")
    print(f"  X = {result.landing_x:.1f} ft (should be positive for right field)")
    print(f"  Y = {result.landing_y:.1f} ft")
    print(f"  Distance from home: {result.distance:.1f} ft")

    # Validate landing position
    if result.landing_x <= 0:
        print(f"  ❌ FAIL: Right field ball has negative X coordinate")
        return False
    else:
        print(f"  ✓ PASS: Right field ball correctly in positive X region")
        return True


def test_coordinate_conversion():
    """Test coordinate conversion functions directly."""
    print("\n" + "="*70)
    print("TEST 4: Coordinate conversion functions")
    print("="*70)

    from batted_ball.trajectory import convert_position_trajectory_to_field, convert_velocity_trajectory_to_field

    # Test 1: Ball hit straight to center field
    # In trajectory coords: x=100 (toward outfield), y=0 (no lateral), z=10
    # Should become: x=0 (no lateral), y=100 (toward CF), z=10
    x_field, y_field, z_field = convert_position_trajectory_to_field(100, 0, 10)
    print(f"\nCenter field position conversion:")
    print(f"  Trajectory: (100, 0, 10) → Field: ({x_field:.1f}, {y_field:.1f}, {z_field:.1f})")

    if abs(x_field) < 1e-6 and abs(y_field - 100) < 1e-6:
        print(f"  ✓ PASS")
    else:
        print(f"  ❌ FAIL: Expected (0, 100, 10)")
        return False

    # Test 2: Ball hit to left field
    # In trajectory coords: x=50, y=50 (left field positive), z=5
    # Should become: x=-50 (left = negative), y=50, z=5
    x_field, y_field, z_field = convert_position_trajectory_to_field(50, 50, 5)
    print(f"\nLeft field position conversion:")
    print(f"  Trajectory: (50, 50, 5) → Field: ({x_field:.1f}, {y_field:.1f}, {z_field:.1f})")

    if abs(x_field + 50) < 1e-6 and abs(y_field - 50) < 1e-6:
        print(f"  ✓ PASS")
    else:
        print(f"  ❌ FAIL: Expected (-50, 50, 5)")
        return False

    # Test 3: Ball hit to right field
    # In trajectory coords: x=50, y=-50 (right field = negative Y in traj), z=5
    # Should become: x=50 (right = positive), y=50, z=5
    x_field, y_field, z_field = convert_position_trajectory_to_field(50, -50, 5)
    print(f"\nRight field position conversion:")
    print(f"  Trajectory: (50, -50, 5) → Field: ({x_field:.1f}, {y_field:.1f}, {z_field:.1f})")

    if abs(x_field - 50) < 1e-6 and abs(y_field - 50) < 1e-6:
        print(f"  ✓ PASS")
    else:
        print(f"  ❌ FAIL: Expected (50, 50, 5)")
        return False

    return True


def main():
    """Run all tests."""
    print("\n" + "="*70)
    print("COORDINATE SYSTEM FIX VALIDATION")
    print("="*70)

    tests = [
        ("Ground ball up middle", test_ground_ball_up_middle),
        ("Ground ball to left", test_ground_ball_to_left),
        ("Ground ball to right", test_ground_ball_to_right),
        ("Coordinate conversions", test_coordinate_conversion),
    ]

    results = []
    for name, test_func in tests:
        try:
            result = test_func()
            results.append((name, result))
        except Exception as e:
            print(f"\n❌ ERROR in {name}: {e}")
            import traceback
            traceback.print_exc()
            results.append((name, False))

    # Summary
    print("\n" + "="*70)
    print("TEST SUMMARY")
    print("="*70)

    passed = sum(1 for _, result in results if result)
    total = len(results)

    for name, result in results:
        status = "✓ PASS" if result else "❌ FAIL"
        print(f"  {status}: {name}")

    print(f"\nOverall: {passed}/{total} tests passed")

    if passed == total:
        print("\n✅ All tests passed! Coordinate system is unified.")
        return 0
    else:
        print("\n❌ Some tests failed. Review coordinate system usage.")
        return 1


if __name__ == "__main__":
    sys.exit(main())
