"""
Exit Velocity and Launch Angle Joint Distribution Module.

Phase 3 Implementation: Implements joint distribution modeling for realistic
batted ball outcomes based on research findings.

Research Findings:
- Overall EV-LA correlation is weak (r ≈ -0.1)
- Hardest-hit balls (EV > 95 mph) cluster in line-drive zone (10-25°)
- Ground balls are pulled most often (~70% pull for GB vs ~50% for FB)
- LA-Spray correlation: r ≈ +0.20 (higher LA → less pull)

This module provides:
1. EVLADistribution class for correlated EV-LA sampling
2. get_spray_angle_for_launch_angle() for LA-spray correlation
"""

import numpy as np
from typing import Tuple, Optional


class EVLADistribution:
    """
    Joint distribution of Exit Velocity and Launch Angle.
    
    Based on research: weak negative correlation (r ≈ -0.1),
    but hardest-hit balls cluster in line-drive zone (10-25°).
    
    The correlation structure captures that:
    - High-quality contact (high EV) tends to produce line drives
    - Weak contact (low EV) can produce extreme angles (popups, worm burners)
    - The overall correlation is weak because many factors affect each independently
    
    Attributes
    ----------
    correlation : float
        EV-LA correlation coefficient (default -0.10)
    ev_mean : float
        Mean exit velocity in mph (default 88.0)
    ev_std : float
        Exit velocity standard deviation (default 12.0)
    la_mean : float
        Mean launch angle in degrees (default 12.0)
    la_std : float
        Launch angle standard deviation (default 20.0)
    """
    
    def __init__(
        self,
        correlation: float = -0.10,
        ev_mean: float = 88.0,
        ev_std: float = 12.0,
        la_mean: float = 12.0,
        la_std: float = 20.0
    ):
        """
        Initialize joint distribution parameters.
        
        Parameters
        ----------
        correlation : float
            EV-LA correlation coefficient (should be around -0.1)
        ev_mean : float
            Mean exit velocity in mph
        ev_std : float
            Exit velocity standard deviation in mph
        la_mean : float
            Mean launch angle in degrees
        la_std : float
            Launch angle standard deviation in degrees
        """
        self.correlation = correlation
        self.ev_mean = ev_mean
        self.ev_std = ev_std
        self.la_mean = la_mean
        self.la_std = la_std
        
        # Precompute covariance matrix for bivariate normal sampling
        self._update_covariance()
    
    def _update_covariance(self):
        """Update covariance matrix from current parameters."""
        # Covariance: cov(EV, LA) = correlation * std_ev * std_la
        cov = self.correlation * self.ev_std * self.la_std
        
        self.covariance_matrix = np.array([
            [self.ev_std ** 2, cov],
            [cov, self.la_std ** 2]
        ])
        
        self.means = np.array([self.ev_mean, self.la_mean])
    
    def sample(self, contact_quality: float = 0.5) -> Tuple[float, float]:
        """
        Sample (EV, LA) pair with appropriate correlation.
        
        For hard contact (quality > 0.8): bias LA toward 10-25° range (line drives)
        For weak contact (quality < 0.3): allow extreme LA values (popups, worm burners)
        
        Parameters
        ----------
        contact_quality : float
            Quality of contact from 0.0 (terrible) to 1.0 (perfect barrel)
            
        Returns
        -------
        tuple[float, float]
            (exit_velocity_mph, launch_angle_deg)
        """
        # Sample from bivariate normal with weak correlation
        sample = np.random.multivariate_normal(self.means, self.covariance_matrix)
        ev, la = sample[0], sample[1]
        
        # Apply contact quality adjustments
        ev, la = self._apply_contact_quality_adjustment(ev, la, contact_quality)
        
        # Clamp to physical bounds
        ev = max(10.0, min(120.0, ev))
        la = max(-20.0, min(85.0, la))
        
        return ev, la
    
    def _apply_contact_quality_adjustment(
        self,
        ev: float,
        la: float,
        contact_quality: float
    ) -> Tuple[float, float]:
        """
        Adjust EV and LA based on contact quality.
        
        Research shows that:
        - High quality contact produces higher EV and more optimal LA (10-25°)
        - Poor quality contact produces lower EV and more extreme LA
        
        Parameters
        ----------
        ev : float
            Exit velocity from base distribution
        la : float
            Launch angle from base distribution
        contact_quality : float
            Quality of contact (0.0 to 1.0)
            
        Returns
        -------
        tuple[float, float]
            Adjusted (exit_velocity, launch_angle)
        """
        if contact_quality >= 0.8:
            # Hard contact: bias toward line drive zone (10-25°)
            # High quality contact tends to produce optimal launch angles
            la_target = 17.5  # Center of line drive zone
            la_blend = 0.4  # How much to bias toward target
            la = la * (1 - la_blend) + la_target * la_blend
            
            # Also ensure EV is reasonably high for quality contact
            ev = max(ev, self.ev_mean + 0.5 * self.ev_std)
            
        elif contact_quality <= 0.3:
            # Weak contact: increase variance, allow extreme angles
            # Poor contact produces more variability
            extra_variance = 1.5 * (0.3 - contact_quality) / 0.3
            la_adjustment = np.random.normal(0, 8.0 * extra_variance)
            la = la + la_adjustment
            
            # Weak contact reduces EV
            ev = min(ev, self.ev_mean - 0.3 * self.ev_std)
            
        # For middle-quality contact, use the base distribution as-is
        return ev, la
    
    def get_la_given_ev(self, exit_velocity: float) -> float:
        """
        Sample launch angle conditioned on exit velocity.
        
        Research: P(LA | EV > 95mph) clusters more around 10-25°
        This implements the conditional distribution LA | EV.
        
        Parameters
        ----------
        exit_velocity : float
            Exit velocity in mph
            
        Returns
        -------
        float
            Launch angle in degrees
        """
        if exit_velocity > 95:
            # Hard hit: favor line-drive angles
            # Narrower distribution centered on optimal LA
            la = np.random.normal(15.0, 12.0)
            
        elif exit_velocity < 80:
            # Weak contact: allow extreme angles
            # Wider distribution, more popups and weak grounders
            la = np.random.normal(12.0, 25.0)
            
        else:
            # Normal contact: use standard distribution
            la = np.random.normal(12.0, 18.0)
        
        # Clamp to physical bounds
        la = max(-20.0, min(85.0, la))
        
        return la
    
    def sample_batch(self, n: int, contact_qualities: Optional[np.ndarray] = None) -> Tuple[np.ndarray, np.ndarray]:
        """
        Sample n (EV, LA) pairs efficiently using vectorized operations.
        
        Parameters
        ----------
        n : int
            Number of samples to generate
        contact_qualities : np.ndarray, optional
            Array of contact quality values. If None, uses 0.5 for all.
            
        Returns
        -------
        tuple[np.ndarray, np.ndarray]
            Arrays of (exit_velocities, launch_angles)
        """
        # Generate base samples from bivariate normal
        samples = np.random.multivariate_normal(self.means, self.covariance_matrix, size=n)
        evs = samples[:, 0]
        las = samples[:, 1]
        
        if contact_qualities is not None:
            # Apply quality adjustments
            for i in range(n):
                evs[i], las[i] = self._apply_contact_quality_adjustment(
                    evs[i], las[i], contact_qualities[i]
                )
        
        # Clamp to physical bounds
        evs = np.clip(evs, 10.0, 120.0)
        las = np.clip(las, -20.0, 85.0)
        
        return evs, las


