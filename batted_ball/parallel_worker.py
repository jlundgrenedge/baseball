"""
Parallel simulation worker for Streamlit and other multi-process applications.

This module contains worker functions that can be safely pickled and run
in separate processes. Kept separate from Streamlit to avoid import issues.
"""

from dataclasses import dataclass, field
from typing import List, Tuple

from batted_ball.database.team_loader import TeamLoader
from batted_ball.game_simulation import GameSimulator
from batted_ball.constants import SimulationMode


@dataclass
class ParallelGameResult:
    """Result from a single parallel game simulation."""
    game_number: int
    away_team_name: str
    home_team_name: str
    away_score: int
    home_score: int
    
    # Batting stats - away
    away_at_bats: int = 0
    away_hits: int = 0
    away_singles: int = 0
    away_doubles: int = 0
    away_triples: int = 0
    away_home_runs: int = 0
    away_walks: int = 0
    away_strikeouts: int = 0
    away_errors: int = 0
    away_ground_balls: int = 0
    away_line_drives: int = 0
    away_fly_balls: int = 0
    away_exit_velocities: List[float] = field(default_factory=list)
    away_launch_angles: List[float] = field(default_factory=list)
    
    # Batting stats - home
    home_at_bats: int = 0
    home_hits: int = 0
    home_singles: int = 0
    home_doubles: int = 0
    home_triples: int = 0
    home_home_runs: int = 0
    home_walks: int = 0
    home_strikeouts: int = 0
    home_errors: int = 0
    home_ground_balls: int = 0
    home_line_drives: int = 0
    home_fly_balls: int = 0
    home_exit_velocities: List[float] = field(default_factory=list)
    home_launch_angles: List[float] = field(default_factory=list)
    
    # Pitching (for series metrics)
    total_pitches: int = 0


def simulate_game_worker(args: Tuple) -> ParallelGameResult:
    """
    Worker function for parallel game simulation.
    
    Runs in a separate process - loads teams from database.
    
    Parameters
    ----------
    args : tuple
        (game_number, away_name, away_season, home_name, home_season)
    
    Returns
    -------
    ParallelGameResult
        Complete game statistics
    """
    game_number, away_name, away_season, home_name, home_season = args
    
    # Load teams in this process from database
    loader = TeamLoader("baseball_teams.db")
    away_team = loader.load_team(away_name, away_season)
    home_team = loader.load_team(home_name, home_season)
    loader.close()
    
    if not away_team or not home_team:
        return ParallelGameResult(
            game_number=game_number,
            away_team_name=away_name,
            home_team_name=home_name,
            away_score=0,
            home_score=0
        )
    
    # Reset pitcher states
    away_team.reset_pitcher_state()
    home_team.reset_pitcher_state()
    
    # Create simulator
    sim = GameSimulator(
        away_team,
        home_team,
        verbose=False,
        debug_metrics=0,
        wind_enabled=True,
        simulation_mode=SimulationMode.FAST
    )
    
    # Simulate game
    final_state = sim.simulate_game(num_innings=9)
    
    # Return result with all stats
    return ParallelGameResult(
        game_number=game_number,
        away_team_name=away_name,
        home_team_name=home_name,
        away_score=final_state.away_score,
        home_score=final_state.home_score,
        # Away batting
        away_at_bats=final_state.away_at_bats,
        away_hits=final_state.away_hits,
        away_singles=final_state.away_singles,
        away_doubles=final_state.away_doubles,
        away_triples=final_state.away_triples,
        away_home_runs=final_state.away_home_runs,
        away_walks=final_state.away_walks,
        away_strikeouts=final_state.away_strikeouts,
        away_errors=final_state.away_errors,
        away_ground_balls=final_state.away_ground_balls,
        away_line_drives=final_state.away_line_drives,
        away_fly_balls=final_state.away_fly_balls,
        away_exit_velocities=list(final_state.away_exit_velocities),
        away_launch_angles=list(final_state.away_launch_angles),
        # Home batting
        home_at_bats=final_state.home_at_bats,
        home_hits=final_state.home_hits,
        home_singles=final_state.home_singles,
        home_doubles=final_state.home_doubles,
        home_triples=final_state.home_triples,
        home_home_runs=final_state.home_home_runs,
        home_walks=final_state.home_walks,
        home_strikeouts=final_state.home_strikeouts,
        home_errors=final_state.home_errors,
        home_ground_balls=final_state.home_ground_balls,
        home_line_drives=final_state.home_line_drives,
        home_fly_balls=final_state.home_fly_balls,
        home_exit_velocities=list(final_state.home_exit_velocities),
        home_launch_angles=list(final_state.home_launch_angles),
        total_pitches=final_state.total_pitches,
    )


class MockGameState:
    """Adapter to feed ParallelGameResult into SeriesMetrics.update_from_game()."""
    def __init__(self, result: ParallelGameResult):
        self.away_score = result.away_score
        self.home_score = result.home_score
        self.away_at_bats = result.away_at_bats
        self.away_hits = result.away_hits
        self.away_singles = result.away_singles
        self.away_doubles = result.away_doubles
        self.away_triples = result.away_triples
        self.away_home_runs = result.away_home_runs
        self.away_walks = result.away_walks
        self.away_strikeouts = result.away_strikeouts
        self.away_errors = result.away_errors
        self.away_ground_balls = result.away_ground_balls
        self.away_line_drives = result.away_line_drives
        self.away_fly_balls = result.away_fly_balls
        self.away_exit_velocities = result.away_exit_velocities
        self.away_launch_angles = result.away_launch_angles
        self.home_at_bats = result.home_at_bats
        self.home_hits = result.home_hits
        self.home_singles = result.home_singles
        self.home_doubles = result.home_doubles
        self.home_triples = result.home_triples
        self.home_home_runs = result.home_home_runs
        self.home_walks = result.home_walks
        self.home_strikeouts = result.home_strikeouts
        self.home_errors = result.home_errors
        self.home_ground_balls = result.home_ground_balls
        self.home_line_drives = result.home_line_drives
        self.home_fly_balls = result.home_fly_balls
        self.home_exit_velocities = result.home_exit_velocities
        self.home_launch_angles = result.home_launch_angles
        self.total_pitches = result.total_pitches
