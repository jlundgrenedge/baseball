"""
Baseball Scorekeeper Module

Provides standard baseball notation for recording plays, and data structures
for box scores and game logs. This enables Baseball-Reference-style statistical
tracking and reporting.

Standard Baseball Position Numbers:
    1 = Pitcher (P)
    2 = Catcher (C)
    3 = First Baseman (1B)
    4 = Second Baseman (2B)
    5 = Third Baseman (3B)
    6 = Shortstop (SS)
    7 = Left Fielder (LF)
    8 = Center Fielder (CF)
    9 = Right Fielder (RF)
    10 = Designated Hitter (DH)

Standard Notation Examples:
    K   = Strikeout swinging
    Ꝁ   = Strikeout looking (backwards K)
    BB  = Walk (base on balls)
    HBP = Hit by pitch
    1B  = Single
    2B  = Double
    3B  = Triple
    HR  = Home run
    F7  = Fly out to left field
    F8  = Fly out to center field
    F9  = Fly out to right field
    L7  = Line out to left field
    G6-3 = Ground out, shortstop to first base
    G4-3 = Ground out, second baseman to first base
    DP 4-6-3 = Double play, 2B to SS to 1B
    DP 6-4-3 = Double play, SS to 2B to 1B
    E6  = Error by shortstop
    FC  = Fielder's choice
    SF  = Sacrifice fly
    SAC = Sacrifice bunt
"""

from dataclasses import dataclass, field
from typing import List, Dict, Optional, Tuple, Any
from datetime import date
from enum import Enum

from .play_outcome import PlayResult, PlayOutcome


# Position name to number mapping
POSITION_TO_NUMBER = {
    'P': 1, 'C': 2, '1B': 3, '2B': 4, '3B': 5,
    'SS': 6, 'LF': 7, 'CF': 8, 'RF': 9, 'DH': 10,
    # Also accept full names
    'pitcher': 1, 'catcher': 2, 'first_base': 3, 'second_base': 4,
    'third_base': 5, 'shortstop': 6, 'left_field': 7, 'center_field': 8,
    'right_field': 9, 'designated_hitter': 10,
}

# Number to position abbreviation mapping
NUMBER_TO_POSITION = {
    1: 'P', 2: 'C', 3: '1B', 4: '2B', 5: '3B',
    6: 'SS', 7: 'LF', 8: 'CF', 9: 'RF', 10: 'DH',
}


def position_to_number(position: str) -> int:
    """Convert position name/abbreviation to standard number."""
    if isinstance(position, int):
        return position
    pos_upper = position.upper().strip()
    pos_lower = position.lower().strip()
    
    # Try uppercase abbreviation first
    if pos_upper in POSITION_TO_NUMBER:
        return POSITION_TO_NUMBER[pos_upper]
    # Try lowercase full name
    if pos_lower in POSITION_TO_NUMBER:
        return POSITION_TO_NUMBER[pos_lower]
    
    # Handle variations
    variations = {
        'FIRST': 3, 'SECOND': 4, 'THIRD': 5, 'SHORT': 6,
        'LEFT': 7, 'CENTER': 8, 'RIGHT': 9,
        'FIRST_BASEMAN': 3, 'SECOND_BASEMAN': 4, 'THIRD_BASEMAN': 5,
        'SHORTSTOP': 6, 'LEFT_FIELDER': 7, 'CENTER_FIELDER': 8, 'RIGHT_FIELDER': 9,
    }
    if pos_upper in variations:
        return variations[pos_upper]
    
    raise ValueError(f"Unknown position: {position}")


def number_to_position(number: int) -> str:
    """Convert position number to abbreviation."""
    if number in NUMBER_TO_POSITION:
        return NUMBER_TO_POSITION[number]
    raise ValueError(f"Unknown position number: {number}")


class PlayType(Enum):
    """Type of play for notation purposes."""
    STRIKEOUT_SWINGING = "K"
    STRIKEOUT_LOOKING = "Ꝁ"
    WALK = "BB"
    HIT_BY_PITCH = "HBP"
    SINGLE = "1B"
    DOUBLE = "2B"
    TRIPLE = "3B"
    HOME_RUN = "HR"
    FLY_OUT = "F"
    LINE_OUT = "L"
    GROUND_OUT = "G"
    POP_OUT = "P"
    DOUBLE_PLAY = "DP"
    TRIPLE_PLAY = "TP"
    FIELDERS_CHOICE = "FC"
    ERROR = "E"
    SACRIFICE_FLY = "SF"
    SACRIFICE_BUNT = "SAC"
    INFIELD_FLY = "IF"


