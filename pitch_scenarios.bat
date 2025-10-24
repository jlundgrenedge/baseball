@echo off
setlocal EnableDelayedExpansion

REM Baseball Pitch Trajectory Scenarios - Phase 3
REM =============================================

:start
cls
echo.
echo ===============================================================
echo     PITCH TRAJECTORY SCENARIOS (Phase 3)
echo ===============================================================
echo.
echo Choose a pitch scenario:
echo.
echo 1.  Fastball (93 mph, 4-seam, high spin)
echo 2.  Curveball (77 mph, 12-6 break)
echo 3.  Slider (85 mph, sharp horizontal break)
echo 4.  Changeup (83 mph, fading action)
echo 5.  2-Seam Fastball (91 mph, sinker)
echo 6.  Splitter (90 mph, tumbling action)
echo 7.  Pitch Comparison (All pitch types)
echo 8.  Strike Zone Test (Different locations)
echo 9.  Velocity Comparison (93 vs 99 mph fastball)
echo 10. Perfect Pitch to Hit (center of zone)
echo.
echo 0. Return to main menu
echo.

set /p "choice=Enter scenario number (0-10): "

if "%choice%"=="0" goto :end
if "%choice%"=="1" goto :fastball
if "%choice%"=="2" goto :curveball
if "%choice%"=="3" goto :slider
if "%choice%"=="4" goto :changeup
if "%choice%"=="5" goto :two_seam
if "%choice%"=="6" goto :splitter
if "%choice%"=="7" goto :comparison
if "%choice%"=="8" goto :strike_zone
if "%choice%"=="9" goto :velocity_comp
if "%choice%"=="10" goto :perfect_pitch

echo Invalid choice. Please try again.
pause
goto :start

:fastball
cls
echo.
echo ===============================================================
echo     4-SEAM FASTBALL
echo ===============================================================
echo.
python -c "import sys; sys.path.insert(0, '.'); from batted_ball import PitchSimulator, create_fastball_4seam; sim = PitchSimulator(); pitch = create_fastball_4seam(velocity=93.0); result = sim.simulate(pitch, target_x=0.0, target_z=2.5); print('\nPitch: 4-Seam Fastball\n'); print('='*70); print(f'Release velocity: {pitch.velocity:.1f} mph'); print(f'Spin rate: {pitch.spin_rpm:.0f} rpm'); print(f'Spin efficiency: {pitch.spin_efficiency:.0%}'); print(); print(f'At Home Plate:'); print(f'  Velocity: {result.plate_speed:.1f} mph'); print(f'  Flight time: {result.flight_time:.3f} sec'); print(f'  Location: ({result.plate_y:+.1f}\", {result.plate_z:.1f}\")'); print(f'  Vertical break: {result.vertical_break:+.1f}\"'); print(f'  Horizontal break: {result.horizontal_break:+.1f}\"'); print(f'  Total break: {result.total_break:.1f}\"'); strike = 'STRIKE ⚾' if result.is_strike else 'BALL'; print(f'  Call: {strike}'); print('='*70); print('\n💡 Fastball \"rises\" due to backspin (less drop than gravity)'); print('='*70);"
echo.
pause
goto :start

:curveball
cls
echo.
echo ===============================================================
echo     CURVEBALL (12-6)
echo ===============================================================
echo.
python -c "import sys; sys.path.insert(0, '.'); from batted_ball import PitchSimulator, create_curveball; sim = PitchSimulator(); pitch = create_curveball(velocity=77.0); result = sim.simulate(pitch, target_x=0.0, target_z=2.5); print('\nPitch: Curveball (12-6)\n'); print('='*70); print(f'Release velocity: {pitch.velocity:.1f} mph'); print(f'Spin rate: {pitch.spin_rpm:.0f} rpm (topspin)'); print(f'Spin efficiency: {pitch.spin_efficiency:.0%}'); print(); print(f'At Home Plate:'); print(f'  Velocity: {result.plate_speed:.1f} mph'); print(f'  Flight time: {result.flight_time:.3f} sec'); print(f'  Location: ({result.plate_y:+.1f}\", {result.plate_z:.1f}\")'); print(f'  Vertical break: {result.vertical_break:+.1f}\" (big drop!)'); print(f'  Horizontal break: {result.horizontal_break:+.1f}\"'); print(f'  Total break: {result.total_break:.1f}\"'); strike = 'STRIKE ⚾' if result.is_strike else 'BALL'; print(f'  Call: {strike}'); print('='*70); print('\n💡 Curveball drops sharply due to topspin'); print('='*70);"
echo.
pause
goto :start

