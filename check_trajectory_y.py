"""Check if trajectory landing positions have correct y-values."""
from batted_ball.game_simulation import GameSimulator, create_test_team

home_team = create_test_team("Home")
away_team = create_test_team("Away")
simulator = GameSimulator(away_team, home_team, verbose=False)
final_state = simulator.simulate_game(num_innings=3)

print("TRAJECTORY LANDING POSITIONS")
print("=" * 80)

for play in simulator.play_by_play:
    physics_data = getattr(play, 'physics_data', None)
    if physics_data and 'launch_angle_deg' in physics_data:
        launch_angle = physics_data['launch_angle_deg']
        
        # Check all batted balls
        if launch_angle > -10:  # Any batted ball
            # Get the batted ball result if available
            batted_ball_result = getattr(play, 'batted_ball_result', None)
            if batted_ball_result:
                print(f"\nLaunch angle: {launch_angle:.1f}°")
                print(f"  landing_x: {batted_ball_result.landing_x:.1f}ft")
                print(f"  landing_y: {batted_ball_result.landing_y:.1f}ft")
                print(f"  Distance: {batted_ball_result.distance:.1f}ft")
                print(f"  Spray angle: {batted_ball_result.spray_angle_landing:.1f}°")
                
                if abs(batted_ball_result.landing_y) < 1.0:
                    print(f"  ⚠️ WARNING: Ball landed on foul line (y ≈ 0)!")
