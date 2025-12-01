"""
Ballpark environmental effects based on real MLB Statcast data.

This module provides distance adjustments for each MLB ballpark based on:
- Temperature: Every 10°F adds 1% distance
- Elevation: Every 800 feet adds 1% distance  
- Roof: Adds 1% distance (controlled environment)
- Environment: Everything else (humidity, wind patterns, etc.)

Data sourced from Baseball Savant 2025 stadium dimensions and effects.
These factors apply to batted balls hit 90+ MPH, 24-32° launch angle, 
0-24° pull angle - providing apples-to-apples comparison.

Usage:
    from batted_ball.ballpark_effects import get_ballpark_effects, get_ballpark_for_team
    
    # Get effects for a specific park
    effects = get_ballpark_effects('coors')
    print(effects.total_distance_added)  # 19.7 feet
    
    # Get ballpark for a team
    park_id = get_ballpark_for_team('COL')  # Returns 'coors'
"""

from dataclasses import dataclass
from typing import Dict, Optional, Tuple


@dataclass
class BallparkEffects:
    """
    Environmental effects for a specific ballpark.
    
    All distance values in feet - positive means balls travel farther.
    Based on MLB Statcast 2025 data for standardized batted ball conditions.
    """
    park_id: str                    # Internal ID (e.g., 'coors', 'fenway')
    team_abbr: str                  # Team abbreviation (e.g., 'COL', 'BOS')
    venue_name: str                 # Official venue name
    
    # Distance effects (feet added to batted balls)
    total_distance_added: float     # Net distance effect
    temperature_effect: float       # From average game temperature
    elevation_effect: float         # From altitude above sea level
    environment_effect: float       # Humidity, wind patterns, etc.
    roof_effect: float              # From retractable/fixed roof
    
    # Environmental data
    avg_temperature_f: float        # Average game-time temperature
    elevation_ft: int               # Elevation above sea level
    roof_pct: int                   # % of games with roof closed
    day_game_pct: int               # % of day games (affects temp)
    
    # Fence dimensions (from dimensions CSV)
    lf_line: int                    # Left field line distance
    lf_gap: int                     # Left-center gap
    cf: int                         # Center field
    rf_gap: int                     # Right-center gap
    rf_line: int                    # Right field line distance
    deepest_point: int              # Deepest point in park
    avg_fence_distance: int         # Average fence distance
    avg_fence_height: float         # Average fence height
    
    def get_distance_multiplier(self) -> float:
        """
        Get distance multiplier for trajectory calculations.
        
        The total_distance_added is calibrated for balls hit ~385 feet
        in standard conditions. Convert to a multiplier.
        
        Returns
        -------
        float
            Multiplier to apply to batted ball distance (e.g., 1.05 = 5% farther)
        """
        # Standard reference distance for the measurements
        REFERENCE_DISTANCE = 385.0  # feet
        return 1.0 + (self.total_distance_added / REFERENCE_DISTANCE)
    
    def get_air_density_factor(self) -> float:
        """
        Get air density factor relative to sea level at 70°F.
        
        Lower air density = less drag = balls travel farther.
        Based on elevation and temperature effects.
        
        Returns
        -------
        float
            Relative air density (< 1.0 means thinner air)
        """
        # Temperature effect: air is ~3% less dense per 10°F above 70°F
        temp_factor = 1.0 - 0.003 * (self.avg_temperature_f - 70.0)
        
        # Elevation effect: air density decreases ~3% per 1000 feet
        # Using barometric formula approximation
        elevation_factor = 1.0 - 0.00003 * self.elevation_ft
        
        return temp_factor * elevation_factor
    
    def get_humidity_factor(self) -> float:
        """
        Estimate relative humidity factor from environment effect.
        
        Humid air is actually LESS dense than dry air (water vapor 
        is lighter than N2/O2), so high humidity = more distance.
        However, wet balls may have more drag.
        
        Returns
        -------
        float
            Estimated humidity factor (0.4-0.8 typical range)
        """
        # Parks with positive environment effect tend to be drier
        # Parks with negative environment effect tend to be more humid
        # Scale environment effect to estimate humidity
        if self.environment_effect > 5:
            return 0.35  # Very dry (e.g., Denver, Sacramento)
        elif self.environment_effect > 2:
            return 0.45  # Dry
        elif self.environment_effect > 0:
            return 0.50  # Average
        elif self.environment_effect > -3:
            return 0.55  # Slightly humid
        else:
            return 0.65  # Humid (coastal parks)


