"""
Baseball baserunning mechanics and physics simulation.

Models individual runner attributes, acceleration physics, base-to-base running,
turn efficiency, sliding mechanics, and baserunner advancement for realistic 
baserunning simulation.
"""

import numpy as np
from typing import Dict, List, Tuple, Optional, Union
from enum import Enum
from .constants import (
    # Baserunning attributes
    RUNNER_SPRINT_SPEED_MIN, RUNNER_SPRINT_SPEED_AVG,
    RUNNER_SPRINT_SPEED_ELITE, RUNNER_SPRINT_SPEED_MAX,
    RUNNER_ACCELERATION_MIN, RUNNER_ACCELERATION_AVG,
    RUNNER_ACCELERATION_ELITE, RUNNER_ACCELERATION_MAX,
    RUNNER_REACTION_TIME_MIN, RUNNER_REACTION_TIME_AVG,
    RUNNER_REACTION_TIME_POOR, RUNNER_REACTION_TIME_MAX,
    # Base-to-base times for validation
    HOME_TO_FIRST_TIME_MIN, HOME_TO_FIRST_TIME_AVG,
    HOME_TO_FIRST_TIME_SLOW, HOME_TO_FIRST_TIME_MAX,
    # Turn mechanics
    TURN_RADIUS_MIN, TURN_RADIUS_AVG, TURN_RADIUS_ELITE,
    TURN_SPEED_RETENTION_POOR, TURN_SPEED_RETENTION_AVG, TURN_SPEED_RETENTION_ELITE,
    # Sliding mechanics
    SLIDE_DECELERATION_RATE, SLIDE_DISTANCE_MIN, SLIDE_DISTANCE_AVG, SLIDE_DISTANCE_MAX,
    # Lead-off distances
    LEADOFF_FIRST_BASE_MIN, LEADOFF_FIRST_BASE_AVG, LEADOFF_FIRST_BASE_MAX,
    LEADOFF_SECOND_BASE_MIN, LEADOFF_SECOND_BASE_AVG, LEADOFF_SECOND_BASE_MAX,
    LEADOFF_THIRD_BASE_MIN, LEADOFF_THIRD_BASE_AVG, LEADOFF_THIRD_BASE_MAX,
    # Attribute rating scales
    BASERUNNING_SPEED_RATING_MIN, BASERUNNING_SPEED_RATING_AVG,
    BASERUNNING_SPEED_RATING_ELITE, BASERUNNING_SPEED_RATING_MAX,
    BASERUNNING_ACCELERATION_RATING_MIN, BASERUNNING_ACCELERATION_RATING_AVG,
    BASERUNNING_ACCELERATION_RATING_ELITE, BASERUNNING_ACCELERATION_RATING_MAX,
    BASERUNNING_BASERUNNING_RATING_MIN, BASERUNNING_BASERUNNING_RATING_AVG,
    BASERUNNING_BASERUNNING_RATING_ELITE, BASERUNNING_BASERUNNING_RATING_MAX,
    # Field layout
    BASE_PATH_LENGTH,
    # Physics constants
    FEET_TO_METERS, METERS_TO_FEET,
    # Play timing
    CLOSE_PLAY_TOLERANCE, SAFE_RUNNER_BIAS,
)
from .field_layout import FieldPosition, FieldLayout


class RunnerState(Enum):
    """Enumeration of possible runner states."""
    LEADING_OFF = "leading_off"
    RUNNING = "running"
    SLIDING = "sliding" 
    ON_BASE = "on_base"
    SCORING = "scoring"
    OUT = "out"
    SAFE = "safe"


class BaserunningResult:
    """Result of a baserunning attempt."""
    
    def __init__(self,
                 runner_name: str,
                 from_base: str,
                 to_base: str,
                 arrival_time: float,
                 final_position: FieldPosition,
                 outcome: str):
        """
        Initialize baserunning result.
        
        Parameters
        ----------
        runner_name : str
            Name of the runner
        from_base : str
            Starting base
        to_base : str
            Target base
        arrival_time : float
            Time when runner reached target (seconds)
        final_position : FieldPosition
            Final position of runner
        outcome : str
            Result ('safe', 'out', 'running')
        """
        self.runner_name = runner_name
        self.from_base = from_base
        self.to_base = to_base
        self.arrival_time = arrival_time
        self.final_position = final_position
        self.outcome = outcome


