"""
Debug script to see why scoring is so low.

Check:
1. Are hits happening?
2. Are runners being created?
3. Is _handle_hit_baserunning being called?
"""

from batted_ball import GameSimulator, create_test_team

def debug_scoring():
    """Debug why scoring is so low."""
    print("Debug: Why is scoring so low?")
    print("=" * 70)
    
    # Create teams
    away_team = create_test_team("Away", team_quality="average")
    home_team = create_test_team("Home", team_quality="average")
    
    # Create game simulator with verbose output
    game = GameSimulator(
        away_team=away_team,
        home_team=home_team,
        verbose=True  # Enable play-by-play
    )
    
    # Run just 3 innings to see what's happening
    print("\nRunning 3-inning game with verbose output...\n")
    final_state = game.simulate_game(num_innings=3)
    
    print("\n" + "=" * 70)
    print("GAME SUMMARY")
    print("=" * 70)
    print(f"Final Score: Away {final_state.away_score} - Home {final_state.home_score}")
    print(f"Total Runs: {final_state.away_score + final_state.home_score}")
    print(f"Innings: {final_state.inning}")

if __name__ == "__main__":
    debug_scoring()
