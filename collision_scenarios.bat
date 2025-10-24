@echo off
setlocal EnableDelayedExpansion

REM Baseball Collision Physics Scenarios - Phase 2
REM ==============================================

:start
cls
echo.
echo ===============================================================
echo     COLLISION PHYSICS SCENARIOS (Phase 2)
echo ===============================================================
echo.
echo Choose a collision scenario:
echo.
echo 1.  Sweet Spot vs Off-Center Comparison
echo 2.  Wood Bat vs Aluminum Bat
echo 3.  Perfect Barrel Contact (110 mph exit velocity)
echo 4.  Jammed Inside Pitch (broken bat contact)
echo 5.  Topped Ball (contact above center)
echo 6.  Undercut Ball (contact below center)
echo 7.  Fastball Contact (94 mph pitch, 70 mph bat)
echo 8.  Changeup Contact (83 mph pitch, 70 mph bat)
echo 9.  Slow Bat Speed (60 mph bat vs 92 mph pitch)
echo 10. Power Hitter (80 mph bat vs 95 mph pitch)
echo.
echo 0. Return to main menu
echo.

set /p "choice=Enter scenario number (0-10): "

if "%choice%"=="0" goto :end
if "%choice%"=="1" goto :sweet_spot_comparison
if "%choice%"=="2" goto :wood_vs_aluminum
if "%choice%"=="3" goto :perfect_barrel
if "%choice%"=="4" goto :jammed
if "%choice%"=="5" goto :topped
if "%choice%"=="6" goto :undercut
if "%choice%"=="7" goto :fastball_contact
if "%choice%"=="8" goto :changeup_contact
if "%choice%"=="9" goto :slow_bat
if "%choice%"=="10" goto :power_hitter

echo Invalid choice. Please try again.
pause
goto :start

:sweet_spot_comparison
cls
echo.
echo ===============================================================
echo     SWEET SPOT VS OFF-CENTER COMPARISON
echo ===============================================================
echo.
python -c "import sys; sys.path.insert(0, '.'); from batted_ball import ContactModel, BattedBallSimulator; from batted_ball.contact import ContactModel as CM; model = CM(bat_type='wood'); sim = BattedBallSimulator(); print('\nSame Swing, Different Contact Locations:\n'); print('Bat speed: 70 mph, Pitch speed: 90 mph, Bat angle: 28°\n'); print('='*70); locations = [('SWEET SPOT', 0.0), ('1 inch off', 1.0), ('2 inches off', 2.0), ('3 inches off (handle)', 3.0)]; results = []; for name, dist in locations: r = model.full_collision(70.0, 90.0, 28.0, distance_from_sweet_spot_inches=dist); traj = sim.simulate(r['exit_velocity'], r['launch_angle'], backspin_rpm=r['backspin_rpm']); results.append((name, r, traj)); print(f'\n{name}:'); print(f'  Exit velocity: {r[\"exit_velocity\"]:.1f} mph'); print(f'  COR: {r[\"cor\"]:.3f}'); print(f'  Vibration loss: {r[\"vibration_loss\"]:.1%}'); print(f'  Distance: {traj.distance:.1f} ft'); print('='*70); sweet_dist = results[0][2].distance; if len(results) > 1: print(f'\nSweet Spot Advantage:'); for i, (name, r, traj) in enumerate(results[1:]): loss = sweet_dist - traj.distance; print(f'  {name}: -{loss:.1f} ft ({loss/sweet_dist*100:.1f}%% reduction)');"
echo.
pause
goto :start