class BaseRunner:
    """
    Represents a baserunner with physical attributes and running mechanics.
    
    Core Physical Attributes:
    - sprint_speed: Maximum running speed (0-100 rating)
    - acceleration: Rate of acceleration to top speed (0-100 rating)
    - base_running_iq: Baserunning intelligence and decision making (0-100 rating)
    - sliding_ability: Sliding technique and timing (0-100 rating)
    - turn_efficiency: Ability to maintain speed through turns (0-100 rating)
    """
    
    def __init__(self,
                 name: str = "Runner",
                 # Physical attributes (0-100 scale)
                 sprint_speed: int = 50,
                 acceleration: int = 50,
                 base_running_iq: int = 50,
                 sliding_ability: int = 50,
                 turn_efficiency: int = 50,
                 # Current state
                 current_base: str = "home",
                 leadoff_distance: float = 0.0):
        """
        Initialize baserunner with attribute ratings.
        
        Parameters
        ----------
        name : str
            Runner's name/identifier
        sprint_speed : int (0-100)
            Sprint speed rating (50=avg MLB ~27 ft/s, 80=elite ~30 ft/s)
        acceleration : int (0-100)
            Acceleration rating (50=avg ~14 ft/s², 80=elite ~18 ft/s²)
        base_running_iq : int (0-100)
            Baserunning intelligence (affects leads, jumps, decisions)
        sliding_ability : int (0-100)
            Sliding technique and timing
        turn_efficiency : int (0-100)
            Ability to maintain speed through turns (50=avg, 80=elite)
        current_base : str
            Current base ('home', 'first', 'second', 'third')
        leadoff_distance : float
            Current leadoff distance in feet
        """
        self.name = name
        
        # Clip all ratings to 0-100 scale
        self.sprint_speed = np.clip(sprint_speed, 0, 100)
        self.acceleration = np.clip(acceleration, 0, 100)
        self.base_running_iq = np.clip(base_running_iq, 0, 100)
        self.sliding_ability = np.clip(sliding_ability, 0, 100)
        self.turn_efficiency = np.clip(turn_efficiency, 0, 100)
        
        # Current state
        self.current_base = current_base
        self.leadoff_distance = leadoff_distance
        self.state = RunnerState.ON_BASE
        self.current_position = None
        self.target_base = None
        
        # Movement state
        self.current_velocity = 0.0  # ft/s along base path
        self.distance_traveled = 0.0  # ft from starting position
        self.is_sliding = False
        self.slide_start_distance = 0.0
    
    def get_sprint_speed_fps(self) -> float:
        """Convert sprint speed rating to feet per second."""
        min_speed = RUNNER_SPRINT_SPEED_MIN
        max_speed = RUNNER_SPRINT_SPEED_MAX
        avg_speed = RUNNER_SPRINT_SPEED_AVG
        
        if self.sprint_speed <= 50:
            factor = (self.sprint_speed - 20) / 30.0
            speed = min_speed + factor * (avg_speed - min_speed)
        else:
            factor = (self.sprint_speed - 50) / 50.0
            speed = avg_speed + factor * (max_speed - avg_speed)
        
        return speed
    
    def get_acceleration_fps2(self) -> float:
        """Convert acceleration rating to feet per second squared."""
        min_accel = RUNNER_ACCELERATION_MIN
        max_accel = RUNNER_ACCELERATION_MAX
        avg_accel = RUNNER_ACCELERATION_AVG
        
        if self.acceleration <= 50:
            factor = (self.acceleration - 20) / 30.0
            accel = min_accel + factor * (avg_accel - min_accel)
        else:
            factor = (self.acceleration - 50) / 50.0
            accel = avg_accel + factor * (max_accel - avg_accel)
        
        return accel
    
    def get_reaction_time_seconds(self) -> float:
        """Get reaction time based on baserunning IQ."""
        min_time = RUNNER_REACTION_TIME_MAX  # Worst reaction
        max_time = RUNNER_REACTION_TIME_MIN  # Best reaction
        avg_time = RUNNER_REACTION_TIME_AVG
        
        # Higher IQ = faster reaction
        if self.base_running_iq <= 50:
            factor = (self.base_running_iq - 20) / 30.0
            time = min_time - factor * (min_time - avg_time)
        else:
            factor = (self.base_running_iq - 50) / 50.0
            time = avg_time - factor * (avg_time - max_time)
        
        return max(time, 0.0)
    
    def get_turn_speed_retention(self) -> float:
        """Get speed retention factor during turns."""
        if self.turn_efficiency <= 50:
            factor = (self.turn_efficiency - 20) / 30.0
            retention = TURN_SPEED_RETENTION_POOR + factor * (TURN_SPEED_RETENTION_AVG - TURN_SPEED_RETENTION_POOR)
        else:
            factor = (self.turn_efficiency - 50) / 50.0
            retention = TURN_SPEED_RETENTION_AVG + factor * (TURN_SPEED_RETENTION_ELITE - TURN_SPEED_RETENTION_AVG)
        
        return retention
    
    def get_optimal_leadoff(self, base: str) -> float:
        """Get optimal leadoff distance for given base."""
        # Base leadoff distances on IQ rating
        if base == "first":
            min_lead = LEADOFF_FIRST_BASE_MIN
            max_lead = LEADOFF_FIRST_BASE_MAX
            avg_lead = LEADOFF_FIRST_BASE_AVG
        elif base == "second":
            min_lead = LEADOFF_SECOND_BASE_MIN
            max_lead = LEADOFF_SECOND_BASE_MAX
            avg_lead = LEADOFF_SECOND_BASE_AVG
        elif base == "third":
            min_lead = LEADOFF_THIRD_BASE_MIN
            max_lead = LEADOFF_THIRD_BASE_MAX
            avg_lead = LEADOFF_THIRD_BASE_AVG
        else:
            return 0.0  # No leadoff from home
        
        # Higher IQ = more aggressive leads (but also smarter)
        if self.base_running_iq <= 50:
            factor = (self.base_running_iq - 20) / 30.0
            leadoff = min_lead + factor * (avg_lead - min_lead)
        else:
            factor = (self.base_running_iq - 50) / 50.0
            leadoff = avg_lead + factor * (max_lead - avg_lead)
        
        return leadoff
    
    def calculate_time_to_base(self, from_base: str, to_base: str, 
                              include_leadoff: bool = True) -> float:
        """
        Calculate time to run from one base to another.
        
        Parameters
        ----------
        from_base : str
            Starting base
        to_base : str
            Target base
        include_leadoff : bool
            Whether to include leadoff advantage
            
        Returns
        -------
        float
            Time in seconds to reach target base
        """
        # Calculate total distance
        if from_base == "home" and to_base == "first":
            total_distance = BASE_PATH_LENGTH
        elif from_base == "first" and to_base == "second":
            total_distance = BASE_PATH_LENGTH
        elif from_base == "second" and to_base == "third":
            total_distance = BASE_PATH_LENGTH
        elif from_base == "third" and to_base == "home":
            total_distance = BASE_PATH_LENGTH
        elif from_base == "first" and to_base == "third":
            total_distance = 2 * BASE_PATH_LENGTH
        elif from_base == "first" and to_base == "home":
            total_distance = 3 * BASE_PATH_LENGTH
        elif from_base == "second" and to_base == "home":
            total_distance = 2 * BASE_PATH_LENGTH
        elif from_base == "home" and to_base == "second":
            total_distance = 2 * BASE_PATH_LENGTH
        elif from_base == "home" and to_base == "third":
            total_distance = 3 * BASE_PATH_LENGTH
        elif from_base == "home" and to_base == "home":  # Complete circuit
            total_distance = 4 * BASE_PATH_LENGTH
        else:
            raise ValueError(f"Invalid base combination: {from_base} to {to_base}")
        
        # Subtract leadoff if applicable
        if include_leadoff and from_base != "home":
            leadoff = self.get_optimal_leadoff(from_base)
            total_distance -= leadoff
        
        # Get physical attributes
        max_speed = self.get_sprint_speed_fps()
        acceleration = self.get_acceleration_fps2()
        reaction_time = self.get_reaction_time_seconds()
        
        # Account for turn efficiency if rounding bases
        need_turn = (
            (from_base == "home" and to_base not in ["first"]) or
            (from_base == "first" and to_base not in ["second"]) or
            (from_base == "second" and to_base not in ["third"]) or
            (from_base == "third" and to_base not in ["home"])
        )
        
        if need_turn:
            turn_retention = self.get_turn_speed_retention()
            effective_max_speed = max_speed * turn_retention
        else:
            effective_max_speed = max_speed
        
        # Calculate running time using kinematics
        time_to_max_speed = effective_max_speed / acceleration
        distance_during_acceleration = 0.5 * acceleration * time_to_max_speed**2
        
        if total_distance <= distance_during_acceleration:
            # Never reach max speed
            running_time = np.sqrt(2 * total_distance / acceleration)
        else:
            # Reach max speed, then constant velocity
            remaining_distance = total_distance - distance_during_acceleration
            time_at_max_speed = remaining_distance / effective_max_speed
            running_time = time_to_max_speed + time_at_max_speed
        
        total_time = reaction_time + running_time
        return total_time
    
    def should_slide(self, distance_to_base: float, current_speed: float) -> bool:
        """
        Determine if runner should slide based on distance and speed.
        
        Parameters
        ----------
        distance_to_base : float
            Distance to target base in feet
        current_speed : float
            Current running speed in ft/s
            
        Returns
        -------
        bool
            True if should slide
        """
        # Slide if running fast and close to base
        slide_threshold_distance = SLIDE_DISTANCE_AVG * (self.sliding_ability / 100.0 + 0.5)
        speed_threshold = 15.0  # ft/s minimum speed to consider sliding
        
        return (distance_to_base <= slide_threshold_distance and 
                current_speed >= speed_threshold)
    
    def calculate_slide_distance(self, initial_speed: float) -> float:
        """
        Calculate distance covered during slide.
        
        Parameters
        ----------
        initial_speed : float
            Speed when slide begins (ft/s)
            
        Returns
        -------
        float
            Distance covered during slide (feet)
        """
        # Use kinematic equation: v² = u² + 2as
        # Final velocity = 0, initial velocity = initial_speed
        # Deceleration = SLIDE_DECELERATION_RATE
        
        slide_distance = (initial_speed**2) / (2 * SLIDE_DECELERATION_RATE)
        
        # Clamp to reasonable bounds
        slide_distance = np.clip(slide_distance, SLIDE_DISTANCE_MIN, SLIDE_DISTANCE_MAX)
        
        # Adjust for sliding ability
        ability_factor = 0.8 + (self.sliding_ability / 100.0) * 0.4  # 0.8 to 1.2 multiplier
        slide_distance *= ability_factor
        
        return slide_distance
    
    def simulate_advance(self, target_base: str, current_time: float = 0.0) -> BaserunningResult:
        """
        Simulate advancement to target base.
        
        Parameters
        ----------
        target_base : str
            Base to advance to
        current_time : float
            Current simulation time
            
        Returns
        -------
        BaserunningResult
            Result of advancement attempt
        """
        start_base = self.current_base
        
        # Calculate time to reach base
        travel_time = self.calculate_time_to_base(start_base, target_base)
        arrival_time = current_time + travel_time
        
        # Simulate position (simplified - assuming straight line for now)
        # In full implementation, would trace actual path around bases
        field_layout = FieldLayout()
        target_position = field_layout.get_base_position(target_base)
        
        # Update runner state
        self.current_base = target_base
        self.target_base = None
        self.state = RunnerState.SAFE
        
        return BaserunningResult(
            runner_name=self.name,
            from_base=start_base,
            to_base=target_base,
            arrival_time=arrival_time,
            final_position=target_position,
            outcome="safe"
        )
    
    def get_home_to_first_time(self) -> float:
        """Get home-to-first time for validation against MLB data."""
        return self.calculate_time_to_base("home", "first", include_leadoff=False)
    
    def start_leading_off(self, base: str):
        """Start taking a leadoff from specified base."""
        self.leadoff_distance = self.get_optimal_leadoff(base)
        self.state = RunnerState.LEADING_OFF
    
    def start_running_to(self, target_base: str):
        """Start running to target base."""
        self.target_base = target_base
        self.state = RunnerState.RUNNING
        self.current_velocity = 0.0
        self.distance_traveled = 0.0
    
    def update_position(self, dt: float):
        """
        Update runner position during simulation step.
        
        Parameters
        ----------
        dt : float
            Time step in seconds
        """
        if self.state != RunnerState.RUNNING:
            return
        
        max_speed = self.get_sprint_speed_fps()
        acceleration = self.get_acceleration_fps2()
        
        if self.is_sliding:
            # Decelerate during slide
            self.current_velocity = max(0.0, self.current_velocity - SLIDE_DECELERATION_RATE * dt)
        else:
            # Accelerate toward max speed
            if self.current_velocity < max_speed:
                self.current_velocity = min(max_speed, self.current_velocity + acceleration * dt)
            
            # Check if should start sliding
            # (This is simplified - full implementation would calculate exact distance to base)
            if self.current_velocity > 15.0:  # Only slide if running fast
                estimated_distance_to_base = 10.0  # Placeholder
                if self.should_slide(estimated_distance_to_base, self.current_velocity):
                    self.is_sliding = True
                    self.slide_start_distance = self.distance_traveled
        
        # Update distance traveled
        self.distance_traveled += self.current_velocity * dt
    
    def __repr__(self):
        return (f"BaseRunner(name='{self.name}', "
                f"speed={self.sprint_speed}, iq={self.base_running_iq}, "
                f"base='{self.current_base}')")


