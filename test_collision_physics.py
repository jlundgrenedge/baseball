"""
Test the new research-based collision physics implementation.
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__)))

from batted_ball.contact import ContactModel
from batted_ball.player import Pitcher, Hitter
from batted_ball.at_bat import AtBatSimulator
import numpy as np

def test_collision_efficiency():
    """Test the collision efficiency calculation for different bat types."""
    print("\n=== Testing Collision Efficiency Calculation ===")
    
    # Test different bat types
    bat_types = ['wood', 'aluminum', 'composite']
    
    for bat_type in bat_types:
        print(f"\n{bat_type.upper()} BAT:")
        contact_model = ContactModel(bat_type=bat_type)
        
        # Test perfect contact
        q_perfect = contact_model.calculate_collision_efficiency(0.0, 0.0)
        print(f"  Perfect contact efficiency (q): {q_perfect:.3f}")
        
        # Test off-center contact
        q_off_center = contact_model.calculate_collision_efficiency(2.0, 1.5)
        print(f"  Off-center contact efficiency (q): {q_off_center:.3f}")
        
        # Test master formula with typical values
        bat_speed = 70  # mph
        pitch_speed = 92  # mph
        
        exit_vel_perfect = contact_model.calculate_exit_velocity_master_formula(
            bat_speed, pitch_speed, q_perfect
        )
        exit_vel_off = contact_model.calculate_exit_velocity_master_formula(
            bat_speed, pitch_speed, q_off_center
        )
        
        print(f"  Exit velocity (perfect): {exit_vel_perfect:.1f} mph")
        print(f"  Exit velocity (off-center): {exit_vel_off:.1f} mph")
        print(f"  Performance difference: {exit_vel_perfect - exit_vel_off:.1f} mph")

def test_full_collision_scenarios():
    """Test full collision scenarios with the new physics."""
    print("\n=== Testing Full Collision Scenarios ===")
    
    contact_model = ContactModel(bat_type='wood')
    
    scenarios = [
        {
            'name': 'Perfect Sweet Spot Contact',
            'bat_speed': 75,
            'pitch_speed': 94,
            'vertical_offset': 0.0,
            'horizontal_offset': 0.0,
            'sweet_spot_distance': 0.0
        },
        {
            'name': 'Slightly Below Center (Backspin)',
            'bat_speed': 75,
            'pitch_speed': 94,
            'vertical_offset': 0.5,  # Half inch below center
            'horizontal_offset': 0.0,
            'sweet_spot_distance': 0.0
        },
        {
            'name': 'Off Sweet Spot + Off Center',
            'bat_speed': 75,
            'pitch_speed': 94,
            'vertical_offset': 0.3,
            'horizontal_offset': 1.0,  # One inch horizontal offset
            'sweet_spot_distance': 2.0  # Two inches from sweet spot
        },
        {
            'name': 'Jammed (Far from Sweet Spot)',
            'bat_speed': 65,  # Slower bat speed when jammed
            'pitch_speed': 94,
            'vertical_offset': 0.0,
            'horizontal_offset': 0.5,
            'sweet_spot_distance': 4.0  # Four inches from sweet spot
        }
    ]
    
    for scenario in scenarios:
        print(f"\n{scenario['name']}:")
        result = contact_model.full_collision(
            bat_speed_mph=scenario['bat_speed'],
            pitch_speed_mph=scenario['pitch_speed'],
            bat_path_angle_deg=10.0,  # Typical upward bat path
            vertical_contact_offset_inches=scenario['vertical_offset'],
            horizontal_contact_offset_inches=scenario['horizontal_offset'],
            distance_from_sweet_spot_inches=scenario['sweet_spot_distance']
        )
        
        print(f"  Exit Velocity: {result['exit_velocity']:.1f} mph")
        print(f"  Launch Angle: {result['launch_angle']:.1f}°")
        print(f"  Backspin: {result['backspin_rpm']:.0f} rpm")
        print(f"  Sidespin: {result['sidespin_rpm']:.0f} rpm")
        print(f"  Collision Efficiency (q): {result['collision_efficiency_q']:.3f}")
        print(f"  Contact Offset Total: {result['contact_offset_total']:.2f} inches")

def test_at_bat_integration():
    """Test how the new collision physics affects at-bat outcomes."""
    print("\n=== Testing At-Bat Integration ===")
    
    # Create players
    pitcher = Pitcher("Research Test Pitcher", velocity=85, command=75, stamina=80)
    hitter = Hitter("Research Test Hitter", 
                   bat_speed=75, 
                   barrel_accuracy=80, 
                   zone_discipline=70, 
                   exit_velocity_ceiling=75)
    
    # Run some at-bats
    simulator = AtBatSimulator(pitcher, hitter)
    
    print("Running 5 at-bats with new collision physics...")
    results = []
    
    for i in range(5):
        result = simulator.simulate_at_bat()
        results.append(result)
        
        print(f"\nAt-Bat {i+1}: {result.outcome}")
        if hasattr(result, 'batted_ball') and result.batted_ball:
            bb = result.batted_ball
            print(f"  Exit Velocity: {bb.exit_velocity:.1f} mph")
            print(f"  Launch Angle: {bb.launch_angle:.1f}°")
            print(f"  Distance: {bb.distance_feet:.0f} ft")
            if hasattr(bb, 'collision_efficiency_q'):
                print(f"  Collision Efficiency: {bb.collision_efficiency_q:.3f}")

if __name__ == "__main__":
    print("Testing New Research-Based Collision Physics")
    print("=" * 50)
    
    test_collision_efficiency()
    test_full_collision_scenarios()
    test_at_bat_integration()
    
    print("\n" + "=" * 50)
    print("Collision Physics Testing Complete!")