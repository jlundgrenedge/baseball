#!/usr/bin/env python3
"""Debug pitch locations to understand why walk rate is so high."""

import numpy as np
from batted_ball import Pitcher, Hitter, AtBatSimulator
from batted_ball.attributes import PitcherAttributes, HitterAttributes

def analyze_pitch_locations():
    """Analyze where pitches are actually landing."""

    # Create average pitcher and hitter
    pitcher = Pitcher(
        name="Average Pitcher",
        attributes=PitcherAttributes(
            RAW_VELOCITY_CAP=50000,
            COMMAND=50000,
            CONTROL=50000,
            STAMINA=50000
        ),
        pitch_arsenal={'fastball': {}}
    )

    hitter = Hitter(
        name="Average Hitter",
        attributes=HitterAttributes(ZONE_DISCERNMENT=50000)
    )

    print("=" * 80)
    print("PITCH LOCATION ANALYSIS")
    print("=" * 80)
    print(f"\nPitcher: {pitcher.attributes.get_command_sigma_inches():.1f}\" sigma command error")
    print(f"Strike zone: ±8.5\" horizontal (17\" wide), 18\"-42\" vertical (24\" tall)")

    # Simulate many pitches
    strike_count = 0
    ball_count = 0
    pitch_locations = []
    intentions = []

    num_pitches = 1000
    for i in range(num_pitches):
        pitcher.pitches_thrown = 0  # Reset each time

        sim = AtBatSimulator(pitcher, hitter)

        # Simulate first pitch (0-0 count)
        count = (0, 0)
        pitch_type = 'fastball'

        # Get target location with intention
        (target_h, target_v), intention = sim.select_target_location(count, pitch_type, return_intention=True)

        # Simulate pitch
        pitch_data = sim.simulate_pitch(pitch_type, (target_h, target_v))

        # Record results
        is_strike = pitch_data['is_strike']
        final_h, final_v = pitch_data['final_location']

        pitch_locations.append((final_h, final_v))
        intentions.append(intention)

        if is_strike:
            strike_count += 1
        else:
            ball_count += 1

    strike_pct = (strike_count / num_pitches) * 100
    ball_pct = (ball_count / num_pitches) * 100

    print(f"\nResults from {num_pitches} first pitches:")
    print(f"  Strikes: {strike_count} ({strike_pct:.1f}%)")
    print(f"  Balls: {ball_count} ({ball_pct:.1f}%)")

    print(f"\nExpected MLB first-pitch strike rate: 58-62%")

    # Analyze intentions
    intention_counts = {}
    for intent in intentions:
        intention_counts[intent] = intention_counts.get(intent, 0) + 1

    print(f"\nPitch intentions:")
    for intent, count in sorted(intention_counts.items(), key=lambda x: -x[1]):
        pct = (count / num_pitches) * 100
        print(f"  {intent}: {count} ({pct:.1f}%)")

    # Analyze location distribution
    locations = np.array(pitch_locations)
    h_locations = locations[:, 0]
    v_locations = locations[:, 1]

    print(f"\nLocation statistics:")
    print(f"  Horizontal: mean={np.mean(h_locations):.1f}\", std={np.std(h_locations):.1f}\"")
    print(f"  Vertical: mean={np.mean(v_locations):.1f}\", std={np.std(v_locations):.1f}\"")

    # Check how many are way outside
    way_outside_h = np.sum(np.abs(h_locations) > 12.0)  # >3.5" outside zone
    way_outside_v_low = np.sum(v_locations < 14.0)  # >4" below zone
    way_outside_v_high = np.sum(v_locations > 46.0)  # >4" above zone

    print(f"\nWay outside zone:")
    print(f"  Horizontal (>12\"): {way_outside_h} ({way_outside_h/num_pitches*100:.1f}%)")
    print(f"  Too low (<14\"): {way_outside_v_low} ({way_outside_v_low/num_pitches*100:.1f}%)")
    print(f"  Too high (>46\"): {way_outside_v_high} ({way_outside_v_high/num_pitches*100:.1f}%)")


if __name__ == "__main__":
    analyze_pitch_locations()
