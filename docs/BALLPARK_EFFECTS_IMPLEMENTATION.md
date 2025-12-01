# Ballpark Effects Implementation

**Implemented**: November 2025

This document describes the comprehensive ballpark effects system integrated into the baseball physics simulator, providing realistic park-specific factors that affect gameplay.

---

## Overview

The simulator now includes detailed data for all **30 MLB ballparks** with:

1. **Fence Dimensions** - Accurate 2025 fence distances and heights at multiple angles
2. **Environmental Effects** - Altitude, temperature, humidity adjustments
3. **Park Factors** - Hit, run, and home run multipliers based on historical data
4. **Team Mappings** - Automatic ballpark assignment based on team

---

## Files Created/Modified

| File | Purpose |
|------|---------|
| `batted_ball/ballpark_effects.py` | **NEW** - Environmental effects, park factors, team mappings |
| `batted_ball/ballpark.py` | **UPDATED** - All 30 MLB parks with 2025 fence dimensions |
| `batted_ball/game_simulation.py` | **UPDATED** - Integration with ballpark effects |
| `batted_ball/team_loader.py` | **UPDATED** - Sets team abbreviation and home ballpark |
| `manage_teams.py` | **UPDATED** - Displays ballpark info when listing teams |

---

## Ballpark Effects Module (`ballpark_effects.py`)

### BallparkEffects Dataclass

```python
@dataclass
class BallparkEffects:
    name: str                    # Full stadium name
    altitude_ft: float           # Feet above sea level
    avg_temperature_f: float     # Average game-time temperature
    avg_humidity: float          # 0.0 to 1.0
    avg_wind_speed_mph: float    # Typical wind speed
    wind_direction_deg: float    # Predominant wind direction
    roof_type: str               # 'open', 'retractable', 'dome'
    environment: str             # 'outdoor', 'indoor', 'variable'
    
    # Park factors (1.0 = league average)
    park_factor_runs: float      # Run scoring factor
    park_factor_hr: float        # Home run factor
    park_factor_hits: float      # Hits factor
    
    # Distance modifiers based on park characteristics
    distance_modifier: float     # Base distance adjustment
```

### All 30 MLB Parks Included

#### American League East
- **Camden Yards** (BAL) - Warm, humid Baltimore summers
- **Fenway Park** (BOS) - Unique dimensions, Green Monster
- **Yankee Stadium** (NYY) - Short porch in right
- **Tropicana Field** → **Steinbrenner Field** (TB) - 2025 temporary home
- **Rogers Centre** (TOR) - Retractable dome

#### American League Central
- **Rate Field** (CHW) - Chicago lakefront weather
- **Progressive Field** (CLE) - Great Lakes humidity
- **Comerica Park** (DET) - Spacious outfield
- **Kauffman Stadium** (KC) - Midwest conditions
- **Target Field** (MIN) - Northern outdoor park

#### American League West
- **Minute Maid Park** (HOU) - Retractable roof, Texas heat
- **Angel Stadium** (LAA) - California coastal
- **Oakland Coliseum** (OAK) - Bay Area marine layer
- **T-Mobile Park** (SEA) - Pacific Northwest
- **Globe Life Field** (TEX) - Climate-controlled dome

#### National League East
- **Truist Park** (ATL) - Hot Atlanta summers
- **loanDepot Park** (MIA) - Retractable roof, Florida humidity
- **Citi Field** (NYM) - Flushing weather
- **Citizens Bank Park** (PHI) - Hitter-friendly
- **Nationals Park** (WSH) - Potomac River humidity

#### National League Central
- **Wrigley Field** (CHC) - Wind off Lake Michigan
- **Great American Ball Park** (CIN) - Ohio River valley
- **American Family Field** (MIL) - Retractable roof
- **Busch Stadium** (STL) - Mississippi River humidity
- **PNC Park** (PIT) - River confluence

#### National League West
- **Chase Field** (ARI) - Retractable roof, desert heat
- **Coors Field** (COL) - **5,280 ft altitude** (biggest effect!)
- **Dodger Stadium** (LAD) - Pitcher's park, dry air
- **Petco Park** (SD) - Marine layer
- **Oracle Park** (SF) - McCovey Cove winds

---

## Fence Dimensions (`ballpark.py`)

Each park has a detailed fence profile with distances and heights at 9 spray angles:

```python
# Example: Fenway Park
"fenway": BallparkDimensions(
    "Fenway Park",
    {
        -45.0:  (309, 37),  # Green Monster! (37 ft wall)
        -33.75: (327, 37),
        -22.5:  (345, 20),
        -11.25: (366, 10),
        0.0:    (388, 10),  # Center field
        11.25:  (383, 5),
        22.5:   (378, 5),
        33.75:  (338, 5),
        45.0:   (299, 5),   # Pesky Pole (shortest in MLB!)
    },
    park_id="fenway", team_abbr="BOS",
)
```

### Spray Angle Convention

| Angle | Location |
|-------|----------|
| -45° | Left field foul line |
| -22.5° | Left-center gap |
| 0° | Dead center field |
| +22.5° | Right-center gap |
| +45° | Right field foul line |

### Notable Park Features

| Park | Feature | Effect |
|------|---------|--------|
| **Fenway** | Green Monster (37 ft) | Turns HRs into doubles, doubles into singles |
| **Yankee Stadium** | Short right porch (314 ft) | Favors left-handed power |
| **Coors Field** | 5,280 ft altitude | ~10% more distance on fly balls |
| **Oracle Park** | Deep right-center (399 ft) | Suppresses right-center HRs |
| **Minute Maid** | Crawford Boxes (315 ft) | Short left field porch |

