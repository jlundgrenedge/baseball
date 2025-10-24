"""
Player attribute system for pitchers and hitters.

Integrates attribute ratings with physics-based simulation to create
realistic baseball gameplay with individual player characteristics.
"""

import numpy as np
from typing import Dict, List, Optional, Tuple
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

        # Core physics attributes (0-100 scale)
        self.velocity = np.clip(velocity, 0, 100)
        self.spin_rate = np.clip(spin_rate, 0, 100)
        self.spin_efficiency = np.clip(spin_efficiency, 0, 100)
        self.spin_axis_control = np.clip(spin_axis_control, 0, 100)
        self.release_extension = np.clip(release_extension, 0, 100)
        self.arm_slot = arm_slot

        # Skill attributes (0-100 scale)
        self.command = np.clip(command, 0, 100)
        self.control = np.clip(control, 0, 100)
        self.pitch_tunneling = np.clip(pitch_tunneling, 0, 100)
        self.deception = np.clip(deception, 0, 100)
        self.stamina = np.clip(stamina, 0, 100)
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

        # Core physical attributes
        self.bat_speed = np.clip(bat_speed, 0, 100)
        self.swing_path_angle = swing_path_angle
        self.barrel_accuracy = np.clip(barrel_accuracy, 0, 100)
        self.swing_timing_precision = np.clip(swing_timing_precision, 0, 100)
        self.bat_control = np.clip(bat_control, 0, 100)

        # Outcome-influencing attributes
        self.exit_velocity_ceiling = np.clip(exit_velocity_ceiling, 0, 100)
        self.launch_angle_tendency = launch_angle_tendency
        self.spin_control = np.clip(spin_control, 0, 100)
        self.spray_tendency = spray_tendency

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
        # 20 = 60 mph, 50 = 70 mph, 80 = 77 mph, 100 = 82 mph
        bat_speed_mph = 60.0 + (self.bat_speed - 20) * 0.275
        return bat_speed_mph

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
        # Higher barrel accuracy = smaller offsets
        # 20 = 2" max offset, 50 = 1" max offset, 80 = 0.3" max offset, 100 = 0.1" max offset
        max_offset = 2.0 - (self.barrel_accuracy - 20) * 0.02375
        max_offset = max(max_offset, 0.1)

        # Add random error based on bat control
        control_factor = self.bat_control / 100.0
        error_std = max_offset * (1.0 - control_factor * 0.7)

        horizontal_offset = np.random.normal(0, error_std)
        vertical_offset = np.random.normal(0, error_std)

        return horizontal_offset, vertical_offset

    def decide_to_swing(
        self,
        pitch_location: Tuple[float, float],
        is_strike: bool,
        count: Tuple[int, int],
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

        Returns
        -------
        bool
            True if swinging, False if taking
        """
        balls, strikes = count

        # Base swing probability based on strike zone
        if is_strike:
            base_swing_prob = 0.65  # Swing at ~65% of strikes
        else:
            # Distance from zone affects chase probability
            h_dist = abs(pitch_location[0])
            v_dist_top = max(0, pitch_location[1] - 3.5)
            v_dist_bottom = max(0, 1.5 - pitch_location[1])
            distance_from_zone = np.sqrt(h_dist**2 + (v_dist_top + v_dist_bottom)**2)

            # Further from zone = less likely to swing
            base_swing_prob = 0.35 * np.exp(-distance_from_zone / 4.0)

        # Adjust for zone discipline (higher = more selective)
        discipline_factor = self.zone_discipline / 100.0
        if is_strike:
            swing_prob = base_swing_prob + (1 - discipline_factor) * 0.20
        else:
            swing_prob = base_swing_prob * (1 - discipline_factor * 0.7)

        # Adjust for aggressiveness
        aggression_factor = self.swing_decision_aggressiveness / 100.0
        swing_prob = swing_prob * (0.7 + aggression_factor * 0.6)

        # Count situation adjustments
        if strikes == 2:
            swing_prob += 0.20  # Protect with 2 strikes
        if balls == 3:
            swing_prob -= 0.15  # More selective on 3-0, 3-1, 3-2

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
        # Faster pitches are harder to time
        velocity_difficulty = (pitch_velocity - 80) / 20.0  # Normalized difficulty

        # Higher precision = less error
        # 20 = 15 ms error, 50 = 8 ms error, 80 = 3 ms error, 100 = 1 ms error
        max_error_ms = 15.0 - (self.swing_timing_precision - 20) * 0.175
        max_error_ms = max(max_error_ms, 1.0)

        # Adjust for velocity difficulty
        adjusted_error = max_error_ms * (1.0 + velocity_difficulty * 0.3)

        # Random error with normal distribution
        timing_error = np.random.normal(0, adjusted_error / 2.0)

        return timing_error

    def __repr__(self):
        return (
            f"Hitter(name='{self.name}', "
            f"bat_speed={self.bat_speed}, barrel_accuracy={self.barrel_accuracy}, "
            f"discipline={self.zone_discipline}, contact={self.bat_control})"
        )
