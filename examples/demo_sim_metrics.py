"""
Demonstration of the Simulation Metrics and Debug System

Shows how to use the comprehensive sim_metrics module to track and analyze
all aspects of simulation performance, from pitch-level physics to game-wide
aggregated statistics.

This provides OOTP-style transparency and Statcast-level detail.
"""

import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from batted_ball.sim_metrics import (
    SimMetricsCollector, DebugLevel,
    PitchMetrics, SwingDecisionMetrics, BattedBallMetrics,
    FieldingMetrics, BaserunningMetrics, PitcherFatigueMetrics,
    ExpectedOutcomeMetrics, BattedBallDistribution, PitchingOutcomes
)
from batted_ball import AtBatSimulator, Pitcher, Hitter
from batted_ball.attributes import create_starter_pitcher, create_balanced_hitter
import numpy as np


def demo_pitch_level_metrics():
    """Demonstrate pitch-level tracking"""
    print("\n" + "="*80)
    print("DEMO 1: PITCH-LEVEL METRICS TRACKING")
    print("="*80)

    collector = SimMetricsCollector(debug_level=DebugLevel.DETAILED)

    # Simulate a single pitch with full metrics
    pitch = PitchMetrics(
        sequence_index=1,
        pitch_type="fastball",
        count_before=(0, 0),
        release_point=(54.5, 2.0, 6.5),  # Distance, side, height in feet
        release_velocity_mph=95.2,
        release_extension_ft=6.5,
        spin_rpm=2250,
        spin_axis_deg=(175, 12),  # Nearly vertical backspin
        spin_efficiency=0.92,
        plate_velocity_mph=86.3,
        plate_location=(2.5, 32.0),  # Slightly inside, belt high
        vertical_approach_angle_deg=-5.8,  # Downward angle
        vertical_break_inches=16.2,  # "Rise" relative to spinless
        horizontal_break_inches=-2.1,  # Slight arm-side run
        total_break_inches=16.3,
        target_location=(0.0, 30.0),  # Middle-middle
        command_error=(2.5, 2.0),  # Missed inside and up
        command_error_magnitude=3.2,
        expected_whiff_prob=0.15,
        expected_chase_prob=0.05,
        expected_swing_prob=0.65,
        expected_contact_prob=0.55,
        batter_swung=True,
        pitch_outcome="contact",
        is_strike=True,
        flight_time_ms=425,
        perceived_velocity_mph=93.0,  # Boosted by extension
    )

    collector.record_pitch(pitch)

    print("\n✅ Pitch metrics recorded successfully!")
    print(f"   Command error: {pitch.command_error_magnitude:.2f}\" from target")
    print(f"   Perceived velocity: {pitch.perceived_velocity_mph:.1f} mph (release: {pitch.release_velocity_mph:.1f})")
    print(f"   Approach angle: {pitch.vertical_approach_angle_deg:.1f}° (typical fastball: -4° to -6°)")


def demo_swing_decision_tracking():
    """Demonstrate swing decision internal logic tracking"""
    print("\n" + "="*80)
    print("DEMO 2: SWING DECISION TRACKING")
    print("="*80)

    collector = SimMetricsCollector(debug_level=DebugLevel.EXHAUSTIVE)

    # Example: Batter facing a slider low and away
    swing_decision = SwingDecisionMetrics(
        pitch_zone_rating="chase",
        pitch_location=(10.5, 16.0),  # Outside and low (chase zone)
        pitch_velocity_mph=84.2,
        pitch_type="slider",
        batter_discipline_rating=65000,  # Above average discipline
        count=(2, 1),  # Hitter's count
        pitch_movement_surprise=2.5,  # Broke 2.5" more than expected
        velocity_deception=-3.2,  # 3 mph slower than expected
        swing_probability=0.28,  # Low due to discipline + count
        take_probability=0.72,
        chase_probability=0.28,
        swung=False,  # Good take!
        swing_quality="none",
        swing_timing_error_ms=0.0,
        bat_ball_contact_offset_inches=(0.0, 0.0),
        total_contact_offset=0.0,
        expected_whiff_pct=0.45,  # Would have been tough pitch to hit
        expected_foul_pct=0.25,
        expected_weak_pct=0.20,
        expected_fair_pct=0.08,
        expected_solid_pct=0.02,
        expected_barrel_pct=0.0,
        contact_made=False,
        contact_quality=None,
        outcome_rolled="take",
    )

    collector.record_swing_decision(swing_decision)

    print("\n✅ Swing decision tracked successfully!")
    print(f"   Location: {swing_decision.pitch_location} ({swing_decision.pitch_zone_rating})")
    print(f"   Discipline check: {swing_decision.batter_discipline_rating:,} rating")
    print(f"   Swing probability: {swing_decision.swing_probability:.1%}")
    print(f"   Decision: {'SWING' if swing_decision.swung else 'TAKE'} ✓")
    print(f"   If swung, expected whiff: {swing_decision.expected_whiff_pct:.1%}")


