"""
Test cases where proximity-based and zone-based assignment should differ significantly.
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__)))

from batted_ball import FieldingSimulator, FieldPosition, FieldLayout
from batted_ball.play_simulation import create_standard_defense

def test_assignment_differences():
    """Test cases where proximity-based assignment differs from zone-based."""
    
    # Create fielding simulator
    field_layout = FieldLayout()
    fielding_sim = FieldingSimulator(field_layout)
    
    fielders = create_standard_defense()
    for pos_name, fielder in fielders.items():
        fielding_sim.add_fielder(pos_name, fielder)
    
    # Print fielder positions for reference
    print("FIELDER STARTING POSITIONS:")
    for pos_name, fielder in fielding_sim.fielders.items():
        pos = fielder.current_position
        print(f"  {pos_name}: ({pos.x:.0f}, {pos.y:.0f})")
    
    print("\n" + "="*70)
    print("TESTING CASES WHERE ASSIGNMENTS SHOULD DIFFER")
    print("="*70)
    
    # Test case 1: Ball between CF and RF but closer to CF
    test_cases = [
        {
            "name": "Ball between CF and RF, closer to CF",
            "position": FieldPosition(75, 290, 0),
            "hang_time": 3.0,
            "expected_zone": "right_field",
            "expected_proximity": "center_field"
        },
        {
            "name": "Ball between CF and LF, closer to CF", 
            "position": FieldPosition(-75, 290, 0),
            "hang_time": 3.0,
            "expected_zone": "left_field",
            "expected_proximity": "center_field"
        },
        {
            "name": "Deep ball slightly right of center",
            "position": FieldPosition(30, 350, 0),
            "hang_time": 4.0,
            "expected_zone": "center_field",
            "expected_proximity": "center_field"
        },
        {
            "name": "Ball at gap edge, shorter hang time",
            "position": FieldPosition(100, 250, 0),
            "hang_time": 2.5,
            "expected_zone": "right_field", 
            "expected_proximity": "right_field"  # RF might still be closer with short time
        }
    ]
    
    for i, case in enumerate(test_cases, 1):
        print(f"\nTest Case {i}: {case['name']}")
        print(f"Ball position: ({case['position'].x}, {case['position'].y})")
        print(f"Hang time: {case['hang_time']}s")
        
        # Get assignments
        zone_assignment = fielding_sim.field_layout.get_nearest_fielder_position(case['position'])
        proximity_assignment = fielding_sim.determine_responsible_fielder(case['position'], case['hang_time'])
        
        print(f"Zone-based: {zone_assignment}")
        print(f"Proximity-based: {proximity_assignment}")
        
        # Show top 3 fielding probabilities
        probabilities = fielding_sim.get_all_fielding_probabilities(case['position'], case['hang_time'])
        top_fielders = sorted(probabilities.items(), key=lambda x: x[1], reverse=True)[:3]
        
        print("Top fielding candidates:")
        for pos, prob in top_fielders:
            if prob > 0:
                fielder = fielding_sim.fielders[pos]
                distance = fielder.current_position.distance_to(case['position'])
                time_needed = fielder.calculate_effective_time_to_position(case['position'])
                margin = case['hang_time'] - time_needed
                print(f"  {pos}: {prob:.3f} prob, {distance:.0f}ft, margin: {margin:.2f}s")
        
        # Check if assignment changed
        if zone_assignment != proximity_assignment:
            print(f"✅ ASSIGNMENT CHANGED: {zone_assignment} → {proximity_assignment}")
        else:
            print(f"⚪ No change: {zone_assignment}")
        
        print("-" * 50)

if __name__ == "__main__":
    test_assignment_differences()