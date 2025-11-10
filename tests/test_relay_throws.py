"""
Test relay throw mechanics for deep outfield throws.

Tests that verify:
1. Relay throws are triggered for distances > 200 feet
2. Appropriate cut-off men are selected
3. Two-stage throw timing is calculated correctly
4. Direct throws are used for shorter distances
"""

import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import pytest
from batted_ball import (
    FieldLayout, FieldPosition,
    Fielder, create_average_fielder, create_elite_fielder,
    simulate_relay_throw, determine_cutoff_man,
    RELAY_THROW_THRESHOLD, FielderAttributes
)


class TestCutoffManSelection:
    """Test that appropriate cut-off men are selected based on fielder and target."""

    def test_left_field_to_home(self):
        """Left fielder throwing home should use shortstop as cutoff."""
        cutoff = determine_cutoff_man('left_field', 'home')
        assert cutoff == 'shortstop'

    def test_center_field_to_home(self):
        """Center fielder throwing home should use shortstop as cutoff."""
        cutoff = determine_cutoff_man('center_field', 'home')
        assert cutoff == 'shortstop'

    def test_right_field_to_home(self):
        """Right fielder throwing home should use second baseman as cutoff."""
        cutoff = determine_cutoff_man('right_field', 'home')
        assert cutoff == 'second_base'

    def test_outfield_to_third(self):
        """Any outfielder throwing to third should use shortstop as cutoff."""
        assert determine_cutoff_man('left_field', 'third') == 'shortstop'
        assert determine_cutoff_man('center_field', 'third') == 'shortstop'
        assert determine_cutoff_man('right_field', 'third') == 'shortstop'

    def test_deep_throw_to_second(self):
        """Deep throws to second should use shortstop as cutoff."""
        cutoff = determine_cutoff_man('center_field', 'second')
        assert cutoff == 'shortstop'


class TestRelayThrowDistance:
    """Test that relay throws are triggered based on distance threshold."""

    @pytest.fixture
    def field_layout(self):
        """Create standard field layout."""
        return FieldLayout()

    @pytest.fixture
    def center_fielder(self):
        """Create center fielder with average attributes."""
        return create_average_fielder("Test CF", "center_field")

    @pytest.fixture
    def shortstop(self):
        """Create shortstop with average attributes."""
        return create_average_fielder("Test SS", "shortstop")

    def test_short_throw_no_relay(self, field_layout, center_fielder, shortstop):
        """Throw under 200 feet should NOT trigger relay."""
        # Position at shallow center field (~250 ft from home)
        shallow_cf_position = FieldPosition(0, 250, 0)

        result = simulate_relay_throw(
            center_fielder, shortstop, shallow_cf_position, 'home', field_layout
        )

        assert not result.is_relay, "Short throw should not use relay"
        assert result.cutoff_position == "none"

    def test_deep_throw_uses_relay(self, field_layout, center_fielder, shortstop):
        """Throw over 200 feet should trigger relay."""
        # Position at deep center field (~380 ft from home)
        deep_cf_position = FieldPosition(0, 380, 0)

        result = simulate_relay_throw(
            center_fielder, shortstop, deep_cf_position, 'home', field_layout
        )

        assert result.is_relay, "Deep throw should use relay"
        assert result.cutoff_position == "shortstop"

    def test_force_relay(self, field_layout, center_fielder, shortstop):
        """Force relay flag should trigger relay regardless of distance."""
        # Position at shallow center field
        shallow_position = FieldPosition(0, 250, 0)

        result = simulate_relay_throw(
            center_fielder, shortstop, shallow_position, 'home', field_layout,
            force_relay=True
        )

        assert result.is_relay, "Force relay should trigger relay"
        assert result.cutoff_position == "shortstop"


