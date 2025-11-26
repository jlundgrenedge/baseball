"""
Quick test to diagnose baserunning scoring bug
"""
from batted_ball.field_layout import FieldLayout, FieldPosition
from batted_ball.baserunning import BaseRunner, BaserunningSimulator
from batted_ball.play_outcome import PlayOutcome, PlayResult
from batted_ball.hit_handler import HitHandler

# Enable debug mode by patching
import batted_ball.hit_handler as hit_handler_module

# Mock class for BattedBallResult
class MockBattedBallResult:
    def __init__(self, landing_x, landing_y, peak_height=50.0, exit_velocity=85.0):
        self.landing_x = landing_x
        self.landing_y = landing_y
        self.peak_height = peak_height
        self.initial_conditions = {
            'exit_velocity': exit_velocity,
            'launch_angle': 15.0,
            'contact_quality': 'fair'
        }

def test_runner_on_third_single():
    """Test that runner on 3rd scores on a single"""
    print("=" * 60)
    print("TEST: Runner on 3rd, batter hits single")
    print("=" * 60)

    # Setup
    field_layout = FieldLayout()
    baserunning_sim = BaserunningSimulator(field_layout)

    # Add runner on third
    runner_on_third = BaseRunner(name="Runner3", sprint_speed=50, base_running_iq=50)
    runner_on_third.current_base = "third"
    baserunning_sim.add_runner("third", runner_on_third)

    # Add batter-runner at home
    batter = BaseRunner(name="Batter", sprint_speed=50, base_running_iq=50)
    batter.current_base = "home"
    baserunning_sim.add_runner("home", batter)

    print(f"Initial runners: {list(baserunning_sim.runners.keys())}")
    print(f"  - Runner on 3rd: {runner_on_third.name}")
    print(f"  - Batter at home: {batter.name}")

    # Create hit handler with DEBUG enabled
    hit_handler = HitHandler(baserunning_sim, current_outs=0)

    # Temporarily enable debug
    original_debug = False
    try:
        # Patch the DEBUG_BASERUNNING variable
        import types
        if hasattr(hit_handler_module, 'HitHandler'):
            # Modify the method to enable debug
            original_method = hit_handler.handle_hit_baserunning

            def debug_handle_hit_baserunning(result, current_outs=0):
                # Print debug info
                print("\n[DEBUG] handle_hit_baserunning called")
                print(f"[DEBUG] Outcome: {result.outcome}")
                print(f"[DEBUG] Runners before: {list(baserunning_sim.runners.keys())}")

                # Get existing runners
                runners_to_process = []
                for base in ["third", "second", "first"]:
                    if base in baserunning_sim.runners:
                        runner = baserunning_sim.runners[base]
                        if runner != batter:
                            runners_to_process.append((base, runner))

                print(f"[DEBUG] Runners to process: {[base for base, _ in runners_to_process]}")

                # Call original method
                result_obj = original_method(result, current_outs)

                print(f"[DEBUG] Runners after: {list(baserunning_sim.runners.keys())}")
                print(f"[DEBUG] Runs scored: {result.runs_scored}")
                print(f"[DEBUG] Final runner positions: {list(result.final_runner_positions.keys())}")

                return result_obj

            hit_handler.handle_hit_baserunning = debug_handle_hit_baserunning

        # Create play result with single
        result = PlayResult()
        result.outcome = PlayOutcome.SINGLE
        result.runs_scored = 0

        # Create batted ball result
        batted_ball = MockBattedBallResult(
            landing_x=0.0,
            landing_y=200.0,  # Single to center field
            peak_height=50.0,
            exit_velocity=85.0
        )
        result.batted_ball_result = batted_ball

        print("\nCalling determine_hit_type()...")
        ball_position = FieldPosition(0.0, 200.0, 0.0)
        hit_handler.determine_hit_type(ball_position, 200.0, result)

        print("\n" + "=" * 60)
        print("RESULTS:")
        print("=" * 60)
        print(f"Outcome: {result.outcome.value}")
        print(f"Runs scored: {result.runs_scored}")
        print(f"Final runners: {list(result.final_runner_positions.keys())}")

        if result.runs_scored == 1:
            print("✓ SUCCESS: Runner scored from 3rd!")
        else:
            print("✗ FAILURE: Runner did not score from 3rd!")
            print("  Expected: 1 run scored")
            print(f"  Actual: {result.runs_scored} runs scored")

    finally:
        pass

    return result.runs_scored == 1


def test_runner_on_second_single():
    """Test that runner on 2nd usually scores on a single"""
    print("\n\n" + "=" * 60)
    print("TEST: Runner on 2nd, batter hits single to CF (200ft)")
    print("=" * 60)

    # Setup
    field_layout = FieldLayout()
    baserunning_sim = BaserunningSimulator(field_layout)

    # Add runner on second
    runner_on_second = BaseRunner(name="Runner2", sprint_speed=50, base_running_iq=50)
    runner_on_second.current_base = "second"
    baserunning_sim.add_runner("second", runner_on_second)

    # Add batter-runner at home
    batter = BaseRunner(name="Batter", sprint_speed=50, base_running_iq=50)
    batter.current_base = "home"
    baserunning_sim.add_runner("home", batter)

    print(f"Initial runners: {list(baserunning_sim.runners.keys())}")

    # Create hit handler
    hit_handler = HitHandler(baserunning_sim, current_outs=0)

    # Create play result with single
    result = PlayResult()
    result.outcome = PlayOutcome.SINGLE
    result.runs_scored = 0

    # Create batted ball result (single to CF, not shallow)
    batted_ball = MockBattedBallResult(
        landing_x=0.0,
        landing_y=200.0,  # Deep enough single
        peak_height=50.0,
        exit_velocity=85.0
    )
    result.batted_ball_result = batted_ball

    print("\nProcessing single...")
    ball_position = FieldPosition(0.0, 200.0, 0.0)
    hit_handler.determine_hit_type(ball_position, 200.0, result)

    print("\n" + "=" * 60)
    print("RESULTS:")
    print("=" * 60)
    print(f"Outcome: {result.outcome.value}")
    print(f"Runs scored: {result.runs_scored}")
    print(f"Final runners: {list(result.final_runner_positions.keys())}")

    if result.runs_scored == 1:
        print("✓ SUCCESS: Runner scored from 2nd!")
    else:
        print("✗ FAILURE: Runner did not score from 2nd!")
        print("  Expected: 1 run scored (runner from 2nd scores on single)")
        print(f"  Actual: {result.runs_scored} runs scored")

    return result.runs_scored == 1


if __name__ == "__main__":
    test1_passed = test_runner_on_third_single()
    test2_passed = test_runner_on_second_single()

    print("\n\n" + "=" * 60)
    print("TEST SUMMARY")
    print("=" * 60)
    print(f"Runner on 3rd + single: {'PASS' if test1_passed else 'FAIL'}")
    print(f"Runner on 2nd + single: {'PASS' if test2_passed else 'FAIL'}")

    if test1_passed and test2_passed:
        print("\n✓ All tests passed - baserunning logic is working!")
        print("  The bug must be elsewhere (game state management or play setup)")
    else:
        print("\n✗ Tests failed - baserunning logic has a bug!")
