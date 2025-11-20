"""
Physics-First Attribute System (0-100,000 scale)

Unified continuous attribute system where all player capabilities are rated on
0-100,000 scale and mapped to physical units via piecewise logistic functions.

No hard-coded "profiles" - all outcomes emerge from physics simulation.

Author: Claude Code
"""

import numpy as np
from typing import Dict, Tuple


# =============================================================================
# CORE MAPPING FUNCTIONS
# =============================================================================

def sigmoid(x: float) -> float:
    """Standard logistic sigmoid: 1 / (1 + e^-x)"""
    return 1.0 / (1.0 + np.exp(-x))


def piecewise_logistic_map(
    rating: float,
    human_min: float,
    human_cap: float,
    super_cap: float,
    H: float = 85000.0,
    k: float = 8.0,
    k2: float = 5.0
) -> float:
    """
    Map 0-100,000 rating to physical units using piecewise logistic.

    Below H (human cap): spreads ratings smoothly across normal human range
    Above H: allows superhuman headroom with gentler scaling

    Parameters
    ----------
    rating : float
        Attribute rating (0-100,000)
    human_min : float
        Physical value at rating=0 (minimum human capability)
    human_cap : float
        Physical value at rating=H (elite human)
    super_cap : float
        Physical value at rating=100,000 (superhuman)
    H : float
        Human capability threshold (default 85,000)
    k : float
        Steepness for human range (higher = more spread)
    k2 : float
        Steepness for superhuman range (gentler)

    Returns
    -------
    float
        Mapped physical value
    """
    rating = np.clip(rating, 0, 100000)

    if rating <= H:
        # Human range: smooth logistic spread
        x = (rating / H) * k - k/2  # Center sigmoid
        return human_min + (human_cap - human_min) * sigmoid(x)
    else:
        # Superhuman range: gentler scaling
        x = ((rating - H) / (100000 - H)) * k2 - k2/2
        return human_cap + (super_cap - human_cap) * sigmoid(x)


def piecewise_logistic_map_inverse(
    rating: float,
    human_min: float,
    human_cap: float,
    super_cap: float,
    H: float = 85000.0,
    k: float = 8.0,
    k2: float = 5.0
) -> float:
    """
    Inverse mapping for "smaller is better" attributes (reaction time, error).

    Maps 0 → human_cap (worst), H → human_min (best human), 100k → super_cap (best super)
    """
    rating = np.clip(rating, 0, 100000)

    if rating <= H:
        x = (rating / H) * k - k/2
        return human_cap - (human_cap - human_min) * sigmoid(x)
    else:
        x = ((rating - H) / (100000 - H)) * k2 - k2/2
        return human_min - (human_min - super_cap) * sigmoid(x)


# =============================================================================
# HITTING ATTRIBUTES
# =============================================================================

