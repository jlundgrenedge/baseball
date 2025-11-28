"""Analyze BABIP by batted ball type from game logs."""
import re
import sys

def analyze_babip(log_file):
    with open(log_file, 'r', encoding='utf-8') as f:
        content = f.read()

    stats = {
        'LINE_DRIVE': {'hits': 0, 'outs': 0, 'hr': 0},
        'GROUND_BALL': {'hits': 0, 'outs': 0, 'hr': 0},
        'FLY_BALL': {'hits': 0, 'outs': 0, 'hr': 0},
        'POPUP': {'hits': 0, 'outs': 0, 'hr': 0},
    }

    # Find batted ball sections with outcome
    bb_pattern = r'BATTED BALL: (\w+).*?OutcomeCodePA: (\w+)'
    matches = re.findall(bb_pattern, content, re.DOTALL)

    for bb_type, outcome in matches:
        bb_type = bb_type.upper()
        if bb_type not in stats:
            print(f'Unknown type: {bb_type}')
            continue
        
        if outcome == 'HOMERUN':
            stats[bb_type]['hr'] += 1
        elif outcome in ['SINGLE', 'DOUBLE', 'TRIPLE']:
            stats[bb_type]['hits'] += 1
        elif outcome.startswith('OUT') or outcome == 'DOUBLE_PLAY':
            stats[bb_type]['outs'] += 1
        # Errors and reached_on_error don't count in BABIP

    print('BABIP by Batted Ball Type (excluding HR):')
    print('=' * 70)
    print(f"{'Type':15s} {'BABIP':>8s} {'Hits':>6s} {'Outs':>6s} {'HR':>5s} {'BIP':>6s}  {'Target':12s} {'Status':8s}")
    print('-' * 70)

    targets = {
        'LINE_DRIVE': (0.700, 0.730, '.700-.730'),
        'GROUND_BALL': (0.200, 0.250, '.200-.250'),
        'FLY_BALL': (0.095, 0.120, '.095-.120'),
        'POPUP': (0.020, 0.100, '.020-.100'),
    }

    issues = []
    for bb_type in ['LINE_DRIVE', 'GROUND_BALL', 'FLY_BALL', 'POPUP']:
        data = stats[bb_type]
        bip = data['hits'] + data['outs']
        low, high, target_str = targets[bb_type]
        
        if bip > 0:
            babip = data['hits'] / bip
            if babip < low:
                status = '🔻 LOW'
                issues.append((bb_type, babip, low, high))
            elif babip > high:
                status = '🔺 HIGH'
                issues.append((bb_type, babip, low, high))
            else:
                status = '✓ OK'
            print(f"{bb_type:15s} {babip:8.3f} {data['hits']:6d} {data['outs']:6d} {data['hr']:5d} {bip:6d}  {target_str:12s} {status}")
        else:
            print(f"{bb_type:15s}      N/A {data['hits']:6d} {data['outs']:6d} {data['hr']:5d} {0:6d}  {target_str:12s}")

    print()
    total_hits = sum(d['hits'] for d in stats.values())
    total_outs = sum(d['outs'] for d in stats.values())
    total_hr = sum(d['hr'] for d in stats.values())
    total_bip = total_hits + total_outs
    if total_bip > 0:
        print(f'Overall BABIP: {total_hits/total_bip:.3f} ({total_hits} hits / {total_bip} BIP)')
    print(f'Total HR: {total_hr}')
    
    if issues:
        print()
        print('Issues to address:')
        for bb_type, babip, low, high in issues:
            if babip < low:
                print(f'  - {bb_type}: BABIP {babip:.3f} is below target {low:.3f}')
            else:
                print(f'  - {bb_type}: BABIP {babip:.3f} is above target {high:.3f}')

if __name__ == '__main__':
    if len(sys.argv) > 1:
        analyze_babip(sys.argv[1])
    else:
        # Default to latest game log
        import glob
        logs = glob.glob('game_logs/game_log_*.txt')
        if logs:
            latest = max(logs)
            print(f'Analyzing: {latest}\n')
            analyze_babip(latest)
        else:
            print('No game logs found')
