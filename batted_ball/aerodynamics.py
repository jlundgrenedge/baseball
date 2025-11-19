"""
Aerodynamic forces on a baseball.

This module calculates:
- Drag force (opposes velocity)
- Magnus force (spin-induced lift, perpendicular to velocity)

Optimized with numba JIT compilation for performance.
"""

import numpy as np
from numba import njit
from .constants import (
    BALL_CROSS_SECTIONAL_AREA,
    BALL_DIAMETER,
    BALL_MASS,
    CD_BASE,
    CD_MIN,
    CD_MAX,
    CL_BASE,
    SPIN_FACTOR,
    SPIN_SATURATION,
    SPIN_DRAG_FACTOR,
    SPIN_DRAG_MAX_INCREASE,
    TILTED_SPIN_DRAG_FACTOR,
    REYNOLDS_DRAG_ENABLED,
    RE_CRITICAL_LOW,
    RE_CRITICAL_HIGH,
    CD_SUBCRITICAL_INCREASE,
    CD_SUPERCRITICAL_DECREASE,
    AIR_DYNAMIC_VISCOSITY,
)


# Numba-optimized helper functions for hot path calculations
@njit(cache=True)
def _norm_3d(v):
    """Fast 3D vector norm calculation."""
    return np.sqrt(v[0]*v[0] + v[1]*v[1] + v[2]*v[2])

@njit(cache=True)
def _normalize_3d(v):
    """Fast 3D vector normalization."""
    mag = _norm_3d(v)
    if mag < 1e-6:
        return np.zeros(3), 0.0
    return v / mag, mag

@njit(cache=True)
def _cross_3d(a, b):
    """Fast 3D cross product."""
    result = np.empty(3)
    result[0] = a[1] * b[2] - a[2] * b[1]
    result[1] = a[2] * b[0] - a[0] * b[2]
    result[2] = a[0] * b[1] - a[1] * b[0]
    return result

@njit(cache=True)
def _calculate_reynolds_number(velocity_magnitude, air_density, ball_diameter=BALL_DIAMETER,
                                 air_viscosity=AIR_DYNAMIC_VISCOSITY):
    """
    Calculate Reynolds number for the baseball.

    Re = ρVD/μ

    Parameters
    ----------
    velocity_magnitude : float
        Speed in m/s
    air_density : float
        Air density in kg/m³
    ball_diameter : float
        Ball diameter in m
    air_viscosity : float
        Dynamic viscosity in kg/(m·s)

    Returns
    -------
    float
        Reynolds number (dimensionless)
    """
    if velocity_magnitude < 1e-6:
        return 0.0

    return (air_density * velocity_magnitude * ball_diameter) / air_viscosity


@njit(cache=True)
def _calculate_reynolds_dependent_cd(velocity_magnitude, air_density, base_cd=CD_BASE):
    """
    Calculate drag coefficient based on Reynolds number.

    Implements velocity-dependent drag to account for aerodynamic regime transitions:
    - Subcritical (Re < 200k): Higher drag (CD increases)
    - Critical (200k < Re < 250k): Baseline drag (CD ≈ 0.32)
    - Supercritical (Re > 250k): Lower drag (CD decreases)

    This matches baseball aerodynamics research showing "drag crisis" effects.

    Parameters
    ----------
    velocity_magnitude : float
        Speed in m/s
    air_density : float
        Air density in kg/m³
    base_cd : float
        Baseline drag coefficient for critical regime

    Returns
    -------
    float
        Reynolds-adjusted drag coefficient
    """
    if not REYNOLDS_DRAG_ENABLED:
        return base_cd

    # Calculate Reynolds number
    reynolds = _calculate_reynolds_number(velocity_magnitude, air_density)

    if reynolds < RE_CRITICAL_LOW:
        # Subcritical regime: increase drag
        # Linear interpolation from base to base + increase
        re_diff = RE_CRITICAL_LOW - reynolds
        re_range = 50000.0  # Transition range
        cd_increase = CD_SUBCRITICAL_INCREASE * min(re_diff / re_range, 1.0)
        cd = base_cd + cd_increase
    elif reynolds > RE_CRITICAL_HIGH:
        # Supercritical regime: decrease drag
        # Linear interpolation from base to base - decrease
        re_diff = reynolds - RE_CRITICAL_HIGH
        re_range = 50000.0  # Transition range
        cd_decrease = CD_SUPERCRITICAL_DECREASE * min(re_diff / re_range, 1.0)
        cd = base_cd - cd_decrease
    else:
        # Critical regime: use baseline
        cd = base_cd

    # Clip to physical bounds
    return min(max(cd, CD_MIN), CD_MAX)


