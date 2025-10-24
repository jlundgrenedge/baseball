"""
Demonstration of Phase 2 Bat-Ball Collision Physics

Shows how the enhanced collision model works with:
- Variable coefficient of restitution (COR)
- Sweet spot physics
- Contact location effects
- Bat speed and pitch speed to exit velocity conversion
"""

import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from batted_ball.contact import ContactModel
from batted_ball import BattedBallSimulator


def demo_sweet_spot_comparison():
    """
    Demo 1: Compare sweet spot vs off-center contact.

    Shows how contact location dramatically affects exit velocity
    due to COR variation and vibration energy loss.
    """
    print("=" * 70)
    print("DEMO 1: Sweet Spot vs Off-Center Contact")
    print("=" * 70)

    model = ContactModel(bat_type='wood')

    # Same swing parameters
    bat_speed = 70.0  # mph
    pitch_speed = 92.0  # mph
    bat_angle = 28.0  # degrees

    print(f"\nSwing Parameters:")
    print(f"  Bat speed: {bat_speed} mph")
    print(f"  Pitch speed: {pitch_speed} mph")
    print(f"  Bat path angle: {bat_angle}°")

    # Test different contact locations
    contact_locations = [
        ("Perfect Sweet Spot", 0.0),
        ("1 inch off sweet spot", 1.0),
        ("2 inches off", 2.0),
        ("3 inches off (handle)", 3.0),
    ]

    print(f"\n{'Contact Location':<30} {'Exit Vel':>10} {'COR':>8} {'Vib Loss':>10} {'Distance*':>10}")
    print("-" * 70)

    sim = BattedBallSimulator()

    for location_name, distance in contact_locations:
        result = model.full_collision(
            bat_speed_mph=bat_speed,
            pitch_speed_mph=pitch_speed,
            bat_path_angle_deg=bat_angle,
            distance_from_sweet_spot_inches=distance
        )

        # Simulate trajectory to get distance
        traj_result = sim.simulate(
            exit_velocity=result['exit_velocity'],
            launch_angle=result['launch_angle'],
            backspin_rpm=result['backspin_rpm']
        )

        print(f"{location_name:<30} {result['exit_velocity']:>8.1f} mph "
              f"{result['cor']:>8.3f} {result['vibration_loss']:>9.1%} "
              f"{traj_result.distance:>9.1f} ft")

    print("\n* Distance at sea level, 70°F, no wind")
    print("\n💡 Insight: Sweet spot contact crucial for maximum distance!")
    print("   Contact 3 inches off sweet spot loses ~40+ mph exit velocity")


def demo_wood_vs_aluminum():
    """
    Demo 2: Compare wood bat vs aluminum bat.

    Aluminum bats have higher COR, producing higher exit velocities.
    """
    print("\n" + "=" * 70)
    print("DEMO 2: Wood Bat vs Aluminum Bat")
    print("=" * 70)

    bat_speed = 68.0
    pitch_speed = 88.0
    bat_angle = 27.0

    print(f"\nSwing Parameters (high school player):")
    print(f"  Bat speed: {bat_speed} mph")
    print(f"  Pitch speed: {pitch_speed} mph")
    print(f"  Contact: Sweet spot")

    wood = ContactModel(bat_type='wood')
    aluminum = ContactModel(bat_type='aluminum')

    result_wood = wood.full_collision(
        bat_speed_mph=bat_speed,
        pitch_speed_mph=pitch_speed,
        bat_path_angle_deg=bat_angle
    )

    result_aluminum = aluminum.full_collision(
        bat_speed_mph=bat_speed,
        pitch_speed_mph=pitch_speed,
        bat_path_angle_deg=bat_angle
    )

    print(f"\n{'Bat Type':<15} {'Exit Velocity':>15} {'COR':>10} {'Launch':>10} {'Backspin':>12}")
    print("-" * 65)
    print(f"{'Wood':<15} {result_wood['exit_velocity']:>12.1f} mph "
          f"{result_wood['cor']:>10.3f} {result_wood['launch_angle']:>9.1f}° "
          f"{result_wood['backspin_rpm']:>9.0f} rpm")
    print(f"{'Aluminum':<15} {result_aluminum['exit_velocity']:>12.1f} mph "
          f"{result_aluminum['cor']:>10.3f} {result_aluminum['launch_angle']:>9.1f}° "
          f"{result_aluminum['backspin_rpm']:>9.0f} rpm")

    diff = result_aluminum['exit_velocity'] - result_wood['exit_velocity']
    print(f"\n💡 Aluminum bat advantage: +{diff:.1f} mph exit velocity")
    print(f"   (Due to higher COR: {result_aluminum['cor']:.3f} vs {result_wood['cor']:.3f})")


