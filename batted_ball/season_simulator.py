"""
2025 MLB Season Simulator.

Simulates the full 2025 MLB season using the real schedule,
processing games day-by-day with parallel execution.

Features:
- Day-by-day simulation following the real schedule
- Parallel processing of each day's games
- Standings tracking with win-loss records
- Progress tracking and resumable simulation
- Detailed game logs and statistics
"""

import sys
import time
import random
import sqlite3
from datetime import date, datetime
from pathlib import Path
from typing import List, Dict, Optional, Tuple, Any
from dataclasses import dataclass, field
from concurrent.futures import ProcessPoolExecutor, as_completed
from multiprocessing import cpu_count
import json

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from batted_ball.schedule_loader import ScheduleLoader, ScheduledGame
from batted_ball.database.team_loader import TeamLoader
from batted_ball.database.team_mappings import TEAM_DIVISIONS, get_team_division
from batted_ball.game_simulation import GameSimulator
from batted_ball.stats_integration import StatsEnabledGameSimulator, StatsTrackingMode
from batted_ball.series_metrics import SeriesMetrics
from batted_ball.constants import SimulationMode


# Ballpark mapping for home teams
TEAM_BALLPARKS = {
    'CHC': 'wrigley', 'CIN': 'great_american', 'NYY': 'yankee',
    'BOS': 'fenway', 'LAD': 'dodger', 'SF': 'oracle', 'COL': 'coors',
    'HOU': 'minute_maid', 'SD': 'petco',
}


@dataclass
class GameResult:
    """Result from a single game simulation."""
    date: date
    away_team: str
    home_team: str
    away_score: int
    home_score: int
    
    # Batting stats - Away
    away_hits: int = 0
    away_singles: int = 0
    away_doubles: int = 0
    away_triples: int = 0
    away_home_runs: int = 0
    away_strikeouts: int = 0
    away_walks: int = 0
    away_at_bats: int = 0
    away_ground_balls: int = 0
    away_line_drives: int = 0
    away_fly_balls: int = 0
    away_exit_velocities: List[float] = field(default_factory=list)
    away_launch_angles: List[float] = field(default_factory=list)
    away_errors: int = 0
    
    # Batting stats - Home
    home_hits: int = 0
    home_singles: int = 0
    home_doubles: int = 0
    home_triples: int = 0
    home_home_runs: int = 0
    home_strikeouts: int = 0
    home_walks: int = 0
    home_at_bats: int = 0
    home_ground_balls: int = 0
    home_line_drives: int = 0
    home_fly_balls: int = 0
    home_exit_velocities: List[float] = field(default_factory=list)
    home_launch_angles: List[float] = field(default_factory=list)
    home_errors: int = 0
    
    # Game totals
    total_pitches: int = 0
    
    # Player-level statistics (serializable dicts for parallel processing)
    # Each list contains dicts with player stats - serialized from PlayerGameBatting/Pitching
    away_player_batting: List[Dict[str, Any]] = field(default_factory=list)
    home_player_batting: List[Dict[str, Any]] = field(default_factory=list)
    away_player_pitching: List[Dict[str, Any]] = field(default_factory=list)
    home_player_pitching: List[Dict[str, Any]] = field(default_factory=list)
    
    @property
    def winner(self) -> str:
        return self.away_team if self.away_score > self.home_score else self.home_team
    
    @property
    def loser(self) -> str:
        return self.home_team if self.away_score > self.home_score else self.away_team
    
    def __str__(self) -> str:
        return f"{self.away_team} {self.away_score} @ {self.home_team} {self.home_score}"


