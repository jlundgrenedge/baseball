"""
Ballpark dimensions and characteristics for MLB stadiums.

Provides detailed ballpark data including fence distances, heights, and other
park-specific factors that affect batted ball outcomes.

Data sourced from official MLB stadium specifications and Statcast data.
"""

import numpy as np
from typing import Dict, Tuple, Optional


class BallparkDimensions:
    """
    Detailed ballpark dimensions including fence distances and heights at various angles.

    All distances in feet, heights in feet, angles in degrees from center field.
    Spray angle convention: 0° = center field, negative = left field, positive = right field.
    """

    def __init__(self, name: str, fence_profile: Dict[float, Tuple[float, float]]):
        """
        Initialize ballpark dimensions.

        Parameters
        ----------
        name : str
            Stadium name
        fence_profile : Dict[float, Tuple[float, float]]
            Mapping of spray angle (degrees) to (distance_ft, height_ft).
            Angles: 0° = center, -45° = left field line, +45° = right field line

        Example
        -------
        fence_profile = {
            -45.0: (310, 37),  # Green Monster at Fenway
            -22.5: (370, 17),  # Left-center
            0.0: (390, 10),    # Dead center
            22.5: (370, 10),   # Right-center
            45.0: (302, 5)     # Right field pole
        }
        """
        self.name = name
        self.fence_profile = fence_profile

        # Sort angles for interpolation
        self.angles = sorted(fence_profile.keys())

    def get_fence_at_angle(self, spray_angle: float) -> Tuple[float, float]:
        """
        Get fence distance and height at a specific spray angle via interpolation.

        Parameters
        ----------
        spray_angle : float
            Spray angle in degrees (0 = center, negative = left, positive = right)

        Returns
        -------
        distance_ft : float
            Fence distance at this angle
        height_ft : float
            Fence height at this angle
        """
        # Clamp angle to field range (-45 to +45 degrees)
        angle = np.clip(spray_angle, -45, 45)

        # Find bracketing angles
        if angle <= self.angles[0]:
            return self.fence_profile[self.angles[0]]
        if angle >= self.angles[-1]:
            return self.fence_profile[self.angles[-1]]

        # Find the two angles that bracket our target
        for i in range(len(self.angles) - 1):
            if self.angles[i] <= angle <= self.angles[i + 1]:
                angle_low = self.angles[i]
                angle_high = self.angles[i + 1]

                dist_low, height_low = self.fence_profile[angle_low]
                dist_high, height_high = self.fence_profile[angle_high]

                # Linear interpolation
                t = (angle - angle_low) / (angle_high - angle_low)
                distance = dist_low + t * (dist_high - dist_low)
                height = height_low + t * (height_high - height_low)

                return distance, height

        # Fallback (shouldn't happen)
        return 400.0, 10.0

    def is_home_run(self, spray_angle: float, distance_ft: float, height_at_fence_ft: float) -> bool:
        """
        Determine if a ball clears the fence for a home run.

        Parameters
        ----------
        spray_angle : float
            Spray angle in degrees
        distance_ft : float
            Horizontal distance ball traveled
        height_at_fence_ft : float
            Ball's height when it reaches the fence distance

        Returns
        -------
        bool
            True if home run (clears fence), False otherwise
        """
        fence_dist, fence_height = self.get_fence_at_angle(spray_angle)

        # Ball must reach fence distance
        if distance_ft < fence_dist - 2:  # 2 ft cushion for measurement error
            return False

        # Ball must be above fence height
        # If height_at_fence is None, estimate based on distance ratio
        if height_at_fence_ft is None:
            # Conservative estimate: ball probably landed before fence
            return distance_ft >= fence_dist + 5  # Needs to go well past fence

        return height_at_fence_ft >= fence_height

    def get_park_factor_description(self) -> str:
        """Get human-readable description of park characteristics."""
        center_dist, center_height = self.fence_profile.get(0.0, (400, 10))
        left_dist, left_height = self.fence_profile.get(-45.0, (330, 10))
        right_dist, right_height = self.fence_profile.get(45.0, (330, 10))

        desc = f"{self.name}:\n"
        desc += f"  Left field: {left_dist:.0f} ft, {left_height:.0f} ft high\n"
        desc += f"  Center field: {center_dist:.0f} ft, {center_height:.0f} ft high\n"
        desc += f"  Right field: {right_dist:.0f} ft, {right_height:.0f} ft high"

        return desc


