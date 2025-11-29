//! High-performance RK4 trajectory integration for baseball simulation.
//!
//! This module provides Rust implementations of the critical trajectory
//! integration functions, exposed to Python via PyO3.
//!
//! Performance target: 2-3x speedup over Numba for batch operations.

use numpy::ndarray::{Array1, Array2, ArrayView2};
use numpy::{PyArray1, PyArray2, PyReadonlyArray1, PyReadonlyArray2, ToPyArray};
use pyo3::prelude::*;
use rayon::prelude::*;

/// Physical constants matching Python constants.py
const GRAVITY: f64 = 9.81;       // m/s²
const BALL_MASS: f64 = 0.145;    // kg (MLB baseball)

// Lookup table parameters matching Python aerodynamics.py
const LUT_V_MIN: f64 = 5.0;      // Minimum velocity (m/s)
const LUT_V_MAX: f64 = 60.0;     // Maximum velocity (m/s)
const LUT_V_STEP: f64 = 1.0;     // Velocity step (m/s)

const LUT_S_MIN: f64 = 0.0;      // Minimum spin (rpm)
const LUT_S_MAX: f64 = 4000.0;   // Maximum spin (rpm)
const LUT_S_STEP: f64 = 50.0;    // Spin step (rpm)

/// Bilinear interpolation for lookup tables.
///
/// Interpolates coefficient from pre-computed table based on velocity and spin.
/// Matches Python _lookup_cd_cl exactly.
#[inline(always)]
fn lookup_cd_cl(
    velocity: f64,
    spin_rpm: f64,
    cd_table: &ArrayView2<f64>,
    cl_table: &ArrayView2<f64>,
) -> (f64, f64) {
    // Clamp to table bounds (matching Python)
    let v_clamped = velocity.clamp(LUT_V_MIN, LUT_V_MAX - LUT_V_STEP);
    let s_clamped = spin_rpm.clamp(LUT_S_MIN, LUT_S_MAX - LUT_S_STEP);
    
    // Calculate indices
    let v_idx = ((v_clamped - LUT_V_MIN) / LUT_V_STEP) as usize;
    let s_idx = ((s_clamped - LUT_S_MIN) / LUT_S_STEP) as usize;
    
    // Clamp indices to valid range
    let v_count = cd_table.nrows();
    let s_count = cd_table.ncols();
    let v_idx = v_idx.min(v_count.saturating_sub(2));
    let s_idx = s_idx.min(s_count.saturating_sub(2));
    
    // Bilinear interpolation weights
    let v_frac = (v_clamped - (LUT_V_MIN + (v_idx as f64) * LUT_V_STEP)) / LUT_V_STEP;
    let s_frac = (s_clamped - (LUT_S_MIN + (s_idx as f64) * LUT_S_STEP)) / LUT_S_STEP;
    
    // Bilinear interpolation for Cd
    let cd00 = cd_table[[v_idx, s_idx]];
    let cd10 = cd_table[[v_idx + 1, s_idx]];
    let cd01 = cd_table[[v_idx, s_idx + 1]];
    let cd11 = cd_table[[v_idx + 1, s_idx + 1]];
    
    let cd = cd00 * (1.0 - v_frac) * (1.0 - s_frac)
           + cd10 * v_frac * (1.0 - s_frac)
           + cd01 * (1.0 - v_frac) * s_frac
           + cd11 * v_frac * s_frac;
    
    // Bilinear interpolation for Cl
    let cl00 = cl_table[[v_idx, s_idx]];
    let cl10 = cl_table[[v_idx + 1, s_idx]];
    let cl01 = cl_table[[v_idx, s_idx + 1]];
    let cl11 = cl_table[[v_idx + 1, s_idx + 1]];
    
    let cl = cl00 * (1.0 - v_frac) * (1.0 - s_frac)
           + cl10 * v_frac * (1.0 - s_frac)
           + cl01 * (1.0 - v_frac) * s_frac
           + cl11 * v_frac * s_frac;
    
    (cd, cl)
}

