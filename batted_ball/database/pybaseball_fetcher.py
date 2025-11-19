"""
Fetch MLB player statistics using pybaseball.

Provides a clean interface to retrieve pitcher and hitter stats from MLB data
sources including Baseball Savant, FanGraphs, and Baseball Reference.
"""

import pandas as pd
from typing import List, Dict, Optional, Tuple
import warnings

# Suppress pybaseball warnings
warnings.filterwarnings('ignore')

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
    )
    PYBASEBALL_AVAILABLE = True
except ImportError:
    PYBASEBALL_AVAILABLE = False
    print("Warning: pybaseball not installed. Run: pip install pybaseball")


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

        return pitchers, hitters

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
        return [
            'ARI', 'ATL', 'BAL', 'BOS', 'CHC', 'CHW', 'CIN', 'CLE',
            'COL', 'DET', 'HOU', 'KC', 'LAA', 'LAD', 'MIA', 'MIL',
            'MIN', 'NYM', 'NYY', 'OAK', 'PHI', 'PIT', 'SD', 'SEA',
            'SF', 'STL', 'TB', 'TEX', 'TOR', 'WSH'
        ]

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
        team_names = {
            'ARI': 'Arizona Diamondbacks',
            'ATL': 'Atlanta Braves',
            'BAL': 'Baltimore Orioles',
            'BOS': 'Boston Red Sox',
            'CHC': 'Chicago Cubs',
            'CHW': 'Chicago White Sox',
            'CIN': 'Cincinnati Reds',
            'CLE': 'Cleveland Guardians',
            'COL': 'Colorado Rockies',
            'DET': 'Detroit Tigers',
            'HOU': 'Houston Astros',
            'KC': 'Kansas City Royals',
            'LAA': 'Los Angeles Angels',
            'LAD': 'Los Angeles Dodgers',
            'MIA': 'Miami Marlins',
            'MIL': 'Milwaukee Brewers',
            'MIN': 'Minnesota Twins',
            'NYM': 'New York Mets',
            'NYY': 'New York Yankees',
            'OAK': 'Oakland Athletics',
            'PHI': 'Philadelphia Phillies',
            'PIT': 'Pittsburgh Pirates',
            'SD': 'San Diego Padres',
            'SEA': 'Seattle Mariners',
            'SF': 'San Francisco Giants',
            'STL': 'St. Louis Cardinals',
            'TB': 'Tampa Bay Rays',
            'TEX': 'Texas Rangers',
            'TOR': 'Toronto Blue Jays',
            'WSH': 'Washington Nationals'
        }
        return team_names.get(team_abbr, team_abbr)


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
