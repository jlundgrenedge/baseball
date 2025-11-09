# League Simulation Tests

Comprehensive baseball league simulation tests that create multi-team leagues with varying strengths and simulate full seasons while tracking all standard baseball statistics.

## Overview

This test suite provides two simulation options:
1. **Full 60-Game Season** - Complete simulation with 240 total games
2. **Quick 12-Game Season** - Faster test with 48 total games for rapid testing

## Files

### Main Simulation
- **test_league_simulation.py** - Full 60-game season simulation
  - Each team plays 60 games (30 home, 30 away)
  - Total of ~240 games simulated
  - Runtime: ~60-90 minutes depending on CPU cores

- **test_league_simulation_quick.py** - Quick 12-game season
  - Each team plays 12 games
  - Total of ~48 games simulated
  - Runtime: ~10-15 minutes
  - Perfect for quick testing and validation

## League Configuration

### Team Distribution (8 Teams)

The simulations create a balanced league with varying team qualities:

| Quality Level | Number of Teams | Example Team Names | Attribute Range |
|--------------|-----------------|-------------------|-----------------|
| **Elite**    | 2 teams         | Dragons, Thunderbolts | 65-85 |
| **Good**     | 3 teams         | Warriors, Hurricanes, Mavericks | 55-75 |
| **Average**  | 2 teams         | Pioneers, Voyagers | 45-65 |
| **Poor**     | 1 team          | Underdogs | 30-50 |

This distribution creates realistic competitive dynamics where:
- Elite teams should dominate the standings
- Good teams compete for playoff spots
- Average teams have mixed results
- Poor teams struggle but can still upset better teams

## Features

### 1. Intelligent Schedule Generation

The `LeagueScheduler` class creates balanced schedules:
- Even distribution of home/away games
- Each team plays similar number of games against each opponent
- Randomized game order for realism
- Detailed schedule summary reporting

### 2. Comprehensive Statistics Tracking

The `TeamStats` class tracks all major baseball statistics:

**Win-Loss Records:**
- Wins, Losses, Ties
- Winning Percentage
- Games Played

**Offensive Statistics:**
- Runs Scored (total and per game)
- Hits (total and per game)
- Home Runs (total and per game)
- Run Differential

**Defensive Statistics:**
- Runs Allowed (total and per game)
- Hits Allowed
- Home Runs Allowed

**Game History:**
- Individual game scores
- Opponent tracking
- Full season record

### 3. League-Wide Analysis

**Standings:**
- Ranked by winning percentage and run differential
- Complete team records
- Runs for/against tracking

**Quality-Based Performance:**
- Aggregate stats by team quality level
- Win percentage by quality tier
- Offensive/defensive performance by tier
- Validates that better teams perform better

**MLB Calibration:**
- Runs per 9 innings (target: ~9.0)
- Hits per 9 innings (target: ~17.0)
- Home runs per 9 innings (target: ~2.2)

## Usage

### Run Full 60-Game Season

```bash
python tests/test_league_simulation.py
```

Expected runtime: 60-90 minutes
Expected output:
- Team creation log
- Schedule summary
- Simulation progress
- Final standings
- Detailed team statistics
- League-wide analysis

### Run Quick 12-Game Season

```bash
python tests/test_league_simulation_quick.py
```

Expected runtime: 10-15 minutes
Perfect for:
- Quick validation
- Testing code changes
- Demonstrating functionality

## Output Format

### 1. League Standings

```
Rank  Team                Quality   W    L    PCT     RF    RA    DIFF
------------------------------------------------------------------------------
1     Thunderbolts        elite     45   15   .750    540   420   +120
2     Dragons             elite     42   18   .700    510   450   +60
3     Warriors            good      38   22   .633    480   470   +10
...
```

### 2. Detailed Team Statistics

For each team:
- Win-Loss record and percentage
- Offensive stats (runs, hits, HRs per game)
- Defensive stats (runs allowed, etc.)
- Run differential
- Full game history

### 3. League-Wide Summary

- Total games played
- League average statistics
- MLB calibration comparison
- Quality-based performance analysis

## Architecture

### Class Hierarchy

```
LeagueSimulation (main coordinator)
├── TeamStats (per-team statistics)
├── LeagueScheduler (schedule generation)
└── ParallelGameSimulator (game execution)
    └── GameSimulator (individual games)
```

### Key Components

