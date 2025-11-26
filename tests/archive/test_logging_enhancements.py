#!/usr/bin/env python3
"""
Test script for logging enhancements.
Runs a short 1-inning game to verify all EASY logging tasks work correctly.
"""

from batted_ball.game_simulation import create_test_team, GameSimulator

# Create two teams
away_team = create_test_team("Visitors", team_quality="good")
home_team = create_test_team("Home", team_quality="good")

# Create simulator with verbose logging to file
sim = GameSimulator(
    away_team=away_team,
    home_team=home_team,
    verbose=True,
    log_file="test_enhanced_logging.log",
    ballpark="Test Stadium"
)

# Run a 1-inning game
print("Running 1-inning test game with enhanced logging...")
result = sim.simulate_game(num_innings=1, rng_seed=42)

print("\n" + "="*80)
print("Test complete!")
print(f"Check 'test_enhanced_logging.log' for enhanced logging features:")
print("  - SIM CONFIG block at the beginning")
print("  - ZoneBucket for each pitch")
print("  - OutcomeCodePitch for each pitch")
print("  - OutcomeCodePA for each plate appearance")
print("  - SABERMETRIC SUMMARY for each team at the end")
print("="*80)
