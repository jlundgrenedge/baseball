"""
Complete baseball play simulation engine.

Integrates trajectory physics, fielding mechanics, and baserunning physics
to simulate complete plays from bat contact to final outcomes with realistic
timing and decision-making.
"""

import math
import numpy as np
from typing import Dict, List, Tuple, Optional, Union
from enum import Enum
from .constants import (
    # Field dimensions
    HOME_PLATE_HEIGHT,
    # Physics constants
    FEET_TO_METERS, METERS_TO_FEET, MPH_TO_MS,
    GRAVITY,
    # Play timing
    CLOSE_PLAY_TOLERANCE, SAFE_RUNNER_BIAS,
    TAG_APPLICATION_TIME, TAG_AVOIDANCE_SUCCESS_RATE,
    GROUND_BALL_AIR_RESISTANCE,
)
from .field_layout import FieldLayout, FieldPosition
from .fielding import (
    Fielder, FieldingSimulator, FieldingResult, ThrowResult,
    simulate_fielder_throw, simulate_relay_throw, determine_cutoff_man,
    RelayThrowResult, RELAY_THROW_THRESHOLD
)
from .baserunning import (
    BaseRunner, BaserunningSimulator, BaserunningResult, RunnerState,
    detect_force_situation, decide_runner_advancement
)
from .trajectory import BattedBallSimulator, BattedBallResult
from .ground_ball_physics import GroundBallSimulator, GroundBallResult
from .ground_ball_interception import GroundBallInterceptor, GroundBallInterceptionResult
from .outfield_interception import OutfieldInterceptor, OutfieldInterceptionResult


class PlayOutcome(Enum):
    """Possible outcomes of a play."""
    FLY_OUT = "fly_out"
    LINE_OUT = "line_out"
    GROUND_OUT = "ground_out"
    FORCE_OUT = "force_out"
    DOUBLE_PLAY = "double_play"
    TRIPLE_PLAY = "triple_play"
    SINGLE = "single"
    DOUBLE = "double"
    TRIPLE = "triple"
    HOME_RUN = "home_run"
    ERROR = "error"
    FIELDERS_CHOICE = "fielders_choice"


class PlayEvent:
    """Represents a single event during a play."""
    
    def __init__(self, time: float, event_type: str, description: str, 
                 positions_involved: List[str] = None):
        """
        Initialize play event.
        
        Parameters
        ----------
        time : float
            Time when event occurred (seconds from contact)
        event_type : str
            Type of event ('catch', 'throw', 'runner_arrival', etc.)
        description : str
            Human-readable description
        positions_involved : List[str], optional
            Fielding positions involved
        """
        self.time = time
        self.event_type = event_type
        self.description = description
        self.positions_involved = positions_involved or []


class PlayResult:
    """Complete result of a play simulation."""
    
    def __init__(self):
        """Initialize empty play result."""
        self.outcome = None
        self.events = []
        self.runs_scored = 0
        self.outs_made = 0
        self.final_runner_positions = {}
        self.batted_ball_result = None
        self.fielding_results = []
        self.baserunning_results = []
        self.play_description = ""
        self.primary_fielder = None  # Fielder who made the primary play
        
    def add_event(self, event: PlayEvent):
        """Add an event to the play."""
        self.events.append(event)
        
    def get_events_chronological(self) -> List[PlayEvent]:
        """Get events sorted by time."""
        return sorted(self.events, key=lambda e: e.time)
    
    def generate_description(self) -> str:
        """Generate a human-readable play description."""
        if not self.events:
            return "No play events recorded"
        
        events = self.get_events_chronological()
        descriptions = [event.description for event in events]
        return ". ".join(descriptions) + "."


