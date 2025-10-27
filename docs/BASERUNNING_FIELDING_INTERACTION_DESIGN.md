# Baserunning-Fielding Interaction System Design

## Overview
This document outlines the comprehensive design for modeling realistic baserunning and fielding interactions in baseball, including force plays, double plays, throw timing, and runner advancement decisions.

## Current State Problems

### High Scoring Issues
- **Current**: Runs/9 = 13.5 (should be ~9.0)
- **Root cause**: Overly aggressive baserunning
  - All runners score on doubles/triples (unrealistic)
  - Runner on 3rd always scores on singles (should sometimes hold)
  - No force plays or double plays
  - No throw timing simulation

### Simplified Baserunning Logic (Current)
```python
# Current implementation in play_simulation.py line 783-796
if result.outcome == PlayOutcome.SINGLE:
    if base == "third":
        result.runs_scored += 1  # ALWAYS scores - too aggressive!
elif result.outcome in [PlayOutcome.DOUBLE, PlayOutcome.TRIPLE]:
    # Everyone scores on doubles/triples - WAY too aggressive!
    result.runs_scored += 1
```

## Design Requirements

### 1. Force Play Detection
**Definition**: Runner MUST advance when forced by batter-runner.

**Implementation**:
```python
def detect_force_situation(runners: Dict[str, BaseRunner], batter_ran: bool) -> Dict[str, bool]:
    """
    Determine which runners are forced to advance.
    
    Force scenarios:
    - Runner on 1st, batter runs → forced to 2nd
    - Runners on 1st and 2nd, batter runs → both forced
    - Runner on 3rd only → NOT forced (can stay)
    
    Returns:
        Dict mapping base → is_forced (bool)
    """
    forces = {}
    
    if not batter_ran:
        return forces  # No forces if batter didn't run
    
    # Runner on first is ALWAYS forced when batter runs
    if "first" in runners:
        forces["first"] = True
        
        # If runner on second, they're forced too
        if "second" in runners:
            forces["second"] = True
            
            # If runner on third, they're forced too
            if "third" in runners:
                forces["third"] = True
    
    return forces
```

### 2. Throw Physics

**Key Parameters**:
- Arm strength: 70-95 mph (infielders ~85 mph, outfielders vary)
- Transfer time: 0.4-0.8 seconds (receive ball → release throw)
- Throw accuracy: affects whether throw is on-target
- Arc trajectory: throws have slight arc, affecting time

**Implementation**:
```python
class ThrowResult:
    """Result of a throw from fielder to base."""
    def __init__(self, 
                 from_position: FieldPosition,
                 to_base: str,
                 throw_velocity_mph: float,
                 transfer_time: float,
                 flight_time: float,
                 arrival_time: float,  # Total time from fielding ball
                 accuracy: float,  # 0-1, probability of good throw
                 on_target: bool):
        self.from_position = from_position
        self.to_base = to_base
        self.throw_velocity_mph = throw_velocity_mph
        self.transfer_time = transfer_time
        self.flight_time = flight_time
        self.arrival_time = arrival_time
        self.accuracy = accuracy
        self.on_target = on_target


def simulate_throw(fielder: Fielder, 
                   from_position: FieldPosition,
                   to_base: str,
                   field_layout: FieldLayout) -> ThrowResult:
    """
    Simulate a throw from fielder to base.
    
    Physics:
    1. Transfer time: receive ball → release (0.4-0.8s based on attributes)
    2. Throw velocity: 70-95 mph based on arm strength
    3. Distance: calculate from field position to base
    4. Flight time: distance / velocity (with arc adjustment)
    5. Accuracy: probability throw is on-target (catchable immediately)
    
    Returns:
        ThrowResult with timing and accuracy
    """
    # Get fielder attributes
    if fielder.attributes_v2:
        arm_strength = fielder.attributes_v2.get_arm_strength_mph()  # 70-95 mph
        transfer_time = fielder.attributes_v2.get_transfer_time_sec()  # 0.4-0.8s
        accuracy = fielder.attributes_v2.get_arm_accuracy_prob()  # 0.85-0.98
    else:
        arm_strength = 82.0  # Average
        transfer_time = 0.6
        accuracy = 0.90
    
    # Calculate distance
    base_position = field_layout.get_base_position(to_base)
    distance_ft = from_position.horizontal_distance_to(base_position)
    
    # Flight time with arc adjustment (throws have slight upward arc)
    # Arc adds ~5-10% to straight-line time
    straight_time = (distance_ft / (arm_strength * 1.467))  # mph to ft/s
    flight_time = straight_time * 1.07  # 7% arc penalty
    
    # Total time
    total_time = transfer_time + flight_time
    
    # Roll for accuracy
    on_target = np.random.random() < accuracy
    
    # Bad throw adds 0.5-1.0s for receiving fielder to handle
    if not on_target:
        total_time += np.random.uniform(0.5, 1.0)
    
    return ThrowResult(
        from_position=from_position,
        to_base=to_base,
        throw_velocity_mph=arm_strength,
        transfer_time=transfer_time,
        flight_time=flight_time,
        arrival_time=total_time,
        accuracy=accuracy,
        on_target=on_target
    )
```

