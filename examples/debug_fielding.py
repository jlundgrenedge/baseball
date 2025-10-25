#!/usr/bin/env python3

"""
Debug script to understand why fielding logic isn't working.
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from batted_ball.game_simulation import GameSimulator, create_test_team

def debug_single_play():
    """Debug a single play to see what's happening."""
    print("FIELDING DEBUG ANALYSIS")
    print("=" * 50)
    
    # Create simple teams
    visitors = create_test_team("Debug Visitors")
    home = create_test_team("Debug Home")
    
    # Create game simulator
    simulator = GameSimulator(visitors, home)
    
    # Get first batter and pitcher
    batter = visitors.hitters[0]
    pitcher = home.pitchers[0]
    
    print(f"Batter: {batter.name} (bat_speed: {batter.bat_speed})")
    print(f"Pitcher: {pitcher.name} (velocity: {pitcher.velocity})")
    print()
    
    # Simulate a few at-bats with detailed output
    for i in range(5):
        print(f"\n--- At-Bat {i+1} ---")
        
        # Get at-bat result
        from batted_ball.at_bat import AtBatSimulator
        at_bat_sim = AtBatSimulator(pitcher, batter)
        at_bat_result = at_bat_sim.simulate_at_bat()
        
        if at_bat_result.outcome in ['SINGLE', 'DOUBLE', 'TRIPLE', 'HOME_RUN']:
            # Get batted ball details
            trajectory = at_bat_result.batted_ball_result
            
            if trajectory:
                print(f"Exit Velocity: {trajectory.exit_velocity:.1f} mph")
                print(f"Launch Angle: {trajectory.launch_angle:.1f}°")
                print(f"Distance: {trajectory.distance:.0f} ft")
                print(f"Peak Height: {trajectory.peak_height:.1f} ft")
                print(f"Flight Time: {trajectory.flight_time:.2f} s")
                print(f"Landing: ({trajectory.landing_x:.0f}, {trajectory.landing_y:.0f})")
                
                # Analyze what the fielding logic would see
                from batted_ball.play_simulation import PlaySimulator
                from batted_ball.fielding import FieldingSimulator
                from batted_ball.baserunning import BaserunningSimulator
                
                fielding_sim = FieldingSimulator()
                baserunning_sim = BaserunningSimulator()
                play_sim = PlaySimulator(fielding_sim, baserunning_sim)
                
                # Check if it's an air ball
                _, _, is_air_ball = play_sim._analyze_batted_ball(trajectory)
                print(f"Air ball: {is_air_ball}")
                
                # Check fielding time
                from batted_ball.fielding import FieldPosition
                ball_position = FieldPosition(trajectory.landing_x, trajectory.landing_y, 0.0)
                responsible_position = fielding_sim.determine_responsible_fielder(ball_position)
                fielder = fielding_sim.fielders[responsible_position]
                
                fielder_time = fielder.calculate_time_to_position(ball_position)
                ball_time = trajectory.flight_time
                
                print(f"Responsible fielder: {responsible_position}")
                print(f"Fielder time: {fielder_time:.2f}s")
                print(f"Ball time: {ball_time:.2f}s")
                print(f"Can field: {fielder_time <= ball_time}")
        
        print(f"Result: {at_bat_result.outcome}")

if __name__ == "__main__":
    debug_single_play()