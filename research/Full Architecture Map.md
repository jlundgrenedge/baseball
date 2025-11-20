# Full Architecture Map

**Simulation Engine Overview:** The baseball simulation is organized
into modular subsystems that mimic the real game flow from pitch to
final play outcome. Below is a high-level map of the engine’s components
and how data flows through them in a single plate appearance:

- **GameSimulator (Game Loop):** Coordinates innings and at-bats. It
  selects the next batter/pitcher, calls the AtBat simulator, and
  updates game state (outs, score, base runners) after each
  result[\[1\]](https://github.com/jlundgrenedge/baseball/blob/2bf615c0de18cb7dbc2d4f8084c6e9afedea44b5/docs/GAME_SIMULATION_NOTES.md#L36-L44)[\[2\]](https://github.com/jlundgrenedge/baseball/blob/2bf615c0de18cb7dbc2d4f8084c6e9afedea44b5/batted_ball/game_simulation.py#L486-L495).
- **AtBatSimulator (Plate Appearance Engine):** Simulates one **at-bat**
  pitch-by-pitch. It integrates the pitcher and batter subsystems with
  physics models:
- **Pitch Selection & Command:** The pitcher chooses a pitch type and
  target location given the
  count[\[3\]](https://github.com/jlundgrenedge/baseball/blob/2bf615c0de18cb7dbc2d4f8084c6e9afedea44b5/batted_ball/at_bat.py#L846-L855).
  A pitch is thrown with realistic velocity, spin, and an *error* offset
  from the target based on the pitcher’s command
  rating[\[4\]](https://github.com/jlundgrenedge/baseball/blob/2bf615c0de18cb7dbc2d4f8084c6e9afedea44b5/batted_ball/at_bat.py#L496-L505)[\[5\]](https://github.com/jlundgrenedge/baseball/blob/2bf615c0de18cb7dbc2d4f8084c6e9afedea44b5/batted_ball/at_bat.py#L559-L568).
  The pitch trajectory is computed (including gravity and break) and a
  final location at the plate is
  obtained[\[6\]](https://github.com/jlundgrenedge/baseball/blob/2bf615c0de18cb7dbc2d4f8084c6e9afedea44b5/batted_ball/at_bat.py#L852-L861)[\[7\]](https://github.com/jlundgrenedge/baseball/blob/2bf615c0de18cb7dbc2d4f8084c6e9afedea44b5/batted_ball/at_bat.py#L570-L578).
- **Batter Decision:** As the pitch comes in, the batter decides whether
  to swing. This uses the **Batter Decision System** (zone discipline
  and swing aggressiveness) based on pitch location, type, velocity, and
  the
  count[\[8\]](https://github.com/jlundgrenedge/baseball/blob/2bf615c0de18cb7dbc2d4f8084c6e9afedea44b5/batted_ball/player.py#L630-L639)[\[9\]](https://github.com/jlundgrenedge/baseball/blob/2bf615c0de18cb7dbc2d4f8084c6e9afedea44b5/batted_ball/player.py#L656-L665).
  For strikes, baseline swing probability ~75% (higher in the zone
  center) and for balls, a lower “chase” probability decays with
  distance from the
  zone[\[8\]](https://github.com/jlundgrenedge/baseball/blob/2bf615c0de18cb7dbc2d4f8084c6e9afedea44b5/batted_ball/player.py#L630-L639)[\[10\]](https://github.com/jlundgrenedge/baseball/blob/2bf615c0de18cb7dbc2d4f8084c6e9afedea44b5/batted_ball/player.py#L648-L657).
  Batter attributes modulate this: good discipline lowers chase odds and
  slightly lowers in-zone
  swing%[\[9\]](https://github.com/jlundgrenedge/baseball/blob/2bf615c0de18cb7dbc2d4f8084c6e9afedea44b5/batted_ball/player.py#L656-L665),
  reaction speed affects overall swing
  frequency[\[11\]](https://github.com/jlundgrenedge/baseball/blob/2bf615c0de18cb7dbc2d4f8084c6e9afedea44b5/batted_ball/player.py#L670-L679),
  pitch type and count further adjust the swing chance (e.g. more swings
  with 2 strikes, fewer with 3
  balls)[\[12\]](https://github.com/jlundgrenedge/baseball/blob/2bf615c0de18cb7dbc2d4f8084c6e9afedea44b5/batted_ball/player.py#L696-L704).
- **Pitch Outcome:** If the batter **does not swing**, the pitch is
  either a called strike or a ball, and the count is
  updated[\[13\]](https://github.com/jlundgrenedge/baseball/blob/2bf615c0de18cb7dbc2d4f8084c6e9afedea44b5/batted_ball/at_bat.py#L908-L917).
  If the batter **swings**, the **Contact & Whiff Model** runs:
  - **Contact vs. Whiff:** A probability of missing (whiffing) is
    calculated based on pitch characteristics and batter
    skill[\[14\]](https://github.com/jlundgrenedge/baseball/blob/2bf615c0de18cb7dbc2d4f8084c6e9afedea44b5/batted_ball/at_bat.py#L612-L620)[\[15\]](https://github.com/jlundgrenedge/baseball/blob/2bf615c0de18cb7dbc2d4f8084c6e9afedea44b5/batted_ball/at_bat.py#L628-L636).
    This uses a **base whiff rate** by pitch type (e.g. ~20% for
    fastballs, ~35% for sliders) adjusted for pitch velocity (harder
    throws = more whiffs) and pitch
    movement[\[16\]](https://github.com/jlundgrenedge/baseball/blob/2bf615c0de18cb7dbc2d4f8084c6e9afedea44b5/batted_ball/player.py#L862-L871)[\[17\]](https://github.com/jlundgrenedge/baseball/blob/2bf615c0de18cb7dbc2d4f8084c6e9afedea44b5/batted_ball/player.py#L883-L891).
    Critically, the batter’s **contact ability** influences this via
    their barrel accuracy: smaller timing/aim error = lower whiff
    chance[\[18\]](https://github.com/jlundgrenedge/baseball/blob/2bf615c0de18cb7dbc2d4f8084c6e9afedea44b5/batted_ball/player.py#L892-L901).
    (In the current model, elite hitters with ~5 mm barrel error get a
    ~0.80× whiff multiplier, poor hitters ~1.6×, after recent
    recalibration[\[19\]](https://github.com/jlundgrenedge/baseball/blob/2bf615c0de18cb7dbc2d4f8084c6e9afedea44b5/MLB_REALISM_FIXES_2025-11-20.md#L55-L63)[\[20\]](https://github.com/jlundgrenedge/baseball/blob/2bf615c0de18cb7dbc2d4f8084c6e9afedea44b5/batted_ball/player.py#L893-L901).)
    The pitcher can also contribute a “stuff” multiplier if they have an
    exceptionally nasty
    pitch[\[21\]](https://github.com/jlundgrenedge/baseball/blob/2bf615c0de18cb7dbc2d4f8084c6e9afedea44b5/batted_ball/at_bat.py#L620-L626)[\[22\]](https://github.com/jlundgrenedge/baseball/blob/2bf615c0de18cb7dbc2d4f8084c6e9afedea44b5/batted_ball/player.py#L259-L268).
    If a random draw falls below the final whiff probability, the swing
    misses – a **swinging
    strike**[\[15\]](https://github.com/jlundgrenedge/baseball/blob/2bf615c0de18cb7dbc2d4f8084c6e9afedea44b5/batted_ball/at_bat.py#L628-L636)[\[23\]](https://github.com/jlundgrenedge/baseball/blob/2bf615c0de18cb7dbc2d4f8084c6e9afedea44b5/batted_ball/at_bat.py#L928-L936).
  - **Bat–Ball Collision:** If contact is not missed, the bat-ball
    physics are simulated. The batter’s swing brings in their **bat
    speed** (mapped from a power attribute, e.g. ~75 mph average for 50k
    rating)[\[24\]](https://github.com/jlundgrenedge/baseball/blob/2bf615c0de18cb7dbc2d4f8084c6e9afedea44b5/batted_ball/attributes.py#L140-L149)
    and swing angle. The pitch’s incoming speed and downward trajectory
    are known. The **Contact Model** computes the outcome of the
    collision: exit velocity, launch angle, spin, and
    direction[\[25\]](https://github.com/jlundgrenedge/baseball/blob/2bf615c0de18cb7dbc2d4f8084c6e9afedea44b5/batted_ball/at_bat.py#L644-L652)[\[26\]](https://github.com/jlundgrenedge/baseball/blob/2bf615c0de18cb7dbc2d4f8084c6e9afedea44b5/batted_ball/at_bat.py#L676-L684).
    It uses a physics formula **Batted Ball Speed = q \* pitch_speed +
    (1+q) \* bat_speed**, where *q* is an effective collision
    efficiency[\[27\]](https://github.com/jlundgrenedge/baseball/blob/2bf615c0de18cb7dbc2d4f8084c6e9afedea44b5/MLB_REALISM_FIXES_2025-11-20.md#L94-L102).
    This *q* starts from a base bat coefficient (wood ~0.13 in v1) and
    is reduced by any off-center miss on the barrel (barrel accuracy and
    timing
    errors)[\[28\]](https://github.com/jlundgrenedge/baseball/blob/2bf615c0de18cb7dbc2d4f8084c6e9afedea44b5/MLB_REALISM_FIXES_2025-11-20.md#L96-L104)[\[29\]](https://github.com/jlundgrenedge/baseball/blob/2bf615c0de18cb7dbc2d4f8084c6e9afedea44b5/batted_ball/contact.py#L546-L555).
    For example, previously q≈0.09 yielded ~90 mph exits on 90 mph
    pitches[\[27\]](https://github.com/jlundgrenedge/baseball/blob/2bf615c0de18cb7dbc2d4f8084c6e9afedea44b5/MLB_REALISM_FIXES_2025-11-20.md#L94-L102).
    After recent tuning, q was increased to ~0.14 to boost exit speeds
    (discussed
    later)[\[30\]](https://github.com/jlundgrenedge/baseball/blob/2bf615c0de18cb7dbc2d4f8084c6e9afedea44b5/MLB_REALISM_FIXES_2025-11-20.md#L116-L124).
    The model also adjusts launch angle based on where on the ball the
    bat strikes (hitting below center adds loft/backspin, above center
    produces
    topspin)[\[31\]](https://github.com/jlundgrenedge/baseball/blob/2bf615c0de18cb7dbc2d4f8084c6e9afedea44b5/batted_ball/contact.py#L126-L135)[\[32\]](https://github.com/jlundgrenedge/baseball/blob/2bf615c0de18cb7dbc2d4f8084c6e9afedea44b5/batted_ball/contact.py#L139-L148).
    Spin rates (backspin/sidespin) are calculated from contact offsets
    and bat
    motion[\[33\]](https://github.com/jlundgrenedge/baseball/blob/2bf615c0de18cb7dbc2d4f8084c6e9afedea44b5/batted_ball/contact.py#L582-L590)[\[34\]](https://github.com/jlundgrenedge/baseball/blob/2bf615c0de18cb7dbc2d4f8084c6e9afedea44b5/batted_ball/contact.py#L594-L602).
    All these physics factors combine to produce a **batted ball
    trajectory** output.
- **Ball in Play & Fielding:** If the ball is put in play (contact made
  and not
  foul)[\[35\]](https://github.com/jlundgrenedge/baseball/blob/2bf615c0de18cb7dbc2d4f8084c6e9afedea44b5/batted_ball/at_bat.py#L976-L985),
  the simulation hands off to the **Batted Ball Flight** and
  **Fielding** subsystems. The trajectory (exit velocity, launch angle,
  spin, spray direction) is fed into the **BattedBallSimulator**, which
  numerically simulates the ball’s flight through the air until it lands
  or is
  caught[\[36\]](https://github.com/jlundgrenedge/baseball/blob/2bf615c0de18cb7dbc2d4f8084c6e9afedea44b5/batted_ball/at_bat.py#L702-L710).
  This uses drag and Magnus lift formulas with the computed spin and
  velocity (including adjustments for altitude, wind,
  etc.)[\[37\]](https://github.com/jlundgrenedge/baseball/blob/2bf615c0de18cb7dbc2d4f8084c6e9afedea44b5/batted_ball/constants.py#L243-L252)[\[38\]](https://github.com/jlundgrenedge/baseball/blob/2bf615c0de18cb7dbc2d4f8084c6e9afedea44b5/batted_ball/constants.py#L254-L263).
  The result is a landing distance, hang time, and peak height for the
  hit[\[39\]](https://github.com/jlundgrenedge/baseball/blob/2bf615c0de18cb7dbc2d4f8084c6e9afedea44b5/batted_ball/at_bat.py#L936-L945)[\[40\]](https://github.com/jlundgrenedge/baseball/blob/2bf615c0de18cb7dbc2d4f8084c6e9afedea44b5/batted_ball/at_bat.py#L950-L958).
  Next, the **Fielding AI** determines if a fielder catches it or how
  the play unfolds:
  - Each batted ball is classified (ground ball, line drive, fly, etc.)
    and the defense “reacts.” Fielders have speed, acceleration, and
    reaction attributes mapped to real units (e.g. an average fielder
    ~27 ft/s
    sprint)[\[41\]](https://github.com/jlundgrenedge/baseball/blob/2bf615c0de18cb7dbc2d4f8084c6e9afedea44b5/batted_ball/attributes.py#L80-L88).
    Given the ball’s trajectory and hang time, the nearest fielder’s
    time to intercept is computed versus the ball’s arrival. A catch is
    successful if the fielder can arrive by or before the ball’s landing
    (with some margin for
    error)[\[42\]](https://github.com/jlundgrenedge/baseball/blob/2bf615c0de18cb7dbc2d4f8084c6e9afedea44b5/batted_ball/fielding.py#L84-L93)[\[43\]](https://github.com/jlundgrenedge/baseball/blob/2bf615c0de18cb7dbc2d4f8084c6e9afedea44b5/batted_ball/fielding.py#L94-L101).
    In v1, fielders occasionally fail to catch even reachable balls due
    to conservative success tuning, contributing to high hit rates (an
    issue noted for
    tuning)[\[44\]](https://github.com/jlundgrenedge/baseball/blob/2bf615c0de18cb7dbc2d4f8084c6e9afedea44b5/docs/GAME_SIMULATION_NOTES.md#L99-L107).
    Caught balls become outs (fly outs or line outs). If not caught, the
    ball lands for a hit.
  - For ground balls, the engine simulates the ball rolling and the
    fielder’s chance to field and throw out a runner. Fielder attributes
    (reaction time, fielding range, arm strength) determine if they
    reach the grounder in time to throw out the batter at
    first[\[45\]](https://github.com/jlundgrenedge/baseball/blob/2bf615c0de18cb7dbc2d4f8084c6e9afedea44b5/batted_ball/fielding.py#L130-L139)[\[46\]](https://github.com/jlundgrenedge/baseball/blob/2bf615c0de18cb7dbc2d4f8084c6e9afedea44b5/batted_ball/attributes.py#L74-L82).
    Currently, very few ground balls turn into outs (another realism
    gap)[\[47\]](https://github.com/jlundgrenedge/baseball/blob/2bf615c0de18cb7dbc2d4f8084c6e9afedea44b5/docs/GAME_SIMULATION_NOTES.md#L109-L117).
- **Play Outcome & Runner Advancement:** Finally, the **PlaySimulation**
  logic (baserunning module) advances any base runners and the batter
  based on the type of hit or
  out[\[48\]](https://github.com/jlundgrenedge/baseball/blob/2bf615c0de18cb7dbc2d4f8084c6e9afedea44b5/batted_ball/game_simulation.py#L525-L534)[\[49\]](https://github.com/jlundgrenedge/baseball/blob/2bf615c0de18cb7dbc2d4f8084c6e9afedea44b5/batted_ball/game_simulation.py#L548-L556).
  For example, on a single, runners typically advance one base; on a
  double, two bases, etc. Home runs score all
  runners[\[50\]](https://github.com/jlundgrenedge/baseball/blob/2bf615c0de18cb7dbc2d4f8084c6e9afedea44b5/docs/GAME_SIMULATION_NOTES.md#L86-L93).
  Outs are recorded and the inning state updated. The GameSimulator then
  proceeds to the next batter or next half-inning as appropriate.

**End-to-End Chain Summary:** *Pitcher selects pitch → Pitch trajectory
computed (velocity, spin, command error) → Batter’s swing decision
(swing or take) → If swing: contact vs. miss determined → If contact:
exit velocity & launch angle computed → Ball flight simulated → Fielders
attempt play → Outcome (strike/ball, hit or out) updates the game
state.* This causal pipeline ensures each subsystem’s output feeds the
next stage, mirroring the real-time sequence of baseball events.

# Subsystem-by-Subsystem Breakdown

## 1. Pitching Physics & Command

**Components:** Pitcher attributes, pitch selection logic, pitch physics
(trajectory simulator), and command model.

**Pitch Arsenal & Selection:** Each pitcher has an arsenal of pitch
types (fastball, slider, etc.). In v1, a simple AI chooses pitch type
based on previous pitches and count. For example, after a breaking ball,
the logic slightly prefers a fastball next (20% weight
boost)[\[51\]](https://github.com/jlundgrenedge/baseball/blob/2bf615c0de18cb7dbc2d4f8084c6e9afedea44b5/batted_ball/at_bat.py#L301-L310).
The selection weights also depend on pitcher “confidence” or usage
ratings for each pitch (e.g. a high “usage” means the pitcher is
comfortable throwing that pitch
often)[\[52\]](https://github.com/jlundgrenedge/baseball/blob/2bf615c0de18cb7dbc2d4f8084c6e9afedea44b5/batted_ball/player.py#L258-L267)[\[53\]](https://github.com/jlundgrenedge/baseball/blob/2bf615c0de18cb7dbc2d4f8084c6e9afedea44b5/batted_ball/player.py#L274-L283).
The result is a pitch type choice each throw.

**Command & Targeting:** The ***determine_pitch_intention*** function
decides how aggressive or conservative the pitcher is with location
based on the
count[\[54\]](https://github.com/jlundgrenedge/baseball/blob/2bf615c0de18cb7dbc2d4f8084c6e9afedea44b5/batted_ball/at_bat.py#L402-L411).
For instance, in 0-0 counts, about 90% of pitches are intended to be
strikes (either over the plate or on corners) versus ~10% intentionally
thrown as waste pitches out of the
zone[\[55\]](https://github.com/jlundgrenedge/baseball/blob/2bf615c0de18cb7dbc2d4f8084c6e9afedea44b5/batted_ball/at_bat.py#L414-L422).
With two strikes, pitchers will “waste” a pitch ~45% of the time to get
the batter to
chase[\[56\]](https://github.com/jlundgrenedge/baseball/blob/2bf615c0de18cb7dbc2d4f8084c6e9afedea44b5/batted_ball/at_bat.py#L426-L434).
(These percentages were tuned because initially too many pitches were
intentionally off the plate, causing excessive
walks[\[57\]](https://github.com/jlundgrenedge/baseball/blob/2bf615c0de18cb7dbc2d4f8084c6e9afedea44b5/MLB_REALISM_FIXES_2025-11-20.md#L73-L81).)
Once an intention is set, the engine picks a target within or outside
the strike zone accordingly: e.g. *strike_corner* might target a corner
of the zone with slight random
offset[\[58\]](https://github.com/jlundgrenedge/baseball/blob/2bf615c0de18cb7dbc2d4f8084c6e9afedea44b5/batted_ball/at_bat.py#L391-L398),
while *waste_chase* might target a few inches outside the zone
boundary[\[59\]](https://github.com/jlundgrenedge/baseball/blob/2bf615c0de18cb7dbc2d4f8084c6e9afedea44b5/batted_ball/at_bat.py#L363-L371).

**Command Error Model:** After a target is chosen, the actual pitch
location is offset by a random error based on the pitcher’s **command
rating**. This is implemented as a Gaussian (normal) deviation in
inches. An average MLB-level command (50k rating) maps to ~6.5 inches
standard deviation, whereas a wild pitcher (0 rating) might be ~10
inches[\[60\]](https://github.com/jlundgrenedge/baseball/blob/2bf615c0de18cb7dbc2d4f8084c6e9afedea44b5/batted_ball/attributes.py#L144-L149).
In code, this uses the pitcher’s COMMAND attribute to compute a sigma;
fatigue increases this sigma (up to 2× larger when the pitcher is
exhausted)[\[61\]](https://github.com/jlundgrenedge/baseball/blob/2bf615c0de18cb7dbc2d4f8084c6e9afedea44b5/batted_ball/player.py#L180-L186)[\[62\]](https://github.com/jlundgrenedge/baseball/blob/2bf615c0de18cb7dbc2d4f8084c6e9afedea44b5/batted_ball/player.py#L231-L240).
The engine then draws a random horizontal and vertical error from that
distribution[\[63\]](https://github.com/jlundgrenedge/baseball/blob/2bf615c0de18cb7dbc2d4f8084c6e9afedea44b5/batted_ball/player.py#L235-L243).
For example, a pitcher with elite control (~85k, ~4.5″ sigma) will dot
pitches near the corners, while a poor control pitcher’s pitch might
stray a foot off the
target[\[64\]](https://github.com/jlundgrenedge/baseball/blob/2bf615c0de18cb7dbc2d4f8084c6e9afedea44b5/batted_ball/attributes.py#L146-L149).
This command error, combined with intentional “balls” logic above,
yields the final outcome of each pitch as a ball or strike. (Notably, a
bug that previously ignored the COMMAND attribute was fixed to use the
actual
rating[\[61\]](https://github.com/jlundgrenedge/baseball/blob/2bf615c0de18cb7dbc2d4f8084c6e9afedea44b5/batted_ball/player.py#L180-L186).)

**Pitch Trajectory Physics:** The **PitchSimulator** then computes the
pitch’s flight from release to plate with gravity and Magnus force from
spin. Pitcher attributes set the initial velocity (e.g. a 50k velocity
rating ~93 mph fastball) and spin (e.g. ~2250 rpm at
50k)[\[65\]](https://github.com/jlundgrenedge/baseball/blob/2bf615c0de18cb7dbc2d4f8084c6e9afedea44b5/batted_ball/attributes.py#L128-L136).
Different pitch types apply multipliers (curveballs slower with more
spin,
etc.)[\[66\]](https://github.com/jlundgrenedge/baseball/blob/2bf615c0de18cb7dbc2d4f8084c6e9afedea44b5/batted_ball/player.py#L116-L124)[\[67\]](https://github.com/jlundgrenedge/baseball/blob/2bf615c0de18cb7dbc2d4f8084c6e9afedea44b5/batted_ball/player.py#L150-L158).
The pitch is numerically integrated to get final velocity at plate,
movement (break), and whether it crossed the strike zone (used for
`is_strike`)[\[68\]](https://github.com/jlundgrenedge/baseball/blob/2bf615c0de18cb7dbc2d4f8084c6e9afedea44b5/batted_ball/at_bat.py#L540-L548)[\[7\]](https://github.com/jlundgrenedge/baseball/blob/2bf615c0de18cb7dbc2d4f8084c6e9afedea44b5/batted_ball/at_bat.py#L570-L578).
The simulation provides detailed physics like vertical and horizontal
break in inches, which the engine logs per pitch.

**Effect on Stats:** This subsystem primarily influences **Walk rate
(BB%)** and to some extent strikeouts. The **pitch intention logic** and
**command error** together determine how often pitches miss the zone.
Initially, the simulation overshot with ~15% walks (MLB ~8.5%) because
the AI was throwing too many non-competitive pitches across various
counts[\[69\]](https://github.com/jlundgrenedge/baseball/blob/2bf615c0de18cb7dbc2d4f8084c6e9afedea44b5/MLB_REALISM_FIXES_2025-11-20.md#L19-L22)[\[57\]](https://github.com/jlundgrenedge/baseball/blob/2bf615c0de18cb7dbc2d4f8084c6e9afedea44b5/MLB_REALISM_FIXES_2025-11-20.md#L73-L81).
Adjusting those intention probabilities closer to 90% strikes in neutral
counts fixed much of
this[\[70\]](https://github.com/jlundgrenedge/baseball/blob/2bf615c0de18cb7dbc2d4f8084c6e9afedea44b5/MLB_REALISM_FIXES_2025-11-20.md#L75-L83)[\[55\]](https://github.com/jlundgrenedge/baseball/blob/2bf615c0de18cb7dbc2d4f8084c6e9afedea44b5/batted_ball/at_bat.py#L414-L422).
The command attribute mapping is tuned so that an average pitcher yields
~62–65% strikes (which aligns with MLB zone
percentage)[\[71\]](https://github.com/jlundgrenedge/baseball/blob/2bf615c0de18cb7dbc2d4f8084c6e9afedea44b5/batted_ball/at_bat.py#L340-L348)[\[60\]](https://github.com/jlundgrenedge/baseball/blob/2bf615c0de18cb7dbc2d4f8084c6e9afedea44b5/batted_ball/attributes.py#L144-L149).
One recent improvement suggestion is to incorporate an **umpire model or
framing** – currently every pitch strictly uses the zone definition, but
adding a probability for borderline strikes to be called balls (and vice
versa) could further refine walk rates. Overall, this module provides
the foundation for plate discipline outcomes: it sets the stage upon
which batters either walk or put the ball in play depending on these
pitch locations.

## 2. Batter Decision System

**Components:** Batter’s plate discipline, pitch recognition, swing
timing, and approach logic.

This subsystem controls *if and when* the batter swings. It aims to
model real batting eye and strategy.

**Zone & Chase Behavior:** The **decide_to_swing** function uses whether
the pitch is a strike and its location to compute a base swing
probability[\[8\]](https://github.com/jlundgrenedge/baseball/blob/2bf615c0de18cb7dbc2d4f8084c6e9afedea44b5/batted_ball/player.py#L630-L639)[\[10\]](https://github.com/jlundgrenedge/baseball/blob/2bf615c0de18cb7dbc2d4f8084c6e9afedea44b5/batted_ball/player.py#L648-L657): -
In the strike zone: batters swing much more often. The code models
higher swing probability for pitches down the middle (~85%) and a bit
lower on the edges
(~65%)[\[72\]](https://github.com/jlundgrenedge/baseball/blob/2bf615c0de18cb7dbc2d4f8084c6e9afedea44b5/batted_ball/player.py#L632-L640),
reflecting that strikes on the corners are sometimes taken. - Outside
the zone: a **chase probability** is calculated that decays as the pitch
gets farther from the zone. Just outside the zone might yield ~30–35%
swing (if it’s only an inch or two off) dropping toward ~10% or less for
a pitch way
outside[\[10\]](https://github.com/jlundgrenedge/baseball/blob/2bf615c0de18cb7dbc2d4f8084c6e9afedea44b5/batted_ball/player.py#L648-L657).

**Batter Attributes:** Several hitter attributes modify these baseline
probabilities: - **Zone Discernment (Discipline):** A high discipline
batter will be more selective. In code, for pitches out of the zone, the
swing probability is multiplied by a factor (1 –
0.85*discipline)[\[73\]](https://github.com/jlundgrenedge/baseball/blob/2bf615c0de18cb7dbc2d4f8084c6e9afedea44b5/batted_ball/player.py#L660-L668).
For an elite disciplinarian (discipline≈0.90 on 0–1 scale), this factor
~0.235, meaning a ~76% reduction in chase
swings[\[74\]](https://github.com/jlundgrenedge/baseball/blob/2bf615c0de18cb7dbc2d4f8084c6e9afedea44b5/batted_ball/player.py#L662-L670).
Poor discipline (≈0.45) might only cut chase odds ~38%. This creates a
~13–15 point swing% gap between good and bad eyes, matching MLB
data[\[74\]](https://github.com/jlundgrenedge/baseball/blob/2bf615c0de18cb7dbc2d4f8084c6e9afedea44b5/batted_ball/player.py#L662-L670).
In-zone, high discipline slightly* reduces *swing rate on strikes
(willing to take borderline
strikes)[\[75\]](https://github.com/jlundgrenedge/baseball/blob/2bf615c0de18cb7dbc2d4f8084c6e9afedea44b5/batted_ball/player.py#L656-L664).
-* *Swing Timing (Aggressiveness):* *The batter’s* *swing decision
latency* *(reaction time) is mapped to an aggression factor. Faster
reactors (e.g. 75 ms elite) swing more, slower ones (200 ms) swing
less[\[11\]](https://github.com/jlundgrenedge/baseball/blob/2bf615c0de18cb7dbc2d4f8084c6e9afedea44b5/batted_ball/player.py#L670-L679).
The model linearly scales latency to a multiplier between 0.9 (very
aggressive) and 0.2 (very
passive)[\[76\]](https://github.com/jlundgrenedge/baseball/blob/2bf615c0de18cb7dbc2d4f8084c6e9afedea44b5/batted_ball/player.py#L674-L682).
This represents how quickly a batter decides – shorter time = more
“hair-trigger” swings. -* *Velocity & Break Adjustment:* *Higher pitch
speed slightly* reduces *swings (fast pitches are harder to read – up to
10% swing reduction for
100 mph)[\[77\]](https://github.com/jlundgrenedge/baseball/blob/2bf615c0de18cb7dbc2d4f8084c6e9afedea44b5/batted_ball/player.py#L683-L690).
Breaking balls increase chase likelihood (e.g. sliders/curves +25%
out-of-zone swing, since they fool
batters)[\[78\]](https://github.com/jlundgrenedge/baseball/blob/2bf615c0de18cb7dbc2d4f8084c6e9afedea44b5/batted_ball/player.py#L688-L695).
-* *Count-based logic:*\* With two strikes, batters adopt “protect
mode,” swinging more even at close pitches (the code adds +15% swing on
strikes and up to +40% on borderline balls with 2
strikes)[\[12\]](https://github.com/jlundgrenedge/baseball/blob/2bf615c0de18cb7dbc2d4f8084c6e9afedea44b5/batted_ball/player.py#L696-L704).
Conversely, in a 3-ball count, batters become selective: if 3–x and the
pitch is a ball, swing probability halves (don’t chase on
3-0/3-1)[\[79\]](https://github.com/jlundgrenedge/baseball/blob/2bf615c0de18cb7dbc2d4f8084c6e9afedea44b5/batted_ball/player.py#L702-L710).

**Outcome of Decision:** This system outputs a boolean – swing or take –
for each pitch. If “take,” the pitch outcome is determined by location
(ball or called strike). If “swing,” then we proceed to the contact
calculation (whiff or contact).

**Implications for Stats:** The Batter Decision System heavily
influences **Walks (BB%)** and indirectly **Strikeouts (K%)**. In the
initial build, one identified issue was the lack of walks – partly
because batters might swing too often at pitches they should take. The
current model gives a realistic chase rate spread, and indeed after
tuning pitcher behavior, walks are now mostly governed by the pitcher’s
accuracy. However, this system can still be tweaked. For example, if
walk rates are low, one could reduce overall swing aggressiveness
slightly or increase the discipline effect. It’s a delicate balance: if
batters never chase, walks will spike (and strikeouts may drop because
batters will reach 4 balls more often). If batters chase too much, walks
vanish but strikeouts can increase (swinging at bad pitches leads to
more misses).

One insight from the recent analysis is that **strikeout rate and walk
rate are coupled via this system**: if we globally make batters swing
(and miss) more to raise K%, we also prolong at-bats, which
paradoxically *increases* walks because more pitches = more chances to
reach ball
four[\[80\]](https://github.com/jlundgrenedge/baseball/blob/2bf615c0de18cb7dbc2d4f8084c6e9afedea44b5/MLB_REALISM_PASS4_FINDINGS_2025-11-20.md#L64-L73)[\[81\]](https://github.com/jlundgrenedge/baseball/blob/2bf615c0de18cb7dbc2d4f8084c6e9afedea44b5/MLB_REALISM_PASS4_FINDINGS_2025-11-20.md#L74-L82).
This was seen when a +100% across-the-board whiff increase caused walk
rate to worsen from 17% to
21%[\[82\]](https://github.com/jlundgrenedge/baseball/blob/2bf615c0de18cb7dbc2d4f8084c6e9afedea44b5/MLB_REALISM_PASS4_FINDINGS_2025-11-20.md#L48-L56)[\[83\]](https://github.com/jlundgrenedge/baseball/blob/2bf615c0de18cb7dbc2d4f8084c6e9afedea44b5/MLB_REALISM_PASS4_FINDINGS_2025-11-20.md#L80-L88).
Thus, the batter decision logic must be tuned in concert with the
pitching subsystem to achieve the right mix of swings, misses, and
takes.

## 3. Bat–Ball Collision Physics

Once a swing is decided and the bat is put into motion, the
**ContactModel** handles the moment of impact between bat and ball. This
subsystem translates the batter’s physical swing and the pitch
characteristics into exit velocity, launch angle, and spin – the key
factors for batted ball outcomes.

**Collision Model (Exit Velocity):** The simulation uses a
**physics-first collision formula** for exit velocity (EV):

``` math
\text{ExitVelo} = q \cdot V_{\text{pitch}} + (1 + q) \cdot V_{\text{bat}},
```

where *q* is the **collision efficiency** (related to coefficient of
restitution). For a perfect on-the-sweet-spot hit with a wood bat, q was
initially ~0.13. In that ideal case, a 90 mph pitch and 75 mph bat swing
would produce ~**90 mph** exit
velocity[\[27\]](https://github.com/jlundgrenedge/baseball/blob/2bf615c0de18cb7dbc2d4f8084c6e9afedea44b5/MLB_REALISM_FIXES_2025-11-20.md#L94-L102).
Many factors adjust the effective q: - **Bat Material:** Different bats
have different base q (wood vs aluminum, etc.), but MLB uses wood
exclusively. (Constants were wood:0.13, aluminum:0.11
originally)[\[84\]](https://github.com/jlundgrenedge/baseball/blob/2bf615c0de18cb7dbc2d4f8084c6e9afedea44b5/MLB_REALISM_FIXES_2025-11-20.md#L110-L118). -
**Sweet Spot & Mishit Penalties:** If the batter’s swing is not
perfectly on the sweet spot, energy transfer drops. The engine computes
a **distance from sweet spot** (inches) combining vertical and
horizontal miss on the bat
barrel[\[85\]](https://github.com/jlundgrenedge/baseball/blob/2bf615c0de18cb7dbc2d4f8084c6e9afedea44b5/batted_ball/contact.py#L546-L554).
Any distance \> ~1 inch incurs an EV penalty. Initially this penalty was
significant (e.g. a 2″ miss could cut exit speed ~10%+), but v1.0 had an
overly harsh penalty that led to too many weak hits. It was later
*softened*: the sweet spot “radius” was effectively widened to ~1.1″
with a gentler falloff beyond that (penalty capped at 30% vs 35%
before)[\[86\]](https://github.com/jlundgrenedge/baseball/blob/2bf615c0de18cb7dbc2d4f8084c6e9afedea44b5/batted_ball/contact.py#L562-L570).
This change increased overall exit velos by allowing slightly off-center
hits to still be hit hard. - **Pitch Impact Location:** The vertical
location where the bat meets the ball can also slightly reduce EV.
Hitting under the center of the ball (to loft it) or over it (for
chop/topspin) is less efficient than squarely in the center. The model
applies a modest EV reduction (2–3% per inch) for hitting significantly
above or below the ball’s
center[\[87\]](https://github.com/jlundgrenedge/baseball/blob/2bf615c0de18cb7dbc2d4f8084c6e9afedea44b5/batted_ball/contact.py#L130-L139)[\[32\]](https://github.com/jlundgrenedge/baseball/blob/2bf615c0de18cb7dbc2d4f8084c6e9afedea44b5/batted_ball/contact.py#L139-L148). -
**Energy Loss Factors:** The constants include energy lost to vibrations
and ball deformation. For example, a portion (~ up to 10%) of energy can
be lost if contact excites bat vibrations far from the
node[\[88\]](https://github.com/jlundgrenedge/baseball/blob/2bf615c0de18cb7dbc2d4f8084c6e9afedea44b5/batted_ball/constants.py#L274-L282).
The model includes such factors, although many are encapsulated in the
single *q* value for simplicity.

All these considerations funnel into an effective *q* used in the exit
velocity
formula[\[89\]](https://github.com/jlundgrenedge/baseball/blob/2bf615c0de18cb7dbc2d4f8084c6e9afedea44b5/batted_ball/contact.py#L549-L558).
After computing raw exit speed, the code ensures a minimum EV (no less
than 15 mph) so that even the weakest contacts dribble forward a
bit[\[90\]](https://github.com/jlundgrenedge/baseball/blob/2bf615c0de18cb7dbc2d4f8084c6e9afedea44b5/batted_ball/contact.py#L570-L578).

**Launch Angle & Spin:** The launch angle is determined by the geometry
of the swing and contact: - **Swing Plane vs Pitch Plane:** The batter’s
swing has an **attack angle** (e.g. +7° for an average hitter’s
uppercut)[\[91\]](https://github.com/jlundgrenedge/baseball/blob/2bf615c0de18cb7dbc2d4f8084c6e9afedea44b5/batted_ball/attributes.py#L8-L16).
The pitch has a downward trajectory (usually ~-5° to -10°). When the bat
intersects the ball, the relative angle influences the launch. The code
computes launch angle via a function that uses the bat’s path and the
pitch’s approach angle, adjusted by how far under or over the ball was
hit[\[92\]](https://github.com/jlundgrenedge/baseball/blob/2bf615c0de18cb7dbc2d4f8084c6e9afedea44b5/batted_ball/contact.py#L575-L583).
In general, hitting below the ball (under its center) increases launch
angle (more loft) whereas hitting above it drives the ball down. -
**Contact Vertical Offset:** If the bat meets the ball below its
midpoint, it produces backspin and a higher launch angle. An inch below
center can add a significant loft – the constants indicate each inch
below center adds a certain degrees to launch and a few hundred RPM of
backspin[\[93\]](https://github.com/jlundgrenedge/baseball/blob/2bf615c0de18cb7dbc2d4f8084c6e9afedea44b5/batted_ball/contact.py#L113-L121)[\[94\]](https://github.com/jlundgrenedge/baseball/blob/2bf615c0de18cb7dbc2d4f8084c6e9afedea44b5/batted_ball/contact.py#L126-L134).
Conversely, hitting above center creates topspin and a lower launch
angle[\[95\]](https://github.com/jlundgrenedge/baseball/blob/2bf615c0de18cb7dbc2d4f8084c6e9afedea44b5/batted_ball/contact.py#L117-L125)[\[32\]](https://github.com/jlundgrenedge/baseball/blob/2bf615c0de18cb7dbc2d4f8084c6e9afedea44b5/batted_ball/contact.py#L139-L148).
The simulation uses these rules to adjust the initial launch angle and
spin axis. In v1, **attack angles were calibrated too high** (average
12° with ±15° variance), yielding an excess of fly balls ~54% (MLB
~34%). This was corrected by lowering average attack angles to ~7° for
normal hitters (with variance ensuring a mix of grounders and fly
balls)[\[96\]](https://github.com/jlundgrenedge/baseball/blob/2bf615c0de18cb7dbc2d4f8084c6e9afedea44b5/MLB_REALISM_FIXES_2025-11-20.md#L35-L44)[\[97\]](https://github.com/jlundgrenedge/baseball/blob/2bf615c0de18cb7dbc2d4f8084c6e9afedea44b5/MLB_REALISM_FIXES_2025-11-20.md#L42-L48). -
**Horizontal (Side) Offset:** If the bat hits the ball off the side of
the sweet spot (toward the handle or end), it can introduce sidespin and
also reduces exit velocity
slightly[\[98\]](https://github.com/jlundgrenedge/baseball/blob/2bf615c0de18cb7dbc2d4f8084c6e9afedea44b5/batted_ball/contact.py#L152-L160).
The model adds ~300 RPM of sidespin per inch of horizontal miss and cuts
EV by up to 40% if hit two inches off the barrel
end[\[98\]](https://github.com/jlundgrenedge/baseball/blob/2bf615c0de18cb7dbc2d4f8084c6e9afedea44b5/batted_ball/contact.py#L152-L160).

**Output:** The ContactModel returns a dictionary with the computed
**exit_velocity**, **launch_angle**, **backspin_rpm**, **sidespin_rpm**,
and a qualitative **contact_quality** label (e.g. *barrel*, *solid*,
*weak*) based on how far off the sweet spot the hit
was[\[99\]](https://github.com/jlundgrenedge/baseball/blob/2bf615c0de18cb7dbc2d4f8084c6e9afedea44b5/batted_ball/at_bat.py#L716-L725)[\[100\]](https://github.com/jlundgrenedge/baseball/blob/2bf615c0de18cb7dbc2d4f8084c6e9afedea44b5/batted_ball/at_bat.py#L728-L732).
This feeds directly into the next stage (ball flight). It also notes the
*q* used and offsets for
logging/debugging[\[101\]](https://github.com/jlundgrenedge/baseball/blob/2bf615c0de18cb7dbc2d4f8084c6e9afedea44b5/batted_ball/at_bat.py#L726-L734).

**Impact on Stats:** This subsystem dictates **power outcomes** –
extra-base hits and home run rates – and batting average on balls in
play (quality of contact leads to hits or outs). In the initial version,
a major problem was **extremely low HR/FB% and Hard-Hit%** – essentially
the collision was too “dead.” Average exit velocity was ~85 mph (a bit
low), but more telling, only ~5% of balls were hit 95+ mph (MLB ~40%
hard-hit) and almost no fly balls were going over the fence (HR/FB ~0.6%
vs 12.5%
MLB)[\[102\]](https://github.com/jlundgrenedge/baseball/blob/2bf615c0de18cb7dbc2d4f8084c6e9afedea44b5/MLB_REALISM_FIXES_2025-11-20.md#L20-L28)[\[103\]](https://github.com/jlundgrenedge/baseball/blob/2bf615c0de18cb7dbc2d4f8084c6e9afedea44b5/MLB_REALISM_FIXES_2025-11-20.md#L91-L100).
The root cause was that the chosen collision efficiency (q=0.13) was too
low *after* all the mishit
penalties[\[103\]](https://github.com/jlundgrenedge/baseball/blob/2bf615c0de18cb7dbc2d4f8084c6e9afedea44b5/MLB_REALISM_FIXES_2025-11-20.md#L91-L100).
Effectively, q dropped to ~0.09 on most
swings[\[28\]](https://github.com/jlundgrenedge/baseball/blob/2bf615c0de18cb7dbc2d4f8084c6e9afedea44b5/MLB_REALISM_FIXES_2025-11-20.md#L96-L104),
which capped exit velocities around 90–100 mph even for perfect swings –
not enough to regularly clear fences. The developers experimented with
increasing q: - Raising to q=0.18 made average EV ~105 mph and produced
plenty of homers, but **overshot massively** – HR/FB spiked to ~55% and
nearly every ball was a rocket (hard-hit
~95%)[\[104\]](https://github.com/jlundgrenedge/baseball/blob/2bf615c0de18cb7dbc2d4f8084c6e9afedea44b5/batted_ball/constants.py#L244-L252)[\[105\]](https://github.com/jlundgrenedge/baseball/blob/2bf615c0de18cb7dbc2d4f8084c6e9afedea44b5/batted_ball/constants.py#L246-L255). -
After iteration, they settled on a much lower q=0.03 (!), which may seem
counterintuitive but recall other adjustments were made. In a later
realism pass, the “best” compromise had q ~0.03 yielding 94 mph average
EV and ~40%
hard-hit[\[106\]](https://github.com/jlundgrenedge/baseball/blob/2bf615c0de18cb7dbc2d4f8084c6e9afedea44b5/batted_ball/constants.py#L250-L259)[\[107\]](https://github.com/jlundgrenedge/baseball/blob/2bf615c0de18cb7dbc2d4f8084c6e9afedea44b5/batted_ball/constants.py#L261-L265).
Even so, HR/FB was only ~6.3% – still about half of MLB
norm[\[108\]](https://github.com/jlundgrenedge/baseball/blob/2bf615c0de18cb7dbc2d4f8084c6e9afedea44b5/MLB_REALISM_PASS4_FINDINGS_2025-11-20.md#L24-L28)[\[109\]](https://github.com/jlundgrenedge/baseball/blob/2bf615c0de18cb7dbc2d4f8084c6e9afedea44b5/MLB_REALISM_PASS4_FINDINGS_2025-11-20.md#L90-L99).
This highlighted that with a **single-parameter collision model (q)**,
you cannot independently tune average exit velocity and HR
production[\[109\]](https://github.com/jlundgrenedge/baseball/blob/2bf615c0de18cb7dbc2d4f8084c6e9afedea44b5/MLB_REALISM_PASS4_FINDINGS_2025-11-20.md#L90-L99).
The tail of the EV distribution is what matters for homers, and making
the tail fatter (more 100+ mph hits) also raises the mean EV and
hard-hit%. Thus, decoupling these will be a goal for v2 (see **Root
Causes** and **Version 2 Plan** below).

In summary, the bat-ball physics subsystem provides a physically
grounded way to go from swing to batted ball. Its strengths are in
producing a variety of outcomes (grounders vs flies, varying exit
speeds). Its weakness so far was calibration – ensuring the distribution
of EV and launch angle yields realistic rates of singles, doubles,
homers, etc. The recent adjustments (lower attack angle, tweaking q and
sweet spot penalty) moved it closer to MLB benchmarks but trade-offs
remained (e.g., HR/FB vs EV).

## 4. Batted Ball Flight Model

Once the ball leaves the bat, the **trajectory simulator** (often called
`BattedBallSimulator`) takes over to track the ball’s flight through the
air. This subsystem uses physics to determine how far the ball goes and
whether it becomes a hit or an out.

**Physics of Flight:** The model treats the batted ball as a projectile
under gravity, air drag, and lift (Magnus effect from backspin or
topspin): - **Drag:** The simulation uses a drag coefficient (Cd) that
slows the ball. It’s calibrated so that a typical 100 mph, 28° launch
goes ~395 ft (which is a benchmark for a well-hit
homer)[\[110\]](https://github.com/jlundgrenedge/baseball/blob/2bf615c0de18cb7dbc2d4f8084c6e9afedea44b5/batted_ball/constants.py#L234-L243)[\[111\]](https://github.com/jlundgrenedge/baseball/blob/2bf615c0de18cb7dbc2d4f8084c6e9afedea44b5/batted_ball/constants.py#L296-L301).
There’s sophistication here: Cd isn’t constant – it varies with velocity
(Reynolds number effects). The code enables a *Reynolds drag adjustment*
that lowers drag at very high speeds and increases it at certain
mid-speeds, reflecting real baseball
aerodynamics[\[112\]](https://github.com/jlundgrenedge/baseball/blob/2bf615c0de18cb7dbc2d4f8084c6e9afedea44b5/batted_ball/constants.py#L37-L45).
(This was tweaked on 2025-11-19 to fine-tune how backspin impacts
distance[\[113\]](https://github.com/jlundgrenedge/baseball/blob/2bf615c0de18cb7dbc2d4f8084c6e9afedea44b5/batted_ball/constants.py#L30-L38).)
In practice, this means the model tries to match Statcast data: e.g., a
ball with a lot of backspin might experience a bit more drag (due to a
“drag crisis” around certain speeds) which can shorten its carry
slightly if not accounted
for[\[114\]](https://github.com/jlundgrenedge/baseball/blob/2bf615c0de18cb7dbc2d4f8084c6e9afedea44b5/batted_ball/constants.py#L38-L46). -
**Lift (Magnus Effect):** Backspin generates an upward lift force that
keeps the ball in the air longer, causing it to travel farther (the same
reason golf balls carry). The engine includes a lift coefficient that is
proportional to spin rate. Constants like `SPIN_FACTOR` ~1.45e-4 and a
cap `CL_MAX` ~0.45 are
used[\[115\]](https://github.com/jlundgrenedge/baseball/blob/2bf615c0de18cb7dbc2d4f8084c6e9afedea44b5/batted_ball/constants.py#L50-L58)[\[116\]](https://github.com/jlundgrenedge/baseball/blob/2bf615c0de18cb7dbc2d4f8084c6e9afedea44b5/batted_ball/constants.py#L52-L60).
In v1, the lift was actually a bit high, causing very long hang times
(fielders had 2–3 extra seconds on some flies). They reduced the max
lift coefficient from 0.6 to 0.45 to prevent “floaters” and make balls
drop more
realistically[\[116\]](https://github.com/jlundgrenedge/baseball/blob/2bf615c0de18cb7dbc2d4f8084c6e9afedea44b5/batted_ball/constants.py#L52-L60).
So a 1500 rpm backspin might add on the order of tens of feet to a fly
ball’s distance. Topspin (negative backspin in code) does the opposite:
it pushes the ball down sooner. - **Gravity & Environmental Factors:**
Gravity is standard (9.81 m/s² down). They also include air density
effects for altitude and
temperature[\[117\]](https://github.com/jlundgrenedge/baseball/blob/2bf615c0de18cb7dbc2d4f8084c6e9afedea44b5/batted_ball/at_bat.py#L76-L84).
For example, at Coors Field’s 5200 ft altitude, air is thinner so the
ball goes farther – the code has a ~+30 ft distance boost for Coors (or
generally ~+6 ft per 1000 ft
altitude)[\[118\]](https://github.com/jlundgrenedge/baseball/blob/2bf615c0de18cb7dbc2d4f8084c6e9afedea44b5/batted_ball/constants.py#L298-L306).
Wind can be set; a tailwind adds carry (~3.8 ft per 1 mph of
wind)[\[119\]](https://github.com/jlundgrenedge/baseball/blob/2bf615c0de18cb7dbc2d4f8084c6e9afedea44b5/batted_ball/constants.py#L102-L105).

**Trajectory Simulation:** Given initial speed, angle, and spin, the
simulator numerically integrates the ball’s flight until it hits the
ground. The output is a `BattedBallResult` object containing: -
**Distance (carry):** How far from home plate the ball traveled (in
feet). - **Hang time (flight_time):** How long the ball was airborne
(seconds). - **Peak height:** The apex of the trajectory. - It also
flags if the ball cleared a typical fence height (~8 ft at ~330+ ft for
a home run) or if it’s a ground ball, etc., but the determination of hit
type is often done in the play outcome stage.

**Hit Classification & Outcomes:** The flight results are used to
determine what kind of hit or out occurred. Rules in `PlaySimulator` and
`play_outcome` classify: - If a ball’s distance exceeds ~380 ft (and has
sufficient height), it’s a **Home
Run**[\[120\]](https://github.com/jlundgrenedge/baseball/blob/2bf615c0de18cb7dbc2d4f8084c6e9afedea44b5/docs/GAME_SIMULATION_NOTES.md#L76-L84).
(They used 380 ft with 40+ ft apex or any 400+ ft as HR
criteria[\[121\]](https://github.com/jlundgrenedge/baseball/blob/2bf615c0de18cb7dbc2d4f8084c6e9afedea44b5/docs/GAME_SIMULATION_NOTES.md#L75-L83),
though ideally stadium-specific dimensions would be used in future.) -
If it’s a high short fly (pop-up) or a standard fly in range of
fielders, it’s likely an **Out** (caught). One noted gap was no explicit
infield fly handling – v1 did not have a concept of an automatic easy
pop-out, but adding near-100% catch on very high short flies is
planned[\[122\]](https://github.com/jlundgrenedge/baseball/blob/2bf615c0de18cb7dbc2d4f8084c6e9afedea44b5/docs/GAME_SIMULATION_NOTES.md#L117-L124). -
Line drives and grounders can be hits or outs depending on if a fielder
can get them. There’s a notion of **catch probability**: faster
outfielders + shorter hang time = more likely hit. Initially, fielders
weren’t catching enough; raising their speed or reaction or giving them
more credit on tough plays is on the tuning
list[\[123\]](https://github.com/jlundgrenedge/baseball/blob/2bf615c0de18cb7dbc2d4f8084c6e9afedea44b5/docs/GAME_SIMULATION_NOTES.md#L100-L108). -
Ground balls: if fielded before exiting the infield, usually an out (if
the throw beats the runner). But v1 had few ground outs because perhaps
runners were too fast or fielder reaction too slow. Plans include
increasing fielder agility or reducing baserunner speed on grounders to
yield a realistic ground-out
rate[\[124\]](https://github.com/jlundgrenedge/baseball/blob/2bf615c0de18cb7dbc2d4f8084c6e9afedea44b5/docs/GAME_SIMULATION_NOTES.md#L109-L116).

**Baserunning and Fielding Integration:** The flight model hands off to
the fielding module as soon as the ball is in play. For example, the
**Fielding AI** uses the hang time to compute when the ball will land vs
when a fielder
arrives[\[42\]](https://github.com/jlundgrenedge/baseball/blob/2bf615c0de18cb7dbc2d4f8084c6e9afedea44b5/batted_ball/fielding.py#L84-L93).
If caught, the play ends (with possible runner tagging if deep enough).
If not caught, the ball’s landing position and momentum determine how
far it rolls, etc. The fielders then chase it down and throw if needed.
The baserunning logic will advance runners – e.g., on a gap double, a
runner on first will usually score, on a single they go
station-to-station, etc. All that is handled in `simulate_complete_play`
in
PlaySimulator[\[125\]](https://github.com/jlundgrenedge/baseball/blob/2bf615c0de18cb7dbc2d4f8084c6e9afedea44b5/batted_ball/game_simulation.py#L550-L559)
and the baserunning helper functions.

**Statistical Role:** This subsystem, combined with fielding, largely
determines **Batting Average on Balls in Play (BABIP)** and extra-base
hit rates. For instance, too many long flies not caught will inflate
BABIP and doubles/triples. In early builds, BABIP came out low (~.236)
partly because *so many* fly balls were being generated (and many of
those were
caught)[\[126\]](https://github.com/jlundgrenedge/baseball/blob/2bf615c0de18cb7dbc2d4f8084c6e9afedea44b5/MLB_REALISM_FIXES_2025-11-20.md#L22-L28).
After adjusting the launch angle distribution to get more grounders
(which tend to sneak through for hits) and tweaking fielder success,
BABIP moved closer to normal (~.248, still a tad
low)[\[127\]](https://github.com/jlundgrenedge/baseball/blob/2bf615c0de18cb7dbc2d4f8084c6e9afedea44b5/MLB_REALISM_PASS4_FINDINGS_2025-11-20.md#L20-L28).
Achieving a correct **HR/FB%** intersects with this module too: given a
set of exit velocities from the collision model, the carry model and
stadium fence distance decide what fraction of deep flies leave the
park. In our case, even after upping exit speeds, HR/FB remained low at
6.3%. This suggests the carry model (spin, drag) could be further
refined or that not enough balls were launched in the optimal 25–30°
range. It was noted that separating launch angle effects from exit velo
might help – e.g., some hitters produce a lot of high fly balls but not
all are home runs (pop-ups). The engine might need to allow tuning of
how many fly balls are “just high lofted outs” vs line-drive homers.

In all, the flight and fielding subsystem is where the “rubber meets the
road” for turning physics into actual outs or hits in the stat line. It
is fairly advanced in v1, but realism tuning (especially for outfield
play and pop-ups) is scheduled. A future improvement could include
modeling individual stadium dimensions and wind currents, but v1 treats
every field generically.

## 5. Fielding AI

**Components:** Player fielding attributes, reaction logic, running to
the ball, catching attempts, throwing to bases.

Fielding AI is responsible for converting batted ball trajectories into
outs (or not). Each defensive player has a **FielderAttributes** profile
that maps to physical skills: - **Sprint Speed:** How fast they run
(ft/s). Average ~27 ft/s (which matches MLB average outfielder ~18.5
mph)[\[41\]](https://github.com/jlundgrenedge/baseball/blob/2bf615c0de18cb7dbc2d4f8084c6e9afedea44b5/batted_ball/attributes.py#L80-L88).
Elite can approach 30 ft/s (~20.5
mph)[\[128\]](https://github.com/jlundgrenedge/baseball/blob/2bf615c0de18cb7dbc2d4f8084c6e9afedea44b5/batted_ball/attributes.py#L78-L86). -
**Acceleration:** How quickly they reach top speed (ft/s²). Elite ~80,
avg ~60
ft/s²[\[46\]](https://github.com/jlundgrenedge/baseball/blob/2bf615c0de18cb7dbc2d4f8084c6e9afedea44b5/batted_ball/attributes.py#L74-L82). -
**Reaction Time:** How long before they start moving on contact. Elite
~0.05 s, avg ~0.1 s, poor ~0.3–0.4
s[\[129\]](https://github.com/jlundgrenedge/baseball/blob/2bf615c0de18cb7dbc2d4f8084c6e9afedea44b5/batted_ball/attributes.py#L68-L76)[\[130\]](https://github.com/jlundgrenedge/baseball/blob/2bf615c0de18cb7dbc2d4f8084c6e9afedea44b5/batted_ball/attributes.py#L86-L94). -
**Fielding Range/Route:** An efficiency factor (0–1) that simulates how
direct a route they take. Elite ~0.96, avg ~0.88 (meaning an avg fielder
might cover ~12% less ground due to imperfect
route)[\[131\]](https://github.com/jlundgrenedge/baseball/blob/2bf615c0de18cb7dbc2d4f8084c6e9afedea44b5/batted_ball/attributes.py#L84-L91). -
**Hands/Glove (Catch ability):** Probability of catching when in
position, and tendency to commit errors on easy plays. Mapped such that
elite has very few drop errors. - **Arm Strength & Accuracy:** For
throws, infielders and outfielders have velocity (e.g. 75 mph avg
infielder throw, 88 mph elite
OF)[\[132\]](https://github.com/jlundgrenedge/baseball/blob/2bf615c0de18cb7dbc2d4f8084c6e9afedea44b5/batted_ball/attributes.py#L98-L101)
and accuracy (elite misses by \<2 ft, poor by up to 10+
ft)[\[133\]](https://github.com/jlundgrenedge/baseball/blob/2bf615c0de18cb7dbc2d4f8084c6e9afedea44b5/batted_ball/attributes.py#L116-L120). -
**Transfer & Release Time:** How fast they get the ball out of the glove
(important for turning double plays). This was tuned to slow down
infield releases because initially double plays were too
automatic[\[134\]](https://github.com/jlundgrenedge/baseball/blob/2bf615c0de18cb7dbc2d4f8084c6e9afedea44b5/batted_ball/attributes.py#L92-L100).

**Fielding Play Logic:** - **On contact:** The game determines which
fielder is “responsible” (e.g. a fly to the gap might assign the nearest
outfielder). The fielder’s reaction time elapses, then they run toward
the landing spot of the ball. - **Catch determination:** The engine
compares the **ball’s arrival time** at that spot to the **fielder’s
arrival time**. Fielder arrival time = reaction_time + time to sprint
the distance (taking into account acceleration and any route
inefficiency). If the fielder arrives earlier than the ball (plus maybe
a small margin for making the catch posture), the catch is made, barring
a random drop error
chance[\[42\]](https://github.com/jlundgrenedge/baseball/blob/2bf615c0de18cb7dbc2d4f8084c6e9afedea44b5/batted_ball/fielding.py#L84-L93)[\[135\]](https://github.com/jlundgrenedge/baseball/blob/2bf615c0de18cb7dbc2d4f8084c6e9afedea44b5/batted_ball/fielding.py#L54-L62).
The margin (ball_arrival - fielder_arrival) might be used to decide if
it’s a **“clanky” play** or error – e.g. if the fielder had time to camp
but drops it, that’s an error. In v1, outfielders were a bit too slow or
the margin logic was too strict, resulting in more hits than MLB norms.
The plan is to **increase catch success** especially on routine
flies[\[44\]](https://github.com/jlundgrenedge/baseball/blob/2bf615c0de18cb7dbc2d4f8084c6e9afedea44b5/docs/GAME_SIMULATION_NOTES.md#L99-L107).
Also, **infield pop-ups** were not explicitly modeled – ideally these
should be almost guaranteed outs due to long hang times and short
distance, which will be fixed by treating very high short flies as
automatic
outs[\[122\]](https://github.com/jlundgrenedge/baseball/blob/2bf615c0de18cb7dbc2d4f8084c6e9afedea44b5/docs/GAME_SIMULATION_NOTES.md#L117-L124). -
**Ground balls:** For a grounder, the engine checks if an infielder
reaches it before it gets through. This is similar: time to reach the
ball vs ball reaching/outfield grass. If fielded, then a throw is made
to the target base (usually first base for the batter, or second base
for a force). The throw’s success depends on arm strength (how quickly
it gets there) vs runner speed, and accuracy (errant throws can pull the
first baseman off the bag or go wild, resulting in errors). Currently,
ground balls often get ruled as hits – either because fielders can’t
reach them in time or the runner beats the throw. This is slated for
improvement by possibly slowing runner acceleration or improving
infielder range/reaction so that *routine grounders become outs* ~75% of
the time as in
MLB[\[124\]](https://github.com/jlundgrenedge/baseball/blob/2bf615c0de18cb7dbc2d4f8084c6e9afedea44b5/docs/GAME_SIMULATION_NOTES.md#L109-L116). -
**Throwing and Baserunner Advancement:** If a ball falls for a hit,
outfielders chase it down. The time this takes, plus their throw speed,
determines if runners can take extra bases. E.g., on a deep ball to the
wall, a fast runner might stretch a double to a triple if the outfielder
has a weak arm or bobbles the pickup. The simulation does incorporate
bobbles and error probabilities – e.g. an outfielder might misplay a
ball (e.g. overrunning it or a drop) rarely, which is scored as an error
allowing extra
advance[\[136\]](https://github.com/jlundgrenedge/baseball/blob/2bf615c0de18cb7dbc2d4f8084c6e9afedea44b5/batted_ball/fielding.py#L80-L88)[\[43\]](https://github.com/jlundgrenedge/baseball/blob/2bf615c0de18cb7dbc2d4f8084c6e9afedea44b5/batted_ball/fielding.py#L94-L101).
The baserunning AI uses the known locations and times to decide to send
runners or not (not overly sophisticated in v1, but based on reasonable
thresholds of distance and arm strength).

**Statistical Impact:** Fielding AI, along with the Batted Ball Model,
determines outcomes on balls in play – influencing batting average,
extra base hits, and even strikeouts indirectly (via foul territory
catches of pop-ups, though those are not explicitly in v1). If fielders
are too good, BABIP falls and offense dies. If they’re too poor, every
ball is a hit. v1 had *too many hits*, as noted in the GameSimulation
notes: **“too offense-heavy – very few outs on balls in
play”**[\[137\]](https://github.com/jlundgrenedge/baseball/blob/2bf615c0de18cb7dbc2d4f8084c6e9afedea44b5/docs/GAME_SIMULATION_NOTES.md#L95-L103).
Specifically, outfielders weren’t catching enough and infielders not
converting groundouts, leading to an inflated batting average. The
planned tuning (higher catch success and maybe slightly larger fielding
ranges) should create more outs. This will directly lower BABIP and
overall batting average closer to ~.300 on contact.

Notably, fielding doesn’t much affect K% or BB% (those are decided
before the ball is in play), but it does affect HR/FB indirectly (if
fielders could pull back home run balls or something – not modeled
here). In terms of **gameplay polish**, fielding AI is one area
earmarked for improvements in v2 (making sure the fielders behave
realistically, e.g., taking proper routes, hitting cut-off men, etc.,
though those details are beyond the current scope).

## 6. Plate Appearance Engine

This isn’t a single class but the coordination of subsystems to simulate
a full **plate appearance (PA)** from start to finish. It encompasses
the AtBatSimulator (pitch loop) and the integration with Game State
(outs, score, etc.).

**At-Bat Loop:** The PA engine loops pitch by pitch until a terminal
outcome is reached – strikeout, walk, or ball in play. We saw the
mechanics in the AtBatSimulator’s
`simulate_at_bat()`[\[3\]](https://github.com/jlundgrenedge/baseball/blob/2bf615c0de18cb7dbc2d4f8084c6e9afedea44b5/batted_ball/at_bat.py#L846-L855)[\[13\]](https://github.com/jlundgrenedge/baseball/blob/2bf615c0de18cb7dbc2d4f8084c6e9afedea44b5/batted_ball/at_bat.py#L908-L917).
It increments balls and strikes accordingly, and exits when strikes ≥3
or balls ≥4 or contact-in-play
occurs[\[138\]](https://github.com/jlundgrenedge/baseball/blob/2bf615c0de18cb7dbc2d4f8084c6e9afedea44b5/batted_ball/at_bat.py#L1007-L1015).
One thing to highlight is how **foul balls** are handled: on a contacted
ball, the code checks if it’s foul by evaluating launch angle and spray
angle (e.g. too high or extreme pull/push =
foul)[\[139\]](https://github.com/jlundgrenedge/baseball/blob/2bf615c0de18cb7dbc2d4f8084c6e9afedea44b5/batted_ball/at_bat.py#L961-L970).
If it’s foul and the batter had fewer than two strikes, it’s just a
strike
added[\[140\]](https://github.com/jlundgrenedge/baseball/blob/2bf615c0de18cb7dbc2d4f8084c6e9afedea44b5/batted_ball/at_bat.py#L977-L985).
With two strikes, extra fouls do not add strikes (except perhaps a cap
on very weak contact fouls was implemented with a random chance to count
as out to avoid infinite
fouls[\[141\]](https://github.com/jlundgrenedge/baseball/blob/2bf615c0de18cb7dbc2d4f8084c6e9afedea44b5/batted_ball/at_bat.py#L972-L980)
set at 22% for weak contacts). This rule prevents endless foul loops
while keeping most realism (in MLB, batters can foul off many pitches –
here extremely weak fouls have a small chance to be treated as an out to
increase balls in
play)[\[141\]](https://github.com/jlundgrenedge/baseball/blob/2bf615c0de18cb7dbc2d4f8084c6e9afedea44b5/batted_ball/at_bat.py#L972-L980).

**Outcome Determination:** When the loop ends, the AtBatResult is
finalized with an outcome code (“strikeout”, “walk”, or “in_play”) and
the final
count[\[138\]](https://github.com/jlundgrenedge/baseball/blob/2bf615c0de18cb7dbc2d4f8084c6e9afedea44b5/batted_ball/at_bat.py#L1007-L1015).
If it’s a K or BB, GameSimulator updates the appropriate stats and game
state (outs or base runner on first for
walk)[\[142\]](https://github.com/jlundgrenedge/baseball/blob/2bf615c0de18cb7dbc2d4f8084c6e9afedea44b5/batted_ball/game_simulation.py#L564-L573)[\[143\]](https://github.com/jlundgrenedge/baseball/blob/2bf615c0de18cb7dbc2d4f8084c6e9afedea44b5/batted_ball/game_simulation.py#L582-L590).
If it’s in play, the PlaySimulator takes over to resolve hit vs out and
runner
movement[\[144\]](https://github.com/jlundgrenedge/baseball/blob/2bf615c0de18cb7dbc2d4f8084c6e9afedea44b5/batted_ball/game_simulation.py#L524-L533)[\[145\]](https://github.com/jlundgrenedge/baseball/blob/2bf615c0de18cb7dbc2d4f8084c6e9afedea44b5/batted_ball/game_simulation.py#L551-L559).

**Integration with Game State:** The **GameState** object keeps track of
outs, runs, bases, etc., and is updated after each PA: - Strikeout: add
an out, batter is out, runners
hold[\[146\]](https://github.com/jlundgrenedge/baseball/blob/2bf615c0de18cb7dbc2d4f8084c6e9afedea44b5/batted_ball/game_simulation.py#L568-L576). -
Walk: batter to first, and if bases were loaded, it forces a
run[\[147\]](https://github.com/jlundgrenedge/baseball/blob/2bf615c0de18cb7dbc2d4f8084c6e9afedea44b5/batted_ball/game_simulation.py#L594-L603).
The code moves existing runners up one base in order (with the runner
from third scoring on a bases-loaded
walk)[\[147\]](https://github.com/jlundgrenedge/baseball/blob/2bf615c0de18cb7dbc2d4f8084c6e9afedea44b5/batted_ball/game_simulation.py#L594-L603). -
Ball in play: the result from PlaySimulator will contain how many bases
each runner took and if runs scored. The engine then updates the
BaseState (who’s on first/second/third)
accordingly[\[148\]](https://github.com/jlundgrenedge/baseball/blob/2bf615c0de18cb7dbc2d4f8084c6e9afedea44b5/batted_ball/game_simulation.py#L526-L534)[\[147\]](https://github.com/jlundgrenedge/baseball/blob/2bf615c0de18cb7dbc2d4f8084c6e9afedea44b5/batted_ball/game_simulation.py#L594-L603)
and adds runs via `score_run()` when needed (e.g. runner scoring from
third)[\[149\]](https://github.com/jlundgrenedge/baseball/blob/2bf615c0de18cb7dbc2d4f8084c6e9afedea44b5/batted_ball/game_simulation.py#L598-L601).
It also increments hit stats (single/double/etc.) or errors in GameState
as appropriate.

Between batters, it also manages innings: if 3 outs are made, it
switches sides (top/bottom) and resets the base runners, etc. The
GameSimulator’s loop continues until 9 innings (or extra if needed for a
tie, though v1 may not have extras fully in place).

**Statistics Collection:** Throughout, metrics are collected. There is a
`metrics_collector` that can log each pitch and contact (for computing
series stats like swing %, whiff %, etc.). After a series of games, the
`SeriesMetrics` aggregator computes overall rates like K%, BB%, HR/FB,
etc., which have been used to compare against MLB
benchmarks[\[150\]](https://github.com/jlundgrenedge/baseball/blob/2bf615c0de18cb7dbc2d4f8084c6e9afedea44b5/MLB_REALISM_FIXES_2025-11-20.md#L11-L19)[\[102\]](https://github.com/jlundgrenedge/baseball/blob/2bf615c0de18cb7dbc2d4f8084c6e9afedea44b5/MLB_REALISM_FIXES_2025-11-20.md#L20-L28).

**Significance:** The PA engine is essentially the **referee** that
makes sure the rules of baseball are followed (4 balls, 3 strikes,
runners advance on walks, etc.). It’s also where certain *game-level
behaviors* are implemented: - **Pitch sequencing memory:** The
AtBatSimulator tracks the last 2 pitch types to avoid throwing the same
pitch over and over
unrealistically[\[151\]](https://github.com/jlundgrenedge/baseball/blob/2bf615c0de18cb7dbc2d4f8084c6e9afedea44b5/batted_ball/at_bat.py#L843-L851)[\[152\]](https://github.com/jlundgrenedge/baseball/blob/2bf615c0de18cb7dbc2d4f8084c6e9afedea44b5/batted_ball/at_bat.py#L884-L888). -
**Stamina usage:** Each pitch thrown increments the pitcher’s count
(`pitches_thrown`), which the velocity and command functions use to
apply fatigue penalties over the course of a
game[\[153\]](https://github.com/jlundgrenedge/baseball/blob/2bf615c0de18cb7dbc2d4f8084c6e9afedea44b5/batted_ball/player.py#L122-L129)[\[154\]](https://github.com/jlundgrenedge/baseball/blob/2bf615c0de18cb7dbc2d4f8084c6e9afedea44b5/batted_ball/at_bat.py#L556-L564).
If a pitcher gets tired, their velocity drops (up to 4 mph slower) and
their command worsens (up to +3″
error)[\[155\]](https://github.com/jlundgrenedge/baseball/blob/2bf615c0de18cb7dbc2d4f8084c6e9afedea44b5/batted_ball/at_bat.py#L559-L567). -
**Safety and edge cases:** The code has safeguards (e.g., break out of
very long at-bats after some absurd number of pitches to prevent
infinite loops, though realistically the foul logic already handles
that). Also, it tracks things like if a half-inning is going too long
(more of an internal check).

In short, the Plate Appearance engine ties everything together in a
coherent sequence. It doesn’t produce any physics or AI logic itself,
but without it the simulation wouldn’t obey baseball’s count rules or
advance runners correctly. Think of it as the conductor coordinating the
pitcher, batter, and fielders each play.

## 7. Ratings Integration

The simulation uses a **unified ratings system** (0–100,000 scale
internally) for players, mapping these to real-world physical
parameters. This subsystem isn’t a single module but a set of mapping
functions (in `attributes.py`) and how those values feed into the above
systems.

**Philosophy:** The design is “physics-first” – meaning a player’s
ratings are converted to things like mph, feet, seconds, etc., which the
physics engine uses. So instead of a traditional “overall 85” type
rating, you have e.g. a **Pitcher’s velocity rating** that maps to a
4-seam speed, or a **Hitter’s barrel accuracy** that maps to a
millimeter error.

Key rating mappings (anchors were tuned with MLB averages in mind): -
**Pitcher Velocity:** 50,000 → ~91–93 mph fastball (MLB
avg)[\[65\]](https://github.com/jlundgrenedge/baseball/blob/2bf615c0de18cb7dbc2d4f8084c6e9afedea44b5/batted_ball/attributes.py#L128-L136).
Elite (85,000)
~98 mph[\[156\]](https://github.com/jlundgrenedge/baseball/blob/2bf615c0de18cb7dbc2d4f8084c6e9afedea44b5/batted_ball/attributes.py#L126-L134).
Minimum 0 → 76 mph (a very slow pitcher or position
player)[\[156\]](https://github.com/jlundgrenedge/baseball/blob/2bf615c0de18cb7dbc2d4f8084c6e9afedea44b5/batted_ball/attributes.py#L126-L134). -
**Pitcher Spin:** 50k → ~2250 rpm fastball spin (avg
MLB)[\[157\]](https://github.com/jlundgrenedge/baseball/blob/2bf615c0de18cb7dbc2d4f8084c6e9afedea44b5/batted_ball/attributes.py#L132-L140),
85k → ~2700 rpm
(elite)[\[157\]](https://github.com/jlundgrenedge/baseball/blob/2bf615c0de18cb7dbc2d4f8084c6e9afedea44b5/batted_ball/attributes.py#L132-L140). -
**Pitcher Stamina:** determines how many pitches before fatigue; e.g.
50k ~ 100 pitches. - **Pitcher Command (Control):** Mapped to that
Gaussian error sigma. Notably anchors were set so 50k control ≈ 6.5″
standard miss (roughly 8-9% walk rate) and 0 control ≈ 10″ miss (~20-25%
walk
rate)[\[60\]](https://github.com/jlundgrenedge/baseball/blob/2bf615c0de18cb7dbc2d4f8084c6e9afedea44b5/batted_ball/attributes.py#L144-L149).
Elite 85k ≈ 4.5″ miss (3-5%
walk)[\[60\]](https://github.com/jlundgrenedge/baseball/blob/2bf615c0de18cb7dbc2d4f8084c6e9afedea44b5/batted_ball/attributes.py#L144-L149).
These were explicitly tuned to match target walk percentages for various
pitcher qualities. - **Hitter Bat Speed (Power):** 50k → ~75 mph bat
swing
speed[\[24\]](https://github.com/jlundgrenedge/baseball/blob/2bf615c0de18cb7dbc2d4f8084c6e9afedea44b5/batted_ball/attributes.py#L140-L149)
(this was raised from 70 to 75 in a fix to get more exit
velo[\[24\]](https://github.com/jlundgrenedge/baseball/blob/2bf615c0de18cb7dbc2d4f8084c6e9afedea44b5/batted_ball/attributes.py#L140-L149)).
Elite 85k → ~85 mph, and 100k (superhuman)
~95 mph[\[24\]](https://github.com/jlundgrenedge/baseball/blob/2bf615c0de18cb7dbc2d4f8084c6e9afedea44b5/batted_ball/attributes.py#L140-L149).
This means an elite power hitter can generate 100+ mph exits when
combined with pitch speed and a good collision (e.g. 85 mph bat + 90 mph
pitch with a high q). - **Hitter Attack Angle (Launch Angle
inclination):** 50k → **+7°** swing
plane[\[91\]](https://github.com/jlundgrenedge/baseball/blob/2bf615c0de18cb7dbc2d4f8084c6e9afedea44b5/batted_ball/attributes.py#L8-L16)
(after recent recalibration; was 12° before). 85k (fly-ball hitter) →
~17°[\[91\]](https://github.com/jlundgrenedge/baseball/blob/2bf615c0de18cb7dbc2d4f8084c6e9afedea44b5/batted_ball/attributes.py#L8-L16).
0 → -5° (extreme ground-ball
hitter)[\[91\]](https://github.com/jlundgrenedge/baseball/blob/2bf615c0de18cb7dbc2d4f8084c6e9afedea44b5/batted_ball/attributes.py#L8-L16).
The variance of attack angle is separate: 50k variance ~3° std dev, 0
rating variance 8° (very inconsistent), 85k only 1° (very consistent
swing)[\[158\]](https://github.com/jlundgrenedge/baseball/blob/2bf615c0de18cb7dbc2d4f8084c6e9afedea44b5/batted_ball/attributes.py#L13-L19).
So you can have an elite consistent uppercut vs a sloppy hacker. -
**Barrel Accuracy:** This is the hitter’s ability to meet the ball on
the sweet spot. Anchors: 50k → **10 mm** average
error[\[159\]](https://github.com/jlundgrenedge/baseball/blob/2bf615c0de18cb7dbc2d4f8084c6e9afedea44b5/batted_ball/attributes.py#L20-L28),
85k → 5 mm, 0 → 35 mm
(terrible)[\[159\]](https://github.com/jlundgrenedge/baseball/blob/2bf615c0de18cb7dbc2d4f8084c6e9afedea44b5/batted_ball/attributes.py#L20-L28).
Decreasing these values was part of fixing low offensive output –
originally average was 13 mm and it was lowered to 10 mm to increase
good contact
rate[\[159\]](https://github.com/jlundgrenedge/baseball/blob/2bf615c0de18cb7dbc2d4f8084c6e9afedea44b5/batted_ball/attributes.py#L20-L28).
This rating feeds directly into the whiff and contact quality
calculations (as discussed, it scales whiff probability and determines
how far off the sweet spot collisions are). - **Timing (Swing
Precision):** Affects how late/early the batter is. 50k timing precision
~6 ms standard timing error, elite 3 ms, poor
15 ms[\[160\]](https://github.com/jlundgrenedge/baseball/blob/2bf615c0de18cb7dbc2d4f8084c6e9afedea44b5/batted_ball/attributes.py#L24-L31).
This timing error is converted to a horizontal contact point miss
(roughly 0.1 inch per ms in the contact
model)[\[161\]](https://github.com/jlundgrenedge/baseball/blob/2bf615c0de18cb7dbc2d4f8084c6e9afedea44b5/batted_ball/at_bat.py#L646-L654). -
**Plate Discipline (Zone Discernment):** 50k → factor 0.70 (avg), 85k →
0.88, 0 →
0.40[\[162\]](https://github.com/jlundgrenedge/baseball/blob/2bf615c0de18cb7dbc2d4f8084c6e9afedea44b5/batted_ball/attributes.py#L44-L48).
This is used as described in the swing decision model to modify swing
rates. - **Swing Decision Latency:** 50k → 130 ms reaction (avg), 85k →
100 ms (quick), 0 → 200 ms (very
slow)[\[163\]](https://github.com/jlundgrenedge/baseball/blob/2bf615c0de18cb7dbc2d4f8084c6e9afedea44b5/batted_ball/attributes.py#L38-L46).
This feeds the aggression factor for
swinging[\[164\]](https://github.com/jlundgrenedge/baseball/blob/2bf615c0de18cb7dbc2d4f8084c6e9afedea44b5/batted_ball/player.py#L672-L680). -
**Speed (Running):** 50k for runners ~27 ft/s, 85k ~30 ft/s as
mentioned, which affects running out hits and taking extra
bases[\[41\]](https://github.com/jlundgrenedge/baseball/blob/2bf615c0de18cb7dbc2d4f8084c6e9afedea44b5/batted_ball/attributes.py#L80-L88).
Similarly, fielding speed ratings map to those sprint speeds. -
**Fielding Skill Ratings:** As enumerated before – reaction, arm, etc.,
each with anchors (e.g., 50k arm for an OF ~75 mph, 85k ~88 mph
throw)[\[132\]](https://github.com/jlundgrenedge/baseball/blob/2bf615c0de18cb7dbc2d4f8084c6e9afedea44b5/batted_ball/attributes.py#L98-L101).

All these mappings are done via either linear scales or logistic curves
to allow some nonlinear scaling (the `piecewise_logistic_map` in
code)[\[165\]](https://github.com/jlundgrenedge/baseball/blob/2bf615c0de18cb7dbc2d4f8084c6e9afedea44b5/batted_ball/attributes.py#L24-L33)[\[166\]](https://github.com/jlundgrenedge/baseball/blob/2bf615c0de18cb7dbc2d4f8084c6e9afedea44b5/batted_ball/attributes.py#L64-L72).
The logistic mapping ensures diminishing returns at the extremes and a
smooth progression in the human range.

**How Ratings Tie In:** During simulation: - When a new **Hitter** or
**Pitcher** object is created, it stores these attribute objects. Calls
like `pitcher.get_pitch_velocity_mph(pitch_type)` will pull the raw
velocity rating and apply
modifiers[\[167\]](https://github.com/jlundgrenedge/baseball/blob/2bf615c0de18cb7dbc2d4f8084c6e9afedea44b5/batted_ball/player.py#L98-L106)[\[168\]](https://github.com/jlundgrenedge/baseball/blob/2bf615c0de18cb7dbc2d4f8084c6e9afedea44b5/batted_ball/player.py#L112-L120).
Likewise, `hitter.get_bat_speed_mph()` uses the mapping for bat
speed[\[169\]](https://github.com/jlundgrenedge/baseball/blob/2bf615c0de18cb7dbc2d4f8084c6e9afedea44b5/batted_ball/attributes.py#L137-L145)[\[170\]](https://github.com/jlundgrenedge/baseball/blob/2bf615c0de18cb7dbc2d4f8084c6e9afedea44b5/batted_ball/attributes.py#L151-L159). -
The **AtBatSimulator** at runtime doesn’t know about ratings explicitly;
it asks the Pitcher and Hitter for needed parameters (velocity, spin,
discipline factors, etc.), and those in turn apply the attribute
mappings. This design makes it easy to swap in different players and
have the physics respond realistically to their skills. - For example, a
pitcher with 90th percentile control and average velocity will throw
slower but hit spots, leading to fewer walks but also maybe fewer
strikeouts (since stuff is average). A wild power pitcher (high
velocity, low command) will throw bullets but miss the zone often,
yielding more walks and, depending on batter discipline, potentially
more strikeouts (if batters chase the heat) – the engine can reflect
these combinations.

**Calibration to Realism:** The ratings were initially set so that 50k
in everything produces roughly MLB-average outcomes. However, due to the
complex interactions in the simulation, some ratings had to be
re-weighted. For instance, raising bat speed anchors by ~5 mph was
required because even with higher collision efficiency, exit velos were
a bit
low[\[24\]](https://github.com/jlundgrenedge/baseball/blob/2bf615c0de18cb7dbc2d4f8084c6e9afedea44b5/batted_ball/attributes.py#L140-L149).
Similarly, attack angle anchors were adjusted to fix GB/FB
ratios[\[91\]](https://github.com/jlundgrenedge/baseball/blob/2bf615c0de18cb7dbc2d4f8084c6e9afedea44b5/batted_ball/attributes.py#L8-L16),
and barrel accuracy anchors tightened to increase offense (more solid
hits)[\[159\]](https://github.com/jlundgrenedge/baseball/blob/2bf615c0de18cb7dbc2d4f8084c6e9afedea44b5/batted_ball/attributes.py#L20-L28).
The command rating anchor was explicitly tied to walk rate expectations
as
noted[\[60\]](https://github.com/jlundgrenedge/baseball/blob/2bf615c0de18cb7dbc2d4f8084c6e9afedea44b5/batted_ball/attributes.py#L144-L149).

In a sense, the Ratings Integration subsystem is the **input
calibration** layer for the entire sim. To get MLB-like stats, these
mappings are tuned such that an “average” 50k player in each skill
produces average MLB results in each component (velocity, K%, BB%,
BABIP, etc.). Discrepancies in output indicate either mis-tuning or
interactions that weren’t linear. For example, even after tuning
individual pieces, the combined outcome was that K% ended up way low
(10%) and BB% way high (15%) in a test
series[\[171\]](https://github.com/jlundgrenedge/baseball/blob/2bf615c0de18cb7dbc2d4f8084c6e9afedea44b5/MLB_REALISM_FIXES_2025-11-20.md#L18-L22).
That means some rating interactions (like discipline + command + barrel
accuracy) produced emergent behavior that deviated from expectation.
Thus, further rating or model adjustments were needed (and will be in
v2). The goal is to eventually allow independent control – e.g., one
could adjust a “league environment” slider for strikeouts or offense by
nudging these mappings or a global multiplier, without breaking the
physics feel.

# Diagnostics: Root Causes of Realism Gaps (K%, BB%, HR/FB)

We identified three primary statistical areas where v1 of the simulation
fell short of MLB realism: **Strikeout rate (K%), Walk rate (BB%),** and
**Home Run per Fly Ball rate (HR/FB)**. Below we trace each issue to its
root causes in the code/math:

### Strikeout Rate (K%)

**Observed Problem:** The simulation’s strikeout rate was significantly
**too low**. In a 10-game test it was ~10.5% of plate appearances, less
than half the MLB norm
(~22%)[\[171\]](https://github.com/jlundgrenedge/baseball/blob/2bf615c0de18cb7dbc2d4f8084c6e9afedea44b5/MLB_REALISM_FIXES_2025-11-20.md#L18-L22).
Even after some fixes, the best achieved was ~8.2% in Pass
3[\[108\]](https://github.com/jlundgrenedge/baseball/blob/2bf615c0de18cb7dbc2d4f8084c6e9afedea44b5/MLB_REALISM_PASS4_FINDINGS_2025-11-20.md#L24-L28)
– extremely low.

**Root Cause:** **Batters make contact too easily** – the whiff
probability was dampened excessively by batter skill factors. The key
culprit lies in how **barrel accuracy** was being used in the whiff
calculation. In `Hitter.calculate_whiff_probability()`, the batter’s
barrel accuracy rating produces a **contact_factor** that scales the
base whiff
chance[\[18\]](https://github.com/jlundgrenedge/baseball/blob/2bf615c0de18cb7dbc2d4f8084c6e9afedea44b5/batted_ball/player.py#L892-L901).
Originally, an elite hitter (5 mm barrel error) got a 0.60× multiplier
(i.e. 40% reduction in whiffs), an average hitter (~10 mm) ~0.84× (16%
reduction)[\[19\]](https://github.com/jlundgrenedge/baseball/blob/2bf615c0de18cb7dbc2d4f8084c6e9afedea44b5/MLB_REALISM_FIXES_2025-11-20.md#L55-L63).
This was double-dipping, because barrel accuracy also makes better
contact when they do hit. The effect: good hitters very rarely struck
out in the sim. The dev notes confirm *“barrel accuracy was being
dual-used to also reduce whiffs too
much”*[\[172\]](https://github.com/jlundgrenedge/baseball/blob/2bf615c0de18cb7dbc2d4f8084c6e9afedea44b5/MLB_REALISM_FIXES_2025-11-20.md#L64-L68).
They adjusted those multipliers – for elites from 0.60× up to 0.80×
(only 20% whiff reduction), set average ~1.0× (no bonus), and poor
hitters ~1.6× (instead of
1.8×)[\[173\]](https://github.com/jlundgrenedge/baseball/blob/2bf615c0de18cb7dbc2d4f8084c6e9afedea44b5/MLB_REALISM_FIXES_2025-11-20.md#L56-L64)[\[174\]](https://github.com/jlundgrenedge/baseball/blob/2bf615c0de18cb7dbc2d4f8084c6e9afedea44b5/MLB_REALISM_FIXES_2025-11-20.md#L58-L61).
This change in code (see `contact_factor` formula recalibrated at
`player.py:892-900`) was aimed to raise K% into the 20%
range[\[175\]](https://github.com/jlundgrenedge/baseball/blob/2bf615c0de18cb7dbc2d4f8084c6e9afedea44b5/MLB_REALISM_FIXES_2025-11-20.md#L62-L67).

**Additional Factors:** Another contributor is the **foul ball logic** –
batters in v1 rarely strike out looking; most Ks would be swinging. But
if a batter can keep fouling off tough pitches, strikeouts might be
prolonged or turned into balls in play. The code did have a reduced foul
probability on weak contact (only 22% of “weak” contacts become foul,
down from
40%)[\[176\]](https://github.com/jlundgrenedge/baseball/blob/2bf615c0de18cb7dbc2d4f8084c6e9afedea44b5/batted_ball/at_bat.py#L970-L978)
to avoid infinite fouls, which *increases* balls in play. That could
lower K% because some borderline foul-tip strikes that a real batter
might eventually miss are instead put in play weakly in the sim. Thus,
batters put a ball in play eventually rather than whiffing.

**Evidence:** When the whiff model was aggressively tuned (50–100%
higher whiff baseline), K% did rise (up to 22.6% in an extreme
test)[\[177\]](https://github.com/jlundgrenedge/baseball/blob/2bf615c0de18cb7dbc2d4f8084c6e9afedea44b5/MLB_REALISM_PASS4_FINDINGS_2025-11-20.md#L50-L58).
However, that introduced unintended side-effects (as discussed, more
walks, lower offense) because of how it interacted with pitch counts.
The **coupling** of K% with the pitch-by-pitch at-bat process is a root
structural cause: more strikeouts mean more 2-strike counts and longer
ABs. The engine doesn’t currently simulate things like a batter giving
up contact to avoid a K (except via the swing decision logic which we
already tuned). So fundamentally, K% could not be fixed by one parameter
without affecting others – a sign that **strikeout events need
decoupling** (see Plan section).

In summary, the low K% came from *too much contact*. The math in the
whiff probability gave batters a generous contact ability, meaning few
swinging strikes. This was a code-level cause. A deeper systems cause is
that every strikeout must “earn” its 3 strikes, and batters were adept
at staying alive. Without an independent strikeout resolution mechanism,
any attempt to force more strikeouts cascaded into other
issues[\[178\]](https://github.com/jlundgrenedge/baseball/blob/2bf615c0de18cb7dbc2d4f8084c6e9afedea44b5/MLB_REALISM_PASS4_FINDINGS_2025-11-20.md#L63-L71)[\[81\]](https://github.com/jlundgrenedge/baseball/blob/2bf615c0de18cb7dbc2d4f8084c6e9afedea44b5/MLB_REALISM_PASS4_FINDINGS_2025-11-20.md#L74-L82).

### Walk Rate (BB%)

**Observed Problem:** The sim produced **too many walks**. It was around
15% of PAs, nearly double the MLB average
~8.5%[\[69\]](https://github.com/jlundgrenedge/baseball/blob/2bf615c0de18cb7dbc2d4f8084c6e9afedea44b5/MLB_REALISM_FIXES_2025-11-20.md#L19-L22).
In later tuning passes, ironically, attempts to fix K% made BB% even
worse (spiking above
20%)[\[179\]](https://github.com/jlundgrenedge/baseball/blob/2bf615c0de18cb7dbc2d4f8084c6e9afedea44b5/MLB_REALISM_PASS4_FINDINGS_2025-11-20.md#L38-L46)[\[82\]](https://github.com/jlundgrenedge/baseball/blob/2bf615c0de18cb7dbc2d4f8084c6e9afedea44b5/MLB_REALISM_PASS4_FINDINGS_2025-11-20.md#L48-L56).

**Root Cause:** **Pitch selection strategy overshot on “ball” pitches.**
The engine explicitly models a pitcher’s intention to throw outside the
zone (for strategic balls). These probabilities were initially set too
high. For example, on the first pitch (0-0 count) pitchers were only
aiming in the zone ~83% of the time (17% intentionally
out)[\[70\]](https://github.com/jlundgrenedge/baseball/blob/2bf615c0de18cb7dbc2d4f8084c6e9afedea44b5/MLB_REALISM_FIXES_2025-11-20.md#L75-L83).
In hitters’ counts like 2-0, 25% of the time they’d “pitch around”
(ball_intentional)[\[70\]](https://github.com/jlundgrenedge/baseball/blob/2bf615c0de18cb7dbc2d4f8084c6e9afedea44b5/MLB_REALISM_FIXES_2025-11-20.md#L75-L83).
And even in neutral counts, about 20% were intentional balls. These
rates caused an abundance of 3-ball counts and eventually walks. The fix
was straightforward: **reduce the intentional ball probabilities across
the board**. The code at `at_bat.py:412-441` reflects this
recalibration[\[180\]](https://github.com/jlundgrenedge/baseball/blob/2bf615c0de18cb7dbc2d4f8084c6e9afedea44b5/batted_ball/at_bat.py#L412-L420)[\[181\]](https://github.com/jlundgrenedge/baseball/blob/2bf615c0de18cb7dbc2d4f8084c6e9afedea44b5/batted_ball/at_bat.py#L430-L438): -
First pitch: lowered from 17% to 10% ball_intentional (now ~90% are
aimed as
strikes)[\[70\]](https://github.com/jlundgrenedge/baseball/blob/2bf615c0de18cb7dbc2d4f8084c6e9afedea44b5/MLB_REALISM_FIXES_2025-11-20.md#L75-L83). -
Hitter’s counts (e.g. 2-1): lowered from 25% to
15%[\[70\]](https://github.com/jlundgrenedge/baseball/blob/2bf615c0de18cb7dbc2d4f8084c6e9afedea44b5/MLB_REALISM_FIXES_2025-11-20.md#L75-L83). -
Even counts: 20% →
12%[\[182\]](https://github.com/jlundgrenedge/baseball/blob/2bf615c0de18cb7dbc2d4f8084c6e9afedea44b5/MLB_REALISM_FIXES_2025-11-20.md#L76-L84).

This brought the *intended* strike rate closer to MLB reality (~62–65%
of pitches are strikes in MLB). Since the command error already adds
some random balls, having 15-20% intentionally off was double-counting
wildness. After adjustment, expected walk rate dropped from 15% to
~8.5%[\[183\]](https://github.com/jlundgrenedge/baseball/blob/2bf615c0de18cb7dbc2d4f8084c6e9afedea44b5/MLB_REALISM_FIXES_2025-11-20.md#L80-L88).

**Additional Factors:** The **pitcher Control rating** mapping was
actually fine (as noted, 50k control was meant to yield ~8%
walks)[\[60\]](https://github.com/jlundgrenedge/baseball/blob/2bf615c0de18cb7dbc2d4f8084c6e9afedea44b5/batted_ball/attributes.py#L144-L149).
The issue was the AI logic layered on top. Another factor is the
**batter discipline**: if batters never chased, every off-target pitch
becomes a ball, increasing walks. In v1, batters do chase some
(especially poor discipline ones). The discipline tuning (using up to
85% reduction for elite) might have made good hitters walk a lot since
they rarely fish out of the zone. This means high BB% in the sim could
also be because the distribution of batter discipline or the lack of
called strike 3’s. But the dominant cause was the overzealous
intentional balls.

Interestingly, when they tried to *lower* walk rate by decreasing
intentional balls further (to near 0), they found an unexpected outcome:
K% dropped in some
cases[\[184\]](https://github.com/jlundgrenedge/baseball/blob/2bf615c0de18cb7dbc2d4f8084c6e9afedea44b5/MLB_REALISM_PASS4_FINDINGS_2025-11-20.md#L66-L73).
Why? Because with fewer walks, pitchers were always in the zone and
batters put more balls in play earlier, rather than going to deep counts
where strikeouts happen. This highlights the model’s coupling: **Walk
rate and K rate are inversely linked through count
dynamics**[\[178\]](https://github.com/jlundgrenedge/baseball/blob/2bf615c0de18cb7dbc2d4f8084c6e9afedea44b5/MLB_REALISM_PASS4_FINDINGS_2025-11-20.md#L63-L71).
The current architecture can’t change one without affecting the other.

**Evidence:** The developers’ fix list explicitly mentions walk rate was
high due to intentional ball rates, and that they adjusted those to
target
8.5%[\[57\]](https://github.com/jlundgrenedge/baseball/blob/2bf615c0de18cb7dbc2d4f8084c6e9afedea44b5/MLB_REALISM_FIXES_2025-11-20.md#L73-L81)[\[185\]](https://github.com/jlundgrenedge/baseball/blob/2bf615c0de18cb7dbc2d4f8084c6e9afedea44b5/MLB_REALISM_FIXES_2025-11-20.md#L82-L86).
After the fix, in the “best” calibrated scenario, walk rate was still
high (17%) – suggesting either not all fixes were applied or other
interactions (like those whiff changes) pushed it up
again[\[108\]](https://github.com/jlundgrenedge/baseball/blob/2bf615c0de18cb7dbc2d4f8084c6e9afedea44b5/MLB_REALISM_PASS4_FINDINGS_2025-11-20.md#L24-L28).
The Pass 4 experiments showed even when they cut intentional balls
drastically (to 3% on first pitch), walk % stayed
~21%[\[82\]](https://github.com/jlundgrenedge/baseball/blob/2bf615c0de18cb7dbc2d4f8084c6e9afedea44b5/MLB_REALISM_PASS4_FINDINGS_2025-11-20.md#L48-L56).
That counterintuitive result was explained by the **longer at-bats from
more whiffs** – more pitches per PA gave more chances to reach four
balls[\[186\]](https://github.com/jlundgrenedge/baseball/blob/2bf615c0de18cb7dbc2d4f8084c6e9afedea44b5/MLB_REALISM_PASS4_FINDINGS_2025-11-20.md#L66-L74).
This is an architectural limitation: in reality, pitchers who get into
many deep counts might strike out a lot *and* walk a lot (think Gerrit
Cole early in career), whereas efficient pitchers have low of both. Our
simulation currently applies broad changes to everyone, causing a seesaw
effect rather than allowing independent variation.

In short, the high BB% issue was mainly a design tuning error in pitch
intent logic. The engine was “playing it safe” too often. Reducing those
safe pitches was the direct remedy. But to truly fix it under all
conditions, the model might need to simulate smarter situational
pitching (e.g. only nibble when a power hitter is up or base open)
rather than a flat probability each count. Also, introducing umpire
variability (some of those borderline 3-2 pitches could be strike three
calls, preventing a walk) might naturally curb walks without changing
how pitchers pitch. These deeper issues will be addressed in v2.

### Home Run per Fly Ball Rate (HR/FB)

**Observed Problem:** *Extremely* low HR/FB in early simulations –
around 0.5–1% of fly balls became home
runs[\[187\]](https://github.com/jlundgrenedge/baseball/blob/2bf615c0de18cb7dbc2d4f8084c6e9afedea44b5/MLB_REALISM_FIXES_2025-11-20.md#L22-L25).
This is an order of magnitude below MLB’s ~12–13%. Essentially, almost
no homers were happening despite plenty of fly balls. Later calibration
improved HR frequency somewhat, but even the best scenario saw only 6.3%
HR/FB[\[108\]](https://github.com/jlundgrenedge/baseball/blob/2bf615c0de18cb7dbc2d4f8084c6e9afedea44b5/MLB_REALISM_PASS4_FINDINGS_2025-11-20.md#L24-L28)[\[109\]](https://github.com/jlundgrenedge/baseball/blob/2bf615c0de18cb7dbc2d4f8084c6e9afedea44b5/MLB_REALISM_PASS4_FINDINGS_2025-11-20.md#L90-L99).

**Root Cause:** **Insufficient exit velocity on fly balls**, stemming
from the collision model’s single-parameter tuning. Initially, the
bat-ball physics (low q value plus heavy penalties) capped how hard
balls were hit. Many fly balls were likely high but not deep (e.g.
85–90 mph, 35° launch – resulting in routine outs). The **energy
transfer (q)** was set too low for balls to reach home-run distance. As
per the analysis, with q~0.09 effective, even perfect contact at 90 mph
pitch yielded ~90 mph
exit[\[27\]](https://github.com/jlundgrenedge/baseball/blob/2bf615c0de18cb7dbc2d4f8084c6e9afedea44b5/MLB_REALISM_FIXES_2025-11-20.md#L94-L102),
which for a 25–30° launch might travel ~350 ft at best – a fly out. So
even though 54% of balls were flies, virtually all died in the
park[\[188\]](https://github.com/jlundgrenedge/baseball/blob/2bf615c0de18cb7dbc2d4f8084c6e9afedea44b5/MLB_REALISM_FIXES_2025-11-20.md#L16-L24).

To fix this, they raised collision efficiency dramatically (to q=0.18) –
this made the average exit velo *too high* (100+ mph regularly) and
overshot HR/FB to unrealistic
levels[\[105\]](https://github.com/jlundgrenedge/baseball/blob/2bf615c0de18cb7dbc2d4f8084c6e9afedea44b5/batted_ball/constants.py#L246-L255).
They dialed back to find a middle ground. The fundamental issue
revealed: using one parameter (q) to tune power means a trade-off
between overall EV and the tail of the EV distribution. With q=0.04 or
0.05, you got enough 100+ mph hits to have ~12% HR/FB, but then
*average* EV was ~96 mph (way above MLB avg ~88) and hard-hit
~55%[\[105\]](https://github.com/jlundgrenedge/baseball/blob/2bf615c0de18cb7dbc2d4f8084c6e9afedea44b5/batted_ball/constants.py#L246-L255)[\[109\]](https://github.com/jlundgrenedge/baseball/blob/2bf615c0de18cb7dbc2d4f8084c6e9afedea44b5/MLB_REALISM_PASS4_FINDINGS_2025-11-20.md#L90-L99).
With q=0.03, average EV ~94 (still a bit high), hard-hit 40% (spot on),
but HR/FB only
~6%[\[189\]](https://github.com/jlundgrenedge/baseball/blob/2bf615c0de18cb7dbc2d4f8084c6e9afedea44b5/MLB_REALISM_PASS4_FINDINGS_2025-11-20.md#L92-L100).
So at q=0.03, the distribution’s tail is still too thin – not enough of
those 105+ mph, ideal-launch drives that account for most homers.

Why not just pick q=0.04 to get HR/FB right? Because then too many other
metrics went out of whack (as shown by only 1/10 benchmarks passing at
q=0.04 vs 5/10 at
q=0.03)[\[105\]](https://github.com/jlundgrenedge/baseball/blob/2bf615c0de18cb7dbc2d4f8084c6e9afedea44b5/batted_ball/constants.py#L246-L255)[\[190\]](https://github.com/jlundgrenedge/baseball/blob/2bf615c0de18cb7dbc2d4f8084c6e9afedea44b5/batted_ball/constants.py#L251-L260).
That indicated a deeper coupling: **HR/FB could not be adjusted without
affecting exit velocity and hard-hit
averages**[\[109\]](https://github.com/jlundgrenedge/baseball/blob/2bf615c0de18cb7dbc2d4f8084c6e9afedea44b5/MLB_REALISM_PASS4_FINDINGS_2025-11-20.md#L90-L99)[\[191\]](https://github.com/jlundgrenedge/baseball/blob/2bf615c0de18cb7dbc2d4f8084c6e9afedea44b5/MLB_REALISM_PASS4_FINDINGS_2025-11-20.md#L96-L101).

Another angle: the **launch angle distribution** might not have enough
optimal HR-launches. Initially it had *too many* fly balls, but perhaps
too many of those were high pop flies. After lowering attack angles, the
fly ball rate went to ~34%
(normal)[\[97\]](https://github.com/jlundgrenedge/baseball/blob/2bf615c0de18cb7dbc2d4f8084c6e9afedea44b5/MLB_REALISM_FIXES_2025-11-20.md#L42-L48).
But it’s possible a lot of those flies are lower EV (because high attack
angle swings sacrifice some EV, or because the best EV hits might be
more line-drive-ish). If the simulation isn’t producing enough
**“barrelled” balls** (high EV, 25–30° launch), HR/FB suffers. The
contact quality label “barrel” typically corresponds to those ideal
homers. If barrel rate was low (it likely was, given low hard-hit%),
that directly cuts HR/FB. They improved barrel rate by lowering
barrel_accuracy
penalties[\[159\]](https://github.com/jlundgrenedge/baseball/blob/2bf615c0de18cb7dbc2d4f8084c6e9afedea44b5/batted_ball/attributes.py#L20-L28),
which did raise hard-hit%. That got ISO and hard-hit% in
line[\[192\]](https://github.com/jlundgrenedge/baseball/blob/2bf615c0de18cb7dbc2d4f8084c6e9afedea44b5/MLB_REALISM_FIXES_2025-11-20.md#L22-L26)[\[193\]](https://github.com/jlundgrenedge/baseball/blob/2bf615c0de18cb7dbc2d4f8084c6e9afedea44b5/MLB_REALISM_FIXES_2025-11-20.md#L126-L131),
meaning more doubles and such, but HR/FB remained low. This suggests the
**carry model** or aerodynamic factors might also be at play – perhaps
the spin and drag settings yield less carry than MLB balls. However, the
more likely cause is the one identified: a single collision efficiency
parameter can’t shape the distribution tail independently.

**Evidence:** The power metrics fix in the docs shows exactly the
calculation and resolution: - Problem: q too low (0.13 base, ~0.09
effective), yielding avg EV 85 and HR/FB
~0.6%[\[103\]](https://github.com/jlundgrenedge/baseball/blob/2bf615c0de18cb7dbc2d4f8084c6e9afedea44b5/MLB_REALISM_FIXES_2025-11-20.md#L91-L100)[\[194\]](https://github.com/jlundgrenedge/baseball/blob/2bf615c0de18cb7dbc2d4f8084c6e9afedea44b5/MLB_REALISM_FIXES_2025-11-20.md#L126-L129). -
Solution: bump wood bat q to 0.18 (they later revised this down after
testing)[\[84\]](https://github.com/jlundgrenedge/baseball/blob/2bf615c0de18cb7dbc2d4f8084c6e9afedea44b5/MLB_REALISM_FIXES_2025-11-20.md#L110-L118). -
Outcome expectation: HR/FB to ~12.5%, Hard-hit ~40%, ISO ~0.150 achieved
when effective q
~0.14[\[30\]](https://github.com/jlundgrenedge/baseball/blob/2bf615c0de18cb7dbc2d4f8084c6e9afedea44b5/MLB_REALISM_FIXES_2025-11-20.md#L116-L124)[\[193\]](https://github.com/jlundgrenedge/baseball/blob/2bf615c0de18cb7dbc2d4f8084c6e9afedea44b5/MLB_REALISM_FIXES_2025-11-20.md#L126-L131).

Later, the Pass 4 findings explicitly note **“cannot independently tune
EV and HR/FB with single
parameter”**[\[109\]](https://github.com/jlundgrenedge/baseball/blob/2bf615c0de18cb7dbc2d4f8084c6e9afedea44b5/MLB_REALISM_PASS4_FINDINGS_2025-11-20.md#L90-L99)[\[191\]](https://github.com/jlundgrenedge/baseball/blob/2bf615c0de18cb7dbc2d4f8084c6e9afedea44b5/MLB_REALISM_PASS4_FINDINGS_2025-11-20.md#L96-L101).
They tried q=0.04 vs 0.03 to illustrate this: 12.8% HR/FB at q=0.04 but
EV too high, vs correct EV at q=0.03 but HR/FB half
short[\[189\]](https://github.com/jlundgrenedge/baseball/blob/2bf615c0de18cb7dbc2d4f8084c6e9afedea44b5/MLB_REALISM_PASS4_FINDINGS_2025-11-20.md#L92-L100).

Therefore, the root cause of low HR/FB is the **lack of a separate
mechanism to boost the frequency of very hard-hit fly balls**. The
engine could get either overall hard contact right or HRs right, but not
both simultaneously with the current design. Factors such as
backspin-lift might also be a cause – if the model underestimates how
far a 98 mph, 30° fly goes (perhaps due to drag or not enough lift),
that could reduce HRs. The constants did reduce lift a bit to fix hang
time[\[116\]](https://github.com/jlundgrenedge/baseball/blob/2bf615c0de18cb7dbc2d4f8084c6e9afedea44b5/batted_ball/constants.py#L52-L60),
which might have unintentionally made some would-be homers fall short.
In v2, they might address this by refining the drag/lift model (carry
model) so that high-backspin balls travel the extra 5–10 feet needed to
clear fences.

In summary, the low HR/FB boiled down to *not enough balls hit 380+ ft*.
That was mainly due to not enough exit velocity on those trajectories,
traced to the collision efficiency and contact model limitations. Once
that was partially fixed, it became clear a second parameter or approach
is needed to fine-tune HR production without skewing all contact quality
metrics.

------------------------------------------------------------------------

**Coupling Summary:** These diagnostics show a common thread: K%, BB%,
HR/FB are entangled with each other and with other stats in the current
simulation. K% ↔ BB% trade-off via pitch count dynamics, and HR/FB ↔ EV
↔ overall offense trade-off via collision physics. This motivates an
architectural rework in v2.0 to **decouple these factors**, giving us
independent “knobs” for each. We now turn to designing that improved
architecture.

# Proposed v2.0 Engine Design (Decoupling K, BB, HR/FB)

To address the above issues, Version 2.0 will introduce a more modular
architecture where strikeouts, walks, and power can be tuned
**independently** without unintentional side effects. The overarching
strategy is to **decouple the subsystems** responsible for K%, BB%, and
HR/FB. Below are the design changes and new components planned:

## 1. **Decoupled Strikeout Model (Whiff & Foul System Overhaul)**

**Goal:** Achieve correct K% (~22%) without artificially increasing walk
length or suppressing offense. We will introduce a **two-stage strikeout
model**: - **Pitching/Swing Stage:** As before, each pitch can be a
strike or ball, swung or taken, with possible whiff. We will recalibrate
this stage to produce a realistic number of two-strike counts and
swinging strikes. Importantly, we will *limit the maximum length of an
at-bat* by curbing infinite foul balls. - **Strikeout Resolution
Stage:** Once two strikes are reached, we introduce a new mechanic: a
**“put-away chance”** that a strikeout occurs *on the next pitch*
(swinging or looking) independent of the usual count progression. This
represents the pitcher making a great pitch or the batter getting
overmatched. In practice, it means we don’t always require a third
swinging strike event – there will be a tuned probability that a
two-strike count ends in a K on each subsequent pitch. This is akin to
modeling the distribution of how often strikeouts happen after various
foul counts.

**Implementation:** We’ll add a function
`maybe_strikeout_now(batter, pitcher, count)` that triggers when count
is 2 strikes. For example, after a foul with 2 strikes, instead of
always continuing, there’s, say, a 10–15% chance (tunable) that the
batter is eventually sat down on the next pitch (strikeout) regardless
of contact made (we can narratively interpret this as the batter swung
and missed a tough pitch or was caught looking on a borderline pitch).
This probability can be adjusted to hit the target K% **without**
requiring endless pitch-by-pitch attrition. Essentially, it shortcuts
some at-bats to strikeouts. This might feel like “cheating,” but we’ll
integrate it in a subtle way – e.g., if a batter has already fouled off
3+ pitches with 2 strikes (demonstrating difficulty finishing the PA),
the put-away chance increases each pitch. This mimics real life where
eventually the pitcher usually wins these battles.

**Whiff and Contact Attributes:** We will **split the batter’s contact
skill into two ratings**: - a **Contact frequency** rating (affecting
whiff probability) and - a **Contact quality** rating (affecting how
well they hit it when they do connect).

Currently, Barrel Accuracy was doing both. In v2, for example,
**Vision** or “Hit Probability” attribute could determine pure
swing-and-miss tendency (K%. e.g., Joe Player might strike out a lot but
still barrel the ones he hits). Meanwhile, **Barrel Accuracy** (or a
renamed Power/Quality attribute) would affect exit velocity and quality
of contact on those that are hit. This decoupling lets us tune K% via
the Vision attribute independently. For instance, we can lower the
Vision of all players by 10% to increase K% without altering their
Power.

**Foul Ball Tuning:** We’ll implement a **foul limit or difficulty**:
Each successive foul with 2 strikes slightly increases the chance of the
next pitch resulting in an out (strikeout or ball in play) instead of
another foul. This is another way to ensure strikeouts happen at a
reasonable clip without infinite fouls. MLB data shows batters rarely
foul more than ~4–5 times with 2 strikes. We’ll enforce a soft cap:
e.g., after 3 fouls with 2 strikes, the batter’s contact rating for
additional fouls effectively degrades (simulating that pitchers will
eventually win). This can be done by multiplying whiff probability by a
factor \>1 on each successive 2-strike foul.

**Pitcher “Put-Away” Ability:** We can introduce a new **Pitcher
attribute: “put-away pitch” effectiveness**. This would complement the
whiff multiplier (stuff). It specifically boosts strikeout probability
when the batter has 2 strikes. Some pitchers have trouble finishing
hitters; others excel. This attribute would be part of
`get_pitch_whiff_multiplier` or a new function used in the strikeout
resolution stage. For example, a pitcher with an elite slider might get
a +20% K finisher boost in two-strike counts.

**Looking Strikeouts:** To allow strikeouts without additional swings
(which would add pitches), we’ll incorporate a **called strike 3
probability**. In MLB about 25% of Ks are looking. We can simulate this
by occasionally deeming the final strike came from the batter not
swinging at a borderline pitch. This ties in with the umpire model (see
below) – basically, with 2 strikes, a pitch slightly outside might be
called a strike to ring up the batter. This provides another pathway to
a K without lengthening the at-bat.

**Expected Outcome:** With these changes, we have direct control over
K%. The *put-away chance* and *foul limit* are knobs to dial aggregate
K% up or down **without** affecting how often batters walk. We’d
calibrate these so that with average ratings, K% comes out ~22%. For
instance, if we want more Ks, we increase the base put-away probability
or reduce the foul cap. This does not require increasing whiffs on every
pitch (which would also increase pitch count and walks); it specifically
targets the scenario of extended 2-strike battles.

This effectively **decouples K-rate from the rest of the pitch count
mechanics**, fulfilling the design goal. It preserves the physics-based
feel for the first two strikes, and only uses a probabilistic shortcut
at the end of the PA.

## 2. **Dedicated Walk/Control Module (Tuning Walk Rate)**

**Goal:** Control BB% (~8%) separately, by modeling pitcher control and
umpire calls in a more nuanced way, without influencing K% or overall
pitch count drastically.

**Pitcher Control as a Distribution:** We will refine the **pitch
location model**. Instead of the current mix of intentions and a fixed
error distribution, v2 will explicitly simulate each pitch’s miss
distance as a sum of: - A **systematic miss** (intentional or due to
wildness) and - A **random miss** (Gaussian error).

We’ll introduce a **Pitcher Control Module** that, given a pitcher’s
control rating and situation, outputs a probability of the pitch being
in the strike zone. This can be thought of as replacing the hardcoded
intention probabilities. For example, a pitcher with average control
might have a baseline 60% zone%. If facing a dangerous hitter, the
module might strategically lower that to 55% (pitch carefully), whereas
against a weak hitter or pitcher ahead in count, it might go to 70%
(challenge in zone). This logic can use pitcher’s own “nibbling
tendency” trait and the base-out state (e.g., base open, be more
careful). The key is these probabilities are tunable globally. We can
adjust a global aggressiveness slider to hit a target league walk rate.

**Count-by-Count Tuning:** We’ll maintain count-based behavior but make
it data-driven. For MLB realism: first-pitch strike \~~60%, 3-0 strike
\~~ grooved high % since pitchers don’t want a walk, etc. We’ll ensure
the module’s output replicates those (the current values are now closer
after the fix: 0-0 ~90% strike intents
etc.[\[55\]](https://github.com/jlundgrenedge/baseball/blob/2bf615c0de18cb7dbc2d4f8084c6e9afedea44b5/batted_ball/at_bat.py#L414-L422)).
The difference is in v2 these won’t be magic numbers but derived from
pitcher control and strategy parameters that we can calibrate.

**Umpire and Framing Model:** A big decoupling tool for walks is to
simulate the variability in called strikes on borderline pitches: - We
add an **Umpire module** that for each pitch on the edge of the zone
(say within 1–2 inches of the zone boundary) has a certain chance to
call it a strike or ball, influenced by catcher framing rating. This
introduces a stochastic element that can be tuned without altering
pitcher behavior. For instance, if the league walk rate is high, we
could globally make umpires a tad more generous on strikes (calling more
borderline strikes, effectively reducing walks). - Catcher Framing
attribute: a good framer increases the odds that a borderline ball is
called a strike. This doesn’t change true zone % but changes outcome of
close pitches. It’s a way to reduce walks (and increase strikeouts
looking) especially for teams with good catchers.

**Intentional Walks / Pitch Around logic:** We’ll formalize “intentional
balls” as a separate decision. Instead of being baked into every pitch,
it will be a scenario-based toggle: if a weak hitter is on deck or
setting up a double play, etc., the AI may semi-intentionally walk a
batter. That’s more of a managerial layer. In normal at-bats, pitchers
will generally aim for the zone proportional to their control ability;
we remove the random 10–20% outright non-competitive pitch except when
logically appropriate (e.g., 0-2 count waste pitch remains but that’s
part of strategy logic).

**Better Integration with K%:** By removing the heavy intentional ball
probabilities, we make walks mostly a function of pitcher missing the
zone (control) and batters not chasing. In v2, if we manage to get K%
right via stage 1, the pitch counts won’t balloon unpredictably. Walk
rate can then be tuned by adjusting how tight the umpire zone is and how
much miss distance pitchers have. We can also add a **“patient hitter”
trait** (batter attribute for drawing walks) that doesn’t affect K. For
example, separate from discipline (which affects chase), an attribute
that simply increases the likelihood the batter will take close pitches
even if they are strikes (hoping for a walk). But that might reduce K
looking or increase them; careful tuning needed.

**Projected Outcome:** With a dedicated control module, we can dial the
league walk rate to 8% by adjusting one parameter (say, the effective
sigma of the pitch distribution globally or the border-call bias).
Because the K model is separate, adjusting walks won’t inadvertently
change K. If walks are too high, we could globally tighten the zone
(slightly larger effective strike zone via umpire calls) – batters will
get fewer free passes but their strikeouts looking will rise a bit
(which contributes to K% in a different way than swinging Ks). That is
fine since we can offset swinging K if needed with our whiff model.

In sum, the walk tuning is achieved by **isolating the control vs
outcome relationship** and adding the human element of umpire calls.
This gives multiple independent levers: pitcher accuracy, batter
patience, and umpire strictness – all of which can be adjusted to
achieve target BB% without disturbing other parts of the sim.

## 3. **Two-Parameter Power Model (Exit Velo & HR Probability)**

**Goal:** Enable independent tuning of overall exit velocity
distribution vs. home run frequency. We will separate the factors that
determine how hard the ball is hit from those that determine how many of
the hard-hit balls become homers.

**Collision Model Split:** In v2, the **collision will output two key
values**: *Raw Exit Velocity* and a *“Lifted Distance Boost”* (or a
proxy for how well the ball was optimized for carry). We introduce a
second parameter alongside q: - **Parameter A (Power):** governs the
kinetic energy transfer – essentially the average exit velocity and
hard-hit rate. This is similar to q but we will treat it as calibrating
EV to match league avg EV and hard-hit%. - **Parameter B (Barrel Lift
Factor):** governs how frequently a batted ball is a *home-run
trajectory* given its EV.

How to implement Parameter B? A couple of approaches: - **Launch Angle &
Backspin correlation:** We can adjust the relationship between contact
point and launch angle. For instance, currently a perfect contact might
be around 12–15° launch (line drive). We could introduce variability or
a slight bias so that a fraction of high EV contacts get higher launch
angles (~25–30°) more often. Essentially, decouple the correlation that
sometimes exists where the hardest hits tend to be lower liners. In v2,
even a super hard hit can be launched at 30° (a monster homer) or at 10°
(scorching double) with some probability. By tuning that probability, we
affect HR/FB. This could be done via a **“swing type” selection**: e.g.,
a power hitter might occasionally uppercut more on a 3-0 count. We can
model that as: for a given bat swing, decide if it’s a normal swing or a
“power swing” that trades a bit of contact probability for a higher
loft. Those power swings, when contact is made, produce more HR-friendly
balls. This way, overall EV might stay the same, but distribution of
launch angles for high EV balls shifts upward. - **Carry &
Aerodynamics:** We implement a more advanced ball flight model that
factors in spin-rate differences and drag variations. In reality, not
all 100 mph, 30° flies go the same distance – spin (backspin especially)
can add or subtract carry. We can artificially boost Parameter B by
reducing drag on high backspin balls (e.g., incorporate **reduced Cd for
high backspin**, simulating the ball riding the air). Or conversely,
increase lift coefficient for those balls. The net effect: a certain
percentage of fly balls that previously fell at the warning track now
carry over the fence. We could make this a tunable global “carry
factor.” If HR/FB is low, increase carry factor by 5% – home runs go up
without needing more 110 mph hits. This is a physically-plausible tweak
since MLB balls sometimes are “juiced” (lower drag). - **Explicit Home
Run Probability Function:** As a more abstract solution (less physics-y
but effective), we could after each ball is hit, apply a slight overlay:
if a ball is a deep fly (say \>300 ft) but not quite a HR, have a small
chance to “boost” it into a homer. Essentially assign a probability that
a given fly ball becomes a HR based on its EV and angle. This
probability can be tuned. This is somewhat akin to how one might
post-process to fix HR rate (like a roll of the dice turning some outs
into HRs). However, we prefer to embed it in physics if possible.

We will likely combine the first two: improve the launch angle/backspin
modeling (Parameter B influences how often a hitter drives the ball vs
hits a high fly), and refine the aerodynamic carry (Parameter B also
influences how far given launch/EV goes).

**Bat Speed vs Launch Trade-off:** We’ll simulate **situational
swinging**. For example, on a 2-0 count, a hitter might do an all-in
power swing (yielding higher launch angle and EV) vs with 2 strikes they
might shorten up (lower EV, maybe lower angle). By incorporating this
behavior, we can up the incidence of optimal homers on certain counts
without inflating average EV across all swings. This count-based
approach can raise HRs (since many HRs come when ahead in count). It
decouples HR/FB because you can increase aggressiveness on hitter’s
counts to produce HR swings, without changing what happens on other
swings that determine EV distribution. This is complex but doable –
essentially give batters an “approach” AI.

**Player Attributes for Power:** We can introduce a **Power – Loft
split**. Two batters might both have a 90 power (can hit ball hard), but
one has a “fly ball tendency” that yields more HR (at cost of maybe more
pop-ups), whereas the other is a line-drive hitter who hits fewer HR per
hard-hit ball. In v2, a **Fly Ball Tendency attribute** (or use the
existing SPRAY/LAUNCH angle attributes in a more nuanced way) will allow
some hitters to have high HR/FB (e.g., 20% – they maximize their hard
contact into homers) vs others lower (10% – they hit a lot of hard
doubles). By tuning the distribution of this attribute in the league, we
can match overall HR/FB. And crucially, we can tune it globally if
needed: e.g., if league HR/FB is low, increase all hitters’ loft
tendency by a small amount.

**Carry Model Improvements:** We plan to refine the physics: - Include
**spin decay** and more granular drag modeling so that we can adjust the
outcome of high-fly balls. Possibly integrate a **wind resistance
factor** that we can tweak separate from other pieces. - We could also
explicitly model the **“drag coefficient variability”** that MLB saw in
different years (the 2019 juiced ball had lower drag). By coding that
in, we have a single parameter (average Cd or seam height parameter) to
tune HR distance without altering EV. Lower Cd =\> balls carry further
=\> HR/FB up, while EV, hard-hit remain same.

**Expected Outcome:** Using these two parameters: - Parameter A
(power/exit velo) will be set so that league avg EV ~88 mph, hard-hit
~35-40%, ISO ~0.150 (doubles/triples + HR). This ensures general offense
is right (a combination of singles and XBH). - Parameter B (HR tuning)
will be set such that given the EV distribution from A, the fraction of
fly balls leaving the park ~12%. We adjust B (via aerodynamic or angle
biases) to reach that target. If later we want to simulate a “dead ball”
era vs a “live ball” era, we can lower or raise Parameter B easily
(instead of fiddling with q and breaking everything else).

By decoupling in this way, if we want more homers we don’t necessarily
increase batting average or doubles – we specifically allow more of the
existing fly balls to be homers. Conversely, if too many homers, we can
dial back carry or launch angle a bit without reducing overall exit
velos that would also kill doubles.

## 4. **Enhanced Ball Drag & Spin (Carry Model Refinement)**

*(This ties into Parameter B above but is worth detailing as a new
module.)*

We will implement a more detailed **ball flight aerodynamics module**: -
Account for **spin axis tilt** properly (sidespin vs backspin
differences affecting hooking or tailing of fly balls, which can
slightly reduce distance if sidespin is high – we can simulate that). -
**Dynamic Drag:** We already have Re dependence; we’ll calibrate it with
Statcast distance data. Perhaps introduce a **slight altitude effect on
drag** beyond just air density (since high altitude also changes Magnus
effect). - Consider **Atmospheric conditions** like humidity (MLB found
different drag in different climates). - **Spin Decay:** In v1, spin
might be constant. In reality, spin might decay a bit during flight. We
can introduce a spin decay rate which effectively could reduce lift over
time for extremely high fly balls. Tuning this could help manage hang
times independently of initial exit conditions.

The reason for this subsystem is to have additional dials for how far
the ball carries. For example, if HR/FB is low, one can reduce spin
decay or reduce drag globally by 5%. That might add a few feet to fly
balls, turning some outs into homers, *without changing how hard the
ball was hit*. That’s a pure carry adjustment.

Additionally, by simulating these in detail, we ensure **consistency**:
e.g., if we want to simulate a change in baseball (2021 MLB changed ball
to increase drag, HRs dropped), we can do that by adjusting one
constant.

## 5. **Independent Tuning Knobs Summary:**

By the above changes, we effectively create independent controls for: -
**K% (via whiff/put-away probabilities)** – e.g., a global multiplier on
whiff probability or on the 2-strike put-away chance tunes
K%[\[195\]](https://github.com/jlundgrenedge/baseball/blob/2bf615c0de18cb7dbc2d4f8084c6e9afedea44b5/MLB_REALISM_PASS4_FINDINGS_2025-11-20.md#L118-L126). -
**BB% (via zone% and umpire calls)** – e.g., tweak target zone
percentage or widen/narrow the called strike zone to tune
walks[\[196\]](https://github.com/jlundgrenedge/baseball/blob/2bf615c0de18cb7dbc2d4f8084c6e9afedea44b5/MLB_REALISM_PASS4_FINDINGS_2025-11-20.md#L122-L128). -
**HR/FB (via ball carry and launch distribution)** – e.g., adjust the
drag coefficient or increase launch angle for high EV hits to tune HR
production[\[197\]](https://github.com/jlundgrenedge/baseball/blob/2bf615c0de18cb7dbc2d4f8084c6e9afedea44b5/MLB_REALISM_PASS4_FINDINGS_2025-11-20.md#L128-L133). -
**BABIP (via fielder efficiency)** – not explicitly asked, but similarly
we can adjust fielder reaction/speed to tune BABIP without affecting the
above (just changes outs on balls in play). - **SLG vs AVG balance** –
by adjusting power parameter A, we change extra-base hit frequency
relative to singles.

All these can be done largely **independently**. Of course, some
interactions remain (e.g., if K% goes up, balls in play go down,
slightly affecting BABIP denominator). But those are second-order
effects that we can monitor.

We will also ensure our design supports **per-player variability** on
these new traits (Vision vs Power, Fly-ball tendency, etc.), so the
engine can produce diverse player types (the Adam Dunn high-K high-HR
type, the Ichiro low-K low-HR type, etc.). Those player traits will feed
into these subsystems in an additive way. For instance, Dunn has low
Vision (K a lot) but high Power and high loft tendency (so when he does
hit, more are HR). Ichiro opposite.

## Diagrams & Modules:

We can visualize the new flow with decoupling as:

**Pitch/At-Bat Flow v2:**

    Pitcher Control Module --(target & error)--> Pitch location --> Batter Swing Decision --> 
       [strike/ball outcome recorded] 
        if swing:
             Whiff Calculation (uses Vision attribute, count-based put-away mod) --> 
             if whiff, strike (or K if 3rd strike via put-away logic)
             if contact:
                  Contact Quality (uses Power attribute) --> EV
                  Launch Angle & Spin (uses Loft tendency + pitch physics) --> initial trajectory 
                  Ball Flight Module (uses adjustable drag/lift parameters) --> distance
                  Fielding Module (uses fielder ratings) --> catch or not
                  [Outcome recorded (hit type or out)]

The **bolded new parts** are: - Pitcher Control Module (separate from
AtBat logic, feeds into it). - Vision attribute affecting Whiff
independently of Power. - Put-Away logic when count = 2 strikes (forcing
resolution of K). - Loft attribute affecting Launch Angle separate from
EV. - Adjustable Ball Flight (drag/lift) that can be tuned globally.

We will implement new classes or methods for these, for example: -
`PitchIntentionDecider` (replacing hardcoded intentions): returns target
zone probability distribution. - `Umpire` class: method
`call_pitch(strike_prob, pitch_location)` that returns strike/ball with
some randomness on edges. -
`ContactResult = CollisionModel.full_collision(..., launch_angle_bias)`
where launch_angle_bias comes from batter’s Loft trait and situational
swing choice. - A configuration object or global singleton
`PhysicsTuning` with fields like `global_drag_coefficient`,
`hr_distance_boost` etc., to easily tweak aerodynamic factors.

We’ll also incorporate tests and calibration routines (discussed in Test
Plan) to ensure each of these modules can be tuned to hit isolated
targets (e.g., simulate 1000 PAs with only control module varying to
verify walk rate output).

# Prioritized Realism Roadmap

Finally, we outline a development roadmap with priority tiers to
implement the above changes and other improvements, focusing on
achieving MLB realism:

**Tier 1 – Critical Fixes (High Priority, directly addressing K%, BB%,
HR/FB):** 1. **Whiff & Strikeout Overhaul:** Implement the decoupled
strikeout model. Includes adding the Vision attribute, adjusting
`calculate_whiff_probability` to use it, and introducing the 2-strike
put-away logic. Target outcome: raise K% to ~22% (from
~8%)[\[108\]](https://github.com/jlundgrenedge/baseball/blob/2bf615c0de18cb7dbc2d4f8084c6e9afedea44b5/MLB_REALISM_PASS4_FINDINGS_2025-11-20.md#L24-L28)[\[175\]](https://github.com/jlundgrenedge/baseball/blob/2bf615c0de18cb7dbc2d4f8084c6e9afedea44b5/MLB_REALISM_FIXES_2025-11-20.md#L62-L67).
*Deliverable:* Verified K% in test series, and realistic strikeout
distribution (swinging vs looking Ks). 2. **Pitcher Control & Walk
Tuning:** Build the Pitcher Control module to replace fixed intention
rates. Integrate an Umpire call variability. Tune walk rate down to
~8-9% (from
15%+)[\[69\]](https://github.com/jlundgrenedge/baseball/blob/2bf615c0de18cb7dbc2d4f8084c6e9afedea44b5/MLB_REALISM_FIXES_2025-11-20.md#L19-L22)[\[183\]](https://github.com/jlundgrenedge/baseball/blob/2bf615c0de18cb7dbc2d4f8084c6e9afedea44b5/MLB_REALISM_FIXES_2025-11-20.md#L80-L88).
Ensure this doesn’t conflict with the new K system (they will be tuned
in concert). *Deliverable:* Walk rate in line, and no pathological
increase when whiffs are raised (the control on K should prevent that
feedback loop). 3. **Two-Param Collision Model & Carry:** Modify
collision/contact to separate EV and launch factors. Re-calibrate base
collision efficiency (Parameter A) to keep average EV ~88 mph, 40%
hard-hit[\[193\]](https://github.com/jlundgrenedge/baseball/blob/2bf615c0de18cb7dbc2d4f8084c6e9afedea44b5/MLB_REALISM_FIXES_2025-11-20.md#L126-L131).
Implement carry/loft adjustments (Parameter B) to push HR/FB toward
~12%[\[189\]](https://github.com/jlundgrenedge/baseball/blob/2bf615c0de18cb7dbc2d4f8084c6e9afedea44b5/MLB_REALISM_PASS4_FINDINGS_2025-11-20.md#L92-L100)
without altering other stats. *Deliverable:* Achieve target HR/FB and
ISO (~.150) simultaneously with correct EV. Hard-hit% should remain
~40%. This will involve iterating on the drag/lift constants and launch
angle distributions. 4. **Fielding Adjustments for Balance:** Although
not one of the “big 3” metrics, it’s in this tier because it affects
batting average and overall realism. Increase out conversion on balls in
play: e.g., improve outfielder catch success on fly balls (to get more
fly outs), and tune grounder fielding for more ground outs. This will
bring BABIP and overall batting average in line (target BABIP ~.300).
*Deliverable:* Roughly 3 outs per inning on balls in play – meaning
hitting isn’t overpowered. Specifically, ensure ~70–75% of balls in play
are converted to outs (MLB average), given the new K% will cover the
rest of outs.

Tier 1 fixes will be done first as they drastically change core stats.
After each fix, we’ll run multi-game simulations to verify improvements
(e.g., after K and BB fixes, ensure K%↑ without BB%↑ too much, etc.,
then after power fix ensure offense not too high or low).

**Tier 2 – Subsystem Tuning and Secondary Realism Improvements:** 1.
**Pitch Type Balance & Deception:** Revisit pitch effectiveness. Ensure
that breaking balls have appropriately higher whiff rates but also risk
(e.g., more likely to be balls). Tune the `pitch_effectiveness` usage:
e.g., sliders should generate more strikeouts but if overused lead to
more walks. This tuning will work now that K and BB are decoupled – we
can adjust individual pitch outcomes. *Deliverable:* Diversity of K%
contributions by pitch (fastballs vs offspeed whiffs roughly matching
real tendencies). 2. **Exit Velocity Variance & Barrels:** Fine-tune the
randomness in exit velo. We might increase the variability of EV on
contact so that even with the same average, there’s a realistic spread
(standard deviation ~9–10 mph). This ensures not every hit is
average-ish; we want a good mix of weak contact and barrels.
*Deliverable:* EV distribution matches Statcast (e.g., some 110+ mph
hits by big sluggers, some dribblers \<60 mph). 3. **Launch Angle &
Batted Ball Mix:** Double-check the distribution of ground/line/fly.
After Tier 1, we expect ~45% GB, 20% LD, 35%
FB[\[97\]](https://github.com/jlundgrenedge/baseball/blob/2bf615c0de18cb7dbc2d4f8084c6e9afedea44b5/MLB_REALISM_FIXES_2025-11-20.md#L42-L48).
We will do minor tweaks via the **Loft attribute** variance or swing
decision (e.g., maybe slightly reduce pop-ups by capping launch angle at
60° unless it’s an infield fly scenario). Also introduce **pop-up outs**
explicitly (virtually 100% catch for infield
flies)[\[122\]](https://github.com/jlundgrenedge/baseball/blob/2bf615c0de18cb7dbc2d4f8084c6e9afedea44b5/docs/GAME_SIMULATION_NOTES.md#L117-L124).
*Deliverable:* Batted ball type percentages within a few points of MLB,
and the engine can categorize infield fly outs separately. 4.
**Baserunning & Extra Bases:** Improve baserunning AI so that it
properly tags up on deep flies, goes first-to-third on singles, etc.
While not directly affecting the three key rates, this improves scoring
realism and how doubles/triples occur. Also incorporate chance of runner
thrown out on base (stretching a double, etc.) for added realism.
*Deliverable:* Extra-base advancement percentages (1st to 3rd on single
~28% etc.) align with MLB averages. 5. **Stamina and Reliever Usage:**
Introduce multi-pitcher logic (like pulling the starter when tired).
This can indirectly affect K/BB if not managed (since relievers often
have different rates). We’ll ensure the stamina model plus AI
replacement yields realistic complete games (virtually none), average
pitcher innings, and maybe a slight uptick in K% in late innings (since
fresh relievers). *Deliverable:* Realistic pitching changes and fatigue
effect on performance.

Tier 2 ensures that after addressing the big statistical discrepancies,
all other aspects of gameplay are tuned so the simulation “feels” right
and secondary stats (like distribution of doubles, triples, steals
maybe) are reasonable.

**Tier 3 – Gameplay Polishing and Additional Features:** 1. **Fielding
AI Polish:** Add more nuance – e.g., catcher fielding (passed balls,
wild pitches), smarter cutoff man logic, better error animations (who is
charged the error). Many of these don’t affect overall stats hugely
(errors are rare, maybe effect on unearned runs). But they add to
realism and completeness. 2. **Baserunning AI Polish:** Things like
pickoff attempts, rundowns, stealing logic (if we choose to include
steals), and base coach decisions. Again, mainly for completeness; could
be skipped if focusing purely on stat realism, but it makes the sim more
immersive. 3. **In-game Strategy/Management:** Incorporate substitutions
(pinch hitters, defensive replacements), mound visits or pitch-around
strategy dynamically. This doesn’t change season stats much but could
slightly alter single-game outcomes. For example, bringing in a lefty
reliever vs a lefty batter might reduce that PA’s offense (platoon
effect). If we implement that, we should verify it doesn’t skew overall
averages beyond acceptable. 4. **Season Mode & Persistence:** Not
directly realism of single game stats, but if we go there – ensure that
the distribution of player stats over a season looks realistic (which it
should if single games are, but things like injury frequency, fatigue
over season can be tuned). 5. **User Experience Enhancements:** Better
logging, visualization, perhaps a simple UI to watch the simulation,
etc. These don’t affect the engine’s stat output but improve usability.

The roadmap emphasizes Tier 1 as the must-have fixes to get the core
metrics in line, Tier 2 to refine and prevent any secondary issues from
Tier 1 changes, and Tier 3 to round out the simulation as a full
package.

# *(Optional)* Post-v2.0 Test Plan

After implementing the above, we’ll conduct extensive testing to
validate that the engine meets MLB realism benchmarks and that the
decoupling works as intended (i.e., adjusting one aspect doesn’t
inadvertently throw off others). The test plan includes:

- **Unit Tests for Subsystems:** Write specific tests for the new
  modules. For example:

- Feed the **Whiff/Strikeout module** a scenario with a given
  batter/pitcher and ensure that when we dial the “putAwayProbability”
  up or down, the observed strikeout rate in a large sample of identical
  matchups changes accordingly and only modestly affects pitch count
  distribution. Essentially, isolate a batter-pitcher duel and simulate
  10,000 PAs to see K%, BB% outcomes.

- Test the **Pitcher Control/Umpire module** by simulating a wild
  pitcher vs a control pitcher over many PAs and verifying the walk
  rates differ as expected, and that tweaking the global zone threshold
  moves both accordingly. Also verify edge-case: a pitch just at the
  corner gets called strike certain % consistent with our framing
  settings.

- Test the **Collision & Carry model** by generating a range of contact
  inputs (various bat speeds, angles) and ensure the outputs (distance,
  etc.) match expected physics. We can cross-verify with known
  trajectories (e.g., a 100 mph 30° should go out ~400ft at sea level
  with no wind – if not, adjust).

- Fielding: Simulate many balls in play at various locations and ensure
  the fielding module returns catches in realistic probability. E.g., a
  ball with 5s hang time 300ft away should be caught \>95% of time by an
  average MLB outfielder; if our simulation shows less, we adjust
  fielder speed/reaction.

- **Integration Tests (Full-game simulations):** Run long simulations
  (e.g., 100+ games, or a full season 2430 games) and aggregate stats.
  We will utilize the `series_metrics.py` or a new stats aggregator to
  compute: league-wide BA, OBP, SLG, K%, BB%, HR%, 2B%, 3B%, BABIP, etc.
  Compare these to target ranges. Every metric that’s off, see if it’s
  explainable or if something in code is still coupling them.

- We expect after tuning: K% ~22, BB% ~8-9, HR/FB ~12, AVG ~.250, OBP
  ~.320, SLG ~.420 (just example targets). We’ll allow small tolerances
  (since even MLB year-to-year varies). If any are out of line, we
  adjust the responsible module.

- Ensure no *new* emergent issue: e.g., maybe double plays are missing –
  check DP frequency vs MLB. If low, maybe base running is too
  conservative or ground ball outs distribution needs tweak.

- **Regression Tests:** We will freeze the tuned parameters and then
  stress-test edge conditions:

- Extreme pitchers (100 control vs 0 control, 100 velocity vs 60
  velocity, etc.) to see if engine still behaves reasonably (shouldn’t
  produce impossible stats like 0% walks or 50% walks except at the
  extremes).

- Extreme batters (max Vision vs min Vision, max Power vs min Power) to
  ensure our decoupling works per player: e.g., a max Vision, min Power
  guy strikes out very little but also hits almost no homers – does the
  sim reflect that? We can simulate that player’s season and confirm.

- We also simulate different team or league configurations: if one sets
  a league where everyone has 70k Vision (above avg), does K% drop
  correspondingly and everything else stay okay? If yes, our model is
  robust; if a change causes something weird (like if K% drop somehow
  increases HR% unphysically), that indicates hidden coupling that needs
  addressing.

- **Comparison with Real Game Situations:** We’ll test specific
  scenarios:

- High leverage ABs: e.g., 9th inning, do pitchers nibble more? If yes,
  does that match real (walk rate slightly higher in certain
  situations)? We might not have that logic yet, but it’s something to
  observe.

- Does the sim produce plausible stat lines for individual players? For
  instance, can we identify “strikeout pitchers” vs “control pitchers”
  in the output stats? If our decoupling works, pitchers with high stuff
  but poor control should indeed show high K and high BB (like Robbie
  Ray), whereas finesse guys show low K low BB (like prime
  Maddux)[\[60\]](https://github.com/jlundgrenedge/baseball/blob/2bf615c0de18cb7dbc2d4f8084c6e9afedea44b5/batted_ball/attributes.py#L144-L149).
  We can generate a set of prototype players and simulate a season to
  see if the correlation between K and BB is now more free (not all
  pitchers have identical K/BB traits).

- **Performance Testing:** Ensure the added complexity (e.g., Monte
  Carlo checks for umpire calls, more logic in at-bat) doesn’t slow sim
  beyond acceptable limits, or if it does, consider optimizing (this is
  more a coding concern, but as we add complexity, we watch runtime).

We will maintain a **realism checklist** (10/10 metrics passing as in
the docs) and not consider v2.0 done until all are green: - GB/LD/FB
distribution ✅, - K% ✅, - BB% ✅, - Hard-hit% ✅, - HR/FB ✅, - ISO
✅, - BABIP ✅, - Runs/game and ERA in plausible range, etc.

In conclusion, this deep overhaul and the testing regiment will yield a
simulation engine that **achieves MLB realism on all key metrics**, with
the flexibility to adjust each aspect independently – ensuring that
future tuning or rule changes (e.g., if we want to simulate 1968 or 2019
offense levels) can be done by turning the appropriate dial without
breaking the whole
system.[\[191\]](https://github.com/jlundgrenedge/baseball/blob/2bf615c0de18cb7dbc2d4f8084c6e9afedea44b5/MLB_REALISM_PASS4_FINDINGS_2025-11-20.md#L96-L101)[\[195\]](https://github.com/jlundgrenedge/baseball/blob/2bf615c0de18cb7dbc2d4f8084c6e9afedea44b5/MLB_REALISM_PASS4_FINDINGS_2025-11-20.md#L118-L126)

------------------------------------------------------------------------

[\[1\]](https://github.com/jlundgrenedge/baseball/blob/2bf615c0de18cb7dbc2d4f8084c6e9afedea44b5/docs/GAME_SIMULATION_NOTES.md#L36-L44)
[\[44\]](https://github.com/jlundgrenedge/baseball/blob/2bf615c0de18cb7dbc2d4f8084c6e9afedea44b5/docs/GAME_SIMULATION_NOTES.md#L99-L107)
[\[47\]](https://github.com/jlundgrenedge/baseball/blob/2bf615c0de18cb7dbc2d4f8084c6e9afedea44b5/docs/GAME_SIMULATION_NOTES.md#L109-L117)
[\[50\]](https://github.com/jlundgrenedge/baseball/blob/2bf615c0de18cb7dbc2d4f8084c6e9afedea44b5/docs/GAME_SIMULATION_NOTES.md#L86-L93)
[\[120\]](https://github.com/jlundgrenedge/baseball/blob/2bf615c0de18cb7dbc2d4f8084c6e9afedea44b5/docs/GAME_SIMULATION_NOTES.md#L76-L84)
[\[121\]](https://github.com/jlundgrenedge/baseball/blob/2bf615c0de18cb7dbc2d4f8084c6e9afedea44b5/docs/GAME_SIMULATION_NOTES.md#L75-L83)
[\[122\]](https://github.com/jlundgrenedge/baseball/blob/2bf615c0de18cb7dbc2d4f8084c6e9afedea44b5/docs/GAME_SIMULATION_NOTES.md#L117-L124)
[\[123\]](https://github.com/jlundgrenedge/baseball/blob/2bf615c0de18cb7dbc2d4f8084c6e9afedea44b5/docs/GAME_SIMULATION_NOTES.md#L100-L108)
[\[124\]](https://github.com/jlundgrenedge/baseball/blob/2bf615c0de18cb7dbc2d4f8084c6e9afedea44b5/docs/GAME_SIMULATION_NOTES.md#L109-L116)
[\[137\]](https://github.com/jlundgrenedge/baseball/blob/2bf615c0de18cb7dbc2d4f8084c6e9afedea44b5/docs/GAME_SIMULATION_NOTES.md#L95-L103)
GitHub

<https://github.com/jlundgrenedge/baseball/blob/2bf615c0de18cb7dbc2d4f8084c6e9afedea44b5/docs/GAME_SIMULATION_NOTES.md>

[\[2\]](https://github.com/jlundgrenedge/baseball/blob/2bf615c0de18cb7dbc2d4f8084c6e9afedea44b5/batted_ball/game_simulation.py#L486-L495)
[\[48\]](https://github.com/jlundgrenedge/baseball/blob/2bf615c0de18cb7dbc2d4f8084c6e9afedea44b5/batted_ball/game_simulation.py#L525-L534)
[\[49\]](https://github.com/jlundgrenedge/baseball/blob/2bf615c0de18cb7dbc2d4f8084c6e9afedea44b5/batted_ball/game_simulation.py#L548-L556)
[\[125\]](https://github.com/jlundgrenedge/baseball/blob/2bf615c0de18cb7dbc2d4f8084c6e9afedea44b5/batted_ball/game_simulation.py#L550-L559)
[\[142\]](https://github.com/jlundgrenedge/baseball/blob/2bf615c0de18cb7dbc2d4f8084c6e9afedea44b5/batted_ball/game_simulation.py#L564-L573)
[\[143\]](https://github.com/jlundgrenedge/baseball/blob/2bf615c0de18cb7dbc2d4f8084c6e9afedea44b5/batted_ball/game_simulation.py#L582-L590)
[\[144\]](https://github.com/jlundgrenedge/baseball/blob/2bf615c0de18cb7dbc2d4f8084c6e9afedea44b5/batted_ball/game_simulation.py#L524-L533)
[\[145\]](https://github.com/jlundgrenedge/baseball/blob/2bf615c0de18cb7dbc2d4f8084c6e9afedea44b5/batted_ball/game_simulation.py#L551-L559)
[\[146\]](https://github.com/jlundgrenedge/baseball/blob/2bf615c0de18cb7dbc2d4f8084c6e9afedea44b5/batted_ball/game_simulation.py#L568-L576)
[\[147\]](https://github.com/jlundgrenedge/baseball/blob/2bf615c0de18cb7dbc2d4f8084c6e9afedea44b5/batted_ball/game_simulation.py#L594-L603)
[\[148\]](https://github.com/jlundgrenedge/baseball/blob/2bf615c0de18cb7dbc2d4f8084c6e9afedea44b5/batted_ball/game_simulation.py#L526-L534)
[\[149\]](https://github.com/jlundgrenedge/baseball/blob/2bf615c0de18cb7dbc2d4f8084c6e9afedea44b5/batted_ball/game_simulation.py#L598-L601)
GitHub

<https://github.com/jlundgrenedge/baseball/blob/2bf615c0de18cb7dbc2d4f8084c6e9afedea44b5/batted_ball/game_simulation.py>

[\[3\]](https://github.com/jlundgrenedge/baseball/blob/2bf615c0de18cb7dbc2d4f8084c6e9afedea44b5/batted_ball/at_bat.py#L846-L855)
[\[4\]](https://github.com/jlundgrenedge/baseball/blob/2bf615c0de18cb7dbc2d4f8084c6e9afedea44b5/batted_ball/at_bat.py#L496-L505)
[\[5\]](https://github.com/jlundgrenedge/baseball/blob/2bf615c0de18cb7dbc2d4f8084c6e9afedea44b5/batted_ball/at_bat.py#L559-L568)
[\[6\]](https://github.com/jlundgrenedge/baseball/blob/2bf615c0de18cb7dbc2d4f8084c6e9afedea44b5/batted_ball/at_bat.py#L852-L861)
[\[7\]](https://github.com/jlundgrenedge/baseball/blob/2bf615c0de18cb7dbc2d4f8084c6e9afedea44b5/batted_ball/at_bat.py#L570-L578)
[\[13\]](https://github.com/jlundgrenedge/baseball/blob/2bf615c0de18cb7dbc2d4f8084c6e9afedea44b5/batted_ball/at_bat.py#L908-L917)
[\[14\]](https://github.com/jlundgrenedge/baseball/blob/2bf615c0de18cb7dbc2d4f8084c6e9afedea44b5/batted_ball/at_bat.py#L612-L620)
[\[15\]](https://github.com/jlundgrenedge/baseball/blob/2bf615c0de18cb7dbc2d4f8084c6e9afedea44b5/batted_ball/at_bat.py#L628-L636)
[\[21\]](https://github.com/jlundgrenedge/baseball/blob/2bf615c0de18cb7dbc2d4f8084c6e9afedea44b5/batted_ball/at_bat.py#L620-L626)
[\[23\]](https://github.com/jlundgrenedge/baseball/blob/2bf615c0de18cb7dbc2d4f8084c6e9afedea44b5/batted_ball/at_bat.py#L928-L936)
[\[25\]](https://github.com/jlundgrenedge/baseball/blob/2bf615c0de18cb7dbc2d4f8084c6e9afedea44b5/batted_ball/at_bat.py#L644-L652)
[\[26\]](https://github.com/jlundgrenedge/baseball/blob/2bf615c0de18cb7dbc2d4f8084c6e9afedea44b5/batted_ball/at_bat.py#L676-L684)
[\[35\]](https://github.com/jlundgrenedge/baseball/blob/2bf615c0de18cb7dbc2d4f8084c6e9afedea44b5/batted_ball/at_bat.py#L976-L985)
[\[36\]](https://github.com/jlundgrenedge/baseball/blob/2bf615c0de18cb7dbc2d4f8084c6e9afedea44b5/batted_ball/at_bat.py#L702-L710)
[\[39\]](https://github.com/jlundgrenedge/baseball/blob/2bf615c0de18cb7dbc2d4f8084c6e9afedea44b5/batted_ball/at_bat.py#L936-L945)
[\[40\]](https://github.com/jlundgrenedge/baseball/blob/2bf615c0de18cb7dbc2d4f8084c6e9afedea44b5/batted_ball/at_bat.py#L950-L958)
[\[51\]](https://github.com/jlundgrenedge/baseball/blob/2bf615c0de18cb7dbc2d4f8084c6e9afedea44b5/batted_ball/at_bat.py#L301-L310)
[\[54\]](https://github.com/jlundgrenedge/baseball/blob/2bf615c0de18cb7dbc2d4f8084c6e9afedea44b5/batted_ball/at_bat.py#L402-L411)
[\[55\]](https://github.com/jlundgrenedge/baseball/blob/2bf615c0de18cb7dbc2d4f8084c6e9afedea44b5/batted_ball/at_bat.py#L414-L422)
[\[56\]](https://github.com/jlundgrenedge/baseball/blob/2bf615c0de18cb7dbc2d4f8084c6e9afedea44b5/batted_ball/at_bat.py#L426-L434)
[\[58\]](https://github.com/jlundgrenedge/baseball/blob/2bf615c0de18cb7dbc2d4f8084c6e9afedea44b5/batted_ball/at_bat.py#L391-L398)
[\[59\]](https://github.com/jlundgrenedge/baseball/blob/2bf615c0de18cb7dbc2d4f8084c6e9afedea44b5/batted_ball/at_bat.py#L363-L371)
[\[68\]](https://github.com/jlundgrenedge/baseball/blob/2bf615c0de18cb7dbc2d4f8084c6e9afedea44b5/batted_ball/at_bat.py#L540-L548)
[\[71\]](https://github.com/jlundgrenedge/baseball/blob/2bf615c0de18cb7dbc2d4f8084c6e9afedea44b5/batted_ball/at_bat.py#L340-L348)
[\[99\]](https://github.com/jlundgrenedge/baseball/blob/2bf615c0de18cb7dbc2d4f8084c6e9afedea44b5/batted_ball/at_bat.py#L716-L725)
[\[100\]](https://github.com/jlundgrenedge/baseball/blob/2bf615c0de18cb7dbc2d4f8084c6e9afedea44b5/batted_ball/at_bat.py#L728-L732)
[\[101\]](https://github.com/jlundgrenedge/baseball/blob/2bf615c0de18cb7dbc2d4f8084c6e9afedea44b5/batted_ball/at_bat.py#L726-L734)
[\[117\]](https://github.com/jlundgrenedge/baseball/blob/2bf615c0de18cb7dbc2d4f8084c6e9afedea44b5/batted_ball/at_bat.py#L76-L84)
[\[138\]](https://github.com/jlundgrenedge/baseball/blob/2bf615c0de18cb7dbc2d4f8084c6e9afedea44b5/batted_ball/at_bat.py#L1007-L1015)
[\[139\]](https://github.com/jlundgrenedge/baseball/blob/2bf615c0de18cb7dbc2d4f8084c6e9afedea44b5/batted_ball/at_bat.py#L961-L970)
[\[140\]](https://github.com/jlundgrenedge/baseball/blob/2bf615c0de18cb7dbc2d4f8084c6e9afedea44b5/batted_ball/at_bat.py#L977-L985)
[\[141\]](https://github.com/jlundgrenedge/baseball/blob/2bf615c0de18cb7dbc2d4f8084c6e9afedea44b5/batted_ball/at_bat.py#L972-L980)
[\[151\]](https://github.com/jlundgrenedge/baseball/blob/2bf615c0de18cb7dbc2d4f8084c6e9afedea44b5/batted_ball/at_bat.py#L843-L851)
[\[152\]](https://github.com/jlundgrenedge/baseball/blob/2bf615c0de18cb7dbc2d4f8084c6e9afedea44b5/batted_ball/at_bat.py#L884-L888)
[\[154\]](https://github.com/jlundgrenedge/baseball/blob/2bf615c0de18cb7dbc2d4f8084c6e9afedea44b5/batted_ball/at_bat.py#L556-L564)
[\[155\]](https://github.com/jlundgrenedge/baseball/blob/2bf615c0de18cb7dbc2d4f8084c6e9afedea44b5/batted_ball/at_bat.py#L559-L567)
[\[161\]](https://github.com/jlundgrenedge/baseball/blob/2bf615c0de18cb7dbc2d4f8084c6e9afedea44b5/batted_ball/at_bat.py#L646-L654)
[\[176\]](https://github.com/jlundgrenedge/baseball/blob/2bf615c0de18cb7dbc2d4f8084c6e9afedea44b5/batted_ball/at_bat.py#L970-L978)
[\[180\]](https://github.com/jlundgrenedge/baseball/blob/2bf615c0de18cb7dbc2d4f8084c6e9afedea44b5/batted_ball/at_bat.py#L412-L420)
[\[181\]](https://github.com/jlundgrenedge/baseball/blob/2bf615c0de18cb7dbc2d4f8084c6e9afedea44b5/batted_ball/at_bat.py#L430-L438)
GitHub

<https://github.com/jlundgrenedge/baseball/blob/2bf615c0de18cb7dbc2d4f8084c6e9afedea44b5/batted_ball/at_bat.py>

[\[8\]](https://github.com/jlundgrenedge/baseball/blob/2bf615c0de18cb7dbc2d4f8084c6e9afedea44b5/batted_ball/player.py#L630-L639)
[\[9\]](https://github.com/jlundgrenedge/baseball/blob/2bf615c0de18cb7dbc2d4f8084c6e9afedea44b5/batted_ball/player.py#L656-L665)
[\[10\]](https://github.com/jlundgrenedge/baseball/blob/2bf615c0de18cb7dbc2d4f8084c6e9afedea44b5/batted_ball/player.py#L648-L657)
[\[11\]](https://github.com/jlundgrenedge/baseball/blob/2bf615c0de18cb7dbc2d4f8084c6e9afedea44b5/batted_ball/player.py#L670-L679)
[\[12\]](https://github.com/jlundgrenedge/baseball/blob/2bf615c0de18cb7dbc2d4f8084c6e9afedea44b5/batted_ball/player.py#L696-L704)
[\[16\]](https://github.com/jlundgrenedge/baseball/blob/2bf615c0de18cb7dbc2d4f8084c6e9afedea44b5/batted_ball/player.py#L862-L871)
[\[17\]](https://github.com/jlundgrenedge/baseball/blob/2bf615c0de18cb7dbc2d4f8084c6e9afedea44b5/batted_ball/player.py#L883-L891)
[\[18\]](https://github.com/jlundgrenedge/baseball/blob/2bf615c0de18cb7dbc2d4f8084c6e9afedea44b5/batted_ball/player.py#L892-L901)
[\[20\]](https://github.com/jlundgrenedge/baseball/blob/2bf615c0de18cb7dbc2d4f8084c6e9afedea44b5/batted_ball/player.py#L893-L901)
[\[22\]](https://github.com/jlundgrenedge/baseball/blob/2bf615c0de18cb7dbc2d4f8084c6e9afedea44b5/batted_ball/player.py#L259-L268)
[\[52\]](https://github.com/jlundgrenedge/baseball/blob/2bf615c0de18cb7dbc2d4f8084c6e9afedea44b5/batted_ball/player.py#L258-L267)
[\[53\]](https://github.com/jlundgrenedge/baseball/blob/2bf615c0de18cb7dbc2d4f8084c6e9afedea44b5/batted_ball/player.py#L274-L283)
[\[61\]](https://github.com/jlundgrenedge/baseball/blob/2bf615c0de18cb7dbc2d4f8084c6e9afedea44b5/batted_ball/player.py#L180-L186)
[\[62\]](https://github.com/jlundgrenedge/baseball/blob/2bf615c0de18cb7dbc2d4f8084c6e9afedea44b5/batted_ball/player.py#L231-L240)
[\[63\]](https://github.com/jlundgrenedge/baseball/blob/2bf615c0de18cb7dbc2d4f8084c6e9afedea44b5/batted_ball/player.py#L235-L243)
[\[66\]](https://github.com/jlundgrenedge/baseball/blob/2bf615c0de18cb7dbc2d4f8084c6e9afedea44b5/batted_ball/player.py#L116-L124)
[\[67\]](https://github.com/jlundgrenedge/baseball/blob/2bf615c0de18cb7dbc2d4f8084c6e9afedea44b5/batted_ball/player.py#L150-L158)
[\[72\]](https://github.com/jlundgrenedge/baseball/blob/2bf615c0de18cb7dbc2d4f8084c6e9afedea44b5/batted_ball/player.py#L632-L640)
[\[73\]](https://github.com/jlundgrenedge/baseball/blob/2bf615c0de18cb7dbc2d4f8084c6e9afedea44b5/batted_ball/player.py#L660-L668)
[\[74\]](https://github.com/jlundgrenedge/baseball/blob/2bf615c0de18cb7dbc2d4f8084c6e9afedea44b5/batted_ball/player.py#L662-L670)
[\[75\]](https://github.com/jlundgrenedge/baseball/blob/2bf615c0de18cb7dbc2d4f8084c6e9afedea44b5/batted_ball/player.py#L656-L664)
[\[76\]](https://github.com/jlundgrenedge/baseball/blob/2bf615c0de18cb7dbc2d4f8084c6e9afedea44b5/batted_ball/player.py#L674-L682)
[\[77\]](https://github.com/jlundgrenedge/baseball/blob/2bf615c0de18cb7dbc2d4f8084c6e9afedea44b5/batted_ball/player.py#L683-L690)
[\[78\]](https://github.com/jlundgrenedge/baseball/blob/2bf615c0de18cb7dbc2d4f8084c6e9afedea44b5/batted_ball/player.py#L688-L695)
[\[79\]](https://github.com/jlundgrenedge/baseball/blob/2bf615c0de18cb7dbc2d4f8084c6e9afedea44b5/batted_ball/player.py#L702-L710)
[\[153\]](https://github.com/jlundgrenedge/baseball/blob/2bf615c0de18cb7dbc2d4f8084c6e9afedea44b5/batted_ball/player.py#L122-L129)
[\[164\]](https://github.com/jlundgrenedge/baseball/blob/2bf615c0de18cb7dbc2d4f8084c6e9afedea44b5/batted_ball/player.py#L672-L680)
[\[167\]](https://github.com/jlundgrenedge/baseball/blob/2bf615c0de18cb7dbc2d4f8084c6e9afedea44b5/batted_ball/player.py#L98-L106)
[\[168\]](https://github.com/jlundgrenedge/baseball/blob/2bf615c0de18cb7dbc2d4f8084c6e9afedea44b5/batted_ball/player.py#L112-L120)
GitHub

<https://github.com/jlundgrenedge/baseball/blob/2bf615c0de18cb7dbc2d4f8084c6e9afedea44b5/batted_ball/player.py>

[\[19\]](https://github.com/jlundgrenedge/baseball/blob/2bf615c0de18cb7dbc2d4f8084c6e9afedea44b5/MLB_REALISM_FIXES_2025-11-20.md#L55-L63)
[\[27\]](https://github.com/jlundgrenedge/baseball/blob/2bf615c0de18cb7dbc2d4f8084c6e9afedea44b5/MLB_REALISM_FIXES_2025-11-20.md#L94-L102)
[\[28\]](https://github.com/jlundgrenedge/baseball/blob/2bf615c0de18cb7dbc2d4f8084c6e9afedea44b5/MLB_REALISM_FIXES_2025-11-20.md#L96-L104)
[\[30\]](https://github.com/jlundgrenedge/baseball/blob/2bf615c0de18cb7dbc2d4f8084c6e9afedea44b5/MLB_REALISM_FIXES_2025-11-20.md#L116-L124)
[\[57\]](https://github.com/jlundgrenedge/baseball/blob/2bf615c0de18cb7dbc2d4f8084c6e9afedea44b5/MLB_REALISM_FIXES_2025-11-20.md#L73-L81)
[\[69\]](https://github.com/jlundgrenedge/baseball/blob/2bf615c0de18cb7dbc2d4f8084c6e9afedea44b5/MLB_REALISM_FIXES_2025-11-20.md#L19-L22)
[\[70\]](https://github.com/jlundgrenedge/baseball/blob/2bf615c0de18cb7dbc2d4f8084c6e9afedea44b5/MLB_REALISM_FIXES_2025-11-20.md#L75-L83)
[\[84\]](https://github.com/jlundgrenedge/baseball/blob/2bf615c0de18cb7dbc2d4f8084c6e9afedea44b5/MLB_REALISM_FIXES_2025-11-20.md#L110-L118)
[\[96\]](https://github.com/jlundgrenedge/baseball/blob/2bf615c0de18cb7dbc2d4f8084c6e9afedea44b5/MLB_REALISM_FIXES_2025-11-20.md#L35-L44)
[\[97\]](https://github.com/jlundgrenedge/baseball/blob/2bf615c0de18cb7dbc2d4f8084c6e9afedea44b5/MLB_REALISM_FIXES_2025-11-20.md#L42-L48)
[\[102\]](https://github.com/jlundgrenedge/baseball/blob/2bf615c0de18cb7dbc2d4f8084c6e9afedea44b5/MLB_REALISM_FIXES_2025-11-20.md#L20-L28)
[\[103\]](https://github.com/jlundgrenedge/baseball/blob/2bf615c0de18cb7dbc2d4f8084c6e9afedea44b5/MLB_REALISM_FIXES_2025-11-20.md#L91-L100)
[\[126\]](https://github.com/jlundgrenedge/baseball/blob/2bf615c0de18cb7dbc2d4f8084c6e9afedea44b5/MLB_REALISM_FIXES_2025-11-20.md#L22-L28)
[\[150\]](https://github.com/jlundgrenedge/baseball/blob/2bf615c0de18cb7dbc2d4f8084c6e9afedea44b5/MLB_REALISM_FIXES_2025-11-20.md#L11-L19)
[\[171\]](https://github.com/jlundgrenedge/baseball/blob/2bf615c0de18cb7dbc2d4f8084c6e9afedea44b5/MLB_REALISM_FIXES_2025-11-20.md#L18-L22)
[\[172\]](https://github.com/jlundgrenedge/baseball/blob/2bf615c0de18cb7dbc2d4f8084c6e9afedea44b5/MLB_REALISM_FIXES_2025-11-20.md#L64-L68)
[\[173\]](https://github.com/jlundgrenedge/baseball/blob/2bf615c0de18cb7dbc2d4f8084c6e9afedea44b5/MLB_REALISM_FIXES_2025-11-20.md#L56-L64)
[\[174\]](https://github.com/jlundgrenedge/baseball/blob/2bf615c0de18cb7dbc2d4f8084c6e9afedea44b5/MLB_REALISM_FIXES_2025-11-20.md#L58-L61)
[\[175\]](https://github.com/jlundgrenedge/baseball/blob/2bf615c0de18cb7dbc2d4f8084c6e9afedea44b5/MLB_REALISM_FIXES_2025-11-20.md#L62-L67)
[\[182\]](https://github.com/jlundgrenedge/baseball/blob/2bf615c0de18cb7dbc2d4f8084c6e9afedea44b5/MLB_REALISM_FIXES_2025-11-20.md#L76-L84)
[\[183\]](https://github.com/jlundgrenedge/baseball/blob/2bf615c0de18cb7dbc2d4f8084c6e9afedea44b5/MLB_REALISM_FIXES_2025-11-20.md#L80-L88)
[\[185\]](https://github.com/jlundgrenedge/baseball/blob/2bf615c0de18cb7dbc2d4f8084c6e9afedea44b5/MLB_REALISM_FIXES_2025-11-20.md#L82-L86)
[\[187\]](https://github.com/jlundgrenedge/baseball/blob/2bf615c0de18cb7dbc2d4f8084c6e9afedea44b5/MLB_REALISM_FIXES_2025-11-20.md#L22-L25)
[\[188\]](https://github.com/jlundgrenedge/baseball/blob/2bf615c0de18cb7dbc2d4f8084c6e9afedea44b5/MLB_REALISM_FIXES_2025-11-20.md#L16-L24)
[\[192\]](https://github.com/jlundgrenedge/baseball/blob/2bf615c0de18cb7dbc2d4f8084c6e9afedea44b5/MLB_REALISM_FIXES_2025-11-20.md#L22-L26)
[\[193\]](https://github.com/jlundgrenedge/baseball/blob/2bf615c0de18cb7dbc2d4f8084c6e9afedea44b5/MLB_REALISM_FIXES_2025-11-20.md#L126-L131)
[\[194\]](https://github.com/jlundgrenedge/baseball/blob/2bf615c0de18cb7dbc2d4f8084c6e9afedea44b5/MLB_REALISM_FIXES_2025-11-20.md#L126-L129)
GitHub

<https://github.com/jlundgrenedge/baseball/blob/2bf615c0de18cb7dbc2d4f8084c6e9afedea44b5/MLB_REALISM_FIXES_2025-11-20.md>

[\[24\]](https://github.com/jlundgrenedge/baseball/blob/2bf615c0de18cb7dbc2d4f8084c6e9afedea44b5/batted_ball/attributes.py#L140-L149)
[\[41\]](https://github.com/jlundgrenedge/baseball/blob/2bf615c0de18cb7dbc2d4f8084c6e9afedea44b5/batted_ball/attributes.py#L80-L88)
[\[46\]](https://github.com/jlundgrenedge/baseball/blob/2bf615c0de18cb7dbc2d4f8084c6e9afedea44b5/batted_ball/attributes.py#L74-L82)
[\[60\]](https://github.com/jlundgrenedge/baseball/blob/2bf615c0de18cb7dbc2d4f8084c6e9afedea44b5/batted_ball/attributes.py#L144-L149)
[\[64\]](https://github.com/jlundgrenedge/baseball/blob/2bf615c0de18cb7dbc2d4f8084c6e9afedea44b5/batted_ball/attributes.py#L146-L149)
[\[65\]](https://github.com/jlundgrenedge/baseball/blob/2bf615c0de18cb7dbc2d4f8084c6e9afedea44b5/batted_ball/attributes.py#L128-L136)
[\[91\]](https://github.com/jlundgrenedge/baseball/blob/2bf615c0de18cb7dbc2d4f8084c6e9afedea44b5/batted_ball/attributes.py#L8-L16)
[\[128\]](https://github.com/jlundgrenedge/baseball/blob/2bf615c0de18cb7dbc2d4f8084c6e9afedea44b5/batted_ball/attributes.py#L78-L86)
[\[129\]](https://github.com/jlundgrenedge/baseball/blob/2bf615c0de18cb7dbc2d4f8084c6e9afedea44b5/batted_ball/attributes.py#L68-L76)
[\[130\]](https://github.com/jlundgrenedge/baseball/blob/2bf615c0de18cb7dbc2d4f8084c6e9afedea44b5/batted_ball/attributes.py#L86-L94)
[\[131\]](https://github.com/jlundgrenedge/baseball/blob/2bf615c0de18cb7dbc2d4f8084c6e9afedea44b5/batted_ball/attributes.py#L84-L91)
[\[132\]](https://github.com/jlundgrenedge/baseball/blob/2bf615c0de18cb7dbc2d4f8084c6e9afedea44b5/batted_ball/attributes.py#L98-L101)
[\[133\]](https://github.com/jlundgrenedge/baseball/blob/2bf615c0de18cb7dbc2d4f8084c6e9afedea44b5/batted_ball/attributes.py#L116-L120)
[\[134\]](https://github.com/jlundgrenedge/baseball/blob/2bf615c0de18cb7dbc2d4f8084c6e9afedea44b5/batted_ball/attributes.py#L92-L100)
[\[156\]](https://github.com/jlundgrenedge/baseball/blob/2bf615c0de18cb7dbc2d4f8084c6e9afedea44b5/batted_ball/attributes.py#L126-L134)
[\[157\]](https://github.com/jlundgrenedge/baseball/blob/2bf615c0de18cb7dbc2d4f8084c6e9afedea44b5/batted_ball/attributes.py#L132-L140)
[\[158\]](https://github.com/jlundgrenedge/baseball/blob/2bf615c0de18cb7dbc2d4f8084c6e9afedea44b5/batted_ball/attributes.py#L13-L19)
[\[159\]](https://github.com/jlundgrenedge/baseball/blob/2bf615c0de18cb7dbc2d4f8084c6e9afedea44b5/batted_ball/attributes.py#L20-L28)
[\[160\]](https://github.com/jlundgrenedge/baseball/blob/2bf615c0de18cb7dbc2d4f8084c6e9afedea44b5/batted_ball/attributes.py#L24-L31)
[\[162\]](https://github.com/jlundgrenedge/baseball/blob/2bf615c0de18cb7dbc2d4f8084c6e9afedea44b5/batted_ball/attributes.py#L44-L48)
[\[163\]](https://github.com/jlundgrenedge/baseball/blob/2bf615c0de18cb7dbc2d4f8084c6e9afedea44b5/batted_ball/attributes.py#L38-L46)
[\[165\]](https://github.com/jlundgrenedge/baseball/blob/2bf615c0de18cb7dbc2d4f8084c6e9afedea44b5/batted_ball/attributes.py#L24-L33)
[\[166\]](https://github.com/jlundgrenedge/baseball/blob/2bf615c0de18cb7dbc2d4f8084c6e9afedea44b5/batted_ball/attributes.py#L64-L72)
[\[169\]](https://github.com/jlundgrenedge/baseball/blob/2bf615c0de18cb7dbc2d4f8084c6e9afedea44b5/batted_ball/attributes.py#L137-L145)
[\[170\]](https://github.com/jlundgrenedge/baseball/blob/2bf615c0de18cb7dbc2d4f8084c6e9afedea44b5/batted_ball/attributes.py#L151-L159)
GitHub

<https://github.com/jlundgrenedge/baseball/blob/2bf615c0de18cb7dbc2d4f8084c6e9afedea44b5/batted_ball/attributes.py>

[\[29\]](https://github.com/jlundgrenedge/baseball/blob/2bf615c0de18cb7dbc2d4f8084c6e9afedea44b5/batted_ball/contact.py#L546-L555)
[\[31\]](https://github.com/jlundgrenedge/baseball/blob/2bf615c0de18cb7dbc2d4f8084c6e9afedea44b5/batted_ball/contact.py#L126-L135)
[\[32\]](https://github.com/jlundgrenedge/baseball/blob/2bf615c0de18cb7dbc2d4f8084c6e9afedea44b5/batted_ball/contact.py#L139-L148)
[\[33\]](https://github.com/jlundgrenedge/baseball/blob/2bf615c0de18cb7dbc2d4f8084c6e9afedea44b5/batted_ball/contact.py#L582-L590)
[\[34\]](https://github.com/jlundgrenedge/baseball/blob/2bf615c0de18cb7dbc2d4f8084c6e9afedea44b5/batted_ball/contact.py#L594-L602)
[\[85\]](https://github.com/jlundgrenedge/baseball/blob/2bf615c0de18cb7dbc2d4f8084c6e9afedea44b5/batted_ball/contact.py#L546-L554)
[\[86\]](https://github.com/jlundgrenedge/baseball/blob/2bf615c0de18cb7dbc2d4f8084c6e9afedea44b5/batted_ball/contact.py#L562-L570)
[\[87\]](https://github.com/jlundgrenedge/baseball/blob/2bf615c0de18cb7dbc2d4f8084c6e9afedea44b5/batted_ball/contact.py#L130-L139)
[\[89\]](https://github.com/jlundgrenedge/baseball/blob/2bf615c0de18cb7dbc2d4f8084c6e9afedea44b5/batted_ball/contact.py#L549-L558)
[\[90\]](https://github.com/jlundgrenedge/baseball/blob/2bf615c0de18cb7dbc2d4f8084c6e9afedea44b5/batted_ball/contact.py#L570-L578)
[\[92\]](https://github.com/jlundgrenedge/baseball/blob/2bf615c0de18cb7dbc2d4f8084c6e9afedea44b5/batted_ball/contact.py#L575-L583)
[\[93\]](https://github.com/jlundgrenedge/baseball/blob/2bf615c0de18cb7dbc2d4f8084c6e9afedea44b5/batted_ball/contact.py#L113-L121)
[\[94\]](https://github.com/jlundgrenedge/baseball/blob/2bf615c0de18cb7dbc2d4f8084c6e9afedea44b5/batted_ball/contact.py#L126-L134)
[\[95\]](https://github.com/jlundgrenedge/baseball/blob/2bf615c0de18cb7dbc2d4f8084c6e9afedea44b5/batted_ball/contact.py#L117-L125)
[\[98\]](https://github.com/jlundgrenedge/baseball/blob/2bf615c0de18cb7dbc2d4f8084c6e9afedea44b5/batted_ball/contact.py#L152-L160)
GitHub

<https://github.com/jlundgrenedge/baseball/blob/2bf615c0de18cb7dbc2d4f8084c6e9afedea44b5/batted_ball/contact.py>

[\[37\]](https://github.com/jlundgrenedge/baseball/blob/2bf615c0de18cb7dbc2d4f8084c6e9afedea44b5/batted_ball/constants.py#L243-L252)
[\[38\]](https://github.com/jlundgrenedge/baseball/blob/2bf615c0de18cb7dbc2d4f8084c6e9afedea44b5/batted_ball/constants.py#L254-L263)
[\[88\]](https://github.com/jlundgrenedge/baseball/blob/2bf615c0de18cb7dbc2d4f8084c6e9afedea44b5/batted_ball/constants.py#L274-L282)
[\[104\]](https://github.com/jlundgrenedge/baseball/blob/2bf615c0de18cb7dbc2d4f8084c6e9afedea44b5/batted_ball/constants.py#L244-L252)
[\[105\]](https://github.com/jlundgrenedge/baseball/blob/2bf615c0de18cb7dbc2d4f8084c6e9afedea44b5/batted_ball/constants.py#L246-L255)
[\[106\]](https://github.com/jlundgrenedge/baseball/blob/2bf615c0de18cb7dbc2d4f8084c6e9afedea44b5/batted_ball/constants.py#L250-L259)
[\[107\]](https://github.com/jlundgrenedge/baseball/blob/2bf615c0de18cb7dbc2d4f8084c6e9afedea44b5/batted_ball/constants.py#L261-L265)
[\[110\]](https://github.com/jlundgrenedge/baseball/blob/2bf615c0de18cb7dbc2d4f8084c6e9afedea44b5/batted_ball/constants.py#L234-L243)
[\[111\]](https://github.com/jlundgrenedge/baseball/blob/2bf615c0de18cb7dbc2d4f8084c6e9afedea44b5/batted_ball/constants.py#L296-L301)
[\[112\]](https://github.com/jlundgrenedge/baseball/blob/2bf615c0de18cb7dbc2d4f8084c6e9afedea44b5/batted_ball/constants.py#L37-L45)
[\[113\]](https://github.com/jlundgrenedge/baseball/blob/2bf615c0de18cb7dbc2d4f8084c6e9afedea44b5/batted_ball/constants.py#L30-L38)
[\[114\]](https://github.com/jlundgrenedge/baseball/blob/2bf615c0de18cb7dbc2d4f8084c6e9afedea44b5/batted_ball/constants.py#L38-L46)
[\[115\]](https://github.com/jlundgrenedge/baseball/blob/2bf615c0de18cb7dbc2d4f8084c6e9afedea44b5/batted_ball/constants.py#L50-L58)
[\[116\]](https://github.com/jlundgrenedge/baseball/blob/2bf615c0de18cb7dbc2d4f8084c6e9afedea44b5/batted_ball/constants.py#L52-L60)
[\[118\]](https://github.com/jlundgrenedge/baseball/blob/2bf615c0de18cb7dbc2d4f8084c6e9afedea44b5/batted_ball/constants.py#L298-L306)
[\[119\]](https://github.com/jlundgrenedge/baseball/blob/2bf615c0de18cb7dbc2d4f8084c6e9afedea44b5/batted_ball/constants.py#L102-L105)
[\[190\]](https://github.com/jlundgrenedge/baseball/blob/2bf615c0de18cb7dbc2d4f8084c6e9afedea44b5/batted_ball/constants.py#L251-L260)
GitHub

<https://github.com/jlundgrenedge/baseball/blob/2bf615c0de18cb7dbc2d4f8084c6e9afedea44b5/batted_ball/constants.py>

[\[42\]](https://github.com/jlundgrenedge/baseball/blob/2bf615c0de18cb7dbc2d4f8084c6e9afedea44b5/batted_ball/fielding.py#L84-L93)
[\[43\]](https://github.com/jlundgrenedge/baseball/blob/2bf615c0de18cb7dbc2d4f8084c6e9afedea44b5/batted_ball/fielding.py#L94-L101)
[\[45\]](https://github.com/jlundgrenedge/baseball/blob/2bf615c0de18cb7dbc2d4f8084c6e9afedea44b5/batted_ball/fielding.py#L130-L139)
[\[135\]](https://github.com/jlundgrenedge/baseball/blob/2bf615c0de18cb7dbc2d4f8084c6e9afedea44b5/batted_ball/fielding.py#L54-L62)
[\[136\]](https://github.com/jlundgrenedge/baseball/blob/2bf615c0de18cb7dbc2d4f8084c6e9afedea44b5/batted_ball/fielding.py#L80-L88)
GitHub

<https://github.com/jlundgrenedge/baseball/blob/2bf615c0de18cb7dbc2d4f8084c6e9afedea44b5/batted_ball/fielding.py>

[\[80\]](https://github.com/jlundgrenedge/baseball/blob/2bf615c0de18cb7dbc2d4f8084c6e9afedea44b5/MLB_REALISM_PASS4_FINDINGS_2025-11-20.md#L64-L73)
[\[81\]](https://github.com/jlundgrenedge/baseball/blob/2bf615c0de18cb7dbc2d4f8084c6e9afedea44b5/MLB_REALISM_PASS4_FINDINGS_2025-11-20.md#L74-L82)
[\[82\]](https://github.com/jlundgrenedge/baseball/blob/2bf615c0de18cb7dbc2d4f8084c6e9afedea44b5/MLB_REALISM_PASS4_FINDINGS_2025-11-20.md#L48-L56)
[\[83\]](https://github.com/jlundgrenedge/baseball/blob/2bf615c0de18cb7dbc2d4f8084c6e9afedea44b5/MLB_REALISM_PASS4_FINDINGS_2025-11-20.md#L80-L88)
[\[108\]](https://github.com/jlundgrenedge/baseball/blob/2bf615c0de18cb7dbc2d4f8084c6e9afedea44b5/MLB_REALISM_PASS4_FINDINGS_2025-11-20.md#L24-L28)
[\[109\]](https://github.com/jlundgrenedge/baseball/blob/2bf615c0de18cb7dbc2d4f8084c6e9afedea44b5/MLB_REALISM_PASS4_FINDINGS_2025-11-20.md#L90-L99)
[\[127\]](https://github.com/jlundgrenedge/baseball/blob/2bf615c0de18cb7dbc2d4f8084c6e9afedea44b5/MLB_REALISM_PASS4_FINDINGS_2025-11-20.md#L20-L28)
[\[177\]](https://github.com/jlundgrenedge/baseball/blob/2bf615c0de18cb7dbc2d4f8084c6e9afedea44b5/MLB_REALISM_PASS4_FINDINGS_2025-11-20.md#L50-L58)
[\[178\]](https://github.com/jlundgrenedge/baseball/blob/2bf615c0de18cb7dbc2d4f8084c6e9afedea44b5/MLB_REALISM_PASS4_FINDINGS_2025-11-20.md#L63-L71)
[\[179\]](https://github.com/jlundgrenedge/baseball/blob/2bf615c0de18cb7dbc2d4f8084c6e9afedea44b5/MLB_REALISM_PASS4_FINDINGS_2025-11-20.md#L38-L46)
[\[184\]](https://github.com/jlundgrenedge/baseball/blob/2bf615c0de18cb7dbc2d4f8084c6e9afedea44b5/MLB_REALISM_PASS4_FINDINGS_2025-11-20.md#L66-L73)
[\[186\]](https://github.com/jlundgrenedge/baseball/blob/2bf615c0de18cb7dbc2d4f8084c6e9afedea44b5/MLB_REALISM_PASS4_FINDINGS_2025-11-20.md#L66-L74)
[\[189\]](https://github.com/jlundgrenedge/baseball/blob/2bf615c0de18cb7dbc2d4f8084c6e9afedea44b5/MLB_REALISM_PASS4_FINDINGS_2025-11-20.md#L92-L100)
[\[191\]](https://github.com/jlundgrenedge/baseball/blob/2bf615c0de18cb7dbc2d4f8084c6e9afedea44b5/MLB_REALISM_PASS4_FINDINGS_2025-11-20.md#L96-L101)
[\[195\]](https://github.com/jlundgrenedge/baseball/blob/2bf615c0de18cb7dbc2d4f8084c6e9afedea44b5/MLB_REALISM_PASS4_FINDINGS_2025-11-20.md#L118-L126)
[\[196\]](https://github.com/jlundgrenedge/baseball/blob/2bf615c0de18cb7dbc2d4f8084c6e9afedea44b5/MLB_REALISM_PASS4_FINDINGS_2025-11-20.md#L122-L128)
[\[197\]](https://github.com/jlundgrenedge/baseball/blob/2bf615c0de18cb7dbc2d4f8084c6e9afedea44b5/MLB_REALISM_PASS4_FINDINGS_2025-11-20.md#L128-L133)
GitHub

<https://github.com/jlundgrenedge/baseball/blob/2bf615c0de18cb7dbc2d4f8084c6e9afedea44b5/MLB_REALISM_PASS4_FINDINGS_2025-11-20.md>
