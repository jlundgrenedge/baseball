# Game Simulation Implementation Notes

## Summary

✅ **Working:** Full baseball game simulation with realistic physics!
- Exit velocities: 95-115 mph (MLB-realistic)
- Variety of outcomes: HRs, triples, doubles, singles, strikeouts
- Scoring system functional
- Detailed play-by-play with physics data

⚠️ **Needs Tuning:** Offense/defense balance
- Too many hits (needs more outs)
- Fielders should catch more fly balls
- Ground ball outs need improvement

**Current State:** Playable game that demonstrates all the physics working together. Just needs statistical balancing to match MLB averages.

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

## Fixed Issues ✓

### 1. Exit Velocities (FIXED)
**Was:** 220-235 mph (double conversion bug)
**Now:** 95-115 mph (realistic MLB range)

**Root cause:** Exit velocity was being converted from m/s to mph twice
- Once in contact model (already returned mph)
- Again in game_simulation.py (multiplied by 2.237 again)

**Fix:** Removed double conversion in `game_simulation.py` line 375

### 2. Outcome Variety (IMPROVED)
**Was:** Almost every ball = single
**Now:** Mix of home runs, doubles, triples, singles, strikeouts

**Improvements made:**
- Added distance-based outcome classification in `play_simulation.py`
- Home runs: 380+ ft with 40+ ft peak, or 400+ ft
- Triples: 380+ ft
- Doubles: 280+ ft or slow retrieval time
- Singles: everything else

**Still needs:** More fly outs and ground outs (too offense-heavy)

### 3. Scoring (FIXED)
**Was:** Score stayed 0-0
**Now:** Runs are scored and tallied properly

**Improvements made:**
- Home runs count all runners on base
- Runners advance on extra-base hits
- Score updates correctly each play

## Remaining Issues to Address

### 1. Too Offense-Heavy (MEDIUM PRIORITY)
**Current:** Lots of home runs and doubles, very few outs
**Expected:** More balanced - roughly 3 outs per inning from balls in play

**Likely causes:**
- Fielders not catching enough fly balls
- Launch angle distribution may favor line drives too much
- Catch probability in fielding simulator may be too low

**Fix locations:**
- `batted_ball/fielding.py` - Increase catch success rates
- `batted_ball/play_simulation.py` - Tune when balls are catchable vs HRs
- May need to adjust launch angle distributions in contact model

### 2. Missing Ground Outs
**Current:** Very few ground balls result in outs
**Expected:** Ground balls should often result in outs

**Fix locations:**
- `batted_ball/play_simulation.py` _handle_ground_ball method
- May need faster fielder movement or slower runners

### 3. No Pop Outs / Infield Flies
**Current:** All fly balls either caught for outs in outfield or become hits
**Expected:** Some high pop-ups should be easy outs

**Fix locations:**
- Need to classify very high, short-distance fly balls as pop-ups
- Infielders should have near 100% catch rate on pop-ups

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