def demo_batted_ball_metrics():
    """Demonstrate comprehensive batted ball tracking"""
    print("\n" + "="*80)
    print("DEMO 3: BATTED BALL FLIGHT METRICS")
    print("="*80)

    collector = SimMetricsCollector(debug_level=DebugLevel.DETAILED)

    # Example: Well-struck fly ball
    batted_ball = BattedBallMetrics(
        bat_speed_mph=72.5,
        pitch_speed_mph=93.1,
        collision_efficiency_q=0.21,
        exit_velocity_mph=103.2,  # Hard hit!
        launch_angle_deg=28.0,  # Optimal
        spray_angle_deg=-12.0,  # Pulled slightly
        backspin_rpm=1850,
        sidespin_rpm=-320,  # Slight hook
        distance_ft=408.0,
        hang_time_sec=5.2,
        apex_height_ft=102.0,
        landing_x_ft=-85.0,  # Left-center
        landing_y_ft=402.0,
        drag_coefficient_avg=0.32,
        lift_coefficient_avg=0.18,
        magnus_force_contribution_ft=42.0,  # Backspin added 42 ft
        drag_force_loss_ft=-58.0,  # Drag reduced distance by 58 ft
        wind_speed_mph=8.0,
        wind_direction_deg=180,  # Headwind
        wind_effect_ft=-12.0,  # Lost 12 ft to headwind
        expected_distance_ft=415.0,  # Slightly under-performed
        expected_hr_probability=0.82,
        is_home_run=True,
    )

    collector.record_batted_ball(batted_ball)

    print("\n✅ Batted ball metrics captured!")
    print(f"   Quality: {'BARREL ⭐' if batted_ball.barrel else 'HARD HIT' if batted_ball.hard_hit else 'MEDIUM'}")
    print(f"   Exit velo: {batted_ball.exit_velocity_mph:.1f} mph, LA: {batted_ball.launch_angle_deg:.1f}°")
    print(f"   Spin: {batted_ball.backspin_rpm:.0f} rpm backspin, {batted_ball.sidespin_rpm:+.0f} rpm sidespin")
    print(f"   Physics: Magnus +{batted_ball.magnus_force_contribution_ft:.0f} ft, Drag {batted_ball.drag_force_loss_ft:.0f} ft")
    print(f"   Environment: Wind {batted_ball.wind_effect_ft:+.0f} ft")
    print(f"   Result: {batted_ball.distance_ft:.0f} ft {'HOME RUN! 💣' if batted_ball.is_home_run else ''}")
    print(f"   Expected: {batted_ball.expected_distance_ft:.0f} ft (xHR: {batted_ball.expected_hr_probability:.0%})")