@dataclass
class TeamStanding:
    """Standings record for a single team."""
    team: str
    wins: int = 0
    losses: int = 0
    runs_scored: int = 0
    runs_allowed: int = 0
    home_wins: int = 0
    home_losses: int = 0
    away_wins: int = 0
    away_losses: int = 0
    streak: int = 0  # Positive = winning, negative = losing
    last_10: List[str] = field(default_factory=list)  # 'W' or 'L'
    
    @property
    def win_pct(self) -> float:
        total = self.wins + self.losses
        return self.wins / total if total > 0 else 0.0
    
    @property
    def run_diff(self) -> int:
        return self.runs_scored - self.runs_allowed
    
    @property
    def games_back(self) -> float:
        """Calculated relative to leader when displayed."""
        return 0.0  # Set by standings display
    
    @property
    def last_10_record(self) -> str:
        wins = sum(1 for x in self.last_10[-10:] if x == 'W')
        losses = 10 - wins if len(self.last_10) >= 10 else len(self.last_10) - wins
        return f"{wins}-{losses}"
    
    @property
    def streak_str(self) -> str:
        if self.streak > 0:
            return f"W{self.streak}"
        elif self.streak < 0:
            return f"L{-self.streak}"
        return "-"
    
    def update_from_game(self, result: GameResult, is_home: bool):
        """Update standings from a game result."""
        if is_home:
            self.runs_scored += result.home_score
            self.runs_allowed += result.away_score
            won = result.home_score > result.away_score
            if won:
                self.wins += 1
                self.home_wins += 1
                self.streak = self.streak + 1 if self.streak > 0 else 1
                self.last_10.append('W')
            else:
                self.losses += 1
                self.home_losses += 1
                self.streak = self.streak - 1 if self.streak < 0 else -1
                self.last_10.append('L')
        else:
            self.runs_scored += result.away_score
            self.runs_allowed += result.home_score
            won = result.away_score > result.home_score
            if won:
                self.wins += 1
                self.away_wins += 1
                self.streak = self.streak + 1 if self.streak > 0 else 1
                self.last_10.append('W')
            else:
                self.losses += 1
                self.away_losses += 1
                self.streak = self.streak - 1 if self.streak < 0 else -1
                self.last_10.append('L')
        
        # Keep only last 10
        if len(self.last_10) > 10:
            self.last_10 = self.last_10[-10:]


# Database team name cache
_team_name_cache: Dict[str, Tuple[str, int]] = {}


def _batting_to_dict(batting) -> Dict[str, Any]:
    """Convert PlayerGameBatting to serializable dict."""
    return {
        'player_id': batting.player_id,
        'player_name': batting.player_name,
        'team': batting.team,
        'position': batting.position,
        'batting_order': batting.batting_order,
        'plate_appearances': batting.plate_appearances,
        'at_bats': batting.at_bats,
        'runs': batting.runs,
        'hits': batting.hits,
        'doubles': batting.doubles,
        'triples': batting.triples,
        'home_runs': batting.home_runs,
        'rbi': batting.rbi,
        'walks': batting.walks,
        'strikeouts': batting.strikeouts,
        'hit_by_pitch': batting.hit_by_pitch,
        'sacrifice_flies': batting.sacrifice_flies,
        'sacrifice_bunts': batting.sacrifice_bunts,
        'stolen_bases': batting.stolen_bases,
        'caught_stealing': batting.caught_stealing,
        'gidp': batting.gidp,
        'left_on_base': batting.left_on_base,
        'exit_velocities': list(batting.exit_velocities),
        'launch_angles': list(batting.launch_angles),
    }


def _pitching_to_dict(pitching) -> Dict[str, Any]:
    """Convert PlayerGamePitching to serializable dict."""
    return {
        'player_id': pitching.player_id,
        'player_name': pitching.player_name,
        'team': pitching.team,
        'outs_recorded': pitching.outs_recorded,
        'hits_allowed': pitching.hits_allowed,
        'runs_allowed': pitching.runs_allowed,
        'earned_runs': pitching.earned_runs,
        'walks': pitching.walks,
        'strikeouts': pitching.strikeouts,
        'home_runs_allowed': pitching.home_runs_allowed,
        'hit_batters': pitching.hit_batters,
        'win': pitching.win,
        'loss': pitching.loss,
        'save': pitching.save,
        'hold': pitching.hold,
        'blown_save': pitching.blown_save,
        'pitches': pitching.pitches,
        'strikes': pitching.strikes,
        'balls': pitching.balls,
        'ground_balls': pitching.ground_balls,
        'fly_balls': pitching.fly_balls,
        'line_drives': pitching.line_drives,
        'batters_faced': pitching.batters_faced,
    }


