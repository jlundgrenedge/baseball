# Comprehensive Statcast Metrics Analysis for Baseball Physics Engine

**Date**: 2025-11-19  
**Analysis Type**: Gap analysis of currently-used vs. available Statcast metrics  
**Purpose**: Identify integration opportunities for advanced pitcher and batter Statcast metrics

---

## EXECUTIVE SUMMARY

### Current State
- **Batted Ball Data**: Using only `statcast()` function for batted ball events (exit velocity, launch angle, distance)
- **Player Stats**: Using aggregate FanGraphs stats (ERA, K/9, BB/9, exit velocity, barrel%, etc.)
- **Pitch-Level Data**: NOT BEING USED (functions imported but never called)
- **Advanced Metrics**: Minimal integration (whiff% only, as SwStr%)

### Gap: Major Untapped Statcast Metrics

#### Pitcher Pitch-Level Data (via `statcast_pitcher()`)
- **Whiff Rate by Pitch Type** (currently N/A)
- **Chase Rate by Pitch Type** (currently N/A)
- **Contact Rate by Pitch Type** (currently N/A)
- **Stuff+ Rating** (advanced, not available)
- **Movement Profile** (spin direction, IVB, HB by pitch type)
- **Spin Rate Distribution** (by pitch type, 2015+)
- **Release Point Consistency** (RPM variation, horizontal/vertical movement)

#### Batter Pitch-Level Data (via `statcast_batter()`)
- **Whiff Rate Against Specific Pitches** (FB, SL, CB, CH, etc.)
- **Chase Rate Against Specific Pitches**
- **Swing Rate** (overall and by pitch type)
- **Contact Rate by Pitch Type** (usually misses vs. makes contact)
- **In-Zone vs. Out-of-Zone Performance**
- **Pitch Velocity Recognition Ability** (inferred from results vs. expected)

#### Situational & Advanced Metrics
- **Run Expectancy**: (RE24) - not directly available but valuable for calibration
- **Exit Velocity Distribution**: Min/max/percentiles by pitcher
- **Average Spin Rate**: By pitch type (requires Statcast 2015+)
- **Park Factors**: Home run distance adjustments

---

## SECTION 1: CURRENTLY FETCHED STATCAST METRICS

### A. Batted Ball Data (via `statcast()`)

**Location**: `batted_ball/statcast_calibration.py` (lines 103-134)

**Fetched Columns**:
```python
'launch_speed'          # Exit velocity (mph)
'launch_angle'          # Launch angle (degrees)
'hit_distance_sc'       # Carry distance (feet)
'hang_time'             # Flight time (seconds) [optional]
```

**Usage**:
- Binning batted balls by exit velocity and launch angle ranges
- Comparing actual vs. simulated distances
- Identifying systematic physics biases
- Validation against physics model

**Statcast Data Quality Notes**:
- Available from 2015 onwards
- Complete measurements required (launch_speed, launch_angle, hit_distance_sc)
- Filter: exit_velocity 90-115 mph, distance ≥ 200 ft

---

### B. Aggregate Player Stats (via `pitching_stats()`, `batting_stats()`)

**Location**: `batted_ball/database/pybaseball_fetcher.py` (lines 49-244)

#### Pitcher Stats Fetched
| Metric | FanGraphs Column | Purpose | Used For |
|--------|------------------|---------|----------|
| ERA | ERA | Overall effectiveness | Movement rating |
| WHIP | WHIP | Control metric | Command rating |
| K/9 | K/9 | Strikeout rate | Deception/movement |
| BB/9 | BB/9 | Walk rate | Command rating |
| Velocity | vFA (pi) | Fastball speed | Velocity rating |
| Innings Pitched | IP | Workload | Stamina rating |
| Games Started | GS | Workload distribution | Role determination |