# =============================================================================
# MLB BALLPARK EFFECTS DATABASE (2025 Season Data)
# =============================================================================
# Data from Baseball Savant stadium dimensions and distance effects
# Total effect broken down into: Temperature + Elevation + Environment + Roof

MLB_BALLPARK_EFFECTS: Dict[str, BallparkEffects] = {
    # -----------------------------------------------------------------
    # Rank 1: Coors Field - The most hitter-friendly park in MLB
    # -----------------------------------------------------------------
    "coors": BallparkEffects(
        park_id="coors",
        team_abbr="COL",
        venue_name="Coors Field",
        total_distance_added=19.7,
        temperature_effect=1.1,
        elevation_effect=23.5,
        environment_effect=-4.9,  # Humidor helps reduce effect
        roof_effect=0.0,
        avg_temperature_f=76.7,
        elevation_ft=5190,
        roof_pct=0,
        day_game_pct=34,
        lf_line=347, lf_gap=408, cf=415, rf_gap=385, rf_line=351,
        deepest_point=422, avg_fence_distance=386, avg_fence_height=11.6,
    ),
    
    # -----------------------------------------------------------------
    # Rank 2: Sutter Health Park (Athletics 2025)
    # -----------------------------------------------------------------
    "sutter": BallparkEffects(
        park_id="sutter",
        team_abbr="OAK",
        venue_name="Sutter Health Park",
        total_distance_added=10.3,
        temperature_effect=2.4,
        elevation_effect=-2.3,
        environment_effect=10.2,  # Hot Sacramento summers
        roof_effect=0.0,
        avg_temperature_f=80.2,
        elevation_ft=24,
        roof_pct=0,
        day_game_pct=29,
        lf_line=330, lf_gap=386, cf=401, rf_gap=375, rf_line=324,
        deepest_point=403, avg_fence_distance=373, avg_fence_height=7.1,
    ),
    
    # -----------------------------------------------------------------
    # Rank 3: Truist Park
    # -----------------------------------------------------------------
    "truist": BallparkEffects(
        park_id="truist",
        team_abbr="ATL",
        venue_name="Truist Park",
        total_distance_added=8.1,
        temperature_effect=1.8,
        elevation_effect=2.4,
        environment_effect=3.9,
        roof_effect=0.0,
        avg_temperature_f=78.7,
        elevation_ft=1001,
        roof_pct=0,
        day_game_pct=31,
        lf_line=335, lf_gap=386, cf=400, rf_gap=379, rf_line=326,
        deepest_point=402, avg_fence_distance=374, avg_fence_height=10.1,
    ),
    
    # -----------------------------------------------------------------
    # Rank 4: Chase Field
    # -----------------------------------------------------------------
    "chase": BallparkEffects(
        park_id="chase",
        team_abbr="ARI",
        venue_name="Chase Field",
        total_distance_added=7.1,
        temperature_effect=1.8,
        elevation_effect=2.8,
        environment_effect=-0.6,
        roof_effect=3.1,  # Retractable roof
        avg_temperature_f=78.6,
        elevation_ft=1086,
        roof_pct=81,
        day_game_pct=25,
        lf_line=329, lf_gap=389, cf=406, rf_gap=389, rf_line=334,
        deepest_point=411, avg_fence_distance=380, avg_fence_height=11.7,
    ),
    
    # -----------------------------------------------------------------
    # Rank 5: Kauffman Stadium
    # -----------------------------------------------------------------
    "kauffman": BallparkEffects(
        park_id="kauffman",
        team_abbr="KC",
        venue_name="Kauffman Stadium",
        total_distance_added=6.0,
        temperature_effect=1.4,
        elevation_effect=1.7,
        environment_effect=2.9,
        roof_effect=0.0,
        avg_temperature_f=77.5,
        elevation_ft=856,
        roof_pct=0,
        day_game_pct=43,
        lf_line=324, lf_gap=393, cf=410, rf_gap=393, rf_line=326,
        deepest_point=410, avg_fence_distance=384, avg_fence_height=8.7,
    ),
    
    # -----------------------------------------------------------------
    # Rank 6: American Family Field
    # -----------------------------------------------------------------
    "american_family": BallparkEffects(
        park_id="american_family",
        team_abbr="MIL",
        venue_name="American Family Field",
        total_distance_added=2.4,
        temperature_effect=-0.7,
        elevation_effect=0.5,
        environment_effect=0.9,
        roof_effect=1.7,  # Retractable roof
        avg_temperature_f=72.2,
        elevation_ft=597,
        roof_pct=45,
        day_game_pct=38,
        lf_line=341, lf_gap=371, cf=399, rf_gap=377, rf_line=345,
        deepest_point=399, avg_fence_distance=372, avg_fence_height=6.9,
    ),
    
    # -----------------------------------------------------------------
    # Rank 7: PNC Park
    # -----------------------------------------------------------------
    "pnc": BallparkEffects(
        park_id="pnc",
        team_abbr="PIT",
        venue_name="PNC Park",
        total_distance_added=1.4,
        temperature_effect=-0.3,
        elevation_effect=1.3,
        environment_effect=0.4,
        roof_effect=0.0,
        avg_temperature_f=73.2,
        elevation_ft=780,
        roof_pct=0,
        day_game_pct=38,
        lf_line=324, lf_gap=400, cf=398, rf_gap=378, rf_line=319,
        deepest_point=409, avg_fence_distance=373, avg_fence_height=11.1,
    ),
    
    # -----------------------------------------------------------------
    # Rank 8: Angel Stadium
    # -----------------------------------------------------------------
    "angel": BallparkEffects(
        park_id="angel",
        team_abbr="LAA",
        venue_name="Angel Stadium",
        total_distance_added=1.3,
        temperature_effect=0.3,
        elevation_effect=-1.7,
        environment_effect=2.7,
        roof_effect=0.0,
        avg_temperature_f=74.9,
        elevation_ft=151,
        roof_pct=0,
        day_game_pct=22,
        lf_line=330, lf_gap=386, cf=398, rf_gap=369, rf_line=330,
        deepest_point=403, avg_fence_distance=375, avg_fence_height=6.1,
    ),
    
    # -----------------------------------------------------------------
    # Rank 9: Target Field
    # -----------------------------------------------------------------
    "target": BallparkEffects(
        park_id="target",
        team_abbr="MIN",
        venue_name="Target Field",
        total_distance_added=1.2,
        temperature_effect=-0.4,
        elevation_effect=1.5,
        environment_effect=0.1,
        roof_effect=0.0,
        avg_temperature_f=72.9,
        elevation_ft=815,
        roof_pct=0,
        day_game_pct=49,
        lf_line=338, lf_gap=382, cf=404, rf_gap=373, rf_line=328,
        deepest_point=410, avg_fence_distance=370, avg_fence_height=13.9,
    ),
    
    # -----------------------------------------------------------------
    # Rank 10: Citizens Bank Park
    # -----------------------------------------------------------------
    "citizens_bank": BallparkEffects(
        park_id="citizens_bank",
        team_abbr="PHI",
        venue_name="Citizens Bank Park",
        total_distance_added=1.1,
        temperature_effect=0.4,
        elevation_effect=-2.3,
        environment_effect=3.0,
        roof_effect=0.0,
        avg_temperature_f=75.1,
        elevation_ft=20,
        roof_pct=0,
        day_game_pct=29,
        lf_line=328, lf_gap=375, cf=402, rf_gap=370, rf_line=330,
        deepest_point=409, avg_fence_distance=365, avg_fence_height=10.3,
    ),
    
    # -----------------------------------------------------------------
    # Rank 11: Oracle Park
    # -----------------------------------------------------------------
    "oracle": BallparkEffects(
        park_id="oracle",
        team_abbr="SF",
        venue_name="Oracle Park",
        total_distance_added=-0.2,
        temperature_effect=-4.0,
        elevation_effect=-2.4,
        environment_effect=6.2,  # Dry San Francisco summers
        roof_effect=0.0,
        avg_temperature_f=63.6,
        elevation_ft=0,
        roof_pct=0,
        day_game_pct=37,
        lf_line=340, lf_gap=377, cf=391, rf_gap=411, rf_line=304,
        deepest_point=413, avg_fence_distance=371, avg_fence_height=12.1,
    ),
    
    # -----------------------------------------------------------------
    # Rank 12: Great American Ball Park
    # -----------------------------------------------------------------
    "great_american": BallparkEffects(
        park_id="great_american",
        team_abbr="CIN",
        venue_name="Great American Ball Park",
        total_distance_added=-0.3,
        temperature_effect=0.1,
        elevation_effect=0.2,
        environment_effect=-0.6,
        roof_effect=0.0,
        avg_temperature_f=74.2,
        elevation_ft=535,
        roof_pct=0,
        day_game_pct=39,
        lf_line=328, lf_gap=376, cf=404, rf_gap=368, rf_line=324,
        deepest_point=404, avg_fence_distance=364, avg_fence_height=8.9,
    ),
    
    # -----------------------------------------------------------------
    # Rank 13: loanDepot Park
    # -----------------------------------------------------------------
    "loandepot": BallparkEffects(
        park_id="loandepot",
        team_abbr="MIA",
        venue_name="loanDepot park",
        total_distance_added=-0.4,
        temperature_effect=-0.2,
        elevation_effect=-2.3,
        environment_effect=-0.9,
        roof_effect=3.0,  # Retractable roof
        avg_temperature_f=73.6,
        elevation_ft=10,
        roof_pct=80,
        day_game_pct=41,
        lf_line=344, lf_gap=387, cf=396, rf_gap=384, rf_line=335,
        deepest_point=403, avg_fence_distance=374, avg_fence_height=8.6,
    ),
    
    # -----------------------------------------------------------------
    # Rank 14: Camden Yards
    # -----------------------------------------------------------------
    "camden": BallparkEffects(
        park_id="camden",
        team_abbr="BAL",
        venue_name="Oriole Park at Camden Yards",
        total_distance_added=-0.6,
        temperature_effect=1.7,
        elevation_effect=-2.2,
        environment_effect=-0.1,
        roof_effect=0.0,
        avg_temperature_f=78.5,
        elevation_ft=33,
        roof_pct=0,
        day_game_pct=45,
        lf_line=333, lf_gap=371, cf=400, rf_gap=386, rf_line=318,
        deepest_point=408, avg_fence_distance=371, avg_fence_height=9.0,
    ),
    
    # -----------------------------------------------------------------
    # Rank 15: Dodger Stadium
    # -----------------------------------------------------------------
    "dodger": BallparkEffects(
        park_id="dodger",
        team_abbr="LAD",
        venue_name="Dodger Stadium",
        total_distance_added=-0.9,
        temperature_effect=-0.8,
        elevation_effect=0.1,
        environment_effect=-0.2,
        roof_effect=0.0,
        avg_temperature_f=71.9,
        elevation_ft=515,
        roof_pct=0,
        day_game_pct=23,
        lf_line=327, lf_gap=372, cf=395, rf_gap=372, rf_line=326,
        deepest_point=395, avg_fence_distance=369, avg_fence_height=7.0,
    ),
    
    # -----------------------------------------------------------------
    # Rank 16: Globe Life Field
    # -----------------------------------------------------------------
    "globe_life": BallparkEffects(
        park_id="globe_life",
        team_abbr="TEX",
        venue_name="Globe Life Field",
        total_distance_added=-0.9,
        temperature_effect=0.3,
        elevation_effect=0.2,
        environment_effect=-4.9,
        roof_effect=3.5,  # Retractable roof
        avg_temperature_f=74.7,
        elevation_ft=545,
        roof_pct=91,
        day_game_pct=28,
        lf_line=328, lf_gap=381, cf=406, rf_gap=373, rf_line=321,
        deepest_point=411, avg_fence_distance=377, avg_fence_height=7.8,
    ),
    
    # -----------------------------------------------------------------
    # Rank 17: Daikin Park (formerly Minute Maid)
    # -----------------------------------------------------------------
    "daikin": BallparkEffects(
        park_id="daikin",
        team_abbr="HOU",
        venue_name="Daikin Park",
        total_distance_added=-1.4,
        temperature_effect=-0.4,
        elevation_effect=-2.2,
        environment_effect=-2.5,
        roof_effect=3.7,  # Retractable roof
        avg_temperature_f=73.0,
        elevation_ft=45,
        roof_pct=98,
        day_game_pct=22,
        lf_line=315, lf_gap=367, cf=409, rf_gap=378, rf_line=325,
        deepest_point=416, avg_fence_distance=364, avg_fence_height=12.6,
    ),
    
    # -----------------------------------------------------------------
    # Rank 18: Rogers Centre
    # -----------------------------------------------------------------
    "rogers": BallparkEffects(
        park_id="rogers",
        team_abbr="TOR",
        venue_name="Rogers Centre",
        total_distance_added=-1.4,
        temperature_effect=-1.7,
        elevation_effect=-1.1,
        environment_effect=-0.6,
        roof_effect=2.0,  # Retractable roof
        avg_temperature_f=69.5,
        elevation_ft=270,
        roof_pct=53,
        day_game_pct=45,
        lf_line=328, lf_gap=381, cf=400, rf_gap=373, rf_line=328,
        deepest_point=400, avg_fence_distance=365, avg_fence_height=11.9,
    ),
    
    # -----------------------------------------------------------------
    # Rank 19: Busch Stadium
    # -----------------------------------------------------------------
    "busch": BallparkEffects(
        park_id="busch",
        team_abbr="STL",
        venue_name="Busch Stadium",
        total_distance_added=-1.7,
        temperature_effect=1.1,
        elevation_effect=-0.2,
        environment_effect=-2.6,
        roof_effect=0.0,
        avg_temperature_f=76.9,
        elevation_ft=460,
        roof_pct=0,
        day_game_pct=41,
        lf_line=335, lf_gap=390, cf=400, rf_gap=391, rf_line=335,
        deepest_point=401, avg_fence_distance=377, avg_fence_height=7.4,
    ),
    
    # -----------------------------------------------------------------
    # Rank 20: Nationals Park
    # -----------------------------------------------------------------
    "nationals": BallparkEffects(
        park_id="nationals",
        team_abbr="WSH",
        venue_name="Nationals Park",
        total_distance_added=-1.9,
        temperature_effect=0.9,
        elevation_effect=-2.2,
        environment_effect=-0.6,
        roof_effect=0.0,
        avg_temperature_f=76.4,
        elevation_ft=35,
        roof_pct=0,
        day_game_pct=48,
        lf_line=336, lf_gap=377, cf=402, rf_gap=370, rf_line=335,
        deepest_point=407, avg_fence_distance=371, avg_fence_height=9.8,
    ),
    
    # -----------------------------------------------------------------
    # Rank 21: Comerica Park
    # -----------------------------------------------------------------
    "comerica": BallparkEffects(
        park_id="comerica",
        team_abbr="DET",
        venue_name="Comerica Park",
        total_distance_added=-2.0,
        temperature_effect=-0.9,
        elevation_effect=0.5,
        environment_effect=-1.6,
        roof_effect=0.0,
        avg_temperature_f=71.5,
        elevation_ft=600,
        roof_pct=0,
        day_game_pct=42,
        lf_line=343, lf_gap=384, cf=412, rf_gap=391, rf_line=327,
        deepest_point=417, avg_fence_distance=377, avg_fence_height=6.7,
    ),
    
    # -----------------------------------------------------------------
    # Rank 22: Progressive Field
    # -----------------------------------------------------------------
    "progressive": BallparkEffects(
        park_id="progressive",
        team_abbr="CLE",
        venue_name="Progressive Field",
        total_distance_added=-2.3,
        temperature_effect=-1.1,
        elevation_effect=0.7,
        environment_effect=-1.9,
        roof_effect=0.0,
        avg_temperature_f=71.2,
        elevation_ft=653,
        roof_pct=0,
        day_game_pct=39,
        lf_line=325, lf_gap=368, cf=400, rf_gap=375, rf_line=325,
        deepest_point=409, avg_fence_distance=366, avg_fence_height=13.4,
    ),
    
    # -----------------------------------------------------------------
    # Rank 23: Fenway Park
    # -----------------------------------------------------------------
    "fenway": BallparkEffects(
        park_id="fenway",
        team_abbr="BOS",
        venue_name="Fenway Park",
        total_distance_added=-3.7,
        temperature_effect=-1.5,
        elevation_effect=-2.3,
        environment_effect=0.1,
        roof_effect=0.0,
        avg_temperature_f=70.1,
        elevation_ft=21,
        roof_pct=0,
        day_game_pct=35,
        lf_line=309, lf_gap=345, cf=388, rf_gap=378, rf_line=299,
        deepest_point=417, avg_fence_distance=362, avg_fence_height=20.3,
    ),
    
    # -----------------------------------------------------------------
    # Rank 24: Petco Park
    # -----------------------------------------------------------------
    "petco": BallparkEffects(
        park_id="petco",
        team_abbr="SD",
        venue_name="Petco Park",
        total_distance_added=-3.9,
        temperature_effect=-1.8,
        elevation_effect=-2.2,
        environment_effect=0.1,
        roof_effect=0.0,
        avg_temperature_f=69.2,
        elevation_ft=23,
        roof_pct=0,
        day_game_pct=34,
        lf_line=335, lf_gap=381, cf=396, rf_gap=389, rf_line=322,
        deepest_point=399, avg_fence_distance=371, avg_fence_height=6.7,
    ),
    
    # -----------------------------------------------------------------
    # Rank 25: T-Mobile Park
    # -----------------------------------------------------------------
    "tmobile": BallparkEffects(
        park_id="tmobile",
        team_abbr="SEA",
        venue_name="T-Mobile Park",
        total_distance_added=-4.1,
        temperature_effect=-3.0,
        elevation_effect=-2.3,
        environment_effect=0.7,
        roof_effect=0.5,  # Retractable roof (rarely closed)
        avg_temperature_f=65.9,
        elevation_ft=10,
        roof_pct=12,
        day_game_pct=26,
        lf_line=331, lf_gap=379, cf=401, rf_gap=382, rf_line=327,
        deepest_point=405, avg_fence_distance=367, avg_fence_height=7.6,
    ),
    
    # -----------------------------------------------------------------
    # Rank 26: Citi Field
    # -----------------------------------------------------------------
    "citi": BallparkEffects(
        park_id="citi",
        team_abbr="NYM",
        venue_name="Citi Field",
        total_distance_added=-4.7,
        temperature_effect=-1.1,
        elevation_effect=-2.3,
        environment_effect=-1.3,
        roof_effect=0.0,
        avg_temperature_f=71.2,
        elevation_ft=10,
        roof_pct=0,
        day_game_pct=39,
        lf_line=334, lf_gap=368, cf=407, rf_gap=372, rf_line=330,
        deepest_point=408, avg_fence_distance=370, avg_fence_height=8.2,
    ),
    
    # -----------------------------------------------------------------
    # Rank 27: Wrigley Field
    # -----------------------------------------------------------------
    "wrigley": BallparkEffects(
        park_id="wrigley",
        team_abbr="CHC",
        venue_name="Wrigley Field",
        total_distance_added=-5.4,
        temperature_effect=-1.9,
        elevation_effect=0.4,
        environment_effect=-3.9,  # Lake Michigan wind patterns
        roof_effect=0.0,
        avg_temperature_f=68.9,
        elevation_ft=595,
        roof_pct=0,
        day_game_pct=62,  # Most day games in MLB
        lf_line=354, lf_gap=356, cf=397, rf_gap=379, rf_line=349,
        deepest_point=401, avg_fence_distance=368, avg_fence_height=11.2,
    ),
    
    # -----------------------------------------------------------------
    # Rank 28: Steinbrenner Field (Rays 2025 temporary home)
    # -----------------------------------------------------------------
    "steinbrenner": BallparkEffects(
        park_id="steinbrenner",
        team_abbr="TB",
        venue_name="George M. Steinbrenner Field",
        total_distance_added=-5.9,
        temperature_effect=3.8,  # Hot Florida weather
        elevation_effect=-2.2,
        environment_effect=-7.5,  # Humid Florida air
        roof_effect=0.0,
        avg_temperature_f=84.2,
        elevation_ft=34,
        roof_pct=0,
        day_game_pct=40,
        lf_line=319, lf_gap=391, cf=407, rf_gap=365, rf_line=314,
        deepest_point=408, avg_fence_distance=368, avg_fence_height=6.1,
    ),
    
    # -----------------------------------------------------------------
    # Rank 29: Yankee Stadium
    # -----------------------------------------------------------------
    "yankee": BallparkEffects(
        park_id="yankee",
        team_abbr="NYY",
        venue_name="Yankee Stadium",
        total_distance_added=-6.2,
        temperature_effect=-0.2,
        elevation_effect=-2.1,
        environment_effect=-3.9,
        roof_effect=0.0,
        avg_temperature_f=73.4,
        elevation_ft=55,
        roof_pct=0,
        day_game_pct=33,
        lf_line=318, lf_gap=392, cf=408, rf_gap=364, rf_line=313,
        deepest_point=409, avg_fence_distance=369, avg_fence_height=8.1,
    ),
    
    # -----------------------------------------------------------------
    # Rank 30: Rate Field (formerly Guaranteed Rate)
    # -----------------------------------------------------------------
    "rate": BallparkEffects(
        park_id="rate",
        team_abbr="CHW",
        venue_name="Rate Field",
        total_distance_added=-8.1,
        temperature_effect=-1.6,
        elevation_effect=0.4,
        environment_effect=-6.9,  # Lake Michigan wind patterns (worse than Wrigley)
        roof_effect=0.0,
        avg_temperature_f=69.7,
        elevation_ft=595,
        roof_pct=0,
        day_game_pct=42,
        lf_line=328, lf_gap=379, cf=400, rf_gap=380, rf_line=335,
        deepest_point=402, avg_fence_distance=369, avg_fence_height=6.6,
    ),
    
    # -----------------------------------------------------------------
    # Generic park (neutral effects)
    # -----------------------------------------------------------------
    "generic": BallparkEffects(
        park_id="generic",
        team_abbr="",
        venue_name="Generic MLB Park",
        total_distance_added=0.0,
        temperature_effect=0.0,
        elevation_effect=0.0,
        environment_effect=0.0,
        roof_effect=0.0,
        avg_temperature_f=70.0,
        elevation_ft=0,
        roof_pct=0,
        day_game_pct=35,
        lf_line=330, lf_gap=375, cf=400, rf_gap=375, rf_line=330,
        deepest_point=400, avg_fence_distance=370, avg_fence_height=8.0,
    ),
}


