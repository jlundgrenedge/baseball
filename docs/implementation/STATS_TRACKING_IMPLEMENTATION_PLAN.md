# Statistics Tracking & Persistence Implementation Plan

**Version**: 1.0 | **Created**: 2025-12-01

## Overview

This document outlines the implementation plan for comprehensive statistical tracking during 2025 MLB season simulations. The goal is to accumulate and persist player and team statistics across multiple simulation runs, enabling historical analysis and Baseball-Reference-style reporting.

## Design Philosophy

### Storage Decision: SQLite + JSON Hybrid

After evaluating options, we recommend a **SQLite database** for structured stats with **JSON files** for play-by-play details:

| Aspect | SQLite | JSON Files | Our Approach |
|--------|--------|------------|--------------|
| **Read speed** | Fast (indexed queries) | Moderate | SQLite for stats |
| **Write speed** | Fast (batch inserts) | Very fast (append) | SQLite with batching |
| **Querying** | SQL (powerful) | Manual parsing | SQLite for aggregates |
| **Flexibility** | Schema-bound | Schema-free | JSON for play-by-play |
| **Size** | Compact | Larger | SQLite for efficiency |
| **Concurrency** | Good with WAL mode | File locks needed | SQLite WAL mode |

**Location**: `saved_stats/season_stats.db` (SQLite) + `saved_stats/play_by_play/` (JSON)

---

## Phase 1: Foundation - Play Notation & Box Scores

**Goal**: Create a scorekeeping system that tracks plays using standard baseball notation.

### 1.1 Play Notation System

Create a `Scorekeeper` class that translates simulation events into standard baseball notation:

```python
# Standard baseball scoring notation
# Positions: 1=P, 2=C, 3=1B, 4=2B, 5=3B, 6=SS, 7=LF, 8=CF, 9=RF
# 
# Examples:
#   "K"       - Strikeout swinging
#   "ꓘ"       - Strikeout looking
#   "BB"      - Walk
#   "1B"      - Single
#   "2B"      - Double  
#   "3B"      - Triple
#   "HR"      - Home run
#   "F9"      - Fly out to right field
#   "L7"      - Line out to left field
#   "G6-3"    - Ground out, shortstop to first base
#   "DP 4-6-3" - Double play, 2B to SS to 1B
#   "E6"      - Error by shortstop
#   "FC"      - Fielder's choice
```

**File**: `batted_ball/scorekeeper.py`

```python
@dataclass
class PlayNotation:
    """A single play recorded in baseball notation."""
    notation: str           # e.g., "G6-3", "HR", "K"
    description: str        # Human-readable description
    batter_id: str          # Player ID
    pitcher_id: str         # Player ID
    runners_advanced: Dict[int, int]  # {from_base: to_base}
    runs_scored: int
    rbi: int
    outs_recorded: int
    
@dataclass
class InningLog:
    """All plays in a half-inning."""
    inning: int
    is_top: bool
    plays: List[PlayNotation]
    runs: int
    hits: int
    errors: int
    left_on_base: int

@dataclass
class GameLog:
    """Complete game record with all plays."""
    game_id: str
    date: date
    away_team: str
    home_team: str
    innings: List[InningLog]
    final_score: Tuple[int, int]  # (away, home)
    
    # Line score
    away_line: List[int]  # Runs per inning
    home_line: List[int]
    
    # Box score stats
    away_batting: List[PlayerGameBatting]
    home_batting: List[PlayerGameBatting]
    away_pitching: List[PlayerGamePitching]
    home_pitching: List[PlayerGamePitching]
```

### 1.2 Mapping Simulation Events to Notation

Hook into `PlayResult` and `AtBatResult` to generate notation:

```python
def play_result_to_notation(
    play_result: PlayResult,
    at_bat_result: AtBatResult,
    primary_fielder_position: int,
    relay_positions: List[int] = None
) -> str:
    """
    Convert a play result to standard notation.
    
    Examples:
    - Fly out to CF: "F8"
    - Ground out SS to 1B: "G6-3" 
    - Double play 2B-SS-1B: "DP 4-6-3"
    - Single to RF: "1B 9"
    - Home run to LF: "HR 7"
    """
```

### 1.3 Box Score Data Structures