@njit(cache=True)
def _calculate_lift_coefficient_fast(spin_rate_rpm):
    """Fast lift coefficient calculation."""
    if spin_rate_rpm <= SPIN_SATURATION:
        return SPIN_FACTOR * spin_rate_rpm
    else:
        cl_at_saturation = SPIN_FACTOR * SPIN_SATURATION
        excess_spin = spin_rate_rpm - SPIN_SATURATION
        return cl_at_saturation + SPIN_FACTOR * excess_spin * 0.2

@njit(cache=True)
def _calculate_spin_adjusted_cd_fast(base_cd, spin_rate_rpm, velocity_unit, spin_axis_unit, v_mag, air_density):
    """
    Calculate spin-adjusted drag coefficient.

    Includes:
    1. Reynolds-dependent base CD (velocity effects)
    2. Spin-induced drag increase
    3. Asymmetric drag for tilted spin axis

    Parameters
    ----------
    base_cd : float
        Base drag coefficient (before Reynolds adjustment)
    spin_rate_rpm : float
        Spin rate in RPM
    velocity_unit : np.ndarray
        Normalized velocity vector
    spin_axis_unit : np.ndarray
        Normalized spin axis vector
    v_mag : float
        Velocity magnitude in m/s
    air_density : float
        Air density in kg/m³

    Returns
    -------
    float
        Effective drag coefficient
    """
    # Start with Reynolds-dependent base CD
    cd_adjusted = _calculate_reynolds_dependent_cd(v_mag, air_density, base_cd)

    # Add drag increase from total spin rate
    if spin_rate_rpm > 0:
        spin_drag_increase = SPIN_DRAG_FACTOR * spin_rate_rpm
        spin_drag_increase = min(spin_drag_increase, SPIN_DRAG_MAX_INCREASE)
        cd_adjusted += spin_drag_increase

    # Add asymmetric drag for tilted spin axis
    if spin_rate_rpm > 100 and v_mag > 1e-6:
        cross_prod = _cross_3d(velocity_unit, spin_axis_unit)
        cross_mag = _norm_3d(cross_prod)

        if cross_mag > 1e-6:
            cross_unit = cross_prod / cross_mag
            vertical_component = abs(cross_unit[2])
            horizontal_component = np.sqrt(cross_unit[0]**2 + cross_unit[1]**2)

            if horizontal_component > 0.1:
                tilted_drag = TILTED_SPIN_DRAG_FACTOR * spin_rate_rpm * horizontal_component
                cd_adjusted += tilted_drag

    return cd_adjusted

@njit(cache=True)
def calculate_aerodynamic_forces_fast(velocity, spin_axis, spin_rate_rpm, cd_base, air_density, cross_area):
    """
    Optimized calculation of total aerodynamic forces.

    This function is JIT-compiled with numba for maximum performance.
    Used in the hot loop during trajectory integration.

    Now includes Reynolds-number dependent drag coefficient for improved accuracy
    across different exit velocities (Statcast calibration, Nov 2025).

    Returns: (total_force, drag_force, magnus_force)
    """
    # Normalize velocity
    velocity_unit, v_mag = _normalize_3d(velocity)

    if v_mag < 1e-6:
        return np.zeros(3), np.zeros(3), np.zeros(3)

    # Normalize spin axis
    spin_axis_unit, spin_mag = _normalize_3d(spin_axis)

    # Calculate spin-adjusted drag coefficient (includes Reynolds effects)
    cd_effective = _calculate_spin_adjusted_cd_fast(
        cd_base, spin_rate_rpm, velocity_unit, spin_axis_unit, v_mag, air_density
    )

    # Drag force: F_d = 0.5 * C_d * rho * A * v²
    drag_magnitude = 0.5 * cd_effective * air_density * cross_area * v_mag * v_mag
    drag_force = -drag_magnitude * velocity_unit

    # Magnus force
    magnus_force = np.zeros(3)
    if v_mag > 1e-6 and spin_rate_rpm > 1.0 and spin_mag > 1e-6:
        # Calculate lift coefficient
        cl = _calculate_lift_coefficient_fast(spin_rate_rpm)

        # Magnus force magnitude: F_m = 0.5 * C_l * rho * A * v²
        magnus_magnitude = 0.5 * cl * air_density * cross_area * v_mag * v_mag

        # Direction: perpendicular to velocity and spin axis
        force_direction = _cross_3d(velocity_unit, spin_axis_unit)
        force_dir_unit, force_dir_mag = _normalize_3d(force_direction)

        if force_dir_mag > 1e-6:
            magnus_force = magnus_magnitude * force_dir_unit

    total_force = drag_force + magnus_force

    return total_force, drag_force, magnus_force


