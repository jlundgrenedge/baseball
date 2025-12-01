"""
Unified team abbreviation and name mappings for the baseball simulation.

This module provides a single source of truth for team codes, ensuring
consistency across:
- MLB schedule files (Retrosheet format)
- Baseball Savant/Statcast data
- FanGraphs data
- Our internal database

Usage:
    from batted_ball.database.team_mappings import (
        TEAM_ABBR_MAP,         # CSV -> DB abbreviation mapping
        DB_TO_CSV_MAP,         # DB -> CSV abbreviation mapping (reverse)
        TEAM_FULL_NAMES,       # Abbreviation -> Full team name
        TEAM_DIVISIONS,        # Division info for each team
        get_team_name,         # Helper function
        get_db_abbr,           # Convert any abbr to our DB standard
        get_all_team_abbrs,    # Get list of all valid DB abbreviations
    )
"""

from typing import Dict, List, Optional

# =============================================================================
# MASTER TEAM ABBREVIATION MAPPING
# =============================================================================
# Maps all known external abbreviations to our standard database abbreviations
# This handles:
#   - Retrosheet codes (used in schedule CSV): NYA, LAN, CHN, etc.
#   - Older team codes: ANA (Angels), FLA (Marlins pre-2012), etc.
#   - Alternate codes from various sources

TEAM_ABBR_MAP: Dict[str, str] = {
    # =========================================================================
    # American League East
    # =========================================================================
    'BAL': 'BAL',   # Baltimore Orioles
    'BOS': 'BOS',   # Boston Red Sox
    'NYA': 'NYY',   # New York Yankees (Retrosheet: NYA)
    'NYY': 'NYY',   # New York Yankees (standard)
    'TBA': 'TB',    # Tampa Bay Rays (Retrosheet: TBA)
    'TBR': 'TB',    # Tampa Bay Rays (old alternate)
    'TB':  'TB',    # Tampa Bay Rays (standard)
    'TOR': 'TOR',   # Toronto Blue Jays
    
    # =========================================================================
    # American League Central
    # =========================================================================
    'CHA': 'CHW',   # Chicago White Sox (Retrosheet: CHA)
    'CHW': 'CHW',   # Chicago White Sox (standard)
    'CLE': 'CLE',   # Cleveland Guardians
    'DET': 'DET',   # Detroit Tigers
    'KCA': 'KC',    # Kansas City Royals (Retrosheet: KCA)
    'KCR': 'KC',    # Kansas City Royals (old alternate)
    'KC':  'KC',    # Kansas City Royals (standard)
    'MIN': 'MIN',   # Minnesota Twins
    
    # =========================================================================
    # American League West
    # =========================================================================
    'HOU': 'HOU',   # Houston Astros
    'ANA': 'LAA',   # Los Angeles Angels (Anaheim: ANA)
    'LAA': 'LAA',   # Los Angeles Angels (standard)
    'ATH': 'OAK',   # Athletics (2025: moved from Oakland, using ATH)
    'OAK': 'OAK',   # Oakland Athletics (standard/historical)
    'SEA': 'SEA',   # Seattle Mariners
    'TEX': 'TEX',   # Texas Rangers
    
    # =========================================================================
    # National League East
    # =========================================================================
    'ATL': 'ATL',   # Atlanta Braves
    'FLA': 'MIA',   # Florida Marlins (pre-2012)
    'MIA': 'MIA',   # Miami Marlins (standard)
    'NYN': 'NYM',   # New York Mets (Retrosheet: NYN)
    'NYM': 'NYM',   # New York Mets (standard)
    'PHI': 'PHI',   # Philadelphia Phillies
    'WAS': 'WSH',   # Washington Nationals (Retrosheet: WAS)
    'WSN': 'WSH',   # Washington Nationals (old alternate)
    'WSH': 'WSH',   # Washington Nationals (standard)
    
    # =========================================================================
    # National League Central
    # =========================================================================
    'CHN': 'CHC',   # Chicago Cubs (Retrosheet: CHN)
    'CHC': 'CHC',   # Chicago Cubs (standard)
    'CIN': 'CIN',   # Cincinnati Reds
    'MIL': 'MIL',   # Milwaukee Brewers
    'PIT': 'PIT',   # Pittsburgh Pirates
    'SLN': 'STL',   # St. Louis Cardinals (Retrosheet: SLN)
    'STL': 'STL',   # St. Louis Cardinals (standard)
    
    # =========================================================================
    # National League West
    # =========================================================================
    'ARI': 'ARI',   # Arizona Diamondbacks
    'COL': 'COL',   # Colorado Rockies
    'LAN': 'LAD',   # Los Angeles Dodgers (Retrosheet: LAN)
    'LAD': 'LAD',   # Los Angeles Dodgers (standard)
    'SDN': 'SD',    # San Diego Padres (Retrosheet: SDN)
    'SDP': 'SD',    # San Diego Padres (old alternate)
    'SD':  'SD',    # San Diego Padres (standard)
    'SFN': 'SF',    # San Francisco Giants (Retrosheet: SFN)
    'SFG': 'SF',    # San Francisco Giants (old alternate)
    'SF':  'SF',    # San Francisco Giants (standard)
}

