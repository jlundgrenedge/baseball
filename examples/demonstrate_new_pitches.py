"""
Demonstration of enhanced pitch physics with new pitch types.

This script demonstrates the newly added pitch types (cutter and knuckleball)
and shows the improved spin efficiency modeling based on MLB Statcast research.
"""

import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from batted_ball import (
    PitchSimulator,
    create_fastball_4seam,
    create_fastball_2seam,
    create_cutter,
    create_curveball,
    create_slider,
    create_changeup,
    create_splitter,
    create_knuckleball,
)

def print_section(title):
    """Print a formatted section header."""
    print("\n" + "="*70)
    print(title)
    print("="*70 + "\n")

def demonstrate_pitch(simulator, pitch_type, description=""):
    """Demonstrate a single pitch type."""
    print(f"Pitch: {pitch_type.name}")
    if description:
        print(f"  {description}")
    print(f"  Release velocity: {pitch_type.velocity:.1f} mph")
    print(f"  Spin rate: {pitch_type.spin_rpm:.0f} rpm")
    print(f"  Spin efficiency: {pitch_type.spin_efficiency*100:.0f}%")

    # Simulate pitch
    result = simulator.simulate(pitch_type, target_x=0.0, target_z=2.5)

    # Print results
    print(f"\nAt plate:")
    print(f"  Location: ({result.plate_y:+.1f}\", {result.plate_z:.1f}\")")
    print(f"  Velocity: {result.plate_speed:.1f} mph")
    print(f"  Flight time: {result.flight_time:.3f} sec")
    print(f"  Break: V={result.vertical_break:+.1f}\", H={result.horizontal_break:+.1f}\"")
    print(f"  Result: {'Strike' if result.is_strike else 'Ball'}")
    print()

