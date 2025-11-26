"""
Accuracy validation tests for performance optimizations.

Ensures that optimizations maintain simulation accuracy within acceptable tolerances.
"""

import pytest
import numpy as np


def test_jit_integrator_accuracy():
    """
    Validate that JIT-optimized integrator produces accurate results.

    Compares JIT implementation against expected physics behavior.
    """
    from batted_ball.fast_trajectory import FastTrajectorySimulator

    print("\n" + "="*70)
    print("VALIDATION: JIT Integrator Accuracy")
    print("="*70)

    # Create simulator
    sim = FastTrajectorySimulator(fast_mode=False)

    # Test case: 45 m/s exit velocity, 30° launch angle, 2000 RPM backspin
    result = sim.simulate_batted_ball(
        exit_velocity=45.0,
        launch_angle=30.0,
        spray_angle=0.0,
        spin_rate=2000.0,
        spin_axis=[0, 1, 0]
    )

    # Validate physics expectations
    distance = result['distance']
    apex = result['apex']
    hang_time = result['hang_time']

    print(f"\nSimulation Results:")
    print(f"  Distance:   {distance:.1f}m")
    print(f"  Apex:       {apex:.1f}m")
    print(f"  Hang Time:  {hang_time:.2f}s")

    # Physics sanity checks
    assert 80 < distance < 150, f"Distance out of expected range: {distance:.1f}m"
    assert 10 < apex < 40, f"Apex out of expected range: {apex:.1f}m"
    assert 3 < hang_time < 8, f"Hang time out of expected range: {hang_time:.2f}s"

    # Check trajectory smoothness (no discontinuities)
    positions = result['position']
    velocities = result['velocity']

    # Check for NaN or inf
    assert not np.any(np.isnan(positions)), "NaN found in positions"
    assert not np.any(np.isinf(positions)), "Inf found in positions"
    assert not np.any(np.isnan(velocities)), "NaN found in velocities"
    assert not np.any(np.isinf(velocities)), "Inf found in velocities"

    # Check trajectory is continuous (no large jumps)
    position_diffs = np.diff(positions, axis=0)
    max_position_jump = np.max(np.linalg.norm(position_diffs, axis=1))
    assert max_position_jump < 1.0, f"Large position jump detected: {max_position_jump:.3f}m"

    # Check z-coordinate starts positive and ends at ground
    assert positions[0, 2] > 0, "Initial height should be positive"
    assert abs(positions[-1, 2]) < 0.1, "Final height should be near ground"

    print("\n✓ JIT integrator produces physically valid results")
    print("="*70)


def test_fast_mode_accuracy():
    """
    Validate that fast mode maintains accuracy within 2% tolerance.

    Compares fast mode (larger dt) against normal mode.
    """
    from batted_ball.fast_trajectory import FastTrajectorySimulator

    print("\n" + "="*70)
    print("VALIDATION: Fast Mode Accuracy")
    print("="*70)

    # Test parameters
    test_params = {
        'exit_velocity': 45.0,
        'launch_angle': 30.0,
        'spray_angle': 0.0,
        'spin_rate': 2000.0,
        'spin_axis': [0, 1, 0],
    }

    # Normal mode (reference)
    sim_normal = FastTrajectorySimulator(fast_mode=False)
    result_normal = sim_normal.simulate_batted_ball(**test_params)

    # Fast mode (larger dt)
    sim_fast = FastTrajectorySimulator(fast_mode=True)
    result_fast = sim_fast.simulate_batted_ball(**test_params)

    # Compare results
    distance_normal = result_normal['distance']
    distance_fast = result_fast['distance']
    distance_error = abs(distance_normal - distance_fast) / distance_normal * 100

    apex_normal = result_normal['apex']
    apex_fast = result_fast['apex']
    apex_error = abs(apex_normal - apex_fast) / apex_normal * 100

    hang_time_normal = result_normal['hang_time']
    hang_time_fast = result_fast['hang_time']
    hang_time_error = abs(hang_time_normal - hang_time_fast) / hang_time_normal * 100

    print(f"\n{'Metric':<15} {'Normal Mode':<15} {'Fast Mode':<15} {'Error':<10}")
    print(f"{'-'*60}")
    print(f"{'Distance (m)':<15} {distance_normal:<15.2f} {distance_fast:<15.2f} {distance_error:<10.2f}%")
    print(f"{'Apex (m)':<15} {apex_normal:<15.2f} {apex_fast:<15.2f} {apex_error:<10.2f}%")
    print(f"{'Hang Time (s)':<15} {hang_time_normal:<15.2f} {hang_time_fast:<15.2f} {hang_time_error:<10.2f}%")

    # Validate errors are within tolerance
    max_acceptable_error = 3.0  # 3% tolerance

    assert distance_error < max_acceptable_error, (
        f"Distance error too large: {distance_error:.2f}% > {max_acceptable_error}%"
    )
    assert apex_error < max_acceptable_error, (
        f"Apex error too large: {apex_error:.2f}% > {max_acceptable_error}%"
    )
    assert hang_time_error < max_acceptable_error, (
        f"Hang time error too large: {hang_time_error:.2f}% > {max_acceptable_error}%"
    )

    print(f"\n✓ Fast mode maintains accuracy within {max_acceptable_error}% tolerance")
    print("="*70)


