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
        wind_speed: float = 0.0,
        wind_direction: float = 0.0,
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
        wind_speed : float
            Wind speed in mph (default: 0 = no wind)
            Positive = tailwind (toward outfield), negative = headwind
        wind_direction : float
            Wind direction in degrees (default: 0 = straight to center field)
            0° = tailwind, 90° = left-to-right crosswind, 180° = headwind
        fast_mode : bool
            If True, uses faster simulation with larger time steps (~2x speedup)
            Recommended for bulk simulations (1000+ at-bats)
        """
        self.pitcher = pitcher
        self.hitter = hitter
        self.altitude = altitude
        self.temperature = temperature
        self.humidity = humidity
        self.wind_speed = wind_speed
        self.wind_direction = wind_direction
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
        Select target location for pitch with realistic strike/ball distribution.

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
        
        # MLB strike rate is typically 62-65%. We need to intentionally target
        # outside the zone more often to achieve realistic ball rates.
        
        # Determine pitcher's intention for this pitch
        intention = self._determine_pitch_intention(balls, strikes, pitch_type)
        
        if intention == 'strike_looking':
            # Aim for easy strike (middle of zone)
            horizontal_target = np.random.normal(0, 2.0)  # Near center
            vertical_target = np.random.normal(30.0, 3.0)  # Middle of zone
            
        elif intention == 'strike_competitive':
            # Aim for strike but on edges for swing-and-miss
            # Strike zone: ±8.5" horizontal, 18"-42" vertical
            if np.random.random() < 0.5:
                # Target horizontal edges
                horizontal_target = np.random.choice([-6.0, 6.0]) + np.random.normal(0, 1.5)
                vertical_target = np.random.uniform(20.0, 40.0)
            else:
                # Target vertical edges  
                horizontal_target = np.random.normal(0, 3.0)
                vertical_target = np.random.choice([20.0, 40.0]) + np.random.normal(0, 1.5)
                
        elif intention == 'waste_chase':
            # Intentionally outside zone - chase pitch
            if np.random.random() < 0.4:
                # Low chase (most common)
                horizontal_target = np.random.normal(0, 4.0)
                vertical_target = np.random.uniform(10.0, 16.0)  # Below zone
            elif np.random.random() < 0.7:
                # Outside chase
                side = np.random.choice([-1, 1])
                horizontal_target = side * np.random.uniform(10.0, 15.0)  # Outside zone
                vertical_target = np.random.uniform(20.0, 38.0)
            else:
                # High chase
                horizontal_target = np.random.normal(0, 4.0)
                vertical_target = np.random.uniform(44.0, 50.0)  # Above zone
                
        elif intention == 'ball_intentional':
            # Intentionally throw ball (avoid contact in tough spots)
            if np.random.random() < 0.6:
                # Wide
                side = np.random.choice([-1, 1])
                horizontal_target = side * np.random.uniform(12.0, 18.0)
                vertical_target = np.random.uniform(25.0, 35.0)
            else:
                # Low
                horizontal_target = np.random.normal(0, 5.0)
                vertical_target = np.random.uniform(8.0, 15.0)
                
        else:  # 'strike_corner'
            # Target corners of strike zone
            corner_h = np.random.choice([-7.0, 7.0])
            corner_v = np.random.choice([20.0, 40.0])
            horizontal_target = corner_h + np.random.normal(0, 1.0)
            vertical_target = corner_v + np.random.normal(0, 1.0)

        return horizontal_target, vertical_target
    
    def _determine_pitch_intention(self, balls: int, strikes: int, pitch_type: str) -> str:
        """
        Determine pitcher's intention based on count and situation.
        
        Returns
        -------
        str
            One of: 'strike_looking', 'strike_competitive', 'strike_corner', 
                   'waste_chase', 'ball_intentional'
        """
        # Count-based probabilities for different intentions
        if balls == 0 and strikes == 0:
            # First pitch - often strike looking
            intentions = ['strike_looking', 'strike_competitive', 'strike_corner']
            probabilities = [0.50, 0.35, 0.15]
            
        elif balls >= 3:
            # Must throw strike
            intentions = ['strike_looking', 'strike_competitive']
            probabilities = [0.70, 0.30]
            
        elif strikes >= 2:
            # Can waste pitches
            intentions = ['waste_chase', 'strike_competitive', 'strike_corner']
            probabilities = [0.45, 0.35, 0.20]
            
        elif balls >= 2 and strikes <= 1:
            # Hitter's count - be more careful
            intentions = ['strike_competitive', 'ball_intentional', 'strike_corner']
            probabilities = [0.50, 0.30, 0.20]
            
        else:
            # Even count - mixed approach
            intentions = ['strike_competitive', 'strike_corner', 'waste_chase', 'ball_intentional']
            probabilities = [0.40, 0.25, 0.20, 0.15]
        
        # Adjust for pitcher's control rating
        # TODO: Add control rating to PitcherAttributes
        # For now, use average control (50/100 = 0.5) for all pitchers
        # This maintains game balance while we extend the attribute system
        control_factor = 0.5  # Average MLB control
        
        # Poor control pitchers throw more unintentional balls
        if control_factor < 0.5:
            # Increase chance of unintentional misses
            if 'ball_intentional' in intentions:
                idx = intentions.index('ball_intentional')
                probabilities[idx] *= 1.5
            else:
                intentions.append('ball_intentional')
                probabilities.append(0.15)
                
        # Normalize probabilities
        total = sum(probabilities)
        probabilities = [p / total for p in probabilities]
        
        return np.random.choice(intentions, p=probabilities)

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
        bat_speed_max = self.hitter.get_bat_speed_mph()
        
        # Add bat speed variance - not every swing is max effort
        # MLB hitters vary swing speed by ~5-10% based on pitch type, location, situation
        # Standard deviation of 4% creates realistic variance
        bat_speed_variance = 0.04 * bat_speed_max
        bat_speed = np.random.normal(bat_speed_max, bat_speed_variance)
        # Clamp to reasonable range (80-100% of max)
        bat_speed = np.clip(bat_speed, bat_speed_max * 0.80, bat_speed_max * 1.0)

        # Get contact point offset
        h_offset, v_offset = self.hitter.get_contact_point_offset(pitch_location)

        # Get swing timing error
        timing_error_ms = self.hitter.get_swing_timing_error_ms(pitch_velocity)

        # Timing error affects horizontal offset
        # More realistic approximation: 1 ms = ~0.1 inch offset (reduced from 0.5)
        timing_offset = timing_error_ms * 0.1

        # Total horizontal offset
        total_h_offset = h_offset + timing_offset

        # Calculate total offset for contact quality
        total_offset = np.sqrt(total_h_offset**2 + v_offset**2)
        
        # Calculate pitch location difficulty factor
        location_difficulty = self._calculate_location_difficulty(pitch_location)
        
        # Apply location difficulty to contact offset
        # Harder locations increase effective offset (worse contact)
        adjusted_offset = total_offset * (1.0 + location_difficulty)

        # Get actual pitch trajectory angle from pitch simulation
        # Use the actual downward angle from the pitch's trajectory at the plate
        # instead of assuming a constant 7° for all pitches (more realistic)
        pitch_result = pitch_data.get('result')
        if pitch_result and hasattr(pitch_result, 'plate_angle_vertical'):
            # Use the actual trajectory angle (positive = downward approach)
            pitch_trajectory_angle = pitch_result.plate_angle_vertical
        else:
            # Fallback to typical downward angle if not available
            pitch_trajectory_angle = 7.0

        # Contact made - simulate with physics
        collision_result = self.contact_model.full_collision(
            bat_speed_mph=bat_speed,
            pitch_speed_mph=pitch_velocity,
            bat_path_angle_deg=self.hitter.get_swing_path_angle_deg(
                pitch_location=pitch_location,
                pitch_type=pitch_type
            ),  # Sample swing path with realistic variance influenced by pitch
            pitch_trajectory_angle_deg=pitch_trajectory_angle,  # Use actual pitch trajectory angle
            vertical_contact_offset_inches=v_offset,
            horizontal_contact_offset_inches=total_h_offset,
            distance_from_sweet_spot_inches=adjusted_offset  # Use adjusted offset for contact quality
        )

        # Generate spray angle for this at-bat using hitter's spray tendency
        # MLB hitters have individual spray patterns - some pull heavily, others use all fields
        # Get hitter's spray tendency bias (pull vs. opposite field tendency)
        base_spray = self.hitter.attributes.get_spray_tendency_deg()
        # Add realistic spray variance around the hitter's tendency
        # Standard deviation of ~22° creates realistic MLB spray patterns
        spray_std_dev = 22.0  # degrees - realistic MLB spray variation
        spray_angle = np.random.normal(base_spray, spray_std_dev)
        # Clamp to reasonable bounds (-45° to +45°, foul lines)
        spray_angle = np.clip(spray_angle, -45.0, 45.0)

        # Simulate batted ball trajectory with environmental conditions including wind
        batted_ball_result = self.batted_ball_sim.simulate(
            exit_velocity=collision_result['exit_velocity'],
            launch_angle=collision_result['launch_angle'],
            spray_angle=spray_angle,  # Use generated spray angle, not fixed tendency
            backspin_rpm=collision_result['backspin_rpm'],
            altitude=self.altitude,
            temperature=self.temperature,
            wind_speed=self.wind_speed,
            wind_direction=self.wind_direction,
            fast_mode=self.fast_mode,
        )

        # Determine contact quality based on adjusted offset and location
        contact_quality = self._determine_contact_quality(adjusted_offset, pitch_location, pitch_data.get('is_strike', True))
        
        return {
            'contact_quality': contact_quality,
            'exit_velocity': collision_result['exit_velocity'],
            'launch_angle': collision_result['launch_angle'],
            'spray_angle': spray_angle,  # Return actual spray angle used
            'distance': batted_ball_result.distance,
            'hang_time': batted_ball_result.flight_time,
            'peak_height': batted_ball_result.peak_height,
            'trajectory': batted_ball_result,
            # Include collision physics data
            'collision_efficiency_q': collision_result.get('collision_efficiency_q', None),
            'contact_offset_total': collision_result.get('contact_offset_total', None),
            'sweet_spot_distance': collision_result.get('sweet_spot_distance', None),
            'backspin_rpm': collision_result['backspin_rpm'],
            'sidespin_rpm': collision_result['sidespin_rpm'],
        }
    
    def _calculate_location_difficulty(self, pitch_location: Tuple[float, float]) -> float:
        """
        Calculate difficulty multiplier based on pitch location.
        
        Parameters
        ----------
        pitch_location : tuple
            (horizontal_inches, vertical_inches) at plate
            
        Returns
        -------
        float
            Difficulty factor (0.0 = easy middle, 1.0+ = very difficult)
        """
        h_pos, v_pos = pitch_location
        
        # Strike zone boundaries: ±8.5" horizontal, 18"-42" vertical
        # Calculate distance from sweet spot (center of zone)
        sweet_spot_h = 0.0
        sweet_spot_v = 30.0  # Middle of strike zone
        
        h_distance = abs(h_pos - sweet_spot_h)
        v_distance = abs(v_pos - sweet_spot_v)
        
        # Distance from center affects difficulty
        horizontal_difficulty = h_distance / 8.5  # Normalized to zone edge
        vertical_difficulty = v_distance / 12.0   # Normalized to zone edge
        
        # Corners are especially difficult
        corner_factor = min(horizontal_difficulty * vertical_difficulty, 0.5)
        
        # Outside the zone is much more difficult
        out_of_zone_factor = 0.0
        if abs(h_pos) > 8.5:  # Outside horizontally
            out_of_zone_factor += (abs(h_pos) - 8.5) / 8.5  # Exponential difficulty
        if v_pos < 18.0:  # Below zone
            out_of_zone_factor += (18.0 - v_pos) / 10.0
        elif v_pos > 42.0:  # Above zone
            out_of_zone_factor += (v_pos - 42.0) / 10.0
            
        # Combine factors
        total_difficulty = horizontal_difficulty + vertical_difficulty + corner_factor + out_of_zone_factor
        
        # Cap at reasonable maximum
        return min(total_difficulty, 2.0)
    
    def _determine_contact_quality(self, offset: float, pitch_location: Tuple[float, float], is_strike: bool) -> str:
        """
        Determine contact quality based on offset and pitch location.
        
        Parameters
        ----------
        offset : float
            Contact point offset from sweet spot (inches)
        pitch_location : tuple
            (horizontal_inches, vertical_inches) at plate
        is_strike : bool
            Whether pitch was in strike zone
            
        Returns
        -------
        str
            Contact quality: 'solid', 'fair', or 'weak'
        """
        # Base thresholds
        solid_threshold = 0.75
        weak_threshold = 1.8
        
        # Adjust thresholds based on pitch location
        if not is_strike:
            # Swings at balls are much more likely to be weak
            solid_threshold *= 0.5  # Much harder to get solid contact
            weak_threshold *= 0.7   # More likely to be weak
            
        # Hitter ability affects thresholds
        # Derive contact ability from barrel accuracy in mm
        # Elite: ~5mm error, Average: ~15mm error, Poor: ~30mm error
        # Map to 0-1 scale: 5mm = 1.0, 15mm = 0.5, 30mm = 0.2
        barrel_error_mm = self.hitter.attributes.get_barrel_accuracy_mm()
        contact_ability = max(0.2, min(1.0, 1.0 - (barrel_error_mm - 5) / 25.0))
        solid_threshold *= (1.5 - contact_ability * 0.5)  # Elite hitters have lower threshold
        weak_threshold *= (1.3 - contact_ability * 0.3)
        
        if offset < solid_threshold:
            return 'solid'
        elif offset > weak_threshold:
            return 'weak'
        else:
            return 'fair'

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
            count_before_pitch = (balls, strikes)
            pitch_type = self.select_pitch_type(count_before_pitch, recent_pitch_types)
            target_location = self.select_target_location(count_before_pitch, pitch_type)

            # Simulate pitch
            pitch_data = self.simulate_pitch(pitch_type, target_location)

            # Annotate pitch with contextual data for downstream logging/debugging
            pitch_data['sequence_index'] = len(pitches) + 1
            pitch_data['count_before'] = count_before_pitch
            pitch_data['swing'] = False
            pitch_data['pitch_outcome'] = 'unknown'

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
                    pitch_data['pitch_outcome'] = 'called_strike'
                    if verbose:
                        print(f"  Called strike {strikes}")
                else:
                    balls += 1
                    pitch_data['pitch_outcome'] = 'ball'
                    if verbose:
                        print(f"  Ball {balls}")
            else:
                # Swing
                pitch_data['swing'] = True
                if verbose:
                    print(f"  Swings...")

                contact_result = self.simulate_contact(pitch_data)

                if contact_result is None:
                    # Whiff
                    strikes += 1
                    pitch_data['pitch_outcome'] = 'swinging_strike'
                    if verbose:
                        print(f"  Swinging strike {strikes}")
                else:
                    # Contact made
                    contact_summary = {
                        'contact_quality': contact_result['contact_quality'],
                        'exit_velocity': contact_result['exit_velocity'],
                        'launch_angle': contact_result['launch_angle'],
                        'distance': contact_result['distance'],
                        'hang_time': contact_result['hang_time'],
                    }
                    pitch_data['contact_summary'] = contact_summary
                    pitch_data['pitch_outcome'] = 'contact'

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
                        pitch_data['pitch_outcome'] = 'foul'
                        if strikes < 2:
                            strikes += 1
                        if verbose:
                            print(f"  FOUL BALL")
                    else:
                        # Ball in play
                        pitch_data['pitch_outcome'] = 'ball_in_play'
                        if verbose:
                            print(f"  BALL IN PLAY!")

                        pitch_data['count_after'] = (balls, strikes)
                        pitches.append(pitch_data)
                        return AtBatResult(
                            outcome='in_play',
                            pitches=pitches,
                            final_count=(balls, strikes),
                            batted_ball_result=contact_result,
                        )

            pitch_data['count_after'] = (balls, strikes)
            pitches.append(pitch_data)

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
