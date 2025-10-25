"""
Baseball fielding mechanics and physics simulation.

Models individual fielder attributes, reaction times, movement physics,
catching mechanics, and throwing physics for realistic defensive play simulation.
"""

import numpy as np
from typing import Dict, List, Tuple, Optional, Union
from .constants import (
    # Fielding attributes
    FIELDER_SPRINT_SPEED_MIN, FIELDER_SPRINT_SPEED_AVG, 
    FIELDER_SPRINT_SPEED_ELITE, FIELDER_SPRINT_SPEED_MAX,
    FIELDER_ACCELERATION_MIN, FIELDER_ACCELERATION_AVG,
    FIELDER_ACCELERATION_ELITE, FIELDER_ACCELERATION_MAX,
    FIELDER_REACTION_TIME_MIN, FIELDER_REACTION_TIME_AVG,
    FIELDER_REACTION_TIME_POOR, FIELDER_REACTION_TIME_MAX,
    # Throwing attributes
    INFIELDER_THROW_VELOCITY_MIN, INFIELDER_THROW_VELOCITY_AVG,
    INFIELDER_THROW_VELOCITY_ELITE, INFIELDER_THROW_VELOCITY_MAX,
    OUTFIELDER_THROW_VELOCITY_MIN, OUTFIELDER_THROW_VELOCITY_AVG,
    OUTFIELDER_THROW_VELOCITY_ELITE, OUTFIELDER_THROW_VELOCITY_MAX,
    INFIELDER_TRANSFER_TIME_MIN, INFIELDER_TRANSFER_TIME_AVG,
    INFIELDER_TRANSFER_TIME_POOR, INFIELDER_TRANSFER_TIME_MAX,
    OUTFIELDER_TRANSFER_TIME_MIN, OUTFIELDER_TRANSFER_TIME_AVG,
    OUTFIELDER_TRANSFER_TIME_POOR, OUTFIELDER_TRANSFER_TIME_MAX,
    THROWING_ACCURACY_ELITE, THROWING_ACCURACY_AVG,
    THROWING_ACCURACY_POOR, THROWING_ACCURACY_TERRIBLE,
    # Attribute rating scales
    FIELDING_SPEED_RATING_MIN, FIELDING_SPEED_RATING_AVG,
    FIELDING_SPEED_RATING_ELITE, FIELDING_SPEED_RATING_MAX,
    FIELDING_REACTION_RATING_MIN, FIELDING_REACTION_RATING_AVG,
    FIELDING_REACTION_RATING_ELITE, FIELDING_REACTION_RATING_MAX,
    FIELDING_ARM_RATING_MIN, FIELDING_ARM_RATING_AVG,
    FIELDING_ARM_RATING_ELITE, FIELDING_ARM_RATING_MAX,
    FIELDING_ACCURACY_RATING_MIN, FIELDING_ACCURACY_RATING_AVG,
    FIELDING_ACCURACY_RATING_ELITE, FIELDING_ACCURACY_RATING_MAX,
    FIELDING_RANGE_ELITE, FIELDING_RANGE_AVG, FIELDING_RANGE_POOR,
    # Physics constants
    GRAVITY, FEET_TO_METERS, METERS_TO_FEET, MPH_TO_MS, MS_TO_MPH,
    DEG_TO_RAD, RAD_TO_DEG,
    # Play outcome tolerances
    CLOSE_PLAY_TOLERANCE, SAFE_RUNNER_BIAS,
    TAG_APPLICATION_TIME, TAG_AVOIDANCE_SUCCESS_RATE,
)
from .field_layout import FieldPosition, FieldLayout


