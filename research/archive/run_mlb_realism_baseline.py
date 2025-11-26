"""
MLB Realism Baseline Metrics Harness

This script establishes a reproducible baseline measurement of all 10 MLB realism
benchmarks for the current simulation engine (Pass 3 baseline).

Purpose:
- Simulate configurable number of games
- Collect comprehensive statistics
- Compare against MLB benchmarks
- Output results in JSON and Markdown formats
- Provide baseline for v2.0 comparisons

Usage:
    python research/run_mlb_realism_baseline.py --games 20
    python research/run_mlb_realism_baseline.py --games 100 --output custom_name
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import argparse
import json
from datetime import datetime
from pathlib import Path
import numpy as np

from batted_ball import GameSimulator, create_test_team
from batted_ball.series_metrics import SeriesMetrics


def run_baseline_simulation(num_games=20, verbose=False):
    """
    Run baseline simulation for specified number of games.

    Parameters
    ----------
    num_games : int
        Number of games to simulate (default: 20)
    verbose : bool
        Whether to print game-by-game output (default: False)

    Returns
    -------
    SeriesMetrics
        Comprehensive statistics for the simulated series
    """
    print(f"\n{'='*80}")
    print(f"MLB REALISM BASELINE SIMULATION")
    print(f"{'='*80}\n")
    print(f"Configuration:")
    print(f"  Games to simulate: {num_games}")
    print(f"  Verbose output: {verbose}")
    print(f"  Teams: Average vs Average (for baseline neutrality)")
    print()

    # Create neutral teams (both "average" quality)
    away_team = create_test_team("Visitors", "average")
    home_team = create_test_team("Home Team", "average")

    # Initialize series metrics
    series = SeriesMetrics()
    series.away_team_name = away_team.name
    series.home_team_name = home_team.name

    # Simulate games
    print(f"Simulating {num_games} games...")
    for game_num in range(1, num_games + 1):
        if not verbose:
            # Progress indicator
            if game_num % 5 == 0 or game_num == 1:
                print(f"  Game {game_num}/{num_games}...", end='', flush=True)
        else:
            print(f"\n{'='*40}")
            print(f"Game {game_num}/{num_games}")
            print(f"{'='*40}")

        # Simulate game
        simulator = GameSimulator(away_team, home_team, verbose=verbose)
        final_state = simulator.simulate_game(num_innings=9)

        # Update series metrics
        series.update_from_game(final_state)

        if not verbose:
            if game_num % 5 == 0:
                print(f" Done. Score: {final_state.away_score}-{final_state.home_score}")

    print(f"\n✅ Simulation complete: {num_games} games\n")

    return series


def analyze_distributions(series):
    """
    Analyze detailed distributions beyond standard metrics.

    Parameters
    ----------
    series : SeriesMetrics
        Series statistics

    Returns
    -------
    dict
        Dictionary of distribution analyses
    """
    combined_evs = series.away_batting.exit_velocities + series.home_batting.exit_velocities
    combined_las = series.away_batting.launch_angles + series.home_batting.launch_angles

    distributions = {}

    # Exit velocity distribution
    if combined_evs:
        ev_array = np.array(combined_evs)
        distributions['exit_velocity'] = {
            'mean': float(np.mean(ev_array)),
            'median': float(np.median(ev_array)),
            'std': float(np.std(ev_array)),
            'min': float(np.min(ev_array)),
            'max': float(np.max(ev_array)),
            'percentile_25': float(np.percentile(ev_array, 25)),
            'percentile_75': float(np.percentile(ev_array, 75)),
            'percentile_90': float(np.percentile(ev_array, 90)),
            'percentile_95': float(np.percentile(ev_array, 95)),
            'count_95plus': int(np.sum(ev_array >= 95)),
            'percent_95plus': float(np.sum(ev_array >= 95) / len(ev_array) * 100),
            'count_100plus': int(np.sum(ev_array >= 100)),
            'percent_100plus': float(np.sum(ev_array >= 100) / len(ev_array) * 100),
        }

    # Launch angle distribution
    if combined_las:
        la_array = np.array(combined_las)
        distributions['launch_angle'] = {
            'mean': float(np.mean(la_array)),
            'median': float(np.median(la_array)),
            'std': float(np.std(la_array)),
            'min': float(np.min(la_array)),
            'max': float(np.max(la_array)),
            'percentile_25': float(np.percentile(la_array, 25)),
            'percentile_75': float(np.percentile(la_array, 75)),
        }

        # Batted ball type percentages
        ground_balls = np.sum(la_array < 10)
        line_drives = np.sum((la_array >= 10) & (la_array < 25))
        fly_balls = np.sum((la_array >= 25) & (la_array < 50))
        pop_ups = np.sum(la_array >= 50)
        total = len(la_array)

        distributions['batted_ball_types'] = {
            'ground_balls': int(ground_balls),
            'line_drives': int(line_drives),
            'fly_balls': int(fly_balls),
            'pop_ups': int(pop_ups),
            'ground_ball_pct': float(ground_balls / total * 100),
            'line_drive_pct': float(line_drives / total * 100),
            'fly_ball_pct': float(fly_balls / total * 100),
            'pop_up_pct': float(pop_ups / total * 100),
        }

    # Calculate combined metrics
    combined_batting = series.away_batting
    combined_batting.at_bats += series.home_batting.at_bats
    combined_batting.hits += series.home_batting.hits
    combined_batting.walks += series.home_batting.walks
    combined_batting.strikeouts += series.home_batting.strikeouts
    combined_batting.balls_in_play += series.home_batting.balls_in_play
    combined_batting.home_runs += series.home_batting.home_runs
    combined_batting.fly_balls += series.home_batting.fly_balls
    combined_batting.hit_by_pitch += series.home_batting.hit_by_pitch
    combined_batting.sacrifice_flies += series.home_batting.sacrifice_flies

    # Plate appearance metrics
    total_pa = (combined_batting.at_bats + combined_batting.walks +
                combined_batting.hit_by_pitch + combined_batting.sacrifice_flies)

    if total_pa > 0:
        distributions['plate_appearance_outcomes'] = {
            'total_pa': total_pa,
            'strikeouts': combined_batting.strikeouts,
            'walks': combined_batting.walks,
            'balls_in_play': combined_batting.balls_in_play,
            'k_rate': float(combined_batting.strikeouts / total_pa),
            'bb_rate': float(combined_batting.walks / total_pa),
            'contact_rate': float(combined_batting.balls_in_play / total_pa),
        }

    return distributions


def save_results(series, distributions, output_name="baseline"):
    """
    Save results to JSON and Markdown files.

    Parameters
    ----------
    series : SeriesMetrics
        Series statistics
    distributions : dict
        Distribution analyses
    output_name : str
        Base name for output files (default: "baseline")
    """
    # Create results directory
    results_dir = Path("research/results")
    results_dir.mkdir(parents=True, exist_ok=True)

    # Compute realism checks
    series.compute_realism_checks()

    # Prepare JSON output
    json_data = {
        'metadata': {
            'timestamp': datetime.now().isoformat(),
            'num_games': series.num_games,
            'away_team': series.away_team_name,
            'home_team': series.home_team_name,
            'simulation_version': 'Pass 3 Baseline (5/10 passing)',
        },
        'series_summary': {
            'away_wins': series.away_wins,
            'home_wins': series.home_wins,
            'away_total_runs': series.away_runs,
            'home_total_runs': series.home_runs,
            'avg_runs_per_game': (series.away_runs + series.home_runs) / (2 * series.num_games),
        },
        'mlb_benchmarks': {},
        'detailed_metrics': {},
        'distributions': distributions,
    }

    # Add MLB benchmarks
    for check in series.realism_checks:
        json_data['mlb_benchmarks'][check.metric_name] = {
            'actual': float(check.actual_value),
            'mlb_min': float(check.mlb_min),
            'mlb_max': float(check.mlb_max),
            'mlb_avg': float(check.mlb_avg) if check.mlb_avg is not None else None,
            'status': check.status,
            'passing': check.status == 'OK',
        }

    # Count passing benchmarks
    passing_count = sum(1 for check in series.realism_checks if check.status == 'OK')
    total_count = len(series.realism_checks)
    json_data['metadata']['benchmarks_passing'] = f"{passing_count}/{total_count}"

    # Add detailed metrics (combined batting)
    combined_batting = series.away_batting
    combined_batting.at_bats += series.home_batting.at_bats
    combined_batting.hits += series.home_batting.hits
    combined_batting.singles += series.home_batting.singles
    combined_batting.doubles += series.home_batting.doubles
    combined_batting.triples += series.home_batting.triples
    combined_batting.home_runs += series.home_batting.home_runs
    combined_batting.walks += series.home_batting.walks
    combined_batting.strikeouts += series.home_batting.strikeouts
    combined_batting.fly_balls += series.home_batting.fly_balls
    combined_batting.ground_balls += series.home_batting.ground_balls
    combined_batting.line_drives += series.home_batting.line_drives
    combined_batting.balls_in_play += series.home_batting.balls_in_play
    combined_batting.balls_in_play_no_hr += series.home_batting.balls_in_play_no_hr
    combined_batting.hard_hit_balls += series.home_batting.hard_hit_balls

    json_data['detailed_metrics']['batting'] = {
        'avg': float(combined_batting.get_batting_avg()),
        'obp': float(combined_batting.get_obp()),
        'slg': float(combined_batting.get_slg()),
        'ops': float(combined_batting.get_ops()),
        'iso': float(combined_batting.get_iso()),
        'babip': float(combined_batting.get_babip()),
        'woba': float(combined_batting.get_woba()),
        'k_rate': float(combined_batting.get_k_rate()),
        'bb_rate': float(combined_batting.get_bb_rate()),
        'hr_fb_rate': float(combined_batting.get_hr_fb_rate()),
    }

    # Add pitching metrics
    combined_era = (series.away_pitching.get_era() + series.home_pitching.get_era()) / 2
    combined_whip = (series.away_pitching.get_whip() + series.home_pitching.get_whip()) / 2

    json_data['detailed_metrics']['pitching'] = {
        'era': float(combined_era),
        'whip': float(combined_whip),
        'k_per_9': float((series.away_pitching.get_k_per_9() + series.home_pitching.get_k_per_9()) / 2),
        'bb_per_9': float((series.away_pitching.get_bb_per_9() + series.home_pitching.get_bb_per_9()) / 2),
    }

    # Save JSON
    json_path = results_dir / f"{output_name}_summary.json"
    with open(json_path, 'w') as f:
        json.dump(json_data, f, indent=2)
    print(f"📄 JSON saved to: {json_path}")

    # Save Markdown report
    md_path = results_dir / f"{output_name}_summary.md"
    with open(md_path, 'w') as f:
        f.write(f"# MLB Realism Baseline Report\n\n")
        f.write(f"**Generated**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
        f.write(f"**Simulation Version**: Pass 3 Baseline (5/10 passing)\n\n")
        f.write(f"---\n\n")

        f.write(f"## Series Summary\n\n")
        f.write(f"- **Games Simulated**: {series.num_games}\n")
        f.write(f"- **Teams**: {series.away_team_name} vs {series.home_team_name}\n")
        f.write(f"- **Record**: {series.away_team_name} {series.away_wins}-{series.home_wins} {series.home_team_name}\n")
        f.write(f"- **Total Runs**: {series.away_runs + series.home_runs}\n")
        f.write(f"- **Avg Runs/Game**: {(series.away_runs + series.home_runs) / (2 * series.num_games):.2f}\n\n")

        f.write(f"---\n\n")
        f.write(f"## MLB Realism Benchmarks ({passing_count}/{total_count} Passing)\n\n")
        f.write(f"| Status | Metric | Actual | MLB Range | MLB Avg |\n")
        f.write(f"|--------|--------|--------|-----------|----------|\n")

        for check in series.realism_checks:
            emoji = check.get_emoji()
            mlb_range = f"{check.mlb_min:.3f}-{check.mlb_max:.3f}"
            mlb_avg = f"{check.mlb_avg:.3f}" if check.mlb_avg is not None else "N/A"
            f.write(f"| {emoji} | {check.metric_name} | {check.actual_value:.3f} | {mlb_range} | {mlb_avg} |\n")

        f.write(f"\n---\n\n")
        f.write(f"## Detailed Metrics\n\n")
        f.write(f"### Batting\n\n")
        f.write(f"| Metric | Value |\n")
        f.write(f"|--------|-------|\n")
        for key, value in json_data['detailed_metrics']['batting'].items():
            f.write(f"| {key.upper()} | {value:.3f} |\n")

        f.write(f"\n### Pitching\n\n")
        f.write(f"| Metric | Value |\n")
        f.write(f"|--------|-------|\n")
        for key, value in json_data['detailed_metrics']['pitching'].items():
            f.write(f"| {key.upper()} | {value:.3f} |\n")

        if distributions.get('exit_velocity'):
            f.write(f"\n---\n\n")
            f.write(f"## Exit Velocity Distribution\n\n")
            ev_dist = distributions['exit_velocity']
            f.write(f"| Statistic | Value |\n")
            f.write(f"|-----------|-------|\n")
            f.write(f"| Mean | {ev_dist['mean']:.1f} mph |\n")
            f.write(f"| Median | {ev_dist['median']:.1f} mph |\n")
            f.write(f"| Std Dev | {ev_dist['std']:.1f} mph |\n")
            f.write(f"| Min | {ev_dist['min']:.1f} mph |\n")
            f.write(f"| Max | {ev_dist['max']:.1f} mph |\n")
            f.write(f"| 95th percentile | {ev_dist['percentile_95']:.1f} mph |\n")
            f.write(f"| **95+ mph hits** | {ev_dist['count_95plus']} ({ev_dist['percent_95plus']:.1f}%) |\n")
            f.write(f"| **100+ mph hits** | {ev_dist['count_100plus']} ({ev_dist['percent_100plus']:.1f}%) |\n")

        if distributions.get('batted_ball_types'):
            f.write(f"\n---\n\n")
            f.write(f"## Batted Ball Type Distribution\n\n")
            bb_dist = distributions['batted_ball_types']
            f.write(f"| Type | Count | Percentage |\n")
            f.write(f"|------|-------|------------|\n")
            f.write(f"| Ground Balls | {bb_dist['ground_balls']} | {bb_dist['ground_ball_pct']:.1f}% |\n")
            f.write(f"| Line Drives | {bb_dist['line_drives']} | {bb_dist['line_drive_pct']:.1f}% |\n")
            f.write(f"| Fly Balls | {bb_dist['fly_balls']} | {bb_dist['fly_ball_pct']:.1f}% |\n")
            f.write(f"| Pop Ups | {bb_dist['pop_ups']} | {bb_dist['pop_up_pct']:.1f}% |\n")
            f.write(f"\n**MLB Expected**: GB ~45%, LD ~21%, FB ~34%\n")

        if distributions.get('plate_appearance_outcomes'):
            f.write(f"\n---\n\n")
            f.write(f"## Plate Appearance Outcomes\n\n")
            pa_dist = distributions['plate_appearance_outcomes']
            f.write(f"| Outcome | Count | Rate |\n")
            f.write(f"|---------|-------|------|\n")
            f.write(f"| Total PA | {pa_dist['total_pa']} | 100.0% |\n")
            f.write(f"| Strikeouts | {pa_dist['strikeouts']} | {pa_dist['k_rate']*100:.1f}% |\n")
            f.write(f"| Walks | {pa_dist['walks']} | {pa_dist['bb_rate']*100:.1f}% |\n")
            f.write(f"| Balls in Play | {pa_dist['balls_in_play']} | {pa_dist['contact_rate']*100:.1f}% |\n")

        f.write(f"\n---\n\n")
        f.write(f"## Known Issues (Root Causes)\n\n")
        f.write(f"From Pass 4 findings, the following issues are architectural and cannot be fixed with parameter tuning alone:\n\n")
        f.write(f"### 🚨 K% Too Low (Current: ~8%, Target: ~22%)\n")
        f.write(f"- **Root Cause**: Barrel accuracy double-dips (affects both whiff AND contact quality)\n")
        f.write(f"- **Fix Required**: Decouple VISION (whiff) from POWER (contact quality)\n\n")
        f.write(f"### 🚨 BB% Too High (Current: ~17%, Target: ~8-9%)\n")
        f.write(f"- **Root Cause**: Too many intentional balls + K% coupling (longer at-bats → more walks)\n")
        f.write(f"- **Fix Required**: Dynamic pitch control module + umpire model\n\n")
        f.write(f"### 🚨 HR/FB Too Low (Current: ~6%, Target: ~12-15%)\n")
        f.write(f"- **Root Cause**: Single parameter (q) controls both mean EV and EV tail\n")
        f.write(f"- **Fix Required**: Two-parameter power model (EV distribution + launch angle/carry)\n\n")

        f.write(f"---\n\n")
        f.write(f"*Report generated by `research/run_mlb_realism_baseline.py`*\n")

    print(f"📄 Markdown report saved to: {md_path}")


def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(
        description="Run MLB realism baseline simulation and generate comprehensive metrics report."
    )
    parser.add_argument(
        '--games',
        type=int,
        default=20,
        help='Number of games to simulate (default: 20)'
    )
    parser.add_argument(
        '--verbose',
        action='store_true',
        help='Enable verbose game-by-game output'
    )
    parser.add_argument(
        '--output',
        type=str,
        default='baseline',
        help='Base name for output files (default: baseline)'
    )

    args = parser.parse_args()

    # Run simulation
    series = run_baseline_simulation(num_games=args.games, verbose=args.verbose)

    # Analyze distributions
    print("Analyzing distributions...")
    distributions = analyze_distributions(series)

    # Print summary to console
    series.print_summary()

    # Save results
    print(f"\nSaving results...")
    save_results(series, distributions, output_name=args.output)

    print(f"\n{'='*80}")
    print(f"✅ BASELINE METRICS CAPTURE COMPLETE")
    print(f"{'='*80}\n")
    print(f"Next steps:")
    print(f"  1. Review the generated reports in research/results/")
    print(f"  2. Confirm baseline matches known Pass 3 results (5/10 passing)")
    print(f"  3. Begin Phase 1: Instrument subsystems with detailed logging")
    print()


if __name__ == "__main__":
    main()
