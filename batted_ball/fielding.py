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


class FieldingResult:
    """Result of a fielding attempt."""
    
    def __init__(self, 
                 success: bool,
                 fielder_arrival_time: float,
                 ball_arrival_time: float,
                 catch_position: FieldPosition,
                 fielder_name: str):
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
        """
        self.success = success
        self.fielder_arrival_time = fielder_arrival_time
        self.ball_arrival_time = ball_arrival_time
        self.catch_position = catch_position
        self.fielder_name = fielder_name
        self.margin = fielder_arrival_time - ball_arrival_time  # Negative = made it


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
    
    Core Physical Attributes:
    - sprint_speed: Maximum running speed (0-100 rating)
    - acceleration: Rate of acceleration to top speed (0-100 rating)
    - reaction_time: Delay before movement begins (0-100 rating)
    - arm_strength: Throwing velocity capability (0-100 rating)
    - throwing_accuracy: Precision of throws (0-100 rating)
    - transfer_quickness: Speed of glove-to-hand transition (0-100 rating)
    - fielding_range: Effective area coverage (0-100 rating)
    """
    
    def __init__(self,
                 name: str = "Fielder",
                 position: str = "infield",
                 # Physical attributes (0-100 scale)
                 sprint_speed: int = 50,
                 acceleration: int = 50,
                 reaction_time: int = 50,
                 arm_strength: int = 50,
                 throwing_accuracy: int = 50,
                 transfer_quickness: int = 50,
                 fielding_range: int = 50,
                 # Position and state
                 current_position: Optional[FieldPosition] = None):
        """
        Initialize fielder with attribute ratings.
        
        Parameters
        ----------
        name : str
            Fielder's name/identifier
        position : str
            Position type ('infield', 'outfield', 'catcher')
        sprint_speed : int (0-100)
            Sprint speed rating (50=avg MLB ~27 ft/s, 80=elite ~30 ft/s)
        acceleration : int (0-100)
            Acceleration rating (50=avg ~16 ft/s², 80=elite ~20 ft/s²)
        reaction_time : int (0-100)
            Reaction rating (50=avg ~0.15s, 80=elite ~0.05s, higher=faster)
        arm_strength : int (0-100)
            Throwing velocity rating (position-dependent ranges)
        throwing_accuracy : int (0-100)
            Throwing precision (50=avg ~2° error, 80=elite ~1° error)
        transfer_quickness : int (0-100)
            Glove-to-hand speed (50=avg, position-dependent)
        fielding_range : int (0-100)
            Range factor (50=avg, affects effective coverage area)
        current_position : FieldPosition, optional
            Current field position
        """
        self.name = name
        self.position = position.lower()
        
        # Clip all ratings to 0-100 scale
        self.sprint_speed = np.clip(sprint_speed, 0, 100)
        self.acceleration = np.clip(acceleration, 0, 100)
        self.reaction_time = np.clip(reaction_time, 0, 100)
        self.arm_strength = np.clip(arm_strength, 0, 100)
        self.throwing_accuracy = np.clip(throwing_accuracy, 0, 100)
        self.transfer_quickness = np.clip(transfer_quickness, 0, 100)
        self.fielding_range = np.clip(fielding_range, 0, 100)
        
        # Position and state
        self.current_position = current_position
        self.is_infielder = position.lower() in ['infield', 'catcher']
        
        # Movement state
        self.current_velocity = np.array([0.0, 0.0, 0.0])  # ft/s
        self.is_moving = False
        self.target_position = None
    
    def get_sprint_speed_fps(self) -> float:
        """Convert sprint speed rating to feet per second."""
        # Linear mapping: 20=min, 50=avg, 80=elite, 100=max
        min_speed = FIELDER_SPRINT_SPEED_MIN
        max_speed = FIELDER_SPRINT_SPEED_MAX
        avg_speed = FIELDER_SPRINT_SPEED_AVG
        
        if self.sprint_speed <= 50:
            # 20-50 range: min to avg
            factor = (self.sprint_speed - 20) / 30.0
            speed = min_speed + factor * (avg_speed - min_speed)
        else:
            # 50-100 range: avg to max  
            factor = (self.sprint_speed - 50) / 50.0
            speed = avg_speed + factor * (max_speed - avg_speed)
        
        return speed
    
    def get_acceleration_fps2(self) -> float:
        """Convert acceleration rating to feet per second squared using Statcast metrics."""
        # Use research-based acceleration times instead of raw ft/s²
        from .constants import (
            FIELDER_ACCELERATION_TIME_ELITE,
            FIELDER_ACCELERATION_TIME_AVG, 
            FIELDER_ACCELERATION_TIME_POOR,
            FIELDER_ACCELERATION_TIME_MAX
        )
        
        # Map rating to acceleration time (lower time = better acceleration)
        if self.acceleration >= 80:
            accel_time = FIELDER_ACCELERATION_TIME_ELITE
        elif self.acceleration >= 60:
            # Interpolate between elite and average
            factor = (self.acceleration - 60) / 20.0
            accel_time = FIELDER_ACCELERATION_TIME_AVG + factor * (FIELDER_ACCELERATION_TIME_ELITE - FIELDER_ACCELERATION_TIME_AVG)
        elif self.acceleration >= 40:
            # Interpolate between average and poor
            factor = (self.acceleration - 40) / 20.0
            accel_time = FIELDER_ACCELERATION_TIME_POOR + factor * (FIELDER_ACCELERATION_TIME_AVG - FIELDER_ACCELERATION_TIME_POOR)
        else:
            # Poor to max
            factor = max(0, (self.acceleration - 20) / 20.0)
            accel_time = FIELDER_ACCELERATION_TIME_MAX + factor * (FIELDER_ACCELERATION_TIME_POOR - FIELDER_ACCELERATION_TIME_MAX)
        
        # Convert to acceleration in ft/s²
        # a = v_max / t, assuming velocity reaches ~80% of max during acceleration phase
        max_speed = self.get_sprint_speed_fps_statcast()
        return (0.80 * max_speed) / accel_time
    
    def get_sprint_speed_fps_statcast(self) -> float:
        """Convert sprint speed rating to fps using Statcast-calibrated values."""
        from .constants import (
            FIELDER_SPRINT_SPEED_STATCAST_MIN,
            FIELDER_SPRINT_SPEED_STATCAST_AVG,
            FIELDER_SPRINT_SPEED_STATCAST_ELITE,
            FIELDER_SPRINT_SPEED_STATCAST_MAX
        )
        
        # Use research-based Statcast values
        if self.sprint_speed >= 80:
            # Elite to max
            factor = (self.sprint_speed - 80) / 20.0
            speed = FIELDER_SPRINT_SPEED_STATCAST_ELITE + factor * (FIELDER_SPRINT_SPEED_STATCAST_MAX - FIELDER_SPRINT_SPEED_STATCAST_ELITE)
        elif self.sprint_speed >= 50:
            # Average to elite
            factor = (self.sprint_speed - 50) / 30.0
            speed = FIELDER_SPRINT_SPEED_STATCAST_AVG + factor * (FIELDER_SPRINT_SPEED_STATCAST_ELITE - FIELDER_SPRINT_SPEED_STATCAST_AVG)
        else:
            # Min to average
            factor = max(0, (self.sprint_speed - 20) / 30.0)
            speed = FIELDER_SPRINT_SPEED_STATCAST_MIN + factor * (FIELDER_SPRINT_SPEED_STATCAST_AVG - FIELDER_SPRINT_SPEED_STATCAST_MIN)
        
        return speed
    
    def get_first_step_time(self) -> float:
        """Get first step time based on Statcast research."""
        from .constants import (
            FIELDER_FIRST_STEP_TIME_ELITE,
            FIELDER_FIRST_STEP_TIME_AVG,
            FIELDER_FIRST_STEP_TIME_POOR,
            FIELDER_FIRST_STEP_TIME_MAX
        )
        
        # Higher reaction rating = faster first step (lower time)
        if self.reaction_time >= 80:
            return FIELDER_FIRST_STEP_TIME_ELITE
        elif self.reaction_time >= 60:
            factor = (self.reaction_time - 60) / 20.0
            return FIELDER_FIRST_STEP_TIME_AVG + factor * (FIELDER_FIRST_STEP_TIME_ELITE - FIELDER_FIRST_STEP_TIME_AVG)
        elif self.reaction_time >= 40:
            factor = (self.reaction_time - 40) / 20.0
            return FIELDER_FIRST_STEP_TIME_POOR + factor * (FIELDER_FIRST_STEP_TIME_AVG - FIELDER_FIRST_STEP_TIME_POOR)
        else:
            factor = max(0, (self.reaction_time - 20) / 20.0)
            return FIELDER_FIRST_STEP_TIME_MAX + factor * (FIELDER_FIRST_STEP_TIME_POOR - FIELDER_FIRST_STEP_TIME_MAX)
    
    def get_route_efficiency(self) -> float:
        """Get route efficiency based on Statcast research."""
        from .constants import (
            ROUTE_EFFICIENCY_ELITE,
            ROUTE_EFFICIENCY_AVG,
            ROUTE_EFFICIENCY_POOR,
            ROUTE_EFFICIENCY_MIN
        )
        
        # Map fielding range rating to route efficiency
        if self.fielding_range >= 80:
            return ROUTE_EFFICIENCY_ELITE
        elif self.fielding_range >= 60:
            factor = (self.fielding_range - 60) / 20.0
            return ROUTE_EFFICIENCY_AVG + factor * (ROUTE_EFFICIENCY_ELITE - ROUTE_EFFICIENCY_AVG)
        elif self.fielding_range >= 40:
            factor = (self.fielding_range - 40) / 20.0
            return ROUTE_EFFICIENCY_POOR + factor * (ROUTE_EFFICIENCY_AVG - ROUTE_EFFICIENCY_POOR)
        else:
            factor = max(0, (self.fielding_range - 20) / 20.0)
            return ROUTE_EFFICIENCY_MIN + factor * (ROUTE_EFFICIENCY_POOR - ROUTE_EFFICIENCY_MIN)
    
    def calculate_directional_speed_penalty(self, movement_direction: np.ndarray) -> float:
        """Calculate speed penalty based on movement direction."""
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
            return FORWARD_MOVEMENT_PENALTY  # Forward movement
        elif angle_deg <= 135:
            return LATERAL_MOVEMENT_PENALTY   # Lateral movement
        else:
            return BACKWARD_MOVEMENT_PENALTY  # Backward movement
    
    def calculate_optimal_intercept_point(self, ball_trajectory_data: dict, 
                                        current_time: float) -> np.ndarray:
        """
        Calculate optimal intercept point using advanced trajectory prediction.
        
        Uses iterative approach to find the point where fielder and ball
        arrive simultaneously, accounting for fielder's movement capabilities.
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
    
    def get_reaction_time_seconds(self) -> float:
        """Convert reaction time rating to seconds (higher rating = faster reaction)."""
        min_time = FIELDER_REACTION_TIME_MAX  # Worst reaction (highest time)
        max_time = FIELDER_REACTION_TIME_MIN  # Best reaction (lowest time)
        avg_time = FIELDER_REACTION_TIME_AVG
        
        # Higher rating = lower reaction time
        if self.reaction_time <= 50:
            factor = (self.reaction_time - 20) / 30.0
            time = min_time - factor * (min_time - avg_time)
        else:
            factor = (self.reaction_time - 50) / 50.0
            time = avg_time - factor * (avg_time - max_time)
        
        return max(time, 0.0)
    
    def get_throw_velocity_mph(self) -> float:
        """Convert arm strength rating to throwing velocity in mph."""
        if self.is_infielder:
            min_vel = INFIELDER_THROW_VELOCITY_MIN
            max_vel = INFIELDER_THROW_VELOCITY_MAX
            avg_vel = INFIELDER_THROW_VELOCITY_AVG
        else:
            min_vel = OUTFIELDER_THROW_VELOCITY_MIN
            max_vel = OUTFIELDER_THROW_VELOCITY_MAX
            avg_vel = OUTFIELDER_THROW_VELOCITY_AVG
        
        if self.arm_strength <= 50:
            factor = (self.arm_strength - 20) / 30.0
            velocity = min_vel + factor * (avg_vel - min_vel)
        else:
            factor = (self.arm_strength - 50) / 50.0
            velocity = avg_vel + factor * (max_vel - avg_vel)
        
        return velocity
    
    def get_transfer_time_seconds(self) -> float:
        """Convert transfer quickness rating to seconds."""
        if self.is_infielder:
            min_time = INFIELDER_TRANSFER_TIME_MAX   # Slowest (highest time)
            max_time = INFIELDER_TRANSFER_TIME_MIN   # Fastest (lowest time)
            avg_time = INFIELDER_TRANSFER_TIME_AVG
        else:
            min_time = OUTFIELDER_TRANSFER_TIME_MAX
            max_time = OUTFIELDER_TRANSFER_TIME_MIN
            avg_time = OUTFIELDER_TRANSFER_TIME_AVG
        
        # Higher rating = lower transfer time
        if self.transfer_quickness <= 50:
            factor = (self.transfer_quickness - 20) / 30.0
            time = min_time - factor * (min_time - avg_time)
        else:
            factor = (self.transfer_quickness - 50) / 50.0
            time = avg_time - factor * (avg_time - max_time)
        
        return time
    
    def get_throwing_accuracy_std_degrees(self) -> float:
        """Convert throwing accuracy rating to standard deviation in degrees."""
        min_accuracy = THROWING_ACCURACY_TERRIBLE  # Worst accuracy (highest error)
        max_accuracy = THROWING_ACCURACY_ELITE     # Best accuracy (lowest error)
        avg_accuracy = THROWING_ACCURACY_AVG
        
        # Higher rating = lower error
        if self.throwing_accuracy <= 50:
            factor = (self.throwing_accuracy - 20) / 30.0
            std_deg = min_accuracy - factor * (min_accuracy - avg_accuracy)
        else:
            factor = (self.throwing_accuracy - 50) / 50.0
            std_deg = avg_accuracy - factor * (avg_accuracy - max_accuracy)
        
        return std_deg
    
    def get_effective_range_multiplier(self) -> float:
        """Get range multiplier based on fielding range rating."""
        if self.fielding_range <= 50:
            # Below average: 0.8 to 1.0 multiplier
            factor = (self.fielding_range - 20) / 30.0
            multiplier = FIELDING_RANGE_POOR + factor * (FIELDING_RANGE_AVG - FIELDING_RANGE_POOR)
        else:
            # Above average: 1.0 to 1.25 multiplier
            factor = (self.fielding_range - 50) / 50.0
            multiplier = FIELDING_RANGE_AVG + factor * (FIELDING_RANGE_ELITE - FIELDING_RANGE_AVG)
        
        return multiplier
    
    def calculate_time_to_position(self, target: FieldPosition) -> float:
        """
        Calculate time required to reach a target position using research-based multi-phase model.

        Implements:
        - Fast reaction model for short distances (< 15ft)
        - Multi-phase model for longer distances

        Parameters
        ----------
        target : FieldPosition
            Target position to reach

        Returns
        -------
        float
            Time in seconds to reach position
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

        # Get research-based physical attributes
        max_speed = self.get_sprint_speed_fps_statcast()

        # For very short distances (pop-ups, etc), use simplified model
        # These are quick reactions without full acceleration phase
        # NOTE: This already includes reaction time, so don't add it again in calculate_effective_time_to_position
        if distance < 15.0:
            # Quick reaction model: minimal delay + fast movement at partial speed
            quick_reaction_time = 0.10  # Quick first step for close plays (reduced from 0.15)
            # Use 70% of max speed for short bursts (increased from 60% for better performance)
            burst_speed = max_speed * 0.70
            movement_time = distance / burst_speed
            return quick_reaction_time + movement_time

        # For longer distances, use full multi-phase model
        first_step_time = self.get_first_step_time()
        acceleration = self.get_acceleration_fps2()
        route_efficiency = self.get_route_efficiency() / 100.0  # Convert to fraction

        # Apply directional speed penalty
        direction_penalty = self.calculate_directional_speed_penalty(movement_vector)
        effective_max_speed = max_speed * direction_penalty

        # Apply route efficiency (affects effective distance)
        effective_distance = distance / route_efficiency

        # Multi-phase movement model:
        # Phase 1: First step time (from research)
        phase1_time = first_step_time

        # Phase 2: Acceleration phase
        # Time to reach 80% of max speed (research shows this is typical acceleration target)
        target_speed = 0.80 * effective_max_speed
        acceleration_time = target_speed / acceleration
        acceleration_distance = 0.5 * acceleration * acceleration_time**2

        if effective_distance <= acceleration_distance:
            # Never reach target speed - solve quadratic equation
            # distance = 0.5 * acceleration * time^2
            acceleration_time = np.sqrt(2 * effective_distance / acceleration)
            constant_velocity_time = 0.0
        else:
            # Phase 3: Constant velocity phase
            remaining_distance = effective_distance - acceleration_distance
            constant_velocity_time = remaining_distance / target_speed

        total_time = phase1_time + acceleration_time + constant_velocity_time
        return total_time

    def calculate_effective_time_to_position(self, target: FieldPosition) -> float:
        """Calculate time to reach a target after accounting for range skill and reaction time."""
        if self.current_position is None:
            raise ValueError("Current position not set")

        # Calculate base time (includes reaction time for short distances)
        base_time = self.calculate_time_to_position(target)

        # Check if this was a short-distance calculation (< 15ft)
        distance = self.current_position.distance_to(target)
        is_short_distance = distance < 15.0

        # For short distances, base_time already includes reaction time
        # For long distances, we need to add it
        if is_short_distance:
            # Short distance model already includes reaction, just apply range multiplier
            range_multiplier = self.get_effective_range_multiplier()
            # For short plays, range affects the movement portion (subtract reaction, adjust, add back)
            reaction_component = 0.10  # The reaction time built into short-distance model
            movement_component = base_time - reaction_component
            adjusted_movement = movement_component / range_multiplier
            return reaction_component + adjusted_movement
        else:
            # Long distance: add reaction time and apply range multiplier
            reaction_time = self.get_reaction_time_seconds()
            range_multiplier = self.get_effective_range_multiplier()
            adjusted_movement = base_time / range_multiplier
            return reaction_time + adjusted_movement
    
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
        Calculate catch probability using research-based probabilistic model.
        
        Based on Statcast research incorporating:
        - Distance to ball
        - Available time
        - Movement direction (backward penalty)
        - Fielder attributes
        
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
        
        # Base probability for routine plays
        probability = CATCH_PROB_BASE
        
        # Distance penalty: harder plays farther away
        distance_penalty = (distance / 10.0) * CATCH_PROB_DISTANCE_PENALTY
        probability -= distance_penalty
        
        # Time bonus/penalty: more time = higher probability
        time_margin = ball_arrival_time - fielder_time
        if time_margin > 0:
            time_bonus = min(time_margin, 2.0) * CATCH_PROB_TIME_BONUS
            probability += time_bonus
        else:
            # Time deficit - very low probability
            probability *= max(0.1, (1.0 + time_margin / 0.5))  # Severe penalty for late arrival
        
        # Backward movement penalty
        from .constants import BACKWARD_MOVEMENT_PENALTY
        direction_penalty = self.calculate_directional_speed_penalty(movement_vector)
        if direction_penalty == BACKWARD_MOVEMENT_PENALTY:
            probability -= CATCH_PROB_BACKWARD_PENALTY
        
        # Fielder skill adjustments
        # Range affects difficult plays more than easy ones
        if distance > 15.0:  # Difficult play
            range_factor = (self.fielding_range - 50) / 50.0  # -1 to +1
            probability += range_factor * 0.3
        
        # Clamp to valid range
        probability = max(CATCH_PROB_MIN, min(1.0, probability))
        
        return probability

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
        
        # Use research-based catch probability
        catch_probability = self.calculate_catch_probability(ball_position, ball_arrival_time)
        success = np.random.random() < catch_probability
        
        return FieldingResult(
            success=success,
            fielder_arrival_time=effective_fielder_time,
            ball_arrival_time=ball_arrival_time,
            catch_position=ball_position,
            fielder_name=self.name
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
        return (f"Fielder(name='{self.name}', position='{self.position}', "
                f"speed={self.sprint_speed}, arm={self.arm_strength}, "
                f"range={self.fielding_range})")


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
        """Add a fielder at a specific position."""
        # Set fielder to standard position if not already positioned
        if fielder.current_position is None:
            standard_pos = self.field_layout.get_defensive_position(position_name)
            fielder.update_position(standard_pos)
        
        self.fielders[position_name] = fielder
    
    def determine_responsible_fielder(self, ball_position: FieldPosition) -> str:
        """Determine which fielder should attempt to field the ball."""
        return self.field_layout.get_nearest_fielder_position(ball_position)
    
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
        responsible_position = self.determine_responsible_fielder(ball_position)
        
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
                        prob = 0.20 * (fielder.fielding_range / 100.0)
                    else:
                        prob = 0.0
                
                probabilities[pos_name] = prob
                
            except ValueError:
                probabilities[pos_name] = 0.0
        
        return probabilities


# Convenience functions for creating fielders
def create_elite_fielder(name: str, position: str) -> Fielder:
    """Create an elite fielder with high ratings."""
    return Fielder(
        name=name,
        position=position,
        sprint_speed=85,
        acceleration=85,
        reaction_time=85,
        arm_strength=85,
        throwing_accuracy=85,
        transfer_quickness=85,
        fielding_range=85
    )


def create_average_fielder(name: str, position: str) -> Fielder:
    """Create an average fielder with typical ratings."""
    return Fielder(
        name=name,
        position=position,
        sprint_speed=50,
        acceleration=50,
        reaction_time=50,
        arm_strength=50,
        throwing_accuracy=50,
        transfer_quickness=50,
        fielding_range=50
    )


def create_poor_fielder(name: str, position: str) -> Fielder:
    """Create a below-average fielder."""
    return Fielder(
        name=name,
        position=position,
        sprint_speed=30,
        acceleration=30,
        reaction_time=30,
        arm_strength=30,
        throwing_accuracy=30,
        transfer_quickness=30,
        fielding_range=30
    )