class HitterAttributes:
    """
    Physics-based hitting attributes (0-100,000 scale).

    Maps to bat kinematics, contact point control, and collision geometry
    that deterministically produce EV/LA/spin via physics simulation.
    """

    def __init__(
        self,
        BAT_SPEED: float = 50000,
        ATTACK_ANGLE_CONTROL: float = 50000,
        ATTACK_ANGLE_VARIANCE: float = 50000,
        BARREL_ACCURACY: float = 50000,
        TIMING_PRECISION: float = 50000,
        PITCH_PLANE_MATCH: float = 50000,
        IMPACT_SPIN_GAIN: float = 50000,
        LAUNCH_OFFSET_CONTROL: float = 50000,
        SWING_DECISION_LATENCY: float = 50000,
        ZONE_DISCERNMENT: float = 50000,
        SPRAY_TENDENCY: float = 50000
    ):
        """Initialize hitter attributes (default: league average = 50,000)"""
        self.BAT_SPEED = np.clip(BAT_SPEED, 0, 100000)
        self.ATTACK_ANGLE_CONTROL = np.clip(ATTACK_ANGLE_CONTROL, 0, 100000)
        self.ATTACK_ANGLE_VARIANCE = np.clip(ATTACK_ANGLE_VARIANCE, 0, 100000)
        self.BARREL_ACCURACY = np.clip(BARREL_ACCURACY, 0, 100000)
        self.TIMING_PRECISION = np.clip(TIMING_PRECISION, 0, 100000)
        self.PITCH_PLANE_MATCH = np.clip(PITCH_PLANE_MATCH, 0, 100000)
        self.IMPACT_SPIN_GAIN = np.clip(IMPACT_SPIN_GAIN, 0, 100000)
        self.LAUNCH_OFFSET_CONTROL = np.clip(LAUNCH_OFFSET_CONTROL, 0, 100000)
        self.SWING_DECISION_LATENCY = np.clip(SWING_DECISION_LATENCY, 0, 100000)
        self.ZONE_DISCERNMENT = np.clip(ZONE_DISCERNMENT, 0, 100000)
        self.SPRAY_TENDENCY = np.clip(SPRAY_TENDENCY, 0, 100000)

    def get_bat_speed_mph(self) -> float:
        """
        Convert BAT_SPEED rating to barrel speed (mph).

        Anchors (recalibrated 2025-11-19 to fix low exit velocities):
        - 0: 60 mph (minimum MLB capability - raised from 52 mph)
        - 50k: 75 mph (average MLB - raised from 70 mph for realistic exit velos)
        - 85k: 85 mph (elite MLB - top 10%, raised from 80 mph)
        - 100k: 95 mph (superhuman - raised from 92 mph)

        Rationale: Previous mapping produced exit velocities of 60-85 mph with q=0.05-0.12,
        far below MLB average of 88 mph. New mapping produces 85-95 mph exit velocities
        with same collision efficiencies, enabling realistic power hitting and home runs.
        """
        return piecewise_logistic_map(
            self.BAT_SPEED,
            human_min=60.0,  # Raised from 52.0
            human_cap=85.0,  # Raised from 80.0
            super_cap=95.0   # Raised from 92.0
        )

    def get_attack_angle_mean_deg(self) -> float:
        """
        Convert ATTACK_ANGLE_CONTROL to mean swing plane angle (degrees).

        Anchors:
        - 0: -5° (extreme downward chop)
        - 50k: 12° (average MLB)
        - 85k: 28° (elite uppercut / power hitter)
        - 100k: 40° (extreme uppercut)
        """
        return piecewise_logistic_map(
            self.ATTACK_ANGLE_CONTROL,
            human_min=-5.0,
            human_cap=28.0,
            super_cap=40.0
        )

    def get_attack_angle_variance_deg(self) -> float:
        """
        Convert ATTACK_ANGLE_VARIANCE to swing plane consistency (deg RMS).

        Lower rating = more variance (less consistent)

        Anchors:
        - 0: 8° variance (very inconsistent)
        - 50k: 3° variance (average)
        - 85k: 1° variance (elite consistency)
        - 100k: 0.3° variance (robotic)
        """
        return piecewise_logistic_map_inverse(
            self.ATTACK_ANGLE_VARIANCE,
            human_min=1.0,
            human_cap=8.0,
            super_cap=0.3
        )

    def get_barrel_accuracy_mm(self) -> float:
        """
        Convert BARREL_ACCURACY to radial contact-point error (mm RMS).

        Lower = closer to sweet spot consistently

        Anchors (recalibrated 2025-11-19 to increase solid contact rate):
        - 0: 35 mm error (poor - reduced from 40mm)
        - 50k: 10 mm error (average - reduced from 13mm for more barrels)
        - 85k: 5 mm error (elite - reduced from 7mm)
        - 100k: 2 mm error (superhuman)

        Rationale: Previous mapping produced only ~5% solid contact rate.
        MLB "barrel" rate is ~8-10% of balls in play. Reducing error by ~20-30%
        should increase solid contact to realistic ~10-12% rate.
        """
        return piecewise_logistic_map_inverse(
            self.BARREL_ACCURACY,
            human_min=5.0,   # Reduced from 7.0
            human_cap=35.0,  # Reduced from 40.0
            super_cap=2.0
        )

    def get_timing_precision_ms(self) -> float:
        """
        Convert TIMING_PRECISION to temporal error at commit (ms RMS).

        Affects pull/oppo spray via slight lead/lag

        Anchors:
        - 0: 15 ms error (poor timing)
        - 50k: 6 ms error (average)
        - 85k: 3 ms error (elite)
        - 100k: 1 ms error (superhuman)
        """
        return piecewise_logistic_map_inverse(
            self.TIMING_PRECISION,
            human_min=3.0,
            human_cap=15.0,
            super_cap=1.0
        )

    def get_pitch_plane_match_factor(self) -> float:
        """
        Ability to adjust swing to pitch descent angle (0-1 scale).

        Higher = better matching, less mishits from plane mismatch

        Anchors:
        - 0: 0.50 (poor adjustment)
        - 50k: 0.75 (average)
        - 85k: 0.92 (elite)
        - 100k: 0.98 (superhuman)
        """
        return piecewise_logistic_map(
            self.PITCH_PLANE_MATCH,
            human_min=0.50,
            human_cap=0.92,
            super_cap=0.98
        )

    def get_swing_decision_latency_ms(self) -> float:
        """
        Time from pitch recognition to swing commit (ms).

        Lower = faster decisions

        Anchors:
        - 0: 200 ms (slow/bad)
        - 50k: 130 ms (average)
        - 85k: 100 ms (elite)
        - 100k: 75 ms (superhuman)
        """
        return piecewise_logistic_map_inverse(
            self.SWING_DECISION_LATENCY,
            human_min=100.0,
            human_cap=200.0,
            super_cap=75.0
        )

    def get_zone_discernment_factor(self) -> float:
        """
        Ability to identify pitch location/type (0-1 scale).

        Higher = better recognition, fewer chases

        Anchors:
        - 0: 0.40 (poor recognition)
        - 50k: 0.70 (average)
        - 85k: 0.88 (elite)
        - 100k: 0.96 (superhuman)
        """
        return piecewise_logistic_map(
            self.ZONE_DISCERNMENT,
            human_min=0.40,
            human_cap=0.88,
            super_cap=0.96
        )

    def get_spray_tendency_deg(self) -> float:
        """
        Convert SPRAY_TENDENCY to mean spray angle bias (degrees).

        Determines whether a hitter pulls the ball, hits to all fields,
        or goes opposite field. The spray angle is relative to center field:
        - Negative = opposite field (left field for RHH, right field for LHH)
        - 0 = center field (neutral, all fields)
        - Positive = pull field (right field for RHH, left field for LHH)

        Anchors:
        - 0: -15° (extreme opposite field hitter)
        - 50k: 0° (neutral spray, uses all fields)
        - 85k: +15° (pull-heavy hitter)
        - 100k: +25° (extreme dead-pull hitter)

        Note: The actual spray angle will have variance (~22° std dev) added
        to this mean, creating realistic spray patterns.
        """
        return piecewise_logistic_map(
            self.SPRAY_TENDENCY,
            human_min=-15.0,
            human_cap=15.0,
            super_cap=25.0
        )

    def get_impact_spin_gain_factor(self) -> float:
        """
        Convert IMPACT_SPIN_GAIN to spin imparted on contact (0-1 scale).

        Higher = more spin on contact (affects backspin/sidespin)

        Anchors:
        - 0: 0.50 (low spin generation)
        - 50k: 0.75 (average)
        - 85k: 0.90 (elite spin)
        - 100k: 0.98 (superhuman)
        """
        return piecewise_logistic_map(
            self.IMPACT_SPIN_GAIN,
            human_min=0.50,
            human_cap=0.90,
            super_cap=0.98
        )

    def get_launch_offset_control_factor(self) -> float:
        """
        Convert LAUNCH_OFFSET_CONTROL to launch angle offset control (0-1 scale).

        Higher = better control over launch angle adjustments

        Anchors:
        - 0: 0.40 (poor control)
        - 50k: 0.70 (average)
        - 85k: 0.88 (elite)
        - 100k: 0.96 (superhuman)
        """
        return piecewise_logistic_map(
            self.LAUNCH_OFFSET_CONTROL,
            human_min=0.40,
            human_cap=0.88,
            super_cap=0.96
        )


