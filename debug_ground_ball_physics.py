"""Debug detailed ground ball physics."""
import sys
sys.path.append('.')

from batted_ball import BattedBallSimulator
from batted_ball.ground_ball_physics import GroundBallSimulator
from batted_ball.field_layout import FieldPosition
import numpy as np

def debug_ground_ball_physics():
    """Debug the ground ball physics simulation."""
    
    # Create simulators
    ball_sim = BattedBallSimulator()
    ground_sim = GroundBallSimulator(surface_type='grass')
    
    # Test a typical ground ball
    print("DEBUGGING GROUND BALL PHYSICS")
    print("="*50)
    
    # 85 mph, 5° launch angle ground ball
    result = ball_sim.simulate(
        exit_velocity=85.0,
        launch_angle=5.0,
        spray_angle=-20.0,
        backspin_rpm=500.0,
        fast_mode=False
    )
    
    print(f"Batted ball result:")
    print(f"  Exit velocity: 85.0 mph")
    print(f"  Launch angle: 5.0°")
    print(f"  Flight time: {result.flight_time:.3f}s")
    print(f"  Distance: {result.distance:.1f}ft")
    print(f"  Peak height: {result.peak_height:.1f}ft")
    print(f"  Landing velocity: {np.linalg.norm(result.velocity[-1]) * 2.237:.1f} mph")  # m/s to mph
    print(f"  Landing position: ({result.landing_x:.1f}, {result.landing_y:.1f})")
    
    # Test target positions at different distances
    test_targets = [
        (68.0, 18.0),   # Second base position
        (90.0, 90.0),   # First base
        (0.0, 127.0),   # Straight to center at shortstop depth
    ]
    
    for target_x, target_y in test_targets:
        print(f"\nTesting ground ball to target: ({target_x:.1f}, {target_y:.1f})")
        
        # Simulate ground ball to this target
        ground_result = ground_sim.simulate_from_trajectory(
            result, 
            target_position=(target_x, target_y)
        )
        
        print(f"  Time to target: {ground_result.time_to_target:.3f}s")
        print(f"  Total distance: {ground_result.total_distance:.1f}ft")
        print(f"  Rolling start time: {ground_result.rolling_start_time:.3f}s")
        print(f"  Number of bounces: {len(ground_result.bounces)}")
        
        if ground_result.time_to_target > 2.0:
            print(f"  ⚠️  SLOW: > 2.0s to reach target")
        else:
            print(f"  ✅ OK: Reasonable timing")
            
        # Show some trajectory points
        if len(ground_result.trajectory_points) > 5:
            print(f"  Sample trajectory points:")
            for i in range(0, min(len(ground_result.trajectory_points), 10), 2):
                t, x, y, z = ground_result.trajectory_points[i]
                print(f"    t={t:.2f}s: ({x:.1f}, {y:.1f}, {z:.1f})")

def debug_ground_ball_classification():
    """Test if ground balls are being classified correctly."""
    
    print("\nDEBUGGING GROUND BALL CLASSIFICATION")
    print("="*50)
    
    # Test cases with known expected classifications
    test_cases = [
        (85.0, 2.0, "Definitely ground ball"),
        (85.0, 5.0, "Should be ground ball"),
        (85.0, 8.0, "Borderline ground ball"),
        (85.0, 15.0, "Borderline line drive"),
        (85.0, 25.0, "Definitely line drive"),
    ]
    
    from batted_ball.play_simulation import PlaySimulator
    play_sim = PlaySimulator()
    
    ball_sim = BattedBallSimulator()
    
    for exit_velo, launch_angle, description in test_cases:
        result = ball_sim.simulate(
            exit_velocity=exit_velo,
            launch_angle=launch_angle,
            spray_angle=0.0,
            backspin_rpm=500.0,
        )
        
        # Use the play simulator's classification logic
        landing_pos, hang_time, is_air_ball = play_sim._analyze_batted_ball(result)
        
        classification = "Air ball" if is_air_ball else "Ground ball"
        
        print(f"{description:25s}: LA={launch_angle:4.1f}°, PH={result.peak_height:4.1f}ft -> {classification}")
        
        if launch_angle <= 8.0 and is_air_ball:
            print(f"  ⚠️  MISCLASSIFIED: Should be ground ball!")
        elif launch_angle >= 20.0 and not is_air_ball:
            print(f"  ⚠️  MISCLASSIFIED: Should be air ball!")

if __name__ == '__main__':
    debug_ground_ball_physics()
    debug_ground_ball_classification()