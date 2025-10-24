"""
Validation tests for Phase 2: Bat-Ball Collision Physics

Tests the enhanced collision model with:
1. Variable coefficient of restitution (COR)
2. Sweet spot physics and vibration energy loss
3. Exit velocity predictions from bat/pitch speeds
4. Contact location effects

Validates against empirical baseball data and physics principles.
"""

import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from batted_ball.contact import ContactModel
import numpy as np


def test_cor_variation():
    """
    Test 1: Coefficient of Restitution varies with contact location.

    Expected behavior:
    - COR maximum at sweet spot (0.55 for wood)
    - COR decreases linearly with distance from sweet spot
    - Minimum COR = 0.35
    """
    print("=" * 70)
    print("TEST 1: Coefficient of Restitution Variation")
    print("=" * 70)

    model = ContactModel(bat_type='wood')

    # Test sweet spot
    cor_sweet = model.calculate_cor(distance_from_sweet_spot_inches=0.0)
    print(f"\n✓ Sweet spot COR: {cor_sweet:.3f}")
    assert abs(cor_sweet - 0.55) < 0.01, "Sweet spot COR should be 0.55"

    # Test degradation
    cor_1inch = model.calculate_cor(distance_from_sweet_spot_inches=1.0)
    print(f"✓ 1 inch from sweet spot: {cor_1inch:.3f}")
    expected_1inch = 0.55 - 0.03 * 1.0
    assert abs(cor_1inch - expected_1inch) < 0.01, "COR degradation incorrect"

    # Test far from sweet spot
    cor_far = model.calculate_cor(distance_from_sweet_spot_inches=10.0)
    print(f"✓ 10 inches from sweet spot: {cor_far:.3f} (floor at minimum)")
    assert cor_far >= 0.35, "COR should not go below minimum"

    # Test aluminum bonus
    model_aluminum = ContactModel(bat_type='aluminum')
    cor_aluminum = model_aluminum.calculate_cor(0.0)
    print(f"\n✓ Aluminum bat sweet spot COR: {cor_aluminum:.3f}")
    assert cor_aluminum > cor_sweet, "Aluminum should have higher COR"

    print("\n✅ TEST 1 PASSED: COR variation working correctly")
    return True


def test_vibration_energy_loss():
    """
    Test 2: Energy loss from vibrations increases with distance from sweet spot.

    Expected behavior:
    - Zero loss at sweet spot
    - Linear increase with distance (20% per inch)
    - Maximum loss capped at 60%
    """
    print("\n" + "=" * 70)
    print("TEST 2: Vibration Energy Loss")
    print("=" * 70)

    model = ContactModel()

    # Sweet spot: no loss
    loss_sweet = model.calculate_vibration_energy_loss(0.0)
    print(f"\n✓ Sweet spot vibration loss: {loss_sweet:.1%}")
    assert loss_sweet == 0.0, "Sweet spot should have zero vibration loss"

    # 1 inch off: 20% loss
    loss_1inch = model.calculate_vibration_energy_loss(1.0)
    print(f"✓ 1 inch off: {loss_1inch:.1%} energy lost to vibrations")
    assert abs(loss_1inch - 0.20) < 0.01, "Should lose 20% per inch"

    # 2 inches off: 40% loss
    loss_2inch = model.calculate_vibration_energy_loss(2.0)
    print(f"✓ 2 inches off: {loss_2inch:.1%} energy lost")
    assert abs(loss_2inch - 0.40) < 0.01, "Should lose 40% at 2 inches"

    # Far off: capped at 60%
    loss_far = model.calculate_vibration_energy_loss(10.0)
    print(f"✓ 10 inches off: {loss_far:.1%} (capped at maximum)")
    assert loss_far <= 0.60, "Loss should be capped at 60%"

    print("\n✅ TEST 2 PASSED: Vibration energy loss working correctly")
    return True