:wood_vs_aluminum
cls
echo.
echo ===============================================================
echo     WOOD BAT VS ALUMINUM BAT
echo ===============================================================
echo.
python -c "import sys; sys.path.insert(0, '.'); from batted_ball import ContactModel, BattedBallSimulator; sim = BattedBallSimulator(); print('\nHigh School Player (68 mph bat, 88 mph pitch):\n'); wood = ContactModel(bat_type='wood'); aluminum = ContactModel(bat_type='aluminum'); r_wood = wood.full_collision(68.0, 88.0, 27.0); r_alum = aluminum.full_collision(68.0, 88.0, 27.0); t_wood = sim.simulate(r_wood['exit_velocity'], r_wood['launch_angle'], backspin_rpm=r_wood['backspin_rpm']); t_alum = sim.simulate(r_alum['exit_velocity'], r_alum['launch_angle'], backspin_rpm=r_alum['backspin_rpm']); print('='*70); print('WOOD BAT:'); print(f'  Exit velocity: {r_wood[\"exit_velocity\"]:.1f} mph'); print(f'  COR: {r_wood[\"cor\"]:.3f}'); print(f'  Distance: {t_wood.distance:.1f} ft'); print(); print('ALUMINUM BAT:'); print(f'  Exit velocity: {r_alum[\"exit_velocity\"]:.1f} mph'); print(f'  COR: {r_alum[\"cor\"]:.3f}'); print(f'  Distance: {t_alum.distance:.1f} ft'); print(); print('='*70); diff_ev = r_alum['exit_velocity'] - r_wood['exit_velocity']; diff_dist = t_alum.distance - t_wood.distance; print(f'\nAluminum Bat Advantage:'); print(f'  Exit velocity: +{diff_ev:.1f} mph'); print(f'  Distance: +{diff_dist:.1f} ft'); print('='*70);"
echo.
pause
goto :start

:perfect_barrel
cls
echo.
echo ===============================================================
echo     PERFECT BARREL CONTACT
echo ===============================================================
echo.
python -c "import sys; sys.path.insert(0, '.'); from batted_ball import ContactModel, BattedBallSimulator; model = ContactModel(); sim = BattedBallSimulator(); print('\nElite Contact: 75 mph bat + 94 mph fastball\n'); print('='*70); r = model.full_collision(75.0, 94.0, 28.0, vertical_contact_offset_inches=-0.5, distance_from_sweet_spot_inches=0.0); traj = sim.simulate(r['exit_velocity'], r['launch_angle'], backspin_rpm=r['backspin_rpm']); print(f'\nCollision Results:'); print(f'  Exit velocity: {r[\"exit_velocity\"]:.1f} mph'); print(f'  Launch angle: {r[\"launch_angle\"]:.1f}°'); print(f'  Backspin: {r[\"backspin_rpm\"]:.0f} rpm'); print(f'  COR: {r[\"cor\"]:.3f}'); print(f'  Vibration loss: {r[\"vibration_loss\"]:.1%}'); print(); print(f'Trajectory Results:'); print(f'  Distance: {traj.distance:.1f} ft'); print(f'  Flight time: {traj.flight_time:.2f} sec'); print(f'  Peak height: {traj.peak_height:.1f} ft'); print('='*70); if traj.distance >= 400: print('\n🚀 MONSTER HOME RUN!'); elif traj.distance >= 350: print('\n⚾ HOME RUN!'); print('='*70);"
echo.
pause
goto :start

:jammed
cls
echo.
echo ===============================================================
echo     JAMMED INSIDE PITCH (Broken Bat)
echo ===============================================================
echo.
python -c "import sys; sys.path.insert(0, '.'); from batted_ball import ContactModel, BattedBallSimulator; model = ContactModel(); sim = BattedBallSimulator(); print('\n65 mph bat (late swing) + 96 mph fastball\nContact 4 inches from sweet spot (toward handle)\n'); print('='*70); r = model.full_collision(65.0, 96.0, 5.0, vertical_contact_offset_inches=1.0, distance_from_sweet_spot_inches=4.0); traj = sim.simulate(r['exit_velocity'], r['launch_angle'], backspin_rpm=r['backspin_rpm']); print(f'\nCollision Results:'); print(f'  Exit velocity: {r[\"exit_velocity\"]:.1f} mph (weak!)'); print(f'  Launch angle: {r[\"launch_angle\"]:.1f}°'); print(f'  Backspin: {r[\"backspin_rpm\"]:.0f} rpm'); print(f'  COR: {r[\"cor\"]:.3f} (poor)'); print(f'  Vibration loss: {r[\"vibration_loss\"]:.1%} (ouch!)'); print(); print(f'Trajectory Results:'); print(f'  Distance: {traj.distance:.1f} ft'); print(f'  Flight time: {traj.flight_time:.2f} sec'); print(f'  Peak height: {traj.peak_height:.1f} ft'); print('='*70); print('\n⚠️  Broken bat contact - weak popup or grounder'); print('='*70);"
echo.
pause
goto :start

