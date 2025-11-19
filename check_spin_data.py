from batted_ball.statcast_calibration import StatcastCalibrator

# Fetch the data
calibrator = StatcastCalibrator()
data = calibrator.fetch_statcast_data(
    start_date='2024-06-01',
    end_date='2024-06-30',
    min_exit_velocity=90.0,
    min_distance=200.0
)

# Check what columns we have
print("Available columns:")
print(data.columns.tolist())
print()

# Check for spin-related columns
spin_columns = [col for col in data.columns if 'spin' in col.lower()]
print(f"Spin-related columns found: {spin_columns}")
print()

# Check how much spin data we have
for col in spin_columns:
    total = len(data)
    non_null = data[col].notna().sum()
    pct = 100 * non_null / total
    print(f"{col}: {non_null}/{total} ({pct:.1f}%) have data")
    if non_null > 0:
        print(f"  Range: {data[col].min():.0f} - {data[col].max():.0f} rpm")
        print(f"  Mean: {data[col].mean():.0f} rpm")
print()

# If we have batted ball spin, show correlation with launch angle
if 'hit_spin_rate' in data.columns and data['hit_spin_rate'].notna().sum() > 100:
    print("Correlation between launch angle and spin:")
    spin_data = data[data['hit_spin_rate'].notna()]

    # Bin by launch angle
    for la_min in range(15, 40, 5):
        la_max = la_min + 5
        bin_data = spin_data[
            (spin_data['launch_angle'] >= la_min) &
            (spin_data['launch_angle'] < la_max)
        ]
        if len(bin_data) > 10:
            avg_spin = bin_data['hit_spin_rate'].mean()
            std_spin = bin_data['hit_spin_rate'].std()
            print(f"  {la_min}-{la_max}°: {avg_spin:.0f} ± {std_spin:.0f} rpm (n={len(bin_data)})")
