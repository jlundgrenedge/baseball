"""
PyBaseball Integration Module

Maps real MLB statistics from pybaseball to the physics-based attribute system (0-100,000 scale).

This module provides functions to:
1. Fetch player statistics from pybaseball
2. Convert MLB stats to simulation attributes using percentile-based mapping
3. Create Player objects (Pitcher, Hitter) from real MLB data
4. Build Team objects from actual MLB rosters

Author: Baseball Physics Simulation Engine
"""

import numpy as np
from typing import Dict, List, Optional, Tuple
import warnings

# Attempt to import pybaseball (optional dependency)
try:
    import pybaseball as pyb
    PYBASEBALL_AVAILABLE = True
except ImportError:
    PYBASEBALL_AVAILABLE = False
    warnings.warn(
        "pybaseball not installed. Install with: pip install pybaseball\n"
        "This module requires pybaseball to fetch MLB data."
    )

from .attributes import HitterAttributes, PitcherAttributes, FielderAttributes
from .player import Pitcher, Hitter, generate_pitch_arsenal
from .fielding import Fielder
from .game_simulation import Team
from .defense_factory import create_standard_defense


# =============================================================================
# POSITION MAPPING UTILITIES
# =============================================================================

def map_position_abbreviation_to_full_name(position_abbr: str) -> str:
    """
    Convert position abbreviation to full position name used by field_layout.

    Parameters
    ----------
    position_abbr : str
        Position abbreviation (e.g., 'RF', '1B', 'SS')

    Returns
    -------
    str
        Full position name (e.g., 'right_field', 'first_base', 'shortstop')
    """
    position_mapping = {
        'P': 'pitcher',
        'C': 'catcher',
        '1B': 'first_base',
        '2B': 'second_base',
        '3B': 'third_base',
        'SS': 'shortstop',
        'LF': 'left_field',
        'CF': 'center_field',
        'RF': 'right_field',
        'DH': 'designated_hitter'  # DH doesn't have a field position
    }
    return position_mapping.get(position_abbr, position_abbr.lower())


# =============================================================================
# PERCENTILE-BASED MAPPING UTILITIES
# =============================================================================

def percentile_to_attribute(percentile: float, invert: bool = False) -> float:
    """
    Convert a percentile (0-100) to attribute rating (0-100,000).

    Mapping strategy:
    - 50th percentile (league average) → 50,000
    - 95th percentile (elite) → 85,000
    - 99th percentile (superstar) → 95,000
    - 5th percentile (poor) → 15,000

    Parameters
    ----------
    percentile : float
        Percentile rank (0-100)
    invert : bool
        If True, invert the mapping (for "lower is better" stats like K%, BB%)

    Returns
    -------
    float
        Attribute rating (0-100,000)
    """
    if invert:
        percentile = 100 - percentile

    # Clip to valid range
    percentile = np.clip(percentile, 0, 100)

    # Piecewise linear mapping with steeper slope for elite tier
    if percentile <= 50:
        # Below average to average: 0-50 percentile → 0-50,000
        return percentile * 1000
    elif percentile <= 95:
        # Average to elite: 50-95 percentile → 50,000-85,000
        return 50000 + (percentile - 50) * (35000 / 45)
    else:
        # Elite to superstar: 95-100 percentile → 85,000-100,000
        return 85000 + (percentile - 95) * (15000 / 5)


def stat_to_percentile(value: float, league_values: List[float]) -> float:
    """
    Calculate percentile rank of a value within a distribution.

    Parameters
    ----------
    value : float
        Player's stat value
    league_values : list of float
        League distribution of the stat

    Returns
    -------
    float
        Percentile rank (0-100)
    """
    if len(league_values) == 0:
        return 50.0  # Default to average if no data

    # Remove NaN values
    league_values = [v for v in league_values if not np.isnan(v)]

    if len(league_values) == 0:
        return 50.0

    # Calculate percentile
    percentile = (np.sum(np.array(league_values) <= value) / len(league_values)) * 100
    return np.clip(percentile, 0, 100)


# =============================================================================
# HITTER STAT MAPPING
# =============================================================================

