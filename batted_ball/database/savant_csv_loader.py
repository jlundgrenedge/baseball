"""
Load Baseball Savant CSV exports directly instead of scraping.

This module loads pre-downloaded CSV files from Baseball Savant containing:
- jump.csv: Outfielder Jump metrics (Reaction, Burst, Route, Bootup)
- outs_above_average.csv: OAA by position and direction
- directional_outs_above_average.csv: OAA broken into 6 directional segments
- catch_probability.csv: Catch probability by difficulty (5-star to 1-star)
- positioning.csv: Average starting depth and angle by fielder/position
- fielding-run-value.csv: Comprehensive fielding runs (range, arm, DP, framing, etc.)

Usage:
    loader = SavantCSVLoader(data_dir="data/bballsavant/2025")
    jump_data = loader.get_jump_data("Pete Crow-Armstrong")
    positioning = loader.get_positioning("Pete Crow-Armstrong", "CF")
"""

import os
import pandas as pd
from typing import Dict, Optional, List, Any
from pathlib import Path


class SavantCSVLoader:
    """Load and query Baseball Savant CSV exports."""
    
    def __init__(self, data_dir: str = None, season: int = 2025):
        """
        Initialize the loader with a data directory.
        
        Parameters
        ----------
        data_dir : str, optional
            Path to directory containing CSV files. 
            Defaults to data/bballsavant/{season}/ relative to project root.
        season : int
            Season year for data (default 2025)
        """
        self.season = season
        
        if data_dir is None:
            # Find project root (look for batted_ball directory)
            current = Path(__file__).parent
            while current.parent != current:
                if (current / "batted_ball").exists():
                    data_dir = current / "data" / "bballsavant" / str(season)
                    break
                current = current.parent
            else:
                data_dir = Path(f"data/bballsavant/{season}")
        
        self.data_dir = Path(data_dir)
        
        # Lazy-loaded DataFrames
        self._jump_df: Optional[pd.DataFrame] = None
        self._oaa_df: Optional[pd.DataFrame] = None
        self._directional_oaa_df: Optional[pd.DataFrame] = None
        self._catch_prob_df: Optional[pd.DataFrame] = None
        self._positioning_df: Optional[pd.DataFrame] = None
        self._fielding_runs_df: Optional[pd.DataFrame] = None
        
        # Name lookup cache (player_id -> normalized name)
        self._name_cache: Dict[int, str] = {}
    
    def _normalize_name(self, name: str) -> str:
        """
        Normalize player name for matching.
        
        Handles formats like:
        - "Crow-Armstrong, Pete" -> "pete crow-armstrong"
        - "Pete Crow-Armstrong" -> "pete crow-armstrong"
        """
        if not name:
            return ""
        name = name.strip().lower()
        # If comma-separated (Last, First), reverse it
        if ", " in name:
            parts = name.split(", ", 1)
            name = f"{parts[1]} {parts[0]}"
        return name
    
    def _match_player(self, df: pd.DataFrame, player_name: str, 
                      name_col: str = "last_name, first_name") -> Optional[pd.Series]:
        """
        Find a player in a DataFrame by name.
        
        Parameters
        ----------
        df : pd.DataFrame
            DataFrame to search
        player_name : str
            Player name to find (any format)
        name_col : str
            Column name containing player names
            
        Returns
        -------
        pd.Series or None
            Matching row, or None if not found
        """
        if df is None or len(df) == 0:
            return None
            
        target = self._normalize_name(player_name)
        
        for idx, row in df.iterrows():
            if name_col in row.index:
                row_name = self._normalize_name(str(row[name_col]))
                if row_name == target:
                    return row
                # Also try partial match on last name
                target_parts = target.split()
                row_parts = row_name.split()
                if target_parts and row_parts:
                    # Match if last names match and first initial matches
                    if (target_parts[-1] == row_parts[-1] and 
                        target_parts[0][0] == row_parts[0][0]):
                        return row
        
        return None
    
    # =========================================================================
    # JUMP DATA
    # =========================================================================
    
    @property
    def jump_df(self) -> Optional[pd.DataFrame]:
        """Load jump.csv lazily."""
        if self._jump_df is None:
            path = self.data_dir / "jump.csv"
            if path.exists():
                self._jump_df = pd.read_csv(path)
        return self._jump_df
    
    def get_jump_data(self, player_name: str) -> Optional[Dict[str, float]]:
        """
        Get Jump metrics for a player.
        
        Parameters
        ----------
        player_name : str
            Player name (any format)
            
        Returns
        -------
        dict or None
            Jump data with keys:
            - oaa: Outs Above Average
            - reaction_ft: Feet covered in first 1.5s vs avg (reaction)
            - burst_ft: Feet covered in second 1.5s vs avg (burst/acceleration)
            - route_ft: Feet lost/gained from route direction
            - bootup_ft: Total jump = reaction + burst + route
            - bootup_distance: Actual feet covered in 3s (not vs avg)
            - n_opportunities: Number of plays
        """
        if self.jump_df is None:
            return None
            
        row = self._match_player(self.jump_df, player_name)
        if row is None:
            return None
            
        return {
            'oaa': row.get('outs_above_average'),
            'reaction_ft': row.get('rel_league_reaction_distance'),
            'burst_ft': row.get('rel_league_burst_distance'),
            'route_ft': row.get('rel_league_routing_distance'),
            'bootup_ft': row.get('rel_league_bootup_distance'),  # Total = reaction + burst + route
            'bootup_distance': row.get('f_bootup_distance'),  # Actual feet in 3s
            'n_opportunities': row.get('n'),
            'n_outs': row.get('n_outs'),
        }
    
    # =========================================================================
    # OUTS ABOVE AVERAGE
    # =========================================================================
    
    @property
    def oaa_df(self) -> Optional[pd.DataFrame]:
        """Load outs_above_average.csv lazily."""
        if self._oaa_df is None:
            path = self.data_dir / "outs_above_average.csv"
            if path.exists():
                self._oaa_df = pd.read_csv(path)
        return self._oaa_df
    
    def get_oaa_data(self, player_name: str) -> Optional[Dict[str, Any]]:
        """
        Get OAA metrics for a player.
        
        Returns
        -------
        dict or None
            OAA data with keys:
            - oaa: Total Outs Above Average
            - oaa_infront: OAA on balls hit in front
            - oaa_toward_3b: OAA on balls toward 3B line
            - oaa_toward_1b: OAA on balls toward 1B line
            - oaa_behind: OAA on balls hit behind
            - oaa_vs_rhh: OAA against right-handed hitters
            - oaa_vs_lhh: OAA against left-handed hitters
            - fielding_runs_prevented: Total runs saved
            - success_rate: Actual success rate %
            - expected_success_rate: Expected success rate %
            - position: Primary position
            - team: Team name
        """
        if self.oaa_df is None:
            return None
            
        row = self._match_player(self.oaa_df, player_name)
        if row is None:
            return None
        
        return {
            'oaa': row.get('outs_above_average'),
            'oaa_infront': row.get('outs_above_average_infront'),
            'oaa_toward_3b': row.get('outs_above_average_lateral_toward3bline'),
            'oaa_toward_1b': row.get('outs_above_average_lateral_toward1bline'),
            'oaa_behind': row.get('outs_above_average_behind'),
            'oaa_vs_rhh': row.get('outs_above_average_rhh'),
            'oaa_vs_lhh': row.get('outs_above_average_lhh'),
            'fielding_runs_prevented': row.get('fielding_runs_prevented'),
            'success_rate': row.get('actual_success_rate_formatted'),
            'expected_success_rate': row.get('adj_estimated_success_rate_formatted'),
            'position': row.get('primary_pos_formatted'),
            'team': row.get('display_team_name'),
        }
    
    # =========================================================================
    # DIRECTIONAL OAA (6 segments)
    # =========================================================================
    
    @property
    def directional_oaa_df(self) -> Optional[pd.DataFrame]:
        """Load directional_outs_above_average.csv lazily."""
        if self._directional_oaa_df is None:
            path = self.data_dir / "directional_outs_above_average.csv"
            if path.exists():
                self._directional_oaa_df = pd.read_csv(path)
        return self._directional_oaa_df
    
    def get_directional_oaa(self, player_name: str) -> Optional[Dict[str, Any]]:
        """
        Get directional OAA broken into 6 segments.
        
        The 6 segments are:
        - back_left: Going back and to the left
        - back: Going straight back
        - back_right: Going back and to the right
        - in_left: Coming in and to the left
        - in: Coming straight in
        - in_right: Coming in and to the right
        
        Returns
        -------
        dict or None
            Directional OAA data with keys for each segment
        """
        if self.directional_oaa_df is None:
            return None
            
        row = self._match_player(self.directional_oaa_df, player_name)
        if row is None:
            return None
        
        return {
            'oaa': row.get('n_outs_above_average'),
            'attempts': row.get('attempts'),
            # Back segments (going away from plate)
            'oaa_back_left': row.get('n_oaa_slice_back_left'),
            'oaa_back': row.get('n_oaa_slice_back'),
            'oaa_back_right': row.get('n_oaa_slice_back_right'),
            'oaa_back_all': row.get('n_oaa_slice_back_all'),
            # In segments (coming toward plate)
            'oaa_in_left': row.get('n_oaa_slice_in_left'),
            'oaa_in': row.get('n_oaa_slice_in'),
            'oaa_in_right': row.get('n_oaa_slice_in_right'),
            'oaa_in_all': row.get('n_oaa_slice_in_all'),
        }
    
    # =========================================================================
    # CATCH PROBABILITY (5-star system)
    # =========================================================================
    
    @property
    def catch_prob_df(self) -> Optional[pd.DataFrame]:
        """Load catch_probability.csv lazily."""
        if self._catch_prob_df is None:
            path = self.data_dir / "catch_probability.csv"
            if path.exists():
                self._catch_prob_df = pd.read_csv(path)
        return self._catch_prob_df
    
    def get_catch_probability(self, player_name: str) -> Optional[Dict[str, Any]]:
        """
        Get catch probability performance by difficulty level.
        
        Levels (based on catch probability):
        - 5-star: 0-25% catch probability (hardest)
        - 4-star: 25-50% catch probability
        - 3-star: 50-75% catch probability
        - 2-star: 75-90% catch probability
        - 1-star: 90-95% catch probability (easiest "non-routine")
        
        Returns
        -------
        dict or None
            Catch probability data with made/opportunities/pct for each level
        """
        if self.catch_prob_df is None:
            return None
            
        row = self._match_player(self.catch_prob_df, player_name)
        if row is None:
            return None
        
        return {
            'oaa': row.get('oaa'),
            # 5-star (hardest)
            '5star_made': row.get('n_fieldout_5stars'),
            '5star_opp': row.get('n_opp_5stars'),
            '5star_pct': row.get('n_5star_percent'),
            # 4-star
            '4star_made': row.get('n_fieldout_4stars'),
            '4star_opp': row.get('n_opp_4stars'),
            '4star_pct': row.get('n_4star_percent'),
            # 3-star
            '3star_made': row.get('n_fieldout_3stars'),
            '3star_opp': row.get('n_opp_3stars'),
            '3star_pct': row.get('n_3star_percent'),
            # 2-star
            '2star_made': row.get('n_fieldout_2stars'),
            '2star_opp': row.get('n_opp_2stars'),
            '2star_pct': row.get('n_2star_percent'),
            # 1-star (easiest)
            '1star_made': row.get('n_fieldout_1stars'),
            '1star_opp': row.get('n_opp_1stars'),
            '1star_pct': row.get('n_1star_percent'),
        }
    
    # =========================================================================
    # POSITIONING (depth and angle)
    # =========================================================================
    
    @property
    def positioning_df(self) -> Optional[pd.DataFrame]:
        """Load positioning.csv lazily."""
        if self._positioning_df is None:
            path = self.data_dir / "positioning.csv"
            if path.exists():
                self._positioning_df = pd.read_csv(path)
        return self._positioning_df
    
    def get_positioning(self, player_name: str, position: str = None) -> Optional[Dict[str, Any]]:
        """
        Get average starting position for a fielder.
        
        Parameters
        ----------
        player_name : str
            Player name
        position : str, optional
            Filter to specific position (CF, LF, RF, SS, etc.)
            
        Returns
        -------
        dict or None
            Positioning data:
            - depth_ft: Distance from home plate in feet
            - angle_deg: Angle from center (0°=center, -45°=3B line, +45°=1B line)
            - pa: Plate appearances at this position
        """
        if self.positioning_df is None:
            return None
        
        # Find all entries for this player
        target = self._normalize_name(player_name)
        matches = []
        
        name_col = 'name_fielder'
        for idx, row in self.positioning_df.iterrows():
            if name_col in row.index:
                row_name = self._normalize_name(str(row[name_col]))
                if row_name == target:
                    if position is None or row.get('position') == position:
                        matches.append(row)
        
        if not matches:
            return None
        
        # If position specified, return that one; otherwise return the one with most PA
        if len(matches) == 1:
            row = matches[0]
        else:
            row = max(matches, key=lambda r: r.get('pa', 0))
        
        return {
            'position': row.get('position'),
            'depth_ft': row.get('avg_norm_start_distance'),
            'angle_deg': row.get('avg_norm_start_angle'),
            'pa': row.get('pa'),
            'team': row.get('fld_name_display_club'),
        }
    
    def get_all_positioning(self, player_name: str) -> List[Dict[str, Any]]:
        """Get positioning data for all positions a player has played."""
        if self.positioning_df is None:
            return []
        
        target = self._normalize_name(player_name)
        results = []
        
        name_col = 'name_fielder'
        for idx, row in self.positioning_df.iterrows():
            if name_col in row.index:
                row_name = self._normalize_name(str(row[name_col]))
                if row_name == target:
                    results.append({
                        'position': row.get('position'),
                        'depth_ft': row.get('avg_norm_start_distance'),
                        'angle_deg': row.get('avg_norm_start_angle'),
                        'pa': row.get('pa'),
                        'team': row.get('fld_name_display_club'),
                    })
        
        return results
    
    # =========================================================================
    # FIELDING RUN VALUE
    # =========================================================================
    
    @property
    def fielding_runs_df(self) -> Optional[pd.DataFrame]:
        """Load fielding-run-value.csv lazily."""
        if self._fielding_runs_df is None:
            path = self.data_dir / "fielding-run-value.csv"
            if path.exists():
                self._fielding_runs_df = pd.read_csv(path)
        return self._fielding_runs_df
    
    def get_fielding_runs(self, player_name: str) -> Optional[Dict[str, Any]]:
        """
        Get comprehensive fielding run values.
        
        Returns
        -------
        dict or None
            Fielding run data:
            - total_runs: Total fielding runs above average
            - range_runs: Runs from range/positioning
            - arm_runs: Runs from arm (outfielders)
            - dp_runs: Runs from double plays (infielders)
            - framing_runs: Runs from pitch framing (catchers)
            - throwing_runs: Runs from throwing out runners (catchers)
            - blocking_runs: Runs from blocking pitches (catchers)
        """
        if self.fielding_runs_df is None:
            return None
        
        row = self._match_player(self.fielding_runs_df, player_name, name_col='name')
        if row is None:
            return None
        
        return {
            'total_runs': row.get('total_runs'),
            'inf_of_runs': row.get('inf_of_runs'),
            'range_runs': row.get('range_runs'),
            'arm_runs': row.get('arm_runs'),
            'dp_runs': row.get('dp_runs'),
            'catching_runs': row.get('catching_runs'),
            'framing_runs': row.get('framing_runs'),
            'throwing_runs': row.get('throwing_runs'),
            'blocking_runs': row.get('blocking_runs'),
        }
    
    # =========================================================================
    # BULK OPERATIONS
    # =========================================================================
    
    def get_all_jump_data(self) -> pd.DataFrame:
        """Get the full jump DataFrame for bulk operations."""
        return self.jump_df
    
    def get_all_oaa_data(self) -> pd.DataFrame:
        """Get the full OAA DataFrame for bulk operations."""
        return self.oaa_df
    
    def get_all_positioning_data(self) -> pd.DataFrame:
        """Get the full positioning DataFrame for bulk operations."""
        return self.positioning_df
    
    def get_complete_fielding_profile(self, player_name: str) -> Dict[str, Any]:
        """
        Get all available fielding data for a player in one call.
        
        Returns
        -------
        dict
            Complete fielding profile with all available data
        """
        return {
            'jump': self.get_jump_data(player_name),
            'oaa': self.get_oaa_data(player_name),
            'directional_oaa': self.get_directional_oaa(player_name),
            'catch_probability': self.get_catch_probability(player_name),
            'positioning': self.get_all_positioning(player_name),
            'fielding_runs': self.get_fielding_runs(player_name),
        }