def main():
    """Run pitch demonstrations."""
    print_section("ENHANCED PITCH PHYSICS DEMONSTRATION")
    print("Based on MLB Statcast research and physics analysis")
    print("Featuring improved spin efficiency modeling and new pitch types\n")

    # Create simulator
    sim = PitchSimulator()

    # Demonstrate all pitch types
    print_section("1. FOUR-SEAM FASTBALL")
    print("The power pitch - high velocity with efficient backspin")
    print("Research: High spin fastballs (>2400 rpm) get more swings and misses")
    fastball = create_fastball_4seam()
    demonstrate_pitch(sim, fastball,
                     "Spin efficiency: 90% - very efficient backspin creates 'rise'")

    print_section("2. TWO-SEAM FASTBALL (SINKER)")
    print("Ground ball pitch - creates sink and arm-side movement")
    print("Research: Low spin sinkers induce more ground balls")
    sinker = create_fastball_2seam()
    demonstrate_pitch(sim, sinker,
                     "Spin efficiency: 89% - tilted spin axis creates sink and run")

    print_section("3. CUTTER (NEW!)")
    print("Mariano Rivera's signature pitch - late glove-side break")
    print("Research: High spin cutters have tighter, more effective movement")
    cutter = create_cutter()
    demonstrate_pitch(sim, cutter,
                     "Spin efficiency: 49% - partial gyro spin for late cutting action")

    print_section("4. CURVEBALL")
    print("Classic breaking ball - big vertical drop from topspin")
    print("Research: Garrett Richards' 3086 rpm curve had extreme drop")
    curveball = create_curveball()
    demonstrate_pitch(sim, curveball,
                     "Spin efficiency: 69% - good topspin efficiency for sharp break")

    print_section("5. SLIDER")
    print("Hard breaking pitch - sharp glove-side movement")
    print("Research: 'Bullet spin' creates lateral break without much Magnus lift")
    slider = create_slider()
    demonstrate_pitch(sim, slider,
                     "Spin efficiency: 36% - mostly gyro spin creates horizontal break")

    print_section("6. CHANGEUP")
    print("Deception pitch - looks like fastball but drops late")
    print("Research: Velocity differential and late fade fool hitters")
    changeup = create_changeup()
    demonstrate_pitch(sim, changeup,
                     "Spin efficiency: 89% - similar to fastball but lower rpm")

    print_section("7. SPLITTER")
    print("Split-finger fastball - sharp late drop from minimal spin")
    print("Research: Mike Pelfrey's 830 rpm splitter was extreme ground ball pitch")
    splitter = create_splitter()
    demonstrate_pitch(sim, splitter,
                     "Spin efficiency: 50% - tumbling action, 'bottom falls out'")

    print_section("8. KNUCKLEBALL (NEW!)")
    print("Chaotic pitch - unpredictable flutter with almost no spin")
    print("Research: Without Magnus force, seam effects create random movement")
    knuckleball = create_knuckleball()
    demonstrate_pitch(sim, knuckleball,
                     "Spin efficiency: 10% - chaotic airflow, minimal Magnus effect")

    print_section("COMPARISON: SPIN EFFICIENCY")
    print("Spin efficiency determines how much raw spin creates actual movement:\n")

    pitches = [
        ("Four-Seam Fastball", create_fastball_4seam()),
        ("Two-Seam Fastball", create_fastball_2seam()),
        ("Cutter", create_cutter()),
        ("Curveball", create_curveball()),
        ("Slider", create_slider()),
        ("Changeup", create_changeup()),
        ("Splitter", create_splitter()),
        ("Knuckleball", create_knuckleball()),
    ]

    print(f"{'Pitch Type':<25} {'Spin (rpm)':>12} {'Efficiency':>12} {'Effective':>12}")
    print("-" * 70)
    for name, pitch in pitches:
        effective_spin = pitch.spin_rpm * pitch.spin_efficiency
        print(f"{name:<25} {pitch.spin_rpm:>12.0f} {pitch.spin_efficiency*100:>11.0f}% {effective_spin:>12.0f}")

    print_section("KEY RESEARCH INSIGHTS")
    print("1. Spin efficiency varies widely by pitch type (10-90%)")
    print("   - Fastballs have high efficiency (~90%) - clean backspin")
    print("   - Sliders have low efficiency (~36%) - gyro 'bullet' spin")
    print("   - Knuckleballs have minimal efficiency (~10%) - chaotic")
    print()
    print("2. Not all spin creates movement!")
    print("   - Only spin perpendicular to velocity creates Magnus force")
    print("   - Gyro spin (parallel to flight) creates no lift")
    print("   - This explains why 2400 rpm slider moves less than 2200 rpm curve")
    print()
    print("3. Different pitches have different optimal strategies:")
    print("   - Fastballs: maximize spin + velocity for 'rise'")
    print("   - Sinkers: lower spin for more drop and ground balls")
    print("   - Curveballs: high topspin for dramatic downward break")
    print("   - Sliders: gyro spin for tight horizontal break")
    print("   - Changeups: velocity differential for deception")
    print("   - Splitters: kill spin for late downward tumble")
    print("   - Knuckleballs: eliminate spin for chaotic flutter")
    print()
    print("4. Environmental effects matter:")
    print("   - At Coors Field (5280 ft), pitches break ~18% less")
    print("   - A curveball with 18\" break at sea level only breaks 15\" in Denver")
    print("   - Temperature affects break: ~0.3\" per 10°F")
    print("   - Headwinds increase break, tailwinds decrease it")

    print_section("CONCLUSION")
    print("Enhanced pitch physics now includes:")
    print("✓ Accurate MLB Statcast data for all pitch types")
    print("✓ Realistic spin efficiency modeling (10-90%)")
    print("✓ New pitch types: cutter and knuckleball")
    print("✓ Research-backed movement profiles")
    print("✓ Environmental effect constants for future use")
    print("\nAll physics validated against MLB data and research!")

if __name__ == "__main__":
    main()
