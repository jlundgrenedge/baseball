"""
Player attribute system for pitchers and hitters.

Integrates attribute ratings with physics-based simulation to create
realistic baseball gameplay with individual player characteristics.
"""

import numpy as np
from typing import Dict, List, Optional, Tuple
from .attributes import HitterAttributes, FielderAttributes, PitcherAttributes
from .constants import (
    # Pitcher attribute scales
    VELOCITY_RATING_MIN,
    VELOCITY_RATING_AVG,
    VELOCITY_RATING_ELITE,
    VELOCITY_RATING_MAX,
    MOVEMENT_RATING_MIN,
    MOVEMENT_RATING_AVG,
    MOVEMENT_RATING_ELITE,
    MOVEMENT_RATING_MAX,
    COMMAND_RATING_MIN,
    COMMAND_RATING_AVG,
    COMMAND_RATING_ELITE,
    COMMAND_RATING_MAX,
    DECEPTION_RATING_MIN,
    DECEPTION_RATING_AVG,
    DECEPTION_RATING_ELITE,
    DECEPTION_RATING_MAX,
    RELEASE_EXTENSION_MIN,
    RELEASE_EXTENSION_AVG,
    RELEASE_EXTENSION_MAX,
    ARM_ANGLE_OVERHAND,
    ARM_ANGLE_3_4,
    ARM_ANGLE_SIDEARM,
    # Pitch characteristics
    FASTBALL_4SEAM_VELOCITY_AVG,
    FASTBALL_4SEAM_SPIN_AVG,
)


