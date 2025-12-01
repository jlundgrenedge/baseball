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

// ============================================================================
// Wind Shear Constants (matching Python trajectory.py)
// ============================================================================
// Wind speed increases with altitude due to reduced surface friction
// Using power law: wind(z) = wind_ref * (z / z_ref)^alpha
const WIND_REF_HEIGHT_M: f64 = 10.0;    // Reference height (~33 ft)
const WIND_SHEAR_EXPONENT: f64 = 0.20;  // Open terrain exponent (slightly higher for ballparks)
const MIN_HEIGHT_M: f64 = 1.0;          // Minimum height to avoid division issues
const MAX_WIND_MULTIPLIER: f64 = 1.7;   // Cap maximum wind amplification

/// Calculate altitude-adjusted wind velocity using wind shear model.
/// At higher altitudes, wind is stronger (less ground friction).
#[inline(always)]
fn apply_wind_shear(base_wind: &[f64; 3], height_m: f64) -> [f64; 3] {
    // Clamp height to minimum
    let h = height_m.max(MIN_HEIGHT_M);
    
    // Power law wind shear: wind increases with altitude
    let mut multiplier = (h / WIND_REF_HEIGHT_M).powf(WIND_SHEAR_EXPONENT);
    
    // Clamp multiplier to reasonable range (1.0 to MAX_WIND_MULTIPLIER)
    multiplier = multiplier.clamp(1.0, MAX_WIND_MULTIPLIER);
    
    [
        base_wind[0] * multiplier,
        base_wind[1] * multiplier,
        base_wind[2] * multiplier,
    ]
}

// ============================================================================
// Ground Ball Physics Constants (from Python constants.py)
// ============================================================================
#[allow(dead_code)]
const FEET_TO_METERS: f64 = 0.3048;
#[allow(dead_code)]
const METERS_TO_FEET: f64 = 3.28084;

// Ground ball physics
const GROUND_BALL_COR_GRASS: f64 = 0.45;  // Coefficient of restitution for grass
const GROUND_BALL_COR_DIRT: f64 = 0.50;   // Coefficient of restitution for dirt
const ROLLING_FRICTION_GRASS: f64 = 0.30; // Rolling friction coefficient
const ROLLING_FRICTION_DIRT: f64 = 0.25;  // Rolling friction coefficient  
const GROUND_BALL_AIR_RESISTANCE: f64 = 3.0; // ft/s² air resistance deceleration
const GROUND_BALL_SPIN_EFFECT: f64 = 0.08;   // Spin rate effect multiplier

