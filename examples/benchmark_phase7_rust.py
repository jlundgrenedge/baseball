"""
Phase 7 Benchmark: Rust (PyO3) vs Numba Trajectory Integration

Compares performance of the Rust-based trajectory integrator against
the existing Numba implementation.

Target: 2-3x speedup for batch operations.
"""

import numpy as np
import time
import sys
import os

# Add parent directory for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# ============================================================================
# Test Configuration
# ============================================================================

BATCH_SIZES = [10, 50, 100, 500, 1000]
WARMUP_ITERATIONS = 3
BENCHMARK_ITERATIONS = 5

# Standard trajectory parameters
DT = 0.01  # 10ms timestep (ultra-fast mode)
MAX_TIME = 10.0
GROUND_LEVEL = 0.0
AIR_DENSITY = 1.225  # kg/m³
CROSS_AREA = 0.00426  # m² (baseball)


def create_test_trajectories(n: int) -> tuple:
    """Create random initial states and spin parameters."""
    np.random.seed(42)
    
    # Initial states: [x, y, z, vx, vy, vz]
    # Typical batted ball: 35-50 m/s exit velocity, 10-35 degree launch angle
    exit_velocities = np.random.uniform(35, 50, n)  # m/s
    launch_angles = np.random.uniform(10, 35, n)  # degrees
    
    initial_states = np.zeros((n, 6))
    initial_states[:, 0] = 0.0  # x = 0
    initial_states[:, 1] = 0.0  # y = 0  
    initial_states[:, 2] = 1.0  # z = 1m (contact height)
    initial_states[:, 3] = exit_velocities * np.cos(np.radians(launch_angles))  # vx
    initial_states[:, 4] = 0.0  # vy = 0
    initial_states[:, 5] = exit_velocities * np.sin(np.radians(launch_angles))  # vz
    
    # Spin parameters: [spin_x, spin_y, spin_z, spin_rpm]
    spin_params = np.zeros((n, 4))
    spin_params[:, 0] = 0.0  # spin_x
    spin_params[:, 1] = 1.0  # spin_y (backspin axis)
    spin_params[:, 2] = 0.0  # spin_z
    spin_params[:, 3] = np.random.uniform(1500, 2500, n)  # RPM
    
    return initial_states, spin_params


def get_lookup_tables():
    """Get or create aerodynamic lookup tables."""
    from batted_ball.aerodynamics import get_lookup_tables as get_aero_tables
    return get_aero_tables()


def benchmark_numba_batch(initial_states, spin_params, cd_table, cl_table, iterations=5):
    """Benchmark the Numba implementation."""
    from batted_ball.integrator import calculate_trajectory_endpoints_batch
    from batted_ball.aerodynamics import aerodynamic_force_tuple_lookup
    
    times = []
    cd_base = 0.3  # Not used with lookup but required for interface
    
    for _ in range(iterations):
        start = time.perf_counter()
        landing_pos, landing_times, distances, apex_heights = calculate_trajectory_endpoints_batch(
            initial_states, DT, MAX_TIME, GROUND_LEVEL,
            spin_params, cd_base, AIR_DENSITY, CROSS_AREA,
            cd_table, cl_table, aerodynamic_force_tuple_lookup
        )
        elapsed = time.perf_counter() - start
        times.append(elapsed)
    
    return np.mean(times), np.std(times), landing_pos, distances


def benchmark_rust_batch(initial_states, spin_params, cd_table, cl_table, iterations=5):
    """Benchmark the Rust implementation."""
    try:
        import trajectory_rs
    except ImportError:
        print("❌ trajectory_rs not found. Build with: cd trajectory_rs && maturin develop --release")
        return None, None, None, None
    
    times = []
    
    for _ in range(iterations):
        start = time.perf_counter()
        landing_pos, landing_times, distances, apex_heights = trajectory_rs.integrate_trajectories_batch(
            initial_states, DT, MAX_TIME, GROUND_LEVEL,
            spin_params, AIR_DENSITY, CROSS_AREA,
            cd_table, cl_table
        )
        elapsed = time.perf_counter() - start
        times.append(elapsed)
    
    return np.mean(times), np.std(times), landing_pos, distances


