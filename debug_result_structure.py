"""
Quick test to see what data structure is returned by at-bat simulation.
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__)))

from batted_ball.at_bat import AtBatSimulator
from batted_ball.player import Pitcher, Hitter

def inspect_at_bat_result():
    """Inspect the structure of at-bat results."""
    print("=== Inspecting At-Bat Result Structure ===")
    
    pitcher = Pitcher("Test Pitcher", velocity=85, command=75, stamina=80)
    hitter = Hitter("Test Hitter", 
                   bat_speed=75, 
                   barrel_accuracy=80, 
                   zone_discipline=70, 
                   exit_velocity_ceiling=75)
    
    simulator = AtBatSimulator(pitcher, hitter)
    
    # Run a few at-bats until we get contact
    for i in range(10):
        result = simulator.simulate_at_bat()
        print(f"\nAt-bat {i+1}:")
        print(f"  Outcome: {result.outcome}")
        print(f"  Has batted_ball_result: {hasattr(result, 'batted_ball_result')}")
        
        if hasattr(result, 'batted_ball_result') and result.batted_ball_result:
            bb = result.batted_ball_result
            print(f"  batted_ball_result type: {type(bb)}")
            if isinstance(bb, dict):
                print(f"  batted_ball_result keys: {list(bb.keys())}")
                if 'trajectory' in bb:
                    traj = bb['trajectory']
                    print(f"  trajectory type: {type(traj)}")
                    print(f"  exit_velocity: {bb.get('exit_velocity', 'not found')}")
                    print(f"  launch_angle: {bb.get('launch_angle', 'not found')}")
                    print(f"  distance: {bb.get('distance', 'not found')}")
                    
                    # Check trajectory properties
                    if hasattr(traj, 'exit_velocity'):
                        print(f"  trajectory.exit_velocity: {traj.exit_velocity}")
                    if hasattr(traj, 'distance'):
                        print(f"  trajectory.distance: {traj.distance}")
            else:
                print(f"  batted_ball_result attributes: {dir(bb)}")
            break

if __name__ == "__main__":
    inspect_at_bat_result()