### 3. Double Play Mechanics

**Common Double Play Types**:
- **6-4-3**: Shortstop → 2nd base → 1st base
- **4-6-3**: 2nd baseman → SS at 2nd → 1st base  
- **5-4-3**: 3rd baseman → 2nd base → 1st base
- **3-6-3**: 1st baseman → SS at 2nd → back to 1st

**Requirements for Double Play**:
1. Ground ball (not fly ball or line drive)
2. Runner on first base (forced to second)
3. Less than 2 outs
4. Ball fielded cleanly with sufficient time

**Timing Analysis**:
```
Example: 6-4-3 double play
1. SS fields grounder at position (40, 150) 
2. Time to field: 1.2s (ball travel + fielder movement)
3. Runner on first starts running immediately (0.0s reaction)
4. Runner time to 2nd base: 3.5s (90 ft in 3.5s for average runner)

Throw #1: SS → 2nd base
- Distance: ~50 ft
- Transfer: 0.5s
- Throw flight: 0.4s (85 mph throw)
- Total: 1.2s + 0.5s + 0.4s = 2.1s
- Runner arrival: 3.5s
- TIME MARGIN: 3.5 - 2.1 = 1.4s → FORCE OUT at 2nd ✓

Throw #2: 2nd base → 1st base  
- Batter-runner starts: 0.0s
- Batter time to 1st: 4.3s (right-handed batter)
- 2nd baseman receives: 2.1s
- Transfer: 0.4s
- Throw flight: 0.5s (127 ft at 85 mph)
- Total: 2.1s + 0.4s + 0.5s = 3.0s
- Batter arrival: 4.3s
- TIME MARGIN: 4.3 - 3.0 = 1.3s → OUT at 1st ✓

Result: DOUBLE PLAY (2 outs)
```

