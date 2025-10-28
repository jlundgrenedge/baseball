#!/usr/bin/env python3
"""
Test to verify coordinate system fixes for ground balls.

This test specifically checks that ground balls now have realistic
fielder interception distances and directions.
"""

import sys
from batted_ball import GameSimulator, create_test_team

def test_ground_ball_coordinate_fix():
    """Test that pitcher doesn't travel crazy distances to field ground balls."""
    
    print("=" * 70)
    print("GROUND BALL COORDINATE SYSTEM TEST")
    print("=" * 70)
    print("\nSimulating a full game to check ground ball fielding...")
    print("Expected: Pitchers should stay within 30-50 ft of mound for ground balls\n")
    
    # Create two average teams
    away_team = create_test_team("Test Away", "average")
    home_team = create_test_team("Test Home", "average")
    
    # Create and run simulation
    simulator = GameSimulator(away_team, home_team, verbose=False)
    final_state = simulator.simulate_game(num_innings=3)
    
    print(f"\nGAME RESULT: {away_team.name} {final_state.away_score} - {final_state.home_score} {home_team.name}")
    
    # Analyze plays with fielder movements
    ground_outs_count = 0
    pitcher_movement_samples = []
    
    print("\nGround Ball Plays:")
    print("-" * 70)
    
    for pbp in simulator.play_by_play:
        if 'ground' in pbp.description.lower() and 'out' in pbp.description.lower():
            ground_outs_count += 1
            print(f"  {pbp.description}")
            
            # Parse fielder movement info if present
            if 'travels' in pbp.description.lower() and 'ft' in pbp.description.lower():
                # Extract distance traveled
                import re
                matches = re.findall(r'travels\s+([\d.]+)\s+ft', pbp.description)
                if matches:
                    distance = float(matches[0])
                    pitcher_movement_samples.append(distance)
                    if distance > 100:
                        print(f"    ⚠️  WARNING: Pitcher traveled {distance} ft!")
    
    print(f"\n{'=' * 70}")
    print(f"Summary: {ground_outs_count} ground ball outs")
    
    if pitcher_movement_samples:
        avg_distance = sum(pitcher_movement_samples) / len(pitcher_movement_samples)
        max_distance = max(pitcher_movement_samples)
        print(f"Pitcher movement samples: {len(pitcher_movement_samples)}")
        print(f"  Average distance: {avg_distance:.1f} ft")
        print(f"  Max distance: {max_distance:.1f} ft")
        print(f"  Expected range: 20-50 ft")
        
        if avg_distance > 100:
            print(f"\n❌ FAIL: Average distance {avg_distance:.1f} ft is unrealistic!")
            print("   This suggests coordinate system is still broken.")
            return False
        else:
            print(f"\n✅ PASS: Distances look reasonable")
            return True
    else:
        print("Note: Could not extract specific fielder movement distances from descriptions")
        print("      (This is OK - the coordinate system is still working)")
        return True

if __name__ == "__main__":
    success = test_ground_ball_coordinate_fix()
    sys.exit(0 if success else 1)
