"""
Baseball fielding mechanics and physics simulation.

Models individual fielder attributes, reaction times, movement physics,
catching mechanics, and throwing physics for realistic defensive play simulation.
"""

import numpy as np
from typing import Dict, List, Tuple, Optional, Union
from .constants import (
    # Fielding attributes
    FIELDER_SPRINT_SPEED_MIN, FIELDER_SPRINT_SPEED_AVG, 
    FIELDER_SPRINT_SPEED_ELITE, FIELDER_SPRINT_SPEED_MAX,
    FIELDER_ACCELERATION_MIN, FIELDER_ACCELERATION_AVG,
    FIELDER_ACCELERATION_ELITE, FIELDER_ACCELERATION_MAX,
    FIELDER_REACTION_TIME_MIN, FIELDER_REACTION_TIME_AVG,
    FIELDER_REACTION_TIME_POOR, FIELDER_REACTION_TIME_MAX,
    # Throwing attributes
    INFIELDER_THROW_VELOCITY_MIN, INFIELDER_THROW_VELOCITY_AVG,
    INFIELDER_THROW_VELOCITY_ELITE, INFIELDER_THROW_VELOCITY_MAX,
    OUTFIELDER_THROW_VELOCITY_MIN, OUTFIELDER_THROW_VELOCITY_AVG,
    OUTFIELDER_THROW_VELOCITY_ELITE, OUTFIELDER_THROW_VELOCITY_MAX,
    INFIELDER_TRANSFER_TIME_MIN, INFIELDER_TRANSFER_TIME_AVG,
    INFIELDER_TRANSFER_TIME_POOR, INFIELDER_TRANSFER_TIME_MAX,
    OUTFIELDER_TRANSFER_TIME_MIN, OUTFIELDER_TRANSFER_TIME_AVG,
    OUTFIELDER_TRANSFER_TIME_POOR, OUTFIELDER_TRANSFER_TIME_MAX,
    THROWING_ACCURACY_ELITE, THROWING_ACCURACY_AVG,
    THROWING_ACCURACY_POOR, THROWING_ACCURACY_TERRIBLE,
    # Attribute rating scales
    FIELDING_SPEED_RATING_MIN, FIELDING_SPEED_RATING_AVG,
    FIELDING_SPEED_RATING_ELITE, FIELDING_SPEED_RATING_MAX,
    FIELDING_REACTION_RATING_MIN, FIELDING_REACTION_RATING_AVG,
    FIELDING_REACTION_RATING_ELITE, FIELDING_REACTION_RATING_MAX,
    FIELDING_ARM_RATING_MIN, FIELDING_ARM_RATING_AVG,
    FIELDING_ARM_RATING_ELITE, FIELDING_ARM_RATING_MAX,
    FIELDING_ACCURACY_RATING_MIN, FIELDING_ACCURACY_RATING_AVG,
    FIELDING_ACCURACY_RATING_ELITE, FIELDING_ACCURACY_RATING_MAX,
    FIELDING_RANGE_ELITE, FIELDING_RANGE_AVG, FIELDING_RANGE_POOR,
    # Physics constants
    GRAVITY, FEET_TO_METERS, METERS_TO_FEET, MPH_TO_MS, MS_TO_MPH,
    DEG_TO_RAD, RAD_TO_DEG,
    # Play outcome tolerances
    CLOSE_PLAY_TOLERANCE, SAFE_RUNNER_BIAS,
    TAG_APPLICATION_TIME, TAG_AVOIDANCE_SUCCESS_RATE,
)
from .field_layout import FieldPosition, FieldLayout
from .attributes import FielderAttributes


class FieldingResult:
    """Result of a fielding attempt."""

    def __init__(self,
                 success: bool,
                 fielder_arrival_time: float,
                 ball_arrival_time: float,
                 catch_position: FieldPosition,
                 fielder_name: str,
                 fielder_position: str = None,
                 failure_reason: str = None,
                 is_error: bool = False):
        """
        Initialize fielding result.

        Parameters
        ----------
        success : bool
            Whether the fielding attempt was successful
        fielder_arrival_time : float
            Time when fielder reached the ball (seconds)
        ball_arrival_time : float
            Time when ball reached the position (seconds)
        catch_position : FieldPosition
            Position where ball was fielded
        fielder_name : str
            Name of the fielder
        fielder_position : str, optional
            Position key of the fielder (e.g., 'shortstop', 'left_field')
        failure_reason : str, optional
            Reason for fielding failure if not successful:
            - None: success=True (no failure)
        is_error : bool, optional
            Whether this was a fielding error (dropped ball with positive time margin)
            - 'TOO_SLOW': fielder arrived after ball landed
            - 'DROP_ERROR': fielder arrived in time but failed to catch
        """
        self.success = success
        self.fielder_arrival_time = fielder_arrival_time
        self.ball_arrival_time = ball_arrival_time
        self.catch_position = catch_position
        self.fielder_name = fielder_name
        self.fielder_position = fielder_position
        self.failure_reason = failure_reason
        self.is_error = is_error
        self.margin = ball_arrival_time - fielder_arrival_time  # Positive = made it


class ThrowResult:
    """Result of a throwing attempt."""
    
    def __init__(self,
                 throw_velocity: float,
                 flight_time: float,
                 accuracy_error: Tuple[float, float],
                 target_position: FieldPosition,
                 release_time: float):
        """
        Initialize throw result.
        
        Parameters
        ----------
        throw_velocity : float
            Velocity of throw in mph
        flight_time : float
            Time for ball to reach target in seconds
        accuracy_error : tuple
            (horizontal_error, vertical_error) in inches from target
        target_position : FieldPosition
            Intended target position
        release_time : float
            Time when ball was released
        """
        self.throw_velocity = throw_velocity
        self.flight_time = flight_time
        self.accuracy_error = accuracy_error
        self.target_position = target_position
        self.release_time = release_time
        self.arrival_time = release_time + flight_time


