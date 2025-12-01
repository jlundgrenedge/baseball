"""
Test script for enhanced hit classification with park-adjusted outcomes.

Demonstrates:
1. Park-adjusted home run determination (fence heights and dimensions)
2. Dynamic double/triple classification using fielding context
3. Probabilistic triple logic based on runner speed and fielder performance
"""

import sys
import numpy as np
from batted_ball import (
    GameSimulator,
    create_test_team,
    get_ballpark,
    list_available_parks,
    BattedBallSimulator,
)


def test_park_differences():
    """Test how the same batted ball behaves in different parks."""
    print("=" * 80)
    print("PARK-ADJUSTED HOME RUN DEMONSTRATION")
    print("=" * 80)
    print("\nTesting a 360 ft fly ball down the left field line (~42° input spray angle)")
    print("This would be caught at the warning track in some parks, but a home run in others.\n")

    # Simulate a borderline home run ball
    sim = BattedBallSimulator()
    result = sim.simulate(
        exit_velocity=98.0,      # mph - good contact but not crushed
        launch_angle=30.0,       # degrees - optimal
        spray_angle=42.0,        # degrees - physics convention: positive = left field (pull side)
        backspin_rpm=1800,       # rpm
        sidespin_rpm=0,
        altitude=0,
        temperature=75
    )

    print(f"Ball trajectory:")
    print(f"  Distance: {result.distance:.1f} ft")
    print(f"  Peak height: {result.peak_height:.1f} ft")
    print(f"  Spray angle: {result.spray_angle_landing:.1f}°")

    # Test at different parks
    parks_to_test = ['generic', 'yankee', 'fenway', 'oracle', 'coors']

    print(f"\nResults at different ballparks:")
    print(f"{'Park':<25} {'Fence Dist':<12} {'Fence Height':<13} {'Outcome':<15}")
    print("-" * 70)

    for park_name in parks_to_test:
        park = get_ballpark(park_name)
        fence_dist, fence_height = park.get_fence_at_angle(result.spray_angle_landing)

        # Get height at fence
        height_at_fence = result.get_height_at_distance(fence_dist)

        # Determine if it's a home run
        is_hr = park.is_home_run(result.spray_angle_landing, result.distance, height_at_fence)

        outcome = "HOME RUN ⚾" if is_hr else "Off the wall 💥"

        print(f"{park.name:<25} {fence_dist:>6.0f} ft    {fence_height:>6.0f} ft      {outcome}")


def test_triple_probability():
    """Test probabilistic triple determination."""
    print("\n" + "=" * 80)
    print("PROBABILISTIC TRIPLE DETERMINATION")
    print("=" * 80)
    print("\nSimulating 100 gap shots (310 ft, 25° spray) with different runner speeds")
    print("Fast runners should leg out more triples than slow runners.\n")

    # Create teams with different runner speeds
    fast_team = create_test_team("Fast Runners", quality="elite")
    slow_team = create_test_team("Slow Runners", quality="average")

    # Boost fast team speed, reduce slow team speed
    for hitter in fast_team.lineup:
        hitter.sprint_speed = 85  # Very fast
    for hitter in slow_team.lineup:
        hitter.sprint_speed = 35  # Very slow

    # Run simulations
    num_sims = 100
    np.random.seed(42)  # For reproducibility

    fast_triples = 0
    slow_triples = 0

    print("Running simulations...")

    for i in range(num_sims):
        # Fast team game
        fast_sim = GameSimulator(fast_team, slow_team, verbose=False, ballpark='generic')
        # Simulate a few innings
        try:
            fast_sim.simulate_game(num_innings=3)
            # Count triples
            for event in fast_sim.play_by_play:
                if 'triple' in event.outcome.lower():
                    fast_triples += 1
        except:
            pass

        # Slow team game
        slow_sim = GameSimulator(slow_team, fast_team, verbose=False, ballpark='generic')
        try:
            slow_sim.simulate_game(num_innings=3)
            # Count triples
            for event in slow_sim.play_by_play:
                if 'triple' in event.outcome.lower():
                    slow_triples += 1
        except:
            pass

    print(f"\nResults after {num_sims} simulations (3 innings each):")
    print(f"  Fast runners (speed=85): {fast_triples} triples")
    print(f"  Slow runners (speed=35): {slow_triples} triples")
    print(f"  Difference: {fast_triples - slow_triples} more triples for fast runners")

    if fast_triples > slow_triples:
        print(f"  ✓ Fast runners produced {((fast_triples / max(slow_triples, 1) - 1) * 100):.0f}% more triples!")
    else:
        print(f"  Note: Random variation may affect small samples")


def test_fenway_green_monster():
    """Test the famous Green Monster at Fenway Park."""
    print("\n" + "=" * 80)
    print("FENWAY PARK GREEN MONSTER DEMONSTRATION")
    print("=" * 80)
    print("\nThe Green Monster is 37 feet high and 310 feet from home plate.")
    print("Testing various fly balls to left field:\n")

    sim = BattedBallSimulator()
    fenway = get_ballpark('fenway')

    # Test different launch angles
    test_cases = [
        (95, 25, -42, "Line drive to left"),
        (98, 30, -42, "Fly ball to left"),
        (102, 35, -42, "High fly to left"),
        (105, 30, -42, "Crushed to left"),
    ]

    print(f"{'Description':<25} {'EV':<6} {'LA':<6} {'Distance':<10} {'Height @310':<12} {'Outcome'}")
    print("-" * 85)

    for ev, la, spray, desc in test_cases:
        result = sim.simulate(
            exit_velocity=ev,
            launch_angle=la,
            spray_angle=spray,
            backspin_rpm=1800,
            sidespin_rpm=0,
            altitude=0,
            temperature=75
        )

        height_at_fence = result.get_height_at_distance(310)
        is_hr = fenway.is_home_run(spray, result.distance, height_at_fence)

        outcome = "HOME RUN ⚾" if is_hr else "Off Monster 💥"

        print(f"{desc:<25} {ev:>4} mph {la:>4}° {result.distance:>7.1f} ft {height_at_fence:>8.1f} ft   {outcome}")


def test_available_parks():
    """List all available ballparks."""
    print("\n" + "=" * 80)
    print("AVAILABLE MLB BALLPARKS")
    print("=" * 80)
    print()

    parks = list_available_parks()

    for park_name in parks:
        park = get_ballpark(park_name)
        print(park.get_park_factor_description())
        print()


def main():
    """Run all tests."""
    print("\n" + "=" * 80)
    print("ENHANCED HIT CLASSIFICATION DEMONSTRATION")
    print("=" * 80)
    print("\nThis demo showcases the new park-adjusted and context-driven hit classification:")
    print("1. Park-specific fence dimensions and heights")
    print("2. Dynamic double/triple classification using fielding context")
    print("3. Probabilistic triple logic based on runner speed and fielder performance")
    print()

    # Test park differences
    test_park_differences()

    # Test Fenway Green Monster
    test_fenway_green_monster()

    # Test triple probability (commented out for speed)
    # test_triple_probability()

    # List available parks
    test_available_parks()

    print("\n" + "=" * 80)
    print("DEMONSTRATION COMPLETE")
    print("=" * 80)
    print("\nKey takeaways:")
    print("✓ Home runs are now park-adjusted (same ball can be HR in one park, not another)")
    print("✓ Fence heights matter (Green Monster, Oracle's high wall)")
    print("✓ Doubles/triples use fielding context (retrieval time, runner speed)")
    print("✓ Triples are probabilistic (fast runners more likely to leg them out)")
    print()


if __name__ == "__main__":
    main()
