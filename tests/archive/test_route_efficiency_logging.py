"""
Test script for route efficiency logging feature.

Tests various fielding scenarios to validate that route efficiency metrics
are correctly calculated and logged for airborne batted balls.
"""

from batted_ball import (
    BattedBallSimulator,
    Environment,
    Pitcher,
    Hitter,
    AtBatSimulator,
)
from batted_ball.play_simulation import PlaySimulator
from batted_ball.fielding import Fielder
from batted_ball.attributes import FielderAttributes
from batted_ball.field_layout import FieldLayout
from batted_ball.trajectory import BattedBallResult
from batted_ball.play_outcome import PlayResult


def create_test_fielder(name: str, position: str, speed: int = 70000, reaction: int = 70000):
    """Create a test fielder with specified attributes (0-100,000 scale)."""
    attrs = FielderAttributes(
        REACTION_TIME=reaction,
        ACCELERATION=70000,
        TOP_SPRINT_SPEED=speed,
        ROUTE_EFFICIENCY=70000,
        AGILITY=70000,
        FIELDING_SECURE=70000,
        TRANSFER_TIME=70000,
        ARM_STRENGTH=70000,
        ARM_ACCURACY=70000
    )
    return Fielder(
        name=name,
        position=position,
        attributes=attrs
    )


def setup_test_defense():
    """Create a standard defensive setup."""
    fielders = {
        'pitcher': create_test_fielder('Pitcher', 'pitcher'),
        'catcher': create_test_fielder('Catcher', 'catcher'),
        'first_base': create_test_fielder('First', 'first_base'),
        'second_base': create_test_fielder('Second', 'second_base'),
        'third_base': create_test_fielder('Third', 'third_base'),
        'shortstop': create_test_fielder('Short', 'shortstop'),
        'left_field': create_test_fielder('Left', 'left_field', speed=80000, reaction=75000),
        'center_field': create_test_fielder('Center', 'center_field', speed=85000, reaction=80000),
        'right_field': create_test_fielder('Right', 'right_field', speed=80000, reaction=75000),
    }
    return fielders


def test_routine_fly_ball():
    """
    Test 1: Routine fly ball - fielder should arrive early.
    Expected: route_efficiency 0.90-1.00, high catch probability
    """
    print("=" * 80)
    print("TEST 1: ROUTINE FLY BALL")
    print("=" * 80)

    # Simulate a routine fly ball to center field
    sim = BattedBallSimulator()
    trajectory = sim.simulate(
        exit_velocity=85.0,    # mph - moderate
        launch_angle=35.0,     # high fly ball
        spray_angle=0.0,       # straight to center
        backspin_rpm=2000.0,
        sidespin_rpm=0.0,
        altitude=0.0,
        temperature=70.0
    )

    print(f"Ball trajectory: {trajectory.distance:.1f} ft, {trajectory.flight_time:.2f}s hang time")
    print(f"Landing position: ({trajectory.landing_x:.1f}, {trajectory.landing_y:.1f})")

    # Set up play simulation
    play_sim = PlaySimulator()
    fielders = setup_test_defense()
    play_sim.setup_defense(fielders)

    # Create play result
    result = PlayResult()

    # Simulate catch attempt via fly_ball_handler
    from batted_ball.field_layout import FieldPosition
    ball_position = FieldPosition(trajectory.landing_x, trajectory.landing_y, 0.0)
    catch_result = play_sim.fly_ball_handler.simulate_catch_attempt(
        ball_position,
        trajectory.flight_time,
        result
    )

    # Print all events
    print("\nPlay Events:")
    for event in result.events:
        if event.event_type == "route_efficiency":
            print(f"\n{event.description}")
        elif event.event_type == "route_efficiency_warning":
            print(f"  ⚠ {event.description}")
        else:
            print(f"  [{event.time:.2f}s] {event.event_type}: {event.description}")

    print(f"\nCatch result: {'SUCCESS' if catch_result.success else 'FAILED'}")
    print()


def test_tough_running_catch():
    """
    Test 2: Tough running catch - fielder must sprint at near-max speed.
    Expected: route_efficiency 0.80-0.90, moderate catch probability
    """
    print("=" * 80)
    print("TEST 2: TOUGH RUNNING CATCH")
    print("=" * 80)

    # Simulate a line drive to the gap
    sim = BattedBallSimulator()
    trajectory = sim.simulate(
        exit_velocity=100.0,   # mph - hard hit
        launch_angle=18.0,     # line drive
        spray_angle=20.0,      # right-center gap
        backspin_rpm=1500.0,
        sidespin_rpm=500.0,
        altitude=0.0,
        temperature=70.0
    )

    print(f"Ball trajectory: {trajectory.distance:.1f} ft, {trajectory.flight_time:.2f}s hang time")
    print(f"Landing position: ({trajectory.landing_x:.1f}, {trajectory.landing_y:.1f})")

    # Set up play simulation
    play_sim = PlaySimulator()
    fielders = setup_test_defense()
    play_sim.setup_defense(fielders)

    # Create play result
    result = PlayResult()

    # Simulate catch attempt
    from batted_ball.field_layout import FieldPosition
    ball_position = FieldPosition(trajectory.landing_x, trajectory.landing_y, 0.0)
    catch_result = play_sim.fly_ball_handler.simulate_catch_attempt(
        ball_position,
        trajectory.flight_time,
        result
    )

    # Print all events
    print("\nPlay Events:")
    for event in result.events:
        if event.event_type == "route_efficiency":
            print(f"\n{event.description}")
        elif event.event_type == "route_efficiency_warning":
            print(f"  ⚠ {event.description}")
        else:
            print(f"  [{event.time:.2f}s] {event.event_type}: {event.description}")

    print(f"\nCatch result: {'SUCCESS' if catch_result.success else 'FAILED'}")
    print()


