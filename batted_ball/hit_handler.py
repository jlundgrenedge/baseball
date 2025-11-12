"""
Hit handler module for determining hit types and baserunning logic.

Contains methods for classifying hits and managing runner advancement.
"""

import numpy as np
from .field_layout import FieldPosition
from .play_outcome import PlayOutcome, PlayEvent, PlayResult
from .baserunning import decide_runner_advancement


class HitHandler:
    """Handler for hit determination and baserunning logic."""

    def __init__(self, baserunning_simulator, current_outs: int = 0):
        """
        Initialize hit handler.

        Parameters
        ----------
        baserunning_simulator : BaserunningSimulator
            Reference to baserunning simulator
        current_outs : int
            Current number of outs
        """
        self.baserunning_simulator = baserunning_simulator
        self.current_outs = current_outs

    def determine_hit_type(self, ball_position: FieldPosition, distance_ft: float, result: PlayResult):
        """Determine hit type when no fielder can intercept, with contact quality gates."""
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
        # BUT NOT HOME RUNS - need solid contact for HRs (realistic baseball)
        elif contact_quality == 'fair' or exit_velocity < 95:
            # Fair contact maxes out at triples - no home runs without solid contact
            if distance_ft > 300 and 10 < abs_angle < 50 and exit_velocity >= 88:
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

        self.handle_hit_baserunning(result, self.current_outs)

    def handle_hit_baserunning(self, result: PlayResult, current_outs: int = 0):
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

        # Get batter runner - they might already be on first, second, or third base
        # Check in order: home (original position) -> first -> second -> third
        if DEBUG_BASERUNNING:
            print(f"  [BR] Looking for batter runner...")
            print(f"  [BR] Runners in simulator: {list(self.baserunning_simulator.runners.keys())}")
            for base, runner in self.baserunning_simulator.runners.items():
                print(f"  [BR]   {base}: {runner.name}")

        batter_runner = self.baserunning_simulator.get_runner_at_base("home")
        if not batter_runner:
            batter_runner = self.baserunning_simulator.get_runner_at_base("first")
        if not batter_runner:
            batter_runner = self.baserunning_simulator.get_runner_at_base("second")
        if not batter_runner:
            batter_runner = self.baserunning_simulator.get_runner_at_base("third")

        if not batter_runner:
            if DEBUG_BASERUNNING:
                print(f"  [BR] No batter runner found at any base!")
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
        runner_targets = {}  # Track where each runner is going (for throw logic)

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
            runner_targets[base] = target_base  # Track for throw destination logic

            # LOG RUNNER ADVANCEMENT DECISION
            # Get ball retrieval time from events for proper timestamp
            ball_retrieval_time = 0.0
            for event in result.events:
                if event.event_type == "ball_retrieved":
                    ball_retrieval_time = event.time
                    break

            # Log the advancement decision with reasoning
            result.add_event(PlayEvent(
                ball_retrieval_time + 0.05,
                "runner_advancement_decision",
                f"Runner on {base} advancing to {target_base} (risk: {decision['risk_level']}, advancing {decision['advancement_bases']} bases)"
            ))

            if DEBUG_BASERUNNING:
                print(f"  [BR] Runner on {base} -> {target_base} (risk: {decision['risk_level']})")

            # If runner scores, increment runs and mark for removal
            if target_base == "home":
                result.runs_scored += 1
                runners_to_remove.append(base)
                # Log runner scoring
                result.add_event(PlayEvent(
                    ball_retrieval_time + 0.06,
                    "runner_scores",
                    f"Runner from {base} scores"
                ))
                if DEBUG_BASERUNNING:
                    print(f"  [BR] -> Runner scores!")
            else:
                # Move runner to new base
                runner.current_base = target_base
                new_positions[target_base] = runner
                runners_to_remove.append(base)  # Remove from old base
                # Log runner advancement completion
                result.add_event(PlayEvent(
                    ball_retrieval_time + 0.07,
                    "runner_advances",
                    f"Runner advances from {base} to {target_base} (safe)"
                ))

        # Store runner targets for later throw destination logic
        # This will be used by the caller to determine where to throw
        result.runner_targets = runner_targets
        result.batter_target_base = batter_base

        # Apply all runner movements
        for base in runners_to_remove:
            self.baserunning_simulator.remove_runner(base)

        for base, runner in new_positions.items():
            if runner != batter_runner:  # Batter already added above
                self.baserunning_simulator.add_runner(base, runner)
                result.final_runner_positions[base] = runner