def map_hitter_stats_to_attributes(stats: Dict) -> HitterAttributes:
    """
    Convert MLB hitting statistics to HitterAttributes (0-100,000 scale).

    Key stat mappings:
    - Exit Velocity (avg) → BAT_SPEED
    - Barrel% → BARREL_ACCURACY
    - K% → ZONE_DISCERNMENT (inverse), SWING_DECISION_LATENCY (inverse)
    - BB% → ZONE_DISCERNMENT
    - Launch Angle (avg) → ATTACK_ANGLE_CONTROL
    - Pull%, Oppo% → SPRAY_TENDENCY
    - Hard Hit% → BAT_SPEED, BARREL_ACCURACY

    Parameters
    ----------
    stats : dict
        Dictionary with player's stats and league percentiles
        Expected keys: 'exit_velocity_avg', 'barrel_pct', 'k_pct', 'bb_pct',
                      'launch_angle_avg', 'pull_pct', 'hard_hit_pct', etc.

    Returns
    -------
    HitterAttributes
        Mapped attributes on 0-100,000 scale
    """
    # Helper to get stat with default
    def get_stat(key: str, default: float = 50.0) -> float:
        return stats.get(key, default)

    # Exit velocity → BAT_SPEED
    # MLB average ~89 mph, elite ~95 mph
    ev_percentile = get_stat('exit_velocity_avg_percentile', 50.0)
    bat_speed = percentile_to_attribute(ev_percentile)

    # Barrel% → BARREL_ACCURACY
    # MLB average ~8%, elite ~15%+
    barrel_percentile = get_stat('barrel_pct_percentile', 50.0)
    barrel_accuracy = percentile_to_attribute(barrel_percentile)

    # K% → ZONE_DISCERNMENT, SWING_DECISION_LATENCY (inverse - lower K% is better)
    # MLB average ~22%, elite <15%
    k_percentile = get_stat('k_pct_percentile', 50.0)
    zone_discernment = percentile_to_attribute(k_percentile, invert=True)
    swing_decision_latency = percentile_to_attribute(k_percentile, invert=True)

    # BB% → ZONE_DISCERNMENT (also contributes)
    # MLB average ~8%, elite >12%
    bb_percentile = get_stat('bb_pct_percentile', 50.0)
    zone_discernment = (zone_discernment + percentile_to_attribute(bb_percentile)) / 2

    # Launch Angle → ATTACK_ANGLE_CONTROL
    # MLB average ~12°, fly ball hitters ~20°, ground ball hitters ~5°
    la_percentile = get_stat('launch_angle_avg_percentile', 50.0)
    attack_angle_control = percentile_to_attribute(la_percentile)

    # Hard Hit% → Contributes to BAT_SPEED and BARREL_ACCURACY
    # MLB average ~40%, elite >50%
    hh_percentile = get_stat('hard_hit_pct_percentile', 50.0)
    bat_speed = (bat_speed + percentile_to_attribute(hh_percentile)) / 2
    barrel_accuracy = (barrel_accuracy + percentile_to_attribute(hh_percentile)) / 2

    # Pull% / Oppo% → SPRAY_TENDENCY
    # >40% pull → high spray tendency (pull hitter)
    # >30% oppo → low spray tendency (oppo hitter)
    pull_pct = get_stat('pull_pct', 40.0)
    oppo_pct = get_stat('oppo_pct', 30.0)
    if pull_pct > oppo_pct + 10:
        # Pull hitter: 60-85th percentile → 60,000-85,000
        spray_tendency = 60000 + (pull_pct - 40) * 1000
    elif oppo_pct > pull_pct + 10:
        # Opposite field hitter: 15-40th percentile → 15,000-40,000
        spray_tendency = 40000 - (oppo_pct - 30) * 1000
    else:
        # Balanced hitter: around 50,000
        spray_tendency = 50000
    spray_tendency = np.clip(spray_tendency, 0, 100000)

    # ATTACK_ANGLE_VARIANCE → based on consistency (use default good consistency)
    attack_angle_variance = 55000  # Slightly above average consistency

    # TIMING_PRECISION → correlates with K% and contact rate
    timing_precision = percentile_to_attribute(k_percentile, invert=True)

    # PITCH_PLANE_MATCH → correlates with contact ability
    contact_pct = 100 - get_stat('k_pct', 22.0)
    contact_percentile = (contact_pct - 60) / 20 * 50 + 50  # Rough approximation
    contact_percentile = np.clip(contact_percentile, 0, 100)
    pitch_plane_match = percentile_to_attribute(contact_percentile)

    # IMPACT_SPIN_GAIN, LAUNCH_OFFSET_CONTROL → use defaults (hard to measure from stats)
    impact_spin_gain = 50000
    launch_offset_control = 50000

    return HitterAttributes(
        BAT_SPEED=bat_speed,
        ATTACK_ANGLE_CONTROL=attack_angle_control,
        ATTACK_ANGLE_VARIANCE=attack_angle_variance,
        BARREL_ACCURACY=barrel_accuracy,
        TIMING_PRECISION=timing_precision,
        PITCH_PLANE_MATCH=pitch_plane_match,
        IMPACT_SPIN_GAIN=impact_spin_gain,
        LAUNCH_OFFSET_CONTROL=launch_offset_control,
        SWING_DECISION_LATENCY=swing_decision_latency,
        ZONE_DISCERNMENT=zone_discernment,
        SPRAY_TENDENCY=spray_tendency
    )


