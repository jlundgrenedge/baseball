"""
Baseball Batted Ball Physics Simulator

A realistic physics-based simulator for baseball batted ball trajectories
and pitch trajectories, with player attribute system for gameplay.

Includes:
- Phase 1: Spin-dependent aerodynamics and trajectory simulation
- Phase 2: Bat-ball collision physics with sweet spot effects
- Phase 3: Pitch trajectory simulation with different pitch types
- Phase 4: Player attribute system and at-bat simulation
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
from .constants import *

__version__ = '1.0.0'
__author__ = 'Baseball Physics Team'

__all__ = [
    'BattedBallSimulator',
    'BattedBallResult',
    'Environment',
    'create_standard_environment',
    'create_coors_field_environment',
    'adjust_for_contact_point',
    'ContactModel',
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
    'Pitcher',
    'Hitter',
    'AtBatSimulator',
    'AtBatResult',
]