class FieldingResult:
    """Result of a fielding attempt."""
    
    def __init__(self, 
                 success: bool,
                 fielder_arrival_time: float,
                 ball_arrival_time: float,
                 catch_position: FieldPosition,
                 fielder_name: str):
        """
        Initialize fielding result.
        
        Parameters
        ----------
        success : bool
            Whether the fielding attempt was successful
        fielder_arrival_time : float
            Time when fielder reached the ball (seconds)
        ball_arrival_time : float
            Time when ball reached the position (seconds)
        catch_position : FieldPosition
            Position where ball was fielded
        fielder_name : str
            Name of the fielder
        """
        self.success = success
        self.fielder_arrival_time = fielder_arrival_time
        self.ball_arrival_time = ball_arrival_time
        self.catch_position = catch_position
        self.fielder_name = fielder_name
        self.margin = fielder_arrival_time - ball_arrival_time  # Negative = made it


class ThrowResult:
    """Result of a throwing attempt."""
    
    def __init__(self,
                 throw_velocity: float,
                 flight_time: float,
                 accuracy_error: Tuple[float, float],
                 target_position: FieldPosition,
                 release_time: float):
        """
        Initialize throw result.
        
        Parameters
        ----------
        throw_velocity : float
            Velocity of throw in mph
        flight_time : float
            Time for ball to reach target in seconds
        accuracy_error : tuple
            (horizontal_error, vertical_error) in inches from target
        target_position : FieldPosition
            Intended target position
        release_time : float
            Time when ball was released
        """
        self.throw_velocity = throw_velocity
        self.flight_time = flight_time
        self.accuracy_error = accuracy_error
        self.target_position = target_position
        self.release_time = release_time
        self.arrival_time = release_time + flight_time