# =============================================================================
# TEAM TO BALLPARK MAPPING
# =============================================================================
# Maps team abbreviations to their home ballpark

TEAM_BALLPARK_MAP: Dict[str, str] = {
    # American League East
    "BAL": "camden",
    "BOS": "fenway",
    "NYY": "yankee",
    "TB":  "steinbrenner",  # 2025: Rays playing at Steinbrenner Field
    "TOR": "rogers",
    
    # American League Central
    "CHW": "rate",
    "CLE": "progressive",
    "DET": "comerica",
    "KC":  "kauffman",
    "MIN": "target",
    
    # American League West
    "HOU": "daikin",
    "LAA": "angel",
    "OAK": "sutter",  # 2025: Athletics at Sutter Health Park (Sacramento)
    "SEA": "tmobile",
    "TEX": "globe_life",
    
    # National League East
    "ATL": "truist",
    "MIA": "loandepot",
    "NYM": "citi",
    "PHI": "citizens_bank",
    "WSH": "nationals",
    
    # National League Central
    "CHC": "wrigley",
    "CIN": "great_american",
    "MIL": "american_family",
    "PIT": "pnc",
    "STL": "busch",
    
    # National League West
    "ARI": "chase",
    "COL": "coors",
    "LAD": "dodger",
    "SD":  "petco",
    "SF":  "oracle",
}


