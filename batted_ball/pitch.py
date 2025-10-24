"""
Pitch trajectory simulator for baseball pitches.

Implements realistic pitch physics including:
- Different pitch types (fastball, curveball, slider, changeup)
- Pitch-specific spin characteristics
- Trajectory from mound to plate
- Break and movement calculations
- Integration with collision model

Phase 3 Implementation
"""

import numpy as np
from .constants import (
    GRAVITY,
    MPH_TO_MS,
    MS_TO_MPH,
    FEET_TO_METERS,
    METERS_TO_FEET,
    DEG_TO_RAD,
    RAD_TO_DEG,
    DT_DEFAULT,
    MAX_SIMULATION_TIME,
    GROUND_LEVEL,
    # Mound and plate geometry
    MOUND_DISTANCE,
    MOUND_HEIGHT_FEET,
    RELEASE_HEIGHT,
    RELEASE_EXTENSION,
    STRIKE_ZONE_WIDTH,
    STRIKE_ZONE_BOTTOM,
    STRIKE_ZONE_TOP,
    # Pitch characteristics
    FASTBALL_VELOCITY_AVG,
    FASTBALL_SPIN_AVG,
    CURVEBALL_VELOCITY_AVG,
    CURVEBALL_SPIN_AVG,
    SLIDER_VELOCITY_AVG,
    SLIDER_SPIN_AVG,
    CHANGEUP_VELOCITY_AVG,
    CHANGEUP_SPIN_AVG,
)
from .environment import Environment
from .aerodynamics import AerodynamicForces
from .integrator import integrate_trajectory


class PitchType:
    """
    Definition of a pitch type with characteristic spin and velocity.

    Each pitch type has:
    - Typical velocity range
    - Spin rate and efficiency
    - Spin axis orientation (determines break direction)
    """

    def __init__(self, name, velocity, spin_rpm, spin_axis, spin_efficiency=1.0):
        """
        Initialize pitch type.

        Parameters
        ----------
        name : str
            Name of pitch type (e.g., "Fastball", "Curveball")
        velocity : float
            Typical velocity in mph
        spin_rpm : float
            Spin rate in rpm
        spin_axis : ndarray
            Unit vector for spin axis in (x, y, z)
            Convention: z = vertical, x = toward plate, y = horizontal
        spin_efficiency : float
            Fraction of spin that contributes to Magnus force (0-1)
            Lower efficiency = more seam-shifted wake effects
        """
        self.name = name
        self.velocity = velocity
        self.spin_rpm = spin_rpm
        self.spin_axis = spin_axis / np.linalg.norm(spin_axis)  # Normalize
        self.spin_efficiency = spin_efficiency

    def __repr__(self):
        return (
            f"PitchType(name='{self.name}', velocity={self.velocity:.1f} mph, "
            f"spin={self.spin_rpm:.0f} rpm)"
        )


# ============================================================================
# PITCH TYPE DEFINITIONS
# ============================================================================

def create_fastball_4seam(velocity=None, spin_rpm=None):
    """
    Create a 4-seam fastball.

    Characteristics:
    - High backspin (2000-2700 rpm)
    - Spin axis nearly vertical (perpendicular to velocity)
    - Creates "rise" (actually less drop than gravity alone)
    - Slight arm-side run

    Parameters
    ----------
    velocity : float, optional
        Release velocity in mph (default: 93 mph)
    spin_rpm : float, optional
        Spin rate in rpm (default: 2200 rpm)
    """
    if velocity is None:
        velocity = FASTBALL_VELOCITY_AVG
    if spin_rpm is None:
        spin_rpm = FASTBALL_SPIN_AVG

    # Spin axis: mostly vertical with slight tilt
    # For RHP: tilted slightly toward first base
    # Convention: [toward_plate, horizontal, vertical]
    spin_axis = np.array([0.1, -0.05, 1.0])  # Slight backward and glove-side tilt

    return PitchType("Fastball (4-seam)", velocity, spin_rpm, spin_axis, spin_efficiency=1.0)


