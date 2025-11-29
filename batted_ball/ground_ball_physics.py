"""
Ground ball physics simulation.

Simulates realistic ground ball bouncing, rolling, and deceleration
based on physics principles including coefficient of restitution,
rolling friction, and spin effects.

COORDINATE SYSTEM:
This module uses FIELD COORDINATES exclusively:
- X-axis: Lateral (positive = RIGHT field, negative = LEFT field)
- Y-axis: Forward direction (positive = toward CENTER field)
- Z-axis: Vertical (positive = up)

Velocities from BattedBallResult are converted from trajectory coordinates
to field coordinates using convert_velocity_trajectory_to_field() at the entry
point (simulate_from_trajectory) to ensure consistency with field positions
and fielder locations.

RUST ACCELERATION:
When the trajectory_rs Rust library is available, this module automatically
uses the native Rust implementation for significant performance gains (~4x).
The Python implementation is kept as a fallback.
"""

import numpy as np
from typing import Tuple, Dict
from .constants import (
    GRAVITY,
    FEET_TO_METERS,
    METERS_TO_FEET,
    MPH_TO_MS,
    MS_TO_MPH,
    GROUND_BALL_COR_DEFAULT,
    GROUND_BALL_COR_GRASS,
    GROUND_BALL_COR_TURF,
    GROUND_BALL_COR_DIRT,
    ROLLING_FRICTION_DEFAULT,
    ROLLING_FRICTION_GRASS,
    ROLLING_FRICTION_TURF,
    ROLLING_FRICTION_DIRT,
    GROUND_BALL_AIR_RESISTANCE,
    BOUNCE_HEIGHT_THRESHOLD,
    MIN_BOUNCES_BEFORE_ROLLING,
    MAX_GROUND_BALL_BOUNCES,
    SPIN_RETENTION_PER_BOUNCE,
)
from .trajectory import convert_velocity_trajectory_to_field

# Try to import Rust ground ball functions
_RUST_GROUND_BALL_AVAILABLE = False
try:
    from trajectory_rs import (
        simulate_ground_ball as _rust_simulate_ground_ball,
        get_ball_position_at_time as _rust_get_ball_position_at_time,
    )
    _RUST_GROUND_BALL_AVAILABLE = True
except ImportError:
    pass


def is_rust_ground_ball_available() -> bool:
    """Check if Rust ground ball physics acceleration is available."""
    return _RUST_GROUND_BALL_AVAILABLE


class GroundBallResult:
    """Result of ground ball simulation."""

    def __init__(self):
        """Initialize ground ball result."""
        self.total_distance = 0.0  # Total horizontal distance traveled (feet)
        self.total_time = 0.0  # Total time from landing to stop (seconds)
        self.final_position = np.array([0.0, 0.0, 0.0])  # Final (x, y, z) in feet
        self.bounces = []  # List of bounce events [(time, x, y, height), ...]
        self.rolling_start_time = 0.0  # When ball transitioned to rolling
        self.time_to_target = None  # Time to reach requested target (seconds)
        self.trajectory_points = []  # List of (time, x, y, z) for visualization


