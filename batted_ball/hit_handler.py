"""
Hit handler module for determining hit types and baserunning logic.

Contains methods for classifying hits and managing runner advancement.
Enhanced with park-adjusted home run logic and dynamic extra-base hit classification.
"""

import numpy as np
from .field_layout import FieldPosition
from .play_outcome import PlayOutcome, PlayEvent, PlayResult
from .baserunning import decide_runner_advancement
from .ballpark import get_ballpark, BallparkDimensions


class HitHandler:
    """Handler for hit determination and baserunning logic."""

    def __init__(self, baserunning_simulator, current_outs: int = 0, ballpark: str = "generic"):
        """
        Initialize hit handler.

        Parameters
        ----------
        baserunning_simulator : BaserunningSimulator
            Reference to baserunning simulator
        current_outs : int
            Current number of outs
        ballpark : str or BallparkDimensions
            Ballpark name or dimensions object (default: "generic")
        """
        self.baserunning_simulator = baserunning_simulator
        self.current_outs = current_outs

        # Initialize ballpark dimensions
        if isinstance(ballpark, BallparkDimensions):
            self.ballpark = ballpark
        else:
            self.ballpark = get_ballpark(ballpark)

    def determine_hit_type(self, ball_position: FieldPosition, distance_ft: float, result: PlayResult):
        """
        Determine hit type when no fielder can intercept.

        Enhanced with:
        - Park-adjusted home run logic (fence heights and dimensions)
        - Dynamic double/triple classification using fielding context
        - Probabilistic triple logic based on runner speed and fielder performance
        """
        # Get contact quality and exit velocity for gates
        batted_ball = result.batted_ball_result
        peak_height = batted_ball.peak_height if batted_ball else 0

        # Extract contact quality and exit velocity from initial conditions
        contact_quality = batted_ball.initial_conditions.get('contact_quality', 'fair') if batted_ball else 'fair'
        exit_velocity = batted_ball.initial_conditions.get('exit_velocity', 85.0) if batted_ball else 85.0

        # Calculate spray angle for park-adjusted fence determination
        spray_angle = np.arctan2(ball_position.x, ball_position.y) * 180.0 / np.pi
        abs_angle = abs(spray_angle)

        # PARK-ADJUSTED FENCE DIMENSIONS
        fence_distance, fence_height = self.ballpark.get_fence_at_angle(spray_angle)

        # Get ball height at fence distance (if trajectory available)
        height_at_fence = None
        if batted_ball and hasattr(batted_ball, 'get_height_at_distance'):
            try:
                height_at_fence = batted_ball.get_height_at_distance(fence_distance)
            except:
                height_at_fence = None

        # CONTACT QUALITY GATES - Limit outcomes based on contact quality
        # Weak contact (< 80 mph EV) cannot produce extra-base hits beyond singles
        if contact_quality == 'weak' or exit_velocity < 80:
            # Weak contact maxes out at singles
            result.outcome = PlayOutcome.SINGLE

        # Fair contact (80-88 mph EV) can produce singles, doubles, and triples
        # Home runs possible if ball clears fence (park-adjusted)
        elif contact_quality == 'fair' or exit_velocity < 88:
            # PARK-ADJUSTED HOME RUN DETERMINATION
            if self.ballpark.is_home_run(spray_angle, distance_ft, height_at_fence):
                result.outcome = PlayOutcome.HOME_RUN
                result.runs_scored = 1
            # Dynamic double/triple classification
            else:
                result.outcome = self._classify_extra_base_hit(
                    distance_ft, spray_angle, abs_angle, exit_velocity,
                    result, is_fair_contact=True
                )

        # Solid contact (88+ mph EV) - full range of outcomes
        else:  # solid contact
            # PARK-ADJUSTED HOME RUN DETERMINATION
            if self.ballpark.is_home_run(spray_angle, distance_ft, height_at_fence):
                result.outcome = PlayOutcome.HOME_RUN
                result.runs_scored = 1
            # Dynamic double/triple classification
            else:
                result.outcome = self._classify_extra_base_hit(
                    distance_ft, spray_angle, abs_angle, exit_velocity,
                    result, is_fair_contact=False
                )

        self.handle_hit_baserunning(result, self.current_outs)

    def _classify_extra_base_hit(self, distance_ft: float, spray_angle: float,
                                  abs_angle: float, exit_velocity: float,
                                  result: PlayResult, is_fair_contact: bool) -> PlayOutcome:
        """
        Classify double vs triple vs single using dynamic context.

        Uses fielding context (retrieval time), runner speed, and probabilistic factors.

        Parameters
        ----------
        distance_ft : float
            Ball distance
        spray_angle : float
            Spray angle in degrees
        abs_angle : float
            Absolute spray angle
        exit_velocity : float
            Exit velocity in mph
        result : PlayResult
            Play result object with fielding context
        is_fair_contact : bool
            True if fair contact (80-88 mph), False if solid (88+ mph)

        Returns
        -------
        PlayOutcome
            SINGLE, DOUBLE, or TRIPLE
        """
        # Extract fielding context from result events
        retrieval_time = self._get_retrieval_time_from_events(result)
        fielder_speed = self._get_fielder_speed_from_result(result)

        # Get batter runner speed
        batter_runner = self.baserunning_simulator.get_runner_at_base("home")
        if not batter_runner:
            # Try other bases if batter already advanced
            for base in ["first", "second", "third"]:
                batter_runner = self.baserunning_simulator.get_runner_at_base(base)
                if batter_runner:
                    break

        runner_speed = getattr(batter_runner, 'sprint_speed', 50.0) if batter_runner else 50.0

        # Base thresholds (more conservative than old fixed thresholds)
        triple_distance_min = 290  # Reduced from 300 to allow more context-driven triples
        double_distance_min = 220  # Reduced from 230 for more nuanced classification

        # TRIPLE DETERMINATION (Probabilistic + Context-Driven)
        if distance_ft >= triple_distance_min:
            # Check if ball is in gap (gaps produce more triples)
            in_gap = 10 < abs_angle < 50

            if in_gap:
                # Calculate triple probability based on multiple factors
                triple_prob = self._calculate_triple_probability(
                    distance_ft=distance_ft,
                    retrieval_time=retrieval_time,
                    runner_speed=runner_speed,
                    fielder_speed=fielder_speed,
                    exit_velocity=exit_velocity,
                    is_fair_contact=is_fair_contact
                )

                # Roll dice for triple
                if np.random.random() < triple_prob:
                    return PlayOutcome.TRIPLE

        # DOUBLE DETERMINATION (Context-Driven)
        if distance_ft >= double_distance_min:
            # Doubles are common for balls in the outfield
            # Even shorter hits can be doubles with slow fielders or fast runners

            # Adjust threshold based on context
            double_threshold = double_distance_min

            # Fast runner bonus (lower threshold)
            if runner_speed > 70:
                double_threshold -= 15

            # Slow fielder bonus (lower threshold)
            if fielder_speed < 40:
                double_threshold -= 10

            # Long retrieval time bonus
            if retrieval_time > 4.0:
                double_threshold -= 10

            if distance_ft >= double_threshold:
                return PlayOutcome.DOUBLE

        # Default to single
        return PlayOutcome.SINGLE

    def _calculate_triple_probability(self, distance_ft: float, retrieval_time: float,
                                       runner_speed: float, fielder_speed: float,
                                       exit_velocity: float, is_fair_contact: bool) -> float:
        """
        Calculate probability of a triple based on multiple contextual factors.

        Returns value between 0.0 (no chance) and 1.0 (guaranteed triple).
        """
        # Base probability (start conservative)
        base_prob = 0.05  # 5% base chance for balls in gap > 290 ft

        # DISTANCE FACTOR (most important)
        # 290-310 ft: +0.10, 310-330: +0.20, 330+: +0.30
        if distance_ft >= 330:
            base_prob += 0.30
        elif distance_ft >= 310:
            base_prob += 0.20
        else:
            base_prob += 0.10

        # RUNNER SPEED FACTOR
        # Fast runners (70+) get big bonus, slow runners (< 40) get penalty
        speed_factor = (runner_speed - 50.0) / 100.0  # Normalize around average (50)
        base_prob += speed_factor * 0.25  # ±25% based on speed

        # FIELDER SPEED FACTOR
        # Slow fielders increase triple chance
        fielder_factor = (50.0 - fielder_speed) / 100.0  # Inverse of fielder speed
        base_prob += fielder_factor * 0.15  # Up to +15% for very slow fielders

        # RETRIEVAL TIME FACTOR
        # Long retrieval times favor triples
        if retrieval_time > 5.0:
            base_prob += 0.15
        elif retrieval_time > 4.5:
            base_prob += 0.10
        elif retrieval_time > 4.0:
            base_prob += 0.05

        # EXIT VELOCITY FACTOR (secondary)
        # Hard-hit balls are more likely to roll far in gaps
        if exit_velocity >= 100:
            base_prob += 0.10
        elif exit_velocity >= 95:
            base_prob += 0.05

        # CONTACT QUALITY PENALTY
        # Fair contact less likely to produce triples (less carry)
        if is_fair_contact:
            base_prob *= 0.7  # 30% penalty

        # RANDOM VARIANCE (ball bounce luck)
        # Add small random factor (±5%)
        luck_factor = np.random.uniform(-0.05, 0.05)
        base_prob += luck_factor

        # Clamp to valid probability range
        return np.clip(base_prob, 0.0, 0.95)  # Max 95% (never guaranteed)

    def _get_retrieval_time_from_events(self, result: PlayResult) -> float:
        """Extract ball retrieval time from play events."""
        for event in result.events:
            if event.event_type == "ball_retrieved":
                return event.time
        # Default if not found
        return 3.0

    def _get_fielder_speed_from_result(self, result: PlayResult) -> float:
        """Extract fielder speed from primary fielder."""
        if result.primary_fielder and hasattr(result.primary_fielder, 'sprint_speed'):
            return result.primary_fielder.sprint_speed
        # Default to average
        return 50.0

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

            # LOG RUNNER ADVANCEMENT DECISION WITH TIMING
            # Get ball retrieval time from events for proper timestamp
            ball_retrieval_time = 0.0
            for event in result.events:
                if event.event_type == "ball_retrieved":
                    ball_retrieval_time = event.time
                    break

            # Extract ball arrival times at each base from race_analysis event
            ball_at_base = {}
            for event in result.events:
                if event.event_type == "race_analysis":
                    # Parse: "Ball arrival times - 1st: X.XXs, 2nd: X.XXs, 3rd: X.XXs, home: X.XXs"
                    import re
                    desc = event.description
                    base_labels = {"1st": "first", "2nd": "second", "3rd": "third", "home": "home"}
                    for label, base_name in base_labels.items():
                        pattern = f"{label}: ([0-9.]+)s"
                        match = re.search(pattern, desc)
                        if match:
                            ball_at_base[base_name] = float(match.group(1))
                    break

            # Calculate runner arrival time
            # FIX FOR TIME TRAVEL BUG: Runners start running when ball is hit (t=0)
            # calculate_time_to_base returns duration, we need absolute timestamp

            # FIX FOR "12.01s TIME ARTIFACT" BUG (Enhanced):
            # Use dictionary key as source of truth for runner location
            # The dictionary key tells us where the runner IS (first/second/third)
            # The runner.current_base attribute may be stale (often stuck at "home")
            #
            # CRITICAL: Always use dictionary key, not runner.current_base
            # This prevents incorrect time calculations like using "home->third" (17s)
            # when the runner is actually at "second" and should use "second->third" (5.5s)

            actual_base = base  # ALWAYS use dictionary key as source of truth

            # ALWAYS sync runner's current_base to match dictionary (don't just check, force it)
            # This ensures runner.current_base is never stale for future calculations
            if runner.current_base != base:
                if DEBUG_BASERUNNING:
                    print(f"  [BR FIX] Runner at dictionary key '{base}' had stale current_base='{runner.current_base}' - forcing sync")
                runner.current_base = base  # Force synchronization

            # Calculate movement time using correct base
            runner_time_to_target = runner.calculate_time_to_base(actual_base, target_base, include_leadoff=False)

            # FIX FOR "12.01s TIME ARTIFACT" BUG - Validation:
            # Sanity check: 1-base advances should be ~3.5-6s, 2-base ~10-14s, 3-base ~15-20s
            # If we get an unexpected time, recalculate with physics approximation
            expected_bases = {
                ("first", "second"): 1, ("second", "third"): 1, ("third", "home"): 1,
                ("first", "third"): 2, ("second", "home"): 2, ("home", "second"): 2,
                ("first", "home"): 3, ("home", "third"): 3
            }
            base_pair = (actual_base, target_base)
            if base_pair in expected_bases:
                expected_num_bases = expected_bases[base_pair]
                # Typical range: 1 base = 3.5-6s, 2 bases = 10-14s, 3 bases = 15-20s
                expected_min = 3.5 * expected_num_bases
                expected_max = 6.5 * expected_num_bases
                if not (expected_min <= runner_time_to_target <= expected_max):
                    if DEBUG_BASERUNNING:
                        print(f"  [BR WARNING] Time {runner_time_to_target:.2f}s for {actual_base}->{target_base} "
                              f"is outside expected range [{expected_min:.1f}, {expected_max:.1f}]s for {expected_num_bases} bases")
                    # Use physics approximation: distance / avg_speed
                    # Average sprint speed ~27 ft/s, distance = 90ft * num_bases
                    runner_time_to_target = (90.0 * expected_num_bases) / 27.0

            runner_start_time = 0.0  # Runners start at contact (time 0)
            runner_arrival_time = runner_start_time + runner_time_to_target

            # Log the advancement DECISION with reasoning
            result.add_event(PlayEvent(
                ball_retrieval_time + 0.05,
                "runner_advancement_decision",
                f"DECISION: Runner on {base} attempts advance to {target_base} (risk: {decision['risk_level']}, advancing {decision['advancement_bases']} bases)"
            ))

            if DEBUG_BASERUNNING:
                print(f"  [BR] Runner on {base} -> {target_base} (risk: {decision['risk_level']})")

            # If runner scores, increment runs and mark for removal
            if target_base == "home":
                result.runs_scored += 1
                runners_to_remove.append(base)

                # Log runner scoring with race timing
                ball_time_at_home = ball_at_base.get("home", float('inf'))
                time_difference = runner_arrival_time - ball_time_at_home

                if time_difference < 0:
                    margin_desc = f"beats throw by {abs(time_difference):.2f}s"
                else:
                    margin_desc = f"ball arrives {time_difference:.2f}s later (no play)"

                result.add_event(PlayEvent(
                    runner_arrival_time, "runner_scores",
                    f"Runner from {base} scores at {runner_arrival_time:.2f}s (ball: {ball_time_at_home:.2f}s, {margin_desc})"
                ))
                if DEBUG_BASERUNNING:
                    print(f"  [BR] -> Runner scores!")
            else:
                # Move runner to new base
                runner.current_base = target_base
                new_positions[target_base] = runner
                runners_to_remove.append(base)  # Remove from old base

                # Log runner advancement with race timing
                ball_time_at_target = ball_at_base.get(target_base, float('inf'))
                time_difference = runner_arrival_time - ball_time_at_target

                if ball_time_at_target == float('inf'):
                    # No ball timing available - use simple message
                    status_desc = "safe"
                elif time_difference < -0.5:
                    status_desc = f"safe (beats throw by {abs(time_difference):.2f}s)"
                elif time_difference < 0:
                    status_desc = f"safe (close play, beats throw by {abs(time_difference):.2f}s)"
                else:
                    status_desc = f"safe (ball arrives {time_difference:.2f}s later, no play)"

                result.add_event(PlayEvent(
                    runner_arrival_time, "runner_advances",
                    f"Runner arrives at {target_base} at {runner_arrival_time:.2f}s ({status_desc}) - Runner: {runner_arrival_time:.2f}s vs Ball: {ball_time_at_target:.2f}s"
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
