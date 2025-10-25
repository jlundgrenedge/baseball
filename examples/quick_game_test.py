"""
Quick Game Simulation Test

A simple script to run a quick game simulation test without user interaction.
Perfect for quick testing and validation.
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from batted_ball import GameSimulator, create_test_team


def quick_test():
    """Run a quick 2-inning test game"""
    print("QUICK GAME SIMULATION TEST")
    print("=" * 40)
    print()
    
    # Create two teams
    away_team = create_test_team("Visitors", "average")
    home_team = create_test_team("Home Team", "good")
    
    print(f"Simulating: {away_team.name} @ {home_team.name}")
    print("Length: 2 innings (for quick testing)")
    print()
    
    # Create and run simulation with less verbose output
    simulator = GameSimulator(away_team, home_team, verbose=False)
    final_state = simulator.simulate_game(num_innings=2)
    
    # Print summary
    print(f"FINAL: {away_team.name} {final_state.away_score} - {final_state.home_score} {home_team.name}")
    print(f"Stats: {final_state.total_hits} hits, {final_state.total_home_runs} HR, {final_state.total_pitches} pitches")
    
    # Show notable plays
    notable_plays = [p for p in simulator.play_by_play if any(word in p.description for word in ['HOME RUN', 'DOUBLE', 'TRIPLE'])]
    if notable_plays:
        print("\nNotable plays:")
        for play in notable_plays:
            physics = play.physics_data
            print(f"  {play.batter_name}: {play.description} - {physics.get('distance_ft', 0):.0f} ft")
    
    print("\n✅ Game simulation test completed successfully!")


if __name__ == "__main__":
    quick_test()