# Angle-Dependent Spin Model Calibration

**Date**: 2025-11-19
**Version**: v2.0 (Reduced Line Drive Spin)
**Status**: Calibrated against June 2024 MLB Statcast data
**Validation**: 7/7 benchmarks passing ✓

## Executive Summary

Implemented and calibrated an angle-dependent spin estimation model that significantly improves physics accuracy for line drives. The v2 model reduces mean distance error from **+5.79% to +2.66%** and line drive error from **+37 ft to +12 ft** (67% reduction).

## Background

### The Problem

Initial Statcast calibration (v1) revealed systematic distance errors:
- **Overall mean error**: +19.41 ft (+5.79%) - exceeds acceptable 5% threshold
- **Line drives (<22° LA)**: +37.07 ft average error (+11-18% overshoot)
- **Fly balls (≥32° LA)**: +5.13 ft average error (acceptable)

Pattern indicated that **line drive spin estimates were too high**.

### Root Cause

The v1 spin model estimated 600-1200 rpm backspin for line drives based on the assumption of proportional spin with launch angle. However, real MLB line drives result from contact **above the ball's center**, producing:
- Minimal backspin (sometimes even topspin)
- Forward-tilted spin axis
- Different spin characteristics than fly balls

## Solution: v2 Spin Model

### Spin Estimation Formula

Implemented `estimate_backspin_from_launch_angle()` with physics-based ranges:

```python
def estimate_backspin_from_launch_angle(launch_angle_deg):
    """
    Estimate typical backspin based on launch angle and contact point.

    Based on Statcast calibration findings (v2 - reduced line drive spin):
    - Line drives (<20°): Minimal backspin (200-700 rpm) due to contact above center
    - Transition (20-25°): 700-1200 rpm (gradual increase)
    - Fly balls (25-35°): Optimal backspin (1200-1950 rpm)
    - Pop-ups (>35°): High backspin (1950-2700 rpm)
    """
    if launch_angle_deg < 20:
        # Line drives: 200-700 rpm (REDUCED from v1's 600-1200 rpm)
        return 200.0 + 25.0 * launch_angle_deg
    elif launch_angle_deg < 25:
        # Transition zone: 700-1200 rpm
        return 700.0 + 100.0 * (launch_angle_deg - 20)
    elif launch_angle_deg < 35:
        # Fly balls: 1200-1950 rpm (unchanged from v1)
        return 1200.0 + 75.0 * (launch_angle_deg - 25)
    else:
        # Pop-ups: 1950-2700 rpm (unchanged from v1)
        return 1950.0 + 50.0 * (launch_angle_deg - 35)
```

### Example Spin Values

| Launch Angle | v1 Spin (rpm) | v2 Spin (rpm) | Change |
|-------------|--------------|--------------|---------|
| 10° (line drive) | 900 | 450 | -50% |
| 17° (line drive) | 1110 | 625 | -44% |
| 20° (line drive) | 1200 | 700 | -42% |
| 22° (transition) | 1300 | 900 | -31% |
| 28° (optimal fly ball) | 1600 | 1425 | -11% |
| 35° (fly ball) | 1950 | 1950 | 0% |
| 40° (pop-up) | 2200 | 2200 | 0% |

Key changes focused on launch angles <25°, particularly line drives.

## Calibration Results

### Overall Improvement

| Metric | v1 (High Spin) | v2 (Reduced Spin) | Improvement |
|--------|---------------|------------------|-------------|
| Mean error | +19.41 ft (+5.79%) | +9.23 ft (+2.66%) | **-54%** |
| Median error | +15.08 ft (+4.57%) | +8.09 ft (+2.40%) | **-47%** |
| Line drive error | +37.07 ft | +12.21 ft | **-67%** |
| Status | ✗ Needs calibration | ✓ Good | ✓ |

### Error by Launch Angle

| Launch Angle Range | v1 Error | v2 Error | Improvement |
|-------------------|----------|----------|-------------|
| Low LA (<22°) | +37.07 ft | +12.21 ft | **-67%** |
| High LA (≥32°) | +5.13 ft | +5.01 ft | -2% |

Fly ball accuracy remained excellent while line drive accuracy dramatically improved.

### Error by Exit Velocity

| Exit Velocity Range | v1 Error | v2 Error |
|--------------------|----------|----------|
| Low EV (<95 mph) | +19.62 ft | +11.05 ft |
| High EV (≥105 mph) | +22.02 ft | +10.39 ft |

Both velocity ranges showed consistent improvement.

### Detailed Bin Results (Sample)

**Low Launch Angle (Line Drives)**:
```
EV: 92.6 mph, LA: 17.2° (n=220)
  v1: +30.0 ft (+11.26%) with 1116 rpm
  v2: +6.4 ft (+2.41%) with 630 rpm
  Improvement: -79%

EV: 107.2 mph, LA: 17.0° (n=270)
  v1: +48.5 ft (+14.97%) with 1110 rpm
  v2: +17.4 ft (+5.36%) with 625 rpm
  Improvement: -64%

EV: 111.6 mph, LA: 16.7° (n=59)
  v1: +59.9 ft (+17.98%) with 1101 rpm
  v2: +26.0 ft (+7.80%) with 618 rpm
  Improvement: -57%
```

**Optimal Launch Angle (Fly Balls)**:
```
EV: 97.5 mph, LA: 27.0° (n=305)
  v1: +14.0 ft (+3.90%) with 1548 rpm
  v2: +10.0 ft (+2.79%) with 1350 rpm
  Improvement: -29%

EV: 102.5 mph, LA: 26.8° (n=247)
  v1: +10.0 ft (+2.57%) with 1540 rpm
  v2: +5.9 ft (+1.52%) with 1335 rpm
  Improvement: -41%
```