@dataclass
class PlayNotation:
    """
    A single play recorded in standard baseball notation.
    
    Attributes
    ----------
    notation : str
        Standard baseball notation (e.g., "G6-3", "HR", "K")
    description : str
        Human-readable description of the play
    batter_id : str
        Player ID of the batter
    batter_name : str
        Name of the batter
    pitcher_id : str
        Player ID of the pitcher
    pitcher_name : str
        Name of the pitcher
    play_type : PlayType
        Categorized type of play
    fielders_involved : List[int]
        Position numbers of fielders involved (in order of touches)
    runners_advanced : Dict[int, int]
        Mapping of base movements {from_base: to_base} (0=home, 4=scored)
    runs_scored : int
        Number of runs scored on this play
    rbi : int
        RBIs credited to the batter
    outs_recorded : int
        Number of outs recorded
    is_hit : bool
        Whether this was a base hit
    is_at_bat : bool
        Whether this counts as an official at-bat
    is_error : bool
        Whether an error occurred
    
    # Physics data (optional)
    exit_velocity : float
        Exit velocity in mph (if batted ball)
    launch_angle : float
        Launch angle in degrees (if batted ball)
    distance : float
        Distance traveled in feet (if batted ball)
    """
    notation: str
    description: str
    batter_id: str
    batter_name: str
    pitcher_id: str
    pitcher_name: str
    play_type: PlayType
    fielders_involved: List[int] = field(default_factory=list)
    runners_advanced: Dict[int, int] = field(default_factory=dict)
    runs_scored: int = 0
    rbi: int = 0
    outs_recorded: int = 0
    is_hit: bool = False
    is_at_bat: bool = True
    is_error: bool = False
    
    # Physics data
    exit_velocity: Optional[float] = None
    launch_angle: Optional[float] = None
    distance: Optional[float] = None
    
    def __str__(self) -> str:
        return self.notation


@dataclass
class InningLog:
    """
    Record of all plays in a half-inning.
    
    Attributes
    ----------
    inning : int
        Inning number (1-based)
    is_top : bool
        True if top of inning (away team batting)
    plays : List[PlayNotation]
        All plays in this half-inning
    runs : int
        Runs scored in this half-inning
    hits : int
        Hits in this half-inning
    errors : int
        Errors committed (by defense) in this half-inning
    left_on_base : int
        Runners stranded at end of inning
    """
    inning: int
    is_top: bool
    plays: List[PlayNotation] = field(default_factory=list)
    runs: int = 0
    hits: int = 0
    errors: int = 0
    left_on_base: int = 0
    
    def add_play(self, play: PlayNotation):
        """Add a play to this inning."""
        self.plays.append(play)
        self.runs += play.runs_scored
        if play.is_hit:
            self.hits += 1
        if play.is_error:
            self.errors += 1
    
    @property
    def half_inning_label(self) -> str:
        """Return 'Top 1st', 'Bot 3rd', etc."""
        prefix = "Top" if self.is_top else "Bot"
        suffix = self._ordinal(self.inning)
        return f"{prefix} {suffix}"
    
    @staticmethod
    def _ordinal(n: int) -> str:
        """Convert number to ordinal (1st, 2nd, 3rd, etc.)"""
        if 10 <= n % 100 <= 13:
            suffix = 'th'
        else:
            suffix = {1: 'st', 2: 'nd', 3: 'rd'}.get(n % 10, 'th')
        return f"{n}{suffix}"


