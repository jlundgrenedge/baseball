"""
At-bat simulation engine integrating pitcher and hitter attributes with physics.

Simulates realistic plate appearances using:
- Pitcher attributes → pitch physics parameters
- Hitter attributes → swing decision and contact quality
- Physics engines → pitch trajectory and batted ball flight
"""

import numpy as np
from typing import Dict, List, Optional, Tuple
from .player import Pitcher, Hitter
from .pitch import (
    PitchSimulator,
    create_fastball_4seam,
    create_fastball_2seam,
    create_cutter,
    create_curveball,
    create_slider,
    create_changeup,
    create_splitter,
)
from .contact import ContactModel
from .trajectory import BattedBallSimulator
from .constants import (
    STRIKE_ZONE_WIDTH,
    STRIKE_ZONE_BOTTOM,
    STRIKE_ZONE_TOP,
)


class AtBatResult:
    """Container for at-bat simulation results."""

    def __init__(
        self,
        outcome: str,
        pitches: List[Dict],
        final_count: Tuple[int, int],
        batted_ball_result: Optional[Dict] = None,
    ):
        """
        Initialize at-bat result.

        Parameters
        ----------
        outcome : str
            Final outcome: 'strikeout', 'walk', 'in_play', 'foul'
        pitches : list
            List of pitch dictionaries with details
        final_count : tuple
            (balls, strikes) at conclusion
        batted_ball_result : dict, optional
            Batted ball trajectory data if ball was put in play
        """
        self.outcome = outcome
        self.pitches = pitches
        self.final_count = final_count
        self.batted_ball_result = batted_ball_result

    def __repr__(self):
        return f"AtBatResult(outcome='{self.outcome}', count={self.final_count}, pitches={len(self.pitches)})"


