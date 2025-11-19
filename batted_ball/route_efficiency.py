"""
Route efficiency analysis for fielding plays.

Provides detailed metrics about fielder performance including:
- Optimal vs actual distance traveled
- Route efficiency (quality of path taken)
- Required vs available speed
- Catch probability based on timing margins
- Outcome validation

This module is used to generate diagnostic logging for airborne batted balls
(line drives and fly balls) to analyze fielder route quality and catch difficulty.
"""

import math
from typing import Optional, Dict, Any
from .field_layout import FieldPosition
from .fielding import Fielder, FieldingResult


class RouteEfficiencyMetrics:
    """Container for route efficiency analysis metrics."""

    def __init__(self):
        self.fielder_name: str = ""
        self.fielder_position: str = ""
        self.reaction_time_sec: float = 0.0
        self.optimal_distance_ft: float = 0.0
        self.actual_distance_ft: float = 0.0
        self.route_efficiency: float = 0.0
        self.required_speed_ft_per_sec: float = 0.0
        self.max_speed_ft_per_sec: float = 0.0
        self.catch_probability: float = 0.0
        self.ball_arrival_time: float = 0.0
        self.fielder_arrival_time: float = 0.0
        self.margin_sec: float = 0.0
        self.outcome: str = ""

    def to_log_format(self) -> str:
        """
        Format metrics as multi-line log output.

        Returns
        -------
        str
            Formatted log block ready for game log
        """
        lines = [
            "FieldingPlayModel:",
            f"  Fielder: {self.fielder_name} ({self.fielder_position})",
            f"  ReactionTimeSec: {self.reaction_time_sec:.2f}",
            f"  OptimalDistanceFt: {self.optimal_distance_ft:.1f}",
            f"  ActualDistanceFt: {self.actual_distance_ft:.1f}",
            f"  RouteEfficiency: {self.route_efficiency:.2f}",
            f"  RequiredSpeedFtPerSec: {self.required_speed_ft_per_sec:.1f}",
            f"  MaxSpeedFtPerSec: {self.max_speed_ft_per_sec:.1f}",
            f"  CatchProbability: {self.catch_probability:.2f}",
            f"  BallArrivalTime: {self.ball_arrival_time:.2f}",
            f"  FielderArrivalTime: {self.fielder_arrival_time:.2f}",
            f"  MarginSec: {self.margin_sec:+.2f}",
            f"  Outcome: {self.outcome}",
        ]
        return "\n".join(lines)


