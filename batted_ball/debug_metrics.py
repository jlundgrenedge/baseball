"""
Debug Metrics Collection for V2.0 Development

This module provides detailed logging and metrics collection for understanding
where K%, BB%, and HR/FB are generated in the simulation.

Purpose:
- Track pitch intention decisions and outcomes
- Monitor swing decisions and reasoning
- Log whiff calculations and factors
- Record collision physics details
- Capture flight trajectory information
- Enable root cause analysis for MLB realism issues

Usage:
    from batted_ball.debug_metrics import DebugMetricsCollector

    collector = DebugMetricsCollector()
    collector.log_pitch_intention(...)
    collector.save_results("output.json")
"""

from dataclasses import dataclass, field, asdict
from typing import Dict, List, Optional, Any
from collections import defaultdict
import json
from pathlib import Path


@dataclass
class PitchIntentionLog:
    """Record of a single pitch intention decision"""
    game_id: int
    inning: int
    balls: int
    strikes: int
    outs: int
    pitch_type: str
    intention: str  # 'strike_looking', 'strike_competitive', 'strike_corner', 'waste_chase', 'ball_intentional'
    target_x: float  # Target horizontal location (inches from center)
    target_z: float  # Target vertical location (inches from ground)
    actual_x: float  # Actual horizontal location after command error
    actual_z: float  # Actual vertical location after command error
    is_in_zone: bool  # Whether final location is in strike zone
    command_error_x: float  # Horizontal error (inches)
    command_error_z: float  # Vertical error (inches)
    pitcher_control: float  # Pitcher's control rating (0-100k)
    pitcher_command_sigma: float  # Command error std dev (inches)


@dataclass
class SwingDecisionLog:
    """Record of a single swing decision"""
    game_id: int
    inning: int
    balls: int
    strikes: int
    outs: int
    pitch_type: str
    pitch_x: float
    pitch_z: float
    is_in_zone: bool
    distance_from_zone: float  # For out-of-zone pitches (inches)

    # Decision factors
    base_swing_prob: float  # Before modifiers
    discipline_modifier: float  # From batter discipline
    reaction_modifier: float  # From reaction time
    velocity_modifier: float  # From pitch velocity
    pitch_type_modifier: float  # Breaking ball adjustment
    count_modifier: float  # Two-strike protection, etc.
    final_swing_prob: float  # After all modifiers

    # Outcome
    did_swing: bool

    # Batter attributes
    batter_discipline: float  # 0-100k
    batter_reaction_time_ms: float


@dataclass
class WhiffLog:
    """Record of a whiff calculation"""
    game_id: int
    inning: int
    balls: int
    strikes: int
    pitch_type: str
    pitch_velocity_mph: float
    pitch_movement_total: float  # Total break (inches)

    # Whiff calculation factors
    base_whiff_rate: float  # By pitch type
    velocity_multiplier: float  # Higher velocity → more whiffs
    movement_multiplier: float  # More break → more whiffs
    contact_factor: float  # From batter barrel accuracy (ISSUE: double-dipping)
    stuff_multiplier: float  # From pitcher stuff rating
    final_whiff_prob: float  # Combined probability

    # Outcome
    did_whiff: bool

    # Attributes
    batter_barrel_accuracy_mm: float  # RMS error
    pitcher_stuff_rating: float  # 0-100k


@dataclass
class CollisionLog:
    """Record of bat-ball collision physics"""
    game_id: int
    inning: int
    pitch_velocity_mph: float
    bat_speed_mph: float

    # Contact point
    impact_location_vertical_in: float  # Vertical offset from ball center
    impact_location_horizontal_in: float  # Horizontal offset on bat barrel
    distance_from_sweet_spot_in: float  # Total distance from optimal

    # Collision efficiency
    base_collision_efficiency_q: float  # Material constant (wood ~0.03)
    sweet_spot_penalty: float  # Reduction from off-center hit
    effective_q: float  # Final efficiency used

    # Outputs
    exit_velocity_mph: float
    launch_angle_deg: float
    backspin_rpm: float
    sidespin_rpm: float
    spray_angle_deg: float
    contact_quality: str  # 'barrel', 'solid', 'weak', etc.

    # Swing parameters
    attack_angle_deg: float  # Batter's swing plane
    swing_type: str  # 'normal', 'power', 'contact' (for future v2)