@dataclass 
class PlayerGameBatting:
    """
    A single player's batting statistics for one game.
    
    This is a box score line for a position player.
    """
    player_id: str
    player_name: str
    team: str
    position: str = ""
    batting_order: int = 0
    
    # Standard box score stats
    plate_appearances: int = 0
    at_bats: int = 0
    runs: int = 0
    hits: int = 0
    doubles: int = 0
    triples: int = 0
    home_runs: int = 0
    rbi: int = 0
    walks: int = 0
    strikeouts: int = 0
    hit_by_pitch: int = 0
    sacrifice_flies: int = 0
    sacrifice_bunts: int = 0
    stolen_bases: int = 0
    caught_stealing: int = 0
    gidp: int = 0  # Grounded into double play
    left_on_base: int = 0
    
    # Physics-based metrics (lists for per-batted-ball tracking)
    exit_velocities: List[float] = field(default_factory=list)
    launch_angles: List[float] = field(default_factory=list)
    
    @property
    def singles(self) -> int:
        """Calculate singles from hits and extra-base hits."""
        return self.hits - self.doubles - self.triples - self.home_runs
    
    @property
    def total_bases(self) -> int:
        """Calculate total bases."""
        return self.singles + 2*self.doubles + 3*self.triples + 4*self.home_runs
    
    @property
    def batting_avg(self) -> float:
        """Calculate batting average."""
        return self.hits / self.at_bats if self.at_bats > 0 else 0.0
    
    @property
    def on_base_pct(self) -> float:
        """Calculate on-base percentage."""
        numerator = self.hits + self.walks + self.hit_by_pitch
        denominator = self.at_bats + self.walks + self.hit_by_pitch + self.sacrifice_flies
        return numerator / denominator if denominator > 0 else 0.0
    
    @property
    def slugging_pct(self) -> float:
        """Calculate slugging percentage."""
        return self.total_bases / self.at_bats if self.at_bats > 0 else 0.0
    
    @property
    def ops(self) -> float:
        """Calculate OPS (on-base plus slugging)."""
        return self.on_base_pct + self.slugging_pct
    
    @property
    def avg_exit_velocity(self) -> float:
        """Calculate average exit velocity."""
        if not self.exit_velocities:
            return 0.0
        return sum(self.exit_velocities) / len(self.exit_velocities)
    
    @property
    def avg_launch_angle(self) -> float:
        """Calculate average launch angle."""
        if not self.launch_angles:
            return 0.0
        return sum(self.launch_angles) / len(self.launch_angles)
    
    @property
    def hard_hit_count(self) -> int:
        """Count balls hit 95+ mph."""
        return sum(1 for ev in self.exit_velocities if ev >= 95.0)
    
    @property
    def hard_hit_pct(self) -> float:
        """Percentage of batted balls 95+ mph."""
        if not self.exit_velocities:
            return 0.0
        return 100.0 * self.hard_hit_count / len(self.exit_velocities)
    
    def box_score_line(self) -> str:
        """Return formatted box score line."""
        return (f"{self.player_name:<20} {self.at_bats:>3} {self.runs:>3} {self.hits:>3} "
                f"{self.rbi:>3} {self.walks:>3} {self.strikeouts:>3}")


@dataclass
class PlayerGamePitching:
    """
    A single pitcher's statistics for one game.
    
    This is a box score line for a pitcher.
    """
    player_id: str
    player_name: str
    team: str
    
    # Innings pitched (stored as outs for precision, displayed as X.1, X.2)
    outs_recorded: int = 0
    
    # Standard stats
    hits_allowed: int = 0
    runs_allowed: int = 0
    earned_runs: int = 0
    walks: int = 0
    strikeouts: int = 0
    home_runs_allowed: int = 0
    hit_batters: int = 0
    
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
    
    # Batted ball types
    ground_balls: int = 0
    fly_balls: int = 0
    line_drives: int = 0
    
    # Batters faced
    batters_faced: int = 0
    
    @property
    def innings_pitched(self) -> float:
        """
        Return innings pitched in standard format (e.g., 6.1 = 6⅓).
        
        Note: This is display format. 6.1 means 6 and 1/3 innings,
        NOT 6.1 mathematical innings.
        """
        full_innings = self.outs_recorded // 3
        partial = self.outs_recorded % 3
        return float(f"{full_innings}.{partial}")
    
    @property
    def innings_pitched_decimal(self) -> float:
        """Return innings pitched as true decimal (for calculations)."""
        return self.outs_recorded / 3.0
    
    @property
    def era(self) -> float:
        """Calculate ERA (earned run average)."""
        if self.outs_recorded == 0:
            return 0.0 if self.earned_runs == 0 else float('inf')
        ip = self.outs_recorded / 3.0
        return 9.0 * self.earned_runs / ip
    
    @property
    def whip(self) -> float:
        """Calculate WHIP (walks + hits per inning pitched)."""
        if self.outs_recorded == 0:
            return 0.0
        ip = self.outs_recorded / 3.0
        return (self.walks + self.hits_allowed) / ip
    
    @property
    def k_per_9(self) -> float:
        """Calculate strikeouts per 9 innings."""
        if self.outs_recorded == 0:
            return 0.0
        ip = self.outs_recorded / 3.0
        return 9.0 * self.strikeouts / ip
    
    @property
    def bb_per_9(self) -> float:
        """Calculate walks per 9 innings."""
        if self.outs_recorded == 0:
            return 0.0
        ip = self.outs_recorded / 3.0
        return 9.0 * self.walks / ip
    
    @property
    def decision_str(self) -> str:
        """Return decision string (W, L, S, H, BS, or empty)."""
        if self.win:
            return "W"
        if self.loss:
            return "L"
        if self.save:
            return "S"
        if self.blown_save:
            return "BS"
        if self.hold:
            return "H"
        return ""
    
    def box_score_line(self) -> str:
        """Return formatted box score line."""
        ip_str = f"{self.innings_pitched:.1f}".replace('.0', '.0')  # Keep .0 for full innings
        decision = f" ({self.decision_str})" if self.decision_str else ""
        return (f"{self.player_name:<20}{decision:<5} {ip_str:>4} {self.hits_allowed:>3} "
                f"{self.runs_allowed:>3} {self.earned_runs:>3} {self.walks:>3} {self.strikeouts:>3}")