# =============================================================================
# PITCHER STAT MAPPING
# =============================================================================

def map_pitcher_stats_to_attributes(stats: Dict) -> PitcherAttributes:
    """
    Convert MLB pitching statistics to PitcherAttributes (0-100,000 scale).

    Key stat mappings:
    - Fastball Velocity (avg) → RAW_VELOCITY_CAP
    - Spin Rate → SPIN_RATE_CAP
    - K% or K/9 → DECEPTION, SPIN_EFFICIENCY
    - BB% or BB/9 → COMMAND (inverse), CONTROL (inverse)
    - Whiff% → DECEPTION
    - IP, Pitches → STAMINA

    Parameters
    ----------
    stats : dict
        Dictionary with player's stats and league percentiles
        Expected keys: 'velocity_avg', 'spin_rate', 'k_pct', 'bb_pct',
                      'whiff_pct', 'innings_pitched', etc.

    Returns
    -------
    PitcherAttributes
        Mapped attributes on 0-100,000 scale
    """
    # Helper to get stat with default
    def get_stat(key: str, default: float = 50.0) -> float:
        return stats.get(key, default)

    # Fastball velocity → RAW_VELOCITY_CAP
    # MLB average ~93 mph, elite 98+ mph
    velo_percentile = get_stat('velocity_avg_percentile', 50.0)
    raw_velocity_cap = percentile_to_attribute(velo_percentile)

    # Spin rate → SPIN_RATE_CAP
    # MLB average ~2250 rpm, elite 2600+ rpm
    spin_percentile = get_stat('spin_rate_percentile', 50.0)
    spin_rate_cap = percentile_to_attribute(spin_percentile)

    # K% → DECEPTION, SPIN_EFFICIENCY
    # MLB average ~22%, elite >28%
    k_percentile = get_stat('k_pct_percentile', 50.0)
    deception = percentile_to_attribute(k_percentile)
    spin_efficiency = percentile_to_attribute(k_percentile)

    # Whiff% → DECEPTION (also contributes)
    # MLB average ~25%, elite >30%
    whiff_percentile = get_stat('whiff_pct_percentile', 50.0)
    deception = (deception + percentile_to_attribute(whiff_percentile)) / 2

    # BB% → COMMAND, CONTROL (inverse - lower BB% is better)
    # MLB average ~8%, elite <5%
    bb_percentile = get_stat('bb_pct_percentile', 50.0)
    command = percentile_to_attribute(bb_percentile, invert=True)
    control = percentile_to_attribute(bb_percentile, invert=True)

    # IP or role → STAMINA
    role = get_stat('role', 'starter')
    if role == 'starter':
        # Starters: higher stamina (60,000-80,000)
        ip_percentile = get_stat('innings_pitched_percentile', 50.0)
        stamina = 60000 + percentile_to_attribute(ip_percentile) * 0.2
    else:
        # Relievers: lower stamina (30,000-50,000)
        stamina = 40000
    stamina = np.clip(stamina, 0, 100000)

    # FATIGUE_RESISTANCE → based on role and performance late in games
    fatigue_resistance = 50000 if role == 'starter' else 60000

    # SPIN_AXIS_CONTROL, RELEASE_EXTENSION, ARM_SLOT → use defaults
    spin_axis_control = 50000
    release_extension = 50000
    arm_slot = 50000
    release_height = 50000

    # TUNNELING → correlates with deception
    tunneling = deception

    return PitcherAttributes(
        RAW_VELOCITY_CAP=raw_velocity_cap,
        SPIN_RATE_CAP=spin_rate_cap,
        SPIN_EFFICIENCY=spin_efficiency,
        SPIN_AXIS_CONTROL=spin_axis_control,
        RELEASE_EXTENSION=release_extension,
        ARM_SLOT=arm_slot,
        RELEASE_HEIGHT=release_height,
        COMMAND=command,
        CONTROL=control,
        TUNNELING=tunneling,
        DECEPTION=deception,
        STAMINA=stamina,
        FATIGUE_RESISTANCE=fatigue_resistance
    )


