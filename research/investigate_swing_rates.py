"""
Investigate swing rates by count and situation

Focus: Why are batters so aggressive early in counts?
- 64.4% swing rate on 0-0 (MLB typical: 45-50%)
- 46% of PA end on first pitch contact
- Only 9.6% of PA reach 2-strike counts

This diagnostic will show:
1. Swing rate by count (in-zone vs out-of-zone)
2. MLB typical swing rates for comparison
3. Discipline factor effectiveness
4. Where the aggression problem is worst
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from batted_ball import create_test_team
from batted_ball.at_bat import AtBatSimulator
from collections import defaultdict

def investigate_swing_rates():
    """Analyze swing rates by count and zone"""

    print("="*80)
    print("SWING RATE INVESTIGATION BY COUNT")
    print("="*80)
    print()

    # Create teams
    away_team = create_test_team("Visitors", "average")
    home_team = create_test_team("Home", "average")

    print("Simulating 10 games (500 PA) with swing rate tracking...")
    print()

    # Track swing decisions by count
    swing_data = defaultdict(lambda: {
        'total_pitches': 0,
        'in_zone': 0,
        'out_zone': 0,
        'in_zone_swings': 0,
        'out_zone_swings': 0,
        'total_swings': 0
    })

    # Track hitter discipline distribution
    discipline_ratings = []

    # Track first-pitch outcomes specifically
    first_pitch_outcomes = {
        'total': 0,
        'ball': 0,
        'called_strike': 0,
        'swing': 0,
        'swing_miss': 0,
        'foul': 0,
        'in_play': 0
    }

    # Track PA progression
    pa_progression = {
        'total_pa': 0,
        'reached_1_pitch': 0,
        'reached_2_pitch': 0,
        'reached_3_pitch': 0,
        'reached_4_pitch': 0,
        'reached_5_pitch': 0,
        'reached_6_pitch': 0,
        'reached_2strike': 0
    }

    # Simulate games
    for game_num in range(1, 11):
        for ab_num in range(50):
            # Alternate teams
            if ab_num % 2 == 0:
                pitcher = away_team.get_current_pitcher()
                hitter = home_team.get_next_batter()
            else:
                pitcher = home_team.get_current_pitcher()
                hitter = away_team.get_next_batter()

            # Track discipline (zone discernment)
            discipline_ratings.append(hitter.attributes.ZONE_DISCERNMENT)

            at_bat_sim = AtBatSimulator(pitcher=pitcher, hitter=hitter)
            at_bat_result = at_bat_sim.simulate_at_bat()

            pa_progression['total_pa'] += 1
            num_pitches = len(at_bat_result.pitches)

            # Track PA length
            if num_pitches >= 1:
                pa_progression['reached_1_pitch'] += 1
            if num_pitches >= 2:
                pa_progression['reached_2_pitch'] += 1
            if num_pitches >= 3:
                pa_progression['reached_3_pitch'] += 1
            if num_pitches >= 4:
                pa_progression['reached_4_pitch'] += 1
            if num_pitches >= 5:
                pa_progression['reached_5_pitch'] += 1
            if num_pitches >= 6:
                pa_progression['reached_6_pitch'] += 1

            # Check if reached 2 strikes
            for pitch_data in at_bat_result.pitches:
                strikes = pitch_data.get('strikes', 0)
                if strikes == 2:
                    pa_progression['reached_2strike'] += 1
                    break

            # Analyze each pitch
            for pitch_idx, pitch_data in enumerate(at_bat_result.pitches):
                balls = pitch_data.get('balls', 0)
                strikes = pitch_data.get('strikes', 0)
                count_key = f"{balls}-{strikes}"

                is_in_zone = pitch_data.get('is_strike', False)
                did_swing = pitch_data.get('swing', False)

                swing_data[count_key]['total_pitches'] += 1

                if is_in_zone:
                    swing_data[count_key]['in_zone'] += 1
                    if did_swing:
                        swing_data[count_key]['in_zone_swings'] += 1
                else:
                    swing_data[count_key]['out_zone'] += 1
                    if did_swing:
                        swing_data[count_key]['out_zone_swings'] += 1

                if did_swing:
                    swing_data[count_key]['total_swings'] += 1

                # First pitch tracking
                if pitch_idx == 0:
                    first_pitch_outcomes['total'] += 1

                    if is_in_zone and not did_swing:
                        first_pitch_outcomes['called_strike'] += 1
                    elif not is_in_zone and not did_swing:
                        first_pitch_outcomes['ball'] += 1
                    elif did_swing:
                        first_pitch_outcomes['swing'] += 1

                        pitch_outcome = pitch_data.get('pitch_outcome', 'unknown')
                        if pitch_outcome in ['whiff', 'swinging_strike']:
                            first_pitch_outcomes['swing_miss'] += 1
                        elif pitch_outcome == 'foul':
                            first_pitch_outcomes['foul'] += 1
                        elif pitch_outcome in ['in_play', 'hit', 'out', 'ball_in_play']:
                            first_pitch_outcomes['in_play'] += 1

    print()
    print("="*80)
    print("SWING RATE ANALYSIS BY COUNT")
    print("="*80)
    print()

    # MLB typical swing rates for comparison
    mlb_typical = {
        '0-0': {'overall': 0.47, 'in_zone': 0.68, 'out_zone': 0.28},
        '1-0': {'overall': 0.42, 'in_zone': 0.63, 'out_zone': 0.24},
        '0-1': {'overall': 0.47, 'in_zone': 0.70, 'out_zone': 0.28},
        '2-0': {'overall': 0.38, 'in_zone': 0.60, 'out_zone': 0.20},
        '1-1': {'overall': 0.46, 'in_zone': 0.69, 'out_zone': 0.27},
        '0-2': {'overall': 0.55, 'in_zone': 0.78, 'out_zone': 0.38},
        '3-0': {'overall': 0.25, 'in_zone': 0.55, 'out_zone': 0.10},
        '2-1': {'overall': 0.45, 'in_zone': 0.68, 'out_zone': 0.26},
        '1-2': {'overall': 0.56, 'in_zone': 0.80, 'out_zone': 0.39},
        '3-1': {'overall': 0.35, 'in_zone': 0.65, 'out_zone': 0.15},
        '2-2': {'overall': 0.57, 'in_zone': 0.82, 'out_zone': 0.40},
        '3-2': {'overall': 0.60, 'in_zone': 0.85, 'out_zone': 0.42}
    }

    print("Format: Count | Overall Swing% | In-Zone Swing% | Out-Zone Swing% (Chase%)")
    print("        [MLB Typical] | Difference from MLB")
    print()

    # Sort counts
    counts_order = [
        '0-0', '1-0', '0-1', '2-0', '1-1', '0-2', '3-0', '2-1', '1-2', '3-1', '2-2', '3-2'
    ]

    problem_counts = []

    for count in counts_order:
        if count in swing_data:
            data = swing_data[count]

            # Calculate swing rates
            total_pitches = data['total_pitches']
            overall_swing_pct = (data['total_swings'] / total_pitches * 100) if total_pitches > 0 else 0

            in_zone_swing_pct = (data['in_zone_swings'] / data['in_zone'] * 100) if data['in_zone'] > 0 else 0
            out_zone_swing_pct = (data['out_zone_swings'] / data['out_zone'] * 100) if data['out_zone'] > 0 else 0

            # Get MLB typical
            mlb = mlb_typical.get(count, {'overall': 0.47, 'in_zone': 0.70, 'out_zone': 0.28})
            mlb_overall = mlb['overall'] * 100
            mlb_in_zone = mlb['in_zone'] * 100
            mlb_out_zone = mlb['out_zone'] * 100

            # Calculate differences
            diff_overall = overall_swing_pct - mlb_overall
            diff_in_zone = in_zone_swing_pct - mlb_in_zone
            diff_out_zone = out_zone_swing_pct - mlb_out_zone

            # Flag problem counts
            is_problem = False
            if count in ['0-0', '1-0', '0-1', '1-1'] and diff_overall > 10:
                is_problem = True
                problem_counts.append({
                    'count': count,
                    'diff_overall': diff_overall,
                    'diff_in_zone': diff_in_zone,
                    'diff_out_zone': diff_out_zone
                })

            marker = "🚨" if is_problem else "  "

            print(f"{marker} {count:4s}: Overall {overall_swing_pct:5.1f}% | In-Zone {in_zone_swing_pct:5.1f}% | Chase {out_zone_swing_pct:5.1f}%")
            print(f"        [MLB: {mlb_overall:5.1f}% | {mlb_in_zone:5.1f}% | {mlb_out_zone:5.1f}%]")
            print(f"        Diff: {diff_overall:+5.1f}pp | {diff_in_zone:+5.1f}pp | {diff_out_zone:+5.1f}pp")
            print()

    # First pitch analysis
    print("="*80)
    print("FIRST PITCH (0-0 COUNT) DETAILED ANALYSIS")
    print("="*80)
    print()

    fp_total = first_pitch_outcomes['total']
    if fp_total > 0:
        print(f"Total First Pitches: {fp_total}")
        print()
        print("Outcomes:")
        print(f"   Ball (no swing):        {first_pitch_outcomes['ball']:3d} ({first_pitch_outcomes['ball']/fp_total*100:5.1f}%)")
        print(f"   Called Strike:          {first_pitch_outcomes['called_strike']:3d} ({first_pitch_outcomes['called_strike']/fp_total*100:5.1f}%)")
        print(f"   Swing:                  {first_pitch_outcomes['swing']:3d} ({first_pitch_outcomes['swing']/fp_total*100:5.1f}%)")
        print()

        if first_pitch_outcomes['swing'] > 0:
            swing_total = first_pitch_outcomes['swing']
            print("Swing Outcomes:")
            print(f"   Whiff:                  {first_pitch_outcomes['swing_miss']:3d} ({first_pitch_outcomes['swing_miss']/swing_total*100:5.1f}%)")
            print(f"   Foul:                   {first_pitch_outcomes['foul']:3d} ({first_pitch_outcomes['foul']/swing_total*100:5.1f}%)")
            print(f"   In Play:                {first_pitch_outcomes['in_play']:3d} ({first_pitch_outcomes['in_play']/swing_total*100:5.1f}%)")
            print()

            in_play_pct_of_pa = first_pitch_outcomes['in_play'] / fp_total * 100
            print(f"   🚨 First Pitch Balls in Play: {in_play_pct_of_pa:.1f}% of all PA")
            print(f"      MLB Typical: ~15-20%")
            print(f"      Difference: +{in_play_pct_of_pa - 17.5:.1f}pp")
            print()

    # PA progression analysis
    print("="*80)
    print("PLATE APPEARANCE LENGTH ANALYSIS")
    print("="*80)
    print()

    total_pa = pa_progression['total_pa']
    print(f"Total PA: {total_pa}")
    print()
    print("PA Reaching Each Length:")
    print(f"   1+ pitch:  {pa_progression['reached_1_pitch']:3d} ({pa_progression['reached_1_pitch']/total_pa*100:5.1f}%)")
    print(f"   2+ pitches: {pa_progression['reached_2_pitch']:3d} ({pa_progression['reached_2_pitch']/total_pa*100:5.1f}%) [MLB: ~80%]")
    print(f"   3+ pitches: {pa_progression['reached_3_pitch']:3d} ({pa_progression['reached_3_pitch']/total_pa*100:5.1f}%) [MLB: ~60%]")
    print(f"   4+ pitches: {pa_progression['reached_4_pitch']:3d} ({pa_progression['reached_4_pitch']/total_pa*100:5.1f}%) [MLB: ~45%]")
    print(f"   5+ pitches: {pa_progression['reached_5_pitch']:3d} ({pa_progression['reached_5_pitch']/total_pa*100:5.1f}%) [MLB: ~30%]")
    print(f"   6+ pitches: {pa_progression['reached_6_pitch']:3d} ({pa_progression['reached_6_pitch']/total_pa*100:5.1f}%) [MLB: ~20%]")
    print()

    two_strike_pct = pa_progression['reached_2strike'] / total_pa * 100
    print(f"   ⭐ Reached 2 Strikes: {pa_progression['reached_2strike']:3d} ({two_strike_pct:5.1f}%)")
    print(f"      MLB Typical: 50-65%")
    print(f"      Gap: {two_strike_pct - 57.5:.1f}pp from MLB average (57.5%)")
    print()

    # Hitter discipline analysis
    print("="*80)
    print("HITTER ZONE DISCERNMENT DISTRIBUTION")
    print("="*80)
    print()

    avg_discipline = sum(discipline_ratings) / len(discipline_ratings)
    min_discipline = min(discipline_ratings)
    max_discipline = max(discipline_ratings)

    print(f"Hitters sampled: {len(discipline_ratings)}")
    print(f"Average ZONE_DISCERNMENT: {avg_discipline:,.0f}")
    print(f"Range: {min_discipline:,.0f} - {max_discipline:,.0f}")
    print()

    # Discipline buckets
    buckets = {
        'Poor (0-30k)': 0,
        'Below Avg (30-45k)': 0,
        'Average (45-55k)': 0,
        'Above Avg (55-70k)': 0,
        'Elite (70-100k)': 0
    }

    for disc in discipline_ratings:
        if disc < 30000:
            buckets['Poor (0-30k)'] += 1
        elif disc < 45000:
            buckets['Below Avg (30-45k)'] += 1
        elif disc < 55000:
            buckets['Average (45-55k)'] += 1
        elif disc < 70000:
            buckets['Above Avg (55-70k)'] += 1
        else:
            buckets['Elite (70-100k)'] += 1

    print("Zone Discernment Distribution:")
    for bucket_name, count in buckets.items():
        pct = count / len(discipline_ratings) * 100
        print(f"   {bucket_name:25s}: {count:3d} ({pct:5.1f}%)")
    print()

    # Summary and diagnosis
    print("="*80)
    print("DIAGNOSIS")
    print("="*80)
    print()

    if problem_counts:
        print("🚨 EARLY-COUNT AGGRESSION PROBLEMS:")
        print()
        for problem in problem_counts:
            print(f"   {problem['count']:4s}: {problem['diff_overall']:+.1f}pp too aggressive overall")
            if problem['diff_in_zone'] > 5:
                print(f"         → {problem['diff_in_zone']:+.1f}pp too aggressive in-zone")
            if problem['diff_out_zone'] > 5:
                print(f"         → {problem['diff_out_zone']:+.1f}pp too much chasing")
        print()

    # Identify primary fix
    print("PRIMARY FIX NEEDED:")
    print()

    # Check 0-0 specifically
    zero_zero_data = swing_data.get('0-0', {})
    if zero_zero_data.get('total_pitches', 0) > 0:
        zero_zero_swing = zero_zero_data['total_swings'] / zero_zero_data['total_pitches'] * 100
        zero_zero_in_zone = (zero_zero_data['in_zone_swings'] / zero_zero_data['in_zone'] * 100) if zero_zero_data['in_zone'] > 0 else 0

        if zero_zero_swing > 55:
            print(f"1. Reduce 0-0 overall swing rate: {zero_zero_swing:.1f}% → ~47%")
            print(f"   Need: -{zero_zero_swing - 47:.1f} percentage points")
            print()

        if zero_zero_in_zone > 75:
            print(f"2. Reduce 0-0 in-zone aggression: {zero_zero_in_zone:.1f}% → ~68%")
            print(f"   Need: -{zero_zero_in_zone - 68:.1f} percentage points")
            print()

    print("3. This will increase PA length and 2-strike frequency")
    print(f"   Current 2-strike freq: {two_strike_pct:.1f}%")
    print(f"   Target: 55-60%")
    print(f"   Increase needed: +{55 - two_strike_pct:.1f}pp")
    print()

    print("RECOMMENDED ACTION:")
    print("   Increase discipline multiplier effect on early counts (0-0, 1-0, 0-1)")
    print("   This will make batters more patient and let counts develop")
    print()

    print("="*80)

if __name__ == "__main__":
    investigate_swing_rates()
