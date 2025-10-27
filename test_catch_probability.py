"""Test catch probability distribution in game situations."""
import sys
sys.path.append('.')

from batted_ball import GameSimulator, create_test_team
import numpy as np

print("Testing catch probability distribution...")
print("=" * 60)

# Create two average teams
away_team = create_test_team("Test Away", "average")
home_team = create_test_team("Test Home", "average")

# Create simulator
simulator = GameSimulator(away_team, home_team, verbose=False)

# Track catch probabilities
catch_probs = []
catch_attempts = []
hits = 0
outs = 0

# Simulate a bunch of at-bats
from batted_ball.at_bat import AtBatSimulator
from batted_ball.play_simulation import PlaySimulator

at_bat_sim = AtBatSimulator(home_team.pitchers[0], away_team.players[0])
play_sim = PlaySimulator(home_team.players, away_team.players)

print("\nSimulating 100 balls in play...")
balls_in_play = 0
successful_catches = 0
missed_catches = 0

while balls_in_play < 100:
    # Simulate at-bat
    ab_result = at_bat_sim.simulate_at_bat()
    
    if ab_result.outcome in ['single', 'double', 'triple', 'home_run', 'out']:
        balls_in_play += 1
        
        if ab_result.outcome == 'out':
            # Track catch situations
            # For now just count
            outs += 1
        else:
            hits += 1

print(f"\nResults from 100 balls in play:")
print(f"  Hits: {hits}")
print(f"  Outs: {outs}")
print(f"  Hit Rate: {hits / 100:.1%}")
print(f"\nMLB average for balls in play: ~30% become hits")
print(f"Our simulation: {hits / 100:.1%} become hits")
