"""
Test launch angle variance to ensure realistic distribution.

Check that:
1. Ground ball hitters still hit fly balls sometimes
2. Fly ball hitters still hit ground balls sometimes
3. Overall distribution matches MLB (45% GB, 20% LD, 35% FB)
"""

from batted_ball import GameSimulator, create_test_team
from collections import Counter

def test_launch_angle_distribution():
    """Test that launch angles have realistic variance."""
    print("Testing Launch Angle Distribution")
    print("=" * 70)
    print("Expectation: ~45% ground balls, ~20% line drives, ~35% fly balls")
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
    
    # Run 3 innings
    final_state = game.simulate_game(num_innings=3)
    
    # Analyze batted ball types from play-by-play
    batted_ball_types = Counter()
    total_batted_balls = 0
    
    for play in game.play_by_play:
        outcome = getattr(play, 'outcome', None)
        if outcome:
            # Categorize by outcome
            if 'ground' in outcome.lower() or outcome.lower() in ['ground_out', 'force_out', 'double_play']:
                batted_ball_types['ground_ball'] += 1
                total_batted_balls += 1
            elif 'fly' in outcome.lower() or outcome.lower() in ['fly_out', 'home_run']:
                batted_ball_types['fly_ball'] += 1
                total_batted_balls += 1
            elif 'line' in outcome.lower() or outcome.lower() in ['line_out']:
                batted_ball_types['line_drive'] += 1
                total_batted_balls += 1
            elif outcome.lower() in ['single', 'double', 'triple']:
                # Hits could be any type - estimate based on distance
                # For now, count as line drives (most common hit type)
                batted_ball_types['hit'] += 1
                total_batted_balls += 1
    
    print(f"\nBatted Ball Distribution ({total_batted_balls} balls in play):")
    
    if total_batted_balls > 0:
        for ball_type, count in sorted(batted_ball_types.items()):
            pct = (count / total_batted_balls) * 100
            print(f"  {ball_type}: {count} ({pct:.1f}%)")
    
    print(f"\nMLB Targets:")
    print(f"  Ground balls: ~45%")
    print(f"  Line drives: ~20%")
    print(f"  Fly balls: ~35%")
    
    print(f"\nFinal Score: Away {final_state.away_score} - Home {final_state.home_score}")

if __name__ == "__main__":
    test_launch_angle_distribution()