class BaserunningSimulator:
    """
    Manages baserunning simulation for multiple runners.
    """
    
    def __init__(self, field_layout: FieldLayout):
        """
        Initialize baserunning simulator.
        
        Parameters
        ----------
        field_layout : FieldLayout
            Field layout for base positions
        """
        self.field_layout = field_layout
        self.runners = {}  # base -> runner mapping
        self.current_time = 0.0
    
    def add_runner(self, base: str, runner: BaseRunner):
        """Add a runner to specified base."""
        runner.current_base = base
        self.runners[base] = runner
    
    def remove_runner(self, base: str):
        """Remove runner from specified base."""
        if base in self.runners:
            del self.runners[base]
    
    def advance_all_runners(self, bases_to_advance: int = 1) -> List[BaserunningResult]:
        """
        Advance all runners by specified number of bases.
        
        Parameters
        ----------
        bases_to_advance : int
            Number of bases to advance (1 for single, 2 for double, etc.)
            
        Returns
        -------
        List[BaserunningResult]
            Results for each runner's advancement
        """
        results = []
        base_order = ["home", "first", "second", "third"]
        
        # Process runners in reverse order to avoid conflicts
        runners_to_process = list(self.runners.items())
        runners_to_process.sort(key=lambda x: base_order.index(x[0]), reverse=True)
        
        for base, runner in runners_to_process:
            if base == "home":
                continue  # Batter-runner handled separately
            
            # Determine target base
            current_idx = base_order.index(base)
            target_idx = current_idx + bases_to_advance
            
            if target_idx >= len(base_order):
                # Scoring
                target_base = "home"
                result = runner.simulate_advance(target_base, self.current_time)
                results.append(result)
                self.remove_runner(base)
            else:
                target_base = base_order[target_idx]
                result = runner.simulate_advance(target_base, self.current_time)
                results.append(result)
                self.remove_runner(base)
                self.add_runner(target_base, runner)
        
        return results
    
    def get_runner_at_base(self, base: str) -> Optional[BaseRunner]:
        """Get runner currently at specified base."""
        return self.runners.get(base)
    
    def simulate_race_to_base(self, runner: BaseRunner, target_base: str,
                             ball_arrival_time: float) -> str:
        """
        Simulate race between runner and ball to base.
        
        Parameters
        ----------
        runner : BaseRunner
            Runner attempting to reach base
        target_base : str
            Base being contested
        ball_arrival_time : float
            Time when ball arrives at base
            
        Returns
        -------
        str
            Outcome ('safe', 'out', 'close')
        """
        runner_time = runner.calculate_time_to_base(runner.current_base, target_base)
        runner_arrival = self.current_time + runner_time
        
        # Compare times
        time_difference = runner_arrival - ball_arrival_time
        
        if time_difference <= -CLOSE_PLAY_TOLERANCE:
            return "safe"  # Runner clearly beats ball
        elif time_difference <= SAFE_RUNNER_BIAS:
            return "safe"  # Close play, tie goes to runner
        elif time_difference <= CLOSE_PLAY_TOLERANCE:
            return "close"  # Very close play
        else:
            return "out"   # Ball clearly beats runner


