"""Debug trajectory distance issues."""
import sys
sys.path.append('.')

from batted_ball import BattedBallSimulator
import numpy as np

def debug_trajectory_distances():
    """Debug why low launch angle balls are traveling too far."""
    
    print("DEBUGGING TRAJECTORY DISTANCES")
    print("="*50)
    
    # Test various launch angles to see distance vs angle relationship
    test_cases = [
        (85.0, 2.0, "Very low"),
        (85.0, 5.0, "Low"), 
        (85.0, 8.0, "Medium-low"),
        (85.0, 12.0, "Medium"),
        (85.0, 20.0, "Higher"),
    ]
    
    ball_sim = BattedBallSimulator()
    
    print(f"{'Description':12s} {'LA':>4s} {'Dist':>6s} {'Flight':>7s} {'Peak':>6s} {'Expected':>10s}")
    print("-" * 60)
    
    for exit_velo, launch_angle, description in test_cases:
        result = ball_sim.simulate(
            exit_velocity=exit_velo,
            launch_angle=launch_angle,
            spray_angle=0.0,
            backspin_rpm=500.0,  # Low backspin for ground balls
        )
        
        # Expected distances for ground balls
        if launch_angle <= 5.0:
            expected = "30-60 ft"
        elif launch_angle <= 10.0:
            expected = "60-100 ft"
        elif launch_angle <= 15.0:
            expected = "100-150 ft"
        else:
            expected = "150+ ft"
        
        print(f"{description:12s} {launch_angle:4.1f}° {result.distance:6.1f}ft {result.flight_time:6.3f}s {result.peak_height:5.1f}ft {expected:>10s}")
        
        if launch_angle <= 8.0 and result.distance > 100.0:
            print(f"  ⚠️  PROBLEM: {launch_angle}° ground ball traveling {result.distance:.1f}ft (too far!)")

def debug_real_ground_ball_physics():
    """Compare with real-world ground ball expectations."""
    
    print(f"\nREAL-WORLD GROUND BALL EXPECTATIONS")
    print("="*50)
    
    print("Research from 'Baseball Simulation Fielding Improvements.md':")
    print("- 95 mph ground ball travels ~120 ft to 3B in 0.85-1.00 seconds")
    print("- This implies the ball LANDS much closer to home and ROLLS to the fielder")
    print()
    
    print("Expected ground ball physics:")
    print("- 2-5° launch angle: Land 20-40 ft from home, roll 80-100 ft to fielder")
    print("- 6-10° launch angle: Land 40-80 ft from home, roll 40-80 ft to fielder") 
    print("- Total travel time to infielder: 0.8-1.5 seconds")
    print()
    
    print("Current simulation problems:")
    print("- 5° ground balls landing 113 ft from home (should be ~30 ft)")
    print("- Ground balls traveling as if they're line drives")
    print("- Need to check trajectory physics for low launch angles")

if __name__ == '__main__':
    debug_trajectory_distances()
    debug_real_ground_ball_physics()