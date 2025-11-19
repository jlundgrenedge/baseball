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
