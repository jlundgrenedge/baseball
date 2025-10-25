"""
Performance optimization utilities for the baseball simulation engine.

Provides memory-efficient trajectory buffers, object pooling, and caching
to reduce allocation overhead and improve simulation speed.
"""

import numpy as np
from typing import Dict, List, Optional, Any
from functools import lru_cache
from .constants import (
    MAX_SIMULATION_TIME,
    DT_DEFAULT,
    DT_FAST,
    BALL_CROSS_SECTIONAL_AREA,
    CD_BASE,
    SPIN_FACTOR,
    SPIN_SATURATION,
)


class TrajectoryBuffer:
    """
    Pre-allocated buffers for trajectory calculations to avoid repeated allocation.
    
    Reduces memory allocation overhead by reusing arrays across simulations.
    """
    
    def __init__(self, max_steps: int = 15000, buffer_count: int = 10):
        """
        Initialize trajectory buffers.
        
        Parameters
        ----------
        max_steps : int
            Maximum number of integration steps per trajectory
        buffer_count : int
            Number of concurrent buffers to maintain
        """
        self.max_steps = max_steps
        self.buffer_count = buffer_count
        
        # Pre-allocate all buffers
        self.position_buffers = np.zeros((buffer_count, max_steps, 3), dtype=np.float64)
        self.velocity_buffers = np.zeros((buffer_count, max_steps, 3), dtype=np.float64)
        self.time_buffers = np.zeros((buffer_count, max_steps), dtype=np.float64)
        
        # Track which buffers are in use
        self.buffer_available = [True] * buffer_count
        self.next_buffer_index = 0
    
    def get_buffer(self):
        """
        Get an available buffer for trajectory calculation.
        
        Returns
        -------
        tuple
            (buffer_index, position_array, velocity_array, time_array)
        """
        # Find next available buffer
        for i in range(self.buffer_count):
            buffer_idx = (self.next_buffer_index + i) % self.buffer_count
            if self.buffer_available[buffer_idx]:
                self.buffer_available[buffer_idx] = False
                self.next_buffer_index = (buffer_idx + 1) % self.buffer_count
                
                return (
                    buffer_idx,
                    self.position_buffers[buffer_idx],
                    self.velocity_buffers[buffer_idx],
                    self.time_buffers[buffer_idx]
                )
        
        # All buffers in use - allocate new ones (should be rare)
        return (
            -1,  # Indicates temporary allocation
            np.zeros((self.max_steps, 3), dtype=np.float64),
            np.zeros((self.max_steps, 3), dtype=np.float64),
            np.zeros(self.max_steps, dtype=np.float64)
        )
    
    def release_buffer(self, buffer_index: int):
        """Release a buffer back to the pool."""
        if buffer_index >= 0:  # Only release pooled buffers
            self.buffer_available[buffer_index] = True


class ResultObjectPool:
    """
    Object pool for frequently created result objects to reduce GC pressure.
    """
    
    def __init__(self, pool_size: int = 100):
        """Initialize object pool."""
        self.pool_size = pool_size
        self.result_pool = []
        self.pitch_data_pool = []
        self.contact_result_pool = []
        
        # Pre-allocate objects
        for _ in range(pool_size):
            self.result_pool.append({})
            self.pitch_data_pool.append({})
            self.contact_result_pool.append({})
    
    def get_result_dict(self) -> Dict:
        """Get a reusable result dictionary."""
        if self.result_pool:
            result = self.result_pool.pop()
            result.clear()
            return result
        return {}
    
    def return_result_dict(self, result: Dict):
        """Return a result dictionary to the pool."""
        if len(self.result_pool) < self.pool_size:
            self.result_pool.append(result)
    
    def get_pitch_data(self) -> Dict:
        """Get a reusable pitch data dictionary."""
        if self.pitch_data_pool:
            data = self.pitch_data_pool.pop()
            data.clear()
            return data
        return {}
    
    def return_pitch_data(self, data: Dict):
        """Return pitch data to the pool."""
        if len(self.pitch_data_pool) < self.pool_size:
            self.pitch_data_pool.append(data)


# Global instances for performance optimization
_trajectory_buffer = None
_result_pool = None