class Fielder:
    """
    Represents a defensive player with physical attributes and fielding mechanics.

    Uses physics-first attribute system (0-100,000 scale) mapped to real physical units.
    All attributes are defined via FielderAttributes object which provides:
    - Sprint speed (fps)
    - Acceleration (fps²)
    - Reaction time (seconds)
    - Arm strength (mph)
    - Throwing accuracy (feet)
    - Transfer quickness (seconds)
    - Fielding range and route efficiency
    """

    def __init__(self,
                 name: str,
                 position: str,
                 attributes: FielderAttributes,
                 current_position: Optional[FieldPosition] = None):
        """
        Initialize fielder with physics-first attributes.

        Parameters
        ----------
        name : str
            Fielder's name/identifier
        position : str
            Position type ('infield', 'outfield', 'catcher')
        attributes : FielderAttributes
            Physics-first attribute system (0-100,000 scale)
            Provides all fielding capabilities mapped to physical units
        current_position : FieldPosition, optional
            Current field position
        """
        self.name = name
        self.position = position.lower()
        self.attributes = attributes

        # Position and state
        self.current_position = current_position
        self.is_infielder = position.lower() in ['infield', 'catcher']

        # Movement state
        self.current_velocity = np.array([0.0, 0.0, 0.0])  # ft/s
        self.is_moving = False
        self.target_position = None
    
    def get_acceleration_fps2(self) -> float:
        """Get acceleration in feet per second squared."""
        return self.attributes.get_acceleration_fps2()

    def get_sprint_speed_fps_statcast(self) -> float:
        """Get top sprint speed in fps using Statcast-calibrated values."""
        return self.attributes.get_top_sprint_speed_fps()

    def get_sprint_speed_fps(self) -> float:
        """Get sprint speed in fps (alias for get_sprint_speed_fps_statcast for compatibility)."""
        return self.get_sprint_speed_fps_statcast()

    def get_first_step_time(self) -> float:
        """Get first step/reaction time in seconds."""
        return self.attributes.get_reaction_time_s()

    def get_reaction_time_seconds(self) -> float:
        """Get reaction time in seconds (alias for get_first_step_time for compatibility)."""
        return self.get_first_step_time()

    def get_route_efficiency(self) -> float:
        """Get route efficiency percentage (0.0-1.0)."""
        return self.attributes.get_route_efficiency_pct()
    
    def calculate_directional_speed_penalty(self, movement_direction: np.ndarray) -> float:
        """
        Calculate speed penalty based on movement direction.
        
        2025-11-26: Updated to use player-specific RANGE_BACK and RANGE_IN modifiers
        instead of fixed constants. This allows for differentiation between players
        like Pete Crow-Armstrong (+15 back OAA) vs Juan Soto (-5 back OAA).
        
        Returns
        -------
        float
            Speed multiplier (0.85 to 1.15) based on direction and player ability
        """
        from .constants import (
            FORWARD_MOVEMENT_PENALTY,
            LATERAL_MOVEMENT_PENALTY,
            BACKWARD_MOVEMENT_PENALTY
        )
        
        # Normalize direction vector
        direction_mag = np.linalg.norm(movement_direction[:2])  # Only consider x,y
        if direction_mag < 1e-6:
            return FORWARD_MOVEMENT_PENALTY
        
        direction_unit = movement_direction[:2] / direction_mag
        
        # Forward is positive y direction in our coordinate system
        forward_component = direction_unit[1]
        
        # Determine primary direction
        angle = np.arctan2(direction_unit[0], direction_unit[1])  # angle from forward
        angle_deg = np.abs(np.degrees(angle))
        
        if angle_deg <= 45:
            # Forward movement - use player's RANGE_IN modifier
            # Elite players coming in can be faster than base constant
            base_penalty = FORWARD_MOVEMENT_PENALTY  # 1.0
            player_modifier = self.attributes.get_range_in_modifier()  # 0.90 to 1.12
            # Blend: base is 1.0, player can modify it ± ~10%
            return base_penalty * player_modifier
        elif angle_deg <= 135:
            # Lateral movement - use average of back and in modifiers
            # Lateral is less affected by directional ability
            back_mod = self.attributes.get_range_back_modifier()
            in_mod = self.attributes.get_range_in_modifier()
            avg_directional = (back_mod + in_mod) / 2.0
            # Blend with base lateral penalty (0.97)
            return LATERAL_MOVEMENT_PENALTY * avg_directional
        else:
            # Backward movement - use player's RANGE_BACK modifier
            # This is where player differences are most pronounced
            # Elite: 1.0-1.10, Poor: 0.85-0.93
            base_penalty = BACKWARD_MOVEMENT_PENALTY  # 0.93
            player_modifier = self.attributes.get_range_back_modifier()  # 0.85 to 1.15
            
            # The player modifier already encodes their ability relative to average
            # Elite (85k+): modifier > 1.0 means they're BETTER going back than average
            # Poor (15k-): modifier < 1.0 means they're WORSE going back than average
            # 
            # Combined with base penalty:
            # - Elite player (modifier 1.10): 0.93 * 1.10 = 1.02 (slightly FASTER going back!)
            # - Average player (modifier 1.0): 0.93 * 1.0 = 0.93 (standard penalty)
            # - Poor player (modifier 0.85): 0.93 * 0.85 = 0.79 (much slower going back)
            return base_penalty * player_modifier
    
    def calculate_optimal_intercept_point(self, ball_trajectory_data: dict,
                                        current_time: float) -> np.ndarray:
        """
        Calculate optimal intercept point using advanced trajectory prediction.

        Uses iterative approach to find the point where fielder and ball
        arrive simultaneously, accounting for fielder's movement capabilities.

        COORDINATE SYSTEM: ball_trajectory_data is expected to be in FIELD COORDINATES
        (from play_simulation._create_trajectory_data_for_pursuit), not trajectory coords.
        - X-axis: Lateral (positive = RIGHT field)
        - Y-axis: Forward (positive = toward CENTER field)
        - Z-axis: Vertical (positive = up)
        """
        from .constants import (
            TRAJECTORY_PREDICTION_SAMPLES,
            INTERCEPT_CONVERGENCE_TOLERANCE,
            MAX_PURSUIT_DISTANCE
        )
        
        ball_pos = ball_trajectory_data['position']
        ball_vel = ball_trajectory_data['velocity']
        ball_time = ball_trajectory_data['time']
        
        # Find current ball state
        current_idx = np.argmin(np.abs(ball_time - current_time))
        if current_idx >= len(ball_time) - 1:
            return ball_pos[-1][:2]  # Ball already landed
        
        # Sample future trajectory points
        future_indices = np.linspace(current_idx, len(ball_time)-1, 
                                   min(TRAJECTORY_PREDICTION_SAMPLES, len(ball_time) - current_idx))
        
        best_intercept = None
        best_margin = float('inf')
        
        for idx in future_indices:
            idx = int(idx)
            if idx >= len(ball_time):
                continue
                
            # Future ball position and time
            future_ball_pos = ball_pos[idx]
            future_time = ball_time[idx]
            
            # Skip if ball is too high (still climbing significantly)
            if future_ball_pos[2] > 15.0 and idx < len(ball_time) - 5:
                continue
                
            # Calculate distance to intercept point
            intercept_distance = np.sqrt(
                (future_ball_pos[0] - self.current_position.x)**2 +
                (future_ball_pos[1] - self.current_position.y)**2
            )
            
            # Skip if too far away
            if intercept_distance > MAX_PURSUIT_DISTANCE:
                continue
            
            # Calculate fielder time to reach this point
            intercept_pos = FieldPosition(future_ball_pos[0], future_ball_pos[1], 0)
            fielder_time = self.calculate_time_to_position(intercept_pos)
            total_fielder_time = current_time + fielder_time
            
            # Time margin (positive = fielder arrives first)
            time_margin = future_time - total_fielder_time
            
            # Prefer intercepts where fielder arrives slightly early
            if -0.5 <= time_margin <= 0.2 and abs(time_margin) < abs(best_margin):
                best_margin = time_margin
                best_intercept = future_ball_pos[:2]
        
        # If no good intercept found, try final landing position
        if best_intercept is None:
            return ball_pos[-1][:2]
            
        return best_intercept
    
    def calculate_oac_pursuit_target_advanced(self, ball_trajectory_data: dict,
                                            current_time: float) -> np.ndarray:
        """
        Advanced Optical Acceleration Cancellation pursuit target calculation.

        Implements research-based OAC algorithm that maintains constant
        bearing angle to the ball through dynamic positioning.

        COORDINATE SYSTEM: ball_trajectory_data is expected to be in FIELD COORDINATES
        (from play_simulation._create_trajectory_data_for_pursuit), not trajectory coords.
        - X-axis: Lateral (positive = RIGHT field)
        - Y-axis: Forward (positive = toward CENTER field)
        - Z-axis: Vertical (positive = up)
        """
        from .constants import (
            OAC_CONTROL_GAIN,
            OAC_ANGULAR_THRESHOLD,
            PURSUIT_PREDICTION_TIME,
            VELOCITY_PREDICTION_WEIGHT
        )
        
        ball_pos = ball_trajectory_data['position']
        ball_vel = ball_trajectory_data['velocity']
        ball_time = ball_trajectory_data['time']
        
        # Find current and future ball state
        current_idx = np.argmin(np.abs(ball_time - current_time))
        future_time = current_time + PURSUIT_PREDICTION_TIME
        future_idx = np.argmin(np.abs(ball_time - future_time))
        
        if current_idx >= len(ball_time) - 1:
            return ball_pos[-1][:2]
        
        # Current ball position and velocity
        current_ball_pos = ball_pos[current_idx]
        current_ball_vel = ball_vel[current_idx]
        
        # Predict future ball position using velocity
        dt = PURSUIT_PREDICTION_TIME
        predicted_pos = current_ball_pos + current_ball_vel * dt
        
        # Blend prediction with actual trajectory if available
        if future_idx < len(ball_time):
            actual_future_pos = ball_pos[future_idx]
            blended_pos = (VELOCITY_PREDICTION_WEIGHT * predicted_pos + 
                          (1 - VELOCITY_PREDICTION_WEIGHT) * actual_future_pos)
        else:
            blended_pos = predicted_pos
        
        # Calculate bearing angle and rate of change
        fielder_pos = np.array([self.current_position.x, self.current_position.y])
        current_bearing = np.arctan2(current_ball_pos[1] - fielder_pos[1],
                                   current_ball_pos[0] - fielder_pos[0])
        future_bearing = np.arctan2(blended_pos[1] - fielder_pos[1],
                                   blended_pos[0] - fielder_pos[0])
        
        bearing_rate = (future_bearing - current_bearing) / dt
        
        # OAC control: adjust position to minimize bearing rate
        if abs(bearing_rate) > OAC_ANGULAR_THRESHOLD:
            # Calculate correction vector
            correction_magnitude = OAC_CONTROL_GAIN * abs(bearing_rate)
            correction_angle = current_bearing + np.pi/2  # Perpendicular to bearing
            
            if bearing_rate > 0:
                correction_angle += np.pi  # Reverse direction
            
            correction_vector = correction_magnitude * np.array([
                np.cos(correction_angle),
                np.sin(correction_angle)
            ])
            
            # Apply correction to target position
            target_pos = blended_pos[:2] + correction_vector
        else:
            target_pos = blended_pos[:2]
        
        return target_pos
    
    def calculate_optimal_route(self, target_position: FieldPosition,
                               ball_trajectory_data: dict = None) -> tuple:
        """
        Calculate optimal route to target considering obstacles and efficiency.

        COORDINATE SYSTEM: ball_trajectory_data (if provided) is expected to be in FIELD COORDINATES
        (from play_simulation._create_trajectory_data_for_pursuit), not trajectory coords.

        Returns (route_positions, total_time, route_efficiency)
        """
        from .constants import (
            ROUTE_OPTIMIZATION_SAMPLES,
            PURSUIT_ANGLE_PREFERENCE,
            ANTICIPATION_BONUS_TIME
        )
        
        if self.current_position is None:
            raise ValueError("Current position not set")
        
        start_pos = np.array([self.current_position.x, self.current_position.y])
        target_pos = np.array([target_position.x, target_position.y])
        
        # Direct route as baseline
        direct_distance = np.linalg.norm(target_pos - start_pos)
        direct_time = self.calculate_time_to_position(target_position)
        
        # If ball trajectory available, optimize approach angle
        if ball_trajectory_data is not None:
            ball_pos = ball_trajectory_data['position']
            ball_vel = ball_trajectory_data['velocity']
            
            # Calculate ball's expected direction at intercept
            if len(ball_pos) > 1:
                ball_direction = ball_vel[-5:].mean(axis=0)[:2]  # Average recent velocity
                ball_direction_norm = np.linalg.norm(ball_direction)
                
                if ball_direction_norm > 1e-6:
                    ball_unit_dir = ball_direction / ball_direction_norm
                    
                    # Preferred approach angle (slightly to the side)
                    preferred_angle = np.radians(PURSUIT_ANGLE_PREFERENCE)
                    
                    # Calculate approach vectors
                    approach_angles = [preferred_angle, -preferred_angle, 0]
                    best_route = None
                    best_time = float('inf')
                    
                    for angle in approach_angles:
                        # Rotate ball direction by angle
                        cos_a, sin_a = np.cos(angle), np.sin(angle)
                        rotated_dir = np.array([
                            ball_unit_dir[0] * cos_a - ball_unit_dir[1] * sin_a,
                            ball_unit_dir[0] * sin_a + ball_unit_dir[1] * cos_a
                        ])
                        
                        # Approach point slightly offset from target
                        approach_distance = min(10.0, direct_distance * 0.2)
                        approach_point = target_pos - rotated_dir * approach_distance
                        
                        # Calculate route time via approach point
                        approach_pos = FieldPosition(approach_point[0], approach_point[1], 0)
                        
                        try:
                            time_to_approach = self.calculate_time_to_position(approach_pos)
                            
                            # Update position temporarily to calculate second leg
                            old_pos = self.current_position
                            self.current_position = approach_pos
                            time_approach_to_target = self.calculate_time_to_position(target_position)
                            self.current_position = old_pos
                            
                            total_time = time_to_approach + time_approach_to_target
                            
                            # Add anticipation bonus for good angles
                            if abs(angle) == preferred_angle:
                                total_time -= ANTICIPATION_BONUS_TIME
                            
                            if total_time < best_time:
                                best_time = total_time
                                best_route = [start_pos, approach_point, target_pos]
                        
                        except ValueError:
                            continue
                    
                    if best_route is not None:
                        route_efficiency = direct_time / best_time if best_time > 0 else 1.0
                        return best_route, best_time, route_efficiency
        
        # Fallback to direct route
        return [start_pos, target_pos], direct_time, 1.0
    
    def get_anticipation_adjustment(self, ball_trajectory_data: dict, 
                                  batter_tendencies: dict = None) -> np.ndarray:
        """
        Calculate anticipation-based position adjustment before ball contact.
        
        Uses batter tendencies and pitch context to pre-position optimally.
        """
        from .constants import (
            OUTFIELD_DEPTH_ADJUSTMENT_FAST,
            OUTFIELD_DEPTH_ADJUSTMENT_POWER,
            DEFENSIVE_SHIFT_THRESHOLD
        )
        
        if self.current_position is None:
            return np.array([0.0, 0.0])
        
        adjustment = np.array([0.0, 0.0])
        
        # Use batter tendencies if available
        if batter_tendencies:
            # Pull/opposite field tendency
            if 'spray_tendency' in batter_tendencies:
                spray = batter_tendencies['spray_tendency']
                if abs(spray) > DEFENSIVE_SHIFT_THRESHOLD:
                    # Shift toward pull side
                    shift_amount = 15.0 * (spray / 45.0)  # Max 15 ft shift
                    adjustment[0] += shift_amount
            
            # Power vs contact adjustments
            if 'power_rating' in batter_tendencies:
                power = batter_tendencies['power_rating']
                if power > 70 and not self.is_infielder:  # High power, outfielder
                    # Move back for power hitters
                    adjustment[1] += OUTFIELD_DEPTH_ADJUSTMENT_POWER
            
            if 'speed_rating' in batter_tendencies:
                speed = batter_tendencies['speed_rating']
                if speed > 80 and self.is_infielder:  # Fast runner, infielder
                    # Move in slightly for fast runners
                    adjustment[1] -= 5.0
        
        return adjustment
    
    def get_throw_velocity_mph(self) -> float:
        """Get throwing velocity in mph."""
        return self.attributes.get_arm_strength_mph()

    def get_transfer_time_seconds(self) -> float:
        """Get transfer time (glove to hand) in seconds."""
        return self.attributes.get_transfer_time_s()

    def get_throwing_accuracy_std_degrees(self) -> float:
        """Get throwing accuracy error in degrees."""
        # Get error in feet, convert to angular error
        # For typical throw distance of 90 ft, 1 ft error ≈ 0.64 degrees
        error_ft = self.attributes.get_arm_accuracy_sigma_ft()
        avg_throw_distance_ft = 90.0
        std_deg = np.degrees(np.arctan(error_ft / avg_throw_distance_ft))
        return std_deg

    def get_effective_range_multiplier(self) -> float:
        """Get range multiplier for effective fielding time."""
        # Range multiplier improves effective movement speed
        # Higher range = can cover more ground in same time
        route_efficiency = self.attributes.get_route_efficiency_pct()
        # Convert route efficiency (0.85-0.98) to range multiplier (0.8-1.25)
        # Better routes = effectively faster
        # NERFED 2025-11-19: Reduced multipliers to prevent vacuum-cleaner defense
        if route_efficiency >= 0.92:
            return 1.08  # Elite range (was 1.15)
        elif route_efficiency >= 0.88:
            return 1.03  # Above average (was 1.05)
        else:
            return 0.95  # Below average
    
    def calculate_time_to_position(self, target: FieldPosition) -> float:
        """
        Calculate time required to reach a target position using simplified empirical model.

        Uses distance-based effective speeds calibrated to real fielding plays:
        - Short distances (< 30ft): Quick burst speed (~75-85% of max)
        - Medium distances (30-60ft): Acceleration phase (~80-90% of max)
        - Long distances (> 60ft): Near full sprint with route efficiency

        FIELDING REALISM ENHANCEMENTS (Pass #2):
        - Added stochastic route efficiency variance (±2% noise)
        - Added reaction time jitter (~±50ms)
        - Integrated Statcast Jump metric (feet covered in right direction in first 3s)

        JUMP INTEGRATION (2025-11-26):
        Jump represents "feet covered in the right direction in the first 3 seconds".
        Elite fielders (+4 ft) effectively start closer to the ball because they cover
        more ground early. Poor fielders (-6 ft) effectively start further away.
        
        Implementation: Jump is converted to a distance credit applied to medium/long plays.
        Short plays (<30ft) don't benefit as much from Jump since there's no pursuit.

        Parameters
        ----------
        target : FieldPosition
            Target position to reach

        Returns
        -------
        float
            Time in seconds to reach position (includes reaction/first-step time)
        """
        if self.current_position is None:
            raise ValueError("Current position not set")

        # Calculate distance and direction to target
        distance = self.current_position.distance_to(target)
        movement_vector = np.array([
            target.x - self.current_position.x,
            target.y - self.current_position.y,
            0.0
        ])

        # Get base physical attributes
        max_speed = self.get_sprint_speed_fps_statcast()
        first_step_time = self.get_first_step_time()

        # FIELDING REALISM: Add reaction time jitter (~±50ms)
        reaction_jitter = np.random.normal(0, 0.05)  # ~±50ms std dev
        first_step_time = max(0.0, first_step_time + reaction_jitter)

        # STATCAST JUMP: Get fielder's Jump metric (feet above/below average in first 3s)
        # This replaces the random "jump quality" roll with actual player data
        # Jump ranges from ~-6 ft (poor) to +7 ft (elite)
        jump_feet = self.attributes.get_jump_feet()
        
        # Add stochastic variance to Jump (~±1 ft per play for variability)
        jump_variance = np.random.normal(0, 1.0)  # ±1 ft std dev
        effective_jump_feet = jump_feet + jump_variance

        # Apply directional speed penalty
        direction_penalty = self.calculate_directional_speed_penalty(movement_vector)
        directional_max_speed = max_speed * direction_penalty

        # Calculate effective speed based on distance
        # MLB fielders can sprint at near-max speed for defensive plays
        if distance < 30.0:
            # Short burst: 88-94% of max speed
            # Jump has minimal effect on short plays - fielder is already close
            speed_percentage = 0.88 + (distance / 30.0) * 0.06  # 88% at 0ft, 94% at 30ft
            effective_speed = directional_max_speed * speed_percentage
            route_penalty = 1.0  # No route inefficiency on short plays
            # Jump credit: minimal on short plays (scaled by distance/30)
            jump_distance_credit = effective_jump_feet * (distance / 30.0) * 0.3
        elif distance < 60.0:
            # Medium range: 94-98% of max speed
            normalized_dist = (distance - 30.0) / 30.0  # 0 to 1
            speed_percentage = 0.94 + normalized_dist * 0.04  # 94% to 98%
            effective_speed = directional_max_speed * speed_percentage
            # Minor route inefficiency
            route_efficiency_raw = self.get_route_efficiency()
            route_efficiency = route_efficiency_raw if route_efficiency_raw <= 1.0 else route_efficiency_raw / 100.0

            # FIELDING REALISM: Add stochastic variance (±2% noise)
            route_eff_variance = np.random.normal(0, 0.02)  # ±2% noise
            route_efficiency = np.clip(route_efficiency + route_eff_variance, 0.85, 0.99)

            # REBALANCED 2025-01-XX: Route efficiency more impactful on medium-range plays
            route_penalty = 1.0 + (1.0 - route_efficiency) * 0.5
            
            # Jump credit: moderate on medium plays (full effect)
            jump_distance_credit = effective_jump_feet
        else:
            # Long range: 98-100% of max speed
            normalized_dist = min((distance - 60.0) / 60.0, 1.0)  # 0 to 1, capped
            speed_percentage = 0.98 + normalized_dist * 0.02  # 98% to 100%
            effective_speed = directional_max_speed * speed_percentage
            # Reduced route efficiency penalty
            route_efficiency_raw = self.get_route_efficiency()
            route_efficiency = route_efficiency_raw if route_efficiency_raw <= 1.0 else route_efficiency_raw / 100.0

            # FIELDING REALISM: Add stochastic variance (±2% noise)
            route_eff_variance = np.random.normal(0, 0.02)  # ±2% noise
            route_efficiency = np.clip(route_efficiency + route_eff_variance, 0.85, 0.99)

            # REBALANCED 2025-01-XX: Route efficiency more impactful on long-range plays
            route_penalty = 1.0 + (1.0 - route_efficiency) * 0.35
            
            # Jump credit: full effect on long plays
            # Long plays benefit most from good Jump (early direction, burst)
            jump_distance_credit = effective_jump_feet

        # Calculate effective distance (route penalty increases, jump credit decreases)
        # Jump credit reduces effective distance (positive jump = less distance to cover)
        effective_distance = max(1.0, distance * route_penalty - jump_distance_credit)
        
        # Calculate movement time
        movement_time = effective_distance / effective_speed

        # Total time = first step + movement
        total_time = first_step_time + movement_time
        return total_time

    def calculate_effective_time_to_position(self, target: FieldPosition) -> float:
        """Calculate time to reach target after accounting for fielder range skill."""
        if self.current_position is None:
            raise ValueError("Current position not set")

        # Get base time (already includes first-step/reaction time)
        base_time = self.calculate_time_to_position(target)

        # Apply range multiplier to improve/reduce effective time
        # Higher range = faster effective movement
        range_multiplier = self.get_effective_range_multiplier()

        # Separate first-step from movement to apply range only to movement
        first_step_time = self.get_first_step_time()
        movement_time = max(base_time - first_step_time, 0.0)

        # Range affects movement efficiency
        adjusted_movement = movement_time / range_multiplier

        return first_step_time + adjusted_movement
    
    def can_reach_ball(self, ball_position: FieldPosition, ball_arrival_time: float) -> bool:
        """
        Determine if fielder can reach ball before it arrives at position.
        
        Parameters
        ----------
        ball_position : FieldPosition
            Position where ball will arrive
        ball_arrival_time : float
            Time when ball will arrive (seconds from contact)
            
        Returns
        -------
        bool
            True if fielder can reach ball in time
        """
        effective_time = self.calculate_effective_time_to_position(ball_position)

        return effective_time <= ball_arrival_time
    
    def calculate_catch_probability(self, ball_position: FieldPosition,
                                  ball_arrival_time: float) -> float:
        """
        Calculate catch probability using physics-based probabilistic model.

        Based on Statcast research incorporating:
        - Distance to ball
        - Opportunity time (time available)
        - Movement direction (backward penalty)
        - Fielder secure probability (hands)

        Parameters
        ----------
        ball_position : FieldPosition
            Position where ball will arrive
        ball_arrival_time : float
            Time when ball arrives

        Returns
        -------
        float
            Probability of successful catch (0.0 to 1.0)
        """
        from .constants import (
            CATCH_PROB_BASE,
            CATCH_PROB_DISTANCE_PENALTY,
            CATCH_PROB_TIME_BONUS,
            CATCH_PROB_BACKWARD_PENALTY,
            CATCH_PROB_MIN
        )

        if self.current_position is None:
            return 0.0

        # Calculate horizontal distance and movement direction (fielders move on the ground)
        # Create ground position under the ball for accurate fielder movement calculation
        ground_position = FieldPosition(ball_position.x, ball_position.y, 0.0)
        distance = self.current_position.horizontal_distance_to(ball_position)
        movement_vector = np.array([
            ball_position.x - self.current_position.x,
            ball_position.y - self.current_position.y,
            0.0
        ])

        # Calculate fielder time to reach ground position under ball
        fielder_time = self.calculate_effective_time_to_position(ground_position)

        # Use physics-based secure probability (hands rating)
        base_secure_prob = self.attributes.get_fielding_secure_prob()

        # Catch probability model calibrated for MLB-realistic hit rates
        # Time margin is the key factor
        time_margin = ball_arrival_time - fielder_time

        # SAFETY CHECK: Impossible catches for fielders arriving extremely late
        # If fielder is more than 1 second late, catch is impossible (ball already dropped/rolled)
        if time_margin < -1.0:
            return 0.0

        # Time-based catch probability bands (tuned for MLB BABIP of ~.300)
        # MLB fielders convert ~70% of balls in play into outs
        # These base probabilities get multiplied by secure_prob (~0.92) and other penalties
        #
        # IMPORTANT: Negative time margin means fielder arrives AFTER the ball lands.
        # For fly balls, this should result in a drop (ball already on ground).
        # Only allow diving/stretching catches for very small negative margins (< -0.15s).
        #
        # TUNING: High base probabilities to account for compounding penalties
        # Penalties: hands (~0.92) * distance (0.85-0.96) * backward (0.93 if applicable)
        # Worst case: 0.92 * 0.85 * 0.93 = 0.727x multiplier
        # Best case (short distance, moving in): 0.92 = 0.92x multiplier
        # Target: ~9 runs/9 innings and ~15-18 hits/9 innings (not 57 hits!)
        # NERFED 2025-11-19: Adjusted time margins to reduce "vacuum cleaner" catches
        # REBALANCED 2025-01-XX: Further adjusted to increase BABIP from 0.248 to ~0.300
        # Problem: Too many plays had 0.95+ catch probability (45.6% of plays)
        # Solution: Lower base probabilities and add intermediate tier at 0.5s
        #
        # 2025-11-26: Added player-specific catch bonuses from Statcast Catch Probability
        # - CATCH_ELITE: Bonus for 5-star plays (time_margin < -0.15)
        # - CATCH_DIFFICULT: Bonus for 3-4 star plays (time_margin -0.15 to 0.2)
        if time_margin >= 1.0:
            # Fielder arrives well ahead (1.0+s early) - very routine play
            # Standing and waiting, minimal chance of error
            # Reduced from 0.99 to 0.95 - even routine plays have ~5% variance
            return 0.95  # 95% success rate (was 0.99)
        elif time_margin >= 0.5:
            # Fielder arrives comfortably (0.5-1.0s early) - routine play
            # NEW TIER: Bridge between "waiting" and "running catch"
            probability = 0.92  # After worst penalties: 0.92 * 0.727 = 0.67 (67%)
        elif time_margin >= 0.2:
            # Fielder arrives with time (0.2-0.5s early) - solid play
            # Reduced from 0.98 to 0.88 for more realistic variance
            probability = 0.88  # After worst penalties: 0.88 * 0.727 = 0.64 (64%)
            # Apply CATCH_DIFFICULT bonus for 3-4 star difficulty plays
            catch_difficult_bonus = self.attributes.get_catch_difficult_bonus()
            probability = min(1.0, probability + catch_difficult_bonus)  # Up to +0.20 for elite
        elif time_margin >= 0.0:
            # Fielder arrives on time (0-0.2s early) - difficult running catch
            # In reality, arriving exactly on time is challenging, not routine
            # Reduced from 0.85 to 0.78 for more misses on close plays
            probability = 0.78  # After worst penalties: 0.78 * 0.727 = 0.567 (57%)
            # Apply CATCH_DIFFICULT bonus for 3-4 star difficulty plays
            catch_difficult_bonus = self.attributes.get_catch_difficult_bonus()
            probability = min(1.0, probability + catch_difficult_bonus)  # Up to +0.20 for elite
        elif time_margin > -0.15:
            # Fielder very slightly late (-0.15-0.0s) - diving/stretching range
            # This represents the fielder's reach/dive ability (2-4 feet)
            probability = 0.42  # After penalties: 0.42 * 0.92 = 0.39 (unchanged)
            # Apply CATCH_DIFFICULT bonus for 3-4 star difficulty plays
            catch_difficult_bonus = self.attributes.get_catch_difficult_bonus()
            probability = min(1.0, probability + catch_difficult_bonus)  # Up to +0.20 for elite
        elif time_margin > -0.35:
            # Fielder late (-0.35--0.15s) - extremely difficult diving plays
            # Requires spectacular diving effort
            # This is 5-star territory - apply CATCH_ELITE bonus
            probability = 0.10  # After penalties: 0.10 * 0.92 = 0.09 (unchanged)
            # Apply CATCH_ELITE bonus for 5-star plays (0-25% expected catch rate)
            catch_elite_bonus = self.attributes.get_catch_elite_bonus()
            probability = min(1.0, probability + catch_elite_bonus)  # Up to +0.40 for elite like Crow-Armstrong
        elif time_margin > -0.60:
            # Very late (-0.60--0.35s) - nearly impossible
            # Would require fielder to be on the ground already
            probability = 0.03  # After penalties: 0.03 * 0.92 = 0.03
            # Apply CATCH_ELITE bonus for 5-star plays
            catch_elite_bonus = self.attributes.get_catch_elite_bonus()
            probability = min(1.0, probability + catch_elite_bonus)  # Up to +0.40 for elite
        else:
            # Impossibly late (< -0.60s)
            # Ball has already landed and rolled away
            probability = 0.01

        # Apply fielder's hands rating as a multiplier (typically 0.90-0.93 for average)
        probability *= base_secure_prob

        # Distance penalty for long running catches
        # Graduated penalty based on distance to allow gap hits while not over-penalizing
        # TUNING: Reduced penalties - fielders who arrive on time should make the play
        # regardless of distance. Distance mainly matters when fielder is cutting it close.
        if distance > 120:
            probability *= 0.85  # 15% penalty for 120+ ft plays (reduced from 25%)
        elif distance > 100:
            probability *= 0.92  # 8% penalty for 100-120 ft plays (reduced from 18%)
        elif distance > 80:
            probability *= 0.96  # 4% penalty for 80-100 ft plays (reduced from 10%)

        # Backward movement penalty
        from .constants import BACKWARD_MOVEMENT_PENALTY
        direction_penalty = self.calculate_directional_speed_penalty(movement_vector)
        if direction_penalty == BACKWARD_MOVEMENT_PENALTY:
            probability *= 0.93  # 7% penalty

        # Clamp to valid range [0.0, 1.0]
        probability = max(0.0, min(1.0, probability))

        # FIELDING REALISM: For catches with probability > 0.95, introduce 1-2% chance of misplay
        # This creates more realistic bloop hits and occasional defensive lapses on routine plays
        if probability > 0.95:
            # Roll for misplay: 1.5% chance of fielder misjudging or bubbling the catch
            misplay_roll = np.random.random()
            if misplay_roll < 0.015:  # 1.5% chance
                # Misplay occurred - reduce probability significantly (to ~50-70%)
                probability *= np.random.uniform(0.50, 0.70)
        
        return probability

    def calculate_fielding_error_probability(self, ball_position: FieldPosition,
                                            time_margin: float,
                                            distance_traveled: float) -> float:
        """
        Calculate probability of committing a fielding error (bobble/misplay).

        Even when a fielder reaches the ball, there's a chance of an error.
        Based on MLB fielding percentage data (~1-2% error rate).

        Parameters
        ----------
        ball_position : FieldPosition
            Position where ball is being fielded
        time_margin : float
            Time margin (positive = early, negative = late)
        distance_traveled : float
            Distance fielder had to travel to reach ball

        Returns
        -------
        float
            Probability of fielding error (0.0 to 1.0)
        """
        from .constants import (
            FIELDING_ERROR_BASE_RATE,
            FIELDING_ERROR_DIFFICULT_MULTIPLIER,
            FIELDING_ERROR_RUSHED_MULTIPLIER,
            FIELDING_ERROR_DISTANCE_THRESHOLD,
            FIELDING_ERROR_TIME_THRESHOLD
        )

        # Start with base error rate (1.5% for routine plays)
        error_prob = FIELDING_ERROR_BASE_RATE

        # Adjust based on fielder's hands rating (secure_prob)
        # Better hands = lower error rate
        secure_prob = self.attributes.get_fielding_secure_prob()
        # Invert: if secure_prob is 0.92, error multiplier is 1.0/0.92 = 1.087
        # If secure_prob is 0.95, error multiplier is 1.0/0.95 = 1.053
        # If secure_prob is 0.88, error multiplier is 1.0/0.88 = 1.136
        hands_multiplier = 1.0 / max(secure_prob, 0.01)  # Avoid division by zero

        # Difficult play penalty (long distance)
        if distance_traveled > FIELDING_ERROR_DISTANCE_THRESHOLD:
            error_prob *= FIELDING_ERROR_DIFFICULT_MULTIPLIER

        # Rushed play penalty (tight time margin)
        if abs(time_margin) < FIELDING_ERROR_TIME_THRESHOLD:
            error_prob *= FIELDING_ERROR_RUSHED_MULTIPLIER

        # Apply hands multiplier
        error_prob *= hands_multiplier

        # Clamp to valid range [0.0, 0.25] - max 25% error rate for extreme plays
        error_prob = max(0.0, min(0.25, error_prob))

        return error_prob

    def calculate_throwing_error_probability(self, throw_distance: float,
                                            is_rushed: bool = False,
                                            is_off_balance: bool = False) -> float:
        """
        Calculate probability of committing a throwing error (wild throw/errant throw).

        Based on MLB throwing error rates (~0.5-1% of throws).

        Parameters
        ----------
        throw_distance : float
            Distance of throw in feet
        is_rushed : bool
            Whether fielder is rushed (tight timing)
        is_off_balance : bool
            Whether fielder is off-balance (difficult angle)

        Returns
        -------
        float
            Probability of throwing error (0.0 to 1.0)
        """
        from .constants import (
            THROWING_ERROR_BASE_RATE,
            THROWING_ERROR_LONG_THROW_MULTIPLIER,
            THROWING_ERROR_RUSHED_MULTIPLIER,
            THROWING_ERROR_DISTANCE_THRESHOLD,
            THROWING_ERROR_MIN_DISTANCE
        )

        # Start with base error rate (0.8%)
        error_prob = THROWING_ERROR_BASE_RATE

        # Very short throws are easier (reduce error rate)
        if throw_distance < THROWING_ERROR_MIN_DISTANCE:
            error_prob *= 0.5

        # Long throw penalty
        if throw_distance > THROWING_ERROR_DISTANCE_THRESHOLD:
            error_prob *= THROWING_ERROR_LONG_THROW_MULTIPLIER

        # Rushed throw penalty
        if is_rushed:
            error_prob *= THROWING_ERROR_RUSHED_MULTIPLIER

        # Off-balance penalty
        if is_off_balance:
            error_prob *= 1.5

        # Adjust based on fielder's throwing accuracy
        accuracy_sigma_ft = self.attributes.get_arm_accuracy_sigma_ft()
        # Better accuracy = lower error rate
        # avg_accuracy ~3.0 ft, elite ~1.5 ft, poor ~5.0 ft
        # Normalize: accuracy_multiplier = accuracy / 3.0
        accuracy_multiplier = max(accuracy_sigma_ft / 3.0, 0.5)  # Min 0.5x for elite
        error_prob *= accuracy_multiplier

        # Clamp to valid range [0.0, 0.15] - max 15% error rate for extreme situations
        error_prob = max(0.0, min(0.15, error_prob))

        return error_prob

    def attempt_fielding(self, ball_position: FieldPosition,
                        ball_arrival_time: float) -> FieldingResult:
        """
        Attempt to field a ball at given position and time using research-based model.

        Parameters
        ----------
        ball_position : FieldPosition
            Position where ball arrives
        ball_arrival_time : float
            Time when ball arrives

        Returns
        -------
        FieldingResult
            Result of fielding attempt
        """
        effective_fielder_time = self.calculate_effective_time_to_position(ball_position)

        # Determine if fielder can reach the ball in time
        # Positive time margin = fielder arrives before ball
        time_margin = ball_arrival_time - effective_fielder_time

        # Use research-based catch probability
        catch_probability = self.calculate_catch_probability(ball_position, ball_arrival_time)
        catch_roll = np.random.random()
        success = catch_roll < catch_probability

        # Determine failure reason if not successful
        failure_reason = None
        if not success:
            # Check if fielder arrives too late (more than 0.15s after ball)
            # Allow small negative margins for diving/stretching catches
            if time_margin < -0.15:
                failure_reason = 'TOO_SLOW'
            else:
                # Fielder arrived in time (or close enough) but failed the catch roll
                failure_reason = 'DROP_ERROR'

        return FieldingResult(
            success=success,
            fielder_arrival_time=effective_fielder_time,
            ball_arrival_time=ball_arrival_time,
            catch_position=ball_position,
            fielder_name=self.name,
            fielder_position=self.position,
            failure_reason=failure_reason
        )
    
    def throw_ball(self, target_position: FieldPosition, 
                   from_position: Optional[FieldPosition] = None) -> ThrowResult:
        """
        Simulate throwing the ball to a target position.
        
        Parameters
        ----------
        target_position : FieldPosition
            Target to throw to
        from_position : FieldPosition, optional
            Position throwing from (defaults to current position)
            
        Returns
        -------
        ThrowResult
            Result of throw simulation
        """
        if from_position is None:
            from_position = self.current_position
        if from_position is None:
            raise ValueError("Throwing position not specified")
        
        # Calculate throw distance
        throw_distance = from_position.distance_to(target_position)
        
        # Get throwing attributes
        throw_velocity_mph = self.get_throw_velocity_mph()
        throw_velocity_fps = throw_velocity_mph * MPH_TO_MS / FEET_TO_METERS  # Convert to ft/s
        accuracy_std_deg = self.get_throwing_accuracy_std_degrees()
        transfer_time = self.get_transfer_time_seconds()
        
        # Calculate flight time using ballistic trajectory
        # Simplified: assume optimal angle for distance and calculate time
        # For a line drive throw, approximate time as distance/velocity
        # More sophisticated: solve ballistic equation
        
        # Simple approximation for now (can be enhanced with full trajectory)
        flight_time = throw_distance / throw_velocity_fps
        
        # Add slight adjustment for arc (throws aren't perfectly horizontal)
        # Rule of thumb: add ~5% to flight time for typical throw arc
        flight_time *= 1.05
        
        # Calculate accuracy error
        horizontal_error_deg = np.random.normal(0, accuracy_std_deg)
        vertical_error_deg = np.random.normal(0, accuracy_std_deg)
        
        # Convert angular error to linear error at target distance
        # For small angles, tan(θ) ≈ θ (in radians), so use sin for better numerical stability
        horizontal_error_inches = throw_distance * 12 * np.sin(horizontal_error_deg * DEG_TO_RAD)
        vertical_error_inches = throw_distance * 12 * np.sin(vertical_error_deg * DEG_TO_RAD)
        
        return ThrowResult(
            throw_velocity=throw_velocity_mph,
            flight_time=flight_time,
            accuracy_error=(horizontal_error_inches, vertical_error_inches),
            target_position=target_position,
            release_time=transfer_time  # Time from catch to release
        )
    
    def update_position(self, new_position: FieldPosition):
        """Update fielder's current position."""
        self.current_position = new_position
        self.current_velocity = np.array([0.0, 0.0, 0.0])
        self.is_moving = False
    
    def start_movement_to(self, target: FieldPosition):
        """Start movement toward a target position."""
        self.target_position = target
        self.is_moving = True
    
    def __repr__(self):
        speed = self.attributes.get_top_sprint_speed_fps()
        arm = self.attributes.get_arm_strength_mph()
        route_eff = self.attributes.get_route_efficiency_pct()
        return (f"Fielder(name='{self.name}', position='{self.position}', "
                f"speed={speed:.1f} fps, arm={arm:.1f} mph, "
                f"route_eff={route_eff:.2f})")


