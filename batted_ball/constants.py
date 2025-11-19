"""
Physical constants and baseball specifications for trajectory simulation.
"""

import math

# ============================================================================
# FUNDAMENTAL PHYSICAL CONSTANTS
# ============================================================================

GRAVITY = 9.81  # m/s² - gravitational acceleration
RHO_SEA_LEVEL = 1.225  # kg/m³ - air density at sea level, 15°C

# ============================================================================
# BASEBALL SPECIFICATIONS (Official MLB)
# ============================================================================

BALL_MASS = 0.145  # kg (approximately 5.125 oz)
BALL_DIAMETER = 0.074  # meters (approximately 2.9 inches)
BALL_RADIUS = BALL_DIAMETER / 2.0  # meters
BALL_CIRCUMFERENCE = math.pi * BALL_DIAMETER  # meters
BALL_CROSS_SECTIONAL_AREA = math.pi * (BALL_RADIUS ** 2)  # m²

# ============================================================================
# AERODYNAMIC COEFFICIENTS
# ============================================================================

# Drag coefficient (dimensionless)
# Varies with Reynolds number, but typically 0.3-0.5 for baseball
# Calibrated to match empirical distance data
CD_BASE = 0.32  # Base drag coefficient (calibrated)
CD_MIN = 0.25    # Minimum drag coefficient
CD_MAX = 0.5    # Maximum drag coefficient

# Lift coefficient (Magnus effect)
# Relates to spin rate and velocity
CL_BASE = 0.0001  # Base lift coefficient per rpm
CL_MAX = 0.6      # Maximum lift coefficient (high spin saturation)

# Spin factor for Magnus effect (empirically derived)
# This relates spin rate to lift coefficient
# Calibrated to match empirical backspin effects (~60 ft boost for 1500 rpm)
# Fine-tuned to balance benchmark distance with backspin boost
SPIN_FACTOR = 0.000145  # Empirical constant for C_L calculation (re-calibrated)

# ============================================================================
# UNIT CONVERSION CONSTANTS
# ============================================================================

MPH_TO_MS = 0.44704      # miles per hour to meters per second
MS_TO_MPH = 1.0 / MPH_TO_MS  # meters per second to miles per hour
FEET_TO_METERS = 0.3048  # feet to meters
METERS_TO_FEET = 1.0 / FEET_TO_METERS  # meters to feet
DEG_TO_RAD = math.pi / 180.0  # degrees to radians
RAD_TO_DEG = 180.0 / math.pi  # radians to degrees

# ============================================================================
# ENVIRONMENTAL REFERENCE VALUES
# ============================================================================

TEMP_REFERENCE_F = 70.0  # Fahrenheit - reference temperature
TEMP_REFERENCE_C = (TEMP_REFERENCE_F - 32.0) * 5.0 / 9.0  # Celsius
TEMP_REFERENCE_K = TEMP_REFERENCE_C + 273.15  # Kelvin

ALTITUDE_SEA_LEVEL = 0.0  # feet
PRESSURE_SEA_LEVEL = 101325.0  # Pascals

# Temperature lapse rate (standard atmosphere)
LAPSE_RATE = 0.0065  # K/m - temperature decrease with altitude

# ============================================================================
# EMPIRICAL CALIBRATION CONSTANTS
# ============================================================================

# Distance change per mph exit velocity (empirically ~5 ft/mph)
DISTANCE_PER_MPH = 5.0  # feet per mph

# Distance change per degree Fahrenheit (empirically ~0.3-0.4 ft/°F)
DISTANCE_PER_DEGREE_F = 0.35  # feet per °F

# Distance change per 1000 feet altitude (empirically ~6 ft/1000 ft)
DISTANCE_PER_1000_FT_ALTITUDE = 6.0  # feet per 1000 ft

# Wind effect (empirically ~3.5-4 ft per mph wind)
DISTANCE_PER_MPH_WIND = 3.8  # feet per mph tailwind

# Optimal launch angle for maximum distance
OPTIMAL_LAUNCH_ANGLE = 28.0  # degrees

# Typical backspin range for fly balls
TYPICAL_BACKSPIN_MIN = 1500.0  # rpm
TYPICAL_BACKSPIN_MAX = 2500.0  # rpm
TYPICAL_BACKSPIN_OPTIMAL = 1800.0  # rpm

# Spin saturation point (diminishing returns above this)
SPIN_SATURATION = 2500.0  # rpm

# Spin-dependent drag enhancement
# Spinning ball experiences additional drag due to turbulent boundary layer
SPIN_DRAG_FACTOR = 0.00002  # Additional drag per rpm of total spin
SPIN_DRAG_MAX_INCREASE = 0.15  # Maximum drag coefficient increase (caps at high spin)

# Asymmetric drag for tilted spin axis (affects sidespin)
# When spin axis is tilted (both backspin and sidespin), drag increases
TILTED_SPIN_DRAG_FACTOR = 0.00001  # Additional drag for non-aligned spin

# ============================================================================
# SIMULATION PARAMETERS
# ============================================================================

# Time step for numerical integration (seconds)
DT_DEFAULT = 0.001  # 1 millisecond (good balance of accuracy and speed)
DT_FINE = 0.0005    # 0.5 millisecond (higher accuracy)
DT_COARSE = 0.005   # 5 milliseconds (faster, less accurate)
DT_FAST = 0.002     # 2 milliseconds (for bulk simulations - 2x faster, <1% accuracy loss)

# Maximum simulation time (to prevent infinite loops)
MAX_SIMULATION_TIME = 10.0  # seconds

# Ground level height (simulation stops when ball reaches this)
GROUND_LEVEL = 0.0  # meters

# Home plate height (typical contact point)
HOME_PLATE_HEIGHT = 0.9144  # meters (3 feet - typical contact height)

# ============================================================================
# BASEBALL FIELD DIMENSIONS
# ============================================================================

# Distances in feet (converted to meters when needed)
INFIELD_RADIUS = 95.0  # feet - approximate infield radius
OUTFIELD_WARNING_TRACK = 320.0  # feet - typical warning track distance
FENCE_HEIGHT_MIN = 8.0  # feet - minimum fence height
FENCE_HEIGHT_MAX = 37.0  # feet - maximum fence height (e.g., Green Monster)

