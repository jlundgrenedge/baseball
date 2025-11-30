"""
Parallel randomized team simulation for high-volume testing.

Uses multiprocessing to simulate multiple games concurrently,
providing 4-8x speedup on multi-core systems.

Each game uses:
- Random away team
- Random home team (different from away)
- Random starting pitcher from each team's rotation
- Home team's ballpark

This provides unbiased testing across the full range of 
player attributes in the database at high speed.
"""

import sys
import random
import time
from pathlib import Path
from datetime import datetime
from typing import List, Tuple, Dict, Any, Optional
from dataclasses import dataclass, field
import sqlite3
from multiprocessing import Pool, cpu_count
from concurrent.futures import ProcessPoolExecutor, as_completed

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from batted_ball.database.team_loader import TeamLoader
from batted_ball.game_simulation import GameSimulator
from batted_ball.series_metrics import SeriesMetrics
from batted_ball.constants import SimulationMode


# Map team abbreviations to their home ballpark
TEAM_BALLPARKS = {
    'CHC': 'wrigley',
    'CIN': 'great_american',
    'NYY': 'yankee',
    'BOS': 'fenway',
    'LAD': 'dodger',
    'SF': 'oracle',
    'SFG': 'oracle',
    'COL': 'coors',
    'HOU': 'minute_maid',
    'SD': 'petco',
    'SDP': 'petco',
}


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
    home_ground_balls: int = 0
    home_line_drives: int = 0
    home_fly_balls: int = 0
    home_exit_velocities: List[float] = field(default_factory=list)
    home_launch_angles: List[float] = field(default_factory=list)


def get_all_teams() -> List[Tuple[str, str, int]]:
    """Get all teams from the database."""
    conn = sqlite3.connect('baseball_teams.db')
    cursor = conn.cursor()
    cursor.execute("SELECT team_name, team_abbr, season FROM teams")
    teams = cursor.fetchall()
    conn.close()
    return teams


def get_team_ballpark(team_abbr: str) -> str:
    """Get the home ballpark for a team."""
    return TEAM_BALLPARKS.get(team_abbr.upper(), 'generic')


def _simulate_single_game_worker(args: Tuple) -> ParallelGameResult:
    """
    Worker function for parallel game simulation.
    
    Runs in a separate process, so needs to reload teams from database.
    
    Parameters
    ----------
    args : tuple
        (game_number, away_team_info, home_team_info, simulation_mode)
    
    Returns
    -------
    ParallelGameResult
        Complete game statistics
    """
    game_number, away_team_info, home_team_info, use_ultra_fast = args
    away_name, away_abbr, away_season = away_team_info
    home_name, home_abbr, home_season = home_team_info
    
    # Load teams in this process
    loader = TeamLoader()
    away_team = loader.load_team(away_name, away_season)
    home_team = loader.load_team(home_name, home_season)
    loader.close()
    
    if not away_team or not home_team:
        # Return empty result on failure
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
    
    # Pick random starting pitchers
    away_starters = away_team.get_starters()
    home_starters = home_team.get_starters()
    
    if away_starters:
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
    ballpark = get_team_ballpark(home_abbr)
    
    # Set simulation mode
    mode = SimulationMode.ULTRA_FAST if use_ultra_fast else SimulationMode.FAST
    
    # Create simulator (no verbose output in parallel mode)
    sim = GameSimulator(
        away_team,
        home_team,
        verbose=False,
        debug_metrics=0,
        ballpark=ballpark,
        wind_enabled=True,
        starter_innings=5,
        simulation_mode=mode
    )
    
    # Simulate game
    final_state = sim.simulate_game(num_innings=9)
    
    # Package result
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
        home_ground_balls=final_state.home_ground_balls,
        home_line_drives=final_state.home_line_drives,
        home_fly_balls=final_state.home_fly_balls,
        home_exit_velocities=list(final_state.home_exit_velocities),
        home_launch_angles=list(final_state.home_launch_angles),
    )


