"""Run multiple games to find double play situations."""
import sys
sys.path.append('.')

from batted_ball import GameSimulator, create_test_team
import numpy as np

print("Running Multiple Games to Test Double Plays")
print("=" * 70)

total_force_outs = 0
total_double_plays = 0
total_games = 10

for game_num in range(1, total_games + 1):
    np.random.seed(40 + game_num)
    
    home_team = create_test_team("Home")
    away_team = create_test_team("Away")
    
    game = GameSimulator(away_team, home_team, verbose=False)
    final_state = game.simulate_game(num_innings=9)
    
    # Count outcomes
    force_outs_this_game = 0
    double_plays_this_game = 0
    
    for play in game.play_by_play:
        if hasattr(play, 'outcome'):
            outcome_name = play.outcome.name if hasattr(play.outcome, 'name') else str(play.outcome)
            
            if outcome_name == 'force_out':
                force_outs_this_game += 1
            elif outcome_name == 'double_play':
                double_plays_this_game += 1
                print(f"\nGame {game_num}: DOUBLE PLAY!")
                print(f"  Batter: {play.batter_name}")
                # Skip description to avoid Unicode issues
                # print(f"  Description: {play.description}")
    
    total_force_outs += force_outs_this_game
    total_double_plays += double_plays_this_game
    
    print(f"Game {game_num}: {force_outs_this_game} force outs, {double_plays_this_game} DPs (Score: {final_state.away_score}-{final_state.home_score})")

print("\n" + "=" * 70)
print("SUMMARY ACROSS ALL GAMES")
print("=" * 70)
print(f"Total games: {total_games}")
print(f"Total force outs: {total_force_outs} ({total_force_outs/total_games:.1f} per game)")
print(f"Total double plays: {total_double_plays} ({total_double_plays/total_games:.1f} per game)")
print(f"\nMLB Average: ~1.5 double plays per game")

if total_double_plays > 0:
    print(f"\n[SUCCESS] Double plays are working!")
elif total_force_outs > 0:
    print(f"\n[PARTIAL] Force plays working, but DPs need timing adjustment")
else:
    print(f"\n[FAIL] Neither force plays nor DPs are occurring")