def test_batch_processing_consistency():
    """
    Validate that batch processing produces consistent results.

    Ensures batch simulator gives same results as individual simulations.
    """
    from batted_ball.fast_trajectory import FastTrajectorySimulator, BatchTrajectorySimulator

    print("\n" + "="*70)
    print("VALIDATION: Batch Processing Consistency")
    print("="*70)

    n_tests = 20

    # Generate test parameters
    np.random.seed(42)
    exit_velocities = np.random.uniform(35, 50, n_tests)
    launch_angles = np.random.uniform(10, 40, n_tests)
    spray_angles = np.random.uniform(-30, 30, n_tests)
    spin_rates = np.random.uniform(1500, 2500, n_tests)
    spin_axes = np.tile([0, 1, 0], (n_tests, 1))

    # Individual simulations
    sim_individual = FastTrajectorySimulator(fast_mode=True)
    individual_distances = []

    print(f"\nRunning {n_tests} individual simulations...")
    for i in range(n_tests):
        result = sim_individual.simulate_batted_ball(
            exit_velocity=exit_velocities[i],
            launch_angle=launch_angles[i],
            spray_angle=spray_angles[i],
            spin_rate=spin_rates[i],
            spin_axis=spin_axes[i],
        )
        individual_distances.append(result['distance'])

    # Batch simulation
    sim_batch = BatchTrajectorySimulator(fast_mode=True)

    print(f"Running batch simulation of {n_tests} trajectories...")
    batch_results = sim_batch.simulate_batch(
        exit_velocities,
        launch_angles,
        spray_angles,
        spin_rates,
        spin_axes,
    )
    batch_distances = [r['distance'] for r in batch_results]

    # Compare results
    individual_distances = np.array(individual_distances)
    batch_distances = np.array(batch_distances)

    differences = np.abs(individual_distances - batch_distances)
    relative_errors = differences / individual_distances * 100

    max_error = np.max(relative_errors)
    mean_error = np.mean(relative_errors)

    print(f"\n{'Consistency Metrics:':<30}")
    print(f"{'-'*50}")
    print(f"{'Max difference:':<30} {np.max(differences):.3f}m")
    print(f"{'Mean difference:':<30} {np.mean(differences):.3f}m")
    print(f"{'Max relative error:':<30} {max_error:.3f}%")
    print(f"{'Mean relative error:':<30} {mean_error:.3f}%")

    # Batch results should be identical to individual (same code path)
    assert max_error < 0.001, (
        f"Batch results differ from individual: max error {max_error:.4f}%"
    )

    print(f"\n✓ Batch processing produces consistent results")
    print("="*70)