# =============================================================================
# FIELDING ATTRIBUTES
# =============================================================================

class FielderAttributes:
    """Physics-based fielding attributes for kinematic races."""

    def __init__(
        self,
        REACTION_TIME: float = 50000,
        ACCELERATION: float = 50000,
        TOP_SPRINT_SPEED: float = 50000,
        ROUTE_EFFICIENCY: float = 50000,
        AGILITY: float = 50000,
        FIELDING_SECURE: float = 50000,
        TRANSFER_TIME: float = 50000,
        ARM_STRENGTH: float = 50000,
        ARM_ACCURACY: float = 50000
    ):
        """Initialize fielder attributes (default: league average = 50,000)"""
        self.REACTION_TIME = np.clip(REACTION_TIME, 0, 100000)
        self.ACCELERATION = np.clip(ACCELERATION, 0, 100000)
        self.TOP_SPRINT_SPEED = np.clip(TOP_SPRINT_SPEED, 0, 100000)
        self.ROUTE_EFFICIENCY = np.clip(ROUTE_EFFICIENCY, 0, 100000)
        self.AGILITY = np.clip(AGILITY, 0, 100000)
        self.FIELDING_SECURE = np.clip(FIELDING_SECURE, 0, 100000)
        self.TRANSFER_TIME = np.clip(TRANSFER_TIME, 0, 100000)
        self.ARM_STRENGTH = np.clip(ARM_STRENGTH, 0, 100000)
        self.ARM_ACCURACY = np.clip(ARM_ACCURACY, 0, 100000)

    def get_reaction_time_s(self) -> float:
        """
        First movement delay (seconds).

        Anchors:
        - 0: 0.30 s (very slow)
        - 50k: 0.10 s (average MLB)
        - 85k: 0.05 s (elite)
        - 100k: 0.00 s (perfect anticipation)

        Note: Previous values (0.23s average) were too slow, causing fielders
        to react 0.13s late on every play, contributing to excessive hits.
        """
        return piecewise_logistic_map_inverse(
            self.REACTION_TIME,
            human_min=0.05,
            human_cap=0.30,
            super_cap=0.00
        )

    def get_acceleration_fps2(self) -> float:
        """
        Acceleration (ft/s²).

        Anchors:
        - 0: 35 ft/s² (slow)
        - 50k: 60 ft/s² (average MLB)
        - 85k: 80 ft/s² (elite burst)
        - 100k: 100 ft/s² (exceptional)

        Note: Previous values (12 ft/s² average) were 5x too low, causing
        fielders to take far too long to reach running speed, resulting in
        late arrivals and excessive hits.
        """
        return piecewise_logistic_map(
            self.ACCELERATION,
            human_min=35.0,
            human_cap=80.0,
            super_cap=100.0
        )

    def get_top_sprint_speed_fps(self) -> float:
        """
        Top sprint speed (ft/s) - calibrated to MLB Statcast data.

        Anchors:
        - 0: 24 ft/s (slow ~16.4 mph)
        - 50k: 27 ft/s (average ~18.4 mph) - matches MLB average
        - 85k: 30 ft/s (elite ~20.5 mph) - elite outfielders
        - 100k: 32 ft/s (fastest ~21.8 mph) - absolute MLB max

        Note: Values calibrated to MLB Statcast sprint speed data.
        - MLB average: ~27 ft/s
        - Elite outfielder: ~30 ft/s
        - Fastest: ~31 ft/s

        Previous values (37.0 ft/s elite) were superhuman, causing 2-3s early margins.
        Current values match realistic MLB fielding capabilities.
        """
        return piecewise_logistic_map(
            self.TOP_SPRINT_SPEED,
            human_min=24.0,
            human_cap=30.0,
            super_cap=32.0
        )

    def get_route_efficiency_pct(self) -> float:
        """
        Path efficiency as fraction (0-1).

        1.0 = perfect geodesic

        Anchors:
        - 0: 0.70 (poor routes)
        - 50k: 0.88 (average)
        - 85k: 0.96 (elite)
        - 100k: 0.99 (nearly perfect)
        """
        return piecewise_logistic_map(
            self.ROUTE_EFFICIENCY,
            human_min=0.70,
            human_cap=0.96,
            super_cap=0.99
        )

    def get_transfer_time_s(self) -> float:
        """
        Glove-to-throw latency (seconds).

        Anchors:
        - 0: 1.20 s (slow)
        - 50k: 0.75 s (average) - INCREASED from 0.45s to slow down unrealistic double plays
        - 85k: 0.50 s (elite)
        - 100k: 0.30 s (superhuman)

        Real-world double play pivot and release takes significant time.
        Previous values (0.45s average) resulted in 2+ second margins on force plays.
        """
        return piecewise_logistic_map_inverse(
            self.TRANSFER_TIME,
            human_min=0.50,
            human_cap=1.20,
            super_cap=0.30
        )

    def get_arm_strength_mph(self) -> float:
        """
        Throw velocity (mph).

        Anchors:
        - 0: 60 mph (weak)
        - 50k: 75 mph (average) - DECREASED from 82 mph for realistic game-speed throws
        - 85k: 88 mph (elite)
        - 100k: 100 mph (superhuman)

        Game-speed infield throws are rarely max effort. Most routine plays use 75-80 mph.
        Elite defenders can hit 88-92 mph on crucial plays.
        Previous 82 mph average resulted in unrealistically fast double play execution.
        """
        return piecewise_logistic_map(
            self.ARM_STRENGTH,
            human_min=60.0,
            human_cap=88.0,
            super_cap=100.0
        )

    def get_agility_factor(self) -> float:
        """
        Change-of-direction ability (0-1 scale).

        Higher = better deceleration and direction changes

        Anchors:
        - 0: 0.50 (poor agility)
        - 50k: 0.75 (average)
        - 85k: 0.90 (elite)
        - 100k: 0.98 (superhuman)
        """
        return piecewise_logistic_map(
            self.AGILITY,
            human_min=0.50,
            human_cap=0.90,
            super_cap=0.98
        )

    def get_fielding_secure_prob(self) -> float:
        """
        Base catch success probability (0-1 scale).

        Probability of securing ball when in position

        TUNED: Reduced from previous values (0.60/0.85/0.96/0.99) to increase offensive production
        More fielding errors = more hits = closer to MLB offensive averages

        Anchors:
        - 0: 0.50 (poor hands)
        - 50k: 0.75 (average)
        - 85k: 0.88 (elite)
        - 100k: 0.93 (superhuman)
        """
        return piecewise_logistic_map(
            self.FIELDING_SECURE,
            human_min=0.50,
            human_cap=0.88,
            super_cap=0.93
        )

    def get_arm_accuracy_sigma_ft(self) -> float:
        """
        Throw accuracy dispersion (feet, standard deviation).

        Lower rating = worse accuracy (more scatter)

        Anchors:
        - 0: 12 ft (poor accuracy)
        - 50k: 5 ft (average)
        - 85k: 2 ft (elite)
        - 100k: 0.5 ft (pinpoint)
        """
        return piecewise_logistic_map_inverse(
            self.ARM_ACCURACY,
            human_min=2.0,
            human_cap=12.0,
            super_cap=0.5
        )

    def get_acceleration_time_s(self) -> float:
        """
        Time to reach top speed from stationary (seconds).

        Derived from acceleration rating

        Anchors:
        - 0: 4.5 s (slow)
        - 50k: 3.0 s (average)
        - 85k: 2.2 s (elite)
        - 100k: 1.5 s (superhuman)
        """
        # Use top speed and acceleration to compute time
        v_max = self.get_top_sprint_speed_fps()
        a = self.get_acceleration_fps2()
        return v_max / a  # t = v/a for constant acceleration