# =============================================================================
# THROW PHYSICS SIMULATION
# =============================================================================

class DetailedThrowResult:
    """
    Detailed result of a throw from fielder to base.
    
    This extends the basic ThrowResult with baserunning-relevant timing info.
    """
    def __init__(self,
                 from_position: FieldPosition,
                 to_base: str,
                 throw_velocity_mph: float,
                 transfer_time: float,
                 flight_time: float,
                 arrival_time: float,  # Total: transfer + flight
                 accuracy_sigma_ft: float,
                 on_target: bool):
        """
        Initialize detailed throw result.
        
        Parameters
        ----------
        from_position : FieldPosition
            Position where throw was made from
        to_base : str
            Target base name
        throw_velocity_mph : float
            Velocity of throw in mph
        transfer_time : float
            Time from fielding ball to release (seconds)
        flight_time : float
            Time ball is in flight (seconds)
        arrival_time : float
            Total time from fielding to arrival at base (seconds)
        accuracy_sigma_ft : float
            Standard deviation of throw accuracy (feet)
        on_target : bool
            Whether throw arrived on-target (catchable immediately)
        """
        self.from_position = from_position
        self.to_base = to_base
        self.throw_velocity_mph = throw_velocity_mph
        self.transfer_time = transfer_time
        self.flight_time = flight_time
        self.arrival_time = arrival_time
        self.accuracy_sigma_ft = accuracy_sigma_ft
        self.on_target = on_target


