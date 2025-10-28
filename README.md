# Baseball Physics Simulation Engine

A comprehensive physics-based baseball simulation engine that models complete games from pitch to play outcome. This system evolved through 5 development phases to create a fully integrated simulation with empirically-validated physics at every layer.

## Overview

This is a **complete baseball game simulator** built on rigorous physics principles. Unlike arcade-style games or statistical simulations, this engine models the actual physical interactions of every element: spinning baseballs in flight, bat-ball collisions, fielder movement, and baserunning dynamics.

**Current Capabilities:**
- Full 9-inning game simulation with realistic play-by-play
- 8 pitch types with spin-dependent aerodynamics  
- Bat-ball contact physics with sweet spot modeling
- Complete defensive plays including fielding and baserunning
- Player attribute system (0-100 ratings) mapped to physical parameters
- Environmental effects (altitude, temperature, wind)
- Force plays, double plays, and complex baserunning scenarios

## Installation

```bash
pip install -r requirements.txt
```

**Requirements**: Python 3.8+, NumPy, (optional: numba for JIT optimization)

## Quick Start Examples

### Simulate a Complete Game

```python
from batted_ball.game_simulation import GameSimulator, create_test_team

# Create two teams
home_team = create_test_team("Home Team", quality="good")
away_team = create_test_team("Away Team", quality="average")

# Simulate 9-inning game
sim = GameSimulator(away_team, home_team, verbose=True)
final_state = sim.simulate_game(num_innings=9)

print(f"Final Score: {final_state.away_score} - {final_state.home_score}")
```

### Simulate a Single At-Bat

```python
from batted_ball import AtBatSimulator, Pitcher, Hitter

# Create players with attributes
pitcher = Pitcher("Ace", velocity=85, command=75, stamina=80)
hitter = Hitter("Slugger", contact=70, power=85, discipline=60)

# Simulate plate appearance
sim = AtBatSimulator(pitcher, hitter)
result = sim.simulate_at_bat()

print(f"Outcome: {result.outcome}")
print(f"Pitches thrown: {len(result.pitches)}")
```

### Analyze Batted Ball Physics

```python
from batted_ball import BattedBallSimulator

sim = BattedBallSimulator()
result = sim.simulate(
    exit_velocity=100.0,    # mph
    launch_angle=28.0,      # degrees
    spray_angle=0.0,        # degrees (0 = center field)
    backspin_rpm=1800.0,    # rpm
    sidespin_rpm=0.0,       # rpm
    altitude=0.0,           # feet (sea level)
    temperature=70.0        # Fahrenheit
)

print(f"Distance: {result.distance:.1f} feet")
print(f"Flight time: {result.flight_time:.2f} seconds")
print(f"Peak height: {result.peak_height:.1f} feet")
```

## Development Phases

### Phase 1: Spin-Dependent Aerodynamics (COMPLETE)
**Files**: `aerodynamics.py`, `trajectory.py`, `integrator.py`

Implemented Magnus force and spin-dependent drag using empirical coefficients calibrated against MLB Statcast data. Key achievement: correctly models how spinning balls experience increased drag, particularly for balls with combined sidespin and backspin.

**Validation**: 7/7 benchmark tests pass
- Exit velocity effect: ~5 ft per 1 mph
- Optimal launch angle: 25-30°
- Altitude effect: Coors Field adds ~30 ft
- Backspin effect: 1500 rpm adds ~50-60 ft

### Phase 2: Bat-Ball Collision Physics (COMPLETE)
**Files**: `contact.py`

Models realistic contact quality based on impact location relative to bat's sweet spot. Off-center hits reduce exit velocity and add unwanted spin, creating popup/groundball outcomes that match real baseball distributions.

### Phase 3: Pitch Trajectory Simulation (COMPLETE)
**Files**: `pitch.py`

Eight pitch types with realistic spin characteristics:
- 4-seam/2-seam fastballs
- Cutter, slider, curveball
- Changeup, splitter, knuckleball

Each pitch uses position-dependent spin (orientation changes during flight) for accurate movement patterns.

### Phase 4: Player Attributes & At-Bat Engine (COMPLETE)
**Files**: `player.py`, `at_bat.py`, `attributes.py`

Player ratings (0-100 scale) map directly to physics parameters:
- Pitcher: velocity → mph, command → location accuracy (std dev), repertoire → pitch mix
- Hitter: bat speed → exit velocity, contact → sweet spot %, discipline → swing decisions
- Complete pitch-by-pitch at-bat simulation with count management and swing decisions

### Phase 5: Fielding & Baserunning (COMPLETE)
**Files**: `fielding.py`, `baserunning.py`, `field_layout.py`, `play_simulation.py`, `game_simulation.py`

**Fielding Physics:**
- Sprint speeds: 23-32 ft/s (calibrated to MLB Statcast)
- Reaction times: 0-0.5 seconds based on skill
- Throwing velocities: 70-105 mph position-dependent
- Catch probability model using timing comparisons

