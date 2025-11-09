"""
Quick test of parallel vs sequential - 10 games only for fast comparison.
"""
import sys
import time
sys.path.append('.')

from batted_ball import create_test_team, GameSimulator
from batted_ball.parallel_game_simulation import ParallelGameSimulator


print("="*70)
print("QUICK PARALLEL TEST: 10 Games")
print("="*70)

# Create teams once
away = create_test_team("Away", "average")
home = create_test_team("Home", "average")

print("\n1. Sequential (baseline)...")
start = time.time()
seq_results = []
for i in range(10):
    # Reuse same teams (faster)
    away.current_batter_index = 0
    home.current_batter_index = 0
    sim = GameSimulator(away, home, verbose=False)
    final = sim.simulate_game(num_innings=9)
    seq_results.append(final.away_score + final.home_score)
seq_time = time.time() - start
print(f"   Time: {seq_time:.1f}s ({10/seq_time:.2f} games/sec)")
print(f"   Avg runs/game: {sum(seq_results)/10:.1f}")

print("\n2. Parallel (using all cores)...")
parallel_sim = ParallelGameSimulator()
start = time.time()
result = parallel_sim.simulate_games(away, home, num_games=10, num_innings=9)
par_time = result.simulation_time
print(f"   Time: {par_time:.1f}s ({result.games_per_second:.2f} games/sec)")
print(f"   Avg runs/game: {result.avg_runs_per_game:.1f}")

print(f"\nSpeedup: {seq_time/par_time:.2f}x faster")
print(f"Time saved: {seq_time-par_time:.1f}s")
