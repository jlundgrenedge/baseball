# Baseball Batted Ball Physics Simulator

A realistic physics-based simulator for baseball batted ball trajectories, incorporating empirically-validated aerodynamics and environmental factors.

## Features

- **Realistic Physics**: Implements drag forces, Magnus effect (spin-induced lift), and gravity
- **Environmental Factors**: Accounts for altitude, temperature, wind, and air density
- **Contact Quality**: Models sweet spot vs off-center hits
- **3D Trajectories**: Full three-dimensional flight path simulation
- **Empirically Validated**: Calibrated against real-world baseball data

## Installation

```bash
pip install -r requirements.txt
```

## Quick Start

```python
from batted_ball import BattedBallSimulator

# Create simulator
sim = BattedBallSimulator()

# Simulate a batted ball
result = sim.simulate(
    exit_velocity=100.0,    # mph
    launch_angle=28.0,      # degrees
    spray_angle=0.0,        # degrees (0 = center field)
    backspin_rpm=1800.0,    # rpm
    sidespin_rpm=0.0,       # rpm
    altitude=0.0,           # feet (sea level)
    temperature=70.0,       # Fahrenheit
    wind_speed=0.0,         # mph (+ = tailwind)
    wind_direction=0.0      # degrees
)

print(f"Distance: {result.distance:.1f} feet")
print(f"Flight time: {result.flight_time:.2f} seconds")
print(f"Peak height: {result.peak_height:.1f} feet")
```

## Physics Model

The simulator uses numerical integration (RK4 method) to solve the equations of motion:

- **Gravity**: 9.81 m/s² downward
- **Drag Force**: F_d = 0.5 × C_d × ρ × A × v²
- **Magnus Force**: F_l = 0.5 × C_l × ρ × A × v² (perpendicular to velocity)

### Validation Benchmarks

The model reproduces these empirical relationships:

- ~5 feet per 1 mph increase in exit velocity
- Optimal launch angle for home runs: 25-30°
- 100 mph at 28° with 1800 rpm backspin ≈ 390-400 feet (sea level)
- Coors Field (5,200 ft) adds ~30+ feet vs sea level
- Backspin 0→1500 rpm adds ~60 feet
- +10°F adds ~3-4 feet of carry

## Project Structure

```
batted_ball/
├── __init__.py          # Package initialization
├── constants.py         # Physical constants and baseball specs
├── environment.py       # Environmental factors (air density, etc.)
├── aerodynamics.py      # Drag and Magnus force calculations
├── integrator.py        # Numerical integration (RK4)
├── trajectory.py        # Main trajectory simulator
├── contact.py           # Contact point modeling
└── validation.py        # Empirical validation tests

examples/
├── basic_simulation.py  # Simple usage example
├── distance_analysis.py # Analyze factors affecting distance
└── validate_model.py    # Run validation benchmarks

tests/
└── test_physics.py      # Unit tests
```

## License

MIT License
