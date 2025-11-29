"""
Play outcome data structures for baseball play simulation.

Contains enums and data classes representing play results and events.
"""

from enum import Enum
from typing import List


class PlayOutcome(Enum):
    """Possible outcomes of a play."""
    FLY_OUT = "fly_out"
    LINE_OUT = "line_out"
    GROUND_OUT = "ground_out"
    FORCE_OUT = "force_out"
    DOUBLE_PLAY = "double_play"
    TRIPLE_PLAY = "triple_play"
    INFIELD_FLY = "infield_fly"  # Infield fly rule - batter out, runners advance at own risk
    SINGLE = "single"
    DOUBLE = "double"
    TRIPLE = "triple"
    HOME_RUN = "home_run"
    ERROR = "error"
    FIELDERS_CHOICE = "fielders_choice"


class PlayEvent:
    """Represents a single event during a play.
    
    Uses __slots__ for memory efficiency and faster attribute access.
    Phase 6 optimization: ~20% memory reduction per instance.
    """
    __slots__ = ('time', 'event_type', 'description', 'positions_involved')

    def __init__(self, time: float, event_type: str, description: str,
                 positions_involved: List[str] = None):
        """
        Initialize play event.

        Parameters
        ----------
        time : float
            Time when event occurred (seconds from contact)
        event_type : str
            Type of event ('catch', 'throw', 'runner_arrival', etc.)
        description : str
            Human-readable description
        positions_involved : List[str], optional
            Fielding positions involved
        """
        self.time = time
        self.event_type = event_type
        self.description = description
        self.positions_involved = positions_involved or []


class PlayResult:
    """Complete result of a play simulation.
    
    Uses __slots__ for memory efficiency and faster attribute access.
    Phase 6 optimization: ~20% memory reduction per instance.
    """
    __slots__ = ('outcome', 'events', 'runs_scored', 'outs_made', 'initial_runner_positions',
                 'final_runner_positions', 'batted_ball_result', 'fielding_results',
                 'baserunning_results', 'play_description', 'primary_fielder',
                 'runner_targets', 'batter_target_base')

    def __init__(self):
        """Initialize empty play result."""
        self.outcome = None
        self.events = []
        self.runs_scored = 0
        self.outs_made = 0
        self.initial_runner_positions = {}
        self.final_runner_positions = {}
        self.batted_ball_result = None
        self.fielding_results = []
        self.baserunning_results = []
        self.play_description = ""
        self.primary_fielder = None  # Fielder who made the primary play
        self.runner_targets = {}  # Runner advancement targets
        self.batter_target_base = None  # Batter's target base on hit

    def add_event(self, event: PlayEvent):
        """Add an event to the play."""
        self.events.append(event)

    def get_events_chronological(self) -> List[PlayEvent]:
        """Get events sorted by time."""
        return sorted(self.events, key=lambda e: e.time)

    def generate_description(self) -> str:
        """Generate a human-readable play description."""
        if not self.events:
            return "No play events recorded"

        events = self.get_events_chronological()
        descriptions = [event.description for event in events]
        return ". ".join(descriptions) + "."
