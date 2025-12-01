"""
Database module for storing and retrieving MLB teams and player attributes.

This module provides functionality to:
- Fetch MLB player statistics using pybaseball
- Convert MLB stats to game attributes (0-100,000 scale)
- Store teams and players in SQLite database
- Load teams from database for game simulations
- Export database to CSV files for AI ingestion
- Unified team abbreviation mappings
"""

from .team_database import TeamDatabase
from .stats_converter import StatsConverter
from .pybaseball_fetcher import PybaseballFetcher
from .team_loader import TeamLoader
from .csv_exporter import CSVExporter
from .team_mappings import (
    TEAM_ABBR_MAP,
    TEAM_FULL_NAMES,
    TEAM_DIVISIONS,
    get_db_abbr,
    get_team_name,
    get_all_team_abbrs,
    get_team_division,
    get_teams_by_division,
)

__all__ = [
    'TeamDatabase',
    'StatsConverter',
    'PybaseballFetcher',
    'TeamLoader',
    'CSVExporter',
    # Team mappings
    'TEAM_ABBR_MAP',
    'TEAM_FULL_NAMES',
    'TEAM_DIVISIONS',
    'get_db_abbr',
    'get_team_name',
    'get_all_team_abbrs',
    'get_team_division',
    'get_teams_by_division',
]
