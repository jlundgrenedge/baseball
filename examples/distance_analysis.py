"""
Distance analysis examples.

Analyzes how different factors affect batted ball distance.
"""

import sys
sys.path.insert(0, '..')

import numpy as np
import matplotlib
matplotlib.use('Agg')  # Use non-interactive backend
import matplotlib.pyplot as plt

from batted_ball import BattedBallSimulator


def analyze_exit_velocity_effect():
    """Analyze how exit velocity affects distance."""
    print("Analyzing exit velocity effect...")

    sim = BattedBallSimulator()
    velocities = np.arange(70, 111, 2)  # 70-110 mph
    distances = []

    for ev in velocities:
        result = sim.simulate(
            exit_velocity=float(ev),
            launch_angle=28.0,
            backspin_rpm=1800.0,
        )
        distances.append(result.distance)

    # Plot
    plt.figure(figsize=(10, 6))
    plt.plot(velocities, distances, 'b-', linewidth=2, label='Simulated')

    # Linear fit to show ~5 ft/mph relationship
    coeffs = np.polyfit(velocities, distances, 1)
    fit_line = np.polyval(coeffs, velocities)
    plt.plot(velocities, fit_line, 'r--', label=f'Linear fit: {coeffs[0]:.2f} ft/mph')

    plt.xlabel('Exit Velocity (mph)', fontsize=12)
    plt.ylabel('Distance (feet)', fontsize=12)
    plt.title('Exit Velocity vs Distance', fontsize=14, fontweight='bold')
    plt.legend()
    plt.grid(True, alpha=0.3)
    plt.tight_layout()
    plt.savefig('exit_velocity_analysis.png', dpi=150)
    print(f"  Saved: exit_velocity_analysis.png")
    print(f"  Slope: {coeffs[0]:.2f} ft/mph (expected: ~5 ft/mph)")
    plt.close()


def analyze_launch_angle_effect():
    """Analyze how launch angle affects distance."""
    print("Analyzing launch angle effect...")

    sim = BattedBallSimulator()
    angles = np.arange(5, 51, 1)  # 5-50 degrees
    distances = []

    for angle in angles:
        result = sim.simulate(
            exit_velocity=100.0,
            launch_angle=float(angle),
            backspin_rpm=1800.0,
        )
        distances.append(result.distance)

    # Plot
    plt.figure(figsize=(10, 6))
    plt.plot(angles, distances, 'g-', linewidth=2)

    # Mark optimal angle
    optimal_idx = np.argmax(distances)
    optimal_angle = angles[optimal_idx]
    optimal_distance = distances[optimal_idx]

    plt.plot(optimal_angle, optimal_distance, 'r*', markersize=15,
             label=f'Optimal: {optimal_angle}° → {optimal_distance:.1f} ft')

    plt.xlabel('Launch Angle (degrees)', fontsize=12)
    plt.ylabel('Distance (feet)', fontsize=12)
    plt.title('Launch Angle vs Distance (100 mph exit velo)', fontsize=14, fontweight='bold')
    plt.legend()
    plt.grid(True, alpha=0.3)
    plt.tight_layout()
    plt.savefig('launch_angle_analysis.png', dpi=150)
    print(f"  Saved: launch_angle_analysis.png")
    print(f"  Optimal angle: {optimal_angle}° (expected: ~25-30°)")
    plt.close()


def analyze_backspin_effect():
    """Analyze how backspin affects distance."""
    print("Analyzing backspin effect...")

    sim = BattedBallSimulator()
    spins = np.arange(0, 3001, 100)  # 0-3000 rpm
    distances = []

    for spin in spins:
        result = sim.simulate(
            exit_velocity=100.0,
            launch_angle=28.0,
            backspin_rpm=float(spin),
        )
        distances.append(result.distance)

    # Plot
    plt.figure(figsize=(10, 6))
    plt.plot(spins, distances, 'm-', linewidth=2)

    # Mark saturation point
    plt.axvline(x=2500, color='r', linestyle='--', alpha=0.5,
                label='Spin saturation (~2500 rpm)')

    plt.xlabel('Backspin (rpm)', fontsize=12)
    plt.ylabel('Distance (feet)', fontsize=12)
    plt.title('Backspin vs Distance (100 mph, 28°)', fontsize=14, fontweight='bold')
    plt.legend()
    plt.grid(True, alpha=0.3)
    plt.tight_layout()
    plt.savefig('backspin_analysis.png', dpi=150)
    print(f"  Saved: backspin_analysis.png")
    print(f"  Note: Diminishing returns above ~2500 rpm")
    plt.close()


