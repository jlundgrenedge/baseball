"""
FAST Three True Outcomes (TTO) Diagnostic - Skips Fielding/Baserunning

This version bypasses PlaySimulator (fielding/baserunning) entirely for 5-10× speedup.
For TTO (K/BB/HR), we only need to know if the ball would clear the fence.

Run with:
    python research/run_tto_diagnostic_fast.py           # Default 20 games (~1000 PA)
    python research/run_tto_diagnostic_fast.py --quick   # Quick 10 games (~500 PA)

Author: Phase 2C Development (TTO Focus)
Date: 2025-11-20
"""

import sys
import os
import time
from collections import defaultdict
import numpy as np

# Add parent directory to path
script_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(script_dir)
if parent_dir not in sys.path:
    sys.path.insert(0, parent_dir)

from batted_ball import create_test_team
from batted_ball.at_bat import AtBatSimulator
from batted_ball.ballpark import get_ballpark


def is_home_run_simple(batted_ball_result, spray_angle_deg, ballpark_name="generic"):
    """
    Quick HR check without full fielding simulation.

    Uses ballpark fence dimensions to determine if ball clears fence.
    """
    if not batted_ball_result:
        return False

    # Get distance and peak height
    distance_ft = batted_ball_result.distance
    peak_height_ft = batted_ball_result.peak_height

    # Get ballpark fence dimensions
    ballpark = get_ballpark(ballpark_name)
    fence_distance, fence_height = ballpark.get_fence_at_angle(spray_angle_deg)

    # Check if ball reached fence distance
    if distance_ft < fence_distance:
        return False

    # Check if ball cleared fence
    # MATCH LOGIC FROM play_simulation.py (after fence fix)
    is_home_run = False
    if distance_ft >= fence_distance:
        # Get the ball's height when it crosses the fence distance
        height_at_fence = None
        try:
            height_at_fence = batted_ball_result.get_height_at_distance(fence_distance)
        except:
            pass

        if height_at_fence is not None and height_at_fence > fence_height:
            # Ball was above fence height when it crossed the fence distance
            is_home_run = True
        elif distance_ft >= fence_distance + 30:  # 30+ ft past fence = definite HR
            # Ball landed well beyond fence (even if low trajectory)
            is_home_run = True

    return is_home_run


