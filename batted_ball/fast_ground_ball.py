"""
High-performance ground ball physics using Rust native code.

This module provides ultra-fast ground ball trajectory calculations by using:
1. Rust native code for simulation (10-15× speedup when available)
2. Python fallback when Rust is not installed
3. Parallel fielder interception calculations

Use this for high-volume fielding simulations where maximum speed is critical.
"""

import numpy as np
from typing import Optional, Tuple, List, Dict, Any

from .constants import (
    GRAVITY,
    FEET_TO_METERS,
    METERS_TO_FEET,
    ROLLING_FRICTION_GRASS,
    ROLLING_FRICTION_DIRT,
    GROUND_BALL_COR_GRASS,
    GROUND_BALL_COR_DIRT,
    GROUND_BALL_AIR_RESISTANCE,
    GROUND_BALL_SPIN_EFFECT,
)

# Try to import Rust ground ball library for maximum performance
try:
    import trajectory_rs
    # Check if ground ball functions are available (Phase 8)
    RUST_GROUND_BALL_AVAILABLE = hasattr(trajectory_rs, 'simulate_ground_ball')
except ImportError:
    RUST_GROUND_BALL_AVAILABLE = False
    trajectory_rs = None


def is_rust_ground_ball_available() -> bool:
    """Check if Phase 8 Rust ground ball library is available."""
    return RUST_GROUND_BALL_AVAILABLE


class GroundBallResult:
    """Container for ground ball simulation result."""
    
    def __init__(
        self,
        landing_position: Tuple[float, float],
        landing_velocity_mph: float,
        direction: Tuple[float, float],
        landing_time: float,
        friction: float,
        spin_effect: float,
    ):
        """
        Initialize ground ball result.
        
        Parameters
        ----------
        landing_position : tuple
            (x, y) position where ball starts rolling (feet)
        landing_velocity_mph : float
            Ball velocity at start of rolling phase (mph)
        direction : tuple
            (dx, dy) unit vector of travel direction
        landing_time : float
            Time when ball starts rolling (seconds)
        friction : float
            Rolling friction coefficient
        spin_effect : float
            Spin effect on trajectory curvature
        """
        self.landing_position = landing_position
        self.landing_velocity_mph = landing_velocity_mph
        self.direction = direction
        self.landing_time = landing_time
        self.friction = friction
        self.spin_effect = spin_effect


class InterceptionResult:
    """Container for fielder interception result."""
    
    def __init__(
        self,
        can_intercept: bool,
        interception_point: Tuple[float, float],
        fielder_time: float,
        ball_time: float,
        margin: float,
        ball_velocity_mph: float,
    ):
        """
        Initialize interception result.
        
        Parameters
        ----------
        can_intercept : bool
            Whether fielder can reach the ball
        interception_point : tuple
            (x, y) where interception occurs (feet)
        fielder_time : float
            Time for fielder to reach interception point (seconds)
        ball_time : float
            Time for ball to reach interception point (seconds)
        margin : float
            Time margin (positive = fielder arrives first)
        ball_velocity_mph : float
            Ball velocity at interception (mph)
        """
        self.can_intercept = can_intercept
        self.interception_point = interception_point
        self.fielder_time = fielder_time
        self.ball_time = ball_time
        self.margin = margin
        self.ball_velocity_mph = ball_velocity_mph


