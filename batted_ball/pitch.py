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
    RELEASE_EXTENSION_AVG,
    RELEASE_EXTENSION_MAX,
    STRIKE_ZONE_WIDTH,
    STRIKE_ZONE_BOTTOM,
    STRIKE_ZONE_TOP,
    # Pitch characteristics
    FASTBALL_4SEAM_VELOCITY_AVG,
    FASTBALL_4SEAM_SPIN_AVG,
    FASTBALL_2SEAM_VELOCITY_AVG,
    FASTBALL_2SEAM_SPIN_AVG,
    CUTTER_VELOCITY_AVG,
    CUTTER_SPIN_AVG,
    CURVEBALL_VELOCITY_AVG,
    CURVEBALL_SPIN_AVG,
    SLIDER_VELOCITY_AVG,
    SLIDER_SPIN_AVG,
    CHANGEUP_VELOCITY_AVG,
    CHANGEUP_SPIN_AVG,
    SPLITTER_VELOCITY_AVG,
    SPLITTER_SPIN_AVG,
    KNUCKLEBALL_VELOCITY_AVG,
    KNUCKLEBALL_SPIN_AVG,
    # Spin efficiency
    SPIN_EFFICIENCY_4SEAM,
    SPIN_EFFICIENCY_2SEAM,
    SPIN_EFFICIENCY_CUTTER,
    SPIN_EFFICIENCY_CURVEBALL,
    SPIN_EFFICIENCY_SLIDER,
    SPIN_EFFICIENCY_CHANGEUP,
    SPIN_EFFICIENCY_SPLITTER,
    SPIN_EFFICIENCY_KNUCKLEBALL,
    # Environmental effects
    PITCH_BREAK_REDUCTION_PER_1000_FT,
    PITCH_BREAK_CHANGE_PER_10_DEG_F,
    EXTENSION_PERCEIVED_VELOCITY_BOOST_PER_FOOT,
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

    Characteristics (from MLB Statcast data):
    - Velocity: 88-102 mph (avg 93 mph)
    - Spin: 1800-2700 rpm (avg 2200 rpm)
    - Spin efficiency: 90% (very efficient backspin)
    - Spin axis nearly vertical (perpendicular to velocity)
    - Creates "rise" (actually less drop than gravity alone)
    - Slight arm-side run (~2" horizontal break)
    - ~16" of vertical "rise" relative to spinless trajectory

    Research notes:
    - High spin fastballs up in the zone get more swings and misses
    - Batters tend to swing under high-spin fastballs
    - Elite spin: >2400 rpm (generates ~18-20" of rise)

    Parameters
    ----------
    velocity : float, optional
        Release velocity in mph (default: 93 mph)
    spin_rpm : float, optional
        Spin rate in rpm (default: 2200 rpm)
    """
    if velocity is None:
        velocity = FASTBALL_4SEAM_VELOCITY_AVG
    if spin_rpm is None:
        spin_rpm = FASTBALL_4SEAM_SPIN_AVG

    # Spin axis: mostly vertical with slight tilt
    # For RHP: tilted slightly toward first base
    # Convention: [toward_plate, horizontal, vertical]
    spin_axis = np.array([0.1, -0.05, 1.0])  # Slight backward and glove-side tilt

    return PitchType("Fastball (4-seam)", velocity, spin_rpm, spin_axis,
                     spin_efficiency=SPIN_EFFICIENCY_4SEAM)


def create_fastball_2seam(velocity=None, spin_rpm=None):
    """
    Create a 2-seam fastball (sinker).

    Characteristics (from MLB Statcast data):
    - Velocity: 88-95 mph (avg 92 mph)
    - Spin: 1800-2500 rpm (avg 2100 rpm)
    - Spin efficiency: 89% (efficient with slight tilt)
    - More horizontal spin component (sidespin)
    - More arm-side run (~8" horizontal), less vertical "rise" (~10")
    - Effective for inducing ground balls

    Research notes:
    - Low spin sinkers produce more ground balls
    - Tilted spin axis creates both sink and arm-side movement
    - Wily Peralta's 1740 rpm sinker had extreme ground ball rate
    - High spin sinkers act more like straight fastballs (less effective)

    Parameters
    ----------
    velocity : float, optional
        Release velocity in mph (default: 92 mph)
    spin_rpm : float, optional
        Spin rate in rpm (default: 2100 rpm)
    """
    if velocity is None:
        velocity = FASTBALL_2SEAM_VELOCITY_AVG
    if spin_rpm is None:
        spin_rpm = FASTBALL_2SEAM_SPIN_AVG

    # More horizontal tilt than 4-seam
    spin_axis = np.array([0.15, -0.3, 1.0])  # More arm-side tilt

    return PitchType("Fastball (2-seam)", velocity, spin_rpm, spin_axis,
                     spin_efficiency=SPIN_EFFICIENCY_2SEAM)


def create_cutter(velocity=None, spin_rpm=None):
    """
    Create a cutter (cut fastball).

    Characteristics (from MLB Statcast data):
    - Velocity: 85-95 mph (avg 88 mph)
    - Spin: 2000-2600 rpm (avg 2200 rpm)
    - Spin efficiency: 49% (partial gyro spin)
    - Slightly tilted backspin (between 4-seam and slider)
    - Late glove-side cut (~3" horizontal)
    - Moderate drop (~6" vertical)

    Research notes:
    - Mariano Rivera's cutter: ~2500 rpm, tight 3-5" glove-side break
    - High spin helps maximize late movement
    - Essentially a "small slider" - faster with tighter break
    - Effective for sawing off bats

    Parameters
    ----------
    velocity : float, optional
        Release velocity in mph (default: 88 mph)
    spin_rpm : float, optional
        Spin rate in rpm (default: 2200 rpm)
    """
    if velocity is None:
        velocity = CUTTER_VELOCITY_AVG
    if spin_rpm is None:
        spin_rpm = CUTTER_SPIN_AVG

    # Spin axis: between fastball and slider (slight glove-side tilt)
    spin_axis = np.array([0.3, 0.3, 1.0])  # Tilted toward glove side

    return PitchType("Cutter", velocity, spin_rpm, spin_axis,
                     spin_efficiency=SPIN_EFFICIENCY_CUTTER)


def create_curveball(velocity=None, spin_rpm=None):
    """
    Create a curveball.

    Characteristics (from MLB Statcast data):
    - Velocity: 70-82 mph (avg 78 mph)
    - Spin: 2200-3200 rpm (avg 2500 rpm)
    - Spin efficiency: 69% (good topspin efficiency)
    - Spin axis mostly horizontal (perpendicular to vertical)
    - Large vertical drop (~12" below spinless trajectory)
    - Moderate horizontal break (~6" glove-side)
    - "12-6" curve breaks straight down

    Research notes:
    - Garrett Richards: 3086 rpm curveball, extreme drop
    - High spin curves dive more sharply
    - Overhand delivery produces pure 12-6 break
    - 3/4 arm angle produces more horizontal "slurve" movement

    Parameters
    ----------
    velocity : float, optional
        Release velocity in mph (default: 78 mph)
    spin_rpm : float, optional
        Spin rate in rpm (default: 2500 rpm)
    """
    if velocity is None:
        velocity = CURVEBALL_VELOCITY_AVG
    if spin_rpm is None:
        spin_rpm = CURVEBALL_SPIN_AVG

    # Spin axis: tilted forward (topspin) and slightly horizontal
    # Pure topspin would be [1, 0, 0]
    # 12-6 curve: [0.9, 0.2, -0.1] (mostly forward, slight glove-side)
    spin_axis = np.array([0.9, 0.2, -0.1])

    return PitchType("Curveball", velocity, spin_rpm, spin_axis,
                     spin_efficiency=SPIN_EFFICIENCY_CURVEBALL)


def create_slider(velocity=None, spin_rpm=None):
    """
    Create a slider.

    Characteristics (from MLB Statcast data):
    - Velocity: 78-91 mph (avg 85 mph)
    - Spin: 1800-2800 rpm (avg 2400 rpm)
    - Spin efficiency: 36% (mostly gyro spin - "bullet spin")
    - Spin axis tilted 45° (mix of side and topspin)
    - Sharp horizontal break (~5" glove-side)
    - Moderate vertical drop (~2")

    Research notes:
    - Low spin efficiency (30-40%) is typical for sliders
    - Gyro spin creates lateral break without much Magnus lift
    - Harder sliders have less drop, slower ones sweep more
    - Effective chase pitch - starts in zone, breaks out

    Parameters
    ----------
    velocity : float, optional
        Release velocity in mph (default: 85 mph)
    spin_rpm : float, optional
        Spin rate in rpm (default: 2400 rpm)
    """
    if velocity is None:
        velocity = SLIDER_VELOCITY_AVG
    if spin_rpm is None:
        spin_rpm = SLIDER_SPIN_AVG

    # Spin axis: 45° tilt (gyroscopic)
    # Mostly sidespin (glove-side) with forward tilt
    spin_axis = np.array([0.5, 0.7, 0.0])  # 45° tilt, glove-side

    return PitchType("Slider", velocity, spin_rpm, spin_axis,
                     spin_efficiency=SPIN_EFFICIENCY_SLIDER)


def create_changeup(velocity=None, spin_rpm=None):
    """
    Create a changeup.

    Characteristics (from MLB Statcast data):
    - Velocity: 75-88 mph (avg 84 mph), typically 8-10 mph slower than fastball
    - Spin: 1400-2100 rpm (avg 1750 rpm)
    - Spin efficiency: 89% (similar to fastball but lower rpm)
    - Similar spin axis to fastball but less efficient
    - More vertical drop (~8") and arm-side fade (~14")
    - Relies on velocity differential and deception

    Research notes:
    - Key is deception - should look like fastball until it "dies"
    - Circle change grip creates slight sidespin for fade
    - Gravity has more time to act due to lower velocity
    - Effective for inducing weak contact and ground balls

    Parameters
    ----------
    velocity : float, optional
        Release velocity in mph (default: 84 mph)
    spin_rpm : float, optional
        Spin rate in rpm (default: 1750 rpm)
    """
    if velocity is None:
        velocity = CHANGEUP_VELOCITY_AVG
    if spin_rpm is None:
        spin_rpm = CHANGEUP_SPIN_AVG

    # Spin axis: similar to fastball but less efficient
    spin_axis = np.array([0.1, -0.15, 1.0])  # Slight arm-side tilt

    return PitchType("Changeup", velocity, spin_rpm, spin_axis,
                     spin_efficiency=SPIN_EFFICIENCY_CHANGEUP)


def create_splitter(velocity=None, spin_rpm=None):
    """
    Create a splitter (split-finger fastball).

    Characteristics (from MLB Statcast data):
    - Velocity: 80-90 mph (avg 85 mph)
    - Spin: 1000-1800 rpm (avg 1500 rpm) - very low
    - Spin efficiency: 50% (tumbling action)
    - Grip kills spin, creating "knuckle effect"
    - Sharp late drop (~10" below spinless trajectory)
    - Minimal horizontal movement (~2")
    - "Bottom falls out" late in flight

    Research notes:
    - Mike Pelfrey's splitter: 830 rpm, extreme ground ball pitch
    - Low spin means gravity dominates (minimal Magnus force)
    - Effective for inducing weak contact and ground balls
    - Difficult to control due to unpredictable break

    Parameters
    ----------
    velocity : float, optional
        Release velocity in mph (default: 85 mph)
    spin_rpm : float, optional
        Spin rate in rpm (default: 1500 rpm)
    """
    if velocity is None:
        velocity = SPLITTER_VELOCITY_AVG
    if spin_rpm is None:
        spin_rpm = SPLITTER_SPIN_AVG

    # Spin axis: variable, but generally forward tilt
    spin_axis = np.array([0.6, 0.1, 0.3])  # Forward tilt, low efficiency

    return PitchType("Splitter", velocity, spin_rpm, spin_axis,
                     spin_efficiency=SPIN_EFFICIENCY_SPLITTER)


def create_knuckleball(velocity=None, spin_rpm=None):
    """
    Create a knuckleball.

    Characteristics (from MLB Statcast data):
    - Velocity: 65-80 mph (avg 72 mph)
    - Spin: 50-500 rpm (avg 200 rpm) - extremely low
    - Spin efficiency: 10% (chaotic, minimal Magnus)
    - Almost no spin (ideally 1-3 rotations during flight)
    - Unpredictable flutter and zig-zag movement
    - Random lateral and vertical deviations

    Research notes:
    - Without spin, Magnus effect vanishes
    - Ball's trajectory dominated by chaotic airflow around seams
    - Asymmetric turbulence causes unpredictable movement
    - Even pitcher doesn't know exact break
    - If spin >500 rpm, acts like slow batting practice fastball
    - Very difficult to throw and catch

    Parameters
    ----------
    velocity : float, optional
        Release velocity in mph (default: 72 mph)
    spin_rpm : float, optional
        Spin rate in rpm (default: 200 rpm)
    """
    if velocity is None:
        velocity = KNUCKLEBALL_VELOCITY_AVG
    if spin_rpm is None:
        spin_rpm = KNUCKLEBALL_SPIN_AVG

    # Spin axis: random/variable (doesn't matter much with so little spin)
    # Add randomness to simulate unpredictability
    spin_axis = np.random.randn(3)
    spin_axis = spin_axis / np.linalg.norm(spin_axis) if np.linalg.norm(spin_axis) > 0 else np.array([0, 0, 1])

    return PitchType("Knuckleball", velocity, spin_rpm, spin_axis,
                     spin_efficiency=SPIN_EFFICIENCY_KNUCKLEBALL)


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

        # Spin parameters (needed for iteration)
        effective_spin_rpm = pitch_type.spin_rpm * pitch_type.spin_efficiency
        spin_axis = pitch_type.spin_axis

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
        # Use iterative approach to compensate for Magnus force drift
        # This ensures the pitch actually goes where intended despite spin effects

        # Initial velocity magnitude
        v0_mag = pitch_type.velocity * MPH_TO_MS

        # Start with simple ballistic aim (no Magnus compensation)
        aim_point_m = target_pos_m.copy()

        # Iteratively refine aim to hit actual target
        for iteration in range(5):  # 5 iterations for good convergence
            # Horizontal distance to aim point
            dx = aim_point_m[0] - release_pos_m[0]  # Negative (toward plate)
            dy = aim_point_m[1] - release_pos_m[1]  # Horizontal offset
            dz = aim_point_m[2] - release_pos_m[2]  # Vertical drop

            # Estimate flight time
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

            v0_vec_test = np.array([vx * scale, vy * scale, vz * scale])

            # Quick trajectory simulation to see where this actually goes
            test_state = np.concatenate([release_pos_m, v0_vec_test])

            def test_force(position, velocity):
                total_force, _, _ = aero.calculate_total_aerodynamic_force(
                    velocity, spin_axis, effective_spin_rpm
                )
                return total_force

            def test_stop(position):
                x, y, z = position
                return x <= 0.0 or z <= GROUND_LEVEL

            test_traj = integrate_trajectory(
                test_state,
                test_force,
                dt=self.dt,
                max_time=2.0,
                ground_level=GROUND_LEVEL,
                method='euler',  # Use euler for speed
                custom_stop_condition=test_stop
            )

            # Find where it actually crossed
            x_positions = test_traj['position'][:, 0]
            plate_crossing_idx = np.where(x_positions <= 0)[0]

            if len(plate_crossing_idx) > 0:
                idx = plate_crossing_idx[0]
                # Get actual crossing position
                actual_cross_m = test_traj['position'][idx]

                # Calculate error from desired target
                error_y = actual_cross_m[1] - target_pos_m[1]
                error_z = actual_cross_m[2] - target_pos_m[2]

                # Adjust aim point to compensate (move opposite to error)
                # Use higher correction factor for better convergence
                aim_point_m[1] -= error_y * 0.9  # 90% correction factor
                aim_point_m[2] -= error_z * 0.9

                # If error is very small, we've converged
                if abs(error_y) < 0.005 and abs(error_z) < 0.005:  # <0.5 cm
                    break

        # Final velocity vector
        v0_vec = v0_vec_test

        # Create initial state
        initial_state = np.concatenate([release_pos_m, v0_vec])

        # Define force function (uses spin_axis and effective_spin_rpm from above)
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
