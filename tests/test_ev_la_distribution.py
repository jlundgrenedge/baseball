"""
Tests for EV/LA Distribution Correlation (Phase 3).

Validates:
1. EV-LA correlation matches research (~-0.1)
2. Hard-hit balls favor line-drive LA (10-25°)
3. Ground ball spray has ~70% pull bias
4. LA-spray correlation is present (higher LA → less pull)
"""

import numpy as np
import pytest
import sys
import os

# Add the project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from batted_ball.ev_la_distribution import (
    EVLADistribution,
    get_spray_angle_for_launch_angle,
    apply_ev_la_correlation_adjustment,
)


class TestEVLADistribution:
    """Tests for the EVLADistribution class."""
    
    def test_initialization(self):
        """Test that distribution initializes with default parameters."""
        dist = EVLADistribution()
        
        assert dist.correlation == -0.10
        assert dist.ev_mean == 88.0
        assert dist.ev_std == 12.0
        assert dist.la_mean == 12.0
        assert dist.la_std == 20.0
    
    def test_custom_parameters(self):
        """Test distribution with custom parameters."""
        dist = EVLADistribution(
            correlation=-0.15,
            ev_mean=90.0,
            ev_std=10.0,
            la_mean=15.0,
            la_std=18.0
        )
        
        assert dist.correlation == -0.15
        assert dist.ev_mean == 90.0
    
    def test_sample_returns_tuple(self):
        """Test that sample returns (EV, LA) tuple."""
        dist = EVLADistribution()
        result = dist.sample()
        
        assert isinstance(result, tuple)
        assert len(result) == 2
        
        ev, la = result
        assert isinstance(ev, (int, float))
        assert isinstance(la, (int, float))
    
    def test_sample_within_bounds(self):
        """Test that samples are within physical bounds."""
        dist = EVLADistribution()
        
        for _ in range(100):
            ev, la = dist.sample()
            
            # Exit velocity bounds
            assert 10.0 <= ev <= 120.0, f"EV {ev} out of bounds"
            
            # Launch angle bounds
            assert -20.0 <= la <= 85.0, f"LA {la} out of bounds"
    
    def test_ev_la_correlation(self):
        """Test EV-LA correlation matches research (~-0.1)."""
        dist = EVLADistribution()
        n_samples = 5000
        
        samples = [dist.sample() for _ in range(n_samples)]
        ev = np.array([s[0] for s in samples])
        la = np.array([s[1] for s in samples])
        
        correlation = np.corrcoef(ev, la)[0, 1]
        
        # Research shows correlation around -0.1, allow reasonable tolerance
        assert -0.20 < correlation < 0.05, \
            f"EV-LA correlation {correlation:.3f} should be around -0.1"
    
    def test_high_quality_contact_favors_line_drives(self):
        """Test that high quality contact produces more line drives."""
        dist = EVLADistribution()
        n_samples = 1000
        
        # Sample with high contact quality
        high_quality_samples = [dist.sample(contact_quality=0.9) for _ in range(n_samples)]
        la_high = np.array([s[1] for s in high_quality_samples])
        
        # Sample with low contact quality
        low_quality_samples = [dist.sample(contact_quality=0.2) for _ in range(n_samples)]
        la_low = np.array([s[1] for s in low_quality_samples])
        
        # Count line drives (10-25°)
        ld_pct_high = np.sum((la_high >= 10) & (la_high <= 25)) / n_samples
        ld_pct_low = np.sum((la_low >= 10) & (la_low <= 25)) / n_samples
        
        # High quality should produce more line drives than low quality
        assert ld_pct_high > ld_pct_low, \
            f"High quality LD% ({ld_pct_high:.1%}) should exceed low quality LD% ({ld_pct_low:.1%})"
    
    def test_hard_hit_la_distribution(self):
        """Test hard-hit balls cluster in line-drive zone."""
        dist = EVLADistribution()
        n_samples = 2000
        
        # Sample and filter for hard hits (EV > 95)
        all_samples = [dist.sample(contact_quality=0.85) for _ in range(n_samples)]
        hard_hits = [(ev, la) for ev, la in all_samples if ev > 95]
        
        if len(hard_hits) > 50:  # Need enough samples
            la_hard = np.array([h[1] for h in hard_hits])
            
            # Most hard hits should be in line-drive zone (10-25°)
            ld_pct = np.sum((la_hard >= 10) & (la_hard <= 25)) / len(la_hard)
            
            # At least 30% should be line drives (research shows clustering)
            assert ld_pct > 0.30, \
                f"Only {ld_pct:.1%} of hard hits are line drives, expected >30%"
    
    def test_get_la_given_ev_hard_hit(self):
        """Test conditional LA sampling for hard hits."""
        dist = EVLADistribution()
        n_samples = 500
        
        # Sample LA given high EV
        la_samples = [dist.get_la_given_ev(100.0) for _ in range(n_samples)]
        la = np.array(la_samples)
        
        # Mean should be around 15° (line-drive zone)
        mean_la = np.mean(la)
        assert 10 < mean_la < 20, \
            f"Mean LA for hard hits is {mean_la:.1f}°, expected 10-20°"
    
    def test_get_la_given_ev_weak_contact(self):
        """Test conditional LA sampling for weak contact."""
        dist = EVLADistribution()
        n_samples = 500
        
        # Sample LA given low EV
        la_samples = [dist.get_la_given_ev(70.0) for _ in range(n_samples)]
        la = np.array(la_samples)
        
        # Standard deviation should be wider than for hard contact
        std_la = np.std(la)
        assert std_la > 15, \
            f"LA std dev for weak contact is {std_la:.1f}°, expected >15° (more variance)"
    
    def test_batch_sampling(self):
        """Test batch sampling produces correct number of samples."""
        dist = EVLADistribution()
        n = 1000
        
        evs, las = dist.sample_batch(n)
        
        assert len(evs) == n
        assert len(las) == n
        
        # Check bounds
        assert np.all(evs >= 10.0) and np.all(evs <= 120.0)
        assert np.all(las >= -20.0) and np.all(las <= 85.0)