# Typical fence distances by field position
FENCE_DISTANCES = {
    'left_field': 330.0,      # feet
    'left_center': 375.0,     # feet
    'center_field': 400.0,    # feet
    'right_center': 375.0,    # feet
    'right_field': 330.0,     # feet
}

# Typical fence heights
FENCE_HEIGHTS = {
    'standard': 10.0,         # feet - most common
    'fenway_green_monster': 37.0,  # feet - famous example
}

# ============================================================================
# CONTACT QUALITY PARAMETERS
# ============================================================================

# Sweet spot contact (optimal)
SWEET_SPOT_EFFICIENCY = 1.0  # 100% energy transfer

# Off-center contact efficiency reductions
OFF_CENTER_EFFICIENCY_REDUCTION = 0.15  # 15% reduction per inch off-center

# Contact point effects on spin and angle
BELOW_CENTER_BACKSPIN_INCREASE = 200.0  # rpm per inch below center
BELOW_CENTER_ANGLE_INCREASE = 2.0       # degrees per inch below center
ABOVE_CENTER_TOPSPIN_INCREASE = 200.0   # rpm per inch above center
ABOVE_CENTER_ANGLE_DECREASE = 2.0       # degrees per inch above center

# ============================================================================
# BAT-BALL COLLISION PHYSICS (PHASE 2)
# ============================================================================

# Bat specifications (typical MLB wood bat)
BAT_MASS = 0.905  # kg (approximately 32 oz)
BAT_LENGTH = 0.864  # meters (34 inches)

# Sweet spot location (from barrel end)
# Located at the node of vibration - minimal energy loss from vibrations
SWEET_SPOT_DISTANCE_FROM_BARREL = 0.152  # meters (6 inches from barrel end)
SWEET_SPOT_WIDTH = 0.051  # meters (2 inches - effective sweet spot region)

# Coefficient of Restitution (COR) - ratio of relative velocity after/before collision
# COR varies with contact location, bat material, and ball compression
COR_SWEET_SPOT = 0.55  # Maximum COR at sweet spot (wood bat)
COR_MINIMUM = 0.35     # Minimum COR (far from sweet spot, high vibration loss)
COR_ALUMINUM_BONUS = 0.05  # Aluminum bats have slightly higher COR

# Collision efficiency factors
# Effective mass ratio affects energy transfer
# Calibrated to produce empirical ~1.2*v_bat + 0.2*v_pitch relationship
BAT_EFFECTIVE_MASS_RATIO = 0.85  # Fraction of bat mass effective at sweet spot
# This produces realistic exit velocities matching MLB data (~85% of bat mass)
# Represents the effective mass involved in the collision at the sweet spot

# Energy loss from vibrations (off sweet spot contact)
VIBRATION_LOSS_FACTOR = 0.20  # Energy loss per inch from sweet spot (20% per inch)
MAX_VIBRATION_LOSS = 0.60      # Maximum energy loss (60%)

# Contact location effects on COR
# COR decreases as you move away from sweet spot
COR_DEGRADATION_PER_INCH = 0.03  # COR reduction per inch from sweet spot

# Collision geometry effects
# The angle between bat and ball paths affects launch angle and spin
# Increased from 0.85 to 0.95 to allow power hitters to achieve HR launch angles (28-32°)
COLLISION_ANGLE_TO_LAUNCH_ANGLE_RATIO = 0.95  # How much collision angle affects launch
FRICTION_COEFFICIENT = 0.35  # Ball-bat friction (affects spin generation)

# Spin generation from collision
# Tangential friction during collision creates spin
SPIN_FROM_FRICTION_FACTOR = 40.0  # rpm per degree of collision angle
BASE_BACKSPIN_FROM_COMPRESSION = 800.0  # rpm from ball compression (always present)

# ============================================================================
# VALIDATION BENCHMARK VALUES
# ============================================================================

# Known relationship: 100 mph at 28° with 1800 rpm backspin
BENCHMARK_EXIT_VELOCITY = 100.0  # mph
BENCHMARK_LAUNCH_ANGLE = 28.0    # degrees
BENCHMARK_BACKSPIN = 1800.0      # rpm

# ============================================================================
# ADVANCED COLLISION PHYSICS CONSTANTS (Research-Based)
# ============================================================================

# Collision Efficiency (q) - Master formula parameter
# BBS = q * v_pitch + (1 + q) * v_bat
# RESTORED 2025-11-19: Increased from 0.08 to 0.12 to restore power hitting
# Previous reductions were too aggressive, suppressing realistic power output
# With typical bat speed 78 mph and pitch speed 83 mph:
# - Old q=0.08: EV = 0.08*83 + 1.08*78 = 91 mph (too low, suppressed HRs)
# - Mid q=0.12: EV = 0.12*83 + 1.12*78 = 97 mph (0 HRs per game - too low)
# - Try q=0.13: EV = 0.13*83 + 1.13*78 = 99 mph (target: 2-5 HRs/game)
# - Was q=0.14: EV = 0.14*83 + 1.14*78 = 100.5 mph (16 HRs/game - too high!)
# This provides optimal balance for realistic MLB home run rates (~2.2/game avg)
# Combined with hit_handler distance-first logic for more realistic HR distribution
COLLISION_EFFICIENCY_WOOD = 0.13        # Wood bats (maple, ash, birch) - balanced power hitting
COLLISION_EFFICIENCY_ALUMINUM = 0.11    # Aluminum bats (BBCOR regulated) - reduced from 0.24
COLLISION_EFFICIENCY_COMPOSITE = 0.12   # Composite bats (BBCOR regulated) - reduced from 0.25

# Sweet Spot Physics
SWEET_SPOT_LENGTH_INCHES = 6.0           # Length of sweet spot zone
SWEET_SPOT_CENTER_FROM_TIP = 6.0         # Distance from bat tip to sweet spot center
VIBRATIONAL_NODE_1_FROM_TIP = 5.5        # First vibrational node location
VIBRATIONAL_NODE_2_FROM_TIP = 6.5        # Second vibrational node location
CENTER_OF_PERCUSSION_FROM_TIP = 6.2      # Center of percussion location