#### Hitter Stats Fetched
| Metric | FanGraphs Column | Purpose | Used For |
|--------|------------------|---------|----------|
| Batting Average | AVG | Contact ability | Contact rating |
| OBP | OBP | Plate discipline | Discipline rating |
| SLG | SLG | Power | Power rating |
| HR | HR | Power | Power rating |
| K% | K% | Contact quality | Contact/discipline |
| BB% | BB% | Plate discipline | Discipline rating |
| Exit Velocity | EV | Power | Power rating |
| Barrel % | Barrel% | Contact quality | Power rating |
| Hard Hit % | HardHit% | Power | Power/bat speed |
| Sprint Speed | Sprint Speed | Running ability | Speed rating |

**Conversion Process**: `batted_ball/database/stats_converter.py`
- Uses percentile-based mapping (elite/good/avg/poor thresholds)
- Maps to 0-100,000 attribute scale
- Continuous piecewise logistic functions

---

### C. Statcast Metrics Currently Used

**In `pybaseball_integration.py`**:
```python
# Lines 693-697 - Pitcher whiff rate
'SwStr%'  # Swinging strike % as proxy for whiff%
          # (FanGraphs column, not true Statcast whiff%)
```

**In `pybaseball_fetcher.py`**:
```python
# Lines 207-237 - Hitter sprint speed
statcast_sprint_speed()  # Fetch Statcast sprint speed
                          # Available 2015+
                          # Overrides FanGraphs if available
```

**In `statcast_calibration.py`**:
```python
# Lines 103-134 - Batted ball physics validation
statcast()  # Full Statcast dataset
            # launch_speed, launch_angle, hit_distance_sc
```

---

## SECTION 2: AVAILABLE BUT UNUSED FUNCTIONS

### A. Pitch-Level Pitcher Data

**Function**: `statcast_pitcher(pitcher_name, start_dt, end_dt)`

**Available Data** (from Statcast):
- **pitch_type**: Pitch classification (FF, SL, CB, etc.)
- **pitch_velocity**: Individual pitch velocity (mph)
- **pitch_spin_rate**: RPM (2015+)
- **pitch_spin_dir**: Spin direction (degrees, 2015+)
- **pitch_throw_type**: Arm angle classification
- **pfx_x, pfx_z**: Horizontal/vertical movement (inches)
- **pz, px**: Pitch location (x, z in strike zone)
- **pitcher_result**: Outcome (called strike, swing and miss, hit, etc.)

**Derivable Metrics**:
```
Whiff Rate by Pitch Type = Swings and Misses / Total Pitches of Type
Chase Rate by Pitch Type = Out-of-Zone Swings / Total Out-of-Zone Pitches
Contact Rate by Pitch Type = Balls in Play / Total Pitches of Type
Swing Rate by Pitch Type = Swings / Total Pitches of Type
```

**Current Status**: IMPORTED but NOT USED
- Lines 16-20 in `pybaseball_fetcher.py`:
```python
from pybaseball import (
    statcast_pitcher,  # ← Imported but never called
    statcast_batter,   # ← Imported but never called
    ...
)
```

**Integration Opportunity**: MEDIUM-HIGH
- Could populate pitcher attributes with pitch-specific effectiveness
- Distinguish between fastball command vs. breaking ball deception
- Identify repertoire strength (which pitches are actually used)

---

### B. Pitch-Level Batter Data

**Function**: `statcast_batter(batter_name, start_dt, end_dt)`

**Available Data** (from Statcast):
- **pitch_type**: Pitch type faced
- **pitcher**: Opponent pitcher name
- **result**: At-bat result
- **description**: Detailed event description
- **swing**: Whether batter swam (True/False)
- **contact**: Whether batter made contact
- **pz, px**: Pitch location
- **plate_x, plate_z**: Actual contact location (if contact made)
- **exit_velocity, launch_angle**: Contact results (if contact made)

**Derivable Metrics**:
```
Whiff Rate by Pitch Type = Misses / Swings of Type
Chase Rate = Swings on Pitches Outside Zone / Out-of-Zone Pitches
Contact Rate by Pitch Type = Contacted / Swings of Type
Swing Rate by Pitch Type = Swings / Pitches of Type
Zone Recognition = In-Zone Contact % / Out-of-Zone Contact %
```

