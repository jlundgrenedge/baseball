"""
Baseball Batted Ball Physics Simulator

A realistic physics-based simulator for baseball batted ball trajectories
and pitch trajectories, with player attribute system for gameplay.

Includes:
- Phase 1: Spin-dependent aerodynamics and trajectory simulation
- Phase 2: Bat-ball collision physics with sweet spot effects
- Phase 3: Pitch trajectory simulation with different pitch types
- Phase 4: Player attribute system and at-bat simulation
- Phase 5: Fielding and baserunning mechanics for complete play simulation
"""

from .trajectory import BattedBallSimulator, BattedBallResult
from .environment import Environment, create_standard_environment, create_coors_field_environment
from .contact import adjust_for_contact_point, ContactModel
from .pitch import (
    PitchSimulator,
    PitchResult,
    PitchType,
    create_fastball_4seam,
    create_fastball_2seam,
    create_cutter,
    create_curveball,
    create_slider,
    create_changeup,
    create_splitter,
    create_knuckleball,
)
from .player import Pitcher, Hitter
from .at_bat import AtBatSimulator, AtBatResult

# Fielding and baserunning modules
from .field_layout import (
    FieldLayout,
    FieldPosition,
    BaseLocation,
    DefensivePosition,
    create_standard_field,
    distance_between_positions,
    position_from_coordinates,
    get_standard_defensive_alignment,
)
from .fielding import (
    Fielder,
    FieldingResult,
    ThrowResult,
    DetailedThrowResult,
    RelayThrowResult,
    FieldingSimulator,
    simulate_fielder_throw,
    simulate_relay_throw,
    determine_cutoff_man,
    create_elite_fielder,
    create_average_fielder,
    create_poor_fielder,
    RELAY_THROW_THRESHOLD,
)
from .baserunning import (
    BaseRunner,
    BaserunningResult,
    BaserunningSimulator,
    RunnerState,
    create_speed_runner,
    create_smart_runner,
    create_average_runner,
    create_slow_runner,
)
from .play_outcome import (
    PlayResult,
    PlayEvent,
    PlayOutcome,
)
from .defense_factory import (
    create_standard_defense,
    create_elite_defense,
)
from .play_simulation import (
    PlaySimulator,
    simulate_play_from_trajectory,
)
from .game_simulation import (
    GameSimulator,
    GameState,
    Team,
    BaseState,
    PlayByPlayEvent,
    create_test_team,
)
from .series_metrics import (
    SeriesMetrics,
    AdvancedBattingMetrics,
    PitchingMetrics,
    FieldingMetrics,
    RealismCheck,
)
from .ballpark import (
    BallparkDimensions,
    get_ballpark,
    list_available_parks,
    MLB_BALLPARKS,
)

from .constants import *
from .constants import SimulationMode, get_dt_for_mode

# Performance optimization modules (optional imports)
try:
    from .performance import (
        TrajectoryBuffer,
        ResultObjectPool,
        OptimizedAerodynamicForces,
        UltraFastMode,
        PerformanceTracker
    )
    from .bulk_simulation import BulkAtBatSimulator, BulkSimulationSettings, BulkSimulationResult
    from .parallel_game_simulation import (
        ParallelGameSimulator,
        ParallelSimulationSettings,
        ParallelSimulationResult,
        GameResult
    )
    _PERFORMANCE_AVAILABLE = True
except ImportError:
    _PERFORMANCE_AVAILABLE = False

# PyBaseball integration (optional import)
try:
    from .pybaseball_integration import (
        PYBASEBALL_AVAILABLE,
        create_mlb_player,
        create_team_from_mlb_roster,
        fetch_player_batting_stats,
        fetch_player_pitching_stats,
        create_hitter_from_mlb_stats,
        create_fielder_from_mlb_stats,
        create_pitcher_from_mlb_stats,
    )
    _PYBASEBALL_INTEGRATION_AVAILABLE = True
except ImportError:
    _PYBASEBALL_INTEGRATION_AVAILABLE = False

__version__ = '1.1.0'
__author__ = 'Baseball Physics Team'

__all__ = [
    # Simulation modes
    'SimulationMode',
    'get_dt_for_mode',
    
    # Core trajectory simulation
    'BattedBallSimulator',
    'BattedBallResult',
    'Environment',
    'create_standard_environment',
    'create_coors_field_environment',
    'adjust_for_contact_point',
    'ContactModel',
    
    # Pitch simulation
    'PitchSimulator',
    'PitchResult',
    'PitchType',
    'create_fastball_4seam',
    'create_fastball_2seam',
    'create_cutter',
    'create_curveball',
    'create_slider',
    'create_changeup',
    'create_splitter',
    'create_knuckleball',
    
    # Player attributes and at-bat
    'Pitcher',
    'Hitter',
    'AtBatSimulator',
    'AtBatResult',
    
    # Field layout
    'FieldLayout',
    'FieldPosition',
    'BaseLocation',
    'DefensivePosition',
    'create_standard_field',
    'distance_between_positions',
    'position_from_coordinates',
    'get_standard_defensive_alignment',
    
    # Fielding mechanics
    'Fielder',
    'FieldingResult',
    'ThrowResult',
    'DetailedThrowResult',
    'RelayThrowResult',
    'FieldingSimulator',
    'simulate_fielder_throw',
    'simulate_relay_throw',
    'determine_cutoff_man',
    'create_elite_fielder',
    'create_average_fielder',
    'create_poor_fielder',
    'RELAY_THROW_THRESHOLD',
    
    # Baserunning mechanics
    'BaseRunner',
    'BaserunningResult',
    'BaserunningSimulator',
    'RunnerState',
    'create_speed_runner',
    'create_smart_runner',
    'create_average_runner',
    'create_slow_runner',
    
    # Complete play simulation
    'PlaySimulator',
    'PlayResult',
    'PlayEvent',
    'PlayOutcome',
    'create_standard_defense',
    'create_elite_defense',
    'simulate_play_from_trajectory',

    # Game simulation
    'GameSimulator',
    'GameState',
    'Team',
    'BaseState',
    'PlayByPlayEvent',
    'create_test_team',

    # Ballpark dimensions
    'BallparkDimensions',
    'get_ballpark',
    'list_available_parks',
    'MLB_BALLPARKS',
]

# Add performance modules if available
if _PERFORMANCE_AVAILABLE:
    __all__.extend([
        'TrajectoryBuffer',
        'ResultObjectPool',
        'OptimizedAerodynamicForces',
        'UltraFastMode',
        'PerformanceTracker',
        'BulkAtBatSimulator',
        'BulkSimulationSettings',
        'BulkSimulationResult',
        'ParallelGameSimulator',
        'ParallelSimulationSettings',
        'ParallelSimulationResult',
        'GameResult'
    ])

# Add pybaseball integration if available
if _PYBASEBALL_INTEGRATION_AVAILABLE:
    __all__.extend([
        'PYBASEBALL_AVAILABLE',
        'create_mlb_player',
        'create_team_from_mlb_roster',
        'fetch_player_batting_stats',
        'fetch_player_pitching_stats',
        'create_hitter_from_mlb_stats',
        'create_fielder_from_mlb_stats',
        'create_pitcher_from_mlb_stats',
    ])
