# Version 2.0 Implementation Plan
**Baseball Physics Simulation Engine - MLB Realism Architecture Overhaul**

**Created**: 2025-11-20
**Status**: Planning Phase
**Goal**: Decouple K%, BB%, and HR/FB to achieve independent tuning without breaking other metrics

---

## Table of Contents
1. [Goals & Success Criteria](#goals--success-criteria)
2. [Current State (Baseline)](#current-state-baseline)
3. [Subsystem Map](#subsystem-map)
4. [V2 Decoupling Strategy](#v2-decoupling-strategy)
5. [Task Breakdown (Phases)](#task-breakdown-phases)
6. [Implementation Details](#implementation-details)
7. [Testing & Validation](#testing--validation)
8. [Risk Assessment](#risk-assessment)

---

## Goals & Success Criteria

### Target Metrics (MLB 2020s)
| Metric | Current | Target | Status |
|--------|---------|--------|--------|
| **K% (Strikeout Rate)** | 8.2% | 22-24% | 🚨 CRITICAL |
| **BB% (Walk Rate)** | 17.2% | 8-9% | 🚨 CRITICAL |
| **HR/FB (Home Run per Fly Ball)** | 6.3% | 12-15% | 🚨 CRITICAL |
| Hard Hit % | 40.3% | 35-45% | ✓ PASSING |
| Exit Velocity (avg) | 94 mph | 86-90 mph | ⚠️ CLOSE |
| ISO (Isolated Power) | 0.154 | 0.120-0.180 | ✓ PASSING |
| Batting Average | 0.232 | 0.230-0.270 | ✓ PASSING |
| BABIP | 0.248 | 0.260+ | ⚠️ CLOSE |
| Runs/Game | 4.3 | 3.8-5.2 | ✓ PASSING |
| Team ERA | 4.3 | 3.5-5.0 | ✓ PASSING |

### Success Criteria
1. **All 10 MLB benchmark metrics passing** (vs current 5/10)
2. **Independent tuning**: Adjust K% without affecting BB% or HR/FB
3. **Maintain existing passes**: Don't break Hard Hit %, ISO, BA, Runs/Game, ERA
4. **Realistic distributions**:
   - Swing% in-zone: 65-70%
   - Swing% out-of-zone (chase): 25-35%
   - Contact rate: 75-80%
   - Ground ball %: 43-47%
   - Line drive %: 20-24%
   - Fly ball %: 32-37%
   - Launch angle distribution: Realistic shape
5. **Player variation**: Model diverse player types (low-K contact hitters, high-K power sluggers, control vs power pitchers)

---

## Current State (Baseline)

### Pass 3 Baseline (5/10 Passing)
- **Collision Efficiency (q)**: 0.03 (sweet spot after extensive calibration)
- **Whiff Rates**: Base 0.20 for fastballs, 0.35 for breaking balls
- **Intentional Ball %**: ~10% on first pitch, ~45% with 2 strikes
- **Attack Angle**: ~7° average (fixed from 12°)
- **Launch Angle Distribution**: Ground ball 45%, Line drive 20%, Fly ball 35%

### Known Issues (Root Causes)
1. **K% Coupling**: Whiff probability dampened too much by barrel accuracy (double-dipping)
2. **BB% Coupling**: K% increases → longer at-bats → more walks (paradoxical)
3. **HR/FB Coupling**: Single parameter (q) controls both EV mean and EV tail; can't tune independently

### Files to Modify
- `batted_ball/at_bat.py` - Pitch intention, at-bat simulation
- `batted_ball/player.py` - Whiff calculation, swing decision
- `batted_ball/contact.py` - Collision physics
- `batted_ball/attributes.py` - Player attribute mappings
- `batted_ball/constants.py` - Physics constants
- `batted_ball/trajectory.py` - Ball flight physics
- `batted_ball/game_simulation.py` - Game loop

---

## Subsystem Map

### Subsystem 1: Pitching Physics & Command
**Responsibilities**: Pitch selection, target location, command error
**Primary Influence**: BB% (walk rate)
**Key Files**:
- `batted_ball/at_bat.py:402-441` - `determine_pitch_intention()`
- `batted_ball/player.py:180-243` - `get_command_sigma_inches()`
- `batted_ball/attributes.py:144-149` - Command attribute mapping

**Current Issues**:
- Too many intentional balls (10% first pitch, up to 45% with 2 strikes)
- Command error adds on top of intention → double-counting wildness
- No umpire variability on borderline calls

### Subsystem 2: Batter Decision System
**Responsibilities**: Swing/take decision, chase behavior, count-based approach
**Primary Influence**: BB% + K% (coupled)
**Key Files**:
- `batted_ball/player.py:630-710` - `decide_to_swing()`
- `batted_ball/player.py:656-665` - Zone discipline logic
- `batted_ball/player.py:696-704` - Count-based adjustments

**Current Issues**:
- Swing decisions affect both K% (via whiffs) and BB% (via pitch counts)
- No separation between "swing tendency" and "contact ability"
- Two-strike protection mode paradoxically extends at-bats → more walks

### Subsystem 3: Bat-Ball Collision
**Responsibilities**: Exit velocity, launch angle, spin
**Primary Influence**: HR/FB (via EV distribution)
**Key Files**:
- `batted_ball/contact.py:546-590` - Collision efficiency calculation
- `batted_ball/constants.py:244-265` - Collision efficiency constants
- `batted_ball/attributes.py:140-149` - Bat speed mapping

**Current Issues**:
- Single parameter (q) controls mean EV AND EV tail
- q=0.03: Good avg EV (94 mph), low HR/FB (6.3%)
- q=0.04: Good HR/FB (12.8%), too-high avg EV (96 mph)
- Can't independently tune hard-hit frequency vs HR frequency

### Subsystem 4: Batted Ball Flight
**Responsibilities**: Trajectory simulation, carry distance
**Primary Influence**: HR/FB (via carry model)
**Key Files**:
- `batted_ball/trajectory.py` - BattedBallSimulator
- `batted_ball/aerodynamics.py` - Drag and Magnus force
- `batted_ball/constants.py:234-301` - Drag coefficient, lift coefficient

**Current Issues**:
- Drag/lift calibrated for benchmarks but may underestimate carry on HR-type balls
- No independent "carry factor" to adjust HR distance vs general flight

### Subsystem 5: Contact & Whiff Model
**Responsibilities**: Contact vs miss, whiff probability
**Primary Influence**: K% (strikeout rate)
**Key Files**:
- `batted_ball/player.py:862-901` - `calculate_whiff_probability()`
- `batted_ball/at_bat.py:612-636` - Whiff check

**Current Issues**:
- Barrel accuracy used for BOTH whiff reduction AND contact quality (double-dipping)
- Elite hitters: 0.80× whiff multiplier (still too generous)
- Poor hitters: 1.6× whiff multiplier (not harsh enough)
- No separate "contact frequency" vs "contact quality" attributes

### Subsystem 6: Fielding & Baserunning
**Responsibilities**: Catch probability, outs on balls in play
**Secondary Influence**: BABIP, overall offense
**Key Files**:
- `batted_ball/fielding.py:84-139` - Fielder movement, catch logic
- `batted_ball/baserunning.py` - Runner advancement

**Current Issues**:
- Affects BABIP (currently 0.248 vs 0.260 target)
- Conservative catch success tuning → high hit rates
- Not a primary focus for v2 but may need minor adjustments

---

## V2 Decoupling Strategy

### Strategy 1: Decouple K% (Strikeout Rate)

#### Goal
Achieve ~22% K rate without increasing BB% or suppressing overall offense

#### Approach: Two-Stage Strikeout Model

**Stage 1: Pitch-by-Pitch (First 2 Strikes)**
- Maintain current whiff calculation for first 2 strikes
- Use realistic swing/take decisions
- Generate natural 2-strike counts

**Stage 2: Strikeout Resolution (After 2 Strikes)**
- NEW: Add "put-away probability" for 2-strike counts
- NEW: Model that some 2-strike battles end in K without requiring 3rd swinging strike
- NEW: Implements called strike 3 (~25% of Ks in MLB)
- NEW: Foul ball fatigue (each successive foul increases K probability)

#### Implementation Plan

**New Attributes**:
```python
class Hitter:
    VISION = rating  # NEW: Contact frequency (0-100k) - affects whiff
    POWER = rating   # RENAME: Barrel accuracy → affects EV/quality when contact made

class Pitcher:
    PUTAWAY_SKILL = rating  # NEW: Effectiveness at finishing hitters (0-100k)
```

**New Functions**:
```python
def maybe_strikeout_now(batter, pitcher, count, fouls_with_2_strikes):
    """
    Probabilistically resolve strikeout on 2-strike counts.
    Base probability ~10-15%, increases with:
    - Pitcher putaway_skill
    - Number of fouls with 2 strikes (fatigue)
    - Pitch type (breaking balls higher)
    Returns: (is_strikeout, strikeout_type)  # 'swinging' or 'looking'
    """
    pass

def calculate_whiff_probability_v2(batter, pitch):
    """
    Use VISION attribute instead of POWER/barrel_accuracy.
    Elite vision (85k+): 0.70× whiff multiplier
    Average vision (50k): 1.0× multiplier
    Poor vision (20k): 1.8× multiplier
    """
    pass
```

**Tuning Knobs**:
- `K_PUTAWAY_BASE_PROB` - Base probability of K resolution on 2-strike pitch (target: ~12%)
- `K_FOUL_FATIGUE_MULTIPLIER` - Increase per successive foul (target: +3% per foul)
- `K_LOOKING_PROBABILITY` - Fraction of Ks that are looking vs swinging (target: ~25%)

**Expected Outcome**:
- K% → 22% (from 8.2%)
- BB% → Independent (won't increase due to longer at-bats)
- Contact rate → Realistic (~78%)

---

### Strategy 2: Decouple BB% (Walk Rate)

#### Goal
Achieve ~8-9% BB rate without affecting K% or overall strike zone behavior

#### Approach: Pitcher Control Module + Umpire Model

**Component 1: Pitcher Control Module**
- Replace hardcoded "intentional ball" probabilities with dynamic control model
- Model pitch location as: `actual_location = target + systematic_error + random_error`
- Systematic error = f(control rating, situation, batter threat)
- Random error = Gaussian(0, command_sigma)

**Component 2: Umpire Call Variability**
- NEW: Probabilistic strike calls on borderline pitches (within 2" of zone edge)
- NEW: Catcher framing influence
- NEW: Tunable strike zone width

#### Implementation Plan

**New Classes**:
```python
class PitcherControlModule:
    def determine_zone_target_probability(pitcher, count, batter_threat_level):
        """
        Calculate probability pitch will be in zone based on:
        - Pitcher control rating
        - Count (3-ball: high zone %, 0-2: lower zone %)
        - Batter threat (dangerous hitter: nibble more)
        Returns zone probability (e.g., 0.65 = 65% zone rate)
        """
        pass

    def generate_pitch_location(pitcher, target, count):
        """
        Returns actual pitch location with error.
        Uses pitcher's COMMAND attribute for error distribution.
        """
        pass

class UmpireModel:
    def call_pitch(pitch_location, zone_bounds, framing_bonus=0):
        """
        Probabilistically call strike/ball on borderline pitches.
        - Pitches >2" outside zone: 100% ball
        - Pitches >2" inside zone: 100% strike
        - Pitches within 2" of edge: probabilistic based on distance + framing
        Returns 'strike' or 'ball'
        """
        pass
```

**New Attributes**:
```python
class Pitcher:
    CONTROL = rating  # EXISTING: Affects command_sigma
    NIBBLING_TENDENCY = rating  # NEW: How often pitcher pitches carefully (0-1)

class Catcher:
    FRAMING = rating  # NEW: Bonus to borderline strike probability (+0% to +5%)
```

**Tuning Knobs**:
- `BB_ZONE_TARGET_NEUTRAL` - Target zone % in neutral counts (tune to ~62%)
- `BB_ZONE_TARGET_AHEAD` - Target zone % when ahead in count (tune to ~70%)
- `BB_ZONE_TARGET_BEHIND` - Target zone % when behind in count (tune to ~55%)
- `BB_UMPIRE_BORDERLINE_BIAS` - Strikeagain call probability on edge pitches (tune to ~50%)
- `BB_FRAMING_BONUS_MAX` - Max framing bonus to strike probability (tune to ~5%)

**Expected Outcome**:
- BB% → 8-9% (from 17.2%)
- K% → Independent (umpire model can increase called K% if needed)
- Zone % → ~62-65% (MLB realistic)

---

### Strategy 3: Decouple HR/FB (Home Run Rate)

#### Goal
Achieve ~12-15% HR/FB while maintaining realistic average EV (~88 mph) and hard-hit % (~40%)

#### Approach: Two-Parameter Power Model

**Parameter A: Exit Velocity Distribution (Collision Efficiency)**
- Controls mean EV and hard-hit %
- Calibrate to: avg EV ~88 mph, hard-hit ~40%
- Current q=0.03 is close, minor adjustments only

**Parameter B: Home Run Trajectory Frequency**
- NEW: Controls how often high-EV balls become HR-trajectories
- Decouples HR frequency from average power
- Three sub-mechanisms:

**Mechanism B1: Launch Angle Bias for High-EV Contacts**
```python
# When high-EV contact is made (>95 mph), occasionally bias launch angle upward
if exit_velocity > 95:
    if random() < HR_LAUNCH_BIAS_PROBABILITY:
        launch_angle += random.normal(5, 2)  # +5° average boost
```

**Mechanism B2: Situational Swing Selection**
```python
# Batters choose swing type based on count
if count in [(2, 0), (3, 0), (3, 1)]:  # Hitter's counts
    swing_type = choose_swing_type(batter.approach)
    if swing_type == "power":
        launch_angle_target += 3  # More loft
        ev_variance += 5  # Higher variance
```

**Mechanism B3: Enhanced Carry Model**
```python
# Add "carry factor" to aerodynamics for HR-type balls
if launch_angle in [25, 35] and backspin_rpm > 1500:
    drag_coefficient *= (1 - HR_CARRY_BOOST)  # Reduce drag 3-5%
    # OR
    lift_coefficient *= (1 + HR_LIFT_BOOST)   # Increase Magnus lift
```

#### Implementation Plan

**New Attributes**:
```python
class Hitter:
    FLY_BALL_TENDENCY = rating  # NEW: Affects launch angle distribution (0-100k)
    APPROACH = enum  # NEW: 'contact', 'balanced', 'power' affects swing selection
```

**Modified Functions**:
```python
def calculate_collision_v2(batter, pitcher, pitch, swing_type='normal'):
    """
    Calculate exit velocity using existing collision efficiency (Parameter A).
    Then apply launch angle adjustment based on:
    - Swing type (normal, power, contact)
    - Batter fly_ball_tendency
    - Random variation
    Returns (exit_velocity, launch_angle, spin)
    """
    # Parameter A: EV (keep existing q=0.03)
    exit_velocity = compute_exit_velocity(q=0.03, ...)

    # Parameter B: Launch angle for HR
    base_launch_angle = compute_launch_angle(...)
    if exit_velocity > 95 and random() < HR_FAVORABLE_LAUNCH_PROB:
        launch_angle = base_launch_angle + random.normal(5, 2)
    else:
        launch_angle = base_launch_angle

    return exit_velocity, launch_angle, spin

def simulate_ball_flight_v2(exit_velocity, launch_angle, backspin, ...):
    """
    Enhanced flight model with HR carry adjustment.
    """
    # Check if this is a potential HR ball
    is_potential_hr = (25 <= launch_angle <= 35) and exit_velocity > 95

    if is_potential_hr:
        # Apply HR carry boost
        effective_drag = base_drag * (1 - HR_CARRY_BOOST)
        effective_lift = base_lift * (1 + HR_LIFT_BOOST)
    else:
        effective_drag = base_drag
        effective_lift = base_lift

    # Run trajectory simulation
    trajectory = integrate_trajectory(effective_drag, effective_lift, ...)
    return trajectory
```

**Tuning Knobs**:
- `HR_LAUNCH_BIAS_PROBABILITY` - Probability high-EV contacts get favorable launch angle (tune to ~0.15)
- `HR_LAUNCH_ANGLE_BOOST` - Average degrees added to launch angle for HR balls (tune to ~5°)
- `HR_CARRY_BOOST` - Drag reduction for potential HR balls (tune to ~0.03-0.05)
- `HR_LIFT_BOOST` - Magnus lift increase for high-backspin HR balls (tune to ~0.05-0.08)
- `POWER_SWING_FREQUENCY` - How often batters use power swing in hitter's counts (tune to ~0.30)

**Expected Outcome**:
- HR/FB → 12-15% (from 6.3%)
- Avg EV → 88 mph (minimal change from 94 mph via q adjustment)
- Hard-hit % → 40% (maintained)
- ISO → Maintained at ~0.150

---

## Task Breakdown (Phases)

### Phase 0: Baseline Metrics Harness ✅ PRIORITY 1
**Goal**: Establish reproducible measurement of all 10 MLB realism metrics

**Tasks**:
- [x] 0.1 Create `research/run_mlb_realism_baseline.py` script
  - Simulate NL Central 2025 for configurable number of games (default: 20 games)
  - Use existing teams and rosters
  - Collect detailed per-pitch, per-at-bat, per-game statistics

- [x] 0.2 Implement comprehensive metrics calculation
  - K% = strikeouts / plate appearances
  - BB% = walks / plate appearances
  - HR/FB = home runs / fly balls
  - All 10 MLB benchmarks plus supporting metrics
  - Per-team and league-wide aggregations

- [x] 0.3 Create output formats
  - JSON: `research/results/baseline_summary.json` (machine-readable)
  - Markdown: `research/results/baseline_summary.md` (human-readable report)
  - Include distributions (EV, LA, swing%, contact rate)

- [x] 0.4 Establish comparison framework
  - Store baseline results for comparison
  - Create diff tool to compare before/after calibrations
  - Version control for metrics history

**Deliverables**:
- `research/run_mlb_realism_baseline.py` - Main metrics harness
- `research/results/baseline_summary.json` - Current baseline (Pass 3)
- `research/results/baseline_summary.md` - Human-readable report
- Documentation of how to run and interpret results

**Acceptance Criteria**:
- Script runs in <5 minutes for 20 games
- All 10 MLB metrics computed correctly
- Baseline matches known Pass 3 results (5/10 passing)

---

### Phase 1: Metrics-First Refactor ⏳ PRIORITY 2
**Goal**: Instrument subsystems to understand where K%, BB%, HR/FB are generated

**Tasks**:
- [ ] 1.1 Add detailed logging to pitch intention logic
  - Track zone vs out-of-zone pitch targets by count
  - Track intentional ball % by situation
  - Track command error distribution
  - Output: `research/results/pitch_intention_analysis.json`

- [ ] 1.2 Add detailed logging to swing decision logic
  - Track swing% by zone (in-zone vs out-of-zone)
  - Track chase rate by distance from zone
  - Track swing% by count
  - Track swing% by pitch type
  - Output: `research/results/swing_decision_analysis.json`

- [ ] 1.3 Add detailed logging to whiff model
  - Track whiff rate by pitch type
  - Track whiff rate by pitcher stuff rating
  - Track whiff rate by batter contact ability
  - Track contact rate vs barrel accuracy correlation
  - Output: `research/results/whiff_analysis.json`

- [ ] 1.4 Add detailed logging to collision model
  - Track EV distribution by q value
  - Track launch angle distribution
  - Track correlation between EV and launch angle
  - Track barrel rate (optimal EV + LA combinations)
  - Output: `research/results/collision_analysis.json`

- [ ] 1.5 Add detailed logging to flight model
  - Track carry distance by EV/LA combination
  - Track HR vs fly-out classification
  - Track fence-clearing margin (how many feet over/under)
  - Output: `research/results/flight_analysis.json`

- [ ] 1.6 Create analysis notebook
  - Jupyter notebook to visualize all logged metrics
  - Identify which subsystems contribute most to K%, BB%, HR/FB
  - Validate root cause analysis from Full Architecture Map
  - Output: `research/v2_subsystem_analysis.ipynb`

**Deliverables**:
- Enhanced logging throughout all subsystems
- JSON outputs for each subsystem analysis
- Jupyter notebook with visualizations
- Confirmed understanding of metric sources

**Acceptance Criteria**:
- Can trace each K, BB, HR back to contributing factors
- Logging overhead <10% performance impact
- Visualizations clearly show metric distributions

---

### Phase 2: Introduce Decoupled Control Parameters 🎯 PRIORITY 3
**Goal**: Implement new attributes, modules, and tuning knobs per V2 design

#### Phase 2A: K% Decoupling (Strikeout Model)

**Tasks**:
- [ ] 2A.1 Add VISION attribute to Hitter class
  - Modify `batted_ball/attributes.py`
  - Add `VISION` to 0-100k scale
  - Add `get_contact_frequency_multiplier()` method
  - Map: Elite (85k+) → 0.70×, Average (50k) → 1.0×, Poor (20k) → 1.8×

- [ ] 2A.2 Add PUTAWAY_SKILL attribute to Pitcher class
  - Modify `batted_ball/player.py`
  - Add `PUTAWAY_SKILL` to 0-100k scale
  - Add `get_putaway_probability()` method

- [ ] 2A.3 Implement `calculate_whiff_probability_v2()`
  - Use VISION instead of barrel_accuracy
  - Remove double-dipping of barrel accuracy
  - Keep pitch type/velocity/movement adjustments
  - File: `batted_ball/player.py`

- [ ] 2A.4 Implement `maybe_strikeout_now()` function
  - Add 2-strike K resolution logic
  - Base probability ~12%, adjusted by:
    - Pitcher putaway_skill
    - Fouls with 2 strikes (fatigue)
    - Pitch type
  - Return strikeout type ('swinging', 'looking')
  - File: `batted_ball/at_bat.py`

- [ ] 2A.5 Add foul ball fatigue tracking
  - Track consecutive fouls with 2 strikes
  - Increase K probability +3% per successive foul
  - Cap at reasonable limit (e.g., 5 fouls max)

- [ ] 2A.6 Add called strike 3 logic
  - ~25% of Ks should be looking
  - Integrate with umpire model (Phase 2B)
  - Model borderline pitch called strike 3

- [ ] 2A.7 Add configuration constants
  - `K_PUTAWAY_BASE_PROB = 0.12`
  - `K_FOUL_FATIGUE_MULTIPLIER = 0.03`
  - `K_LOOKING_PROBABILITY = 0.25`
  - File: `batted_ball/constants.py`

**Deliverables**:
- VISION and PUTAWAY_SKILL attributes implemented
- New whiff calculation using VISION
- 2-strike K resolution logic
- Configuration constants in constants.py

---

#### Phase 2B: BB% Decoupling (Walk Model)

**Tasks**:
- [ ] 2B.1 Create PitcherControlModule class
  - New file: `batted_ball/pitcher_control.py`
  - `determine_zone_target_probability()` method
  - `generate_pitch_location()` method
  - Replace hardcoded intentions in `at_bat.py`

- [ ] 2B.2 Create UmpireModel class
  - New file: `batted_ball/umpire.py`
  - `call_pitch()` method for borderline strikes
  - Probabilistic strike/ball calls within 2" of zone edge
  - Consider catcher framing

- [ ] 2B.3 Add FRAMING attribute to Catcher class
  - Modify `batted_ball/player.py` or create `Catcher` class
  - Map to bonus probability (+0% to +5%)
  - File: `batted_ball/attributes.py`

- [ ] 2B.4 Add NIBBLING_TENDENCY to Pitcher class
  - Affects zone target probability by situation
  - Range: 0.0 (always aggressive) to 1.0 (always careful)

- [ ] 2B.5 Refactor pitch intention logic
  - Replace `determine_pitch_intention()` with PitcherControlModule
  - Remove hardcoded intentional ball %s
  - Use dynamic zone probability
  - File: `batted_ball/at_bat.py:402-441`

- [ ] 2B.6 Integrate umpire calls into at-bat loop
  - After pitch location determined, call UmpireModel
  - Use result for strike/ball determination
  - Track called strikes vs swinging strikes
  - File: `batted_ball/at_bat.py`

- [ ] 2B.7 Add configuration constants
  - `BB_ZONE_TARGET_NEUTRAL = 0.62`
  - `BB_ZONE_TARGET_AHEAD = 0.70`
  - `BB_ZONE_TARGET_BEHIND = 0.55`
  - `BB_UMPIRE_BORDERLINE_BIAS = 0.50`
  - `BB_FRAMING_BONUS_MAX = 0.05`
  - File: `batted_ball/constants.py`

**Deliverables**:
- PitcherControlModule class
- UmpireModel class
- FRAMING attribute for catchers
- Refactored pitch intention logic
- Configuration constants

---

#### Phase 2C: HR/FB Decoupling (Power Model)

**Tasks**:
- [ ] 2C.1 Add FLY_BALL_TENDENCY attribute to Hitter class
  - Affects launch angle distribution
  - Map: Low (20k) → -5° bias, Average (50k) → 0°, High (85k) → +5° bias
  - File: `batted_ball/attributes.py`

- [ ] 2C.2 Add APPROACH attribute to Hitter class
  - Enum: 'contact', 'balanced', 'power'
  - Affects swing type selection by count
  - 'power' approach → more fly balls in hitter's counts

- [ ] 2C.3 Implement situational swing selection
  - New function: `choose_swing_type(count, approach)`
  - Returns 'normal', 'power', 'contact'
  - Power swings more likely in hitter's counts (2-0, 3-0, 3-1)
  - File: `batted_ball/at_bat.py`

- [ ] 2C.4 Modify collision calculation for launch angle bias
  - Add parameter: `swing_type` to `calculate_collision()`
  - For high-EV contacts (>95 mph), apply HR launch bias
  - Probability-based boost to launch angle (+5° avg)
  - File: `batted_ball/contact.py`

- [ ] 2C.5 Implement enhanced carry model
  - Modify `simulate_ball_flight()` function
  - Detect potential HR balls (25-35° launch, 95+ mph EV)
  - Apply carry boost: reduce drag or increase lift
  - File: `batted_ball/trajectory.py`

- [ ] 2C.6 Add separate EV and HR tuning
  - Keep Parameter A (q=0.03 or adjust slightly for avg EV ~88)
  - Add Parameter B controls for HR frequency
  - Ensure independence via testing

- [ ] 2C.7 Add configuration constants
  - `HR_LAUNCH_BIAS_PROBABILITY = 0.15`
  - `HR_LAUNCH_ANGLE_BOOST = 5.0`  # degrees
  - `HR_CARRY_BOOST = 0.04`  # drag reduction
  - `HR_LIFT_BOOST = 0.06`  # Magnus lift increase
  - `POWER_SWING_FREQUENCY = 0.30`
  - File: `batted_ball/constants.py`

**Deliverables**:
- FLY_BALL_TENDENCY and APPROACH attributes
- Situational swing selection logic
- Enhanced collision calculation with launch angle bias
- Enhanced flight model with carry boost
- Configuration constants for HR tuning

---

### Phase 3: Tuning Loops 🔧 PRIORITY 4
**Goal**: Systematically tune each decoupled parameter to hit target metrics

#### Phase 3A: K% Tuning

**Tasks**:
- [ ] 3A.1 Create K% tuning script
  - File: `research/tune_k_rate.py`
  - Vary K_PUTAWAY_BASE_PROB from 0.08 to 0.16
  - Vary K_FOUL_FATIGUE_MULTIPLIER from 0.02 to 0.05
  - Vary VISION attribute distribution
  - Run 20-game sims for each configuration

- [ ] 3A.2 Establish independence of K% from BB%
  - For each K% config, verify BB% doesn't increase
  - Track pitches-per-PA to ensure no explosion
  - Target: K% ~22%, BB% stable at ~8-9%

- [ ] 3A.3 Verify contact rate distribution
  - Ensure contact rate ~78% (realistic)
  - Check swing% in-zone and out-of-zone still realistic
  - Verify whiff rate by pitch type matches MLB

- [ ] 3A.4 Document K% tuning results
  - Record each configuration tested
  - Plot K% vs tuning parameters
  - Identify optimal settings
  - File: `research/experiments/k_rate_tuning_results.md`

**Deliverables**:
- K% tuning script
- Optimal K% configuration (target: ~22%)
- Verified independence from BB%
- Tuning results documentation

---

#### Phase 3B: BB% Tuning

**Tasks**:
- [ ] 3B.1 Create BB% tuning script
  - File: `research/tune_bb_rate.py`
  - Vary BB_ZONE_TARGET_NEUTRAL from 0.58 to 0.68
  - Vary BB_UMPIRE_BORDERLINE_BIAS from 0.45 to 0.55
  - Vary BB_FRAMING_BONUS_MAX from 0.00 to 0.08
  - Run 20-game sims for each configuration

- [ ] 3B.2 Establish independence of BB% from K%
  - For each BB% config, verify K% remains ~22%
  - Track zone% to ensure realistic (62-65%)
  - Target: BB% ~8-9%, K% stable at ~22%

- [ ] 3B.3 Verify pitch location distributions
  - Check zone% by count matches MLB
  - Verify command error distribution realistic
  - Check called strike % on borderline pitches

- [ ] 3B.4 Document BB% tuning results
  - Record each configuration tested
  - Plot BB% vs tuning parameters
  - Identify optimal settings
  - File: `research/experiments/bb_rate_tuning_results.md`

**Deliverables**:
- BB% tuning script
- Optimal BB% configuration (target: ~8-9%)
- Verified independence from K%
- Tuning results documentation

---

#### Phase 3C: HR/FB Tuning

**Tasks**:
- [ ] 3C.1 Create HR/FB tuning script
  - File: `research/tune_hr_rate.py`
  - Vary HR_LAUNCH_BIAS_PROBABILITY from 0.10 to 0.25
  - Vary HR_CARRY_BOOST from 0.02 to 0.08
  - Vary FLY_BALL_TENDENCY distribution
  - Vary collision efficiency q from 0.025 to 0.035 (Parameter A)
  - Run 20-game sims for each configuration

- [ ] 3C.2 Establish independence of HR/FB from avg EV
  - For each HR/FB config, verify avg EV stays ~88 mph
  - Verify hard-hit% stays ~40%
  - Target: HR/FB ~12-15%, EV independent

- [ ] 3C.3 Verify EV distribution shape
  - Check EV distribution tail (95+ mph %)
  - Ensure barrel rate realistic
  - Verify ISO remains ~0.150

- [ ] 3C.4 Verify launch angle distributions
  - Check GB/LD/FB% stays realistic
  - Verify launch angle distribution shape
  - Ensure not too many pop-ups

- [ ] 3C.5 Document HR/FB tuning results
  - Record each configuration tested
  - Plot HR/FB vs tuning parameters
  - Identify optimal settings
  - File: `research/experiments/hr_rate_tuning_results.md`

**Deliverables**:
- HR/FB tuning script
- Optimal HR/FB configuration (target: ~12-15%)
- Verified independence from avg EV and hard-hit%
- Tuning results documentation

---

#### Phase 3D: Full Integration Tuning

**Tasks**:
- [ ] 3D.1 Run full 100-game simulation with all v2 features
  - Use optimal configs from Phases 3A, 3B, 3C
  - Measure all 10 MLB benchmarks
  - Track all supporting metrics

- [ ] 3D.2 Fine-tune interactions
  - If any metrics regressed, identify cause
  - Make small adjustments to maintain independence
  - Re-run simulations until all 10/10 passing

- [ ] 3D.3 Verify player variability
  - Simulate diverse player types:
    - Contact hitter (high VISION, low POWER, low FLY_BALL_TENDENCY)
    - Power slugger (low VISION, high POWER, high FLY_BALL_TENDENCY)
    - Control pitcher (high CONTROL, low VELOCITY, high PUTAWAY_SKILL)
    - Power pitcher (low CONTROL, high VELOCITY, high STUFF)
  - Verify each produces realistic stat lines

- [ ] 3D.4 Stress test edge cases
  - All max attributes team vs all min attributes team
  - Extreme pitcher (0 control) vs extreme hitter (0 vision)
  - Ensure no infinite loops or crashes

- [ ] 3D.5 Document final configuration
  - Record all tuned constants
  - Explain reasoning for each value
  - Provide guidance for future tuning
  - File: `research/v2_final_configuration.md`

**Deliverables**:
- 100-game validation simulation results
- All 10/10 MLB benchmarks passing
- Verified player type diversity
- Final configuration documentation

---

### Phase 4: Set Default Configuration and Document 📝 PRIORITY 5
**Goal**: Freeze v2.0 configuration, document usage, and provide user guidance

**Tasks**:
- [ ] 4.1 Create v2.0 configuration file
  - New file: `batted_ball/config_v2.py`
  - Contains all tuned constants
  - Separate sections for K%, BB%, HR/FB controls
  - Include comments explaining each parameter

- [ ] 4.2 Add configuration loading system
  - Ability to load v1 (legacy) or v2 configs
  - Environment variable or command-line flag to choose
  - Default to v2 for new simulations

- [ ] 4.3 Update CLAUDE.md
  - Add v2 architecture section
  - Explain decoupling mechanisms
  - Document new attributes (VISION, PUTAWAY_SKILL, etc.)
  - Provide tuning guidance

- [ ] 4.4 Create v2 user guide
  - File: `docs/V2_ARCHITECTURE_GUIDE.md`
  - Explain each decoupling mechanism
  - Provide examples of tuning K%, BB%, HR/FB independently
  - Include before/after comparisons

- [ ] 4.5 Create v2 tuning guide
  - File: `docs/V2_TUNING_GUIDE.md`
  - Step-by-step instructions for adjusting each metric
  - Explain which knobs to turn and expected effects
  - Include troubleshooting section

- [ ] 4.6 Update README.md
  - Add v2.0 release notes
  - Highlight 10/10 MLB benchmarks passing
  - Link to v2 architecture and tuning guides

- [ ] 4.7 Create example scripts
  - `examples/v2_demo_independent_tuning.py` - Shows K%, BB%, HR/FB tuning
  - `examples/v2_demo_player_types.py` - Shows diverse player types
  - `examples/v2_comparison_v1_vs_v2.py` - Compares v1 and v2 metrics

**Deliverables**:
- v2 configuration file and loading system
- Updated CLAUDE.md with v2 architecture
- V2 architecture guide
- V2 tuning guide
- Updated README.md
- Example scripts demonstrating v2 features

---

## Implementation Details

### New Files to Create
1. `batted_ball/pitcher_control.py` - PitcherControlModule class
2. `batted_ball/umpire.py` - UmpireModel class
3. `batted_ball/config_v2.py` - V2 configuration constants
4. `research/run_mlb_realism_baseline.py` - Baseline metrics harness
5. `research/tune_k_rate.py` - K% tuning script
6. `research/tune_bb_rate.py` - BB% tuning script
7. `research/tune_hr_rate.py` - HR/FB tuning script
8. `docs/V2_ARCHITECTURE_GUIDE.md` - User documentation
9. `docs/V2_TUNING_GUIDE.md` - Tuning documentation
10. `research/v2_subsystem_analysis.ipynb` - Analysis notebook

### Files to Modify
1. `batted_ball/attributes.py` - Add VISION, FLY_BALL_TENDENCY, APPROACH, PUTAWAY_SKILL, FRAMING
2. `batted_ball/player.py` - Modify whiff calculation, add new attribute methods
3. `batted_ball/at_bat.py` - Add 2-strike K resolution, refactor pitch intention, integrate umpire
4. `batted_ball/contact.py` - Add swing type parameter, launch angle bias for high EV
5. `batted_ball/trajectory.py` - Add carry boost for potential HR balls
6. `batted_ball/constants.py` - Add all v2 tuning constants
7. `batted_ball/game_simulation.py` - Minor updates for new attributes
8. `CLAUDE.md` - Document v2 architecture
9. `README.md` - Update with v2 release notes

### Constants to Add (batted_ball/constants.py)
```python
# ============================================================================
# V2.0 MLB Realism Controls
# ============================================================================

# --- K% (Strikeout Rate) Controls ---
K_PUTAWAY_BASE_PROB = 0.12  # Base probability of K on 2-strike pitch (tune: 0.08-0.16)
K_FOUL_FATIGUE_MULTIPLIER = 0.03  # K prob increase per foul with 2 strikes (tune: 0.02-0.05)
K_LOOKING_PROBABILITY = 0.25  # Fraction of Ks that are looking vs swinging
K_VISION_ELITE_MULTIPLIER = 0.70  # Whiff multiplier for elite vision (85k+)
K_VISION_AVERAGE_MULTIPLIER = 1.00  # Whiff multiplier for average vision (50k)
K_VISION_POOR_MULTIPLIER = 1.80  # Whiff multiplier for poor vision (20k)

# --- BB% (Walk Rate) Controls ---
BB_ZONE_TARGET_NEUTRAL = 0.62  # Target zone % in neutral counts (tune: 0.58-0.68)
BB_ZONE_TARGET_AHEAD = 0.70  # Target zone % when ahead in count (tune: 0.65-0.75)
BB_ZONE_TARGET_BEHIND = 0.55  # Target zone % when behind in count (tune: 0.50-0.60)
BB_UMPIRE_BORDERLINE_BIAS = 0.50  # Strike call probability on edge pitches (tune: 0.45-0.55)
BB_FRAMING_BONUS_MAX = 0.05  # Max catcher framing bonus to strike probability (tune: 0.00-0.08)
BB_BORDERLINE_DISTANCE_INCHES = 2.0  # Distance from zone edge for probabilistic calls

# --- HR/FB (Home Run Rate) Controls ---
HR_LAUNCH_BIAS_PROBABILITY = 0.15  # Probability high-EV gets favorable launch (tune: 0.10-0.25)
HR_LAUNCH_ANGLE_BOOST_DEG = 5.0  # Average degrees added for HR-favorable launch (tune: 3.0-7.0)
HR_LAUNCH_ANGLE_BOOST_SIGMA_DEG = 2.0  # Std dev of launch angle boost
HR_EV_THRESHOLD_MPH = 95.0  # Minimum EV for HR launch bias to apply
HR_CARRY_BOOST = 0.04  # Drag coefficient reduction for potential HR balls (tune: 0.02-0.08)
HR_LIFT_BOOST = 0.06  # Magnus lift coefficient increase for HR balls (tune: 0.03-0.10)
HR_OPTIMAL_LAUNCH_MIN_DEG = 25.0  # Min launch angle for HR carry boost
HR_OPTIMAL_LAUNCH_MAX_DEG = 35.0  # Max launch angle for HR carry boost
HR_BACKSPIN_THRESHOLD_RPM = 1500.0  # Min backspin for HR lift boost

# --- Power Swing Controls ---
POWER_SWING_FREQUENCY_HITTERS_COUNT = 0.30  # Power swing % in hitter's counts (2-0, 3-0, 3-1)
POWER_SWING_LA_BOOST_DEG = 3.0  # Launch angle increase for power swings
POWER_SWING_EV_VARIANCE_INCREASE = 5.0  # mph - EV variance increase for power swings

# --- Collision Efficiency (Parameter A) ---
COLLISION_EFFICIENCY_Q = 0.03  # Base collision efficiency (tune: 0.025-0.035 for avg EV ~88 mph)

# --- V2 Feature Flags ---
V2_STRIKEOUT_MODEL_ENABLED = True  # Enable 2-strike K resolution
V2_PITCHER_CONTROL_MODULE_ENABLED = True  # Enable dynamic zone targeting
V2_UMPIRE_MODEL_ENABLED = True  # Enable probabilistic borderline calls
V2_HR_MODEL_ENABLED = True  # Enable HR launch bias and carry boost
```

---

## Testing & Validation

### Unit Tests
- `tests/test_v2_strikeout_model.py` - Test K resolution logic
- `tests/test_v2_pitcher_control.py` - Test zone probability calculations
- `tests/test_v2_umpire.py` - Test borderline call logic
- `tests/test_v2_collision_enhanced.py` - Test launch angle bias
- `tests/test_v2_flight_carry.py` - Test HR carry boost

### Integration Tests
- `tests/test_v2_full_game.py` - Full 9-inning game simulation
- `tests/test_v2_season.py` - 162-game season simulation
- `tests/test_v2_independence.py` - Verify K%, BB%, HR/FB independence

### Validation Criteria
All 10 MLB benchmarks must pass:
1. ✓ K% = 22-24%
2. ✓ BB% = 8-9%
3. ✓ HR/FB = 12-15%
4. ✓ Hard Hit % = 35-45%
5. ✓ Exit Velocity = 86-90 mph
6. ✓ ISO = 0.120-0.180
7. ✓ Batting Average = 0.230-0.270
8. ✓ BABIP = 0.260+
9. ✓ Runs/Game = 3.8-5.2
10. ✓ Team ERA = 3.5-5.0

---

## Risk Assessment

### High Risk
1. **K% / BB% coupling not fully broken**
   - Mitigation: Extensive Phase 3 testing with independence verification
   - Fallback: Adjust put-away logic to shorten at-bats without increasing whiffs

2. **HR/FB increases break avg EV or hard-hit%**
   - Mitigation: Two-parameter model with separate EV and carry controls
   - Fallback: Reduce carry boost, increase launch angle bias compensation

3. **Performance degradation from new logic**
   - Mitigation: Profile code, optimize hot paths
   - Fallback: Add feature flags to disable v2 features if needed

### Medium Risk
1. **Player attribute distributions need rebalancing**
   - Mitigation: Phase 3D includes player type validation
   - Fallback: Adjust attribute mappings in attributes.py

2. **Umpire model affects game feel unexpectedly**
   - Mitigation: Tune borderline bias carefully in Phase 3B
   - Fallback: Reduce borderline zone from 2" to 1" for less variability

3. **Swing type selection AI too simplistic**
   - Mitigation: Start with count-based rules, iterate if needed
   - Fallback: Simplify to fixed probability rather than situational

### Low Risk
1. **Documentation becomes outdated**
   - Mitigation: Update docs as part of Phase 4
   - Fallback: Clear versioning in all documents

2. **Backward compatibility with v1**
   - Mitigation: Feature flags and config loading system
   - Fallback: Maintain v1 code path with V2_*_ENABLED flags

---

## Progress Tracking

### Phase Completion Status
- [x] Phase 0: Baseline Metrics Harness - COMPLETE
- [ ] Phase 1: Metrics-First Refactor - NOT STARTED
- [ ] Phase 2A: K% Decoupling - NOT STARTED
- [ ] Phase 2B: BB% Decoupling - NOT STARTED
- [ ] Phase 2C: HR/FB Decoupling - NOT STARTED
- [ ] Phase 3A: K% Tuning - NOT STARTED
- [ ] Phase 3B: BB% Tuning - NOT STARTED
- [ ] Phase 3C: HR/FB Tuning - NOT STARTED
- [ ] Phase 3D: Full Integration - NOT STARTED
- [ ] Phase 4: Documentation - NOT STARTED

### Current Focus
**Phase 0: Baseline Metrics Harness**

---

## Next Steps
1. ✅ Complete Phase 0: Create and run baseline metrics harness
2. ⏳ Begin Phase 1: Add detailed logging to all subsystems
3. 🎯 Once Phase 1 complete, begin Phase 2A (K% decoupling)

---

**Last Updated**: 2025-11-20
**Version**: 1.0
**Status**: Initial planning complete, ready to begin implementation
