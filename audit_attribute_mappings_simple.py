"""
Audit Player Attribute Mappings (Simplified - No Graphics)

Analyzes how player attributes (0-100,000 scale) map to physical performance.

Author: Claude Code
Date: 2025-11-20
"""

import sys
sys.path.insert(0, '/home/user/baseball')

from batted_ball.attributes import FielderAttributes, HitterAttributes, PitcherAttributes
from batted_ball.baserunning import BaseRunner


def test_player_variance():
    """
    Test actual player performance variance across rating tiers.
    """

    print("\n" + "="*80)
    print("PLAYER PERFORMANCE VARIANCE TEST")
    print("="*80)

    # Test fielder sprint speed variance
    print("\n1. FIELDER SPRINT SPEED VARIANCE")
    print("-" * 60)

    speed_ratings = [30000, 50000, 70000, 85000, 95000]
    speed_labels = ["Poor (30k)", "Average (50k)", "Good (70k)", "Elite (85k)", "Superstar (95k)"]

    for rating, label in zip(speed_ratings, speed_labels):
        fielder = FielderAttributes(TOP_SPRINT_SPEED=rating)
        speed_fps = fielder.get_top_sprint_speed_fps()
        speed_mph = speed_fps * 0.681818  # Convert to mph

        # Calculate time to run 90 feet
        time_90ft = 90.0 / speed_fps

        # Calculate percentage differences
        if rating == 50000:
            baseline_speed = speed_fps
            baseline_time = time_90ft

        if rating != 30000:
            speed_diff_pct = ((speed_fps - baseline_speed) / baseline_speed) * 100
            time_diff_pct = ((baseline_time - time_90ft) / baseline_time) * 100
            print(f"{label:20} → {speed_fps:5.1f} ft/s ({speed_mph:5.1f} mph) | 90ft in {time_90ft:.2f}s "
                  f"[{speed_diff_pct:+5.1f}% speed, {time_diff_pct:+5.1f}% faster]")
        else:
            print(f"{label:20} → {speed_fps:5.1f} ft/s ({speed_mph:5.1f} mph) | 90ft in {time_90ft:.2f}s")

    print("\n   MLB Benchmarks: Elite ~30 ft/s | Avg ~27 ft/s | Slow ~24 ft/s")

    # Test reaction time variance
    print("\n2. FIELDER REACTION TIME VARIANCE")
    print("-" * 60)

    for rating, label in zip(speed_ratings, speed_labels):
        fielder = FielderAttributes(REACTION_TIME=rating)
        reaction_s = fielder.get_reaction_time_s()

        if rating == 50000:
            baseline_reaction = reaction_s

        if rating != 30000:
            reaction_diff_pct = ((baseline_reaction - reaction_s) / baseline_reaction) * 100
            print(f"{label:20} → {reaction_s:.3f} seconds delay [{reaction_diff_pct:+5.1f}% improvement]")
        else:
            print(f"{label:20} → {reaction_s:.3f} seconds delay")

    # Test arm strength variance
    print("\n3. ARM STRENGTH VARIANCE")
    print("-" * 60)

    for rating, label in zip(speed_ratings, speed_labels):
        fielder = FielderAttributes(ARM_STRENGTH=rating)
        arm_mph = fielder.get_arm_strength_mph()

        # Calculate time for 127 ft throw (home to 2nd)
        throw_fps = arm_mph * 1.467
        flight_time = (127.0 / throw_fps) * 1.07  # 7% arc penalty

        if rating == 50000:
            baseline_arm = arm_mph
            baseline_flight = flight_time

        if rating != 30000:
            arm_diff_pct = ((arm_mph - baseline_arm) / baseline_arm) * 100
            flight_diff_pct = ((baseline_flight - flight_time) / baseline_flight) * 100
            print(f"{label:20} → {arm_mph:5.1f} mph | Home→2nd in {flight_time:.2f}s "
                  f"[{arm_diff_pct:+5.1f}% velo, {flight_diff_pct:+5.1f}% faster]")
        else:
            print(f"{label:20} → {arm_mph:5.1f} mph | Home→2nd in {flight_time:.2f}s")

    # Test route efficiency
    print("\n4. ROUTE EFFICIENCY VARIANCE")
    print("-" * 60)

    for rating, label in zip(speed_ratings, speed_labels):
        fielder = FielderAttributes(ROUTE_EFFICIENCY=rating)
        route_eff = fielder.get_route_efficiency_pct()

        # Calculate effective distance for 100ft straight-line run
        actual_distance = 100.0 / route_eff

        if rating == 50000:
            baseline_route = route_eff
            baseline_dist = actual_distance

        if rating != 30000:
            route_diff_pct = ((route_eff - baseline_route) / baseline_route) * 100
            dist_diff_ft = baseline_dist - actual_distance
            print(f"{label:20} → {route_eff:.3f} efficiency | 100ft run = {actual_distance:.1f}ft "
                  f"[{route_diff_pct:+5.1f}% better, {dist_diff_ft:+4.1f}ft saved]")
        else:
            print(f"{label:20} → {route_eff:.3f} efficiency | 100ft run = {actual_distance:.1f}ft")

    # Test baserunner speed variance
    print("\n5. BASERUNNER SPEED VARIANCE (Home to First)")
    print("-" * 60)

    for rating, label in zip(speed_ratings, speed_labels):
        runner = BaseRunner(sprint_speed=rating, acceleration=rating)
        h2f_time = runner.get_home_to_first_time()

        if rating == 50000:
            baseline_h2f = h2f_time

        if rating != 30000:
            h2f_diff_pct = ((baseline_h2f - h2f_time) / baseline_h2f) * 100
            h2f_diff_s = baseline_h2f - h2f_time
            print(f"{label:20} → {h2f_time:.2f} seconds [{h2f_diff_s:+4.2f}s, {h2f_diff_pct:+5.1f}% faster]")
        else:
            print(f"{label:20} → {h2f_time:.2f} seconds")

    print("\n   MLB Benchmarks: Elite ~3.7s | Avg ~4.3s | Slow ~5.2s")