# =============================================================================
# FIELDER STAT MAPPING
# =============================================================================

def map_fielder_stats_to_attributes(stats: Dict, position: str) -> FielderAttributes:
    """
    Convert MLB fielding statistics to FielderAttributes (0-100,000 scale).

    Key stat mappings:
    - Sprint Speed → TOP_SPRINT_SPEED
    - Outs Above Average → REACTION_TIME, ROUTE_EFFICIENCY, FIELDING_SECURE
    - Arm Strength (from position) → ARM_STRENGTH
    - Fielding% → FIELDING_SECURE

    Parameters
    ----------
    stats : dict
        Dictionary with player's stats and league percentiles
        Expected keys: 'sprint_speed', 'outs_above_avg', 'fielding_pct'
    position : str
        Defensive position (used for arm strength defaults)

    Returns
    -------
    FielderAttributes
        Mapped attributes on 0-100,000 scale
    """
    # Helper to get stat with default
    def get_stat(key: str, default: float = 50.0) -> float:
        return stats.get(key, default)

    # Sprint speed → TOP_SPRINT_SPEED
    # MLB average ~27 ft/s, elite >29 ft/s
    sprint_percentile = get_stat('sprint_speed_percentile', 50.0)
    top_sprint_speed = percentile_to_attribute(sprint_percentile)

    # Outs Above Average → REACTION_TIME, ROUTE_EFFICIENCY, FIELDING_SECURE
    oaa_percentile = get_stat('outs_above_avg_percentile', 50.0)
    reaction_time = percentile_to_attribute(oaa_percentile)
    route_efficiency = percentile_to_attribute(oaa_percentile)
    fielding_secure = percentile_to_attribute(oaa_percentile)

    # Position-based ARM_STRENGTH defaults
    # Catchers, SS, 3B, RF, CF: stronger arms
    # 1B, 2B, LF: weaker arms
    arm_strength_defaults = {
        'C': 60000, 'P': 45000,
        '1B': 40000, '2B': 50000, '3B': 65000, 'SS': 65000,
        'LF': 50000, 'CF': 60000, 'RF': 70000
    }
    arm_strength = arm_strength_defaults.get(position, 50000)

    # Fielding% → FIELDING_SECURE
    fielding_pct = get_stat('fielding_pct', 0.98)
    if fielding_pct >= 0.99:
        fielding_secure = (fielding_secure + 70000) / 2
    elif fielding_pct < 0.97:
        fielding_secure = (fielding_secure + 30000) / 2

    # ACCELERATION → correlates with sprint speed
    acceleration = top_sprint_speed

    # AGILITY → use sprint speed as proxy
    agility = top_sprint_speed

    # TRANSFER_TIME → use default (hard to measure)
    transfer_time = 50000

    # ARM_ACCURACY → use default (hard to measure from basic stats)
    arm_accuracy = 50000

    return FielderAttributes(
        REACTION_TIME=reaction_time,
        ACCELERATION=acceleration,
        TOP_SPRINT_SPEED=top_sprint_speed,
        ROUTE_EFFICIENCY=route_efficiency,
        AGILITY=agility,
        FIELDING_SECURE=fielding_secure,
        TRANSFER_TIME=transfer_time,
        ARM_STRENGTH=arm_strength,
        ARM_ACCURACY=arm_accuracy
    )


