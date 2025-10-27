"""
Debug why fly balls are not being caught.

Add instrumentation to see:
1. Are fielders being checked for fly balls?
2. What are the time margins?
3. What are the catch probabilities?
"""

from batted_ball import GameSimulator, create_test_team
from collections import defaultdict

def debug_fly_ball_catching():
    """Debug fly ball fielding."""
    print("Debugging Fly Ball Fielding")
    print("=" * 80)
    
    # Create teams
    away_team = create_test_team("Away", team_quality="average")
    home_team = create_test_team("Home", team_quality="average")
    
    # Create game simulator
    game = GameSimulator(
        away_team=away_team,
        home_team=home_team,
        verbose=False
    )
    
    # Run just 3 innings for quick analysis
    final_state = game.simulate_game(num_innings=3)
    
    # Collect fly balls
    fly_balls = []
    for play in game.play_by_play:
        physics_data = getattr(play, 'physics_data', None)
        if physics_data and 'launch_angle_deg' in physics_data:
            launch_angle = physics_data['launch_angle_deg']
            if launch_angle >= 25:  # Fly ball
                outcome = getattr(play, 'outcome', 'unknown')
                exit_velo = physics_data.get('exit_velocity_mph', 0)
                distance = physics_data.get('distance_ft', 0)
                hang_time = physics_data.get('hang_time_sec', 0)
                
                fly_balls.append({
                    'batter': getattr(play, 'batter_name', 'Unknown'),
                    'launch_angle': launch_angle,
                    'exit_velo': exit_velo,
                    'distance': distance,
                    'hang_time': hang_time,
                    'outcome': outcome
                })
    
    print(f"\nFound {len(fly_balls)} fly balls:")
    print("=" * 80)
    
    for fb in fly_balls:
        caught = "OUT" if fb['outcome'] in ['fly_out', 'line_out'] else "HIT"
        print(f"{fb['batter']:20s}: {fb['launch_angle']:5.1f}° @ {fb['exit_velo']:5.1f} mph")
        print(f"  Distance: {fb['distance']:6.1f} ft, Hang time: {fb['hang_time']:.2f}s")
        print(f"  Outcome: {fb['outcome']:15s} [{caught}]")
        print()
    
    # Summary
    caught_count = sum(1 for fb in fly_balls if fb['outcome'] in ['fly_out', 'line_out'])
    hit_count = len(fly_balls) - caught_count
    
    print("=" * 80)
    print(f"Fly balls caught: {caught_count}/{len(fly_balls)} ({caught_count/len(fly_balls)*100:.1f}%)" if fly_balls else "No fly balls")
    print(f"Fly balls for hits: {hit_count}/{len(fly_balls)} ({hit_count/len(fly_balls)*100:.1f}%)" if fly_balls else "")
    print(f"Target: ~75-80% caught, ~20-25% hits")
    
    print(f"\nFinal Score: Away {final_state.away_score} - Home {final_state.home_score}")

if __name__ == "__main__":
    debug_fly_ball_catching()