# Reverse mapping: DB abbreviation -> primary Retrosheet code
# (for when we need to look up schedule data)
DB_TO_CSV_MAP: Dict[str, str] = {
    'BAL': 'BAL',
    'BOS': 'BOS',
    'NYY': 'NYA',
    'TB':  'TBA',
    'TOR': 'TOR',
    'CHW': 'CHA',
    'CLE': 'CLE',
    'DET': 'DET',
    'KC':  'KCA',
    'MIN': 'MIN',
    'HOU': 'HOU',
    'LAA': 'ANA',
    'OAK': 'ATH',   # 2025 schedule uses ATH
    'SEA': 'SEA',
    'TEX': 'TEX',
    'ATL': 'ATL',
    'MIA': 'MIA',
    'NYM': 'NYN',
    'PHI': 'PHI',
    'WSH': 'WAS',
    'CHC': 'CHN',
    'CIN': 'CIN',
    'MIL': 'MIL',
    'PIT': 'PIT',
    'STL': 'SLN',
    'ARI': 'ARI',
    'COL': 'COL',
    'LAD': 'LAN',
    'SD':  'SDN',
    'SF':  'SFN',
}

# =============================================================================
# TEAM FULL NAMES
# =============================================================================
# Maps DB abbreviation to official team name

TEAM_FULL_NAMES: Dict[str, str] = {
    # American League East
    'BAL': 'Baltimore Orioles',
    'BOS': 'Boston Red Sox',
    'NYY': 'New York Yankees',
    'TB':  'Tampa Bay Rays',
    'TOR': 'Toronto Blue Jays',
    
    # American League Central
    'CHW': 'Chicago White Sox',
    'CLE': 'Cleveland Guardians',
    'DET': 'Detroit Tigers',
    'KC':  'Kansas City Royals',
    'MIN': 'Minnesota Twins',
    
    # American League West
    'HOU': 'Houston Astros',
    'LAA': 'Los Angeles Angels',
    'OAK': 'Athletics',  # No longer Oakland as of 2025
    'SEA': 'Seattle Mariners',
    'TEX': 'Texas Rangers',
    
    # National League East
    'ATL': 'Atlanta Braves',
    'MIA': 'Miami Marlins',
    'NYM': 'New York Mets',
    'PHI': 'Philadelphia Phillies',
    'WSH': 'Washington Nationals',
    
    # National League Central
    'CHC': 'Chicago Cubs',
    'CIN': 'Cincinnati Reds',
    'MIL': 'Milwaukee Brewers',
    'PIT': 'Pittsburgh Pirates',
    'STL': 'St. Louis Cardinals',
    
    # National League West
    'ARI': 'Arizona Diamondbacks',
    'COL': 'Colorado Rockies',
    'LAD': 'Los Angeles Dodgers',
    'SD':  'San Diego Padres',
    'SF':  'San Francisco Giants',
}

# =============================================================================
# TEAM DIVISIONS
# =============================================================================
# Maps DB abbreviation to (league, division)

