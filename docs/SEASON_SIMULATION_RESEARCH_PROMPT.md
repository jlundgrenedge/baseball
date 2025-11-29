# Deep Research Prompt: MLB Season Simulation & Statistical Tracking System

## Executive Summary

**Objective**: Design and implement a comprehensive **162-game MLB season simulation system** with full statistical tracking at team and individual levels, enabling validation of the physics engine against real MLB season outcomes.

**Current State**: The simulation engine can run individual games between MLB teams from the database, but lacks:
- Season scheduling (162-game balanced schedule)
- Persistent statistical accumulation across games
- Individual player stat tracking (batting, pitching, fielding)
- Team standings and rankings
- Advanced metrics calculation (WAR, wRC+, FIP, etc.)
- Season-level validation against real MLB data

**Target State**: Run a complete 162-game MLB season simulation with full statistical output comparable to Baseball-Reference or FanGraphs season data.

**Repository**: `jlundgrenedge/baseball` (GitHub)

---

## Background & Context

### What We Currently Have

The simulation engine models complete 9-inning games with physics-based outcomes. We have:

1. **MLB Database Integration** (`batted_ball/database/`)
   - Real player data via pybaseball
   - Hitter and pitcher attributes mapped to physics parameters
   - Team rosters from MLB

2. **Game Simulation** (`batted_ball/game_simulation.py`)
   - Full 9-inning games with realistic outcomes
   - Play-by-play logging
   - Basic game statistics (runs, hits, errors)

3. **Performance Infrastructure**
   - Rust acceleration (~6 seconds per game)
   - Parallel game simulation capability
   - Bulk simulation tools

4. **Existing Metrics** (`batted_ball/sim_metrics.py`, `batted_ball/series_metrics.py`)
   - Basic simulation metrics
   - Series-level aggregation
   - Some advanced stat calculations

### What We Need to Build

| Component | Description | Priority |
|-----------|-------------|----------|
| **Schedule Generator** | Create realistic 162-game MLB schedule | HIGH |
| **Season State Manager** | Track standings, stats across games | HIGH |
| **Individual Stat Tracker** | Batting, pitching, fielding stats per player | HIGH |
| **Team Stat Aggregator** | Team-level statistics and rankings | HIGH |
| **Advanced Metrics Engine** | WAR, wRC+, FIP, xwOBA, etc. | MEDIUM |
| **Validation Framework** | Compare sim output to real MLB seasons | MEDIUM |
| **Fatigue/Rest System** | Realistic pitcher usage patterns | MEDIUM |
| **Injury Simulation** | Optional roster dynamics | LOW |
| **Playoff Simulation** | Post-season bracket simulation | LOW |

---

## Key Files to Analyze

### Existing Infrastructure

| File | Lines | Description | Relevance |
|------|-------|-------------|-----------|
| `batted_ball/database/` | ~2,000+ | MLB player/team data | **Core data source** |
| `batted_ball/game_simulation.py` | 815+ | Game orchestration | **Integration point** |
| `batted_ball/sim_metrics.py` | ~400 | Simulation metrics | **Extend this** |
| `batted_ball/series_metrics.py` | ~300 | Series aggregation | **Extend this** |
| `batted_ball/parallel_game_simulation.py` | 605 | Multi-game execution | **Use for season** |
| `batted_ball/player.py` | ~500 | Player data structures | **Add stat tracking** |
| `batted_ball/at_bat.py` | 830 | At-bat outcomes | **Stat source** |
| `batted_ball/play_simulation.py` | ~600 | Play outcomes | **Stat source** |

### External Data Sources to Consider

| Source | Data Available | Integration Complexity |
|--------|----------------|------------------------|
| **pybaseball** | Already integrated - Statcast, player stats | LOW |
| **Retrosheet** | Historical schedules, game logs | MEDIUM |
| **Baseball-Reference** | Season stats for validation | MEDIUM (scraping) |
| **FanGraphs** | Advanced metrics, leaderboards | MEDIUM (scraping) |
| **MLB Stats API** | Official schedules, rosters | MEDIUM |

