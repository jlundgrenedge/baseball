#!/usr/bin/env python3
"""
Test script to validate walk rate fixes.

Tests the fatigue multiplier changes to ensure walk rates are MLB-realistic.
Expected MLB walk rate: 8-9% of plate appearances
"""

import numpy as np
from batted_ball import Pitcher, Hitter, AtBatSimulator
from batted_ball.attributes import PitcherAttributes, HitterAttributes


def test_command_error_progression():
    """Test that command error increases gradually with fatigue."""
    print("=" * 70)
    print("TEST 1: Command Error Progression with Fatigue")
    print("=" * 70)

    # Create average pitcher
    pitcher = Pitcher(
        name="Test Pitcher",
        attributes=PitcherAttributes(
            RAW_VELOCITY_CAP=65000,  # 93 mph
            COMMAND=50000,   # Average command (16" sigma base)
            CONTROL=50000,   # Average control
            STAMINA=50000    # 90 pitches stamina
        ),
        pitch_arsenal={'fastball': {}}
    )

    print(f"\nPitcher: {pitcher.name}")
    print(f"  Base command sigma: {pitcher.attributes.get_command_sigma_inches():.1f}\"")
    print(f"  Stamina capacity: {pitcher.attributes.get_stamina_pitches():.0f} pitches")

    # Test command error at different pitch counts
    test_points = [0, 25, 50, 70, 85, 95]

    print(f"\n{'Pitches':<10} {'Fatigue %':<12} {'Sigma (in)':<15} {'RMS Error (in)':<15} {'RMS Error (ft)':<15}")
    print("-" * 70)

    for pitches in test_points:
        pitcher.pitches_thrown = pitches

        # Sample command errors
        errors = []
        for _ in range(1000):
            h_err, v_err = pitcher.get_command_error_inches('fastball')
            total_err = np.sqrt(h_err**2 + v_err**2)
            errors.append(total_err)

        mean_error = np.mean(errors)
        stamina_cap = pitcher.attributes.get_stamina_pitches()
        fatigue_pct = (pitches / stamina_cap) * 100

        # Get effective sigma (should match the RMS / sqrt(2))
        sigma = mean_error / np.sqrt(2)

        print(f"{pitches:<10} {fatigue_pct:<12.0f} {sigma:<15.1f} {mean_error:<15.1f} {mean_error/12:<15.2f}")

    print("\nExpected MLB values:")
    print("  Fresh pitcher: ~16\" sigma (~23\" RMS = 1.9 ft)")
    print("  Fatigued (75%): ~19\" sigma (~27\" RMS = 2.25 ft)")
    print("  Exhausted (100%): ~22\" sigma (~31\" RMS = 2.6 ft) [capped at 24\" sigma]")


def test_walk_rates():
    """Test walk rates in simulated at-bats."""
    print("\n" + "=" * 70)
    print("TEST 2: Walk Rates in Simulated At-Bats")
    print("=" * 70)

    # Create average pitcher
    pitcher = Pitcher(
        name="Average Pitcher",
        attributes=PitcherAttributes(
            RAW_VELOCITY_CAP=50000,   # ~92 mph
            COMMAND=50000,    # Average command
            CONTROL=50000,    # Average control
            STAMINA=50000     # 90 pitches
        ),
        pitch_arsenal={'fastball': {}, 'slider': {}, 'changeup': {}}
    )

    # Create average hitter
    hitter = Hitter(
        name="Average Hitter",
        attributes=HitterAttributes(
            BAT_SPEED=50000,
            BARREL_ACCURACY=50000,
            ZONE_DISCERNMENT=50000,
            SWING_DECISION_LATENCY=50000
        ),
        speed=50000
    )

    print(f"\nSimulating 200 at-bats...")
    print(f"Pitcher: {pitcher.name} (Command: 50k, Control: 50k)")
    print(f"Hitter: {hitter.name} (Discipline: 50k)")

    # Simulate at-bats
    num_at_bats = 200
    outcomes = {
        'strikeout': 0,
        'walk': 0,
        'in_play': 0,
    }

    total_pitches = 0
    walk_pitches = []

    for i in range(num_at_bats):
        # Reset pitcher periodically (simulate multiple games)
        if i % 30 == 0:
            pitcher.pitches_thrown = 0

        sim = AtBatSimulator(pitcher, hitter)
        result = sim.simulate_at_bat(verbose=False)

        outcomes[result.outcome] = outcomes.get(result.outcome, 0) + 1
        total_pitches += len(result.pitches)

        if result.outcome == 'walk':
            walk_pitches.append(len(result.pitches))

    # Calculate statistics
    total = sum(outcomes.values())
    walk_rate = (outcomes['walk'] / total) * 100
    k_rate = (outcomes['strikeout'] / total) * 100

    print(f"\nResults from {total} at-bats:")
    print(f"  Walks: {outcomes['walk']} ({walk_rate:.1f}%)")
    print(f"  Strikeouts: {outcomes['strikeout']} ({k_rate:.1f}%)")
    print(f"  Balls in play: {outcomes['in_play']} ({outcomes['in_play']/total*100:.1f}%)")
    print(f"  Average pitches per AB: {total_pitches / total:.1f}")

    if walk_pitches:
        print(f"  Average pitches per walk: {np.mean(walk_pitches):.1f}")

    print(f"\nMLB benchmarks:")
    print(f"  Walk rate: 8-9%")
    print(f"  Strikeout rate: 22-24%")
    print(f"  Balls in play: 67-70%")

    # Validation
    if 6 <= walk_rate <= 12:
        print(f"\n✓ Walk rate ({walk_rate:.1f}%) is within acceptable range (6-12%)")
    else:
        print(f"\n✗ Walk rate ({walk_rate:.1f}%) is outside acceptable range (6-12%)")
        if walk_rate > 12:
            print("  → Still too high, may need further tuning")
        else:
            print("  → Too low, command error may need slight increase")