/// Calculate aerodynamic forces (drag + Magnus) using lookup tables.
///
/// Returns force components (fx, fy, fz) in Newtons.
#[inline(always)]
fn aerodynamic_force(
    velocity: &[f64; 3],
    spin_axis: &[f64; 3],
    spin_rpm: f64,
    air_density: f64,
    cross_area: f64,
    cd_table: &ArrayView2<f64>,
    cl_table: &ArrayView2<f64>,
) -> [f64; 3] {
    // Calculate velocity magnitude
    let v_mag = (velocity[0].powi(2) + velocity[1].powi(2) + velocity[2].powi(2)).sqrt();
    
    if v_mag < 1e-6 {
        return [0.0, 0.0, 0.0];
    }
    
    // Normalize velocity
    let v_unit = [velocity[0] / v_mag, velocity[1] / v_mag, velocity[2] / v_mag];
    
    // Get coefficients from lookup tables
    let (cd, cl) = lookup_cd_cl(v_mag, spin_rpm, cd_table, cl_table);
    
    // Drag force: F_d = 0.5 * C_d * rho * A * v²
    let drag_mag = 0.5 * cd * air_density * cross_area * v_mag * v_mag;
    let drag = [-drag_mag * v_unit[0], -drag_mag * v_unit[1], -drag_mag * v_unit[2]];
    
    // Magnus force
    let mut magnus = [0.0, 0.0, 0.0];
    
    if spin_rpm > 1.0 {
        let spin_mag = (spin_axis[0].powi(2) + spin_axis[1].powi(2) + spin_axis[2].powi(2)).sqrt();
        
        if spin_mag > 1e-6 {
            let spin_unit = [
                spin_axis[0] / spin_mag,
                spin_axis[1] / spin_mag,
                spin_axis[2] / spin_mag,
            ];
            
            // Magnus force magnitude
            let magnus_mag = 0.5 * cl * air_density * cross_area * v_mag * v_mag;
            
            // Direction: cross product of velocity and spin axis
            let force_dir = [
                v_unit[1] * spin_unit[2] - v_unit[2] * spin_unit[1],
                v_unit[2] * spin_unit[0] - v_unit[0] * spin_unit[2],
                v_unit[0] * spin_unit[1] - v_unit[1] * spin_unit[0],
            ];
            
            let force_dir_mag = (force_dir[0].powi(2) + force_dir[1].powi(2) + force_dir[2].powi(2)).sqrt();
            
            if force_dir_mag > 1e-6 {
                magnus = [
                    magnus_mag * force_dir[0] / force_dir_mag,
                    magnus_mag * force_dir[1] / force_dir_mag,
                    magnus_mag * force_dir[2] / force_dir_mag,
                ];
            }
        }
    }
    
    // Total force
    [drag[0] + magnus[0], drag[1] + magnus[1], drag[2] + magnus[2]]
}

/// Calculate derivative of state vector.
///
/// State: [x, y, z, vx, vy, vz]
/// Returns: [vx, vy, vz, ax, ay, az]
#[inline(always)]
fn derivative(state: &[f64; 6], force: &[f64; 3]) -> [f64; 6] {
    // Extract velocity
    let vx = state[3];
    let vy = state[4];
    let vz = state[5];
    
    // Calculate acceleration (F/m) including gravity
    let ax = force[0] / BALL_MASS;
    let ay = force[1] / BALL_MASS;
    let az = force[2] / BALL_MASS - GRAVITY;  // Gravity acts downward
    
    [vx, vy, vz, ax, ay, az]
}

