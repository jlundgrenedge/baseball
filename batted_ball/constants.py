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
COLLISION_ANGLE_TO_LAUNCH_ANGLE_RATIO = 0.85  # How much collision angle affects launch
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

# Pitch velocity ranges (mph)
FASTBALL_VELOCITY_MIN = 88.0
FASTBALL_VELOCITY_MAX = 102.0
FASTBALL_VELOCITY_AVG = 93.0

CURVEBALL_VELOCITY_MIN = 72.0
CURVEBALL_VELOCITY_MAX = 82.0
CURVEBALL_VELOCITY_AVG = 77.0

SLIDER_VELOCITY_MIN = 82.0
SLIDER_VELOCITY_MAX = 90.0
SLIDER_VELOCITY_AVG = 85.0

CHANGEUP_VELOCITY_MIN = 78.0
CHANGEUP_VELOCITY_MAX = 88.0
CHANGEUP_VELOCITY_AVG = 83.0

# Pitch spin ranges (rpm) - from MLB Statcast data
FASTBALL_SPIN_MIN = 1800.0
FASTBALL_SPIN_MAX = 2700.0
FASTBALL_SPIN_AVG = 2200.0

CURVEBALL_SPIN_MIN = 2200.0
CURVEBALL_SPIN_MAX = 3200.0
CURVEBALL_SPIN_AVG = 2500.0

SLIDER_SPIN_MIN = 2200.0
SLIDER_SPIN_MAX = 2800.0
SLIDER_SPIN_AVG = 2400.0

CHANGEUP_SPIN_MIN = 1500.0
CHANGEUP_SPIN_MAX = 2000.0
CHANGEUP_SPIN_AVG = 1750.0

# Pitch break characteristics (inches of movement from straight line)
# Vertical break: positive = rises (less drop than gravity alone)
# Horizontal break: positive = arm side (RHP moves to right)

FASTBALL_VERTICAL_BREAK_AVG = 16.0    # inches (appears to "rise")
FASTBALL_HORIZONTAL_BREAK_AVG = -8.0  # inches (slight glove side run)

CURVEBALL_VERTICAL_BREAK_AVG = -12.0  # inches (big drop)
CURVEBALL_HORIZONTAL_BREAK_AVG = 6.0  # inches (sweeping)

SLIDER_VERTICAL_BREAK_AVG = 2.0       # inches (moderate drop)
SLIDER_HORIZONTAL_BREAK_AVG = 5.0     # inches (sharp glove side)

CHANGEUP_VERTICAL_BREAK_AVG = -8.0    # inches (drops)
CHANGEUP_HORIZONTAL_BREAK_AVG = 14.0  # inches (arm side fade)
