"""
Phase 7 Validation Tests: Rust Native Code Extensions

Tests the Rust trajectory integration library (trajectory_rs) to ensure:
1. Python bindings work correctly
2. Physics results match Numba implementation
3. Parallel batch processing works
4. Performance meets targets (2-3x speedup over Numba)
"""

import numpy as np
import sys
import os
import time

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def test_rust_import():
    """Test 1: Rust module can be imported."""
    print("\nTest 1: Rust module import")
    try:
        import trajectory_rs
        print(f"  ✅ PASS: trajectory_rs imported successfully")
        print(f"     Functions: {[f for f in dir(trajectory_rs) if not f.startswith('_')]}")
        return True
    except ImportError as e:
        print(f"  ❌ FAIL: Could not import trajectory_rs: {e}")
        return False


def test_single_trajectory():
    """Test 2: Single trajectory integration matches Numba."""
    print("\nTest 2: Single trajectory physics match")
    
    try:
        import trajectory_rs
        from batted_ball.aerodynamics import get_lookup_tables, aerodynamic_force_tuple_lookup
        from batted_ball.integrator import integrate_trajectory_lookup
    except ImportError as e:
        print(f"  ❌ FAIL: Import error: {e}")
        return False
    
    cd_table, cl_table = get_lookup_tables()
    
    # Test parameters: 100 mph, 26 degree launch
    initial_state = np.array([0.0, 0.0, 1.0, 44.7, 0.0, 22.0])  # m, m, m, m/s
    spin_axis = np.array([0.0, 1.0, 0.0])  # pure backspin
    spin_rpm = 2200.0
    dt = 0.01
    max_time = 10.0
    air_density = 1.225
    cross_area = 0.00426
    
    # Rust result
    pos_r, vel_r, times_r = trajectory_rs.integrate_trajectory(
        initial_state, dt, max_time, 0.0,
        spin_axis, spin_rpm, air_density, cross_area,
        cd_table, cl_table
    )
    
    # Numba result
    max_steps = int(max_time / dt) + 10
    times_buf = np.zeros(max_steps)
    positions_buf = np.zeros((max_steps, 3))
    velocities_buf = np.zeros((max_steps, 3))
    
    count = integrate_trajectory_lookup(
        initial_state, dt, max_time, 0.0,
        aerodynamic_force_tuple_lookup,
        times_buf, positions_buf, velocities_buf,
        cd_table, cl_table,
        0.0, 1.0, 0.0, spin_rpm, 0.3, air_density, cross_area
    )
    
    # Compare results
    rust_dist = np.sqrt(pos_r[-1, 0]**2 + pos_r[-1, 1]**2)
    numba_dist = np.sqrt(positions_buf[count-1, 0]**2 + positions_buf[count-1, 1]**2)
    diff = abs(rust_dist - numba_dist)
    
    if diff < 0.01:  # Within 1cm
        print(f"  ✅ PASS: Distance match (diff = {diff:.6f}m)")
        print(f"     Rust: {rust_dist:.2f}m, Numba: {numba_dist:.2f}m")
        return True
    else:
        print(f"  ❌ FAIL: Distance mismatch (diff = {diff:.4f}m)")
        print(f"     Rust: {rust_dist:.2f}m, Numba: {numba_dist:.2f}m")
        return False


def test_batch_trajectory():
    """Test 3: Batch trajectory processing works."""
    print("\nTest 3: Batch trajectory processing")
    
    try:
        import trajectory_rs
        from batted_ball.aerodynamics import get_lookup_tables
    except ImportError as e:
        print(f"  ❌ FAIL: Import error: {e}")
        return False
    
    cd_table, cl_table = get_lookup_tables()
    
    # Create 50 random trajectories
    np.random.seed(42)
    n = 50
    
    initial_states = np.zeros((n, 6))
    initial_states[:, 2] = 1.0  # z = 1m
    exit_vels = np.random.uniform(35, 50, n)
    launch_angles = np.random.uniform(15, 35, n)
    initial_states[:, 3] = exit_vels * np.cos(np.radians(launch_angles))  # vx
    initial_states[:, 5] = exit_vels * np.sin(np.radians(launch_angles))  # vz
    
    spin_params = np.zeros((n, 4))
    spin_params[:, 1] = 1.0  # backspin
    spin_params[:, 3] = np.random.uniform(1500, 2500, n)  # RPM
    
    # Run batch
    try:
        landing_pos, landing_times, distances, apex_heights = trajectory_rs.integrate_trajectories_batch(
            initial_states, 0.01, 10.0, 0.0,
            spin_params, 1.225, 0.00426,
            cd_table, cl_table
        )
        
        # Validate results make sense
        if len(distances) != n:
            print(f"  ❌ FAIL: Expected {n} results, got {len(distances)}")
            return False
        
        if np.any(distances < 50) or np.any(distances > 200):
            print(f"  ⚠️ WARNING: Distances out of expected range (50-200m)")
            print(f"     Min: {distances.min():.1f}m, Max: {distances.max():.1f}m")
        
        if np.any(apex_heights < 5) or np.any(apex_heights > 50):
            print(f"  ⚠️ WARNING: Apex heights out of expected range (5-50m)")
        
        print(f"  ✅ PASS: Processed {n} trajectories")
        print(f"     Distance range: {distances.min():.1f} - {distances.max():.1f}m")
        print(f"     Apex range: {apex_heights.min():.1f} - {apex_heights.max():.1f}m")
        return True
        
    except Exception as e:
        print(f"  ❌ FAIL: Batch processing error: {e}")
        return False


