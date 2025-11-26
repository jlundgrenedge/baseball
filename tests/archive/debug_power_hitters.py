"""Debug power hitter performance - see if they're hitting home runs."""
import sys
sys.path.append('.')

from batted_ball import GameSimulator, create_test_team

print("Running debug game with detailed batted ball logging...")
print("=" * 80)

# Create teams
away_team = create_test_team("Road Warriors", "average")
home_team = create_test_team("Home Heroes", "average")

# Find power/fly ball hitters
print("\nPower/Fly Ball Hitters:")
for team in [away_team, home_team]:
    for i, hitter in enumerate(team.hitters):
        # Use the main attributes object
        if hasattr(hitter, 'attributes') and hitter.attributes:
            attack_angle = hitter.attributes.get_attack_angle_mean_deg()
            bat_speed = hitter.attributes.get_bat_speed_mph()
            if attack_angle >= 15.0:  # Should be power or fly ball
                print(f"  {team.name} #{i+1}: {hitter.name} - {bat_speed:.1f} mph bat, {attack_angle:.1f}° angle")

# Run game with detailed tracking
simulator = GameSimulator(away_team, home_team, verbose=False)
final_state = simulator.simulate_game(num_innings=9)

# Extract fly balls from play-by-play
power_hitter_fly_balls = []
home_runs = []

for play in simulator.play_by_play:
    # Log all home runs
    if 'HOME RUN' in play.description:
        hr_info = {
            'description': play.description,
            'physics': play.physics_data if hasattr(play, 'physics_data') else None
        }
        home_runs.append(hr_info)
        print(f"\n  HOME RUN: {play.description}")
        if hr_info['physics']:
            print(f"    {hr_info['physics'].get('exit_velocity_mph', 0):.1f} mph @ {hr_info['physics'].get('launch_angle_deg', 0):.1f}° → {hr_info['physics'].get('distance_ft', 0):.0f} ft (apex {hr_info['physics'].get('peak_height_ft', 0):.0f} ft)")
    
    # Log all fly balls
    if hasattr(play, 'physics_data') and play.physics_data:
        la = play.physics_data.get('launch_angle_deg', 0)
        
        # Check if it's a fly ball (>20 deg)
        if la >= 20.0:
            distance = play.physics_data.get('distance_ft', 0)
            apex = play.physics_data.get('peak_height_ft', 0)
            exit_velo = play.physics_data.get('exit_velocity_mph', 0)
            
            detail = {
                'hitter': play.batter_name,
                'exit_velo': exit_velo,
                'launch_angle': la,
                'distance': distance,
                'apex': apex,
                'outcome': 'HR' if 'HOME RUN' in play.description else play.outcome
            }
            power_hitter_fly_balls.append(detail)
            if 'HOME RUN' not in play.description:  # Don't double-log HRs
                print(f"\n  Fly Ball: {play.batter_name} - {exit_velo:.1f} mph @ {la:.1f}° → {distance:.0f} ft (apex {apex:.0f} ft)")
                print(f"    Outcome: {detail['outcome']}")

print(f"\n{'=' * 80}")
print(f"FINAL RESULTS")
print(f"{'=' * 80}")
print(f"Score: {away_team.name} {final_state.away_score} - {home_team.name} {final_state.home_score}")
print(f"Total Home Runs: {final_state.total_home_runs}")
print(f"Total Fly Balls (>20°): {len(power_hitter_fly_balls)}")

if power_hitter_fly_balls:
    print(f"\nFly Ball Summary:")
    print(f"  Avg Exit Velo: {sum(fb['exit_velo'] for fb in power_hitter_fly_balls) / len(power_hitter_fly_balls):.1f} mph")
    print(f"  Avg Launch Angle: {sum(fb['launch_angle'] for fb in power_hitter_fly_balls) / len(power_hitter_fly_balls):.1f}°")
    print(f"  Avg Distance: {sum(fb['distance'] for fb in power_hitter_fly_balls) / len(power_hitter_fly_balls):.0f} ft")
    print(f"  Avg Apex: {sum(fb['apex'] for fb in power_hitter_fly_balls) / len(power_hitter_fly_balls):.0f} ft")
    
    # Show longest fly balls
    print(f"\nLongest Fly Balls:")
    sorted_fbs = sorted(power_hitter_fly_balls, key=lambda x: x['distance'], reverse=True)[:5]
    for fb in sorted_fbs:
        print(f"  {fb['exit_velo']:.1f} mph @ {fb['launch_angle']:.1f}° → {fb['distance']:.0f} ft (apex {fb['apex']:.0f} ft) - {fb['outcome']}")