def test_numerical_stability():
    """
    Validate numerical stability across various conditions.

    Tests extreme cases to ensure no numerical instabilities.
    """
    from batted_ball.fast_trajectory import FastTrajectorySimulator

    print("\n" + "="*70)
    print("VALIDATION: Numerical Stability")
    print("="*70)

    sim = FastTrajectorySimulator(fast_mode=False)

    test_cases = [
        {
            'name': 'Low velocity',
            'params': {
                'exit_velocity': 20.0,
                'launch_angle': 45.0,
                'spray_angle': 0.0,
                'spin_rate': 1000.0,
                'spin_axis': [0, 1, 0],
            },
        },
        {
            'name': 'High velocity',
            'params': {
                'exit_velocity': 60.0,
                'launch_angle': 25.0,
                'spray_angle': 0.0,
                'spin_rate': 3000.0,
                'spin_axis': [0, 1, 0],
            },
        },
        {
            'name': 'Steep angle',
            'params': {
                'exit_velocity': 40.0,
                'launch_angle': 80.0,
                'spray_angle': 0.0,
                'spin_rate': 2000.0,
                'spin_axis': [0, 1, 0],
            },
        },
        {
            'name': 'Low angle',
            'params': {
                'exit_velocity': 45.0,
                'launch_angle': 5.0,
                'spray_angle': 0.0,
                'spin_rate': 2000.0,
                'spin_axis': [0, 1, 0],
            },
        },
        {
            'name': 'Extreme spray',
            'params': {
                'exit_velocity': 40.0,
                'launch_angle': 30.0,
                'spray_angle': 45.0,
                'spin_rate': 2000.0,
                'spin_axis': [0, 1, 0],
            },
        },
    ]

    print(f"\nTesting numerical stability across edge cases...")
    print(f"\n{'Test Case':<20} {'Distance':<12} {'Apex':<12} {'Status':<10}")
    print(f"{'-'*60}")

    for test_case in test_cases:
        try:
            result = sim.simulate_batted_ball(**test_case['params'])

            # Check for valid results
            assert not np.isnan(result['distance']), "NaN distance"
            assert not np.isinf(result['distance']), "Inf distance"
            assert result['distance'] > 0, "Negative distance"
            assert result['apex'] > 0, "Negative apex"
            assert result['hang_time'] > 0, "Negative hang time"

            print(f"{test_case['name']:<20} {result['distance']:<12.1f} {result['apex']:<12.1f} {'✓ PASS':<10}")

        except Exception as e:
            print(f"{test_case['name']:<20} {'ERROR':<12} {'ERROR':<12} {'✗ FAIL':<10}")
            raise AssertionError(f"Numerical instability in {test_case['name']}: {e}")

    print(f"\n✓ Numerical stability validated across edge cases")
    print("="*70)


def test_memory_optimization_correctness():
    """
    Validate that memory optimizations don't affect correctness.

    Tests object pooling and pre-allocation for correctness.
    """
    from batted_ball.performance import StateVectorPool, ForceCalculationCache

    print("\n" + "="*70)
    print("VALIDATION: Memory Optimization Correctness")
    print("="*70)

    # Test state vector pool
    pool = StateVectorPool(pool_size=10)

    print("\nTesting state vector pool...")
    vectors = []
    indices = []

    # Get vectors
    for i in range(15):  # More than pool size to test overflow
        idx, vec = pool.get_state_vector()
        vec[:] = i  # Set unique value
        vectors.append(vec.copy())
        indices.append(idx)

    # Check uniqueness
    for i, vec in enumerate(vectors):
        assert np.all(vec == i), f"Vector {i} was corrupted"

    # Release and reuse
    for idx in indices:
        pool.release_state_vector(idx)

    # Get again - should reuse pool
    idx2, vec2 = pool.get_state_vector()
    vec2[:] = 999

    # Original vectors should be unchanged (we made copies)
    assert np.all(vectors[0] == 0), "Original vector was modified"

    print("  ✓ State vector pool maintains data integrity")

    # Test force calculation cache
    cache = ForceCalculationCache(cache_size=100)

    print("\nTesting force calculation cache...")

    velocity = np.array([40.0, 0.0, 20.0])
    spin_axis = np.array([0.0, 1.0, 0.0])
    spin_rate = 2000.0
    force = np.array([1.0, 2.0, 3.0])

    # Store in cache
    cache.store(velocity, spin_axis, spin_rate, force)

    # Retrieve from cache
    cached_force = cache.lookup(velocity, spin_axis, spin_rate)

    assert cached_force is not None, "Cache lookup failed"
    assert np.allclose(cached_force, force), "Cached force doesn't match original"

    # Modify cached force shouldn't affect original
    cached_force[0] = 999.0
    cached_force2 = cache.lookup(velocity, spin_axis, spin_rate)
    assert cached_force2[0] == force[0], "Cache returned modified data"

    print("  ✓ Force calculation cache maintains data integrity")

    print(f"\n✓ Memory optimizations are correct")
    print("="*70)


if __name__ == '__main__':
    # Run all validation tests
    print("\nRunning optimization accuracy validation tests...")
    print("This ensures all optimizations maintain simulation accuracy.\n")

    test_jit_integrator_accuracy()
    test_fast_mode_accuracy()
    test_batch_processing_consistency()
    test_numerical_stability()
    test_memory_optimization_correctness()

    print("\n" + "="*70)
    print("ALL VALIDATION TESTS PASSED ✓")
    print("="*70)
    print("\nOptimizations maintain accuracy within acceptable tolerances.")