def _get_team_name_from_db(team_abbr: str, season: int = 2024) -> Optional[Tuple[str, int]]:
    """Look up team full name from database by abbreviation."""
    cache_key = f"{team_abbr}_{season}"
    if cache_key in _team_name_cache:
        return _team_name_cache[cache_key]
    
    try:
        conn = sqlite3.connect('baseball_teams.db')
        cursor = conn.cursor()
        
        # Try exact match first
        cursor.execute(
            "SELECT team_name, season FROM teams WHERE team_abbr = ? AND season = ?",
            (team_abbr, season)
        )
        row = cursor.fetchone()
        
        # If no exact season match, try to find any season
        if not row:
            cursor.execute(
                "SELECT team_name, season FROM teams WHERE team_abbr = ? ORDER BY season DESC LIMIT 1",
                (team_abbr,)
            )
            row = cursor.fetchone()
        
        conn.close()
        
        if row:
            result = (row[0], row[1])
            _team_name_cache[cache_key] = result
            return result
        return None
    except Exception:
        return None


def _simulate_game_worker(args: Tuple) -> Optional[GameResult]:
    """
    Worker function for parallel game simulation.
    
    Parameters
    ----------
    args : tuple
        (game_date, away_abbr, home_abbr, season)
    
    Returns
    -------
    GameResult or None
        Game result if successful
    """
    game_date, away_abbr, home_abbr, season = args
    
    # Look up team names
    away_info = _get_team_name_from_db(away_abbr, season)
    home_info = _get_team_name_from_db(home_abbr, season)
    
    if not away_info or not home_info:
        return None
    
    away_name, away_season = away_info
    home_name, home_season = home_info
    
    # Load teams
    loader = TeamLoader()
    away_team = loader.load_team(away_name, away_season)
    home_team = loader.load_team(home_name, home_season)
    loader.close()
    
    if not away_team or not home_team:
        return None
    
    # Reset pitcher states
    away_team.reset_pitcher_state()
    home_team.reset_pitcher_state()
    
    # Pick starting pitchers (rotate through rotation)
    away_starters = away_team.get_starters()
    home_starters = home_team.get_starters()
    
    if away_starters:
        # Use random starter for variety
        away_starter = random.choice(away_starters[:min(5, len(away_starters))])
        for i, p in enumerate(away_team.pitchers):
            if p.name == away_starter.name:
                away_team.pitchers[0], away_team.pitchers[i] = away_team.pitchers[i], away_team.pitchers[0]
                break
    
    if home_starters:
        home_starter = random.choice(home_starters[:min(5, len(home_starters))])
        for i, p in enumerate(home_team.pitchers):
            if p.name == home_starter.name:
                home_team.pitchers[0], home_team.pitchers[i] = home_team.pitchers[i], home_team.pitchers[0]
                break
    
    # Get ballpark
    ballpark = TEAM_BALLPARKS.get(home_abbr, 'generic')
    
    # Create stats-enabled simulator for player-level tracking
    sim = StatsEnabledGameSimulator(
        away_team,
        home_team,
        stats_mode=StatsTrackingMode.BASIC,  # Basic mode for speed (box scores only)
        game_date=game_date,
        verbose=False,
        debug_metrics=0,
        ballpark=ballpark,
        wind_enabled=True,
        starter_innings=5,
        simulation_mode=SimulationMode.ULTRA_FAST
    )
    
    # Simulate game
    final_state = sim.simulate_game(num_innings=9)
    
    # Get player-level stats from game log
    game_log = sim.get_game_log()
    
    # Convert player stats to serializable dicts
    away_batting = []
    home_batting = []
    away_pitching = []
    home_pitching = []
    
    if game_log:
        for batter in game_log.away_batting:
            if batter.plate_appearances > 0:
                away_batting.append(_batting_to_dict(batter))
        for batter in game_log.home_batting:
            if batter.plate_appearances > 0:
                home_batting.append(_batting_to_dict(batter))
        for pitcher in game_log.away_pitching:
            away_pitching.append(_pitching_to_dict(pitcher))
        for pitcher in game_log.home_pitching:
            home_pitching.append(_pitching_to_dict(pitcher))
    
    return GameResult(
        date=game_date,
        away_team=away_abbr,
        home_team=home_abbr,
        away_score=final_state.away_score,
        home_score=final_state.home_score,
        # Away batting stats
        away_hits=final_state.away_hits,
        away_singles=final_state.away_singles,
        away_doubles=final_state.away_doubles,
        away_triples=final_state.away_triples,
        away_home_runs=final_state.away_home_runs,
        away_strikeouts=final_state.away_strikeouts,
        away_walks=final_state.away_walks,
        away_at_bats=final_state.away_at_bats,
        away_ground_balls=final_state.away_ground_balls,
        away_line_drives=final_state.away_line_drives,
        away_fly_balls=final_state.away_fly_balls,
        away_exit_velocities=list(final_state.away_exit_velocities),
        away_launch_angles=list(final_state.away_launch_angles),
        away_errors=final_state.away_errors,
        # Home batting stats
        home_hits=final_state.home_hits,
        home_singles=final_state.home_singles,
        home_doubles=final_state.home_doubles,
        home_triples=final_state.home_triples,
        home_home_runs=final_state.home_home_runs,
        home_strikeouts=final_state.home_strikeouts,
        home_walks=final_state.home_walks,
        home_at_bats=final_state.home_at_bats,
        home_ground_balls=final_state.home_ground_balls,
        home_line_drives=final_state.home_line_drives,
        home_fly_balls=final_state.home_fly_balls,
        home_exit_velocities=list(final_state.home_exit_velocities),
        home_launch_angles=list(final_state.home_launch_angles),
        home_errors=final_state.home_errors,
        # Game totals
        total_pitches=final_state.total_pitches,
        # Player-level stats
        away_player_batting=away_batting,
        home_player_batting=home_batting,
        away_player_pitching=away_pitching,
        home_player_pitching=home_pitching,
    )