@dataclass
class FlightLog:
    """Record of batted ball flight trajectory"""
    game_id: int
    inning: int

    # Initial conditions
    exit_velocity_mph: float
    launch_angle_deg: float
    spray_angle_deg: float
    backspin_rpm: float
    sidespin_rpm: float

    # Flight parameters
    drag_coefficient: float
    lift_coefficient: float
    altitude_ft: float
    temperature_f: float

    # Trajectory outputs
    distance_ft: float
    hang_time_sec: float
    peak_height_ft: float
    final_x_ft: float  # Landing position
    final_y_ft: float

    # Classification
    batted_ball_type: str  # 'ground_ball', 'line_drive', 'fly_ball', 'pop_up'
    is_home_run: bool
    fielding_outcome: str  # 'caught', 'dropped', 'landed_hit', 'out_of_park'


@dataclass
class PlateAppearanceOutcome:
    """Summary of complete plate appearance"""
    game_id: int
    inning: int
    batter_name: str
    pitcher_name: str

    # Count progression
    initial_count: tuple  # (balls, strikes)
    final_count: tuple
    num_pitches: int
    num_fouls_with_2_strikes: int

    # Outcome
    result: str  # 'strikeout_swinging', 'strikeout_looking', 'walk', 'single', 'double', etc.
    num_swings: int
    num_whiffs: int
    num_fouls: int
    made_contact: bool

    # If ball in play
    exit_velocity_mph: Optional[float] = None
    launch_angle_deg: Optional[float] = None
    distance_ft: Optional[float] = None


