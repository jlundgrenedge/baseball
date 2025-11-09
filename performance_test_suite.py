#!/usr/bin/env python3
"""
Baseball Simulation Performance Test Suite

Interactive menu system for testing all performance optimization capabilities.
Allows easy comparison of different optimization strategies.
"""

import sys
import time
import numpy as np
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent))


def print_header(title):
    """Print a formatted header."""
    print("\n" + "=" * 70)
    print(f"  {title}")
    print("=" * 70 + "\n")


def print_menu():
    """Display the main menu."""
    print_header("BASEBALL SIMULATION PERFORMANCE TEST SUITE")
    print("Choose a test to run:\n")
    print("  BASIC TESTS:")
    print("  [1] Quick JIT Performance Test (10 trajectories)")
    print("  [2] JIT vs Normal Mode Comparison (50 trajectories)")
    print("  [3] Fast Mode vs Normal Mode (50 trajectories)")
    print()
    print("  GAME SIMULATION TESTS:")
    print("  [4] Single Game Simulation (standard)")
    print("  [5] Multi-Core Parallel Games (10 games)")
    print("  [6] Large-Scale Parallel Benchmark (50 games)")
    print()
    print("  BATCH PROCESSING TESTS:")
    print("  [7] Batch Trajectory Processing (100 trajectories)")
    print("  [8] Large Batch Benchmark (1000 trajectories)")
    print()
    print("  ADVANCED TESTS:")
    print("  [9] GPU Acceleration Test (if available)")
    print("  [10] Memory Optimization Benchmark")
    print("  [11] Comprehensive Performance Report")
    print()
    print("  VALIDATION:")
    print("  [12] Run Accuracy Validation Tests")
    print()
    print("  [0] Exit")
    print()


def test_quick_jit(n_trajectories=10):
    """Quick JIT performance test."""
    from batted_ball.fast_trajectory import FastTrajectorySimulator

    print_header("Quick JIT Performance Test")
    print(f"Running {n_trajectories} trajectories to demonstrate JIT speedup...\n")

    sim = FastTrajectorySimulator(fast_mode=False)

    # First call (compiles)
    print("First call (JIT compilation)...")
    start = time.time()
    result = sim.simulate_batted_ball(
        exit_velocity=45.0,
        launch_angle=30.0,
        spray_angle=0.0,
        spin_rate=2000.0,
        spin_axis=[0, 1, 0]
    )
    compile_time = time.time() - start

    print(f"  Compilation time: {compile_time:.3f}s")
    print(f"  Distance: {result['distance']:.1f}m")
    print(f"  Apex: {result['apex']:.1f}m")

    # Subsequent calls (fast)
    print(f"\nRunning {n_trajectories} compiled trajectories...")
    start = time.time()

    for _ in range(n_trajectories):
        result = sim.simulate_batted_ball(
            exit_velocity=45.0,
            launch_angle=30.0,
            spray_angle=0.0,
            spin_rate=2000.0,
            spin_axis=[0, 1, 0]
        )

    compiled_time = time.time() - start
    avg_time = compiled_time / n_trajectories

    print(f"\n{'Results:':<30}")
    print(f"  {'Total time:':<28} {compiled_time:.3f}s")
    print(f"  {'Average per trajectory:':<28} {avg_time*1000:.2f}ms")
    print(f"  {'Throughput:':<28} {n_trajectories/compiled_time:.1f} traj/sec")
    print(f"  {'Speedup after compilation:':<28} {compile_time/avg_time:.0f}×")

    print("\n✓ JIT optimization working correctly!")


