"""
Swing Decision Logic Diagnostic Tool
=====================================

This script analyzes the current swing decision model to identify issues with:
- Swing rates on borderline and outside pitches
- Relationship between batter ratings and swing behavior
- Zone-based swing probability distributions
- Expected value reasoning in swing decisions

Usage:
    python diagnose_swing_logic.py
"""

import numpy as np
import matplotlib.pyplot as plt
from batted_ball import Pitcher, Hitter
from batted_ball.attributes import HitterAttributes

def analyze_swing_probability_by_location(hitter, count=(0, 0)):
    """
    Analyze swing probability across different pitch locations.
    """
    print("\n" + "="*80)
    print(f"SWING PROBABILITY BY LOCATION (Count: {count[0]}-{count[1]})")
    print("="*80)

    # Define zones to test
    zones = {
        'Heart (0", 30")': (0.0, 30.0, True),
        'Edge High (0", 40")': (0.0, 40.0, True),
        'Edge Low (0", 20")': (0.0, 20.0, True),
        'Edge Inside (7", 30")': (7.0, 30.0, True),
        'Edge Outside (-7", 30")': (-7.0, 30.0, True),
        'Corner High-Inside (7", 40")': (7.0, 40.0, True),
        'Just Outside High (0", 44")': (0.0, 44.0, False),
        'Just Outside Low (0", 16")': (0.0, 16.0, False),
        'Just Outside Wide (10", 30")': (10.0, 30.0, False),
        'Chase Low (0", 12")': (0.0, 12.0, False),
        'Chase Wide (13", 30")': (13.0, 30.0, False),
        'Way Outside (16", 30")': (16.0, 30.0, False),
    }

    results = []

    for zone_name, (h_loc, v_loc, is_strike) in zones.items():
        # Run 1000 trials to get swing rate
        swings = 0
        n_trials = 1000

        for _ in range(n_trials):
            decision = hitter.decide_to_swing(
                pitch_location=(h_loc, v_loc),
                is_strike=is_strike,
                count=count,
                pitch_velocity=92.0,
                pitch_type='fastball'
            )
            if decision:
                swings += 1

        swing_rate = swings / n_trials
        results.append((zone_name, h_loc, v_loc, is_strike, swing_rate))

        print(f"{zone_name:30s} | Strike: {str(is_strike):5s} | Swing Rate: {swing_rate:5.1%}")

    return results

def analyze_discipline_effect(counts=[(0, 0), (2, 0), (0, 2), (3, 2)]):
    """
    Analyze how discipline rating affects swing rates.
    """
    print("\n" + "="*80)
    print("DISCIPLINE RATING EFFECT ON CHASE RATE")
    print("="*80)

    discipline_levels = {
        'Poor (20k)': 20000,
        'Below Avg (40k)': 40000,
        'Average (50k)': 50000,
        'Good (70k)': 70000,
        'Elite (90k)': 90000,
    }

    # Test location: Chase pitch (low and outside zone)
    chase_location = (10.0, 16.0)  # Just outside zone
    is_strike = False

    print(f"\nChase Pitch Location: {chase_location} (outside zone)")
    print("\nDiscipline Level      | Zone Discernment | " + " | ".join([f"{c[0]}-{c[1]}" for c in counts]))
    print("-" * 80)

    for disc_name, disc_rating in discipline_levels.items():
        # Create hitter with this discipline level
        attrs = HitterAttributes(ZONE_DISCERNMENT=disc_rating)
        hitter = Hitter(
            name=f"Test_{disc_name}",
            attributes=attrs,
            speed=50000
        )

        zone_disc_factor = attrs.get_zone_discernment_factor()

        # Test swing rate for each count
        swing_rates = []
        for count in counts:
            swings = sum(
                hitter.decide_to_swing(
                    pitch_location=chase_location,
                    is_strike=is_strike,
                    count=count,
                    pitch_velocity=92.0,
                    pitch_type='slider'
                )
                for _ in range(1000)
            ) / 1000.0
            swing_rates.append(swings)

        rates_str = " | ".join([f"{rate:5.1%}" for rate in swing_rates])
        print(f"{disc_name:20s} | {zone_disc_factor:16.3f} | {rates_str}")