def simulate_fielder_throw(fielder: 'Fielder',
                           from_position: FieldPosition,
                           to_base: str,
                           field_layout: FieldLayout) -> DetailedThrowResult:
    """
    Simulate a throw from fielder to base using physics-based timing.
    
    Incorporates:
    - Transfer time (glove-to-release): 0.4-0.8s based on fielder attributes
    - Throw velocity: 60-105 mph based on arm strength
    - Flight time: distance / velocity with 7% arc penalty
    - Accuracy: probabilistic on-target determination
    
    Parameters
    ----------
    fielder : Fielder
        Fielder making the throw
    from_position : FieldPosition
        Position where fielder is throwing from
    to_base : str
        Target base ('first', 'second', 'third', 'home')
    field_layout : FieldLayout
        Field layout for base positions
        
    Returns
    -------
    DetailedThrowResult
        Complete throw timing and accuracy information
        
    Examples
    --------
    >>> # Shortstop throws to first base
    >>> ss_position = FieldPosition(40, 150, 0)  # SS fielding position
    >>> throw_result = simulate_fielder_throw(shortstop, ss_position, "first", field_layout)
    >>> print(f"Throw arrives in {throw_result.arrival_time:.2f}s")
    Throw arrives in 1.12s
    
    Notes
    -----
    - Throws have slight arc, adding ~7% to straight-line flight time
    - Inaccurate throws add 0.5-1.0s for receiving fielder to handle
    - Transfer time varies by position (infielders faster than outfielders)
    """
    # Get fielder throwing attributes from physics-first system
    arm_strength_mph = fielder.attributes.get_arm_strength_mph()  # 60-105 mph
    transfer_time = fielder.attributes.get_transfer_time_s()  # 0.4-0.8s
    accuracy_sigma_ft = fielder.attributes.get_arm_accuracy_sigma_ft()  # 2-12 ft
    
    # Get target base position
    base_position = field_layout.get_base_position(to_base)
    
    # Calculate horizontal distance (throws are ground-level to ground-level)
    distance_ft = from_position.horizontal_distance_to(base_position)
    
    # Convert throw velocity to ft/s
    throw_velocity_fps = arm_strength_mph * 1.467  # mph to ft/s
    
    # Calculate straight-line flight time
    straight_flight_time = distance_ft / throw_velocity_fps
    
    # Add arc penalty (throws have upward arc, adding ~7% to travel time)
    flight_time = straight_flight_time * 1.07
    
    # Determine if throw is on-target using accuracy
    # Throws with sigma < 3 ft are very accurate (95% on-target)
    # Throws with sigma > 8 ft are poor (70% on-target)
    on_target_probability = np.clip(1.0 - (accuracy_sigma_ft - 2.0) / 15.0, 0.70, 0.98)
    on_target = np.random.random() < on_target_probability
    
    # Off-target throws require extra handling time by receiving fielder
    handling_penalty = 0.0
    if not on_target:
        handling_penalty = np.random.uniform(0.5, 1.0)
    
    # Total arrival time
    total_time = transfer_time + flight_time + handling_penalty
    
    return DetailedThrowResult(
        from_position=from_position,
        to_base=to_base,
        throw_velocity_mph=arm_strength_mph,
        transfer_time=transfer_time,
        flight_time=flight_time,
        arrival_time=total_time,
        accuracy_sigma_ft=accuracy_sigma_ft,
        on_target=on_target
    )


