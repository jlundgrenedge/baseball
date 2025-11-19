
import sys
import os
import numpy as np

# Add the current directory to the path
sys.path.append(os.getcwd())


from batted_ball.game_simulation import GameState, GameSimulator, create_test_team
from batted_ball.play_simulation import PlaySimulator
from batted_ball.play_outcome import PlayOutcome, PlayResult, PlayEvent
from batted_ball.trajectory import BattedBallResult
from batted_ball.baserunning import BaseRunner
from batted_ball.field_layout import FieldPosition

def reproduce_infield_single():
    print("Reproducing Infield Single Bug...")
    
    # Create teams
    away_team = create_test_team("Away Team")
    home_team = create_test_team("Home Team")
    
    # Create simulator
    sim = GameSimulator(away_team, home_team, verbose=True)
    


    # Setup: Runner on 3rd, 0 outs
    sim.game_state.runner_on_third = away_team.hitters[0]
    sim.game_state.outs = 0
    
    print(f"Runner on 3rd: {sim.game_state.runner_on_third.name}")
    

    # Create a WEAK ground ball result (Infield Single)
    
    # Mock trajectory
    steps = 10
    time = np.linspace(0, 0.5, steps)
    position = np.zeros((steps, 3))
    position[:, 1] = np.linspace(0, 40.0, steps)
    velocity = np.zeros((steps, 3))
    

    batted_ball = BattedBallResult(
        {
            'time': time,
            'position': position,
            'velocity': velocity
        },
        {'contact_quality': 'weak', 'exit_velocity': 40.0, 'launch_angle': -10.0},
        None
    )
    # Manually set derived properties
    batted_ball.landing_x = 0.0
    batted_ball.landing_y = 40.0
    batted_ball.hang_time = 0.5
    batted_ball.peak_height = 2.0
    batted_ball.flight_time = 0.5
    batted_ball.distance = 40.0




    # Create PlaySimulator
    play_sim = PlaySimulator()
    play_sim.setup_defense(home_team.fielders)
    

    # Setup runner on 3rd in PlaySimulator
    runner_on_3rd = BaseRunner(sim.game_state.runner_on_third.name, sprint_speed=27.0)
    runner_on_3rd.current_base = "third"
    play_sim.setup_baserunners({"third": runner_on_3rd})
    

    # Create batter runner
    batter = away_team.hitters[1]
    batter_runner = BaseRunner(batter.name, sprint_speed=100000.0) # SUPERHUMAN Fast batter

    # Monkeypatch ThrowingLogic to force a SINGLE
    # This simulates the case where ThrowingLogic determines the batter is safe
    # We want to see if it advances other runners
    
    original_simulate_throw = play_sim.ground_ball_handler.throwing_logic.simulate_throw_to_first
    
    def force_single(fielder, release_time, batter_runner, result):
        print("DEBUG: Forcing SINGLE in ThrowingLogic")
        result.outcome = PlayOutcome.SINGLE
        # Logic copied from ThrowingLogic for a single
        batter_runner.current_base = "first"
        play_sim.baserunning_simulator.remove_runner("home")
        play_sim.baserunning_simulator.add_runner("first", batter_runner)
        result.final_runner_positions["first"] = batter_runner
        result.add_event(PlayEvent(0.0, "safe_at_first", "Safe at first (Forced)"))
        
    play_sim.ground_ball_handler.throwing_logic.simulate_throw_to_first = force_single
    
    # Simulate the play
    print("\nSimulating Play...")
    play_result = play_sim.simulate_complete_play(
        batted_ball_result=batted_ball,
        batter_runner=batter_runner,
        current_outs=0
    )
    
    # Restore
    play_sim.ground_ball_handler.throwing_logic.simulate_throw_to_first = original_simulate_throw
    
    print(f"\nPlay Outcome: {play_result.outcome}")
    print(f"Runs Scored: {play_result.runs_scored}")
    print(f"Final Runner Positions: {play_result.final_runner_positions.keys()}")
    
    print("\nEvents:")
    for event in play_result.get_events_chronological():
        print(f"[{event.time:.2f}s] {event.description}")
        
    # Check if runner on 3rd scored
    # If Infield Single, runner on 3rd SHOULD score (or at least try)
    # If runs_scored is 0, it confirms the bug
    
    if play_result.outcome == PlayOutcome.SINGLE and play_result.runs_scored == 0:
        print("\nFAILURE: Infield Single, but runner on 3rd did NOT score.")
    elif play_result.runs_scored > 0:
        print("\nSUCCESS: Runner scored.")
    else:
        print("\nUNCLEAR: Outcome was not SINGLE or other issue.")


if __name__ == "__main__":
    # Redirect stdout to file
    import sys
    original_stdout = sys.stdout
    with open("reproduction_log_infield.txt", "w") as f:
        sys.stdout = f
        try:
            reproduce_infield_single()
        finally:
            sys.stdout = original_stdout
    
    # Print file content to stdout for tool to capture (hopefully enough fits)
    with open("reproduction_log_infield.txt", "r") as f:
        print(f.read())
