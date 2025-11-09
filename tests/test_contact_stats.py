"""Simple test to understand contact generation and home runs."""
import sys
sys.path.append('.')

from batted_ball.contact import BatBallContact
from batted_ball.player import Hitter, Pitcher
from batted_ball.attributes import create_starter_pitcher, create_power_hitter

# Create power hitter and pitcher
hitter_attr = create_power_hitter()
pitcher_attr = create_starter_pitcher(quality="good")

hitter = Hitter(name="Power Guy", attributes_v2=hitter_attr)
pitcher = Pitcher(name="Ace", attributes_v2=pitcher_attr)

# Create contact simulator
contact = BatBallContact()

# Simulate 100 contacts to see exit velocity distribution
print("Simulating 100 power hitter contacts...")
print("=" * 60)

results = []
for i in range(100):
    result = contact.simulate_contact(
        pitch_speed=95,  # mph
        bat_speed=hitter.attributes_v2.get_bat_speed_mph(),
        pitch_angle=5,  # Slight downward
        bat_angle=hitter.attributes_v2.get_optimal_swing_angle(),
        contact_quality="solid"
    )
    results.append(result)

# Analyze exit velocities
evs = [r['exit_velocity'] for r in results]
las = [r['launch_angle'] for r in results]

print(f"\nExit Velocity Statistics:")
print(f"  Average: {sum(evs)/len(evs):.1f} mph")
print(f"  Max: {max(evs):.1f} mph")
print(f"  Min: {min(evs):.1f} mph")

# Count different ranges
ev_90_plus = sum(1 for ev in evs if ev >= 90)
ev_95_plus = sum(1 for ev in evs if ev >= 95)
ev_100_plus = sum(1 for ev in evs if ev >= 100)
ev_105_plus = sum(1 for ev in evs if ev >= 105)

print(f"\nExit Velocity Distribution:")
print(f"  90+ mph: {ev_90_plus}/100 ({ev_90_plus}%)")
print(f"  95+ mph: {ev_95_plus}/100 ({ev_95_plus}%)")
print(f"  100+ mph: {ev_100_plus}/100 ({ev_100_plus}%)")
print(f"  105+ mph: {ev_105_plus}/100 ({ev_105_plus}%)")

print(f"\nLaunch Angle Statistics:")
print(f"  Average: {sum(las)/len(las):.1f}°")
print(f"  Max: {max(las):.1f}°")
print(f"  Min: {min(las):.1f}°")

# Count optimal HR launch angles (20-35°)
optimal_la = sum(1 for la in las if 20 <= la <= 35)
print(f"  Optimal HR angle (20-35°): {optimal_la}/100 ({optimal_la}%)")

# Estimate home runs
# Need: 95+ mph AND 20-35° launch angle
hr_candidates = sum(1 for r in results if r['exit_velocity'] >= 95 and 20 <= r['launch_angle'] <= 35)
print(f"\n Estimated HR candidates (95+ mph, 20-35° LA): {hr_candidates}/100 ({hr_candidates}%)")

print(f"\nMLB Benchmarks (for reference):")
print(f"  Average exit velocity: ~88-90 mph")
print(f"  Average home run exit velocity: ~103 mph")
print(f"  Average home run launch angle: ~27°")
print(f"  Home run rate on contact: ~2-3%")