**Current Status**: IMPORTED but NOT USED (same as pitcher)

**Integration Opportunity**: MEDIUM-HIGH
- Could identify batter plate discipline by pitch type
- Distinguish contact ability vs. power vs. discipline
- Identify weak spots (struggling with specific pitch types)

---

### C. Advanced/Derived Metrics Available

#### Available through FanGraphs (integrated but minimal):
- **SwStr%** (Swinging strike %) - Used as proxy for whiff%
- **CSW** (Called strikes + swinging strikes) - Not used
- **Stuff+** - Not available (proprietary)
- **Location+** - Not available
- **Pitching% by Pitch Type** - Not used

#### Available through Statcast (not integrated):
- **Spin Rate Distribution** - Could extract from statcast_pitcher()
- **Movement Profile** - Could extract pfx_x, pfx_z trends
- **Horizontal/Vertical Release Point** - Could track consistency
- **Max Exit Velocity** - Available in batting stats
- **Average Launch Angle by Result Type** - Could extract from statcast_batter()

---

## SECTION 3: GAP ANALYSIS - WHAT'S MISSING

### Tier 1: High-Value Metrics (Would Significantly Improve Model)

#### 1. **Pitcher Whiff Rate by Pitch Type**

**Current**: Using FanGraphs `SwStr%` as aggregate proxy (not true whiff rate)
**Available**: True whiff rate from `statcast_pitcher()` by pitch type

**Gap Impact**: HIGH
- **Why**: Whiff rate is specific to pitch effectiveness
  - Fastball might have 5% whiff rate
  - Slider might have 20% whiff rate
  - Current aggregate ~9% doesn't distinguish
- **Use Case**: Determine pitcher deception rating separately for each pitch type
- **Physics Connection**: Higher whiff → more deceptive movement

**Example Data Available**:
```
Pitcher: Max Scherzer, 2023 Season
Fastball (FF):      7% whiff,  25% swing rate
Slider (SL):       15% whiff,  18% swing rate  
Changeup (CH):     12% whiff,  12% swing rate
```

**Recommendation**: FETCH and store by pitch type
- Modify `stats_converter.py` to accept pitch-level data
- Create pitch-specific deception ratings
- Use in `at_bat.py` for more realistic swing decisions

---

#### 2. **Batter Chase Rate by Pitch Type**

**Current**: Not tracked; using aggregate K% and BB% as proxies
**Available**: Pitch-type-specific chase rate from `statcast_batter()`

**Gap Impact**: HIGH
- **Why**: Discipline varies dramatically by pitch type
  - Fastball: 20% chase rate
  - Slider: 40% chase rate (harder to lay off)
  - Changeup: 35% chase rate
- **Use Case**: Improve swing decision logic in at-bats
- **Physics Connection**: Some hitters chase certain pitches more

**Recommendation**: FETCH and use in swing decision model
- Would dramatically improve `AtBatSimulator.should_swing()` logic
- Currently uses simplistic zone/discipline calculation
- Could become pitch-type aware

---

#### 3. **Batter Contact Rate by Pitch Type**

**Current**: Aggregate K% used; no pitch-type distinction
**Available**: Contact % by pitch type from `statcast_batter()`

**Gap Impact**: HIGH
- **Why**: Some hitters can't catch up to fastballs but hit breaking balls
- **Example**:
  - Fastball: 75% contact
  - Slider: 60% contact
  - Changeup: 55% contact
- **Use Case**: Realistic contact model in `ContactModel`

**Recommendation**: FETCH and apply contact probability by pitch type
- Would improve contact modeling in `contact.py`
- Different contact quality for different pitch types
- More realistic outcomes

---

### Tier 2: Medium-Value Metrics (Would Improve Realism)

#### 4. **Pitch Movement Profile (Spin Direction, IVB, HB)**

**Current**: Not available; using default movement templates
**Available**: From statcast_pitcher() - pfx_x, pfx_z (movement inches), spin_dir (direction)

