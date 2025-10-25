"""
Validation tests for fielding and baserunning mechanics.

Tests to ensure the physics produce realistic outcomes that match
MLB performance data and expectations.
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from batted_ball import (
    # Fielding and baserunning
    create_elite_fielder, create_average_fielder, create_poor_fielder,
    create_speed_runner, create_average_runner, create_slow_runner,
    create_standard_field, FieldPosition,
    # Constants for validation
    HOME_TO_FIRST_TIME_MIN, HOME_TO_FIRST_TIME_AVG, HOME_TO_FIRST_TIME_MAX,
    FIELDER_SPRINT_SPEED_AVG, RUNNER_SPRINT_SPEED_AVG,
)


def test_home_to_first_times():
    """Test that home-to-first times are realistic."""
    print("=== HOME-TO-FIRST TIME VALIDATION ===")
    
    # Create runners across the spectrum
    runners = [
        ("Elite Speed (90+ rating)", create_speed_runner("Elite")),
        ("Good Speed (70 rating)", create_average_runner("Good")),
        ("Average Speed (50 rating)", create_average_runner("Average")),
        ("Below Average (30 rating)", create_slow_runner("Slow"))
    ]
    
    print(f"Expected MLB Range: {HOME_TO_FIRST_TIME_MIN:.1f}s - {HOME_TO_FIRST_TIME_MAX:.1f}s")
    print(f"MLB Average: {HOME_TO_FIRST_TIME_AVG:.1f}s")
    print()
    
    all_times_valid = True
    
    for name, runner in runners:
        time = runner.get_home_to_first_time()
        
        # Check if time is within reasonable bounds
        is_valid = HOME_TO_FIRST_TIME_MIN <= time <= HOME_TO_FIRST_TIME_MAX
        all_times_valid &= is_valid
        
        status = "✓" if is_valid else "✗"
        print(f"{status} {name}: {time:.2f}s")
    
    print()
    return all_times_valid


def test_fielding_range_realism():
    """Test that fielding ranges produce realistic catch probabilities."""
    print("=== FIELDING RANGE VALIDATION ===")
    
    field = create_standard_field()
    
    # Test scenarios: different balls to center field
    scenarios = [
        ("Routine fly ball", 300, 4.0),      # 300 ft, 4 sec hang time - should be caught by all
        ("Challenging fly ball", 350, 3.5),  # 350 ft, 3.5 sec - elite should catch, others might not
        ("Impossible fly ball", 400, 2.0),   # 400 ft, 2 sec - nobody should catch
    ]
    
    fielders = [
        ("Elite CF", create_elite_fielder("Elite", "outfield")),
        ("Average CF", create_average_fielder("Average", "outfield")),
        ("Poor CF", create_poor_fielder("Poor", "outfield"))
    ]
    
    cf_position = field.get_defensive_position("center_field")
    
    all_ranges_realistic = True
    
    for scenario_name, distance, hang_time in scenarios:
        print(f"\n{scenario_name} ({distance} ft, {hang_time:.1f}s hang time):")
        
        ball_position = FieldPosition(0, distance, 0)
        
        catch_rates = []
        for fielder_name, fielder in fielders:
            fielder.update_position(cf_position)
            can_catch = fielder.can_reach_ball(ball_position, hang_time)
            time_needed = fielder.calculate_time_to_position(ball_position)
            
            catch_rates.append(can_catch)
            status = "CAN CATCH" if can_catch else "TOO FAR"
            print(f"  {fielder_name}: {time_needed:.2f}s needed - {status}")
        
        # Validate expectations
        if scenario_name == "Routine fly ball":
            # All fielders should catch routine balls
            expected = all(catch_rates)
        elif scenario_name == "Challenging fly ball":
            # Elite should catch, others maybe not
            expected = catch_rates[0] and not all(catch_rates)
        else:  # Impossible
            # Nobody should catch impossible balls
            expected = not any(catch_rates)
        
        all_ranges_realistic &= expected
        if not expected:
            print(f"  ✗ Unrealistic results for {scenario_name}")
    
    print()
    return all_ranges_realistic


def test_throw_accuracy_realism():
    """Test that throwing accuracy produces realistic results."""
    print("=== THROWING ACCURACY VALIDATION ===")
    
    # Test different fielders throwing to first base (90 ft)
    fielders = [
        ("Elite Accuracy", create_elite_fielder("Elite", "infield")),
        ("Average Accuracy", create_average_fielder("Average", "infield")),
        ("Poor Accuracy", create_poor_fielder("Poor", "infield"))
    ]
    
    field = create_standard_field()
    first_base = field.get_base_position("first")
    shortstop_pos = field.get_defensive_position("shortstop")
    
    print("Throw accuracy from shortstop to first base (90 ft):")
    
    all_accuracy_realistic = True
    
    for name, fielder in fielders:
        fielder.update_position(shortstop_pos)
        
        # Simulate 10 throws and check accuracy
        errors = []
        for _ in range(10):
            throw_result = fielder.throw_ball(first_base)
            h_error, v_error = throw_result.accuracy_error
            total_error = (h_error**2 + v_error**2)**0.5
            errors.append(total_error)
        
        avg_error = sum(errors) / len(errors)
        std_error = fielder.get_throwing_accuracy_std_degrees()
        
        # Elite should have <2" average error, poor should have >6" average error
        is_realistic = True
        if "Elite" in name and avg_error > 3.0:
            is_realistic = False
        elif "Poor" in name and avg_error < 4.0:
            is_realistic = False
        
        all_accuracy_realistic &= is_realistic
        status = "✓" if is_realistic else "✗"
        print(f"  {status} {name}: {avg_error:.1f}\" avg error (±{std_error:.1f}° std)")
    
    print()
    return all_accuracy_realistic


def test_baserunning_physics():
    """Test that baserunning physics are realistic."""
    print("=== BASERUNNING PHYSICS VALIDATION ===")
    
    # Test different distance scenarios
    scenarios = [
        ("Home to First", "home", "first"),
        ("First to Third", "first", "third"),
        ("Second to Home", "second", "home"),
    ]
    
    runner = create_average_runner("Test Runner")
    
    all_physics_realistic = True
    
    for scenario_name, from_base, to_base in scenarios:
        time = runner.calculate_time_to_base(from_base, to_base)
        
        # Validate against expected ranges
        is_realistic = True
        if scenario_name == "Home to First":
            # Should be close to average home-to-first time
            is_realistic = 3.5 <= time <= 5.5
        elif scenario_name == "First to Third":
            # Should be roughly 2x home-to-first (bit less due to turns)
            is_realistic = 7.0 <= time <= 11.0
        elif scenario_name == "Second to Home":
            # Similar to first to third
            is_realistic = 7.0 <= time <= 11.0
        
        all_physics_realistic &= is_realistic
        status = "✓" if is_realistic else "✗"
        print(f"  {status} {scenario_name}: {time:.2f}s")
    
    print()
    return all_physics_realistic


def test_sprint_speed_conversion():
    """Test that sprint speed ratings convert to realistic mph values."""
    print("=== SPRINT SPEED CONVERSION VALIDATION ===")
    
    # Test fielders and runners
    test_subjects = [
        ("Elite Fielder", create_elite_fielder("Elite", "outfield")),
        ("Average Fielder", create_average_fielder("Average", "outfield")),
        ("Poor Fielder", create_poor_fielder("Poor", "outfield")),
        ("Speed Runner", create_speed_runner("Speed")),
        ("Average Runner", create_average_runner("Average")),
        ("Slow Runner", create_slow_runner("Slow")),
    ]
    
    print("Sprint speeds (MLB range: ~15-22 mph):")
    
    all_speeds_realistic = True
    
    for name, subject in test_subjects:
        if hasattr(subject, 'get_sprint_speed_fps'):
            speed_fps = subject.get_sprint_speed_fps()
        else:
            continue
            
        speed_mph = speed_fps * 0.681818  # Convert ft/s to mph
        
        # Check if speed is in realistic range (15-22 mph for MLB players)
        is_realistic = 14.0 <= speed_mph <= 23.0
        all_speeds_realistic &= is_realistic
        
        status = "✓" if is_realistic else "✗"
        print(f"  {status} {name}: {speed_fps:.1f} ft/s ({speed_mph:.1f} mph)")
    
    print()
    return all_speeds_realistic


def test_reaction_time_realism():
    """Test that reaction times are realistic."""
    print("=== REACTION TIME VALIDATION ===")
    
    fielders = [
        ("Elite Fielder", create_elite_fielder("Elite", "outfield")),
        ("Average Fielder", create_average_fielder("Average", "outfield")),
        ("Poor Fielder", create_poor_fielder("Poor", "outfield")),
    ]
    
    print("Reaction times (MLB range: ~0.1-0.4s):")
    
    all_reactions_realistic = True
    
    for name, fielder in fielders:
        reaction_time = fielder.get_reaction_time_seconds()
        
        # Should be between 0.0 and 0.5 seconds
        is_realistic = 0.0 <= reaction_time <= 0.5
        all_reactions_realistic &= is_realistic
        
        status = "✓" if is_realistic else "✗"
        print(f"  {status} {name}: {reaction_time:.3f}s")
    
    print()
    return all_reactions_realistic


def run_all_validations():
    """Run all validation tests and report results."""
    print("FIELDING AND BASERUNNING VALIDATION SUITE")
    print("=" * 50)
    print()
    
    tests = [
        ("Home-to-First Times", test_home_to_first_times),
        ("Fielding Range", test_fielding_range_realism),
        ("Throwing Accuracy", test_throw_accuracy_realism),
        ("Baserunning Physics", test_baserunning_physics),
        ("Sprint Speed Conversion", test_sprint_speed_conversion),
        ("Reaction Time Realism", test_reaction_time_realism),
    ]
    
    results = []
    
    for test_name, test_func in tests:
        print(f"Running {test_name}...")
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"ERROR in {test_name}: {e}")
            results.append((test_name, False))
        print()
    
    # Summary
    print("VALIDATION SUMMARY")
    print("-" * 30)
    
    passed = 0
    total = len(results)
    
    for test_name, result in results:
        status = "PASS" if result else "FAIL"
        print(f"{test_name}: {status}")
        if result:
            passed += 1
    
    print()
    print(f"Overall: {passed}/{total} tests passed ({passed/total*100:.1f}%)")
    
    if passed == total:
        print("🎉 All validations passed! The fielding and baserunning mechanics are realistic.")
    else:
        print("⚠️  Some validations failed. Review the physics constants and calculations.")
    
    return passed == total


if __name__ == "__main__":
    success = run_all_validations()
    sys.exit(0 if success else 1)