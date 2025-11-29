"""
Numerical integration methods for baseball trajectory simulation.

Implements Runge-Kutta 4th order (RK4) method for accurate trajectory calculation.
Optimized with numba JIT compilation for performance.

Performance Notes:
- Integration loop is the primary bottleneck (50-70% of total computation time)
- Numba JIT compilation provides 5-10× speedup on integration functions
- Pre-allocated arrays reduce memory allocation overhead
- Buffered integration eliminates allocation in hot path

Phase 5: Numba Parallel Integration
- @njit(parallel=True) with prange for batch trajectory processing
- Parallelizes multiple independent trajectory calculations
- Expected 2-3x speedup on multi-core systems for batch operations
"""

import numpy as np
from numba import njit, prange
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


# ============================================================================
# Phase 3: Lookup-Based Integration for Ultra-Fast Mode
# ============================================================================

@njit(cache=True)
def _step_rk4_lookup(state, dt, force_func, cd_table, cl_table, 
                      spin_x, spin_y, spin_z, spin_rpm, cd_base, air_density, cross_area):
    """
    RK4 step using lookup-based force calculation.
    
    Optimized for ultra-fast simulation by using pre-computed lookup tables
    for aerodynamic coefficients instead of full physics calculation.
    """
    # k1: derivative at beginning of interval
    pos = state[:3]
    vel = state[3:]
    fx, fy, fz = force_func(pos, vel, spin_x, spin_y, spin_z, spin_rpm, 
                            cd_base, air_density, cross_area, cd_table, cl_table)
    k1 = _derivative_jit(state, fx, fy, fz)

    # k2: derivative at midpoint using k1
    state_k2 = state + 0.5 * dt * k1
    pos2 = state_k2[:3]
    vel2 = state_k2[3:]
    fx2, fy2, fz2 = force_func(pos2, vel2, spin_x, spin_y, spin_z, spin_rpm,
                               cd_base, air_density, cross_area, cd_table, cl_table)
    k2 = _derivative_jit(state_k2, fx2, fy2, fz2)

    # k3: derivative at midpoint using k2
    state_k3 = state + 0.5 * dt * k2
    pos3 = state_k3[:3]
    vel3 = state_k3[3:]
    fx3, fy3, fz3 = force_func(pos3, vel3, spin_x, spin_y, spin_z, spin_rpm,
                               cd_base, air_density, cross_area, cd_table, cl_table)
    k3 = _derivative_jit(state_k3, fx3, fy3, fz3)

    # k4: derivative at end using k3
    state_k4 = state + dt * k3
    pos4 = state_k4[:3]
    vel4 = state_k4[3:]
    fx4, fy4, fz4 = force_func(pos4, vel4, spin_x, spin_y, spin_z, spin_rpm,
                               cd_base, air_density, cross_area, cd_table, cl_table)
    k4 = _derivative_jit(state_k4, fx4, fy4, fz4)

    # Weighted average: new_state = old_state + (dt/6)*(k1 + 2*k2 + 2*k3 + k4)
    new_state = state + (dt / 6.0) * (k1 + 2.0*k2 + 2.0*k3 + k4)

    return new_state


