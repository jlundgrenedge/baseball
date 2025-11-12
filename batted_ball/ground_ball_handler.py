"""
Ground ball handling module for baseball play simulation.

Contains logic for handling ground ball fielding, including interception analysis,
fielding timing, throwing sequences, and ground ball roll calculations.
"""

import math
import numpy as np
from typing import Dict, List, Tuple, Optional

from .constants import (
    # Physics constants
    METERS_TO_FEET, MPH_TO_MS,
    # Play timing
    CLOSE_PLAY_TOLERANCE, SAFE_RUNNER_BIAS,
)
from .field_layout import FieldPosition
from .fielding import Fielder
from .ground_ball_physics import GroundBallResult
from .play_outcome import PlayEvent, PlayOutcome


class GroundBallHandler:
    """
    Handles all ground ball fielding scenarios including:
    - Ground ball interception and fielding
    - Fielding timing calculations
    - Throw attempts and out determinations
    - Ground ball roll time estimation
    """

    def __init__(self, field_layout, fielding_simulator, baserunning_simulator,
                 ground_ball_simulator, ground_ball_interceptor, current_outs: int,
                 hit_handler=None, throwing_logic=None):
        """
        Initialize ground ball handler.

        Parameters
        ----------
        field_layout : FieldLayout
            Field layout for position calculations
        fielding_simulator : FieldingSimulator
            Fielding simulator for fielder access
        baserunning_simulator : BaserunningSimulator
            Baserunning simulator for runner management
        ground_ball_simulator : GroundBallSimulator
            Ground ball physics simulator
        ground_ball_interceptor : GroundBallInterceptor
            Ground ball interception system
        current_outs : int
            Current number of outs
        hit_handler : HitHandler, optional
            Reference to hit handler for hit baserunning
        throwing_logic : ThrowingLogic, optional
            Reference to throwing logic for throw simulations
        """
        self.field_layout = field_layout
        self.fielding_simulator = fielding_simulator
        self.baserunning_simulator = baserunning_simulator
        self.ground_ball_simulator = ground_ball_simulator
        self.ground_ball_interceptor = ground_ball_interceptor
        self.current_outs = current_outs
        self.hit_handler = hit_handler
        self.throwing_logic = throwing_logic

    def handle_ground_ball(self, ball_position: FieldPosition, result):
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
        # Only treat as weak hit if BOTH conditions are met:
        # 1. Very close to home plate (< 15 ft)
        # 2. Low exit velocity (< 65 mph) - this distinguishes bunts/topped balls from hard grounders
        exit_velocity_mph = batted_ball.exit_velocity * 3.6 * 0.621371  # m/s to mph
        is_weak_hit = distance_from_home < 15.0 and exit_velocity_mph < 65.0

        if is_weak_hit:
            result.add_event(PlayEvent(
                0.3, "weak_hit",
                f"Weakly hit ball near home plate ({distance_from_home:.0f} ft, EV {exit_velocity_mph:.1f} mph)"
            ))

            # Find closest fielder among pitcher, catcher, corner infielders
            # IMPORTANT: Catcher can only field balls hit behind or very near home plate
            # since they're positioned behind the plate facing forward
            potential_fielders = ['pitcher', 'catcher', 'first_base', 'third_base']

            # Check if ball is in front of home plate (going away from catcher)
            ball_is_in_front = ball_position.y > 5.0  # More than 5 ft in front of home plate

            # If ball is clearly in front of home plate, exclude catcher
            if ball_is_in_front:
                potential_fielders = ['pitcher', 'first_base', 'third_base']

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
                # Let handle_hit_baserunning place the batter and advance all runners
                if self.hit_handler:
                    self.hit_handler.handle_hit_baserunning(result, self.current_outs)
                else:
                    # Fallback if no hit handler
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
            if batter_runner and self.throwing_logic:
                self.throwing_logic.simulate_throw_to_first(closest_fielder, fielding_time, batter_runner, result)
            else:
                # Fallback: if no batter runner or throwing logic, default to single
                result.outcome = PlayOutcome.SINGLE
                # Let handle_hit_baserunning place the batter and advance all runners
                if self.hit_handler:
                    self.hit_handler.handle_hit_baserunning(result, self.current_outs)
                elif batter_runner:
                    # Last resort fallback if no hit_handler
                    batter_runner.current_base = "first"
                    self.baserunning_simulator.remove_runner("home")
                    self.baserunning_simulator.add_runner("first", batter_runner)
                    result.final_runner_positions["first"] = batter_runner

            return

        # Use new ground ball interception system for normal ground balls
        interception = self.ground_ball_interceptor.find_best_interception(
            batted_ball, self.fielding_simulator.fielders
        )

        # ENHANCED LOGGING: Show detailed interception analysis
        self.log_ground_ball_interception_details(interception, ball_position, result)

        if not interception.can_be_fielded:
            # Ball gets through the infield
            result.outcome = PlayOutcome.SINGLE
            result.add_event(PlayEvent(
                1.5, "ball_through",
                f"Ground ball through the infield to ({ball_position.x:.1f}, {ball_position.y:.1f})"
            ))
            if self.hit_handler:
                self.hit_handler.determine_hit_type(ball_position, distance_from_home, result)
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
        if batter_runner and self.throwing_logic:
            self.throwing_logic.simulate_throw_to_first(fielder, fielding_time, batter_runner, result)
        else:
            # Fallback: if no batter runner or throwing logic, default to single
            result.outcome = PlayOutcome.SINGLE
            # Let handle_hit_baserunning place the batter and advance all runners
            if self.hit_handler:
                self.hit_handler.handle_hit_baserunning(result, self.current_outs)
            elif batter_runner:
                # Last resort fallback if no hit_handler exists
                batter_runner.current_base = "first"
                self.baserunning_simulator.remove_runner("home")
                self.baserunning_simulator.add_runner("first", batter_runner)
                result.final_runner_positions["first"] = batter_runner

    def simulate_ground_ball_fielding(self, fielder, ball_position: FieldPosition,
                                      ball_time: float, result,
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
            distance_to_fielder = self.get_closest_fielder_distance(ball_position)
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
                if self.hit_handler:
                    self.hit_handler.handle_hit_baserunning(result, self.current_outs)
            elif time_difference <= SAFE_RUNNER_BIAS:
                # Close play, tie goes to runner
                result.outcome = PlayOutcome.SINGLE
                result.add_event(PlayEvent(
                    runner_time_to_first, "infield_single",
                    f"Infield single on close play (runner {runner_time_to_first:.2f}s vs ball {ball_arrival_at_first:.2f}s)"
                ))
                if self.hit_handler:
                    self.hit_handler.handle_hit_baserunning(result, self.current_outs)
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

    def attempt_ground_ball_out(self, fielder, ball_position: FieldPosition,
                               catch_time: float, result,
                               position_name: str = None) -> bool:
        """Attempt to field ground ball and throw out runner, checking for force plays and double plays."""
        from .baserunning import create_average_runner

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
        if self.throwing_logic:
            force_result = self.throwing_logic.attempt_force_play(fielder, ball_position, fielding_time, result)
        else:
            force_result = None

        if debug_force:
            if force_result:
                print(f"  Force play attempted: {force_result}")
            else:
                print(f"  No force situation detected")

        if force_result and force_result['success']:
            # We got the force out! Check if double play is possible
            can_attempt_dp = result.outs_made < 2  # Need less than 2 outs for DP

            if can_attempt_dp and self.throwing_logic:
                dp_success = self.throwing_logic.attempt_double_play(fielder, ball_position, fielding_time, result, force_result)

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
            result.add_event(PlayEvent(
                runner_time_to_first, "safe_at_first",
                f"Safe at first, beats throw by {abs(time_difference):.2f}s"
            ))
            # Let handle_hit_baserunning place the batter and advance all runners
            if self.hit_handler:
                self.hit_handler.handle_hit_baserunning(result, self.current_outs)
            else:
                # Fallback if no hit handler
                batter_runner.current_base = "first"
                self.baserunning_simulator.remove_runner("home")
                self.baserunning_simulator.add_runner("first", batter_runner)
                result.final_runner_positions["first"] = batter_runner
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
            # Let handle_hit_baserunning place the batter and advance all runners
            if self.hit_handler:
                self.hit_handler.handle_hit_baserunning(result, self.current_outs)
            else:
                # Fallback if no hit handler
                batter_runner.current_base = "first"
                self.baserunning_simulator.remove_runner("home")
                self.baserunning_simulator.add_runner("first", batter_runner)
                result.final_runner_positions["first"] = batter_runner
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

    def log_ground_ball_interception_details(self, interception, ball_position: FieldPosition, result):
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

    def estimate_ground_ball_roll_time(self, distance_to_fielder: float,
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

    def get_closest_fielder_distance(self, ball_position: FieldPosition) -> float:
        """Get distance from ball to closest fielder for ground ball roll calculation."""
        min_distance = float('inf')

        for fielder in self.fielding_simulator.fielders.values():
            if fielder.current_position:
                distance = fielder.current_position.distance_to(ball_position)
                min_distance = min(min_distance, distance)

        return min_distance if min_distance != float('inf') else 100.0  # Default fallback
