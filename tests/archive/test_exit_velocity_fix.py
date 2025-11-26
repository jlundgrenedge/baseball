#!/usr/bin/env python3
"""
Quick test to verify exit velocity improvements after recalibration.

Expected improvements:
- Average exit velocity should increase from ~75 mph to ~88-92 mph
- Solid contact should occur ~10-15% of balls in play
- Maximum exit velocities should reach 95-105 mph
- Home runs should occur at ~1-3% rate in games
"""

import sys
import numpy as np
from batted_ball.player import Pitcher, Hitter, generate_pitch_arsenal
from batted_ball.attributes import (
    HitterAttributes, PitcherAttributes,
    create_power_hitter, create_balanced_hitter, create_groundball_hitter
)
from batted_ball.at_bat import AtBatSimulator

def test_exit_velocities():
    """Test exit velocities with recalibrated attributes."""

    print("=" * 70)
    print("EXIT VELOCITY CALIBRATION TEST")
    print("=" * 70)

    # Create test players with different power levels using HitterAttributes
    # Testing specific bat speed ratings to verify the mapping changes
    test_hitters = [
        ("Low Power (26k BAT_SPEED)", Hitter(
            name="Weak",
            attributes=HitterAttributes(
                BAT_SPEED=26000,  # Should produce ~63 mph bat speed (raised from 57)
                BARREL_ACCURACY=50000,
                ATTACK_ANGLE_CONTROL=40000,
            ),
            speed=50000
        )),
        ("Average (50k BAT_SPEED)", Hitter(
            name="Average",
            attributes=HitterAttributes(
                BAT_SPEED=50000,  # Should produce ~75 mph bat speed (raised from 70)
                BARREL_ACCURACY=50000,
                ATTACK_ANGLE_CONTROL=45000,
            ),
            speed=50000
        )),
        ("Good (66k BAT_SPEED)", Hitter(
            name="Good",
            attributes=HitterAttributes(
                BAT_SPEED=66000,  # Should produce ~80 mph bat speed
                BARREL_ACCURACY=65000,
                ATTACK_ANGLE_CONTROL=52000,
            ),
            speed=60000
        )),
        ("Elite (85k BAT_SPEED)", Hitter(
            name="Elite",
            attributes=HitterAttributes(
                BAT_SPEED=85000,  # Should produce ~85 mph bat speed (raised from 80)
                BARREL_ACCURACY=80000,
                ATTACK_ANGLE_CONTROL=58000,
            ),
            speed=70000
        )),
    ]

    # Create average pitcher
    pitcher_attrs = PitcherAttributes(
        RAW_VELOCITY_CAP=60000,  # ~93 mph fastball
        COMMAND=60000,
        STAMINA=70000
    )
    pitch_arsenal = generate_pitch_arsenal(pitcher_attrs, role="starter")
    pitcher = Pitcher(name="Test P", attributes=pitcher_attrs, pitch_arsenal=pitch_arsenal)

    for hitter_name, hitter in test_hitters:
        bat_speed_rating = hitter.attributes.BAT_SPEED
        bat_speed_mph = hitter.attributes.get_bat_speed_mph()
        print(f"\n{hitter_name}")
        print(f"  BAT_SPEED rating: {bat_speed_rating}, maps to {bat_speed_mph:.1f} mph")
        print("-" * 70)

        sim = AtBatSimulator(pitcher, hitter)

        # Simulate 50 at-bats to get statistics
        exit_velos = []
        launch_angles = []
        collision_qs = []
        solid_contact_count = 0
        total_contact = 0
        hr_count = 0

        for _ in range(50):
            result = sim.simulate_at_bat(verbose=False)

            if result.outcome == 'in_play' and result.batted_ball_result:
                bb = result.batted_ball_result
                total_contact += 1
                exit_velos.append(bb['exit_velocity'])
                launch_angles.append(bb['launch_angle'])
                collision_qs.append(bb.get('collision_efficiency_q', 0))

                if bb['contact_quality'] == 'solid':
                    solid_contact_count += 1

                # Check for home run (simplified: distance > 380 ft, angle 20-40°)
                if bb['distance'] > 380 and 20 <= bb['launch_angle'] <= 40:
                    hr_count += 1

        if exit_velos:
            print(f"  Balls in Play: {total_contact}")
            print(f"  Exit Velocity: {np.mean(exit_velos):.1f} mph avg, {np.max(exit_velos):.1f} mph max")
            print(f"  Launch Angle: {np.mean(launch_angles):.1f}° avg (±{np.std(launch_angles):.1f}°)")
            print(f"  Collision Efficiency (q): {np.mean(collision_qs):.3f} avg (±{np.std(collision_qs):.3f})")
            print(f"  Solid Contact Rate: {solid_contact_count}/{total_contact} = {100*solid_contact_count/total_contact:.1f}%")
            print(f"  Home Runs: {hr_count} ({100*hr_count/total_contact:.1f}% of BIP)")

            # Check if improvements are working
            avg_ev = np.mean(exit_velos)
            max_ev = np.max(exit_velos)
            avg_q = np.mean(collision_qs)

            # Expectations based on bat speed rating
            bat_speed_rating = hitter.attributes.BAT_SPEED
            if bat_speed_rating <= 30000:
                expected_avg_ev = (75, 85)  # Low power should still be 75-85 mph
                expected_max_ev = (85, 95)
            elif bat_speed_rating <= 55000:
                expected_avg_ev = (85, 92)  # Average should be 85-92 mph
                expected_max_ev = (90, 100)
            elif bat_speed_rating <= 70000:
                expected_avg_ev = (88, 95)  # Good should be 88-95 mph
                expected_max_ev = (95, 105)
            else:
                expected_avg_ev = (90, 98)  # Elite should be 90-98 mph
                expected_max_ev = (98, 110)

            # Check results
            checks_passed = True
            if not (expected_avg_ev[0] <= avg_ev <= expected_avg_ev[1]):
                print(f"  ⚠ WARNING: Avg EV {avg_ev:.1f} outside expected range {expected_avg_ev}")
                checks_passed = False
            else:
                print(f"  ✓ Avg EV within expected range {expected_avg_ev}")

            if not (expected_max_ev[0] <= max_ev <= expected_max_ev[1]):
                print(f"  ⚠ WARNING: Max EV {max_ev:.1f} outside expected range {expected_max_ev}")
                checks_passed = False
            else:
                print(f"  ✓ Max EV within expected range {expected_max_ev}")

            if avg_q < 0.12:
                print(f"  ⚠ WARNING: Avg collision efficiency {avg_q:.3f} still too low (target: >0.12)")
                checks_passed = False
            else:
                print(f"  ✓ Collision efficiency improved (avg q = {avg_q:.3f})")
        else:
            print(f"  No balls in play in 50 at-bats")

    print("\n" + "=" * 70)
    print("TEST COMPLETE")
    print("=" * 70)

if __name__ == "__main__":
    test_exit_velocities()
