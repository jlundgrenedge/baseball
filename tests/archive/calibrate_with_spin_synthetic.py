"""
Calibration test using synthetic data with angle-dependent spin model.

This bypasses pybaseball compatibility issues while still demonstrating
the improved line drive spin estimates (v2).
"""

import numpy as np
import pandas as pd
from batted_ball.trajectory import BattedBallSimulator


def estimate_backspin_from_launch_angle(launch_angle_deg):
    """
    Estimate typical backspin based on launch angle.

    Based on Statcast calibration findings (v2 - reduced line drive spin):
    - Line drives (<20°): Minimal backspin (200-700 rpm) due to contact above center
    - Transition (20-25°): 700-1200 rpm (gradual increase)
    - Fly balls (25-35°): Optimal backspin (1200-1950 rpm)
    - Pop-ups (>35°): High backspin (1950-2700 rpm)

    v1 had 600-1200 rpm for line drives → +37 ft avg error
    v2 reduces to 200-700 rpm for better calibration
    """
    if launch_angle_deg < 20:
        # Line drives: 200-700 rpm (REDUCED from v1)
        return 200.0 + 25.0 * launch_angle_deg
    elif launch_angle_deg < 25:
        # Transition zone: 700-1200 rpm
        return 700.0 + 100.0 * (launch_angle_deg - 20)
    elif launch_angle_deg < 35:
        # Fly balls: 1200-1950 rpm
        return 1200.0 + 75.0 * (launch_angle_deg - 25)
    else:
        # Pop-ups: 1950-2700 rpm
        return 1950.0 + 50.0 * (launch_angle_deg - 35)


def generate_realistic_mlb_data():
    """
    Generate synthetic data matching the structure from the actual
    Statcast calibration, but with realistic MLB outcomes.

    Based on the actual June 2024 Statcast data bins.
    """
    # These are the actual bins and outcomes from the user's calibration run
    bins = [
        # EV, LA, count, actual distance (from real MLB data)
        (92.6, 17.2, 220, 266.4, 31.1),
        (92.6, 22.1, 287, 308.6, 24.1),
        (92.6, 26.9, 270, 333.7, 22.5),
        (92.6, 31.9, 268, 335.2, 19.7),
        (92.5, 36.9, 271, 326.5, 18.4),

        (97.7, 17.1, 335, 288.7, 32.8),
        (97.5, 22.1, 290, 335.7, 26.0),
        (97.5, 27.0, 305, 360.1, 21.1),
        (97.4, 31.9, 275, 363.4, 18.4),
        (97.3, 36.9, 217, 352.3, 17.5),

        (102.3, 16.8, 345, 305.1, 37.6),
        (102.4, 21.9, 356, 359.3, 28.2),
        (102.5, 26.8, 247, 389.0, 22.6),
        (102.2, 31.9, 219, 389.1, 19.3),
        (102.2, 36.9, 134, 378.2, 19.6),

        (107.2, 17.0, 270, 323.9, 40.4),
        (107.2, 22.0, 221, 382.4, 32.1),
        (107.0, 26.8, 172, 410.1, 23.2),
        (106.7, 31.9, 96, 414.2, 15.4),
        (107.0, 36.6, 50, 402.5, 17.2),

        (111.6, 16.7, 59, 333.2, 44.1),
        (111.5, 22.4, 47, 401.0, 36.6),
        (111.8, 26.6, 28, 430.7, 33.0),
        (112.0, 31.9, 17, 422.9, 31.0),
    ]

    return pd.DataFrame(bins, columns=[
        'avg_ev', 'avg_la', 'count', 'avg_distance', 'std_distance'
    ])