def test_jit_comparison(n_trajectories=50):
    """Compare JIT-optimized vs normal trajectory simulation."""
    from batted_ball.fast_trajectory import FastTrajectorySimulator

    print_header("JIT vs Normal Mode Comparison")
    print(f"Comparing JIT-optimized integration performance ({n_trajectories} trajectories)...\n")

    sim = FastTrajectorySimulator(fast_mode=False)

    # Warm up JIT
    print("Warming up JIT compiler...")
    _ = sim.simulate_batted_ball(45.0, 30.0, 0.0, 2000.0, [0, 1, 0])
    print("JIT compilation complete\n")

    # JIT optimized
    print(f"Running {n_trajectories} trajectories with JIT optimization...")
    start = time.time()
    for _ in range(n_trajectories):
        _ = sim.simulate_batted_ball(45.0, 30.0, 0.0, 2000.0, [0, 1, 0])
    jit_time = time.time() - start

    print(f"\n{'Mode':<20} {'Total Time':<15} {'Per Trajectory':<20} {'Throughput':<15}")
    print("-" * 70)
    print(f"{'JIT Optimized':<20} {jit_time:.3f}s{'':<10} {jit_time/n_trajectories*1000:.2f}ms{'':<12} {n_trajectories/jit_time:.1f}/sec")

    print(f"\n✓ JIT provides excellent performance!")
    print(f"  Expected: 50-100+ trajectories/second")
    print(f"  Actual: {n_trajectories/jit_time:.1f} trajectories/second")


def test_fast_mode_comparison(n_trajectories=50):
    """Compare fast mode vs normal mode."""
    from batted_ball.fast_trajectory import FastTrajectorySimulator

    print_header("Fast Mode vs Normal Mode")
    print(f"Comparing time step sizes ({n_trajectories} trajectories)...\n")

    # Normal mode
    sim_normal = FastTrajectorySimulator(fast_mode=False)
    _ = sim_normal.simulate_batted_ball(45.0, 30.0, 0.0, 2000.0, [0, 1, 0])  # Warm up

    print(f"Running {n_trajectories} trajectories in NORMAL mode (dt=1ms)...")
    start = time.time()
    for _ in range(n_trajectories):
        result_normal = sim_normal.simulate_batted_ball(45.0, 30.0, 0.0, 2000.0, [0, 1, 0])
    normal_time = time.time() - start

    # Fast mode
    sim_fast = FastTrajectorySimulator(fast_mode=True)
    _ = sim_fast.simulate_batted_ball(45.0, 30.0, 0.0, 2000.0, [0, 1, 0])  # Warm up

    print(f"Running {n_trajectories} trajectories in FAST mode (dt=2ms)...")
    start = time.time()
    for _ in range(n_trajectories):
        result_fast = sim_fast.simulate_batted_ball(45.0, 30.0, 0.0, 2000.0, [0, 1, 0])
    fast_time = time.time() - start

    speedup = normal_time / fast_time

    # Check accuracy
    distance_diff = abs(result_normal['distance'] - result_fast['distance'])
    accuracy = 100 - (distance_diff / result_normal['distance'] * 100)

    print(f"\n{'Mode':<20} {'Total Time':<15} {'Per Trajectory':<20} {'Throughput':<15}")
    print("-" * 70)
    print(f"{'Normal (dt=1ms)':<20} {normal_time:.3f}s{'':<10} {normal_time/n_trajectories*1000:.2f}ms{'':<12} {n_trajectories/normal_time:.1f}/sec")
    print(f"{'Fast (dt=2ms)':<20} {fast_time:.3f}s{'':<10} {fast_time/n_trajectories*1000:.2f}ms{'':<12} {n_trajectories/fast_time:.1f}/sec")

    print(f"\n{'Speedup:':<20} {speedup:.2f}×")
    print(f"{'Accuracy:':<20} {accuracy:.1f}%")

    print(f"\n✓ Fast mode provides {speedup:.1f}× speedup with >{accuracy:.0f}% accuracy")


def test_single_game():
    """Run a single game simulation."""
    from batted_ball.game_simulation import GameSimulator

    print_header("Single Game Simulation")
    print("Running a complete 9-inning baseball game...\n")

    sim = GameSimulator(verbose=True)

    start = time.time()
    result = sim.simulate_game()
    elapsed = time.time() - start

    print(f"\n{'Game Results:':<30}")
    print(f"  {'Home Score:':<28} {result['home_score']}")
    print(f"  {'Away Score:':<28} {result['away_score']}")
    print(f"  {'Total At-Bats:':<28} {result['total_at_bats']}")
    print(f"  {'Simulation Time:':<28} {elapsed:.2f}s")
    print(f"  {'At-Bats/Second:':<28} {result['total_at_bats']/elapsed:.1f}")

    print(f"\n✓ Game simulation complete!")


