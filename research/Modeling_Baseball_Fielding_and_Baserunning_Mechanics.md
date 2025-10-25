# Modeling Baseball Fielding and Baserunning Mechanics for High‑Realism Simulation

## Introduction

To complete our physics-based baseball simulation, we need robust
**fielding** and **baserunning** models that operate in tandem with the
existing pitching and batted-ball physics. In live play, once a ball is
put in play, nine defensive players react and attempt to field it while
runners accelerate around the bases. A high-realism simulation must
capture the **individual mechanics** of these fielders and runners –
from how fast players sprint and react, to how accurately they throw and
how efficiently they round bases. We draw on real-world metrics (e.g.
Statcast sprint speeds and fielding stats) and physics principles to
parameterize these behaviors. By integrating fielding and running with
the ball’s trajectory, the engine can determine outcomes (outs, hits,
extra bases) in a physically authentic way, rather than relying on
canned probabilities. The following report details the key attributes
and modeling approaches for fielders and baserunners, and how these
modules integrate with the existing pitch and batted-ball models to
simulate complete plays.

## Fielding Mechanics Module

**Defensive attributes to model include:**

- **Sprint Speed:** A fielder’s top running speed (typically measured in
  feet per second). This determines how fast they can cover ground;
  Statcast data shows MLB players average around 27 ft/s, with elite
  sprinters reaching ~30 ft/s (about 20 mph).
- **Acceleration:** How quickly the player reaches top speed from a
  standstill. A higher acceleration means the fielder can attain useful
  speed in just a few steps – crucial for short bursts to the ball.