---

## Research Questions

### 1. Schedule Generation

**Question**: How should we generate a realistic 162-game MLB schedule?

A real MLB schedule has complex constraints:
- 30 teams in 2 leagues, 3 divisions each
- Balanced division play (76 games vs division rivals)
- Interleague play
- Home/away balance
- Travel considerations
- Series structure (2-4 game series)

Please analyze:
- Should we use historical schedules from Retrosheet/MLB?
- Should we generate synthetic schedules with proper constraints?
- What scheduling algorithms exist for sports leagues?
- How do we handle the 2023+ balanced schedule format?
- What's the minimum viable schedule for validation purposes?

**Suggested approach**:
```python
# Example schedule structure
class SeasonSchedule:
    def __init__(self, year: int):
        self.games: List[ScheduledGame] = []
        
    def generate_schedule(self, teams: List[Team]) -> None:
        """Generate 162-game schedule per team"""
        pass
        
class ScheduledGame:
    game_id: str
    date: datetime
    home_team: str
    away_team: str
    game_number: int  # For doubleheaders
```

### 2. Statistical Tracking Architecture

**Question**: What data structures should track statistics across a season?

We need to track:
- **Batting**: PA, AB, H, 2B, 3B, HR, RBI, R, BB, K, SB, CS, HBP, SF, GDP, AVG, OBP, SLG, OPS
- **Pitching**: G, GS, W, L, SV, HLD, IP, H, R, ER, HR, BB, K, ERA, WHIP, K/9, BB/9, HR/9
- **Fielding**: G, GS, Inn, PO, A, E, DP, FPct, RF, UZR (if possible)
- **Team**: W, L, RS, RA, Pythagorean W-L, run differential

Please analyze:
- What's the most efficient data structure for accumulating stats?
- Should stats be stored per-game and aggregated, or running totals?
- How do we handle splits (vs LHP/RHP, home/away, monthly)?
- What database/storage format should we use (SQLite, Parquet, JSON)?
- How do we ensure stats are correctly attributed (e.g., earned runs)?

**Suggested approach**:
```python
@dataclass
class BattingStats:
    pa: int = 0
    ab: int = 0
    hits: int = 0
    doubles: int = 0
    triples: int = 0
    home_runs: int = 0
    rbi: int = 0
    runs: int = 0
    walks: int = 0
    strikeouts: int = 0
    stolen_bases: int = 0
    caught_stealing: int = 0
    
    @property
    def avg(self) -> float:
        return self.hits / self.ab if self.ab > 0 else 0.0
    
    @property
    def obp(self) -> float:
        # (H + BB + HBP) / (AB + BB + HBP + SF)
        pass
```

### 3. Game Result Integration

**Question**: How do we capture all necessary statistics from each simulated game?

The current `GameResult` object has basic info, but we need detailed stat lines.

Please analyze:
- What additional data needs to be captured from `game_simulation.py`?
- How do we track individual plate appearances and their outcomes?
- How do we track pitch-by-pitch data for pitching stats?
- How do we attribute fielding plays to specific players?
- Should we create a detailed box score object?

**Suggested approach**:
```python
@dataclass
class DetailedGameResult:
    game_id: str
    home_team: str
    away_team: str
    final_score: Tuple[int, int]
    innings: int
    
    # Detailed stat lines
    home_batting: Dict[str, BattingGameLine]  # player_id -> stats
    away_batting: Dict[str, BattingGameLine]
    home_pitching: Dict[str, PitchingGameLine]
    away_pitching: Dict[str, PitchingGameLine]
    
    # Play-by-play for advanced analysis
    plays: List[PlayEvent]
```

### 4. Advanced Metrics Calculation

**Question**: How should we calculate advanced sabermetric statistics?

Key metrics needed:
- **Batting**: wRC+, wOBA, xwOBA, ISO, BABIP, BB%, K%, Hard Hit%, Barrel%
- **Pitching**: FIP, xFIP, SIERA, K-BB%, HR/FB%, GB%, SwStr%
- **Fielding**: UZR, DRS, OAA (if physics allows)
- **Value**: WAR (bWAR or fWAR methodology)