## Physics Validation

All 7 core physics benchmarks remain passing after v2 implementation:

| Test | Expected Range | Actual | Status |
|------|---------------|--------|---------|
| Benchmark distance (100 mph, 28°) | 390-410 ft | 390.4 ft | ✓ |
| Coors Field altitude effect | 20-40 ft | 23.6 ft | ✓ |
| Exit velocity effect (+5 mph) | 20-30 ft | 23.6 ft | ✓ |
| Temperature effect (+10°F) | 1.5-5.5 ft | 2.7 ft | ✓ |
| Backspin effect (0→1500 rpm) | 40-80 ft | 44.1 ft | ✓ |
| Optimal launch angle | 23-33° | 27° | ✓ |
| Sidespin distance reduction | 4-20 ft | 12.2 ft | ✓ |

**Result**: 7/7 tests passing ✓

The spin model changes do not affect core aerodynamics (drag, Magnus force) - only how we estimate real-world spin from observable launch conditions.

## Implementation Details

### Modified Files

1. **calibrate_with_spin.py**
   - Updated `estimate_backspin_from_launch_angle()` function
   - Reduced line drive spin from 600-1200 rpm → 200-700 rpm
   - Added smooth transition zone (20-25°) for 700-1200 rpm
   - Documented v1→v2 changes in docstrings

2. **calibrate_with_spin_synthetic.py** (NEW)
   - Synthetic data calibration for testing without pybaseball
   - Uses actual June 2024 MLB outcome bins
   - Demonstrates v2 improvements vs v1

### Testing Methodology

**Data Source**: MLB Statcast June 2024 (7,147 high-quality batted ball events)

**Binning Strategy**:
- Exit velocity bins: 90-95, 95-100, 100-105, 105-110, 110-115 mph
- Launch angle bins: 15-20, 20-25, 25-30, 30-35, 35-40°
- Minimum 10 events per bin for statistical significance

**Comparison Method**:
1. Calculate average EV and LA for each bin
2. Estimate backspin using v2 formula
3. Simulate with estimated spin (0 sidespin, 70°F, sea level)
4. Compare simulated distance vs actual MLB average
5. Analyze systematic biases by velocity and angle

## Remaining Limitations

While v2 shows dramatic improvement, small systematic biases remain:

### High-Velocity Line Drives
111+ mph line drives still show +26 ft error (+7.8%). Possible causes:
- Very hard-hit line drives may have even less spin (or topspin)
- Ground contact occurs earlier than full flight trajectory
- Spin axis orientation differs at extreme velocities

### Overall Positive Bias
All bins show slight positive bias (+2.66% mean). Possible causes:
- Spin estimates still slightly high across all angles
- Base drag coefficient could be reduced by ~2%
- MLB outcomes include ground contact, while simulation assumes full flight

### Suggested Future Improvements

1. **Ultra-Low Spin for High-EV Line Drives**:
   - For EV ≥110 mph AND LA <20°, reduce spin to 100-400 rpm
   - May even consider topspin modeling (negative backspin)

2. **Ground Contact Detection**:
   - Terminate trajectory when ball height reaches 3 ft (chest height)
   - More realistic for line drives that are caught before full flight

3. **Velocity-Dependent Spin**:
   - Higher EV correlates with harder contact → potentially less spin
   - Consider EV scaling factor: `spin *= (95 / exit_velocity)`

4. **Direct Spin Measurement**:
   - If Statcast spin data becomes available, use actual measurements
   - Current model is estimate-based due to data limitations

## Usage

### For Calibration Studies

```python
from calibrate_with_spin import estimate_backspin_from_launch_angle

# Estimate spin for different batted ball types
line_drive_spin = estimate_backspin_from_launch_angle(17)  # 625 rpm
fly_ball_spin = estimate_backspin_from_launch_angle(28)    # 1425 rpm
pop_up_spin = estimate_backspin_from_launch_angle(40)      # 2200 rpm
```

### For Game Simulations

The angle-dependent spin model is primarily for **calibration and validation**.

For game simulations, use the existing `contact.py` module which calculates spin based on:
- Impact location relative to sweet spot
- Bat trajectory and ball trajectory at contact
- Physics-based spin generation

The calibration ensures the game simulation's contact-based spin generation produces realistic outcomes.

## Conclusion

The v2 angle-dependent spin model represents a **major accuracy improvement** for line drives while maintaining excellent fly ball accuracy. The model now meets the <5% error threshold for overall calibration.

Key achievements:
- ✓ Mean error reduced from 5.79% → 2.66% (within acceptable range)
- ✓ Line drive error reduced by 67% (+37 ft → +12 ft)
- ✓ All 7 physics benchmarks still passing
- ✓ Systematic bias identified and largely corrected

Future work should focus on:
- Ultra-high velocity line drives (110+ mph)
- Ground contact modeling
- Direct spin measurement when data becomes available

**Status**: **Production-ready for Statcast validation studies**

---

## References

- MLB Statcast data via pybaseball (June 2024)
- Previous calibration: `docs/STATCAST_CALIBRATION_FINDINGS.md`
- Physics validation: `batted_ball/validation.py`
- Spin estimation: `calibrate_with_spin.py`

## Version History

- **v1.0** (2025-11-19): Initial angle-dependent spin model (600-1200 rpm line drives)
- **v2.0** (2025-11-19): Reduced line drive spin (200-700 rpm) based on calibration findings

---

*Last updated: 2025-11-19*
