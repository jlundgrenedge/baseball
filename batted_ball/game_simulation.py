"""
Game Simulation Module

This module provides a complete baseball game simulation system that integrates
all the physics-based mechanics (pitching, hitting, fielding, baserunning) into
a full 9-inning game with detailed tracking and output.
"""

from dataclasses import dataclass, field
from typing import List, Dict, Optional, Tuple, Union
from enum import Enum
import random
import sys
import numpy as np

from .player import Pitcher, Hitter, generate_pitch_arsenal
from .fielding import Fielder
from .baserunning import BaseRunner, create_average_runner, create_speed_runner, create_slow_runner
from .play_simulation import PlaySimulator
from .play_outcome import PlayResult, PlayOutcome
from .defense_factory import create_standard_defense
from .at_bat import AtBatSimulator
from .constants import SimulationMode
from .ballpark_effects import get_ballpark_effects, get_ballpark_for_team, MLB_BALLPARK_EFFECTS
from .attributes import (
    create_power_hitter,
    create_balanced_hitter,
    create_groundball_hitter,
    create_starter_pitcher,
    create_reliever_pitcher
)

class BaseState(Enum):
    """Represents which bases have runners"""
    EMPTY = "empty"
    FIRST = "1st"
    SECOND = "2nd"
    THIRD = "3rd"
    FIRST_SECOND = "1st_2nd"
    FIRST_THIRD = "1st_3rd"
    SECOND_THIRD = "2nd_3rd"
    LOADED = "loaded"


def get_zone_bucket(location: Tuple[float, float]) -> str:
    """
    Classify pitch location into a zone bucket.

    Parameters
    ----------
    location : tuple
        (x, z) location in inches at plate crossing

    Returns
    -------
    str
        Zone bucket label (e.g., "MID_MIDDLE", "LOW_AWAY", etc.)
    """
    from .constants import STRIKE_ZONE_WIDTH, STRIKE_ZONE_BOTTOM, STRIKE_ZONE_TOP

    x_inches, z_inches = location

    # Strike zone boundaries (in inches)
    # x: negative = inside (for RHH), positive = outside
    # Simplify: treat as universal (not handedness-specific)
    sz_left = -STRIKE_ZONE_WIDTH / 2.0
    sz_right = STRIKE_ZONE_WIDTH / 2.0
    sz_bottom = STRIKE_ZONE_BOTTOM
    sz_top = STRIKE_ZONE_TOP

    # Horizontal classification
    third_width = STRIKE_ZONE_WIDTH / 3.0
    if x_inches < sz_left:
        horiz = "IN"
    elif x_inches < sz_left + third_width:
        horiz = "IN"
    elif x_inches < sz_left + 2 * third_width:
        horiz = "MID"
    elif x_inches <= sz_right:
        horiz = "AWAY"
    else:
        horiz = "AWAY"

    # Vertical classification
    third_height = (sz_top - sz_bottom) / 3.0
    if z_inches < sz_bottom:
        vert = "LOW"
    elif z_inches < sz_bottom + third_height:
        vert = "LOW"
    elif z_inches < sz_bottom + 2 * third_height:
        vert = "MID"
    elif z_inches <= sz_top:
        vert = "UP"
    else:
        vert = "UP"

    return f"{vert}_{horiz}"


def get_pitch_outcome_code(pitch_data: Dict) -> str:
    """
    Convert pitch outcome to a standard outcome code.

    Parameters
    ----------
    pitch_data : dict
        Pitch data dictionary with 'pitch_outcome' key

    Returns
    -------
    str
        Standard outcome code for parsing
    """
    outcome = pitch_data.get('pitch_outcome', 'unknown')
    swing = pitch_data.get('swing', False)

    outcome_map = {
        'ball': 'BALL',
        'called_strike': 'STRIKE_TAKEN',
        'swinging_strike': 'STRIKE_SWING',
        'foul': 'FOUL',
        'ball_in_play': 'INPLAY',
        'contact': 'INPLAY',
    }

    return outcome_map.get(outcome, 'UNKNOWN')


def get_pa_outcome_code(outcome: str, batted_ball_result: Optional[Dict] = None) -> str:
    """
    Convert plate appearance outcome to a standard outcome code.

    Parameters
    ----------
    outcome : str
        PA outcome ('strikeout', 'walk', 'single', 'home_run', etc.)
    batted_ball_result : dict, optional
        Batted ball data if applicable

    Returns
    -------
    str
        Standard PA outcome code for parsing
    """
    # Map common outcomes
    outcome_map = {
        'strikeout': 'STRIKEOUT_SWING',  # Default to swing, can refine
        'walk': 'WALK',
        'single': 'SINGLE',
        'double': 'DOUBLE',
        'triple': 'TRIPLE',
        'home_run': 'HOMERUN',
        'fly_out': 'OUT_FLY',
        'line_out': 'OUT_LINE',
        'ground_out': 'OUT_GROUND',
        'force_out': 'OUT_FORCE',
        'double_play': 'DOUBLE_PLAY',
        'error': 'REACHED_ON_ERROR',
        'fielders_choice': 'FIELDERS_CHOICE',
    }

    return outcome_map.get(outcome, outcome.upper())


@dataclass
class GameState:
    """Tracks the complete state of a baseball game"""
    inning: int = 1
    is_top: bool = True  # True = top of inning (away team batting)
    outs: int = 0
    away_score: int = 0
    home_score: int = 0

    # Runners on base (None if empty, Hitter object if occupied)
    runner_on_first: Optional[Hitter] = None
    runner_on_second: Optional[Hitter] = None
    runner_on_third: Optional[Hitter] = None

    # Game statistics - Total (both teams)
    total_pitches: int = 0
    total_hits: int = 0
    total_home_runs: int = 0

    # Per-team statistics - Away team
    away_hits: int = 0
    away_singles: int = 0
    away_doubles: int = 0
    away_triples: int = 0
    away_home_runs: int = 0
    away_strikeouts: int = 0
    away_walks: int = 0
    away_errors: int = 0
    away_at_bats: int = 0
    away_ground_balls: int = 0  # Launch angle < 10 degrees
    away_fly_balls: int = 0     # Launch angle >= 25 degrees
    away_line_drives: int = 0   # Launch angle 10-25 degrees
    away_exit_velocities: List[float] = field(default_factory=list)
    away_launch_angles: List[float] = field(default_factory=list)
    # Out tracking by batted ball type (Phase 1.7 - for validating defense calibration)
    away_ground_ball_outs: int = 0
    away_fly_ball_outs: int = 0
    away_line_drive_outs: int = 0

    # Per-team statistics - Home team
    home_hits: int = 0
    home_singles: int = 0
    home_doubles: int = 0
    home_triples: int = 0
    home_home_runs: int = 0
    home_strikeouts: int = 0
    home_walks: int = 0
    home_errors: int = 0
    home_at_bats: int = 0
    home_ground_balls: int = 0
    home_fly_balls: int = 0
    home_line_drives: int = 0
    home_exit_velocities: List[float] = field(default_factory=list)
    home_launch_angles: List[float] = field(default_factory=list)
    # Out tracking by batted ball type (Phase 1.7)
    home_ground_ball_outs: int = 0
    home_fly_ball_outs: int = 0
    home_line_drive_outs: int = 0

    def get_batting_team(self) -> str:
        """Returns which team is currently batting"""
        return "Away" if self.is_top else "Home"

    def get_pitching_team(self) -> str:
        """Returns which team is currently pitching"""
        return "Home" if self.is_top else "Away"

    def get_base_state(self) -> BaseState:
        """Returns the current base/runner situation"""
        first = self.runner_on_first is not None
        second = self.runner_on_second is not None
        third = self.runner_on_third is not None

        if not any([first, second, third]):
            return BaseState.EMPTY
        elif first and second and third:
            return BaseState.LOADED
        elif first and second:
            return BaseState.FIRST_SECOND
        elif first and third:
            return BaseState.FIRST_THIRD
        elif second and third:
            return BaseState.SECOND_THIRD
        elif first:
            return BaseState.FIRST
        elif second:
            return BaseState.SECOND
        elif third:
            return BaseState.THIRD

    def clear_bases(self):
        """Clear all runners from bases"""
        self.runner_on_first = None
        self.runner_on_second = None
        self.runner_on_third = None

    def add_out(self):
        """Add an out"""
        self.outs += 1

    def end_half_inning(self):
        """End the current half inning"""
        self.outs = 0
        self.clear_bases()

        if self.is_top:
            # Switch to bottom of inning
            self.is_top = False
        else:
            # Move to next inning
            self.is_top = True
            self.inning += 1

    def score_run(self, for_away_team: bool):
        """Add a run to the appropriate team"""
        if for_away_team:
            self.away_score += 1
        else:
            self.home_score += 1

    def __str__(self) -> str:
        """String representation of game state"""
        half = "Top" if self.is_top else "Bot"
        base_state = self.get_base_state().value
        return (f"{half} {self.inning} | {self.away_score}-{self.home_score} | "
                f"{self.outs} out | Runners: {base_state}")


