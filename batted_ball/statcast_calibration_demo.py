"""
Demo script for Statcast calibration using synthetic data.

This demonstrates the calibration process when live Statcast data
is not accessible (e.g., SSL/network issues). In production, you
would use real Statcast data via the statcast_calibration module.

This creates realistic "pseudo-Statcast" data based on known MLB
distributions and compares it against the simulation to validate
the physics model is working correctly.
"""

import numpy as np
import pandas as pd
from .trajectory import BattedBallSimulator
from .constants import CD_BASE, SPIN_FACTOR, CL_MAX


def generate_synthetic_statcast_data(n_samples: int = 1000) -> pd.DataFrame:
    """
    Generate synthetic batted ball data matching MLB distributions.

    Based on 2023-2024 MLB Statcast averages:
    - Exit velocity: 88.5 mph average, typically 85-110 mph range
    - Launch angle: ~12° average (including ground balls), 15-40° for fly balls
    - Distance follows quadratic relationship with EV and optimal LA ~28°

    Parameters
    ----------
    n_samples : int
        Number of synthetic batted ball events

    Returns
    -------
    pd.DataFrame
        Synthetic Statcast data with realistic distributions
    """
    np.random.seed(42)  # Reproducible

    # Generate exit velocities (normal distribution around MLB average)
    # MLB average ~88.5 mph, std ~9 mph, filter to 90-115 mph for fly balls
    exit_velocities = np.random.normal(100, 7, n_samples)
    exit_velocities = np.clip(exit_velocities, 90, 115)

    # Generate launch angles (skewed toward optimal ~28°)
    # Use beta distribution to match realistic fly ball distribution
    launch_angles = 15 + 25 * np.random.beta(2, 2, n_samples)  # 15-40° range, peak ~28°

    # Generate realistic distances based on exit velocity and launch angle
    # Using empirical MLB relationships:
    # - Distance ≈ 5 ft/mph * (EV - 60)
    # - Optimal angle ~28°, falls off outside 20-35° range
    # - Add noise to simulate varying conditions (spin, wind, etc.)

    distances = []
    hang_times = []

    for ev, la in zip(exit_velocities, launch_angles):
        # Realistic MLB distance formula based on Statcast data:
        # At optimal 28° launch angle:
        # - 85 mph → ~290 ft
        # - 90 mph → ~330 ft
        # - 100 mph → ~405 ft
        # - 110 mph → ~480 ft
        # Approximately 7.5 ft per mph above 85 mph baseline

        # Base distance from exit velocity (empirical: ~7.5 ft per mph above 85)
        base_dist = 290.0 + 7.5 * (ev - 85)  # Calibrated to Statcast averages

        # Launch angle efficiency (peak at 28°, drops off outside 20-35°)
        # Using realistic efficiency curve: 100% at 28°, ~90% at 20°/35°, ~75% at 15°/40°
        angle_diff = abs(la - 28)
        if angle_diff < 5:
            angle_efficiency = 1.0 - 0.01 * angle_diff
        elif angle_diff < 10:
            angle_efficiency = 0.95 - 0.02 * (angle_diff - 5)
        else:
            angle_efficiency = 0.85 - 0.02 * (angle_diff - 10)

        angle_efficiency = max(angle_efficiency, 0.60)  # Floor at 60%

        # Calculate expected distance
        expected_dist = base_dist * angle_efficiency

        # Add realistic noise (±8% typical variation for spin/conditions)
        noise = np.random.normal(0, expected_dist * 0.08)
        actual_dist = expected_dist + noise

        distances.append(max(actual_dist, 200))  # Minimum 200 ft for this data

        # Hang time roughly scales with launch angle and exit velocity
        # Higher angle = longer hang time, higher EV = slightly longer too
        # Typical range: 4-6 seconds for fly balls
        base_hang = 2.5 + 0.10 * la  # Launch angle effect dominates
        ev_factor = 0.005 * (ev - 90)  # Small EV effect
        hang_time = base_hang + ev_factor + np.random.normal(0, 0.3)
        hang_times.append(max(hang_time, 3.5))

    return pd.DataFrame({
        'exit_velocity': exit_velocities,
        'launch_angle': launch_angles,
        'distance': distances,
        'hang_time': hang_times,
    })