def create_fastball_2seam(velocity=None, spin_rpm=None):
    """
    Create a 2-seam fastball (sinker).

    Characteristics:
    - Similar velocity to 4-seam but 1-2 mph slower
    - More horizontal spin component (sidespin)
    - More arm-side run, less vertical "rise"
    - Effective for inducing ground balls
    """
    if velocity is None:
        velocity = FASTBALL_VELOCITY_AVG - 1.5
    if spin_rpm is None:
        spin_rpm = FASTBALL_SPIN_AVG - 200

    # More horizontal tilt than 4-seam
    spin_axis = np.array([0.15, -0.3, 1.0])  # More arm-side tilt

    return PitchType("Fastball (2-seam)", velocity, spin_rpm, spin_axis, spin_efficiency=0.95)


def create_curveball(velocity=None, spin_rpm=None):
    """
    Create a curveball.

    Characteristics:
    - Lower velocity (72-82 mph)
    - High topspin (2200-3200 rpm)
    - Spin axis mostly horizontal (perpendicular to vertical)
    - Large vertical drop, moderate horizontal break
    - "12-6" curve breaks straight down
    """
    if velocity is None:
        velocity = CURVEBALL_VELOCITY_AVG
    if spin_rpm is None:
        spin_rpm = CURVEBALL_SPIN_AVG

    # Spin axis: tilted forward (topspin) and slightly horizontal
    # Pure topspin would be [1, 0, 0]
    # 12-6 curve: [0.9, 0.2, -0.1] (mostly forward, slight glove-side)
    spin_axis = np.array([0.9, 0.2, -0.1])

    return PitchType("Curveball", velocity, spin_rpm, spin_axis, spin_efficiency=0.85)


def create_slider(velocity=None, spin_rpm=None):
    """
    Create a slider.

    Characteristics:
    - Velocity between fastball and curve (82-90 mph)
    - Moderate spin (2200-2800 rpm)
    - Spin axis tilted 45° (mix of side and topspin)
    - Sharp horizontal break (glove side)
    - Moderate vertical drop
    """
    if velocity is None:
        velocity = SLIDER_VELOCITY_AVG
    if spin_rpm is None:
        spin_rpm = SLIDER_SPIN_AVG

    # Spin axis: 45° tilt (gyroscopic)
    # Mostly sidespin (glove-side) with forward tilt
    spin_axis = np.array([0.5, 0.7, 0.0])  # 45° tilt, glove-side

    return PitchType("Slider", velocity, spin_rpm, spin_axis, spin_efficiency=0.75)


def create_changeup(velocity=None, spin_rpm=None):
    """
    Create a changeup.

    Characteristics:
    - Slower velocity (78-88 mph), looks like fastball
    - Lower spin (1500-2000 rpm)
    - Similar spin axis to fastball but less efficient
    - More vertical drop and arm-side fade
    - Relies on velocity differential
    """
    if velocity is None:
        velocity = CHANGEUP_VELOCITY_AVG
    if spin_rpm is None:
        spin_rpm = CHANGEUP_SPIN_AVG

    # Spin axis: similar to fastball but less efficient
    spin_axis = np.array([0.1, -0.15, 1.0])  # Slight arm-side tilt

    return PitchType("Changeup", velocity, spin_rpm, spin_axis, spin_efficiency=0.65)


def create_splitter(velocity=None, spin_rpm=None):
    """
    Create a splitter (split-finger fastball).

    Characteristics:
    - Fastball velocity but very low spin (1000-1500 rpm)
    - Tumbles with unpredictable break
    - Sharp late drop
    - Difficult to control
    """
    if velocity is None:
        velocity = FASTBALL_VELOCITY_AVG - 3.0
    if spin_rpm is None:
        spin_rpm = 1200.0

    # Spin axis: variable, but generally forward tilt
    spin_axis = np.array([0.6, 0.1, 0.3])  # Forward tilt, low efficiency

    return PitchType("Splitter", velocity, spin_rpm, spin_axis, spin_efficiency=0.50)


# ============================================================================
# PITCH RESULT CLASS
# ============================================================================