# =============================================================================
# PLAYER CREATION FROM MLB DATA
# =============================================================================

def create_hitter_from_mlb_stats(
    name: str,
    stats: Dict,
    position: str = 'RF'
) -> Hitter:
    """
    Create a Hitter object from MLB statistics.

    Parameters
    ----------
    name : str
        Player name
    stats : dict
        Hitting statistics with percentiles
    position : str
        Primary defensive position (for later fielder creation)

    Returns
    -------
    Hitter
        Complete Hitter object with mapped attributes
    """
    hitter_attrs = map_hitter_stats_to_attributes(stats)

    # Zone discipline and aggressiveness are already part of HitterAttributes
    return Hitter(
        name=name,
        attributes=hitter_attrs
    )


def create_fielder_from_mlb_stats(
    name: str,
    position: str,
    fielder_stats: Optional[Dict] = None
) -> Fielder:
    """
    Create a Fielder object from MLB statistics.

    Parameters
    ----------
    name : str
        Player name
    position : str
        Defensive position (e.g., 'RF', 'SS', '1B')
    fielder_stats : dict, optional
        Fielding statistics with percentiles

    Returns
    -------
    Fielder
        Complete Fielder object with mapped attributes
    """
    if fielder_stats is None:
        fielder_stats = {}

    fielder_attrs = map_fielder_stats_to_attributes(fielder_stats, position)

    # Determine position type for Fielder constructor
    position_types = {
        'C': 'catcher',
        'P': 'pitcher',
        '1B': 'infield', '2B': 'infield', '3B': 'infield', 'SS': 'infield',
        'LF': 'outfield', 'CF': 'outfield', 'RF': 'outfield'
    }
    position_type = position_types.get(position, 'outfield')

    return Fielder(
        name=name,
        position=position_type,
        attributes=fielder_attrs
    )


def create_pitcher_from_mlb_stats(
    name: str,
    stats: Dict,
    role: str = 'starter'
) -> Pitcher:
    """
    Create a Pitcher object from MLB statistics.

    Parameters
    ----------
    name : str
        Player name
    stats : dict
        Pitching statistics with percentiles
    role : str
        'starter' or 'reliever'

    Returns
    -------
    Pitcher
        Complete Pitcher object with mapped attributes
    """
    stats['role'] = role
    pitcher_attrs = map_pitcher_stats_to_attributes(stats)

    # Generate pitch arsenal based on pitcher attributes
    pitch_arsenal = generate_pitch_arsenal(pitcher_attrs, role=role)

    return Pitcher(
        name=name,
        attributes=pitcher_attrs,
        pitch_arsenal=pitch_arsenal
    )


# =============================================================================
# MLB DATA FETCHING (requires pybaseball)
# =============================================================================

def fetch_player_batting_stats(player_name: str, season: int = 2024) -> Optional[Dict]:
    """
    Fetch batting statistics for a player from pybaseball.

    Parameters
    ----------
    player_name : str
        Player's full name (e.g., "Aaron Judge")
    season : int
        MLB season year

    Returns
    -------
    dict or None
        Dictionary with stats and percentiles, or None if not found
    """
    if not PYBASEBALL_AVAILABLE:
        warnings.warn(f"pybaseball not available - cannot fetch stats for {player_name}. Using league average.")
        return None

    # Split name
    parts = player_name.split()
    if len(parts) < 2:
        return None
    first_name, last_name = parts[0], parts[-1]

    try:
        # Lookup player ID
        player_id_df = pyb.playerid_lookup(last_name, first_name)
        if player_id_df.empty:
            return None

        # Get stats for the season
        stats_df = pyb.batting_stats(season, season)
        player_stats = stats_df[stats_df['Name'].str.contains(player_name, case=False)]

        if player_stats.empty:
            return None

        player_row = player_stats.iloc[0]

        # Calculate percentiles within league
        stats = {}

        # Exit velocity (if available from Statcast)
        if 'EV' in player_row:
            ev = player_row['EV']
            stats['exit_velocity_avg'] = ev
            stats['exit_velocity_avg_percentile'] = stat_to_percentile(ev, stats_df['EV'].tolist())

        # Barrel %
        if 'Barrel%' in player_row:
            barrel = player_row['Barrel%']
            stats['barrel_pct'] = barrel
            stats['barrel_pct_percentile'] = stat_to_percentile(barrel, stats_df['Barrel%'].tolist())

        # K%
        if 'K%' in player_row:
            k_pct = player_row['K%']
            stats['k_pct'] = k_pct
            stats['k_pct_percentile'] = stat_to_percentile(k_pct, stats_df['K%'].tolist())

        # BB%
        if 'BB%' in player_row:
            bb_pct = player_row['BB%']
            stats['bb_pct'] = bb_pct
            stats['bb_pct_percentile'] = stat_to_percentile(bb_pct, stats_df['BB%'].tolist())

        # Launch angle
        if 'LA' in player_row:
            la = player_row['LA']
            stats['launch_angle_avg'] = la
            stats['launch_angle_avg_percentile'] = stat_to_percentile(la, stats_df['LA'].tolist())

        # Hard Hit %
        if 'HardHit%' in player_row:
            hh = player_row['HardHit%']
            stats['hard_hit_pct'] = hh
            stats['hard_hit_pct_percentile'] = stat_to_percentile(hh, stats_df['HardHit%'].tolist())

        # Pull%, Oppo%
        if 'Pull%' in player_row:
            stats['pull_pct'] = player_row['Pull%']
        if 'Oppo%' in player_row:
            stats['oppo_pct'] = player_row['Oppo%']

        return stats

    except Exception as e:
        warnings.warn(f"Error fetching stats for {player_name}: {e}")
        return None