:topped
cls
echo.
echo ===============================================================
echo     TOPPED BALL (Contact Above Center)
echo ===============================================================
echo.
python -c "import sys; sys.path.insert(0, '.'); from batted_ball import ContactModel, BattedBallSimulator; model = ContactModel(); sim = BattedBallSimulator(); print('\n70 mph bat + 90 mph pitch\nContact 1 inch above center\n'); print('='*70); r = model.full_collision(70.0, 90.0, 25.0, vertical_contact_offset_inches=1.0, distance_from_sweet_spot_inches=0.0); traj = sim.simulate(r['exit_velocity'], r['launch_angle'], backspin_rpm=r['backspin_rpm']); print(f'\nCollision Results:'); print(f'  Exit velocity: {r[\"exit_velocity\"]:.1f} mph'); print(f'  Launch angle: {r[\"launch_angle\"]:.1f}° (low!)'); print(f'  Backspin: {r[\"backspin_rpm\"]:.0f} rpm (reduced)'); print(); print(f'Trajectory Results:'); print(f'  Distance: {traj.distance:.1f} ft'); print(f'  Peak height: {traj.peak_height:.1f} ft'); print('='*70); if r['launch_angle'] < 10: print('\n⚾ Ground ball - likely infield out'); else: print('\n⚾ Line drive or weak fly'); print('='*70);"
echo.
pause
goto :start

:undercut
cls
echo.
echo ===============================================================
echo     UNDERCUT BALL (Contact Below Center)
echo ===============================================================
echo.
python -c "import sys; sys.path.insert(0, '.'); from batted_ball import ContactModel, BattedBallSimulator; model = ContactModel(); sim = BattedBallSimulator(); print('\n70 mph bat + 90 mph pitch\nContact 1 inch below center\n'); print('='*70); r = model.full_collision(70.0, 90.0, 25.0, vertical_contact_offset_inches=-1.0, distance_from_sweet_spot_inches=0.0); traj = sim.simulate(r['exit_velocity'], r['launch_angle'], backspin_rpm=r['backspin_rpm']); print(f'\nCollision Results:'); print(f'  Exit velocity: {r[\"exit_velocity\"]:.1f} mph'); print(f'  Launch angle: {r[\"launch_angle\"]:.1f}° (higher)'); print(f'  Backspin: {r[\"backspin_rpm\"]:.0f} rpm (increased)'); print(); print(f'Trajectory Results:'); print(f'  Distance: {traj.distance:.1f} ft'); print(f'  Peak height: {traj.peak_height:.1f} ft'); print('='*70); if traj.distance >= 350: print('\n🚀 Fly ball - potential home run!'); elif traj.distance >= 250: print('\n⚾ Deep fly ball'); else: print('\n⚾ Fly ball'); print('='*70);"
echo.
pause
goto :start

:fastball_contact
cls
echo.
echo ===============================================================
echo     FASTBALL CONTACT
echo ===============================================================
echo.
python -c "import sys; sys.path.insert(0, '.'); from batted_ball import ContactModel, BattedBallSimulator; model = ContactModel(); sim = BattedBallSimulator(); print('\n70 mph bat + 94 mph fastball (typical MLB at-bat)\n'); print('='*70); r = model.full_collision(70.0, 94.0, 28.0, distance_from_sweet_spot_inches=0.0); traj = sim.simulate(r['exit_velocity'], r['launch_angle'], backspin_rpm=r['backspin_rpm']); print(f'\nCollision Results:'); print(f'  Bat speed: 70 mph'); print(f'  Pitch speed: 94 mph'); print(f'  Exit velocity: {r[\"exit_velocity\"]:.1f} mph'); print(f'  Launch angle: {r[\"launch_angle\"]:.1f}°'); print(f'  Backspin: {r[\"backspin_rpm\"]:.0f} rpm'); print(); print(f'Trajectory Results:'); print(f'  Distance: {traj.distance:.1f} ft'); print(f'  Flight time: {traj.flight_time:.2f} sec'); print('='*70);"
echo.
pause
goto :start

