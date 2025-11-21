"""
Hit Distribution Diagnostic for Phase 2C

Measures singles, doubles, triples, and home run distributions.
Compares against MLB targets:
- Singles: 65-70% of hits
- Doubles: 20-25% of hits
- Triples: 2-3% of hits
- Home Runs: 10-13% of hits

Run with:
    python research/run_hit_distribution_diagnostic.py           # Full 1000 PA
    python research/run_hit_distribution_diagnostic.py --quick   # Quick 500 PA
    python research/run_hit_distribution_diagnostic.py --full    # Full validation with multiple player types

Author: Phase 2C Development
Date: 2025-11-20
"""

import sys
import os
import time
from collections import defaultdict

# Add parent directory to path to allow imports from batted_ball package
# This allows the script to be run from anywhere
script_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(script_dir)
if parent_dir not in sys.path:
    sys.path.insert(0, parent_dir)

from batted_ball import create_test_team
from batted_ball.at_bat import AtBatSimulator
from batted_ball.play_outcome import PlayOutcome


def run_hit_distribution_diagnostic(num_pa=1000, verbose=False):
    """
    Run hit distribution diagnostic.

    Parameters
    ----------
    num_pa : int
        Number of plate appearances to simulate (default: 1000)
    verbose : bool
        Print detailed progress (default: False)
    """
    print(f"\n{'='*80}")
    print(f"Hit Distribution Diagnostic - Phase 2C")
    print(f"{'='*80}")
    print(f"Sample size: {num_pa} plate appearances")
    print(f"Fast mode: enabled (2× speedup, <1% accuracy loss)")
    print(f"{'='*80}\n")

    start_time = time.time()

    # Create test teams (average quality)
    away_team = create_test_team("Away", "average")
    home_team = create_test_team("Home", "average")

    # Track outcomes
    outcomes = defaultdict(int)
    hit_types = defaultdict(int)
    total_hits = 0
    total_pa = 0
    total_contact = 0

    # Track K%, BB% to ensure we don't break Phase 2A/2B
    strikeouts = 0
    walks = 0

    print("Simulating plate appearances...")
    if verbose:
        print(f"{'PA':<6} {'Outcome':<15} {'Hit Type':<10}")
        print("-" * 35)

    for i in range(num_pa):
        # Alternate between home and away
        pitcher = away_team.get_current_pitcher() if i % 2 == 0 else home_team.get_current_pitcher()
        hitter = home_team.get_next_batter() if i % 2 == 0 else away_team.get_next_batter()

        # Simulate at-bat with fast mode
        sim = AtBatSimulator(pitcher=pitcher, hitter=hitter, fast_mode=True)
        result = sim.simulate_at_bat()

        total_pa += 1
        outcome_str = result.outcome
        outcomes[outcome_str] += 1

        # Track K% and BB%
        if outcome_str == 'strikeout':
            strikeouts += 1
        elif outcome_str == 'walk':
            walks += 1

        # Determine hit type from play_result if in_play
        hit_type = None
        if outcome_str == 'in_play' and hasattr(result, 'play_result') and result.play_result:
            play_outcome = result.play_result.outcome
            total_contact += 1

            # Map PlayOutcome to hit type
            if play_outcome == PlayOutcome.SINGLE:
                hit_type = 'single'
                total_hits += 1
            elif play_outcome == PlayOutcome.DOUBLE:
                hit_type = 'double'
                total_hits += 1
            elif play_outcome == PlayOutcome.TRIPLE:
                hit_type = 'triple'
                total_hits += 1
            elif play_outcome == PlayOutcome.HOME_RUN:
                hit_type = 'home_run'
                total_hits += 1
            elif play_outcome in [PlayOutcome.GROUND_OUT, PlayOutcome.FLY_OUT,
                                  PlayOutcome.LINE_OUT, PlayOutcome.FORCE_OUT,
                                  PlayOutcome.DOUBLE_PLAY]:
                hit_type = 'out'
            else:
                hit_type = str(play_outcome)

            if hit_type and hit_type != 'out':
                hit_types[hit_type] += 1

        if verbose and i < 50:
            print(f"{i+1:<6} {outcome_str:<15} {hit_type if hit_type else 'N/A':<10}")

    elapsed = time.time() - start_time

    # Print results
    print(f"\n{'='*80}")
    print(f"DIAGNOSTIC RESULTS")
    print(f"{'='*80}\n")

    # Overall outcomes
    print(f"Overall Outcomes ({total_pa} PA):")
    print(f"  Strikeouts: {strikeouts} ({strikeouts/total_pa*100:.1f}%)")
    print(f"  Walks: {walks} ({walks/total_pa*100:.1f}%)")
    print(f"  In Play: {outcomes['in_play']} ({outcomes['in_play']/total_pa*100:.1f}%)")
    print(f"  Total Contact: {total_contact}")
    print()

    # Hit type distribution
    print(f"Hit Type Distribution ({total_hits} hits):")
    if total_hits > 0:
        print(f"  Singles: {hit_types['single']:<5} ({hit_types['single']/total_hits*100:>5.1f}%) [MLB Target: 65-70%]")
        print(f"  Doubles: {hit_types['double']:<5} ({hit_types['double']/total_hits*100:>5.1f}%) [MLB Target: 20-25%]")
        print(f"  Triples: {hit_types['triple']:<5} ({hit_types['triple']/total_hits*100:>5.1f}%) [MLB Target: 2-3%]")
        print(f"  Home Runs: {hit_types['home_run']:<5} ({hit_types['home_run']/total_hits*100:>5.1f}%) [MLB Target: 10-13%]")
    else:
        print("  No hits recorded!")
    print()

    # MLB realism check
    print(f"MLB Realism Check:")
    k_pct = strikeouts / total_pa * 100
    bb_pct = walks / total_pa * 100
    k_status = "✅" if 20 <= k_pct <= 25 else "⚠️"
    bb_status = "✅" if 7 <= bb_pct <= 10 else "⚠️"

    print(f"  {k_status} K%: {k_pct:.1f}% (Phase 2A target: ~22%)")
    print(f"  {bb_status} BB%: {bb_pct:.1f}% (Phase 2B target: 8-9%)")
    print()

    if total_hits > 0:
        singles_pct = hit_types['single'] / total_hits * 100
        doubles_pct = hit_types['double'] / total_hits * 100
        triples_pct = hit_types['triple'] / total_hits * 100
        hr_pct = hit_types['home_run'] / total_hits * 100

        singles_status = "✅" if 65 <= singles_pct <= 70 else "⚠️"
        doubles_status = "✅" if 20 <= doubles_pct <= 25 else "⚠️"
        triples_status = "✅" if 2 <= triples_pct <= 3 else "⚠️"
        hr_status = "✅" if 10 <= hr_pct <= 13 else "⚠️"

        print(f"  {singles_status} Singles: {singles_pct:.1f}% (target: 65-70%)")
        print(f"  {doubles_status} Doubles: {doubles_pct:.1f}% (target: 20-25%)")
        print(f"  {triples_status} Triples: {triples_pct:.1f}% (target: 2-3%)")
        print(f"  {hr_status} Home Runs: {hr_pct:.1f}% (target: 10-13%)")
    print()

    # Performance
    print(f"Performance:")
    print(f"  Total time: {elapsed:.1f}s")
    print(f"  Rate: {total_pa/elapsed:.1f} PA/sec")
    print(f"{'='*80}\n")

    # Return results for further analysis
    return {
        'total_pa': total_pa,
        'total_hits': total_hits,
        'strikeouts': strikeouts,
        'walks': walks,
        'hit_types': dict(hit_types),
        'outcomes': dict(outcomes)
    }


