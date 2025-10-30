"""
Test scoring with runner on first base
"""
from batted_ball.player import Pitcher, Hitter
from batted_ball.game_simulation import create_test_team
from batted_ball.at_bat import AtBatSimulator
from batted_ball.play_simulation import PlaySimulator, create_standard_defense
from batted_ball.baserunning import BaserunningSimulator, BaseRunner
from batted_ball.environment import create_standard_environment

def test_runner_on_first_scenarios():
    """Test various hit scenarios with a runner on first"""
    
    # Create teams
    road_team, home_team = create_test_team("Road"), create_test_team("Home")
    
    env = create_standard_environment()
    
    print("=" * 60)
    print("Testing scoring with runner on first base")
    print("=" * 60)
    
    # Test 10 at-bats with a runner on first
    hits = 0
    runs_scored = 0
    doubles = 0
    triples = 0
    
    for i in range(10):
        # Create at-bat
        pitcher = road_team.pitchers[0]  # Use first pitcher
        hitter = home_team.hitters[i % len(home_team.hitters)]
        
        at_bat_sim = AtBatSimulator(pitcher, hitter)
        at_bat_result = at_bat_sim.simulate_at_bat()
        
        # Only test if ball was put in play
        if at_bat_result.outcome not in ["strikeout", "walk"]:
            # Create play simulation
            defense = create_standard_defense()
            play_sim = PlaySimulator(defense, env)
            
            # Add runner on first BEFORE simulating play
            runner = BaseRunner(name="Runner1", sprint_speed=60.0, base_running_iq=60.0)
            runner.current_base = "first"
            play_sim.baserunning_simulator.add_runner("first", runner)
            
            # Simulate play
            play_result = play_sim.simulate_play(at_bat_result, current_outs=0)
            
            # Check result
            if play_result.outcome.value in ["single", "double", "triple", "home_run"]:
                hits += 1
                
                if play_result.outcome.value == "double":
                    doubles += 1
                elif play_result.outcome.value == "triple":
                    triples += 1
                    
                runs = play_result.runs_scored
                runs_scored += runs
                
                print(f"\nAt-bat {i+1}:")
                print(f"  Result: {play_result.outcome.value}")
                print(f"  Runs scored: {runs}")
                print(f"  Final runner positions: {list(play_result.final_runner_positions.keys())}")
                
                # Show detailed events if runs scored
                if runs > 0:
                    print(f"  *** RUNS SCORED! ***")
                    for event in play_result.events[-5:]:  # Last 5 events
                        print(f"    [{event.time:.2f}s] {event.description}")
    
    print("\n" + "=" * 60)
    print("SUMMARY")
    print("=" * 60)
    print(f"At-bats with runner on 1st: 10")
    print(f"Hits: {hits}")
    print(f"  Singles: {hits - doubles - triples}")
    print(f"  Doubles: {doubles}")
    print(f"  Triples: {triples}")
    print(f"Runs scored: {runs_scored}")
    print(f"Average runs per hit: {runs_scored / hits if hits > 0 else 0:.2f}")
    print("\nExpected: With runner on 1st, should score ~40-60% of the time on hits")
    print(f"Actual: {(runs_scored / hits * 100) if hits > 0 else 0:.0f}% of hits resulted in runs")

if __name__ == "__main__":
    test_runner_on_first_scenarios()
