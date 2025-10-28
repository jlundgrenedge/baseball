"""
Test outfield timing by running a complete game simulation.
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from batted_ball import GameSimulator, create_test_team

def test_outfield_timing_via_game():
    """Test outfield timing through complete game simulation."""
    
    print("Testing outfield timing via complete game simulation...")
    
    # Create test teams
    away_team = create_test_team("Test Away", "average")
    home_team = create_test_team("Test Home", "average")
    
    # Create game simulator (this should use complete play simulation)
    simulator = GameSimulator(away_team, home_team, verbose=True)
    
    # Override stdout to capture the debug output
    import io
    from contextlib import redirect_stdout
    
    captured_output = io.StringIO()
    
    try:
        with redirect_stdout(captured_output):
            final_state = simulator.simulate_game(num_innings=3)
        
        output = captured_output.getvalue()
        
        # Look for our debug messages in the output
        lines = output.split('\n')
        ball_handling_events = []
        debug_messages = []
        
        for line in lines:
            if 'DEBUG:' in line:
                debug_messages.append(line.strip())
            if any(keyword in line.lower() for keyword in ['retrieved', 'caught', 'ball']):
                ball_handling_events.append(line.strip())
        
        print(f"Debug messages found: {len(debug_messages)}")
        for msg in debug_messages[:10]:  # Show first 10
            print(f"  {msg}")
        
        print(f"\nBall handling events found: {len(ball_handling_events)}")
        for event in ball_handling_events[:10]:  # Show first 10
            print(f"  {event}")
            
        print(f"\nGame completed - Final score in game state")
        
    except Exception as e:
        output = captured_output.getvalue()
        print(f"Error during game simulation: {e}")
        if output:
            print("Captured output:")
            print(output[:1000])  # First 1000 chars

if __name__ == "__main__":
    test_outfield_timing_via_game()