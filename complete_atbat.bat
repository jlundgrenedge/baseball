@echo off
setlocal EnableDelayedExpansion

REM Complete At-Bat Scenarios - Pitch + Collision + Trajectory
REM ===========================================================

:start
cls
echo.
echo ===============================================================
echo     COMPLETE AT-BAT SCENARIOS (Phases 1+2+3)
echo ===============================================================
echo.
echo Simulate complete at-bats from pitch to landing:
echo.
echo 1.  Fastball Home Run (94 mph pitch, good swing)
echo 2.  Changeup Fly Out (fooled by off-speed)
echo 3.  Curveball Pop-up (swing under the pitch)
echo 4.  Fastball Line Drive (perfect timing)
echo 5.  Breaking Ball Base Hit (stay back, go oppo)
echo 6.  Fastball Ground Ball (topped)
echo 7.  Pitcher's Duel (good pitch, weak contact)
echo 8.  Hitter's Count (groove fastball, crushed)
echo 9.  Two-Strike Curveball (fooled badly)
echo 10. Perfect At-Bat (all outcomes shown)
echo.
echo 0. Return to main menu
echo.

set /p "choice=Enter scenario number (0-10): "

if "%choice%"=="0" goto :end
if "%choice%"=="1" goto :hr_fastball
if "%choice%"=="2" goto :changeup_flyout
if "%choice%"=="3" goto :curve_popup
if "%choice%"=="4" goto :fb_liner
if "%choice%"=="5" goto :breaking_single
if "%choice%"=="6" goto :fb_grounder
if "%choice%"=="7" goto :pitchers_duel
if "%choice%"=="8" goto :hitters_count
if "%choice%"=="9" goto :two_strike_curve
if "%choice%"=="10" goto :perfect_atbat

echo Invalid choice. Please try again.
pause
goto :start

:hr_fastball
cls
echo.
echo ===============================================================
echo     FASTBALL HOME RUN
echo ===============================================================
echo.
python examples/validate_pitch.py > nul 2>&1
python -c "import sys; sys.path.insert(0, '.'); from batted_ball import PitchSimulator, create_fastball_4seam, ContactModel, BattedBallSimulator; print('\nSituation: 3-2 count, hitter sits fastball\n'); print('='*70); print('\nPHASE 3: PITCH'); print('-'*70); pitch_sim = PitchSimulator(); fastball = create_fastball_4seam(velocity=94.0); pitch_result = pitch_sim.simulate_at_batter(fastball, target_x=0.0, target_z=2.5); print(f'Pitch: {fastball.name}'); print(f'Location: Center of zone'); print(f'Velocity at plate: {pitch_result[\"pitch_speed\"]:.1f} mph'); print(f'Pitch angle: {pitch_result[\"pitch_angle\"]:.1f}°'); print(); print('PHASE 2: COLLISION'); print('-'*70); collision = ContactModel().full_collision(bat_speed_mph=72.0, pitch_speed_mph=pitch_result[\"pitch_speed\"], bat_path_angle_deg=28.0, pitch_trajectory_angle_deg=pitch_result[\"pitch_angle\"], vertical_contact_offset_inches=-0.5, distance_from_sweet_spot_inches=0.0); print(f'Bat speed: 72 mph (good swing)'); print(f'Contact: Sweet spot, slight undercut'); print(f'Exit velocity: {collision[\"exit_velocity\"]:.1f} mph'); print(f'Launch angle: {collision[\"launch_angle\"]:.1f}°'); print(f'Backspin: {collision[\"backspin_rpm\"]:.0f} rpm'); print(f'COR: {collision[\"cor\"]:.3f}'); print(); print('PHASE 1: TRAJECTORY'); print('-'*70); traj = BattedBallSimulator().simulate(collision['exit_velocity'], collision['launch_angle'], backspin_rpm=collision['backspin_rpm']); print(f'Distance: {traj.distance:.1f} feet'); print(f'Flight time: {traj.flight_time:.2f} seconds'); print(f'Peak height: {traj.peak_height:.1f} feet'); print(); print('='*70); if traj.distance >= 400: print('\n💥 CRUSHED! MONSTER HOME RUN!'); elif traj.distance >= 350: print('\n🚀 HOME RUN! No doubt about it!'); else: print('\n⚾ Warning track power'); print('='*70);"
echo.
pause
goto :start

