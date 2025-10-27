"""Check actual hang times on fly balls"""
from batted_ball.game_simulation import GameSimulator, create_test_team

home_team = create_test_team("Home")
away_team = create_test_team("Away")
simulator = GameSimulator(away_team, home_team, verbose=False)
final_state = simulator.simulate_game(num_innings=9)

fly_ball_hang_times = []

for play in simulator.play_by_play:
    physics_data = getattr(play, 'physics_data', None)
    if physics_data and 'launch_angle_deg' in physics_data:
        launch_angle = physics_data['launch_angle_deg']
        if 25 <= launch_angle < 50:  # Fly ball
            hang_time = physics_data.get('hang_time_sec', 0)
            distance = physics_data.get('distance_ft', 0)
            fly_ball_hang_times.append({
                'hang_time': hang_time,
                'distance': distance,
                'launch_angle': launch_angle
            })

if fly_ball_hang_times:
    import statistics
    hang_times = [fb['hang_time'] for fb in fly_ball_hang_times]
    distances = [fb['distance'] for fb in fly_ball_hang_times]
    
    print(f"FLY BALL HANG TIME ANALYSIS")
    print("=" * 80)
    print(f"Total fly balls: {len(fly_ball_hang_times)}")
    print()
    print("HANG TIME STATISTICS:")
    print(f"  Mean: {statistics.mean(hang_times):.2f}s")
    print(f"  Median: {statistics.median(hang_times):.2f}s")
    print(f"  Min: {min(hang_times):.2f}s")
    print(f"  Max: {max(hang_times):.2f}s")
    print()
    print("DISTANCE STATISTICS:")
    print(f"  Mean: {statistics.mean(distances):.1f}ft")
    print(f"  Median: {statistics.median(distances):.1f}ft")
    print(f"  Min: {min(distances):.1f}ft")
    print(f"  Max: {max(distances):.1f}ft")
    print()
    print("SAMPLE FLY BALLS:")
    print("-" * 80)
    for i, fb in enumerate(fly_ball_hang_times[:20], 1):
        print(f"#{i}: {fb['distance']:.1f}ft, {fb['hang_time']:.2f}s hang time, LA: {fb['launch_angle']:.1f}°")
        
        # Calculate if fielder at 265ft can reach it
        fielder_pos = 265
        ball_pos = fb['distance']
        distance_to_cover = abs(ball_pos - fielder_pos)
        time_available = fb['hang_time'] - 0.1  # Minus first-step
        speed_needed = distance_to_cover / time_available if time_available > 0 else 999
        
        can_reach = speed_needed <= 28  # Average fielder speed
        status = "✓ REACHABLE" if can_reach else "✗ TOO FAR"
        print(f"    Distance to cover: {distance_to_cover:.1f}ft, Speed needed: {speed_needed:.1f} ft/s [{status}]")
else:
    print("No fly balls found")
