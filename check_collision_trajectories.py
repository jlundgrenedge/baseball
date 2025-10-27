"""Check trajectory landing positions by simulating collisions directly."""
from batted_ball.contact import simulate_collision_fast
from batted_ball.environment import Environment
import numpy as np

env = Environment()

print("TRAJECTORY LANDING POSITIONS FROM DIRECT COLLISION SIMULATION")
print("=" * 80)

for i in range(20):
    # Typical contact parameters
    pitch_velocity = np.array([0.0, -40.0, 0.0])  # Coming from mound
    bat_velocity = np.array([0.0, 30.0, 10.0])  # Swing
    bat_angle_deg = 15.0  # Uppercut
    
    # Simulate
    result = simulate_collision_fast(
        pitch_velocity, 
        bat_velocity, 
        bat_angle_deg,
        backspin_rpm=2000,
        env=env
    )
    
    traj = result['trajectory']
    
    print(f"\n#{i+1}:")
    print(f"  Launch angle: {traj.launch_angle:.1f}°")
    print(f"  landing_x: {traj.landing_x:.1f}ft")
    print(f"  landing_y: {traj.landing_y:.1f}ft")
    print(f"  Distance: {traj.distance:.1f}ft")
    
    if abs(traj.landing_y) < 5.0:
        print(f"  ⚠️  y-coordinate is very small (nearly on foul line)!")