# Convenience functions for creating runners
def create_speed_runner(name: str) -> BaseRunner:
    """Create a speed-focused runner."""
    return BaseRunner(
        name=name,
        sprint_speed=85,
        acceleration=85,
        base_running_iq=70,
        sliding_ability=60,
        turn_efficiency=80
    )


def create_smart_runner(name: str) -> BaseRunner:
    """Create an intelligent baserunner."""
    return BaseRunner(
        name=name,
        sprint_speed=60,
        acceleration=50,
        base_running_iq=90,
        sliding_ability=80,
        turn_efficiency=75
    )


def create_average_runner(name: str) -> BaseRunner:
    """Create an average runner."""
    return BaseRunner(
        name=name,
        sprint_speed=50,
        acceleration=50,
        base_running_iq=50,
        sliding_ability=50,
        turn_efficiency=50
    )


def create_slow_runner(name: str) -> BaseRunner:
    """Create a slow runner."""
    return BaseRunner(
        name=name,
        sprint_speed=25,
        acceleration=30,
        base_running_iq=40,
        sliding_ability=40,
        turn_efficiency=40
    )


def validate_home_to_first_times():
    """Validate that home-to-first times match MLB expectations."""
    print("Home-to-First Time Validation:")
    print(f"Expected range: {HOME_TO_FIRST_TIME_MIN:.1f}s - {HOME_TO_FIRST_TIME_MAX:.1f}s")
    print(f"MLB average: {HOME_TO_FIRST_TIME_AVG:.1f}s")
    print()
    
    runners = [
        ("Elite Speed", create_speed_runner("Speed")),
        ("Average", create_average_runner("Average")),
        ("Slow", create_slow_runner("Slow"))
    ]
    
    for name, runner in runners:
        time = runner.get_home_to_first_time()
        print(f"{name:12}: {time:.2f}s")
    
    print()


