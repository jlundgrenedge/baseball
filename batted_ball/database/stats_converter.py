"""
Convert MLB statistics to game attributes (0-100,000 scale).

Maps real MLB player statistics to the physics-first attribute system using
percentile-based transformations and empirical relationships.

Sources:
- MLB Statcast data (2015-2024)
- Baseball Savant percentile ranks
- Empirical correlations between stats and physical capabilities
"""

import numpy as np
from typing import Dict, Optional, Tuple


class StatsConverter:
    """Convert MLB statistics to game attributes (0-100,000 scale)."""

    # Pitcher stat ranges (from MLB data 2015-2024)
    # ERA ranges (starters + qualified relievers)
    PITCHER_ERA_ELITE = 2.50  # Top 10%
    PITCHER_ERA_GOOD = 3.50   # Top 30%
    PITCHER_ERA_AVG = 4.20    # League average
    PITCHER_ERA_POOR = 5.50   # Bottom 30%

    # K/9 ranges
    PITCHER_K9_ELITE = 11.0   # Top 10%
    PITCHER_K9_GOOD = 9.5     # Top 30%
    PITCHER_K9_AVG = 8.5      # League average
    PITCHER_K9_POOR = 6.5     # Bottom 30%

    # BB/9 ranges (lower is better)
    PITCHER_BB9_ELITE = 1.8   # Top 10%
    PITCHER_BB9_GOOD = 2.5    # Top 30%
    PITCHER_BB9_AVG = 3.2     # League average
    PITCHER_BB9_POOR = 4.0    # Bottom 30%

    # Fastball velocity (mph)
    PITCHER_VELO_ELITE = 97.0
    PITCHER_VELO_GOOD = 94.5
    PITCHER_VELO_AVG = 92.5
    PITCHER_VELO_POOR = 90.0

    # Hitter stat ranges
    # OPS ranges
    HITTER_OPS_ELITE = 0.900  # Top 10%
    HITTER_OPS_GOOD = 0.800   # Top 30%
    HITTER_OPS_AVG = 0.720    # League average
    HITTER_OPS_POOR = 0.650   # Bottom 30%

    # Batting average
    HITTER_AVG_ELITE = 0.300
    HITTER_AVG_GOOD = 0.280
    HITTER_AVG_AVG = 0.250
    HITTER_AVG_POOR = 0.220

    # Exit velocity (mph)
    HITTER_EV_ELITE = 92.0    # Top 10%
    HITTER_EV_GOOD = 89.5     # Top 30%
    HITTER_EV_AVG = 87.5      # League average
    HITTER_EV_POOR = 85.0     # Bottom 30%

    # Sprint speed (ft/s)
    HITTER_SPEED_ELITE = 29.5
    HITTER_SPEED_GOOD = 28.5
    HITTER_SPEED_AVG = 27.5
    HITTER_SPEED_POOR = 26.0

    # Barrel rate (%)
    HITTER_BARREL_ELITE = 12.0
    HITTER_BARREL_GOOD = 8.0
    HITTER_BARREL_AVG = 6.0
    HITTER_BARREL_POOR = 4.0

    # K% ranges (lower is better for contact)
    HITTER_K_PCT_ELITE = 15.0   # Top contact (low K%)
    HITTER_K_PCT_GOOD = 20.0
    HITTER_K_PCT_AVG = 23.0
    HITTER_K_PCT_POOR = 28.0

    # Defensive metric ranges (v2 addition for BABIP tuning)
    # OAA (Outs Above Average) - Statcast metric
    FIELDER_OAA_ELITE = 8.0     # +8 OAA = elite defender
    FIELDER_OAA_GOOD = 3.0
    FIELDER_OAA_AVG = 0.0
    FIELDER_OAA_POOR = -5.0

    # DRS (Defensive Runs Saved) - FanGraphs metric
    FIELDER_DRS_ELITE = 10.0    # +10 DRS = elite
    FIELDER_DRS_GOOD = 5.0
    FIELDER_DRS_AVG = 0.0
    FIELDER_DRS_POOR = -5.0

    @staticmethod
    def percentile_to_rating(
        value: float,
        elite: float,
        good: float,
        avg: float,
        poor: float,
        inverse: bool = False
    ) -> int:
        """
        Convert a stat value to 0-100,000 rating using percentile mapping.

        Parameters
        ----------
        value : float
            The stat value to convert
        elite : float
            Elite threshold (90th percentile)
        good : float
            Good threshold (70th percentile)
        avg : float
            Average threshold (50th percentile)
        poor : float
            Poor threshold (30th percentile)
        inverse : bool
            If True, lower values are better (e.g., ERA, BB/9)

        Returns
        -------
        int
            Rating from 0-100,000
        """
        if inverse:
            # Lower is better - flip the scale
            if value <= elite:
                # Elite range (90k-100k)
                return int(90000 + 10000 * (elite - value) / max(elite * 0.2, 0.5))
            elif value <= good:
                # Good range (70k-90k)
                t = (value - elite) / (good - elite)
                return int(90000 - 20000 * t)
            elif value <= avg:
                # Average range (50k-70k)
                t = (value - good) / (avg - good)
                return int(70000 - 20000 * t)
            elif value <= poor:
                # Below average (30k-50k)
                t = (value - avg) / (poor - avg)
                return int(50000 - 20000 * t)
            else:
                # Poor range (0-30k)
                t = min((value - poor) / (poor * 0.5), 1.0)
                return int(30000 - 30000 * t)
        else:
            # Higher is better
            if value >= elite:
                # Elite range (90k-100k)
                return int(90000 + 10000 * (value - elite) / max(elite * 0.1, 0.05))
            elif value >= good:
                # Good range (70k-90k)
                t = (value - good) / (elite - good)
                return int(70000 + 20000 * t)
            elif value >= avg:
                # Average range (50k-70k)
                t = (value - avg) / (good - avg)
                return int(50000 + 20000 * t)
            elif value >= poor:
                # Below average (30k-50k)
                t = (value - poor) / (avg - poor)
                return int(30000 + 20000 * t)
            else:
                # Poor range (0-30k)
                t = max(value / poor, 0.0)
                return int(30000 * t)

    @classmethod
    def mlb_stats_to_pitcher_attributes(
        cls,
        era: Optional[float] = None,
        whip: Optional[float] = None,
        k_per_9: Optional[float] = None,
        bb_per_9: Optional[float] = None,
        avg_fastball_velo: Optional[float] = None,
        innings_pitched: Optional[float] = None,
        games_pitched: Optional[int] = None,
    ) -> Dict[str, int]:
        """
        Convert MLB pitcher statistics to game attributes.

        Parameters
        ----------
        era : float, optional
            Earned run average
        whip : float, optional
            Walks + hits per inning pitched
        k_per_9 : float, optional
            Strikeouts per 9 innings
        bb_per_9 : float, optional
            Walks per 9 innings
        avg_fastball_velo : float, optional
            Average fastball velocity in mph
        innings_pitched : float, optional
            Total innings pitched
        games_pitched : int, optional
            Total games pitched

        Returns
        -------
        dict
            Dictionary with keys: velocity, command, stamina, movement, repertoire
        """
        attributes = {}

        # VELOCITY (from avg fastball velo)
        if avg_fastball_velo is not None:
            attributes['velocity'] = cls.percentile_to_rating(
                avg_fastball_velo,
                cls.PITCHER_VELO_ELITE,
                cls.PITCHER_VELO_GOOD,
                cls.PITCHER_VELO_AVG,
                cls.PITCHER_VELO_POOR,
                inverse=False
            )
        else:
            attributes['velocity'] = 50000  # Default average

        # COMMAND (from BB/9 and WHIP)
        command_rating = 50000
        if bb_per_9 is not None:
            bb_rating = cls.percentile_to_rating(
                bb_per_9,
                cls.PITCHER_BB9_ELITE,
                cls.PITCHER_BB9_GOOD,
                cls.PITCHER_BB9_AVG,
                cls.PITCHER_BB9_POOR,
                inverse=True  # Lower BB/9 is better
            )
            command_rating = bb_rating

        if whip is not None:
            whip_rating = cls.percentile_to_rating(
                whip,
                0.95,   # Elite WHIP
                1.10,   # Good WHIP
                1.28,   # Average WHIP
                1.45,   # Poor WHIP
                inverse=True
            )
            # Average BB/9 and WHIP ratings
            command_rating = int((command_rating + whip_rating) / 2)

        attributes['command'] = command_rating

        # STAMINA (from innings pitched and games)
        if innings_pitched is not None and games_pitched is not None and games_pitched > 0:
            ip_per_game = innings_pitched / games_pitched
            # Starters average 5-6 IP/game, relievers 1-2 IP/game
            stamina_rating = cls.percentile_to_rating(
                ip_per_game,
                6.5,    # Elite (deep starter)
                5.5,    # Good starter
                3.0,    # Swing man
                1.5,    # Reliever
                inverse=False
            )
            attributes['stamina'] = stamina_rating
        else:
            attributes['stamina'] = 60000  # Default to starter-ish

        # MOVEMENT/REPERTOIRE (from K/9 and ERA)
        movement_rating = 50000
        if k_per_9 is not None:
            # High K/9 suggests good stuff (movement + deception)
            movement_rating = cls.percentile_to_rating(
                k_per_9,
                cls.PITCHER_K9_ELITE,
                cls.PITCHER_K9_GOOD,
                cls.PITCHER_K9_AVG,
                cls.PITCHER_K9_POOR,
                inverse=False
            )

        if era is not None:
            # Good ERA suggests overall effectiveness
            era_rating = cls.percentile_to_rating(
                era,
                cls.PITCHER_ERA_ELITE,
                cls.PITCHER_ERA_GOOD,
                cls.PITCHER_ERA_AVG,
                cls.PITCHER_ERA_POOR,
                inverse=True
            )
            # Blend K/9 and ERA for movement
            movement_rating = int((movement_rating + era_rating) / 2)

        attributes['movement'] = movement_rating
        attributes['repertoire'] = movement_rating  # Use same for now

        return attributes

    @classmethod
    def mlb_stats_to_hitter_attributes(
        cls,
        batting_avg: Optional[float] = None,
        on_base_pct: Optional[float] = None,
        slugging_pct: Optional[float] = None,
        ops: Optional[float] = None,
        home_runs: Optional[int] = None,
        strikeouts: Optional[int] = None,
        walks: Optional[int] = None,
        at_bats: Optional[int] = None,
        avg_exit_velo: Optional[float] = None,
        max_exit_velo: Optional[float] = None,
        barrel_pct: Optional[float] = None,
        sprint_speed: Optional[float] = None,
        stolen_bases: Optional[int] = None,
    ) -> Dict[str, int]:
        """
        Convert MLB hitter statistics to game attributes.

        Parameters
        ----------
        batting_avg : float, optional
            Batting average
        on_base_pct : float, optional
            On-base percentage
        slugging_pct : float, optional
            Slugging percentage
        ops : float, optional
            On-base plus slugging
        home_runs : int, optional
            Total home runs
        strikeouts : int, optional
            Total strikeouts
        walks : int, optional
            Total walks
        at_bats : int, optional
            Total at-bats
        avg_exit_velo : float, optional
            Average exit velocity (mph)
        max_exit_velo : float, optional
            Maximum exit velocity (mph)
        barrel_pct : float, optional
            Barrel percentage
        sprint_speed : float, optional
            Sprint speed (ft/s)
        stolen_bases : int, optional
            Total stolen bases (used for speed estimation when sprint_speed unavailable)

        Returns
        -------
        dict
            Dictionary with keys: contact, power, discipline, speed
        """
        attributes = {}

        # Calculate OPS if not provided
        if ops is None and on_base_pct is not None and slugging_pct is not None:
            ops = on_base_pct + slugging_pct

        # CONTACT (from batting average and K%)
        contact_rating = 50000
        if batting_avg is not None:
            contact_rating = cls.percentile_to_rating(
                batting_avg,
                cls.HITTER_AVG_ELITE,
                cls.HITTER_AVG_GOOD,
                cls.HITTER_AVG_AVG,
                cls.HITTER_AVG_POOR,
                inverse=False
            )

        if strikeouts is not None and at_bats is not None and at_bats > 0:
            k_pct = (strikeouts / at_bats) * 100
            k_rating = cls.percentile_to_rating(
                k_pct,
                cls.HITTER_K_PCT_ELITE,
                cls.HITTER_K_PCT_GOOD,
                cls.HITTER_K_PCT_AVG,
                cls.HITTER_K_PCT_POOR,
                inverse=True  # Lower K% is better
            )
            # Average batting avg and K% ratings
            contact_rating = int((contact_rating + k_rating) / 2)

        attributes['contact'] = contact_rating

        # POWER (from exit velocity, barrel %, slugging, HRs)
        power_ratings = []

        if avg_exit_velo is not None:
            ev_rating = cls.percentile_to_rating(
                avg_exit_velo,
                cls.HITTER_EV_ELITE,
                cls.HITTER_EV_GOOD,
                cls.HITTER_EV_AVG,
                cls.HITTER_EV_POOR,
                inverse=False
            )
            power_ratings.append(ev_rating)

        if barrel_pct is not None:
            barrel_rating = cls.percentile_to_rating(
                barrel_pct,
                cls.HITTER_BARREL_ELITE,
                cls.HITTER_BARREL_GOOD,
                cls.HITTER_BARREL_AVG,
                cls.HITTER_BARREL_POOR,
                inverse=False
            )
            power_ratings.append(barrel_rating)

        if slugging_pct is not None:
            slg_rating = cls.percentile_to_rating(
                slugging_pct,
                0.550,  # Elite slugging
                0.470,  # Good slugging
                0.410,  # Average slugging
                0.360,  # Poor slugging
                inverse=False
            )
            power_ratings.append(slg_rating)

        if home_runs is not None and at_bats is not None and at_bats > 0:
            hr_per_ab = home_runs / at_bats
            hr_rating = cls.percentile_to_rating(
                hr_per_ab,
                0.065,  # Elite (40+ HR in 600 AB)
                0.050,  # Good (30 HR)
                0.035,  # Average (20 HR)
                0.020,  # Poor (12 HR)
                inverse=False
            )
            power_ratings.append(hr_rating)

        if power_ratings:
            attributes['power'] = int(np.mean(power_ratings))
        else:
            attributes['power'] = 50000

        # DISCIPLINE (from walk rate, OBP, K rate)
        discipline_ratings = []

        if walks is not None and at_bats is not None and at_bats > 0:
            bb_pct = (walks / at_bats) * 100
            bb_rating = cls.percentile_to_rating(
                bb_pct,
                15.0,   # Elite walk rate
                11.0,   # Good
                8.5,    # Average
                6.0,    # Poor
                inverse=False
            )
            discipline_ratings.append(bb_rating)

        if on_base_pct is not None:
            obp_rating = cls.percentile_to_rating(
                on_base_pct,
                0.380,  # Elite OBP
                0.350,  # Good
                0.320,  # Average
                0.300,  # Poor
                inverse=False
            )
            discipline_ratings.append(obp_rating)

        # Also factor in K% (already calculated for contact)
        if strikeouts is not None and at_bats is not None and at_bats > 0:
            k_pct = (strikeouts / at_bats) * 100
            k_disc_rating = cls.percentile_to_rating(
                k_pct,
                cls.HITTER_K_PCT_ELITE,
                cls.HITTER_K_PCT_GOOD,
                cls.HITTER_K_PCT_AVG,
                cls.HITTER_K_PCT_POOR,
                inverse=True
            )
            discipline_ratings.append(k_disc_rating)

        if discipline_ratings:
            attributes['discipline'] = int(np.mean(discipline_ratings))
        else:
            attributes['discipline'] = 50000

        # SPEED (from sprint speed, with stolen bases fallback)
        # Priority: sprint_speed (Statcast physical measurement) > stolen_bases estimation > default
        if sprint_speed is not None:
            # Use actual sprint speed from Statcast (ft/s)
            speed_rating = cls.percentile_to_rating(
                sprint_speed,
                cls.HITTER_SPEED_ELITE,
                cls.HITTER_SPEED_GOOD,
                cls.HITTER_SPEED_AVG,
                cls.HITTER_SPEED_POOR,
                inverse=False
            )
            attributes['speed'] = speed_rating
        elif stolen_bases is not None and at_bats is not None and at_bats > 0:
            # FALLBACK: Estimate from stolen bases when sprint speed not available
            # Note: This is imperfect (strategy-dependent) but better than defaulting to average
            # SB per 600 AB: Elite 30+, Good 15-25, Avg 5-15, Poor <5
            sb_per_600 = (stolen_bases / at_bats) * 600
            speed_rating = cls.percentile_to_rating(
                sb_per_600,
                30.0,   # Elite (30+ SB per 600 AB)
                20.0,   # Good (20 SB)
                10.0,   # Average (10 SB)
                5.0,    # Poor (5 SB)
                inverse=False
            )
            attributes['speed'] = speed_rating
        else:
            # No speed data available - use league average
            attributes['speed'] = 50000  # Default average

        return attributes

    @classmethod
    def mlb_stats_to_pitcher_attributes_v2(
        cls,
        era: Optional[float] = None,
        whip: Optional[float] = None,
        k_per_9: Optional[float] = None,
        bb_per_9: Optional[float] = None,
        avg_fastball_velo: Optional[float] = None,
        innings_pitched: Optional[float] = None,
        games_pitched: Optional[int] = None,
    ) -> Dict[str, any]:
        """
        Convert MLB pitcher statistics to v2 game attributes (Phase 2A/2B).

        Includes all v1 attributes PLUS v2 additions:
        - PUTAWAY_SKILL: Finishing ability with 2 strikes (from K/9)
        - NIBBLING_TENDENCY: Control strategy by count (from BB/9)

        Parameters
        ----------
        Same as mlb_stats_to_pitcher_attributes

        Returns
        -------
        dict
            Dictionary with v1 keys (velocity, command, stamina, movement, repertoire)
            PLUS v2 keys (putaway_skill, nibbling_tendency)
        """
        # Get v1 attributes using existing method
        attrs = cls.mlb_stats_to_pitcher_attributes(
            era, whip, k_per_9, bb_per_9, avg_fastball_velo, innings_pitched, games_pitched
        )

        # Add v2 attributes

        # PUTAWAY_SKILL: Finishing ability with 2 strikes (0-100k)
        # High K/9 = high finishing ability
        if k_per_9 is not None:
            attrs['putaway_skill'] = cls.percentile_to_rating(
                k_per_9,
                cls.PITCHER_K9_ELITE,   # 11.0 K/9 = elite (95k-100k)
                cls.PITCHER_K9_GOOD,    # 9.5 K/9 = good (70k-90k)
                cls.PITCHER_K9_AVG,     # 8.5 K/9 = average (50k-70k)
                cls.PITCHER_K9_POOR,    # 6.5 K/9 = poor (30k-50k)
                inverse=False
            )
        else:
            attrs['putaway_skill'] = 50000  # Default average

        # NIBBLING_TENDENCY: Control strategy (0.0-1.0, NOT 0-100k!)
        # High BB/9 = high nibbling (pitches around zone)
        # Low BB/9 = low nibbling (attacks zone)
        if bb_per_9 is not None:
            if bb_per_9 < 2.0:
                attrs['nibbling_tendency'] = 0.20  # Aggressive (Gerrit Cole)
            elif bb_per_9 < 2.5:
                attrs['nibbling_tendency'] = 0.35
            elif bb_per_9 < 3.5:
                attrs['nibbling_tendency'] = 0.50  # Average
            elif bb_per_9 < 4.5:
                attrs['nibbling_tendency'] = 0.65
            else:
                attrs['nibbling_tendency'] = 0.80  # Very careful
        else:
            attrs['nibbling_tendency'] = 0.50  # Default average

        return attrs

    @classmethod
    def mlb_stats_to_hitter_attributes_v2(
        cls,
        batting_avg: Optional[float] = None,
        on_base_pct: Optional[float] = None,
        slugging_pct: Optional[float] = None,
        ops: Optional[float] = None,
        home_runs: Optional[int] = None,
        strikeouts: Optional[int] = None,
        walks: Optional[int] = None,
        at_bats: Optional[int] = None,
        avg_exit_velo: Optional[float] = None,
        max_exit_velo: Optional[float] = None,
        barrel_pct: Optional[float] = None,
        sprint_speed: Optional[float] = None,
        stolen_bases: Optional[int] = None,
    ) -> Dict[str, int]:
        """
        Convert MLB hitter statistics to v2 game attributes (Phase 2A).

        Includes all v1 attributes PLUS v2 additions:
        - VISION: Contact frequency independent of power (from K%)

        Parameters
        ----------
        Same as mlb_stats_to_hitter_attributes

        Returns
        -------
        dict
            Dictionary with v1 keys (contact, power, discipline, speed)
            PLUS v2 key (vision)
        """
        # Get v1 attributes using existing method
        attrs = cls.mlb_stats_to_hitter_attributes(
            batting_avg, on_base_pct, slugging_pct, ops, home_runs,
            strikeouts, walks, at_bats, avg_exit_velo, max_exit_velo,
            barrel_pct, sprint_speed, stolen_bases
        )

        # Add v2 attribute: VISION
        # Controls whiff probability independently from contact quality
        # Low K% = high VISION = fewer whiffs
        if strikeouts is not None and at_bats is not None and at_bats > 0:
            k_pct = (strikeouts / at_bats) * 100
            attrs['vision'] = cls.percentile_to_rating(
                k_pct,
                cls.HITTER_K_PCT_ELITE,    # 15% K = elite vision (95k-100k)
                cls.HITTER_K_PCT_GOOD,     # 20% K = good vision (70k-90k)
                cls.HITTER_K_PCT_AVG,      # 23% K = average vision (50k-70k)
                cls.HITTER_K_PCT_POOR,     # 28% K = poor vision (30k-50k)
                inverse=True  # Lower K% is better
            )
        else:
            attrs['vision'] = 50000  # Default average

        return attrs

    @classmethod
    def mlb_stats_to_defensive_attributes(
        cls,
        position: str,
        oaa: Optional[float] = None,
        sprint_speed: Optional[float] = None,
        arm_strength_mph: Optional[float] = None,
        drs: Optional[float] = None,
        jump: Optional[float] = None,
        fielding_pct: Optional[float] = None
    ) -> Dict[str, int]:
        """
        Convert MLB defensive metrics to v2 game attributes (CRITICAL for BABIP tuning).

        Maps Statcast and FanGraphs defensive metrics to FielderAttributes (0-100k).

        Strategy:
        - Sprint speed → TOP_SPRINT_SPEED (direct mapping)
        - OAA + Jump → REACTION_TIME (better OAA/jump = faster reaction)
        - OAA + DRS → ROUTE_EFFICIENCY (better overall defense = better routes)
        - Arm strength → ARM_STRENGTH (direct mapping by position)
        - Fielding % → FIELDING_SECURE (fewer errors = more secure)
        - OAA residual → ARM_ACCURACY (defense not explained by speed/range)

        Parameters
        ----------
        position : str
            Primary position (C, 1B, 2B, SS, 3B, LF, CF, RF)
        oaa : float, optional
            Outs Above Average (Statcast)
        sprint_speed : float, optional
            Sprint speed in ft/s (Statcast)
        arm_strength_mph : float, optional
            Throw velocity in mph (Statcast, position-specific)
        drs : float, optional
            Defensive Runs Saved (FanGraphs)
        jump : float, optional
            Outfielder first step efficiency (Statcast)
        fielding_pct : float, optional
            Traditional fielding percentage

        Returns
        -------
        dict
            Dictionary with defensive attribute keys (all 0-100k scale):
            - reaction_time, top_sprint_speed, route_efficiency,
              arm_strength, arm_accuracy, fielding_secure
        """
        attrs = {}

        # 1. TOP_SPRINT_SPEED - Direct from Statcast sprint speed
        if sprint_speed is not None:
            attrs['top_sprint_speed'] = cls.percentile_to_rating(
                sprint_speed,
                cls.HITTER_SPEED_ELITE,   # 29.5 ft/s = elite
                cls.HITTER_SPEED_GOOD,    # 28.5 ft/s = good
                cls.HITTER_SPEED_AVG,     # 27.5 ft/s = average
                cls.HITTER_SPEED_POOR,    # 26.0 ft/s = poor
                inverse=False
            )
        else:
            attrs['top_sprint_speed'] = 50000  # Default average

        # 2. REACTION_TIME - From OAA + Jump (inverse: better OAA = faster reaction)
        # Combine OAA and jump into composite reaction score
        reaction_score = 0.0
        has_reaction_data = False

        if oaa is not None:
            reaction_score += oaa * 0.6  # OAA primary indicator
            has_reaction_data = True

        if jump is not None and position in ['LF', 'CF', 'RF']:
            reaction_score += jump * 0.4  # Jump for outfielders
            has_reaction_data = True

        if has_reaction_data:
            attrs['reaction_time'] = cls.percentile_to_rating(
                reaction_score,
                cls.FIELDER_OAA_ELITE,    # +8 OAA = elite reaction
                cls.FIELDER_OAA_GOOD,     # +3 OAA = good
                cls.FIELDER_OAA_AVG,      # 0 OAA = average
                cls.FIELDER_OAA_POOR,     # -5 OAA = poor
                inverse=True  # Higher OAA = LOWER reaction time (faster)
            )
        else:
            attrs['reaction_time'] = 50000

        # 3. ROUTE_EFFICIENCY - From OAA + DRS composite
        route_score = 0.0
        has_route_data = False

        if oaa is not None:
            route_score += oaa * 0.5
            has_route_data = True

        if drs is not None:
            route_score += drs * 0.5
            has_route_data = True

        if has_route_data:
            # Use average of OAA and DRS thresholds
            attrs['route_efficiency'] = cls.percentile_to_rating(
                route_score,
                (cls.FIELDER_OAA_ELITE + cls.FIELDER_DRS_ELITE) / 2,  # ~9.0
                (cls.FIELDER_OAA_GOOD + cls.FIELDER_DRS_GOOD) / 2,    # ~4.0
                (cls.FIELDER_OAA_AVG + cls.FIELDER_DRS_AVG) / 2,      # 0.0
                (cls.FIELDER_OAA_POOR + cls.FIELDER_DRS_POOR) / 2,    # ~-5.0
                inverse=False
            )
        else:
            attrs['route_efficiency'] = 50000

        # 4. ARM_STRENGTH - Position-specific from Statcast arm data
        # Position-specific thresholds (in mph)
        position_thresholds = {
            'C': {'elite': 83, 'good': 80, 'avg': 77, 'poor': 74},  # Catcher
            'SS': {'elite': 88, 'good': 85, 'avg': 82, 'poor': 79},  # Shortstop
            '3B': {'elite': 88, 'good': 85, 'avg': 82, 'poor': 79},  # Third base
            '2B': {'elite': 85, 'good': 82, 'avg': 79, 'poor': 76},  # Second base
            '1B': {'elite': 85, 'good': 82, 'avg': 79, 'poor': 76},  # First base
            'RF': {'elite': 92, 'good': 88, 'avg': 85, 'poor': 82},  # Right field (strongest)
            'CF': {'elite': 90, 'good': 87, 'avg': 84, 'poor': 81},  # Center field
            'LF': {'elite': 88, 'good': 85, 'avg': 82, 'poor': 79},  # Left field
        }

        thresh = position_thresholds.get(position, position_thresholds.get('CF', position_thresholds['CF']))

        if arm_strength_mph is not None:
            attrs['arm_strength'] = cls.percentile_to_rating(
                arm_strength_mph,
                thresh['elite'],
                thresh['good'],
                thresh['avg'],
                thresh['poor'],
                inverse=False
            )
        else:
            # Estimate from DRS/OAA if arm strength not available
            # Better defenders tend to have better arms
            if (drs is not None and drs > 5) or (oaa is not None and oaa > 5):
                # Elite defender - likely above average arm
                estimated_arm = thresh['good']
            elif (drs is not None and drs < -5) or (oaa is not None and oaa < -5):
                # Poor defender - likely below average arm
                estimated_arm = thresh['poor']
            else:
                # Average defender - average arm
                estimated_arm = thresh['avg']

            attrs['arm_strength'] = cls.percentile_to_rating(
                estimated_arm,
                thresh['elite'],
                thresh['good'],
                thresh['avg'],
                thresh['poor'],
                inverse=False
            )

        # 5. FIELDING_SECURE - From fielding % (higher % = more secure)
        if fielding_pct is not None:
            attrs['fielding_secure'] = cls.percentile_to_rating(
                fielding_pct,
                0.995,  # Elite fielding %
                0.985,  # Good
                0.975,  # Average
                0.960,  # Poor
                inverse=False
            )
        else:
            attrs['fielding_secure'] = 50000

        # 6. ARM_ACCURACY - Residual from defensive metrics
        # Use DRS that isn't explained by range (proxy for throwing accuracy)
        if drs is not None:
            # If we have OAA, calculate residual
            # If not, use DRS scaled down (less confident estimate)
            if oaa is not None:
                accuracy_score = drs - (oaa * 0.5)  # DRS beyond range
            else:
                accuracy_score = drs * 0.3  # Conservative estimate from DRS alone

            attrs['arm_accuracy'] = cls.percentile_to_rating(
                accuracy_score,
                5.0,   # Elite accuracy
                2.0,   # Good
                0.0,   # Average
                -3.0,  # Poor
                inverse=False
            )
        else:
            attrs['arm_accuracy'] = 50000

        return attrs

    @staticmethod
    def pitch_effectiveness_to_attributes(
        pitch_metrics: Dict[str, Dict[str, float]]
    ) -> Dict[str, Dict[str, int]]:
        """
        Convert pitch-level Statcast metrics to pitch-specific attribute adjustments.

        Parameters
        ----------
        pitch_metrics : dict
            Dictionary mapping pitch type to metrics:
            {'fastball': {'whiff_pct': 0.24, 'velocity': 96.5, ...}, ...}

        Returns
        -------
        dict
            Dictionary mapping pitch type to attribute adjustments:
            {'fastball': {'stuff_bonus': +5000, 'deception': 60000, ...}, ...}
        """
        pitch_attributes = {}

        for pitch_type, metrics in pitch_metrics.items():
            attrs = {}

            # STUFF/EFFECTIVENESS - Based on whiff rate
            # Elite whiff rate (>30% for breaking balls, >20% for fastballs) = high stuff
            # Average whiff rate (~20-25% breaking, ~10-15% fastball) = average stuff
            # Poor whiff rate (<15% breaking, <8% fastball) = poor stuff
            if 'whiff_pct' in metrics:
                whiff = metrics['whiff_pct']

                # Adjust thresholds based on pitch type
                if pitch_type in ['slider', 'splitter']:
                    # Breaking balls have higher baseline whiff rates
                    elite_whiff = 0.35
                    good_whiff = 0.28
                    avg_whiff = 0.22
                    poor_whiff = 0.16
                elif pitch_type in ['curveball', 'changeup']:
                    elite_whiff = 0.32
                    good_whiff = 0.25
                    avg_whiff = 0.20
                    poor_whiff = 0.14
                else:  # fastball, 2-seam, cutter
                    elite_whiff = 0.22
                    good_whiff = 0.16
                    avg_whiff = 0.12
                    poor_whiff = 0.08

                # Convert to 0-100,000 scale (stuffeffectiveness rating)
                stuff_rating = StatsConverter.percentile_to_rating(
                    whiff,
                    elite_whiff,
                    good_whiff,
                    avg_whiff,
                    poor_whiff,
                    inverse=False
                )
                attrs['stuff'] = stuff_rating

            # VELOCITY - Direct mapping
            if 'velocity' in metrics:
                velo = metrics['velocity']
                # Map velocity to adjustment (relative to pitcher's baseline)
                # This will be used to adjust pitch-specific velocity
                if pitch_type in ['fastball', '4-seam']:
                    # Fastball is the reference velocity
                    attrs['velocity'] = int(velo)
                else:
                    # Other pitches typically slower
                    # Store absolute velocity, will be used in pitch creation
                    attrs['velocity'] = int(velo)

            # USAGE - How often they throw this pitch
            if 'usage_pct' in metrics:
                usage = metrics['usage_pct']
                # Convert to 0-100 scale for usage rating
                # Higher usage typically means more confidence in the pitch
                attrs['usage'] = int(usage * 100)

            if attrs:
                pitch_attributes[pitch_type] = attrs

        return pitch_attributes

    @staticmethod
    def batter_discipline_to_attributes(
        pitch_metrics: Dict[str, Dict[str, float]]
    ) -> Dict[str, Dict[str, int]]:
        """
        Convert batter pitch-level Statcast metrics to pitch-specific attributes.

        Parameters
        ----------
        pitch_metrics : dict
            Dictionary mapping pitch type to metrics:
            {'fastball': {'chase_pct': 0.22, 'contact_pct': 0.78, ...}, ...}

        Returns
        -------
        dict
            Dictionary mapping pitch type to discipline attributes:
            {'fastball': {'recognition': 75000, 'contact_ability': 80000, ...}, ...}
        """
        pitch_attributes = {}

        for pitch_type, metrics in pitch_metrics.items():
            attrs = {}

            # RECOGNITION/DISCIPLINE - Based on chase rate
            # Lower chase rate = better discipline/recognition
            if 'chase_pct' in metrics:
                chase = metrics['chase_pct']

                # Adjust thresholds based on pitch type
                if pitch_type in ['slider', 'splitter']:
                    # Harder pitches to recognize - higher chase is more acceptable
                    elite_chase = 0.25  # Elite hitters chase 25% on sliders
                    good_chase = 0.32
                    avg_chase = 0.40
                    poor_chase = 0.50
                elif pitch_type in ['curveball', 'changeup']:
                    elite_chase = 0.22
                    good_chase = 0.30
                    avg_chase = 0.38
                    poor_chase = 0.48
                else:  # fastball, 2-seam, cutter
                    elite_chase = 0.15  # Should rarely chase fastballs
                    good_chase = 0.20
                    avg_chase = 0.26
                    poor_chase = 0.34

                # Convert to 0-100,000 scale (recognition rating)
                recognition_rating = StatsConverter.percentile_to_rating(
                    chase,
                    elite_chase,
                    good_chase,
                    avg_chase,
                    poor_chase,
                    inverse=True  # Lower chase is better
                )
                attrs['recognition'] = recognition_rating

            # CONTACT ABILITY - Based on contact rate when swinging
            if 'contact_pct' in metrics:
                contact = metrics['contact_pct']

                # Thresholds based on pitch type
                if pitch_type in ['slider', 'splitter']:
                    # Harder to make contact with
                    elite_contact = 0.70
                    good_contact = 0.63
                    avg_contact = 0.56
                    poor_contact = 0.48
                elif pitch_type in ['curveball', 'changeup']:
                    elite_contact = 0.75
                    good_contact = 0.68
                    avg_contact = 0.60
                    poor_contact = 0.52
                else:  # fastball, 2-seam, cutter
                    elite_contact = 0.85
                    good_contact = 0.79
                    avg_contact = 0.72
                    poor_contact = 0.64

                # Convert to 0-100,000 scale (contact ability rating)
                contact_rating = StatsConverter.percentile_to_rating(
                    contact,
                    elite_contact,
                    good_contact,
                    avg_contact,
                    poor_contact,
                    inverse=False
                )
                attrs['contact_ability'] = contact_rating

            # WHIFF TENDENCY - Based on whiff rate
            if 'whiff_pct' in metrics:
                whiff = metrics['whiff_pct']

                # Thresholds (lower is better for hitters)
                if pitch_type in ['slider', 'splitter']:
                    elite_whiff = 0.22
                    good_whiff = 0.28
                    avg_whiff = 0.35
                    poor_whiff = 0.44
                elif pitch_type in ['curveball', 'changeup']:
                    elite_whiff = 0.18
                    good_whiff = 0.25
                    avg_whiff = 0.32
                    poor_whiff = 0.40
                else:  # fastball, 2-seam, cutter
                    elite_whiff = 0.10
                    good_whiff = 0.14
                    avg_whiff = 0.19
                    poor_whiff = 0.25

                # Convert to 0-100,000 scale (anti-whiff rating)
                anti_whiff_rating = StatsConverter.percentile_to_rating(
                    whiff,
                    elite_whiff,
                    good_whiff,
                    avg_whiff,
                    poor_whiff,
                    inverse=True  # Lower whiff is better
                )
                attrs['whiff_resistance'] = anti_whiff_rating

            if attrs:
                pitch_attributes[pitch_type] = attrs

        return pitch_attributes