# =============================================================================
# RELAY THROW MECHANICS
# =============================================================================

class RelayThrowResult:
    """
    Result of a relay throw involving a cut-off man.

    Contains timing for both legs of the relay: fielder → cutoff → target.
    """
    def __init__(self,
                 from_position: FieldPosition,
                 cutoff_position: str,
                 to_base: str,
                 first_throw: DetailedThrowResult,
                 second_throw: DetailedThrowResult,
                 relay_handling_time: float,
                 total_arrival_time: float,
                 is_relay: bool = True):
        """
        Initialize relay throw result.

        Parameters
        ----------
        from_position : FieldPosition
            Original fielder's throwing position
        cutoff_position : str
            Position name of cut-off man (e.g., 'shortstop', 'second_base')
        to_base : str
            Target base name
        first_throw : DetailedThrowResult
            Throw from fielder to cut-off man
        second_throw : DetailedThrowResult
            Throw from cut-off man to target base
        relay_handling_time : float
            Time for cut-off man to receive, turn, and release (seconds)
        total_arrival_time : float
            Total time from initial throw to ball arrival at target
        is_relay : bool
            True if relay was used, False if direct throw
        """
        self.from_position = from_position
        self.cutoff_position = cutoff_position
        self.to_base = to_base
        self.first_throw = first_throw
        self.second_throw = second_throw
        self.relay_handling_time = relay_handling_time
        self.total_arrival_time = total_arrival_time
        self.is_relay = is_relay