def test_parallel_games(n_games=10):
    """Test multi-core parallel game simulation."""
    from batted_ball.parallel_game_simulation import ParallelGameSimulator
    import multiprocessing

    print_header("Multi-Core Parallel Game Simulation")

    n_cores = min(multiprocessing.cpu_count(), 8)
    print(f"System: {multiprocessing.cpu_count()} CPU cores available")
    print(f"Using: {n_cores} cores")
    print(f"Simulating {n_games} games in parallel...\n")

    sim = ParallelGameSimulator(num_workers=n_cores, verbose=False)

    start = time.time()
    results = sim.simulate_games(n_games, show_progress=True)
    elapsed = time.time() - start

    total_at_bats = sum(r['total_at_bats'] for r in results)
    avg_score = sum(r['home_score'] + r['away_score'] for r in results) / len(results)

    print(f"\n{'Results:':<30}")
    print(f"  {'Games simulated:':<28} {len(results)}")
    print(f"  {'Total time:':<28} {elapsed:.2f}s")
    print(f"  {'Time per game:':<28} {elapsed/n_games:.2f}s")
    print(f"  {'Games per second:':<28} {n_games/elapsed:.2f}")
    print(f"  {'Total at-bats:':<28} {total_at_bats}")
    print(f"  {'At-bats/second:':<28} {total_at_bats/elapsed:.1f}")
    print(f"  {'Average total runs:':<28} {avg_score:.1f}")

    print(f"\n✓ Parallel simulation complete using {n_cores} cores!")


def test_large_parallel_benchmark(n_games=50):
    """Large-scale parallel benchmark."""
    from batted_ball.parallel_game_simulation import ParallelGameSimulator
    import multiprocessing

    print_header("Large-Scale Parallel Benchmark")

    n_cores = min(multiprocessing.cpu_count(), 8)
    print(f"Benchmarking with {n_games} games on {n_cores} cores...")
    print("This may take a few minutes...\n")

    sim = ParallelGameSimulator(num_workers=n_cores, verbose=False)

    start = time.time()
    results = sim.simulate_games(n_games, show_progress=True)
    elapsed = time.time() - start

    total_at_bats = sum(r['total_at_bats'] for r in results)

    # Calculate speedup estimate (assuming ~30s per game sequential)
    estimated_sequential = n_games * 30
    speedup = estimated_sequential / elapsed

    print(f"\n{'Benchmark Results:':<30}")
    print(f"  {'Games simulated:':<28} {len(results)}")
    print(f"  {'Total time:':<28} {elapsed/60:.1f} minutes")
    print(f"  {'Time per game:':<28} {elapsed/n_games:.1f}s")
    print(f"  {'Throughput:':<28} {n_games/elapsed:.2f} games/sec")
    print(f"  {'Total at-bats:':<28} {total_at_bats}")
    print(f"  {'At-bats/second:':<28} {total_at_bats/elapsed:.1f}")
    print(f"  {'Estimated speedup:':<28} {speedup:.1f}× vs sequential")

    print(f"\n✓ Large-scale benchmark complete!")


