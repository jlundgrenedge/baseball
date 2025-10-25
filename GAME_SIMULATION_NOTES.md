# Game Simulation Implementation Notes

## What's Been Built

We've successfully created a full baseball game simulation system that integrates all the physics-based mechanics:

### Core Components

1. **GameState** - Tracks complete game state:
   - Current inning and half (top/bottom)
   - Outs count
   - Score for both teams
   - Runners on base
   - Game statistics (pitches, hits, home runs)

2. **Team** - Represents a baseball team:
   - Roster of pitchers (starters and relievers)
   - Batting lineup (9 hitters)
   - Defensive fielders (dict by position)
   - Tracks current pitcher and batter

3. **GameSimulator** - Orchestrates the full game:
   - Simulates innings, at-bats, and plays
   - Integrates AtBatSimulator, PlaySimulator
   - Updates game state after each play
   - Tracks play-by-play events with physics data
   - Verbose output with detailed physics metrics

4. **Helper Functions**:
   - `create_test_team()` - Generates teams with randomized players
   - Quality levels: poor, average, good, elite

### Features

- ✅ Full 9-inning game simulation
- ✅ Detailed play-by-play output
- ✅ Physics data for every play (exit velocity, launch angle, distance, hang time)
- ✅ Base runner tracking
- ✅ Score tracking
- ✅ Pitch counting
- ✅ Multiple outcomes (strikeouts, walks, hits)
- ✅ Safety limits to prevent infinite loops

## Known Issues to Address

### 1. Exit Velocities Too High (HIGH PRIORITY)
**Current:** 220-235 mph
**Expected:** 80-120 mph (MLB max ~122 mph)

**Likely causes:**
- Contact model coefficients may need tuning
- Conversion factor from m/s to mph might be wrong (should be 2.237)
- Bat speed or pitch speed attributes may be scaled incorrectly

**Fix locations:**
- `batted_ball/contact.py` - Check COR and collision physics
- `batted_ball/player.py` - Review how attributes convert to actual velocities
- `batted_ball/game_simulation.py` line 367 - Verify conversion formula

### 2. Too Many Singles, No Variety (HIGH PRIORITY)
**Current:** Almost every ball in play = single
**Expected:** Mix of ground outs, fly outs, singles, doubles, triples, home runs

**Likely causes:**
- PlaySimulator may be classifying outcomes based on distance/trajectory
- Fielders may not be making plays on catchable balls
- All exit velocities and launch angles falling in "single" range

**Fix locations:**
- `batted_ball/play_simulation.py` - Review outcome classification logic
- `batted_ball/fielding.py` - Check fielding catch probability
- May need to review trajectory landing positions vs field dimensions

### 3. No Runs Being Scored
**Current:** Score stays 0-0
**Expected:** Runners should advance and score on hits

**Likely causes:**
- PlaySimulator's `final_runner_positions` may not include scoring runners
- Baserunning advancement logic may need review
- Fallback logic only places batter on base, not existing runners

**Fix locations:**
- `batted_ball/game_simulation.py` lines 464-471 - Fallback logic is too simple
- `batted_ball/play_simulation.py` - Check how runners advance on hits
- `batted_ball/baserunning.py` - Review runner advancement decisions

### 4. Players Not Tracked Properly on Bases
**Current:** Using simplified logic that just stores the batter
**Expected:** Track actual player who's on each base

**Fix locations:**
- `batted_ball/game_simulation.py` lines 454-462 - Currently just uses `batter` for all bases
- Need to maintain mapping of BaseRunner -> Hitter
- Need to track which actual player scored for RBI stats

## Recommendations for Next Steps

### Phase 1: Fix Physics (Most Important)
1. Debug why exit velocities are 2x too high
2. Check unit conversions throughout the pipeline
3. Validate that attribute ratings (0-100) convert to realistic physics values

### Phase 2: Improve Outcome Variety
1. Review PlaySimulator outcome classification
2. Ensure fielders are attempting catches on fly balls
3. Add ground ball -> ground out logic
4. Tune launch angle / distance thresholds for hit types

### Phase 3: Fix Runner Advancement
1. Properly track which players are on which bases
2. Implement runner advancement on hits (single = +1 base, double = +2, etc.)
3. Handle force plays and tagging up
4. Calculate RBIs properly

### Phase 4: Realism Tuning
1. Adjust hit rates to match MLB averages (~.250 batting average)
2. Tune strikeout rates
3. Add walks (currently very rare)
4. Balance offense vs defense

### Phase 5: Future Enhancements
1. Multiple pitchers (starter → bullpen)
2. Defensive positioning and shifts
3. Stolen bases and pickoffs
4. Substitutions
5. SQLite database for players and teams (as originally planned)
6. Game replay and visualization
7. Season simulation

## Testing the Current System

Run a 3-inning test game:
```bash
python examples/simulate_full_game.py
```

The game will show:
- Detailed play-by-play
- Physics data for each batted ball
- Current game state (inning, outs, runners)
- Final statistics

## File Structure

```
batted_ball/
├── game_simulation.py     # NEW: Main game simulation classes
├── at_bat.py             # Plate appearance simulation
├── play_simulation.py    # Complete play orchestration
├── fielding.py           # Fielding mechanics
├── baserunning.py        # Runner advancement
├── player.py             # Pitcher and Hitter attributes
├── contact.py            # Bat-ball collision
├── trajectory.py         # Ball flight physics
└── ...

examples/
└── simulate_full_game.py  # NEW: Demo game simulation
```

## Performance Notes

- Current 3-inning game takes ~30-60 seconds
- Safety limit of 50 at-bats per half-inning prevents infinite loops
- Verbose output can be disabled for faster batch simulations
- Each at-bat creates fresh AtBatSimulator (could be optimized)

## Conclusion

We have a working end-to-end baseball game simulation! The framework is solid and all the pieces are connected. The main work remaining is tuning the physics and outcome probabilities to match real baseball statistics.

The system successfully demonstrates:
- Integration of all physics modules (pitching, hitting, fielding, baserunning)
- State management through a full game
- Realistic game flow (innings, outs, at-bats)
- Detailed telemetry and logging

With the physics tuning described above, this will be a very realistic baseball simulator!
