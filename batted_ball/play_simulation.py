"""
Complete baseball play simulation engine.

Integrates trajectory physics, fielding mechanics, and baserunning physics
to simulate complete plays from bat contact to final outcomes with realistic
timing and decision-making.
"""

import numpy as np
from typing import Dict, Optional

# Import data classes from play_outcome module
from .play_outcome import PlayOutcome, PlayEvent, PlayResult

# Import field layout and core components
from .field_layout import FieldLayout, FieldPosition
from .fielding import FieldingSimulator, Fielder
from .baserunning import BaseRunner, BaserunningSimulator
from .trajectory import BattedBallResult
from .ground_ball_physics import GroundBallSimulator
from .ground_ball_interception import GroundBallInterceptor
from .outfield_interception import OutfieldInterceptor

# Import new modular components
from .play_analyzer import PlayAnalyzer
from .hit_handler import HitHandler
from .throwing_logic import ThrowingLogic
from .ground_ball_handler import GroundBallHandler
from .fly_ball_handler import FlyBallHandler


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

        # Create handler instances
        self.play_analyzer = PlayAnalyzer()
        self.throwing_logic = ThrowingLogic(self.field_layout, self.baserunning_simulator)
        self.hit_handler = HitHandler(self.baserunning_simulator, self.current_outs)
        self.ground_ball_handler = GroundBallHandler(
            self.field_layout,
            self.fielding_simulator,
            self.baserunning_simulator,
            self.ground_ball_simulator,
            self.ground_ball_interceptor,
            self.current_outs,
            hit_handler=self.hit_handler,
            throwing_logic=self.throwing_logic
        )
        self.fly_ball_handler = FlyBallHandler(
            self.field_layout,
            self.fielding_simulator,
            self.baserunning_simulator,
            self.outfield_interceptor,
            self.current_outs
        )

        # Set cross-references for handlers that need them
        self.fly_ball_handler.play_analyzer = self.play_analyzer
        self.fly_ball_handler.hit_handler = self.hit_handler
        self.fly_ball_handler.throwing_logic = self.throwing_logic

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
        self.current_outs = current_outs

        # Update current_outs in all handlers
        self.hit_handler.current_outs = current_outs
        self.ground_ball_handler.current_outs = current_outs
        self.fly_ball_handler.current_outs = current_outs

        # Capture initial runner positions before play starts
        result.initial_runner_positions = dict(self.baserunning_simulator.runners)

        # Add batter-runner to bases
        self.baserunning_simulator.add_runner("home", batter_runner)

        # Determine ball landing position and type using play analyzer
        ball_landing_pos, hang_time, is_air_ball = self.play_analyzer.analyze_batted_ball(batted_ball_result)

        # Add contact event
        result.add_event(PlayEvent(
            0.0, "contact",
            f"Ball hit to {self.play_analyzer.describe_field_location(ball_landing_pos)}"
        ))

        if is_air_ball:
            # Check for home run FIRST before attempting catch
            distance_ft = np.sqrt(ball_landing_pos.x**2 + ball_landing_pos.y**2)
            spray_angle = np.arctan2(ball_landing_pos.x, ball_landing_pos.y) * 180.0 / np.pi
            peak_height = batted_ball_result.peak_height if batted_ball_result else 0

            # Determine fence distance and height based on spray angle
            abs_angle = abs(spray_angle)
            if abs_angle < 10:  # Dead center
                fence_distance = 400.0
                fence_height = 10.0
            elif abs_angle < 25:  # Center-left/right gaps
                fence_distance = 380.0
                fence_height = 10.0
            elif abs_angle < 40:  # Deeper alleys
                fence_distance = 360.0
                fence_height = 10.0
            else:  # Down the lines
                fence_distance = 330.0
                fence_height = 10.0

            # Check if ball cleared fence
            # CRITICAL: Must check height AT THE FENCE, not peak height!
            is_home_run = False
            if distance_ft >= fence_distance:
                # Get the ball's height when it crosses the fence distance
                height_at_fence = batted_ball_result.get_height_at_distance(fence_distance) if batted_ball_result else None

                if height_at_fence is not None and height_at_fence > fence_height:
                    # Ball was above fence height when it crossed the fence distance
                    is_home_run = True
                elif distance_ft >= fence_distance + 30:  # 30+ ft past fence = definite HR
                    # Ball landed well beyond fence (even if low trajectory)
                    is_home_run = True

            if is_home_run:
                # Ball cleared fence - it's a home run!
                result.outcome = PlayOutcome.HOME_RUN
                result.runs_scored = 1 + len([r for r in result.initial_runner_positions.values() if r is not None])
                result.add_event(PlayEvent(
                    0.0, "fly_ball_analysis",
                    f"Fly ball coordinates: ({ball_landing_pos.x:.1f}, {ball_landing_pos.y:.1f}) ft, distance {distance_ft:.1f} ft, hang time {hang_time:.2f}s"
                ))
                result.add_event(PlayEvent(
                    hang_time, "home_run",
                    f"HOME RUN! Ball travels {distance_ft:.0f} feet over the {fence_distance:.0f}-foot fence"
                ))
                # Finalize and return - no catch attempt needed
                result.play_description = result.generate_description()
                return result

            # Not a home run - attempt catch at landing position using fly ball handler
            catch_result = self.fly_ball_handler.simulate_catch_attempt(ball_landing_pos, hang_time, result)

            if catch_result.success:
                # Ball caught - delegate to fly ball handler
                self.fly_ball_handler.handle_fly_ball_caught(catch_result, result)
            elif hasattr(catch_result, 'is_error') and catch_result.is_error:
                # FIX FOR BUTTERFINGERS BUG: Fielding error (dropped with positive time margin)
                # Ball stays at fielder's location, runners advance 1-2 bases only
                self.fly_ball_handler.handle_fielding_error(catch_result, ball_landing_pos, hang_time, result)
            else:
                # Ball dropped - becomes hit (trajectory interception already ran)
                self.fly_ball_handler.handle_ball_in_play(ball_landing_pos, hang_time, result)
        else:
            # Ground ball - delegate to ground ball handler
            self.ground_ball_handler.handle_ground_ball(ball_landing_pos, result)

        # Finalize result
        result.play_description = result.generate_description()
        return result

    def reset_simulation(self):
        """Reset simulator for new play."""
        self.current_time = 0.0
        self.baserunning_simulator = BaserunningSimulator(self.field_layout)

        # CRITICAL: Update all handlers to use the new baserunning simulator
        # Otherwise they'll reference the old (empty) simulator
        self.hit_handler.baserunning_simulator = self.baserunning_simulator
        self.fly_ball_handler.baserunning_simulator = self.baserunning_simulator
        self.ground_ball_handler.baserunning_simulator = self.baserunning_simulator
        self.throwing_logic.baserunning_simulator = self.baserunning_simulator


# Convenience function for setting up simulations
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
