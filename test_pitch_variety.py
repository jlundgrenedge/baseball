#!/usr/bin/env python3
"""
Test script to verify that pitchers are using multiple pitch types
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from batted_ball import GameSimulator, create_test_team

def test_pitch_variety():
    """Run a single inning and count pitch types used"""
    print("TESTING PITCH VARIETY")
    print("=" * 60)
    print()

    # Create two teams
    visitors = create_test_team("Visitors", "average")
    home = create_test_team("Home", "good")

    print()
    print("Starting game simulation...")
    print()

    # Create game simulator with verbose output to see pitch details
    simulator = GameSimulator(visitors, home, verbose=True)

    # Simulate just 1 inning to see pitch variety
    final_state = simulator.simulate_game(num_innings=1)

    print()
    print("=" * 60)
    print("PITCH TYPE ANALYSIS")
    print("=" * 60)

    # Count pitch types from play-by-play
    pitch_types = {}
    for event in simulator.play_by_play:
        if hasattr(event, 'pitch_data') and event.pitch_data:
            for pitch in event.pitch_data:
                pitch_type = pitch.get('type', 'unknown')
                pitch_types[pitch_type] = pitch_types.get(pitch_type, 0) + 1

    if pitch_types:
        print(f"\nPitch types used:")
        for pitch_type, count in sorted(pitch_types.items()):
            print(f"  {pitch_type}: {count}")
        print(f"\nTotal unique pitch types: {len(pitch_types)}")

        if len(pitch_types) > 1:
            print("\n✅ SUCCESS: Multiple pitch types are being used!")
        else:
            print("\n⚠️  WARNING: Only one pitch type detected")
    else:
        print("\n⚠️  WARNING: No pitch data found in play-by-play events")

    print(f"\nFinal Score: {visitors.name} {final_state.away_score} - {final_state.home_score} {home.name}")

if __name__ == "__main__":
    test_pitch_variety()
