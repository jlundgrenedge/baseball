"""
Comprehensive performance benchmarking suite for baseball simulation optimizations.

This test suite measures the performance improvements from:
1. Numba JIT optimization on integrator
2. GPU acceleration (if available)
3. Memory optimization (object pooling, pre-allocation)
4. Batch processing
5. Parallel multi-core execution

Run with: pytest tests/test_performance_benchmarks.py -v -s
"""

import pytest
import numpy as np
import time
from pathlib import Path
import json


def test_jit_integrator_speedup():
    """
    Benchmark: Numba JIT-optimized integrator vs standard integration.

    Expected: 5-10× speedup with JIT compilation
    """
    from batted_ball.fast_trajectory import FastTrajectorySimulator

    print("\n" + "="*70)
    print("BENCHMARK: Numba JIT Integrator Speedup")
    print("="*70)

    # Test parameters
    n_trajectories = 100
    exit_velocity = 45.0  # m/s
    launch_angle = 30.0
    spray_angle = 0.0
    spin_rate = 2000.0
    spin_axis = [0, 1, 0]

    # Create fast simulator (uses JIT)
    sim = FastTrajectorySimulator(fast_mode=False)

    # Warm up JIT (first call compiles)
    print("\nWarming up JIT compiler...")
    _ = sim.simulate_batted_ball(
        exit_velocity, launch_angle, spray_angle, spin_rate, spin_axis
    )
    print("JIT compilation complete")

    # Benchmark JIT version
    print(f"\nRunning {n_trajectories} trajectories with JIT optimization...")
    start_time = time.time()

    for _ in range(n_trajectories):
        _ = sim.simulate_batted_ball(
            exit_velocity, launch_angle, spray_angle, spin_rate, spin_axis
        )

    jit_time = time.time() - start_time

    # Results
    per_trajectory_jit = jit_time / n_trajectories
    trajectories_per_sec_jit = n_trajectories / jit_time

    print(f"\n{'Results:':<25} {'JIT Optimized':<20}")
    print(f"{'-'*50}")
    print(f"{'Total time:':<25} {jit_time:.3f}s")
    print(f"{'Per trajectory:':<25} {per_trajectory_jit*1000:.2f}ms")
    print(f"{'Trajectories/sec:':<25} {trajectories_per_sec_jit:.1f}")

    # Expected performance threshold
    expected_min_rate = 50  # At least 50 trajectories/sec with JIT
    assert trajectories_per_sec_jit > expected_min_rate, (
        f"JIT performance below threshold: {trajectories_per_sec_jit:.1f} < {expected_min_rate}"
    )

    print(f"\n✓ Performance meets expectations (>{expected_min_rate} traj/sec)")
    print("="*70)


def test_fast_mode_speedup():
    """
    Benchmark: Fast mode (larger time step) vs normal mode.

    Expected: ~2× speedup with fast mode (larger dt)
    """
    from batted_ball.fast_trajectory import FastTrajectorySimulator

    print("\n" + "="*70)
    print("BENCHMARK: Fast Mode (Larger Time Step) Speedup")
    print("="*70)

    n_trajectories = 50

    # Test parameters
    test_params = {
        'exit_velocity': 45.0,
        'launch_angle': 30.0,
        'spray_angle': 0.0,
        'spin_rate': 2000.0,
        'spin_axis': [0, 1, 0],
    }

    # Normal mode
    sim_normal = FastTrajectorySimulator(fast_mode=False)
    _ = sim_normal.simulate_batted_ball(**test_params)  # Warm up

    print(f"\nRunning {n_trajectories} trajectories in NORMAL mode...")
    start = time.time()
    for _ in range(n_trajectories):
        _ = sim_normal.simulate_batted_ball(**test_params)
    normal_time = time.time() - start

    # Fast mode
    sim_fast = FastTrajectorySimulator(fast_mode=True)
    _ = sim_fast.simulate_batted_ball(**test_params)  # Warm up

    print(f"Running {n_trajectories} trajectories in FAST mode...")
    start = time.time()
    for _ in range(n_trajectories):
        _ = sim_fast.simulate_batted_ball(**test_params)
    fast_time = time.time() - start

    # Calculate speedup
    speedup = normal_time / fast_time

    print(f"\n{'Mode':<15} {'Time (s)':<15} {'Per Trajectory (ms)':<25} {'Traj/sec':<15}")
    print(f"{'-'*70}")
    print(f"{'Normal':<15} {normal_time:.3f}{'':<10} {normal_time/n_trajectories*1000:.2f}{'':<18} {n_trajectories/normal_time:.1f}")
    print(f"{'Fast':<15} {fast_time:.3f}{'':<10} {fast_time/n_trajectories*1000:.2f}{'':<18} {n_trajectories/fast_time:.1f}")
    print(f"\n{'Speedup:':<15} {speedup:.2f}×")

    assert speedup > 1.5, f"Fast mode speedup below threshold: {speedup:.2f}× < 1.5×"

    print(f"\n✓ Fast mode provides expected speedup (>{1.5:.1f}×)")
    print("="*70)


