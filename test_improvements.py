#!/usr/bin/env python3
"""Test the improved pitch/swing mechanics."""

from batted_ball.at_bat import AtBatSimulator
from batted_ball.player import Pitcher, Hitter

def test_improved_mechanics():
    # Create realistic players
    pitcher = Pitcher(
        name='MLB Starter',
        velocity=70,    # Good velocity
        command=60,     # Above average command  
        control=65      # Good control
    )

    hitter = Hitter(
        name='MLB Hitter', 
        bat_speed=65,           # Above average bat speed
        zone_discipline=60,     # Good discipline
        barrel_accuracy=65,     # Good contact ability
        swing_decision_aggressiveness=55  # Slightly aggressive
    )

    sim = AtBatSimulator(pitcher, hitter)

    print('Sample At-Bat with Improved Mechanics:')
    print('=' * 50)

    result = sim.simulate_at_bat(verbose=True)

    print(f'\nFinal Outcome: {result.outcome}')
    print(f'Final Count: {result.final_count[0]}-{result.final_count[1]}')
    print(f'Total Pitches: {len(result.pitches)}')

    # Analyze pitch distribution
    strikes = sum(1 for p in result.pitches if p['is_strike'])
    balls = sum(1 for p in result.pitches if not p['is_strike'])
    swings = sum(1 for p in result.pitches if p['swing'])

    print(f'\nPitch Distribution:')
    print(f'  Strikes: {strikes}/{len(result.pitches)} ({strikes/len(result.pitches):.1%})')
    print(f'  Balls: {balls}/{len(result.pitches)} ({balls/len(result.pitches):.1%})')
    print(f'  Swings: {swings}/{len(result.pitches)} ({swings/len(result.pitches):.1%})')

    if result.batted_ball_result:
        bbr = result.batted_ball_result
        print(f'\nBatted Ball Result:')
        print(f'  Contact Quality: {bbr["contact_quality"]}')
        print(f'  Exit Velocity: {bbr["exit_velocity"]:.1f} mph')
        print(f'  Launch Angle: {bbr["launch_angle"]:.1f} degrees')
        print(f'  Distance: {bbr["distance"]:.1f} ft')

if __name__ == '__main__':
    test_improved_mechanics()