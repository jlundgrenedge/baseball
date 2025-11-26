"""
Test parallel game simulation to demonstrate speedup.

Runs multiple games in parallel and compares performance to sequential execution.
"""
import sys
import time
sys.path.append('.')

from batted_ball import create_test_team, GameSimulator
from batted_ball.parallel_game_simulation import (
    ParallelGameSimulator,
    ParallelSimulationSettings
)


def test_sequential_games(num_games: int):
    """Run games sequentially (old method)."""
    print(f"\n{'='*70}")
    print(f"SEQUENTIAL SIMULATION: {num_games} games")
    print(f"{'='*70}")
    
    start_time = time.time()
    
    results = []
    for i in range(1, num_games + 1):
        # Create fresh teams for each game
        away = create_test_team(f"Away{i}", "average")
        home = create_test_team(f"Home{i}", "average")
        
        # Run game (no output)
        sim = GameSimulator(away, home, verbose=False)
        final_state = sim.simulate_game(num_innings=9)
        
        results.append({
            'game': i,
            'runs': final_state.away_score + final_state.home_score,
            'hits': final_state.total_hits,
            'hrs': final_state.total_home_runs
        })
        
        # Progress update
        if i % max(1, num_games // 5) == 0:
            elapsed = time.time() - start_time
            rate = i / elapsed
            eta = (num_games - i) / rate if i < num_games else 0
            print(f"  Progress: {i}/{num_games} ({i/num_games*100:.0f}%) - "
                  f"{rate:.2f} games/sec - ETA: {eta:.1f}s")
    
    end_time = time.time()
    total_time = end_time - start_time
    games_per_sec = num_games / total_time
    
    # Calculate stats
    total_runs = sum(r['runs'] for r in results)
    total_hits = sum(r['hits'] for r in results)
    total_hrs = sum(r['hrs'] for r in results)
    
    print(f"\nSequential Results:")
    print(f"  Time: {total_time:.1f} seconds")
    print(f"  Rate: {games_per_sec:.2f} games/second")
    print(f"  Total Runs: {total_runs} ({total_runs/num_games:.1f} per game)")
    print(f"  Total Hits: {total_hits} ({total_hits/num_games:.1f} per game)")
    print(f"  Total HRs: {total_hrs} ({total_hrs/num_games:.2f} per game)")
    
    return total_time, games_per_sec


def test_parallel_games(num_games: int):
    """Run games in parallel (new method)."""
    print(f"\n{'='*70}")
    print(f"PARALLEL SIMULATION: {num_games} games")
    print(f"{'='*70}")
    
    # Create teams
    away = create_test_team("Away", "average")
    home = create_test_team("Home", "average")
    
    # Configure parallel simulator
    settings = ParallelSimulationSettings.for_game_count(num_games)
    parallel_sim = ParallelGameSimulator(settings)
    
    # Run parallel simulation
    result = parallel_sim.simulate_games(away, home, num_games, num_innings=9)
    
    print(f"\nParallel Results:")
    print(f"  Time: {result.simulation_time:.1f} seconds")
    print(f"  Rate: {result.games_per_second:.2f} games/second")
    print(f"  Total Runs: {result.total_runs} ({result.avg_runs_per_game:.1f} per game)")
    print(f"  Total Hits: {result.total_hits} ({result.avg_hits_per_game:.1f} per game)")
    print(f"  Total HRs: {result.total_home_runs} ({result.avg_hrs_per_game:.2f} per game)")
    
    return result.simulation_time, result.games_per_second


def main():
    """Run comparison test."""
    # Test with different game counts
    test_sizes = [10, 20, 60]
    
    print("\n" + "="*70)
    print("PARALLEL GAME SIMULATION PERFORMANCE TEST")
    print("="*70)
    print("\nThis test compares sequential vs parallel game simulation.")
    print("Expected speedup: 5-8x on multi-core systems")
    
    for num_games in test_sizes:
        print(f"\n{'#'*70}")
        print(f"# TEST: {num_games} Games")
        print(f"{'#'*70}")
        
        # Run sequential
        seq_time, seq_rate = test_sequential_games(num_games)
        
        # Run parallel
        par_time, par_rate = test_parallel_games(num_games)
        
        # Calculate speedup
        speedup = seq_time / par_time if par_time > 0 else 0
        
        print(f"\n{'='*70}")
        print(f"COMPARISON FOR {num_games} GAMES")
        print(f"{'='*70}")
        print(f"Sequential: {seq_time:.1f}s ({seq_rate:.2f} games/sec)")
        print(f"Parallel:   {par_time:.1f}s ({par_rate:.2f} games/sec)")
        print(f"Speedup:    {speedup:.2f}x faster")
        print(f"Time saved: {seq_time - par_time:.1f} seconds ({(1-par_time/seq_time)*100:.1f}%)")
    
    print(f"\n{'='*70}")
    print("TEST COMPLETE")
    print(f"{'='*70}")
    print("\nConclusion:")
    print("  - Parallel simulation provides significant speedup for multi-game analysis")
    print("  - Larger sample sizes benefit more from parallelization")
    print("  - Use ParallelGameSimulator for any simulation with 10+ games")


if __name__ == "__main__":
    main()