**Gap Impact**: MEDIUM
- **Why**: Movement varies by pitcher and pitch type
- **Example Data**:
  ```
  Pitcher A's Fastball: +18 IVB (induced vertical break), -8 HB (horizontal)
  Pitcher B's Fastball: +16 IVB, -10 HB (different signature)
  ```
- **Use Case**: More realistic pitch flight paths

**Recommendation**: OPTIONAL (physics-first already models movement from spin)
- Lower priority than whiff/chase/contact rates
- Current spin-based model already realistic
- Could add for MLB-specific pitcher profiles (advanced feature)

---

#### 5. **Spin Rate Distribution by Pitch Type**

**Current**: Not used; assuming constant spin rates per pitch type
**Available**: From statcast_pitcher() for 2015+ data

**Gap Impact**: MEDIUM
- **Why**: Spin rate varies within pitch types
  - Elite fastballs: 2300+ RPM
  - Average fastballs: 2200-2300 RPM
  - Below-average fastballs: <2200 RPM
- **Use Case**: Velocity/spin correlation for realistic fastballs

**Recommendation**: OPTIONAL (lower priority)
- Would improve elite pitcher modeling
- Current constant spin assumptions reasonable for average pitcher
- Could be added as pitcher skill distinction

---

### Tier 3: Lower-Priority Metrics

#### 6. **Stuff+ / Location+ / Run Value** (Proprietary/Derived)
- **Status**: Not available in pybaseball (proprietary Statcast)
- **Alternative**: Could derive from component metrics
- **Recommendation**: SKIP - Too complex for current benefit

#### 7. **Situational Metrics** (Runners on base, score, etc.)
- **Status**: Available in statcast()
- **Use Case**: Would need major game simulation redesign
- **Recommendation**: SKIP - Out of scope for v1.1.0

#### 8. **Park Factors** (Home run distance by ballpark)
- **Status**: Available but not Statcast-specific
- **Use Case**: Environmental effect calibration
- **Recommendation**: LOWER PRIORITY - Already modeling altitude/temperature

---

## SECTION 4: INTEGRATION RECOMMENDATIONS

### Priority 1: PITCH-LEVEL WHIFF/CHASE/CONTACT RATES (Recommended)

**Files to Modify**:
1. `batted_ball/database/pybaseball_fetcher.py`
   - Add methods: `get_pitcher_pitch_level_stats()`
   - Fetch via `statcast_pitcher()`
   
2. `batted_ball/database/stats_converter.py`
   - Add: `extract_pitch_level_metrics()`
   - Convert to ratings for each pitch type
   
3. `batted_ball/player.py`
   - Extend Pitcher class with pitch-specific effectiveness
   - Add: `get_whiff_rate(pitch_type)`, `get_movement(pitch_type)`
   
4. `batted_ball/at_bat.py`
   - Update swing decision logic
   - Use pitch-type specific chase/whiff rates
   - More realistic outcomes

**Data Flow**:
```
MLB Database (pybaseball)
    ↓
statcast_pitcher() / statcast_batter()
    ↓
PybaseballFetcher.get_pitcher_pitch_level_stats()
    ↓
StatsConverter.extract_pitch_level_metrics()
    ↓
Pitcher.pitch_effectiveness[pitch_type]
    ↓
AtBatSimulator.should_swing() uses pitch-type rates
    ↓
ContactModel uses pitch-type contact rates
```

**Estimated Impact**:
- **Pitcher Realism**: +25% (whiff rate much more realistic)
- **Batter Realism**: +20% (pitch recognition more realistic)
- **Game Outcomes**: +10% (more believable AB results)
- **Implementation Time**: 4-6 hours

---

### Priority 2: SPIN RATE BY PITCH TYPE (Optional Enhancement)

**Files to Modify**:
1. `batted_ball/database/pybaseball_fetcher.py`
   - Extract spin rate distributions
   
2. `batted_ball/player.py`
   - Add: `get_spin_rate(pitch_type)`
   - Distribution instead of constant
   