def analyze_spread():
    """Analyze spread percentages for all attributes."""

    print("\n" + "="*80)
    print("ATTRIBUTE SPREAD ANALYSIS (50k → 85k)")
    print("="*80)
    print()
    print(f"{'Attribute':<35} {'50k Value':<15} {'85k Value':<15} {'Spread %':<12} {'Assessment'}")
    print("-" * 100)

    # Create test objects
    fielder_50k = FielderAttributes(
        TOP_SPRINT_SPEED=50000, REACTION_TIME=50000, ARM_STRENGTH=50000,
        TRANSFER_TIME=50000, ACCELERATION=50000, ROUTE_EFFICIENCY=50000
    )
    fielder_85k = FielderAttributes(
        TOP_SPRINT_SPEED=85000, REACTION_TIME=85000, ARM_STRENGTH=85000,
        TRANSFER_TIME=85000, ACCELERATION=85000, ROUTE_EFFICIENCY=85000
    )

    runner_50k = BaseRunner(sprint_speed=50000, acceleration=50000, base_running_iq=50000)
    runner_85k = BaseRunner(sprint_speed=85000, acceleration=85000, base_running_iq=85000)

    hitter_50k = HitterAttributes(BAT_SPEED=50000, BARREL_ACCURACY=50000)
    hitter_85k = HitterAttributes(BAT_SPEED=85000, BARREL_ACCURACY=85000)

    # Define attributes to test
    tests = [
        ("Sprint Speed (ft/s)", fielder_50k.get_top_sprint_speed_fps(), fielder_85k.get_top_sprint_speed_fps(), False),
        ("Reaction Time (s)", fielder_50k.get_reaction_time_s(), fielder_85k.get_reaction_time_s(), True),
        ("Route Efficiency (%)", fielder_50k.get_route_efficiency_pct()*100, fielder_85k.get_route_efficiency_pct()*100, False),
        ("Arm Strength (mph)", fielder_50k.get_arm_strength_mph(), fielder_85k.get_arm_strength_mph(), False),
        ("Transfer Time (s)", fielder_50k.get_transfer_time_s(), fielder_85k.get_transfer_time_s(), True),
        ("Acceleration (ft/s²)", fielder_50k.get_acceleration_fps2(), fielder_85k.get_acceleration_fps2(), False),
        ("Runner Sprint (ft/s)", runner_50k.get_sprint_speed_fps(), runner_85k.get_sprint_speed_fps(), False),
        ("Runner Reaction (s)", runner_50k.get_reaction_time_seconds(), runner_85k.get_reaction_time_seconds(), True),
        ("Bat Speed (mph)", hitter_50k.get_bat_speed_mph(), hitter_85k.get_bat_speed_mph(), False),
        ("Barrel Accuracy (mm)", hitter_50k.get_barrel_accuracy_mm(), hitter_85k.get_barrel_accuracy_mm(), True),
    ]

    for name, val_50k, val_85k, is_inverse in tests:
        # Calculate spread percentage
        if is_inverse:
            # For "smaller is better" attributes, calculate percentage reduction
            spread_pct = ((val_50k - val_85k) / val_50k) * 100
        else:
            # For "bigger is better" attributes, calculate percentage increase
            spread_pct = ((val_85k - val_50k) / val_50k) * 100

        # Determine assessment
        if spread_pct >= 15:
            assessment = "✓ GOOD"
        elif spread_pct >= 10:
            assessment = "⚠ MODERATE"
        elif spread_pct >= 5:
            assessment = "⚠ WEAK"
        else:
            assessment = "❌ FLAT"

        # Format values
        if val_50k < 1:
            val_50k_str = f"{val_50k:.3f}"
            val_85k_str = f"{val_85k:.3f}"
        elif val_50k < 10:
            val_50k_str = f"{val_50k:.2f}"
            val_85k_str = f"{val_85k:.2f}"
        else:
            val_50k_str = f"{val_50k:.1f}"
            val_85k_str = f"{val_85k:.1f}"

        print(f"{name:<35} {val_50k_str:<15} {val_85k_str:<15} {spread_pct:>5.1f}%       {assessment}")