# Energy Loss Mechanisms
VIBRATION_ENERGY_LOSS_MAX = 0.10         # Max energy lost to bat vibrations (10%)
VIBRATION_ENERGY_LOSS_RATE = 0.015       # Energy loss per inch from sweet spot
BALL_DEFORMATION_ENERGY_LOSS = 0.70      # Energy lost in ball deformation (~70%)
TRAMPOLINE_ENERGY_RECOVERY = 0.95        # Energy recovery from bat barrel flex

# Contact Offset Effects (Research-Based)
OFFSET_EFFICIENCY_DEGRADATION = 0.04     # Efficiency loss per inch of offset (reduced from 0.08)
HORIZONTAL_OFFSET_SPIN_FACTOR = 400.0    # rpm per inch of horizontal offset
VERTICAL_OFFSET_SPIN_FACTOR = 500.0      # rpm per inch of vertical offset
SPIN_INDEPENDENCE_FACTOR = 0.95          # How much bat overwrites pitch spin

# Material-Specific Properties
WOOD_ENERGY_STORAGE_RATIO = 0.02         # Wood stores only 2% of deformation energy
METAL_ENERGY_STORAGE_RATIO = 0.12        # Metal stores ~12% of deformation energy
COMPOSITE_ENERGY_STORAGE_RATIO = 0.15    # Composite stores ~15% of deformation energy

# Contact Force and Time
CONTACT_TIME_MS = 0.7                     # Contact duration in milliseconds
PEAK_FORCE_FACTOR = 2.0                  # Peak force is 2x average force
FORCE_TIME_PROFILE = 'sine_squared'      # Force follows sine-squared profile

# Bat Speed vs Pitch Speed Importance
BAT_SPEED_MULTIPLIER = 6.0               # Bat speed is 6x more important than pitch speed
PITCH_SPEED_DISTANCE_FACTOR = 1.0        # Feet added per mph of pitch speed
BAT_SPEED_DISTANCE_FACTOR = 5.0          # Feet added per mph of bat speed
BENCHMARK_DISTANCE_SEA_LEVEL = 395.0  # feet (expected result)
BENCHMARK_TOLERANCE = 10.0       # feet (acceptable error)

# Coors Field (Denver, CO)
COORS_FIELD_ALTITUDE = 5200.0    # feet
COORS_FIELD_DISTANCE_BOOST = 30.0  # feet (additional vs sea level)

# ============================================================================
# PITCHING PHYSICS (PHASE 3)
# ============================================================================

# Mound and plate specifications (MLB official)
MOUND_DISTANCE = 60.5  # feet from home plate to pitching rubber
MOUND_HEIGHT = 10.0    # inches above home plate level
MOUND_HEIGHT_FEET = MOUND_HEIGHT / 12.0  # feet

# Pitcher release point (typical for overhand delivery)
RELEASE_HEIGHT = 6.0   # feet above mound (total ~6.8 ft above plate)
RELEASE_EXTENSION = 6.0  # feet in front of rubber (stride)
# Actual release point: 60.5 - 6.0 = 54.5 ft from plate

# Strike zone dimensions
STRIKE_ZONE_WIDTH = 17.0 / 12.0  # feet (17 inches)
STRIKE_ZONE_BOTTOM = 1.5  # feet above ground (knees)
STRIKE_ZONE_TOP = 3.5     # feet above ground (letters)
STRIKE_ZONE_HEIGHT = STRIKE_ZONE_TOP - STRIKE_ZONE_BOTTOM

# Home plate dimensions
HOME_PLATE_WIDTH = STRIKE_ZONE_WIDTH  # 17 inches

# Pitch velocity ranges (mph) - from MLB Statcast data
# Source: MLB.com Statcast 2016-2023 averages
FASTBALL_4SEAM_VELOCITY_MIN = 88.0
FASTBALL_4SEAM_VELOCITY_MAX = 102.0
FASTBALL_4SEAM_VELOCITY_AVG = 93.0

FASTBALL_2SEAM_VELOCITY_MIN = 88.0
FASTBALL_2SEAM_VELOCITY_MAX = 95.0
FASTBALL_2SEAM_VELOCITY_AVG = 92.0

CUTTER_VELOCITY_MIN = 85.0
CUTTER_VELOCITY_MAX = 95.0
CUTTER_VELOCITY_AVG = 88.0

CURVEBALL_VELOCITY_MIN = 70.0
CURVEBALL_VELOCITY_MAX = 82.0
CURVEBALL_VELOCITY_AVG = 78.0

SLIDER_VELOCITY_MIN = 78.0
SLIDER_VELOCITY_MAX = 91.0
SLIDER_VELOCITY_AVG = 85.0

CHANGEUP_VELOCITY_MIN = 75.0
CHANGEUP_VELOCITY_MAX = 88.0
CHANGEUP_VELOCITY_AVG = 84.0

SPLITTER_VELOCITY_MIN = 80.0
SPLITTER_VELOCITY_MAX = 90.0
SPLITTER_VELOCITY_AVG = 85.0

KNUCKLEBALL_VELOCITY_MIN = 65.0
KNUCKLEBALL_VELOCITY_MAX = 80.0
KNUCKLEBALL_VELOCITY_AVG = 72.0

# Pitch spin ranges (rpm) - from MLB Statcast data
FASTBALL_4SEAM_SPIN_MIN = 1800.0
FASTBALL_4SEAM_SPIN_MAX = 2700.0
FASTBALL_4SEAM_SPIN_AVG = 2200.0

FASTBALL_2SEAM_SPIN_MIN = 1800.0
FASTBALL_2SEAM_SPIN_MAX = 2500.0
FASTBALL_2SEAM_SPIN_AVG = 2100.0

CUTTER_SPIN_MIN = 2000.0
CUTTER_SPIN_MAX = 2600.0
CUTTER_SPIN_AVG = 2200.0

CURVEBALL_SPIN_MIN = 2200.0
CURVEBALL_SPIN_MAX = 3200.0
CURVEBALL_SPIN_AVG = 2500.0

SLIDER_SPIN_MIN = 1800.0
SLIDER_SPIN_MAX = 2800.0
SLIDER_SPIN_AVG = 2400.0