def fetch_player_pitching_stats(player_name: str, season: int = 2024) -> Optional[Dict]:
    """
    Fetch pitching statistics for a player from pybaseball.

    Parameters
    ----------
    player_name : str
        Player's full name
    season : int
        MLB season year

    Returns
    -------
    dict or None
        Dictionary with stats and percentiles, or None if not found
    """
    if not PYBASEBALL_AVAILABLE:
        warnings.warn(f"pybaseball not available - cannot fetch stats for {player_name}. Using league average.")
        return None

    try:
        # Get pitching stats
        stats_df = pyb.pitching_stats(season, season)
        player_stats = stats_df[stats_df['Name'].str.contains(player_name, case=False)]

        if player_stats.empty:
            return None

        player_row = player_stats.iloc[0]
        stats = {}

        # Velocity
        if 'vFA (pi)' in player_row:  # Fastball velocity
            velo = player_row['vFA (pi)']
            stats['velocity_avg'] = velo
            stats['velocity_avg_percentile'] = stat_to_percentile(velo, stats_df['vFA (pi)'].tolist())

        # K%
        if 'K%' in player_row:
            k_pct = player_row['K%']
            stats['k_pct'] = k_pct
            stats['k_pct_percentile'] = stat_to_percentile(k_pct, stats_df['K%'].tolist())

        # BB%
        if 'BB%' in player_row:
            bb_pct = player_row['BB%']
            stats['bb_pct'] = bb_pct
            stats['bb_pct_percentile'] = stat_to_percentile(bb_pct, stats_df['BB%'].tolist())

        # Whiff%
        if 'SwStr%' in player_row:  # Swinging strike % as proxy for whiff%
            whiff = player_row['SwStr%']
            stats['whiff_pct'] = whiff
            stats['whiff_pct_percentile'] = stat_to_percentile(whiff, stats_df['SwStr%'].tolist())

        # Innings pitched
        if 'IP' in player_row:
            ip = player_row['IP']
            stats['innings_pitched'] = ip
            stats['innings_pitched_percentile'] = stat_to_percentile(ip, stats_df['IP'].tolist())

        # Determine role (starter vs reliever)
        if 'GS' in player_row and 'G' in player_row:
            gs = player_row['GS']
            g = player_row['G']
            if gs / max(g, 1) > 0.5:
                stats['role'] = 'starter'
            else:
                stats['role'] = 'reliever'

        return stats

    except Exception as e:
        warnings.warn(f"Error fetching stats for {player_name}: {e}")
        return None


# =============================================================================
# TEAM CREATION FROM MLB ROSTER
# =============================================================================

