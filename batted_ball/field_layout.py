"""
Baseball field layout and coordinate system definitions.

Defines the standard MLB field dimensions, base locations, defensive positions,
and coordinate system for integration with trajectory physics and fielding mechanics.

Coordinate System:
- Origin: Home plate center
- X-axis: Positive toward right field, negative toward left field
- Y-axis: Positive toward center field, negative toward home plate
- Z-axis: Positive upward, negative downward
- Units: Feet (converted to meters internally for physics calculations)
"""

import numpy as np
from typing import Dict, List, Tuple, Optional
from .constants import (
    # Field dimensions
    BASE_PATH_LENGTH,
    HOME_TO_FIRST_DISTANCE,
    PITCHERS_MOUND_DISTANCE,
    # Base coordinates
    HOME_PLATE_X, HOME_PLATE_Y,
    FIRST_BASE_X, FIRST_BASE_Y,
    SECOND_BASE_X, SECOND_BASE_Y,
    THIRD_BASE_X, THIRD_BASE_Y,
    # Defensive positions
    PITCHER_X, PITCHER_Y,
    CATCHER_X, CATCHER_Y,
    FIRST_BASEMAN_X, FIRST_BASEMAN_Y,
    SECOND_BASEMAN_X, SECOND_BASEMAN_Y,
    SHORTSTOP_X, SHORTSTOP_Y,
    THIRD_BASEMAN_X, THIRD_BASEMAN_Y,
    LEFT_FIELDER_X, LEFT_FIELDER_Y,
    CENTER_FIELDER_X, CENTER_FIELDER_Y,
    RIGHT_FIELDER_X, RIGHT_FIELDER_Y,
    # Outfield dimensions
    LEFT_FIELD_WALL_DISTANCE,
    CENTER_FIELD_WALL_DISTANCE,
    RIGHT_FIELD_WALL_DISTANCE,
    OUTFIELD_WALL_HEIGHT,
    # Unit conversions
    FEET_TO_METERS,
    METERS_TO_FEET,
)


class FieldPosition:
    """Represents a position on the baseball field."""
    
    def __init__(self, x: float, y: float, z: float = 0.0):
        """
        Initialize field position.
        
        Parameters
        ----------
        x : float
            X coordinate in feet (+ toward right field)
        y : float
            Y coordinate in feet (+ toward center field)
        z : float
            Z coordinate in feet (+ upward)
        """
        self.x = x
        self.y = y
        self.z = z
    
    def distance_to(self, other: 'FieldPosition') -> float:
        """Calculate distance to another position in feet."""
        dx = self.x - other.x
        dy = self.y - other.y
        dz = self.z - other.z
        return np.sqrt(dx**2 + dy**2 + dz**2)

    def horizontal_distance_to(self, other: 'FieldPosition') -> float:
        """Calculate horizontal (x,y) distance to another position, ignoring height."""
        dx = self.x - other.x
        dy = self.y - other.y
        return np.sqrt(dx**2 + dy**2)
    
    def to_meters(self) -> Tuple[float, float, float]:
        """Convert position to meters for physics calculations."""
        return (self.x * FEET_TO_METERS, 
                self.y * FEET_TO_METERS, 
                self.z * FEET_TO_METERS)
    
    def to_array(self) -> np.ndarray:
        """Return position as numpy array in feet."""
        return np.array([self.x, self.y, self.z])
    
    def __repr__(self):
        return f"FieldPosition(x={self.x:.1f}, y={self.y:.1f}, z={self.z:.1f})"


class BaseLocation:
    """Represents a base with its position and properties."""
    
    def __init__(self, name: str, position: FieldPosition, is_force_base: bool = True):
        """
        Initialize base.
        
        Parameters
        ----------
        name : str
            Base name ('home', 'first', 'second', 'third')
        position : FieldPosition
            Position of the base
        is_force_base : bool
            Whether this is a force play base
        """
        self.name = name
        self.position = position
        self.is_force_base = is_force_base
    
    def __repr__(self):
        return f"BaseLocation(name='{self.name}', position={self.position})"