:slider
cls
echo.
echo ===============================================================
echo     SLIDER
echo ===============================================================
echo.
python -c "import sys; sys.path.insert(0, '.'); from batted_ball import PitchSimulator, create_slider; sim = PitchSimulator(); pitch = create_slider(velocity=85.0); result = sim.simulate(pitch, target_x=0.0, target_z=2.5); print('\nPitch: Slider\n'); print('='*70); print(f'Release velocity: {pitch.velocity:.1f} mph'); print(f'Spin rate: {pitch.spin_rpm:.0f} rpm (gyro spin)'); print(f'Spin efficiency: {pitch.spin_efficiency:.0%}'); print(); print(f'At Home Plate:'); print(f'  Velocity: {result.plate_speed:.1f} mph'); print(f'  Flight time: {result.flight_time:.3f} sec'); print(f'  Location: ({result.plate_y:+.1f}\", {result.plate_z:.1f}\")'); print(f'  Vertical break: {result.vertical_break:+.1f}\"'); print(f'  Horizontal break: {result.horizontal_break:+.1f}\" (sharp!)'); print(f'  Total break: {result.total_break:.1f}\"'); strike = 'STRIKE ⚾' if result.is_strike else 'BALL'; print(f'  Call: {strike}'); print('='*70); print('\n💡 Slider has sharp horizontal break (glove-side)'); print('='*70);"
echo.
pause
goto :start

:changeup
cls
echo.
echo ===============================================================
echo     CHANGEUP
echo ===============================================================
echo.
python -c "import sys; sys.path.insert(0, '.'); from batted_ball import PitchSimulator, create_changeup; sim = PitchSimulator(); pitch = create_changeup(velocity=83.0); result = sim.simulate(pitch, target_x=0.0, target_z=2.5); print('\nPitch: Changeup\n'); print('='*70); print(f'Release velocity: {pitch.velocity:.1f} mph (10 mph slower than FB)'); print(f'Spin rate: {pitch.spin_rpm:.0f} rpm (low spin)'); print(f'Spin efficiency: {pitch.spin_efficiency:.0%}'); print(); print(f'At Home Plate:'); print(f'  Velocity: {result.plate_speed:.1f} mph'); print(f'  Flight time: {result.flight_time:.3f} sec'); print(f'  Location: ({result.plate_y:+.1f}\", {result.plate_z:.1f}\")'); print(f'  Vertical break: {result.vertical_break:+.1f}\" (drops)'); print(f'  Horizontal break: {result.horizontal_break:+.1f}\" (fades)'); print(f'  Total break: {result.total_break:.1f}\"'); strike = 'STRIKE ⚾' if result.is_strike else 'BALL'; print(f'  Call: {strike}'); print('='*70); print('\n💡 Changeup fades with arm-side movement'); print('='*70);"
echo.
pause
goto :start