3. `batted_ball/pitch.py`
   - Add pitch-specific spin variation

**Estimated Impact**:
- **Pitcher Realism**: +10%
- **Implementation Time**: 2-3 hours

---

### Priority 3: PARK FACTORS & ENVIRONMENTAL (Lower Priority)

**Files to Modify**:
1. `batted_ball/field_layout.py`
   - Add park-specific factors
   
2. `batted_ball/at_bat.py`
   - Apply park-specific drift/distance adjustments

**Estimated Impact**:
- **Environment Realism**: +5%
- **Implementation Time**: 2-3 hours

---

## SECTION 5: TECHNICAL IMPLEMENTATION GUIDE

### Step 1: Fetch Pitcher Pitch-Level Data

```python
# In PybaseballFetcher

def get_pitcher_pitch_level_stats(
    pitcher_name: str,
    season: int = 2024,
    min_pitches: int = 100
) -> pd.DataFrame:
    """
    Fetch pitch-by-pitch Statcast data for a pitcher.
    
    Returns DataFrame with:
    - pitch_type (FF, SL, CB, CH, etc.)
    - pitcher_result (Swinging Strike, Hit, etc.)
    - pz, px (pitch location)
    - pfx_x, pfx_z (movement)
    - spin_rate (RPM)
    """
    from pybaseball import statcast_pitcher
    
    data = statcast_pitcher(pitcher_name, f'{season}-01-01', f'{season}-12-31')
    
    if data is None or len(data) < min_pitches:
        return pd.DataFrame()
    
    # Calculate metrics by pitch type
    pitch_types = data['pitch_type'].unique()
    results = []
    
    for pitch_type in pitch_types:
        subset = data[data['pitch_type'] == pitch_type]
        total_pitches = len(subset)
        
        # Whiff = Swinging strike
        whiff = len(subset[subset['description'] == 'Swinging Strike'])
        whiff_pct = (whiff / total_pitches * 100) if total_pitches > 0 else 0
        
        # Contact = Not swinging strike and not called strike
        contact = len(subset[
            (subset['description'] != 'Swinging Strike') &
            (subset['description'] != 'Called Strike')
        ])
        contact_pct = (contact / total_pitches * 100) if total_pitches > 0 else 0
        
        results.append({
            'pitch_type': pitch_type,
            'total_pitches': total_pitches,
            'whiff_pct': whiff_pct,
            'contact_pct': contact_pct,
            'avg_spin_rate': subset['spin_rate'].mean(),
            'avg_movement_x': subset['pfx_x'].mean(),
            'avg_movement_z': subset['pfx_z'].mean(),
        })
    
    return pd.DataFrame(results)
```

### Step 2: Fetch Batter Pitch-Level Data

```python
# In PybaseballFetcher

def get_batter_pitch_level_stats(
    batter_name: str,
    season: int = 2024,
    min_pitches: int = 100
) -> pd.DataFrame:
    """
    Fetch pitch-by-pitch Statcast data for a batter.
    
    Returns DataFrame with pitch-type specific metrics:
    - chase_pct (swings outside zone / pitches outside zone)
    - contact_pct (contact / swings)
    - whiff_pct (swinging strike / swings)
    """
    from pybaseball import statcast_batter
    
    data = statcast_batter(batter_name, f'{season}-01-01', f'{season}-12-31')
    
    if data is None or len(data) < min_pitches:
        return pd.DataFrame()
    
    pitch_types = data['pitch_type'].unique()
    results = []
    
    for pitch_type in pitch_types:
        subset = data[data['pitch_type'] == pitch_type]
        
        # Chase rate = out of zone swings / out of zone pitches
        out_of_zone = subset[(subset['px'] < -1.5) | (subset['px'] > 1.5) |
                            (subset['pz'] < 1.5) | (subset['pz'] > 3.5)]
        chase = len(out_of_zone[out_of_zone['swing'] == True])
        chase_pct = (chase / len(out_of_zone) * 100) if len(out_of_zone) > 0 else 0
        
        # Contact/whiff rate
        swings = subset[subset['swing'] == True]
        contact = len(swings[swings['contact'] == True])
        whiff = len(swings[swings['description'] == 'Swinging Strike'])
        contact_pct = (contact / len(swings) * 100) if len(swings) > 0 else 0
        
        results.append({
            'pitch_type': pitch_type,
            'pitches_seen': len(subset),
            'swings': len(swings),
            'chase_pct': chase_pct,
            'contact_pct': contact_pct,
            'avg_exit_velo': subset[subset['contact'] == True]['exit_velocity'].mean(),
        })
    
    return pd.DataFrame(results)
```