def create_team_from_mlb_roster(
    team_name: str,
    roster_hitters: List[Tuple[str, str]],  # (name, position) pairs
    roster_pitchers: List[Tuple[str, str]],  # (name, role) pairs
    season: int = 2024
) -> Team:
    """
    Create a Team object from MLB roster data.

    Parameters
    ----------
    team_name : str
        Team name
    roster_hitters : list of (str, str)
        List of (player_name, position) tuples for hitters
    roster_pitchers : list of (str, str)
        List of (player_name, role) tuples for pitchers
    season : int
        MLB season year

    Returns
    -------
    Team
        Complete Team object with real MLB players

    Example
    -------
    >>> roster_hitters = [
    ...     ("Aaron Judge", "RF"),
    ...     ("Juan Soto", "LF"),
    ...     # ... 7 more hitters
    ... ]
    >>> roster_pitchers = [
    ...     ("Gerrit Cole", "starter"),
    ...     ("Carlos Rodon", "starter"),
    ...     # ... more pitchers
    ... ]
    >>> yankees = create_team_from_mlb_roster("Yankees", roster_hitters, roster_pitchers, 2024)
    """
    hitters = []
    for player_name, position in roster_hitters:
        stats = fetch_player_batting_stats(player_name, season)
        if stats is None:
            # Use league average if player not found
            stats = {}
        hitter = create_hitter_from_mlb_stats(player_name, stats, position=position)
        hitters.append(hitter)

    pitchers = []
    for player_name, role in roster_pitchers:
        stats = fetch_player_pitching_stats(player_name, season)
        if stats is None:
            # Use league average if player not found
            stats = {}
        pitcher = create_pitcher_from_mlb_stats(player_name, stats, role=role)
        pitchers.append(pitcher)

    # Create fielders from hitters (skip DH as they don't play defense)
    fielders = {}
    for i, (player_name, position) in enumerate(roster_hitters):
        # Skip designated hitter - they don't have a defensive position
        if position == 'DH':
            continue
        fielder = create_fielder_from_mlb_stats(player_name, position)
        # Map position abbreviation (e.g., 'RF') to full name (e.g., 'right_field')
        position_full_name = map_position_abbreviation_to_full_name(position)
        fielders[position_full_name] = fielder
        # Stop after we have 8 position players (pitcher will be added separately)
        if len(fielders) >= 8:
            break

    # Add pitcher as a fielder (use the first pitcher in the rotation)
    if pitchers:
        pitcher_name = roster_pitchers[0][0] if roster_pitchers else "Pitcher"
        pitcher_fielder = create_fielder_from_mlb_stats(pitcher_name, 'P')
        fielders['pitcher'] = pitcher_fielder

    return Team(
        name=team_name,
        pitchers=pitchers,
        hitters=hitters,
        fielders=fielders
    )


# =============================================================================
# CONVENIENCE FUNCTIONS
# =============================================================================

def create_mlb_player(player_name: str, season: int = 2024, role: str = 'hitter'):
    """
    Create a player from MLB data (convenience function).

    Parameters
    ----------
    player_name : str
        Player's full name
    season : int
        MLB season year
    role : str
        'hitter', 'pitcher', or 'starter'/'reliever'

    Returns
    -------
    Hitter or Pitcher
        Player object with attributes mapped from MLB stats
    """
    if role == 'hitter':
        stats = fetch_player_batting_stats(player_name, season)
        if stats is None:
            stats = {}
        return create_hitter_from_mlb_stats(player_name, stats)
    else:
        stats = fetch_player_pitching_stats(player_name, season)
        if stats is None:
            stats = {}
        pitcher_role = 'starter' if role in ['pitcher', 'starter'] else 'reliever'
        return create_pitcher_from_mlb_stats(player_name, stats, role=pitcher_role)


__all__ = [
    'PYBASEBALL_AVAILABLE',
    'map_position_abbreviation_to_full_name',
    'percentile_to_attribute',
    'stat_to_percentile',
    'map_hitter_stats_to_attributes',
    'map_pitcher_stats_to_attributes',
    'map_fielder_stats_to_attributes',
    'create_hitter_from_mlb_stats',
    'create_fielder_from_mlb_stats',
    'create_pitcher_from_mlb_stats',
    'fetch_player_batting_stats',
    'fetch_player_pitching_stats',
    'create_team_from_mlb_roster',
    'create_mlb_player',
]