**Implementation**:
```python
def attempt_double_play(fielding_result: FieldingResult,
                       runners: Dict[str, BaseRunner],
                       batter_runner: BaseRunner,
                       field_layout: FieldLayout,
                       fielders: List[Fielder]) -> DoublePlayResult:
    """
    Attempt a ground ball double play.
    
    Requirements:
    - Ground ball
    - Runner on first (forced to second)
    - Less than 2 outs
    - Fielded cleanly
    
    Returns:
        DoublePlayResult with outcomes for each base
    """
    # Check requirements
    if not fielding_result.is_ground_ball:
        return DoublePlayResult(False, "Not a ground ball")
    
    if "first" not in runners:
        return DoublePlayResult(False, "No runner on first")
    
    # Identify pivot fielder (usually SS or 2B depending on ball location)
    pivot_base = "second"
    pivot_fielder = identify_pivot_fielder(fielding_result.ball_position, fielders)
    
    # Simulate throw #1: Fielding fielder → pivot base
    throw1 = simulate_throw(
        fielding_result.fielder,
        fielding_result.ball_position,
        pivot_base,
        field_layout
    )
    
    # Calculate runner timing to pivot base
    runner_on_first = runners["first"]
    runner_time_to_second = runner_on_first.calculate_time_to_base("first", "second")
    
    # Race #1: Runner vs throw to second
    runner_arrival_pivot = fielding_result.time + runner_time_to_second
    throw_arrival_pivot = fielding_result.time + throw1.arrival_time
    
    if runner_arrival_pivot < throw_arrival_pivot:
        # Runner beats throw - no double play possible
        return DoublePlayResult(False, "Runner beat throw to second")
    
    # Force out at second! Now attempt throw to first
    throw2 = simulate_throw(
        pivot_fielder,
        field_layout.get_base_position("second"),
        "first",
        field_layout
    )
    
    # Calculate batter-runner timing to first
    batter_time_to_first = batter_runner.calculate_time_to_base("home", "first")
    
    # Race #2: Batter-runner vs relay throw to first
    batter_arrival_first = fielding_result.time + batter_time_to_first
    throw_arrival_first = throw_arrival_pivot + throw2.arrival_time
    
    if batter_arrival_first < throw_arrival_first - 0.1:  # Need clear out
        # Batter beats throw - only one out
        return DoublePlayResult(
            True, 
            "Double play attempted, only got force out at second",
            outs_made=1,
            out_locations=["second"]
        )
    
    # Double play completed!
    return DoublePlayResult(
        True,
        "Double play! 6-4-3",
        outs_made=2,
        out_locations=["second", "first"]
    )
```

### 4. Runner Advancement Decision Logic

**Current Problem**: Runners advance deterministically without considering:
- Ball location (deep fly ball vs shallow)
- Number of outs
- Runner speed
- Game situation

**Decision Framework**:

```python
class AdvancementDecision:
    """Decision for runner to advance or hold."""
    def __init__(self, 
                 should_advance: bool,
                 target_base: str,
                 confidence: float,  # 0-1, how certain decision is
                 reasoning: str):
        self.should_advance = should_advance
        self.target_base = target_base
        self.confidence = confidence
        self.reasoning = reasoning


def decide_runner_advancement(runner: BaseRunner,
                              current_base: str,
                              ball_location: FieldPosition,
                              ball_speed: float,  # Speed when fielded
                              hit_type: PlayOutcome,
                              num_outs: int,
                              runners: Dict[str, BaseRunner],
                              field_layout: FieldLayout) -> AdvancementDecision:
    """
    Decide whether runner should advance and how far.
    
    Factors:
    1. Force situation (must run if forced)
    2. Number of outs (2 outs = run on contact)
    3. Ball location (outfield depth, arm strength of fielder)
    4. Runner speed
    5. Base running IQ (smart runners make better decisions)
    
    Returns:
        AdvancementDecision
    """
    # Check if forced to run
    force_situation = detect_force_situation(runners, batter_ran=True)
    if current_base in force_situation and force_situation[current_base]:
        return AdvancementDecision(
            True, 
            advance_one_base(current_base),
            1.0,
            "Forced to advance"
        )
    
    # With 2 outs, runners run on contact
    if num_outs == 2:
        return AdvancementDecision(
            True,
            advance_bases_on_hit(current_base, hit_type),
            0.95,
            "2 outs, running on contact"
        )
    
    # Calculate if runner can advance safely
    if hit_type == PlayOutcome.SINGLE:
        return decide_single_advancement(
            runner, current_base, ball_location, field_layout
        )
    elif hit_type == PlayOutcome.DOUBLE:
        return decide_double_advancement(
            runner, current_base, ball_location, field_layout
        )
    elif hit_type == PlayOutcome.FLY_OUT:
        return decide_tag_up(
            runner, current_base, ball_location, num_outs, field_layout
        )


def decide_single_advancement(runner: BaseRunner,
                             current_base: str,
                             ball_location: FieldPosition,
                             field_layout: FieldLayout) -> AdvancementDecision:
    """
    Decide advancement on single.
    
    General rules:
    - Runner on 2nd → usually advances to 3rd (85% of time)
    - Runner on 3rd → scores on most singles (90%), holds on shallow hits
    - Runner on 1st → usually stays at 1st, advances to 2nd on outfield singles
    """
    if current_base == "third":
        # Check ball location - if hit to outfield, runner scores
        ball_depth = ball_location.y  # Distance toward outfield
        
        if ball_depth > 180:  # Deep in outfield
            return AdvancementDecision(True, "home", 0.95, "Deep single, scoring from 3rd")
        elif ball_depth > 120:  # Medium depth
            return AdvancementDecision(True, "home", 0.80, "Medium single, attempting to score")
        else:  # Shallow (infield single)
            return AdvancementDecision(False, "third", 0.70, "Shallow hit, holding at 3rd")
    
    elif current_base == "second":
        # Most runners advance to 3rd on singles
        ball_depth = ball_location.y
        
        if ball_depth > 150:
            return AdvancementDecision(True, "third", 0.90, "Advancing to 3rd")
        else:
            # Infield single - might hold
            return AdvancementDecision(True, "third", 0.60, "Risky advance to 3rd")
    
    elif current_base == "first":
        # Usually stay at 1st on infield singles, advance to 2nd on outfield singles
        ball_depth = ball_location.y
        
        if ball_depth > 180:
            return AdvancementDecision(True, "second", 0.85, "Taking extra base")
        else:
            return AdvancementDecision(False, "first", 0.80, "Staying at 1st")
```