# =============================================================================
# HELPER FUNCTIONS FOR LEGACY COMPATIBILITY
# =============================================================================

def create_power_hitter(quality: str = "average") -> HitterAttributes:
    """
    Create a power hitter with high BAT_SPEED and MODERATE-ELEVATED attack angle.

    FIX (2025-11-19): Reduced attack angle from 65k-80k to 48k-62k to achieve realistic
    ground ball rates (~43% GB). The high attack angle was creating avg launch angles of
    ~25° instead of MLB average ~12-13°. With 15° natural variance, 48k-62k (10-16° mean)
    produces realistic GB/LD/FB distribution while still enabling home runs via high bat speed.

    MLB averages: ~88-89 mph exit velo, ~12-13° launch angle, ~43% ground balls
    Target: 2-3% HR rate on contact via combination of bat speed + occasional high launch angles
    """
    quality_ranges = {
        "poor": (25000, 45000),
        "average": (45000, 65000),
        "good": (60000, 80000),
        "elite": (75000, 95000)
    }

    min_r, max_r = quality_ranges.get(quality, (45000, 65000))

    # Power hitters: ELITE bat speed + MODERATE-ELEVATED attack angle
    # Bat speed: 88k-98k → 75-80 mph bat speed → 95-105 mph exit velocity (realistic MLB power)
    # Attack angle: 48k-62k → mean of 10-16° (realistic MLB average)
    # Combined with 15° natural variance, produces realistic distribution:
    #   - ~43% ground balls (< 10°)
    #   - ~24% line drives (10-25°)
    #   - ~33% fly balls (> 25°)
    # Home runs come from high bat speed producing 95-105 mph EV at occasional high launch angles
    bat_speed_min = max(88000, min_r + 33000)  # Minimum 88k for power
    bat_speed_max = min(98000, bat_speed_min + 10000)

    # RECALIBRATED (2025-11-19): Increased attack angle to enable more home runs
    # 42k-58k → 8-14° mean, which with 15° variance creates realistic launch angle distribution
    # With higher bat speeds (88k-98k) and better collision efficiency, this produces:
    # ~38-42% GB, ~22-26% LD, ~32-40% FB (MLB realistic with power hitter bias)
    # Home runs come from combination of high bat speed + elevated launch angles (20-35°)
    attack_angle_min = max(42000, min_r - 3000)  # Raised from 32k
    attack_angle_max = min(58000, attack_angle_min + 16000)  # Raised from 45k, up to 58k
    
    # Ensure valid ranges (min < max)
    if bat_speed_min >= bat_speed_max:
        bat_speed_max = bat_speed_min + 5000
    if attack_angle_min >= attack_angle_max:
        attack_angle_max = attack_angle_min + 5000
    
    # Power hitters tend to pull the ball
    # NOTE: Physics has left field positive, so NEGATIVE spray = pull right for RHH
    # Range: 15k-40k → -15° to -5° strong pull tendency (right field for RHH)
    spray_min = max(15000, min_r - 35000)
    spray_max = min(40000, spray_min + 25000)
    if spray_min >= spray_max:
        spray_max = spray_min + 10000

    return HitterAttributes(
        BAT_SPEED=np.random.randint(bat_speed_min, bat_speed_max),  # Elite bat speed
        ATTACK_ANGLE_CONTROL=np.random.randint(attack_angle_min, attack_angle_max),  # BOOSTED for HRs
        ATTACK_ANGLE_VARIANCE=np.random.randint(min_r, max_r),
        BARREL_ACCURACY=np.random.randint(min_r + 5000, max_r + 10000),
        TIMING_PRECISION=np.random.randint(min_r, max_r),
        PITCH_PLANE_MATCH=np.random.randint(min_r, max_r),
        SWING_DECISION_LATENCY=np.random.randint(min_r, max_r),
        ZONE_DISCERNMENT=np.random.randint(min_r, max_r),
        SPRAY_TENDENCY=np.random.randint(spray_min, spray_max)  # Pull tendency
    )


