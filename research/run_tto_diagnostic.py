"""
Three True Outcomes (TTO) Diagnostic for Phase 2C

Focuses on K%, BB%, and HR% - the outcomes independent of defense.
This is the correct focus for Phase 2C before tackling BABIP/fielding in later phases.

MLB Targets:
- K%: ~22% of PA
- BB%: ~8-9% of PA
- HR%: ~3-4% of PA (or ~10-13% of hits)

Run with:
    python research/run_tto_diagnostic.py           # Full 1000 PA
    python research/run_tto_diagnostic.py --quick   # Quick 500 PA

Author: Phase 2C Development (TTO Focus)
Date: 2025-11-20
"""

import sys
import os
import time
from collections import defaultdict

# Add parent directory to path to allow imports from batted_ball package
script_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(script_dir)
if parent_dir not in sys.path:
    sys.path.insert(0, parent_dir)

from batted_ball import create_test_team
from batted_ball.game_simulation import GameSimulator


def run_tto_diagnostic(num_games=10, verbose=False):
    """
    Run Three True Outcomes diagnostic using full game simulation.

    This ensures we get accurate HR data from play simulation.

    Parameters
    ----------
    num_games : int
        Number of games to simulate (default: 10 = ~500-600 PA)
    verbose : bool
        Print detailed progress (default: False)
    """
    print(f"\n{'='*80}")
    print(f"Three True Outcomes (TTO) Diagnostic - Phase 2C")
    print(f"{'='*80}")
    print(f"Sample size: {num_games} games (~{num_games * 50} PA expected)")
    print(f"Focus: K%, BB%, HR% (defense-independent outcomes)")
    print(f"{'='*80}\n")

    start_time = time.time()

    # Create test teams (average quality)
    away_team = create_test_team("Away", "average")
    home_team = create_test_team("Home", "average")

    # Track three true outcomes across all games
    total_strikeouts = 0
    total_walks = 0
    total_home_runs = 0
    total_pa = 0
    total_hits = 0
    total_in_play = 0

    print(f"Simulating {num_games} games...")
    if verbose:
        print(f"{'Game':<6} {'PA':<6} {'K':<6} {'BB':<6} {'HR':<6}")
        print("-" * 35)

    for game_num in range(num_games):
        # Simulate full game
        sim = GameSimulator(away_team, home_team, verbose=False)
        result = sim.simulate_game(num_innings=9)

        # Extract stats from game state
        game_state = sim.game_state

        # Track outcomes
        game_k = game_state.away_strikeouts + game_state.home_strikeouts
        game_bb = game_state.away_walks + game_state.home_walks
        game_hr = game_state.away_home_runs + game_state.home_home_runs
        game_hits = game_state.away_hits + game_state.home_hits

        # Calculate PA from game (K + BB + ABs)
        game_ab = game_state.away_at_bats + game_state.home_at_bats
        game_pa = game_k + game_bb + game_ab

        total_strikeouts += game_k
        total_walks += game_bb
        total_home_runs += game_hr
        total_hits += game_hits
        total_pa += game_pa

        if verbose:
            print(f"{game_num+1:<6} {game_pa:<6} {game_k:<6} {game_bb:<6} {game_hr:<6}")

    elapsed = time.time() - start_time

    # Calculate percentages
    k_pct = (total_strikeouts / total_pa * 100) if total_pa > 0 else 0
    bb_pct = (total_walks / total_pa * 100) if total_pa > 0 else 0
    hr_pct = (total_home_runs / total_pa * 100) if total_pa > 0 else 0
    hr_per_hit_pct = (total_home_runs / total_hits * 100) if total_hits > 0 else 0

    # Print results
    print(f"\n{'='*80}")
    print(f"THREE TRUE OUTCOMES RESULTS")
    print(f"{'='*80}\n")

    print(f"Sample Statistics:")
    print(f"  Total games: {num_games}")
    print(f"  Total PA: {total_pa}")
    print(f"  Total hits: {total_hits}")
    print(f"  Avg PA per game: {total_pa/num_games:.1f}")
    print()

    print(f"Three True Outcomes:")
    print(f"  Strikeouts: {total_strikeouts} ({k_pct:.1f}% of PA)")
    print(f"  Walks: {total_walks} ({bb_pct:.1f}% of PA)")
    print(f"  Home Runs: {total_home_runs} ({hr_pct:.1f}% of PA, {hr_per_hit_pct:.1f}% of hits)")
    print()

    # MLB realism check
    print(f"MLB Realism Check:")

    # K% check (target: 22%)
    k_status = "✅" if 20 <= k_pct <= 25 else "⚠️"
    print(f"  {k_status} K%: {k_pct:.1f}% (Phase 2A target: ~22%)")

    # BB% check (target: 8-9%)
    bb_status = "✅" if 7 <= bb_pct <= 10 else "⚠️"
    print(f"  {bb_status} BB%: {bb_pct:.1f}% (Phase 2B target: 8-9%)")

    # HR% check (target: 3-4% of PA, or 10-13% of hits)
    hr_pa_status = "✅" if 2.5 <= hr_pct <= 4.5 else "⚠️"
    hr_hit_status = "✅" if 10 <= hr_per_hit_pct <= 13 else "⚠️"
    print(f"  {hr_pa_status} HR% (PA): {hr_pct:.1f}% (MLB target: 3-4% of PA)")
    print(f"  {hr_hit_status} HR% (Hits): {hr_per_hit_pct:.1f}% (MLB target: 10-13% of hits)")
    print()

    # Performance
    print(f"Performance:")
    print(f"  Total time: {elapsed:.1f}s")
    print(f"  Rate: {num_games/elapsed:.2f} games/sec ({total_pa/elapsed:.1f} PA/sec)")
    print(f"{'='*80}\n")

    # Summary assessment
    print(f"Phase 2C Assessment:")
    if k_status == "✅" and bb_status == "✅" and hr_pa_status == "✅":
        print(f"  ✅ ALL THREE TRUE OUTCOMES IN TARGET RANGE!")
        print(f"  Phase 2C COMPLETE - Ready for Phase 2D (BABIP calibration)")
    else:
        print(f"  ⚠️ Tuning needed:")
        if k_status != "✅":
            print(f"     - K% is {k_pct:.1f}% (target: ~22%)")
        if bb_status != "✅":
            print(f"     - BB% is {bb_pct:.1f}% (target: 8-9%)")
        if hr_pa_status != "✅":
            print(f"     - HR% is {hr_pct:.1f}% (target: 3-4% of PA)")
    print()

    # Return results for further analysis
    return {
        'total_pa': total_pa,
        'total_hits': total_hits,
        'strikeouts': total_strikeouts,
        'walks': total_walks,
        'home_runs': total_home_runs,
        'k_pct': k_pct,
        'bb_pct': bb_pct,
        'hr_pct': hr_pct,
        'hr_per_hit_pct': hr_per_hit_pct
    }


