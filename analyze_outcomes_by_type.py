"""
Analyze batted ball outcomes by type to understand scoring issues.

Check:
1. What % of each ball type becomes a hit?
2. Are we getting realistic BABIP?
3. Is the issue line drive %, or line drive hit rates?
"""

from batted_ball import GameSimulator, create_test_team
from collections import Counter, defaultdict

def categorize_launch_angle(angle_deg):
    """Categorize launch angle into batted ball type."""
    if angle_deg < 10:
        return 'ground_ball'
    elif 10 <= angle_deg < 25:
        return 'line_drive'
    elif 25 <= angle_deg < 50:
        return 'fly_ball'
    else:
        return 'pop_up'

def analyze_outcomes_by_type():
    """Analyze outcomes by batted ball type."""
    print("Batted Ball Outcome Analysis")
    print("=" * 80)
    
    # Create teams
    away_team = create_test_team("Away", team_quality="average")
    home_team = create_test_team("Home", team_quality="average")
    
    # Create game simulator
    game = GameSimulator(
        away_team=away_team,
        home_team=home_team,
        verbose=False
    )
    
    # Run full game
    final_state = game.simulate_game(num_innings=9)
    
    # Collect data by ball type
    by_type = defaultdict(lambda: {'total': 0, 'hits': 0, 'outs': 0, 'outcomes': Counter()})
    
    for play in game.play_by_play:
        physics_data = getattr(play, 'physics_data', None)
        if physics_data and 'launch_angle_deg' in physics_data:
            launch_angle = physics_data['launch_angle_deg']
            exit_velo = physics_data.get('exit_velocity_mph', 0)
            outcome = getattr(play, 'outcome', 'unknown')
            
            ball_type = categorize_launch_angle(launch_angle)
            by_type[ball_type]['total'] += 1
            by_type[ball_type]['outcomes'][outcome] += 1
            
            # Categorize as hit or out
            if outcome in ['single', 'double', 'triple', 'home_run']:
                by_type[ball_type]['hits'] += 1
            elif outcome in ['ground_out', 'fly_out', 'line_out', 'force_out', 'double_play']:
                by_type[ball_type]['outs'] += 1
    
    print("\nOUTCOME RATES BY BALL TYPE")
    print("=" * 80)
    
    total_balls = sum(data['total'] for data in by_type.values())
    total_hits = sum(data['hits'] for data in by_type.values())
    total_outs = sum(data['outs'] for data in by_type.values())
    
    for ball_type in ['ground_ball', 'line_drive', 'fly_ball', 'pop_up']:
        if ball_type not in by_type:
            continue
            
        data = by_type[ball_type]
        count = data['total']
        hits = data['hits']
        outs = data['outs']
        
        pct_of_total = (count / total_balls) * 100 if total_balls > 0 else 0
        hit_rate = (hits / count) * 100 if count > 0 else 0
        
        print(f"\n{ball_type.upper()}: {count} balls ({pct_of_total:.1f}% of all batted balls)")
        print(f"  Hit rate: {hits}/{count} = {hit_rate:.1f}%")
        print(f"  Out rate: {outs}/{count} = {(outs/count)*100:.1f}%" if count > 0 else "")
        print(f"  Outcomes: {dict(data['outcomes'])}")
    
    # Calculate BABIP
    babip = total_hits / total_balls if total_balls > 0 else 0
    
    print("\n" + "=" * 80)
    print("OVERALL STATISTICS")
    print("=" * 80)
    print(f"Total batted balls: {total_balls}")
    print(f"Total hits: {total_hits}")
    print(f"Total outs: {total_outs}")
    print(f"BABIP: {babip:.3f} (target: .290-.310)")
    print(f"Final Score: Away {final_state.away_score} - Home {final_state.home_score}")
    print(f"Total runs: {final_state.away_score + final_state.home_score}")
    
    print("\n" + "=" * 80)
    print("MLB BENCHMARKS")
    print("=" * 80)
    print("Ground balls: ~24% hit rate")
    print("Line drives: ~60-70% hit rate")
    print("Fly balls: ~20-25% hit rate")
    print("Overall BABIP: ~.290-.310")

if __name__ == "__main__":
    analyze_outcomes_by_type()