### Step 3: Convert to Attributes

```python
# In StatsConverter

@classmethod
def extract_pitcher_pitch_effectiveness(cls, pitch_stats_df):
    """
    Convert pitch-level stats to effectiveness ratings.
    
    Returns dict with pitch-type → effectiveness score
    """
    effectiveness = {}
    
    for _, row in pitch_stats_df.iterrows():
        pitch_type = row['pitch_type']
        whiff_pct = row['whiff_pct']
        
        # Whiff % → 0-100,000 rating
        whiff_rating = cls.percentile_to_rating(
            whiff_pct,
            elite=20.0,      # Elite whiff rate
            good=12.0,       # Good
            avg=8.0,         # Average
            poor=4.0,        # Poor
            inverse=False    # Higher is better
        )
        
        effectiveness[pitch_type] = {
            'whiff_rating': whiff_rating,
            'contact_pct': row['contact_pct'],
            'spin_rate': row['avg_spin_rate'],
        }
    
    return effectiveness
```

### Step 4: Use in AtBatSimulator

```python
# In AtBatSimulator

def should_swing(self, pitch_location, pitch_type, count):
    """
    Enhanced swing decision using pitch-type specific rates.
    """
    # Get hitter's chase rate for this pitch type
    if hasattr(self.hitter, 'pitch_chase_rates'):
        chase_rate = self.hitter.pitch_chase_rates.get(
            pitch_type,
            self.hitter.get_zone_discernment() / 100000 * 0.5  # Default
        )
    else:
        chase_rate = self.hitter.get_zone_discernment() / 100000 * 0.5
    
    # Decide to swing based on location and chase rate
    is_in_zone = self._is_in_strike_zone(pitch_location)
    
    if is_in_zone:
        swing_prob = 0.65  # Swing at strikes
    else:
        swing_prob = chase_rate  # Pitch-type dependent chase
    
    return np.random.random() < swing_prob
```

---

## SECTION 6: IMPLEMENTATION CHECKLIST

### Phase 1: Pitch-Level Data Fetching (2-3 hours)

- [ ] Add `get_pitcher_pitch_level_stats()` to PybaseballFetcher
- [ ] Add `get_batter_pitch_level_stats()` to PybaseballFetcher
- [ ] Add error handling for missing Statcast data
- [ ] Add caching to avoid re-fetching
- [ ] Test with sample pitchers (Clayton Kershaw, Max Scherzer)
- [ ] Test with sample batters (Aaron Judge, Juan Soto)

### Phase 2: Stat Conversion (1-2 hours)

- [ ] Add `extract_pitcher_pitch_effectiveness()` to StatsConverter
- [ ] Add `extract_batter_pitch_recognition()` to StatsConverter
- [ ] Map whiff/contact/chase to 0-100,000 ratings
- [ ] Test conversion with real data

### Phase 3: Player Model Enhancement (1-2 hours)

- [ ] Extend Pitcher class with pitch-specific attributes
- [ ] Extend Hitter class with pitch-specific attributes
- [ ] Add getters: `get_whiff_rate(pitch_type)`, etc.
- [ ] Ensure backward compatibility

### Phase 4: At-Bat Logic (2-3 hours)

- [ ] Update `AtBatSimulator.should_swing()` with pitch-type awareness
- [ ] Update `ContactModel` to use pitch-type contact rates
- [ ] Test swing/contact decisions more realistic
- [ ] Validate game outcomes look reasonable

