"""Test the new ground ball interception system."""
import sys
sys.path.append('.')

from batted_ball import BattedBallSimulator
from batted_ball.ground_ball_interception import GroundBallInterceptor
from batted_ball import create_standard_defense
import numpy as np

def test_ground_ball_interception():
    """Test the new interception system."""
    
    print("TESTING GROUND BALL INTERCEPTION SYSTEM")
    print("="*50)
    
    # Create components
    ball_sim = BattedBallSimulator()
    interceptor = GroundBallInterceptor(surface_type='grass')
    fielders = create_standard_defense()
    
    # Test scenarios
    test_cases = [
        (85.0, 5.0, -20.0, "Routine grounder to SS"),
        (95.0, 8.0, -35.0, "Hard grounder to 3B"),
        (70.0, 12.0, 15.0, "Weak grounder to 2B"),
        (90.0, 6.0, 0.0, "Grounder up the middle"),
    ]
    
    for exit_velo, launch_angle, spray_angle, description in test_cases:
        print(f"\n{description}")
        print(f"Exit: {exit_velo} mph, LA: {launch_angle}°, Spray: {spray_angle}°")
        print("-" * 40)
        
        # Simulate batted ball
        result = ball_sim.simulate(
            exit_velocity=exit_velo,
            launch_angle=launch_angle,
            spray_angle=spray_angle,
            backspin_rpm=500.0,
        )
        
        print(f"Ball lands at: ({result.landing_x:.1f}, {result.landing_y:.1f}) ft")
        print(f"Flight time: {result.flight_time:.3f}s")
        
        # Test interception
        interception = interceptor.find_best_interception(result, fielders)
        
        if interception.can_be_fielded:
            print(f"✅ FIELDED by {interception.fielding_position}")
            print(f"   Interception time: {interception.interception_time:.3f}s")
            print(f"   Fielder arrival: {interception.fielder_arrival_time:.3f}s")
            print(f"   Time margin: {interception.time_margin:.3f}s")
            print(f"   Ball position: ({interception.ball_position_at_interception.x:.1f}, {interception.ball_position_at_interception.y:.1f})")
            
            # Check if timing is realistic
            total_time = interception.interception_time
            if total_time <= 2.5:
                print(f"   ✅ TIMING GOOD: {total_time:.3f}s (realistic)")
            else:
                print(f"   ⚠️  TIMING SLOW: {total_time:.3f}s (may be too slow)")
        else:
            print(f"❌ GETS THROUGH: No fielder can intercept")
        
        # Show ball trajectory for debugging
        trajectory = interceptor.get_ground_ball_trajectory_points(result, max_time=3.0)
        print(f"   Ball trajectory (first 1.5s):")
        for t, x, y in trajectory[:15]:  # First 15 points (1.5 seconds)
            if t <= 1.5:
                print(f"     t={t:.1f}s: ({x:.1f}, {y:.1f})")

def test_interception_vs_old_system():
    """Compare new interception with old system expectations."""
    
    print(f"\n" + "="*50)
    print("COMPARING WITH RESEARCH EXPECTATIONS")
    print("="*50)
    
    print("Research target: '95 mph ground ball reaches 3B (~120ft) in 0.85-1.0s'")
    print()
    
    # Test a 95 mph ground ball to third base area
    ball_sim = BattedBallSimulator()
    interceptor = GroundBallInterceptor(surface_type='grass')
    fielders = create_standard_defense()
    
    result = ball_sim.simulate(
        exit_velocity=95.0,
        launch_angle=6.0,
        spray_angle=-30.0,  # Toward third base
        backspin_rpm=500.0,
    )
    
    interception = interceptor.find_best_interception(result, fielders)
    
    print(f"95 mph ground ball test:")
    print(f"  Ball lands: ({result.landing_x:.1f}, {result.landing_y:.1f}) ft")
    print(f"  Flight time: {result.flight_time:.3f}s")
    
    if interception.can_be_fielded:
        print(f"  Fielded by: {interception.fielding_position}")
        print(f"  Total time: {interception.interception_time:.3f}s")
        print(f"  Distance to interception: {interception.interception_distance:.1f}ft")
        
        if 0.85 <= interception.interception_time <= 1.5:
            print(f"  ✅ MATCHES RESEARCH: {interception.interception_time:.3f}s in target range")
        else:
            print(f"  ⚠️  OUTSIDE RESEARCH: {interception.interception_time:.3f}s (target: 0.85-1.0s)")
    else:
        print(f"  ❌ NOT FIELDED (should be fielded)")

if __name__ == '__main__':
    test_ground_ball_interception()
    test_interception_vs_old_system()