class FastGroundBallSimulator:
    """
    High-performance ground ball simulator with Rust backend.
    
    This class provides maximum performance for ground ball physics by
    leveraging:
    - Rust native code for simulation (10-15× faster when available)
    - Parallel interception calculations across multiple fielders
    - Optimized physics with bouncing and rolling phases
    
    Performance improvements over pure Python:
    - With Rust: ~10-15× faster for ground ball simulation
    - With parallel interception: ~4× faster for multi-fielder scenarios
    
    Example
    -------
    >>> sim = FastGroundBallSimulator()
    >>> result = sim.simulate_ground_ball(
    ...     x0=0, y0=0,
    ...     vx_mph=50, vy_mph=60, vz_mph=-5,
    ...     spin_rpm=1000
    ... )
    >>> print(f"Landing at ({result.landing_position[0]:.1f}, {result.landing_position[1]:.1f})")
    """
    
    def __init__(
        self,
        use_rust: Optional[bool] = None,
        surface: str = "grass",
    ):
        """
        Initialize fast ground ball simulator.
        
        Parameters
        ----------
        use_rust : bool, optional
            If True, use Rust native code when available.
            If None, auto-detect based on availability.
        surface : str
            Playing surface type: "grass" or "dirt"
        """
        if use_rust is not None:
            self.use_rust = use_rust and RUST_GROUND_BALL_AVAILABLE
        else:
            self.use_rust = RUST_GROUND_BALL_AVAILABLE
        
        self.surface = surface
        self.is_grass = surface.lower() == "grass"
        
        # Surface-specific parameters
        if self.is_grass:
            self.friction = ROLLING_FRICTION_GRASS
            self.cor = GROUND_BALL_COR_GRASS
        else:
            self.friction = ROLLING_FRICTION_DIRT
            self.cor = GROUND_BALL_COR_DIRT
    
    def simulate_ground_ball(
        self,
        x0: float,
        y0: float,
        vx_mph: float,
        vy_mph: float,
        vz_mph: float = 0.0,
        spin_rpm: float = 500.0,
    ) -> GroundBallResult:
        """
        Simulate ground ball trajectory.
        
        Parameters
        ----------
        x0 : float
            Starting X position (feet, + = right field)
        y0 : float
            Starting Y position (feet, + = center field)
        vx_mph : float
            X velocity (mph)
        vy_mph : float
            Y velocity (mph)
        vz_mph : float
            Z velocity (mph, typically small negative for ground balls)
        spin_rpm : float
            Spin rate (rpm), affects trajectory curvature
        
        Returns
        -------
        GroundBallResult
            Simulation result with landing position, velocity, and physics params
        """
        if self.use_rust:
            # Use Rust native implementation
            (landing_x, landing_y, landing_vel, dir_x, dir_y,
             landing_time, friction, spin_effect) = trajectory_rs.simulate_ground_ball(
                x0, y0, vx_mph, vy_mph, vz_mph, spin_rpm, self.is_grass
            )
            return GroundBallResult(
                landing_position=(landing_x, landing_y),
                landing_velocity_mph=landing_vel,
                direction=(dir_x, dir_y),
                landing_time=landing_time,
                friction=friction,
                spin_effect=spin_effect,
            )
        else:
            # Python fallback implementation
            return self._simulate_ground_ball_python(
                x0, y0, vx_mph, vy_mph, vz_mph, spin_rpm
            )
    
    def _simulate_ground_ball_python(
        self,
        x0: float,
        y0: float,
        vx_mph: float,
        vy_mph: float,
        vz_mph: float,
        spin_rpm: float,
    ) -> GroundBallResult:
        """Python fallback for ground ball simulation."""
        # Convert velocities to ft/s
        vx_fps = vx_mph * 5280.0 / 3600.0
        vy_fps = vy_mph * 5280.0 / 3600.0
        vz_fps = vz_mph * 5280.0 / 3600.0
        
        # Initial horizontal velocity magnitude
        vh_fps = np.sqrt(vx_fps**2 + vy_fps**2)
        
        # Calculate spin effect
        spin_effect = (spin_rpm / 1000.0) * GROUND_BALL_SPIN_EFFECT
        
        # Direction of travel
        if vh_fps > 1e-6:
            direction = (vx_fps / vh_fps, vy_fps / vh_fps)
        else:
            direction = (1.0, 0.0)
        
        # Simulate bouncing phase
        pos = [x0, y0]
        vz = vz_fps
        vh = vh_fps
        time = 0.0
        g = GRAVITY * METERS_TO_FEET
        
        # Maximum 3 bounces, or until vertical energy is low
        bounces = 0
        while bounces < 3 and abs(vz) > 1.0:
            if vz > 0:
                # Going up then down
                t_up = vz / g
                t_air = 2 * t_up
                
                # Move horizontally during air time
                distance = vh * t_air
                pos[0] += distance * direction[0]
                pos[1] += distance * direction[1]
                time += t_air
                
                # Lose energy on bounce
                vz = vz * self.cor
                vh = vh * (1.0 - self.friction * 0.1)
            else:
                # Already going down (first impact)
                vz = (-vz) * self.cor
            
            bounces += 1
        
        # Convert horizontal velocity back to mph
        landing_velocity_mph = vh * 3600.0 / 5280.0
        
        return GroundBallResult(
            landing_position=tuple(pos),
            landing_velocity_mph=landing_velocity_mph,
            direction=direction,
            landing_time=time,
            friction=self.friction,
            spin_effect=spin_effect,
        )
    
    def get_ball_position_at_time(
        self,
        result: GroundBallResult,
        time_after_landing: float,
    ) -> Tuple[Tuple[float, float], float]:
        """
        Get ball position and velocity at a given time after landing.
        
        Parameters
        ----------
        result : GroundBallResult
            Result from simulate_ground_ball
        time_after_landing : float
            Time since ball started rolling (seconds)
        
        Returns
        -------
        tuple
            ((x, y), velocity_mph) at the specified time
        """
        if self.use_rust:
            x, y, vel = trajectory_rs.get_ball_position_at_time(
                result.landing_position[0],
                result.landing_position[1],
                result.landing_velocity_mph,
                result.direction[0],
                result.direction[1],
                result.friction,
                result.spin_effect,
                time_after_landing,
            )
            return ((x, y), vel)
        else:
            return self._get_ball_position_python(result, time_after_landing)
    
    def _get_ball_position_python(
        self,
        result: GroundBallResult,
        time_after_landing: float,
    ) -> Tuple[Tuple[float, float], float]:
        """Python fallback for ball position calculation."""
        if time_after_landing <= 0:
            return (result.landing_position, result.landing_velocity_mph)
        
        # Deceleration in ft/s²
        decel = GRAVITY * METERS_TO_FEET * result.friction + GROUND_BALL_AIR_RESISTANCE
        
        # Convert initial velocity to ft/s
        v0_fps = result.landing_velocity_mph * 5280.0 / 3600.0
        
        # Time to stop
        time_to_stop = v0_fps / decel
        effective_time = min(time_after_landing, time_to_stop)
        
        # Distance traveled
        distance = v0_fps * effective_time - 0.5 * decel * effective_time**2
        
        # Apply spin effect (curve the path slightly)
        curve_factor = result.spin_effect * effective_time * 0.1
        curved_dir = [
            result.direction[0] - curve_factor * result.direction[1],
            result.direction[1] + curve_factor * result.direction[0],
        ]
        dir_mag = np.sqrt(curved_dir[0]**2 + curved_dir[1]**2)
        if dir_mag > 1e-6:
            normalized_dir = (curved_dir[0] / dir_mag, curved_dir[1] / dir_mag)
        else:
            normalized_dir = result.direction
        
        # New position
        pos = (
            result.landing_position[0] + distance * normalized_dir[0],
            result.landing_position[1] + distance * normalized_dir[1],
        )
        
        # Current velocity
        current_velocity_fps = max(0, v0_fps - decel * effective_time)
        current_velocity_mph = current_velocity_fps * 3600.0 / 5280.0
        
        return (pos, current_velocity_mph)
    
    def calculate_fielder_travel_time(
        self,
        distance_ft: float,
        sprint_speed_fps: float,
        reaction_time: float = 0.3,
        acceleration: float = 28.0,
    ) -> float:
        """
        Calculate fielder travel time to a given distance.
        
        Parameters
        ----------
        distance_ft : float
            Distance to travel (feet)
        sprint_speed_fps : float
            Fielder sprint speed (ft/s)
        reaction_time : float
            Initial reaction delay (seconds)
        acceleration : float
            Acceleration rate (ft/s²)
        
        Returns
        -------
        float
            Total time to reach destination
        """
        if self.use_rust:
            return trajectory_rs.calculate_fielder_travel_time(
                distance_ft, sprint_speed_fps, reaction_time, acceleration
            )
        else:
            return self._calculate_travel_time_python(
                distance_ft, sprint_speed_fps, reaction_time, acceleration
            )
    
    def _calculate_travel_time_python(
        self,
        distance_ft: float,
        sprint_speed_fps: float,
        reaction_time: float,
        acceleration: float,
    ) -> float:
        """Python fallback for fielder travel time."""
        if distance_ft <= 0:
            return reaction_time
        
        max_speed = min(sprint_speed_fps, 30.0)
        
        # Distance to reach max speed
        accel_distance = (max_speed ** 2) / (2.0 * acceleration)
        
        if distance_ft <= accel_distance:
            # Never reaches max speed
            travel_time = np.sqrt(2.0 * distance_ft / acceleration)
        else:
            # Time to reach max speed + time at max speed
            time_to_max = max_speed / acceleration
            remaining_distance = distance_ft - accel_distance
            travel_time = time_to_max + remaining_distance / max_speed
        
        return reaction_time + travel_time
    
    def find_interception_point(
        self,
        ground_ball_result: GroundBallResult,
        fielder_x: float,
        fielder_y: float,
        sprint_speed_fps: float,
        reaction_time: float = 0.3,
        exit_velocity_mph: float = 80.0,
    ) -> InterceptionResult:
        """
        Find optimal interception point for a fielder.
        
        Parameters
        ----------
        ground_ball_result : GroundBallResult
            Result from simulate_ground_ball
        fielder_x : float
            Fielder starting X position (feet)
        fielder_y : float  
            Fielder starting Y position (feet)
        sprint_speed_fps : float
            Fielder sprint speed (ft/s)
        reaction_time : float
            Fielder reaction time (seconds)
        exit_velocity_mph : float
            Original exit velocity (for charge bonus calculation)
        
        Returns
        -------
        InterceptionResult
            Interception details including can_intercept, position, times, margin
        """
        if self.use_rust:
            (can_intercept, intercept_x, intercept_y, fielder_time,
             ball_time, margin, ball_vel) = trajectory_rs.find_interception_point(
                ground_ball_result.landing_position[0],
                ground_ball_result.landing_position[1],
                ground_ball_result.landing_velocity_mph,
                ground_ball_result.direction[0],
                ground_ball_result.direction[1],
                ground_ball_result.landing_time,
                ground_ball_result.friction,
                ground_ball_result.spin_effect,
                fielder_x,
                fielder_y,
                sprint_speed_fps,
                reaction_time,
                exit_velocity_mph,
            )
            return InterceptionResult(
                can_intercept=can_intercept,
                interception_point=(intercept_x, intercept_y),
                fielder_time=fielder_time,
                ball_time=ball_time,
                margin=margin,
                ball_velocity_mph=ball_vel,
            )
        else:
            return self._find_interception_python(
                ground_ball_result, fielder_x, fielder_y,
                sprint_speed_fps, reaction_time, exit_velocity_mph
            )
    
    def _find_interception_python(
        self,
        result: GroundBallResult,
        fielder_x: float,
        fielder_y: float,
        sprint_speed_fps: float,
        reaction_time: float,
        exit_velocity_mph: float,
    ) -> InterceptionResult:
        """Python fallback for interception calculation."""
        # Calculate charge bonus
        dx = result.landing_position[0] - fielder_x
        dy = result.landing_position[1] - fielder_y
        distance_to_landing = np.sqrt(dx**2 + dy**2)
        
        velocity_factor = np.clip(1.0 - (exit_velocity_mph - 60.0) / 60.0, 0.2, 1.0)
        distance_factor = np.clip(distance_to_landing / 150.0, 0.3, 1.0)
        speed_factor = sprint_speed_fps / 27.0
        charge_bonus = min(20.0, 20.0 * velocity_factor * distance_factor * speed_factor)
        
        best_result = InterceptionResult(
            can_intercept=False,
            interception_point=(0, 0),
            fielder_time=float('inf'),
            ball_time=0,
            margin=float('-inf'),
            ball_velocity_mph=0,
        )
        
        # Test interception points at different times
        max_test_time = 6.0
        time_step = 0.05
        
        test_time = 0.0
        while test_time <= max_test_time:
            pos, ball_vel = self.get_ball_position_at_time(result, test_time)
            
            if ball_vel < 0.1:
                break
            
            # Distance from fielder to this point
            dx = pos[0] - fielder_x
            dy = pos[1] - fielder_y
            distance = np.sqrt(dx**2 + dy**2)
            
            # Apply charge bonus
            effective_distance = max(0, distance - charge_bonus)
            
            # Time for fielder to reach this point
            fielder_time = self.calculate_fielder_travel_time(
                effective_distance, sprint_speed_fps, reaction_time
            )
            
            # Total ball time = landing time + rolling time
            total_ball_time = result.landing_time + test_time
            
            # Margin: positive = fielder arrives first
            margin = total_ball_time - fielder_time
            
            if margin > best_result.margin:
                best_result = InterceptionResult(
                    can_intercept=margin >= 0,
                    interception_point=pos,
                    fielder_time=fielder_time,
                    ball_time=total_ball_time,
                    margin=margin,
                    ball_velocity_mph=ball_vel,
                )
            
            test_time += time_step
        
        return best_result
    
    def find_best_interception(
        self,
        ground_ball_result: GroundBallResult,
        fielder_positions: np.ndarray,
        fielder_speeds: np.ndarray,
        reaction_times: np.ndarray,
        exit_velocity_mph: float = 80.0,
    ) -> Tuple[int, InterceptionResult]:
        """
        Find the best fielder to intercept the ground ball.
        
        Parameters
        ----------
        ground_ball_result : GroundBallResult
            Result from simulate_ground_ball
        fielder_positions : np.ndarray
            Array of (x, y) fielder positions, shape (N, 2)
        fielder_speeds : np.ndarray
            Array of fielder sprint speeds (ft/s), shape (N,)
        reaction_times : np.ndarray
            Array of fielder reaction times (seconds), shape (N,)
        exit_velocity_mph : float
            Original exit velocity (for charge bonus)
        
        Returns
        -------
        tuple
            (best_fielder_index, InterceptionResult)
            best_fielder_index is -1 if no fielder can intercept
        """
        if self.use_rust:
            (best_idx, can_intercept, intercept_x, intercept_y,
             fielder_time, ball_time, margin, ball_vel) = trajectory_rs.find_best_interception(
                ground_ball_result.landing_position[0],
                ground_ball_result.landing_position[1],
                ground_ball_result.landing_velocity_mph,
                ground_ball_result.direction[0],
                ground_ball_result.direction[1],
                ground_ball_result.landing_time,
                ground_ball_result.friction,
                ground_ball_result.spin_effect,
                np.ascontiguousarray(fielder_positions, dtype=np.float64),
                np.ascontiguousarray(fielder_speeds, dtype=np.float64),
                np.ascontiguousarray(reaction_times, dtype=np.float64),
                exit_velocity_mph,
            )
            result = InterceptionResult(
                can_intercept=can_intercept,
                interception_point=(intercept_x, intercept_y),
                fielder_time=fielder_time,
                ball_time=ball_time,
                margin=margin,
                ball_velocity_mph=ball_vel,
            )
            return (best_idx, result)
        else:
            return self._find_best_interception_python(
                ground_ball_result, fielder_positions, fielder_speeds,
                reaction_times, exit_velocity_mph
            )
    
    def _find_best_interception_python(
        self,
        result: GroundBallResult,
        fielder_positions: np.ndarray,
        fielder_speeds: np.ndarray,
        reaction_times: np.ndarray,
        exit_velocity_mph: float,
    ) -> Tuple[int, InterceptionResult]:
        """Python fallback for finding best interception."""
        best_idx = -1
        best_result = InterceptionResult(
            can_intercept=False,
            interception_point=(0, 0),
            fielder_time=float('inf'),
            ball_time=0,
            margin=float('-inf'),
            ball_velocity_mph=0,
        )
        
        for i in range(len(fielder_positions)):
            intercept = self.find_interception_point(
                result,
                fielder_positions[i, 0],
                fielder_positions[i, 1],
                fielder_speeds[i],
                reaction_times[i],
                exit_velocity_mph,
            )
            
            if intercept.margin > best_result.margin:
                best_idx = i
                best_result = intercept
        
        return (best_idx, best_result)