@dataclass
class Team:
    """Represents a baseball team with players"""
    name: str
    pitchers: List[Pitcher]
    hitters: List[Hitter]  # Batting lineup (9 players)
    fielders: Dict[str, Fielder]  # Defensive positions dict keyed by position name

    abbreviation: str = ""  # Team abbreviation (e.g., 'NYY', 'LAD') for ballpark lookups
    home_ballpark: str = ""  # Home ballpark name (e.g., 'yankee', 'dodger')
    current_pitcher_index: int = 0
    current_batter_index: int = 0

    def get_current_pitcher(self) -> Pitcher:
        """Get the current pitcher"""
        return self.pitchers[self.current_pitcher_index]

    def get_next_batter(self) -> Hitter:
        """Get the next batter in the lineup and advance"""
        batter = self.hitters[self.current_batter_index]
        self.current_batter_index = (self.current_batter_index + 1) % len(self.hitters)
        return batter

    def switch_pitcher(self, index: int):
        """Switch to a different pitcher"""
        if 0 <= index < len(self.pitchers):
            self.current_pitcher_index = index

    def get_starters(self) -> List[Pitcher]:
        """Get list of starting pitchers (those with is_starter=True)"""
        starters = [p for p in self.pitchers if getattr(p, 'is_starter', True)]
        # If no starters found (legacy data), treat first 5 as starters
        if not starters:
            starters = self.pitchers[:min(5, len(self.pitchers))]
        return starters

    def get_relievers(self) -> List[Pitcher]:
        """Get list of relief pitchers (those with is_starter=False)"""
        relievers = [p for p in self.pitchers if not getattr(p, 'is_starter', True)]
        # If no relievers found (legacy data), treat remaining pitchers as relievers
        if not relievers:
            relievers = self.pitchers[5:] if len(self.pitchers) > 5 else []
        return relievers

    def get_random_reliever(self) -> Optional[Pitcher]:
        """Get a random reliever from the bullpen"""
        relievers = self.get_relievers()
        if relievers:
            return random.choice(relievers)
        # Fallback: if no relievers, return any non-current pitcher
        available = [p for i, p in enumerate(self.pitchers) if i != self.current_pitcher_index]
        return random.choice(available) if available else None

    def switch_to_reliever(self) -> Optional[Pitcher]:
        """Switch to a random reliever and return the new pitcher"""
        reliever = self.get_random_reliever()
        if reliever:
            # Find index of this reliever
            try:
                idx = self.pitchers.index(reliever)
                self.switch_pitcher(idx)
                return reliever
            except ValueError:
                pass
        return None

    def reset_pitcher_state(self):
        """Reset all pitchers' state (pitch count, fatigue) for a new game"""
        for pitcher in self.pitchers:
            pitcher.pitches_thrown = 0


class PitcherRotation:
    """
    Manages pitcher rotation across a series of games.
    
    Cycles through starters (up to 5) for each game, and handles
    bullpen usage within games (reliever after 5 innings).
    """
    
    def __init__(self, team: Team, num_starters: int = 5):
        """
        Initialize pitcher rotation manager.
        
        Parameters
        ----------
        team : Team
            The team to manage rotation for
        num_starters : int
            Number of starters to cycle through (default 5)
        """
        self.team = team
        self.starters = team.get_starters()[:num_starters]
        self.relievers = team.get_relievers()
        self.current_starter_index = 0
        
        # Fallback if not enough starters
        if len(self.starters) < num_starters:
            # Add some relievers to starter rotation if needed
            needed = num_starters - len(self.starters)
            self.starters.extend(self.relievers[:needed])
    
    def get_game_starter(self) -> Pitcher:
        """
        Get the starting pitcher for the current game and advance rotation.
        
        Returns
        -------
        Pitcher
            The starting pitcher for this game
        """
        if not self.starters:
            return self.team.pitchers[0]  # Fallback
        
        starter = self.starters[self.current_starter_index]
        self.current_starter_index = (self.current_starter_index + 1) % len(self.starters)
        return starter
    
    def set_game_starter(self, team: Team, starter: Pitcher):
        """
        Set a specific starter for the team at the start of a game.
        
        Parameters
        ----------
        team : Team
            The team to set the starter for
        starter : Pitcher
            The pitcher to start
        """
        try:
            idx = team.pitchers.index(starter)
            team.switch_pitcher(idx)
            # Reset this pitcher's state for fresh start
            starter.pitches_thrown = 0
        except ValueError:
            pass  # Pitcher not found, keep current
    
    def get_random_reliever(self) -> Optional[Pitcher]:
        """Get a random reliever from the bullpen"""
        if self.relievers:
            return random.choice(self.relievers)
        return None


@dataclass
class PlayByPlayEvent:
    """A single play-by-play event in the game"""
    inning: int
    is_top: bool
    batter_name: str
    pitcher_name: str
    outcome: str
    description: str
    physics_data: Dict
    game_state_after: str


