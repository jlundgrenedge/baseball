from batted_ball.statcast_calibration import StatcastCalibrator
from batted_ball.constants import TYPICAL_BACKSPIN_OPTIMAL
import pandas as pd

def estimate_backspin_from_launch_angle(launch_angle_deg):
    """
    Estimate typical backspin based on launch angle.

    Based on empirical patterns:
    - Line drives (10-20°): Less backspin, more topspin component
    - Fly balls (25-35°): Optimal backspin
    - Pop-ups (>40°): High backspin
    """
    if launch_angle_deg < 20:
        # Line drives: 600-1200 rpm
        return 600.0 + 30.0 * launch_angle_deg
    elif launch_angle_deg < 35:
        # Fly balls: 1200-1950 rpm (linear interpolation)
        return 1200.0 + 50.0 * (launch_angle_deg - 20)
    else:
        # Pop-ups: 1950-2700 rpm
        return 1950.0 + 50.0 * (launch_angle_deg - 35)

# Initialize calibrator
calibrator = StatcastCalibrator()

# Fetch data
print("Fetching Statcast data...")
data = calibrator.fetch_statcast_data(
    start_date='2024-06-01',
    end_date='2024-06-30',
    min_exit_velocity=90.0,
    min_distance=200.0
)

# Bin by launch conditions
ev_bins = [(90, 95), (95, 100), (100, 105), (105, 110), (110, 115)]
la_bins = [(15, 20), (20, 25), (25, 30), (30, 35), (35, 40)]

print("\nBinning data...")
binned = calibrator.bin_by_launch_conditions(ev_bins, la_bins)

# Compare with simulation using ANGLE-DEPENDENT SPIN
print("\nRunning simulations with launch-angle-dependent spin...")

from batted_ball.trajectory import BattedBallSimulator

sim = BattedBallSimulator()
sim_distances = []
sim_hang_times = []
spin_estimates = []

for _, row in binned.iterrows():
    # Estimate spin based on launch angle
    estimated_spin = estimate_backspin_from_launch_angle(row['avg_la'])
    spin_estimates.append(estimated_spin)

    # Simulate with estimated spin
    result = sim.simulate(
        exit_velocity=row['avg_ev'],
        launch_angle=row['avg_la'],
        backspin_rpm=estimated_spin,  # <-- KEY CHANGE: angle-dependent!
        sidespin_rpm=0.0,
        spray_angle=0.0,
        altitude=0.0,
        temperature=70.0
    )

    sim_distances.append(result.distance)
    sim_hang_times.append(result.flight_time)

binned['estimated_spin'] = spin_estimates
binned['sim_distance'] = sim_distances
binned['sim_hang_time'] = sim_hang_times
binned['distance_error'] = binned['sim_distance'] - binned['avg_distance']
binned['distance_error_pct'] = 100 * binned['distance_error'] / binned['avg_distance']

# Generate report
print("\n" + "="*70)
print("STATCAST CALIBRATION WITH ANGLE-DEPENDENT SPIN")
print("="*70)
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
    print()

# Interpretation
mean_err_pct = binned['distance_error_pct'].mean()
if abs(mean_err_pct) < 2.0:
    print("INTERPRETATION:")
    print(f"  ✓ EXCELLENT: Mean error {mean_err_pct:+.2f}% is within 2% tolerance")
elif abs(mean_err_pct) < 5.0:
    print("INTERPRETATION:")
    print(f"  ⚠ GOOD: Mean error {mean_err_pct:+.2f}% is within 5% tolerance")
else:
    print("INTERPRETATION:")
    print(f"  ✗ NEEDS CALIBRATION: Mean error {mean_err_pct:+.2f}% exceeds 5%")
print()

print("="*70)
print("DETAILED RESULTS BY BIN")
print("="*70)
print()

for _, row in binned.iterrows():
    print(f"EV: {row['avg_ev']:.1f} mph, LA: {row['avg_la']:.1f}° (n={row['count']})")
    print(f"  Actual: {row['avg_distance']:.1f} ± {row['std_distance']:.1f} ft")
    print(f"  Simulated: {row['sim_distance']:.1f} ft (using {row['estimated_spin']:.0f} rpm backspin)")
    print(f"  Error: {row['distance_error']:+.1f} ft ({row['distance_error_pct']:+.2f}%)")
    print()

print("="*70)
print()

# Save results
binned.to_csv('calibration_with_angle_dependent_spin.csv', index=False)
print("Results saved to: calibration_with_angle_dependent_spin.csv")