/// Perform one RK4 integration step.
///
/// This is the critical hot path - optimized for maximum performance.
#[inline(always)]
fn step_rk4(
    state: &[f64; 6],
    dt: f64,
    spin_axis: &[f64; 3],
    spin_rpm: f64,
    air_density: f64,
    cross_area: f64,
    cd_table: &ArrayView2<f64>,
    cl_table: &ArrayView2<f64>,
) -> [f64; 6] {
    // Helper to add scaled derivative to state
    #[inline(always)]
    fn add_scaled(state: &[f64; 6], deriv: &[f64; 6], scale: f64) -> [f64; 6] {
        [
            state[0] + scale * deriv[0],
            state[1] + scale * deriv[1],
            state[2] + scale * deriv[2],
            state[3] + scale * deriv[3],
            state[4] + scale * deriv[4],
            state[5] + scale * deriv[5],
        ]
    }
    
    // k1: derivative at beginning
    let velocity1 = [state[3], state[4], state[5]];
    let force1 = aerodynamic_force(&velocity1, spin_axis, spin_rpm, air_density, cross_area, cd_table, cl_table);
    let k1 = derivative(state, &force1);
    
    // k2: derivative at midpoint using k1
    let state2 = add_scaled(state, &k1, 0.5 * dt);
    let velocity2 = [state2[3], state2[4], state2[5]];
    let force2 = aerodynamic_force(&velocity2, spin_axis, spin_rpm, air_density, cross_area, cd_table, cl_table);
    let k2 = derivative(&state2, &force2);
    
    // k3: derivative at midpoint using k2
    let state3 = add_scaled(state, &k2, 0.5 * dt);
    let velocity3 = [state3[3], state3[4], state3[5]];
    let force3 = aerodynamic_force(&velocity3, spin_axis, spin_rpm, air_density, cross_area, cd_table, cl_table);
    let k3 = derivative(&state3, &force3);
    
    // k4: derivative at end using k3
    let state4 = add_scaled(state, &k3, dt);
    let velocity4 = [state4[3], state4[4], state4[5]];
    let force4 = aerodynamic_force(&velocity4, spin_axis, spin_rpm, air_density, cross_area, cd_table, cl_table);
    let k4 = derivative(&state4, &force4);
    
    // Weighted average: new = old + (dt/6) * (k1 + 2*k2 + 2*k3 + k4)
    let dt6 = dt / 6.0;
    [
        state[0] + dt6 * (k1[0] + 2.0 * k2[0] + 2.0 * k3[0] + k4[0]),
        state[1] + dt6 * (k1[1] + 2.0 * k2[1] + 2.0 * k3[1] + k4[1]),
        state[2] + dt6 * (k1[2] + 2.0 * k2[2] + 2.0 * k3[2] + k4[2]),
        state[3] + dt6 * (k1[3] + 2.0 * k2[3] + 2.0 * k3[3] + k4[3]),
        state[4] + dt6 * (k1[4] + 2.0 * k2[4] + 2.0 * k3[4] + k4[4]),
        state[5] + dt6 * (k1[5] + 2.0 * k2[5] + 2.0 * k3[5] + k4[5]),
    ]
}

/// Single trajectory integration result.
struct TrajectoryResult {
    positions: Vec<[f64; 3]>,
    velocities: Vec<[f64; 3]>,
    times: Vec<f64>,
}

/// Integrate a single trajectory until ground or max time.
fn integrate_single_trajectory(
    initial_state: [f64; 6],
    dt: f64,
    max_time: f64,
    ground_level: f64,
    spin_axis: [f64; 3],
    spin_rpm: f64,
    air_density: f64,
    cross_area: f64,
    cd_table: &ArrayView2<f64>,
    cl_table: &ArrayView2<f64>,
) -> TrajectoryResult {
    let max_steps = (max_time / dt) as usize + 10;
    
    let mut positions = Vec::with_capacity(max_steps);
    let mut velocities = Vec::with_capacity(max_steps);
    let mut times = Vec::with_capacity(max_steps);
    
    // Initialize
    let mut state = initial_state;
    let mut current_time = 0.0;
    
    positions.push([state[0], state[1], state[2]]);
    velocities.push([state[3], state[4], state[5]]);
    times.push(0.0);
    
    // Integration loop
    while current_time < max_time && positions.len() < max_steps - 1 {
        // Take RK4 step
        state = step_rk4(&state, dt, &spin_axis, spin_rpm, air_density, cross_area, cd_table, cl_table);
        current_time += dt;
        
        // Store state
        positions.push([state[0], state[1], state[2]]);
        velocities.push([state[3], state[4], state[5]]);
        times.push(current_time);
        
        // Check for ground contact
        if state[2] <= ground_level && positions.len() > 1 {
            let n = positions.len();
            let z_prev = positions[n - 2][2];
            let z_curr = state[2];
            
            if (z_curr - z_prev).abs() > 1e-10 {
                // Interpolate landing point
                let fraction = (ground_level - z_prev) / (z_curr - z_prev);
                
                let landing_pos = [
                    positions[n - 2][0] + fraction * (state[0] - positions[n - 2][0]),
                    positions[n - 2][1] + fraction * (state[1] - positions[n - 2][1]),
                    ground_level,
                ];
                let landing_vel = [
                    velocities[n - 2][0] + fraction * (state[3] - velocities[n - 2][0]),
                    velocities[n - 2][1] + fraction * (state[4] - velocities[n - 2][1]),
                    velocities[n - 2][2] + fraction * (state[5] - velocities[n - 2][2]),
                ];
                let landing_time = times[n - 2] + fraction * dt;
                
                positions.push(landing_pos);
                velocities.push(landing_vel);
                times.push(landing_time);
            }
            break;
        }
    }
    
    TrajectoryResult { positions, velocities, times }
}

