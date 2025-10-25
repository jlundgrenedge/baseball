#!/usr/bin/env python3

"""
Simple test to check fielding mechanics.
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from batted_ball.fielding import FieldingSimulator, FieldPosition
from batted_ball.field_layout import FieldLayout

def test_fielding_basics():
    """Test basic fielding mechanics."""
    print("FIELDING BASICS TEST")
    print("=" * 40)
    
    # Create fielding simulator
    field_layout = FieldLayout()
    fielding_sim = FieldingSimulator(field_layout)
    
    # Test a few ball positions
    test_positions = [
        FieldPosition(150, 0, 0),      # Straight center field, shallow
        FieldPosition(250, 0, 0),      # Straight center field, medium  
        FieldPosition(350, 0, 0),      # Straight center field, deep
        FieldPosition(90, 90, 0),      # Right field line
        FieldPosition(150, -150, 0),   # Left center gap
    ]
    
    for i, pos in enumerate(test_positions):
        print(f"\nTest {i+1}: Ball at ({pos.x:.0f}, {pos.y:.0f})")
        
        # Who is responsible?
        responsible = fielding_sim.determine_responsible_fielder(pos)
        fielder = fielding_sim.fielders[responsible]
        
        print(f"  Responsible: {responsible}")
        print(f"  Fielder position: ({fielder.current_position.x:.0f}, {fielder.current_position.y:.0f})")
        
        # How long to get there?
        time_to_ball = fielder.calculate_time_to_position(pos)
        print(f"  Time to reach: {time_to_ball:.2f}s")
        
        # What about a typical flight time?
        flight_time = 3.0  # 3 seconds is typical for a fly ball
        print(f"  Assumed flight time: {flight_time:.2f}s")
        print(f"  Can field: {time_to_ball <= flight_time}")

if __name__ == "__main__":
    test_fielding_basics()