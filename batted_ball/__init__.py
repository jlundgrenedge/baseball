"""
Baseball Batted Ball Physics Simulator

A realistic physics-based simulator for baseball batted ball trajectories.
"""

from .trajectory import BattedBallSimulator, BattedBallResult
from .environment import Environment, create_standard_environment, create_coors_field_environment
from .contact import adjust_for_contact_point, ContactModel
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
]