def main():
    print("="*70)
    print("STATCAST CALIBRATION WITH ANGLE-DEPENDENT SPIN (v2)")
    print("Using synthetic data based on actual June 2024 MLB outcomes")
    print("="*70)
    print()

    # Load realistic MLB outcome data
    binned = generate_realistic_mlb_data()
    print(f"Loaded {len(binned)} bins from actual MLB data")
    print()

    # Run simulations with angle-dependent spin (v2)
    print("Running simulations with v2 spin model (reduced line drive spin)...")
    sim = BattedBallSimulator()

    sim_distances = []
    spin_estimates = []

    for _, row in binned.iterrows():
        # Estimate spin based on launch angle (v2 model)
        estimated_spin = estimate_backspin_from_launch_angle(row['avg_la'])
        spin_estimates.append(estimated_spin)

        # Simulate
        result = sim.simulate(
            exit_velocity=row['avg_ev'],
            launch_angle=row['avg_la'],
            backspin_rpm=estimated_spin,
            sidespin_rpm=0.0,
            spray_angle=0.0,
            altitude=0.0,
            temperature=70.0
        )

        sim_distances.append(result.distance)

    binned['estimated_spin'] = spin_estimates
    binned['sim_distance'] = sim_distances
    binned['distance_error'] = binned['sim_distance'] - binned['avg_distance']
    binned['distance_error_pct'] = 100 * binned['distance_error'] / binned['avg_distance']

    # Generate report
    print()
    print("="*70)
    print("CALIBRATION RESULTS - v2 SPIN MODEL")
    print("="*70)
    print()

    print("SPIN MODEL CHANGES:")
    print("  v1: Line drives (<20°) had 600-1200 rpm → +37 ft avg error")
    print("  v2: Line drives (<20°) now 200-700 rpm → testing...")
    print()

    print("OVERALL STATISTICS:")
    print(f"  Mean distance error: {binned['distance_error'].mean():+.2f} ft ({binned['distance_error_pct'].mean():+.2f}%)")
    print(f"  Median distance error: {binned['distance_error'].median():+.2f} ft ({binned['distance_error_pct'].median():+.2f}%)")
    print(f"  Std dev of errors: {binned['distance_error'].std():.2f} ft")
    print(f"  Max overshoot: {binned['distance_error'].max():+.2f} ft")
    print(f"  Max undershoot: {binned['distance_error'].min():+.2f} ft")
    print()

    # By velocity
    high_ev = binned[binned['avg_ev'] >= 105]
    low_ev = binned[binned['avg_ev'] < 95]

    if len(high_ev) > 0 and len(low_ev) > 0:
        print("VELOCITY-DEPENDENT BIAS:")
        print(f"  High EV (≥105 mph) bias: {high_ev['distance_error'].mean():+.2f} ft")
        print(f"  Low EV (<95 mph) bias: {low_ev['distance_error'].mean():+.2f} ft")
        print()

    # By angle
    high_la = binned[binned['avg_la'] >= 32]
    low_la = binned[binned['avg_la'] < 22]

    if len(high_la) > 0 and len(low_la) > 0:
        print("ANGLE-DEPENDENT BIAS:")
        print(f"  High LA (≥32°) bias: {high_la['distance_error'].mean():+.2f} ft")
        print(f"  Low LA (<22°) bias: {low_la['distance_error'].mean():+.2f} ft")

        # Show improvement from v1
        print()
        print("IMPROVEMENT vs v1:")
        print(f"  v1 line drive error: +37.07 ft")
        print(f"  v2 line drive error: {low_la['distance_error'].mean():+.2f} ft")
        if low_la['distance_error'].mean() < 37.07:
            improvement = 37.07 - low_la['distance_error'].mean()
            print(f"  ✓ IMPROVED by {improvement:.2f} ft ({improvement/37.07*100:.1f}% reduction)")
        print()

    # Interpretation
    mean_err_pct = binned['distance_error_pct'].mean()
    if abs(mean_err_pct) < 2.0:
        print("INTERPRETATION:")
        print(f"  ✓ EXCELLENT: Mean error {mean_err_pct:+.2f}% is within 2% tolerance")
    elif abs(mean_err_pct) < 5.0:
        print("INTERPRETATION:")
        print(f"  ✓ GOOD: Mean error {mean_err_pct:+.2f}% is within 5% tolerance")
    else:
        print("INTERPRETATION:")
        print(f"  ⚠ NEEDS MORE TUNING: Mean error {mean_err_pct:+.2f}% still exceeds 5%")
        print(f"     Consider further spin reduction for line drives")
    print()

    print("="*70)
    print("DETAILED RESULTS BY BIN")
    print("="*70)
    print()

    for _, row in binned.iterrows():
        print(f"EV: {row['avg_ev']:.1f} mph, LA: {row['avg_la']:.1f}° (n={int(row['count'])})")
        print(f"  Actual: {row['avg_distance']:.1f} ± {row['std_distance']:.1f} ft")
        print(f"  Simulated: {row['sim_distance']:.1f} ft (using {row['estimated_spin']:.0f} rpm backspin)")
        print(f"  Error: {row['distance_error']:+.1f} ft ({row['distance_error_pct']:+.2f}%)")
        print()

    print("="*70)
    print()

    # Save results
    binned.to_csv('calibration_v2_synthetic.csv', index=False)
    print("Results saved to: calibration_v2_synthetic.csv")
    print()

    return binned


if __name__ == "__main__":
    results = main()
