"""Quick test to simulate a game with database teams."""
import sys
import io

# Force UTF-8 encoding for Windows console
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

from batted_ball.database.team_loader import TeamLoader
from batted_ball.game_simulation import GameSimulator

# Load teams
loader = TeamLoader('baseball_teams.db')
cubs = loader.load_team("Chicago Cubs", 2025)
reds = loader.load_team("Cincinnati Reds", 2025)

if not cubs or not reds:
    print("ERROR: Failed to load teams")
    exit(1)

print(f"\n=== SIMULATING GAME ===")
print(f"{cubs.name} vs {reds.name}")

# Create simulator
sim = GameSimulator(home_team=cubs, away_team=reds, verbose=False)  # Disable verbose logging

# Run game
result = sim.simulate_game()

# Show results
print(f"\n=== FINAL SCORE ===")
print(f"{result.away_team}: {result.away_runs}")
print(f"{result.home_team}: {result.home_runs}")
print(f"\nWinner: {result.winning_team}")

print(f"\n=== BOX SCORE ===")
print(f"{result.away_team}:")
print(f"  Runs: {result.away_runs}, Hits: {result.away_hits}, Errors: {result.away_errors}")
print(f"{result.home_team}:")
print(f"  Runs: {result.home_runs}, Hits: {result.home_hits}, Errors: {result.home_errors}")

print(f"\n=== PITCHER STATS ===")
print(f"Starting Pitchers:")
print(f"  {cubs.name}: {cubs.pitchers[0].name}")
print(f"  {reds.name}: {reds.pitchers[0].name}")

loader.close()
print("\n✓ Game simulation completed successfully!")
