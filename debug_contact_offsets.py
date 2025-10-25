"""
Debug contact offset calculation to identify sources of degradation.
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__)))

from batted_ball.at_bat import AtBatSimulator
from batted_ball.player import Pitcher, Hitter
import numpy as np

def debug_contact_offsets():
    """Debug where the large contact offsets are coming from."""
    print("=== Contact Offset Debugging ===")
    
    pitcher = Pitcher("Debug Pitcher", velocity=85, command=75, stamina=80)
    hitter = Hitter("Debug Hitter", 
                   bat_speed=75, 
                   barrel_accuracy=80,  # High barrel accuracy
                   bat_control=80,      # High bat control
                   zone_discipline=70)
    
    simulator = AtBatSimulator(pitcher, hitter)
    
    print(f"Hitter barrel_accuracy: {hitter.barrel_accuracy}")
    print(f"Hitter bat_control: {hitter.bat_control}")
    
    # Test contact point offset calculation directly
    print(f"\n=== Direct Contact Point Offset Tests ===")
    test_locations = [
        (0.0, 0.0),    # Right down the middle
        (2.0, 1.0),    # Slightly off center
        (-3.0, -2.0),  # Edge of zone
    ]
    
    for i, location in enumerate(test_locations):
        print(f"\nTest {i+1}: Pitch location {location}")
        for j in range(5):  # Multiple samples
            h_offset, v_offset = hitter.get_contact_point_offset(location)
            total_offset = np.sqrt(h_offset**2 + v_offset**2)
            print(f"  Sample {j+1}: h_offset={h_offset:.3f}, v_offset={v_offset:.3f}, total={total_offset:.3f}")
    
    # Sample some full contact simulations to see all offset sources
    print(f"\n=== Full Contact Simulation Analysis ===")
    contact_count = 0
    offset_components = []
    
    # Try to get some contact examples
    for attempt in range(20):
        result = simulator.simulate_at_bat()
        if hasattr(result, 'batted_ball_result') and result.batted_ball_result:
            contact_count += 1
            bbr = result.batted_ball_result
            
            # Extract offset data
            offset_data = {
                'total_offset': bbr.get('contact_offset_total', 'N/A'),
                'exit_velocity': bbr['exit_velocity'],
                'collision_efficiency': bbr.get('collision_efficiency_q', 'N/A')
            }
            offset_components.append(offset_data)
            
            print(f"Contact {contact_count}:")
            print(f"  Total Offset: {offset_data['total_offset']:.3f} inches")
            print(f"  Exit Velocity: {offset_data['exit_velocity']:.1f} mph")
            print(f"  Collision Efficiency: {offset_data['collision_efficiency']:.3f}")
            
            if contact_count >= 10:  # Get 10 examples
                break
    
    if offset_components:
        # Analyze the distribution
        offsets = [oc['total_offset'] for oc in offset_components if isinstance(oc['total_offset'], (int, float))]
        exit_vels = [oc['exit_velocity'] for oc in offset_components]
        
        print(f"\n=== Summary of {len(offsets)} contacts ===")
        print(f"Average total offset: {sum(offsets)/len(offsets):.3f} inches")
        print(f"Range: {min(offsets):.3f} - {max(offsets):.3f} inches")
        print(f"Average exit velocity: {sum(exit_vels)/len(exit_vels):.1f} mph")
        
        # Count by quality
        good_contacts = len([o for o in offsets if o < 0.5])
        fair_contacts = len([o for o in offsets if 0.5 <= o < 1.0])
        poor_contacts = len([o for o in offsets if o >= 1.0])
        
        print(f"Contact quality distribution:")
        print(f"  Good (<0.5\"): {good_contacts} ({good_contacts/len(offsets)*100:.1f}%)")
        print(f"  Fair (0.5-1.0\"): {fair_contacts} ({fair_contacts/len(offsets)*100:.1f}%)")
        print(f"  Poor (>1.0\"): {poor_contacts} ({poor_contacts/len(offsets)*100:.1f}%)")

if __name__ == "__main__":
    debug_contact_offsets()