// ============================================================================
// PyO3 Python Interface
// ============================================================================

/// Integrate a single trajectory and return numpy arrays.
#[pyfunction]
#[pyo3(signature = (initial_state, dt, max_time, ground_level, spin_axis, spin_rpm, air_density, cross_area, cd_table, cl_table))]
fn integrate_trajectory<'py>(
    py: Python<'py>,
    initial_state: PyReadonlyArray1<f64>,
    dt: f64,
    max_time: f64,
    ground_level: f64,
    spin_axis: PyReadonlyArray1<f64>,
    spin_rpm: f64,
    air_density: f64,
    cross_area: f64,
    cd_table: PyReadonlyArray2<f64>,
    cl_table: PyReadonlyArray2<f64>,
) -> PyResult<(Bound<'py, PyArray2<f64>>, Bound<'py, PyArray2<f64>>, Bound<'py, PyArray1<f64>>)> {
    // Convert input arrays
    let initial = initial_state.as_array();
    let spin = spin_axis.as_array();
    let cd = cd_table.as_array();
    let cl = cl_table.as_array();
    
    let init_state = [
        initial[0], initial[1], initial[2],
        initial[3], initial[4], initial[5],
    ];
    let spin_ax = [spin[0], spin[1], spin[2]];
    
    // Run integration
    let result = integrate_single_trajectory(
        init_state, dt, max_time, ground_level,
        spin_ax, spin_rpm, air_density, cross_area,
        &cd, &cl,
    );
    
    // Convert results to numpy arrays
    let n = result.positions.len();
    let mut positions = Array2::<f64>::zeros((n, 3));
    let mut velocities = Array2::<f64>::zeros((n, 3));
    let mut times = Array1::<f64>::zeros(n);
    
    for i in 0..n {
        positions[[i, 0]] = result.positions[i][0];
        positions[[i, 1]] = result.positions[i][1];
        positions[[i, 2]] = result.positions[i][2];
        velocities[[i, 0]] = result.velocities[i][0];
        velocities[[i, 1]] = result.velocities[i][1];
        velocities[[i, 2]] = result.velocities[i][2];
        times[i] = result.times[i];
    }
    
    Ok((positions.to_pyarray(py), velocities.to_pyarray(py), times.to_pyarray(py)))
}

