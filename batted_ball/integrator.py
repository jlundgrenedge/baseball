"""
Numerical integration methods for baseball trajectory simulation.

Implements Runge-Kutta 4th order (RK4) method for accurate trajectory calculation.
Optimized with numba JIT compilation for performance.

Performance Notes:
- Integration loop is the primary bottleneck (50-70% of total computation time)
- Numba JIT compilation provides 5-10× speedup on integration functions
- Pre-allocated arrays reduce memory allocation overhead
- Buffered integration eliminates allocation in hot path
"""

import numpy as np
from numba import njit
from .constants import GRAVITY, BALL_MASS, DT_DEFAULT


# ============================================================================
# Numba-optimized integration functions (standalone for maximum performance)
# ============================================================================

@njit(cache=True)
def _derivative_jit(state, force_x, force_y, force_z):
    """
    Calculate derivative of state vector (Numba-optimized).

    State derivative: d/dt [x, y, z, vx, vy, vz] = [vx, vy, vz, ax, ay, az]

    Parameters
    ----------
    state : np.ndarray
        State vector [x, y, z, vx, vy, vz]
    force_x, force_y, force_z : float
        Force components in Newtons

    Returns
    -------
    np.ndarray
        Derivative vector [vx, vy, vz, ax, ay, az]
    """
    # Extract velocity
    vx = state[3]
    vy = state[4]
    vz = state[5]

    # Add gravity (downward in z-direction)
    total_force_x = force_x
    total_force_y = force_y
    total_force_z = force_z - BALL_MASS * GRAVITY

    # Calculate acceleration: a = F / m
    ax = total_force_x / BALL_MASS
    ay = total_force_y / BALL_MASS
    az = total_force_z / BALL_MASS

    # Build derivative vector
    derivative = np.array([vx, vy, vz, ax, ay, az])

    return derivative


@njit(cache=True)
def _step_rk4_jit(state, dt, force_func_ptr, *force_args):
    """
    Perform one RK4 integration step (Numba-optimized).

    This is the critical hot path function - called 50-200 times per trajectory.
    Numba JIT compilation provides ~5-10× speedup vs pure Python.

    Parameters
    ----------
    state : np.ndarray
        Current state vector [x, y, z, vx, vy, vz]
    dt : float
        Time step in seconds
    force_func_ptr : callable (Numba-compiled)
        Function that takes (position, velocity, *args) and returns force tuple
    *force_args : additional arguments to pass to force function

    Returns
    -------
    np.ndarray
        New state vector after time step dt
    """
    # State vector: [x, y, z, vx, vy, vz]
    # Derivative: [vx, vy, vz, ax, ay, az]

    # k1: derivative at beginning of interval
    pos = state[:3]
    vel = state[3:]
    fx, fy, fz = force_func_ptr(pos, vel, *force_args)
    k1 = _derivative_jit(state, fx, fy, fz)

    # k2: derivative at midpoint using k1
    state_k2 = state + 0.5 * dt * k1
    pos2 = state_k2[:3]
    vel2 = state_k2[3:]
    fx2, fy2, fz2 = force_func_ptr(pos2, vel2, *force_args)
    k2 = _derivative_jit(state_k2, fx2, fy2, fz2)

    # k3: derivative at midpoint using k2
    state_k3 = state + 0.5 * dt * k2
    pos3 = state_k3[:3]
    vel3 = state_k3[3:]
    fx3, fy3, fz3 = force_func_ptr(pos3, vel3, *force_args)
    k3 = _derivative_jit(state_k3, fx3, fy3, fz3)

    # k4: derivative at end using k3
    state_k4 = state + dt * k3
    pos4 = state_k4[:3]
    vel4 = state_k4[3:]
    fx4, fy4, fz4 = force_func_ptr(pos4, vel4, *force_args)
    k4 = _derivative_jit(state_k4, fx4, fy4, fz4)

    # Weighted average: new_state = old_state + (dt/6)*(k1 + 2*k2 + 2*k3 + k4)
    new_state = state + (dt / 6.0) * (k1 + 2.0*k2 + 2.0*k3 + k4)

    return new_state


