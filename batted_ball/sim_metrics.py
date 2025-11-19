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
    command_error: Tuple[float, float]     # (h_error, v_error) in inches
    command_error_magnitude: float         # Total error magnitude

    # Decision probabilities (BEFORE outcome)
    expected_whiff_prob: float = 0.0
    expected_chase_prob: float = 0.0
    expected_swing_prob: float = 0.0
    expected_contact_prob: float = 0.0

    # Actual outcome
    batter_swung: bool = False
    pitch_outcome: str = "unknown"  # 'ball', 'called_strike', 'swinging_strike', 'foul', 'contact'
    is_strike: bool = False

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
    # Contact mechanics
    bat_speed_mph: float
    pitch_speed_mph: float
    collision_efficiency_q: float  # The q parameter from collision physics

    # Launch conditions
    exit_velocity_mph: float
    launch_angle_deg: float
    spray_angle_deg: float  # -45 to +45, 0 = center field

    # Spin characteristics
    backspin_rpm: float  # Positive = backspin
    sidespin_rpm: float  # Positive = toward pull side

    # Trajectory results
    distance_ft: float
    hang_time_sec: float
    apex_height_ft: float

    # Landing coordinates (field coordinates, home = 0,0)
    landing_x_ft: float  # Horizontal (positive = right field for RHH)
    landing_y_ft: float  # Depth (positive = toward outfield)

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
    is_home_run: bool = False

    # Hit classification
    hit_type: str = "unknown"  # 'ground_ball', 'line_drive', 'fly_ball', 'popup'
    hard_hit: bool = False  # EV >= 95 mph
    barrel: bool = False    # Optimal EV + LA combo

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

    def record_fatigue(self, metrics: PitcherFatigueMetrics):
        """Record pitcher fatigue metrics"""
        if self.enabled:
            self.fatigue_metrics.append(metrics)

    def record_expected_outcome(self, metrics: ExpectedOutcomeMetrics):
        """Record expected vs actual outcome"""
        if self.enabled:
            metrics.calculate_delta()
            self.expected_outcome_metrics.append(metrics)

    def _print_pitch_debug(self, m: PitchMetrics):
        """Print pitch debug output"""
        print(f"\n📊 PITCH #{m.sequence_index}: {m.pitch_type} ({m.count_before[0]}-{m.count_before[1]})")
        print(f"   Release: {m.release_velocity_mph:.1f} mph, {m.spin_rpm:.0f} rpm")
        print(f"   Plate: {m.plate_velocity_mph:.1f} mph @ ({m.plate_location[0]:+.1f}\", {m.plate_location[1]:.1f}\")")
        print(f"   Break: V={m.vertical_break_inches:+.1f}\", H={m.horizontal_break_inches:+.1f}\"")
        print(f"   Command error: {m.command_error_magnitude:.2f}\" (target: {m.target_location})")
        print(f"   Expected: Swing={m.expected_swing_prob:.1%}, Whiff={m.expected_whiff_prob:.1%}")
        print(f"   Outcome: {m.pitch_outcome} {'(swung)' if m.batter_swung else '(taken)'}")

    def _print_swing_debug(self, m: SwingDecisionMetrics):
        """Print swing decision debug output"""
        print(f"\n🎯 SWING DECISION:")
        print(f"   Location: {m.pitch_location} ({m.pitch_zone_rating})")
        print(f"   Swing prob: {m.swing_probability:.1%}")
        print(f"   Expected outcomes: Whiff={m.expected_whiff_pct:.1%}, Solid={m.expected_solid_pct:.1%}")
        if m.swung:
            print(f"   Timing error: {m.swing_timing_error_ms:+.1f} ms")
            print(f"   Contact offset: {m.total_contact_offset:.2f}\"")
            print(f"   Result: {m.contact_quality if m.contact_made else 'WHIFF'}")

    def _print_batted_ball_debug(self, m: BattedBallMetrics):
        """Print batted ball debug output"""
        print(f"\n⚾ BATTED BALL: {m.hit_type.upper()}")
        print(f"   EV: {m.exit_velocity_mph:.1f} mph, LA: {m.launch_angle_deg:.1f}°")
        print(f"   Spin: {m.backspin_rpm:.0f} rpm backspin, {m.sidespin_rpm:+.0f} rpm sidespin")
        print(f"   Distance: {m.distance_ft:.1f} ft (apex: {m.apex_height_ft:.1f} ft)")
        print(f"   Landing: ({m.landing_x_ft:.1f}, {m.landing_y_ft:.1f})")
        print(f"   Quality: {'BARREL' if m.barrel else 'HARD' if m.hard_hit else 'MEDIUM'}")

    def _print_fielding_debug(self, m: FieldingMetrics):
        """Print fielding debug output"""
        print(f"\n🧤 FIELDING: {m.fielder_name} ({m.fielder_position})")
        print(f"   Starting: ({m.starting_position[0]:.1f}, {m.starting_position[1]:.1f})")
        print(f"   Distance: {m.distance_to_ball_ft:.1f} ft")
        print(f"   Route: {m.route_efficiency_pct:.0f}% efficient")
        print(f"   Speed: {m.actual_avg_speed_fps:.1f} fps (max: {m.top_sprint_speed_fps:.1f})")
        print(f"   Timing: {m.time_margin_sec:+.2f}s margin")
        print(f"   Catch prob: {m.expected_catch_probability:.1%}")
        print(f"   Result: {'SUCCESS' if m.catch_successful else f'FAIL ({m.failure_reason})'}")

    def print_summary(self):
        """Print complete summary of collected metrics"""
        if not self.enabled:
            return

        print("\n" + "="*80)
        print("SIMULATION METRICS SUMMARY")
        print("="*80)

        # Pitch summary
        if self.pitch_metrics:
            print(f"\n📊 PITCHES: {len(self.pitch_metrics)} total")
            strikes = sum(1 for p in self.pitch_metrics if p.is_strike)
            swings = sum(1 for p in self.pitch_metrics if p.batter_swung)
            print(f"   Strikes: {strikes}/{len(self.pitch_metrics)} ({100*strikes/len(self.pitch_metrics):.1f}%)")
            print(f"   Swings: {swings}/{len(self.pitch_metrics)} ({100*swings/len(self.pitch_metrics):.1f}%)")

            # Average command error
            avg_error = np.mean([p.command_error_magnitude for p in self.pitch_metrics])
            print(f"   Avg command error: {avg_error:.2f}\"")

        # Batted ball summary
        if self.batted_ball_metrics:
            print(f"\n⚾ BATTED BALLS: {len(self.batted_ball_metrics)} total")

            avg_ev = np.mean([b.exit_velocity_mph for b in self.batted_ball_metrics])
            avg_la = np.mean([b.launch_angle_deg for b in self.batted_ball_metrics])
            avg_dist = np.mean([b.distance_ft for b in self.batted_ball_metrics])

            print(f"   Avg EV: {avg_ev:.1f} mph")
            print(f"   Avg LA: {avg_la:.1f}°")
            print(f"   Avg distance: {avg_dist:.1f} ft")

            barrels = sum(1 for b in self.batted_ball_metrics if b.barrel)
            hard_hit = sum(1 for b in self.batted_ball_metrics if b.hard_hit)

            print(f"   Barrels: {barrels} ({100*barrels/len(self.batted_ball_metrics):.1f}%)")
            print(f"   Hard hit: {hard_hit} ({100*hard_hit/len(self.batted_ball_metrics):.1f}%)")

            # Hit type distribution
            gbs = sum(1 for b in self.batted_ball_metrics if b.hit_type == 'ground_ball')
            lds = sum(1 for b in self.batted_ball_metrics if b.hit_type == 'line_drive')
            fbs = sum(1 for b in self.batted_ball_metrics if b.hit_type == 'fly_ball')

            total = len(self.batted_ball_metrics)
            print(f"   GB/LD/FB: {100*gbs/total:.0f}% / {100*lds/total:.0f}% / {100*fbs/total:.0f}%")

        # Fielding summary
        if self.fielding_metrics:
            print(f"\n🧤 FIELDING PLAYS: {len(self.fielding_metrics)} total")
            successes = sum(1 for f in self.fielding_metrics if f.catch_successful)
            print(f"   Successful: {successes}/{len(self.fielding_metrics)} ({100*successes/len(self.fielding_metrics):.1f}%)")

            avg_prob = np.mean([f.expected_catch_probability for f in self.fielding_metrics])
            print(f"   Avg catch probability: {avg_prob:.1%}")

            errors = sum(1 for f in self.fielding_metrics if f.is_error)
            if errors > 0:
                print(f"   Errors: {errors}")

        print("="*80 + "\n")

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