@njit(cache=True)
def aerodynamic_force_tuple(position, velocity, spin_axis_x, spin_axis_y, spin_axis_z,
                              spin_rate_rpm, cd_base, air_density, cross_area):
    """
    Aerodynamic force function compatible with JIT integrator.

    Returns force components as tuple (fx, fy, fz) for use with integrate_trajectory_jit.

    This is a wrapper optimized for use in the Numba-compiled integration loop.

    Parameters
    ----------
    position : np.ndarray
        Position vector [x, y, z] (not used for aerodynamics, but required for interface)
    velocity : np.ndarray
        Velocity vector [vx, vy, vz] in m/s
    spin_axis_x, spin_axis_y, spin_axis_z : float
        Spin axis components
    spin_rate_rpm : float
        Spin rate in RPM
    cd_base : float
        Base drag coefficient
    air_density : float
        Air density in kg/m³
    cross_area : float
        Cross-sectional area in m²

    Returns
    -------
    tuple of (fx, fy, fz)
        Force components in Newtons
    """
    spin_axis = np.array([spin_axis_x, spin_axis_y, spin_axis_z])
    total_force, _, _ = calculate_aerodynamic_forces_fast(
        velocity, spin_axis, spin_rate_rpm, cd_base, air_density, cross_area
    )
    return total_force[0], total_force[1], total_force[2]