CHANGEUP_SPIN_MIN = 1400.0
CHANGEUP_SPIN_MAX = 2100.0
CHANGEUP_SPIN_AVG = 1750.0

SPLITTER_SPIN_MIN = 1000.0
SPLITTER_SPIN_MAX = 1800.0
SPLITTER_SPIN_AVG = 1500.0

KNUCKLEBALL_SPIN_MIN = 50.0
KNUCKLEBALL_SPIN_MAX = 500.0
KNUCKLEBALL_SPIN_AVG = 200.0

# Spin efficiency values (percentage of spin that creates Magnus force)
# Source: YakkerTech/SeeMagnus 2020 MLB average data
SPIN_EFFICIENCY_4SEAM = 0.90    # 90% - very efficient backspin
SPIN_EFFICIENCY_2SEAM = 0.89    # 89% - efficient with slight tilt
SPIN_EFFICIENCY_CUTTER = 0.49   # 49% - partial gyro spin
SPIN_EFFICIENCY_CURVEBALL = 0.69  # 69% - good topspin efficiency
SPIN_EFFICIENCY_SLIDER = 0.36   # 36% - mostly gyro spin (bullet spin)
SPIN_EFFICIENCY_CHANGEUP = 0.89  # 89% - similar to fastball but lower rpm
SPIN_EFFICIENCY_SPLITTER = 0.50  # 50% - tumbling action
SPIN_EFFICIENCY_KNUCKLEBALL = 0.10  # 10% - chaotic, minimal Magnus

# Pitch break characteristics (inches of movement from straight line)
# Vertical break: positive = rises (less drop than gravity alone)
# Horizontal break: positive = arm side (RHP moves to right)
# Source: MLB Statcast typical values

FASTBALL_4SEAM_VERTICAL_BREAK_AVG = 16.0    # inches (appears to "rise")
FASTBALL_4SEAM_HORIZONTAL_BREAK_AVG = -2.0  # inches (slight arm side)

FASTBALL_2SEAM_VERTICAL_BREAK_AVG = 10.0    # inches (less rise, more sink)
FASTBALL_2SEAM_HORIZONTAL_BREAK_AVG = -8.0  # inches (arm side run)

CUTTER_VERTICAL_BREAK_AVG = 6.0       # inches (moderate drop)
CUTTER_HORIZONTAL_BREAK_AVG = 3.0     # inches (glove side cut)

CURVEBALL_VERTICAL_BREAK_AVG = -12.0  # inches (big drop)
CURVEBALL_HORIZONTAL_BREAK_AVG = 6.0  # inches (sweeping)

SLIDER_VERTICAL_BREAK_AVG = 2.0       # inches (moderate drop)
SLIDER_HORIZONTAL_BREAK_AVG = 5.0     # inches (sharp glove side)

CHANGEUP_VERTICAL_BREAK_AVG = -8.0    # inches (drops)
CHANGEUP_HORIZONTAL_BREAK_AVG = 14.0  # inches (arm side fade)

SPLITTER_VERTICAL_BREAK_AVG = -10.0   # inches (sharp late drop)
SPLITTER_HORIZONTAL_BREAK_AVG = 2.0   # inches (minimal horizontal)

KNUCKLEBALL_VERTICAL_BREAK_AVG = 0.0  # inches (unpredictable)
KNUCKLEBALL_HORIZONTAL_BREAK_AVG = 0.0  # inches (random flutter)

# ============================================================================
# PITCHER RELEASE MECHANICS
# ============================================================================

# Release extension (feet in front of rubber)
# Source: MLB Statcast extension data
RELEASE_EXTENSION_MIN = 5.0   # feet (short stride)
RELEASE_EXTENSION_AVG = 6.0   # feet (typical)
RELEASE_EXTENSION_MAX = 7.5   # feet (long stride, e.g., Tyler Glasnow)

# Perceived velocity boost from extension
# Source: Sports Illustrated analysis (1.7 mph per foot)
EXTENSION_PERCEIVED_VELOCITY_BOOST_PER_FOOT = 1.7  # mph per foot

# Arm angle effects (degrees from vertical)
# 0° = over-the-top, 45° = three-quarters, 90° = sidearm
ARM_ANGLE_OVERHAND = 0.0      # degrees (12 o'clock)
ARM_ANGLE_HIGH_3_4 = 30.0     # degrees (1 o'clock for RHP)
ARM_ANGLE_3_4 = 45.0          # degrees (typical)
ARM_ANGLE_LOW_3_4 = 60.0      # degrees
ARM_ANGLE_SIDEARM = 90.0      # degrees (3 o'clock)
ARM_ANGLE_SUBMARINE = 120.0   # degrees (below sidearm)

# ============================================================================
# PITCHER ATTRIBUTE SYSTEM
# ============================================================================

# Velocity rating scale (0-100,000)
VELOCITY_RATING_MIN = 20000      # Position player pitching
VELOCITY_RATING_AVG = 50000      # Average MLB pitcher
VELOCITY_RATING_ELITE = 80000    # Elite fastball
VELOCITY_RATING_MAX = 100000     # Aroldis Chapman, Jordan Hicks level

# Movement rating scale (0-100,000)
MOVEMENT_RATING_MIN = 20000      # Minimal break
MOVEMENT_RATING_AVG = 50000      # Average MLB break
MOVEMENT_RATING_ELITE = 80000    # Elite movement
MOVEMENT_RATING_MAX = 100000     # Exceptional break

# Command rating scale (0-100,000)
COMMAND_RATING_MIN = 20000       # Poor control
COMMAND_RATING_AVG = 50000       # Average control
COMMAND_RATING_ELITE = 80000     # Excellent command
COMMAND_RATING_MAX = 100000      # Greg Maddux level

# Deception rating scale (0-100,000)
DECEPTION_RATING_MIN = 20000     # Easy to read
DECEPTION_RATING_AVG = 50000     # Average deception
DECEPTION_RATING_ELITE = 80000   # Very deceptive
DECEPTION_RATING_MAX = 100000    # Extreme deception

# ============================================================================
# ENVIRONMENTAL EFFECTS ON PITCHES
# ============================================================================

