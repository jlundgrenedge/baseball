"""
Baseball Game Simulation Demo

This script demonstrates the complete game simulation capabilities,
showing how all the physics components work together to simulate
realistic baseball games with full play-by-play action.
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from batted_ball import (
    GameSimulator,
    create_test_team,
    GameState,
    Team
)


def main():
    """Run the game simulation demonstration"""
    print("BASEBALL GAME SIMULATION DEMO")
    print("=" * 50)
    print()
    print("This demonstration shows the complete game simulation system")
    print("that integrates all physics components:")
    print("- Realistic pitch simulation")
    print("- Bat-ball collision physics") 
    print("- Fielding mechanics with reaction time and range")
    print("- Baserunning physics and timing")
    print("- Complete play outcomes based on timing comparisons")
    print()
    
    # Ask user for simulation type
    print("Choose simulation type:")
    print("1. Quick Game (3 innings)")
    print("2. Full Game (9 innings)")
    print("3. Custom Team Matchup")
    print("4. Quality Comparison Game")
    
    choice = input("\nEnter choice (1-4): ").strip()
    
    if choice == "1":
        run_quick_game()
    elif choice == "2":
        run_full_game()
    elif choice == "3":
        run_custom_matchup()
    elif choice == "4":
        run_quality_comparison()
    else:
        print("Invalid choice, running quick game...")
        run_quick_game()


def run_quick_game():
    """Run a quick 3-inning demonstration game"""
    print("\n" + "=" * 60)
    print("QUICK GAME DEMO - 3 INNINGS")
    print("=" * 60)
    
    # Create two average teams
    away_team = create_test_team("Visitors", "average")
    home_team = create_test_team("Home Team", "average")
    
    # Create and run simulation
    simulator = GameSimulator(away_team, home_team, verbose=True)
    final_state = simulator.simulate_game(num_innings=3)
    
    print_game_summary(simulator, final_state)


def run_full_game():
    """Run a complete 9-inning game"""
    print("\n" + "=" * 60)
    print("FULL GAME SIMULATION - 9 INNINGS")
    print("=" * 60)
    
    # Create two teams with slightly different qualities
    away_team = create_test_team("Road Warriors", "good")
    home_team = create_test_team("Home Heroes", "average")
    
    # Create and run simulation
    simulator = GameSimulator(away_team, home_team, verbose=True)
    final_state = simulator.simulate_game(num_innings=9)
    
    print_game_summary(simulator, final_state)


def run_custom_matchup():
    """Let user create custom team matchup"""
    print("\n" + "=" * 60)
    print("CUSTOM TEAM MATCHUP")
    print("=" * 60)
    
    print("Team quality options: poor, average, good, elite")
    
    away_name = input("Away team name: ").strip() or "Visitors"
    away_quality = input("Away team quality: ").strip() or "average"
    
    home_name = input("Home team name: ").strip() or "Home Team"
    home_quality = input("Home team quality: ").strip() or "average"
    
    innings = input("Number of innings (default 9): ").strip()
    try:
        innings = int(innings) if innings else 9
    except ValueError:
        innings = 9
    
    # Create teams
    away_team = create_test_team(away_name, away_quality)
    home_team = create_test_team(home_name, home_quality)
    
    print(f"\nSimulating {innings}-inning game:")
    print(f"{away_name} ({away_quality}) @ {home_name} ({home_quality})")
    
    # Create and run simulation
    simulator = GameSimulator(away_team, home_team, verbose=True)
    final_state = simulator.simulate_game(num_innings=innings)
    
    print_game_summary(simulator, final_state)


def run_quality_comparison():
    """Run games between teams of different quality levels"""
    print("\n" + "=" * 60)
    print("TEAM QUALITY COMPARISON")
    print("=" * 60)
    
    print("This will simulate multiple short games between teams of different qualities")
    print("to demonstrate how player attributes affect game outcomes.\n")
    
    qualities = ["poor", "average", "good", "elite"]
    
    for away_quality in ["poor", "elite"]:
        for home_quality in ["poor", "elite"]:
            print(f"\n{'-' * 40}")
            print(f"{away_quality.upper()} Team @ {home_quality.upper()} Team")
            print(f"{'-' * 40}")
            
            away_team = create_test_team(f"{away_quality.title()} Visitors", away_quality)
            home_team = create_test_team(f"{home_quality.title()} Home", home_quality)
            
            # Run short 3-inning game with less verbose output
            simulator = GameSimulator(away_team, home_team, verbose=False)
            final_state = simulator.simulate_game(num_innings=3)
            
            print(f"RESULT: {away_team.name} {final_state.away_score} - {final_state.home_score} {home_team.name}")
            print(f"Total Hits: {final_state.total_hits}, Home Runs: {final_state.total_home_runs}")
            
            # Show a few key plays
            hits = [play for play in simulator.play_by_play if 'SINGLE' in play.description or 'DOUBLE' in play.description or 'HOME RUN' in play.description]
            if hits:
                print("Key hits:")
                for hit in hits[:3]:  # Show first 3 hits
                    physics = hit.physics_data
                    print(f"  {hit.description} - EV: {physics.get('exit_velocity_mph', 0)} mph, Dist: {physics.get('distance_ft', 0)} ft")


def print_game_summary(simulator: GameSimulator, final_state: GameState):
    """Print a detailed game summary"""
    print("\n" + "=" * 80)
    print("DETAILED GAME SUMMARY")
    print("=" * 80)
    
    # Basic stats
    print(f"Final Score: {simulator.away_team.name} {final_state.away_score} - {final_state.home_score} {simulator.home_team.name}")
    print(f"Innings Played: {final_state.inning - (0 if final_state.is_top else 1)}")
    print(f"Total Pitches: {final_state.total_pitches}")
    print(f"Total Hits: {final_state.total_hits}")
    print(f"Home Runs: {final_state.total_home_runs}")
    print()
    
    # Play-by-play summary
    print("PLAY-BY-PLAY HIGHLIGHTS:")
    print("-" * 40)
    
    # Show all scoring plays and notable events
    for play in simulator.play_by_play:
        if any(keyword in play.description for keyword in ['HOME RUN', 'RUN', 'DOUBLE PLAY', 'TRIPLE']):
            inning_text = f"T{play.inning}" if play.is_top else f"B{play.inning}"
            print(f"{inning_text}: {play.batter_name} - {play.description}")
    
    # Physics summary
    print(f"\nPHYSICS SUMMARY:")
    print("-" * 40)
    
    exit_velocities = [play.physics_data.get('exit_velocity_mph', 0) for play in simulator.play_by_play if play.physics_data.get('exit_velocity_mph', 0) > 0]
    distances = [play.physics_data.get('distance_ft', 0) for play in simulator.play_by_play if play.physics_data.get('distance_ft', 0) > 0]
    
    if exit_velocities:
        print(f"Average Exit Velocity: {sum(exit_velocities)/len(exit_velocities):.1f} mph")
        print(f"Max Exit Velocity: {max(exit_velocities):.1f} mph")
    
    if distances:
        print(f"Average Hit Distance: {sum(distances)/len(distances):.1f} ft")
        print(f"Longest Hit: {max(distances):.1f} ft")
    
    # Home runs detail
    home_runs = [play for play in simulator.play_by_play if 'HOME RUN' in play.description]
    if home_runs:
        print(f"\nHOME RUN DETAILS:")
        print("-" * 20)
        for hr in home_runs:
            physics = hr.physics_data
            print(f"{hr.batter_name}: {physics.get('distance_ft', 0):.0f} ft, "
                  f"EV: {physics.get('exit_velocity_mph', 0):.0f} mph, "
                  f"LA: {physics.get('launch_angle_deg', 0):.0f}°")
    
    print("\n" + "=" * 80)


def demonstrate_physics_integration():
    """Show how all physics components work together"""
    print("\n" + "=" * 80)
    print("PHYSICS INTEGRATION DEMONSTRATION")
    print("=" * 80)
    print()
    print("This simulation demonstrates how all physics components work together:")
    print()
    print("1. PITCH PHYSICS:")
    print("   - Pitcher attributes determine velocity, spin rate, location accuracy")
    print("   - 8 different pitch types with realistic spin characteristics")
    print("   - Strike zone modeling and batter pitch recognition")
    print()
    print("2. BAT-BALL COLLISION:")
    print("   - Hitter attributes affect bat speed, barrel accuracy, swing timing")
    print("   - Sweet spot physics determine exit velocity and launch angle")
    print("   - Realistic distribution of ground balls, line drives, fly balls")
    print()
    print("3. TRAJECTORY PHYSICS:")
    print("   - Spin-dependent aerodynamics (Magnus force)")
    print("   - Environmental effects (altitude, temperature, humidity)")
    print("   - Accurate flight time and landing position calculations")
    print()
    print("4. FIELDING MECHANICS:")
    print("   - Fielder reaction time, sprint speed, and acceleration")
    print("   - Range calculations based on ball hang time vs. fielder arrival")
    print("   - Throwing accuracy and velocity based on fielder attributes")
    print()
    print("5. BASERUNNING PHYSICS:")
    print("   - Runner acceleration, top speed, and base-to-base times")
    print("   - Turn efficiency when rounding bases")
    print("   - Realistic sliding mechanics with friction modeling")
    print()
    print("6. PLAY OUTCOMES:")
    print("   - Timing comparisons determine safe/out calls")
    print("   - Multi-runner advancement based on individual runner speeds")
    print("   - Complete play simulation from contact to final outcome")
    print()
    print("=" * 80)


if __name__ == "__main__":
    try:
        main()
        
        # Ask if user wants to see physics explanation
        show_physics = input("\nWould you like to see how the physics integration works? (y/n): ").strip().lower()
        if show_physics in ['y', 'yes']:
            demonstrate_physics_integration()
        
        print("\nThanks for trying the Baseball Physics Game Simulator!")
        
    except KeyboardInterrupt:
        print("\n\nSimulation interrupted by user. Thanks for playing!")
    except Exception as e:
        print(f"\nError during simulation: {e}")
        print("Please check that all required modules are properly installed.")