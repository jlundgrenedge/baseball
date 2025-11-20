"""
Series-level metrics aggregation for multi-game simulations.

This module provides comprehensive statistics tracking across a series of games,
including MLB benchmarks and realism checks with larger sample sizes.
"""

from dataclasses import dataclass, field
from typing import List, Dict, Optional
from collections import defaultdict
import numpy as np


@dataclass
class PitchingMetrics:
    """Aggregate pitching statistics for a series"""
    # Basic counting stats
    innings_pitched: float = 0.0
    hits_allowed: int = 0
    runs_allowed: int = 0
    earned_runs: int = 0
    walks: int = 0
    strikeouts: int = 0
    home_runs_allowed: int = 0
    batters_faced: int = 0
    pitches_thrown: int = 0

    # Pitch type tracking
    pitch_type_counts: Dict[str, int] = field(default_factory=lambda: defaultdict(int))
    pitch_type_strikes: Dict[str, int] = field(default_factory=lambda: defaultdict(int))
    pitch_type_swstr: Dict[str, int] = field(default_factory=lambda: defaultdict(int))

    # Quality metrics
    quality_starts: int = 0  # 6+ IP, 3 ER or fewer

    def get_era(self) -> float:
        """Calculate ERA"""
        if self.innings_pitched == 0:
            return 0.0
        return (self.earned_runs * 9.0) / self.innings_pitched

    def get_whip(self) -> float:
        """Calculate WHIP"""
        if self.innings_pitched == 0:
            return 0.0
        return (self.walks + self.hits_allowed) / self.innings_pitched

    def get_k_per_9(self) -> float:
        """Calculate K/9"""
        if self.innings_pitched == 0:
            return 0.0
        return (self.strikeouts * 9.0) / self.innings_pitched

    def get_bb_per_9(self) -> float:
        """Calculate BB/9"""
        if self.innings_pitched == 0:
            return 0.0
        return (self.walks * 9.0) / self.innings_pitched

    def get_hr_per_9(self) -> float:
        """Calculate HR/9"""
        if self.innings_pitched == 0:
            return 0.0
        return (self.home_runs_allowed * 9.0) / self.innings_pitched

    def get_k_bb_ratio(self) -> float:
        """Calculate K/BB ratio"""
        if self.walks == 0:
            return self.strikeouts if self.strikeouts > 0 else 0.0
        return self.strikeouts / self.walks


