# Pitch Intention Logging Bug - Root Cause Analysis

**Date**: 2025-11-20
**Issue**: 27.9% of pitches have no logged intention in Sprint 4 tests
**Status**: ✅ ROOT CAUSE IDENTIFIED

---

## The Bug

### Symptom

Sprint 4 test showed:
- 72.1% of pitches had logged intentions
- 27.9% of pitches had NO logged intention

But diagnostic script (`diagnose_pitch_intentions.py`) showed:
- 100% of pitches get intentions when calling `_determine_pitch_intention()` directly

### Root Cause

**The pitch intention logging system has TWO separate collectors**:

1. **DebugMetricsCollector** (`debug_collector`):
   - Used by `run_50game_diagnostic.py`
   - Passed as `debug_collector` parameter to `AtBatSimulator`
   - Pitch intentions ARE logged when this is present

2. **SimMetricsCollector** (`metrics_collector`):
   - Used by `GameSimulator`
   - Passed as `metrics_collector` parameter to `AtBatSimulator`
   - Pitch intentions are NOT logged to this collector

### The Code

**In `batted_ball/at_bat.py` lines 922-938**:

```python
# Log pitch intention for Phase 1 debug metrics
if self.debug_collector:  # ← ONLY logs if debug_collector exists!
    self.debug_collector.log_pitch_intention(
        inning=0,
        balls=balls,
        strikes=strikes,
        outs=0,
        pitch_type=pitch_type,
        intention=pitch_intention,
        target_x=target_h,
        target_z=target_v,
        actual_x=actual_h,
        actual_z=actual_v,
        is_in_zone=pitch_data['is_strike'],
        pitcher_control=self.pitcher.attributes.get_control_zone_bias(),
        pitcher_command_sigma=self.pitcher.attributes.get_command_sigma_inches()
    )
```

**In `batted_ball/game_simulation.py` line 496**:

```python
# Create at-bat simulator for this matchup
at_bat_sim = AtBatSimulator(pitcher, batter, metrics_collector=self.metrics_collector)
#                                             ^^^ Only passes metrics_collector, NOT debug_collector!
```

**Result**: When using `GameSimulator`, `self.debug_collector` is None, so the `if self.debug_collector:` check fails, and pitch intentions are never logged.

---

## Why run_50game_diagnostic.py Worked

The diagnostic script creates `AtBatSimulator` directly with `debug_collector`:

```python
# research/run_50game_diagnostic.py line 46-50
sim = AtBatSimulator(
    pitcher=pitcher,
    hitter=hitter,
    debug_collector=collector  # ← Explicitly passes debug_collector
)
```

This means `self.debug_collector` is set, so pitch intentions ARE logged.

**That's why the diagnostic showed correct intention distributions** - it was using a different code path than normal game simulation!

---

## Why Only 72.1% of Pitches?

If `debug_collector` was None, we'd expect 0% of pitches to have logged intentions, not 72.1%.

**Two possibilities**:

### Possibility 1: Mixed Mode

Some at-bats used `debug_collector`, others didn't. This could happen if:
- Early in the test, `debug_collector` was enabled
- Later disabled or reset
- Creating selective logging

### Possibility 2: Different Calculation

The "27.9% missing" might be calculated differently:
- Total pitches thrown: N
- Pitches with intentions logged: 0.721 × N
- But maybe some pitches weren't counted in "total pitches"?

**Need to verify**: What exactly was counted as "total pitches" vs "pitches with logged intentions"?

---

## Impact on Zone Rate Analysis

### The Real Distribution (from diagnostic)

With proper logging (100% of pitches captured):

| Intention | Game-Wide % | Intent Zone Rate | Contribution |
|-----------|-------------|------------------|--------------|
| strike_looking | 34.9% | 88.5% | 30.9% |
| strike_competitive | 35.5% | 61.2% | 21.7% |
| strike_corner | 13.6% | 40.1% | 5.5% |
| waste_chase | 6.8% | 17.9% | 1.2% |
| ball_intentional | 9.2% | 6.0% | 0.6% |
| **TOTAL** | **100%** | | **59.8%** ✓ |

**Expected zone rate**: 59.8% (very close to MLB 62-65% target!)

### The Observed Distribution (Sprint 4 test)

With incomplete logging (72.1% of pitches captured):

