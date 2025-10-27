"""
Test script to verify proximity-based fielder assignment is working correctly.
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__)))

from batted_ball import FieldingSimulator, FieldPosition, FieldLayout
from batted_ball.play_simulation import create_standard_defense

def test_proximity_assignment():
    """Test that proximity-based assignment works better than zone-based."""
    
    # Create fielding simulator with standard positioning
    field_layout = FieldLayout()
    fielding_sim = FieldingSimulator(field_layout)
    
    # Add fielders in standard positions
    fielders = create_standard_defense()
    for pos_name, fielder in fielders.items():
        fielding_sim.add_fielder(pos_name, fielder)
    
    # Test case from your analysis: ball at (100, 300)
    # Zone system would assign to RF at (135, 234) = 166ft away
    # Proximity system should prefer CF at (0, 290) = 100ft away
    ball_position = FieldPosition(100, 300, 0)
    hang_time = 3.5  # seconds
    
    print("="*60)
    print("PROXIMITY-BASED FIELDER ASSIGNMENT TEST")
    print("="*60)
    
    print(f"\nTest ball position: ({ball_position.x}, {ball_position.y})")
    print(f"Hang time: {hang_time}s")
    
    # Get zone-based assignment (old method)
    zone_assignment = fielding_sim.field_layout.get_nearest_fielder_position(ball_position)
    print(f"\nZone-based assignment: {zone_assignment}")
    
    # Get proximity-based assignment (new method)
    proximity_assignment = fielding_sim.determine_responsible_fielder(ball_position, hang_time)
    print(f"Proximity-based assignment: {proximity_assignment}")
    
    # Show fielding probabilities for all fielders
    probabilities = fielding_sim.get_all_fielding_probabilities(ball_position, hang_time)
    
    print(f"\nFielding probabilities for all fielders:")
    for pos, prob in sorted(probabilities.items(), key=lambda x: x[1], reverse=True):
        if prob > 0:
            fielder = fielding_sim.fielders[pos]
            distance = fielder.current_position.distance_to(ball_position)
            time_needed = fielder.calculate_effective_time_to_position(ball_position)
            margin = hang_time - time_needed
            print(f"  {pos}: {prob:.3f} probability, {distance:.0f}ft away, " +
                  f"needs {time_needed:.2f}s (margin: {margin:.2f}s)")
    
    # Test another case: ball at (0, 350) - should clearly go to CF
    print("\n" + "-"*60)
    ball_position2 = FieldPosition(0, 350, 0)
    hang_time2 = 4.0
    
    print(f"\nTest ball position: ({ball_position2.x}, {ball_position2.y})")
    print(f"Hang time: {hang_time2}s")
    
    zone_assignment2 = fielding_sim.field_layout.get_nearest_fielder_position(ball_position2)
    proximity_assignment2 = fielding_sim.determine_responsible_fielder(ball_position2, hang_time2)
    
    print(f"\nZone-based assignment: {zone_assignment2}")
    print(f"Proximity-based assignment: {proximity_assignment2}")
    
    probabilities2 = fielding_sim.get_all_fielding_probabilities(ball_position2, hang_time2)
    print(f"\nFielding probabilities:")
    for pos, prob in sorted(probabilities2.items(), key=lambda x: x[1], reverse=True):
        if prob > 0:
            fielder = fielding_sim.fielders[pos]
            distance = fielder.current_position.distance_to(ball_position2)
            time_needed = fielder.calculate_effective_time_to_position(ball_position2)
            margin = hang_time2 - time_needed
            print(f"  {pos}: {prob:.3f} probability, {distance:.0f}ft away, " +
                  f"needs {time_needed:.2f}s (margin: {margin:.2f}s)")

if __name__ == "__main__":
    test_proximity_assignment()