def run_calibration_demo():
    """
    Run calibration demo with synthetic data.
    """
    print("=" * 70)
    print("STATCAST CALIBRATION DEMO")
    print("Using synthetic data (realistic MLB distributions)")
    print("=" * 70)
    print()

    # Generate synthetic data
    print("Generating 1000 synthetic batted ball events...")
    data = generate_synthetic_statcast_data(n_samples=1000)
    print(f"Generated {len(data)} events")
    print(f"Exit velocity range: {data['exit_velocity'].min():.1f} - {data['exit_velocity'].max():.1f} mph")
    print(f"Launch angle range: {data['launch_angle'].min():.1f} - {data['launch_angle'].max():.1f}°")
    print(f"Distance range: {data['distance'].min():.1f} - {data['distance'].max():.1f} ft")
    print()

    # Define bins
    ev_bins = [(90, 95), (95, 100), (100, 105), (105, 110), (110, 115)]
    la_bins = [(15, 20), (20, 25), (25, 30), (30, 35), (35, 40)]

    # Bin data
    print("Binning data by exit velocity and launch angle...")
    binned_results = []

    for ev_min, ev_max in ev_bins:
        for la_min, la_max in la_bins:
            bin_data = data[
                (data['exit_velocity'] >= ev_min) &
                (data['exit_velocity'] < ev_max) &
                (data['launch_angle'] >= la_min) &
                (data['launch_angle'] < la_max)
            ]

            if len(bin_data) < 5:
                continue

            binned_results.append({
                'ev_min': ev_min,
                'ev_max': ev_max,
                'la_min': la_min,
                'la_max': la_max,
                'count': len(bin_data),
                'avg_ev': bin_data['exit_velocity'].mean(),
                'avg_la': bin_data['launch_angle'].mean(),
                'avg_distance': bin_data['distance'].mean(),
                'std_distance': bin_data['distance'].std(),
                'avg_hang_time': bin_data['hang_time'].mean(),
            })

    binned_df = pd.DataFrame(binned_results)
    print(f"Created {len(binned_df)} bins with sufficient data")
    print()

    # Run simulations
    print("Running physics simulations for each bin...")
    simulator = BattedBallSimulator()
    sim_distances = []
    sim_hang_times = []

    for _, row in binned_df.iterrows():
        result = simulator.simulate(
            exit_velocity=row['avg_ev'],
            launch_angle=row['avg_la'],
            backspin_rpm=1800,  # Typical fly ball backspin
            sidespin_rpm=0,
            spray_angle=0,
            altitude=0,
            temperature=70,
        )
        sim_distances.append(result.distance)
        sim_hang_times.append(result.flight_time)

    binned_df['sim_distance'] = sim_distances
    binned_df['sim_hang_time'] = sim_hang_times
    binned_df['distance_error'] = binned_df['sim_distance'] - binned_df['avg_distance']
    binned_df['distance_error_pct'] = 100 * binned_df['distance_error'] / binned_df['avg_distance']
    binned_df['hang_time_error'] = binned_df['sim_hang_time'] - binned_df['avg_hang_time']

    # Analyze results
    print("=" * 70)
    print("CALIBRATION RESULTS")
    print("=" * 70)
    print()

    print("CURRENT PHYSICS CONSTANTS:")
    print(f"  CD_BASE (drag coefficient): {CD_BASE:.4f}")
    print(f"  SPIN_FACTOR (Magnus effect): {SPIN_FACTOR:.6f}")
    print(f"  CL_MAX (max lift coefficient): {CL_MAX:.4f}")
    print()

    print("OVERALL STATISTICS:")
    print(f"  Mean distance error: {binned_df['distance_error'].mean():+.2f} ft ({binned_df['distance_error_pct'].mean():+.2f}%)")
    print(f"  Median distance error: {binned_df['distance_error'].median():+.2f} ft ({binned_df['distance_error_pct'].median():+.2f}%)")
    print(f"  Std dev of errors: {binned_df['distance_error'].std():.2f} ft")
    print(f"  Max overshoot: {binned_df['distance_error'].max():+.2f} ft")
    print(f"  Max undershoot: {binned_df['distance_error'].min():+.2f} ft")
    print()

    print(f"  Mean hang time error: {binned_df['hang_time_error'].mean():+.2f} s")
    print(f"  Median hang time error: {binned_df['hang_time_error'].median():+.2f} s")
    print()

    # Check for systematic biases
    high_ev = binned_df[binned_df['avg_ev'] >= 105]
    low_ev = binned_df[binned_df['avg_ev'] < 95]

    if len(high_ev) > 0 and len(low_ev) > 0:
        print("VELOCITY-DEPENDENT BIAS:")
        print(f"  High EV (≥105 mph) bias: {high_ev['distance_error'].mean():+.2f} ft")
        print(f"  Low EV (<95 mph) bias: {low_ev['distance_error'].mean():+.2f} ft")
        print()

    high_la = binned_df[binned_df['avg_la'] >= 32]
    low_la = binned_df[binned_df['avg_la'] < 22]

    if len(high_la) > 0 and len(low_la) > 0:
        print("ANGLE-DEPENDENT BIAS:")
        print(f"  High LA (≥32°) bias: {high_la['distance_error'].mean():+.2f} ft")
        print(f"  Low LA (<22°) bias: {low_la['distance_error'].mean():+.2f} ft")
        print()

    # Interpretation
    mean_err_pct = binned_df['distance_error_pct'].mean()

    print("INTERPRETATION:")
    if abs(mean_err_pct) < 2.0:
        print(f"  ✓ EXCELLENT: Mean error {mean_err_pct:+.2f}% is within 2% tolerance")
        print("    Physics model is well-calibrated to MLB data")
    elif abs(mean_err_pct) < 5.0:
        print(f"  ⚠ GOOD: Mean error {mean_err_pct:+.2f}% is within 5% tolerance")
        print("    Minor adjustments could improve accuracy")
    else:
        print(f"  ✗ NEEDS TUNING: Mean error {mean_err_pct:+.2f}% exceeds 5%")
        print("    Consider adjusting drag/Magnus coefficients")

    print()

    # Detailed results
    print("=" * 70)
    print("DETAILED RESULTS BY BIN")
    print("=" * 70)
    print()

    for _, row in binned_df.iterrows():
        print(f"EV: {row['avg_ev']:.1f} mph, LA: {row['avg_la']:.1f}° (n={row['count']})")
        print(f"  Actual: {row['avg_distance']:.1f} ± {row['std_distance']:.1f} ft, {row['avg_hang_time']:.2f} s")
        print(f"  Simulated: {row['sim_distance']:.1f} ft, {row['sim_hang_time']:.2f} s")
        print(f"  Distance error: {row['distance_error']:+.1f} ft ({row['distance_error_pct']:+.2f}%)")
        print(f"  Hang time error: {row['hang_time_error']:+.2f} s")
        print()

    print("=" * 70)
    print()

    print("NOTE: This demo uses synthetic data.")
    print("For real calibration, use statcast_calibration.py with actual MLB data.")
    print()

    return binned_df


if __name__ == "__main__":
    results = run_calibration_demo()
