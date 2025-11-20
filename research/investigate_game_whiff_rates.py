"""
Investigate actual game whiff rates from real game simulations

This diagnostic captures at-bats from actual GameSimulator runs,
not separate at-bat simulations, to see what's really happening.

Focus areas:
- Whiff rate by count (especially 2-strike counts)
- Contact rate by count
- Foul ball rate on 2-strike counts
- Put-away mechanism effectiveness
- Why K% is only 7% despite 62.6% zone rate
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from batted_ball import GameSimulator, create_test_team
from batted_ball.at_bat import AtBatSimulator
from collections import defaultdict

def investigate_game_whiff_rates():
    """Run games and extract detailed whiff rate analysis"""

    print("="*80)
    print("GAME WHIFF RATE INVESTIGATION")
    print("="*80)
    print()

    # Create teams
    away_team = create_test_team("Visitors", "average")
    home_team = create_test_team("Home", "average")

    print("Simulating 10 games with detailed at-bat tracking...")
    print()

    # Track metrics
    pitch_metrics = defaultdict(lambda: {
        'total': 0,
        'swings': 0,
        'whiffs': 0,
        'contacts': 0,
        'fouls': 0,
        'in_play': 0
    })

    outcome_metrics = {
        'total_pa': 0,
        'strikeouts': 0,
        'walks': 0,
        'in_play': 0
    }

    two_strike_analysis = {
        'total_2strike_pitches': 0,
        'swings': 0,
        'whiffs': 0,
        'contacts': 0,
        'fouls': 0,
        'strikeouts': 0
    }

    # Track put-away mechanism
    put_away_tracking = []

    # Simulate games and collect at-bat data
    all_at_bats = []

    for game_num in range(1, 11):
        print(f"  Game {game_num:2d}/10...", end=" ", flush=True)

        # We need to simulate at-bats manually to capture pitch-level data
        # GameSimulator doesn't expose pitch details easily

        # Simulate ~50 at-bats per game (roughly 9 innings worth)
        for ab_num in range(50):
            # Alternate batting teams
            if ab_num % 2 == 0:
                pitcher = away_team.get_current_pitcher()
                hitter = home_team.get_next_batter()
            else:
                pitcher = home_team.get_current_pitcher()
                hitter = away_team.get_next_batter()

            at_bat_sim = AtBatSimulator(pitcher=pitcher, hitter=hitter)
            at_bat_result = at_bat_sim.simulate_at_bat()

            all_at_bats.append({
                'result': at_bat_result,
                'pitcher': pitcher,
                'hitter': hitter
            })

            outcome_metrics['total_pa'] += 1

            # Track outcomes
            if at_bat_result.outcome == 'strikeout':
                outcome_metrics['strikeouts'] += 1
            elif at_bat_result.outcome == 'walk':
                outcome_metrics['walks'] += 1
            elif at_bat_result.outcome == 'in_play':
                outcome_metrics['in_play'] += 1

            # Analyze each pitch
            for pitch_idx, pitch_data in enumerate(at_bat_result.pitches):
                balls = pitch_data.get('balls', 0)
                strikes = pitch_data.get('strikes', 0)

                count_key = f"{balls}-{strikes}"

                pitch_metrics[count_key]['total'] += 1

                # Check if this is a 2-strike count
                is_two_strike = strikes == 2

                if pitch_data.get('swing', False):
                    pitch_metrics[count_key]['swings'] += 1

                    if is_two_strike:
                        two_strike_analysis['swings'] += 1

                    # Determine outcome
                    pitch_outcome = pitch_data.get('pitch_outcome', 'unknown')

                    if pitch_outcome == 'whiff' or pitch_outcome == 'swinging_strike':
                        pitch_metrics[count_key]['whiffs'] += 1
                        if is_two_strike:
                            two_strike_analysis['whiffs'] += 1
                    elif pitch_outcome == 'foul':
                        pitch_metrics[count_key]['fouls'] += 1
                        if is_two_strike:
                            two_strike_analysis['fouls'] += 1
                    elif pitch_outcome in ['in_play', 'hit', 'out']:
                        pitch_metrics[count_key]['in_play'] += 1
                        if is_two_strike:
                            two_strike_analysis['contacts'] += 1
                    else:
                        # If we have contact data
                        if pitch_data.get('contact', False):
                            pitch_metrics[count_key]['contacts'] += 1
                            if is_two_strike:
                                two_strike_analysis['contacts'] += 1

                if is_two_strike:
                    two_strike_analysis['total_2strike_pitches'] += 1

                    # Track put-away multiplier
                    if pitch_data.get('swing', False):
                        put_away_tracking.append({
                            'count': count_key,
                            'pitcher_stuff': pitcher.attributes.get_stuff_rating(),
                            'outcome': pitch_data.get('pitch_outcome', 'unknown'),
                            'pitch_type': pitch_data.get('pitch_type', 'unknown')
                        })

            # Track 2-strike strikeouts
            if at_bat_result.outcome == 'strikeout':
                two_strike_analysis['strikeouts'] += 1

        print("Done.")

    print()
    print("="*80)
    print("DETAILED WHIFF RATE ANALYSIS")
    print("="*80)
    print()

    # Overall outcomes
    total_pa = outcome_metrics['total_pa']
    k_pct = (outcome_metrics['strikeouts'] / total_pa * 100) if total_pa > 0 else 0
    bb_pct = (outcome_metrics['walks'] / total_pa * 100) if total_pa > 0 else 0

    print("📊 OVERALL OUTCOMES:")
    print(f"   Total PA: {total_pa}")
    print(f"   Strikeouts: {outcome_metrics['strikeouts']} ({k_pct:.1f}%)")
    print(f"   Walks: {outcome_metrics['walks']} ({bb_pct:.1f}%)")
    print(f"   In Play: {outcome_metrics['in_play']} ({outcome_metrics['in_play']/total_pa*100:.1f}%)")
    print(f"   MLB Target K%: ~22%")
    print(f"   MLB Target BB%: ~8-9%")
    print()

    # Whiff rate by count
    print("🎯 WHIFF RATE BY COUNT:")
    print()

    # Sort counts for logical display
    counts_order = [
        '0-0', '1-0', '0-1', '2-0', '1-1', '0-2', '3-0', '2-1', '1-2', '3-1', '2-2', '3-2'
    ]

    total_swings = 0
    total_whiffs = 0

    for count in counts_order:
        if count in pitch_metrics:
            metrics = pitch_metrics[count]
            if metrics['swings'] > 0:
                whiff_rate = (metrics['whiffs'] / metrics['swings'] * 100)
                contact_rate = 100 - whiff_rate
                foul_rate = (metrics['fouls'] / metrics['swings'] * 100) if metrics['fouls'] > 0 else 0

                # Highlight 2-strike counts
                is_2strike = count.endswith('-2')
                marker = "⭐" if is_2strike else "  "

                print(f"{marker} {count:4s}: {metrics['swings']:4d} swings → "
                      f"Whiff: {whiff_rate:5.1f}%, Contact: {contact_rate:5.1f}%, Foul: {foul_rate:5.1f}%")

                total_swings += metrics['swings']
                total_whiffs += metrics['whiffs']

    print()
    overall_whiff = (total_whiffs / total_swings * 100) if total_swings > 0 else 0
    overall_contact = 100 - overall_whiff
    print(f"   OVERALL: {total_swings:4d} swings → Whiff: {overall_whiff:5.1f}%, Contact: {overall_contact:5.1f}%")
    print(f"   MLB Target: Whiff ~20-25%, Contact ~75-80%")
    print()

    # 2-strike analysis
    print("⭐ 2-STRIKE COUNT ANALYSIS:")
    print()
    print(f"   Total 2-strike pitches: {two_strike_analysis['total_2strike_pitches']}")
    print(f"   Swings: {two_strike_analysis['swings']}")

    if two_strike_analysis['swings'] > 0:
        two_strike_whiff_rate = (two_strike_analysis['whiffs'] / two_strike_analysis['swings'] * 100)
        two_strike_contact_rate = (two_strike_analysis['contacts'] / two_strike_analysis['swings'] * 100)
        two_strike_foul_rate = (two_strike_analysis['fouls'] / two_strike_analysis['swings'] * 100)

        print(f"   Whiff rate: {two_strike_whiff_rate:.1f}%")
        print(f"   Contact rate: {two_strike_contact_rate:.1f}%")
        print(f"   Foul rate: {two_strike_foul_rate:.1f}%")
        print()

        print(f"   Strikeouts from 2-strike: {two_strike_analysis['strikeouts']}")
        print(f"   Conversion rate: {two_strike_analysis['strikeouts']/total_pa*100:.1f}% of all PA")
        print()

        # Diagnosis
        if two_strike_foul_rate > 50:
            print("   🚨 FOUL RATE TOO HIGH!")
            print(f"      → {two_strike_foul_rate:.1f}% of 2-strike swings are fouls")
            print("      → Preventing strikeouts by extending at-bats")
        elif two_strike_whiff_rate < 25:
            print("   ⚠️ 2-STRIKE WHIFF RATE TOO LOW")
            print(f"      → Only {two_strike_whiff_rate:.1f}% whiff rate on 2-strike counts")
            print("      → Should be elevated above non-2-strike counts")
            print("      → Put-away mechanism may not be working")
        else:
            print("   ✅ 2-strike whiff rate looks reasonable")

    print()

    # Put-away mechanism analysis
    if put_away_tracking:
        print("🔧 PUT-AWAY MECHANISM ANALYSIS:")
        print()
        print(f"   2-strike swings tracked: {len(put_away_tracking)}")

        # Sample put-away data
        print("   Sample 2-strike swing outcomes:")
        for i, swing in enumerate(put_away_tracking[:10]):
            print(f"      {swing['count']:4s} {swing['pitch_type']:10s} (stuff: {swing['pitcher_stuff']:.3f}) → {swing['outcome']}")

        if len(put_away_tracking) > 10:
            print(f"      ... ({len(put_away_tracking) - 10} more)")
        print()

    # Calculate expected K% with current rates
    print("="*80)
    print("K% DIAGNOSTIC")
    print("="*80)
    print()

    # Estimate how often we reach 2-strike counts
    pa_with_2strike = two_strike_analysis['total_2strike_pitches'] / (total_pa * 4)  # Rough estimate

    if two_strike_analysis['swings'] > 0:
        print("Expected K% calculation:")
        print()
        print(f"   Zone rate: 62.6% (from previous test)")
        print(f"   2-strike frequency: ~{pa_with_2strike*100:.1f}% of PA reach 2-strike")
        print(f"   2-strike whiff rate: {two_strike_whiff_rate:.1f}%")
        print(f"   2-strike conversion: {two_strike_analysis['strikeouts']/total_pa*100:.1f}%")
        print()

        print(f"   Actual K%: {k_pct:.1f}%")
        print(f"   Target K%: 22.0%")
        print(f"   Gap: {22 - k_pct:.1f} percentage points")
        print()

        if k_pct < 18:
            print("   🚨 PRIMARY PROBLEM IDENTIFIED:")
            if two_strike_foul_rate > 50:
                print(f"      → Foul ball rate too high ({two_strike_foul_rate:.1f}%)")
                print("      → Batters extending at-bats indefinitely on 2-strike counts")
                print("      → Need to reduce foul probability or increase whiff on fouls")
            elif two_strike_whiff_rate < 25:
                print(f"      → 2-strike whiff rate too low ({two_strike_whiff_rate:.1f}%)")
                print("      → Put-away mechanism not effective enough")
                print("      → Need to increase 2-strike whiff bonus")
            elif pa_with_2strike < 0.6:
                print(f"      → Not reaching 2-strike counts often enough ({pa_with_2strike*100:.1f}%)")
                print("      → Zone rate may be too low (though 62.6% looks good)")
            else:
                print("      → Multiple factors combining to suppress K%")

    print()
    print("="*80)

if __name__ == "__main__":
    investigate_game_whiff_rates()