def test_elite_vs_poor_command():
    """Test that elite vs poor command pitchers show clear differentiation."""
    print("\n" + "=" * 70)
    print("TEST 3: Elite vs Poor Command Differentiation")
    print("=" * 70)

    # Create pitchers with different command levels
    elite_pitcher = Pitcher(
        name="Elite Command",
        attributes=PitcherAttributes(
            RAW_VELOCITY_CAP=50000,
            COMMAND=85000,   # Elite command (9.5" sigma)
            CONTROL=85000,
            STAMINA=50000
        ),
        pitch_arsenal={'fastball': {}}
    )

    poor_pitcher = Pitcher(
        name="Poor Command",
        attributes=PitcherAttributes(
            RAW_VELOCITY_CAP=50000,
            COMMAND=20000,   # Poor command (~21.5" sigma)
            CONTROL=20000,
            STAMINA=50000
        ),
        pitch_arsenal={'fastball': {}}
    )

    hitter = Hitter(
        name="Average Hitter",
        attributes=HitterAttributes(ZONE_DISCERNMENT=50000, SWING_DECISION_LATENCY=50000)
    )

    print(f"\nElite Command Pitcher: {elite_pitcher.attributes.get_command_sigma_inches():.1f}\" sigma")
    print(f"Poor Command Pitcher: {poor_pitcher.attributes.get_command_sigma_inches():.1f}\" sigma")

    # Simulate 100 at-bats for each
    num_at_bats = 100

    results = {}
    for pitcher in [elite_pitcher, poor_pitcher]:
        walks = 0
        strikeouts = 0

        for _ in range(num_at_bats):
            pitcher.pitches_thrown = 0  # Reset between ABs
            sim = AtBatSimulator(pitcher, hitter)
            result = sim.simulate_at_bat(verbose=False)

            if result.outcome == 'walk':
                walks += 1
            elif result.outcome == 'strikeout':
                strikeouts += 1

        results[pitcher.name] = {
            'walks': walks,
            'walk_rate': (walks / num_at_bats) * 100,
            'strikeouts': strikeouts
        }

    print(f"\n{'Pitcher':<20} {'Walks':<10} {'Walk %':<10}")
    print("-" * 40)
    for name, stats in results.items():
        print(f"{name:<20} {stats['walks']:<10} {stats['walk_rate']:<10.1f}")

    elite_walk_rate = results['Elite Command']['walk_rate']
    poor_walk_rate = results['Poor Command']['walk_rate']

    print(f"\nExpected:")
    print(f"  Elite: 3-5% walks")
    print(f"  Poor: 12-18% walks")

    if poor_walk_rate > elite_walk_rate * 1.5:
        print(f"\n✓ Clear differentiation between elite and poor command")
    else:
        print(f"\n✗ Insufficient differentiation between command levels")


if __name__ == "__main__":
    print("\n" + "=" * 70)
    print("WALK RATE FIX VALIDATION")
    print("Testing fatigue multiplier changes (2.0× → 1.4×, nonlinear)")
    print("=" * 70)

    test_command_error_progression()
    test_walk_rates()
    test_elite_vs_poor_command()

    print("\n" + "=" * 70)
    print("VALIDATION COMPLETE")
    print("=" * 70)
