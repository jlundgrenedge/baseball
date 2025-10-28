# Baseball Physics Simulator - AI Developer Guide

## Project Overview
Complete physics-based baseball game simulator evolved through 5 phases: aerodynamics → collision → pitching → attributes → fielding/baserunning. Simulates full 9-inning games from pitch to outcome using empirically-calibrated physics.

## Architecture: Layered Simulation Stack

### Layer 1: Physics Engine (Core)
- **constants.py**: All coefficients from MLB Statcast data (not theoretical values)
- **aerodynamics.py**: Magnus force + spin-dependent drag (key: asymmetric drag for sidespin)
- **integrator.py**: RK4 solver, DT=0.001s (accurate) or 0.002s (fast mode)
- **environment.py**: Air density effects from altitude/temperature

### Layer 2: Ball Flight
- **trajectory.py**: `BattedBallSimulator` returns `BattedBallResult` with position arrays
- **pitch.py**: 8 pitch types (`create_fastball_4seam()`, `create_curveball()`, etc.)
- **contact.py**: Sweet spot collision model (off-center = velocity loss + bad spin)

### Layer 3: Game Actions
- **at_bat.py**: `AtBatSimulator` runs pitch-by-pitch PA, returns `AtBatResult`
- **fielding.py**: `Fielder` physics (sprint speed 23-32 ft/s, reaction time 0-0.5s)
- **baserunning.py**: `BaseRunner` timing (home-to-first 3.7-5.2s validated)

### Layer 4: Complete Plays
- **play_simulation.py**: `PlaySimulator` coordinates trajectory → fielding → baserunning
- **game_simulation.py**: `GameSimulator` runs full 9-inning games with teams

### Attribute System (attributes.py)
**Critical**: Uses 0-100,000 scale with piecewise logistic mapping:
- `piecewise_logistic_map()`: Ratings → physical units (velocity, speed, etc.)
- Below 85k: Normal human range (smooth sigmoid spread)
- Above 85k: Superhuman headroom (gentler scaling)
- Example: `HitterAttributes.get_bat_speed_mph()` → 50-120 mph range

## Development Workflows

### Physics Changes (Validation Required)
```python
# After ANY physics modification:
from batted_ball.validation import ValidationSuite
suite = ValidationSuite()
results = suite.run_all_tests()  # MUST pass 7/7 tests
# Tests: exit velocity effect, launch angle, altitude, backspin, temperature
```

### Performance Modes
```python
# Standard: DT_DEFAULT=0.001s (accurate)
sim = AtBatSimulator(pitcher, hitter)

# Fast: DT_FAST=0.002s (2x speedup, <1% accuracy loss)
sim = AtBatSimulator(pitcher, hitter, fast_mode=True)

# UltraFast: 10x speedup, <2% accuracy loss
from batted_ball.performance import UltraFastMode
with UltraFastMode():
    # Bulk simulation code
```

### Testing Commands
```bash
python -m batted_ball.validation          # Run 7 benchmark tests
python test_performance.py                # Benchmark simulation speed
python examples/game_simulation_demo.py   # Full game demo
python examples/validate_model.py         # Integration tests
```

## Critical Implementation Details

### Coordinate System (NEVER VIOLATE)
**Origin**: Home plate (0,0,0)
- **X**: Right field (+), Left field (-)
- **Y**: Center field (+), Home plate (-)
- **Z**: Upward (+), Downward (-)
- **ALL modules** (trajectory, fielding, baserunning) must maintain this alignment

### Unit Conversion (Automatic)
- **Internal**: SI units (m, m/s, kg) for physics
- **External**: Baseball units (ft, mph, degrees) for users
- **Conversions**: `MPH_TO_MS`, `FEET_TO_METERS` in constants.py (handled automatically)
- **Never mix**: Functions take baseball units, convert internally, return baseball units

### Spin Convention (Right-Hand Rule)
- Spin vectors point along rotation axis
- **Backspin**: Positive Y-axis (+topspin on screen)
- **Sidespin**: Positive X-axis = tail away from RHH
- **Gyro spin**: Positive Z-axis (bullet spin)

### Attribute Mapping Pattern
```python
# Legacy (0-100 scale, still supported):
pitcher = Pitcher(name="Ace", velocity=85, command=75)

# New (0-100,000 physics-first scale, preferred):
from batted_ball.attributes import create_starter_pitcher
attributes = create_starter_pitcher(quality="good")
pitcher = Pitcher(name="Ace", attributes_v2=attributes)

# Access physical values:
mph = pitcher.attributes_v2.get_raw_velocity_mph()  # Direct physical value
```