def test_exit_velocity_empirical():
    """
    Test 3: Exit velocity predictions match empirical baseball data.

    Empirical relationships (from MLB Statcast and physics research):
    1. 70 mph bat + 90 mph pitch ≈ 100-105 mph exit velocity (sweet spot)
    2. Exit velocity scales with bat speed (~1.2x contribution)
    3. Pitch speed contributes less (~0.2x contribution)
    4. Off sweet spot reduces exit velocity
    """
    print("\n" + "=" * 70)
    print("TEST 3: Exit Velocity Empirical Validation")
    print("=" * 70)

    model = ContactModel()

    # Test 1: Typical MLB swing (sweet spot)
    bat_speed = 70.0  # mph (typical MLB bat speed)
    pitch_speed = 90.0  # mph (typical fastball)

    ev_sweet = model.calculate_exit_velocity(
        bat_speed_mph=bat_speed,
        pitch_speed_mph=pitch_speed,
        distance_from_sweet_spot_inches=0.0
    )

    print(f"\n✓ Sweet spot contact:")
    print(f"  Bat: {bat_speed} mph, Pitch: {pitch_speed} mph")
    print(f"  Exit velocity: {ev_sweet:.1f} mph")

    # Expected range: 100-105 mph
    assert 95 <= ev_sweet <= 110, f"Exit velocity {ev_sweet:.1f} outside expected range"

    # Test 2: Bat speed dominance
    ev_fast_bat = model.calculate_exit_velocity(75.0, 90.0, distance_from_sweet_spot_inches=0.0)
    ev_slow_bat = model.calculate_exit_velocity(65.0, 90.0, distance_from_sweet_spot_inches=0.0)

    bat_speed_effect = (ev_fast_bat - ev_slow_bat) / (75.0 - 65.0)
    print(f"\n✓ Bat speed effect: {bat_speed_effect:.2f} mph EV per 1 mph bat speed")
    # Should be around 1.0-1.5 mph EV per mph bat speed
    assert 0.8 <= bat_speed_effect <= 1.8, "Bat speed contribution out of range"

    # Test 3: Off sweet spot reduces exit velocity
    ev_off_sweet = model.calculate_exit_velocity(
        bat_speed_mph=70.0,
        pitch_speed_mph=90.0,
        distance_from_sweet_spot_inches=2.0  # 2 inches off
    )

    print(f"\n✓ 2 inches from sweet spot:")
    print(f"  Exit velocity: {ev_off_sweet:.1f} mph")
    print(f"  Reduction: {ev_sweet - ev_off_sweet:.1f} mph ({(ev_sweet - ev_off_sweet)/ev_sweet*100:.1f}%)")

    assert ev_off_sweet < ev_sweet, "Off sweet spot should reduce exit velocity"
    reduction_pct = (ev_sweet - ev_off_sweet) / ev_sweet
    assert 0.10 <= reduction_pct <= 0.50, "Exit velocity reduction should be 10-50%"

    print("\n✅ TEST 3 PASSED: Exit velocity predictions reasonable")
    return True


