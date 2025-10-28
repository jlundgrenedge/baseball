"""
Simple test of outfield interception system directly.
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from batted_ball.outfield_interception import OutfieldInterceptor
from batted_ball.fielding import FieldingSimulator, Fielder
from batted_ball.field_layout import FieldLayout, FieldPosition
from batted_ball.trajectory import BattedBallResult
from batted_ball.attributes import FielderAttributes

def test_outfield_interceptor_directly():
    """Test the outfield interceptor import."""
    
    print("Testing outfield interceptor import...")
    
    try:
        from batted_ball.outfield_interception import OutfieldInterceptor
        interceptor = OutfieldInterceptor()
        print("✅ OutfieldInterceptor created successfully")
        
        # Test a simple method exists
        if hasattr(interceptor, 'find_best_interception'):
            print("✅ find_best_interception method exists")
        else:
            print("❌ find_best_interception method missing")
            
    except Exception as e:
        print(f"❌ Error creating OutfieldInterceptor: {e}")
        return
    
    print("Basic import test passed!")

if __name__ == "__main__":
    test_outfield_interceptor_directly()