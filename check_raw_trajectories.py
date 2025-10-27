"""Directly check trajectory landing positions."""
from batted_ball.at_bat import AtBatSimulator
from batted_ball.player import Pitcher, Hitter

# Create pitcher and hitter using proper constructor
pitcher = Pitcher(name="Test Pitcher", velocity=95.0, spin_rate=2400, command=50)
hitter = Hitter(name="Test Hitter", bat_speed=75, swing_path_angle=15, contact_quality=50)

# Simulate a few at-bats
sim = AtBatSimulator(pitcher, hitter)

print("CHECKING TRAJECTORY LANDING POSITIONS")
print("=" * 80)

for i in range(20):
    result = sim.simulate_at_bat()
    
    if result.batted_ball_result and 'trajectory' in result.batted_ball_result:
        traj = result.batted_ball_result['trajectory']
        
        print(f"\n#{i+1}:")
        print(f"  Launch angle: {traj.launch_angle:.1f}°")
        print(f"  landing_x: {traj.landing_x:.1f}ft")
        print(f"  landing_y: {traj.landing_y:.1f}ft")
        print(f"  Distance: {traj.distance:.1f}ft")
        print(f"  Spray angle: {traj.spray_angle_landing:.1f}°")
        
        if abs(traj.landing_y) < 1.0:
            print(f"  ⚠️ WARNING: y-coordinate is nearly zero!")