def analyze_altitude_effect():
    """Analyze how altitude affects distance."""
    print("Analyzing altitude effect...")

    sim = BattedBallSimulator()
    altitudes = np.arange(0, 6001, 500)  # 0-6000 ft
    distances = []

    for alt in altitudes:
        result = sim.simulate(
            exit_velocity=100.0,
            launch_angle=28.0,
            backspin_rpm=1800.0,
            altitude=float(alt),
        )
        distances.append(result.distance)

    # Plot
    plt.figure(figsize=(10, 6))
    plt.plot(altitudes, distances, 'c-', linewidth=2, label='Simulated')

    # Mark Coors Field
    coors_idx = 10  # 5000 ft
    plt.plot(5200, distances[coors_idx], 'r*', markersize=15,
             label=f'Coors Field (5200 ft)')

    # Linear fit
    coeffs = np.polyfit(altitudes, distances, 1)
    fit_line = np.polyval(coeffs, altitudes)
    plt.plot(altitudes, fit_line, 'r--', alpha=0.5,
             label=f'Linear fit: {coeffs[0]*1000:.2f} ft per 1000 ft altitude')

    plt.xlabel('Altitude (feet)', fontsize=12)
    plt.ylabel('Distance (feet)', fontsize=12)
    plt.title('Altitude vs Distance (100 mph, 28°)', fontsize=14, fontweight='bold')
    plt.legend()
    plt.grid(True, alpha=0.3)
    plt.tight_layout()
    plt.savefig('altitude_analysis.png', dpi=150)
    print(f"  Saved: altitude_analysis.png")
    print(f"  Slope: {coeffs[0]*1000:.2f} ft per 1000 ft (expected: ~6 ft/1000 ft)")
    plt.close()


def analyze_temperature_effect():
    """Analyze how temperature affects distance."""
    print("Analyzing temperature effect...")

    sim = BattedBallSimulator()
    temps = np.arange(40, 101, 5)  # 40-100°F
    distances = []

    for temp in temps:
        result = sim.simulate(
            exit_velocity=100.0,
            launch_angle=28.0,
            backspin_rpm=1800.0,
            temperature=float(temp),
        )
        distances.append(result.distance)

    # Plot
    plt.figure(figsize=(10, 6))
    plt.plot(temps, distances, 'orange', linewidth=2, label='Simulated')

    # Linear fit
    coeffs = np.polyfit(temps, distances, 1)
    fit_line = np.polyval(coeffs, temps)
    plt.plot(temps, fit_line, 'r--', alpha=0.5,
             label=f'Linear fit: {coeffs[0]:.3f} ft/°F')

    plt.xlabel('Temperature (°F)', fontsize=12)
    plt.ylabel('Distance (feet)', fontsize=12)
    plt.title('Temperature vs Distance (100 mph, 28°)', fontsize=14, fontweight='bold')
    plt.legend()
    plt.grid(True, alpha=0.3)
    plt.tight_layout()
    plt.savefig('temperature_analysis.png', dpi=150)
    print(f"  Saved: temperature_analysis.png")
    print(f"  Slope: {coeffs[0]:.3f} ft/°F (expected: ~0.35 ft/°F)")
    plt.close()


def plot_3d_trajectory():
    """Plot a 3D trajectory."""
    print("Creating 3D trajectory plot...")

    sim = BattedBallSimulator()
    result = sim.simulate(
        exit_velocity=105.0,
        launch_angle=28.0,
        spray_angle=15.0,  # Pull side
        backspin_rpm=1800.0,
    )

    traj = result.get_trajectory_feet()

    # Create 3D plot
    fig = plt.figure(figsize=(12, 8))
    ax = fig.add_subplot(111, projection='3d')

    ax.plot(traj['x'], traj['y'], traj['z'], 'b-', linewidth=2, label='Ball trajectory')

    # Mark start and end
    ax.plot([traj['x'][0]], [traj['y'][0]], [traj['z'][0]], 'go',
            markersize=10, label='Contact')
    ax.plot([traj['x'][-1]], [traj['y'][-1]], [traj['z'][-1]], 'ro',
            markersize=10, label='Landing')

    ax.set_xlabel('Distance to Outfield (ft)', fontsize=10)
    ax.set_ylabel('Lateral Distance (ft)', fontsize=10)
    ax.set_zlabel('Height (ft)', fontsize=10)
    ax.set_title('3D Batted Ball Trajectory\n(105 mph, 28°, 15° pull)',
                 fontsize=12, fontweight='bold')
    ax.legend()
    plt.tight_layout()
    plt.savefig('trajectory_3d.png', dpi=150)
    print(f"  Saved: trajectory_3d.png")
    plt.close()


def main():
    """Run all distance analyses."""
    print("=" * 70)
    print("BATTED BALL DISTANCE ANALYSIS")
    print("=" * 70)
    print()

    analyze_exit_velocity_effect()
    print()

    analyze_launch_angle_effect()
    print()

    analyze_backspin_effect()
    print()

    analyze_altitude_effect()
    print()

    analyze_temperature_effect()
    print()

    plot_3d_trajectory()
    print()

    print("=" * 70)
    print("Analysis complete! Check the generated PNG files.")
    print("=" * 70)


if __name__ == '__main__':
    main()
