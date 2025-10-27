"""Quick test game to check current simulation state."""
import sys
sys.path.append('.')

from batted_ball import GameSimulator, create_test_team

print("Running quick 3-inning test game...")
print("=" * 60)

# Create two average teams
away_team = create_test_team("Test Away", "average")
home_team = create_test_team("Test Home", "average")

# Create and run simulation with less verbose output
simulator = GameSimulator(away_team, home_team, verbose=False)
final_state = simulator.simulate_game(num_innings=3)

print(f"\nFINAL: {away_team.name} {final_state.away_score} - {final_state.home_score} {home_team.name}")
print(f"Total Hits: {final_state.total_hits}")
print(f"Home Runs: {final_state.total_home_runs}")
print(f"Total Pitches: {final_state.total_pitches}")

# Count play types
singles = sum(1 for p in simulator.play_by_play if 'SINGLE' in p.description and 'DOUBLE' not in p.description and 'TRIPLE' not in p.description)
doubles = sum(1 for p in simulator.play_by_play if 'DOUBLE' in p.description)
triples = sum(1 for p in simulator.play_by_play if 'TRIPLE' in p.description)
homers = sum(1 for p in simulator.play_by_play if 'HOME RUN' in p.description)

print(f"\nHit Breakdown:")
print(f"  Singles: {singles}")
print(f"  Doubles: {doubles}")
print(f"  Triples: {triples}")
print(f"  Home Runs: {homers}")

# Show pitcher velocities
print(f"\nPitcher Velocities:")
print(f"  {away_team.name}: {away_team.pitchers[0].get_pitch_velocity_mph('fastball'):.1f} mph")
print(f"  {home_team.name}: {home_team.pitchers[0].get_pitch_velocity_mph('fastball'):.1f} mph")
