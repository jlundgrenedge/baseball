# Baseball Physics Simulator - AI Developer Guide

## Project Overview
Complete physics-based baseball game simulator evolved through 5 phases: aerodynamics → collision → pitching → attributes → fielding/baserunning. Simulates full 9-inning games from pitch to outcome using empirically-calibrated physics.

**⚠️ CRITICAL**: This is a **physics-first** simulator. All gameplay emerges from physical parameters (exit velocity, sprint speed, throw times), NOT statistical probabilities or dice rolls. Changes must preserve empirical validation against MLB data.

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
python test_full_game.py                  # Quick 9-inning game test
python test_quick_game.py                 # 3-inning game test
```

### Debugging Workflow
```bash
# For detailed play-by-play analysis, check enhanced_game_log.txt
# Shows timing breakdowns, margin analysis, fielder decisions
# Example: "Runner margins (positive = runner beats ball) - 1st: +1.28s, 2nd: -2.73s"

# Common debugging patterns:
python test_full_game.py > game_output.txt  # Capture game stats
# Check: Runs/9 (expect ~9.0), BABIP (expect ~.300), Hits/9 (expect ~17.0)
```

## Critical Implementation Details

### Coordinate System (NEVER VIOLATE)
**Origin**: Home plate (0,0,0)
- **X**: Right field (+), Left field (-)
- **Y**: Center field (+), Home plate (-)
- **Z**: Upward (+), Downward (-)
- **ALL modules** (trajectory, fielding, baserunning) must maintain this alignment

**CRITICAL BUG PATTERN**: Trajectory physics uses different internal coords (x=outfield, y=lateral). Positions ARE converted correctly in `trajectory.py`, but velocities MUST also be converted:
```python
# When passing velocities from trajectory to ground ball/fielding:
from batted_ball.trajectory import convert_velocity_trajectory_to_field
vx_field, vy_field, vz_field = convert_velocity_trajectory_to_field(
    vx_traj, vy_traj, vz_traj
)
# Never use trajectory velocities directly with field positions!
```
See `COORDINATE_SYSTEM_FIX_REPORT.md` for historical bug details.

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

### API Reference (Use This to Avoid Import Errors!)

**Common Import Mistakes** - Always verify imports before writing test code:

```python
# CORRECT imports for common functionality:
from batted_ball.game_simulation import create_test_team, GameSimulator, Team
from batted_ball.player import Pitcher, Hitter
from batted_ball.at_bat import AtBatSimulator
from batted_ball.play_simulation import PlaySimulator, create_standard_defense
from batted_ball.baserunning import BaseRunner
from batted_ball.environment import create_standard_environment
from batted_ball.trajectory import BattedBallSimulator

# WRONG - these don't exist in these modules:
# from batted_ball.player import create_test_team  # ❌ Wrong module
# from batted_ball.fielding import create_standard_defense  # ❌ Wrong module
```

**Class Method Names** - Common errors:

```python
# AtBatSimulator
result = simulator.simulate_at_bat()  # ✓ CORRECT
result = simulator.simulate()  # ❌ WRONG - no such method

# PlaySimulator  
result = play_sim.simulate_complete_play(batted_ball, runner, outs)  # ✓ CORRECT
result = play_sim.simulate_play(at_bat_result, outs)  # ❌ WRONG - wrong signature

# Team object attributes
pitchers = team.pitchers  # ✓ CORRECT - list of pitchers
pitcher = team.pitcher  # ❌ WRONG - no such attribute
hitters = team.hitters  # ✓ CORRECT - list of hitters
```

**Result Object Patterns** - Enums vs Strings:

```python
# AtBatResult.outcome is a STRING, not an Enum:
if at_bat_result.outcome == "in_play":  # ✓ CORRECT
if at_bat_result.outcome.value == "in_play":  # ❌ WRONG - no .value attribute