```python
@dataclass
class PlayerGameBatting:
    """A single player's batting line for one game."""
    player_id: str
    player_name: str
    position: str
    order: int  # Batting order (1-9)
    
    # Standard box score stats
    at_bats: int = 0
    runs: int = 0
    hits: int = 0
    rbi: int = 0
    walks: int = 0
    strikeouts: int = 0
    
    # Extended stats
    doubles: int = 0
    triples: int = 0
    home_runs: int = 0
    stolen_bases: int = 0
    caught_stealing: int = 0
    hit_by_pitch: int = 0
    sacrifice_flies: int = 0
    sacrifice_bunts: int = 0
    gidp: int = 0  # Grounded into double play
    left_on_base: int = 0
    
    # Physics-based metrics
    exit_velocities: List[float] = field(default_factory=list)
    launch_angles: List[float] = field(default_factory=list)

@dataclass
class PlayerGamePitching:
    """A single pitcher's line for one game."""
    player_id: str
    player_name: str
    
    # Standard box score stats
    innings_pitched: float  # e.g., 6.1 = 6⅓ innings
    hits_allowed: int = 0
    runs_allowed: int = 0
    earned_runs: int = 0
    walks: int = 0
    strikeouts: int = 0
    home_runs_allowed: int = 0
    
    # Decision
    win: bool = False
    loss: bool = False
    save: bool = False
    hold: bool = False
    blown_save: bool = False
    
    # Pitch counts
    pitches: int = 0
    strikes: int = 0
    balls: int = 0
    
    # Extended stats
    batters_faced: int = 0
    ground_balls: int = 0
    fly_balls: int = 0
    line_drives: int = 0
```

### 1.4 Implementation Tasks

| Task | Priority | Effort | Notes |
|------|----------|--------|-------|
| Create `scorekeeper.py` with PlayNotation | HIGH | 2 hours | Core notation system |
| Create notation mapping from PlayResult | HIGH | 3 hours | Convert sim events → notation |
| Create box score data structures | HIGH | 1 hour | PlayerGameBatting, PlayerGamePitching |
| Hook into GameSimulator to record plays | HIGH | 3 hours | Capture each play during sim |
| Create GameLog aggregation | MEDIUM | 2 hours | Combine innings → game |
| Unit tests for notation | MEDIUM | 2 hours | Verify correct notation |

---

## Phase 2: Database Schema & Persistence

**Goal**: Create SQLite database for persisting stats across simulation runs.

### 2.1 Database Schema

**File**: `saved_stats/season_stats.db`