# =============================================================================
# ACCESSOR FUNCTIONS
# =============================================================================

def get_ballpark_effects(park_id: str) -> BallparkEffects:
    """
    Get ballpark effects by park ID.
    
    Parameters
    ----------
    park_id : str
        Park identifier (e.g., 'coors', 'fenway', 'yankee')
    
    Returns
    -------
    BallparkEffects
        Environmental effects for the ballpark
    
    Examples
    --------
    >>> effects = get_ballpark_effects('coors')
    >>> print(effects.total_distance_added)
    19.7
    """
    park_id_lower = park_id.lower()
    
    # Handle common aliases
    aliases = {
        "minute_maid": "daikin",
        "minutemaid": "daikin",
        "guaranteed_rate": "rate",
        "guaranteedrate": "rate",
        "tropicana": "steinbrenner",  # Rays 2025
        "trop": "steinbrenner",
        "oakland": "sutter",  # A's 2025
        "coliseum": "sutter",
        "safeco": "tmobile",
        "miller": "american_family",
    }
    
    if park_id_lower in aliases:
        park_id_lower = aliases[park_id_lower]
    
    if park_id_lower in MLB_BALLPARK_EFFECTS:
        return MLB_BALLPARK_EFFECTS[park_id_lower]
    
    # Default to generic
    return MLB_BALLPARK_EFFECTS["generic"]


