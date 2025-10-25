#!/usr/bin/env python3
"""
Test script for advanced AI pursuit strategies in fielding.
Tests the new trajectory prediction, OAC pursuit, and route optimization methods.
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from batted_ball.fielding import Fielder, FieldPosition
import math

def test_advanced_ai_pursuit():
    """Test the new advanced AI pursuit methods."""
    print("Testing Advanced AI Pursuit Strategies")
    print("=" * 50)
    
    # Create a high-rated right fielder (like the ones failing in the game log)
    right_fielder = Fielder(
        name="RF Test",
        position="outfield",
        sprint_speed=85,      # High speed
        acceleration=88,      # High acceleration
        reaction_time=90,     # Excellent reaction time
        arm_strength=82,      # Strong arm
        throwing_accuracy=85, # Good accuracy
        transfer_quickness=86,# Quick transfer
        fielding_range=90,    # Excellent range
        current_position=FieldPosition(280.0, 100.0, 0.0)  # Deep right field
    )
    
    print(f"Right Fielder Stats:")
    print(f"  Sprint Speed: {right_fielder.sprint_speed}")
    print(f"  Range: {right_fielder.fielding_range}")
    print(f"  Reaction: {right_fielder.reaction_time}")
    print(f"  Max Speed: {right_fielder.get_sprint_speed_fps():.2f} ft/s")
    print()
    
    # Simulate a challenging ball (like those missed in the game log)
    # Ball hit to right-center field gap - create trajectory arrays
    import numpy as np
    
    # Create a simple trajectory simulation for testing
    time_points = np.linspace(0.0, 5.0, 50)  # 5 seconds of flight
    positions = []
    velocities = []
    
    initial_pos = np.array([0.0, 0.0, 1.0])  # Home plate
    initial_vel = np.array([35.0, 25.0, 15.0])  # Toward right-center gap
    
    for t in time_points:
        # Simple ballistic trajectory with gravity
        pos = initial_pos + initial_vel * t + 0.5 * np.array([0, 0, -9.81]) * t**2
        vel = initial_vel + np.array([0, 0, -9.81]) * t
        
        # Stop if ball hits ground
        if pos[2] <= 0:
            pos[2] = 0
            vel = np.array([0, 0, 0])
            
        positions.append(pos)
        velocities.append(vel)
    
    positions = np.array(positions)
    velocities = np.array(velocities)
    
    ball_trajectory_data = {
        'position': positions,
        'velocity': velocities,
        'time': time_points
    }
    
    current_time = 1.5  # 1.5 seconds into flight
    
    print("Ball Trajectory Data:")
    current_idx = np.argmin(np.abs(time_points - current_time))
    print(f"  Current Position: {positions[current_idx]}")
    print(f"  Current Velocity: {velocities[current_idx]}")
    print(f"  Time Since Contact: {current_time} seconds")
    print()
    
    # Test 1: Optimal Intercept Point Calculation
    print("1. Testing Optimal Intercept Point Calculation:")
    try:
        intercept_point = right_fielder.calculate_optimal_intercept_point(
            ball_trajectory_data, 
            current_time=current_time
        )
        print(f"   Optimal Intercept Point: {intercept_point}")
        
        # Calculate distance to intercept
        current_pos = right_fielder.current_position
        distance = math.sqrt(
            (intercept_point[0] - current_pos.x)**2 + 
            (intercept_point[1] - current_pos.y)**2
        )
        print(f"   Distance to Intercept: {distance:.2f} m")
        
    except Exception as e:
        print(f"   ERROR: {e}")
        import traceback
        traceback.print_exc()
    
    print()
    
    # Test 2: OAC Pursuit Target (Advanced)
    print("2. Testing OAC Pursuit Target (Advanced):")
    try:
        pursuit_target = right_fielder.calculate_oac_pursuit_target_advanced(
            ball_trajectory_data,
            current_time=current_time
        )
        print(f"   OAC Pursuit Target: {pursuit_target}")
        
    except Exception as e:
        print(f"   ERROR: {e}")
        import traceback
        traceback.print_exc()
    
    print()
    
    # Test 3: Optimal Route Calculation
    print("3. Testing Optimal Route Calculation:")
    try:
        # Use the intercept point as target
        target_position = FieldPosition(200.0, 80.0, 0.0)  # Example target
        
        optimal_route = right_fielder.calculate_optimal_route(
            target_position,
            ball_trajectory_data  # Full trajectory data
        )
        print(f"   Optimal Route: {optimal_route}")
        
    except Exception as e:
        print(f"   ERROR: {e}")
        import traceback
        traceback.print_exc()
    
    print()
    print("Advanced AI Pursuit Test Complete!")

if __name__ == "__main__":
    test_advanced_ai_pursuit()