```sql
-- Simulation sessions (each run of the simulator)
CREATE TABLE simulation_sessions (
    session_id TEXT PRIMARY KEY,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    season INTEGER,
    start_date DATE,
    end_date DATE,
    games_simulated INTEGER,
    description TEXT
);

-- Game results (one row per game)
CREATE TABLE games (
    game_id TEXT PRIMARY KEY,
    session_id TEXT REFERENCES simulation_sessions(session_id),
    game_date DATE,
    away_team TEXT,
    home_team TEXT,
    away_score INTEGER,
    home_score INTEGER,
    innings INTEGER,
    attendance INTEGER,
    weather TEXT,
    ballpark TEXT,
    UNIQUE(session_id, game_date, away_team, home_team)
);

-- Player batting stats per game
CREATE TABLE player_game_batting (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    game_id TEXT REFERENCES games(game_id),
    player_id TEXT,
    player_name TEXT,
    team TEXT,
    batting_order INTEGER,
    position TEXT,
    
    -- Standard stats
    plate_appearances INTEGER DEFAULT 0,
    at_bats INTEGER DEFAULT 0,
    runs INTEGER DEFAULT 0,
    hits INTEGER DEFAULT 0,
    doubles INTEGER DEFAULT 0,
    triples INTEGER DEFAULT 0,
    home_runs INTEGER DEFAULT 0,
    rbi INTEGER DEFAULT 0,
    walks INTEGER DEFAULT 0,
    strikeouts INTEGER DEFAULT 0,
    hit_by_pitch INTEGER DEFAULT 0,
    sacrifice_flies INTEGER DEFAULT 0,
    sacrifice_bunts INTEGER DEFAULT 0,
    stolen_bases INTEGER DEFAULT 0,
    caught_stealing INTEGER DEFAULT 0,
    gidp INTEGER DEFAULT 0,
    
    -- Physics metrics (stored as averages for the game)
    avg_exit_velocity REAL,
    avg_launch_angle REAL,
    max_exit_velocity REAL,
    hard_hit_count INTEGER DEFAULT 0,  -- 95+ mph
    barrel_count INTEGER DEFAULT 0,
    
    UNIQUE(game_id, player_id)
);

-- Player pitching stats per game
CREATE TABLE player_game_pitching (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    game_id TEXT REFERENCES games(game_id),
    player_id TEXT,
    player_name TEXT,
    team TEXT,
    
    -- Standard stats
    innings_pitched REAL DEFAULT 0,
    hits_allowed INTEGER DEFAULT 0,
    runs_allowed INTEGER DEFAULT 0,
    earned_runs INTEGER DEFAULT 0,
    walks INTEGER DEFAULT 0,
    strikeouts INTEGER DEFAULT 0,
    home_runs_allowed INTEGER DEFAULT 0,
    
    -- Decision
    win INTEGER DEFAULT 0,
    loss INTEGER DEFAULT 0,
    save INTEGER DEFAULT 0,
    hold INTEGER DEFAULT 0,
    blown_save INTEGER DEFAULT 0,
    
    -- Pitch counts
    pitches INTEGER DEFAULT 0,
    strikes INTEGER DEFAULT 0,
    balls INTEGER DEFAULT 0,
    
    -- Batted ball types against
    ground_balls INTEGER DEFAULT 0,
    fly_balls INTEGER DEFAULT 0,
    line_drives INTEGER DEFAULT 0,
    
    UNIQUE(game_id, player_id)
);

-- Aggregated season batting stats (computed from game stats)
CREATE TABLE player_season_batting (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    session_id TEXT REFERENCES simulation_sessions(session_id),
    player_id TEXT,
    player_name TEXT,
    team TEXT,
    
    -- Aggregated stats
    games INTEGER DEFAULT 0,
    plate_appearances INTEGER DEFAULT 0,
    at_bats INTEGER DEFAULT 0,
    runs INTEGER DEFAULT 0,
    hits INTEGER DEFAULT 0,
    doubles INTEGER DEFAULT 0,
    triples INTEGER DEFAULT 0,
    home_runs INTEGER DEFAULT 0,
    rbi INTEGER DEFAULT 0,
    walks INTEGER DEFAULT 0,
    strikeouts INTEGER DEFAULT 0,
    stolen_bases INTEGER DEFAULT 0,
    caught_stealing INTEGER DEFAULT 0,
    
    -- Calculated rates (updated periodically)
    batting_avg REAL,
    on_base_pct REAL,
    slugging_pct REAL,
    ops REAL,
    babip REAL,
    
    -- Physics metrics
    avg_exit_velocity REAL,
    avg_launch_angle REAL,
    hard_hit_pct REAL,
    barrel_pct REAL,
    
    UNIQUE(session_id, player_id)
);

-- Aggregated season pitching stats
CREATE TABLE player_season_pitching (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    session_id TEXT REFERENCES simulation_sessions(session_id),
    player_id TEXT,
    player_name TEXT,
    team TEXT,
    
    -- Aggregated stats
    games INTEGER DEFAULT 0,
    games_started INTEGER DEFAULT 0,
    innings_pitched REAL DEFAULT 0,
    wins INTEGER DEFAULT 0,
    losses INTEGER DEFAULT 0,
    saves INTEGER DEFAULT 0,
    holds INTEGER DEFAULT 0,
    
    hits_allowed INTEGER DEFAULT 0,
    runs_allowed INTEGER DEFAULT 0,
    earned_runs INTEGER DEFAULT 0,
    walks INTEGER DEFAULT 0,
    strikeouts INTEGER DEFAULT 0,
    home_runs_allowed INTEGER DEFAULT 0,
    
    -- Calculated rates
    era REAL,
    whip REAL,
    k_per_9 REAL,
    bb_per_9 REAL,
    hr_per_9 REAL,
    k_bb_ratio REAL,
    
    -- Batted ball rates
    ground_ball_pct REAL,
    fly_ball_pct REAL,
    line_drive_pct REAL,
    
    UNIQUE(session_id, player_id)
);

-- Team standings per session
CREATE TABLE team_standings (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    session_id TEXT REFERENCES simulation_sessions(session_id),
    team TEXT,
    league TEXT,
    division TEXT,
    
    wins INTEGER DEFAULT 0,
    losses INTEGER DEFAULT 0,
    runs_scored INTEGER DEFAULT 0,
    runs_allowed INTEGER DEFAULT 0,
    home_wins INTEGER DEFAULT 0,
    home_losses INTEGER DEFAULT 0,
    away_wins INTEGER DEFAULT 0,
    away_losses INTEGER DEFAULT 0,
    
    UNIQUE(session_id, team)
);

-- Indexes for fast queries
CREATE INDEX idx_games_session ON games(session_id);
CREATE INDEX idx_games_date ON games(game_date);
CREATE INDEX idx_batting_game ON player_game_batting(game_id);
CREATE INDEX idx_batting_player ON player_game_batting(player_id);
CREATE INDEX idx_pitching_game ON player_game_pitching(game_id);
CREATE INDEX idx_pitching_player ON player_game_pitching(player_id);
CREATE INDEX idx_season_batting_session ON player_season_batting(session_id);
CREATE INDEX idx_season_pitching_session ON player_season_pitching(session_id);
```

