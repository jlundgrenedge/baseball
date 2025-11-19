"""
Simulation Metrics and Debug Output System

Provides comprehensive tracking and analysis of simulation internals for:
- Physics debugging
- Model tuning and calibration
- Validation against MLB Statcast data
- Understanding sim behavior and realism

This module implements the complete metrics system requested for OOTP-style transparency.
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple
from enum import Enum
import numpy as np


class DebugLevel(Enum):
    """Debug output verbosity levels"""
    OFF = 0          # No debug output
    BASIC = 1        # Key decisions and outcomes only
    DETAILED = 2     # Full per-pitch/play tracking
    EXHAUSTIVE = 3   # All internal calculations and probabilities


# ============================================================================
# A. PITCH-LEVEL TRACKING
# ============================================================================

@dataclass
class PitchMetrics:
    """
    Complete pitch-level metrics for debugging and analysis.

    Tracks everything from release to plate crossing including:
    - Release mechanics
    - Trajectory physics
    - Command accuracy
    - Expected vs actual outcomes
    """
    # Basic pitch info
    sequence_index: int
    pitch_type: str
    count_before: Tuple[int, int]

    # Release mechanics
    release_point: Tuple[float, float, float]  # (x, y, z) in feet
    release_velocity_mph: float
    release_extension_ft: float

    # Spin characteristics
    spin_rpm: float
    spin_axis_deg: Tuple[float, float]  # (azimuth, elevation)
    spin_efficiency: float  # 0.0-1.0

    # Trajectory at plate
    plate_velocity_mph: float
    plate_location: Tuple[float, float]  # (horizontal, vertical) in inches
    vertical_approach_angle_deg: float  # Negative = downward

    # Pitch movement
    vertical_break_inches: float
    horizontal_break_inches: float
    total_break_inches: float

    # Command and accuracy
    target_location: Tuple[float, float]  # Intended location (inches)

    # Player/team identification (with defaults)
    pitcher_name: str = "Unknown"
    pitcher_team: str = "Unknown"  # 'away' or 'home'
    batter_name: str = "Unknown"
    batter_team: str = "Unknown"  # 'away' or 'home'

    # Calculated fields (with defaults)
    command_error: Tuple[float, float] = (0.0, 0.0)     # (h_error, v_error) in inches
    command_error_magnitude: float = 0.0         # Total error magnitude

    # Decision probabilities (BEFORE outcome)
    expected_whiff_prob: float = 0.0
    expected_chase_prob: float = 0.0
    expected_swing_prob: float = 0.0
    expected_contact_prob: float = 0.0

    # Actual outcome
    batter_swung: bool = False
    pitch_outcome: str = "unknown"  # 'ball', 'called_strike', 'swinging_strike', 'foul', 'contact'
    is_strike: bool = False

    # Zone classification
    zone_classification: str = "unknown"  # 'in_zone', 'edge', 'chase', 'waste'

    # Flight physics
    flight_time_ms: float = 0.0
    perceived_velocity_mph: float = 0.0  # Adjusted for extension

    def __post_init__(self):
        """Calculate derived metrics"""
        if self.target_location and self.plate_location:
            h_err = self.plate_location[0] - self.target_location[0]
            v_err = self.plate_location[1] - self.target_location[1]
            self.command_error = (h_err, v_err)
            self.command_error_magnitude = np.sqrt(h_err**2 + v_err**2)

        # Perceived velocity boost from extension
        # ~1 mph per foot of extension (makes pitch "faster" to hitter)
        if self.release_extension_ft:
            extension_boost = self.release_extension_ft * 1.0
            self.perceived_velocity_mph = self.plate_velocity_mph + extension_boost

        # Calculate zone classification
        self.zone_classification = self._classify_zone()

    def _classify_zone(self) -> str:
        """
        Classify pitch location into zone categories.

        Strike zone (MLB规则):
        - Horizontal: -8.5" to +8.5" (17" plate width)
        - Vertical: ~18" to 42" (varies by batter height, using average)

        Returns
        -------
        str
            'in_zone', 'edge', 'chase', or 'waste'
        """
        h_loc = self.plate_location[0]
        v_loc = self.plate_location[1]

        # Strike zone boundaries
        H_ZONE_MIN = -8.5
        H_ZONE_MAX = 8.5
        V_ZONE_MIN = 18.0
        V_ZONE_MAX = 42.0

        # Edge definition: within 2" of zone boundary
        EDGE_MARGIN = 2.0
        # Chase zone: 2-6" outside zone (pitches batters commonly chase)
        CHASE_MIN = 2.0
        CHASE_MAX = 6.0

        # Calculate distances from zone
        h_inside = max(0, H_ZONE_MIN - h_loc, h_loc - H_ZONE_MAX)
        v_inside = max(0, V_ZONE_MIN - v_loc, v_loc - V_ZONE_MAX)

        # Check if in strike zone
        if H_ZONE_MIN <= h_loc <= H_ZONE_MAX and V_ZONE_MIN <= v_loc <= V_ZONE_MAX:
            # Inside zone - check if on edge
            h_dist_to_edge = min(abs(h_loc - H_ZONE_MIN), abs(h_loc - H_ZONE_MAX))
            v_dist_to_edge = min(abs(v_loc - V_ZONE_MIN), abs(v_loc - V_ZONE_MAX))

            if h_dist_to_edge < EDGE_MARGIN or v_dist_to_edge < EDGE_MARGIN:
                return "edge"
            else:
                return "in_zone"

        # Outside zone - determine how far
        max_outside = max(h_inside, v_inside)

        if max_outside < CHASE_MIN:
            return "edge"  # Just outside, still borderline
        elif max_outside < CHASE_MAX:
            return "chase"  # Chase zone - commonly swung at
        else:
            return "waste"  # Too far outside, obvious ball


@dataclass
class SwingDecisionMetrics:
    """
    Detailed tracking of swing decision process.

    Reveals internal decision-making logic for debugging discipline/contact models.
    """
    # Decision inputs
    pitch_zone_rating: str  # 'in_zone', 'edge', 'chase', 'waste'
    pitch_location: Tuple[float, float]  # (h, v) in inches
    pitch_velocity_mph: float
    pitch_type: str
    batter_discipline_rating: int  # 0-100,000
    count: Tuple[int, int]  # (balls, strikes)

    # Pitch deception factors
    pitch_movement_surprise: float = 0.0  # How much more/less break than expected
    velocity_deception: float = 0.0       # Difference from expected velocity

    # Decision probabilities
    swing_probability: float = 0.0
    take_probability: float = 0.0
    chase_probability: float = 0.0  # If out of zone

    # Actual decision
    swung: bool = False
    swing_quality: str = "none"  # 'perfect', 'good', 'poor', 'whiff'

    # Timing (if swung)
    swing_timing_error_ms: float = 0.0  # Negative = early, positive = late
    bat_ball_contact_offset_inches: Tuple[float, float] = (0.0, 0.0)  # (h, v)
    total_contact_offset: float = 0.0

    # Expected contact quality distribution (BEFORE random roll)
    expected_whiff_pct: float = 0.0
    expected_foul_pct: float = 0.0
    expected_weak_pct: float = 0.0
    expected_fair_pct: float = 0.0
    expected_solid_pct: float = 0.0
    expected_barrel_pct: float = 0.0

    # Actual outcome
    contact_made: bool = False
    contact_quality: Optional[str] = None  # 'weak', 'fair', 'solid', 'barrel'
    outcome_rolled: str = "unknown"  # What the RNG selected


# ============================================================================
# B. BATTED BALL FLIGHT DEBUGGING
# ============================================================================

@dataclass
class BattedBallMetrics:
    """
    Complete batted ball trajectory physics and debugging.

    Provides transparency into aerodynamic calculations and flight physics.
    """
    # Launch conditions (required)
    exit_velocity_mph: float
    launch_angle_deg: float
    spray_angle_deg: float  # -45 to +45, 0 = center field

    # Spin characteristics (required)
    backspin_rpm: float  # Positive = backspin
    sidespin_rpm: float  # Positive = toward pull side

    # Trajectory results (required)
    distance_ft: float
    hang_time_sec: float
    apex_height_ft: float

    # Landing coordinates (required, field coordinates, home = 0,0)
    landing_x_ft: float  # Horizontal (positive = right field for RHH)
    landing_y_ft: float  # Depth (positive = toward outfield)

    # Player/team identification (with defaults)
    batter_name: str = "Unknown"
    batter_team: str = "Unknown"  # 'away' or 'home'
    pitcher_name: str = "Unknown"
    pitcher_team: str = "Unknown"  # 'away' or 'home'

    # Contact mechanics (with defaults)
    bat_speed_mph: float = 0.0
    pitch_speed_mph: float = 0.0
    collision_efficiency_q: float = 0.0  # The q parameter from collision physics

    # Calculated fields (with defaults)
    total_spin_rpm: float = 0.0
    spin_axis_deg: float = 0.0  # Direction of spin axis

    # Aerodynamic forces summary
    drag_coefficient_avg: float = 0.0
    lift_coefficient_avg: float = 0.0
    magnus_force_contribution_ft: float = 0.0  # How much Magnus added to distance
    drag_force_loss_ft: float = 0.0            # How much drag reduced distance

    # Wind effects (if present)
    wind_speed_mph: float = 0.0
    wind_direction_deg: float = 0.0
    wind_effect_ft: float = 0.0  # Net distance change from wind

    # Expected vs actual
    expected_distance_ft: float = 0.0  # Statcast xDistance model
    expected_hr_probability: float = 0.0
    expected_batting_avg: float = 0.0  # xBA based on EV/LA
    expected_woba: float = 0.0          # xwOBA based on EV/LA
    expected_slg: float = 0.0           # xSLG based on EV/LA
    is_home_run: bool = False
    actual_outcome: str = "unknown"     # Actual game result

    # Hit classification
    hit_type: str = "unknown"  # 'ground_ball', 'line_drive', 'fly_ball', 'popup'
    hard_hit: bool = False  # EV >= 95 mph
    barrel: bool = False    # Optimal EV + LA combo

    # Fielding context
    catch_probability: float = 0.0  # Probability fielder makes the play
    gb_difficulty: str = "unknown"  # For ground balls: 'routine', 'average', 'tough', 'infield_hit'

    def __post_init__(self):
        """Calculate derived metrics"""
        self.total_spin_rpm = np.sqrt(self.backspin_rpm**2 + self.sidespin_rpm**2)
        if self.total_spin_rpm > 0:
            self.spin_axis_deg = np.degrees(np.arctan2(self.sidespin_rpm, self.backspin_rpm))

        # Hard hit threshold (Statcast standard)
        self.hard_hit = self.exit_velocity_mph >= 95.0

        # Barrel classification (simplified Statcast model)
        # Optimal: EV >= 98, LA between 26-30 degrees
        if self.exit_velocity_mph >= 98.0 and 26.0 <= self.launch_angle_deg <= 30.0:
            self.barrel = True

        # Hit type classification
        if self.launch_angle_deg < 10:
            self.hit_type = "ground_ball"
        elif self.launch_angle_deg < 25:
            self.hit_type = "line_drive"
        elif self.launch_angle_deg < 50:
            self.hit_type = "fly_ball"
        else:
            self.hit_type = "popup"

        # Calculate expected stats (xBA, xwOBA, xSLG) from EV/LA
        self._calculate_expected_stats()

        # Calculate ground ball difficulty if applicable
        if self.hit_type == "ground_ball":
            self.gb_difficulty = self._calculate_gb_difficulty()

    def _calculate_expected_stats(self):
        """
        Calculate expected batting average and wOBA based on EV/LA.

        Uses simplified Statcast model:
        - xBA increases with EV and optimal LA (sweet spot ~15-25°)
        - Ground balls (<10°): low xBA regardless of EV
        - Line drives (10-25°): highest xBA
        - Fly balls (25-50°): xBA depends heavily on EV
        - Pop-ups (>50°): very low xBA
        """
        ev = self.exit_velocity_mph
        la = self.launch_angle_deg

        # xBA model (simplified Statcast regression)
        if la < 10:  # Ground balls
            # GB xBA depends mostly on EV (faster = harder to field)
            if ev < 70:
                self.expected_batting_avg = 0.100
            elif ev < 90:
                self.expected_batting_avg = 0.220 + (ev - 70) * 0.005
            else:  # Hard GB
                self.expected_batting_avg = min(0.320 + (ev - 90) * 0.003, 0.450)

        elif la < 25:  # Line drives
            # LD have highest xBA, very dependent on EV
            if ev < 70:
                self.expected_batting_avg = 0.450
            elif ev < 95:
                self.expected_batting_avg = 0.550 + (ev - 70) * 0.006
            else:
                self.expected_batting_avg = min(0.700 + (ev - 95) * 0.010, 0.950)

        elif la < 50:  # Fly balls
            # FB xBA heavily dependent on EV (need power to clear outfield)
            if ev < 85:
                self.expected_batting_avg = 0.150  # Lazy fly out
            elif ev < 98:
                self.expected_batting_avg = 0.200 + (ev - 85) * 0.015
            elif ev < 105:
                self.expected_batting_avg = 0.400 + (ev - 98) * 0.040  # Warning track power
            else:
                self.expected_batting_avg = min(0.680 + (ev - 105) * 0.030, 0.950)  # Wall scraper to no-doubter

        else:  # Pop-ups (>50°)
            self.expected_batting_avg = 0.020  # Almost always out

        # xSLG model (expected slugging on contact)
        # Multiply xBA by expected bases (1B/2B/3B/HR probabilities)
        if la < 10:  # Ground balls
            # Mostly singles, rare doubles
            expected_bases = 1.05 if ev > 95 else 1.02
        elif la < 25:  # Line drives
            # Mix of singles, doubles, some HRs if hard hit
            if ev < 95:
                expected_bases = 1.40
            elif ev < 105:
                expected_bases = 1.80  # Gap shots, doubles
            else:
                expected_bases = 2.40  # Line drive HRs
        elif la < 50:  # Fly balls
            # Highest HR probability
            if ev < 95:
                expected_bases = 1.20
            elif ev < 100:
                expected_bases = 2.00  # Warning track doubles
            elif ev < 105:
                expected_bases = 3.20  # Mix of XBH and HR
            else:
                expected_bases = 3.80  # Almost all HRs
        else:  # Pop-ups
            expected_bases = 1.00  # Rare IF single

        self.expected_slg = self.expected_batting_avg * expected_bases

        # xwOBA model (weighted on-base average)
        # wOBA weights: BB=0.69, 1B=0.88, 2B=1.24, 3B=1.56, HR=1.95
        # For batted balls, assume mix based on EV/LA
        # Simplified: xwOBA ≈ 0.8 + (xSLG - xBA) * 0.5
        self.expected_woba = 0.80 * self.expected_batting_avg + 0.30 * self.expected_slg

    def _calculate_gb_difficulty(self) -> str:
        """
        Calculate ground ball difficulty rating.

        Based on:
        - Exit velocity (faster = harder to field)
        - Hang time (less time = harder)
        - Launch angle (sharper = more hops, harder to field cleanly)

        Returns
        -------
        str
            'routine', 'average', 'tough', or 'infield_hit'
        """
        ev = self.exit_velocity_mph
        hang_time = self.hang_time_sec
        la = self.launch_angle_deg

        # Difficulty factors
        # EV: <80 = soft, 80-95 = medium, >95 = hard
        # Hang time: >3.0s = slow roller, 2-3s = average, <2s = fast
        # LA: 0-3° = sharp grounder (hard to field cleanly), 3-8° = normal GB

        # Calculate difficulty score (0-100, higher = harder)
        difficulty_score = 0

        # Exit velocity contribution (0-40 points)
        if ev < 70:
            ev_points = 10  # Very soft
        elif ev < 85:
            ev_points = 20 + (ev - 70) * 0.67  # Soft to medium
        elif ev < 95:
            ev_points = 30 + (ev - 85) * 0.5  # Medium to hard
        else:
            ev_points = min(40, 35 + (ev - 95) * 1.0)  # Very hard

        difficulty_score += ev_points

        # Hang time contribution (0-30 points)
        # Less time = harder to field
        if hang_time > 3.0:
            hang_points = 5  # Plenty of time (slow roller)
        elif hang_time > 2.0:
            hang_points = 15 + (3.0 - hang_time) * 10  # Average
        else:
            hang_points = min(30, 25 + (2.0 - hang_time) * 25)  # Fast

        difficulty_score += hang_points

        # Launch angle contribution (0-30 points)
        # Sharp grounders (low LA) are harder to field cleanly
        if la < 1.0:
            la_points = 30  # Bullet, very sharp
        elif la < 3.0:
            la_points = 25 - (la - 1.0) * 2.5  # Sharp
        elif la < 6.0:
            la_points = 15 - (la - 3.0) * 2  # Normal
        else:
            la_points = max(5, 9 - (la - 6.0) * 1)  # High bounce

        difficulty_score += la_points

        # Classify based on total difficulty score
        if difficulty_score < 35:
            return "routine"      # Easy play, slow roller or soft contact
        elif difficulty_score < 60:
            return "average"      # Standard GB, should be fielded
        elif difficulty_score < 80:
            return "tough"        # Hard-hit or fast, challenging play
        else:
            return "infield_hit"  # Extremely difficult, likely a hit


# ============================================================================
# C. FIELDING INTERACTION DEBUG
# ============================================================================

@dataclass
class FieldingMetrics:
    """
    Complete fielding play debugging information.

    Tracks fielder performance, positioning, and decision-making.
    """
    # Fielder identification
    fielder_name: str
    fielder_position: str  # 'SS', 'CF', 'LF', etc.

    # Starting position
    starting_position: Tuple[float, float]  # (x, y) in feet from home plate

    # Ball landing location
    ball_landing_position: Tuple[float, float, float]  # (x, y, z) in feet

    # Reaction and movement
    reaction_time_ms: float  # Milliseconds to first movement
    distance_to_ball_ft: float
    route_efficiency_pct: float  # 100% = optimal path, <100% = suboptimal

    # Sprint physics
    top_sprint_speed_fps: float  # Feet per second
    time_to_top_speed_sec: float
    actual_avg_speed_fps: float

    # Timing
    ball_hang_time_sec: float
    fielder_eta_sec: float  # When fielder reaches ball location
    time_margin_sec: float  # ETA - hang_time (negative = makes it)

    # Catch probability and outcome
    opportunity_difficulty: float  # 0-100 scale (Statcast OAA style)
    expected_catch_probability: float  # 0.0-1.0
    catch_successful: bool = False

    # If failed
    failure_reason: Optional[str] = None  # 'too_slow', 'drop_error', 'bad_route', etc.
    is_error: bool = False  # True if should have been made

    # If successful - throwing
    exchange_time_sec: Optional[float] = None  # Time to transfer ball
    throw_velocity_mph: Optional[float] = None
    throw_accuracy_error_ft: Optional[float] = None  # Distance from target
    throw_flight_time_sec: Optional[float] = None

    # Decision quality
    correct_fielder_assigned: bool = True  # Was this the right fielder?
    alternative_fielders: List[str] = field(default_factory=list)  # Who else could have made it


@dataclass
class BaserunningMetrics:
    """
    Complete baserunning play debugging.

    Tracks runner decisions, speed, and advancement outcomes.
    """
    # Runner identification
    runner_name: str
    starting_base: str  # '1st', '2nd', '3rd', 'home'
    target_base: str

    # Runner attributes
    top_sprint_speed_fps: float  # Statcast sprint speed
    acceleration_fps2: float

    # Starting conditions
    lead_distance_ft: float  # How far off base at contact
    jump_time_sec: float     # Time to start running (reaction)
    jump_quality: str        # 'excellent', 'good', 'average', 'poor'

    # Route and speed
    distance_to_run_ft: float
    turn_efficiency_pct: float  # Speed retention through turn
    actual_run_time_sec: float

    # Decision making
    risk_score: float  # 0.0-1.0 (how risky the advancement attempt)
    expected_success_probability: float  # Based on ball/runner ETAs
    send_decision: str  # 'auto', 'aggressive', 'conservative', 'coach_send', 'coach_hold'

    # Outcome timing
    runner_arrival_time_sec: float
    ball_arrival_time_sec: float  # When ball reaches base
    time_margin_sec: float  # Positive = safe, negative = out

    # Actual outcome
    advance_successful: bool = False
    outcome: str = "unknown"  # 'safe', 'out', 'tag_avoided', 'error'

    # Throwing defense
    outfielder_exchange_time_sec: Optional[float] = None
    throw_velocity_mph: Optional[float] = None
    throw_accuracy_error_ft: Optional[float] = None


# ============================================================================
# D. PITCHER FATIGUE MONITORING
# ============================================================================

@dataclass
class PitcherFatigueMetrics:
    """
    Tracks pitcher fatigue and its effects on performance.

    Shows how stamina degrades velocity, spin, and command over time.
    """
    pitcher_name: str

    # Current state
    pitches_thrown: int
    current_inning: int
    outs_recorded: int

    # Fatigue level
    current_fatigue_pct: float  # 0-100%, higher = more tired
    stamina_rating: int  # 0-100,000 base stamina

    # Velocity degradation
    base_velocity_mph: float  # Fresh velocity
    current_velocity_mph: float
    velocity_loss_mph: float  # How much lost to fatigue

    # Spin degradation
    base_spin_rpm: float
    current_spin_rpm: float
    spin_loss_rpm: float

    # Command degradation
    base_command_sigma: float  # Control when fresh (inches)
    current_command_sigma: float
    command_penalty_pct: float  # % worse command

    # Situational stress
    runners_on_base: int  # 0-3
    is_high_leverage: bool  # High stress situation
    stress_inning: bool  # Long inning (>20 pitches)

    # Times through order penalty
    times_through_order: int  # How many times facing this lineup
    tto_penalty_multiplier: float  # Performance penalty (typically 1.0-1.3)

    # Predicted performance
    expected_whiff_rate: float  # With current fatigue
    expected_walk_rate: float
    expected_hard_contact_rate: float


# ============================================================================
# E. PROBABILISTIC DEBUG OUTPUT
# ============================================================================

@dataclass
class ExpectedOutcomeMetrics:
    """
    Expected vs actual outcome comparison (Statcast-style xStats).

    Critical for model validation and tuning.
    """
    # Situation
    pitcher_name: str
    batter_name: str
    count: Tuple[int, int]

    # Expected batting outcomes (BEFORE plate appearance)
    xBA: float  # Expected batting average
    xSLG: float  # Expected slugging
    xwOBA: float  # Expected weighted on-base average
    xISO: float  # Expected isolated power

    # Expected event probabilities
    expected_k_prob: float  # Strikeout
    expected_bb_prob: float  # Walk
    expected_contact_prob: float  # Any contact

    # Expected batted ball outcomes (IF contact made)
    expected_hr_prob: float
    expected_xbh_prob: float  # Extra-base hit
    expected_babip: float  # Batting average on balls in play

    # Expected batted ball quality
    expected_exit_velocity: float
    expected_launch_angle: float
    expected_barrel_prob: float
    expected_hard_hit_prob: float

    # Actual outcomes
    actual_outcome: str  # 'strikeout', 'walk', 'single', 'fly_out', etc.
    actual_exit_velocity: Optional[float] = None
    actual_launch_angle: Optional[float] = None
    actual_distance: Optional[float] = None

    # Comparison
    outcome_vs_expected: str = ""  # 'better', 'expected', 'worse'
    performance_delta: float = 0.0  # How much better/worse than expected

    def calculate_delta(self):
        """Calculate performance vs expectation"""
        # Map outcomes to value (simplified)
        outcome_values = {
            'home_run': 2.0,
            'triple': 1.5,
            'double': 1.2,
            'single': 0.9,
            'walk': 0.7,
            'error': 0.5,
            'fly_out': 0.0,
            'ground_out': 0.0,
            'line_out': 0.0,
            'strikeout': -0.3,
        }

        actual_value = outcome_values.get(self.actual_outcome, 0.0)
        expected_value = self.xwOBA

        self.performance_delta = actual_value - expected_value

        if self.performance_delta > 0.2:
            self.outcome_vs_expected = "much_better"
        elif self.performance_delta > 0.05:
            self.outcome_vs_expected = "better"
        elif self.performance_delta < -0.2:
            self.outcome_vs_expected = "much_worse"
        elif self.performance_delta < -0.05:
            self.outcome_vs_expected = "worse"
        else:
            self.outcome_vs_expected = "expected"


# ============================================================================
# F. SUMMARY STATISTICS AGGREGATION
# ============================================================================

@dataclass
class BattedBallDistribution:
    """Aggregate batted ball type distribution"""
    total_balls_in_play: int = 0

    # Launch angle distribution
    ground_balls: int = 0  # LA < 10°
    line_drives: int = 0   # LA 10-25°
    fly_balls: int = 0     # LA 25-50°
    popups: int = 0        # LA > 50°

    # Contact quality
    barrels: int = 0
    hard_hit: int = 0  # EV >= 95 mph
    medium: int = 0    # EV 85-95 mph
    soft: int = 0      # EV < 85 mph

    # Outcomes
    weak_contact: int = 0
    fair_contact: int = 0
    solid_contact: int = 0

    def get_percentages(self) -> Dict[str, float]:
        """Get distribution as percentages"""
        if self.total_balls_in_play == 0:
            return {}

        total = self.total_balls_in_play
        return {
            'ground_ball_pct': 100.0 * self.ground_balls / total,
            'line_drive_pct': 100.0 * self.line_drives / total,
            'fly_ball_pct': 100.0 * self.fly_balls / total,
            'popup_pct': 100.0 * self.popups / total,
            'barrel_pct': 100.0 * self.barrels / total,
            'hard_hit_pct': 100.0 * self.hard_hit / total,
        }

    def compare_to_mlb(self) -> Dict[str, str]:
        """Compare to MLB averages"""
        mlb_averages = {
            'ground_ball_pct': 44.0,
            'line_drive_pct': 21.0,
            'fly_ball_pct': 35.0,
            'barrel_pct': 8.0,
            'hard_hit_pct': 38.0,
        }

        pct = self.get_percentages()
        comparison = {}

        for key, mlb_val in mlb_averages.items():
            sim_val = pct.get(key, 0.0)
            diff = sim_val - mlb_val
            if abs(diff) < 2.0:
                status = "✓ Match"
            elif diff > 0:
                status = f"↑ +{diff:.1f}%"
            else:
                status = f"↓ {diff:.1f}%"
            comparison[key] = status

        return comparison


@dataclass
class PitchingOutcomes:
    """Aggregate pitching outcome statistics"""
    total_pitches: int = 0

    # Per-pitch outcomes
    called_strikes: int = 0
    swinging_strikes: int = 0
    fouls: int = 0
    balls: int = 0
    in_play: int = 0

    # Advanced metrics
    swings: int = 0
    whiffs: int = 0
    contacts: int = 0
    chases: int = 0  # Swings at pitches out of zone
    takes: int = 0

    # By pitch type
    pitch_type_counts: Dict[str, int] = field(default_factory=dict)
    pitch_type_whiffs: Dict[str, int] = field(default_factory=dict)

    def get_rates(self) -> Dict[str, float]:
        """Calculate advanced pitching rates"""
        if self.total_pitches == 0:
            return {}

        total_strikes = self.called_strikes + self.swinging_strikes

        rates = {
            'csw_pct': 100.0 * (self.called_strikes + self.whiffs) / self.total_pitches,
            'whiff_pct': 100.0 * self.whiffs / self.swings if self.swings > 0 else 0.0,
            'swing_pct': 100.0 * self.swings / self.total_pitches,
            'contact_pct': 100.0 * self.contacts / self.swings if self.swings > 0 else 0.0,
            'strike_pct': 100.0 * total_strikes / self.total_pitches,
        }

        return rates


@dataclass
class InningMetrics:
    """Summary metrics for a single inning"""
    inning_number: int
    is_top: bool

    batted_balls: BattedBallDistribution = field(default_factory=BattedBallDistribution)
    pitching: PitchingOutcomes = field(default_factory=PitchingOutcomes)

    runs_scored: int = 0
    hits: int = 0
    errors: int = 0

    pitch_metrics: List[PitchMetrics] = field(default_factory=list)
    batted_ball_metrics: List[BattedBallMetrics] = field(default_factory=list)
    fielding_metrics: List[FieldingMetrics] = field(default_factory=list)


@dataclass
class GameMetrics:
    """Complete game-level aggregated metrics"""
    game_id: str
    away_team: str
    home_team: str

    innings: List[InningMetrics] = field(default_factory=list)

    # Away team aggregates
    away_batted_balls: BattedBallDistribution = field(default_factory=BattedBallDistribution)
    away_pitching: PitchingOutcomes = field(default_factory=PitchingOutcomes)

    # Home team aggregates
    home_batted_balls: BattedBallDistribution = field(default_factory=BattedBallDistribution)
    home_pitching: PitchingOutcomes = field(default_factory=PitchingOutcomes)

    def generate_summary_report(self) -> str:
        """Generate comprehensive summary report"""
        report = []
        report.append("="*80)
        report.append(f"SIMULATION METRICS SUMMARY: {self.away_team} @ {self.home_team}")
        report.append("="*80)

        # Batted ball distributions
        report.append("\nBATTED BALL DISTRIBUTIONS:")
        report.append("-"*80)

        away_pct = self.away_batted_balls.get_percentages()
        home_pct = self.home_batted_balls.get_percentages()

        report.append(f"\n{self.away_team:20s} | {self.home_team:20s} | MLB Avg")
        report.append("-"*60)

        mlb_avgs = {
            'GB%': 44.0, 'LD%': 21.0, 'FB%': 35.0,
            'Barrel%': 8.0, 'HardHit%': 38.0
        }

        for stat, mlb_val in mlb_avgs.items():
            key = stat.lower().replace('%', '_pct')
            away_val = away_pct.get(key, 0.0)
            home_val = home_pct.get(key, 0.0)
            report.append(f"{stat:12s}: {away_val:5.1f}% | {home_val:5.1f}% | {mlb_val:5.1f}%")

        # Pitching outcomes
        report.append("\nPITCHING OUTCOMES:")
        report.append("-"*80)

        away_rates = self.away_pitching.get_rates()
        home_rates = self.home_pitching.get_rates()

        report.append(f"\n{'Metric':15s} | {self.away_team:12s} | {self.home_team:12s} | Target")
        report.append("-"*60)

        targets = {
            'CSW%': 28.0, 'Whiff%': 25.0, 'Swing%': 47.0, 'Contact%': 75.0
        }

        for metric, target in targets.items():
            key = metric.lower().replace('%', '_pct')
            away_val = away_rates.get(key, 0.0)
            home_val = home_rates.get(key, 0.0)
            report.append(f"{metric:15s} | {away_val:11.1f}% | {home_val:11.1f}% | {target:.1f}%")

        report.append("="*80)

        return "\n".join(report)


# ============================================================================
# G. METRICS COLLECTOR - MAIN INTERFACE
# ============================================================================

class SimMetricsCollector:
    """
    Central metrics collection system for simulation debugging.

    Usage:
        collector = SimMetricsCollector(debug_level=DebugLevel.DETAILED)

        # During simulation
        collector.record_pitch(pitch_metrics)
        collector.record_batted_ball(bb_metrics)
        collector.record_fielding(field_metrics)

        # After simulation
        collector.print_summary()
        collector.export_csv("game_metrics.csv")
    """

    def __init__(self, debug_level: DebugLevel = DebugLevel.OFF):
        """
        Initialize metrics collector.

        Parameters
        ----------
        debug_level : DebugLevel
            Verbosity level for output
        """
        self.debug_level = debug_level
        self.enabled = debug_level != DebugLevel.OFF

        # Storage
        self.pitch_metrics: List[PitchMetrics] = []
        self.swing_metrics: List[SwingDecisionMetrics] = []
        self.batted_ball_metrics: List[BattedBallMetrics] = []
        self.fielding_metrics: List[FieldingMetrics] = []
        self.baserunning_metrics: List[BaserunningMetrics] = []
        self.fatigue_metrics: List[PitcherFatigueMetrics] = []
        self.expected_outcome_metrics: List[ExpectedOutcomeMetrics] = []

        # Game metrics
        self.game_metrics: Optional[GameMetrics] = None

    def record_pitch(self, metrics: PitchMetrics):
        """Record pitch-level metrics"""
        if self.enabled:
            self.pitch_metrics.append(metrics)

            if self.debug_level.value >= DebugLevel.DETAILED.value:
                self._print_pitch_debug(metrics)

    def record_swing_decision(self, metrics: SwingDecisionMetrics):
        """Record swing decision metrics"""
        if self.enabled:
            self.swing_metrics.append(metrics)

            if self.debug_level.value >= DebugLevel.EXHAUSTIVE.value:
                self._print_swing_debug(metrics)

    def record_batted_ball(self, metrics: BattedBallMetrics):
        """Record batted ball metrics"""
        if self.enabled:
            self.batted_ball_metrics.append(metrics)

            if self.debug_level.value >= DebugLevel.DETAILED.value:
                self._print_batted_ball_debug(metrics)

    def record_fielding(self, metrics: FieldingMetrics):
        """Record fielding metrics"""
        if self.enabled:
            self.fielding_metrics.append(metrics)

            if self.debug_level.value >= DebugLevel.DETAILED.value:
                self._print_fielding_debug(metrics)

    def record_baserunning(self, metrics: BaserunningMetrics):
        """Record baserunning metrics"""
        if self.enabled:
            self.baserunning_metrics.append(metrics)
            if self.debug_level.value >= DebugLevel.DETAILED.value:
                self._print_baserunning_debug(metrics)

    def record_fatigue(self, metrics: PitcherFatigueMetrics):
        """Record pitcher fatigue metrics"""
        if self.enabled:
            self.fatigue_metrics.append(metrics)
            if self.debug_level.value >= DebugLevel.DETAILED.value:
                self._print_fatigue_debug(metrics)

    def record_expected_outcome(self, metrics: ExpectedOutcomeMetrics):
        """Record expected vs actual outcome"""
        if self.enabled:
            metrics.calculate_delta()
            self.expected_outcome_metrics.append(metrics)
            if self.debug_level.value >= DebugLevel.DETAILED.value:
                self._print_expected_outcome_debug(metrics)

    def _print_expected_outcome_debug(self, m: ExpectedOutcomeMetrics):
        """Print expected vs actual run value for plate appearance"""
        print(f"\n📈 EXPECTED vs ACTUAL OUTCOME:")
        print(f"   Matchup: {m.batter_name} vs {m.pitcher_name} ({m.count[0]}-{m.count[1]})")
        print(f"   Expected Stats (before PA):")
        print(f"     - xBA: {m.xBA:.3f}")
        print(f"     - xSLG: {m.xSLG:.3f}")
        print(f"     - xwOBA: {m.xwOBA:.3f}")
        print(f"     - xISO: {m.xISO:.3f}")

        print(f"   Expected Probabilities:")
        print(f"     - Strikeout: {m.expected_k_prob:.1%}")
        print(f"     - Walk: {m.expected_bb_prob:.1%}")
        print(f"     - Contact: {m.expected_contact_prob:.1%}")

        if m.expected_contact_prob > 0.01:
            print(f"   Expected Batted Ball Outcomes (if contact):")
            print(f"     - Home run: {m.expected_hr_prob:.1%}")
            print(f"     - Extra-base hit: {m.expected_xbh_prob:.1%}")
            print(f"     - BABIP: {m.expected_babip:.3f}")
            print(f"   Expected Batted Ball Quality:")
            print(f"     - EV: {m.expected_exit_velocity:.1f} mph")
            print(f"     - LA: {m.expected_launch_angle:.1f}°")
            print(f"     - Barrel prob: {m.expected_barrel_prob:.1%}")
            print(f"     - Hard hit prob: {m.expected_hard_hit_prob:.1%}")

        print(f"   Actual Outcome: {m.actual_outcome.upper()}")
        if m.actual_exit_velocity:
            print(f"   Actual Batted Ball: EV={m.actual_exit_velocity:.1f} mph, LA={m.actual_launch_angle:.1f}°, Dist={m.actual_distance:.1f} ft")

        # Run value comparison
        outcome_icons = {"much_better": "🔥", "better": "✓", "expected": "=", "worse": "↓", "much_worse": "❌"}
        outcome_icon = outcome_icons.get(m.outcome_vs_expected, "?")
        print(f"   xRunValue (based on contact): {m.xwOBA:.3f}")
        print(f"   Performance: {m.outcome_vs_expected.upper()} {outcome_icon}")
        print(f"   Luck/Performance Delta: {m.performance_delta:+.3f}")

    def _print_pitch_debug(self, m: PitchMetrics):
        """Print pitch debug output"""
        # Machine-readable outcome code
        outcome_code = self._get_outcome_code(m.pitch_outcome, m.batter_swung)

        print(f"\n📊 PITCH #{m.sequence_index}: {m.pitch_type} ({m.count_before[0]}-{m.count_before[1]}) [CODE: {outcome_code}]")
        print(f"   Release: {m.release_velocity_mph:.1f} mph, {m.spin_rpm:.0f} rpm")
        print(f"   Plate: {m.plate_velocity_mph:.1f} mph @ ({m.plate_location[0]:+.1f}\", {m.plate_location[1]:.1f}\")")
        print(f"   Break: V={m.vertical_break_inches:+.1f}\", H={m.horizontal_break_inches:+.1f}\"")

        # Zone classification
        zone_icon = {"in_zone": "🎯", "edge": "⚡", "chase": "🎣", "waste": "🗑️"}
        zone_display = zone_icon.get(m.zone_classification, "❓")
        print(f"   Zone: {m.zone_classification.upper()} {zone_display}")

        # Enhanced Intent vs Actual section
        target_h = float(m.target_location[0]) if m.target_location else 0.0
        target_v = float(m.target_location[1]) if m.target_location else 0.0
        h_err = m.plate_location[0] - target_h
        v_err = m.plate_location[1] - target_v

        # Determine target zone description
        target_zone_desc = self._describe_target_zone(target_h, target_v)
        miss_direction = self._describe_miss_direction(h_err, v_err)

        print(f"   Intent: {target_zone_desc} (target: {target_h:+.1f}\", {target_v:.1f}\")")
        print(f"   Result: Miss {miss_direction} (error: {abs(h_err):.1f}\" H, {abs(v_err):.1f}\" V, total {m.command_error_magnitude:.2f}\")")

        # Only show expected probabilities if they're actually computed (non-zero)
        if m.expected_swing_prob > 0.01 or m.expected_whiff_prob > 0.01:
            print(f"   Expected: Swing={m.expected_swing_prob:.1%}, Whiff={m.expected_whiff_prob:.1%}")

        print(f"   Outcome: {m.pitch_outcome} {'(swung)' if m.batter_swung else '(taken)'}")

    def _get_outcome_code(self, outcome: str, swung: bool) -> str:
        """Generate machine-readable outcome code"""
        if swung:
            if outcome == 'swinging_strike':
                return 'STRIKE_SWING'
            elif outcome == 'foul':
                return 'FOUL'
            elif outcome in ['contact', 'ball_in_play']:
                return 'INPLAY'
            elif outcome == 'ball':
                return 'BALL_SWING'  # Edge case
        else:
            if outcome == 'called_strike':
                return 'STRIKE_TAKEN'
            elif outcome == 'ball':
                return 'BALL'
        return 'UNKNOWN'

    def _describe_target_zone(self, h: float, v: float) -> str:
        """Describe the pitcher's intended target zone"""
        # Horizontal zones
        if h < -5:
            h_zone = "inside"
        elif h < -2:
            h_zone = "inside-corner"
        elif h < 2:
            h_zone = "middle"
        elif h < 5:
            h_zone = "outside-corner"
        else:
            h_zone = "outside"

        # Vertical zones
        if v < 22:
            v_zone = "low"
        elif v < 28:
            v_zone = "low-middle"
        elif v < 34:
            v_zone = "middle"
        elif v < 40:
            v_zone = "high-middle"
        else:
            v_zone = "high"

        return f"{v_zone}, {h_zone}"

    def _describe_miss_direction(self, h_err: float, v_err: float) -> str:
        """Describe the direction of command miss"""
        h_dir = "arm-side" if h_err > 0 else "glove-side" if h_err < 0 else ""
        v_dir = "high" if v_err > 0 else "low" if v_err < 0 else ""

        if abs(h_err) > abs(v_err) * 1.5:
            return f"{abs(h_err):.1f}\" {h_dir}"
        elif abs(v_err) > abs(h_err) * 1.5:
            return f"{abs(v_err):.1f}\" {v_dir}"
        elif h_dir and v_dir:
            return f"{abs(h_err):.1f}\" {h_dir}, {abs(v_err):.1f}\" {v_dir}"
        else:
            return "on target"

    def _print_swing_debug(self, m: SwingDecisionMetrics):
        """Print swing decision debug output with full reasoning"""
        print(f"\n🎯 SWING DECISION:")
        print(f"   Pitch location: ({m.pitch_location[0]:+.1f}\", {m.pitch_location[1]:.1f}\") - Zone: {m.pitch_zone_rating.upper()}")
        print(f"   Pitch type: {m.pitch_type} @ {m.pitch_velocity_mph:.1f} mph")

        # Decision model
        print(f"   Swing Decision Model:")
        print(f"     - Swing probability: {m.swing_probability:.1%}")
        print(f"     - Take probability: {m.take_probability:.1%}")
        if m.pitch_zone_rating == 'chase':
            print(f"     - Chase probability: {m.chase_probability:.1%}")
        print(f"     - Batter discipline rating: {m.batter_discipline_rating:,}")
        print(f"     - Count: {m.count[0]}-{m.count[1]}")

        # Decision made
        print(f"   Decision: {'SWING' if m.swung else 'TAKE'}")

        # If swung, show contact quality breakdown
        if m.swung:
            print(f"   Expected Contact Outcomes (before swing):")
            print(f"     - Whiff: {m.expected_whiff_pct:.1%}")
            print(f"     - Foul: {m.expected_foul_pct:.1%}")
            print(f"     - Weak contact: {m.expected_weak_pct:.1%}")
            print(f"     - Fair contact: {m.expected_fair_pct:.1%}")
            print(f"     - Solid contact: {m.expected_solid_pct:.1%}")
            print(f"     - Barrel: {m.expected_barrel_pct:.1%}")

            print(f"   Swing Execution:")
            print(f"     - Timing error: {m.swing_timing_error_ms:+.1f} ms {'(late)' if m.swing_timing_error_ms > 0 else '(early)' if m.swing_timing_error_ms < 0 else '(perfect)'}")
            print(f"     - Contact offset: {m.total_contact_offset:.2f}\" from sweet spot")
            if m.bat_ball_contact_offset_inches != (0.0, 0.0):
                print(f"     - Offset breakdown: ({m.bat_ball_contact_offset_inches[0]:+.2f}\", {m.bat_ball_contact_offset_inches[1]:+.2f}\")")
            print(f"   Result: {m.contact_quality.upper() if m.contact_made else 'WHIFF'}")

    def _print_batted_ball_debug(self, m: BattedBallMetrics):
        """Print batted ball debug output with physics validation"""
        print(f"\n⚾ BATTED BALL: {m.hit_type.upper()}")
        print(f"   EV: {m.exit_velocity_mph:.1f} mph, LA: {m.launch_angle_deg:.1f}°, Spray: {m.spray_angle_deg:+.1f}°")
        print(f"   Spin: {m.backspin_rpm:.0f} rpm backspin, {m.sidespin_rpm:+.0f} rpm sidespin")

        # Contact Quality Model Inputs
        if m.bat_speed_mph > 0 or m.pitch_speed_mph > 0:
            print(f"   Contact Model Inputs:")
            if m.bat_speed_mph > 0:
                print(f"     - Bat speed: {m.bat_speed_mph:.1f} mph")
            if m.pitch_speed_mph > 0:
                print(f"     - Pitch speed: {m.pitch_speed_mph:.1f} mph")
            if m.collision_efficiency_q > 0:
                print(f"     - Collision efficiency (q): {m.collision_efficiency_q:.3f}")
                print(f"     - Resulting EV: {m.exit_velocity_mph:.1f} mph")

        print(f"   Distance: {m.distance_ft:.1f} ft (apex: {m.apex_height_ft:.1f} ft)")
        print(f"   Hang time: {m.hang_time_sec:.2f} s")
        print(f"   Landing: ({m.landing_x_ft:.1f}, {m.landing_y_ft:.1f})")
        print(f"   Quality: {'BARREL ⭐' if m.barrel else 'HARD 💪' if m.hard_hit else 'MEDIUM'}")

        # Physics Validation Sub-Block
        if m.expected_distance_ft > 0:
            distance_delta = m.distance_ft - m.expected_distance_ft
            hang_time_predicted = self._predict_hang_time(m.exit_velocity_mph, m.launch_angle_deg)
            hang_time_delta = m.hang_time_sec - hang_time_predicted if hang_time_predicted > 0 else 0

            print(f"   Physics Consistency Check:")
            print(f"     - Predicted distance: {m.expected_distance_ft:.1f} ft")
            print(f"     - Actual simulated: {m.distance_ft:.1f} ft")
            print(f"     - Delta: {distance_delta:+.1f} ft ({100*distance_delta/m.expected_distance_ft:+.1f}%)")
            if hang_time_predicted > 0:
                print(f"     - Predicted hang time: {hang_time_predicted:.2f} s")
                print(f"     - Actual hang time: {m.hang_time_sec:.2f} s")
                print(f"     - Delta: {hang_time_delta:+.3f} s")

        # Ground ball difficulty rating
        if m.hit_type == "ground_ball" and m.gb_difficulty != "unknown":
            gb_icons = {"routine": "✓", "average": "↔", "tough": "⚠", "infield_hit": "🔥"}
            gb_icon = gb_icons.get(m.gb_difficulty, "?")
            print(f"   GB Difficulty: {m.gb_difficulty.upper()} {gb_icon}")

        # Expected outcomes (xStats)
        print(f"   Expected Stats: xBA={m.expected_batting_avg:.3f}, xSLG={m.expected_slg:.3f}, xwOBA={m.expected_woba:.3f}")

        # Show actual outcome if available
        if m.actual_outcome != "unknown":
            print(f"   Actual Outcome: {m.actual_outcome}")

        # Show catch probability if available
        if m.catch_probability > 0.0:
            catch_rating = "routine" if m.catch_probability > 0.90 else "likely" if m.catch_probability > 0.70 else "50-50" if m.catch_probability > 0.40 else "tough" if m.catch_probability > 0.15 else "nearly impossible"
            print(f"   Catch Probability: {m.catch_probability:.1%} ({catch_rating})")

    def _predict_hang_time(self, ev_mph: float, la_deg: float) -> float:
        """Simple hang time prediction based on EV and LA"""
        if la_deg < 10:
            return 0  # Ground balls don't have meaningful hang time
        # Simplified physics: t = 2 * v_z / g
        # v_z = v * sin(LA)
        import math
        v_fps = ev_mph * 1.467  # mph to fps
        v_z = v_fps * math.sin(math.radians(la_deg))
        g = 32.174  # ft/s^2
        hang_time = 2 * v_z / g
        return max(0, hang_time)

    def _print_fielding_debug(self, m: FieldingMetrics):
        """Print fielding debug output with enhanced route efficiency"""
        print(f"\n🧤 FIELDING: {m.fielder_name} ({m.fielder_position})")
        print(f"   Starting position: ({m.starting_position[0]:.1f}, {m.starting_position[1]:.1f})")
        print(f"   Ball landing: ({m.ball_landing_position[0]:.1f}, {m.ball_landing_position[1]:.1f}, {m.ball_landing_position[2]:.1f})")

        # Reaction and route
        print(f"   Fielder Reaction:")
        print(f"     - Reaction time: {m.reaction_time_ms:.0f} ms")
        optimal_distance = m.distance_to_ball_ft
        actual_distance = optimal_distance / (m.route_efficiency_pct / 100.0) if m.route_efficiency_pct > 0 else optimal_distance
        inefficiency_distance = actual_distance - optimal_distance
        print(f"     - Optimal route distance: {optimal_distance:.1f} ft")
        if inefficiency_distance > 0.5:
            print(f"     - Actual path taken: {actual_distance:.1f} ft (+{inefficiency_distance:.1f} ft inefficiency)")
        print(f"     - Route efficiency: {m.route_efficiency_pct:.1f}%")

        # Sprint physics
        print(f"   Sprint Physics:")
        print(f"     - Top sprint speed: {m.top_sprint_speed_fps:.1f} ft/s ({m.top_sprint_speed_fps * 0.681818:.1f} mph)")
        print(f"     - Time to top speed: {m.time_to_top_speed_sec:.2f} s")
        print(f"     - Actual avg speed: {m.actual_avg_speed_fps:.1f} ft/s ({m.actual_avg_speed_fps * 0.681818:.1f} mph)")

        # Timing
        print(f"   Timing:")
        print(f"     - Ball hang time: {m.ball_hang_time_sec:.2f} s")
        print(f"     - Fielder ETA: {m.fielder_eta_sec:.2f} s")
        print(f"     - Time margin: {m.time_margin_sec:+.2f} s {'(makes it)' if m.time_margin_sec < 0 else '(too slow)'}")

        # Outcome
        print(f"   Expected catch probability: {m.expected_catch_probability:.1%}")
        print(f"   Opportunity difficulty: {m.opportunity_difficulty:.0f}/100 {'(routine)' if m.opportunity_difficulty < 30 else '(average)' if m.opportunity_difficulty < 60 else '(difficult)'}")
        print(f"   Result: {'✓ SUCCESS' if m.catch_successful else f'✗ FAIL ({m.failure_reason})'}")

        # Throwing (if successful)
        if m.catch_successful and m.throw_velocity_mph:
            print(f"   Throw:")
            print(f"     - Exchange time: {m.exchange_time_sec:.2f} s")
            print(f"     - Throw velocity: {m.throw_velocity_mph:.1f} mph")
            print(f"     - Throw flight time: {m.throw_flight_time_sec:.2f} s")
            if m.throw_accuracy_error_ft:
                print(f"     - Accuracy error: {m.throw_accuracy_error_ft:.1f} ft from target")

    def _print_baserunning_debug(self, m: BaserunningMetrics):
        """Print baserunning debug output with enhanced speed diagnostics"""
        print(f"\n🏃 BASERUNNING: {m.runner_name} ({m.starting_base} → {m.target_base})")

        # Runner physical profile
        print(f"   Runner Speed Profile:")
        print(f"     - Top sprint speed: {m.top_sprint_speed_fps:.1f} ft/s ({m.top_sprint_speed_fps * 0.681818:.1f} mph)")
        statcast_rating = "elite" if m.top_sprint_speed_fps > 29 else "above avg" if m.top_sprint_speed_fps > 27 else "average" if m.top_sprint_speed_fps > 25 else "below avg"
        print(f"     - Speed rating: {statcast_rating} (Statcast percentile estimate)")
        print(f"     - Acceleration: {m.acceleration_fps2:.1f} ft/s²")

        # Starting conditions
        print(f"   Starting Conditions:")
        print(f"     - Lead distance: {m.lead_distance_ft:.1f} ft off base")
        print(f"     - Jump time: {m.jump_time_sec:.2f} s (reaction)")
        print(f"     - Jump quality: {m.jump_quality.upper()}")

        # Route and efficiency
        print(f"   Route:")
        print(f"     - Distance to run: {m.distance_to_run_ft:.1f} ft")
        print(f"     - Turn efficiency: {m.turn_efficiency_pct:.1f}% (speed retention through turn)")
        avg_speed = m.distance_to_run_ft / m.actual_run_time_sec if m.actual_run_time_sec > 0 else 0
        print(f"     - Average speed: {avg_speed:.1f} ft/s during run")
        print(f"     - Actual run time: {m.actual_run_time_sec:.2f} s")

        # Decision context
        decision_icon = {"aggressive": "⚡", "conservative": "🛡️", "auto": "🤖", "coach_send": "👋", "coach_hold": "🛑"}
        decision_display = decision_icon.get(m.send_decision, "")
        print(f"   Decision: {m.send_decision.upper()} {decision_display}")
        print(f"     - Risk score: {m.risk_score:.2f} (0=safe, 1=risky)")
        print(f"     - Expected success probability: {m.expected_success_probability:.1%}")

        # Timing outcome
        print(f"   Timing Outcome:")
        print(f"     - Runner arrival: {m.runner_arrival_time_sec:.2f} s")
        print(f"     - Ball arrival: {m.ball_arrival_time_sec:.2f} s")
        print(f"     - Margin: {m.time_margin_sec:+.2f} s {'(SAFE)' if m.time_margin_sec > 0 else '(OUT)'}")

        # Defensive play (if applicable)
        if m.throw_velocity_mph:
            print(f"   Defensive Throw:")
            print(f"     - Outfielder exchange: {m.outfielder_exchange_time_sec:.2f} s")
            print(f"     - Throw velocity: {m.throw_velocity_mph:.1f} mph")
            if m.throw_accuracy_error_ft:
                print(f"     - Accuracy error: {m.throw_accuracy_error_ft:.1f} ft")

        # Final result
        result_icon = "✓" if m.advance_successful else "✗"
        print(f"   Result: {m.outcome.upper()} {result_icon}")

    def _print_fatigue_debug(self, m: PitcherFatigueMetrics):
        """Print pitcher fatigue diagnostics"""
        print(f"\n⚡ PITCHER FATIGUE: {m.pitcher_name}")
        print(f"   Pitch Count: {m.pitches_thrown} (Inning {m.current_inning}, {m.outs_recorded} outs recorded)")
        print(f"   Stamina rating: {m.stamina_rating:,}")

        # Fatigue level
        fatigue_pct = m.current_fatigue_pct
        fatigue_status = "fresh" if fatigue_pct < 20 else "good" if fatigue_pct < 40 else "tiring" if fatigue_pct < 60 else "fatigued" if fatigue_pct < 80 else "exhausted"
        print(f"   Fatigue: {fatigue_pct:.1f}% ({fatigue_status})")

        # Velocity degradation
        print(f"   Velocity:")
        print(f"     - Base (fresh): {m.base_velocity_mph:.1f} mph")
        print(f"     - Current: {m.current_velocity_mph:.1f} mph")
        print(f"     - Loss: -{m.velocity_loss_mph:.1f} mph")

        # Spin degradation
        print(f"   Spin:")
        print(f"     - Base (fresh): {m.base_spin_rpm:.0f} rpm")
        print(f"     - Current: {m.current_spin_rpm:.0f} rpm")
        print(f"     - Loss: -{m.spin_loss_rpm:.0f} rpm")

        # Command degradation
        print(f"   Command:")
        print(f"     - Base control (fresh): {m.base_command_sigma:.2f}\" std dev")
        print(f"     - Current control: {m.current_command_sigma:.2f}\" std dev")
        print(f"     - Penalty: +{m.command_penalty_pct:.1f}% worse")

        # Situational stress
        if m.runners_on_base > 0 or m.is_high_leverage:
            print(f"   Situational Factors:")
            if m.runners_on_base > 0:
                print(f"     - Runners on base: {m.runners_on_base}")
            if m.is_high_leverage:
                print(f"     - High leverage situation: YES")
            if m.stress_inning:
                print(f"     - Stress inning (>20 pitches): YES")

        # Times through order
        if m.times_through_order > 1:
            print(f"   Times Through Order: {m.times_through_order}")
            print(f"     - TTO penalty multiplier: {m.tto_penalty_multiplier:.2f}x")

        # Predicted performance
        if m.expected_whiff_rate > 0:
            print(f"   Expected Performance (with current fatigue):")
            print(f"     - Whiff rate: {m.expected_whiff_rate:.1%}")
            print(f"     - Walk rate: {m.expected_walk_rate:.1%}")
            print(f"     - Hard contact rate: {m.expected_hard_contact_rate:.1%}")

    def print_summary(self):
        """Print comprehensive summary with team splits and per-player breakdowns"""
        if not self.enabled:
            return

        print("\n" + "="*80)
        print("SIMULATION METRICS SUMMARY")
        print("="*80)

        # Split metrics by team
        self._print_team_summaries()

        # Per-pitcher breakdowns
        self._print_pitcher_summaries()

        # Per-batter breakdowns
        self._print_batter_summaries()

        # Model drift metrics
        self._print_model_drift_summary()

        print("="*80 + "\n")

    def _print_team_summaries(self):
        """Print metrics split by team"""
        if not self.pitch_metrics and not self.batted_ball_metrics:
            return

        for team in ['away', 'home']:
            team_label = team.upper()

            # Team pitching metrics
            team_pitches = [p for p in self.pitch_metrics if p.pitcher_team == team]
            if team_pitches:
                print(f"\n📊 PITCHING ({team_label} team): {len(team_pitches)} pitches")
                strikes = sum(1 for p in team_pitches if p.is_strike)
                swings = sum(1 for p in team_pitches if p.batter_swung)
                whiffs = sum(1 for p in team_pitches if p.batter_swung and p.pitch_outcome == 'swinging_strike')

                print(f"   Strike%: {100*strikes/len(team_pitches):.1f}%")
                print(f"   Swing%: {100*swings/len(team_pitches):.1f}%")
                if swings > 0:
                    print(f"   Whiff%: {100*whiffs/swings:.1f}%")

                avg_error = np.mean([p.command_error_magnitude for p in team_pitches])
                print(f"   Avg command error: {avg_error:.2f}\"")

            # Team batting metrics
            team_batted_balls = [b for b in self.batted_ball_metrics if b.batter_team == team]
            if team_batted_balls:
                print(f"\n⚾ BATTING ({team_label} team): {len(team_batted_balls)} balls in play")

                avg_ev = np.mean([b.exit_velocity_mph for b in team_batted_balls])
                avg_la = np.mean([b.launch_angle_deg for b in team_batted_balls])
                avg_dist = np.mean([b.distance_ft for b in team_batted_balls])

                print(f"   Avg EV: {avg_ev:.1f} mph | LA: {avg_la:.1f}° | Dist: {avg_dist:.1f} ft")

                barrels = sum(1 for b in team_batted_balls if b.barrel)
                hard_hit = sum(1 for b in team_batted_balls if b.hard_hit)

                print(f"   Barrels: {barrels} ({100*barrels/len(team_batted_balls):.1f}%) | Hard hit: {hard_hit} ({100*hard_hit/len(team_batted_balls):.1f}%)")

                # Hit type distribution
                gbs = sum(1 for b in team_batted_balls if b.hit_type == 'ground_ball')
                lds = sum(1 for b in team_batted_balls if b.hit_type == 'line_drive')
                fbs = sum(1 for b in team_batted_balls if b.hit_type == 'fly_ball')

                total = len(team_batted_balls)
                print(f"   GB/LD/FB: {100*gbs/total:.0f}% / {100*lds/total:.0f}% / {100*fbs/total:.0f}%")

                # Expected stats
                avg_xba = np.mean([b.expected_batting_avg for b in team_batted_balls])
                avg_xslg = np.mean([b.expected_slg for b in team_batted_balls])
                avg_xwoba = np.mean([b.expected_woba for b in team_batted_balls])

                print(f"   xBA: {avg_xba:.3f} | xSLG: {avg_xslg:.3f} | xwOBA: {avg_xwoba:.3f}")

    def _print_pitcher_summaries(self):
        """Print per-pitcher pitch-type breakdowns"""
        if not self.pitch_metrics:
            return

        # Group pitches by pitcher
        from collections import defaultdict
        pitcher_pitches = defaultdict(list)
        for p in self.pitch_metrics:
            if p.pitcher_name != "Unknown":
                pitcher_pitches[p.pitcher_name].append(p)

        if not pitcher_pitches:
            return

        print(f"\n🎯 PER-PITCHER BREAKDOWNS:")
        print("-" * 80)

        for pitcher_name in sorted(pitcher_pitches.keys()):
            pitches = pitcher_pitches[pitcher_name]
            print(f"\n  {pitcher_name} ({pitches[0].pitcher_team.upper()}) - {len(pitches)} pitches")

            # Group by pitch type
            pitch_types = defaultdict(list)
            for p in pitches:
                pitch_types[p.pitch_type].append(p)

            # Print summary for each pitch type
            for pitch_type in sorted(pitch_types.keys()):
                type_pitches = pitch_types[pitch_type]
                usage = len(type_pitches)
                usage_pct = 100 * usage / len(pitches)

                strikes = sum(1 for p in type_pitches if p.is_strike)
                strike_pct = 100 * strikes / usage if usage > 0 else 0

                swings = sum(1 for p in type_pitches if p.batter_swung)
                whiffs = sum(1 for p in type_pitches if p.batter_swung and p.pitch_outcome == 'swinging_strike')
                whiff_pct = 100 * whiffs / swings if swings > 0 else 0

                avg_velo = np.mean([p.plate_velocity_mph for p in type_pitches])
                avg_error = np.mean([p.command_error_magnitude for p in type_pitches])

                print(f"    {pitch_type:12s}: {usage:3d} ({usage_pct:4.1f}%) | Strike%: {strike_pct:4.1f} | Whiff%: {whiff_pct:4.1f} | Velo: {avg_velo:4.1f} mph | Cmd: {avg_error:4.1f}\"")

    def _print_batter_summaries(self):
        """Print per-batter contact quality summaries"""
        if not self.batted_ball_metrics:
            return

        # Group batted balls by batter
        from collections import defaultdict
        batter_balls = defaultdict(list)
        for b in self.batted_ball_metrics:
            if b.batter_name != "Unknown":
                batter_balls[b.batter_name].append(b)

        if not batter_balls:
            return

        # Only show batters with 2+ balls in play
        batters_with_enough_data = {name: balls for name, balls in batter_balls.items() if len(balls) >= 2}

        if not batters_with_enough_data:
            return

        print(f"\n🏏 PER-BATTER CONTACT QUALITY:")
        print("-" * 80)

        for team in ['away', 'home']:
            team_batters = {name: balls for name, balls in batters_with_enough_data.items()
                           if balls[0].batter_team == team}

            if not team_batters:
                continue

            print(f"\n  {team.upper()} TEAM:")

            for batter_name in sorted(team_batters.keys()):
                balls = team_batters[batter_name]

                avg_ev = np.mean([b.exit_velocity_mph for b in balls])
                avg_la = np.mean([b.launch_angle_deg for b in balls])
                avg_xba = np.mean([b.expected_batting_avg for b in balls])
                avg_xslg = np.mean([b.expected_slg for b in balls])

                barrels = sum(1 for b in balls if b.barrel)
                hard_hit = sum(1 for b in balls if b.hard_hit)

                print(f"    {batter_name:20s}: {len(balls):2d} BIP | EV: {avg_ev:5.1f} mph | LA: {avg_la:5.1f}° | xBA: {avg_xba:.3f} | xSLG: {avg_xslg:.3f} | Barrels: {barrels} | Hard: {hard_hit}")

    def _print_model_drift_summary(self):
        """Print game-level model drift indicators"""
        if not self.batted_ball_metrics and not self.expected_outcome_metrics:
            return

        print(f"\n📉 MODEL DRIFT INDICATORS (Physics Validation):")
        print("-" * 80)

        # Expected vs actual distance drift
        if self.batted_ball_metrics:
            balls_with_expected = [b for b in self.batted_ball_metrics if b.expected_distance_ft > 0]
            if balls_with_expected:
                actual_distances = [b.distance_ft for b in balls_with_expected]
                expected_distances = [b.expected_distance_ft for b in balls_with_expected]
                distance_deltas = [actual - expected for actual, expected in zip(actual_distances, expected_distances)]

                avg_expected = np.mean(expected_distances)
                avg_actual = np.mean(actual_distances)
                avg_delta = np.mean(distance_deltas)
                std_delta = np.std(distance_deltas)

                print(f"  Distance Prediction:")
                print(f"    - Mean predicted distance: {avg_expected:.1f} ft")
                print(f"    - Mean simulated distance: {avg_actual:.1f} ft")
                print(f"    - Average delta: {avg_delta:+.1f} ft ({100*avg_delta/avg_expected:+.1f}%)")
                print(f"    - Std dev of deltas: {std_delta:.1f} ft")
                print(f"    - Sample size: {len(balls_with_expected)} batted balls")

                # Identify systematic biases
                if abs(avg_delta) > 5:
                    bias_dir = "over-predicting" if avg_delta < 0 else "under-predicting"
                    print(f"    - ⚠ Systematic bias detected: {bias_dir} distance by {abs(avg_delta):.1f} ft")

        # Expected outcomes vs actual
        if self.expected_outcome_metrics:
            total_xwoba = sum(m.xwOBA for m in self.expected_outcome_metrics)
            avg_xwoba = total_xwoba / len(self.expected_outcome_metrics) if self.expected_outcome_metrics else 0

            # Calculate actual wOBA equivalent
            outcome_values = {
                'home_run': 2.0,
                'triple': 1.5,
                'double': 1.2,
                'single': 0.9,
                'walk': 0.7,
                'error': 0.5,
                'fly_out': 0.0,
                'ground_out': 0.0,
                'line_out': 0.0,
                'strikeout': -0.3,
            }
            actual_values = [outcome_values.get(m.actual_outcome, 0.0) for m in self.expected_outcome_metrics]
            avg_actual_value = np.mean(actual_values) if actual_values else 0

            print(f"\n  Expected vs Actual Outcomes:")
            print(f"    - Average xwOBA: {avg_xwoba:.3f}")
            print(f"    - Average actual value: {avg_actual_value:.3f}")
            print(f"    - Delta: {avg_actual_value - avg_xwoba:+.3f}")
            print(f"    - Sample size: {len(self.expected_outcome_metrics)} PAs")

            # Count outcome mismatches
            better_count = sum(1 for m in self.expected_outcome_metrics if m.outcome_vs_expected in ['better', 'much_better'])
            worse_count = sum(1 for m in self.expected_outcome_metrics if m.outcome_vs_expected in ['worse', 'much_worse'])
            expected_count = sum(1 for m in self.expected_outcome_metrics if m.outcome_vs_expected == 'expected')

            print(f"    - Better than expected: {better_count} ({100*better_count/len(self.expected_outcome_metrics):.1f}%)")
            print(f"    - As expected: {expected_count} ({100*expected_count/len(self.expected_outcome_metrics):.1f}%)")
            print(f"    - Worse than expected: {worse_count} ({100*worse_count/len(self.expected_outcome_metrics):.1f}%)")

        # Fielding performance checks
        if self.fielding_metrics:
            routine_plays = [f for f in self.fielding_metrics if f.expected_catch_probability > 0.90]
            if routine_plays:
                routine_success = sum(1 for f in routine_plays if f.catch_successful)
                routine_total = len(routine_plays)
                routine_pct = 100 * routine_success / routine_total if routine_total > 0 else 0

                print(f"\n  Fielding Performance:")
                print(f"    - Routine plays (>90% catch prob): {routine_success}/{routine_total} ({routine_pct:.1f}%)")

                if routine_pct < 95:
                    print(f"    - ⚠ Warning: Fielders missing routine plays at high rate")

            # Outlier high-EV outs
            high_ev_outs = [b for b in self.batted_ball_metrics
                           if b.exit_velocity_mph > 105 and b.actual_outcome in ['fly_out', 'line_out', 'ground_out']]
            if high_ev_outs:
                print(f"    - Outlier high-EV outs (>105 mph EV): {len(high_ev_outs)}")
                if len(high_ev_outs) > 2:
                    print(f"    - ℹ Notable: {len(high_ev_outs)} very hard-hit balls resulted in outs")

        print()

    def export_csv(self, filename: str):
        """Export all metrics to CSV file for external analysis"""
        import csv

        # Export pitch metrics
        if self.pitch_metrics:
            with open(f"{filename}_pitches.csv", 'w', newline='') as f:
                writer = csv.DictWriter(f, fieldnames=[
                    'sequence', 'type', 'release_velo', 'plate_velo', 'spin_rpm',
                    'h_location', 'v_location', 'v_break', 'h_break',
                    'command_error', 'outcome', 'swung'
                ])
                writer.writeheader()
                for p in self.pitch_metrics:
                    writer.writerow({
                        'sequence': p.sequence_index,
                        'type': p.pitch_type,
                        'release_velo': p.release_velocity_mph,
                        'plate_velo': p.plate_velocity_mph,
                        'spin_rpm': p.spin_rpm,
                        'h_location': p.plate_location[0],
                        'v_location': p.plate_location[1],
                        'v_break': p.vertical_break_inches,
                        'h_break': p.horizontal_break_inches,
                        'command_error': p.command_error_magnitude,
                        'outcome': p.pitch_outcome,
                        'swung': p.batter_swung
                    })

        # Export batted ball metrics
        if self.batted_ball_metrics:
            with open(f"{filename}_batted_balls.csv", 'w', newline='') as f:
                writer = csv.DictWriter(f, fieldnames=[
                    'ev', 'la', 'spray', 'distance', 'hang_time',
                    'backspin', 'sidespin', 'hit_type', 'hard_hit', 'barrel'
                ])
                writer.writeheader()
                for b in self.batted_ball_metrics:
                    writer.writerow({
                        'ev': b.exit_velocity_mph,
                        'la': b.launch_angle_deg,
                        'spray': b.spray_angle_deg,
                        'distance': b.distance_ft,
                        'hang_time': b.hang_time_sec,
                        'backspin': b.backspin_rpm,
                        'sidespin': b.sidespin_rpm,
                        'hit_type': b.hit_type,
                        'hard_hit': b.hard_hit,
                        'barrel': b.barrel
                    })


# ============================================================================
# H. CONVENIENCE FUNCTIONS
# ============================================================================

def create_pitch_metrics_from_simulation(pitch_data: Dict, sequence_index: int) -> PitchMetrics:
    """
    Create PitchMetrics from existing simulation pitch_data dict.

    Helper function to integrate with existing at_bat.py code.
    """
    return PitchMetrics(
        sequence_index=sequence_index,
        pitch_type=pitch_data.get('pitch_type', 'unknown'),
        count_before=pitch_data.get('count_before', (0, 0)),
        release_point=(0.0, 0.0, 0.0),  # TODO: Extract from pitch simulation
        release_velocity_mph=pitch_data.get('velocity_release', 0.0),
        release_extension_ft=0.0,  # TODO: Add to pitch data
        spin_rpm=0.0,  # TODO: Add to pitch data
        spin_axis_deg=(0.0, 0.0),
        spin_efficiency=0.0,
        plate_velocity_mph=pitch_data.get('velocity_plate', 0.0),
        plate_location=pitch_data.get('final_location', (0.0, 0.0)),
        vertical_approach_angle_deg=0.0,  # TODO: Extract from pitch result
        vertical_break_inches=pitch_data.get('break', (0.0, 0.0))[0],
        horizontal_break_inches=pitch_data.get('break', (0.0, 0.0))[1],
        total_break_inches=0.0,
        target_location=pitch_data.get('target_location', (0.0, 0.0)),
        command_error=(0.0, 0.0),
        command_error_magnitude=0.0,
        batter_swung=pitch_data.get('swing', False),
        pitch_outcome=pitch_data.get('pitch_outcome', 'unknown'),
        is_strike=pitch_data.get('is_strike', False),
        flight_time_ms=0.0,
    )


def create_batted_ball_metrics_from_contact(contact_result: Dict) -> BattedBallMetrics:
    """
    Create BattedBallMetrics from existing contact_result dict.

    Helper function to integrate with existing at_bat.py code.
    """
    trajectory = contact_result.get('trajectory')

    return BattedBallMetrics(
        bat_speed_mph=0.0,  # TODO: Add to contact result
        pitch_speed_mph=0.0,
        collision_efficiency_q=contact_result.get('collision_efficiency_q', 0.0),
        exit_velocity_mph=contact_result.get('exit_velocity', 0.0),
        launch_angle_deg=contact_result.get('launch_angle', 0.0),
        spray_angle_deg=contact_result.get('spray_angle', 0.0),
        backspin_rpm=contact_result.get('backspin_rpm', 0.0),
        sidespin_rpm=contact_result.get('sidespin_rpm', 0.0),
        distance_ft=contact_result.get('distance', 0.0),
        hang_time_sec=contact_result.get('hang_time', 0.0),
        apex_height_ft=contact_result.get('peak_height', 0.0),
        landing_x_ft=trajectory.landing_x if trajectory else 0.0,
        landing_y_ft=trajectory.landing_y if trajectory else 0.0,
    )
