"""
Aerodynamic forces on a baseball.

This module calculates:
- Drag force (opposes velocity)
- Magnus force (spin-induced lift, perpendicular to velocity)
"""

import numpy as np
from .constants import (
    BALL_CROSS_SECTIONAL_AREA,
    BALL_MASS,
    CD_BASE,
    CL_BASE,
    SPIN_FACTOR,
    SPIN_SATURATION,
)


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

    def calculate_drag_force(self, velocity_vector, cd=None):
        """
        Calculate drag force opposing the baseball's motion.

        Drag force: F_d = 0.5 * C_d * rho * A * v²
        Direction: Opposite to velocity vector

        Parameters
        ----------
        velocity_vector : np.ndarray
            Velocity vector [vx, vy, vz] in m/s
        cd : float, optional
            Drag coefficient. If None, uses default CD_BASE.

        Returns
        -------
        np.ndarray
            Drag force vector [Fx, Fy, Fz] in Newtons
        """
        if cd is None:
            cd = CD_BASE

        # Velocity magnitude
        v_mag = np.linalg.norm(velocity_vector)

        if v_mag < 1e-6:  # Avoid division by zero
            return np.zeros(3)

        # Drag force magnitude: F_d = 0.5 * C_d * rho * A * v²
        drag_magnitude = (
            0.5 * cd * self.air_density * self.cross_sectional_area * v_mag**2
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
        drag_force = self.calculate_drag_force(velocity_vector, cd)
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
    Adjust drag coefficient based on Reynolds number.

    At very high or low Reynolds numbers, C_d may vary.
    For typical baseball velocities (20-50 m/s), C_d is relatively constant.

    Parameters
    ----------
    velocity_ms : float
        Velocity in m/s
    base_cd : float
        Base drag coefficient

    Returns
    -------
    float
        Adjusted drag coefficient
    """
    # For baseball velocities, C_d is fairly constant around 0.35
    # This function can be enhanced if more detailed Reynolds number
    # dependence is needed
    return base_cd
