#!/usr/bin/env python3
"""
Comprehensive test of coordinate system fixes with multiple scenarios.
"""

import sys
from batted_ball.trajectory import BattedBallSimulator
from batted_ball.ground_ball_interception import GroundBallInterceptor
from batted_ball.fielding import Fielder
from batted_ball.field_layout import FieldLayout, FieldPosition

def test_scenario(name, exit_velocity, launch_angle, spray_angle, fielders_to_test=['pitcher', 'shortstop']):
    """Test a specific ground ball scenario."""
    
    print(f"\n{'='*70}")
    print(f"TEST: {name}")
    print(f"{'='*70}")
    print(f"Velocity: {exit_velocity} mph, Angle: {launch_angle}°, Spray: {spray_angle}°")
    
    # Create batted ball
    sim = BattedBallSimulator()
    result = sim.simulate(
        exit_velocity=exit_velocity,
        launch_angle=launch_angle,
        spray_angle=spray_angle,
        backspin_rpm=1000,
        sidespin_rpm=0,
        initial_height=2.0
    )
    
    print(f"\nBatted Ball:")
    print(f"  Landing: ({result.landing_x:.1f}, {result.landing_y:.1f}) ft at distance {result.distance:.1f} ft")
    print(f"  Landing velocity: ({result.velocity[-1][0]:.1f}, {result.velocity[-1][1]:.1f}, {result.velocity[-1][2]:.1f}) m/s")
    
    # Create fielders
    field = FieldLayout()
    fielders = {}
    
    for pos_name in ['pitcher', 'catcher', 'first_base', 'second_base', 'shortstop', 'third_base']:
        pos = field.get_defensive_position(pos_name)
        fielder = Fielder(pos_name.replace('_', ' ').title(), pos_name, 60, 60, 60, 60)
        fielder.current_position = FieldPosition(pos.x, pos.y, pos.z)
        fielders[pos_name] = fielder
    
    # Test interception
    interceptor = GroundBallInterceptor(surface_type='grass')
    interception = interceptor.find_best_interception(result, fielders)
    
    if interception.can_be_fielded:
        fielder_start = fielders[interception.fielding_position].current_position
        distance_traveled = fielder_start.distance_to(interception.ball_position_at_interception)
        
        print(f"\nBest Interception:")
        print(f"  Fielder: {interception.fielding_position}")
        print(f"  Start position: ({fielder_start.x:.1f}, {fielder_start.y:.1f}) ft")
        print(f"  Intercept position: ({interception.ball_position_at_interception.x:.1f}, {interception.ball_position_at_interception.y:.1f}) ft")
        print(f"  Distance traveled: {distance_traveled:.1f} ft")
        print(f"  Time margin: {interception.time_margin:.3f} s")
        
        # Validation
        if distance_traveled > 200:
            print(f"\n  ❌ FAIL: Distance {distance_traveled:.1f} ft is unrealistic!")
            return False
        elif distance_traveled > 100:
            print(f"\n  ⚠️  WARNING: Distance {distance_traveled:.1f} ft seems far")
            return True
        else:
            print(f"\n  ✅ PASS")
            return True
    else:
        print(f"\nCould not be fielded")
        return True

def main():
    """Run multiple test scenarios."""
    
    print("="*70)
    print("COORDINATE SYSTEM FIX - COMPREHENSIVE VALIDATION")
    print("="*70)
    
    all_pass = True
    
    # Test 1: Ground ball up the middle
    all_pass &= test_scenario(
        "Ground ball up the middle",
        exit_velocity=75,
        launch_angle=5,
        spray_angle=0
    )
    
    # Test 2: Ground ball to the left (shortstop)
    all_pass &= test_scenario(
        "Ground ball to left field side",
        exit_velocity=80,
        launch_angle=8,
        spray_angle=-30
    )
    
    # Test 3: Ground ball to the right (first base)
    all_pass &= test_scenario(
        "Ground ball to right field side",
        exit_velocity=80,
        launch_angle=8,
        spray_angle=30
    )
    
    # Test 4: Weak ground ball
    all_pass &= test_scenario(
        "Weak ground ball",
        exit_velocity=50,
        launch_angle=2,
        spray_angle=0
    )
    
    # Test 5: Harder ground ball
    all_pass &= test_scenario(
        "Harder ground ball",
        exit_velocity=95,
        launch_angle=10,
        spray_angle=0
    )
    
    print(f"\n{'='*70}")
    if all_pass:
        print("✅ ALL TESTS PASSED - Coordinate system is fixed!")
        return 0
    else:
        print("❌ SOME TESTS FAILED - Check coordinate system")
        return 1

if __name__ == "__main__":
    sys.exit(main())
