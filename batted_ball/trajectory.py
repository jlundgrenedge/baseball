"""
Main baseball trajectory simulator.

Combines aerodynamics, environment, and integration to simulate complete
batted ball trajectories.
"""

import numpy as np
from .constants import (
    MPH_TO_MS,
    MS_TO_MPH,
    FEET_TO_METERS,
    METERS_TO_FEET,
    HOME_PLATE_HEIGHT,
    DT_DEFAULT,
    MAX_SIMULATION_TIME,
    GROUND_LEVEL,
)
from .environment import Environment
from .aerodynamics import AerodynamicForces, create_spin_axis
from .integrator import integrate_trajectory, create_initial_state


class BattedBallResult:
    """
    Container for batted ball simulation results.
    """

    def __init__(self, trajectory_data, initial_conditions, environment):
        """
        Initialize result object.

        Parameters
        ----------
        trajectory_data : dict
            Dictionary with trajectory arrays from integrator
        initial_conditions : dict
            Dictionary of initial conditions used
        environment : Environment
            Environment object used in simulation
        """
        self.trajectory_data = trajectory_data
        self.initial_conditions = initial_conditions
        self.environment = environment

        # Extract arrays
        self.time = trajectory_data['time']
        self.position = trajectory_data['position']  # Nx3 array in meters
        self.velocity = trajectory_data['velocity']  # Nx3 array in m/s

        # Calculate derived quantities
        self._calculate_results()

    def _calculate_results(self):
        """Calculate derived quantities from trajectory."""
        # Landing point (last point in trajectory)
        landing_pos = self.position[-1]
        self.landing_x = landing_pos[0] * METERS_TO_FEET  # feet
        self.landing_y = landing_pos[1] * METERS_TO_FEET  # feet
        self.landing_z = landing_pos[2] * METERS_TO_FEET  # feet

        # Distance from home plate (horizontal distance)
        self.distance = np.sqrt(landing_pos[0]**2 + landing_pos[1]**2) * METERS_TO_FEET

        # Flight time
        self.flight_time = self.time[-1]

        # Peak height
        max_z_index = np.argmax(self.position[:, 2])
        self.peak_height = self.position[max_z_index, 2] * METERS_TO_FEET
        self.time_to_peak = self.time[max_z_index]

        # Final velocity
        final_vel = self.velocity[-1]
        self.final_velocity = np.linalg.norm(final_vel) * MS_TO_MPH

        # Spray angle at landing
        self.spray_angle_landing = np.rad2deg(
            np.arctan2(landing_pos[1], landing_pos[0])
        )

    def __repr__(self):
        return (
            f"BattedBallResult(\n"
            f"  distance={self.distance:.1f} ft,\n"
            f"  flight_time={self.flight_time:.2f} s,\n"
            f"  peak_height={self.peak_height:.1f} ft,\n"
            f"  landing=({self.landing_x:.1f}, {self.landing_y:.1f}) ft\n"
            f")"
        )

    def get_trajectory_feet(self):
        """
        Get trajectory in feet for plotting.

        Returns
        -------
        dict
            Dictionary with 'x', 'y', 'z', 'time' in feet and seconds
        """
        return {
            'x': self.position[:, 0] * METERS_TO_FEET,
            'y': self.position[:, 1] * METERS_TO_FEET,
            'z': self.position[:, 2] * METERS_TO_FEET,
            'time': self.time,
        }


