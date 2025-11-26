# Simulation Metrics and Debug System Guide

**Version**: 1.2.0
**Last Updated**: 2025-11-19
**Status**: Production-Ready

---

## Table of Contents

1. [Overview](#overview)
2. [What's Included](#whats-included)
3. [Quick Start](#quick-start)
4. [Debug Levels](#debug-levels)
5. [Metrics Categories](#metrics-categories)
6. [Integration Guide](#integration-guide)
7. [Usage Examples](#usage-examples)
8. [CSV Export](#csv-export)
9. [Tuning and Calibration](#tuning-and-calibration)
10. [Comparison to MLB Statcast](#comparison-to-mlb-statcast)

---

## Overview

The Simulation Metrics System provides **OOTP-style transparency** with **Statcast-level detail** for the baseball physics simulation engine. This system reveals the internal decision-making, physics calculations, and probability models that drive every outcome in the sim.

### Why This Matters

- **Debug Physics**: See exactly how drag, Magnus force, and other physics affect outcomes
- **Tune Models**: Compare expected vs actual to find calibration issues
- **Validate Realism**: Match distributions to MLB Statcast data
- **Understand Decisions**: See why a batter swung, why a fielder failed, etc.
- **Export for Analysis**: Generate CSV files for R, Python, Excel analysis

### Philosophy

> **"If OOTP showed you this much detail, tuning would be 10x easier."**

Instead of guessing why your sim produces too many strikeouts or not enough home runs, you can now **see the exact probabilities and calculations** that led to each outcome.

---

## What's Included

The system tracks **8 categories** of metrics across **4 levels** of verbosity:

### A. Pitch-Level Tracking
- Release mechanics (velocity, spin, extension)
- Trajectory physics (break, movement, approach angle)
- Command accuracy (intended vs actual location)
- Expected probabilities (whiff%, swing%, contact%)
- Actual outcomes

### B. Swing Decision Tracking
- Internal decision inputs (zone rating, discipline, count leverage)
- Pitch deception (movement surprise, velocity difference)
- Swing probability distribution **before** RNG roll
- Contact quality probabilities (whiff/foul/weak/solid/barrel)
- Timing error and contact offset
- Actual outcome vs expected

### C. Batted Ball Flight Debugging
- Contact mechanics (bat speed, collision efficiency q)
- Launch conditions (EV, LA, spray angle, spin)
- Aerodynamic forces (drag, Magnus, wind effects)
- Landing coordinates and distance
- Expected vs actual distance (xHR probability)
- Hit classification (barrel, hard-hit, etc.)

### D. Fielding Interaction Debug
- Starting position and ball landing location
- Reaction time and route efficiency
- Sprint speed physics (acceleration, top speed)
- Catch probability (Statcast OAA-style)
- Timing margin (fielder ETA vs ball hang time)
- Error breakdown (too slow, drop, bad route, etc.)

### E. Baserunning Debug
- Runner attributes (sprint speed, acceleration)
- Starting conditions (lead, jump quality)
- Route efficiency through turns
- Risk assessment and success probability
- Outcome timing (runner vs ball arrival)

### F. Pitcher Fatigue Monitoring
- Current fatigue level (0-100%)
- Velocity, spin, and command degradation
- Times-through-order penalty
- High-leverage stress factors
- Expected performance changes

### G. Probabilistic Debug Output
- Expected stats (xBA, xSLG, xwOBA, xISO)
- Expected event probabilities (K%, BB%, HR%)
- Expected batted ball quality
- Actual vs expected comparison
- Performance delta (how much beat/missed expectations)

### H. Summary Statistics Aggregation
- Batted ball distributions (GB/LD/FB%, barrel%, hard-hit%)
- Pitching outcomes (CSW%, whiff%, swing%, contact%)
- Comparison to MLB averages
- Inning-by-inning and game-level aggregation

---

## Quick Start

### Installation

The metrics system is included in `batted_ball/sim_metrics.py`. No additional dependencies required beyond the standard simulation requirements.

### Basic Usage

```python
from batted_ball.sim_metrics import SimMetricsCollector, DebugLevel

# Create collector with desired verbosity
collector = SimMetricsCollector(debug_level=DebugLevel.DETAILED)

# During simulation, record metrics
collector.record_pitch(pitch_metrics)
collector.record_batted_ball(bb_metrics)
collector.record_fielding(field_metrics)

# After simulation, view summary
collector.print_summary()

# Export for analysis
collector.export_csv("game_20250119")
```

### Run the Demo

```bash
python examples/demo_sim_metrics.py
```

This comprehensive demo shows all 8 categories of metrics with example data.

---

## Debug Levels

The system supports 4 verbosity levels:

### Level 0: OFF
```python
collector = SimMetricsCollector(debug_level=DebugLevel.OFF)
```
- No debug output
- Minimal performance overhead
- Use for production simulations

### Level 1: BASIC
```python
collector = SimMetricsCollector(debug_level=DebugLevel.BASIC)
```
- Key outcomes only (result of each at-bat, final scores)
- Aggregated statistics
- Good for quick game monitoring

**Example Output:**
```
At-bat complete: home_run
   EV: 106.2 mph, LA: 28°, Distance: 425 ft
```

### Level 2: DETAILED
```python
collector = SimMetricsCollector(debug_level=DebugLevel.DETAILED)
```
- Every pitch, swing, batted ball
- Fielding plays with timing
- Baserunning decisions
- Perfect for debugging specific issues

**Example Output:**
```
📊 PITCH #3: slider (1-2)
   Plate: 84.2 mph @ (10.5", 16.0") [BALL]
   Break: V=-8.2", H=+5.1"
   Command error: 3.4"
   Expected: Swing=28%, Whiff=45%
   Outcome: take ✓
```

### Level 3: EXHAUSTIVE
```python
collector = SimMetricsCollector(debug_level=DebugLevel.EXHAUSTIVE)
```
- Internal probability distributions
- All physics calculations
- Expected vs actual for everything
- Use for deep model validation

**Example Output:**
```
🎯 SWING DECISION:
   Zone: chase (10.5", 16.0")
   Discipline: 65,000 rating
   Deception: -3.2 mph, +2.5" break surprise
   Probabilities:
      Swing: 28%  Take: 72%  Chase: 28%
   If swung, expected:
      Whiff: 45%  Foul: 25%  Weak: 20%
      Fair: 8%    Solid: 2%   Barrel: 0%
   Decision: TAKE (correct given probabilities)
```

---

## Metrics Categories

### Pitch Metrics (`PitchMetrics`)

Tracks every aspect of a single pitch:

```python
pitch = PitchMetrics(
    sequence_index=1,
    pitch_type="fastball",
    count_before=(0, 0),

    # Release
    release_point=(54.5, 2.0, 6.5),  # x, y, z in feet
    release_velocity_mph=95.2,
    release_extension_ft=6.5,

    # Spin
    spin_rpm=2250,
    spin_axis_deg=(175, 12),  # azimuth, elevation
    spin_efficiency=0.92,

    # At plate
    plate_velocity_mph=86.3,
    plate_location=(2.5, 32.0),  # h, v in inches
    vertical_approach_angle_deg=-5.8,

    # Movement
    vertical_break_inches=16.2,
    horizontal_break_inches=-2.1,

    # Command
    target_location=(0.0, 30.0),
    command_error=(2.5, 2.0),
    command_error_magnitude=3.2,

    # Probabilities
    expected_whiff_prob=0.15,
    expected_swing_prob=0.65,

    # Outcome
    batter_swung=True,
    pitch_outcome="contact",
    is_strike=True,
)
```

**Key Insights:**
- **Command Error**: How far from target (elite < 2", average ~4", poor > 6")
- **Perceived Velocity**: Release velo + extension boost (~1 mph per foot)
- **Approach Angle**: Typical fastball -4° to -6°, curve -8° to -12°

### Swing Decision Metrics (`SwingDecisionMetrics`)

Reveals the internal logic behind swing decisions:

```python
swing = SwingDecisionMetrics(
    pitch_zone_rating="chase",  # in_zone, edge, chase, waste
    pitch_location=(10.5, 16.0),
    pitch_velocity_mph=84.2,
    pitch_type="slider",
    batter_discipline_rating=65000,
    count=(2, 1),  # Hitter's count

    # Deception
    pitch_movement_surprise=2.5,  # Broke 2.5" more than expected
    velocity_deception=-3.2,  # 3 mph slower

    # Decision probabilities
    swing_probability=0.28,
    chase_probability=0.28,

    # If swung, expected outcomes
    expected_whiff_pct=0.45,
    expected_barrel_pct=0.0,

    # Actual
    swung=False,  # Good take!
)
```

**Tuning Use:**
- If `swing_probability` doesn't match MLB swing rates (~47%), adjust discipline model
- If `expected_whiff_pct` too high/low, recalibrate contact quality formulas

### Batted Ball Metrics (`BattedBallMetrics`)

Complete flight physics transparency:

```python
bb = BattedBallMetrics(
    # Contact
    bat_speed_mph=72.5,
    pitch_speed_mph=93.1,
    collision_efficiency_q=0.21,

    # Launch
    exit_velocity_mph=103.2,
    launch_angle_deg=28.0,
    spray_angle_deg=-12.0,
    backspin_rpm=1850,
    sidespin_rpm=-320,

    # Result
    distance_ft=408.0,
    hang_time_sec=5.2,
    apex_height_ft=102.0,

    # Physics breakdown
    magnus_force_contribution_ft=42.0,  # Backspin added 42 ft
    drag_force_loss_ft=-58.0,  # Drag reduced 58 ft
    wind_effect_ft=-12.0,  # Headwind cost 12 ft

    # Expected
    expected_distance_ft=415.0,
    expected_hr_probability=0.82,
    is_home_run=True,
)
```

**Key Insights:**
- **Collision Efficiency (q)**: Typical 0.18-0.24 (wood), 0.24-0.25 (BBCOR)
- **Magnus Contribution**: Backspin typically adds 30-60 ft
- **Drag Loss**: Typically reduces distance by 50-100 ft
- **Barrel**: EV ≥ 98 mph + LA 26-30° (MLB standard)

### Fielding Metrics (`FieldingMetrics`)

Track every defensive play:

```python
field = FieldingMetrics(
    fielder_name="Byron Buxton",
    fielder_position="CF",

    # Position
    starting_position=(0.0, 380.0),
    ball_landing_position=(-45.0, 402.0, 0.0),

    # Movement
    reaction_time_ms=185,  # Elite
    distance_to_ball_ft=48.5,
    route_efficiency_pct=96.5,  # Nearly optimal

    # Speed
    top_sprint_speed_fps=31.2,  # Elite (30+ = elite)
    actual_avg_speed_fps=29.8,

    # Timing
    ball_hang_time_sec=5.2,
    fielder_eta_sec=4.95,
    time_margin_sec=-0.25,  # 0.25 sec early

    # Difficulty
    opportunity_difficulty=72.0,  # 0-100 scale
    expected_catch_probability=0.48,

    # Outcome
    catch_successful=True,
)
```

**Statcast Comparison:**
- **Sprint Speed**: MLB average ~27 ft/s, elite >30 ft/s
- **Reaction Time**: Elite <200 ms, average ~300 ms, poor >400 ms
- **OAA Calculation**: `1.0 - expected_catch_probability` if successful

### Expected Outcome Metrics (`ExpectedOutcomeMetrics`)

Critical for validation:

```python
expected = ExpectedOutcomeMetrics(
    pitcher_name="Average Joe",
    batter_name="Mike Trout",
    count=(2, 1),

    # Expected
    xBA=0.312,
    xSLG=0.542,
    xwOBA=0.401,
    expected_hr_prob=0.08,
    expected_exit_velocity=94.5,

    # Actual
    actual_outcome="home_run",
    actual_exit_velocity=106.2,
    actual_distance=425.0,
)

expected.calculate_delta()
# Performance delta: +1.599 (beat expectations significantly)
# Outcome vs expected: "much_better"
```

**Validation:**
- Over 1000+ PAs, `xBA` should converge to actual BA
- Large delta indicates either luck or model miscalibration
- Use to identify which matchups are over/underperforming

---

## Integration Guide

### Step 1: Create Collector

In your game simulation initialization:

```python
from batted_ball.sim_metrics import SimMetricsCollector, DebugLevel

class GameSimulator:
    def __init__(self, ..., debug_level=DebugLevel.OFF):
        self.metrics = SimMetricsCollector(debug_level=debug_level)
```

### Step 2: Record Metrics During Simulation

#### In `at_bat.py` - Pitch Recording

```python
def simulate_pitch(self, ...):
    # ... existing pitch simulation ...

    if self.metrics.enabled:
        pitch_metrics = PitchMetrics(
            sequence_index=len(self.pitches) + 1,
            pitch_type=pitch_type,
            count_before=(balls, strikes),
            release_velocity_mph=velocity,
            plate_velocity_mph=result.plate_speed,
            plate_location=result.plate_location,
            # ... fill in all fields ...
        )
        self.metrics.record_pitch(pitch_metrics)

    return pitch_data
```

#### In `at_bat.py` - Batted Ball Recording

```python
def simulate_contact(self, ...):
    # ... existing contact simulation ...

    if self.metrics.enabled:
        bb_metrics = BattedBallMetrics(
            bat_speed_mph=bat_speed,
            pitch_speed_mph=pitch_velocity,
            exit_velocity_mph=collision_result['exit_velocity'],
            # ... fill in all fields ...
        )
        self.metrics.record_batted_ball(bb_metrics)

    return contact_result
```

#### In `fielding.py` - Fielding Recording

```python
def simulate_fielding_play(self, ...):
    # ... existing fielding simulation ...

    if self.metrics.enabled:
        field_metrics = FieldingMetrics(
            fielder_name=fielder.name,
            fielder_position=fielder.position,
            distance_to_ball_ft=distance,
            expected_catch_probability=catch_prob,
            catch_successful=success,
            # ... fill in all fields ...
        )
        self.metrics.record_fielding(field_metrics)

    return fielding_result
```

### Step 3: Generate Output

After simulation:

```python
# Print to console
collector.print_summary()

# Export to CSV
collector.export_csv("game_data_20250119")
# Creates: game_data_20250119_pitches.csv
#          game_data_20250119_batted_balls.csv
```

---

## Usage Examples

### Example 1: Debug Why Strikeout Rate is Too High

```python
collector = SimMetricsCollector(debug_level=DebugLevel.DETAILED)

# Run simulations...

# After 100 games
k_rate = strikeouts / plate_appearances

if k_rate > 0.25:  # Too high
    # Check swing decisions
    avg_whiff_prob = np.mean([s.expected_whiff_pct
                               for s in collector.swing_metrics
                               if s.swung])

    print(f"Average expected whiff%: {avg_whiff_prob:.1%}")
    # If this is reasonable (~25%), problem is in swing probability
    # If this is too high (>30%), problem is in contact quality model
```

### Example 2: Tune Home Run Distance

```python
collector = SimMetricsCollector(debug_level=DebugLevel.EXHAUSTIVE)

# Simulate many home runs
for bb in collector.batted_ball_metrics:
    if bb.is_home_run:
        print(f"Distance: {bb.distance_ft:.0f} ft")
        print(f"  Magnus: +{bb.magnus_force_contribution_ft:.0f} ft")
        print(f"  Drag: {bb.drag_force_loss_ft:.0f} ft")
        print(f"  Expected: {bb.expected_distance_ft:.0f} ft")
        print()

# If all HRs are 30 ft short, increase backspin or reduce drag
```

### Example 3: Validate Fielding Catch Probabilities

```python
# Group by difficulty bins
bins = [(0, 30), (30, 70), (70, 95), (95, 100)]

for low, high in bins:
    plays = [f for f in collector.fielding_metrics
             if low <= f.opportunity_difficulty < high]

    if plays:
        success_rate = sum(f.catch_successful for f in plays) / len(plays)
        avg_exp = np.mean([f.expected_catch_probability for f in plays])

        print(f"Difficulty {low}-{high}: {success_rate:.1%} success")
        print(f"  Expected: {avg_exp:.1%}")
        print(f"  Delta: {success_rate - avg_exp:+.1%}")
```

---

## CSV Export

The `export_csv()` method generates detailed CSV files for external analysis:

### Pitch CSV Columns

```
sequence, type, release_velo, plate_velo, spin_rpm,
h_location, v_location, v_break, h_break,
command_error, outcome, swung
```

### Batted Ball CSV Columns

```
ev, la, spray, distance, hang_time,
backspin, sidespin, hit_type, hard_hit, barrel
```

### Analysis in R

```r
library(tidyverse)

pitches <- read_csv("game_pitches.csv")
batted_balls <- read_csv("game_batted_balls.csv")

# Whiff rate by pitch type
pitches %>%
  filter(swung == TRUE) %>%
  group_by(type) %>%
  summarize(whiff_rate = mean(outcome == "swinging_strike"))

# Launch angle distribution
ggplot(batted_balls, aes(x = la)) +
  geom_histogram(binwidth = 5) +
  labs(title = "Launch Angle Distribution",
       x = "Launch Angle (degrees)")
```

---

## Tuning and Calibration

### MLB Targets

Use these benchmarks to validate your sim:

**Batted Ball Distribution:**
- Ground balls: 44%
- Line drives: 21%
- Fly balls: 35%
- Barrels: 8%
- Hard-hit: 38%

**Pitching Outcomes:**
- CSW% (Called Strikes + Whiffs): 28%
- Whiff%: 25%
- Swing%: 47%
- Contact%: 75%

**Expected Stats:**
- League average xBA: .245
- League average xSLG: .420
- League average xwOBA: .320

### Calibration Workflow

1. **Run 100+ games** with `DebugLevel.BASIC`
2. **Export aggregated statistics**
3. **Compare to MLB targets** (see comparison functions in metrics)
4. **Identify discrepancies** (e.g., GB% too low)
5. **Adjust physics constants** (e.g., increase bat path angle variance)
6. **Re-run and validate**

---

## Comparison to MLB Statcast

This system provides **equivalent** metrics to Statcast:

| Statcast Metric | Sim Metric | Location |
|-----------------|------------|----------|
| Exit Velocity | `exit_velocity_mph` | BattedBallMetrics |
| Launch Angle | `launch_angle_deg` | BattedBallMetrics |
| Barrel | `barrel` (bool) | BattedBallMetrics |
| Hard-Hit% | `hard_hit` (bool) | BattedBallMetrics |
| Sprint Speed | `top_sprint_speed_fps` | FieldingMetrics |
| OAA (Outs Above Avg) | Calc from `expected_catch_probability` | FieldingMetrics |
| CSW% | Calc in `PitchingOutcomes` | PitchingOutcomes |
| xBA | `xBA` | ExpectedOutcomeMetrics |
| xwOBA | `xwOBA` | ExpectedOutcomeMetrics |

---

## Performance Considerations

- **Level 0 (OFF)**: <1% overhead
- **Level 1 (BASIC)**: ~2% overhead
- **Level 2 (DETAILED)**: ~5% overhead (print statements)
- **Level 3 (EXHAUSTIVE)**: ~10% overhead (extensive printing)

**Recommendation**: Use Level 0 for batch simulations, Level 2 for debugging.

---

## Future Enhancements

Potential additions for v1.3.0:

1. **Real-time dashboards** (web interface showing metrics during sim)
2. **Automated regression testing** (compare metrics across versions)
3. **Machine learning integration** (train xStats models on sim data)
4. **Play-by-play export** (JSON format for replay systems)
5. **Hot zones visualization** (spray charts, pitch location heat maps)

---

## Support and Feedback

For questions, issues, or feature requests:
- Check `examples/demo_sim_metrics.py` for working examples
- Review `batted_ball/sim_metrics.py` for data structure definitions
- See `CLAUDE.md` for integration guidance

---

**Version**: 1.2.0
**Last Updated**: 2025-11-19
**Status**: Production-Ready ✓
