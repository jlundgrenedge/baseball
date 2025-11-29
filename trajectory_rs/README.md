# trajectory_rs

High-performance RK4 trajectory integration for baseball simulation, implemented in Rust with PyO3 bindings.

## Features

- **RK4 Integration**: 4th-order Runge-Kutta method for accurate trajectory calculation
- **Parallel Batch Processing**: Uses Rayon for multi-threaded trajectory batches
- **Lookup Tables**: Bilinear interpolation for aerodynamic coefficients
- **Memory Efficient**: Endpoint-only mode for when full trajectories aren't needed

## Performance Target

2-3x speedup over Numba for batch trajectory operations.

## Building

```bash
# From the trajectory_rs directory
cd trajectory_rs

# Build and install in development mode
maturin develop --release

# Or build a wheel
maturin build --release
```

## Usage

```python
import numpy as np
import trajectory_rs

# Single trajectory
initial_state = np.array([0.0, 0.0, 1.0, 40.0, 0.0, 20.0])  # x,y,z,vx,vy,vz
spin_axis = np.array([0.0, 1.0, 0.0])  # backspin
positions, velocities, times = trajectory_rs.integrate_trajectory(
    initial_state, dt=0.005, max_time=10.0, ground_level=0.0,
    spin_axis=spin_axis, spin_rpm=2000.0,
    air_density=1.225, cross_area=0.0042,
    cd_table=cd_table, cl_table=cl_table
)

# Batch processing (parallel)
initial_states = np.zeros((100, 6))  # 100 trajectories
spin_params = np.zeros((100, 4))     # spin_x, spin_y, spin_z, spin_rpm
landing_pos, landing_times, distances, apex_heights = trajectory_rs.integrate_trajectories_batch(
    initial_states, dt=0.005, max_time=10.0, ground_level=0.0,
    spin_params=spin_params,
    air_density=1.225, cross_area=0.0042,
    cd_table=cd_table, cl_table=cl_table
)

# Check/set thread count
print(f"Using {trajectory_rs.get_num_threads()} threads")
trajectory_rs.set_num_threads(8)
```

## Development

```bash
# Install maturin
pip install maturin

# Build in debug mode (faster compile)
maturin develop

# Run tests
cargo test
```

## License

MIT
