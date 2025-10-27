"""Run multiple games to get average statistics."""
import sys
sys.path.append('.')

from batted_ball import GameSimulator, create_test_team
import numpy as np

print("Running 5 full games for statistical average...")
print("=" * 60)

stats = {
    'runs': [],
    'hits': [],
    'hrs': [],
    'triples': [],
    'babip': [],
    'strikeouts': [],
    'walks': []
}

for game_num in range(5):
    print(f"\nGame {game_num + 1}...", end='', flush=True)
    
    # Create two average teams
    away_team = create_test_team(f"Away {game_num+1}", "average")
    home_team = create_test_team(f"Home {game_num+1}", "average")
    
    # Create and run simulation
    simulator = GameSimulator(away_team, home_team, verbose=False)
    final_state = simulator.simulate_game(num_innings=9)
    
    innings_played = final_state.inning - (0 if final_state.is_top else 1)
    
    # Count outcomes
    singles = sum(1 for p in simulator.play_by_play if 'SINGLE' in p.description and 'DOUBLE' not in p.description and 'TRIPLE' not in p.description)
    doubles = sum(1 for p in simulator.play_by_play if 'DOUBLE' in p.description)
    triples = sum(1 for p in simulator.play_by_play if 'TRIPLE' in p.description)
    homers = sum(1 for p in simulator.play_by_play if 'HOME RUN' in p.description)
    strikeouts = sum(1 for p in simulator.play_by_play if 'STRIKEOUT' in p.description or 'strikes out' in p.description.lower())
    walks = sum(1 for p in simulator.play_by_play if 'WALK' in p.description or 'walks' in p.description.lower())
    balls_in_play = sum(1 for p in simulator.play_by_play if p.description and not any(x in p.description for x in ['STRIKEOUT', 'WALK', 'strikes out', 'walks']))
    
    # Calculate BABIP
    hits_on_bip = singles + doubles + triples
    outs_on_bip = balls_in_play - hits_on_bip - homers
    babip = hits_on_bip / (hits_on_bip + outs_on_bip) if (hits_on_bip + outs_on_bip) > 0 else 0
    
    # Per-9 rates
    total_runs = final_state.away_score + final_state.home_score
    runs_per_9 = (total_runs / innings_played) * 9
    hits_per_9 = (final_state.total_hits / innings_played) * 9
    hrs_per_9 = (final_state.total_home_runs / innings_played) * 9
    
    stats['runs'].append(runs_per_9)
    stats['hits'].append(hits_per_9)
    stats['hrs'].append(hrs_per_9)
    stats['triples'].append(triples)
    stats['babip'].append(babip)
    stats['strikeouts'].append(strikeouts)
    stats['walks'].append(walks)
    
    print(f" {final_state.away_score}-{final_state.home_score} ({innings_played} inn)")

print(f"\n{'=' * 60}")
print("AVERAGE STATISTICS (5 games)")
print(f"{'=' * 60}")
print(f"Runs/9:      {np.mean(stats['runs']):.1f} ± {np.std(stats['runs']):.1f} (MLB: ~9.0)")
print(f"Hits/9:      {np.mean(stats['hits']):.1f} ± {np.std(stats['hits']):.1f} (MLB: ~17.0)")
print(f"HRs/9:       {np.mean(stats['hrs']):.2f} ± {np.std(stats['hrs']):.2f} (MLB: ~2.2)")
print(f"Triples/game: {np.mean(stats['triples']):.1f} ± {np.std(stats['triples']):.1f} (MLB: 0-1)")
print(f"BABIP:       {np.mean(stats['babip']):.3f} ± {np.std(stats['babip']):.3f} (MLB: ~.300)")
print(f"Strikeouts:  {np.mean(stats['strikeouts']):.1f} ± {np.std(stats['strikeouts']):.1f}")
print(f"Walks:       {np.mean(stats['walks']):.1f} ± {np.std(stats['walks']):.1f}")

print(f"\n{'=' * 60}")
print("ASSESSMENT")
print(f"{'=' * 60}")

# Check each metric
def assess(name, value, target, tolerance=0.15):
    diff_pct = abs(value - target) / target
    if diff_pct <= tolerance:
        return f"✓ {name}: EXCELLENT"
    elif diff_pct <= 0.30:
        return f"~ {name}: GOOD (within 30%)"
    else:
        return f"✗ {name}: NEEDS WORK ({diff_pct*100:.0f}% off)"

print(assess("Runs/9", np.mean(stats['runs']), 9.0, 0.20))
print(assess("Hits/9", np.mean(stats['hits']), 17.0, 0.15))
print(assess("HRs/9", np.mean(stats['hrs']), 2.2, 0.30))
print(assess("BABIP", np.mean(stats['babip']), 0.300, 0.10))
