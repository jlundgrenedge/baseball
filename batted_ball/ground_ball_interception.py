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
        # Friction coefficients calibrated against MLB ground ball play times
        # A hard-hit ground ball should reach infielders in 1.5-2.5 seconds
        if surface_type == 'grass':
            self.rolling_friction = 0.30  # Natural grass rolling friction
            self.bounce_loss = 0.85       # Velocity retention per bounce
        elif surface_type == 'turf':
            self.rolling_friction = 0.22  # Faster on turf
            self.bounce_loss = 0.90
        else:  # dirt
            self.rolling_friction = 0.35  # Slower on dirt
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
            # Margin: positive = fielder arrives BEFORE ball (good for defense)
            # ball_time is when ball reaches position, fielder_time is when fielder arrives
            # If ball takes 1.5s and fielder takes 1.0s, margin = 1.5 - 1.0 = +0.5s (good)
            time_margin = ball_time - fielder_time
            
            # Only consider fielders who can make the play (margin >= -0.05)
            # Tightened from -0.1 to be more realistic - if the ball beat the fielder there,
            # they usually can't make the play
            if time_margin >= -0.05:
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
        
        # Set result - tightened margin check from -0.1 to -0.05
        if best_fielder is not None and best_margin >= -0.05:
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

        best_option = None
        best_margin = float('-inf')
        best_score = float('-inf')
        
        # =======================================================================
        # SPECIAL CHECK: Ball coming directly at fielder (or close enough to intercept)
        # =======================================================================
        # For balls passing near an infielder's Y-position, check if they can
        # run laterally to intercept it. This handles comebackers to the pitcher
        # and balls hit near (but not directly at) infielders.
        
        # Calculate how close the ball path comes to the fielder (perpendicular distance)
        # Ball path: landing_pos + t * ball_direction
        # Find closest point on ball path to fielder_pos
        to_fielder = fielder_pos - landing_pos
        projection = np.dot(to_fielder, ball_direction)
        
        if projection > 0:  # Ball is moving toward fielder's direction
            closest_point_on_path = landing_pos + projection * ball_direction
            lateral_offset = np.linalg.norm(fielder_pos - closest_point_on_path)
            
            # Calculate when ball reaches this closest point
            distance_ball_travels = projection
            discriminant = ball_speed_fps**2 - 2.0 * decel_fps2 * distance_ball_travels
            
            if discriminant > 0:
                ball_roll_time = (ball_speed_fps - math.sqrt(discriminant)) / decel_fps2
                total_ball_time = flight_time + ball_roll_time
                
                # Calculate fielder time to reach the interception point
                # They need to: react + run laterally + reach for ball
                # Use realistic lateral movement time based on distance
                if lateral_offset <= 3.0:
                    # Very close - just reach/dive
                    lateral_move_time = lateral_offset / 15.0  # Quick lateral movement
                elif lateral_offset <= 8.0:
                    # Moderate distance - run + dive (about 20-25 fps lateral)
                    lateral_move_time = lateral_offset / 22.0
                else:
                    # Far lateral - full sprint (about 28-30 fps for fast fielders)
                    lateral_move_time = self._calculate_fielder_travel_time(lateral_offset, fielder_speed_fps)
                
                total_fielder_time = reaction_time + lateral_move_time
                margin = total_ball_time - total_fielder_time
                
                # Apply position-specific constraints
                can_field_here = True
                if position_name == 'pitcher':
                    # Pitcher can only field near the mound (within ~15 ft)
                    mound_pos = np.array([0.0, 60.5])
                    dist_from_mound = np.linalg.norm(closest_point_on_path - mound_pos)
                    if dist_from_mound > 15.0:
                        can_field_here = False
                    # Also limit lateral range for pitcher (they stay near mound)
                    if lateral_offset > 12.0:
                        can_field_here = False
                
                # Max lateral range for infielders is about 15-20 ft
                max_lateral_range = 18.0  # feet
                if lateral_offset > max_lateral_range:
                    can_field_here = False
                
                if can_field_here and margin >= -0.05:
                    # This is a viable direct-path interception
                    ball_pos = closest_point_on_path
                    best_option = (total_ball_time, total_fielder_time, ball_pos, lateral_offset)
                    best_margin = margin
                    best_score = -lateral_offset  # Prefer shorter lateral distances
        
        # =======================================================================
        # STANDARD CHECK: Test interception points along ball trajectory
        # =======================================================================
        # Test interception points along ball trajectory at different times
        min_test_time = 0.1   # Start testing immediately after landing
        max_test_time = 1.5   # Realistic maximum for infield plays
        time_step = 0.05      # Finer resolution for better accuracy

        test_time = min_test_time
        while test_time <= max_test_time:
            # Calculate ball position at this time
            ball_pos = self._get_ball_position_at_time(landing_pos, ball_direction,
                                                     ball_speed_fps, decel_fps2, test_time)

            # Pitcher special handling - only field balls at positions within 10 feet of mound
            # AND only field balls that are in front of or behind the mound (comebackers),
            # not balls rolling laterally past the mound
            if position_name == 'pitcher':
                mound_pos = np.array([0.0, 60.5])
                interception_distance_from_mound = np.linalg.norm(ball_pos - mound_pos)

                # Restrict to 10 feet from mound (tighter restriction)
                if interception_distance_from_mound > 10.0:
                    test_time += time_step
                    continue

                # Also check lateral distance - pitcher shouldn't field balls > 8 ft to the side
                lateral_distance = abs(ball_pos[0])  # X-coordinate distance from center line
                if lateral_distance > 8.0:
                    test_time += time_step
                    continue

            # Calculate ball speed at this time (for collision timing)
            ball_speed_at_time = max(ball_speed_fps - decel_fps2 * test_time, 1.0)

            # Calculate fielder time to reach this position using REALISTIC acceleration model
            # This is the key fix - fielders don't teleport at top speed!
            distance_to_ball = np.linalg.norm(ball_pos - fielder_pos)
            fielder_movement_time = self._calculate_fielder_travel_time(distance_to_ball, fielder_speed_fps)
            total_fielder_time = reaction_time + fielder_movement_time

            # Total time from contact until ball reaches interception point:
            # ball_time = flight_time (in air) + test_time (rolling)
            total_ball_time = flight_time + test_time
            
            # Fielder arrival time from contact:
            # The fielder reacts at contact and starts moving, NOT waiting for ball to land.
            # So fielder time is just reaction + movement, not flight_time + reaction + movement.
            # NOTE: If reaction_time > flight_time, fielder hasn't finished reacting when ball lands.
            # If reaction_time < flight_time, fielder starts moving while ball is still in air.
            total_fielder_arrival = total_fielder_time  # reaction_time + fielder_movement_time

            # Calculate margin: positive = fielder arrives BEFORE ball (good)
            # ball_time - fielder_time: if ball takes longer, margin is positive (fielder waiting)
            margin = total_ball_time - total_fielder_arrival

            # Track best viable option with scoring based on ball velocity
            # Margin check: require margin >= -0.05s (fielder can be up to 0.05s late)
            # Negative margin means ball arrived first, positive means fielder waiting
            if margin >= -0.05:
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
        """Get fielder TOP SPEED in feet per second (used for long-distance runs).
        
        Note: This is MAX speed. For short distances, use _calculate_fielder_travel_time()
        which accounts for acceleration. Fielders don't hit top speed instantly.
        
        MLB Statcast sprint speed reference:
        - Elite (90th percentile): ~30 ft/s (20.5 mph)
        - Average (50th percentile): ~27 ft/s (18.4 mph)  
        - Poor (10th percentile): ~24 ft/s (16.4 mph)
        """
        # Use the proper method on Fielder class
        return fielder.get_sprint_speed_fps()
    
    def _calculate_fielder_travel_time(self, distance: float, max_speed_fps: float) -> float:
        """
        Calculate time for fielder to cover distance, accounting for acceleration.
        
        Fielders don't instantly hit top speed - they need to accelerate from a
        standing start. This model uses realistic acceleration physics.
        
        Research basis:
        - Elite athletes accelerate at ~10-15 ft/s² from standing start
        - MLB infielders typically accelerate at ~12 ft/s²
        - It takes ~2-2.5 seconds to reach full sprint speed
        
        For short distances (typical infield plays of 10-40 ft), fielders never
        reach top speed, so the "average speed" model is more accurate.
        
        Parameters
        ----------
        distance : float
            Distance to cover in feet
        max_speed_fps : float
            Maximum (top) speed in ft/s
            
        Returns
        -------
        float
            Time in seconds to cover the distance
        """
        # Acceleration for infielder from ready position
        # Baseball players start from an athletic ready stance, allowing faster
        # acceleration than a cold start. Research suggests ~25-30 fps² is realistic.
        # This gives: 20ft in ~1.3s, 30ft in ~1.6s - matching observed fielding times
        acceleration = 28.0  # ft/s² - calibrated for realistic fielding
        
        # Distance to reach top speed: d = v²/(2a)
        distance_to_max_speed = (max_speed_fps ** 2) / (2.0 * acceleration)
        
        if distance <= distance_to_max_speed:
            # Fielder never reaches top speed - entire journey is accelerating
            # Using: d = 0.5 * a * t², solve for t: t = sqrt(2d/a)
            time = math.sqrt(2.0 * distance / acceleration)
        else:
            # Fielder accelerates to top speed, then runs at constant speed
            # Time to reach top speed: t = v/a
            time_to_max_speed = max_speed_fps / acceleration
            
            # Remaining distance at top speed
            remaining_distance = distance - distance_to_max_speed
            time_at_max_speed = remaining_distance / max_speed_fps
            
            time = time_to_max_speed + time_at_max_speed
        
        return time
    
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