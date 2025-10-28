"""
Test outfield ball retrieval timing improvements.
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from batted_ball.at_bat import AtBatSimulator
from batted_ball.player import Pitcher, Hitter
from batted_ball.attributes import PitcherAttributes, HitterAttributes

def test_outfield_retrieval_timing():
    """Test if outfield balls are now retrieved more quickly."""
    
    # Create moderate hitter and pitcher
    hitter = Hitter(
        name="Test Hitter",
        attributes_v2=HitterAttributes(
            BAT_SPEED=60000,      # Above average bat speed
            BARREL_ACCURACY=55000,  # Moderate contact ability
            TIMING_PRECISION=60000,
            ATTACK_ANGLE_CONTROL=50000
        )
    )
    
    pitcher = Pitcher(
        name="Test Pitcher",
        attributes_v2=PitcherAttributes(
            RAW_VELOCITY_CAP=60000,  # Above average velocity
            COMMAND=60000,           # Good command
            SPIN_RATE_CAP=50000,     # Average spin
            STAMINA=70000            # Good stamina
        )
    )
    
    # Simulate many at-bats to find outfield scenarios
    simulator = AtBatSimulator(pitcher, hitter)
    outfield_retrievals = []
    all_retrieval_events = []
    
    print("Testing outfield ball retrieval timing...")
    
    for i in range(500):  # More at-bats to find outfield plays
        result = simulator.simulate_at_bat()
        
        # Look for ANY ball-related events first
        if hasattr(result, 'play_result') and result.play_result:
            events = result.play_result.events
            for event in events:
                # Look for any ball handling events
                if any(keyword in event.description.lower() for keyword in 
                       ['ball', 'caught', 'retrieved', 'intercepted', 'fielded']):
                    
                    all_retrieval_events.append((event.time, event.description))
                    
                    # Check if this looks like an outfield play (including catches)
                    if ("right_field" in event.description or 
                        "left_field" in event.description or 
                        "center_field" in event.description):
                        
                        retrieval_time = event.time
                        outfield_retrievals.append((retrieval_time, event.description))
                        
                        print(f"  At-bat {i+1}: {event.description}")
                        
        if len(outfield_retrievals) >= 10:  # Get enough samples
            break
    
    print(f"\nTotal retrieval events found: {len(all_retrieval_events)}")
    if len(all_retrieval_events) > 0:
        print("Sample retrieval events:")
        for i, (time, desc) in enumerate(all_retrieval_events[:10]):
            print(f"  {i+1}. {time:.2f}s: {desc}")
    
    if outfield_retrievals:
        times = [t for t, desc in outfield_retrievals]
        avg_time = sum(times) / len(times)
        min_time = min(times)
        max_time = max(times)
        
        print(f"\nOutfield Retrieval Time Analysis:")
        print(f"  Samples: {len(outfield_retrievals)}")
        print(f"  Average: {avg_time:.2f}s")
        print(f"  Range: {min_time:.2f}s - {max_time:.2f}s")
        print(f"  Expected: 1.5-2.5s for most plays")
        
        if avg_time < 3.0:
            print("✅ IMPROVEMENT: Average retrieval time is much better!")
        else:
            print("❌ STILL SLOW: Average retrieval time still high")
    else:
        print("No outfield retrieval scenarios found in test")

if __name__ == "__main__":
    test_outfield_retrieval_timing()