:changeup_contact
cls
echo.
echo ===============================================================
echo     CHANGEUP CONTACT
echo ===============================================================
echo.
python -c "import sys; sys.path.insert(0, '.'); from batted_ball import ContactModel, BattedBallSimulator; model = ContactModel(); sim = BattedBallSimulator(); print('\n70 mph bat + 83 mph changeup (slower pitch)\n'); print('='*70); r = model.full_collision(70.0, 83.0, 28.0, distance_from_sweet_spot_inches=0.0); traj = sim.simulate(r['exit_velocity'], r['launch_angle'], backspin_rpm=r['backspin_rpm']); print(f'\nCollision Results:'); print(f'  Bat speed: 70 mph'); print(f'  Pitch speed: 83 mph (changeup)'); print(f'  Exit velocity: {r[\"exit_velocity\"]:.1f} mph'); print(f'  Launch angle: {r[\"launch_angle\"]:.1f}°'); print(f'  Backspin: {r[\"backspin_rpm\"]:.0f} rpm'); print(); print(f'Trajectory Results:'); print(f'  Distance: {traj.distance:.1f} ft'); print(f'  Flight time: {traj.flight_time:.2f} sec'); print('='*70); print('\n💡 Slower pitch = less exit velocity (~11 mph less than fastball)'); print('='*70);"
echo.
pause
goto :start

:slow_bat
cls
echo.
echo ===============================================================
echo     SLOW BAT SPEED (Late Swing)
echo ===============================================================
echo.
python -c "import sys; sys.path.insert(0, '.'); from batted_ball import ContactModel, BattedBallSimulator; model = ContactModel(); sim = BattedBallSimulator(); print('\n60 mph bat (late) + 92 mph fastball\n'); print('='*70); r = model.full_collision(60.0, 92.0, 28.0, distance_from_sweet_spot_inches=0.0); traj = sim.simulate(r['exit_velocity'], r['launch_angle'], backspin_rpm=r['backspin_rpm']); print(f'\nCollision Results:'); print(f'  Bat speed: 60 mph (late swing)'); print(f'  Pitch speed: 92 mph'); print(f'  Exit velocity: {r[\"exit_velocity\"]:.1f} mph'); print(f'  Launch angle: {r[\"launch_angle\"]:.1f}°'); print(); print(f'Trajectory Results:'); print(f'  Distance: {traj.distance:.1f} ft'); print('='*70); print('\n⚠️  Bat speed dominates - slow swing = weak contact'); print('='*70);"
echo.
pause
goto :start

:power_hitter
cls
echo.
echo ===============================================================
echo     POWER HITTER
echo ===============================================================
echo.
python -c "import sys; sys.path.insert(0, '.'); from batted_ball import ContactModel, BattedBallSimulator; model = ContactModel(); sim = BattedBallSimulator(); print('\n80 mph bat + 95 mph fastball (elite power)\n'); print('='*70); r = model.full_collision(80.0, 95.0, 28.0, vertical_contact_offset_inches=-0.5, distance_from_sweet_spot_inches=0.0); traj = sim.simulate(r['exit_velocity'], r['launch_angle'], backspin_rpm=r['backspin_rpm']); print(f'\nCollision Results:'); print(f'  Bat speed: 80 mph (elite)'); print(f'  Pitch speed: 95 mph'); print(f'  Exit velocity: {r[\"exit_velocity\"]:.1f} mph'); print(f'  Launch angle: {r[\"launch_angle\"]:.1f}°'); print(f'  Backspin: {r[\"backspin_rpm\"]:.0f} rpm'); print(); print(f'Trajectory Results:'); print(f'  Distance: {traj.distance:.1f} ft'); print(f'  Flight time: {traj.flight_time:.2f} sec'); print(f'  Peak height: {traj.peak_height:.1f} ft'); print('='*70); if traj.distance >= 450: print('\n💥 TAPE MEASURE SHOT! Upper deck!'); elif traj.distance >= 400: print('\n🚀 MONSTER HOME RUN!'); print('='*70);"
echo.
pause
goto :start

:end
echo.