def benchmark_ground_ball_speedup(n_simulations: int = 1000) -> Dict[str, Any]:
    """
    Benchmark Rust ground ball speedup vs Python.
    
    Parameters
    ----------
    n_simulations : int
        Number of ground ball simulations to run
    
    Returns
    -------
    dict
        Benchmark results with timing info
    """
    import time
    
    # Generate test data
    np.random.seed(42)
    x0 = np.zeros(n_simulations)
    y0 = np.zeros(n_simulations)
    vx_mph = np.random.uniform(40, 80, n_simulations)
    vy_mph = np.random.uniform(50, 90, n_simulations)
    vz_mph = np.random.uniform(-10, 0, n_simulations)
    spin_rpm = np.random.uniform(500, 1500, n_simulations)
    
    results = {}
    
    # Benchmark Rust if available
    if RUST_GROUND_BALL_AVAILABLE:
        rust_sim = FastGroundBallSimulator(use_rust=True)
        
        # Warm up
        _ = rust_sim.simulate_ground_ball(0, 0, 50, 60, -5, 1000)
        
        start = time.time()
        for i in range(n_simulations):
            _ = rust_sim.simulate_ground_ball(
                x0[i], y0[i], vx_mph[i], vy_mph[i], vz_mph[i], spin_rpm[i]
            )
        rust_time = time.time() - start
        
        results['rust_time'] = rust_time
        results['rust_per_sim'] = rust_time / n_simulations
        results['rust_sims_per_sec'] = n_simulations / rust_time
    
    # Benchmark Python
    python_sim = FastGroundBallSimulator(use_rust=False)
    
    start = time.time()
    for i in range(n_simulations):
        _ = python_sim.simulate_ground_ball(
            x0[i], y0[i], vx_mph[i], vy_mph[i], vz_mph[i], spin_rpm[i]
        )
    python_time = time.time() - start
    
    results['python_time'] = python_time
    results['python_per_sim'] = python_time / n_simulations
    results['python_sims_per_sec'] = n_simulations / python_time
    
    if RUST_GROUND_BALL_AVAILABLE:
        results['speedup'] = python_time / rust_time
    else:
        results['speedup'] = 1.0
        results['rust_available'] = False
    
    results['n_simulations'] = n_simulations
    
    return results


# Re-export for convenience
__all__ = [
    'FastGroundBallSimulator',
    'GroundBallResult',
    'InterceptionResult',
    'is_rust_ground_ball_available',
    'benchmark_ground_ball_speedup',
]
