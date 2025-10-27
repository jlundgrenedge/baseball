"""
Analyze hang times by batted ball type to see if they match MLB norms.

MLB Hang Time Benchmarks:
- Line drive / low fly ball: 2.5-3.5 seconds
- Average routine fly ball: 3.5-5.0 seconds  
- High pop-up / deep fly ball: 5.0-6.5 seconds
- Exceptional / towering pop-up: 6.5-7.5 seconds (rare)
"""
from batted_ball.game_simulation import GameSimulator, create_test_team
from collections import defaultdict
import statistics

def categorize_launch_angle(angle_deg):
    """Categorize launch angle into batted ball type."""
    if angle_deg < 10:
        return 'ground_ball'
    elif 10 <= angle_deg < 25:
        return 'line_drive'
    elif 25 <= angle_deg < 50:
        return 'fly_ball'
    else:
        return 'pop_up'

home_team = create_test_team("Home")
away_team = create_test_team("Away")
simulator = GameSimulator(away_team, home_team, verbose=False)
final_state = simulator.simulate_game(num_innings=9)

print("HANG TIME ANALYSIS BY BATTED BALL TYPE")
print("=" * 80)

by_type = defaultdict(list)

for play in simulator.play_by_play:
    physics_data = getattr(play, 'physics_data', None)
    if physics_data and 'launch_angle_deg' in physics_data:
        launch_angle = physics_data['launch_angle_deg']
        hang_time = physics_data.get('hang_time_sec', 0)
        distance = physics_data.get('distance_ft', 0)
        exit_velo = physics_data.get('exit_velocity_mph', 0)
        
        ball_type = categorize_launch_angle(launch_angle)
        by_type[ball_type].append({
            'hang_time': hang_time,
            'distance': distance,
            'launch_angle': launch_angle,
            'exit_velo': exit_velo
        })

# Analyze each type
for ball_type in ['ground_ball', 'line_drive', 'fly_ball', 'pop_up']:
    data = by_type[ball_type]
    if not data:
        continue
    
    hang_times = [d['hang_time'] for d in data]
    distances = [d['distance'] for d in data]
    launch_angles = [d['launch_angle'] for d in data]
    
    print(f"\n{ball_type.upper().replace('_', ' ')} ({len(data)} balls)")
    print("-" * 80)
    print(f"Hang Time:")
    print(f"  Mean: {statistics.mean(hang_times):.2f}s")
    print(f"  Median: {statistics.median(hang_times):.2f}s")
    print(f"  Range: {min(hang_times):.2f}s - {max(hang_times):.2f}s")
    
    print(f"Distance:")
    print(f"  Mean: {statistics.mean(distances):.1f}ft")
    print(f"  Median: {statistics.median(distances):.1f}ft")
    print(f"  Range: {min(distances):.1f}ft - {max(distances):.1f}ft")
    
    print(f"Launch Angle:")
    print(f"  Mean: {statistics.mean(launch_angles):.1f}°")
    print(f"  Range: {min(launch_angles):.1f}° - {max(launch_angles):.1f}°")

# MLB benchmarks
print("\n" + "=" * 80)
print("MLB HANG TIME BENCHMARKS")
print("=" * 80)
print("Line drive / low fly ball:     2.5 - 3.5 seconds")
print("Average routine fly ball:      3.5 - 5.0 seconds")
print("High pop-up / deep fly ball:   5.0 - 6.5 seconds")
print("Exceptional / towering pop-up: 6.5 - 7.5 seconds (rare)")
print()
print("COMPARISON:")
print("-" * 80)

# Check line drives
ld_data = by_type['line_drive']
if ld_data:
    ld_hang_times = [d['hang_time'] for d in ld_data]
    ld_mean = statistics.mean(ld_hang_times)
    ld_status = "✓ GOOD" if 2.5 <= ld_mean <= 3.5 else "✗ PROBLEM"
    print(f"Line drives: {ld_mean:.2f}s avg (target 2.5-3.5s) [{ld_status}]")

# Check fly balls
fb_data = by_type['fly_ball']
if fb_data:
    fb_hang_times = [d['hang_time'] for d in fb_data]
    fb_mean = statistics.mean(fb_hang_times)
    fb_status = "✓ GOOD" if 3.5 <= fb_mean <= 5.0 else "✗ PROBLEM"
    print(f"Fly balls: {fb_mean:.2f}s avg (target 3.5-5.0s) [{fb_status}]")

# Check pop-ups
pu_data = by_type['pop_up']
if pu_data:
    pu_hang_times = [d['hang_time'] for d in pu_data]
    pu_mean = statistics.mean(pu_hang_times)
    pu_status = "✓ GOOD" if pu_mean >= 5.0 else "✗ PROBLEM"
    print(f"Pop-ups: {pu_mean:.2f}s avg (target 5.0-6.5s) [{pu_status}]")