def demo_fielding_metrics():
    """Demonstrate fielding play tracking"""
    print("\n" + "="*80)
    print("DEMO 4: FIELDING INTERACTION METRICS")
    print("="*80)

    collector = SimMetricsCollector(debug_level=DebugLevel.DETAILED)

    # Example: Difficult catch in the gap
    fielding_play = FieldingMetrics(
        fielder_name="Byron Buxton",
        fielder_position="CF",
        starting_position=(0.0, 380.0),  # Deep center
        ball_landing_position=(-45.0, 402.0, 0.0),  # Left-center gap
        reaction_time_ms=185,  # Elite reaction
        distance_to_ball_ft=48.5,
        route_efficiency_pct=96.5,  # Nearly optimal route
        top_sprint_speed_fps=31.2,  # Elite sprint speed (30+ ft/s = elite)
        time_to_top_speed_sec=1.2,
        actual_avg_speed_fps=29.8,
        ball_hang_time_sec=5.2,
        fielder_eta_sec=4.95,  # Arrived with time to spare
        time_margin_sec=-0.25,  # 0.25 seconds early
        opportunity_difficulty=72.0,  # Difficult (50/50 ball)
        expected_catch_probability=0.48,  # Tough play
        catch_successful=True,  # Made it!
        failure_reason=None,
        is_error=False,
        exchange_time_sec=0.65,
        throw_velocity_mph=92.5,
        throw_accuracy_error_ft=1.2,  # Accurate throw
        throw_flight_time_sec=0.95,
        correct_fielder_assigned=True,
        alternative_fielders=["LF"],
    )

    collector.record_fielding(fielding_play)

    print("\n✅ Fielding play tracked!")
    print(f"   Fielder: {fielding_play.fielder_name} ({fielding_play.fielder_position})")
    print(f"   Distance: {fielding_play.distance_to_ball_ft:.1f} ft in {fielding_play.ball_hang_time_sec:.1f} sec")
    print(f"   Speed: {fielding_play.actual_avg_speed_fps:.1f} fps (max: {fielding_play.top_sprint_speed_fps:.1f})")
    print(f"   Route: {fielding_play.route_efficiency_pct:.1f}% efficient")
    print(f"   Difficulty: {fielding_play.opportunity_difficulty:.0f}/100 (xCatch: {fielding_play.expected_catch_probability:.0%})")
    print(f"   Margin: {fielding_play.time_margin_sec:+.2f} sec")
    print(f"   Result: {'✓ CATCH' if fielding_play.catch_successful else '✗ NO CATCH'}")
    print(f"   OAA: +{(1.0 - fielding_play.expected_catch_probability):.2f} (Outs Above Average on play)")


def demo_expected_outcomes():
    """Demonstrate expected vs actual outcome tracking"""
    print("\n" + "="*80)
    print("DEMO 5: EXPECTED VS ACTUAL OUTCOMES")
    print("="*80)

    collector = SimMetricsCollector(debug_level=DebugLevel.BASIC)

    # Example: Elite hitter vs average pitcher
    expected = ExpectedOutcomeMetrics(
        pitcher_name="Average Joe",
        batter_name="Mike Trout",
        count=(2, 1),
        xBA=0.312,  # Expected to hit .312 in this matchup
        xSLG=0.542,
        xwOBA=0.401,
        xISO=0.230,
        expected_k_prob=0.18,
        expected_bb_prob=0.12,
        expected_contact_prob=0.70,
        expected_hr_prob=0.08,
        expected_xbh_prob=0.22,
        expected_babip=0.358,
        expected_exit_velocity=94.5,
        expected_launch_angle=18.5,
        expected_barrel_prob=0.12,
        expected_hard_hit_prob=0.52,
        actual_outcome="home_run",
        actual_exit_velocity=106.2,
        actual_launch_angle=26.0,
        actual_distance=425.0,
    )

    collector.record_expected_outcome(expected)

    print("\n✅ Expected outcomes calculated!")
    print(f"   Matchup: {expected.batter_name} vs {expected.pitcher_name}")
    print(f"   Count: {expected.count[0]}-{expected.count[1]}")
    print(f"\n   EXPECTED:")
    print(f"      xBA: {expected.xBA:.3f}")
    print(f"      xSLG: {expected.xSLG:.3f}")
    print(f"      xwOBA: {expected.xwOBA:.3f}")
    print(f"      xHR: {expected.expected_hr_prob:.1%}")
    print(f"      Expected EV: {expected.expected_exit_velocity:.1f} mph")
    print(f"\n   ACTUAL:")
    print(f"      Outcome: {expected.actual_outcome.upper()}")
    print(f"      EV: {expected.actual_exit_velocity:.1f} mph (Δ +{expected.actual_exit_velocity - expected.expected_exit_velocity:.1f})")
    print(f"      Distance: {expected.actual_distance:.0f} ft")
    print(f"\n   COMPARISON: {expected.outcome_vs_expected.upper()}")
    print(f"      Performance delta: {expected.performance_delta:+.3f} (positive = beat expectations)")