class AerodynamicForces:
    """
    Calculator for aerodynamic forces on a baseball.

    Computes drag and Magnus (lift) forces based on velocity,
    spin rate, and air density.
    """

    def __init__(self, air_density=1.225):
        """
        Initialize aerodynamics calculator.

        Parameters
        ----------
        air_density : float
            Air density in kg/m³ (default: 1.225 = sea level)
        """
        self.air_density = air_density
        self.cross_sectional_area = BALL_CROSS_SECTIONAL_AREA

    def calculate_drag_force(self, velocity_vector, cd=None, spin_rate_rpm=0.0, spin_axis=None):
        """
        Calculate drag force opposing the baseball's motion.

        Drag force: F_d = 0.5 * C_d * rho * A * v²
        Direction: Opposite to velocity vector

        Note: Drag coefficient can be increased by spin rate (spinning balls
        experience higher drag due to turbulent boundary layer effects).

        Parameters
        ----------
        velocity_vector : np.ndarray
            Velocity vector [vx, vy, vz] in m/s
        cd : float, optional
            Base drag coefficient. If None, uses default CD_BASE.
        spin_rate_rpm : float, optional
            Total spin rate in rpm (for spin-dependent drag)
        spin_axis : np.ndarray, optional
            Spin axis unit vector (for asymmetric drag calculation)

        Returns
        -------
        np.ndarray
            Drag force vector [Fx, Fy, Fz] in Newtons
        """
        if cd is None:
            # Use speed-dependent drag coefficient based on research
            cd = adjust_drag_coefficient(np.linalg.norm(velocity_vector))

        # Velocity magnitude
        v_mag = np.linalg.norm(velocity_vector)

        if v_mag < 1e-6:  # Avoid division by zero
            return np.zeros(3)

        # Adjust drag coefficient for spin effects
        cd_effective = self._calculate_spin_adjusted_drag_coefficient(
            cd, spin_rate_rpm, velocity_vector, spin_axis
        )

        # Drag force magnitude: F_d = 0.5 * C_d * rho * A * v²
        drag_magnitude = (
            0.5 * cd_effective * self.air_density * self.cross_sectional_area * v_mag**2
        )

        # Direction: opposite to velocity (unit vector)
        velocity_unit = velocity_vector / v_mag

        # Drag force vector
        drag_force = -drag_magnitude * velocity_unit

        return drag_force

    def calculate_magnus_force(self, velocity_vector, spin_axis, spin_rate_rpm):
        """
        Calculate Magnus force (spin-induced lift) on the baseball.

        Magnus force: F_m = 0.5 * C_l * rho * A * v²
        Direction: perpendicular to both velocity and spin axis (right-hand rule)

        The lift coefficient C_l depends on spin rate and velocity.

        Parameters
        ----------
        velocity_vector : np.ndarray
            Velocity vector [vx, vy, vz] in m/s
        spin_axis : np.ndarray
            Spin axis unit vector [sx, sy, sz] (direction of angular velocity)
            Using right-hand rule: curl fingers in spin direction, thumb is axis
        spin_rate_rpm : float
            Spin rate in revolutions per minute

        Returns
        -------
        np.ndarray
            Magnus force vector [Fx, Fy, Fz] in Newtons
        """
        v_mag = np.linalg.norm(velocity_vector)

        if v_mag < 1e-6 or spin_rate_rpm < 1.0:
            return np.zeros(3)

        # Normalize spin axis
        spin_axis_mag = np.linalg.norm(spin_axis)
        if spin_axis_mag < 1e-6:
            return np.zeros(3)
        spin_axis_unit = spin_axis / spin_axis_mag

        # Calculate lift coefficient based on spin rate
        # C_l increases with spin but saturates at high spin rates
        cl = self._calculate_lift_coefficient(spin_rate_rpm, v_mag)

        # Magnus force magnitude: F_m = 0.5 * C_l * rho * A * v²
        magnus_magnitude = (
            0.5 * cl * self.air_density * self.cross_sectional_area * v_mag**2
        )

        # Direction: perpendicular to velocity and spin axis
        # Using right-hand rule: velocity × spin_axis (for Magnus force)
        velocity_unit = velocity_vector / v_mag
        force_direction = np.cross(velocity_unit, spin_axis_unit)

        # Normalize (should already be unit length, but ensure it)
        force_direction_mag = np.linalg.norm(force_direction)
        if force_direction_mag < 1e-6:
            return np.zeros(3)
        force_direction_unit = force_direction / force_direction_mag

        # Magnus force vector
        magnus_force = magnus_magnitude * force_direction_unit

        return magnus_force

    def _calculate_spin_adjusted_drag_coefficient(
        self, base_cd, spin_rate_rpm, velocity_vector, spin_axis
    ):
        """
        Calculate drag coefficient adjusted for spin effects.

        Spinning baseballs experience increased drag due to:
        1. Turbulent boundary layer from rotation
        2. Asymmetric flow when spin axis is tilted (sidespin + backspin)

        This models the empirical observation that high spin rates and
        especially sidespin reduce carry distance.

        Parameters
        ----------
        base_cd : float
            Base drag coefficient
        spin_rate_rpm : float
            Total spin rate in rpm
        velocity_vector : np.ndarray
            Velocity vector (for detecting spin axis alignment)
        spin_axis : np.ndarray, optional
            Spin axis unit vector

        Returns
        -------
        float
            Adjusted drag coefficient
        """
        cd_adjusted = base_cd

        # Add drag increase from total spin rate
        # Higher spin = more turbulent boundary layer = more drag
        if spin_rate_rpm > 0:
            spin_drag_increase = SPIN_DRAG_FACTOR * spin_rate_rpm
            # Cap the increase to avoid unrealistic values
            spin_drag_increase = min(spin_drag_increase, SPIN_DRAG_MAX_INCREASE)
            cd_adjusted += spin_drag_increase

        # Add asymmetric drag for tilted spin axis (sidespin effect)
        # When spin axis is not aligned with velocity, flow becomes asymmetric
        if spin_axis is not None and spin_rate_rpm > 100:
            v_mag = np.linalg.norm(velocity_vector)
            if v_mag > 1e-6:
                velocity_unit = velocity_vector / v_mag
                spin_axis_mag = np.linalg.norm(spin_axis)

                if spin_axis_mag > 1e-6:
                    spin_axis_unit = spin_axis / spin_axis_mag

                    # Calculate how much spin axis is tilted from velocity direction
                    # Pure backspin: spin axis perpendicular to velocity (dot product ≈ 0)
                    # Tilted spin: spin axis has component along velocity (dot product ≠ 0)
                    # We want to detect when spin axis is NOT purely perpendicular

                    # For a ball with both backspin and sidespin, the spin axis tilts
                    # This creates asymmetric drag. We can estimate this from the
                    # magnitude of spin components that aren't aligned with pure backspin

                    # The cross product of velocity and spin axis gives Magnus direction
                    # If this is purely vertical (pure backspin), no extra drag
                    # If it has horizontal component (sidespin), add extra drag
                    cross_prod = np.cross(velocity_unit, spin_axis_unit)
                    cross_mag = np.linalg.norm(cross_prod)

                    if cross_mag > 1e-6:
                        cross_unit = cross_prod / cross_mag
                        # Check how much the Magnus force direction deviates from vertical
                        vertical_component = abs(cross_unit[2])  # z-component
                        horizontal_component = np.sqrt(cross_unit[0]**2 + cross_unit[1]**2)

                        # More horizontal component = more sidespin = more asymmetric drag
                        if horizontal_component > 0.1:
                            tilted_drag = TILTED_SPIN_DRAG_FACTOR * spin_rate_rpm * horizontal_component
                            cd_adjusted += tilted_drag

        return cd_adjusted

    def _calculate_lift_coefficient(self, spin_rate_rpm, velocity_ms):
        """
        Calculate lift coefficient based on spin rate and velocity.

        The lift coefficient increases with spin rate but saturates
        beyond approximately 2500 rpm.

        Parameters
        ----------
        spin_rate_rpm : float
            Spin rate in rpm
        velocity_ms : float
            Velocity magnitude in m/s

        Returns
        -------
        float
            Lift coefficient (dimensionless)
        """
        # Simple model: C_l is proportional to spin rate with saturation
        # C_l = SPIN_FACTOR * spin_rate_rpm
        # But with saturation to account for diminishing returns

        # Linear relationship with saturation
        if spin_rate_rpm <= SPIN_SATURATION:
            cl = SPIN_FACTOR * spin_rate_rpm
        else:
            # Beyond saturation, increase more slowly
            cl_at_saturation = SPIN_FACTOR * SPIN_SATURATION
            excess_spin = spin_rate_rpm - SPIN_SATURATION
            cl = cl_at_saturation + SPIN_FACTOR * excess_spin * 0.2

        return cl

    def calculate_total_aerodynamic_force(
        self, velocity_vector, spin_axis, spin_rate_rpm, cd=None
    ):
        """
        Calculate total aerodynamic force (drag + Magnus).

        Parameters
        ----------
        velocity_vector : np.ndarray
            Velocity vector [vx, vy, vz] in m/s
        spin_axis : np.ndarray
            Spin axis unit vector
        spin_rate_rpm : float
            Spin rate in rpm
        cd : float, optional
            Drag coefficient

        Returns
        -------
        tuple of np.ndarray
            (total_force, drag_force, magnus_force) in Newtons
        """
        # Use fast JIT-compiled version for better performance
        cd_base = CD_BASE if cd is None else cd
        return calculate_aerodynamic_forces_fast(
            velocity_vector,
            spin_axis,
            spin_rate_rpm,
            cd_base,
            self.air_density,
            self.cross_sectional_area
        )

    def calculate_total_aerodynamic_force_legacy(
        self, velocity_vector, spin_axis, spin_rate_rpm, cd=None
    ):
        """
        Legacy method for calculating total aerodynamic force.
        Kept for reference and testing.
        """
        # Calculate drag force with spin-dependent adjustments
        drag_force = self.calculate_drag_force(
            velocity_vector, cd, spin_rate_rpm, spin_axis
        )
        magnus_force = self.calculate_magnus_force(
            velocity_vector, spin_axis, spin_rate_rpm
        )

        total_force = drag_force + magnus_force

        return total_force, drag_force, magnus_force


