"""
Debug what types of at-bat outcomes we're getting.
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from batted_ball.at_bat import AtBatSimulator
from batted_ball.player import Pitcher, Hitter
from batted_ball.attributes import PitcherAttributes, HitterAttributes

def debug_at_bat_outcomes():
    """Debug what outcomes we're getting from at-bats."""
    
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
    
    # Simulate at-bats and collect outcomes
    simulator = AtBatSimulator(pitcher, hitter)
    outcomes = {}
    
    print("Analyzing at-bat outcomes...")
    
    for i in range(100):
        result = simulator.simulate_at_bat()
        
        # Count outcome types
        if hasattr(result, 'outcome'):
            outcome_type = str(result.outcome)
            outcomes[outcome_type] = outcomes.get(outcome_type, 0) + 1
        
        # Look for any play events - both successful and detailed
        if hasattr(result, 'play_result') and result.play_result:
            events = result.play_result.events
            
            if i < 5 or len(events) > 0:  # Show first 5 and any with events
                print(f"At-bat {i+1} outcome: {result.outcome}")
                if len(events) > 0:
                    print("  Events:")
                    for event in events:
                        print(f"    {event.time:.2f}s: {event.description}")
                else:
                    print("  No events recorded")
                print()
        
        # Track events separately
        if hasattr(result, 'play_result') and result.play_result and len(result.play_result.events) > 0:
            if i >= 10:  # Don't process beyond first 10 that have events
                break
    
    print("Outcome Summary:")
    for outcome, count in sorted(outcomes.items()):
        print(f"  {outcome}: {count}")

if __name__ == "__main__":
    debug_at_bat_outcomes()