"""
50-game diagnostic with FIXED pitch intention logging

This version reads pitch intentions from pitch_data directly,
not from debug_collector, to capture 100% of pitches.

Previous version only captured 72.1% because it relied on debug_collector,
which isn't used by GameSimulator.
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from batted_ball import GameSimulator, create_test_team
from collections import defaultdict

def run_50game_fixed_diagnostic():
    """Run 50 games and extract pitch intentions from pitch_data"""

    print("="*80)
    print("50-GAME FIXED DIAGNOSTIC - Reading Pitch Intentions from pitch_data")
    print("="*80)
    print()

    # Create teams
    away_team = create_test_team("Visitors", "average")
    home_team = create_test_team("Home", "average")

    print(f"Simulating 50 games...")
    print(f"Expected sample: ~500 PA, ~1500-2000 total pitches")
    print()

    # Track pitch intentions across all games
    pitch_intentions = defaultdict(int)
    pitch_intentions_zone = defaultdict(int)
    total_pitches = 0
    total_pitches_with_intent = 0
    total_swings = 0
    total_whiffs = 0
    total_contacts = 0

    # Track by pitch type
    pitch_type_contact = defaultdict(lambda: {'swings': 0, 'whiffs': 0, 'contacts': 0})

    # Track K% and BB%
    total_pa = 0
    strikeouts = 0
    walks = 0

    # Track swing rates
    in_zone_swings = 0
    in_zone_pitches = 0
    out_zone_swings = 0
    out_zone_pitches = 0

    # Track foul balls
    total_fouls = 0
    fouls_with_0_strikes = 0
    fouls_with_1_strike = 0
    fouls_with_2_strikes = 0
    total_pitches_per_pa = 0

    # Simulate 50 games
    for game_num in range(1, 51):
        print(f"  Game {game_num:2d}/50...", end=" ", flush=True)

        sim = GameSimulator(away_team, home_team, verbose=False)
        result = sim.simulate_game(num_innings=9)

        # Extract at-bat results from game state (if available)
        # For now, simulate at-bats directly to get pitch data
        from batted_ball.at_bat import AtBatSimulator

        # Simulate 10 at-bats per game
        for ab in range(10):
            total_pa += 1

            pitcher = away_team.get_current_pitcher() if ab % 2 == 0 else home_team.get_current_pitcher()
            hitter = home_team.get_next_batter() if ab % 2 == 0 else away_team.get_next_batter()

            at_bat_sim = AtBatSimulator(pitcher=pitcher, hitter=hitter)
            at_bat_result = at_bat_sim.simulate_at_bat()

            # Track K% and BB%
            if at_bat_result.outcome == 'strikeout':
                strikeouts += 1
            elif at_bat_result.outcome == 'walk':
                walks += 1

            # Track pitches per PA
            total_pitches_per_pa += len(at_bat_result.pitches)

            # Extract pitch intentions from pitch_data
            for pitch_data in at_bat_result.pitches:
                total_pitches += 1

                # Check if pitch_intent exists
                if 'pitch_intent' in pitch_data:
                    intent_data = pitch_data['pitch_intent']
                    if 'intention_category' in intent_data:
                        total_pitches_with_intent += 1
                        intention = intent_data['intention_category']
                        pitch_intentions[intention] += 1

                        # Check if in zone
                        if pitch_data.get('is_strike', False):
                            pitch_intentions_zone[intention] += 1

                # Track swing/whiff/contact
                if pitch_data.get('swing', False):
                    total_swings += 1
                    pitch_type = pitch_data.get('pitch_type', 'unknown')

                    pitch_type_contact[pitch_type]['swings'] += 1

                    # Check pitch outcome to determine contact
                    pitch_outcome = pitch_data.get('pitch_outcome', 'unknown')
                    if pitch_outcome in ['foul', 'ball_in_play', 'contact']:
                        # Made contact
                        total_contacts += 1
                        pitch_type_contact[pitch_type]['contacts'] += 1
                    elif pitch_outcome in ['swinging_strike', 'whiff']:
                        # Whiffed
                        total_whiffs += 1
                        pitch_type_contact[pitch_type]['whiffs'] += 1
                    else:
                        # Unknown outcome on swing - count as whiff to be safe
                        total_whiffs += 1
                        pitch_type_contact[pitch_type]['whiffs'] += 1

                # Track swing rates by zone
                is_strike = pitch_data.get('is_strike', False)
                did_swing = pitch_data.get('swing', False)

                if is_strike:
                    in_zone_pitches += 1
                    if did_swing:
                        in_zone_swings += 1
                else:
                    out_zone_pitches += 1
                    if did_swing:
                        out_zone_swings += 1

                # Track foul balls
                pitch_outcome = pitch_data.get('pitch_outcome', 'unknown')
                if pitch_outcome == 'foul':
                    total_fouls += 1
                    # Get strike count before this pitch
                    count_before = pitch_data.get('count_before', (0, 0))
                    strikes_before = count_before[1]

                    if strikes_before == 0:
                        fouls_with_0_strikes += 1
                    elif strikes_before == 1:
                        fouls_with_1_strike += 1
                    elif strikes_before >= 2:
                        fouls_with_2_strikes += 1

        print("Done.")

    print()
    print("="*80)
    print("FIXED DIAGNOSTIC RESULTS")
    print("="*80)
    print()

    # Pitch Intention Analysis
    print("🎯 PITCH INTENTION ANALYSIS (Fixed - Reading from pitch_data):")
    print()
    print(f"   Total Pitches: {total_pitches}")
    print(f"   Pitches with Intention Data: {total_pitches_with_intent} ({total_pitches_with_intent/total_pitches*100:.1f}%)")
    print()
    print("   Intention Distribution:")

    for intention in ['strike_looking', 'strike_competitive', 'strike_corner',
                     'waste_chase', 'ball_intentional']:
        count = pitch_intentions.get(intention, 0)
        if total_pitches_with_intent > 0:
            pct = count / total_pitches_with_intent * 100
            zone_count = pitch_intentions_zone.get(intention, 0)
            zone_rate = (zone_count / count * 100) if count > 0 else 0
            print(f"      {intention:20s}: {count:4d} ({pct:5.1f}%) → Zone rate: {zone_rate:.1f}%")

    # Calculate overall zone rate
    total_in_zone = sum(pitch_intentions_zone.get(intent, 0)
                       for intent in ['strike_looking', 'strike_competitive', 'strike_corner',
                                     'waste_chase', 'ball_intentional'])
    overall_zone_rate = (total_in_zone / total_pitches_with_intent * 100) if total_pitches_with_intent > 0 else 0

    print()
    print(f"   Overall Zone Rate: {overall_zone_rate:.1f}%")
    print(f"   MLB Target: ~62-65%")
    print(f"   Expected (from diagnostic): ~59.8%")
    print()

    # Compare to expected distribution
    print("   🔍 COMPARISON TO EXPECTED DISTRIBUTION:")
    print()
    expected_dist = {
        'strike_looking': 34.9,
        'strike_competitive': 35.5,
        'strike_corner': 13.6,
        'waste_chase': 6.8,
        'ball_intentional': 9.2
    }

    for intention, expected_pct in expected_dist.items():
        observed_count = pitch_intentions.get(intention, 0)
        observed_pct = (observed_count / total_pitches_with_intent * 100) if total_pitches_with_intent > 0 else 0
        diff = observed_pct - expected_pct
        status = "✅" if abs(diff) < 3 else "⚠️" if abs(diff) < 6 else "🚨"
        print(f"      {status} {intention:20s}: {observed_pct:5.1f}% (expected: {expected_pct:.1f}%, diff: {diff:+.1f}pp)")

    print()

    # Swing Decision Analysis
    print("🏏 SWING DECISION ANALYSIS:")
    in_zone_swing_pct = (in_zone_swings / in_zone_pitches * 100) if in_zone_pitches > 0 else 0
    out_zone_swing_pct = (out_zone_swings / out_zone_pitches * 100) if out_zone_pitches > 0 else 0

    print(f"   In-Zone Swing%: {in_zone_swing_pct:.1f}% (MLB: ~65-70%)")
    print(f"   Out-of-Zone Swing% (Chase): {out_zone_swing_pct:.1f}% (MLB: ~25-35%)")
    print(f"   Swing% Gap: {in_zone_swing_pct - out_zone_swing_pct:.1f} percentage points")
    print()

    # Contact Rate Analysis
    print("🎯 CONTACT RATE ANALYSIS:")
    if total_swings > 0:
        contact_rate = (total_contacts / total_swings) * 100
        whiff_rate = (total_whiffs / total_swings) * 100

        print(f"   Total Swings: {total_swings}")
        print(f"   Total Contact: {total_contacts} ({contact_rate:.1f}%)")
        print(f"   Total Whiffs: {total_whiffs} ({whiff_rate:.1f}%)")
        print(f"   MLB Target Contact Rate: ~75-80%")
        print(f"   MLB Target Whiff Rate: ~20-25%")
        print()

        # NEW: Foul Ball Analysis
        print("⚾ FOUL BALL ANALYSIS (NEW - KEY FOR K% TUNING):")
        foul_rate = (total_fouls / total_swings) * 100 if total_swings > 0 else 0
        pitches_per_pa = total_pitches_per_pa / total_pa if total_pa > 0 else 0

        print(f"   Total Fouls: {total_fouls}")
        print(f"   Foul Ball Rate: {foul_rate:.1f}% of swings (MLB: ~20-25%)")
        print(f"   MLB Target: 20-25% of swings result in foul balls")
        print()

        # Foul balls by count
        print("   Foul Balls by Count:")
        foul_0_pct = (fouls_with_0_strikes / total_fouls * 100) if total_fouls > 0 else 0
        foul_1_pct = (fouls_with_1_strike / total_fouls * 100) if total_fouls > 0 else 0
        foul_2_pct = (fouls_with_2_strikes / total_fouls * 100) if total_fouls > 0 else 0

        print(f"      With 0 strikes: {fouls_with_0_strikes} ({foul_0_pct:.1f}%)")
        print(f"      With 1 strike:  {fouls_with_1_strike} ({foul_1_pct:.1f}%)")
        print(f"      With 2 strikes: {fouls_with_2_strikes} ({foul_2_pct:.1f}%)")
        print(f"      → 2-strike fouls should be highest (batters protecting plate)")
        print()

        # Pitches per PA
        print("   Pitches per Plate Appearance:")
        print(f"      Average: {pitches_per_pa:.2f} pitches/PA")
        print(f"      MLB Target: 3.8-4.0 pitches/PA")
        print()

        # Diagnosis
        if foul_rate < 15:
            print(f"   🚨 FOUL RATE TOO LOW: {foul_rate:.1f}% (target: 20-25%)")
            print(f"      → This is likely causing SHORT AT-BATS")
            print(f"      → Fewer fouls = fewer pitches per PA = fewer 2-strike counts = lower K%")
            print(f"      → RECOMMENDATION: Increase foul probability (especially with 2 strikes)")
        elif foul_rate > 30:
            print(f"   ⚠️ FOUL RATE TOO HIGH: {foul_rate:.1f}% (target: 20-25%)")
            print(f"      → At-bats may be TOO LONG")
        else:
            print(f"   ✅ Foul rate looks good: {foul_rate:.1f}% (target: 20-25%)")

        print()

        if pitches_per_pa < 3.5:
            print(f"   🚨 PITCHES/PA TOO LOW: {pitches_per_pa:.2f} (target: 3.8-4.0)")
            print(f"      → At-bats ending too quickly")
            print(f"      → Likely causes: low foul rate, high chase rate, or short counts")
        elif pitches_per_pa > 4.5:
            print(f"   ⚠️ PITCHES/PA TOO HIGH: {pitches_per_pa:.2f} (target: 3.8-4.0)")
            print(f"      → At-bats too long, may indicate too many fouls or walks")
        else:
            print(f"   ✅ Pitches/PA looks good: {pitches_per_pa:.2f} (target: 3.8-4.0)")

        print()

        # Contact rate by pitch type
        print("   Contact Rate by Pitch Type:")
        for pitch_type in sorted(pitch_type_contact.keys()):
            stats = pitch_type_contact[pitch_type]
            if stats['swings'] > 0:
                contact_pct = (stats['contacts'] / stats['swings']) * 100
                print(f"      {pitch_type:12s}: {contact_pct:5.1f}% contact ({stats['contacts']:3d}/{stats['swings']:3d} swings)")
        print()

    # K% and BB% Analysis
    print("📊 OUTCOME ANALYSIS:")
    k_pct = (strikeouts / total_pa) * 100 if total_pa > 0 else 0
    bb_pct = (walks / total_pa) * 100 if total_pa > 0 else 0

    print(f"   Total Plate Appearances: {total_pa}")
    print(f"   Strikeouts: {strikeouts} ({k_pct:.1f}%)")
    print(f"   Walks: {walks} ({bb_pct:.1f}%)")
    print(f"   MLB Target K%: ~22%")
    print(f"   MLB Target BB%: ~8-9%")
    print()

    # Diagnosis (with foul ball context)
    pitches_per_pa = total_pitches_per_pa / total_pa if total_pa > 0 else 0
    foul_rate = (total_fouls / total_swings) * 100 if total_swings > 0 else 0

    if k_pct < 18:
        print(f"   🚨 K% TOO LOW: {k_pct:.1f}% (target: 22%)")
        print(f"      → Zone rate: {overall_zone_rate:.1f}% (target: 62-65%)")
        print(f"      → Foul rate: {foul_rate:.1f}% (target: 20-25%)")
        print(f"      → Pitches/PA: {pitches_per_pa:.2f} (target: 3.8-4.0)")
        if overall_zone_rate < 55:
            print(f"      → ZONE RATE is the bottleneck!")
            print(f"      → Need to increase strike_looking pitches or reduce command sigma")
        elif foul_rate < 15 or pitches_per_pa < 3.5:
            print(f"      → Zone rate OK, but FOUL RATE TOO LOW or PITCHES/PA TOO SHORT")
            print(f"      → At-bats not getting deep enough for K opportunities")
            print(f"      → Need to increase foul probability (especially with 2 strikes)")
        else:
            print(f"      → Zone rate OK, fouls OK, but K% still low")
            print(f"      → May need to adjust 2-strike whiff rates or chase rate")
    elif k_pct > 26:
        print(f"   ⚠️ K% TOO HIGH: {k_pct:.1f}% (target: 22%)")
        print(f"      → May need to reduce whiff rates or increase contact rates")
    else:
        print(f"   ✅ K% looks good: {k_pct:.1f}% (target: 22%)")

    print()

    if bb_pct < 6:
        print(f"   ⚠️ BB% TOO LOW: {bb_pct:.1f}% (target: 8-9%)")
        print(f"      → Zone rate may still be too high or batters too aggressive")
    elif bb_pct > 12:
        print(f"   🚨 BB% TOO HIGH: {bb_pct:.1f}% (target: 8-9%)")
        print(f"      → Zone rate too low or batters too passive")
    else:
        print(f"   ✅ BB% looks good: {bb_pct:.1f}% (target: 8-9%)")

    print()
    print("="*80)
    print("CONCLUSION")
    print("="*80)
    print()

    if total_pitches_with_intent >= total_pitches * 0.95:
        print("✅ Pitch intention data captured successfully (≥95% of pitches)")
    else:
        print(f"⚠️ Only {total_pitches_with_intent/total_pitches*100:.1f}% of pitches have intention data")
        print(f"   This suggests pitch_intent is not being stored in pitch_data")

    print()

    # Overall assessment
    zone_ok = 55 <= overall_zone_rate <= 70
    k_ok = 18 <= k_pct <= 26
    bb_ok = 6 <= bb_pct <= 12

    if zone_ok and k_ok and bb_ok:
        print("🎉 PHASE 2A SUCCESS! All metrics at MLB targets!")
        print("   ✅ Zone rate: MLB range")
        print("   ✅ K%: MLB range")
        print("   ✅ BB%: MLB range")
    elif zone_ok:
        print("⚠️ Zone rate good, but K%/BB% need adjustment")
        print(f"   ✅ Zone rate: {overall_zone_rate:.1f}% (target: 62-65%)")
        print(f"   {'✅' if k_ok else '🚨'} K%: {k_pct:.1f}% (target: 22%)")
        print(f"   {'✅' if bb_ok else '⚠️'} BB%: {bb_pct:.1f}% (target: 8-9%)")
    else:
        print("🚨 Zone rate still the primary bottleneck")
        print(f"   Zone rate: {overall_zone_rate:.1f}% (target: 62-65%)")
        print(f"   Need to investigate command sigma execution or pitch intention distribution")

    print()

if __name__ == "__main__":
    run_50game_fixed_diagnostic()