def create_balanced_hitter(quality: str = "average") -> HitterAttributes:
    """
    Create a balanced contact hitter with MODERATE attack angle.

    With 15° variance + pitch adjustments, we want MEAN ~5-10° for balanced hitters.
    This produces realistic distribution: good mix of ground balls, line drives, fly balls.
    """
    quality_ranges = {
        "poor": (25000, 45000),
        "average": (45000, 65000),
        "good": (60000, 80000),
        "elite": (75000, 95000)
    }

    min_r, max_r = quality_ranges.get(quality, (45000, 65000))

    # Balanced: moderate bat speed + MODERATE attack angle
    # RECALIBRATED (2025-11-19): Attack angle: ~38k-52k → mean of ~6-12°
    # Combined with 15° variance + pitch adjustments, produces realistic GB/LD/FB mix
    # With improved bat speeds and collision efficiency, enables occasional home runs
    attack_angle_min = max(38000, min_r - 7000)  # Raised from 27k to 38k
    attack_angle_max = min(52000, attack_angle_min + 14000)  # Raised from 39k to 52k
    
    # Ensure valid range
    if attack_angle_min >= attack_angle_max:
        attack_angle_max = attack_angle_min + 10000
    
    # For barrel accuracy: ensure valid range
    barrel_min = min(max_r, 75000)
    barrel_max = min(85000, barrel_min + 12000)
    
    # Ensure barrel range is valid
    if barrel_min >= barrel_max:
        barrel_max = barrel_min + 5000

    # Balanced hitters use all fields (wide spray distribution)
    # Range: 25k-75k → -14° to +12° (wide left field to right field)
    # This creates realistic all-fields spray pattern
    spray_min = max(20000, min_r - 30000)
    spray_max = min(75000, max_r + 15000)
    if spray_min >= spray_max:
        spray_max = spray_min + 20000

    return HitterAttributes(
        BAT_SPEED=np.random.randint(min_r + 8000, max_r + 13000),  # +8k boost for realistic EV (85-92 mph)
        ATTACK_ANGLE_CONTROL=np.random.randint(attack_angle_min, attack_angle_max),  # Moderate launch angle
        ATTACK_ANGLE_VARIANCE=np.random.randint(min_r + 5000, max_r + 5000),  # Consistent
        BARREL_ACCURACY=np.random.randint(barrel_min, barrel_max),  # HIGH contact skill
        TIMING_PRECISION=np.random.randint(min_r + 5000, max_r + 10000),
        PITCH_PLANE_MATCH=np.random.randint(min_r, max_r),
        SWING_DECISION_LATENCY=np.random.randint(min_r, max_r),
        ZONE_DISCERNMENT=np.random.randint(min_r + 5000, max_r + 10000),
        SPRAY_TENDENCY=np.random.randint(spray_min, spray_max)  # All fields
    )


def create_groundball_hitter(quality: str = "average") -> HitterAttributes:
    """Create a ground ball hitter (low attack angle)."""
    quality_ranges = {
        "poor": (25000, 45000),
        "average": (45000, 65000),
        "good": (60000, 80000),
        "elite": (75000, 95000)
    }

    min_r, max_r = quality_ranges.get(quality, (45000, 65000))

    # Ground ball hitters tend to pull slightly to moderately
    # NOTE: Physics has left field positive, so NEGATIVE spray = pull right for RHH
    # Range: 25k-50k → -14° to 0° moderate pull tendency
    spray_min = max(20000, min_r - 25000)
    spray_max = min(50000, spray_min + 30000)
    if spray_min >= spray_max:
        spray_max = spray_min + 10000

    # Ground ball: VERY LOW attack angle (downward or flat swing)
    # FIX (2025-11-19): Reduced from 15k-35k to 10k-30k for more ground balls
    return HitterAttributes(
        BAT_SPEED=np.random.randint(min_r + 8000, max_r + 8000),  # +8k boost for realistic EV
        ATTACK_ANGLE_CONTROL=np.random.randint(10000, 30000),  # VERY LOW/flat swing for GB
        ATTACK_ANGLE_VARIANCE=np.random.randint(min_r, max_r),
        BARREL_ACCURACY=np.random.randint(min_r, max_r),
        TIMING_PRECISION=np.random.randint(min_r + 5000, max_r + 5000),
        PITCH_PLANE_MATCH=np.random.randint(min_r, max_r),
        SWING_DECISION_LATENCY=np.random.randint(min_r, max_r),
        ZONE_DISCERNMENT=np.random.randint(min_r, max_r),
        SPRAY_TENDENCY=np.random.randint(spray_min, spray_max)  # Slight pull
    )


