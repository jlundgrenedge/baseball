"""Debug script to see actual contact quality in game."""
import sys
sys.path.append('.')

from batted_ball import GameSimulator, create_test_team

# Create two teams
away_team = create_test_team("Test Away", "average")
home_team = create_test_team("Test Home", "average")

# Custom GameSimulator that logs contact data
class DebugGameSimulator(GameSimulator):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.contact_data = []
        self.last_play_result = None
    
    def simulate_at_bat(self, batting_team, pitching_team):
        result = super().simulate_at_bat(batting_team, pitching_team)
        
        # Log contact quality for balls in play
        if hasattr(self, 'last_play_result') and self.last_play_result:
            play = self.last_play_result
            if play.batted_ball_result:
                bb = play.batted_ball_result
                self.contact_data.append({
                    'exit_velocity': bb.initial_conditions.get('exit_velocity', 0),
                    'launch_angle': bb.initial_conditions.get('launch_angle', 0),
                    'distance': bb.distance,
                    'peak_height': bb.peak_height,
                    'outcome': play.outcome.value if play.outcome else 'unknown'
                })
        
        return result

# Run simulation
print("Running 3-inning debug game to analyze contact quality...")
print("=" * 60)

simulator = DebugGameSimulator(away_team, home_team, verbose=False)
final_state = simulator.simulate_game(num_innings=3)

print(f"\nFINAL: {away_team.name} {final_state.away_score} - {final_state.home_score} {home_team.name}")
print(f"Total Balls in Play: {len(simulator.contact_data)}")

# Analyze contact data
if simulator.contact_data:
    print(f"\nContact Quality Analysis:")
    print(f"{'Exit V':<8} {'Launch':<8} {'Distance':<10} {'Peak':<8} {'Outcome':<15}")
    print("-" * 60)
    
    hr_candidates = []
    for contact in simulator.contact_data:
        ev = contact['exit_velocity']
        la = contact['launch_angle']
        dist = contact['distance']
        peak = contact['peak_height']
        outcome = contact['outcome']
        
        # Check if this should have been a HR
        is_hr = outcome == 'home_run'
        could_be_hr = dist >= 395 and peak >= 30
        
        mark = "*** HR!" if is_hr else (">>> MISSED HR" if could_be_hr and not is_hr else "")
        
        print(f"{ev:<8.1f} {la:<8.1f} {dist:<10.1f} {peak:<8.1f} {outcome:<15} {mark}")
        
        if could_be_hr:
            hr_candidates.append(contact)
    
    # Summary statistics
    print(f"\n{'='*60}")
    print(f"Summary Statistics:")
    avg_ev = sum(c['exit_velocity'] for c in simulator.contact_data) / len(simulator.contact_data)
    avg_la = sum(c['launch_angle'] for c in simulator.contact_data) / len(simulator.contact_data)
    avg_dist = sum(c['distance'] for c in simulator.contact_data) / len(simulator.contact_data)
    
    print(f"  Average Exit Velocity: {avg_ev:.1f} mph")
    print(f"  Average Launch Angle: {avg_la:.1f}°")
    print(f"  Average Distance: {avg_dist:.1f} ft")
    
    # HR candidates
    print(f"\nHR Candidates (395+ ft, 30+ ft peak): {len(hr_candidates)}")
    actual_hrs = sum(1 for c in simulator.contact_data if c['outcome'] == 'home_run')
    print(f"Actual HRs: {actual_hrs}")
    
    # Exit velocity distribution
    ev_90_plus = sum(1 for c in simulator.contact_data if c['exit_velocity'] >= 90)
    ev_95_plus = sum(1 for c in simulator.contact_data if c['exit_velocity'] >= 95)
    ev_100_plus = sum(1 for c in simulator.contact_data if c['exit_velocity'] >= 100)
    ev_105_plus = sum(1 for c in simulator.contact_data if c['exit_velocity'] >= 105)
    
    print(f"\nExit Velocity Distribution:")
    print(f"  90+ mph: {ev_90_plus} ({ev_90_plus/len(simulator.contact_data)*100:.1f}%)")
    print(f"  95+ mph: {ev_95_plus} ({ev_95_plus/len(simulator.contact_data)*100:.1f}%)")
    print(f"  100+ mph: {ev_100_plus} ({ev_100_plus/len(simulator.contact_data)*100:.1f}%)")
    print(f"  105+ mph: {ev_105_plus} ({ev_105_plus/len(simulator.contact_data)*100:.1f}%)")
    
    # MLB benchmarks
    print(f"\nMLB Benchmarks:")
    print(f"  Average exit velocity: ~88-90 mph")
    print(f"  90+ mph contact: ~40-45%")
    print(f"  95+ mph contact: ~20-25%")
    print(f"  100+ mph contact: ~8-10%")
    print(f"  Expected HRs per 27 contacts: ~2-3")
