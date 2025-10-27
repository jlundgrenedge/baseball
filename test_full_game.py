"""Run a full 9-inning test game."""
import sys
sys.path.append('.')

from batted_ball import GameSimulator, create_test_team

print("Running FULL 9-inning test game...")
print("=" * 60)

# Create two average teams
away_team = create_test_team("Road Warriors", "average")
home_team = create_test_team("Home Heroes", "average")

# Create and run simulation with less verbose output
simulator = GameSimulator(away_team, home_team, verbose=False)
final_state = simulator.simulate_game(num_innings=9)

print(f"\n{'=' * 60}")
print(f"FINAL SCORE")
print(f"{'=' * 60}")
print(f"{away_team.name}: {final_state.away_score}")
print(f"{home_team.name}: {final_state.home_score}")
print(f"{'=' * 60}")

print(f"\nGame Statistics:")
print(f"  Total Hits: {final_state.total_hits}")
print(f"  Home Runs: {final_state.total_home_runs}")
print(f"  Total Pitches: {final_state.total_pitches}")
print(f"  Innings: {final_state.inning - (0 if final_state.is_top else 1)}")

# Count play types
singles = sum(1 for p in simulator.play_by_play if 'SINGLE' in p.description and 'DOUBLE' not in p.description and 'TRIPLE' not in p.description)
doubles = sum(1 for p in simulator.play_by_play if 'DOUBLE' in p.description)
triples = sum(1 for p in simulator.play_by_play if 'TRIPLE' in p.description)
homers = sum(1 for p in simulator.play_by_play if 'HOME RUN' in p.description)
strikeouts = sum(1 for p in simulator.play_by_play if 'STRIKEOUT' in p.description or 'strikes out' in p.description.lower())
walks = sum(1 for p in simulator.play_by_play if 'WALK' in p.description or 'walks' in p.description.lower())
balls_in_play = sum(1 for p in simulator.play_by_play if p.description and not any(x in p.description for x in ['STRIKEOUT', 'WALK', 'strikes out', 'walks']))

# Calculate BABIP (Batting Average on Balls In Play)
# BABIP = (H - HR) / (AB - K - HR + SF)
# Simplified: Hits / (Hits + Outs on balls in play)
hits_on_bip = singles + doubles + triples
outs_on_bip = balls_in_play - hits_on_bip - homers
babip = hits_on_bip / (hits_on_bip + outs_on_bip) if (hits_on_bip + outs_on_bip) > 0 else 0

print(f"\nHit Breakdown:")
print(f"  Singles: {singles}")
print(f"  Doubles: {doubles}")
print(f"  Triples: {triples}")
print(f"  Home Runs: {homers}")

print(f"\nPlate Appearance Outcomes:")
print(f"  Strikeouts: {strikeouts}")
print(f"  Walks: {walks}")
print(f"  Balls in Play: {balls_in_play}")
print(f"  BABIP: {babip:.3f} (MLB average: ~.300)")

# Show pitcher velocities (reset pitches_thrown to show starting velo)
away_team.pitchers[0].pitches_thrown = 0
home_team.pitchers[0].pitches_thrown = 0
print(f"\nPitcher Starting Velocities:")
print(f"  {away_team.name} SP: {away_team.pitchers[0].get_pitch_velocity_mph('fastball'):.1f} mph")
print(f"  {home_team.name} SP: {home_team.pitchers[0].get_pitch_velocity_mph('fastball'):.1f} mph")

# Calculate per-9-innings rate
if final_state.inning > 1:
    innings_played = final_state.inning - (0 if final_state.is_top else 1)
    total_runs = final_state.away_score + final_state.home_score
    runs_per_9 = (total_runs / innings_played) * 9
    hits_per_9 = (final_state.total_hits / innings_played) * 9
    hrs_per_9 = (final_state.total_home_runs / innings_played) * 9
    
    print(f"\nPer-9-Innings Rates:")
    print(f"  Total Runs/9: {runs_per_9:.1f} (MLB average: ~9.0)")
    print(f"  Hits/9: {hits_per_9:.1f} (MLB average: ~17.0)")
    print(f"  HRs/9: {hrs_per_9:.1f} (MLB average: ~2.2)")