:changeup_flyout
cls
echo.
echo ===============================================================
echo     CHANGEUP FLY OUT
echo ===============================================================
echo.
python -c "import sys; sys.path.insert(0, '.'); from batted_ball import PitchSimulator, create_changeup, ContactModel, BattedBallSimulator; print('\nSituation: Hitter expects fastball, gets changeup\n'); print('='*70); print('\nPHASE 3: PITCH'); print('-'*70); pitch_sim = PitchSimulator(); changeup = create_changeup(velocity=83.0); pitch_result = pitch_sim.simulate_at_batter(changeup, target_x=0.0, target_z=2.5); print(f'Pitch: {changeup.name}'); print(f'Velocity at plate: {pitch_result[\"pitch_speed\"]:.1f} mph (10 mph slower!)'); print(f'Hitter is fooled, starts swing early'); print(); print('PHASE 2: COLLISION'); print('-'*70); collision = ContactModel().full_collision(bat_speed_mph=65.0, pitch_speed_mph=pitch_result[\"pitch_speed\"], bat_path_angle_deg=28.0, pitch_trajectory_angle_deg=pitch_result[\"pitch_angle\"], vertical_contact_offset_inches=0.0, distance_from_sweet_spot_inches=1.5); print(f'Bat speed: 65 mph (off-balance)'); print(f'Contact: 1.5\" from sweet spot (not barreled)'); print(f'Exit velocity: {collision[\"exit_velocity\"]:.1f} mph'); print(f'Launch angle: {collision[\"launch_angle\"]:.1f}°'); print(); print('PHASE 1: TRAJECTORY'); print('-'*70); traj = BattedBallSimulator().simulate(collision['exit_velocity'], collision['launch_angle'], backspin_rpm=collision['backspin_rpm']); print(f'Distance: {traj.distance:.1f} feet'); print(f'Flight time: {traj.flight_time:.2f} seconds'); print(); print('='*70); print('\n⚾ Routine fly ball - OUT'); print('   Changeup worked perfectly!'); print('='*70);"
echo.
pause
goto :start

:curve_popup
cls
echo.
echo ===============================================================
echo     CURVEBALL POP-UP
echo ===============================================================
echo.
python -c "import sys; sys.path.insert(0, '.'); from batted_ball import PitchSimulator, create_curveball, ContactModel, BattedBallSimulator; print('\nSituation: Hitter swings under 12-6 curveball\n'); print('='*70); print('\nPHASE 3: PITCH'); print('-'*70); pitch_sim = PitchSimulator(); curve = create_curveball(velocity=77.0); pitch_result = pitch_sim.simulate_at_batter(curve, target_x=0.0, target_z=1.8); print(f'Pitch: {curve.name}'); print(f'Velocity at plate: {pitch_result[\"pitch_speed\"]:.1f} mph'); print(f'Big 12-6 drop - hitter swings over it'); print(); print('PHASE 2: COLLISION'); print('-'*70); collision = ContactModel().full_collision(bat_speed_mph=68.0, pitch_speed_mph=pitch_result[\"pitch_speed\"], bat_path_angle_deg=25.0, pitch_trajectory_angle_deg=pitch_result[\"pitch_angle\"], vertical_contact_offset_inches=-1.5, distance_from_sweet_spot_inches=0.5); print(f'Bat speed: 68 mph'); print(f'Contact: 1.5\" below center (way under)'); print(f'Exit velocity: {collision[\"exit_velocity\"]:.1f} mph'); print(f'Launch angle: {collision[\"launch_angle\"]:.1f}° (too high!)'); print(); print('PHASE 1: TRAJECTORY'); print('-'*70); traj = BattedBallSimulator().simulate(collision['exit_velocity'], collision['launch_angle'], backspin_rpm=collision['backspin_rpm']); print(f'Distance: {traj.distance:.1f} feet'); print(f'Peak height: {traj.peak_height:.1f} feet'); print(f'Flight time: {traj.flight_time:.2f} seconds'); print(); print('='*70); print('\n⚾ HIGH POP-UP - Infield fly'); print('   Pitcher wins the battle!'); print('='*70);"
echo.
pause
goto :start

