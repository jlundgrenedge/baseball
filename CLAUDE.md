# CLAUDE.md - AI Assistant Guide for Baseball Physics Simulation Engine

**Last Updated**: 2025-01-06
**Repository**: Baseball Physics Simulation Engine
**Purpose**: Guide AI assistants in understanding and working with this codebase
**Version**: 1.3.0 (Rust Acceleration with Full Physics)

---

## Table of Contents
1. [Repository Overview](#repository-overview)
2. [Critical Design Principles](#critical-design-principles)
3. [Codebase Architecture](#codebase-architecture)
4. [Development Workflows](#development-workflows)
5. [Testing Conventions](#testing-conventions)
6. [Common Tasks & Patterns](#common-tasks--patterns)
7. [File Organization Reference](#file-organization-reference)
8. [Performance Considerations](#performance-considerations)
9. [Important Gotchas](#important-gotchas)
10. [Making Changes Safely](#making-changes-safely)

---

## Repository Overview

### What This Is
A **physics-based baseball simulation engine** (~25,600 lines of Python) that models complete games from pitch to play outcome. This is NOT an arcade game or pure statistical simulation - every outcome emerges from rigorous physics calculations calibrated against MLB Statcast data.

### Project Maturity
- **Status**: Production-ready, all 5 development phases complete + Phase 7 Rust acceleration
- **Validation**: 7/7 MLB benchmark tests passing
- **Performance**: Optimized with Rust native code, Numba JIT, parallel processing
- **Documentation**: 42 detailed guides, 8 research papers
- **Version**: 1.3.0 - Rust acceleration with full physics (wind, sidespin)

### Core Capabilities
- Full 9-inning game simulation with realistic play-by-play
- 8 pitch types with spin-dependent aerodynamics
- Bat-ball contact physics with sweet spot modeling
- Complete defensive plays including fielding and baserunning
- Player attribute system (0-100,000 ratings) mapped to physical parameters
- Environmental effects (altitude, temperature, wind)
- Force plays, double plays, and complex baserunning scenarios
- **MLB Integration**: Database system for storing/loading real player data via pybaseball
- **Series Statistics**: Comprehensive multi-game metrics with MLB realism benchmarks
- **Simulation Metrics**: OOTP-style transparency with pitch-level tracking
- **Ballpark System**: MLB stadium dimensions with fence distances and heights
- **Fielding Realism**: Stochastic variance including route efficiency, reaction time, positioning
- **Rust Acceleration**: 5x game speedup via native trajectory integration (Phase 7)

---

## Critical Design Principles

### 1. **Physics-First Approach**
**NEVER** introduce arbitrary rules or probability tables. All gameplay mechanics emerge from physical parameters:
- Contact quality determines exit velocity/launch angle (not rolled dice)
- Fielder attributes control movement speed/reaction (not success probabilities)
- Environmental factors affect aerodynamics realistically

**Example - CORRECT**:
```python
# Exit velocity depends on contact quality (impact location)
exit_velocity = base_velocity * contact_quality_multiplier
```

**Example - INCORRECT**:
```python
# DON'T do this - arbitrary probability table
if random() < 0.3:  # 30% chance of home run
    outcome = "home_run"
```

### 2. **Empirical Calibration**
Every coefficient in `constants.py` is derived from MLB data. When modifying physics:
- Source coefficients from MLB Statcast, research papers, or video analysis
- Document the source in comments
- Run validation suite to ensure benchmarks still pass

### 3. **Coordinate System Consistency**
**CRITICAL**: All modules use identical coordinate system. Breaking this causes fielding/baserunning bugs.

```
Origin: Home plate (0, 0, 0)
X-axis: +X toward right field, -X toward left field
Y-axis: +Y toward center field, -Y toward home plate
Z-axis: +Z upward, -Z downward

Base positions (feet):
- Home plate: (0, 0, 0)
- First base: (63.64, 63.64, 0)
- Second base: (0, 127.28, 0)
- Third base: (-63.64, 63.64, 0)
```

**When modifying fielding/baserunning code**: Verify coordinate consistency by checking calculations against `field_layout.py`.

### 4. **Continuous Attribute Mapping**
Player attributes (0-100,000 scale) map to physical parameters via **continuous functions** (piecewise logistic):

```python
# CORRECT: Continuous mapping in attributes.py using piecewise_logistic_map
def get_bat_speed_mph(self) -> float:
    return piecewise_logistic_map(
        self.BAT_SPEED,  # 0-100,000 rating
        human_min=52.0,  # Minimum human capability
        human_cap=80.0,  # Elite human (at rating=85k)
        super_cap=92.0   # Superhuman (at rating=100k)
    )

# INCORRECT: Hard-coded tiers
if rating >= 80000:
    return 95  # DON'T create discrete buckets
```

### 5. **Validation-Driven Development**
Changes to physics require passing the validation suite:

```bash
python -m batted_ball.validation
```

**Required**: 7/7 tests must pass before committing physics changes:
1. Exit velocity effect (~5 ft per 1 mph)
2. Optimal launch angle (25-30°)
3. Benchmark distance (390-400 ft)
4. Coors Field altitude effect (+30 ft)
5. Backspin effect (+50-60 ft for 1500 RPM)
6. Temperature effect (+3-4 ft per 10°F)
7. Sidespin reduction (-13 ft)

---

## Codebase Architecture

### Module Organization (batted_ball/ package)

#### **Layer 1: Core Physics Engine**
```
constants.py (849 lines)      - ALL empirical coefficients (MLB-calibrated)
environment.py                - Air density, temperature, altitude effects
aerodynamics.py (589 lines)   - Drag + Magnus force (Numba-optimized)
integrator.py (513 lines)     - RK4 numerical solver (DT=0.001s default)
trajectory.py (661 lines)     - BattedBallSimulator class
```

**Key Files**:
- `constants.py`: Modify this for physics tuning. Every constant is documented with source.
- `aerodynamics.py`: Implements spin-dependent drag (key innovation of Phase 1)

#### **Layer 2: Contact & Pitching**
```
contact.py (699 lines)        - Sweet spot physics, impact location effects
pitch.py (880 lines)          - 8 pitch types with spin characteristics
```

**Key Concepts**:
- Sweet spot: ±0.5 inches from center = optimal contact
- Off-center hits: Reduce exit velocity + add unwanted spin
- Pitch types: Each has unique spin axis orientation (position-dependent)

#### **Layer 3: Player Attributes**
```
attributes.py (1,000 lines)   - 0-100,000 → physical parameter mappings
player.py (696 lines)         - Pitcher/Hitter classes
at_bat.py (830 lines)         - Plate appearance simulation
```

**Attribute System**:
- Pitcher: velocity → mph, command → location accuracy, repertoire → pitch mix
- Hitter: bat_speed → exit velocity, contact → sweet spot %, discipline → swing decisions
- All mappings use continuous functions (see `attributes.py` for formulas)

#### **Layer 4: Fielding & Baserunning**
```
field_layout.py (607 lines)           - Field dimensions, position coordinates
fielding.py (1,479 lines) ★LARGEST    - Fielder movement, catching, throwing
baserunning.py (982 lines)            - Runner acceleration, turns, sliding
ground_ball_handler.py (572 lines)    - Ground ball interception logic
fly_ball_handler.py (963 lines)       - Fly ball catch probability
play_simulation.py                    - Coordinate fielding + baserunning
```

**Fielding Physics** (`fielding.py`):
- Sprint speeds: 23-32 ft/s (calibrated to MLB Statcast)
- Reaction times: 0-0.5 seconds based on skill
- Throwing velocities: 70-105 mph (position-dependent)
- Catch timing: Compare hang_time vs time_to_reach

**Baserunning Physics** (`baserunning.py`):
- Home-to-first: 3.7-5.2 seconds (validated against MLB)
- Turn efficiency: 75-92% speed retention at bases
- Sliding: Friction-based deceleration (μ = 0.3)

#### **Layer 5: Game Simulation**
```
game_simulation.py (815 lines)         - 9-inning game orchestration
parallel_game_simulation.py (605)     - Multi-core game simulation
defense_factory.py                    - Helper functions for team creation
play_outcome.py                       - PlayResult, PlayEvent dataclasses
```

#### **Performance Optimization**
```
performance.py (588 lines)            - UltraFastMode, caching, object pooling
bulk_simulation.py (426 lines)        - Efficient large-scale at-bat processing
gpu_acceleration.py (460 lines)       - Optional CUDA acceleration
fast_trajectory.py                    - Optimized trajectory calculations
validation.py                         - 7-benchmark test suite
statcast_calibration.py               - Fetch and compare real MLB Statcast data
statcast_calibration_demo.py          - Demo calibration with synthetic data
```

#### **Layer 6: MLB Database Integration** (NEW in v1.1.0)
```
database/
├── db_schema.py                  - SQLite database schema
├── pybaseball_fetcher.py         - Fetch MLB data via pybaseball
├── stats_converter.py            - MLB stats → game attributes
├── team_database.py              - Database CRUD operations
├── team_loader.py                - Load teams for simulation
└── __init__.py

pybaseball_integration.py         - Create players from MLB stats
hit_handler.py                    - Hit outcome processing
manage_teams.py (root)            - CLI tool for database management
```

**Database System**:
- Fetch real MLB player statistics using pybaseball API
- Convert stats to physics-based game attributes (0-100,000 scale)
- Store teams in SQLite for fast, offline access
- Load teams by name/year without re-scraping
- Support for pitchers, hitters, and fielders

#### **Layer 7: Series Statistics & Metrics** (NEW in v1.2.0)
```
series_metrics.py (708 lines)         - Multi-game statistics aggregation
sim_metrics.py (2,460 lines) ★HUGE   - OOTP-style simulation transparency
route_efficiency.py (380 lines)       - Fielding route quality analysis
ballpark.py (330 lines)               - MLB stadium dimensions & effects
```

**Series Statistics System** (`series_metrics.py`):
- Comprehensive multi-game aggregation (batting, pitching, fielding)
- Advanced sabermetrics: wOBA, ISO, BABIP, HR/FB rate, OPS
- Contact quality metrics: exit velocity, launch angle, barrel %, hard hit %
- MLB realism benchmarks: 10 metrics with pass/fail indicators (✓, ⚠️, 🚨)
- Pitching metrics: ERA, WHIP, K/9, BB/9, HR/9, K/BB ratio
- Run production analysis: totals, averages, ranges, standard deviation
- Larger sample sizes enable robust validation against MLB norms

**Simulation Metrics System** (`sim_metrics.py`):
- OOTP-style transparency for debugging and model tuning
- Pitch-level tracking: release mechanics, trajectory physics, command accuracy
- Contact-level metrics: impact location, exit velocity, launch angle, spin
- Play-level outcomes: fielding assignments, timing, catch probability
- Debug verbosity levels: OFF, BASIC, DETAILED, EXHAUSTIVE
- Physics debugging capabilities for model calibration

**Route Efficiency Analysis** (`route_efficiency.py`):
- Fielder route quality metrics for airborne batted balls
- Optimal vs actual distance traveled calculations
- Route efficiency percentage (quality of path taken)
- Required vs available speed analysis
- Catch probability based on timing margins
- Outcome validation and diagnostic logging

**Ballpark System** (`ballpark.py`):
- MLB stadium-specific dimensions
- Fence distances and heights at various spray angles
- Interpolation for smooth fence profile
- Park factors affecting batted ball outcomes
- Support for unique ballpark features (Green Monster, short porches, etc.)

### Dependency Graph

```
BOTTOM LAYER (Physics Foundation)
constants.py → environment.py → aerodynamics.py → integrator.py → trajectory.py

MIDDLE LAYER (Contact & Pitching)
contact.py ← pitch.py

PLAYER LAYER
player.py ← attributes.py ← at_bat.py

FIELD LAYER
field_layout.py → fielding.py ↔ baserunning.py
                ↓
         play_simulation.py → hit_handler.py

GAME LAYER
game_simulation.py ← play_simulation.py

DATABASE LAYER (Optional, v1.1.0+)
pybaseball_fetcher → stats_converter → team_database → team_loader
                                            ↓
                                        player.py

STATISTICS & METRICS LAYER (Optional, v1.2.0+)
game_simulation.py → series_metrics.py → MLB realism benchmarks
                  ↘ sim_metrics.py → pitch/contact/play tracking
fielding.py → route_efficiency.py → route quality analysis
ballpark.py → batted ball outcomes (fence interactions)

PERFORMANCE OVERLAY (Optional)
performance.py, bulk_simulation.py, parallel_game_simulation.py, statcast_calibration.py
```

**Import Pattern**: Lower layers never import from higher layers. Changes to `constants.py` affect everything; changes to `game_simulation.py` affect nothing else. Database layer is optional and sits alongside the player layer.

---

## Development Workflows

### Workflow 1: Modifying Physics Parameters

**When to use**: Tuning drag coefficients, player attribute ranges, fielding speeds

**Steps**:
1. **Identify the constant**: Check `constants.py` first (849 lines, well-commented)
2. **Document your source**: Add comment citing MLB data, research paper, or rationale
3. **Make the change**: Modify the value
4. **Run validation**: `python -m batted_ball.validation`
5. **Check benchmarks**: Ensure 7/7 tests still pass
6. **Test gameplay**: Run a quick game to verify realistic outcomes

**Example**:
```python
# In constants.py
# OLD: C_D_0 = 0.35  # Base drag coefficient (source: Smith et al. 2019)
# NEW: C_D_0 = 0.33  # Adjusted based on 2024 Statcast data

# Validate
$ python -m batted_ball.validation
# Output: 7/7 tests passed ✓
```

### Workflow 2: Adding a New Pitch Type

**Location**: `pitch.py` (880 lines)

**Steps**:
1. **Define spin characteristics**: Specify spin axis orientation and typical RPM
2. **Add factory function**: Create `create_<pitch_type>()` following existing pattern
3. **Test trajectory**: Use `examples/validate_pitch.py` to verify movement
4. **Update pitcher repertoire**: Modify pitch selection logic in `at_bat.py`
5. **Document**: Add description to pitch type docstrings

**Pattern to follow** (from existing pitch types):
```python
def create_cutter(velocity_mph: float) -> Pitch:
    """Cutter: Slight cutting action away from arm side."""
    spin_rpm = velocity_mph * 15  # ~1400 RPM at 95 mph
    return Pitch(
        pitch_type="cutter",
        velocity_mph=velocity_mph,
        spin_rpm=spin_rpm,
        spin_axis_azimuth=45,    # Degrees from vertical
        spin_axis_elevation=10,  # Degrees from horizontal
        gyro_degree=15          # Spin efficiency
    )
```

### Workflow 3: Tuning Player Attributes

**Location**: `attributes.py` (1,000 lines)

**Key Functions**:
- `get_raw_velocity_mph()`: Pitcher velocity (0-100k → 70-108 mph)
- `get_bat_speed_mph()`: Hitter bat speed (0-100k → 52-92 mph)
- `get_command_sigma_inches()`: Pitch location accuracy (0-100k → 8" - 0.8" std dev)
- `get_barrel_accuracy_mm()`: Contact point error (0-100k → 40mm - 2mm RMS)

**When tuning**:
1. Identify which physical parameter needs adjustment
2. Modify the piecewise_logistic_map parameters (human_min, human_cap, super_cap)
3. Test with `examples/demonstrate_batter_vs_pitcher.py`
4. Verify realistic stat distributions (BA, HR rate)

**Example - Increasing power**:
```python
# OLD: Less bat speed at elite level
def get_bat_speed_mph(self) -> float:
    return piecewise_logistic_map(
        self.BAT_SPEED,
        human_min=52.0,
        human_cap=80.0,   # Old elite cap
        super_cap=92.0
    )

# NEW: More power at elite level
def get_bat_speed_mph(self) -> float:
    return piecewise_logistic_map(
        self.BAT_SPEED,
        human_min=52.0,
        human_cap=83.0,   # Increased elite cap (+3 mph)
        super_cap=95.0    # Increased superhuman cap (+3 mph)
    )
```

### Workflow 4: Debugging Fielding/Baserunning Issues

**Common issues**: Wrong fielder assigned, runners not advancing, impossible throws

**Debugging tools**:
1. **Enable verbose mode**: `GameSimulator(home, away, verbose=True)`
2. **Check coordinates**: Print fielder positions and ball landing locations
3. **Verify timing**: Check `time_to_reach` vs `hang_time` calculations
4. **Use test scripts**: `examples/debug_fielding.py`, `test_baserunning_bug.py`

**Key files to check**:
- `field_layout.py`: Verify position coordinates are correct
- `fielding.py`: Check fielder assignment logic (`_assign_fielder_to_ball()`)
- `baserunning.py`: Verify runner advancement decisions

**Common bug pattern** - Coordinate system mismatch:
```python
# WRONG: Mixing coordinate systems
ball_x = result.final_x  # In physics coordinates (feet, home plate origin)
fielder_x = 200  # In field coordinates (feet, different origin)
distance = abs(ball_x - fielder_x)  # INCORRECT - different reference frames

# CORRECT: Use field_layout helpers
from batted_ball.field_layout import FieldLayout
field = FieldLayout()
ball_pos = (result.final_x, result.final_y, 0)
fielder_pos = field.get_position("CF")
distance = field.distance_between(ball_pos, fielder_pos)
```

### Workflow 5: Adding New Game Statistics

**Location**: `game_simulation.py` (815 lines)

**Pattern**:
1. Add stat tracking to `GameState` dataclass
2. Update stat in appropriate game loop location
3. Add to final summary output

**Example - Tracking strikeouts**:
```python
# In GameState dataclass
@dataclass
class GameState:
    # ... existing fields ...
    strikeouts_home: int = 0
    strikeouts_away: int = 0

# In simulate_inning() method
if at_bat_result.outcome == "strikeout":
    if is_home_batting:
        self.strikeouts_home += 1
    else:
        self.strikeouts_away += 1

# In final summary
print(f"Strikeouts: Away {state.strikeouts_away}, Home {state.strikeouts_home}")
```

### Workflow 6: Working with MLB Database System (NEW in v1.1.0)

**Purpose**: Create teams from real MLB player statistics

**Quick Start**:
```bash
# Install pybaseball (if not already installed)
pip install pybaseball

# Add a team to database
python manage_teams.py add NYY 2024

# List all teams in database
python manage_teams.py list

# Simulate a matchup
python examples/simulate_mlb_matchup.py "New York Yankees" "Los Angeles Dodgers" 2024
```

**Key Components**:

1. **Fetching MLB Data** (`database/pybaseball_fetcher.py`):
   - Uses pybaseball library to get player stats
   - Fetches batting stats, pitching stats, sprint speeds
   - Handles missing data gracefully

2. **Converting Stats** (`database/stats_converter.py`):
   - Maps MLB statistics → 0-100,000 game attributes
   - Converts: BA, OBP, SLG → contact/power/discipline
   - Converts: ERA, WHIP, K/9 → velocity/command/stamina
   - Includes fielding metrics for defensive ratings

3. **Database Operations** (`database/team_database.py`):
   - SQLite database for persistence
   - CRUD operations for teams, pitchers, hitters, fielders
   - Automatic schema creation
   - Team versioning by year

4. **Loading Teams** (`database/team_loader.py`):
   - Load teams from database for simulations
   - Creates Pitcher, Hitter, Fielder objects
   - Handles batting order and pitching rotation

**Example - Adding Multiple Teams**:
```python
from batted_ball.database import TeamDatabase, PybaseballFetcher, StatsConverter

db = TeamDatabase()
fetcher = PybaseballFetcher()
converter = StatsConverter()

# Add Yankees 2024
team_abbr = "NYY"
season = 2024

# Fetch and store
pitchers_df = fetcher.fetch_team_pitching(team_abbr, season)
hitters_df = fetcher.fetch_team_batting(team_abbr, season)

# Convert to attributes
pitchers = converter.convert_pitchers(pitchers_df)
hitters = converter.convert_hitters(hitters_df)

# Store in database
db.add_team("New York Yankees", season, pitchers, hitters)
```

**Example - Using Database Teams in Games**:
```python
from batted_ball.database import TeamLoader
from batted_ball import GameSimulator

loader = TeamLoader()

# Load teams from database
yankees = loader.load_team("New York Yankees", 2024)
dodgers = loader.load_team("Los Angeles Dodgers", 2024)

# Simulate game
sim = GameSimulator(yankees, dodgers, verbose=True)
result = sim.simulate_game(num_innings=9)

print(f"Final: {yankees.name} {result.away_score} - {result.home_score} {dodgers.name}")
```

**Managing Database** (CLI tool):
```bash
# Add single team
python manage_teams.py add NYY 2024

# Add with custom filters
python manage_teams.py add LAD 2024 --min-innings 20 --min-at-bats 50

# Add multiple teams at once
python manage_teams.py add-multiple 2024 NYY BOS TB TOR BAL

# List teams
python manage_teams.py list              # All teams
python manage_teams.py list --season 2024  # Specific season

# Delete team
python manage_teams.py delete "New York Yankees" 2024

# View team details
python manage_teams.py info "Los Angeles Dodgers" 2024
```

**Stat Conversion Mappings**:

The `stats_converter.py` module maps MLB statistics to game attributes:

**Hitters**:
- Contact: f(BA, K%, Contact%) - Batting average, strikeout rate
- Power: f(SLG, ISO, HR) - Slugging, isolated power, home runs
- Discipline: f(BB%, OBP) - Walk rate, on-base percentage
- Speed: f(Sprint_Speed, SB) - Statcast sprint speed or stolen bases

**Pitchers**:
- Velocity: f(AVG_Velo, FB_Velo) - Average/fastball velocity
- Command: f(BB/9, WHIP) - Walk rate, baserunners allowed
- Stamina: f(IP/GS) - Innings per game started
- Repertoire: Based on pitch mix distribution

**Fielders**:
- Reaction: f(Outs_Above_Avg, Range_Runs) - Defensive metrics
- Speed: f(Sprint_Speed) - Statcast sprint speed
- Arm: f(Assists, Position) - Throwing ability by position
- Hands: f(Fielding_Pct, Errors) - Catching reliability

**Database Schema**:
- `teams`: Team metadata (name, season, created_at)
- `pitchers`: Pitcher attributes linked to team
- `hitters`: Hitter attributes linked to team
- `fielders`: Fielder defensive attributes

**Important Notes**:
- First pybaseball fetch may take 30-60 seconds (caching enabled)
- Some players may have incomplete stats (system uses reasonable defaults)
- Database stored at `batted_ball/database/teams.db` by default
- See `DATABASE_README.md` for complete documentation

---

## Testing Conventions

> **⚠️ IMPORTANT**: See `TESTING_STRATEGY.md` for the current testing philosophy.
> The simulation is designed to model real MLB baseball - test with real teams.

### Primary Testing Method: MLB Database Games

```bash
game_simulation.bat → Option 8 → Select teams → 5-10 games
```

**This is your main testing workflow.** Uses real MLB teams from the database.

- **Recommended**: 5-10 games (fast, still statistically meaningful)
- **Time**: 5-10 games ≈ 1-3 minutes
- **Output**: Game logs saved to `game_logs/` folder
- **Never run more than 10 games** - it's slow and unnecessary

### Physics Validation (Required for physics changes)

```bash
python -m batted_ball.validation  # Must pass 7/7 tests
```

Only run this when modifying physics code (`constants.py`, `aerodynamics.py`, etc.)

### Quick Smoke Test (optional)

```bash
python examples/quick_game_test.py
```

Basic sanity check that game flow works (~10 seconds).

### Tests to AVOID

These tests use synthetic `create_test_team()` and don't reflect real MLB gameplay:

| Test | Problem |
|------|---------|
| `test_league_simulation.py` | 240 games with fake teams |
| `test_league_simulation_quick.py` | 112 games with fake teams |
| `test_parallel_*.py` | Performance only, fake teams |
| `test_*_tuning.py` | Outdated calibration, fake teams |

### Expected Game Stats (per 9 innings, 2-team combined)

| Metric | Expected Range | Red Flag |
|--------|----------------|----------|
| Runs | 8-10 | < 4 or > 16 |
| Hits | 15-20 | < 10 or > 28 |
| K% | 20-28% | < 15% or > 35% |
| BB% | 8-12% | < 4% or > 18% |
| HR | 2-4 | 0 in 5 games or > 8 |
| BABIP | .280-.320 | < .200 or > .400 |

---

## Common Tasks & Patterns

### Task 1: Simulate a Single At-Bat

```python
from batted_ball import AtBatSimulator, Pitcher, Hitter

# Create players
pitcher = Pitcher(name="Ace", velocity=85, command=75, stamina=80)
hitter = Hitter(name="Slugger", contact=70, power=85, discipline=60)

# Simulate
sim = AtBatSimulator(pitcher, hitter)
result = sim.simulate_at_bat()

print(f"Outcome: {result.outcome}")
print(f"Pitches: {len(result.pitches)}")
```

**Possible outcomes**: `strikeout`, `walk`, `single`, `double`, `triple`, `home_run`, `ground_out`, `fly_out`, `line_out`

### Task 2: Analyze Batted Ball Trajectory

```python
from batted_ball import BattedBallSimulator

sim = BattedBallSimulator()
result = sim.simulate(
    exit_velocity=100.0,    # mph
    launch_angle=28.0,      # degrees (optimal)
    spray_angle=0.0,        # degrees (0 = center field)
    backspin_rpm=1800.0,    # rpm
    sidespin_rpm=0.0,       # rpm
    altitude=0.0,           # feet (sea level)
    temperature=70.0        # Fahrenheit
)

print(f"Distance: {result.distance:.1f} ft")
print(f"Flight time: {result.flight_time:.2f} s")
print(f"Peak height: {result.peak_height:.1f} ft")
print(f"Landing position: ({result.final_x:.1f}, {result.final_y:.1f})")
```

### Task 3: Create Custom Teams

```python
from batted_ball.game_simulation import Team, create_test_team
from batted_ball import Pitcher, Hitter

# Option 1: Use factory (quick)
team = create_test_team("Yankees", quality="elite")  # or "good", "average", "poor"

# Option 2: Manual construction (precise control)
pitchers = [
    Pitcher("Ace", velocity=95, command=85, stamina=90),
    Pitcher("Starter 2", velocity=88, command=75, stamina=85),
    # ... 9 total pitchers
]
hitters = [
    Hitter("Leadoff", contact=80, power=60, discipline=75, speed=85),
    Hitter("Cleanup", contact=75, power=95, discipline=65, speed=50),
    # ... 9 total hitters (batting order)
]
team = Team(name="Custom", pitchers=pitchers, lineup=hitters)
```

**Attribute guidelines**:
- Elite player: 85-100 in primary skills
- Good player: 70-85
- Average player: 50-70
- Below average: 30-50

### Task 4: Environmental Comparisons

```python
from batted_ball import BattedBallSimulator, Environment

# Sea level (standard conditions)
env_sea = Environment(altitude=0, temperature=70, humidity=0.5)
sim_sea = BattedBallSimulator(environment=env_sea)
dist_sea = sim_sea.simulate(100, 28, 0, 1800, 0).distance

# Coors Field (5,200 ft altitude)
env_coors = Environment(altitude=5200, temperature=75, humidity=0.3)
sim_coors = BattedBallSimulator(environment=env_coors)
dist_coors = sim_coors.simulate(100, 28, 0, 1800, 0).distance

print(f"Sea level: {dist_sea:.1f} ft")
print(f"Coors Field: {dist_coors:.1f} ft")
print(f"Boost: +{dist_coors - dist_sea:.1f} ft")
# Expected output: ~30 ft boost at Coors
```

### Task 5: Batch Simulations (Performance Mode)

```python
from batted_ball import BulkAtBatSimulator, BulkSimulationSettings

settings = BulkSimulationSettings(
    num_at_bats=10000,
    fast_mode=True,              # 2x speedup
    track_detailed_stats=True
)

bulk_sim = BulkAtBatSimulator(pitcher, hitter)
results = bulk_sim.simulate_bulk(settings)

print(f"Batting average: {results.batting_average:.3f}")
print(f"Slugging percentage: {results.slugging_pct:.3f}")
print(f"Home runs: {results.home_runs}")
print(f"Strikeouts: {results.strikeouts}")
```

### Task 6: Parallel Game Simulation

```python
from batted_ball import ParallelGameSimulator, ParallelSimulationSettings

settings = ParallelSimulationSettings(
    num_workers=4,        # CPU cores to use
    chunk_size=10,        # Games per worker batch
    verbose=False
)

sim = ParallelGameSimulator(settings)
results = sim.simulate_games(away_team, home_team, num_games=60)

print(f"Home wins: {results.home_wins}")
print(f"Away wins: {results.away_wins}")
print(f"Average score: {results.avg_home_score:.1f} - {results.avg_away_score:.1f}")
```

### Task 7: Series Statistics with MLB Benchmarks (NEW in v1.2.0)

```python
from batted_ball import GameSimulator, SeriesMetrics

# Create series metrics aggregator
series = SeriesMetrics()

# Simulate multiple games
for game_num in range(10):
    sim = GameSimulator(away_team, home_team, verbose=False)
    result = sim.simulate_game(num_innings=9)

    # Add game to series aggregation
    series.add_game(result)

# Print comprehensive statistics
print(series.get_summary_report())

# Check MLB realism benchmarks
benchmarks = series.get_mlb_realism_benchmarks()
print("\nMLB Realism Check:")
for metric_name, (value, status, expected) in benchmarks.items():
    print(f"{status} {metric_name}: {value:.3f} (expected: {expected})")

# Access specific stats
print(f"\nTeam wOBA: {series.batting_metrics.get_woba():.3f}")
print(f"Team ISO: {series.batting_metrics.get_iso():.3f}")
print(f"Team ERA: {series.pitching_metrics.get_era():.2f}")
print(f"Team WHIP: {series.pitching_metrics.get_whip():.2f}")
```

### Task 8: Using Simulation Metrics for Debugging (NEW in v1.2.0)

```python
from batted_ball import AtBatSimulator
from batted_ball.sim_metrics import DebugLevel, SimulationMetricsCollector

# Create metrics collector with desired verbosity
metrics = SimulationMetricsCollector(debug_level=DebugLevel.DETAILED)

# Simulate at-bat with metrics tracking
sim = AtBatSimulator(pitcher, hitter, metrics_collector=metrics)
result = sim.simulate_at_bat()

# Access pitch-level data
for pitch_metric in metrics.pitch_metrics:
    print(f"Pitch {pitch_metric.sequence_index}: {pitch_metric.pitch_type}")
    print(f"  Velocity: {pitch_metric.release_velocity_mph:.1f} mph")
    print(f"  Location: ({pitch_metric.plate_x_inches:.1f}, {pitch_metric.plate_z_inches:.1f})")
    print(f"  Outcome: {pitch_metric.pitch_outcome}")

# Access contact-level data (if contact was made)
if metrics.contact_metrics:
    contact = metrics.contact_metrics[-1]
    print(f"\nContact Quality:")
    print(f"  Exit velocity: {contact.exit_velocity_mph:.1f} mph")
    print(f"  Launch angle: {contact.launch_angle_deg:.1f}°")
    print(f"  Impact location: {contact.impact_location_mm:.1f} mm from sweet spot")

# Access play-level outcomes
if metrics.play_metrics:
    play = metrics.play_metrics[-1]
    print(f"\nPlay Outcome:")
    print(f"  Assigned fielder: {play.assigned_fielder}")
    print(f"  Catch probability: {play.catch_probability:.2%}")
```

---

## File Organization Reference

### Root Directory Structure
```
/home/user/baseball/
├── batted_ball/              # Main package (45+ Python modules, ~25,600 lines)
│   └── database/             # MLB database system (6 modules, v1.1.0)
├── tests/                    # Test suite (22+ files)
├── examples/                 # Usage demonstrations (21+ files)
├── docs/                     # Documentation (42 MD files)
├── research/                 # Physics research papers (8 files)
├── requirements.txt          # Dependencies (numpy, scipy, matplotlib, numba, pybaseball)
├── README.md                 # User-facing documentation
├── CLAUDE.md                 # This file (AI assistant guide)
├── DATABASE_README.md        # MLB database system guide (v1.1.0)
├── manage_teams.py           # CLI tool for team database (v1.1.0)
├── game_simulation.bat       # Windows runner (interactive menu)
├── performance_test_suite.py # Performance testing script
└── .gitignore                # Standard Python ignores
```

### Key Files by Purpose

**Starting point for understanding**:
1. `README.md` - User-facing overview
2. `batted_ball/__init__.py` - Package exports and public API
3. `batted_ball/constants.py` - All physics constants (start here for tuning)
4. `DATABASE_README.md` - MLB database system guide (v1.1.0)
5. `CLAUDE.md` - This file (AI assistant guide)

**Core physics implementation**:
6. `batted_ball/aerodynamics.py` - Drag + Magnus force
7. `batted_ball/trajectory.py` - BattedBallSimulator class
8. `batted_ball/contact.py` - Sweet spot physics

**Player & gameplay**:
9. `batted_ball/attributes.py` - Attribute → physics mappings
10. `batted_ball/at_bat.py` - Plate appearance logic
11. `batted_ball/game_simulation.py` - 9-inning orchestration

**Fielding & baserunning** (most complex):
12. `batted_ball/fielding.py` - Fielder movement, catching, throwing (1,800+ lines)
13. `batted_ball/baserunning.py` - Runner mechanics (982 lines)
14. `batted_ball/field_layout.py` - Coordinate system reference
15. `batted_ball/hit_handler.py` - Hit outcome processing
16. `batted_ball/route_efficiency.py` - Route quality analysis (NEW v1.2.0)

**Validation & performance**:
17. `batted_ball/validation.py` - 7-benchmark test suite
18. `batted_ball/performance.py` - Optimization modes
19. `batted_ball/statcast_calibration.py` - MLB data validation (v1.1.1)
20. `tests/test_league_simulation.py` - Comprehensive game testing

**MLB Database System** (v1.1.0):
21. `batted_ball/database/team_database.py` - SQLite CRUD operations
22. `batted_ball/database/stats_converter.py` - MLB stats → attributes
23. `batted_ball/database/pybaseball_fetcher.py` - Fetch real player data
24. `manage_teams.py` - CLI for database management

**Series Statistics & Metrics** (NEW in v1.2.0):
25. `batted_ball/series_metrics.py` - Multi-game aggregation with MLB benchmarks
26. `batted_ball/sim_metrics.py` - OOTP-style simulation transparency (HUGE: 2,460 lines)
27. `batted_ball/ballpark.py` - MLB stadium dimensions and effects

### Documentation Hierarchy

**Quick reference** (read first):
- `docs/IMPLEMENTATION_SUMMARY.md` - Overall architecture
- `docs/COORDINATE_SYSTEM_GUIDE.md` - Critical for fielding/baserunning work
- `docs/PHASE5_FIELDING_BASERUNNING_SUMMARY.md` - Complex play mechanics

**Deep dives** (for major changes):
- `research/Modeling Baseball Batted Ball Trajectories.md` - Phase 1 physics
- `research/Bat Ball Physics Collision Physics.md` - Phase 2 contact
- `research/Modeling_Baseball_Fielding_and_Baserunning_Mechanics.md` - Phase 5

**Tuning guides**:
- `docs/SCORING_CALIBRATION_2024.md` - MLB stat alignment
- `docs/BAT_SPEED_COLLISION_TUNING_2024.md` - Contact mechanics
- `docs/FIELDING_CATCH_PROBABILITY_TUNING_2024.md` - Catch model

---

## Performance Considerations

### Rust Acceleration (Phase 7 - Primary Optimization)

The simulation uses native Rust code for trajectory calculations, achieving **5x game speedup**:

**Performance Results**:
| Metric | Before Rust | After Rust | Speedup |
|--------|-------------|------------|---------|
| Game (with wind) | ~30s | **6.2s** | **5x** |
| Batted balls/sec | 4 | **1000+** | **250x** |
| Pitch simulation | 22/sec | **158/sec** | **7x** |

**Rust Library** (`trajectory_rs/`):
- PyO3 bindings for Python integration
- Rayon for parallel batch processing
- Full physics: wind, backspin, topspin, sidespin
- Build: `cd trajectory_rs && maturin build --release && pip install target/wheels/*.whl`

**Key Functions**:
- `integrate_trajectory()`: Standard trajectory (no wind)
- `integrate_trajectory_with_wind()`: Wind-aware trajectory
- `integrate_trajectories_batch()`: Parallel batch processing

**Checking Availability**:
```python
from batted_ball.fast_trajectory import is_rust_available, get_rust_version

if is_rust_available():
    print(f"Rust: {get_rust_version()}")  # Auto-used by BattedBallSimulator
```

### Performance Modes

**Standard Mode** (default):
- Time step: 0.001s (1ms) - maximum accuracy
- Typical at-bat: 50-200ms
- Full game: ~6 seconds (with Rust)
- **Use when**: Precision matters, single game simulations

**Fast Mode**:
```python
sim = AtBatSimulator(pitcher, hitter, fast_mode=True)  # 2x faster
```
- Time step: 0.002s (2ms)
- Accuracy loss: <1%
- **Use when**: Bulk simulations (1000+ at-bats)

**UltraFast Mode**:
```python
from batted_ball.performance import UltraFastMode

with UltraFastMode():
    # Your simulation code here
    sim.simulate_game(num_innings=9)
    # 10x speedup, <2% accuracy loss
```
- Aggressive caching + optimizations
- **Use when**: Large-scale analysis, league simulations

### Numba JIT Compilation

**First run**: 2-5 seconds compilation time (one-time cost)
**Subsequent runs**: 5-10× speedup

**Numba-optimized functions**:
- `aerodynamics._compute_forces()` - Called millions of times
- `integrator.rk4_step()` - Trajectory integration
- Critical loops in fielding/baserunning

**No action needed** - Numba decorators already applied to hot paths.

### Parallel Processing

```python
from batted_ball import ParallelGameSimulator

# Automatically uses multiple CPU cores
sim = ParallelGameSimulator(settings)
results = sim.simulate_games(away, home, num_games=60)
# 5-8× speedup on 8-core machines
```

**When to use**: Simulating 10+ games, league seasons, large-scale stat analysis

### Performance Profiling

```bash
# Benchmark current performance
python performance_test_suite.py

# Run specific benchmarks
python -c "
from batted_ball.performance import PerformanceTracker
tracker = PerformanceTracker()
# Your code here
tracker.print_summary()
"
```

---

## Important Gotchas

### 1. Coordinate System Confusion

**GOTCHA**: Different modules historically used different coordinate systems. This has been fixed, but verify when modifying fielding/baserunning.

**Verification**:
```python
from batted_ball.field_layout import FieldLayout
field = FieldLayout()

# All positions should use home plate origin
cf_pos = field.get_position("CF")
print(cf_pos)  # Should be (0, 400, 0) - center field 400 ft from home
```

**Files to check**: `field_layout.py`, `fielding.py`, `baserunning.py`

### 2. Units: Internal vs External

**Internal (physics calculations)**: SI units (meters, m/s, kg)
**External (user API)**: Baseball units (feet, mph, degrees)

**Conversions handled in**: `constants.py`

**GOTCHA**: When adding new physics calculations, use SI units internally:
```python
# CORRECT
def calculate_distance_internal(velocity_mps, time_s):
    return velocity_mps * time_s  # meters

# Convert at API boundary
def calculate_distance(velocity_mph, time_s):
    velocity_mps = velocity_mph * MPH_TO_MPS
    distance_m = calculate_distance_internal(velocity_mps, time_s)
    return distance_m * METERS_TO_FEET
```

### 3. Player Attribute Ranges

**GOTCHA**: Attributes use 0-100,000 scale, but realistic players typically fall in 30k-100k range. Values below 30k produce unrealistic physics.

**Safe ranges**:
- Elite: 85k-100k (superhuman range starts at 85k)
- Good: 65k-85k (above average to elite human)
- Average: 45k-65k (typical MLB player)
- Below average: 30k-45k (fringe MLB / minor league)
- **Avoid**: 0-30k (produces unplayable characters)

### 4. Time Step Sensitivity

**GOTCHA**: Changing `DT_DEFAULT` in `constants.py` affects ALL physics calculations. Smaller = more accurate but slower.

**Current values**:
```python
DT_DEFAULT = 0.001  # 1ms - standard mode
DT_FAST = 0.002     # 2ms - fast mode
```

**Don't change unless**: Running comprehensive validation after change.

### 5. Validation Suite Must Pass

**GOTCHA**: The 7-benchmark validation suite is non-negotiable. If physics changes break validation, the model is no longer empirically accurate.

**Always run before committing**:
```bash
python -m batted_ball.validation
# Must see: "All validation tests passed! (7/7)"
```

### 6. Fielding Assignment Logic

**GOTCHA**: Ball landing in "no man's land" between fielders can cause ambiguous assignments. The code handles this, but edge cases exist.

**Location**: `fielding.py` → `_assign_fielder_to_ball()`

**Debug approach**:
```python
# Enable verbose to see fielder assignments
sim = GameSimulator(home, away, verbose=True)
# Look for: "Assigned to: <fielder_name>"
```

### 7. Numba Compilation Warnings

**GOTCHA**: First run shows Numba compilation warnings. These are normal and one-time.

**Expected output**:
```
NumbaDeprecationWarning: The 'nopython' keyword argument was not supplied...
<function compiled successfully>
```

**Action**: Ignore warnings, verify speedup on second run.

### 8. File Path Assumptions

**GOTCHA**: Some example scripts assume they're run from the root directory.

**Incorrect**:
```bash
cd examples/
python game_simulation_demo.py  # May fail with import errors
```

**Correct**:
```bash
# Run from root
python examples/game_simulation_demo.py
```

---

## Making Changes Safely

### Pre-Change Checklist

Before modifying core physics:
- [ ] Read relevant documentation in `docs/`
- [ ] Understand current implementation by reading source + comments
- [ ] Identify validation tests affected by change
- [ ] Document the reason for change (MLB data, bug fix, etc.)

### Change Implementation Checklist

1. **Make the change**
   - Modify source files
   - Add/update comments with source citations
   - Follow existing code style

2. **Validate physics**
   ```bash
   python -m batted_ball.validation
   # Must achieve 7/7 passing
   ```

3. **Test gameplay**
   ```bash
   python examples/quick_game_test.py
   # Verify reasonable outcomes
   ```

4. **Check performance**
   ```bash
   python performance_test_suite.py
   # Verify no major regression (>20% slowdown)
   ```

5. **Update documentation**
   - Update relevant `docs/*.md` files
   - Update `CLAUDE.md` if architecture changes
   - Update `README.md` if user-facing API changes

### Post-Change Checklist

- [ ] All validation tests pass (7/7)
- [ ] Game simulation produces realistic scores (0-15 runs typical)
- [ ] No performance regression (>20% slowdown)
- [ ] Documentation updated
- [ ] Code commented with sources
- [ ] Commit with descriptive message

### Git Workflow

**Branch naming**: Use `claude/` prefix for AI-generated branches
```bash
git checkout -b claude/feature-description-SESSION_ID
```

**Commit message format**:
```
Brief description of change

- Detailed point 1
- Detailed point 2
- Validation: 7/7 tests passing

Source: MLB Statcast 2024, Smith et al. 2019, etc.
```

**Before pushing**:
```bash
# Verify validation
python -m batted_ball.validation

# Quick game test
python examples/quick_game_test.py

# Check git status
git status
git diff

# Commit
git add <files>
git commit -m "Message"

# Push to feature branch
git push -u origin <branch-name>
```

---

## Quick Reference: Common File Locations

### When Working On...

**Physics tuning** → `batted_ball/constants.py`
**Pitch types** → `batted_ball/pitch.py`
**Player attributes** → `batted_ball/attributes.py`
**Contact quality** → `batted_ball/contact.py`
**Fielding logic** → `batted_ball/fielding.py`
**Baserunning** → `batted_ball/baserunning.py`
**Game flow** → `batted_ball/game_simulation.py`
**Validation** → `batted_ball/validation.py`
**Performance** → `batted_ball/performance.py`
**MLB data integration** → `batted_ball/database/` (NEW)
**Team management** → `manage_teams.py` (NEW)

### When You Need To...

**Understand architecture** → `docs/IMPLEMENTATION_SUMMARY.md`
**Debug coordinates** → `docs/COORDINATE_SYSTEM_GUIDE.md`
**Learn physics** → `research/Modeling Baseball Batted Ball Trajectories.md`
**Tune scoring** → `docs/SCORING_CALIBRATION_2024.md`
**Use MLB database** → `DATABASE_README.md` (v1.1.0)
**Use series statistics** → `batted_ball/series_metrics.py` or examples (v1.2.0)
**Debug simulations** → `docs/SIM_METRICS_GUIDE.md` (v1.2.0)
**Understand ballparks** → `docs/BALLPARK_HIT_CLASSIFICATION.md` (v1.2.0)
**Validate against Statcast** → `docs/STATCAST_CALIBRATION_FINDINGS.md` (v1.1.1+)
**See examples** → `examples/` directory
**Run tests** → `tests/` directory

---

## Advanced Topics

### Custom Validation Tests

Add new benchmark tests to `validation.py`:

```python
def test_custom_scenario(self):
    """Test description with expected outcome from MLB data."""
    sim = BattedBallSimulator()
    result = sim.simulate(
        exit_velocity=...,
        launch_angle=...,
        # ... parameters
    )

    expected_min = ...  # From MLB data
    expected_max = ...

    if expected_min <= result.distance <= expected_max:
        return True, f"✓ PASS: {result.distance:.1f} ft"
    else:
        return False, f"✗ FAIL: {result.distance:.1f} ft (expected {expected_min}-{expected_max})"
```

### GPU Acceleration (Optional)

If CUDA is available:
```python
from batted_ball.gpu_acceleration import GPUAccelerator

accelerator = GPUAccelerator()
if accelerator.is_available():
    # 10-100× speedup for batch simulations
    results = accelerator.simulate_batch(parameters)
```

**Note**: Requires CUDA-capable GPU and CuPy installation. See `gpu_acceleration.py` for details.

### Custom Fielding Positions

```python
from batted_ball.field_layout import FieldLayout

field = FieldLayout()

# Add custom position
field.add_custom_position(
    position_name="Rover",  # 4-man outfield
    coordinates=(50, 150, 0)  # Shallow center
)

# Use in defense
from batted_ball.fielding import Fielder
rover = Fielder(name="Rover", position="Rover", ...)
```

---

## Conclusion

### Key Principles Recap

1. **Physics-first**: Every outcome from physical simulation, not probability tables
2. **Empirically calibrated**: All constants from MLB data
3. **Coordinate consistency**: Home plate origin, unified across all modules
4. **Continuous attributes**: Smooth mapping from 0-100,000 ratings to physics via piecewise logistic functions
5. **Validation-driven**: 7/7 benchmarks must pass

### When in Doubt

1. **Check `constants.py`** - Most tunable parameters live here
2. **Run validation** - `python -m batted_ball.validation`
3. **Read docs** - 42 guides in `docs/`, 8 research papers in `research/`
4. **Test with examples** - 17 demonstration scripts in `examples/`
5. **Ask questions** - This is a complex system; better to clarify than break

### Resources

- **README.md**: User-facing overview
- **docs/**: 42 detailed implementation guides
- **research/**: Deep physics derivations
- **examples/**: Working code demonstrations
- **tests/**: Validation and regression tests

---

**Last Updated**: 2025-01-06
**Version**: 1.3.0
**Maintainer**: Baseball Physics Simulation Engine Project
**Status**: Production-ready, all 5 phases complete + MLB database + series statistics + Rust acceleration
**Validation**: 7/7 MLB benchmarks passing ✓

---

## Recent Changes

### v1.3.0 - 2025-01-06 (Rust Acceleration with Full Physics)

**Major Performance Improvement**: 5x game speedup via native Rust trajectory integration

1. **Rust Trajectory Library** (`trajectory_rs/`)
   - PyO3 0.23 bindings for seamless Python integration
   - Rayon for parallel batch processing
   - RK4 integrator matching Python physics exactly
   - ~500 lines of Rust code

2. **Full Physics Support in Rust**
   - **Wind support**: `integrate_trajectory_with_wind()` function
   - Proper relative velocity calculation: `drag = f(ball_velocity - wind_velocity)`
   - **Full spin axis support**: 3D spin axis from backspin + sidespin
   - Topspin (negative backspin) uses Rust path
   - High sidespin (any ratio) uses Rust path
   - Falls back to Python only for custom CD overrides

3. **Performance Results**
   | Metric | Before Rust | After Rust | Speedup |
   |--------|-------------|------------|---------|
   | Game (with wind) | ~30s | **6.2s** | **5x** |
   | Batted balls/sec | 4 | **1000+** | **250x** |
   | Pitch simulation | 22/sec | **158/sec** | **7x** |
   | Trajectory batch | 11,000/sec | 183,000/sec | 17x |

4. **Files Created/Modified**
   - `trajectory_rs/Cargo.toml`: Rust project config (PyO3 0.23, Rayon)
   - `trajectory_rs/pyproject.toml`: Python build config (maturin)
   - `trajectory_rs/src/lib.rs`: Full trajectory integrator (~500 LOC)
   - `batted_ball/trajectory.py`: Rust integration with wind + sidespin
   - `batted_ball/pitch.py`: Rust acceleration for pitch simulation

5. **Building the Rust Library**
   ```bash
   cd trajectory_rs
   maturin build --release
   pip install target/wheels/*.whl
   ```

**Impact**: Games now complete in ~6 seconds with full physics (wind, spin), validated with 7/7 physics tests passing.

### v1.2.0 - 2025-11-20 (Series Statistics & Fielding Realism)

**Major Feature Additions**: Multi-game statistics, OOTP-style metrics, ballpark system, fielding realism

1. **Series Statistics System** (`series_metrics.py` - 708 lines)
   - Comprehensive multi-game aggregation for batting, pitching, fielding
   - Advanced sabermetrics: wOBA, ISO, BABIP, HR/FB rate, OPS, wRC+
   - Contact quality tracking: exit velocity, launch angle, barrel %, hard hit %
   - **MLB Realism Benchmarks**: 10 metrics with pass/fail indicators (✓, ⚠️, 🚨)
     - Validates batting avg, BABIP, K%, BB%, ISO, HR/FB, exit velo, etc.
     - Larger sample sizes enable robust model validation
   - Run production analysis with totals, averages, ranges, std deviation
   - Pitching metrics: ERA, WHIP, K/9, BB/9, HR/9, K/BB ratio, pitch types
   - Quality starts tracking and innings-based statistics

2. **Simulation Metrics System** (`sim_metrics.py` - 2,460 lines)
   - **OOTP-style transparency** for debugging and model tuning
   - Pitch-level tracking: release mechanics, trajectory physics, command accuracy
   - Contact-level metrics: impact location, exit velocity, launch angle, spin
   - Play-level outcomes: fielding assignments, timing, catch probability
   - Debug verbosity levels: OFF, BASIC, DETAILED, EXHAUSTIVE
   - Expected vs actual outcome tracking for physics validation
   - Complete audit trail for every pitch, contact, and play

3. **Route Efficiency Analysis** (`route_efficiency.py` - 380 lines)
   - Fielder route quality metrics for airborne batted balls
   - Optimal vs actual distance traveled calculations
   - Route efficiency percentage (quality of path taken)
   - Required vs available speed analysis
   - Catch probability based on timing margins (MarginSec)
   - Multi-line diagnostic logging for game analysis

4. **Ballpark System** (`ballpark.py` - 330 lines)
   - MLB stadium-specific dimensions with fence distances and heights
   - Interpolation for smooth fence profile at any spray angle
   - Support for unique features: Green Monster, short porches, deep alleys
   - Foundation for park factors in batted ball outcomes
   - Hit classification based on fence interaction

5. **Fielding Realism Enhancements** (Pass #2)
   - **Route efficiency variance**: ±2% stochastic noise on fielder routes
   - **Reaction time jitter**: ~±50ms variance in first-step timing
   - **Jump quality modifiers**: Poor (-10%), subpar (-5%), normal (0%), quick (+2%)
   - **Catch probability floor**: 1.5% chance of misplay on routine catches (>0.95 prob)
   - **Positioning variability**: Fielders 1-3 steps (3-9 ft) off ideal position
   - Creates realistic bloop hits, diving misses, late breaks
   - Route efficiencies average 91-93% (down from 97-99%)

6. **New Documentation**
   - `SIM_METRICS_GUIDE.md` - Complete guide to simulation metrics system
   - `BALLPARK_HIT_CLASSIFICATION.md` - Hit outcomes and fence interactions
   - `STATCAST_METRICS_ANALYSIS.md` - Detailed Statcast validation
   - `STATCAST_PITCH_LEVEL_INTEGRATION.md` - Pitch-level data integration

**Impact**: Series-level analysis now provides robust MLB realism validation. OOTP-style metrics enable deep debugging. Fielding stochasticity creates more realistic outcome variance.

### v1.1.2 - 2025-11-19 (Angle-Dependent Spin Calibration)

**Major Calibration Improvement**: Line drive spin estimation refined based on Statcast data

1. **Angle-Dependent Spin Model v2**
   - Reduced line drive spin from 600-1200 rpm → 200-700 rpm
   - Based on physics: line drives result from contact above ball center → minimal backspin
   - Mean distance error reduced from +5.79% → +2.66% (now within 5% tolerance)
   - Line drive error reduced by 67% (+37 ft → +12 ft)
   - All 7 validation benchmarks still passing

2. **Updated Spin Estimation**
   - Line drives (<20°): 200-700 rpm (v2, reduced)
   - Transition zone (20-25°): 700-1200 rpm (new smooth transition)
   - Fly balls (25-35°): 1200-1950 rpm (unchanged, already accurate)
   - Pop-ups (>35°): 1950-2700 rpm (unchanged)

3. **New Files**:
   - `calibrate_with_spin.py` - Updated with v2 spin model
   - `calibrate_with_spin_synthetic.py` - Synthetic data testing (bypasses pybaseball issues)
   - `docs/ANGLE_DEPENDENT_SPIN_CALIBRATION.md` - Complete calibration documentation

4. **Calibration Results**:
   - Mean error: +19.41 ft (+5.79%) → +9.23 ft (+2.66%) ✓
   - Line drive error: +37.07 ft → +12.21 ft (67% improvement) ✓
   - Status: "Needs calibration" → "Good (within 5%)" ✓

**Impact**: Physics model now meets MLB accuracy standards for all batted ball types.

### v1.1.1 - 2025-11-19 (Reynolds Number Enhancement)

**Major Physics Improvement**: Velocity-dependent drag coefficient modeling

1. **Reynolds-Dependent Aerodynamics**
   - Implemented velocity-dependent drag coefficient based on Reynolds number
   - Reduces systematic distance errors from 6.13% to 1.80%
   - All 7 validation benchmarks still passing
   - Zero performance overhead (JIT-compiled)

2. **Statcast Calibration Module**
   - `batted_ball/statcast_calibration.py` - Fetch and compare real MLB data
   - `batted_ball/statcast_calibration_demo.py` - Demo with synthetic data
   - Automated calibration reports showing model accuracy

3. **Enhanced Documentation**
   - `docs/STATCAST_CALIBRATION_FINDINGS.md` - Detailed analysis
   - `docs/REYNOLDS_NUMBER_ENHANCEMENT.md` - Implementation guide
   - `examples/statcast_physics_calibration_example.py` - Usage examples

**Physics Constants Added**:
- `REYNOLDS_DRAG_ENABLED` - Feature flag (default: True)
- `RE_CRITICAL_LOW/HIGH` - Reynolds regime boundaries
- `CD_SUBCRITICAL_INCREASE` - Low-velocity drag adjustment
- `CD_SUPERCRITICAL_DECREASE` - High-velocity drag adjustment

### v1.1.0 - 2025-11-19 (MLB Database Integration)

1. **MLB Database System** - Complete integration with pybaseball for real player data
   - SQLite database for storing teams
   - Automatic stat conversion from MLB to game attributes
   - CLI tool (`manage_teams.py`) for database management
   - New `batted_ball/database/` package with 6 modules

2. **New Modules**:
   - `batted_ball/database/db_schema.py` - Database schema
   - `batted_ball/database/pybaseball_fetcher.py` - Fetch MLB data
   - `batted_ball/database/stats_converter.py` - Convert stats to attributes
   - `batted_ball/database/team_database.py` - CRUD operations
   - `batted_ball/database/team_loader.py` - Load teams for simulation
   - `batted_ball/hit_handler.py` - Hit outcome processing
   - `batted_ball/pybaseball_integration.py` - Public API for MLB integration

3. **New Documentation**:
   - `DATABASE_README.md` - Complete guide to database system
   - Updated examples for MLB team simulations

4. **Bug Fixes**:
   - Fixed runner speed calculation to use player's actual speed attribute
   - Fixed game log truncation in multi-game simulations
   - Improved fielding catch logic and timing

### Migration Notes
- Existing code remains fully backward compatible
- Database features are optional - `import batted_ball` still works without pybaseball
- To use MLB features: `pip install pybaseball`
- See `DATABASE_README.md` for migration guide
