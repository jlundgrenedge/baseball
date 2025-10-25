#!/usr/bin/env python3
"""Compare before/after mechanics with statistics."""

from batted_ball.at_bat import AtBatSimulator
from batted_ball.player import Pitcher, Hitter

def analyze_mechanics():
    # Create test players
    pitcher = Pitcher(name='Test Pitcher', velocity=65, command=55, control=60)
    hitter = Hitter(name='Test Hitter', bat_speed=60, zone_discipline=55, barrel_accuracy=60)
    sim = AtBatSimulator(pitcher, hitter)

    # Run multiple at-bats for statistical analysis
    results = []
    total_pitches = 0
    strikes = 0
    balls = 0
    swings = 0
    out_of_zone_swings = 0
    contact_made = 0
    weak_contact = 0
    solid_contact = 0
    
    print("Analyzing improved mechanics over 25 at-bats...")
    
    for i in range(25):
        result = sim.simulate_at_bat()
        results.append(result)
        
        for pitch in result.pitches:
            total_pitches += 1
            if pitch['is_strike']:
                strikes += 1
            else:
                balls += 1
                
            if pitch['swing']:
                swings += 1
                if not pitch['is_strike']:
                    out_of_zone_swings += 1
                    
                if 'contact_summary' in pitch:
                    contact_made += 1
                    quality = pitch['contact_summary']['contact_quality']
                    if quality == 'weak':
                        weak_contact += 1
                    elif quality == 'solid':
                        solid_contact += 1

    # Print summary statistics
    print(f"\nREALISM ANALYSIS RESULTS:")
    print(f"=" * 40)
    print(f"Total Pitches: {total_pitches}")
    print(f"Strike Rate: {strikes/total_pitches:.1%} (MLB: ~63%)")
    print(f"Ball Rate: {balls/total_pitches:.1%} (MLB: ~37%)")
    print(f"Swing Rate: {swings/total_pitches:.1%} (MLB: ~45-50%)")
    print(f"Out-of-Zone Swing Rate: {out_of_zone_swings/max(swings,1):.1%} (MLB: ~25-30%)")
    print(f"Contact Rate: {contact_made/max(swings,1):.1%} (MLB: ~75-80%)")
    print(f"Contact Quality Distribution:")
    print(f"  Weak: {weak_contact/max(contact_made,1):.1%}")
    print(f"  Fair: {(contact_made-weak_contact-solid_contact)/max(contact_made,1):.1%}")
    print(f"  Solid: {solid_contact/max(contact_made,1):.1%}")
    
    # Outcome distribution
    outcomes = {}
    for result in results:
        outcome = result.outcome
        outcomes[outcome] = outcomes.get(outcome, 0) + 1
    
    print(f"\nOutcome Distribution:")
    for outcome, count in sorted(outcomes.items()):
        print(f"  {outcome}: {count/len(results):.1%}")

if __name__ == '__main__':
    analyze_mechanics()