def create_spin_axis(backspin_rpm, sidespin_rpm):
    """
    Create spin axis vector from backspin and sidespin components.

    Uses right-hand rule convention:
    - Backspin: spin axis points in +x direction (toward pitcher)
    - Sidespin: spin axis points in +z direction (upward for right-hand batter pull)

    Parameters
    ----------
    backspin_rpm : float
        Backspin rate in rpm (positive = ball rotating backward)
    sidespin_rpm : float
        Sidespin rate in rpm (positive = hook to left for RH batter)

    Returns
    -------
    tuple
        (spin_axis_vector, total_spin_rpm)
        spin_axis_vector: np.ndarray unit vector
        total_spin_rpm: float total spin magnitude
    """
    # Convert spin components to spin axis
    # Backspin creates spin axis in horizontal plane perpendicular to flight
    # For simplicity, we'll use a coordinate system where:
    # +x: direction of travel (toward outfield)
    # +y: lateral (left field is positive)
    # +z: vertical (up is positive)

    # Backspin axis (perpendicular to flight direction, in horizontal plane)
    # Points to the right (from batter's perspective looking out)
    backspin_axis = np.array([0.0, 1.0, 0.0])  # y-axis

    # Sidespin axis (vertical)
    sidespin_axis = np.array([0.0, 0.0, 1.0])  # z-axis

    # Total spin vector (vector sum)
    spin_vector = backspin_rpm * backspin_axis + sidespin_rpm * sidespin_axis

    # Total spin magnitude
    total_spin_rpm = np.linalg.norm(spin_vector)

    # Spin axis unit vector
    if total_spin_rpm > 0.1:
        spin_axis = spin_vector / total_spin_rpm
    else:
        spin_axis = np.array([0.0, 0.0, 1.0])  # Default to vertical

    return spin_axis, total_spin_rpm


