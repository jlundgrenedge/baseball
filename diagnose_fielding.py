"""
Diagnostic script to analyze ball landing positions vs fielder positions.

This helps identify why fielders are not catching balls.
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__)))

from batted_ball import GameSimulator, create_test_team
import numpy as np

def main():
    print("\n" + "="*80)
    print("FIELDING DIAGNOSTIC - Ball Trajectories vs Defensive Positioning")
    print("="*80)

    # Create teams
    thunder = create_test_team("Thunder", team_quality="average")
    lightning = create_test_team("Lightning", team_quality="average")

    # Create game simulator
    game_sim = GameSimulator(
        away_team=thunder,
        home_team=lightning,
        verbose=False  # Quiet mode for analysis
    )

    # Simulate 3 innings to collect more data
    print("\nSimulating 3 innings to collect ball trajectory data...")
    final_state = game_sim.simulate_game(num_innings=3)

    # Analyze all balls in play - use different field names
    balls_in_play = [event for event in game_sim.play_by_play
                     if 'distance_ft' in event.physics_data]  # Balls that were hit

    print(f"\nTotal balls in play: {len(balls_in_play)}")
    print(f"Total hits: {final_state.total_hits}")
    if len(balls_in_play) > 0:
        outs = len([e for e in balls_in_play if 'out' in e.description.lower() or 'OUT' in e.description])
        print(f"Outs from balls in play: {outs}")
        print("\nSample ball in play physics_data keys:", list(balls_in_play[0].physics_data.keys()))

    # Fielder standard positions
    fielder_positions = {
        'P': (0, 60.5),
        'C': (0, 0),
        '1B': (90, 90),
        '2B': (45, 110),
        'SS': (-45, 110),
        '3B': (-90, 90),
        'LF': (-135, 234),
        'CF': (0, 290),
        'RF': (135, 234)
    }

    # Analyze play results
    landing_data = []
    for event in balls_in_play:
        distance = event.physics_data.get('distance_ft', 0)
        ev = event.physics_data.get('exit_velocity_mph', 0)
        la = event.physics_data.get('launch_angle_deg', 0)
        hang_time = event.physics_data.get('hang_time_sec', 0)

        is_hit = 'SINGLE' in event.description or 'DOUBLE' in event.description or \
                 'TRIPLE' in event.description or 'HOME RUN' in event.description

        landing_data.append({
            'distance': distance,
            'ev': ev,
            'la': la,
            'hang_time': hang_time,
            'is_hit': is_hit,
            'result': event.description
        })

    # Print statistics
    print("\n" + "="*80)
    print("LANDING POSITION STATISTICS")
    print("="*80)

    # Group by distance ranges
    distance_ranges = [
        (0, 100, "Infield (<100ft)"),
        (100, 200, "Shallow OF (100-200ft)"),
        (200, 300, "Mid OF (200-300ft)"),
        (300, 400, "Deep OF (300-400ft)"),
        (400, 1000, "Very Deep (>400ft)")
    ]

    for min_d, max_d, label in distance_ranges:
        balls_in_range = [d for d in landing_data if min_d <= d['distance'] < max_d]
        if balls_in_range:
            hits = sum(1 for d in balls_in_range if d['is_hit'])
            avg_ev = np.mean([d['ev'] for d in balls_in_range])
            avg_la = np.mean([d['la'] for d in balls_in_range])
            avg_hang_time = np.mean([d['hang_time'] for d in balls_in_range])

            print(f"\n{label}:")
            print(f"  Balls: {len(balls_in_range)}")
            print(f"  Hits: {hits} ({hits/len(balls_in_range)*100:.1f}%)")
            print(f"  Avg EV: {avg_ev:.1f}mph, Avg LA: {avg_la:.1f}°")
            print(f"  Avg hang time: {avg_hang_time:.2f}s")

    # Launch angle analysis
    print("\n" + "="*80)
    print("LAUNCH ANGLE vs HIT RATE")
    print("="*80)

    la_ranges = [
        (-90, 0, "Ground balls (<0°)"),
        (0, 10, "Low liners (0-10°)"),
        (10, 25, "Line drives (10-25°)"),
        (25, 50, "Fly balls (25-50°)"),
        (50, 90, "Pop ups (>50°)")
    ]

    for min_la, max_la, label in la_ranges:
        balls_in_range = [d for d in landing_data if min_la <= d['la'] < max_la]
        if balls_in_range:
            hits = sum(1 for d in balls_in_range if d['is_hit'])
            avg_dist = np.mean([d['distance'] for d in balls_in_range])
            avg_hang = np.mean([d['hang_time'] for d in balls_in_range])

            print(f"\n{label}:")
            print(f"  Balls: {len(balls_in_range)}")
            print(f"  Hits: {hits} ({hits/len(balls_in_range)*100:.1f}%)")
            print(f"  Avg distance: {avg_dist:.1f}ft, Avg hang time: {avg_hang:.2f}s")

    # Calculate coverage capability
    print("\n" + "="*80)
    print("FIELDER COVERAGE ANALYSIS")
    print("="*80)

    print("\nOutfielder positions:")
    print(f"  LF: 234ft deep")
    print(f"  CF: 290ft deep")
    print(f"  RF: 234ft deep")

    # For balls beyond fielder depth, check if fielders had enough time
    deep_balls = [d for d in landing_data if d['distance'] > 300]
    if deep_balls:
        print(f"\nBalls beyond 300ft: {len(deep_balls)}")
        print(f"  Hit rate: {sum(1 for d in deep_balls if d['is_hit'])}/{len(deep_balls)} ({sum(1 for d in deep_balls if d['is_hit'])/len(deep_balls)*100:.1f}%)")

        for ball in deep_balls:
            extra_distance = ball['distance'] - 290  # Distance beyond CF
            speed_needed = extra_distance / ball['hang_time']
            print(f"  {ball['distance']:.0f}ft ball ({ball['hang_time']:.2f}s hang): "
                  f"needs {extra_distance:.0f}ft coverage, {speed_needed:.1f} ft/s required - "
                  f"{'HIT' if ball['is_hit'] else 'OUT'}")

    print("\nFielder max speeds: ~28 ft/s")
    print("With 3s hang time, fielder can cover: ~84ft from starting position")
    print("With 4s hang time, fielder can cover: ~112ft from starting position")

    print("\n" + "="*80)

if __name__ == "__main__":
    main()
