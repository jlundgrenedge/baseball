"""
Ballpark dimensions and characteristics for MLB stadiums.

Provides detailed ballpark data including fence distances, heights, and other
park-specific factors that affect batted ball outcomes.

Data sourced from official MLB stadium specifications and Baseball Savant 2025.

This module provides:
- BallparkDimensions class for fence profiles
- All 30 MLB ballparks with accurate 2025 dimensions
- get_ballpark() function with extensive alias support
- Integration with ballpark_effects module for environmental factors
"""

import numpy as np
from typing import Dict, Tuple, Optional


class BallparkDimensions:
    """
    Detailed ballpark dimensions including fence distances and heights at various angles.

    All distances in feet, heights in feet, angles in degrees from center field.
    Spray angle convention: 0° = center field, negative = left field, positive = right field.
    """

    def __init__(self, name: str, fence_profile: Dict[float, Tuple[float, float]],
                 park_id: str = None, team_abbr: str = None):
        """
        Initialize ballpark dimensions.

        Parameters
        ----------
        name : str
            Stadium name
        fence_profile : Dict[float, Tuple[float, float]]
            Mapping of spray angle (degrees) to (distance_ft, height_ft).
            Angles: 0° = center, -45° = left field line, +45° = right field line
        park_id : str, optional
            Internal park identifier (for linking to ballpark_effects)
        team_abbr : str, optional
            Team abbreviation that plays here

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
        self.park_id = park_id
        self.team_abbr = team_abbr

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


def _create_fence_profile(lf_line, lf_gap, cf, rf_gap, rf_line, 
                          lf_height=8, cf_height=8, rf_height=8) -> Dict[float, Tuple[float, float]]:
    """
    Create a standard 9-point fence profile from the 5 main dimensions.
    """
    lf_gap_height = (lf_height + cf_height) // 2
    rf_gap_height = (rf_height + cf_height) // 2
    
    # Interpolate intermediate points
    lf_alley = (lf_line + lf_gap) // 2
    lf_deep = (lf_gap + cf) // 2
    rf_deep = (cf + rf_gap) // 2
    rf_alley = (rf_gap + rf_line) // 2
    
    return {
        -45.0:  (lf_line, lf_height),
        -33.75: (lf_alley, lf_height),
        -22.5:  (lf_gap, lf_gap_height),
        -11.25: (lf_deep, cf_height),
        0.0:    (cf, cf_height),
        11.25:  (rf_deep, cf_height),
        22.5:   (rf_gap, rf_gap_height),
        33.75:  (rf_alley, rf_height),
        45.0:   (rf_line, rf_height),
    }


# ============================================================================
# MLB BALLPARK DATABASE - 2025 Season
# ============================================================================
# Data sourced from Baseball Savant 2025 stadium dimensions

MLB_BALLPARKS = {
    # GENERIC (neutral park)
    "generic": BallparkDimensions(
        "Generic MLB Park",
        _create_fence_profile(330, 375, 400, 375, 330, 8, 8, 8),
        park_id="generic", team_abbr="",
    ),

    # AMERICAN LEAGUE EAST
    "camden": BallparkDimensions(
        "Oriole Park at Camden Yards",
        _create_fence_profile(333, 371, 400, 386, 318, 7, 9, 7),
        park_id="camden", team_abbr="BAL",
    ),
    "fenway": BallparkDimensions(
        "Fenway Park",
        {
            -45.0:  (309, 37), -33.75: (327, 37), -22.5: (345, 20),
            -11.25: (366, 10), 0.0: (388, 10), 11.25: (383, 5),
            22.5:   (378, 5), 33.75: (338, 5), 45.0: (299, 5),
        },
        park_id="fenway", team_abbr="BOS",
    ),
    "yankee": BallparkDimensions(
        "Yankee Stadium",
        _create_fence_profile(318, 392, 408, 364, 313, 8, 8, 8),
        park_id="yankee", team_abbr="NYY",
    ),
    "steinbrenner": BallparkDimensions(
        "George M. Steinbrenner Field",  # Rays 2025
        _create_fence_profile(319, 391, 407, 365, 314, 6, 6, 6),
        park_id="steinbrenner", team_abbr="TB",
    ),
    "rogers": BallparkDimensions(
        "Rogers Centre",
        _create_fence_profile(328, 381, 400, 373, 328, 12, 12, 12),
        park_id="rogers", team_abbr="TOR",
    ),

    # AMERICAN LEAGUE CENTRAL
    "rate": BallparkDimensions(
        "Rate Field",
        _create_fence_profile(328, 379, 400, 380, 335, 7, 7, 7),
        park_id="rate", team_abbr="CHW",
    ),
    "progressive": BallparkDimensions(
        "Progressive Field",
        _create_fence_profile(325, 368, 400, 375, 325, 13, 13, 13),
        park_id="progressive", team_abbr="CLE",
    ),
    "comerica": BallparkDimensions(
        "Comerica Park",
        _create_fence_profile(343, 384, 412, 391, 327, 7, 7, 7),
        park_id="comerica", team_abbr="DET",
    ),
    "kauffman": BallparkDimensions(
        "Kauffman Stadium",
        _create_fence_profile(324, 393, 410, 393, 326, 9, 9, 9),
        park_id="kauffman", team_abbr="KC",
    ),
    "target": BallparkDimensions(
        "Target Field",
        _create_fence_profile(338, 382, 404, 373, 328, 14, 14, 14),
        park_id="target", team_abbr="MIN",
    ),

    # AMERICAN LEAGUE WEST
    "daikin": BallparkDimensions(
        "Daikin Park",  # Formerly Minute Maid
        {
            -45.0: (315, 19), -33.75: (341, 15), -22.5: (367, 10),
            -11.25: (388, 10), 0.0: (409, 10), 11.25: (393, 10),
            22.5: (378, 10), 33.75: (351, 10), 45.0: (325, 10),
        },
        park_id="daikin", team_abbr="HOU",
    ),
    "minute_maid": BallparkDimensions(  # Alias for backwards compatibility
        "Daikin Park",
        {
            -45.0: (315, 19), -33.75: (341, 15), -22.5: (367, 10),
            -11.25: (388, 10), 0.0: (409, 10), 11.25: (393, 10),
            22.5: (378, 10), 33.75: (351, 10), 45.0: (325, 10),
        },
        park_id="daikin", team_abbr="HOU",
    ),
    "angel": BallparkDimensions(
        "Angel Stadium",
        _create_fence_profile(330, 386, 398, 369, 330, 6, 6, 6),
        park_id="angel", team_abbr="LAA",
    ),
    "sutter": BallparkDimensions(
        "Sutter Health Park",  # Athletics 2025 (Sacramento)
        _create_fence_profile(330, 386, 401, 375, 324, 7, 7, 7),
        park_id="sutter", team_abbr="OAK",
    ),
    "tmobile": BallparkDimensions(
        "T-Mobile Park",
        _create_fence_profile(331, 379, 401, 382, 327, 8, 8, 8),
        park_id="tmobile", team_abbr="SEA",
    ),
    "globe_life": BallparkDimensions(
        "Globe Life Field",
        _create_fence_profile(328, 381, 406, 373, 321, 8, 8, 8),
        park_id="globe_life", team_abbr="TEX",
    ),

    # NATIONAL LEAGUE EAST
    "truist": BallparkDimensions(
        "Truist Park",
        _create_fence_profile(335, 386, 400, 379, 326, 10, 10, 10),
        park_id="truist", team_abbr="ATL",
    ),
    "loandepot": BallparkDimensions(
        "loanDepot park",
        _create_fence_profile(344, 387, 396, 384, 335, 9, 9, 9),
        park_id="loandepot", team_abbr="MIA",
    ),
    "citi": BallparkDimensions(
        "Citi Field",
        _create_fence_profile(334, 368, 407, 372, 330, 8, 8, 8),
        park_id="citi", team_abbr="NYM",
    ),
    "citizens_bank": BallparkDimensions(
        "Citizens Bank Park",
        _create_fence_profile(328, 375, 402, 370, 330, 10, 10, 10),
        park_id="citizens_bank", team_abbr="PHI",
    ),
    "nationals": BallparkDimensions(
        "Nationals Park",
        _create_fence_profile(336, 377, 402, 370, 335, 10, 10, 10),
        park_id="nationals", team_abbr="WSH",
    ),

    # NATIONAL LEAGUE CENTRAL
    "wrigley": BallparkDimensions(
        "Wrigley Field",
        _create_fence_profile(354, 356, 397, 379, 349, 11, 11, 11),
        park_id="wrigley", team_abbr="CHC",
    ),
    "great_american": BallparkDimensions(
        "Great American Ball Park",
        _create_fence_profile(328, 376, 404, 368, 324, 9, 9, 9),
        park_id="great_american", team_abbr="CIN",
    ),
    "american_family": BallparkDimensions(
        "American Family Field",
        _create_fence_profile(341, 371, 399, 377, 345, 7, 7, 7),
        park_id="american_family", team_abbr="MIL",
    ),
    "pnc": BallparkDimensions(
        "PNC Park",
        _create_fence_profile(324, 400, 398, 378, 319, 11, 11, 11),
        park_id="pnc", team_abbr="PIT",
    ),
    "busch": BallparkDimensions(
        "Busch Stadium",
        _create_fence_profile(335, 390, 400, 391, 335, 7, 7, 7),
        park_id="busch", team_abbr="STL",
    ),

    # NATIONAL LEAGUE WEST
    "chase": BallparkDimensions(
        "Chase Field",
        _create_fence_profile(329, 389, 406, 389, 334, 12, 12, 12),
        park_id="chase", team_abbr="ARI",
    ),
    "coors": BallparkDimensions(
        "Coors Field",
        _create_fence_profile(347, 408, 415, 385, 351, 12, 12, 12),
        park_id="coors", team_abbr="COL",
    ),
    "dodger": BallparkDimensions(
        "Dodger Stadium",
        _create_fence_profile(327, 372, 395, 372, 326, 7, 7, 7),
        park_id="dodger", team_abbr="LAD",
    ),
    "petco": BallparkDimensions(
        "Petco Park",
        _create_fence_profile(335, 381, 396, 389, 322, 7, 7, 7),
        park_id="petco", team_abbr="SD",
    ),
    "oracle": BallparkDimensions(
        "Oracle Park",
        {
            -45.0: (340, 8), -33.75: (358, 8), -22.5: (377, 8),
            -11.25: (384, 8), 0.0: (391, 8), 11.25: (401, 8),
            22.5: (411, 25), 33.75: (357, 25), 45.0: (304, 25),
        },
        park_id="oracle", team_abbr="SF",
    ),
}


# ============================================================================
# TEAM-TO-PARK MAPPINGS
# ============================================================================
# Maps team abbreviations, names, and cities to their ballpark

TEAM_TO_PARK = {
    # Team abbreviations (primary key)
    "bal": "camden", "bos": "fenway", "nyy": "yankee", "tb": "steinbrenner", 
    "tor": "rogers", "chw": "rate", "cle": "progressive", "det": "comerica", 
    "kc": "kauffman", "min": "target", "hou": "daikin", "laa": "angel", 
    "oak": "sutter", "sea": "tmobile", "tex": "globe_life",
    "atl": "truist", "mia": "loandepot", "nym": "citi", "phi": "citizens_bank", 
    "wsh": "nationals", "chc": "wrigley", "cin": "great_american", 
    "mil": "american_family", "pit": "pnc", "stl": "busch",
    "ari": "chase", "col": "coors", "lad": "dodger", "sd": "petco", "sf": "oracle",
    
    # Team name variations
    "orioles": "camden", "baltimore orioles": "camden", "baltimore": "camden",
    "red sox": "fenway", "boston red sox": "fenway", "boston": "fenway",
    "yankees": "yankee", "new york yankees": "yankee", 
    "rays": "steinbrenner", "tampa bay rays": "steinbrenner", "tampa bay": "steinbrenner", "tampa": "steinbrenner",
    "blue jays": "rogers", "toronto blue jays": "rogers", "toronto": "rogers",
    "white sox": "rate", "chicago white sox": "rate",
    "guardians": "progressive", "cleveland guardians": "progressive", "cleveland": "progressive",
    "tigers": "comerica", "detroit tigers": "comerica", "detroit": "comerica",
    "royals": "kauffman", "kansas city royals": "kauffman", "kansas city": "kauffman",
    "twins": "target", "minnesota twins": "target", "minnesota": "target",
    "astros": "daikin", "houston astros": "daikin", "houston": "daikin",
    "angels": "angel", "los angeles angels": "angel", "la angels": "angel", "anaheim": "angel",
    "athletics": "sutter", "oakland athletics": "sutter", "oakland": "sutter", "a's": "sutter",
    "mariners": "tmobile", "seattle mariners": "tmobile", "seattle": "tmobile",
    "rangers": "globe_life", "texas rangers": "globe_life", "texas": "globe_life",
    "braves": "truist", "atlanta braves": "truist", "atlanta": "truist",
    "marlins": "loandepot", "miami marlins": "loandepot", "miami": "loandepot",
    "mets": "citi", "new york mets": "citi",
    "phillies": "citizens_bank", "philadelphia phillies": "citizens_bank", "philadelphia": "citizens_bank", "philly": "citizens_bank",
    "nationals": "nationals", "washington nationals": "nationals", "washington": "nationals",
    "cubs": "wrigley", "chicago cubs": "wrigley",
    "reds": "great_american", "cincinnati reds": "great_american", "cincinnati": "great_american",
    "brewers": "american_family", "milwaukee brewers": "american_family", "milwaukee": "american_family",
    "pirates": "pnc", "pittsburgh pirates": "pnc", "pittsburgh": "pnc",
    "cardinals": "busch", "st. louis cardinals": "busch", "st louis cardinals": "busch", "st. louis": "busch", "st louis": "busch",
    "diamondbacks": "chase", "arizona diamondbacks": "chase", "arizona": "chase", "d-backs": "chase", "dbacks": "chase",
    "rockies": "coors", "colorado rockies": "coors", "colorado": "coors", "denver": "coors",
    "dodgers": "dodger", "los angeles dodgers": "dodger", "la dodgers": "dodger", "la": "dodger",
    "padres": "petco", "san diego padres": "petco", "san diego": "petco",
    "giants": "oracle", "san francisco giants": "oracle", "san francisco": "oracle", "sf giants": "oracle",
    
    # Park name variations
    "oriole park": "camden", "oriole park at camden yards": "camden", "camden yards": "camden",
    "fenway park": "fenway",
    "yankee stadium": "yankee",
    "george m. steinbrenner field": "steinbrenner", "steinbrenner field": "steinbrenner",
    "rogers centre": "rogers", "skydome": "rogers",
    "rate field": "rate", "guaranteed rate field": "rate", "u.s. cellular field": "rate", "comiskey park": "rate",
    "progressive field": "progressive", "jacobs field": "progressive",
    "comerica park": "comerica",
    "kauffman stadium": "kauffman", "the k": "kauffman",
    "target field": "target",
    "daikin park": "daikin", "minute maid park": "minute_maid", "minute maid": "minute_maid",
    "angel stadium": "angel", "the big a": "angel",
    "sutter health park": "sutter",
    "t-mobile park": "tmobile", "safeco field": "tmobile",
    "globe life field": "globe_life", "globe life park": "globe_life",
    "truist park": "truist", "suntrust park": "truist",
    "loandepot park": "loandepot", "marlins park": "loandepot",
    "citi field": "citi",
    "citizens bank park": "citizens_bank",
    "nationals park": "nationals",
    "wrigley field": "wrigley",
    "great american ball park": "great_american", "great american ballpark": "great_american",
    "american family field": "american_family", "miller park": "american_family",
    "pnc park": "pnc",
    "busch stadium": "busch",
    "chase field": "chase", "bank one ballpark": "chase",
    "coors field": "coors",
    "dodger stadium": "dodger", "chavez ravine": "dodger",
    "petco park": "petco",
    "oracle park": "oracle", "at&t park": "oracle", "pac bell park": "oracle",
}


def get_ballpark(park_name: str) -> BallparkDimensions:
    """
    Get ballpark dimensions by name, team abbreviation, or city.

    Parameters
    ----------
    park_name : str
        Park identifier (e.g., 'fenway', 'NYY', 'Los Angeles Dodgers')
        Use 'generic' for default MLB dimensions

    Returns
    -------
    BallparkDimensions
        Ballpark dimension object

    Examples
    --------
    >>> park = get_ballpark('fenway')
    >>> park = get_ballpark('BOS')  # Same result via team abbreviation
    >>> park = get_ballpark('Boston Red Sox')  # Also works
    >>> distance, height = park.get_fence_at_angle(-45)
    >>> print(f"Distance: {distance} ft, Height: {height} ft")
    Distance: 309 ft, Height: 37 ft
    """
    park_name_lower = park_name.lower().strip()

    # Try exact match first
    if park_name_lower in MLB_BALLPARKS:
        return MLB_BALLPARKS[park_name_lower]

    # Try team/alias mapping
    if park_name_lower in TEAM_TO_PARK:
        return MLB_BALLPARKS[TEAM_TO_PARK[park_name_lower]]

    # Default to generic
    print(f"Warning: Park '{park_name}' not found, using generic MLB park")
    return MLB_BALLPARKS["generic"]


def get_ballpark_for_team(team_abbr: str) -> BallparkDimensions:
    """
    Get ballpark dimensions for a team by abbreviation.
    
    Parameters
    ----------
    team_abbr : str
        Team abbreviation (e.g., 'NYY', 'BOS', 'LAD')
    
    Returns
    -------
    BallparkDimensions
        Ballpark dimension object for the team's home field
    """
    return get_ballpark(team_abbr)


def list_available_parks() -> list:
    """Get list of all available ballpark names."""
    return sorted(MLB_BALLPARKS.keys())