def demo_aggregated_statistics():
    """Demonstrate game-wide aggregated statistics"""
    print("\n" + "="*80)
    print("DEMO 6: AGGREGATED GAME STATISTICS")
    print("="*80)

    # Simulate a game's worth of batted balls
    batted_balls = BattedBallDistribution()

    # Add simulated batted balls
    for _ in range(50):  # 50 balls in play
        batted_balls.total_balls_in_play += 1

        # Random launch angle
        la = np.random.normal(15.0, 15.0)  # Mean 15°, std 15°

        if la < 10:
            batted_balls.ground_balls += 1
        elif la < 25:
            batted_balls.line_drives += 1
        elif la < 50:
            batted_balls.fly_balls += 1
        else:
            batted_balls.popups += 1

        # Random exit velocity
        ev = np.random.normal(88.0, 8.0)  # Mean 88, std 8

        if ev < 85:
            batted_balls.soft += 1
        elif ev < 95:
            batted_balls.medium += 1
        else:
            batted_balls.hard_hit += 1

        # Barrel check (simplified)
        if ev >= 98 and 26 <= la <= 30:
            batted_balls.barrels += 1

    print("\n✅ Aggregated batted ball distribution:")
    print(f"   Total balls in play: {batted_balls.total_balls_in_play}")
    print()

    pct = batted_balls.get_percentages()
    comparison = batted_balls.compare_to_mlb()

    print(f"   {'Metric':<20s} {'Sim':<10s} {'vs MLB':<15s}")
    print(f"   {'-'*45}")
    print(f"   {'Ground balls':<20s} {pct.get('ground_ball_pct', 0):<10.1f}% {comparison.get('ground_ball_pct', ''):<15s}")
    print(f"   {'Line drives':<20s} {pct.get('line_drive_pct', 0):<10.1f}% {comparison.get('line_drive_pct', ''):<15s}")
    print(f"   {'Fly balls':<20s} {pct.get('fly_ball_pct', 0):<10.1f}% {comparison.get('fly_ball_pct', ''):<15s}")
    print(f"   {'Barrels':<20s} {pct.get('barrel_pct', 0):<10.1f}% {comparison.get('barrel_pct', ''):<15s}")
    print(f"   {'Hard hit':<20s} {pct.get('hard_hit_pct', 0):<10.1f}% {comparison.get('hard_hit_pct', ''):<15s}")


def demo_pitching_outcomes():
    """Demonstrate pitching outcome aggregation"""
    print("\n" + "="*80)
    print("DEMO 7: PITCHING OUTCOMES AGGREGATION")
    print("="*80)

    pitching = PitchingOutcomes()

    # Simulate an inning's worth of pitches
    for _ in range(18):  # ~18 pitches per inning average
        pitching.total_pitches += 1

        # Random outcome
        outcome = np.random.choice(
            ['called_strike', 'swinging_strike', 'foul', 'ball', 'in_play'],
            p=[0.15, 0.10, 0.22, 0.38, 0.15]
        )

        if outcome == 'called_strike':
            pitching.called_strikes += 1
        elif outcome == 'swinging_strike':
            pitching.swinging_strikes += 1
            pitching.swings += 1
            pitching.whiffs += 1
        elif outcome == 'foul':
            pitching.fouls += 1
            pitching.swings += 1
            pitching.contacts += 1
        elif outcome == 'ball':
            pitching.balls += 1
            pitching.takes += 1
        elif outcome == 'in_play':
            pitching.in_play += 1
            pitching.swings += 1
            pitching.contacts += 1

    print("\n✅ Pitching outcomes aggregated:")
    rates = pitching.get_rates()

    print(f"   Total pitches: {pitching.total_pitches}")
    print()
    print(f"   {'Metric':<20s} {'Value':<10s} {'Target':<10s}")
    print(f"   {'-'*40}")
    print(f"   {'CSW%':<20s} {rates.get('csw_pct', 0):<10.1f}% {'~28%':<10s}")
    print(f"   {'Whiff%':<20s} {rates.get('whiff_pct', 0):<10.1f}% {'~25%':<10s}")
    print(f"   {'Swing%':<20s} {rates.get('swing_pct', 0):<10.1f}% {'~47%':<10s}")
    print(f"   {'Contact%':<20s} {rates.get('contact_pct', 0):<10.1f}% {'~75%':<10s}")


