"""Test the complete integrated ground ball system in game scenarios."""
import sys
sys.path.append('.')

from batted_ball import (
    BattedBallSimulator, PlaySimulator, GameSimulator, 
    create_standard_defense, create_test_team,
    Pitcher, Hitter, BaseRunner, AtBatSimulator,
    create_average_runner
)

def test_integrated_ground_ball_plays():
    """Test individual ground ball plays with the integrated system."""
    
    print("TESTING INTEGRATED GROUND BALL SYSTEM")
    print("="*60)
    
    # Setup simulation components
    play_sim = PlaySimulator()
    defense = create_standard_defense()
    play_sim.setup_defense(defense)
    
    ball_sim = BattedBallSimulator()
    
    # Test various ground ball scenarios
    test_cases = [
        (85.0, 5.0, -20.0, "Routine grounder to SS"),
        (95.0, 8.0, -35.0, "Hard grounder to 3B"),
        (70.0, 6.0, 15.0, "Weak grounder to 2B"),
        (90.0, 4.0, 0.0, "Grounder up the middle"),
        (75.0, 3.0, -10.0, "Slow roller to SS"),
    ]
    
    for exit_velo, launch_angle, spray_angle, description in test_cases:
        print(f"\n{description}")
        print(f"Exit: {exit_velo} mph, LA: {launch_angle}°, Spray: {spray_angle}°")
        print("-" * 50)
        
        # Simulate batted ball trajectory
        batted_ball_result = ball_sim.simulate(
            exit_velocity=exit_velo,
            launch_angle=launch_angle,
            spray_angle=spray_angle,
            backspin_rpm=500.0,
        )
        
        print(f"Ball lands: ({batted_ball_result.landing_x:.1f}, {batted_ball_result.landing_y:.1f}) ft")
        print(f"Flight time: {batted_ball_result.flight_time:.3f}s")
        
        # Create a runner for the play
        batter_runner = create_average_runner("Test Batter")
        
        # Simulate complete play
        play_result = play_sim.simulate_complete_play(
            batted_ball_result, 
            batter_runner, 
            current_outs=0
        )
        
        print(f"Outcome: {play_result.outcome.value}")
        print(f"Play description: {play_result.play_description}")
        
        # Show timing details
        print("Play events:")
        for event in play_result.events:
            print(f"  {event.time:.3f}s: {event.event_type} - {event.description}")
        
        # Validate realistic timing
        total_play_time = play_result.events[-1].time if play_result.events else 0.0
        if 0.5 <= total_play_time <= 3.0:
            print(f"✅ TIMING GOOD: {total_play_time:.3f}s (realistic)")
        elif total_play_time < 0.5:
            print(f"⚠️  TIMING FAST: {total_play_time:.3f}s (may be too fast)")
        else:
            print(f"⚠️  TIMING SLOW: {total_play_time:.3f}s (may be too slow)")

def test_quick_game_with_ground_balls():
    """Test a quick game focusing on ground ball realism."""
    
    print(f"\n" + "="*60)
    print("TESTING QUICK GAME WITH GROUND BALL IMPROVEMENTS")
    print("="*60)
    
    # Create teams
    home_team = create_test_team("Home", team_quality="average")
    away_team = create_test_team("Away", team_quality="average")
    
    # Create game
    game_sim = GameSimulator(away_team, home_team)
    
    # Play 3 innings to focus on ground ball analysis
    print("Playing 3 innings to test ground ball system...")
    
    game_result = game_sim.simulate_game(
        home_team, away_team,
        innings=3,  # Short game for testing
        verbose=True
    )
    
    print(f"\nGame Result:")
    print(f"Home: {game_result.home_score}, Away: {game_result.away_score}")
    print(f"Total innings: {game_result.innings_played}")
    
    # Analyze ground ball outcomes
    total_plays = len(game_result.play_by_play)
    ground_outs = 0
    total_outs = 0
    triples = 0
    
    print(f"\nPlay-by-play analysis:")
    for i, play in enumerate(game_result.play_by_play[-10:]):  # Show last 10 plays
        print(f"  {i+1}: {play.description}")
        
        if "ground" in play.description.lower():
            if "out" in play.description.lower():
                ground_outs += 1
            total_outs += 1
        
        if "triple" in play.description.lower():
            triples += 1
    
    print(f"\nGround ball statistics:")
    print(f"  Total plays: {total_plays}")
    print(f"  Ground ball outs: {ground_outs}")
    print(f"  Triples: {triples}")
    
    if triples == 0:
        print(f"  ✅ TRIPLES: {triples} (excellent - no excessive triples)")
    elif triples <= 1:
        print(f"  ✅ TRIPLES: {triples} (good - minimal triples)")
    else:
        print(f"  ⚠️  TRIPLES: {triples} (may be too many)")
    
    if ground_outs >= 2:
        print(f"  ✅ GROUND OUTS: {ground_outs} (good ground ball fielding)")
    else:
        print(f"  ⚠️  GROUND OUTS: {ground_outs} (fewer ground outs than expected)")
    
    return game_result

def test_specific_ground_ball_scenarios():
    """Test specific scenarios mentioned in research."""
    
    print(f"\n" + "="*60)
    print("TESTING SPECIFIC RESEARCH SCENARIOS")
    print("="*60)
    
    play_sim = PlaySimulator()
    defense = create_standard_defense()
    play_sim.setup_defense(defense)
    
    ball_sim = BattedBallSimulator()
    
    # Test: "95 mph ground ball reaches 3B (~120ft) in 0.85-1.0s"
    print("Research scenario: '95 mph ground ball to 3B'")
    print("Expected: Ball travels ~120ft total to 3B in ~0.85-1.0s")
    print("-" * 50)
    
    result = ball_sim.simulate(
        exit_velocity=95.0,
        launch_angle=6.0,
        spray_angle=-30.0,  # Toward third base
        backspin_rpm=500.0,
    )
    
    print(f"Ball trajectory: lands {result.distance:.1f}ft in {result.flight_time:.3f}s")
    
    # Create play
    batter_runner = create_average_runner("Fast Runner")
    play_result = play_sim.simulate_complete_play(result, batter_runner)
    
    print(f"Play outcome: {play_result.outcome.value}")
    print(f"Play description: {play_result.play_description}")
    
    # Find fielding time
    fielding_time = None
    for event in play_result.events:
        if "fielded" in event.description.lower():
            fielding_time = event.time
            print(f"Ball fielded in: {fielding_time:.3f}s")
            break
    
    if fielding_time and 0.7 <= fielding_time <= 1.2:
        print(f"✅ TIMING MATCHES RESEARCH: {fielding_time:.3f}s (target: 0.85-1.0s)")
    elif fielding_time:
        print(f"⚠️  TIMING OUTSIDE RESEARCH: {fielding_time:.3f}s (target: 0.85-1.0s)")
    else:
        print(f"❌ NO FIELDING TIME FOUND")

if __name__ == '__main__':
    test_integrated_ground_ball_plays()
    test_quick_game_with_ground_balls()
    test_specific_ground_ball_scenarios()