"""
Fly ball and catch handling for baseball play simulation.

This module handles all fly ball trajectory interception, catch attempts,
and outfield ball fielding logic.
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
from .field_layout import FieldLayout, FieldPosition
from .fielding import (
    Fielder, FieldingSimulator, FieldingResult,
    simulate_relay_throw, determine_cutoff_man,
)
from .baserunning import (
    BaseRunner, BaserunningSimulator,
    detect_force_situation,
)
from .trajectory import BattedBallResult
from .outfield_interception import OutfieldInterceptor
from .play_outcome import PlayEvent, PlayResult, PlayOutcome


class FlyBallHandler:
    """Handles fly ball trajectory interception and catch attempts."""

    def __init__(self,
                 field_layout: FieldLayout,
                 fielding_simulator: FieldingSimulator,
                 baserunning_simulator: BaserunningSimulator,
                 outfield_interceptor: OutfieldInterceptor,
                 current_outs: int = 0):
        """
        Initialize fly ball handler.

        Parameters
        ----------
        field_layout : FieldLayout
            Field dimensions and base positions
        fielding_simulator : FieldingSimulator
            Fielding simulation engine
        baserunning_simulator : BaserunningSimulator
            Baserunning simulation engine
        outfield_interceptor : OutfieldInterceptor
            Outfield interception calculator
        current_outs : int
            Number of outs before the play
        """
        self.field_layout = field_layout
        self.fielding_simulator = fielding_simulator
        self.baserunning_simulator = baserunning_simulator
        self.outfield_interceptor = outfield_interceptor
        self.current_outs = current_outs

        # FIX FOR DATA CLEANLINESS (Priority 5): Debug flag for verbose fielder assignment logs
        # Set to False to clean up play-by-play logs from clutter
        self.DEBUG_FIELDING_ASSIGNMENT = False

        # These will be set externally by the play simulation
        self.play_analyzer = None
        self.hit_handler = None
        self.throwing_logic = None

    def simulate_catch_attempt(self, ball_position: FieldPosition,
                               hang_time: float, result: PlayResult) -> FieldingResult:
        """Simulate fielder attempting to catch a fly ball."""
        # ENHANCED LOGGING: Add detailed spatial and fielder analysis (only if debug enabled)
        if self.DEBUG_FIELDING_ASSIGNMENT:
            distance_from_home = np.sqrt(ball_position.x**2 + ball_position.y**2)
            result.add_event(PlayEvent(
                0.0, "fly_ball_analysis",
                f"Fly ball coordinates: ({ball_position.x:.1f}, {ball_position.y:.1f}) ft, distance {distance_from_home:.1f} ft, hang time {hang_time:.2f}s"
            ))

        # Determine responsible fielder based on position and capability
        responsible_position = self.fielding_simulator.determine_responsible_fielder(
            ball_position, hang_time
        )

        # ENHANCED LOGGING: Show fielder analysis for catch attempt (only if debug enabled)
        if self.DEBUG_FIELDING_ASSIGNMENT:
            self.log_fly_ball_fielder_analysis(ball_position, hang_time, responsible_position, result)

        # Simulate fielding attempt - NOTE: This should use the same responsible fielder
        catch_result = self.fielding_simulator.simulate_fielding_attempt(
            ball_position, hang_time
        )

        result.fielding_results.append(catch_result)

        if catch_result.success:
            result.add_event(PlayEvent(
                hang_time, "catch",
                f"Caught by {responsible_position} at {self.describe_field_location(ball_position)}"
            ))
        else:
            # Use failure reason to provide accurate description
            if catch_result.failure_reason == 'TOO_SLOW':
                # FIX FOR BALL RETRIEVAL LOGIC BUG: Don't specify which fielder couldn't reach it
                # The retrieval logic will recalculate the closest fielder to pick up the ball
                # This prevents confusing narratives like "first_base couldn't reach it" followed
                # by "Ball retrieved by right_field"
                result.add_event(PlayEvent(
                    hang_time, "ball_drops",
                    f"Ball drops in {self.describe_field_location(ball_position)}"
                ))
            elif catch_result.failure_reason == 'DROP_ERROR':
                # Calculate time margin for context
                time_margin = catch_result.ball_arrival_time - catch_result.fielder_arrival_time

                # FIX FOR BUTTERFINGERS BUG: If fielder arrived early (positive time margin),
                # especially if waiting (>0.5s), this should be a FIELDING ERROR, not a hit.
                if time_margin > 0.0:
                    # Fielder was there in time but dropped it - this is an error
                    result.add_event(PlayEvent(
                        hang_time, "fielding_error",
                        f"ERROR! Ball dropped by {responsible_position} in {self.describe_field_location(ball_position)} (arrived {time_margin:.2f}s early, E{self._get_error_number(responsible_position)})"
                    ))
                    # Mark this as an error, not allowing the ball to roll to the wall
                    # We'll handle this in handle_fly_ball_caught with special error logic
                    catch_result.is_error = True
                else:
                    # FIX FOR "DIVING ATTEMPT VS ROUTINE DROP" BUG (Priority 3):
                    # Fielder arrived slightly late (within diving range, -0.15s to 0.0s margin)
                    # This is a diving attempt - most of these should be HITS, not errors
                    # Only mark as error if ball actually hit the glove and was dropped

                    # Small chance ball hits glove during diving attempt (20%)
                    # This represents cases where fielder gets a glove on it but can't hold on
                    ball_hit_glove = np.random.random() < 0.20

                    if ball_hit_glove:
                        # Ball touched glove but couldn't hold on - this is an error
                        result.add_event(PlayEvent(
                            hang_time, "fielding_error",
                            f"ERROR! Diving attempt by {responsible_position}, ball hit glove but dropped in {self.describe_field_location(ball_position)} (E{self._get_error_number(responsible_position)})"
                        ))
                        catch_result.is_error = True
                    else:
                        # Diving attempt, ball never reached glove - this is a HIT (trapped/just missed)
                        result.add_event(PlayEvent(
                            hang_time, "ball_drops",
                            f"Diving attempt by {responsible_position} in {self.describe_field_location(ball_position)}... just missed!"
                        ))
            else:
                # Fallback for unknown failure reason
                # FIX FOR BALL RETRIEVAL LOGIC BUG: Don't specify fielder, let retrieval logic assign
                result.add_event(PlayEvent(
                    hang_time, "ball_drops",
                    f"Ball drops in {self.describe_field_location(ball_position)}"
                ))

        return catch_result

    def log_fly_ball_fielder_analysis(self, ball_position: FieldPosition, hang_time: float,
                                     responsible_position: str, result: PlayResult):
        """Log detailed fielder analysis for fly ball attempts."""
        from .constants import FIELDING_HIERARCHY

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

        # Collect detailed metrics for viable fielders
        viable_fielders = []

        for pos_name in positions_to_check:
            if pos_name in self.fielding_simulator.fielders:
                fielder = self.fielding_simulator.fielders[pos_name]
                start_pos = fielder.current_position
                distance_to_ball = start_pos.horizontal_distance_to(ball_position)

                # Calculate if this fielder could make the play
                effective_time = fielder.calculate_effective_time_to_position(ball_position)
                time_margin = hang_time - effective_time

                can_reach = time_margin >= 0.0
                hierarchy = FIELDING_HIERARCHY.get(pos_name, 50)

                if can_reach or time_margin > -0.3:  # Show fielders who are close
                    viable_fielders.append({
                        'position': pos_name,
                        'distance': distance_to_ball,
                        'time_margin': time_margin,
                        'hierarchy': hierarchy,
                        'can_reach': can_reach
                    })

                # Create simple analysis string
                status = "CAN REACH" if can_reach else f"late {abs(time_margin):.2f}s"
                fielder_analyses.append(
                    f"{pos_name}: {distance_to_ball:.1f}ft, margin {time_margin:+.2f}s ({status})"
                )

        # Log the basic analysis (all fielders checked)
        if fielder_analyses:
            # Split into chunks if too many
            chunk_size = 4
            for i in range(0, len(fielder_analyses), chunk_size):
                chunk = fielder_analyses[i:i+chunk_size]
                result.add_event(PlayEvent(
                    0.05 + i * 0.002, "fly_ball_fielder_analysis",
                    f"Fielders: {'; '.join(chunk)}"
                ))

        # Log detailed assignment decision if multiple fielders can reach
        viable_count = sum(1 for f in viable_fielders if f['can_reach'])
        if viable_count > 1:
            # Sort by distance to see who's closest
            viable_fielders.sort(key=lambda x: x['distance'])
            closest = viable_fielders[0]

            # Check if assigned fielder is the closest
            assigned_viable = next((f for f in viable_fielders if f['position'] == responsible_position), None)

            if assigned_viable and assigned_viable['position'] != closest['position']:
                # Assignment differs from closest - log reasoning
                reason = ""
                if assigned_viable['time_margin'] > closest['time_margin'] + 0.1:
                    reason = f"arrives {assigned_viable['time_margin'] - closest['time_margin']:.2f}s earlier"
                elif assigned_viable['hierarchy'] > closest['hierarchy']:
                    reason = f"hierarchy priority (H:{assigned_viable['hierarchy']} vs {closest['hierarchy']})"
                else:
                    reason = "similar arrival time, better positioning"

                result.add_event(PlayEvent(
                    0.065, "fly_ball_assignment_reasoning",
                    f"Assigned to {responsible_position} over {closest['position']} ({closest['distance']:.1f}ft closer): {reason}"
                ))

        result.add_event(PlayEvent(
            0.07, "fly_ball_assignment",
            f"Assigned to: {responsible_position}"
        ))

    def handle_fly_ball_caught(self, catch_result: FieldingResult, result: PlayResult):
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

    def handle_fielding_error(self, catch_result: FieldingResult,
                              ball_position: FieldPosition, error_time: float,
                              result: PlayResult):
        """
        Handle fielding error (dropped ball with positive time margin).

        FIX FOR BUTTERFINGERS BUG: When fielder arrives early but drops the ball,
        this should be a fielding error, not a hit that rolls to the wall.

        Ball stays at fielder's location. Runners advance 1-2 bases, not unlimited.
        """
        # Set outcome to ERROR
        result.outcome = PlayOutcome.ERROR
        result.outs_made = 0  # No outs on error

        # Ball stays at fielder's location (bounced off glove)
        # Fielder retrieves it immediately (1-2 seconds to recover)
        recovery_time = 1.5  # seconds to recover from error
        ball_retrieved_time = error_time + recovery_time

        # Get the fielder info
        fielder_position = catch_result.fielder_position
        fielder = self.fielding_simulator.fielders.get(fielder_position)

        result.add_event(PlayEvent(
            ball_retrieved_time, "ball_recovered",
            f"Ball recovered by {fielder_position} after error at {ball_retrieved_time:.2f}s"
        ))

        # Baserunning: Batter reaches base, existing runners advance 1-2 bases
        batter_runner = self.baserunning_simulator.get_runner_at_base("home")
        if not batter_runner:
            return  # Safety check

        # Calculate how far batter can run during error recovery
        time_to_first = batter_runner.calculate_time_to_base("home", "first", include_leadoff=False)
        time_to_second = batter_runner.calculate_time_to_base("home", "second", include_leadoff=False)

        # Determine batter's advancement
        if ball_retrieved_time >= time_to_second:
            # Batter reaches second on error
            batter_target = "second"
            result.add_event(PlayEvent(
                time_to_second, "batter_reaches_second",
                f"Batter reaches second base on error ({time_to_second:.2f}s)"
            ))
        else:
            # Batter reaches first on error
            batter_target = "first"
            result.add_event(PlayEvent(
                time_to_first, "batter_reaches_first",
                f"Batter reaches first base on error ({time_to_first:.2f}s)"
            ))

        # Move batter to target base
        self.baserunning_simulator.remove_runner("home")
        batter_runner.current_base = batter_target
        self.baserunning_simulator.add_runner(batter_target, batter_runner)
        result.final_runner_positions[batter_target] = batter_runner

        # Advance existing runners (force if needed, otherwise hold or advance 1 base)
        # Process in reverse order (third -> second -> first) to avoid conflicts
        for base in ["third", "second", "first"]:
            runner = self.baserunning_simulator.get_runner_at_base(base)
            if runner:
                # Determine where this runner should go
                if base == "third":
                    # Runner on third scores on error
                    target_base = "home"
                    result.runs_scored += 1
                    self.baserunning_simulator.remove_runner(base)
                    result.add_event(PlayEvent(
                        error_time + 0.5, f"runner_scores_from_{base}",
                        f"Runner scores from third on error"
                    ))
                elif base == "second":
                    # Runner on second advances to third (or home if batter only reached first)
                    if batter_target == "first":
                        target_base = "third"
                    else:
                        target_base = "home"
                        result.runs_scored += 1

                    self.baserunning_simulator.remove_runner(base)
                    if target_base == "home":
                        result.add_event(PlayEvent(
                            error_time + 0.8, f"runner_scores_from_{base}",
                            f"Runner scores from second on error"
                        ))
                    else:
                        runner.current_base = target_base
                        self.baserunning_simulator.add_runner(target_base, runner)
                        result.final_runner_positions[target_base] = runner
                        result.add_event(PlayEvent(
                            error_time + 0.8, f"runner_advances_to_{target_base}",
                            f"Runner advances from second to {target_base}"
                        ))
                elif base == "first":
                    # Runner on first advances based on batter's advancement
                    if batter_target == "second":
                        # Forced to second (batter took second)
                        target_base = "third"
                    else:
                        # Advances to second (force play)
                        target_base = "second"

                    self.baserunning_simulator.remove_runner(base)
                    runner.current_base = target_base
                    self.baserunning_simulator.add_runner(target_base, runner)
                    result.final_runner_positions[target_base] = runner
                    result.add_event(PlayEvent(
                        error_time + 0.6, f"runner_advances_to_{target_base}",
                        f"Runner advances from first to {target_base}"
                    ))

    def handle_ball_in_play(self, ball_position: FieldPosition,
                            ball_time: float, result: PlayResult,
                            skip_trajectory_interception: bool = False):
        """Handle ball in play using trajectory interception logic instead of landing spot racing."""
        import numpy as np

        # ENHANCED LOGGING: Add comprehensive outfield ball analysis (only if debug enabled)
        distance_ft = np.sqrt(ball_position.x**2 + ball_position.y**2)
        batted_ball = result.batted_ball_result
        peak_height = batted_ball.peak_height if batted_ball else 0

        if self.DEBUG_FIELDING_ASSIGNMENT:
            result.add_event(PlayEvent(
                ball_time, "outfield_ball_analysis",
                f"Ball in play at ({ball_position.x:.1f}, {ball_position.y:.1f}) ft, distance {distance_ft:.1f} ft, peak height {peak_height:.1f} ft"
            ))

        # Check for home run first (ball clears fence)
        spray_angle = np.arctan2(ball_position.x, ball_position.y) * 180.0 / np.pi

        if self.DEBUG_FIELDING_ASSIGNMENT:
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
        # FIX FOR "SCHRÖDINGER'S CATCH" BUG: Skip if already attempted in play_simulation.py
        if not skip_trajectory_interception:
            if self.attempt_trajectory_interception(batted_ball, result):
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
        self.log_outfield_interception_details(interception_result, ball_position, ball_time, result)

        # Note: Landing position catch check happens BEFORE this method is called
        # If we reach here, ball was not caught and will be a hit

        # Determine hit type first (this is a hit since landing position catch failed)
        if self.hit_handler:
            self.hit_handler.determine_hit_type(ball_position, distance_ft, result)
        else:
            # Fallback if no hit_handler is set
            self._determine_hit_type_fallback(ball_position, distance_ft, result)

        # Now calculate ball retrieval time for baserunning decisions
        if interception_result.can_be_fielded:
            # Use interception-based timing for how long it takes fielder to run down the ball
            ball_retrieved_time = interception_result.interception_time
            responsible_position = interception_result.fielding_position
            fielder = interception_result.fielding_fielder
            ball_position = interception_result.ball_position_at_interception

            location_desc = self.describe_field_location(ball_position)
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

            location_desc = self.describe_field_location(ball_position)
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

        # Log batter runner timing analysis (only if debug enabled)
        if self.DEBUG_FIELDING_ASSIGNMENT:
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

        # Log throw analysis (only if debug enabled)
        if self.DEBUG_FIELDING_ASSIGNMENT:
            result.add_event(PlayEvent(
                ball_retrieved_time + 0.02, "throw_analysis",
                f"Throw times from {responsible_position} - 1st: {relay_to_first.total_arrival_time:.2f}s, 2nd: {relay_to_second.total_arrival_time:.2f}s, 3rd: {relay_to_third.total_arrival_time:.2f}s, home: {relay_to_home.total_arrival_time:.2f}s{relay_info}"
            ))

        # Ball arrival times at each base (retrieval + throw time)
        ball_at_first = ball_retrieved_time + relay_to_first.total_arrival_time
        ball_at_second = ball_retrieved_time + relay_to_second.total_arrival_time
        ball_at_third = ball_retrieved_time + relay_to_third.total_arrival_time
        ball_at_home = ball_retrieved_time + relay_to_home.total_arrival_time

        # ENHANCED LOGGING: Add detailed race comparison (only if debug enabled)
        if self.DEBUG_FIELDING_ASSIGNMENT:
            result.add_event(PlayEvent(
                ball_retrieved_time + 0.03, "race_analysis",
                f"Ball arrival times - 1st: {ball_at_first:.2f}s, 2nd: {ball_at_second:.2f}s, 3rd: {ball_at_third:.2f}s, home: {ball_at_home:.2f}s"
            ))

        # Delegate to hit_handler for final baserunning logic
        if self.hit_handler:
            self.hit_handler.handle_hit_baserunning(result, self.current_outs)

        # DETERMINE AND LOG THROW DESTINATION (after ball retrieval and baserunning decisions)
        # Only for hits (not outs or home runs)
        if result.outcome in [PlayOutcome.SINGLE, PlayOutcome.DOUBLE, PlayOutcome.TRIPLE]:
            # Fielder throws to the most advanced runner (lead runner)
            # Priority: home > third > second > first
            base_priority = {"home": 4, "third": 3, "second": 2, "first": 1}

            # Get runner targets from baserunning decisions
            runner_targets = getattr(result, 'runner_targets', {})
            batter_base = getattr(result, 'batter_target_base', 'first')

            # Find the most advanced target base from runner decisions
            throw_target = batter_base  # Default to batter's base
            throw_target_priority = base_priority.get(batter_base, 0)

            for from_base, to_base in runner_targets.items():
                priority = base_priority.get(to_base, 0)
                if priority > throw_target_priority:
                    throw_target = to_base
                    throw_target_priority = priority

            # SMART THROW LOGIC: On clear singles with no force plays, throw to second to keep runner from advancing
            # Don't throw to first when there's no play - throw ahead of the runner
            if result.outcome == PlayOutcome.SINGLE and len(runner_targets) == 0 and throw_target == "first":
                # Clear single, no runners on base - throw to second to keep batter from advancing
                throw_target = "second"

            # Get fielder info - use the responsible position from earlier in the method
            # or fall back to primary fielder from result
            if interception_result and interception_result.can_be_fielded:
                fielder_name = interception_result.fielding_position
            elif result.primary_fielder:
                fielder_name = result.primary_fielder.position
            else:
                fielder_name = responsible_position if responsible_position else "OF"

            # Log the throw destination
            result.add_event(PlayEvent(
                ball_retrieved_time + 0.08,
                "throw_destination",
                f"Throw from {fielder_name} to {throw_target}"
            ))

            # Get throw timing from earlier analysis (if available)
            # Look for throw_analysis event
            throw_time_to_target = None
            for event in result.events:
                if event.event_type == "throw_analysis":
                    # Parse throw times from the event description
                    # Format: "Throw times from XF - 1st: X.XXs, 2nd: X.XXs, 3rd: X.XXs, home: X.XXs"
                    desc = event.description
                    target_label = {"first": "1st", "second": "2nd", "third": "3rd", "home": "home"}
                    if throw_target in target_label:
                        label = target_label[throw_target]
                        import re
                        pattern = f"{label}: ([0-9.]+)s"
                        match = re.search(pattern, desc)
                        if match:
                            throw_time_to_target = float(match.group(1))
                    break

            # Log throw outcome (if we have timing data)
            if throw_time_to_target:
                ball_arrival = ball_retrieved_time + throw_time_to_target
                result.add_event(PlayEvent(
                    ball_retrieved_time + 0.09,
                    "throw_outcome",
                    f"Ball arrives at {throw_target} at {ball_arrival:.2f}s (no play attempted - runners advance safely)"
                ))

    def log_outfield_interception_details(self, interception_result, ball_position: FieldPosition,
                                         ball_time: float, result: PlayResult):
        """Log detailed information about outfield interception analysis."""
        # Only log if debug mode is enabled
        if not self.DEBUG_FIELDING_ASSIGNMENT:
            return

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

    def attempt_trajectory_interception(self, batted_ball_result: BattedBallResult, result: PlayResult) -> bool:
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
            ball_pos_t = self.calculate_ball_position_at_time(batted_ball_result, t)

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
                    trajectory_data = self.create_trajectory_data_for_pursuit(batted_ball_result, t)

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

                    # ANTI-EXPLOIT: Prevent infielders from catching balls they shouldn't
                    # Infielders can catch pop-ups and shallow hits, but not:
                    # 1. Balls passing overhead too high to reach (> 10 ft)
                    # 2. Line drives/fly balls destined for outfield (landing > 250 ft)
                    infielders = ['first_base', 'second_base', 'third_base', 'shortstop', 'pitcher', 'catcher']
                    if position_name in infielders:
                        max_infielder_reach_height = 10.0  # feet (player height + jumping reach)
                        final_landing_distance = batted_ball_result.distance

                        # Check if ball is too high to reach at this moment
                        if ball_pos_t.z > max_infielder_reach_height:
                            if debug:
                                print(f"    {position_name} skipped - ball too high to reach (height {ball_pos_t.z:.1f}ft > max reach {max_infielder_reach_height:.1f}ft)")
                            continue

                        # Check if ball is destined for outfield (even if currently at catchable height)
                        if final_landing_distance >= 250.0:
                            if debug:
                                print(f"    {position_name} skipped - ball destined for outfield (landing at {final_landing_distance:.0f}ft, infielders only catch < 250ft)")
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
                    return self.attempt_ground_ball_out(fielder, ball_pos_t, t, result, position_name)

        # No interception possible during trajectory - ball will continue to landing position
        # where a catch attempt will be made
        if debug:
            print("    No fielders can intercept during flight")

        # DON'T log "Ball lands uncaught" here - we haven't tried the landing position catch yet!
        # The landing position catch attempt happens in play_simulation.py after this returns False.
        # Only log "uncaught" after BOTH trajectory interception AND landing catch have been attempted.
        return False

    def calculate_ball_position_at_time(self, batted_ball_result: BattedBallResult, t: float) -> FieldPosition:
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

    def create_trajectory_data_for_pursuit(self, batted_ball_result: BattedBallResult, current_time: float) -> dict:
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

    def attempt_ground_ball_out(self, fielder, ball_position: FieldPosition,
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

        # Use simple throw to first (throwing_logic is for more complex scenarios)
        return self._attempt_simple_throw_to_first(
            fielder, ball_position, fielding_time, result, position_name
        )

    def _attempt_simple_throw_to_first(self, fielder, ball_position: FieldPosition,
                                       fielding_time: float, result: PlayResult,
                                       position_name: str) -> bool:
        """Simple fallback for throwing to first base."""
        # Calculate throw time to first base using fielder's actual attributes
        first_base_pos = self.field_layout.get_base_position('first')
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
            return True
        elif time_difference <= SAFE_RUNNER_BIAS:
            # Close play, tie goes to runner
            result.outcome = PlayOutcome.SINGLE
            result.add_event(PlayEvent(
                runner_time_to_first, "safe_at_first",
                f"Safe at first on close play ({runner_time_to_first:.2f}s vs {ball_arrival_at_first:.2f}s)"
            ))
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

            return True

    def _get_error_number(self, position: str) -> int:
        """Get the error number (1-9) for a fielding position."""
        error_numbers = {
            'pitcher': 1,
            'catcher': 2,
            'first_base': 3,
            'second_base': 4,
            'third_base': 5,
            'shortstop': 6,
            'left_field': 7,
            'center_field': 8,
            'right_field': 9
        }
        return error_numbers.get(position, 0)

    def describe_field_location(self, position: FieldPosition) -> str:
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
        # FIX FOR OUTFIELD POP-UP BUG: Updated infield threshold from 95ft to 140ft
        # This accounts for the dirt edge, not just the pitcher's mound distance
        # Balls at 70-75 ft are clearly infield pop-ups, not "outfield" flies
        if distance < 140:
            return "infield"
        elif distance < 180:
            return f"shallow {field_side}outfield"
        elif distance < 280:
            return f"{field_side}outfield"
        elif distance < 360:
            return f"deep {field_side}outfield"
        else:
            return f"warning track / {field_side}wall"

    def _determine_hit_type_fallback(self, ball_position: FieldPosition, distance_ft: float, result: PlayResult):
        """Fallback method to determine hit type when no hit_handler is available."""
        # Simple fallback logic based on distance
        if distance_ft > 300:
            result.outcome = PlayOutcome.TRIPLE
        elif distance_ft > 230:
            result.outcome = PlayOutcome.DOUBLE
        else:
            result.outcome = PlayOutcome.SINGLE
