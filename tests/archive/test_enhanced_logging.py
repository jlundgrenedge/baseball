#!/usr/bin/env python3
"""
Test script to demonstrate enhanced logging features in sim_metrics.py

This script creates sample metrics and demonstrates the new diagnostic output including:
1. Pitcher fatigue diagnostics
2. Machine-readable outcome codes
3. Pitch intent vs actual
4. Hitter decision diagnostics
5. Contact quality model inputs
6. Physics validation
7. Fielder route efficiency
8. Baserunner speed diagnostics
9. Expected vs actual run value
10. Game-level model drift summary
"""

import sys
sys.path.insert(0, '/home/user/baseball')

from batted_ball.sim_metrics import (
    SimMetricsCollector,
    DebugLevel,
    PitchMetrics,
    SwingDecisionMetrics,
    BattedBallMetrics,
    FieldingMetrics,
    BaserunningMetrics,
    PitcherFatigueMetrics,
    ExpectedOutcomeMetrics
)

def test_enhanced_logging():
    """Test all enhanced logging features"""
    print("="*80)
    print("ENHANCED LOGGING TEST - Demonstrating New Diagnostic Features")
    print("="*80)

    # Initialize collector with DETAILED level to show all diagnostics
    collector = SimMetricsCollector(debug_level=DebugLevel.DETAILED)

    # 1. Test Pitcher Fatigue Diagnostics
    print("\n### TEST 1: PITCHER FATIGUE DIAGNOSTICS ###\n")
    fatigue_metrics = PitcherFatigueMetrics(
        pitcher_name="Test Ace",
        pitches_thrown=65,
        current_inning=5,
        outs_recorded=12,
        current_fatigue_pct=45.0,
        stamina_rating=75000,
        base_velocity_mph=95.0,
        current_velocity_mph=93.2,
        velocity_loss_mph=1.8,
        base_spin_rpm=2300,
        current_spin_rpm=2180,
        spin_loss_rpm=120,
        base_command_sigma=2.5,
        current_command_sigma=3.2,
        command_penalty_pct=28.0,
        runners_on_base=2,
        is_high_leverage=True,
        stress_inning=True,
        times_through_order=2,
        tto_penalty_multiplier=1.15,
        expected_whiff_rate=0.23,
        expected_walk_rate=0.09,
        expected_hard_contact_rate=0.35
    )
    collector.record_fatigue(fatigue_metrics)

    # 2. Test Pitch with Intent vs Actual
    print("\n### TEST 2: PITCH WITH INTENT vs ACTUAL & MACHINE-READABLE CODE ###\n")
    pitch_metrics = PitchMetrics(
        sequence_index=1,
        pitch_type="fastball_4seam",
        count_before=(2, 1),
        release_point=(2.0, 55.0, 6.0),
        release_velocity_mph=95.0,
        release_extension_ft=6.5,
        spin_rpm=2300,
        spin_axis_deg=(0, 90),
        spin_efficiency=0.95,
        plate_velocity_mph=86.5,
        plate_location=(2.5, 28.0),  # Actual: slightly inside, low-middle
        vertical_approach_angle_deg=-4.5,
        vertical_break_inches=18.0,
        horizontal_break_inches=-3.5,
        total_break_inches=18.3,
        target_location=(-1.0, 30.0),  # Target: inside corner, middle
        pitcher_name="Test Ace",
        pitcher_team="away",
        batter_name="Test Slugger",
        batter_team="home",
        batter_swung=True,
        pitch_outcome="ball_in_play",
        is_strike=True
    )
    collector.record_pitch(pitch_metrics)

    # 3. Test Swing Decision Diagnostics
    print("\n### TEST 3: HITTER DECISION DIAGNOSTICS ###\n")
    swing_metrics = SwingDecisionMetrics(
        pitch_zone_rating="edge",
        pitch_location=(2.5, 28.0),
        pitch_velocity_mph=95.0,
        pitch_type="fastball_4seam",
        batter_discipline_rating=70000,
        count=(2, 1),
        pitch_movement_surprise=1.5,
        velocity_deception=-2.0,
        swing_probability=0.75,
        take_probability=0.25,
        chase_probability=0.15,
        swung=True,
        swing_quality="good",
        swing_timing_error_ms=-15.0,  # 15ms early
        bat_ball_contact_offset_inches=(0.3, -0.2),
        total_contact_offset=0.36,
        expected_whiff_pct=0.12,
        expected_foul_pct=0.20,
        expected_weak_pct=0.25,
        expected_fair_pct=0.28,
        expected_solid_pct=0.13,
        expected_barrel_pct=0.02,
        contact_made=True,
        contact_quality="solid",
        outcome_rolled="solid"
    )
    collector.record_swing_decision(swing_metrics)

    # 4. Test Batted Ball with Physics Validation & Contact Model Inputs
    print("\n### TEST 4: BATTED BALL WITH PHYSICS VALIDATION & CONTACT MODEL ###\n")
    batted_ball_metrics = BattedBallMetrics(
        exit_velocity_mph=102.5,
        launch_angle_deg=28.0,
        spray_angle_deg=12.0,
        backspin_rpm=1800,
        sidespin_rpm=-200,
        distance_ft=385.0,
        hang_time_sec=5.2,
        apex_height_ft=95.0,
        landing_x_ft=75.0,
        landing_y_ft=375.0,
        batter_name="Test Slugger",
        batter_team="home",
        pitcher_name="Test Ace",
        pitcher_team="away",
        bat_speed_mph=72.0,
        pitch_speed_mph=95.0,
        collision_efficiency_q=0.82,
        expected_distance_ft=380.0,  # For physics validation
        expected_hr_probability=0.65,
        expected_batting_avg=0.720,
        expected_woba=1.450,
        expected_slg=2.800,
        is_home_run=True,
        actual_outcome="home_run",
        catch_probability=0.05
    )
    collector.record_batted_ball(batted_ball_metrics)

    # 5. Test Fielding with Route Efficiency
    print("\n### TEST 5: FIELDING WITH ROUTE EFFICIENCY ###\n")
    fielding_metrics = FieldingMetrics(
        fielder_name="Test CF",
        fielder_position="CF",
        starting_position=(0, 350),
        ball_landing_position=(75, 375, 0),
        reaction_time_ms=180,
        distance_to_ball_ft=78.0,
        route_efficiency_pct=92.0,
        top_sprint_speed_fps=29.5,
        time_to_top_speed_sec=1.2,
        actual_avg_speed_fps=27.8,
        ball_hang_time_sec=5.2,
        fielder_eta_sec=5.5,
        time_margin_sec=0.3,
        opportunity_difficulty=55.0,
        expected_catch_probability=0.75,
        catch_successful=False,
        failure_reason="too_slow",
        is_error=False
    )
    collector.record_fielding(fielding_metrics)

    # 6. Test Baserunning with Speed Diagnostics
    print("\n### TEST 6: BASERUNNING WITH SPEED DIAGNOSTICS ###\n")
    baserunning_metrics = BaserunningMetrics(
        runner_name="Test Runner",
        starting_base="1st",
        target_base="3rd",
        top_sprint_speed_fps=28.5,
        acceleration_fps2=8.5,
        lead_distance_ft=12.0,
        jump_time_sec=0.35,
        jump_quality="good",
        distance_to_run_ft=185.0,
        turn_efficiency_pct=88.0,
        actual_run_time_sec=7.2,
        risk_score=0.65,
        expected_success_probability=0.72,
        send_decision="aggressive",
        runner_arrival_time_sec=7.2,
        ball_arrival_time_sec=7.5,
        time_margin_sec=0.3,
        advance_successful=True,
        outcome="safe",
        outfielder_exchange_time_sec=0.8,
        throw_velocity_mph=88.0,
        throw_accuracy_error_ft=3.5
    )
    collector.record_baserunning(baserunning_metrics)

    # 7. Test Expected vs Actual Outcome
    print("\n### TEST 7: EXPECTED vs ACTUAL RUN VALUE ###\n")
    expected_outcome_metrics = ExpectedOutcomeMetrics(
        pitcher_name="Test Ace",
        batter_name="Test Slugger",
        count=(2, 1),
        xBA=0.285,
        xSLG=0.480,
        xwOBA=0.340,
        xISO=0.195,
        expected_k_prob=0.22,
        expected_bb_prob=0.08,
        expected_contact_prob=0.70,
        expected_hr_prob=0.04,
        expected_xbh_prob=0.12,
        expected_babip=0.310,
        expected_exit_velocity=98.5,
        expected_launch_angle=18.0,
        expected_barrel_prob=0.06,
        expected_hard_hit_prob=0.38,
        actual_outcome="home_run",
        actual_exit_velocity=102.5,
        actual_launch_angle=28.0,
        actual_distance=385.0
    )
    collector.record_expected_outcome(expected_outcome_metrics)

    # 8. Print comprehensive summary with Model Drift
    print("\n### TEST 8: GAME-LEVEL MODEL DRIFT SUMMARY ###\n")
    print("(This appears in the print_summary() call below)")

    # Print full summary
    collector.print_summary()

    print("\n" + "="*80)
    print("✓ ALL ENHANCED LOGGING FEATURES DEMONSTRATED SUCCESSFULLY")
    print("="*80)

if __name__ == "__main__":
    test_enhanced_logging()
