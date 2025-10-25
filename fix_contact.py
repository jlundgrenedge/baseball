#!/usr/bin/env python3
"""Quick script to fix the contact.py file."""

import re

def fix_contact_file():
    with open('batted_ball/contact.py', 'r') as f:
        content = f.read()
    
    # Find the problematic section and replace it
    pattern = r'(        """\n)        # Apply additional.*?exit_velocity = max\(exit_velocity, 15\.0\)  # Minimum 15 mph for any contact\n\n(        # Calculate launch angle)'
    
    replacement = r'''\1        # Calculate exit velocity
        exit_velocity = self.calculate_exit_velocity(
            bat_speed_mph=bat_speed_mph,
            pitch_speed_mph=pitch_speed_mph,
            collision_angle_deg=0.0,  # Assume head-on for now
            distance_from_sweet_spot_inches=distance_from_sweet_spot_inches
        )
        
        # Apply additional exit velocity reduction for off-center contact
        # This simulates the reduced energy transfer for poor contact
        center_distance = np.sqrt(vertical_contact_offset_inches**2 + horizontal_contact_offset_inches**2)
        if center_distance > 0.5:  # Beyond reasonable contact area
            # Exponential degradation for very poor contact
            contact_efficiency = np.exp(-center_distance / 2.0)
            exit_velocity *= contact_efficiency
            
        # Ensure minimum exit velocity for any contact
        exit_velocity = max(exit_velocity, 15.0)  # Minimum 15 mph for any contact

\2'''
    
    new_content = re.sub(pattern, replacement, content, flags=re.DOTALL)
    
    # If that didn't work, try a simpler approach
    if content == new_content:
        # Find and fix manually
        lines = content.split('\n')
        new_lines = []
        in_method = False
        found_docstring_end = False
        skip_until_calculate = False
        
        for i, line in enumerate(lines):
            if 'def full_collision(' in line:
                in_method = True
                new_lines.append(line)
            elif in_method and line.strip() == '"""':
                found_docstring_end = True
                new_lines.append(line)
                # Add the proper exit velocity calculation
                new_lines.append('        # Calculate exit velocity')
                new_lines.append('        exit_velocity = self.calculate_exit_velocity(')
                new_lines.append('            bat_speed_mph=bat_speed_mph,')
                new_lines.append('            pitch_speed_mph=pitch_speed_mph,')
                new_lines.append('            collision_angle_deg=0.0,  # Assume head-on for now')
                new_lines.append('            distance_from_sweet_spot_inches=distance_from_sweet_spot_inches')
                new_lines.append('        )')
                new_lines.append('        ')
                new_lines.append('        # Apply additional exit velocity reduction for off-center contact')
                new_lines.append('        # This simulates the reduced energy transfer for poor contact')
                new_lines.append('        center_distance = np.sqrt(vertical_contact_offset_inches**2 + horizontal_contact_offset_inches**2)')
                new_lines.append('        if center_distance > 0.5:  # Beyond reasonable contact area')
                new_lines.append('            # Exponential degradation for very poor contact')
                new_lines.append('            contact_efficiency = np.exp(-center_distance / 2.0)')
                new_lines.append('            exit_velocity *= contact_efficiency')
                new_lines.append('            ')
                new_lines.append('        # Ensure minimum exit velocity for any contact')
                new_lines.append('        exit_velocity = max(exit_velocity, 15.0)  # Minimum 15 mph for any contact')
                skip_until_calculate = True
            elif skip_until_calculate and '# Calculate launch angle' in line:
                skip_until_calculate = False
                new_lines.append('')
                new_lines.append(line)
            elif not skip_until_calculate:
                new_lines.append(line)
                
        new_content = '\n'.join(new_lines)
    
    with open('batted_ball/contact.py', 'w') as f:
        f.write(new_content)
    
    print("Fixed contact.py!")

if __name__ == '__main__':
    fix_contact_file()