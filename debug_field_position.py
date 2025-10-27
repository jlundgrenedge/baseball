"""
Debug FieldPosition object to see if y-values are really zero or just display issue.
"""
from batted_ball.game_simulation import GameSimulator, create_test_team
from batted_ball import play_simulation

home_team = create_test_team("Home")
away_team = create_test_team("Away")

# Patch _analyze_batted_ball to show detailed info
original_analyze = play_simulation.PlaySimulator._analyze_batted_ball

def debug_analyze(self, batted_ball_result):
    """Show detailed field position info."""
    landing_pos, hang_time, is_air_ball = original_analyze(self, batted_ball_result)
    
    launch_angle = batted_ball_result.initial_conditions.get('launch_angle', 0.0)
    
    # Only print fly balls
    if 25 <= launch_angle < 50:
        print(f"\nFLY BALL:")
        print(f"  BattedBallResult.landing_x: {batted_ball_result.landing_x:.1f}ft")
        print(f"  BattedBallResult.landing_y: {batted_ball_result.landing_y:.1f}ft")
        print(f"  FieldPosition.x: {landing_pos.x:.1f}ft")
        print(f"  FieldPosition.y: {landing_pos.y:.1f}ft")
        print(f"  FieldPosition.z: {landing_pos.z:.1f}ft")
        print(f"  Hang time: {hang_time:.2f}s")
    
    return landing_pos, hang_time, is_air_ball

play_simulation.PlaySimulator._analyze_batted_ball = debug_analyze

# Run short game
simulator = GameSimulator(away_team, home_team, verbose=False)
final_state = simulator.simulate_game(num_innings=2)

print(f"\n{'=' * 80}")
print(f"Game complete")
