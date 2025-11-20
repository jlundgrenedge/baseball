"""
Diagnostic script to analyze pitch intention distribution

This will help us understand why we're only getting 27.8% strike_looking
when we expect ~60% from the code logic.
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import numpy as np
from collections import Counter, defaultdict
from batted_ball import Pitcher, Hitter, create_test_team
from batted_ball.at_bat import AtBatSimulator

def test_pitch_intention_distribution():
    """
    Test what pitch intentions are actually being selected
    """

    print("="*80)
    print("PITCH INTENTION DISTRIBUTION DIAGNOSTIC")
    print("="*80)
    print()

    # Create test pitcher and hitter
    team = create_test_team("Test", "average")
    pitcher = team.pitchers[0]
    hitter = team.hitters[0]

    print(f"Pitcher Control: {pitcher.attributes.CONTROL:,} (0-100k scale)")
    print(f"Control Zone Bias: {pitcher.attributes.get_control_zone_bias():.3f}")
    print()

    # Simulate intentions for different counts
    sim = AtBatSimulator(pitcher, hitter)

    # Test each common count
    counts_to_test = [
        (0, 0, "0-0 (First pitch)"),
        (1, 0, "1-0"),
        (0, 1, "0-1"),
        (1, 1, "1-1 (Even count)"),
        (2, 0, "2-0 (Hitter's count)"),
        (0, 2, "0-2 (Pitcher ahead)"),
        (2, 1, "2-1"),
        (1, 2, "1-2"),
        (2, 2, "2-2 (Full count)"),
        (3, 0, "3-0 (Must throw strike)"),
        (3, 2, "3-2 (Full count)"),
    ]

    # Sample each count 1000 times
    sample_size = 1000

    for balls, strikes, description in counts_to_test:
        intentions = []
        for _ in range(sample_size):
            intention = sim._determine_pitch_intention(balls, strikes, 'fastball')
            intentions.append(intention)

        counts = Counter(intentions)
        total = len(intentions)

        print(f"\n{description}:")
        for intent in ['strike_looking', 'strike_competitive', 'strike_corner', 'waste_chase', 'ball_intentional']:
            count = counts.get(intent, 0)
            pct = (count / total) * 100
            print(f"  {intent:20s}: {count:4d} ({pct:5.1f}%)")

    print()
    print("="*80)
    print("WEIGHTED AVERAGE ACROSS TYPICAL GAME")
    print("="*80)
    print()

    # Estimate typical count distribution in a game
    # Based on MLB data, approximate distribution of counts during at-bats
    count_weights = {
        (0, 0): 1.00,  # Every AB starts here
        (1, 0): 0.50,  # ~50% of ABs reach this
        (0, 1): 0.50,  # ~50% of ABs reach this
        (1, 1): 0.30,  # ~30% reach even counts
        (2, 0): 0.20,  # Fewer reach hitter's counts
        (0, 2): 0.25,  # ~25% reach pitcher ahead 0-2
        (2, 1): 0.15,
        (1, 2): 0.20,
        (2, 2): 0.10,
        (3, 0): 0.05,  # Rare
        (3, 1): 0.05,
        (3, 2): 0.08,
    }

    # Sample intentions according to weights
    all_intentions = []
    for (balls, strikes), weight in count_weights.items():
        num_samples = int(weight * 1000)
        for _ in range(num_samples):
            intention = sim._determine_pitch_intention(balls, strikes, 'fastball')
            all_intentions.append(intention)

    counts = Counter(all_intentions)
    total = len(all_intentions)

    print("Estimated game-wide intention distribution:")
    print(f"(Based on typical count progression in MLB)")
    print()
    for intent in ['strike_looking', 'strike_competitive', 'strike_corner', 'waste_chase', 'ball_intentional']:
        count = counts.get(intent, 0)
        pct = (count / total) * 100
        print(f"  {intent:20s}: {count:4d} ({pct:5.1f}%)")

    print()
    print("Expected zone rate with these intentions:")
    zone_rates = {
        'strike_looking': 0.885,  # Sprint 4 result
        'strike_competitive': 0.612,
        'strike_corner': 0.401,
        'waste_chase': 0.179,
        'ball_intentional': 0.060,
    }

    weighted_zone = 0
    for intent in ['strike_looking', 'strike_competitive', 'strike_corner', 'waste_chase', 'ball_intentional']:
        count = counts.get(intent, 0)
        pct = count / total
        contribution = pct * zone_rates[intent]
        weighted_zone += contribution
        print(f"  {intent:20s}: {pct:5.1%} × {zone_rates[intent]:.1%} = {contribution:.1%} contribution")

    print(f"\nTotal expected zone rate: {weighted_zone:.1%}")
    print()

    print("="*80)
    print("CONTROL BIAS ANALYSIS")
    print("="*80)
    print()

    # Test how control bias affects distribution for 0-0 count
    print("0-0 count intention distribution by pitcher control:")
    print()

    control_values = [
        (30000, "Poor"),
        (50000, "Average"),
        (70000, "Good"),
        (85000, "Elite"),
    ]

    for control_rating, description in control_values:
        # Create pitcher with specific control
        pitcher.attributes.CONTROL = control_rating
        control_bias = pitcher.attributes.get_control_zone_bias()
        sim = AtBatSimulator(pitcher, hitter)

        intentions = []
        for _ in range(sample_size):
            intention = sim._determine_pitch_intention(0, 0, 'fastball')
            intentions.append(intention)

        counts = Counter(intentions)
        total = len(intentions)

        print(f"\n{description} Control ({control_rating:,}, bias={control_bias:.3f}):")
        for intent in ['strike_looking', 'strike_competitive', 'strike_corner', 'ball_intentional']:
            count = counts.get(intent, 0)
            pct = (count / total) * 100
            print(f"  {intent:20s}: {count:4d} ({pct:5.1f}%)")

    print()
    print("="*80)
    print("CONCLUSION")
    print("="*80)
    print()
    print("If observed 27.8% strike_looking is much lower than predicted,")
    print("possible causes:")
    print("1. Count distribution in actual games different from model")
    print("2. Logging only capturing subset of pitches")
    print("3. Different code path being used in game simulation")
    print()

if __name__ == "__main__":
    test_pitch_intention_distribution()
