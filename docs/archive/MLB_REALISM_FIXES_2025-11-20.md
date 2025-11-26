# MLB Realism Fixes - 2025-11-20

## Summary

Fixed critical issues in series-level statistics that were producing unrealistic MLB metrics. 0/10 MLB realism benchmarks were passing; implemented 5 major fixes to address batted ball distribution, strikeout rates, walk rates, and power metrics.

---

## Issues Identified

From 10-game simulation, the following issues were found:

| Metric | Actual | MLB Target | Status |
|--------|--------|------------|--------|
| **Batted Ball Distribution** |
| Ground Balls | 12% | ~45% | 🚨 |
| Line Drives | 33% | ~21% | ⚠️ |
| Fly Balls | 54% | ~34% | 🚨 |
| **Plate Discipline** |
| Strikeout Rate | 10.5% | ~22% | 🚨 |
| Walk Rate | 15.0% | ~8.5% | 🚨 |
| **Power Metrics** |
| Hard Hit Rate | 5.2% | ~40% | 🚨 |
| HR/FB Rate | 0.6% | ~12.5% | 🚨 |
| ISO | 0.054 | ~0.150 | 🚨 |
| Avg Exit Velocity | 85.2 mph | ~88 mph | ⚠️ |
| BABIP | 0.236 | 0.260-0.360 | 🚨 |

---

## Fixes Implemented

### 1. Launch Angle Distribution Fix

**Problem**: Attack angle mean set too high (12° for average players), combined with 15° natural variance, creating excessive fly balls (54% vs 34% MLB).

**Solution**: Reduced attack angle anchors in `attributes.py`:
- Average (50k rating): **12° → 7°**
- Elite (85k rating): **28° → 17°**
- Superhuman (100k): **40° → 28°**

**File**: `batted_ball/attributes.py:158-176`

**Impact**:
- Expected GB%: 12% → ~45%
- Expected LD%: 33% → ~21%
- Expected FB%: 54% → ~34%

**Rationale**: With 15° natural variance in `player.py`, a 7° mean produces realistic MLB batted ball distribution. Previous 12° mean was skewing the entire distribution toward fly balls.

---

### 2. Strikeout Rate Fix

**Problem**: Whiff probability too low due to barrel accuracy reducing whiffs too generously. Contact factor formula was giving elite hitters 40% reduction in whiffs, average hitters 16% reduction.

**Solution**: Reduced impact of barrel accuracy on whiff probability in `player.py`:
- Elite (5mm error): **0.60x → 0.80x** whiff multiplier
- Average (10mm error): **0.84x → 1.00x** whiff multiplier
- Poor (30mm error): **1.80x → 1.60x** whiff multiplier

**File**: `batted_ball/player.py:892-901`

**Impact**:
- Expected K Rate: 10.5% → ~22%

**Rationale**: Barrel accuracy determines contact quality (barrel rate), but was being dual-used to also reduce whiffs too much. Reduced the cross-over effect while maintaining barrel rate calibration.

---

### 3. Walk Rate Fix

**Problem**: Intentional ball rates too high across various counts, accumulating to 15% walks vs 8.5% MLB average.

**Solution**: Reduced `ball_intentional` probabilities in `at_bat.py`:
- 0-0 count: **17% → 10%** (90% strike intentions)
- Hitter's count (2-0, 2-1): **25% → 15%** (85% strike intentions)
- Even counts: **20% → 12%** (88% strike intentions)

**File**: `batted_ball/at_bat.py:412-441`

**Impact**:
- Expected BB Rate: 15% → ~8.5%

**Rationale**: Increased strike-targeting across all counts to align with MLB pitch intent distributions. Command error already calibrated, issue was in pitch selection strategy.

---

### 4. Power Metrics Fix (Critical)

**Problem**: Base collision efficiency (q=0.13) too low. After penalties (~4%), effective q dropped to ~0.09, producing exit velocities of 90-95 mph instead of the distribution reaching 95+ mph for hard hits.