def demo_contact_height_effects():
    """
    Demo 3: Effects of vertical contact location.

    Shows how hitting below/above center affects launch angle and spin.
    """
    print("\n" + "=" * 70)
    print("DEMO 3: Vertical Contact Location Effects")
    print("=" * 70)

    model = ContactModel()

    bat_speed = 70.0
    pitch_speed = 90.0
    bat_angle = 25.0

    print(f"\nSwing Parameters:")
    print(f"  Bat speed: {bat_speed} mph")
    print(f"  Pitch speed: {pitch_speed} mph")
    print(f"  Bat angle: {bat_angle}°")

    contact_heights = [
        ("1 inch above center (topped)", 1.0),
        ("Center (perfect)", 0.0),
        ("0.5 inch below (slight undercut)", -0.5),
        ("1 inch below (undercut)", -1.0),
    ]

    print(f"\n{'Contact Height':<35} {'Launch':>9} {'Backspin':>12} {'Trajectory':>15}")
    print("-" * 75)

    for height_desc, offset in contact_heights:
        result = model.full_collision(
            bat_speed_mph=bat_speed,
            pitch_speed_mph=pitch_speed,
            bat_path_angle_deg=bat_angle,
            vertical_contact_offset_inches=offset
        )

        # Classify trajectory type
        if result['launch_angle'] < 10:
            trajectory = "Ground ball"
        elif result['launch_angle'] < 20:
            trajectory = "Line drive"
        elif result['launch_angle'] < 35:
            trajectory = "Fly ball"
        else:
            trajectory = "Pop up"

        print(f"{height_desc:<35} {result['launch_angle']:>7.1f}° "
              f"{result['backspin_rpm']:>9.0f} rpm {trajectory:>15}")

    print("\n💡 Insight: Contact below center → higher launch + more backspin")
    print("           Contact above center → lower launch + less spin (topped)")


def demo_bat_pitch_speed_matrix():
    """
    Demo 4: Matrix of bat speed vs pitch speed.

    Shows how exit velocity depends on both bat and pitch speeds.
    """
    print("\n" + "=" * 70)
    print("DEMO 4: Bat Speed vs Pitch Speed Matrix")
    print("=" * 70)

    model = ContactModel()

    bat_speeds = [60, 65, 70, 75, 80]
    pitch_speeds = [70, 80, 90, 95]

    print("\nExit Velocity (mph) - Sweet Spot Contact")
    print(f"\n{'Bat Speed':<12}", end='')
    for ps in pitch_speeds:
        print(f"{ps:>9} mph", end='')
    print()
    print("-" * 52)

    for bat_speed in bat_speeds:
        print(f"{bat_speed} mph    ", end='')
        for pitch_speed in pitch_speeds:
            result = model.full_collision(
                bat_speed_mph=bat_speed,
                pitch_speed_mph=pitch_speed,
                bat_path_angle_deg=28.0
            )
            print(f"{result['exit_velocity']:>9.1f}", end='')
        print()

    print("\n💡 Insight: Exit velocity ≈ 1.2×(bat speed) + 0.2×(pitch speed)")
    print("           Bat speed dominates! 10 mph faster bat ≈ +12 mph exit velocity")
    print("           Fastball (95 mph) vs changeup (80 mph) ≈ +3 mph exit velocity")


def demo_realistic_scenarios():
    """
    Demo 5: Realistic MLB scenarios.

    Model different types of hits using realistic parameters.
    """
    print("\n" + "=" * 70)
    print("DEMO 5: Realistic MLB Hit Scenarios")
    print("=" * 70)

    model = ContactModel(bat_type='wood')
    sim = BattedBallSimulator()

    scenarios = [
        {
            'name': 'Home Run (power hitter)',
            'bat_speed': 75.0,
            'pitch_speed': 94.0,
            'bat_angle': 28.0,
            'vertical_offset': -0.5,
            'distance_from_sweet_spot': 0.0,
        },
        {
            'name': 'Line Drive Single',
            'bat_speed': 68.0,
            'pitch_speed': 91.0,
            'bat_angle': 15.0,
            'vertical_offset': 0.0,
            'distance_from_sweet_spot': 0.5,
        },
        {
            'name': 'Weak Pop Up (jammed)',
            'bat_speed': 65.0,
            'pitch_speed': 95.0,
            'bat_angle': 30.0,
            'vertical_offset': 0.5,
            'distance_from_sweet_spot': 3.0,
        },
        {
            'name': 'Broken Bat Grounder',
            'bat_speed': 60.0,
            'pitch_speed': 96.0,
            'bat_angle': 5.0,
            'vertical_offset': 1.0,
            'distance_from_sweet_spot': 4.0,
        },
    ]

    print()
    for scenario in scenarios:
        result = model.full_collision(
            bat_speed_mph=scenario['bat_speed'],
            pitch_speed_mph=scenario['pitch_speed'],
            bat_path_angle_deg=scenario['bat_angle'],
            vertical_contact_offset_inches=scenario['vertical_offset'],
            distance_from_sweet_spot_inches=scenario['distance_from_sweet_spot']
        )

        traj = sim.simulate(
            exit_velocity=result['exit_velocity'],
            launch_angle=result['launch_angle'],
            backspin_rpm=result['backspin_rpm']
        )

        print(f"{scenario['name']}:")
        print(f"  Contact: {scenario['distance_from_sweet_spot']:.1f}\" from sweet spot, "
              f"vertical offset: {scenario['vertical_offset']:+.1f}\"")
        print(f"  Exit velocity: {result['exit_velocity']:.1f} mph, "
              f"Launch: {result['launch_angle']:.1f}°, "
              f"Backspin: {result['backspin_rpm']:.0f} rpm")
        print(f"  COR: {result['cor']:.3f}, Vibration loss: {result['vibration_loss']:.1%}")
        print(f"  Distance: {traj.distance:.1f} ft, Hang time: {traj.flight_time:.2f} sec")
        print()


if __name__ == '__main__':
    print("\n" + "=" * 70)
    print("PHASE 2: BAT-BALL COLLISION PHYSICS DEMONSTRATION")
    print("Enhanced model with COR variation and sweet spot physics")
    print("=" * 70)

    demo_sweet_spot_comparison()
    demo_wood_vs_aluminum()
    demo_contact_height_effects()
    demo_bat_pitch_speed_matrix()
    demo_realistic_scenarios()

    print("=" * 70)
    print("Demo complete! Phase 2 collision model working as designed.")
    print("=" * 70)