class Pitcher:
    """
    Represents a pitcher with physics-first attributes (0-100,000 scale).

    All pitcher capabilities are defined through PitcherAttributes which maps
    ratings to physical units:
    - Velocity (mph)
    - Spin rate (rpm)
    - Stamina (max pitches)
    - Command/control
    """

    def __init__(
        self,
        name: str,
        attributes: PitcherAttributes,
        arm_slot: float = ARM_ANGLE_3_4,
        pitch_arsenal: Optional[Dict[str, Dict]] = None,
    ):
        """
        Initialize pitcher with physics-first attributes.

        Parameters
        ----------
        name : str
            Pitcher's name
        attributes : PitcherAttributes
            Physics-first attribute system (0-100,000 scale)
            Provides velocity, spin, stamina, command mapped to physical units
        arm_slot : float
            Release angle in degrees (0=overhand, 45=3/4, 90=sidearm)
        pitch_arsenal : dict, optional
            Dict of pitch types (keys are pitch names like 'fastball', 'slider')
            Values can be empty dicts or contain modifiers
        """
        self.name = name
        self.attributes = attributes
        self.arm_slot = arm_slot

        # Pitch arsenal (simplified - now just defines available pitches)
        if pitch_arsenal is None:
            # Default: 4-seam fastball
            pitch_arsenal = {'fastball': {}}
        self.pitch_arsenal = pitch_arsenal

        # State variables
        self.pitches_thrown = 0

    def get_pitch_velocity_mph(self, pitch_type: str = 'fastball') -> float:
        """
        Get pitch velocity in MPH with stamina degradation.

        Parameters
        ----------
        pitch_type : str
            Pitch type from arsenal

        Returns
        -------
        float
            Velocity in MPH
        """
        # Get base velocity from physics-first attributes
        velocity_mph = self.attributes.get_raw_velocity_mph()

        # Apply pitch-type modifiers (fastball = 100%, changeup = ~85%, etc.)
        if pitch_type == 'changeup':
            velocity_mph *= 0.85
        elif pitch_type == 'curveball':
            velocity_mph *= 0.88
        elif pitch_type == 'slider':
            velocity_mph *= 0.92

        # Apply stamina degradation based on pitches thrown
        stamina_cap = self.attributes.get_stamina_pitches()
        stamina_factor = max(0.0, 1.0 - (self.pitches_thrown / stamina_cap))
        stamina_loss = (1.0 - stamina_factor) * 4.0  # Up to 4 mph loss when exhausted

        return max(velocity_mph - stamina_loss, 70.0)

    def get_pitch_spin_rpm(self, pitch_type: str = 'fastball', base_spin: float = 2200) -> float:
        """
        Get spin rate in RPM with stamina degradation.

        Parameters
        ----------
        pitch_type : str
            Pitch type from arsenal
        base_spin : float
            Base spin rate (not used, kept for compatibility)

        Returns
        -------
        float
            Spin rate in RPM
        """
        # Get base spin rate from physics-first attributes (for 4-seam fastball)
        base_spin_rpm = self.attributes.get_spin_rate_rpm()

        # Apply pitch-type modifiers
        if pitch_type == 'changeup':
            spin_rpm = base_spin_rpm * 0.70  # Lower spin
        elif pitch_type == 'curveball':
            spin_rpm = base_spin_rpm * 1.10  # Higher spin
        elif pitch_type == 'slider':
            spin_rpm = base_spin_rpm * 0.95  # Slightly lower
        else:  # fastball
            spin_rpm = base_spin_rpm

        # Apply stamina degradation
        stamina_cap = self.attributes.get_stamina_pitches()
        stamina_factor = max(0.0, 1.0 - (self.pitches_thrown / stamina_cap))
        stamina_loss = (1.0 - stamina_factor) * 0.12  # Up to 12% spin loss when exhausted

        return spin_rpm * (1.0 - stamina_loss)

    def get_release_extension_feet(self) -> float:
        """
        Get release extension in feet.

        Returns
        -------
        float
            Extension in feet (typically 5.0-7.5 ft)
        """
        # Use a default value for now since PitcherAttributes doesn't have extension
        # This could be added to attributes later if needed
        return 6.0  # Average MLB extension

    def get_command_error_inches(self, pitch_type: str = 'fastball') -> Tuple[float, float]:
        """
        Calculate location error based on command with stamina effects.

        Parameters
        ----------
        pitch_type : str
            Pitch type from arsenal

        Returns
        -------
        tuple
            (horizontal_error_inches, vertical_error_inches)
        """
        # Get base command error from attributes (in inches)
        # Note: PitcherAttributes doesn't have a command error method yet
        # For now, use a reasonable default that could be added to attributes
        max_error = 3.0  # inches, average MLB command

        # Apply stamina degradation
        stamina_cap = self.attributes.get_stamina_pitches()
        stamina_factor = max(0.0, 1.0 - (self.pitches_thrown / stamina_cap))
        fatigue_multiplier = 1.0 + (1.0 - stamina_factor) * 1.0  # Up to 2x error when exhausted

        # Random error with normal distribution
        horizontal_error = np.random.normal(0, max_error * fatigue_multiplier / 2.0)
        vertical_error = np.random.normal(0, max_error * fatigue_multiplier / 2.0)

        return horizontal_error, vertical_error

    def throw_pitch(self):
        """Update state after throwing a pitch."""
        self.pitches_thrown += 1
        # Stamina degradation is now implicit in get_pitch_velocity_mph() and get_pitch_spin_rpm()
        # based on pitches_thrown relative to stamina_cap

    def __repr__(self):
        velo = self.attributes.get_raw_velocity_mph()
        spin = self.attributes.get_spin_rate_rpm()
        stamina = self.attributes.get_stamina_pitches()
        return (
            f"Pitcher(name='{self.name}', "
            f"velocity={velo:.1f} mph, spin={spin:.0f} rpm, "
            f"stamina={stamina:.0f} pitches, thrown={self.pitches_thrown})"
        )