class GroundBallSimulator:
    """
    Simulates ground ball physics including bouncing and rolling.

    Uses realistic physics including:
    - Coefficient of restitution for bounces
    - Rolling friction
    - Spin effects on bounces
    - Air resistance
    """

    def __init__(self, surface_type='grass'):
        """
        Initialize ground ball simulator.

        Parameters
        ----------
        surface_type : str
            'grass', 'turf', or 'dirt' (affects COR and friction)
        """
        self.surface_type = surface_type

        # Set surface-specific parameters
        if surface_type == 'grass':
            self.cor = GROUND_BALL_COR_GRASS
            self.friction = ROLLING_FRICTION_GRASS
        elif surface_type == 'turf':
            self.cor = GROUND_BALL_COR_TURF
            self.friction = ROLLING_FRICTION_TURF
        elif surface_type == 'dirt':
            self.cor = GROUND_BALL_COR_DIRT
            self.friction = ROLLING_FRICTION_DIRT
        else:
            self.cor = GROUND_BALL_COR_DEFAULT
            self.friction = ROLLING_FRICTION_DEFAULT

    def simulate_from_trajectory(self, batted_ball_result, target_position=None,
                                  use_rust=True) -> GroundBallResult:
        """
        Simulate ground ball from batted ball trajectory result.

        Parameters
        ----------
        batted_ball_result : BattedBallResult
            Result from trajectory simulation
        target_position : tuple, optional
            Target (x, y) position in feet to simulate to (e.g., fielder position)
            If None, simulates until ball stops
        use_rust : bool
            Whether to use Rust acceleration when available (default True)

        Returns
        -------
        GroundBallResult
            Complete ground ball simulation result
        """
        # Get landing conditions from trajectory
        landing_velocity = batted_ball_result.velocity[-1]  # m/s
        landing_position = batted_ball_result.position[-1]  # m

        # Convert velocity from trajectory coordinates to field coordinates
        # CRITICAL: Trajectory uses (x=toward outfield, y=lateral), field uses (x=lateral, y=toward CF)
        vx_field_ms, vy_field_ms, vz_field_ms = convert_velocity_trajectory_to_field(
            landing_velocity[0], landing_velocity[1], landing_velocity[2]
        )
        
        # Convert to feet and mph - NOW IN FIELD COORDINATE SYSTEM
        vx = vx_field_ms * MS_TO_MPH  # mph (lateral, right field = +)
        vy = vy_field_ms * MS_TO_MPH  # mph (toward center field = +)
        vz = vz_field_ms * MS_TO_MPH  # mph (usually negative at landing)

        x0 = landing_position[0] * METERS_TO_FEET  # feet (but needs coordinate conversion!)
        y0 = landing_position[1] * METERS_TO_FEET  # feet (but needs coordinate conversion!)
        
        # WAIT: landing position was already converted in trajectory.py
        # But we need to use the field coordinates here
        # Actually, landing_x and landing_y in batted_ball_result are already in field coords
        # Let's use those instead:
        x0 = batted_ball_result.landing_x
        y0 = batted_ball_result.landing_y

        # Get initial spin (estimate from trajectory)
        initial_spin_rpm = batted_ball_result.initial_conditions.get('backspin_rpm', 0.0)

        return self.simulate(x0, y0, vx, vy, vz, initial_spin_rpm, target_position,
                            use_rust=use_rust)

    def simulate(self, x0, y0, vx_mph, vy_mph, vz_mph, spin_rpm=0.0,
                 target_position=None, max_time=10.0, dt=0.01,
                 use_rust=True) -> GroundBallResult:
        """
        Simulate ground ball bouncing and rolling.

        Parameters
        ----------
        x0, y0 : float
            Initial position in feet (ball landing point)
        vx_mph, vy_mph, vz_mph : float
            Initial velocity in mph (ball velocity at landing)
        spin_rpm : float
            Initial backspin in rpm
        target_position : tuple, optional
            (x, y) target position in feet
        max_time : float
            Maximum simulation time in seconds
        dt : float
            Time step in seconds
        use_rust : bool
            Whether to use Rust acceleration when available (default True)

        Returns
        -------
        GroundBallResult
            Complete simulation result
        """
        # Use Rust implementation if available and enabled
        # Rust version is faster but provides less detailed trajectory
        if use_rust and _RUST_GROUND_BALL_AVAILABLE:
            return self._simulate_rust(x0, y0, vx_mph, vy_mph, vz_mph, spin_rpm,
                                       target_position, max_time)
        
        # Fallback to Python implementation
        return self._simulate_python(x0, y0, vx_mph, vy_mph, vz_mph, spin_rpm,
                                     target_position, max_time, dt)
    
    def _simulate_rust(self, x0, y0, vx_mph, vy_mph, vz_mph, spin_rpm,
                       target_position, max_time) -> GroundBallResult:
        """
        Rust-accelerated ground ball simulation.
        
        Uses native Rust implementation for ~4x performance improvement.
        Returns simplified result without detailed bounce tracking.
        """
        result = GroundBallResult()
        
        # Map surface type to is_grass boolean
        is_grass = self.surface_type in ('grass', 'turf')
        
        # Call Rust function
        # Returns: (landing_x, landing_y, landing_vel_mph, dir_x, dir_y, landing_time, friction, spin_effect)
        rust_result = _rust_simulate_ground_ball(
            x0, y0,
            vx_mph, vy_mph, vz_mph,
            spin_rpm, is_grass
        )
        
        landing_x, landing_y, landing_vel_mph, dir_x, dir_y, landing_time, friction, spin_effect = rust_result
        
        # Calculate final position by rolling from landing point
        # Use get_ball_position_at_time to find where ball stops
        # Find total rolling time (when velocity reaches 0)
        # v = v0 - a*t, so t = v0/a
        fps_to_mph = 3600.0 / 5280.0
        decel_fps2 = GRAVITY * METERS_TO_FEET * friction + GROUND_BALL_AIR_RESISTANCE
        landing_vel_fps = landing_vel_mph / fps_to_mph
        rolling_time = landing_vel_fps / decel_fps2 if decel_fps2 > 0 else 5.0
        rolling_time = min(rolling_time, max_time - landing_time)
        
        # Get final position using Rust
        final_pos = _rust_get_ball_position_at_time(
            landing_x, landing_y, landing_vel_mph,
            dir_x, dir_y, friction, spin_effect, rolling_time
        )
        
        total_time = landing_time + rolling_time
        
        # Populate result
        result.total_time = total_time
        result.final_position = np.array([final_pos[0], final_pos[1], 0.0])
        result.total_distance = np.sqrt((final_pos[0] - x0)**2 + (final_pos[1] - y0)**2)
        result.rolling_start_time = landing_time
        
        # Create minimal trajectory points (start and end)
        result.trajectory_points = [
            (0.0, x0, y0, 0.0),
            (landing_time, landing_x, landing_y, 0.0),
            (total_time, final_pos[0], final_pos[1], 0.0)
        ]
        
        # If target position specified, calculate time to target
        if target_position is not None:
            target_x, target_y = target_position
            result.time_to_target = self._find_time_to_target_rust(
                landing_x, landing_y, landing_vel_mph,
                dir_x, dir_y, friction, spin_effect,
                target_x, target_y, rolling_time
            )
        else:
            result.time_to_target = total_time
        
        return result
    
    def _find_time_to_target_rust(self, landing_x, landing_y, landing_vel_mph,
                                   dir_x, dir_y, friction, spin_effect,
                                   target_x, target_y, max_time) -> float:
        """Find time when ball reaches target position using Rust."""
        # Binary search for time when ball is closest to target
        dt = 0.05
        t = 0.0
        min_dist = float('inf')
        best_time = max_time
        
        while t <= max_time:
            pos = _rust_get_ball_position_at_time(
                landing_x, landing_y, landing_vel_mph,
                dir_x, dir_y, friction, spin_effect, t
            )
            dist = np.sqrt((pos[0] - target_x)**2 + (pos[1] - target_y)**2)
            if dist < min_dist:
                min_dist = dist
                best_time = t
            if dist < 3.0:  # Within 3 feet of target
                return t
            t += dt
        
        return best_time
    
    def _simulate_python(self, x0, y0, vx_mph, vy_mph, vz_mph, spin_rpm=0.0,
                         target_position=None, max_time=10.0, dt=0.01) -> GroundBallResult:
        """
        Python implementation of ground ball simulation.
        
        Provides detailed bounce and trajectory tracking.
        """
        result = GroundBallResult()

        # Convert velocities to ft/s using shared constants to avoid drift
        mph_to_fps = MPH_TO_MS * METERS_TO_FEET
        vx = vx_mph * mph_to_fps
        vy = vy_mph * mph_to_fps
        vz = vz_mph * mph_to_fps

        # Current state
        x, y, z = x0, y0, 0.0  # Start at ground level after first bounce
        t = 0.0
        bounce_count = 0
        is_rolling = False
        current_spin = spin_rpm

        # Record initial position
        result.trajectory_points.append((t, x, y, z))

        # Calculate horizontal velocity magnitude
        v_horizontal = np.sqrt(vx**2 + vy**2)

        # Direction unit vector
        if v_horizontal > 0.1:
            dir_x = vx / v_horizontal
            dir_y = vy / v_horizontal
        else:
            # Ball basically stopped
            result.total_distance = 0.0
            result.total_time = 0.0
            result.final_position = np.array([x, y, z])
            return result

        # Simulate bouncing phase
        while t < max_time and bounce_count < MAX_GROUND_BALL_BOUNCES:
            # Check if we've reached target
            if target_position is not None:
                target_x, target_y = target_position
                dist_to_target = np.sqrt((x - target_x)**2 + (y - target_y)**2)
                if dist_to_target < 2.0:  # Within 2 feet of target
                    result.time_to_target = t
                    break

            # Check if ball is rolling (low vertical velocity and multiple bounces)
            if bounce_count >= MIN_BOUNCES_BEFORE_ROLLING and abs(vz) < 5.0:
                is_rolling = True
                result.rolling_start_time = t
                break

            # Simulate one bounce
            # Time to next ground contact (ballistic trajectory)
            if vz >= 0:
                # Ball is moving up, calculate time to peak then to ground
                t_peak = vz / (GRAVITY * METERS_TO_FEET)  # time to peak
                t_bounce = 2 * t_peak  # total time in air
            else:
                # Ball is moving down (shouldn't happen on first bounce)
                t_bounce = dt

            # Don't let bounce time exceed reasonable limits
            t_bounce = max(dt, min(t_bounce, 0.5))

            # Update position during flight
            x += vx * t_bounce
            y += vy * t_bounce

            # Peak height of this bounce
            if vz > 0:
                bounce_height = (vz**2) / (2 * GRAVITY * METERS_TO_FEET)
            else:
                bounce_height = 0.0

            t += t_bounce

            # Record bounce
            result.bounces.append((t, x, y, bounce_height))
            result.trajectory_points.append((t, x, y, bounce_height / 2))  # midpoint
            result.trajectory_points.append((t + t_bounce, x, y, 0.0))  # landing

            # Apply bounce physics
            # Vertical velocity: reversed and reduced by COR
            vz = -vz * self.cor

            # Horizontal velocity: reduced by friction during bounce contact
            # Energy loss from friction with ground
            friction_loss = 0.95  # Keep 95% of horizontal velocity per bounce
            vx *= friction_loss
            vy *= friction_loss
            v_horizontal *= friction_loss

            # Spin affects bounce (backspin increases bounce height and forward roll)
            if current_spin > 100:  # Significant spin
                # Backspin creates "grabbing" effect on ground
                spin_effect = current_spin / 2000.0  # Normalized spin factor
                vz += spin_effect * 3.0  # Adds to vertical velocity
                # Spin also reduces horizontal velocity (grabs the ground)
                vx *= (1.0 - spin_effect * 0.1)
                vy *= (1.0 - spin_effect * 0.1)
                v_horizontal = np.sqrt(vx**2 + vy**2)

            # Decay spin
            current_spin *= SPIN_RETENTION_PER_BOUNCE

            bounce_count += 1

            # Check if velocity is too low (ball essentially stopped)
            if v_horizontal < 2.0:  # Less than ~1.4 mph
                break

        # Simulate rolling phase
        if is_rolling or v_horizontal > 0.1:
            # Rolling friction deceleration (ft/s²)
            decel = GRAVITY * METERS_TO_FEET * self.friction + GROUND_BALL_AIR_RESISTANCE

            # Current horizontal velocity
            v = v_horizontal

            # Simulate rolling until stopped or target reached
            rolling_start_time = t
            while t < max_time and v > 0.5:  # Stop when velocity < 0.5 ft/s (~0.34 mph)
                # Check if we've reached target
                if target_position is not None:
                    target_x, target_y = target_position
                    dist_to_target = np.sqrt((x - target_x)**2 + (y - target_y)**2)
                    if dist_to_target < 3.0:  # Within 3 feet of target
                        result.time_to_target = t
                        break

                # Update velocity (simple friction model)
                v -= decel * dt
                if v < 0:
                    v = 0
                    break

                # Update position
                x += v * dir_x * dt
                y += v * dir_y * dt
                t += dt

                # Record position every 0.1 seconds
                if int(t / 0.1) > int((t - dt) / 0.1):
                    result.trajectory_points.append((t, x, y, 0.0))

                # Safety check - if ball has rolled a very long distance, stop
                if t - rolling_start_time > 5.0:  # Don't roll for more than 5 seconds
                    break

        # Finalize result
        result.total_distance = np.sqrt((x - x0)**2 + (y - y0)**2)
        result.total_time = t
        if result.time_to_target is None:
            result.time_to_target = t
        result.final_position = np.array([x, y, 0.0])
        result.trajectory_points.append((t, x, y, 0.0))

        return result

    def calculate_time_to_position(self, batted_ball_result, target_x, target_y) -> float:
        """
        Calculate time for ground ball to reach a specific position.

        Parameters
        ----------
        batted_ball_result : BattedBallResult
            Batted ball trajectory result
        target_x, target_y : float
            Target position in feet

        Returns
        -------
        float
            Time in seconds for ball to reach target position
        """
        result = self.simulate_from_trajectory(
            batted_ball_result,
            target_position=(target_x, target_y)
        )
        return result.total_time

    def get_ball_position_at_time(self, batted_ball_result, t, use_rust=True) -> Tuple[float, float, float]:
        """
        Get ball position at a specific time during ground ball phase.

        Parameters
        ----------
        batted_ball_result : BattedBallResult
            Batted ball trajectory result
        t : float
            Time in seconds (relative to landing)
        use_rust : bool
            Whether to use Rust acceleration when available (default True)

        Returns
        -------
        tuple
            (x, y, z) position in feet
        """
        # Use Rust implementation if available
        if use_rust and _RUST_GROUND_BALL_AVAILABLE:
            return self._get_ball_position_at_time_rust(batted_ball_result, t)
        
        return self._get_ball_position_at_time_python(batted_ball_result, t)
    
    def _get_ball_position_at_time_rust(self, batted_ball_result, t) -> Tuple[float, float, float]:
        """Rust-accelerated ball position lookup."""
        # Get landing conditions
        landing_velocity = batted_ball_result.velocity[-1]
        
        # Convert velocity to field coordinates
        vx_field_ms, vy_field_ms, vz_field_ms = convert_velocity_trajectory_to_field(
            landing_velocity[0], landing_velocity[1], landing_velocity[2]
        )
        
        # Convert to mph
        vx_mph = vx_field_ms * MS_TO_MPH
        vy_mph = vy_field_ms * MS_TO_MPH
        vz_mph = vz_field_ms * MS_TO_MPH
        
        x0 = batted_ball_result.landing_x
        y0 = batted_ball_result.landing_y
        spin_rpm = batted_ball_result.initial_conditions.get('backspin_rpm', 0.0)
        
        # Map surface type to is_grass boolean
        is_grass = self.surface_type in ('grass', 'turf')
        
        # First simulate the ground ball to get landing parameters
        rust_result = _rust_simulate_ground_ball(
            x0, y0, vx_mph, vy_mph, vz_mph, spin_rpm, is_grass
        )
        landing_x, landing_y, landing_vel_mph, dir_x, dir_y, landing_time, friction, spin_effect = rust_result
        
        # If t is during bouncing phase, interpolate position
        if t < landing_time:
            # Linear interpolation from start to landing
            frac = t / landing_time if landing_time > 0 else 1.0
            px = x0 + frac * (landing_x - x0)
            py = y0 + frac * (landing_y - y0)
            return (px, py, 0.0)
        
        # Time after landing starts
        time_after_landing = t - landing_time
        
        pos = _rust_get_ball_position_at_time(
            landing_x, landing_y, landing_vel_mph,
            dir_x, dir_y, friction, spin_effect, time_after_landing
        )
        return (pos[0], pos[1], 0.0)
    
    def _get_ball_position_at_time_python(self, batted_ball_result, t) -> Tuple[float, float, float]:
        """Python ball position lookup via simulation."""
        # Simulate ground ball
        result = self.simulate_from_trajectory(batted_ball_result, use_rust=False)

        # Find position at time t by interpolating trajectory points
        if t <= 0:
            return tuple(result.trajectory_points[0][1:])

        if t >= result.total_time:
            return tuple(result.final_position)

        # Find bounding points
        for i in range(len(result.trajectory_points) - 1):
            t1, x1, y1, z1 = result.trajectory_points[i]
            t2, x2, y2, z2 = result.trajectory_points[i + 1]

            if t1 <= t <= t2:
                # Linear interpolation
                alpha = (t - t1) / (t2 - t1) if t2 > t1 else 0.0
                x = x1 + alpha * (x2 - x1)
                y = y1 + alpha * (y2 - y1)
                z = z1 + alpha * (z2 - z1)
                return (x, y, z)

        # Fallback to final position
        return tuple(result.final_position)