def get_spray_angle_for_launch_angle(
    launch_angle: float,
    hitter_spray_tendency: float = 0.0,
    random_state: Optional[np.random.RandomState] = None
) -> float:
    """
    Generate spray angle considering LA-spray correlation.
    
    Research Finding (Section 2):
    - Ground balls are pulled most often (~70% pull for GB vs ~50% for FB)
    - LA-Spray correlation: r ≈ +0.20 (higher LA → less pull)
    
    **PHYSICS SPRAY ANGLE CONVENTION** (used by physics/trajectory):
    - Positive spray angle = LEFT field (pull side for RHH)
    - Negative spray angle = RIGHT field (opposite field for RHH)
    - 0 = straight to center field
    
    Note: This is OPPOSITE to the field/ballpark convention where:
    - Negative = left field, Positive = right field
    The BattedBallResult.spray_angle_landing is converted to field convention.
    
    IMPORTANT: Uses 27° std dev to match the Phase 2C HR rate tuning. 
    This variance was increased from 22° specifically to boost HR rate by
    getting more balls toward the corners (±40-45°) where fences are shorter.
    
    Parameters
    ----------
    launch_angle : float
        Launch angle in degrees
    hitter_spray_tendency : float
        Hitter's base spray tendency in degrees
        Positive = tends to pull (left field), Negative = tends to go oppo (right field)
    random_state : np.random.RandomState, optional
        Random state for reproducibility
        
    Returns
    -------
    float
        Spray angle in degrees (-45 to +45) using PHYSICS convention
    """
    rng = random_state if random_state is not None else np.random
    
    # Use 27° std dev to match Phase 2C HR tuning
    # This was increased from 22° to get ~8-12% of balls to ±40-45° range
    # where shorter fences (330ft vs 400ft center) boost HR rate
    SPRAY_STD_DEV = 27.0
    
    if launch_angle < 10:
        # Ground balls (LA < 10°): Higher pull bias (~65% pull)
        # Slightly less than 70% to avoid over-concentration at pull side
        pull_direction = rng.choice([1, -1], p=[0.65, 0.35])
        # Wide variance for realistic spray distribution
        magnitude = abs(rng.normal(0.0, SPRAY_STD_DEV))
        spray = hitter_spray_tendency + pull_direction * magnitude
        
    elif launch_angle < 25:
        # Line drives (10-25°): Moderate pull (~55% pull)
        pull_direction = rng.choice([1, -1], p=[0.55, 0.45])
        # Same wide variance
        magnitude = abs(rng.normal(0.0, SPRAY_STD_DEV))
        spray = hitter_spray_tendency + pull_direction * magnitude
        
    else:
        # Fly balls (25°+): Even distribution (~50% pull)
        # Pure normal distribution centered on hitter tendency
        spray = hitter_spray_tendency + rng.normal(0.0, SPRAY_STD_DEV)
    
    # Clamp to foul line boundaries
    spray = np.clip(spray, -45.0, 45.0)
    
    return float(spray)


