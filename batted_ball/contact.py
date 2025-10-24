"""
Contact point modeling for batted balls.

Models how the point of contact on the bat affects exit velocity,
launch angle, and spin rate.
"""

from .constants import (
    SWEET_SPOT_EFFICIENCY,
    OFF_CENTER_EFFICIENCY_REDUCTION,
    BELOW_CENTER_BACKSPIN_INCREASE,
    BELOW_CENTER_ANGLE_INCREASE,
    ABOVE_CENTER_TOPSPIN_INCREASE,
    ABOVE_CENTER_ANGLE_DECREASE,
)


def adjust_for_contact_point(
    ideal_exit_velocity,
    ideal_launch_angle,
    ideal_backspin_rpm,
    ideal_sidespin_rpm,
    contact_quality='sweet_spot',
    vertical_offset_inches=0.0,
    horizontal_offset_inches=0.0
):
    """
    Adjust batted ball parameters based on contact point.

    Contact below center: increases launch angle and backspin
    Contact above center: decreases launch angle, adds topspin
    Contact off-center horizontally: adds sidespin, reduces exit velocity

    Parameters
    ----------
    ideal_exit_velocity : float
        Exit velocity for perfect sweet spot contact (mph)
    ideal_launch_angle : float
        Launch angle for perfect contact (degrees)
    ideal_backspin_rpm : float
        Backspin for perfect contact (rpm)
    ideal_sidespin_rpm : float
        Sidespin for perfect contact (rpm)
    contact_quality : str
        Preset: 'sweet_spot', 'below_center', 'above_center', 'off_center'
    vertical_offset_inches : float
        Vertical offset in inches (+ = above center, - = below center)
    horizontal_offset_inches : float
        Horizontal offset in inches (+ = toward pull side)

    Returns
    -------
    dict
        Adjusted parameters: exit_velocity, launch_angle, backspin_rpm, sidespin_rpm
    """
    # Start with ideal values
    exit_velocity = ideal_exit_velocity
    launch_angle = ideal_launch_angle
    backspin_rpm = ideal_backspin_rpm
    sidespin_rpm = ideal_sidespin_rpm

    # Apply preset contact qualities
    if contact_quality == 'sweet_spot':
        # Perfect contact - no adjustments
        pass

    elif contact_quality == 'below_center':
        # Contact below center: higher launch angle, more backspin
        vertical_offset_inches = -1.0  # 1 inch below center

    elif contact_quality == 'above_center':
        # Contact above center: lower angle, topspin
        vertical_offset_inches = 1.0  # 1 inch above center

    elif contact_quality == 'off_center':
        # Off-center horizontally: reduced exit velocity, sidespin
        horizontal_offset_inches = 1.0  # 1 inch off center

    # Apply vertical offset effects
    if vertical_offset_inches < 0:
        # Below center
        inches_below = abs(vertical_offset_inches)

        # Increase launch angle
        launch_angle += inches_below * BELOW_CENTER_ANGLE_INCREASE

        # Increase backspin
        backspin_rpm += inches_below * BELOW_CENTER_BACKSPIN_INCREASE

        # Slight reduction in exit velocity (less efficient contact)
        exit_velocity *= (1.0 - inches_below * 0.02)  # 2% per inch

    elif vertical_offset_inches > 0:
        # Above center
        inches_above = vertical_offset_inches

        # Decrease launch angle
        launch_angle -= inches_above * ABOVE_CENTER_ANGLE_DECREASE

        # Reduce backspin, add topspin (negative backspin)
        backspin_rpm -= inches_above * ABOVE_CENTER_TOPSPIN_INCREASE

        # Reduction in exit velocity
        exit_velocity *= (1.0 - inches_above * 0.03)  # 3% per inch

    # Apply horizontal offset effects
    if abs(horizontal_offset_inches) > 0.1:
        # Off-center contact reduces efficiency
        inches_off = abs(horizontal_offset_inches)

        # Reduce exit velocity
        velocity_reduction = min(inches_off * OFF_CENTER_EFFICIENCY_REDUCTION, 0.4)
        exit_velocity *= (1.0 - velocity_reduction)

        # Add sidespin
        # Positive horizontal offset adds sidespin in that direction
        added_sidespin = horizontal_offset_inches * 300.0  # rpm per inch
        sidespin_rpm += added_sidespin

        # Off-center contact also reduces backspin slightly
        backspin_rpm *= 0.9

    # Ensure physically reasonable values
    exit_velocity = max(exit_velocity, 10.0)  # Minimum 10 mph
    launch_angle = max(min(launch_angle, 85.0), -20.0)  # -20° to 85°
    # Backspin can be negative (topspin)
    # Sidespin can be positive or negative

    return {
        'exit_velocity': exit_velocity,
        'launch_angle': launch_angle,
        'backspin_rpm': backspin_rpm,
        'sidespin_rpm': sidespin_rpm,
    }