### 5. Tag Play Mechanics

**Scenario**: Runner attempting to advance, not forced.
- Runner slides into base
- Fielder receives throw and applies tag
- Close plays determined by timing difference

**Implementation**:
```python
def simulate_tag_play(runner: BaseRunner,
                     target_base: str,
                     throw_arrival_time: float,
                     current_time: float) -> TagPlayResult:
    """
    Simulate tag play (non-force) at base.
    
    Timeline:
    1. Runner slides into base
    2. Fielder receives throw
    3. Fielder applies tag
    
    Close plays (< 0.2s difference) have stochastic outcome.
    """
    # Calculate runner arrival time
    runner_time = runner.calculate_time_to_base(runner.current_base, target_base)
    runner_arrival = current_time + runner_time
    
    # Add slide time (0.3-0.6s based on sliding ability)
    slide_time = runner.get_slide_time()  # 0.3-0.6s
    runner_slide_complete = runner_arrival + slide_time
    
    # Fielder needs time to receive throw and apply tag
    tag_application_time = 0.2 + np.random.uniform(0, 0.2)  # 0.2-0.4s
    fielder_tag_time = throw_arrival_time + tag_application_time
    
    # Compare timing
    time_diff = runner_slide_complete - fielder_tag_time
    
    if time_diff < -0.3:
        # Runner clearly safe
        return TagPlayResult("safe", time_diff, "Runner beat the tag")
    elif time_diff > 0.3:
        # Runner clearly out
        return TagPlayResult("out", time_diff, "Tagged out by clear margin")
    else:
        # Close play! Stochastic outcome with slight runner advantage
        # Runner gets benefit of doubt in 55% of close plays
        safe_prob = 0.55 + (time_diff * 0.5)  # -0.3 to +0.3 → 0.40 to 0.70
        is_safe = np.random.random() < safe_prob
        
        return TagPlayResult(
            "safe" if is_safe else "out",
            time_diff,
            f"BANG-BANG play! Called {'SAFE' if is_safe else 'OUT'}"
        )
```

## Integration with Existing Code

### Modified Functions

