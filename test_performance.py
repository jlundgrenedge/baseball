"""
Performance test for simulation optimizations.

Tests the speed of at-bat simulations with and without fast_mode.
"""

import time
from batted_ball import Pitcher, Hitter, AtBatSimulator


def create_test_pitcher():
    """Create an average MLB pitcher."""
    pitcher = Pitcher(
        name="Test Pitcher",
        velocity=50,
        spin_rate=50,
        spin_efficiency=50,
        command=50,
        control=50,
        deception=50,
        stamina=100,
    )
    pitcher.pitch_arsenal = {
        'fastball': {'velocity': 50, 'movement': 50, 'command': 50, 'usage': 60},
        'slider': {'velocity': 48, 'movement': 60, 'command': 45, 'usage': 25},
        'changeup': {'velocity': 45, 'movement': 55, 'command': 48, 'usage': 15},
    }
    return pitcher


def create_test_hitter():
    """Create an average MLB hitter."""
    return Hitter(
        name="Test Hitter",
        bat_speed=50,
        barrel_accuracy=50,
        swing_timing_precision=50,
        bat_control=50,
        exit_velocity_ceiling=50,
        zone_discipline=50,
        pitch_recognition_speed=50,
        swing_decision_aggressiveness=50,
        adjustment_ability=50,
    )


def run_performance_test(n_at_bats=100, fast_mode=False):
    """Run at-bats and time them."""
    pitcher = create_test_pitcher()
    hitter = create_test_hitter()

    start_time = time.time()

    for i in range(n_at_bats):
        pitcher.current_stamina = 100
        sim = AtBatSimulator(pitcher, hitter, fast_mode=fast_mode)
        result = sim.simulate_at_bat(verbose=False)

    elapsed_time = time.time() - start_time
    return elapsed_time


if __name__ == '__main__':
    print("=" * 70)
    print("SIMULATION PERFORMANCE TEST")
    print("=" * 70)
    print("\nTesting simulation speed with different modes...")
    print("(Running 100 at-bats in each mode)\n")

    # Test normal mode
    print("Testing NORMAL MODE (dt=0.001s)...")
    normal_time = run_performance_test(n_at_bats=100, fast_mode=False)
    print(f"  Completed in {normal_time:.2f} seconds")
    print(f"  Average: {normal_time/100*1000:.1f} ms per at-bat")

    print()

    # Test fast mode
    print("Testing FAST MODE (dt=0.002s, numba-optimized)...")
    fast_time = run_performance_test(n_at_bats=100, fast_mode=True)
    print(f"  Completed in {fast_time:.2f} seconds")
    print(f"  Average: {fast_time/100*1000:.1f} ms per at-bat")

    print()
    print("=" * 70)
    print("RESULTS")
    print("=" * 70)
    speedup = normal_time / fast_time if fast_time > 0 else 0
    print(f"\nSpeedup: {speedup:.2f}x faster")
    print(f"Time saved: {normal_time - fast_time:.2f} seconds ({(1-fast_time/normal_time)*100:.1f}%)")

    print("\n" + "=" * 70)
    print("PROJECTED PERFORMANCE")
    print("=" * 70)

    for n in [1000, 10000, 100000]:
        normal_proj = (normal_time / 100) * n
        fast_proj = (fast_time / 100) * n
        time_saved = normal_proj - fast_proj

        print(f"\n{n:,} at-bats:")
        print(f"  Normal mode: {normal_proj/60:.1f} minutes")
        print(f"  Fast mode:   {fast_proj/60:.1f} minutes")
        print(f"  Time saved:  {time_saved/60:.1f} minutes")

    print("\n" + "=" * 70)
    print("\nRecommendation: Use fast_mode=True for bulk simulations (1000+ at-bats)")
    print("                The performance boost is significant with minimal accuracy loss.")
