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
    Represents a pitcher with attribute ratings that influence pitch physics.

    Core Attributes (Physics-Driven):
    - velocity: Average pitch speed (0-100 rating)
    - spin_rate: Raw RPM generation ability (0-100 rating)
    - spin_efficiency: Percentage of spin creating movement (0-100 rating)
    - spin_axis_control: Ability to repeat spin axis (0-100 rating)
    - release_extension: Stride length (0-100 rating)
    - arm_slot: Release angle in degrees (0=overhand, 45=3/4, 90=sidearm)

    Skill-Based Attributes:
    - command: Accuracy of pitch location (0-100 rating)
    - control: Ability to throw strikes (0-100 rating)
    - pitch_tunneling: Deception in pitch similarity (0-100 rating)
    - deception: Overall deception ability (0-100 rating)
    - stamina: Endurance over outing (0-100 rating)
    - fatigue_resistance: Resistance to attribute degradation (0-100 rating)

    Pitch Arsenal:
    - pitch_arsenal: Dict of pitch types with individual ratings
    """

    def __init__(
        self,
        name: str = "Pitcher",
        # Core physics attributes
        velocity: int = 50,
        spin_rate: int = 50,
        spin_efficiency: int = 50,
        spin_axis_control: int = 50,
        release_extension: int = 50,
        arm_slot: float = ARM_ANGLE_3_4,
        # Skill attributes
        command: int = 50,
        control: int = 50,
        pitch_tunneling: int = 50,
        deception: int = 50,
        stamina: int = 50,
        fatigue_resistance: int = 50,
        # Pitch arsenal
        pitch_arsenal: Optional[Dict[str, Dict[str, int]]] = None,
        # NEW: Physics-first attributes (0-100,000 scale)
        attributes_v2: Optional[PitcherAttributes] = None,
    ):
        """
        Initialize pitcher with attribute ratings.

        Parameters
        ----------
        name : str
            Pitcher's name
        velocity : int (0-100)
            Fastball velocity rating (50=avg MLB, 80=elite, 100=Chapman/Hicks)
        spin_rate : int (0-100)
            Spin generation ability (50=avg MLB, 80=elite)
        spin_efficiency : int (0-100)
            Quality of spin axis (50=avg, 80=elite efficiency)
        spin_axis_control : int (0-100)
            Consistency of spin axis (50=avg, 80=very consistent)
        release_extension : int (0-100)
            Stride length (50=6.0 ft, 80=7.0+ ft)
        arm_slot : float
            Release angle in degrees (0=overhand, 45=3/4, 90=sidearm)
        command : int (0-100)
            Location precision (50=avg, 80=excellent, 100=Maddux-level)
        control : int (0-100)
            Strike-throwing ability (50=avg, 80=excellent)
        pitch_tunneling : int (0-100)
            Pitch similarity/deception (50=avg, 80=very deceptive)
        deception : int (0-100)
            Overall deceptiveness (50=avg, 80=very deceptive)
        stamina : int (0-100)
            Endurance (50=avg starter, 80=workhorse)
        fatigue_resistance : int (0-100)
            Resistance to degradation (50=avg, 80=maintains stuff late)
        pitch_arsenal : dict, optional
            Dict of pitch types with individual ratings
            Format: {'fastball': {'velocity': 60, 'movement': 70, 'command': 50}}
        """
        self.name = name

        # Store new attribute system if provided
        self.attributes_v2 = attributes_v2

        # Core physics attributes (legacy 0-100 scale, or defaults if using attributes_v2)
        self.velocity = np.clip(velocity, 0, 100)
        self.spin_rate = np.clip(spin_rate, 0, 100)
        self.spin_efficiency = np.clip(spin_efficiency, 0, 100)
        self.spin_axis_control = np.clip(spin_axis_control, 0, 100)
        self.release_extension = np.clip(release_extension, 0, 100)
        self.arm_slot = arm_slot

        # Skill attributes (legacy 0-100 scale, or defaults if using attributes_v2)
        self.command = np.clip(command, 0, 100)
        self.control = np.clip(control, 0, 100)
        self.pitch_tunneling = np.clip(pitch_tunneling, 0, 100)
        self.deception = np.clip(deception, 0, 100)
        self.stamina = np.clip(stamina, 0, 100) if attributes_v2 is None else 50
        self.fatigue_resistance = np.clip(fatigue_resistance, 0, 100)

        # Pitch arsenal
        if pitch_arsenal is None:
            # Default: above-average 4-seam fastball
            pitch_arsenal = {
                'fastball': {
                    'velocity': velocity,
                    'movement': 50,
                    'command': command,
                }
            }
        self.pitch_arsenal = pitch_arsenal

        # State variables
        self.current_stamina = stamina  # Decreases during game
        self.pitches_thrown = 0

    def get_pitch_velocity_mph(self, pitch_type: str = 'fastball') -> float:
        """
        Convert velocity rating to actual MPH for a pitch type.

        Parameters
        ----------
        pitch_type : str
            Pitch type from arsenal

        Returns
        -------
        float
            Velocity in MPH
        """
        # Use new attribute system if available
        if self.attributes_v2 is not None:
            # Get base velocity from physics-first attributes
            velocity_mph = self.attributes_v2.get_raw_velocity_mph()

            # Apply pitch-type modifiers (fastball = 100%, changeup = ~85%, etc.)
            if pitch_type == 'changeup':
                velocity_mph *= 0.85
            elif pitch_type == 'curveball':
                velocity_mph *= 0.88
            elif pitch_type == 'slider':
                velocity_mph *= 0.92

            # Apply stamina degradation based on pitches thrown
            stamina_cap = self.attributes_v2.get_stamina_pitches()
            stamina_factor = max(0.0, 1.0 - (self.pitches_thrown / stamina_cap))
            stamina_loss = (1.0 - stamina_factor) * 4.0  # Up to 4 mph loss when exhausted

            return max(velocity_mph - stamina_loss, 70.0)

        # Legacy calculation
        # Get pitch-specific velocity rating or use general rating
        if pitch_type in self.pitch_arsenal:
            velocity_rating = self.pitch_arsenal[pitch_type].get('velocity', self.velocity)
        else:
            velocity_rating = self.velocity

        # Map rating to velocity
        # 20 = 85 mph, 50 = 93 mph, 80 = 98 mph, 100 = 103 mph
        velocity_mph = 85.0 + (velocity_rating - 20) * 0.225

        # Apply stamina degradation
        stamina_factor = self.current_stamina / 100.0
        stamina_loss = (1.0 - stamina_factor) * 3.0  # Up to 3 mph loss when exhausted

        return max(velocity_mph - stamina_loss, 70.0)

    def get_pitch_spin_rpm(self, pitch_type: str = 'fastball', base_spin: float = 2200) -> float:
        """
        Convert spin rating to actual RPM for a pitch type.

        Parameters
        ----------
        pitch_type : str
            Pitch type from arsenal
        base_spin : float
            Base spin rate for pitch type (from pitch constants)

        Returns
        -------
        float
            Spin rate in RPM
        """
        # Use new attribute system if available
        if self.attributes_v2 is not None:
            # Get base spin rate from physics-first attributes (for 4-seam fastball)
            base_spin_rpm = self.attributes_v2.get_spin_rate_rpm()

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
            stamina_cap = self.attributes_v2.get_stamina_pitches()
            stamina_factor = max(0.0, 1.0 - (self.pitches_thrown / stamina_cap))
            stamina_loss = (1.0 - stamina_factor) * 0.12  # Up to 12% spin loss when exhausted

            return spin_rpm * (1.0 - stamina_loss)

        # Legacy calculation
        # Get pitch-specific movement rating (which affects spin)
        if pitch_type in self.pitch_arsenal:
            movement_rating = self.pitch_arsenal[pitch_type].get('movement', self.spin_rate)
        else:
            movement_rating = self.spin_rate

        # Map rating to spin multiplier
        # 20 = 80% of base, 50 = 100% of base, 80 = 120% of base, 100 = 140% of base
        spin_multiplier = 0.80 + (movement_rating - 20) * 0.0075

        # Apply stamina degradation
        stamina_factor = self.current_stamina / 100.0
        stamina_loss = (1.0 - stamina_factor) * 0.10  # Up to 10% spin loss when exhausted

        return base_spin * spin_multiplier * (1.0 - stamina_loss)

    def get_release_extension_feet(self) -> float:
        """
        Convert extension rating to actual feet.

        Returns
        -------
        float
            Extension in feet
        """
        # 20 = 5.0 ft, 50 = 6.0 ft, 80 = 7.0 ft, 100 = 7.5 ft
        extension_ft = RELEASE_EXTENSION_MIN + (self.release_extension / 100.0) * \
                      (RELEASE_EXTENSION_MAX - RELEASE_EXTENSION_MIN)
        return extension_ft

    def get_command_error_inches(self, pitch_type: str = 'fastball') -> Tuple[float, float]:
        """
        Calculate location error based on command rating.

        Parameters
        ----------
        pitch_type : str
            Pitch type from arsenal

        Returns
        -------
        tuple
            (horizontal_error_inches, vertical_error_inches)
        """
        # Get pitch-specific command or use general command
        if pitch_type in self.pitch_arsenal:
            command_rating = self.pitch_arsenal[pitch_type].get('command', self.command)
        else:
            command_rating = self.command

        # Map rating to error (lower rating = more error)
        # 20 = 6" error, 50 = 3" error, 80 = 1" error, 100 = 0.3" error
        max_error = 6.0 - (command_rating - 20) * 0.07125
        max_error = max(max_error, 0.3)

        # Apply stamina degradation
        stamina_factor = self.current_stamina / 100.0
        fatigue_multiplier = 1.0 + (1.0 - stamina_factor) * 1.0  # Up to 2x error when exhausted

        # Random error with normal distribution
        horizontal_error = np.random.normal(0, max_error * fatigue_multiplier / 2.0)
        vertical_error = np.random.normal(0, max_error * fatigue_multiplier / 2.0)

        return horizontal_error, vertical_error

    def throw_pitch(self):
        """Update state after throwing a pitch."""
        self.pitches_thrown += 1

        # Stamina degradation based on fatigue resistance
        # High fatigue resistance = slower stamina loss
        stamina_loss_per_pitch = 0.5 * (100 - self.fatigue_resistance) / 100.0
        self.current_stamina = max(self.current_stamina - stamina_loss_per_pitch, 0)

    def __repr__(self):
        return (
            f"Pitcher(name='{self.name}', "
            f"velocity={self.velocity}, movement={self.spin_rate}, "
            f"command={self.command}, deception={self.deception})"
        )


class Hitter:
    """
    Represents a hitter with attribute ratings that influence contact physics.

    Core Physical Attributes:
    - bat_speed: Swing speed rating (0-100)
    - swing_path_angle: Launch angle tendency (degrees, typically 5-20)
    - barrel_accuracy: Sweet spot contact ability (0-100)
    - swing_timing_precision: Timing consistency (0-100)
    - bat_control: Contact location control (0-100)

    Outcome-Influencing Attributes:
    - exit_velocity_ceiling: Max exit velo capability (0-100)
    - launch_angle_tendency: Typical contact profile (degrees)
    - spin_control: Backspin generation ability (0-100)
    - spray_tendency: Pull vs oppo (degrees, -45 to +45)

    Perception & Decision Attributes:
    - pitch_recognition_speed: How quickly identify pitch (0-100)
    - zone_discipline: Strike zone judgment (0-100)
    - swing_decision_aggressiveness: Swing frequency (0-100)
    - adjustment_ability: Adaptability to difficult pitches (0-100)
    """

    def __init__(
        self,
        name: str = "Hitter",
        # Core physical attributes
        bat_speed: int = 50,
        swing_path_angle: float = 15.0,
        barrel_accuracy: int = 50,
        swing_timing_precision: int = 50,
        bat_control: int = 50,
        # Outcome-influencing attributes
        exit_velocity_ceiling: int = 50,
        launch_angle_tendency: float = 15.0,
        spin_control: int = 50,
        spray_tendency: float = 0.0,
        # Perception & decision attributes
        pitch_recognition_speed: int = 50,
        zone_discipline: int = 50,
        swing_decision_aggressiveness: int = 50,
        adjustment_ability: int = 50,
        # NEW: Physics-first attributes (0-100,000 scale)
        attributes_v2: Optional[HitterAttributes] = None,
    ):
        """
        Initialize hitter with attribute ratings.

        Parameters
        ----------
        name : str
            Hitter's name
        bat_speed : int (0-100)
            Swing speed rating (50=avg MLB ~70 mph, 80=elite ~75 mph)
        swing_path_angle : float
            Natural swing path angle in degrees (5-20 typical)
        barrel_accuracy : int (0-100)
            Sweet spot contact ability (50=avg, 80=elite contact hitter)
        swing_timing_precision : int (0-100)
            Timing consistency (50=avg, 80=rarely mis-timed)
        bat_control : int (0-100)
            Contact location control (50=avg, 80=excellent)
        exit_velocity_ceiling : int (0-100)
            Max exit velo capability (50=avg ~95 mph, 80=elite ~105 mph)
        launch_angle_tendency : float
            Typical launch angle in degrees (15=line drives, 25=fly balls)
        spin_control : int (0-100)
            Backspin generation (50=avg, 80=elite carry)
        spray_tendency : float
            Pull vs oppo in degrees (-45=pull, 0=center, +45=oppo)
        pitch_recognition_speed : int (0-100)
            Pitch identification speed (50=avg, 80=excellent)
        zone_discipline : int (0-100)
            Strike zone judgment (50=avg, 80=excellent patience)
        swing_decision_aggressiveness : int (0-100)
            Swing frequency (50=avg, 80=very aggressive, 20=patient)
        adjustment_ability : int (0-100)
            Adaptability (50=avg, 80=adjusts well to any pitch)
        """
        self.name = name

        # Store new attribute system if provided
        self.attributes_v2 = attributes_v2

        # Core physical attributes (legacy 0-100 scale, or defaults if using attributes_v2)
        self.bat_speed = np.clip(bat_speed, 0, 100)
        self.swing_path_angle = swing_path_angle if attributes_v2 is None else 15.0
        self.barrel_accuracy = np.clip(barrel_accuracy, 0, 100)
        self.swing_timing_precision = np.clip(swing_timing_precision, 0, 100)
        self.bat_control = np.clip(bat_control, 0, 100)

        # Outcome-influencing attributes
        self.exit_velocity_ceiling = np.clip(exit_velocity_ceiling, 0, 100)
        self.launch_angle_tendency = launch_angle_tendency if attributes_v2 is None else 15.0
        self.spin_control = np.clip(spin_control, 0, 100)
        self.spray_tendency = spray_tendency if attributes_v2 is None else 0.0  # Neutral spray for new system

        # Perception & decision attributes
        self.pitch_recognition_speed = np.clip(pitch_recognition_speed, 0, 100)
        self.zone_discipline = np.clip(zone_discipline, 0, 100)
        self.swing_decision_aggressiveness = np.clip(swing_decision_aggressiveness, 0, 100)
        self.adjustment_ability = np.clip(adjustment_ability, 0, 100)

    def get_bat_speed_mph(self) -> float:
        """
        Convert bat speed rating to actual MPH.

        Returns
        -------
        float
            Bat speed in MPH
        """
        # Use new attribute system if available
        if self.attributes_v2 is not None:
            return self.attributes_v2.get_bat_speed_mph()

        # Legacy: 20 = 60 mph, 50 = 70 mph, 80 = 77 mph, 100 = 82 mph
        bat_speed_mph = 60.0 + (self.bat_speed - 20) * 0.275
        return bat_speed_mph

    def get_swing_path_angle_deg(self) -> float:
        """
        Get swing path angle (attack angle) in degrees.

        For new attribute system: samples from mean with variance
        For legacy: returns fixed swing_path_angle

        Returns
        -------
        float
            Swing path angle in degrees
        """
        # Use new attribute system if available
        if self.attributes_v2 is not None:
            mean_angle = self.attributes_v2.get_attack_angle_mean_deg()
            variance = self.attributes_v2.get_attack_angle_variance_deg()

            # Sample from normal distribution
            return np.random.normal(mean_angle, variance)

        # Legacy: fixed angle
        return self.swing_path_angle

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
        # Use new attribute system if available
        if self.attributes_v2 is not None:
            # Get barrel accuracy in mm, convert to inches
            error_mm = self.attributes_v2.get_barrel_accuracy_mm()
            error_inches = error_mm / 25.4  # mm to inches

            # Sample from normal distribution
            horizontal_offset = np.random.normal(0, error_inches)
            vertical_offset = np.random.normal(0, error_inches)

            return horizontal_offset, vertical_offset

        # Legacy calculation
        # Higher barrel accuracy = smaller offsets (adjusted for realism)
        # 20 = 1.5" max offset, 50 = 0.8" max offset, 75 = 0.4" max offset, 100 = 0.15" max offset
        max_offset = 1.5 - (self.barrel_accuracy - 20) * 0.017
        max_offset = max(max_offset, 0.15)

        # Add random error based on bat control - more variance for worse control
        control_factor = self.bat_control / 100.0
        error_std = max_offset * (1.0 - control_factor * 0.3)  # Reduced control impact

        horizontal_offset = np.random.normal(0, error_std)
        vertical_offset = np.random.normal(0, error_std)

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
        # Use new attribute system if available
        if self.attributes_v2 is not None:
            # Get base timing precision (RMS error in ms)
            error_ms = self.attributes_v2.get_timing_precision_ms()

            # Faster pitches harder to time (velocity difficulty adjustment)
            velocity_difficulty = (pitch_velocity - 80) / 20.0
            adjusted_error = error_ms * (1.0 + velocity_difficulty * 0.3)

            # Sample from normal distribution
            return np.random.normal(0, adjusted_error)

        # Legacy calculation
        # Faster pitches are harder to time
        velocity_difficulty = (pitch_velocity - 80) / 20.0  # Normalized difficulty

        # Higher precision = less error (more realistic timing windows)
        # 20 = 8 ms error, 50 = 5 ms error, 80 = 2 ms error, 100 = 0.5 ms error
        max_error_ms = 8.0 - (self.swing_timing_precision - 20) * 0.09
        max_error_ms = max(max_error_ms, 0.5)

        # Adjust for velocity difficulty
        adjusted_error = max_error_ms * (1.0 + velocity_difficulty * 0.3)

        # Random error with normal distribution
        timing_error = np.random.normal(0, adjusted_error / 2.0)

        return timing_error

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
        # Elite contact (85+): 0.6x whiff rate
        # Average (50): 1.0x whiff rate
        # Poor (20): 1.8x whiff rate
        contact_factor = 1.8 - (self.barrel_accuracy - 20) * 0.0125

        # Combine factors
        whiff_prob = base_whiff_rate * velocity_factor * break_factor * contact_factor

        # Clip to reasonable bounds (5% minimum, 70% maximum)
        whiff_prob = np.clip(whiff_prob, 0.05, 0.70)

        return whiff_prob

    def __repr__(self):
        return (
            f"Hitter(name='{self.name}', "
            f"bat_speed={self.bat_speed}, barrel_accuracy={self.barrel_accuracy}, "
            f"discipline={self.zone_discipline}, contact={self.bat_control})"
        )