class TestSprayAngleCorrelation:
    """Tests for LA-spray correlation function."""
    
    def test_ground_ball_pull_bias(self):
        """Test ground balls have ~70% pull bias."""
        n_samples = 1000
        ground_balls = []
        
        for _ in range(n_samples):
            la = np.random.uniform(-5, 9)  # Ground ball LA
            spray = get_spray_angle_for_launch_angle(la, hitter_spray_tendency=0)
            ground_balls.append(spray)
        
        # Positive spray = pulled
        pull_pct = sum(1 for s in ground_balls if s > 0) / n_samples
        
        # Should be around 70% pulled
        assert 0.60 < pull_pct < 0.80, \
            f"Ground ball pull rate is {pull_pct:.1%}, expected 60-80%"
    
    def test_line_drive_moderate_pull(self):
        """Test line drives have moderate pull bias (~55%)."""
        n_samples = 1000
        line_drives = []
        
        for _ in range(n_samples):
            la = np.random.uniform(10, 24)  # Line drive LA
            spray = get_spray_angle_for_launch_angle(la, hitter_spray_tendency=0)
            line_drives.append(spray)
        
        pull_pct = sum(1 for s in line_drives if s > 0) / n_samples
        
        # Should be around 55% pulled
        assert 0.45 < pull_pct < 0.65, \
            f"Line drive pull rate is {pull_pct:.1%}, expected 45-65%"
    
    def test_fly_ball_even_distribution(self):
        """Test fly balls have more even spray distribution (~50%)."""
        n_samples = 1000
        fly_balls = []
        
        for _ in range(n_samples):
            la = np.random.uniform(25, 45)  # Fly ball LA
            spray = get_spray_angle_for_launch_angle(la, hitter_spray_tendency=0)
            fly_balls.append(spray)
        
        pull_pct = sum(1 for s in fly_balls if s > 0) / n_samples
        
        # Should be close to 50% (even distribution)
        assert 0.40 < pull_pct < 0.60, \
            f"Fly ball pull rate is {pull_pct:.1%}, expected 40-60%"
    
    def test_spray_respects_hitter_tendency(self):
        """Test spray angles incorporate hitter's pull tendency."""
        n_samples = 500
        
        # Pull hitter (tendency = +10°)
        pull_sprays = [get_spray_angle_for_launch_angle(15, hitter_spray_tendency=10) 
                       for _ in range(n_samples)]
        
        # Opposite field hitter (tendency = -10°)
        oppo_sprays = [get_spray_angle_for_launch_angle(15, hitter_spray_tendency=-10) 
                       for _ in range(n_samples)]
        
        mean_pull = np.mean(pull_sprays)
        mean_oppo = np.mean(oppo_sprays)
        
        # Pull hitter should have higher mean spray angle
        assert mean_pull > mean_oppo + 10, \
            f"Pull hitter mean ({mean_pull:.1f}°) should exceed oppo hitter ({mean_oppo:.1f}°) by >10°"
    
    def test_spray_within_bounds(self):
        """Test spray angles stay within foul line bounds."""
        for _ in range(500):
            la = np.random.uniform(-10, 60)
            tendency = np.random.uniform(-15, 15)
            spray = get_spray_angle_for_launch_angle(la, hitter_spray_tendency=tendency)
            
            assert -45 <= spray <= 45, \
                f"Spray angle {spray}° outside foul line bounds"
    
    def test_la_spray_correlation_present(self):
        """Test that higher LA produces less pull bias (correlation ~+0.2)."""
        n_samples = 1000
        
        # Generate paired (LA, spray) samples
        las = []
        sprays = []
        for _ in range(n_samples):
            la = np.random.uniform(-5, 50)
            spray = get_spray_angle_for_launch_angle(la, hitter_spray_tendency=0)
            las.append(la)
            sprays.append(spray)
        
        las = np.array(las)
        sprays = np.array(sprays)
        
        # Higher LA should correlate with less extreme (closer to 0) spray
        # This manifests as lower pull rate for higher LA
        low_la = sprays[las < 10]  # Ground balls
        high_la = sprays[las > 25]  # Fly balls
        
        low_la_pull = np.mean(low_la > 0)
        high_la_pull = np.mean(high_la > 0)
        
        # Ground balls should have higher pull rate than fly balls
        assert low_la_pull > high_la_pull, \
            f"GB pull rate ({low_la_pull:.1%}) should exceed FB pull rate ({high_la_pull:.1%})"