Please analyze:
- Which metrics can we calculate from our physics-based simulation?
- What league-average constants do we need (wOBA weights, FIP constant)?
- Should we use historical constants or calculate from sim output?
- How accurate can WAR be without proper replacement-level calibration?
- Can we calculate expected stats (xwOBA, xBA) from our batted ball physics?

**Suggested approach**:
```python
class AdvancedMetricsCalculator:
    def __init__(self, league_context: LeagueContext):
        self.woba_weights = self._calculate_woba_weights()
        self.fip_constant = self._calculate_fip_constant()
        
    def calculate_wrc_plus(self, player_stats: BattingStats) -> float:
        """Calculate wRC+ (weighted Runs Created Plus)"""
        pass
        
    def calculate_war(self, player: Player, stats: BattingStats) -> float:
        """Calculate Wins Above Replacement"""
        pass
```

### 5. Season State Management

**Question**: How do we manage the state of a full season simulation?

We need to track:
- Current standings (W-L, GB, division ranks)
- Player statistics (cumulative, splits)
- Team statistics
- Playoff picture / magic numbers
- Recent performance (last 10, streaks)

Please analyze:
- What's the best architecture for season state?
- Should we checkpoint state to disk for resume capability?
- How do we handle simulation interruption/restart?
- What summary views should be available during simulation?
- How do we efficiently query standings and leaderboards?

**Suggested approach**:
```python
class SeasonSimulator:
    def __init__(self, year: int, teams: List[Team]):
        self.schedule = SeasonSchedule(year)
        self.standings = Standings()
        self.player_stats = PlayerStatsRegistry()
        self.team_stats = TeamStatsRegistry()
        
    def simulate_game(self, game: ScheduledGame) -> DetailedGameResult:
        """Simulate one game and update all statistics"""
        pass
        
    def simulate_season(self, parallel: bool = True) -> SeasonResult:
        """Simulate entire 162-game season"""
        pass
        
    def get_standings(self) -> StandingsView:
        """Get current standings snapshot"""
        pass
        
    def get_player_leaderboard(self, stat: str, min_pa: int = 502) -> List[PlayerStatLine]:
        """Get leaderboard for a given statistic"""
        pass
```

### 6. Pitcher Usage & Rotation

**Question**: How should we model realistic pitcher usage patterns?

MLB teams use:
- 5-man starting rotation
- Bullpen roles (closer, setup, middle relief)
- Pitch count limits (~100 pitches for starters)
- Rest requirements (4+ days for starters)
- Matchup-based bullpen decisions

Please analyze:
- How do we implement starting rotation scheduling?
- How do we model bullpen usage decisions?
- Should we implement fatigue effects on performance?
- How do we handle injuries/IL stints?
- What data do we need from the database for roster construction?

**Suggested approach**:
```python
class PitchingRotationManager:
    def __init__(self, team: Team):
        self.starters = self._identify_starters()
        self.bullpen = self._identify_relievers()
        self.rotation_index = 0
        self.pitcher_fatigue: Dict[str, int] = {}  # Days since last appearance
        
    def get_starting_pitcher(self, game_date: datetime) -> Pitcher:
        """Get the scheduled starter for a game"""
        pass
        
    def get_reliever(self, situation: GameSituation) -> Optional[Pitcher]:
        """Select appropriate reliever for game situation"""
        pass
```

### 7. Validation Against Real MLB Data

**Question**: How do we validate that our season simulation produces realistic results?

Validation targets:
- **Team level**: Win distribution, run scoring, pythagorean records
- **Individual level**: Stat distributions match real leaderboards
- **League level**: Total HRs, batting average, ERA, K rate trends

Please analyze:
- What real MLB season data should we compare against?
- What statistical tests determine if distributions match?
- How do we account for year-to-year variation?
- What's an acceptable deviation from real outcomes?
- Should we compare to specific historical seasons or averages?