class GameSimulator:
    """Simulates a complete baseball game"""

    def __init__(
        self,
        away_team: Team,
        home_team: Team,
        verbose: bool = True,
        log_file: str = None,
        ballpark: str = 'generic',
        debug_metrics: int = 0,
        wind_enabled: bool = True,
        starter_innings: int = 0,
        simulation_mode: Union[SimulationMode, str] = None,
    ):
        """
        Initialize game simulator.

        Parameters
        ----------
        away_team : Team
            Away team
        home_team : Team
            Home team
        verbose : bool
            Print play-by-play to console
        log_file : str, optional
            File to write game log
        ballpark : str
            Ballpark name for environmental effects
        debug_metrics : int
            Metrics debug level: 0=OFF, 1=BASIC, 2=DETAILED, 3=EXHAUSTIVE
        wind_enabled : bool
            Enable random wind conditions (default: True for Phase 2C)
        starter_innings : int
            Number of innings for starting pitcher before bullpen.
            0 = no automatic changes (default, traditional behavior)
            5 = starter goes 5 innings, then random relievers each inning
        simulation_mode : SimulationMode or str, optional
            Simulation speed/accuracy mode. Can be:
            - SimulationMode enum value (ACCURATE, FAST, ULTRA_FAST, EXTREME)
            - String: "accurate", "fast", "ultra_fast", "extreme"
            Defaults to ACCURATE for single games, ULTRA_FAST recommended for bulk.
        """
        self.away_team = away_team
        self.home_team = home_team
        self.verbose = verbose
        self.log_file = log_file
        self.ballpark = ballpark
        self.game_state = GameState()
        self.play_by_play: List[PlayByPlayEvent] = []
        self.starter_innings = starter_innings  # When to switch to bullpen

        # Get ballpark environmental effects (altitude, temperature from ballpark_effects.py)
        # First try to get effects by ballpark name, then by home team abbreviation
        self.ballpark_effects = get_ballpark_effects(ballpark)
        if self.ballpark_effects is None and hasattr(home_team, 'abbreviation'):
            # Try to find ballpark from home team
            team_ballpark = get_ballpark_for_team(home_team.abbreviation)
            if team_ballpark:
                self.ballpark_effects = get_ballpark_effects(team_ballpark)
        
        # Set environmental conditions from ballpark (or defaults)
        if self.ballpark_effects:
            self.altitude = self.ballpark_effects.elevation_ft
            self.temperature = self.ballpark_effects.avg_temperature_f
            self.humidity = 0.5  # Default humidity (could be added to ballpark_effects later)
        else:
            # Default to sea level, 70°F if ballpark not found
            self.altitude = 0.0
            self.temperature = 70.0
            self.humidity = 0.5

        # Parse simulation mode
        if simulation_mode is None:
            self.simulation_mode = SimulationMode.ACCURATE
        elif isinstance(simulation_mode, str):
            mode_map = {
                "accurate": SimulationMode.ACCURATE,
                "fast": SimulationMode.FAST,
                "ultra_fast": SimulationMode.ULTRA_FAST,
                "extreme": SimulationMode.EXTREME,
            }
            self.simulation_mode = mode_map.get(simulation_mode.lower(), SimulationMode.ACCURATE)
        else:
            self.simulation_mode = simulation_mode

        # Generate random wind conditions for this game (Phase 2C)
        # Realistic MLB wind distribution:
        # - Speed: 0-20 MPH, most commonly 3-10 MPH
        # - Direction: Random 0-360°, including tailwinds that help carry balls out
        if wind_enabled:
            # Use triangular distribution for wind speed (mode=9 mph, max=20 mph)
            # Increased mode from 7 to 9 mph to boost HR rate via stronger wind effect
            # MLB stadiums often have 8-12 mph average winds; this is realistic
            # Combined with enhanced wind shear in Rust, high fly balls carry much further
            self.wind_speed = np.random.triangular(0, 9, 20)  # low, mode, high

            # Wind direction: 0-360 degrees
            # 0° = toward CF (tailwind), 90° = toward RF, 180° = headwind, 270° = toward LF
            # Tailwind-heavy distribution to simulate "hitter-friendly" conditions
            # Real parks vary: Wrigley "wind blowing out" days are HR-friendly
            # This biases toward tailwinds to help reach the ~12.5% HR/FB target
            direction_options = [
                (0, 0.18),    # Pure tailwind (blowing out to CF) - helps HRs!
                (45, 0.15),   # Toward RF-CF gap (tailwind component)
                (90, 0.10),   # Toward RF (crosswind)
                (135, 0.07),  # Toward RF-home (slight headwind)
                (180, 0.05),  # Pure headwind (blowing in) - hurts HRs
                (225, 0.07),  # Toward LF-home (slight headwind)
                (270, 0.10),  # Toward LF (crosswind)
                (315, 0.15),  # Toward LF-CF gap (tailwind component)
                (330, 0.13),  # Mostly tailwind
            ]
            directions, weights = zip(*direction_options)
            self.wind_direction = np.random.choice(directions, p=weights)
        else:
            self.wind_speed = 0.0
            self.wind_direction = 0.0

        # Initialize metrics collector
        from .sim_metrics import SimMetricsCollector, DebugLevel
        debug_level_map = {
            0: DebugLevel.OFF,
            1: DebugLevel.BASIC,
            2: DebugLevel.DETAILED,
            3: DebugLevel.EXHAUSTIVE
        }
        self.metrics_collector = SimMetricsCollector(
            debug_level=debug_level_map.get(debug_metrics, DebugLevel.OFF)
        )

        # Open log file if specified
        self.log_handle = None
        if self.log_file:
            self.log_handle = open(self.log_file, 'w', encoding='utf-8')

        # Simulator (we'll create at-bat simulators per at-bat)
        self.play_simulator = PlaySimulator(ballpark=ballpark)

    def log(self, message: str):
        """Log a message to console and/or file"""
        if self.verbose:
            print(message)
        if self.log_handle:
            self.log_handle.write(message + '\n')
            self.log_handle.flush()  # Ensure immediate write

    def close_log(self):
        """Close the log file if open"""
        if self.log_handle:
            self.log_handle.close()
            self.log_handle = None

    def __del__(self):
        """Destructor to ensure log file is closed"""
        self.close_log()

    def print_sim_config(self, rng_seed: int = None):
        """Print simulation configuration block"""
        self.log("SIM CONFIG:")

        # Engine version - try to get git hash if available
        try:
            import subprocess
            git_hash = subprocess.check_output(['git', 'rev-parse', '--short', 'HEAD'],
                                             stderr=subprocess.DEVNULL).decode('ascii').strip()
            self.log(f"  EngineVersion: git-{git_hash}")
        except:
            self.log(f"  EngineVersion: v1.1.2")

        # RNG seed
        if rng_seed is not None:
            self.log(f"  RNGSeed: {rng_seed}")
        else:
            self.log(f"  RNGSeed: random")

        # Ballpark
        self.log(f"  Ballpark: {self.ballpark}")
        if self.ballpark_effects:
            self.log(f"    Park: {self.ballpark_effects.venue_name}")
            self.log(f"    DistanceEffect: {self.ballpark_effects.total_distance_added:+.1f}%")

        # Weather/environment (using actual ballpark data)
        self.log(f"  Weather:")
        self.log(f"    TemperatureF: {self.temperature:.1f}")
        self.log(f"    AltitudeFt: {self.altitude:.0f}")
        self.log(f"    Humidity: {self.humidity:.2f}")
        # Wind info from game conditions (Phase 2C - variable wind)
        self.log(f"    WindSpeedMph: {self.wind_speed:.1f}")
        self.log(f"    WindDirection: {self.wind_direction:.0f}°")
        # Wind description for clarity
        if abs(self.wind_speed) > 0.5:
            if self.wind_direction == 0:
                wind_desc = "toward CF (tailwind)"
            elif self.wind_direction == 90:
                wind_desc = "toward RF (R crosswind)"
            elif self.wind_direction == 180:
                wind_desc = "toward home (headwind)"
            elif self.wind_direction == 270:
                wind_desc = "toward LF (L crosswind, helps RHH!)"
            else:
                wind_desc = f"{self.wind_direction}°"
            self.log(f"    WindDesc: {wind_desc}")

        self.log("")  # Blank line after config

    def simulate_game(self, num_innings: int = 9, rng_seed: int = None) -> GameState:
        """Simulate a complete baseball game"""
        if self.verbose:
            self.log(f"\n{'='*80}")
            self.log(f"GAME START: {self.away_team.name} @ {self.home_team.name}")
            self.log(f"{'='*80}\n")

            # Print SIM CONFIG block
            self.print_sim_config(rng_seed)

        while self.game_state.inning <= num_innings:
            self.simulate_half_inning()

            # Check for mercy rule or if we're past 9 innings with a tie
            if self.game_state.inning > num_innings:
                if self.game_state.away_score != self.game_state.home_score:
                    break  # Game over
                # Continue extra innings if tied

        if self.verbose:
            self.print_final_summary()

        # Print metrics summary if enabled
        if self.metrics_collector.enabled:
            self.metrics_collector.print_summary()

        return self.game_state

    def simulate_half_inning(self):
        """Simulate a half inning (until 3 outs)"""
        batting_team = self.away_team if self.game_state.is_top else self.home_team
        pitching_team = self.home_team if self.game_state.is_top else self.away_team

        # Check for pitcher change at start of inning (bullpen management)
        # If starter_innings is set and we're past that inning, bring in a reliever
        if self.starter_innings > 0 and self.game_state.inning > self.starter_innings:
            # Switch to a random reliever each inning after starter_innings
            old_pitcher = pitching_team.get_current_pitcher()
            new_pitcher = pitching_team.switch_to_reliever()
            if new_pitcher and new_pitcher != old_pitcher:
                if self.verbose:
                    print(f"\n⚾ PITCHING CHANGE: {old_pitcher.name} → {new_pitcher.name}")

        if self.verbose:
            print(f"\n{'='*60}")
            print(f"{self.game_state}")
            print(f"{'='*60}")

        # Safety limit to prevent infinite loops
        at_bats = 0
        max_at_bats = 50

        while self.game_state.outs < 3 and at_bats < max_at_bats:
            self.simulate_at_bat(batting_team, pitching_team)
            at_bats += 1
            
            # Check if inning should end after processing the at-bat
            if self.game_state.outs >= 3:
                break

        if at_bats >= max_at_bats:
            print(f"  WARNING: Hit max at-bats limit ({max_at_bats}), ending inning")

        # End of half inning
        self.game_state.end_half_inning()

    def simulate_at_bat(self, batting_team: Team, pitching_team: Team):
        """Simulate a single at-bat"""
        batter = batting_team.get_next_batter()
        pitcher = pitching_team.get_current_pitcher()

        if self.verbose:
            print(f"\n{batter.name} batting against {pitcher.name}")
            print(f"  Situation: {self.game_state.get_base_state().value}, {self.game_state.outs} out(s)")

        # Create at-bat simulator for this matchup (with game wind conditions and ballpark environment)
        at_bat_sim = AtBatSimulator(
            pitcher,
            batter,
            altitude=self.altitude,
            temperature=self.temperature,
            humidity=self.humidity,
            wind_speed=self.wind_speed,
            wind_direction=self.wind_direction,
            metrics_collector=self.metrics_collector,
            simulation_mode=self.simulation_mode,
        )

        # Simulate the at-bat to get batted ball
        at_bat_result = at_bat_sim.simulate_at_bat()
        num_pitches = len(at_bat_result.pitches)
        self.game_state.total_pitches += num_pitches

        if self.verbose and at_bat_result.pitches:
            self.print_pitch_sequence(at_bat_result.pitches)

        if at_bat_result.outcome in ["strikeout", "walk"]:
            # Handle strikeout or walk
            self.handle_strikeout_or_walk(at_bat_result.outcome, batter)

            # Log the event
            balls, strikes = at_bat_result.final_count
            self.log_play_by_play(
                batter_name=batter.name,
                pitcher_name=pitcher.name,
                outcome=at_bat_result.outcome,
                description=f"{at_bat_result.outcome.upper()} on {num_pitches} pitches",
                physics_data={
                    "pitches_thrown": num_pitches,
                    "final_count": f"{balls}-{strikes}"
                }
            )
        else:
            # Ball was put in play - simulate the complete play

            # Setup defense (fielders is already a dict)
            self.play_simulator.setup_defense(pitching_team.fielders)

            # Setup existing baserunners (not including batter)
            runners_dict = {}
            if self.game_state.runner_on_first:
                runners_dict["first"] = self.create_runner_from_hitter(
                    self.game_state.runner_on_first, "first"
                )
            if self.game_state.runner_on_second:
                runners_dict["second"] = self.create_runner_from_hitter(
                    self.game_state.runner_on_second, "second"
                )
            if self.game_state.runner_on_third:
                runners_dict["third"] = self.create_runner_from_hitter(
                    self.game_state.runner_on_third, "third"
                )

            self.play_simulator.setup_baserunners(runners_dict)

            # Create batter as runner
            batter_runner = self.create_runner_from_hitter(batter, "home")

            # Extract the actual trajectory result from the dict
            trajectory = at_bat_result.batted_ball_result['trajectory']

            # Simulate the play with current outs for realistic baserunning decisions
            play_result = self.play_simulator.simulate_complete_play(
                batted_ball_result=trajectory,
                batter_runner=batter_runner,
                current_outs=self.game_state.outs
            )

            # Process the play result with enhanced physics data
            self.process_play_result(play_result, batter, pitcher, at_bat_result)

            # Reset play simulator for next play
            self.play_simulator.reset_simulation()

    def handle_strikeout_or_walk(self, outcome: str, batter: Hitter):
        """Handle a strikeout or walk"""
        is_away_batting = self.game_state.is_top

        if outcome == "strikeout":
            self.game_state.add_out()
            # Track strikeout statistics
            if is_away_batting:
                self.game_state.away_strikeouts += 1
                self.game_state.away_at_bats += 1
            else:
                self.game_state.home_strikeouts += 1
                self.game_state.home_at_bats += 1

            if self.verbose:
                self.log(f"  ⚾ STRIKEOUT! {self.game_state.outs} out(s)")
                self.log(f"  OutcomeCodePA: {get_pa_outcome_code('strikeout')}")

        elif outcome == "walk":
            # Track walk statistics
            if is_away_batting:
                self.game_state.away_walks += 1
            else:
                self.game_state.home_walks += 1

            # Batter walks to first, runners advance if forced
            if self.verbose:
                self.log(f"  🚶 WALK!")
                self.log(f"  OutcomeCodePA: {get_pa_outcome_code('walk')}")

            # Check for force plays and advance runners
            if self.game_state.runner_on_first is not None:
                if self.game_state.runner_on_second is not None:
                    if self.game_state.runner_on_third is not None:
                        # Bases loaded - runner scores from third
                        self.game_state.score_run(self.game_state.is_top)
                        if self.verbose:
                            print(f"  🏃 Runner scores from third! (RBI Walk)")

                    # Move third to home handled above
                    self.game_state.runner_on_third = self.game_state.runner_on_second

                # Move second to third
                self.game_state.runner_on_second = self.game_state.runner_on_first

            # Batter goes to first
            self.game_state.runner_on_first = batter

    def get_current_runners(self, batter: Hitter) -> List[BaseRunner]:
        """Get current runners on base for play simulation"""
        runners = []

        # Add existing runners
        if self.game_state.runner_on_first:
            runners.append(self.create_runner_from_hitter(
                self.game_state.runner_on_first, "first"
            ))

        if self.game_state.runner_on_second:
            runners.append(self.create_runner_from_hitter(
                self.game_state.runner_on_second, "second"
            ))

        if self.game_state.runner_on_third:
            runners.append(self.create_runner_from_hitter(
                self.game_state.runner_on_third, "third"
            ))

        # Add batter as runner
        runners.append(self.create_runner_from_hitter(batter, "home"))

        return runners

    def create_runner_from_hitter(self, hitter: Hitter, starting_base: str) -> BaseRunner:
        """Create a BaseRunner from a Hitter using their speed attribute"""
        # Use hitter's speed attribute (0-100,000 scale) for baserunning physics
        # Default to average (50000) if hitter doesn't have speed attribute (backward compatibility)
        speed_rating = getattr(hitter, 'speed', 50000)

        # Create runner with hitter's actual speed rating
        # Also use speed for acceleration (correlation between speed and burst)
        # and baserunning IQ (faster players tend to have better baserunning instincts)
        runner = BaseRunner(
            name=hitter.name,
            sprint_speed=speed_rating,
            acceleration=speed_rating,  # Use same rating for acceleration
            base_running_iq=min(speed_rating + 10000, 100000),  # Slight boost to IQ
            sliding_ability=50000,  # Average sliding ability
            turn_efficiency=speed_rating  # Faster runners maintain speed better in turns
        )
        runner.current_base = starting_base
        return runner

    def process_play_result(self, play_result: PlayResult, batter: Hitter, pitcher: Pitcher,
                           at_bat_result=None):
        """Process the result of a play and update game state"""
        outcome = play_result.outcome
        is_away_batting = self.game_state.is_top

        # Track at-bats (all batted balls except sacrifice plays)
        if is_away_batting:
            self.game_state.away_at_bats += 1
        else:
            self.game_state.home_at_bats += 1

        # Count hits
        if outcome in [PlayOutcome.SINGLE, PlayOutcome.DOUBLE, PlayOutcome.TRIPLE, PlayOutcome.HOME_RUN]:
            self.game_state.total_hits += 1
            if outcome == PlayOutcome.HOME_RUN:
                self.game_state.total_home_runs += 1

            # Track per-team hit statistics
            if is_away_batting:
                self.game_state.away_hits += 1
                if outcome == PlayOutcome.SINGLE:
                    self.game_state.away_singles += 1
                elif outcome == PlayOutcome.DOUBLE:
                    self.game_state.away_doubles += 1
                elif outcome == PlayOutcome.TRIPLE:
                    self.game_state.away_triples += 1
                elif outcome == PlayOutcome.HOME_RUN:
                    self.game_state.away_home_runs += 1
            else:
                self.game_state.home_hits += 1
                if outcome == PlayOutcome.SINGLE:
                    self.game_state.home_singles += 1
                elif outcome == PlayOutcome.DOUBLE:
                    self.game_state.home_doubles += 1
                elif outcome == PlayOutcome.TRIPLE:
                    self.game_state.home_triples += 1
                elif outcome == PlayOutcome.HOME_RUN:
                    self.game_state.home_home_runs += 1

        # Track errors
        if outcome == PlayOutcome.ERROR:
            if is_away_batting:
                # Error charged to home team (defense)
                self.game_state.home_errors += 1
            else:
                # Error charged to away team (defense)
                self.game_state.away_errors += 1

        # Enhanced physics data collection from at_bat_result
        last_pitch = {}  # Initialize to avoid scope issues

        if at_bat_result and at_bat_result.batted_ball_result:
            batted_ball_dict = at_bat_result.batted_ball_result
            exit_velocity = round(batted_ball_dict['exit_velocity'], 1)
            launch_angle = round(batted_ball_dict['launch_angle'], 1)

            physics_data = {
                "exit_velocity_mph": exit_velocity,
                "launch_angle_deg": launch_angle,
                "distance_ft": round(batted_ball_dict['distance'], 1),
                "hang_time_sec": round(batted_ball_dict['hang_time'], 2),
                "contact_quality": batted_ball_dict.get('contact_quality', 'unknown'),
                "peak_height_ft": round(batted_ball_dict['peak_height'], 1),
            }

            # Track exit velocity and launch angle for averages
            # Normalize outcome to string for comparison (handles both enum and string types)
            outcome_val = outcome.value if hasattr(outcome, 'value') else str(outcome)
            
            if is_away_batting:
                self.game_state.away_exit_velocities.append(exit_velocity)
                self.game_state.away_launch_angles.append(launch_angle)
                # Categorize by launch angle
                if launch_angle < 10:
                    self.game_state.away_ground_balls += 1
                    # Track outs by batted ball type (Phase 1.7)
                    # Ground balls result in ground_out, force_out, or double_play
                    if outcome_val in ['ground_out', 'force_out', 'double_play']:
                        self.game_state.away_ground_ball_outs += 1
                elif launch_angle < 25:
                    self.game_state.away_line_drives += 1
                    # Line drives caught use fly_out outcome (not line_out which is unused)
                    if outcome_val == 'fly_out':
                        self.game_state.away_line_drive_outs += 1
                else:
                    self.game_state.away_fly_balls += 1
                    # Fly balls result in fly_out or infield_fly
                    if outcome_val in ['fly_out', 'infield_fly']:
                        self.game_state.away_fly_ball_outs += 1
            else:
                self.game_state.home_exit_velocities.append(exit_velocity)
                self.game_state.home_launch_angles.append(launch_angle)
                # Categorize by launch angle
                if launch_angle < 10:
                    self.game_state.home_ground_balls += 1
                    # Track outs by batted ball type (Phase 1.7)
                    # Ground balls result in ground_out, force_out, or double_play
                    if outcome_val in ['ground_out', 'force_out', 'double_play']:
                        self.game_state.home_ground_ball_outs += 1
                elif launch_angle < 25:
                    self.game_state.home_line_drives += 1
                    # Line drives caught use fly_out outcome (not line_out which is unused)
                    if outcome_val == 'fly_out':
                        self.game_state.home_line_drive_outs += 1
                else:
                    self.game_state.home_fly_balls += 1
                    # Fly balls result in fly_out or infield_fly
                    if outcome_val in ['fly_out', 'infield_fly']:
                        self.game_state.home_fly_ball_outs += 1

            # Get the last pitch (the one that was hit)
            last_pitch = at_bat_result.pitches[-1] if at_bat_result.pitches else {}
        else:
            # Fallback to trajectory object (though we always have dict now)
            bb_result = play_result.batted_ball_result
            physics_data = {
                "exit_velocity_mph": 0,
                "launch_angle_deg": 0,
                "distance_ft": round(bb_result.distance, 1),
                "hang_time_sec": round(bb_result.flight_time, 2),
                "peak_height_ft": round(bb_result.peak_height, 1),
                "spin_rpm": 0,
            }

        # Build description
        description = self.build_play_description(play_result, physics_data)

        if self.verbose:
            self.log(f"  {description}")

            # Enhanced physics display
            physics_line = (f"    Physics: EV={physics_data['exit_velocity_mph']} mph, "
                          f"LA={physics_data['launch_angle_deg']}°, "
                          f"Dist={physics_data['distance_ft']} ft")

            # Add optional physics details if available
            hang_time = physics_data.get('hang_time_sec')
            if isinstance(hang_time, (int, float)):
                physics_line += f", Hang={hang_time:.2f}s"

            peak_height = physics_data.get('peak_height_ft')
            if isinstance(peak_height, (int, float)):
                physics_line += f", Peak={peak_height:.1f} ft"

            # Add contact quality if available
            if 'contact_quality' in physics_data:
                physics_line += f", Contact: {physics_data['contact_quality']}"

            self.log(physics_line)

            # Add pitch information if available
            if last_pitch:
                pitch_type = last_pitch.get('pitch_type', 'fastball')
                pitch_velocity = last_pitch.get('velocity_plate', 0)
                pitch_location = last_pitch.get('final_location', (0, 0))
                pitch_line = f"    Pitch: {pitch_type} {pitch_velocity:.1f} mph"
                if pitch_location and len(pitch_location) >= 2:
                    zone_x = pitch_location[0] / 12.0  # Convert inches to feet for display
                    zone_z = pitch_location[1] / 12.0
                    pitch_line += f" at zone ({zone_x:.1f}', {zone_z:.1f}')"
                self.log(pitch_line)

            # Add PA outcome code
            outcome_str = outcome.value if hasattr(outcome, 'value') else str(outcome)
            self.log(f"  OutcomeCodePA: {get_pa_outcome_code(outcome_str, at_bat_result.batted_ball_result if at_bat_result else None)}")

            self.print_play_breakdown(play_result)


        # Update game state based on outcome
        if self.verbose and play_result.runs_scored > 0:
            print(f"    [DEBUG] PlayResult.runs_scored: {play_result.runs_scored}")
            
        self.update_game_state_from_play(play_result, batter)

        # Log play by play
        # Handle both enum and string outcomes
        outcome_str = outcome.value if hasattr(outcome, 'value') else str(outcome)
        self.log_play_by_play(
            batter_name=batter.name,
            pitcher_name=pitcher.name,
            outcome=outcome_str,
            description=description,
            physics_data=physics_data
        )

    def build_play_description(self, play_result: PlayResult, physics_data: Dict) -> str:
        """Build a descriptive string for the play"""
        outcome = play_result.outcome

        if outcome == PlayOutcome.HOME_RUN:
            return f"💥 HOME RUN! {physics_data['distance_ft']} ft shot!"
        elif outcome == PlayOutcome.TRIPLE:
            return f"🔥 TRIPLE! Ball goes to the gap"
        elif outcome == PlayOutcome.DOUBLE:
            return f"⚡ DOUBLE! Extra base hit"
        elif outcome == PlayOutcome.SINGLE:
            return f"✓ SINGLE"
        elif outcome == PlayOutcome.GROUND_OUT:
            fielder_pos = play_result.primary_fielder.position if play_result.primary_fielder else "infield"
            return f"⚾ Ground out to {fielder_pos}"
        elif outcome == PlayOutcome.FLY_OUT:
            fielder_pos = play_result.primary_fielder.position if play_result.primary_fielder else "outfield"

            # FIX FOR OUTFIELD POP-UP BUG: If caught by an infielder, label as "Pop-up to infield"
            # Infielders: pitcher, catcher, first_base, second_base, third_base, shortstop
            infielder_positions = ['pitcher', 'catcher', 'first_base', 'second_base', 'third_base', 'shortstop']
            if fielder_pos in infielder_positions:
                return f"⚾ Pop-up to infield ({fielder_pos})"
            else:
                return f"⚾ Fly out to {fielder_pos}"
        elif outcome == PlayOutcome.LINE_OUT:
            return f"⚾ Line out"
        elif outcome == PlayOutcome.DOUBLE_PLAY:
            return f"⚾⚾ DOUBLE PLAY!"
        elif outcome == PlayOutcome.INFIELD_FLY:
            return f"⚾ INFIELD FLY - Batter Out (rule invoked)"
        else:
            # Handle both enum and string outcomes
            outcome_str = outcome.value if hasattr(outcome, 'value') else str(outcome)
            return f"{outcome_str}"

    def update_game_state_from_play(self, play_result: PlayResult, batter: Hitter):
        """Update game state based on play result"""
        outcome = play_result.outcome

        # Use the outs_made and runs_scored from play result
        for _ in range(play_result.outs_made):
            self.game_state.add_out()

        # Score runs
        for _ in range(play_result.runs_scored):
            self.game_state.score_run(self.game_state.is_top)
            if self.verbose:
                print(f"    🏃 Run scores!")

        # Create reverse lookup: runner name -> hitter BEFORE clearing bases
        # We need to figure out which hitter corresponds to each runner
        # The play_result has BaseRunner objects, but game_state tracks Hitter objects
        # Match by name: BaseRunner.name should equal Hitter.name
        runner_to_hitter = {}
        
        # Add current batter
        runner_to_hitter[batter.name] = batter
        
        # Add existing runners BEFORE clearing (so we can match them later)
        if self.game_state.runner_on_first:
            runner_to_hitter[self.game_state.runner_on_first.name] = self.game_state.runner_on_first
        if self.game_state.runner_on_second:
            runner_to_hitter[self.game_state.runner_on_second.name] = self.game_state.runner_on_second
        if self.game_state.runner_on_third:
            runner_to_hitter[self.game_state.runner_on_third.name] = self.game_state.runner_on_third

        # NOW clear bases
        self.game_state.clear_bases()

        if self.verbose and play_result.final_runner_positions:
            runner_descriptions = []
            for base, runner in play_result.final_runner_positions.items():
                runner_name = getattr(runner, 'name', 'Runner')
                runner_descriptions.append(f"{runner_name} on {base}")
            print(f"    Runners after play: {', '.join(runner_descriptions)}")
        
        # Now update bases from final positions
        for base, runner in play_result.final_runner_positions.items():
            runner_name = getattr(runner, 'name', batter.name)
            hitter = runner_to_hitter.get(runner_name, batter)  # Default to batter if not found
            
            if base == "first":
                self.game_state.runner_on_first = hitter
            elif base == "second":
                self.game_state.runner_on_second = hitter
            elif base == "third":
                self.game_state.runner_on_third = hitter

        # If it was a hit and no runners in final positions, at least put batter on appropriate base
        if outcome in [PlayOutcome.SINGLE, PlayOutcome.DOUBLE, PlayOutcome.TRIPLE] and len(play_result.final_runner_positions) == 0:
            if outcome == PlayOutcome.SINGLE:
                self.game_state.runner_on_first = batter
            elif outcome == PlayOutcome.DOUBLE:
                self.game_state.runner_on_second = batter
            elif outcome == PlayOutcome.TRIPLE:
                self.game_state.runner_on_third = batter

    def log_play_by_play(self, batter_name: str, pitcher_name: str,
                         outcome: str, description: str, physics_data: Dict):
        """Log a play-by-play event"""
        event = PlayByPlayEvent(
            inning=self.game_state.inning,
            is_top=self.game_state.is_top,
            batter_name=batter_name,
            pitcher_name=pitcher_name,
            outcome=outcome,
            description=description,
            physics_data=physics_data,
            game_state_after=str(self.game_state)
        )
        self.play_by_play.append(event)

    def print_pitch_sequence(self, pitches: List[Dict]):
        """Print detailed pitch-by-pitch information for an at-bat."""
        if not pitches:
            return

        self.log("  Pitch sequence:")
        for index, pitch in enumerate(pitches, 1):
            index = pitch.get('sequence_index', index)
            pitch_type = pitch.get('pitch_type', 'pitch')
            velocity_release = pitch.get('velocity_release', 0.0)
            velocity_plate = pitch.get('velocity_plate', 0.0)
            location = pitch.get('final_location')
            count_before = pitch.get('count_before', (0, 0))
            count_after = pitch.get('count_after', count_before)
            outcome = pitch.get('pitch_outcome', 'unknown')

            if location and len(location) >= 2:
                zone_x = location[0] / 12.0
                zone_z = location[1] / 12.0
                location_str = f"({zone_x:.2f}', {zone_z:.2f}')"
                zone_bucket = get_zone_bucket(location)
            else:
                location_str = "(unknown)"
                zone_bucket = "UNKNOWN"

            outcome_map = {
                'ball': 'taken for ball',
                'called_strike': 'taken for strike',
                'swinging_strike': 'swing and miss',
                'foul': 'fouled off',
                'ball_in_play': 'put in play',
            }
            outcome_desc = outcome_map.get(outcome, outcome)

            if pitch.get('swing') and outcome in ['ball', 'called_strike']:
                # Edge case safety - should not happen but provide context
                outcome_desc = f"swing -> {outcome_desc}"

            contact_summary = pitch.get('contact_summary')
            contact_details = ""
            if contact_summary and outcome in ['foul', 'ball_in_play']:
                contact_details = (
                    f" (contact: {contact_summary['contact_quality']}, "
                    f"EV {contact_summary['exit_velocity']:.1f} mph, "
                    f"LA {contact_summary['launch_angle']:.1f}°)"
                )

            self.log(
                f"    #{index}: {pitch_type} {velocity_release:.1f}->{velocity_plate:.1f} mph to {location_str} "
                f"[{count_before[0]}-{count_before[1]} -> {count_after[0]}-{count_after[1]}] "
                f"{outcome_desc}{contact_details}"
            )
            # Add machine-readable codes
            self.log(f"    ZoneBucket: {zone_bucket}")
            self.log(f"    OutcomeCodePitch: {get_pitch_outcome_code(pitch)}")

            # Add fatigue diagnostics if available
            if 'pitcher_pitches_thrown' in pitch:
                fatigue_level = pitch.get('pitcher_fatigue_level', 0.0)
                velo_penalty = pitch.get('velocity_penalty_mph', 0.0)
                command_penalty = pitch.get('command_penalty_inches', 0.0)
                self.log(f"    Fatigue:")
                self.log(f"      PitchCount: {pitch['pitcher_pitches_thrown']}")
                self.log(f"      FatigueLevel: {fatigue_level:.2f}")
                self.log(f"      VelocityPenaltyMph: {velo_penalty:.1f}")
                self.log(f"      CommandPenaltyInches: {command_penalty:.1f}")

            # Add swing decision diagnostics if available
            if 'swing_decision' in pitch:
                sd = pitch['swing_decision']
                self.log(f"    SwingDecisionModel:")
                self.log(f"      EstimatedStrikeProb: {sd['estimated_strike_prob']:.2f}")
                self.log(f"      EV_Swing: {sd['ev_swing']:+.3f}")
                self.log(f"      EV_Take: {sd['ev_take']:+.3f}")
                self.log(f"      AggressionModifier: {sd['aggression_modifier']:+.2f}")
                self.log(f"      Decision: {sd['decision']}")

            # Add pitch intent diagnostics if available
            if 'pitch_intent' in pitch:
                pi = pitch['pitch_intent']
                self.log(f"    PitchIntent:")
                self.log(f"      IntentionCategory: {pi['intention_category']}")
                self.log(f"      IntendedZone: {pi['intended_zone']}")
                self.log(f"      IntendedPitchType: {pi['intended_pitch_type']}")
                self.log(f"      CommandError:")
                self.log(f"        XErrorInches: {pi['x_error_inches']:+.1f}")
                self.log(f"        ZErrorInches: {pi['z_error_inches']:+.1f}")
                if pi['missed_into_zone'] != pi['intended_zone']:
                    self.log(f"      MissedIntoZone: {pi['missed_into_zone']}")

    def print_play_breakdown(self, play_result: PlayResult):
        """Print detailed physics/fielding/baserunning breakdown for a play."""
        events = play_result.get_events_chronological()
        if events:
            self.log("    Play timeline:")
            for event in events:
                self.log(f"      [{event.time:5.2f}s] {event.description} ({event.event_type})")

        if play_result.fielding_results:
            self.log("    Fielding breakdown:")
            for fielding in play_result.fielding_results:
                margin = fielding.ball_arrival_time - fielding.fielder_arrival_time
                status = "made play" if fielding.success else "missed"
                fielder_name = getattr(fielding, 'fielder_name', 'Fielder')
                self.log(
                    f"      {fielder_name}: ball {fielding.ball_arrival_time:.2f}s, "
                    f"arrival {fielding.fielder_arrival_time:.2f}s (margin {margin:+.2f}s) -> {status}"
                )

        if play_result.baserunning_results:
            self.log("    Baserunning results:")
            for baserun in play_result.baserunning_results:
                self.log(
                    f"      {baserun.runner_name}: {baserun.from_base} -> {baserun.to_base} "
                    f"in {baserun.arrival_time:.2f}s ({baserun.outcome})"
                )


    def print_final_summary(self):
        """Print final game summary"""
        self.log(f"\n{'='*80}")
        self.log(f"FINAL SCORE")
        self.log(f"{'='*80}")
        self.log(f"{self.away_team.name}: {self.game_state.away_score}")
        self.log(f"{self.home_team.name}: {self.game_state.home_score}")
        self.log(f"\nGame Statistics:")
        self.log(f"  Total Pitches: {self.game_state.total_pitches}")
        self.log(f"  Total Hits: {self.game_state.total_hits}")
        self.log(f"  Home Runs: {self.game_state.total_home_runs}")

        # Print sabermetric summaries for each team
        self.log(f"\n{'-'*80}")
        self.print_sabermetric_summary(self.away_team.name, is_away=True)
        self.log(f"{'-'*80}")
        self.print_sabermetric_summary(self.home_team.name, is_away=False)
        self.log(f"{'='*80}")

        # Print model drift indicators (combined for both teams)
        self.print_model_drift_indicators()
        self.log(f"{'='*80}\n")

    def print_sabermetric_summary(self, team_name: str, is_away: bool):
        """Print sabermetric summary for a team"""
        gs = self.game_state

        # Get team-specific stats
        if is_away:
            ab = gs.away_at_bats
            h = gs.away_hits
            bb = gs.away_walks
            so = gs.away_strikeouts
            singles = gs.away_singles
            doubles = gs.away_doubles
            triples = gs.away_triples
            hr = gs.away_home_runs
        else:
            ab = gs.home_at_bats
            h = gs.home_hits
            bb = gs.home_walks
            so = gs.home_strikeouts
            singles = gs.home_singles
            doubles = gs.home_doubles
            triples = gs.home_triples
            hr = gs.home_home_runs

        # Calculate sabermetrics
        pa = ab + bb  # Approximate PA (ignoring HBP, SF, etc.)

        # AVG
        avg = h / ab if ab > 0 else 0.0

        # OBP = (H + BB) / PA
        obp = (h + bb) / pa if pa > 0 else 0.0

        # SLG = Total Bases / AB
        total_bases = singles + (2 * doubles) + (3 * triples) + (4 * hr)
        slg = total_bases / ab if ab > 0 else 0.0

        # BABIP = (H - HR) / (AB - K - HR)
        babip_denom = ab - so - hr
        babip = (h - hr) / babip_denom if babip_denom > 0 else 0.0

        # K%
        k_pct = (so / pa * 100) if pa > 0 else 0.0

        # BB%
        bb_pct = (bb / pa * 100) if pa > 0 else 0.0

        # ISO = SLG - AVG
        iso = slg - avg

        self.log(f"SABERMETRIC SUMMARY – {team_name}")
        self.log(f"  PA: {pa}")
        self.log(f"  AVG: {avg:.3f}")
        self.log(f"  OBP: {obp:.3f}")
        self.log(f"  SLG: {slg:.3f}")
        self.log(f"  BABIP: {babip:.3f}")
        self.log(f"  K%: {k_pct:.1f}%")
        self.log(f"  BB%: {bb_pct:.1f}%")
        self.log(f"  ISO: {iso:.3f}")

        # Add compact sabermetric snapshot
        # Calculate contact type rates
        total_bip = singles + doubles + triples + hr
        if is_away:
            gb_count = gs.away_ground_balls
            ld_count = gs.away_line_drives
            fb_count = gs.away_fly_balls
        else:
            gb_count = gs.home_ground_balls
            ld_count = gs.home_line_drives
            fb_count = gs.home_fly_balls

        total_contact = gb_count + ld_count + fb_count
        gb_pct = (gb_count / total_contact * 100) if total_contact > 0 else 0.0
        ld_pct = (ld_count / total_contact * 100) if total_contact > 0 else 0.0
        fb_pct = (fb_count / total_contact * 100) if total_contact > 0 else 0.0
        hr_per_fb = (hr / fb_count * 100) if fb_count > 0 else 0.0

        self.log(f"\n  SABERMETRIC SNAPSHOT:")
        self.log(f"    BABIP: {babip:.3f} | K%: {k_pct:.1f}% | BB%: {bb_pct:.1f}% | ISO: {iso:.3f} | HR/FB: {hr_per_fb:.1f}%")
        self.log(f"    GB%: {gb_pct:.1f}% | LD%: {ld_pct:.1f}% | FB%: {fb_pct:.1f}%")

    def print_model_drift_indicators(self):
        """Print model drift indicators to flag unrealistic stat distributions"""
        gs = self.game_state

        # Combine both teams for model drift analysis
        total_hr = gs.away_home_runs + gs.home_home_runs
        total_fb = gs.away_fly_balls + gs.home_fly_balls
        total_gb = gs.away_ground_balls + gs.home_ground_balls
        total_ld = gs.away_line_drives + gs.home_line_drives
        total_so = gs.away_strikeouts + gs.home_strikeouts
        total_bb = gs.away_walks + gs.home_walks
        total_ab = gs.away_at_bats + gs.home_at_bats
        total_h = gs.away_hits + gs.home_hits
        total_pa = total_ab + total_bb

        # Calculate HR/FB ratio
        hr_per_fb = (total_hr / total_fb * 100) if total_fb > 0 else 0.0

        # Calculate BABIP (already in sabermetric summary, recalc here)
        babip_denom = total_ab - total_so - total_hr
        babip = (total_h - total_hr) / babip_denom if babip_denom > 0 else 0.0

        # Calculate K% and BB%
        k_pct = (total_so / total_pa * 100) if total_pa > 0 else 0.0
        bb_pct = (total_bb / total_pa * 100) if total_pa > 0 else 0.0

        # Calculate average exit velocity
        all_evs = gs.away_exit_velocities + gs.home_exit_velocities
        avg_ev = sum(all_evs) / len(all_evs) if all_evs else 0.0

        # Calculate contact type percentages
        total_contact = total_gb + total_ld + total_fb
        gb_pct = (total_gb / total_contact * 100) if total_contact > 0 else 0.0
        ld_pct = (total_ld / total_contact * 100) if total_contact > 0 else 0.0
        fb_pct = (total_fb / total_contact * 100) if total_contact > 0 else 0.0

        self.log(f"\nMODEL DRIFT INDICATORS:")

        # Always show all metrics (even if not enough data for flags)
        # HR/FB check (MLB typical: 12-14%)
        hr_fb_flag = ""
        if total_fb >= 5:  # Only flag if enough data
            if hr_per_fb < 8:
                hr_fb_flag = " ⚠ too low; MLB ~12-14%"
            elif hr_per_fb > 18:
                hr_fb_flag = " ⚠ too high; MLB ~12-14%"
            else:
                hr_fb_flag = " ok"
        elif total_fb > 0:
            hr_fb_flag = " (sample size too small)"
        else:
            hr_fb_flag = " (no fly balls)"
        self.log(f"  HR/FB: {hr_per_fb:.1f}%{hr_fb_flag}")

        # BABIP check (MLB typical: .290-.310)
        babip_flag = ""
        if babip_denom >= 5:
            if babip < 0.250:
                babip_flag = " ⚠ too low; MLB ~.290-.310"
            elif babip > 0.360:
                babip_flag = " ⚠ too high; MLB ~.290-.310"
            else:
                babip_flag = " ok"
        elif babip_denom > 0:
            babip_flag = " (sample size too small)"
        else:
            babip_flag = " (no balls in play)"
        self.log(f"  BABIP: {babip:.3f}{babip_flag}")

        # K% check (MLB typical: 22-24%)
        k_flag = ""
        if total_pa >= 10:
            if k_pct < 15:
                k_flag = " ⚠ too low; MLB ~22-24%"
            elif k_pct > 30:
                k_flag = " ⚠ too high; MLB ~22-24%"
            else:
                k_flag = " ok"
        elif total_pa > 0:
            k_flag = " (sample size too small)"
        else:
            k_flag = " (no plate appearances)"
        self.log(f"  K%: {k_pct:.1f}%{k_flag}")

        # BB% check (MLB typical: 8-9%)
        bb_flag = ""
        if total_pa >= 10:
            if bb_pct < 5:
                bb_flag = " ⚠ too low; MLB ~8-9%"
            elif bb_pct > 13:
                bb_flag = " ⚠ too high; MLB ~8-9%"
            else:
                bb_flag = " ok"
        elif total_pa > 0:
            bb_flag = " (sample size too small)"
        else:
            bb_flag = " (no plate appearances)"
        self.log(f"  BB%: {bb_pct:.1f}%{bb_flag}")

        # Avg EV check (MLB typical: 87-89 mph)
        ev_flag = ""
        if len(all_evs) >= 5:
            if avg_ev < 82:
                ev_flag = " ⚠ too low; MLB ~87-89 mph"
            elif avg_ev > 94:
                ev_flag = " ⚠ too high; MLB ~87-89 mph"
            else:
                ev_flag = " ok"
        elif len(all_evs) > 0:
            ev_flag = " (sample size too small)"
        else:
            ev_flag = " (no batted balls)"
        self.log(f"  AvgExitVelo: {avg_ev:.1f} mph{ev_flag}")

        # Contact type distribution (MLB typical: ~43% GB, ~24% LD, ~33% FB)
        self.log(f"  Contact Distribution:")
        gb_flag = " ok" if 38 <= gb_pct <= 48 else (" ⚠ too low" if gb_pct < 38 else " ⚠ too high")
        ld_flag = " ok" if 19 <= ld_pct <= 29 else (" ⚠ too low" if ld_pct < 19 else " ⚠ too high")
        fb_flag = " ok" if 28 <= fb_pct <= 38 else (" ⚠ too low" if fb_pct < 28 else " ⚠ too high")
        if total_contact >= 5:
            self.log(f"    GB%: {gb_pct:.1f}% (MLB ~43%){gb_flag}")
            self.log(f"    LD%: {ld_pct:.1f}% (MLB ~24%){ld_flag}")
            self.log(f"    FB%: {fb_pct:.1f}% (MLB ~33%){fb_flag}")
        else:
            self.log(f"    GB%: {gb_pct:.1f}% | LD%: {ld_pct:.1f}% | FB%: {fb_pct:.1f}% (sample size too small)")

        # Phase 1.7: Out rates by batted ball type (MLB typical: GB ~72%, LD ~26%, FB ~79%)
        total_gb_outs = gs.away_ground_ball_outs + gs.home_ground_ball_outs
        total_ld_outs = gs.away_line_drive_outs + gs.home_line_drive_outs
        total_fb_outs = gs.away_fly_ball_outs + gs.home_fly_ball_outs
        
        gb_out_rate = (total_gb_outs / total_gb * 100) if total_gb > 0 else 0.0
        ld_out_rate = (total_ld_outs / total_ld * 100) if total_ld > 0 else 0.0
        fb_out_rate = (total_fb_outs / total_fb * 100) if total_fb > 0 else 0.0
        
        self.log(f"  Out Rates by Type (MLB: GB ~72%, LD ~26%, FB ~79%):")
        if total_contact >= 5:
            gb_out_flag = " ok" if 65 <= gb_out_rate <= 80 else (" ⚠ too low" if gb_out_rate < 65 else " ⚠ too high")
            ld_out_flag = " ok" if 20 <= ld_out_rate <= 35 else (" ⚠ too low" if ld_out_rate < 20 else " ⚠ too high")
            fb_out_flag = " ok" if 72 <= fb_out_rate <= 86 else (" ⚠ too low" if fb_out_rate < 72 else " ⚠ too high")
            self.log(f"    GB Out%: {gb_out_rate:.1f}% ({total_gb_outs}/{total_gb}){gb_out_flag}")
            self.log(f"    LD Out%: {ld_out_rate:.1f}% ({total_ld_outs}/{total_ld}){ld_out_flag}")
            self.log(f"    FB Out%: {fb_out_rate:.1f}% ({total_fb_outs}/{total_fb}){fb_out_flag}")
        else:
            self.log(f"    GB Out%: {gb_out_rate:.1f}% | LD Out%: {ld_out_rate:.1f}% | FB Out%: {fb_out_rate:.1f}% (sample size too small)")