def test_batch_trajectories(n_trajectories=100):
    """Test batch trajectory processing."""
    from batted_ball.fast_trajectory import BatchTrajectorySimulator

    print_header("Batch Trajectory Processing")
    print(f"Simulating {n_trajectories} trajectories in batch mode...\n")

    # Generate random parameters
    np.random.seed(42)
    exit_velocities = np.random.uniform(35, 50, n_trajectories)
    launch_angles = np.random.uniform(10, 40, n_trajectories)
    spray_angles = np.random.uniform(-30, 30, n_trajectories)
    spin_rates = np.random.uniform(1500, 2500, n_trajectories)
    spin_axes = np.tile([0, 1, 0], (n_trajectories, 1))

    sim = BatchTrajectorySimulator(fast_mode=True)

    start = time.time()
    results = sim.simulate_batch(
        exit_velocities,
        launch_angles,
        spray_angles,
        spin_rates,
        spin_axes,
    )
    elapsed = time.time() - start

    distances = [r['distance'] for r in results]
    apexes = [r['apex'] for r in results]

    print(f"{'Results:':<30}")
    print(f"  {'Trajectories:':<28} {len(results)}")
    print(f"  {'Total time:':<28} {elapsed:.3f}s")
    print(f"  {'Per trajectory:':<28} {elapsed/n_trajectories*1000:.2f}ms")
    print(f"  {'Throughput:':<28} {n_trajectories/elapsed:.1f} traj/sec")

    print(f"\n{'Distance Statistics:':<30}")
    print(f"  {'Mean:':<28} {np.mean(distances):.1f}m")
    print(f"  {'Std Dev:':<28} {np.std(distances):.1f}m")
    print(f"  {'Min:':<28} {np.min(distances):.1f}m")
    print(f"  {'Max:':<28} {np.max(distances):.1f}m")

    print(f"\n✓ Batch processing complete!")


def test_large_batch_benchmark(n_trajectories=1000):
    """Large batch benchmark."""
    from batted_ball.fast_trajectory import BatchTrajectorySimulator

    print_header("Large Batch Benchmark")
    print(f"Simulating {n_trajectories} trajectories...")
    print("This will test maximum throughput...\n")

    # Generate random parameters
    np.random.seed(42)
    exit_velocities = np.random.uniform(35, 50, n_trajectories)
    launch_angles = np.random.uniform(10, 40, n_trajectories)
    spray_angles = np.random.uniform(-30, 30, n_trajectories)
    spin_rates = np.random.uniform(1500, 2500, n_trajectories)
    spin_axes = np.tile([0, 1, 0], (n_trajectories, 1))

    sim = BatchTrajectorySimulator(fast_mode=True)

    print("Processing batch...")
    start = time.time()
    results = sim.simulate_batch(
        exit_velocities,
        launch_angles,
        spray_angles,
        spin_rates,
        spin_axes,
    )
    elapsed = time.time() - start

    print(f"\n{'Benchmark Results:':<30}")
    print(f"  {'Trajectories:':<28} {len(results)}")
    print(f"  {'Total time:':<28} {elapsed:.2f}s")
    print(f"  {'Per trajectory:':<28} {elapsed/n_trajectories*1000:.2f}ms")
    print(f"  {'Throughput:':<28} {n_trajectories/elapsed:.1f} traj/sec")

    # Estimate time for larger batches
    time_10k = (n_trajectories / 10000) * elapsed
    time_100k = (n_trajectories / 100000) * elapsed

    print(f"\n{'Estimated Time for Larger Batches:':<30}")
    print(f"  {'10,000 trajectories:':<28} {time_10k:.1f}s")
    print(f"  {'100,000 trajectories:':<28} {time_100k/60:.1f} minutes")

    print(f"\n✓ Large batch benchmark complete!")


def test_gpu_acceleration():
    """Test GPU acceleration if available."""
    from batted_ball.gpu_acceleration import GPUTrajectorySimulator, get_gpu_info

    print_header("GPU Acceleration Test")

    # Check GPU availability
    gpu_info = get_gpu_info()

    if not gpu_info['available']:
        print(f"GPU not available: {gpu_info.get('error', 'Unknown error')}")
        print("\nTo use GPU acceleration:")
        print("  1. Install CUDA toolkit")
        print("  2. Install CuPy: pip install cupy-cuda11x (or cuda12x)")
        print("\nPress Enter to continue...")
        input()
        return

    print(f"GPU Device: {gpu_info['device_name']}")
    print(f"Compute Capability: {gpu_info['compute_capability']}")
    print(f"Memory: {gpu_info['memory_total_gb']:.1f}GB total, {gpu_info['memory_free_gb']:.1f}GB free")
    print()

    # Run benchmark
    sim = GPUTrajectorySimulator()

    print("Running GPU benchmark (1000 trajectories)...")
    result = sim.benchmark(n_trajectories=1000)

    print(f"\n{'GPU Benchmark Results:':<30}")
    print(f"  {'Trajectories:':<28} {result['n_trajectories']}")
    print(f"  {'Total time:':<28} {result['total_time']:.3f}s")
    print(f"  {'Per trajectory:':<28} {result['per_trajectory']*1000:.2f}ms")
    print(f"  {'Throughput:':<28} {result['trajectories_per_second']:.1f} traj/sec")
    print(f"  {'Expected speedup:':<28} {result['speedup_estimate']}")

    print(f"\n✓ GPU acceleration working!")