**Baserunning Physics:**
- Home-to-first times: 3.7-5.2 seconds (validated against MLB)
- Turn efficiency: 75-92% speed retention
- Sliding mechanics with friction-based deceleration
- Force play detection and double play physics

**Complete Play Simulation:**
- Ball-in-play → fielder interception → throw physics → runner timing
- Realistic outcomes: singles, doubles, triples, home runs, outs
- Force plays, double plays, fielder's choice
- Smart baserunning decisions based on situation

## Architecture

### Core Physics Engine
```
batted_ball/
├── constants.py          # Empirical coefficients (ALL calibrated to MLB data)
├── aerodynamics.py       # Drag + Magnus force calculations
├── integrator.py         # RK4 numerical solver (DT=0.001s default)
├── environment.py        # Air density, temperature, altitude effects
└── trajectory.py         # Batted ball flight simulation
```

### Simulation Layers
```
batted_ball/
├── pitch.py              # 8 pitch types with spin characteristics
├── contact.py            # Sweet spot physics, contact quality
├── at_bat.py            # Plate appearance simulation
├── fielding.py          # Fielder movement, catching, throwing
├── baserunning.py       # Runner movement, turns, sliding
├── play_simulation.py   # Complete play resolution
└── game_simulation.py   # Full 9-inning games
```

### Player & Team Management
```
batted_ball/
├── player.py            # Pitcher/Hitter definitions
├── attributes.py        # Attribute → physics mapping
└── field_layout.py      # Field dimensions, positions
```

### Performance & Validation
```
batted_ball/
├── validation.py        # 7 empirical benchmark tests
├── performance.py       # UltraFastMode (10x speedup)
└── bulk_simulation.py   # Efficient bulk at-bat processing
```

## Key Design Principles

### 1. Physics-First Approach
All gameplay mechanics emerge from physical parameters, not arbitrary rules:
- Contact quality determines exit velocity/launch angle (not rolled dice)
- Fielder attributes control movement speed/reaction (not success probabilities)
- Environmental factors affect aerodynamics realistically

### 2. Empirical Calibration
Every coefficient in `constants.py` is derived from MLB data:
- Drag coefficients fit to Statcast trajectories
- Player attribute ranges match scouting scales
- Timing tolerances calibrated to video analysis

### 3. Validation-Driven Development
Changes to physics require passing validation suite:
```python
from batted_ball.validation import ValidationSuite
suite = ValidationSuite()
results = suite.run_all_tests()  # Must achieve 7/7 passing
```

### 4. Coordinate System Consistency
**Critical**: All modules use identical coordinate system
- Origin: Home plate (0, 0, 0)
- X: toward right field (+) / left field (-)
- Y: toward center field (+) / toward home plate (-)
- Z: upward (+) / downward (-)

This consistency is maintained across trajectory, fielding, and baserunning modules.

## Performance Optimization

### Standard Mode
- Time step: 0.001s (1ms) for maximum accuracy
- Typical at-bat: ~50-200ms
- Full game (200+ at-bats): ~30-60 seconds

### Fast Mode
```python
sim = AtBatSimulator(pitcher, hitter, fast_mode=True)  # 2x faster
```
- Time step: 0.002s (2ms)
- Accuracy loss: <1%
- Recommended for bulk simulations (1000+ at-bats)

### UltraFast Mode
```python
from batted_ball.performance import UltraFastMode
with UltraFastMode():
    # Your simulation code here
    pass  # 10x speedup, <2% accuracy loss
```

## Validation & Benchmarks

The model reproduces these empirical MLB relationships:

| Test | Expected | Actual | Status |
|------|----------|--------|--------|
| Exit velocity effect | ~5 ft per 1 mph | 4.8-5.2 ft | ✓ PASS |
| Optimal launch angle | 25-30° | 28° | ✓ PASS |
| Benchmark distance | 390-400 ft | 395 ft | ✓ PASS |
| Coors Field effect | +30 ft | +31 ft | ✓ PASS |
| Backspin effect | +50-60 ft | +54 ft | ✓ PASS |
| Temperature effect | +3-4 ft per 10°F | +3.5 ft | ✓ PASS |
| Sidespin reduction | -13 ft | -12 ft | ✓ PASS |

Run validation: `python -m batted_ball.validation`

## Common Usage Patterns

### Batch Simulation
```python
from batted_ball import BulkAtBatSimulator, BulkSimulationSettings

settings = BulkSimulationSettings(
    num_at_bats=10000,
    fast_mode=True,
    track_detailed_stats=True
)

results = BulkAtBatSimulator(pitcher, hitter).simulate_bulk(settings)
print(f"Batting average: {results.batting_average:.3f}")
```