def get_ballpark_for_team(team_abbr: str) -> str:
    """
    Get ballpark ID for a team.
    
    Parameters
    ----------
    team_abbr : str
        Team abbreviation (e.g., 'NYY', 'COL', 'BOS')
    
    Returns
    -------
    str
        Ballpark ID
    
    Examples
    --------
    >>> get_ballpark_for_team('COL')
    'coors'
    >>> get_ballpark_for_team('NYY')
    'yankee'
    """
    # Normalize to uppercase
    abbr = team_abbr.upper()
    
    # Handle common variations
    from .database.team_mappings import get_db_abbr
    abbr = get_db_abbr(abbr)
    
    return TEAM_BALLPARK_MAP.get(abbr, "generic")


def get_team_ballpark_effects(team_abbr: str) -> BallparkEffects:
    """
    Get ballpark effects for a team's home park.
    
    Parameters
    ----------
    team_abbr : str
        Team abbreviation
    
    Returns
    -------
    BallparkEffects
        Environmental effects for the team's home ballpark
    
    Examples
    --------
    >>> effects = get_team_ballpark_effects('COL')
    >>> print(effects.venue_name)
    'Coors Field'
    >>> print(effects.elevation_ft)
    5190
    """
    park_id = get_ballpark_for_team(team_abbr)
    return get_ballpark_effects(park_id)