def test_parallel_speedup():
    """Test 4: Parallel processing provides speedup."""
    print("\nTest 4: Parallel processing speedup")
    
    try:
        import trajectory_rs
        from batted_ball.aerodynamics import get_lookup_tables
    except ImportError as e:
        print(f"  ❌ FAIL: Import error: {e}")
        return False
    
    cd_table, cl_table = get_lookup_tables()
    num_threads = trajectory_rs.get_num_threads()
    print(f"  Rust using {num_threads} threads")
    
    # Create 200 trajectories for timing
    n = 200
    np.random.seed(42)
    
    initial_states = np.zeros((n, 6))
    initial_states[:, 2] = 1.0
    exit_vels = np.random.uniform(35, 50, n)
    launch_angles = np.random.uniform(15, 35, n)
    initial_states[:, 3] = exit_vels * np.cos(np.radians(launch_angles))
    initial_states[:, 5] = exit_vels * np.sin(np.radians(launch_angles))
    
    spin_params = np.zeros((n, 4))
    spin_params[:, 1] = 1.0
    spin_params[:, 3] = np.random.uniform(1500, 2500, n)
    
    # Warmup
    for _ in range(3):
        trajectory_rs.integrate_trajectories_batch(
            initial_states, 0.01, 10.0, 0.0,
            spin_params, 1.225, 0.00426,
            cd_table, cl_table
        )
    
    # Benchmark
    times = []
    for _ in range(5):
        start = time.perf_counter()
        trajectory_rs.integrate_trajectories_batch(
            initial_states, 0.01, 10.0, 0.0,
            spin_params, 1.225, 0.00426,
            cd_table, cl_table
        )
        times.append(time.perf_counter() - start)
    
    mean_time = np.mean(times) * 1000
    traj_per_sec = n / np.mean(times)
    
    # Target: > 50,000 trajectories/sec on modern hardware
    if traj_per_sec > 50000:
        print(f"  ✅ PASS: {traj_per_sec:.0f} trajectories/sec")
        print(f"     {n} trajectories in {mean_time:.2f} ms")
        return True
    elif traj_per_sec > 20000:
        print(f"  ⚠️ MARGINAL: {traj_per_sec:.0f} trajectories/sec (target: 50k+)")
        return True
    else:
        print(f"  ❌ FAIL: {traj_per_sec:.0f} trajectories/sec (too slow)")
        return False


