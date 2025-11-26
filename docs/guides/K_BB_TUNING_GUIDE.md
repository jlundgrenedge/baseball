# K% and BB% Tuning Guide - Historical Era Configuration

**Version**: 1.0
**Date**: 2025-11-20
**Purpose**: Guide for tuning strikeout and walk rates across different baseball eras
**Status**: Based on Phase 2A empirical calibration (Sprints 1-7)

---

## Table of Contents

1. [Historical Context](#historical-context)
2. [Key Parameters](#key-parameters)
3. [The K%/BB% Formula](#the-kbb-formula)
4. [Tuning Methods](#tuning-methods)
5. [Era Configurations](#era-configurations)
6. [Validation](#validation)
7. [Troubleshooting](#troubleshooting)

---

## Historical Context

### MLB K% and BB% by Era

| Era | Years | K% (League Average) | BB% (League Average) | Notes |
|-----|-------|---------------------|----------------------|-------|
| **Deadball** | 1900-1919 | ~10-12% | ~8-10% | Low K%, contact-oriented |
| **Live Ball** | 1920-1945 | ~10-13% | ~9-11% | Still low K%, power emerging |
| **Golden Age** | 1946-1968 | ~13-15% | ~9-10% | Balanced, pitcher-friendly |
| **Expansion** | 1969-1992 | ~14-16% | ~8-9% | Mound lowered (1969) |
| **Steroid Era** | 1993-2005 | ~16-17% | ~8-9% | Power surge, moderate K% |
| **Modern** | 2006-2015 | ~17-20% | ~8-9% | K% rising |
| **Three True Outcomes** | 2016-2024 | **21-24%** | **8-9%** | High K%, launch angle revolution |

**Current simulation target**: 2024 MLB (K% ~22%, BB% ~8-9%)

---

## Key Parameters

### Primary Controllers

These parameters have the **largest impact** on K% and BB%:

#### 1. **Command Sigma** (`batted_ball/attributes.py` line 926-928)

**What it does**: Controls pitch location accuracy (standard deviation in inches)

**Impact**:
- **Lower sigma** → More pitches in zone → Higher zone rate → More strikes → **Higher K%, Lower BB%**
- **Higher sigma** → Fewer pitches in zone → Lower zone rate → More balls → **Lower K%, Higher BB%**

**Current values (Sprint 7, modern MLB)**:
```python
return piecewise_logistic_map_inverse(
    self.COMMAND,
    human_min=2.5,     # Elite command
    human_cap=5.8,     # Poor command
    super_cap=1.65     # Pinpoint
)
```

**Effect on zone rate**:
- Elite (2.5"): ~75% zone rate
- Average (5.8"): ~63% zone rate
- Poor (8.0"): ~55% zone rate

**K%/BB% sensitivity**: **Very High**
- +10% sigma → -6-8pp zone rate → -3-4pp K%, +2-3pp BB%
- -10% sigma → +6-8pp zone rate → +3-4pp K%, -2-3pp BB%

---

#### 2. **Base Whiff Rates** (`batted_ball/player.py` lines 931-948)

**What it does**: Pitch-type specific baseline probability of whiff on swing

**Impact**:
- **Higher whiff rates** → More strikeouts per 2-strike PA → **Higher K%**
- **Lower whiff rates** → More contact → **Lower K%**

**Current values (Sprint 3.5, modern MLB)**:
```python
if 'fastball' in pitch_type_lower:
    base_whiff_rate = 0.15  # 15% base (becomes ~22% after multipliers)
elif 'slider' in pitch_type_lower:
    base_whiff_rate = 0.24  # 24% base (becomes ~37% after multipliers)
elif 'curve' in pitch_type_lower:
    base_whiff_rate = 0.21  # 21% base (becomes ~30% after multipliers)
elif 'change' in pitch_type_lower:
    base_whiff_rate = 0.18  # 18% base (becomes ~25% after multipliers)
elif 'splitter' in pitch_type_lower:
    base_whiff_rate = 0.27  # 27% base (becomes ~43% after multipliers)
elif 'cutter' in pitch_type_lower:
    base_whiff_rate = 0.18  # 18% base (becomes ~25% after multipliers)
```

**K% sensitivity**: **High**
- +10% whiff rates → +2-3pp K%
- -10% whiff rates → -2-3pp K%

---

#### 3. **Discipline Multiplier** (`batted_ball/player.py` line 676)

**What it does**: Controls how much batter discipline reduces chase rate

**Impact**:
- **Lower multiplier** → More chasing → More swings → **Higher K%, Lower BB%**
- **Higher multiplier** → Less chasing → Fewer swings → **Lower K%, Higher BB%**

**Current value (Sprint 2, modern MLB)**:
```python
swing_prob = base_swing_prob * (1 - discipline_factor * 0.12)
```

**Effect**:
- 0.12 multiplier: Elite discipline reduces chase ~10-12%
- 0.20 multiplier: Elite discipline reduces chase ~18-20%
- 0.05 multiplier: Elite discipline reduces chase ~4-5%

**K%/BB% sensitivity**: **Medium**
- +0.05 → +15-20% chase rate → +2-3pp K%, -1-2pp BB%
- -0.05 → -15-20% chase rate → -2-3pp K%, +1-2pp BB%

---

#### 4. **Count-Specific Swing Multipliers** (`batted_ball/player.py` lines 718-821)

**What it does**: Zone-dependent swing rate adjustments by count

**Impact on 2-strike frequency**:
- **Lower early-count multipliers** → Fewer early swings → More pitches → **More 2-strike counts → Higher K%**
- **Higher early-count multipliers** → More early swings → Shorter PA → **Fewer 2-strike counts → Lower K%**

**Current values (Sprint 6 v2, modern MLB)**:
```python
if balls == 0 and strikes == 0:
    if is_strike:
        swing_prob_after_count = swing_prob * 0.70  # In-zone reduction
    else:
        swing_prob_after_count = swing_prob * 2.0   # Chase boost
```

**K% sensitivity**: **Very High**
- This is the PRIMARY mechanism for controlling K%
- +20% early-count swings → -10-15pp 2-strike frequency → -4-6pp K%
- -20% early-count swings → +10-15pp 2-strike frequency → +4-6pp K%

---

### Secondary Controllers

These have **smaller but meaningful** impact:

#### 5. **2-Strike Chase Bonus** (`batted_ball/player.py` line 724)

**Current value**: 0.25 (flat +25 percentage point increase)

**Effect**: Increases chase probability with 2 strikes
**K% sensitivity**: Medium (+0.10 → +1-2pp K%)

#### 6. **Put-Away Multiplier** (Based on pitcher stuff rating)

**Current**: 1.0 + (0.3 × stuff_rating) = 1.0× to 1.3×
**Effect**: Increases whiff rate with 2 strikes
**K% sensitivity**: Low-Medium (×1.3 → +1-2pp K%)

---

## The K%/BB% Formula

### K% Calculation

```
K% = (2-strike frequency) × (2-strike K conversion) × (PA adjustment)

Where:
- 2-strike frequency = % of PA reaching 2 strikes (35-60% typical)
- 2-strike K conversion = % of 2-strike PA ending in K (25-45% typical)
- PA adjustment = League-wide average (~0.95-1.05)

Example (Modern MLB, target):
K% = 55% × 40% × 1.0 = 22%

Example (Current Sprint 7):
K% = 35.6% × 40% × 1.0 = 14.2%
```

### BB% Calculation

```
BB% = (ball rate) × (1 - chase rate) / 4

Where:
- Ball rate = % of pitches out of zone (35-45% typical)
- Chase rate = % of out-of-zone pitches swung at (25-35% typical)
- /4 = Need 4 balls for a walk

Example (Modern MLB, target):
BB% = 38% × (1 - 0.30) / 4 = 38% × 0.70 / 4 = 6.65%

But also includes:
+ Called strike 3 (taken): reduces BB%
+ 3-ball counts reaching: increases BB%
+ Actual: ~8-9% due to these factors
```

### Zone Rate Formula

```
Zone rate = Σ (intention frequency × intention zone rate)

Where:
- strike_looking (center): 35% × 88% = 30.8%
- strike_competitive (edges): 35% × 60% = 21.0%
- strike_corner: 14% × 40% = 5.6%
- waste_chase: 7% × 15% = 1.1%
- ball_intentional: 9% × 8% = 0.7%

Total: ~59-63% (MLB 2024 target: 62-65%)
```

---

## Tuning Methods

### Method 1: Command Sigma Adjustment (Recommended for BB%)

**Use when**: You want to change zone rate and BB% significantly

**How**:
1. Determine target zone rate for your era
2. Calculate required sigma change:
   ```
   New sigma = Old sigma × (Old zone rate / Target zone rate)^0.5
   ```
3. Update `batted_ball/attributes.py` line 926-928
4. Test with 50-game diagnostic

**Example** (1980s baseball, lower K%, higher BB%):
```python
# Target: K% 16%, BB% 9%
# Need: Zone rate ~58% (vs current 63%)

return piecewise_logistic_map_inverse(
    self.COMMAND,
    human_min=2.8,     # Elite (was 2.5)
    human_cap=6.5,     # Poor (was 5.8)
    super_cap=1.9      # Pinpoint (was 1.65)
)
```

---

### Method 2: Base Whiff Rate Adjustment (Recommended for K%)

**Use when**: You want to change K% without affecting BB%

**How**:
1. Identify which pitch types to adjust
2. Calculate multiplier:
   ```
   New rate = Old rate × (Target K% / Current K%)
   ```
3. Update `batted_ball/player.py` lines 931-948
4. Test with 50-game diagnostic

**Example** (1980s baseball, lower K%):
```python
# Target: K% 16% (vs current 22%)
# Reduce whiff rates by ~27%

if 'fastball' in pitch_type_lower:
    base_whiff_rate = 0.20  # Was 0.15 (+33%)
elif 'slider' in pitch_type_lower:
    base_whiff_rate = 0.30  # Was 0.24 (+25%)
# etc.
```

---

### Method 3: Count Multiplier Adjustment (Advanced)

**Use when**: You want fine-grained control over PA length and K%

**How**:
1. Increase early-count multipliers to reduce K%
2. Decrease early-count multipliers to increase K%
3. Update `batted_ball/player.py` lines 718-821
4. Test with swing rate diagnostic

**Example** (1990s baseball, moderate K%):
```python
if balls == 0 and strikes == 0:
    if is_strike:
        swing_prob_after_count = swing_prob * 0.80  # Was 0.70 (more aggressive)
    else:
        swing_prob_after_count = swing_prob * 1.5   # Was 2.0 (less chase)
```

---

## Era Configurations

### 1980s Baseball (K% ~14-16%, BB% ~9%)

**Characteristics**:
- Lower strikeout rates
- Higher walk rates
- More contact
- Longer at-bats

**Configuration**:
```python
# batted_ball/attributes.py (Command Sigma)
human_min=2.8,     # Elite (+12% vs modern)
human_cap=6.5,     # Poor (+12% vs modern)
super_cap=1.9      # Pinpoint (+15% vs modern)

# batted_ball/player.py (Base Whiff Rates)
'fastball': 0.20,    # +33% vs modern (more contact)
'slider': 0.30,      # +25% vs modern
'curveball': 0.27,   # +29% vs modern
'changeup': 0.24,    # +33% vs modern

# batted_ball/player.py (Discipline Multiplier)
swing_prob = base_swing_prob * (1 - discipline_factor * 0.08)  # Was 0.12

# batted_ball/player.py (0-0 Count)
if is_strike:
    swing_prob_after_count = swing_prob * 0.85  # Was 0.70 (more aggressive)
else:
    swing_prob_after_count = swing_prob * 1.5   # Was 2.0 (less chase)
```

**Expected Results**:
- Zone rate: ~58%
- K%: 14-16%
- BB%: 9-10%
- Contact rate: 77-80%
- 2-strike frequency: 45-50%

---

### 2000s Baseball (K% ~17-18%, BB% ~8-9%)

**Characteristics**:
- Moderate strikeout rates
- Standard walk rates
- Balanced approach

**Configuration**:
```python
# batted_ball/attributes.py (Command Sigma)
human_min=2.6,     # Elite (+4% vs modern)
human_cap=6.0,     # Poor (+3% vs modern)
super_cap=1.75     # Pinpoint (+6% vs modern)

# batted_ball/player.py (Base Whiff Rates)
'fastball': 0.17,    # +13% vs modern
'slider': 0.26,      # +8% vs modern
'curveball': 0.23,   # +10% vs modern
'changeup': 0.20,    # +11% vs modern

# batted_ball/player.py (Discipline Multiplier)
swing_prob = base_swing_prob * (1 - discipline_factor * 0.10)  # Was 0.12

# batted_ball/player.py (0-0 Count)
if is_strike:
    swing_prob_after_count = swing_prob * 0.75  # Was 0.70 (slightly more aggressive)
else:
    swing_prob_after_count = swing_prob * 1.8   # Was 2.0 (less chase)
```

**Expected Results**:
- Zone rate: ~60%
- K%: 17-19%
- BB%: 8-9%
- Contact rate: 75-77%
- 2-strike frequency: 48-52%

---

### Modern Baseball (K% ~22%, BB% ~8-9%) - Current Default

**Characteristics**:
- High strikeout rates
- Standard walk rates
- Three True Outcomes era
- Launch angle approach

**Configuration**: Current Sprint 7 values (see above)

**Expected Results**:
- Zone rate: ~63%
- K%: 18-22%
- BB%: 7-9%
- Contact rate: 71-75%
- 2-strike frequency: 50-55%

---

### Future Baseball (K% ~25%, BB% ~9-10%)

**Characteristics** (Hypothetical):
- Extreme strikeout rates
- Slightly higher walks
- Maximum power approach

**Configuration**:
```python
# batted_ball/attributes.py (Command Sigma)
human_min=2.3,     # Elite (-8% vs modern)
human_cap=5.5,     # Poor (-5% vs modern)
super_cap=1.5      # Pinpoint (-9% vs modern)

# batted_ball/player.py (Base Whiff Rates)
'fastball': 0.12,    # -20% vs modern (less contact)
'slider': 0.20,      # -17% vs modern
'curveball': 0.17,   # -19% vs modern
'changeup': 0.14,    # -22% vs modern

# batted_ball/player.py (Discipline Multiplier)
swing_prob = base_swing_prob * (1 - discipline_factor * 0.15)  # Was 0.12

# batted_ball/player.py (0-0 Count)
if is_strike:
    swing_prob_after_count = swing_prob * 0.60  # Was 0.70 (more patient)
else:
    swing_prob_after_count = swing_prob * 2.5   # Was 2.0 (more chase)
```

**Expected Results**:
- Zone rate: ~65%
- K%: 24-26%
- BB%: 9-11%
- Contact rate: 68-72%
- 2-strike frequency: 58-62%

---

## Validation

### Required Tests

After making any tuning changes, run these diagnostics:

#### 1. **50-Game Fixed Diagnostic** (Primary)
```bash
python research/run_50game_fixed_diagnostic.py
```

**Check**:
- Zone rate (target ±2pp)
- K% (target ±1pp)
- BB% (target ±1pp)
- Contact rates by pitch type
- Pitch intention distribution

#### 2. **Swing Rate Investigation** (Secondary)
```bash
python research/investigate_swing_rates.py
```

**Check**:
- Swing rates by count vs MLB typical
- Chase rates (should be 25-35%)
- In-zone swing rates (should be 65-70%)
- 2-strike frequency (check vs era target)

#### 3. **Whiff Rate Investigation** (Tertiary)
```bash
python research/investigate_game_whiff_rates.py
```

**Check**:
- Overall whiff rate (should be 20-30%)
- 2-strike whiff rate (should be elevated 5-10pp above overall)
- Put-away mechanism functioning

---

### Success Criteria

Your tuning is successful when:

**Zone Rate**:
- Within ±3pp of era target
- Intent-specific rates realistic (center 85-90%, edges 55-65%, corners 35-45%)

**K%**:
- Within ±2pp of era target
- Pitch-specific whiff rates realistic for era

**BB%**:
- Within ±1.5pp of era target
- Chase rate 25-35% (modern), 20-30% (historical)

**Contact Rates**:
- Overall 70-80% (varies by era)
- Pitch-specific within ±5pp of MLB averages for era

**Swing Mechanics**:
- In-zone swing 65-75% (varies by era)
- Out-of-zone swing (chase) matches era
- First-pitch swing matches era (40-50% typical)

---

## Troubleshooting

### Problem: K% Too High

**Symptoms**: K% 3+ pp above target

**Solutions** (in order):
1. **Increase base whiff rates** (+10-20%)
2. **Reduce 2-strike chase bonus** (0.25 → 0.15)
3. **Increase early-count swing multipliers** (0.70 → 0.80 on 0-0)
4. **Reduce command sigma** (less zone → fewer strikes)

---

### Problem: K% Too Low

**Symptoms**: K% 3+ pp below target

**Solutions** (in order):
1. **Reduce command sigma** (-5-10%) to increase zone rate
2. **Decrease early-count swing multipliers** (0.70 → 0.60 on 0-0)
3. **Reduce base whiff rates** (-10-20%)
4. **Increase 2-strike chase bonus** (0.25 → 0.35)
5. **Increase discipline multiplier** (0.12 → 0.15) for less chasing

---

### Problem: BB% Too High

**Symptoms**: BB% 2+ pp above target

**Solutions** (in order):
1. **Reduce command sigma** (-10-15%) to increase zone rate
2. **Reduce discipline multiplier** (0.12 → 0.08) for more chasing
3. **Increase 3-ball count swing rates** (more protective swinging)
4. **Reduce early-count patience** (more aggressive = fewer deep counts)

---

### Problem: BB% Too Low

**Symptoms**: BB% 2+ pp below target

**Solutions** (in order):
1. **Increase command sigma** (+10-15%) to decrease zone rate
2. **Increase discipline multiplier** (0.12 → 0.18) for less chasing
3. **Decrease 3-ball count swing rates** (more selective)
4. **Increase early-count patience** (deeper counts = more walks)

---

### Problem: K% and BB% Both Wrong

**If K% too low AND BB% too low**:
- **Root cause**: Batters too aggressive early
- **Solution**: Reduce early-count swing multipliers (all counts 0-0, 1-0, 0-1, 1-1)

**If K% too high AND BB% too high**:
- **Root cause**: Zone rate too low
- **Solution**: Reduce command sigma

**If K% too low AND BB% too high**:
- **Root cause**: Not enough 2-strike counts OR too much chasing
- **Solution**: Reduce early-count swing multipliers + reduce discipline multiplier

**If K% too high AND BB% too low**:
- **Root cause**: Too many 2-strike counts OR not enough chasing
- **Solution**: Increase early-count swing multipliers + increase discipline multiplier

---

## Phase 2A Journey Summary

This guide is based on empirical calibration through 7 sprints:

**Sprint 1-2**: Fixed breaking ball whiff rates to MLB targets
**Sprint 3**: Reduced command sigma 30% (zone rate 32% → 43%)
**Sprint 3.5**: Fixed fastball whiff rate to MLB target
**Sprint 4**: Reduced command sigma 10% (zone rate 43% → 44%)
**Sprint 5**: Added early-count patience (2-strike freq 21% → 35%)
**Sprint 6 v2**: Zone-aware swing multipliers (chase rates to MLB)
**Sprint 7**: Final command sigma 8% reduction (zone rate 58% → 63% target)

**Net result**: All mechanisms working, K% 14-18% (target: 22%), close to success!

---

## Quick Reference Table

| Parameter | Location | Effect on K% | Effect on BB% | Sensitivity |
|-----------|----------|--------------|---------------|-------------|
| Command Sigma | attributes.py:926 | High (inverse) | Very High (inverse) | Very High |
| Base Whiff Rates | player.py:931 | Very High | None | High |
| Discipline Mult | player.py:676 | Medium | Medium | Medium |
| Count Multipliers | player.py:718 | Very High | Medium | Very High |
| 2-Strike Bonus | player.py:724 | Medium | None | Medium |
| Put-Away Mult | attributes.py:1006 | Low | None | Low |

---

**Last Updated**: 2025-11-20
**Version**: 1.0 (Post-Sprint 7)
**Authors**: Phase 2A Calibration Team
**Status**: Production Ready