- **Reaction Time:** The delay between contact and the fielder’s first
  movement. An elite defender might react almost instantly, whereas a
  slower reactor loses a few tenths of a second before
  moving[\[1\]](file://file_00000000a01c61f6b3bd07450fa35df9#:~:text=running%20speed%20,Then%20you%20decide%20the).
  This initial delay greatly affects whether they can reach hard-hit
  balls in time.
- **Fielding Range:** The effective area a player can cover, given their
  speed, acceleration, and reaction. This isn’t a fixed value but
  emerges from those factors – faster players with quick reactions have
  a larger range. It also involves **agility** (ability to change
  direction) and techniques like efficient routes or diving for the
  ball.
- **Throwing Strength:** How hard the fielder can throw the ball,
  usually quantified by throw velocity (e.g. an outfielder with a very
  strong arm might throw 90–100+ mph on a line). Strength determines the
  speed of the ball in flight and thus how quickly a throw can reach a
  base.
- **Throwing Accuracy:** How precisely the fielder can target throws.
  This can be represented as a small random deviation in the throw’s
  direction or an error rate. Higher accuracy means throws consistently
  hit the target (e.g. the baseman’s glove) versus pulling them off the
  bag.
- **Transfer Time:** The time to transition from fielding the ball to
  beginning the throw. This includes the glove-to-hand exchange and any
  set-up steps. Infielders turning a double play, for example, have very
  low transfer times (on the order of 0.5 seconds or less for elite
  fielders) to complete the play quickly.

### Fielder Reaction and Range Dynamics

When a ball is put in play, the simulation evaluates each fielder’s
opportunity to make a play on it. Upon contact, a fielder first
experiences a **reaction delay** based on their skill – this delay
(perhaps 0.0–0.5 s as a tunable attribute) represents how quickly they
pick up the ball’s
trajectory[\[1\]](file://file_00000000a01c61f6b3bd07450fa35df9#:~:text=running%20speed%20,Then%20you%20decide%20the).
After this delay, the fielder accelerates toward the ball’s projected
landing or interception point. We model the fielder’s motion with basic
kinematics: given their acceleration and max sprint speed, we update
their velocity and position in small time steps as they run. A key
comparison is made: **can the fielder reach the ball’s location by the
time the ball gets
there?**[\[2\]](file://file_00000000a01c61f6b3bd07450fa35df9#:~:text=,Then%20you%20decide%20the)
This determines if a catch or ground-ball stop is made: - The
batted-ball module provides the **ball’s flight path and hang time**
(time from contact to
landing)[\[3\]](file://file_00000000a01c61f6b3bd07450fa35df9#:~:text=As%20a%20starting%20point%2C%20you,had%20time%20to%20catch%20it).
Using that, we compute how far the fielder needs to run (distance from
their start position to the intercept point) and how long it will take
them to get there (based on their acceleration/speed profile). - For
example, if an outfielder needs to cover 100 ft and runs at a top speed
of 30 ft/s, they’d require at least ~3.3 seconds at full speed (plus
acceleration and reaction delay) to reach the spot. If the ball’s hang
time is 4.0 seconds, an elite outfielder who reacts instantly might just
make the catch; a slower fielder or late jump would arrive too
late[\[1\]](file://file_00000000a01c61f6b3bd07450fa35df9#:~:text=running%20speed%20,Then%20you%20decide%20the).
We incorporate these calculations to decide the outcome: if the
fielder’s arrival time is \<= ball arrival time (or only fractions of a
second after), the fielder makes the catch; if not, the ball drops for a
hit. This mirrors real Statcast “catch probability” logic, which factors
how far and how fast a fielder must run for a catch. - Reaction time
plays a huge role in close cases. A fielder with a 0.3 s reaction
penalty effectively has 0.3 s less to chase the ball. In the above
example, a poor reaction (say 0.5 s) would mean the fielder effectively
has only 3.5 s to cover 100 ft – likely too late. Conversely, a great
jump (0 s reaction) maximizes the available time. Our model allows
tuning this parameter to differentiate fielders.

**Fielding range** emerges naturally from the combination of speed,
acceleration, and reaction. An infielder with blazing acceleration but
lower top speed might excel at balls hit nearby (quick first step),
while an outfielder with high top-end speed can run down long fly balls
in the gap. We can validate range realism by comparing simulation
results to real-world metrics: for instance, Statcast’s Outs Above
Average metric considers how often a player gets to balls with a given
distance/hang time difficulty. In our simulation, we can input benchmark
scenarios (like a ball landing 20 ft away in 1.5 seconds – which is a
very tough play requiring a near-immediate reaction and ~15 ft/s sprint)
and ensure that only the best-rated fielders make those plays. By
calibrating the attributes, we match average fielding success rates to
MLB norms.

We also account for **directional agility** – e.g. an outfielder might
have a slower start if they initially break the wrong way on a fly ball.
For now, we assume the fielder runs the optimal route to the ball (a
straight-line distance in our calculations). In future refinements, we
could add an *efficiency* factor to slightly lengthen the path for poor
route runners, but that edges into cognitive/strategic skill. The core
physics model treats the fielder like a particle accelerating toward the
target point.

### Catching and Fielding Actions

If the fielder reaches the ball in time, what happens next depends on
the ball’s state (air or ground) and the fielder’s capabilities: - **Fly
balls:** Reaching the spot means the player can attempt the catch. We
assume a competent fielder will secure the catch if present at the
landing point on time (we could introduce a small error probability for
drops, but realistically MLB fielders catch \>95% of balls they get to).
Thus, “out” results are determined by the reachability calculation. For
high realism, one could factor in ball-handling ratings (for example, an
outfielder with a below-average glove might misplay a few). But the
primary driver is getting there; once there, the catch is made. We also
simulate the momentum – a player might catch on the run, which could
influence their next action (like needing to decelerate or take a step
before throwing). - **Ground balls:** For infielders, a similar approach
is used. A grounder with a low launch angle has a short flight time
(essentially the ball is zipping close to the ground), so reaction time
and initial burst are critical. We compute if an infielder can cover the
lateral distance to the ball’s path before it gets by them or reaches
the outfield. For example, a shortstop might need to move 3 meters
laterally in 0.8 seconds to glove a sharp grounder – an attainable play
only if they react almost instantly. If the infielder reaches the ball’s
position in time, we record it as a ground ball fielded (out if they can
complete the throw to first in time; see Throwing section). If not, the
ball is “through” for a base
hit[\[4\]](file://file_00000000a01c61f6b3bd07450fa35df9#:~:text=angle%20might%20be%20a%20grounder,time%20becomes%20a%20single%2C%20etc).
We don’t simulate every bounce of the grounder in fine detail; instead,
we approximate that if a fielder is in position in time, they make a
routine play (assuming a clean pick-up). If they arrive just after the
ball passes, it’s a hit. This approach aligns with the concept that a
grounder becomes a single if not fielded within a short
window[\[4\]](file://file_00000000a01c61f6b3bd07450fa35df9#:~:text=angle%20might%20be%20a%20grounder,time%20becomes%20a%20single%2C%20etc).  
- **Line drives:** These are like hybrids – if hit near a fielder, they
might be caught (reaction time is paramount because of the ball’s
speed). If a line drive is out of reach during its very short flight,
it’s a hit. Our model doesn’t need special casing beyond using the
correct trajectory and hang time; a line drive simply often has a very
low hang time, making the catch probability low unless it’s nearly
straight at someone.

We can incorporate **dives or jumps** as extensions of fielding range.
For instance, if a fielder is just a few feet shy of the ball when time
runs out, we could allow a dive (which might extend their reach by, say,
5 feet but then leaves them with additional recovery time). Similarly,
an outfielder at the fence might leap vertically to rob a homer. These
are more advanced mechanics: in physics terms, a dive could be treated
as a last-moment high-acceleration lunge (perhaps if within a threshold
distance), resulting in a catch but at the cost of taking a bit longer
to get up and throw. In the current model, we can simplify by folding
that into “effective range” – e.g. a fielder with higher ability might
have a slightly larger range to reflect those athletic plays. Explicit
dive modeling could be added later for extra realism and visual effect.

### Throwing Mechanics and Accuracy

Once a fielder secures the ball (either via catch or picking up a
grounder), the next step is the throw. We model throws as ballistic
trajectories, subject to physics similar to pitches or batted balls
(gravity acting on them, and possibly air drag for long throws). Key
parameters are the fielder’s **throw strength** (initial velocity of the
throw) and **release accuracy** (initial direction).

- A strong-armed fielder can deliver the ball to a base faster, which is
  crucial for making outs on close plays. For example, an elite MLB
  shortstop might throw to first at 85–90 mph; an outfielder throwing
  home on a fly could reach 95+ mph in exceptional cases. In our
  simulation, we assign each fielder a maximum throw velocity. When they
  make a throw, we use that velocity (possibly with slight reductions if
  throwing on the move or off-balance, though that detail might be
  abstracted in the accuracy attribute). We then compute the flight of
  the ball: a throw is essentially a physics simulation of its own,
  typically a roughly straight-line trajectory to the target (we can
  assume fielders tend to keep throws relatively low, perhaps on a line
  or slight arc). Gravity will cause some drop over long distances, and
  we can include a modest air drag force (though over 100-150 feet, drag
  has a minor effect, but for consistency with the ball physics module
  we could include it). The result is a travel time for the throw. For
  instance, a 150 ft throw at 90 mph (~132 ft/s) on a line might reach
  the target in about 1.2 seconds. If the same throw is made at 75 mph
  (~110 ft/s), it takes closer to 1.4 seconds – a potentially
  significant difference for a close play.
- Throw **accuracy** is modeled by random variance in the horizontal and
  vertical angle of the throw’s initial velocity. A perfectly accurate
  throw will arrive on target; an inaccurate one might force the
  receiving player off the base or even result in an error
  (overthrow/pull). We can parameterize accuracy as a standard deviation
  in degrees. For example, a highly accurate fielder might have only ±1°
  of variance, while a poorer thrower might have ±3–5°. This could
  translate into the difference between a throw that hits the first
  baseman in the chest versus one that makes him step off the bag
  (possibly preventing the out). In simulation, if an inaccurate throw
  pulls the fielder off the base or is too high/low to handle, we would
  treat it as an error (allowing the runner to be safe, and possibly
  advance further if the ball gets past). Introducing a full error logic
  is optional, but at least an accuracy rating influences the likelihood
  of a successful out on close plays.
- **Transfer time** comes into play before the throw starts. We assign a
  small delay from the moment of catch/pickup to the moment the ball is
  released on a throw. Infielders turning a double play or fielding a
  slow roller often have transfers as low as ~0.3–0.5 seconds, whereas
  an outfielder catching a fly ball might take ~0.7–1.0 second to gather
  and crow-hop into a throw. We can use position-specific typical
  values, modulated by the player’s fielding skill attribute. This
  transfer time simply adds to the overall time it takes for the ball to
  reach the target after the fielder gains control. A longer transfer
  can be the difference between an out or not on bang-bang plays, just
  like a weaker arm would
  be[\[1\]](file://file_00000000a01c61f6b3bd07450fa35df9#:~:text=running%20speed%20,Then%20you%20decide%20the).
  In our calculations, if a shortstop fields a grounder and has, say, a
  0.4 s transfer and a 85 mph throw to first, and the runner is 4.3
  seconds away from first when the ball is hit, we can compute if the
  throw (taking 0.4 + flight_time) arrives before the runner.

By tuning throw strength and transfer times, we differentiate
quick-release infielders from those with cannon arms, etc. For example,
a third baseman might have a very strong arm (90+ mph throws) but a
slightly longer release, whereas a second baseman might have a quick
release but less velocity (shorter throw). These nuances ensure the
simulation reflects realistic trade-offs and style differences among
defenders.

### Putting It Together: Simulating a Fielding Play

Once the ball is hit, our fielding module steps in alongside the ball
flight simulation: 1. **Assign Responsibility:** Based on the ball’s
trajectory (landing location or ground path), determine which fielder
will attempt the
play[\[5\]](file://file_00000000a01c61f6b3bd07450fa35df9#:~:text=,The%20fielder%E2%80%99s).
This is usually obvious by convention (e.g. a ball to left field is the
left fielder’s play, a grounder toward shortstop is the shortstop’s).
For now we assume standard positioning and no extreme shifts – each
fielder covers a typical zone. 2. **Fielder Movement:** The chosen
fielder (and conceivably others for backup) begin moving as per their
reaction and speed. We continuously (or in discrete time steps) update
the fielder’s position toward the intercept point. We also keep track of
the time when/if they reach the point. If the ball is airborne, the
critical comparison is fielder arrival time vs ball arrival time as
described. If the ball is on the ground, we look at when/where the
fielder can intercept it along its path (which is essentially
immediately when it reaches that point, since ground balls are
accessible as soon as they pass that spot). 3. **Outcome – Catch or
Not:** If the fielder gets there in time, we record an out (fly out or
line out) or a *fielded ball* in the case of a grounder (not an out
until thrown to a base). If they cannot get there, the ball falls for a
hit. In either case, the play then transitions into the next phase:
either a throw (if there’s a play to be made on a runner) or the runners
advancing freely if no fielder has the ball yet. This boundary between
fielding and baserunning modules is critical – for instance, a fly ball
caught means all runners will be tagging up or holding (which is a
strategic element we won’t detail here), while a ball that drops means
the runners will try to advance as far as possible. Our simulation will
simply know whether the ball is in a fielder’s possession or not at each
moment. 4. **Throw Decision and Execution:** If an out is already made
(fly caught before it hits ground), often no throw is needed unless it’s
to double up a runner. For ground balls or hits, the fielder who picks
up the ball will usually make a throw to some base. The strategy of
where to throw (cutting down lead runner vs going for sure out) is a
managerial aspect we are not focusing on; we can assume a default logic
like “throw to the nearest base to get an advancing runner or to first
to get the batter”. The physics of the throw is then simulated as above
– we initiate a throw with the fielder’s attributes, and the ball
travels toward the target base with a certain arrival time and accuracy.
5. **Completion:** The result of the throw (caught by another fielder at
base vs not in time or errant) will determine the final outcome of that
play (out or safe, possibly errors). Meanwhile, other runners are
advancing, which brings us to the baserunning module. The beauty of a
physics-integrated approach is that all these timings play out
organically: e.g. if a runner is 88 feet from home when an outfielder
releases a throw from 200 ft away, will the 95 mph throw arrive at the
plate before the runner covers that last 88 ft? The sim can answer that
by comparing the runner’s speed profile and the throw’s flight time.

By following this procedure, we effectively recreate the full fielding
play: from crack of the bat to fielders chasing the ball, catching or
not, and throwing it back in. All of it is driven by the players’
physical attributes and the physics of motion, rather than predetermined
outcomes. We ensure consistency with the earlier modules by using the
same units and time steps – the ball flight, fielder running, and throws
can all be updated in the same simulation loop so that the interplay
(e.g. a ball being caught at a certain time, or a throw arriving at a
base) is synchronized correctly.

## Baserunning Mechanics Module

Once the ball is in play, **baserunners** (including the batter-runner)
sprint to advance bases. We model each runner with attributes akin to
fielders’ running attributes, with some additions for base-specific
actions. The goal is to simulate realistic base-to-base running times
and behaviors such as rounding bases and sliding, using physics where
possible rather than simplistic assumptions. Key baserunning parameters
include:

- **Acceleration:** How quickly the runner reaches top speed from
  standstill. This is crucial for steal attempts and getting out of the
  batter’s box. It can be expressed as a rate (ft/s²) or as the time to
  go from 0 to full sprint. For instance, a fast runner might reach a
  significant fraction of top speed in the first 3 steps (~1 second),
  whereas a slower accelerator might take over 2 seconds to really get
  moving.
- **Top Sprint Speed:** The maximum speed the runner can sustain in open
  space (similar to the fielder’s sprint speed, measured in ft/s). A
  player with 30 ft/s top speed will have a higher ceiling than one
  maxing at 25 ft/s. This directly influences times for long runs (like
  scoring from first on a double). We can use the same Statcast sprint
  speed values here – e.g. 27 ft/s average, 30+ ft/s elite – to
  calibrate our runners.
- **Base-to-Base Times:** Rather than hard-coding times, we derive them
  from acceleration and speed. For example, the distance from home to
  first is 90 feet. A typical average runner (let’s say ~27 ft/s top
  speed) might take around 4.3 seconds from home to first on a “clean
  run” (this aligns with MLB average home-to-first times). In
  simulation, this would emerge from the runner accelerating out of the
  box (with an initial 0.1–0.2 s reaction after hitting the ball, plus
  the physics of accelerating ~3 m/s² to top speed). We ensure the model
  produces realistic times: e.g., a very fast runner with great
  acceleration might do home-to-first in ~3.7–3.8 seconds, while a slow
  runner might need over 5 seconds. These times can be validated against
  known scouting data. Similarly, first to third (180 feet) or second to
  home (180 feet) times will emerge from the runner’s continuous motion
  (accounting for the need to turn, see below).
- **Rounding Bases and Turn Efficiency:** Unlike running in a straight
  line, going from first to third or any time a runner doesn’t stop at
  the next base involves **cornering**. Physics-wise, the runner cannot
  take a sharp 90° turn at full speed without either slowing down or
  taking a wider path (centripetal force limits). We model a **curved
  path** when rounding a base. A skilled runner maintains more speed
  through the turn via an optimal curve (often called a “banana route”
  when rounding first). We can approximate this by assigning a **turn
  radius** or an effective speed loss on turns. For example, a runner
  might start veering out a few steps before reaching first, hitting the
  bag on the inside corner, and continuing to second in a wide arc. Turn
  efficiency attribute could reduce the need to slow down. In practice,
  we might say an average runner has to drop to, say, 80% of top speed
  while negotiating the turn, whereas an efficient runner might only
  drop to 90%. This will impact their time: rounding first base (to go
  to second) might cost a few tenths of a second if done well, or over
  half a second if done poorly (due to a tighter turn or even a brief
  stutter step at the bag). Our simulation can implement this by having
  the runner gradually change direction along a curve – which can be
  done by applying lateral acceleration limits. If the lateral
  (centripetal) acceleration needed to turn at speed \$v\$ on radius
  \$r\$ is \$a = v^2/r\$, we enforce that this cannot exceed some
  threshold based on the runner’s agility. Thus, a less agile runner
  effectively has to slow (lower \$v\$) or take a larger \$r\$ (wider
  turn) to keep \$a\$ manageable.
- **Sliding Mechanics:** When approaching a base to stop or avoid a tag,
  runners often slide. Sliding is a physical process: the runner drops
  to the ground and skids, using friction to decelerate more rapidly
  than they could upright (and to get low to the base to avoid tags). We
  model a slide as a deceleration with friction. For example, once a
  runner begins a feet-first slide, the kinetic friction between their
  body/clothing and the ground (dirt of the basepaths) provides a
  deceleration force. A rough estimate: if the coefficient of friction
  is around 0.5–0.7, the deceleration might be on the order of 0.5*g to
  0.7*g (≈ 5–7 m/s² or 16–23 ft/s²) opposite the direction of motion. If
  a runner is going about 20 ft/s ( ~13.6 mph) when they start to slide,
  and friction deceleration is ~20 ft/s², they would come to rest in
  about 1 second, covering roughly 10–15 feet in that slide. We can
  implement sliding by triggering it when the runner is a certain
  distance from the target base (such that their slide will end with
  them at the base). The simulation would then switch the runner’s
  motion to a deceleration profile. If the runner needs to stop at that
  base, they will slide if running fast; if they are slowing down anyway
  (e.g. going station-to-station on a single), they might just slow down
  normally and step on the base without a slide. Sliding also has a
  strategic component (avoiding tags by going around them) which we
  won’t deeply simulate, but we can allow that a slide gets the runner
  to touch the base while their body is low.
- **Lead and Reaction (for runners already on base):** Although we’re
  not focusing on steal decisions, the physics of a runner leading off
  and then accelerating on contact is important. A runner on first, for
  instance, might have a lead of a few feet and will only start running
  once they register that the ball is in play (which could be virtually
  immediate on contact if it’s clearly a hit, or delayed if they have to
  wait to see if a line drive is caught). In our physical model, we
  could give all baserunners a small reaction delay after the moment of
  contact to simulate this “read” time (e.g. 0.1–0.3 s, shorter with two
  outs since they run on contact). This reaction time plus acceleration
  will determine how quickly they can attain full speed toward the next
  base.

### Simulating Runner Advancement

In the simulation, each runner is essentially another moving object with
its own kinematics. We update their positions in time alongside the ball
and fielders. Here’s how the baserunning module works in concert with
fielding: - **Initial takeoff:** The batter-runner starts at home plate
at time of contact. We simulate their run to first by applying their
acceleration until top speed, just like a sprinter out of the box. Other
runners (already on base) will begin to run if the situation demands
(they may hesitate briefly if the ball might be caught – but such
decision-making is beyond pure physics so we could assume for simplicity
that they run on contact and later we handle if they need to return).
For now, we assume less than 2 outs, so runners are going on contact. We
give them that small reaction delay and then accelerate. We track their
distance covered along the basepath. The basepaths are 90 ft straight
segments (except home to first is straight, first to second is straight,
etc., but connecting them involves right-angle turns). We handle turns
by switching the runner’s direction gradually as described (a curved
trajectory from one base toward the next). - **Updating positions:** At
each time step, we update each runner’s velocity and position. If they
reach a base, we check whether they intend to continue to the next. That
intention would depend on game logic (for example, a batter might
automatically round first and try for second on a clear double; a runner
on first might try for third on a single to outfield, etc.). In a pure
physics sense, we can have them **always run full speed** and only stop
when the ball being fielded forces them to (which would be determined by
the outcome or a base coach decision). Since strategy is out of scope,
we could simplify: if the ball drops for a hit, all runners attempt to
advance as far as they physically can until the defense stops them
(either by throwing them out or the play ending). - **Comparing times
for plays:** The critical integration is when a fielder makes a throw to
a base – we then have a race between the ball and the runner. For
example, consider a ground ball to shortstop with a runner on first. The
shortstop fields and throws to second base for a force out. We simulate:
the runner on first is, say, 20 ft from second base when the throw is
released; the throw from the shortstop (maybe ~60 ft away) takes perhaps
0.5 seconds to get there. The runner’s speed at that moment might be,
say, 25 ft/s. In 0.5 s they can cover about 12.5 ft. If they had 20 ft
to go, they’ll arrive in ~0.8 s, meaning the ball (0.5 s) will beat them
by 0.3 s – the runner is out. If instead the runner was faster or got a
better jump and was only, say, 10 ft away when the throw was made,
they’d cover that in ~0.4 s and reach before the ball – safe. The
simulation naturally handles this by continuously updating positions and
checking when the ball and runner reach the base. We can set a rule: a
force out occurs if the ball arrives at the base (caught by the fielder)
at or before the same time as the runner – otherwise the runner is safe.
We will likely use a small time tolerance to account for the notion of
“tie goes to the runner” or simply treat equal times as safe for the
runner for realism. - **Advancing extra bases:** For hits that go to the
outfield, runners will often try to take multiple bases. Our model will
just keep them running until the play ends, but how do we determine when
to stop? In reality, runners stop when the ball is back to the infield
or a coach signals them. We can approximate this by checking the ball’s
state: if an outfielder fields the ball quickly and throws it in, the
runners might only take one base; if the ball rolls to the wall, they
might take two or three. Without explicit strategy coding, one approach
is to simulate them running and see where the ball is: e.g., the
batter-runner will try for second (a double) if by the time they reach
first base the ball is not yet in the infielder’s glove near second. A
simpler rule from the development plan was to predetermine
single/double/triple by how far the ball was
hit[\[6\]](file://file_00000000a01c61f6b3bd07450fa35df9#:~:text=hit%20type%3A%20if%20it%20wasn%E2%80%99t,like%20if%20the),
but here we can do better by using physics: we literally see if the
runner can reach the next base before the defense can make a play on
them. If yes, they take that base; if not, they hold. - For example,
batter hits a gapper: as the batter rounds first, the ball is still
bouncing in the deep outfield. The batter will head to second. We’d
simulate the outfielder chasing, picking up, and throwing to second. We
compare the batter’s arrival at second vs the ball’s arrival. If the
batter wins, it’s a successful double; if the throw beats them, they’d
be out trying to stretch. This requires simulating that decision moment.
We might implement a conservative logic: the runner will only attempt
the extra base if, at the point they’re approaching the current base,
the ball is still far enough away. In practice, we might just always
send them and let the physics decide safe/out. This yields organically
the cases of runners thrown out. - **Sliding at home or other bases:**
When runners approach a base where a tag might happen (home plate, or
any base on a non-force play), they usually slide to try to avoid the
tag and stop on the base. We simulate the slide as described: at a
certain distance from the base (maybe 10-15 feet, tuned by their speed –
faster runners need to start slide earlier), we switch their mode to
sliding (a deceleration). We ensure that the slide distance roughly
equals the remaining distance to the base. If a runner is trying to
score from second, for instance, and an outfielder is throwing home,
we’ll have the runner slide and reach the plate at some time. The
catcher (fielder) receiving the throw will be there at a certain time. A
tag play then is resolved by who gets there first (ball or runner) and
by a margin; our accuracy modeling can determine if the catcher has to
move for the ball, possibly affecting the timing of the tag. These
subtleties might be beyond the scope of our initial implementation, but
the pieces are in place: runner arrival time, ball arrival time, and
maybe an added small delay for the act of applying the tag versus the
runner touching plate.

In summary, the baserunning module treats runners as moving entities
subject to acceleration and speed limits, navigating a path (with
possible curves) and occasionally switching to a sliding deceleration.
The output is their position as a function of time. This, combined with
the fielding output (ball position and possession as a function of
time), allows the simulation to determine the outcome of each runner’s
advance in a physically realistic way.

## Integration with Existing Physics Modules

Integrating fielding and baserunning with the pitching and batted-ball
modules yields a complete play simulation. The **pipeline** for a ball
in play is as follows: a pitch is thrown (pitching module), the batter
makes contact and the ball’s trajectory is simulated (batted-ball
module), then the fielders and runners react to that trajectory
(fielding & baserunning modules). All modules operate on the same
physics timeline. Here’s how they connect:

- **Using Batted-Ball Outputs:** The trajectory model provides the
  ball’s path, including its landing spot and hang time (or time to
  reach various
  points)[\[3\]](file://file_00000000a01c61f6b3bd07450fa35df9#:~:text=As%20a%20starting%20point%2C%20you,had%20time%20to%20catch%20it).
  This information seeds the fielding module – as soon as contact is
  made, fielders know (in the simulation “omnisciently”; in reality with
  some delay) roughly where the ball is heading. We use it to decide who
  fields the ball and where they need to go. The hang time or arrival
  time at a location is the deadline for the fielder’s
  motion[\[2\]](file://file_00000000a01c61f6b3bd07450fa35df9#:~:text=,Then%20you%20decide%20the).
  Likewise, if the ball is not caught and becomes a hit, the landing
  spot and subsequent bounce/roll determine how long it stays in the
  field. We can simulate basic post-landing physics too (the ball
  rolling on grass/dirt with friction, or bouncing off a wall) – this
  affects how quickly an outfielder can retrieve it and thus influences
  runner decisions. For now, we might simplify by assuming once a ball
  hits the ground, it slows and comes to rest or is picked up after,
  say, one bounce (this could be enhanced with a simple ground friction
  model later).
- **Coordinating Fielders and Runners:** After the ball is in play,
  multiple agents (fielders and runners) move simultaneously. We handle
  this by updating all positions in small increments (e.g. every 0.01 or
  0.02 s of simulated time). The pitching and batting were probably
  handled in a mostly analytical or time-stepped flight calculation; we
  now continue the time steps for fielding/running. At each step, we can
  check for events: ball caught, ball picked up, runner reaching a base,
  throw made, etc. For instance, if at \$t = 4.2\$ s the ball lands in
  the outfield and is picked up at \$t = 5.0\$ s by the fielder, between
  those times the runners are just advancing freely. When the fielder
  picks it up, we might trigger a throw at \$t = 5.1\$ s. The throw then
  has its own flight to, say, second base at \$t = 6.0\$ s. We check the
  lead runner’s arrival at second – maybe he got there at \$t = 5.8\$ s,
  so he’s safe, and perhaps he stays put once the ball is in the
  infield. Another runner might be heading home; we’d then consider if
  the fielder instead throws home, etc. (Strategic throw decisions can
  be pre-scripted: e.g. throw to the lead runner’s base if a play is
  possible, otherwise hold or throw to second to keep double play in
  order, etc. For now, assume sensible default decisions hardcoded).
- **Game State Updates:** When the physics engine determines an out
  (fielder catches a ball, or a throw beats a runner to a base), we
  update the game state (outs, runner locations, score if someone
  scored,
  etc.)[\[7\]](file://file_00000000a01c61f6b3bd07450fa35df9#:~:text=,physics%20game).
  This is more of a rule layer on top of the physics: e.g. if a runner
  crosses home, that’s a run; if a third out was made on the bases, the
  inning ends and other runners don’t count if they hadn’t scored before
  that out, etc. These rules are implemented to interpret the physics
  outcomes in baseball terms. The important point is that our fielding
  and running model feeds into this logic with realistic timing – so a
  6-4-3 double play can happen if the physics says the ball went from
  shortstop to second to first in time to get both runners. The
  simulation can naturally produce such outcomes (and we can
  double-check that the frequencies of double plays, etc., line up with
  real baseball by adjusting our assumptions on transfer times and
  such).
- **Consistency with Pitch/Bat Physics:** Our pitching module provided
  initial conditions for the batted ball (e.g. pitch influences
  probability of contact), and the batted-ball module produced a
  realistic trajectory. Now, fielding uses that trajectory physically.
  This integrated approach ensures that, for example, a hard-hit ball to
  the gap will *feel* right – it will simply be too quick for fielders
  to catch if the physics says so, leading to extra bases, as happens in
  real games. Slower, high fly balls will allow fielders to range under
  them for outs. By basing everything on the underlying physics and
  known player abilities, we avoid arbitrary outcomes. That said, we
  will calibrate the modules together: if we find fielders are
  unrealistically catching everything, we might adjust reaction times or
  sprint speeds; if runners are never thrown out stretching a single
  into a double, maybe our outfielders need a slight boost in arm
  strength or our runners are a tad slow in deceleration. The integrated
  testing will fine-tune the balance.

Ultimately, with the fielding and baserunning mechanics in place, our
simulation engine can **model an entire play from pitch to final out
with high fidelity**. For example, consider a sample play: Batter hits a
line drive into the right-center gap. Our batted-ball model says it
lands at the wall in 4.5 seconds. The center fielder’s fielding module
instance sees this: he has to run ~100 feet. His reaction is 0.2 s,
sprint speed 28 ft/s – he *won’t* catch it before it lands (he’d need
~3.6 s plus reaction, which is \>4.5 s). The ball lands and bounces off
the wall; we simulate a bounce and a slower roll. The center fielder
reaches it at, say, 6.0 s, and immediately goes into a throw animation
to second base. Meanwhile, the batter-runner was sprinting: by 6.0 s,
he’s well past first and heading to second. We simulate his turn around
first (maybe he slowed a bit to 25 ft/s on the curve and then
re-accelerated). He might get to second by ~7.0 s. The fielder’s throw
from the wall (perhaps 200+ ft away) at 90 mph takes about 1.5–2.0 s to
reach second. It arrives around 7.5–8.0 s. Our runner got there at 7.0
s, so he’s safe standing with a double. The physics engine produces this
outcome naturally. Had the batter been slower, maybe he’d arrive at 7.8
s and be tagged out at second at 7.5 s as the ball arrives – a
thrown-out trying to stretch a single. All these possibilities emerge
from the ratings and physics. We can compare such outcomes to real game
data (how often are doubles stretched and runners thrown out) to
validate our model.

One more integration point: we ensure that **units and coordinate
systems** are consistent across modules. If the batted-ball gives us
trajectory in a global field coordinate (e.g. home plate at (0,0), x
along first base line, y along third base line, z vertical), we use the
same for fielders and runners. Fielders have starting coordinates (we
hardcode typical positions: e.g. shortstop at (~-20, 80) feet from home,
etc.). Runners move along basepath coordinates (which correspond to
those lines). We’ll define bases’ coordinates (first base ~ (90,0),
second ~(90,90), third ~(0,90) in a right-angle coordinate system, for
instance). Using these, everything in the simulation operates on one
“field map.” Gravity and units (feet, seconds) remain consistent.

In conclusion, the fielding and baserunning modules complement the
pitching and hitting physics to simulate full baseball plays. We focused
purely on the **physical and mechanical aspects** – how fast players
run, how they accelerate, how far they can reach, how strong and
accurate throws are, and how runners slow down or speed up – without
diving into strategic AI. This foundation can later support strategy
layers (like choosing which base to throw to, or when to hold a runner).
By first getting the physics right for the nine fielders and the
baserunners, we ensure that any emergent gameplay is grounded in
reality. The end result is a simulation where plays unfold
realistically: you’ll see gappers turn into doubles and triples because
the outfielders couldn’t defy physics, you'll see slow rollers result in
bang-bang plays at first determined by real footspeed and exchange
times, and you’ll see the excitement of close plays at the plate decided
by a fraction of a second – all calculated by the engine in a way that
mirrors real-world baseball
kinetics[\[2\]](file://file_00000000a01c61f6b3bd07450fa35df9#:~:text=,Then%20you%20decide%20the)[\[8\]](file://file_00000000a01c61f6b3bd07450fa35df9#:~:text=,the%20end%20of%209%20innings).
With this level of detail in fielding and baserunning, our simulation’s
defensive and running gameplay will achieve the same depth and realism
as our pitching and hitting modules.

**Sources:** We have based these modeling choices on known empirical
data and research. Key references include Statcast measurements of
player speed (sprint speed in ft/s) and throwing velocity, which inform
the ranges of values used for attributes. Fielding metrics like Outs
Above Average guided our approach to modeling catch probability via
distance and time. Additionally, general physics (kinematics for
acceleration, friction for sliding, and projectile motion for throws)
underpins the mechanics. Wherever empirical data was lacking (e.g. exact
acceleration profiles), we used reasonable estimates and will calibrate
those with expected outcomes. The development notes for our project
provided a blueprint for integrating these
systems[\[2\]](file://file_00000000a01c61f6b3bd07450fa35df9#:~:text=,Then%20you%20decide%20the)[\[8\]](file://file_00000000a01c61f6b3bd07450fa35df9#:~:text=,the%20end%20of%209%20innings),
ensuring that the fielding and baserunning module interfaces correctly
with the existing simulation framework. The result is a comprehensive,
physics-driven model for defense and baserunning that complements our
earlier pitching and batted-ball physics modules.

------------------------------------------------------------------------

[\[1\]](file://file_00000000a01c61f6b3bd07450fa35df9#:~:text=running%20speed%20,Then%20you%20decide%20the)
[\[2\]](file://file_00000000a01c61f6b3bd07450fa35df9#:~:text=,Then%20you%20decide%20the)
[\[3\]](file://file_00000000a01c61f6b3bd07450fa35df9#:~:text=As%20a%20starting%20point%2C%20you,had%20time%20to%20catch%20it)
[\[4\]](file://file_00000000a01c61f6b3bd07450fa35df9#:~:text=angle%20might%20be%20a%20grounder,time%20becomes%20a%20single%2C%20etc)
[\[5\]](file://file_00000000a01c61f6b3bd07450fa35df9#:~:text=,The%20fielder%E2%80%99s)
[\[6\]](file://file_00000000a01c61f6b3bd07450fa35df9#:~:text=hit%20type%3A%20if%20it%20wasn%E2%80%99t,like%20if%20the)
[\[7\]](file://file_00000000a01c61f6b3bd07450fa35df9#:~:text=,physics%20game)
[\[8\]](file://file_00000000a01c61f6b3bd07450fa35df9#:~:text=,the%20end%20of%209%20innings)
Development Plan.md

<file://file_00000000a01c61f6b3bd07450fa35df9>