:fb_liner
cls
echo.
echo ===============================================================
echo     FASTBALL LINE DRIVE
echo ===============================================================
echo.
python -c "import sys; sys.path.insert(0, '.'); from batted_ball import PitchSimulator, create_fastball_4seam, ContactModel, BattedBallSimulator; print('\nSituation: Perfect timing on fastball\n'); print('='*70); print('\nPHASE 3: PITCH'); print('-'*70); pitch_sim = PitchSimulator(); fastball = create_fastball_4seam(velocity=93.0); pitch_result = pitch_sim.simulate_at_batter(fastball, target_x=0.0, target_z=2.8); print(f'Pitch: {fastball.name}'); print(f'Velocity at plate: {pitch_result[\"pitch_speed\"]:.1f} mph'); print(); print('PHASE 2: COLLISION'); print('-'*70); collision = ContactModel().full_collision(bat_speed_mph=70.0, pitch_speed_mph=pitch_result[\"pitch_speed\"], bat_path_angle_deg=15.0, pitch_trajectory_angle_deg=pitch_result[\"pitch_angle\"], vertical_contact_offset_inches=0.0, distance_from_sweet_spot_inches=0.0); print(f'Bat speed: 70 mph (perfect timing)'); print(f'Contact: SWEET SPOT, level swing'); print(f'Exit velocity: {collision[\"exit_velocity\"]:.1f} mph'); print(f'Launch angle: {collision[\"launch_angle\"]:.1f}° (line drive!)'); print(); print('PHASE 1: TRAJECTORY'); print('-'*70); traj = BattedBallSimulator().simulate(collision['exit_velocity'], collision['launch_angle'], backspin_rpm=collision['backspin_rpm']); print(f'Distance: {traj.distance:.1f} feet'); print(f'Peak height: {traj.peak_height:.1f} feet (low)'); print(f'Flight time: {traj.flight_time:.2f} seconds'); print(); print('='*70); if traj.distance >= 250: print('\n💪 SCORCHING LINE DRIVE! Base hit!'); else: print('\n⚾ Line drive - likely a hit'); print('='*70);"
echo.
pause
goto :start

:breaking_single
cls
echo.
echo ===============================================================
echo     BREAKING BALL BASE HIT
echo ===============================================================
echo.
python -c "import sys; sys.path.insert(0, '.'); from batted_ball import PitchSimulator, create_slider, ContactModel, BattedBallSimulator; print('\nSituation: Stay back on slider, go opposite field\n'); print('='*70); print('\nPHASE 3: PITCH'); print('-'*70); pitch_sim = PitchSimulator(); slider = create_slider(velocity=85.0); pitch_result = pitch_sim.simulate_at_batter(slider, target_x=-0.3, target_z=2.5); print(f'Pitch: {slider.name}'); print(f'Velocity at plate: {pitch_result[\"pitch_speed\"]:.1f} mph'); print(f'Breaking away from hitter'); print(); print('PHASE 2: COLLISION'); print('-'*70); collision = ContactModel().full_collision(bat_speed_mph=68.0, pitch_speed_mph=pitch_result[\"pitch_speed\"], bat_path_angle_deg=18.0, pitch_trajectory_angle_deg=pitch_result[\"pitch_angle\"], vertical_contact_offset_inches=0.0, distance_from_sweet_spot_inches=0.5); print(f'Bat speed: 68 mph (stayed back)'); print(f'Contact: Slightly off sweet spot'); print(f'Exit velocity: {collision[\"exit_velocity\"]:.1f} mph'); print(f'Launch angle: {collision[\"launch_angle\"]:.1f}°'); print(); print('PHASE 1: TRAJECTORY'); print('-'*70); traj = BattedBallSimulator().simulate(collision['exit_velocity'], collision['launch_angle'], spray_angle=-20.0, backspin_rpm=collision['backspin_rpm']); print(f'Distance: {traj.distance:.1f} feet'); print(f'Direction: Opposite field'); print(f'Flight time: {traj.flight_time:.2f} seconds'); print(); print('='*70); print('\n⚾ Opposite field base hit!'); print('   Good hitting approach!'); print('='*70);"
echo.
pause
goto :start

:fb_grounder
cls
echo.
echo ===============================================================
echo     FASTBALL GROUND BALL
echo ===============================================================
echo.
python -c "import sys; sys.path.insert(0, '.'); from batted_ball import PitchSimulator, create_fastball_4seam, ContactModel, BattedBallSimulator; print('\nSituation: Topped fastball\n'); print('='*70); print('\nPHASE 3: PITCH'); print('-'*70); pitch_sim = PitchSimulator(); fastball = create_fastball_4seam(velocity=92.0); pitch_result = pitch_sim.simulate_at_batter(fastball, target_x=0.0, target_z=2.2); print(f'Pitch: {fastball.name}'); print(f'Velocity at plate: {pitch_result[\"pitch_speed\"]:.1f} mph'); print(); print('PHASE 2: COLLISION'); print('-'*70); collision = ContactModel().full_collision(bat_speed_mph=70.0, pitch_speed_mph=pitch_result[\"pitch_speed\"], bat_path_angle_deg=20.0, pitch_trajectory_angle_deg=pitch_result[\"pitch_angle\"], vertical_contact_offset_inches=1.2, distance_from_sweet_spot_inches=0.0); print(f'Bat speed: 70 mph'); print(f'Contact: 1.2\" ABOVE center (topped!)'); print(f'Exit velocity: {collision[\"exit_velocity\"]:.1f} mph'); print(f'Launch angle: {collision[\"launch_angle\"]:.1f}° (ground ball)'); print(); print('PHASE 1: TRAJECTORY'); print('-'*70); traj = BattedBallSimulator().simulate(collision['exit_velocity'], collision['launch_angle'], backspin_rpm=collision['backspin_rpm']); print(f'Distance: {traj.distance:.1f} feet'); print(f'Peak height: {traj.peak_height:.1f} feet'); print(); print('='*70); if collision['launch_angle'] < 5: print('\n⚾ GROUND BALL to infield'); elif collision['launch_angle'] < 15: print('\n⚾ Hard ground ball - might get through'); print('='*70);"
echo.
pause
goto :start