# Altitude effect on pitch break (per 1000 ft)
# Source: Alan Nathan physics analysis, Colorado Sun article
PITCH_BREAK_REDUCTION_PER_1000_FT = 0.8  # inches per 1000 ft altitude

# Temperature effect on pitch break (per 10°F)
# Source: Command Trakker weather analysis
PITCH_BREAK_CHANGE_PER_10_DEG_F = 0.3  # inches per 10°F

# Wind effect on pitch movement
# Headwind increases Magnus effect, tailwind decreases it
WIND_MAGNUS_MULTIPLIER_PER_MPH = 0.02  # 2% per mph wind

# ============================================================================
# FIELD LAYOUT AND DIMENSIONS (REGULATION MLB)
# ============================================================================

# Base distances (feet)
BASE_PATH_LENGTH = 90.0  # feet from base to base
HOME_TO_FIRST_DISTANCE = 90.0  # feet
FIRST_TO_SECOND_DISTANCE = 90.0 * math.sqrt(2)  # feet (diagonal)
SECOND_TO_THIRD_DISTANCE = 90.0 * math.sqrt(2)  # feet (diagonal)
THIRD_TO_HOME_DISTANCE = 90.0  # feet
PITCHERS_MOUND_DISTANCE = 60.5  # feet from home plate

# Base coordinates (feet from home plate)
# Using standard right-handed coordinate system:
# X: toward right field (positive), toward left field (negative)
# Y: toward center field (positive), toward home plate (negative)
# Z: upward (positive), downward (negative)
HOME_PLATE_X = 0.0
HOME_PLATE_Y = 0.0
FIRST_BASE_X = 90.0
FIRST_BASE_Y = 0.0
SECOND_BASE_X = 0.0
SECOND_BASE_Y = 90.0
THIRD_BASE_X = -90.0
THIRD_BASE_Y = 0.0

# Foul territory dimensions (approximate)
FOUL_TERRITORY_FIRST_BASE = 50.0  # feet from first base line
FOUL_TERRITORY_THIRD_BASE = 50.0  # feet from third base line
BACKSTOP_DISTANCE = 60.0  # feet behind home plate

# Outfield wall distances (feet from home plate)
# These are approximate for a typical MLB ballpark
LEFT_FIELD_WALL_DISTANCE = 330.0  # feet down the line
LEFT_CENTER_WALL_DISTANCE = 370.0  # feet
CENTER_FIELD_WALL_DISTANCE = 400.0  # feet
RIGHT_CENTER_WALL_DISTANCE = 370.0  # feet
RIGHT_FIELD_WALL_DISTANCE = 330.0  # feet down the line
OUTFIELD_WALL_HEIGHT = 10.0  # feet (varies by ballpark)

# ============================================================================
# DEFENSIVE POSITIONING (TYPICAL MLB)
# ============================================================================

# Standard defensive positions (feet from home plate)
# Pitcher
PITCHER_X = 0.0
PITCHER_Y = 60.5  # On the mound

# Catcher
CATCHER_X = 0.0
CATCHER_Y = -2.0  # Behind home plate

# Infielders (adjusted for better coverage)
FIRST_BASEMAN_X = 75.0    # Slightly closer to the line
FIRST_BASEMAN_Y = 20.0    # Moved up slightly
SECOND_BASEMAN_X = 40.0   # Moved in and left for better gap coverage
SECOND_BASEMAN_Y = 55.0   # Moved in from 50
SHORTSTOP_X = -35.0       # Moved right slightly for better up-the-middle coverage
SHORTSTOP_Y = 55.0        # Moved in from 60
THIRD_BASEMAN_X = -75.0   # Slightly closer to the line
THIRD_BASEMAN_Y = 20.0    # Moved up slightly

# Outfielders (optimized depth and spacing)
# Positioned for optimal fly ball coverage (250-380ft range)
# Spaced at 30° from center for balanced gap coverage (~146ft gaps)
# Shallow enough to cover 270ft balls, deep enough for 350ft balls
LEFT_FIELDER_X = -135.0   # 30° left of center
LEFT_FIELDER_Y = 265.0    # Split difference: between 260 (too shallow) and 275 (too deep)
CENTER_FIELDER_X = 0.0    # Straight up the middle
CENTER_FIELDER_Y = 310.0  # Split difference: between 305 (too shallow) and 320 (too deep)
RIGHT_FIELDER_X = 135.0   # 30° right of center
RIGHT_FIELDER_Y = 265.0   # Split difference: between 260 (too shallow) and 275 (too deep)

# ============================================================================
# FIELDING ATTRIBUTES AND PHYSICS
# ============================================================================

# Sprint speed constants (feet per second)
# Based on MLB Statcast data: https://baseballsavant.mlb.com/sprint_speed_leaderboard
FIELDER_SPRINT_SPEED_MIN = 30.0    # ft/s (~20.5 mph) - slowest MLB players
FIELDER_SPRINT_SPEED_AVG = 35.0    # ft/s (~23.9 mph) - MLB average
FIELDER_SPRINT_SPEED_ELITE = 40.0  # ft/s (~27.3 mph) - elite sprinters
FIELDER_SPRINT_SPEED_MAX = 42.0    # ft/s (~28.6 mph) - absolute fastest

# Acceleration constants (feet per second squared)
# Time to reach 80% of top speed for different athlete types
FIELDER_ACCELERATION_MIN = 40.0    # ft/s² - poor acceleration
FIELDER_ACCELERATION_AVG = 60.0    # ft/s² - average MLB acceleration
FIELDER_ACCELERATION_ELITE = 80.0  # ft/s² - elite first step
FIELDER_ACCELERATION_MAX = 100.0   # ft/s² - exceptional acceleration

# Reaction time constants (seconds)
# Time from bat contact to first movement
FIELDER_REACTION_TIME_MIN = 0.0    # s - perfect anticipation/jump
FIELDER_REACTION_TIME_AVG = 0.10   # s - typical MLB fielder
FIELDER_REACTION_TIME_POOR = 0.20  # s - poor jump/late read
FIELDER_REACTION_TIME_MAX = 0.30   # s - very poor reaction