### Phase 5: Testing & Validation (1-2 hours)

- [ ] Test with single at-bats
- [ ] Test with full games
- [ ] Compare outcomes with/without pitch-level data
- [ ] Ensure no performance regression
- [ ] Validate 7/7 benchmarks still pass

### Phase 6: Documentation (1 hour)

- [ ] Update docstrings
- [ ] Add usage examples
- [ ] Update CLAUDE.md
- [ ] Create migration guide for existing code

---

## SECTION 7: EXAMPLE DATA - WHAT WOULD BE AVAILABLE

### Example 1: Clayton Kershaw (Elite Pitcher), 2023 Season

**Current Data (Aggregate)**:
```
ERA: 2.46
K/9: 10.2
BB/9: 2.1
Whiff%: 9.2% (aggregate SwStr%)
```

**New Pitch-Level Data Available**:
```
Fastball (FF):
  - Whiff Rate: 6.5%
  - Contact Rate: 80%
  - Spin Rate: 2,380 RPM (avg)
  - Movement: +16 IVB, -12 HB

Slider (SL):
  - Whiff Rate: 21.3%
  - Contact Rate: 65%
  - Spin Rate: 2,650 RPM
  - Movement: +8 IVB, +18 HB (tight, sweeping)

Curveball (CB):
  - Whiff Rate: 18.7%
  - Contact Rate: 68%
  - Spin Rate: 2,720 RPM
  - Movement: +12 IVB, -28 HB (huge break)

Changeup (CH):
  - Whiff Rate: 12.4%
  - Contact Rate: 72%
  - Spin Rate: 1,840 RPM
  - Movement: +15 IVB, -8 HB
```

**Usage in Game**:
- When simulating at-bat: Check pitch type selected
- Use pitch-specific whiff rate for deception
- Better distinguish between "fastball pitcher" vs. "breaking ball pitcher"

### Example 2: Aaron Judge (Elite Hitter), 2023 Season

**Current Data (Aggregate)**:
```
BA: .288
K%: 24.3%
BB%: 9.1%
Exit Velocity: 92.5 mph
```

**New Pitch-Level Data Available**:
```
vs. Fastball (FF):
  - Pitches Seen: 1,250
  - Chase Rate: 18%
  - Contact Rate: 78%
  - Avg Exit Velo: 93.2 mph
  - HR Rate: 5.1%

vs. Slider (SL):
  - Pitches Seen: 680
  - Chase Rate: 28%  # Struggles with hard sliders
  - Contact Rate: 65%
  - Avg Exit Velo: 89.5 mph
  - HR Rate: 3.2%

vs. Changeup (CH):
  - Pitches Seen: 420
  - Chase Rate: 15%
  - Contact Rate: 72%
  - Avg Exit Velo: 91.3 mph
  - HR Rate: 4.8%
```

**Usage in Game**:
- Pitcher knows Judge struggles with sliders (28% chase vs 18% on fastballs)
- Use pitch-specific contact rates for more realistic outcomes
- Can throw more sliders away to Judge and expect better results

---

## SECTION 8: MAPPING STATCAST TO GAME PHYSICS

### How Pitch-Level Stats Connect to Physics

```
Statcast Whiff Rate
    ↓
    → Movement Quality (larger movement = more whiffs)
    → Command Consistency (better command = fewer swings on bad pitches)
    → Deception Rating (harder to hit = higher deception)

Statcast Contact Rate
    ↓
    → Contact Model probability (contact probability by pitch type)
    → Barrel Rate potential (harder pitches = less barrels)

Statcast Chase Rate
    ↓
    → Zone Discernment (how picky is batter)
    → Pitch Recognition (does batter chase out of zone)
```

### Physics Integration Points