@njit(cache=True)
def integrate_trajectory_lookup(
    initial_state,
    dt,
    max_time,
    ground_level,
    force_func,
    times_buf,
    positions_buf,
    velocities_buf,
    cd_table,
    cl_table,
    spin_x, spin_y, spin_z,
    spin_rpm,
    cd_base,
    air_density,
    cross_area
):
    """
    Integrate trajectory using lookup tables for ultra-fast simulation.

    Combines buffered integration with lookup-based aerodynamic coefficients
    for maximum speed. 3-5x faster than full physics mode.

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
    force_func : callable (Numba-compiled)
        Lookup-based force function
    times_buf, positions_buf, velocities_buf : np.ndarray
        Pre-allocated buffers
    cd_table, cl_table : np.ndarray
        Pre-computed aerodynamic coefficient tables
    spin_x, spin_y, spin_z : float
        Spin axis components
    spin_rpm : float
        Spin rate in RPM
    cd_base : float
        Base drag coefficient
    air_density : float
        Air density in kg/m³
    cross_area : float
        Cross-sectional area in m²

    Returns
    -------
    int
        step_count: number of steps taken
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

    # Integration loop
    while current_time < max_time and step_count < max_steps - 2:
        # Take RK4 step with lookup tables
        current_state = _step_rk4_lookup(
            current_state, dt, force_func, cd_table, cl_table,
            spin_x, spin_y, spin_z, spin_rpm, cd_base, air_density, cross_area
        )
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


# ============================================================================
# Phase 5: Numba Parallel Integration for Batch Trajectory Processing
# ============================================================================
# These functions use @njit(parallel=True) with prange to parallelize
# multiple independent trajectory calculations across CPU cores.
#
# Use case: Monte Carlo simulations, fielder route analysis, outcome prediction
# Expected speedup: 2-3x on 4+ core systems for batch sizes >= 8
# ============================================================================

@njit(cache=True)
def _integrate_single_trajectory_for_batch(
    initial_state,
    dt,
    max_time,
    ground_level,
    spin_x, spin_y, spin_z,
    spin_rpm,
    cd_base,
    air_density,
    cross_area,
    cd_table,
    cl_table,
    positions_out,
    velocities_out,
    times_out,
    trajectory_idx,
    max_steps,
    force_func
):
    """
    Integrate a single trajectory for batch processing (writes to pre-allocated arrays).
    
    This is a helper for batch integration - writes results directly to output arrays
    at the specified trajectory index.
    
    Returns
    -------
    int
        Number of steps taken for this trajectory
    """
    # Initialize state
    current_state = initial_state.copy()
    current_time = 0.0
    step_count = 0
    
    # Store initial state
    times_out[trajectory_idx, 0] = 0.0
    positions_out[trajectory_idx, 0, 0] = initial_state[0]
    positions_out[trajectory_idx, 0, 1] = initial_state[1]
    positions_out[trajectory_idx, 0, 2] = initial_state[2]
    velocities_out[trajectory_idx, 0, 0] = initial_state[3]
    velocities_out[trajectory_idx, 0, 1] = initial_state[4]
    velocities_out[trajectory_idx, 0, 2] = initial_state[5]
    
    # Integration loop
    while current_time < max_time and step_count < max_steps - 2:
        # RK4 step with lookup tables
        current_state = _step_rk4_lookup(
            current_state, dt, force_func, cd_table, cl_table,
            spin_x, spin_y, spin_z, spin_rpm, cd_base, air_density, cross_area
        )
        current_time += dt
        step_count += 1
        
        # Store state
        times_out[trajectory_idx, step_count] = current_time
        positions_out[trajectory_idx, step_count, 0] = current_state[0]
        positions_out[trajectory_idx, step_count, 1] = current_state[1]
        positions_out[trajectory_idx, step_count, 2] = current_state[2]
        velocities_out[trajectory_idx, step_count, 0] = current_state[3]
        velocities_out[trajectory_idx, step_count, 1] = current_state[4]
        velocities_out[trajectory_idx, step_count, 2] = current_state[5]
        
        # Check ground collision
        if current_state[2] <= ground_level and step_count > 0:
            z_prev = positions_out[trajectory_idx, step_count - 1, 2]
            z_curr = current_state[2]
            
            if abs(z_curr - z_prev) > 1e-10:
                fraction = (ground_level - z_prev) / (z_curr - z_prev)
                step_count += 1
                times_out[trajectory_idx, step_count] = times_out[trajectory_idx, step_count - 1] + fraction * dt
                
                for i in range(3):
                    positions_out[trajectory_idx, step_count, i] = (
                        positions_out[trajectory_idx, step_count - 2, i] + 
                        fraction * (current_state[i] - positions_out[trajectory_idx, step_count - 2, i])
                    )
                    velocities_out[trajectory_idx, step_count, i] = (
                        velocities_out[trajectory_idx, step_count - 2, i] + 
                        fraction * (current_state[i + 3] - velocities_out[trajectory_idx, step_count - 2, i])
                    )
            break
    
    return step_count + 1


@njit(parallel=True, cache=True)
def integrate_trajectories_batch_parallel(
    initial_states,
    dt,
    max_time,
    ground_level,
    spin_params,
    cd_base,
    air_density,
    cross_area,
    cd_table,
    cl_table,
    force_func
):
    """
    Integrate multiple trajectories in parallel using Numba's prange.
    
    Uses @njit(parallel=True) to distribute trajectory calculations across
    CPU cores. Each trajectory is completely independent, making this
    embarrassingly parallel.
    
    Parameters
    ----------
    initial_states : np.ndarray
        Initial states array of shape (N, 6) where each row is [x, y, z, vx, vy, vz]
    dt : float
        Time step in seconds
    max_time : float
        Maximum simulation time in seconds
    ground_level : float
        Height (z) at which to stop simulation (meters)
    spin_params : np.ndarray
        Spin parameters array of shape (N, 4) where each row is [spin_x, spin_y, spin_z, spin_rpm]
    cd_base : float
        Base drag coefficient
    air_density : float
        Air density in kg/m³
    cross_area : float
        Cross-sectional area in m²
    cd_table, cl_table : np.ndarray
        Pre-computed aerodynamic coefficient lookup tables
    force_func : callable
        Numba-compiled force function (aerodynamic_force_tuple_lookup)
    
    Returns
    -------
    tuple of (positions, velocities, times, step_counts)
        - positions: np.ndarray of shape (N, max_steps, 3)
        - velocities: np.ndarray of shape (N, max_steps, 3)
        - times: np.ndarray of shape (N, max_steps)
        - step_counts: np.ndarray of shape (N,) with actual step count per trajectory
    
    Example
    -------
    >>> # Simulate 100 trajectories in parallel
    >>> initial_states = np.zeros((100, 6))
    >>> for i in range(100):
    ...     initial_states[i] = [0, 0, 1, 40+i*0.1, 0, 20]  # Varying exit velocity
    >>> spin_params = np.tile([0, 1, 0, 2000], (100, 1))  # Same spin for all
    >>> cd_table, cl_table = get_lookup_tables()
    >>> pos, vel, times, counts = integrate_trajectories_batch_parallel(
    ...     initial_states, 0.005, 10.0, 0.0, spin_params,
    ...     0.3, 1.225, 0.0042, cd_table, cl_table, force_func
    ... )
    """
    n_trajectories = initial_states.shape[0]
    max_steps = int(max_time / dt) + 10
    
    # Pre-allocate output arrays
    positions = np.zeros((n_trajectories, max_steps, 3))
    velocities = np.zeros((n_trajectories, max_steps, 3))
    times = np.zeros((n_trajectories, max_steps))
    step_counts = np.zeros(n_trajectories, dtype=np.int64)
    
    # Parallel loop over trajectories
    for i in prange(n_trajectories):
        initial_state = initial_states[i]
        spin_x = spin_params[i, 0]
        spin_y = spin_params[i, 1]
        spin_z = spin_params[i, 2]
        spin_rpm = spin_params[i, 3]
        
        step_counts[i] = _integrate_single_trajectory_for_batch(
            initial_state, dt, max_time, ground_level,
            spin_x, spin_y, spin_z, spin_rpm,
            cd_base, air_density, cross_area,
            cd_table, cl_table,
            positions, velocities, times,
            i, max_steps, force_func
        )
    
    return positions, velocities, times, step_counts


@njit(parallel=True, cache=True)
def calculate_trajectory_endpoints_batch(
    initial_states,
    dt,
    max_time,
    ground_level,
    spin_params,
    cd_base,
    air_density,
    cross_area,
    cd_table,
    cl_table,
    force_func
):
    """
    Calculate only final landing positions for batch trajectories (memory efficient).
    
    When you only need the final landing position (e.g., for fielding range analysis),
    this function is more memory efficient than storing full trajectories.
    
    Parameters
    ----------
    initial_states : np.ndarray
        Initial states array of shape (N, 6)
    dt : float
        Time step in seconds
    max_time : float
        Maximum simulation time in seconds
    ground_level : float
        Height (z) at which to stop simulation (meters)
    spin_params : np.ndarray
        Spin parameters array of shape (N, 4)
    cd_base, air_density, cross_area : float
        Physical parameters
    cd_table, cl_table : np.ndarray
        Aerodynamic lookup tables
    force_func : callable
        Numba-compiled force function
    
    Returns
    -------
    tuple of (landing_positions, landing_times, distances, apex_heights)
        - landing_positions: np.ndarray of shape (N, 3) - final [x, y, z] positions
        - landing_times: np.ndarray of shape (N,) - time to ground
        - distances: np.ndarray of shape (N,) - horizontal distance traveled
        - apex_heights: np.ndarray of shape (N,) - maximum height reached
    """
    n_trajectories = initial_states.shape[0]
    
    # Output arrays
    landing_positions = np.zeros((n_trajectories, 3))
    landing_times = np.zeros(n_trajectories)
    distances = np.zeros(n_trajectories)
    apex_heights = np.zeros(n_trajectories)
    
    # Parallel loop
    for i in prange(n_trajectories):
        initial_state = initial_states[i]
        spin_x = spin_params[i, 0]
        spin_y = spin_params[i, 1]
        spin_z = spin_params[i, 2]
        spin_rpm = spin_params[i, 3]
        
        # Integrate trajectory
        current_state = initial_state.copy()
        current_time = 0.0
        max_z = initial_state[2]
        prev_z = initial_state[2]
        max_steps = int(max_time / dt) + 10
        
        for step in range(max_steps):
            # RK4 step
            current_state = _step_rk4_lookup(
                current_state, dt, force_func, cd_table, cl_table,
                spin_x, spin_y, spin_z, spin_rpm, cd_base, air_density, cross_area
            )
            current_time += dt
            
            # Track apex
            if current_state[2] > max_z:
                max_z = current_state[2]
            
            # Check ground
            if current_state[2] <= ground_level:
                # Interpolate landing
                if abs(current_state[2] - prev_z) > 1e-10:
                    fraction = (ground_level - prev_z) / (current_state[2] - prev_z)
                    current_time = current_time - dt + fraction * dt
                    for j in range(3):
                        current_state[j] = current_state[j] - (1 - fraction) * (current_state[j] - 
                            (current_state[j] - current_state[j+3] * dt))
                break
            
            prev_z = current_state[2]
            
            if current_time >= max_time:
                break
        
        # Store results
        landing_positions[i, 0] = current_state[0]
        landing_positions[i, 1] = current_state[1]
        landing_positions[i, 2] = current_state[2]
        landing_times[i] = current_time
        distances[i] = np.sqrt(current_state[0]**2 + current_state[1]**2)
        apex_heights[i] = max_z
    
    return landing_positions, landing_times, distances, apex_heights


@njit(parallel=True, cache=True)
def calculate_fielder_times_batch(
    fielder_positions,
    target_positions,
    sprint_speeds,
    reaction_times,
    route_efficiencies
):
    """
    Calculate fielder arrival times for multiple fielder-target combinations in parallel.
    
    Used for determining which fielder can reach a batted ball fastest.
    Parallelizes across fielder-target pairs.
    
    Parameters
    ----------
    fielder_positions : np.ndarray
        Fielder starting positions of shape (N, 2) - [x, y] coordinates
    target_positions : np.ndarray  
        Target positions of shape (M, 2) - [x, y] coordinates
    sprint_speeds : np.ndarray
        Sprint speeds in ft/s of shape (N,)
    reaction_times : np.ndarray
        Reaction times in seconds of shape (N,)
    route_efficiencies : np.ndarray
        Route efficiency factors (0.85-0.98) of shape (N,)
    
    Returns
    -------
    np.ndarray
        Arrival times of shape (N, M) where entry [i, j] is time for 
        fielder i to reach target j
    
    Notes
    -----
    Uses simplified physics model:
    - Distance calculated as Euclidean distance * route efficiency penalty
    - Time = reaction_time + distance / (speed * effective_speed_factor)
    - Effective speed factor varies by distance (shorter = slower start)
    """
    n_fielders = fielder_positions.shape[0]
    n_targets = target_positions.shape[0]
    
    arrival_times = np.zeros((n_fielders, n_targets))
    
    # Parallel loop over all combinations
    for idx in prange(n_fielders * n_targets):
        i = idx // n_targets  # Fielder index
        j = idx % n_targets   # Target index
        
        # Calculate distance
        dx = target_positions[j, 0] - fielder_positions[i, 0]
        dy = target_positions[j, 1] - fielder_positions[i, 1]
        distance = np.sqrt(dx * dx + dy * dy)
        
        # Route efficiency penalty
        route_eff = route_efficiencies[i]
        route_penalty = 1.0 + (1.0 - route_eff) * 0.5
        effective_distance = distance * route_penalty
        
        # Speed factor based on distance
        if distance < 30.0:
            speed_pct = 0.88 + (distance / 30.0) * 0.06
        elif distance < 60.0:
            speed_pct = 0.94 + ((distance - 30.0) / 30.0) * 0.04
        else:
            speed_pct = 0.98 + min((distance - 60.0) / 60.0, 1.0) * 0.02
        
        effective_speed = sprint_speeds[i] * speed_pct
        
        # Calculate time
        if effective_speed > 0:
            movement_time = effective_distance / effective_speed
        else:
            movement_time = 1e6  # Effectively infinite
        
        arrival_times[i, j] = reaction_times[i] + movement_time
    
    return arrival_times


# ============================================================================
# Batch Trajectory Helper Functions
# ============================================================================

def create_batch_initial_states(
    exit_velocities,
    launch_angles,
    spray_angles,
    initial_positions=None
):
    """
    Create batch initial states from arrays of launch parameters.
    
    Convenience function for preparing input to batch trajectory functions.
    
    Parameters
    ----------
    exit_velocities : array-like
        Exit velocities in m/s of shape (N,)
    launch_angles : array-like
        Launch angles in degrees of shape (N,)
    spray_angles : array-like
        Spray angles in degrees of shape (N,)
    initial_positions : array-like, optional
        Initial positions of shape (N, 3) or (3,) for shared position
        Default: [0, 0, 1] for all trajectories
    
    Returns
    -------
    np.ndarray
        Initial states of shape (N, 6)
    """
    n = len(exit_velocities)
    exit_velocities = np.asarray(exit_velocities, dtype=np.float64)
    launch_angles = np.asarray(launch_angles, dtype=np.float64)
    spray_angles = np.asarray(spray_angles, dtype=np.float64)
    
    # Handle initial positions
    if initial_positions is None:
        positions = np.tile([0.0, 0.0, 1.0], (n, 1))
    else:
        positions = np.asarray(initial_positions, dtype=np.float64)
        if positions.ndim == 1:
            positions = np.tile(positions, (n, 1))
    
    # Convert angles to radians
    launch_rad = np.deg2rad(launch_angles)
    spray_rad = np.deg2rad(spray_angles)
    
    # Calculate velocity components
    vx = exit_velocities * np.cos(launch_rad) * np.cos(spray_rad)
    vy = exit_velocities * np.cos(launch_rad) * np.sin(spray_rad)
    vz = exit_velocities * np.sin(launch_rad)
    
    # Build state array
    states = np.zeros((n, 6), dtype=np.float64)
    states[:, :3] = positions
    states[:, 3] = vx
    states[:, 4] = vy
    states[:, 5] = vz
    
    return states


def create_batch_spin_params(spin_rates, spin_axes):
    """
    Create batch spin parameters array.
    
    Parameters
    ----------
    spin_rates : array-like
        Spin rates in RPM of shape (N,)
    spin_axes : array-like
        Spin axes of shape (N, 3) or (3,) for shared axis
    
    Returns
    -------
    np.ndarray
        Spin parameters of shape (N, 4) as [spin_x, spin_y, spin_z, spin_rpm]
    """
    n = len(spin_rates)
    spin_rates = np.asarray(spin_rates, dtype=np.float64)
    spin_axes = np.asarray(spin_axes, dtype=np.float64)
    
    # Handle shared spin axis
    if spin_axes.ndim == 1:
        spin_axes = np.tile(spin_axes, (n, 1))
    
    # Normalize spin axes
    norms = np.linalg.norm(spin_axes, axis=1, keepdims=True)
    norms = np.where(norms > 1e-6, norms, 1.0)
    spin_axes = spin_axes / norms
    
    # Build spin params array
    spin_params = np.zeros((n, 4), dtype=np.float64)
    spin_params[:, :3] = spin_axes
    spin_params[:, 3] = spin_rates
    
    return spin_params