# Throwing velocity constants (mph)
# Position-specific throwing speeds
INFIELDER_THROW_VELOCITY_MIN = 70.0   # mph
INFIELDER_THROW_VELOCITY_AVG = 82.0   # mph
INFIELDER_THROW_VELOCITY_ELITE = 90.0 # mph
INFIELDER_THROW_VELOCITY_MAX = 95.0   # mph

OUTFIELDER_THROW_VELOCITY_MIN = 75.0   # mph
OUTFIELDER_THROW_VELOCITY_AVG = 85.0   # mph
OUTFIELDER_THROW_VELOCITY_ELITE = 95.0 # mph
OUTFIELDER_THROW_VELOCITY_MAX = 105.0  # mph

# Transfer time constants (seconds)
# Time from catch/pickup to release
INFIELDER_TRANSFER_TIME_MIN = 0.3     # s - elite double play turn
INFIELDER_TRANSFER_TIME_AVG = 0.5     # s - average infielder
INFIELDER_TRANSFER_TIME_POOR = 0.8    # s - slow hands
INFIELDER_TRANSFER_TIME_MAX = 1.2     # s - very slow

OUTFIELDER_TRANSFER_TIME_MIN = 0.6    # s - quick release
OUTFIELDER_TRANSFER_TIME_AVG = 0.9    # s - average outfielder
OUTFIELDER_TRANSFER_TIME_POOR = 1.3   # s - slow to set and throw
OUTFIELDER_TRANSFER_TIME_MAX = 1.8    # s - very slow

# Throwing accuracy constants (degrees standard deviation)
# Accuracy of throw direction
THROWING_ACCURACY_ELITE = 0.3      # ±0.3° - pinpoint accuracy
THROWING_ACCURACY_AVG = 2.0        # ±2.0° - average accuracy
THROWING_ACCURACY_POOR = 4.0       # ±4.0° - inconsistent
THROWING_ACCURACY_TERRIBLE = 8.0   # ±8.0° - wild throws

# Fielding range factors
# Multipliers for effective fielding range based on skill
FIELDING_RANGE_ELITE = 1.25    # 25% larger effective range
FIELDING_RANGE_AVG = 1.00      # Standard range
FIELDING_RANGE_POOR = 0.80     # 20% smaller effective range

# ============================================================================
# RESEARCH-BASED FIELDING PHYSICS ENHANCEMENTS
# ============================================================================

# Speed-Dependent Drag Coefficients (Research Finding)
# Dramatic drag reduction at high speeds due to boundary layer transition
DRAG_COEFFICIENT_LOW_SPEED = 0.52     # Below 31 m/s (~70 mph) - laminar flow
DRAG_COEFFICIENT_HIGH_SPEED = 0.22     # Above 42 m/s (~94 mph) - turbulent flow
DRAG_TRANSITION_SPEED_LOW = 31.0       # m/s - start of transition
DRAG_TRANSITION_SPEED_HIGH = 42.0      # m/s - end of transition

# Statcast-Calibrated Fielder Attributes
# Based on actual MLB Statcast data from research
FIELDER_SPRINT_SPEED_STATCAST_MIN = 26.5    # ft/s - Slow 1B archetype
FIELDER_SPRINT_SPEED_STATCAST_AVG = 28.5    # ft/s - Average MLB SS
FIELDER_SPRINT_SPEED_STATCAST_ELITE = 30.0  # ft/s - Elite Gold Glove CF
FIELDER_SPRINT_SPEED_STATCAST_MAX = 31.0    # ft/s - Absolute fastest

# Acceleration Time to Max Speed (Adjusted for fielding plays)
# Original Statcast times (3.5-4.5s) were for full sprint speed over 90+ feet
# For fielding plays of 15-60ft, fielders reach near-max speed much faster
# These times represent reaching 80% of max sprint speed
# NERFED 2025-11-19: Increased to reduce superhuman fielding coverage
FIELDER_ACCELERATION_TIME_ELITE = 1.0   # seconds - Elite burst (was 3.50)
FIELDER_ACCELERATION_TIME_AVG = 1.6     # seconds - Average MLB (was 1.3, originally 3.80)
FIELDER_ACCELERATION_TIME_POOR = 1.7    # seconds - Poor burst (was 4.20)
FIELDER_ACCELERATION_TIME_MAX = 2.0     # seconds - Very poor (was 4.50)

# First Step Time (Adjusted for fielding plays)
# These represent the delay between ball contact and first movement
# Statcast values (0.30-0.55s) are for initial read + first step
# For active fielding positions, reaction is faster
# NERFED 2025-11-19: Increased to reduce superhuman reaction times
FIELDER_FIRST_STEP_TIME_ELITE = 0.20   # s - Elite reaction (was 0.30)
FIELDER_FIRST_STEP_TIME_AVG = 0.35     # s - Average MLB fielder (was 0.25, originally 0.37)
FIELDER_FIRST_STEP_TIME_POOR = 0.40    # s - Poor reaction (was 0.35, originally 0.45)
FIELDER_FIRST_STEP_TIME_MAX = 0.50     # s - Very poor reaction (was 0.45, originally 0.55)

# Route Efficiency (Statcast metric)
ROUTE_EFFICIENCY_ELITE = 98.0     # % - Elite route running
ROUTE_EFFICIENCY_AVG = 94.7       # % - Average MLB
ROUTE_EFFICIENCY_POOR = 92.0      # % - Poor route running
ROUTE_EFFICIENCY_MIN = 88.0       # % - Very poor

# Directional Movement Penalties (Research-Based)
# Fielders are effectively 1 ft/s slower running backward
FORWARD_MOVEMENT_PENALTY = 1.00    # 100% speed (0° ± 45°)
LATERAL_MOVEMENT_PENALTY = 0.97     # 97% speed (90° ± 45°) - elite lateral movement
BACKWARD_MOVEMENT_PENALTY = 0.93    # 93% speed (180° ± 45°) - elite backpedaling

# Catch Probability Model Constants (Statcast-Based)
CATCH_PROB_BASE = 0.95              # Base catch probability for easy plays
CATCH_PROB_DISTANCE_PENALTY = 0.10  # Penalty per 10 feet of distance
CATCH_PROB_TIME_BONUS = 0.20        # Bonus per second of opportunity time
CATCH_PROB_BACKWARD_PENALTY = 0.15  # Additional penalty for backward movement
CATCH_PROB_MIN = 0.05               # Minimum catch probability

