"""Test to verify catchers don't field ground balls going away from home plate."""
import sys
sys.path.append('.')

from batted_ball import GameSimulator, create_test_team

print("Testing catcher fielding fix...")
print("=" * 70)

# Create two average teams
away_team = create_test_team("Test Away", "average")
home_team = create_test_team("Test Home", "average")

# Create and run simulation with verbose output
simulator = GameSimulator(away_team, home_team, verbose=True)
final_state = simulator.simulate_game(num_innings=2)

print("\n" + "=" * 70)
print("Checking for catcher fielding on ground balls...")
print("=" * 70)

# Check the enhanced game log for catcher fielding issues
catcher_fielding_count = 0
weak_hit_count = 0
for play in simulator.play_by_play:
    # Check if this is a weak hit that was fielded
    if hasattr(play, 'events'):
        has_weak_hit = False
        has_catcher_fielding = False
        ball_position = None

        for event in play.events:
            if event.event_type == "weak_hit":
                has_weak_hit = True
            if "fielded by catcher" in event.description.lower():
                has_catcher_fielding = True
            if event.event_type == "ground_ball_analysis":
                # Extract ball position from description
                # Format: "Ground ball coordinates: (x, y) ft, distance d ft from home"
                if "coordinates:" in event.description:
                    try:
                        coords_part = event.description.split("coordinates:")[1].split("ft,")[0]
                        coords = coords_part.strip().strip("()").split(",")
                        x = float(coords[0])
                        y = float(coords[1])
                        ball_position = (x, y)
                    except:
                        pass

        if has_weak_hit and has_catcher_fielding:
            weak_hit_count += 1
            catcher_fielding_count += 1

            if ball_position:
                x, y = ball_position
                print(f"\n⚠️  Found catcher fielding weak hit:")
                print(f"   Ball position: ({x:.1f}, {y:.1f}) ft")
                print(f"   Y-coordinate (forward): {y:.1f} ft")

                # Check if ball is in front of home plate (y > 5.0)
                if y > 5.0:
                    print(f"   ❌ ERROR: Ball is {y:.1f} ft in FRONT of home plate!")
                    print(f"   Catcher should NOT field this ball!")
                else:
                    print(f"   ✓ OK: Ball is close to home plate (y <= 5.0)")

print("\n" + "=" * 70)
print(f"Summary:")
print(f"  Total weak hits: {weak_hit_count}")
print(f"  Catchers fielding weak hits: {catcher_fielding_count}")
print(f"\nFINAL SCORE: {away_team.name} {final_state.away_score} - {final_state.home_score} {home_team.name}")
print("=" * 70)