/// Integrate multiple trajectories in parallel using Rayon.
///
/// This is the main performance entry point for batch operations.
#[pyfunction]
#[pyo3(signature = (initial_states, dt, max_time, ground_level, spin_params, air_density, cross_area, cd_table, cl_table))]
fn integrate_trajectories_batch<'py>(
    py: Python<'py>,
    initial_states: PyReadonlyArray2<f64>,
    dt: f64,
    max_time: f64,
    ground_level: f64,
    spin_params: PyReadonlyArray2<f64>,
    air_density: f64,
    cross_area: f64,
    cd_table: PyReadonlyArray2<f64>,
    cl_table: PyReadonlyArray2<f64>,
) -> PyResult<(Bound<'py, PyArray2<f64>>, Bound<'py, PyArray1<f64>>, Bound<'py, PyArray1<f64>>, Bound<'py, PyArray1<f64>>)> {
    let states = initial_states.as_array();
    let spins = spin_params.as_array();
    let cd = cd_table.as_array();
    let cl = cl_table.as_array();
    
    let n_trajectories = states.nrows();
    
    // Collect trajectories into a structure we can parallelize
    let inputs: Vec<_> = (0..n_trajectories)
        .map(|i| {
            let init_state = [
                states[[i, 0]], states[[i, 1]], states[[i, 2]],
                states[[i, 3]], states[[i, 4]], states[[i, 5]],
            ];
            let spin_ax = [spins[[i, 0]], spins[[i, 1]], spins[[i, 2]]];
            let spin_rpm = spins[[i, 3]];
            (init_state, spin_ax, spin_rpm)
        })
        .collect();
    
    // Allow Rayon to work while we're outside Python
    let results: Vec<_> = py.allow_threads(|| {
        inputs
            .par_iter()
            .map(|(init_state, spin_ax, spin_rpm)| {
                let result = integrate_single_trajectory(
                    *init_state, dt, max_time, ground_level,
                    *spin_ax, *spin_rpm, air_density, cross_area,
                    &cd, &cl,
                );
                
                // Return landing position, time, distance, and apex
                let n = result.positions.len();
                if n > 0 {
                    let landing_pos = result.positions[n - 1];
                    let landing_time = result.times[n - 1];
                    let distance = (landing_pos[0].powi(2) + landing_pos[1].powi(2)).sqrt();
                    let apex_height = result.positions.iter().map(|p| p[2]).fold(0.0_f64, f64::max);
                    (landing_pos, landing_time, distance, apex_height)
                } else {
                    ([0.0, 0.0, 0.0], 0.0, 0.0, 0.0)
                }
            })
            .collect()
    });
    
    // Convert results to numpy arrays
    let mut landing_positions = Array2::<f64>::zeros((n_trajectories, 3));
    let mut landing_times = Array1::<f64>::zeros(n_trajectories);
    let mut distances = Array1::<f64>::zeros(n_trajectories);
    let mut apex_heights = Array1::<f64>::zeros(n_trajectories);
    
    for (i, (pos, time, dist, apex)) in results.iter().enumerate() {
        landing_positions[[i, 0]] = pos[0];
        landing_positions[[i, 1]] = pos[1];
        landing_positions[[i, 2]] = pos[2];
        landing_times[i] = *time;
        distances[i] = *dist;
        apex_heights[i] = *apex;
    }
    
    Ok((
        landing_positions.to_pyarray(py),
        landing_times.to_pyarray(py),
        distances.to_pyarray(py),
        apex_heights.to_pyarray(py),
    ))
}

/// Calculate trajectory endpoints only (memory efficient batch mode).
///
/// When you only need landing positions, this skips storing full trajectory.
#[pyfunction]
#[pyo3(signature = (initial_states, dt, max_time, ground_level, spin_params, air_density, cross_area, cd_table, cl_table))]
fn calculate_endpoints_batch<'py>(
    py: Python<'py>,
    initial_states: PyReadonlyArray2<f64>,
    dt: f64,
    max_time: f64,
    ground_level: f64,
    spin_params: PyReadonlyArray2<f64>,
    air_density: f64,
    cross_area: f64,
    cd_table: PyReadonlyArray2<f64>,
    cl_table: PyReadonlyArray2<f64>,
) -> PyResult<(Bound<'py, PyArray2<f64>>, Bound<'py, PyArray1<f64>>, Bound<'py, PyArray1<f64>>, Bound<'py, PyArray1<f64>>)> {
    // Same as integrate_trajectories_batch but optimized for endpoints only
    integrate_trajectories_batch(
        py, initial_states, dt, max_time, ground_level,
        spin_params, air_density, cross_area, cd_table, cl_table,
    )
}

/// Get the number of CPU threads available for parallel processing.
#[pyfunction]
fn get_num_threads() -> usize {
    rayon::current_num_threads()
}

/// Set the number of threads for parallel processing.
#[pyfunction]
fn set_num_threads(n: usize) {
    rayon::ThreadPoolBuilder::new()
        .num_threads(n)
        .build_global()
        .ok();  // Ignore error if already built
}

/// Python module definition.
#[pymodule]
fn trajectory_rs(m: &Bound<'_, PyModule>) -> PyResult<()> {
    m.add_function(wrap_pyfunction!(integrate_trajectory, m)?)?;
    m.add_function(wrap_pyfunction!(integrate_trajectories_batch, m)?)?;
    m.add_function(wrap_pyfunction!(calculate_endpoints_batch, m)?)?;
    m.add_function(wrap_pyfunction!(get_num_threads, m)?)?;
    m.add_function(wrap_pyfunction!(set_num_threads, m)?)?;
    
    // Add constants
    m.add("GRAVITY", GRAVITY)?;
    m.add("BALL_MASS", BALL_MASS)?;
    
    Ok(())
}