# Relay throw distance threshold (feet)
RELAY_THROW_THRESHOLD = 200.0


def determine_cutoff_man(fielder_position: str, target_base: str) -> str:
    """
    Determine the appropriate cut-off man for a throw.

    Cut-off man selection follows baseball convention:
    - Left field to home/third: Shortstop (left side alignment)
    - Center field to home: Shortstop (typically plays deeper)
    - Right field to home: Second baseman (right side alignment)
    - Right field to third: Shortstop (cuts across diamond)
    - Deep throws to second: Shortstop or pitcher

    Parameters
    ----------
    fielder_position : str
        Position of fielder making initial throw (e.g., 'left_field', 'center_field')
    target_base : str
        Target base ('home', 'third', 'second', 'first')

    Returns
    -------
    str
        Position name of cut-off man

    Examples
    --------
    >>> determine_cutoff_man('left_field', 'home')
    'shortstop'
    >>> determine_cutoff_man('right_field', 'home')
    'second_base'
    """
    # Normalize position names (handle variations)
    fielder = fielder_position.lower().replace('_', ' ').replace(' ', '_')
    target = target_base.lower()

    # Outfield positions
    is_left_field = 'left' in fielder or fielder == 'lf'
    is_center_field = 'center' in fielder or fielder == 'cf'
    is_right_field = 'right' in fielder or fielder == 'rf'

    # Throws to home plate
    if target == 'home':
        if is_left_field:
            return 'shortstop'
        elif is_center_field:
            return 'shortstop'  # SS typically deeper than 2B
        elif is_right_field:
            return 'second_base'
        else:
            # Infield throws to home - use nearest infielder
            return 'shortstop'

    # Throws to third base
    elif target == 'third':
        return 'shortstop'  # SS is primary cutoff for third

    # Throws to second base (rare relay situation)
    elif target == 'second':
        if is_center_field:
            return 'shortstop'  # SS plays deeper
        else:
            return 'shortstop'  # Default to SS for deep hits

    # Throws to first (very rare relay)
    elif target == 'first':
        return 'second_base'

    # Default to shortstop (most versatile cut-off position)
    return 'shortstop'


