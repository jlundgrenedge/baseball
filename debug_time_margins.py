"""
Investigate why fielders aren't catching fly balls - check time margins.
"""
from batted_ball.game_simulation import GameSimulator, create_test_team
from batted_ball.play_simulation import PlayOutcome

home_team = create_test_team("Home")
away_team = create_test_team("Away")
simulator = GameSimulator(away_team, home_team, verbose=False)
final_state = simulator.simulate_game(num_innings=9)

print("FLY BALL TIME MARGIN ANALYSIS")
print("=" * 80)

fly_ball_data = []

# Check each play-by-play event
for play in simulator.play_by_play:
    physics_data = getattr(play, 'physics_data', None)
    if physics_data and 'launch_angle_deg' in physics_data:
        launch_angle = physics_data['launch_angle_deg']
        
        # Fly ball: 25-50 degrees
        if 25 <= launch_angle < 50:
            outcome = getattr(play, 'outcome', 'unknown')
            caught = outcome in ['fly_out', 'line_out']
            
            data = {
                'distance': physics_data.get('distance_ft', 0),
                'hang_time': physics_data.get('hang_time_sec', 0),
                'launch_angle': launch_angle,
                'caught': caught,
                'outcome': outcome
            }
            
            # Get fielding timing if available from play result
            play_result = getattr(play, 'play_result', None)
            if play_result and hasattr(play_result, 'fielding_results') and play_result.fielding_results:
                fr = play_result.fielding_results[0]
                data['time_margin'] = fr.ball_arrival_time - fr.fielder_arrival_time
                data['fielder'] = fr.fielder_name
            
            fly_ball_data.append(data)

# Analyze time margins
caught_on_time = []
caught_late = []
missed_on_time = []
missed_late = []

for fb in fly_ball_data:
    if 'time_margin' not in fb:
        continue
    
    tm = fb['time_margin']
    if fb['caught']:
        if tm >= 0:
            caught_on_time.append(fb)
        else:
            caught_late.append(fb)
    else:
        if tm >= 0:
            missed_on_time.append(fb)
        else:
            missed_late.append(fb)

print(f"Total fly balls: {len(fly_ball_data)}")
print(f"With timing data: {len([fb for fb in fly_ball_data if 'time_margin' in fb])}")
print()
print(f"Caught when on time: {len(caught_on_time)}")
print(f"Caught when late: {len(caught_late)}")
print(f"MISSED when ON TIME: {len(missed_on_time)} ⚠️")
print(f"Missed when late: {len(missed_late)}")
print()

# Show examples of missed-when-on-time
if missed_on_time:
    print("EXAMPLES OF MISSED CATCHES WHEN FIELDER WAS ON TIME:")
    print("-" * 80)
    for fb in missed_on_time[:10]:
        print(f"Distance: {fb['distance']:.1f}ft, Hang time: {fb['hang_time']:.2f}s, LA: {fb['launch_angle']:.1f}°")
        print(f"Time margin: +{fb['time_margin']:.2f}s (fielder arrived EARLY)")
        print(f"Fielder: {fb['fielder']}, Outcome: {fb['outcome']}")
        print()

# Time margin distribution
time_margins = [fb['time_margin'] for fb in fly_ball_data if 'time_margin' in fb]
if time_margins:
    import statistics
    print(f"Time margin stats:")
    print(f"  Mean: {statistics.mean(time_margins):.2f}s")
    print(f"  Median: {statistics.median(time_margins):.2f}s")
    print(f"  Min: {min(time_margins):.2f}s")
    print(f"  Max: {max(time_margins):.2f}s")
else:
    print("No timing data available - fielding results not being recorded!")