# PlayOutcome IS an Enum:
if play_result.outcome == PlayOutcome.SINGLE:  # ✓ CORRECT
if play_result.outcome.value == "single":  # ✓ ALSO CORRECT
```

### Factory Functions (Preferred Creation)
```python
# Teams & Players (from game_simulation):
team = create_test_team("Team Name", quality="good")  # Returns Team object
# Team has: .pitchers (list), .hitters (list), .name

# Defense (from play_simulation):
defense = create_standard_defense()  # Returns Dict[str, Fielder]

# Environment (from environment):
env = create_standard_environment()  # Sea level, 70°F
env = create_coors_field_environment()  # 5,200 ft altitude

# Pitches (from pitch):
pitch = create_fastball_4seam(velocity, spin_rpm, position)
pitch = create_curveball(velocity, spin_rpm, position)
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

### Test Script Template (Copy This to Avoid Import Errors)
```python
"""
Test script template - copy and modify for new tests
"""
# CORRECT imports - verified working:
from batted_ball.game_simulation import create_test_team
from batted_ball.player import Pitcher, Hitter
from batted_ball.at_bat import AtBatSimulator
from batted_ball.play_simulation import PlaySimulator, create_standard_defense
from batted_ball.baserunning import BaseRunner
from batted_ball.environment import create_standard_environment
from batted_ball.trajectory import BattedBallSimulator

def test_something():
    # Create teams
    home_team = create_test_team("Home", quality="good")
    away_team = create_test_team("Away", quality="average")
    
    # Access team attributes CORRECTLY:
    pitcher = away_team.pitchers[0]  # Note: .pitchers (plural), indexed
    hitter = home_team.hitters[0]    # Note: .hitters (plural), indexed
    
    # Run at-bat simulation:
    at_bat_sim = AtBatSimulator(pitcher, hitter)
    at_bat_result = at_bat_sim.simulate_at_bat()  # Note: simulate_at_bat(), not simulate()
    
    # Check outcome (STRING, not Enum):
    if at_bat_result.outcome == "in_play":  # Note: direct string comparison, no .value
        print("Ball in play!")
    
    # If simulating complete play:
    if at_bat_result.batted_ball_result:
        env = create_standard_environment()
        defense = create_standard_defense()
        play_sim = PlaySimulator()
        play_sim.setup_defense(defense)
        
        # Add batter as runner:
        batter_runner = BaseRunner(name="Batter", sprint_speed=60.0)
        
        # Simulate complete play:
        play_result = play_sim.simulate_complete_play(
            at_bat_result.batted_ball_result,
            batter_runner,
            current_outs=0
        )
        
        # Check play outcome (ENUM):
        from batted_ball.play_simulation import PlayOutcome
        if play_result.outcome == PlayOutcome.SINGLE:
            print("Single!")
        # OR use .value for string:
        if play_result.outcome.value == "single":
            print("Single!")

if __name__ == "__main__":
    test_something()
```

## Integration Gotchas

### Baserunning Margin Calculations (CRITICAL)
**Common Bug**: Calculating margins from HOME for all runners instead of their CURRENT base.
```python
# WRONG - calculates as if runner starts from home:
time_to_second = runner.calculate_time_to_base("home", "second")
margin = ball_arrival_at_second - time_to_second  # -4.5s margin!

# CORRECT - for runner on first:
time_to_second = runner.calculate_time_to_base("first", "second")
margin = ball_arrival_at_second - time_to_second  # +0.6s margin!
```
**Fix Pattern**: Use `decide_runner_advancement()` function which handles this correctly for each runner's position. See recent fix in `play_simulation.py` lines 1423-1600.

### Runner Position Tracking
```python
# CRITICAL ORDER: Get existing runners BEFORE placing batter
existing_runners = []
for base in ["first", "second", "third"]:
    runner = self.baserunning_simulator.get_runner_at_base(base)
    if runner:
        existing_runners.append((base, runner))

# Then move batter
batter_runner.current_base = target_base
self.baserunning_simulator.add_runner(target_base, batter_runner)

# Finally populate final_runner_positions for game state
result.final_runner_positions[base] = runner
```
Violating this order causes batter to overwrite existing runners → 0 runs scored bug.

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

