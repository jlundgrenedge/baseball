"""
Quick debug to understand the hit/scoring flow
"""
from batted_ball.player import Pitcher, Hitter
from batted_ball.game_simulation import create_test_team
from batted_ball.at_bat import AtBatSimulator
from batted_ball.play_simulation import PlaySimulator
from batted_ball.defense_factory import create_standard_defense
from batted_ball.baserunning import BaserunningSimulator, BaseRunner
from batted_ball.environment import create_standard_environment

# Patch hit_handler to add debug output
import batted_ball.hit_handler as hit_handler_module

original_determine = hit_handler_module.HitHandler.determine_hit_type
original_handle_br = hit_handler_module.HitHandler.handle_hit_baserunning

def debug_determine_hit_type(self, ball_position, distance_ft, result):
    print(f"\n[DEBUG determine_hit_type] Called!")
    print(f"  Current outcome: {result.outcome}")
    print(f"  Distance: {distance_ft:.1f} ft")
    print(f"  Runners in simulator: {list(self.baserunning_simulator.runners.keys())}")
    ret = original_determine(self, ball_position, distance_ft, result)
    print(f"  After determine_hit_type, outcome: {result.outcome}")
    print(f"  Runs scored: {result.runs_scored}")
    return ret

def debug_handle_hit_baserunning(self, result, current_outs=0):
    print(f"\n[DEBUG handle_hit_baserunning] Called!")
    print(f"  Outcome: {result.outcome}")
    print(f"  Runners before: {list(self.baserunning_simulator.runners.keys())}")
    ret = original_handle_br(self, result, current_outs)
    print(f"  Runners after: {list(self.baserunning_simulator.runners.keys())}")
    print(f"  Runs scored: {result.runs_scored}")
    print(f"  Final runner positions: {list(result.final_runner_positions.keys())}")
    return ret

hit_handler_module.HitHandler.determine_hit_type = debug_determine_hit_type
hit_handler_module.HitHandler.handle_hit_baserunning = debug_handle_hit_baserunning

# Run a quick test
road_team, home_team = create_test_team("Road"), create_test_team("Home")
env = create_standard_environment()

print("=" * 60)
print("Testing hit scoring with runner on 3rd")
print("=" * 60)

for i in range(5):
    # Create at-bat
    pitcher = road_team.pitchers[0]
    hitter = home_team.hitters[0]

    at_bat_sim = AtBatSimulator(pitcher, hitter)
    at_bat_result = at_bat_sim.simulate_at_bat()

    # Only test if ball was put in play
    if at_bat_result.outcome not in ["strikeout", "walk"]:
        # Create play simulation
        defense = create_standard_defense()
        play_sim = PlaySimulator(defense, env)

        # Add runner on third
        runner = BaseRunner(name="Runner3", sprint_speed=60.0, base_running_iq=60.0)
        runner.current_base = "third"
        play_sim.baserunning_simulator.add_runner("third", runner)

        # Simulate play
        play_result = play_sim.simulate_play(at_bat_result, current_outs=0)

        # Check result
        if play_result.outcome.value in ["single", "double", "triple", "home_run"]:
            print(f"\n{'='*60}")
            print(f"Hit #{i+1}: {play_result.outcome.value}")
            print(f"Runs scored: {play_result.runs_scored}")
            print(f"Final runners: {list(play_result.final_runner_positions.keys())}")
            print(f"{'='*60}\n")
            break
