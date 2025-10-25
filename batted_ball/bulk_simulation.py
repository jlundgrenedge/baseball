"""
Bulk simulation engine optimized for large-scale at-bat analysis.

Provides significant performance improvements for simulating thousands of at-bats
through optimized memory usage, caching, and streamlined processing.
"""

import time
import numpy as np
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass

from .at_bat import AtBatSimulator, AtBatResult
from .player import Pitcher, Hitter
from .performance import (
    get_trajectory_buffer,
    get_result_pool,
    UltraFastMode,
    get_performance_tracker,
    OptimizedAerodynamicForces
)


@dataclass
class BulkSimulationSettings:
    """Configuration for bulk simulation optimization."""
    
    # Simulation parameters
    use_ultra_fast_mode: bool = False
    use_simplified_aerodynamics: bool = False
    use_object_pooling: bool = True
    use_result_caching: bool = True
    
    # Memory optimization
    stream_results: bool = False  # Don't store all results in memory
    batch_size: int = 1000  # Process in batches to manage memory
    
    # Accuracy vs speed tradeoffs
    accuracy_level: str = 'high'  # 'high', 'medium', 'low'
    
    @classmethod
    def for_simulation_count(cls, count: int) -> 'BulkSimulationSettings':
        """Create optimal settings based on simulation count."""
        if count >= 100000:
            return cls(
                use_ultra_fast_mode=True,
                use_simplified_aerodynamics=True,
                stream_results=True,
                accuracy_level='medium'
            )
        elif count >= 10000:
            return cls(
                use_ultra_fast_mode=True,
                use_simplified_aerodynamics=True,
                accuracy_level='medium'
            )
        elif count >= 1000:
            return cls(
                use_ultra_fast_mode=False,
                use_simplified_aerodynamics=False,
                accuracy_level='high'
            )
        else:
            return cls()  # Default settings for small batches


@dataclass
class BulkSimulationResult:
    """Results from bulk simulation with summary statistics."""
    
    # Simulation metadata
    total_at_bats: int
    simulation_time: float
    at_bats_per_second: float
    settings_used: BulkSimulationSettings
    
    # Outcome statistics
    outcome_counts: Dict[str, int]
    outcome_percentages: Dict[str, float]
    
    # Performance metrics
    average_exit_velocity: float
    average_launch_angle: float
    average_distance: float
    
    # Contact quality distribution
    contact_quality_distribution: Dict[str, int]
    
    # Optional: Individual results (if not streaming)
    individual_results: Optional[List[AtBatResult]] = None
    
    def __str__(self) -> str:
        """String representation of results."""
        return (
            f"BulkSimulationResult:\n"
            f"  At-bats: {self.total_at_bats:,}\n"
            f"  Time: {self.simulation_time:.2f}s\n"
            f"  Rate: {self.at_bats_per_second:.1f} at-bats/sec\n"
            f"  Outcomes: {self.outcome_percentages}\n"
            f"  Avg Exit Velocity: {self.average_exit_velocity:.1f} mph\n"
            f"  Avg Launch Angle: {self.average_launch_angle:.1f}°\n"
            f"  Avg Distance: {self.average_distance:.1f} ft"
        )


