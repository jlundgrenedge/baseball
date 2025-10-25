"""
Complete play scenarios using fielding and baserunning mechanics.

Demonstrates various game situations and how the integrated physics
produces realistic outcomes for different types of batted balls and
defensive scenarios.
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from batted_ball import (
    # Core simulation
    BattedBallSimulator, create_standard_environment,
    Pitcher, Hitter,
    # Fielding and baserunning
    create_standard_defense, create_elite_defense,
    create_speed_runner, create_average_runner, create_slow_runner,
    create_elite_fielder, create_average_fielder, create_poor_fielder,
    simulate_play_from_trajectory,
    FieldLayout, FieldPosition, create_standard_field,
)


def scenario_routine_ground_ball():
    """Routine ground ball to shortstop."""
    print("=== SCENARIO 1: ROUTINE GROUND BALL ===")
    
    # Set up simulation
    env = create_standard_environment()
    simulator = BattedBallSimulator()
    
    # Moderate ground ball to shortstop
    ball_result = simulator.simulate(
        exit_velocity=78,
        launch_angle=6,
        spray_angle=0,  # Straight up middle
        backspin_rpm=800
    )
    
    # Standard defense, average batter speed
    defense = create_standard_defense()
    batter_runner = create_average_runner("Average Batter")
    
    # Simulate play
    play_result = simulate_play_from_trajectory(ball_result, defense, batter_runner)
    
    print(f"Outcome: {play_result.outcome}")
    print(f"Description: {play_result.play_description}")
    print()
    
    # Show why this outcome occurred
    if play_result.fielding_results:
        fielding = play_result.fielding_results[0]
        print(f"Fielding: Ball arrived at {fielding.ball_arrival_time:.2f}s")
        print(f"Fielder arrived at {fielding.fielder_arrival_time:.2f}s")
        print(f"Fielding successful: {fielding.success}")
    
    print()


def scenario_deep_fly_ball():
    """Deep fly ball to center field."""
    print("=== SCENARIO 2: DEEP FLY BALL ===")
    
    env = create_standard_environment()
    simulator = BattedBallSimulator()
    
    # Deep fly ball
    ball_result = simulator.simulate(
        exit_velocity=95,
        launch_angle=35,
        spray_angle=0,  # Center field
        backspin_rpm=2200
    )
    
    # Test with different defensive quality
    scenarios = [
        ("Average Defense", create_standard_defense()),
        ("Elite Defense", create_elite_defense())
    ]
    
    for def_name, defense in scenarios:
        batter_runner = create_average_runner("Batter")
        play_result = simulate_play_from_trajectory(ball_result, defense, batter_runner)
        
        print(f"{def_name}:")
        print(f"  Outcome: {play_result.outcome}")
        print(f"  Events: {len(play_result.events)}")
        
        # Show catch attempt details
        if play_result.fielding_results:
            fielding = play_result.fielding_results[0]
            margin = fielding.ball_arrival_time - fielding.fielder_arrival_time
            print(f"  Catch margin: {margin:.2f}s ({'made it' if margin > 0 else 'too late'})")
        
        print()


def scenario_slow_runner_vs_strong_arm():
    """Slow runner vs. strong-armed fielder."""
    print("=== SCENARIO 3: SLOW RUNNER VS. STRONG ARM ===")
    
    env = create_standard_environment()
    simulator = BattedBallSimulator()
    
    # Sharp ground ball to third base
    ball_result = simulator.simulate(
        exit_velocity=88,
        launch_angle=8,
        spray_angle=-45,  # Third base line
        backspin_rpm=900
    )
    
    # Test different runner speeds against elite defense
    runners = [
        ("Speed Runner", create_speed_runner("Fast")),
        ("Average Runner", create_average_runner("Average")),
        ("Slow Runner", create_slow_runner("Slow"))
    ]
    
    defense = create_elite_defense()  # Strong-armed third baseman
    
    for runner_name, batter_runner in runners:
        play_result = simulate_play_from_trajectory(ball_result, defense, batter_runner)
        
        print(f"{runner_name}:")
        print(f"  Outcome: {play_result.outcome}")
        print(f"  Home-to-first time: {batter_runner.get_home_to_first_time():.2f}s")
        
        # Show timing details if there was a play at first
        if play_result.events:
            for event in play_result.events:
                if "first base" in event.description.lower():
                    print(f"  Play timing: {event.description}")
        
        print()


def scenario_gap_shot_with_runners():
    """Ball in the gap with runners on base."""
    print("=== SCENARIO 4: GAP SHOT WITH RUNNERS ===")
    
    env = create_standard_environment()
    simulator = BattedBallSimulator()
    
    # Line drive to right-center gap
    ball_result = simulator.simulate(
        exit_velocity=98,
        launch_angle=12,
        spray_angle=30,  # Right-center gap
        backspin_rpm=2000
    )
    
    # Set up play with runners
    from batted_ball.play_simulation import PlaySimulator
    
    play_sim = PlaySimulator()
    
    # Add defense
    defense = create_standard_defense()
    play_sim.setup_defense(defense)
    
    # Add runners on first and second
    runner_on_first = create_speed_runner("Runner on 1st")
    runner_on_second = create_average_runner("Runner on 2nd")
    baserunners = {
        "first": runner_on_first,
        "second": runner_on_second
    }
    play_sim.setup_baserunners(baserunners)
    
    # Batter-runner
    batter_runner = create_average_runner("Batter")
    
    # Simulate complete play
    play_result = play_sim.simulate_complete_play(ball_result, batter_runner)
    
    print(f"Outcome: {play_result.outcome}")
    print(f"Runs scored: {play_result.runs_scored}")
    print()
    
    print("Play sequence:")
    for event in play_result.get_events_chronological():
        print(f"  {event.time:.1f}s: {event.description}")
    
    print()


def scenario_bunt_defense():
    """Bunt attempt with good defense."""
    print("=== SCENARIO 5: BUNT ATTEMPT ===")
    
    env = create_standard_environment()
    simulator = BattedBallSimulator()
    
    # Bunt down third base line
    ball_result = simulator.simulate(
        exit_velocity=45,  # Soft contact
        launch_angle=25,   # Angle for bunt
        spray_angle=-35,     # Third base side
        backspin_rpm=500       # Little spin
    )
    
    # Elite defense (quick reactions, good arms)
    defense = create_elite_defense()
    
    # Test different runner speeds
    runners = [
        ("Fast Runner", create_speed_runner("Speedster")),
        ("Average Runner", create_average_runner("Regular")),
    ]
    
    for runner_name, batter_runner in runners:
        play_result = simulate_play_from_trajectory(ball_result, defense, batter_runner)
        
        print(f"{runner_name} bunting:")
        print(f"  Outcome: {play_result.outcome}")
        
        # Analyze why outcome occurred
        if play_result.fielding_results:
            fielding = play_result.fielding_results[0]
            print(f"  Ball fielded by: {fielding.fielder_name}")
            print(f"  Fielding time: {fielding.ball_arrival_time:.2f}s")
        
        print()


def scenario_home_run_distance():
    """Test home run scenarios."""
    print("=== SCENARIO 6: HOME RUN ANALYSIS ===")
    
    env = create_standard_environment()
    simulator = BattedBallSimulator()
    
    # Different home run scenarios
    hr_scenarios = [
        ("Just enough", 94, 28, 2200),
        ("No doubter", 105, 25, 2400),
        ("Upper deck", 110, 22, 2500),
    ]
    
    for scenario_name, exit_velo, launch_angle, backspin in hr_scenarios:
        ball_result = simulator.simulate(
            exit_velocity=exit_velo,
            launch_angle=launch_angle,
            spray_angle=0,  # Center field
            backspin_rpm=backspin
        )
        
        distance = ball_result.distance
        max_height = ball_result.peak_height
        hang_time = ball_result.flight_time
        
        print(f"{scenario_name}:")
        print(f"  Distance: {distance:.0f} ft")
        print(f"  Max height: {max_height:.0f} ft")
        print(f"  Hang time: {hang_time:.1f}s")
        
        # Check if outfielders had any chance
        field = create_standard_field()
        ball_landing = FieldPosition(ball_result.landing_x, ball_result.landing_y, ball_result.landing_z)
        ball_pos = ball_landing  # ball_landing is already in feet
        
        # Would center fielder have a chance?
        cf = create_elite_fielder("CF", "outfield")
        cf_start = field.get_defensive_position("center_field")
        cf.update_position(cf_start)
        
        could_catch = cf.can_reach_ball(ball_pos, hang_time)
        print(f"  Catchable by elite CF: {'Yes' if could_catch else 'No'}")
        
        print()


def run_all_scenarios():
    """Run all play scenarios."""
    print("COMPLETE PLAY SCENARIOS")
    print("=" * 40)
    print()
    
    scenarios = [
        scenario_routine_ground_ball,
        scenario_deep_fly_ball,
        scenario_slow_runner_vs_strong_arm,
        scenario_gap_shot_with_runners,
        scenario_bunt_defense,
        scenario_home_run_distance,
    ]
    
    for scenario in scenarios:
        try:
            scenario()
        except Exception as e:
            print(f"Error in scenario: {e}")
            print()
    
    print("All scenarios completed!")
    print("\nThese scenarios demonstrate:")
    print("- Physics-based outcomes varying with player attributes")
    print("- Realistic timing comparisons for close plays")
    print("- Multi-runner advancement logic")
    print("- Integration of trajectory, fielding, and baserunning")
    print("- Defensive skill impact on play outcomes")


if __name__ == "__main__":
    run_all_scenarios()
