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
        ZONE_DISCERNMENT: float = 50000
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

    def get_bat_speed_mph(self) -> float:
        """
        Convert BAT_SPEED rating to barrel speed (mph).

        Anchors:
        - 0: 45 mph (weak/youth)
        - 50k: 63 mph (average MLB)
        - 85k: 73 mph (elite MLB)
        - 100k: 85 mph (superhuman)
        """
        return piecewise_logistic_map(
            self.BAT_SPEED,
            human_min=45.0,
            human_cap=73.0,
            super_cap=85.0
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

        Anchors:
        - 0: 40 mm error (poor)
        - 50k: 13 mm error (average)
        - 85k: 7 mm error (elite)
        - 100k: 2 mm error (superhuman)
        """
        return piecewise_logistic_map_inverse(
            self.BARREL_ACCURACY,
            human_min=7.0,
            human_cap=40.0,
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
        - 0: 0.60 s (very slow)
        - 50k: 0.23 s (average)
        - 85k: 0.14 s (elite)
        - 100k: 0.08 s (superhuman)
        """
        return piecewise_logistic_map_inverse(
            self.REACTION_TIME,
            human_min=0.14,
            human_cap=0.60,
            super_cap=0.08
        )

    def get_acceleration_fps2(self) -> float:
        """
        Acceleration (ft/s²).

        Anchors:
        - 0: 8 ft/s² (slow)
        - 50k: 12 ft/s² (average)
        - 85k: 15 ft/s² (elite)
        - 100k: 20 ft/s² (superhuman)
        """
        return piecewise_logistic_map(
            self.ACCELERATION,
            human_min=8.0,
            human_cap=15.0,
            super_cap=20.0
        )

    def get_top_sprint_speed_fps(self) -> float:
        """
        Top sprint speed (ft/s).

        Anchors:
        - 0: 20 ft/s (slow)
        - 50k: 26.5 ft/s (average ~18 mph)
        - 85k: 29.5 ft/s (elite ~20 mph)
        - 100k: 36 ft/s (superhuman ~25 mph)
        """
        return piecewise_logistic_map(
            self.TOP_SPRINT_SPEED,
            human_min=20.0,
            human_cap=29.5,
            super_cap=36.0
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
        - 0: 0.85 s (slow)
        - 50k: 0.45 s (average)
        - 85k: 0.30 s (elite)
        - 100k: 0.18 s (superhuman)
        """
        return piecewise_logistic_map_inverse(
            self.TRANSFER_TIME,
            human_min=0.30,
            human_cap=0.85,
            super_cap=0.18
        )

    def get_arm_strength_mph(self) -> float:
        """
        Throw velocity (mph).

        Anchors:
        - 0: 60 mph (weak)
        - 50k: 82 mph (average)
        - 85k: 92 mph (elite)
        - 100k: 105 mph (superhuman)
        """
        return piecewise_logistic_map(
            self.ARM_STRENGTH,
            human_min=60.0,
            human_cap=92.0,
            super_cap=105.0
        )


# =============================================================================
# HELPER FUNCTIONS FOR LEGACY COMPATIBILITY
# =============================================================================

def create_power_hitter(quality: str = "average") -> HitterAttributes:
    """
    Create a power hitter with high BAT_SPEED and high ATTACK_ANGLE.

    This naturally produces home runs through physics, no profiles needed.
    """
    quality_ranges = {
        "poor": (25000, 45000),
        "average": (45000, 65000),
        "good": (60000, 80000),
        "elite": (75000, 95000)
    }

    min_r, max_r = quality_ranges.get(quality, (45000, 65000))

    # Power hitters: HIGH bat speed + HIGH attack angle
    return HitterAttributes(
        BAT_SPEED=np.random.randint(max_r, 95000),  # Elite bat speed
        ATTACK_ANGLE_CONTROL=np.random.randint(max_r, 90000),  # High launch angle
        ATTACK_ANGLE_VARIANCE=np.random.randint(min_r, max_r),
        BARREL_ACCURACY=np.random.randint(min_r + 5000, max_r + 10000),
        TIMING_PRECISION=np.random.randint(min_r, max_r),
        PITCH_PLANE_MATCH=np.random.randint(min_r, max_r),
        SWING_DECISION_LATENCY=np.random.randint(min_r, max_r),
        ZONE_DISCERNMENT=np.random.randint(min_r, max_r)
    )


def create_balanced_hitter(quality: str = "average") -> HitterAttributes:
    """Create a balanced contact hitter."""
    quality_ranges = {
        "poor": (25000, 45000),
        "average": (45000, 65000),
        "good": (60000, 80000),
        "elite": (75000, 95000)
    }

    min_r, max_r = quality_ranges.get(quality, (45000, 65000))

    # Balanced: moderate bat speed + moderate attack angle + HIGH barrel accuracy
    return HitterAttributes(
        BAT_SPEED=np.random.randint(min_r, max_r + 5000),
        ATTACK_ANGLE_CONTROL=np.random.randint(min_r - 5000, min_r + 10000),  # More neutral
        ATTACK_ANGLE_VARIANCE=np.random.randint(min_r + 5000, max_r + 5000),  # Consistent
        BARREL_ACCURACY=np.random.randint(max_r, 85000),  # HIGH contact skill
        TIMING_PRECISION=np.random.randint(min_r + 5000, max_r + 10000),
        PITCH_PLANE_MATCH=np.random.randint(min_r, max_r),
        SWING_DECISION_LATENCY=np.random.randint(min_r, max_r),
        ZONE_DISCERNMENT=np.random.randint(min_r + 5000, max_r + 10000)
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

    # Ground ball: LOW attack angle (downward or flat swing)
    return HitterAttributes(
        BAT_SPEED=np.random.randint(min_r, max_r),
        ATTACK_ANGLE_CONTROL=np.random.randint(15000, 35000),  # LOW/flat swing
        ATTACK_ANGLE_VARIANCE=np.random.randint(min_r, max_r),
        BARREL_ACCURACY=np.random.randint(min_r, max_r),
        TIMING_PRECISION=np.random.randint(min_r + 5000, max_r + 5000),
        PITCH_PLANE_MATCH=np.random.randint(min_r, max_r),
        SWING_DECISION_LATENCY=np.random.randint(min_r, max_r),
        ZONE_DISCERNMENT=np.random.randint(min_r, max_r)
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
        - 0: 70 mph (very slow)
        - 50k: 91 mph (average MLB)
        - 85k: 98 mph (elite MLB)
        - 100k: 108 mph (superhuman)
        """
        return piecewise_logistic_map(
            self.RAW_VELOCITY_CAP,
            human_min=70.0,
            human_cap=98.0,
            super_cap=108.0
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

        Lower rating = worse command (more scatter)

        Anchors:
        - 0: 8.0 in (poor command)
        - 50k: 3.5 in (average)
        - 85k: 1.8 in (elite)
        - 100k: 0.8 in (pinpoint)
        """
        return piecewise_logistic_map_inverse(
            self.COMMAND,
            human_min=1.8,
            human_cap=8.0,
            super_cap=0.8
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


# =============================================================================
# HELPER FUNCTIONS FOR PITCHER CREATION
# =============================================================================

def create_starter_pitcher(quality: str = "average") -> PitcherAttributes:
    """
    Create a starting pitcher with balanced attributes and good stamina.
    """
    quality_ranges = {
        "poor": (25000, 45000),
        "average": (45000, 65000),
        "good": (60000, 80000),
        "elite": (75000, 95000)
    }

    min_r, max_r = quality_ranges.get(quality, (45000, 65000))

    # Starters: balanced with GOOD stamina
    return PitcherAttributes(
        RAW_VELOCITY_CAP=np.random.randint(min_r, max_r + 5000),
        SPIN_RATE_CAP=np.random.randint(min_r, max_r + 5000),
        SPIN_EFFICIENCY=np.random.randint(min_r, max_r),
        COMMAND=np.random.randint(min_r, max_r + 5000),  # Starters have better command
        STAMINA=np.random.randint(max_r, 85000),  # HIGH stamina for starters
    )


def create_reliever_pitcher(quality: str = "average") -> PitcherAttributes:
    """
    Create a relief pitcher with high velocity/spin but lower stamina.
    """
    quality_ranges = {
        "poor": (25000, 45000),
        "average": (45000, 65000),
        "good": (60000, 80000),
        "elite": (75000, 95000)
    }

    min_r, max_r = quality_ranges.get(quality, (45000, 65000))

    # Relievers: HIGH velocity/spin, LOW stamina
    return PitcherAttributes(
        RAW_VELOCITY_CAP=np.random.randint(max_r, 90000),  # Higher velo
        SPIN_RATE_CAP=np.random.randint(max_r, 85000),     # Higher spin
        COMMAND=np.random.randint(min_r, max_r),
        STAMINA=np.random.randint(20000, 45000),  # LOW stamina (short relief)
    )
