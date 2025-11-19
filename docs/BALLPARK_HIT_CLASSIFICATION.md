# Ballpark-Adjusted Hit Classification

**Version:** 1.2.0
**Date:** 2025-11-19
**Feature:** Enhanced Hit Classification System

## Overview

The hit classification system has been enhanced with park-adjusted home run determination and dynamic extra-base hit classification. This brings the simulation closer to real MLB outcomes where ballpark dimensions significantly affect game results.

## Key Enhancements

### 1. Park-Adjusted Home Run Logic

**Before:** Fixed fence distances based on spray angle approximations
- Dead center: 400 ft
- Gaps: 380 ft
- Alleys: 360 ft
- Down the lines: 330 ft

**After:** Actual MLB ballpark dimensions with fence heights
- Interpolated fence distances based on exact spray angle
- Fence heights considered (e.g., Green Monster: 37 ft, Oracle right field: 25 ft)
- Ball height at fence distance checked against fence height

**Example:**
```python
from batted_ball import GameSimulator, create_test_team

# Play game at Fenway Park
yankees = create_test_team("Yankees", quality="elite")
red_sox = create_test_team("Red Sox", quality="elite")

# Simulate at Fenway (with Green Monster)
game = GameSimulator(yankees, red_sox, verbose=True, ballpark='fenway')
result = game.simulate_game(num_innings=9)

# Same teams at Yankee Stadium (short porch in right)
game2 = GameSimulator(yankees, red_sox, verbose=True, ballpark='yankee')
result2 = game2.simulate_game(num_innings=9)
```

### 2. Dynamic Double/Triple Classification

**Before:** Fixed distance thresholds
- Triple: distance > 300 ft AND in gap (10-50°)
- Double: distance > 230 ft
- Single: everything else

**After:** Context-driven classification using:
- **Fielder retrieval time** - Slower retrieval increases double/triple probability
- **Runner speed** - Fast runners (70+) get threshold bonuses:
  - Doubles: -15 ft threshold
  - Triples: Higher probability
- **Fielder speed** - Slow fielders (< 40) make doubles more likely
- **Contact quality** - Fair contact (80-88 mph) less likely to produce triples

**Example:**
```python
# Fast runner is more likely to leg out a double on a 215 ft hit
# (below the old 230 ft threshold) if fielder is slow or retrieval is delayed

# Slow runner on same ball typically gets a single
```

### 3. Probabilistic Triple Logic

**Before:** Deterministic (distance > 300 ft + in gap = triple)

**After:** Probability-based calculation considering:

**Base Factors:**
- Distance (most important)
  - 290-310 ft: +10% base
  - 310-330 ft: +20% base
  - 330+ ft: +30% base

**Runner Speed Modifier:**
- Fast runner (70+): Up to +25%
- Average (50): Neutral
- Slow (< 40): Up to -25%

**Fielder Speed Modifier:**
- Very slow fielder: +15%
- Average: Neutral
- Fast fielder: -15%

**Retrieval Time Modifier:**
- > 5.0 seconds: +15%
- 4.5-5.0 seconds: +10%
- 4.0-4.5 seconds: +5%

**Exit Velocity Bonus:**
- 100+ mph: +10%
- 95-100 mph: +5%

**Random Variance:**
- ±5% for ball bounce luck

**Probability Calculation Example:**
```
Ball: 315 ft, 25° spray angle, 98 mph EV
Runner: Speed 75 (fast)
Fielder: Speed 40 (slow)
Retrieval: 4.8 seconds

Base prob: 5% (gap shot)
+ Distance (310-330): +20%
+ Runner speed: +12.5% [(75-50)/100 * 0.25]
+ Fielder slow: +7.5% [(50-40)/100 * 0.15]
+ Retrieval time: +10%
+ EV bonus: +5%
+ Luck: +2% (random)
= 62% chance of triple

Roll dice: random() < 0.62 → Triple or Double
```

## MLB Ballparks Included

1. **Generic MLB Park** - Default, average dimensions
2. **Fenway Park (Boston)** - Famous Green Monster (37 ft left field wall)
3. **Yankee Stadium (New York)** - Short porches in right (314 ft)
4. **Coors Field (Denver)** - Deep center (415 ft), high altitude
5. **Oracle Park (San Francisco)** - High right field wall (25 ft), Triples Alley
6. **Dodger Stadium (Los Angeles)** - Symmetric, pitcher-friendly
7. **Wrigley Field (Chicago)** - Ivy walls, classic dimensions
8. **Petco Park (San Diego)** - Pitcher's park, deep power alleys
9. **Great American Ball Park (Cincinnati)** - Hitter-friendly, short fences
10. **Minute Maid Park (Houston)** - Tall left field wall (19 ft)

## Usage

### Basic Usage

