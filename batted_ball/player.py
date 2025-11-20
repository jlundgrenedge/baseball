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
        pitch_effectiveness: Optional[Dict[str, Dict[str, int]]] = None,
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
        pitch_effectiveness : dict, optional
            Dict mapping pitch type to Statcast-derived effectiveness metrics:
            {'fastball': {'stuff': 75000, 'whiff_bonus': +5000, ...}, ...}
            If None, uses baseline values for all pitches
        """
        self.name = name
        self.attributes = attributes
        self.arm_slot = arm_slot

        # Pitch arsenal (simplified - now just defines available pitches)
        if pitch_arsenal is None:
            # Default: 4-seam fastball
            pitch_arsenal = {'fastball': {}}
        self.pitch_arsenal = pitch_arsenal

        # Pitch-specific effectiveness from Statcast metrics
        # Maps pitch type to {'stuff': rating, 'velocity': mph, 'usage': %}
        self.pitch_effectiveness = pitch_effectiveness or {}

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

        FIXED 2025-11-19: Now actually uses pitcher's COMMAND attribute!
        Previous bug: Hardcoded 3.0" for all pitchers, ignored COMMAND rating.

        Command error follows normal distribution with sigma from COMMAND attribute:
        - Elite (85k): 9.5" sigma (~13" RMS error)
        - Average (50k): 16.0" sigma (~23" RMS error)
        - Poor (20k): 21.5" sigma (~30" RMS error)

        FIXED 2025-11-20: Reduced fatigue penalty and made it nonlinear
        - Fatigue now increases error by up to 1.4× (was 2.0×)
        - Nonlinear curve: gradual increase until 75% stamina, then accelerates
        - Capped at max 24" (2 ft radius) to prevent wild misses

        Parameters
        ----------
        pitch_type : str
            Pitch type from arsenal

        Returns
        -------
        tuple
            (horizontal_error_inches, vertical_error_inches)
        """
        # Get base command error from attributes (FIXED - now actually uses it!)
        command_sigma = self.attributes.get_command_sigma_inches()

        # Apply stamina degradation with NONLINEAR scaling
        stamina_cap = self.attributes.get_stamina_pitches()
        stamina_remaining = max(0.0, 1.0 - (self.pitches_thrown / stamina_cap))

        # Nonlinear fatigue curve: exponential increase after 75% stamina used
        # At 0% fatigue (fresh): multiplier = 1.0
        # At 50% fatigue: multiplier = 1.1 (gradual increase)
        # At 75% fatigue: multiplier = 1.2 (starting to tire)
        # At 100% fatigue (exhausted): multiplier = 1.4 (significant but not crazy)
        fatigue_factor = 1.0 - stamina_remaining
        if fatigue_factor < 0.75:
            # Gradual linear increase for first 75% of stamina
            fatigue_multiplier = 1.0 + fatigue_factor * 0.27  # 0.0 to 0.2 (1.0 to 1.2)
        else:
            # Exponential increase after 75% stamina used
            excess_fatigue = (fatigue_factor - 0.75) / 0.25  # 0.0 to 1.0
            fatigue_multiplier = 1.2 + (excess_fatigue ** 1.8) * 0.2  # 1.2 to 1.4

        # Apply fatigue to command sigma
        effective_sigma = command_sigma * fatigue_multiplier

        # Cap maximum error at 18" (1.5 ft) to prevent excessive walks
        # Strike zone is ~17" wide × 24" tall, so 18" sigma → ~25" RMS = reasonable max
        # This ensures even exhausted poor-command pitchers can throw ~40-50% strikes
        effective_sigma = min(effective_sigma, 18.0)

        # Random error with normal distribution (NO DIVISION - use sigma directly!)
        # Previous bug: Divided by 2.0, making error 10× too small
        horizontal_error = np.random.normal(0, effective_sigma)
        vertical_error = np.random.normal(0, effective_sigma)

        return horizontal_error, vertical_error

    def get_pitch_whiff_multiplier(self, pitch_type: str = 'fastball') -> float:
        """
        Get pitch-type specific whiff rate multiplier based on Statcast metrics.

        This multiplier adjusts the base whiff probability to reflect the pitcher's
        actual effectiveness with each pitch type.

        Parameters
        ----------
        pitch_type : str
            Pitch type from arsenal

        Returns
        -------
        float
            Multiplier for whiff probability (1.0 = baseline, >1.0 = more whiffs)
        """
        # Check if we have Statcast-derived effectiveness for this pitch
        if pitch_type in self.pitch_effectiveness:
            stuff_rating = self.pitch_effectiveness[pitch_type].get('stuff', 50000)

            # Convert stuff rating (0-100,000) to multiplier
            # 100k = 1.5x (elite stuff - 50% more whiffs)
            # 50k = 1.0x (average stuff - baseline)
            # 0k = 0.5x (poor stuff - 50% fewer whiffs)
            multiplier = 0.5 + (stuff_rating / 100000.0)

            return multiplier
        else:
            # No specific data for this pitch - use baseline
            return 1.0

    def get_pitch_usage_rating(self, pitch_type: str = 'fastball') -> int:
        """
        Get pitch usage rating (0-100) indicating confidence/frequency.

        Parameters
        ----------
        pitch_type : str
            Pitch type from arsenal

        Returns
        -------
        int
            Usage rating (0-100, higher = more frequent)
        """
        if pitch_type in self.pitch_effectiveness:
            return self.pitch_effectiveness[pitch_type].get('usage', 50)
        else:
            # Default usage based on pitch type
            default_usage = {
                'fastball': 60,
                '4-seam': 60,
                '2-seam': 50,
                'cutter': 40,
                'slider': 45,
                'curveball': 35,
                'changeup': 40,
                'splitter': 30,
            }
            return default_usage.get(pitch_type, 50)

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
        speed: int = 50000,
        pitch_recognition: Optional[Dict[str, Dict[str, int]]] = None,
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
            Also includes zone discernment and swing decision latency
        speed : int, optional
            Running speed rating (0-100,000 scale, default: 50000 = average)
            Used for baserunning physics
        pitch_recognition : dict, optional
            Dict mapping pitch type to Statcast-derived recognition metrics:
            {'slider': {'recognition': 65000, 'contact_ability': 70000, ...}, ...}
            If None, uses baseline values for all pitches
        """
        self.name = name
        self.attributes = attributes
        self.speed = np.clip(speed, 0, 100000)

        # Pitch-specific recognition from Statcast metrics
        # Maps pitch type to {'recognition': rating, 'contact_ability': rating, 'whiff_resistance': rating}
        self.pitch_recognition = pitch_recognition or {}

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
        return_diagnostics: bool = False,
        debug_collector=None,
    ):
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
        return_diagnostics : bool
            If True, return (decision, diagnostics_dict) tuple

        Returns
        -------
        bool or tuple
            If return_diagnostics=False: True if swinging, False if taking
            If return_diagnostics=True: (decision, diagnostics) tuple
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
        # Use zone_discernment_factor from attributes (0-1 scale, higher = better recognition)
        discipline_factor = self.attributes.get_zone_discernment_factor()
        swing_prob_after_discipline = base_swing_prob  # Track for logging
        if is_strike:
            # Good discipline = slightly lower swing rate in zone (but still high)
            swing_prob = base_swing_prob + (1 - discipline_factor) * 0.15
            swing_prob_after_discipline = swing_prob
        else:
            # Good discipline = lower chase rate, but not eliminating chases entirely
            # PHASE 2A SPRINT 1 2025-11-20: Reduced from 0.30 to 0.15 to increase chase rate
            # PHASE 2A SPRINT 2 2025-11-20: Reduced from 0.15 to 0.12 to further increase chase
            # Previous iterations: 0.85 → 0.40 → 0.30 (Refinement) → 0.15 (Sprint 1) → 0.12 (Sprint 2)
            # Sprint 1 test showed chase rate 17.6% (MLB: 25-35%) - need +7-17 pp more increase
            # Elite discipline (0.90 factor): 1 - 0.90*0.12 = 0.892 → 10.8% reduction
            #   → Base chase 35% * 0.892 = 31.2% actual ✓ (MLB elite: 20-25%)
            # Poor discipline (0.45 factor):  1 - 0.45*0.12 = 0.946 → 5.4% reduction
            #   → Base chase 35% * 0.946 = 33.1% actual ✓ (MLB poor: 30-35%)
            # This creates 1.9 pp spread (elite to poor), tight but meaningful distribution
            # Combined with fixed curveball/changeup: Expected chase 17.6%→21-24%, K% 14%→20-22%
            swing_prob = base_swing_prob * (1 - discipline_factor * 0.12)
            swing_prob_after_discipline = swing_prob

        # Adjust for decision speed (faster decisions = more aggressive swings)
        # Swing decision latency: lower ms = faster = more aggressive
        # Map to aggression factor: 75ms (elite, fast) = 0.9, 130ms (avg) = 0.5, 200ms (slow) = 0.2
        decision_latency_ms = self.attributes.get_swing_decision_latency_ms()
        # FIXED 2025-11-20: Corrected inverted formula
        # Previous: aggression_factor = 1.0 - (decision_latency_ms - 75) / 125
        #   → 75ms gave 1.0, 200ms gave 0.0 (BACKWARDS!)
        # New: aggression_factor = (200 - decision_latency_ms) / 125
        #   → 75ms gives (200-75)/125 = 1.0 (clipped to 0.9) ✓ aggressive
        #   → 130ms gives (200-130)/125 = 0.56 ✓ average
        #   → 200ms gives (200-200)/125 = 0.0 (clipped to 0.2) ✓ passive
        aggression_factor = np.clip((200.0 - decision_latency_ms) / 125.0, 0.2, 0.9)
        swing_prob_after_reaction = swing_prob * (0.8 + aggression_factor * 0.4)
        swing_prob = swing_prob_after_reaction

        # Velocity effect (faster pitches = less time to decide = more takes)
        velocity_difficulty = (pitch_velocity - 85) / 15.0  # Normalized
        swing_prob_after_velocity = swing_prob
        if velocity_difficulty > 0:
            swing_prob_after_velocity = swing_prob * (1.0 - velocity_difficulty * 0.10)  # Up to -10% for 100 mph
        swing_prob = swing_prob_after_velocity

        # Pitch type affects chase rate (breaking balls fool hitters)
        pitch_type_lower = pitch_type.lower()
        swing_prob_after_pitch_type = swing_prob
        if not is_strike:  # Only affects out-of-zone pitches
            if 'slider' in pitch_type_lower or 'curve' in pitch_type_lower:
                swing_prob_after_pitch_type = swing_prob * 1.25  # +25% chase rate on breaking balls
            elif 'change' in pitch_type_lower or 'splitter' in pitch_type_lower:
                swing_prob_after_pitch_type = swing_prob * 1.15  # +15% chase rate on off-speed
        swing_prob = swing_prob_after_pitch_type

        # Count situation adjustments
        swing_prob_after_count = swing_prob
        if strikes == 2:
            # Protect the plate with 2 strikes
            if is_strike:
                swing_prob_after_count = min(swing_prob + 0.15, 0.95)  # +15%, cap at 95%
            else:
                # PHASE 2A REFINEMENT: Increased 2-strike chase bonus for more strikeouts
                # Previous iterations: 0.15 (Sprint 1) → 0.25 (Refinement Sprint 2)
                # Multiplier (1.4×) + flat bonus (+25%) for 2-strike desperation
                # This ensures batters chase even with elite discipline
                # Expected K% increase: +2-3 percentage points
                base_chase_after_discipline = swing_prob
                two_strike_bonus = 0.25  # Flat +25 percentage points (was 0.15)
                swing_prob_after_count = min(base_chase_after_discipline * 1.4 + two_strike_bonus, 0.70)

        if balls == 3:
            # More selective on 3-ball counts
            if not is_strike:
                swing_prob_after_count = swing_prob * 0.5  # Much less likely to chase
            else:
                swing_prob_after_count = min(swing_prob, 0.85)  # Cap swing rate
        swing_prob = swing_prob_after_count

        # Clip to reasonable bounds
        swing_prob = np.clip(swing_prob, 0.0, 0.98)

        # Make decision
        decision = np.random.random() < swing_prob

        # Log swing decision for Phase 1 debug metrics
        if debug_collector:
            # Calculate distance from zone for logging
            if is_strike:
                distance_from_zone_inches = 0.0
            else:
                h_dist = max(0, abs(pitch_location[0]) - 8.5)
                v_dist_top = max(0, pitch_location[1] - 42.0)
                v_dist_bottom = max(0, 18.0 - pitch_location[1])
                distance_from_zone_inches = np.sqrt(h_dist**2 + (v_dist_top + v_dist_bottom)**2)

            debug_collector.log_swing_decision(
                inning=0,  # Player method doesn't have game context
                balls=balls,
                strikes=strikes,
                outs=0,
                pitch_type=pitch_type,
                pitch_x=pitch_location[0],
                pitch_z=pitch_location[1],
                is_in_zone=is_strike,
                distance_from_zone=distance_from_zone_inches,
                base_swing_prob=base_swing_prob,
                discipline_modifier=swing_prob_after_discipline - base_swing_prob,
                reaction_modifier=swing_prob_after_reaction - swing_prob_after_discipline,
                velocity_modifier=swing_prob_after_velocity - swing_prob_after_reaction,
                pitch_type_modifier=swing_prob_after_pitch_type - swing_prob_after_velocity,
                count_modifier=swing_prob_after_count - swing_prob_after_pitch_type,
                final_swing_prob=swing_prob,
                did_swing=decision,
                batter_discipline=discipline_factor,
                batter_reaction_time_ms=decision_latency_ms
            )

        if return_diagnostics:
            # Simplified run value estimates (approximations)
            # EV if swing: contact_rate * avg_value_if_contact - (1-contact_rate) * strikeout_cost
            # EV if take: strike_prob * called_strike_cost + (1-strike_prob) * ball_value

            # Rough estimates based on count
            estimated_strike_prob = swing_prob if is_strike else (1 - swing_prob)

            # Simple run value model (approximation, not actual wOBA)
            if decision:  # Swing
                # Contact outcome value depends on many factors, use rough avg
                ev_swing = 0.0  # Simplified - would need full contact simulation
            else:  # Take
                if is_strike:
                    ev_take = -0.05  # Taking a strike hurts
                else:
                    ev_take = +0.04  # Taking a ball helps

            # For logging purposes, use swing probability as proxy for expected value
            ev_swing_proxy = (swing_prob - 0.5) * 0.1  # Normalized proxy
            ev_take_proxy = ((1 - swing_prob) - 0.5) * 0.1

            diagnostics = {
                'estimated_strike_prob': estimated_strike_prob,
                'ev_swing': ev_swing_proxy,
                'ev_take': ev_take_proxy,
                'aggression_modifier': aggression_factor - 0.5,  # Centered at 0
                'swing_probability': swing_prob,
                'decision': 'SWING' if decision else 'TAKE'
            }
            return decision, diagnostics

        return decision

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

    def get_pitch_recognition_multiplier(self, pitch_type: str = 'fastball') -> float:
        """
        Get pitch-type specific recognition multiplier based on Statcast metrics.

        This affects chase rate - better recognition = less chasing.

        Parameters
        ----------
        pitch_type : str
            Pitch type

        Returns
        -------
        float
            Multiplier for chase probability (1.0 = baseline, <1.0 = better recognition)
        """
        # Check if we have Statcast-derived recognition for this pitch
        if pitch_type in self.pitch_recognition:
            recognition_rating = self.pitch_recognition[pitch_type].get('recognition', 50000)

            # Convert recognition rating (0-100,000) to chase multiplier
            # 100k = 0.5x (elite recognition - 50% less chasing)
            # 50k = 1.0x (average recognition - baseline)
            # 0k = 1.5x (poor recognition - 50% more chasing)
            multiplier = 1.5 - (recognition_rating / 100000.0)

            return multiplier
        else:
            # No specific data for this pitch - use baseline
            return 1.0

    def get_pitch_contact_multiplier(self, pitch_type: str = 'fastball') -> float:
        """
        Get pitch-type specific contact multiplier based on Statcast metrics.

        This affects contact ability when swinging.

        Parameters
        ----------
        pitch_type : str
            Pitch type

        Returns
        -------
        float
            Multiplier for whiff probability (1.0 = baseline, <1.0 = better contact)
        """
        # Check if we have Statcast-derived contact ability for this pitch
        if pitch_type in self.pitch_recognition:
            contact_rating = self.pitch_recognition[pitch_type].get('contact_ability', 50000)

            # Convert contact ability rating (0-100,000) to whiff multiplier
            # 100k = 0.6x (elite contact - 40% fewer whiffs)
            # 50k = 1.0x (average contact - baseline)
            # 0k = 1.4x (poor contact - 40% more whiffs)
            multiplier = 1.4 - 0.8 * (contact_rating / 100000.0)

            return multiplier
        else:
            # No specific data for this pitch - use baseline
            return 1.0

    def calculate_whiff_probability(
        self,
        pitch_velocity: float,
        pitch_type: str,
        pitch_break: Tuple[float, float],
        debug_collector=None,
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
        # PHASE 2A SPRINT 1 2025-11-20: Reduced breaking ball base rates based on 10-game diagnostic
        # PHASE 2A SPRINT 2 2025-11-20: Additional reductions based on Sprint 1 results
        # Sprint 1 results: K% 14% (down from 16%), Whiff 43.6%, Chase 17.6%
        # Analysis showed:
        #   - Slider PERFECT at 64.0% contact (MLB ~63%) → KEEP at 0.24 ✓
        #   - Curveball TERRIBLE at 23.1% contact (MLB ~70%) → 0.30→0.21 (-30%)
        #   - Changeup still low at 51.6% contact (MLB ~68%) → 0.22→0.18 (-18%)
        #   - Splitter likely similar to curveball → 0.38→0.27 (-29%, preventative)
        # Expected impact: Whiff rate 43.6%→30-34%, K% 14%→20-22% (close to 22% target)
        pitch_type_lower = pitch_type.lower()
        if 'fastball' in pitch_type_lower or '4-seam' in pitch_type_lower:
            base_whiff_rate = 0.15  # Sprint 3 fix: REDUCED from 0.20 (-25%)
            # Sprint 3 test showed 37.2% whiff (62.8% contact) vs MLB ~23% whiff (~77% contact)
            # With multipliers (VISION + velocity + put-away), 0.20 base → 37% actual whiff
            # Need 0.15 base → ~23% actual whiff to reach MLB 77% contact target
        elif '2-seam' in pitch_type_lower or 'sinker' in pitch_type_lower:
            base_whiff_rate = 0.18  # 18% for sinkers
        elif 'cutter' in pitch_type_lower:
            base_whiff_rate = 0.18  # Sprint 1: REDUCED from 0.25 (-28%)
        elif 'slider' in pitch_type_lower:
            base_whiff_rate = 0.24  # Sprint 1: REDUCED from 0.35 (-31%) → PERFECT, keep unchanged
        elif 'curve' in pitch_type_lower:
            base_whiff_rate = 0.21  # Sprint 2: REDUCED from 0.30 (-30%) → was 76.9% whiff
        elif 'change' in pitch_type_lower:
            base_whiff_rate = 0.18  # Sprint 2: REDUCED from 0.22 (-18%) → was 48.4% whiff
        elif 'splitter' in pitch_type_lower:
            base_whiff_rate = 0.27  # Sprint 2: REDUCED from 0.38 (-29%) → preventative
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

        # PHASE 2A: Use VISION for contact frequency, NOT barrel accuracy
        # Previous: barrel_error_mm affected whiff (double-dipping)
        # New: VISION affects whiff probability (tracking ability)
        #      barrel_error_mm ONLY affects contact quality in contact.py
        #
        # VISION decouples contact frequency from contact quality:
        # - Power hitters: Low VISION (high whiff) + low barrel_error (high exit velo)
        # - Contact hitters: High VISION (low whiff) + high barrel_error (low exit velo)
        tracking_ability = self.attributes.get_tracking_ability_factor()  # 0.5-1.0
        vision_factor = 2.0 - tracking_ability  # Invert to multiplier: 1.0-1.5
        # Elite VISION (tracking=1.0) → vision_factor=1.0 (low whiff)
        # Average VISION (tracking=0.75) → vision_factor=1.25 (average whiff)
        # Poor VISION (tracking=0.5) → vision_factor=1.5 (high whiff)

        # Apply pitch-specific contact multiplier from Statcast data
        pitch_contact_mult = self.get_pitch_contact_multiplier(pitch_type)

        # Combine factors (using VISION instead of barrel accuracy)
        whiff_prob = base_whiff_rate * velocity_factor * break_factor * vision_factor * pitch_contact_mult

        # Clip to reasonable bounds (5% minimum, 70% maximum)
        whiff_prob = np.clip(whiff_prob, 0.05, 0.70)

        return whiff_prob

    def __repr__(self):
        bat_speed = self.attributes.get_bat_speed_mph()
        attack_angle = self.attributes.get_attack_angle_mean_deg()
        barrel_error = self.attributes.get_barrel_accuracy_mm()
        zone_discern = self.attributes.get_zone_discernment_factor()
        return (
            f"Hitter(name='{self.name}', "
            f"bat_speed={bat_speed:.1f} mph, angle={attack_angle:.1f}°, "
            f"barrel_error={barrel_error:.1f}mm, zone_discern={zone_discern:.2f})"
        )