class PitchResult:
    """
    Container for pitch simulation results.
    """

    def __init__(self, trajectory_data, pitch_type, release_params, environment):
        """
        Initialize pitch result.

        Parameters
        ----------
        trajectory_data : dict
            Trajectory arrays from integrator
        pitch_type : PitchType
            The pitch type used
        release_params : dict
            Release parameters
        environment : Environment
            Environment conditions
        """
        self.trajectory_data = trajectory_data
        self.pitch_type = pitch_type
        self.release_params = release_params
        self.environment = environment

        # Extract arrays
        self.time = trajectory_data['time']
        self.position = trajectory_data['position']  # Nx3 in meters
        self.velocity = trajectory_data['velocity']  # Nx3 in m/s

        # Calculate derived quantities
        self._calculate_results()

    def _calculate_results(self):
        """Calculate pitch characteristics at plate."""
        # Find when pitch crosses home plate (x = 0)
        # Pitch travels in negative x direction (toward plate)
        x_positions = self.position[:, 0]

        # Find crossing point (first time x <= 0)
        plate_crossing_idx = np.where(x_positions <= 0)[0]

        if len(plate_crossing_idx) > 0:
            idx = plate_crossing_idx[0]
            self.crossed_plate = True

            # Interpolate to exact plate crossing
            if idx > 0:
                # Linear interpolation
                x0, x1 = x_positions[idx-1], x_positions[idx]
                t = -x0 / (x1 - x0)  # Fraction between points
                plate_pos = (1-t) * self.position[idx-1] + t * self.position[idx]
                plate_vel = (1-t) * self.velocity[idx-1] + t * self.velocity[idx]
                plate_time = (1-t) * self.time[idx-1] + t * self.time[idx]
            else:
                plate_pos = self.position[idx]
                plate_vel = self.velocity[idx]
                plate_time = self.time[idx]

            # Plate crossing location (in feet)
            self.plate_x = plate_pos[0] * METERS_TO_FEET  # Should be ~0
            self.plate_y = plate_pos[1] * METERS_TO_FEET  # Horizontal location
            self.plate_z = plate_pos[2] * METERS_TO_FEET  # Height

            # Velocity at plate
            self.plate_velocity_vector = plate_vel * MS_TO_MPH
            self.plate_speed = np.linalg.norm(plate_vel) * MS_TO_MPH

            # Flight time to plate
            self.flight_time = plate_time

            # Trajectory angle at plate (degrees below horizontal)
            vx, vy, vz = plate_vel
            self.plate_angle_vertical = np.arctan2(-vz, -vx) * RAD_TO_DEG  # Negative because moving toward plate

            # Check if in strike zone
            in_width = abs(self.plate_y) < STRIKE_ZONE_WIDTH / 2
            in_height = STRIKE_ZONE_BOTTOM <= self.plate_z <= STRIKE_ZONE_TOP
            self.is_strike = in_width and in_height

        else:
            # Pitch didn't reach plate (rare, but possible in weird conditions)
            self.crossed_plate = False
            self.plate_x = self.position[-1, 0] * METERS_TO_FEET
            self.plate_y = self.position[-1, 1] * METERS_TO_FEET
            self.plate_z = self.position[-1, 2] * METERS_TO_FEET
            self.plate_speed = np.linalg.norm(self.velocity[-1]) * MS_TO_MPH
            self.flight_time = self.time[-1]
            self.is_strike = False

        # Calculate break (movement from straight line)
        self._calculate_break()

    def _calculate_break(self):
        """
        Calculate pitch break (deviation from straight line).

        Break is measured as the maximum deviation from a straight line
        connecting release point to plate crossing point.
        """
        # Get release and plate positions
        release_pos = self.position[0]

        if self.crossed_plate:
            # Find plate crossing index
            plate_idx = np.where(self.position[:, 0] <= 0)[0][0]
            plate_pos = self.position[plate_idx]
        else:
            plate_pos = self.position[-1]

        # Straight line from release to plate
        # Parametric: point(t) = release_pos + t * (plate_pos - release_pos), t in [0, 1]

        # Calculate deviation at each point
        max_vertical_dev = 0.0
        max_horizontal_dev = 0.0

        for i in range(len(self.position)):
            pos = self.position[i]

            # Find closest point on straight line
            # Project pos onto line
            vec_to_plate = plate_pos - release_pos
            vec_to_point = pos - release_pos

            # Parameter t for closest point on line
            t = np.dot(vec_to_point, vec_to_plate) / np.dot(vec_to_plate, vec_to_plate)
            t = np.clip(t, 0, 1)  # Clamp to [0, 1]

            # Closest point on line
            closest_point = release_pos + t * vec_to_plate

            # Deviation vector
            deviation = pos - closest_point

            # Vertical deviation (z component)
            vertical_dev = deviation[2]

            # Horizontal deviation (y component)
            horizontal_dev = deviation[1]

            # Track maximum deviations
            max_vertical_dev = max(abs(vertical_dev), abs(max_vertical_dev))
            max_horizontal_dev = max(abs(horizontal_dev), abs(max_horizontal_dev))

        # Convert to inches
        # Positive vertical = rises above straight line
        # Positive horizontal = arm-side (for RHP, toward right)
        self.vertical_break = max_vertical_dev * METERS_TO_FEET * 12.0  # inches
        self.horizontal_break = max_horizontal_dev * METERS_TO_FEET * 12.0  # inches

        # Also calculate total break
        self.total_break = np.sqrt(self.vertical_break**2 + self.horizontal_break**2)

    def __repr__(self):
        strike_str = "Strike" if self.is_strike else "Ball"
        return (
            f"PitchResult({self.pitch_type.name}):\n"
            f"  Location: ({self.plate_y:+.1f}\", {self.plate_z:.1f}\") [{strike_str}]\n"
            f"  Velocity: {self.plate_speed:.1f} mph\n"
            f"  Break: V={self.vertical_break:+.1f}\", H={self.horizontal_break:+.1f}\"\n"
            f"  Flight time: {self.flight_time:.3f} sec"
        )

    def get_trajectory_feet(self):
        """Get trajectory in feet for plotting."""
        return {
            'x': self.position[:, 0] * METERS_TO_FEET,
            'y': self.position[:, 1] * METERS_TO_FEET,
            'z': self.position[:, 2] * METERS_TO_FEET,
            'time': self.time,
        }