def generate_pitch_arsenal(
    pitcher_attributes: PitcherAttributes,
    role: str = "starter",
    arsenal_size: Optional[int] = None
) -> Dict[str, Dict]:
    """
    Generate a realistic pitch arsenal for a pitcher based on their attributes and role.

    MLB pitchers typically have:
    - Starters: 4-5 pitches (need variety to face batters multiple times)
    - Relievers: 2-3 pitches (can rely on best stuff for shorter outings)

    Common pitch combinations:
    - Power pitchers: 4-seam fastball + slider + changeup (+ curveball)
    - Finesse pitchers: 2-seam fastball + changeup + curveball + cutter
    - Groundball pitchers: 2-seam fastball + sinker tendencies + slider

    Parameters
    ----------
    pitcher_attributes : PitcherAttributes
        The pitcher's attributes to determine arsenal composition
    role : str
        "starter" or "reliever" - affects number of pitches
    arsenal_size : int, optional
        Override the number of pitches (otherwise determined by role)

    Returns
    -------
    Dict[str, Dict]
        Dictionary of pitch types (keys: pitch names, values: empty dicts for now)
    """
    import random

    # Get pitcher characteristics
    velocity = pitcher_attributes.get_raw_velocity_mph()
    spin_rate = pitcher_attributes.get_spin_rate_rpm()

    # Determine pitcher type based on velocity
    # High velocity (95+ mph) = power pitcher
    # Medium velocity (90-94 mph) = balanced
    # Low velocity (<90 mph) = finesse pitcher
    is_power_pitcher = velocity >= 95.0
    is_finesse_pitcher = velocity < 90.0

    # Determine arsenal size
    if arsenal_size is None:
        if role == "starter":
            # Starters: 4-5 pitches
            arsenal_size = random.choices([4, 5], weights=[0.4, 0.6])[0]
        else:
            # Relievers: 2-3 pitches
            arsenal_size = random.choices([2, 3], weights=[0.3, 0.7])[0]

    arsenal = {}

    # All pitchers have a fastball as their primary pitch
    # Power pitchers favor 4-seam, finesse pitchers can have 2-seam or 4-seam
    if is_power_pitcher or random.random() < 0.7:
        arsenal['fastball'] = {}  # 4-seam fastball
    else:
        arsenal['2-seam'] = {}  # 2-seam fastball

    # Build list of available secondary pitches
    # Pitch selection is influenced by pitcher type
    if is_power_pitcher:
        # Power pitchers: slider, changeup, curveball, cutter
        # Slider is most common for high-velo pitchers
        secondary_pitches = [
            ('slider', 0.90),      # Very common for power arms
            ('changeup', 0.75),    # Common
            ('curveball', 0.50),   # Less common
            ('cutter', 0.40),      # Less common
        ]
    elif is_finesse_pitcher:
        # Finesse pitchers: changeup, curveball, cutter, slider, splitter
        secondary_pitches = [
            ('changeup', 0.85),    # Very common for finesse
            ('curveball', 0.70),   # Common
            ('cutter', 0.60),      # Common
            ('slider', 0.50),      # Less common
            ('splitter', 0.30),    # Uncommon
        ]
    else:
        # Balanced pitchers: mix of everything
        secondary_pitches = [
            ('slider', 0.75),
            ('changeup', 0.75),
            ('curveball', 0.60),
            ('cutter', 0.45),
            ('splitter', 0.25),
        ]

    # Shuffle to randomize selection order
    random.shuffle(secondary_pitches)

    # Select pitches based on arsenal size
    pitches_needed = arsenal_size - 1  # -1 for fastball already added

    for pitch_name, probability in secondary_pitches:
        if pitches_needed <= 0:
            break

        # Add pitch based on probability
        if random.random() < probability:
            arsenal[pitch_name] = {}
            pitches_needed -= 1

    # If we still need more pitches (rare), add from remaining options
    if pitches_needed > 0:
        remaining_pitches = [
            p for p, _ in secondary_pitches
            if p not in arsenal
        ]
        for pitch_name in remaining_pitches[:pitches_needed]:
            arsenal[pitch_name] = {}

    return arsenal


