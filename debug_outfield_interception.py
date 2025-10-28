#!/usr/bin/env python3
"""
Debug script to understand why outfield interception is failing.
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from batted_ball.game_simulation import GameSimulator
from batted_ball.player import Player, PlayerAttributes
import numpy as np

def create_debug_game():
    """Create a simple game for debugging outfield interception."""
    
    # Create simple teams
    visitors_attributes = PlayerAttributes(
        contact=60, power=70, plate_discipline=65, speed=60,
        fielding=65, arm=60, reaction=60, command=60, movement=60
    )
    home_attributes = PlayerAttributes(
        contact=60, power=70, plate_discipline=65, speed=60,
        fielding=65, arm=60, reaction=60, command=60, movement=60
    )
    
    visitors = Player("Visitors", visitors_attributes)
    home = Player("Home Team", home_attributes)
    
    return GameSimulator(visitors, home, innings=1, log_file='debug_outfield_log.txt')

def main():
    print("Debugging outfield interception...")
    
    game = create_debug_game()
    
    # Run game looking for outfield scenarios
    for attempt in range(5):
        print(f"\nAttempt {attempt + 1}:")
        try:
            game.simulate_game()
            print("Game completed, check debug_outfield_log.txt for outfield drops")
            break
        except Exception as e:
            print(f"Error: {e}")
            continue

if __name__ == "__main__":
    main()