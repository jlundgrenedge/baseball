"""
Demonstration of batter vs pitcher simulation system.

Shows how pitcher and hitter attributes integrate with physics to create
realistic at-bat outcomes.
"""

import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from batted_ball import Pitcher, Hitter, AtBatSimulator


def print_section(title):
    """Print a formatted section header."""
    print("\n" + "="*70)
    print(title)
    print("="*70 + "\n")


def demonstrate_player_creation():
    """Demonstrate creating players with different archetypes."""
    print_section("PLAYER ARCHETYPES")

    # Power pitcher
    power_pitcher = Pitcher(
        name="Max Velocity",
        velocity=85,          # Elite fastball (98 mph)
        spin_rate=60,         # Above average spin
        command=40,           # Below average command
        deception=50,         # Average deception
        pitch_arsenal={
            'fastball': {'velocity': 85, 'movement': 60, 'command': 40},
            'slider': {'velocity': 70, 'movement': 70, 'command': 35},
        }
    )

    # Finesse pitcher
    finesse_pitcher = Pitcher(
        name="Greg Command",
        velocity=45,          # Average fastball (91 mph)
        spin_rate=55,         # Slightly above average
        command=85,           # Elite command
        deception=70,         # Good deception
        pitch_arsenal={
            'fastball': {'velocity': 45, 'movement': 55, 'command': 85},
            'curveball': {'velocity': 40, 'movement': 75, 'command': 80},
            'changeup': {'velocity': 40, 'movement': 65, 'command': 85},
        }
    )

    # Power hitter
    power_hitter = Hitter(
        name="Joey Bombs",
        bat_speed=80,                  # Elite bat speed (75 mph)
        barrel_accuracy=50,            # Average contact
        swing_timing_precision=60,     # Good timing
        zone_discipline=40,            # Aggressive (swings a lot)
        swing_decision_aggressiveness=70,  # Very aggressive
        launch_angle_tendency=25.0,    # Fly ball hitter
        spray_tendency=-10.0,          # Slight pull tendency
    )

    # Contact hitter
    contact_hitter = Hitter(
        name="Tony Contact",
        bat_speed=50,                  # Average bat speed
        barrel_accuracy=85,            # Elite contact ability
        swing_timing_precision=80,     # Elite timing
        zone_discipline=75,            # Very selective
        swing_decision_aggressiveness=30,  # Patient
        launch_angle_tendency=10.0,    # Line drive/ground ball hitter
        spray_tendency=5.0,            # Uses all fields
    )

    print("POWER PITCHER:")
    print(f"  {power_pitcher}")
    print(f"  Fastball: ~{power_pitcher.get_pitch_velocity_mph('fastball'):.0f} mph")
    print(f"  Command error: ~{power_pitcher.get_command_error_inches('fastball')[0]:.1f}\" typical")
    print()

    print("FINESSE PITCHER:")
    print(f"  {finesse_pitcher}")
    print(f"  Fastball: ~{finesse_pitcher.get_pitch_velocity_mph('fastball'):.0f} mph")
    print(f"  Command error: ~{finesse_pitcher.get_command_error_inches('fastball')[0]:.1f}\" typical")
    print()

    print("POWER HITTER:")
    print(f"  {power_hitter}")
    print(f"  Bat speed: ~{power_hitter.get_bat_speed_mph():.0f} mph")
    print(f"  Launch angle tendency: {power_hitter.launch_angle_tendency:.0f}°")
    print()

    print("CONTACT HITTER:")
    print(f"  {contact_hitter}")
    print(f"  Bat speed: ~{contact_hitter.get_bat_speed_mph():.0f} mph")
    print(f"  Launch angle tendency: {contact_hitter.launch_angle_tendency:.0f}°")

    return power_pitcher, finesse_pitcher, power_hitter, contact_hitter


def simulate_at_bat_example(pitcher, hitter, verbose=True):
    """Simulate a single at-bat."""
    sim = AtBatSimulator(pitcher, hitter)
    result = sim.simulate_at_bat(verbose=verbose)
    return result