def list_ballparks() -> list:
    """Get list of all available ballpark IDs."""
    return sorted([k for k in MLB_BALLPARK_EFFECTS.keys() if k != "generic"])


def get_ballpark_by_team_name(team_name: str) -> Optional[str]:
    """
    Get ballpark ID from team name.
    
    Parameters
    ----------
    team_name : str
        Full team name (e.g., 'New York Yankees', 'Colorado Rockies')
    
    Returns
    -------
    str or None
        Ballpark ID, or None if not found
    """
    # Map team names to abbreviations
    name_to_abbr = {
        "Baltimore Orioles": "BAL",
        "Boston Red Sox": "BOS",
        "New York Yankees": "NYY",
        "Tampa Bay Rays": "TB",
        "Toronto Blue Jays": "TOR",
        "Chicago White Sox": "CHW",
        "Cleveland Guardians": "CLE",
        "Detroit Tigers": "DET",
        "Kansas City Royals": "KC",
        "Minnesota Twins": "MIN",
        "Houston Astros": "HOU",
        "Los Angeles Angels": "LAA",
        "Athletics": "OAK",
        "Oakland Athletics": "OAK",
        "Seattle Mariners": "SEA",
        "Texas Rangers": "TEX",
        "Atlanta Braves": "ATL",
        "Miami Marlins": "MIA",
        "New York Mets": "NYM",
        "Philadelphia Phillies": "PHI",
        "Washington Nationals": "WSH",
        "Chicago Cubs": "CHC",
        "Cincinnati Reds": "CIN",
        "Milwaukee Brewers": "MIL",
        "Pittsburgh Pirates": "PIT",
        "St. Louis Cardinals": "STL",
        "Arizona Diamondbacks": "ARI",
        "Colorado Rockies": "COL",
        "Los Angeles Dodgers": "LAD",
        "San Diego Padres": "SD",
        "San Francisco Giants": "SF",
    }
    
    abbr = name_to_abbr.get(team_name)
    if abbr:
        return get_ballpark_for_team(abbr)
    return None


