# Phase 2A Refinement Plan - Push K% to 22%

**Date**: 2025-11-20
**Status**: 🚀 Active - Refinement in Progress
**Branch**: `claude/add-agent-mission-01G6so7LCSpGquX1yLqefgbh`

---

## Current State

### Test Results (10-Game Validation)
- **K% (Strikeout Rate)**: 10.2% ⚠️ (Target: 22%)
- **Chase Rate**: ~20% (Target: 25-35%)
- **BB% (Walk Rate)**: 16.6% (Target: 8-9%)
- **HR/FB Rate**: 13.4% ✅ (Target: 12.5%)
- **BABIP**: 0.268 ✅ (Target: 0.260-0.360)

### Gap Analysis
- **K% Gap**: 11.8 percentage points below target
- **Chase Rate Gap**: 5-15 percentage points below target range

---

## Root Cause Analysis

### Why is K% Still Low?

1. **Chase Rate Too Low** (PRIMARY ISSUE)
   - Current: ~20%
   - Target: 25-35%
   - Impact: Fewer strikeouts on pitches outside the zone

2. **Discipline Impact Still Too Strong**
   - Current multiplier: 0.40
   - Elite discipline reduces chase by 36% (1 - 0.90 × 0.40 = 0.64)
   - This may still be too generous to elite hitters

3. **2-Strike Chase Bonus Too Small**
   - Current bonus: +15% flat
   - May need to be larger to create desperation swings

4. **Whiff Rates May Be Low**
   - Not yet investigated in detail
   - Could be contributing factor

---

## Refinement Strategy

### Approach: Incremental Parameter Tuning

Rather than overhauling the system, we'll make targeted adjustments to the parameters that control chase rate and whiff probability.

**Philosophy**:
- Small, measurable changes
- Test after each change
- Avoid breaking what's working (VISION decoupling, put-away mechanism)

---

## Refinement Sprints

### Sprint 1: Further Reduce Discipline Impact

**Goal**: Increase chase rate by 5-10 percentage points

**Current State**:
```python
# player.py lines 665-674
swing_prob = base_swing_prob * (1 - discipline_factor * 0.40)
```

**Proposed Change**:
```python
# Reduce from 0.40 to 0.30 (25% reduction in discipline effect)
swing_prob = base_swing_prob * (1 - discipline_factor * 0.30)
```

**Expected Impact**:
- Elite discipline (0.90): 1 - 0.90 × 0.30 = 0.73 → 27% reduction
  - Base chase 35% × 0.73 = 25.6% actual ✅ (MLB elite: 20-25%)
- Poor discipline (0.45): 1 - 0.45 × 0.30 = 0.865 → 13.5% reduction
  - Base chase 35% × 0.865 = 30.3% actual ✅ (MLB poor: 30-35%)

**Predicted K% Increase**: +3-5 percentage points

---

### Sprint 2: Increase 2-Strike Chase Bonus

**Goal**: Add more desperation with 2 strikes

**Current State**:
```python
# player.py lines 715-721
two_strike_bonus = 0.15  # Flat +15 percentage points
swing_prob_after_count = min(base_chase_after_discipline * 1.4 + two_strike_bonus, 0.70)
```

**Proposed Change**:
```python
# Increase from 0.15 to 0.25 (67% increase in flat bonus)
two_strike_bonus = 0.25  # Flat +25 percentage points
swing_prob_after_count = min(base_chase_after_discipline * 1.4 + two_strike_bonus, 0.70)
```

**Expected Impact**:
- With 2 strikes, chase rate gets +25% instead of +15%
- More strikeouts on 0-2, 1-2 counts
- Batters more desperate to protect the plate

**Predicted K% Increase**: +2-3 percentage points

---

### Sprint 3: Test Combined Effects

**Goal**: Validate K% reaches 22% target

**Testing Protocol**:
1. Run 10-game validation test (robust sample size)
2. Check K% against target (22%)
3. Verify no regressions (HR/FB, BABIP)
4. Document chase rate improvement

**Success Criteria**:
- K% between 20-24% (22% ± 2%)
- Chase rate between 23-37% (30% ± 7%)
- No regressions on existing metrics

---

### Sprint 4: Optional - Fine-Tune Whiff Rates

**Goal**: If K% still below 20%, investigate whiff probability

**Potential Changes**:
1. Increase base whiff rates in `player.py`
2. Increase put-away multiplier range
3. Add pitch-type specific whiff adjustments

**Only execute if Sprints 1+2 don't reach target**

---

## Implementation Plan

### Phase 1: Reduce Discipline Impact (Sprint 1)
- [ ] Update `player.py` line 672: Change 0.40 → 0.30
- [ ] Update comment to reflect new calculations
- [ ] Run 3-game quick test to verify direction
- [ ] Commit change

### Phase 2: Increase 2-Strike Bonus (Sprint 2)
- [ ] Update `player.py` line 718: Change 0.15 → 0.25
- [ ] Update comment to reflect new bonus
- [ ] Run 3-game quick test to verify direction
- [ ] Commit change

### Phase 3: Validate (Sprint 3)
- [ ] Run 10-game validation test
- [ ] Analyze K%, chase rate, BB%
- [ ] Check for regressions
- [ ] Document results

### Phase 4: Document (Sprint 4)
- [ ] Create PHASE2A_REFINEMENT_COMPLETE.md
- [ ] Update PHASE2A_COMPLETE.md with final results
- [ ] Commit and push all changes

---

## Risk Assessment

### Low Risk Changes
- ✅ Discipline multiplier reduction (0.40 → 0.30)
  - Tested approach (already reduced from 0.85 → 0.40)
  - Small incremental change
  - Easy to revert if overshoots

- ✅ 2-strike chase bonus increase (0.15 → 0.25)
  - Isolated to specific count situation
  - Capped at 0.70 to prevent unrealistic behavior
  - Grounded in MLB data (batters protect plate with 2 strikes)

### Potential Issues
- ⚠️ May overshoot K% target
  - Mitigation: Test after each change
  - Can reduce parameters if needed

- ⚠️ Chase rate may still be below range
  - Mitigation: Have Sprint 4 ready for additional tuning

- ⚠️ BB% may increase
  - Mitigation: Phase 2B will address BB% separately
  - K% is higher priority

---

## Expected Outcomes

### Conservative Estimate (Sprint 1 + Sprint 2)
- K%: 10.2% → 18-20%
- Chase rate: 20% → 26-30%
- BB%: 16.6% → 15-17% (slight improvement)

### Optimistic Estimate
- K%: 10.2% → 21-23% ✅
- Chase rate: 20% → 28-32% ✅
- BB%: 16.6% → 14-16%

### Worst Case
- K%: 10.2% → 15-17%
- Would require Sprint 4 (whiff rate tuning)

---

## Timeline

- **Sprint 1**: 15 minutes (code change + quick test)
- **Sprint 2**: 15 minutes (code change + quick test)
- **Sprint 3**: 30 minutes (10-game test + analysis)
- **Sprint 4**: 30 minutes (documentation)

**Total**: ~90 minutes

---

## Success Definition

**Minimum Success**:
- K% ≥ 20% (90% of target)
- Chase rate ≥ 23% (within 7 pp of range)
- No regressions on HR/FB or BABIP

**Full Success**:
- K% = 20-24% (within 2 pp of 22% target)
- Chase rate = 23-37% (within 7 pp of 30% midpoint)
- BB% ≤ 17% (progress toward eventual 8-9% target)

---

**Plan Created**: 2025-11-20
**Author**: Claude (AI Assistant)
**Session**: Agent Mission 01G6so7LCSpGquX1yLqefgbh