class PlaySimulator:
    """
    Main play simulation engine that coordinates all components.
    """
    
    def __init__(self, field_layout: Optional[FieldLayout] = None, surface_type='grass'):
        """
        Initialize play simulator.

        Parameters
        ----------
        field_layout : FieldLayout, optional
            Field layout (creates standard if not provided)
        surface_type : str, optional
            Field surface type: 'grass', 'turf', or 'dirt' (default: 'grass')
        """
        self.field_layout = field_layout or FieldLayout()
        self.fielding_simulator = FieldingSimulator(self.field_layout)
        self.baserunning_simulator = BaserunningSimulator(self.field_layout)
        self.ground_ball_simulator = GroundBallSimulator(surface_type=surface_type)
        self.ground_ball_interceptor = GroundBallInterceptor(surface_type=surface_type)
        self.outfield_interceptor = OutfieldInterceptor()
        self.current_time = 0.0
        self.current_outs = 0  # Track outs for baserunning decisions
        
    def setup_defense(self, fielders: Dict[str, Fielder]):
        """
        Set up defensive alignment.
        
        Parameters
        ----------
        fielders : dict
            Dictionary mapping position names to Fielder objects
        """
        for position, fielder in fielders.items():
            self.fielding_simulator.add_fielder(position, fielder)
    
    def setup_baserunners(self, runners: Dict[str, BaseRunner]):
        """
        Set up baserunners.
        
        Parameters
        ----------
        runners : dict
            Dictionary mapping base names to BaseRunner objects
        """
        for base, runner in runners.items():
            self.baserunning_simulator.add_runner(base, runner)
    
    def simulate_complete_play(self, batted_ball_result: BattedBallResult,
                              batter_runner: BaseRunner,
                              current_outs: int = 0) -> PlayResult:
        """
        Simulate a complete play from batted ball to final outcome.
        
        Parameters
        ----------
        batted_ball_result : BattedBallResult
            Result of batted ball trajectory simulation
        batter_runner : BaseRunner
            The batter becoming a runner
        current_outs : int, optional
            Number of outs before this play (default: 0)
            
        Returns
        -------
        PlayResult
            Complete play simulation result
        """
        result = PlayResult()
        result.batted_ball_result = batted_ball_result
        self.current_time = 0.0
        self.current_outs = current_outs  # Store for use in baserunning decisions
        
        # Add batter-runner to bases
        self.baserunning_simulator.add_runner("home", batter_runner)
        
        # Determine ball landing position and type
        ball_landing_pos, hang_time, is_air_ball = self._analyze_batted_ball(batted_ball_result)
        
        # Add contact event
        result.add_event(PlayEvent(
            0.0, "contact", 
            f"Ball hit to {self._describe_field_location(ball_landing_pos)}"
        ))
        
        if is_air_ball:
            # Simulate catch attempt
            catch_result = self._simulate_catch_attempt(ball_landing_pos, hang_time, result)
            
            if catch_result.success:
                # Ball caught - determine outcome
                self._handle_fly_ball_caught(catch_result, result)
            else:
                # Ball dropped - becomes hit
                self._handle_ball_in_play(ball_landing_pos, hang_time, result)
        else:
            # Ground ball
            self._handle_ground_ball(ball_landing_pos, result)
        
        # Finalize result
        result.play_description = result.generate_description()
        return result
    
    def _analyze_batted_ball(self, batted_ball_result: BattedBallResult) -> Tuple[FieldPosition, float, bool]:
        """Analyze batted ball trajectory to determine key characteristics."""
        from .constants import GROUND_BALL_LAUNCH_ANGLE_MAX

        # Get final position (landing spot)
        landing_pos = FieldPosition(
            batted_ball_result.landing_x,
            batted_ball_result.landing_y,
            0.0  # Ground level
        )

        # Determine hang time and whether it's an air ball
        hang_time = batted_ball_result.flight_time
        max_height = batted_ball_result.peak_height
        launch_angle = batted_ball_result.initial_conditions.get('launch_angle', 0.0)
        distance = batted_ball_result.distance

        # Improved classification logic
        # Consider multiple factors to determine if it's a ground ball vs air ball

        # Factor 1: Launch angle (strong indicator)
        low_launch_angle = launch_angle < GROUND_BALL_LAUNCH_ANGLE_MAX  # < 15 degrees
        very_low_launch = launch_angle < 10.0  # < 10 degrees = definitely ground ball

        # Factor 2: Peak height relative to distance
        # Ground balls have low peak heights relative to distance
        # Typical: ground ball peak height < 5 ft, line drives 5-15 ft, fly balls > 15 ft
        height_to_distance_ratio = max_height / max(distance, 1.0)  # Avoid division by zero
        is_low_trajectory = height_to_distance_ratio < 0.08  # Less than 8% ratio

        # Factor 3: Absolute peak height
        # Very low balls are definitely ground balls
        very_low = max_height < 3.0

        # Factor 4: Short flight time with short distance (weakly hit balls)
        # These should be ground balls near home plate
        weak_hit = distance < 50.0 and hang_time < 1.0

        # Classification decision tree:
        # Very low launch angles (< 10°) are always ground balls
        # BUT: If the ball lands more than 120 ft away, it's likely a line drive
        if very_low_launch:
            # Balls landing far into outfield (>120 ft) are line drives even with low launch angle
            is_air_ball = distance > 120.0
        # Weak hits near home plate with low peak
        elif weak_hit and max_height < 8.0:
            is_air_ball = False
        # Low launch angle (10-15°) with reasonable peak height
        elif low_launch_angle and max_height < 15.0:
            # If the ball is landing deep (>100 ft), treat as air ball for outfielders to catch
            # Infielders shouldn't be chasing balls 100+ feet away
            is_air_ball = distance > 100.0
        # Low trajectory ratio (< 8%) indicates ground ball/line drive
        elif is_low_trajectory and max_height < 12.0:
            # 6-12 ft range with low ratio = hard ground ball or line drive
            # But only if it's in infield range (< 100 ft)
            if distance > 100.0:
                is_air_ball = True  # Outfield line drive
            else:
                is_air_ball = max_height > 8.0  # 8-12 ft = low line drive (catchable)
        else:
            # Everything else is an air ball (fly balls, pop ups, high line drives)
            is_air_ball = max_height > 8.0 or hang_time > 1.5

        return landing_pos, hang_time, is_air_ball
    
    def _get_closest_fielder_distance(self, ball_position: FieldPosition) -> float:
        """Get distance from ball to closest fielder for ground ball roll calculation."""
        min_distance = float('inf')
        
        for fielder in self.fielding_simulator.fielders.values():
            if fielder.current_position:
                distance = fielder.current_position.distance_to(ball_position)
                min_distance = min(min_distance, distance)
        
        return min_distance if min_distance != float('inf') else 100.0  # Default fallback
    
    def _simulate_ground_ball_fielding(self, fielder, ball_position: FieldPosition,
                                       ball_time: float, result: PlayResult,
                                       ground_ball_result: Optional[GroundBallResult] = None):
        """Simulate ground ball fielding and throwing sequence with proper fielder movement physics."""

        # Calculate fielder movement time to ball position (fielder runs while ball rolls)
        fielder_movement_time = fielder.calculate_effective_time_to_position(ball_position)

        # Calculate ball roll time to fielder's interception point
        if ground_ball_result is not None:
            ball_roll_time = ground_ball_result.time_to_target if ground_ball_result.time_to_target is not None else ground_ball_result.total_time
        else:
            # Fallback: estimate roll time based on distance and initial velocity
            # Use realistic ground ball deceleration per research
            distance_to_fielder = self._get_closest_fielder_distance(ball_position)
            initial_velocity = 80.0  # mph estimated ball speed off bat
            initial_velocity_fps = max(initial_velocity * MPH_TO_MS * METERS_TO_FEET, 1e-3)

            # Use realistic ground ball deceleration: 12-15 ft/s²
            # Research: 95 mph ground ball travels ~120 ft in 0.85-1.00s
            decel = 12.0  # ft/s² - realistic for hard-hit ground balls
            
            # Solve: distance = v0*t - 0.5*decel*t^2
            under_sqrt = max(initial_velocity_fps**2 - 2.0 * decel * distance_to_fielder, 0.0)
            ball_roll_time = (initial_velocity_fps - np.sqrt(under_sqrt)) / decel
            ball_roll_time = max(ball_roll_time, 0.3)  # Minimum realistic roll time

        # Fielder can field when BOTH arrive: max(fielder_time, ball_time)
        fielding_moment = ball_time + max(fielder_movement_time, ball_roll_time)

        # Fielding control time (getting ball under control) scales with range quality
        # Research: fielding & exchange should be 0.7-0.9s total
        range_multiplier = fielder.get_effective_range_multiplier()
        base_control_time = 0.3  # Reduced to 0.3s for more realistic timing
        fielding_control_time = max(0.15, min(base_control_time / max(range_multiplier, 1e-3), 0.5))

        # Throwing time to first base using the fielder's throwing profile
        first_base_pos = self.field_layout.get_base_position("first")
        distance_to_first = ball_position.distance_to(first_base_pos)

        throw_velocity_mph = max(fielder.get_throw_velocity_mph(), 1.0)
        throw_velocity_fps = throw_velocity_mph * MPH_TO_MS * METERS_TO_FEET
        transfer_time = fielder.get_transfer_time_seconds()
        flight_time = distance_to_first / throw_velocity_fps
        throw_time = transfer_time + flight_time

        # Total time for ball to reach first base
        ball_arrival_at_first = fielding_moment + fielding_control_time + throw_time

        # Runner time to first base using proper physics
        batter_runner = self.baserunning_simulator.get_runner_at_base("home")
        if batter_runner:
            runner_time_to_first = batter_runner.calculate_time_to_base(
                "home", "first", include_leadoff=False
            )

            # Apply close play tolerance (tie goes to runner)
            time_difference = runner_time_to_first - ball_arrival_at_first

            if time_difference <= -CLOSE_PLAY_TOLERANCE:
                # Runner beats throw easily
                result.outcome = PlayOutcome.SINGLE
                result.add_event(PlayEvent(
                    runner_time_to_first, "infield_single",
                    f"Infield single, beats throw by {abs(time_difference):.2f}s"
                ))
                self._handle_hit_baserunning(result, self.current_outs)
            elif time_difference <= SAFE_RUNNER_BIAS:
                # Close play, tie goes to runner
                result.outcome = PlayOutcome.SINGLE
                result.add_event(PlayEvent(
                    runner_time_to_first, "infield_single",
                    f"Infield single on close play (runner {runner_time_to_first:.2f}s vs ball {ball_arrival_at_first:.2f}s)"
                ))
                self._handle_hit_baserunning(result, self.current_outs)
            else:
                # Ball beats runner - out at first
                result.outcome = PlayOutcome.GROUND_OUT
                result.outs_made = 1
                result.primary_fielder = fielder
                result.add_event(PlayEvent(
                    ball_arrival_at_first, "ground_out",
                    f"Ground out to {fielder.position}, throw beats runner by {time_difference:.2f}s"
                ))
                self.baserunning_simulator.remove_runner("home")
    
    def _attempt_trajectory_interception(self, batted_ball_result: BattedBallResult, result: PlayResult) -> bool:
        """
        Attempt to intercept ball during its flight trajectory.

        Checks ALL fielders at each trajectory point to find who can make the play.
        This allows for realistic scenarios where multiple fielders compete for the ball.

        Returns True if ball was caught/fielded, False if no interception possible.
        """
        # Sample trajectory at multiple time points to find interception opportunities
        flight_time = batted_ball_result.flight_time
        time_steps = 50  # Check 50 points along trajectory (increased for better coverage)
        dt = flight_time / time_steps

        # Debug first few attempts
        debug = False  # Disable debug output
        # if debug:
        #     if not hasattr(self, 'interception_debug_count'):
        #         self.interception_debug_count = 0
        #     self.interception_debug_count += 1
        #     if self.interception_debug_count > 3:
        #         debug = False  # Only debug first 3 balls in play

        # Sample entire trajectory, checking ALL fielders at each point
        # Skip very early trajectory (first 0.15s or 10% of flight) - ball rising too fast near batter
        start_time_threshold = min(0.15, flight_time * 0.10)

        for i in range(1, time_steps):  # Skip t=0 (still at bat)
            t = i * dt

            # Skip very early trajectory when ball is still near batter
            if t < start_time_threshold:
                continue

            # Get ball position at time t
            ball_pos_t = self._calculate_ball_position_at_time(batted_ball_result, t)

            if debug:
                print(f"  t={t:.2f}s: ball at ({ball_pos_t.x:.0f}, {ball_pos_t.y:.0f}, {ball_pos_t.z:.1f}ft)")

            # For catchable fly balls, check throughout descent phase
            # Skip only extremely high balls (>50ft) during first 30% of flight
            # This allows checks for most fly balls while avoiding premature catches near batter
            if ball_pos_t.z > 50.0 and t < flight_time * 0.3:
                if debug:
                    print(f"    SKIP: ball too high ({ball_pos_t.z:.1f}ft) and still rising")
                continue

            # Check ALL fielders to see who can reach this position
            # Store candidates with their time margins
            candidates = []
            all_fielder_times = []  # Track all fielders for debug

            for position_name, fielder in self.fielding_simulator.fielders.items():
                # Calculate fielder movement time to the ground position under the ball
                # Fielders run on the ground (z=0), not through the air!
                ground_position = FieldPosition(ball_pos_t.x, ball_pos_t.y, 0.0)

                # Enable advanced AI pursuit for better fielding intelligence
                USE_ADVANCED_AI = False  # Disable for now - use simpler calculation

                if USE_ADVANCED_AI:
                    # Create trajectory data for advanced AI pursuit methods
                    trajectory_data = self._create_trajectory_data_for_pursuit(batted_ball_result, t)

                    # Use advanced AI pursuit calculation instead of basic method
                    try:
                        # First try optimal intercept calculation
                        optimal_intercept = fielder.calculate_optimal_intercept_point(
                            trajectory_data, current_time=t
                        )

                        # Calculate time to optimal intercept using advanced route calculation
                        intercept_position = FieldPosition(optimal_intercept[0], optimal_intercept[1], 0.0)
                        route_result = fielder.calculate_optimal_route(
                            intercept_position, trajectory_data
                        )

                        # Extract time from route result (route_positions, total_time, efficiency)
                        effective_time = route_result[1] if isinstance(route_result, tuple) else route_result

                    except Exception:
                        # Fallback to basic method if advanced AI fails
                        effective_time = fielder.calculate_effective_time_to_position(ground_position)
                else:
                    # Use basic method - calculate time to reach ground position
                    effective_time = fielder.calculate_effective_time_to_position(ground_position)

                # Time margin = how much time fielder has to spare
                # Fielder needs to arrive before ball at time t (when we're sampling the trajectory)
                # If fielder can get there in less time than it takes ball to reach this point, they can catch it
                time_margin = t - effective_time  # Positive = fielder arrives before ball at this point

                # Use horizontal distance for display (not 3D distance)
                distance = fielder.current_position.horizontal_distance_to(ball_pos_t)

                # Track for debug
                all_fielder_times.append({
                    'position': position_name,
                    'distance': distance,
                    'time_margin': time_margin,
                    'effective_time': effective_time
                })

                # Fielders need to arrive with time to spare to attempt catch
                # Require at least some margin for realistic catches
                # This prevents unrealistic diving catches where fielder barely gets there
                min_margin = 0.05 if distance > 200 else 0.0
                if time_margin >= min_margin:
                    candidates.append({
                        'position': position_name,
                        'fielder': fielder,
                        'time_margin': time_margin,
                        'distance': distance,
                        'effective_time': effective_time
                    })

            # Debug output - show top 3 closest fielders
            if debug and i <= 3:
                all_fielder_times.sort(key=lambda f: f['distance'])
                print(f"    Closest fielders:")
                for finfo in all_fielder_times[:3]:
                    status = "[OK]" if finfo['time_margin'] >= -0.15 else "[X]"
                    print(f"      {finfo['position']}: {finfo['distance']:.0f}ft away, margin={finfo['time_margin']:.2f}s {status}")

            # If we have candidates, pick the best one (most time to spare)
            if candidates:
                # Sort by time margin (descending) - fielder who gets there earliest
                candidates.sort(key=lambda c: c['time_margin'], reverse=True)
                best_candidate = candidates[0]

                fielder = best_candidate['fielder']
                position_name = best_candidate['position']

                # Fielder can intercept! Use probabilistic catch model
                # Catch if ball is above waist height (2.5ft) to allow for low line drive catches
                if ball_pos_t.z > 2.5:  # Air ball catch attempt
                    # ANTI-EXPLOIT: Prevent unrealistic early catches near home plate
                    # Calculate distance from home plate
                    distance_from_home = math.sqrt(ball_pos_t.x**2 + ball_pos_t.y**2)

                    # Skip catches if ball is too close to home AND still early in flight
                    # This prevents fielders from "catching" balls at 0.15-0.6s that are still near the batter
                    # Only allow very close catches for extremely low line drives (z < 3ft) that infielders can grab
                    if distance_from_home < 100.0 and t < 0.6 and ball_pos_t.z > 3.0:
                        if debug:
                            print(f"    {position_name} skipped - ball too close to home ({distance_from_home:.0f}ft) at t={t:.2f}s, z={ball_pos_t.z:.1f}ft")
                        continue

                    # Calculate catch probability using the fielder's model
                    catch_prob = fielder.calculate_catch_probability(ground_position, t)

                    # Roll for success based on probability
                    catch_roll = np.random.random()
                    catch_success = catch_roll < catch_prob

                    if debug:
                        print(f"    {position_name} catch attempt: prob={catch_prob:.2%}, roll={catch_roll:.2f}, {'SUCCESS' if catch_success else 'MISS'}")

                    if catch_success:
                        # Catch made! Log at the actual time when fielder reaches the ball
                        fielder_arrival_time = best_candidate['effective_time']
                        actual_catch_time = max(t, fielder_arrival_time)  # Can't catch before ball arrives
                        
                        result.outcome = PlayOutcome.FLY_OUT
                        result.outs_made = 1
                        result.primary_fielder = fielder
                        result.add_event(PlayEvent(
                            actual_catch_time, "air_catch",
                            f"Caught by {position_name} at {actual_catch_time:.2f}s ({catch_prob:.0%} prob)"
                        ))
                        self.baserunning_simulator.remove_runner("home")
                        
                        # Preserve all existing runners (they stay on their bases after fly out)
                        for base in ["first", "second", "third"]:
                            runner = self.baserunning_simulator.get_runner_at_base(base)
                            if runner:
                                result.final_runner_positions[base] = runner
                        
                        return True
                    else:
                        # Catch attempt failed - ball drops, continue checking other time points
                        # Don't return here, let the ball keep going to see if another fielder can field it
                        if debug:
                            print(f"    {position_name} missed catch (prob was {catch_prob:.0%})")
                        continue
                else:  # Ground ball / line drive fielding
                    if debug:
                        print(f"    {position_name} fielding at t={t:.2f}s, z={ball_pos_t.z:.1f}ft (margin: {best_candidate['time_margin']:.2f}s)")
                    return self._attempt_ground_ball_out(fielder, ball_pos_t, t, result, position_name)

        # No interception possible
        if debug:
            print("    No fielders can intercept")
        return False
    
    def _calculate_ball_position_at_time(self, batted_ball_result: BattedBallResult, t: float) -> FieldPosition:
        """Calculate ball position at time t during flight using actual physics trajectory."""
        # Use actual trajectory data from physics simulation
        time_array = batted_ball_result.time
        position_array = batted_ball_result.position  # Nx3 array in meters

        # Handle edge cases
        if t <= 0:
            # Return initial position
            pos = position_array[0]
            return FieldPosition(
                pos[0] * METERS_TO_FEET,
                pos[1] * METERS_TO_FEET,
                pos[2] * METERS_TO_FEET
            )

        if t >= batted_ball_result.flight_time:
            # Return final position
            pos = position_array[-1]
            return FieldPosition(
                pos[0] * METERS_TO_FEET,
                pos[1] * METERS_TO_FEET,
                max(0.0, pos[2] * METERS_TO_FEET)  # Don't go below ground
            )

        # Find the two time points that bracket t
        idx = np.searchsorted(time_array, t)

        if idx == 0:
            # At or before first point
            pos = position_array[0]
        elif idx >= len(time_array):
            # At or after last point
            pos = position_array[-1]
        else:
            # Interpolate between two points
            t1 = time_array[idx - 1]
            t2 = time_array[idx]
            pos1 = position_array[idx - 1]
            pos2 = position_array[idx]

            # Linear interpolation factor
            alpha = (t - t1) / (t2 - t1)
            pos = pos1 + alpha * (pos2 - pos1)

        # Convert to feet and return
        return FieldPosition(
            pos[0] * METERS_TO_FEET,
            pos[1] * METERS_TO_FEET,
            max(0.0, pos[2] * METERS_TO_FEET)  # Don't go below ground
        )
    
    def _create_trajectory_data_for_pursuit(self, batted_ball_result: BattedBallResult, current_time: float) -> dict:
        """
        Create trajectory data format expected by advanced AI pursuit methods.

        CRITICAL: Converts trajectory coordinates to field coordinates for consistency
        with fielder positions.
        """
        import numpy as np
        from .trajectory import convert_position_trajectory_to_field, convert_velocity_trajectory_to_field

        # Get trajectory arrays from batted ball result (in trajectory coordinates)
        time_array = batted_ball_result.time
        position_array = batted_ball_result.position  # In meters, trajectory coords
        velocity_array = batted_ball_result.velocity  # In m/s, trajectory coords

        # Find current time index
        current_idx = np.searchsorted(time_array, current_time)

        # Create future trajectory from current time onwards
        future_time = time_array[current_idx:]
        future_positions_traj = position_array[current_idx:]  # Trajectory coords
        future_velocities_traj = velocity_array[current_idx:]  # Trajectory coords

        # Convert positions and velocities to field coordinates
        future_positions_field = np.zeros_like(future_positions_traj)
        future_velocities_field = np.zeros_like(future_velocities_traj)

        for i in range(len(future_positions_traj)):
            # Convert position
            x_field, y_field, z_field = convert_position_trajectory_to_field(
                future_positions_traj[i, 0],  # x_traj (toward outfield)
                future_positions_traj[i, 1],  # y_traj (lateral, left +)
                future_positions_traj[i, 2]   # z_traj (vertical)
            )
            future_positions_field[i] = [x_field, y_field, z_field]

            # Convert velocity
            vx_field, vy_field, vz_field = convert_velocity_trajectory_to_field(
                future_velocities_traj[i, 0],  # vx_traj (toward outfield)
                future_velocities_traj[i, 1],  # vy_traj (lateral, left +)
                future_velocities_traj[i, 2]   # vz_traj (vertical)
            )
            future_velocities_field[i] = [vx_field, vy_field, vz_field]

        return {
            'position': future_positions_field,  # Nx3 array in meters, FIELD COORDS
            'velocity': future_velocities_field, # Nx3 array in m/s, FIELD COORDS
            'time': future_time                 # 1D array in seconds
        }
    
    def _attempt_ground_ball_out(self, fielder, ball_position: FieldPosition,
                                catch_time: float, result: PlayResult,
                                position_name: str = None) -> bool:
        """Attempt to field ground ball and throw out runner, checking for force plays and double plays."""
        # Use position name if provided, otherwise use fielder's position attribute
        if position_name is None:
            position_name = fielder.position

        # Calculate time for fielder to reach ball position
        fielder_reach_time = fielder.calculate_effective_time_to_position(ball_position)

        # Fielding control time (getting ball under control) scales with skill
        range_multiplier = fielder.get_effective_range_multiplier()
        fielding_control_time = max(0.25, 0.5 / max(range_multiplier, 1e-3))
        fielding_control_time = min(fielding_control_time, 0.8)  # Cap at 0.8s

        # Total time when fielder has control of ball
        fielding_time = catch_time + max(fielder_reach_time, 0.0) + fielding_control_time

        # Debug: Check baserunner situation
        debug_force = not hasattr(self, 'force_debug_done')
        if debug_force:
            self.force_debug_done = True
            runners = list(self.baserunning_simulator.runners.keys())
            print(f"\n[FORCE DEBUG] Ground ball fielded by {position_name}")
            print(f"  Runners on base: {runners}")

        # Check for force play situations
        force_result = self._attempt_force_play(fielder, ball_position, fielding_time, result)
        
        if debug_force:
            if force_result:
                print(f"  Force play attempted: {force_result}")
            else:
                print(f"  No force situation detected")
        
        if force_result and force_result['success']:
            # We got the force out! Check if double play is possible
            can_attempt_dp = result.outs_made < 2  # Need less than 2 outs for DP
            
            if can_attempt_dp:
                dp_success = self._attempt_double_play(fielder, ball_position, fielding_time, result, force_result)
                
                if dp_success:
                    # Double play!
                    result.outcome = PlayOutcome.DOUBLE_PLAY
                    result.outs_made = 2
                    result.primary_fielder = fielder
                    result.add_event(PlayEvent(
                        fielding_time, "double_play",
                        f"Double play! {position_name} to {force_result['to_base']} to first"
                    ))
                    # Remove both runners (forced runner and batter)
                    self.baserunning_simulator.remove_runner(force_result['from_base'])
                    self.baserunning_simulator.remove_runner("home")
                    
                    # Add any OTHER runners (not involved in the DP) to final positions
                    forced_base = force_result['from_base']
                    for base in ["first", "second", "third"]:
                        if base != forced_base:  # Don't include the two runners who were out
                            other_runner = self.baserunning_simulator.get_runner_at_base(base)
                            if other_runner:
                                result.final_runner_positions[base] = other_runner
                    
                    return True
            
            # Just the force out (no DP or couldn't complete DP)
            result.outcome = PlayOutcome.FORCE_OUT
            result.outs_made = 1
            result.primary_fielder = fielder
            result.add_event(PlayEvent(
                force_result['throw_arrival'], "force_out",
                f"Force out at {force_result['to_base']} ({position_name})"
            ))
            self.baserunning_simulator.remove_runner(force_result['from_base'])
            
            # Batter is safe at first on fielder's choice
            batter_runner = self.baserunning_simulator.get_runner_at_base("home")
            if batter_runner:
                batter_runner.current_base = "first"
                self.baserunning_simulator.remove_runner("home")
                self.baserunning_simulator.add_runner("first", batter_runner)
                result.outcome = PlayOutcome.SINGLE  # Fielder's choice counted as single
                result.final_runner_positions["first"] = batter_runner
                
                # Add any OTHER runners (not involved in the force) to final positions
                # The force_result tells us which runner was out
                forced_base = force_result['from_base']
                for base in ["first", "second", "third"]:
                    if base != forced_base and base != "first":  # Don't duplicate batter, don't include forced runner
                        other_runner = self.baserunning_simulator.get_runner_at_base(base)
                        if other_runner:
                            result.final_runner_positions[base] = other_runner
            
            return True
        
        # No force play - try to throw out batter at first (original logic)
        # Calculate throw time to first base using fielder's actual attributes
        first_base_pos = self.fielding_simulator.field_layout.get_base_position('first')
        throw_distance = ball_position.distance_to(first_base_pos)

        # Use fielder's actual throwing velocity
        throw_velocity_mph = fielder.get_throw_velocity_mph()
        throw_velocity_fps = throw_velocity_mph * MPH_TO_MS * METERS_TO_FEET
        transfer_time = fielder.get_transfer_time_seconds()
        flight_time = throw_distance / throw_velocity_fps
        throw_time = transfer_time + flight_time

        # Total time for ball to reach first base
        ball_arrival_at_first = fielding_time + throw_time

        # Get runner from baserunning simulator and use proper physics
        batter_runner = self.baserunning_simulator.get_runner_at_base("home")
        if not batter_runner:
            # Fallback: create a default runner if none exists
            from .baserunning import create_average_runner
            batter_runner = create_average_runner("Batter")

        runner_time_to_first = batter_runner.calculate_time_to_base(
            "home", "first", include_leadoff=False
        )

        # Apply close play tolerance (tie goes to runner)
        time_difference = runner_time_to_first - ball_arrival_at_first

        # Debug ground ball attempt
        debug = not hasattr(self, 'ground_ball_debug_done')
        if debug:
            self.ground_ball_debug_done = True
            print(f"      GROUND BALL: {position_name} ball_arrival={ball_arrival_at_first:.2f}s vs runner_time={runner_time_to_first:.2f}s")

        if time_difference <= -CLOSE_PLAY_TOLERANCE:
            # Runner beats throw easily
            result.outcome = PlayOutcome.SINGLE
            batter_runner.current_base = "first"
            self.baserunning_simulator.remove_runner("home")
            self.baserunning_simulator.add_runner("first", batter_runner)
            result.final_runner_positions["first"] = batter_runner
            result.add_event(PlayEvent(
                runner_time_to_first, "safe_at_first",
                f"Safe at first, beats throw by {abs(time_difference):.2f}s"
            ))
            self._handle_hit_baserunning(result, self.current_outs)
            if debug:
                print(f"      SAFE AT FIRST (fielded by {position_name})")
            return True
        elif time_difference <= SAFE_RUNNER_BIAS:
            # Close play, tie goes to runner
            result.outcome = PlayOutcome.SINGLE
            result.add_event(PlayEvent(
                runner_time_to_first, "safe_at_first",
                f"Safe at first on close play ({runner_time_to_first:.2f}s vs {ball_arrival_at_first:.2f}s)"
            ))
            self._handle_hit_baserunning(result, self.current_outs)
            if debug:
                print(f"      SAFE AT FIRST on close play (fielded by {position_name})")
            return True
        else:
            # Ball beats runner - out!
            result.outcome = PlayOutcome.GROUND_OUT
            result.outs_made = 1
            result.primary_fielder = fielder
            result.add_event(PlayEvent(
                ball_arrival_at_first, "ground_out",
                f"Ground out to {position_name}, throw beats runner by {time_difference:.2f}s"
            ))
            self.baserunning_simulator.remove_runner("home")
            
            # Preserve all existing runners (they stay on their bases after ground out)
            for base in ["first", "second", "third"]:
                other_runner = self.baserunning_simulator.get_runner_at_base(base)
                if other_runner:
                    result.final_runner_positions[base] = other_runner
            
            if debug:
                print(f"      GROUND OUT to {position_name}!")
            return True
    
    def _attempt_force_play(self, fielder: Fielder, ball_position: FieldPosition,
                           fielding_time: float, result: PlayResult) -> Optional[Dict]:
        """
        Attempt force play at appropriate base.
        
        Returns dict with force play result or None if no force situation.
        """
        from .baserunning import detect_force_situation, get_force_base
        from .fielding import simulate_fielder_throw
        
        # Check if any runners are forced
        forces = detect_force_situation(self.baserunning_simulator.runners, batter_running=True)
        
        # Debug
        debug_force = not hasattr(self, 'force_attempt_debug_done')
        if debug_force:
            self.force_attempt_debug_done = True
            print(f"  [_attempt_force_play] Checking forces...")
            print(f"    Runners: {list(self.baserunning_simulator.runners.keys())}")
            print(f"    Forces detected: {forces}")
        
        if not forces:
            return None  # No force situations
        
        # Determine optimal force play target
        # Priority: Get lead runner (furthest forced runner)
        force_targets = []
        for base, is_forced in forces.items():
            if is_forced:
                target_base = get_force_base(base)
                runner = self.baserunning_simulator.get_runner_at_base(base)
                if runner:
                    force_targets.append((base, target_base, runner))
        
        if not force_targets:
            return None
        
        # Try to get lead runner first (for potential DP)
        # Order: third->home, second->third, first->second
        base_priority = {"third": 3, "second": 2, "first": 1}
        force_targets.sort(key=lambda x: base_priority.get(x[0], 0), reverse=True)
        
        force_result = None
        for from_base, to_base, runner in force_targets:
            # Simulate throw to force base
            throw = simulate_fielder_throw(fielder, ball_position, to_base, self.field_layout)
            
            # Calculate runner arrival time
            runner_time = runner.calculate_time_to_base(from_base, to_base, include_leadoff=False)
            runner_arrival = fielding_time + runner_time
            throw_arrival = fielding_time + throw.arrival_time
            
            # Check if we get the out
            time_diff = runner_arrival - throw_arrival
            if time_diff > 0.1:  # Clear force out
                force_result = {
                    'success': True,
                    'from_base': from_base,
                    'to_base': to_base,
                    'runner': runner,
                    'throw_arrival': throw_arrival,
                    'runner_arrival': runner_arrival,
                    'time_margin': time_diff
                }
                break  # Got the force out
        
        return force_result
    
    def _attempt_double_play(self, fielder: Fielder, ball_position: FieldPosition,
                            fielding_time: float, result: PlayResult,
                            force_result: Dict) -> bool:
        """
        Attempt double play after getting force out.
        
        Parameters
        ----------
        fielder : Fielder
            Fielder who made initial play
        ball_position : FieldPosition
            Where ball was fielded
        fielding_time : float
            When ball was fielded
        result : PlayResult
            Play result to update
        force_result : Dict
            Result from force play attempt
            
        Returns
        -------
        bool
            True if double play completed
        """
        from .fielding import simulate_fielder_throw
        
        # After force out, try to get batter at first
        force_base = force_result['to_base']
        throw1_arrival = force_result['throw_arrival']
        
        # Get pivot fielder at force base
        # For now, assume same fielder makes both plays (simplified)
        # In reality, a different fielder (SS/2B) would receive and relay
        pivot_position = self.field_layout.get_base_position(force_base)
        
        # Simulate relay throw to first
        relay_throw = simulate_fielder_throw(fielder, pivot_position, "first", self.field_layout)
        
        # Add small relay time penalty (fielder needs to catch, turn, throw)
        relay_penalty = 0.3  # 0.3s to receive and relay
        throw2_arrival = throw1_arrival + relay_penalty + relay_throw.arrival_time
        
        # Get batter-runner timing to first
        batter_runner = self.baserunning_simulator.get_runner_at_base("home")
        if not batter_runner:
            return False
        
        batter_time_to_first = batter_runner.calculate_time_to_base("home", "first", include_leadoff=False)
        batter_arrival = fielding_time + batter_time_to_first
        
        # Check if we get batter out at first
        time_diff = batter_arrival - throw2_arrival
        
        if time_diff > 0.1:  # Clear out at first = double play!
            return True
        
        return False
    
    def _determine_hit_type(self, ball_position: FieldPosition, distance_ft: float, result: PlayResult):
        """Determine hit type when no fielder can intercept, with contact quality gates."""
        import numpy as np

        # Get contact quality and exit velocity for gates
        batted_ball = result.batted_ball_result
        peak_height = batted_ball.peak_height if batted_ball else 0

        # Extract contact quality and exit velocity from initial conditions
        contact_quality = batted_ball.initial_conditions.get('contact_quality', 'fair') if batted_ball else 'fair'
        exit_velocity = batted_ball.initial_conditions.get('exit_velocity', 85.0) if batted_ball else 85.0

        # Calculate spray angle for fence determination
        spray_angle = np.arctan2(ball_position.x, ball_position.y) * 180.0 / np.pi
        abs_angle = abs(spray_angle)

        # Determine fence distance based on spray angle
        if abs_angle < 10:  # Dead center
            fence_distance = 400.0
        elif abs_angle < 25:  # Gaps
            fence_distance = 380.0
        elif abs_angle < 40:  # Alleys
            fence_distance = 360.0
        else:  # Down the lines
            fence_distance = 330.0

        # CONTACT QUALITY GATES - Limit outcomes based on contact quality
        # Weak contact (< 80 mph EV) cannot produce extra-base hits beyond singles
        if contact_quality == 'weak' or exit_velocity < 80:
            # Weak contact maxes out at singles
            if distance_ft < 180:
                result.outcome = PlayOutcome.SINGLE
            else:
                # Weak contact far away still just a single (bloop hit)
                result.outcome = PlayOutcome.SINGLE

        # Fair contact (80-95 mph EV) can produce singles and doubles, rare triples
        elif contact_quality == 'fair' or exit_velocity < 95:
            # FIX: Remove peak height restriction - already checked in main HR logic
            # Allow fair contact (85-95 mph) to be HRs if distance is sufficient
            if distance_ft >= fence_distance - 5:  # 5 ft cushion for measurement variance
                result.outcome = PlayOutcome.HOME_RUN
                result.runs_scored = 1
            elif distance_ft > 300 and 10 < abs_angle < 50 and exit_velocity >= 88:
                # Fair contact can produce triples with decent EV in gaps
                result.outcome = PlayOutcome.TRIPLE
            elif distance_ft > 230:
                result.outcome = PlayOutcome.DOUBLE
            else:
                result.outcome = PlayOutcome.SINGLE

        # Solid contact (95+ mph EV) - full range of outcomes
        else:  # solid contact
            # FIX: Remove peak height restriction - already checked in main HR logic
            if distance_ft >= fence_distance - 5:  # 5 ft cushion
                result.outcome = PlayOutcome.HOME_RUN
                result.runs_scored = 1
            # Triples are RARE but achievable - balls in gaps that roll far
            # Require 300+ ft AND in the gap (10-50° angle)
            elif distance_ft > 300 and 10 < abs_angle < 50:
                result.outcome = PlayOutcome.TRIPLE
            # Doubles for well-hit balls to the outfield - lower threshold for more doubles
            elif distance_ft > 230:
                result.outcome = PlayOutcome.DOUBLE
            else:
                result.outcome = PlayOutcome.SINGLE

        self._handle_hit_baserunning(result, self.current_outs)
    
    def _handle_hit_baserunning(self, result: PlayResult, current_outs: int = 0):
        """
        Handle baserunning advancement for hits using realistic decision logic.
        
        This replaces the old simplistic logic (everyone scores on doubles) with
        realistic baserunning decisions based on:
        - Ball location and distance
        - Fielder position and arm strength
        - Runner speed and baserunning ability
        - Number of outs
        - Force situations
        """
        # DEBUG FLAG - set to True to see baserunning decisions
        DEBUG_BASERUNNING = False
        
        # Get batter runner - they might already be on first base
        batter_runner = self.baserunning_simulator.get_runner_at_base("home")
        if not batter_runner:
            # Batter might already have been moved to first - check there
            batter_runner = self.baserunning_simulator.get_runner_at_base("first")
        
        if not batter_runner:
            if DEBUG_BASERUNNING:
                print(f"  [BR] No batter runner found at home or first!")
            return
        
        # Map outcome to hit type for decision logic
        hit_type_map = {
            PlayOutcome.SINGLE: "single",
            PlayOutcome.DOUBLE: "double",
            PlayOutcome.TRIPLE: "triple"
        }
        hit_type = hit_type_map.get(result.outcome)
        if not hit_type:
            return  # Not a hit outcome
        
        # Get ball location from batted ball result
        if result.batted_ball_result:
            ball_location = FieldPosition(
                result.batted_ball_result.landing_x,
                result.batted_ball_result.landing_y,
                0.0
            )
        else:
            # Fallback if no batted ball info
            ball_location = FieldPosition(0.0, 250.0, 0.0)
        
        # Get fielder information
        fielder_position = result.primary_fielder.position if result.primary_fielder else "CF"
        fielder_arm = result.primary_fielder.arm_strength if result.primary_fielder else 50.0
        
        # Determine target base for batter
        base_map = {
            "single": "first",
            "double": "second", 
            "triple": "third"
        }
        batter_base = base_map[hit_type]
        
        # FIRST: Get existing runners BEFORE placing batter (so we don't overwrite them!)
        runners_to_process = []
        for base in ["third", "second", "first"]:
            if base in self.baserunning_simulator.runners:
                runner = self.baserunning_simulator.runners[base]
                if runner != batter_runner:  # Don't process batter again
                    runners_to_process.append((base, runner))
        
        if DEBUG_BASERUNNING:
            print(f"  [BR] Hit type: {hit_type}, Runners to process: {[base for base, _ in runners_to_process]}")
        
        # THEN: Place batter on appropriate base
        if batter_runner.current_base != batter_base:
            batter_runner.current_base = batter_base
            # Remove from wherever they currently are
            if self.baserunning_simulator.get_runner_at_base("home") == batter_runner:
                self.baserunning_simulator.remove_runner("home")
            self.baserunning_simulator.add_runner(batter_base, batter_runner)
        
        result.final_runner_positions[batter_base] = batter_runner
        
        # Handle existing runners with smart decision logic
        # Track which bases will be occupied after all movements
        new_positions = {batter_base: batter_runner}
        runners_to_remove = []
        
        for base, runner in runners_to_process:
            # Get runner's speed and baserunning ratings
            runner_speed = getattr(runner, 'sprint_speed', 50.0)
            runner_br_iq = getattr(runner, 'base_running_iq', 50.0)  # Correct attribute name
            
            # Make baserunning decision
            decision = decide_runner_advancement(
                current_base=base,
                hit_type=hit_type,
                ball_location=ball_location,
                fielder_position=fielder_position,
                fielder_arm_strength=fielder_arm,
                is_fly_ball=False,  # This is only called for hits
                fly_ball_depth=0.0,
                runner_speed_rating=runner_speed,
                runner_baserunning_rating=runner_br_iq,
                is_forced=False,  # Forces are handled separately in force play logic
                outs=current_outs
            )
            
            target_base = decision["target_base"]
            
            if DEBUG_BASERUNNING:
                print(f"  [BR] Runner on {base} -> {target_base} (risk: {decision['risk_level']})")
            
            # If runner scores, increment runs and mark for removal
            if target_base == "home":
                result.runs_scored += 1
                runners_to_remove.append(base)
                if DEBUG_BASERUNNING:
                    print(f"  [BR] -> Runner scores!")
            else:
                # Move runner to new base
                runner.current_base = target_base
                new_positions[target_base] = runner
                runners_to_remove.append(base)  # Remove from old base
        
        # Apply all runner movements
        for base in runners_to_remove:
            self.baserunning_simulator.remove_runner(base)
        
        for base, runner in new_positions.items():
            if runner != batter_runner:  # Batter already added above
                self.baserunning_simulator.add_runner(base, runner)
                result.final_runner_positions[base] = runner
    
    
    def _simulate_catch_attempt(self, ball_position: FieldPosition, 
                               hang_time: float, result: PlayResult) -> FieldingResult:
        """Simulate fielder attempting to catch a fly ball."""
        # ENHANCED LOGGING: Add detailed spatial and fielder analysis
        distance_from_home = np.sqrt(ball_position.x**2 + ball_position.y**2)
        result.add_event(PlayEvent(
            0.0, "fly_ball_analysis",
            f"Fly ball coordinates: ({ball_position.x:.1f}, {ball_position.y:.1f}) ft, distance {distance_from_home:.1f} ft, hang time {hang_time:.2f}s"
        ))
        
        # Determine responsible fielder based on position and capability
        responsible_position = self.fielding_simulator.determine_responsible_fielder(
            ball_position, hang_time
        )
        
        # ENHANCED LOGGING: Show fielder analysis for catch attempt
        self._log_fly_ball_fielder_analysis(ball_position, hang_time, responsible_position, result)
        
        # Simulate fielding attempt - NOTE: This should use the same responsible fielder
        catch_result = self.fielding_simulator.simulate_fielding_attempt(
            ball_position, hang_time
        )
        
        # ENHANCED LOGGING: Check for assignment consistency 
        if hasattr(catch_result, 'fielder_name') and catch_result.fielder_name:
            # Convert position key to display name for comparison
            position_to_display = {
                'left_field': 'Left Field',
                'center_field': 'Center Field', 
                'right_field': 'Right Field',
                'first_base': 'First Base',
                'second_base': 'Second Base',
                'third_base': 'Third Base',
                'shortstop': 'Shortstop',
                'pitcher': 'Pitcher',
                'catcher': 'Catcher'
            }
            expected_display_name = position_to_display.get(responsible_position, responsible_position)
            
            if catch_result.fielder_name != expected_display_name:
                result.add_event(PlayEvent(
                    0.07, "assignment_discrepancy",
                    f"WARNING: Assigned to {responsible_position} but {catch_result.fielder_name} attempted catch"
                ))
        
        result.fielding_results.append(catch_result)
        
        if catch_result.success:
            result.add_event(PlayEvent(
                hang_time, "catch",
                f"Caught by {responsible_position} at {self._describe_field_location(ball_position)}"
            ))
        else:
            result.add_event(PlayEvent(
                hang_time, "ball_drops",
                f"Ball drops in {self._describe_field_location(ball_position)}, {responsible_position} couldn't reach it"
            ))
        
        return catch_result
    
    def _log_fly_ball_fielder_analysis(self, ball_position: FieldPosition, hang_time: float, 
                                     responsible_position: str, result: PlayResult):
        """Log detailed fielder analysis for fly ball attempts."""
        fielder_analyses = []
        distance_from_home = np.sqrt(ball_position.x**2 + ball_position.y**2)
        
        # Determine which fielders to check based on distance and trajectory
        outfielders = ['left_field', 'center_field', 'right_field']
        infielders = ['first_base', 'second_base', 'third_base', 'shortstop', 'pitcher', 'catcher']
        
        # Always check outfielders
        positions_to_check = outfielders.copy()
        
        # Check infielders only for shorter distances or lower trajectories
        # Rule: Check infielders if distance < 250 ft (pop-ups and shallow flies)
        if distance_from_home < 250:
            positions_to_check.extend(infielders)
        
        for pos_name in positions_to_check:
            if pos_name in self.fielding_simulator.fielders:
                fielder = self.fielding_simulator.fielders[pos_name]
                start_pos = fielder.current_position
                distance_to_ball = start_pos.distance_to(ball_position)
                
                # Calculate if this fielder could make the play (simplified)
                reaction_time = fielder.get_reaction_time_seconds()
                available_time = hang_time - reaction_time
                speed_fps = fielder.get_sprint_speed_fps()
                max_travel = speed_fps * available_time if available_time > 0 else 0
                
                can_reach = distance_to_ball <= max_travel
                margin = available_time - (distance_to_ball / speed_fps) if speed_fps > 0 else -999
                
                status = "can reach" if can_reach else "too far"
                fielder_analyses.append(f"{pos_name}: {distance_to_ball:.1f}ft, margin {margin:.2f}s ({status})")
        
        # Log the analysis (limit to avoid overly long output)
        limited_analyses = fielder_analyses[:6]  # Show more fielders for better analysis
        result.add_event(PlayEvent(
            0.05, "fly_ball_fielder_analysis",
            f"Fielder analysis - {'; '.join(limited_analyses)}"
        ))
        
        result.add_event(PlayEvent(
            0.06, "fly_ball_assignment",
            f"Assigned to: {responsible_position}"
        ))
    
    def _handle_fly_ball_caught(self, catch_result: FieldingResult, result: PlayResult):
        """Handle outcome when fly ball is caught."""
        # Batter is out
        result.outs_made = 1
        
        # Check for double play opportunities (runners tagging up late)
        # Simplified: assume runners hold for now
        result.outcome = PlayOutcome.FLY_OUT
        
        # Remove batter-runner
        self.baserunning_simulator.remove_runner("home")
        
        # Preserve all existing runners (they stay on their bases after fly out)
        for base in ["first", "second", "third"]:
            runner = self.baserunning_simulator.get_runner_at_base(base)
            if runner:
                result.final_runner_positions[base] = runner
    
    def _handle_ball_in_play(self, ball_position: FieldPosition,
                            ball_time: float, result: PlayResult):
        """Handle ball in play using trajectory interception logic instead of landing spot racing."""
        import numpy as np

        # ENHANCED LOGGING: Add comprehensive outfield ball analysis
        distance_ft = np.sqrt(ball_position.x**2 + ball_position.y**2)
        batted_ball = result.batted_ball_result
        peak_height = batted_ball.peak_height if batted_ball else 0
        
        result.add_event(PlayEvent(
            ball_time, "outfield_ball_analysis",
            f"Ball in play at ({ball_position.x:.1f}, {ball_position.y:.1f}) ft, distance {distance_ft:.1f} ft, peak height {peak_height:.1f} ft"
        ))

        # Check for home run first (ball clears fence)
        spray_angle = np.arctan2(ball_position.x, ball_position.y) * 180.0 / np.pi
        
        result.add_event(PlayEvent(
            ball_time + 0.01, "trajectory_analysis", 
            f"Spray angle: {spray_angle:.1f}° from center field"
        ))

        # Determine fence distance based on spray angle
        # MLB standard: 325-330 down lines, 375-385 in gaps, 400-410 in center
        abs_angle = abs(spray_angle)
        if abs_angle < 10:  # Dead center (within 10° of straight away)
            fence_distance = 400.0
            fence_height = 10.0
        elif abs_angle < 25:  # Center-left/right gaps
            fence_distance = 380.0
            fence_height = 10.0
        elif abs_angle < 40:  # Deeper alleys
            fence_distance = 360.0
            fence_height = 8.0
        else:  # Down the lines
            fence_distance = 330.0
            fence_height = 8.0

        # Check if ball clears fence (distance + has sufficient height)
        # Need to have peak height above fence height at fence distance
        # Simplified: if distance exceeds fence and peak > fence height, it's a HR
        is_home_run = False
        if distance_ft >= fence_distance:
            # Ball reached fence distance - check if it cleared fence height
            # FIX: Use more realistic height threshold
            # Line drives with 30+ ft peaks can clear 8-10 ft fences
            # Previous 1.5x multiplier (15 ft) was too restrictive
            if peak_height >= 30.0:  # Reasonable minimum for clearing fence
                is_home_run = True
            elif distance_ft >= fence_distance + 15:  # 15 ft past fence = definite HR
                is_home_run = True

        if is_home_run:
            result.outcome = PlayOutcome.HOME_RUN
            result.runs_scored = 1
            result.add_event(PlayEvent(
                ball_time, "home_run",
                f"HOME RUN! Ball travels {distance_ft:.0f} feet over the fence"
            ))
            return

        # Try trajectory interception instead of landing spot racing
        # Allow trajectory interception for all balls - let the individual checks handle fence distance
        if self._attempt_trajectory_interception(batted_ball, result):
            return  # Ball was caught/fielded

        # Try outfield ball interception instead of final position racing
        # BUT: Skip for very deep fly balls (375+ ft) - those are likely HRs or warning track catches
        skip_outfield = distance_ft >= 375.0
        if not skip_outfield:
            interception_result = self.outfield_interceptor.find_best_interception(
                batted_ball, self.fielding_simulator.fielders
            )
        else:
            # For deep fly balls, create a "cannot be fielded" result
            from .outfield_interception import OutfieldInterceptionResult, FieldPosition
            interception_result = OutfieldInterceptionResult()
            interception_result.can_be_fielded = False
            result.add_event(PlayEvent(
                ball_time, "deep_fly_ball",
                f"Ball too deep ({distance_ft:.1f} ft) - skipping outfield interception"
            ))
        
        # ENHANCED LOGGING: Add detailed outfield interception analysis
        self._log_outfield_interception_details(interception_result, ball_position, ball_time, result)
        
        # CRITICAL FIX: If ball was not caught in the air during trajectory interception,
        # it's a HIT. The outfield interception system should ONLY be used for timing
        # how long it takes to retrieve the ball, NOT for making outs/force plays.
        # The ball has already dropped - it's a hit!
        
        # Determine hit type first (this is a hit since trajectory interception failed)
        self._determine_hit_type(ball_position, distance_ft, result)
        
        # Now calculate ball retrieval time for baserunning decisions
        if interception_result.can_be_fielded:
            # Use interception-based timing for how long it takes fielder to run down the ball
            ball_retrieved_time = interception_result.interception_time
            responsible_position = interception_result.fielding_position
            fielder = interception_result.fielding_fielder
            ball_position = interception_result.ball_position_at_interception
            
            location_desc = self._describe_field_location(ball_position)
            result.add_event(PlayEvent(
                ball_retrieved_time, "ball_retrieved",
                f"Ball retrieved by {responsible_position} in {location_desc} at {ball_retrieved_time:.2f}s ({interception_result.interception_type})"
            ))
        else:
            # Fallback timing if interception system fails
            responsible_position = self.fielding_simulator.determine_responsible_fielder(
                ball_position, ball_time
            )
            fielder = self.fielding_simulator.fielders[responsible_position]
            retrieval_time = fielder.calculate_effective_time_to_position(ball_position)
            ball_retrieved_time = ball_time + retrieval_time
            
            location_desc = self._describe_field_location(ball_position)
            result.add_event(PlayEvent(
                ball_retrieved_time, "ball_retrieved",
                f"Ball retrieved by {responsible_position} in {location_desc} at {ball_retrieved_time:.2f}s"
            ))

        # ENHANCED LOGGING: Add detailed baserunning race analysis
        batter_runner = self.baserunning_simulator.get_runner_at_base("home")
        if not batter_runner:
            return  # Safety check

        # Calculate batter runner times to each base (for logging and first base check)
        time_to_first = batter_runner.calculate_time_to_base("home", "first", include_leadoff=False)
        time_to_second = batter_runner.calculate_time_to_base("home", "second", include_leadoff=False)
        time_to_third = batter_runner.calculate_time_to_base("home", "third", include_leadoff=False)
        # Full circuit: home->1st->2nd->3rd->home
        time_to_home = (time_to_first +
                       batter_runner.calculate_time_to_base("first", "second", include_leadoff=False) +
                       batter_runner.calculate_time_to_base("second", "third", include_leadoff=False) +
                       batter_runner.calculate_time_to_base("third", "home", include_leadoff=False))

        # Log batter runner timing analysis
        result.add_event(PlayEvent(
            ball_retrieved_time + 0.01, "baserunning_analysis",
            f"Batter runner times - 1st: {time_to_first:.2f}s, 2nd: {time_to_second:.2f}s, 3rd: {time_to_third:.2f}s, home: {time_to_home:.2f}s"
        ))

        # Calculate fielder throw times to each base (with transfer time)
        # Use relay-aware throws for long distances (>200 ft)
        first_base_pos = self.field_layout.get_base_position("first")
        second_base_pos = self.field_layout.get_base_position("second")
        third_base_pos = self.field_layout.get_base_position("third")
        home_pos = self.field_layout.get_base_position("home")

        # Determine cut-off men for potential relays
        cutoff_for_home = determine_cutoff_man(responsible_position, 'home')
        cutoff_for_third = determine_cutoff_man(responsible_position, 'third')
        cutoff_for_second = determine_cutoff_man(responsible_position, 'second')
        cutoff_for_first = determine_cutoff_man(responsible_position, 'first')

        # Get cut-off men fielders
        cutoff_home_fielder = self.fielding_simulator.fielders.get(cutoff_for_home, fielder)
        cutoff_third_fielder = self.fielding_simulator.fielders.get(cutoff_for_third, fielder)
        cutoff_second_fielder = self.fielding_simulator.fielders.get(cutoff_for_second, fielder)
        cutoff_first_fielder = self.fielding_simulator.fielders.get(cutoff_for_first, fielder)

        # Calculate throws using relay logic (automatically uses relay if distance > 200 ft)
        relay_to_first = simulate_relay_throw(fielder, cutoff_first_fielder, ball_position, 'first', self.field_layout)
        relay_to_second = simulate_relay_throw(fielder, cutoff_second_fielder, ball_position, 'second', self.field_layout)
        relay_to_third = simulate_relay_throw(fielder, cutoff_third_fielder, ball_position, 'third', self.field_layout)
        relay_to_home = simulate_relay_throw(fielder, cutoff_home_fielder, ball_position, 'home', self.field_layout)

        # Log throw analysis with relay information
        relay_info = ""
        if relay_to_home.is_relay:
            relay_info += f" (home via {relay_to_home.cutoff_position})"
        if relay_to_third.is_relay:
            relay_info += f" (3rd via {relay_to_third.cutoff_position})"

        result.add_event(PlayEvent(
            ball_retrieved_time + 0.02, "throw_analysis",
            f"Throw times from {responsible_position} - 1st: {relay_to_first.total_arrival_time:.2f}s, 2nd: {relay_to_second.total_arrival_time:.2f}s, 3rd: {relay_to_third.total_arrival_time:.2f}s, home: {relay_to_home.total_arrival_time:.2f}s{relay_info}"
        ))

        # Ball arrival times at each base (retrieval + throw time)
        ball_at_first = ball_retrieved_time + relay_to_first.total_arrival_time
        ball_at_second = ball_retrieved_time + relay_to_second.total_arrival_time
        ball_at_third = ball_retrieved_time + relay_to_third.total_arrival_time
        ball_at_home = ball_retrieved_time + relay_to_home.total_arrival_time

        # ENHANCED LOGGING: Add detailed race comparison
        result.add_event(PlayEvent(
            ball_retrieved_time + 0.03, "race_analysis",
            f"Ball arrival times - 1st: {ball_at_first:.2f}s, 2nd: {ball_at_second:.2f}s, 3rd: {ball_at_third:.2f}s, home: {ball_at_home:.2f}s"
        ))

        # NEW APPROACH: Determine hit type based on ball location and distance
        # Then use decide_runner_advancement() for existing runners
        # This accounts for each runner's position and the specific situation
        
        # Classify hit type based on distance and field location
        # These thresholds are based on typical MLB outcomes:
        # - 175-250 ft: Usually singles, sometimes doubles to gaps
        # - 250-325 ft: Usually doubles, sometimes triples to gaps
        # - 325+ ft: Usually triples or home runs
        
        # Adjust thresholds based on ball location (gaps allow more advancement)
        is_gap_hit = False
        abs_x = abs(ball_position.x)
        abs_y = ball_position.y
        # Left-center or right-center gap (large X, moderate-deep Y)
        if abs_x > 150 and abs_y > 200:
            is_gap_hit = True
        
        # Determine base hit type for batter
        if distance_ft >= 325:
            # Very deep - likely triple or inside-the-park HR
            # Check if batter can actually make it home
            if time_to_home < ball_at_home - 0.5:  # Good margin for home
                batter_hit_type = "home_run"
                bases_for_batter = 4
            else:
                batter_hit_type = "triple"
                bases_for_batter = 3
        elif distance_ft >= 230 or (distance_ft >= 200 and is_gap_hit):
            # Deep enough for double, or gap hit
            # Check if batter can actually make second base
            if time_to_second < ball_at_second:  # Can make second safely
                batter_hit_type = "double"
                bases_for_batter = 2
            else:
                batter_hit_type = "single"
                bases_for_batter = 1
        else:
            # Standard single range
            # Check if batter beats throw to first
            if time_to_first < ball_at_first - 0.1:  # Safe at first
                batter_hit_type = "single"
                bases_for_batter = 1
            else:
                # Ball beats batter to first - will be handled below
                batter_hit_type = "single"  # Attempt single
                bases_for_batter = 1

        # Log batter decision
        result.add_event(PlayEvent(
            ball_retrieved_time + 0.04, "batter_decision",
            f"Batter: {batter_hit_type} (distance: {distance_ft:.0f}ft, gap: {is_gap_hit})"
        ))

        # FIX: For singles (bases_for_batter == 1), use _handle_hit_baserunning
        # which properly calls decide_runner_advancement() for each runner
        # CRITICAL: Do NOT throw to first on fly balls that drop - these are clean hits!
        # The ball was not caught, so batter should be safe at first
        if bases_for_batter == 1:
            result.outcome = PlayOutcome.SINGLE
            # Let _handle_hit_baserunning handle batter and all runners with smart decisions
            self._handle_hit_baserunning(result, self.current_outs)
                
        # For extra-base hits (doubles, triples, HR), handle runners using decide_runner_advancement
        elif bases_for_batter >= 2:
            # Get existing runners BEFORE moving batter
            existing_runners = []
            for base in ["first", "second", "third"]:
                runner = self.baserunning_simulator.get_runner_at_base(base)
                if runner:
                    existing_runners.append((base, runner))
            
            # Use decide_runner_advancement for each existing runner
            for base, runner in existing_runners:
                # Get runner attributes
                runner_speed = getattr(runner, 'sprint_speed', 50.0)
                runner_br_iq = getattr(runner, 'base_running_iq', 50.0)
                
                # Get fielder arm strength
                fielder_arm = getattr(fielder, 'arm_strength', 50.0)
                
                # Make baserunning decision
                decision = decide_runner_advancement(
                    current_base=base,
                    hit_type=batter_hit_type,  # "double", "triple", or "home_run"
                    ball_location=ball_position,
                    fielder_position=responsible_position,
                    fielder_arm_strength=fielder_arm,
                    is_fly_ball=False,
                    fly_ball_depth=0.0,
                    runner_speed_rating=runner_speed,
                    runner_baserunning_rating=runner_br_iq,
                    is_forced=False,
                    outs=self.current_outs
                )
                
                target_base = decision["target_base"]
                
                # Log runner decision
                result.add_event(PlayEvent(
                    ball_retrieved_time + 0.05, "runner_advancement",
                    f"Runner on {base} -> {target_base} (risk: {decision['risk_level']})"
                ))
                
                # Move runner
                if target_base == "home":
                    result.runs_scored += 1
                    self.baserunning_simulator.remove_runner(base)
                else:
                    runner.current_base = target_base
                    self.baserunning_simulator.remove_runner(base)
                    self.baserunning_simulator.add_runner(target_base, runner)
                    result.final_runner_positions[target_base] = runner
            
            # Now handle the batter
            if bases_for_batter == 4:
                # Inside-the-park home run
                result.outcome = PlayOutcome.HOME_RUN
                result.runs_scored += 1
                self.baserunning_simulator.remove_runner("home")
                result.add_event(PlayEvent(
                    ball_retrieved_time + 0.06, "batter_scores",
                    f"Batter scores on inside-the-park home run!"
                ))
            elif bases_for_batter == 3:
                result.outcome = PlayOutcome.TRIPLE
                batter_runner.current_base = "third"
                self.baserunning_simulator.remove_runner("home")
                self.baserunning_simulator.add_runner("third", batter_runner)
                result.final_runner_positions["third"] = batter_runner
            elif bases_for_batter == 2:
                result.outcome = PlayOutcome.DOUBLE
                batter_runner.current_base = "second"
                self.baserunning_simulator.remove_runner("home")
                self.baserunning_simulator.add_runner("second", batter_runner)
                result.final_runner_positions["second"] = batter_runner
    
    def _handle_ground_ball(self, ball_position: FieldPosition, result: PlayResult):
        """
        Handle ground ball fielding using new interception-based physics.
        
        Uses the corrected ground ball trajectory physics and realistic 
        fielder interception system for accurate timing and assignments.
        """
        batted_ball = result.batted_ball_result
        distance_from_home = np.sqrt(ball_position.x**2 + ball_position.y**2)
        
        # ENHANCED LOGGING: Add detailed spatial information
        result.add_event(PlayEvent(
            0.0, "ground_ball_analysis",
            f"Ground ball coordinates: ({ball_position.x:.1f}, {ball_position.y:.1f}) ft, distance {distance_from_home:.1f} ft from home"
        ))
        
        # Special handling for very weak hits near home plate (bunts, etc.)
        if distance_from_home < 25.0:
            result.add_event(PlayEvent(
                0.3, "weak_hit",
                f"Weakly hit ball near home plate ({distance_from_home:.0f} ft)"
            ))
            
            # Find closest fielder among pitcher, catcher, corner infielders
            potential_fielders = ['pitcher', 'catcher', 'first_base', 'third_base']
            closest_fielder = None
            closest_position = None
            min_distance = float('inf')
            
            # ENHANCED LOGGING: Show all fielder distances for weak hits
            fielder_distances = []
            for pos_name in potential_fielders:
                if pos_name in self.fielding_simulator.fielders:
                    fielder = self.fielding_simulator.fielders[pos_name]
                    dist = fielder.current_position.distance_to(ball_position)
                    fielder_distances.append(f"{pos_name}: {dist:.1f} ft")
                    if dist < min_distance:
                        min_distance = dist
                        closest_fielder = fielder
                        closest_position = pos_name
            
            result.add_event(PlayEvent(
                0.31, "weak_hit_fielder_analysis",
                f"Fielder distances - {', '.join(fielder_distances)}. Closest: {closest_position}"
            ))
            
            if closest_fielder is None:
                result.outcome = PlayOutcome.SINGLE
                # Place batter on first
                batter_runner = self.baserunning_simulator.get_runner_at_base("home")
                if batter_runner:
                    batter_runner.current_base = "first"
                    self.baserunning_simulator.remove_runner("home")
                    self.baserunning_simulator.add_runner("first", batter_runner)
                    result.final_runner_positions["first"] = batter_runner
                return
            
            # Simple fielding for weak hits (quick pickup)
            fielding_time = 0.8 + min_distance / 30.0  # Base time + travel time
            result.add_event(PlayEvent(
                fielding_time, "weak_hit_fielded",
                f"Weak ground ball fielded by {closest_position}"
            ))
            
            # Attempt throw to first
            batter_runner = self.baserunning_simulator.get_runner_at_base("home")
            if batter_runner:
                self._simulate_throw_to_first(closest_fielder, fielding_time, batter_runner, result)
            
            return
        
        # Use new ground ball interception system for normal ground balls
        interception = self.ground_ball_interceptor.find_best_interception(
            batted_ball, self.fielding_simulator.fielders
        )
        
        # ENHANCED LOGGING: Show detailed interception analysis
        self._log_ground_ball_interception_details(interception, ball_position, result)
        
        if not interception.can_be_fielded:
            # Ball gets through the infield
            result.outcome = PlayOutcome.SINGLE
            result.add_event(PlayEvent(
                1.5, "ball_through", 
                f"Ground ball through the infield to ({ball_position.x:.1f}, {ball_position.y:.1f})"
            ))
            self._determine_hit_type(ball_position, distance_from_home, result)
            return
        
        # Ball is fielded successfully
        fielding_time = interception.interception_time
        fielding_position = interception.fielding_position
        interception_pos = interception.ball_position_at_interception
        
        result.add_event(PlayEvent(
            fielding_time, "ground_ball_fielded",
            f"Ground ball fielded by {fielding_position} at ({interception_pos.x:.1f}, {interception_pos.y:.1f}) in {fielding_time:.2f}s"
        ))
        
        # Get the fielder who made the play
        fielder = self.fielding_simulator.fielders[fielding_position]
        
        # Attempt throw to first base
        batter_runner = self.baserunning_simulator.get_runner_at_base("home")
        if batter_runner:
            self._simulate_throw_to_first(fielder, fielding_time, batter_runner, result)
    
    def _log_ground_ball_interception_details(self, interception, ball_position: FieldPosition, result: PlayResult):
        """Log detailed information about ground ball interception analysis."""
        if not interception.can_be_fielded:
            # Show why no fielder could make the play
            result.add_event(PlayEvent(
                0.1, "ground_ball_interception_analysis",
                f"No fielder could intercept ground ball at ({ball_position.x:.1f}, {ball_position.y:.1f})"
            ))
            return
        
        # Show successful interception details
        fielding_pos = interception.fielding_position
        interception_pos = interception.ball_position_at_interception
        time_margin = interception.time_margin
        
        # Calculate fielder's starting position
        fielder = interception.fielding_fielder
        start_pos = fielder.current_position
        travel_distance = start_pos.distance_to(interception_pos)
        
        result.add_event(PlayEvent(
            0.1, "ground_ball_interception_analysis",
            f"Interception: {fielding_pos} travels {travel_distance:.1f} ft from ({start_pos.x:.1f}, {start_pos.y:.1f}) to ({interception_pos.x:.1f}, {interception_pos.y:.1f}), margin +{time_margin:.2f}s"
        ))
    
    def _log_outfield_interception_details(self, interception_result, ball_position: FieldPosition, 
                                         ball_time: float, result: PlayResult):
        """Log detailed information about outfield interception analysis."""
        if not interception_result.can_be_fielded:
            result.add_event(PlayEvent(
                ball_time + 0.02, "outfield_interception_analysis",
                f"No outfield interception possible - ball will reach final position at ({ball_position.x:.1f}, {ball_position.y:.1f})"
            ))
            return
        
        # Show successful interception details
        fielding_pos = interception_result.fielding_position
        interception_pos = interception_result.ball_position_at_interception
        interception_time = interception_result.interception_time
        interception_type = interception_result.interception_type
        time_margin = interception_result.time_margin
        
        # Calculate fielder details
        fielder = interception_result.fielding_fielder
        start_pos = fielder.current_position
        travel_distance = start_pos.distance_to(interception_pos)
        
        result.add_event(PlayEvent(
            ball_time + 0.02, "outfield_interception_analysis",
            f"Outfield interception: {fielding_pos} ({interception_type}) travels {travel_distance:.1f} ft from ({start_pos.x:.1f}, {start_pos.y:.1f}) to ({interception_pos.x:.1f}, {interception_pos.y:.1f}) at {interception_time:.2f}s, margin +{time_margin:.2f}s"
        ))
    
    def _should_throw_to_first(self, ball_time: float, batter_runner: BaseRunner) -> bool:
        """Determine if fielder should throw to first base."""
        if not batter_runner:
            return False
        
        # Calculate if throw has chance to get runner
        runner_time = batter_runner.calculate_time_to_base("home", "first", include_leadoff=False)
        runner_arrival = runner_time
        
        # Estimate throw time (simplified)
        estimated_throw_time = 1.2  # seconds for average throw to first
        ball_arrival_at_first = ball_time + estimated_throw_time
        
        # Only throw if ball will beat runner by reasonable margin
        return ball_arrival_at_first < (runner_arrival - 0.1)
    
    def _simulate_throw_to_first(self, fielder: Fielder, release_time: float,
                                batter_runner: BaseRunner, result: PlayResult):
        """Simulate throw to first base, checking for force plays and double plays."""
        # Get first base position
        first_base_pos = self.field_layout.get_base_position("first")
        
        # Check for force play situations FIRST
        from .baserunning import detect_force_situation, get_force_base
        from .fielding import simulate_fielder_throw
        
        forces = detect_force_situation(self.baserunning_simulator.runners, batter_running=True)
        
        # Debug output
        debug_force_throw = False  # Disabled after validation
        if not hasattr(self, 'force_throw_debug_count'):
            self.force_throw_debug_count = 0
        
        if debug_force_throw and self.force_throw_debug_count < 3:  # Show first 3 ground balls
            self.force_throw_debug_count += 1
            runners_on = [base for base in self.baserunning_simulator.runners.keys() if base != 'home']
            print(f"\n[GROUND BALL #{self.force_throw_debug_count}]")
            print(f"  Runners on base: {runners_on}")
            print(f"  Forces detected: {forces}")
            if forces:
                print(f"  -> Attempting force play...")
        
        if forces:
            # We have a force situation! Try force play
            # We have a force situation! Try force play
            # Determine optimal force play target
            force_targets = []
            for base, is_forced in forces.items():
                if is_forced:
                    target_base = get_force_base(base)
                    runner = self.baserunning_simulator.get_runner_at_base(base)
                    if runner:
                        force_targets.append((base, target_base, runner))
            
            if force_targets:
                # Priority: Get lead runner (furthest forced runner)
                base_priority = {"third": 3, "second": 2, "first": 1}
                force_targets.sort(key=lambda x: base_priority.get(x[0], 0), reverse=True)
                
                from_base, to_base, runner = force_targets[0]
                
                # Get fielder position
                fielder_pos = fielder.current_position
                ball_position = FieldPosition(fielder_pos.x, fielder_pos.y, 0)
                
                # Simulate throw to force base
                throw = simulate_fielder_throw(fielder, ball_position, to_base, self.field_layout)
                
                # Calculate runner arrival time
                runner_time = runner.calculate_time_to_base(from_base, to_base, include_leadoff=False)
                runner_arrival = release_time + runner_time
                throw_arrival = release_time + throw.arrival_time
                
                # Check if we get the force out
                time_diff = runner_arrival - throw_arrival
                if time_diff > 0.1:  # Clear force out
                    # Got the force out!
                    result.add_event(PlayEvent(
                        throw_arrival, "force_out",
                        f"Force out at {to_base} (margin: {time_diff:.2f}s)"
                    ))
                    
                    # Check for double play if less than 2 outs
                    if result.outs_made < 2:
                        # Try to turn double play
                        # Relay throw to first
                        relay_position = self.field_layout.get_base_position(to_base)
                        relay_ball_pos = FieldPosition(relay_position.x, relay_position.y, 0)
                        relay_throw = simulate_fielder_throw(
                            fielder,  # Use original fielder's arm (approximation)
                            relay_ball_pos,
                            "first",
                            self.field_layout
                        )
                        
                        # Relay throw from force base to first
                        # Time breakdown:
                        # 1. throw_arrival = when ball arrives at force base
                        # 2. relay_throw.arrival_time = transfer + flight for relay throw
                        # 3. No additional receive time needed (already in transfer_time)
                        relay_time = throw_arrival + relay_throw.arrival_time
                        
                        # Check if batter is out
                        batter_time_to_first = batter_runner.calculate_time_to_base("home", "first", include_leadoff=False)
                        batter_arrival = batter_time_to_first  # Batter starts running from contact
                        
                        # Allow reasonably close plays (within 1.5s) to sometimes result in DP
                        # This reflects: (1) batter may slow down slightly, (2) close plays favor defense on DP attempts
                        # (3) our ground ball physics may be slightly conservative
                        close_play_tolerance = 1.5
                        time_margin = batter_arrival - relay_time
                        
                        # For very close plays (< 1.5s), success depends on margin
                        if time_margin > -0.2:  # Ball clearly beats runner
                            dp_success = True
                        elif time_margin > -close_play_tolerance:  # Close play
                            # Probability decreases as margin increases
                            # At -0.2s: 100%, at -1.5s: ~20%
                            dp_probability = 1.0 - ((abs(time_margin) - 0.2) / (close_play_tolerance - 0.2)) * 0.8
                            dp_success = np.random.random() < dp_probability
                        else:
                            dp_success = False
                        
                        if dp_success:
                            # Double play!
                            result.outcome = PlayOutcome.DOUBLE_PLAY
                            result.outs_made = 2
                            result.add_event(PlayEvent(
                                relay_time, "double_play",
                                f"Double play! {fielder.position} to {to_base} to first"
                            ))
                            self.baserunning_simulator.remove_runner(from_base)
                            self.baserunning_simulator.remove_runner("home")
                            return
                        else:
                            # Batter beats relay - fall through to force out only
                            pass
                    
                    # Just force out (no DP)
                    result.outcome = PlayOutcome.FORCE_OUT
                    result.outs_made = 1
                    result.primary_fielder = fielder
                    self.baserunning_simulator.remove_runner(from_base)
                    
                    # Batter safe at first on fielder's choice (but outcome stays FORCE_OUT)
                    if batter_runner:
                        batter_runner.current_base = "first"
                        self.baserunning_simulator.remove_runner("home")
                        self.baserunning_simulator.add_runner("first", batter_runner)
                        result.final_runner_positions["first"] = batter_runner
                    
                    # Handle other runners who weren't involved in force play
                    # They should advance based on the situation
                    for base in ["third", "second", "first"]:
                        runner = self.baserunning_simulator.get_runner_at_base(base)
                        if runner and runner != batter_runner and base != from_base:
                            # This runner wasn't forced - do they advance?
                            # On force out at second: runner on 3rd usually stays (close to advancing)
                            # On force out at home/third: other runners advance 1 base
                            if to_base in ["home", "third"]:
                                # Force play further up - other runners advance
                                target = get_force_base(base)
                                runner.current_base = target
                                self.baserunning_simulator.remove_runner(base)
                                if target == "home":
                                    result.runs_scored += 1
                                else:
                                    self.baserunning_simulator.add_runner(target, runner)
                                    result.final_runner_positions[target] = runner
                            # else: runner on base < force play base usually holds
                    
                    return
        
        # No force play or force play failed - throw to first (original logic)
        # Simulate throw
        throw_result = fielder.throw_ball(first_base_pos)
        throw_arrival_time = release_time + throw_result.release_time + throw_result.flight_time
        
        throw_event_time = release_time + throw_result.release_time
        result.add_event(PlayEvent(
            throw_event_time, "throw_to_first",
            ("Throw to first base "
             f"at {throw_result.throw_velocity:.1f} mph (release {throw_event_time:.2f}s, "
             f"flight {throw_result.flight_time:.2f}s)")
        ))
        
        # Calculate runner time to first
        runner_time = batter_runner.calculate_time_to_base("home", "first", include_leadoff=False)
        runner_arrival_time = runner_time
        
        # Determine outcome
        time_difference = runner_arrival_time - throw_arrival_time
        
        if time_difference <= -CLOSE_PLAY_TOLERANCE:
            # Runner beats throw easily
            outcome = "safe"
            result.outcome = PlayOutcome.SINGLE
            batter_runner.current_base = "first"
            self.baserunning_simulator.remove_runner("home")
            self.baserunning_simulator.add_runner("first", batter_runner)
            result.final_runner_positions["first"] = batter_runner
        elif time_difference <= SAFE_RUNNER_BIAS:
            # Close play, tie goes to runner
            outcome = "safe"
            result.outcome = PlayOutcome.SINGLE
            batter_runner.current_base = "first"
            self.baserunning_simulator.remove_runner("home")
            self.baserunning_simulator.add_runner("first", batter_runner)
            result.final_runner_positions["first"] = batter_runner
        else:
            # Ball beats runner
            outcome = "out"
            result.outcome = PlayOutcome.GROUND_OUT
            result.outs_made = 1
            self.baserunning_simulator.remove_runner("home")
        
        result.add_event(PlayEvent(
            max(throw_arrival_time, runner_arrival_time), "play_at_first",
            f"Runner {outcome} at first base (runner {runner_arrival_time:.2f}s vs ball {throw_arrival_time:.2f}s)"
        ))
        
        # Update runner status is now handled above in the outcome determination

    def _estimate_ground_ball_roll_time(self, distance_to_fielder: float,
                                        exit_velocity_fps: float,
                                        physics_time: Optional[float]) -> float:
        """
        Estimate how long a ground ball takes to reach the fielder.

        Research reference (Baseball Simulation Fielding Improvements.md):
        - 95 mph ground ball travels ~120 ft to 3B in 0.85-1.00 seconds
        - This implies relatively low deceleration on ground balls

        Args:
            distance_to_fielder: Distance in feet
            exit_velocity_fps: Initial exit velocity in ft/s (not landing velocity)
            physics_time: Optional physics-based time estimate
        """
        horizontal_speed = max(exit_velocity_fps, 8.0)  # ensure minimal rolling speed

        # Use realistic ground ball deceleration
        # Research shows ~12-15 ft/s² deceleration for hard-hit ground balls
        # This is much lower than the previous calculation
        decel = 12.0  # ft/s² - realistic ground ball deceleration

        max_reachable_distance = (horizontal_speed ** 2) / (2.0 * decel)
        if distance_to_fielder >= max_reachable_distance:
            # Ball would stop before reaching target; use time to stop as upper bound
            estimated_time = horizontal_speed / decel
        else:
            under_sqrt = max(horizontal_speed ** 2 - 2.0 * decel * distance_to_fielder, 0.0)
            estimated_time = (horizontal_speed - math.sqrt(under_sqrt)) / decel

        estimated_time = max(estimated_time, 0.15)

        if physics_time is not None and physics_time > 0:
            # Trust detailed physics when comparable but guard against runaway values
            return min(physics_time, max(estimated_time, physics_time * 0.4))

        return estimated_time
    
    def _describe_field_location(self, position: FieldPosition) -> str:
        """Generate human-readable description of field location."""
        import numpy as np

        x, y = position.x, position.y

        # Calculate total distance from home plate (not just y-coordinate)
        distance = np.sqrt(x**2 + y**2)

        # Calculate spray angle to determine left/center/right
        spray_angle = np.arctan2(x, y) * 180.0 / np.pi  # degrees from center

        # Determine left/center/right
        if spray_angle < -20:
            field_side = "left "
        elif spray_angle > 20:
            field_side = "right "
        else:
            field_side = ""  # center field (no prefix)

        # Determine depth based on total distance
        if distance < 95:
            return "infield"
        elif distance < 180:
            return f"shallow {field_side}outfield"
        elif distance < 280:
            return f"{field_side}outfield"
        elif distance < 360:
            return f"deep {field_side}outfield"
        else:
            return f"warning track / {field_side}wall"
    
    def reset_simulation(self):
        """Reset simulator for new play."""
        self.current_time = 0.0
        self.baserunning_simulator = BaserunningSimulator(self.field_layout)