class AtBatSimulator:
    """
    Simulates realistic plate appearances between pitcher and hitter.

    Integrates:
    - Pitcher attributes → pitch characteristics
    - Hitter attributes → swing decisions and contact quality
    - Physics simulation → pitch and batted ball trajectories
    """

    def __init__(
        self,
        pitcher: Pitcher,
        hitter: Hitter,
        altitude: float = 0.0,
        temperature: float = 70.0,
        humidity: float = 0.5,
        fast_mode: bool = False,
    ):
        """
        Initialize at-bat simulator.

        Parameters
        ----------
        pitcher : Pitcher
            Pitcher with attribute ratings
        hitter : Hitter
            Hitter with attribute ratings
        altitude : float
            Altitude in feet (default: 0 = sea level)
        temperature : float
            Temperature in Fahrenheit (default: 70)
        humidity : float
            Relative humidity 0-1 (default: 0.5)
        fast_mode : bool
            If True, uses faster simulation with larger time steps (~2x speedup)
            Recommended for bulk simulations (1000+ at-bats)
        """
        self.pitcher = pitcher
        self.hitter = hitter
        self.altitude = altitude
        self.temperature = temperature
        self.humidity = humidity
        self.fast_mode = fast_mode

        # Create physics simulators
        self.pitch_sim = PitchSimulator()
        self.contact_model = ContactModel()
        self.batted_ball_sim = BattedBallSimulator()

    def select_pitch_type(self, count: Tuple[int, int], recent_pitches: List[str] = None) -> str:
        """
        Select pitch type based on count, arsenal, and pitch sequencing.

        Parameters
        ----------
        count : tuple
            (balls, strikes)
        recent_pitches : list, optional
            Last 1-2 pitch types thrown (for sequencing)

        Returns
        -------
        str
            Selected pitch type from pitcher's arsenal
        """
        if recent_pitches is None:
            recent_pitches = []

        arsenal = list(self.pitcher.pitch_arsenal.keys())

        if not arsenal:
            return 'fastball'

        balls, strikes = count

        # Calculate count leverage
        # Positive = pitcher ahead, negative = hitter ahead
        leverage = strikes - balls

        # Build weighted selection based on situation
        pitch_weights = {}

        for pitch_type in arsenal:
            pitch_data = self.pitcher.pitch_arsenal[pitch_type]
            weight = pitch_data.get('usage', 50) / 100.0  # Base weight from usage rating

            # Adjust based on count leverage
            if leverage >= 2:
                # Pitcher ahead (0-2, 1-2, 2-2) - can waste pitch
                if pitch_type in ['slider', 'curveball', 'splitter', 'changeup']:
                    weight *= 1.5  # Favor breaking/offspeed
            elif leverage <= -2:
                # Hitter ahead (3-0, 3-1) - need strike
                if pitch_type in ['fastball', '4-seam', '2-seam', 'cutter']:
                    weight *= 2.0  # Strongly favor fastballs
                else:
                    weight *= 0.3  # Reduce breaking balls
            elif balls == 3 and strikes < 2:
                # 3-ball count - must throw strike
                if pitch_type in ['fastball', '4-seam']:
                    weight *= 2.5
                else:
                    weight *= 0.2
            elif strikes == 2:
                # Two-strike count - put-away pitch
                if pitch_type in ['slider', 'changeup', 'splitter']:
                    weight *= 1.8  # Favor out pitches

            # Pitch sequencing - avoid repeating same pitch
            if recent_pitches:
                if pitch_type == recent_pitches[-1]:
                    weight *= 0.3  # Strongly discourage same pitch
                if len(recent_pitches) >= 2 and pitch_type == recent_pitches[-2]:
                    weight *= 0.5  # Discourage pitch from 2 ago

            # Set-up sequences (fastball -> offspeed)
            if recent_pitches and len(recent_pitches) >= 1:
                last_pitch = recent_pitches[-1]
                if last_pitch in ['fastball', '4-seam'] and pitch_type in ['changeup', 'splitter']:
                    weight *= 1.3  # Favor changeup/splitter after fastball
                elif last_pitch in ['curveball', 'slider'] and pitch_type in ['fastball', '4-seam']:
                    weight *= 1.2  # Favor fastball after breaking ball

            pitch_weights[pitch_type] = max(weight, 0.01)  # Ensure positive weight

        # Weighted random selection
        pitch_types = list(pitch_weights.keys())
        weights = list(pitch_weights.values())
        weights_array = np.array(weights)
        weights_array /= weights_array.sum()  # Normalize

        return np.random.choice(pitch_types, p=weights_array)

    def select_target_location(
        self,
        count: Tuple[int, int],
        pitch_type: str,
    ) -> Tuple[float, float]:
        """
        Select target location for pitch.

        Parameters
        ----------
        count : tuple
            (balls, strikes)
        pitch_type : str
            Type of pitch being thrown

        Returns
        -------
        tuple
            (horizontal_inches, vertical_inches) target location
        """
        balls, strikes = count

        # Simplified targeting logic
        # Returns (horizontal_inches, vertical_inches)

        # Horizontal target (centered with some variation)
        horizontal_target = np.random.normal(0, 3.0)  # Aim near center, ±3" variation

        # Vertical target based on count (in inches)
        # Strike zone: 18" (knees) to 42" (letters), center at 30"
        if balls >= 3:
            # Need strike - aim middle
            vertical_target = 30.0  # Middle of zone (30")
        elif strikes >= 2:
            # Can go outside zone
            if np.random.random() < 0.4:
                # Chase pitch
                vertical_target = np.random.choice([12.0, 48.0])  # Low or high (outside zone)
            else:
                # Still in zone
                vertical_target = 30.0
        else:
            # Normal targeting - varied locations in zone
            vertical_target = np.random.choice([21.0, 30.0, 39.0])  # Low, mid, high in zone

        return horizontal_target, vertical_target

    def simulate_pitch(
        self,
        pitch_type: str,
        target_location: Tuple[float, float],
    ) -> Dict:
        """
        Simulate a single pitch using pitcher attributes.

        Parameters
        ----------
        pitch_type : str
            Type of pitch to throw
        target_location : tuple
            (horizontal_inches, vertical_inches) target

        Returns
        -------
        dict
            Pitch result with trajectory data
        """
        # Get command error
        h_error, v_error = self.pitcher.get_command_error_inches(pitch_type)

        # Actual location includes command error
        actual_target_h = target_location[0] + h_error
        actual_target_v = target_location[1] + v_error

        # Create pitch type with pitcher's attributes
        if pitch_type == 'fastball' or pitch_type == '4-seam':
            velocity = self.pitcher.get_pitch_velocity_mph('fastball')
            spin = self.pitcher.get_pitch_spin_rpm('fastball', 2200)
            pitch = create_fastball_4seam(velocity, spin)
        elif pitch_type == '2-seam' or pitch_type == 'sinker':
            velocity = self.pitcher.get_pitch_velocity_mph('2-seam')
            spin = self.pitcher.get_pitch_spin_rpm('2-seam', 2100)
            pitch = create_fastball_2seam(velocity, spin)
        elif pitch_type == 'cutter':
            velocity = self.pitcher.get_pitch_velocity_mph('cutter')
            spin = self.pitcher.get_pitch_spin_rpm('cutter', 2200)
            pitch = create_cutter(velocity, spin)
        elif pitch_type == 'curveball' or pitch_type == 'curve':
            velocity = self.pitcher.get_pitch_velocity_mph('curveball')
            spin = self.pitcher.get_pitch_spin_rpm('curveball', 2500)
            pitch = create_curveball(velocity, spin)
        elif pitch_type == 'slider':
            velocity = self.pitcher.get_pitch_velocity_mph('slider')
            spin = self.pitcher.get_pitch_spin_rpm('slider', 2400)
            pitch = create_slider(velocity, spin)
        elif pitch_type == 'changeup' or pitch_type == 'change':
            velocity = self.pitcher.get_pitch_velocity_mph('changeup')
            spin = self.pitcher.get_pitch_spin_rpm('changeup', 1750)
            pitch = create_changeup(velocity, spin)
        elif pitch_type == 'splitter':
            velocity = self.pitcher.get_pitch_velocity_mph('splitter')
            spin = self.pitcher.get_pitch_spin_rpm('splitter', 1500)
            pitch = create_splitter(velocity, spin)
        else:
            # Default to fastball
            velocity = self.pitcher.get_pitch_velocity_mph('fastball')
            spin = self.pitcher.get_pitch_spin_rpm('fastball', 2200)
            pitch = create_fastball_4seam(velocity, spin)

        # Simulate pitch with physics
        extension = self.pitcher.get_release_extension_feet()
        # Calculate release distance (mound distance - extension)
        from .constants import MOUND_DISTANCE
        release_distance = MOUND_DISTANCE - extension

        result = self.pitch_sim.simulate(
            pitch,
            target_x=actual_target_h / 12.0,  # Convert inches to feet
            target_z=actual_target_v / 12.0,
            release_distance=release_distance,
            altitude=self.altitude,
            temperature=self.temperature,
            humidity=self.humidity,
            fast_mode=self.fast_mode,
        )

        # Update pitcher state
        self.pitcher.throw_pitch()

        return {
            'pitch_type': pitch_type,
            'target_location': target_location,
            'actual_location': (actual_target_h, actual_target_v),
            'final_location': (result.plate_y * 12, result.plate_z * 12),  # Inches - now accurate!
            'velocity_release': velocity,
            'velocity_plate': result.plate_speed,
            'is_strike': result.is_strike,
            'break': (result.vertical_break, result.horizontal_break),
            'result': result,
        }

    def simulate_contact(
        self,
        pitch_data: Dict,
    ) -> Optional[Dict]:
        """
        Simulate bat-ball contact using hitter attributes.

        Parameters
        ----------
        pitch_data : dict
            Pitch result data

        Returns
        -------
        dict or None
            Batted ball result if contact made, None if whiff
        """
        pitch_velocity = pitch_data['velocity_plate']
        pitch_location = pitch_data['final_location']
        pitch_type = pitch_data['pitch_type']
        pitch_break = pitch_data['break']

        # Calculate whiff probability using MLB Statcast data
        whiff_prob = self.hitter.calculate_whiff_probability(
            pitch_velocity=pitch_velocity,
            pitch_type=pitch_type,
            pitch_break=pitch_break,
        )

        # Check if whiff occurs
        if np.random.random() < whiff_prob:
            return None  # Whiff!

        # Get bat speed from hitter attributes
        bat_speed = self.hitter.get_bat_speed_mph()

        # Get contact point offset
        h_offset, v_offset = self.hitter.get_contact_point_offset(pitch_location)

        # Get swing timing error
        timing_error_ms = self.hitter.get_swing_timing_error_ms(pitch_velocity)

        # Timing error affects horizontal offset
        # Rough approximation: 1 ms = ~0.5 inch offset
        timing_offset = timing_error_ms * 0.5

        # Total horizontal offset
        total_h_offset = h_offset + timing_offset

        # Calculate total offset for contact quality
        total_offset = np.sqrt(total_h_offset**2 + v_offset**2)

        # Contact made - simulate with physics
        collision_result = self.contact_model.full_collision(
            bat_speed_mph=bat_speed,
            pitch_speed_mph=pitch_velocity,
            bat_path_angle_deg=self.hitter.swing_path_angle,  # Hitter's swing path
            pitch_trajectory_angle_deg=7.0,  # Typical downward angle
            vertical_contact_offset_inches=v_offset,
            horizontal_contact_offset_inches=total_h_offset,
        )

        # Simulate batted ball trajectory
        batted_ball_result = self.batted_ball_sim.simulate(
            exit_velocity=collision_result['exit_velocity'],
            launch_angle=collision_result['launch_angle'],
            spray_angle=self.hitter.spray_tendency,  # Use hitter's spray tendency
            backspin_rpm=collision_result['backspin_rpm'],
            altitude=self.altitude,
            temperature=self.temperature,
            fast_mode=self.fast_mode,
        )

        return {
            'contact_quality': 'solid' if total_offset < 0.5 else 'weak' if total_offset > 1.5 else 'fair',
            'exit_velocity': collision_result['exit_velocity'],
            'launch_angle': collision_result['launch_angle'],
            'spray_angle': self.hitter.spray_tendency,
            'distance': batted_ball_result.distance,
            'hang_time': batted_ball_result.flight_time,
            'peak_height': batted_ball_result.peak_height,
            'trajectory': batted_ball_result,
        }

    def simulate_at_bat(self, verbose: bool = False) -> AtBatResult:
        """
        Simulate a complete at-bat.

        Parameters
        ----------
        verbose : bool
            Whether to print play-by-play

        Returns
        -------
        AtBatResult
            Result of the at-bat
        """
        balls = 0
        strikes = 0
        pitches = []
        recent_pitch_types = []  # Track last 2 pitches for sequencing

        while balls < 4 and strikes < 3:
            # Select pitch with sequencing
            pitch_type = self.select_pitch_type((balls, strikes), recent_pitch_types)
            target_location = self.select_target_location((balls, strikes), pitch_type)

            # Simulate pitch
            pitch_data = self.simulate_pitch(pitch_type, target_location)
            pitches.append(pitch_data)

            # Track pitch type for sequencing (keep last 2)
            recent_pitch_types.append(pitch_type)
            if len(recent_pitch_types) > 2:
                recent_pitch_types.pop(0)

            if verbose:
                print(f"\n{balls}-{strikes} count")
                print(f"  Pitch: {pitch_type} @ ({pitch_data['final_location'][0]:.1f}\", "
                      f"{pitch_data['final_location'][1]:.1f}\") - "
                      f"{pitch_data['velocity_plate']:.1f} mph")

            # Hitter decides whether to swing
            should_swing = self.hitter.decide_to_swing(
                pitch_data['final_location'],
                pitch_data['is_strike'],
                (balls, strikes),
                pitch_velocity=pitch_data['velocity_plate'],
                pitch_type=pitch_data['pitch_type'],
            )

            if not should_swing:
                # Pitch taken
                if pitch_data['is_strike']:
                    strikes += 1
                    if verbose:
                        print(f"  Called strike {strikes}")
                else:
                    balls += 1
                    if verbose:
                        print(f"  Ball {balls}")
            else:
                # Swing
                if verbose:
                    print(f"  Swings...")

                contact_result = self.simulate_contact(pitch_data)

                if contact_result is None:
                    # Whiff
                    strikes += 1
                    if verbose:
                        print(f"  Swinging strike {strikes}")
                else:
                    # Contact made
                    if verbose:
                        print(f"  Contact! {contact_result['contact_quality']}")
                        print(f"    Exit velo: {contact_result['exit_velocity']:.1f} mph")
                        print(f"    Launch angle: {contact_result['launch_angle']:.1f}°")
                        print(f"    Distance: {contact_result['distance']:.1f} ft")

                    # Check if foul ball (enhanced logic)
                    launch_angle = contact_result['launch_angle']
                    spray_angle = contact_result['spray_angle']
                    contact_quality = contact_result['contact_quality']

                    is_foul = False

                    # Launch angle fouls (pop-ups behind or ground balls foul)
                    if launch_angle < -10 or launch_angle > 60:
                        is_foul = True

                    # Spray angle fouls (down the lines)
                    # Fair territory is roughly -45° to +45°
                    if abs(spray_angle) > 45:
                        is_foul = True

                    # Weak contact more likely to foul
                    if contact_quality == 'weak' and np.random.random() < 0.4:
                        is_foul = True

                    if is_foul:
                        # Foul ball
                        if strikes < 2:
                            strikes += 1
                        if verbose:
                            print(f"  FOUL BALL")
                    else:
                        # Ball in play
                        if verbose:
                            print(f"  BALL IN PLAY!")
                        return AtBatResult(
                            outcome='in_play',
                            pitches=pitches,
                            final_count=(balls, strikes),
                            batted_ball_result=contact_result,
                        )

        # At-bat concluded
        if strikes >= 3:
            outcome = 'strikeout'
        elif balls >= 4:
            outcome = 'walk'
        else:
            outcome = 'unknown'

        if verbose:
            print(f"\n{outcome.upper()}!")

        return AtBatResult(
            outcome=outcome,
            pitches=pitches,
            final_count=(balls, strikes),
        )