def apply_ev_la_correlation_adjustment(
    exit_velocity: float,
    launch_angle: float,
    contact_quality: float = 0.5
) -> Tuple[float, float]:
    """
    Apply EV-LA correlation adjustment to independently generated values.
    
    This function retrofits a MILD correlation onto existing EV/LA generation.
    The adjustment is intentionally subtle to avoid disrupting the calibrated
    physics model while adding the research-based correlation effect.
    
    Research finding: r ≈ -0.1 (weak negative correlation)
    - Hard hits cluster slightly more in optimal LA range
    - But HRs at 25-30° must still be possible with high EV!
    
    Parameters
    ----------
    exit_velocity : float
        Exit velocity in mph (already generated)
    launch_angle : float
        Launch angle in degrees (already generated)
    contact_quality : float
        Quality of contact (0.0 to 1.0)
        
    Returns
    -------
    tuple[float, float]
        Adjusted (exit_velocity, launch_angle)
    """
    # MINIMAL adjustments - the physics model is already calibrated
    # We only want to add a subtle correlation effect
    
    if exit_velocity > 100:
        # Very hard hits (100+ mph): only adjust extreme popups
        # Keep 25-35° range for potential HRs!
        if launch_angle > 45:
            # Extreme popup with high EV is unrealistic
            # Pull down slightly (but not too much)
            adjustment = (launch_angle - 45) * 0.15
            launch_angle -= adjustment
            
    elif exit_velocity < 70:
        # Very weak contact: allow natural variance
        # No adjustment needed - weak contact already produces varied angles
        pass
    
    # Clamp to physical bounds
    launch_angle = max(-20.0, min(85.0, launch_angle))
    
    return exit_velocity, launch_angle