class Fielder:
    """
    Represents a defensive player with physical attributes and fielding mechanics.
    
    Core Physical Attributes:
    - sprint_speed: Maximum running speed (0-100 rating)
    - acceleration: Rate of acceleration to top speed (0-100 rating)
    - reaction_time: Delay before movement begins (0-100 rating)
    - arm_strength: Throwing velocity capability (0-100 rating)
    - throwing_accuracy: Precision of throws (0-100 rating)
    - transfer_quickness: Speed of glove-to-hand transition (0-100 rating)
    - fielding_range: Effective area coverage (0-100 rating)
    """
    
    def __init__(self,
                 name: str = "Fielder",
                 position: str = "infield",
                 # Physical attributes (0-100 scale)
                 sprint_speed: int = 50,
                 acceleration: int = 50,
                 reaction_time: int = 50,
                 arm_strength: int = 50,
                 throwing_accuracy: int = 50,
                 transfer_quickness: int = 50,
                 fielding_range: int = 50,
                 # Position and state
                 current_position: Optional[FieldPosition] = None):
        """
        Initialize fielder with attribute ratings.
        
        Parameters
        ----------
        name : str
            Fielder's name/identifier
        position : str
            Position type ('infield', 'outfield', 'catcher')
        sprint_speed : int (0-100)
            Sprint speed rating (50=avg MLB ~27 ft/s, 80=elite ~30 ft/s)
        acceleration : int (0-100)
            Acceleration rating (50=avg ~16 ft/s², 80=elite ~20 ft/s²)
        reaction_time : int (0-100)
            Reaction rating (50=avg ~0.15s, 80=elite ~0.05s, higher=faster)
        arm_strength : int (0-100)
            Throwing velocity rating (position-dependent ranges)
        throwing_accuracy : int (0-100)
            Throwing precision (50=avg ~2° error, 80=elite ~1° error)
        transfer_quickness : int (0-100)
            Glove-to-hand speed (50=avg, position-dependent)
        fielding_range : int (0-100)
            Range factor (50=avg, affects effective coverage area)
        current_position : FieldPosition, optional
            Current field position
        """
        self.name = name
        self.position = position.lower()
        
        # Clip all ratings to 0-100 scale
        self.sprint_speed = np.clip(sprint_speed, 0, 100)
        self.acceleration = np.clip(acceleration, 0, 100)
        self.reaction_time = np.clip(reaction_time, 0, 100)
        self.arm_strength = np.clip(arm_strength, 0, 100)
        self.throwing_accuracy = np.clip(throwing_accuracy, 0, 100)
        self.transfer_quickness = np.clip(transfer_quickness, 0, 100)
        self.fielding_range = np.clip(fielding_range, 0, 100)
        
        # Position and state
        self.current_position = current_position
        self.is_infielder = position.lower() in ['infield', 'catcher']
        
        # Movement state
        self.current_velocity = np.array([0.0, 0.0, 0.0])  # ft/s
        self.is_moving = False
        self.target_position = None
    
    def get_sprint_speed_fps(self) -> float:
        """Convert sprint speed rating to feet per second."""
        # Linear mapping: 20=min, 50=avg, 80=elite, 100=max
        min_speed = FIELDER_SPRINT_SPEED_MIN
        max_speed = FIELDER_SPRINT_SPEED_MAX
        avg_speed = FIELDER_SPRINT_SPEED_AVG
        
        if self.sprint_speed <= 50:
            # 20-50 range: min to avg
            factor = (self.sprint_speed - 20) / 30.0
            speed = min_speed + factor * (avg_speed - min_speed)
        else:
            # 50-100 range: avg to max  
            factor = (self.sprint_speed - 50) / 50.0
            speed = avg_speed + factor * (max_speed - avg_speed)
        
        return speed
    
    def get_acceleration_fps2(self) -> float:
        """Convert acceleration rating to feet per second squared."""
        min_accel = FIELDER_ACCELERATION_MIN
        max_accel = FIELDER_ACCELERATION_MAX
        avg_accel = FIELDER_ACCELERATION_AVG
        
        if self.acceleration <= 50:
            factor = (self.acceleration - 20) / 30.0
            accel = min_accel + factor * (avg_accel - min_accel)
        else:
            factor = (self.acceleration - 50) / 50.0
            accel = avg_accel + factor * (max_accel - avg_accel)
        
        return accel
    
    def get_reaction_time_seconds(self) -> float:
        """Convert reaction time rating to seconds (higher rating = faster reaction)."""
        min_time = FIELDER_REACTION_TIME_MAX  # Worst reaction (highest time)
        max_time = FIELDER_REACTION_TIME_MIN  # Best reaction (lowest time)
        avg_time = FIELDER_REACTION_TIME_AVG
        
        # Higher rating = lower reaction time
        if self.reaction_time <= 50:
            factor = (self.reaction_time - 20) / 30.0
            time = min_time - factor * (min_time - avg_time)
        else:
            factor = (self.reaction_time - 50) / 50.0
            time = avg_time - factor * (avg_time - max_time)
        
        return max(time, 0.0)
    
    def get_throw_velocity_mph(self) -> float:
        """Convert arm strength rating to throwing velocity in mph."""
        if self.is_infielder:
            min_vel = INFIELDER_THROW_VELOCITY_MIN
            max_vel = INFIELDER_THROW_VELOCITY_MAX
            avg_vel = INFIELDER_THROW_VELOCITY_AVG
        else:
            min_vel = OUTFIELDER_THROW_VELOCITY_MIN
            max_vel = OUTFIELDER_THROW_VELOCITY_MAX
            avg_vel = OUTFIELDER_THROW_VELOCITY_AVG
        
        if self.arm_strength <= 50:
            factor = (self.arm_strength - 20) / 30.0
            velocity = min_vel + factor * (avg_vel - min_vel)
        else:
            factor = (self.arm_strength - 50) / 50.0
            velocity = avg_vel + factor * (max_vel - avg_vel)
        
        return velocity
    
    def get_transfer_time_seconds(self) -> float:
        """Convert transfer quickness rating to seconds."""
        if self.is_infielder:
            min_time = INFIELDER_TRANSFER_TIME_MAX   # Slowest (highest time)
            max_time = INFIELDER_TRANSFER_TIME_MIN   # Fastest (lowest time)
            avg_time = INFIELDER_TRANSFER_TIME_AVG
        else:
            min_time = OUTFIELDER_TRANSFER_TIME_MAX
            max_time = OUTFIELDER_TRANSFER_TIME_MIN
            avg_time = OUTFIELDER_TRANSFER_TIME_AVG
        
        # Higher rating = lower transfer time
        if self.transfer_quickness <= 50:
            factor = (self.transfer_quickness - 20) / 30.0
            time = min_time - factor * (min_time - avg_time)
        else:
            factor = (self.transfer_quickness - 50) / 50.0
            time = avg_time - factor * (avg_time - max_time)
        
        return time
    
    def get_throwing_accuracy_std_degrees(self) -> float:
        """Convert throwing accuracy rating to standard deviation in degrees."""
        min_accuracy = THROWING_ACCURACY_TERRIBLE  # Worst accuracy (highest error)
        max_accuracy = THROWING_ACCURACY_ELITE     # Best accuracy (lowest error)
        avg_accuracy = THROWING_ACCURACY_AVG
        
        # Higher rating = lower error
        if self.throwing_accuracy <= 50:
            factor = (self.throwing_accuracy - 20) / 30.0
            std_deg = min_accuracy - factor * (min_accuracy - avg_accuracy)
        else:
            factor = (self.throwing_accuracy - 50) / 50.0
            std_deg = avg_accuracy - factor * (avg_accuracy - max_accuracy)
        
        return std_deg
    
    def get_effective_range_multiplier(self) -> float:
        """Get range multiplier based on fielding range rating."""
        if self.fielding_range <= 50:
            # Below average: 0.8 to 1.0 multiplier
            factor = (self.fielding_range - 20) / 30.0
            multiplier = FIELDING_RANGE_POOR + factor * (FIELDING_RANGE_AVG - FIELDING_RANGE_POOR)
        else:
            # Above average: 1.0 to 1.25 multiplier
            factor = (self.fielding_range - 50) / 50.0
            multiplier = FIELDING_RANGE_AVG + factor * (FIELDING_RANGE_ELITE - FIELDING_RANGE_AVG)
        
        return multiplier
    
    def calculate_time_to_position(self, target: FieldPosition) -> float:
        """
        Calculate time required to reach a target position.
        
        Parameters
        ----------
        target : FieldPosition
            Target position to reach
            
        Returns
        -------
        float
            Time in seconds to reach position
        """
        if self.current_position is None:
            raise ValueError("Current position not set")
        
        # Calculate distance to target
        distance = self.current_position.distance_to(target)
        
        # Get physical attributes
        max_speed = self.get_sprint_speed_fps()
        acceleration = self.get_acceleration_fps2()
        reaction_time = self.get_reaction_time_seconds()
        
        # Time to reach max speed
        time_to_max_speed = max_speed / acceleration
        distance_during_acceleration = 0.5 * acceleration * time_to_max_speed**2
        
        if distance <= distance_during_acceleration:
            # Never reach max speed - solve quadratic equation
            # distance = 0.5 * acceleration * time^2
            time_running = np.sqrt(2 * distance / acceleration)
            total_time = reaction_time + time_running
        else:
            # Reach max speed, then run at constant speed
            remaining_distance = distance - distance_during_acceleration
            time_at_max_speed = remaining_distance / max_speed
            total_time = reaction_time + time_to_max_speed + time_at_max_speed
        
        return total_time
    
    def can_reach_ball(self, ball_position: FieldPosition, ball_arrival_time: float) -> bool:
        """
        Determine if fielder can reach ball before it arrives at position.
        
        Parameters
        ----------
        ball_position : FieldPosition
            Position where ball will arrive
        ball_arrival_time : float
            Time when ball will arrive (seconds from contact)
            
        Returns
        -------
        bool
            True if fielder can reach ball in time
        """
        fielder_time = self.calculate_time_to_position(ball_position)
        
        # Apply range multiplier to effective time
        range_multiplier = self.get_effective_range_multiplier()
        effective_time = fielder_time / range_multiplier
        
        return effective_time <= ball_arrival_time
    
    def attempt_fielding(self, ball_position: FieldPosition, 
                        ball_arrival_time: float) -> FieldingResult:
        """
        Attempt to field a ball at given position and time.
        
        Parameters
        ----------
        ball_position : FieldPosition
            Position where ball arrives
        ball_arrival_time : float
            Time when ball arrives
            
        Returns
        -------
        FieldingResult
            Result of fielding attempt
        """
        fielder_time = self.calculate_time_to_position(ball_position)
        range_multiplier = self.get_effective_range_multiplier()
        effective_fielder_time = fielder_time / range_multiplier
        
        # Determine success
        success = effective_fielder_time <= ball_arrival_time
        
        # If close, there's a small chance for a diving catch
        if not success and (effective_fielder_time - ball_arrival_time) <= 0.3:
            # 20% chance for diving play if within 0.3 seconds
            dive_success_rate = 0.20 * (self.fielding_range / 100.0)  # Better fielders more likely
            if np.random.random() < dive_success_rate:
                success = True
                effective_fielder_time = ball_arrival_time - 0.05  # Just barely made it
        
        return FieldingResult(
            success=success,
            fielder_arrival_time=effective_fielder_time,
            ball_arrival_time=ball_arrival_time,
            catch_position=ball_position,
            fielder_name=self.name
        )
    
    def throw_ball(self, target_position: FieldPosition, 
                   from_position: Optional[FieldPosition] = None) -> ThrowResult:
        """
        Simulate throwing the ball to a target position.
        
        Parameters
        ----------
        target_position : FieldPosition
            Target to throw to
        from_position : FieldPosition, optional
            Position throwing from (defaults to current position)
            
        Returns
        -------
        ThrowResult
            Result of throw simulation
        """
        if from_position is None:
            from_position = self.current_position
        if from_position is None:
            raise ValueError("Throwing position not specified")
        
        # Calculate throw distance
        throw_distance = from_position.distance_to(target_position)
        
        # Get throwing attributes
        throw_velocity_mph = self.get_throw_velocity_mph()
        throw_velocity_fps = throw_velocity_mph * MPH_TO_MS / FEET_TO_METERS  # Convert to ft/s
        accuracy_std_deg = self.get_throwing_accuracy_std_degrees()
        transfer_time = self.get_transfer_time_seconds()
        
        # Calculate flight time using ballistic trajectory
        # Simplified: assume optimal angle for distance and calculate time
        # For a line drive throw, approximate time as distance/velocity
        # More sophisticated: solve ballistic equation
        
        # Simple approximation for now (can be enhanced with full trajectory)
        flight_time = throw_distance / throw_velocity_fps
        
        # Add slight adjustment for arc (throws aren't perfectly horizontal)
        # Rule of thumb: add ~5% to flight time for typical throw arc
        flight_time *= 1.05
        
        # Calculate accuracy error
        horizontal_error_deg = np.random.normal(0, accuracy_std_deg)
        vertical_error_deg = np.random.normal(0, accuracy_std_deg)
        
        # Convert angular error to linear error at target distance
        # For small angles, tan(θ) ≈ θ (in radians), so use sin for better numerical stability
        horizontal_error_inches = throw_distance * 12 * np.sin(horizontal_error_deg * DEG_TO_RAD)
        vertical_error_inches = throw_distance * 12 * np.sin(vertical_error_deg * DEG_TO_RAD)
        
        return ThrowResult(
            throw_velocity=throw_velocity_mph,
            flight_time=flight_time,
            accuracy_error=(horizontal_error_inches, vertical_error_inches),
            target_position=target_position,
            release_time=transfer_time  # Time from catch to release
        )
    
    def update_position(self, new_position: FieldPosition):
        """Update fielder's current position."""
        self.current_position = new_position
        self.current_velocity = np.array([0.0, 0.0, 0.0])
        self.is_moving = False
    
    def start_movement_to(self, target: FieldPosition):
        """Start movement toward a target position."""
        self.target_position = target
        self.is_moving = True
    
    def __repr__(self):
        return (f"Fielder(name='{self.name}', position='{self.position}', "
                f"speed={self.sprint_speed}, arm={self.arm_strength}, "
                f"range={self.fielding_range})")