# When handling force/double plays, preserve uninvolved runners:
# 1. Get existing runners before processing outs
# 2. Remove only the out runners
# 3. Keep remaining runners in final_runner_positions
```

## Recent Bug Patterns & Fixes

### Quick Troubleshooting Guide

**Import Errors:**
- `cannot import name 'create_test_team' from 'batted_ball.player'`
  - → Use `from batted_ball.game_simulation import create_test_team`
- `cannot import name 'create_standard_defense' from 'batted_ball.fielding'`
  - → Use `from batted_ball.play_simulation import create_standard_defense`

**Attribute Errors:**
- `'Team' object has no attribute 'pitcher'`
  - → Use `team.pitchers[0]` (plural, indexed)
- `'AtBatSimulator' object has no attribute 'simulate'`
  - → Use `simulator.simulate_at_bat()` (full method name)
- `'PlaySimulator' object has no attribute 'simulate_play'`
  - → Use `play_sim.simulate_complete_play(batted_ball, runner, outs)`
- `'str' object has no attribute 'value'`
  - → AtBatResult.outcome is a STRING, use direct comparison: `outcome == "in_play"`
  - → PlayResult.outcome IS an Enum, can use `.value` or direct comparison with Enum

**When Writing Tests:**
1. Copy the test script template from the "Test Script Template" section
2. Verify imports match the "API Reference" section
3. Use `.pitchers[0]` and `.hitters[0]` to access team players
4. Use `simulate_at_bat()` for at-bats (not `simulate()`)
5. Check if result attributes are strings or Enums before accessing `.value`

### 1. Baserunning Margins (Fixed 2024)
**Symptom**: 20 hits but only 2-1 score. Runners not advancing on base hits.  
**Root Cause**: Margin calculation used batter time from home for ALL runners.  
**Fix**: Use `decide_runner_advancement()` per runner with correct starting base.  
**Location**: `play_simulation.py` _handle_ball_in_play() lines 1423-1600

### 2. Coordinate System Velocity Bug (Fixed 2024)
**Symptom**: Fielders running wrong direction, traveling 300+ ft on grounders.  
**Root Cause**: Landing velocities not converted from trajectory coords to field coords.  
**Fix**: Added `convert_velocity_trajectory_to_field()` helper, applied in ground_ball modules.  
**Location**: `trajectory.py`, `ground_ball_interception.py`, `ground_ball_physics.py`

### 3. Runner Placement Order Bug (Fixed 2024)
**Symptom**: 26 hits in game but 0 runs scored.  
**Root Cause**: Batter placement overwrote existing runners in final_runner_positions.  
**Fix**: Get existing runners BEFORE placing batter, preserve all in final_runner_positions.  
**Location**: Multiple locations in `play_simulation.py` (_handle_hit_baserunning, etc.)

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
docs/                 # Development log (see below)
research/             # Physics references
tests/                # Unit tests
```

### Documentation Strategy: The `docs/` Folder

**Critical**: The `docs/` folder is a **comprehensive development log** tracking the evolution of this project, NOT just reference documentation.

**When Creating Documentation:**
- **All new documentation files MUST go in `docs/`** (not in root or other folders)
- Name files descriptively with context: `FEATURE_NAME_IMPLEMENTATION.md`, `BUG_NAME_FIX.md`, etc.
- Include date context in the file or filename when documenting major changes
- Document WHY decisions were made, not just WHAT was changed

**When Reading Documentation:**
- **Check file modification dates** - newer files reflect current implementation
- **Older docs may be outdated** - if code was radically changed, old design docs may not match current behavior
- **Cross-reference with code** - when in doubt, the code is the source of truth
- **Recent files indicate recent work** - sort by date to understand current project focus

**Examples of Outdated Scenarios:**
- Early phase docs may describe systems that were completely rewritten
- Performance optimization docs may reference old approaches that were replaced
- Bug fix reports document issues that have since been resolved
- Design documents may describe planned features that were implemented differently

