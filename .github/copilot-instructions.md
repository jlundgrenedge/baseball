# Baseball Physics Simulator - AI Developer Guide

## Project Overview
This is a comprehensive physics-based baseball simulation engine that models batted ball trajectories, pitch dynamics, and player interactions. The codebase evolved through 4 phases: spin-dependent aerodynamics → bat-ball collision → pitch simulation → player attributes and at-bat engine.

## Architecture & Core Components

### Physics Engine (`batted_ball/`)
- **Constants**: All empirical coefficients calibrated against MLB Statcast data in `constants.py` 
- **Aerodynamics**: Magnus force + spin-dependent drag calculations in `aerodynamics.py`
- **Integration**: RK4 numerical solver in `integrator.py` with configurable time steps
- **Environment**: Air density, temperature, altitude effects in `environment.py`

### Simulation Layers
1. **Trajectory** (`trajectory.py`): Core batted ball flight simulation
2. **Pitch** (`pitch.py`): 8 pitch types with realistic spin characteristics  
3. **Contact** (`contact.py`): Sweet spot physics and collision modeling
4. **At-Bat** (`at_bat.py`): Full plate appearance simulation with player attributes

### Key Design Patterns

**Physics Calibration**: All coefficients in `constants.py` are empirically derived from MLB data, not theoretical values. When modifying physics, always validate against the 7 benchmark tests in `validation.py`.

**Result Objects**: Every simulator returns structured result objects (`BattedBallResult`, `PitchResult`, `AtBatResult`) with calculated metrics, not raw trajectory data.

**Environment Context**: Environmental factors (altitude, temperature, wind) are passed to simulations, not global state.

## Development Workflows

### Validation-First Development
Always run validation after physics changes:
```python
from batted_ball.validation import ValidationSuite
suite = ValidationSuite()
results = suite.run_all_tests()
# Must achieve 7/7 passing tests
```

### Performance Testing
For bulk simulations (1000+ at-bats), use fast mode:
```python
sim = AtBatSimulator(pitcher, hitter, fast_mode=True)  # 2x faster
python test_performance.py  # Benchmark performance changes
```

### Batch File Runners
- `run_simulation.bat`: Interactive batted ball simulator
- `pitch_scenarios.bat`: Pitch type demonstrations
- `complete_atbat.bat`: Full at-bat simulations
- Use these for manual testing and demonstrations

## Critical Implementation Details

### Spin-Dependent Drag (Phase 1 Achievement)
The model correctly implements empirical observation that spinning balls experience increased drag:
- Pure backspin: minimal drag penalty
- Sidespin + backspin: asymmetric drag reduces distance ~13ft
- Implementation in `aerodynamics.py._calculate_spin_adjusted_drag_coefficient()`

### Time Step Strategy
- Default: `DT_DEFAULT = 0.001s` (1ms) for accuracy
- Fast mode: `DT_FAST = 0.002s` (2ms) for 2x speedup with <1% accuracy loss
- Choose based on use case: single simulations vs bulk analysis

### Player Attribute System
Player ratings (0-100 scale) directly map to physics parameters:
- Pitcher velocity rating → actual mph ranges per pitch type
- Hitter bat speed → exit velocity potential  
- Command rating → location accuracy (standard deviation)

## Testing & Validation

### Empirical Benchmarks
The model reproduces these MLB relationships (all tests must pass):
- ~5 ft per 1 mph exit velocity increase
- Optimal launch angle: 25-30° for distance
- Backspin 0→1500 rpm adds ~50-60 feet
- Coors Field (5,200 ft) adds ~30 feet vs sea level

### Unit Tests
- `tests/test_physics.py`: Core physics validation
- `examples/validate_*.py`: Integration testing
- Run after any physics modifications

## Integration Points

### External Dependencies
Minimal external dependencies by design:
- `numpy`: Core mathematical operations
- `numba` (optional): JIT compilation for performance
- No game engine or UI dependencies

### Data Flow
1. **Input**: Player attributes + environmental conditions
2. **Physics**: Convert attributes to physical parameters
3. **Simulation**: Numerical integration of motion equations  
4. **Output**: Structured results with calculated metrics

## Common Gotchas

### Unit Conversions
All internal calculations use SI units (m, m/s, kg), but user interface uses baseball units (ft, mph). Conversion constants in `constants.py` handle this automatically.

### Coordinate System
- X: toward center field (positive)
- Y: toward pull side (positive for RHB)  
- Z: upward (positive)
- Home plate at origin (0,0,0)

### Spin Axis Convention
Spin vectors point along axis of rotation (right-hand rule). Backspin = positive Y-axis for typical contact.

## File Organization Logic

- **Core physics**: `batted_ball/*.py` (importable package)
- **Examples**: `examples/*.py` (usage demonstrations)
- **Validation**: Test files that verify empirical accuracy
- **Research**: Documentation and development notes
- **Batch scripts**: Windows command-line interfaces

When adding new features, follow the phase pattern: implement physics → validate empirically → integrate with existing systems → optimize performance.