# =============================================================================
# FORCE PLAY DETECTION
# =============================================================================

def detect_force_situation(runners: Dict[str, 'BaseRunner'], batter_running: bool = True) -> Dict[str, bool]:
    """
    Determine which runners are forced to advance.
    
    A runner is forced when:
    - A runner behind them is forced to advance (chain reaction)
    - The batter hits the ball and must run to first
    
    Parameters
    ----------
    runners : Dict[str, BaseRunner]
        Current baserunners (base name -> runner)
    batter_running : bool
        Whether batter is running to first (default True)
        
    Returns
    -------
    Dict[str, bool]
        Mapping of base -> is_forced (True/False)
        
    Examples
    --------
    >>> # Runner on 1st only - forced to 2nd
    >>> runners = {"first": runner1}
    >>> forces = detect_force_situation(runners)
    >>> forces["first"]  # True - must advance to 2nd
    
    >>> # Runners on 1st and 2nd - both forced
    >>> runners = {"first": runner1, "second": runner2}
    >>> forces = detect_force_situation(runners)
    >>> forces["first"]  # True - must advance to 2nd
    >>> forces["second"]  # True - forced by runner on 1st
    
    >>> # Runner on 2nd only - NOT forced
    >>> runners = {"second": runner2}
    >>> forces = detect_force_situation(runners)
    >>> forces.get("second", False)  # False - can stay
    """
    forces = {}
    
    if not batter_running:
        return forces  # No forces if batter didn't run
    
    # Work backwards from first base
    # Runner on 1st is ALWAYS forced when batter runs
    if "first" in runners:
        forces["first"] = True
        
        # If runner on 2nd, they're forced too (by runner on 1st)
        if "second" in runners:
            forces["second"] = True
            
            # If runner on 3rd, they're forced too (by runner on 2nd)
            if "third" in runners:
                forces["third"] = True
    
    return forces