class FieldingSimulator:
    """
    Manages fielding simulation for multiple fielders and ball in play.
    """
    
    def __init__(self, field_layout: FieldLayout):
        """
        Initialize fielding simulator.
        
        Parameters
        ----------
        field_layout : FieldLayout
            Field layout and positioning
        """
        self.field_layout = field_layout
        self.fielders = {}
        self.current_time = 0.0
    
    def add_fielder(self, position_name: str, fielder: Fielder):
        """Add a fielder at a specific position."""
        # Set fielder to standard position if not already positioned
        if fielder.current_position is None:
            standard_pos = self.field_layout.get_defensive_position(position_name)
            fielder.update_position(standard_pos)
        
        self.fielders[position_name] = fielder
    
    def determine_responsible_fielder(self, ball_position: FieldPosition) -> str:
        """Determine which fielder should attempt to field the ball."""
        return self.field_layout.get_nearest_fielder_position(ball_position)
    
    def simulate_fielding_attempt(self, ball_position: FieldPosition, 
                                 ball_arrival_time: float) -> FieldingResult:
        """
        Simulate fielding attempt by the responsible fielder.
        
        Parameters
        ----------
        ball_position : FieldPosition
            Where the ball will arrive
        ball_arrival_time : float
            When the ball will arrive
            
        Returns
        -------
        FieldingResult
            Result of the fielding attempt
        """
        responsible_position = self.determine_responsible_fielder(ball_position)
        
        if responsible_position not in self.fielders:
            raise ValueError(f"No fielder assigned to position {responsible_position}")
        
        fielder = self.fielders[responsible_position]
        return fielder.attempt_fielding(ball_position, ball_arrival_time)
    
    def get_all_fielding_probabilities(self, ball_position: FieldPosition,
                                     ball_arrival_time: float) -> Dict[str, float]:
        """
        Calculate fielding probability for all fielders.
        
        Parameters
        ----------
        ball_position : FieldPosition
            Ball position
        ball_arrival_time : float
            Ball arrival time
            
        Returns
        -------
        dict
            Mapping of fielder position to probability of successful fielding
        """
        probabilities = {}
        
        for pos_name, fielder in self.fielders.items():
            try:
                time_needed = fielder.calculate_time_to_position(ball_position)
                range_multiplier = fielder.get_effective_range_multiplier()
                effective_time = time_needed / range_multiplier
                
                if effective_time <= ball_arrival_time:
                    # Base probability if they can get there
                    prob = 0.95  # 95% chance if they reach it
                    
                    # Reduce if it's very close
                    margin = ball_arrival_time - effective_time
                    if margin < 0.1:  # Very close play
                        prob *= 0.8
                else:
                    # Small chance for diving play
                    time_deficit = effective_time - ball_arrival_time
                    if time_deficit <= 0.3:
                        prob = 0.20 * (fielder.fielding_range / 100.0)
                    else:
                        prob = 0.0
                
                probabilities[pos_name] = prob
                
            except ValueError:
                probabilities[pos_name] = 0.0
        
        return probabilities


# Convenience functions for creating fielders
def create_elite_fielder(name: str, position: str) -> Fielder:
    """Create an elite fielder with high ratings."""
    return Fielder(
        name=name,
        position=position,
        sprint_speed=85,
        acceleration=85,
        reaction_time=85,
        arm_strength=85,
        throwing_accuracy=85,
        transfer_quickness=85,
        fielding_range=85
    )


def create_average_fielder(name: str, position: str) -> Fielder:
    """Create an average fielder with typical ratings."""
    return Fielder(
        name=name,
        position=position,
        sprint_speed=50,
        acceleration=50,
        reaction_time=50,
        arm_strength=50,
        throwing_accuracy=50,
        transfer_quickness=50,
        fielding_range=50
    )


def create_poor_fielder(name: str, position: str) -> Fielder:
    """Create a below-average fielder."""
    return Fielder(
        name=name,
        position=position,
        sprint_speed=30,
        acceleration=30,
        reaction_time=30,
        arm_strength=30,
        throwing_accuracy=30,
        transfer_quickness=30,
        fielding_range=30
    )