def test_sweet_spot_advantage():
    """
    Test 4: Sweet spot contact produces significantly better results.

    Expected behavior:
    - Higher exit velocity at sweet spot
    - Higher COR at sweet spot
    - No energy loss from vibrations at sweet spot
    """
    print("\n" + "=" * 70)
    print("TEST 4: Sweet Spot Advantage")
    print("=" * 70)

    model = ContactModel()

    # Same swing, different contact points
    bat_speed = 70.0
    pitch_speed = 90.0

    result_sweet = model.full_collision(
        bat_speed_mph=bat_speed,
        pitch_speed_mph=pitch_speed,
        bat_path_angle_deg=30.0,
        distance_from_sweet_spot_inches=0.0
    )

    result_off = model.full_collision(
        bat_speed_mph=bat_speed,
        pitch_speed_mph=pitch_speed,
        bat_path_angle_deg=30.0,
        distance_from_sweet_spot_inches=3.0  # 3 inches off
    )

    print(f"\n✓ Sweet Spot Contact:")
    print(f"  Exit Velocity: {result_sweet['exit_velocity']:.1f} mph")
    print(f"  COR: {result_sweet['cor']:.3f}")
    print(f"  Vibration Loss: {result_sweet['vibration_loss']:.1%}")
    print(f"  Launch Angle: {result_sweet['launch_angle']:.1f}°")
    print(f"  Backspin: {result_sweet['backspin_rpm']:.0f} rpm")

    print(f"\n✓ 3 Inches Off Sweet Spot:")
    print(f"  Exit Velocity: {result_off['exit_velocity']:.1f} mph")
    print(f"  COR: {result_off['cor']:.3f}")
    print(f"  Vibration Loss: {result_off['vibration_loss']:.1%}")
    print(f"  Launch Angle: {result_off['launch_angle']:.1f}°")
    print(f"  Backspin: {result_off['backspin_rpm']:.0f} rpm")

    print(f"\n✓ Sweet Spot Advantage:")
    print(f"  Exit velocity: +{result_sweet['exit_velocity'] - result_off['exit_velocity']:.1f} mph")
    print(f"  COR: +{result_sweet['cor'] - result_off['cor']:.3f}")

    assert result_sweet['exit_velocity'] > result_off['exit_velocity'], "Sweet spot should have higher EV"
    assert result_sweet['cor'] > result_off['cor'], "Sweet spot should have higher COR"
    assert result_sweet['vibration_loss'] < result_off['vibration_loss'], "Sweet spot should have less vibration"

    print("\n✅ TEST 4 PASSED: Sweet spot provides clear advantage")
    return True


def test_contact_offset_effects():
    """
    Test 5: Vertical contact offset affects launch angle and spin.

    Expected behavior:
    - Below center: higher launch angle, more backspin
    - Above center: lower launch angle, less backspin (topspin)
    """
    print("\n" + "=" * 70)
    print("TEST 5: Contact Offset Effects")
    print("=" * 70)

    model = ContactModel()

    # Same bat path, different contact heights
    bat_speed = 70.0
    pitch_speed = 90.0
    bat_angle = 25.0

    # Center contact
    result_center = model.full_collision(
        bat_speed_mph=bat_speed,
        pitch_speed_mph=pitch_speed,
        bat_path_angle_deg=bat_angle,
        vertical_contact_offset_inches=0.0
    )

    # Below center
    result_below = model.full_collision(
        bat_speed_mph=bat_speed,
        pitch_speed_mph=pitch_speed,
        bat_path_angle_deg=bat_angle,
        vertical_contact_offset_inches=-1.0  # 1 inch below
    )

    # Above center
    result_above = model.full_collision(
        bat_speed_mph=bat_speed,
        pitch_speed_mph=pitch_speed,
        bat_path_angle_deg=bat_angle,
        vertical_contact_offset_inches=1.0  # 1 inch above
    )

    print(f"\n✓ Center Contact:")
    print(f"  Launch Angle: {result_center['launch_angle']:.1f}°")
    print(f"  Backspin: {result_center['backspin_rpm']:.0f} rpm")

    print(f"\n✓ 1 Inch Below Center (undercut):")
    print(f"  Launch Angle: {result_below['launch_angle']:.1f}° (+{result_below['launch_angle'] - result_center['launch_angle']:.1f}°)")
    print(f"  Backspin: {result_below['backspin_rpm']:.0f} rpm (+{result_below['backspin_rpm'] - result_center['backspin_rpm']:.0f} rpm)")

    print(f"\n✓ 1 Inch Above Center (topped):")
    print(f"  Launch Angle: {result_above['launch_angle']:.1f}° ({result_above['launch_angle'] - result_center['launch_angle']:.1f}°)")
    print(f"  Backspin: {result_above['backspin_rpm']:.0f} rpm ({result_above['backspin_rpm'] - result_center['backspin_rpm']:.0f} rpm)")

    assert result_below['launch_angle'] > result_center['launch_angle'], "Below center should increase launch angle"
    assert result_below['backspin_rpm'] > result_center['backspin_rpm'], "Below center should increase backspin"
    assert result_above['launch_angle'] < result_center['launch_angle'], "Above center should decrease launch angle"
    assert result_above['backspin_rpm'] < result_center['backspin_rpm'], "Above center should decrease backspin"

    print("\n✅ TEST 5 PASSED: Contact offset effects working correctly")
    return True


