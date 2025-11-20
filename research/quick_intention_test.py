"""
Quick 10-game test to verify pitch intention logging fix
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from batted_ball import create_test_team
from batted_ball.at_bat import AtBatSimulator
from collections import defaultdict

def quick_test():
    print("="*80)
    print("QUICK PITCH INTENTION TEST (10 games)")
    print("="*80)
    print()

    away_team = create_test_team("Visitors", "average")
    home_team = create_test_team("Home", "average")

    pitch_intentions = defaultdict(int)
    pitch_intentions_zone = defaultdict(int)
    total_pitches = 0
    total_with_intent = 0

    for game_num in range(1, 11):
        for ab in range(10):
            pitcher = away_team.get_current_pitcher() if ab % 2 == 0 else home_team.get_current_pitcher()
            hitter = home_team.get_next_batter() if ab % 2 == 0 else away_team.get_next_batter()

            at_bat_sim = AtBatSimulator(pitcher=pitcher, hitter=hitter)
            at_bat_result = at_bat_sim.simulate_at_bat()

            for pitch_data in at_bat_result.pitches:
                total_pitches += 1

                if 'pitch_intent' in pitch_data:
                    intent_data = pitch_data['pitch_intent']
                    if 'intention_category' in intent_data:
                        total_with_intent += 1
                        intention = intent_data['intention_category']
                        pitch_intentions[intention] += 1

                        if pitch_data.get('is_strike', False):
                            pitch_intentions_zone[intention] += 1

    print(f"Total Pitches: {total_pitches}")
    print(f"Pitches with Intention: {total_with_intent} ({total_with_intent/total_pitches*100:.1f}%)")
    print()
    print("Intention Distribution:")

    for intention in ['strike_looking', 'strike_competitive', 'strike_corner',
                     'waste_chase', 'ball_intentional']:
        count = pitch_intentions.get(intention, 0)
        if total_with_intent > 0:
            pct = count / total_with_intent * 100
            zone_count = pitch_intentions_zone.get(intention, 0)
            zone_rate = (zone_count / count * 100) if count > 0 else 0
            print(f"  {intention:20s}: {count:4d} ({pct:5.1f}%) → Zone: {zone_rate:.1f}%")

    # Overall zone rate
    total_in_zone = sum(pitch_intentions_zone.values())
    overall_zone = (total_in_zone / total_with_intent * 100) if total_with_intent > 0 else 0
    print()
    print(f"Overall Zone Rate: {overall_zone:.1f}%")
    print(f"Expected: ~59.8%")
    print(f"MLB Target: 62-65%")
    print()

    if total_with_intent >= total_pitches * 0.95:
        print("✅ SUCCESS: 95%+ of pitches have intention data!")
    else:
        print(f"🚨 PROBLEM: Only {total_with_intent/total_pitches*100:.1f}% of pitches have intention data")

if __name__ == "__main__":
    quick_test()