# =============================================================================
# PITCHING ATTRIBUTES
# =============================================================================

class PitcherAttributes:
    """
    Physics-based pitching attributes (0-100,000 scale).

    Maps to pitch velocity, spin rate/axis, release point, and command
    that deterministically produce pitch trajectories via physics.
    """

    def __init__(
        self,
        RAW_VELOCITY_CAP: float = 50000,
        SPIN_RATE_CAP: float = 50000,
        SPIN_EFFICIENCY: float = 50000,
        SPIN_AXIS_CONTROL: float = 50000,
        RELEASE_EXTENSION: float = 50000,
        ARM_SLOT: float = 50000,
        RELEASE_HEIGHT: float = 50000,
        COMMAND: float = 50000,
        CONTROL: float = 50000,
        TUNNELING: float = 50000,
        DECEPTION: float = 50000,
        STAMINA: float = 50000,
        FATIGUE_RESISTANCE: float = 50000
    ):
        """Initialize pitcher attributes (default: league average = 50,000)"""
        self.RAW_VELOCITY_CAP = np.clip(RAW_VELOCITY_CAP, 0, 100000)
        self.SPIN_RATE_CAP = np.clip(SPIN_RATE_CAP, 0, 100000)
        self.SPIN_EFFICIENCY = np.clip(SPIN_EFFICIENCY, 0, 100000)
        self.SPIN_AXIS_CONTROL = np.clip(SPIN_AXIS_CONTROL, 0, 100000)
        self.RELEASE_EXTENSION = np.clip(RELEASE_EXTENSION, 0, 100000)
        self.ARM_SLOT = np.clip(ARM_SLOT, 0, 100000)
        self.RELEASE_HEIGHT = np.clip(RELEASE_HEIGHT, 0, 100000)
        self.COMMAND = np.clip(COMMAND, 0, 100000)
        self.CONTROL = np.clip(CONTROL, 0, 100000)
        self.TUNNELING = np.clip(TUNNELING, 0, 100000)
        self.DECEPTION = np.clip(DECEPTION, 0, 100000)
        self.STAMINA = np.clip(STAMINA, 0, 100000)
        self.FATIGUE_RESISTANCE = np.clip(FATIGUE_RESISTANCE, 0, 100000)

    def get_raw_velocity_mph(self) -> float:
        """
        Convert RAW_VELOCITY_CAP to fastball velocity (mph).

        Anchors:
        - 0: 76 mph (minimum human)
        - 50k: 91 mph (average MLB)
        - 85k: 98 mph (elite MLB)
        - 100k: 109 mph (superhuman)
        """
        return piecewise_logistic_map(
            self.RAW_VELOCITY_CAP,
            human_min=76.0,
            human_cap=98.4,
            super_cap=109.0
        )

    def get_spin_rate_rpm(self) -> float:
        """
        Convert SPIN_RATE_CAP to spin rate (rpm) for 4-seam fastball.

        Anchors:
        - 0: 1600 rpm (low spin)
        - 50k: 2250 rpm (average MLB)
        - 85k: 2700 rpm (elite MLB)
        - 100k: 3400 rpm (superhuman)
        """
        return piecewise_logistic_map(
            self.SPIN_RATE_CAP,
            human_min=1600.0,
            human_cap=2700.0,
            super_cap=3400.0
        )

    def get_spin_efficiency_pct(self) -> float:
        """
        Convert SPIN_EFFICIENCY to percentage (0-100).

        Anchors:
        - 0: 70% (poor efficiency)
        - 50k: 88% (average)
        - 85k: 96% (elite)
        - 100k: 99% (nearly perfect)
        """
        return piecewise_logistic_map(
            self.SPIN_EFFICIENCY,
            human_min=70.0,
            human_cap=96.0,
            super_cap=99.0
        )

    def get_command_sigma_inches(self) -> float:
        """
        Convert COMMAND to target dispersion (inches, standard deviation).

        RESCALED 2025-11-19 to match MLB Statcast reality (1.0-2.5 ft RMS error).

        Previous mapping was 10× too accurate (3.5" sigma → 5" RMS vs MLB's 18-24" RMS).
        New mapping calibrated to Statcast command data:

        Lower rating = worse command (more scatter)

        Anchors (4.5× larger for MLB realism):
        - 0: 24.0 in (poor command, ~34" RMS = 2.8 ft) - wild pitcher
        - 50k: 16.0 in (average, ~23" RMS = 1.9 ft) - typical MLB starter
        - 85k: 9.5 in (elite, ~13" RMS = 1.1 ft) - Maddux/Glavine level
        - 100k: 5.0 in (pinpoint, ~7" RMS = 0.6 ft) - superhuman

        Note: RMS = sigma × √2 for 2D normal distribution (horizontal + vertical)

        Sources: MLB Statcast command metrics, Baseball Prospectus pitch location data
        """
        return piecewise_logistic_map_inverse(
            self.COMMAND,
            human_min=9.5,     # Was 1.8 (elite), now MLB realistic
            human_cap=24.0,    # Was 8.0 (poor), now MLB realistic
            super_cap=5.0      # Was 0.8 (pinpoint), now MLB realistic
        )

    def get_stamina_pitches(self) -> float:
        """
        Convert STAMINA to effective pitch count before fatigue.

        Anchors:
        - 0: 40 pitches (poor stamina)
        - 50k: 90 pitches (average starter)
        - 85k: 110 pitches (workhorse)
        - 100k: 135 pitches (superhuman)
        """
        return piecewise_logistic_map(
            self.STAMINA,
            human_min=40.0,
            human_cap=110.0,
            super_cap=135.0
        )

    def get_control_zone_bias(self) -> float:
        """
        Convert CONTROL to strike zone targeting bias (0-1 scale).

        NEW 2025-11-19: Maps CONTROL attribute to physical parameter.

        CONTROL represents ability to throw strikes (zone targeting tendency),
        distinct from COMMAND which represents precision (hit your spots).

        Higher control = more likely to target strikes vs intentional balls
        This directly affects walk rate:
        - Elite control (85k): 5-6% BB rate (targets strikes 75% of the time)
        - Average control (50k): 8-9% BB rate (targets strikes 65% of the time)
        - Poor control (20k): 12-15% BB rate (targets strikes 50% of the time)

        Anchors:
        - 0: 0.50 (poor control, 50% strike intentions)
        - 50k: 0.65 (average, 65% strike intentions)
        - 85k: 0.75 (elite, 75% strike intentions)
        - 100k: 0.85 (pinpoint, 85% strike intentions)

        Returns
        -------
        float
            Probability of targeting strike zone vs ball (0.5-0.85)

        Sources: MLB Statcast zone rates, FanGraphs BB% correlations
        """
        return piecewise_logistic_map(
            self.CONTROL,
            human_min=0.50,
            human_cap=0.75,
            super_cap=0.85
        )


