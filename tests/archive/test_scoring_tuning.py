"""
Test script to validate scoring and HR rate tuning.

This script runs a small sample of games to verify that:
1. HR rate is reduced closer to MLB average (2.2/9)
2. Overall run scoring is increased (toward 9.0/9)
3. Runs come more from organic play (hits, baserunning) vs HRs
"""

from batted_ball.game_simulation import create_test_team, GameSimulator
from batted_ball.environment import create_standard_environment

def run_test_games(num_games=5):
    """Run test games and report statistics."""
    
    print("=" * 60)
    print(f"Running {num_games} test games to validate tuning...")
    print("=" * 60)
    print()
    
    # Create teams
    home_team = create_test_team("Home", team_quality="good")
    away_team = create_test_team("Away", team_quality="good")
    
    # Track statistics
    total_runs = 0
    total_hits = 0
    total_hrs = 0
    total_innings = 0
    
    # Run games
    for i in range(num_games):
        print(f"Game {i+1}/{num_games}...", end=" ", flush=True)
        
        env = create_standard_environment()
        sim = GameSimulator(home_team, away_team, env)
        result = sim.simulate_game()
        
        # Accumulate stats
        total_runs += result.away_score + result.home_score
        total_hits += result.total_hits
        total_hrs += result.total_home_runs
        total_innings += 9
        
        print(f"Final: {result.away_score}-{result.home_score}, HRs: {result.total_home_runs}")
    
    print()
    print("=" * 60)
    print(f"RESULTS ACROSS {num_games} GAMES ({total_innings} innings)")
    print("=" * 60)
    
    # Calculate per-9-inning stats
    runs_per_9 = (total_runs / total_innings) * 9 if total_innings > 0 else 0
    hrs_per_9 = (total_hrs / total_innings) * 9 if total_innings > 0 else 0
    hits_per_9 = (total_hits / total_innings) * 9 if total_innings > 0 else 0
    
    print(f"Runs/9: {runs_per_9:.2f} (MLB target: ~9.0)")
    print(f"HRs/9: {hrs_per_9:.2f} (MLB target: ~2.2)")
    print(f"Hits/9: {hits_per_9:.1f} (MLB target: ~17.0)")
    print()
    print(f"Total HRs: {total_hrs}")
    print(f"Total Runs: {total_runs}")
    
    if total_hrs > 0:
        hr_contribution = (total_hrs * 4) / total_runs * 100  # HRs account for ~4 runs on average
        print(f"HR contribution to runs: ~{hr_contribution:.0f}% (counting runners on base)")
    
    print()
    print("ANALYSIS:")
    print("-" * 60)
    
    # Evaluate results
    if 2.0 <= hrs_per_9 <= 2.5:
        print("✓ HR rate looks good!")
    elif hrs_per_9 > 2.5:
        print(f"✗ HR rate still too high ({hrs_per_9:.2f} vs target 2.2)")
    else:
        print(f"✗ HR rate may be too low ({hrs_per_9:.2f} vs target 2.2)")
    
    if 8.0 <= runs_per_9 <= 10.0:
        print("✓ Run scoring looks good!")
    elif runs_per_9 < 8.0:
        print(f"✗ Run scoring still too low ({runs_per_9:.2f} vs target 9.0)")
    else:
        print(f"✗ Run scoring may be too high ({runs_per_9:.2f} vs target 9.0)")
    
    if 15.0 <= hits_per_9 <= 19.0:
        print("✓ Hit rate looks good!")
    else:
        print(f"? Hit rate: {hits_per_9:.1f} (target ~17.0)")
    
    print("=" * 60)


if __name__ == "__main__":
    run_test_games(60)
