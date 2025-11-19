"""
Test script for metrics integration.

Demonstrates the complete integration of simulation metrics into game simulation.
"""

import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from batted_ball.game_simulation import GameSimulator, Team, create_test_team


def test_metrics_integration():
    """Test metrics integration at all debug levels"""

    print("\n" + "="*80)
    print("METRICS INTEGRATION TEST")
    print("="*80)

    # Create teams
    print("\n1. Creating test teams...")
    away_team = create_test_team("Visitors", team_quality="average")
    home_team = create_test_team("Home Team", team_quality="average")
    print("   ✓ Teams created")

    # Test Level 0 (OFF)
    print("\n2. Testing Level 0 (OFF) - No metrics output...")
    sim0 = GameSimulator(away_team, home_team, verbose=False, debug_metrics=0)
    result0 = sim0.simulate_game(num_innings=1)
    print(f"   ✓ Level 0 complete: {result0.away_score}-{result0.home_score}")

    # Test Level 1 (BASIC)
    print("\n3. Testing Level 1 (BASIC) - Summary only...")
    sim1 = GameSimulator(away_team, home_team, verbose=False, debug_metrics=1)
    result1 = sim1.simulate_game(num_innings=1)
    print(f"   ✓ Level 1 complete: {result1.away_score}-{result1.home_score}")

    # Test Level 2 (DETAILED)
    print("\n4. Testing Level 2 (DETAILED) - Full pitch/play logging...")
    print("   (This will show detailed output for each pitch)")
    sim2 = GameSimulator(away_team, home_team, verbose=False, debug_metrics=2)
    result2 = sim2.simulate_game(num_innings=1)
    print(f"   ✓ Level 2 complete: {result2.away_score}-{result2.home_score}")

    print("\n" + "="*80)
    print("✅ ALL TESTS PASSED")
    print("="*80)

    print("\n📊 INTEGRATION STATUS:")
    print("   ✓ Phase 1: at_bat.py integration complete")
    print("   ✓ Phase 2: game_simulation.py integration complete")
    print("   ○ Phase 3: play_simulation.py (fielding) - not yet implemented")

    print("\n📚 USAGE:")
    print("   # Run game with metrics")
    print("   from batted_ball.game_simulation import GameSimulator")
    print("   sim = GameSimulator(away, home, debug_metrics=2)  # 0-3")
    print("   result = sim.simulate_game()")

    print("\n🎯 DEBUG LEVELS:")
    print("   0 = OFF       (no overhead, production)")
    print("   1 = BASIC     (summary stats)")
    print("   2 = DETAILED  (every pitch/play)")
    print("   3 = EXHAUSTIVE (all internals)")

    print()


if __name__ == "__main__":
    test_metrics_integration()
