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
    FieldingSimulator,
    create_elite_fielder,
    create_average_fielder,
    create_poor_fielder,
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
from .play_simulation import (
    PlaySimulator,
    PlayResult,
    PlayEvent,
    PlayOutcome,
    create_standard_defense,
    create_elite_defense,
    simulate_play_from_trajectory,
)

from .constants import *

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
    _PERFORMANCE_AVAILABLE = True
except ImportError:
    _PERFORMANCE_AVAILABLE = False

__version__ = '1.1.0'
__author__ = 'Baseball Physics Team'

__all__ = [
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
    'FieldingSimulator',
    'create_elite_fielder',
    'create_average_fielder',
    'create_poor_fielder',
    
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
        'BulkSimulationResult'
    ])
