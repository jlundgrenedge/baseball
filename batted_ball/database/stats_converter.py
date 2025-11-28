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
            Rating from 0-100,000 (ALWAYS clipped to this range)
        """
        if inverse:
            # Lower is better - flip the scale
            if value <= elite:
                # Elite range (90k-100k)
                rating = 90000 + 10000 * (elite - value) / max(elite * 0.2, 0.5)
            elif value <= good:
                # Good range (70k-90k)
                t = (value - elite) / (good - elite)
                rating = 90000 - 20000 * t
            elif value <= avg:
                # Average range (50k-70k)
                t = (value - good) / (avg - good)
                rating = 70000 - 20000 * t
            elif value <= poor:
                # Below average (30k-50k)
                t = (value - avg) / (poor - avg)
                rating = 50000 - 20000 * t
            else:
                # Poor range (0-30k)
                t = min((value - poor) / (poor * 0.5), 1.0)
                rating = 30000 - 30000 * t
        else:
            # Higher is better
            if value >= elite:
                # Elite range (90k-100k)
                rating = 90000 + 10000 * (value - elite) / max(elite * 0.1, 0.05)
            elif value >= good:
                # Good range (70k-90k)
                t = (value - good) / (elite - good)
                rating = 70000 + 20000 * t
            elif value >= avg:
                # Average range (50k-70k)
                t = (value - avg) / (good - avg)
                rating = 50000 + 20000 * t
            elif value >= poor:
                # Below average (30k-50k)
                t = (value - poor) / (avg - poor)
                rating = 30000 + 20000 * t
            else:
                # Poor range (0-30k)
                t = max(value / poor, 0.0)
                rating = 30000 * t

        # CRITICAL: Clip to valid 0-100,000 range
        return int(np.clip(rating, 0, 100000))

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
        Convert MLB hitter statistics to v2 game attributes (Phase 2A + 2C).

        Includes all v1 attributes PLUS v2 additions:
        - VISION: Contact frequency independent of power (from K%)
        - ATTACK_ANGLE_CONTROL: Launch angle tendency for HR generation (from HR rate, SLG, barrel%)

        Parameters
        ----------
        Same as mlb_stats_to_hitter_attributes

        Returns
        -------
        dict
            Dictionary with v1 keys (contact, power, discipline, speed)
            PLUS v2 keys (vision, attack_angle_control)
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

        # Add v2 attribute: ATTACK_ANGLE_CONTROL (Phase 2C - CRITICAL for HR generation)
        # Controls launch angle tendency - higher = more fly balls = more HR potential
        # Inferred from HR rate, SLG, and barrel% since launch angle data not always available
        #
        # Target ranges (matching generic team creation in attributes.py):
        # - Power hitters (high HR, high SLG): 72k-88k → mean launch angle 18-24°
        # - Balanced hitters (moderate HR/SLG): 58k-75k → mean launch angle 13-19°
        # - Contact/groundball hitters (low HR/SLG): 45k-60k → mean launch angle 9-15°
        attrs['attack_angle_control'] = cls._calculate_attack_angle_control(
            home_runs=home_runs,
            at_bats=at_bats,
            slugging_pct=slugging_pct,
            barrel_pct=barrel_pct,
            avg_exit_velo=avg_exit_velo
        )

        return attrs

    @classmethod
    def _calculate_attack_angle_control(
        cls,
        home_runs: Optional[int] = None,
        at_bats: Optional[int] = None,
        slugging_pct: Optional[float] = None,
        barrel_pct: Optional[float] = None,
        avg_exit_velo: Optional[float] = None
    ) -> int:
        """
        Calculate ATTACK_ANGLE_CONTROL from available MLB stats.

        Since launch angle data may not always be available, we infer it from:
        - HR rate (most indicative of elevated launch tendency)
        - Slugging percentage (correlates with extra base hits / fly ball success)
        - Barrel % (optimal EV+LA combo frequency)
        - Exit velocity (power indicator)

        FIX 2025-11-25: Boosted output ranges to match generic team creation.
        Previous scaling was too conservative, producing 50-68k instead of 58-88k.

        Target ranges to match generic team creation:
        - Power hitters: 75k-92k (HR rate > 5%, SLG > 0.500) - for ~18-24° mean LA
        - Balanced hitters: 62k-78k (HR rate 2-5%, SLG 0.400-0.500) - for ~14-18° mean LA
        - Contact/GB hitters: 50k-65k (HR rate < 2%, SLG < 0.400) - for ~10-14° mean LA

        Returns
        -------
        int
            ATTACK_ANGLE_CONTROL rating (0-100k scale)
        """
        attack_angle_scores = []

        # 1. HR rate - most direct indicator of elevated launch tendency
        if home_runs is not None and at_bats is not None and at_bats > 0:
            hr_per_ab = home_runs / at_bats
            # Thresholds based on MLB data:
            # Elite power (40+ HR in 600 AB): >0.065 HR/AB
            # Good power (30 HR): ~0.050
            # Average power (18-20 HR): ~0.033
            # Low power (<12 HR): <0.020
            hr_score = cls.percentile_to_rating(
                hr_per_ab,
                0.065,  # Elite HR rate
                0.050,  # Good
                0.033,  # Average
                0.020,  # Poor
                inverse=False
            )
            attack_angle_scores.append(hr_score * 1.5)  # Weight HR most heavily

        # 2. Slugging percentage - correlates with launch success
        if slugging_pct is not None:
            slg_score = cls.percentile_to_rating(
                slugging_pct,
                0.550,  # Elite SLG
                0.470,  # Good
                0.410,  # Average
                0.360,  # Poor
                inverse=False
            )
            attack_angle_scores.append(slg_score)

        # 3. Barrel % - optimal EV+LA combo frequency (direct measure of good fly balls)
        if barrel_pct is not None:
            barrel_score = cls.percentile_to_rating(
                barrel_pct,
                cls.HITTER_BARREL_ELITE,   # 12% = elite
                cls.HITTER_BARREL_GOOD,    # 8%
                cls.HITTER_BARREL_AVG,     # 6%
                cls.HITTER_BARREL_POOR,    # 4%
                inverse=False
            )
            attack_angle_scores.append(barrel_score * 1.2)  # Weight barrel highly

        # 4. Exit velocity as tie-breaker (power hitters tend to hit more fly balls)
        if avg_exit_velo is not None:
            ev_score = cls.percentile_to_rating(
                avg_exit_velo,
                cls.HITTER_EV_ELITE,   # 92 mph
                cls.HITTER_EV_GOOD,    # 89.5
                cls.HITTER_EV_AVG,     # 87.5
                cls.HITTER_EV_POOR,    # 85
                inverse=False
            )
            attack_angle_scores.append(ev_score * 0.5)  # Lower weight

        if attack_angle_scores:
            # Calculate weighted average
            total_weight = 0
            weighted_sum = 0
            weights = [1.5, 1.0, 1.2, 0.5]  # HR, SLG, Barrel, EV
            for i, score in enumerate(attack_angle_scores):
                w = weights[i] if i < len(weights) else 1.0
                weighted_sum += score * w
                total_weight += w
            raw_score = weighted_sum / total_weight

            # FIX 2025-11-25: BOOSTED scaling to match generic team creation
            # Generic teams produce: power=72-88k, balanced=58-75k, GB=45-60k
            # Previous scaling was too conservative, clipping at 88k max
            #
            # New mapping: more aggressive boost to match generic teams
            # - Raw 85k+ → 80k-95k (elite power, fly ball hitters)
            # - Raw 65k-85k → 68k-80k (good power, balanced hitters)
            # - Raw 45k-65k → 58k-68k (average hitters)
            # - Raw <45k → 50k-58k (groundball hitters)
            if raw_score >= 85000:
                # Elite power hitter → high attack angle (80-95k)
                attack_angle = 80000 + int((raw_score - 85000) / 15000 * 15000)
            elif raw_score >= 65000:
                # Good power/balanced hitter (68-80k)
                attack_angle = 68000 + int((raw_score - 65000) / 20000 * 12000)
            elif raw_score >= 45000:
                # Average hitter (58-68k)
                attack_angle = 58000 + int((raw_score - 45000) / 20000 * 10000)
            else:
                # Contact/groundball hitter (50-58k)
                attack_angle = 50000 + int(raw_score / 45000 * 8000)

            return int(np.clip(attack_angle, 50000, 95000))
        else:
            # No data - use balanced default that matches generic teams
            return 65000  # Moderate-high attack angle for MLB average

    # Jump metric ranges (Statcast "feet in right direction in first 3 seconds")
    # Positive = towards ball, negative = wrong direction
    FIELDER_JUMP_ELITE = 4.0      # +4 ft = elite first step
    FIELDER_JUMP_GOOD = 2.0       # +2 ft = good
    FIELDER_JUMP_AVG = 0.0        # 0 ft = average
    FIELDER_JUMP_POOR = -3.0      # -3 ft = poor first step/wrong direction
    
    # Jump COMPONENT ranges (each is feet vs average in its time window)
    # Reaction: feet covered in first 1.5 seconds (first step quality)
    FIELDER_REACTION_FT_ELITE = 2.5   # +2.5 ft = elite first step
    FIELDER_REACTION_FT_GOOD = 1.0    # +1 ft = good
    FIELDER_REACTION_FT_AVG = 0.0     # 0 ft = average
    FIELDER_REACTION_FT_POOR = -2.0   # -2 ft = poor first step
    
    # Burst: feet covered in second 1.5 seconds (acceleration phase)
    FIELDER_BURST_FT_ELITE = 2.5      # +2.5 ft = explosive acceleration
    FIELDER_BURST_FT_GOOD = 1.0       # +1 ft = good acceleration
    FIELDER_BURST_FT_AVG = 0.0        # 0 ft = average
    FIELDER_BURST_FT_POOR = -2.0      # -2 ft = slow acceleration
    
    # Route: feet lost/gained from direction (route efficiency component)
    FIELDER_ROUTE_FT_ELITE = 1.5      # +1.5 ft = excellent routes (rarely wrong direction)
    FIELDER_ROUTE_FT_GOOD = 0.5       # +0.5 ft = good routes
    FIELDER_ROUTE_FT_AVG = 0.0        # 0 ft = average
    FIELDER_ROUTE_FT_POOR = -2.0      # -2 ft = poor routes (wrong direction)
    
    # Directional OAA thresholds (from Baseball Savant directional_outs_above_average.csv)
    # These measure ability to make plays in specific directions relative to starting position
    # Back OAA: Ability to go back on deep balls (outfielders) or away from plate (infielders)
    FIELDER_BACK_OAA_ELITE = 8.0      # +8 OAA going back = elite range backward
    FIELDER_BACK_OAA_GOOD = 3.0       # +3 OAA = good
    FIELDER_BACK_OAA_AVG = 0.0        # 0 = average
    FIELDER_BACK_OAA_POOR = -5.0      # -5 OAA = struggles going back
    
    # In OAA: Ability to come in on shallow balls (outfielders) or charge (infielders)
    FIELDER_IN_OAA_ELITE = 6.0        # +6 OAA coming in = elite charging ability
    FIELDER_IN_OAA_GOOD = 2.0         # +2 OAA = good
    FIELDER_IN_OAA_AVG = 0.0          # 0 = average
    FIELDER_IN_OAA_POOR = -4.0        # -4 OAA = struggles coming in

    # Catch Probability: 5-star plays (hardest, 0-25% expected catch rate)
    # Elite outfielders like Pete Crow-Armstrong convert 50%+ of these
    FIELDER_CATCH_5STAR_ELITE = 50.0  # 50%+ = elite (Crow-Armstrong: 59.4%)
    FIELDER_CATCH_5STAR_GOOD = 35.0   # 35%+ = good  
    FIELDER_CATCH_5STAR_AVG = 20.0    # 20% = average (roughly at expectation)
    FIELDER_CATCH_5STAR_POOR = 10.0   # 10% = poor

    # Catch Probability: 3-4 star plays (difficult, 25-75% expected catch rate)
    # These differentiate good from great fielders
    FIELDER_CATCH_34STAR_ELITE = 85.0   # 85%+ = elite  
    FIELDER_CATCH_34STAR_GOOD = 75.0    # 75%+ = good
    FIELDER_CATCH_34STAR_AVG = 65.0     # 65% = average
    FIELDER_CATCH_34STAR_POOR = 50.0    # 50% = poor

    @classmethod
    def mlb_stats_to_defensive_attributes(
        cls,
        position: str,
        oaa: Optional[float] = None,
        sprint_speed: Optional[float] = None,
        arm_strength_mph: Optional[float] = None,
        drs: Optional[float] = None,
        jump: Optional[float] = None,
        jump_reaction: Optional[float] = None,
        jump_burst: Optional[float] = None,
        jump_route: Optional[float] = None,
        fielding_pct: Optional[float] = None,
        back_oaa: Optional[float] = None,
        in_oaa: Optional[float] = None,
        catch_5star_pct: Optional[float] = None,
        catch_34star_pct: Optional[float] = None
    ) -> Dict[str, int]:
        """
        Convert MLB defensive metrics to v2 game attributes (CRITICAL for BABIP tuning).

        Maps Statcast and FanGraphs defensive metrics to FielderAttributes (0-100k).

        Strategy:
        - Sprint speed → TOP_SPRINT_SPEED (direct mapping)
        - OAA + Jump Reaction → REACTION_TIME (better first step = faster reaction)
        - OAA + DRS + Jump Route → ROUTE_EFFICIENCY (better routes = more efficient)
        - Jump Burst → BURST (acceleration in second 1.5s)
        - Arm strength → ARM_STRENGTH (direct mapping by position)
        - Fielding % → FIELDING_SECURE (fewer errors = more secure)
        - OAA residual → ARM_ACCURACY (defense not explained by speed/range)
        - Jump → JUMP (composite metric, for legacy compatibility)
        - Back OAA → RANGE_BACK (ability to go back on balls)
        - In OAA → RANGE_IN (ability to come in on balls)
        - Catch Prob 5-star → CATCH_ELITE (elite plays, 0-25% expected)
        - Catch Prob 3-4 star → CATCH_DIFFICULT (difficult plays, 25-75% expected)

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
            Outfielder first step efficiency in feet (Statcast)
            Represents "feet covered in right direction in first 3 seconds"
            Typical range: -4 to +6 ft, where positive = towards ball
        fielding_pct : float, optional
            Traditional fielding percentage
        back_oaa : float, optional
            Directional OAA going back (sum of back_left, back, back_right slices)
        in_oaa : float, optional
            Directional OAA coming in (sum of in_left, in, in_right slices)
        catch_5star_pct : float, optional
            Catch success rate on 5-star plays (0-25% expected catch rate)
            Elite fielders convert 50%+ of these (e.g., Crow-Armstrong: 59.4%)
        catch_34star_pct : float, optional
            Catch success rate on 3-4 star plays (25-75% expected catch rate)
            Differentiates good from great fielders

        Returns
        -------
        dict
            Dictionary with defensive attribute keys (all 0-100k scale):
            - reaction_time, top_sprint_speed, route_efficiency,
              arm_strength, arm_accuracy, fielding_secure, jump,
              range_back, range_in, catch_elite, catch_difficult
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

        # 2. REACTION_TIME - From OAA (higher OAA = better fielder = faster reaction)
        # 
        # FIX 2025-11-25: Was using inverse=True which caused ALL players to get 100k.
        # The bug: inverse=True means "lower values are better" (like ERA), but for OAA
        # higher values are better. Also was scaling OAA by 0.6 but comparing against
        # unscaled thresholds.
        #
        # REACTION_TIME attribute: higher = faster reaction (100k = 0.00s, 0 = 0.30s)
        # OAA metric: higher = better defender
        # Therefore: inverse=False (higher OAA → higher attribute → faster reaction)
        #
        # 2025-11-26: Prefer Jump Reaction component when available (more direct measure)
        if jump_reaction is not None and position in ['LF', 'CF', 'RF']:
            # Outfielders with jump reaction data - direct measure of first 1.5s performance
            attrs['reaction_time'] = cls.percentile_to_rating(
                jump_reaction,
                cls.FIELDER_REACTION_FT_ELITE,  # +2.5 ft = elite first step
                cls.FIELDER_REACTION_FT_GOOD,   # +1 ft = good
                cls.FIELDER_REACTION_FT_AVG,    # 0 ft = average
                cls.FIELDER_REACTION_FT_POOR,   # -2 ft = poor
                inverse=False
            )
        elif oaa is not None:
            attrs['reaction_time'] = cls.percentile_to_rating(
                oaa,  # Use OAA directly, not scaled
                cls.FIELDER_OAA_ELITE,    # +8 OAA = elite reaction (90k-100k)
                cls.FIELDER_OAA_GOOD,     # +3 OAA = good (70k-90k)
                cls.FIELDER_OAA_AVG,      # 0 OAA = average (50k-70k)
                cls.FIELDER_OAA_POOR,     # -5 OAA = poor (30k-50k)
                inverse=False  # Higher OAA = higher rating = faster reaction
            )
        elif jump is not None and position in ['LF', 'CF', 'RF']:
            # Outfielders: use composite jump metric if OAA not available
            # Jump is typically 0-5 ft range, scale to match OAA thresholds
            jump_as_oaa = jump * 2.0  # Rough conversion: 4 ft jump ≈ +8 OAA equivalent
            attrs['reaction_time'] = cls.percentile_to_rating(
                jump_as_oaa,
                cls.FIELDER_OAA_ELITE,
                cls.FIELDER_OAA_GOOD,
                cls.FIELDER_OAA_AVG,
                cls.FIELDER_OAA_POOR,
                inverse=False
            )
        else:
            attrs['reaction_time'] = 50000  # Default average

        # 3. ROUTE_EFFICIENCY - From OAA + DRS composite, OR Jump Route component
        # 2025-11-26: Prefer Jump Route component for outfielders (direct route measure)
        if jump_route is not None and position in ['LF', 'CF', 'RF']:
            # Outfielders with jump route data - direct measure of direction efficiency
            attrs['route_efficiency'] = cls.percentile_to_rating(
                jump_route,
                cls.FIELDER_ROUTE_FT_ELITE,  # +1.5 ft = excellent routes
                cls.FIELDER_ROUTE_FT_GOOD,   # +0.5 ft = good routes
                cls.FIELDER_ROUTE_FT_AVG,    # 0 ft = average
                cls.FIELDER_ROUTE_FT_POOR,   # -2 ft = poor routes
                inverse=False
            )
        else:
            # Fall back to OAA + DRS composite
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
            # FIX 2025-11-25: When arm_strength_mph is not available, derive from OAA
            # using a continuous scale instead of just 3 buckets (which gave everyone 50k or 70k).
            #
            # Use OAA to estimate arm strength on the 0-100k scale directly.
            # OAA correlates somewhat with arm (good fielders often have good arms),
            # but add some variance since arm and range are somewhat independent.
            #
            # Mapping: OAA -> arm_strength attribute
            # +10 OAA -> ~80k (very good arm)
            # +5 OAA -> ~65k (above average)
            # 0 OAA -> ~50k (average)
            # -5 OAA -> ~35k (below average)
            # -10 OAA -> ~20k (poor arm)
            if oaa is not None:
                # Scale OAA to arm strength: 50k base + 3k per OAA point
                # Capped at 20k-80k range (leave room for actual arm data to exceed)
                arm_from_oaa = 50000 + int(oaa * 3000)
                attrs['arm_strength'] = int(np.clip(arm_from_oaa, 20000, 80000))
            elif drs is not None:
                # DRS as fallback (similar scale)
                arm_from_drs = 50000 + int(drs * 2500)
                attrs['arm_strength'] = int(np.clip(arm_from_drs, 20000, 80000))
            else:
                # No defensive data - use average
                attrs['arm_strength'] = 50000

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

        # 7. BURST - Acceleration in second 1.5 seconds (from Jump Burst component)
        # 2025-11-26: New attribute mapping Statcast Burst component
        if jump_burst is not None and position in ['LF', 'CF', 'RF']:
            # Outfielders with burst data - direct measure of acceleration phase
            attrs['burst'] = cls.percentile_to_rating(
                jump_burst,
                cls.FIELDER_BURST_FT_ELITE,  # +2.5 ft = explosive acceleration
                cls.FIELDER_BURST_FT_GOOD,   # +1 ft = good
                cls.FIELDER_BURST_FT_AVG,    # 0 ft = average
                cls.FIELDER_BURST_FT_POOR,   # -2 ft = poor
                inverse=False
            )
        elif position in ['LF', 'CF', 'RF']:
            # Outfielders without burst data - derive from OAA or sprint speed
            if sprint_speed is not None:
                # Faster players tend to have better burst
                # Estimate: 29.5 ft/s → ~75k, 27.5 ft/s → ~50k, 26 ft/s → ~30k
                burst_from_speed = int((sprint_speed - 27.5) * 12500 + 50000)
                attrs['burst'] = int(np.clip(burst_from_speed, 20000, 85000))
            elif oaa is not None:
                # Use OAA as proxy
                burst_from_oaa = 50000 + int(oaa * 2500)
                attrs['burst'] = int(np.clip(burst_from_oaa, 20000, 85000))
            else:
                attrs['burst'] = 50000
        else:
            # Infielders: burst less measured, default to average
            attrs['burst'] = 50000

        # 8. JUMP - Direct mapping of Statcast jump metric (feet in right direction in 3s)
        # This is a FIRST-CLASS attribute that models reaction + burst + route direction
        # separately from pure reaction time or route efficiency
        if jump is not None:
            # Jump metric: typical range -4 to +6 ft
            # Positive = moved towards ball in first 3 seconds
            # Negative = initially wrong direction
            attrs['jump'] = cls.percentile_to_rating(
                jump,
                cls.FIELDER_JUMP_ELITE,   # +4 ft = elite first step
                cls.FIELDER_JUMP_GOOD,    # +2 ft = good
                cls.FIELDER_JUMP_AVG,     # 0 ft = average
                cls.FIELDER_JUMP_POOR,    # -3 ft = poor
                inverse=False  # Higher jump is better
            )
        elif position in ['LF', 'CF', 'RF']:
            # Outfielders: derive from OAA if available
            # Good outfielders typically have good jumps
            if oaa is not None:
                # Scale OAA to jump rating: higher OAA = better jump
                # +8 OAA → ~75k, 0 OAA → ~50k, -5 OAA → ~30k
                jump_from_oaa = 50000 + int(oaa * 3125)  # ±25k swing over ±8 OAA range
                attrs['jump'] = int(np.clip(jump_from_oaa, 15000, 90000))
            else:
                attrs['jump'] = 50000  # Default average for outfielders
        else:
            # Infielders: jump is less critical, default to average
            # But if we have OAA, use a smaller influence
            if oaa is not None:
                jump_from_oaa = 50000 + int(oaa * 2000)  # Smaller influence for infielders
                attrs['jump'] = int(np.clip(jump_from_oaa, 25000, 80000))
            else:
                attrs['jump'] = 50000

        # 9. RANGE_BACK - Ability to go back on balls (from directional OAA)
        # 2025-11-26: New attribute for player-specific backward movement ability
        if back_oaa is not None:
            attrs['range_back'] = cls.percentile_to_rating(
                back_oaa,
                cls.FIELDER_BACK_OAA_ELITE,  # +8 OAA back = elite
                cls.FIELDER_BACK_OAA_GOOD,   # +3 OAA = good
                cls.FIELDER_BACK_OAA_AVG,    # 0 = average
                cls.FIELDER_BACK_OAA_POOR,   # -5 OAA = poor
                inverse=False  # Higher back_oaa is better
            )
        elif position in ['LF', 'CF', 'RF']:
            # Outfielders: derive from OAA if available (back range is important)
            if oaa is not None:
                # Estimate: better overall fielders tend to be better going back
                range_back_from_oaa = 50000 + int(oaa * 2500)
                attrs['range_back'] = int(np.clip(range_back_from_oaa, 25000, 80000))
            else:
                attrs['range_back'] = 50000
        else:
            # Infielders: going back is less critical, default closer to average
            if oaa is not None:
                range_back_from_oaa = 50000 + int(oaa * 1500)
                attrs['range_back'] = int(np.clip(range_back_from_oaa, 30000, 75000))
            else:
                attrs['range_back'] = 50000

        # 10. RANGE_IN - Ability to come in on balls (from directional OAA)
        # 2025-11-26: New attribute for player-specific forward/charging movement
        if in_oaa is not None:
            attrs['range_in'] = cls.percentile_to_rating(
                in_oaa,
                cls.FIELDER_IN_OAA_ELITE,  # +6 OAA in = elite
                cls.FIELDER_IN_OAA_GOOD,   # +2 OAA = good
                cls.FIELDER_IN_OAA_AVG,    # 0 = average
                cls.FIELDER_IN_OAA_POOR,   # -4 OAA = poor
                inverse=False  # Higher in_oaa is better
            )
        elif position in ['LF', 'CF', 'RF']:
            # Outfielders: derive from OAA + sprint speed
            if oaa is not None:
                range_in_from_oaa = 50000 + int(oaa * 2000)
                attrs['range_in'] = int(np.clip(range_in_from_oaa, 25000, 80000))
            elif sprint_speed is not None:
                # Faster runners tend to charge better
                range_in_from_speed = int((sprint_speed - 27.5) * 10000 + 50000)
                attrs['range_in'] = int(np.clip(range_in_from_speed, 30000, 75000))
            else:
                attrs['range_in'] = 50000
        else:
            # Infielders: charging ability is important
            if oaa is not None:
                range_in_from_oaa = 50000 + int(oaa * 2500)
                attrs['range_in'] = int(np.clip(range_in_from_oaa, 25000, 85000))
            else:
                attrs['range_in'] = 50000

        # 11. CATCH_ELITE - Ability to make 5-star catches (0-25% expected catch rate)
        # 2025-11-26: New attribute for player-specific elite catch ability
        # Crow-Armstrong converts 59.4% of 5-star plays (elite is 50%+)
        if catch_5star_pct is not None and position in ['LF', 'CF', 'RF']:
            attrs['catch_elite'] = cls.percentile_to_rating(
                catch_5star_pct,
                cls.FIELDER_CATCH_5STAR_ELITE,  # 50% = elite
                cls.FIELDER_CATCH_5STAR_GOOD,   # 35% = good
                cls.FIELDER_CATCH_5STAR_AVG,    # 20% = average
                cls.FIELDER_CATCH_5STAR_POOR,   # 10% = poor
                inverse=False  # Higher catch % is better
            )
        elif position in ['LF', 'CF', 'RF']:
            # Outfielders without catch probability data - derive from OAA
            # Elite fielders (high OAA) tend to make difficult catches
            if oaa is not None:
                # +8 OAA → ~75k, 0 OAA → ~50k, -5 OAA → ~30k
                catch_elite_from_oaa = 50000 + int(oaa * 3125)
                attrs['catch_elite'] = int(np.clip(catch_elite_from_oaa, 20000, 85000))
            else:
                attrs['catch_elite'] = 50000
        else:
            # Infielders: elite catches less common, use OAA influence
            if oaa is not None:
                catch_elite_from_oaa = 50000 + int(oaa * 2000)
                attrs['catch_elite'] = int(np.clip(catch_elite_from_oaa, 30000, 75000))
            else:
                attrs['catch_elite'] = 50000

        # 12. CATCH_DIFFICULT - Ability to make 3-4 star catches (25-75% expected)
        # 2025-11-26: New attribute for player-specific difficult catch ability
        if catch_34star_pct is not None and position in ['LF', 'CF', 'RF']:
            attrs['catch_difficult'] = cls.percentile_to_rating(
                catch_34star_pct,
                cls.FIELDER_CATCH_34STAR_ELITE,  # 85% = elite
                cls.FIELDER_CATCH_34STAR_GOOD,   # 75% = good
                cls.FIELDER_CATCH_34STAR_AVG,    # 65% = average
                cls.FIELDER_CATCH_34STAR_POOR,   # 50% = poor
                inverse=False  # Higher catch % is better
            )
        elif position in ['LF', 'CF', 'RF']:
            # Outfielders without catch probability data - derive from OAA
            if oaa is not None:
                # Similar scale but tighter since 3-4 star has higher baseline
                catch_diff_from_oaa = 50000 + int(oaa * 2500)
                attrs['catch_difficult'] = int(np.clip(catch_diff_from_oaa, 25000, 80000))
            else:
                attrs['catch_difficult'] = 50000
        else:
            # Infielders: derive from OAA
            if oaa is not None:
                catch_diff_from_oaa = 50000 + int(oaa * 2000)
                attrs['catch_difficult'] = int(np.clip(catch_diff_from_oaa, 30000, 75000))
            else:
                attrs['catch_difficult'] = 50000

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