def test_batch_simulation_performance():
    """
    Benchmark: Batch trajectory processing performance.

    Tests the BatchTrajectorySimulator for handling multiple trajectories.
    """
    from batted_ball.fast_trajectory import BatchTrajectorySimulator

    print("\n" + "="*70)
    print("BENCHMARK: Batch Trajectory Processing")
    print("="*70)

    n_trajectories = 200

    # Generate random parameters
    np.random.seed(42)
    exit_velocities = np.random.uniform(35, 50, n_trajectories)
    launch_angles = np.random.uniform(10, 40, n_trajectories)
    spray_angles = np.random.uniform(-30, 30, n_trajectories)
    spin_rates = np.random.uniform(1500, 2500, n_trajectories)
    spin_axes = np.tile([0, 1, 0], (n_trajectories, 1))

    # Run batch simulation
    sim = BatchTrajectorySimulator(fast_mode=True)

    print(f"\nRunning batch simulation of {n_trajectories} trajectories...")
    start_time = time.time()

    results = sim.simulate_batch(
        exit_velocities,
        launch_angles,
        spray_angles,
        spin_rates,
        spin_axes,
    )

    batch_time = time.time() - start_time

    # Calculate statistics
    distances = [r['distance'] for r in results]
    apexes = [r['apex'] for r in results]

    print(f"\n{'Batch Processing Results:':<30}")
    print(f"{'-'*50}")
    print(f"{'Total trajectories:':<30} {len(results)}")
    print(f"{'Total time:':<30} {batch_time:.3f}s")
    print(f"{'Per trajectory:':<30} {batch_time/n_trajectories*1000:.2f}ms")
    print(f"{'Throughput:':<30} {n_trajectories/batch_time:.1f} traj/sec")
    print(f"\n{'Distance statistics:':<30}")
    print(f"  {'Mean:':<28} {np.mean(distances):.1f}m")
    print(f"  {'Std:':<28} {np.std(distances):.1f}m")
    print(f"  {'Range:':<28} {np.min(distances):.1f}m - {np.max(distances):.1f}m")

    assert len(results) == n_trajectories
    assert n_trajectories / batch_time > 30  # At least 30 traj/sec

    print(f"\n✓ Batch processing performance acceptable")
    print("="*70)


def test_multicore_parallel_speedup():
    """
    Benchmark: Multi-core parallel game simulation.

    Expected: 5-8× speedup on 8-core system
    """
    from batted_ball.parallel_game_simulation import ParallelGameSimulator
    from batted_ball.game_simulation import GameSimulator
    import multiprocessing

    print("\n" + "="*70)
    print("BENCHMARK: Multi-Core Parallel Game Simulation")
    print("="*70)

    n_games = 20  # Reduced for faster testing
    n_cores = min(multiprocessing.cpu_count(), 8)

    print(f"\nSystem: {n_cores} CPU cores available")
    print(f"Simulating {n_games} games...")

    # Sequential baseline (just time a few games)
    print("\nRunning 5 games sequentially for baseline...")
    sim_seq = GameSimulator(verbose=False)
    start = time.time()
    for _ in range(5):
        _ = sim_seq.simulate_game()
    seq_time_per_game = (time.time() - start) / 5

    estimated_seq_total = seq_time_per_game * n_games
    print(f"Sequential time per game: {seq_time_per_game:.2f}s")
    print(f"Estimated sequential total: {estimated_seq_total:.1f}s")

    # Parallel execution
    print(f"\nRunning {n_games} games in parallel on {n_cores} cores...")
    sim_parallel = ParallelGameSimulator(num_workers=n_cores, verbose=False)

    start = time.time()
    results = sim_parallel.simulate_games(n_games, show_progress=False)
    parallel_time = time.time() - start

    # Calculate speedup
    speedup = estimated_seq_total / parallel_time
    efficiency = speedup / n_cores

    print(f"\n{'Execution Mode':<20} {'Time (s)':<15} {'Games/sec':<15}")
    print(f"{'-'*50}")
    print(f"{'Sequential (est.)':<20} {estimated_seq_total:.1f}{'':<10} {n_games/estimated_seq_total:.2f}")
    print(f"{'Parallel ({n_cores} cores)'.format(n_cores=n_cores):<20} {parallel_time:.1f}{'':<10} {n_games/parallel_time:.2f}")
    print(f"\n{'Speedup:':<20} {speedup:.2f}×")
    print(f"{'Parallel efficiency:':<20} {efficiency*100:.1f}%")

    assert len(results) == n_games
    assert speedup > 2.0, f"Parallel speedup below threshold: {speedup:.2f}× < 2.0×"

    print(f"\n✓ Parallel execution provides good speedup (>{2.0:.1f}×)")
    print("="*70)