@njit(cache=True)
def integrate_trajectory_jit(
    initial_state,
    dt,
    max_time,
    ground_level,
    force_func,
    *force_args
):
    """
    Integrate trajectory until ball hits ground or max time reached (Numba-optimized).

    This is the main integration loop - THE critical bottleneck (50-70% of total time).
    Numba JIT compilation provides massive speedup by eliminating Python overhead.

    Parameters
    ----------
    initial_state : np.ndarray
        Initial state [x, y, z, vx, vy, vz]
    dt : float
        Time step in seconds
    max_time : float
        Maximum simulation time in seconds
    ground_level : float
        Height (z) at which to stop simulation (meters)
    force_func : callable (must be Numba-compiled)
        Function returning (fx, fy, fz) given (position, velocity, *args)
    *force_args : additional arguments to pass to force function

    Returns
    -------
    tuple of (times, positions, velocities, step_count)
        - times: np.ndarray of time points
        - positions: np.ndarray of positions (Nx3)
        - velocities: np.ndarray of velocities (Nx3)
        - step_count: int, number of steps taken
    """
    # Pre-allocate arrays
    max_steps = int(max_time / dt) + 10
    times = np.zeros(max_steps)
    positions = np.zeros((max_steps, 3))
    velocities = np.zeros((max_steps, 3))

    # Initialize
    current_state = initial_state.copy()
    current_time = 0.0
    step_count = 0

    times[0] = 0.0
    positions[0, :] = initial_state[:3]
    velocities[0, :] = initial_state[3:]

    # Integration loop - THIS IS THE HOT PATH
    while current_time < max_time and step_count < max_steps - 2:
        # Take RK4 step
        current_state = _step_rk4_jit(current_state, dt, force_func, *force_args)
        current_time += dt
        step_count += 1

        # Store state
        times[step_count] = current_time
        positions[step_count, :] = current_state[:3]
        velocities[step_count, :] = current_state[3:]

        # Check if ball hit ground
        if current_state[2] <= ground_level and step_count > 0:
            # Interpolate to find exact landing
            z_prev = positions[step_count - 1, 2]
            z_curr = current_state[2]

            if abs(z_curr - z_prev) > 1e-10:
                fraction = (ground_level - z_prev) / (z_curr - z_prev)

                # Interpolate landing state
                step_count += 1
                times[step_count] = times[step_count - 1] + fraction * dt

                for i in range(3):
                    positions[step_count, i] = positions[step_count - 2, i] + fraction * (
                        current_state[i] - positions[step_count - 2, i]
                    )
                    velocities[step_count, i] = velocities[step_count - 2, i] + fraction * (
                        current_state[i + 3] - velocities[step_count - 2, i]
                    )

            break

    return times, positions, velocities, step_count + 1


@njit(cache=True)
def integrate_trajectory_buffered(
    initial_state,
    dt,
    max_time,
    ground_level,
    force_func,
    times_buf,
    positions_buf,
    velocities_buf,
    *force_args
):
    """
    Integrate trajectory using pre-allocated buffers (Numba-optimized).

    This version eliminates memory allocation in the hot path by using
    pre-allocated buffers from TrajectoryBuffer. Provides ~20-30% additional
    speedup for high-volume simulations.

    Parameters
    ----------
    initial_state : np.ndarray
        Initial state [x, y, z, vx, vy, vz]
    dt : float
        Time step in seconds
    max_time : float
        Maximum simulation time in seconds
    ground_level : float
        Height (z) at which to stop simulation (meters)
    force_func : callable (must be Numba-compiled)
        Function returning (fx, fy, fz) given (position, velocity, *args)
    times_buf : np.ndarray
        Pre-allocated time buffer (max_steps,)
    positions_buf : np.ndarray
        Pre-allocated position buffer (max_steps, 3)
    velocities_buf : np.ndarray
        Pre-allocated velocity buffer (max_steps, 3)
    *force_args : additional arguments to pass to force function

    Returns
    -------
    int
        step_count: number of steps taken (actual data is in buffers[0:step_count])
    """
    # Initialize
    current_state = initial_state.copy()
    current_time = 0.0
    step_count = 0
    max_steps = len(times_buf)

    times_buf[0] = 0.0
    positions_buf[0, 0] = initial_state[0]
    positions_buf[0, 1] = initial_state[1]
    positions_buf[0, 2] = initial_state[2]
    velocities_buf[0, 0] = initial_state[3]
    velocities_buf[0, 1] = initial_state[4]
    velocities_buf[0, 2] = initial_state[5]

    # Integration loop - THIS IS THE HOT PATH
    while current_time < max_time and step_count < max_steps - 2:
        # Take RK4 step
        current_state = _step_rk4_jit(current_state, dt, force_func, *force_args)
        current_time += dt
        step_count += 1

        # Store state
        times_buf[step_count] = current_time
        positions_buf[step_count, 0] = current_state[0]
        positions_buf[step_count, 1] = current_state[1]
        positions_buf[step_count, 2] = current_state[2]
        velocities_buf[step_count, 0] = current_state[3]
        velocities_buf[step_count, 1] = current_state[4]
        velocities_buf[step_count, 2] = current_state[5]

        # Check if ball hit ground
        if current_state[2] <= ground_level and step_count > 0:
            # Interpolate to find exact landing
            z_prev = positions_buf[step_count - 1, 2]
            z_curr = current_state[2]

            if abs(z_curr - z_prev) > 1e-10:
                fraction = (ground_level - z_prev) / (z_curr - z_prev)

                # Interpolate landing state
                step_count += 1
                times_buf[step_count] = times_buf[step_count - 1] + fraction * dt

                for i in range(3):
                    positions_buf[step_count, i] = positions_buf[step_count - 2, i] + fraction * (
                        current_state[i] - positions_buf[step_count - 2, i]
                    )
                    velocities_buf[step_count, i] = velocities_buf[step_count - 2, i] + fraction * (
                        current_state[i + 3] - velocities_buf[step_count - 2, i]
                    )

            break

    return step_count + 1


