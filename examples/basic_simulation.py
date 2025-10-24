"""
Basic batted ball simulation examples.

Demonstrates simple usage of the BattedBallSimulator.
"""

import sys
sys.path.insert(0, '..')

from batted_ball import BattedBallSimulator


def main():
    """Run basic simulation examples."""

    print("=" * 70)
    print("BASIC BATTED BALL SIMULATION EXAMPLES")
    print("=" * 70)
    print()

    # Create simulator
    sim = BattedBallSimulator()

    # Example 1: Perfect home run swing
    print("Example 1: Perfect Home Run Swing")
    print("-" * 70)
    result1 = sim.simulate(
        exit_velocity=105.0,    # mph - elite exit velocity
        launch_angle=28.0,      # degrees - optimal for distance
        spray_angle=0.0,        # degrees - center field
        backspin_rpm=1800.0,    # rpm - optimal backspin
        altitude=0.0,           # feet - sea level
        temperature=75.0,       # Fahrenheit
    )
    print(result1)
    print()

    # Example 2: Line drive single
    print("Example 2: Line Drive Single")
    print("-" * 70)
    result2 = sim.simulate(
        exit_velocity=95.0,     # mph
        launch_angle=12.0,      # degrees - line drive angle
        spray_angle=15.0,       # degrees - slight pull
        backspin_rpm=1200.0,    # rpm - less backspin on line drive
        altitude=0.0,
        temperature=75.0,
    )
    print(result2)
    print()

    # Example 3: Pop-up
    print("Example 3: Pop-up (Too Much Launch Angle)")
    print("-" * 70)
    result3 = sim.simulate(
        exit_velocity=85.0,     # mph - lower exit velo
        launch_angle=55.0,      # degrees - too steep
        spray_angle=0.0,
        backspin_rpm=2200.0,    # rpm - lots of backspin
        altitude=0.0,
        temperature=75.0,
    )
    print(result3)
    print()

    # Example 4: Coors Field home run
    print("Example 4: Coors Field Home Run (High Altitude)")
    print("-" * 70)
    result4 = sim.simulate(
        exit_velocity=100.0,
        launch_angle=28.0,
        spray_angle=0.0,
        backspin_rpm=1800.0,
        altitude=5200.0,        # feet - Coors Field elevation
        temperature=75.0,
    )
    print(result4)
    print()

    # Example 5: Effect of wind
    print("Example 5: 10 mph Tailwind Effect")
    print("-" * 70)
    result5 = sim.simulate(
        exit_velocity=100.0,
        launch_angle=28.0,
        spray_angle=0.0,
        backspin_rpm=1800.0,
        altitude=0.0,
        temperature=75.0,
        wind_speed=10.0,        # mph - tailwind
        wind_direction=0.0,     # degrees - straight out to center
    )
    print(result5)
    print()

    # Example 6: Cold weather vs hot weather
    print("Example 6: Temperature Comparison (50°F vs 90°F)")
    print("-" * 70)
    result_cold = sim.simulate(
        exit_velocity=100.0,
        launch_angle=28.0,
        backspin_rpm=1800.0,
        temperature=50.0,       # Cold day
    )
    result_hot = sim.simulate(
        exit_velocity=100.0,
        launch_angle=28.0,
        backspin_rpm=1800.0,
        temperature=90.0,       # Hot day
    )
    print(f"50°F: {result_cold.distance:.1f} feet")
    print(f"90°F: {result_hot.distance:.1f} feet")
    print(f"Difference: {result_hot.distance - result_cold.distance:.1f} feet")
    print()

    # Example 7: Contact quality comparison
    print("Example 7: Contact Quality Comparison")
    print("-" * 70)

    # Sweet spot
    result_sweet = sim.simulate_contact(
        exit_velocity=100.0,
        launch_angle=28.0,
        backspin_rpm=1800.0,
        contact_quality='sweet_spot',
    )

    # Below center (under it)
    result_below = sim.simulate_contact(
        exit_velocity=100.0,
        launch_angle=28.0,
        backspin_rpm=1800.0,
        contact_quality='below_center',
    )

    # Above center (topped)
    result_above = sim.simulate_contact(
        exit_velocity=100.0,
        launch_angle=28.0,
        backspin_rpm=1800.0,
        contact_quality='above_center',
    )

    print(f"Sweet spot: {result_sweet.distance:.1f} feet, angle: {result_sweet.initial_conditions['launch_angle']:.1f}°")
    print(f"Below center: {result_below.distance:.1f} feet, angle: {result_below.initial_conditions['launch_angle']:.1f}°")
    print(f"Above center: {result_above.distance:.1f} feet, angle: {result_above.initial_conditions['launch_angle']:.1f}°")
    print()

    print("=" * 70)
    print("All examples completed!")
    print("=" * 70)


if __name__ == '__main__':
    main()
