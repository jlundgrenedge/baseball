"""
Demonstration of fielding and baserunning mechanics.

Shows how to use the new fielding, baserunning, and play simulation
modules to create realistic baseball plays.
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from batted_ball import (
    # Existing modules
    BattedBallSimulator, create_standard_environment,
    Pitcher, Hitter, create_fastball_4seam,
    # New fielding/baserunning modules
    FieldLayout, create_standard_field,
    Fielder, create_elite_fielder, create_average_fielder, create_poor_fielder,
    BaseRunner, create_speed_runner, create_average_runner, create_slow_runner,
    PlaySimulator, create_standard_defense, create_elite_defense,
    simulate_play_from_trajectory
)


def demonstrate_fielding_attributes():
    """Demonstrate how fielding attributes affect performance."""
    print("=== FIELDING ATTRIBUTES DEMONSTRATION ===\n")
    
    # Create fielders with different skill levels
    elite_cf = create_elite_fielder("Elite CF", "outfield")
    avg_cf = create_average_fielder("Average CF", "outfield") 
    poor_cf = create_poor_fielder("Poor CF", "outfield")
    
    fielders = [
        ("Elite Center Fielder", elite_cf),
        ("Average Center Fielder", avg_cf),
        ("Poor Center Fielder", poor_cf)
    ]
    
    # Set up field layout and target position
    field = create_standard_field()
    cf_position = field.get_defensive_position("center_field")
    
    # Deep fly ball to center field
    deep_fly_position = field.position_from_coordinates(0, 350, 0)  # 350 feet to center
    hang_time = 4.5  # seconds
    
    print(f"Scenario: Deep fly ball to center field")
    print(f"Ball location: {deep_fly_position}")
    print(f"Hang time: {hang_time:.1f} seconds")
    print(f"Center fielder starting position: {cf_position}")
    print()
    
    for name, fielder in fielders:
        fielder.update_position(cf_position)
        
        # Calculate attributes
        sprint_speed = fielder.get_sprint_speed_fps()
        acceleration = fielder.get_acceleration_fps2()
        reaction_time = fielder.get_reaction_time_seconds()
        
        # Calculate time to reach ball
        time_needed = fielder.calculate_time_to_position(deep_fly_position)
        can_catch = fielder.can_reach_ball(deep_fly_position, hang_time)
        
        print(f"{name}:")
        print(f"  Sprint Speed: {sprint_speed:.1f} ft/s ({sprint_speed * 0.681818:.1f} mph)")
        print(f"  Acceleration: {acceleration:.1f} ft/s²")
        print(f"  Reaction Time: {reaction_time:.2f} seconds")
        print(f"  Time to reach ball: {time_needed:.2f} seconds")
        print(f"  Can make catch: {'YES' if can_catch else 'NO'}")
        print()


def demonstrate_baserunning_attributes():
    """Demonstrate how baserunning attributes affect performance."""
    print("=== BASERUNNING ATTRIBUTES DEMONSTRATION ===\n")
    
    # Create runners with different skill levels
    speed_runner = create_speed_runner("Speed Demon")
    avg_runner = create_average_runner("Average Runner")
    slow_runner = create_slow_runner("Slow Runner")
    
    runners = [
        ("Speed Runner", speed_runner),
        ("Average Runner", avg_runner),
        ("Slow Runner", slow_runner)
    ]
    
    print("Home-to-First Base Times:")
    print("-" * 40)
    
    for name, runner in runners:
        # Calculate attributes
        sprint_speed = runner.get_sprint_speed_fps()
        acceleration = runner.get_acceleration_fps2()
        reaction_time = runner.get_reaction_time_seconds()
        
        # Calculate home-to-first time
        h2f_time = runner.get_home_to_first_time()
        
        print(f"{name}:")
        print(f"  Sprint Speed: {sprint_speed:.1f} ft/s ({sprint_speed * 0.681818:.1f} mph)")
        print(f"  Acceleration: {acceleration:.1f} ft/s²")
        print(f"  Reaction Time: {reaction_time:.2f} seconds")
        print(f"  Home-to-First Time: {h2f_time:.2f} seconds")
        print()
    
    print("Expected MLB Range: 3.7s (elite) to 5.2s (slow)")
    print("MLB Average: ~4.3 seconds")
    print()


def demonstrate_simple_play():
    """Demonstrate a simple ground ball play."""
    print("=== SIMPLE GROUND BALL PLAY ===\n")
    
    # Set up players
    pitcher = Pitcher(name="Starter", velocity=75, command=60)
    hitter = Hitter(name="Contact Hitter", bat_speed=60, barrel_accuracy=70)
    
    # Create batted ball (ground ball to shortstop)
    env = create_standard_environment()
    simulator = BattedBallSimulator()
    
    # Simulate a ground ball (low launch angle, moderate exit velocity)
    ball_result = simulator.simulate(
        exit_velocity=85,
        launch_angle=5,  # Low angle = ground ball
        spray_angle=10,    # Toward shortstop area
        backspin_rpm=1000
    )
    
    # Set up defense
    defense = create_standard_defense()
    
    # Create batter-runner
    batter_runner = create_average_runner("Batter")
    
    # Simulate complete play
    play_result = simulate_play_from_trajectory(ball_result, defense, batter_runner)
    
    print("Play Result:")
    print(f"Outcome: {play_result.outcome}")
    print(f"Outs Made: {play_result.outs_made}")
    print(f"Description: {play_result.play_description}")
    print()
    
    print("Play Events:")
    for event in play_result.get_events_chronological():
        print(f"  {event.time:.2f}s: {event.description}")
    print()


def demonstrate_close_play():
    """Demonstrate a close play at first base."""
    print("=== CLOSE PLAY AT FIRST BASE ===\n")
    
    # Compare elite defense vs average defense on same batted ball
    env = create_standard_environment()
    simulator = BattedBallSimulator()
    
    # Sharp ground ball to third base
    ball_result = simulator.simulate(
        exit_velocity=95,  # Hard hit
        launch_angle=8,    # Ground ball
        spray_angle=-45,     # Down third base line
        backspin_rpm=800
    )
    
    # Two different defensive scenarios
    scenarios = [
        ("Average Defense", create_standard_defense(), create_average_runner("Average Batter")),
        ("Elite Defense", create_elite_defense(), create_average_runner("Same Batter"))
    ]
    
    for scenario_name, defense, batter_runner in scenarios:
        play_result = simulate_play_from_trajectory(ball_result, defense, batter_runner)
        
        print(f"{scenario_name}:")
        print(f"  Outcome: {play_result.outcome}")
        print(f"  Play: {play_result.play_description}")
        print()


def demonstrate_outfield_play():
    """Demonstrate an outfield play with runner advancement."""
    print("=== OUTFIELD PLAY WITH RUNNERS ===\n")
    
    # Set up scenario: Runner on first, ball hit to gap
    env = create_standard_environment()
    simulator = BattedBallSimulator()
    
    # Line drive to right-center gap
    ball_result = simulator.simulate(
        exit_velocity=102,  # Well-struck
        launch_angle=15,    # Line drive
        spray_angle=30,       # Right-center gap
        backspin_rpm=2200
    )
    
    # Set up play simulation
    play_sim = PlaySimulator()
    
    # Add defense
    defense = create_standard_defense()
    play_sim.setup_defense(defense)
    
    # Add runners
    runner_on_first = create_speed_runner("Fast Runner")
    baserunners = {"first": runner_on_first}
    play_sim.setup_baserunners(baserunners)
    
    # Add batter-runner
    batter_runner = create_average_runner("Batter")
    
    # Simulate the play
    play_result = play_sim.simulate_complete_play(ball_result, batter_runner)
    
    print("Multi-Runner Play:")
    print(f"Outcome: {play_result.outcome}")
    print(f"Runs Scored: {play_result.runs_scored}")
    print(f"Final Runner Positions: {play_result.final_runner_positions}")
    print()
    
    print("Detailed Events:")
    for event in play_result.get_events_chronological():
        print(f"  {event.time:.2f}s: {event.description}")
    print()


def validate_physics_realism():
    """Validate that physics produce realistic outcomes."""
    print("=== PHYSICS VALIDATION ===\n")
    
    # Test 1: Home-to-first times should be realistic
    print("1. Home-to-First Time Validation:")
    
    runners = [
        create_speed_runner("Elite Speed"),
        create_average_runner("Average Speed"), 
        create_slow_runner("Slow Speed")
    ]
    
    times = [runner.get_home_to_first_time() for runner in runners]
    print(f"   Elite speed: {times[0]:.2f}s (should be ~3.7-4.0s)")
    print(f"   Average speed: {times[1]:.2f}s (should be ~4.2-4.4s)")
    print(f"   Slow speed: {times[2]:.2f}s (should be ~4.8-5.2s)")
    print()
    
    # Test 2: Fielding ranges should be reasonable
    print("2. Fielding Range Validation:")
    
    field = create_standard_field()
    cf_pos = field.get_defensive_position("center_field")
    
    fielders = [
        create_elite_fielder("Elite CF", "outfield"),
        create_average_fielder("Average CF", "outfield"),
        create_poor_fielder("Poor CF", "outfield")
    ]
    
    # Test ball 100 feet away with 3-second hang time
    test_position = field.position_from_coordinates(0, 380, 0)  # 380 ft to center
    hang_time = 3.0
    
    for i, fielder in enumerate(fielders):
        fielder.update_position(cf_pos)
        can_catch = fielder.can_reach_ball(test_position, hang_time)
        time_needed = fielder.calculate_time_to_position(test_position)
        
        level = ["Elite", "Average", "Poor"][i]
        print(f"   {level} CF: {time_needed:.2f}s to reach (3.0s available) - {'CAN CATCH' if can_catch else 'TOO FAR'}")
    
    print()


def main():
    """Run all demonstrations."""
    print("BASEBALL FIELDING AND BASERUNNING DEMONSTRATION")
    print("=" * 50)
    print()
    
    demonstrate_fielding_attributes()
    demonstrate_baserunning_attributes()
    demonstrate_simple_play()
    demonstrate_close_play()
    demonstrate_outfield_play()
    validate_physics_realism()
    
    print("Demonstration complete!")
    print("\nKey Features Demonstrated:")
    print("- Physics-based fielding with reaction time, speed, and range")
    print("- Realistic baserunning with acceleration and turn efficiency")
    print("- Complete play simulation integrating all components")
    print("- Outcome determination based on timing comparisons")
    print("- Validation against MLB performance benchmarks")


if __name__ == "__main__":
    main()