# ============================================================================
# MLB BALLPARK DATABASE
# ============================================================================
# Data sourced from official MLB specifications and ballparkpal.com
# Updated for 2024 season

MLB_BALLPARKS = {
    "generic": BallparkDimensions(
        "Generic MLB Park",
        {
            -45.0: (330, 10),   # Left field line
            -33.75: (360, 10),  # Left-center alley
            -22.5: (380, 10),   # Left-center gap
            -11.25: (390, 10),  # Left-center
            0.0: (400, 10),     # Dead center
            11.25: (390, 10),   # Right-center
            22.5: (380, 10),    # Right-center gap
            33.75: (360, 10),   # Right-center alley
            45.0: (330, 10),    # Right field line
        }
    ),

    "fenway": BallparkDimensions(
        "Fenway Park (Boston)",
        {
            -45.0: (310, 37),   # Left field line (Green Monster!)
            -33.75: (370, 17),  # Left-center (Monster decreases)
            -22.5: (379, 10),   # Deep left-center
            -11.25: (390, 10),  # Left-center
            0.0: (390, 10),     # Center (short!)
            11.25: (380, 5),    # Right-center
            22.5: (373, 5),     # Right-center
            33.75: (380, 5),    # Deep right (Pesky's Pole area)
            45.0: (302, 5),     # Right field line (Pesky's Pole)
        }
    ),

    "yankee": BallparkDimensions(
        "Yankee Stadium (New York)",
        {
            -45.0: (318, 8),    # Left field line (short porch)
            -33.75: (365, 10),  # Left-center
            -22.5: (385, 10),   # Deep left-center
            -11.25: (399, 10),  # Left-center
            0.0: (408, 10),     # Dead center
            11.25: (385, 10),   # Right-center
            22.5: (370, 10),    # Right-center
            33.75: (353, 8),    # Right field (famous short porch)
            45.0: (314, 8),     # Right field line
        }
    ),

    "coors": BallparkDimensions(
        "Coors Field (Denver)",
        {
            -45.0: (347, 8),    # Left field line
            -33.75: (370, 8),   # Left-center
            -22.5: (390, 8),    # Left-center gap
            -11.25: (405, 8),   # Deep left-center
            0.0: (415, 8),      # Dead center (deep!)
            11.25: (405, 8),    # Deep right-center
            22.5: (390, 8),     # Right-center gap
            33.75: (370, 8),    # Right-center
            45.0: (350, 8),     # Right field line
        }
    ),

    "oracle": BallparkDimensions(
        "Oracle Park (San Francisco)",
        {
            -45.0: (339, 8),    # Left field line
            -33.75: (364, 8),   # Left-center
            -22.5: (382, 8),    # Left-center gap
            -11.25: (399, 8),   # Deep left-center
            0.0: (399, 8),      # Center
            11.25: (421, 8),    # Deep right-center (Triples Alley!)
            22.5: (421, 25),    # Right-center (high wall)
            33.75: (382, 25),   # Right field (brick wall)
            45.0: (309, 25),    # Right field line (McCovey Cove side)
        }
    ),

    "dodger": BallparkDimensions(
        "Dodger Stadium (Los Angeles)",
        {
            -45.0: (330, 8),    # Left field line
            -33.75: (360, 8),   # Left-center
            -22.5: (375, 8),    # Left-center gap
            -11.25: (385, 8),   # Left-center
            0.0: (395, 8),      # Center
            11.25: (385, 8),    # Right-center
            22.5: (375, 8),     # Right-center gap
            33.75: (360, 8),    # Right-center
            45.0: (330, 8),     # Right field line
        }
    ),

    "wrigley": BallparkDimensions(
        "Wrigley Field (Chicago)",
        {
            -45.0: (355, 11),   # Left field line (ivy wall)
            -33.75: (368, 11),  # Left-center
            -22.5: (388, 11),   # Left-center gap
            -11.25: (390, 11),  # Left-center
            0.0: (400, 11),     # Center
            11.25: (390, 11),   # Right-center
            22.5: (368, 11),    # Right-center gap
            33.75: (360, 11),   # Right-center
            45.0: (353, 11),    # Right field line
        }
    ),

    "petco": BallparkDimensions(
        "Petco Park (San Diego)",
        {
            -45.0: (336, 8),    # Left field line
            -33.75: (367, 8),   # Left-center
            -22.5: (382, 8),    # Left-center gap
            -11.25: (396, 8),   # Left-center
            0.0: (396, 8),      # Center (pitcher's park)
            11.25: (391, 8),    # Right-center
            22.5: (382, 8),     # Right-center gap
            33.75: (367, 8),    # Right-center
            45.0: (322, 8),     # Right field line
        }
    ),

    "great_american": BallparkDimensions(
        "Great American Ball Park (Cincinnati)",
        {
            -45.0: (328, 12),   # Left field line (hitter-friendly!)
            -33.75: (358, 12),  # Left-center
            -22.5: (379, 12),   # Left-center gap
            -11.25: (390, 12),  # Left-center
            0.0: (404, 12),     # Center
            11.25: (390, 8),    # Right-center
            22.5: (370, 8),     # Right-center gap
            33.75: (358, 8),    # Right-center
            45.0: (325, 8),     # Right field line
        }
    ),

    "minute_maid": BallparkDimensions(
        "Minute Maid Park (Houston)",
        {
            -45.0: (315, 19),   # Left field line (tall wall!)
            -33.75: (362, 19),  # Left-center
            -22.5: (390, 10),   # Left-center gap
            -11.25: (409, 10),  # Deep left-center
            0.0: (409, 10),     # Center
            11.25: (390, 10),   # Right-center
            22.5: (373, 10),    # Right-center gap
            33.75: (350, 10),   # Right-center
            45.0: (326, 10),    # Right field line
        }
    ),
}