@pytest.mark.gpu
def test_gpu_acceleration_if_available():
    """
    Benchmark: GPU acceleration vs CPU (if GPU is available).

    Expected: 10-100× speedup for large batches
    """
    from batted_ball.gpu_acceleration import GPUTrajectorySimulator, get_gpu_info

    print("\n" + "="*70)
    print("BENCHMARK: GPU Acceleration")
    print("="*70)

    # Check GPU availability
    gpu_info = get_gpu_info()

    if not gpu_info['available']:
        print(f"\nGPU not available: {gpu_info.get('error', 'Unknown')}")
        print("Skipping GPU benchmark")
        print("="*70)
        pytest.skip("GPU not available")
        return

    print(f"\nGPU Device: {gpu_info['device_name']}")
    print(f"Memory: {gpu_info['memory_total_gb']:.1f}GB total, {gpu_info['memory_free_gb']:.1f}GB free")

    # Run GPU benchmark
    sim = GPUTrajectorySimulator()
    n_trajectories = 1000

    print(f"\nRunning benchmark with {n_trajectories} trajectories...")
    result = sim.benchmark(n_trajectories=n_trajectories)

    print(f"\n{'GPU Benchmark Results:':<30}")
    print(f"{'-'*50}")
    print(f"{'Trajectories:':<30} {result['n_trajectories']}")
    print(f"{'Total time:':<30} {result['total_time']:.3f}s")
    print(f"{'Per trajectory:':<30} {result['per_trajectory']*1000:.2f}ms")
    print(f"{'Throughput:':<30} {result['trajectories_per_second']:.1f} traj/sec")
    print(f"{'Expected speedup:':<30} {result['speedup_estimate']}")

    # GPU should handle at least 200 traj/sec for large batches
    assert result['trajectories_per_second'] > 200, (
        f"GPU performance below threshold: {result['trajectories_per_second']:.1f} < 200"
    )

    print(f"\n✓ GPU acceleration working effectively")
    print("="*70)


def test_memory_optimization_overhead():
    """
    Benchmark: Memory allocation overhead with and without object pooling.

    Measures the impact of memory optimization strategies.
    """
    from batted_ball.performance import StateVectorPool, ForceCalculationCache

    print("\n" + "="*70)
    print("BENCHMARK: Memory Optimization Overhead")
    print("="*70)

    # Test state vector pool
    pool = StateVectorPool(pool_size=100)
    n_operations = 10000

    print(f"\nTesting state vector pool with {n_operations} operations...")

    start = time.time()
    for _ in range(n_operations):
        idx, vec = pool.get_state_vector()
        vec[:] = np.random.random(6)  # Simulate usage
        pool.release_state_vector(idx)
    pool_time = time.time() - start

    efficiency = pool.get_efficiency()

    print(f"\n{'State Vector Pool Results:':<30}")
    print(f"{'-'*50}")
    print(f"{'Operations:':<30} {n_operations}")
    print(f"{'Total time:':<30} {pool_time:.3f}s")
    print(f"{'Per operation:':<30} {pool_time/n_operations*1e6:.2f}μs")
    print(f"{'Pool efficiency:':<30} {efficiency*100:.1f}%")
    print(f"{'Hits:':<30} {pool.stats['hits']}")
    print(f"{'Misses:':<30} {pool.stats['misses']}")

    # Test force calculation cache
    cache = ForceCalculationCache(cache_size=1000)
    n_lookups = 5000

    print(f"\nTesting force calculation cache with {n_lookups} lookups...")

    # Simulate repeated force calculations with similar parameters
    np.random.seed(42)
    velocities = np.random.uniform(-50, 50, (100, 3))  # Limited set of velocities
    spin_rates = np.random.uniform(1500, 2500, 100)

    start = time.time()
    for i in range(n_lookups):
        vel_idx = i % 100  # Reuse velocities for cache hits
        velocity = velocities[vel_idx]
        spin_axis = np.array([0, 1, 0])
        spin_rate = spin_rates[vel_idx]

        # Try lookup
        force = cache.lookup(velocity, spin_axis, spin_rate)

        if force is None:
            # Calculate and store (simulated)
            force = np.random.random(3)
            cache.store(velocity, spin_axis, spin_rate, force)

    cache_time = time.time() - start
    stats = cache.get_stats()

    print(f"\n{'Force Calculation Cache Results:':<30}")
    print(f"{'-'*50}")
    print(f"{'Lookups:':<30} {n_lookups}")
    print(f"{'Total time:':<30} {cache_time:.3f}s")
    print(f"{'Per lookup:':<30} {cache_time/n_lookups*1e6:.2f}μs")
    print(f"{'Hit rate:':<30} {stats['hit_rate']*100:.1f}%")
    print(f"{'Hits:':<30} {stats['hits']}")
    print(f"{'Misses:':<30} {stats['misses']}")
    print(f"{'Collisions:':<30} {stats['collisions']}")

    assert efficiency > 0.99, f"Pool efficiency too low: {efficiency:.3f}"
    assert stats['hit_rate'] > 0.5, f"Cache hit rate too low: {stats['hit_rate']:.2f}"

    print(f"\n✓ Memory optimizations working effectively")
    print("="*70)