def get_trajectory_buffer() -> TrajectoryBuffer:
    """Get the global trajectory buffer instance."""
    global _trajectory_buffer
    if _trajectory_buffer is None:
        _trajectory_buffer = TrajectoryBuffer()
    return _trajectory_buffer

def get_result_pool() -> ResultObjectPool:
    """Get the global result object pool."""
    global _result_pool
    if _result_pool is None:
        _result_pool = ResultObjectPool()
    return _result_pool


@lru_cache(maxsize=1000)
def cached_aerodynamic_params(velocity_round: float, spin_rate_round: float) -> tuple:
    """
    Cache aerodynamic parameters for common velocity/spin combinations.
    
    Parameters are rounded to reduce cache misses while maintaining accuracy.
    
    Parameters
    ----------
    velocity_round : float
        Velocity rounded to nearest 0.5 m/s
    spin_rate_round : float  
        Spin rate rounded to nearest 50 rpm
        
    Returns
    -------
    tuple
        (drag_coefficient, lift_coefficient)
    """
    # Calculate spin-adjusted drag coefficient
    cd_adjusted = CD_BASE
    if spin_rate_round > 0:
        spin_drag_increase = 0.00002 * spin_rate_round  # SPIN_DRAG_FACTOR
        spin_drag_increase = min(spin_drag_increase, 0.15)  # SPIN_DRAG_MAX_INCREASE
        cd_adjusted += spin_drag_increase
    
    # Calculate lift coefficient
    if spin_rate_round <= SPIN_SATURATION:
        cl = SPIN_FACTOR * spin_rate_round
    else:
        cl_at_saturation = SPIN_FACTOR * SPIN_SATURATION
        excess_spin = spin_rate_round - SPIN_SATURATION
        cl = cl_at_saturation + SPIN_FACTOR * excess_spin * 0.2
    
    return cd_adjusted, cl


def round_for_cache(value: float, precision: float) -> float:
    """Round value to specified precision for cache efficiency."""
    return round(value / precision) * precision


class OptimizedAerodynamicForces:
    """
    Optimized aerodynamic force calculator using caching and lookup tables.
    
    Provides significant speedup for repeated calculations with similar parameters.
    """
    
    def __init__(self, air_density: float = 1.225):
        """
        Initialize optimized aerodynamics calculator.
        
        Parameters
        ----------
        air_density : float
            Air density in kg/m³
        """
        self.air_density = air_density
        self.cross_sectional_area = BALL_CROSS_SECTIONAL_AREA
        
        # Build lookup tables for common scenarios
        self._build_force_lookup_table()
    
    def _build_force_lookup_table(self):
        """Build lookup tables for common velocity/spin combinations."""
        # Velocity range: 10-50 m/s in 1 m/s steps
        # Spin range: 0-3000 rpm in 100 rpm steps
        self.velocity_table = np.arange(10, 51, 1)  # 41 entries
        self.spin_table = np.arange(0, 3001, 100)   # 31 entries
        
        # Pre-compute drag and lift coefficients
        self.cd_table = np.zeros((len(self.velocity_table), len(self.spin_table)))
        self.cl_table = np.zeros((len(self.velocity_table), len(self.spin_table)))
        
        for i, velocity in enumerate(self.velocity_table):
            for j, spin in enumerate(self.spin_table):
                cd, cl = cached_aerodynamic_params(velocity, spin)
                self.cd_table[i, j] = cd
                self.cl_table[i, j] = cl
    
    def get_coefficients_fast(self, velocity_ms: float, spin_rate_rpm: float) -> tuple:
        """
        Get aerodynamic coefficients using lookup table interpolation.
        
        Parameters
        ----------
        velocity_ms : float
            Velocity magnitude in m/s
        spin_rate_rpm : float
            Spin rate in rpm
            
        Returns
        -------
        tuple
            (drag_coefficient, lift_coefficient)
        """
        # Clamp to table bounds
        v_clamped = np.clip(velocity_ms, self.velocity_table[0], self.velocity_table[-1])
        s_clamped = np.clip(spin_rate_rpm, self.spin_table[0], self.spin_table[-1])
        
        # Find indices for bilinear interpolation
        v_idx = np.searchsorted(self.velocity_table, v_clamped) - 1
        v_idx = np.clip(v_idx, 0, len(self.velocity_table) - 2)
        
        s_idx = np.searchsorted(self.spin_table, s_clamped) - 1  
        s_idx = np.clip(s_idx, 0, len(self.spin_table) - 2)
        
        # Bilinear interpolation weights
        v_weight = (v_clamped - self.velocity_table[v_idx]) / (
            self.velocity_table[v_idx + 1] - self.velocity_table[v_idx]
        )
        s_weight = (s_clamped - self.spin_table[s_idx]) / (
            self.spin_table[s_idx + 1] - self.spin_table[s_idx]
        )
        
        # Interpolate drag coefficient
        cd_00 = self.cd_table[v_idx, s_idx]
        cd_01 = self.cd_table[v_idx, s_idx + 1]
        cd_10 = self.cd_table[v_idx + 1, s_idx]
        cd_11 = self.cd_table[v_idx + 1, s_idx + 1]
        
        cd_interpolated = (
            cd_00 * (1 - v_weight) * (1 - s_weight) +
            cd_01 * (1 - v_weight) * s_weight +
            cd_10 * v_weight * (1 - s_weight) +
            cd_11 * v_weight * s_weight
        )
        
        # Interpolate lift coefficient
        cl_00 = self.cl_table[v_idx, s_idx]
        cl_01 = self.cl_table[v_idx, s_idx + 1]
        cl_10 = self.cl_table[v_idx + 1, s_idx]
        cl_11 = self.cl_table[v_idx + 1, s_idx + 1]
        
        cl_interpolated = (
            cl_00 * (1 - v_weight) * (1 - s_weight) +
            cl_01 * (1 - v_weight) * s_weight +
            cl_10 * v_weight * (1 - s_weight) +
            cl_11 * v_weight * s_weight
        )
        
        return cd_interpolated, cl_interpolated