def get_force_base(current_base: str) -> str:
    """
    Get the base a forced runner must advance to.
    
    Parameters
    ----------
    current_base : str
        Current base occupied by runner
        
    Returns
    -------
    str
        Target base for forced runner
    """
    base_advancement = {
        "home": "first",
        "first": "second",
        "second": "third",
        "third": "home"
    }
    return base_advancement.get(current_base, "home")


def decide_runner_advancement(
    current_base: str,
    hit_type: str,
    ball_location: FieldPosition,
    fielder_position: str,
    fielder_arm_strength: float,
    is_fly_ball: bool = False,
    fly_ball_depth: float = 0.0,
    runner_speed_rating: float = 50.0,
    runner_baserunning_rating: float = 50.0,
    is_forced: bool = False,
    outs: int = 0
) -> Dict[str, any]:
    """
    Decide how far a runner should attempt to advance based on situation.
    
    This implements realistic baserunning decision logic:
    - Force situations: runner MUST advance
    - Fly balls: tag up if deep enough and runner is fast enough
    - Singles: advance 1 base (2 bases if ball hit to RF with runner on 1st)
    - Doubles: advance to 3rd (only score from 2nd with 2 outs or if ball is deep)
    - Triples: everyone scores
    
    Parameters
    ----------
    current_base : str
        Runner's current base ("first", "second", "third")
    hit_type : str
        Type of hit ("single", "double", "triple", "fly_ball")
    ball_location : FieldPosition
        Where the ball landed/was caught
    fielder_position : str
        Position of fielder who fielded the ball
    fielder_arm_strength : float
        Fielder's arm strength rating (0-100)
    is_fly_ball : bool
        Whether this is a fly ball (for tag-up logic)
    fly_ball_depth : float
        Distance of fly ball in feet (for tag-up decisions)
    runner_speed_rating : float
        Runner's speed rating (0-100)
    runner_baserunning_rating : float
        Runner's baserunning intelligence rating (0-100)
    is_forced : bool
        Whether runner is forced to advance
    outs : int
        Number of outs (affects aggressiveness)
        
    Returns
    -------
    dict
        Dictionary with:
        - target_base: str - base runner should attempt to reach
        - should_tag_up: bool - whether runner should tag up (fly balls)
        - advancement_bases: int - number of bases to advance
        - risk_level: str - "safe", "aggressive", "very_risky"
    """
    import numpy as np
    
    # Force situations - runner MUST advance
    if is_forced:
        return {
            "target_base": get_force_base(current_base),
            "should_tag_up": False,
            "advancement_bases": 1,
            "risk_level": "safe"
        }
    
    # Fly ball tag-up logic
    if is_fly_ball:
        should_tag = False
        target = current_base  # Default: stay on base
        risk = "safe"
        
        # Tag up from 3rd base on any fly ball with <2 outs
        if current_base == "third" and outs < 2:
            if fly_ball_depth > 200:  # Medium or deep fly
                should_tag = True
                target = "home"
                risk = "safe"
            elif fly_ball_depth > 150 and runner_speed_rating > 60:
                should_tag = True
                target = "home"
                risk = "aggressive"
        
        # Tag up from 2nd to 3rd on deep flies
        elif current_base == "second":
            if fly_ball_depth > 300 and runner_speed_rating > 50:
                should_tag = True
                target = "third"
                risk = "safe"
        
        # Rarely tag from 1st (need very deep fly + elite speed)
        elif current_base == "first":
            if fly_ball_depth > 350 and runner_speed_rating > 80:
                should_tag = True
                target = "second"
                risk = "aggressive"
        
        return {
            "target_base": target,
            "should_tag_up": should_tag,
            "advancement_bases": 1 if should_tag else 0,
            "risk_level": risk
        }
    
    # Ground ball / hit advancement logic
    distance = np.sqrt(ball_location.x**2 + ball_location.y**2)
    
    # Singles
    if hit_type == "single":
        if current_base == "third":
            # Always score from 3rd on single
            return {
                "target_base": "home",
                "should_tag_up": False,
                "advancement_bases": 1,
                "risk_level": "safe"
            }
        
        elif current_base == "second":
            # Usually score from 2nd on single
            # Don't score only if: strong arm CF + shallow single
            if fielder_position == "CF" and fielder_arm_strength > 75 and distance < 180:
                return {
                    "target_base": "third",
                    "should_tag_up": False,
                    "advancement_bases": 1,
                    "risk_level": "safe"
                }
            else:
                return {
                    "target_base": "home",
                    "should_tag_up": False,
                    "advancement_bases": 2,  # 2nd to home
                    "risk_level": "safe"
                }
        
        elif current_base == "first":
            # First to third opportunity on single
            # Go for it if: ball to RF, weak arm, deep ball, good baserunning
            angle = np.arctan2(ball_location.x, ball_location.y) * 180 / np.pi
            is_to_right_field = angle > 20  # Ball to right side
            
            if (is_to_right_field and 
                (fielder_arm_strength < 60 or distance > 250) and
                runner_baserunning_rating > 60):
                return {
                    "target_base": "third",
                    "should_tag_up": False,
                    "advancement_bases": 2,
                    "risk_level": "aggressive"
                }
            else:
                return {
                    "target_base": "second",
                    "should_tag_up": False,
                    "advancement_bases": 1,
                    "risk_level": "safe"
                }
    
    # Doubles
    elif hit_type == "double":
        if current_base == "third":
            # Always score from 3rd on double
            return {
                "target_base": "home",
                "should_tag_up": False,
                "advancement_bases": 1,
                "risk_level": "safe"
            }
        
        elif current_base == "second":
            # Score from 2nd on double MOST of the time
            # Don't score only if: shallow double to CF with strong arm
            if fielder_position == "CF" and fielder_arm_strength > 75 and distance < 300:
                return {
                    "target_base": "third",
                    "should_tag_up": False,
                    "advancement_bases": 1,
                    "risk_level": "safe"
                }
            else:
                # Usually score from 2nd on double
                return {
                    "target_base": "home",
                    "should_tag_up": False,
                    "advancement_bases": 2,
                    "risk_level": "safe"
                }
        
        elif current_base == "first":
            # First to third on double (rarely try to score)
            if outs == 2 and runner_speed_rating > 75 and distance > 380:
                return {
                    "target_base": "home",
                    "should_tag_up": False,
                    "advancement_bases": 3,
                    "risk_level": "very_risky"
                }
            else:
                return {
                    "target_base": "third",
                    "should_tag_up": False,
                    "advancement_bases": 2,
                    "risk_level": "safe"
                }
    
    # Triples - everyone scores
    elif hit_type == "triple":
        return {
            "target_base": "home",
            "should_tag_up": False,
            "advancement_bases": 3 if current_base == "first" else (2 if current_base == "second" else 1),
            "risk_level": "safe"
        }
    
    # Default: advance 1 base
    return {
        "target_base": get_force_base(current_base),
        "should_tag_up": False,
        "advancement_bases": 1,
        "risk_level": "safe"
    }


if __name__ == "__main__":
    validate_home_to_first_times()