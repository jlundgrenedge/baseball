# Phase 1: Debug Metrics Integration Guide

## Overview

This guide describes how to integrate the `DebugMetricsCollector` into
the simulation engine to track where K%, BB%, and HR/FB are generated.

## Integration Points

### 1. GameSimulator (game_simulation.py)

```python
class GameSimulator:
    def __init__(self, away_team, home_team, verbose=False, debug_collector=None):
        self.debug_collector = debug_collector
        if debug_collector:
            debug_collector.start_game(game_id)
```

### 2. AtBatSimulator (at_bat.py)

Add logging in `_determine_pitch_intention()`:

```python
def _determine_pitch_intention(self, balls, strikes, pitch_type):
    # ... existing logic ...
    
    if self.debug_collector:
        self.debug_collector.log_pitch_intention(
            inning=self.current_inning,
            balls=balls,
            strikes=strikes,
            # ... all parameters ...
        )
```

### 3. Hitter.decide_to_swing() (player.py)

```python
def decide_to_swing(self, pitch, balls, strikes, debug_collector=None):
    # ... calculate swing probability ...
    
    if debug_collector:
        debug_collector.log_swing_decision(...)
    
    return did_swing
```

### 4. Whiff Calculation (player.py)

Similar pattern for `calculate_whiff_probability()`

### 5. Collision Physics (contact.py)

Log in `calculate_contact_result()` or similar function

### 6. Ball Flight (trajectory.py)

Log in `BattedBallSimulator.simulate()`

## Testing

1. Run with debug enabled: `python research/run_debug_analysis.py --games 5`
2. Verify metrics are being collected
3. Analyze output JSON for insights
4. Compare against MLB benchmarks

## Expected Insights

- **K% Analysis**: See which whiff factors contribute most (barrel accuracy vs pitch type)
- **BB% Analysis**: See how many walks come from intentional balls vs command error
- **HR/FB Analysis**: See EV/LA distributions and identify tail issues

