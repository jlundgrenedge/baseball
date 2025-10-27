"""Test pitcher velocity generation."""
import sys
sys.path.append('.')

from batted_ball import create_test_team

# Test different team qualities
for quality in ['poor', 'average', 'good', 'elite']:
    team = create_test_team(f'Test {quality}', quality)
    pitcher = team.pitchers[0]
    velo = pitcher.get_pitch_velocity_mph('fastball')
    print(f'{quality.capitalize():8s} quality pitcher: {velo:.1f} mph')