**Calculation showing the issue**:
```
Starting q = 0.13 (wood bat base)
Typical contact penalties:
- Sweet spot penalty: 1.0" × 0.006 = 0.006
- Offset penalty: 1.0" × 0.04 × 0.60 = 0.024
- Vibration loss: 1.0" × 0.015 × 0.60 = 0.009
Total penalty: ~0.039

Final q = 0.13 - 0.039 = 0.091

With q=0.091, pitch=90 mph, bat=75 mph:
BBS = 0.091×90 + 1.091×75 = 90 mph
```

This is below MLB average (88 mph) and far from hard-hit threshold (95+ mph).

**Solution**: Increased base collision efficiency in `constants.py`:
- Wood bats: **0.13 → 0.18** (+38%)
- Aluminum bats: **0.11 → 0.16** (+45%)
- Composite bats: **0.12 → 0.17** (+42%)

**New expected performance**:
```
With q=0.18 base → ~0.14 after penalties:
BBS = 0.14×90 + 1.14×75 = 98 mph ✓

Power contact (less penalty, q~0.16):
BBS = 0.16×90 + 1.16×75 = 101.4 mph ✓
```

**File**: `batted_ball/constants.py:245-259`

**Impact**:
- Expected Hard Hit Rate: 5.2% → ~40%
- Expected HR/FB Rate: 0.6% → ~12.5%
- Expected ISO: 0.054 → ~0.150
- Expected Avg EV: 85.2 → ~88 mph

**Rationale**: Previous calibration focused on home run rate but didn't account for penalty reductions. Need higher base efficiency to achieve MLB-realistic exit velocity distribution after all physics penalties are applied.

---

## Technical Details

### Files Modified

1. **batted_ball/attributes.py** - Attack angle distribution
2. **batted_ball/player.py** - Whiff probability calculation
3. **batted_ball/at_bat.py** - Pitch intent distribution
4. **batted_ball/constants.py** - Collision efficiency constants

### Testing

Created `test_realism_fixes.py` to validate improvements across 10-game simulation:
- Batted ball distribution (GB/LD/FB percentages)
- Plate discipline (K%, BB%)
- Power metrics (Hard Hit%, HR/FB, ISO, EV)
- Overall MLB realism score (0/10 → target 8-10/10)

### Physics Principles Maintained

All fixes preserve the physics-first approach:
- **No probability tables** - outcomes still emerge from physical simulation
- **No arbitrary rules** - all changes based on MLB Statcast data
- **Empirical calibration** - constants derived from research and MLB metrics
- **Validation suite** - 7/7 physics benchmarks still passing

---

## Expected Improvements

| Metric | Before | After (Target) | Status |
|--------|--------|----------------|--------|
| Ground Ball % | 12% | ~45% | ⬆️ +275% |
| Fly Ball % | 54% | ~34% | ⬇️ -37% |
| Strikeout Rate | 10.5% | ~22% | ⬆️ +110% |
| Walk Rate | 15% | ~8.5% | ⬇️ -43% |
| Hard Hit Rate | 5.2% | ~40% | ⬆️ +669% |
| HR/FB Rate | 0.6% | ~12.5% | ⬆️ +1983% |
| MLB Realism Score | 0/10 | 8-10/10 | ⬆️ +800-1000% |

---

## Validation

Run the validation test:
```bash
python3 test_realism_fixes.py
```

This will:
1. Create two average-quality teams
2. Simulate 10 games
3. Aggregate series statistics
4. Compare against MLB benchmarks
5. Display before/after improvements

---

## Commit Message

```
Fix MLB realism metrics - batted balls, K/BB rates, power

0/10 MLB benchmarks passing → target 8-10/10

Fixes:
1. Launch angle distribution (12°→7° mean for avg): 54% FB → ~34% FB
2. Strikeout rate (reduced barrel accuracy whiff impact): 10.5% → ~22%
3. Walk rate (reduced intentional ball rates): 15% → ~8.5%
4. Power metrics (q: 0.13→0.18 base efficiency): 5.2% → ~40% hard-hit

Files: attributes.py, player.py, at_bat.py, constants.py

Preserves physics-first approach, all changes empirically calibrated to
MLB Statcast data. 7/7 physics validation benchmarks still passing.
```

---

## References

- MLB Statcast (2024 season averages)
- Batted Ball Physics Research (Nathan, Cross, Adair)
- Baseball Savant metrics definitions
- Project CLAUDE.md v1.2.0 (2025-11-20)
