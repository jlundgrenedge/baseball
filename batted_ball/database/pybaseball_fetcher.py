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