**Suggested approach**:
```python
class SeasonValidator:
    def __init__(self, sim_results: SeasonResult, real_season: int):
        self.sim = sim_results
        self.real = self._load_real_season_data(real_season)
        
    def validate_team_wins(self) -> ValidationResult:
        """Compare simulated W-L to actual"""
        pass
        
    def validate_stat_distributions(self, stat: str) -> ValidationResult:
        """Compare stat distribution using KS test"""
        pass
        
    def generate_validation_report(self) -> ValidationReport:
        """Comprehensive validation report"""
        pass
```

### 8. Performance Considerations

**Question**: How do we efficiently simulate an entire 30-team, 162-game season?

Total games per season: 2,430 games
At ~6 seconds/game: ~4 hours for one season
Target: Multiple seasons for statistical validation

Please analyze:
- Can we parallelize season simulation effectively?
- What's the memory footprint of full season state?
- Should we use database storage vs. in-memory?
- Can we run multiple independent seasons in parallel?
- What output format is most efficient for analysis?

**Suggested approach**:
```python
def simulate_multiple_seasons(
    n_seasons: int,
    year: int,
    parallel_games: bool = True,
    parallel_seasons: bool = True
) -> List[SeasonResult]:
    """Simulate multiple independent seasons for statistical validation"""
    pass
```

### 9. Output & Reporting

**Question**: What output formats and reports should we generate?

Desired outputs:
- Final standings (division, league, overall)
- Individual stat leaderboards (batting, pitching)
- Team statistics summary
- Award predictions (MVP, Cy Young, ROY)
- Playoff bracket results
- Comparison to real season outcomes

Please analyze:
- What file formats are best (CSV, JSON, Parquet, SQLite)?
- Should we generate Baseball-Reference-style pages?
- How do we visualize season results?
- What summary statistics are most valuable?
- Should we integrate with existing baseball analysis tools?

**Suggested approach**:
```python
class SeasonReporter:
    def __init__(self, results: SeasonResult):
        self.results = results
        
    def export_standings(self, format: str = 'csv') -> Path:
        pass
        
    def export_batting_leaders(self, min_pa: int = 502) -> Path:
        pass
        
    def export_pitching_leaders(self, min_ip: float = 162.0) -> Path:
        pass
        
    def generate_html_report(self) -> Path:
        """Generate comprehensive HTML season report"""
        pass
```

### 10. Replay & Historical Comparison

**Question**: Can we simulate historical seasons and compare to actual outcomes?

Use cases:
- Simulate 2023 season with 2023 rosters, compare to actual
- Run "what-if" scenarios (trades, injuries)
- Validate that sim produces realistic ranges

Please analyze:
- What historical data is available via pybaseball?
- How do we construct historical rosters?
- What's a fair comparison methodology?
- Can we isolate physics accuracy from roster accuracy?
- Should we use actual schedules or generated ones?

---

## Deliverables Requested

### 1. Architecture Design Document

- Complete system architecture for season simulation
- Data flow diagrams
- Class hierarchy and relationships
- Storage schema design

### 2. Statistical Tracking Specification

- Complete list of statistics to track
- Data structures for each stat category
- Aggregation and calculation methods
- Split tracking requirements

### 3. Implementation Roadmap

Prioritized development phases:
| Phase | Components | Estimated Effort |
|-------|------------|------------------|
| 1 | Schedule generator, basic season loop | 1 week |
| 2 | Individual stat tracking, box scores | 1 week |
| 3 | Standings, team stats, leaderboards | 1 week |
| 4 | Advanced metrics (wRC+, FIP, WAR) | 1-2 weeks |
| 5 | Validation framework | 1 week |
| 6 | Reporting & visualization | 1 week |

### 4. Data Model Specification

- Player statistics schema
- Team statistics schema
- Game result schema
- Season state schema

### 5. Validation Plan

- Metrics to validate
- Data sources for comparison
- Acceptable deviation thresholds
- Automated validation tests