# =============================================================================
# HELPER FUNCTIONS FOR FIELDER CREATION
# =============================================================================

def create_elite_fielder(quality: str = "average") -> FielderAttributes:
    """
    Create an elite defensive player (center fielders, shortstops).

    Emphasizes: speed, range, quick reactions
    """
    quality_ranges = {
        "poor": (25000, 45000),
        "average": (45000, 65000),
        "good": (60000, 80000),
        "elite": (75000, 95000)
    }

    min_r, max_r = quality_ranges.get(quality, (45000, 65000))

    # Elite fielders: HIGH speed, reaction, route efficiency
    return FielderAttributes(
        REACTION_TIME=np.random.randint(max_r, 90000),      # Elite reactions
        ACCELERATION=np.random.randint(max_r, 85000),       # Fast acceleration
        TOP_SPRINT_SPEED=np.random.randint(max_r, 90000),   # Elite speed
        ROUTE_EFFICIENCY=np.random.randint(max_r, 88000),   # Good routes
        AGILITY=np.random.randint(max_r, 85000),            # Good agility
        FIELDING_SECURE=np.random.randint(max_r, 85000),    # Sure hands
        TRANSFER_TIME=np.random.randint(max_r, 85000),      # Quick transfer
        ARM_STRENGTH=np.random.randint(min_r, max_r + 10000),  # Arm varies
        ARM_ACCURACY=np.random.randint(min_r + 5000, max_r + 5000)
    )


def create_average_fielder(quality: str = "average") -> FielderAttributes:
    """
    Create an average defensive player (corner outfielders, 2B/3B).

    Balanced attributes - boosted for competitive gameplay
    """
    quality_ranges = {
        "poor": (25000, 45000),
        "average": (48000, 62000),  # Boosted from 45k-65k
        "good": (60000, 80000),
        "elite": (75000, 95000)
    }

    min_r, max_r = quality_ranges.get(quality, (48000, 62000))

    # Average fielders: boost speed/reaction/hands for competitive defense
    return FielderAttributes(
        REACTION_TIME=np.random.randint(min_r + 2000, max_r + 8000),  # Faster reactions
        ACCELERATION=np.random.randint(min_r + 2000, max_r + 8000),   # Better acceleration
        TOP_SPRINT_SPEED=np.random.randint(min_r + 2000, max_r + 8000),  # Faster speed
        ROUTE_EFFICIENCY=np.random.randint(min_r + 2000, max_r + 5000),  # Better routes
        AGILITY=np.random.randint(min_r, max_r + 3000),
        FIELDING_SECURE=np.random.randint(min_r + 8000, max_r + 12000),  # CRITICAL: better hands
        TRANSFER_TIME=np.random.randint(min_r + 2000, max_r + 5000),  # Faster transfer
        ARM_STRENGTH=np.random.randint(min_r, max_r + 5000),
        ARM_ACCURACY=np.random.randint(min_r, max_r + 3000)
    )