def simulate_relay_throw(fielder: 'Fielder',
                        cutoff_man: 'Fielder',
                        from_position: FieldPosition,
                        target_base: str,
                        field_layout: FieldLayout,
                        force_relay: bool = False) -> RelayThrowResult:
    """
    Simulate a throw that may require a relay through a cut-off man.

    Automatically determines if a relay is needed based on throw distance.
    If distance > RELAY_THROW_THRESHOLD (200 ft), uses two-stage relay.
    Otherwise, performs direct throw.

    Parameters
    ----------
    fielder : Fielder
        Fielder making the initial throw
    cutoff_man : Fielder
        Cut-off man who will relay the throw
    from_position : FieldPosition
        Position where fielder is throwing from
    target_base : str
        Target base name ('home', 'third', 'second', 'first')
    field_layout : FieldLayout
        Field layout for base positions
    force_relay : bool, optional
        Force use of relay regardless of distance (default: False)

    Returns
    -------
    RelayThrowResult
        Complete relay throw result with timing for each stage

    Examples
    --------
    >>> # Deep center field throw to home
    >>> cf_position = FieldPosition(0, 380, 0)  # Deep center
    >>> result = simulate_relay_throw(cf, shortstop, cf_position, 'home', field_layout)
    >>> print(f"Relay time: {result.total_arrival_time:.2f}s via {result.cutoff_position}")
    Relay time: 3.45s via shortstop

    Notes
    -----
    - Relay throws add handling time (~0.2-0.4s) for cut-off man to receive and release
    - Total time may be longer than direct throw, but represents realistic play
    - Cut-off men have better arm accuracy and positioning for second throw
    """
    # Get target base position
    target_position = field_layout.get_base_position(target_base)

    # Calculate direct throw distance
    direct_distance = from_position.horizontal_distance_to(target_position)

    # Determine if relay is needed
    needs_relay = force_relay or direct_distance > RELAY_THROW_THRESHOLD

    if not needs_relay:
        # Direct throw - no relay needed
        direct_throw = simulate_fielder_throw(fielder, from_position, target_base, field_layout)

        return RelayThrowResult(
            from_position=from_position,
            cutoff_position="none",
            to_base=target_base,
            first_throw=direct_throw,
            second_throw=direct_throw,  # Same as first for direct throws
            relay_handling_time=0.0,
            total_arrival_time=direct_throw.arrival_time,
            is_relay=False
        )

    # RELAY THROW - Two stage throw

    # Position cut-off man optimally between fielder and target
    # Cut-off man typically positioned ~2/3 of the way to target or at standard position
    cutoff_standard_pos = field_layout.get_defensive_position(cutoff_man.position)

    # Use cut-off man's standard position (realistic - they run to cutoff position)
    cutoff_position = cutoff_standard_pos

    # Stage 1: Fielder to cut-off man
    # Calculate throw manually since we're throwing to a position, not a base
    first_throw_distance = from_position.horizontal_distance_to(cutoff_position)

    # Get fielder's throwing attributes
    fielder_arm_mph = fielder.attributes.get_arm_strength_mph()
    fielder_transfer = fielder.attributes.get_transfer_time_s()
    fielder_accuracy = fielder.attributes.get_arm_accuracy_sigma_ft()

    # Calculate flight time
    first_throw_velocity_fps = fielder_arm_mph * 1.467  # mph to ft/s
    first_throw_flight_time = (first_throw_distance / first_throw_velocity_fps) * 1.07

    # Determine accuracy
    on_target_prob_1 = np.clip(1.0 - (fielder_accuracy - 2.0) / 15.0, 0.70, 0.98)
    first_on_target = np.random.random() < on_target_prob_1

    # Create first throw result
    first_throw = DetailedThrowResult(
        from_position=from_position,
        to_base=f"{cutoff_man.position}_cutoff",
        throw_velocity_mph=fielder_arm_mph,
        transfer_time=fielder_transfer,
        flight_time=first_throw_flight_time,
        arrival_time=fielder_transfer + first_throw_flight_time,
        accuracy_sigma_ft=fielder_accuracy,
        on_target=first_on_target
    )

    # Relay handling time: cut-off man receives, turns, and releases
    # Faster than full transfer (already positioned, anticipating throw)
    # Typical range: 0.2-0.4 seconds for skilled middle infielders
    relay_handling_time = np.random.uniform(0.2, 0.4)

    # Stage 2: Cut-off man to target base
    second_throw = simulate_fielder_throw(
        cutoff_man,
        cutoff_position,
        target_base,
        field_layout
    )

    # Total time: first throw + relay handling + second throw
    total_time = first_throw.arrival_time + relay_handling_time + second_throw.arrival_time

    return RelayThrowResult(
        from_position=from_position,
        cutoff_position=cutoff_man.position,
        to_base=target_base,
        first_throw=first_throw,
        second_throw=second_throw,
        relay_handling_time=relay_handling_time,
        total_arrival_time=total_time,
        is_relay=True
    )