---

## How Effects Are Applied

### 1. Game Initialization

```python
# In GameSimulator.__init__()
from .ballpark_effects import get_team_ballpark_effects

# Get ballpark effects for home team
effects = get_team_ballpark_effects(home_team.abbreviation)
if effects:
    self.altitude = effects.altitude_ft
    self.temperature = effects.avg_temperature_f
    self.humidity = effects.avg_humidity
```

### 2. Trajectory Physics

The altitude affects air density, which affects:
- **Drag force** - Less drag at altitude = more distance
- **Magnus force** - Less lift from spin at altitude

```python
# In Environment class
air_density = calculate_air_density(altitude, temperature, humidity)
# Lower density at Coors = balls fly farther
```

### 3. Home Run Detection

```python
# In play_simulation.py
from .ballpark import get_ballpark

ballpark_obj = get_ballpark(self.ballpark)
fence_distance, fence_height = ballpark_obj.get_fence_at_angle(spray_angle)

# Check if ball cleared the fence
if distance_ft >= fence_distance:
    height_at_fence = batted_ball_result.get_height_at_distance(fence_distance)
    if height_at_fence > fence_height:
        is_home_run = True
```

---

## Team-to-Ballpark Mapping

### Automatic Assignment

When loading teams from the database, the `team_loader.py` automatically assigns the correct home ballpark:

```python
# Team abbreviation → Ballpark mapping
TEAM_BALLPARK_MAP = {
    "BAL": "camden", "BOS": "fenway", "NYY": "yankee",
    "TB": "steinbrenner", "TOR": "rogers",
    "CHW": "rate", "CLE": "progressive", "DET": "comerica",
    # ... all 30 teams
    "COL": "coors",  # The thin air advantage!
    # ...
}
```

### Viewing Team Ballpark

```bash
python manage_teams.py --action list
```

Output includes:
```
Team: Colorado Rockies (COL)
  Home Ballpark: Coors Field
  Altitude: 5280 ft | Temperature: 70°F
  Park Factor (Runs): 1.15
```

---

## Coors Field: The Extreme Example

Coors Field demonstrates the maximum ballpark effect:

```python
"coors": BallparkEffects(
    name="Coors Field",
    altitude_ft=5280,           # Mile high!
    avg_temperature_f=70,
    avg_humidity=0.35,          # Very dry
    park_factor_runs=1.15,      # 15% more runs
    park_factor_hr=1.25,        # 25% more home runs
    distance_modifier=1.08,     # 8% more distance
)
```

### Physics at Altitude

At 5,280 feet:
- Air density is ~17% lower than sea level
- Reduced drag = balls travel ~8-10% farther
- Breaking balls break less (less Magnus force)
- Fly balls that are warning track elsewhere become HRs

### Validation Test

```python
# From validation.py - must pass!
"Coors Field altitude effect"
Expected: 30.0 ± 10.0 ft additional distance
Actual: 29.1 ft ✓
```

---

## Usage Examples

### Get Ballpark for a Team

```python
from batted_ball.ballpark_effects import get_ballpark_for_team, get_team_ballpark_effects

# Get ballpark name
park_name = get_ballpark_for_team("COL")  # Returns "coors"

# Get full effects
effects = get_team_ballpark_effects("BOS")
print(f"Fenway altitude: {effects.altitude_ft} ft")
print(f"HR park factor: {effects.park_factor_hr}")
```

### Simulate with Specific Ballpark

```python
from batted_ball import GameSimulator

# Ballpark is set based on home team
game = GameSimulator(away_team, home_team)  # Uses home_team's park

# Or specify explicitly
game = GameSimulator(away_team, home_team, ballpark="coors")
```

### Get Fence at Any Angle

```python
from batted_ball.ballpark import get_ballpark

fenway = get_ballpark("fenway")

# Left field line (Green Monster)
dist, height = fenway.get_fence_at_angle(-45)
print(f"Green Monster: {dist} ft, {height} ft high")  # 309 ft, 37 ft

# Right field line (Pesky Pole)
dist, height = fenway.get_fence_at_angle(45)
print(f"Pesky Pole: {dist} ft, {height} ft high")  # 299 ft, 5 ft
```

---

## Data Sources

- **Fence dimensions**: MLB official stadium specifications, Baseball Savant 2025
- **Altitudes**: USGS elevation data
- **Park factors**: FanGraphs park factors (3-year rolling average)
- **Weather data**: Historical game-time averages from Weather Underground

---

## Coordinate System Note

**Important**: The spray angle convention in `ballpark.py` uses **field coordinates**:

| Spray Angle | Direction |
|-------------|-----------|
| Negative (-) | LEFT field |
| Zero (0) | CENTER field |
| Positive (+) | RIGHT field |

See `docs/COORDINATE_SYSTEMS.md` for full details on coordinate conventions.

---

## Future Enhancements

Potential additions for future versions:

1. **Wind effects per park** - Wrigley's wind patterns, Oracle's marine layer
2. **Day/Night splits** - Temperature variations affect ball flight
3. **Seasonal adjustments** - April in Minnesota vs. August in Arizona
4. **Roof status** - Open vs. closed for retractable roofs
5. **Humidity effects on grip** - Affects pitch movement
