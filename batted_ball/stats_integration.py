"""
Stats Integration Module

Provides integration between the game simulation and statistics tracking systems.
Wraps GameSimulator to optionally record detailed statistics via Scorekeeper.

This module allows stats tracking to be enabled/disabled without modifying
the core game simulation code.
"""

from dataclasses import dataclass
from datetime import date
from typing import Optional, Union
from enum import Enum
import uuid

from .game_simulation import GameSimulator, Team, GameState
from .scorekeeper import (
    Scorekeeper, GameLog, PlayNotation, PlayerGameBatting, PlayerGamePitching
)
from .play_outcome import PlayResult, PlayOutcome
from .constants import SimulationMode


class StatsTrackingMode(Enum):
    """Level of statistics tracking detail."""
    DISABLED = "disabled"      # No stats tracking
    BASIC = "basic"            # Box scores only (fastest)
    STANDARD = "standard"      # Box scores + basic play notation
    DETAILED = "detailed"      # Full play-by-play with physics data


class StatsEnabledGameSimulator(GameSimulator):
    """
    Extended GameSimulator that records detailed statistics.
    
    Wraps the base GameSimulator and adds a Scorekeeper to record
    plays in baseball notation, generate box scores, and track
    individual player statistics.
    
    Usage:
        simulator = StatsEnabledGameSimulator(
            away_team, home_team,
            stats_mode=StatsTrackingMode.STANDARD
        )
        game_state = simulator.simulate_game()
        game_log = simulator.get_game_log()
    """
    
    def __init__(
        self,
        away_team: Team,
        home_team: Team,
        stats_mode: StatsTrackingMode = StatsTrackingMode.STANDARD,
        game_date: date = None,
        **kwargs
    ):
        """
        Initialize stats-enabled game simulator.
        
        Parameters
        ----------
        away_team : Team
            Away team
        home_team : Team
            Home team
        stats_mode : StatsTrackingMode
            Level of statistics tracking
        game_date : date
            Date of the game (for records)
        **kwargs
            Additional arguments passed to GameSimulator
        """
        super().__init__(away_team, home_team, **kwargs)
        
        self.stats_mode = stats_mode
        self.game_date = game_date or date.today()
        
        # Initialize scorekeeper if stats enabled
        if stats_mode != StatsTrackingMode.DISABLED:
            self.scorekeeper = Scorekeeper(
                game_id=str(uuid.uuid4())[:8],
                game_date=self.game_date,
                away_team=getattr(away_team, 'abbreviation', away_team.name[:3].upper()),
                home_team=getattr(home_team, 'abbreviation', home_team.name[:3].upper()),
            )
        else:
            self.scorekeeper = None
        
        # Track current inning for scorekeeper
        self._last_inning = 1
        self._last_is_top = True
    
    def simulate_half_inning(self):
        """Simulate a half inning with stats tracking."""
        # Notify scorekeeper of new half-inning
        if self.scorekeeper:
            self.scorekeeper.start_half_inning(
                self.game_state.inning,
                self.game_state.is_top
            )
        
        # Run base simulation
        super().simulate_half_inning()
        
        # End half-inning in scorekeeper
        if self.scorekeeper:
            # Count runners left on base
            lob = sum([
                1 if self.game_state.runner_on_first else 0,
                1 if self.game_state.runner_on_second else 0,
                1 if self.game_state.runner_on_third else 0,
            ])
            self.scorekeeper.end_half_inning(lob)
    
    def handle_strikeout_or_walk(self, outcome: str, batter):
        """Handle strikeout or walk with stats recording."""
        batting_team = self.away_team if self.game_state.is_top else self.home_team
        pitching_team = self.home_team if self.game_state.is_top else self.away_team
        pitcher = pitching_team.get_current_pitcher()
        
        # Record in scorekeeper
        if self.scorekeeper:
            batter_team_abbr = getattr(batting_team, 'abbreviation', batting_team.name[:3].upper())
            pitcher_team_abbr = getattr(pitching_team, 'abbreviation', pitching_team.name[:3].upper())
            
            if outcome == "strikeout":
                self.scorekeeper.record_strikeout(
                    batter_id=batter.name,  # Use name as ID for now
                    batter_name=batter.name,
                    batter_team=batter_team_abbr,
                    pitcher_id=pitcher.name,
                    pitcher_name=pitcher.name,
                    pitcher_team=pitcher_team_abbr,
                    looking=False,  # TODO: Determine from pitch sequence
                )
            elif outcome == "walk":
                # Check for runs scored on walk (bases loaded)
                runs_on_walk = 0
                if (self.game_state.runner_on_first and 
                    self.game_state.runner_on_second and 
                    self.game_state.runner_on_third):
                    runs_on_walk = 1
                
                self.scorekeeper.record_walk(
                    batter_id=batter.name,
                    batter_name=batter.name,
                    batter_team=batter_team_abbr,
                    pitcher_id=pitcher.name,
                    pitcher_name=pitcher.name,
                    pitcher_team=pitcher_team_abbr,
                    runs_scored=runs_on_walk,
                )
        
        # Run base implementation
        super().handle_strikeout_or_walk(outcome, batter)
    
    def process_play_result(self, play_result: PlayResult, batter, pitcher, at_bat_result=None):
        """Process play result with stats recording."""
        # Record in scorekeeper
        if self.scorekeeper and at_bat_result:
            batting_team = self.away_team if self.game_state.is_top else self.home_team
            pitching_team = self.home_team if self.game_state.is_top else self.away_team
            
            batter_team_abbr = getattr(batting_team, 'abbreviation', batting_team.name[:3].upper())
            pitcher_team_abbr = getattr(pitching_team, 'abbreviation', pitching_team.name[:3].upper())
            
            # Extract physics data
            bb_result = at_bat_result.batted_ball_result
            exit_velocity = bb_result.get('exit_velocity') if bb_result else None
            launch_angle = bb_result.get('launch_angle') if bb_result else None
            distance = bb_result.get('distance') if bb_result else None
            
            # Get primary fielder position
            primary_fielder_pos = None
            if play_result.primary_fielder:
                primary_fielder_pos = getattr(play_result.primary_fielder, 'position', None)
            
            # Get relay positions if any
            relay_positions = []
            if hasattr(play_result, 'fielders_involved'):
                for f in play_result.fielders_involved:
                    if hasattr(f, 'position'):
                        relay_positions.append(f.position)
            
            # Calculate RBI
            rbi = play_result.runs_scored
            # Home runs: batter's RBI equals runs scored
            if play_result.outcome == PlayOutcome.HOME_RUN:
                rbi = play_result.runs_scored
            
            self.scorekeeper.record_batted_ball(
                batter_id=batter.name,
                batter_name=batter.name,
                batter_team=batter_team_abbr,
                pitcher_id=pitcher.name,
                pitcher_name=pitcher.name,
                pitcher_team=pitcher_team_abbr,
                play_result=play_result,
                exit_velocity=exit_velocity,
                launch_angle=launch_angle,
                distance=distance,
                primary_fielder_position=primary_fielder_pos,
                relay_positions=relay_positions,
                runs_scored=play_result.runs_scored,
                rbi=rbi,
            )
        
        # Run base implementation
        super().process_play_result(play_result, batter, pitcher, at_bat_result)
    
    def simulate_game(self, num_innings: int = 9, rng_seed: int = None) -> GameState:
        """Simulate game with stats finalization."""
        # Run base game simulation
        result = super().simulate_game(num_innings, rng_seed)
        
        # Finalize game log
        if self.scorekeeper:
            # Set pitcher decisions
            self._assign_pitcher_decisions()
        
        return result
    
    def _assign_pitcher_decisions(self):
        """Assign W/L/S decisions to pitchers."""
        if not self.scorekeeper:
            return
        
        game_state = self.game_state
        away_won = game_state.away_score > game_state.home_score
        
        # Simple decision logic:
        # Win goes to starter of winning team
        # Loss goes to starter of losing team
        # (In reality this is more complex - based on when lead was taken)
        
        for pid, stats in self.scorekeeper.pitching_stats.items():
            if away_won:
                if stats.team == self.scorekeeper.away_team:
                    # Check if this was the starter
                    if list(self.scorekeeper.pitching_stats.keys()).index(pid) == 0:
                        stats.win = True
                else:
                    # First pitcher on losing team gets loss
                    home_pitchers = [s for s in self.scorekeeper.pitching_stats.values() 
                                    if s.team == self.scorekeeper.home_team]
                    if home_pitchers and stats == home_pitchers[0]:
                        stats.loss = True
            else:
                if stats.team == self.scorekeeper.home_team:
                    home_pitchers = [s for s in self.scorekeeper.pitching_stats.values() 
                                    if s.team == self.scorekeeper.home_team]
                    if home_pitchers and stats == home_pitchers[0]:
                        stats.win = True
                else:
                    away_pitchers = [s for s in self.scorekeeper.pitching_stats.values() 
                                    if s.team == self.scorekeeper.away_team]
                    if away_pitchers and stats == away_pitchers[0]:
                        stats.loss = True
    
    def get_game_log(self) -> Optional[GameLog]:
        """
        Get the complete game log with all statistics.
        
        Returns
        -------
        GameLog or None
            Complete game log if stats tracking enabled, None otherwise
        """
        if not self.scorekeeper:
            return None
        
        return self.scorekeeper.finalize_game()
    
    def print_box_score(self):
        """Print formatted box score to console."""
        game_log = self.get_game_log()
        if not game_log:
            print("Stats tracking not enabled")
            return
        
        print("\n" + "=" * 70)
        print(game_log.get_line_score_str())
        print("=" * 70)
        
        # Away batting
        print(f"\n{game_log.away_team} Batting")
        print("-" * 50)
        print(f"{'Player':<20} {'AB':>3} {'R':>3} {'H':>3} {'RBI':>3} {'BB':>3} {'K':>3}")
        for stats in game_log.away_batting:
            if stats.plate_appearances > 0:
                print(stats.box_score_line())
        
        # Home batting
        print(f"\n{game_log.home_team} Batting")
        print("-" * 50)
        print(f"{'Player':<20} {'AB':>3} {'R':>3} {'H':>3} {'RBI':>3} {'BB':>3} {'K':>3}")
        for stats in game_log.home_batting:
            if stats.plate_appearances > 0:
                print(stats.box_score_line())
        
        # Pitching
        print(f"\n{game_log.away_team} Pitching")
        print("-" * 60)
        print(f"{'Pitcher':<25} {'IP':>4} {'H':>3} {'R':>3} {'ER':>3} {'BB':>3} {'K':>3}")
        for stats in game_log.away_pitching:
            print(stats.box_score_line())
        
        print(f"\n{game_log.home_team} Pitching")
        print("-" * 60)
        print(f"{'Pitcher':<25} {'IP':>4} {'H':>3} {'R':>3} {'ER':>3} {'BB':>3} {'K':>3}")
        for stats in game_log.home_pitching:
            print(stats.box_score_line())
        
        print("=" * 70)


def simulate_game_with_stats(
    away_team: Team,
    home_team: Team,
    game_date: date = None,
    stats_mode: StatsTrackingMode = StatsTrackingMode.STANDARD,
    **kwargs
) -> tuple:
    """
    Convenience function to simulate a game and return both state and log.
    
    Parameters
    ----------
    away_team : Team
        Away team
    home_team : Team
        Home team
    game_date : date
        Date of game
    stats_mode : StatsTrackingMode
        Level of stats tracking
    **kwargs
        Additional arguments for GameSimulator
    
    Returns
    -------
    tuple
        (GameState, GameLog) - game state and optional game log
    """
    simulator = StatsEnabledGameSimulator(
        away_team,
        home_team,
        stats_mode=stats_mode,
        game_date=game_date,
        **kwargs
    )
    
    game_state = simulator.simulate_game()
    game_log = simulator.get_game_log()
    
    return game_state, game_log
