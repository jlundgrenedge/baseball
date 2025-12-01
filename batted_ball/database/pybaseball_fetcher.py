"""
Fetch MLB player statistics using pybaseball.

Provides a clean interface to retrieve pitcher and hitter stats from MLB data
sources including Baseball Savant, FanGraphs, and Baseball Reference.

Can also load data from pre-downloaded Baseball Savant CSV files in 
data/bballsavant/{season}/ for faster, more reliable access.
"""

import pandas as pd
from typing import List, Dict, Optional, Tuple
import warnings

# Suppress pybaseball warnings
warnings.filterwarnings('ignore')

# Try to import the CSV loader for Baseball Savant data
try:
    from .savant_csv_loader import SavantCSVLoader
    SAVANT_CSV_AVAILABLE = True
except ImportError:
    SAVANT_CSV_AVAILABLE = False

try:
    from pybaseball import (
        pitching_stats,
        batting_stats,
        statcast_pitcher,
        statcast_batter,
        playerid_lookup,
        team_pitching,
        team_batting,
        statcast_sprint_speed,
        fielding_stats,             # v2: For DRS and traditional fielding metrics
    )
    # Try to import Statcast fielding functions (may not be available in all versions)
    try:
        from pybaseball import statcast_outs_above_average, statcast_outfielder_jump
        STATCAST_FIELDING_AVAILABLE = True
    except ImportError:
        STATCAST_FIELDING_AVAILABLE = False

    PYBASEBALL_AVAILABLE = True
except ImportError:
    PYBASEBALL_AVAILABLE = False
    STATCAST_FIELDING_AVAILABLE = False
    print("Warning: pybaseball not installed. Run: pip install pybaseball")

# For arm strength data - need to fetch directly from Baseball Savant
import requests
from io import StringIO