def analyze_zone_swing_gradient():
    """
    Analyze how swing probability changes from center to edge of zone.
    """
    print("\n" + "="*80)
    print("SWING PROBABILITY GRADIENT (Center to Edge)")
    print("="*80)

    # Create average hitter
    hitter = Hitter(
        name="Average Joe",
        attributes=HitterAttributes(),
        speed=50000
    )

    # Test horizontal positions from center (0") to outside (15")
    horizontal_positions = np.linspace(0, 15, 16)
    vertical_center = 30.0  # Middle of zone

    print("\nHorizontal Distance | Strike? | Swing Rate (1000 trials)")
    print("-" * 60)

    for h_pos in horizontal_positions:
        # Determine if strike (zone is ±8.5")
        is_strike = abs(h_pos) <= 8.5

        # Calculate swing rate
        swings = sum(
            hitter.decide_to_swing(
                pitch_location=(h_pos, vertical_center),
                is_strike=is_strike,
                count=(0, 0),
                pitch_velocity=92.0,
                pitch_type='fastball'
            )
            for _ in range(1000)
        ) / 1000.0

        zone_marker = "IN ZONE" if is_strike else "OUTSIDE"
        print(f"{h_pos:5.1f}\"            | {zone_marker:7s} | {swings:5.1%}")

def analyze_swing_diagnostics():
    """
    Examine swing decision diagnostics for specific pitches.
    """
    print("\n" + "="*80)
    print("SWING DECISION DIAGNOSTICS")
    print("="*80)

    # Create hitters with different profiles
    # Note: SWING_DECISION_LATENCY attribute is inverse-mapped
    #   - High rating (90k) → Low latency (fast, aggressive)
    #   - Low rating (20k) → High latency (slow, passive)
    hitters = {
        'Disciplined': Hitter(
            name="Patient Pete",
            attributes=HitterAttributes(
                ZONE_DISCERNMENT=85000,  # Elite discipline
                SWING_DECISION_LATENCY=50000  # Average decision speed
            ),
            speed=50000
        ),
        'Aggressive': Hitter(
            name="Hacker Harry",
            attributes=HitterAttributes(
                BAT_SPEED=70000,
                ZONE_DISCERNMENT=30000,  # Poor discipline
                SWING_DECISION_LATENCY=90000  # Very fast/aggressive (high rating = low latency!)
            ),
            speed=50000
        ),
        'Average': Hitter(
            name="Average Joe",
            attributes=HitterAttributes(
                ZONE_DISCERNMENT=50000,
                SWING_DECISION_LATENCY=50000
            ),
            speed=50000
        ),
    }

    # Test pitches
    test_pitches = [
        ('Heart Strike', (0.0, 30.0), True),
        ('Edge Strike', (7.5, 30.0), True),
        ('Borderline', (9.0, 30.0), False),
        ('Chase Low', (0.0, 14.0), False),
        ('Way Outside', (14.0, 30.0), False),
    ]

    for pitch_name, location, is_strike in test_pitches:
        print(f"\n{pitch_name}: {location} (Strike: {is_strike})")
        print("-" * 80)

        for hitter_type, hitter in hitters.items():
            decision, diagnostics = hitter.decide_to_swing(
                pitch_location=location,
                is_strike=is_strike,
                count=(1, 1),
                pitch_velocity=92.0,
                pitch_type='fastball',
                return_diagnostics=True
            )

            print(f"  {hitter_type:12s}: {diagnostics['decision']:5s} "
                  f"(p={diagnostics['swing_probability']:.3f}, "
                  f"aggr={diagnostics['aggression_modifier']:+.3f})")

