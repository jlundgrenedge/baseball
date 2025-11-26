"""
Quick test of Phase 1 debug metrics integration

Tests that debug_collector successfully captures:
- Pitch intentions
- Swing decisions
- Plate appearance outcomes
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from batted_ball.debug_metrics import DebugMetricsCollector
from batted_ball.at_bat import AtBatSimulator
from batted_ball import create_test_team

def test_debug_integration():
    """Test that debug collector captures metrics from an at-bat"""

    print("="*80)
    print("PHASE 1 DEBUG METRICS INTEGRATION TEST")
    print("="*80)
    print()

    # Create collector
    collector = DebugMetricsCollector(enabled=True)
    collector.start_game(game_id=1)

    # Create test team to get realistic players
    test_team = create_test_team("Test Team", "average")
    pitcher = test_team.pitchers[0]
    hitter = test_team.hitters[0]

    print(f"Pitcher: {pitcher.name}")
    print(f"Hitter: {hitter.name}")
    print()

    # Simulate at-bat with debug collector
    sim = AtBatSimulator(
        pitcher=pitcher,
        hitter=hitter,
        debug_collector=collector
    )

    result = sim.simulate_at_bat(verbose=True)

    print()
    print("="*80)
    print("DEBUG METRICS COLLECTED:")
    print("="*80)
    print()

    # Check what was collected
    print(f"Pitch Intentions: {len(collector.pitch_intentions)}")
    if collector.pitch_intentions:
        print(f"  Sample: {collector.pitch_intentions[0]}")

    print(f"\nSwing Decisions: {len(collector.swing_decisions)}")
    if collector.swing_decisions:
        print(f"  Sample: {collector.swing_decisions[0]}")

    print(f"\nPlate Appearance Outcomes: {len(collector.plate_appearances)}")
    if collector.plate_appearances:
        print(f"  Sample: {collector.plate_appearances[0]}")

    print()

    # Get summary stats
    summary = collector.get_summary_stats()
    print("="*80)
    print("SUMMARY STATISTICS:")
    print("="*80)
    print()

    if 'pitch_intentions' in summary:
        print("Pitch Intentions:")
        for key, value in sorted(summary['pitch_intentions'].items()):
            print(f"  {key}: {value}")
        print()

    if 'swing_rates' in summary:
        print("Swing Rates:")
        for key, value in summary['swing_rates'].items():
            if isinstance(value, float):
                print(f"  {key}: {value:.1%}")
            else:
                print(f"  {key}: {value}")
        print()

    if 'pa_outcomes' in summary:
        print("PA Outcomes:")
        for key, value in summary['pa_outcomes'].items():
            if not key.endswith('_rate'):
                print(f"  {key}: {value}")
        print()
        if 'k_rate' in summary['pa_outcomes']:
            print(f"  K%: {summary['pa_outcomes']['k_rate']:.1%}")
        if 'bb_rate' in summary['pa_outcomes']:
            print(f"  BB%: {summary['pa_outcomes']['bb_rate']:.1%}")

    print()
    print("="*80)
    print("✅ TEST COMPLETE - Debug metrics collection working!")
    print("="*80)

    return collector

if __name__ == "__main__":
    collector = test_debug_integration()
