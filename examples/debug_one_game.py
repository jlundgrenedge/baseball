#!/usr/bin/env python3

"""
Quick debug script to check one game and see what's happening with fielding.
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from batted_ball.game_simulation import GameSimulator, create_test_team

def debug_one_game():
    """Run one quick game with debug output."""
    print("DEBUG GAME TEST")
    print("=" * 40)
    
    # Create teams
    visitors = create_test_team("Debug Visitors", "average")
    home = create_test_team("Debug Home", "average")
    
    # Create game simulator
    simulator = GameSimulator(visitors, home, verbose=False)
    
    # Simulate just a few plays and check what happens
    try:
        final_state = simulator.simulate_game(num_innings=1)
        print(f"\nFINAL: {visitors.name} {final_state.away_score} - {final_state.home_score} {home.name}")
        print(f"Total outs: {final_state.away_outs + final_state.home_outs}")
        
        # Count play types
        hit_count = 0
        out_count = 0
        for event in simulator.play_by_play:
            if "TRIPLE" in event.description or "DOUBLE" in event.description or "HOME RUN" in event.description:
                hit_count += 1
            elif "out" in event.description.lower() or "catch" in event.description.lower():
                out_count += 1
        
        print(f"Recorded hits: {hit_count}")
        print(f"Recorded fielding outs: {out_count}")
        
    except KeyboardInterrupt:
        print("Interrupted")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    debug_one_game()