#!/usr/bin/env python3
"""
Direct test of ground ball interception to see actual fielder movements.
"""

import sys
from batted_ball.trajectory import BattedBallSimulator
from batted_ball.ground_ball_interception import GroundBallInterceptor
from batted_ball.fielding import Fielder
from batted_ball.field_layout import FieldLayout, FieldPosition
from batted_ball.constants import FEET_TO_METERS

def test_ground_ball_interception():
    """Test ground ball interception directly."""
    
    print("=" * 70)
    print("DIRECT GROUND BALL INTERCEPTION TEST")
    print("=" * 70)
    
    # Create a batted ball (up the middle, low launch angle)
    sim = BattedBallSimulator()
    result = sim.simulate(
        exit_velocity=75.0,
        launch_angle=5.0,  # Low launch = ground ball
        spray_angle=0.0,   # Up the middle
        backspin_rpm=1200,
        sidespin_rpm=0,
        initial_height=2.0  # Contact height in feet
    )
    
    print(f"\nBatted Ball Result:")
    print(f"  Landing position: ({result.landing_x:.1f}, {result.landing_y:.1f}) ft")
    print(f"  Distance: {result.distance:.1f} ft")
    print(f"  Landing velocity (final): {result.velocity[-1]} m/s")
    print(f"  Flight time: {result.flight_time:.3f} s")
    
    # Create fielders at standard positions
    field = FieldLayout()
    fielders = {}
    
    # Pitcher at standard position
    pitcher_pos = field.get_defensive_position('pitcher')
    pitcher = Fielder("Pitcher", "pitcher", 60, 60, 60, 60)
    pitcher.current_position = FieldPosition(pitcher_pos.x, pitcher_pos.y, pitcher_pos.z)
    fielders['pitcher'] = pitcher
    
    # Add a few other fielders
    for pos_name in ['catcher', 'first_base', 'second_base', 'shortstop', 'third_base']:
        pos = field.get_defensive_position(pos_name)
        fielder = Fielder(pos_name.replace('_', ' ').title(), pos_name, 60, 60, 60, 60)
        fielder.current_position = FieldPosition(pos.x, pos.y, pos.z)
        fielders[pos_name] = fielder
    
    # Run ground ball interception analysis
    interceptor = GroundBallInterceptor(surface_type='grass')
    interception = interceptor.find_best_interception(result, fielders)
    
    print(f"\nGround Ball Interception Result:")
    print(f"  Can be fielded: {interception.can_be_fielded}")
    
    if interception.can_be_fielded:
        print(f"  Fielding position: {interception.fielding_position}")
        print(f"  Fielder: {interception.fielding_fielder.name}")
        print(f"  Interception position: ({interception.ball_position_at_interception.x:.1f}, {interception.ball_position_at_interception.y:.1f}) ft")
        print(f"  Interception time: {interception.interception_time:.3f} s")
        print(f"  Fielder arrival time: {interception.fielder_arrival_time:.3f} s")
        print(f"  Time margin: {interception.time_margin:.3f} s (+ = early arrival)")
        print(f"  Fielder traveled: {interception.interception_distance:.1f} ft")
        
        # Check if this is reasonable
        fielder_start = fielders[interception.fielding_position].current_position
        print(f"\n  Fielder start position: ({fielder_start.x:.1f}, {fielder_start.y:.1f}) ft")
        
        distance_traveled = fielder_start.distance_to(interception.ball_position_at_interception)
        print(f"  Distance from start to interception: {distance_traveled:.1f} ft")
        
        if interception.fielding_position == 'pitcher':
            # Pitcher should travel max ~40 ft for nearby ground balls
            if distance_traveled > 60:
                print(f"\n  ⚠️  WARNING: Pitcher traveled {distance_traveled:.1f} ft - seems far!")
                return False
            elif distance_traveled > 150:
                print(f"\n  ❌ FAIL: Pitcher traveled {distance_traveled:.1f} ft - COORDINATE BUG!")
                return False
        
        print(f"\n  ✅ PASS: Fielder movement looks reasonable")
        return True
    else:
        print(f"  Could not be fielded")
        return None

if __name__ == "__main__":
    success = test_ground_ball_interception()
    if success is None:
        sys.exit(0)
    sys.exit(0 if success else 1)
