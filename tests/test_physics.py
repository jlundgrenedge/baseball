"""
Unit tests for batted ball physics simulator.
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

import unittest
import numpy as np

from batted_ball import BattedBallSimulator
from batted_ball.environment import Environment, calculate_air_density
from batted_ball.aerodynamics import AerodynamicForces, create_spin_axis
from batted_ball.constants import GRAVITY, BALL_MASS


class TestEnvironment(unittest.TestCase):
    """Test environment module."""

    def test_sea_level_density(self):
        """Test air density at sea level is reasonable."""
        env = Environment(altitude_ft=0.0, temperature_f=70.0)
        # Should be close to 1.2 kg/m³
        self.assertAlmostEqual(env.air_density, 1.2, delta=0.1)

    def test_altitude_reduces_density(self):
        """Test that altitude reduces air density."""
        env_sea = Environment(altitude_ft=0.0, temperature_f=70.0)
        env_coors = Environment(altitude_ft=5200.0, temperature_f=70.0)
        self.assertLess(env_coors.air_density, env_sea.air_density)

    def test_temperature_affects_density(self):
        """Test that temperature affects air density."""
        env_cold = Environment(altitude_ft=0.0, temperature_f=40.0)
        env_hot = Environment(altitude_ft=0.0, temperature_f=90.0)
        # Cold air is denser
        self.assertGreater(env_cold.air_density, env_hot.air_density)


class TestAerodynamics(unittest.TestCase):
    """Test aerodynamics module."""

    def test_drag_opposes_velocity(self):
        """Test that drag force opposes velocity."""
        aero = AerodynamicForces(air_density=1.2)
        velocity = np.array([40.0, 0.0, 0.0])  # Moving in +x direction
        drag = aero.calculate_drag_force(velocity)

        # Drag should be in -x direction
        self.assertLess(drag[0], 0.0)
        self.assertAlmostEqual(drag[1], 0.0, places=10)
        self.assertAlmostEqual(drag[2], 0.0, places=10)

    def test_drag_increases_with_velocity(self):
        """Test that drag force increases with velocity squared."""
        aero = AerodynamicForces(air_density=1.2)

        v1 = np.array([20.0, 0.0, 0.0])
        v2 = np.array([40.0, 0.0, 0.0])  # 2x velocity

        drag1 = aero.calculate_drag_force(v1)
        drag2 = aero.calculate_drag_force(v2)

        # Drag should be ~4x for 2x velocity
        drag1_mag = np.linalg.norm(drag1)
        drag2_mag = np.linalg.norm(drag2)
        ratio = drag2_mag / drag1_mag
        self.assertAlmostEqual(ratio, 4.0, delta=0.1)

    def test_magnus_force_perpendicular(self):
        """Test that Magnus force is perpendicular to velocity."""
        aero = AerodynamicForces(air_density=1.2)

        velocity = np.array([40.0, 0.0, 10.0])  # Moving in x-z plane
        spin_axis = np.array([0.0, 1.0, 0.0])  # Spinning around y-axis
        spin_rpm = 1800.0

        magnus = aero.calculate_magnus_force(velocity, spin_axis, spin_rpm)

        # Magnus force should be perpendicular to velocity
        dot_product = np.dot(magnus, velocity)
        self.assertAlmostEqual(dot_product, 0.0, delta=1.0)

    def test_spin_axis_creation(self):
        """Test creation of spin axis from backspin/sidespin."""
        spin_axis, total_rpm = create_spin_axis(
            backspin_rpm=1800.0,
            sidespin_rpm=0.0
        )

        # Pure backspin: axis should be in y-direction
        self.assertAlmostEqual(total_rpm, 1800.0, delta=0.1)
        self.assertAlmostEqual(np.linalg.norm(spin_axis), 1.0, places=10)


class TestSimulator(unittest.TestCase):
    """Test main simulator."""

    def test_basic_simulation(self):
        """Test that basic simulation completes successfully."""
        sim = BattedBallSimulator()
        result = sim.simulate(
            exit_velocity=100.0,
            launch_angle=28.0,
            backspin_rpm=1800.0,
        )

        # Check that we got reasonable results
        self.assertGreater(result.distance, 300.0)  # At least 300 feet
        self.assertLess(result.distance, 500.0)     # Less than 500 feet
        self.assertGreater(result.flight_time, 3.0)  # At least 3 seconds
        self.assertLess(result.flight_time, 8.0)    # Less than 8 seconds

    def test_higher_velocity_increases_distance(self):
        """Test that higher exit velocity increases distance."""
        sim = BattedBallSimulator()

        result1 = sim.simulate(
            exit_velocity=90.0,
            launch_angle=28.0,
            backspin_rpm=1800.0,
        )

        result2 = sim.simulate(
            exit_velocity=100.0,
            launch_angle=28.0,
            backspin_rpm=1800.0,
        )

        self.assertGreater(result2.distance, result1.distance)

    def test_altitude_increases_distance(self):
        """Test that higher altitude increases distance."""
        sim = BattedBallSimulator()

        result_sea = sim.simulate(
            exit_velocity=100.0,
            launch_angle=28.0,
            backspin_rpm=1800.0,
            altitude=0.0,
        )

        result_coors = sim.simulate(
            exit_velocity=100.0,
            launch_angle=28.0,
            backspin_rpm=1800.0,
            altitude=5200.0,
        )

        self.assertGreater(result_coors.distance, result_sea.distance)

    def test_backspin_increases_distance(self):
        """Test that backspin increases distance."""
        sim = BattedBallSimulator()

        result_no_spin = sim.simulate(
            exit_velocity=100.0,
            launch_angle=28.0,
            backspin_rpm=0.0,
        )

        result_with_spin = sim.simulate(
            exit_velocity=100.0,
            launch_angle=28.0,
            backspin_rpm=1800.0,
        )

        self.assertGreater(result_with_spin.distance, result_no_spin.distance)


def run_tests():
    """Run all unit tests."""
    unittest.main(argv=[''], exit=False, verbosity=2)


if __name__ == '__main__':
    run_tests()