class MockGameState:
    """
    Lightweight game state to feed into SeriesMetrics.update_from_game().
    
    Reconstructed from ParallelGameResult.
    """
    def __init__(self, result: ParallelGameResult):
        self.away_score = result.away_score
        self.home_score = result.home_score
        
        # Away batting
        self.away_at_bats = result.away_at_bats
        self.away_hits = result.away_hits
        self.away_singles = result.away_singles
        self.away_doubles = result.away_doubles
        self.away_triples = result.away_triples
        self.away_home_runs = result.away_home_runs
        self.away_walks = result.away_walks
        self.away_strikeouts = result.away_strikeouts
        self.away_ground_balls = result.away_ground_balls
        self.away_line_drives = result.away_line_drives
        self.away_fly_balls = result.away_fly_balls
        self.away_exit_velocities = result.away_exit_velocities
        self.away_launch_angles = result.away_launch_angles
        
        # Home batting
        self.home_at_bats = result.home_at_bats
        self.home_hits = result.home_hits
        self.home_singles = result.home_singles
        self.home_doubles = result.home_doubles
        self.home_triples = result.home_triples
        self.home_home_runs = result.home_home_runs
        self.home_walks = result.home_walks
        self.home_strikeouts = result.home_strikeouts
        self.home_ground_balls = result.home_ground_balls
        self.home_line_drives = result.home_line_drives
        self.home_fly_balls = result.home_fly_balls
        self.home_exit_velocities = result.home_exit_velocities
        self.home_launch_angles = result.home_launch_angles
        
        # Fielding (not tracked in parallel mode)
        self.away_errors = 0
        self.home_errors = 0
        
        # Pitching (not fully tracked)
        self.total_pitches = 0


