# Debug: run multiple games and check launch angle values and HR production
import random
import numpy as np
from batted_ball.game_simulation import create_test_team, GameSimulator

print("Simulating 5 games to gather statistics...")

all_launch_angles = []
all_exit_velocities = []
total_runs = 0
total_hits = 0
total_hr = 0
total_fly_balls = 0  # for HR/FB rate

for game_num in range(5):
    np.random.seed(42 + game_num)
    random.seed(42 + game_num)
    
    home = create_test_team('Home', team_quality='good')
    away = create_test_team('Away', team_quality='average')
    
    sim = GameSimulator(away, home, verbose=False)
    result = sim.simulate_game(num_innings=9)
    
    # Collect launch angles and EVs
    angles = result.away_launch_angles + result.home_launch_angles
    evs = result.away_exit_velocities + result.home_exit_velocities
    all_launch_angles.extend(angles)
    all_exit_velocities.extend(evs)
    
    # Aggregate game stats
    total_runs += result.away_score + result.home_score
    total_hits += result.away_hits + result.home_hits
    total_hr += result.away_home_runs + result.home_home_runs
    total_fly_balls += result.away_fly_balls + result.home_fly_balls
    
    print(f"  Game {game_num + 1}: {result.away_score}-{result.home_score}, "
          f"{result.away_hits + result.home_hits} hits, {len(angles)} batted balls, "
          f"{result.away_home_runs + result.home_home_runs} HR")

angles = np.array(all_launch_angles)
evs = np.array(all_exit_velocities)

print()
print(f"Total batted balls: {len(angles)}")
print(f"Mean launch angle: {np.mean(angles):.1f}°")
print(f"Std deviation: {np.std(angles):.1f}°")
print()

# Distribution
gb = np.sum(angles < 10)
ld = np.sum((angles >= 10) & (angles < 25))
fb = np.sum((angles >= 25) & (angles < 50))
popup = np.sum(angles >= 50)
total = len(angles)

print("Batted Ball Distribution:")
print(f"  Ground Ball (<10°):  {gb} ({100*gb/total:.1f}%) target 45%")
print(f"  Line Drive (10-25°): {ld} ({100*ld/total:.1f}%) target 21%")
print(f"  Fly Ball (25-50°):   {fb} ({100*fb/total:.1f}%) target 34%")
print(f"  Pop-up (>50°):       {popup} ({100*popup/total:.1f}%)")

print()
print("Exit Velocity:")
print(f"  Mean: {np.mean(evs):.1f} mph")
print(f"  Hard Hit (95+): {100*np.sum(evs>=95)/len(evs):.1f}%")

print()
print("Launch Angle Distribution:")
print(f"  10th percentile: {np.percentile(angles, 10):.1f}°")
print(f"  25th percentile: {np.percentile(angles, 25):.1f}°")
print(f"  50th percentile: {np.percentile(angles, 50):.1f}°")
print(f"  75th percentile: {np.percentile(angles, 75):.1f}°")
print(f"  90th percentile: {np.percentile(angles, 90):.1f}°")

print()
print(f"Game Totals (5 games, 9 innings each):")
print(f"  Runs: {total_runs} ({total_runs/10:.1f} per team per game)")
print(f"  Hits: {total_hits} ({total_hits/10:.1f} per team per game)")
print(f"  HR: {total_hr} ({total_hr/10:.1f} per team per game)")
print(f"  Fly Balls: {total_fly_balls}")
if total_fly_balls > 0:
    print(f"  HR/FB: {100*total_hr/total_fly_balls:.1f}% (target 12.5%)")

# Analyze fly ball characteristics
fb_mask = (angles >= 25) & (angles < 50)
fb_angles = angles[fb_mask]
fb_evs = evs[fb_mask]

print()
print("Fly Ball Analysis:")
print(f"  Count: {len(fb_angles)}")
print(f"  Mean LA: {np.mean(fb_angles):.1f}°")
print(f"  Mean EV: {np.mean(fb_evs):.1f} mph")
print(f"  EV 100+: {np.sum(fb_evs >= 100)} ({100*np.sum(fb_evs >= 100)/len(fb_evs):.1f}%)")
print(f"  EV 105+: {np.sum(fb_evs >= 105)} ({100*np.sum(fb_evs >= 105)/len(fb_evs):.1f}%)")

# Check barrel combinations (EV 100+ and LA 25-32)
barrel_mask = (evs >= 100) & (angles >= 25) & (angles <= 32)
print(f"  Barrels (EV 100+, LA 25-32°): {np.sum(barrel_mask)}")

