#!/usr/bin/env python3
"""
Run multiple games to get stable BABIP statistics
"""
import sys
from batted_ball.game_simulation import GameSimulator, create_test_team

# Track outcomes across multiple games
all_ground_balls = []
all_line_drives = []
all_fly_balls = []
all_pop_ups = []

def classify_ball(launch_angle):
    """Classify batted ball by launch angle"""
    if launch_angle < 10:
        return 'GROUND_BALL'
    elif launch_angle < 25:
        return 'LINE_DRIVE'
    elif launch_angle < 50:
        return 'FLY_BALL'
    else:
        return 'POP_UP'

# Run 5 games (45 innings)
print("Running 5 games to gather BABIP statistics...")
print("=" * 80)

for game_num in range(1, 6):
    print(f"\nGame {game_num}/5...", end=" ", flush=True)
    
    away_team = create_test_team("Away", 70)
    home_team = create_test_team("Home", 70)
    sim = GameSimulator(away_team, home_team)
    result = sim.simulate_game(num_innings=9)
    
    # Analyze plays
    for play in result['play_log']:
        if 'launch_angle' not in play or play.get('outcome_type') in ['strikeout', 'walk', 'hbp']:
            continue
            
        ball_type = classify_ball(play['launch_angle'])
        is_hit = play.get('outcome_type') in ['single', 'double', 'triple', 'home_run']
        
        if ball_type == 'GROUND_BALL':
            all_ground_balls.append(is_hit)
        elif ball_type == 'LINE_DRIVE':
            all_line_drives.append(is_hit)
        elif ball_type == 'FLY_BALL':
            all_fly_balls.append(is_hit)
        elif ball_type == 'POP_UP':
            all_pop_ups.append(is_hit)
    
    print(f"Done. Score: {result['away_score']}-{result['home_score']}")

# Calculate statistics
print("\n" + "=" * 80)
print("AGGREGATE STATISTICS (5 games)")
print("=" * 80)

total_balls = len(all_ground_balls) + len(all_line_drives) + len(all_fly_balls) + len(all_pop_ups)
total_hits = sum(all_ground_balls) + sum(all_line_drives) + sum(all_fly_balls) + sum(all_pop_ups)

print(f"\nTotal batted balls: {total_balls}")
print(f"Total hits: {total_hits}")
print(f"Overall BABIP: {total_hits/total_balls:.3f}")

print(f"\nGROUND BALLS: {len(all_ground_balls)} balls")
if all_ground_balls:
    gb_hit_rate = sum(all_ground_balls) / len(all_ground_balls)
    print(f"  Hit rate: {sum(all_ground_balls)}/{len(all_ground_balls)} = {gb_hit_rate:.1%}")
    print(f"  Target: ~24%")
    print(f"  Status: {'✓ GOOD' if 0.20 <= gb_hit_rate <= 0.30 else '✗ OFF TARGET'}")

print(f"\nLINE DRIVES: {len(all_line_drives)} balls")
if all_line_drives:
    ld_hit_rate = sum(all_line_drives) / len(all_line_drives)
    print(f"  Hit rate: {sum(all_line_drives)}/{len(all_line_drives)} = {ld_hit_rate:.1%}")
    print(f"  Target: 60-70%")
    print(f"  Status: {'✓ GOOD' if 0.55 <= ld_hit_rate <= 0.75 else '✗ OFF TARGET'}")

print(f"\nFLY BALLS: {len(all_fly_balls)} balls")
if all_fly_balls:
    fb_hit_rate = sum(all_fly_balls) / len(all_fly_balls)
    print(f"  Hit rate: {sum(all_fly_balls)}/{len(all_fly_balls)} = {fb_hit_rate:.1%}")
    print(f"  Target: 20-25%")
    print(f"  Status: {'✓ GOOD' if 0.18 <= fb_hit_rate <= 0.28 else '✗ OFF TARGET'}")

print(f"\nPOP UPS: {len(all_pop_ups)} balls")
if all_pop_ups:
    pu_hit_rate = sum(all_pop_ups) / len(all_pop_ups)
    print(f"  Hit rate: {sum(all_pop_ups)}/{len(all_pop_ups)} = {pu_hit_rate:.1%}")
    print(f"  Target: ~2-5%")
    print(f"  Status: {'✓ GOOD' if pu_hit_rate <= 0.10 else '✗ OFF TARGET'}")

print("\n" + "=" * 80)
