"""Debug why outfielders are being selected for infield ground balls."""
import sys
sys.path.append('.')

from batted_ball import BattedBallSimulator, PlaySimulator, create_standard_defense
from batted_ball.ground_ball_interception import GroundBallInterceptor
import numpy as np

def debug_fielder_selection():
    """Debug why wrong fielders are being selected for ground balls."""
    
    print("DEBUGGING FIELDER SELECTION FOR GROUND BALLS")
    print("="*60)
    
    # Setup
    play_sim = PlaySimulator()
    defense = create_standard_defense()
    play_sim.setup_defense(defense)
    
    ball_sim = BattedBallSimulator()
    interceptor = GroundBallInterceptor(surface_type='grass')
    
    # Test case: Routine grounder to shortstop area
    result = ball_sim.simulate(
        exit_velocity=85.0,
        launch_angle=5.0,
        spray_angle=-20.0,
        backspin_rpm=500.0,
    )
    
    print(f"Ground ball to SS area:")
    print(f"  Ball lands at: ({result.landing_x:.1f}, {result.landing_y:.1f}) ft")
    print()
    
    # Check each fielder individually
    positioned_fielders_dict = play_sim.fielding_simulator.fielders
    
    print("Individual fielder analysis:")
    print(f"{'Position':12s} {'Distance':>8s} {'Speed':>6s} {'React':>6s} {'Can Field?':>10s} {'Time':>6s}")
    print("-" * 65)
    
    for pos_name, fielder in positioned_fielders_dict.items():
        if fielder.current_position is None:
            continue
            
        # Calculate distance to ball landing spot
        fielder_pos = np.array([fielder.current_position.x, fielder.current_position.y])
        ball_pos = np.array([result.landing_x, result.landing_y])
        distance = np.linalg.norm(ball_pos - fielder_pos)
        
        # Get fielder capabilities
        fielder_speed = interceptor._get_fielder_speed_fps(fielder)
        reaction_time = fielder.get_reaction_time_seconds()
        
        # Test this fielder's interception capability
        single_result = interceptor._calculate_fielder_interception(
            np.array([result.landing_x, result.landing_y]), 
            np.array([1.0, 0.0]),  # Direction doesn't matter much for this test
            50.0,  # Ball speed
            20.0,  # Deceleration
            fielder, 
            result.flight_time
        )
        
        can_field = "Yes" if single_result is not None else "No"
        time_str = f"{single_result[0]:.2f}s" if single_result else "N/A"
        
        print(f"{pos_name:12s} {distance:7.1f}ft {fielder_speed:5.1f} {reaction_time:5.3f}s {can_field:>10s} {time_str:>6s}")
    
    print()
    
    # Run the full interception analysis
    interception = interceptor.find_best_interception(result, positioned_fielders_dict)
    
    print("Best interception result:")
    if interception.can_be_fielded:
        print(f"  Selected fielder: {interception.fielding_position}")
        print(f"  Interception time: {interception.interception_time:.3f}s")
        print(f"  Ball position: ({interception.ball_position_at_interception.x:.1f}, {interception.ball_position_at_interception.y:.1f})")
    
    # Check if shortstop should be the obvious choice
    shortstop = positioned_fielders_dict['shortstop']
    ss_pos = np.array([shortstop.current_position.x, shortstop.current_position.y])
    ss_distance = np.linalg.norm(ball_pos - ss_pos)
    print(f"\nExpected: Shortstop at ({ss_pos[0]:.1f}, {ss_pos[1]:.1f}) is only {ss_distance:.1f}ft from ball")
    print(f"  Should easily field this ground ball!")

def debug_fielder_attributes():
    """Debug fielder speed and reaction time attributes."""
    
    print(f"\nDEBUGGING FIELDER ATTRIBUTES")
    print("="*50)
    
    defense = create_standard_defense()
    
    print(f"{'Position':12s} {'Sprint':>6s} {'React':>6s} {'Arm':>5s} {'Range':>5s}")
    print("-" * 45)
    
    for pos_name, fielder in defense.items():
        sprint = getattr(fielder, 'sprint_speed', 'N/A')
        react = getattr(fielder, 'reaction_time', 'N/A')
        arm = getattr(fielder, 'arm_strength', 'N/A')
        range_attr = getattr(fielder, 'fielding_range', 'N/A')
        
        print(f"{pos_name:12s} {sprint:>6} {react:>6} {arm:>5} {range_attr:>5}")

if __name__ == '__main__':
    debug_fielder_selection()
    debug_fielder_attributes()