:pitchers_duel
cls
echo.
echo ===============================================================
echo     PITCHER'S DUEL
echo ===============================================================
echo.
python -c "import sys; sys.path.insert(0, '.'); from batted_ball import PitchSimulator, create_fastball_4seam, ContactModel, BattedBallSimulator; print('\nSituation: Great pitch on corner, weak contact\n'); print('='*70); print('\nPHASE 3: PITCH'); print('-'*70); pitch_sim = PitchSimulator(); fastball = create_fastball_4seam(velocity=95.0); pitch_result = pitch_sim.simulate_at_batter(fastball, target_x=0.65, target_z=3.3); print(f'Pitch: {fastball.name}'); print(f'Velocity at plate: {pitch_result[\"pitch_speed\"]:.1f} mph'); print(f'Location: High and away (tough pitch!)'); print(); print('PHASE 2: COLLISION'); print('-'*70); collision = ContactModel().full_collision(bat_speed_mph=62.0, pitch_speed_mph=pitch_result[\"pitch_speed\"], bat_path_angle_deg=28.0, pitch_trajectory_angle_deg=pitch_result[\"pitch_angle\"], vertical_contact_offset_inches=0.5, distance_from_sweet_spot_inches=2.5); print(f'Bat speed: 62 mph (reaching)'); print(f'Contact: 2.5\" from sweet spot'); print(f'Exit velocity: {collision[\"exit_velocity\"]:.1f} mph (weak)'); print(f'Launch angle: {collision[\"launch_angle\"]:.1f}°'); print(); print('PHASE 1: TRAJECTORY'); print('-'*70); traj = BattedBallSimulator().simulate(collision['exit_velocity'], collision['launch_angle'], backspin_rpm=collision['backspin_rpm']); print(f'Distance: {traj.distance:.1f} feet'); print(); print('='*70); print('\n⚾ Weak fly ball - easy out'); print('   Pitcher executed perfectly!'); print('='*70);"
echo.
pause
goto :start

:hitters_count
cls
echo.
echo ===============================================================
echo     HITTER'S COUNT (3-1, Groove Fastball)
echo ===============================================================
echo.
python -c "import sys; sys.path.insert(0, '.'); from batted_ball import PitchSimulator, create_fastball_4seam, ContactModel, BattedBallSimulator; print('\nSituation: 3-1 count, pitcher grooves fastball\n'); print('='*70); print('\nPHASE 3: PITCH'); print('-'*70); pitch_sim = PitchSimulator(); fastball = create_fastball_4seam(velocity=91.0); pitch_result = pitch_sim.simulate_at_batter(fastball, target_x=0.0, target_z=2.5); print(f'Pitch: {fastball.name}'); print(f'Velocity at plate: {pitch_result[\"pitch_speed\"]:.1f} mph'); print(f'Location: RIGHT DOWN THE MIDDLE'); print(); print('PHASE 2: COLLISION'); print('-'*70); collision = ContactModel().full_collision(bat_speed_mph=76.0, pitch_speed_mph=pitch_result[\"pitch_speed\"], bat_path_angle_deg=27.0, pitch_trajectory_angle_deg=pitch_result[\"pitch_angle\"], vertical_contact_offset_inches=-0.3, distance_from_sweet_spot_inches=0.0); print(f'Bat speed: 76 mph (AGGRESSIVE, on time)'); print(f'Contact: SWEET SPOT BARREL'); print(f'Exit velocity: {collision[\"exit_velocity\"]:.1f} mph'); print(f'Launch angle: {collision[\"launch_angle\"]:.1f}°'); print(f'COR: {collision[\"cor\"]:.3f} (maximum)'); print(); print('PHASE 1: TRAJECTORY'); print('-'*70); traj = BattedBallSimulator().simulate(collision['exit_velocity'], collision['launch_angle'], backspin_rpm=collision['backspin_rpm']); print(f'Distance: {traj.distance:.1f} feet'); print(f'Flight time: {traj.flight_time:.2f} seconds'); print(f'Peak height: {traj.peak_height:.1f} feet'); print(); print('='*70); if traj.distance >= 450: print('\n💥💥💥 ABSOLUTELY CRUSHED!!!'); print('   TAPE MEASURE HOME RUN!'); elif traj.distance >= 400: print('\n🚀🚀 MONSTER HOME RUN!'); elif traj.distance >= 350: print('\n🚀 HOME RUN!'); print('='*70);"
echo.
pause
goto :start