### 2.2 Stats Database Manager

**File**: `batted_ball/stats_database.py`

```python
class StatsDatabase:
    """
    Manages reading/writing simulation statistics to SQLite.
    
    Usage:
        db = StatsDatabase()
        session_id = db.create_session(season=2025, description="April simulation")
        
        # After each game
        db.save_game(session_id, game_result, batting_stats, pitching_stats)
        
        # Get aggregated stats
        batting_leaders = db.get_batting_leaders(session_id, stat='home_runs', limit=10)
    """
    
    def __init__(self, db_path: str = "saved_stats/season_stats.db"):
        ...
    
    # Session management
    def create_session(self, season: int, description: str = "") -> str:
        """Create a new simulation session, returns session_id."""
        
    def get_sessions(self) -> List[Dict]:
        """List all simulation sessions."""
        
    def get_session_summary(self, session_id: str) -> Dict:
        """Get summary stats for a session."""
    
    # Game saving
    def save_game(
        self,
        session_id: str,
        game_result: GameResult,
        away_batting: List[PlayerGameBatting],
        home_batting: List[PlayerGameBatting],
        away_pitching: List[PlayerGamePitching],
        home_pitching: List[PlayerGamePitching]
    ):
        """Save a complete game with all player stats."""
    
    def save_games_batch(self, session_id: str, games: List[...]):
        """Batch save multiple games for performance."""
    
    # Aggregation
    def update_season_stats(self, session_id: str):
        """Recompute season aggregates from game stats."""
    
    # Querying
    def get_batting_leaders(
        self, 
        session_id: str, 
        stat: str = 'home_runs',
        min_pa: int = 0,
        limit: int = 10
    ) -> List[Dict]:
        """Get batting leaderboard for a stat."""
    
    def get_pitching_leaders(
        self,
        session_id: str,
        stat: str = 'strikeouts',
        min_ip: float = 0,
        limit: int = 10
    ) -> List[Dict]:
        """Get pitching leaderboard for a stat."""
    
    def get_player_game_log(
        self,
        session_id: str,
        player_id: str
    ) -> List[Dict]:
        """Get all game stats for a player."""
    
    def get_team_stats(self, session_id: str, team: str) -> Dict:
        """Get aggregated team statistics."""
```

### 2.3 Implementation Tasks

| Task | Priority | Effort | Notes |
|------|----------|--------|-------|
| Create database schema | HIGH | 1 hour | SQL file + initialization |
| Implement StatsDatabase class | HIGH | 4 hours | CRUD operations |
| Add batch insert for games | HIGH | 2 hours | Performance optimization |
| Create session management | MEDIUM | 1 hour | Track simulation runs |
| Add aggregation queries | MEDIUM | 2 hours | Season stats from games |
| Add leaderboard queries | MEDIUM | 2 hours | Top N players |
| WAL mode for concurrency | LOW | 30 min | Enable write-ahead logging |

---

## Phase 3: Integration with Season Simulator

**Goal**: Connect the stats tracking to the existing SeasonSimulator.

### 3.1 Modify SeasonSimulator

Add stats tracking to `season_simulator.py`:

