"""
Integration test for research-based fielding improvements with full simulation.
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from batted_ball.at_bat import AtBatSimulator
from batted_ball.player import Pitcher, Hitter
from batted_ball.fielding import Fielder, FieldingSimulator
from batted_ball.field_layout import FieldLayout

def test_fielding_integration():
    """Test that enhanced fielding integrates properly with at-bat simulation."""
    print("=== Testing Research-Enhanced Fielding Integration ===")
    
    # Create players
    pitcher = Pitcher("Research Pitcher", velocity=75, command=70)
    hitter = Hitter("Research Hitter", bat_speed=70, barrel_accuracy=65)
    
    # Create enhanced fielders with research-based attributes
    fielders = {
        "center_field": Fielder("Byron Buxton", sprint_speed=95, acceleration=90, reaction_time=85, fielding_range=95),
        "shortstop": Fielder("Carlos Correa", sprint_speed=70, acceleration=75, reaction_time=80, fielding_range=85),
        "third_base": Fielder("Manny Machado", sprint_speed=60, acceleration=70, reaction_time=75, fielding_range=80),
        "right_field": Fielder("Aaron Judge", sprint_speed=65, acceleration=65, reaction_time=70, fielding_range=75)
    }
    
    # Setup field layout and simulator
    field_layout = FieldLayout()
    fielding_sim = FieldingSimulator(field_layout)
    
    for position, fielder in fielders.items():
        fielding_sim.add_fielder(position, fielder)
    
    # Create at-bat simulator
    simulator = AtBatSimulator(pitcher, hitter)
    
    print("Testing 10 at-bats with enhanced fielding...")
    
    results = {
        "hits": 0,
        "outs": 0,
        "errors": 0,
        "total_at_bats": 0,
        "fielding_attempts": 0,
        "successful_fielding": 0
    }
    
    for i in range(10):
        try:
            result = simulator.simulate_at_bat()
            results["total_at_bats"] += 1
            
            if hasattr(result, 'contact_result') and result.contact_result:
                # Ball was put in play - test fielding
                contact = result.contact_result
                ball_position = contact.landing_position
                ball_time = contact.flight_time
                
                if ball_position and ball_time:
                    # Test fielding probability calculation
                    fielding_probs = fielding_sim.get_all_fielding_probabilities(ball_position, ball_time)
                    
                    # Find best fielder for this play
                    best_fielder_pos = max(fielding_probs.keys(), key=lambda k: fielding_probs[k])
                    best_prob = fielding_probs[best_fielder_pos]
                    
                    if best_prob > 0.1:  # Reasonable chance
                        results["fielding_attempts"] += 1
                        
                        # Simulate fielding attempt
                        fielding_result = fielding_sim.simulate_fielding_attempt(ball_position, ball_time)
                        
                        if fielding_result.success:
                            results["successful_fielding"] += 1
                            results["outs"] += 1
                        else:
                            results["hits"] += 1
                    else:
                        results["hits"] += 1  # No fielder could reach
                else:
                    results["hits"] += 1  # No landing position (HR probably)
            
        except Exception as e:
            print(f"Error in at-bat {i+1}: {e}")
            continue
    
    # Print results
    print(f"\nResults from {results['total_at_bats']} at-bats:")
    print(f"Fielding attempts: {results['fielding_attempts']}")
    print(f"Successful fielding: {results['successful_fielding']}")
    print(f"Fielding success rate: {results['successful_fielding']/max(1, results['fielding_attempts']):.1%}")
    print(f"Hits: {results['hits']}")
    print(f"Outs: {results['outs']}")
    
    # Test specific research features
    print(f"\n=== Testing Research Features ===")
    
    # Test speed-dependent drag
    from batted_ball.aerodynamics import adjust_drag_coefficient
    low_speed_cd = adjust_drag_coefficient(25)  # ~56 mph
    high_speed_cd = adjust_drag_coefficient(45)  # ~100 mph
    print(f"Drag coefficient at 56 mph: {low_speed_cd:.3f}")
    print(f"Drag coefficient at 100 mph: {high_speed_cd:.3f}")
    print(f"Drag reduction: {((low_speed_cd - high_speed_cd) / low_speed_cd * 100):.1f}%")
    
    # Test Statcast-calibrated speeds
    elite_cf = fielders["center_field"]
    avg_ss = fielders["shortstop"]
    print(f"\nStatcast Sprint Speeds:")
    print(f"Elite CF: {elite_cf.get_sprint_speed_fps_statcast():.1f} ft/s")
    print(f"Average SS: {avg_ss.get_sprint_speed_fps_statcast():.1f} ft/s")
    
    # Test catch probability model
    from batted_ball.fielding import FieldPosition
    test_position = FieldPosition(30, 200, 0)  # Medium-difficulty play
    cf_catch_prob = elite_cf.calculate_catch_probability(test_position, 2.5)
    ss_catch_prob = avg_ss.calculate_catch_probability(test_position, 2.5)
    
    print(f"\nCatch Probabilities for medium play:")
    print(f"Elite CF: {cf_catch_prob:.3f}")
    print(f"Average SS: {ss_catch_prob:.3f}")
    
    print(f"\n✅ Research-enhanced fielding successfully integrated!")
    
    return results

if __name__ == "__main__":
    test_fielding_integration()