# Optical Acceleration Cancellation Constants
OAC_CONTROL_GAIN = 2.0              # Control gain for OAC algorithm
OAC_ANGULAR_THRESHOLD = 0.001       # Threshold for optical acceleration (rad/s²)
OAC_MAX_ACCELERATION = 8.0          # Maximum fielder acceleration (ft/s²)

# Advanced AI Pursuit Strategy Constants
TRAJECTORY_PREDICTION_SAMPLES = 20   # Number of future trajectory points to analyze
PURSUIT_PREDICTION_TIME = 0.5        # Seconds ahead to predict ball position
INTERCEPT_CONVERGENCE_TOLERANCE = 2.0 # Distance tolerance for intercept calculation (ft)
DYNAMIC_POSITIONING_THRESHOLD = 1.0   # Minimum time to initiate repositioning (s)

# Fielder Intelligence Constants
ANTICIPATION_BONUS_TIME = 0.3         # Time bonus for good anticipation (s)
ROUTE_OPTIMIZATION_SAMPLES = 10       # Number of route options to evaluate
PURSUIT_ANGLE_PREFERENCE = 15.0       # Preferred angle for ball approach (degrees)
MAX_PURSUIT_DISTANCE = 120.0          # Maximum distance to attempt pursuit (ft)

# Ball Trajectory Intelligence
MINIMUM_HANG_TIME_FOR_PURSUIT = 1.5   # Minimum flight time to enable advanced pursuit (s)
TRAJECTORY_UPDATE_FREQUENCY = 0.1     # How often to recalculate pursuit target (s)
VELOCITY_PREDICTION_WEIGHT = 0.7      # Weight for velocity-based vs position-based prediction

# Positioning Strategy Constants
OUTFIELD_DEPTH_ADJUSTMENT_FAST = 20.0 # Depth adjustment for fast runners (ft)
OUTFIELD_DEPTH_ADJUSTMENT_POWER = 15.0 # Depth adjustment for power hitters (ft)
DEFENSIVE_SHIFT_THRESHOLD = 0.6       # Pull tendency threshold for shifting
GAP_COVERAGE_PRIORITY = 1.2           # Multiplier for gap coverage importance

# Defensive Hierarchy for "Call Off" Logic
# When multiple fielders can reach a ball, priority is given based on position:
# - Center fielder has best view and range (highest priority)
# - Corner outfielders next (better angles than infielders)
# - Infielders lowest priority on fly balls (but high on ground balls)
#
# Priority values: Higher = takes precedence on contested balls
FIELDING_HIERARCHY = {
    'center_field': 100,      # CF has authority on all fly balls
    'left_field': 80,         # Corner OFs defer to CF
    'right_field': 80,
    'shortstop': 60,          # Middle infielders can make plays
    'second_base': 60,
    'third_base': 50,         # Corner infielders
    'first_base': 50,
    'pitcher': 40,            # Pitcher lowest priority
    'catcher': 30             # Catcher rarely involved in fly balls
}

# Distance threshold for applying hierarchy (feet)
# If fielders are within this distance of each other's arrival times,
# use hierarchy to break ties
FIELDING_HIERARCHY_DISTANCE_THRESHOLD = 20.0  # feet
FIELDING_HIERARCHY_TIME_THRESHOLD = 0.3       # seconds

# ============================================================================
# BASERUNNING ATTRIBUTES AND PHYSICS
# ============================================================================

# Runner sprint speed constants (feet per second)
# Based on MLB Statcast data
RUNNER_SPRINT_SPEED_MIN = 22.0     # ft/s (~15 mph) - slowest
RUNNER_SPRINT_SPEED_AVG = 27.0     # ft/s (~18.4 mph) - MLB average
RUNNER_SPRINT_SPEED_ELITE = 30.0   # ft/s (~20.5 mph) - elite speed
RUNNER_SPRINT_SPEED_MAX = 32.0     # ft/s (~21.8 mph) - absolute fastest

# Runner acceleration constants (feet per second squared)
RUNNER_ACCELERATION_MIN = 10.0     # ft/s² - poor burst
RUNNER_ACCELERATION_AVG = 14.0     # ft/s² - average acceleration
RUNNER_ACCELERATION_ELITE = 18.0   # ft/s² - explosive first step
RUNNER_ACCELERATION_MAX = 22.0     # ft/s² - exceptional burst

# Base-to-base times (seconds) for validation
# These emerge from physics but used for calibration
HOME_TO_FIRST_TIME_MIN = 3.7       # s - elite speedsters
HOME_TO_FIRST_TIME_AVG = 4.3       # s - MLB average
HOME_TO_FIRST_TIME_SLOW = 5.2      # s - slow runners
HOME_TO_FIRST_TIME_MAX = 6.0       # s - very slow

# Baserunning reaction time (seconds)
# Time from bat contact to start of advance
RUNNER_REACTION_TIME_MIN = 0.05    # s - excellent jump
RUNNER_REACTION_TIME_AVG = 0.15    # s - average reaction
RUNNER_REACTION_TIME_POOR = 0.25   # s - poor jump
RUNNER_REACTION_TIME_MAX = 0.40    # s - very poor reaction

# Base rounding physics
# Turn efficiency around bases
TURN_RADIUS_MIN = 8.0              # ft - tight turns (speed loss)
TURN_RADIUS_AVG = 12.0             # ft - average base rounding
TURN_RADIUS_ELITE = 15.0           # ft - wide, efficient turns

# Speed retention during turns (fraction of straight-line speed)
TURN_SPEED_RETENTION_POOR = 0.75   # 25% speed loss in turn
TURN_SPEED_RETENTION_AVG = 0.85    # 15% speed loss in turn
TURN_SPEED_RETENTION_ELITE = 0.92  # 8% speed loss in turn

# Sliding mechanics
SLIDE_DECELERATION_RATE = 20.0     # ft/s² - friction deceleration
SLIDE_DISTANCE_MIN = 8.0           # ft - short slide
SLIDE_DISTANCE_AVG = 12.0          # ft - typical slide
SLIDE_DISTANCE_MAX = 18.0          # ft - long slide