def test_impossible_catch():
    """
    Test 3: Impossible ball - required speed exceeds fielder max.
    Expected: outcome = HIT, catch_probability < 0.10
    """
    print("=" * 80)
    print("TEST 3: IMPOSSIBLE CATCH (OVER THE HEAD)")
    print("=" * 80)

    # Simulate a ball well over the fielder's head
    sim = BattedBallSimulator()
    trajectory = sim.simulate(
        exit_velocity=108.0,   # mph - crushed
        launch_angle=28.0,     # optimal launch angle
        spray_angle=-15.0,     # left-center
        backspin_rpm=2200.0,
        sidespin_rpm=0.0,
        altitude=0.0,
        temperature=70.0
    )

    print(f"Ball trajectory: {trajectory.distance:.1f} ft, {trajectory.flight_time:.2f}s hang time")
    print(f"Landing position: ({trajectory.landing_x:.1f}, {trajectory.landing_y:.1f})")

    # Set up play simulation with average fielders
    play_sim = PlaySimulator()
    fielders = setup_test_defense()
    play_sim.setup_defense(fielders)

    # Create play result
    result = PlayResult()

    # Simulate catch attempt
    from batted_ball.field_layout import FieldPosition
    ball_position = FieldPosition(trajectory.landing_x, trajectory.landing_y, 0.0)
    catch_result = play_sim.fly_ball_handler.simulate_catch_attempt(
        ball_position,
        trajectory.flight_time,
        result
    )

    # Print all events
    print("\nPlay Events:")
    for event in result.events:
        if event.event_type == "route_efficiency":
            print(f"\n{event.description}")
        elif event.event_type == "route_efficiency_warning":
            print(f"  ⚠ {event.description}")
        else:
            print(f"  [{event.time:.2f}s] {event.event_type}: {event.description}")

    print(f"\nCatch result: {'SUCCESS' if catch_result.success else 'FAILED'}")
    print()


def test_edge_case_margin():
    """
    Test 4: Edge case with slightly negative margin (diving catch range).
    Expected: catch_prob ~0.15, could go either way
    """
    print("=" * 80)
    print("TEST 4: EDGE CASE - DIVING CATCH RANGE")
    print("=" * 80)

    # Simulate a ball just out of easy reach
    sim = BattedBallSimulator()
    trajectory = sim.simulate(
        exit_velocity=95.0,    # mph
        launch_angle=25.0,     # medium fly ball
        spray_angle=25.0,      # toward right field line
        backspin_rpm=1800.0,
        sidespin_rpm=800.0,
        altitude=0.0,
        temperature=70.0
    )

    print(f"Ball trajectory: {trajectory.distance:.1f} ft, {trajectory.flight_time:.2f}s hang time")
    print(f"Landing position: ({trajectory.landing_x:.1f}, {trajectory.landing_y:.1f})")

    # Set up play simulation
    play_sim = PlaySimulator()
    fielders = setup_test_defense()
    play_sim.setup_defense(fielders)

    # Create play result
    result = PlayResult()

    # Simulate catch attempt
    from batted_ball.field_layout import FieldPosition
    ball_position = FieldPosition(trajectory.landing_x, trajectory.landing_y, 0.0)
    catch_result = play_sim.fly_ball_handler.simulate_catch_attempt(
        ball_position,
        trajectory.flight_time,
        result
    )

    # Print all events
    print("\nPlay Events:")
    for event in result.events:
        if event.event_type == "route_efficiency":
            print(f"\n{event.description}")
        elif event.event_type == "route_efficiency_warning":
            print(f"  ⚠ {event.description}")
        else:
            print(f"  [{event.time:.2f}s] {event.event_type}: {event.description}")

    print(f"\nCatch result: {'SUCCESS' if catch_result.success else 'FAILED'}")
    print()


def main():
    """Run all test scenarios."""
    print("\n")
    print("╔" + "=" * 78 + "╗")
    print("║" + " " * 20 + "ROUTE EFFICIENCY LOGGING TEST SUITE" + " " * 23 + "║")
    print("╚" + "=" * 78 + "╝")
    print("\n")

    # Run test scenarios
    test_routine_fly_ball()
    test_tough_running_catch()
    test_impossible_catch()
    test_edge_case_margin()

    print("=" * 80)
    print("ALL TESTS COMPLETED")
    print("=" * 80)
    print("\nValidation Notes:")
    print("  ✓ Check that FieldingPlayModel block appears for each test")
    print("  ✓ Verify route efficiency values are in [0.0, 1.0] range")
    print("  ✓ Confirm required speed vs max speed makes sense")
    print("  ✓ Validate catch probability correlates with outcome")
    print("  ✓ Review any warnings flagged by the analyzer")
    print()


if __name__ == "__main__":
    main()