def print_ballpark_summary():
    """Print summary of all ballpark effects."""
    print("\n" + "="*90)
    print("MLB BALLPARK DISTANCE EFFECTS (2025)")
    print("="*90)
    print(f"{'Rank':<5} {'Park':<30} {'Team':<5} {'Total':>7} {'Temp':>6} {'Elev':>6} {'Env':>6} {'Roof':>6}")
    print("-"*90)
    
    # Sort by total distance
    sorted_parks = sorted(
        [(k, v) for k, v in MLB_BALLPARK_EFFECTS.items() if k != "generic"],
        key=lambda x: x[1].total_distance_added,
        reverse=True
    )
    
    for rank, (park_id, effects) in enumerate(sorted_parks, 1):
        print(f"{rank:<5} {effects.venue_name:<30} {effects.team_abbr:<5} "
              f"{effects.total_distance_added:>+7.1f} {effects.temperature_effect:>+6.1f} "
              f"{effects.elevation_effect:>+6.1f} {effects.environment_effect:>+6.1f} "
              f"{effects.roof_effect:>+6.1f}")
    
    print("="*90)
    print("Note: All values in feet added to batted ball distance")
    print("      Positive = balls travel farther, Negative = balls travel shorter")


if __name__ == "__main__":
    # Demo the module
    print_ballpark_summary()
    
    print("\n\nExample usage:")
    print("-" * 40)
    
    # Get Coors Field effects
    coors = get_ballpark_effects("coors")
    print(f"\n{coors.venue_name}:")
    print(f"  Total distance effect: {coors.total_distance_added:+.1f} ft")
    print(f"  Distance multiplier: {coors.get_distance_multiplier():.4f}")
    print(f"  Elevation: {coors.elevation_ft:,} ft")
    print(f"  Avg temperature: {coors.avg_temperature_f}°F")
    
    # Get team ballpark
    yankees_park = get_ballpark_for_team("NYY")
    yankees_effects = get_ballpark_effects(yankees_park)
    print(f"\nNew York Yankees home park: {yankees_effects.venue_name}")
    print(f"  Distance effect: {yankees_effects.total_distance_added:+.1f} ft")