def identify_issues():
    """
    Identify specific issues with the current swing logic.
    """
    print("\n" + "="*80)
    print("IDENTIFIED ISSUES AND RECOMMENDATIONS")
    print("="*80)

    issues = []

    # Test 1: Check base chase rates
    avg_hitter = Hitter(name="Test", attributes=HitterAttributes(), speed=50000)

    # Just outside zone pitch
    chase_swings = sum(
        avg_hitter.decide_to_swing(
            pitch_location=(10.0, 30.0),  # 1.5" outside zone
            is_strike=False,
            count=(0, 0),
            pitch_velocity=92.0,
            pitch_type='fastball'
        )
        for _ in range(1000)
    ) / 1000.0

    # MLB average chase rate is ~28-32%
    if chase_swings > 0.35:
        issues.append(f"❌ ISSUE 1: Base chase rate too high ({chase_swings:.1%} vs MLB avg ~30%)")
    else:
        print(f"✅ Base chase rate OK: {chase_swings:.1%}")

    # Test 2: Check discipline differentiation
    poor_disc_hitter = Hitter(
        name="Poor",
        attributes=HitterAttributes(ZONE_DISCERNMENT=20000),
        speed=50000
    )
    elite_disc_hitter = Hitter(
        name="Elite",
        attributes=HitterAttributes(ZONE_DISCERNMENT=90000),
        speed=50000
    )

    poor_chase = sum(
        poor_disc_hitter.decide_to_swing(
            pitch_location=(10.0, 30.0),
            is_strike=False,
            count=(0, 0),
            pitch_velocity=92.0,
            pitch_type='fastball'
        )
        for _ in range(1000)
    ) / 1000.0

    elite_chase = sum(
        elite_disc_hitter.decide_to_swing(
            pitch_location=(10.0, 30.0),
            is_strike=False,
            count=(0, 0),
            pitch_velocity=92.0,
            pitch_type='fastball'
        )
        for _ in range(1000)
    ) / 1000.0

    discipline_spread = poor_chase - elite_chase

    if discipline_spread < 0.15:
        issues.append(f"❌ ISSUE 2: Discipline rating has weak effect (spread: {discipline_spread:.1%}, want >15%)")
    else:
        print(f"✅ Discipline differentiation OK: Poor={poor_chase:.1%}, Elite={elite_chase:.1%}, Spread={discipline_spread:.1%}")

    # Test 3: Check in-zone swing rates
    heart_swings = sum(
        avg_hitter.decide_to_swing(
            pitch_location=(0.0, 30.0),  # Heart of zone
            is_strike=True,
            count=(0, 0),
            pitch_velocity=92.0,
            pitch_type='fastball'
        )
        for _ in range(1000)
    ) / 1000.0

    # MLB average swing rate on pitches in zone is ~67-70%
    if heart_swings > 0.90:
        issues.append(f"❌ ISSUE 3: In-zone swing rate too high ({heart_swings:.1%} vs MLB avg ~68%)")
    elif heart_swings < 0.60:
        issues.append(f"❌ ISSUE 3: In-zone swing rate too low ({heart_swings:.1%} vs MLB avg ~68%)")
    else:
        print(f"✅ In-zone swing rate OK: {heart_swings:.1%}")

    # Print all issues
    if issues:
        print("\n⚠️  ISSUES FOUND:")
        for issue in issues:
            print(f"  {issue}")
    else:
        print("\n✅ All checks passed!")

    # Recommendations
    print("\n💡 RECOMMENDATIONS:")
    print("  1. Verify base swing probabilities match MLB Statcast data")
    print("  2. Increase discipline rating effect on chase rate")
    print("  3. Add expected value (EV) reasoning to swing decisions")
    print("  4. Consider pitch-specific recognition (e.g., slider vs fastball)")
    print("  5. Implement zone-specific swing maps (heat, edge, chase)")

def main():
    """
    Run all diagnostic tests.
    """
    print("\n" + "="*80)
    print("SWING DECISION LOGIC DIAGNOSTIC REPORT")
    print("="*80)

    # Create test hitters
    avg_hitter = Hitter(
        name="Average Joe",
        attributes=HitterAttributes(),
        speed=50000
    )

    # Run diagnostics
    analyze_swing_probability_by_location(avg_hitter, count=(0, 0))
    analyze_swing_probability_by_location(avg_hitter, count=(0, 2))
    analyze_swing_probability_by_location(avg_hitter, count=(3, 2))
    analyze_discipline_effect()
    analyze_zone_swing_gradient()
    analyze_swing_diagnostics()
    identify_issues()

    print("\n" + "="*80)
    print("DIAGNOSTIC COMPLETE")
    print("="*80)

if __name__ == "__main__":
    main()