:two_strike_curve
cls
echo.
echo ===============================================================
echo     TWO-STRIKE CURVEBALL
echo ===============================================================
echo.
python -c "import sys; sys.path.insert(0, '.'); from batted_ball import PitchSimulator, create_curveball, ContactModel, BattedBallSimulator; print('\nSituation: 0-2 count, chasing curve in dirt\n'); print('='*70); print('\nPHASE 3: PITCH'); print('-'*70); pitch_sim = PitchSimulator(); curve = create_curveball(velocity=76.0); pitch_result = pitch_sim.simulate_at_batter(curve, target_x=0.0, target_z=1.2); print(f'Pitch: {curve.name}'); print(f'Velocity at plate: {pitch_result[\"pitch_speed\"]:.1f} mph'); print(f'Location: BELOW ZONE (ball in dirt!)'); print(); print('PHASE 2: COLLISION'); print('-'*70); collision = ContactModel().full_collision(bat_speed_mph=70.0, pitch_speed_mph=pitch_result[\"pitch_speed\"], bat_path_angle_deg=10.0, pitch_trajectory_angle_deg=pitch_result[\"pitch_angle\"], vertical_contact_offset_inches=-2.0, distance_from_sweet_spot_inches=3.0); print(f'Bat speed: 70 mph (protective swing)'); print(f'Contact: Horrible - way under, off handle'); print(f'Exit velocity: {collision[\"exit_velocity\"]:.1f} mph'); print(f'Launch angle: {collision[\"launch_angle\"]:.1f}°'); print(); print('PHASE 1: TRAJECTORY'); print('-'*70); traj = BattedBallSimulator().simulate(collision['exit_velocity'], collision['launch_angle'], backspin_rpm=collision['backspin_rpm']); print(f'Distance: {traj.distance:.1f} feet'); print(); print('='*70); print('\n⚾ Weak dribbler - easy out'); print('   Chased a pitch in the dirt!'); print('='*70);"
echo.
pause
goto :start

:perfect_atbat
cls
echo.
echo ===============================================================
echo     PERFECT AT-BAT ANALYSIS
echo ===============================================================
echo.
python -c "import sys; sys.path.insert(0, '.'); from batted_ball import PitchSimulator, create_fastball_4seam, ContactModel, BattedBallSimulator; print('\nAnalyzing same pitch with different swings:\n'); print('='*70); pitch_sim = PitchSimulator(); fastball = create_fastball_4seam(velocity=93.0); pitch_result = pitch_sim.simulate_at_batter(fastball, target_x=0.0, target_z=2.5); print(f'\nPITCH: 93 mph Fastball, center of zone'); print(f'Velocity at plate: {pitch_result[\"pitch_speed\"]:.1f} mph'); print(); print('='*70); scenarios = [('Perfect Barrel', 72.0, 28.0, 0.0, 0.0), ('Late Swing', 65.0, 28.0, 0.0, 1.5), ('Topped', 70.0, 20.0, 1.0, 0.0), ('Under', 70.0, 30.0, -1.0, 0.0)]; for name, bat_spd, angle, v_off, sweet_off in scenarios: coll = ContactModel().full_collision(bat_spd, pitch_result['pitch_speed'], angle, vertical_contact_offset_inches=v_off, distance_from_sweet_spot_inches=sweet_off); traj = BattedBallSimulator().simulate(coll['exit_velocity'], coll['launch_angle'], backspin_rpm=coll['backspin_rpm']); print(f'\n{name}:'); print(f'  Bat: {bat_spd} mph, Contact: {sweet_off:.1f}\" from sweet'); print(f'  Exit: {coll[\"exit_velocity\"]:.1f} mph @ {coll[\"launch_angle\"]:.1f}°'); print(f'  Distance: {traj.distance:.1f} ft'); print('='*70); print('\n💡 Same pitch, vastly different outcomes!'); print('   Timing and contact quality are everything.'); print('='*70);"
echo.
pause
goto :start

:end
echo.
