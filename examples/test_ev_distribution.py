"""Test EV distribution after hard swing implementation."""
import numpy as np
import sys
import io
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from batted_ball.database.team_loader import TeamLoader
from batted_ball.game_simulation import GameSimulator, PitcherRotation

# Run 10 games, collect EV data
all_evs = []
np.random.seed(42)

loader = TeamLoader()
teams = loader.db.list_teams()

# Get first two teams
if len(teams) < 2:
    print('Need 2+ teams in DB')
    sys.exit(1)

# Get team info
team1 = teams[0]
team2 = teams[1]
print(f"Using: {team1['team_name']} ({team1['season']}) vs {team2['team_name']} ({team2['season']})")

all_q_values = []
all_bat_speeds = []

for i in range(10):
    # Load fresh teams each game
    away_team = loader.load_team(team1['team_name'], team1['season'])
    home_team = loader.load_team(team2['team_name'], team2['season'])
    
    # Reset pitcher states
    away_team.reset_pitcher_state()
    home_team.reset_pitcher_state()
    
    # Quiet mode
    old_stdout = sys.stdout
    sys.stdout = io.StringIO()
    
    try:
        sim = GameSimulator(away_team, home_team, verbose=False, debug_metrics=0, wind_enabled=True)
        result = sim.simulate_game(num_innings=9)
    finally:
        sys.stdout = old_stdout
    
    # Collect EVs from game state
    all_evs.extend(result.away_exit_velocities)
    all_evs.extend(result.home_exit_velocities)
    
    print(f'Game {i+1}: {result.away_score}-{result.home_score}')

loader.close()

all_evs = np.array(all_evs)
print(f'\nTotal balls in play (10 games): {len(all_evs)}')
print(f'Mean EV: {np.mean(all_evs):.1f} mph')
print(f'Std Dev EV: {np.std(all_evs):.1f} mph')
print(f'Min EV: {np.min(all_evs):.1f} mph, Max EV: {np.max(all_evs):.1f} mph')
print()
print('Hard Hit Breakdown:')
print(f'  95+ mph: {np.sum(all_evs >= 95)} ({100*np.sum(all_evs >= 95)/len(all_evs):.1f}%) - target ~35-40%')
print(f'  100+ mph: {np.sum(all_evs >= 100)} ({100*np.sum(all_evs >= 100)/len(all_evs):.1f}%)')
print(f'  105+ mph: {np.sum(all_evs >= 105)} ({100*np.sum(all_evs >= 105)/len(all_evs):.1f}%)')
print(f'  110+ mph: {np.sum(all_evs >= 110)} ({100*np.sum(all_evs >= 110)/len(all_evs):.1f}%)')

# EV distribution percentiles
percentiles = [10, 25, 50, 75, 90, 95, 99]
print('\nEV Percentiles:')
for p in percentiles:
    print(f'  {p}th: {np.percentile(all_evs, p):.1f} mph')