:two_seam
cls
echo.
echo ===============================================================
echo     2-SEAM FASTBALL (Sinker)
echo ===============================================================
echo.
python -c "import sys; sys.path.insert(0, '.'); from batted_ball import PitchSimulator, create_fastball_2seam; sim = PitchSimulator(); pitch = create_fastball_2seam(velocity=91.5); result = sim.simulate(pitch, target_x=0.0, target_z=2.5); print('\nPitch: 2-Seam Fastball (Sinker)\n'); print('='*70); print(f'Release velocity: {pitch.velocity:.1f} mph'); print(f'Spin rate: {pitch.spin_rpm:.0f} rpm'); print(f'Spin efficiency: {pitch.spin_efficiency:.0%}'); print(); print(f'At Home Plate:'); print(f'  Velocity: {result.plate_speed:.1f} mph'); print(f'  Flight time: {result.flight_time:.3f} sec'); print(f'  Location: ({result.plate_y:+.1f}\", {result.plate_z:.1f}\")'); print(f'  Vertical break: {result.vertical_break:+.1f}\"'); print(f'  Horizontal break: {result.horizontal_break:+.1f}\" (arm-side run)'); print(f'  Total break: {result.total_break:.1f}\"'); strike = 'STRIKE ⚾' if result.is_strike else 'BALL'; print(f'  Call: {strike}'); print('='*70); print('\n💡 2-seamer has more horizontal movement than 4-seam'); print('='*70);"
echo.
pause
goto :start

:splitter
cls
echo.
echo ===============================================================
echo     SPLITTER (Split-Finger Fastball)
echo ===============================================================
echo.
python -c "import sys; sys.path.insert(0, '.'); from batted_ball import PitchSimulator, create_splitter; sim = PitchSimulator(); pitch = create_splitter(velocity=90.0); result = sim.simulate(pitch, target_x=0.0, target_z=2.0); print('\nPitch: Splitter\n'); print('='*70); print(f'Release velocity: {pitch.velocity:.1f} mph'); print(f'Spin rate: {pitch.spin_rpm:.0f} rpm (very low!)'); print(f'Spin efficiency: {pitch.spin_efficiency:.0%}'); print(); print(f'At Home Plate:'); print(f'  Velocity: {result.plate_speed:.1f} mph'); print(f'  Flight time: {result.flight_time:.3f} sec'); print(f'  Location: ({result.plate_y:+.1f}\", {result.plate_z:.1f}\")'); print(f'  Vertical break: {result.vertical_break:+.1f}\" (sharp drop!)'); print(f'  Horizontal break: {result.horizontal_break:+.1f}\"'); print(f'  Total break: {result.total_break:.1f}\"'); strike = 'STRIKE ⚾' if result.is_strike else 'BALL'; print(f'  Call: {strike}'); print('='*70); print('\n💡 Splitter tumbles with unpredictable late drop'); print('='*70);"
echo.
pause
goto :start

:comparison
cls
echo.
echo ===============================================================
echo     PITCH TYPE COMPARISON
echo ===============================================================
echo.
python -c "import sys; sys.path.insert(0, '.'); from batted_ball import PitchSimulator, create_fastball_4seam, create_curveball, create_slider, create_changeup; sim = PitchSimulator(); pitches = [(create_fastball_4seam(), 'Fastball'), (create_curveball(), 'Curveball'), (create_slider(), 'Slider'), (create_changeup(), 'Changeup')]; print('\nComparing All Pitch Types (targeted at center of zone):\n'); print('='*80); print(f'{'Pitch Type':<15} {'Release':<12} {'At Plate':<12} {'Flight':<10} {'V Break':<10} {'H Break':<10}'); print('-'*80); for pitch, name in pitches: result = sim.simulate(pitch, target_x=0.0, target_z=2.5); print(f'{name:<15} {pitch.velocity:>7.1f} mph {result.plate_speed:>8.1f} mph {result.flight_time:>6.3f} s {result.vertical_break:>7.1f}\" {result.horizontal_break:>7.1f}\"'); print('='*80); print('\nKey Observations:'); print('  - Fastball: High velocity, appears to \"rise\"'); print('  - Curveball: Big vertical drop, slowest pitch'); print('  - Slider: Sharp horizontal break'); print('  - Changeup: Similar to fastball but slower (fools timing)'); print('='*80);"
echo.
pause
goto :start

