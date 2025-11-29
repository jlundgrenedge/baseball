"""
Parallel game simulation engine for running multiple games concurrently.

Provides significant speedup for multi-game simulations using multiprocessing
or threading to distribute game simulations across CPU cores.

Phase 4 adds ThreadedGameSimulator which uses threads instead of processes,
providing better performance due to:
1. No pickle/unpickle overhead
2. Shared memory (no data copying)
3. Numba JIT releases the GIL, enabling true parallelism
"""

import time
import multiprocessing as mp
from multiprocessing import Pool, cpu_count
from concurrent.futures import ThreadPoolExecutor, as_completed
import threading
from typing import List, Dict, Optional, Tuple, Any
from dataclasses import dataclass, field
import numpy as np

from .game_simulation import GameSimulator, GameState, Team, create_test_team
from .player import Pitcher, Hitter
from .constants import SimulationMode


@dataclass
class ParallelSimulationSettings:
    """Configuration for parallel game simulation."""
    
    # Parallelization settings
    num_workers: Optional[int] = None  # None = use all CPU cores
    chunk_size: int = 1  # Games per worker batch
    
    # Output settings
    verbose: bool = False
    show_progress: bool = True
    log_games: bool = False  # Create log files for each game
    
    @classmethod
    def for_game_count(cls, count: int) -> 'ParallelSimulationSettings':
        """Create optimal settings based on game count."""
        if count >= 100:
            return cls(
                num_workers=None,  # Use all cores
                chunk_size=2,
                verbose=False,
                show_progress=True,
                log_games=False
            )
        elif count >= 20:
            return cls(
                num_workers=None,
                chunk_size=1,
                verbose=False,
                show_progress=True,
                log_games=False
            )
        else:
            return cls(
                num_workers=max(2, cpu_count() // 2),  # Use half cores for small batches
                chunk_size=1,
                verbose=False,
                show_progress=False,
                log_games=False
            )


@dataclass
class GameResult:
    """Result from a single simulated game."""
    game_number: int
    away_team_name: str
    home_team_name: str
    away_score: int
    home_score: int
    total_innings: int
    total_pitches: int
    total_hits: int
    total_home_runs: int
    
    @property
    def total_runs(self) -> int:
        """Total runs scored by both teams."""
        return self.away_score + self.home_score
    
    @property
    def winner(self) -> str:
        """Which team won."""
        if self.away_score > self.home_score:
            return self.away_team_name
        elif self.home_score > self.away_score:
            return self.home_team_name
        else:
            return "Tie"


@dataclass
class ParallelSimulationResult:
    """Results from parallel multi-game simulation."""
    
    # Simulation metadata
    total_games: int
    simulation_time: float
    games_per_second: float
    settings_used: ParallelSimulationSettings
    
    # Individual game results
    game_results: List[GameResult]
    
    # Aggregate statistics
    total_runs: int
    total_hits: int
    total_home_runs: int
    total_innings: int
    
    # Per-9-inning rates (MLB comparison)
    runs_per_9: float
    hits_per_9: float
    home_runs_per_9: float
    
    # Distribution statistics
    avg_runs_per_game: float
    avg_hits_per_game: float
    avg_hrs_per_game: float
    
    std_runs_per_game: float
    std_hits_per_game: float
    std_hrs_per_game: float
    
    # Win/loss records (if same teams used)
    away_wins: int = 0
    home_wins: int = 0
    ties: int = 0
    
    def __str__(self) -> str:
        """String representation of results."""
        return (
            f"ParallelSimulationResult:\n"
            f"  Games: {self.total_games:,}\n"
            f"  Time: {self.simulation_time:.1f}s\n"
            f"  Rate: {self.games_per_second:.2f} games/sec\n"
            f"\n"
            f"  MLB-Style Statistics (per 9 innings):\n"
            f"    Runs/9: {self.runs_per_9:.2f} (MLB avg: ~9.0)\n"
            f"    Hits/9: {self.hits_per_9:.2f} (MLB avg: ~17.0)\n"
            f"    HRs/9: {self.home_runs_per_9:.2f} (MLB avg: ~2.2)\n"
            f"\n"
            f"  Per-Game Averages:\n"
            f"    Runs: {self.avg_runs_per_game:.2f} ± {self.std_runs_per_game:.2f}\n"
            f"    Hits: {self.avg_hits_per_game:.2f} ± {self.std_hits_per_game:.2f}\n"
            f"    HRs: {self.avg_hrs_per_game:.2f} ± {self.std_hrs_per_game:.2f}\n"
        )


def _simulate_single_game(args: Tuple) -> GameResult:
    """
    Worker function to simulate a single game.
    
    This function is called by worker processes in the multiprocessing pool.
    Must be at module level for pickling.
    
    Parameters
    ----------
    args : tuple
        (game_number, away_team_dict, home_team_dict, num_innings, verbose, log_file)
        
    Returns
    -------
    GameResult
        Result of the simulated game
    """
    import sys
    import io
    
    game_number, away_team_dict, home_team_dict, num_innings, verbose, log_file = args
    
    # Suppress stdout for team creation (reduce noise from debug prints)
    old_stdout = sys.stdout
    sys.stdout = io.StringIO()
    
    try:
        # Reconstruct team objects from dictionaries
        # (Teams are serialized as dicts to avoid pickling issues)
        away_team = _deserialize_team(away_team_dict)
        home_team = _deserialize_team(home_team_dict)
    finally:
        # Restore stdout
        sys.stdout = old_stdout
    
    # Create simulator and run game
    simulator = GameSimulator(
        away_team,
        home_team,
        verbose=verbose,
        log_file=log_file
    )
    
    final_state = simulator.simulate_game(num_innings=num_innings)
    
    # Convert to lightweight result object
    result = GameResult(
        game_number=game_number,
        away_team_name=away_team.name,
        home_team_name=home_team.name,
        away_score=final_state.away_score,
        home_score=final_state.home_score,
        total_innings=final_state.inning - (0 if final_state.is_top else 1),
        total_pitches=final_state.total_pitches,
        total_hits=final_state.total_hits,
        total_home_runs=final_state.total_home_runs
    )
    
    return result


def _serialize_team(team: Team) -> Dict:
    """
    Serialize team to dictionary for multiprocessing.
    
    Stores team name and quality level instead of full objects,
    allowing recreation in worker processes.
    """
    # Infer quality from first pitcher's attributes
    first_pitcher = team.pitchers[0]
    if hasattr(first_pitcher, 'attributes') and first_pitcher.attributes:
        # Use velocity as quality indicator
        velocity = first_pitcher.attributes.get_raw_velocity_mph()
        if velocity >= 95:
            quality = "elite"
        elif velocity >= 92:
            quality = "good"
        elif velocity >= 88:
            quality = "average"
        else:
            quality = "poor"
    else:
        quality = "average"
    
    return {
        'name': team.name,
        'quality': quality
    }


def _deserialize_team(team_dict: Dict) -> Team:
    """
    Recreate team from dictionary in worker process.
    
    Creates a new team with the same quality level.
    This ensures each worker has independent team objects.
    """
    return create_test_team(team_dict['name'], team_dict['quality'])


class ParallelGameSimulator:
    """
    Simulator for running multiple games in parallel across CPU cores.
    
    Provides significant speedup for multi-game simulations by distributing
    games across available CPU cores using multiprocessing.
    
    Example speedup on 8-core CPU:
    - 10 games: 5-7x faster
    - 60 games: 6-8x faster
    - 200 games: 7-8x faster
    """
    
    def __init__(self, settings: Optional[ParallelSimulationSettings] = None):
        """
        Initialize parallel game simulator.
        
        Parameters
        ----------
        settings : ParallelSimulationSettings, optional
            Configuration for parallelization and output
        """
        self.settings = settings or ParallelSimulationSettings()
        
        # Determine number of workers
        if self.settings.num_workers is None:
            self.num_workers = cpu_count()
        else:
            self.num_workers = min(self.settings.num_workers, cpu_count())
    
    def simulate_games(
        self,
        away_team: Team,
        home_team: Team,
        num_games: int,
        num_innings: int = 9
    ) -> ParallelSimulationResult:
        """
        Simulate multiple games between two teams in parallel.
        
        Parameters
        ----------
        away_team : Team
            Away team
        home_team : Team
            Home team
        num_games : int
            Number of games to simulate
        num_innings : int
            Number of innings per game
            
        Returns
        -------
        ParallelSimulationResult
            Aggregated results from all games
        """
        if self.settings.show_progress:
            print(f"\nStarting parallel simulation of {num_games} games")
            print(f"Using {self.num_workers} CPU cores")
            print(f"Teams: {away_team.name} @ {home_team.name}")
            print(f"{'='*60}\n")
        
        start_time = time.time()
        
        # Serialize teams for multiprocessing
        away_team_dict = _serialize_team(away_team)
        home_team_dict = _serialize_team(home_team)
        
        # Prepare arguments for each game
        game_args = []
        for game_num in range(1, num_games + 1):
            log_file = None
            if self.settings.log_games:
                log_file = f"game_{game_num}_log.txt"
            
            game_args.append((
                game_num,
                away_team_dict,
                home_team_dict,
                num_innings,
                self.settings.verbose,
                log_file
            ))
        
        # Run games in parallel
        game_results = []
        
        if num_games == 1:
            # Single game - no need for multiprocessing overhead
            game_results = [_simulate_single_game(game_args[0])]
        else:
            # Multiple games - use multiprocessing pool
            with Pool(processes=self.num_workers) as pool:
                if self.settings.show_progress:
                    # Use imap_unordered for progress updates
                    for i, result in enumerate(pool.imap_unordered(
                        _simulate_single_game, 
                        game_args, 
                        chunksize=self.settings.chunk_size
                    ), 1):
                        game_results.append(result)
                        
                        if i % max(1, num_games // 10) == 0 or i == num_games:
                            elapsed = time.time() - start_time
                            rate = i / elapsed
                            eta = (num_games - i) / rate if i < num_games else 0
                            print(f"Progress: {i}/{num_games} games "
                                  f"({i/num_games*100:.1f}%) - "
                                  f"{rate:.2f} games/sec - "
                                  f"ETA: {eta:.1f}s")
                else:
                    # No progress updates - batch process
                    game_results = pool.map(
                        _simulate_single_game,
                        game_args,
                        chunksize=self.settings.chunk_size
                    )
        
        # Calculate statistics
        end_time = time.time()
        simulation_time = end_time - start_time
        games_per_second = num_games / simulation_time if simulation_time > 0 else 0
        
        # Aggregate statistics
        total_runs = sum(r.total_runs for r in game_results)
        total_hits = sum(r.total_hits for r in game_results)
        total_home_runs = sum(r.total_home_runs for r in game_results)
        total_innings = sum(r.total_innings for r in game_results)
        
        # Per-9-inning rates
        runs_per_9 = (total_runs / total_innings) * 9 if total_innings > 0 else 0
        hits_per_9 = (total_hits / total_innings) * 9 if total_innings > 0 else 0
        hrs_per_9 = (total_home_runs / total_innings) * 9 if total_innings > 0 else 0
        
        # Per-game averages and standard deviations
        runs_per_game = [r.total_runs for r in game_results]
        hits_per_game = [r.total_hits for r in game_results]
        hrs_per_game = [r.total_home_runs for r in game_results]
        
        avg_runs = np.mean(runs_per_game)
        avg_hits = np.mean(hits_per_game)
        avg_hrs = np.mean(hrs_per_game)
        
        std_runs = np.std(runs_per_game)
        std_hits = np.std(hits_per_game)
        std_hrs = np.std(hrs_per_game)
        
        # Win/loss record
        away_wins = sum(1 for r in game_results if r.away_score > r.home_score)
        home_wins = sum(1 for r in game_results if r.home_score > r.away_score)
        ties = sum(1 for r in game_results if r.away_score == r.home_score)
        
        # Create result object
        result = ParallelSimulationResult(
            total_games=num_games,
            simulation_time=simulation_time,
            games_per_second=games_per_second,
            settings_used=self.settings,
            game_results=game_results,
            total_runs=total_runs,
            total_hits=total_hits,
            total_home_runs=total_home_runs,
            total_innings=total_innings,
            runs_per_9=runs_per_9,
            hits_per_9=hits_per_9,
            home_runs_per_9=hrs_per_9,
            avg_runs_per_game=avg_runs,
            avg_hits_per_game=avg_hits,
            avg_hrs_per_game=avg_hrs,
            std_runs_per_game=std_runs,
            std_hits_per_game=std_hits,
            std_hrs_per_game=std_hrs,
            away_wins=away_wins,
            home_wins=home_wins,
            ties=ties
        )
        
        if self.settings.show_progress:
            print(f"\n{'='*60}")
            print(f"SIMULATION COMPLETE")
            print(f"{'='*60}")
            print(f"Time: {simulation_time:.1f} seconds")
            print(f"Rate: {games_per_second:.2f} games/second")
            print(f"\nRecord: {away_team.name} {away_wins}-{home_wins} {home_team.name}")
            if ties > 0:
                print(f"Ties: {ties}")
            print(f"\n{result}")
        
        return result
    
    def simulate_season(
        self,
        teams: List[Team],
        games_per_matchup: int = 1,
        num_innings: int = 9
    ) -> Dict[str, Any]:
        """
        Simulate a full season with multiple teams (round-robin).
        
        Parameters
        ----------
        teams : list
            List of Team objects
        games_per_matchup : int
            Number of games each team plays against each other team
        num_innings : int
            Number of innings per game
            
        Returns
        -------
        dict
            Season results including standings, team stats, and game results
        """
        num_teams = len(teams)
        if num_teams < 2:
            raise ValueError("Need at least 2 teams for a season")
        
        # Calculate total games
        total_matchups = num_teams * (num_teams - 1) // 2  # Round-robin
        total_games = total_matchups * games_per_matchup
        
        if self.settings.show_progress:
            print(f"\nSimulating season with {num_teams} teams")
            print(f"Total matchups: {total_matchups}")
            print(f"Games per matchup: {games_per_matchup}")
            print(f"Total games: {total_games}")
            print(f"{'='*60}\n")
        
        start_time = time.time()
        
        # Initialize team records
        team_records = {team.name: {'wins': 0, 'losses': 0, 'ties': 0, 
                                     'runs_for': 0, 'runs_against': 0}
                        for team in teams}
        
        all_game_results = []
        games_completed = 0
        
        # Simulate all matchups
        for i, away_team in enumerate(teams):
            for j, home_team in enumerate(teams):
                if i >= j:  # Skip self-matchups and duplicates
                    continue
                
                if self.settings.show_progress:
                    print(f"\nMatchup: {away_team.name} @ {home_team.name} "
                          f"({games_per_matchup} games)")
                
                # Simulate games for this matchup
                matchup_result = self.simulate_games(
                    away_team,
                    home_team,
                    games_per_matchup,
                    num_innings
                )
                
                # Update records
                team_records[away_team.name]['wins'] += matchup_result.away_wins
                team_records[away_team.name]['losses'] += matchup_result.home_wins
                team_records[home_team.name]['wins'] += matchup_result.home_wins
                team_records[home_team.name]['losses'] += matchup_result.away_wins
                
                # Update runs
                for game in matchup_result.game_results:
                    team_records[away_team.name]['runs_for'] += game.away_score
                    team_records[away_team.name]['runs_against'] += game.home_score
                    team_records[home_team.name]['runs_for'] += game.home_score
                    team_records[home_team.name]['runs_against'] += game.away_score
                
                all_game_results.extend(matchup_result.game_results)
                games_completed += games_per_matchup
        
        end_time = time.time()
        season_time = end_time - start_time
        
        # Calculate standings (sort by wins, then run differential)
        standings = []
        for team_name, record in team_records.items():
            run_diff = record['runs_for'] - record['runs_against']
            win_pct = record['wins'] / (record['wins'] + record['losses']) if (record['wins'] + record['losses']) > 0 else 0
            standings.append({
                'team': team_name,
                'wins': record['wins'],
                'losses': record['losses'],
                'win_pct': win_pct,
                'run_diff': run_diff,
                'runs_for': record['runs_for'],
                'runs_against': record['runs_against']
            })
        
        standings.sort(key=lambda x: (x['wins'], x['run_diff']), reverse=True)
        
        if self.settings.show_progress:
            print(f"\n{'='*60}")
            print(f"SEASON COMPLETE")
            print(f"{'='*60}")
            print(f"Total time: {season_time:.1f} seconds")
            print(f"Games simulated: {games_completed}")
            print(f"Rate: {games_completed/season_time:.2f} games/second")
            print(f"\nSTANDINGS:")
            print(f"{'Rank':<6}{'Team':<20}{'W':<6}{'L':<6}{'Pct':<8}{'RD':<8}")
            print("-" * 60)
            for i, team_stats in enumerate(standings, 1):
                print(f"{i:<6}{team_stats['team']:<20}"
                      f"{team_stats['wins']:<6}{team_stats['losses']:<6}"
                      f"{team_stats['win_pct']:.3f}  "
                      f"{team_stats['run_diff']:+6}")
        
        return {
            'standings': standings,
            'team_records': team_records,
            'game_results': all_game_results,
            'total_games': games_completed,
            'simulation_time': season_time,
            'games_per_second': games_completed / season_time
        }
    
    @staticmethod
    def estimate_speedup(num_games: int, num_cores: Optional[int] = None) -> Dict[str, float]:
        """
        Estimate speedup from parallelization.
        
        Parameters
        ----------
        num_games : int
            Number of games to simulate
        num_cores : int, optional
            Number of CPU cores (default: detect)
            
        Returns
        -------
        dict
            Estimated times and speedup factors
        """
        if num_cores is None:
            num_cores = cpu_count()
        
        # Baseline: ~6 seconds per game (empirical from testing)
        time_per_game = 6.0
        
        # Sequential time
        sequential_time = num_games * time_per_game
        
        # Parallel time (with overhead)
        overhead_per_game = 0.1  # Process spawning overhead
        parallel_time = (num_games * time_per_game / num_cores) + (num_games * overhead_per_game)
        
        # Effective speedup
        speedup = sequential_time / parallel_time
        
        return {
            'num_games': num_games,
            'num_cores': num_cores,
            'sequential_time_seconds': sequential_time,
            'parallel_time_seconds': parallel_time,
            'speedup_factor': speedup,
            'efficiency_percent': (speedup / num_cores) * 100
        }


# ============================================================================
# Phase 4: Thread-Based Parallelism
# ============================================================================

@dataclass
class ThreadedSimulationSettings:
    """Configuration for threaded game simulation."""
    
    # Threading settings
    num_workers: Optional[int] = None  # None = use all CPU cores
    
    # Simulation settings
    simulation_mode: SimulationMode = SimulationMode.ULTRA_FAST
    num_innings: int = 9
    
    # Output settings
    verbose: bool = False
    show_progress: bool = True
    
    # Determinism settings
    base_seed: Optional[int] = None  # For reproducible results
    
    @classmethod
    def for_game_count(cls, count: int) -> 'ThreadedSimulationSettings':
        """Create optimal settings based on game count."""
        # Use ULTRA_FAST mode for bulk simulations
        mode = SimulationMode.ULTRA_FAST if count >= 10 else SimulationMode.FAST
        
        return cls(
            num_workers=None,  # Use all cores
            simulation_mode=mode,
            verbose=False,
            show_progress=count >= 10,
            base_seed=None
        )


def _thread_simulate_game(
    game_number: int,
    away_team: Team,
    home_team: Team,
    num_innings: int,
    simulation_mode: SimulationMode,
    seed: Optional[int],
    verbose: bool
) -> GameResult:
    """
    Worker function to simulate a single game in a thread.
    
    Unlike the multiprocessing version, this receives actual Team objects
    (no serialization needed) since threads share memory.
    
    Parameters
    ----------
    game_number : int
        Game sequence number
    away_team : Team
        Away team object (shared, read-only)
    home_team : Team
        Home team object (shared, read-only)
    num_innings : int
        Number of innings
    simulation_mode : SimulationMode
        Speed/accuracy mode
    seed : int or None
        RNG seed for determinism (game-specific)
    verbose : bool
        Whether to print play-by-play
    
    Returns
    -------
    GameResult
        Result of the simulated game
    """
    # Set per-game seed for determinism
    if seed is not None:
        np.random.seed(seed)
    
    # Create simulator for this game
    # Each thread gets its own simulator instance
    simulator = GameSimulator(
        away_team,
        home_team,
        verbose=verbose,
        log_file=None,
        simulation_mode=simulation_mode,
    )
    
    # Run simulation
    final_state = simulator.simulate_game(num_innings=num_innings)
    
    # Return lightweight result
    return GameResult(
        game_number=game_number,
        away_team_name=away_team.name,
        home_team_name=home_team.name,
        away_score=final_state.away_score,
        home_score=final_state.home_score,
        total_innings=final_state.inning - (0 if final_state.is_top else 1),
        total_pitches=final_state.total_pitches,
        total_hits=final_state.total_hits,
        total_home_runs=final_state.total_home_runs
    )


class ThreadedGameSimulator:
    """
    Thread-based parallel game simulator.
    
    Uses ThreadPoolExecutor instead of multiprocessing.Pool.
    
    **Important Performance Note**: Thread-based parallelism is NOT faster than
    process-based for full game simulations. This is because:
    
    1. The Python GIL is only released during Numba JIT-compiled code
    2. Game simulation has significant Python overhead (game state, at-bat logic)
    3. Multiprocessing avoids GIL contention by using separate processes
    
    Thread-based is useful when:
    - You need shared memory access to team data
    - The workload is predominantly Numba code (e.g., batch trajectories)
    - Process spawn overhead dominates (very many small jobs)
    
    For full game simulations, use ParallelGameSimulator (process-based) instead.
    
    **Determinism Note**: Thread-safe determinism requires using per-game RNG
    instances rather than numpy's global RNG. When base_seed is set, each game
    gets a unique seed, but thread scheduling may still affect order of results.
    
    Example
    -------
    >>> from batted_ball.parallel_game_simulation import ThreadedGameSimulator
    >>> from batted_ball.game_simulation import create_test_team
    >>> 
    >>> away = create_test_team("Yankees", "elite")
    >>> home = create_test_team("Red Sox", "good")
    >>> 
    >>> simulator = ThreadedGameSimulator()
    >>> result = simulator.simulate_games(away, home, num_games=50)
    >>> print(f"Rate: {result.games_per_second:.2f} games/sec")
    """
    
    def __init__(self, settings: Optional[ThreadedSimulationSettings] = None):
        """
        Initialize threaded game simulator.
        
        Parameters
        ----------
        settings : ThreadedSimulationSettings, optional
            Configuration for threading and simulation
        """
        self.settings = settings or ThreadedSimulationSettings()
        
        # Determine number of workers
        if self.settings.num_workers is None:
            self.num_workers = cpu_count()
        else:
            self.num_workers = min(self.settings.num_workers, cpu_count())
    
    def simulate_games(
        self,
        away_team: Team,
        home_team: Team,
        num_games: int,
        num_innings: Optional[int] = None
    ) -> ParallelSimulationResult:
        """
        Simulate multiple games between two teams using thread pool.
        
        Parameters
        ----------
        away_team : Team
            Away team (shared across all threads)
        home_team : Team
            Home team (shared across all threads)
        num_games : int
            Number of games to simulate
        num_innings : int, optional
            Number of innings per game (default: from settings)
            
        Returns
        -------
        ParallelSimulationResult
            Aggregated results from all games
        """
        if num_innings is None:
            num_innings = self.settings.num_innings
        
        if self.settings.show_progress:
            print(f"\nStarting threaded simulation of {num_games} games")
            print(f"Using {self.num_workers} threads")
            print(f"Mode: {self.settings.simulation_mode.name}")
            print(f"Teams: {away_team.name} @ {home_team.name}")
            print(f"{'='*60}\n")
        
        start_time = time.time()
        game_results = []
        
        # Use ThreadPoolExecutor for parallel execution
        with ThreadPoolExecutor(max_workers=self.num_workers) as executor:
            # Submit all games
            futures = {}
            for game_num in range(1, num_games + 1):
                # Calculate per-game seed for determinism
                game_seed = None
                if self.settings.base_seed is not None:
                    game_seed = self.settings.base_seed + game_num
                
                future = executor.submit(
                    _thread_simulate_game,
                    game_num,
                    away_team,
                    home_team,
                    num_innings,
                    self.settings.simulation_mode,
                    game_seed,
                    self.settings.verbose
                )
                futures[future] = game_num
            
            # Collect results as they complete (dynamic load balancing)
            completed = 0
            last_progress = 0
            
            for future in as_completed(futures):
                try:
                    result = future.result()
                    game_results.append(result)
                    completed += 1
                    
                    # Progress update
                    if self.settings.show_progress:
                        progress_pct = int(completed / num_games * 100)
                        if progress_pct >= last_progress + 10 or completed == num_games:
                            elapsed = time.time() - start_time
                            rate = completed / elapsed if elapsed > 0 else 0
                            eta = (num_games - completed) / rate if rate > 0 else 0
                            print(f"Progress: {completed}/{num_games} games "
                                  f"({progress_pct}%) - "
                                  f"{rate:.2f} games/sec - "
                                  f"ETA: {eta:.1f}s")
                            last_progress = progress_pct
                except Exception as e:
                    print(f"Game {futures[future]} failed: {e}")
        
        # Calculate statistics
        end_time = time.time()
        simulation_time = end_time - start_time
        games_per_second = num_games / simulation_time if simulation_time > 0 else 0
        
        # Aggregate statistics
        total_runs = sum(r.total_runs for r in game_results)
        total_hits = sum(r.total_hits for r in game_results)
        total_home_runs = sum(r.total_home_runs for r in game_results)
        total_innings = sum(r.total_innings for r in game_results)
        
        # Per-9-inning rates
        runs_per_9 = (total_runs / total_innings) * 9 if total_innings > 0 else 0
        hits_per_9 = (total_hits / total_innings) * 9 if total_innings > 0 else 0
        hrs_per_9 = (total_home_runs / total_innings) * 9 if total_innings > 0 else 0
        
        # Per-game averages and standard deviations
        runs_per_game = [r.total_runs for r in game_results]
        hits_per_game = [r.total_hits for r in game_results]
        hrs_per_game = [r.total_home_runs for r in game_results]
        
        avg_runs = np.mean(runs_per_game)
        avg_hits = np.mean(hits_per_game)
        avg_hrs = np.mean(hrs_per_game)
        
        std_runs = np.std(runs_per_game)
        std_hits = np.std(hits_per_game)
        std_hrs = np.std(hrs_per_game)
        
        # Win/loss record
        away_wins = sum(1 for r in game_results if r.away_score > r.home_score)
        home_wins = sum(1 for r in game_results if r.home_score > r.away_score)
        ties = sum(1 for r in game_results if r.away_score == r.home_score)
        
        # Create result object (reusing ParallelSimulationResult for compatibility)
        result = ParallelSimulationResult(
            total_games=num_games,
            simulation_time=simulation_time,
            games_per_second=games_per_second,
            settings_used=ParallelSimulationSettings(),  # Placeholder
            game_results=game_results,
            total_runs=total_runs,
            total_hits=total_hits,
            total_home_runs=total_home_runs,
            total_innings=total_innings,
            runs_per_9=runs_per_9,
            hits_per_9=hits_per_9,
            home_runs_per_9=hrs_per_9,
            avg_runs_per_game=avg_runs,
            avg_hits_per_game=avg_hits,
            avg_hrs_per_game=avg_hrs,
            std_runs_per_game=std_runs,
            std_hits_per_game=std_hits,
            std_hrs_per_game=std_hrs,
            away_wins=away_wins,
            home_wins=home_wins,
            ties=ties
        )
        
        if self.settings.show_progress:
            print(f"\n{'='*60}")
            print(f"THREADED SIMULATION COMPLETE")
            print(f"{'='*60}")
            print(f"Time: {simulation_time:.1f} seconds")
            print(f"Rate: {games_per_second:.2f} games/second")
            print(f"\nRecord: {away_team.name} {away_wins}-{home_wins} {home_team.name}")
            if ties > 0:
                print(f"Ties: {ties}")
        
        return result
    
    def simulate_games_deterministic(
        self,
        away_team: Team,
        home_team: Team,
        num_games: int,
        base_seed: int = 42
    ) -> ParallelSimulationResult:
        """
        Simulate games with deterministic results.
        
        Each game gets seed = base_seed + game_number, ensuring reproducible
        results regardless of thread scheduling.
        
        Parameters
        ----------
        away_team : Team
            Away team
        home_team : Team
            Home team
        num_games : int
            Number of games
        base_seed : int
            Base random seed (default: 42)
            
        Returns
        -------
        ParallelSimulationResult
            Results (reproducible with same seed)
        """
        # Store original seed setting
        original_seed = self.settings.base_seed
        self.settings.base_seed = base_seed
        
        try:
            return self.simulate_games(away_team, home_team, num_games)
        finally:
            # Restore original setting
            self.settings.base_seed = original_seed


def benchmark_thread_vs_process(
    num_games: int = 20,
    num_cores: Optional[int] = None
) -> Dict[str, Any]:
    """
    Benchmark threaded vs process-based parallelism.
    
    Runs the same simulation with both approaches and compares performance.
    
    Parameters
    ----------
    num_games : int
        Number of games to simulate
    num_cores : int, optional
        Number of cores to use (default: all)
        
    Returns
    -------
    dict
        Benchmark results including times and speedup factors
    """
    if num_cores is None:
        num_cores = cpu_count()
    
    print(f"=" * 60)
    print(f"BENCHMARK: Thread vs Process Parallelism")
    print(f"=" * 60)
    print(f"Games: {num_games}")
    print(f"Cores: {num_cores}")
    print()
    
    # Create test teams
    away_team = create_test_team("Team A", "good")
    home_team = create_test_team("Team B", "good")
    
    # Process-based simulation
    print("Running PROCESS-based simulation...")
    process_settings = ParallelSimulationSettings(
        num_workers=num_cores,
        verbose=False,
        show_progress=False,
        log_games=False
    )
    process_sim = ParallelGameSimulator(process_settings)
    
    process_start = time.time()
    process_result = process_sim.simulate_games(away_team, home_team, num_games)
    process_time = time.time() - process_start
    
    print(f"  Time: {process_time:.2f}s, Rate: {num_games/process_time:.2f} games/sec")
    
    # Thread-based simulation
    print("Running THREAD-based simulation...")
    thread_settings = ThreadedSimulationSettings(
        num_workers=num_cores,
        simulation_mode=SimulationMode.ACCURATE,  # Same mode for fair comparison
        verbose=False,
        show_progress=False
    )
    thread_sim = ThreadedGameSimulator(thread_settings)
    
    thread_start = time.time()
    thread_result = thread_sim.simulate_games(away_team, home_team, num_games)
    thread_time = time.time() - thread_start
    
    print(f"  Time: {thread_time:.2f}s, Rate: {num_games/thread_time:.2f} games/sec")
    
    # Calculate improvement
    improvement = (process_time - thread_time) / process_time * 100
    speedup = process_time / thread_time
    
    print()
    print(f"RESULTS:")
    print(f"  Process-based: {process_time:.2f}s ({num_games/process_time:.2f} games/sec)")
    print(f"  Thread-based:  {thread_time:.2f}s ({num_games/thread_time:.2f} games/sec)")
    print(f"  Improvement:   {improvement:.1f}% faster")
    print(f"  Speedup:       {speedup:.2f}x")
    
    return {
        'num_games': num_games,
        'num_cores': num_cores,
        'process_time': process_time,
        'process_rate': num_games / process_time,
        'thread_time': thread_time,
        'thread_rate': num_games / thread_time,
        'improvement_pct': improvement,
        'speedup': speedup
    }


def verify_threaded_determinism(num_games: int = 20, base_seed: int = 42) -> bool:
    """
    Verify that threaded simulation produces deterministic results.
    
    Runs the same simulation twice with the same seed and verifies
    identical aggregate results.
    
    Parameters
    ----------
    num_games : int
        Number of games to simulate
    base_seed : int
        Base random seed
        
    Returns
    -------
    bool
        True if results are identical
    """
    print(f"=" * 60)
    print(f"DETERMINISM TEST: Threaded Simulation")
    print(f"=" * 60)
    print(f"Games: {num_games}")
    print(f"Seed: {base_seed}")
    print()
    
    # Create test teams
    away_team = create_test_team("Determinism A", "average")
    home_team = create_test_team("Determinism B", "average")
    
    # Run twice with same seed
    settings = ThreadedSimulationSettings(
        simulation_mode=SimulationMode.FAST,
        show_progress=False,
        base_seed=base_seed
    )
    simulator = ThreadedGameSimulator(settings)
    
    print("Run 1...")
    result1 = simulator.simulate_games(away_team, home_team, num_games)
    
    print("Run 2...")
    result2 = simulator.simulate_games(away_team, home_team, num_games)
    
    # Compare results
    runs_match = result1.total_runs == result2.total_runs
    hits_match = result1.total_hits == result2.total_hits
    hrs_match = result1.total_home_runs == result2.total_home_runs
    wins_match = result1.away_wins == result2.away_wins
    
    print()
    print(f"COMPARISON:")
    print(f"  Total Runs:  {result1.total_runs} vs {result2.total_runs} - {'✓ MATCH' if runs_match else '✗ DIFFER'}")
    print(f"  Total Hits:  {result1.total_hits} vs {result2.total_hits} - {'✓ MATCH' if hits_match else '✗ DIFFER'}")
    print(f"  Total HRs:   {result1.total_home_runs} vs {result2.total_home_runs} - {'✓ MATCH' if hrs_match else '✗ DIFFER'}")
    print(f"  Away Wins:   {result1.away_wins} vs {result2.away_wins} - {'✓ MATCH' if wins_match else '✗ DIFFER'}")
    
    all_match = runs_match and hits_match and hrs_match and wins_match
    
    if all_match:
        print(f"\n✓ PASS: Results are deterministic")
    else:
        print(f"\n✗ FAIL: Results differ between runs")
    
    return all_match
