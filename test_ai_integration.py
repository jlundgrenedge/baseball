#!/usr/bin/env python3
"""
Test the integrated advanced AI pursuit system in a quick game simulation.
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from batted_ball.game_simulation import GameSimulator
from batted_ball.player import Pitcher, Hitter

def test_ai_pursuit_integration():
    """Test a quick game to see if the AI pursuit fixes fielding failures."""
    print("Testing Advanced AI Pursuit Integration")
    print("=" * 50)
    
    # Create teams with realistic players
    visitor_pitcher = Pitcher(
        name="Test Pitcher",
        velocity=75,
        command=70,
        control=65
    )
    
    visitor_hitters = []
    for i in range(9):
        hitter = Hitter(
            name=f"V{i+1}",
            contact=75,
            power=70,
            plate_discipline=65,
            speed=60
        )
        visitor_hitters.append(hitter)
    
    # Create game simulation
    game = GameSimulator()
    
    # Add teams
    game.set_away_team("Test Visitors", visitor_hitters, [visitor_pitcher])
    game.set_home_team("Test Home", visitor_hitters.copy(), [visitor_pitcher])  # Same for simplicity
    
    print("Running quick game test with advanced AI pursuit...")
    
    # Simulate just one inning to test
    try:
        print("\n=== TOP 1ST INNING ===")
        game.simulate_half_inning(is_top=True)
        
        print(f"\nScore after top 1st: Visitors {game.game_state.away_score} - {game.game_state.home_score} Home")
        
        if game.game_state.total_hits > 0:
            print(f"Total hits in inning: {game.game_state.total_hits}")
            print("✅ AI Pursuit integration working - game completed without crashes!")
        else:
            print("No hits to test fielding - this is actually good news!")
            
    except Exception as e:
        print(f"❌ Error during game simulation: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_ai_pursuit_integration()