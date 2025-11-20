"""
Pitcher Control Module - V2.0 Phase 2B

Replaces hardcoded "intentional ball" probabilities with dynamic control model.
Determines zone targeting probability based on count, situation, and pitcher attributes.

Source: v2_Implementation_Plan.md - Phase 2B
Goal: Achieve 8-9% BB rate independent of K% through realistic pitch location control.
"""

import numpy as np
from typing import Tuple, Optional

from .constants import (
    BB_ZONE_TARGET_NEUTRAL,
    BB_ZONE_TARGET_AHEAD,
    BB_ZONE_TARGET_BEHIND,
    BB_ZONE_TARGET_THREE_BALL,
    BB_NIBBLING_BASE,
    STRIKE_ZONE_WIDTH,
    STRIKE_ZONE_BOTTOM,
    STRIKE_ZONE_TOP,
)


class PitcherControlModule:
    """
    Dynamic pitcher control model for realistic pitch location targeting.

    This replaces the old hardcoded intention probabilities with a more
    nuanced model that accounts for:
    - Count leverage (ahead/behind/neutral)
    - Pitcher control rating
    - Pitcher nibbling tendency (personality)
    - Batter threat level (future enhancement)

    The model works in two stages:
    1. Determine if pitcher targets zone (probability-based)
    2. Generate actual pitch location with command error
    """

    def __init__(self, pitcher):
        """
        Initialize control module for a specific pitcher.

        Parameters
        ----------
        pitcher : Pitcher
            The pitcher whose control to model
        """
        self.pitcher = pitcher

    def determine_zone_target_probability(
        self,
        balls: int,
        strikes: int,
        batter_threat_level: float = 0.5
    ) -> float:
        """
        Calculate probability that pitcher will target the strike zone.

        This probability accounts for:
        - Count situation (ahead/behind/neutral)
        - Pitcher control rating
        - Nibbling tendency (pitcher personality)
        - Batter threat level (optional, for future use)

        Parameters
        ----------
        balls : int
            Current ball count (0-3)
        strikes : int
            Current strike count (0-2)
        batter_threat_level : float, optional
            Measure of batter danger (0-1 scale)
            High threat = pitcher nibbles more
            Default 0.5 (neutral)

        Returns
        -------
        float
            Probability of targeting zone (0.0-1.0)
            Example: 0.65 means 65% chance pitcher aims for zone
        """
        # Determine base zone target based on count leverage
        if balls == 3:
            # 3-ball count: MUST throw strike
            base_zone_prob = BB_ZONE_TARGET_THREE_BALL

        elif strikes == 2:
            # 2-strike count: Can waste pitches
            # Reduce zone targeting to allow chase pitches
            base_zone_prob = 0.45  # Lower than neutral

        elif balls >= 2 and strikes <= 1:
            # Behind in count (2-0, 2-1, 3-0, 3-1): Pitcher nibbles
            base_zone_prob = BB_ZONE_TARGET_BEHIND

        elif strikes >= 1 and balls == 0:
            # Ahead in count (0-1, 0-2): Pitcher attacks
            base_zone_prob = BB_ZONE_TARGET_AHEAD

        else:
            # Neutral count (0-0, 1-0, 1-1, 2-2): Balanced approach
            base_zone_prob = BB_ZONE_TARGET_NEUTRAL

        # Adjust for pitcher control rating
        # High control = more confident targeting zone even in tough counts
        # Low control = forced to target zone more to avoid walks
        control_bias = self.pitcher.attributes.get_control_zone_bias()

        # Control adjustment:
        # Elite control (0.85): Can afford to nibble more when behind
        # Poor control (0.50): Must target zone more to avoid walks
        if balls >= 2:
            # When behind, high control pitchers nibble MORE
            # Poor control pitchers must groove it
            control_adjustment = (control_bias - 0.65) * 0.3
            # Elite (0.85): -0.06 (nibble more)
            # Poor (0.50): +0.045 (target zone more)
        else:
            # When ahead or neutral, high control pitchers attack MORE
            control_adjustment = (control_bias - 0.65) * 0.2
            # Elite (0.85): +0.04 (more aggressive)
            # Poor (0.50): -0.03 (less confident)

        zone_prob = base_zone_prob + control_adjustment

        # Adjust for nibbling tendency (pitcher personality)
        # Get pitcher-specific nibbling tendency
        nibbling_tendency = self.pitcher.attributes.get_nibbling_tendency()

        # High nibbling tendency = reduce zone targeting when not forced
        if balls < 3 and strikes < 2:
            nibbling_adjustment = (nibbling_tendency - BB_NIBBLING_BASE) * 0.15
            zone_prob -= nibbling_adjustment

        # Clamp to valid probability range
        zone_prob = np.clip(zone_prob, 0.10, 0.95)

        return zone_prob

    def generate_pitch_location(
        self,
        balls: int,
        strikes: int,
        pitch_type: str,
        batter_threat_level: float = 0.5
    ) -> Tuple[float, float]:
        """
        Generate actual pitch location using zone targeting and command error.

        Two-stage process:
        1. Decide if targeting zone (probability-based)
        2. Generate location with command error

        Parameters
        ----------
        balls : int
            Current ball count
        strikes : int
            Current strike count
        pitch_type : str
            Type of pitch being thrown
        batter_threat_level : float, optional
            Batter danger level (0-1), default 0.5

        Returns
        -------
        Tuple[float, float]
            Target location as (horizontal_inches, vertical_inches)
            Horizontal: 0 = center, negative = inside, positive = outside
            Vertical: 18" = bottom of zone, 42" = top of zone
        """
        # Determine if pitcher targets zone
        zone_prob = self.determine_zone_target_probability(
            balls, strikes, batter_threat_level
        )

        targets_zone = np.random.random() < zone_prob

        # Generate target location
        if targets_zone:
            return self._generate_zone_target(balls, strikes, pitch_type)
        else:
            return self._generate_out_of_zone_target(balls, strikes, pitch_type)

    def _generate_zone_target(
        self,
        balls: int,
        strikes: int,
        pitch_type: str
    ) -> Tuple[float, float]:
        """
        Generate target location within strike zone.

        Targets different parts of zone based on count:
        - Ahead in count: Attack edges/corners
        - Behind in count: Target center (safe)
        - Neutral: Mix of locations

        Parameters
        ----------
        balls : int
            Ball count
        strikes : int
            Strike count
        pitch_type : str
            Type of pitch

        Returns
        -------
        Tuple[float, float]
            Target location (horizontal_inches, vertical_inches)
        """
        # Strike zone in inches: horizontal ±8.5", vertical 18-42"

        # Determine zone targeting strategy
        if strikes == 0 and balls == 0:
            # First pitch: Down the middle
            target_strategy = 'center'
        elif balls >= 2:
            # Behind: Safe middle-in approach
            target_strategy = 'center'
        elif strikes >= 1:
            # Ahead: Can attack edges/corners
            target_strategy = np.random.choice(['edge', 'corner', 'center'],
                                               p=[0.40, 0.35, 0.25])
        else:
            # Neutral: Mix
            target_strategy = np.random.choice(['center', 'edge', 'corner'],
                                               p=[0.40, 0.35, 0.25])

        if target_strategy == 'center':
            # Target middle of zone
            horizontal = np.random.normal(0, 2.0)
            vertical = np.random.normal(30.0, 3.0)

        elif target_strategy == 'edge':
            # Target edges (not quite corners)
            if np.random.random() < 0.5:
                # Vertical edge (up/down)
                horizontal = np.random.normal(0, 3.0)
                vertical = np.random.choice([22.0, 38.0]) + np.random.normal(0, 2.0)
            else:
                # Horizontal edge (in/out)
                horizontal = np.random.choice([-6.0, 6.0]) + np.random.normal(0, 1.5)
                vertical = np.random.normal(30.0, 4.0)

        else:  # corner
            # Target corners
            horizontal = np.random.choice([-6.5, 6.5]) + np.random.normal(0, 1.0)
            vertical = np.random.choice([22.0, 38.0]) + np.random.normal(0, 1.5)

        return horizontal, vertical

    def _generate_out_of_zone_target(
        self,
        balls: int,
        strikes: int,
        pitch_type: str
    ) -> Tuple[float, float]:
        """
        Generate target location outside strike zone.

        Two categories:
        1. Chase pitches (2-strike counts): Just outside zone
        2. Waste pitches (other counts): Well outside zone

        Parameters
        ----------
        balls : int
            Ball count
        strikes : int
            Strike count
        pitch_type : str
            Type of pitch

        Returns
        -------
        Tuple[float, float]
            Target location (horizontal_inches, vertical_inches)
        """
        if strikes == 2:
            # Chase pitch: Just outside zone (within 3-6 inches)
            chase_location = np.random.choice(['low', 'away', 'high', 'in'],
                                              p=[0.45, 0.30, 0.15, 0.10])

            if chase_location == 'low':
                # Low chase (most common)
                horizontal = np.random.normal(0, 4.0)
                vertical = np.random.uniform(11.0, 17.0)
            elif chase_location == 'away':
                # Outside
                side = np.random.choice([-1, 1])
                horizontal = side * np.random.uniform(9.5, 14.0)
                vertical = np.random.uniform(22.0, 38.0)
            elif chase_location == 'high':
                # High
                horizontal = np.random.normal(0, 4.0)
                vertical = np.random.uniform(43.0, 48.0)
            else:  # in
                # Inside (rare)
                side = np.random.choice([-1, 1])
                horizontal = side * np.random.uniform(9.5, 13.0)
                vertical = np.random.uniform(24.0, 36.0)

        else:
            # Waste pitch: Well outside zone
            waste_location = np.random.choice(['low', 'away'], p=[0.60, 0.40])

            if waste_location == 'low':
                horizontal = np.random.normal(0, 5.0)
                vertical = np.random.uniform(8.0, 15.0)
            else:  # away
                side = np.random.choice([-1, 1])
                horizontal = side * np.random.uniform(13.0, 19.0)
                vertical = np.random.uniform(24.0, 36.0)

        return horizontal, vertical