### 6. Code Examples

For each major component:
- Detailed implementation approach
- Example code structures
- Integration patterns with existing codebase
- Test cases

---

## Constraints & Requirements

### Must Preserve

1. **Physics-first approach**: All outcomes emerge from physics, not probability tables
2. **Database compatibility**: Use existing MLB player database
3. **Performance**: Season simulation in reasonable time (<4 hours)
4. **Accuracy**: 7/7 validation tests must still pass

### Acceptable Tradeoffs

1. **Simplified scheduling**: Don't need exact historical schedules
2. **Approximate advanced metrics**: WAR doesn't need to match bWAR/fWAR exactly
3. **Simplified roster management**: No trades/injuries in first version
4. **Storage space**: Larger stat files are acceptable

### Integration Requirements

- Must integrate with existing `batted_ball/` module structure
- Must use existing `database/` for player data
- Should leverage existing `parallel_game_simulation.py`
- Should extend existing `sim_metrics.py` and `series_metrics.py`

---

## Expected Metrics Ranges (For Validation)

### Team-Level (Per 162 Games)

| Metric | Expected Range | Source |
|--------|----------------|--------|
| Wins | 40-120 | Historical |
| Runs Scored | 550-950 | Historical |
| Runs Allowed | 550-950 | Historical |
| Run Differential | -300 to +300 | Historical |

### League-Level (Full Season)

| Metric | Expected Range | Source |
|--------|----------------|--------|
| League AVG | .240-.270 | 2019-2023 |
| League OBP | .310-.340 | 2019-2023 |
| League SLG | .400-.450 | 2019-2023 |
| League ERA | 3.80-4.50 | 2019-2023 |
| K/9 (league) | 8.5-9.5 | 2019-2023 |
| HR/game | 1.0-1.4 | 2019-2023 |

### Individual Leaders (Typical)

| Category | Leader Range | Source |
|----------|--------------|--------|
| AVG leader | .320-.370 | Historical |
| HR leader | 45-60 | Historical |
| RBI leader | 120-150 | Historical |
| ERA leader | 1.80-2.50 | Historical |
| K leader | 280-350 | Historical |
| WAR leader | 8-12 | Historical |

---

## Appendix: Existing Relevant Code

### Current Game Result Structure
```python
# From game_simulation.py (approximate)
@dataclass
class GameResult:
    home_team: str
    away_team: str
    home_score: int
    away_score: int
    innings: int
    plays: List[str]  # Play-by-play text
```

### Current Metrics (sim_metrics.py)
```python
# Basic metrics currently available
- At-bat outcomes (H, K, BB, etc.)
- Batted ball characteristics (EV, LA, distance)
- Play outcomes (single, double, out, etc.)
```

### Database Integration
```python
# From database module
- get_team_roster(team_code) -> List[Player]
- get_hitter_attributes(player_id) -> HitterAttributes
- get_pitcher_attributes(player_id) -> PitcherAttributes
```

---

## Quick Start for Analysis

```bash
# Clone and setup
git clone https://github.com/jlundgrenedge/baseball.git
cd baseball
pip install -r requirements.txt

# Explore existing metrics
python -c "from batted_ball.sim_metrics import *; help(SimulationMetrics)"

# Run multi-game simulation for reference
python examples/simulate_db_teams.py

# Check database integration
python -c "from batted_ball.database import get_all_teams; print(get_all_teams())"
```

---

## Success Criteria

1. **Functional**: Can simulate complete 162-game MLB season for all 30 teams
2. **Statistical**: Output includes full batting, pitching, fielding statistics
3. **Validated**: Season outcomes fall within expected ranges vs. real MLB
4. **Performant**: Full season simulation completes in <4 hours
5. **Usable**: Clear output reports, exportable data, leaderboard queries
6. **Extensible**: Architecture supports future additions (playoffs, trades, injuries)

---

*Document Version: 1.0*  
*Created: 2025-11-29*  
*Purpose: Deep research prompt for MLB season simulation and statistical tracking system*
