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
    
    # Batting stats
    away_hits: int = 0
    home_hits: int = 0
    away_home_runs: int = 0
    home_home_runs: int = 0
    away_strikeouts: int = 0
    home_strikeouts: int = 0
    away_walks: int = 0
    home_walks: int = 0
    
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
    
    # Create simulator
    sim = GameSimulator(
        away_team,
        home_team,
        verbose=False,
        debug_metrics=0,
        ballpark=ballpark,
        wind_enabled=True,
        starter_innings=5,
        simulation_mode=SimulationMode.ULTRA_FAST
    )
    
    # Simulate game
    final_state = sim.simulate_game(num_innings=9)
    
    return GameResult(
        date=game_date,
        away_team=away_abbr,
        home_team=home_abbr,
        away_score=final_state.away_score,
        home_score=final_state.home_score,
        away_hits=final_state.away_hits,
        home_hits=final_state.home_hits,
        away_home_runs=final_state.away_home_runs,
        home_home_runs=final_state.home_home_runs,
        away_strikeouts=final_state.away_strikeouts,
        home_strikeouts=final_state.home_strikeouts,
        away_walks=final_state.away_walks,
        home_walks=final_state.home_walks,
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
        verbose: bool = True
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
        """
        self.schedule = ScheduleLoader(schedule_path)
        self.season = season
        self.num_workers = num_workers or max(1, cpu_count() - 1)
        self.verbose = verbose
        
        # Initialize standings for all teams
        self.standings: Dict[str, TeamStanding] = {}
        for team in self.schedule.get_all_teams():
            self.standings[team] = TeamStanding(team=team)
        
        # Track all results
        self.results: List[GameResult] = []
        self.current_date: Optional[date] = None
        
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
        
        self.results.extend(results)
        self.current_date = game_date
        
        return results
    
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
        
        return {
            'games_played': len(self.results),
            'total_runs': total_runs,
            'runs_per_game': total_runs / len(self.results),
            'total_home_runs': total_hrs,
            'home_runs_per_game': total_hrs / len(self.results),
            'home_team_wins': sum(1 for r in self.results if r.home_score > r.away_score),
            'away_team_wins': sum(1 for r in self.results if r.away_score > r.home_score),
        }
    
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