@dataclass
class GameLog:
    """
    Complete record of a simulated game.
    
    Contains play-by-play, box scores, and line score.
    """
    game_id: str
    game_date: date
    away_team: str
    home_team: str
    
    # Play-by-play by inning
    innings: List[InningLog] = field(default_factory=list)
    
    # Final score
    away_score: int = 0
    home_score: int = 0
    
    # Line score (runs per inning)
    away_line: List[int] = field(default_factory=list)
    home_line: List[int] = field(default_factory=list)
    
    # Box score data
    away_batting: List[PlayerGameBatting] = field(default_factory=list)
    home_batting: List[PlayerGameBatting] = field(default_factory=list)
    away_pitching: List[PlayerGamePitching] = field(default_factory=list)
    home_pitching: List[PlayerGamePitching] = field(default_factory=list)
    
    # Totals
    away_hits: int = 0
    home_hits: int = 0
    away_errors: int = 0
    home_errors: int = 0
    
    @property
    def final_score_str(self) -> str:
        """Return formatted final score."""
        return f"{self.away_team} {self.away_score}, {self.home_team} {self.home_score}"
    
    @property
    def winner(self) -> str:
        """Return winning team abbreviation."""
        return self.away_team if self.away_score > self.home_score else self.home_team
    
    @property
    def loser(self) -> str:
        """Return losing team abbreviation."""
        return self.home_team if self.away_score > self.home_score else self.away_team
    
    def get_line_score_str(self) -> str:
        """Return formatted line score."""
        # Pad innings to same length
        max_innings = max(len(self.away_line), len(self.home_line), 9)
        away = self.away_line + [0] * (max_innings - len(self.away_line))
        home = self.home_line + [0] * (max_innings - len(self.home_line))
        
        # Header
        header = "     " + " ".join(f"{i+1:>2}" for i in range(max_innings)) + "  | R  H  E"
        away_str = f"{self.away_team:<4} " + " ".join(f"{r:>2}" for r in away) + f"  |{self.away_score:>2} {self.away_hits:>2} {self.away_errors:>2}"
        home_str = f"{self.home_team:<4} " + " ".join(f"{r:>2}" for r in home) + f"  |{self.home_score:>2} {self.home_hits:>2} {self.home_errors:>2}"
        
        return f"{header}\n{away_str}\n{home_str}"