def create_test_team(name: str, team_quality: str = "average") -> Team:
    """
    Create a test team with randomized but realistic players.

    Creates a mix of different batter types:
    - Ground ball hitters (low launch angle ~8-15°)
    - Line drive hitters (medium launch angle ~15-22°)
    - Fly ball hitters (high launch angle ~22-32°)
    - Power hitters (high launch angle + high exit velo ~25-35°)

    Args:
        name: Team name
        team_quality: "poor", "average", "good", or "elite"

    Returns:
        Complete Team object
    """
    # Quality determines attribute ranges
    quality_ranges = {
        "poor": (30, 50),
        "average": (45, 65),
        "good": (55, 75),
        "elite": (65, 85)
    }

    min_attr, max_attr = quality_ranges.get(team_quality, (45, 65))

    # Create pitchers using PHYSICS-FIRST approach
    # Starters have balanced attributes + high stamina
    # Relievers have high velocity/spin + low stamina
    pitchers = []
    for i in range(3):
        role = "Starter" if i == 0 else "Reliever"

        # Use physics-first attribute creators (100,000-point scale)
        if i == 0:
            attributes = create_starter_pitcher(team_quality)
        else:
            attributes = create_reliever_pitcher(team_quality)

        # Generate realistic pitch arsenal based on pitcher attributes and role
        pitch_arsenal = generate_pitch_arsenal(
            attributes,
            role="starter" if i == 0 else "reliever"
        )

        # Create pitcher with unified attribute system
        pitcher = Pitcher(
            name=f"{name} Pitcher {i+1} ({role})",
            attributes=attributes,
            pitch_arsenal=pitch_arsenal
        )
        pitchers.append(pitcher)

        # Debug output for first team created
        if not hasattr(create_test_team, 'pitchers_debug_shown'):
            velo = attributes.get_raw_velocity_mph()
            spin = attributes.get_spin_rate_rpm()
            stamina = attributes.get_stamina_pitches()
            arsenal_str = ", ".join(pitch_arsenal.keys())
            print(f"    {role}: {velo:.1f} mph, {spin:.0f} rpm, {stamina:.0f} pitch stamina")
            print(f"      Arsenal: {arsenal_str}")

    if not hasattr(create_test_team, 'pitchers_debug_shown'):
        create_test_team.pitchers_debug_shown = True

    # Define batter type profiles
    # Each profile has (swing_path_angle_range, launch_angle_tendency_range, description)
    # Increased swing path angles for fly ball/power hitters to enable home runs (need 25-30° launch)
    batter_types = [
        ((6, 12), (8, 15), "ground ball"),      # Ground ball hitter
        ((10, 16), (12, 20), "line drive"),     # Line drive hitter
        ((14, 20), (18, 26), "balanced"),       # Balanced
        ((20, 28), (22, 30), "fly ball"),       # Fly ball hitter (increased from 16-22)
        ((24, 32), (25, 35), "power"),          # Power hitter (increased from 18-24)
    ]

    # Create hitters (9-player lineup) with varied types using PHYSICS-FIRST approach
    # No profiles needed - power emerges from HIGH bat speed + HIGH attack angle
    hitters = []
    position_names = ["C", "1B", "2B", "3B", "SS", "LF", "CF", "RF", "DH"]
    # FIX (2025-11-19): Increased ground ball % from 15% to 25% for realistic GB rate (~43%)
    # MLB distribution: ~43% GB, ~24% LD, ~33% FB
    hitter_type_weights = [0.25, 0.25, 0.30, 0.15, 0.05]  # GB, LD, Balanced, FB, Power
    hitter_type_names = ["groundball", "line drive", "balanced", "fly ball", "power"]

    for i, pos in enumerate(position_names):
        # Randomly select hitter type (for display only - physics determines outcomes)
        hitter_type_idx = random.choices(range(5), weights=hitter_type_weights)[0]
        hitter_type = hitter_type_names[hitter_type_idx]

        # Use physics-first attribute creators (100,000-point scale)
        if hitter_type == "power":
            attributes = create_power_hitter(team_quality)
        elif hitter_type == "fly ball":
            # FIX: Fly ball hitters should also use power hitter attributes
            # They hit for less power than pure power hitters but still elevate the ball
            attributes = create_power_hitter(team_quality)
        elif hitter_type == "groundball":
            attributes = create_groundball_hitter(team_quality)
        else:  # balanced, line drive
            attributes = create_balanced_hitter(team_quality)

        # Create hitter with unified attribute system
        hitter = Hitter(
            name=f"{name} {pos}",
            attributes=attributes
        )
        hitters.append(hitter)

        # Debug output for first team created
        if not hasattr(create_test_team, 'debug_shown'):
            bat_speed = attributes.get_bat_speed_mph()
            attack_angle = attributes.get_attack_angle_mean_deg()
            print(f"    {pos}: {hitter_type} hitter (bat: {bat_speed:.1f} mph, angle: {attack_angle:.1f}°)")

    if not hasattr(create_test_team, 'debug_shown'):
        create_test_team.debug_shown = True

    # Create fielders using standard defense
    fielders = create_standard_defense()

    return Team(
        name=name,
        pitchers=pitchers,
        hitters=hitters,
        fielders=fielders
    )