def get_ballpark(park_name: str) -> BallparkDimensions:
    """
    Get ballpark dimensions by name.

    Parameters
    ----------
    park_name : str
        Park identifier (e.g., 'fenway', 'yankee', 'coors')
        Use 'generic' for default MLB dimensions

    Returns
    -------
    BallparkDimensions
        Ballpark dimension object

    Examples
    --------
    >>> park = get_ballpark('fenway')
    >>> distance, height = park.get_fence_at_angle(-45)  # Green Monster
    >>> print(f"Distance: {distance} ft, Height: {height} ft")
    Distance: 310 ft, Height: 37 ft
    """
    park_name_lower = park_name.lower()

    # Handle various name formats
    name_aliases = {
        "fenway park": "fenway",
        "boston": "fenway",
        "yankee stadium": "yankee",
        "yankees": "yankee",
        "new york": "yankee",
        "coors field": "coors",
        "colorado": "coors",
        "denver": "coors",
        "oracle park": "oracle",
        "san francisco": "oracle",
        "giants": "oracle",
        "dodger stadium": "dodger",
        "los angeles": "dodger",
        "la": "dodger",
        "wrigley field": "wrigley",
        "chicago cubs": "wrigley",
        "cubs": "wrigley",
        "petco park": "petco",
        "san diego": "petco",
        "padres": "petco",
        "great american ball park": "great_american",
        "cincinnati": "great_american",
        "reds": "great_american",
        "minute maid park": "minute_maid",
        "houston": "minute_maid",
        "astros": "minute_maid",
    }

    # Try exact match first
    if park_name_lower in MLB_BALLPARKS:
        return MLB_BALLPARKS[park_name_lower]

    # Try alias
    if park_name_lower in name_aliases:
        return MLB_BALLPARKS[name_aliases[park_name_lower]]

    # Default to generic
    print(f"Warning: Park '{park_name}' not found, using generic MLB park")
    return MLB_BALLPARKS["generic"]


def list_available_parks() -> list:
    """Get list of all available ballpark names."""
    return sorted(MLB_BALLPARKS.keys())
