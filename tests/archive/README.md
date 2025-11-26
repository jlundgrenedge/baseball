# Archived Tests

These tests have been archived because they use synthetic `create_test_team()` instead of real MLB data, or are one-off bug fix/calibration tests that are no longer needed.

**The simulation's purpose is modeling real MLB baseball.** Testing with synthetic teams doesn't validate the simulation for its intended use.

## When to use these

These tests may still be useful for:
- Performance benchmarking (`performance_test_suite.py`)
- Debugging specific physics issues (`debug_*.py`)
- Historical reference for how bugs were fixed
- Understanding calibration approaches

## Current testing approach

See `TESTING_STRATEGY.md` in the project root for the current testing philosophy:

1. **Physics validation**: `python -m batted_ball.validation` (7/7 tests)
2. **MLB games**: `game_simulation.bat` → Option 8 → 5-10 games with real teams

## Archived files

### League/Parallel Simulation (synthetic teams)
- `test_league_simulation.py` - 240 games with synthetic teams
- `test_league_simulation_quick.py` - 112 games with synthetic teams
- `test_parallel_*.py` - Performance testing with synthetic teams
- `test_multi_game_sample.py` - Multi-game with synthetic teams
- `LEAGUE_SIMULATION_README.md` - Old league documentation

### Bug Fix Tests (already fixed)
- `test_fix.py` - Generic fix test
- `test_baserunning_bug.py` - Baserunning bug reproduction
- `test_exit_velocity_fix.py` - Exit velocity calibration
- `test_walk_rate_fix.py` - Walk rate fix
- `test_hit_handler_force_score.py` - Force score bug
- `test_runner_on_first_scoring.py` - Scoring bug

### Calibration Tests (synthetic teams, outdated)
- `test_scoring_tuning.py` - Score calibration
- `test_series_metrics.py` - Series metrics with synthetic teams
- `test_optimization_accuracy.py` - Accuracy testing
- `test_pitcher_command_fixes.py` - Pitcher command calibration
- `test_pitch_variety.py` - Pitch variety testing
- `test_realism_fixes.py` - Realism calibration

### Logging/Integration Tests (synthetic teams)
- `test_enhanced_logging.py` - Logging test
- `test_logging_enhancements.py` - Logging test
- `test_route_efficiency_logging.py` - Route logging
- `test_bat_tracking_integration.py` - Bat tracking
- `test_fielder_assignment.py` - Fielder assignment

### Debug Scripts
- `debug_contact_quality.py` - Contact debugging
- `debug_outfield_interception.py` - Outfield debugging
- `debug_power_hitters.py` - Power hitter debugging

### Performance
- `performance_test_suite.py` - Performance benchmarking suite
- `test_performance_benchmarks.py` - Performance benchmarks