def demonstrate_matchups():
    """Demonstrate different pitcher-hitter matchups."""
    print_section("MATCHUP SIMULATIONS")

    # Create players
    power_pitcher, finesse_pitcher, power_hitter, contact_hitter = demonstrate_player_creation()

    # Matchup 1: Power vs Power
    print_section("MATCHUP 1: Power Pitcher vs Power Hitter")
    print(f"{power_pitcher.name} (Velocity: {power_pitcher.velocity}) "
          f"vs {power_hitter.name} (Bat Speed: {power_hitter.bat_speed})")
    result1 = simulate_at_bat_example(power_pitcher, power_hitter, verbose=True)

    # Matchup 2: Finesse vs Contact
    print_section("MATCHUP 2: Finesse Pitcher vs Contact Hitter")
    print(f"{finesse_pitcher.name} (Command: {finesse_pitcher.command}) "
          f"vs {contact_hitter.name} (Barrel Accuracy: {contact_hitter.barrel_accuracy})")
    result2 = simulate_at_bat_example(finesse_pitcher, contact_hitter, verbose=True)

    # Matchup 3: Power vs Contact
    print_section("MATCHUP 3: Power Pitcher vs Contact Hitter")
    print(f"{power_pitcher.name} (Velocity: {power_pitcher.velocity}) "
          f"vs {contact_hitter.name} (Contact: {contact_hitter.barrel_accuracy})")
    result3 = simulate_at_bat_example(power_pitcher, contact_hitter, verbose=True)

    # Matchup 4: Finesse vs Power
    print_section("MATCHUP 4: Finesse Pitcher vs Power Hitter")
    print(f"{finesse_pitcher.name} (Command: {finesse_pitcher.command}) "
          f"vs {power_hitter.name} (Power: {power_hitter.bat_speed})")
    result4 = simulate_at_bat_example(finesse_pitcher, power_hitter, verbose=True)


def run_multiple_at_bats(pitcher, hitter, num_at_bats=10):
    """Simulate multiple at-bats and show statistics."""
    print_section(f"STATISTICAL ANALYSIS: {num_at_bats} AT-BATS")
    print(f"{pitcher.name} vs {hitter.name}\n")

    sim = AtBatSimulator(pitcher, hitter)

    outcomes = {
        'strikeout': 0,
        'walk': 0,
        'in_play': 0,
    }

    batted_balls = []
    total_pitches = 0

    for i in range(num_at_bats):
        # Reset pitcher stamina for each at-bat
        pitcher.current_stamina = pitcher.stamina
        pitcher.pitches_thrown = 0

        result = sim.simulate_at_bat(verbose=False)

        outcomes[result.outcome] += 1
        total_pitches += len(result.pitches)

        if result.batted_ball_result:
            batted_balls.append(result.batted_ball_result)

    # Print statistics
    print(f"Results over {num_at_bats} at-bats:")
    print(f"  Strikeouts: {outcomes['strikeout']} ({outcomes['strikeout']/num_at_bats*100:.1f}%)")
    print(f"  Walks: {outcomes['walk']} ({outcomes['walk']/num_at_bats*100:.1f}%)")
    print(f"  Balls in play: {outcomes['in_play']} ({outcomes['in_play']/num_at_bats*100:.1f}%)")
    print(f"  Average pitches/PA: {total_pitches/num_at_bats:.1f}")

    if batted_balls:
        print(f"\nBatted ball statistics ({len(batted_balls)} balls in play):")
        avg_exit_velo = sum(bb['exit_velocity'] for bb in batted_balls) / len(batted_balls)
        avg_launch_angle = sum(bb['launch_angle'] for bb in batted_balls) / len(batted_balls)
        avg_distance = sum(bb['distance'] for bb in batted_balls) / len(batted_balls)

        print(f"  Average exit velocity: {avg_exit_velo:.1f} mph")
        print(f"  Average launch angle: {avg_launch_angle:.1f}°")
        print(f"  Average distance: {avg_distance:.1f} ft")

        # Count home runs (rough estimate: >400 ft)
        home_runs = sum(1 for bb in batted_balls if bb['distance'] > 400)
        print(f"  Estimated home runs: {home_runs} ({home_runs/len(batted_balls)*100:.1f}%)")