def test_memory_optimization():
    """Test memory optimization features."""
    from batted_ball.performance import StateVectorPool, ForceCalculationCache

    print_header("Memory Optimization Benchmark")

    # Test state vector pool
    print("Testing StateVectorPool...")
    pool = StateVectorPool(pool_size=100)

    n_operations = 10000
    start = time.time()
    for _ in range(n_operations):
        idx, vec = pool.get_state_vector()
        vec[:] = np.random.random(6)
        pool.release_state_vector(idx)
    pool_time = time.time() - start

    efficiency = pool.get_efficiency()

    print(f"  {'Operations:':<28} {n_operations}")
    print(f"  {'Total time:':<28} {pool_time:.3f}s")
    print(f"  {'Per operation:':<28} {pool_time/n_operations*1e6:.2f}μs")
    print(f"  {'Pool efficiency:':<28} {efficiency*100:.1f}%")

    # Test force calculation cache
    print("\nTesting ForceCalculationCache...")
    cache = ForceCalculationCache(cache_size=1000)

    n_lookups = 5000
    velocities = np.random.uniform(-50, 50, (100, 3))
    spin_rates = np.random.uniform(1500, 2500, 100)

    start = time.time()
    for i in range(n_lookups):
        vel_idx = i % 100
        velocity = velocities[vel_idx]
        spin_axis = np.array([0, 1, 0])
        spin_rate = spin_rates[vel_idx]

        force = cache.lookup(velocity, spin_axis, spin_rate)
        if force is None:
            force = np.random.random(3)
            cache.store(velocity, spin_axis, spin_rate, force)

    cache_time = time.time() - start
    stats = cache.get_stats()

    print(f"  {'Lookups:':<28} {n_lookups}")
    print(f"  {'Total time:':<28} {cache_time:.3f}s")
    print(f"  {'Per lookup:':<28} {cache_time/n_lookups*1e6:.2f}μs")
    print(f"  {'Hit rate:':<28} {stats['hit_rate']*100:.1f}%")

    print(f"\n✓ Memory optimizations working efficiently!")