class DebugMetricsCollector:
    """
    Collects detailed metrics for analyzing MLB realism issues.

    This class is designed to be lightweight and can be disabled for
    production simulations. When enabled, it captures granular data
    about every pitch, swing, contact, and flight.
    """

    def __init__(self, enabled: bool = True):
        """
        Initialize metrics collector.

        Parameters
        ----------
        enabled : bool
            If False, all logging calls are no-ops (zero overhead)
        """
        self.enabled = enabled

        if enabled:
            # Detailed logs
            self.pitch_intentions: List[PitchIntentionLog] = []
            self.swing_decisions: List[SwingDecisionLog] = []
            self.whiff_logs: List[WhiffLog] = []
            self.collision_logs: List[CollisionLog] = []
            self.flight_logs: List[FlightLog] = []
            self.plate_appearances: List[PlateAppearanceOutcome] = []

            # Aggregated statistics
            self.stats = {
                'pitch_intentions': defaultdict(int),
                'swing_by_zone': defaultdict(int),
                'whiff_by_pitch_type': defaultdict(lambda: {'total': 0, 'whiffs': 0}),
                'contact_quality': defaultdict(int),
                'batted_ball_types': defaultdict(int),
                'pa_outcomes': defaultdict(int),
            }

            # Current game/PA tracking
            self.current_game_id = 0
            self.current_pa_pitches = []

    def start_game(self, game_id: int):
        """Mark the start of a new game"""
        if not self.enabled:
            return
        self.current_game_id = game_id

    def start_plate_appearance(self):
        """Mark the start of a new plate appearance"""
        if not self.enabled:
            return
        self.current_pa_pitches = []

    def log_pitch_intention(
        self,
        inning: int,
        balls: int,
        strikes: int,
        outs: int,
        pitch_type: str,
        intention: str,
        target_x: float,
        target_z: float,
        actual_x: float,
        actual_z: float,
        is_in_zone: bool,
        pitcher_control: float,
        pitcher_command_sigma: float
    ):
        """Log a pitch intention decision"""
        if not self.enabled:
            return

        log = PitchIntentionLog(
            game_id=self.current_game_id,
            inning=inning,
            balls=balls,
            strikes=strikes,
            outs=outs,
            pitch_type=pitch_type,
            intention=intention,
            target_x=target_x,
            target_z=target_z,
            actual_x=actual_x,
            actual_z=actual_z,
            is_in_zone=is_in_zone,
            command_error_x=actual_x - target_x,
            command_error_z=actual_z - target_z,
            pitcher_control=pitcher_control,
            pitcher_command_sigma=pitcher_command_sigma
        )

        self.pitch_intentions.append(log)
        self.stats['pitch_intentions'][intention] += 1

        # Track zone vs out-of-zone by intention
        key = f"{intention}_{'zone' if is_in_zone else 'ball'}"
        self.stats['pitch_intentions'][key] += 1

    def log_swing_decision(
        self,
        inning: int,
        balls: int,
        strikes: int,
        outs: int,
        pitch_type: str,
        pitch_x: float,
        pitch_z: float,
        is_in_zone: bool,
        distance_from_zone: float,
        base_swing_prob: float,
        discipline_modifier: float,
        reaction_modifier: float,
        velocity_modifier: float,
        pitch_type_modifier: float,
        count_modifier: float,
        final_swing_prob: float,
        did_swing: bool,
        batter_discipline: float,
        batter_reaction_time_ms: float
    ):
        """Log a swing decision"""
        if not self.enabled:
            return

        log = SwingDecisionLog(
            game_id=self.current_game_id,
            inning=inning,
            balls=balls,
            strikes=strikes,
            outs=outs,
            pitch_type=pitch_type,
            pitch_x=pitch_x,
            pitch_z=pitch_z,
            is_in_zone=is_in_zone,
            distance_from_zone=distance_from_zone,
            base_swing_prob=base_swing_prob,
            discipline_modifier=discipline_modifier,
            reaction_modifier=reaction_modifier,
            velocity_modifier=velocity_modifier,
            pitch_type_modifier=pitch_type_modifier,
            count_modifier=count_modifier,
            final_swing_prob=final_swing_prob,
            did_swing=did_swing,
            batter_discipline=batter_discipline,
            batter_reaction_time_ms=batter_reaction_time_ms
        )

        self.swing_decisions.append(log)

        # Aggregate stats
        zone_key = 'in_zone' if is_in_zone else 'out_of_zone'
        self.stats['swing_by_zone'][f"{zone_key}_total"] += 1
        if did_swing:
            self.stats['swing_by_zone'][f"{zone_key}_swings"] += 1

    def log_whiff(
        self,
        inning: int,
        balls: int,
        strikes: int,
        pitch_type: str,
        pitch_velocity_mph: float,
        pitch_movement_total: float,
        base_whiff_rate: float,
        velocity_multiplier: float,
        movement_multiplier: float,
        contact_factor: float,
        stuff_multiplier: float,
        final_whiff_prob: float,
        did_whiff: bool,
        batter_barrel_accuracy_mm: float,
        pitcher_stuff_rating: float
    ):
        """Log a whiff calculation"""
        if not self.enabled:
            return

        log = WhiffLog(
            game_id=self.current_game_id,
            inning=inning,
            balls=balls,
            strikes=strikes,
            pitch_type=pitch_type,
            pitch_velocity_mph=pitch_velocity_mph,
            pitch_movement_total=pitch_movement_total,
            base_whiff_rate=base_whiff_rate,
            velocity_multiplier=velocity_multiplier,
            movement_multiplier=movement_multiplier,
            contact_factor=contact_factor,
            stuff_multiplier=stuff_multiplier,
            final_whiff_prob=final_whiff_prob,
            did_whiff=did_whiff,
            batter_barrel_accuracy_mm=batter_barrel_accuracy_mm,
            pitcher_stuff_rating=pitcher_stuff_rating
        )

        self.whiff_logs.append(log)

        # Aggregate by pitch type
        self.stats['whiff_by_pitch_type'][pitch_type]['total'] += 1
        if did_whiff:
            self.stats['whiff_by_pitch_type'][pitch_type]['whiffs'] += 1

    def log_collision(
        self,
        inning: int,
        pitch_velocity_mph: float,
        bat_speed_mph: float,
        impact_location_vertical_in: float,
        impact_location_horizontal_in: float,
        distance_from_sweet_spot_in: float,
        base_collision_efficiency_q: float,
        sweet_spot_penalty: float,
        effective_q: float,
        exit_velocity_mph: float,
        launch_angle_deg: float,
        backspin_rpm: float,
        sidespin_rpm: float,
        spray_angle_deg: float,
        contact_quality: str,
        attack_angle_deg: float,
        swing_type: str = 'normal'
    ):
        """Log a bat-ball collision"""
        if not self.enabled:
            return

        log = CollisionLog(
            game_id=self.current_game_id,
            inning=inning,
            pitch_velocity_mph=pitch_velocity_mph,
            bat_speed_mph=bat_speed_mph,
            impact_location_vertical_in=impact_location_vertical_in,
            impact_location_horizontal_in=impact_location_horizontal_in,
            distance_from_sweet_spot_in=distance_from_sweet_spot_in,
            base_collision_efficiency_q=base_collision_efficiency_q,
            sweet_spot_penalty=sweet_spot_penalty,
            effective_q=effective_q,
            exit_velocity_mph=exit_velocity_mph,
            launch_angle_deg=launch_angle_deg,
            backspin_rpm=backspin_rpm,
            sidespin_rpm=sidespin_rpm,
            spray_angle_deg=spray_angle_deg,
            contact_quality=contact_quality,
            attack_angle_deg=attack_angle_deg,
            swing_type=swing_type
        )

        self.collision_logs.append(log)
        self.stats['contact_quality'][contact_quality] += 1

    def log_flight(
        self,
        inning: int,
        exit_velocity_mph: float,
        launch_angle_deg: float,
        spray_angle_deg: float,
        backspin_rpm: float,
        sidespin_rpm: float,
        drag_coefficient: float,
        lift_coefficient: float,
        altitude_ft: float,
        temperature_f: float,
        distance_ft: float,
        hang_time_sec: float,
        peak_height_ft: float,
        final_x_ft: float,
        final_y_ft: float,
        batted_ball_type: str,
        is_home_run: bool,
        fielding_outcome: str
    ):
        """Log a batted ball flight"""
        if not self.enabled:
            return

        log = FlightLog(
            game_id=self.current_game_id,
            inning=inning,
            exit_velocity_mph=exit_velocity_mph,
            launch_angle_deg=launch_angle_deg,
            spray_angle_deg=spray_angle_deg,
            backspin_rpm=backspin_rpm,
            sidespin_rpm=sidespin_rpm,
            drag_coefficient=drag_coefficient,
            lift_coefficient=lift_coefficient,
            altitude_ft=altitude_ft,
            temperature_f=temperature_f,
            distance_ft=distance_ft,
            hang_time_sec=hang_time_sec,
            peak_height_ft=peak_height_ft,
            final_x_ft=final_x_ft,
            final_y_ft=final_y_ft,
            batted_ball_type=batted_ball_type,
            is_home_run=is_home_run,
            fielding_outcome=fielding_outcome
        )

        self.flight_logs.append(log)
        self.stats['batted_ball_types'][batted_ball_type] += 1

    def log_plate_appearance_outcome(
        self,
        inning: int,
        batter_name: str,
        pitcher_name: str,
        initial_count: tuple,
        final_count: tuple,
        num_pitches: int,
        num_fouls_with_2_strikes: int,
        result: str,
        num_swings: int,
        num_whiffs: int,
        num_fouls: int,
        made_contact: bool,
        exit_velocity_mph: Optional[float] = None,
        launch_angle_deg: Optional[float] = None,
        distance_ft: Optional[float] = None
    ):
        """Log a complete plate appearance outcome"""
        if not self.enabled:
            return

        outcome = PlateAppearanceOutcome(
            game_id=self.current_game_id,
            inning=inning,
            batter_name=batter_name,
            pitcher_name=pitcher_name,
            initial_count=initial_count,
            final_count=final_count,
            num_pitches=num_pitches,
            num_fouls_with_2_strikes=num_fouls_with_2_strikes,
            result=result,
            num_swings=num_swings,
            num_whiffs=num_whiffs,
            num_fouls=num_fouls,
            made_contact=made_contact,
            exit_velocity_mph=exit_velocity_mph,
            launch_angle_deg=launch_angle_deg,
            distance_ft=distance_ft
        )

        self.plate_appearances.append(outcome)
        self.stats['pa_outcomes'][result] += 1

    def get_summary_stats(self) -> Dict[str, Any]:
        """
        Get aggregated summary statistics.

        Returns
        -------
        dict
            Summary statistics for analysis
        """
        if not self.enabled:
            return {}

        summary = {
            'total_games': self.current_game_id,
            'total_plate_appearances': len(self.plate_appearances),
            'total_pitches': len(self.pitch_intentions),
            'total_swings': len([s for s in self.swing_decisions if s.did_swing]),
            'total_whiffs': len([w for w in self.whiff_logs if w.did_whiff]),
            'total_contacts': len(self.collision_logs),
            'total_flights': len(self.flight_logs),
        }

        # Pitch intention breakdown
        if self.pitch_intentions:
            summary['pitch_intentions'] = dict(self.stats['pitch_intentions'])

            # Calculate zone rates by intention
            for intention in ['strike_looking', 'strike_competitive', 'strike_corner', 'waste_chase', 'ball_intentional']:
                total_key = intention
                zone_key = f"{intention}_zone"
                if self.stats['pitch_intentions'][total_key] > 0:
                    zone_rate = self.stats['pitch_intentions'][zone_key] / self.stats['pitch_intentions'][total_key]
                    summary['pitch_intentions'][f"{intention}_zone_rate"] = zone_rate

        # Swing rates
        if self.swing_decisions:
            summary['swing_rates'] = dict(self.stats['swing_by_zone'])

            in_zone_total = self.stats['swing_by_zone'].get('in_zone_total', 0)
            in_zone_swings = self.stats['swing_by_zone'].get('in_zone_swings', 0)
            out_zone_total = self.stats['swing_by_zone'].get('out_of_zone_total', 0)
            out_zone_swings = self.stats['swing_by_zone'].get('out_of_zone_swings', 0)

            if in_zone_total > 0:
                summary['swing_rates']['in_zone_pct'] = in_zone_swings / in_zone_total
            if out_zone_total > 0:
                summary['swing_rates']['out_of_zone_pct'] = out_zone_swings / out_zone_total

        # Whiff rates by pitch type
        if self.whiff_logs:
            summary['whiff_rates'] = {}
            for pitch_type, data in self.stats['whiff_by_pitch_type'].items():
                if data['total'] > 0:
                    summary['whiff_rates'][pitch_type] = {
                        'total': data['total'],
                        'whiffs': data['whiffs'],
                        'whiff_rate': data['whiffs'] / data['total']
                    }

        # Contact quality distribution
        if self.collision_logs:
            summary['contact_quality'] = dict(self.stats['contact_quality'])
            total_contacts = sum(self.stats['contact_quality'].values())
            summary['contact_quality']['total'] = total_contacts
            for quality, count in self.stats['contact_quality'].items():
                summary['contact_quality'][f"{quality}_pct"] = count / total_contacts if total_contacts > 0 else 0

        # Batted ball types
        if self.flight_logs:
            summary['batted_ball_types'] = dict(self.stats['batted_ball_types'])
            total_balls = sum(self.stats['batted_ball_types'].values())
            for bb_type, count in self.stats['batted_ball_types'].items():
                summary['batted_ball_types'][f"{bb_type}_pct"] = count / total_balls if total_balls > 0 else 0

        # PA outcomes
        if self.plate_appearances:
            summary['pa_outcomes'] = dict(self.stats['pa_outcomes'])
            total_pas = len(self.plate_appearances)

            # Calculate key rates
            strikeouts = sum(1 for pa in self.plate_appearances if 'strikeout' in pa.result)
            walks = sum(1 for pa in self.plate_appearances if pa.result == 'walk')

            summary['pa_outcomes']['k_rate'] = strikeouts / total_pas if total_pas > 0 else 0
            summary['pa_outcomes']['bb_rate'] = walks / total_pas if total_pas > 0 else 0

        return summary

    def save_results(self, output_path: str, include_detailed: bool = True):
        """
        Save collected metrics to JSON file.

        Parameters
        ----------
        output_path : str
            Path to output JSON file
        include_detailed : bool
            If True, include all detailed logs (large file)
            If False, only include summary statistics
        """
        if not self.enabled:
            print("Debug metrics collection is disabled")
            return

        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)

        data = {
            'summary': self.get_summary_stats(),
        }

        if include_detailed:
            data['detailed'] = {
                'pitch_intentions': [asdict(log) for log in self.pitch_intentions],
                'swing_decisions': [asdict(log) for log in self.swing_decisions],
                'whiff_logs': [asdict(log) for log in self.whiff_logs],
                'collision_logs': [asdict(log) for log in self.collision_logs],
                'flight_logs': [asdict(log) for log in self.flight_logs],
                'plate_appearances': [asdict(pa) for pa in self.plate_appearances],
            }

        with open(output_path, 'w') as f:
            json.dump(data, f, indent=2)

        print(f"Debug metrics saved to: {output_path}")
        print(f"  Total games: {self.current_game_id}")
        print(f"  Total plate appearances: {len(self.plate_appearances)}")
        print(f"  Total pitches: {len(self.pitch_intentions)}")
        print(f"  File size: {output_path.stat().st_size / 1024:.1f} KB")
