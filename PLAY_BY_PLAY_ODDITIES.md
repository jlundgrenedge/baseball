**FIRST BASEMAN ERROR - SHOULD HAVE BEEN HIT? PLUS RUNNER ADVANCED TO SECOND: PROBLEM WITH ERROR LOGIC**

Pete Crow-Armstrong batting against Freddy Peralta

&nbsp; Situation: empty, 0 out(s)



📊 PITCH #1: curveball (0-0) \[CODE: STRIKE\_TAKEN]

&nbsp;  Release: 85.4 mph, 2946 rpm

&nbsp;  Plate: 77.3 mph @ (+4.1", 27.3")

&nbsp;  Break: V=+15.6", H=+4.6"

&nbsp;  Zone: IN\_ZONE 🎯

&nbsp;  Intent: low-middle, middle (target: +1.0", 27.1")

&nbsp;  Result: Miss 3.1" arm-side (error: 3.1" H, 0.2" V, total 3.07")

&nbsp;  Outcome: called\_strike (taken)



⚾ BATTED BALL: LINE\_DRIVE

&nbsp;  EV: 79.9 mph, LA: 10.2°, Spray: -45.0°

&nbsp;  Spin: 114 rpm backspin, +520 rpm sidespin

&nbsp;  Contact Model Inputs:

&nbsp;    - Pitch speed: 77.1 mph

&nbsp;    - Collision efficiency (q): 0.066

&nbsp;    - Resulting EV: 79.9 mph

&nbsp;  Distance: 142.9 ft (apex: 9.3 ft)

&nbsp;  Hang time: 1.41 s

&nbsp;  Landing: (101.1, 101.0)

&nbsp;  Quality: MEDIUM

&nbsp;  Expected Stats: xBA=0.609, xSLG=0.853, xwOBA=0.743

&nbsp; Pitch sequence:

&nbsp;   #1: curveball 85.4->77.3 mph to (0.34', 2.27') \[0-0 -> 0-1] taken for strike

&nbsp;   ZoneBucket: UP\_AWAY

&nbsp;   OutcomeCodePitch: STRIKE\_TAKEN

&nbsp;   Fatigue:

&nbsp;     PitchCount: 1

&nbsp;     FatigueLevel: 0.00

&nbsp;     VelocityPenaltyMph: 0.0

&nbsp;     CommandPenaltyInches: 0.0

&nbsp;   SwingDecisionModel:

&nbsp;     EstimatedStrikeProb: 0.48

&nbsp;     EV\_Swing: -0.002

&nbsp;     EV\_Take: +0.002

&nbsp;     AggressionModifier: +0.04

&nbsp;     Decision: TAKE

&nbsp;   PitchIntent:

&nbsp;     IntentionCategory: strike\_looking

&nbsp;     IntendedZone: UP\_AWAY

&nbsp;     IntendedPitchType: curveball

&nbsp;     CommandError:

&nbsp;       XErrorInches: +3.1

&nbsp;       ZErrorInches: +0.2

&nbsp;   #2: curveball 85.4->77.1 mph to (-0.42', 2.93') \[0-1 -> 0-1] put in play (contact: weak, EV 79.9 mph, LA 10.2°)

&nbsp;   ZoneBucket: UP\_IN

&nbsp;   OutcomeCodePitch: INPLAY

&nbsp;   Fatigue:

&nbsp;     PitchCount: 2

&nbsp;     FatigueLevel: 0.01

&nbsp;     VelocityPenaltyMph: 0.0

&nbsp;     CommandPenaltyInches: 0.0

&nbsp;   SwingDecisionModel:

&nbsp;     EstimatedStrikeProb: 0.71

&nbsp;     EV\_Swing: +0.021

&nbsp;     EV\_Take: -0.021

&nbsp;     AggressionModifier: +0.04

&nbsp;     Decision: SWING

&nbsp;   PitchIntent:

&nbsp;     IntentionCategory: strike\_corner

&nbsp;     IntendedZone: UP\_IN

&nbsp;     IntendedPitchType: curveball

&nbsp;     CommandError:

&nbsp;       XErrorInches: +0.0

&nbsp;       ZErrorInches: +4.1

&nbsp; error

&nbsp;   Physics: EV=79.9 mph, LA=10.2°, Dist=142.9 ft, Hang=1.41s, Peak=9.3 ft, Contact: weak

&nbsp;   Pitch: curveball 77.1 mph at zone (-0.4', 2.9')

&nbsp; OutcomeCodePA: REACHED\_ON\_ERROR

&nbsp;   Play timeline:

&nbsp;     \[ 0.00s] Ball hit to shallow right outfield (contact)

&nbsp;     \[ 1.41s] ERROR! Diving attempt by first\_base, ball hit glove but dropped in shallow right outfield (E3) (fielding\_error)

&nbsp;     \[ 1.41s] FieldingPlayModel:

&nbsp; Fielder: Rhys Hoskins (1b)

&nbsp; ReactionTimeSec: 0.15

&nbsp; OptimalDistanceFt: 38.4

&nbsp; ActualDistanceFt: 38.4

&nbsp; RouteEfficiency: 1.00

&nbsp; RequiredSpeedFtPerSec: 30.6

&nbsp; MaxSpeedFtPerSec: 25.3

&nbsp; CatchProbability: 0.42

&nbsp; BallArrivalTime: 1.41

&nbsp; FielderArrivalTime: 1.53

&nbsp; MarginSec: -0.12

&nbsp; Outcome: ERROR (route\_efficiency)

&nbsp;     \[ 1.41s] WARNING: Required speed (30.6 ft/s) exceeds fielder max (25.3 ft/s) by >10% but outcome is ERROR (route\_efficiency\_warning)

&nbsp;     \[ 2.01s] Runner advances from first to second (runner\_advances\_to\_second)

&nbsp;     \[ 2.91s] Ball recovered by 1b after error at 2.91s (ball\_recovered)

&nbsp;     \[ 3.76s] Batter reaches first base on error (3.76s) (batter\_reaches\_first)

&nbsp;   Fielding breakdown:

&nbsp;     Rhys Hoskins: ball 1.41s, arrival 1.53s (margin -0.12s) -> missed

&nbsp;   Runners after play: Pete Crow-Armstrong on first, Pete Crow-Armstrong on second

