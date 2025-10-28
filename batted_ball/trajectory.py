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
    DT_FAST,
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
        
        # Coordinate system conversion:
        # Integrator uses: x=toward outfield, y=lateral (left field positive), z=up
        # Field layout uses: x=lateral (right field positive), y=toward center field, z=up
        # Therefore: field_x = -integrator_y, field_y = integrator_x
        self.landing_x = -landing_pos[1] * METERS_TO_FEET  # Negate for right-handed coords
        self.landing_y = landing_pos[0] * METERS_TO_FEET   # Toward center field
        self.landing_z = landing_pos[2] * METERS_TO_FEET   # Up

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

    @property
    def exit_velocity(self):
        """Exit velocity in mph."""
        return self.initial_conditions['exit_velocity']
    
    @property
    def launch_angle(self):
        """Launch angle in degrees."""
        return self.initial_conditions['launch_angle']
    
    @property
    def backspin_rpm(self):
        """Backspin in rpm."""
        return self.initial_conditions['backspin_rpm']
    
    @property
    def sidespin_rpm(self):
        """Sidespin in rpm."""
        return self.initial_conditions.get('sidespin_rpm', 0)
    
    @property
    def distance_feet(self):
        """Distance in feet (alias for distance)."""
        return self.distance

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
        max_time=MAX_SIMULATION_TIME,
        fast_mode=False
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
        fast_mode : bool
            If True, uses larger time step (2ms vs 1ms) for ~2x speedup
            with minimal accuracy loss (<1%). Recommended for bulk simulations.

        Returns
        -------
        BattedBallResult
            Object containing trajectory and derived quantities
        """
        # Use fast time step if fast_mode is enabled
        dt_to_use = DT_FAST if fast_mode else self.dt

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

        # GROUND BALL PHYSICS CORRECTION
        # For very low launch angles, apply realistic ground ball physics
        is_ground_ball = launch_angle <= 10.0
        
        if is_ground_ball:
            # Apply ground ball trajectory corrections
            initial_state, max_time, use_simplified_physics = self._apply_ground_ball_corrections(
                initial_state, launch_angle, max_time, exit_velocity
            )
        else:
            use_simplified_physics = False

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
            if use_simplified_physics:
                # Ground ball: use minimal aerodynamics (mostly gravity + minimal drag)
                return self._calculate_simplified_ground_ball_forces(velocity, env)
            
            # Regular aerodynamic physics
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
            dt=dt_to_use,
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
    
    def _apply_ground_ball_corrections(self, initial_state, launch_angle, max_time, exit_velocity):
        """
        Apply realistic physics corrections for ground balls.
        
        For very low launch angles (≤10°), the ball behaves more like a 
        bouncing/rolling object than a true projectile. Research shows:
        - 95 mph ground ball travels ~120ft total to 3B in ~0.85-1.0s
        - This implies much shorter flight distance than current simulation
        
        Parameters
        ----------
        initial_state : array
            Initial [position, velocity] state
        launch_angle : float
            Launch angle in degrees
        max_time : float
            Maximum simulation time
        exit_velocity : float
            Exit velocity in mph
            
        Returns
        -------
        tuple
            (corrected_initial_state, corrected_max_time, use_simplified_physics)
        """
        # For ground balls, reduce effective velocity based on launch angle
        # Very low angles lose energy quickly due to ground interaction
        if launch_angle <= 5.0:
            # Very low: 60-70% of velocity (simulates immediate ground interaction)
            velocity_factor = 0.60 + (launch_angle / 5.0) * 0.10  # 0.60-0.70
        elif launch_angle <= 8.0:
            # Low: 70-80% of velocity
            velocity_factor = 0.70 + ((launch_angle - 5.0) / 3.0) * 0.10  # 0.70-0.80
        else:
            # Medium-low: 80-90% of velocity
            velocity_factor = 0.80 + ((launch_angle - 8.0) / 2.0) * 0.10  # 0.80-0.90
        
        # Apply velocity reduction
        corrected_state = initial_state.copy()
        corrected_state[3:6] *= velocity_factor  # Reduce velocity components
        
        # Reduce max simulation time for ground balls (they land much faster)
        corrected_max_time = min(max_time, 1.5)  # Cap at 1.5 seconds
        
        use_simplified_physics = True
        
        return corrected_state, corrected_max_time, use_simplified_physics
    
    def _calculate_simplified_ground_ball_forces(self, velocity, env):
        """
        Calculate simplified forces for ground ball trajectories.
        
        Ground balls experience:
        - Gravity (primary force)
        - Minimal drag (much less than full aerodynamic model)
        - No significant Magnus effect (due to ground interaction)
        
        Parameters
        ----------
        velocity : array
            Current velocity vector [vx, vy, vz] in m/s
        env : Environment
            Environment object for air density
            
        Returns
        -------
        array
            Force vector [Fx, Fy, Fz] in Newtons
        """
        from .constants import BALL_MASS, BALL_CROSS_SECTIONAL_AREA, GRAVITY
        
        # Start with gravity
        force = np.array([0.0, 0.0, -BALL_MASS * GRAVITY])
        
        # Add minimal drag (much reduced compared to full aerodynamics)
        speed = np.linalg.norm(velocity)
        if speed > 0.1:  # Avoid division by zero
            # Use much lower drag coefficient for ground balls
            cd_ground = 0.08  # Much lower than standard ~0.32
            drag_magnitude = 0.5 * env.air_density * cd_ground * BALL_CROSS_SECTIONAL_AREA * speed**2
            drag_direction = -velocity / speed  # Opposite to velocity
            drag_force = drag_magnitude * drag_direction
            force += drag_force
        
        return force


def convert_velocity_trajectory_to_field(vx_traj_ms, vy_traj_ms, vz_traj_ms):
    """
    Convert velocity vector from trajectory/integrator coordinates to field coordinates.

    This is critical for ground ball and fielding calculations to maintain consistent
    coordinate systems across the simulation.

    **Trajectory Coordinate System** (used in physics calculations):
    - X-axis: Direction toward outfield (positive = center field direction)
    - Y-axis: Lateral/spray direction (positive = left field)
    - Z-axis: Vertical (positive = up)

    **Field Coordinate System** (used for positions and fielding):
    - X-axis: Lateral (positive = RIGHT field, negative = LEFT field)
    - Y-axis: Forward direction (positive = toward CENTER field)
    - Z-axis: Vertical (positive = up)

    Parameters
    ----------
    vx_traj_ms : float
        X-component of velocity in trajectory coords (m/s, toward outfield)
    vy_traj_ms : float
        Y-component of velocity in trajectory coords (m/s, lateral, left field positive)
    vz_traj_ms : float
        Z-component of velocity in trajectory coords (m/s, vertical)

    Returns
    -------
    tuple of float
        (vx_field_ms, vy_field_ms, vz_field_ms) - velocity in field coordinates (m/s)
        - vx_field: lateral velocity (positive = toward right field)
        - vy_field: forward velocity (positive = toward center field)
        - vz_field: vertical velocity (unchanged)

    Examples
    --------
    A ball hit up the middle in the integrator (vx=10 m/s, vy=0) becomes:
    >>> convert_velocity_trajectory_to_field(10, 0, 0)
    (0, 10, 0)  # Pure center field direction

    A ball hit to left field (vx=5, vy=10) becomes:
    >>> convert_velocity_trajectory_to_field(5, 10, 0)
    (-10, 5, 0)  # Negative X (left field), positive Y (forward)
    """
    # Coordinate transformation:
    # trajectory_x (toward outfield) -> field_y (toward center field)
    # trajectory_y (left field +) -> -field_x (right field +)
    # trajectory_z stays the same
    vx_field_ms = -vy_traj_ms  # Negate Y for handedness conversion
    vy_field_ms = vx_traj_ms   # Outfield direction becomes forward
    vz_field_ms = vz_traj_ms   # Vertical unchanged

    return vx_field_ms, vy_field_ms, vz_field_ms


def convert_position_trajectory_to_field(x_traj_m, y_traj_m, z_traj_m):
    """
    Convert position vector from trajectory/integrator coordinates to field coordinates.

    Same coordinate transformation as velocity, but applied to positions.
    Used for converting trajectory data positions to field layout coordinates.

    **Trajectory Coordinate System** (used in physics calculations):
    - X-axis: Direction toward outfield (positive = center field direction)
    - Y-axis: Lateral/spray direction (positive = left field)
    - Z-axis: Vertical (positive = up)

    **Field Coordinate System** (used for positions and fielding):
    - X-axis: Lateral (positive = RIGHT field, negative = LEFT field)
    - Y-axis: Forward direction (positive = toward CENTER field)
    - Z-axis: Vertical (positive = up)

    Parameters
    ----------
    x_traj_m : float
        X-component of position in trajectory coords (meters, toward outfield)
    y_traj_m : float
        Y-component of position in trajectory coords (meters, lateral, left field positive)
    z_traj_m : float
        Z-component of position in trajectory coords (meters, vertical)

    Returns
    -------
    tuple of float
        (x_field_m, y_field_m, z_field_m) - position in field coordinates (meters)
        - x_field: lateral position (positive = toward right field)
        - y_field: forward position (positive = toward center field)
        - z_field: vertical position (unchanged)

    Examples
    --------
    A ball at center field 100m out (x=100, y=0):
    >>> convert_position_trajectory_to_field(100, 0, 10)
    (0, 100, 10)  # At center field, 100m forward

    A ball in left field (x=50, y=50):
    >>> convert_position_trajectory_to_field(50, 50, 5)
    (-50, 50, 5)  # Negative X (left field), 50m forward
    """
    # Same transformation as velocity:
    # trajectory_x (toward outfield) -> field_y (toward center field)
    # trajectory_y (left field +) -> -field_x (right field +)
    # trajectory_z stays the same
    x_field_m = -y_traj_m  # Negate Y for handedness conversion
    y_field_m = x_traj_m   # Outfield direction becomes forward
    z_field_m = z_traj_m   # Vertical unchanged

    return x_field_m, y_field_m, z_field_m

