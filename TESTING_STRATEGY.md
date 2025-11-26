# Baseball Physics Simulator - Testing Strategy

**Last Updated**: 2025-11-26  
**Purpose**: Define the focused testing approach for development

---

## Core Philosophy

> **The simulation exists to model MLB baseball using real player data.**  
> Testing with synthetic `create_test_team()` is useful only for early physics development.  
> At this stage, **all meaningful testing should use real MLB teams from the database**.

---

## Testing Tiers

### Tier 1: Physics Validation (REQUIRED for physics changes)

```bash
python -m batted_ball.validation
```

- **Must pass**: 7/7 tests
- **When to run**: Before committing ANY physics-related change
- **Time**: ~5 seconds
- **What it tests**: Core aerodynamics (drag, Magnus, altitude, temperature effects)

This is the ONLY synthetic test that matters. It validates the physics engine itself.

### Tier 2: MLB Database Games (PRIMARY testing method)

```bash
game_simulation.bat → Option 8 → Select teams → 5-10 games
```

- **Recommended**: 5-10 games (fast, still statistically meaningful)
- **Time**: 5-10 games ≈ 1-3 minutes
- **What it tests**: Real game flow with actual player attributes
- **Output**: Game logs saved to `game_logs/` folder

**This is your main testing workflow.** Real MLB teams with real stats from the database.

#### Quick Alternative (command line):
```bash
python examples/simulate_db_teams.py
```

### Tier 3: Quick Sanity Check (optional)

```bash
python examples/quick_game_test.py
```

- **Time**: ~10 seconds
- **What it tests**: Basic game flow works without crashes
- **Uses**: Synthetic teams (acceptable for quick smoke test)

---

## What NOT to Run Regularly

These tests exist but are **not needed for normal development**:

| Test File | Why Not | When To Use |
|-----------|---------|-------------|
| `tests/test_league_simulation.py` | 240 games, 10-20 min | Never (synthetic teams) |
| `tests/test_league_simulation_quick.py` | 112 games, 2-5 min | Never (synthetic teams) |
| `tests/test_parallel_*.py` | Performance testing only | Optimization work |
| `tests/test_*_tuning.py` | Outdated calibration tests | Archive |

**These tests use synthetic teams and don't reflect real MLB gameplay.**

---

## Recommended Development Workflow

### For Physics Changes

1. Make your change in `constants.py`, `aerodynamics.py`, etc.
2. Run: `python -m batted_ball.validation` (must pass 7/7)
3. Run: `game_simulation.bat` → Option 8 → 5 games with MLB teams
4. Check game log output for realistic stats

### For Game Logic Changes

1. Make your change in `game_simulation.py`, `at_bat.py`, etc.
2. Run: `game_simulation.bat` → Option 8 → 5-10 games
3. Review the detailed log output

### For Bug Fixes

1. Reproduce with MLB teams (5 games)
2. Fix the bug
3. Verify with MLB teams (5 games)
4. If physics-related, also run validation

---

## Game Log Analysis

After running MLB games, check the log in `game_logs/`:

### Expected Stats (per 9 innings, 2-team combined)
- **Runs**: 8-10 total
- **Hits**: 15-20 total
- **HR**: 2-4 total
- **K%**: 20-28%
- **BB%**: 8-12%
- **BABIP**: .280-.320

### Red Flags
- K% > 35% or < 15%
- BB% > 18% or < 4%
- HR > 8 per game or 0 HR in 5 games
- BABIP > .400 or < .200

---

## Performance Notes

| Games | Approximate Time | Use Case |
|-------|------------------|----------|
| 1-3 | 20-60 seconds | Quick check |
| 5-10 | 1-3 minutes | **Standard testing** |
| 20+ | 5+ minutes | Only if investigating trends |
| 50+ | 15+ minutes | Avoid (use 10-game samples instead) |

**Don't run more than 10 games for routine testing.** The simulation is computationally intensive.

---

## Test Folder Structure

```
tests/
├── test_physics.py          # ✓ KEEP - Unit tests for physics modules
├── test_contact_stats.py    # ✓ KEEP - Contact mechanics validation
├── test_hr_detection.py     # ✓ KEEP - Home run physics
├── test_ground_ball_fielding.py  # ✓ KEEP - Fielding mechanics
├── archive/                 # Moved here - obsolete synthetic tests
│   ├── test_league_simulation.py
│   ├── test_league_simulation_quick.py
│   ├── test_parallel_*.py
│   ├── test_scoring_tuning.py
│   └── ...
```

---

## Summary

1. **Physics changes** → `python -m batted_ball.validation` (7/7 required)
2. **All other testing** → `game_simulation.bat` → Option 8 → 5-10 games with MLB teams
3. **Avoid** synthetic team tests and large game counts (>10)
4. **Check logs** in `game_logs/` for realistic stats

The goal is testing with **real MLB data**, not tuning synthetic teams.
