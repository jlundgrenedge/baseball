"""
Test launch angle variance with detailed tracking.

Track actual launch angles from batted balls to verify variance.
"""

from batted_ball import GameSimulator, create_test_team
from collections import Counter
import numpy as np

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

def test_launch_angle_details():
    """Test that launch angles have realistic variance."""
    print("Testing Launch Angle Variance - Detailed Analysis")
    print("=" * 80)
    print("MLB Targets: ~45% GB (<10°), ~20% LD (10-25°), ~35% FB (25-50°)")
    print("=" * 80)
    
    # Create teams
    away_team = create_test_team("Away", team_quality="average")
    home_team = create_test_team("Home", team_quality="average")
    
    # Create game simulator - disable verbose to avoid Unicode issues
    game = GameSimulator(
        away_team=away_team,
        home_team=home_team,
        verbose=False  # Disable to avoid Unicode printing issues
    )
    
    # Run 9 full innings for more data
    final_state = game.simulate_game(num_innings=9)
    
    # Collect launch angles from play-by-play
    launch_angles = []
    batted_ball_types = Counter()
    
    print("\n" + "=" * 80)
    print("BATTED BALL ANALYSIS")
    print("=" * 80)
    
    for play in game.play_by_play:
        # Check if play has physics_data with launch angle
        physics_data = getattr(play, 'physics_data', None)
        if physics_data and 'launch_angle_deg' in physics_data:
            launch_angle = physics_data['launch_angle_deg']
            launch_angles.append(launch_angle)
            
            ball_type = categorize_launch_angle(launch_angle)
            batted_ball_types[ball_type] += 1
            
            # Print each batted ball
            batter_name = getattr(play, 'batter_name', 'Unknown')
            outcome = getattr(play, 'outcome', 'Unknown')
            exit_velo = physics_data.get('exit_velocity_mph', 0)
            print(f"  {batter_name:20s}: {launch_angle:6.1f}° @ {exit_velo:5.1f} mph -> {ball_type:12s} ({outcome})")
    
    total = len(launch_angles)
    
    if total > 0:
        print("\n" + "=" * 80)
        print(f"DISTRIBUTION SUMMARY ({total} batted balls)")
        print("=" * 80)
        
        for ball_type in ['ground_ball', 'line_drive', 'fly_ball', 'pop_up']:
            count = batted_ball_types[ball_type]
            pct = (count / total) * 100
            print(f"  {ball_type:12s}: {count:3d} ({pct:5.1f}%)")
        
        print("\n" + "=" * 80)
        print("STATISTICS")
        print("=" * 80)
        print(f"  Mean:   {np.mean(launch_angles):6.1f}°")
        print(f"  Median: {np.median(launch_angles):6.1f}°")
        print(f"  Std Dev: {np.std(launch_angles):5.1f}°")
        print(f"  Min:    {np.min(launch_angles):6.1f}°")
        print(f"  Max:    {np.max(launch_angles):6.1f}°")
        
        print("\n" + "=" * 80)
        print("MLB TARGETS")
        print("=" * 80)
        print(f"  Ground balls: ~45%")
        print(f"  Line drives:  ~20%")
        print(f"  Fly balls:    ~35%")
        print(f"  Mean launch:  ~12-15°")
        print(f"  Std Dev:      ~15-20°")
    
    print("\n" + "=" * 80)
    print(f"Final Score: Away {final_state.away_score} - Home {final_state.home_score}")
    print("=" * 80)

if __name__ == "__main__":
    test_launch_angle_details()
