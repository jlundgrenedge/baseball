"""
Advanced baseball statistics calculations.

Implements sabermetric stats including:
- wOBA (weighted On-Base Average)
- wRC+ (weighted Runs Created Plus)
- FIP (Fielding Independent Pitching)
- Simplified WAR (Wins Above Replacement)

These calculations use league-average constants derived from the simulation's
actual results, making them context-appropriate for the simulated environment.
"""

from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple
import sqlite3
from datetime import date


@dataclass
class LeagueConstants:
    """
    League-wide constants used for advanced stat calculations.
    
    These are calculated from the simulation's actual results to provide
    context-appropriate baselines.
    """
    # Offensive constants
    league_woba: float = 0.320          # League average wOBA
    woba_scale: float = 1.25            # wOBA to runs conversion
    runs_per_pa: float = 0.12           # League R/PA
    runs_per_win: float = 10.0          # Runs per win (standard)
    
    # wOBA weights (2024 MLB approximate)
    wBB: float = 0.690                  # Walk weight
    wHBP: float = 0.720                 # HBP weight  
    w1B: float = 0.880                  # Single weight
    w2B: float = 1.240                  # Double weight
    w3B: float = 1.560                  # Triple weight
    wHR: float = 2.010                  # Home run weight
    
    # Pitching constants
    league_era: float = 4.00            # League average ERA
    league_fip: float = 4.00            # League average FIP
    fip_constant: float = 3.10          # FIP constant (cFIP)
    
    # Replacement level
    replacement_level_batting: float = 0.030  # Runs above replacement per PA
    replacement_level_pitching: float = 0.030 # Runs above replacement per IP


@dataclass
class AdvancedBattingStats:
    """Advanced batting statistics for a player."""
    player_name: str
    team: str
    
    # Traditional stats for reference
    games: int
    pa: int
    avg: float
    obp: float
    slg: float
    ops: float
    
    # Advanced stats
    woba: float
    wrc: float          # Weighted Runs Created
    wrc_plus: float     # wRC+ (100 = league average)
    
    # WAR components
    batting_runs: float
    replacement_runs: float
    war: float
    
    # Rate stats
    bb_pct: float
    k_pct: float
    iso: float          # Isolated Power (SLG - AVG)
    babip: float        # BABIP


@dataclass
class AdvancedPitchingStats:
    """Advanced pitching statistics for a player."""
    player_name: str
    team: str
    
    # Traditional stats for reference
    games: int
    ip: float
    era: float
    whip: float
    
    # Advanced stats
    fip: float
    xfip: float         # Expected FIP (normalized HR/FB)
    
    # WAR components
    fip_runs: float
    replacement_runs: float
    war: float
    
    # Rate stats
    k_per_9: float
    bb_per_9: float
    hr_per_9: float
    k_bb_ratio: float   # K/BB ratio


