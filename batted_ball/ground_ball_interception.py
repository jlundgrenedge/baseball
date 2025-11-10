"""
Ground ball interception physics.

Implements realistic ground ball fielding by calculating fielder trajectory
intersections with the rolling ball path, rather than final resting positions.

COORDINATE SYSTEM:
This module uses FIELD COORDINATES exclusively for positions and velocities:
- X-axis: Lateral (positive = RIGHT field, negative = LEFT field)
- Y-axis: Forward direction (positive = toward CENTER field)
- Z-axis: Vertical (positive = up)

Velocities from BattedBallResult are converted from trajectory coordinates
to field coordinates using convert_velocity_trajectory_to_field() at the entry
point (find_best_interception) to ensure consistency throughout calculations.
"""

import numpy as np
import math
from typing import Dict, List, Tuple, Optional
from .field_layout import FieldPosition
from .fielding import Fielder
from .constants import (
    METERS_TO_FEET, FEET_TO_METERS, MPH_TO_MS, MS_TO_MPH,
    GRAVITY, GROUND_BALL_AIR_RESISTANCE
)
from .trajectory import convert_velocity_trajectory_to_field


class GroundBallInterceptionResult:
    """Result of ground ball interception analysis."""
    
    def __init__(self):
        self.can_be_fielded = False
        self.fielding_fielder = None
        self.fielding_position = None
        self.interception_time = 0.0
        self.interception_distance = 0.0
        self.ball_position_at_interception = None
        self.fielder_arrival_time = 0.0
        self.time_margin = 0.0  # Positive = fielder has time, negative = ball gets through