```python
class SeasonSimulator:
    def __init__(self, ..., track_stats: bool = True, stats_db_path: str = None):
        self.track_stats = track_stats
        if track_stats:
            self.stats_db = StatsDatabase(stats_db_path or "saved_stats/season_stats.db")
            self.session_id = None
            self.scorekeeper = Scorekeeper()
    
    def simulate_range(self, start_date, end_date, session_name: str = None):
        """Enhanced to track stats."""
        if self.track_stats:
            self.session_id = self.stats_db.create_session(
                season=2025,
                description=session_name or f"Simulation {start_date} to {end_date}"
            )
        
        # ... existing simulation logic ...
        
        # After each day, batch save games
        if self.track_stats:
            self._save_day_stats(day_results)
    
    def _save_day_stats(self, results: List[GameResult]):
        """Save all game stats from a day."""
        for result in results:
            self.stats_db.save_game(
                self.session_id,
                result,
                result.away_batting_stats,
                result.home_batting_stats,
                result.away_pitching_stats,
                result.home_pitching_stats
            )
```

### 3.2 Modify GameSimulator

Enhance `game_simulation.py` to track individual player stats:

```python
class GameSimulator:
    def __init__(self, ..., scorekeeper: Scorekeeper = None):
        self.scorekeeper = scorekeeper
        self.away_batting_stats: Dict[str, PlayerGameBatting] = {}
        self.home_batting_stats: Dict[str, PlayerGameBatting] = {}
        self.away_pitching_stats: Dict[str, PlayerGamePitching] = {}
        self.home_pitching_stats: Dict[str, PlayerGamePitching] = {}
    
    def _record_at_bat_stats(
        self,
        batter: Hitter,
        pitcher: Pitcher,
        at_bat_result: AtBatResult,
        play_result: PlayResult,
        is_away_batting: bool
    ):
        """Update player stats after each at-bat."""
        # Get or create batting stats for this player
        stats_dict = self.away_batting_stats if is_away_batting else self.home_batting_stats
        if batter.player_id not in stats_dict:
            stats_dict[batter.player_id] = PlayerGameBatting(
                player_id=batter.player_id,
                player_name=batter.name,
                ...
            )
        
        stats = stats_dict[batter.player_id]
        
        # Update based on outcome
        outcome = at_bat_result.outcome
        if outcome == "strikeout":
            stats.strikeouts += 1
            stats.at_bats += 1
        elif outcome == "walk":
            stats.walks += 1
        elif outcome == "in_play":
            # Use play_result to determine hit type
            ...
        
        # Record notation
        if self.scorekeeper:
            self.scorekeeper.record_play(...)
```

### 3.3 Modify Worker Function

Update `_simulate_game_worker` to return player stats:

```python
@dataclass
class DetailedGameResult(GameResult):
    """Extended game result with player-level stats."""
    away_batting_stats: List[PlayerGameBatting] = field(default_factory=list)
    home_batting_stats: List[PlayerGameBatting] = field(default_factory=list)
    away_pitching_stats: List[PlayerGamePitching] = field(default_factory=list)
    home_pitching_stats: List[PlayerGamePitching] = field(default_factory=list)
    play_by_play: Optional[List[PlayNotation]] = None
```

### 3.4 Implementation Tasks

| Task | Priority | Effort | Notes |
|------|----------|--------|-------|
| Add stats tracking to GameSimulator | HIGH | 4 hours | Per-player stat accumulation |
| Create DetailedGameResult | HIGH | 1 hour | Extended result class |
| Hook into at_bat outcomes | HIGH | 3 hours | Connect outcomes → stats |
| Modify worker function | HIGH | 2 hours | Return detailed stats |
| Add session management to SeasonSimulator | MEDIUM | 2 hours | Create/resume sessions |
| Batch save after each day | MEDIUM | 2 hours | Performance optimization |
| Add progress callback with stats | LOW | 1 hour | Show live stat updates |

---

## Phase 4: Reporting & Queries

**Goal**: Enable Baseball-Reference-style stat reports.

### 4.1 Report Generator

**File**: `batted_ball/stats_reports.py`