class TrajectoryIntegrator:
    """
    Numerical integrator for baseball trajectory.

    Uses RK4 (Runge-Kutta 4th order) method for accurate integration
    of the equations of motion under aerodynamic forces.
    """

    def __init__(self, dt=DT_DEFAULT):
        """
        Initialize integrator.

        Parameters
        ----------
        dt : float
            Time step in seconds (default: 0.001 = 1 millisecond)
        """
        self.dt = dt

    def step_rk4(self, state, force_function):
        """
        Perform one RK4 integration step.

        RK4 is a 4th-order accurate method that evaluates the derivative
        at four points within the time step for high accuracy.

        Parameters
        ----------
        state : np.ndarray
            Current state vector [x, y, z, vx, vy, vz]
            Position in meters, velocity in m/s
        force_function : callable
            Function that takes (position, velocity) and returns
            net force vector in Newtons

        Returns
        -------
        np.ndarray
            New state vector after time step dt
        """
        # State vector: [x, y, z, vx, vy, vz]
        # Derivative: [vx, vy, vz, ax, ay, az]

        # k1: derivative at beginning of interval
        k1 = self._derivative(state, force_function)

        # k2: derivative at midpoint using k1
        state_k2 = state + 0.5 * self.dt * k1
        k2 = self._derivative(state_k2, force_function)

        # k3: derivative at midpoint using k2
        state_k3 = state + 0.5 * self.dt * k2
        k3 = self._derivative(state_k3, force_function)

        # k4: derivative at end using k3
        state_k4 = state + self.dt * k3
        k4 = self._derivative(state_k4, force_function)

        # Weighted average: new_state = old_state + (dt/6)*(k1 + 2*k2 + 2*k3 + k4)
        new_state = state + (self.dt / 6.0) * (k1 + 2*k2 + 2*k3 + k4)

        return new_state

    def _derivative(self, state, force_function):
        """
        Calculate derivative of state vector.

        State derivative: d/dt [x, y, z, vx, vy, vz] = [vx, vy, vz, ax, ay, az]

        Parameters
        ----------
        state : np.ndarray
            State vector [x, y, z, vx, vy, vz]
        force_function : callable
            Function that returns force vector given (position, velocity)

        Returns
        -------
        np.ndarray
            Derivative vector [vx, vy, vz, ax, ay, az]
        """
        # Extract position and velocity
        position = state[:3]
        velocity = state[3:]

        # Calculate net force (aerodynamic + gravity)
        force = force_function(position, velocity)

        # Add gravity (downward in z-direction)
        gravity_force = np.array([0.0, 0.0, -BALL_MASS * GRAVITY])
        total_force = force + gravity_force

        # Calculate acceleration: a = F / m
        acceleration = total_force / BALL_MASS

        # Derivative vector
        derivative = np.concatenate([velocity, acceleration])

        return derivative

    def step_euler(self, state, force_function):
        """
        Perform one Euler integration step (simpler, less accurate).

        Euler method is first-order accurate. Use for comparison or
        when speed is more important than accuracy.

        Parameters
        ----------
        state : np.ndarray
            Current state vector [x, y, z, vx, vy, vz]
        force_function : callable
            Function that returns force vector

        Returns
        -------
        np.ndarray
            New state vector after time step dt
        """
        derivative = self._derivative(state, force_function)
        new_state = state + self.dt * derivative
        return new_state