class PybaseballFetcher:
    """Fetch MLB statistics using pybaseball library."""

    def __init__(self, season: int = 2024):
        """
        Initialize fetcher for a specific season.

        Parameters
        ----------
        season : int
            MLB season year (e.g., 2024)
        """
        if not PYBASEBALL_AVAILABLE:
            raise ImportError("pybaseball is not installed. Run: pip install pybaseball")

        self.season = season

    def get_team_pitchers(
        self,
        team_abbr: str,
        min_innings: float = 20.0,
        include_statcast: bool = True
    ) -> pd.DataFrame:
        """
        Get all pitchers for a team with their statistics.

        Parameters
        ----------
        team_abbr : str
            Team abbreviation (e.g., 'NYY', 'LAD', 'BOS')
        min_innings : float
            Minimum innings pitched to include
        include_statcast : bool
            Whether to include Statcast data (exit velo, etc.)

        Returns
        -------
        pd.DataFrame
            Pitcher statistics with columns:
            - Name, Team, IP, ERA, WHIP, K/9, BB/9, avg_fastball_velo, etc.
        """
        # Get FanGraphs pitching stats for the season
        print(f"Fetching pitcher stats for {team_abbr} ({self.season})...")
        try:
            # Get all pitching stats for the season
            stats = pitching_stats(self.season, qual=0)  # qual=0 gets all players

            # Filter by team
            team_stats = stats[stats['Team'] == team_abbr].copy()

            # Filter by minimum innings
            team_stats = team_stats[team_stats['IP'] >= min_innings]

            # Select and rename key columns
            columns_map = {
                'Name': 'player_name',
                'Team': 'team',
                'IP': 'innings_pitched',
                'G': 'games_pitched',
                'GS': 'games_started',
                'ERA': 'era',
                'WHIP': 'whip',
                'K/9': 'k_per_9',
                'BB/9': 'bb_per_9',
                'FIP': 'fip',
                'SO': 'strikeouts',
                'BB': 'walks',
                'Pitches': 'pitches_thrown',
            }

            # Keep only columns that exist
            available_cols = [col for col in columns_map.keys() if col in team_stats.columns]
            pitcher_df = team_stats[available_cols].copy()
            pitcher_df.rename(columns=columns_map, inplace=True)

            # Add season
            pitcher_df['season'] = self.season

            # Try to add Statcast velocity data
            if include_statcast and 'avg_fastball_velo' not in pitcher_df.columns:
                # FanGraphs might have velocity as 'vFA (pi)'
                if 'vFA (pi)' in team_stats.columns:
                    pitcher_df['avg_fastball_velo'] = team_stats['vFA (pi)']
                elif 'FB%' in team_stats.columns:
                    # Estimate based on FanGraphs data - typically available as velocity column
                    # This is a fallback - Statcast would be better
                    pitcher_df['avg_fastball_velo'] = None

            print(f"  Found {len(pitcher_df)} pitchers")
            return pitcher_df.reset_index(drop=True)

        except Exception as e:
            print(f"Error fetching pitcher stats: {e}")
            return pd.DataFrame()

    def get_team_hitters(
        self,
        team_abbr: str,
        min_at_bats: int = 50,
        include_statcast: bool = True
    ) -> pd.DataFrame:
        """
        Get all hitters for a team with their statistics.

        Parameters
        ----------
        team_abbr : str
            Team abbreviation (e.g., 'NYY', 'LAD', 'BOS')
        min_at_bats : int
            Minimum at-bats to include
        include_statcast : bool
            Whether to include Statcast data (exit velo, barrel%, sprint speed)

        Returns
        -------
        pd.DataFrame
            Hitter statistics with columns:
            - Name, Team, AB, AVG, OBP, SLG, OPS, HR, BB, SO, etc.
        """
        # Get FanGraphs batting stats for the season
        print(f"Fetching hitter stats for {team_abbr} ({self.season})...")
        try:
            # Get all batting stats for the season
            stats = batting_stats(self.season, qual=0)  # qual=0 gets all players

            # Filter by team
            team_stats = stats[stats['Team'] == team_abbr].copy()

            # Filter by minimum at-bats
            team_stats = team_stats[team_stats['AB'] >= min_at_bats]

            # Select and rename key columns
            columns_map = {
                'Name': 'player_name',
                'Team': 'team',
                'G': 'games_played',
                'AB': 'at_bats',
                'PA': 'plate_appearances',
                'H': 'hits',
                'HR': 'home_runs',
                'R': 'runs',
                'RBI': 'rbi',
                'SB': 'stolen_bases',
                'BB': 'walks',
                'SO': 'strikeouts',
                'AVG': 'batting_avg',
                'OBP': 'on_base_pct',
                'SLG': 'slugging_pct',
                'OPS': 'ops',
                'wOBA': 'woba',
                'wRC+': 'wrc_plus',
            }

            # Keep only columns that exist
            available_cols = [col for col in columns_map.keys() if col in team_stats.columns]
            hitter_df = team_stats[available_cols].copy()
            hitter_df.rename(columns=columns_map, inplace=True)

            # Add season
            hitter_df['season'] = self.season

            # Try to add Statcast data if available
            if include_statcast:
                # FanGraphs often has Barrel%, HardHit%, etc.
                if 'Barrel%' in team_stats.columns:
                    hitter_df['barrel_pct'] = team_stats['Barrel%']
                if 'HardHit%' in team_stats.columns:
                    hitter_df['hard_hit_pct'] = team_stats['HardHit%']
                if 'EV' in team_stats.columns:
                    hitter_df['avg_exit_velo'] = team_stats['EV']
                if 'maxEV' in team_stats.columns:
                    hitter_df['max_exit_velo'] = team_stats['maxEV']
                if 'Sprint Speed' in team_stats.columns:
                    hitter_df['sprint_speed'] = team_stats['Sprint Speed']

                # Try to fetch Statcast sprint speed data (only available 2015+)
                if self.season >= 2015:
                    try:
                        print(f"  Fetching Statcast sprint speed data...")
                        sprint_data = statcast_sprint_speed(self.season, min_opp=10)

                        if sprint_data is not None and len(sprint_data) > 0:
                            # Merge sprint speed by player name
                            # Note: Name matching can be tricky, so we'll do our best
                            sprint_data = sprint_data.rename(columns={
                                'last_name, first_name': 'full_name',
                                'sprint_speed': 'sprint_speed_statcast'
                            })

                            # Try to match players by name
                            for idx, row in hitter_df.iterrows():
                                player_name = row['player_name']
                                # Try exact match first
                                match = sprint_data[sprint_data['full_name'] == player_name]
                                if len(match) == 0:
                                    # Try partial match (last name)
                                    last_name = player_name.split()[-1] if ' ' in player_name else player_name
                                    match = sprint_data[sprint_data['full_name'].str.contains(last_name, case=False, na=False)]

                                if len(match) > 0:
                                    # Take first match
                                    hitter_df.at[idx, 'sprint_speed'] = match.iloc[0]['sprint_speed_statcast']

                            print(f"  Added sprint speed for {hitter_df['sprint_speed'].notna().sum()} players")
                    except Exception as e:
                        print(f"  Could not fetch Statcast sprint speed: {e}")

            print(f"  Found {len(hitter_df)} hitters")
            return hitter_df.reset_index(drop=True)

        except Exception as e:
            print(f"Error fetching hitter stats: {e}")
            return pd.DataFrame()

    def get_team_roster(
        self,
        team_abbr: str,
        min_pitcher_innings: float = 20.0,
        min_hitter_at_bats: int = 50
    ) -> Tuple[pd.DataFrame, pd.DataFrame]:
        """
        Get complete team roster (pitchers and hitters).

        Parameters
        ----------
        team_abbr : str
            Team abbreviation
        min_pitcher_innings : float
            Minimum innings for pitchers
        min_hitter_at_bats : int
            Minimum at-bats for hitters

        Returns
        -------
        tuple of (pitchers_df, hitters_df)
            Two DataFrames with pitcher and hitter statistics
        """
        pitchers = self.get_team_pitchers(team_abbr, min_pitcher_innings)
        hitters = self.get_team_hitters(team_abbr, min_hitter_at_bats)

        # Add defensive metrics to hitters (v2 addition for BABIP tuning)
        hitters = self._add_defensive_metrics(hitters, team_abbr)

        return pitchers, hitters

    def _add_defensive_metrics(
        self,
        hitters_df: pd.DataFrame,
        team_abbr: str
    ) -> pd.DataFrame:
        """
        Add defensive metrics to hitter DataFrame (v2 addition).

        Fetches OAA, DRS, arm strength, and fielding % from Statcast and FanGraphs.

        Parameters
        ----------
        hitters_df : pd.DataFrame
            Hitter statistics DataFrame
        team_abbr : str
            Team abbreviation

        Returns
        -------
        pd.DataFrame
            Hitter DataFrame with defensive metrics added
        """
        if len(hitters_df) == 0:
            return hitters_df

        print(f"  Fetching defensive metrics...")

        # Initialize defensive columns
        hitters_df['oaa'] = None
        hitters_df['drs'] = None
        hitters_df['arm_strength_mph'] = None
        hitters_df['fielding_pct'] = None
        hitters_df['jump'] = None
        hitters_df['jump_oaa'] = None       # Statcast Jump: OAA from jump metrics (outfielders only)
        hitters_df['jump_reaction'] = None  # Statcast Jump: reaction component (feet in first 1.5s)
        hitters_df['jump_burst'] = None     # Statcast Jump: burst component (feet in second 1.5s)
        hitters_df['jump_route'] = None     # Statcast Jump: route component (feet from direction)
        hitters_df['back_oaa'] = None       # Directional OAA: sum of back slices (back_left + back + back_right)
        hitters_df['in_oaa'] = None         # Directional OAA: sum of in slices (in_left + in + in_right)
        hitters_df['catch_5star_pct'] = None  # Catch probability: 5-star plays (0-25% expected)
        hitters_df['catch_34star_pct'] = None # Catch probability: 3-4 star plays (25-75% expected)
        hitters_df['primary_position'] = None
        
        # Initialize bat tracking columns
        hitters_df['bat_speed'] = None
        hitters_df['swing_length'] = None
        hitters_df['squared_up_rate'] = None
        hitters_df['hard_swing_rate'] = None
        
        # 0. Try to load from Baseball Savant CSV files first (faster, more reliable)
        csv_jump_loaded = 0
        csv_oaa_loaded = 0
        if SAVANT_CSV_AVAILABLE:
            try:
                savant = SavantCSVLoader(season=self.season)
                
                # Check if CSV data is available
                if savant.jump_df is not None or savant.oaa_df is not None:
                    print(f"    Loading from Baseball Savant CSV files...")
                    
                    for idx, row in hitters_df.iterrows():
                        player_name = row['player_name']
                        
                        # Load Jump data (outfielders)
                        jump_data = savant.get_jump_data(player_name)
                        if jump_data:
                            if jump_data.get('bootup_ft') is not None:
                                hitters_df.at[idx, 'jump'] = jump_data['bootup_ft']
                            if jump_data.get('oaa') is not None:
                                hitters_df.at[idx, 'jump_oaa'] = jump_data['oaa']
                            if jump_data.get('reaction_ft') is not None:
                                hitters_df.at[idx, 'jump_reaction'] = jump_data['reaction_ft']
                            if jump_data.get('burst_ft') is not None:
                                hitters_df.at[idx, 'jump_burst'] = jump_data['burst_ft']
                            if jump_data.get('route_ft') is not None:
                                hitters_df.at[idx, 'jump_route'] = jump_data['route_ft']
                            csv_jump_loaded += 1
                        
                        # Load OAA data
                        oaa_data = savant.get_oaa_data(player_name)
                        if oaa_data:
                            if oaa_data.get('oaa') is not None:
                                hitters_df.at[idx, 'oaa'] = oaa_data['oaa']
                            if oaa_data.get('fielding_runs_prevented') is not None:
                                # Store as extra data if needed
                                pass
                            if oaa_data.get('position'):
                                hitters_df.at[idx, 'primary_position'] = oaa_data['position']
                            csv_oaa_loaded += 1
                        
                        # Load Directional OAA data (for RANGE_BACK and RANGE_IN attributes)
                        dir_oaa = savant.get_directional_oaa(player_name)
                        if dir_oaa:
                            # Sum back slices for back_oaa
                            back_left = dir_oaa.get('oaa_back_left') or 0
                            back_center = dir_oaa.get('oaa_back') or 0
                            back_right = dir_oaa.get('oaa_back_right') or 0
                            back_total = back_left + back_center + back_right
                            if any([dir_oaa.get('oaa_back_left'), dir_oaa.get('oaa_back'), 
                                    dir_oaa.get('oaa_back_right')]):
                                hitters_df.at[idx, 'back_oaa'] = back_total
                            
                            # Sum in slices for in_oaa
                            in_left = dir_oaa.get('oaa_in_left') or 0
                            in_center = dir_oaa.get('oaa_in') or 0
                            in_right = dir_oaa.get('oaa_in_right') or 0
                            in_total = in_left + in_center + in_right
                            if any([dir_oaa.get('oaa_in_left'), dir_oaa.get('oaa_in'),
                                    dir_oaa.get('oaa_in_right')]):
                                hitters_df.at[idx, 'in_oaa'] = in_total
                        
                        # Load Catch Probability data (for CATCH_ELITE and CATCH_DIFFICULT attributes)
                        catch_prob = savant.get_catch_probability(player_name)
                        if catch_prob:
                            # 5-star plays (hardest, 0-25% expected)
                            if catch_prob.get('5star_pct') is not None:
                                hitters_df.at[idx, 'catch_5star_pct'] = catch_prob['5star_pct']
                            
                            # Combined 3-4 star plays (difficult, 25-75% expected)
                            # Calculate weighted average of 3-star and 4-star catch rates
                            star3_made = catch_prob.get('3star_made') or 0
                            star3_opp = catch_prob.get('3star_opp') or 0
                            star4_made = catch_prob.get('4star_made') or 0
                            star4_opp = catch_prob.get('4star_opp') or 0
                            
                            total_opp = star3_opp + star4_opp
                            if total_opp > 0:
                                combined_pct = ((star3_made + star4_made) / total_opp) * 100
                                hitters_df.at[idx, 'catch_34star_pct'] = combined_pct
                        
                        # Load Bat Tracking data (bat speed, squared-up rate, swing length)
                        bat_tracking = savant.get_bat_tracking(player_name)
                        if bat_tracking:
                            if bat_tracking.get('avg_bat_speed') is not None:
                                hitters_df.at[idx, 'bat_speed'] = bat_tracking['avg_bat_speed']
                            if bat_tracking.get('swing_length') is not None:
                                hitters_df.at[idx, 'swing_length'] = bat_tracking['swing_length']
                            if bat_tracking.get('squared_up_per_swing') is not None:
                                hitters_df.at[idx, 'squared_up_rate'] = bat_tracking['squared_up_per_swing']
                            if bat_tracking.get('hard_swing_rate') is not None:
                                hitters_df.at[idx, 'hard_swing_rate'] = bat_tracking['hard_swing_rate']
                    
                    if csv_jump_loaded > 0:
                        print(f"    Loaded Jump data for {csv_jump_loaded} players from CSV")
                    if csv_oaa_loaded > 0:
                        print(f"    Loaded OAA data for {csv_oaa_loaded} players from CSV")
                    
                    # Count bat tracking loaded
                    csv_bat_loaded = hitters_df['bat_speed'].notna().sum()
                    if csv_bat_loaded > 0:
                        print(f"    Loaded Bat Tracking data for {csv_bat_loaded} players from CSV")
                        
            except Exception as e:
                print(f"    Could not load from CSV files: {e}")

        try:
            # 1. Fetch Statcast fielding data (OAA, arm strength, jump)
            # Note: Statcast fielding data only available 2016+ and in newer pybaseball versions
            if self.season >= 2016 and STATCAST_FIELDING_AVAILABLE:
                try:
                    print(f"    Fetching Statcast fielding data (OAA)...")
                    # Use statcast_outs_above_average if available
                    statcast_defense = statcast_outs_above_average(self.season)

                    if statcast_defense is not None and len(statcast_defense) > 0:
                        # Match players by name
                        for idx, row in hitters_df.iterrows():
                            player_name = row['player_name']

                            # Try different name column possibilities
                            name_columns = ['last_name, first_name', 'name', 'player_name']
                            match = None

                            for name_col in name_columns:
                                if name_col in statcast_defense.columns:
                                    # Try exact match
                                    match = statcast_defense[
                                        statcast_defense[name_col] == player_name
                                    ]

                                    if len(match) == 0:
                                        # Try partial match (last name)
                                        last_name = player_name.split()[-1] if ' ' in player_name else player_name
                                        match = statcast_defense[
                                            statcast_defense[name_col].str.contains(
                                                last_name, case=False, na=False
                                            )
                                        ]

                                    if len(match) > 0:
                                        break

                            if match is not None and len(match) > 0:
                                player_defense = match.iloc[0]

                                # OAA (Outs Above Average)
                                oaa_columns = ['outs_above_average', 'oaa', 'outs_above_avg']
                                for col in oaa_columns:
                                    if col in player_defense.index and pd.notna(player_defense[col]):
                                        hitters_df.at[idx, 'oaa'] = player_defense[col]
                                        break

                                # Arm strength (mph) - might not be in OAA data
                                if 'arm_strength' in player_defense.index and pd.notna(player_defense['arm_strength']):
                                    hitters_df.at[idx, 'arm_strength_mph'] = player_defense['arm_strength']

                                # Jump (outfielders first step efficiency)
                                if 'jump' in player_defense.index and pd.notna(player_defense['jump']):
                                    hitters_df.at[idx, 'jump'] = player_defense['jump']

                        oaa_count = hitters_df['oaa'].notna().sum()
                        print(f"    Added OAA for {oaa_count} players")

                except Exception as e:
                    print(f"    Could not fetch Statcast fielding data: {e}")
                    print(f"    Will use DRS-based estimates instead")
            else:
                if self.season < 2016:
                    print(f"    Statcast fielding data not available before 2016")
                else:
                    print(f"    Statcast fielding functions not available in this pybaseball version")
                print(f"    Will derive defensive metrics from DRS")

            # 1b. Fetch arm strength data from Baseball Savant (direct scrape)
            # This data is not available via pybaseball functions
            if self.season >= 2020:  # Arm strength data reliable from 2020+
                try:
                    print(f"    Fetching Baseball Savant arm strength data...")
                    arm_data = self._fetch_arm_strength_leaderboard()
                    
                    if arm_data is not None and len(arm_data) > 0:
                        arm_count = 0
                        for idx, row in hitters_df.iterrows():
                            player_name = row['player_name']
                            
                            # Try to match by name (format: "Last, First" in savant data)
                            if ' ' in player_name:
                                parts = player_name.split()
                                # Try "Last, First" format
                                last_first = f"{parts[-1]}, {parts[0]}"
                                match = arm_data[
                                    arm_data['fielder_name'].str.contains(last_first, case=False, na=False)
                                ]
                                
                                if len(match) == 0:
                                    # Try just last name
                                    match = arm_data[
                                        arm_data['fielder_name'].str.contains(parts[-1], case=False, na=False)
                                    ]
                            else:
                                match = arm_data[
                                    arm_data['fielder_name'].str.contains(player_name, case=False, na=False)
                                ]
                            
                            if len(match) > 0:
                                arm_mph = match.iloc[0]['arm_overall']
                                if pd.notna(arm_mph) and arm_mph > 0:
                                    hitters_df.at[idx, 'arm_strength_mph'] = float(arm_mph)
                                    arm_count += 1
                        
                        print(f"    Added arm strength for {arm_count} players")
                    
                except Exception as e:
                    print(f"    Could not fetch arm strength data: {e}")

            # 1c. Fetch bat tracking data from Baseball Savant (direct scrape)
            # Bat tracking metrics: bat speed, swing length, squared-up rate
            if self.season >= 2024:  # Bat tracking data available from 2024
                try:
                    print(f"    Fetching Baseball Savant bat tracking data...")
                    bat_data = self._fetch_bat_tracking_leaderboard()
                    
                    # Fallback: If season > 2024, also fetch 2024 data for players not in current season
                    # This helps when 2025+ data isn't fully populated yet
                    bat_data_fallback = None
                    if self.season > 2024:
                        bat_data_fallback = self._fetch_bat_tracking_leaderboard(season_override=2024)
                        if bat_data_fallback is not None:
                            print(f"    Also loaded 2024 bat tracking as fallback ({len(bat_data_fallback)} players)")
                    
                    if bat_data is not None and len(bat_data) > 0:
                        bat_count = 0
                        fallback_count = 0
                        
                        for idx, row in hitters_df.iterrows():
                            player_name = row['player_name']
                            
                            # Try to match by name (format: "Last, First" in savant data)
                            match = self._match_player_in_bat_tracking(player_name, bat_data)
                            
                            # If no match in current season, try fallback data
                            if match is None and bat_data_fallback is not None:
                                match = self._match_player_in_bat_tracking(player_name, bat_data_fallback)
                                if match is not None:
                                    fallback_count += 1
                            
                            if match is not None:
                                bat_row = match
                                
                                # Bat speed (mph) - e.g., 72.5 mph
                                if 'avg_bat_speed' in bat_row.index and pd.notna(bat_row['avg_bat_speed']):
                                    hitters_df.at[idx, 'bat_speed'] = float(bat_row['avg_bat_speed'])
                                
                                # Swing length (feet) - e.g., 7.2 ft
                                if 'swing_length' in bat_row.index and pd.notna(bat_row['swing_length']):
                                    hitters_df.at[idx, 'swing_length'] = float(bat_row['swing_length'])
                                
                                # Squared up rate (percentage) - e.g., 0.285 (28.5%)
                                if 'squared_up_per_swing' in bat_row.index and pd.notna(bat_row['squared_up_per_swing']):
                                    hitters_df.at[idx, 'squared_up_rate'] = float(bat_row['squared_up_per_swing'])
                                
                                # Hard swing rate (percentage) - swings 75+ mph
                                if 'hard_swing_rate' in bat_row.index and pd.notna(bat_row['hard_swing_rate']):
                                    hitters_df.at[idx, 'hard_swing_rate'] = float(bat_row['hard_swing_rate'])
                                
                                bat_count += 1
                        
                        if fallback_count > 0:
                            print(f"    Added bat tracking for {bat_count} players ({fallback_count} from 2024 fallback)")
                        else:
                            print(f"    Added bat tracking for {bat_count} players")
                    
                except Exception as e:
                    print(f"    Could not fetch bat tracking data: {e}")

            # 1d. Fetch Jump leaderboard from Baseball Savant (Reaction, Burst, Route components)
            # Jump = feet covered in right direction in first 3 seconds after pitch release
            if self.season >= 2020:  # Jump data available from 2020+
                try:
                    print(f"    Fetching Baseball Savant outfielder jump data...")
                    jump_data = self._fetch_jump_leaderboard()
                    
                    if jump_data is not None and len(jump_data) > 0:
                        jump_count = 0
                        
                        for idx, row in hitters_df.iterrows():
                            player_name = row['player_name']
                            position = row.get('primary_position', '')
                            
                            # Jump data is only relevant for outfielders
                            if position not in ['LF', 'CF', 'RF', 'OF']:
                                continue
                            
                            # Match player by name
                            match = None
                            if ' ' in player_name:
                                parts = player_name.split()
                                last_first = f"{parts[-1]}, {parts[0]}"
                                
                                # Get name column
                                name_col = 'player_name' if 'player_name' in jump_data.columns else 'name'
                                if name_col not in jump_data.columns:
                                    # Try to find any name-like column
                                    for col in jump_data.columns:
                                        if 'name' in col.lower():
                                            name_col = col
                                            break
                                
                                if name_col in jump_data.columns:
                                    match = jump_data[
                                        jump_data[name_col].str.contains(last_first, case=False, na=False)
                                    ]
                                    
                                    if len(match) == 0:
                                        # Try just last name
                                        match = jump_data[
                                            jump_data[name_col].str.contains(parts[-1], case=False, na=False)
                                        ]
                                        # Only use if unique match
                                        if len(match) > 1:
                                            match = pd.DataFrame()  # Reset - ambiguous
                            
                            if match is not None and len(match) > 0:
                                jump_row = match.iloc[0]
                                
                                # Reaction (feet in first 1.5s vs average)
                                if 'reaction_ft' in jump_row.index and pd.notna(jump_row['reaction_ft']):
                                    hitters_df.at[idx, 'jump_reaction'] = float(jump_row['reaction_ft'])
                                
                                # Burst (feet in second 1.5s vs average)
                                if 'burst_ft' in jump_row.index and pd.notna(jump_row['burst_ft']):
                                    hitters_df.at[idx, 'jump_burst'] = float(jump_row['burst_ft'])
                                
                                # Route (feet lost/gained from direction)
                                if 'route_ft' in jump_row.index and pd.notna(jump_row['route_ft']):
                                    hitters_df.at[idx, 'jump_route'] = float(jump_row['route_ft'])
                                
                                # Total Jump (feet vs average = Reaction + Burst + Route)
                                if 'jump_ft' in jump_row.index and pd.notna(jump_row['jump_ft']):
                                    hitters_df.at[idx, 'jump'] = float(jump_row['jump_ft'])
                                
                                jump_count += 1
                        
                        print(f"    Added jump data for {jump_count} outfielders")
                    
                except Exception as e:
                    print(f"    Could not fetch jump leaderboard data: {e}")

            # 2. Fetch FanGraphs fielding data (DRS, fielding %, position)
            try:
                print(f"    Fetching FanGraphs fielding data (DRS)...")
                fg_defense = fielding_stats(self.season, qual=0)

                if fg_defense is not None and len(fg_defense) > 0:
                    # Filter by team
                    team_defense = fg_defense[fg_defense['Team'] == team_abbr].copy()

                    # Match players by name
                    for idx, row in hitters_df.iterrows():
                        player_name = row['player_name']

                        # Try exact match
                        match = team_defense[team_defense['Name'] == player_name]

                        if len(match) == 0:
                            # Try partial match
                            last_name = player_name.split()[-1] if ' ' in player_name else player_name
                            match = team_defense[
                                team_defense['Name'].str.contains(last_name, case=False, na=False)
                            ]

                        if len(match) > 0:
                            player_defense = match.iloc[0]

                            # DRS (Defensive Runs Saved)
                            if 'DRS' in player_defense.index:
                                hitters_df.at[idx, 'drs'] = player_defense['DRS']

                            # Fielding percentage
                            if 'Fld%' in player_defense.index:
                                hitters_df.at[idx, 'fielding_pct'] = player_defense['Fld%']

                            # Primary position
                            if 'Pos' in player_defense.index:
                                pos = player_defense['Pos']
                                # Clean up position (remove multi-position designations)
                                if isinstance(pos, str) and len(pos) > 0:
                                    # Take first position if multiple listed
                                    primary_pos = pos.split('/')[0].strip()
                                    hitters_df.at[idx, 'primary_position'] = primary_pos

                    drs_count = hitters_df['drs'].notna().sum()
                    print(f"    Added DRS for {drs_count} players")

            except Exception as e:
                print(f"    Could not fetch FanGraphs fielding data: {e}")

            # 3. Derive OAA from DRS when Statcast data unavailable
            # OAA and DRS measure similar things; OAA ≈ DRS * 0.6
            missing_oaa = hitters_df['oaa'].isna() & hitters_df['drs'].notna()
            if missing_oaa.sum() > 0:
                print(f"    Deriving OAA from DRS for {missing_oaa.sum()} players without Statcast data")
                hitters_df.loc[missing_oaa, 'oaa'] = hitters_df.loc[missing_oaa, 'drs'] * 0.6

            # 4. Estimate fielding_pct from FanGraphs if not already set
            # Most players have fielding% in FanGraphs data (already fetched above)
            # If still missing, use position-based defaults
            missing_fpct = hitters_df['fielding_pct'].isna()
            if missing_fpct.sum() > 0:
                # Use conservative defaults by position
                position_defaults = {
                    'C': 0.990, '1B': 0.993, '2B': 0.983, 'SS': 0.972,
                    '3B': 0.958, 'LF': 0.982, 'CF': 0.988, 'RF': 0.985
                }
                for idx in hitters_df[missing_fpct].index:
                    pos = hitters_df.at[idx, 'primary_position']
                    if pos and pos in position_defaults:
                        hitters_df.at[idx, 'fielding_pct'] = position_defaults[pos]

        except Exception as e:
            print(f"  Error fetching defensive metrics: {e}")

        return hitters_df

    def _fetch_arm_strength_leaderboard(self) -> Optional[pd.DataFrame]:
        """
        Fetch arm strength leaderboard directly from Baseball Savant.
        
        This data is not available via pybaseball functions, so we scrape
        the Baseball Savant CSV export directly.
        
        Returns
        -------
        pd.DataFrame or None
            DataFrame with arm strength data:
            - fielder_name: Player name (format: "Last, First")
            - player_id: MLBAM player ID
            - primary_position: Position number
            - arm_overall: Overall arm strength in MPH
            - max_arm_strength: Maximum arm strength in MPH
            - arm_rf, arm_cf, arm_lf, etc.: Position-specific arm strength
        """
        try:
            url = f'https://baseballsavant.mlb.com/leaderboard/arm-strength?year={self.season}&pos=&team=&min=5&csv=true'
            response = requests.get(url, timeout=15)
            
            if response.status_code == 200:
                df = pd.read_csv(StringIO(response.text))
                return df
            else:
                print(f"    Baseball Savant returned status {response.status_code}")
                return None
                
        except Exception as e:
            print(f"    Error fetching arm strength: {e}")
            return None

    def _fetch_jump_leaderboard(self) -> Optional[pd.DataFrame]:
        """
        Fetch outfielder jump leaderboard directly from Baseball Savant.
        
        Jump is the Statcast metric that measures "feet covered in the right direction
        in the first three seconds after pitch release." It has three components:
        - Reaction: Feet covered in first 1.5 seconds (first step quality)
        - Burst: Feet covered in second 1.5 seconds (acceleration phase)
        - Route: Feet lost/gained from direction (route efficiency over 3s)
        
        Total Jump (Feet vs Avg) = Reaction + Burst + Route
        
        Returns
        -------
        pd.DataFrame or None
            DataFrame with jump data:
            - player_name: Player name (format: "Last, First")
            - player_id: MLBAM player ID
            - outs: Number of outs made
            - opp: Number of opportunities
            - oaa: Outs Above Average
            - reaction_ft: Reaction component in feet vs average
            - burst_ft: Burst component in feet vs average
            - route_ft: Route component in feet vs average
            - jump_ft: Total jump (feet vs average)
            - feet_covered: Total feet covered in 3 seconds
        """
        try:
            url = f'https://baseballsavant.mlb.com/leaderboard/outfield_jump?year={self.season}&min=25&csv=true'
            response = requests.get(url, timeout=15)
            
            if response.status_code == 200 and len(response.text) > 100:
                df = pd.read_csv(StringIO(response.text))
                
                # Standardize column names based on Baseball Savant format
                # The leaderboard has: Outs, Opp, %, OAA, Reaction, Burst, Route, Feet vs Avg, Feet Covered
                rename_map = {}
                for col in df.columns:
                    col_lower = col.lower().strip()
                    if 'reaction' in col_lower:
                        rename_map[col] = 'reaction_ft'
                    elif 'burst' in col_lower:
                        rename_map[col] = 'burst_ft'
                    elif 'route' in col_lower:
                        rename_map[col] = 'route_ft'
                    elif 'feet vs' in col_lower or 'feet_vs' in col_lower:
                        rename_map[col] = 'jump_ft'
                    elif 'feet covered' in col_lower or 'feet_covered' in col_lower:
                        rename_map[col] = 'feet_covered'
                    elif col_lower == 'oaa':
                        rename_map[col] = 'oaa'
                    elif 'name' in col_lower or 'player' in col_lower:
                        rename_map[col] = 'player_name'
                
                if rename_map:
                    df = df.rename(columns=rename_map)
                
                return df
            else:
                print(f"    Baseball Savant jump leaderboard returned status {response.status_code}")
                return None
                
        except Exception as e:
            print(f"    Error fetching jump leaderboard: {e}")
            return None

    def _match_player_in_bat_tracking(self, player_name: str, bat_data: pd.DataFrame) -> Optional[pd.Series]:
        """
        Match a player name to bat tracking data.
        
        Parameters
        ----------
        player_name : str
            Player name in "First Last" format
        bat_data : pd.DataFrame
            Bat tracking data with 'name' column in "Last, First" format
            
        Returns
        -------
        pd.Series or None
            Matched row from bat_data, or None if no match
        """
        if ' ' in player_name:
            parts = player_name.split()
            # Try "Last, First" format
            last_first = f"{parts[-1]}, {parts[0]}"
            match = bat_data[
                bat_data['name'].str.contains(last_first, case=False, na=False)
            ]
            
            if len(match) == 0:
                # Try just last name (for unique last names)
                last_matches = bat_data[
                    bat_data['name'].str.contains(parts[-1], case=False, na=False)
                ]
                # Only use if it's a unique match
                if len(last_matches) == 1:
                    match = last_matches
        else:
            match = bat_data[
                bat_data['name'].str.contains(player_name, case=False, na=False)
            ]
        
        if len(match) > 0:
            return match.iloc[0]
        return None

    def _fetch_bat_tracking_leaderboard(self, min_swings: int = 100, season_override: int = None) -> Optional[pd.DataFrame]:
        """
        Fetch bat tracking leaderboard directly from Baseball Savant.
        
        This data includes bat speed, swing length, and contact quality metrics
        from Statcast's bat tracking system (available from 2024+).
        
        Parameters
        ----------
        min_swings : int
            Minimum competitive swings to qualify (default 100)
        season_override : int, optional
            Override season to fetch (used for fallback to 2024 data)
        
        Returns
        -------
        pd.DataFrame or None
            DataFrame with bat tracking data:
            - id: MLBAM player ID
            - name: Player name (format: "Last, First")
            - avg_bat_speed: Average bat speed in mph
            - swing_length: Swing length in feet
            - squared_up_per_swing: % of swings that square up the ball
            - hard_swing_rate: % of swings that are hard swings
            - blast_per_swing: % of swings with "blast" contact (elite contact)
        """
        try:
            season = season_override if season_override is not None else self.season
            url = f'https://baseballsavant.mlb.com/leaderboard/bat-tracking?year={season}&min={min_swings}&csv=true'
            response = requests.get(url, timeout=15)
            
            if response.status_code == 200 and len(response.text) > 100:
                df = pd.read_csv(StringIO(response.text))
                return df
            else:
                print(f"    Baseball Savant bat tracking returned status {response.status_code}")
                return None
                
        except Exception as e:
            print(f"    Error fetching bat tracking: {e}")
            return None

    def get_pitcher_statcast_metrics(
        self,
        player_name: str,
        min_pitches: int = 100
    ) -> Optional[Dict[str, Dict[str, float]]]:
        """
        Get pitch-level Statcast metrics for a pitcher (whiff%, spin rate, etc.).

        Parameters
        ----------
        player_name : str
            Player name (e.g., "Gerrit Cole")
        min_pitches : int
            Minimum pitches thrown per pitch type to include

        Returns
        -------
        dict or None
            Dictionary mapping pitch type to metrics:
            {
                'fastball': {'whiff_pct': 0.24, 'chase_pct': 0.28, 'spin_rate': 2400, ...},
                'slider': {'whiff_pct': 0.38, 'chase_pct': 0.42, 'spin_rate': 2650, ...},
                ...
            }
        """
        try:
            print(f"Fetching Statcast pitch-level data for {player_name}...")

            # Fetch pitch-level data from Statcast
            # Note: This requires player ID - we'd need to look it up first
            # For now, we'll use the aggregate stats approach with FanGraphs data
            # which includes SwStr% (swinging strike rate) as a proxy for whiff rate

            # Get pitching stats which includes some plate discipline metrics
            stats = pitching_stats(self.season, qual=0)

            # Find the player
            player_stats = stats[stats['Name'].str.contains(player_name, case=False, na=False)]

            if len(player_stats) == 0:
                print(f"  Player {player_name} not found")
                return None

            player_stats = player_stats.iloc[0]

            # FanGraphs provides pitch-type specific data in separate columns
            pitch_metrics = {}

            # Map FanGraphs pitch type suffixes to our pitch types
            pitch_type_mapping = {
                'FA': 'fastball',      # 4-seam fastball
                'FT': '2-seam',        # 2-seam/sinker
                'FC': 'cutter',        # Cutter
                'SI': '2-seam',        # Sinker (treat as 2-seam)
                'SL': 'slider',        # Slider
                'CU': 'curveball',     # Curveball
                'CH': 'changeup',      # Changeup
                'FS': 'splitter',      # Splitter
                'KC': 'curveball',     # Knuckle-curve (treat as curveball)
            }

            # Extract metrics for each pitch type
            for fg_type, our_type in pitch_type_mapping.items():
                # Check if this pitcher throws this pitch type (usage %)
                usage_col = f'{fg_type}%'
                if usage_col in player_stats.index and player_stats[usage_col] > 5.0:  # At least 5% usage
                    metrics = {}

                    # Velocity (vFA, vFT, vSL, etc.)
                    velo_col = f'v{fg_type} (pi)'
                    if velo_col in player_stats.index and not pd.isna(player_stats[velo_col]):
                        metrics['velocity'] = float(player_stats[velo_col])

                    # Whiff rate (SwStr%) - FanGraphs provides this
                    # Note: SwStr% is swinging strike rate, which is close to whiff rate
                    if 'SwStr%' in player_stats.index and not pd.isna(player_stats['SwStr%']):
                        # Use aggregate SwStr% as baseline, then adjust by pitch type
                        base_whiff = float(player_stats['SwStr%']) / 100.0

                        # Adjust based on typical pitch type effectiveness
                        # Source: MLB Statcast average whiff rates by pitch type
                        pitch_type_multipliers = {
                            'fastball': 0.75,   # Fastballs typically 25% below average
                            '2-seam': 0.70,     # Sinkers even lower
                            'cutter': 0.95,     # Cutters near average
                            'slider': 1.30,     # Sliders 30% above average
                            'curveball': 1.15,  # Curves above average
                            'changeup': 1.20,   # Changeups above average
                            'splitter': 1.40,   # Splitters highest
                        }

                        multiplier = pitch_type_multipliers.get(our_type, 1.0)
                        metrics['whiff_pct'] = base_whiff * multiplier

                    # Spin rate (not always available in FanGraphs)
                    spin_col = f'Spin (pi)'
                    if spin_col in player_stats.index and not pd.isna(player_stats[spin_col]):
                        metrics['spin_rate'] = float(player_stats[spin_col])

                    # Usage percentage
                    if usage_col in player_stats.index:
                        metrics['usage_pct'] = float(player_stats[usage_col]) / 100.0

                    if metrics:  # Only add if we got some data
                        if our_type not in pitch_metrics:
                            pitch_metrics[our_type] = {}
                        # Merge/average if we have multiple pitch types mapping to same category
                        for key, value in metrics.items():
                            if key in pitch_metrics[our_type]:
                                # Average if we already have a value
                                pitch_metrics[our_type][key] = (pitch_metrics[our_type][key] + value) / 2
                            else:
                                pitch_metrics[our_type][key] = value

            print(f"  Found metrics for {len(pitch_metrics)} pitch types")
            return pitch_metrics if pitch_metrics else None

        except Exception as e:
            print(f"  Error fetching Statcast metrics: {e}")
            return None

    def get_batter_statcast_metrics(
        self,
        player_name: str,
        min_pitches: int = 100
    ) -> Optional[Dict[str, Dict[str, float]]]:
        """
        Get pitch-level Statcast metrics for a batter (chase%, contact%, etc.).

        Parameters
        ----------
        player_name : str
            Player name (e.g., "Aaron Judge")
        min_pitches : int
            Minimum pitches seen per pitch type to include

        Returns
        -------
        dict or None
            Dictionary mapping pitch type to metrics:
            {
                'fastball': {'chase_pct': 0.22, 'contact_pct': 0.78, 'whiff_pct': 0.18, ...},
                'slider': {'chase_pct': 0.35, 'contact_pct': 0.65, 'whiff_pct': 0.28, ...},
                ...
            }
        """
        try:
            print(f"Fetching Statcast pitch-level data for {player_name}...")

            # Get batting stats
            stats = batting_stats(self.season, qual=0)

            # Find the player
            player_stats = stats[stats['Name'].str.contains(player_name, case=False, na=False)]

            if len(player_stats) == 0:
                print(f"  Player {player_name} not found")
                return None

            player_stats = player_stats.iloc[0]

            # Extract plate discipline metrics
            pitch_metrics = {}

            # Aggregate metrics we can use to estimate pitch-type performance
            aggregate_metrics = {}

            # O-Swing% (chase rate on pitches outside zone)
            if 'O-Swing%' in player_stats.index and not pd.isna(player_stats['O-Swing%']):
                aggregate_metrics['chase_pct'] = float(player_stats['O-Swing%']) / 100.0

            # Z-Contact% (contact rate on pitches in zone)
            if 'Z-Contact%' in player_stats.index and not pd.isna(player_stats['Z-Contact%']):
                aggregate_metrics['zone_contact_pct'] = float(player_stats['Z-Contact%']) / 100.0

            # O-Contact% (contact rate on pitches outside zone)
            if 'O-Contact%' in player_stats.index and not pd.isna(player_stats['O-Contact%']):
                aggregate_metrics['chase_contact_pct'] = float(player_stats['O-Contact%']) / 100.0

            # Contact% (overall contact rate)
            if 'Contact%' in player_stats.index and not pd.isna(player_stats['Contact%']):
                aggregate_metrics['contact_pct'] = float(player_stats['Contact%']) / 100.0

            # SwStr% (swinging strike rate = whiff rate)
            if 'SwStr%' in player_stats.index and not pd.isna(player_stats['SwStr%']):
                aggregate_metrics['whiff_pct'] = float(player_stats['SwStr%']) / 100.0

            # Create pitch-type specific metrics by adjusting aggregate metrics
            # based on typical hitter performance vs different pitch types
            pitch_types = ['fastball', '2-seam', 'cutter', 'slider', 'curveball', 'changeup', 'splitter']

            for pitch_type in pitch_types:
                metrics = {}

                # Chase rate adjustments (harder to identify = higher chase rate)
                if 'chase_pct' in aggregate_metrics:
                    base_chase = aggregate_metrics['chase_pct']
                    chase_multipliers = {
                        'fastball': 0.70,   # Easier to identify
                        '2-seam': 0.75,
                        'cutter': 0.85,
                        'slider': 1.40,     # Hardest to identify (highest chase)
                        'curveball': 1.25,
                        'changeup': 1.30,
                        'splitter': 1.35,
                    }
                    metrics['chase_pct'] = base_chase * chase_multipliers.get(pitch_type, 1.0)

                # Contact rate adjustments (harder movement = lower contact)
                if 'contact_pct' in aggregate_metrics:
                    base_contact = aggregate_metrics['contact_pct']
                    contact_multipliers = {
                        'fastball': 1.15,   # Easier to make contact
                        '2-seam': 1.10,
                        'cutter': 1.05,
                        'slider': 0.75,     # Hardest to make contact
                        'curveball': 0.85,
                        'changeup': 0.80,
                        'splitter': 0.70,
                    }
                    metrics['contact_pct'] = base_contact * contact_multipliers.get(pitch_type, 1.0)

                # Whiff rate adjustments (inverse of contact for swings)
                if 'whiff_pct' in aggregate_metrics:
                    base_whiff = aggregate_metrics['whiff_pct']
                    whiff_multipliers = {
                        'fastball': 0.70,
                        '2-seam': 0.75,
                        'cutter': 0.90,
                        'slider': 1.50,     # Highest whiff rate
                        'curveball': 1.25,
                        'changeup': 1.35,
                        'splitter': 1.55,
                    }
                    metrics['whiff_pct'] = base_whiff * whiff_multipliers.get(pitch_type, 1.0)

                if metrics:
                    pitch_metrics[pitch_type] = metrics

            print(f"  Estimated metrics for {len(pitch_metrics)} pitch types")
            return pitch_metrics if pitch_metrics else None

        except Exception as e:
            print(f"  Error fetching batter Statcast metrics: {e}")
            return None

    @staticmethod
    def get_available_teams() -> List[str]:
        """
        Get list of MLB team abbreviations.

        Returns
        -------
        list of str
            Team abbreviations (e.g., ['NYY', 'LAD', 'BOS', ...])
        """
        # Use centralized team mappings
        from .team_mappings import get_all_team_abbrs
        return get_all_team_abbrs()

    @staticmethod
    def get_team_name(team_abbr: str) -> str:
        """
        Get full team name from abbreviation.

        Parameters
        ----------
        team_abbr : str
            Team abbreviation (e.g., 'NYY')

        Returns
        -------
        str
            Full team name (e.g., 'New York Yankees')
        """
        # Use centralized team mappings
        from .team_mappings import get_team_name as _get_team_name
        return _get_team_name(team_abbr)


if __name__ == "__main__":
    # Test the fetcher
    print("=== PyBaseball Fetcher Test ===\n")

    # Test with Yankees 2024
    fetcher = PybaseballFetcher(season=2024)

    print("Available teams:")
    teams = fetcher.get_available_teams()
    print(f"  {', '.join(teams[:10])}...")

    print("\n" + "="*60)
    print("Fetching NYY (New York Yankees) roster for 2024...")
    print("="*60)

    pitchers, hitters = fetcher.get_team_roster(
        'NYY',
        min_pitcher_innings=10.0,  # Lower threshold for testing
        min_hitter_at_bats=30      # Lower threshold for testing
    )

    print("\n--- Pitchers ---")
    if len(pitchers) > 0:
        print(pitchers[['player_name', 'innings_pitched', 'era', 'whip', 'k_per_9']].head(10))
    else:
        print("No pitcher data available")

    print("\n--- Hitters ---")
    if len(hitters) > 0:
        print(hitters[['player_name', 'at_bats', 'batting_avg', 'ops', 'home_runs']].head(10))
    else:
        print("No hitter data available")
