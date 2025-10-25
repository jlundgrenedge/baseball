"""
Comprehensive test of the new collision physics with detailed analysis.
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__)))

from batted_ball.at_bat import AtBatSimulator
from batted_ball.player import Pitcher, Hitter

def test_realistic_collision_scenarios():
    """Test realistic collision scenarios and compare to MLB data."""
    print("\n=== Comprehensive Collision Physics Test ===")
    
    # Create typical MLB pitcher and hitter
    pitcher = Pitcher("MLB Pitcher", velocity=92, command=70, stamina=80)
    hitter = Hitter("MLB Hitter", 
                   bat_speed=75,          # Typical MLB bat speed 
                   barrel_accuracy=75,    # Good contact ability
                   zone_discipline=70,    # Decent plate discipline
                   exit_velocity_ceiling=80)  # Good power
    
    simulator = AtBatSimulator(pitcher, hitter)
    
    # Run 50 at-bats to get statistical sample
    print("Running 50 at-bats with new collision physics...")
    
    results = []
    contact_results = []
    
    for i in range(50):
        result = simulator.simulate_at_bat()
        results.append(result)
        
        if hasattr(result, 'batted_ball_result') and result.batted_ball_result:
            contact_results.append(result.batted_ball_result)
    
    # Analyze results
    analyze_collision_results(contact_results)
    analyze_outcome_distribution(results)

def analyze_collision_results(contact_results):
    """Analyze the collision physics results."""
    if not contact_results:
        print("No contact results to analyze")
        return
        
    print(f"\n=== Contact Analysis ({len(contact_results)} contacts) ===")
    
    # Exit velocity analysis
    exit_vels = [r['exit_velocity'] for r in contact_results]
    avg_exit_vel = sum(exit_vels) / len(exit_vels)
    max_exit_vel = max(exit_vels)
    min_exit_vel = min(exit_vels)
    
    print(f"Exit Velocity:")
    print(f"  Average: {avg_exit_vel:.1f} mph")
    print(f"  Range: {min_exit_vel:.1f} - {max_exit_vel:.1f} mph")
    
    # Launch angle analysis
    launch_angles = [r['launch_angle'] for r in contact_results]
    avg_launch = sum(launch_angles) / len(launch_angles)
    
    print(f"Launch Angle:")
    print(f"  Average: {avg_launch:.1f}°")
    
    # Distance analysis
    distances = [r['distance'] for r in contact_results]
    avg_distance = sum(distances) / len(distances)
    max_distance = max(distances)
    
    print(f"Distance:")
    print(f"  Average: {avg_distance:.0f} ft")
    print(f"  Maximum: {max_distance:.0f} ft")
    
    # Quality breakdown
    hard_hit = len([v for v in exit_vels if v >= 95])  # Hard hit (95+ mph)
    medium_hit = len([v for v in exit_vels if 80 <= v < 95])  # Medium (80-94 mph)
    weak_hit = len([v for v in exit_vels if v < 80])  # Weak (<80 mph)
    
    print(f"Contact Quality:")
    print(f"  Hard Hit (95+ mph): {hard_hit} ({hard_hit/len(exit_vels)*100:.1f}%)")
    print(f"  Medium Hit (80-94 mph): {medium_hit} ({medium_hit/len(exit_vels)*100:.1f}%)")
    print(f"  Weak Hit (<80 mph): {weak_hit} ({weak_hit/len(exit_vels)*100:.1f}%)")
    
    # Collision efficiency analysis
    efficiencies = [r.get('collision_efficiency_q') for r in contact_results]
    if any(e is not None for e in efficiencies):
        valid_efficiencies = [e for e in efficiencies if e is not None]
        if valid_efficiencies:
            avg_efficiency = sum(valid_efficiencies) / len(valid_efficiencies)
            print(f"Collision Efficiency (q):")
            print(f"  Average: {avg_efficiency:.3f}")
            print(f"  Range: {min(valid_efficiencies):.3f} - {max(valid_efficiencies):.3f}")
        
    # Contact offset analysis
    offsets = [r.get('contact_offset_total') for r in contact_results]
    valid_offsets = [o for o in offsets if o is not None]
    if valid_offsets:
        avg_offset = sum(valid_offsets) / len(valid_offsets)
        print(f"Contact Offset:")
        print(f"  Average: {avg_offset:.2f} inches")
        print(f"  Range: {min(valid_offsets):.2f} - {max(valid_offsets):.2f} inches")
        
    # Spin analysis
    backspins = [r.get('backspin_rpm', 0) for r in contact_results]
    sidespins = [r.get('sidespin_rpm', 0) for r in contact_results]
    avg_backspin = sum(backspins) / len(backspins)
    avg_sidespin = abs(sum(sidespins)) / len(sidespins)  # Average absolute sidespin
    
    print(f"Spin Rates:")
    print(f"  Average Backspin: {avg_backspin:.0f} rpm")
    print(f"  Average |Sidespin|: {avg_sidespin:.0f} rpm")

def analyze_outcome_distribution(results):
    """Analyze at-bat outcomes."""
    print(f"\n=== Outcome Distribution ({len(results)} at-bats) ===")
    
    outcomes = {}
    for result in results:
        outcome = result.outcome
        outcomes[outcome] = outcomes.get(outcome, 0) + 1
    
    for outcome, count in outcomes.items():
        percentage = count / len(results) * 100
        print(f"  {outcome}: {count} ({percentage:.1f}%)")
    
    # Calculate contact rate
    contact_outcomes = ['single', 'double', 'triple', 'home_run', 'groundout', 'flyout', 'lineout']
    contacts = sum(outcomes.get(outcome, 0) for outcome in contact_outcomes)
    if 'in_play' in outcomes:
        contacts += outcomes['in_play']
    
    contact_rate = contacts / len(results) * 100
    print(f"  Contact Rate: {contact_rate:.1f}%")

def compare_to_mlb_benchmarks(contact_results):
    """Compare results to known MLB benchmarks."""
    print(f"\n=== MLB Benchmark Comparison ===")
    
    if not contact_results:
        print("No contact results for comparison")
        return
    
    # MLB averages (approximate)
    mlb_avg_exit_vel = 89.0  # mph
    mlb_avg_launch_angle = 10.0  # degrees
    mlb_hard_hit_rate = 35.0  # percentage (95+ mph)
    
    exit_vels = [r['exit_velocity'] for r in contact_results]
    launch_angles = [r['launch_angle'] for r in contact_results]
    
    avg_exit_vel = sum(exit_vels) / len(exit_vels)
    avg_launch = sum(launch_angles) / len(launch_angles)
    hard_hit_count = len([v for v in exit_vels if v >= 95])
    hard_hit_rate = hard_hit_count / len(exit_vels) * 100
    
    print(f"Exit Velocity: {avg_exit_vel:.1f} mph (MLB: {mlb_avg_exit_vel:.1f} mph)")
    print(f"Launch Angle: {avg_launch:.1f}° (MLB: {mlb_avg_launch_angle:.1f}°)")
    print(f"Hard Hit Rate: {hard_hit_rate:.1f}% (MLB: {mlb_hard_hit_rate:.1f}%)")
    
    # Assess realism
    exit_vel_diff = abs(avg_exit_vel - mlb_avg_exit_vel)
    launch_diff = abs(avg_launch - mlb_avg_launch_angle)
    hard_hit_diff = abs(hard_hit_rate - mlb_hard_hit_rate)
    
    print(f"\nRealism Assessment:")
    print(f"  Exit Velocity Accuracy: {'✓' if exit_vel_diff < 3 else '✗'} (±{exit_vel_diff:.1f} mph)")
    print(f"  Launch Angle Accuracy: {'✓' if launch_diff < 2 else '✗'} (±{launch_diff:.1f}°)")
    print(f"  Hard Hit Rate Accuracy: {'✓' if hard_hit_diff < 10 else '✗'} (±{hard_hit_diff:.1f}%)")

if __name__ == "__main__":
    print("Research-Based Collision Physics Analysis")
    print("=" * 50)
    
    test_realistic_collision_scenarios()
    
    print("\n" + "=" * 50)
    print("Analysis Complete!")