def contact_point_from_swing(
    bat_speed_mph,
    pitch_speed_mph,
    bat_angle_deg,
    contact_height_inches,
    sweet_spot_height_inches=36.0
):
    """
    Calculate contact point from swing parameters.

    This is a simplified model. In reality, contact point depends on
    many factors including bat trajectory, pitch location, timing, etc.

    Parameters
    ----------
    bat_speed_mph : float
        Bat speed at contact (mph)
    pitch_speed_mph : float
        Incoming pitch speed (mph)
    bat_angle_deg : float
        Bat angle at contact (degrees from horizontal)
    contact_height_inches : float
        Height of contact point above ground (inches)
    sweet_spot_height_inches : float
        Height of optimal sweet spot contact (inches)

    Returns
    -------
    dict
        Contact parameters: vertical_offset, horizontal_offset, exit_velocity
    """
    # Vertical offset from sweet spot
    vertical_offset = contact_height_inches - sweet_spot_height_inches

    # Exit velocity (simplified collision model)
    # EV ≈ 0.2 * pitch_speed + 1.2 * bat_speed (typical rule of thumb)
    exit_velocity = 0.2 * pitch_speed_mph + 1.2 * bat_speed_mph

    # Bat angle affects launch angle
    # This is a simplification
    launch_angle = bat_angle_deg * 0.8  # Approximate relationship

    # Horizontal offset (would need more info to determine)
    # For now, assume centered contact
    horizontal_offset = 0.0

    return {
        'vertical_offset': vertical_offset,
        'horizontal_offset': horizontal_offset,
        'exit_velocity': exit_velocity,
        'launch_angle': launch_angle,
    }


class ContactModel:
    """
    Model for bat-ball contact physics.

    Provides methods to calculate exit velocity, launch angle, and spin
    from bat and pitch parameters.
    """

    def __init__(self):
        """Initialize contact model."""
        pass

    def calculate_exit_velocity(
        self,
        bat_speed_mph,
        pitch_speed_mph,
        collision_efficiency=0.2
    ):
        """
        Calculate exit velocity from bat and pitch speed.

        Uses simplified collision model:
        EV = collision_efficiency * pitch_speed + (1 + collision_efficiency) * bat_speed

        For baseball, typical collision_efficiency ≈ 0.2

        Parameters
        ----------
        bat_speed_mph : float
            Bat speed at contact (mph)
        pitch_speed_mph : float
            Pitch speed (mph)
        collision_efficiency : float
            Coefficient of restitution-like parameter (default: 0.2)

        Returns
        -------
        float
            Exit velocity in mph
        """
        ev = collision_efficiency * pitch_speed_mph + \
             (1 + collision_efficiency) * bat_speed_mph
        return ev

    def calculate_launch_angle(
        self,
        bat_path_angle_deg,
        pitch_trajectory_angle_deg
    ):
        """
        Calculate launch angle from bat path and pitch trajectory.

        Simplified model: launch angle is weighted average of bat and pitch angles

        Parameters
        ----------
        bat_path_angle_deg : float
            Bat path angle at contact (degrees)
        pitch_trajectory_angle_deg : float
            Pitch trajectory angle at contact (degrees, typically negative)

        Returns
        -------
        float
            Launch angle in degrees
        """
        # Weighted average (bat has more influence)
        launch_angle = 0.7 * bat_path_angle_deg + 0.3 * pitch_trajectory_angle_deg
        return launch_angle

    def calculate_backspin(
        self,
        exit_velocity_mph,
        launch_angle_deg,
        bat_speed_mph
    ):
        """
        Estimate backspin from exit velocity and launch angle.

        Empirical relationship: higher launch angles typically produce more backspin

        Parameters
        ----------
        exit_velocity_mph : float
            Exit velocity (mph)
        launch_angle_deg : float
            Launch angle (degrees)
        bat_speed_mph : float
            Bat speed (mph)

        Returns
        -------
        float
            Backspin in rpm
        """
        # Simplified model: backspin increases with launch angle
        # Typical range: 1000-2500 rpm
        base_spin = 1000.0
        angle_contribution = launch_angle_deg * 50.0  # rpm per degree
        speed_contribution = bat_speed_mph * 5.0  # rpm per mph

        backspin = base_spin + angle_contribution + speed_contribution

        # Clamp to reasonable range
        backspin = max(500.0, min(backspin, 3000.0))

        return backspin