class FieldingSimulator:
    """
    Manages fielding simulation for multiple fielders and ball in play.
    """
    
    def __init__(self, field_layout: FieldLayout):
        """
        Initialize fielding simulator.
        
        Parameters
        ----------
        field_layout : FieldLayout
            Field layout and positioning
        """
        self.field_layout = field_layout
        self.fielders = {}
        self.current_time = 0.0
    
    def add_fielder(self, position_name: str, fielder: Fielder):
        """
        Add a fielder at a specific position.

        FIELDING REALISM ENHANCEMENT (Pass #2):
        Introduces slight positioning variability (~1-3 steps off ideal spot)
        to simulate realistic defensive alignment variance.
        """
        # Set fielder to standard position if not already positioned
        if fielder.current_position is None:
            standard_pos = self.field_layout.get_defensive_position(position_name)

            # FIELDING REALISM: Add positioning variability
            # Fielders are not always perfectly positioned
            # Variance: 1-3 steps (3-9 feet) in random direction
            steps_variance = np.random.uniform(1, 3)  # 1-3 steps
            feet_variance = steps_variance * 3.0  # Each step ~3 feet

            # Random angle for position offset
            angle = np.random.uniform(0, 2 * np.pi)

            # Calculate position offset
            x_offset = feet_variance * np.cos(angle)
            y_offset = feet_variance * np.sin(angle)

            # Apply offset to standard position
            adjusted_pos = FieldPosition(
                standard_pos.x + x_offset,
                standard_pos.y + y_offset,
                standard_pos.z
            )

            fielder.update_position(adjusted_pos)

        self.fielders[position_name] = fielder
    
    def determine_responsible_fielder(self, ball_position: FieldPosition,
                                     ball_arrival_time: Optional[float] = None) -> str:
        """
        Determine which fielder should attempt to field the ball based on
        physics-first approach: who can actually catch it.

        Implements "Bystander Effect" fix:
        1. Iterate through all fielders and check who can make the catch
        2. A fielder can catch if their arrival time < ball arrival time
        3. Among fielders who can catch, select the one who arrives earliest (best time margin)
        4. Use defensive hierarchy as tie-breaker if multiple arrive at similar times
        5. Only fall back to zone assignment if no one can catch it

        This ensures we NEVER assign to a fielder who can't make the play
        when another fielder could have caught it.

        Parameters
        ----------
        ball_position : FieldPosition
            Position where ball will land
        ball_arrival_time : float, optional
            Time when ball will arrive (used for capability assessment)

        Returns
        -------
        str
            Name of the fielder position best suited to field the ball
        """
        from .constants import (
            FIELDING_HIERARCHY,
            FIELDING_HIERARCHY_TIME_THRESHOLD,
            FIELDING_HIERARCHY_DISTANCE_THRESHOLD
        )

        # If no arrival time provided, use zone assignment as fallback
        if ball_arrival_time is None:
            return self.field_layout.get_nearest_fielder_position(ball_position)

        # PHYSICS-FIRST APPROACH: Check who can actually catch the ball
        # Calculate effective time for all fielders
        fielders_who_can_catch = []

        for pos_name, fielder in self.fielders.items():
            try:
                # Calculate how long it takes this fielder to reach the ball
                effective_time = fielder.calculate_effective_time_to_position(ball_position)

                # Time margin: positive = fielder arrives before ball (can catch)
                time_margin = ball_arrival_time - effective_time

                # Only consider fielders who arrive before or very close to ball arrival
                # Allow small negative margin for diving catches (up to -0.15s)
                if time_margin >= -0.15:
                    distance = fielder.current_position.horizontal_distance_to(ball_position)
                    hierarchy_priority = FIELDING_HIERARCHY.get(pos_name, 50)

                    fielders_who_can_catch.append({
                        'position': pos_name,
                        'fielder': fielder,
                        'effective_time': effective_time,
                        'time_margin': time_margin,
                        'distance': distance,
                        'hierarchy': hierarchy_priority
                    })

            except (ValueError, AttributeError):
                # Fielder can't reach this position
                continue

        # If no one can catch it, fall back to zone assignment
        if not fielders_who_can_catch:
            return self.field_layout.get_nearest_fielder_position(ball_position)

        # Sort by time margin (descending) - fielder who arrives earliest gets priority
        fielders_who_can_catch.sort(key=lambda x: x['time_margin'], reverse=True)

        # Get the fielder with the best time margin (arrives earliest)
        best_fielder = fielders_who_can_catch[0]

        # Check for contested plays (multiple fielders arrive within threshold)
        contested_fielders = [
            f for f in fielders_who_can_catch
            if abs(f['time_margin'] - best_fielder['time_margin']) <= FIELDING_HIERARCHY_TIME_THRESHOLD
        ]

        if len(contested_fielders) > 1:
            # Multiple fielders can make the play with similar timing
            # Apply tie-breaking logic:

            # 1. Check if one fielder is significantly closer
            closest_fielder = min(contested_fielders, key=lambda x: x['distance'])

            # If closest fielder is more than DISTANCE_THRESHOLD closer than others, assign to them
            for other in contested_fielders:
                if other['position'] != closest_fielder['position']:
                    distance_diff = other['distance'] - closest_fielder['distance']
                    if distance_diff > FIELDING_HIERARCHY_DISTANCE_THRESHOLD:
                        # Closest fielder is significantly closer
                        return closest_fielder['position']

            # 2. If no one is significantly closer, use defensive hierarchy
            # Higher hierarchy value = higher priority (center fielder > corner outfielders, etc.)
            contested_fielders.sort(key=lambda x: x['hierarchy'], reverse=True)
            return contested_fielders[0]['position']

        # Clear winner - assign to fielder with best time margin
        return best_fielder['position']
    
    def simulate_fielding_attempt(self, ball_position: FieldPosition, 
                                 ball_arrival_time: float) -> FieldingResult:
        """
        Simulate fielding attempt by the responsible fielder.
        
        Parameters
        ----------
        ball_position : FieldPosition
            Where the ball will arrive
        ball_arrival_time : float
            When the ball will arrive
            
        Returns
        -------
        FieldingResult
            Result of the fielding attempt
        """
        responsible_position = self.determine_responsible_fielder(ball_position, ball_arrival_time)
        
        if responsible_position not in self.fielders:
            raise ValueError(f"No fielder assigned to position {responsible_position}")
        
        fielder = self.fielders[responsible_position]
        return fielder.attempt_fielding(ball_position, ball_arrival_time)
    
    def get_all_fielding_probabilities(self, ball_position: FieldPosition,
                                     ball_arrival_time: float) -> Dict[str, float]:
        """
        Calculate fielding probability for all fielders.
        
        Parameters
        ----------
        ball_position : FieldPosition
            Ball position
        ball_arrival_time : float
            Ball arrival time
            
        Returns
        -------
        dict
            Mapping of fielder position to probability of successful fielding
        """
        probabilities = {}
        
        for pos_name, fielder in self.fielders.items():
            try:
                effective_time = fielder.calculate_effective_time_to_position(ball_position)
                
                if effective_time <= ball_arrival_time:
                    # Base probability if they can get there
                    prob = 0.95  # 95% chance if they reach it
                    
                    # Reduce if it's very close
                    margin = ball_arrival_time - effective_time
                    if margin < 0.1:  # Very close play
                        prob *= 0.8
                else:
                    # Small chance for diving play
                    time_deficit = effective_time - ball_arrival_time
                    if time_deficit <= 0.3:
                        # Derive range from route efficiency (higher = better range)
                        # Elite: 0.95+ -> 80/100, Average: 0.88 -> 50/100, Poor: 0.85 -> 20/100
                        route_eff = fielder.attributes.get_route_efficiency_pct()
                        range_score = (route_eff - 0.85) / 0.10 * 60 + 20  # Map 0.85-0.95 to 20-80
                        range_score = max(20, min(100, range_score))
                        prob = 0.20 * (range_score / 100.0)
                    else:
                        prob = 0.0
                
                probabilities[pos_name] = prob
                
            except ValueError:
                probabilities[pos_name] = 0.0
        
        return probabilities


# Convenience functions for creating fielders
def create_elite_fielder(name: str, position: str, quality: str = "good") -> Fielder:
    """Create an elite fielder using physics-first attribute system (0-100,000 scale)."""
    from .attributes import create_elite_fielder as create_elite_attrs

    # Determine position type for specialized attributes
    is_middle_infield = position.lower() in ['shortstop', 'second base', 'second_base']
    is_center_field = 'center' in position.lower()

    if is_middle_infield or is_center_field:
        # Elite range/speed positions
        attributes = create_elite_attrs(quality)
    else:
        # Use average fielder attributes for other positions
        from .attributes import create_average_fielder as create_avg_attrs
        attributes = create_avg_attrs(quality)

    return Fielder(
        name=name,
        position=position,
        attributes=attributes
    )


def create_average_fielder(name: str, position: str, quality: str = "average") -> Fielder:
    """Create an average fielder using physics-first attribute system (0-100,000 scale)."""
    from .attributes import create_average_fielder as create_avg_attrs

    attributes = create_avg_attrs(quality)

    return Fielder(
        name=name,
        position=position,
        attributes=attributes
    )


def create_poor_fielder(name: str, position: str, quality: str = "poor") -> Fielder:
    """Create a below-average fielder using physics-first attribute system (0-100,000 scale)."""
    from .attributes import create_slow_fielder as create_slow_attrs

    attributes = create_slow_attrs(quality)

    return Fielder(
        name=name,
        position=position,
        attributes=attributes
    )