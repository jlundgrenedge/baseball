
import sys
import os
import numpy as np

# Add the current directory to the path so we can import the modules
sys.path.append(os.getcwd())

from batted_ball.game_simulation import GameState, GameSimulator, Team, create_test_team
from batted_ball.play_simulation import PlaySimulator
from batted_ball.play_outcome import PlayOutcome, PlayResult
from batted_ball.trajectory import BattedBallResult
from batted_ball.baserunning import BaseRunner

def reproduce_phantom_run():
    print("Reproducing Phantom Run Bug...")
    
    # Create teams
    away_team = create_test_team("Away Team")
    home_team = create_test_team("Home Team")
    
    # Create simulator
    sim = GameSimulator(away_team, home_team, verbose=True)
    
    # Manually set up a situation: Runner on 3rd, 0 outs
    sim.game_state.runner_on_third = away_team.hitters[0]
    sim.game_state.outs = 0
    sim.game_state.is_top = True
    
    print(f"Initial Score: Away {sim.game_state.away_score} - Home {sim.game_state.home_score}")
    print(f"Runner on 3rd: {sim.game_state.runner_on_third.name}")
    
    # Create a mock play result that simulates a single where runner scores
    # We'll use the PlaySimulator directly to generate the result to test the handler logic
    
    play_sim = PlaySimulator()
    play_sim.setup_defense(home_team.fielders)
    
    # Setup runner on 3rd
    runner_on_3rd = BaseRunner(sim.game_state.runner_on_third.name, sprint_speed=60000) # Fast runner
    play_sim.setup_baserunners({"third": runner_on_3rd})
    
    # Create batter runner
    batter = away_team.hitters[1]
    batter_runner = BaseRunner(batter.name, sprint_speed=60000)
    

import sys
import os
import numpy as np

# Add the current directory to the path so we can import the modules
sys.path.append(os.getcwd())

from batted_ball.game_simulation import GameState, GameSimulator, Team, create_test_team
from batted_ball.play_simulation import PlaySimulator
from batted_ball.play_outcome import PlayOutcome, PlayResult, PlayEvent
from batted_ball.trajectory import BattedBallResult
from batted_ball.baserunning import BaseRunner