class SeasonSimulator:
    """
    Simulates the 2025 MLB season day-by-day.
    
    Usage:
        sim = SeasonSimulator()
        sim.simulate_season()  # Run full season
        sim.simulate_range(start_date, end_date)  # Run date range
        sim.print_standings()
    """
    
    def __init__(
        self,
        schedule_path: Optional[str] = None,
        season: int = 2024,  # Database season to use for rosters
        num_workers: Optional[int] = None,
        verbose: bool = True,
        stats_db: Optional['StatsDatabase'] = None,
        stats_season_id: Optional[int] = None,
    ):
        """
        Initialize the season simulator.
        
        Parameters
        ----------
        schedule_path : str, optional
            Path to schedule CSV
        season : int
            Season year to use for team rosters in database
        num_workers : int, optional
            Number of parallel workers (default: CPU count - 1)
        verbose : bool
            Print progress output
        stats_db : StatsDatabase, optional
            Statistics database for recording player stats
        stats_season_id : int, optional
            Season ID in stats database (required if stats_db provided)
        """
        self.schedule = ScheduleLoader(schedule_path)
        self.season = season
        self.num_workers = num_workers or max(1, cpu_count() - 1)
        self.verbose = verbose
        
        # Stats tracking
        self.stats_db = stats_db
        self.stats_season_id = stats_season_id
        
        # Initialize standings for all teams
        self.standings: Dict[str, TeamStanding] = {}
        for team in self.schedule.get_all_teams():
            self.standings[team] = TeamStanding(team=team)
        
        # Track all results
        self.results: List[GameResult] = []
        self.current_date: Optional[date] = None
        
        # Aggregate series metrics across all games
        self.series_metrics = SeriesMetrics()
        
        # Track which teams are in database
        self._available_teams: Optional[set] = None
    
    def _get_available_teams(self) -> set:
        """Get teams that are available in the database."""
        if self._available_teams is not None:
            return self._available_teams
        
        available = set()
        for team_abbr in self.schedule.get_all_teams():
            if _get_team_name_from_db(team_abbr, self.season):
                available.add(team_abbr)
        
        self._available_teams = available
        return available
    
    def _can_simulate_game(self, game: ScheduledGame) -> bool:
        """Check if we have both teams in the database."""
        available = self._get_available_teams()
        return game.away_team in available and game.home_team in available
    
    def simulate_day(self, game_date: date) -> List[GameResult]:
        """
        Simulate all games for a single day.
        
        Parameters
        ----------
        game_date : date
            The date to simulate
        
        Returns
        -------
        List[GameResult]
            Results of all games on that date
        """
        games = self.schedule.get_games_for_date(game_date)
        
        if not games:
            return []
        
        # Filter to games we can simulate
        playable = [g for g in games if self._can_simulate_game(g)]
        
        if not playable:
            return []
        
        # Prepare arguments for parallel simulation
        game_args = [
            (game_date, g.away_team, g.home_team, self.season)
            for g in playable
        ]
        
        # Run games in parallel
        results = []
        with ProcessPoolExecutor(max_workers=min(self.num_workers, len(game_args))) as executor:
            futures = [executor.submit(_simulate_game_worker, args) for args in game_args]
            
            for future in as_completed(futures):
                result = future.result()
                if result:
                    results.append(result)
                    
                    # Update standings
                    self.standings[result.away_team].update_from_game(result, is_home=False)
                    self.standings[result.home_team].update_from_game(result, is_home=True)
                    
                    # Update series metrics (GameResult has same attributes as GameState)
                    self.series_metrics.update_from_game(result)
                    
                    # Record to stats database if enabled
                    if self.stats_db and self.stats_season_id:
                        self._record_game_to_stats_db(result)
        
        self.results.extend(results)
        self.current_date = game_date
        
        return results
    
    def _record_game_to_stats_db(self, result: GameResult):
        """Record a game result to the stats database."""
        self.stats_db.record_game_from_dicts(
            season_id=self.stats_season_id,
            game_date=result.date,
            away_team=result.away_team,
            home_team=result.home_team,
            away_score=result.away_score,
            home_score=result.home_score,
            away_batting=result.away_player_batting,
            home_batting=result.home_player_batting,
            away_pitching=result.away_player_pitching,
            home_pitching=result.home_player_pitching,
        )
    
    def simulate_range(
        self,
        start_date: date,
        end_date: date,
        progress_callback: Optional[callable] = None
    ) -> Dict[str, Any]:
        """
        Simulate games within a date range.
        
        Parameters
        ----------
        start_date : date
            First date to simulate (inclusive)
        end_date : date
            Last date to simulate (inclusive)
        progress_callback : callable, optional
            Function called with (current_date, total_dates, games_today)
        
        Returns
        -------
        Dict
            Summary statistics
        """
        games_by_date = self.schedule.get_games_in_range(start_date, end_date)
        dates = sorted(games_by_date.keys())
        
        if self.verbose:
            print(f"\n{'='*60}")
            print(f"  2025 MLB SEASON SIMULATION")
            print(f"{'='*60}")
            print(f"  Date range: {start_date} to {end_date}")
            print(f"  Game days: {len(dates)}")
            print(f"  Workers: {self.num_workers}")
            print(f"{'='*60}\n")
        
        total_games = 0
        skipped_games = 0
        start_time = time.time()
        
        for i, game_date in enumerate(dates):
            scheduled = games_by_date[game_date]
            playable = [g for g in scheduled if self._can_simulate_game(g)]
            
            if self.verbose:
                print(f"[{game_date}] Simulating {len(playable)}/{len(scheduled)} games...", end='', flush=True)
            
            day_results = self.simulate_day(game_date)
            
            total_games += len(day_results)
            skipped_games += len(scheduled) - len(playable)
            
            if self.verbose:
                print(f" Done ({len(day_results)} completed)")
            
            if progress_callback:
                progress_callback(game_date, len(dates), len(day_results))
        
        elapsed = time.time() - start_time
        
        return {
            'start_date': start_date,
            'end_date': end_date,
            'game_days': len(dates),
            'games_simulated': total_games,
            'games_skipped': skipped_games,
            'elapsed_seconds': elapsed,
            'games_per_second': total_games / elapsed if elapsed > 0 else 0,
        }
    
    def simulate_season(self, progress_callback: Optional[callable] = None) -> Dict[str, Any]:
        """
        Simulate the entire 2025 season.
        
        Parameters
        ----------
        progress_callback : callable, optional
            Function called with (current_date, total_dates, games_today)
        
        Returns
        -------
        Dict
            Summary statistics
        """
        first_date, last_date = self.schedule.get_date_range()
        return self.simulate_range(first_date, last_date, progress_callback)
    
    def get_standings(self, league: Optional[str] = None, division: Optional[str] = None) -> List[TeamStanding]:
        """
        Get current standings, optionally filtered by league/division.
        
        Parameters
        ----------
        league : str, optional
            Filter by league ('AL' or 'NL')
        division : str, optional
            Filter by division ('East', 'Central', 'West')
        
        Returns
        -------
        List[TeamStanding]
            Standings sorted by win percentage
        """
        standings_list = []
        for s in self.standings.values():
            # Filter by league/division if specified
            team_div = get_team_division(s.team)
            if team_div:
                team_league, team_division = team_div
                if league and team_league != league:
                    continue
                if division and team_division != division:
                    continue
            standings_list.append(s)
        
        return sorted(standings_list, key=lambda s: (s.wins, s.run_diff), reverse=True)
    
    def get_standings_by_division(self) -> Dict[str, List[TeamStanding]]:
        """
        Get standings organized by division.
        
        Returns
        -------
        Dict[str, List[TeamStanding]]
            Dictionary with keys like 'AL East', 'NL West', etc.
        """
        divisions = {}
        for team_abbr, standing in self.standings.items():
            div_info = get_team_division(team_abbr)
            if div_info:
                league, division = div_info
                div_key = f"{league} {division}"
            else:
                div_key = "Unknown"
            
            if div_key not in divisions:
                divisions[div_key] = []
            divisions[div_key].append(standing)
        
        # Sort each division by wins
        for div_key in divisions:
            divisions[div_key] = sorted(
                divisions[div_key],
                key=lambda s: (s.wins, s.run_diff),
                reverse=True
            )
        
        return divisions
    
    def print_standings(self, top_n: Optional[int] = None, by_division: bool = True):
        """Print current standings to console."""
        
        if by_division:
            self.print_division_standings()
        else:
            self._print_overall_standings(top_n)
    
    def print_division_standings(self):
        """Print standings organized by division."""
        divisions = self.get_standings_by_division()
        
        # Define order for display
        division_order = [
            'AL East', 'AL Central', 'AL West',
            'NL East', 'NL Central', 'NL West'
        ]
        
        print(f"\n{'='*74}")
        print(f"  2025 MLB STANDINGS BY DIVISION (through {self.current_date})")
        print(f"{'='*74}")
        
        for div_key in division_order:
            if div_key not in divisions:
                continue
            
            standings = divisions[div_key]
            if not standings:
                continue
            
            print(f"\n  {div_key}")
            print(f"  {'-'*70}")
            print(f"  {'Team':<5} {'W':>4} {'L':>4} {'Pct':>6} {'GB':>5} {'RS':>5} {'RA':>5} {'Diff':>5} {'Strk':>5} {'L10':>6}")
            print(f"  {'-'*70}")
            
            leader = standings[0]
            leader_wins = leader.wins
            leader_losses = leader.losses
            
            for s in standings:
                # Calculate games back
                gb = ((leader_wins - s.wins) + (s.losses - leader_losses)) / 2
                gb_str = "-" if gb == 0 else f"{gb:.1f}"
                
                print(f"  {s.team:<5} {s.wins:>4} {s.losses:>4} {s.win_pct:>6.3f} {gb_str:>5} "
                      f"{s.runs_scored:>5} {s.runs_allowed:>5} {s.run_diff:>+5} {s.streak_str:>5} {s.last_10_record:>6}")
        
        print(f"\n{'='*74}")
    
    def _print_overall_standings(self, top_n: Optional[int] = None):
        """Print overall standings (not by division)."""
        standings = self.get_standings()
        
        if top_n:
            standings = standings[:top_n]
        
        print(f"\n{'='*70}")
        print(f"  2025 MLB STANDINGS (through {self.current_date})")
        print(f"{'='*70}")
        print(f"{'Rank':<5} {'Team':<6} {'W':>4} {'L':>4} {'Pct':>6} {'GB':>5} {'RS':>5} {'RA':>5} {'Diff':>5} {'Strk':>5} {'L10':>6}")
        print("-" * 70)
        
        leader_wins = standings[0].wins if standings else 0
        leader_losses = standings[0].losses if standings else 0
        
        for i, s in enumerate(standings, 1):
            # Calculate games back
            gb = ((leader_wins - s.wins) + (s.losses - leader_losses)) / 2
            gb_str = "-" if gb == 0 else f"{gb:.1f}"
            
            print(f"{i:<5} {s.team:<6} {s.wins:>4} {s.losses:>4} {s.win_pct:>6.3f} {gb_str:>5} "
                  f"{s.runs_scored:>5} {s.runs_allowed:>5} {s.run_diff:>+5} {s.streak_str:>5} {s.last_10_record:>6}")
        
        print("=" * 70)
    
    def get_summary_stats(self) -> Dict[str, Any]:
        """Get summary statistics for the simulation."""
        if not self.results:
            return {}
        
        total_runs = sum(r.away_score + r.home_score for r in self.results)
        total_hrs = sum(r.away_home_runs + r.home_home_runs for r in self.results)
        
        # Combine away and home batting stats for league-wide metrics
        away = self.series_metrics.away_batting
        home = self.series_metrics.home_batting
        
        # Combined totals
        total_at_bats = away.at_bats + home.at_bats
        total_hits = away.hits + home.hits
        total_singles = away.singles + home.singles
        total_doubles = away.doubles + home.doubles
        total_triples = away.triples + home.triples
        total_home_runs_b = away.home_runs + home.home_runs
        total_walks = away.walks + home.walks
        total_strikeouts = away.strikeouts + home.strikeouts
        total_ground_balls = away.ground_balls + home.ground_balls
        total_line_drives = away.line_drives + home.line_drives
        total_fly_balls = away.fly_balls + home.fly_balls
        total_bip = away.balls_in_play_no_hr + home.balls_in_play_no_hr
        
        # Combined exit velocities and launch angles
        all_exit_velocities = away.exit_velocities + home.exit_velocities
        all_launch_angles = away.launch_angles + home.launch_angles
        
        # Calculate rates
        plate_appearances = total_at_bats + total_walks
        batted_balls = total_ground_balls + total_line_drives + total_fly_balls
        
        # Batting stats
        batting_avg = total_hits / total_at_bats if total_at_bats > 0 else 0
        on_base_pct = (total_hits + total_walks) / plate_appearances if plate_appearances > 0 else 0
        total_bases = total_singles + 2*total_doubles + 3*total_triples + 4*total_home_runs_b
        slugging_pct = total_bases / total_at_bats if total_at_bats > 0 else 0
        ops = on_base_pct + slugging_pct
        hits_no_hr = total_hits - total_home_runs_b
        babip = hits_no_hr / total_bip if total_bip > 0 else 0
        strikeout_rate = 100 * total_strikeouts / plate_appearances if plate_appearances > 0 else 0
        walk_rate = 100 * total_walks / plate_appearances if plate_appearances > 0 else 0
        
        # Exit velocity and launch angle
        avg_exit_velocity = sum(all_exit_velocities) / len(all_exit_velocities) if all_exit_velocities else 0
        avg_launch_angle = sum(all_launch_angles) / len(all_launch_angles) if all_launch_angles else 0
        
        # Batted ball rates
        ground_ball_rate = 100 * total_ground_balls / batted_balls if batted_balls > 0 else 0
        line_drive_rate = 100 * total_line_drives / batted_balls if batted_balls > 0 else 0
        fly_ball_rate = 100 * total_fly_balls / batted_balls if batted_balls > 0 else 0
        
        # Pitching stats (combined from both teams)
        away_p = self.series_metrics.away_pitching
        home_p = self.series_metrics.home_pitching
        total_innings = away_p.innings_pitched + home_p.innings_pitched
        total_runs_allowed = away_p.runs_allowed + home_p.runs_allowed
        total_hits_allowed = away_p.hits_allowed + home_p.hits_allowed
        total_walks_p = away_p.walks + home_p.walks
        total_strikeouts_p = away_p.strikeouts + home_p.strikeouts
        total_hr_allowed = away_p.home_runs_allowed + home_p.home_runs_allowed
        
        era = 9 * total_runs_allowed / total_innings if total_innings > 0 else 0
        whip = (total_walks_p + total_hits_allowed) / total_innings if total_innings > 0 else 0
        k_per_9 = 9 * total_strikeouts_p / total_innings if total_innings > 0 else 0
        bb_per_9 = 9 * total_walks_p / total_innings if total_innings > 0 else 0
        hr_per_9 = 9 * total_hr_allowed / total_innings if total_innings > 0 else 0
        
        return {
            'games_played': len(self.results),
            'total_runs': total_runs,
            'runs_per_game': total_runs / len(self.results),
            'total_home_runs': total_hrs,
            'home_runs_per_game': total_hrs / len(self.results),
            'home_team_wins': sum(1 for r in self.results if r.home_score > r.away_score),
            'away_team_wins': sum(1 for r in self.results if r.away_score > r.home_score),
            # Batting stats
            'batting_avg': batting_avg,
            'on_base_pct': on_base_pct,
            'slugging_pct': slugging_pct,
            'ops': ops,
            'babip': babip,
            'strikeout_rate': strikeout_rate,
            'walk_rate': walk_rate,
            'avg_exit_velocity': avg_exit_velocity,
            'avg_launch_angle': avg_launch_angle,
            'ground_ball_rate': ground_ball_rate,
            'line_drive_rate': line_drive_rate,
            'fly_ball_rate': fly_ball_rate,
            # Pitching stats
            'era': era,
            'whip': whip,
            'k_per_9': k_per_9,
            'bb_per_9': bb_per_9,
            'hr_per_9': hr_per_9,
        }
    
    def get_series_metrics(self) -> SeriesMetrics:
        """Return the aggregated series metrics for all simulated games."""
        return self.series_metrics
    
    def save_results(self, filepath: str):
        """Save simulation results to JSON file."""
        # Get division info for each team
        def get_div_info(team_abbr):
            div = get_team_division(team_abbr)
            return {'league': div[0], 'division': div[1]} if div else {'league': None, 'division': None}
        
        data = {
            'meta': {
                'simulation_date': datetime.now().isoformat(),
                'season': self.season,
                'games_simulated': len(self.results),
                'last_game_date': str(self.current_date) if self.current_date else None,
            },
            'standings_by_division': {
                div_key: [
                    {
                        'team': s.team,
                        'wins': s.wins,
                        'losses': s.losses,
                        'win_pct': round(s.win_pct, 3),
                        'runs_scored': s.runs_scored,
                        'runs_allowed': s.runs_allowed,
                        'run_diff': s.run_diff,
                        'home_record': f"{s.home_wins}-{s.home_losses}",
                        'away_record': f"{s.away_wins}-{s.away_losses}",
                        'streak': s.streak_str,
                        'last_10': s.last_10_record,
                    }
                    for s in standings
                ]
                for div_key, standings in self.get_standings_by_division().items()
            },
            'standings': [
                {
                    'team': s.team,
                    **get_div_info(s.team),
                    'wins': s.wins,
                    'losses': s.losses,
                    'runs_scored': s.runs_scored,
                    'runs_allowed': s.runs_allowed,
                    'home_record': f"{s.home_wins}-{s.home_losses}",
                    'away_record': f"{s.away_wins}-{s.away_losses}",
                    'streak': s.streak_str,
                    'last_10': s.last_10_record,
                }
                for s in self.get_standings()
            ],
            'results': [
                {
                    'date': str(r.date),
                    'away': r.away_team,
                    'home': r.home_team,
                    'away_score': r.away_score,
                    'home_score': r.home_score,
                }
                for r in self.results
            ]
        }
        
        with open(filepath, 'w') as f:
            json.dump(data, f, indent=2)
        
        if self.verbose:
            print(f"\nResults saved to: {filepath}")


if __name__ == "__main__":
    # Quick test
    print("=== Season Simulator Test ===")
    
    sim = SeasonSimulator()
    
    # Show available teams
    available = sim._get_available_teams()
    print(f"\nTeams available in database: {len(available)}")
    if available:
        print(f"  {', '.join(sorted(available))}")
    else:
        print("  No teams found! Add teams first with manage_teams.py")
        sys.exit(1)
    
    # Simulate first week
    from datetime import date
    
    # Find a date with games
    for game_date in sim.schedule.get_all_game_dates():
        games = sim.schedule.get_games_for_date(game_date)
        playable = [g for g in games if sim._can_simulate_game(g)]
        if playable:
            print(f"\nSimulating {game_date}: {len(playable)} games")
            results = sim.simulate_day(game_date)
            print(f"  Completed {len(results)} games")
            for r in results:
                print(f"    {r}")
            break
    
    # Show standings
    sim.print_standings(top_n=10)