:strike_zone
cls
echo.
echo ===============================================================
echo     STRIKE ZONE TEST
echo ===============================================================
echo.
python -c "import sys; sys.path.insert(0, '.'); from batted_ball import PitchSimulator, create_fastball_4seam; sim = PitchSimulator(); pitch = create_fastball_4seam(); locations = [('Center', 0.0, 2.5), ('Low', 0.0, 1.5), ('High', 0.0, 3.5), ('Inside', 0.6, 2.5), ('Outside', -0.6, 2.5), ('Below zone', 0.0, 0.8), ('Above zone', 0.0, 4.2)]; print('\n93 mph Fastball to Different Locations:\n'); print('='*70); print(f'{'Target Location':<20} {'Actual Location':>20} {'Call':>12}'); print('-'*70); for name, x, z in locations: result = sim.simulate(pitch, target_x=x, target_z=z); call = 'STRIKE ⚾' if result.is_strike else 'BALL'; print(f'{name:<20} ({result.plate_y:+5.1f}\", {result.plate_z:4.1f}\") {call:>12}'); print('='*70); print('\n💡 Strike zone: 17\" wide x 1.5-3.5 ft high'); print('   Pitches move 5-12\" due to spin!'); print('='*70);"
echo.
pause
goto :start

:velocity_comp
cls
echo.
echo ===============================================================
echo     VELOCITY COMPARISON (93 vs 99 mph)
echo ===============================================================
echo.
python -c "import sys; sys.path.insert(0, '.'); from batted_ball import PitchSimulator, create_fastball_4seam; sim = PitchSimulator(); fb_93 = create_fastball_4seam(velocity=93.0); fb_99 = create_fastball_4seam(velocity=99.0); r_93 = sim.simulate(fb_93, target_x=0.0, target_z=2.5); r_99 = sim.simulate(fb_99, target_x=0.0, target_z=2.5); print('\nAverage MLB Fastball vs Elite Fastball:\n'); print('='*70); print('93 MPH FASTBALL (Average):'); print(f'  Velocity at plate: {r_93.plate_speed:.1f} mph'); print(f'  Flight time: {r_93.flight_time:.3f} sec'); print(f'  Vertical break: {r_93.vertical_break:+.1f}\"'); print(); print('99 MPH FASTBALL (Elite):'); print(f'  Velocity at plate: {r_99.plate_speed:.1f} mph'); print(f'  Flight time: {r_99.flight_time:.3f} sec'); print(f'  Vertical break: {r_99.vertical_break:+.1f}\"'); print(); print('='*70); time_diff = (r_93.flight_time - r_99.flight_time) * 1000; print(f'\nTime difference: {time_diff:.0f} milliseconds'); print(f'Batter has {time_diff:.0f} ms less to react to 99 mph fastball!'); print('='*70);"
echo.
pause
goto :start

:perfect_pitch
cls
echo.
echo ===============================================================
echo     PERFECT PITCH TO HIT
echo ===============================================================
echo.
python -c "import sys; sys.path.insert(0, '.'); from batted_ball import PitchSimulator, create_fastball_4seam; sim = PitchSimulator(); pitch = create_fastball_4seam(velocity=92.0); result = sim.simulate(pitch, target_x=0.0, target_z=2.5); print('\n92 mph Fastball down the middle:\n'); print('='*70); print('PITCH:'); print(f'  Type: {pitch.name}'); print(f'  Velocity: {pitch.velocity:.1f} mph'); print(f'  Spin: {pitch.spin_rpm:.0f} rpm'); print(); print('AT PLATE:'); print(f'  Velocity: {result.plate_speed:.1f} mph'); print(f'  Location: CENTER OF ZONE ({result.plate_y:+.1f}\", {result.plate_z:.1f}\")'); print(f'  Flight time: {result.flight_time:.3f} sec'); print(); print('='*70); print('\n⚾ HITTER\'S PITCH! Center-cut fastball'); print('   Perfect for hitting!'); print('\n💡 See collision_scenarios.bat to simulate hitting this pitch'); print('='*70);"
echo.
pause
goto :start

:end
echo.
