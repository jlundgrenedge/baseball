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
        
        # Consider it an air ball if it gets more than 10 feet high
        is_air_ball = max_height > 10.0
        
        return landing_pos, hang_time, is_air_ball
    
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
                            initial_time: float, result: PlayResult):
        """Handle ball in play (hit that wasn't caught)."""
        # Simulate fielder retrieving ball
        responsible_position = self.fielding_simulator.determine_responsible_fielder(ball_position)
        fielder = self.fielding_simulator.fielders[responsible_position]
        
        # Calculate time for fielder to reach ball
        retrieval_time = fielder.calculate_time_to_position(ball_position)
        ball_retrieved_time = initial_time + retrieval_time
        
        result.add_event(PlayEvent(
            ball_retrieved_time, "ball_retrieved",
            f"Ball retrieved by {responsible_position}"
        ))
        
        # Start baserunners
        batter_runner = self.baserunning_simulator.get_runner_at_base("home")
        if batter_runner:
            batter_runner.start_running_to("first")
        
        # Advance other runners
        runner_results = self.baserunning_simulator.advance_all_runners(1)
        result.baserunning_results.extend(runner_results)
        
        # Determine if throw is made to first
        throw_to_first = self._should_throw_to_first(ball_retrieved_time, batter_runner)
        
        if throw_to_first:
            self._simulate_throw_to_first(fielder, ball_retrieved_time, batter_runner, result)
        else:
            # Batter reaches first safely
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