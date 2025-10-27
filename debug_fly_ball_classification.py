"""
Debug what happens to fly balls in the play simulation.
Track if they're being classified correctly and if catch attempts are happening.
"""
from batted_ball.game_simulation import GameSimulator, create_test_team
from batted_ball.play_simulation import PlayOutcome

home_team = create_test_team("Home")
away_team = create_test_team("Away")

# Patch the PlaySimulator to add debug output
from batted_ball import play_simulation
original_analyze = play_simulation.PlaySimulator._analyze_batted_ball

def debug_analyze(self, batted_ball_result):
    """Wrapper to debug ball classification."""
    landing_pos, hang_time, is_air_ball = original_analyze(self, batted_ball_result)
    
    launch_angle = batted_ball_result.initial_conditions.get('launch_angle', 0.0)
    max_height = batted_ball_result.peak_height
    distance = batted_ball_result.distance
    
    # Only print fly balls (25-50°)
    if 25 <= launch_angle < 50:
        print(f"\nFLY BALL DETECTED:")
        print(f"  Launch angle: {launch_angle:.1f}°")
        print(f"  Distance: {distance:.1f}ft")
        print(f"  Peak height: {max_height:.1f}ft")
        print(f"  Hang time: {hang_time:.2f}s")
        print(f"  Classified as AIR BALL: {is_air_ball}")
        if not is_air_ball:
            print(f"  ⚠️ WARNING: FLY BALL CLASSIFIED AS GROUND BALL!")
    
    return landing_pos, hang_time, is_air_ball

# Monkey patch
play_simulation.PlaySimulator._analyze_batted_ball = debug_analyze

# Run short game
simulator = GameSimulator(away_team, home_team, verbose=False)
final_state = simulator.simulate_game(num_innings=3)

print(f"\n{'=' * 80}")
print(f"Game complete: {final_state.away_score} - {final_state.home_score}")
