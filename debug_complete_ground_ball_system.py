"""Debug ground ball interception with proper fielder positioning."""
import sys
sys.path.append('.')

from batted_ball import BattedBallSimulator, PlaySimulator, create_standard_defense
from batted_ball.ground_ball_interception import GroundBallInterceptor
import numpy as np

def debug_complete_interception_system():
    """Test ground ball interception with properly positioned fielders."""
    
    print("DEBUGGING COMPLETE GROUND BALL INTERCEPTION SYSTEM")
    print("="*60)
    
    # Create complete simulation system
    play_sim = PlaySimulator()
    defense = create_standard_defense()
    play_sim.setup_defense(defense)
    
    # Get fielders with positions from the fielding simulator
    positioned_fielders = list(play_sim.fielding_simulator.fielders.values())
    
    print("Fielder positions (properly positioned):")
    for pos_name, fielder in play_sim.fielding_simulator.fielders.items():
        if fielder.current_position:
            print(f"  {pos_name}: ({fielder.current_position.x:.1f}, {fielder.current_position.y:.1f})")
        else:
            print(f"  {pos_name}: NO POSITION SET")
    print()
    
    # Test ground ball cases
    test_cases = [
        (85.0, 5.0, -20.0, "Routine grounder to SS"),
        (95.0, 8.0, -35.0, "Hard grounder to 3B"),
        (70.0, 12.0, 15.0, "Weak grounder to 2B"),
        (90.0, 6.0, 0.0, "Grounder up the middle"),
    ]
    
    ball_sim = BattedBallSimulator()
    interceptor = GroundBallInterceptor(surface_type='grass')
    
    for exit_velo, launch_angle, spray_angle, description in test_cases:
        print(f"{description}")
        print(f"Exit: {exit_velo} mph, LA: {launch_angle}°, Spray: {spray_angle}°")
        print("-" * 40)
        
        # Simulate batted ball
        result = ball_sim.simulate(
            exit_velocity=exit_velo,
            launch_angle=launch_angle,
            spray_angle=spray_angle,
            backspin_rpm=500.0,
        )
        
        print(f"Ball lands at: ({result.landing_x:.1f}, {result.landing_y:.1f}) ft")
        print(f"Flight time: {result.flight_time:.3f}s")
        
        # Expected landing distances for debugging
        if launch_angle <= 8.0:
            if result.distance > 120.0:
                print(f"  ⚠️  DISTANCE ISSUE: {launch_angle}° ball landing {result.distance:.1f}ft (expected <120ft)")
        
        # Test interception with properly positioned fielders (pass as dictionary)
        positioned_fielders_dict = play_sim.fielding_simulator.fielders
        interception = interceptor.find_best_interception(result, positioned_fielders_dict)
        
        if interception.can_be_fielded:
            print(f"✅ FIELDED by {interception.fielding_position}")
            print(f"   Interception time: {interception.interception_time:.3f}s")
            print(f"   Fielder arrival: {interception.fielder_arrival_time:.3f}s")
            print(f"   Time margin: {interception.time_margin:.3f}s")
            print(f"   Ball position: ({interception.ball_position_at_interception.x:.1f}, {interception.ball_position_at_interception.y:.1f})")
            
            # Check if timing is realistic (should be 1.0-2.5s for ground balls)
            total_time = interception.interception_time
            if 1.0 <= total_time <= 2.5:
                print(f"   ✅ TIMING GOOD: {total_time:.3f}s (realistic range)")
            elif total_time < 1.0:
                print(f"   ⚠️  TIMING FAST: {total_time:.3f}s (may be too fast)")
            else:
                print(f"   ⚠️  TIMING SLOW: {total_time:.3f}s (may be too slow)")
        else:
            print(f"❌ GETS THROUGH: No fielder can intercept")
            print(f"   Ball lands too far: ({result.landing_x:.1f}, {result.landing_y:.1f})")
        
        print()

def debug_ground_ball_distances():
    """Debug why ground balls are landing too far."""
    
    print("DEBUGGING GROUND BALL DISTANCES")
    print("="*50)
    
    ball_sim = BattedBallSimulator()
    
    # Test low launch angles that should be short ground balls
    test_angles = [2.0, 4.0, 6.0, 8.0, 10.0, 12.0]
    
    print(f"{'Angle':>5s} {'Distance':>8s} {'Flight Time':>11s} {'Peak Height':>11s} {'Expected':>12s}")
    print("-" * 60)
    
    for angle in test_angles:
        result = ball_sim.simulate(
            exit_velocity=85.0,
            launch_angle=angle,
            spray_angle=0.0,
            backspin_rpm=500.0,
        )
        
        # Expected distances based on research
        if angle <= 5.0:
            expected = "20-50 ft"
        elif angle <= 8.0:
            expected = "50-80 ft"
        elif angle <= 12.0:
            expected = "80-120 ft"
        else:
            expected = "120+ ft"
        
        print(f"{angle:5.1f}° {result.distance:7.1f}ft {result.flight_time:10.3f}s {result.peak_height:10.1f}ft {expected:>12s}")
        
        # Flag problematic distances
        if angle <= 5.0 and result.distance > 60.0:
            print(f"       ❌ PROBLEM: Very low angle traveling {result.distance:.1f}ft")
        elif angle <= 8.0 and result.distance > 100.0:
            print(f"       ⚠️  PROBLEM: Low angle traveling {result.distance:.1f}ft")

def compare_with_research_expectations():
    """Compare with documented research expectations."""
    
    print(f"\nCOMPARISON WITH RESEARCH")
    print("="*50)
    
    print("From research documents:")
    print("- '95 mph ground ball travels ~120 ft to 3B in 0.85-1.00 seconds'")
    print("- Expected: Ball LANDS ~40-60ft, ROLLS to 120ft total")
    print("- Expected fielding time: 0.85-1.5 seconds total")
    print()
    
    # Test the specific research case
    ball_sim = BattedBallSimulator()
    result = ball_sim.simulate(
        exit_velocity=95.0,
        launch_angle=6.0,  # Typical ground ball
        spray_angle=-30.0,  # Toward third base
        backspin_rpm=500.0,
    )
    
    print(f"95 mph ground ball toward 3B:")
    print(f"  Current simulation: lands {result.distance:.1f}ft in {result.flight_time:.3f}s")
    print(f"  Research target: ball travels ~120ft total to 3B in ~0.85-1.0s")
    print()
    
    if result.distance > 130.0:
        print(f"  ❌ DISTANCE PROBLEM: Landing too far ({result.distance:.1f}ft vs expected ~120ft total)")
    else:
        print(f"  ✅ DISTANCE OK: Landing {result.distance:.1f}ft is reasonable")
    
    if result.flight_time > 1.2:
        print(f"  ⚠️  FLIGHT TIME: {result.flight_time:.3f}s (expected ~0.4-0.8s flight + rolling)")
    else:
        print(f"  ✅ FLIGHT TIME: {result.flight_time:.3f}s seems reasonable")

if __name__ == '__main__':
    debug_complete_interception_system()
    debug_ground_ball_distances()
    compare_with_research_expectations()