#!/usr/bin/env python3
"""Test advanced AI pursuit system against challenging fielding scenarios."""

from batted_ball.play_simulation import PlaySimulator
from batted_ball.fielding import Fielder, FieldPosition
from batted_ball.environment import Environment

def test_ai_pursuit():
    """Test the advanced AI pursuit system against original game log issues."""
    
    # Setup
    env = Environment()
    sim = PlaySimulator(env)
    
    # Create fielders with different skill levels and set positions
    elite_rf = Fielder(
        name='Elite RF',
        position='outfield',
        sprint_speed=90,
        fielding_range=90,
        reaction_time=90,
        arm_strength=85,
        current_position=FieldPosition(250, 25, 0)  # Right field starting position
    )
    avg_rf = Fielder(
        name='Average RF', 
        position='outfield',
        sprint_speed=50,
        fielding_range=50,
        reaction_time=50,
        arm_strength=50,
        current_position=FieldPosition(250, 25, 0)  # Right field starting position
    )
    poor_rf = Fielder(
        name='Poor RF',
        position='outfield', 
        sprint_speed=20,
        fielding_range=20,
        reaction_time=20,
        arm_strength=30,
        current_position=FieldPosition(250, 25, 0)  # Right field starting position
    )
    
    print("=== ADVANCED AI PURSUIT TESTING ===")
    print("Testing scenarios similar to original game log failures")
    print()
    
    # Test scenarios based on original game log
    scenarios = [
        {"name": "Original Problem Case", "distance": 300, "hang_time": 3.0},
        {"name": "Moderate Challenge", "distance": 250, "hang_time": 2.5},
        {"name": "Easier Play", "distance": 200, "hang_time": 2.0},
        {"name": "Extreme Challenge", "distance": 350, "hang_time": 3.5},
    ]
    
    fielders = [
        ("Elite RF", elite_rf),
        ("Average RF", avg_rf), 
        ("Poor RF", poor_rf)
    ]
    
    for scenario in scenarios:
        print(f"--- {scenario['name']} ---")
        print(f"Distance: {scenario['distance']} ft, Hang Time: {scenario['hang_time']}s")
        print()
        
        for name, fielder in fielders:
            # Set up ball position at specified distance
            ball_pos = FieldPosition(scenario['distance'], 0, 0)
            
            # Use the fielder's attempt_fielding method
            result = fielder.attempt_fielding(
                ball_position=ball_pos,
                ball_arrival_time=scenario['hang_time']
            )
            
            # Extract timing information
            arrival_time = result.fielder_arrival_time
            ball_time = result.ball_arrival_time
            margin = arrival_time - ball_time
            status = 'CATCH' if result.success else 'MISS'
            improvement = margin < -5.0  # Better than original 8-9s deficits
            
            print(f"{name}: arrival {arrival_time:.2f}s vs ball {ball_time:.2f}s")
            print(f"  → Margin: {margin:.2f}s ({status})")
            if improvement:
                print(f"  ✓ MAJOR IMPROVEMENT over original 8-9s deficits!")
            elif margin < -8.0:
                print(f"  ⚠️  Still challenging but better than worst cases")
            print()
        
        print()

if __name__ == "__main__":
    test_ai_pursuit()