@dataclass
class AdvancedBattingMetrics:
    """Advanced sabermetric batting statistics"""
    # Base stats
    at_bats: int = 0
    hits: int = 0
    singles: int = 0
    doubles: int = 0
    triples: int = 0
    home_runs: int = 0
    walks: int = 0
    strikeouts: int = 0
    hit_by_pitch: int = 0
    sacrifice_flies: int = 0

    # Contact quality
    balls_in_play: int = 0
    balls_in_play_no_hr: int = 0  # For BABIP

    # Batted ball types
    ground_balls: int = 0
    line_drives: int = 0
    fly_balls: int = 0
    pop_ups: int = 0

    # Expected stats
    exit_velocities: List[float] = field(default_factory=list)
    launch_angles: List[float] = field(default_factory=list)
    barrels: int = 0
    hard_hit_balls: int = 0  # 95+ mph

    # wOBA weights (2024 MLB)
    wOBA_BB: float = 0.69
    wOBA_HBP: float = 0.72
    wOBA_1B: float = 0.88
    wOBA_2B: float = 1.24
    wOBA_3B: float = 1.56
    wOBA_HR: float = 2.07
    wOBA_scale: float = 1.185

    def get_batting_avg(self) -> float:
        """Calculate batting average"""
        if self.at_bats == 0:
            return 0.0
        return self.hits / self.at_bats

    def get_obp(self) -> float:
        """Calculate on-base percentage"""
        pa = self.at_bats + self.walks + self.hit_by_pitch + self.sacrifice_flies
        if pa == 0:
            return 0.0
        return (self.hits + self.walks + self.hit_by_pitch) / pa

    def get_slg(self) -> float:
        """Calculate slugging percentage"""
        if self.at_bats == 0:
            return 0.0
        total_bases = self.singles + 2*self.doubles + 3*self.triples + 4*self.home_runs
        return total_bases / self.at_bats

    def get_ops(self) -> float:
        """Calculate OPS (OBP + SLG)"""
        return self.get_obp() + self.get_slg()

    def get_iso(self) -> float:
        """Calculate isolated power (SLG - AVG)"""
        return self.get_slg() - self.get_batting_avg()

    def get_babip(self) -> float:
        """Calculate BABIP (batting average on balls in play)"""
        if self.balls_in_play_no_hr == 0:
            return 0.0
        hits_no_hr = self.hits - self.home_runs
        return hits_no_hr / self.balls_in_play_no_hr

    def get_woba(self) -> float:
        """Calculate wOBA (weighted on-base average)"""
        pa = self.at_bats + self.walks + self.hit_by_pitch + self.sacrifice_flies
        if pa == 0:
            return 0.0

        numerator = (self.wOBA_BB * self.walks +
                    self.wOBA_HBP * self.hit_by_pitch +
                    self.wOBA_1B * self.singles +
                    self.wOBA_2B * self.doubles +
                    self.wOBA_3B * self.triples +
                    self.wOBA_HR * self.home_runs)

        return numerator / pa

    def get_k_rate(self) -> float:
        """Calculate strikeout rate"""
        pa = self.at_bats + self.walks + self.hit_by_pitch + self.sacrifice_flies
        if pa == 0:
            return 0.0
        return self.strikeouts / pa

    def get_bb_rate(self) -> float:
        """Calculate walk rate"""
        pa = self.at_bats + self.walks + self.hit_by_pitch + self.sacrifice_flies
        if pa == 0:
            return 0.0
        return self.walks / pa

    def get_hr_fb_rate(self) -> float:
        """Calculate HR/FB ratio"""
        if self.fly_balls == 0:
            return 0.0
        return self.home_runs / self.fly_balls

    def get_avg_exit_velo(self) -> float:
        """Calculate average exit velocity"""
        if not self.exit_velocities:
            return 0.0
        return np.mean(self.exit_velocities)

    def get_avg_launch_angle(self) -> float:
        """Calculate average launch angle"""
        if not self.launch_angles:
            return 0.0
        return np.mean(self.launch_angles)

    def get_barrel_rate(self) -> float:
        """Calculate barrel rate"""
        if self.balls_in_play == 0:
            return 0.0
        return self.barrels / self.balls_in_play

    def get_hard_hit_rate(self) -> float:
        """Calculate hard hit rate"""
        if self.balls_in_play == 0:
            return 0.0
        return self.hard_hit_balls / self.balls_in_play


@dataclass
class FieldingMetrics:
    """Fielding statistics for a series"""
    # Overall
    total_chances: int = 0  # Putouts + assists + errors
    putouts: int = 0
    assists: int = 0
    errors: int = 0

    # By position
    errors_by_position: Dict[str, int] = field(default_factory=lambda: defaultdict(int))
    chances_by_position: Dict[str, int] = field(default_factory=lambda: defaultdict(int))

    # Timing statistics (fielder arrival - ball arrival)
    timing_margins: List[float] = field(default_factory=list)  # In seconds
    plays_with_negative_margin: int = 0  # Diving catches, etc.

    # Double plays
    double_plays_turned: int = 0
    double_play_opportunities: int = 0

    def get_fielding_percentage(self) -> float:
        """Calculate overall fielding percentage"""
        if self.total_chances == 0:
            return 0.0
        return (self.putouts + self.assists) / self.total_chances

    def get_error_rate(self) -> float:
        """Calculate error rate"""
        if self.total_chances == 0:
            return 0.0
        return self.errors / self.total_chances

    def get_avg_timing_margin(self) -> float:
        """Calculate average timing margin"""
        if not self.timing_margins:
            return 0.0
        return np.mean(self.timing_margins)

    def get_double_play_rate(self) -> float:
        """Calculate double play conversion rate"""
        if self.double_play_opportunities == 0:
            return 0.0
        return self.double_plays_turned / self.double_play_opportunities


