"""
Ground ball physics simulation.

Simulates realistic ground ball bouncing, rolling, and deceleration
based on physics principles including coefficient of restitution,
rolling friction, and spin effects.
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

    def simulate_from_trajectory(self, batted_ball_result, target_position=None) -> GroundBallResult:
        """
        Simulate ground ball from batted ball trajectory result.

        Parameters
        ----------
        batted_ball_result : BattedBallResult
            Result from trajectory simulation
        target_position : tuple, optional
            Target (x, y) position in feet to simulate to (e.g., fielder position)
            If None, simulates until ball stops

        Returns
        -------
        GroundBallResult
            Complete ground ball simulation result
        """
        # Get landing conditions from trajectory
        landing_velocity = batted_ball_result.velocity[-1]  # m/s
        landing_position = batted_ball_result.position[-1]  # m

        # Convert to feet and mph
        vx = landing_velocity[0] * MS_TO_MPH  # mph
        vy = landing_velocity[1] * MS_TO_MPH  # mph
        vz = landing_velocity[2] * MS_TO_MPH  # mph (usually negative at landing)

        x0 = landing_position[0] * METERS_TO_FEET  # feet
        y0 = landing_position[1] * METERS_TO_FEET  # feet

        # Get initial spin (estimate from trajectory)
        initial_spin_rpm = batted_ball_result.initial_conditions.get('backspin_rpm', 0.0)

        return self.simulate(x0, y0, vx, vy, vz, initial_spin_rpm, target_position)

    def simulate(self, x0, y0, vx_mph, vy_mph, vz_mph, spin_rpm=0.0,
                 target_position=None, max_time=10.0, dt=0.01) -> GroundBallResult:
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

        Returns
        -------
        GroundBallResult
            Complete simulation result
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

    def get_ball_position_at_time(self, batted_ball_result, t) -> Tuple[float, float, float]:
        """
        Get ball position at a specific time during ground ball phase.

        Parameters
        ----------
        batted_ball_result : BattedBallResult
            Batted ball trajectory result
        t : float
            Time in seconds (relative to landing)

        Returns
        -------
        tuple
            (x, y, z) position in feet
        """
        # Simulate ground ball
        result = self.simulate_from_trajectory(batted_ball_result)

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