class DefensivePosition:
    """Represents a defensive position with standard location."""
    
    def __init__(self, name: str, number: int, standard_position: FieldPosition, 
                 is_infielder: bool = True):
        """
        Initialize defensive position.
        
        Parameters
        ----------
        name : str
            Position name (e.g., 'shortstop', 'center_field')
        number : int
            Defensive position number (1-9)
        standard_position : FieldPosition
            Standard/default position
        is_infielder : bool
            Whether this is an infield position
        """
        self.name = name
        self.number = number
        self.standard_position = standard_position
        self.is_infielder = is_infielder
    
    def __repr__(self):
        return f"DefensivePosition(name='{self.name}', number={self.number})"


class FieldLayout:
    """
    Complete baseball field layout with bases, positions, and boundaries.
    
    Provides methods for field geometry calculations, position assignments,
    and integration with trajectory physics.
    """
    
    def __init__(self):
        """Initialize standard MLB field layout."""
        self._setup_bases()
        self._setup_defensive_positions()
        self._setup_field_boundaries()
    
    def _setup_bases(self):
        """Initialize base locations."""
        self.bases = {
            'home': BaseLocation(
                'home',
                FieldPosition(HOME_PLATE_X, HOME_PLATE_Y, 0.0),
                is_force_base=True
            ),
            'first': BaseLocation(
                'first',
                FieldPosition(FIRST_BASE_X, FIRST_BASE_Y, 0.0),
                is_force_base=True
            ),
            'second': BaseLocation(
                'second',
                FieldPosition(SECOND_BASE_X, SECOND_BASE_Y, 0.0),
                is_force_base=True
            ),
            'third': BaseLocation(
                'third',
                FieldPosition(THIRD_BASE_X, THIRD_BASE_Y, 0.0),
                is_force_base=True
            )
        }
    
    def _setup_defensive_positions(self):
        """Initialize standard defensive positions."""
        self.defensive_positions = {
            'pitcher': DefensivePosition(
                'pitcher', 1,
                FieldPosition(0.0, PITCHERS_MOUND_DISTANCE, 0.0),
                is_infielder=True
            ),
            'catcher': DefensivePosition(
                'catcher', 2,
                FieldPosition(CATCHER_X, CATCHER_Y, 0.0),
                is_infielder=True
            ),
            'first_base': DefensivePosition(
                'first_base', 3,
                FieldPosition(FIRST_BASEMAN_X, FIRST_BASEMAN_Y, 0.0),
                is_infielder=True
            ),
            'second_base': DefensivePosition(
                'second_base', 4,
                FieldPosition(SECOND_BASEMAN_X, SECOND_BASEMAN_Y, 0.0),
                is_infielder=True
            ),
            'third_base': DefensivePosition(
                'third_base', 5,
                FieldPosition(THIRD_BASEMAN_X, THIRD_BASEMAN_Y, 0.0),
                is_infielder=True
            ),
            'shortstop': DefensivePosition(
                'shortstop', 6,
                FieldPosition(SHORTSTOP_X, SHORTSTOP_Y, 0.0),
                is_infielder=True
            ),
            'left_field': DefensivePosition(
                'left_field', 7,
                FieldPosition(LEFT_FIELDER_X, LEFT_FIELDER_Y, 0.0),
                is_infielder=False
            ),
            'center_field': DefensivePosition(
                'center_field', 8,
                FieldPosition(CENTER_FIELDER_X, CENTER_FIELDER_Y, 0.0),
                is_infielder=False
            ),
            'right_field': DefensivePosition(
                'right_field', 9,
                FieldPosition(RIGHT_FIELDER_X, RIGHT_FIELDER_Y, 0.0),
                is_infielder=False
            )
        }
    
    def _setup_field_boundaries(self):
        """Initialize field boundaries and foul territory."""
        # Foul lines (infinite lines from home plate)
        self.first_base_line_angle = 0.0  # degrees (toward first base)
        self.third_base_line_angle = 90.0  # degrees (toward third base)
        
        # Outfield wall (simplified as arc)
        self.outfield_wall = {
            'left_field_distance': LEFT_FIELD_WALL_DISTANCE,
            'center_field_distance': CENTER_FIELD_WALL_DISTANCE,
            'right_field_distance': RIGHT_FIELD_WALL_DISTANCE,
            'height': OUTFIELD_WALL_HEIGHT
        }
    
    def get_base_position(self, base_name: str) -> FieldPosition:
        """Get position of a base."""
        if base_name not in self.bases:
            raise ValueError(f"Unknown base: {base_name}")
        return self.bases[base_name].position
    
    def get_defensive_position(self, position_name: str) -> FieldPosition:
        """Get standard position of a defensive player."""
        if position_name not in self.defensive_positions:
            raise ValueError(f"Unknown defensive position: {position_name}")
        return self.defensive_positions[position_name].standard_position
    
    def is_fair_territory(self, position: FieldPosition) -> bool:
        """
        Determine if a position is in fair territory.
        
        Parameters
        ----------
        position : FieldPosition
            Position to check
            
        Returns
        -------
        bool
            True if in fair territory
        """
        # Check if in the 90-degree fair territory sector
        # Fair territory is between first base line (x >= 0, y >= 0) 
        # and third base line (x <= 0, y >= 0) for y > 0
        if position.y < 0:  # Behind home plate
            return False
        
        if position.y == 0:  # On home plate line
            return position.x == 0  # Only home plate itself
        
        # In front of home plate: check foul lines
        # First base line: x/y ratio should be reasonable for fair territory
        # Third base line: similar check
        
        # For simplicity, use 45-degree lines (can be refined)
        # Fair if -position.y <= position.x <= position.y
        return -position.y <= position.x <= position.y
    
    def get_nearest_fielder_position(self, ball_position: FieldPosition) -> str:
        """
        Determine which fielder should handle a ball at given position.
        Uses realistic fielding zones instead of just distance.
        
        Parameters
        ----------
        ball_position : FieldPosition
            Position of the ball
            
        Returns
        -------
        str
            Name of the responsible fielder position
        """
        ball_x = ball_position.x
        ball_y = ball_position.y
        
        # Calculate distance from home plate
        distance_from_home = (ball_x**2 + ball_y**2)**0.5
        
        # Very close to home plate - catcher territory
        if distance_from_home < 30.0:
            return 'catcher'
        
        # Close to pitcher's mound
        pitcher_distance = ((ball_x - 0)**2 + (ball_y - 60.5)**2)**0.5
        if pitcher_distance < 25.0:
            return 'pitcher'
        
        # Determine infield vs outfield based on distance
        # Balls beyond 180 feet go to outfielders
        if distance_from_home > 180.0:
            # Outfield responsibility based on spray angle from center field
            # Calculate angle: 0° = straight center, +angle = right, -angle = left
            import numpy as np
            spray_angle = np.arctan2(ball_x, ball_y) * 180.0 / np.pi

            # Divide outfield into zones:
            # Left field: -90° to -30°
            # Center field: -30° to +30°
            # Right field: +30° to +90°
            if spray_angle < -30:  # Left field zone
                return 'left_field'
            elif spray_angle > 30:  # Right field zone
                return 'right_field'
            else:  # Center field zone (-30° to +30°)
                return 'center_field'
        else:
            # Infield responsibility
            if ball_x > 45:  # Right side of infield
                return 'first_base'
            elif ball_x < -45:  # Left side of infield
                return 'third_base'
            elif ball_x > 0:  # Right of center
                return 'second_base'
            else:  # Left of center
                return 'shortstop'
    
    def calculate_base_path_distance(self, from_base: str, to_base: str) -> float:
        """
        Calculate distance along base paths between bases.
        
        Parameters
        ----------
        from_base : str
            Starting base name
        to_base : str
            Ending base name
            
        Returns
        -------
        float
            Distance along base paths in feet
        """
        # Define base order for path calculations
        base_order = ['home', 'first', 'second', 'third', 'home']
        
        if from_base not in base_order[:4] or to_base not in base_order[:4]:
            raise ValueError("Invalid base name")
        
        from_idx = base_order.index(from_base)
        to_idx = base_order.index(to_base) if to_base != 'home' else 4
        
        if to_idx <= from_idx:
            # Going around the horn
            distance = 0.0
            for i in range(from_idx, 4):
                distance += BASE_PATH_LENGTH
            if to_base != 'home':
                for i in range(0, base_order.index(to_base)):
                    distance += BASE_PATH_LENGTH
        else:
            # Direct path
            distance = (to_idx - from_idx) * BASE_PATH_LENGTH
        
        return distance
    
    def get_base_path_positions(self, from_base: str, to_base: str, 
                               num_points: int = 100) -> List[FieldPosition]:
        """
        Get positions along the base path between two bases.
        
        Parameters
        ----------
        from_base : str
            Starting base
        to_base : str
            Ending base
        num_points : int
            Number of intermediate positions
            
        Returns
        -------
        List[FieldPosition]
            Positions along the path
        """
        from_pos = self.get_base_position(from_base)
        to_pos = self.get_base_position(to_base)
        
        positions = []
        for i in range(num_points + 1):
            t = i / num_points
            x = from_pos.x + t * (to_pos.x - from_pos.x)
            y = from_pos.y + t * (to_pos.y - from_pos.y)
            z = from_pos.z + t * (to_pos.z - from_pos.z)
            positions.append(FieldPosition(x, y, z))
        
        return positions
    
    def is_home_run(self, ball_position: FieldPosition) -> bool:
        """
        Determine if a ball position represents a home run.
        
        Parameters
        ----------
        ball_position : FieldPosition
            Ball position to check
            
        Returns
        -------
        bool
            True if home run
        """
        if not self.is_fair_territory(ball_position):
            return False
        
        # Calculate distance from home plate
        distance = ball_position.distance_to(self.get_base_position('home'))
        
        # Simplified: check if beyond outfield wall distance
        # In reality, this would depend on the angle and specific ballpark
        if distance >= CENTER_FIELD_WALL_DISTANCE and ball_position.z >= OUTFIELD_WALL_HEIGHT:
            return True
        
        return False
    
    def create_custom_positioning(self, position_adjustments: Dict[str, Tuple[float, float]]) -> Dict[str, FieldPosition]:
        """
        Create custom defensive positioning.
        
        Parameters
        ----------
        position_adjustments : dict
            Dictionary mapping position names to (x_offset, y_offset) adjustments
            
        Returns
        -------
        dict
            Custom positioning dictionary
        """
        custom_positions = {}
        
        for pos_name, def_pos in self.defensive_positions.items():
            if pos_name in position_adjustments:
                x_offset, y_offset = position_adjustments[pos_name]
                custom_x = def_pos.standard_position.x + x_offset
                custom_y = def_pos.standard_position.y + y_offset
                custom_positions[pos_name] = FieldPosition(custom_x, custom_y, 0.0)
            else:
                custom_positions[pos_name] = def_pos.standard_position
        
        return custom_positions
    
    def position_from_coordinates(self, x: float, y: float, z: float = 0.0) -> FieldPosition:
        """Create a FieldPosition from coordinates."""
        return FieldPosition(x, y, z)

    def apply_defensive_shift(self, spray_tendency: float, shift_type: str = 'standard') -> Dict[str, FieldPosition]:
        """
        Apply defensive positioning strategy based on batter spray tendency.

        Implements realistic defensive shifts similar to modern MLB analytics:
        - Pull shift: Move infielders toward pull side for pull-heavy hitters
        - No doubles defense: Outfielders deeper, no gaps
        - Standard positioning: No special positioning

        Parameters
        ----------
        spray_tendency : float
            Batter's spray tendency in degrees from HitterAttributes.get_spray_tendency_deg()
            Negative = opposite field tendency
            0 = balanced (all fields)
            Positive = pull tendency
        shift_type : str
            Type of defensive strategy:
            - 'standard': Normal positioning (no shift)
            - 'pull_shift': Shift infielders toward pull side
            - 'no_doubles': Deep outfield positioning
            - 'infield_in': Shallow infield for preventing runs
            - 'outfield_shallow': Shallow outfield for preventing base hits

        Returns
        -------
        dict
            Custom positioning dictionary with adjusted fielder positions
        """
        adjustments = {}

        # Determine if batter is pull-heavy (threshold: +10° = moderate pull tendency)
        is_pull_hitter = spray_tendency >= 10.0
        is_extreme_pull = spray_tendency >= 18.0
        is_opposite_field = spray_tendency <= -10.0

        if shift_type == 'pull_shift' and is_pull_hitter:
            # Shift infield toward pull side (assume right-handed batter convention)
            # Pull side is positive X (right field) for RHH
            shift_magnitude = min(abs(spray_tendency) / 15.0, 1.5)  # Scale shift with tendency

            # Second baseman moves toward first base line
            adjustments['second_base'] = (15.0 * shift_magnitude, -5.0)

            # Shortstop moves toward second base (or even to right side in extreme shifts)
            if is_extreme_pull:
                adjustments['shortstop'] = (25.0 * shift_magnitude, 0.0)
            else:
                adjustments['shortstop'] = (15.0 * shift_magnitude, 5.0)

            # Third baseman moves toward shortstop position
            adjustments['third_base'] = (10.0 * shift_magnitude, 10.0)

            # First baseman holds position (or slightly back)
            adjustments['first_base'] = (0.0, 5.0)

            # Outfield shift: right fielder in, center fielder toward right-center gap
            adjustments['right_field'] = (-10.0 * shift_magnitude, -10.0)
            adjustments['center_field'] = (15.0 * shift_magnitude, 0.0)

        elif shift_type == 'pull_shift' and is_opposite_field:
            # Shift toward opposite field (negative X for LHH pulling to left)
            shift_magnitude = min(abs(spray_tendency) / 15.0, 1.5)

            # Mirror of pull shift adjustments
            adjustments['shortstop'] = (-15.0 * shift_magnitude, -5.0)
            adjustments['second_base'] = (-15.0 * shift_magnitude, 5.0)
            if is_extreme_pull:
                adjustments['second_base'] = (-25.0 * shift_magnitude, 0.0)

            adjustments['first_base'] = (-10.0 * shift_magnitude, 10.0)
            adjustments['left_field'] = (10.0 * shift_magnitude, -10.0)
            adjustments['center_field'] = (-15.0 * shift_magnitude, 0.0)

        elif shift_type == 'no_doubles':
            # Deep outfield positioning - prevent extra base hits
            # Move all outfielders back 20-30 feet
            adjustments['left_field'] = (0.0, 25.0)
            adjustments['center_field'] = (0.0, 30.0)
            adjustments['right_field'] = (0.0, 25.0)

            # Infield plays at double play depth (slightly back)
            adjustments['second_base'] = (0.0, 5.0)
            adjustments['shortstop'] = (0.0, 5.0)

        elif shift_type == 'infield_in':
            # Shallow infield positioning - prevent runs from scoring
            # Move infielders toward home plate
            adjustments['first_base'] = (0.0, -15.0)
            adjustments['second_base'] = (0.0, -15.0)
            adjustments['third_base'] = (0.0, -15.0)
            adjustments['shortstop'] = (0.0, -15.0)

        elif shift_type == 'outfield_shallow':
            # Shallow outfield - prevent base hits
            # Move outfielders in 30-40 feet
            adjustments['left_field'] = (0.0, -35.0)
            adjustments['center_field'] = (0.0, -40.0)
            adjustments['right_field'] = (0.0, -35.0)

        # Apply adjustments using existing method
        return self.create_custom_positioning(adjustments)

    def __repr__(self):
        return "FieldLayout(MLB standard dimensions)"


# Module-level convenience functions
def create_standard_field() -> FieldLayout:
    """Create a standard MLB field layout."""
    return FieldLayout()


def distance_between_positions(pos1: FieldPosition, pos2: FieldPosition) -> float:
    """Calculate distance between two field positions."""
    return pos1.distance_to(pos2)


def position_from_coordinates(x: float, y: float, z: float = 0.0) -> FieldPosition:
    """Create a FieldPosition from coordinates."""
    return FieldPosition(x, y, z)


def get_standard_defensive_alignment() -> Dict[str, FieldPosition]:
    """Get standard defensive positioning."""
    field = create_standard_field()
    return {name: pos.standard_position 
            for name, pos in field.defensive_positions.items()}