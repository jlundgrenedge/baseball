#!/usr/bin/env python3
"""
Test advanced AI pursuit with detailed fielding breakdown to compare with original game log.
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from batted_ball.game_simulation import GameSimulator

def test_detailed_fielding():
    """Run a game with detailed fielding output to see AI pursuit improvements."""
    print("ADVANCED AI PURSUIT FIELDING TEST")
    print("=" * 50)
    print("Testing against the catastrophic fielding failures from your game log...")
    print("Previously: Right fielders missing balls with 8-9 second deficits")
    print("Now: Advanced AI pursuit with trajectory prediction and route optimization")
    print()
    
    # Create game
    game = GameSimulator()
    
    # Set up teams (simple for testing)
    game.set_away_team("Visitors")
    game.set_home_team("Home Team") 
    
    print("Simulating 1 inning with detailed fielding breakdown...")
    print()
    
    # Run one inning to see detailed fielding results
    try:
        game.start_game()
        game.simulate_half_inning(is_top=True)
        
        print(f"\nGame completed successfully!")
        print(f"Score: Visitors {game.game_state.away_score} - {game.game_state.home_score} Home Team")
        print(f"Hits: {game.game_state.total_hits}")
        
        print("\n✅ Advanced AI Pursuit integration successful!")
        print("Compare this fielding performance to your original game log.")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_detailed_fielding()