"""Detailed fly ball debugging with fielder assignments and calculations."""
from batted_ball.game_simulation import GameSimulator, create_test_team
from batted_ball.play_simulation import PlayOutcome
import numpy as np

print("DETAILED FLY BALL FIELDING ANALYSIS")
print("=" * 80)

# Create teams and simulate
home_team = create_test_team("Home")
away_team = create_test_team("Away")
simulator = GameSimulator(away_team, home_team, verbose=False)
final_state = simulator.simulate_game(num_innings=9)

fly_ball_count = 0
caught_count = 0

for inning_result in simulator.results_tracker.inning_results:
    for half_inning in [inning_result.top, inning_result.bottom]:
        for pa in half_inning.plate_appearances:
            if pa.batted_ball_result and pa.batted_ball_result.is_fly_ball():
                fly_ball_count += 1
                
                # Get result details
                result = pa.play_result
                caught = result.outcome == PlayOutcome.FLY_OUT
                
                if caught:
                    caught_count += 1
                
                # Get ball info
                distance = pa.batted_ball_result.max_distance
                hang_time = pa.batted_ball_result.hang_time
                landing_x = pa.batted_ball_result.landing_position[0]
                landing_y = pa.batted_ball_result.landing_position[1]
                
                # Print details
                print(f"\nFly Ball #{fly_ball_count}:")
                print(f"  Distance: {distance:.1f}ft, Hang time: {hang_time:.2f}s")
                print(f"  Landing position: ({landing_x:.1f}, {landing_y:.1f})")
                print(f"  Outcome: {'CAUGHT' if caught else 'NOT CAUGHT'} - {result.outcome.name}")
                
                # Show fielding result if available
                if result.fielding_results:
                    fr = result.fielding_results[0]
                    print(f"  Fielder: {fr.fielder_name}")
                    print(f"  Fielder arrival time: {fr.fielder_arrival_time:.2f}s")
                    print(f"  Ball arrival time: {fr.ball_arrival_time:.2f}s")
                    print(f"  Time margin: {fr.ball_arrival_time - fr.fielder_arrival_time:.2f}s")
                    
                    # Check if this makes sense
                    if not caught and (fr.ball_arrival_time - fr.fielder_arrival_time) > 0:
                        print(f"  ⚠️ WARNING: Fielder arrived ON TIME but didn't catch!")
                

print(f"\n{'=' * 80}")
print(f"SUMMARY: {caught_count}/{fly_ball_count} fly balls caught ({100*caught_count/fly_ball_count if fly_ball_count > 0 else 0:.1f}%)")
print(f"Target: 75-80% catch rate")
