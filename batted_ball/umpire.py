"""
Umpire Model - V2.0 Phase 2B

Probabilistic ball/strike calls on borderline pitches.
Simulates umpire inconsistency and catcher framing impact.

Source: v2_Implementation_Plan.md - Phase 2B
Goal: Add realistic variability to strike zone enforcement, affecting BB% independently of K%.
"""

import numpy as np
from typing import Tuple, Optional

from .constants import (
    BB_UMPIRE_BORDERLINE_BIAS,
    BB_BORDERLINE_DISTANCE_INCHES,
    BB_FRAMING_BONUS_MAX,
    STRIKE_ZONE_WIDTH,
    STRIKE_ZONE_BOTTOM,
    STRIKE_ZONE_TOP,
)


class UmpireModel:
    """
    Umpire model for probabilistic ball/strike calls.

    Real MLB umpires are not perfect machines. They have:
    - Inconsistency on borderline pitches
    - Tendency to favor/penalize certain pitchers
    - Susceptibility to catcher framing
    - Strike zone that varies slightly game-to-game

    This model simulates realistic umpire behavior while maintaining
    overall strike zone accuracy.

    Key features:
    1. Definitive calls on clear strikes/balls (>2" from edge)
    2. Probabilistic calls on borderline pitches (within 2" of edge)
    3. Catcher framing influence on borderline pitches
    4. Count-based bias (optional, future enhancement)
    """

    def __init__(
        self,
        borderline_bias: float = BB_UMPIRE_BORDERLINE_BIAS,
        consistency: float = 1.0
    ):
        """
        Initialize umpire model.

        Parameters
        ----------
        borderline_bias : float, optional
            Base strike probability on borderline pitches (0-1)
            0.50 = neutral, 0.55 = pitcher-friendly, 0.45 = batter-friendly
            Default from constants
        consistency : float, optional
            Umpire consistency (0-1 scale)
            1.0 = perfectly consistent, 0.5 = highly variable
            Affects how much randomness in borderline calls
            Default 1.0 (standard umpire)
        """
        self.borderline_bias = borderline_bias
        self.consistency = consistency

        # Calculate strike zone boundaries (in inches)
        # Horizontal: ±8.5" from center (17" wide zone)
        # Vertical: 18" (bottom) to 42" (top) - 24" tall zone
        self.zone_left = -STRIKE_ZONE_WIDTH * 6.0  # -8.5"
        self.zone_right = STRIKE_ZONE_WIDTH * 6.0  # +8.5"
        self.zone_bottom = STRIKE_ZONE_BOTTOM * 12.0  # 18"
        self.zone_top = STRIKE_ZONE_TOP * 12.0  # 42"

    def call_pitch(
        self,
        horizontal_inches: float,
        vertical_inches: float,
        framing_bonus: float = 0.0
    ) -> str:
        """
        Determine ball or strike call for a pitch.

        Three-zone system:
        1. Clear strike (>2" inside zone): Always strike
        2. Borderline (within 2" of edge): Probabilistic
        3. Clear ball (>2" outside zone): Always ball

        Parameters
        ----------
        horizontal_inches : float
            Horizontal pitch location in inches from center
            Negative = inside, positive = outside
        vertical_inches : float
            Vertical pitch location in inches above ground
        framing_bonus : float, optional
            Catcher framing bonus (0.0 to BB_FRAMING_BONUS_MAX)
            Adds to strike probability on borderline pitches
            Default 0.0 (no framing bonus)

        Returns
        -------
        str
            Either 'strike' or 'ball'
        """
        # Check if pitch is clearly in or out of zone
        is_clearly_in_zone = self._is_clearly_in_zone(
            horizontal_inches, vertical_inches
        )
        is_clearly_out_of_zone = self._is_clearly_out_of_zone(
            horizontal_inches, vertical_inches
        )

        # Definitive calls
        if is_clearly_in_zone:
            return 'strike'
        if is_clearly_out_of_zone:
            return 'ball'

        # Borderline pitch: Probabilistic call
        return self._call_borderline_pitch(
            horizontal_inches, vertical_inches, framing_bonus
        )

    def _is_clearly_in_zone(
        self,
        horizontal: float,
        vertical: float
    ) -> bool:
        """
        Check if pitch is clearly inside strike zone.

        "Clearly" means >2" away from all edges.

        Parameters
        ----------
        horizontal : float
            Horizontal location (inches from center)
        vertical : float
            Vertical location (inches above ground)

        Returns
        -------
        bool
            True if clearly inside zone
        """
        borderline = BB_BORDERLINE_DISTANCE_INCHES

        # Must be inside all four boundaries by at least borderline distance
        horizontal_clear = (
            horizontal > (self.zone_left + borderline) and
            horizontal < (self.zone_right - borderline)
        )
        vertical_clear = (
            vertical > (self.zone_bottom + borderline) and
            vertical < (self.zone_top - borderline)
        )

        return horizontal_clear and vertical_clear

    def _is_clearly_out_of_zone(
        self,
        horizontal: float,
        vertical: float
    ) -> bool:
        """
        Check if pitch is clearly outside strike zone.

        "Clearly" means >2" away from nearest edge.

        Parameters
        ----------
        horizontal : float
            Horizontal location (inches from center)
        vertical : float
            Vertical location (inches above ground)

        Returns
        -------
        bool
            True if clearly outside zone
        """
        borderline = BB_BORDERLINE_DISTANCE_INCHES

        # Check if outside any boundary by more than borderline distance
        too_far_left = horizontal < (self.zone_left - borderline)
        too_far_right = horizontal > (self.zone_right + borderline)
        too_low = vertical < (self.zone_bottom - borderline)
        too_high = vertical > (self.zone_top + borderline)

        return too_far_left or too_far_right or too_low or too_high

    def _call_borderline_pitch(
        self,
        horizontal: float,
        vertical: float,
        framing_bonus: float
    ) -> str:
        """
        Make probabilistic call on borderline pitch.

        Strike probability based on:
        1. How close to zone edge (closer = higher probability)
        2. Umpire borderline bias
        3. Catcher framing bonus
        4. Umpire consistency

        Parameters
        ----------
        horizontal : float
            Horizontal location
        vertical : float
            Vertical location
        framing_bonus : float
            Catcher framing bonus

        Returns
        -------
        str
            'strike' or 'ball'
        """
        # Calculate distance from zone edge
        # Negative = inside zone, positive = outside zone
        distance_from_zone = self._calculate_distance_from_zone(
            horizontal, vertical
        )

        # Base strike probability
        # Inside zone: Higher probability
        # Outside zone: Lower probability
        # Right on edge: Use borderline_bias
        if distance_from_zone <= 0:
            # Inside zone: Start at 100%, decrease as approach edge
            # At edge (0): Use borderline_bias
            # Deep inside (-2"): 100% (but this is "clearly in")
            base_prob = self.borderline_bias + (
                (1.0 - self.borderline_bias) *
                (-distance_from_zone / BB_BORDERLINE_DISTANCE_INCHES)
            )
        else:
            # Outside zone: Start at borderline_bias, decrease as move away
            # At edge (0): Use borderline_bias
            # Far outside (+2"): ~0% (but this is "clearly out")
            base_prob = self.borderline_bias * (
                1.0 - (distance_from_zone / BB_BORDERLINE_DISTANCE_INCHES)
            )

        # Apply framing bonus
        strike_probability = base_prob + framing_bonus

        # Apply consistency factor
        # Perfect consistency (1.0): Use exact probability
        # Lower consistency: Add random noise
        if self.consistency < 1.0:
            noise_magnitude = (1.0 - self.consistency) * 0.2
            noise = np.random.normal(0, noise_magnitude)
            strike_probability += noise

        # Clamp to valid range
        strike_probability = np.clip(strike_probability, 0.0, 1.0)

        # Make call
        return 'strike' if np.random.random() < strike_probability else 'ball'

    def _calculate_distance_from_zone(
        self,
        horizontal: float,
        vertical: float
    ) -> float:
        """
        Calculate signed distance from strike zone edge.

        Negative = inside zone
        Zero = on edge
        Positive = outside zone

        Uses minimum distance to any edge.

        Parameters
        ----------
        horizontal : float
            Horizontal location
        vertical : float
            Vertical location

        Returns
        -------
        float
            Signed distance in inches
            Negative = inside, positive = outside
        """
        # Calculate distance to each edge
        # Negative = inside, positive = outside
        dist_left = self.zone_left - horizontal  # Negative if right of left edge
        dist_right = horizontal - self.zone_right  # Negative if left of right edge
        dist_bottom = self.zone_bottom - vertical  # Negative if above bottom
        dist_top = vertical - self.zone_top  # Negative if below top

        # Find minimum absolute distance
        horizontal_distance = max(dist_left, dist_right)
        vertical_distance = max(dist_bottom, dist_top)

        # Return minimum (closest edge)
        return min(horizontal_distance, vertical_distance)

    def get_framing_bonus(self, catcher_framing_rating: float) -> float:
        """
        Calculate catcher framing bonus to strike probability.

        Parameters
        ----------
        catcher_framing_rating : float
            Catcher's framing ability (0-100,000 scale)
            50,000 = average, 85,000+ = elite

        Returns
        -------
        float
            Framing bonus to add to strike probability
            Range: 0.0 to BB_FRAMING_BONUS_MAX
        """
        # Map 0-100k rating to 0.0-1.0 scale
        normalized_rating = catcher_framing_rating / 100000.0

        # Apply logistic curve for realistic distribution
        # Average (0.5): ~25% of max bonus
        # Elite (0.85): ~90% of max bonus
        # Poor (0.2): ~5% of max bonus
        if normalized_rating < 0.5:
            # Below average: 0-25% of max
            fraction = normalized_rating * 0.5
        else:
            # Above average: 25-100% of max
            fraction = 0.25 + (normalized_rating - 0.5) * 1.5

        fraction = np.clip(fraction, 0.0, 1.0)
        return fraction * BB_FRAMING_BONUS_MAX
