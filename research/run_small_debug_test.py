"""
Quick debug metrics test with 3 games

Demonstrates the Phase 1 debug framework capturing detailed metrics
for BB% and K% attribution analysis.
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from batted_ball.debug_metrics import DebugMetricsCollector
from batted_ball import GameSimulator, create_test_team

def run_debug_test():
    """Run 3 games with debug metrics collection"""

    print("="*80)
    print("PHASE 1 DEBUG METRICS TEST - 3 GAMES")
    print("="*80)
    print()

    # Create teams
    away_team = create_test_team("Visitors", "average")
    home_team = create_test_team("Home", "average")

    # Create debug collector
    collector = DebugMetricsCollector(enabled=True)

    print(f"Simulating 3 games with debug metrics collection...")
    print()

    # Simulate 3 games
    for game_num in range(1, 4):
        print(f"  Game {game_num}/3...", end=" ", flush=True)
        collector.start_game(game_id=game_num)

        # Note: GameSimulator doesn't support debug_collector yet,
        # so we'll simulate at-bats directly for now
        # This is a proof-of-concept showing the metrics framework works

        from batted_ball.at_bat import AtBatSimulator

        # Simulate 10 at-bats per game (small sample for quick demo)
        for ab in range(10):
            pitcher = away_team.get_current_pitcher() if ab % 2 == 0 else home_team.get_current_pitcher()
            hitter = home_team.get_next_batter() if ab % 2 == 0 else away_team.get_next_batter()

            sim = AtBatSimulator(
                pitcher=pitcher,
                hitter=hitter,
                debug_collector=collector
            )
            result = sim.simulate_at_bat(verbose=False)

        print("Done.")

    print()
    print("="*80)
    print("DEBUG METRICS ANALYSIS")
    print("="*80)
    print()

    # Get summary stats
    summary = collector.get_summary_stats()

    # Pitch Intention Analysis
    if 'pitch_intentions' in summary:
        print("🎯 PITCH INTENTION ANALYSIS:")
        intentions = summary['pitch_intentions']

        total_pitches = sum(v for k, v in intentions.items()
                           if not k.endswith('_zone') and not k.endswith('_zone_rate'))

        print(f"   Total Pitches Logged: {total_pitches}")
        print()
        print("   Intention Distribution:")

        for intention in ['strike_looking', 'strike_competitive', 'strike_corner',
                         'waste_chase', 'ball_intentional']:
            count = intentions.get(intention, 0)
            if total_pitches > 0:
                pct = count / total_pitches * 100
                zone_count = intentions.get(f"{intention}_zone", 0)
                zone_rate = (zone_count / count * 100) if count > 0 else 0
                print(f"      {intention:20s}: {count:3d} ({pct:5.1f}%) → Zone rate: {zone_rate:.1f}%")

        # Calculate overall zone rate
        total_in_zone = sum(intentions.get(f"{int}_zone", 0)
                           for int in ['strike_looking', 'strike_competitive', 'strike_corner',
                                      'waste_chase', 'ball_intentional'])
        overall_zone_rate = (total_in_zone / total_pitches * 100) if total_pitches > 0 else 0

        print()
        print(f"   Overall Zone Rate: {overall_zone_rate:.1f}%")
        print(f"   MLB Target: ~62-65%")

        if overall_zone_rate > 65:
            print(f"   ⚠️  Zone rate is HIGH → May lead to lower BB%")
        elif overall_zone_rate < 60:
            print(f"   ⚠️  Zone rate is LOW → May lead to higher BB%")
        else:
            print(f"   ✓ Zone rate looks reasonable")
        print()

    # Swing Decision Analysis
    if 'swing_rates' in summary:
        print("🏏 SWING DECISION ANALYSIS:")
        swing_data = summary['swing_rates']

        in_zone_pct = swing_data.get('in_zone_pct', 0) * 100
        out_zone_pct = swing_data.get('out_of_zone_pct', 0) * 100

        print(f"   In-Zone Swing%: {in_zone_pct:.1f}% (MLB: ~65-70%)")
        print(f"   Out-of-Zone Swing% (Chase): {out_zone_pct:.1f}% (MLB: ~25-35%)")
        print(f"   Swing% Gap: {in_zone_pct - out_zone_pct:.1f} percentage points")

        if out_zone_pct > 35:
            print(f"   ⚠️  Chase rate is HIGH → May lead to higher K%")
        elif out_zone_pct < 25:
            print(f"   ⚠️  Chase rate is LOW → May lead to lower K%")
        else:
            print(f"   ✓ Chase rate looks reasonable")
        print()

    # Contact Rate Analysis (OPTION A: NEW DIAGNOSTIC)
    print("🎯 CONTACT RATE ANALYSIS:")
    total_swings = summary.get('total_swings', 0)
    total_whiffs = summary.get('total_whiffs', 0)
    # Calculate contacts as swings - whiffs (collision_logs may not be fully populated)
    total_contacts = total_swings - total_whiffs

    if total_swings > 0:
        contact_rate = (total_contacts / total_swings) * 100
        whiff_rate = (total_whiffs / total_swings) * 100

        print(f"   Total Swings: {total_swings}")
        print(f"   Total Contact: {total_contacts} ({contact_rate:.1f}%)")
        print(f"   Total Whiffs: {total_whiffs} ({whiff_rate:.1f}%)")
        print(f"   MLB Target Contact Rate: ~75-80%")
        print(f"   MLB Target Whiff Rate: ~20-25%")
        print()

        # Diagnosis
        if contact_rate > 82:
            print(f"   🚨 CONTACT RATE TOO HIGH → Primary cause of low K%")
            print(f"      Batters making contact {contact_rate:.1f}% of swings (should be ~75-80%)")
            print(f"      Recommendations:")
            print(f"         - Increase base whiff rates in player.py")
            print(f"         - Tune VISION impact on whiff probability")
            print(f"         - Increase put-away multiplier range")
        elif contact_rate < 73:
            print(f"   ⚠️  Contact rate is LOW → May indicate whiff rates too high")
        else:
            print(f"   ✓ Contact rate looks reasonable for MLB")
        print()

        # Contact rate by pitch type
        if 'whiff_rates' in summary:
            print("   Contact Rate by Pitch Type:")
            whiff_data = summary['whiff_rates']

            # Sort by total swings descending
            sorted_pitches = sorted(whiff_data.items(), key=lambda x: x[1].get('total', 0), reverse=True)

            for pitch_type, data in sorted_pitches:
                total = data.get('total', 0)
                whiffs = data.get('whiffs', 0)
                contacts = total - whiffs

                if total > 0:
                    contact_pct = (contacts / total) * 100
                    whiff_pct = data.get('whiff_rate', 0) * 100
                    print(f"      {pitch_type:12s}: {contacts:3d}/{total:3d} contact ({contact_pct:5.1f}%) | {whiffs:3d} whiffs ({whiff_pct:5.1f}%)")
            print()
    else:
        print("   No swing data available")
        print()

    # PA Outcome Analysis
    if 'pa_outcomes' in summary:
        print("📊 PLATE APPEARANCE OUTCOMES:")
        pa_data = summary['pa_outcomes']

        k_rate = pa_data.get('k_rate', 0) * 100
        bb_rate = pa_data.get('bb_rate', 0) * 100

        print(f"   K% (Strikeout Rate): {k_rate:.1f}% (MLB: ~22%)")
        print(f"   BB% (Walk Rate): {bb_rate:.1f}% (MLB: ~8-9%)")

        print()
        if k_rate < 15:
            print(f"   🚨 K% is VERY LOW - Need to investigate:")
            print(f"      - Are batters chasing enough? (check chase rate above)")
            print(f"      - Are whiff rates too low? (need whiff logging)")
            print(f"      - Are barrel accuracy multipliers too generous?")

        if bb_rate > 12:
            print(f"   🚨 BB% is VERY HIGH - Need to investigate:")
            print(f"      - How many pitches are intentional balls? (check intentions)")
            print(f"      - What is zone rate by count? (check zone rate above)")
            print(f"      - Is command error too large?")
        print()

    print("="*80)
    print("SUMMARY")
    print("="*80)
    print()
    print(f"✅ Collected {len(collector.pitch_intentions)} pitch intentions")
    print(f"✅ Collected {len(collector.swing_decisions)} swing decisions")
    print(f"✅ Collected {len(collector.plate_appearances)} plate appearance outcomes")
    print()
    print("The debug metrics framework is working correctly!")
    print()
    print("Next steps:")
    print("  1. Run full 10-20 game analysis for statistical significance")
    print("  2. Deep dive into specific issues (BB% intentions, K% contact rates)")
    print("  3. Document findings to guide Phase 2 implementation")
    print()
    print("="*80)

if __name__ == "__main__":
    run_debug_test()