TEAM_DIVISIONS: Dict[str, tuple] = {
    # American League East
    'BAL': ('AL', 'East'),
    'BOS': ('AL', 'East'),
    'NYY': ('AL', 'East'),
    'TB':  ('AL', 'East'),
    'TOR': ('AL', 'East'),
    
    # American League Central
    'CHW': ('AL', 'Central'),
    'CLE': ('AL', 'Central'),
    'DET': ('AL', 'Central'),
    'KC':  ('AL', 'Central'),
    'MIN': ('AL', 'Central'),
    
    # American League West
    'HOU': ('AL', 'West'),
    'LAA': ('AL', 'West'),
    'OAK': ('AL', 'West'),
    'SEA': ('AL', 'West'),
    'TEX': ('AL', 'West'),
    
    # National League East
    'ATL': ('NL', 'East'),
    'MIA': ('NL', 'East'),
    'NYM': ('NL', 'East'),
    'PHI': ('NL', 'East'),
    'WSH': ('NL', 'East'),
    
    # National League Central
    'CHC': ('NL', 'Central'),
    'CIN': ('NL', 'Central'),
    'MIL': ('NL', 'Central'),
    'PIT': ('NL', 'Central'),
    'STL': ('NL', 'Central'),
    
    # National League West
    'ARI': ('NL', 'West'),
    'COL': ('NL', 'West'),
    'LAD': ('NL', 'West'),
    'SD':  ('NL', 'West'),
    'SF':  ('NL', 'West'),
}


# =============================================================================
# HELPER FUNCTIONS
# =============================================================================

def get_db_abbr(abbr: str) -> str:
    """
    Convert any team abbreviation to our standard DB abbreviation.
    
    Parameters
    ----------
    abbr : str
        Any team abbreviation (Retrosheet, Statcast, FanGraphs, etc.)
    
    Returns
    -------
    str
        Standard DB abbreviation, or the input if not found
    
    Examples
    --------
    >>> get_db_abbr('NYA')
    'NYY'
    >>> get_db_abbr('LAN')
    'LAD'
    >>> get_db_abbr('NYY')
    'NYY'
    """
    return TEAM_ABBR_MAP.get(abbr.upper(), abbr.upper())


def get_csv_abbr(db_abbr: str) -> str:
    """
    Convert DB abbreviation to Retrosheet/CSV abbreviation.
    
    Parameters
    ----------
    db_abbr : str
        Standard DB abbreviation
    
    Returns
    -------
    str
        Retrosheet abbreviation for schedule lookups
    """
    return DB_TO_CSV_MAP.get(db_abbr.upper(), db_abbr.upper())


def get_team_name(abbr: str) -> str:
    """
    Get full team name from any abbreviation.
    
    Parameters
    ----------
    abbr : str
        Any team abbreviation
    
    Returns
    -------
    str
        Full team name, or the abbreviation if not found
    
    Examples
    --------
    >>> get_team_name('NYY')
    'New York Yankees'
    >>> get_team_name('NYA')  # Retrosheet code
    'New York Yankees'
    """
    db_abbr = get_db_abbr(abbr)
    return TEAM_FULL_NAMES.get(db_abbr, abbr)


def get_all_team_abbrs() -> List[str]:
    """
    Get list of all valid DB team abbreviations.
    
    Returns
    -------
    List[str]
        Sorted list of 30 MLB team abbreviations
    """
    return sorted(TEAM_FULL_NAMES.keys())


def get_team_division(abbr: str) -> Optional[tuple]:
    """
    Get league and division for a team.
    
    Parameters
    ----------
    abbr : str
        Any team abbreviation
    
    Returns
    -------
    tuple or None
        (league, division) tuple, e.g., ('AL', 'East')
    """
    db_abbr = get_db_abbr(abbr)
    return TEAM_DIVISIONS.get(db_abbr)


def get_teams_by_division(league: str = None, division: str = None) -> List[str]:
    """
    Get teams filtered by league and/or division.
    
    Parameters
    ----------
    league : str, optional
        'AL' or 'NL'
    division : str, optional
        'East', 'Central', or 'West'
    
    Returns
    -------
    List[str]
        List of team abbreviations matching the criteria
    """
    teams = []
    for abbr, (lg, div) in TEAM_DIVISIONS.items():
        if league and lg != league:
            continue
        if division and div != division:
            continue
        teams.append(abbr)
    return sorted(teams)
