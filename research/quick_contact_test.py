"""
Quick 10-game test with contact rate fix validation
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from batted_ball import create_test_team
from batted_ball.at_bat import AtBatSimulator
from collections import defaultdict

print("="*80)
print("QUICK CONTACT RATE TEST (10 games)")
print("="*80)
print()

away_team = create_test_team("Visitors", "average")
home_team = create_test_team("Home", "average")

total_swings = 0
total_contacts = 0
total_whiffs = 0
strikeouts = 0
total_pa = 0

pitch_type_contact = defaultdict(lambda: {'swings': 0, 'whiffs': 0, 'contacts': 0})

for game in range(10):
    for ab in range(50):
        total_pa += 1
        pitcher = away_team.get_current_pitcher() if ab % 2 == 0 else home_team.get_current_pitcher()
        hitter = home_team.get_next_batter() if ab % 2 == 0 else away_team.get_next_batter()

        at_bat_sim = AtBatSimulator(pitcher=pitcher, hitter=hitter)
        at_bat_result = at_bat_sim.simulate_at_bat()

        if at_bat_result.outcome == 'strikeout':
            strikeouts += 1

        for pitch_data in at_bat_result.pitches:
            if pitch_data.get('swing', False):
                total_swings += 1
                pitch_type = pitch_data.get('pitch_type', 'unknown')
                pitch_type_contact[pitch_type]['swings'] += 1

                # Fixed: Check pitch_outcome instead of 'contact' field
                pitch_outcome = pitch_data.get('pitch_outcome', 'unknown')
                if pitch_outcome in ['foul', 'ball_in_play', 'contact']:
                    total_contacts += 1
                    pitch_type_contact[pitch_type]['contacts'] += 1
                elif pitch_outcome in ['swinging_strike', 'whiff']:
                    total_whiffs += 1
                    pitch_type_contact[pitch_type]['whiffs'] += 1
                else:
                    total_whiffs += 1
                    pitch_type_contact[pitch_type]['whiffs'] += 1

print(f"Total PA: {total_pa}")
print(f"Total Swings: {total_swings}")
print(f"Total Contacts: {total_contacts}")
print(f"Total Whiffs: {total_whiffs}")
print()

if total_swings > 0:
    contact_rate = total_contacts / total_swings * 100
    whiff_rate = total_whiffs / total_swings * 100

    print(f"Contact Rate: {contact_rate:.1f}% (MLB: ~75-80%)")
    print(f"Whiff Rate: {whiff_rate:.1f}% (MLB: ~20-25%)")
    print()

    # By pitch type
    print("Contact Rate by Pitch Type:")
    for pitch_type in sorted(pitch_type_contact.keys()):
        stats = pitch_type_contact[pitch_type]
        if stats['swings'] > 0:
            contact_pct = stats['contacts'] / stats['swings'] * 100
            print(f"  {pitch_type:12s}: {contact_pct:5.1f}% ({stats['contacts']}/{stats['swings']} swings)")
    print()

k_pct = strikeouts / total_pa * 100
print(f"K%: {k_pct:.1f}% (target: 22%)")
print()

if abs(contact_rate - 77.5) < 5:
    print("✅ Contact rates look good!")
else:
    print(f"⚠️ Contact rate {contact_rate:.1f}% is outside expected range")

if 18 <= k_pct <= 26:
    print(f"✅ K% {k_pct:.1f}% is in reasonable range!")
elif k_pct < 18:
    print(f"⚠️ K% {k_pct:.1f}% still below target 22%")
else:
    print(f"⚠️ K% {k_pct:.1f}% above target 22%")