def test_realistic_home_run():
    """
    Test 6: Model produces realistic home run parameters.

    Use the enhanced collision model to simulate a typical home run
    and verify the parameters are realistic.
    """
    print("\n" + "=" * 70)
    print("TEST 6: Realistic Home Run Scenario")
    print("=" * 70)

    model = ContactModel(bat_type='wood')

    # Typical home run scenario
    # Good bat speed, slight uppercut, sweet spot contact
    result = model.full_collision(
        bat_speed_mph=72.0,      # Good bat speed
        pitch_speed_mph=92.0,    # Fastball
        bat_path_angle_deg=28.0, # Optimal angle
        vertical_contact_offset_inches=-0.5,  # Slightly below center
        distance_from_sweet_spot_inches=0.0   # Sweet spot!
    )

    print(f"\n✓ Home Run Ball Parameters:")
    print(f"  Exit Velocity: {result['exit_velocity']:.1f} mph")
    print(f"  Launch Angle: {result['launch_angle']:.1f}°")
    print(f"  Backspin: {result['backspin_rpm']:.0f} rpm")
    print(f"  COR: {result['cor']:.3f}")
    print(f"  Vibration Loss: {result['vibration_loss']:.1%}")

    # Validation ranges (from MLB Statcast data)
    # Home runs typically: 95-115 mph exit velo, 20-35° launch, 1500-2500 rpm backspin
    print(f"\n✓ Validation Against MLB Data:")

    ev_valid = 95 <= result['exit_velocity'] <= 115
    print(f"  Exit velocity in range [95-115 mph]: {ev_valid}")

    la_valid = 20 <= result['launch_angle'] <= 35
    print(f"  Launch angle in range [20-35°]: {la_valid}")

    bs_valid = 1200 <= result['backspin_rpm'] <= 2800
    print(f"  Backspin in range [1200-2800 rpm]: {bs_valid}")

    assert ev_valid, f"Exit velocity {result['exit_velocity']:.1f} outside MLB range"
    assert la_valid, f"Launch angle {result['launch_angle']:.1f} outside optimal range"
    assert bs_valid, f"Backspin {result['backspin_rpm']:.0f} outside typical range"

    print("\n✅ TEST 6 PASSED: Home run parameters realistic")
    return True


def run_all_tests():
    """Run all validation tests for collision model."""
    print("\n" + "=" * 70)
    print("PHASE 2 COLLISION MODEL VALIDATION")
    print("Testing enhanced bat-ball collision physics")
    print("=" * 70)

    tests = [
        ("COR Variation", test_cor_variation),
        ("Vibration Energy Loss", test_vibration_energy_loss),
        ("Exit Velocity Empirical", test_exit_velocity_empirical),
        ("Sweet Spot Advantage", test_sweet_spot_advantage),
        ("Contact Offset Effects", test_contact_offset_effects),
        ("Realistic Home Run", test_realistic_home_run),
    ]

    results = []
    for name, test_func in tests:
        try:
            passed = test_func()
            results.append((name, passed))
        except AssertionError as e:
            print(f"\n❌ TEST FAILED: {name}")
            print(f"   Error: {e}")
            results.append((name, False))
        except Exception as e:
            print(f"\n❌ TEST ERROR: {name}")
            print(f"   Unexpected error: {e}")
            results.append((name, False))

    # Summary
    print("\n" + "=" * 70)
    print("VALIDATION SUMMARY")
    print("=" * 70)

    passed = sum(1 for _, result in results if result)
    total = len(results)

    for name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status}: {name}")

    print(f"\n{'='*70}")
    print(f"Results: {passed}/{total} tests passed ({100*passed/total:.0f}%)")
    print(f"{'='*70}")

    if passed == total:
        print("\n🎉 ALL TESTS PASSED! Collision model validated successfully.")
        return True
    else:
        print(f"\n⚠️  {total - passed} test(s) failed. Review implementation.")
        return False


if __name__ == '__main__':
    success = run_all_tests()
    sys.exit(0 if success else 1)