class BattedBallSimulator:
    """
    Main simulator for batted baseball trajectories.

    Combines all physics components to simulate realistic ball flight.
    """

    def __init__(self, dt=DT_DEFAULT):
        """
        Initialize simulator.

        Parameters
        ----------
        dt : float
            Time step for integration in seconds
        """
        self.dt = dt

    def simulate(
        self,
        exit_velocity,
        launch_angle,
        spray_angle=0.0,
        backspin_rpm=1800.0,
        sidespin_rpm=0.0,
        altitude=0.0,
        temperature=70.0,
        humidity=0.5,
        wind_speed=0.0,
        wind_direction=0.0,
        initial_height=None,
        initial_position=None,
        cd=None,
        method='rk4',
        max_time=MAX_SIMULATION_TIME
    ):
        """
        Simulate a batted ball trajectory.

        Parameters
        ----------
        exit_velocity : float
            Exit velocity off bat in mph
        launch_angle : float
            Launch angle in degrees (0 = horizontal, 90 = straight up)
        spray_angle : float
            Spray angle in degrees (0 = center field, + = pull, - = oppo)
        backspin_rpm : float
            Backspin rate in rpm (default: 1800)
        sidespin_rpm : float
            Sidespin rate in rpm (default: 0)
        altitude : float
            Altitude in feet above sea level (default: 0)
        temperature : float
            Temperature in Fahrenheit (default: 70)
        humidity : float
            Relative humidity 0-1 (default: 0.5)
        wind_speed : float
            Wind speed in mph, positive = tailwind (default: 0)
        wind_direction : float
            Wind direction in degrees (default: 0 = straight to outfield)
        initial_height : float, optional
            Initial height in feet (default: 3 ft = typical contact height)
        initial_position : tuple, optional
            Initial (x, y, z) position in feet. Overrides initial_height.
        cd : float, optional
            Drag coefficient (default: uses standard value)
        method : str
            Integration method: 'rk4' or 'euler' (default: 'rk4')
        max_time : float
            Maximum simulation time in seconds

        Returns
        -------
        BattedBallResult
            Object containing trajectory and derived quantities
        """
        # Create environment
        env = Environment(altitude, temperature, humidity)

        # Create aerodynamics calculator with air density
        aero = AerodynamicForces(air_density=env.air_density)

        # Create spin axis from backspin and sidespin
        spin_axis, total_spin_rpm = create_spin_axis(backspin_rpm, sidespin_rpm)

        # Convert units
        exit_velocity_ms = exit_velocity * MPH_TO_MS

        # Initial position
        if initial_position is not None:
            pos_x, pos_y, pos_z = initial_position
            initial_pos_m = np.array([
                pos_x * FEET_TO_METERS,
                pos_y * FEET_TO_METERS,
                pos_z * FEET_TO_METERS
            ])
        else:
            if initial_height is None:
                initial_height = 3.0  # feet (typical contact height)
            initial_pos_m = np.array([
                0.0,
                0.0,
                initial_height * FEET_TO_METERS
            ])

        # Create initial state
        initial_state = create_initial_state(
            initial_pos_m,
            exit_velocity_ms,
            launch_angle,
            spray_angle
        )

        # Add wind to initial velocity (if any)
        if abs(wind_speed) > 0.1:
            wind_velocity_ms = wind_speed * MPH_TO_MS
            wind_angle_rad = np.deg2rad(wind_direction)
            wind_vx = wind_velocity_ms * np.cos(wind_angle_rad)
            wind_vy = wind_velocity_ms * np.sin(wind_angle_rad)
            # Wind affects the air velocity relative to ball
            # (not added directly to ball velocity, but affects aerodynamic forces)
            # For simplicity in this version, we'll consider it in the force function

        # Define force function for integration
        def force_function(position, velocity):
            """Calculate aerodynamic forces at given state."""
            # Account for wind (subtract wind from velocity to get relative velocity)
            if abs(wind_speed) > 0.1:
                wind_velocity = np.array([wind_vx, wind_vy, 0.0])
                relative_velocity = velocity - wind_velocity
            else:
                relative_velocity = velocity

            # Calculate aerodynamic forces
            total_force, _, _ = aero.calculate_total_aerodynamic_force(
                relative_velocity,
                spin_axis,
                total_spin_rpm,
                cd=cd
            )

            return total_force

        # Integrate trajectory
        trajectory_data = integrate_trajectory(
            initial_state,
            force_function,
            dt=self.dt,
            max_time=max_time,
            ground_level=GROUND_LEVEL,
            method=method
        )

        # Store initial conditions
        initial_conditions = {
            'exit_velocity': exit_velocity,
            'launch_angle': launch_angle,
            'spray_angle': spray_angle,
            'backspin_rpm': backspin_rpm,
            'sidespin_rpm': sidespin_rpm,
            'total_spin_rpm': total_spin_rpm,
            'altitude': altitude,
            'temperature': temperature,
            'humidity': humidity,
            'wind_speed': wind_speed,
            'wind_direction': wind_direction,
        }

        # Create result object
        result = BattedBallResult(trajectory_data, initial_conditions, env)

        return result

    def simulate_contact(
        self,
        exit_velocity,
        launch_angle,
        spray_angle=0.0,
        backspin_rpm=1800.0,
        sidespin_rpm=0.0,
        contact_quality='sweet_spot',
        contact_vertical_offset=0.0,
        contact_horizontal_offset=0.0,
        **kwargs
    ):
        """
        Simulate with contact point modeling.

        Parameters
        ----------
        exit_velocity : float
            Ideal exit velocity for sweet spot contact (mph)
        launch_angle : float
            Ideal launch angle for sweet spot contact (degrees)
        spray_angle : float
            Spray angle (degrees)
        backspin_rpm : float
            Ideal backspin for sweet spot (rpm)
        sidespin_rpm : float
            Ideal sidespin (rpm)
        contact_quality : str
            'sweet_spot', 'below_center', 'above_center', 'off_center'
        contact_vertical_offset : float
            Vertical offset from sweet spot in inches (+ = above, - = below)
        contact_horizontal_offset : float
            Horizontal offset from sweet spot in inches (+ = toward pull side)
        **kwargs
            Additional arguments passed to simulate()

        Returns
        -------
        BattedBallResult
            Simulation result with adjusted parameters based on contact
        """
        # Import contact module
        from .contact import adjust_for_contact_point

        # Adjust parameters based on contact quality
        adjusted = adjust_for_contact_point(
            exit_velocity,
            launch_angle,
            backspin_rpm,
            sidespin_rpm,
            contact_quality,
            contact_vertical_offset,
            contact_horizontal_offset
        )

        # Run simulation with adjusted parameters
        return self.simulate(
            adjusted['exit_velocity'],
            adjusted['launch_angle'],
            spray_angle,
            adjusted['backspin_rpm'],
            adjusted['sidespin_rpm'],
            **kwargs
        )