**How to Use docs/ Effectively:**
1. **Before making changes**: Check for recent (last 3-6 months) docs on that subsystem
2. **When debugging**: Look for `*_FIX.md` or `*_ANALYSIS.md` files related to the issue
3. **Understanding history**: Read phase summaries (`PHASE1_SUMMARY.md`, etc.) for high-level evolution
4. **After implementing**: Create new doc summarizing what changed and why
5. **When conflicting info**: Newer file dates + actual code behavior override older docs

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

## Research & Physics Documentation

The `research/` directory contains detailed physics documentation that informed the implementation. Refer to these when modifying physics or understanding design decisions:

### **Core Physics References**
- **`Modeling Baseball Batted Ball Trajectories for Realistic Simulation.md`**: 
  - Exit velocity effects (~5 ft per 1 mph), optimal launch angles (25-30°)
  - Magnus force and spin-dependent drag empirical coefficients
  - Environmental effects (Coors Field +30 ft, temperature effects)
  - Backspin/sidespin asymmetric drag modeling
  - **Use when**: Modifying trajectory physics, calibrating distance/flight models

- **`Modeling Baseball Pitching Dynamics.md`**:
  - All 8 pitch types with velocity/spin ranges from MLB Statcast
  - Spin axis orientations and movement profiles per pitch type
  - Position-dependent spin (orientation changes during flight)
  - Pitcher attribute → physics parameter mappings
  - **Use when**: Adding pitch types, adjusting pitch movement, tuning pitcher attributes

- **`Bat Ball Physics Collision Physics.md`**:
  - Sweet spot collision model and contact quality mechanics
  - How off-center hits reduce exit velocity and add unwanted spin
  - Exit velocity as function of bat speed and pitch velocity
  - Contact quality gates (weak/fair/solid) for outcome distributions
  - **Use when**: Modifying contact.py, adjusting hit outcome distributions

- **`Modeling_Baseball_Fielding_and_Baserunning_Mechanics.md`**:
  - Fielder sprint speeds (23-32 ft/s), reaction times (0-0.5s) from Statcast
  - Throwing velocities by position, catch probability models
  - Runner timing validation (home-to-first: 3.7-5.2s)
  - Turn efficiency (75-92%), sliding mechanics with friction
  - **Use when**: Tuning fielding/baserunning physics, adjusting defensive positioning

### **Enhancement Planning**
- **`Baseball Simulation Fielding Improvements.md`**: Documents fielding system design decisions
- **`Baseball Simulation Model Enhancement Plan.md`**: Overall project roadmap and phase planning
- **`Development Plan.md`**: Implementation timeline and integration strategy

### **How to Use Research Docs**
1. **Before changing physics**: Check relevant research doc for empirical basis
2. **When adding features**: Look for related sections in research docs for constraints
3. **When debugging stats**: Research docs explain expected MLB-like outcomes
4. **Cite sources**: Research docs include [citations] to original MLB data sources

## Game Balance & Calibration

### Expected MLB-Like Statistics
When debugging game simulation, check these benchmarks (per 9 innings):
- **Runs/9**: ~9.0 (both teams combined)
- **Hits/9**: ~17.0 (both teams combined)  
- **Home Runs/9**: ~2.2 (both teams combined)
- **BABIP**: ~.300 (batting average on balls in play)
- **Strikeout rate**: ~20-25% of plate appearances

If stats deviate significantly:
- **Low scoring**: Check baserunning margins, fielding catch probability, HR thresholds
- **High BABIP**: Fielders may be positioned poorly or too slow
- **Low BABIP**: Fielders too fast or catch probability too high
- **No doubles/triples**: Check hit type classification in _handle_ball_in_play()

### Common Calibration Files
- `play_simulation.py`: Hit type thresholds, baserunning margins, HR detection
- `fielding.py`: Sprint speeds, reaction times, catch probability model
- `baserunning.py`: Running speeds, turn efficiency, decision thresholds
- `constants.py`: All empirical physics coefficients