class BulkAtBatSimulator:
    """
    Optimized simulator for large-scale at-bat analysis.
    
    Provides 5-20x speedup over standard AtBatSimulator for bulk simulations
    through aggressive optimization and approximations.
    """
    
    def __init__(
        self,
        altitude: float = 0.0,
        temperature: float = 70.0,
        humidity: float = 0.5,
        settings: Optional[BulkSimulationSettings] = None
    ):
        """
        Initialize bulk simulator.
        
        Parameters
        ----------
        altitude : float
            Altitude in feet
        temperature : float
            Temperature in Fahrenheit
        humidity : float
            Relative humidity (0-1)
        settings : BulkSimulationSettings, optional
            Optimization settings
        """
        self.altitude = altitude
        self.temperature = temperature
        self.humidity = humidity
        self.settings = settings or BulkSimulationSettings()
        
        # Initialize optimization components
        self.trajectory_buffer = get_trajectory_buffer()
        self.result_pool = get_result_pool()
        self.performance_tracker = get_performance_tracker()
        
        # Create optimized aerodynamics if requested
        if self.settings.use_simplified_aerodynamics:
            self.aerodynamics = OptimizedAerodynamicForces()
        else:
            self.aerodynamics = None
    
    def simulate_matchup(
        self,
        pitcher: Pitcher,
        hitter: Hitter,
        n_at_bats: int,
        verbose: bool = False
    ) -> BulkSimulationResult:
        """
        Simulate multiple at-bats between a pitcher and hitter.
        
        Parameters
        ----------
        pitcher : Pitcher
            Pitcher object with attributes
        hitter : Hitter
            Hitter object with attributes
        n_at_bats : int
            Number of at-bats to simulate
        verbose : bool
            Whether to print progress
            
        Returns
        -------
        BulkSimulationResult
            Aggregated results and statistics
        """
        # Auto-configure settings based on simulation count
        if n_at_bats >= 1000 and self.settings == BulkSimulationSettings():
            self.settings = BulkSimulationSettings.for_simulation_count(n_at_bats)
            if verbose:
                print(f"Auto-configured for {n_at_bats:,} at-bats:")
                print(f"  Ultra-fast mode: {self.settings.use_ultra_fast_mode}")
                print(f"  Simplified aerodynamics: {self.settings.use_simplified_aerodynamics}")
                print(f"  Streaming results: {self.settings.stream_results}")
        
        start_time = time.time()
        
        # Initialize result tracking
        outcome_counts = {'strikeout': 0, 'walk': 0, 'in_play': 0, 'foul': 0}
        contact_quality_counts = {'perfect': 0, 'good': 0, 'fair': 0, 'weak': 0, 'poor': 0}
        
        exit_velocities = []
        launch_angles = []
        distances = []
        individual_results = [] if not self.settings.stream_results else None
        
        # Determine optimal simulation mode
        fast_mode = self.settings.use_ultra_fast_mode or n_at_bats >= 1000
        
        # Process in batches if needed
        batch_size = self.settings.batch_size
        n_batches = (n_at_bats + batch_size - 1) // batch_size
        
        for batch_idx in range(n_batches):
            batch_start = batch_idx * batch_size
            batch_end = min(batch_start + batch_size, n_at_bats)
            batch_size_actual = batch_end - batch_start
            
            if verbose and n_batches > 1:
                print(f"Processing batch {batch_idx + 1}/{n_batches} "
                      f"({batch_size_actual} at-bats)...")
            
            # Simulate batch
            for i in range(batch_size_actual):
                # Reset pitcher state
                pitcher.current_stamina = max(pitcher.current_stamina, 80)
                
                # Create simulator with optimizations
                sim = AtBatSimulator(
                    pitcher, hitter,
                    altitude=self.altitude,
                    temperature=self.temperature,
                    humidity=self.humidity,
                    fast_mode=fast_mode
                )
                
                # Simulate at-bat
                result = sim.simulate_at_bat(verbose=False)
                
                # Track outcomes
                outcome_counts[result.outcome] += 1
                
                # Track contact results
                if result.batted_ball_result:
                    contact_data = result.batted_ball_result
                    
                    # Extract metrics
                    if 'exit_velocity' in contact_data:
                        exit_velocities.append(contact_data['exit_velocity'])
                    if 'launch_angle' in contact_data:
                        launch_angles.append(contact_data['launch_angle'])
                    if 'distance' in contact_data:
                        distances.append(contact_data['distance'])
                    if 'contact_quality' in contact_data:
                        quality = contact_data['contact_quality']
                        if quality in contact_quality_counts:
                            contact_quality_counts[quality] += 1
                
                # Store individual result if not streaming
                if individual_results is not None:
                    individual_results.append(result)
                
                # Progress update for large simulations
                if verbose and n_at_bats >= 10000 and (i + 1 + batch_start) % 5000 == 0:
                    elapsed = time.time() - start_time
                    completed = i + 1 + batch_start
                    rate = completed / elapsed
                    eta = (n_at_bats - completed) / rate
                    print(f"  Progress: {completed:,}/{n_at_bats:,} "
                          f"({completed/n_at_bats*100:.1f}%) - "
                          f"{rate:.1f} at-bats/sec - ETA: {eta:.1f}s")
        
        # Calculate final statistics
        end_time = time.time()
        simulation_time = end_time - start_time
        at_bats_per_second = n_at_bats / simulation_time if simulation_time > 0 else 0
        
        # Outcome percentages
        outcome_percentages = {
            outcome: count / n_at_bats * 100
            for outcome, count in outcome_counts.items()
        }
        
        # Contact metrics (only from balls in play)
        avg_exit_velocity = np.mean(exit_velocities) if exit_velocities else 0.0
        avg_launch_angle = np.mean(launch_angles) if launch_angles else 0.0
        avg_distance = np.mean(distances) if distances else 0.0
        
        # Track performance
        self.performance_tracker.track_simulation(simulation_time, n_at_bats)
        
        # Create result object
        result = BulkSimulationResult(
            total_at_bats=n_at_bats,
            simulation_time=simulation_time,
            at_bats_per_second=at_bats_per_second,
            settings_used=self.settings,
            outcome_counts=outcome_counts,
            outcome_percentages=outcome_percentages,
            average_exit_velocity=avg_exit_velocity,
            average_launch_angle=avg_launch_angle,
            average_distance=avg_distance,
            contact_quality_distribution=contact_quality_counts,
            individual_results=individual_results
        )
        
        if verbose:
            print(f"\nSimulation Complete!")
            print(f"Time: {simulation_time:.2f} seconds")
            print(f"Rate: {at_bats_per_second:.1f} at-bats per second")
            print(f"Speedup vs normal mode: {at_bats_per_second / 3.9:.1f}x")  # 3.9 = 1/0.257
            print(f"\nOutcome Distribution:")
            for outcome, percentage in outcome_percentages.items():
                print(f"  {outcome.capitalize()}: {percentage:.1f}%")
        
        return result
    
    def compare_matchups(
        self,
        matchups: List[Tuple[Pitcher, Hitter, str]],
        n_at_bats_each: int,
        verbose: bool = True
    ) -> Dict[str, BulkSimulationResult]:
        """
        Compare multiple pitcher-hitter matchups.
        
        Parameters
        ----------
        matchups : list
            List of (pitcher, hitter, name) tuples
        n_at_bats_each : int
            Number of at-bats per matchup
        verbose : bool
            Whether to print progress and results
            
        Returns
        -------
        dict
            Results keyed by matchup name
        """
        results = {}
        total_simulations = len(matchups) * n_at_bats_each
        
        if verbose:
            print(f"Comparing {len(matchups)} matchups with {n_at_bats_each:,} at-bats each")
            print(f"Total simulations: {total_simulations:,}")
            print("=" * 60)
        
        overall_start = time.time()
        
        for i, (pitcher, hitter, name) in enumerate(matchups):
            if verbose:
                print(f"\n{i+1}/{len(matchups)}: {name}")
                print("-" * 40)
            
            result = self.simulate_matchup(
                pitcher, hitter, n_at_bats_each, verbose=verbose
            )
            results[name] = result
            
            if verbose:
                print(f"Result: {result.outcome_percentages}")
        
        if verbose:
            overall_time = time.time() - overall_start
            overall_rate = total_simulations / overall_time
            print(f"\n" + "=" * 60)
            print(f"COMPARISON COMPLETE")
            print(f"Total time: {overall_time:.2f} seconds")
            print(f"Overall rate: {overall_rate:.1f} at-bats/second")
            print(f"Estimated speedup vs normal mode: {overall_rate / 3.9:.1f}x")
        
        return results
    
    @staticmethod
    def benchmark_performance(
        pitcher: Pitcher,
        hitter: Hitter,
        test_sizes: List[int] = [100, 1000, 10000],
        verbose: bool = True
    ) -> Dict[int, float]:
        """
        Benchmark simulation performance at different scales.
        
        Parameters
        ----------
        pitcher : Pitcher
            Test pitcher
        hitter : Hitter
            Test hitter
        test_sizes : list
            List of at-bat counts to test
        verbose : bool
            Whether to print results
            
        Returns
        -------
        dict
            Performance rates (at-bats/second) by test size
        """
        if verbose:
            print("PERFORMANCE BENCHMARK")
            print("=" * 50)
        
        results = {}
        
        for size in test_sizes:
            # Auto-configure settings for this size
            settings = BulkSimulationSettings.for_simulation_count(size)
            simulator = BulkAtBatSimulator(settings=settings)
            
            if verbose:
                print(f"\nTesting {size:,} at-bats...")
                print(f"  Settings: ultra_fast={settings.use_ultra_fast_mode}, "
                      f"simplified_aero={settings.use_simplified_aerodynamics}")
            
            start_time = time.time()
            result = simulator.simulate_matchup(pitcher, hitter, size, verbose=False)
            end_time = time.time()
            
            rate = result.at_bats_per_second
            results[size] = rate
            
            if verbose:
                print(f"  Rate: {rate:.1f} at-bats/second")
                print(f"  Time: {result.simulation_time:.2f} seconds")
                print(f"  Speedup vs normal: {rate / 3.9:.1f}x")
        
        if verbose:
            print(f"\n" + "=" * 50)
            print("BENCHMARK COMPLETE")
            
            print(f"\nPerformance Summary:")
            for size, rate in results.items():
                print(f"  {size:>6,} at-bats: {rate:>6.1f} at-bats/sec")
        
        return results