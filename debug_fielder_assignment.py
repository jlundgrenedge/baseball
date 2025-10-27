#!/usr/bin/env python3
"""
Debug fielder assignment and positioning
"""
import sys
import numpy as np
from batted_ball.game_simulation import GameSimulator
from batted_ball.play_simulation import PlaySimulator
from batted_ball.field_layout import FieldLayout

# Monkey-patch to log fielder assignments
original_assign_fielder = PlaySimulator._assign_fielding_responsibility

def patched_assign_fielder(self, field_pos):
    result = original_assign_fielder(self, field_pos)
    print(f"\nFIELDER ASSIGNMENT:")
    print(f"  Ball position: ({field_pos.x:.1f}, {field_pos.y:.1f})")
    print(f"  Assigned to: {result}")
    
    # Show all fielder positions
    print(f"\n  Fielder positions:")
    layout = FieldLayout()
    for pos_name, pos_coords in layout.get_all_positions().items():
        print(f"    {pos_name}: ({pos_coords[0]:.1f}, {pos_coords[1]:.1f})")
    
    return result

PlaySimulator._assign_fielding_responsibility = patched_assign_fielder

# Run simulation
print("Starting game simulation with fielder assignment debugging...")
sim = GameSimulator()
result = sim.simulate_game(innings=2, verbose=False)

print(f"\n\nFinal Score: {result['away_score']} - {result['home_score']}")