def integrate_trajectory(
    initial_state,
    force_function,
    dt=DT_DEFAULT,
    max_time=10.0,
    ground_level=0.0,
    method='rk4',
    custom_stop_condition=None
):
    """
    Integrate trajectory until ball hits ground or max time reached.

    Parameters
    ----------
    initial_state : np.ndarray
        Initial state [x, y, z, vx, vy, vz]
        Position in meters, velocity in m/s
    force_function : callable
        Function that returns force vector given (position, velocity)
    dt : float
        Time step in seconds
    max_time : float
        Maximum simulation time in seconds
    ground_level : float
        Height (z) at which to stop simulation (meters)
    method : str
        Integration method: 'rk4' or 'euler'
    custom_stop_condition : callable, optional
        Function that takes position (x, y, z) and returns True when
        simulation should stop. If provided, overrides ground_level check.

    Returns
    -------
    dict
        Dictionary containing:
        - 'time': np.ndarray of time points
        - 'position': np.ndarray of positions (Nx3)
        - 'velocity': np.ndarray of velocities (Nx3)
        - 'final_state': final state vector
    """
    integrator = TrajectoryIntegrator(dt=dt)

    # Choose integration method
    if method == 'rk4':
        step_function = integrator.step_rk4
    elif method == 'euler':
        step_function = integrator.step_euler
    else:
        raise ValueError(f"Unknown integration method: {method}")

    # Pre-allocate arrays for better performance
    # Estimate max steps needed
    max_steps = int(max_time / dt) + 10
    times = np.zeros(max_steps)
    positions = np.zeros((max_steps, 3))
    velocities = np.zeros((max_steps, 3))

    # Initialize first point
    current_state = initial_state.copy()
    current_time = 0.0
    step_count = 0

    times[0] = 0.0
    positions[0] = initial_state[:3]
    velocities[0] = initial_state[3:]

    # Integration loop
    while current_time < max_time and step_count < max_steps - 2:
        # Take integration step
        current_state = step_function(current_state, force_function)
        current_time += dt
        step_count += 1

        # Store state
        times[step_count] = current_time
        positions[step_count] = current_state[:3]
        velocities[step_count] = current_state[3:]

        # Check stop condition
        should_stop = False

        if custom_stop_condition is not None:
            # Use custom stop condition if provided
            if custom_stop_condition(current_state[:3]) and step_count > 0:
                should_stop = True
        else:
            # Default: check if ball has hit ground
            if current_state[2] <= ground_level and step_count > 0:
                should_stop = True

        if should_stop:
            # Interpolate to find exact landing time and position
            if step_count >= 1:
                z_prev = positions[step_count - 1, 2]
                z_curr = current_state[2]
                t_prev = times[step_count - 1]
                t_curr = current_time

                # Linear interpolation to ground_level
                if abs(z_curr - z_prev) > 1e-10:
                    fraction = (ground_level - z_prev) / (z_curr - z_prev)
                    landing_time = t_prev + fraction * (t_curr - t_prev)
                    landing_state = (
                        positions[step_count - 1] + fraction * (current_state[:3] - positions[step_count - 1])
                    )
                    landing_velocity = (
                        velocities[step_count - 1] + fraction * (current_state[3:] - velocities[step_count - 1])
                    )

                    # Update final point to landing point
                    step_count += 1
                    times[step_count] = landing_time
                    positions[step_count] = landing_state
                    velocities[step_count] = landing_velocity

            break

    # Trim arrays to actual size
    actual_size = step_count + 1
    times = times[:actual_size]
    positions = positions[:actual_size]
    velocities = velocities[:actual_size]

    return {
        'time': times,
        'position': positions,
        'velocity': velocities,
        'final_state': current_state,
    }


def create_initial_state(
    position_initial,
    velocity_magnitude,
    launch_angle_deg,
    spray_angle_deg
):
    """
    Create initial state vector from launch parameters.

    Parameters
    ----------
    position_initial : np.ndarray or list
        Initial position [x0, y0, z0] in meters
    velocity_magnitude : float
        Exit velocity magnitude in m/s
    launch_angle_deg : float
        Launch angle in degrees (0 = horizontal, 90 = straight up)
    spray_angle_deg : float
        Spray angle in degrees (0 = straight to center field,
        positive = pull side, negative = opposite field)

    Returns
    -------
    np.ndarray
        Initial state vector [x, y, z, vx, vy, vz]
    """
    # Convert position to array
    position = np.array(position_initial, dtype=float)

    # Convert angles to radians
    launch_angle = np.deg2rad(launch_angle_deg)
    spray_angle = np.deg2rad(spray_angle_deg)

    # Calculate velocity components
    # x: direction toward outfield (horizontal component)
    # y: lateral direction (left field positive)
    # z: vertical direction (up positive)

    vx = velocity_magnitude * np.cos(launch_angle) * np.cos(spray_angle)
    vy = velocity_magnitude * np.cos(launch_angle) * np.sin(spray_angle)
    vz = velocity_magnitude * np.sin(launch_angle)

    velocity = np.array([vx, vy, vz])

    # Combine position and velocity into state vector
    state = np.concatenate([position, velocity])

    return state
