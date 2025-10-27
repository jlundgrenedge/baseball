"""
Debug: Count play outcomes to understand what's happening.
"""

from batted_ball import GameSimulator, create_test_team
from collections import Counter

def count_outcomes():
    """Count different play outcomes."""
    print("Counting Play Outcomes")
    print("=" * 70)
    
    # Create teams
    away_team = create_test_team("Away", team_quality="average")
    home_team = create_test_team("Home", team_quality="average")
    
    # Create game simulator
    game = GameSimulator(
        away_team=away_team,
        home_team=home_team,
        verbose=False
    )
    
    # Run 9 innings
    final_state = game.simulate_game(num_innings=9)
    
    # Count outcomes from play-by-play
    outcomes = Counter()
    for play in game.play_by_play:
        if hasattr(play, 'outcome') and play.outcome:
            outcomes[play.outcome] += 1
    
    print(f"\nFinal Score: Away {final_state.away_score} - Home {final_state.home_score}")
    print(f"Total Runs: {final_state.away_score + final_state.home_score}")
    print(f"\nPlay Outcomes:")
    for outcome, count in sorted(outcomes.items(), key=lambda x: x[1], reverse=True):
        print(f"  {outcome}: {count}")
    
    print(f"\nTotal Plays: {sum(outcomes.values())}")

if __name__ == "__main__":
    count_outcomes()