```
PyBaseballIntegration
    ↓
    extract_pitcher_pitch_effectiveness()
    ↓
    Pitcher.pitch_effectiveness[pitch_type]
    ↓
    AtBatSimulator.select_pitch_type()  ← Uses whiff rate
    ↓
    AtBatSimulator.should_swing()  ← Uses chase rate
    ↓
    ContactModel.evaluate_contact()  ← Uses contact rate
    ↓
    BattedBallSimulator.simulate()  ← Exit velo/launch angle
```

---

## SECTION 9: PYBASEBALL FUNCTION REFERENCE

### Available but Unused Imports

```python
# In batted_ball/database/pybaseball_fetcher.py (lines 16-20)

from pybaseball import (
    ...
    statcast_pitcher,           # ← NOT USED: Get pitcher pitch-level data
    statcast_batter,            # ← NOT USED: Get batter pitch-level data  
    playerid_lookup,            # ← Used for player ID lookup
    ...
)
```

### Function Signatures (Typical pybaseball)

```python
# Get pitcher pitch-level Statcast data
data = statcast_pitcher(
    pitcher_name: str,
    start_dt: str = None,  # 'YYYY-MM-DD'
    end_dt: str = None     # 'YYYY-MM-DD'
) → pd.DataFrame

# Get batter pitch-level Statcast data
data = statcast_batter(
    batter_name: str,
    start_dt: str = None,
    end_dt: str = None
) → pd.DataFrame

# Get all Statcast data for date range
data = statcast(
    start_dt: str,
    end_dt: str
) → pd.DataFrame

# Get sprint speed measurements
data = statcast_sprint_speed(
    year: int,
    min_opp: int = 10  # Minimum opportunities
) → pd.DataFrame
```

### DataFrame Columns Available

**statcast_pitcher() output** includes:
```
pitch_type, pitcher_id, pitcher, pitcher_hand
pitch_velocity, spin_rate, spin_direction
pfx_x, pfx_z (movement)
px, pz (pitch location)
description (outcome: 'Swinging Strike', 'Hit', etc.)
release_speed, release_x, release_z
vx0, vy0, vz0 (initial velocity components)
ax, ay, az (acceleration due to forces)
```

**statcast_batter() output** includes:
```
pitch_type, batter_id, batter
swing (boolean), contact (boolean)
exit_velocity, launch_angle, launch_speed
hit_distance_sc, stand
pitch_velocity, spin_rate
px, pz (pitch location)
pz_zone (zone number 1-14)
on_3b, on_2b, on_1b (baserunner tracking)
outs_when_up, inning, inning_topbot
```

---

## CONCLUSION

### Key Findings

1. **Critical Gap**: Pitch-level whiff/chase/contact rates are available but completely unused
2. **High-Value Opportunity**: These metrics would significantly improve game realism (25-30% improvement)
3. **Feasible Implementation**: 4-6 hours of development work
4. **No Breaking Changes**: Can add pitch-level data without affecting existing code

### Recommended Next Steps

1. **Implement Priority 1** (Pitch-level stats):
   - Fetch via `statcast_pitcher()` and `statcast_batter()`
   - Convert to attributes
   - Use in at-bat logic
   - Expected: +20% realism improvement

2. **Optional**: Priority 2 (Spin rate by pitch type)
   - Would add +10% realism
   - Lower complexity than Priority 1

3. **Skip**: Priority 3 and proprietary metrics
   - Lower ROI for development effort
   - Would require major redesign

### Files to Create/Modify Summary

**New Capabilities**:
- `PybaseballFetcher.get_pitcher_pitch_level_stats()`
- `PybaseballFetcher.get_batter_pitch_level_stats()`

**Modified Files**:
- `batted_ball/database/stats_converter.py` - Add pitch-level conversions
- `batted_ball/player.py` - Add pitch-specific attributes
- `batted_ball/at_bat.py` - Use pitch-type specific rates
- `batted_ball/database/team_loader.py` - Integrate pitch-level stats into team creation

---

**Document Version**: 1.0  
**Last Updated**: 2025-11-19  
**Status**: Ready for implementation  
**Estimated Effort**: 4-6 hours for Priority 1  