**1. `play_simulation.py::_handle_ball_in_play()`**
```python
def _handle_ball_in_play(self, batted_ball: BattedBallResult, result: PlayResult):
    """Handle ball in play with realistic baserunning."""
    
    # Get fielding result (who fields it, when, where)
    fielding_result = self._simulate_fielding(batted_ball)
    
    # Check for force plays and double plays on ground balls
    if fielding_result.is_ground_ball and len(self.runners) > 0:
        dp_result = self.attempt_double_play(fielding_result)
        if dp_result.success:
            result.outs_made = dp_result.outs_made
            result.outcome = PlayOutcome.DOUBLE_PLAY
            return
    
    # Determine hit outcome based on ball location
    hit_type = self._classify_hit(batted_ball, fielding_result)
    
    # For each runner, decide advancement
    for base, runner in self.runners.items():
        decision = decide_runner_advancement(
            runner, base, fielding_result.ball_position,
            fielding_result.ball_speed, hit_type,
            result.outs, self.runners, self.field_layout
        )
        
        if decision.should_advance:
            # Simulate race: runner vs throw
            throw_result = simulate_throw(
                fielding_result.fielder,
                fielding_result.ball_position,
                decision.target_base,
                self.field_layout
            )
            
            # Determine outcome
            if is_force_play(base, decision.target_base, self.runners):
                outcome = simulate_force_play(runner, throw_result)
            else:
                outcome = simulate_tag_play(runner, throw_result)
            
            if outcome == "out":
                result.outs_made += 1
            else:
                # Runner advances successfully
                self.advance_runner(base, decision.target_base)
```

## Validation Metrics

After implementation, games should show:

### Target Statistics
- **Runs/9 innings**: 8-10 (currently 13.5)
- **Double plays per game**: 1.0-1.5 (currently 0)
- **Runners thrown out**: 2-3 per game
- **BABIP**: 0.290-0.310 (currently variable)

### Test Scenarios
1. **Ground ball with runner on 1st, 0 outs**: Should result in DP ~10-12% of time
2. **Single to outfield with runner on 2nd**: Runner advances to 3rd ~85% of time
3. **Single to outfield with runner on 3rd**: Runner scores ~90% of time
4. **Double to gap with runner on 1st**: Runner should score
5. **Double to gap with runner on 2nd**: Runner should score

## Implementation Priority

1. **Phase 1 - Throw Physics** (2-3 hours)
   - Implement `simulate_throw()` in fielding.py
   - Add arm strength/accuracy attributes to FielderAttributes
   - Test throw timing accuracy

2. **Phase 2 - Force Plays** (2-3 hours)
   - Implement `detect_force_situation()`
   - Add force play logic to ground ball handling
   - Test with simple scenarios

3. **Phase 3 - Double Plays** (3-4 hours)
   - Implement `attempt_double_play()`
   - Add pivot fielder identification
   - Test 6-4-3, 4-6-3 scenarios

4. **Phase 4 - Runner Decisions** (4-5 hours)
   - Implement `decide_runner_advancement()`
   - Add base running IQ to runner attributes
   - Test various hit scenarios

5. **Phase 5 - Tag Plays** (2-3 hours)
   - Implement `simulate_tag_play()`
   - Add sliding mechanics
   - Test close plays

6. **Phase 6 - Integration** (3-4 hours)
   - Modify `_handle_ball_in_play()`
   - Update `_handle_hit_baserunning()`
   - Full system testing

**Total estimated time**: 16-22 hours

## Expected Impact

This system will:
1. **Reduce scoring** from 13.5 to ~9 runs/9 innings
2. **Add realism** with double plays, force outs, and runners thrown out
3. **Create tension** with close plays and racing scenarios
4. **Enable strategy** with hit-and-run, sacrifice bunts, etc. (future)

## Notes

- All timing constants should be calibrated against MLB data
- Runner attributes (speed, base running IQ) affect all decisions
- Fielder attributes (arm strength, accuracy, transfer time) affect outcomes
- System should be deterministic given inputs (for reproducibility)
- Stochastic elements only in close plays and throw accuracy