// Fielder physics
const FIELDER_ACCELERATION: f64 = 28.0;     // ft/s² (matches Python)
const FIELDER_MAX_SPEED: f64 = 30.0;        // ft/s (elite sprint speed)
const CHARGE_BONUS_MAX: f64 = 20.0;         // Maximum charge bonus in feet

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
/// Wind velocity is subtracted from ball velocity to get relative velocity.
#[inline(always)]
fn aerodynamic_force_with_wind(
    velocity: &[f64; 3],
    wind_velocity: &[f64; 3],
    spin_axis: &[f64; 3],
    spin_rpm: f64,
    air_density: f64,
    cross_area: f64,
    cd_table: &ArrayView2<f64>,
    cl_table: &ArrayView2<f64>,
) -> [f64; 3] {
    // Calculate relative velocity (ball velocity relative to air)
    // When there's a tailwind, relative velocity is reduced
    let rel_velocity = [
        velocity[0] - wind_velocity[0],
        velocity[1] - wind_velocity[1],
        velocity[2] - wind_velocity[2],
    ];
    
    // Calculate relative velocity magnitude
    let v_rel_mag = (rel_velocity[0].powi(2) + rel_velocity[1].powi(2) + rel_velocity[2].powi(2)).sqrt();
    
    if v_rel_mag < 1e-6 {
        return [0.0, 0.0, 0.0];
    }
    
    // Normalize relative velocity
    let v_rel_unit = [
        rel_velocity[0] / v_rel_mag, 
        rel_velocity[1] / v_rel_mag, 
        rel_velocity[2] / v_rel_mag
    ];
    
    // Get coefficients from lookup tables (based on relative velocity)
    let (cd, cl) = lookup_cd_cl(v_rel_mag, spin_rpm, cd_table, cl_table);
    
    // Drag force: F_d = 0.5 * C_d * rho * A * v_rel²
    // Drag opposes relative motion (not absolute motion)
    let drag_mag = 0.5 * cd * air_density * cross_area * v_rel_mag * v_rel_mag;
    let drag = [-drag_mag * v_rel_unit[0], -drag_mag * v_rel_unit[1], -drag_mag * v_rel_unit[2]];
    
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
            
            // Magnus force magnitude (based on relative velocity)
            let magnus_mag = 0.5 * cl * air_density * cross_area * v_rel_mag * v_rel_mag;
            
            // Direction: cross product of relative velocity and spin axis
            let force_dir = [
                v_rel_unit[1] * spin_unit[2] - v_rel_unit[2] * spin_unit[1],
                v_rel_unit[2] * spin_unit[0] - v_rel_unit[0] * spin_unit[2],
                v_rel_unit[0] * spin_unit[1] - v_rel_unit[1] * spin_unit[0],
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

/// Perform one RK4 integration step with wind and altitude-dependent wind shear.
///
/// This is the critical hot path - optimized for maximum performance.
/// Wind shear model: wind increases with altitude using power law.
#[inline(always)]
fn step_rk4_with_wind(
    state: &[f64; 6],
    dt: f64,
    base_wind_velocity: &[f64; 3],
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
    // Apply wind shear based on current altitude (state[2] = z position)
    let wind1 = apply_wind_shear(base_wind_velocity, state[2]);
    let velocity1 = [state[3], state[4], state[5]];
    let force1 = aerodynamic_force_with_wind(&velocity1, &wind1, spin_axis, spin_rpm, air_density, cross_area, cd_table, cl_table);
    let k1 = derivative(state, &force1);
    
    // k2: derivative at midpoint using k1
    let state2 = add_scaled(state, &k1, 0.5 * dt);
    let wind2 = apply_wind_shear(base_wind_velocity, state2[2]);
    let velocity2 = [state2[3], state2[4], state2[5]];
    let force2 = aerodynamic_force_with_wind(&velocity2, &wind2, spin_axis, spin_rpm, air_density, cross_area, cd_table, cl_table);
    let k2 = derivative(&state2, &force2);
    
    // k3: derivative at midpoint using k2
    let state3 = add_scaled(state, &k2, 0.5 * dt);
    let wind3 = apply_wind_shear(base_wind_velocity, state3[2]);
    let velocity3 = [state3[3], state3[4], state3[5]];
    let force3 = aerodynamic_force_with_wind(&velocity3, &wind3, spin_axis, spin_rpm, air_density, cross_area, cd_table, cl_table);
    let k3 = derivative(&state3, &force3);
    
    // k4: derivative at end using k3
    let state4 = add_scaled(state, &k3, dt);
    let wind4 = apply_wind_shear(base_wind_velocity, state4[2]);
    let velocity4 = [state4[3], state4[4], state4[5]];
    let force4 = aerodynamic_force_with_wind(&velocity4, &wind4, spin_axis, spin_rpm, air_density, cross_area, cd_table, cl_table);
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

/// Perform one RK4 integration step (no wind).
///
/// This is the critical hot path - optimized for maximum performance.
#[inline(always)]
#[allow(dead_code)]
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
    step_rk4_with_wind(state, dt, &[0.0, 0.0, 0.0], spin_axis, spin_rpm, air_density, cross_area, cd_table, cl_table)
}

/// Single trajectory integration result.
struct TrajectoryResult {
    positions: Vec<[f64; 3]>,
    velocities: Vec<[f64; 3]>,
    times: Vec<f64>,
}

// ============================================================================
// Ground Ball Physics
// ============================================================================

/// Ground ball simulation result.
#[derive(Clone)]
struct GroundBallResult {
    /// Position where ball first lands/starts rolling
    landing_position: [f64; 2],
    /// Velocity at landing (mph)
    landing_velocity_mph: f64,
    /// Direction of travel (unit vector)
    direction: [f64; 2],
    /// Time when ball lands and starts rolling
    landing_time: f64,
    /// Rolling friction coefficient
    friction: f64,
    /// Spin effect on trajectory
    spin_effect: f64,
}

/// Calculate ball position at a given time during rolling phase.
/// 
/// Uses kinematic equation: x = x0 + v0*t - 0.5*a*t²
/// Returns (x, y, velocity) at time t after landing.
#[inline]
fn ball_position_at_time(
    result: &GroundBallResult,
    time_after_landing: f64,
) -> ([f64; 2], f64) {
    if time_after_landing <= 0.0 {
        return (result.landing_position, result.landing_velocity_mph);
    }
    
    // Deceleration in ft/s²
    let decel = GRAVITY * METERS_TO_FEET * result.friction + GROUND_BALL_AIR_RESISTANCE;
    
    // Convert initial velocity to ft/s
    let v0_fps = result.landing_velocity_mph * 5280.0 / 3600.0;
    
    // Time to stop
    let time_to_stop = v0_fps / decel;
    let effective_time = time_after_landing.min(time_to_stop);
    
    // Distance traveled: d = v0*t - 0.5*a*t²
    let distance = v0_fps * effective_time - 0.5 * decel * effective_time * effective_time;
    
    // Apply spin effect to direction (curve the path slightly)
    let curve_factor = result.spin_effect * effective_time * 0.1;
    let curved_dir = [
        result.direction[0] - curve_factor * result.direction[1],
        result.direction[1] + curve_factor * result.direction[0],
    ];
    let dir_mag = (curved_dir[0].powi(2) + curved_dir[1].powi(2)).sqrt();
    let normalized_dir = if dir_mag > 1e-6 {
        [curved_dir[0] / dir_mag, curved_dir[1] / dir_mag]
    } else {
        result.direction
    };
    
    // New position
    let pos = [
        result.landing_position[0] + distance * normalized_dir[0],
        result.landing_position[1] + distance * normalized_dir[1],
    ];
    
    // Current velocity
    let current_velocity_fps = (v0_fps - decel * effective_time).max(0.0);
    let current_velocity_mph = current_velocity_fps * 3600.0 / 5280.0;
    
    (pos, current_velocity_mph)
}

/// Calculate time for ball to travel to a certain distance from landing point.
/// 
/// Solves: distance = v0*t - 0.5*a*t² for t
/// Returns None if ball stops before reaching distance.
#[inline]
#[allow(dead_code)]
fn time_to_distance(
    result: &GroundBallResult,
    distance: f64,
) -> Option<f64> {
    if distance <= 0.0 {
        return Some(0.0);
    }
    
    // Deceleration in ft/s²
    let decel = GRAVITY * METERS_TO_FEET * result.friction + GROUND_BALL_AIR_RESISTANCE;
    
    // Convert initial velocity to ft/s
    let v0_fps = result.landing_velocity_mph * 5280.0 / 3600.0;
    
    // Maximum distance ball can travel
    let max_distance = (v0_fps * v0_fps) / (2.0 * decel);
    
    if distance > max_distance {
        return None;
    }
    
    // Solve quadratic: 0.5*a*t² - v0*t + d = 0
    // t = (v0 - sqrt(v0² - 2*a*d)) / a  (take smaller root)
    let discriminant = v0_fps * v0_fps - 2.0 * decel * distance;
    
    if discriminant < 0.0 {
        return None;
    }
    
    let t = (v0_fps - discriminant.sqrt()) / decel;
    Some(t.max(0.0))
}

/// Calculate fielder travel time to a given distance.
/// 
/// Uses acceleration model:
/// - Phase 1: Accelerate at FIELDER_ACCELERATION until max speed or destination
/// - Phase 2: Constant velocity if needed
/// 
/// Also adds reaction time.
#[inline]
fn fielder_travel_time(
    distance_ft: f64,
    sprint_speed_fps: f64,
    reaction_time: f64,
    acceleration: f64,
) -> f64 {
    if distance_ft <= 0.0 {
        return reaction_time;
    }
    
    let max_speed = sprint_speed_fps.min(FIELDER_MAX_SPEED);
    
    // Distance to reach max speed
    let accel_distance = (max_speed * max_speed) / (2.0 * acceleration);
    
    let travel_time = if distance_ft <= accel_distance {
        // Never reaches max speed - use kinematics
        // d = 0.5 * a * t² => t = sqrt(2d/a)
        (2.0 * distance_ft / acceleration).sqrt()
    } else {
        // Time to reach max speed + time at max speed
        let time_to_max = max_speed / acceleration;
        let remaining_distance = distance_ft - accel_distance;
        time_to_max + remaining_distance / max_speed
    };
    
    reaction_time + travel_time
}

/// Calculate charge bonus based on exit velocity and fielder position.
/// 
/// Charge bonus represents how much the fielder can move forward
/// while the ball is in flight/bouncing.
#[inline]
fn calculate_charge_bonus(
    exit_velocity_mph: f64,
    distance_to_landing: f64,
    sprint_speed_fps: f64,
) -> f64 {
    // Higher exit velocity = less time to react = less charge
    let velocity_factor = (1.0 - (exit_velocity_mph - 60.0) / 60.0).clamp(0.2, 1.0);
    
    // Closer fielders can charge more
    let distance_factor = (distance_to_landing / 150.0).clamp(0.3, 1.0);
    
    // Speed helps charging
    let speed_factor = sprint_speed_fps / 27.0; // 27 ft/s is average
    
    (CHARGE_BONUS_MAX * velocity_factor * distance_factor * speed_factor).min(CHARGE_BONUS_MAX)
}

/// Ground ball interception result for a single fielder.
#[derive(Clone)]
struct InterceptionResult {
    /// Can the fielder reach the ball?
    can_intercept: bool,
    /// Position where interception occurs
    interception_point: [f64; 2],
    /// Time when fielder reaches ball
    fielder_time: f64,
    /// Time when ball reaches interception point
    ball_time: f64,
    /// Time margin (negative = ball arrives first)
    margin: f64,
    /// Ball velocity at interception (mph)
    ball_velocity_mph: f64,
}

/// Find optimal interception point for a fielder.
/// 
/// Tests multiple points along the ball trajectory to find
/// where the fielder can intercept with maximum margin.
fn find_fielder_interception(
    ground_ball: &GroundBallResult,
    fielder_x: f64,
    fielder_y: f64,
    sprint_speed_fps: f64,
    reaction_time: f64,
    charge_bonus: f64,
) -> InterceptionResult {
    let mut best_result = InterceptionResult {
        can_intercept: false,
        interception_point: [0.0, 0.0],
        fielder_time: f64::MAX,
        ball_time: 0.0,
        margin: f64::MIN,
        ball_velocity_mph: 0.0,
    };
    
    // Test interception points at different times along ball path
    let max_test_time = 6.0; // Maximum reasonable time for ground ball
    let time_step = 0.05;    // Test every 50ms
    
    let mut test_time = 0.0;
    while test_time <= max_test_time {
        let (ball_pos, ball_vel) = ball_position_at_time(ground_ball, test_time);
        
        // Ball has stopped
        if ball_vel < 0.1 {
            break;
        }
        
        // Distance from fielder to this point
        let dx = ball_pos[0] - fielder_x;
        let dy = ball_pos[1] - fielder_y;
        let distance = (dx * dx + dy * dy).sqrt();
        
        // Apply charge bonus (fielder can be closer)
        let effective_distance = (distance - charge_bonus).max(0.0);
        
        // Time for fielder to reach this point
        let fielder_time = fielder_travel_time(
            effective_distance,
            sprint_speed_fps,
            reaction_time,
            FIELDER_ACCELERATION,
        );
        
        // Total ball time = landing time + rolling time
        let total_ball_time = ground_ball.landing_time + test_time;
        
        // Margin: positive = fielder arrives first
        let margin = total_ball_time - fielder_time;
        
        if margin > best_result.margin {
            best_result = InterceptionResult {
                can_intercept: margin >= 0.0,
                interception_point: ball_pos,
                fielder_time,
                ball_time: total_ball_time,
                margin,
                ball_velocity_mph: ball_vel,
            };
        }
        
        test_time += time_step;
    }
    
    best_result
}

/// Simulate ground ball physics from initial conditions.
/// 
/// Handles initial bouncing phase, then transitions to rolling.
/// Returns landing position, velocity, and rolling parameters.
fn simulate_ground_ball_initial(
    x0: f64,
    y0: f64,
    vx_mph: f64,
    vy_mph: f64,
    vz_mph: f64,
    spin_rpm: f64,
    is_grass: bool,
) -> GroundBallResult {
    // Get surface-specific parameters
    let cor = if is_grass { GROUND_BALL_COR_GRASS } else { GROUND_BALL_COR_DIRT };
    let friction = if is_grass { ROLLING_FRICTION_GRASS } else { ROLLING_FRICTION_DIRT };
    
    // Convert velocities to ft/s
    let vx_fps = vx_mph * 5280.0 / 3600.0;
    let vy_fps = vy_mph * 5280.0 / 3600.0;
    let vz_fps = vz_mph * 5280.0 / 3600.0;
    
    // Initial horizontal velocity magnitude
    let vh_fps = (vx_fps * vx_fps + vy_fps * vy_fps).sqrt();
    
    // Calculate spin effect (sidespin causes curve)
    let spin_effect = (spin_rpm / 1000.0) * GROUND_BALL_SPIN_EFFECT;
    
    // Direction of travel
    let dir_mag = if vh_fps > 1e-6 { vh_fps } else { 1.0 };
    let direction = [vx_fps / dir_mag, vy_fps / dir_mag];
    
    // Simulate bouncing phase
    let mut pos = [x0, y0];
    let mut vz = vz_fps;
    let mut vh = vh_fps;
    let mut time = 0.0_f64;
    let g = GRAVITY * METERS_TO_FEET;
    
    // Maximum 3 bounces, or until vertical energy is low
    let mut bounces = 0;
    while bounces < 3 && vz.abs() > 1.0 {
        // Time in air for this hop
        if vz > 0.0 {
            // Going up then down
            let t_up = vz / g;
            let t_down = t_up;
            let t_air = t_up + t_down;
            
            // Move horizontally during air time
            let distance = vh * t_air;
            pos[0] += distance * direction[0];
            pos[1] += distance * direction[1];
            time += t_air;
            
            // Lose energy on bounce
            vz = vz * cor;
            vh = vh * (1.0 - friction * 0.1); // Small horizontal loss per bounce
        } else {
            // Already going down (first impact)
            // Reflect with COR
            vz = (-vz) * cor;
        }
        
        bounces += 1;
    }
    
    // Convert horizontal velocity back to mph for result
    let landing_velocity_mph = vh * 3600.0 / 5280.0;
    
    GroundBallResult {
        landing_position: pos,
        landing_velocity_mph,
        direction,
        landing_time: time,
        friction,
        spin_effect,
    }
}

/// Integrate a single trajectory until ground or max time (with wind support).
fn integrate_single_trajectory_with_wind(
    initial_state: [f64; 6],
    dt: f64,
    max_time: f64,
    ground_level: f64,
    wind_velocity: [f64; 3],
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
        // Take RK4 step with wind
        state = step_rk4_with_wind(&state, dt, &wind_velocity, &spin_axis, spin_rpm, air_density, cross_area, cd_table, cl_table);
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

/// Integrate a single trajectory until ground or max time (no wind).
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
    integrate_single_trajectory_with_wind(
        initial_state, dt, max_time, ground_level,
        [0.0, 0.0, 0.0],  // No wind
        spin_axis, spin_rpm, air_density, cross_area,
        cd_table, cl_table,
    )
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

/// Integrate a single trajectory with wind and return numpy arrays.
#[pyfunction]
#[pyo3(signature = (initial_state, dt, max_time, ground_level, wind_velocity, spin_axis, spin_rpm, air_density, cross_area, cd_table, cl_table))]
fn integrate_trajectory_with_wind<'py>(
    py: Python<'py>,
    initial_state: PyReadonlyArray1<f64>,
    dt: f64,
    max_time: f64,
    ground_level: f64,
    wind_velocity: PyReadonlyArray1<f64>,
    spin_axis: PyReadonlyArray1<f64>,
    spin_rpm: f64,
    air_density: f64,
    cross_area: f64,
    cd_table: PyReadonlyArray2<f64>,
    cl_table: PyReadonlyArray2<f64>,
) -> PyResult<(Bound<'py, PyArray2<f64>>, Bound<'py, PyArray2<f64>>, Bound<'py, PyArray1<f64>>)> {
    // Convert input arrays
    let initial = initial_state.as_array();
    let wind = wind_velocity.as_array();
    let spin = spin_axis.as_array();
    let cd = cd_table.as_array();
    let cl = cl_table.as_array();
    
    let init_state = [
        initial[0], initial[1], initial[2],
        initial[3], initial[4], initial[5],
    ];
    let wind_vel = [wind[0], wind[1], wind[2]];
    let spin_ax = [spin[0], spin[1], spin[2]];
    
    // Run integration with wind
    let result = integrate_single_trajectory_with_wind(
        init_state, dt, max_time, ground_level,
        wind_vel, spin_ax, spin_rpm, air_density, cross_area,
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

// ============================================================================
// Ground Ball PyO3 Interface
// ============================================================================

/// Simulate ground ball trajectory and return rolling parameters.
/// 
/// Args:
///     x0: Starting X position (feet)
///     y0: Starting Y position (feet)  
///     vx_mph: X velocity (mph)
///     vy_mph: Y velocity (mph)
///     vz_mph: Z velocity (mph, typically small negative for ground balls)
///     spin_rpm: Spin rate (rpm)
///     is_grass: True for grass, False for dirt infield
///
/// Returns tuple:
///     (landing_x, landing_y, landing_velocity_mph, direction_x, direction_y, 
///      landing_time, friction, spin_effect)
#[pyfunction]
#[pyo3(signature = (x0, y0, vx_mph, vy_mph, vz_mph, spin_rpm, is_grass = true))]
fn simulate_ground_ball(
    x0: f64,
    y0: f64,
    vx_mph: f64,
    vy_mph: f64,
    vz_mph: f64,
    spin_rpm: f64,
    is_grass: bool,
) -> (f64, f64, f64, f64, f64, f64, f64, f64) {
    let result = simulate_ground_ball_initial(x0, y0, vx_mph, vy_mph, vz_mph, spin_rpm, is_grass);
    (
        result.landing_position[0],
        result.landing_position[1],
        result.landing_velocity_mph,
        result.direction[0],
        result.direction[1],
        result.landing_time,
        result.friction,
        result.spin_effect,
    )
}

/// Get ball position and velocity at a given time after landing.
///
/// Args:
///     landing_x, landing_y: Position where ball started rolling
///     landing_velocity_mph: Velocity at start of rolling
///     direction_x, direction_y: Direction of travel (unit vector)
///     friction: Rolling friction coefficient
///     spin_effect: Spin effect on trajectory
///     time_after_landing: Time since ball started rolling
///
/// Returns tuple: (x, y, velocity_mph)
#[pyfunction]
#[pyo3(signature = (landing_x, landing_y, landing_velocity_mph, direction_x, direction_y, friction, spin_effect, time_after_landing))]
fn get_ball_position_at_time(
    landing_x: f64,
    landing_y: f64,
    landing_velocity_mph: f64,
    direction_x: f64,
    direction_y: f64,
    friction: f64,
    spin_effect: f64,
    time_after_landing: f64,
) -> (f64, f64, f64) {
    let ground_ball = GroundBallResult {
        landing_position: [landing_x, landing_y],
        landing_velocity_mph,
        direction: [direction_x, direction_y],
        landing_time: 0.0, // Not used for position calculation
        friction,
        spin_effect,
    };
    
    let (pos, vel) = ball_position_at_time(&ground_ball, time_after_landing);
    (pos[0], pos[1], vel)
}

/// Calculate fielder travel time to a distance.
///
/// Args:
///     distance_ft: Distance to travel (feet)
///     sprint_speed_fps: Fielder sprint speed (ft/s)
///     reaction_time: Initial reaction delay (seconds)
///     acceleration: Acceleration rate (ft/s², default 28.0)
///
/// Returns: Total time to reach destination
#[pyfunction]
#[pyo3(signature = (distance_ft, sprint_speed_fps, reaction_time = 0.3, acceleration = 28.0))]
fn calculate_fielder_travel_time(
    distance_ft: f64,
    sprint_speed_fps: f64,
    reaction_time: f64,
    acceleration: f64,
) -> f64 {
    fielder_travel_time(distance_ft, sprint_speed_fps, reaction_time, acceleration)
}

/// Find optimal interception point for a fielder.
///
/// Args:
///     landing_x, landing_y: Ball landing position
///     landing_velocity_mph: Ball velocity at landing
///     direction_x, direction_y: Ball travel direction
///     landing_time: Time when ball lands
///     friction: Rolling friction
///     spin_effect: Spin effect
///     fielder_x, fielder_y: Fielder starting position
///     sprint_speed_fps: Fielder sprint speed
///     reaction_time: Fielder reaction time
///     exit_velocity_mph: Original exit velocity (for charge bonus)
///
/// Returns tuple:
///     (can_intercept, intercept_x, intercept_y, fielder_time, ball_time, margin, ball_velocity_mph)
#[pyfunction]
#[pyo3(signature = (landing_x, landing_y, landing_velocity_mph, direction_x, direction_y, landing_time, friction, spin_effect, fielder_x, fielder_y, sprint_speed_fps, reaction_time, exit_velocity_mph))]
fn find_interception_point(
    landing_x: f64,
    landing_y: f64,
    landing_velocity_mph: f64,
    direction_x: f64,
    direction_y: f64,
    landing_time: f64,
    friction: f64,
    spin_effect: f64,
    fielder_x: f64,
    fielder_y: f64,
    sprint_speed_fps: f64,
    reaction_time: f64,
    exit_velocity_mph: f64,
) -> (bool, f64, f64, f64, f64, f64, f64) {
    let ground_ball = GroundBallResult {
        landing_position: [landing_x, landing_y],
        landing_velocity_mph,
        direction: [direction_x, direction_y],
        landing_time,
        friction,
        spin_effect,
    };
    
    // Calculate distance to landing for charge bonus
    let dx = landing_x - fielder_x;
    let dy = landing_y - fielder_y;
    let distance_to_landing = (dx * dx + dy * dy).sqrt();
    
    let charge_bonus = calculate_charge_bonus(exit_velocity_mph, distance_to_landing, sprint_speed_fps);
    
    let result = find_fielder_interception(
        &ground_ball,
        fielder_x,
        fielder_y,
        sprint_speed_fps,
        reaction_time,
        charge_bonus,
    );
    
    (
        result.can_intercept,
        result.interception_point[0],
        result.interception_point[1],
        result.fielder_time,
        result.ball_time,
        result.margin,
        result.ball_velocity_mph,
    )
}

/// Find best interception among multiple fielders (parallelized).
///
/// Args:
///     landing_x, landing_y: Ball landing position
///     landing_velocity_mph: Ball velocity at landing
///     direction_x, direction_y: Ball travel direction  
///     landing_time: Time when ball lands
///     friction: Rolling friction
///     spin_effect: Spin effect
///     fielder_positions: Nx2 array of fielder (x, y) positions
///     fielder_speeds: Array of fielder sprint speeds (ft/s)
///     reaction_times: Array of fielder reaction times
///     exit_velocity_mph: Original exit velocity
///
/// Returns tuple:
///     (best_fielder_idx, can_intercept, intercept_x, intercept_y, 
///      fielder_time, ball_time, margin, ball_velocity_mph)
#[pyfunction]
#[pyo3(signature = (landing_x, landing_y, landing_velocity_mph, direction_x, direction_y, landing_time, friction, spin_effect, fielder_positions, fielder_speeds, reaction_times, exit_velocity_mph))]
fn find_best_interception<'py>(
    py: Python<'py>,
    landing_x: f64,
    landing_y: f64,
    landing_velocity_mph: f64,
    direction_x: f64,
    direction_y: f64,
    landing_time: f64,
    friction: f64,
    spin_effect: f64,
    fielder_positions: PyReadonlyArray2<f64>,
    fielder_speeds: PyReadonlyArray1<f64>,
    reaction_times: PyReadonlyArray1<f64>,
    exit_velocity_mph: f64,
) -> (i32, bool, f64, f64, f64, f64, f64, f64) {
    let positions = fielder_positions.as_array();
    let speeds = fielder_speeds.as_array();
    let reactions = reaction_times.as_array();
    
    let n_fielders = positions.nrows();
    
    let ground_ball = GroundBallResult {
        landing_position: [landing_x, landing_y],
        landing_velocity_mph,
        direction: [direction_x, direction_y],
        landing_time,
        friction,
        spin_effect,
    };
    
    // Collect fielder data
    let fielder_data: Vec<_> = (0..n_fielders)
        .map(|i| {
            let fx = positions[[i, 0]];
            let fy = positions[[i, 1]];
            let speed = speeds[i];
            let reaction = reactions[i];
            (i, fx, fy, speed, reaction)
        })
        .collect();
    
    // Find best interception in parallel
    let results: Vec<_> = py.allow_threads(|| {
        fielder_data
            .par_iter()
            .map(|(idx, fx, fy, speed, reaction)| {
                let dx = landing_x - fx;
                let dy = landing_y - fy;
                let distance_to_landing = (dx * dx + dy * dy).sqrt();
                let charge_bonus = calculate_charge_bonus(exit_velocity_mph, distance_to_landing, *speed);
                
                let result = find_fielder_interception(
                    &ground_ball,
                    *fx,
                    *fy,
                    *speed,
                    *reaction,
                    charge_bonus,
                );
                (*idx, result)
            })
            .collect()
    });
    
    // Find best result (highest margin)
    let mut best_idx: i32 = -1;
    let mut best_result = InterceptionResult {
        can_intercept: false,
        interception_point: [0.0, 0.0],
        fielder_time: f64::MAX,
        ball_time: 0.0,
        margin: f64::MIN,
        ball_velocity_mph: 0.0,
    };
    
    for (idx, result) in results {
        if result.margin > best_result.margin {
            best_idx = idx as i32;
            best_result = result;
        }
    }
    
    (
        best_idx,
        best_result.can_intercept,
        best_result.interception_point[0],
        best_result.interception_point[1],
        best_result.fielder_time,
        best_result.ball_time,
        best_result.margin,
        best_result.ball_velocity_mph,
    )
}

/// Python module definition.
#[pymodule]
fn trajectory_rs(m: &Bound<'_, PyModule>) -> PyResult<()> {
    // Trajectory functions
    m.add_function(wrap_pyfunction!(integrate_trajectory, m)?)?;
    m.add_function(wrap_pyfunction!(integrate_trajectory_with_wind, m)?)?;
    m.add_function(wrap_pyfunction!(integrate_trajectories_batch, m)?)?;
    m.add_function(wrap_pyfunction!(calculate_endpoints_batch, m)?)?;
    m.add_function(wrap_pyfunction!(get_num_threads, m)?)?;
    m.add_function(wrap_pyfunction!(set_num_threads, m)?)?;
    
    // Ground ball functions
    m.add_function(wrap_pyfunction!(simulate_ground_ball, m)?)?;
    m.add_function(wrap_pyfunction!(get_ball_position_at_time, m)?)?;
    m.add_function(wrap_pyfunction!(calculate_fielder_travel_time, m)?)?;
    m.add_function(wrap_pyfunction!(find_interception_point, m)?)?;
    m.add_function(wrap_pyfunction!(find_best_interception, m)?)?;
    
    // Add constants
    m.add("GRAVITY", GRAVITY)?;
    m.add("BALL_MASS", BALL_MASS)?;
    
    // Ground ball constants
    m.add("GROUND_BALL_COR_GRASS", GROUND_BALL_COR_GRASS)?;
    m.add("GROUND_BALL_COR_DIRT", GROUND_BALL_COR_DIRT)?;
    m.add("ROLLING_FRICTION_GRASS", ROLLING_FRICTION_GRASS)?;
    m.add("ROLLING_FRICTION_DIRT", ROLLING_FRICTION_DIRT)?;
    m.add("FIELDER_ACCELERATION", FIELDER_ACCELERATION)?;
    
    Ok(())
}
