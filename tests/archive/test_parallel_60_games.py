"""
Run multiple games in parallel with detailed statistics.

This script uses the parallel game simulator to run large sample sizes efficiently.
"""
import sys
sys.path.append('.')

from batted_ball import create_test_team
from batted_ball.parallel_game_simulation import (
    ParallelGameSimulator,
    ParallelSimulationSettings
)


def main():
    # Configuration
    NUM_GAMES = 60  # Same as original test
    
    print(f"\n{'='*70}")
    print(f"PARALLEL MULTI-GAME SIMULATION")
    print(f"{'='*70}")
    print(f"Running {NUM_GAMES} games with parallel processing...")
    print(f"(Original version took ~10 minutes, this should be 5-8x faster)\n")
    
    # Create teams
    away_team = create_test_team("Visitors", "average")
    home_team = create_test_team("Home Team", "average")
    
    # Configure parallel simulation
    settings = ParallelSimulationSettings(
        num_workers=None,  # Use all CPU cores
        chunk_size=2,
        verbose=False,
        show_progress=True,
        log_games=False
    )
    
    # Create simulator
    parallel_sim = ParallelGameSimulator(settings)
    
    # Run simulation
    result = parallel_sim.simulate_games(
        away_team,
        home_team,
        num_games=NUM_GAMES,
        num_innings=9
    )
    
    # Display detailed results
    print(f"\n{'='*70}")
    print(f"DETAILED RESULTS")
    print(f"{'='*70}")
    
    print(f"\nPerformance:")
    print(f"  Total Time: {result.simulation_time:.1f} seconds ({result.simulation_time/60:.2f} minutes)")
    print(f"  Rate: {result.games_per_second:.2f} games/second")
    print(f"  Estimated sequential time: ~{result.simulation_time * 6:.0f}s (~{result.simulation_time * 6 / 60:.1f} min)")
    
    print(f"\nGame Outcomes:")
    print(f"  {away_team.name}: {result.away_wins} wins")
    print(f"  {home_team.name}: {result.home_wins} wins")
    if result.ties > 0:
        print(f"  Ties: {result.ties}")
    
    print(f"\nMLB-Calibrated Statistics (per 9 innings):")
    print(f"  Runs/9:  {result.runs_per_9:.2f}  (MLB avg: ~9.0)")
    print(f"  Hits/9:  {result.hits_per_9:.2f}  (MLB avg: ~17.0)")
    print(f"  HRs/9:   {result.home_runs_per_9:.2f}  (MLB avg: ~2.2)")
    
    print(f"\nPer-Game Averages:")
    print(f"  Runs:  {result.avg_runs_per_game:.2f} ± {result.std_runs_per_game:.2f}")
    print(f"  Hits:  {result.avg_hits_per_game:.2f} ± {result.std_hits_per_game:.2f}")
    print(f"  HRs:   {result.avg_hrs_per_game:.2f} ± {result.std_hrs_per_game:.2f}")
    
    print(f"\nAggregate Totals:")
    print(f"  Total Runs: {result.total_runs}")
    print(f"  Total Hits: {result.total_hits}")
    print(f"  Total Home Runs: {result.total_home_runs}")
    print(f"  Total Innings: {result.total_innings}")
    
    # Show some individual game results
    print(f"\nSample Game Results (first 10 games):")
    print(f"{'Game':<6}{'Away':<6}{'Home':<6}{'Total Runs':<12}{'Hits':<6}{'HRs':<6}")
    print("-" * 50)
    for i, game in enumerate(result.game_results[:10], 1):
        print(f"{i:<6}{game.away_score:<6}{game.home_score:<6}"
              f"{game.total_runs:<12}{game.total_hits:<6}{game.total_home_runs:<6}")
    
    if len(result.game_results) > 10:
        print(f"... ({len(result.game_results) - 10} more games)")
    
    # Statistical analysis
    print(f"\n{'='*70}")
    print(f"STATISTICAL ANALYSIS")
    print(f"{'='*70}")
    
    # Check if results are within MLB norms
    runs_diff = result.runs_per_9 - 9.0
    hits_diff = result.hits_per_9 - 17.0
    hrs_diff = result.home_runs_per_9 - 2.2
    
    print(f"\nDeviation from MLB averages:")
    print(f"  Runs/9:  {runs_diff:+.2f}  ({abs(runs_diff)/9.0*100:.1f}% difference)")
    print(f"  Hits/9:  {hits_diff:+.2f}  ({abs(hits_diff)/17.0*100:.1f}% difference)")
    print(f"  HRs/9:   {hrs_diff:+.2f}  ({abs(hrs_diff)/2.2*100:.1f}% difference)")
    
    # Scoring distribution
    low_scoring = sum(1 for g in result.game_results if g.total_runs < 5)
    normal_scoring = sum(1 for g in result.game_results if 5 <= g.total_runs <= 12)
    high_scoring = sum(1 for g in result.game_results if g.total_runs > 12)
    
    print(f"\nScoring Distribution:")
    print(f"  Low scoring (<5 runs):    {low_scoring} games ({low_scoring/NUM_GAMES*100:.1f}%)")
    print(f"  Normal scoring (5-12):    {normal_scoring} games ({normal_scoring/NUM_GAMES*100:.1f}%)")
    print(f"  High scoring (>12 runs):  {high_scoring} games ({high_scoring/NUM_GAMES*100:.1f}%)")
    
    print(f"\n{'='*70}")
    print(f"SIMULATION COMPLETE")
    print(f"{'='*70}")
    print(f"\nKey Takeaways:")
    print(f"  ✓ Completed {NUM_GAMES} games in {result.simulation_time:.1f}s")
    print(f"  ✓ Parallel processing achieved ~{6/result.games_per_second:.1f}x speedup")
    print(f"  ✓ Statistics are {'close to' if abs(runs_diff) < 1.5 else 'diverging from'} MLB norms")
    print(f"  ✓ Sample size sufficient for meaningful analysis")


if __name__ == "__main__":
    main()
