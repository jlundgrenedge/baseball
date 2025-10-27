"""
Debug the catch attempt process for fly balls.
"""
from batted_ball.game_simulation import GameSimulator, create_test_team
from batted_ball.play_simulation import PlayOutcome
from batted_ball import play_simulation

home_team = create_test_team("Home")
away_team = create_test_team("Away")

# Patch simulate_catch_attempt to add debug output
original_catch_attempt = play_simulation.PlaySimulator._simulate_catch_attempt

fly_ball_count = 0
catch_attempt_count = 0

def debug_catch_attempt(self, ball_position, hang_time, result):
    """Wrapper to debug catch attempts."""
    global catch_attempt_count
    catch_attempt_count += 1
    
    print(f"\nCATCH ATTEMPT #{catch_attempt_count}:")
    print(f"  Ball position: ({ball_position.x:.1f}, {ball_position.y:.1f})")
    print(f"  Hang time: {hang_time:.2f}s")
    
    # Call original
    catch_result = original_catch_attempt(self, ball_position, hang_time, result)
    
    print(f"  Catch success: {catch_result.success}")
    print(f"  Responsible fielder: {self.fielding_simulator.determine_responsible_fielder(ball_position, hang_time)}")
    
    return catch_result

# Patch
play_simulation.PlaySimulator._simulate_catch_attempt = debug_catch_attempt

# Also patch _analyze to count fly balls
original_analyze = play_simulation.PlaySimulator._analyze_batted_ball

def debug_analyze(self, batted_ball_result):
    """Count fly balls."""
    global fly_ball_count
    landing_pos, hang_time, is_air_ball = original_analyze(self, batted_ball_result)
    
    launch_angle = batted_ball_result.initial_conditions.get('launch_angle', 0.0)
    if 25 <= launch_angle < 50:
        fly_ball_count += 1
    
    return landing_pos, hang_time, is_air_ball

play_simulation.PlaySimulator._analyze_batted_ball = debug_analyze

# Run short game
simulator = GameSimulator(away_team, home_team, verbose=False)
final_state = simulator.simulate_game(num_innings=3)

print(f"\n{'=' * 80}")
print(f"SUMMARY:")
print(f"  Total fly balls (25-50°): {fly_ball_count}")
print(f"  Total catch attempts: {catch_attempt_count}")
print(f"  Game score: {final_state.away_score} - {final_state.home_score}")

if fly_ball_count != catch_attempt_count:
    print(f"\n⚠️ WARNING: Mismatch! {fly_ball_count} fly balls but only {catch_attempt_count} catch attempts!")