@dataclass
class RealismCheck:
    """MLB benchmark comparison for realism validation"""
    metric_name: str
    actual_value: float
    mlb_min: float
    mlb_max: float
    mlb_avg: Optional[float] = None
    status: str = ""  # "OK", "WARNING", "CRITICAL"

    def __post_init__(self):
        """Determine status based on MLB ranges"""
        if self.mlb_min <= self.actual_value <= self.mlb_max:
            self.status = "OK"
        elif self.mlb_avg is not None:
            # Within 20% of average is warning, outside is critical
            deviation = abs(self.actual_value - self.mlb_avg) / self.mlb_avg
            if deviation < 0.20:
                self.status = "WARNING"
            else:
                self.status = "CRITICAL"
        else:
            self.status = "WARNING"

    def get_emoji(self) -> str:
        """Get status emoji"""
        if self.status == "OK":
            return "✓"
        elif self.status == "WARNING":
            return "⚠️"
        else:
            return "🚨"


@dataclass
class SeriesMetrics:
    """Comprehensive series-level statistics and realism checks"""
    num_games: int = 0

    # Team names
    away_team_name: str = ""
    home_team_name: str = ""

    # Win-loss records
    away_wins: int = 0
    home_wins: int = 0

    # Runs
    away_runs: int = 0
    home_runs: int = 0

    # Run distributions (for variance analysis)
    away_runs_per_game: List[int] = field(default_factory=list)
    home_runs_per_game: List[int] = field(default_factory=list)

    # Team metrics
    away_batting: AdvancedBattingMetrics = field(default_factory=AdvancedBattingMetrics)
    home_batting: AdvancedBattingMetrics = field(default_factory=AdvancedBattingMetrics)

    away_pitching: PitchingMetrics = field(default_factory=PitchingMetrics)
    home_pitching: PitchingMetrics = field(default_factory=PitchingMetrics)

    away_fielding: FieldingMetrics = field(default_factory=FieldingMetrics)
    home_fielding: FieldingMetrics = field(default_factory=FieldingMetrics)

    # Game-level metrics aggregation
    total_pitches: int = 0
    total_at_bats: int = 0
    total_plate_appearances: int = 0

    # Realism checks
    realism_checks: List[RealismCheck] = field(default_factory=list)

    def update_from_game(self, game_state, is_away_batting: bool = True):
        """
        Update series metrics from a completed game.

        Parameters
        ----------
        game_state : GameState
            Completed game state with all statistics
        is_away_batting : bool
            Not used, kept for compatibility
        """
        self.num_games += 1

        # Update wins/losses
        if game_state.away_score > game_state.home_score:
            self.away_wins += 1
        else:
            self.home_wins += 1

        # Update runs
        self.away_runs += game_state.away_score
        self.home_runs += game_state.home_score
        self.away_runs_per_game.append(game_state.away_score)
        self.home_runs_per_game.append(game_state.home_score)

        # Update batting stats - Away team
        self._update_batting_metrics(
            self.away_batting,
            game_state.away_at_bats,
            game_state.away_hits,
            game_state.away_singles,
            game_state.away_doubles,
            game_state.away_triples,
            game_state.away_home_runs,
            game_state.away_walks,
            game_state.away_strikeouts,
            game_state.away_ground_balls,
            game_state.away_line_drives,
            game_state.away_fly_balls,
            game_state.away_exit_velocities,
            game_state.away_launch_angles
        )

        # Update batting stats - Home team
        self._update_batting_metrics(
            self.home_batting,
            game_state.home_at_bats,
            game_state.home_hits,
            game_state.home_singles,
            game_state.home_doubles,
            game_state.home_triples,
            game_state.home_home_runs,
            game_state.home_walks,
            game_state.home_strikeouts,
            game_state.home_ground_balls,
            game_state.home_line_drives,
            game_state.home_fly_balls,
            game_state.home_exit_velocities,
            game_state.home_launch_angles
        )

        # Update pitching stats
        # Estimate innings (3 outs = 1 inning, assume 9 innings per game)
        innings_per_game = 9.0
        self.away_pitching.innings_pitched += innings_per_game
        self.home_pitching.innings_pitched += innings_per_game

        # Home pitching faces away batters
        self.home_pitching.hits_allowed += game_state.away_hits
        self.home_pitching.runs_allowed += game_state.away_score
        self.home_pitching.earned_runs += game_state.away_score  # Simplified
        self.home_pitching.walks += game_state.away_walks
        self.home_pitching.strikeouts += game_state.away_strikeouts
        self.home_pitching.home_runs_allowed += game_state.away_home_runs
        self.home_pitching.batters_faced += game_state.away_at_bats + game_state.away_walks

        # Away pitching faces home batters
        self.away_pitching.hits_allowed += game_state.home_hits
        self.away_pitching.runs_allowed += game_state.home_score
        self.away_pitching.earned_runs += game_state.home_score  # Simplified
        self.away_pitching.walks += game_state.home_walks
        self.away_pitching.strikeouts += game_state.home_strikeouts
        self.away_pitching.home_runs_allowed += game_state.home_home_runs
        self.away_pitching.batters_faced += game_state.home_at_bats + game_state.home_walks

        # Update fielding stats
        self.away_fielding.errors += game_state.away_errors
        self.home_fielding.errors += game_state.home_errors

        # Total pitches
        self.total_pitches += game_state.total_pitches

    def _update_batting_metrics(self, metrics: AdvancedBattingMetrics,
                                at_bats: int, hits: int, singles: int,
                                doubles: int, triples: int, home_runs: int,
                                walks: int, strikeouts: int,
                                ground_balls: int, line_drives: int, fly_balls: int,
                                exit_velos: List[float], launch_angles: List[float]):
        """Update batting metrics from game data"""
        metrics.at_bats += at_bats
        metrics.hits += hits
        metrics.singles += singles
        metrics.doubles += doubles
        metrics.triples += triples
        metrics.home_runs += home_runs
        metrics.walks += walks
        metrics.strikeouts += strikeouts

        # Batted ball types
        metrics.ground_balls += ground_balls
        metrics.line_drives += line_drives
        metrics.fly_balls += fly_balls

        # Balls in play
        bip = ground_balls + line_drives + fly_balls
        metrics.balls_in_play += bip
        metrics.balls_in_play_no_hr += bip - home_runs

        # Exit velocities and launch angles
        metrics.exit_velocities.extend(exit_velos)
        metrics.launch_angles.extend(launch_angles)

        # Count barrels and hard hit (simplified - based on EV)
        for ev in exit_velos:
            if ev >= 95.0:
                metrics.hard_hit_balls += 1
            if ev >= 98.0:  # Simplified barrel definition
                metrics.barrels += 1

    def compute_realism_checks(self):
        """Compute realism checks against MLB benchmarks"""
        self.realism_checks = []

        # Combined batting stats
        combined_batting = AdvancedBattingMetrics()
        combined_batting.at_bats = self.away_batting.at_bats + self.home_batting.at_bats
        combined_batting.hits = self.away_batting.hits + self.home_batting.hits
        combined_batting.singles = self.away_batting.singles + self.home_batting.singles
        combined_batting.doubles = self.away_batting.doubles + self.home_batting.doubles
        combined_batting.triples = self.away_batting.triples + self.home_batting.triples
        combined_batting.home_runs = self.away_batting.home_runs + self.home_batting.home_runs
        combined_batting.walks = self.away_batting.walks + self.home_batting.walks
        combined_batting.strikeouts = self.away_batting.strikeouts + self.home_batting.strikeouts
        combined_batting.fly_balls = self.away_batting.fly_balls + self.home_batting.fly_balls
        combined_batting.balls_in_play = self.away_batting.balls_in_play + self.home_batting.balls_in_play
        combined_batting.balls_in_play_no_hr = self.away_batting.balls_in_play_no_hr + self.home_batting.balls_in_play_no_hr
        combined_batting.exit_velocities = self.away_batting.exit_velocities + self.home_batting.exit_velocities
        combined_batting.hard_hit_balls = self.away_batting.hard_hit_balls + self.home_batting.hard_hit_balls

        # Only compute checks if we have enough data
        if combined_batting.at_bats < 20:
            return

        # 1. Batting Average
        if combined_batting.at_bats > 0:
            avg = combined_batting.get_batting_avg()
            self.realism_checks.append(RealismCheck(
                "Batting Average",
                avg,
                mlb_min=0.230,
                mlb_max=0.270,
                mlb_avg=0.248
            ))

        # 2. BABIP
        babip = combined_batting.get_babip()
        if babip > 0:
            self.realism_checks.append(RealismCheck(
                "BABIP",
                babip,
                mlb_min=0.260,
                mlb_max=0.360,
                mlb_avg=0.295
            ))

        # 3. HR/FB rate
        hr_fb = combined_batting.get_hr_fb_rate()
        if combined_batting.fly_balls > 10:
            self.realism_checks.append(RealismCheck(
                "HR/FB Rate",
                hr_fb,
                mlb_min=0.09,
                mlb_max=0.16,
                mlb_avg=0.125
            ))

        # 4. K Rate
        k_rate = combined_batting.get_k_rate()
        self.realism_checks.append(RealismCheck(
            "Strikeout Rate",
            k_rate,
            mlb_min=0.18,
            mlb_max=0.26,
            mlb_avg=0.22
        ))

        # 5. BB Rate
        bb_rate = combined_batting.get_bb_rate()
        self.realism_checks.append(RealismCheck(
            "Walk Rate",
            bb_rate,
            mlb_min=0.07,
            mlb_max=0.10,
            mlb_avg=0.085
        ))

        # 6. ISO
        iso = combined_batting.get_iso()
        self.realism_checks.append(RealismCheck(
            "Isolated Power (ISO)",
            iso,
            mlb_min=0.120,
            mlb_max=0.180,
            mlb_avg=0.150
        ))

        # 7. Average Exit Velocity
        avg_ev = combined_batting.get_avg_exit_velo()
        if avg_ev > 0:
            self.realism_checks.append(RealismCheck(
                "Avg Exit Velocity (mph)",
                avg_ev,
                mlb_min=86.0,
                mlb_max=90.0,
                mlb_avg=88.0
            ))

        # 8. Hard Hit Rate
        hard_hit_rate = combined_batting.get_hard_hit_rate()
        if hard_hit_rate > 0:
            self.realism_checks.append(RealismCheck(
                "Hard Hit Rate",
                hard_hit_rate,
                mlb_min=0.35,
                mlb_max=0.45,
                mlb_avg=0.40
            ))

        # 9. Runs per game
        avg_runs = (self.away_runs + self.home_runs) / (2 * self.num_games)
        self.realism_checks.append(RealismCheck(
            "Runs per Team per Game",
            avg_runs,
            mlb_min=3.8,
            mlb_max=5.2,
            mlb_avg=4.5
        ))

        # 10. Combined pitching ERA
        combined_era = (self.away_pitching.get_era() + self.home_pitching.get_era()) / 2
        if combined_era > 0:
            self.realism_checks.append(RealismCheck(
                "Team ERA",
                combined_era,
                mlb_min=3.50,
                mlb_max=5.00,
                mlb_avg=4.25
            ))

    def print_summary(self):
        """Print comprehensive series summary"""
        self.compute_realism_checks()

        print("\n" + "="*80)
        print("COMPREHENSIVE SERIES STATISTICS")
        print("="*80)

        # Basic series info
        print(f"\n📊 SERIES OVERVIEW:")
        print(f"   Games Played: {self.num_games}")
        print(f"   {self.away_team_name}: {self.away_wins}-{self.home_wins}")
        print(f"   {self.home_team_name}: {self.home_wins}-{self.away_wins}")

        # Run analysis
        print(f"\n🏃 RUN PRODUCTION:")
        print(f"   {self.away_team_name}:")
        print(f"      Total: {self.away_runs} ({self.away_runs/self.num_games:.2f} per game)")
        if self.away_runs_per_game:
            print(f"      Range: {min(self.away_runs_per_game)}-{max(self.away_runs_per_game)} runs")
            print(f"      Std Dev: {np.std(self.away_runs_per_game):.2f}")

        print(f"   {self.home_team_name}:")
        print(f"      Total: {self.home_runs} ({self.home_runs/self.num_games:.2f} per game)")
        if self.home_runs_per_game:
            print(f"      Range: {min(self.home_runs_per_game)}-{max(self.home_runs_per_game)} runs")
            print(f"      Std Dev: {np.std(self.home_runs_per_game):.2f}")

        # Batting statistics for both teams
        for team_name, batting in [(self.away_team_name, self.away_batting),
                                     (self.home_team_name, self.home_batting)]:
            print(f"\n⚾ BATTING - {team_name}:")
            print(f"   Triple Slash: .{int(batting.get_batting_avg()*1000):03d}/.{int(batting.get_obp()*1000):03d}/.{int(batting.get_slg()*1000):03d}")
            print(f"   OPS: {batting.get_ops():.3f}")
            print(f"   wOBA: {batting.get_woba():.3f} (MLB avg ~0.320)")
            print(f"\n   Plate Discipline:")
            print(f"      K Rate: {batting.get_k_rate()*100:.1f}% (MLB avg ~22%)")
            print(f"      BB Rate: {batting.get_bb_rate()*100:.1f}% (MLB avg ~8.5%)")
            print(f"      K/BB Ratio: {batting.strikeouts/batting.walks if batting.walks > 0 else 0:.2f}")
            print(f"\n   Power Metrics:")
            print(f"      ISO: {batting.get_iso():.3f} (MLB avg ~0.150)")
            print(f"      HR/FB: {batting.get_hr_fb_rate()*100:.1f}% (MLB avg ~12.5%)")
            print(f"      Home Runs: {batting.home_runs} ({batting.home_runs/self.num_games:.1f} per game)")
            print(f"\n   Contact Quality:")
            print(f"      BABIP: {batting.get_babip():.3f} (MLB range: .260-.360)")
            print(f"      Avg Exit Velo: {batting.get_avg_exit_velo():.1f} mph (MLB avg ~88 mph)")
            print(f"      Avg Launch Angle: {batting.get_avg_launch_angle():.1f}°")
            print(f"      Hard Hit Rate: {batting.get_hard_hit_rate()*100:.1f}% (MLB avg ~40%)")
            print(f"      Barrel Rate: {batting.get_barrel_rate()*100:.1f}% (MLB avg ~8%)")
            print(f"\n   Batted Ball Distribution:")
            total_bb = batting.ground_balls + batting.line_drives + batting.fly_balls
            if total_bb > 0:
                print(f"      Ground Balls: {batting.ground_balls/total_bb*100:.1f}% (MLB avg ~45%)")
                print(f"      Line Drives: {batting.line_drives/total_bb*100:.1f}% (MLB avg ~21%)")
                print(f"      Fly Balls: {batting.fly_balls/total_bb*100:.1f}% (MLB avg ~34%)")

        # Pitching statistics
        for team_name, pitching in [(self.away_team_name, self.away_pitching),
                                      (self.home_team_name, self.home_pitching)]:
            print(f"\n🎯 PITCHING - {team_name}:")
            print(f"   ERA: {pitching.get_era():.2f} (MLB avg ~4.25)")
            print(f"   WHIP: {pitching.get_whip():.2f} (MLB avg ~1.30)")
            print(f"   K/9: {pitching.get_k_per_9():.1f} (MLB avg ~8.5)")
            print(f"   BB/9: {pitching.get_bb_per_9():.1f} (MLB avg ~3.0)")
            print(f"   HR/9: {pitching.get_hr_per_9():.2f} (MLB avg ~1.2)")
            print(f"   K/BB Ratio: {pitching.get_k_bb_ratio():.2f} (MLB avg ~2.8)")
            print(f"\n   Totals:")
            print(f"      IP: {pitching.innings_pitched:.1f}")
            print(f"      Pitches: {pitching.pitches_thrown} ({pitching.pitches_thrown/pitching.innings_pitched:.1f} per inning)")
            print(f"      Batters Faced: {pitching.batters_faced}")

        # Fielding statistics
        for team_name, fielding in [(self.away_team_name, self.away_fielding),
                                      (self.home_team_name, self.home_fielding)]:
            print(f"\n🧤 FIELDING - {team_name}:")
            print(f"   Errors: {fielding.errors} ({fielding.errors/self.num_games:.1f} per game)")
            if fielding.errors_by_position:
                print(f"   Errors by Position:")
                for pos, count in sorted(fielding.errors_by_position.items(),
                                        key=lambda x: x[1], reverse=True):
                    print(f"      {pos}: {count}")

        # MLB Realism Checks
        print(f"\n🎯 MLB REALISM BENCHMARKS:")
        print("="*80)

        if not self.realism_checks:
            print("   ⚠️  Not enough data for realism checks (need 20+ at-bats)")
        else:
            # Group by status
            ok_checks = [c for c in self.realism_checks if c.status == "OK"]
            warning_checks = [c for c in self.realism_checks if c.status == "WARNING"]
            critical_checks = [c for c in self.realism_checks if c.status == "CRITICAL"]

            print(f"\n   Summary: {len(ok_checks)}/{len(self.realism_checks)} metrics within MLB range")

            # Print all checks
            print(f"\n   {'Metric':<30} {'Actual':>10} {'MLB Range':>20} {'Status':>8}")
            print("   " + "-"*70)

            for check in self.realism_checks:
                if check.mlb_avg is not None:
                    mlb_range = f"{check.mlb_min:.3f}-{check.mlb_max:.3f} (avg {check.mlb_avg:.3f})"
                else:
                    mlb_range = f"{check.mlb_min:.3f}-{check.mlb_max:.3f}"

                print(f"   {check.metric_name:<30} {check.actual_value:>10.3f} {mlb_range:>20} {check.get_emoji():>8}")

            # Warnings and critical issues
            if warning_checks:
                print(f"\n   ⚠️  WARNINGS ({len(warning_checks)}):")
                for check in warning_checks:
                    print(f"      - {check.metric_name}: {check.actual_value:.3f} (outside range {check.mlb_min:.3f}-{check.mlb_max:.3f})")

            if critical_checks:
                print(f"\n   🚨 CRITICAL ISSUES ({len(critical_checks)}):")
                for check in critical_checks:
                    print(f"      - {check.metric_name}: {check.actual_value:.3f} (far from MLB avg {check.mlb_avg:.3f})")

            if not warning_checks and not critical_checks:
                print(f"\n   ✓ All metrics within expected MLB ranges!")

        print("\n" + "="*80)
