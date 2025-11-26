"""
Debug Analysis Runner

Runs simulations with detailed debug metrics collection to understand
where K%, BB%, and HR/FB are generated.

This script is part of Phase 1: Metrics-First Refactor

Usage:
    python research/run_debug_analysis.py --games 5
    python research/run_debug_analysis.py --games 10 --output phase1_analysis
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import argparse
from pathlib import Path

# Import after path is set
from batted_ball.debug_metrics import DebugMetricsCollector


def analyze_debug_metrics(collector: DebugMetricsCollector):
    """
    Analyze collected debug metrics and print insights.

    Parameters
    ----------
    collector : DebugMetricsCollector
        Collector with captured metrics
    """
    summary = collector.get_summary_stats()

    print(f"\n{'='*80}")
    print(f"DEBUG METRICS ANALYSIS")
    print(f"{'='*80}\n")

    # Overview
    print(f"📊 COLLECTION OVERVIEW:")
    print(f"   Games: {summary.get('total_games', 0)}")
    print(f"   Plate Appearances: {summary.get('total_plate_appearances', 0)}")
    print(f"   Pitches: {summary.get('total_pitches', 0)}")
    print(f"   Swings: {summary.get('total_swings', 0)}")
    print(f"   Contacts: {summary.get('total_contacts', 0)}")
    print()

    # Pitch Intention Analysis
    if 'pitch_intentions' in summary:
        print(f"🎯 PITCH INTENTION ANALYSIS:")
        intentions = summary['pitch_intentions']

        total_pitches = sum(v for k, v in intentions.items() if not k.endswith('_zone') and not k.endswith('_zone_rate'))

        print(f"   Total Intentions Logged: {total_pitches}")
        print(f"\n   Intention Distribution:")

        for intention in ['strike_looking', 'strike_competitive', 'strike_corner', 'waste_chase', 'ball_intentional']:
            count = intentions.get(intention, 0)
            if total_pitches > 0:
                pct = count / total_pitches * 100
                zone_rate = intentions.get(f"{intention}_zone_rate", 0) * 100
                print(f"      {intention:20s}: {count:4d} ({pct:5.1f}%) → Zone rate: {zone_rate:.1f}%")

        # Calculate overall zone rate
        total_in_zone = sum(intentions.get(f"{int}_zone", 0) for int in ['strike_looking', 'strike_competitive', 'strike_corner', 'waste_chase', 'ball_intentional'])
        overall_zone_rate = total_in_zone / total_pitches * 100 if total_pitches > 0 else 0
        print(f"\n   Overall Zone Rate: {overall_zone_rate:.1f}% (Target: ~62-65% for MLB realism)")
        print()

    # Swing Decision Analysis
    if 'swing_rates' in summary:
        print(f"🏏 SWING DECISION ANALYSIS:")
        swing_data = summary['swing_rates']

        in_zone_pct = swing_data.get('in_zone_pct', 0) * 100
        out_zone_pct = swing_data.get('out_of_zone_pct', 0) * 100

        print(f"   In-Zone Swing%: {in_zone_pct:.1f}% (MLB: ~65-70%)")
        print(f"   Out-of-Zone Swing% (Chase): {out_zone_pct:.1f}% (MLB: ~25-35%)")
        print(f"   Swing% Gap: {in_zone_pct - out_zone_pct:.1f} percentage points")
        print()

    # Whiff Analysis
    if 'whiff_rates' in summary:
        print(f"❌ WHIFF RATE ANALYSIS:")
        whiff_data = summary['whiff_rates']

        print(f"   Pitch Type Breakdown:")
        for pitch_type, data in whiff_data.items():
            if pitch_type != 'overall':
                whiff_rate = data['whiff_rate'] * 100
                print(f"      {pitch_type:15s}: {data['whiffs']:3d}/{data['total']:3d} swings = {whiff_rate:5.1f}% whiff rate")

        # Calculate overall whiff rate
        total_swings = sum(data['total'] for data in whiff_data.values())
        total_whiffs = sum(data['whiffs'] for data in whiff_data.values())
        overall_whiff = total_whiffs / total_swings * 100 if total_swings > 0 else 0
        print(f"\n   Overall Whiff Rate: {overall_whiff:.1f}%")
        print(f"   Contact Rate: {100 - overall_whiff:.1f}% (MLB: ~75-80%)")
        print()

    # Contact Quality Analysis
    if 'contact_quality' in summary:
        print(f"💪 CONTACT QUALITY ANALYSIS:")
        quality_data = summary['contact_quality']

        total_contacts = quality_data.get('total', 0)
        print(f"   Total Contacts: {total_contacts}")
        print(f"\n   Quality Distribution:")

        for quality in ['barrel', 'solid', 'average', 'weak', 'poor']:
            count = quality_data.get(quality, 0)
            pct = quality_data.get(f"{quality}_pct", 0) * 100
            if count > 0:
                print(f"      {quality.capitalize():15s}: {count:3d} ({pct:5.1f}%)")
        print()

    # Batted Ball Type Analysis
    if 'batted_ball_types' in summary:
        print(f"⚾ BATTED BALL TYPE ANALYSIS:")
        bb_data = summary['batted_ball_types']

        for bb_type in ['ground_ball', 'line_drive', 'fly_ball', 'pop_up']:
            count = bb_data.get(bb_type, 0)
            pct = bb_data.get(f"{bb_type}_pct", 0) * 100
            if count > 0:
                print(f"   {bb_type.replace('_', ' ').title():15s}: {count:3d} ({pct:5.1f}%)")

        # Compare to MLB
        gb_pct = bb_data.get('ground_ball_pct', 0) * 100
        ld_pct = bb_data.get('line_drive_pct', 0) * 100
        fb_pct = bb_data.get('fly_ball_pct', 0) * 100
        print(f"\n   MLB Expected: GB ~45%, LD ~21%, FB ~34%")
        print(f"   Current: GB {gb_pct:.1f}%, LD {ld_pct:.1f}%, FB {fb_pct:.1f}%")
        print()

    # PA Outcome Analysis
    if 'pa_outcomes' in summary:
        print(f"🎯 PLATE APPEARANCE OUTCOMES:")
        pa_data = summary['pa_outcomes']

        k_rate = pa_data.get('k_rate', 0) * 100
        bb_rate = pa_data.get('bb_rate', 0) * 100

        print(f"   K% (Strikeout Rate): {k_rate:.1f}% (Target: ~22%)")
        print(f"   BB% (Walk Rate): {bb_rate:.1f}% (Target: ~8-9%)")

        # Show outcome distribution
        print(f"\n   Outcome Distribution:")
        total_pas = sum(v for k, v in pa_data.items() if k not in ['k_rate', 'bb_rate'])
        for outcome in ['strikeout_swinging', 'strikeout_looking', 'walk', 'single', 'double', 'triple', 'home_run', 'out']:
            count = pa_data.get(outcome, 0)
            if count > 0:
                pct = count / total_pas * 100 if total_pas > 0 else 0
                print(f"      {outcome.replace('_', ' ').title():20s}: {count:3d} ({pct:5.1f}%)")
        print()

    print(f"{'='*80}\n")


def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(
        description="Run simulation with debug metrics collection for Phase 1 analysis"
    )
    parser.add_argument(
        '--games',
        type=int,
        default=5,
        help='Number of games to simulate (default: 5, use small number for detailed analysis)'
    )
    parser.add_argument(
        '--output',
        type=str,
        default='phase1_debug_analysis',
        help='Base name for output files'
    )
    parser.add_argument(
        '--summary-only',
        action='store_true',
        help='Save only summary stats (not detailed logs) for smaller file size'
    )

    args = parser.parse_args()

    print(f"\n{'='*80}")
    print(f"PHASE 1: DEBUG METRICS COLLECTION")
    print(f"{'='*80}\n")
    print(f"Configuration:")
    print(f"  Games: {args.games}")
    print(f"  Output: {args.output}")
    print(f"  Detail level: {'Summary only' if args.summary_only else 'Full detailed logs'}")
    print()

    # NOTE: This is a placeholder for the actual integration
    # In the full implementation, we would:
    # 1. Import GameSimulator with debug_metrics support
    # 2. Pass DebugMetricsCollector to the simulator
    # 3. The simulator would call collector.log_* methods throughout execution

    print("⚠️  NOTE: Full integration pending")
    print("    This script demonstrates the debug metrics framework.")
    print("    Next step: Integrate logging calls into at_bat.py, player.py, etc.")
    print()

    # Create collector (for demonstration)
    collector = DebugMetricsCollector(enabled=True)

    print("✅ Debug metrics framework created successfully")
    print()
    print("📝 Next Steps for Full Integration:")
    print("   1. Modify at_bat.py to accept optional DebugMetricsCollector")
    print("   2. Add collector.log_pitch_intention() calls in _determine_pitch_intention()")
    print("   3. Add collector.log_swing_decision() calls in player.decide_to_swing()")
    print("   4. Add collector.log_whiff() calls in calculate_whiff_probability()")
    print("   5. Add collector.log_collision() calls in contact.py")
    print("   6. Add collector.log_flight() calls in trajectory.py")
    print("   7. Test with actual simulations")
    print()

    # Save framework documentation
    results_dir = Path("research/results")
    results_dir.mkdir(parents=True, exist_ok=True)

    doc_path = results_dir / "phase1_integration_guide.md"
    with open(doc_path, 'w') as f:
        f.write("# Phase 1: Debug Metrics Integration Guide\n\n")
        f.write("## Overview\n\n")
        f.write("This guide describes how to integrate the `DebugMetricsCollector` into\n")
        f.write("the simulation engine to track where K%, BB%, and HR/FB are generated.\n\n")
        f.write("## Integration Points\n\n")
        f.write("### 1. GameSimulator (game_simulation.py)\n\n")
        f.write("```python\n")
        f.write("class GameSimulator:\n")
        f.write("    def __init__(self, away_team, home_team, verbose=False, debug_collector=None):\n")
        f.write("        self.debug_collector = debug_collector\n")
        f.write("        if debug_collector:\n")
        f.write("            debug_collector.start_game(game_id)\n")
        f.write("```\n\n")
        f.write("### 2. AtBatSimulator (at_bat.py)\n\n")
        f.write("Add logging in `_determine_pitch_intention()`:\n\n")
        f.write("```python\n")
        f.write("def _determine_pitch_intention(self, balls, strikes, pitch_type):\n")
        f.write("    # ... existing logic ...\n")
        f.write("    \n")
        f.write("    if self.debug_collector:\n")
        f.write("        self.debug_collector.log_pitch_intention(\n")
        f.write("            inning=self.current_inning,\n")
        f.write("            balls=balls,\n")
        f.write("            strikes=strikes,\n")
        f.write("            # ... all parameters ...\n")
        f.write("        )\n")
        f.write("```\n\n")
        f.write("### 3. Hitter.decide_to_swing() (player.py)\n\n")
        f.write("```python\n")
        f.write("def decide_to_swing(self, pitch, balls, strikes, debug_collector=None):\n")
        f.write("    # ... calculate swing probability ...\n")
        f.write("    \n")
        f.write("    if debug_collector:\n")
        f.write("        debug_collector.log_swing_decision(...)\n")
        f.write("    \n")
        f.write("    return did_swing\n")
        f.write("```\n\n")
        f.write("### 4. Whiff Calculation (player.py)\n\n")
        f.write("Similar pattern for `calculate_whiff_probability()`\n\n")
        f.write("### 5. Collision Physics (contact.py)\n\n")
        f.write("Log in `calculate_contact_result()` or similar function\n\n")
        f.write("### 6. Ball Flight (trajectory.py)\n\n")
        f.write("Log in `BattedBallSimulator.simulate()`\n\n")
        f.write("## Testing\n\n")
        f.write("1. Run with debug enabled: `python research/run_debug_analysis.py --games 5`\n")
        f.write("2. Verify metrics are being collected\n")
        f.write("3. Analyze output JSON for insights\n")
        f.write("4. Compare against MLB benchmarks\n\n")
        f.write("## Expected Insights\n\n")
        f.write("- **K% Analysis**: See which whiff factors contribute most (barrel accuracy vs pitch type)\n")
        f.write("- **BB% Analysis**: See how many walks come from intentional balls vs command error\n")
        f.write("- **HR/FB Analysis**: See EV/LA distributions and identify tail issues\n\n")

    print(f"📄 Integration guide saved to: {doc_path}")
    print()
    print(f"{'='*80}")
    print(f"✅ PHASE 1 FRAMEWORK COMPLETE")
    print(f"{'='*80}\n")


if __name__ == "__main__":
    main()