class UltraFastMode:
    """
    Ultra-fast simulation mode with aggressive approximations.
    
    Trades some accuracy for significant speed improvement:
    - Larger time steps (5-10ms vs 1-2ms)
    - Simplified aerodynamics
    - Reduced precision calculations
    
    Target: 5-10x faster than normal mode with <5% accuracy loss.
    """
    
    # Ultra-fast time step (10ms - 10x faster than default)
    DT_ULTRA_FAST = 0.01
    
    @staticmethod
    def should_use_ultra_fast(simulation_count: int) -> bool:
        """Recommend ultra-fast mode based on simulation count."""
        return simulation_count >= 10000
    
    @staticmethod  
    def get_optimal_time_step(simulation_count: int) -> float:
        """Get optimal time step based on simulation requirements."""
        if simulation_count >= 100000:
            return UltraFastMode.DT_ULTRA_FAST  # 10ms
        elif simulation_count >= 10000:
            return 0.005  # 5ms
        elif simulation_count >= 1000:
            return DT_FAST  # 2ms
        else:
            return DT_DEFAULT  # 1ms


class PerformanceTracker:
    """
    Track simulation performance for optimization and regression detection.
    """
    
    def __init__(self):
        """Initialize performance tracker."""
        self.simulation_times = []
        self.memory_usage = []
        self.cache_hit_rates = {}
    
    def track_simulation(self, duration: float, at_bat_count: int):
        """Track a simulation performance."""
        self.simulation_times.append({
            'duration': duration,
            'at_bats': at_bat_count,
            'rate': at_bat_count / duration if duration > 0 else 0
        })
    
    def get_performance_summary(self) -> Dict[str, Any]:
        """Get performance summary statistics."""
        if not self.simulation_times:
            return {'status': 'No data'}
        
        rates = [sim['rate'] for sim in self.simulation_times]
        
        return {
            'total_simulations': len(self.simulation_times),
            'average_rate': np.mean(rates),
            'median_rate': np.median(rates),
            'std_rate': np.std(rates),
            'min_rate': np.min(rates),
            'max_rate': np.max(rates),
            'cache_stats': self.cache_hit_rates.copy()
        }


# Global performance tracker
_performance_tracker = None

def get_performance_tracker() -> PerformanceTracker:
    """Get the global performance tracker."""
    global _performance_tracker
    if _performance_tracker is None:
        _performance_tracker = PerformanceTracker()
    return _performance_tracker