class GroundBallInterceptor:
    """
    Calculates ground ball interception physics.
    
    For each fielder, determines if and when they can intercept
    a ground ball along its rolling trajectory.
    """
    
    def __init__(self, surface_type='grass'):
        self.surface_type = surface_type
        
        # Ground ball deceleration parameters
        if surface_type == 'grass':
            self.rolling_friction = 0.08  # Rolling friction coefficient
            self.bounce_loss = 0.85       # Velocity retention per bounce
        elif surface_type == 'turf':
            self.rolling_friction = 0.06  # Faster on turf
            self.bounce_loss = 0.90
        else:  # dirt
            self.rolling_friction = 0.12  # Slower on dirt
            self.bounce_loss = 0.75
    
    def find_best_interception(self, batted_ball_result, fielders: Dict[str, Fielder]) -> GroundBallInterceptionResult:
        """
        Find which fielder can best intercept the ground ball.

        Parameters
        ----------
        batted_ball_result : BattedBallResult
            Trajectory result with landing position and velocity
        fielders : dict
            Available fielders by position name

        Returns
        -------
        GroundBallInterceptionResult
            Best interception scenario (or none if ball gets through)
        """
        result = GroundBallInterceptionResult()

        # Get ground ball initial conditions
        landing_pos = np.array([batted_ball_result.landing_x, batted_ball_result.landing_y])

        # Extract landing velocity (still in trajectory coordinates - m/s)
        landing_velocity_traj = batted_ball_result.velocity[-1]  # m/s in trajectory coords

        # Convert velocity from trajectory coordinates to field coordinates
        # This is CRITICAL: trajectory uses (x=outfield, y=lateral), field uses (x=lateral, y=forward)
        vx_field_ms, vy_field_ms, vz_field_ms = convert_velocity_trajectory_to_field(
            landing_velocity_traj[0], landing_velocity_traj[1], landing_velocity_traj[2]
        )

        # Now use field-coordinate velocity for direction
        landing_velocity_field = np.array([vx_field_ms, vy_field_ms, vz_field_ms])

        # Convert to feet and mph for ground ball physics
        ball_speed_mph = np.linalg.norm(landing_velocity_field[:2]) * MS_TO_MPH  # Horizontal speed only
        ball_direction = landing_velocity_field[:2] / max(np.linalg.norm(landing_velocity_field[:2]), 1e-6)

        # Get exit velocity for fielding strategy
        exit_velocity_mph = batted_ball_result.exit_velocity * MS_TO_MPH  # Convert from m/s to mph

        # Calculate ground ball trajectory parameters
        ball_speed_fps = ball_speed_mph * MPH_TO_MS * METERS_TO_FEET
        decel_fps2 = GRAVITY * METERS_TO_FEET * self.rolling_friction + GROUND_BALL_AIR_RESISTANCE

        best_margin = float('-inf')
        best_fielder = None
        best_position = None
        best_interception_time = 0.0
        best_ball_position = None
        best_fielder_time = 0.0

        # Test each fielder for interception capability
        for position_name, fielder in fielders.items():
            if fielder.current_position is None:
                continue

            # Calculate optimal interception for this fielder
            interception_data = self._calculate_fielder_interception(
                landing_pos, ball_direction, ball_speed_fps, decel_fps2,
                fielder, batted_ball_result.flight_time, position_name, exit_velocity_mph
            )

            if interception_data is None:
                continue  # Fielder cannot intercept

            ball_time, fielder_time, ball_pos, distance = interception_data
            time_margin = fielder_time - ball_time
            
            # Only consider fielders who can make the play (margin >= -0.1)
            if time_margin >= -0.1:
                # Prioritize by fielder appropriateness and distance
                is_better = False
                
                if best_fielder is None:
                    is_better = True
                else:
                    # Priority 1: Infielders over outfielders for ground balls
                    current_is_infielder = position_name in ['pitcher', 'catcher', 'first_base', 'second_base', 'third_base', 'shortstop']
                    best_is_infielder = best_position in ['pitcher', 'catcher', 'first_base', 'second_base', 'third_base', 'shortstop']
                    
                    if current_is_infielder and not best_is_infielder:
                        is_better = True
                    elif current_is_infielder == best_is_infielder:
                        # Priority 2: Among same type, prefer shorter distance (faster play)
                        current_distance = np.linalg.norm(ball_pos - np.array([fielder.current_position.x, fielder.current_position.y]))
                        best_distance = np.linalg.norm(best_ball_position - np.array([best_fielder.current_position.x, best_fielder.current_position.y]))
                        
                        if current_distance < best_distance:
                            is_better = True
                
                if is_better:
                    best_margin = time_margin
                    best_fielder = fielder
                    best_position = position_name
                    best_interception_time = ball_time
                    best_ball_position = ball_pos
                    best_fielder_time = fielder_time
        
        # Set result
        if best_fielder is not None and best_margin >= -0.1:  # Allow slight negative margin
            result.can_be_fielded = True
            result.fielding_fielder = best_fielder
            result.fielding_position = best_position
            result.interception_time = best_interception_time
            result.ball_position_at_interception = FieldPosition(best_ball_position[0], best_ball_position[1], 0.0)
            result.fielder_arrival_time = best_fielder_time
            result.time_margin = best_margin
            result.interception_distance = np.linalg.norm(best_ball_position - landing_pos)
        
        return result
    
    def _calculate_fielder_interception(self, landing_pos: np.ndarray, ball_direction: np.ndarray,
                                      ball_speed_fps: float, decel_fps2: float,
                                      fielder: Fielder, flight_time: float, position_name: str,
                                      exit_velocity_mph: float) -> Optional[Tuple[float, float, np.ndarray, float]]:
        """
        Calculate optimal interception point for a specific fielder.

        On hard-hit balls, fielders let the ball come to them.
        On weak hits, fielders can charge forward aggressively.

        Returns
        -------
        tuple or None
            (ball_time, fielder_time, ball_position, distance) or None if impossible
        """
        fielder_pos = np.array([fielder.current_position.x, fielder.current_position.y])

        # Pitcher special handling - only field balls within 20 feet of mound
        # This ensures pitchers only field comebackers and balls hit near the mound,
        # while balls to the sides go to appropriate infielders (1B, 2B, 3B, SS)
        if position_name == 'pitcher':
            ball_distance_from_mound = np.linalg.norm(landing_pos - np.array([0.0, 60.5]))
            if ball_distance_from_mound > 20.0:  # Pitcher only fields balls within 20 feet of mound
                return None

        # Special handling for catcher - they can only field very short balls
        # since they're positioned behind home plate facing forward
        if position_name == 'catcher':
            # Catcher can only field balls very close to home plate (< 15 ft)
            ball_distance_from_home = np.linalg.norm(landing_pos)
            if ball_distance_from_home > 15.0:  # 15 feet cutoff
                return None  # Catcher can't field balls this far out

            # For very short balls, catcher needs to run forward to field them
            # Check if ball is moving away from catcher (positive Y direction)
            if ball_direction[1] > 0 and np.dot(ball_direction, landing_pos) > 0:
                # Ball is moving away from catcher - they'd be chasing it from behind
                # Only allow if it's very close and slow
                if ball_distance_from_home > 10.0 or ball_speed_fps > 30.0:
                    return None

        # Get fielder capabilities
        fielder_speed_fps = self._get_fielder_speed_fps(fielder)
        reaction_time = fielder.get_reaction_time_seconds()

        # Determine fielding strategy based on exit velocity
        # Hard-hit balls (> 85 mph): Let the ball come to you
        # Medium (70-85 mph): Moderate approach
        # Weak hits (< 70 mph): Can charge aggressively
        is_hard_hit = exit_velocity_mph > 85.0
        is_weak_hit = exit_velocity_mph < 70.0

        # Test interception points along ball trajectory at different times
        min_test_time = 0.1   # Start testing immediately after landing
        max_test_time = 1.5   # Realistic maximum for infield plays
        time_step = 0.05      # Finer resolution for better accuracy

        best_option = None
        best_margin = float('-inf')
        best_score = float('-inf')

        test_time = min_test_time
        while test_time <= max_test_time:
            # Calculate ball position at this time
            ball_pos = self._get_ball_position_at_time(landing_pos, ball_direction,
                                                     ball_speed_fps, decel_fps2, test_time)

            # Calculate ball speed at this time (for collision timing)
            ball_speed_at_time = max(ball_speed_fps - decel_fps2 * test_time, 1.0)

            # Calculate fielder time to reach this position
            distance_to_ball = np.linalg.norm(ball_pos - fielder_pos)
            fielder_movement_time = distance_to_ball / fielder_speed_fps
            total_fielder_time = reaction_time + fielder_movement_time

            # Total time from contact: flight_time + test_time
            total_ball_time = flight_time + test_time
            total_fielder_arrival = flight_time + total_fielder_time

            # Calculate margin (positive = fielder arrives first)
            margin = total_fielder_arrival - total_ball_time

            # Track best viable option with scoring based on ball velocity
            if margin >= -0.1:  # Tighter tolerance for realistic plays
                # Calculate score based on fielding strategy
                if is_hard_hit:
                    # For hard-hit balls: Prefer interceptions CLOSER to fielder's position
                    # This makes fielders "let the ball come to them"
                    score = -distance_to_ball  # Lower distance = higher score
                elif is_weak_hit:
                    # For weak hits: Prefer earlier interceptions (charge forward)
                    score = -total_ball_time
                else:
                    # Medium velocity: Balance between distance and time
                    score = -distance_to_ball * 0.5 - total_ball_time * 0.5

                # Update best option if this is better
                if best_option is None or score > best_score:
                    best_option = (total_ball_time, total_fielder_arrival, ball_pos, distance_to_ball)
                    best_margin = margin
                    best_score = score

            test_time += time_step

        return best_option
    
    def _get_ball_position_at_time(self, landing_pos: np.ndarray, direction: np.ndarray,
                                  initial_speed_fps: float, decel_fps2: float, time: float) -> np.ndarray:
        """
        Calculate ball position at specific time after landing.
        
        Uses kinematic equation: x = x0 + v0*t - 0.5*a*t^2
        """
        # Distance traveled with deceleration
        distance = initial_speed_fps * time - 0.5 * decel_fps2 * time**2
        distance = max(distance, 0.0)  # Ball can't go backwards
        
        # Position along trajectory
        ball_pos = landing_pos + direction * distance
        return ball_pos
    
    def _get_fielder_speed_fps(self, fielder: Fielder) -> float:
        """Get fielder movement speed in feet per second."""
        # Use fielder's sprint speed rating to determine fps
        # Average MLB fielder: ~27 ft/s, Elite: ~30 ft/s, Poor: ~24 ft/s
        
        sprint_rating = getattr(fielder, 'sprint_speed', 50)  # Default to average
        
        if sprint_rating >= 80:
            return 30.0  # Elite speed
        elif sprint_rating >= 60:
            return 24.0 + (sprint_rating - 60) * 0.3  # 24-30 fps range
        elif sprint_rating >= 40:
            return 20.0 + (sprint_rating - 40) * 0.2  # 20-24 fps range  
        else:
            return max(18.0, 16.0 + sprint_rating * 0.05)  # 16-20 fps range
    
    def get_ground_ball_trajectory_points(self, batted_ball_result, max_time: float = 3.0) -> List[Tuple[float, float, float]]:
        """
        Get trajectory points for visualization/debugging.
        
        Returns list of (time, x, y) tuples showing ball position over time.
        """
        landing_pos = np.array([batted_ball_result.landing_x, batted_ball_result.landing_y])
        
        # Extract landing velocity (in trajectory coordinates)
        landing_velocity_traj = batted_ball_result.velocity[-1]
        
        # Convert to field coordinates
        vx_field_ms, vy_field_ms, vz_field_ms = convert_velocity_trajectory_to_field(
            landing_velocity_traj[0], landing_velocity_traj[1], landing_velocity_traj[2]
        )
        landing_velocity_field = np.array([vx_field_ms, vy_field_ms, vz_field_ms])
        
        ball_speed_mph = np.linalg.norm(landing_velocity_field[:2]) * MS_TO_MPH
        ball_direction = landing_velocity_field[:2] / max(np.linalg.norm(landing_velocity_field[:2]), 1e-6)
        ball_speed_fps = ball_speed_mph * MPH_TO_MS * METERS_TO_FEET
        decel_fps2 = GRAVITY * METERS_TO_FEET * self.rolling_friction + GROUND_BALL_AIR_RESISTANCE
        
        points = []
        time_step = 0.1
        time = 0.0
        
        while time <= max_time:
            pos = self._get_ball_position_at_time(landing_pos, ball_direction, ball_speed_fps, decel_fps2, time)
            points.append((time, pos[0], pos[1]))
            
            # Stop if ball speed is very low
            speed_at_time = max(ball_speed_fps - decel_fps2 * time, 0.0)
            if speed_at_time < 5.0 and time > 1.0:
                break
                
            time += time_step
        
        return points