def reproduce_phantom_run():
    print("Reproducing Phantom Run Bug...")
    
    # Create teams
    away_team = create_test_team("Away Team")
    home_team = create_test_team("Home Team")
    
    # Create simulator
    sim = GameSimulator(away_team, home_team, verbose=True)
    
    # Manually set up a situation: Runner on 3rd, 0 outs
    sim.game_state.runner_on_third = away_team.hitters[0]
    sim.game_state.outs = 0
    sim.game_state.is_top = True
    
    print(f"Initial Score: Away {sim.game_state.away_score} - Home {sim.game_state.home_score}")
    print(f"Runner on 3rd: {sim.game_state.runner_on_third.name}")
    
    # Create a mock play result that simulates a single where runner scores
    # We'll use the PlaySimulator directly to generate the result to test the handler logic
    
    play_sim = PlaySimulator()
    play_sim.setup_defense(home_team.fielders)
    
    # Setup runner on 3rd
    runner_on_3rd = BaseRunner(sim.game_state.runner_on_third.name, sprint_speed=60000) # Fast runner
    play_sim.setup_baserunners({"third": runner_on_3rd})
    
    # Create batter runner
    batter = away_team.hitters[1]
    batter_runner = BaseRunner(batter.name, sprint_speed=60000)
    

    # Create a batted ball result (Single to center-right field)
    # We need to mock BattedBallResult

    # Create a batted ball result (Line drive to right-center gap)
    # We need to mock BattedBallResult

    # Create a batted ball result (Bloop Single


    # GAP DOUBLE SIMULATION
    print("\n--- GAP DOUBLE SIMULATION ---")
    


    # Create a batted ball result (Gap Double to right-center)
    # Use BattedBallResult directly to avoid attribute errors
    
    # Mock trajectory arrays (needed for interception logic)
    steps = 100
    time = np.linspace(0, 3.0, steps)
    position = np.zeros((steps, 3))
    
    # Populate trajectory (simple arc)
    M_TO_FT = 3.28084
    traj_x_end = 100.0 / M_TO_FT
    traj_y_end = 350.0 / M_TO_FT
    
    # Linear x/y, parabolic z
    position[:, 0] = np.linspace(0, traj_x_end, steps)
    position[:, 1] = np.linspace(0, traj_y_end, steps)
    position[:, 2] = (40.0 / M_TO_FT) * np.sin(np.pi * time / 3.0)
    
    # Velocity (derivative)
    velocity = np.zeros((steps, 3))
    velocity[:, 0] = traj_x_end / 3.0
    velocity[:, 1] = traj_y_end / 3.0
    velocity[:, 2] = 0 # Simplified
    
    batted_ball = BattedBallResult(
        {
            'time': time,
            'position': position,
            'velocity': velocity
        },
        {'contact_quality': 'solid', 'exit_velocity': 105.0, 'launch_angle': 20.0},
        None
    )
    # Manually set derived properties that might be calculated in __init__
    batted_ball.landing_x = 100.0
    batted_ball.landing_y = 350.0
    batted_ball.hang_time = 3.0
    batted_ball.peak_height = 40.0
    batted_ball.flight_time = 3.0
    batted_ball.distance = 364.0
    


    # Monkeypatch FlyBallHandler to force a hit (prevent catch)
    original_interception = play_sim.fly_ball_handler.attempt_trajectory_interception
    play_sim.fly_ball_handler.attempt_trajectory_interception = lambda *args, **kwargs: False
    

    # Monkeypatch HitHandler to debug runs_scored
    original_handle_hit = play_sim.hit_handler.handle_hit_baserunning
    
    def debug_handle_hit(result, current_outs=0):
        print(f"DEBUG: Calling handle_hit_baserunning. Initial runs: {result.runs_scored}")
        original_handle_hit(result, current_outs)
        print(f"DEBUG: Finished handle_hit_baserunning. Final runs: {result.runs_scored}")
        
    play_sim.hit_handler.handle_hit_baserunning = debug_handle_hit
    
    # Also patch simulate_catch_attempt to fail
    original_catch = play_sim.fly_ball_handler.simulate_catch_attempt
    class MockCatchResult:
        def __init__(self):
            self.success = False
            self.failure_reason = 'TOO_SLOW'
            self.fielder_arrival_time = 10.0
            self.ball_arrival_time = 3.0
            self.catch_position = None
            self.fielder_name = "right_field"
            self.fielder_position = "right_field"
            
    play_sim.fly_ball_handler.simulate_catch_attempt = lambda *args, **kwargs: MockCatchResult()

    # Simulate the play
    print("\nSimulating Play...")
    play_result = play_sim.simulate_complete_play(
        batted_ball_result=batted_ball,
        batter_runner=batter_runner,
        current_outs=0
    )
    
    # Restore original methods (good practice)
    play_sim.fly_ball_handler.attempt_trajectory_interception = original_interception
    play_sim.fly_ball_handler.simulate_catch_attempt = original_catch
    play_sim.hit_handler.handle_hit_baserunning = original_handle_hit
    

    # Write results to log file
    with open("reproduction_log.txt", "w") as f:
        f.write(f"Play Outcome: {play_result.outcome}\n")
        f.write(f"Runs Scored (in PlayResult): {play_result.runs_scored}\n")
        
        f.write("\nEvents:\n")
        for event in play_result.get_events_chronological():
            f.write(f"[{event.time:.2f}s] {event.description}\n")
            
        f.write("\nUpdating Game State...\n")
        # Reset score first to be sure
        sim.game_state.away_score = 0
        sim.game_state.home_score = 0
        sim.process_play_result(play_result, batter, home_team.pitchers[0])
        
        f.write(f"\nFinal Score: Away {sim.game_state.away_score} - Home {sim.game_state.home_score}\n")
        
        if play_result.runs_scored > 0 and sim.game_state.away_score == 0:
            f.write("\nFAILURE: Phantom Run Detected! PlayResult has runs, but GameState score is 0.\n")
        elif play_result.runs_scored == 0:
            # Check if runner scored in logs
            runner_scored_log = any("scores" in e.description for e in play_result.events)
            if runner_scored_log:
                 f.write("\nFAILURE: Log says runner scored, but runs_scored is 0!\n")
            else:
                 f.write("\nINFO: Runner did not score (maybe held at 3rd?). Check logic.\n")
        else:
            f.write("\nSUCCESS: Run scored and recorded correctly.\n")
            
    # Also print to stdout for immediate feedback if possible
    print(open("reproduction_log.txt").read())

if __name__ == "__main__":
    reproduce_phantom_run()
