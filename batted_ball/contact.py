"""
Contact point modeling for batted balls.

Models how the point of contact on the bat affects exit velocity,
launch angle, and spin rate.

Phase 2 Enhancement: Implements physics-based bat-ball collision model
with variable coefficient of restitution and sweet spot physics.
"""

import numpy as np
from .constants import (
    SWEET_SPOT_EFFICIENCY,
    OFF_CENTER_EFFICIENCY_REDUCTION,
    BELOW_CENTER_BACKSPIN_INCREASE,
    BELOW_CENTER_ANGLE_INCREASE,
    ABOVE_CENTER_TOPSPIN_INCREASE,
    ABOVE_CENTER_ANGLE_DECREASE,
    # Phase 2: Collision physics constants
    BAT_MASS,
    BALL_MASS,
    COR_SWEET_SPOT,
    COR_MINIMUM,
    COR_ALUMINUM_BONUS,
    COR_DEGRADATION_PER_INCH,
    BAT_EFFECTIVE_MASS_RATIO,
    VIBRATION_LOSS_FACTOR,
    MAX_VIBRATION_LOSS,
    SPIN_FROM_FRICTION_FACTOR,
    BASE_BACKSPIN_FROM_COMPRESSION,
    # Advanced research-based constants
    COLLISION_EFFICIENCY_WOOD,
    COLLISION_EFFICIENCY_ALUMINUM,
    COLLISION_EFFICIENCY_COMPOSITE,
    WOOD_ENERGY_STORAGE_RATIO,
    METAL_ENERGY_STORAGE_RATIO,
    COMPOSITE_ENERGY_STORAGE_RATIO,
    OFFSET_EFFICIENCY_DEGRADATION,
    HORIZONTAL_OFFSET_SPIN_FACTOR,
    VERTICAL_OFFSET_SPIN_FACTOR,
    VIBRATION_ENERGY_LOSS_MAX,
    VIBRATION_ENERGY_LOSS_RATE,
    TRAMPOLINE_ENERGY_RECOVERY,
    BAT_EFFECTIVE_MASS_RATIO,
    COR_SWEET_SPOT,
    COR_MINIMUM,
    COR_DEGRADATION_PER_INCH,
    COR_ALUMINUM_BONUS,
    SWEET_SPOT_DISTANCE_FROM_BARREL,
    SWEET_SPOT_WIDTH,
    VIBRATION_LOSS_FACTOR,
    MAX_VIBRATION_LOSS,
    COLLISION_ANGLE_TO_LAUNCH_ANGLE_RATIO,
    FRICTION_COEFFICIENT,
    SPIN_FROM_FRICTION_FACTOR,
    BASE_BACKSPIN_FROM_COMPRESSION,
    MPH_TO_MS,
    MS_TO_MPH,
    METERS_TO_FEET,
    FEET_TO_METERS,
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
    Enhanced physics-based model for bat-ball contact.

    Phase 2 Implementation: Implements realistic collision physics with:
    - Variable coefficient of restitution (COR) based on contact location
    - Sweet spot physics with vibration energy loss
    - Physics-based exit velocity calculation from bat/pitch speeds
    - Collision angle effects on launch angle and spin generation

    Provides methods to calculate exit velocity, launch angle, and spin
    from bat and pitch parameters using validated collision mechanics.
    """

    def __init__(self, bat_type='wood'):
        """
        Initialize contact model with research-based collision physics.

        Parameters
        ----------
        bat_type : str
            Type of bat: 'wood', 'aluminum', or 'composite'
        """
        self.bat_type = bat_type
        
        # Set collision efficiency based on bat material (research-based)
        if bat_type == 'wood':
            self.base_collision_efficiency = COLLISION_EFFICIENCY_WOOD  # 0.20
            self.energy_storage_ratio = WOOD_ENERGY_STORAGE_RATIO      # 0.02
        elif bat_type == 'aluminum':
            self.base_collision_efficiency = COLLISION_EFFICIENCY_ALUMINUM  # 0.24 (BBCOR regulated)
            self.energy_storage_ratio = METAL_ENERGY_STORAGE_RATIO         # 0.12
        elif bat_type == 'composite':
            self.base_collision_efficiency = COLLISION_EFFICIENCY_COMPOSITE  # 0.25 (BBCOR regulated)
            self.energy_storage_ratio = COMPOSITE_ENERGY_STORAGE_RATIO      # 0.15
        else:
            self.base_collision_efficiency = COLLISION_EFFICIENCY_WOOD
            self.energy_storage_ratio = WOOD_ENERGY_STORAGE_RATIO

    def calculate_collision_efficiency(self, distance_from_sweet_spot_inches, contact_offset_total):
        """
        Calculate collision efficiency (q) based on research.
        
        The master formula: BBS = q * v_pitch + (1 + q) * v_bat
        where q represents all collision physics complexity.
        
        Parameters
        ----------
        distance_from_sweet_spot_inches : float
            Distance from optimal sweet spot location
        contact_offset_total : float
            Total contact offset from bat center
            
        Returns
        -------
        float
            Collision efficiency (q)
        """
        # Start with base efficiency for bat material
        q = self.base_collision_efficiency
        
        # Reduce efficiency based on distance from sweet spot
        # Sweet spot is zone of maximum performance
        sweet_spot_penalty = min(distance_from_sweet_spot_inches * 0.01, 0.08)  # Max 8% penalty
        q -= sweet_spot_penalty
        
        # Reduce efficiency based on contact offset (mis-hit)
        offset_penalty = contact_offset_total * OFFSET_EFFICIENCY_DEGRADATION
        q -= offset_penalty
        
        # Account for vibrational energy loss
        # Energy lost to bat vibrations reduces collision efficiency
        vibration_loss = min(distance_from_sweet_spot_inches * VIBRATION_ENERGY_LOSS_RATE, 
                             VIBRATION_ENERGY_LOSS_MAX)
        q -= vibration_loss
        
        # Trampoline effect for non-wood bats
        if self.bat_type != 'wood':
            # Barrel deformation stores and returns energy more efficiently than ball deformation
            trampoline_benefit = self.energy_storage_ratio * TRAMPOLINE_ENERGY_RECOVERY * 0.1
            q += trampoline_benefit
        
        # Ensure reasonable bounds
        return max(q, 0.05)  # Minimum efficiency for any contact

    def calculate_vibration_energy_loss(self, distance_from_sweet_spot_inches):
        """
        Calculate energy loss from bat vibrations.

        Contact away from sweet spot causes bat vibrations that absorb
        kinetic energy, reducing exit velocity. Sweet spot is at a node
        where vibrations are minimized.

        Parameters
        ----------
        distance_from_sweet_spot_inches : float
            Distance from sweet spot (inches)

        Returns
        -------
        float
            Fraction of energy lost to vibrations (0.0 to MAX_VIBRATION_LOSS)
        """
        distance_abs = abs(distance_from_sweet_spot_inches)

        # Energy loss increases with distance from sweet spot
        energy_loss = VIBRATION_LOSS_FACTOR * distance_abs

        # Cap at maximum loss
        energy_loss = min(energy_loss, MAX_VIBRATION_LOSS)

        return energy_loss

    def calculate_exit_velocity_master_formula(
        self,
        bat_speed_mph,
        pitch_speed_mph,
        collision_efficiency_q
    ):
        """
        Calculate exit velocity using the research-based master formula.
        
        BBS = q * v_pitch + (1 + q) * v_bat
        
        This is the fundamental equation from collision physics research.
        The collision efficiency q encapsulates all the complex physics:
        - Ball's coefficient of restitution
        - Bat's material properties  
        - Energy lost to bat vibrations
        - Trampoline effect (for non-wood bats)
        
        Parameters
        ----------
        bat_speed_mph : float
            Bat speed at contact (mph)
        pitch_speed_mph : float
            Incoming pitch speed (mph)
        collision_efficiency_q : float
            Collision efficiency parameter
            
        Returns
        -------
        float
            Exit velocity in mph
        """
        # The master formula from collision physics research
        exit_velocity = (collision_efficiency_q * pitch_speed_mph + 
                        (1.0 + collision_efficiency_q) * bat_speed_mph)
        
        return max(exit_velocity, 10.0)  # Minimum exit velocity

    def calculate_launch_angle(
        self,
        bat_path_angle_deg,
        pitch_trajectory_angle_deg=0.0,
        vertical_contact_offset_inches=0.0
    ):
        """
        Calculate launch angle from bat path and pitch trajectory.

        Launch angle is primarily determined by bat path angle, with
        contributions from pitch angle and contact point offset.

        Parameters
        ----------
        bat_path_angle_deg : float
            Bat path angle at contact (degrees from horizontal)
            Positive = upward swing
        pitch_trajectory_angle_deg : float
            Pitch trajectory angle at contact (degrees, typically negative)
            Default 0 = horizontal pitch
        vertical_contact_offset_inches : float
            Vertical offset from bat center (inches)
            Positive = above center, Negative = below center

        Returns
        -------
        float
            Launch angle in degrees
        """
        # Bat path dominates launch angle
        launch_angle = bat_path_angle_deg * COLLISION_ANGLE_TO_LAUNCH_ANGLE_RATIO

        # Small contribution from pitch angle (ball "bounces" off bat)
        launch_angle += pitch_trajectory_angle_deg * 0.15

        # Contact offset affects angle
        # Below center: higher launch angle (undercut)
        # Above center: lower launch angle (topped)
        if vertical_contact_offset_inches < 0:
            # Below center
            launch_angle += abs(vertical_contact_offset_inches) * BELOW_CENTER_ANGLE_INCREASE
        elif vertical_contact_offset_inches > 0:
            # Above center
            launch_angle -= vertical_contact_offset_inches * ABOVE_CENTER_ANGLE_DECREASE

        # Clamp to physically reasonable range
        launch_angle = max(-20.0, min(launch_angle, 85.0))

        return launch_angle

    def calculate_backspin(
        self,
        exit_velocity_mph,
        launch_angle_deg,
        bat_speed_mph,
        vertical_contact_offset_inches=0.0
    ):
        """
        Calculate backspin from collision physics.

        Spin is generated by:
        1. Ball compression and rebound (always produces some backspin)
        2. Friction between bat and ball during collision (tangential force)
        3. Contact offset creating torque

        Parameters
        ----------
        exit_velocity_mph : float
            Exit velocity (mph)
        launch_angle_deg : float
            Launch angle (degrees)
        bat_speed_mph : float
            Bat speed (mph)
        vertical_contact_offset_inches : float
            Vertical offset from bat center (inches)
            Below center = more backspin

        Returns
        -------
        float
            Backspin in rpm (negative = topspin)
        """
        # Base backspin from ball compression during collision
        backspin = BASE_BACKSPIN_FROM_COMPRESSION

        # Spin from friction (proportional to launch angle and bat speed)
        # Higher launch angle = more tangential friction = more spin
        friction_spin = SPIN_FROM_FRICTION_FACTOR * launch_angle_deg
        friction_spin *= (bat_speed_mph / 70.0)  # Scale with bat speed (70 mph = typical)
        backspin += friction_spin

        # Additional spin from contact offset
        if vertical_contact_offset_inches < 0:
            # Below center: adds backspin
            backspin += abs(vertical_contact_offset_inches) * BELOW_CENTER_BACKSPIN_INCREASE
        elif vertical_contact_offset_inches > 0:
            # Above center: reduces backspin (adds topspin)
            backspin -= vertical_contact_offset_inches * ABOVE_CENTER_TOPSPIN_INCREASE

        # Moderate scaling with exit velocity (faster ball = more friction effect)
        # Use sqrt scaling to avoid excessive values
        velocity_scaling = np.sqrt(exit_velocity_mph / 100.0)  # 100 mph = typical
        backspin *= velocity_scaling

        # Clamp to reasonable range (-3000 to 3000 rpm)
        backspin = max(-3000.0, min(backspin, 3000.0))

        return backspin

    def full_collision(
        self,
        bat_speed_mph,
        pitch_speed_mph,
        bat_path_angle_deg,
        pitch_trajectory_angle_deg=0.0,
        vertical_contact_offset_inches=0.0,
        horizontal_contact_offset_inches=0.0,
        distance_from_sweet_spot_inches=0.0
    ):
        """
        Perform complete collision calculation.

        Calculates all batted ball parameters from bat and pitch parameters
        using physics-based collision model with sweet spot effects.

        Parameters
        ----------
        bat_speed_mph : float
            Bat speed at contact (mph)
        pitch_speed_mph : float
            Pitch speed (mph)
        bat_path_angle_deg : float
            Bat path angle (degrees from horizontal)
        pitch_trajectory_angle_deg : float
            Pitch angle (degrees). Default 0.
        vertical_contact_offset_inches : float
            Vertical offset from bat center (inches). Default 0.
        horizontal_contact_offset_inches : float
            Horizontal offset (inches). Affects sidespin. Default 0.
        distance_from_sweet_spot_inches : float
            Distance from sweet spot along bat (inches). Default 0.

        Returns
        -------
        dict
            Contains: exit_velocity, launch_angle, backspin_rpm, sidespin_rpm,
            cor (coefficient of restitution used),
            vibration_loss (fraction of energy lost to vibrations)
        """
        # Calculate total contact offset for efficiency calculation
        contact_offset_total = np.sqrt(vertical_contact_offset_inches**2 + horizontal_contact_offset_inches**2)
        
        # Calculate collision efficiency using research-based method
        collision_efficiency_q = self.calculate_collision_efficiency(
            distance_from_sweet_spot_inches, contact_offset_total
        )
        
        # Calculate exit velocity using master formula
        exit_velocity = self.calculate_exit_velocity_master_formula(
            bat_speed_mph=bat_speed_mph,
            pitch_speed_mph=pitch_speed_mph,
            collision_efficiency_q=collision_efficiency_q
        )
        
        # Apply additional exit velocity reduction for off-center contact
        # TUNED: Gentle penalty to reduce extreme HR rate while preserving power hitting
        # 0.7": ~0% penalty, 1.0": ~2% penalty, 1.5": ~8% penalty, 2.0": ~15% penalty
        if contact_offset_total > 0.6:  # Start penalty at 0.6" offset (sweet spot zone)
            offset_beyond_sweet = max(0, contact_offset_total - 0.6)
            # Power-law penalty: scales as offset^1.15 for very gentle scaling
            penalty = offset_beyond_sweet ** 1.15 * 0.08
            penalty = min(penalty, 0.35)  # Cap at 35% penalty
            exit_velocity *= (1.0 - penalty)
            
        # Ensure minimum exit velocity for any contact
        exit_velocity = max(exit_velocity, 15.0)  # Minimum 15 mph for any contact

        # Calculate launch angle
        launch_angle = self.calculate_launch_angle(
            bat_path_angle_deg=bat_path_angle_deg,
            pitch_trajectory_angle_deg=pitch_trajectory_angle_deg,
            vertical_contact_offset_inches=vertical_contact_offset_inches
        )

        # Calculate spin based on research: bat "erases" pitch spin and creates new spin
        # Research shows final spin is nearly independent of initial pitch spin
        
        # Backspin from vertical offset (contact below/above ball center)
        if abs(vertical_contact_offset_inches) > 0.1:
            # Positive offset (below center) = backspin, negative (above) = topspin
            vertical_spin = -vertical_contact_offset_inches * VERTICAL_OFFSET_SPIN_FACTOR
        else:
            # Minimal vertical offset gets base backspin from compression
            vertical_spin = BASE_BACKSPIN_FROM_COMPRESSION
            
        # Sidespin from horizontal offset
        horizontal_spin = horizontal_contact_offset_inches * HORIZONTAL_OFFSET_SPIN_FACTOR
        
        # Total backspin and sidespin
        backspin = vertical_spin
        sidespin = horizontal_spin
        
        # Apply exit velocity factor to spin (higher exit velocity = more spin potential)
        spin_velocity_factor = min(exit_velocity / 100.0, 1.2)  # Cap at 120 mph equivalent
        backspin *= spin_velocity_factor
        sidespin *= spin_velocity_factor

        return {
            'exit_velocity': exit_velocity,
            'launch_angle': launch_angle,
            'backspin_rpm': backspin,
            'sidespin_rpm': sidespin,
            'collision_efficiency_q': collision_efficiency_q,
            'contact_offset_total': contact_offset_total,
            'sweet_spot_distance': distance_from_sweet_spot_inches,
        }
