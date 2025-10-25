"""
Full Baseball Game Simulation Demo

This script demonstrates a complete 9-inning baseball game simulation
with detailed physics tracking and realistic gameplay.
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from batted_ball import GameSimulator, create_test_team


def main():
    print("\n" + "="*80)
    print("BASEBALL GAME SIMULATION - Physics-Based Baseball")
    print("="*80)

    # Create two test teams with different quality levels
    print("\nCreating teams...")

    # Away team: "Thunder" - a good team
    thunder = create_test_team("Thunder", team_quality="good")
    print(f"  ⚡ {thunder.name} (Good team)")
    print(f"     Starting pitcher: {thunder.pitchers[0].name}")
    print(f"       - Velocity: {thunder.pitchers[0].velocity}")
    print(f"       - Spin Rate: {thunder.pitchers[0].spin_rate}")
    print(f"       - Command: {thunder.pitchers[0].command}")

    # Home team: "Lightning" - an average team
    lightning = create_test_team("Lightning", team_quality="average")
    print(f"  ⚡ {lightning.name} (Average team)")
    print(f"     Starting pitcher: {lightning.pitchers[0].name}")
    print(f"       - Velocity: {lightning.pitchers[0].velocity}")
    print(f"       - Spin Rate: {lightning.pitchers[0].spin_rate}")
    print(f"       - Command: {lightning.pitchers[0].command}")

    # Create game simulator
    game_sim = GameSimulator(
        away_team=thunder,
        home_team=lightning,
        verbose=True  # Enable detailed play-by-play output
    )

    # Simulate the game (start with 3 innings for testing)
    print("\nStarting game simulation...\n")
    final_state = game_sim.simulate_game(num_innings=3)

    # Print some interesting statistics
    print("\n" + "="*80)
    print("DETAILED GAME STATISTICS")
    print("="*80)

    # Analyze play-by-play for interesting moments
    home_runs = [event for event in game_sim.play_by_play
                 if "HOME RUN" in event.description]

    if home_runs:
        print(f"\n🏆 HOME RUNS ({len(home_runs)}):")
        for hr in home_runs:
            half = "Top" if hr.is_top else "Bot"
            print(f"  {half} {hr.inning}: {hr.batter_name}")
            print(f"    {hr.description}")
            print(f"    Distance: {hr.physics_data['distance_ft']} ft, "
                  f"Exit Velo: {hr.physics_data['exit_velocity_mph']} mph, "
                  f"Launch Angle: {hr.physics_data['launch_angle_deg']}°")

    # Find highest exit velocity
    all_balls_in_play = [event for event in game_sim.play_by_play
                         if 'exit_velocity_mph' in event.physics_data]

    if all_balls_in_play:
        hardest_hit = max(all_balls_in_play,
                         key=lambda e: e.physics_data['exit_velocity_mph'])
        print(f"\n💪 HARDEST HIT BALL:")
        print(f"  {hardest_hit.batter_name}: {hardest_hit.physics_data['exit_velocity_mph']} mph")
        print(f"  Result: {hardest_hit.description}")
        print(f"  Launch Angle: {hardest_hit.physics_data['launch_angle_deg']}°, "
              f"Distance: {hardest_hit.physics_data['distance_ft']} ft")

    # Calculate average exit velocity
    if all_balls_in_play:
        avg_ev = sum(e.physics_data['exit_velocity_mph'] for e in all_balls_in_play) / len(all_balls_in_play)
        print(f"\n📊 AVERAGE EXIT VELOCITY: {avg_ev:.1f} mph")

    # Pitch count by team
    away_pitches = sum(1 for e in game_sim.play_by_play
                       if e.is_top and 'pitches_thrown' in e.physics_data)
    home_pitches = sum(1 for e in game_sim.play_by_play
                       if not e.is_top and 'pitches_thrown' in e.physics_data)

    print(f"\n⚾ PITCH COUNTS:")
    print(f"  {thunder.name}: ~{final_state.total_pitches // 2} pitches")
    print(f"  {lightning.name}: ~{final_state.total_pitches // 2} pitches")

    # Scoring summary by inning
    print(f"\n📋 GAME FLOW:")
    innings_data = {}
    for event in game_sim.play_by_play:
        inning_key = (event.inning, event.is_top)
        if inning_key not in innings_data:
            innings_data[inning_key] = {
                'runs': 0,
                'hits': 0,
                'outs': 0
            }

    # Print inning-by-inning
    for inning in range(1, final_state.inning + 1):
        top_events = [e for e in game_sim.play_by_play
                      if e.inning == inning and e.is_top]
        bot_events = [e for e in game_sim.play_by_play
                      if e.inning == inning and not e.is_top]

        if top_events or bot_events:
            print(f"\n  Inning {inning}:")
            if top_events:
                hits = sum(1 for e in top_events if 'SINGLE' in e.description or
                          'DOUBLE' in e.description or 'TRIPLE' in e.description or
                          'HOME RUN' in e.description)
                print(f"    Top: {len(top_events)} plate appearances, {hits} hit(s)")
            if bot_events:
                hits = sum(1 for e in bot_events if 'SINGLE' in e.description or
                          'DOUBLE' in e.description or 'TRIPLE' in e.description or
                          'HOME RUN' in e.description)
                print(f"    Bot: {len(bot_events)} plate appearances, {hits} hit(s)")

    print("\n" + "="*80)
    print("GAME COMPLETE")
    print("="*80)

    # Determine winner
    if final_state.away_score > final_state.home_score:
        print(f"🏆 {thunder.name} wins {final_state.away_score}-{final_state.home_score}!")
    elif final_state.home_score > final_state.away_score:
        print(f"🏆 {lightning.name} wins {final_state.home_score}-{final_state.away_score}!")
    else:
        print(f"🤝 Game tied {final_state.away_score}-{final_state.away_score}!")

    print("\nDoes this feel like a real baseball game? Let's review:")
    print(f"  ✓ Total pitches: {final_state.total_pitches} (typical: 250-300)")
    print(f"  ✓ Total hits: {final_state.total_hits} (typical: 15-20)")
    print(f"  ✓ Home runs: {final_state.total_home_runs} (typical: 1-3)")
    print(f"  ✓ Final score: {final_state.away_score}-{final_state.home_score} (typical: 3-7 runs)")

    if all_balls_in_play:
        print(f"  ✓ Average exit velocity: {avg_ev:.1f} mph (MLB avg: ~88-90 mph)")

    print("\n")


if __name__ == "__main__":
    main()