```python
class StatsReporter:
    """Generate formatted statistical reports."""
    
    def __init__(self, db: StatsDatabase):
        self.db = db
    
    def print_batting_leaders(
        self,
        session_id: str,
        stats: List[str] = ['home_runs', 'rbi', 'batting_avg', 'stolen_bases'],
        top_n: int = 10
    ):
        """Print formatted batting leaderboards."""
    
    def print_pitching_leaders(
        self,
        session_id: str,
        stats: List[str] = ['wins', 'era', 'strikeouts', 'saves'],
        top_n: int = 10
    ):
        """Print formatted pitching leaderboards."""
    
    def print_player_season(self, session_id: str, player_id: str):
        """Print a player's full season stats."""
    
    def print_team_roster_stats(self, session_id: str, team: str):
        """Print all player stats for a team."""
    
    def export_to_csv(self, session_id: str, output_dir: str):
        """Export all stats to CSV files."""
    
    def generate_html_report(self, session_id: str, output_path: str):
        """Generate an HTML report with stats tables."""
```

### 4.2 Streamlit Integration

Add to `app.py`:

```python
def display_season_stats():
    """Display accumulated season statistics."""
    st.header("📊 Season Statistics")
    
    db = StatsDatabase()
    sessions = db.get_sessions()
    
    if not sessions:
        st.warning("No simulation sessions found. Run a season simulation first.")
        return
    
    # Session selector
    session = st.selectbox("Select Session", sessions, format_func=lambda x: x['description'])
    
    # Tabs for different views
    tab1, tab2, tab3, tab4 = st.tabs(["Batting", "Pitching", "Teams", "Game Logs"])
    
    with tab1:
        display_batting_leaders(db, session['session_id'])
    
    with tab2:
        display_pitching_leaders(db, session['session_id'])
    
    with tab3:
        display_team_stats(db, session['session_id'])
    
    with tab4:
        display_game_logs(db, session['session_id'])
```

### 4.3 Implementation Tasks

| Task | Priority | Effort | Notes |
|------|----------|--------|-------|
| Create StatsReporter class | MEDIUM | 3 hours | Formatted output |
| Batting leaderboards | MEDIUM | 2 hours | Multiple stat categories |
| Pitching leaderboards | MEDIUM | 2 hours | Multiple stat categories |
| Player season view | MEDIUM | 2 hours | Full stat line |
| Team roster stats | MEDIUM | 2 hours | All players on team |
| CSV export | MEDIUM | 1 hour | Data export |
| Streamlit integration | MEDIUM | 4 hours | UI for viewing stats |
| HTML report generation | LOW | 3 hours | Static report output |

---

## Phase 5: Advanced Metrics (Future)

**Goal**: Calculate sabermetric stats like WAR, wRC+, FIP.

### 5.1 Advanced Metrics Calculator

```python
class AdvancedMetrics:
    """Calculate advanced sabermetric statistics."""
    
    def calculate_woba(self, batting_stats: PlayerSeasonBatting) -> float:
        """Calculate weighted on-base average."""
        # wOBA = (0.69×uBB + 0.72×HBP + 0.88×1B + 1.24×2B + 1.56×3B + 1.95×HR) / PA
    
    def calculate_wrc_plus(
        self,
        batting_stats: PlayerSeasonBatting,
        league_avg_woba: float,
        woba_scale: float,
        league_r_per_pa: float,
        park_factor: float = 1.0
    ) -> float:
        """Calculate wRC+ (weighted runs created plus)."""
    
    def calculate_fip(
        self,
        pitching_stats: PlayerSeasonPitching,
        fip_constant: float
    ) -> float:
        """Calculate Fielding Independent Pitching."""
        # FIP = ((13×HR)+(3×(BB+HBP))-(2×K))/IP + constant
    
    def calculate_war_batting(
        self,
        batting_stats: PlayerSeasonBatting,
        fielding_runs: float,
        position_adjustment: float,
        replacement_level: float,
        runs_per_win: float
    ) -> float:
        """Calculate position player WAR (simplified)."""
    
    def calculate_war_pitching(
        self,
        pitching_stats: PlayerSeasonPitching,
        league_era: float,
        replacement_level: float,
        runs_per_win: float
    ) -> float:
        """Calculate pitcher WAR (simplified)."""
```

### 5.2 League Constants

Store league-wide constants needed for advanced metrics:

```python
@dataclass
class LeagueConstants:
    """League-wide constants for a simulation session."""
    session_id: str
    
    # Offensive environment
    league_avg_woba: float
    woba_scale: float
    league_r_per_pa: float
    league_batting_avg: float
    league_obp: float
    league_slg: float
    
    # Pitching environment  
    league_era: float
    league_fip: float
    fip_constant: float  # Derived from ERA - FIP_raw
    
    # WAR constants
    runs_per_win: float  # Typically ~10
    replacement_level: float  # Wins expected from replacement player
    
    # Position adjustments (runs per 162 games)
    position_adjustments: Dict[str, float]  # {'C': 12.5, 'SS': 7.5, ...}
```