def benchmark_single_trajectory():
    """Compare single trajectory integration."""
    print("\n" + "="*60)
    print("SINGLE TRAJECTORY BENCHMARK")
    print("="*60)
    
    cd_table, cl_table = get_lookup_tables()
    
    # Single trajectory
    initial_state = np.array([0.0, 0.0, 1.0, 40.0, 0.0, 20.0])  # x,y,z,vx,vy,vz
    spin_axis = np.array([0.0, 1.0, 0.0])
    spin_rpm = 2000.0
    
    # Warmup
    try:
        import trajectory_rs
        for _ in range(WARMUP_ITERATIONS):
            trajectory_rs.integrate_trajectory(
                initial_state, DT, MAX_TIME, GROUND_LEVEL,
                spin_axis, spin_rpm, AIR_DENSITY, CROSS_AREA,
                cd_table, cl_table
            )
    except ImportError:
        print("❌ trajectory_rs not available")
        return
    
    # Benchmark Rust
    rust_times = []
    for _ in range(20):
        start = time.perf_counter()
        pos_r, vel_r, time_r = trajectory_rs.integrate_trajectory(
            initial_state, DT, MAX_TIME, GROUND_LEVEL,
            spin_axis, spin_rpm, AIR_DENSITY, CROSS_AREA,
            cd_table, cl_table
        )
        rust_times.append(time.perf_counter() - start)
    
    # Benchmark Numba single trajectory
    from batted_ball.integrator import integrate_trajectory_lookup
    from batted_ball.aerodynamics import aerodynamic_force_tuple_lookup
    
    # Allocate buffers for Numba
    max_steps = int(MAX_TIME / DT) + 10
    times_buf = np.zeros(max_steps)
    positions_buf = np.zeros((max_steps, 3))
    velocities_buf = np.zeros((max_steps, 3))
    
    # Warmup Numba
    for _ in range(WARMUP_ITERATIONS):
        integrate_trajectory_lookup(
            initial_state, DT, MAX_TIME, GROUND_LEVEL,
            aerodynamic_force_tuple_lookup,
            times_buf, positions_buf, velocities_buf,
            cd_table, cl_table,
            0.0, 1.0, 0.0, spin_rpm, 0.3, AIR_DENSITY, CROSS_AREA
        )
    
    numba_times = []
    for _ in range(20):
        start = time.perf_counter()
        count = integrate_trajectory_lookup(
            initial_state, DT, MAX_TIME, GROUND_LEVEL,
            aerodynamic_force_tuple_lookup,
            times_buf, positions_buf, velocities_buf,
            cd_table, cl_table,
            0.0, 1.0, 0.0, spin_rpm, 0.3, AIR_DENSITY, CROSS_AREA
        )
        numba_times.append(time.perf_counter() - start)
    
    pos_n = positions_buf[:count]
    rust_mean = np.mean(rust_times) * 1000
    numba_mean = np.mean(numba_times) * 1000
    speedup = numba_mean / rust_mean
    
    print(f"\nSingle trajectory ({len(time_r)} steps):")
    print(f"  Rust:  {rust_mean:.3f} ms (±{np.std(rust_times)*1000:.3f})")
    print(f"  Numba: {numba_mean:.3f} ms (±{np.std(numba_times)*1000:.3f})")
    print(f"  Speedup: {speedup:.2f}x {'✅' if speedup > 1.0 else '❌'}")
    
    # Verify results match
    landing_dist_rust = np.sqrt(pos_r[-1, 0]**2 + pos_r[-1, 1]**2)
    landing_dist_numba = np.sqrt(pos_n[-1, 0]**2 + pos_n[-1, 1]**2)
    print(f"\n  Landing distance - Rust: {landing_dist_rust:.2f}m, Numba: {landing_dist_numba:.2f}m")
    
    return speedup


def benchmark_batch_trajectories():
    """Compare batch trajectory integration."""
    print("\n" + "="*60)
    print("BATCH TRAJECTORY BENCHMARK")
    print("="*60)
    
    cd_table, cl_table = get_lookup_tables()
    
    # Check Rust availability
    try:
        import trajectory_rs
        print(f"Rust threads: {trajectory_rs.get_num_threads()}")
    except ImportError:
        print("❌ trajectory_rs not available")
        return
    
    results = []
    
    for batch_size in BATCH_SIZES:
        print(f"\nBatch size: {batch_size}")
        
        initial_states, spin_params = create_test_trajectories(batch_size)
        
        # Warmup both implementations
        for _ in range(WARMUP_ITERATIONS):
            benchmark_numba_batch(initial_states, spin_params, cd_table, cl_table, iterations=1)
            benchmark_rust_batch(initial_states, spin_params, cd_table, cl_table, iterations=1)
        
        # Benchmark
        numba_mean, numba_std, numba_pos, numba_dist = benchmark_numba_batch(
            initial_states, spin_params, cd_table, cl_table, iterations=BENCHMARK_ITERATIONS
        )
        rust_mean, rust_std, rust_pos, rust_dist = benchmark_rust_batch(
            initial_states, spin_params, cd_table, cl_table, iterations=BENCHMARK_ITERATIONS
        )
        
        if rust_mean is None:
            continue
        
        speedup = numba_mean / rust_mean
        traj_per_sec_rust = batch_size / rust_mean
        traj_per_sec_numba = batch_size / numba_mean
        
        print(f"  Numba: {numba_mean*1000:.2f} ms (±{numba_std*1000:.2f}) | {traj_per_sec_numba:.0f} traj/sec")
        print(f"  Rust:  {rust_mean*1000:.2f} ms (±{rust_std*1000:.2f}) | {traj_per_sec_rust:.0f} traj/sec")
        print(f"  Speedup: {speedup:.2f}x {'✅' if speedup > 1.0 else '❌'}")
        
        # Verify results are close
        if numba_dist is not None and rust_dist is not None:
            max_diff = np.max(np.abs(numba_dist - rust_dist))
            print(f"  Max distance diff: {max_diff:.4f}m {'✅' if max_diff < 1.0 else '⚠️'}")
        
        results.append({
            'batch_size': batch_size,
            'numba_ms': numba_mean * 1000,
            'rust_ms': rust_mean * 1000,
            'speedup': speedup,
            'rust_traj_per_sec': traj_per_sec_rust,
        })
    
    return results