if __name__ == "__main__":
    # Test the converter with sample stats
    converter = StatsConverter()

    # Test pitcher conversion
    print("=== Pitcher Stats Conversion ===")
    print("\nElite Pitcher (deGrom-like):")
    pitcher_attrs = converter.mlb_stats_to_pitcher_attributes(
        era=2.15,
        whip=0.90,
        k_per_9=12.5,
        bb_per_9=1.7,
        avg_fastball_velo=98.5,
        innings_pitched=180.0,
        games_pitched=30
    )
    print(f"  Velocity: {pitcher_attrs['velocity']:,} / 100,000")
    print(f"  Command:  {pitcher_attrs['command']:,} / 100,000")
    print(f"  Stamina:  {pitcher_attrs['stamina']:,} / 100,000")
    print(f"  Movement: {pitcher_attrs['movement']:,} / 100,000")

    print("\nAverage Pitcher:")
    pitcher_attrs = converter.mlb_stats_to_pitcher_attributes(
        era=4.20,
        whip=1.28,
        k_per_9=8.5,
        bb_per_9=3.2,
        avg_fastball_velo=92.5,
        innings_pitched=150.0,
        games_pitched=28
    )
    print(f"  Velocity: {pitcher_attrs['velocity']:,} / 100,000")
    print(f"  Command:  {pitcher_attrs['command']:,} / 100,000")
    print(f"  Stamina:  {pitcher_attrs['stamina']:,} / 100,000")
    print(f"  Movement: {pitcher_attrs['movement']:,} / 100,000")

    # Test hitter conversion
    print("\n=== Hitter Stats Conversion ===")
    print("\nElite Hitter (MVP-like):")
    hitter_attrs = converter.mlb_stats_to_hitter_attributes(
        batting_avg=0.310,
        on_base_pct=0.410,
        slugging_pct=0.620,
        home_runs=45,
        strikeouts=120,
        walks=95,
        at_bats=580,
        avg_exit_velo=93.5,
        barrel_pct=14.5,
        sprint_speed=29.0
    )
    print(f"  Contact:    {hitter_attrs['contact']:,} / 100,000")
    print(f"  Power:      {hitter_attrs['power']:,} / 100,000")
    print(f"  Discipline: {hitter_attrs['discipline']:,} / 100,000")
    print(f"  Speed:      {hitter_attrs['speed']:,} / 100,000")

    print("\nAverage Hitter:")
    hitter_attrs = converter.mlb_stats_to_hitter_attributes(
        batting_avg=0.250,
        on_base_pct=0.320,
        slugging_pct=0.410,
        home_runs=18,
        strikeouts=145,
        walks=50,
        at_bats=550,
        avg_exit_velo=87.5,
        barrel_pct=6.0,
        sprint_speed=27.5
    )
    print(f"  Contact:    {hitter_attrs['contact']:,} / 100,000")
    print(f"  Power:      {hitter_attrs['power']:,} / 100,000")
    print(f"  Discipline: {hitter_attrs['discipline']:,} / 100,000")
    print(f"  Speed:      {hitter_attrs['speed']:,} / 100,000")