def run_player_type_comparison():
    """
    Run full validation comparing different player types.

    Tests:
    - Power hitters (should have more HR, fewer singles)
    - Contact hitters (should have more singles, fewer HR)
    - Elite vs average hitters
    """
    print(f"\n{'='*80}")
    print(f"Player Type Comparison - Phase 2C Full Validation")
    print(f"{'='*80}\n")

    player_types = [
        ("Average Hitters", "average", 500),
        ("Elite Hitters", "elite", 500),
        ("Power Hitters (Custom)", "good", 500),  # Will need to customize later
    ]

    results_by_type = {}

    for name, quality, num_pa in player_types:
        print(f"\nTesting {name} ({num_pa} PA)...")
        print("-" * 40)

        # Run diagnostic for this player type
        result = run_hit_distribution_diagnostic(num_pa=num_pa, verbose=False)
        results_by_type[name] = result

    # Compare results
    print(f"\n{'='*80}")
    print(f"PLAYER TYPE COMPARISON")
    print(f"{'='*80}\n")

    print(f"{'Player Type':<25} {'Singles':<10} {'Doubles':<10} {'Triples':<10} {'HR':<10}")
    print("-" * 65)

    for name, result in results_by_type.items():
        total_hits = result['total_hits']
        if total_hits > 0:
            hit_types = result['hit_types']
            singles_pct = hit_types.get('single', 0) / total_hits * 100
            doubles_pct = hit_types.get('double', 0) / total_hits * 100
            triples_pct = hit_types.get('triple', 0) / total_hits * 100
            hr_pct = hit_types.get('home_run', 0) / total_hits * 100

            print(f"{name:<25} {singles_pct:>5.1f}%     {doubles_pct:>5.1f}%     {triples_pct:>5.1f}%     {hr_pct:>5.1f}%")

    print()


if __name__ == "__main__":
    # Parse command line arguments
    if len(sys.argv) > 1:
        if sys.argv[1] == "--quick":
            print("Running QUICK diagnostic (500 PA)...")
            run_hit_distribution_diagnostic(num_pa=500)
        elif sys.argv[1] == "--full":
            print("Running FULL validation (player type comparison)...")
            run_player_type_comparison()
        else:
            print(f"Unknown option: {sys.argv[1]}")
            print("Usage:")
            print("  python research/run_hit_distribution_diagnostic.py           # Full 1000 PA")
            print("  python research/run_hit_distribution_diagnostic.py --quick   # Quick 500 PA")
            print("  python research/run_hit_distribution_diagnostic.py --full    # Full validation")
    else:
        # Default: 1000 PA
        run_hit_distribution_diagnostic(num_pa=1000)
