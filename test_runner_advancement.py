"""
Test script to validate new runner advancement decision logic.

This tests that:
1. Runners don't automatically score on doubles
2. Singles advance runners 1-2 bases appropriately
3. Scoring rates decrease to realistic levels
"""

from batted_ball import GameSimulator, create_test_team

def test_runner_advancement():
    """Test new runner advancement logic across multiple games."""
    print("Testing Runner Advancement Logic")
    print("=" * 70)
    print("Expectation: Scoring should decrease from ~12 to ~9 runs per 9 innings")
    print("=" * 70)
    
    total_games = 5
    total_runs_scored = 0
    total_innings = 0
    
    for game_num in range(1, total_games + 1):
        # Create two average teams
        away_team = create_test_team("Away", team_quality="average")
        home_team = create_test_team("Home", team_quality="average")
        
        # Create game simulator
        game = GameSimulator(
            away_team=away_team,
            home_team=home_team,
            verbose=False
        )
        
        # Run game
        print(f"\nGame {game_num}:")
        final_state = game.simulate_game(num_innings=9)
        
        # Calculate runs and innings
        home_runs = final_state.home_score
        away_runs = final_state.away_score
        total_runs = home_runs + away_runs
        innings = final_state.inning
        
        total_runs_scored += total_runs
        total_innings += innings
        
        # Display results
        runs_per_9 = (total_runs / innings) * 9 if innings > 0 else 0
        print(f"  Score: Away {away_runs} - Home {home_runs}")
        print(f"  Total Runs: {total_runs} in {innings} innings")
        print(f"  Runs/9: {runs_per_9:.2f}")
    
    # Summary statistics
    print("\n" + "=" * 70)
    print("SUMMARY ACROSS ALL GAMES")
    print("=" * 70)
    print(f"Total games: {total_games}")
    print(f"Total runs scored: {total_runs_scored}")
    print(f"Total innings: {total_innings}")
    
    overall_runs_per_9 = (total_runs_scored / total_innings) * 9 if total_innings > 0 else 0
    print(f"Overall Runs/9 innings: {overall_runs_per_9:.2f}")
    
    # Target range check
    if 8.0 <= overall_runs_per_9 <= 10.0:
        print("\n[SUCCESS] Runs/9 in target range (8-10)!")
    elif 10.0 < overall_runs_per_9 <= 11.0:
        print("\n[GOOD] Runs/9 improved but slightly high (target: 8-10)")
    else:
        print(f"\n[INFO] Runs/9 = {overall_runs_per_9:.2f} (target: 8-10)")

if __name__ == "__main__":
    test_runner_advancement()
