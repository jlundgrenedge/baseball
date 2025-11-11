"""
Defense factory functions for creating standard defensive alignments.
"""

from typing import Dict
from .fielding import Fielder, create_average_fielder, create_elite_fielder


def create_standard_defense() -> Dict[str, Fielder]:
    """Create a standard defensive alignment with average fielders."""
    return {
        'pitcher': create_average_fielder('Pitcher', 'pitcher'),
        'catcher': create_average_fielder('Catcher', 'catcher'),
        'first_base': create_average_fielder('First Base', 'first_base'),
        'second_base': create_average_fielder('Second Base', 'second_base'),
        'third_base': create_average_fielder('Third Base', 'third_base'),
        'shortstop': create_average_fielder('Shortstop', 'shortstop'),
        'left_field': create_average_fielder('Left Field', 'left_field'),
        'center_field': create_average_fielder('Center Field', 'center_field'),
        'right_field': create_average_fielder('Right Field', 'right_field'),
    }


def create_elite_defense() -> Dict[str, Fielder]:
    """Create an elite defensive alignment."""
    return {
        'pitcher': create_elite_fielder('Elite Pitcher', 'pitcher'),
        'catcher': create_elite_fielder('Elite Catcher', 'catcher'),
        'first_base': create_elite_fielder('Elite First Base', 'first_base'),
        'second_base': create_elite_fielder('Elite Second Base', 'second_base'),
        'third_base': create_elite_fielder('Elite Third Base', 'third_base'),
        'shortstop': create_elite_fielder('Elite Shortstop', 'shortstop'),
        'left_field': create_elite_fielder('Elite Left Field', 'left_field'),
        'center_field': create_elite_fielder('Elite Center Field', 'center_field'),
        'right_field': create_elite_fielder('Elite Right Field', 'right_field'),
    }
