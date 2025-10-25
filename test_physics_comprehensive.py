"""
Comprehensive analysis of the research-based collision physics with larger sample.
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__)))

from batted_ball.at_bat import AtBatSimulator
from batted_ball.player import Pitcher, Hitter

def comprehensive_physics_test():
    """Run comprehensive test with large sample size."""
    print("\n=== Large Sample Collision Physics Analysis ===")
    
    # Create realistic MLB players
    pitcher = Pitcher("MLB Pitcher", velocity=92, command=70, stamina=80)
    hitter = Hitter("MLB Hitter", 
                   bat_speed=75,          # Good MLB bat speed 
                   barrel_accuracy=75,    # Good contact ability
                   zone_discipline=70,    # Decent plate discipline
                   exit_velocity_ceiling=80,  # Good power
                   swing_path_angle=12.0) # Slightly upward swing
    
    simulator = AtBatSimulator(pitcher, hitter)
    
    # Run larger sample
    print("Running 100 at-bats for statistical significance...")
    
    results = []
    contact_results = []
    
    for i in range(100):
        result = simulator.simulate_at_bat()
        results.append(result)
        
        if hasattr(result, 'batted_ball_result') and result.batted_ball_result:
            contact_results.append(result.batted_ball_result)
    
    print(f"Collected {len(contact_results)} contact events from {len(results)} at-bats")
    
    # Detailed analysis
    analyze_physics_performance(contact_results)
    analyze_realism(contact_results)

def analyze_physics_performance(contact_results):
    """Analyze the performance of the new collision physics."""
    if not contact_results:
        print("No contact results to analyze")
        return
        
    print(f"\n=== Physics Performance Analysis ===")
    
    # Exit velocity distribution
    exit_vels = [r['exit_velocity'] for r in contact_results]
    print(f"Exit Velocity Distribution:")
    print(f"  Average: {sum(exit_vels)/len(exit_vels):.1f} mph")
    print(f"  Median: {sorted(exit_vels)[len(exit_vels)//2]:.1f} mph")
    print(f"  Range: {min(exit_vels):.1f} - {max(exit_vels):.1f} mph")
    
    # Quality tiers
    excellent = len([v for v in exit_vels if v >= 105])  # Excellent (105+ mph)
    hard_hit = len([v for v in exit_vels if 95 <= v < 105])  # Hard hit (95-104 mph)
    medium_hit = len([v for v in exit_vels if 80 <= v < 95])  # Medium (80-94 mph)
    weak_hit = len([v for v in exit_vels if 60 <= v < 80])  # Weak (60-79 mph)
    very_weak = len([v for v in exit_vels if v < 60])  # Very weak (<60 mph)
    
    total = len(exit_vels)
    print(f"\nContact Quality Distribution:")
    print(f"  Excellent (105+ mph): {excellent} ({excellent/total*100:.1f}%)")
    print(f"  Hard Hit (95-104 mph): {hard_hit} ({hard_hit/total*100:.1f}%)")
    print(f"  Medium Hit (80-94 mph): {medium_hit} ({medium_hit/total*100:.1f}%)")
    print(f"  Weak Hit (60-79 mph): {weak_hit} ({weak_hit/total*100:.1f}%)")
    print(f"  Very Weak (<60 mph): {very_weak} ({very_weak/total*100:.1f}%)")
    
    # Collision efficiency analysis
    efficiencies = [r.get('collision_efficiency_q') for r in contact_results]
    valid_efficiencies = [e for e in efficiencies if e is not None]
    if valid_efficiencies:
        print(f"\nCollision Efficiency (q):")
        print(f"  Average: {sum(valid_efficiencies)/len(valid_efficiencies):.3f}")
        print(f"  Range: {min(valid_efficiencies):.3f} - {max(valid_efficiencies):.3f}")
        
        # Efficiency vs Exit Velocity correlation
        eff_vel_pairs = [(r.get('collision_efficiency_q'), r['exit_velocity']) 
                        for r in contact_results if r.get('collision_efficiency_q') is not None]
        if len(eff_vel_pairs) > 10:
            high_eff = [vel for eff, vel in eff_vel_pairs if eff > 0.15]
            low_eff = [vel for eff, vel in eff_vel_pairs if eff < 0.10]
            if high_eff and low_eff:
                print(f"  High Efficiency (>0.15) avg exit vel: {sum(high_eff)/len(high_eff):.1f} mph")
                print(f"  Low Efficiency (<0.10) avg exit vel: {sum(low_eff)/len(low_eff):.1f} mph")
    
    # Contact offset analysis
    offsets = [r.get('contact_offset_total') for r in contact_results]
    valid_offsets = [o for o in offsets if o is not None]
    if valid_offsets:
        print(f"\nContact Quality Metrics:")
        print(f"  Average Contact Offset: {sum(valid_offsets)/len(valid_offsets):.2f} inches")
        
        # Perfect contact rate
        perfect_contacts = len([o for o in valid_offsets if o < 0.25])
        print(f"  Perfect Contact Rate (<0.25\" offset): {perfect_contacts/len(valid_offsets)*100:.1f}%")

def analyze_realism(contact_results):
    """Compare to MLB realism standards."""
    print(f"\n=== MLB Realism Assessment ===")
    
    if not contact_results:
        print("No contact results for comparison")
        return
    
    exit_vels = [r['exit_velocity'] for r in contact_results]
    launch_angles = [r['launch_angle'] for r in contact_results]
    distances = [r['distance'] for r in contact_results]
    
    # MLB benchmarks
    mlb_avg_exit_vel = 89.0
    mlb_hard_hit_rate = 35.8  # 2023 MLB average
    mlb_avg_distance = 250.0  # Approximate for contact
    
    avg_exit_vel = sum(exit_vels) / len(exit_vels)
    avg_launch_angle = sum(launch_angles) / len(launch_angles)
    avg_distance = sum(distances) / len(distances)
    
    hard_hit_count = len([v for v in exit_vels if v >= 95])
    hard_hit_rate = hard_hit_count / len(exit_vels) * 100
    
    print(f"Key Metrics vs MLB Standards:")
    print(f"  Exit Velocity: {avg_exit_vel:.1f} mph (MLB: {mlb_avg_exit_vel:.1f} mph)")
    print(f"  Hard Hit Rate: {hard_hit_rate:.1f}% (MLB: {mlb_hard_hit_rate:.1f}%)")
    print(f"  Average Distance: {avg_distance:.0f} ft (MLB: ~{mlb_avg_distance:.0f} ft)")
    print(f"  Launch Angle: {avg_launch_angle:.1f}°")
    
    # Calculate accuracy scores
    exit_vel_accuracy = max(0, 100 - abs(avg_exit_vel - mlb_avg_exit_vel) * 10)
    hard_hit_accuracy = max(0, 100 - abs(hard_hit_rate - mlb_hard_hit_rate) * 2)
    distance_accuracy = max(0, 100 - abs(avg_distance - mlb_avg_distance) * 0.2)
    
    overall_realism = (exit_vel_accuracy + hard_hit_accuracy + distance_accuracy) / 3
    
    print(f"\nRealism Scores (0-100):")
    print(f"  Exit Velocity Realism: {exit_vel_accuracy:.1f}")
    print(f"  Hard Hit Rate Realism: {hard_hit_accuracy:.1f}")
    print(f"  Distance Realism: {distance_accuracy:.1f}")
    print(f"  Overall Realism Score: {overall_realism:.1f}")
    
    if overall_realism >= 80:
        print("  ✓ EXCELLENT realism - physics model is highly accurate")
    elif overall_realism >= 60:
        print("  ✓ GOOD realism - physics model is solid")
    elif overall_realism >= 40:
        print("  ~ FAIR realism - physics model needs tuning")
    else:
        print("  ✗ POOR realism - physics model needs significant improvement")

if __name__ == "__main__":
    print("Research-Based Collision Physics - Comprehensive Analysis")
    print("=" * 60)
    
    comprehensive_physics_test()
    
    print("\n" + "=" * 60)
    print("Comprehensive Analysis Complete!")