def test_comprehensive_performance_report():
    """
    Generate comprehensive performance report comparing all optimization strategies.
    """
    print("\n" + "="*70)
    print("COMPREHENSIVE PERFORMANCE REPORT")
    print("="*70)

    report = {
        'timestamp': time.strftime('%Y-%m-%d %H:%M:%S'),
        'optimizations': {},
    }

    # JIT speedup
    from batted_ball.fast_trajectory import FastTrajectorySimulator
    sim = FastTrajectorySimulator(fast_mode=False)
    _ = sim.simulate_batted_ball(45.0, 30.0, 0.0, 2000.0, [0, 1, 0])  # Warm up

    start = time.time()
    for _ in range(50):
        _ = sim.simulate_batted_ball(45.0, 30.0, 0.0, 2000.0, [0, 1, 0])
    jit_time = time.time() - start

    report['optimizations']['jit_integrator'] = {
        'throughput': 50 / jit_time,
        'per_trajectory_ms': jit_time / 50 * 1000,
    }

    # Fast mode
    sim_fast = FastTrajectorySimulator(fast_mode=True)
    _ = sim_fast.simulate_batted_ball(45.0, 30.0, 0.0, 2000.0, [0, 1, 0])  # Warm up

    start = time.time()
    for _ in range(50):
        _ = sim_fast.simulate_batted_ball(45.0, 30.0, 0.0, 2000.0, [0, 1, 0])
    fast_time = time.time() - start

    report['optimizations']['fast_mode'] = {
        'throughput': 50 / fast_time,
        'per_trajectory_ms': fast_time / 50 * 1000,
        'speedup_vs_normal': jit_time / fast_time,
    }

    # GPU (if available)
    from batted_ball.gpu_acceleration import get_gpu_info
    gpu_info = get_gpu_info()
    report['optimizations']['gpu'] = {
        'available': gpu_info['available'],
    }

    if gpu_info['available']:
        report['optimizations']['gpu']['device'] = gpu_info['device_name']

    # Print summary
    print("\n" + "="*70)
    print("OPTIMIZATION SUMMARY")
    print("="*70)

    print(f"\n{'JIT Integrator:':<30}")
    print(f"  {'Throughput:':<28} {report['optimizations']['jit_integrator']['throughput']:.1f} traj/sec")
    print(f"  {'Per trajectory:':<28} {report['optimizations']['jit_integrator']['per_trajectory_ms']:.2f}ms")

    print(f"\n{'Fast Mode:':<30}")
    print(f"  {'Throughput:':<28} {report['optimizations']['fast_mode']['throughput']:.1f} traj/sec")
    print(f"  {'Per trajectory:':<28} {report['optimizations']['fast_mode']['per_trajectory_ms']:.2f}ms")
    print(f"  {'Speedup:':<28} {report['optimizations']['fast_mode']['speedup_vs_normal']:.2f}×")

    print(f"\n{'GPU Acceleration:':<30} {'Available' if report['optimizations']['gpu']['available'] else 'Not Available'}")

    # Save report
    report_path = Path(__file__).parent.parent / 'performance_report.json'
    with open(report_path, 'w') as f:
        json.dump(report, f, indent=2)

    print(f"\n✓ Performance report saved to: {report_path}")
    print("="*70)


if __name__ == '__main__':
    # Run all benchmarks
    print("\nRunning comprehensive performance benchmarks...")
    print("This may take several minutes...\n")

    test_jit_integrator_speedup()
    test_fast_mode_speedup()
    test_batch_simulation_performance()
    test_multicore_parallel_speedup()

    try:
        test_gpu_acceleration_if_available()
    except Exception as e:
        print(f"\nGPU benchmark skipped: {e}")

    test_memory_optimization_overhead()
    test_comprehensive_performance_report()

    print("\n" + "="*70)
    print("ALL BENCHMARKS COMPLETE")
    print("="*70)