### Result Object Pattern
Every simulator returns structured objects with calculated metrics:
- `BattedBallResult`: distance, flight_time, peak_height, landing_x/y, position array
- `PitchResult`: final_location, velocity_plate, movement, trajectory
- `AtBatResult`: outcome (strikeout/walk/in_play), pitches list, batted_ball_result
- `PlayResult`: outcome (single/double/out), runs_scored, outs_made, events timeline
- **Never return raw arrays** - always wrap in result objects

### Environmental Context (Not Global State)
```python
# Create environment first:
env = create_standard_environment()  # Sea level, 70°F
# OR
env = create_coors_field_environment()  # 5,200 ft altitude

# Pass to simulator:
sim = BattedBallSimulator(env)  # Not global config
```

## Common Patterns & Conventions

### Factory Functions (Preferred Creation)
```python
# Pitches: create_fastball_4seam(), create_curveball(), create_slider()
# Players: create_test_team(), create_power_hitter(), create_starter_pitcher()
# Fielders: create_elite_fielder(), create_average_fielder()
# Runners: create_speed_runner(), create_smart_runner()
# Defense: create_standard_defense(), create_elite_defense()
# Environment: create_standard_environment(), create_coors_field_environment()
```

### Validation-First Development
1. Identify which benchmark test your change affects
2. Make physics change
3. Run `ValidationSuite().run_all_tests()`
4. If test fails, adjust coefficients in constants.py
5. Iterate until 7/7 pass (don't compromise accuracy)

### Performance Profiling
```python
# For bulk operations (1000+ at-bats):
from batted_ball.bulk_simulation import BulkAtBatSimulator
sim = BulkAtBatSimulator(pitcher, hitter)
results = sim.simulate_bulk(num_at_bats=10000, fast_mode=True)
```

## Integration Gotchas

### Trajectory Arrays vs Landing Position
```python
# trajectory.position is Nx3 numpy array (entire flight path in meters)
# trajectory.landing_x/landing_y is final position (feet)
# For fielding: use landing_x/landing_y, NOT position[-1]
```

### Time Steps and Accuracy
- **Never change DT_DEFAULT** without revalidating all 7 tests
- Fast mode acceptable for bulk sims, not single high-stakes plays
- Ground balls: physics timesteps are different (use ground_ball_physics.py)

### Fielder/Runner Movement Physics
```python
# Fielders: calculate_effective_time_to_position() includes:
#   - First step time (reaction)
#   - Acceleration phase
#   - Sprint phase
#   - Route efficiency penalty
# Runners: calculate_time_to_base() includes:
#   - Reaction time
#   - Leadoff advantage
#   - Turn speed loss (if rounding bases)
```

### Force Plays & Double Plays
```python
# Use baserunning module functions:
from batted_ball.baserunning import detect_force_situation, get_force_base
forces = detect_force_situation(runners, batter_running=True)
# Returns: {"first": True, "second": True} for runners forced to advance
```

## File Organization

```
batted_ball/          # Core package (importable)
  ├── constants.py    # All empirical coefficients
  ├── aerodynamics.py # Magnus + drag physics
  ├── trajectory.py   # Ball flight
  ├── at_bat.py       # Plate appearances
  ├── fielding.py     # Defensive mechanics
  ├── game_simulation.py  # Full games
  └── validation.py   # 7 benchmark tests
examples/             # Usage demonstrations
  ├── game_simulation_demo.py
  ├── validate_model.py
  └── basic_simulation.py
docs/                 # Phase summaries
research/             # Physics references
tests/                # Unit tests
```

## When Adding Features

**Phase Pattern**: Implement physics → validate empirically → integrate → optimize

1. **Physics layer**: Add to appropriate module (trajectory/fielding/etc.)
2. **Constants**: Add empirical coefficients to constants.py with MLB data source
3. **Validation**: Create benchmark test or extend existing
4. **Integration**: Add to higher-level simulators (at_bat/play/game)
5. **Factory functions**: Add convenience creation functions
6. **Documentation**: Update relevant phase summary in docs/
7. **Performance**: Profile and optimize if needed (performance.py)

## Examples to Learn From

- **Complete workflow**: `examples/game_simulation_demo.py`
- **Physics validation**: `batted_ball/validation.py`
- **Attribute mapping**: `batted_ball/attributes.py` (piecewise_logistic_map)
- **Play resolution**: `batted_ball/play_simulation.py` (PlaySimulator class)
- **Performance optimization**: `batted_ball/performance.py` (UltraFastMode)