class TestEVLACorrelationAdjustment:
    """Tests for the EV-LA correlation adjustment function."""
    
    def test_high_ev_high_la_adjustment(self):
        """Test high EV + high LA gets adjusted toward line-drive zone."""
        # High EV popup (unrealistic) should be adjusted down
        ev, la = apply_ev_la_correlation_adjustment(105, 50, contact_quality=0.9)
        
        # LA should be reduced toward line-drive zone
        assert la < 50, \
            f"LA {la}° should be reduced from 50° for hard hit ball"
        
        # EV should be unchanged
        assert ev == 105
    
    def test_high_ev_optimal_la_unchanged(self):
        """Test high EV with already-optimal LA stays mostly unchanged."""
        # Hard hit line drive - should stay similar
        np.random.seed(42)
        ev, la = apply_ev_la_correlation_adjustment(100, 18, contact_quality=0.9)
        
        # LA should stay close to original (already in optimal zone)
        assert abs(la - 18) < 3, \
            f"Optimal LA 18° changed to {la}° unnecessarily"
    
    def test_weak_contact_allows_extremes(self):
        """Test weak contact preserves natural variance (no aggressive adjustment)."""
        # With the simplified adjustment function, weak contact should pass through
        # mostly unchanged - the physics model already handles variance appropriately
        np.random.seed(42)
        weak_adjustments = []
        for _ in range(100):
            ev, la = apply_ev_la_correlation_adjustment(70, 15, contact_quality=0.1)
            weak_adjustments.append(la)
        
        # The adjustment should be minimal for weak contact
        # All values should be close to the input (15)
        mean_la = np.mean(weak_adjustments)
        assert abs(mean_la - 15) < 1, \
            f"Weak contact LA mean {mean_la:.1f} should be close to input (15)"
    
    def test_bounds_respected(self):
        """Test that adjustments respect physical bounds."""
        for _ in range(100):
            ev = np.random.uniform(60, 115)
            la = np.random.uniform(-15, 80)
            quality = np.random.random()
            
            adj_ev, adj_la = apply_ev_la_correlation_adjustment(ev, la, quality)
            
            assert -20 <= adj_la <= 85, \
                f"Adjusted LA {adj_la}° outside bounds"


class TestIntegration:
    """Integration tests for the EV-LA distribution system."""
    
    def test_full_workflow(self):
        """Test complete workflow from distribution to spray angle."""
        dist = EVLADistribution()
        
        # Sample EV-LA pair
        ev, la = dist.sample(contact_quality=0.7)
        
        # Get correlated spray angle
        spray = get_spray_angle_for_launch_angle(la, hitter_spray_tendency=5)
        
        # Verify all values are reasonable
        assert 10 <= ev <= 120
        assert -20 <= la <= 85
        assert -45 <= spray <= 45
    
    def test_batted_ball_type_distribution(self):
        """Test that sampled LAs produce reasonable batted ball type distribution."""
        dist = EVLADistribution()
        n_samples = 2000
        
        samples = [dist.sample() for _ in range(n_samples)]
        la = np.array([s[1] for s in samples])
        
        # Count batted ball types
        gb_pct = np.sum(la < 10) / n_samples
        ld_pct = np.sum((la >= 10) & (la < 25)) / n_samples
        fb_pct = np.sum((la >= 25) & (la < 50)) / n_samples
        popup_pct = np.sum(la >= 50) / n_samples
        
        # These should be in reasonable MLB-like ranges
        # Note: The actual game uses a different LA generation system
        # This distribution is supplementary for correlation effects
        print(f"Distribution: GB {gb_pct:.1%}, LD {ld_pct:.1%}, FB {fb_pct:.1%}, PU {popup_pct:.1%}")
        
        # Basic sanity checks
        assert 0.15 < gb_pct < 0.60, f"GB% {gb_pct:.1%} outside expected range"
        assert 0.10 < ld_pct < 0.50, f"LD% {ld_pct:.1%} outside expected range"
        assert 0.10 < fb_pct < 0.50, f"FB% {fb_pct:.1%} outside expected range"


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