### 5.3 Implementation Tasks

| Task | Priority | Effort | Notes |
|------|----------|--------|-------|
| Create AdvancedMetrics class | LOW | 3 hours | Core calculations |
| Calculate league constants | LOW | 2 hours | From simulation data |
| wOBA calculation | LOW | 1 hour | Linear weights |
| wRC+ calculation | LOW | 2 hours | Park-adjusted |
| FIP calculation | LOW | 1 hour | Pitching metric |
| Simplified WAR | LOW | 3 hours | Approximate WAR |
| Add to database schema | LOW | 1 hour | Store advanced metrics |
| Add to reports | LOW | 2 hours | Display in leaderboards |

---

## Implementation Order & Timeline

### Phase 1: Foundation (Week 1) ✅ COMPLETE
- [x] Create `scorekeeper.py` with play notation
- [x] Create box score data structures
- [x] Hook into GameSimulator for play recording
- [x] Unit tests

### Phase 2: Database (Week 1-2) ✅ COMPLETE
- [x] Create database schema
- [x] Implement StatsDatabase class
- [x] Add batch insert operations
- [x] Add aggregation queries
- [x] Connect SeasonSimulator to stats database
- [x] Player-level stats captured in parallel processing

### Phase 3: Integration (Week 2) ✅ COMPLETE
- [x] Modify GameSimulator for player stats (StatsEnabledGameSimulator)
- [x] Create DetailedGameResult (GameResult with player_batting/pitching lists)
- [x] Modify SeasonSimulator for sessions (stats_db, stats_season_id params)
- [x] Connect stats saving to simulation loop

### Phase 4: Reporting (Week 3) ✅ COMPLETE
- [x] Create StatsReporter class (within StatsDatabase)
- [x] Batting/pitching leaderboards
- [x] Streamlit integration (Player Stats tab)
- [x] CSV/HTML export (export_batting_to_csv, export_pitching_to_csv, export_to_html)

### Phase 5: Advanced Stats ✅ COMPLETE
- [x] League constants calculation (LeagueConstants dataclass)
- [x] wOBA, wRC+ implementation (AdvancedStatsCalculator)
- [x] FIP, xFIP implementation
- [x] Simplified WAR (batting + pitching)
- [x] Advanced Stats tab in UI (WAR Leaders, wRC+, FIP)

---

## Performance Considerations

1. **Batch Writes**: Save games in batches (per day) rather than individually
2. **WAL Mode**: Enable SQLite WAL mode for better concurrency
3. **Indexed Queries**: Ensure indexes on commonly queried columns
4. **Lazy Aggregation**: Only compute season aggregates when requested
5. **Optional Detail**: Allow disabling play-by-play for faster simulation

```python
# Performance settings
class StatsTrackingMode(Enum):
    DISABLED = 0      # No stats tracking (fastest)
    BASIC = 1         # Team totals only
    STANDARD = 2      # Player game stats (recommended)
    DETAILED = 3      # + Play-by-play notation
    FULL = 4          # + Physics metrics for every batted ball
```

---

## File Structure

```
saved_stats/
├── season_stats.db          # SQLite database
├── play_by_play/            # JSON files for detailed logs (optional)
│   ├── 2025-04-01/
│   │   ├── NYY_vs_BOS.json
│   │   └── ...
│   └── ...
└── exports/                 # CSV/HTML exports
    └── ...

batted_ball/
├── scorekeeper.py           # NEW: Play notation system
├── stats_database.py        # NEW: SQLite operations
├── stats_reports.py         # NEW: Report generation
├── season_simulator.py      # MODIFIED: Add stats tracking
├── game_simulation.py       # MODIFIED: Add player stat collection
└── ...
```

---

## Success Criteria

1. **Accumulation**: Stats persist across simulation runs
2. **Accuracy**: Player totals match game-by-game sums
3. **Performance**: <5% overhead from stats tracking
4. **Queryability**: Can get leaderboards, game logs, player stats
5. **Baseball Notation**: Plays recorded in standard notation (6-3, F9, etc.)
6. **Box Scores**: Full box score data for each game
7. **Resumability**: Can continue a partially simulated season
