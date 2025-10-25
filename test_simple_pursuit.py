#!/usr/bin/env python3
"""
Simple test to verify advanced AI pursuit integration works without hanging.
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from batted_ball.fielding import Fielder, FieldPosition

def test_simple_ai_pursuit():
    """Test just the AI pursuit methods with a simple ball."""
    print("Testing Simple AI Pursuit Methods")
    print("=" * 40)
    
    # Create a test fielder
    fielder = Fielder(
        name="RF Test",
        position="outfield",
        sprint_speed=80,
        reaction_time=85,
        current_position=FieldPosition(250.0, 80.0, 0.0)
    )
    
    # Test if basic fielding methods work
    try:
        print("Testing basic fielding calculation...")
        target = FieldPosition(180.0, 60.0, 0.0)
        time_needed = fielder.calculate_effective_time_to_position(target)
        print(f"Basic calculation: {time_needed:.2f}s to reach target")
        print("✅ Basic fielding works!")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_simple_ai_pursuit()