# Convenience functions for setting up simulations
def create_standard_defense() -> Dict[str, Fielder]:
    """Create a standard defensive alignment with average fielders."""
    from .fielding import create_average_fielder
    
    return {
        'pitcher': create_average_fielder('Pitcher', 'infield'),
        'catcher': create_average_fielder('Catcher', 'infield'),
        'first_base': create_average_fielder('First Base', 'infield'),
        'second_base': create_average_fielder('Second Base', 'infield'),
        'third_base': create_average_fielder('Third Base', 'infield'),
        'shortstop': create_average_fielder('Shortstop', 'infield'),
        'left_field': create_average_fielder('Left Field', 'outfield'),
        'center_field': create_average_fielder('Center Field', 'outfield'),
        'right_field': create_average_fielder('Right Field', 'outfield'),
    }


def create_elite_defense() -> Dict[str, Fielder]:
    """Create an elite defensive alignment."""
    from .fielding import create_elite_fielder
    
    return {
        'pitcher': create_elite_fielder('Elite Pitcher', 'infield'),
        'catcher': create_elite_fielder('Elite Catcher', 'infield'),
        'first_base': create_elite_fielder('Elite First Base', 'infield'),
        'second_base': create_elite_fielder('Elite Second Base', 'infield'),
        'third_base': create_elite_fielder('Elite Third Base', 'infield'),
        'shortstop': create_elite_fielder('Elite Shortstop', 'infield'),
        'left_field': create_elite_fielder('Elite Left Field', 'outfield'),
        'center_field': create_elite_fielder('Elite Center Field', 'outfield'),
        'right_field': create_elite_fielder('Elite Right Field', 'outfield'),
    }


def simulate_play_from_trajectory(batted_ball_result: BattedBallResult,
                                 defense: Dict[str, Fielder],
                                 batter_runner: BaseRunner,
                                 baserunners: Dict[str, BaseRunner] = None) -> PlayResult:
    """
    Convenience function to simulate a complete play.
    
    Parameters
    ----------
    batted_ball_result : BattedBallResult
        Trajectory simulation result
    defense : dict
        Defensive alignment
    batter_runner : BaseRunner
        Batter becoming runner
    baserunners : dict, optional
        Existing baserunners
        
    Returns
    -------
    PlayResult
        Complete play result
    """
    simulator = PlaySimulator()
    simulator.setup_defense(defense)
    
    if baserunners:
        simulator.setup_baserunners(baserunners)
    
    return simulator.simulate_complete_play(batted_ball_result, batter_runner)