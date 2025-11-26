"""Run multiple games and average the stats."""
import sys
sys.path.append('.')

from batted_ball import GameSimulator, create_test_team

NUM_GAMES = 20  # Run 20 games to see average

total_runs = 0
total_hits = 0
total_hrs = 0
total_innings = 0

print(f"Running {NUM_GAMES} games to test power hitter boost...\n")

for game_num in range(1, NUM_GAMES + 1):
    # Create teams
    away_team = create_test_team(f"Away{game_num}", "average")
    home_team = create_test_team(f"Home{game_num}", "average")
    
    # Run game
    simulator = GameSimulator(away_team, home_team, verbose=False)
    final_state = simulator.simulate_game(num_innings=9)
    
    # Collect stats
    innings_played = final_state.inning - (0 if final_state.is_top else 1)
    runs = final_state.away_score + final_state.home_score
    hits = final_state.total_hits
    hrs = final_state.total_home_runs
    
    total_runs += runs
    total_hits += hits
    total_hrs += hrs
    total_innings += innings_played
    
    print(f"Game {game_num}: {runs} runs, {hits} hits, {hrs} HRs in {innings_played} innings")

# Calculate per-9 rates
print(f"\n{'='*60}")
print(f"AVERAGES ACROSS {NUM_GAMES} GAMES ({total_innings} total innings)")
print(f"{'='*60}")
runs_per_9 = (total_runs / total_innings) * 9 if total_innings > 0 else 0
hits_per_9 = (total_hits / total_innings) * 9 if total_innings > 0 else 0
hrs_per_9 = (total_hrs / total_innings) * 9 if total_innings > 0 else 0

print(f"Runs/9: {runs_per_9:.1f} (MLB avg: ~9.0)")
print(f"Hits/9: {hits_per_9:.1f} (MLB avg: ~17.0)")
print(f"HRs/9: {hrs_per_9:.2f} (MLB avg: ~2.2)")
print(f"\nTotal HRs: {total_hrs} across {NUM_GAMES} games (avg {total_hrs/NUM_GAMES:.1f} per game)")
