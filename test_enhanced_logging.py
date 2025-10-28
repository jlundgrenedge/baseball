#!/usr/bin/env python3
"""
Test script to demonstrate enhanced logging to file
"""

import sys
sys.path.append('.')

from batted_ball.game_simulation import GameSimulator, create_test_team

def main():
    print("Testing enhanced game logging...")
    
    # Create two teams
    away_team = create_test_team("Visitors")
    home_team = create_test_team("Home Team")
    
    # Create simulator with file logging
    simulator = GameSimulator(
        away_team=away_team,
        home_team=home_team,
        verbose=True,  # Still show on console
        log_file="enhanced_game_log.txt"  # Also write to file
    )
    
    try:
        # Run a short 2-inning game
        print("Running 2-inning game with enhanced logging...")
        final_state = simulator.simulate_game(num_innings=2)
        
        print(f"\nGame completed! Final score: {final_state.away_score} - {final_state.home_score}")
        print("Enhanced logging has been written to 'enhanced_game_log.txt'")
        
    finally:
        # Ensure log file is closed
        simulator.close_log()

if __name__ == "__main__":
    main()