"""Analyze HR/FB rate across multiple games to understand why it might be low."""
import sys
sys.path.insert(0, '.')

from batted_ball.database import TeamLoader
from batted_ball import GameSimulator
from batted_ball.play_outcome import PlayOutcome
from batted_ball.ballpark import get_ballpark
import random
import numpy as np

loader = TeamLoader()
team1 = loader.load_team('New York Yankees', season=2025)
team2 = loader.load_team('Los Angeles Dodgers', season=2025)

# Track cumulative stats
total_hrs = 0
total_fbs = 0
park = get_ballpark('generic')

# Track fly ball characteristics
fly_ball_evs = []
fly_ball_las = []
fly_ball_dists = []
hr_evs = []
hr_las = []
hr_dists = []

# Run 50 games  
num_games = 50
for game_num in range(num_games):
    game = GameSimulator(team1, team2, verbose=False, ballpark='generic')
    result = game.simulate_game()
    
    # Get stats from GameState
    hrs = result.away_home_runs + result.home_home_runs
    fbs = result.away_fly_balls + result.home_fly_balls
    total_hrs += hrs
    total_fbs += fbs
    
    # Analyze individual plays
    for play in game.play_by_play:
        physics = play.physics_data
        if physics.get('launch_angle_deg', 0) >= 25:  # Fly ball
            ev = physics.get('exit_velocity_mph', 0)
            la = physics.get('launch_angle_deg', 0)
            dist = physics.get('distance_ft', 0)
            
            fly_ball_evs.append(ev)
            fly_ball_las.append(la)
            fly_ball_dists.append(dist)
            
            if 'HOME RUN' in play.description:
                hr_evs.append(ev)
                hr_las.append(la)
                hr_dists.append(dist)

# Final analysis
print(f'\nTotal over {num_games} games:')
print(f'  Home runs: {total_hrs}')
print(f'  Fly balls: {total_fbs}')
print(f'  HR/FB rate: {100*total_hrs/total_fbs if total_fbs else 0:.1f}%')
print(f'  MLB target: 9-16%')

print(f'\nFly ball EV distribution:')
print(f'  Mean: {np.mean(fly_ball_evs):.1f} mph')
print(f'  Median: {np.median(fly_ball_evs):.1f} mph')
print(f'  P90: {np.percentile(fly_ball_evs, 90):.1f} mph')
print(f'  P95: {np.percentile(fly_ball_evs, 95):.1f} mph')
print(f'  Max: {max(fly_ball_evs):.1f} mph')

print(f'\nFly ball LA distribution:')
print(f'  Mean: {np.mean(fly_ball_las):.1f}°')
print(f'  Median: {np.median(fly_ball_las):.1f}°')

print(f'\nFly ball distance distribution:')
print(f'  Mean: {np.mean(fly_ball_dists):.1f} ft')
print(f'  Median: {np.median(fly_ball_dists):.1f} ft')
print(f'  P90: {np.percentile(fly_ball_dists, 90):.1f} ft')
print(f'  # > 330 ft: {sum(1 for d in fly_ball_dists if d > 330)} / {len(fly_ball_dists)}')
print(f'  # > 350 ft: {sum(1 for d in fly_ball_dists if d > 350)} / {len(fly_ball_dists)}')
print(f'  # > 380 ft: {sum(1 for d in fly_ball_dists if d > 380)} / {len(fly_ball_dists)}')
print(f'  # > 400 ft: {sum(1 for d in fly_ball_dists if d > 400)} / {len(fly_ball_dists)}')

if hr_evs:
    print(f'\nHR characteristics:')
    print(f'  Mean EV: {np.mean(hr_evs):.1f} mph')
    print(f'  Mean LA: {np.mean(hr_las):.1f}°')
    print(f'  Mean Dist: {np.mean(hr_dists):.1f} ft')
    print(f'  Min Dist: {min(hr_dists):.1f} ft')
