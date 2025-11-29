"""
Benchmark script to compare simulation speed and accuracy across different modes.

Usage:
    python benchmarks/benchmark_simulation_modes.py
"""

import time
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from batted_ball.constants import SimulationMode, get_dt_for_mode
from batted_ball.fast_trajectory import FastTrajectorySimulator, benchmark_jit_speedup
from batted_ball.trajectory import BattedBallSimulator


def benchmark_trajectory_modes(n_trajectories: int = 500):
    """
    Benchmark trajectory simulation across all modes.
    
    Parameters
    ----------
    n_trajectories : int
        Number of trajectories to simulate per mode
    """
    print("=" * 70)
    print("TRAJECTORY SIMULATION BENCHMARK")
    print(f"Simulating {n_trajectories} trajectories per mode")
    print("=" * 70)
    
    # Test parameters (typical fly ball)
    test_params = {
        'exit_velocity': 45.0,  # m/s (~100 mph)
        'launch_angle': 28.0,
        'spray_angle': 0.0,
        'spin_rate': 2000.0,
        'spin_axis': [0, 1, 0],  # pure backspin
    }
    
    results = {}
    
    for mode in SimulationMode:
        print(f"\nBenchmarking {mode.value.upper()} mode (dt={get_dt_for_mode(mode)*1000:.1f}ms)...")
        
        sim = FastTrajectorySimulator(simulation_mode=mode)
        
        # Warmup (JIT compilation)
        _ = sim.simulate_batted_ball(**test_params)
        
        # Benchmark
        start = time.time()
        distances = []
        for _ in range(n_trajectories):
            result = sim.simulate_batted_ball(**test_params)
            distances.append(result['distance'])
        elapsed = time.time() - start
        
        avg_distance = sum(distances) / len(distances)
        
        results[mode] = {
            'total_time': elapsed,
            'per_trajectory': elapsed / n_trajectories,
            'trajectories_per_second': n_trajectories / elapsed,
            'avg_distance': avg_distance,
            'dt': get_dt_for_mode(mode),
        }
        
        print(f"  Time: {elapsed:.3f}s total, {elapsed/n_trajectories*1000:.2f}ms per trajectory")
        print(f"  Speed: {n_trajectories/elapsed:.1f} trajectories/second")
        print(f"  Avg distance: {avg_distance:.2f}m")
    
    # Summary comparison
    print("\n" + "=" * 70)
    print("SUMMARY")
    print("=" * 70)
    print(f"{'Mode':<12} {'Time Step':<10} {'Speed (traj/s)':<15} {'Speedup':<10} {'Avg Dist (m)':<12} {'Diff':<8}")
    print("-" * 70)
    
    baseline = results[SimulationMode.ACCURATE]
    baseline_speed = baseline['trajectories_per_second']
    baseline_dist = baseline['avg_distance']
    
    for mode in SimulationMode:
        r = results[mode]
        speedup = r['trajectories_per_second'] / baseline_speed
        dist_diff = r['avg_distance'] - baseline_dist
        dist_pct = (dist_diff / baseline_dist) * 100
        
        print(f"{mode.value:<12} {r['dt']*1000:>6.1f}ms    {r['trajectories_per_second']:>10.1f}     {speedup:>6.1f}x     {r['avg_distance']:>8.2f}     {dist_pct:>+5.2f}%")
    
    return results


def benchmark_game_simulation(n_games: int = 3):
    """
    Benchmark game simulation with different modes.
    
    Note: This is slower, so we run fewer iterations.
    """
    print("\n" + "=" * 70)
    print("GAME SIMULATION BENCHMARK")
    print(f"Simulating {n_games} games per mode")
    print("=" * 70)
    
    from batted_ball.game_simulation import GameSimulator, create_test_team
    
    results = {}
    
    for mode in [SimulationMode.ACCURATE, SimulationMode.FAST, SimulationMode.ULTRA_FAST]:
        print(f"\nBenchmarking {mode.value.upper()} mode...")
        
        total_time = 0
        total_pitches = 0
        
        for i in range(n_games):
            away_team = create_test_team("Away", "away")
            home_team = create_test_team("Home", "home")
            
            start = time.time()
            sim = GameSimulator(
                away_team, 
                home_team, 
                verbose=False,
                simulation_mode=mode
            )
            sim.simulate_game()
            elapsed = time.time() - start
            
            total_time += elapsed
            total_pitches += sim.game_state.total_pitches
        
        results[mode] = {
            'total_time': total_time,
            'per_game': total_time / n_games,
            'games_per_minute': (n_games / total_time) * 60,
            'avg_pitches': total_pitches / n_games,
        }
        
        print(f"  Time: {total_time:.2f}s total, {total_time/n_games:.2f}s per game")
        print(f"  Speed: {(n_games/total_time)*60:.1f} games/minute")
        print(f"  Avg pitches: {total_pitches/n_games:.0f}")
    
    # Summary
    print("\n" + "=" * 70)
    print("GAME SIMULATION SUMMARY")
    print("=" * 70)
    print(f"{'Mode':<12} {'Sec/Game':<12} {'Games/Min':<12} {'Speedup':<10}")
    print("-" * 50)
    
    baseline = results[SimulationMode.ACCURATE]
    
    for mode in results:
        r = results[mode]
        speedup = r['games_per_minute'] / baseline['games_per_minute']
        print(f"{mode.value:<12} {r['per_game']:>8.2f}s    {r['games_per_minute']:>8.1f}      {speedup:>6.1f}x")
    
    return results


def main():
    print("=" * 70)
    print("SIMULATION MODE PERFORMANCE BENCHMARK")
    print("=" * 70)
    print("\nThis benchmark compares different simulation modes:")
    print("- ACCURATE: 1ms time step (baseline, highest accuracy)")
    print("- FAST: 2ms time step (~2x speedup)")
    print("- ULTRA_FAST: 5ms time step (~5x speedup)")
    print("- EXTREME: 10ms time step (~10x speedup)")
    print("")
    
    # Trajectory benchmark
    traj_results = benchmark_trajectory_modes(n_trajectories=500)
    
    # Game benchmark (optional - takes longer)
    print("\n" + "-" * 70)
    print("Running game simulation benchmark (3 games per mode)...")
    print("(This takes ~1-2 minutes)")
    game_results = benchmark_game_simulation(n_games=3)
    
    print("\n" + "=" * 70)
    print("BENCHMARK COMPLETE")
    print("=" * 70)
    
    # Recommendations
    print("\nRECOMMENDATIONS:")
    print("-" * 50)
    print("- Physics validation: Use ACCURATE mode")
    print("- Single games (demo): Use FAST mode")
    print("- Bulk simulations (162+ games): Use ULTRA_FAST mode")
    print("- Massive Monte Carlo (1000+ games): Use EXTREME mode")
    print("")


if __name__ == "__main__":
    main()