class Hitter:
    """
    Represents a hitter with physics-first attributes (0-100,000 scale).

    All hitting capabilities are defined through HitterAttributes which maps
    ratings to physical units:
    - Bat speed (mph)
    - Attack angle mean/variance (degrees)
    - Barrel accuracy (mm)
    - Timing precision (ms)
    """

    def __init__(
        self,
        name: str,
        attributes: HitterAttributes,
        # Simplified decision-making attributes (not yet in HitterAttributes)
        zone_discipline: int = 50,
        swing_decision_aggressiveness: int = 50,
    ):
        """
        Initialize hitter with physics-first attributes.

        Parameters
        ----------
        name : str
            Hitter's name
        attributes : HitterAttributes
            Physics-first attribute system (0-100,000 scale)
            Provides bat speed, attack angle, barrel accuracy, timing mapped to physical units
        zone_discipline : int (0-100)
            Strike zone judgment (50=avg, 80=excellent patience)
            TODO: Move to HitterAttributes in future
        swing_decision_aggressiveness : int (0-100)
            Swing frequency (50=avg, 80=very aggressive, 20=patient)
            TODO: Move to HitterAttributes in future
        """
        self.name = name
        self.attributes = attributes

        # Decision attributes (kept as 0-100 for now, could move to attributes later)
        self.zone_discipline = np.clip(zone_discipline, 0, 100)
        self.swing_decision_aggressiveness = np.clip(swing_decision_aggressiveness, 0, 100)

    def get_bat_speed_mph(self) -> float:
        """
        Get bat speed in MPH.

        Returns
        -------
        float
            Bat speed in MPH (typically 65-80 mph)
        """
        return self.attributes.get_bat_speed_mph()

    def get_swing_path_angle_deg(self, pitch_location: Optional[Tuple[float, float]] = None,
                                  pitch_type: Optional[str] = None) -> float:
        """
        Get swing path angle (attack angle) in degrees with realistic variance.

        In reality, even "fly ball hitters" hit ground balls 40-45% of the time.
        Launch angle is influenced by:
        - Player tendency (mean)
        - Pitch location (high/low)
        - Pitch type (fastball/breaking ball)
        - Random variation from contact point
        
        MLB Launch Angle Distribution:
        - Ground balls: < 10°
        - Line drives: 10-25°
        - Fly balls: 25-50°
        - Pop-ups: > 50°

        Parameters
        ----------
        pitch_location : tuple, optional
            (horizontal_inches, vertical_inches) at plate
        pitch_type : str, optional
            Type of pitch ('fastball', 'curveball', etc.)

        Returns
        -------
        float
            Swing path angle in degrees with realistic variance
        """
        # Get attack angle parameters from physics-first attributes
        mean_angle = self.attributes.get_attack_angle_mean_deg()
        base_variance = self.attributes.get_attack_angle_variance_deg()
        
        # CRITICAL: Add much larger natural variance to create realistic outcome distribution
        # Even the best hitters have huge variance in launch angle (15-20° std dev)
        # This is what creates the ground ball / line drive / fly ball distribution
        natural_variance = 15.0  # Standard deviation in degrees
        
        # Adjust mean based on pitch location (if provided)
        location_adjustment = 0.0
        if pitch_location is not None:
            vertical_location = pitch_location[1]  # inches from center of zone
            # High pitches (~+12") tend to produce fly balls
            # Low pitches (~-12") tend to produce ground balls
            # REDUCED: Was 0.8 deg/inch, now 0.3 deg/inch for more realistic effect
            # At 0.3: +12" pitch adds ~+3.6° (not +9.6°)
            location_adjustment = vertical_location * 0.3  # ~0.3 deg per inch
        
        # Adjust based on pitch type (if provided)
        pitch_adjustment = 0.0
        if pitch_type is not None:
            # Breaking balls (downward movement) tend to be topped more often
            if pitch_type in ['curveball', 'slider', 'slurve']:
                pitch_adjustment = -2.0  # Slightly more ground balls (was -5.0)
            # Rising fastballs tend to be lifted more
            elif pitch_type in ['four_seam', 'two_seam']:
                pitch_adjustment = 1.0  # Slightly more fly balls (was +2.0)
        
        # Combine all factors
        adjusted_mean = mean_angle + location_adjustment + pitch_adjustment
        
        # Sample from distribution with large natural variance
        # Use player's base_variance to modulate the natural variance slightly
        # (more consistent hitters have slightly less extreme outcomes)
        consistency_factor = np.clip(base_variance / 3.0, 0.7, 1.3)
        total_variance = natural_variance * consistency_factor
        
        # Sample from normal distribution
        launch_angle = np.random.normal(adjusted_mean, total_variance)
        
        # Realistic bounds: -25° (extreme topper) to +70° (extreme pop-up)
        return np.clip(launch_angle, -25.0, 70.0)

    def get_contact_point_offset(self, pitch_location: Tuple[float, float]) -> Tuple[float, float]:
        """
        Calculate contact point offset from sweet spot.

        Parameters
        ----------
        pitch_location : tuple
            (horizontal_inches, vertical_inches) at plate

        Returns
        -------
        tuple
            (horizontal_offset_inches, vertical_offset_inches) from sweet spot
        """
        # Get barrel accuracy in mm, convert to inches
        error_mm = self.attributes.get_barrel_accuracy_mm()
        error_inches = error_mm / 25.4  # mm to inches

        # Sample from normal distribution
        horizontal_offset = np.random.normal(0, error_inches)
        vertical_offset = np.random.normal(0, error_inches)

        return horizontal_offset, vertical_offset

    def decide_to_swing(
        self,
        pitch_location: Tuple[float, float],
        is_strike: bool,
        count: Tuple[int, int],
        pitch_velocity: float = 90.0,
        pitch_type: str = 'fastball',
    ) -> bool:
        """
        Decide whether to swing at a pitch.

        Parameters
        ----------
        pitch_location : tuple
            (horizontal_inches, vertical_inches) at plate
        is_strike : bool
            Whether pitch is in strike zone
        count : tuple
            (balls, strikes)
        pitch_velocity : float
            Pitch speed in mph (affects reaction time)
        pitch_type : str
            Type of pitch (affects chase rate)

        Returns
        -------
        bool
            True if swinging, False if taking
        """
        balls, strikes = count

        # Base swing probability based on strike zone
        if is_strike:
            # MLB average: ~75% swing rate on pitches in zone, varies by location
            # Center of zone: higher swing rate, edges: lower swing rate
            h_distance_from_center = abs(pitch_location[0]) / 8.5  # Normalized
            v_distance_from_center = abs(pitch_location[1] - 30.0) / 12.0  # Normalized
            zone_difficulty = (h_distance_from_center + v_distance_from_center) / 2.0
            
            # Swing rate varies from 85% (center) to 65% (edges)
            base_swing_prob = 0.85 - zone_difficulty * 0.20
        else:
            # Distance from zone affects chase probability
            # Strike zone boundaries: ±8.5" horizontal, 18"-42" vertical
            h_dist = max(0, abs(pitch_location[0]) - 8.5)
            v_dist_top = max(0, pitch_location[1] - 42.0)
            v_dist_bottom = max(0, 18.0 - pitch_location[1])
            distance_from_zone = np.sqrt(h_dist**2 + (v_dist_top + v_dist_bottom)**2)

            # Further from zone = less likely to swing
            # MLB chase rates: ~35% just outside, ~10% way outside
            if distance_from_zone < 3.0:
                base_swing_prob = 0.35 * np.exp(-distance_from_zone / 4.0)
            else:
                base_swing_prob = 0.10 * np.exp(-distance_from_zone / 8.0)

        # Adjust for zone discipline (higher = more selective)
        discipline_factor = self.zone_discipline / 100.0
        if is_strike:
            # Good discipline = slightly lower swing rate in zone (but still high)
            swing_prob = base_swing_prob + (1 - discipline_factor) * 0.15
        else:
            # Good discipline = much lower chase rate
            swing_prob = base_swing_prob * (1 - discipline_factor * 0.6)

        # Adjust for aggressiveness
        aggression_factor = self.swing_decision_aggressiveness / 100.0
        swing_prob = swing_prob * (0.8 + aggression_factor * 0.4)

        # Velocity effect (faster pitches = less time to decide = more takes)
        velocity_difficulty = (pitch_velocity - 85) / 15.0  # Normalized
        if velocity_difficulty > 0:
            swing_prob *= (1.0 - velocity_difficulty * 0.10)  # Up to -10% for 100 mph

        # Pitch type affects chase rate (breaking balls fool hitters)
        pitch_type_lower = pitch_type.lower()
        if not is_strike:  # Only affects out-of-zone pitches
            if 'slider' in pitch_type_lower or 'curve' in pitch_type_lower:
                swing_prob *= 1.25  # +25% chase rate on breaking balls
            elif 'change' in pitch_type_lower or 'splitter' in pitch_type_lower:
                swing_prob *= 1.15  # +15% chase rate on off-speed

        # Count situation adjustments
        if strikes == 2:
            # Protect the plate with 2 strikes
            if is_strike:
                swing_prob = min(swing_prob + 0.15, 0.95)  # +15%, cap at 95%
            else:
                swing_prob = min(swing_prob * 1.4, 0.70)  # +40% chase, cap at 70%

        if balls == 3:
            # More selective on 3-ball counts
            if not is_strike:
                swing_prob *= 0.5  # Much less likely to chase
            else:
                swing_prob = min(swing_prob, 0.85)  # Cap swing rate

        # Clip to reasonable bounds
        swing_prob = np.clip(swing_prob, 0.0, 0.98)

        # Make decision
        return np.random.random() < swing_prob

    def get_swing_timing_error_ms(self, pitch_velocity: float) -> float:
        """
        Calculate timing error based on pitch velocity and precision.

        Parameters
        ----------
        pitch_velocity : float
            Pitch speed in MPH

        Returns
        -------
        float
            Timing error in milliseconds (positive = early, negative = late)
        """
        # Get base timing precision (RMS error in ms)
        error_ms = self.attributes.get_timing_precision_ms()

        # Faster pitches harder to time (velocity difficulty adjustment)
        velocity_difficulty = (pitch_velocity - 80) / 20.0
        adjusted_error = error_ms * (1.0 + velocity_difficulty * 0.3)

        # Sample from normal distribution
        return np.random.normal(0, adjusted_error)

    def calculate_whiff_probability(
        self,
        pitch_velocity: float,
        pitch_type: str,
        pitch_break: Tuple[float, float],
    ) -> float:
        """
        Calculate probability of whiffing (missing) on a swing.

        Based on MLB Statcast data for pitch-type specific whiff rates.

        Parameters
        ----------
        pitch_velocity : float
            Pitch speed in mph
        pitch_type : str
            Type of pitch
        pitch_break : tuple
            (vertical_break_inches, horizontal_break_inches)

        Returns
        -------
        float
            Probability of whiff (0.0 to 1.0)
        """
        # Base whiff rates from MLB Statcast data
        pitch_type_lower = pitch_type.lower()
        if 'fastball' in pitch_type_lower or '4-seam' in pitch_type_lower:
            base_whiff_rate = 0.20  # 20% for fastballs
        elif '2-seam' in pitch_type_lower or 'sinker' in pitch_type_lower:
            base_whiff_rate = 0.18  # 18% for sinkers
        elif 'cutter' in pitch_type_lower:
            base_whiff_rate = 0.25  # 25% for cutters
        elif 'slider' in pitch_type_lower:
            base_whiff_rate = 0.35  # 35% for sliders (highest)
        elif 'curve' in pitch_type_lower:
            base_whiff_rate = 0.30  # 30% for curveballs
        elif 'change' in pitch_type_lower:
            base_whiff_rate = 0.32  # 32% for changeups
        elif 'splitter' in pitch_type_lower:
            base_whiff_rate = 0.38  # 38% for splitters
        elif 'knuckle' in pitch_type_lower:
            base_whiff_rate = 0.40  # 40% for knuckleballs
        else:
            base_whiff_rate = 0.25  # Default

        # Velocity effect (faster = harder to hit)
        velocity_difficulty = (pitch_velocity - 85) / 15.0  # Normalized
        velocity_factor = 1.0 + velocity_difficulty * 0.20  # Up to +20% for 100 mph

        # Break effect (more movement = more whiffs)
        v_break, h_break = pitch_break
        break_magnitude = np.sqrt(v_break**2 + h_break**2)
        break_factor = 1.0 + (break_magnitude / 100.0)  # +1% per inch of break

        # Barrel accuracy affects ability to make contact
        # Derive contact_factor from barrel accuracy in mm
        # Elite: ~5mm error -> 0.6x whiff rate
        # Average: ~15mm error -> 1.0x whiff rate
        # Poor: ~30mm error -> 1.8x whiff rate
        barrel_error_mm = self.attributes.get_barrel_accuracy_mm()
        # Map linearly: 5mm -> 0.6, 15mm -> 1.0, 30mm -> 1.8
        contact_factor = 0.6 + (barrel_error_mm - 5) * 0.048

        # Combine factors
        whiff_prob = base_whiff_rate * velocity_factor * break_factor * contact_factor

        # Clip to reasonable bounds (5% minimum, 70% maximum)
        whiff_prob = np.clip(whiff_prob, 0.05, 0.70)

        return whiff_prob

    def __repr__(self):
        bat_speed = self.attributes.get_bat_speed_mph()
        attack_angle = self.attributes.get_attack_angle_mean_deg()
        barrel_error = self.attributes.get_barrel_accuracy_mm()
        return (
            f"Hitter(name='{self.name}', "
            f"bat_speed={bat_speed:.1f} mph, angle={attack_angle:.1f}°, "
            f"barrel_error={barrel_error:.1f}mm, discipline={self.zone_discipline})"
        )