### Environmental Comparison
```python
from batted_ball import create_standard_environment, create_coors_field_environment

# Sea level
env_sea = create_standard_environment()
sim_sea = BattedBallSimulator(env_sea)
dist_sea = sim_sea.simulate(100, 28, 0, 1800, 0).distance

# Coors Field (5,200 ft altitude)
env_coors = create_coors_field_environment()
sim_coors = BattedBallSimulator(env_coors)
dist_coors = sim_coors.simulate(100, 28, 0, 1800, 0).distance

print(f"Coors boost: +{dist_coors - dist_sea:.1f} feet")
```

### Complete Play Scenarios
```python
from batted_ball.play_simulation import simulate_play_from_trajectory
from batted_ball import create_standard_defense, create_average_runner

# Simulate ball in play
trajectory_result = sim.simulate(95, 15, 0, 2200, 0)

# Set up defense
defense = create_standard_defense()
batter_runner = create_average_runner("Batter")

# Simulate complete defensive play
play_result = simulate_play_from_trajectory(
    trajectory_result, defense, batter_runner
)
print(f"Play outcome: {play_result.outcome}")
```

## Coordinate System & Units

**Internal (Physics)**: SI units (meters, m/s, kg)  
**External (User)**: Baseball units (feet, mph, degrees)  
**Conversions**: Handled automatically in `constants.py`

**Field Coordinates**:
- Home plate: (0, 0, 0)
- First base: (63.64, 63.64, 0)
- Second base: (0, 127.28, 0)  
- Third base: (-63.64, 63.64, 0)
- Center field: (0, 400, 0)

## File Organization

- **Core physics**: `batted_ball/*.py` (importable package)
- **Examples**: `examples/*.py` (usage demonstrations)
- **Validation**: Test files verifying empirical accuracy
- **Documentation**: `docs/*.md` (phase summaries, research notes)
- **Research**: `research/*.md` (physics modeling references)

## Critical Implementation Notes

### Spin-Dependent Drag (Phase 1 Key Achievement)
The model correctly implements the empirical observation that spinning balls experience increased drag:
- Pure backspin: minimal drag penalty
- Sidespin + backspin: asymmetric drag reduces distance ~13 ft
- Implementation: `aerodynamics._calculate_spin_adjusted_drag_coefficient()`

### Time Step Strategy
- Default: `DT_DEFAULT = 0.001s` (1ms) for accuracy
- Fast mode: `DT_FAST = 0.002s` (2ms) for 2x speedup
- Choose based on use case: single simulations vs bulk analysis

### Contact Quality Gates (Phase 2)
Contact quality determines possible outcomes:
- **Weak contact** (< 80 mph): singles only
- **Fair contact** (80-95 mph): singles, doubles, rare triples
- **Solid contact** (95+ mph): full range including home runs

### Player Attribute System (Phase 4)
Ratings (0-100) map to physical parameters:
- Pitcher velocity rating → actual mph ranges per pitch type
- Hitter bat speed → exit velocity potential
- Command rating → location accuracy (standard deviation)
- All mappings use sigmoid/linear interpolation for smooth scaling

## Development Workflow

### Making Physics Changes
1. Modify coefficients in `constants.py` or physics in relevant module
2. Run validation: `python -m batted_ball.validation`
3. Verify 7/7 tests still pass
4. Benchmark performance if needed: `python test_performance.py`

### Adding New Features
1. Maintain coordinate system consistency
2. Add validation tests for new physics
3. Update documentation
4. Follow existing attribute → physics mapping patterns

### Testing
```bash
# Run validation suite
python -m batted_ball.validation

# Run unit tests
pytest tests/

# Performance benchmarking
python test_performance.py

# Quick game test
python test_quick_game.py
```

## Batch File Runners

**Windows users**: Convenient batch file for interactive game simulation
```bash
game_simulation.bat
```
Provides detailed physics output and play-by-play commentary.

## Known Limitations & Future Work

### Current Limitations
1. No pitcher fatigue modeling (stamina tracked but not applied)
2. Simplified umpire calls (no error modeling on close plays)
3. Basic defensive positioning (no shifts or count-based adjustments)
4. No weather effects on fielding (wind on throws not modeled)

### Planned Enhancements
1. **Detailed defensive strategy**: Shifts, positioning by count/batter
2. **Pitcher fatigue**: Velocity/command degradation over innings
3. **Umpire modeling**: Realistic strike zone variation
4. **Advanced baserunning**: Steal attempts, pickoffs, leads
5. **Injury simulation**: Performance impact modeling

## Research References

See `research/` directory for detailed physics documentation:
- `Modeling Baseball Batted Ball Trajectories for Realistic Simulation.md`
- `Bat Ball Physics Collision Physics.md`
- `Modeling Baseball Pitching Dynamics.md`
- `Baseball Simulation Fielding Improvements.md`

## License

MIT License

## Citation

If you use this simulator in research, please cite:
```
Baseball Physics Simulation Engine (2024)
https://github.com/jlundgrenedge/baseball
```

## Support

For issues, questions, or contributions, see the repository issues page.
