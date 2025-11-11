"""
Throwing and force play logic for baseball play simulation.

This module handles fielder throwing decisions, throw simulations,
force play detection, and double play attempts.
"""

import numpy as np
from typing import Dict, Optional

from .constants import CLOSE_PLAY_TOLERANCE, SAFE_RUNNER_BIAS
from .field_layout import FieldLayout, FieldPosition
from .fielding import Fielder, simulate_fielder_throw
from .baserunning import BaseRunner, BaserunningSimulator, detect_force_situation, get_force_base


class PlayEvent:
    """Represents a single event during a play."""

    def __init__(self, time: float, event_type: str, description: str):
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
        """
        self.time = time
        self.event_type = event_type
        self.description = description


class PlayOutcome:
    """Play outcome constants."""
    SINGLE = "single"
    GROUND_OUT = "ground_out"
    FORCE_OUT = "force_out"
    DOUBLE_PLAY = "double_play"


class PlayResult:
    """Minimal play result interface for throwing logic."""

    def __init__(self):
        self.outcome = None
        self.outs_made = 0
        self.runs_scored = 0
        self.final_runner_positions = {}
        self.events = []
        self.primary_fielder = None

    def add_event(self, event: PlayEvent):
        """Add an event to the play."""
        self.events.append(event)


class ThrowingLogic:
    """Handles throwing decisions and force play logic for baseball play simulation."""

    def __init__(self, field_layout: FieldLayout, baserunning_simulator: BaserunningSimulator):
        """
        Initialize throwing logic.

        Parameters
        ----------
        field_layout : FieldLayout
            Field layout for position information
        baserunning_simulator : BaserunningSimulator
            Baserunning simulator for runner management
        """
        self.field_layout = field_layout
        self.baserunning_simulator = baserunning_simulator

    def should_throw_to_first(self, ball_time: float, batter_runner: BaseRunner) -> bool:
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

    def simulate_throw_to_first(self, fielder: Fielder, release_time: float,
                                batter_runner: BaseRunner, result: PlayResult):
        """Simulate throw to first base, checking for force plays and double plays."""
        # Get first base position
        first_base_pos = self.field_layout.get_base_position("first")

        # Check for force play situations FIRST
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

    def attempt_force_play(self, fielder: Fielder, ball_position: FieldPosition,
                           fielding_time: float, result: PlayResult) -> Optional[Dict]:
        """
        Attempt force play at appropriate base.

        Returns dict with force play result or None if no force situation.
        """
        # Check if any runners are forced
        forces = detect_force_situation(self.baserunning_simulator.runners, batter_running=True)

        # Debug
        debug_force = not hasattr(self, 'force_attempt_debug_done')
        if debug_force:
            self.force_attempt_debug_done = True
            print(f"  [attempt_force_play] Checking forces...")
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

    def attempt_double_play(self, fielder: Fielder, ball_position: FieldPosition,
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