def calculate_reynolds_number(velocity_ms, diameter=0.074, air_density=1.225):
    """
    Calculate Reynolds number for the baseball.

    Re = (rho * v * D) / mu

    where mu is dynamic viscosity of air (~1.8e-5 Pa·s)

    Parameters
    ----------
    velocity_ms : float
        Velocity in m/s
    diameter : float
        Ball diameter in meters (default: 0.074 m)
    air_density : float
        Air density in kg/m³ (default: 1.225)

    Returns
    -------
    float
        Reynolds number (dimensionless)
    """
    mu = 1.8e-5  # Dynamic viscosity of air (Pa·s)
    Re = (air_density * velocity_ms * diameter) / mu
    return Re


def adjust_drag_coefficient(velocity_ms, base_cd=CD_BASE):
    """
    Adjust drag coefficient based on speed-dependent research findings.
    
    Research shows dramatic drag reduction at high speeds due to 
    boundary layer transition from laminar to turbulent flow.
    This creates a critical Reynolds number transition zone.

    Parameters
    ----------
    velocity_ms : float
        Velocity in m/s
    base_cd : float
        Base drag coefficient (used for reference, overridden by research data)

    Returns
    -------
    float
        Speed-dependent drag coefficient
    """
    from .constants import (
        DRAG_COEFFICIENT_LOW_SPEED,
        DRAG_COEFFICIENT_HIGH_SPEED, 
        DRAG_TRANSITION_SPEED_LOW,
        DRAG_TRANSITION_SPEED_HIGH
    )
    
    # Speed-dependent drag coefficient based on research
    if velocity_ms <= DRAG_TRANSITION_SPEED_LOW:
        # Low speed: laminar boundary layer, higher drag
        return DRAG_COEFFICIENT_LOW_SPEED
    elif velocity_ms >= DRAG_TRANSITION_SPEED_HIGH:
        # High speed: turbulent boundary layer, much lower drag
        return DRAG_COEFFICIENT_HIGH_SPEED
    else:
        # Transition zone: smooth interpolation between regimes
        # Linear interpolation for simplicity
        t = (velocity_ms - DRAG_TRANSITION_SPEED_LOW) / (DRAG_TRANSITION_SPEED_HIGH - DRAG_TRANSITION_SPEED_LOW)
        return DRAG_COEFFICIENT_LOW_SPEED + t * (DRAG_COEFFICIENT_HIGH_SPEED - DRAG_COEFFICIENT_LOW_SPEED)