def run_tto_diagnostic_fast(num_games=20, verbose=False):
    """
    Fast TTO diagnostic that skips fielding/baserunning simulation.

    Only simulates K/BB/HR - ignores other hit outcomes.
    5-10× faster than full game simulation.
    """
    print(f"\n{'='*80}")
    print(f"FAST Three True Outcomes (TTO) Diagnostic - Phase 2C")
    print(f"{'='*80}")
    print(f"Sample size: {num_games} games (~{num_games * 50} PA expected)")
    print(f"Mode: FAST (skips fielding/baserunning for 5-10× speedup)")
    print(f"Focus: K%, BB%, HR% only")
    print(f"{'='*80}\n")

    start_time = time.time()

    # Create test teams (average quality)
    away_team = create_test_team("Away", "average")
    home_team = create_test_team("Home", "average")

    # Track three true outcomes
    total_strikeouts = 0
    total_walks = 0
    total_home_runs = 0
    total_pa = 0
    total_in_play = 0

    # Track HR details for debugging
    hr_details = []

    # Approximate hit count (for HR% of hits calculation)
    # We don't simulate full plays, so we estimate hits from in_play - outs
    # Rough estimate: ~30% of BIP become hits (MLB BABIP)
    estimated_hits = 0

    print(f"Simulating {num_games} games (fast mode - no fielding)...")

    # Simulate multiple games worth of plate appearances
    target_pa = num_games * 50  # ~50 PA per game on average

    pitcher_idx = 0
    batter_idx = 0

    for pa_num in range(target_pa):
        # Alternate pitcher/batter selection
        if pa_num % 2 == 0:
            pitcher = away_team.pitchers[pitcher_idx % len(away_team.pitchers)]
            hitter = home_team.hitters[batter_idx % len(home_team.hitters)]
        else:
            pitcher = home_team.pitchers[pitcher_idx % len(home_team.pitchers)]
            hitter = away_team.hitters[batter_idx % len(away_team.hitters)]

        # Simulate at-bat
        sim = AtBatSimulator(pitcher=pitcher, hitter=hitter, fast_mode=True)
        result = sim.simulate_at_bat()

        total_pa += 1
        outcome = result.outcome

        # Track outcomes
        if outcome == 'strikeout':
            total_strikeouts += 1
        elif outcome == 'walk':
            total_walks += 1
        elif outcome == 'in_play':
            total_in_play += 1

            # Check if it's a home run (skip full fielding simulation)
            if result.batted_ball_result:
                bb_result = result.batted_ball_result.get('trajectory')
                spray_angle = result.batted_ball_result.get('spray_angle', 0.0)
                exit_velo = result.batted_ball_result.get('exit_velocity', 0.0)
                launch_angle = result.batted_ball_result.get('launch_angle', 0.0)

                if bb_result and is_home_run_simple(bb_result, spray_angle):
                    total_home_runs += 1
                    estimated_hits += 1  # HR counts as hit

                    # Log HR details for debugging
                    from batted_ball.ballpark import get_ballpark
                    ballpark = get_ballpark('generic')
                    fence_dist, fence_height = ballpark.get_fence_at_angle(spray_angle)

                    try:
                        height_at_fence = bb_result.get_height_at_distance(fence_dist)
                    except:
                        height_at_fence = None

                    hr_details.append({
                        'exit_velo': exit_velo,
                        'launch_angle': launch_angle,
                        'spray_angle': spray_angle,
                        'distance': bb_result.distance,
                        'peak_height': bb_result.peak_height,
                        'fence_distance': fence_dist,
                        'fence_height': fence_height,
                        'height_at_fence': height_at_fence,
                        'hitter': hitter.name
                    })
                else:
                    # Estimate non-HR hits using BABIP ~0.300
                    if np.random.random() < 0.30:
                        estimated_hits += 1

        # Rotate batters every PA, pitchers every 20 PA
        batter_idx += 1
        if pa_num % 20 == 0:
            pitcher_idx += 1

    elapsed = time.time() - start_time

    # Calculate percentages
    k_pct = (total_strikeouts / total_pa * 100) if total_pa > 0 else 0
    bb_pct = (total_walks / total_pa * 100) if total_pa > 0 else 0
    hr_pct = (total_home_runs / total_pa * 100) if total_pa > 0 else 0
    hr_per_hit_pct = (total_home_runs / estimated_hits * 100) if estimated_hits > 0 else 0

    # Print results
    print(f"\n{'='*80}")
    print(f"FAST TTO RESULTS")
    print(f"{'='*80}\n")

    print(f"Sample Statistics:")
    print(f"  Total PA: {total_pa}")
    print(f"  Estimated hits: {estimated_hits} (using BABIP ~0.30)")
    print(f"  In play: {total_in_play}")
    print()

    print(f"Three True Outcomes:")
    print(f"  Strikeouts: {total_strikeouts} ({k_pct:.1f}% of PA)")
    print(f"  Walks: {total_walks} ({bb_pct:.1f}% of PA)")
    print(f"  Home Runs: {total_home_runs} ({hr_pct:.1f}% of PA, {hr_per_hit_pct:.1f}% of hits)")
    print()

    # MLB realism check
    print(f"MLB Realism Check:")

    # K% check (target: 22%)
    k_status = "✅" if 20 <= k_pct <= 25 else "⚠️"
    print(f"  {k_status} K%: {k_pct:.1f}% (Phase 2A target: ~22%)")

    # BB% check (target: 8-9%)
    bb_status = "✅" if 7 <= bb_pct <= 10 else "⚠️"
    print(f"  {bb_status} BB%: {bb_pct:.1f}% (Phase 2B target: 8-9%)")

    # HR% check (target: 3-4% of PA, or 10-13% of hits)
    hr_pa_status = "✅" if 2.5 <= hr_pct <= 4.5 else "⚠️"
    hr_hit_status = "✅" if 10 <= hr_per_hit_pct <= 13 else "⚠️"
    print(f"  {hr_pa_status} HR% (PA): {hr_pct:.1f}% (MLB target: 3-4% of PA)")
    print(f"  {hr_hit_status} HR% (Hits): {hr_per_hit_pct:.1f}% (MLB target: 10-13% of hits)")
    print()

    # Performance
    print(f"Performance:")
    print(f"  Total time: {elapsed:.1f}s")
    print(f"  Rate: {total_pa/elapsed:.1f} PA/sec (vs ~4 PA/sec in full mode)")
    print(f"  Speedup: ~{(total_pa/elapsed)/4.0:.1f}× faster")
    print(f"{'='*80}\n")

    # Print HR details for debugging
    if hr_details:
        print(f"HOME RUN DETAILS (Total: {len(hr_details)}):")
        print(f"{'='*80}")
        for i, hr in enumerate(hr_details, 1):
            print(f"\nHR #{i}: {hr['hitter']}")
            print(f"  Exit Velocity: {hr['exit_velo']:.1f} mph")
            print(f"  Launch Angle: {hr['launch_angle']:.1f}°")
            print(f"  Spray Angle: {hr['spray_angle']:.1f}°")
            print(f"  Distance: {hr['distance']:.1f} ft")
            print(f"  Peak Height: {hr['peak_height']:.1f} ft")
            print(f"  Fence Distance: {hr['fence_distance']:.1f} ft")
            print(f"  Fence Height: {hr['fence_height']:.1f} ft")
            if hr['height_at_fence'] is not None:
                print(f"  Height at Fence: {hr['height_at_fence']:.1f} ft (cleared by {hr['height_at_fence'] - hr['fence_height']:.1f} ft)")
            else:
                print(f"  Height at Fence: None (line drive well past fence)")
        print(f"\n{'='*80}\n")
    else:
        print(f"NO HOME RUNS HIT IN THIS SAMPLE")
        print(f"{'='*80}\n")

    # Return results
    return {
        'total_pa': total_pa,
        'estimated_hits': estimated_hits,
        'strikeouts': total_strikeouts,
        'walks': total_walks,
        'home_runs': total_home_runs,
        'k_pct': k_pct,
        'bb_pct': bb_pct,
        'hr_pct': hr_pct,
        'hr_per_hit_pct': hr_per_hit_pct
    }


if __name__ == "__main__":
    # Parse command line arguments
    if len(sys.argv) > 1:
        if sys.argv[1] == "--quick":
            print("Running QUICK diagnostic (10 games, ~500 PA)...")
            run_tto_diagnostic_fast(num_games=10)
        else:
            print(f"Unknown option: {sys.argv[1]}")
            print("Usage:")
            print("  python research/run_tto_diagnostic_fast.py           # Default 20 games (~1000 PA)")
            print("  python research/run_tto_diagnostic_fast.py --quick   # Quick 10 games (~500 PA)")
    else:
        # Default: 20 games
        run_tto_diagnostic_fast(num_games=20)