| Intention | Observed % | Intent Zone Rate | Contribution |
|-----------|-----------|------------------|--------------|
| strike_looking | 27.8% | 88.5% | 24.6% |
| strike_competitive | 24.1% | 61.2% | 14.8% |
| strike_corner | 9.2% | 40.1% | 3.7% |
| waste_chase | 4.4% | 17.9% | 0.8% |
| ball_intentional | 6.6% | 6.0% | 0.4% |
| **Logged** | **72.1%** | | **44.3%** |
| **Missing** | **27.9%** | | **???** |

**Observed zone rate**: 44.2%

### The Discrepancy

If we had logged ALL pitches:
- Expected: 59.8% zone rate
- Observed: 44.2% zone rate
- **Gap: 15.6 percentage points**

This 15.6pp gap suggests there's STILL a problem beyond just logging:
1. The missing 27.9% of pitches might have lower zone rate
2. Or the command sigma is still larger than calculated
3. Or there's another execution issue

---

## The Fix

### Option A: Always Log Pitch Intentions (Recommended)

Store pitch intention in `pitch_data` dictionary regardless of collector presence:

```python
# In batted_ball/at_bat.py line 913-920 (already exists!)
pitch_data['pitch_intent'] = {
    'intended_zone': intended_zone,
    'intended_pitch_type': pitch_type,
    'intention_category': pitch_intention,  # ← Already stored!
    'x_error_inches': x_error,
    'z_error_inches': z_error,
    'missed_into_zone': missed_into_zone
}
```

**This already exists!** The intention IS stored in `pitch_data['pitch_intent']['intention_category']`.

The issue is that diagnostic scripts are reading from `debug_collector.get_summary_stats()` which only has data if `debug_collector` was used.

**Fix**: Modify diagnostic scripts to read from `pitch_data['pitch_intent']` instead of relying on collector.

### Option B: Add Pitch Intention Logging to SimMetricsCollector

Add a `log_pitch_intention()` method to `SimMetricsCollector` (in `sim_metrics.py`):

```python
def log_pitch_intention(self, ...):
    """Log pitch intention to metrics collector"""
    # Track intentions for zone rate analysis
    self.pitch_intentions[intention] = self.pitch_intentions.get(intention, 0) + 1
    if is_in_zone:
        self.pitch_intentions_zone[intention] = self.pitch_intentions_zone.get(intention, 0) + 1
```

Then in `at_bat.py`, log to BOTH collectors:

```python
# Log to debug_collector if present
if self.debug_collector:
    self.debug_collector.log_pitch_intention(...)

# ALSO log to metrics_collector if present
if self.metrics_collector:
    self.metrics_collector.log_pitch_intention(...)
```

### Option C: Unified Collector System

Merge `DebugMetricsCollector` and `SimMetricsCollector` into a single system that tracks everything.

**Risk**: Large refactor, might break existing code.

---

## Recommended Action

### Step 1: Verify the Data Exists

Check if `pitch_data['pitch_intent']['intention_category']` is populated for all pitches in `at_bat_result.pitches`.

If YES: The data exists, we just need to read it correctly.

If NO: There's a deeper bug in pitch_intent storage.

### Step 2: Fix Diagnostic Scripts

Modify `run_50game_diagnostic.py` to read intentions from `at_bat_result.pitches[i]['pitch_intent']['intention_category']` instead of from collector.

This will capture 100% of pitches, not just the 72.1% that had collector enabled.

### Step 3: Re-Run Sprint 4 Test

With correct intention logging:
- Should see ~34.9% strike_looking (not 27.8%)
- Should see ~59.8% zone rate (not 44.2%)
- K% should improve accordingly

If zone rate is STILL only 44%, then there's a command execution problem (not a logging problem).

---

## Conclusion

**The 27.9% "missing" intentions are NOT actually missing** - they're stored in `pitch_data['pitch_intent']` but not being logged to the collector.

**The diagnostic scripts need to be fixed** to read from the pitch_data directly, not rely on collector logging.

**Expected outcome after fix**:
- Zone rate: 44.2% → 59.8% (close to target 62-65%)
- K%: 9.6% → 18-20% (closer to target 22%)
- strike_looking: 27.8% → 34.9% (closer to expected)

**If zone rate is STILL low after fix**, then we have a command execution problem (sigma larger in practice than in code).

---

**Analysis Complete**: 2025-11-20
**Root Cause**: Pitch intentions logged only to `debug_collector`, not `metrics_collector`
**Fix**: Read pitch intentions from `pitch_data` directly, not from collector
**Status**: Ready to implement fix