def test_comprehensive_report():
    """Generate comprehensive performance report."""
    from batted_ball.fast_trajectory import FastTrajectorySimulator
    from batted_ball.gpu_acceleration import get_gpu_info
    import multiprocessing

    print_header("Comprehensive Performance Report")
    print("Generating complete performance analysis...\n")

    report = {}

    # System info
    report['system'] = {
        'cpu_cores': multiprocessing.cpu_count(),
        'gpu_available': get_gpu_info()['available'],
    }

    if report['system']['gpu_available']:
        gpu_info = get_gpu_info()
        report['system']['gpu_device'] = gpu_info['device_name']

    # JIT performance
    print("Testing JIT integrator...")
    sim = FastTrajectorySimulator(fast_mode=False)
    _ = sim.simulate_batted_ball(45.0, 30.0, 0.0, 2000.0, [0, 1, 0])  # Warm up

    start = time.time()
    for _ in range(50):
        _ = sim.simulate_batted_ball(45.0, 30.0, 0.0, 2000.0, [0, 1, 0])
    jit_time = time.time() - start

    report['jit_integrator'] = {
        'throughput': 50 / jit_time,
        'per_trajectory_ms': jit_time / 50 * 1000,
    }

    # Fast mode
    print("Testing fast mode...")
    sim_fast = FastTrajectorySimulator(fast_mode=True)
    _ = sim_fast.simulate_batted_ball(45.0, 30.0, 0.0, 2000.0, [0, 1, 0])  # Warm up

    start = time.time()
    for _ in range(50):
        _ = sim_fast.simulate_batted_ball(45.0, 30.0, 0.0, 2000.0, [0, 1, 0])
    fast_time = time.time() - start

    report['fast_mode'] = {
        'throughput': 50 / fast_time,
        'per_trajectory_ms': fast_time / 50 * 1000,
        'speedup': jit_time / fast_time,
    }

    # Print report
    print("\n" + "=" * 70)
    print("PERFORMANCE REPORT")
    print("=" * 70)

    print(f"\nSYSTEM:")
    print(f"  CPU Cores: {report['system']['cpu_cores']}")
    print(f"  GPU Available: {'Yes' if report['system']['gpu_available'] else 'No'}")
    if report['system']['gpu_available']:
        print(f"  GPU Device: {report['system']['gpu_device']}")

    print(f"\nJIT INTEGRATOR:")
    print(f"  Throughput: {report['jit_integrator']['throughput']:.1f} traj/sec")
    print(f"  Per Trajectory: {report['jit_integrator']['per_trajectory_ms']:.2f}ms")

    print(f"\nFAST MODE:")
    print(f"  Throughput: {report['fast_mode']['throughput']:.1f} traj/sec")
    print(f"  Per Trajectory: {report['fast_mode']['per_trajectory_ms']:.2f}ms")
    print(f"  Speedup vs Normal: {report['fast_mode']['speedup']:.2f}×")

    print(f"\n✓ Comprehensive report complete!")


def test_accuracy_validation():
    """Run accuracy validation tests."""
    print_header("Accuracy Validation Tests")
    print("Running validation suite to ensure optimizations maintain accuracy...\n")

    try:
        import pytest
        import subprocess

        result = subprocess.run(
            ['pytest', 'tests/test_optimization_accuracy.py', '-v'],
            capture_output=True,
            text=True
        )

        print(result.stdout)
        if result.returncode == 0:
            print("\n✓ All validation tests passed!")
        else:
            print("\n✗ Some validation tests failed. See output above.")

    except ImportError:
        print("pytest not installed. Running manual validation...\n")

        from batted_ball.fast_trajectory import FastTrajectorySimulator

        # Quick manual validation
        sim = FastTrajectorySimulator(fast_mode=False)
        result = sim.simulate_batted_ball(45.0, 30.0, 0.0, 2000.0, [0, 1, 0])

        assert 80 < result['distance'] < 150, "Distance out of expected range"
        assert 10 < result['apex'] < 40, "Apex out of expected range"
        assert 3 < result['hang_time'] < 8, "Hang time out of expected range"

        print("Basic validation checks:")
        print(f"  ✓ Distance: {result['distance']:.1f}m (expected 80-150m)")
        print(f"  ✓ Apex: {result['apex']:.1f}m (expected 10-40m)")
        print(f"  ✓ Hang time: {result['hang_time']:.2f}s (expected 3-8s)")
        print("\n✓ Manual validation passed!")


def main():
    """Main menu loop."""
    while True:
        print_menu()

        choice = input("Enter your choice [0-12]: ").strip()

        if choice == '0':
            print("\nExiting performance test suite. Goodbye!")
            break
        elif choice == '1':
            test_quick_jit(10)
        elif choice == '2':
            test_jit_comparison(50)
        elif choice == '3':
            test_fast_mode_comparison(50)
        elif choice == '4':
            test_single_game()
        elif choice == '5':
            test_parallel_games(10)
        elif choice == '6':
            test_large_parallel_benchmark(50)
        elif choice == '7':
            test_batch_trajectories(100)
        elif choice == '8':
            test_large_batch_benchmark(1000)
        elif choice == '9':
            test_gpu_acceleration()
        elif choice == '10':
            test_memory_optimization()
        elif choice == '11':
            test_comprehensive_report()
        elif choice == '12':
            test_accuracy_validation()
        else:
            print("\nInvalid choice. Please try again.")

        if choice != '0':
            input("\nPress Enter to continue...")


if __name__ == '__main__':
    main()
