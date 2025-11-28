"""
Analyze why ground ball BABIP is too low (.056 vs target .200-.250).
"""

import os
import re
from collections import defaultdict

def analyze_game_log(log_path):
    """Parse game log for ground ball and fielding data."""
    
    with open(log_path, 'r', encoding='utf-8', errors='replace') as f:
        content = f.read()
    
    lines = content.split('\n')
    
    # Collect ground ball plays
    ground_ball_outcomes = []
    
    for i, line in enumerate(lines):
        # Check for GROUND_BALL type
        if 'GROUND_BALL' in line or 'BattedBallType.GROUND_BALL' in line:
            # Get surrounding context
            start = max(0, i - 30)
            end = min(len(lines), i + 20)
            context_lines = lines[start:end]
            context = '\n'.join(context_lines)
            
            # Determine outcome
            outcome = "UNKNOWN"
            
            # Look in the context for the outcome
            for ctx_line in context_lines:
                if 'SINGLE' in ctx_line:
                    outcome = "SINGLE"
                    break
                elif 'DOUBLE' in ctx_line:
                    outcome = "DOUBLE"
                    break
                elif 'PlayOutcome.OUT' in ctx_line or 'Result: OUT' in ctx_line:
                    outcome = "OUT"
                    break
                elif 'FIELDERS_CHOICE' in ctx_line:
                    outcome = "FIELDERS_CHOICE"
                    break
            
            # Extract exit velocity if available
            ev_match = re.search(r'exit_velocity[:\s=]*(\d+\.?\d*)', context, re.IGNORECASE)
            ev = float(ev_match.group(1)) if ev_match else None
            
            # Extract landing position
            land_x_match = re.search(r'landing_x[:\s=]*(-?\d+\.?\d*)', context)
            land_y_match = re.search(r'landing_y[:\s=]*(-?\d+\.?\d*)', context)
            land_x = float(land_x_match.group(1)) if land_x_match else None
            land_y = float(land_y_match.group(1)) if land_y_match else None
            
            ground_ball_outcomes.append({
                'outcome': outcome,
                'exit_velocity': ev,
                'land_x': land_x,
                'land_y': land_y,
                'line': i
            })
    
    return ground_ball_outcomes


def main():
    log_dir = "game_logs"
    
    logs = sorted([f for f in os.listdir(log_dir) if f.endswith('.txt')], reverse=True)
    
    if not logs:
        print("No game logs found")
        return
    
    log_path = os.path.join(log_dir, logs[0])
    print(f"Analyzing: {log_path}")
    print()
    
    outcomes = analyze_game_log(log_path)
    
    # Summarize
    outcome_counts = defaultdict(int)
    ev_by_outcome = defaultdict(list)
    
    for gb in outcomes:
        outcome_counts[gb['outcome']] += 1
        if gb['exit_velocity']:
            ev_by_outcome[gb['outcome']].append(gb['exit_velocity'])
    
    print(f"Total ground balls found: {len(outcomes)}")
    print()
    print("Ground Ball Outcomes:")
    for outcome, count in sorted(outcome_counts.items()):
        pct = count / len(outcomes) * 100 if outcomes else 0
        avg_ev = sum(ev_by_outcome[outcome]) / len(ev_by_outcome[outcome]) if ev_by_outcome[outcome] else 0
        print(f"  {outcome}: {count} ({pct:.1f}%) - Avg EV: {avg_ev:.1f} mph")
    
    hits = outcome_counts.get('SINGLE', 0) + outcome_counts.get('DOUBLE', 0)
    total = len(outcomes)
    if total > 0:
        babip = hits / total
        print(f"\nGround Ball BABIP: {babip:.3f}")
        print(f"Target range: .200-.250")
    
    # Print some sample ground ball plays
    print("\n" + "="*60)
    print("Sample Ground Ball Plays (first 5 singles, first 5 outs):")
    print("="*60)
    
    singles = [gb for gb in outcomes if gb['outcome'] == 'SINGLE'][:5]
    outs = [gb for gb in outcomes if gb['outcome'] == 'OUT'][:5]
    
    print("\nSINGLES:")
    for gb in singles:
        print(f"  EV: {gb['exit_velocity']}, Landing: ({gb['land_x']}, {gb['land_y']})")
    
    print("\nOUTS:")
    for gb in outs:
        print(f"  EV: {gb['exit_velocity']}, Landing: ({gb['land_x']}, {gb['land_y']})")


if __name__ == "__main__":
    main()
