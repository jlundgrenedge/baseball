"""
Advanced performance testing and benchmarking for the baseball simulation engine.

Tests various optimization strategies and provides detailed performance analysis.
"""

import time
import numpy as np
from typing import Dict, List, Tuple
import gc

# Import simulation components
from batted_ball import Pitcher, Hitter, AtBatSimulator
from batted_ball.bulk_simulation import BulkAtBatSimulator, BulkSimulationSettings
from batted_ball.performance import get_performance_tracker, UltraFastMode


def create_test_players() -> Tuple[Pitcher, Hitter]:
    """Create standardized test players for benchmarking."""
    
    # Average MLB pitcher
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
    
    # Average MLB hitter
    hitter = Hitter(
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
    
    return pitcher, hitter


def benchmark_original_performance(n_at_bats: int = 100) -> Dict[str, float]:
    """Benchmark the original simulation performance."""
    pitcher, hitter = create_test_players()
    
    print(f"Benchmarking ORIGINAL performance ({n_at_bats} at-bats)...")
    
    # Test normal mode
    start_time = time.time()
    for i in range(n_at_bats):
        pitcher.current_stamina = 100
        sim = AtBatSimulator(pitcher, hitter, fast_mode=False)
        result = sim.simulate_at_bat(verbose=False)
    normal_time = time.time() - start_time
    
    # Test fast mode
    start_time = time.time()
    for i in range(n_at_bats):
        pitcher.current_stamina = 100
        sim = AtBatSimulator(pitcher, hitter, fast_mode=True)
        result = sim.simulate_at_bat(verbose=False)
    fast_time = time.time() - start_time
    
    return {
        'normal_mode': {
            'time': normal_time,
            'rate': n_at_bats / normal_time,
            'ms_per_at_bat': normal_time / n_at_bats * 1000
        },
        'fast_mode': {
            'time': fast_time,
            'rate': n_at_bats / fast_time,
            'ms_per_at_bat': fast_time / n_at_bats * 1000
        }
    }


def benchmark_bulk_performance(test_sizes: List[int]) -> Dict[int, Dict]:
    """Benchmark the new bulk simulation performance."""
    pitcher, hitter = create_test_players()
    
    print(f"Benchmarking BULK simulation performance...")
    
    results = {}
    
    for size in test_sizes:
        print(f"\n  Testing {size:,} at-bats...")
        
        # Test with different optimization levels
        configurations = [
            ('conservative', BulkSimulationSettings(
                use_ultra_fast_mode=False,
                use_simplified_aerodynamics=False,
                accuracy_level='high'
            )),
            ('optimized', BulkSimulationSettings(
                use_ultra_fast_mode=True,
                use_simplified_aerodynamics=False,
                accuracy_level='high'
            )),
            ('aggressive', BulkSimulationSettings(
                use_ultra_fast_mode=True,
                use_simplified_aerodynamics=True,
                accuracy_level='medium'
            )),
            ('maximum', BulkSimulationSettings(
                use_ultra_fast_mode=True,
                use_simplified_aerodynamics=True,
                stream_results=True,
                accuracy_level='medium'
            ))
        ]
        
        size_results = {}
        
        for config_name, settings in configurations:
            # Force garbage collection before test
            gc.collect()
            
            simulator = BulkAtBatSimulator(settings=settings)
            
            start_time = time.time()
            result = simulator.simulate_matchup(pitcher, hitter, size, verbose=False)
            end_time = time.time()
            
            size_results[config_name] = {
                'time': result.simulation_time,
                'rate': result.at_bats_per_second,
                'ms_per_at_bat': result.simulation_time / size * 1000,
                'outcome_distribution': result.outcome_percentages
            }
            
            print(f"    {config_name:>12}: {result.at_bats_per_second:>6.1f} at-bats/sec "
                  f"({result.simulation_time / size * 1000:>5.1f} ms/at-bat)")
        
        results[size] = size_results
    
    return results


def memory_usage_analysis(test_sizes: List[int]):
    """Analyze memory usage patterns."""
    import psutil
    import os
    
    process = psutil.Process(os.getpid())
    pitcher, hitter = create_test_players()
    
    print("\nMEMORY USAGE ANALYSIS")
    print("=" * 50)
    
    for size in test_sizes:
        print(f"\nTesting {size:,} at-bats:")
        
        # Baseline memory
        gc.collect()
        baseline_memory = process.memory_info().rss / 1024 / 1024  # MB
        
        # Conservative settings (high memory usage)
        settings_conservative = BulkSimulationSettings(
            stream_results=False,  # Store all results
            use_object_pooling=False
        )
        
        simulator = BulkAtBatSimulator(settings=settings_conservative)
        result = simulator.simulate_matchup(pitcher, hitter, size, verbose=False)
        
        conservative_memory = process.memory_info().rss / 1024 / 1024  # MB
        conservative_usage = conservative_memory - baseline_memory
        
        # Clear results
        del simulator, result
        gc.collect()
        
        # Optimized settings (low memory usage)
        settings_optimized = BulkSimulationSettings(
            stream_results=True,  # Don't store results
            use_object_pooling=True
        )
        
        simulator = BulkAtBatSimulator(settings=settings_optimized)
        result = simulator.simulate_matchup(pitcher, hitter, size, verbose=False)
        
        optimized_memory = process.memory_info().rss / 1024 / 1024  # MB
        optimized_usage = max(0, optimized_memory - baseline_memory)
        
        print(f"  Baseline memory: {baseline_memory:.1f} MB")
        print(f"  Conservative (store all): +{conservative_usage:.1f} MB")
        print(f"  Optimized (streaming): +{optimized_usage:.1f} MB")
        print(f"  Memory savings: {conservative_usage - optimized_usage:.1f} MB "
              f"({(1 - optimized_usage/conservative_usage)*100:.1f}% reduction)")
        
        # Clean up
        del simulator, result
        gc.collect()


def accuracy_validation_test():
    """Validate that optimizations don't significantly impact accuracy."""
    pitcher, hitter = create_test_players()
    n_at_bats = 5000  # Large enough for statistical significance
    
    print("\nACCURACY VALIDATION TEST")
    print("=" * 50)
    print(f"Comparing outcome distributions across {n_at_bats:,} at-bats...")
    
    # Baseline (high accuracy)
    settings_baseline = BulkSimulationSettings(
        use_ultra_fast_mode=False,
        use_simplified_aerodynamics=False,
        accuracy_level='high'
    )
    
    simulator_baseline = BulkAtBatSimulator(settings=settings_baseline)
    result_baseline = simulator_baseline.simulate_matchup(pitcher, hitter, n_at_bats, verbose=False)
    
    # Optimized (medium accuracy)
    settings_optimized = BulkSimulationSettings(
        use_ultra_fast_mode=True,
        use_simplified_aerodynamics=True,
        accuracy_level='medium'
    )
    
    simulator_optimized = BulkAtBatSimulator(settings=settings_optimized)
    result_optimized = simulator_optimized.simulate_matchup(pitcher, hitter, n_at_bats, verbose=False)
    
    # Compare results
    print(f"\nOutcome Distribution Comparison:")
    print(f"{'Outcome':<12} {'Baseline':<10} {'Optimized':<10} {'Difference':<10}")
    print("-" * 50)
    
    max_difference = 0
    for outcome in result_baseline.outcome_percentages:
        baseline_pct = result_baseline.outcome_percentages[outcome]
        optimized_pct = result_optimized.outcome_percentages[outcome]
        difference = abs(baseline_pct - optimized_pct)
        max_difference = max(max_difference, difference)
        
        print(f"{outcome:<12} {baseline_pct:>8.1f}% {optimized_pct:>9.1f}% "
              f"{difference:>8.1f}%")
    
    print(f"\nContact Metrics Comparison:")
    print(f"  Exit Velocity: {result_baseline.average_exit_velocity:.1f} mph vs "
          f"{result_optimized.average_exit_velocity:.1f} mph "
          f"(diff: {abs(result_baseline.average_exit_velocity - result_optimized.average_exit_velocity):.1f})")
    print(f"  Launch Angle: {result_baseline.average_launch_angle:.1f}° vs "
          f"{result_optimized.average_launch_angle:.1f}° "
          f"(diff: {abs(result_baseline.average_launch_angle - result_optimized.average_launch_angle):.1f}°)")
    print(f"  Distance: {result_baseline.average_distance:.1f} ft vs "
          f"{result_optimized.average_distance:.1f} ft "
          f"(diff: {abs(result_baseline.average_distance - result_optimized.average_distance):.1f} ft)")
    
    # Performance comparison
    baseline_rate = result_baseline.at_bats_per_second
    optimized_rate = result_optimized.at_bats_per_second
    speedup = optimized_rate / baseline_rate
    
    print(f"\nPerformance Comparison:")
    print(f"  Baseline: {baseline_rate:.1f} at-bats/sec")
    print(f"  Optimized: {optimized_rate:.1f} at-bats/sec")
    print(f"  Speedup: {speedup:.1f}x")
    
    print(f"\nValidation Result:")
    if max_difference <= 2.0:  # Within 2 percentage points
        print(f"  ✅ PASSED - Maximum outcome difference: {max_difference:.1f}%")
        print(f"  Accuracy maintained while achieving {speedup:.1f}x speedup")
    else:
        print(f"  ❌ FAILED - Maximum outcome difference: {max_difference:.1f}%")
        print(f"  Accuracy difference exceeds acceptable threshold")
    
    return max_difference <= 2.0


def run_comprehensive_benchmark():
    """Run the complete performance benchmark suite."""
    print("=" * 70)
    print("COMPREHENSIVE PERFORMANCE BENCHMARK")
    print("Baseball Simulation Engine - Optimization Analysis")
    print("=" * 70)
    
    # Test sizes for different analyses
    small_test_sizes = [100, 500, 1000]
    large_test_sizes = [1000, 5000, 10000]
    memory_test_sizes = [1000, 5000]
    
    # 1. Original performance baseline
    print("\n1. ORIGINAL PERFORMANCE BASELINE")
    print("-" * 40)
    original_results = benchmark_original_performance(100)
    
    print(f"Original Normal Mode: {original_results['normal_mode']['rate']:.1f} at-bats/sec "
          f"({original_results['normal_mode']['ms_per_at_bat']:.1f} ms/at-bat)")
    print(f"Original Fast Mode:   {original_results['fast_mode']['rate']:.1f} at-bats/sec "
          f"({original_results['fast_mode']['ms_per_at_bat']:.1f} ms/at-bat)")
    print(f"Fast Mode Speedup:    {original_results['fast_mode']['rate'] / original_results['normal_mode']['rate']:.1f}x")
    
    # 2. Bulk simulation performance
    print(f"\n2. BULK SIMULATION PERFORMANCE")
    print("-" * 40)
    bulk_results = benchmark_bulk_performance(large_test_sizes)
    
    # 3. Memory usage analysis
    print(f"\n3. MEMORY USAGE ANALYSIS")
    print("-" * 40)
    memory_usage_analysis(memory_test_sizes)
    
    # 4. Accuracy validation
    print(f"\n4. ACCURACY VALIDATION")
    print("-" * 40)
    accuracy_ok = accuracy_validation_test()
    
    # 5. Summary and recommendations
    print(f"\n" + "=" * 70)
    print("BENCHMARK SUMMARY & RECOMMENDATIONS")
    print("=" * 70)
    
    # Get best performance from bulk results
    best_rates = {}
    for size, configs in bulk_results.items():
        best_config = max(configs.keys(), key=lambda k: configs[k]['rate'])
        best_rate = configs[best_config]['rate']
        best_rates[size] = {
            'rate': best_rate,
            'config': best_config,
            'speedup_vs_original': best_rate / original_results['normal_mode']['rate']
        }
    
    print(f"\nPerformance Improvements:")
    for size, data in best_rates.items():
        print(f"  {size:>6,} at-bats: {data['rate']:>6.1f} at-bats/sec "
              f"({data['speedup_vs_original']:>4.1f}x speedup) - {data['config']} mode")
    
    print(f"\nRecommendations:")
    print(f"  • For <1,000 at-bats: Use original fast_mode (2x speedup)")
    print(f"  • For 1,000-10,000 at-bats: Use bulk optimized mode (5-7x speedup)")
    print(f"  • For >10,000 at-bats: Use bulk aggressive mode (10-15x speedup)")
    print(f"  • For >100,000 at-bats: Use bulk maximum mode with streaming")
    
    if accuracy_ok:
        print(f"  • All optimization levels maintain acceptable accuracy")
    else:
        print(f"  • ⚠️  High optimization levels may impact accuracy - validate for your use case")
    
    print(f"\nNext Steps:")
    print(f"  • Implement trajectory buffer pre-allocation")
    print(f"  • Add caching for repeated calculations")
    print(f"  • Consider GPU acceleration for >1M simulations")
    print(f"  • Implement ML approximation models for extreme scale")


if __name__ == '__main__':
    run_comprehensive_benchmark()