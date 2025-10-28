"""Debug ground ball timing issues."""
import sys
sys.path.append('.')

from batted_ball import (
    BattedBallSimulator, create_standard_environment,
    create_standard_defense, create_average_runner,
    PlaySimulator, create_fastball_4seam,
    Pitcher, Hitter
)
import numpy as np

def test_ground_ball_timing():
    """Test timing of ground ball plays."""
    
    # Create components
    sim = BattedBallSimulator()
    play_sim = PlaySimulator()
    
    # Create defense
    defense = create_standard_defense()
    play_sim.setup_defense(defense)
    
    # Create batter-runner
    batter_runner = create_average_runner("Test Batter")
    
    # Simulate a ground ball hit to different positions
    test_scenarios = [
        ("Routine grounder to SS", 85.0, 5.0, -20.0),  # 85 mph, 5° LA, left side
        ("Hard grounder to 3B", 95.0, 8.0, -35.0),     # 95 mph, 8° LA, third base
        ("Weak grounder to 2B", 70.0, 12.0, 15.0),     # 70 mph, 12° LA, right side
    ]
    
    for description, exit_velo, launch_angle, spray_angle in test_scenarios:
        print(f"\n" + "="*60)
        print(f"SCENARIO: {description}")
        print(f"Exit Velo: {exit_velo} mph, Launch Angle: {launch_angle}°, Spray: {spray_angle}°")
        print("="*60)
        
        # Simulate batted ball
        result = sim.simulate(
            exit_velocity=exit_velo,
            launch_angle=launch_angle,
            spray_angle=spray_angle,
            backspin_rpm=500.0,  # Low backspin for ground ball
            fast_mode=False
        )
        
        print(f"Flight time: {result.flight_time:.3f}s")
        print(f"Landing position: ({result.landing_x:.1f}, {result.landing_y:.1f}) ft")
        print(f"Distance: {result.distance:.1f} ft")
        print(f"Peak height: {result.peak_height:.1f} ft")
        
        # Simulate complete play
        play_result = play_sim.simulate_complete_play(result, batter_runner)
        
        print(f"\nPLAY OUTCOME: {play_result.outcome}")
        print("Play events:")
        for event in play_result.get_events_chronological():
            print(f"  [{event.time:5.2f}s] {event.description}")
        
        # Analyze timing breakdown
        ground_ball_events = [e for e in play_result.events if 'ground_ball' in e.event_type or 'fielded' in e.description.lower()]
        if ground_ball_events:
            fielding_event = ground_ball_events[0]
            print(f"\nTIMING ANALYSIS:")
            print(f"  Contact to fielding: {fielding_event.time:.3f}s")
            print(f"  Ball flight time: {result.flight_time:.3f}s")
            print(f"  Ground phase time: {fielding_event.time - result.flight_time:.3f}s")
            
            # Check if this matches research expectations
            expected_ball_time = 0.85 + 1.0  # 0.85-1.0s travel + up to 1.0s fielder movement
            if fielding_event.time > expected_ball_time:
                print(f"  ⚠️  TIMING TOO SLOW: {fielding_event.time:.3f}s vs expected ~{expected_ball_time:.3f}s")
            else:
                print(f"  ✅ TIMING OK: {fielding_event.time:.3f}s within expected range")

if __name__ == '__main__':
    test_ground_ball_timing()