"""
Statcast-based physics calibration module.

This module fetches real MLB Statcast data and compares it against
simulation results to validate and tune aerodynamic constants.

Uses pybaseball to access Statcast batted ball events with:
- Launch speed (exit velocity)
- Launch angle (vertical)
- Hit distance (carry distance)
- Hang time (flight time)

By comparing simulation vs actual outcomes across different launch
conditions, we can identify systematic biases in the physics model
and adjust drag/Magnus coefficients accordingly.
"""

import numpy as np
import pandas as pd
from typing import Dict, List, Tuple, Optional
import warnings
warnings.filterwarnings('ignore')

try:
    from pybaseball import statcast
    PYBASEBALL_AVAILABLE = True
except ImportError:
    PYBASEBALL_AVAILABLE = False
    print("WARNING: pybaseball not available. Install with: pip install pybaseball")

from .trajectory import BattedBallSimulator
from .constants import (
    CD_BASE,
    SPIN_FACTOR,
    CL_MAX,
    TYPICAL_BACKSPIN_OPTIMAL,
    OPTIMAL_LAUNCH_ANGLE,
)


class StatcastCalibrator:
    """
    Calibrates physics model against real Statcast data.

    Workflow:
    1. Fetch Statcast batted ball events for a date range
    2. Filter for quality data (complete measurements)
    3. Bin by exit velocity and launch angle
    4. Compare average actual vs simulated outcomes
    5. Identify systematic deviations
    6. Generate calibration report
    """

    def __init__(self, simulator: Optional[BattedBallSimulator] = None):
        """
        Initialize calibrator.

        Parameters
        ----------
        simulator : BattedBallSimulator, optional
            Physics simulator to validate. If None, creates default.
        """
        if not PYBASEBALL_AVAILABLE:
            raise ImportError("pybaseball required for Statcast calibration")

        self.simulator = simulator or BattedBallSimulator()
        self.statcast_data = None
        self.calibration_results = None

    def fetch_statcast_data(
        self,
        start_date: str,
        end_date: str,
        min_exit_velocity: float = 90.0,
        max_exit_velocity: float = 115.0,
        min_distance: float = 200.0,
    ) -> pd.DataFrame:
        """
        Fetch Statcast batted ball data.

        Parameters
        ----------
        start_date : str
            Start date in 'YYYY-MM-DD' format
        end_date : str
            End date in 'YYYY-MM-DD' format
        min_exit_velocity : float
            Minimum exit velocity to include (mph)
        max_exit_velocity : float
            Maximum exit velocity to include (mph)
        min_distance : float
            Minimum hit distance to include (feet)

        Returns
        -------
        pd.DataFrame
            Filtered Statcast data with complete measurements
        """
        print(f"Fetching Statcast data from {start_date} to {end_date}...")
        print("This may take 30-60 seconds on first run (caching enabled)...")

        # Fetch data from Statcast
        data = statcast(start_dt=start_date, end_dt=end_date)

        print(f"Fetched {len(data)} total batted ball events")

        # Filter for quality data with complete measurements
        filtered = data[
            (data['launch_speed'].notna()) &
            (data['launch_angle'].notna()) &
            (data['hit_distance_sc'].notna()) &
            (data['launch_speed'] >= min_exit_velocity) &
            (data['launch_speed'] <= max_exit_velocity) &
            (data['hit_distance_sc'] >= min_distance)
        ].copy()

        # Rename columns for clarity
        filtered = filtered.rename(columns={
            'launch_speed': 'exit_velocity',
            'launch_angle': 'launch_angle',
            'hit_distance_sc': 'distance',
        })

        # Calculate hang time if not present (some older data may lack it)
        # Hang time not always available, but we'll use it when present
        if 'hang_time' in filtered.columns:
            filtered = filtered[filtered['hang_time'].notna()]

        print(f"Filtered to {len(filtered)} high-quality events")
        print(f"Exit velocity range: {filtered['exit_velocity'].min():.1f} - {filtered['exit_velocity'].max():.1f} mph")
        print(f"Launch angle range: {filtered['launch_angle'].min():.1f} - {filtered['launch_angle'].max():.1f}°")
        print(f"Distance range: {filtered['distance'].min():.1f} - {filtered['distance'].max():.1f} ft")

        self.statcast_data = filtered
        return filtered

    def bin_by_launch_conditions(
        self,
        ev_bins: List[Tuple[float, float]],
        la_bins: List[Tuple[float, float]],
    ) -> pd.DataFrame:
        """
        Bin Statcast data by exit velocity and launch angle ranges.

        Parameters
        ----------
        ev_bins : List[Tuple[float, float]]
            Exit velocity bins [(min1, max1), (min2, max2), ...]
        la_bins : List[Tuple[float, float]]
            Launch angle bins [(min1, max1), (min2, max2), ...]

        Returns
        -------
        pd.DataFrame
            Summary statistics for each bin
        """
        if self.statcast_data is None:
            raise ValueError("Must call fetch_statcast_data() first")

        results = []

        for ev_min, ev_max in ev_bins:
            for la_min, la_max in la_bins:
                # Filter to bin
                bin_data = self.statcast_data[
                    (self.statcast_data['exit_velocity'] >= ev_min) &
                    (self.statcast_data['exit_velocity'] < ev_max) &
                    (self.statcast_data['launch_angle'] >= la_min) &
                    (self.statcast_data['launch_angle'] < la_max)
                ]

                if len(bin_data) < 10:
                    continue  # Skip bins with insufficient data

                # Calculate statistics
                results.append({
                    'ev_min': ev_min,
                    'ev_max': ev_max,
                    'la_min': la_min,
                    'la_max': la_max,
                    'count': len(bin_data),
                    'avg_ev': bin_data['exit_velocity'].mean(),
                    'avg_la': bin_data['launch_angle'].mean(),
                    'avg_distance': bin_data['distance'].mean(),
                    'std_distance': bin_data['distance'].std(),
                    'median_distance': bin_data['distance'].median(),
                    'avg_hang_time': bin_data['hang_time'].mean() if 'hang_time' in bin_data.columns else None,
                })

        return pd.DataFrame(results)

    def compare_with_simulation(
        self,
        binned_data: pd.DataFrame,
        assumed_backspin: float = TYPICAL_BACKSPIN_OPTIMAL,
        assumed_sidespin: float = 0.0,
    ) -> pd.DataFrame:
        """
        Compare Statcast averages with simulation results.

        Parameters
        ----------
        binned_data : pd.DataFrame
            Binned Statcast data from bin_by_launch_conditions()
        assumed_backspin : float
            Backspin to use in simulations (rpm) - Statcast doesn't measure spin
        assumed_sidespin : float
            Sidespin to use in simulations (rpm)

        Returns
        -------
        pd.DataFrame
            Comparison with actual vs simulated distances
        """
        results = binned_data.copy()

        sim_distances = []
        sim_hang_times = []

        for _, row in results.iterrows():
            # Simulate at bin center
            sim_result = self.simulator.simulate(
                exit_velocity=row['avg_ev'],
                launch_angle=row['avg_la'],
                backspin_rpm=assumed_backspin,
                sidespin_rpm=assumed_sidespin,
                spray_angle=0.0,  # Straight to center field
                altitude=0.0,  # Sea level average
                temperature=70.0,  # Standard conditions
            )

            sim_distances.append(sim_result.distance)
            sim_hang_times.append(sim_result.flight_time)

        results['sim_distance'] = sim_distances
        results['sim_hang_time'] = sim_hang_times
        results['distance_error'] = results['sim_distance'] - results['avg_distance']
        results['distance_error_pct'] = 100 * results['distance_error'] / results['avg_distance']

        if results['avg_hang_time'].notna().any():
            results['hang_time_error'] = results['sim_hang_time'] - results['avg_hang_time']

        self.calibration_results = results
        return results

    def analyze_systematic_bias(self) -> Dict[str, float]:
        """
        Analyze systematic biases in the physics model.

        Returns
        -------
        dict
            Summary statistics of model errors
        """
        if self.calibration_results is None:
            raise ValueError("Must call compare_with_simulation() first")

        results = self.calibration_results

        analysis = {
            'mean_distance_error_ft': results['distance_error'].mean(),
            'median_distance_error_ft': results['distance_error'].median(),
            'std_distance_error_ft': results['distance_error'].std(),
            'mean_distance_error_pct': results['distance_error_pct'].mean(),
            'median_distance_error_pct': results['distance_error_pct'].median(),
            'max_overshoot_ft': results['distance_error'].max(),
            'max_undershoot_ft': results['distance_error'].min(),
        }

        # Check for velocity-dependent bias
        high_ev_mask = results['avg_ev'] >= 105
        low_ev_mask = results['avg_ev'] < 95

        if high_ev_mask.any() and low_ev_mask.any():
            analysis['high_ev_bias_ft'] = results[high_ev_mask]['distance_error'].mean()
            analysis['low_ev_bias_ft'] = results[low_ev_mask]['distance_error'].mean()

        # Check for angle-dependent bias
        high_la_mask = results['avg_la'] >= 35
        low_la_mask = results['avg_la'] < 20

        if high_la_mask.any() and low_la_mask.any():
            analysis['high_la_bias_ft'] = results[high_la_mask]['distance_error'].mean()
            analysis['low_la_bias_ft'] = results[low_la_mask]['distance_error'].mean()

        return analysis

    def generate_calibration_report(self) -> str:
        """
        Generate a detailed calibration report.

        Returns
        -------
        str
            Formatted report text
        """
        if self.calibration_results is None:
            raise ValueError("Must run calibration first")

        bias = self.analyze_systematic_bias()

        report = []
        report.append("=" * 70)
        report.append("STATCAST PHYSICS CALIBRATION REPORT")
        report.append("=" * 70)
        report.append("")

        report.append("CURRENT PHYSICS CONSTANTS:")
        report.append(f"  CD_BASE (drag coefficient): {CD_BASE:.4f}")
        report.append(f"  SPIN_FACTOR (Magnus effect): {SPIN_FACTOR:.6f}")
        report.append(f"  CL_MAX (max lift coefficient): {CL_MAX:.4f}")
        report.append("")

        report.append("OVERALL BIAS ANALYSIS:")
        report.append(f"  Mean distance error: {bias['mean_distance_error_ft']:+.2f} ft ({bias['mean_distance_error_pct']:+.2f}%)")
        report.append(f"  Median distance error: {bias['median_distance_error_ft']:+.2f} ft ({bias['median_distance_error_pct']:+.2f}%)")
        report.append(f"  Std dev of errors: {bias['std_distance_error_ft']:.2f} ft")
        report.append(f"  Max overshoot: {bias['max_overshoot_ft']:+.2f} ft")
        report.append(f"  Max undershoot: {bias['max_undershoot_ft']:+.2f} ft")
        report.append("")

        if 'high_ev_bias_ft' in bias:
            report.append("VELOCITY-DEPENDENT BIAS:")
            report.append(f"  High EV (≥105 mph) bias: {bias['high_ev_bias_ft']:+.2f} ft")
            report.append(f"  Low EV (<95 mph) bias: {bias['low_ev_bias_ft']:+.2f} ft")
            report.append("")

        if 'high_la_bias_ft' in bias:
            report.append("ANGLE-DEPENDENT BIAS:")
            report.append(f"  High LA (≥35°) bias: {bias['high_la_bias_ft']:+.2f} ft")
            report.append(f"  Low LA (<20°) bias: {bias['low_la_bias_ft']:+.2f} ft")
            report.append("")

        report.append("INTERPRETATION & RECOMMENDATIONS:")
        report.append("")

        mean_err = bias['mean_distance_error_ft']
        mean_err_pct = bias['mean_distance_error_pct']

        if abs(mean_err_pct) < 2.0:
            report.append(f"  ✓ EXCELLENT: Mean error {mean_err_pct:+.2f}% is within 2% tolerance")
            report.append("    No adjustments recommended - model is well-calibrated")
        elif abs(mean_err_pct) < 5.0:
            report.append(f"  ⚠ GOOD: Mean error {mean_err_pct:+.2f}% is within 5% tolerance")
            report.append("    Minor adjustments could improve accuracy")
        else:
            report.append(f"  ✗ NEEDS CALIBRATION: Mean error {mean_err_pct:+.2f}% exceeds 5%")
            report.append("    Significant adjustments recommended")

        report.append("")

        if mean_err > 10:
            report.append("  RECOMMENDATION: Simulation overshoots distance")
            report.append(f"    - Consider increasing CD_BASE from {CD_BASE:.4f} to {CD_BASE * 1.05:.4f}")
            report.append("    - OR decreasing SPIN_FACTOR (reduces Magnus lift)")
        elif mean_err < -10:
            report.append("  RECOMMENDATION: Simulation undershoots distance")
            report.append(f"    - Consider decreasing CD_BASE from {CD_BASE:.4f} to {CD_BASE * 0.95:.4f}")
            report.append("    - OR increasing SPIN_FACTOR (increases Magnus lift)")

        if 'high_ev_bias_ft' in bias:
            if bias['high_ev_bias_ft'] - bias['low_ev_bias_ft'] > 15:
                report.append("")
                report.append("  VELOCITY-DEPENDENT BIAS DETECTED:")
                report.append("    High EV balls overshoot more than low EV")
                report.append("    This suggests Reynolds number effects on drag coefficient")
                report.append("    Consider velocity-dependent CD modeling")

        report.append("")
        report.append("DETAILED RESULTS BY BIN:")
        report.append("")

        for _, row in self.calibration_results.iterrows():
            report.append(f"  EV: {row['avg_ev']:.1f} mph, LA: {row['avg_la']:.1f}° (n={row['count']})")
            report.append(f"    Actual: {row['avg_distance']:.1f} ± {row['std_distance']:.1f} ft")
            report.append(f"    Simulated: {row['sim_distance']:.1f} ft")
            report.append(f"    Error: {row['distance_error']:+.1f} ft ({row['distance_error_pct']:+.2f}%)")
            report.append("")

        report.append("=" * 70)

        return "\n".join(report)

    def run_full_calibration(
        self,
        start_date: str,
        end_date: str,
        ev_bins: Optional[List[Tuple[float, float]]] = None,
        la_bins: Optional[List[Tuple[float, float]]] = None,
    ) -> str:
        """
        Run complete calibration workflow.

        Parameters
        ----------
        start_date : str
            Start date for Statcast data (YYYY-MM-DD)
        end_date : str
            End date for Statcast data (YYYY-MM-DD)
        ev_bins : List[Tuple[float, float]], optional
            Exit velocity bins. Default: [(90, 95), (95, 100), (100, 105), (105, 110), (110, 115)]
        la_bins : List[Tuple[float, float]], optional
            Launch angle bins. Default: [(15, 20), (20, 25), (25, 30), (30, 35), (35, 40)]

        Returns
        -------
        str
            Calibration report
        """
        # Default bins
        if ev_bins is None:
            ev_bins = [(90, 95), (95, 100), (100, 105), (105, 110), (110, 115)]

        if la_bins is None:
            la_bins = [(15, 20), (20, 25), (25, 30), (30, 35), (35, 40)]

        # Workflow
        self.fetch_statcast_data(start_date, end_date)
        binned = self.bin_by_launch_conditions(ev_bins, la_bins)
        self.compare_with_simulation(binned)
        report = self.generate_calibration_report()

        return report


def quick_calibration_check(start_date: str = "2024-06-01", end_date: str = "2024-06-30") -> str:
    """
    Quick calibration check against one month of Statcast data.

    Parameters
    ----------
    start_date : str
        Start date (default: June 2024)
    end_date : str
        End date (default: June 2024)

    Returns
    -------
    str
        Calibration report
    """
    calibrator = StatcastCalibrator()
    return calibrator.run_full_calibration(start_date, end_date)


if __name__ == "__main__":
    # Run calibration check
    print("Running Statcast calibration...")
    report = quick_calibration_check()
    print(report)

    # Save report
    with open("statcast_calibration_report.txt", "w") as f:
        f.write(report)

    print("\nReport saved to: statcast_calibration_report.txt")