# ============================================================================
# PITCH SIMULATOR CLASS
# ============================================================================

class PitchSimulator:
    """
    Simulator for baseball pitches.

    Simulates pitch trajectory from release to home plate using the same
    aerodynamics as batted balls but with pitch-specific spin characteristics.
    """

    def __init__(self, dt=DT_DEFAULT):
        """
        Initialize pitch simulator.

        Parameters
        ----------
        dt : float
            Time step for integration (seconds)
        """
        self.dt = dt

    def simulate(
        self,
        pitch_type,
        target_x=0.0,
        target_z=None,
        release_height=None,
        release_distance=None,
        release_side=0.0,
        altitude=0.0,
        temperature=70.0,
        humidity=0.5,
        method='rk4'
    ):
        """
        Simulate a pitch trajectory.

        Parameters
        ----------
        pitch_type : PitchType
            Type of pitch to throw (use create_fastball(), etc.)
        target_x : float
            Horizontal target location at plate in feet (default: 0 = center)
        target_z : float, optional
            Vertical target height at plate in feet
            (default: middle of strike zone = 2.5 ft)
        release_height : float, optional
            Release height above ground in feet (default: 6.8 ft)
        release_distance : float, optional
            Release distance from plate in feet (default: 54.5 ft)
        release_side : float
            Release point horizontal offset in feet (default: 0 = center)
            Positive = first base side (for RHP, this is natural)
        altitude : float
            Altitude in feet (default: 0 = sea level)
        temperature : float
            Temperature in Fahrenheit (default: 70)
        humidity : float
            Relative humidity 0-1 (default: 0.5)
        method : str
            Integration method: 'rk4' or 'euler'

        Returns
        -------
        PitchResult
            Object containing trajectory and pitch characteristics
        """
        # Default values
        if release_height is None:
            release_height = RELEASE_HEIGHT + MOUND_HEIGHT_FEET
        if release_distance is None:
            release_distance = MOUND_DISTANCE - RELEASE_EXTENSION
        if target_z is None:
            target_z = (STRIKE_ZONE_TOP + STRIKE_ZONE_BOTTOM) / 2.0

        # Create environment
        env = Environment(altitude, temperature, humidity)

        # Create aerodynamics calculator
        aero = AerodynamicForces(air_density=env.air_density)

        # Release position (in meters)
        release_pos_m = np.array([
            release_distance * FEET_TO_METERS,  # Distance from plate
            release_side * FEET_TO_METERS,      # Horizontal offset
            release_height * FEET_TO_METERS     # Height above ground
        ])

        # Target position at plate (in meters)
        target_pos_m = np.array([
            0.0,                          # Home plate
            target_x * FEET_TO_METERS,    # Horizontal location
            target_z * FEET_TO_METERS     # Height
        ])

        # Calculate initial velocity to hit target
        # Account for gravity drop during flight

        # Horizontal distance to plate
        dx = target_pos_m[0] - release_pos_m[0]  # Negative (toward plate)
        dy = target_pos_m[1] - release_pos_m[1]  # Horizontal offset
        dz = target_pos_m[2] - release_pos_m[2]  # Vertical drop

        # Initial velocity magnitude
        v0_mag = pitch_type.velocity * MPH_TO_MS

        # Estimate flight time (rough approximation)
        horizontal_distance = np.sqrt(dx**2 + dy**2)
        flight_time_estimate = abs(horizontal_distance / v0_mag)

        # Calculate gravity drop during flight
        gravity_drop = 0.5 * GRAVITY * flight_time_estimate**2

        # Adjust target height to compensate for gravity
        adjusted_dz = dz + gravity_drop

        # Calculate velocity components
        # vx and vy to cover horizontal distance in flight_time
        vx = dx / flight_time_estimate
        vy = dy / flight_time_estimate
        # vz to cover vertical distance + gravity compensation
        vz = adjusted_dz / flight_time_estimate

        # Normalize to match desired pitch velocity
        v_current = np.sqrt(vx**2 + vy**2 + vz**2)
        scale = v0_mag / v_current

        v0_vec = np.array([vx * scale, vy * scale, vz * scale])

        # Create initial state
        initial_state = np.concatenate([release_pos_m, v0_vec])

        # Spin axis (in pitch coordinates)
        # Apply spin efficiency
        effective_spin_rpm = pitch_type.spin_rpm * pitch_type.spin_efficiency
        spin_axis = pitch_type.spin_axis

        # Define force function
        def force_function(position, velocity):
            """Calculate aerodynamic forces."""
            total_force, _, _ = aero.calculate_total_aerodynamic_force(
                velocity,
                spin_axis,
                effective_spin_rpm
            )
            return total_force

        # Integrate trajectory
        # Stop when pitch crosses plate (x = 0) or hits ground
        def stop_condition(position):
            """Stop when ball crosses plate or hits ground."""
            x, y, z = position
            return x <= 0.0 or z <= GROUND_LEVEL

        trajectory_data = integrate_trajectory(
            initial_state,
            force_function,
            dt=self.dt,
            max_time=2.0,  # Pitch takes ~0.4-0.5 sec, but allow margin
            ground_level=GROUND_LEVEL,
            method=method,
            custom_stop_condition=stop_condition
        )

        # Store release parameters
        release_params = {
            'velocity': pitch_type.velocity,
            'spin_rpm': pitch_type.spin_rpm,
            'spin_axis': pitch_type.spin_axis,
            'release_height': release_height,
            'release_distance': release_distance,
            'release_side': release_side,
            'target_x': target_x,
            'target_z': target_z,
        }

        # Create result
        result = PitchResult(trajectory_data, pitch_type, release_params, env)

        return result

    def simulate_at_batter(
        self,
        pitch_type,
        target_x=0.0,
        target_z=None,
        **kwargs
    ):
        """
        Simulate pitch and return parameters for collision model.

        This is the integration point with Phase 2 collision physics.

        Parameters
        ----------
        pitch_type : PitchType
            Type of pitch
        target_x : float
            Horizontal target location (feet)
        target_z : float
            Vertical target height (feet)
        **kwargs
            Additional arguments passed to simulate()

        Returns
        -------
        dict
            Contains: pitch_speed (mph), pitch_angle (degrees), result (PitchResult)
        """
        result = self.simulate(pitch_type, target_x, target_z, **kwargs)

        return {
            'pitch_speed': result.plate_speed,
            'pitch_angle': result.plate_angle_vertical,
            'result': result,
        }
