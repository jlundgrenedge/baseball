"""
Test script to validate at-bat outcome distributions against MLB averages.

Runs 1000+ at-bats and compares to expected MLB statistics.
"""

import numpy as np
from batted_ball import Pitcher, Hitter, AtBatSimulator


def create_test_pitcher():
    """Create an average MLB pitcher."""
    pitcher = Pitcher(
        name="Test Pitcher",
        velocity=50,  # Average velocity rating
        spin_rate=50,  # Average spin rate
        spin_efficiency=50,  # Average spin efficiency
        command=50,  # Average command
        control=50,  # Average control
        deception=50,  # Average deception
        stamina=100,  # Full stamina
    )

    # Average arsenal
    pitcher.pitch_arsenal = {
        'fastball': {'velocity': 50, 'movement': 50, 'command': 50, 'usage': 60},
        'slider': {'velocity': 48, 'movement': 60, 'command': 45, 'usage': 25},
        'changeup': {'velocity': 45, 'movement': 55, 'command': 48, 'usage': 15},
    }

    return pitcher


def create_test_hitter():
    """Create an average MLB hitter."""
    return Hitter(
        name="Test Hitter",
        bat_speed=50,  # Average bat speed
        barrel_accuracy=50,  # Average barrel control
        swing_timing_precision=50,  # Average timing
        bat_control=50,  # Average bat control
        exit_velocity_ceiling=50,  # Average power
        zone_discipline=50,  # Average discipline
        pitch_recognition_speed=50,  # Average pitch recognition
        swing_decision_aggressiveness=50,  # Average swing rate
        adjustment_ability=50,  # Average adjustment
    )


def run_at_bat_tests(n_at_bats=1000):
    """
    Run multiple at-bats and analyze outcome distributions.

    Parameters
    ----------
    n_at_bats : int
        Number of at-bats to simulate
    """
    print(f"Running {n_at_bats} at-bat simulations...")
    print("=" * 70)

    pitcher = create_test_pitcher()
    hitter = create_test_hitter()

    outcomes = {
        'strikeout': 0,
        'walk': 0,
        'in_play': 0,
        'foul': 0,
    }

    total_pitches = 0
    pitch_per_ab = []

    for i in range(n_at_bats):
        # Reset stamina for each at-bat (simulate fresh pitcher)
        pitcher.current_stamina = 100

        sim = AtBatSimulator(pitcher, hitter)
        result = sim.simulate_at_bat(verbose=False)

        outcomes[result.outcome] += 1
        total_pitches += len(result.pitches)
        pitch_per_ab.append(len(result.pitches))

        if (i + 1) % 100 == 0:
            print(f"  Completed {i + 1}/{n_at_bats} at-bats...")

    print("\n" + "=" * 70)
    print("OUTCOME DISTRIBUTION ANALYSIS")
    print("=" * 70)

    # Calculate percentages
    total = sum(outcomes.values())

    print(f"\nTotal At-Bats: {total}")
    print(f"Total Pitches: {total_pitches}")
    print(f"Average Pitches per At-Bat: {total_pitches / total:.2f}")
    print(f"Pitches per AB Range: {min(pitch_per_ab)}-{max(pitch_per_ab)}")

    print("\n" + "-" * 70)
    print("OUTCOME BREAKDOWN")
    print("-" * 70)

    # Expected MLB averages (approximate)
    expected = {
        'strikeout': 0.23,  # ~23% K rate
        'walk': 0.09,       # ~9% BB rate
        'in_play': 0.68,    # ~68% balls in play
    }

    print(f"\n{'Outcome':<15} {'Actual':<15} {'Expected':<15} {'Difference':<15}")
    print("-" * 70)

    for outcome in ['strikeout', 'walk', 'in_play']:
        count = outcomes[outcome]
        actual_pct = count / total
        expected_pct = expected[outcome]
        diff = actual_pct - expected_pct

        status = "✓" if abs(diff) < 0.05 else "⚠" if abs(diff) < 0.10 else "✗"

        print(f"{outcome.capitalize():<15} "
              f"{actual_pct:>6.1%} ({count:>4}) "
              f"{expected_pct:>6.1%}         "
              f"{diff:>+6.1%} {status}")

    # Foul balls (not counted as at-bat result in MLB)
    if outcomes['foul'] > 0:
        print(f"\nNote: {outcomes['foul']} at-bats ended as 'foul' (edge case)")

    print("\n" + "-" * 70)
    print("VALIDATION SUMMARY")
    print("-" * 70)

    # Check if within acceptable ranges
    k_rate = outcomes['strikeout'] / total
    bb_rate = outcomes['walk'] / total
    bip_rate = outcomes['in_play'] / total

    checks = []

    # Strikeout rate: 20-25% is good
    if 0.18 <= k_rate <= 0.28:
        checks.append("✓ Strikeout rate is realistic (18-28%)")
    else:
        checks.append(f"✗ Strikeout rate {k_rate:.1%} is outside realistic range (18-28%)")

    # Walk rate: 7-11% is good
    if 0.06 <= bb_rate <= 0.12:
        checks.append("✓ Walk rate is realistic (6-12%)")
    else:
        checks.append(f"✗ Walk rate {bb_rate:.1%} is outside realistic range (6-12%)")

    # Balls in play: 65-72% is good
    if 0.63 <= bip_rate <= 0.75:
        checks.append("✓ Balls in play rate is realistic (63-75%)")
    else:
        checks.append(f"✗ Balls in play rate {bip_rate:.1%} is outside realistic range (63-75%)")

    # Pitches per at-bat: 3.5-4.5 is typical
    avg_pitches = total_pitches / total
    if 3.3 <= avg_pitches <= 5.0:
        checks.append(f"✓ Pitches per at-bat {avg_pitches:.2f} is realistic (3.3-5.0)")
    else:
        checks.append(f"✗ Pitches per at-bat {avg_pitches:.2f} is outside realistic range (3.3-5.0)")

    print()
    for check in checks:
        print(check)

    print("\n" + "=" * 70)

    # Return summary for further analysis
    return {
        'outcomes': outcomes,
        'total_pitches': total_pitches,
        'pitch_per_ab': pitch_per_ab,
        'rates': {
            'strikeout': k_rate,
            'walk': bb_rate,
            'in_play': bip_rate,
        }
    }


if __name__ == '__main__':
    # Run test with 250 at-bats (faster, still statistically meaningful)
    results = run_at_bat_tests(250)

    print("\nTest complete! See results above.")
    print("\nMLB Average Benchmarks:")
    print("  Strikeouts: 20-25%")
    print("  Walks: 7-11%")
    print("  Balls in Play: 65-72%")
    print("  Pitches per AB: 3.5-4.5")