class AdvancedStatsCalculator:
    """
    Calculate advanced statistics from season data.
    
    This class computes league constants from actual simulation results
    and uses them to calculate context-appropriate advanced stats.
    """
    
    def __init__(self, db_path: str = "saved_stats/season_stats.db"):
        """Initialize with path to stats database."""
        self.db_path = db_path
        self._conn: Optional[sqlite3.Connection] = None
    
    def _get_connection(self) -> sqlite3.Connection:
        """Get database connection."""
        if self._conn is None:
            self._conn = sqlite3.connect(self.db_path)
            self._conn.row_factory = sqlite3.Row
        return self._conn
    
    def close(self):
        """Close database connection."""
        if self._conn:
            self._conn.close()
            self._conn = None
    
    def calculate_league_constants(self, season_id: int) -> LeagueConstants:
        """
        Calculate league-wide constants from the season's data.
        
        These constants are used as baselines for wRC+, FIP, etc.
        
        Parameters
        ----------
        season_id : int
            The season to calculate constants for
        
        Returns
        -------
        LeagueConstants
            Calculated league constants
        """
        conn = self._get_connection()
        cursor = conn.cursor()
        
        # Get league batting totals
        cursor.execute("""
            SELECT 
                SUM(plate_appearances) as total_pa,
                SUM(at_bats) as total_ab,
                SUM(hits) as total_h,
                SUM(doubles) as total_2b,
                SUM(triples) as total_3b,
                SUM(home_runs) as total_hr,
                SUM(walks) as total_bb,
                SUM(hit_by_pitch) as total_hbp,
                SUM(runs) as total_r,
                SUM(sacrifice_flies) as total_sf
            FROM season_batting
            WHERE season_id = ?
        """, (season_id,))
        
        batting = cursor.fetchone()
        
        # Get league pitching totals
        cursor.execute("""
            SELECT 
                SUM(outs_recorded) as total_outs,
                SUM(earned_runs) as total_er,
                SUM(strikeouts) as total_k,
                SUM(walks) as total_bb,
                SUM(home_runs_allowed) as total_hr,
                SUM(fly_balls) as total_fb
            FROM season_pitching
            WHERE season_id = ?
        """, (season_id,))
        
        pitching = cursor.fetchone()
        
        constants = LeagueConstants()
        
        if batting and batting['total_pa'] and batting['total_pa'] > 0:
            pa = batting['total_pa']
            ab = batting['total_ab'] or 1
            h = batting['total_h'] or 0
            singles = h - (batting['total_2b'] or 0) - (batting['total_3b'] or 0) - (batting['total_hr'] or 0)
            doubles = batting['total_2b'] or 0
            triples = batting['total_3b'] or 0
            hr = batting['total_hr'] or 0
            bb = batting['total_bb'] or 0
            hbp = batting['total_hbp'] or 0
            sf = batting['total_sf'] or 0
            runs = batting['total_r'] or 0
            
            # Calculate league wOBA
            woba_num = (constants.wBB * bb + constants.wHBP * hbp + 
                       constants.w1B * singles + constants.w2B * doubles + 
                       constants.w3B * triples + constants.wHR * hr)
            woba_den = ab + bb + sf + hbp
            
            if woba_den > 0:
                constants.league_woba = woba_num / woba_den
            
            # Calculate runs per PA
            if pa > 0:
                constants.runs_per_pa = runs / pa
        
        if pitching and pitching['total_outs'] and pitching['total_outs'] > 0:
            outs = pitching['total_outs']
            ip = outs / 3.0
            er = pitching['total_er'] or 0
            k = pitching['total_k'] or 0
            bb = pitching['total_bb'] or 0
            hr = pitching['total_hr'] or 0
            fb = pitching['total_fb'] or 1
            
            # Calculate league ERA
            if ip > 0:
                constants.league_era = 9.0 * er / ip
            
            # Calculate league FIP
            if ip > 0:
                fip_core = (13 * hr + 3 * bb - 2 * k) / ip
                constants.league_fip = fip_core + constants.fip_constant
            
            # Adjust FIP constant to align FIP with ERA
            if ip > 0:
                fip_core = (13 * hr + 3 * bb - 2 * k) / ip
                constants.fip_constant = constants.league_era - fip_core
        
        return constants
    
    def calculate_batting_stats(
        self, 
        season_id: int, 
        min_pa: int = 50,
        constants: Optional[LeagueConstants] = None
    ) -> List[AdvancedBattingStats]:
        """
        Calculate advanced batting stats for all qualified players.
        
        Parameters
        ----------
        season_id : int
            The season to calculate for
        min_pa : int
            Minimum plate appearances to qualify
        constants : LeagueConstants, optional
            Pre-calculated league constants (will calculate if not provided)
        
        Returns
        -------
        List[AdvancedBattingStats]
            Advanced stats for each qualified player
        """
        if constants is None:
            constants = self.calculate_league_constants(season_id)
        
        conn = self._get_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT 
                player_name, team, games, plate_appearances, at_bats,
                runs, hits, doubles, triples, home_runs, rbi,
                walks, strikeouts, hit_by_pitch, sacrifice_flies,
                batted_balls
            FROM season_batting
            WHERE season_id = ? AND plate_appearances >= ?
            ORDER BY plate_appearances DESC
        """, (season_id, min_pa))
        
        results = []
        
        for row in cursor.fetchall():
            pa = row['plate_appearances']
            ab = row['at_bats'] or 1
            h = row['hits'] or 0
            doubles = row['doubles'] or 0
            triples = row['triples'] or 0
            hr = row['home_runs'] or 0
            singles = h - doubles - triples - hr
            bb = row['walks'] or 0
            hbp = row['hit_by_pitch'] or 0
            so = row['strikeouts'] or 0
            sf = row['sacrifice_flies'] or 0
            batted_balls = row['batted_balls'] or 0
            
            # Traditional stats
            avg = h / ab if ab > 0 else 0
            obp_num = h + bb + hbp
            obp_den = ab + bb + hbp + sf
            obp = obp_num / obp_den if obp_den > 0 else 0
            
            tb = singles + 2*doubles + 3*triples + 4*hr
            slg = tb / ab if ab > 0 else 0
            ops = obp + slg
            iso = slg - avg
            
            # BABIP = (H - HR) / (AB - K - HR + SF)
            babip_num = h - hr
            babip_den = ab - so - hr + sf
            babip = babip_num / babip_den if babip_den > 0 else 0
            
            # Rate stats
            bb_pct = bb / pa if pa > 0 else 0
            k_pct = so / pa if pa > 0 else 0
            
            # wOBA calculation
            woba_num = (constants.wBB * bb + constants.wHBP * hbp + 
                       constants.w1B * singles + constants.w2B * doubles + 
                       constants.w3B * triples + constants.wHR * hr)
            woba_den = ab + bb + sf + hbp
            woba = woba_num / woba_den if woba_den > 0 else 0
            
            # wRC (Weighted Runs Created)
            # wRC = ((wOBA - lgwOBA) / wOBA_scale + R/PA) * PA
            wrc = ((woba - constants.league_woba) / constants.woba_scale + 
                   constants.runs_per_pa) * pa
            
            # wRC+ = 100 * (wRC/PA) / league_runs_per_pa
            # Simplified: wRC+ = 100 * wOBA / league_wOBA (approximately)
            if constants.league_woba > 0:
                wrc_plus = 100 * (woba / constants.league_woba)
            else:
                wrc_plus = 100
            
            # Batting runs above average
            batting_runs = ((woba - constants.league_woba) / constants.woba_scale) * pa
            
            # Replacement runs
            replacement_runs = constants.replacement_level_batting * pa
            
            # WAR (simplified: batting runs + replacement runs, converted to wins)
            war = (batting_runs + replacement_runs) / constants.runs_per_win
            
            results.append(AdvancedBattingStats(
                player_name=row['player_name'],
                team=row['team'],
                games=row['games'],
                pa=pa,
                avg=round(avg, 3),
                obp=round(obp, 3),
                slg=round(slg, 3),
                ops=round(ops, 3),
                woba=round(woba, 3),
                wrc=round(wrc, 1),
                wrc_plus=round(wrc_plus, 0),
                batting_runs=round(batting_runs, 1),
                replacement_runs=round(replacement_runs, 1),
                war=round(war, 1),
                bb_pct=round(bb_pct * 100, 1),
                k_pct=round(k_pct * 100, 1),
                iso=round(iso, 3),
                babip=round(babip, 3)
            ))
        
        return results
    
    def calculate_pitching_stats(
        self,
        season_id: int,
        min_ip: float = 10.0,
        constants: Optional[LeagueConstants] = None
    ) -> List[AdvancedPitchingStats]:
        """
        Calculate advanced pitching stats for all qualified players.
        
        Parameters
        ----------
        season_id : int
            The season to calculate for
        min_ip : float
            Minimum innings pitched to qualify
        constants : LeagueConstants, optional
            Pre-calculated league constants
        
        Returns
        -------
        List[AdvancedPitchingStats]
            Advanced stats for each qualified player
        """
        if constants is None:
            constants = self.calculate_league_constants(season_id)
        
        conn = self._get_connection()
        cursor = conn.cursor()
        
        min_outs = int(min_ip * 3)
        
        cursor.execute("""
            SELECT 
                player_name, team, games, outs_recorded,
                hits_allowed, runs_allowed, earned_runs,
                walks, strikeouts, home_runs_allowed, hit_batters,
                batters_faced, fly_balls, ground_balls
            FROM season_pitching
            WHERE season_id = ? AND outs_recorded >= ?
            ORDER BY outs_recorded DESC
        """, (season_id, min_outs))
        
        # Fetch all player rows BEFORE running another query
        player_rows = cursor.fetchall()
        
        results = []
        
        # Get league average HR/FB rate for xFIP
        cursor.execute("""
            SELECT 
                SUM(home_runs_allowed) as total_hr,
                SUM(fly_balls) as total_fb
            FROM season_pitching
            WHERE season_id = ?
        """, (season_id,))
        league_totals = cursor.fetchone()
        league_hr_fb = 0.10  # Default 10%
        if league_totals and league_totals['total_fb'] and league_totals['total_fb'] > 0:
            league_hr_fb = (league_totals['total_hr'] or 0) / league_totals['total_fb']
        
        for row in player_rows:
            outs = row['outs_recorded']
            ip = outs / 3.0
            
            h = row['hits_allowed'] or 0
            er = row['earned_runs'] or 0
            bb = row['walks'] or 0
            so = row['strikeouts'] or 0
            hr = row['home_runs_allowed'] or 0
            fb = row['fly_balls'] or 1
            bf = row['batters_faced'] or 1
            
            # Traditional stats
            era = 9.0 * er / ip if ip > 0 else 0
            whip = (bb + h) / ip if ip > 0 else 0
            
            # Rate stats
            k_per_9 = 9.0 * so / ip if ip > 0 else 0
            bb_per_9 = 9.0 * bb / ip if ip > 0 else 0
            hr_per_9 = 9.0 * hr / ip if ip > 0 else 0
            k_bb = so / bb if bb > 0 else so
            
            # FIP = (13*HR + 3*BB - 2*K) / IP + cFIP
            fip = (13 * hr + 3 * bb - 2 * so) / ip + constants.fip_constant if ip > 0 else 0
            
            # xFIP - uses league HR/FB rate
            expected_hr = fb * league_hr_fb
            xfip = (13 * expected_hr + 3 * bb - 2 * so) / ip + constants.fip_constant if ip > 0 else 0
            
            # FIP-based runs (runs saved vs league average)
            fip_runs = (constants.league_fip - fip) * ip / 9.0
            
            # Replacement runs
            replacement_runs = constants.replacement_level_pitching * ip
            
            # WAR (simplified)
            war = (fip_runs + replacement_runs) / constants.runs_per_win
            
            results.append(AdvancedPitchingStats(
                player_name=row['player_name'],
                team=row['team'],
                games=row['games'],
                ip=round(ip, 1),
                era=round(era, 2),
                whip=round(whip, 2),
                fip=round(fip, 2),
                xfip=round(xfip, 2),
                fip_runs=round(fip_runs, 1),
                replacement_runs=round(replacement_runs, 1),
                war=round(war, 1),
                k_per_9=round(k_per_9, 1),
                bb_per_9=round(bb_per_9, 1),
                hr_per_9=round(hr_per_9, 1),
                k_bb_ratio=round(k_bb, 2)
            ))
        
        return results
    
    def get_war_leaders(
        self,
        season_id: int,
        stat_type: str = "batting",
        limit: int = 10
    ) -> List[dict]:
        """
        Get WAR leaders for a season.
        
        Parameters
        ----------
        season_id : int
            The season
        stat_type : str
            "batting" or "pitching"
        limit : int
            Number of leaders to return
        
        Returns
        -------
        List[dict]
            WAR leaders with name, team, and WAR
        """
        constants = self.calculate_league_constants(season_id)
        
        if stat_type == "batting":
            stats = self.calculate_batting_stats(season_id, min_pa=20, constants=constants)
            stats.sort(key=lambda x: x.war, reverse=True)
            return [
                {"player_name": s.player_name, "team": s.team, "war": s.war, 
                 "wrc_plus": s.wrc_plus, "woba": s.woba}
                for s in stats[:limit]
            ]
        else:
            stats = self.calculate_pitching_stats(season_id, min_ip=5.0, constants=constants)
            stats.sort(key=lambda x: x.war, reverse=True)
            return [
                {"player_name": s.player_name, "team": s.team, "war": s.war,
                 "fip": s.fip, "era": s.era}
                for s in stats[:limit]
            ]
