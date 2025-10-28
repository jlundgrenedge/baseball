"""Debug ground ball interception issues."""
import sys
sys.path.append('.')

from batted_ball import BattedBallSimulator
from batted_ball.ground_ball_interception import GroundBallInterceptor
from batted_ball import create_standard_defense
import numpy as np

def debug_ground_ball_basics():
    """Debug basic ground ball trajectory."""
    
    print("DEBUGGING GROUND BALL TRAJECTORY")
    print("="*50)
    
    # Test simple ground ball
    ball_sim = BattedBallSimulator()
    result = ball_sim.simulate(
        exit_velocity=90.0,
        launch_angle=6.0,
        spray_angle=0.0,  # Straight
        backspin_rpm=500.0,
    )
    
    print(f"Basic ground ball (90 mph, 6°, straight):")
    print(f"  Landing position: ({result.landing_x:.1f}, {result.landing_y:.1f}) ft")
    print(f"  Flight time: {result.flight_time:.3f}s")
    print(f"  Peak height: {result.peak_height:.1f} ft")
    print()
    
    # Check trajectory points directly
    print("Trajectory points (from BattedBallResult):")
    if hasattr(result, 'trajectory_x') and len(result.trajectory_x) > 0:
        for i in range(0, min(10, len(result.trajectory_x))):
            t = i * 0.1  # Assuming 0.1s intervals
            x = result.trajectory_x[i]
            y = result.trajectory_y[i]
            z = result.trajectory_z[i]
            print(f"  t={t:.1f}s: ({x:.1f}, {y:.1f}, {z:.1f})")
    else:
        print("  No trajectory data in result")
    
    print()
    
    # Test ground ball interception calculation
    interceptor = GroundBallInterceptor(surface_type='grass')
    trajectory_points = interceptor.get_ground_ball_trajectory_points(result, max_time=2.0)
    
    print("Ground ball rolling trajectory (from interception system):")
    for i, (t, x, y) in enumerate(trajectory_points[:10]):
        print(f"  t={t:.1f}s: ({x:.1f}, {y:.1f})")
    
    print()
    
    # Check fielder positions
    fielders_dict = create_standard_defense()
    fielders = list(fielders_dict.values())
    print("Fielder positions:")
    for position, fielder in fielders_dict.items():
        print(f"  {position}: ({fielder.x:.1f}, {fielder.y:.1f})")

def debug_interception_calculation():
    """Debug the interception calculation."""
    
    print("\nDEBUGGING INTERCEPTION CALCULATION")
    print("="*50)
    
    # Simple test case
    ball_sim = BattedBallSimulator()
    result = ball_sim.simulate(
        exit_velocity=85.0,
        launch_angle=5.0,
        spray_angle=-20.0,  # Toward SS area
        backspin_rpm=500.0,
    )
    
    interceptor = GroundBallInterceptor(surface_type='grass')
    fielders_dict = create_standard_defense()
    fielders = list(fielders_dict.values())
    
    # Find shortstop
    shortstop = None
    for position, fielder in fielders_dict.items():
        if position == 'shortstop':
            shortstop = fielder
            break
    
    if shortstop is None:
        print("ERROR: No shortstop found")
        return
    
    print(f"Ball: lands at ({result.landing_x:.1f}, {result.landing_y:.1f})")
    print(f"Shortstop: positioned at ({shortstop.x:.1f}, {shortstop.y:.1f})")
    print()
    
    # Test individual fielder interception
    single_result = interceptor._calculate_fielder_interception(result, shortstop)
    
    print(f"Shortstop interception analysis:")
    print(f"  Can intercept: {single_result.can_intercept}")
    if single_result.can_intercept:
        print(f"  Interception time: {single_result.interception_time:.3f}s")
        print(f"  Ball position: ({single_result.ball_x:.1f}, {single_result.ball_y:.1f})")
        print(f"  Fielder travel distance: {single_result.fielder_distance:.1f}ft")
        print(f"  Time margin: {single_result.time_margin:.3f}s")
    else:
        print(f"  Reason: Cannot reach in time")
    
    # Test all fielders
    interception = interceptor.find_best_interception(result, fielders)
    print(f"\nBest interception result:")
    print(f"  Can be fielded: {interception.can_be_fielded}")
    if interception.can_be_fielded:
        print(f"  Best fielder: {interception.fielding_position}")
        print(f"  Time: {interception.interception_time:.3f}s")

def test_coordinate_system():
    """Test if coordinate system is correct."""
    
    print("\nTESTING COORDINATE SYSTEM")
    print("="*50)
    
    # Test ball hit straight up the middle
    ball_sim = BattedBallSimulator()
    result = ball_sim.simulate(
        exit_velocity=90.0,
        launch_angle=6.0,
        spray_angle=0.0,  # Straight up middle
        backspin_rpm=500.0,
    )
    
    print(f"Ball hit straight up middle (spray_angle=0°):")
    print(f"  Should land near x=0 (up the middle)")
    print(f"  Actually lands at: ({result.landing_x:.1f}, {result.landing_y:.1f})")
    print()
    
    # Test ball hit to left field
    result_left = ball_sim.simulate(
        exit_velocity=90.0,
        launch_angle=6.0,
        spray_angle=45.0,  # Left field
        backspin_rpm=500.0,
    )
    
    print(f"Ball hit to left field (spray_angle=45°):")
    print(f"  Should land at negative x (left field)")
    print(f"  Actually lands at: ({result_left.landing_x:.1f}, {result_left.landing_y:.1f})")
    print()
    
    # Test ball hit to right field
    result_right = ball_sim.simulate(
        exit_velocity=90.0,
        launch_angle=6.0,
        spray_angle=-45.0,  # Right field
        backspin_rpm=500.0,
    )
    
    print(f"Ball hit to right field (spray_angle=-45°):")
    print(f"  Should land at positive x (right field)")
    print(f"  Actually lands at: ({result_right.landing_x:.1f}, {result_right.landing_y:.1f})")

if __name__ == '__main__':
    debug_ground_ball_basics()
    debug_interception_calculation()
    test_coordinate_system()