def demonstrate_attribute_effects():
    """Show how different attributes affect outcomes."""
    print_section("ATTRIBUTE EFFECTS DEMONSTRATION")

    # Base pitcher
    base_pitcher = Pitcher(
        name="Average Joe",
        velocity=50,
        command=50,
        pitch_arsenal={'fastball': {'velocity': 50, 'movement': 50, 'command': 50}}
    )

    # Base hitter
    base_hitter = Hitter(
        name="Average Al",
        bat_speed=50,
        barrel_accuracy=50,
        zone_discipline=50,
    )

    # Elite velocity pitcher
    elite_velo_pitcher = Pitcher(
        name="Flame Thrower",
        velocity=90,
        command=50,
        pitch_arsenal={'fastball': {'velocity': 90, 'movement': 50, 'command': 50}}
    )

    # Elite command pitcher
    elite_command_pitcher = Pitcher(
        name="Pinpoint Pete",
        velocity=50,
        command=90,
        pitch_arsenal={'fastball': {'velocity': 50, 'movement': 50, 'command': 90}}
    )

    print("Testing effect of VELOCITY:")
    print(f"  Base pitcher velocity: {base_pitcher.get_pitch_velocity_mph('fastball'):.0f} mph")
    print(f"  Elite pitcher velocity: {elite_velo_pitcher.get_pitch_velocity_mph('fastball'):.0f} mph")
    print()

    run_multiple_at_bats(base_pitcher, base_hitter, 20)
    print()
    run_multiple_at_bats(elite_velo_pitcher, base_hitter, 20)

    print("\n" + "="*70 + "\n")
    print("Testing effect of COMMAND:")
    print(f"  Base pitcher command error: ~{base_pitcher.get_command_error_inches('fastball')[0]:.1f}\"")
    print(f"  Elite pitcher command error: ~{elite_command_pitcher.get_command_error_inches('fastball')[0]:.1f}\"")
    print()

    run_multiple_at_bats(base_pitcher, base_hitter, 20)
    print()
    run_multiple_at_bats(elite_command_pitcher, base_hitter, 20)


def main():
    """Run full demonstration."""
    print_section("BATTER VS PITCHER SIMULATION SYSTEM")
    print("Integrating player attributes with physics-based simulation")
    print()
    print("Features:")
    print("  ✓ Pitcher attributes → pitch characteristics")
    print("  ✓ Hitter attributes → swing decisions and contact quality")
    print("  ✓ Physics simulation → realistic trajectories and outcomes")

    # Demonstrate different matchups
    demonstrate_matchups()

    # Show statistical analysis
    print("\n" + "="*70)
    print("Running statistical analysis...")
    print("="*70)

    power_pitcher = Pitcher(
        name="Max Velocity",
        velocity=85,
        command=40,
        pitch_arsenal={
            'fastball': {'velocity': 85, 'movement': 60, 'command': 40},
            'slider': {'velocity': 70, 'movement': 70, 'command': 35},
        }
    )

    power_hitter = Hitter(
        name="Joey Bombs",
        bat_speed=80,
        barrel_accuracy=50,
        zone_discipline=40,
        swing_decision_aggressiveness=70,
    )

    run_multiple_at_bats(power_pitcher, power_hitter, 50)

    # Demonstrate attribute effects
    demonstrate_attribute_effects()

    print_section("CONCLUSION")
    print("The batter vs pitcher system successfully integrates:")
    print()
    print("1. PITCHER ATTRIBUTES:")
    print("   - Velocity, spin rate, command, deception")
    print("   - Release mechanics (extension, arm slot)")
    print("   - Pitch arsenal with individual ratings")
    print("   - Stamina and fatigue effects")
    print()
    print("2. HITTER ATTRIBUTES:")
    print("   - Bat speed, barrel accuracy, timing")
    print("   - Zone discipline and swing decisions")
    print("   - Launch angle and spray tendencies")
    print("   - Pitch recognition ability")
    print()
    print("3. PHYSICS INTEGRATION:")
    print("   - Attributes → physical parameters")
    print("   - Pitch trajectory simulation")
    print("   - Bat-ball collision physics")
    print("   - Batted ball flight simulation")
    print()
    print("Result: Realistic at-bat outcomes driven by player attributes!")


if __name__ == "__main__":
    main()