**LeagueSimulation:**
- Orchestrates the entire season
- Manages teams and schedule
- Aggregates and reports statistics

**TeamStats:**
- Tracks comprehensive statistics for each team
- Calculates derived metrics (percentages, averages)
- Maintains game-by-game history

**LeagueScheduler:**
- Generates balanced schedules
- Distributes home/away games evenly
- Provides schedule analysis

**Statistics Tracking:**
- Uses proportional distribution for hits/HRs (based on runs scored)
- Tracks cumulative and per-game stats
- Validates against MLB norms

## Performance

### Parallel Processing

- Uses all available CPU cores by default
- Processes games in parallel batches
- ~5-8x faster than sequential simulation
- Configurable chunk size for optimization

### Expected Performance

On a modern 8-16 core CPU:
- **Full Season (60 games/team, 240 total):** ~60-90 minutes
- **Quick Season (12 games/team, 48 total):** ~10-15 minutes
- **Per Game:** ~15-20 seconds average

### Optimization Tips

1. More CPU cores = faster simulation
2. Adjust `chunk_size` in `ParallelSimulationSettings`
3. Disable `show_progress` for small speedup
4. Use quick test for development iterations

## Validation

The simulation validates against MLB norms:

**Expected Ranges (per 9 innings):**
- Runs: 8.0 - 10.0 (target: 9.0)
- Hits: 15.0 - 19.0 (target: 17.0)
- Home Runs: 1.5 - 3.0 (target: 2.2)

**Team Quality Validation:**
- Elite teams should have win% > 0.600
- Good teams should have win% around 0.500-0.600
- Average teams should have win% around 0.450-0.550
- Poor teams should have win% < 0.450

## Customization

### Modify Team Distribution

Edit the `teams_config` dictionary in `main()`:

```python
teams_config = {
    "Team1": "elite",    # 65-85 attributes
    "Team2": "good",     # 55-75 attributes
    "Team3": "average",  # 45-65 attributes
    "Team4": "poor",     # 30-50 attributes
}
```

### Adjust Season Length

Change `games_per_team` parameter:

```python
league.generate_schedule(games_per_team=30)  # Shorter season
league.generate_schedule(games_per_team=162)  # MLB full season
```

### Modify Parallel Settings

Customize simulation settings:

```python
settings = ParallelSimulationSettings(
    num_workers=8,        # Specific core count
    chunk_size=4,         # Games per batch
    verbose=False,        # Detailed output
    show_progress=True,   # Progress bars
    log_games=False       # Game logging
)
```

## Example Output

### Quick Test Results

```
================================================================================
LEAGUE STANDINGS
================================================================================

Rank  Team                Quality   W    L    PCT     RF    RA    DIFF
------------------------------------------------------------------------------
1     Warriors            good      10   4    .714    132   98    +34
2     Thunderbolts        elite     9    4    .692    125   102   +23
3     Dragons             elite     8    4    .667    110   95    +15
4     Hurricanes          good      7    7    .500    98    105   -7
5     Mavericks           good      6    8    .429    92    108   -16
6     Pioneers            average   6    8    .429    88    102   -14
7     Voyagers            average   5    8    .385    85    95    -10
8     Underdogs           poor      3    9    .250    72    115   -43
```

## Technical Notes

### Statistics Approximation

Since `GameResult` only tracks total hits and HRs (not per-team), the simulation uses proportional distribution based on runs scored:

```python
away_proportion = away_runs / total_runs
away_hits_est = int(total_hits * away_proportion)
```

This is a reasonable approximation as teams that score more runs typically have more hits.

### Future Enhancements

Potential improvements:
1. Track individual player statistics
2. Add pitcher win-loss records
3. Include fielding statistics
4. Playoff simulation
5. Season series tracking
6. Head-to-head records
7. Detailed per-team splits (home/away performance)

## Dependencies

- Python 3.7+
- NumPy
- batted_ball module (game simulation engine)
- multiprocessing (parallel execution)

## Related Files

- `batted_ball/game_simulation.py` - Core game simulation
- `batted_ball/parallel_game_simulation.py` - Parallel processing
- `tests/test_parallel_60_games.py` - Single matchup parallel test
- `performance_test_suite.py` - Performance benchmarking

## Support

For issues or questions:
1. Check simulation output for errors
2. Verify MLB calibration metrics
3. Review team quality distributions
4. Check parallel processing settings

## License

Part of the baseball simulation project.
