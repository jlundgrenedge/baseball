"""
Debug launch angle generation to see what's going wrong.
"""

from batted_ball import create_test_team
import numpy as np

def debug_launch_angles():
    """Debug launch angle generation."""
    print("Debugging Launch Angle Generation")
    print("=" * 80)
    
    # Create one team
    team = create_test_team("Test", team_quality="average")
    
    # Test each hitter
    for hitter in team.hitters:
        print(f"\n{hitter.name}:")
        
        # Get base attributes
        if hitter.attributes_v2:
            mean_angle = hitter.attributes_v2.get_attack_angle_mean_deg()
            base_variance = hitter.attributes_v2.get_attack_angle_variance_deg()
            print(f"  Mean angle: {mean_angle:.1f}°")
            print(f"  Base variance: {base_variance:.1f}°")
            
            # Calculate total variance
            natural_variance = 15.0
            consistency_factor = np.clip(base_variance / 3.0, 0.7, 1.3)
            total_variance = natural_variance * consistency_factor
            print(f"  Consistency factor: {consistency_factor:.2f}")
            print(f"  Total variance: {total_variance:.1f}°")
            
            # Generate 100 samples
            samples = []
            for _ in range(100):
                angle = hitter.get_swing_path_angle_deg()
                samples.append(angle)
            
            # Analyze
            print(f"  Actual mean: {np.mean(samples):.1f}°")
            print(f"  Actual std: {np.std(samples):.1f}°")
            print(f"  Min: {np.min(samples):.1f}°, Max: {np.max(samples):.1f}°")
            
            # Count distribution
            gb = sum(1 for s in samples if s < 10)
            ld = sum(1 for s in samples if 10 <= s < 25)
            fb = sum(1 for s in samples if 25 <= s < 50)
            pu = sum(1 for s in samples if s >= 50)
            print(f"  Distribution: GB={gb}%, LD={ld}%, FB={fb}%, PU={pu}%")

if __name__ == "__main__":
    debug_launch_angles()