def simulate_parallel_random_games(
    num_games: int,
    num_workers: Optional[int] = None,
    use_ultra_fast: bool = True
):
    """
    Simulate games with random team matchups using parallel processing.
    
    Parameters
    ----------
    num_games : int
        Number of games to simulate
    num_workers : int, optional
        Number of parallel workers (default: CPU count)
    use_ultra_fast : bool
        Use ULTRA_FAST simulation mode (5x faster trajectories)
    """
    # Get all available teams
    all_teams = get_all_teams()
    
    if len(all_teams) < 2:
        print("❌ Need at least 2 teams in database!")
        return
    
    # Determine worker count
    if num_workers is None:
        num_workers = min(cpu_count(), num_games)
    num_workers = max(1, min(num_workers, num_games))
    
    print(f"\n{'='*70}")
    print(f"  PARALLEL RANDOMIZED SIMULATION")
    print(f"{'='*70}")
    print(f"\n📊 Found {len(all_teams)} teams in database")
    print(f"🎲 Simulating {num_games} games with random matchups")
    print(f"⚡ Using {num_workers} parallel workers")
    print(f"🚀 Mode: {'ULTRA_FAST' if use_ultra_fast else 'FAST'}")
    print()
    
    # Create log file
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    log_filename = f"game_log_PARALLEL_{num_games}_games_{timestamp}.txt"
    log_path = Path("game_logs") / log_filename
    log_path.parent.mkdir(exist_ok=True)
    
    print(f"📝 Game log: {log_path}\n")
    
    # Generate random matchups
    matchups = []
    for game_num in range(1, num_games + 1):
        away_team_info, home_team_info = random.sample(all_teams, 2)
        matchups.append((game_num, away_team_info, home_team_info, use_ultra_fast))
    
    # Initialize metrics
    series_metrics = SeriesMetrics(
        away_team_name="Various (Away)",
        home_team_name="Various (Home)"
    )
    
    # Track results
    results: List[ParallelGameResult] = []
    
    # Run parallel simulation
    start_time = time.time()
    completed = 0
    
    print(f"Starting parallel simulation...")
    print(f"[{'.' * 50}]", end='\r')
    
    with ProcessPoolExecutor(max_workers=num_workers) as executor:
        # Submit all games
        futures = {executor.submit(_simulate_single_game_worker, m): m[0] for m in matchups}
        
        # Collect results
        for future in as_completed(futures):
            try:
                result = future.result()
                results.append(result)
                completed += 1
                
                # Progress bar
                progress = int(completed / num_games * 50)
                print(f"[{'#' * progress}{'.' * (50 - progress)}] {completed}/{num_games}", end='\r')
                
            except Exception as e:
                print(f"\n⚠️ Game failed: {e}")
    
    elapsed = time.time() - start_time
    games_per_second = num_games / elapsed if elapsed > 0 else 0
    
    print(f"\n\n✅ Completed {num_games} games in {elapsed:.1f} seconds")
    print(f"⚡ Rate: {games_per_second:.2f} games/second")
    
    # Sort results by game number
    results.sort(key=lambda r: r.game_number)
    
    # Update series metrics from results
    for result in results:
        mock_state = MockGameState(result)
        series_metrics.update_from_game(mock_state)
    
    # Write log file
    with open(log_path, 'w', encoding='utf-8') as log_file:
        log_file.write(f"{'='*80}\n")
        log_file.write(f"PARALLEL RANDOMIZED GAME SERIES LOG\n")
        log_file.write(f"{'='*80}\n")
        log_file.write(f"Total Games: {num_games}\n")
        log_file.write(f"Teams in Pool: {len(all_teams)}\n")
        log_file.write(f"Workers Used: {num_workers}\n")
        log_file.write(f"Simulation Mode: {'ULTRA_FAST' if use_ultra_fast else 'FAST'}\n")
        log_file.write(f"Total Time: {elapsed:.1f} seconds\n")
        log_file.write(f"Rate: {games_per_second:.2f} games/second\n")
        log_file.write(f"Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        log_file.write(f"{'='*80}\n\n")
        
        # Write matchup history
        log_file.write("MATCHUP RESULTS\n")
        log_file.write("-" * 80 + "\n")
        for r in results:
            winner = r.away_team_name if r.away_score > r.home_score else r.home_team_name
            log_file.write(
                f"Game {r.game_number}: {r.away_team_name} {r.away_score} @ "
                f"{r.home_team_name} {r.home_score} ({winner} wins)\n"
            )
        
        # Capture summary
        import io
        old_stdout = sys.stdout
        summary_output = io.StringIO()
        sys.stdout = summary_output
        try:
            series_metrics.print_summary()
        finally:
            sys.stdout = old_stdout
        
        log_file.write("\n\n")
        log_file.write(summary_output.getvalue())
    
    # Print summary to console
    print("\n" + "=" * 70)
    print("  PARALLEL SERIES COMPLETE")
    print("=" * 70)
    series_metrics.print_summary()
    
    print(f"\n✅ Complete game log saved to: {log_path}")
    print(f"   File size: {log_path.stat().st_size / 1024:.1f} KB")
    
    # Show speedup estimate
    sequential_estimate = num_games * 6  # ~6 seconds per game sequential
    speedup = sequential_estimate / elapsed if elapsed > 0 else 1
    print(f"\n⚡ Estimated speedup: {speedup:.1f}x vs sequential")


def main():
    """Main entry point with interactive prompts."""
    # Check for command-line arguments
    if len(sys.argv) > 1:
        try:
            num_games = int(sys.argv[1])
            num_workers = int(sys.argv[2]) if len(sys.argv) > 2 else None
            if 1 <= num_games <= 1000:
                print(f"\n🎲 Running {num_games} parallel randomized games...")
                simulate_parallel_random_games(num_games, num_workers)
                return
        except ValueError:
            pass
    
    print("\n" + "=" * 70)
    print("  PARALLEL RANDOMIZED TEAM SIMULATION")
    print("=" * 70)
    print("\nThis mode randomly selects teams for each game and runs")
    print("simulations in parallel for 4-8x speedup on multi-core systems.\n")
    
    # Check database exists
    if not Path("baseball_teams.db").exists():
        print("❌ Database not found! Run option 5 first to add teams.")
        return
    
    # Show CPU info
    cores = cpu_count()
    print(f"💻 Detected {cores} CPU cores")
    
    # Get number of games
    while True:
        try:
            choice = input("\nNumber of games to simulate (1-1000, 0 to cancel): ").strip()
            if choice == '0':
                print("Cancelled.")
                return
            num_games = int(choice)
            if 1 <= num_games <= 1000:
                break
            print("Please enter 1-1000.")
        except ValueError:
            print("Invalid input.")
    
    # Get number of workers
    default_workers = min(cores, num_games)
    while True:
        try:
            choice = input(f"Number of parallel workers (1-{cores}, Enter for {default_workers}): ").strip()
            if choice == '':
                num_workers = default_workers
                break
            num_workers = int(choice)
            if 1 <= num_workers <= cores:
                break
            print(f"Please enter 1-{cores}.")
        except ValueError:
            print("Invalid input.")
    
    # Confirm
    print(f"\nWill simulate {num_games} games using {num_workers} parallel workers.")
    print(f"Estimated time: {num_games * 6 / num_workers / 60:.1f} minutes")
    confirm = input("Proceed? (y/n): ").strip().lower()
    if confirm != 'y':
        print("Cancelled.")
        return
    
    # Run simulation
    simulate_parallel_random_games(num_games, num_workers)
    
    input("\nPress Enter to continue...")


if __name__ == "__main__":
    main()
