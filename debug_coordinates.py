"""Debug coordinate system issues."""
import sys
sys.path.append('.')

from batted_ball import BattedBallSimulator
from batted_ball.ground_ball_physics import GroundBallSimulator
import numpy as np

def debug_coordinates():
    """Debug coordinate system issues in ground ball physics."""
    
    print("DEBUGGING COORDINATE SYSTEM")
    print("="*50)
    
    # Create a simple test case - ball hit straight up the middle
    ball_sim = BattedBallSimulator()
    
    result = ball_sim.simulate(
        exit_velocity=85.0,
        launch_angle=5.0,
        spray_angle=0.0,  # Straight up the middle
        backspin_rpm=500.0,
    )
    
    print(f"Batted ball trajectory:")
    print(f"  Exit velocity: 85.0 mph")
    print(f"  Launch angle: 5.0°") 
    print(f"  Spray angle: 0.0° (straight up middle)")
    print(f"  Landing position: ({result.landing_x:.1f}, {result.landing_y:.1f}) ft")
    print(f"  Final position vector: {result.position[-1]} m")
    print(f"  Final velocity vector: {result.velocity[-1]} m/s")
    
    # Convert to check coordinate system
    final_pos_ft = result.position[-1] * 3.28084  # m to ft
    print(f"  Final position in feet: ({final_pos_ft[0]:.1f}, {final_pos_ft[1]:.1f}, {final_pos_ft[2]:.1f})")
    
    # Now check what ground ball simulator does with this
    ground_sim = GroundBallSimulator()
    
    # Check coordinates at different points in ground ball simulation
    print(f"\nGround ball simulation input:")
    landing_velocity = result.velocity[-1]  # m/s
    landing_position = result.position[-1]  # m
    
    from batted_ball.constants import MS_TO_MPH, METERS_TO_FEET
    
    vx = landing_velocity[0] * MS_TO_MPH
    vy = landing_velocity[1] * MS_TO_MPH  
    vz = landing_velocity[2] * MS_TO_MPH
    
    x0 = landing_position[0] * METERS_TO_FEET
    y0 = landing_position[1] * METERS_TO_FEET
    
    print(f"  Landing velocity: ({vx:.1f}, {vy:.1f}, {vz:.1f}) mph")
    print(f"  Landing position: ({x0:.1f}, {y0:.1f}) ft")
    
    # Test a target at shortstop position (should be close!)
    target_x, target_y = 0.0, 127.0  # Straight up middle at shortstop depth
    
    print(f"\nTarget position: ({target_x:.1f}, {target_y:.1f}) ft")
    print(f"Distance from landing to target: {np.sqrt((target_x - x0)**2 + (target_y - y0)**2):.1f} ft")
    
    # This should be a short distance for a ball hit straight up the middle!
    
    # Now run the ground ball simulation
    ground_result = ground_sim.simulate_from_trajectory(result, target_position=(target_x, target_y))
    
    print(f"\nGround ball result:")
    print(f"  Time to target: {ground_result.time_to_target:.3f}s")
    print(f"  Total distance traveled: {ground_result.total_distance:.1f}ft")
    
    if ground_result.time_to_target > 2.0:
        print(f"  ⚠️  PROBLEM: Time too long for a {np.sqrt((target_x - x0)**2 + (target_y - y0)**2):.1f}ft ground ball")

if __name__ == '__main__':
    debug_coordinates()