# Convenience function for quick access
def load_savant_data(season: int = 2025) -> SavantCSVLoader:
    """Create a SavantCSVLoader for the given season."""
    return SavantCSVLoader(season=season)


if __name__ == "__main__":
    # Demo usage
    loader = SavantCSVLoader()
    
    print("=" * 60)
    print("BASEBALL SAVANT CSV LOADER DEMO")
    print("=" * 60)
    
    # Test with Pete Crow-Armstrong (elite CF)
    player = "Pete Crow-Armstrong"
    print(f"\n{player}:")
    
    jump = loader.get_jump_data(player)
    if jump:
        print(f"  Jump: OAA={jump['oaa']}, Reaction={jump['reaction_ft']:.1f}ft, "
              f"Burst={jump['burst_ft']:.1f}ft, Route={jump['route_ft']:.1f}ft")
    
    oaa = loader.get_oaa_data(player)
    if oaa:
        print(f"  OAA: {oaa['oaa']} (Position: {oaa['position']}, Team: {oaa['team']})")
    
    pos = loader.get_positioning(player, "CF")
    if pos:
        print(f"  Positioning (CF): Depth={pos['depth_ft']}ft, Angle={pos['angle_deg']}°")
    
    catch = loader.get_catch_probability(player)
    if catch:
        print(f"  5-star catches: {catch['5star_made']}/{catch['5star_opp']} "
              f"({catch['5star_pct']}%)")
    
    # Test with a poor defender
    player = "Nick Castellanos"
    print(f"\n{player}:")
    
    jump = loader.get_jump_data(player)
    if jump:
        print(f"  Jump: OAA={jump['oaa']}, Reaction={jump['reaction_ft']:.1f}ft, "
              f"Burst={jump['burst_ft']:.1f}ft, Route={jump['route_ft']:.1f}ft")
    
    catch = loader.get_catch_probability(player)
    if catch:
        print(f"  5-star catches: {catch['5star_made']}/{catch['5star_opp']} "
              f"({catch['5star_pct']}%)")
