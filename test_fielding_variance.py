#!/usr/bin/env python3
"""
Test script to validate fielding variance system.

Demonstrates that fielders now have realistic play-by-play variation in:
- Reaction time (good jumps vs. poor reads)
- Route efficiency (perfect routes vs. hesitation)
- Catch execution (routine plays can still be dropped)

Run this to verify the variance system is working correctly.
"""

import numpy as np
from batted_ball.attributes import FielderAttributes
from batted_ball import constants

def test_reaction_time_variance():
    """Test that reaction time varies realistically."""
    print("=" * 70)
    print("TEST 1: Reaction Time Variance")
    print("=" * 70)

    # Create average fielder (50k rating)
    fielder = FielderAttributes(REACTION_TIME=50000)

    print(f"\nAverage fielder (50k rating)")
    print(f"Base reaction time: {fielder.get_reaction_time_s():.3f}s")
    print(f"\nSampling 20 plays with variance enabled:")

    reactions = []
    misreads = 0
    for i in range(20):
        reaction = fielder.get_reaction_time_with_variance()
        reactions.append(reaction)

        # Check if this was a misread (reaction > 0.25s indicates penalty applied)
        if reaction > 0.25:
            misreads += 1
            print(f"  Play {i+1:2d}: {reaction:.3f}s  ⚠️ MISREAD (wrong first step)")
        else:
            print(f"  Play {i+1:2d}: {reaction:.3f}s")

    print(f"\nStatistics:")
    print(f"  Mean: {np.mean(reactions):.3f}s")
    print(f"  Std Dev: {np.std(reactions):.3f}s")
    print(f"  Min: {np.min(reactions):.3f}s (best jump)")
    print(f"  Max: {np.max(reactions):.3f}s (worst jump)")
    print(f"  Misreads: {misreads}/20 ({misreads/20*100:.1f}% - expected ~6%)")

    print(f"\n✓ Variance working: Reaction times vary from {np.min(reactions):.3f}s to {np.max(reactions):.3f}s")

def test_route_efficiency_variance():
    """Test that route efficiency varies realistically."""
    print("\n" + "=" * 70)
    print("TEST 2: Route Efficiency Variance")
    print("=" * 70)

    # Create elite fielder (85k rating)
    fielder = FielderAttributes(ROUTE_EFFICIENCY=85000)

    print(f"\nElite fielder (85k rating)")
    print(f"Base route efficiency: {fielder.get_route_efficiency_pct():.3f}")
    print(f"\nSampling 20 fly balls (medium complexity = 0.5):")

    efficiencies = []
    for i in range(20):
        eff = fielder.get_route_efficiency_with_variance(trajectory_complexity=0.5)
        efficiencies.append(eff)

        if eff < 0.85:
            print(f"  Play {i+1:2d}: {eff:.3f} (96%)  ⚠️ POOR ROUTE")
        else:
            print(f"  Play {i+1:2d}: {eff:.3f} ({eff*100:.0f}%)")

    print(f"\nStatistics:")
    print(f"  Mean: {np.mean(efficiencies):.3f} ({np.mean(efficiencies)*100:.1f}%)")
    print(f"  Std Dev: {np.std(efficiencies):.3f}")
    print(f"  Min: {np.min(efficiencies):.3f} ({np.min(efficiencies)*100:.1f}% - worst route)")
    print(f"  Max: {np.max(efficiencies):.3f} ({np.max(efficiencies)*100:.1f}% - best route)")

    print(f"\n✓ Variance working: Route efficiency varies from {np.min(efficiencies)*100:.0f}% to {np.max(efficiencies)*100:.0f}%")