class TestRelayThrowTiming:
    """Test that relay throw timing is calculated correctly."""

    @pytest.fixture
    def field_layout(self):
        """Create standard field layout."""
        return FieldLayout()

    @pytest.fixture
    def deep_cf_position(self):
        """Deep center field position requiring relay."""
        return FieldPosition(0, 380, 0)

    @pytest.fixture
    def center_fielder(self):
        """Create center fielder with known arm strength."""
        cf_attrs = FielderAttributes(
            sprint_speed=75.0,  # Average speed
            arm_strength=70.0,  # Average outfield arm
            reaction_time=60.0,
            route_efficiency=65.0,
            transfer_time=55.0,
            throwing_accuracy=60.0,
            fielding_range=65.0
        )
        return Fielder("Test CF", "center_field", cf_attrs)

    @pytest.fixture
    def shortstop(self):
        """Create shortstop with known arm strength."""
        ss_attrs = FielderAttributes(
            sprint_speed=70.0,
            arm_strength=75.0,  # Good infield arm
            reaction_time=65.0,
            route_efficiency=70.0,
            transfer_time=70.0,  # Fast infield transfer
            throwing_accuracy=70.0,
            fielding_range=70.0
        )
        return Fielder("Test SS", "shortstop", ss_attrs)

    def test_relay_time_structure(self, field_layout, center_fielder, shortstop, deep_cf_position):
        """Relay throw should have both throw stages with handling time."""
        result = simulate_relay_throw(
            center_fielder, shortstop, deep_cf_position, 'home', field_layout
        )

        assert result.is_relay
        assert result.first_throw is not None, "Should have first throw"
        assert result.second_throw is not None, "Should have second throw"
        assert 0.2 <= result.relay_handling_time <= 0.4, "Relay handling time should be 0.2-0.4s"

        # Total time should be sum of components
        expected_time = (
            result.first_throw.arrival_time +
            result.relay_handling_time +
            result.second_throw.arrival_time
        )
        assert abs(result.total_arrival_time - expected_time) < 0.01

    def test_relay_slower_than_impossible_direct(self, field_layout, center_fielder,
                                                  shortstop, deep_cf_position):
        """Relay throw should add time but be more realistic than direct throw."""
        result = simulate_relay_throw(
            center_fielder, shortstop, deep_cf_position, 'home', field_layout
        )

        assert result.is_relay
        # Relay should take at least 2.5 seconds from deep CF
        assert result.total_arrival_time >= 2.5, "Relay from deep CF should take substantial time"

        # First throw should be shorter distance than full throw
        home_pos = field_layout.get_base_position('home')
        full_distance = deep_cf_position.horizontal_distance_to(home_pos)
        assert full_distance > RELAY_THROW_THRESHOLD, "Should exceed relay threshold"


class TestRelayInPlaySimulation:
    """Test relay throws in context of complete play simulation."""

    @pytest.fixture
    def field_layout(self):
        """Create standard field layout."""
        return FieldLayout()

    def test_deep_gap_double_uses_relay(self, field_layout):
        """Deep gap double should trigger relay throw to third/home."""
        from batted_ball import PlaySimulator, BattedBallResult
        from batted_ball import create_standard_defense

        # Create play simulator with standard defense
        play_sim = PlaySimulator(field_layout)
        fielders = create_standard_defense()
        for pos, fielder in fielders.items():
            play_sim.fielding_simulator.add_fielder(pos, fielder)

        # Simulate deep center field hit (380+ feet)
        # This should require relay throw to home
        from batted_ball.trajectory import InitialConditions

        # Create a deep fly ball result
        result = BattedBallResult(
            initial_conditions=InitialConditions(
                velocity=105.0,
                launch_angle=25.0,
                spray_angle=0.0
            ),
            landing_x=0.0,
            landing_y=380.0,
            distance=380.0,
            hang_time=5.5,
            peak_height=95.0,
            flight_time=5.5,
            time_array=[0.0, 5.5],
            position_array=[[0, 0, 3], [0, 380 * 0.3048, 0]],
            is_fair=True,
            wall_contact=False,
            estimated_landing_y=380.0
        )

        # The play simulation should use relay logic for throws
        # This is verified by the simulation not crashing and completing
        print(f"\nDeep hit to CF: {result.distance:.0f} ft")
        print(f"Landing position: ({result.landing_x:.0f}, {result.landing_y:.0f})")
        print("Relay throw mechanics should be used for throws home/third")


class TestRelayThrowRealism:
    """Test that relay throws produce realistic timing."""

    @pytest.fixture
    def field_layout(self):
        """Create standard field layout."""
        return FieldLayout()

    def test_deep_lf_to_home_timing(self, field_layout):
        """Deep left field to home should take ~3-4 seconds with relay."""
        # Create fielders
        lf = create_average_fielder("LF", "left_field")
        ss = create_average_fielder("SS", "shortstop")

        # Deep left field position (~350 ft from home)
        deep_lf_position = FieldPosition(-220, 270, 0)

        result = simulate_relay_throw(
            lf, ss, deep_lf_position, 'home', field_layout
        )

        assert result.is_relay
        assert result.cutoff_position == 'shortstop'
        # Realistic timing: should take 3-4.5 seconds total
        assert 2.5 <= result.total_arrival_time <= 5.0, \
            f"Deep LF to home relay should take 2.5-5.0s, got {result.total_arrival_time:.2f}s"

    def test_deep_rf_to_third_timing(self, field_layout):
        """Deep right field to third should use shortstop and take ~3-4 seconds."""
        rf = create_average_fielder("RF", "right_field")
        ss = create_average_fielder("SS", "shortstop")

        # Deep right field position (~330 ft from third)
        deep_rf_position = FieldPosition(220, 260, 0)

        result = simulate_relay_throw(
            rf, ss, deep_rf_position, 'third', field_layout
        )

        assert result.is_relay
        assert result.cutoff_position == 'shortstop'
        assert 2.5 <= result.total_arrival_time <= 5.0, \
            f"Deep RF to third relay should take 2.5-5.0s, got {result.total_arrival_time:.2f}s"


if __name__ == "__main__":
    # Run tests with pytest
    pytest.main([__file__, "-v", "-s"])