class RouteEfficiencyAnalyzer:
    """
    Analyzes fielder route efficiency for airborne batted balls.

    Computes optimal path, actual path, efficiency ratios, and validates
    that outcomes align with physical constraints.
    """

    def __init__(self):
        """Initialize route efficiency analyzer."""
        self.debug_warnings: list = []

    def analyze_fielding_play(self,
                             fielder: Fielder,
                             fielder_start_position: FieldPosition,
                             ball_intercept_position: FieldPosition,
                             ball_hang_time: float,
                             fielding_result: FieldingResult) -> RouteEfficiencyMetrics:
        """
        Analyze a complete fielding play and generate efficiency metrics.

        Parameters
        ----------
        fielder : Fielder
            The fielder who attempted the play
        fielder_start_position : FieldPosition
            Fielder's starting position when ball was hit
        ball_intercept_position : FieldPosition
            Where the ball landed or was caught
        ball_hang_time : float
            Time ball was in the air (seconds)
        fielding_result : FieldingResult
            Result of the fielding attempt

        Returns
        -------
        RouteEfficiencyMetrics
            Complete metrics for the play
        """
        metrics = RouteEfficiencyMetrics()

        # Basic fielder information
        metrics.fielder_name = fielder.name
        metrics.fielder_position = fielding_result.fielder_position or "UNKNOWN"

        # Reaction time (first step time from fielder attributes)
        metrics.reaction_time_sec = fielder.get_first_step_time()

        # Calculate optimal distance (straight-line Euclidean distance)
        metrics.optimal_distance_ft = self._calculate_optimal_distance(
            fielder_start_position,
            ball_intercept_position
        )

        # Calculate actual distance traveled
        # This approximates the actual path distance
        metrics.actual_distance_ft = self._calculate_actual_distance(
            fielder,
            fielder_start_position,
            ball_intercept_position,
            fielding_result
        )

        # Route efficiency (optimal / actual)
        # First clamp actual distance to prevent impossible values where actual < optimal
        if metrics.actual_distance_ft > 0:
            # Clamp actual distance to be at least equal to optimal distance
            # This prevents route efficiency > 1.0 which is physically impossible
            if metrics.actual_distance_ft < metrics.optimal_distance_ft:
                metrics.actual_distance_ft = metrics.optimal_distance_ft

            # Calculate efficiency (always <= 1.0 due to clamping above)
            metrics.route_efficiency = metrics.optimal_distance_ft / metrics.actual_distance_ft

            # Ensure it's in valid range [0.0, 1.0]
            metrics.route_efficiency = min(1.0, max(0.0, metrics.route_efficiency))
        else:
            # Zero distance = perfect efficiency
            metrics.route_efficiency = 1.0

        # Fielder speed capabilities
        metrics.max_speed_ft_per_sec = fielder.get_sprint_speed_fps_statcast()

        # Required speed to make the play
        # Account for reaction time reducing available movement time
        available_movement_time = ball_hang_time - metrics.reaction_time_sec
        if available_movement_time > 0:
            metrics.required_speed_ft_per_sec = (
                metrics.optimal_distance_ft / available_movement_time
            )
        else:
            # Impossible play - no time after reaction
            metrics.required_speed_ft_per_sec = 999.9

        # Timing data from fielding result
        metrics.ball_arrival_time = fielding_result.ball_arrival_time
        metrics.fielder_arrival_time = fielding_result.fielder_arrival_time
        metrics.margin_sec = fielding_result.margin  # Already computed in FieldingResult

        # Catch probability based on time margin
        metrics.catch_probability = self._calculate_catch_probability(metrics.margin_sec)

        # Outcome determination
        metrics.outcome = self._determine_outcome(fielding_result)

        # Validation checks
        self._validate_metrics(metrics, fielding_result)

        return metrics

    def _calculate_optimal_distance(self,
                                    start_pos: FieldPosition,
                                    end_pos: FieldPosition) -> float:
        """
        Calculate optimal straight-line distance.

        Parameters
        ----------
        start_pos : FieldPosition
            Starting position
        end_pos : FieldPosition
            Ending position

        Returns
        -------
        float
            Euclidean distance in feet
        """
        dx = end_pos.x - start_pos.x
        dy = end_pos.y - start_pos.y
        # Fielders move on ground (ignore z)
        return math.sqrt(dx * dx + dy * dy)

    def _calculate_actual_distance(self,
                                   fielder: Fielder,
                                   start_pos: FieldPosition,
                                   end_pos: FieldPosition,
                                   fielding_result: FieldingResult) -> float:
        """
        Calculate actual distance traveled by fielder.

        Currently approximates using fielder's movement time and speed.
        Future enhancement: Track actual curved path if route simulation is added.

        Parameters
        ----------
        fielder : Fielder
            The fielder
        start_pos : FieldPosition
            Starting position
        end_pos : FieldPosition
            Ending position
        fielding_result : FieldingResult
            Fielding result containing timing data

        Returns
        -------
        float
            Estimated actual distance in feet
        """
        # Get fielder's actual movement time (total time - reaction time)
        reaction_time = fielder.get_first_step_time()
        total_time = fielding_result.fielder_arrival_time
        movement_time = max(0.0, total_time - reaction_time)

        # Get fielder's effective sprint speed
        max_speed = fielder.get_sprint_speed_fps_statcast()

        # Calculate optimal distance to determine route penalty
        optimal_distance = self._calculate_optimal_distance(start_pos, end_pos)

        # Apply route efficiency penalty based on distance
        # This mirrors the logic in Fielder.calculate_time_to_position()
        if optimal_distance < 30.0:
            # Short plays: minimal route inefficiency
            route_penalty = 1.0
            speed_percentage = 0.88 + (optimal_distance / 30.0) * 0.06
        elif optimal_distance < 60.0:
            # Medium plays: minor route inefficiency
            route_efficiency = fielder.get_route_efficiency()
            # Handle percentage vs decimal
            if route_efficiency > 1.0:
                route_efficiency = route_efficiency / 100.0
            route_penalty = 1.0 + (1.0 - route_efficiency) * 0.3
            speed_percentage = 0.94 + ((optimal_distance - 30.0) / 30.0) * 0.04
        else:
            # Long plays: reduced route penalty
            route_efficiency = fielder.get_route_efficiency()
            if route_efficiency > 1.0:
                route_efficiency = route_efficiency / 100.0
            route_penalty = 1.0 + (1.0 - route_efficiency) * 0.15
            speed_percentage = 0.98 + min((optimal_distance - 60.0) / 60.0, 1.0) * 0.02

        # Effective speed accounting for acceleration/distance effects
        effective_speed = max_speed * speed_percentage

        # Actual distance = optimal * route penalty
        # OR we can use: effective_speed * movement_time
        # Use the second approach as it's more accurate to what actually happened
        actual_distance = effective_speed * movement_time

        return actual_distance

    def _calculate_catch_probability(self, margin_sec: float) -> float:
        """
        Calculate expected catch probability based on time margin.

        This uses simplified thresholds. The actual catch probability in the
        simulation is more complex and includes fielder skill modifiers.

        Parameters
        ----------
        margin_sec : float
            Time margin (positive = fielder early, negative = fielder late)

        Returns
        -------
        float
            Catch probability [0.0, 1.0]
        """
        # Note: margin in FieldingResult is ball_time - fielder_time
        # So POSITIVE margin means fielder arrived EARLY (good!)
        # NEGATIVE margin means fielder arrived LATE (bad!)

        if margin_sec >= 1.2:
            # Fielder 1.2+ seconds early - very routine
            return 0.95
        elif margin_sec >= 0.5:
            # Fielder 0.5-1.2s early - routine
            return 0.70
        elif margin_sec >= 0.0:
            # Fielder arrived on time (0-0.5s early) - challenging
            return 0.50
        elif margin_sec >= -0.4:
            # Fielder slightly late (0-0.4s late) - difficult/diving
            return 0.15
        else:
            # Fielder very late (>0.4s) - nearly impossible
            return 0.02

    def _determine_outcome(self, fielding_result: FieldingResult) -> str:
        """
        Determine outcome string from fielding result.

        Parameters
        ----------
        fielding_result : FieldingResult
            Result of fielding attempt

        Returns
        -------
        str
            Outcome: "CAUGHT", "HIT", or "ERROR"
        """
        if fielding_result.success:
            return "CAUGHT"
        elif fielding_result.is_error:
            return "ERROR"
        else:
            return "HIT"

    def _validate_metrics(self,
                         metrics: RouteEfficiencyMetrics,
                         fielding_result: FieldingResult):
        """
        Validate metrics for consistency and flag anomalies.

        Parameters
        ----------
        metrics : RouteEfficiencyMetrics
            Computed metrics
        fielding_result : FieldingResult
            Fielding result
        """
        # Check A: Validate route efficiency bounds
        if metrics.route_efficiency > 1.02:
            self.debug_warnings.append(
                f"Route efficiency {metrics.route_efficiency:.2f} exceeds 1.0 - "
                f"possible calculation error"
            )

        if metrics.route_efficiency < 0.30:
            self.debug_warnings.append(
                f"Route efficiency {metrics.route_efficiency:.2f} very low (<0.30) - "
                f"possible path bug or extreme adjustment"
            )

        # Check B: Validate required speed vs max speed
        if metrics.outcome != "HIT" and metrics.required_speed_ft_per_sec > metrics.max_speed_ft_per_sec * 1.1:
            self.debug_warnings.append(
                f"WARNING: Required speed ({metrics.required_speed_ft_per_sec:.1f} ft/s) "
                f"exceeds fielder max ({metrics.max_speed_ft_per_sec:.1f} ft/s) by >10% "
                f"but outcome is {metrics.outcome}"
            )

        # Check C: Catch probability vs outcome correlation
        if metrics.catch_probability > 0.85 and metrics.outcome != "CAUGHT":
            self.debug_warnings.append(
                f"FLAG: High catch probability ({metrics.catch_probability:.2f}) "
                f"but ball was not caught - possible defensive anomaly (routine ball dropped)"
            )

        if metrics.catch_probability < 0.10 and metrics.outcome == "CAUGHT":
            self.debug_warnings.append(
                f"FLAG: Very low catch probability ({metrics.catch_probability:.2f}) "
                f"but ball was caught - exceptional/unlikely catch"
            )

        # Check D: Arrival time consistency (within 0.05s tolerance)
        # This checks that our calculated times match the fielding result
        # margin_sec should equal (ball_arrival_time - fielder_arrival_time)
        calculated_margin = metrics.ball_arrival_time - metrics.fielder_arrival_time
        time_diff = abs(calculated_margin - metrics.margin_sec)
        if time_diff > 0.05:
            self.debug_warnings.append(
                f"WARNING: Arrival time mismatch detected ({time_diff:.3f}s difference)"
            )

    def get_warnings(self) -> list:
        """
        Get all validation warnings generated during analysis.

        Returns
        -------
        list
            List of warning strings
        """
        return self.debug_warnings.copy()

    def clear_warnings(self):
        """Clear accumulated warnings."""
        self.debug_warnings.clear()
