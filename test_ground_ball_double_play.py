"""Test ground ball double play in realistic game simulation."""
import sys
sys.path.append('.')

from batted_ball import (
    GameSimulator,
    create_test_team
)
import numpy as np

print("Testing Ground Ball Double Plays in Realistic Game")
print("=" * 70)

# Seed for reproducibility
np.random.seed(42)

# Create teams
home_team = create_test_team("Home")
away_team = create_test_team("Away")

# Create game simulator  
game = GameSimulator(away_team, home_team, verbose=False)

print("\nSimulating full 9-inning game...")
print("-" * 70)

# Simulate game
final_state = game.simulate_game(num_innings=9)

# Now analyze the play-by-play for double plays
double_plays = []
force_outs = []
total_ground_outs = 0
all_outcomes = {}
ground_balls_with_runner_on_first = 0

for play in game.play_by_play:
    # Check outcome
    if hasattr(play, 'outcome'):
        outcome_name = play.outcome.name if hasattr(play.outcome, 'name') else str(play.outcome)
        
        # Track all outcomes
        all_outcomes[outcome_name] = all_outcomes.get(outcome_name, 0) + 1
        
        # For ground outs, check if runner was on first
        if outcome_name == 'ground_out':
            # Check the play description or events for runner info
            description = play.description.lower()
            if 'runner' in description or 'force' in description:
                print(f"\nGround out with runner context: {play.description}")
            
            # Count as ground ball with potential force situation
            # (We can't easily check baserunner state from play_by_play, but we can from events)
            total_ground_outs += 1
        
        if 'DOUBLE_PLAY' in outcome_name:
            double_plays.append(play)
            print(f"\n[DP] DOUBLE PLAY!")
            print(f"   Batter: {play.batter_name}")
            print(f"   Description: {play.description}")
            if hasattr(play, 'physics_data') and play.physics_data:
                print(f"   Ball location: {play.physics_data.get('landing_position', 'N/A')}")
        
        if 'FORCE_OUT' in outcome_name or 'force_out' in outcome_name:
            force_outs.append(play)
            print(f"\n[FORCE] FORCE OUT")
            print(f"   Batter: {play.batter_name}")
            print(f"   Description: {play.description}")
        
        if 'GROUND' in outcome_name or 'ground' in outcome_name:
            total_ground_outs += 1

print("\n" + "=" * 70)
print("SUMMARY")
print("=" * 70)
print(f"All outcomes seen:")
for outcome, count in sorted(all_outcomes.items()):
    print(f"  {outcome}: {count}")
print(f"\nTotal ground outs: {total_ground_outs}")
print(f"Force outs: {len(force_outs)}")
print(f"Double plays: {len(double_plays)}")

print(f"\nFinal score:")
print(f"Away: {final_state.away_score}")
print(f"Home: {final_state.home_score}")

# Check if we saw any double plays
if len(double_plays) > 0:
    print(f"\n[SUCCESS] Double plays are working ({len(double_plays)} in 9 innings)")
    print(f"Expected rate: ~1-2 per game")
elif len(force_outs) > 0:
    print(f"\n[WARNING] Force plays working ({len(force_outs)}), but no double plays yet")
    print("   (DP timing might need tuning)")
else:
    print("\n[INFO] No force plays or double plays seen in this game")
    print("   (Requires runner on first + ground ball for force play)")
    print(f"   Had {total_ground_outs} ground outs total")