def run_player_comparison():
    """
    Compare TTO across different player quality levels.

    Elite hitters should have:
    - Lower K%
    - Higher BB%
    - Higher HR%
    """
    print(f"\n{'='*80}")
    print(f"Player Quality Comparison - Three True Outcomes")
    print(f"{'='*80}\n")

    qualities = [
        ("Elite vs Elite", "elite", "elite", 5),
        ("Average vs Average", "average", "average", 5),
        ("Poor vs Poor", "poor", "poor", 5),
    ]

    results_by_quality = {}

    for name, away_quality, home_quality, num_games in qualities:
        print(f"Testing {name} ({num_games} games)...")
        print("-" * 40)

        away_team = create_test_team("Away", away_quality)
        home_team = create_test_team("Home", home_quality)

        total_k = 0
        total_bb = 0
        total_hr = 0
        total_pa = 0
        total_hits = 0

        for _ in range(num_games):
            sim = GameSimulator(away_team, home_team, verbose=False)
            result = sim.simulate_game(num_innings=9)

            game_state = sim.game_state
            game_k = game_state.away_strikeouts + game_state.home_strikeouts
            game_bb = game_state.away_walks + game_state.home_walks
            game_hr = game_state.away_home_runs + game_state.home_home_runs
            game_hits = game_state.away_hits + game_state.home_hits
            game_ab = game_state.away_at_bats + game_state.home_at_bats
            game_pa = game_k + game_bb + game_ab

            total_k += game_k
            total_bb += game_bb
            total_hr += game_hr
            total_hits += game_hits
            total_pa += game_pa

        k_pct = (total_k / total_pa * 100) if total_pa > 0 else 0
        bb_pct = (total_bb / total_pa * 100) if total_pa > 0 else 0
        hr_pct = (total_hr / total_pa * 100) if total_pa > 0 else 0

        results_by_quality[name] = {
            'k_pct': k_pct,
            'bb_pct': bb_pct,
            'hr_pct': hr_pct,
            'total_pa': total_pa
        }

        print(f"  K%: {k_pct:.1f}%, BB%: {bb_pct:.1f}%, HR%: {hr_pct:.1f}%")
        print()

    # Compare results
    print(f"\n{'='*80}")
    print(f"PLAYER QUALITY COMPARISON")
    print(f"{'='*80}\n")

    print(f"{'Quality':<25} {'K%':<10} {'BB%':<10} {'HR%':<10} {'PA':<10}")
    print("-" * 65)

    for name, result in results_by_quality.items():
        print(f"{name:<25} {result['k_pct']:>5.1f}%     {result['bb_pct']:>5.1f}%     {result['hr_pct']:>5.1f}%     {result['total_pa']:<10}")

    print()


if __name__ == "__main__":
    # Parse command line arguments
    if len(sys.argv) > 1:
        if sys.argv[1] == "--quick":
            print("Running QUICK diagnostic (5 games, ~250 PA)...")
            run_tto_diagnostic(num_games=5)
        elif sys.argv[1] == "--full":
            print("Running FULL validation (player quality comparison)...")
            run_player_comparison()
        else:
            print(f"Unknown option: {sys.argv[1]}")
            print("Usage:")
            print("  python research/run_tto_diagnostic.py           # Default 10 games (~500 PA)")
            print("  python research/run_tto_diagnostic.py --quick   # Quick 5 games (~250 PA)")
            print("  python research/run_tto_diagnostic.py --full    # Player quality comparison")
    else:
        # Default: 10 games
        run_tto_diagnostic(num_games=10)