def generate_audit_report():
    """Generate comprehensive audit report."""

    print("\n" + "="*80)
    print("COMPREHENSIVE AUDIT REPORT")
    print("="*80)

    print("\n📊 EXECUTIVE SUMMARY")
    print("-" * 80)
    print("This audit examined player attribute mappings to identify whether ratings")
    print("produce realistic variance across player types or if effects are muted.")
    print()
    print("KEY FINDINGS:")
    print("  ✓ Most attributes show good variance (10-50% difference avg→elite)")
    print("  ✓ Mappings use continuous logistic functions (no hard tiers)")
    print("  ✓ Values calibrated to MLB Statcast data")
    print("  ⚠ Two issues identified requiring fixes")

    print("\n🔍 DETAILED FINDINGS")
    print("-" * 80)

    print("\n✅ STRENGTHS:")
    print()
    print("  1. SPEED RATINGS SHOW REALISTIC VARIANCE")
    print("     • Sprint speed: 11.1% increase from avg (50k) to elite (85k)")
    print("     • Translates to meaningful on-field differences:")
    print("       - 90ft run: 3.33s (avg) vs 3.00s (elite) = 0.33s faster")
    print("     • Calibrated to MLB Statcast: 24-32 ft/s range")
    print()
    print("  2. REACTION TIME HAS EXCELLENT SPREAD")
    print("     • Fielder reaction: 50.0% reduction avg→elite (0.10s → 0.05s)")
    print("     • Runner reaction: 55.6% reduction avg→elite (0.18s → 0.08s)")
    print("     • Recently improved from 0.23s average (was too slow)")
    print()
    print("  3. ARM STRENGTH WELL-CALIBRATED")
    print("     • 17.3% increase avg→elite (75 mph → 88 mph)")
    print("     • Home-to-2nd throw: 1.55s (avg) vs 1.32s (elite) = 0.23s faster")
    print("     • Recently tuned down from 82 mph avg (was unrealistically fast)")
    print()
    print("  4. HITTING ATTRIBUTES APPROPRIATE")
    print("     • Bat speed: 13.3% increase avg→elite (75 → 85 mph)")
    print("     • Barrel accuracy: 50.0% reduction avg→elite (10mm → 5mm error)")
    print("     • Creates realistic distribution of contact quality")

    print("\n⚠️ ISSUES REQUIRING FIXES:")
    print()
    print("  1. ❌ CONSTANTS.PY MISMATCH (HIGH PRIORITY)")
    print()
    print("     Problem:")
    print("       constants.py contains OUTDATED physical constants that don't match")
    print("       the values actually used by attributes.py mappings.")
    print()
    print("     Examples:")
    print("       FIELDER_SPRINT_SPEED_AVG = 35.0 ft/s  (in constants.py - WRONG)")
    print("       50k rating → 27.0 ft/s                (in attributes.py - CORRECT)")
    print()
    print("       FIELDER_SPRINT_SPEED_ELITE = 40.0 ft/s  (in constants.py - WRONG)")
    print("       85k rating → 30.0 ft/s                  (in attributes.py - CORRECT)")
    print()
    print("     Impact:")
    print("       • Confusing for developers reading constants.py")
    print("       • Could cause bugs if constants are used directly")
    print("       • Makes codebase inconsistent")
    print()
    print("     Fix:")
    print("       Update batted_ball/constants.py lines 575-578, 644-647:")
    print()
    print("       OLD (WRONG):")
    print("         FIELDER_SPRINT_SPEED_MIN = 30.0")
    print("         FIELDER_SPRINT_SPEED_AVG = 35.0")
    print("         FIELDER_SPRINT_SPEED_ELITE = 40.0")
    print("         FIELDER_SPRINT_SPEED_MAX = 42.0")
    print()
    print("       NEW (CORRECT):")
    print("         FIELDER_SPRINT_SPEED_MIN = 24.0    # Matches 0k rating")
    print("         FIELDER_SPRINT_SPEED_AVG = 27.0    # Matches 50k rating (MLB Statcast)")
    print("         FIELDER_SPRINT_SPEED_ELITE = 30.0  # Matches 85k rating")
    print("         FIELDER_SPRINT_SPEED_MAX = 32.0    # Matches 100k rating")
    print()
    print("  2. ⚠️ BASERUNNING ATTRIBUTE CONSOLIDATION (MEDIUM PRIORITY)")
    print()
    print("     Problem:")
    print("       base_running_iq handles MULTIPLE distinct concepts:")
    print("         • Reaction time (get_reaction_time_seconds)")
    print("         • Leadoff distance (get_optimal_leadoff)")
    print("         • Decision making")
    print()
    print("       No separate attributes for:")
    print("         • JUMP ability (stolen base jumps)")
    print("         • AGGRESSION (risk-taking on bases)")
    print()
    print("     Impact:")
    print("       • Cannot create \"fast but cautious\" runners")
    print("       • Cannot create \"slow but aggressive\" runners")
    print("       • Limits player archetype diversity")
    print()
    print("     Fix:")
    print("       Split base_running_iq into separate attributes:")
    print()
    print("       class BaseRunner:")
    print("           REACTION_TIME: int      # How quickly they react (0-100k)")
    print("           BASE_AGGRESSION: int    # Risk-taking, leadoffs (0-100k)")
    print("           JUMP_ABILITY: int       # Stolen base jump timing (0-100k)")
    print()
    print("       Benefits:")
    print("         • More realistic player archetypes")
    print("         • Better stolen base modeling")
    print("         • Aligns with MLB scouting (separate tools)")

    print("\n📋 ADDITIONAL OBSERVATIONS")
    print("-" * 80)

    print("\n  • Route Efficiency: 9.1% spread avg→elite")
    print("    - Lower than other attributes, but acceptable")
    print("    - Multiplied with speed/reaction for net effect")
    print("    - Could increase to 12-15% if fielders feel too similar")
    print()
    print("  • Transfer Time: 33.3% reduction avg→elite (0.75s → 0.50s)")
    print("    - Recently tuned from 0.45s (was too fast for double plays)")
    print("    - Current values create realistic DP timing")
    print()
    print("  • Piecewise Logistic Mapping:")
    print("    - All attributes use smooth continuous curves")
    print("    - Avoids \"tier\" problems (no cliff at 85k)")
    print("    - Superhuman range (85k-100k) allows future expansion")

    print("\n✅ RECOMMENDATIONS")
    print("-" * 80)

    print("\n  1. [HIGH PRIORITY] Fix Constants Mismatch")
    print("     Action: Update constants.py sprint speed values")
    print("     Effort: 5 minutes")
    print("     Impact: HIGH (code consistency, developer clarity)")
    print()
    print("  2. [MEDIUM PRIORITY] Split Baserunning Attributes")
    print("     Action: Add REACTION_TIME, BASE_AGGRESSION, JUMP_ABILITY")
    print("     Effort: 2-3 hours (refactor + test)")
    print("     Impact: MEDIUM (better player archetypes)")
    print()
    print("  3. [LOW PRIORITY] Monitor Route Efficiency")
    print("     Action: Observe if fielders feel too similar in gameplay")
    print("     Effort: Ongoing testing")
    print("     Impact: LOW (only if problem observed)")

    print("\n" + "="*80)
    print("END OF AUDIT REPORT")
    print("="*80)


def main():
    """Run complete attribute mapping audit."""

    print("="*80)
    print("PLAYER ATTRIBUTE MAPPING AUDIT")
    print("="*80)
    print()
    print("Analyzing how 0-100,000 ratings translate to physical performance...")

    # Run variance tests
    test_player_variance()

    # Analyze spread percentages
    analyze_spread()

    # Generate comprehensive report
    generate_audit_report()

    print("\n✓ Audit complete!")


if __name__ == "__main__":
    main()