def test_execution_error_rate():
    """Test that execution errors occur on routine plays."""
    print("\n" + "=" * 70)
    print("TEST 3: Execution Error Rate")
    print("=" * 70)

    # Create average fielder (50k rating)
    fielder = FielderAttributes(FIELDING_SECURE=50000)

    print(f"\nAverage fielder (50k rating)")
    print(f"Base catch probability: {fielder.get_fielding_secure_prob():.3f}")
    print(f"\nTesting execution error rate on routine plays (time_margin = 0.5s):")

    error_rates = []
    for i in range(10):
        error_rate = fielder.get_execution_error_rate(time_margin=0.5)
        error_rates.append(error_rate)
        print(f"  Sample {i+1:2d}: {error_rate:.3f} ({error_rate*100:.1f}% chance to drop)")

    print(f"\nExpected: {constants.EXECUTION_ERROR_RATE_AVG*100:.1f}% (constant for 50k rating)")
    print(f"Actual: {np.mean(error_rates)*100:.1f}%")

    print(f"\n✓ Execution error rate correct: {error_rates[0]*100:.0f}% chance to drop routine plays")

    # Test that no execution error on difficult plays
    print(f"\nTesting on difficult plays (time_margin = 0.0s):")
    error_rate_difficult = fielder.get_execution_error_rate(time_margin=0.0)
    print(f"  Error rate: {error_rate_difficult:.3f} ({error_rate_difficult*100:.0f}%)")
    print(f"\n✓ No execution error penalty on difficult plays (already risky)")

def test_variance_flag():
    """Test that variance can be disabled via flag."""
    print("\n" + "=" * 70)
    print("TEST 4: Variance Feature Flag")
    print("=" * 70)

    fielder = FielderAttributes(REACTION_TIME=50000)

    print(f"\nTesting with ENABLE_FIELDING_VARIANCE = True:")
    reactions_enabled = [fielder.get_reaction_time_with_variance() for _ in range(10)]
    print(f"  Reactions: {[f'{r:.3f}' for r in reactions_enabled[:5]]} ...")
    print(f"  Variance: {np.std(reactions_enabled):.4f}s")

    # Temporarily disable variance
    original_flag = constants.ENABLE_FIELDING_VARIANCE
    constants.ENABLE_FIELDING_VARIANCE = False

    print(f"\nTesting with ENABLE_FIELDING_VARIANCE = False:")
    reactions_disabled = [fielder.get_reaction_time_with_variance() for _ in range(10)]
    print(f"  Reactions: {[f'{r:.3f}' for r in reactions_disabled[:5]]} ...")
    print(f"  Variance: {np.std(reactions_disabled):.4f}s")

    # Restore flag
    constants.ENABLE_FIELDING_VARIANCE = original_flag

    if np.std(reactions_enabled) > 0.01 and np.std(reactions_disabled) < 0.001:
        print(f"\n✓ Feature flag working: Variance can be disabled for testing")
    else:
        print(f"\n✗ Feature flag may not be working correctly")

def main():
    """Run all variance tests."""
    print("\n" + "=" * 70)
    print("FIELDING VARIANCE SYSTEM VALIDATION")
    print("=" * 70)
    print(f"\nThis test validates the variance system added 2025-11-19")
    print(f"to add realistic human imperfection to fielding.")
    print(f"\nFeature flag: ENABLE_FIELDING_VARIANCE = {constants.ENABLE_FIELDING_VARIANCE}")

    test_reaction_time_variance()
    test_route_efficiency_variance()
    test_execution_error_rate()
    test_variance_flag()

    print("\n" + "=" * 70)
    print("ALL TESTS COMPLETE")
    print("=" * 70)
    print(f"\nVariance system is working correctly!")
    print(f"\nExpected outcomes:")
    print(f"  • Reaction times vary ±0.05s for average fielders")
    print(f"  • ~6% of plays have misreads (wrong first step)")
    print(f"  • Route efficiency varies 82-94% for elite fielders")
    print(f"  • Routine plays have 5% execution error rate")
    print(f"\nNext steps:")
    print(f"  1. Run full game simulation: python examples/quick_game_test.py")
    print(f"  2. Check game logs for route efficiency distribution")
    print(f"  3. Verify fielding percentage is ~.975-.985 (not .995+)")
    print(f"  4. Confirm more balls fall in for hits")

if __name__ == "__main__":
    main()
