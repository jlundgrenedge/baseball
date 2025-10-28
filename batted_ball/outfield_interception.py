"""
Outfield ball interception physics.

Implements realistic outfield fielding by calculating fielder trajectory
intersections with the ball's flight/rolling path, rather than final resting positions.
"""

import numpy as np
import math
from typing import Dict, List, Tuple, Optional
from .field_layout import FieldPosition
from .fielding import Fielder
from .constants import (
    METERS_TO_FEET, FEET_TO_METERS, MPH_TO_MS, MS_TO_MPH,
    GRAVITY
)


class OutfieldInterceptionResult:
    """Result of outfield ball interception analysis."""
    
    def __init__(self):
        self.can_be_fielded = False
        self.fielding_fielder = None
        self.fielding_position = None
        self.interception_time = 0.0
        self.interception_distance = 0.0
        self.ball_position_at_interception = None
        self.fielder_arrival_time = 0.0
        self.time_margin = 0.0  # Positive = fielder has time, negative = ball gets through
        self.interception_type = None  # 'air_catch', 'ground_pickup', 'rolling_stop'


class OutfieldInterceptor:
    """
    Calculates outfield ball interception physics.
    
    For each fielder, determines if and when they can intercept
    a ball during its trajectory or rolling phase.
    """
    
    def __init__(self):
        # Outfield-specific parameters
        self.air_reaction_bonus = 0.2  # Outfielders react faster to fly balls
        self.ground_ball_decel = 15.0  # fps^2 for balls rolling in outfield grass
        
    def find_best_interception(self, batted_ball_result, fielders: Dict[str, Fielder]) -> OutfieldInterceptionResult:
        """
        Find which fielder can best intercept the outfield ball.
        
        Parameters
        ----------
        batted_ball_result : BattedBallResult
            The trajectory result containing ball path
        fielders : Dict[str, Fielder]
            All available fielders
            
        Returns
        -------
        OutfieldInterceptionResult
            Best interception option or failed attempt
        """
        result = OutfieldInterceptionResult()
        
        # Extract trajectory information
        trajectory_data = batted_ball_result.trajectory_data
        if not trajectory_data or len(trajectory_data.get('time', [])) < 2:
            return result
            
        # Convert trajectory data to trajectory points for processing
        # Note: trajectory_data from play_simulation is already in FIELD COORDINATES
        times = trajectory_data['time']
        positions = trajectory_data['position']  # Nx3 array in meters, FIELD COORDS
        velocities = trajectory_data['velocity']  # Nx3 array in m/s, FIELD COORDS

        trajectory = []
        for i in range(len(times)):
            point = type('Point', (), {
                't': times[i],
                'x': positions[i][0] * METERS_TO_FEET,  # Field X (lateral, right +)
                'y': positions[i][1] * METERS_TO_FEET,  # Field Y (forward, CF +)
                'z': positions[i][2] * METERS_TO_FEET   # Field Z (vertical, up +)
            })()
            trajectory.append(point)
            
        # Get ball landing information
        landing_pos = np.array([batted_ball_result.landing_x, batted_ball_result.landing_y])
        ball_time = batted_ball_result.flight_time
        
        # Get ball velocity at landing for rolling calculations
        # Extract final velocity vector from trajectory data
        velocities = trajectory_data['velocity']  # Nx3 array in m/s, FIELD COORDS (already converted)
        final_velocity_ms = velocities[-1]  # Final velocity in m/s, FIELD COORDS

        # Convert to feet per second
        # Note: trajectory_data from play_simulation is already in field coordinates
        final_velocity_field = np.array([
            final_velocity_ms[0] * METERS_TO_FEET,  # Right field positive (already converted)
            final_velocity_ms[1] * METERS_TO_FEET   # Center field positive (already converted)
        ])
        ground_speed_fps = np.linalg.norm(final_velocity_field)
        
        # Search for best fielder option
        best_fielder = None
        best_position = None
        best_margin = float('-inf')
        best_interception_time = 0.0
        best_ball_position = None
        best_fielder_time = 0.0
        best_interception_type = None
        
        for position_name, fielder in fielders.items():
            # Try multiple interception strategies
            interception_options = []
            
            # Option 1: Air catch during flight (if ball is high enough)
            air_option = self._calculate_air_interception(
                trajectory, fielder, position_name
            )
            if air_option:
                interception_options.append((*air_option, 'air_catch'))
            
            # Option 2: Ground pickup at landing spot
            ground_option = self._calculate_ground_interception(
                landing_pos, ground_speed_fps, fielder, ball_time
            )
            if ground_option:
                interception_options.append((*ground_option, 'ground_pickup'))
            
            # Option 3: Intercept rolling ball (for soft hits that keep rolling)
            if ground_speed_fps > 10.0:  # Only if ball has significant rolling speed
                rolling_option = self._calculate_rolling_interception(
                    landing_pos, final_velocity_field, fielder, ball_time
                )
                if rolling_option:
                    interception_options.append((*rolling_option, 'rolling_stop'))
            
            # Find best option for this fielder
            for ball_time_opt, fielder_time_opt, ball_pos_opt, distance_opt, interception_type in interception_options:
                time_margin = fielder_time_opt - ball_time_opt
                
                # Only consider realistic plays (margin >= -0.2 for outfield)
                if time_margin >= -0.2:
                    # Determine if this is better than current best
                    is_better = False
                    
                    if best_fielder is None:
                        is_better = True
                    else:
                        # Priority 1: Outfielders over infielders for outfield balls
                        current_is_outfielder = position_name in ['left_field', 'center_field', 'right_field']
                        best_is_outfielder = best_position in ['left_field', 'center_field', 'right_field']
                        
                        if current_is_outfielder and not best_is_outfielder:
                            is_better = True
                        elif current_is_outfielder == best_is_outfielder:
                            # Priority 2: Earlier interception time (faster play)
                            if ball_time_opt < best_interception_time:
                                is_better = True
                            elif abs(ball_time_opt - best_interception_time) < 0.1:
                                # Priority 3: Better time margin
                                if time_margin > best_margin:
                                    is_better = True
                    
                    if is_better:
                        best_margin = time_margin
                        best_fielder = fielder
                        best_position = position_name
                        best_interception_time = ball_time_opt
                        best_ball_position = ball_pos_opt
                        best_fielder_time = fielder_time_opt
                        best_interception_type = interception_type
        
        # Set result
        if best_fielder is not None and best_margin >= -0.2:  # Allow slight negative margin for outfield
            result.can_be_fielded = True
            result.fielding_fielder = best_fielder
            result.fielding_position = best_position
            result.interception_time = best_interception_time
            result.ball_position_at_interception = FieldPosition(best_ball_position[0], best_ball_position[1], 0.0)
            result.fielder_arrival_time = best_fielder_time
            result.time_margin = best_margin
            result.interception_distance = np.linalg.norm(best_ball_position - landing_pos)
            result.interception_type = best_interception_type
        
        return result
    
    def _calculate_air_interception(self, trajectory: List, fielder: Fielder, 
                                  position_name: str) -> Optional[Tuple[float, float, np.ndarray, float]]:
        """
        Calculate if fielder can catch ball in the air during flight.
        
        Returns
        -------
        tuple or None
            (ball_time, fielder_time, ball_position, distance) or None if impossible
        """
        fielder_pos = np.array([fielder.current_position.x, fielder.current_position.y])
        fielder_speed_fps = self._get_fielder_speed_fps(fielder)
        reaction_time = fielder.get_reaction_time_seconds() - self.air_reaction_bonus
        
        best_option = None
        best_margin = float('-inf')
        
        # Test interception points during flight
        for i, point in enumerate(trajectory):
            if i == 0:
                continue  # Skip contact point
                
            ball_time = point.t
            ball_pos = np.array([point.x, point.y])
            
            # Only consider points where ball is catchable height (z > 2 ft and z < 12 ft)
            if point.z < 2.0 * FEET_TO_METERS or point.z > 12.0 * FEET_TO_METERS:
                continue
            
            # Calculate distance fielder must travel
            distance_to_ball = np.linalg.norm(ball_pos - fielder_pos)
            
            # Calculate fielder arrival time
            fielder_time = reaction_time + distance_to_ball / fielder_speed_fps
            
            time_margin = fielder_time - ball_time
            
            # Track best option
            if time_margin > best_margin and time_margin >= -0.2:
                best_margin = time_margin
                best_option = (ball_time, fielder_time, ball_pos, distance_to_ball)
        
        return best_option
    
    def _calculate_ground_interception(self, landing_pos: np.ndarray, ground_speed_fps: float,
                                     fielder: Fielder, ball_landing_time: float) -> Optional[Tuple[float, float, np.ndarray, float]]:
        """
        Calculate if fielder can field ball at landing spot.
        
        Returns
        -------
        tuple or None
            (ball_time, fielder_time, ball_position, distance) or None if impossible
        """
        fielder_pos = np.array([fielder.current_position.x, fielder.current_position.y])
        fielder_speed_fps = self._get_fielder_speed_fps(fielder)
        reaction_time = fielder.get_reaction_time_seconds()
        
        # Calculate distance fielder must travel to landing spot
        distance_to_landing = np.linalg.norm(landing_pos - fielder_pos)
        
        # Calculate fielder arrival time
        fielder_time = reaction_time + distance_to_landing / fielder_speed_fps
        
        # Ball is available at landing time
        ball_time = ball_landing_time
        
        return (ball_time, fielder_time, landing_pos, distance_to_landing)
    
    def _calculate_rolling_interception(self, landing_pos: np.ndarray, initial_velocity: np.ndarray,
                                      fielder: Fielder, ball_landing_time: float) -> Optional[Tuple[float, float, np.ndarray, float]]:
        """
        Calculate if fielder can intercept ball while it's rolling.
        
        Returns
        -------
        tuple or None
            (ball_time, fielder_time, ball_position, distance) or None if impossible
        """
        fielder_pos = np.array([fielder.current_position.x, fielder.current_position.y])
        fielder_speed_fps = self._get_fielder_speed_fps(fielder)
        reaction_time = fielder.get_reaction_time_seconds()
        
        # Ball rolling parameters
        initial_speed_fps = np.linalg.norm(initial_velocity)
        if initial_speed_fps < 5.0:  # Ball too slow to intercept while rolling
            return None
            
        direction = initial_velocity / initial_speed_fps
        decel_fps2 = self.ground_ball_decel
        
        best_option = None
        best_margin = float('-inf')
        
        # Test interception points along rolling trajectory
        max_test_time = min(3.0, initial_speed_fps / decel_fps2)  # Until ball stops
        test_time = 0.1
        
        while test_time <= max_test_time:
            # Calculate ball position at this time after landing
            current_speed = max(0, initial_speed_fps - decel_fps2 * test_time)
            if current_speed < 1.0:  # Ball essentially stopped
                break
                
            # Distance traveled while rolling
            distance_traveled = initial_speed_fps * test_time - 0.5 * decel_fps2 * test_time**2
            ball_pos = landing_pos + direction * distance_traveled
            
            # Calculate fielder requirements
            distance_to_ball = np.linalg.norm(ball_pos - fielder_pos)
            fielder_time = reaction_time + distance_to_ball / fielder_speed_fps
            ball_time = ball_landing_time + test_time
            
            time_margin = fielder_time - ball_time
            
            if time_margin > best_margin and time_margin >= -0.3:
                best_margin = time_margin
                best_option = (ball_time, fielder_time, ball_pos, distance_to_ball)
            
            test_time += 0.1
        
        return best_option
    
    def _get_fielder_speed_fps(self, fielder: Fielder) -> float:
        """Get fielder's running speed in feet per second."""
        # Convert from fielder speed rating to fps
        # Typical outfielder: 20-28 fps (14-19 mph)
        base_speed = 20.0  # fps
        speed_bonus = (fielder.sprint_speed - 50) * 0.16  # 8 fps range for 50-point rating spread
        return max(15.0, base_speed + speed_bonus)