def demo_full_integration():
    """Demonstrate using metrics collector with actual simulation"""
    print("\n" + "="*80)
    print("DEMO 8: FULL INTEGRATION WITH ACTUAL SIMULATION")
    print("="*80)

    # Create collector
    collector = SimMetricsCollector(debug_level=DebugLevel.BASIC)

    # Create players
    pitcher_attrs = create_starter_pitcher(quality="average")
    hitter_attrs = create_balanced_hitter(quality="average")

    pitcher = Pitcher(name="Average Joe", attributes=pitcher_attrs)
    hitter = Hitter(name="Joe Batter", attributes=hitter_attrs)

    # Create simulator
    sim = AtBatSimulator(pitcher, hitter, altitude=0, temperature=70)

    print("\n🎮 Running at-bat simulation with metrics collection...")

    # Simulate at-bat
    result = sim.simulate_at_bat(verbose=False)

    # Manually create metrics from result (integration with existing code)
    print(f"\n✅ At-bat complete: {result.outcome}")
    print(f"   Pitches thrown: {len(result.pitches)}")
    print(f"   Final count: {result.final_count[0]}-{result.final_count[1]}")

    # Create pitch metrics for each pitch
    for i, pitch_data in enumerate(result.pitches):
        from batted_ball.sim_metrics import create_pitch_metrics_from_simulation

        pitch_metrics = create_pitch_metrics_from_simulation(pitch_data, i + 1)
        # Would normally record this: collector.record_pitch(pitch_metrics)

    # If ball was put in play, create batted ball metrics
    if result.batted_ball_result:
        from batted_ball.sim_metrics import create_batted_ball_metrics_from_contact

        bb_metrics = create_batted_ball_metrics_from_contact(result.batted_ball_result)
        print(f"\n   Batted ball: {bb_metrics.exit_velocity_mph:.1f} mph, {bb_metrics.launch_angle_deg:.1f}°")
        print(f"   Distance: {bb_metrics.distance_ft:.1f} ft")
        print(f"   Type: {bb_metrics.hit_type}")
        # Would normally record this: collector.record_batted_ball(bb_metrics)

    print("\n   📊 Note: Full integration requires updating at_bat.py to populate all metrics")
    print("   This demo shows the data structures are ready for integration.")


def main():
    """Run all demonstrations"""
    print("\n" + "🎯"*40)
    print(" "*20 + "SIMULATION METRICS SYSTEM DEMONSTRATION")
    print(" "*20 + "OOTP-Style Transparency + Statcast Detail")
    print("🎯"*40)

    # Run all demos
    demo_pitch_level_metrics()
    demo_swing_decision_tracking()
    demo_batted_ball_metrics()
    demo_fielding_metrics()
    demo_expected_outcomes()
    demo_aggregated_statistics()
    demo_pitching_outcomes()
    demo_full_integration()

    print("\n" + "="*80)
    print("✅ ALL DEMONSTRATIONS COMPLETE")
    print("="*80)

    print("\n📚 NEXT STEPS:")
    print("   1. Integrate metrics collection into at_bat.py (populate PitchMetrics)")
    print("   2. Integrate into play_simulation.py (populate FieldingMetrics)")
    print("   3. Add to game_simulation.py (use collector throughout)")
    print("   4. Add CLI flag: --debug-metrics [0|1|2|3] for verbosity levels")
    print("   5. Enable CSV export for external analysis")

    print("\n📊 BENEFITS:")
    print("   ✓ Debug physics calculations in real-time")
    print("   ✓ Tune models by comparing expected vs actual")
    print("   ✓ Validate against MLB Statcast data")
    print("   ✓ Understand why specific outcomes occurred")
    print("   ✓ Export data for external analysis (R, Python, Excel)")

    print("\n" + "="*80 + "\n")


if __name__ == "__main__":
    main()