def create_slow_fielder(quality: str = "average") -> FielderAttributes:
    """
    Create a slower defensive player (1B, DH types).

    Lower speed/range, but decent hands
    """
    quality_ranges = {
        "poor": (25000, 45000),
        "average": (45000, 65000),
        "good": (60000, 80000),
        "elite": (75000, 95000)
    }

    min_r, max_r = quality_ranges.get(quality, (45000, 65000))

    # Slow fielders: LOW speed/acceleration, decent hands
    return FielderAttributes(
        REACTION_TIME=np.random.randint(min_r - 10000, min_r + 5000),  # Slower reactions
        ACCELERATION=np.random.randint(min_r - 10000, min_r + 5000),   # Poor acceleration
        TOP_SPRINT_SPEED=np.random.randint(min_r - 15000, min_r),      # Low speed
        ROUTE_EFFICIENCY=np.random.randint(min_r - 5000, min_r + 5000),
        AGILITY=np.random.randint(min_r - 10000, min_r),               # Poor agility
        FIELDING_SECURE=np.random.randint(min_r, max_r),               # Decent hands
        TRANSFER_TIME=np.random.randint(min_r, max_r),
        ARM_STRENGTH=np.random.randint(min_r - 5000, min_r + 5000),    # Weaker arm
        ARM_ACCURACY=np.random.randint(min_r, max_r)
    )


def create_power_arm_fielder(quality: str = "average") -> FielderAttributes:
    """
    Create a defensive player with elite throwing (right fielders, catchers).

    Emphasizes: arm strength and accuracy
    """
    quality_ranges = {
        "poor": (25000, 45000),
        "average": (45000, 65000),
        "good": (60000, 80000),
        "elite": (75000, 95000)
    }

    min_r, max_r = quality_ranges.get(quality, (45000, 65000))

    # Power arm: HIGH arm strength + accuracy
    return FielderAttributes(
        REACTION_TIME=np.random.randint(min_r, max_r + 5000),
        ACCELERATION=np.random.randint(min_r, max_r + 5000),
        TOP_SPRINT_SPEED=np.random.randint(min_r, max_r + 5000),
        ROUTE_EFFICIENCY=np.random.randint(min_r, max_r),
        AGILITY=np.random.randint(min_r, max_r),
        FIELDING_SECURE=np.random.randint(min_r + 5000, max_r + 5000),
        TRANSFER_TIME=np.random.randint(max_r, 85000),          # Quick transfer
        ARM_STRENGTH=np.random.randint(max_r + 5000, 92000),    # ELITE arm
        ARM_ACCURACY=np.random.randint(max_r, 85000)            # Good accuracy
    )


# =============================================================================
# HELPER FUNCTIONS FOR PITCHER CREATION
# =============================================================================

def create_starter_pitcher(quality: str = "average") -> PitcherAttributes:
    """
    Create a starting pitcher with balanced attributes and good stamina.

    Velocity targets (per get_raw_velocity_mph mapping: 50k=91mph, 85k=98mph):
    - poor: 88-91 mph (48k-55k range) - Soft-tossing starter
    - average: 91-94 mph (55k-65k range) - MLB average starter
    - good: 93-96 mph (63k-73k range) - Above average starter
    - elite: 95-99 mph (72k-88k range) - Ace level starter
    """
    quality_ranges = {
        "poor": (48000, 55000),      # 88-91 mph starters (was 85-90)
        "average": (55000, 65000),   # 91-94 mph starters (was 50-60k)
        "good": (63000, 73000),      # 93-96 mph starters (was 58-68k)
        "elite": (72000, 88000)      # 95-99 mph starters (was 70-88k)
    }

    min_r, max_r = quality_ranges.get(quality, (55000, 65000))

    # Starters: balanced with GOOD stamina
    # Add +3000 variance to velocity for some randomness
    # For stamina: ensure we have valid range (min_stamina < max_stamina)
    stamina_min = min(max_r, 75000)  # Cap at 75k to ensure valid range
    stamina_max = min(85000, stamina_min + 15000)  # Add range, cap at 85k
    
    return PitcherAttributes(
        RAW_VELOCITY_CAP=np.random.randint(min_r, max_r + 3000),
        SPIN_RATE_CAP=np.random.randint(min_r, max_r + 3000),
        SPIN_EFFICIENCY=np.random.randint(min_r, max_r),
        COMMAND=np.random.randint(min_r, max_r + 3000),  # Starters have better command
        STAMINA=np.random.randint(stamina_min, stamina_max),  # HIGH stamina for starters
    )


def create_reliever_pitcher(quality: str = "average") -> PitcherAttributes:
    """
    Create a relief pitcher with high velocity/spin but lower stamina.

    Relievers typically throw 1-3 mph harder than starters.
    Velocity targets:
    - poor: 89-93 mph (50k-60k range) - Soft-tossing reliever
    - average: 93-97 mph (62k-78k range) - Average MLB reliever
    - good: 95-98 mph (72k-85k range) - Good setup man
    - elite: 97-102 mph (80k-92k range) - Elite closer
    """
    quality_ranges = {
        "poor": (50000, 60000),      # 89-93 mph relievers (was 87-92)
        "average": (62000, 78000),   # 93-97 mph relievers (was 57-75k)
        "good": (72000, 85000),      # 95-98 mph relievers (was 70-82k)
        "elite": (80000, 92000)      # 97-102 mph closers (was 78-92k)
    }

    min_r, max_r = quality_ranges.get(quality, (62000, 78000))

    # Relievers: HIGH velocity/spin, LOW stamina
    return PitcherAttributes(
        RAW_VELOCITY_CAP=np.random.randint(max_r - 3000, max_r + 5000),  # Higher velo than starters
        SPIN_RATE_CAP=np.random.randint(max_r - 5000, max_r + 3000),     # Higher spin
        COMMAND=np.random.randint(min_r, max_r),
        STAMINA=np.random.randint(20000, 45000),  # LOW stamina (short relief)
    )