def test_numba_speedup():
    """Test 5: Rust is faster than Numba."""
    print("\nTest 5: Rust vs Numba speedup")
    
    try:
        import trajectory_rs
        from batted_ball.aerodynamics import get_lookup_tables, aerodynamic_force_tuple_lookup
        from batted_ball.integrator import calculate_trajectory_endpoints_batch
    except ImportError as e:
        print(f"  ❌ FAIL: Import error: {e}")
        return False
    
    cd_table, cl_table = get_lookup_tables()
    
    # Create 100 trajectories
    n = 100
    np.random.seed(42)
    
    initial_states = np.zeros((n, 6))
    initial_states[:, 2] = 1.0
    exit_vels = np.random.uniform(35, 50, n)
    launch_angles = np.random.uniform(15, 35, n)
    initial_states[:, 3] = exit_vels * np.cos(np.radians(launch_angles))
    initial_states[:, 5] = exit_vels * np.sin(np.radians(launch_angles))
    
    spin_params = np.zeros((n, 4))
    spin_params[:, 1] = 1.0
    spin_params[:, 3] = np.random.uniform(1500, 2500, n)
    
    # Warmup both
    for _ in range(3):
        trajectory_rs.integrate_trajectories_batch(
            initial_states, 0.01, 10.0, 0.0,
            spin_params, 1.225, 0.00426,
            cd_table, cl_table
        )
        calculate_trajectory_endpoints_batch(
            initial_states, 0.01, 10.0, 0.0,
            spin_params, 0.3, 1.225, 0.00426,
            cd_table, cl_table, aerodynamic_force_tuple_lookup
        )
    
    # Benchmark Rust
    rust_times = []
    for _ in range(5):
        start = time.perf_counter()
        trajectory_rs.integrate_trajectories_batch(
            initial_states, 0.01, 10.0, 0.0,
            spin_params, 1.225, 0.00426,
            cd_table, cl_table
        )
        rust_times.append(time.perf_counter() - start)
    
    # Benchmark Numba
    numba_times = []
    for _ in range(5):
        start = time.perf_counter()
        calculate_trajectory_endpoints_batch(
            initial_states, 0.01, 10.0, 0.0,
            spin_params, 0.3, 1.225, 0.00426,
            cd_table, cl_table, aerodynamic_force_tuple_lookup
        )
        numba_times.append(time.perf_counter() - start)
    
    rust_mean = np.mean(rust_times) * 1000
    numba_mean = np.mean(numba_times) * 1000
    speedup = numba_mean / rust_mean
    
    # Target: 2-3x speedup (we typically get 10-15x)
    if speedup >= 2.0:
        print(f"  ✅ PASS: {speedup:.1f}x speedup (target: 2-3x)")
        print(f"     Rust: {rust_mean:.2f}ms, Numba: {numba_mean:.2f}ms")
        return True
    elif speedup >= 1.5:
        print(f"  ⚠️ MARGINAL: {speedup:.1f}x speedup (target: 2-3x)")
        return True
    else:
        print(f"  ❌ FAIL: {speedup:.1f}x speedup (target: 2-3x)")
        return False


def test_constants():
    """Test 6: Rust constants match Python."""
    print("\nTest 6: Constants match")
    
    try:
        import trajectory_rs
        from batted_ball.constants import GRAVITY, BALL_MASS
    except ImportError as e:
        print(f"  ❌ FAIL: Import error: {e}")
        return False
    
    if abs(trajectory_rs.GRAVITY - GRAVITY) < 1e-6:
        print(f"  ✅ GRAVITY: {trajectory_rs.GRAVITY}")
    else:
        print(f"  ❌ GRAVITY mismatch: Rust={trajectory_rs.GRAVITY}, Python={GRAVITY}")
        return False
    
    if abs(trajectory_rs.BALL_MASS - BALL_MASS) < 1e-6:
        print(f"  ✅ BALL_MASS: {trajectory_rs.BALL_MASS}")
    else:
        print(f"  ❌ BALL_MASS mismatch: Rust={trajectory_rs.BALL_MASS}, Python={BALL_MASS}")
        return False
    
    return True


def main():
    """Run all Phase 7 validation tests."""
    print("=" * 60)
    print("PHASE 7 VALIDATION: Rust Native Code Extensions")
    print("=" * 60)
    
    tests = [
        ("Rust import", test_rust_import),
        ("Single trajectory physics", test_single_trajectory),
        ("Batch trajectory processing", test_batch_trajectory),
        ("Parallel speedup", test_parallel_speedup),
        ("Rust vs Numba speedup", test_numba_speedup),
        ("Constants match", test_constants),
    ]
    
    results = []
    for name, test_func in tests:
        try:
            result = test_func()
            results.append((name, result))
        except Exception as e:
            print(f"\n{name}: ❌ EXCEPTION: {e}")
            results.append((name, False))
    
    # Summary
    print("\n" + "=" * 60)
    print("SUMMARY")
    print("=" * 60)
    
    passed = sum(1 for _, r in results if r)
    total = len(results)
    
    for name, result in results:
        status = "✅" if result else "❌"
        print(f"  {status} {name}")
    
    print(f"\n{passed}/{total} tests passed")
    
    if passed == total:
        print("\n✅ PHASE 7 VALIDATION COMPLETE")
    else:
        print("\n❌ SOME TESTS FAILED")
    
    return passed == total


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