# Lead-off distances (feet)
LEADOFF_FIRST_BASE_MIN = 8.0       # ft - conservative lead
LEADOFF_FIRST_BASE_AVG = 12.0      # ft - standard lead
LEADOFF_FIRST_BASE_MAX = 18.0      # ft - aggressive lead

LEADOFF_SECOND_BASE_MIN = 12.0     # ft
LEADOFF_SECOND_BASE_AVG = 18.0     # ft
LEADOFF_SECOND_BASE_MAX = 25.0     # ft

LEADOFF_THIRD_BASE_MIN = 15.0      # ft
LEADOFF_THIRD_BASE_AVG = 20.0      # ft
LEADOFF_THIRD_BASE_MAX = 28.0      # ft

# ============================================================================
# ATTRIBUTE RATING SCALES (0-100,000) FOR FIELDING/BASERUNNING
# ============================================================================

# Fielding attribute scales
FIELDING_SPEED_RATING_MIN = 20000     # 23 ft/s sprint speed
FIELDING_SPEED_RATING_AVG = 50000     # 27 ft/s sprint speed
FIELDING_SPEED_RATING_ELITE = 80000   # 30 ft/s sprint speed
FIELDING_SPEED_RATING_MAX = 100000    # 32 ft/s sprint speed

FIELDING_REACTION_RATING_MIN = 20000   # 0.5s reaction time
FIELDING_REACTION_RATING_AVG = 50000   # 0.15s reaction time
FIELDING_REACTION_RATING_ELITE = 80000 # 0.05s reaction time
FIELDING_REACTION_RATING_MAX = 100000  # 0.0s reaction time

FIELDING_ARM_RATING_MIN = 20000       # 70 mph (inf), 75 mph (of)
FIELDING_ARM_RATING_AVG = 50000       # 82 mph (inf), 85 mph (of)
FIELDING_ARM_RATING_ELITE = 80000     # 90 mph (inf), 95 mph (of)
FIELDING_ARM_RATING_MAX = 100000      # 95 mph (inf), 105 mph (of)

FIELDING_ACCURACY_RATING_MIN = 20000   # 8° standard deviation
FIELDING_ACCURACY_RATING_AVG = 50000   # 2° standard deviation
FIELDING_ACCURACY_RATING_ELITE = 80000 # 1° standard deviation
FIELDING_ACCURACY_RATING_MAX = 100000  # 0.5° standard deviation

# Baserunning attribute scales
BASERUNNING_SPEED_RATING_MIN = 20000   # 22 ft/s sprint speed
BASERUNNING_SPEED_RATING_AVG = 50000   # 27 ft/s sprint speed
BASERUNNING_SPEED_RATING_ELITE = 80000 # 30 ft/s sprint speed
BASERUNNING_SPEED_RATING_MAX = 100000  # 32 ft/s sprint speed

BASERUNNING_ACCELERATION_RATING_MIN = 20000    # 10 ft/s² acceleration
BASERUNNING_ACCELERATION_RATING_AVG = 50000    # 14 ft/s² acceleration
BASERUNNING_ACCELERATION_RATING_ELITE = 80000  # 18 ft/s² acceleration
BASERUNNING_ACCELERATION_RATING_MAX = 100000   # 22 ft/s² acceleration

BASERUNNING_BASERUNNING_RATING_MIN = 20000     # Poor base running IQ
BASERUNNING_BASERUNNING_RATING_AVG = 50000     # Average base running
BASERUNNING_BASERUNNING_RATING_ELITE = 80000   # Elite base running IQ
BASERUNNING_BASERUNNING_RATING_MAX = 100000    # Perfect base running

# ============================================================================
# GROUND BALL PHYSICS
# ============================================================================

# Coefficient of restitution for ground bounces
# Ratio of relative velocity after/before bounce
# Source: Physics of Baseball (Adair), turf studies
GROUND_BALL_COR_GRASS = 0.45       # Natural grass (moderate bounce)
GROUND_BALL_COR_TURF = 0.55        # Artificial turf (higher bounce)
GROUND_BALL_COR_DIRT = 0.40        # Dirt infield (lower bounce)
GROUND_BALL_COR_DEFAULT = 0.45     # Default to grass

# Coefficient of rolling friction
# Source: Sports science studies on baseball surfaces
ROLLING_FRICTION_GRASS = 0.08      # Natural grass rolling friction
ROLLING_FRICTION_TURF = 0.06       # Artificial turf (smoother)
ROLLING_FRICTION_DIRT = 0.10       # Dirt infield (rougher)
ROLLING_FRICTION_DEFAULT = 0.08    # Default to grass

# Ground ball deceleration from air resistance (ft/s²)
# Additional to rolling friction
GROUND_BALL_AIR_RESISTANCE = 2.0   # ft/s² (minor effect)

# Bounce height threshold (feet)
# Below this height, ball is considered rolling (no more bounces)
BOUNCE_HEIGHT_THRESHOLD = 0.5      # ft - below this, transitions to pure rolling

# Minimum bounce count before transition to rolling
# High backspin balls can bounce multiple times before rolling
MIN_BOUNCES_BEFORE_ROLLING = 2

# Maximum number of bounces to simulate
MAX_GROUND_BALL_BOUNCES = 10

# Spin decay rate on ground contact
# Fraction of spin retained after each bounce
SPIN_RETENTION_PER_BOUNCE = 0.70   # 30% spin loss per bounce

# Launch angle threshold for ground balls vs line drives
# Below this angle with low peak height = ground ball
GROUND_BALL_LAUNCH_ANGLE_MAX = 15.0  # degrees

# ============================================================================
# PLAY OUTCOME TIMING TOLERANCES
# ============================================================================

# Close play timing tolerances (seconds)
# "Tie goes to runner" implementation
CLOSE_PLAY_TOLERANCE = 0.08        # s - within 0.08s considered tie (increased from 0.05)
SAFE_RUNNER_BIAS = 0.05            # s - slight bias toward runner (increased from 0.02 to allow more infield hits)

# Tag play timing
TAG_APPLICATION_TIME = 0.10        # s - time to apply tag after catch
TAG_AVOIDANCE_SUCCESS_RATE = 0.15  # 15% chance to avoid tag if close