def verify_physics_accuracy():
    """Verify Rust produces same results as Numba."""
    print("\n" + "="*60)
    print("PHYSICS ACCURACY VERIFICATION")
    print("="*60)
    
    cd_table, cl_table = get_lookup_tables()
    
    try:
        import trajectory_rs
    except ImportError:
        print("❌ trajectory_rs not available")
        return False
    
    # Test trajectory
    initial_state = np.array([0.0, 0.0, 1.0, 44.7, 0.0, 22.0])  # ~100mph, 26deg
    spin_axis = np.array([0.0, 1.0, 0.0])
    spin_rpm = 2200.0
    
    # Rust trajectory
    pos_r, vel_r, times_r = trajectory_rs.integrate_trajectory(
        initial_state, DT, MAX_TIME, GROUND_LEVEL,
        spin_axis, spin_rpm, AIR_DENSITY, CROSS_AREA,
        cd_table, cl_table
    )
    
    # Numba trajectory - use buffered version
    from batted_ball.integrator import integrate_trajectory_lookup
    from batted_ball.aerodynamics import aerodynamic_force_tuple_lookup
    
    # Allocate buffers for Numba
    max_steps = int(MAX_TIME / DT) + 10
    times_buf = np.zeros(max_steps)
    positions_buf = np.zeros((max_steps, 3))
    velocities_buf = np.zeros((max_steps, 3))
    
    count = integrate_trajectory_lookup(
        initial_state, DT, MAX_TIME, GROUND_LEVEL,
        aerodynamic_force_tuple_lookup,
        times_buf, positions_buf, velocities_buf,
        cd_table, cl_table,
        0.0, 1.0, 0.0, spin_rpm, 0.3, AIR_DENSITY, CROSS_AREA
    )
    times_n = times_buf[:count]
    pos_n = positions_buf[:count]
    vel_n = velocities_buf[:count]
    
    # Compare key metrics
    rust_distance = np.sqrt(pos_r[-1, 0]**2 + pos_r[-1, 1]**2)
    numba_distance = np.sqrt(pos_n[-1, 0]**2 + pos_n[-1, 1]**2)
    rust_apex = np.max(pos_r[:, 2])
    numba_apex = np.max(pos_n[:, 2])
    rust_time = times_r[-1]
    numba_time = times_n[-1]
    
    print(f"\nMetric          Rust        Numba       Diff")
    print(f"Distance (m):   {rust_distance:8.2f}    {numba_distance:8.2f}    {abs(rust_distance-numba_distance):.4f}")
    print(f"Apex (m):       {rust_apex:8.2f}    {numba_apex:8.2f}    {abs(rust_apex-numba_apex):.4f}")
    print(f"Flight time:    {rust_time:8.4f}    {numba_time:8.4f}    {abs(rust_time-numba_time):.6f}")
    print(f"Steps:          {len(times_r):8d}    {len(times_n):8d}")
    
    # Check tolerance (should be within 1m for distance, 0.5m for apex)
    distance_ok = abs(rust_distance - numba_distance) < 1.0
    apex_ok = abs(rust_apex - numba_apex) < 0.5
    time_ok = abs(rust_time - numba_time) < 0.1
    
    all_ok = distance_ok and apex_ok and time_ok
    print(f"\nPhysics Match: {'✅ PASS' if all_ok else '❌ FAIL'}")
    
    return all_ok


def main():
    """Run all benchmarks."""
    print("="*60)
    print("PHASE 7 BENCHMARK: Rust (PyO3/Rayon) vs Numba")
    print("="*60)
    
    # Verify physics first
    physics_ok = verify_physics_accuracy()
    if not physics_ok:
        print("\n⚠️ Physics accuracy check failed - results may not be comparable")
    
    # Single trajectory benchmark
    single_speedup = benchmark_single_trajectory()
    
    # Batch benchmark
    batch_results = benchmark_batch_trajectories()
    
    # Summary
    print("\n" + "="*60)
    print("SUMMARY")
    print("="*60)
    
    if batch_results:
        avg_speedup = np.mean([r['speedup'] for r in batch_results])
        max_traj_per_sec = max([r['rust_traj_per_sec'] for r in batch_results])
        
        print(f"\nSingle trajectory speedup: {single_speedup:.2f}x")
        print(f"Average batch speedup: {avg_speedup:.2f}x")
        print(f"Max throughput: {max_traj_per_sec:.0f} trajectories/sec")
        
        if avg_speedup >= 2.0:
            print(f"\n✅ TARGET MET: {avg_speedup:.1f}x speedup (target: 2-3x)")
        elif avg_speedup >= 1.5:
            print(f"\n⚠️ PARTIAL: {avg_speedup:.1f}x speedup (target: 2-3x)")
        else:
            print(f"\n❌ BELOW TARGET: {avg_speedup:.1f}x speedup (target: 2-3x)")
    
    return physics_ok and batch_results is not None


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
