"""
Complete baseball play simulation engine.

Integrates trajectory physics, fielding mechanics, and baserunning physics
to simulate complete plays from bat contact to final outcomes with realistic
timing and decision-making.
"""

import numpy as np
from typing import Dict, List, Tuple, Optional, Union
from enum import Enum
from .constants import (
    # Field dimensions
    HOME_PLATE_HEIGHT,
    # Physics constants
    FEET_TO_METERS, METERS_TO_FEET,
    # Play timing
    CLOSE_PLAY_TOLERANCE, SAFE_RUNNER_BIAS,
    TAG_APPLICATION_TIME, TAG_AVOIDANCE_SUCCESS_RATE,
)
from .field_layout import FieldLayout, FieldPosition
from .fielding import Fielder, FieldingSimulator, FieldingResult, ThrowResult
from .baserunning import BaseRunner, BaserunningSimulator, BaserunningResult, RunnerState
from .trajectory import BattedBallSimulator, BattedBallResult


class PlayOutcome(Enum):
    """Possible outcomes of a play."""
    FLY_OUT = "fly_out"
    LINE_OUT = "line_out"
    GROUND_OUT = "ground_out"
    FORCE_OUT = "force_out"
    SINGLE = "single"
    DOUBLE = "double"
    TRIPLE = "triple"
    HOME_RUN = "home_run"
    ERROR = "error"
    FIELDERS_CHOICE = "fielders_choice"
    DOUBLE_PLAY = "double_play"
    TRIPLE_PLAY = "triple_play"


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
    
    def __init__(self, field_layout: Optional[FieldLayout] = None):
        """
        Initialize play simulator.
        
        Parameters
        ----------
        field_layout : FieldLayout, optional
            Field layout (creates standard if not provided)
        """
        self.field_layout = field_layout or FieldLayout()
        self.fielding_simulator = FieldingSimulator(self.field_layout)
        self.baserunning_simulator = BaserunningSimulator(self.field_layout)
        self.current_time = 0.0
        
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
                              batter_runner: BaseRunner) -> PlayResult:
        """
        Simulate a complete play from batted ball to final outcome.
        
        Parameters
        ----------
        batted_ball_result : BattedBallResult
            Result of batted ball trajectory simulation
        batter_runner : BaseRunner
            The batter becoming a runner
            
        Returns
        -------
        PlayResult
            Complete play simulation result
        """
        result = PlayResult()
        result.batted_ball_result = batted_ball_result
        self.current_time = 0.0
        
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
        # Get final position (landing spot)
        landing_pos = FieldPosition(
            batted_ball_result.landing_x,
            batted_ball_result.landing_y,
            0.0  # Ground level
        )
        
        # Determine hang time and whether it's an air ball
        hang_time = batted_ball_result.flight_time
        max_height = batted_ball_result.peak_height
        
        # Air ball: high enough that fielders can attempt to catch it in the air
        # Ground ball: low trajectory that bounces/rolls to fielder
        # Any ball with decent height OR hang time should be catchable
        is_air_ball = max_height > 2.0 or hang_time > 0.8
        
        return landing_pos, hang_time, is_air_ball
    
    def _get_closest_fielder_distance(self, ball_position: FieldPosition) -> float:
        """Get distance from ball to closest fielder for ground ball roll calculation."""
        min_distance = float('inf')
        
        for fielder in self.fielding_simulator.fielders.values():
            if fielder.current_position:
                distance = fielder.current_position.distance_to(ball_position)
                min_distance = min(min_distance, distance)
        
        return min_distance if min_distance != float('inf') else 100.0  # Default fallback
    
    def _simulate_ground_ball_fielding(self, fielder, ball_position: FieldPosition, ball_time: float, result: PlayResult):
        """Simulate ground ball fielding and throwing sequence."""
        # Time for ball to roll/bounce to final position (simplified)
        initial_velocity = 80.0  # mph estimated ball speed off bat
        distance_to_fielder = self._get_closest_fielder_distance(ball_position)
        
        # Ball slows down due to friction/bouncing
        roll_time = distance_to_fielder / (initial_velocity * 0.3)  # Ball slows significantly
        fielder_arrival_time = ball_time + roll_time
        
        # Fielding time (getting ball under control)
        fielding_time = 0.5 if fielder.range > 75 else 1.0
        
        # Throwing time to first base (simplified)
        distance_to_first = ball_position.distance_to(FieldPosition(90, 0, 0))  # 90 ft to first base
        throw_speed = fielder.arm_strength * 1.2  # mph
        throw_time = distance_to_first / (throw_speed * 1.467)  # Convert mph to ft/s
        
        total_fielder_time = fielder_arrival_time + fielding_time + throw_time
        
        # Runner time to first base
        batter_runner = self.baserunning_simulator.get_runner_at_base("home")
        if batter_runner:
            runner_time_to_first = self.baserunning_simulator.calculate_base_time(
                batter_runner, "home", "first"
            )
            
            # Compare times to determine out or safe
            if total_fielder_time < runner_time_to_first:
                # Out at first
                result.outcome = PlayOutcome.GROUND_OUT
                result.outs_made = 1
                result.primary_fielder = fielder
                result.add_event(PlayEvent(
                    total_fielder_time, "ground_out",
                    f"Ground out to {fielder.position}, fielded and thrown to first"
                ))
                self.baserunning_simulator.remove_runner("home")
            else:
                # Safe - it's a hit
                result.outcome = PlayOutcome.SINGLE
                result.add_event(PlayEvent(
                    runner_time_to_first, "infield_single",
                    f"Infield single, beats throw to first"
                ))
                self._handle_hit_baserunning(result)
    
    def _attempt_trajectory_interception(self, batted_ball_result: BattedBallResult, result: PlayResult) -> bool:
        """
        Attempt to intercept ball during its flight trajectory.
        
        Returns True if ball was caught/fielded, False if no interception possible.
        """
        # Sample trajectory at multiple time points to find interception opportunities
        flight_time = batted_ball_result.flight_time
        time_steps = 20  # Check 20 points along trajectory
        dt = flight_time / time_steps
        
        # Debug first few attempts
        debug = not hasattr(self, 'interception_debug_done')
        if debug:
            self.interception_debug_done = True
            print(f"INTERCEPTION DEBUG: flight_time={flight_time:.2f}s, peak_height={batted_ball_result.peak_height:.1f}ft")
        
        # Sample entire trajectory, focusing on key interception windows
        for i in range(1, time_steps):  # Skip t=0 (still at bat)
            t = i * dt
            
            # Get ball position at time t
            ball_pos_t = self._calculate_ball_position_at_time(batted_ball_result, t)
            
            if debug and i <= 3:
                print(f"  t={t:.2f}s: ball at ({ball_pos_t.x:.0f}, {ball_pos_t.y:.0f}, {ball_pos_t.z:.1f})")
            
            # Skip very high fly balls (>12ft) until they come down  
            if ball_pos_t.z > 12.0:
                continue
                
            # Find responsible fielder for this position
            responsible_position = self.fielding_simulator.determine_responsible_fielder(ball_pos_t)
            
            if responsible_position not in self.fielding_simulator.fielders:
                continue
                
            fielder = self.fielding_simulator.fielders[responsible_position]
            
            # Calculate if fielder can reach this position by time t
            fielder_time_needed = fielder.calculate_time_to_position(ball_pos_t)
            range_multiplier = fielder.get_effective_range_multiplier()
            effective_time = fielder_time_needed / range_multiplier
            
            if debug and i <= 3:
                distance = fielder.current_position.distance_to(ball_pos_t)
                print(f"    {responsible_position}: dist={distance:.0f}ft, needs {effective_time:.2f}s, has {t:.2f}s")
            
            # Give fielders some margin - they don't need to be exactly on time
            time_margin = 0.1  # 0.1 second margin for fielding
            if effective_time <= (t + time_margin):
                # Fielder can intercept! Determine catch vs field
                if ball_pos_t.z > 3.0:  # Air ball (raised from 1.0 to 3.0)
                    if debug:
                        print(f"    CAUGHT at t={t:.2f}s!")
                    result.outcome = PlayOutcome.FLY_OUT
                    result.outs_made = 1
                    result.primary_fielder = fielder
                    result.add_event(PlayEvent(
                        t, "catch",
                        f"Caught by {responsible_position} at {ball_pos_t.x:.0f}ft, {ball_pos_t.z:.1f}ft high"
                    ))
                    self.baserunning_simulator.remove_runner("home")
                    return True
                else:  # Ground ball / line drive
                    # Check if fielder can throw out runner
                    if debug:
                        print(f"    Attempting ground ball out at t={t:.2f}s, z={ball_pos_t.z:.1f}ft")
                    return self._attempt_ground_ball_out(fielder, ball_pos_t, t, result)
        
        # No interception possible
        if debug:
            print("    No interception possible")
        return False
    
    def _calculate_ball_position_at_time(self, batted_ball_result: BattedBallResult, t: float) -> FieldPosition:
        """Calculate ball position at time t during flight."""
        # Simplified trajectory calculation - would use full physics in real implementation
        # For now, linear interpolation between start and end
        progress = t / batted_ball_result.flight_time
        
        x = batted_ball_result.landing_x * progress
        y = batted_ball_result.landing_y * progress
        
        # Simple parabolic height calculation
        # Ball starts at contact height, peaks at mid-flight, ends at ground
        if progress <= 0.5:
            # Ascending
            height_progress = progress * 2  # 0 to 1
            z = 3.0 + (batted_ball_result.peak_height - 3.0) * height_progress
        else:
            # Descending  
            height_progress = (progress - 0.5) * 2  # 0 to 1
            z = batted_ball_result.peak_height * (1.0 - height_progress)
            
        return FieldPosition(x, y, z)
    
    def _attempt_ground_ball_out(self, fielder, ball_position: FieldPosition, 
                                catch_time: float, result: PlayResult) -> bool:
        """Attempt to field ground ball and throw out runner."""
        # Calculate time for fielder to reach ball, field it, and throw to first
        fielder_reach_time = fielder.calculate_time_to_position(ball_position)
        fielding_time = 0.3 + (fielder.fielding_range / 100.0) * 0.2  # 0.3-0.5s based on skill
        
        # Calculate throw time to first base
        first_base_pos = self.fielding_simulator.field_layout.get_base_position('first')
        throw_distance = ball_position.distance_to(first_base_pos)
        throw_velocity_mph = 70 + (fielder.arm_strength / 100.0) * 25  # 70-95 mph throws
        throw_velocity_fps = throw_velocity_mph * 1.467  # Convert mph to ft/s
        throw_time = throw_distance / throw_velocity_fps
        
        # Total time for fielder to complete the play
        total_fielder_time = catch_time + fielder_reach_time + fielding_time + throw_time
        
        # Calculate runner time to first base
        runner_speed_fps = 25.0  # Average runner speed (about 17 mph)
        distance_to_first = 90.0  # Base path distance
        runner_time = distance_to_first / runner_speed_fps  # About 3.6 seconds
        
        # Debug ground ball attempt
        debug = not hasattr(self, 'ground_ball_debug_done')
        if debug:
            self.ground_ball_debug_done = True
            print(f"      GROUND BALL: fielder_time={total_fielder_time:.1f}s vs runner_time={runner_time:.1f}s")
        
        if total_fielder_time < runner_time:
            result.outcome = PlayOutcome.GROUND_OUT
            result.outs_made = 1
            result.primary_fielder = fielder
            result.add_event(PlayEvent(
                total_fielder_time, "ground_out",
                f"Ground out to {fielder.position} ({total_fielder_time:.1f}s vs {runner_time:.1f}s)"
            ))
            self.baserunning_simulator.remove_runner("home")
            if debug:
                print(f"      GROUND OUT!")
            return True
        else:
            # Safe at first - it's a hit
            result.outcome = PlayOutcome.SINGLE
            result.add_event(PlayEvent(
                runner_time, "safe_at_first",
                f"Safe at first - fielder too slow ({total_fielder_time:.1f}s vs {runner_time:.1f}s)"
            ))
            self._handle_hit_baserunning(result)
            if debug:
                print(f"      SAFE AT FIRST")
            return True  # Still handled, just as hit instead of out
    
    def _determine_hit_type(self, ball_position: FieldPosition, distance_ft: float, result: PlayResult):
        """Determine hit type when no fielder can intercept."""
        if distance_ft > 350:
            result.outcome = PlayOutcome.TRIPLE
        elif distance_ft > 250:
            result.outcome = PlayOutcome.DOUBLE  
        else:
            result.outcome = PlayOutcome.SINGLE
        
        self._handle_hit_baserunning(result)
    
    def _handle_hit_baserunning(self, result: PlayResult):
        """Handle baserunning advancement for hits."""
        # Get batter runner
        batter_runner = self.baserunning_simulator.get_runner_at_base("home")
        if not batter_runner:
            return
        
        # Determine where batter runner ends up based on hit type
        if result.outcome == PlayOutcome.SINGLE:
            batter_runner.current_base = "first"
            self.baserunning_simulator.remove_runner("home")
            self.baserunning_simulator.add_runner("first", batter_runner)
            result.final_runner_positions["first"] = batter_runner
        elif result.outcome == PlayOutcome.DOUBLE:
            batter_runner.current_base = "second"
            self.baserunning_simulator.remove_runner("home")
            self.baserunning_simulator.add_runner("second", batter_runner)
            result.final_runner_positions["second"] = batter_runner
        elif result.outcome == PlayOutcome.TRIPLE:
            batter_runner.current_base = "third"
            self.baserunning_simulator.remove_runner("home")
            self.baserunning_simulator.add_runner("third", batter_runner)
            result.final_runner_positions["third"] = batter_runner
        
        # Handle existing runners (simplified - they advance safely)
        # In reality, this would involve more complex timing analysis
        runners_to_remove = []
        for base, runner in self.baserunning_simulator.runners.items():
            if base != "home":  # Don't move the batter again
                # Advance runner based on hit type
                if result.outcome == PlayOutcome.SINGLE:
                    if base == "third":
                        result.runs_scored += 1
                        runners_to_remove.append(base)
                    elif base == "second":
                        runner.current_base = "third"
                        result.final_runner_positions["third"] = runner
                        runners_to_remove.append(base)
                    # First base runner usually stays at first or advances to second
                elif result.outcome in [PlayOutcome.DOUBLE, PlayOutcome.TRIPLE]:
                    # Everyone scores on doubles/triples
                    result.runs_scored += 1
                    runners_to_remove.append(base)
        
        # Remove runners who scored
        for base in runners_to_remove:
            self.baserunning_simulator.remove_runner(base)
    
    def _simulate_catch_attempt(self, ball_position: FieldPosition, 
                               hang_time: float, result: PlayResult) -> FieldingResult:
        """Simulate fielder attempting to catch a fly ball."""
        # Determine responsible fielder
        responsible_position = self.fielding_simulator.determine_responsible_fielder(ball_position)
        
        # Simulate fielding attempt
        catch_result = self.fielding_simulator.simulate_fielding_attempt(
            ball_position, hang_time
        )
        
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
    
    def _handle_fly_ball_caught(self, catch_result: FieldingResult, result: PlayResult):
        """Handle outcome when fly ball is caught."""
        # Batter is out
        result.outs_made = 1
        
        # Check for double play opportunities (runners tagging up late)
        # Simplified: assume runners hold for now
        result.outcome = PlayOutcome.FLY_OUT
        
        # Remove batter-runner
        self.baserunning_simulator.remove_runner("home")
    
    def _handle_ball_in_play(self, ball_position: FieldPosition,
                            ball_time: float, result: PlayResult):
        """Handle ball in play using trajectory interception logic instead of landing spot racing."""
        import numpy as np

        # Check for home run first (ball clears fence)
        distance_ft = np.sqrt(ball_position.x**2 + ball_position.y**2)
        batted_ball = result.batted_ball_result
        peak_height = batted_ball.peak_height if batted_ball else 0

        # Home run: Needs both distance and height to clear 10 ft fence
        is_home_run = False
        if distance_ft >= 380 and peak_height >= 40:
            is_home_run = True
        elif distance_ft >= 400:  # Deep enough that it clears regardless
            is_home_run = True

        if is_home_run:
            result.outcome = PlayOutcome.HOME_RUN
            result.runs_scored = 1
            result.add_event(PlayEvent(
                ball_time, "home_run",
                f"HOME RUN! Ball travels {distance_ft:.0f} feet"
            ))
            return

        # Try trajectory interception instead of landing spot racing
        if self._attempt_trajectory_interception(batted_ball, result):
            return  # Ball was caught/fielded
            
        # No fielder could intercept - it's a hit
        self._determine_hit_type(ball_position, distance_ft, result)

        # Not a home run - simulate fielding and baserunning race
        responsible_position = self.fielding_simulator.determine_responsible_fielder(ball_position)
        fielder = self.fielding_simulator.fielders[responsible_position]

        # Time for fielder to reach ball and prepare throw
        retrieval_time = fielder.calculate_time_to_position(ball_position)
        ball_retrieved_time = ball_time + retrieval_time

        result.add_event(PlayEvent(
            ball_retrieved_time, "ball_retrieved",
            f"Ball retrieved by {responsible_position}"
        ))

        # Get batter as runner
        batter_runner = self.baserunning_simulator.get_runner_at_base("home")
        if not batter_runner:
            return  # Safety check

        # Calculate runner times to each base
        time_to_first = batter_runner.calculate_time_to_base("home", "first", include_leadoff=False)
        time_to_second = batter_runner.calculate_time_to_base("home", "second", include_leadoff=False)
        time_to_third = batter_runner.calculate_time_to_base("home", "third", include_leadoff=False)
        # Full circuit: home->1st->2nd->3rd->home
        time_to_home = (time_to_first +
                       batter_runner.calculate_time_to_base("first", "second", include_leadoff=False) +
                       batter_runner.calculate_time_to_base("second", "third", include_leadoff=False) +
                       batter_runner.calculate_time_to_base("third", "home", include_leadoff=False))

        # Calculate fielder throw times to each base (with transfer time)
        first_base_pos = self.field_layout.get_base_position("first")
        second_base_pos = self.field_layout.get_base_position("second")
        third_base_pos = self.field_layout.get_base_position("third")
        home_pos = self.field_layout.get_base_position("home")

        throw_to_first_result = fielder.throw_ball(first_base_pos)
        throw_to_second_result = fielder.throw_ball(second_base_pos)
        throw_to_third_result = fielder.throw_ball(third_base_pos)
        throw_to_home_result = fielder.throw_ball(home_pos)

        # Ball arrival times at each base (retrieval + transfer + flight)
        ball_at_first = ball_retrieved_time + throw_to_first_result.release_time + throw_to_first_result.flight_time
        ball_at_second = ball_retrieved_time + throw_to_second_result.release_time + throw_to_second_result.flight_time
        ball_at_third = ball_retrieved_time + throw_to_third_result.release_time + throw_to_third_result.flight_time
        ball_at_home = ball_retrieved_time + throw_to_home_result.release_time + throw_to_home_result.flight_time

        # DEBUG: Print times to understand what's happening
        DEBUG = False
        if DEBUG:
            print(f"    DEBUG Times:")
            print(f"      Ball retrieved: {ball_retrieved_time:.2f}s")
            print(f"      Runner to 1st: {time_to_first:.2f}s, Ball to 1st: {ball_at_first:.2f}s")
            print(f"      Runner to 2nd: {time_to_second:.2f}s, Ball to 2nd: {ball_at_second:.2f}s")
            print(f"      Runner to 3rd: {time_to_third:.2f}s, Ball to 3rd: {ball_at_third:.2f}s")

        # Determine how far runner can go (with conservative margin)
        # Runners are cautious - they need significant advantage to take extra base
        SAFE_MARGIN = 1.5  # Runner needs big advantage to attempt next base (increased from 0.3)

        # Can runner make home? (inside-the-park home run)
        if time_to_home + SAFE_MARGIN < ball_at_home:
            bases_to_try = 4  # Try for home
        # Can runner make third?
        elif time_to_third + SAFE_MARGIN < ball_at_third:
            bases_to_try = 3
        # Can runner make second?
        elif time_to_second + SAFE_MARGIN < ball_at_second:
            bases_to_try = 2
        # Just try for first
        else:
            bases_to_try = 1

        # Simulate the actual attempt based on decision
        if bases_to_try >= 2:
            # Advance existing runners proportionally
            runner_results = self.baserunning_simulator.advance_all_runners(bases_to_try)
            result.baserunning_results.extend(runner_results)

        # Determine outcome for batter
        if bases_to_try == 4:
            # Inside-the-park home run attempt
            if time_to_home < ball_at_home:
                result.outcome = PlayOutcome.HOME_RUN
                result.runs_scored = 1
                self.baserunning_simulator.remove_runner("home")
            else:
                result.outcome = PlayOutcome.TRIPLE  # Held at third
                batter_runner.current_base = "third"
                self.baserunning_simulator.remove_runner("home")
                self.baserunning_simulator.add_runner("third", batter_runner)
        elif bases_to_try == 3:
            result.outcome = PlayOutcome.TRIPLE
            batter_runner.current_base = "third"
            self.baserunning_simulator.remove_runner("home")
            self.baserunning_simulator.add_runner("third", batter_runner)
        elif bases_to_try == 2:
            result.outcome = PlayOutcome.DOUBLE
            batter_runner.current_base = "second"
            self.baserunning_simulator.remove_runner("home")
            self.baserunning_simulator.add_runner("second", batter_runner)
        else:
            # Try for first - simulate throw
            if ball_at_first < time_to_first - 0.1:  # Ball beats runner
                self._simulate_throw_to_first(fielder, ball_retrieved_time, batter_runner, result)
            else:
                result.outcome = PlayOutcome.SINGLE
                batter_runner.current_base = "first"
                self.baserunning_simulator.remove_runner("home")
                self.baserunning_simulator.add_runner("first", batter_runner)
    
    def _handle_ground_ball(self, ball_position: FieldPosition, result: PlayResult):
        """Handle ground ball fielding."""
        # Ground balls have very short flight time
        ground_ball_time = 0.5  # seconds for ball to reach fielder area
        
        # Simulate fielding attempt
        fielding_result = self.fielding_simulator.simulate_fielding_attempt(
            ball_position, ground_ball_time
        )
        
        result.fielding_results.append(fielding_result)
        
        if fielding_result.success:
            result.add_event(PlayEvent(
                fielding_result.ball_arrival_time, "ground_ball_fielded",
                f"Ground ball fielded by {fielding_result.fielder_name}"
            ))
            
            # Attempt throw to first
            responsible_fielder = self.fielding_simulator.fielders[fielding_result.fielder_name]
            batter_runner = self.baserunning_simulator.get_runner_at_base("home")
            
            if batter_runner:
                self._simulate_throw_to_first(
                    responsible_fielder, fielding_result.ball_arrival_time, 
                    batter_runner, result
                )
        else:
            # Ball gets through
            result.add_event(PlayEvent(
                ground_ball_time, "ball_through",
                f"Ground ball gets through {fielding_result.fielder_name}"
            ))
            result.outcome = PlayOutcome.SINGLE
    
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
        """Simulate throw to first base."""
        # Get first base position
        first_base_pos = self.field_layout.get_base_position("first")
        
        # Simulate throw
        throw_result = fielder.throw_ball(first_base_pos)
        throw_arrival_time = release_time + throw_result.release_time + throw_result.flight_time
        
        result.add_event(PlayEvent(
            release_time + throw_result.release_time, "throw_to_first",
            f"Throw to first base"
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
        elif time_difference <= SAFE_RUNNER_BIAS:
            # Close play, tie goes to runner
            outcome = "safe"
            result.outcome = PlayOutcome.SINGLE
        else:
            # Ball beats runner
            outcome = "out"
            result.outcome = PlayOutcome.GROUND_OUT
            result.outs_made = 1
        
        result.add_event(PlayEvent(
            max(throw_arrival_time, runner_arrival_time), "play_at_first",
            f"Runner {outcome} at first base"
        ))
        
        # Update runner status
        if outcome == "safe":
            batter_runner.current_base = "first"
            self.baserunning_simulator.remove_runner("home")
            self.baserunning_simulator.add_runner("first", batter_runner)
        else:
            self.baserunning_simulator.remove_runner("home")
    
    def _describe_field_location(self, position: FieldPosition) -> str:
        """Generate human-readable description of field location."""
        x, y = position.x, position.y
        
        if y < 50:
            return "infield"
        elif y < 150:
            return "shallow outfield"
        elif y < 250:
            return "outfield"
        else:
            return "deep outfield"
        
        # Could be enhanced with more specific locations (left field, etc.)
    
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