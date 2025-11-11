"""
Play analyzer module for batted ball trajectory analysis.

Contains methods for analyzing batted ball characteristics, calculating ball positions,
and generating field location descriptions.
"""

import numpy as np
from typing import Tuple
from .field_layout import FieldPosition
from .trajectory import BattedBallResult, convert_position_trajectory_to_field, convert_velocity_trajectory_to_field
from .constants import GROUND_BALL_LAUNCH_ANGLE_MAX, METERS_TO_FEET


class PlayAnalyzer:
    """Analyzer for batted ball trajectories and field locations."""

    @staticmethod
    def analyze_batted_ball(batted_ball_result: BattedBallResult) -> Tuple[FieldPosition, float, bool]:
        """Analyze batted ball trajectory to determine key characteristics."""
        # Get final position (landing spot)
        landing_pos = FieldPosition(
            batted_ball_result.landing_x,
            batted_ball_result.landing_y,
            0.0  # Ground level
        )

        # Determine hang time and whether it's an air ball
        hang_time = batted_ball_result.flight_time
        max_height = batted_ball_result.peak_height
        launch_angle = batted_ball_result.initial_conditions.get('launch_angle', 0.0)
        distance = batted_ball_result.distance

        # Improved classification logic
        # Consider multiple factors to determine if it's a ground ball vs air ball

        # Factor 1: Launch angle (strong indicator)
        low_launch_angle = launch_angle < GROUND_BALL_LAUNCH_ANGLE_MAX  # < 15 degrees
        very_low_launch = launch_angle < 10.0  # < 10 degrees = definitely ground ball

        # Factor 2: Peak height relative to distance
        # Ground balls have low peak heights relative to distance
        # Typical: ground ball peak height < 5 ft, line drives 5-15 ft, fly balls > 15 ft
        height_to_distance_ratio = max_height / max(distance, 1.0)  # Avoid division by zero
        is_low_trajectory = height_to_distance_ratio < 0.08  # Less than 8% ratio

        # Factor 3: Absolute peak height
        # Very low balls are definitely ground balls
        very_low = max_height < 3.0

        # Factor 4: Short flight time with short distance (weakly hit balls)
        # These should be ground balls near home plate
        weak_hit = distance < 50.0 and hang_time < 1.0

        # Classification decision tree:
        # Very low launch angles (< 10°) are always ground balls
        # BUT: If the ball lands more than 120 ft away, it's likely a line drive
        if very_low_launch:
            # Balls landing far into outfield (>120 ft) are line drives even with low launch angle
            is_air_ball = distance > 120.0
        # Weak hits near home plate with low peak
        elif weak_hit and max_height < 8.0:
            is_air_ball = False
        # Low launch angle (10-15°) with reasonable peak height
        elif low_launch_angle and max_height < 15.0:
            # If the ball is landing deep (>100 ft), treat as air ball for outfielders to catch
            # Infielders shouldn't be chasing balls 100+ feet away
            is_air_ball = distance > 100.0
        # Low trajectory ratio (< 8%) indicates ground ball/line drive
        elif is_low_trajectory and max_height < 12.0:
            # 6-12 ft range with low ratio = hard ground ball or line drive
            # But only if it's in infield range (< 100 ft)
            if distance > 100.0:
                is_air_ball = True  # Outfield line drive
            else:
                is_air_ball = max_height > 8.0  # 8-12 ft = low line drive (catchable)
        else:
            # Everything else is an air ball (fly balls, pop ups, high line drives)
            is_air_ball = max_height > 8.0 or hang_time > 1.5

        return landing_pos, hang_time, is_air_ball

    @staticmethod
    def calculate_ball_position_at_time(batted_ball_result: BattedBallResult, t: float) -> FieldPosition:
        """Calculate ball position at time t during flight using actual physics trajectory."""
        # Use actual trajectory data from physics simulation
        time_array = batted_ball_result.time
        position_array = batted_ball_result.position  # Nx3 array in meters

        # Handle edge cases
        if t <= 0:
            # Return initial position
            pos = position_array[0]
            return FieldPosition(
                pos[0] * METERS_TO_FEET,
                pos[1] * METERS_TO_FEET,
                pos[2] * METERS_TO_FEET
            )

        if t >= batted_ball_result.flight_time:
            # Return final position
            pos = position_array[-1]
            return FieldPosition(
                pos[0] * METERS_TO_FEET,
                pos[1] * METERS_TO_FEET,
                max(0.0, pos[2] * METERS_TO_FEET)  # Don't go below ground
            )

        # Find the two time points that bracket t
        idx = np.searchsorted(time_array, t)

        if idx == 0:
            # At or before first point
            pos = position_array[0]
        elif idx >= len(time_array):
            # At or after last point
            pos = position_array[-1]
        else:
            # Interpolate between two points
            t1 = time_array[idx - 1]
            t2 = time_array[idx]
            pos1 = position_array[idx - 1]
            pos2 = position_array[idx]

            # Linear interpolation factor
            alpha = (t - t1) / (t2 - t1)
            pos = pos1 + alpha * (pos2 - pos1)

        # Convert to feet and return
        return FieldPosition(
            pos[0] * METERS_TO_FEET,
            pos[1] * METERS_TO_FEET,
            max(0.0, pos[2] * METERS_TO_FEET)  # Don't go below ground
        )

    @staticmethod
    def create_trajectory_data_for_pursuit(batted_ball_result: BattedBallResult, current_time: float) -> dict:
        """
        Create trajectory data format expected by advanced AI pursuit methods.

        CRITICAL: Converts trajectory coordinates to field coordinates for consistency
        with fielder positions.
        """
        # Get trajectory arrays from batted ball result (in trajectory coordinates)
        time_array = batted_ball_result.time
        position_array = batted_ball_result.position  # In meters, trajectory coords
        velocity_array = batted_ball_result.velocity  # In m/s, trajectory coords

        # Find current time index
        current_idx = np.searchsorted(time_array, current_time)

        # Create future trajectory from current time onwards
        future_time = time_array[current_idx:]
        future_positions_traj = position_array[current_idx:]  # Trajectory coords
        future_velocities_traj = velocity_array[current_idx:]  # Trajectory coords

        # Convert positions and velocities to field coordinates
        future_positions_field = np.zeros_like(future_positions_traj)
        future_velocities_field = np.zeros_like(future_velocities_traj)

        for i in range(len(future_positions_traj)):
            # Convert position
            x_field, y_field, z_field = convert_position_trajectory_to_field(
                future_positions_traj[i, 0],  # x_traj (toward outfield)
                future_positions_traj[i, 1],  # y_traj (lateral, left +)
                future_positions_traj[i, 2]   # z_traj (vertical)
            )
            future_positions_field[i] = [x_field, y_field, z_field]

            # Convert velocity
            vx_field, vy_field, vz_field = convert_velocity_trajectory_to_field(
                future_velocities_traj[i, 0],  # vx_traj (toward outfield)
                future_velocities_traj[i, 1],  # vy_traj (lateral, left +)
                future_velocities_traj[i, 2]   # vz_traj (vertical)
            )
            future_velocities_field[i] = [vx_field, vy_field, vz_field]

        return {
            'position': future_positions_field,  # Nx3 array in meters, FIELD COORDS
            'velocity': future_velocities_field, # Nx3 array in m/s, FIELD COORDS
            'time': future_time                 # 1D array in seconds
        }

    @staticmethod
    def describe_field_location(position: FieldPosition) -> str:
        """Generate human-readable description of field location."""
        x, y = position.x, position.y

        # Calculate total distance from home plate (not just y-coordinate)
        distance = np.sqrt(x**2 + y**2)

        # Calculate spray angle to determine left/center/right
        spray_angle = np.arctan2(x, y) * 180.0 / np.pi  # degrees from center

        # Determine left/center/right
        if spray_angle < -20:
            field_side = "left "
        elif spray_angle > 20:
            field_side = "right "
        else:
            field_side = ""  # center field (no prefix)

        # Determine depth based on total distance
        if distance < 95:
            return "infield"
        elif distance < 180:
            return f"shallow {field_side}outfield"
        elif distance < 280:
            return f"{field_side}outfield"
        elif distance < 360:
            return f"deep {field_side}outfield"
        else:
            return f"warning track / {field_side}wall"