class Scorekeeper:
    """
    Records plays during a game simulation and generates baseball notation.
    
    Usage:
        scorekeeper = Scorekeeper()
        
        # During simulation
        notation = scorekeeper.record_strikeout(batter, pitcher, looking=False)
        notation = scorekeeper.record_batted_ball(batter, pitcher, play_result, at_bat_result)
        
        # Get game log
        game_log = scorekeeper.get_game_log()
    """
    
    def __init__(self, game_id: str = None, game_date: date = None,
                 away_team: str = "", home_team: str = ""):
        """
        Initialize the scorekeeper.
        
        Parameters
        ----------
        game_id : str, optional
            Unique identifier for this game
        game_date : date, optional
            Date of the game
        away_team : str
            Away team abbreviation
        home_team : str
            Home team abbreviation
        """
        self.game_id = game_id or ""
        self.game_date = game_date or date.today()
        self.away_team = away_team
        self.home_team = home_team
        
        # Current half-inning tracking
        self.current_inning = 1
        self.is_top_of_inning = True
        self.current_half_inning: InningLog = InningLog(inning=1, is_top=True)
        
        # All innings
        self.innings: List[InningLog] = []
        
        # Player game stats (keyed by player_id)
        self.batting_stats: Dict[str, PlayerGameBatting] = {}
        self.pitching_stats: Dict[str, PlayerGamePitching] = {}
        
        # Track batting order for each team
        self.away_order: List[str] = []  # List of player_ids in order
        self.home_order: List[str] = []
        
        # Line scores
        self.away_line: List[int] = []
        self.home_line: List[int] = []
        
        # Running totals
        self.away_runs = 0
        self.home_runs = 0
        self.current_half_inning_runs = 0
    
    def start_half_inning(self, inning: int, is_top: bool):
        """
        Start a new half-inning.
        
        Parameters
        ----------
        inning : int
            Inning number (1-based)
        is_top : bool
            True if top of inning (away batting)
        """
        # Save previous half-inning if it exists and has plays
        if self.current_half_inning and self.current_half_inning.plays:
            self.innings.append(self.current_half_inning)
            
            # Update line score
            if self.current_half_inning.is_top:
                self.away_line.append(self.current_half_inning.runs)
            else:
                self.home_line.append(self.current_half_inning.runs)
        
        # Start new half-inning
        self.current_inning = inning
        self.is_top_of_inning = is_top
        self.current_half_inning = InningLog(inning=inning, is_top=is_top)
        self.current_half_inning_runs = 0
    
    def end_half_inning(self, left_on_base: int = 0):
        """
        End the current half-inning.
        
        Parameters
        ----------
        left_on_base : int
            Number of runners left on base
        """
        self.current_half_inning.left_on_base = left_on_base
    
    def _get_or_create_batter_stats(self, player_id: str, player_name: str, 
                                     team: str) -> PlayerGameBatting:
        """Get existing batting stats or create new entry."""
        if player_id not in self.batting_stats:
            # Determine batting order
            order_list = self.away_order if team == self.away_team else self.home_order
            if player_id not in order_list:
                order_list.append(player_id)
            order = order_list.index(player_id) + 1
            
            self.batting_stats[player_id] = PlayerGameBatting(
                player_id=player_id,
                player_name=player_name,
                team=team,
                batting_order=order,
            )
        return self.batting_stats[player_id]
    
    def _get_or_create_pitcher_stats(self, player_id: str, player_name: str,
                                      team: str) -> PlayerGamePitching:
        """Get existing pitching stats or create new entry."""
        if player_id not in self.pitching_stats:
            self.pitching_stats[player_id] = PlayerGamePitching(
                player_id=player_id,
                player_name=player_name,
                team=team,
            )
        return self.pitching_stats[player_id]
    
    def record_strikeout(self, batter_id: str, batter_name: str, batter_team: str,
                         pitcher_id: str, pitcher_name: str, pitcher_team: str,
                         looking: bool = False, pitches: int = 0) -> PlayNotation:
        """
        Record a strikeout.
        
        Parameters
        ----------
        batter_id, batter_name, batter_team : str
            Batter information
        pitcher_id, pitcher_name, pitcher_team : str
            Pitcher information
        looking : bool
            True if called third strike (backwards K)
        pitches : int
            Number of pitches in the at-bat
        
        Returns
        -------
        PlayNotation
            The recorded play
        """
        play_type = PlayType.STRIKEOUT_LOOKING if looking else PlayType.STRIKEOUT_SWINGING
        notation = "Ꝁ" if looking else "K"
        description = f"{batter_name} struck out {'looking' if looking else 'swinging'}"
        
        play = PlayNotation(
            notation=notation,
            description=description,
            batter_id=batter_id,
            batter_name=batter_name,
            pitcher_id=pitcher_id,
            pitcher_name=pitcher_name,
            play_type=play_type,
            outs_recorded=1,
            is_hit=False,
            is_at_bat=True,
        )
        
        # Update stats
        batter_stats = self._get_or_create_batter_stats(batter_id, batter_name, batter_team)
        batter_stats.plate_appearances += 1
        batter_stats.at_bats += 1
        batter_stats.strikeouts += 1
        
        pitcher_stats = self._get_or_create_pitcher_stats(pitcher_id, pitcher_name, pitcher_team)
        pitcher_stats.batters_faced += 1
        pitcher_stats.strikeouts += 1
        pitcher_stats.outs_recorded += 1
        pitcher_stats.pitches += pitches
        
        # Add to inning log
        self.current_half_inning.add_play(play)
        
        return play
    
    def record_walk(self, batter_id: str, batter_name: str, batter_team: str,
                    pitcher_id: str, pitcher_name: str, pitcher_team: str,
                    pitches: int = 0, intentional: bool = False,
                    runs_scored: int = 0) -> PlayNotation:
        """
        Record a walk (base on balls).
        
        Parameters
        ----------
        runs_scored : int
            Runs scored on the play (e.g., bases loaded walk)
        
        Returns
        -------
        PlayNotation
        """
        notation = "IBB" if intentional else "BB"
        description = f"{batter_name} walked" + (" (intentional)" if intentional else "")
        
        play = PlayNotation(
            notation=notation,
            description=description,
            batter_id=batter_id,
            batter_name=batter_name,
            pitcher_id=pitcher_id,
            pitcher_name=pitcher_name,
            play_type=PlayType.WALK,
            runs_scored=runs_scored,
            rbi=runs_scored,  # RBI on walk
            outs_recorded=0,
            is_hit=False,
            is_at_bat=False,  # Walks don't count as at-bats
        )
        
        # Update stats
        batter_stats = self._get_or_create_batter_stats(batter_id, batter_name, batter_team)
        batter_stats.plate_appearances += 1
        batter_stats.walks += 1
        batter_stats.rbi += runs_scored
        
        pitcher_stats = self._get_or_create_pitcher_stats(pitcher_id, pitcher_name, pitcher_team)
        pitcher_stats.batters_faced += 1
        pitcher_stats.walks += 1
        pitcher_stats.pitches += pitches
        
        # Track runs
        if runs_scored > 0:
            self._score_runs(runs_scored)
        
        self.current_half_inning.add_play(play)
        
        return play
    
    def record_batted_ball(
        self,
        batter_id: str,
        batter_name: str,
        batter_team: str,
        pitcher_id: str,
        pitcher_name: str,
        pitcher_team: str,
        play_result: PlayResult,
        exit_velocity: float = None,
        launch_angle: float = None,
        distance: float = None,
        primary_fielder_position: str = None,
        relay_positions: List[str] = None,
        runs_scored: int = 0,
        rbi: int = 0,
        pitches: int = 0,
    ) -> PlayNotation:
        """
        Record a batted ball play.
        
        Parameters
        ----------
        play_result : PlayResult
            The result from play simulation
        exit_velocity : float
            Exit velocity in mph
        launch_angle : float
            Launch angle in degrees
        distance : float
            Distance in feet
        primary_fielder_position : str
            Position of primary fielder (e.g., "SS", "CF")
        relay_positions : List[str]
            Positions involved in relay throws
        runs_scored : int
            Runs that scored on the play
        rbi : int
            RBIs credited to batter
        pitches : int
            Number of pitches in the at-bat
        
        Returns
        -------
        PlayNotation
        """
        outcome = play_result.outcome
        
        # Determine fielder numbers
        fielders = []
        if primary_fielder_position:
            try:
                fielders.append(position_to_number(primary_fielder_position))
            except ValueError:
                pass
        if relay_positions:
            for pos in relay_positions:
                try:
                    fielders.append(position_to_number(pos))
                except ValueError:
                    pass
        
        # Generate notation based on outcome
        notation, play_type, is_hit, is_at_bat, outs = self._generate_batted_ball_notation(
            outcome, fielders, launch_angle
        )
        
        # Build description
        description = self._generate_play_description(
            batter_name, outcome, fielders, exit_velocity, distance
        )
        
        play = PlayNotation(
            notation=notation,
            description=description,
            batter_id=batter_id,
            batter_name=batter_name,
            pitcher_id=pitcher_id,
            pitcher_name=pitcher_name,
            play_type=play_type,
            fielders_involved=fielders,
            runs_scored=runs_scored,
            rbi=rbi,
            outs_recorded=outs,
            is_hit=is_hit,
            is_at_bat=is_at_bat,
            is_error=(outcome == PlayOutcome.ERROR),
            exit_velocity=exit_velocity,
            launch_angle=launch_angle,
            distance=distance,
        )
        
        # Update batter stats
        batter_stats = self._get_or_create_batter_stats(batter_id, batter_name, batter_team)
        batter_stats.plate_appearances += 1
        if is_at_bat:
            batter_stats.at_bats += 1
        if is_hit:
            batter_stats.hits += 1
            if outcome == PlayOutcome.DOUBLE:
                batter_stats.doubles += 1
            elif outcome == PlayOutcome.TRIPLE:
                batter_stats.triples += 1
            elif outcome == PlayOutcome.HOME_RUN:
                batter_stats.home_runs += 1
                batter_stats.runs += 1  # Batter scores on HR
        batter_stats.rbi += rbi
        batter_stats.runs += (1 if outcome == PlayOutcome.HOME_RUN else 0)
        
        # Track physics
        if exit_velocity is not None:
            batter_stats.exit_velocities.append(exit_velocity)
        if launch_angle is not None:
            batter_stats.launch_angles.append(launch_angle)
        
        # GIDP tracking
        if outcome == PlayOutcome.DOUBLE_PLAY:
            batter_stats.gidp += 1
        
        # Update pitcher stats
        pitcher_stats = self._get_or_create_pitcher_stats(pitcher_id, pitcher_name, pitcher_team)
        pitcher_stats.batters_faced += 1
        pitcher_stats.pitches += pitches
        pitcher_stats.outs_recorded += outs
        if is_hit:
            pitcher_stats.hits_allowed += 1
        if outcome == PlayOutcome.HOME_RUN:
            pitcher_stats.home_runs_allowed += 1
        pitcher_stats.runs_allowed += runs_scored
        pitcher_stats.earned_runs += runs_scored  # Simplified: all runs earned
        
        # Track batted ball types for pitcher
        if launch_angle is not None:
            if launch_angle < 10:
                pitcher_stats.ground_balls += 1
            elif launch_angle < 25:
                pitcher_stats.line_drives += 1
            else:
                pitcher_stats.fly_balls += 1
        
        # Track runs
        if runs_scored > 0:
            self._score_runs(runs_scored)
        
        self.current_half_inning.add_play(play)
        
        return play
    
    def _generate_batted_ball_notation(
        self,
        outcome: PlayOutcome,
        fielders: List[int],
        launch_angle: float = None
    ) -> Tuple[str, PlayType, bool, bool, int]:
        """
        Generate baseball notation for a batted ball outcome.
        
        Returns
        -------
        Tuple of (notation, play_type, is_hit, is_at_bat, outs_recorded)
        """
        # Default fielder for notation
        f1 = fielders[0] if fielders else 0
        
        if outcome == PlayOutcome.SINGLE:
            return f"1B", PlayType.SINGLE, True, True, 0
        
        elif outcome == PlayOutcome.DOUBLE:
            return f"2B", PlayType.DOUBLE, True, True, 0
        
        elif outcome == PlayOutcome.TRIPLE:
            return f"3B", PlayType.TRIPLE, True, True, 0
        
        elif outcome == PlayOutcome.HOME_RUN:
            return f"HR", PlayType.HOME_RUN, True, True, 0
        
        elif outcome == PlayOutcome.FLY_OUT:
            # Determine if line drive or fly ball by launch angle
            if launch_angle is not None and 10 <= launch_angle < 25:
                return f"L{f1}", PlayType.LINE_OUT, False, True, 1
            return f"F{f1}", PlayType.FLY_OUT, False, True, 1
        
        elif outcome == PlayOutcome.LINE_OUT:
            return f"L{f1}", PlayType.LINE_OUT, False, True, 1
        
        elif outcome == PlayOutcome.GROUND_OUT:
            if len(fielders) >= 2:
                return f"G{fielders[0]}-{fielders[1]}", PlayType.GROUND_OUT, False, True, 1
            return f"G{f1}", PlayType.GROUND_OUT, False, True, 1
        
        elif outcome == PlayOutcome.FORCE_OUT:
            if len(fielders) >= 2:
                return f"FC {fielders[0]}-{fielders[1]}", PlayType.FIELDERS_CHOICE, False, True, 1
            return f"FC", PlayType.FIELDERS_CHOICE, False, True, 1
        
        elif outcome == PlayOutcome.DOUBLE_PLAY:
            if len(fielders) >= 3:
                return f"DP {fielders[0]}-{fielders[1]}-{fielders[2]}", PlayType.DOUBLE_PLAY, False, True, 2
            elif len(fielders) >= 2:
                return f"DP {fielders[0]}-{fielders[1]}", PlayType.DOUBLE_PLAY, False, True, 2
            return f"DP", PlayType.DOUBLE_PLAY, False, True, 2
        
        elif outcome == PlayOutcome.TRIPLE_PLAY:
            return f"TP", PlayType.TRIPLE_PLAY, False, True, 3
        
        elif outcome == PlayOutcome.ERROR:
            return f"E{f1}", PlayType.ERROR, False, True, 0
        
        elif outcome == PlayOutcome.FIELDERS_CHOICE:
            return f"FC", PlayType.FIELDERS_CHOICE, False, True, 0
        
        elif outcome == PlayOutcome.INFIELD_FLY:
            return f"IF", PlayType.INFIELD_FLY, False, True, 1
        
        # Fallback
        return f"?", PlayType.GROUND_OUT, False, True, 1
    
    def _generate_play_description(
        self,
        batter_name: str,
        outcome: PlayOutcome,
        fielders: List[int],
        exit_velocity: float = None,
        distance: float = None
    ) -> str:
        """Generate human-readable description of a play."""
        ev_str = f" ({exit_velocity:.0f} mph)" if exit_velocity else ""
        dist_str = f", {distance:.0f} ft" if distance else ""
        
        fielder_names = [number_to_position(f) for f in fielders if f in NUMBER_TO_POSITION]
        
        if outcome == PlayOutcome.SINGLE:
            return f"{batter_name} singles{ev_str}"
        elif outcome == PlayOutcome.DOUBLE:
            return f"{batter_name} doubles{ev_str}{dist_str}"
        elif outcome == PlayOutcome.TRIPLE:
            return f"{batter_name} triples{ev_str}{dist_str}"
        elif outcome == PlayOutcome.HOME_RUN:
            return f"{batter_name} homers{ev_str}{dist_str}"
        elif outcome == PlayOutcome.FLY_OUT:
            to = fielder_names[0] if fielder_names else "outfield"
            return f"{batter_name} flies out to {to}{dist_str}"
        elif outcome == PlayOutcome.LINE_OUT:
            to = fielder_names[0] if fielder_names else "infield"
            return f"{batter_name} lines out to {to}"
        elif outcome == PlayOutcome.GROUND_OUT:
            if len(fielder_names) >= 2:
                return f"{batter_name} grounds out {fielder_names[0]} to {fielder_names[1]}"
            return f"{batter_name} grounds out"
        elif outcome == PlayOutcome.DOUBLE_PLAY:
            if len(fielder_names) >= 2:
                chain = " to ".join(fielder_names)
                return f"{batter_name} grounds into double play, {chain}"
            return f"{batter_name} grounds into double play"
        elif outcome == PlayOutcome.ERROR:
            on = fielder_names[0] if fielder_names else "fielder"
            return f"{batter_name} reaches on error by {on}"
        elif outcome == PlayOutcome.FIELDERS_CHOICE:
            return f"{batter_name} reaches on fielder's choice"
        
        return f"{batter_name} batted ball"
    
    def _score_runs(self, runs: int):
        """Track runs scored in game totals only."""
        # Note: Inning runs are tracked via add_play() -> play.runs_scored
        # This method only updates game totals
        if self.is_top_of_inning:
            self.away_runs += runs
        else:
            self.home_runs += runs
    
    def record_run_scored(self, runner_id: str, runner_name: str, runner_team: str):
        """Record a run scored by a specific runner."""
        runner_stats = self._get_or_create_batter_stats(runner_id, runner_name, runner_team)
        runner_stats.runs += 1
    
    def finalize_game(self) -> GameLog:
        """
        Finalize the game and return the complete GameLog.
        
        Call this after the game is complete.
        """
        # Save final half-inning
        if self.current_half_inning and self.current_half_inning.plays:
            self.innings.append(self.current_half_inning)
            if self.current_half_inning.is_top:
                self.away_line.append(self.current_half_inning.runs)
            else:
                self.home_line.append(self.current_half_inning.runs)
        
        # Split batting stats by team
        away_batting = [s for s in self.batting_stats.values() if s.team == self.away_team]
        home_batting = [s for s in self.batting_stats.values() if s.team == self.home_team]
        
        # Sort by batting order
        away_batting.sort(key=lambda x: x.batting_order)
        home_batting.sort(key=lambda x: x.batting_order)
        
        # Split pitching stats by team
        away_pitching = [s for s in self.pitching_stats.values() if s.team == self.away_team]
        home_pitching = [s for s in self.pitching_stats.values() if s.team == self.home_team]
        
        # Calculate totals
        away_hits = sum(s.hits for s in away_batting)
        home_hits = sum(s.hits for s in home_batting)
        away_errors = sum(i.errors for i in self.innings if not i.is_top)  # Away defense = bottom innings
        home_errors = sum(i.errors for i in self.innings if i.is_top)  # Home defense = top innings
        
        return GameLog(
            game_id=self.game_id,
            game_date=self.game_date,
            away_team=self.away_team,
            home_team=self.home_team,
            innings=self.innings,
            away_score=self.away_runs,
            home_score=self.home_runs,
            away_line=self.away_line,
            home_line=self.home_line,
            away_batting=away_batting,
            home_batting=home_batting,
            away_pitching=away_pitching,
            home_pitching=home_pitching,
            away_hits=away_hits,
            home_hits=home_hits,
            away_errors=away_errors,
            home_errors=home_errors,
        )
    
    def reset(self):
        """Reset for a new game."""
        self.__init__(
            game_id=self.game_id,
            game_date=self.game_date,
            away_team=self.away_team,
            home_team=self.home_team,
        )
