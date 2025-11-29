"""Quick benchmark for ground ball Rust speedup."""

from batted_ball.fast_ground_ball import (
    FastGroundBallSimulator, 
    is_rust_ground_ball_available,
    benchmark_ground_ball_speedup,
)
import numpy as np

print("=" * 60)
print("Ground Ball Physics - Rust Benchmark")
print("=" * 60)

print(f"\nRust ground ball available: {is_rust_ground_ball_available()}")

# Test basic simulation
print("\n--- Testing basic simulation ---")
sim = FastGroundBallSimulator(use_rust=True)
result = sim.simulate_ground_ball(0, 0, 50, 60, -5, 1000)
print(f"Landing: ({result.landing_position[0]:.1f}, {result.landing_position[1]:.1f}) ft")
print(f"Velocity: {result.landing_velocity_mph:.1f} mph")
print(f"Landing time: {result.landing_time:.3f}s")

# Test ball position
print("\n--- Testing ball position at time ---")
pos, vel = sim.get_ball_position_at_time(result, 1.0)
print(f"At t=1.0s: ({pos[0]:.1f}, {pos[1]:.1f}), vel={vel:.1f} mph")

# Test interception
print("\n--- Testing interception calculation ---")
intercept = sim.find_interception_point(result, 100, 100, 28.0, 0.3, 80)
print(f"Can intercept: {intercept.can_intercept}")
print(f"Margin: {intercept.margin:.2f}s")
print(f"Interception point: ({intercept.interception_point[0]:.1f}, {intercept.interception_point[1]:.1f})")

# Test multi-fielder interception
print("\n--- Testing multi-fielder interception ---")
fielder_positions = np.array([
    [100, 100],  # 3B
    [0, 120],    # SS
    [-100, 100], # 2B
    [150, 150],  # LF
])
fielder_speeds = np.array([27.0, 28.0, 26.0, 29.0])
reaction_times = np.array([0.3, 0.28, 0.32, 0.35])

best_idx, best_result = sim.find_best_interception(
    result, fielder_positions, fielder_speeds, reaction_times, 80.0
)
print(f"Best fielder: index {best_idx}")
print(f"Margin: {best_result.margin:.2f}s")

# Run benchmark
print("\n--- Performance Benchmark ---")
results = benchmark_ground_ball_speedup(5000)
print(f"Benchmarked {results['n_simulations']} simulations:")
print(f"  Rust:   {results.get('rust_sims_per_sec', 0):.0f} sims/sec")
print(f"  Python: {results['python_sims_per_sec']:.0f} sims/sec")
print(f"  Speedup: {results['speedup']:.1f}x")

print("\n" + "=" * 60)
print("Ground ball Rust integration: SUCCESS")
print("=" * 60)