```python
from batted_ball import GameSimulator, create_test_team, get_ballpark

# Create teams
home = create_test_team("Home Team", quality="elite")
away = create_test_team("Away Team", quality="good")

# Simulate at specific ballpark
game = GameSimulator(away, home, verbose=True, ballpark='fenway')
result = game.simulate_game(num_innings=9)
```

### Inspecting Ballpark Dimensions

```python
from batted_ball import get_ballpark, list_available_parks

# List all parks
parks = list_available_parks()
print(parks)  # ['coors', 'dodger', 'fenway', 'generic', ...]

# Get specific park
fenway = get_ballpark('fenway')

# Get fence at specific angle
distance, height = fenway.get_fence_at_angle(-45)  # Left field line
print(f"Green Monster: {distance} ft, {height} ft high")  # 310 ft, 37 ft

# Check if ball clears fence
spray_angle = -42  # To left field
ball_distance = 320  # ft
ball_height_at_fence = 40  # ft

is_hr = fenway.is_home_run(spray_angle, ball_distance, ball_height_at_fence)
print(f"Home run: {is_hr}")  # True (ball cleared 37 ft wall)
```

### Creating Custom Ballparks

```python
from batted_ball import BallparkDimensions

custom_park = BallparkDimensions(
    name="Custom Park",
    fence_profile={
        -45.0: (300, 20),   # Short left field, high wall
        -22.5: (370, 10),   # Left-center gap
        0.0: (420, 8),      # Deep center
        22.5: (370, 10),    # Right-center gap
        45.0: (320, 8),     # Right field line
    }
)

# Use in game
game = GameSimulator(away, home, verbose=True, ballpark=custom_park)
```

## Impact on Game Statistics

### Expected Changes

1. **Home Run Rates**
   - Coors Field: +15-20% home runs (deep but thin air)
   - Great American Ball Park: +10-15% (short fences)
   - Petco Park: -10-15% (deep power alleys)
   - Oracle Park: -5-10% (high right field wall)

2. **Triple Rates**
   - Fast teams: +30-50% more triples
   - Slow teams: -20-30% fewer triples
   - Overall triple rate: More realistic variance

3. **Park-Specific Quirks**
   - Fenway: More doubles off Green Monster, fewer home runs to left
   - Yankee Stadium: More home runs to right field (short porch)
   - Oracle: More triples in right-center gap (Triples Alley)

## Technical Details

### Files Modified

1. **batted_ball/ballpark.py** (NEW)
   - BallparkDimensions class
   - MLB_BALLPARKS database
   - get_ballpark() function
   - Fence interpolation logic

2. **batted_ball/hit_handler.py**
   - Added ballpark parameter to __init__
   - Updated determine_hit_type() to use park-specific fences
   - Added _classify_extra_base_hit() for dynamic classification
   - Added _calculate_triple_probability() for probabilistic triples
   - Added helper methods for extracting fielding context

3. **batted_ball/play_simulation.py**
   - Added ballpark parameter to PlaySimulator.__init__
   - Passes ballpark to HitHandler

4. **batted_ball/game_simulation.py**
   - Added ballpark parameter to GameSimulator.__init__
   - Passes ballpark to PlaySimulator

5. **batted_ball/__init__.py**
   - Exports ballpark module (BallparkDimensions, get_ballpark, etc.)

### Validation

All 7 physics validation tests still pass:
- ✓ Benchmark distance
- ✓ Coors Field altitude effect
- ✓ Exit velocity effect
- ✓ Temperature effect
- ✓ Backspin effect
- ✓ Optimal launch angle
- ✓ Sidespin reduction

Physics accuracy maintained while adding gameplay realism.

## Performance

**Impact:** Negligible (< 1% slowdown)
- Fence interpolation: O(log n) lookup (very fast)
- Triple probability calculation: Simple arithmetic
- No additional trajectory simulations

## Future Enhancements

Potential areas for expansion:

1. **Wind Effects by Park**
   - Wrigley: Strong winds from Lake Michigan
   - Oracle: Bay winds affect right field

2. **Field Surface Effects**
   - Turf vs grass affects ground ball speed
   - Wet/dry conditions

3. **Elevation Adjustments**
   - Coors Field thin air (already in physics, could integrate better)

4. **Day/Night Games**
   - Visibility affects fielding

5. **Dynamic Weather**
   - Temperature, humidity, wind speed

## References

- Official MLB ballpark dimensions: [MLB.com](https://www.mlb.com)
- Ballpark specifications: [BallparkPal.com](https://ballparkpal.com)
- Statcast data: MLB Advanced Media

## Version History

- **1.2.0** (2025-11-19): Initial ballpark-adjusted hit classification
  - 10 MLB ballparks with accurate dimensions
  - Dynamic double/triple classification
  - Probabilistic triple logic

---

**Maintained by:** Baseball Physics Simulation Engine Project
**Status:** Production-ready
**Validation:** 7/7 physics tests passing
