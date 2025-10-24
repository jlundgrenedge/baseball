# Modeling Baseball Pitching Dynamics for High‑Realism Simulation

Building a high-realism pitching module requires integrating physics
with baseball specifics. This report examines how to simulate various
pitch types, their spin and movement, release mechanics, and
environmental effects, and how these factors translate into on-field
outcomes. We also propose how to parameterize pitchers (via attributes
like velocity, spin, command, deception) to drive a realistic game
engine.

## Pitch Types and Key Characteristics

Modern pitchers use a variety of pitch types, each with distinct
velocity ranges, spin profiles, and movement. **Table 1** summarizes the
key characteristics of major pitch categories – including typical speed,
spin rate, spin axis/orientation, and movement (“break”). These values
are based on MLB Statcast averages and physics principles:

| **Pitch Type** | **Velocity (mph)** | **Spin Rate (rpm)** | **Spin Axis / Orientation** | **Movement Profile (Break)** |
|----|----|----|----|----|
| **Four-Seam Fastball** (RHP) | ~90–100 (avg ~93)[\[1\]](https://www.mlb.com/news/statcast-spin-rate-compared-to-velocity-c160896926#:~:text=Velocity%20Highest%20velo%3A%2099,knuckler) | ~2,200 (avg)[\[2\]](https://www.mlb.com/news/statcast-spin-rate-compared-to-velocity-c160896926#:~:text=Spin%20Highest%20spin%3A%202%2C553%20rpm%2C,than%20Stephen%20Strasburg%20or%20Jose) | Backspin (axis roughly horizontal, ball spinning with bottom moving toward catcher) | “Rises” or falls less than gravity: ~8–12″ less drop than a spinless pitch[\[3\]](https://baseball.physics.illinois.edu/Denver.html#:~:text=average%20speed%20is%20about%2096,about%204%20inches%20less%20at). Minimal horizontal break (some arm-side tail if axis is tilted). |
| **Two-Seam Fastball / Sinker** | ~88–95 (avg ~92)[\[4\]](https://www.mlb.com/news/statcast-spin-rate-compared-to-velocity-c160896926#:~:text=Velocity%20Highest%20velo%3A%2098,CUT%20FASTBALL) | ~2,100 (avg)[\[5\]](https://www.mlb.com/news/statcast-spin-rate-compared-to-velocity-c160896926#:~:text=Spin%20Highest%20spin%3A%202%2C484%20rpm,1%2C763%20rpm%29%20had%20the) | Tilted backspin with some sidespin (axis ~1–2 o’clock from RHP view) | More downward drop than a four-seam (due to lower backspin) and notable arm-side run. Induces “sink” and ~6–10″ of arm-side tail. Lower spin sinkers dive more and generate grounders[\[6\]](https://www.mlb.com/news/statcast-spin-rate-compared-to-velocity-c160896926#:~:text=MLB%20average%3A%202%2C123%20rpm%20Lowest,Velocity). |
| **Cutter** | ~85–95 (avg ~88)[\[7\]](https://www.mlb.com/news/statcast-spin-rate-compared-to-velocity-c160896926#:~:text=Velocity%20Highest%20velo%3A%2095,5%20mph) | ~2,200 (avg)[\[8\]](https://www.mlb.com/news/statcast-spin-rate-compared-to-velocity-c160896926#:~:text=Spin%20Highest%20spin%3A%202%2C555%20rpm%2C,high%20spin%20on%20a%20cutter) | Slightly tilted backspin (between a four-seam and slider axis) | Late glove-side cut of a few inches with modest drop (often ~2–5″ horizontal break). A cutter is essentially a small slider: faster than a true slider but with tighter, shorter break. High spin helps its movement[\[8\]](https://www.mlb.com/news/statcast-spin-rate-compared-to-velocity-c160896926#:~:text=Spin%20Highest%20spin%3A%202%2C555%20rpm%2C,high%20spin%20on%20a%20cutter). |
| **Slider** | ~78–88 (avg ~85)[\[9\]](https://www.mlb.com/news/statcast-spin-rate-compared-to-velocity-c160896926#:~:text=Velocity%20Highest%20velo%3A%2091,mph%3B%20the%20second%20slowest%20is) | ~2,000 (avg)[\[10\]](https://www.mlb.com/news/statcast-spin-rate-compared-to-velocity-c160896926#:~:text=Spin%20Highest%20spin%3A%202%2C654%20rpm%2C,5%20mph%2C%20Caminero) (wide range) | Side-spin or diagonal spin (axis tilted toward pitcher’s arm side) | Sharp glove-side horizontal break (~6–12″) with some downward drop. Thrown with **lower spin efficiency** (~30–40% active spin on average[\[11\]](https://www.seemagnus.com/blog-posts-test/a-discussion-of-spin-efficiency#:~:text=Pitch%20Type2020%20Mean%20MLB%20Spin,Seam%20Fastball89.8Cutter49.1Sinker89.0Changeup89.3Curveball68.7Slider35.9Values%20are%20approximate)) – many sliders have bullet-like spin, yielding more lateral break and less Magnus lift. Sliders vary widely; harder sliders have less drop, slower ones can sweep more. |
| **Curveball** (“12–6” overhand) | ~70–80 (avg ~78)[\[12\]](https://www.mlb.com/news/statcast-spin-rate-compared-to-velocity-c160896926#:~:text=belongs%20to%20Carlos%20Martinez%20at,KNUCKLE%20CURVE) | ~2,300 (avg)[\[13\]](https://www.mlb.com/news/statcast-spin-rate-compared-to-velocity-c160896926#:~:text=Spin%20Highest%20spin%3A%203%2C086%20rpm%2C,Velocity) | Topspin (forward spin, axis near vertical) | Heavy downward break (“drop”) due to topspin Magnus force. A true 12–6 curve has ~12–20″ more drop than a fastball, with little lateral movement. High-spin curves dive more sharply[\[14\]](https://www.mlb.com/news/statcast-spin-rate-compared-to-velocity-c160896926#:~:text=Curves%20are%20thrown%20slowly%2C%20generally,spin%3A%201%2C302%20rpm%2C%20Logan%20Kensing)[\[13\]](https://www.mlb.com/news/statcast-spin-rate-compared-to-velocity-c160896926#:~:text=Spin%20Highest%20spin%3A%203%2C086%20rpm%2C,Velocity). Slurves or 3/4-arm curves will have a mix of downward and glove-side break. |
| **Changeup** (e.g. circle change) | ~75–88 (avg ~84)[\[15\]](https://www.mlb.com/news/statcast-spin-rate-compared-to-velocity-c160896926#:~:text=though%20more%20spin%20on%20a,difference%20between%20his%20fastball%20and) (usually 5–10+ mph slower than fastball) | ~1,500–1,800 (avg ~1,750)[\[16\]](https://www.mlb.com/news/statcast-spin-rate-compared-to-velocity-c160896926#:~:text=Spin%20Highest%20spin%3A%202%2C421%20rpm%2C,Velocity) | Backspin (like a slow fastball, often with slight arm-side tilt) | Less velocity and often lower spin cause it to drop more than a fastball. Many changeups also have slight arm-side fade (due to pronation imparting some sidespin). The result is ~2–4″ more drop than a four-seam and a few inches of arm-side fade, deceiving hitters by mimicking a fastball before dying low. |
| **Splitter** (Split-Finger FB) | ~80–90 (avg ~85)[\[17\]](https://www.mlb.com/news/statcast-spin-rate-compared-to-velocity-c160896926#:~:text=highest,most%20unexpectedly%20dominant%20pitch%20in)[\[15\]](https://www.mlb.com/news/statcast-spin-rate-compared-to-velocity-c160896926#:~:text=though%20more%20spin%20on%20a,difference%20between%20his%20fastball%20and) | ~1,000–1,600 (avg ~1,524)[\[18\]](https://www.mlb.com/news/statcast-spin-rate-compared-to-velocity-c160896926#:~:text=Spin%20Highest%20spin%3A%202%2C077%20rpm%2C,4%20mph%2C%20Familia) | Forward tumble (partial topspin, or simply very low spin) | The splitter is gripped to kill spin, causing a **“knuckle” effect**. It has significantly more drop – the “bottom falls out” late. Low spin (often \<1500 rpm) means gravity dominates, so a splitter might drop on the order of 4–6″ more than a changeup. Little horizontal movement typically. Low-spin splitters excel at inducing ground balls[\[18\]](https://www.mlb.com/news/statcast-spin-rate-compared-to-velocity-c160896926#:~:text=Spin%20Highest%20spin%3A%202%2C077%20rpm%2C,4%20mph%2C%20Familia). |
| **Knuckleball** | ~65–80 (typically 70s) | \<500 (very low) | No consistent axis (wobbles; near-zero spin) | **Unpredictable flutter**. With almost no spin, Magnus effect is negligible; instead, seam effects and vortices make the ball dance randomly. A good knuckler can drift or “zig-zag” a few inches in multiple directions unpredictably[\[19\]](https://www.comsol.it/blogs/physics-behind-baseball-pitches#:~:text=The%20knuckleball%20is%20the%20most,easier%20to%20hit%20because%20the)[\[20\]](https://www.comsol.it/blogs/physics-behind-baseball-pitches#:~:text=actually%20its%20enemy,as%20seen%20in%20this%20GIF). (High spin destroys this effect, so knuckleballers strive for minimal rotation.) |

**Table 1:** Typical velocity, spin, and movement for common pitch
types. (RHP = right-handed pitcher; movement directions are described
for RHP perspective.) High-speed pitches like fastballs have backspin
that resists gravity, whereas breaking balls (curves, sliders) use
topspin or side-spin to deviate the ball’s path. Data from Statcast
pitch
tracking[\[1\]](https://www.mlb.com/news/statcast-spin-rate-compared-to-velocity-c160896926#:~:text=Velocity%20Highest%20velo%3A%2099,knuckler)[\[10\]](https://www.mlb.com/news/statcast-spin-rate-compared-to-velocity-c160896926#:~:text=Spin%20Highest%20spin%3A%202%2C654%20rpm%2C,5%20mph%2C%20Caminero).

**Fastballs (Four-Seam):** The four-seamer is the primary power pitch.
Its tight backspin stabilizes the ball and creates an upward Magnus
force (more on Magnus below) that makes it drop slower than expected.
This gives a “rising” illusion to hitters. Four-seams average around
92–95 mph in today’s game with ~2200 rpm of
backspin[\[1\]](https://www.mlb.com/news/statcast-spin-rate-compared-to-velocity-c160896926#:~:text=Velocity%20Highest%20velo%3A%2099,knuckler).
Because of the backspin, a 4-seam fastball might only drop ~12 inches on
its way to the plate instead of ~18 inches under gravity alone (i.e. a
~6″ “rise” relative to a spinless
trajectory)[\[3\]](https://baseball.physics.illinois.edu/Denver.html#:~:text=average%20speed%20is%20about%2096,about%204%20inches%20less%20at).
This flatter trajectory often leads to late swings or hitters
undercutting the ball (resulting in pop-ups or whiffs). Four-seamers
have little horizontal break (usually \<5″ to the arm side) since the
spin axis is typically near-horizontal, so the Magnus force is mostly
upward.

**Two-Seam & Sinker:** Two-seam fastballs (sinkers) are thrown with a
grip along the seams to induce more finger-side spin and slightly lower
spin rate. They average ~91–92 mph and ~2100
rpm[\[4\]](https://www.mlb.com/news/statcast-spin-rate-compared-to-velocity-c160896926#:~:text=Velocity%20Highest%20velo%3A%2098,CUT%20FASTBALL).
The spin axis is tilted, producing some topspin component. As a result,
sinkers have **more downward break** than four-seamers (gravity is less
resisted) and **arm-side run** (the Magnus force has a lateral component
toward the arm side). A good sinker from a righty might break down and
to the right ~6–10 inches each way, diving under bats and toward the
hitter’s hands. Because sinkers “drop” more, they tend to induce ground
balls. In fact, pitchers with very low-spin sinkers (e.g. Wily Peralta
~1740 rpm) had among the highest ground-ball
rates[\[6\]](https://www.mlb.com/news/statcast-spin-rate-compared-to-velocity-c160896926#:~:text=MLB%20average%3A%202%2C123%20rpm%20Lowest,Velocity).
By contrast, a sinker with unusually high spin is actually
counterproductive – it won’t sink as much (acting more like a straight
fastball)[\[6\]](https://www.mlb.com/news/statcast-spin-rate-compared-to-velocity-c160896926#:~:text=MLB%20average%3A%202%2C123%20rpm%20Lowest,Velocity).

**Cutters:** A cutter is thrown like a four-seam but with a slightly
off-center grip. This reduces backspin efficiency and adds a bit of
slider-like spin. Cutters are generally 85–90 mph (slower than
four-seams) with spin ~2100–2300
rpm[\[21\]](https://www.mlb.com/news/statcast-spin-rate-compared-to-velocity-c160896926#:~:text=Spin%20Highest%20spin%3A%202%2C555%20rpm%2C,6%20mph%2C%20Richards).
The spin axis is such that the ball has a small amount of glove-side
Magnus force. The result is a late-breaking, small lateral movement –
often just a few inches – that “cuts” away from a same-handed batter’s
barrel at the last moment. Mariano Rivera’s legendary cutter had high
spin (~2500+ rpm) and tight 3–5″ glove-side break, constantly sawing off
bats[\[22\]](https://www.mlb.com/news/statcast-spin-rate-compared-to-velocity-c160896926#:~:text=Spin%20Highest%20spin%3A%202%2C555%20rpm%2C,Velocity).
High spin is desirable for cutters to maximize that late movement.

**Sliders:** A slider is a harder, lateral-breaking pitch in the mid-80s
(avg
~85 mph)[\[9\]](https://www.mlb.com/news/statcast-spin-rate-compared-to-velocity-c160896926#:~:text=Velocity%20Highest%20velo%3A%2091,mph%3B%20the%20second%20slowest%20is)
with spin ~2000
rpm[\[10\]](https://www.mlb.com/news/statcast-spin-rate-compared-to-velocity-c160896926#:~:text=Spin%20Highest%20spin%3A%202%2C654%20rpm%2C,5%20mph%2C%20Caminero),
though both speed and spin vary widely. The defining feature is its
**gyrospin** – many sliders are thrown with bullet-like spin (imagine a
football spiral). This means a large portion of the spin does *not*
produce Magnus force (low spin efficiency ~30–40% on
average)[\[11\]](https://www.seemagnus.com/blog-posts-test/a-discussion-of-spin-efficiency#:~:text=Pitch%20Type2020%20Mean%20MLB%20Spin,Seam%20Fastball89.8Cutter49.1Sinker89.0Changeup89.3Curveball68.7Slider35.9Values%20are%20approximate).
Instead of big topspin drop, a slider gets a shorter, more cutting
break. It will dart glove-side (~6–12″ horizontally) and usually have
some downward tilt (a hard slider might only drop a few inches more than
a fastball, whereas a slower, sweepy slider can drop more). Because
sliders rely on sidespin, they are most effective when thrown with a
consistent tight spiral – any wobble can make break less consistent.
Sliders can be deadly chase pitches, starting in the strike zone and
breaking out of it late.

**Curveballs:** A curveball uses topspin to get dramatic downward break.
Thrown ~72–82 mph (much slower) with high spin (avg ~2300 rpm, many
exceeding
2500)[\[23\]](https://www.mlb.com/news/statcast-spin-rate-compared-to-velocity-c160896926#:~:text=Curves%20are%20thrown%20slowly%2C%20generally,pitch%20of%20any%20pitcher%20all)[\[13\]](https://www.mlb.com/news/statcast-spin-rate-compared-to-velocity-c160896926#:~:text=Spin%20Highest%20spin%3A%203%2C086%20rpm%2C,Velocity),
a curve’s spin axis is near-vertical. That forward spin generates a
Magnus force downward, *with* gravity, causing the pitch to drop much
more than other pitches. An overhand “12–6” curve (spin axis truly
vertical) might have 40–50% more drop than a same-speed pitch with no
spin. For example, a curve might break downward on the order of 15–20″
versus ~12″ gravity-only drop – an extra several inches that often fools
batters. High-spin curves accentuate this: Garrett Richards famously had
a curve over 3000 rpm that dived sharply and was very hard to
hit[\[13\]](https://www.mlb.com/news/statcast-spin-rate-compared-to-velocity-c160896926#:~:text=Spin%20Highest%20spin%3A%203%2C086%20rpm%2C,Velocity).
Some curves (thrown from a lower arm slot or with angled spin axis) also
have a horizontal component, breaking diagonally. A “knuckle curve” is a
variation where the finger grip kills some spin; it tends to have
slightly less predictable movement but still primarily drops
hard[\[24\]](https://www.mlb.com/news/statcast-spin-rate-compared-to-velocity-c160896926#:~:text=KNUCKLE%20CURVE)[\[25\]](https://www.mlb.com/news/statcast-spin-rate-compared-to-velocity-c160896926#:~:text=Lowest%20spin%3A%201%2C122%20rpm%2C%20Carter,7).
In general, curveballs thrown with topspin will “bite” downward, often
inducing hitters to swing over the ball or freeze as it drops into the
zone.

**Changeups & Splitters:** Changeups are off-speed pitches thrown to
mimic a fastball’s release but with lower velocity and spin. A typical
changeup is ~10 mph slower than the fastball (mid-80s for a pitcher
whose fastball is
mid-90s)[\[26\]](https://www.mlb.com/news/statcast-spin-rate-compared-to-velocity-c160896926#:~:text=Changeups%20are%20low%20spin%20and,Spin)[\[15\]](https://www.mlb.com/news/statcast-spin-rate-compared-to-velocity-c160896926#:~:text=though%20more%20spin%20on%20a,difference%20between%20his%20fastball%20and).
By design, they often have less spin (e.g. ~1700
rpm)[\[16\]](https://www.mlb.com/news/statcast-spin-rate-compared-to-velocity-c160896926#:~:text=Spin%20Highest%20spin%3A%202%2C421%20rpm%2C,Velocity)
and sometimes a different axis due to grip (circle-change grip can
impart slight sidespin). The reduced speed means gravity has more time
to act, so changeups drop more than fastballs. Many also exhibit
**arm-side fade**, gently tailing away from opposite-handed hitters. The
Magnus effect on a changeup is modest (some backspin lift but much less
than a fastball, and slight side force for fade). The key to a good
changeup is deception – it should look like a fastball out of hand, then
arrive slower and lower. Splitters are akin to changeups in outcome but
achieved differently: a splitter grip (ball wedged between fingers)
drastically reduces spin (often under 1500
rpm)[\[18\]](https://www.mlb.com/news/statcast-spin-rate-compared-to-velocity-c160896926#:~:text=Spin%20Highest%20spin%3A%202%2C077%20rpm%2C,4%20mph%2C%20Familia).
This makes the pitch behave almost like a knuckleball in terms of
movement – very little Magnus force, so it **drops very sharply late**.
A splitter in the mid-80s can almost emulate a slow curve’s drop, but
thrown with fastball arm action. Because of the minimal Magnus support,
splitters and changeups tend to generate weak contact (hitters roll over
or top the ball) and ground balls. In fact, pitchers like Mike Pelfrey,
whose splitter had extremely low spin (~830 rpm), found it was their
best ground-ball
pitch[\[18\]](https://www.mlb.com/news/statcast-spin-rate-compared-to-velocity-c160896926#:~:text=Spin%20Highest%20spin%3A%202%2C077%20rpm%2C,4%20mph%2C%20Familia).

**Knuckleball:** The knuckleball is a unique, rare pitch thrown with the
intent of **almost no spin** (ideally 1–3 rotations during the ball’s
flight). Without spin, the Magnus effect vanishes – instead, the ball’s
trajectory is dominated by chaotic airflow around the seams. A good
knuckler (typically ~65–75 mph) flutters unpredictably by a few inches
in various
directions[\[19\]](https://www.comsol.it/blogs/physics-behind-baseball-pitches#:~:text=The%20knuckleball%20is%20the%20most,easier%20to%20hit%20because%20the)[\[20\]](https://www.comsol.it/blogs/physics-behind-baseball-pitches#:~:text=actually%20its%20enemy,as%20seen%20in%20this%20GIF).
As the ball slips out of the fingers, the lack of rotation means the
stitches take new orientations as the ball travels, causing asymmetric
turbulence. This results in a zig-zag path that is impossible to predict
or replicate exactly. Even the pitcher doesn’t know the precise break of
a knuckleball – it might dart left, right, or drop suddenly just before
reaching the plate. In simulation, modeling a knuckleball could involve
random lateral and vertical force perturbations. Notably, if a
knuckleball spins too much (say \>500 rpm), it begins to behave like a
slow, batting-practice fastball (straight and easy to
hit)[\[27\]](https://www.comsol.it/blogs/physics-behind-baseball-pitches#:~:text=behind%20the%20ball%2C%20as%20explained,as%20seen%20in%20this%20GIF).
So maintaining that low spin is crucial for effectiveness.

## The Role of Spin and the Magnus Effect in Movement

The **Magnus effect** is the physical phenomenon that causes a spinning
ball to curve in flight. When a baseball is spinning, it pushes on the
air; the stitches and rotation create a pressure difference that yields
a force on the ball **perpendicular** to its direction of
travel[\[28\]](file://file_0000000028e86230881cd8d2f850493e#:~:text=factor,2%24%20in%20the%20upward).
In essence, the ball moves *in the direction that the front of the ball
is spinning*. This is the key to pitch movement: a ball with backspin
experiences an upward force (opposing gravity), while a ball with
topspin gets a downward force (adding to gravity). Similarly,
side-spinning balls get a sideways force that makes them break left or
right[\[29\]](https://www.reddit.com/r/ColoradoRockies/comments/31s5zy/why_is_it_so_hard_to_pitch_at_coors/#:~:text=,seen%20during%20some%20baseball%20pitches)[\[30\]](https://www.reddit.com/r/ColoradoRockies/comments/31s5zy/why_is_it_so_hard_to_pitch_at_coors/#:~:text=,rotor%20ships%20and%20Flettner%20aeroplanes).

*Illustration of the Magnus effect.* A back-spinning ball deflects the
airflow downward, producing an upward lift force on the ball (red
arrow). Topspin would do the opposite, pushing the ball downward. The
force is always perpendicular to the velocity and proportional to spin
rate[\[29\]](https://www.reddit.com/r/ColoradoRockies/comments/31s5zy/why_is_it_so_hard_to_pitch_at_coors/#:~:text=,seen%20during%20some%20baseball%20pitches)[\[31\]](https://www.reddit.com/r/ColoradoRockies/comments/31s5zy/why_is_it_so_hard_to_pitch_at_coors/#:~:text=).

In **baseball terms**: this means a fastball with **backspin** “hops” or
stays up longer than expected, a curveball with **topspin** dives more,
and a slider or cutter with **side-spin** breaks laterally. The strength
of the Magnus force increases with spin rate and with velocity (faster
pitch + faster spin = more
movement)[\[32\]](https://physics.wooster.edu/wp-content/uploads/2021/08/Junior-IS-Thesis-Web_1999_Nowicki.pdf#:~:text=,depending%20on%20the%20seams)[\[33\]](https://www.physics.sydney.edu.au/~cross/TRAJECTORIES/Trajectories.html#:~:text=ball%20trajectories%20The%20Magnus%20force,but%20CL%20depends%20on).
It also depends on the orientation of the spin axis:

- If the spin axis is perfectly **vertical** (like a pure topspin or
  pure backspin case), the Magnus force is vertical (down or up). A 12–6
  curve (topspin, vertical axis) thus has virtually only downward break.
  A pure backspin pitch (axis vertical, but ball spinning backward)
  yields only upward lift – a theoretical pure “rising” fastball.
- If the spin axis is **horizontal** (imagine the ball spinning like a
  globe on its axis), the Magnus force is horizontal. This happens with
  pure side-spin. For example, a sidespin axis (like a frisbee throw)
  can make a pitch break sideways. A classic slider often has a
  significant sidespin component, hence its glove-side sweep.
- In most real pitches, the spin axis is **tilted** somewhere in
  between. For instance, a typical four-seam fastball from an overhand
  pitcher might have an axis tilted slightly, say towards 1 o’clock (for
  a RHP). This produces mostly backspin (upward force) but a bit of
  arm-side force – yielding a fastball that both “rises” and has a tiny
  tail toward the arm side. A sinker might be tilted more forward
  (closer to 2 o’clock axis), producing more downward and arm-side
  Magnus force (hence sink and run).

The **spin efficiency** or “active spin” of a pitch is a critical
concept here. Not all the raw spin a pitcher imparts actually causes
movement – only the spin component perpendicular to the flight path
(i.e. the *useful* spin) creates Magnus
force[\[34\]](https://www.seemagnus.com/blog-posts-test/a-discussion-of-spin-efficiency#:~:text=One%20such%20discovery%20is%20that,expressed%20when%20talking%20about%20spin)[\[35\]](https://www.seemagnus.com/blog-posts-test/a-discussion-of-spin-efficiency#:~:text=induced%20movement%20on%20a%20pitch,generate%20the%20movement%20they%20feature).
A gyroball or pure bullet spin (axis parallel to flight direction) has
almost 0% active spin – it will have a high rpm but little movement (the
spin is oriented wrong to push the air sideways). Pitches like sliders
often have lower active spin percentages (30–50%), meaning a lot of the
spin is gyro spin not causing
break[\[11\]](https://www.seemagnus.com/blog-posts-test/a-discussion-of-spin-efficiency#:~:text=Pitch%20Type2020%20Mean%20MLB%20Spin,Seam%20Fastball89.8Cutter49.1Sinker89.0Changeup89.3Curveball68.7Slider35.9Values%20are%20approximate).
In contrast, a well-thrown four-seam or sinker can have \>90% active
spin (almost all of the spin is on an axis that generates lift or
dive)[\[11\]](https://www.seemagnus.com/blog-posts-test/a-discussion-of-spin-efficiency#:~:text=Pitch%20Type2020%20Mean%20MLB%20Spin,Seam%20Fastball89.8Cutter49.1Sinker89.0Changeup89.3Curveball68.7Slider35.9Values%20are%20approximate).
When designing a simulation, **spin efficiency** should modulate how
much movement a pitch gets for a given spin rate. For example, two
pitchers might both impart 2400 rpm on their slider – but if one has 80%
efficiency vs another’s 20%, the first will have dramatically more
movement (the latter might just spin like a bullet with only modest
break).

To quantify Magnus effect: the force can be modeled similarly to lift on
an airplane wing. A simple equation for the **Magnus (lift) force** is:

``` math
F_{L} = \frac{1}{2}C_{L}\,\rho\, A\, v^{2},
```

where *C\<sub\>L\</sub\>* is a lift coefficient that depends on the spin
rate and ball properties, ρ is air density, *A* is the cross-sectional
area of the ball, and *v* is the
velocity[\[36\]](file://file_0000000028e86230881cd8d2f850493e#:~:text=break%20downward%20%E2%80%93%20for%20a,2).
The direction of **F\<sub\>L\</sub\>** is perpendicular to the velocity
vector, toward the direction of spin (use right-hand rule for the
cross-product of spin axis with velocity). For a well-spun baseball,
*C\<sub\>L\>* is on the order of
0.2–0.3[\[36\]](file://file_0000000028e86230881cd8d2f850493e#:~:text=break%20downward%20%E2%80%93%20for%20a,2)
(higher with more spin until it levels off). This means a fastball at
90 mph with vigorous backspin can experience an upward force roughly 1/5
the weight of the ball, enough to reduce its drop by several inches over
the 60.5 ft of flight.

The **horizontal vs vertical break** of pitches can be understood by
decomposing that Magnus force. A “rising” fastball doesn’t actually go
up – it just falls slower. For instance, a 95 mph four-seam might drop
~15″ by the time it reaches the plate, whereas the same 95 mph ball with
no spin would drop ~20″; we say it has ~5″ of “ride” or lift. On the
other hand, a curve might drop ~30″ (an extra ~10″ more than gravity
alone) due to topspin. Horizontal break is measured similarly – e.g. a
slider might break 8″ to the side versus a hypothetical spinless
trajectory. Statcast data often reports movement as “inches of break”
compared to a reference throw without spin. A pitcher’s ability to
generate high spin with an efficient axis is what produces elite
movement numbers (e.g. \>20″ of induced vertical break on a four-seamer
is excellent).

It’s worth noting **diminishing returns** in spin: beyond a certain
point, extra spin doesn’t equal extra movement due to flow physics.
Also, very high spin can slightly increase drag (which counteracts some
benefits; more on drag below). But generally, up to moderate ranges,
more spin + good axis = more movement. For simulation, one can input
spin rate and axis per pitch and compute Magnus force each time step to
update the ball’s velocity vector (as described later in the physics
modeling section).

## Release Mechanics: Arm Angle, Release Point, and Deception

A pitcher’s **delivery mechanics** significantly influence the pitch
trajectory *even before* physics takes over in mid-flight. Key
mechanical factors include the arm slot (angle), the release height and
extension toward home plate, and any deceptive elements in the delivery.
These affect the pitch’s initial conditions (velocity vector, spin axis)
and the batter’s perception.

**Arm Angle / Slot:** Pitchers throw from varying arm slots – from
overhand (high three-quarters or straight over the top) to sidearm or
even submarine. The arm angle changes the orientation of the spin axis
and the plane of the pitch trajectory out of the hand. An overhand
pitcher tends to impart backspin/topspin in a more vertical plane. For
example, an overhand curveball gets pure topspin causing a straight
downward break (the classic 12–6 curve). A low sidearm pitcher, however,
will impart a more tilted spin – their curveball (often called a
“sweeper” or slurve) might have more sidespin, resulting in a big
horizontal sweep in addition to drop. Similarly, a sidearm or 3/4
delivery on a fastball often means the spin axis isn’t perfectly
horizontal – it might be tilted to produce some arm-side run. In short,
**higher arm slots** generally yield pitches with more vertical movement
(e.g. 12–6 curves, “rising” four-seams), while **lower arm slots** yield
more horizontal movement (e.g. frisbee sliders, sinkers that run). In a
simulation, the arm angle could be a parameter that automatically tilts
the spin axis of all pitches from that pitcher accordingly.

Arm angle also affects the **plane of delivery**. A true overhand
pitcher releases the ball closer to the centerline of the mound and high
above the ground; a sidearmer releases from way out to the side and low.
This means sidearmers present the batter with a drastically different
angle – the pitch may appear to come in from the side. Overhand pitchers
create steep “downhill” plane toward the plate. These differences can
influence outcomes: low-arm-angle pitchers tend to have more platoon
splits (their pitches sweep across the zone, very effective vs
same-handed batters but sometimes easier for opposite-handed batters to
see). High arm slots can be advantageous for getting on top of the ball
for downward action (useful for sinkers) or extreme ride on high
fastballs.

**Release Point and Extension:** The release point in space (height
above ground, horizontal position, and distance in front of the rubber)
affects both the physics of the pitch and the timing for the batter. A
pitcher with a long stride and reach (e.g. 7+ feet of **extension**)
essentially releases the ball closer to home plate. This **reduces the
flight time**, making the pitch “play faster” to the hitter. Statcast
measures this as **perceived velocity** – for each foot of extension,
the perceived velo increases by roughly
1–2 mph[\[37\]](https://www.si.com/mlb/diamondbacks/analysis/does-more-extension-yield-better-fastball-performance#:~:text=The%20graph%20shows%20not%20only,than%20its%20radar%20gun%20reading).
For example, if two pitchers both throw 95 mph, but one releases at 55
ft from home and another at 53 ft, the first gives the batter 2 fewer
feet to react – effectively “adding” ~3–4 mph in perception. Empirical
analysis confirms this: *“every additional foot of extension at release
adds ~1.7 mph to the perceived
velocity”*[\[37\]](https://www.si.com/mlb/diamondbacks/analysis/does-more-extension-yield-better-fastball-performance#:~:text=The%20graph%20shows%20not%20only,than%20its%20radar%20gun%20reading).
In simulation, one can adjust the apparent velocity or reaction time
based on extension. Beyond timing, a farther release means the ball has
slightly less distance to travel, so less time for gravity and Magnus
forces to act – slightly reducing total break. (A pitch released closer
will break a tad less by the plate simply because it’s in flight for,
say, 0.39 seconds instead of 0.41 seconds). High extension is generally
beneficial for a pitcher; there’s essentially no downside in terms of
control, and it makes the stuff “jump on” hitters more
quickly[\[38\]](https://www.si.com/mlb/diamondbacks/analysis/does-more-extension-yield-better-fastball-performance#:~:text=Earlier%20this%20month%2C%20Nick%20Piecoro,or%20at%20the%20ballpark)[\[37\]](https://www.si.com/mlb/diamondbacks/analysis/does-more-extension-yield-better-fastball-performance#:~:text=The%20graph%20shows%20not%20only,than%20its%20radar%20gun%20reading).

The **vertical release height** also influences the trajectory shape. A
very tall pitcher with an overhand delivery (say release point 6.5 ft
high) will have a sharper downward angle toward the zone, all else
equal, compared to a shorter pitcher or lower slot. This can make it
harder for a batter to square up low pitches (steeper angle into the
bat). It might also slightly increase the effective drop on pitches by
the time they cross the plate (since they started higher). A low release
(sidearm) comes in shallower, which can be advantageous for staying off
the bat plane on high pitches. These nuances can affect how certain
pitches perform; for example, a high-release curveball might drop into
the zone later, whereas a low-release slider might skim across more
horizontally.

**Deception:** Beyond pure physics, pitchers use deception in their
delivery to upset a batter’s timing and balance. This includes how well
they **hide the ball** (some pitchers turn their body such that the
batter only sees the ball at the last moment), the consistency of their
arm speed on all pitches, and the similarity of release tunnels for
different pitch types. While harder to quantify, deception can be
treated in simulation as a modifier to batter reaction or pitch
recognition. For example, a high deception rating could reduce the
batter’s ability to distinguish pitch type early, leading to more late
or incorrect swings. Real examples: pitchers like Yu Darvish are known
for “tunneling” – throwing different pitches from the same release point
and initial trajectory, so the batter can’t tell them apart until the
break occurs. Another aspect is varying timing in the delivery (quick
pitches, hesitation windups) which might not be modeled in physics but
could be an attribute affecting hitter timing.

One measurable deception factor is the **spin mirroring** or contrast
between pitches – but that’s more strategy than a mechanic. From a
mechanics perspective, think of deception as anything that makes the
pitch’s effective velocity or trajectory harder to pick up. A classic
deceptive pitcher might have a sneaky fastball that “hides” the ball (so
it seems to get on you faster), or an over-the-top curve that looks like
a fastball until it plunges downward.

In a comprehensive simulation, **release mechanics** inputs could
include: arm slot angle, release height, extension, and a deception
rating. These would influence the initial conditions (spin axis
orientation, release position) and possibly the batter’s hitting
attributes (e.g. a deception rating could make batters have a penalty on
reaction or contact for that pitcher). For example, a sidearm pitcher’s
parameters would generate more lateral Magnus force (altering pitch
movement outputs), while a high-extension pitcher’s code might reduce
batter reaction time by a few milliseconds.

## Physics-Based Trajectory Modeling (Drag & Magnus Equations)

To simulate a pitch’s flight accurately, the game engine must
incorporate the relevant forces: **gravity**, **air drag**, and **Magnus
force** (lift). The equations of motion can be integrated stepwise to
track the ball from release to plate. Below we outline the key physics
formulas and considerations:

- **Gravity:** Provides a constant downward acceleration *g* = 9.8 m/s²
  (32 ft/s²). This acts on the mass of the baseball (5.25 oz or 0.145
  kg) straight down. In a vacuum, a pitch is a simple parabola under
  gravity – but in air, drag and spin forces dominate the subtle
  movements.

- **Air Drag:** As the ball moves through air, it experiences a
  retarding force opposite to its velocity. A standard drag equation is:

``` math
**F_{d} = \frac{1}{2}C_{d}\,\rho\, A\, v^{2}**,
```

acting opposite the velocity
vector[\[39\]](file://file_0000000028e86230881cd8d2f850493e#:~:text=In%20simulation%20terms%2C%20we%20will,same%20ball%20at%20sea%20level).
Here *C\<sub\>d\</sub\>* is the drag coefficient, ρ air density, *A*
cross-sectional area (~0.0042 m² for a baseball), and *v* the speed. For
a baseball, experimental data shows *C\<sub\>d\>* ≈ 0.3–0.4 in the range
of typical pitch
speeds[\[40\]](file://file_0000000028e86230881cd8d2f850493e#:~:text=coefficient%2C%20%24,quantify%20those%20environmental%20effects%20shortly).
Drag is significant: a 95 mph fastball might lose around 8–10% of its
speed by the time it reaches the plate (it leaves the hand at 95,
arrives maybe ~86 mph due to
drag)[\[41\]](https://baseball.physics.illinois.edu/Denver.html#:~:text=commonly%20referred%20to%20as%20,plate%20at%20about%2086%20mph)[\[42\]](https://baseball.physics.illinois.edu/Denver.html#:~:text=Roughly%20speaking%2C%20a%20baseball%20loses,plate%20at%20about%2086%20mph).
We must include this deceleration for realism. Drag also has a slight
downward component if the velocity has a downward angle (this
effectively makes the ball drop a bit more than gravity alone would,
especially for sinking pitches).

In simulation, we update velocity each small timestep: *v* decreases due
to drag by an amount $`\Delta v = - \left( F_{d}/m \right)\Delta t`$ in
the direction of motion. Because *F_d* ∝ *v²*, this is nonlinear – but
small timesteps (e.g. 1 ms) can handle it. Drag is why even the hardest
straight fastball can never truly “rise” – gravity and drag combined
will ensure it falls, just a question of how much. It’s also why
pitchers at higher altitude get a slight bump: with thinner air,
*C\<sub\>d\</sub\>* effective is lower (less drag), so their pitches
hold speed better.

- **Magnus (Lift) Force:** As detailed in the spin section, the Magnus
  force is perpendicular to velocity and proportional to spin. The
  magnitude can be calculated by the lift formula given earlier:
  $`F_{L} = \frac{1}{2}C_{L}\,\rho\, A\, v^{2}`$ . *C\<sub\>L\</sub\>*
  is a **lift coefficient** that encapsulates how effectively the ball’s
  spin generates force. It depends on the spin parameter (often defined
  as $`\text{spin factor} = \frac{\omega R}{v}`$ , where ω is angular
  speed in rad/s and R ball radius). For MLB pitches, a rough range is
  *C\<sub\>L\>* ≈
  0.1–0.3[\[36\]](file://file_0000000028e86230881cd8d2f850493e#:~:text=break%20downward%20%E2%80%93%20for%20a,2).
  For example, a fast-spinning curveball might have *C\<sub\>L\>* ~0.25,
  whereas a slower spinning pitch has *C\<sub\>L\>* \<0.1. The direction
  of this force is given by the right-hand rule: if you point your right
  thumb along the spin axis (from the ball’s perspective), your curled
  fingers show the direction the ball will move. We decompose Magnus
  into vertical and horizontal components based on axis orientation.

*Example:* Suppose we have a RHP’s slider with partial side-top spin. If
the spin axis is 45° between vertical and horizontal, pointing toward
1:30 on a clock (from pitcher’s view, that’s axis tilted to arm side and
downwards a bit). This will produce a Magnus force that is 45° between
upward and horizontal – i.e. partly up (reducing drop) and partly toward
the glove side. We calculate *F\<sub\>L*\> with the above formula and
then split into components according to the axis. The simulation would
add these components to the acceleration: e.g. a +y acceleration for
upward lift, +x for horizontal break (depending on coordinate setup).

- **Trajectory Integration:** Combining forces, the acceleration of the
  ball at any instant is: **a(t) = (F\<sub\>gravity\</sub\> +
  F\<sub\>drag\</sub\> + F\<sub\>Magnus\</sub\>) / m**. Gravity is
  constant (0, -g). Drag = $`- \frac{1}{2}C_{d}\rho Av^{2}\widehat{v}`$
  (opposite velocity unit vector). Magnus =
  $`\frac{1}{2}C_{L}\rho Av^{2}\widehat{n}`$ , where $`\widehat{n}`$ is
  the unit vector perpendicular to velocity in the direction of
  spin-induced deflection. These equations typically have to be solved
  numerically, but a simple approach (Euler or 4th-order Runge-Kutta)
  with small time steps (on the order of 0.001–0.005 s) is sufficient to
  get realistic
  trajectories[\[43\]](file://file_0000000028e86230881cd8d2f850493e#:~:text=Trajectory%20computation%3A%20At%20each%20small,time)[\[44\]](file://file_0000000028e86230881cd8d2f850493e#:~:text=velocity%20and%20position,time%20in%20a%20game).
  Given today’s computing power, this can be done in real-time for a
  game.

If simulating thousands of pitches, one might also use an analytical or
precomputed lookup for pitch movement given parameters. For instance,
one could precompute how much vertical/horizontal break a pitch with X
spin and Y velocity would have after 0.4 seconds of flight. In fact,
Statcast provides “movement” numbers which essentially are outcomes of
these physics equations fitted to real data. But doing it dynamically
has the advantage of naturally handling different environmental
conditions like wind or altitude by just changing ρ (air density) or
adding a wind velocity to the relative airflow.

- **Seam Effects (Advanced):** For extreme realism, one might consider
  that the baseball’s **seams** can cause deviations beyond pure Magnus
  effect. Recent research on “seam-shifted wake” shows that certain
  pitches (like a two-seamer or cutter with specific orientations) can
  get movement that isn’t fully explained by the steady Magnus effect –
  the seams can trip turbulence asymmetrically and make the ball break
  in unusual ways. These effects are harder to model (requiring fluid
  dynamics beyond a simple coefficient). In a high-fidelity sim, one
  could incorporate an empirical adjustment for seam effects on specific
  pitches (e.g. give an extra few inches of break to a well-executed
  two-seam if thrown with a “laminar express” grip). However, for most
  simulation purposes, Magnus + drag covers the majority of pitch
  behavior.

- **Timestep & Collision:** The flight from mound to plate lasts
  ~0.4–0.5 seconds for a fastball (longer for slow pitches). With a 1 ms
  timestep, that’s ~400 steps – trivial for a computer. At each step, we
  update velocity and position. We stop when the ball reaches the front
  of home plate (or earlier if contact occurs). If simulating the
  **pitch-bat collision**, the trajectory might be interrupted earlier
  when the bat intercepts the ball. Otherwise, for a pitch that isn’t
  hit, one must check if it crosses the strike zone boundaries for a
  strike/ball call.

In summary, the physics engine will take each pitch’s initial speed,
spin rate, spin axis, and release position and then apply these
equations to produce a realistic trajectory. Calibration against known
pitch data (like ensuring a 12–6 curve with 2500 rpm actually breaks
~2–3 feet downward, etc.) can be done by tuning *C\<sub\>L\>* and
*C\<sub\>d\>* within known
ranges[\[45\]](https://baseball.physics.illinois.edu/Denver.html#:~:text=peak%20speed,A).
The end result is a pitch that slows down a bit (drag), falls due to
gravity (modulated by lift), and curves horizontally/vertically
according to spin – matching what players see on the field.

## Environmental Factors Affecting Pitches (Altitude, Weather, Wind)

**Stadium environment** plays a subtle but important role in pitch
movement and velocity. Because drag and Magnus forces depend on air
density (ρ in those formulas), any factor that changes air density will
change how much a pitch breaks and how quickly it slows
down[\[46\]](https://www.reddit.com/r/ColoradoRockies/comments/31s5zy/why_is_it_so_hard_to_pitch_at_coors/#:~:text=The%20Magnus%20Effect%20is%20the,to%20the%20density%20of%20air)[\[47\]](https://baseball.physics.illinois.edu/Denver.html#:~:text=played%20in%20a%20vacuum%20and,of%20their%20values%20at%20Fenway).
The main environmental factors are **altitude (air pressure)**,
**temperature**, **humidity**, and **wind**. A high-realism simulation
should account for these to differentiate pitching at Coors Field vs at
sea level, or a cold April game vs a hot July game.

- **Altitude (Air Density):** Higher elevations have thinner air (lower
  ρ). This reduces both drag and Magnus forces in roughly equal
  proportion[\[47\]](https://baseball.physics.illinois.edu/Denver.html#:~:text=played%20in%20a%20vacuum%20and,of%20their%20values%20at%20Fenway).
  Denver’s Coors Field (5280 ft elevation) is the extreme case – air
  density is about 82% of sea-level
  density[\[48\]](https://coloradosun.com/2023/08/22/colorado-rockies-coors-field-elevation/#:~:text=If%20you%20throw%20that%20pitch,it%20is%20at%20sea%20level)[\[49\]](https://baseball.physics.illinois.edu/Denver.html#:~:text=mean%20lower%20air%20density,of%20their%20values%20at%20Fenway).
  As a result, pitches at Coors break only ~80% as much as they would at
  sea
  level[\[45\]](https://baseball.physics.illinois.edu/Denver.html#:~:text=peak%20speed,A).
  Alan Nathan notes: if a curveball has an 18″ break in Boston, the same
  pitch would break ~15″ in Denver (about 3–4″
  less)[\[3\]](https://baseball.physics.illinois.edu/Denver.html#:~:text=average%20speed%20is%20about%2096,about%204%20inches%20less%20at).
  Similarly, a fastball that “rises” 10″ at sea level might only rise
  ~8″ at Coors, effectively dropping more by comparison (pitchers often
  say their fastball “doesn’t ride as much” up there). This is why
  breaking balls are less effective at altitude – *“your stuff
  automatically is not as good”* in thin air, as former Rockies manager
  Jim Leyland
  lamented[\[50\]](https://coloradosun.com/2023/08/22/colorado-rockies-coors-field-elevation/#:~:text=staffs%20have%20experienced%20for%20the,work%20in%20baseball%E2%80%99s%20weirdest%20funhouse).
  Empirical data from 2023 showed curveballs at Coors had on average ~2″
  less vertical and horizontal break than at other
  parks[\[51\]](https://coloradosun.com/2023/08/22/colorado-rockies-coors-field-elevation/#:~:text=about%209%20inches,it%20is%20at%20sea%20level).
  For simulation, one can input park altitude and adjust air density:
  e.g. use ρ = 1.0 kg/m³ at sea level vs 0.82 kg/m³ at Coors (at a given
  temperature) – the Magnus and drag forces computed will then naturally
  be ~18% lower. The net effect: pitches at altitude are a bit
  straighter and a bit faster (since less drag means higher retained
  velocity). Indeed, a 95 mph pitch might only lose ~8% of its speed by
  the plate at Coors vs 10% at sea
  level[\[52\]](https://baseball.physics.illinois.edu/Denver.html#:~:text=In%20light%20of%20the%20above,to%20the%20Magnus%20force%2C%20an),
  giving batters maybe ~1 mph more velocity to handle. These are subtle
  differences, but across a full game they matter. In a simulator, you’d
  see fewer big-breaking curveballs in Denver, and pitchers might rely
  more on other strategies (or break stuff a bit less).

- **Temperature:** Warm air is less dense than cold air (hot molecules
  are more spread out). A rough rule: air density decreases ~3% for
  every 10 °C (18 °F) increase in temperature (at constant pressure). So
  a hot 95 °F (35 °C) day might have air ~10% thinner than a chilly
  45 °F (7 °C) day. That’s comparable to some altitude effects. In
  practical terms, **pitches will break a bit less on hot days** and
  slightly more on cold
  days[\[53\]](https://commandtrakker.com/Weather%20and%20altitude%20effects%20on%20pitched%20and%20batted%20baseballs.html#:~:text=Higher%20Temperature%3A%20Causes%20the%20air,air%20resistance%20could%20allow%20a)[\[54\]](https://commandtrakker.com/Weather%20and%20altitude%20effects%20on%20pitched%20and%20batted%20baseballs.html#:~:text=Lower%20Temperature%3A%20Increases%20air%20density%2C,and%20the%20slide%20in%20sliders).
  One analysis noted a 10 °F increase might only shave a fraction of an
  inch off a curve’s
  break[\[55\]](https://commandtrakker.com/Weather%20and%20altitude%20effects%20on%20pitched%20and%20batted%20baseballs.html#:~:text=reduces%20air%20density%2C%20which%20in,which%20is%20responsible%20for%20the)
  – not huge, but potentially noticeable. The trade-off is that a
  fastball will also *travel faster* (less drag slowing it down) in
  warmer, thinner
  air[\[56\]](https://commandtrakker.com/Weather%20and%20altitude%20effects%20on%20pitched%20and%20batted%20baseballs.html#:~:text=designed%20to%20have%20a%20significant,the%20movement%20of%20breaking%20balls).
  Conversely, on a cold dense-air night, a curveball might snap extra
  hard (a few percent more Magnus), but the fastball will lose speed a
  tad faster. For a simulation, adjusting ρ by temperature (and
  atmospheric pressure) is the way to go. If you include a weather
  system, you could have a “cold April game” where break is exaggerated
  (and offense may be down as a result of good breaking pitches), vs a
  “scorching August” game where pitchers need to rely more on location
  since their curves/ sliders don’t move as much.

- **Humidity:** There is a common misconception that humid air is
  “heavy.” In fact, **humid air is *less dense*** than dry air at the
  same temperature and
  pressure[\[57\]](https://baseball.physics.illinois.edu/Denver.html#:~:text=By%20the%20way%2C%20another%20thing,link%20for%20a%20nice%20discussion).
  Water vapor (H₂O) has lower molecular weight than the N₂/O₂ that make
  up dry air, so adding humidity displaces some heavier molecules. The
  effect of humidity on density is relatively small in typical outdoor
  ranges – going from say 0% to 100% humidity might lower air density by
  ~1–2%. So the impact on pitches is minimal, but theoretically, higher
  humidity means very slightly less drag and Magnus. This might add a
  few tenths of an inch of difference in
  movement[\[58\]](https://commandtrakker.com/Weather%20and%20altitude%20effects%20on%20pitched%20and%20batted%20baseballs.html#:~:text=Higher%20Humidity%3A%20Adds%20moisture%20to,the%20movement%20of%20breaking%20pitches).
  In other words, a dry desert air (like Arizona before they used a
  humidor) is a bit denser than a muggy Florida air (when adjusted for
  temp). Most simulations can probably ignore humidity or include it as
  a small tweak to ρ. (MLB parks now store balls in humidors which
  affect the ball’s liveliness, but that’s another factor not related to
  flight physics.)

- **Wind:** Wind can alter pitch trajectories by changing the **relative
  air velocity** experienced by the ball. A **headwind** (wind blowing
  *in* from centerfield toward home) effectively increases the airflow
  over the ball, enhancing drag and Magnus effect. It’s like the ball is
  moving faster through the air than its speedometer reading. A pitcher
  throwing 90 mph into a 10 mph headwind experiences 100 mph worth of
  air drag on the ball. That could make a curve break a bit more (more
  air force) and also slow the pitch down slightly more by the time it
  reaches the plate. A **tailwind** does the opposite: reduces relative
  velocity (90 mph pitch with 10 mph tailwind feels like 80 mph to the
  air), cutting drag and Magnus. The pitch will not break as much and
  will arrive faster. Crosswinds can also push a pitch laterally –
  essentially adding a constant sideways force. A 10 mph crosswind, if
  fully perpendicular, during ~0.4 s of flight might nudge a ball a few
  inches off course. In the real world this is rarely noticeable except
  in extreme gusts, but it can make the difference between a pitch
  catching the corner or sailing off the plate. For a high-end sim, one
  can model wind by simply adding the wind vector (negative) to the
  ball’s velocity when computing drag/Magnus
  forces[\[59\]](file://file_0000000028e86230881cd8d2f850493e#:~:text=But%20including%20wind%20adds%20a,out%20on%20a%20calm%20day)[\[60\]](file://file_0000000028e86230881cd8d2f850493e#:~:text=In%20practical%20terms%2C%20our%20module,5%20mph%20of%20tailwind%20%E2%89%88).
  For example, if wind is blowing towards right field at 5 mph, you
  subtract that from the ball’s velocity in the horizontal direction
  when calculating forces – effectively the ball feels like it has a
  5 mph sideways component pushing it. Wind can thus be an input to the
  physics engine. Fans know that Wrigley Field with a howling in-blowing
  wind can make even fastballs feel “heavy” with extra drop, whereas
  with wind out, everything carries (though that affects batted balls
  more than pitches).

In summary, **denser air = more movement, but more drag**; **thin air =
less movement, but pitches retain speed**. These environmental impacts
can be on the order of a few inches of break or a couple mph of velo
difference, which at the elite level is significant. A robust simulation
could allow park factors or weather settings to alter a global air
density parameter and wind vector, so that each pitch’s physics are
computed accordingly. This would recreate the “Coors Field effect” where
breaking balls don’t bite as much and high pitches are more dangerous,
versus a place like San Francisco on a cool, humid night where pitchers
get a little extra snap on their breaking stuff.

## Influence on Batter Outcomes and In-Game Results

All the detailed pitch attributes – velocity, movement, spin, release –
ultimately matter because of how they influence the **batter’s success
or failure**. In a simulation, we need to translate pitch physics into
probabilities of outcomes: swing-and-miss, weak contact, solid contact,
grounder vs fly, etc. Real-world data and baseball theory suggest
several key links between pitch characteristics and batter results:

- **Velocity:** Faster pitches give the batter less time to react,
  generally leading to more swings and misses or poor contact if the
  hitter is late. Each extra mph of velocity has value – for example,
  increasing a fastball from 92 to 95 mph tends to increase strikeout
  rates. However, velocity alone isn’t everything (hitters can time even
  100 mph if it’s straight). In simulation, a higher velocity should
  correspond to a higher chance of the batter being late (and thus
  missing or fouling off). But pairing velocity with movement is what
  really generates **“stuff.”**

- **Spin and “Rise” on Fastballs:** High-spin fastballs up in the zone
  are notoriously effective at getting swinging strikes. Because the
  backspin fastball drops less, hitters often **swing under** it,
  thinking it will be lower than it
  is[\[61\]](https://www.drivelinebaseball.com/2019/01/deeper-dive-fastball-spin-rate/?srsltid=AfmBOoooDHa4PfQDYwImU_EhOdPJCeFjotAgpzgWQ7Gn_r_GmKwf1wsr#:~:text=Now%20the%20fastest%20spin%20rate,spin%20fastballs%20on%20the%20ground).
  A study showed that when holding velocity constant, fastballs with ~+1
  inch more vertical movement and ~50 rpm more spin had higher
  swing-and-miss
  rates[\[62\]](https://sites.northwestern.edu/nusportsanalytics/2019/06/30/theres-more-to-a-good-fastball-than-just-being-fast/#:~:text=The%20most%20interesting%20data%20from,can%20be%20seen%20by%20the).
  In fact, one analysis found that swinging strikes on fastballs were
  associated with about 0.36 mph more velocity **and** 54 rpm higher
  spin (about 1″ extra lift) compared to fastballs put in
  play[\[63\]](https://sites.northwestern.edu/nusportsanalytics/2019/06/30/theres-more-to-a-good-fastball-than-just-being-fast/#:~:text=Swinging%20strikes%2092,13)[\[62\]](https://sites.northwestern.edu/nusportsanalytics/2019/06/30/theres-more-to-a-good-fastball-than-just-being-fast/#:~:text=The%20most%20interesting%20data%20from,can%20be%20seen%20by%20the).
  This corroborates the idea that a “riding” fastball is hard to hit. In
  game terms, a pitcher with an elite high-spin four-seam can yield more
  strikeouts and pop-ups (when hitters do connect, they often get under
  it, resulting in harmless fly balls). Conversely, a low-spin fastball
  tends to get contacted more and often driven down (more line drives or
  grounders). So, we might implement that a high spin rate gives a bonus
  to whiff probability, especially if thrown in the upper part of the
  zone.

- **Vertical vs Horizontal Movement (Breaking Balls):** Different
  movement profiles yield different typical outcomes. A **12–6
  curveball** (pure topspin, big drop) is great for swings-and-misses if
  located low – batters often swing over it as it dips below the barrel.
  Those that do make contact may drive it into the ground (hence
  curveballs often have high ground-ball rates when located well). A
  **sweeping slider** (big horizontal break) is effective at getting
  chase swings off the plate – a righty’s slider breaking away from a
  right-handed batter can make them whiff or at best hit a cue-shot weak
  grounder. Sliders generally have high whiff rates on chase swings and
  tend to produce weaker pulled contact when put in play (since the bat
  often doesn’t square up the moving ball). If a batter does square up a
  hanging slider (one that didn’t break as much or was left in the
  middle), it can be hit hard, but that’s a mistake by the pitcher. In
  simulation, one could tie horizontal break to **miss-hit probability**
  – e.g. more lateral movement increases the chance of off-the-end or
  off-the-hands contact, resulting in weak hits.

- **Spin Axis Consistency and Tunneling:** If a pitcher can make
  multiple pitches look the same out of hand (similar release point and
  initial trajectory) but then diverge due to spin differences, it’s
  harder for the batter to adjust. For example, an 95 mph high-spin
  fastball and an 85 mph curve might come out on the same line for the
  first 30 feet before the curve dives. This **tunneling** effect means
  the batter might commit to a swing expecting the fastball, only for
  the curve to drop under the bat. In outcomes, this shows up as more
  **chase swings** and whiffs. Some advanced metrics like “Shadow Zone”
  and “chase rate” can be linked to deception/tunneling. In practical
  terms, a pitcher with good tunneling (deception attribute) might force
  more bad swings (or called strikes, since batter gives up on pitch
  thinking it’s a ball).

- **Command and Location:** It’s not just the physics of the pitch
  itself, but where it’s located. A perfectly located low-and-away
  slider is likely to induce a flail and a miss or weak grounder. The
  same slider hung over the heart might be crushed. So a pitcher’s
  **command rating** will interplay with these physics: high movement
  pitches need to be harnessed. In simulation, we’d modulate outcome
  probabilities by whether the pitch ended up in a good location (this
  comes from the command vs error in aim). Good command + nasty movement
  yields strikeouts and weak contact. Poor command, even with great
  stuff, can result in walks (if the pitcher tries to nibble and misses)
  or meatballs (if they miss over the plate).

- **Ground Balls vs Fly Balls:** As a rule of thumb, pitches that drop
  more (e.g. sinkers, splitters, low curves) tend to produce more ground
  balls if contact is made, because batters hit the top of the ball. A
  sinking two-seam or splitter often results in batters rolling over the
  pitch, generating grounders or at best low line drives. Indeed,
  pitchers known for sinkers usually have high GB%. For example, Dallas
  Keuchel in his prime had a heavy sinker that batters pounded into the
  ground. In contrast, high-riding four-seamers up in the zone encourage
  batters to swing under, leading to **fly balls and pop-ups** (or
  whiffs)[\[61\]](https://www.drivelinebaseball.com/2019/01/deeper-dive-fastball-spin-rate/?srsltid=AfmBOoooDHa4PfQDYwImU_EhOdPJCeFjotAgpzgWQ7Gn_r_GmKwf1wsr#:~:text=Now%20the%20fastest%20spin%20rate,spin%20fastballs%20on%20the%20ground).
  Neither is inherently “better” – grounders are often outs but can
  sneak through for singles; fly balls can be outs or extra-base hits if
  squared. But for simulation, you’d use pitch movement and location to
  influence the type of contact: a downward-breaking pitch low in zone
  -\> increased grounder probability; an “up-shoot” fastball up in zone
  -\> increased pop-up or shallow fly probability (and strikeouts if
  they miss).

- **Whiff vs Contact:** Pitches with **greater deviation from a straight
  line** (either vertically, horizontally, or both) have higher miss
  rates because the bat has a harder time intersecting their path. For
  instance, a study of fastballs found that those with higher vertical
  movement (more “hop”) had higher swinging strike
  percentages[\[62\]](https://sites.northwestern.edu/nusportsanalytics/2019/06/30/theres-more-to-a-good-fastball-than-just-being-fast/#:~:text=The%20most%20interesting%20data%20from,can%20be%20seen%20by%20the).
  Similarly, a slider that moves 8″ horizontally is tougher to hit than
  one that moves 2″. The extreme is the knuckleball – its
  unpredictability yields lots of misses *when it’s on*, but also lots
  of walks if it’s too wild. In simulation, each pitch could have a
  baseline “whiff probability” tied to its movement and velocity. High
  velocity + high movement = high whiff%. Slow, flat pitches = low
  whiff% (easy to track and hit). Of course, contextual factors like
  count (pitcher ahead vs behind) and batter skill matter too.

- **Quality of Contact:** Movement also tends to affect how **hard** the
  ball is hit when contact is made. A well-located slider might be hit,
  but likely not on the sweet spot, resulting in a weak grounder or a
  floater. In Statcast terms, a good pitch yields a low exit velocity or
  a poor launch angle (e.g., topped into the ground or gotten under for
  a high pop). You can integrate this by reducing the batter’s expected
  exit velo based on pitch quality – e.g. give a penalty to exit velo if
  the pitch had x inches of unexpected break or was located on the
  edges. This way, even when contact happens against a nasty pitch, it’s
  often “weak contact.” Many simulations use a “weak/medium/hard
  contact” tier that can be influenced by pitch attributes. For example,
  **sinkers and cutters in on the hands** often result in jammed, weak
  contact; changeups can cause off-balance, soft contact if the batter
  is out in front.

As evidence of these effects, consider MLB metrics: A high-spin
four-seam fastball up in the zone produces a lot of swinging strikes and
fly-ball
outs[\[61\]](https://www.drivelinebaseball.com/2019/01/deeper-dive-fastball-spin-rate/?srsltid=AfmBOoooDHa4PfQDYwImU_EhOdPJCeFjotAgpzgWQ7Gn_r_GmKwf1wsr#:~:text=Now%20the%20fastest%20spin%20rate,spin%20fastballs%20on%20the%20ground).
A low-spin sinker produces fewer whiffs but lots of ground
balls[\[6\]](https://www.mlb.com/news/statcast-spin-rate-compared-to-velocity-c160896926#:~:text=MLB%20average%3A%202%2C123%20rpm%20Lowest,Velocity).
A great curveball (e.g. Kershaw’s) gets both strikeouts (when chased or
dropped in for called strikes) and ground outs (when contact is made).
On the flip side, a poorly thrown breaking ball (low spin or flat axis)
might not break enough and gets hit hard. Thus, the **modeled attributes
directly drive in-game results**: velocity and spin drive strikeouts vs
contact; movement and location drive grounders vs fly balls and barrels
vs weak hits.

**In the simulation engine**, one could proceed as follows after
computing the pitch trajectory: determine if the pitch is a strike or
ball (based on where it crosses the zone). If the batter swings,
determine contact or miss probability using a function of pitch
velocity, movement, and deception versus the batter’s skill. If contact,
determine if it’s hit squarely or not – influenced by how late the swing
is (velocity + deception cause lateness) and how well the bat’s path
matched the pitch break (movement + command locating away from sweet
spot cause mishits). Then decide ground vs fly by the pitch’s
spin-induced axis (e.g. topspin pitches likely cause grounders if
contact, backspin/up in zone likely cause flies). This kind of logic,
backed by data distributions, will yield realistic outcomes: e.g., a
pitcher with an “A+” 97 mph riding fastball and “A” command might
generate a high strikeout rate and a lot of pop-ups, whereas a pitcher
with a “B” 90 mph sinker but “A+” command might not K many but will get
tons of grounders and weak contact if he hits his spots.

## Parameterizing Pitchers via Attribute Ratings

To integrate all the above into a user-friendly baseball simulation, we
can assign each pitcher a set of **attribute ratings** that feed into
the physics model and outcome algorithms. These ratings distill the
physical and skill-based traits of a pitcher. Below are recommended
attributes and how they influence the pitch outputs:

- **Velocity (Power):** This rating governs how hard the pitcher throws.
  It can be tied to a fastball speed (e.g. a 0–100 scale mapping to a
  fastball MPH, or separate ratings per pitch type). A high velocity
  rating means the pitcher’s fastball averages very high (upper 90s),
  and their other pitches scale accordingly (e.g. a changeup ~10 mph
  lower than the fastball). Velocity rating directly feeds the initial
  speed of the pitch in the physics engine. It also indirectly
  influences outcomes by reducing batter reaction time and increasing
  strikeout potential. In many games, this is called “Speed” or just
  reflected in the individual pitch velocity.

- **Spin & Movement (Break):** We can have a **Spin Rate** or
  **Movement** rating that reflects the pitcher’s ability to impart spin
  and have their pitches move. This might be a single rating that is
  then applied differently for different pitch types (e.g. an “80”
  movement pitcher might have an elite riding fastball and a
  big-breaking curve). Alternatively, one can assign a separate movement
  rating per pitch (some games do list each pitch with a grade for
  velocity, control, movement). If simplifying to one attribute, it
  encapsulates how above-average the pitcher’s Magnus effect is – higher
  means more inches of break across their pitches. For example, a
  pitcher with a high movement attribute might get +3 inches more break
  on their curve than average, or a much higher active spin percentage
  on their fastball (hence more “ride”). This rating would modify the
  spin rate or *C\<sub\>L\</sub\>* used in the physics model. It could
  also encompass **Spin Efficiency** – pitchers with great movement
  often have not just raw rpm but also a clean axis. A specific approach
  is to have both **Spin Rate** and **Spin Efficiency** stats: e.g. one
  pitcher might have 2500 rpm (high) but only 70% efficiency on his
  slider, versus another with 2200 rpm but 95% efficiency – the latter
  might actually move more. For simplicity, an aggregate movement rating
  can implicitly cover both (or you can bury the details and just use it
  to compute net break).

- **Command (Control):** This rating determines how well the pitcher can
  locate pitches. In the engine, it would translate to variance in the
  target vs actual outcome of the pitch. A high command pitcher will hit
  the catcher’s target more often, enabling them to paint corners and
  avoid hanging pitches. This doesn’t directly enter the physics of
  flight, but it’s crucial for outcomes – it affects walk rates and how
  often a mistake pitch is left over the plate. Good command paired with
  high movement is deadly (pitches break but still nip the edges of the
  zone). Poor command means even if a pitch has great movement, the
  pitcher may not harness it (leading to more balls or meaty pitches).
  Many sims use separate **Control** ratings per pitch (since a pitcher
  might locate his fastball better than his curve, etc.), which is even
  more granular.

- **Pitch Arsenal & Individual Pitch Ratings:** It’s often practical to
  treat each pitch type a pitcher throws as having its own ratings. For
  example: a pitcher’s **Fastball (93 mph, 60 grade movement, 55
  control)**, **Slider (85 mph, 65 movement, 50 control)**, **Changeup
  (83 mph, 50 movement, 60 control)**, etc. These can be derived from
  the base attributes plus pitch-specific modifiers. For instance, a
  pitcher might have a global velocity of 95 mph (which sets his
  fastball ~95, slider 85, change 83), a movement of 60 (above average –
  applied to all, but maybe sliders inherently have a boost, changeups
  inherently have slightly less due to physics), and then control per
  pitch. This level of detail ensures the simulator knows exactly how
  each pitch will behave.

- **Deception (Hide/Tunnel):** We propose a deception or “release”
  rating that influences how hard it is for batters to pick up the
  pitch. This could modify the effective reaction time for the batter
  (similar to extension’s effect) or reduce the batter’s contact
  quality. For example, a high deception rating could mean the pitcher
  has an identical delivery for all pitches and hides the ball well – so
  batters get a penalty on recognizing the pitch type, increasing chase
  swings and misses. In the game engine, this might increase the
  probability of a swinging strike on what would otherwise be a contact,
  or increase the batter’s timing variance (leading to more weak
  contact). Deception is somewhat intangible, but very real – pitchers
  like Tyler Glasnow, who has a 7+ ft extension and a long stride,
  appear to “explode” the ball on hitters (high perceived velocity and
  hard-to-see
  release)[\[64\]](https://www.reddit.com/r/baseball/comments/1cag8mi/tyler_glasnow_has_a_99th_percentile_extension_75/#:~:text=Tyler%20Glasnow%20has%20a%2099th,Analysis)[\[65\]](https://www.si.com/mlb/diamondbacks/analysis/does-more-extension-yield-better-fastball-performance#:~:text=Does%20More%20Extension%20Yield%20Better,reading%20of%20a%20pitcher%27s%20fastball).
  That could be captured by a combined **Extension/Deception** stat.
  Alternatively, extension could be tied to velocity rating (since it
  effectively boosts perceived velo), and deception as an independent
  skill.

- **Stamina and Consistency:** While not explicitly asked, in a broader
  sim one would also have stamina (how long they can maintain velocity
  and command) and maybe a “pitchability” or intelligence factor (how
  well they sequence pitches). These influence how attributes might
  change over a game or how AI chooses pitches. But as far as pitch
  dynamics, they’re secondary.

- **Derived “Stuff” Metric:** Some systems (like MLB’s scouting or
  Statcast’s “Stuff+”) effectively combine velocity and movement into
  one metric. For instance, **Stuff** could be a rating that
  encapsulates how hard and nasty the pitcher’s repertoire is. A
  simulation might internally calculate this but it’s basically a result
  of the above attributes. For users, it might be useful to see an
  aggregate (like Overall rating), but under the hood, it’s better to
  keep velocity and movement separate because they affect different
  things (timing vs location of contact etc.).

**How attributes influence simulation:** The workflow would be: a
pitcher’s attributes set the parameters for each pitch thrown – initial
speed (from velocity & pitch type), spin rate and axis (from movement
attribute and pitch type, plus maybe platoon of arm angle attribute),
and precision of aiming (from command). Then the physics engine
simulates the pitch flight. Then the batter’s interaction (timing,
contact) is influenced by those resulting pitch characteristics and
perhaps directly by deception/ext. For example, if a pitcher has 95
velocity and 70 movement, his fastball might come in at 96 mph with 2400
rpm backspin and an axis that yields 18″ of lift and 7″ run. The
batter’s likelihood to miss could be calculated by a function that takes
into account the 96 mph (fast), 18″ lift (unusual – likely a whiff if
swinging under), and deception (maybe he also has a long arm action that
hides the ball). If the batter does hit it, the 18″ lift means it was
likely hit under for a fly or pop-up. Meanwhile, suppose the same
pitcher’s changeup: velocity attribute gives it ~86 mph, movement
attribute might give it say 1700 rpm with slight arm-side spin,
resulting in say 2,300 rpm of total spin but much of it inactive
(because changeups often have some sidespin), net maybe 8″ drop and 6″
fade. The deception and velocity differential might fool the batter into
swinging early and over it, yielding a weak grounder or whiff. All these
probabilities can be tweaked to realistic values by benchmarking against
real pitch stats (like whiff% for each pitch type at certain
velocity/movement combos).

In a simpler rating system (if the game doesn’t simulate every physics
detail), one could use the attributes in lookup tables. For instance, a
pitcher with 95 mph (A grade), 60 movement (B grade), and 50 control (C)
might get a pre-set outcome distribution for each pitch (e.g. 15% whiff,
50% ball in play weak, 20% ball in play hard, 15% ball/looking, etc.),
modified by batter attributes. But given this project aims for high
realism, leaning into the physics as the core and then mapping to
outcomes via physics is preferable.

**Summary of Recommended Attributes:**

- **Velocity:** influences pitch speed (and thus batter timing).
- **Spin/Movement:** influences pitch break (Magnus force) – could be
  split into Spin Rate and Spin Efficiency if detailed.
- **Command:** influences accuracy of pitch placement.
- **Deception/Extension:** influences perceived velocity and batter’s
  ability to read the pitch.
- **Each Pitch’s Ratings:** velocity offset, movement, control for that
  pitch type (since many pitchers have one pitch that’s standout and
  others that are average).

Using these, the simulation can create a pitcher profile. For example:

> *Pitcher A:* 98 mph heater (Velocity 90/100), high spin (Movement 80)
> four-seam with 100% spin efficiency, but mediocre command (50) and
> average deception (50). In game, he’ll throw very hard with huge
> “rise” – lots of strikeouts, but if he misses location, he can be
> hittable (mistakes might go a long way because they’re straight and
> over the plate).
>
> *Pitcher B:* 91 mph sinkerballer (Velocity 60), Movement 75 (he has
> great sink), Command 80, Deception 40 (a bit easy to pick up). He will
> top out lower on the radar gun, but his sinker has heavy drop and run.
> He spots it well at the knees. Hitters will rarely square him up –
> lots of grounders and weak contact – but he won’t get a ton of
> swinging strikes. If his command falters, he doesn’t have velocity to
> blow it by hitters, but with command he can induce easy outs.
>
> *Pitcher C:* Nasty slider specialist – maybe a reliever with Velocity
> 70 (95 mph FB), Movement 90 (slider and curve with elite break),
> Command 50, Deception 70. His slider might have 15″ sweep at 87 mph,
> causing a very high whiff rate, especially since he hides the ball
> well. However, with average command he might throw some wild pitches
> or fall behind in counts on occasion.

Such archetypes show how attribute combos lead to distinct styles, which
is what we see in MLB.

Empirically, these attributes correlate with results: high velocity and
spin correlate with
strikeouts[\[62\]](https://sites.northwestern.edu/nusportsanalytics/2019/06/30/theres-more-to-a-good-fastball-than-just-being-fast/#:~:text=The%20most%20interesting%20data%20from,can%20be%20seen%20by%20the);
high movement (especially sink) correlates with ground ball
rate[\[6\]](https://www.mlb.com/news/statcast-spin-rate-compared-to-velocity-c160896926#:~:text=MLB%20average%3A%202%2C123%20rpm%20Lowest,Velocity);
high command correlates with low walk rate and fewer homer mistakes. By
basing the sim on these and validating against Statcast data (like
whiff%, GB%, etc. for given pitch profiles), we ensure the game engine
produces believable outcomes.

**In conclusion**, by breaking down pitches via velocity, spin axis,
spin rate, and movement, applying physics (Magnus and drag) to their
trajectory, and accounting for human factors (release mechanics and
deception), we can simulate pitches with high fidelity. The
environmental model further grounds it in reality (a curve in Coors
really won’t break as much). Finally, mapping these pitch dynamics to
batter-pitch outcomes through attribute-driven probabilities will let
the broader simulation reflect the cat-and-mouse game of baseball: the
power pitcher racking up Ks and fly outs, the finesse sinkerballer
getting two-hop grounders, and everything in between – all based on
fundamental physics and realistic data.

**Sources:**

1.  Lindbergh, Ben. *“Statcast spin rate compared to velocity.”*
    MLB.com (2016) – Average pitch velocities and spin rates for
    different pitch
    types[\[1\]](https://www.mlb.com/news/statcast-spin-rate-compared-to-velocity-c160896926#:~:text=Velocity%20Highest%20velo%3A%2099,knuckler)[\[66\]](https://www.mlb.com/news/statcast-spin-rate-compared-to-velocity-c160896926#:~:text=Spin%20Highest%20spin%3A%202%2C654%20rpm%2C,6%20mph),
    demonstrating how sliders have less spin than curves, etc., and
    noting high-spin fastballs stay up while high-spin curves
    dive[\[14\]](https://www.mlb.com/news/statcast-spin-rate-compared-to-velocity-c160896926#:~:text=Curves%20are%20thrown%20slowly%2C%20generally,spin%3A%201%2C302%20rpm%2C%20Logan%20Kensing).
2.  Driveline Baseball. *“A Deeper Dive into Fastball Spin
    Rate.”* (2019) – Research showing hitters swing under high-spin
    fastballs (more whiffs and fly
    balls)[\[61\]](https://www.drivelinebaseball.com/2019/01/deeper-dive-fastball-spin-rate/?srsltid=AfmBOoooDHa4PfQDYwImU_EhOdPJCeFjotAgpzgWQ7Gn_r_GmKwf1wsr#:~:text=Now%20the%20fastest%20spin%20rate,spin%20fastballs%20on%20the%20ground)
    and that low-spin fastballs are hit on the ground more. Emphasizes
    importance of spin axis alignment for
    movement[\[67\]](https://www.drivelinebaseball.com/2019/01/deeper-dive-fastball-spin-rate/?srsltid=AfmBOoooDHa4PfQDYwImU_EhOdPJCeFjotAgpzgWQ7Gn_r_GmKwf1wsr#:~:text=There%20is%20a%20distinction%20between,because%20of%20the%20ball%E2%80%99s%20axis).
3.  Nathan, Alan M. *“Baseball at High Altitude.”* (2007) – Physics
    analysis of Coors Field effect: air density ~82% at 5280 ft,
    resulting in ~18% reduction in Magnus and drag
    forces[\[47\]](https://baseball.physics.illinois.edu/Denver.html#:~:text=played%20in%20a%20vacuum%20and,of%20their%20values%20at%20Fenway).
    Notes an 18″ break at sea level becomes ~15″ at Coors (e.g.
    curveball drops ~4″
    less)[\[3\]](https://baseball.physics.illinois.edu/Denver.html#:~:text=average%20speed%20is%20about%2096,about%204%20inches%20less%20at),
    and fastballs lose slightly less speed (1 mph
    difference)[\[52\]](https://baseball.physics.illinois.edu/Denver.html#:~:text=In%20light%20of%20the%20above,to%20the%20Magnus%20force%2C%20an).
    Also clarifies humid air is less dense than dry
    air[\[57\]](https://baseball.physics.illinois.edu/Denver.html#:~:text=By%20the%20way%2C%20another%20thing,link%20for%20a%20nice%20discussion).
4.  Colorado Sun – Ingold, John. *“Are the Rockies bad because they’re
    too high? Elevation affects baseball.”* (2023) – Example that an
    average curveball drops ~9.5″ at sea level but only ~7″ at Coors
    (~25%
    less)[\[48\]](https://coloradosun.com/2023/08/22/colorado-rockies-coors-field-elevation/#:~:text=If%20you%20throw%20that%20pitch,it%20is%20at%20sea%20level),
    turning a would-be strike into a meatball. Confirms real-world
    frustrations of pitchers at altitude.
5.  Statcast via Northwestern Univ. analysis (Wyatt, 2019) – Data from
    2018 showing fastballs that got swinging strikes were ~0.36 mph
    faster and had ~1″ more vertical movement (54 rpm more spin) than
    those put in
    play[\[63\]](https://sites.northwestern.edu/nusportsanalytics/2019/06/30/theres-more-to-a-good-fastball-than-just-being-fast/#:~:text=Swinging%20strikes%2092,13)[\[62\]](https://sites.northwestern.edu/nusportsanalytics/2019/06/30/theres-more-to-a-good-fastball-than-just-being-fast/#:~:text=The%20most%20interesting%20data%20from,can%20be%20seen%20by%20the).
    Supports the link between velocity/spin and whiffs.
6.  Sports Illustrated – McDermott, Michael. *“Does More Extension Yield
    Better Fastball Performance?”* (2023) – Found that each additional
    foot of release extension adds ~1.7 mph to perceived
    velocity[\[37\]](https://www.si.com/mlb/diamondbacks/analysis/does-more-extension-yield-better-fastball-performance#:~:text=The%20graph%20shows%20not%20only,than%20its%20radar%20gun%20reading),
    validating that extension makes pitches “play up.” Also notes that
    beyond velocity, spin rate, spin axis, and active spin are key to a
    fastball’s
    success[\[68\]](https://www.si.com/mlb/diamondbacks/analysis/does-more-extension-yield-better-fastball-performance#:~:text=With%20an%20r,be%20at%20getting%20hitters%20out).
7.  YakkerTech (SeeMagnus blog). *“A Discussion of Spin
    Efficiency.”* (2025) – Provides average MLB spin efficiency by
    pitch: ~90% for four-seam, ~35% for slider,
    etc.[\[11\]](https://www.seemagnus.com/blog-posts-test/a-discussion-of-spin-efficiency#:~:text=Pitch%20Type2020%20Mean%20MLB%20Spin,Seam%20Fastball89.8Cutter49.1Sinker89.0Changeup89.3Curveball68.7Slider35.9Values%20are%20approximate).
    Explains that not all spin leads to movement (gyro vs true spin) and
    gives real pitcher example (Luis Castillo’s gyro slider ~14%
    efficient yet effective via
    tunneling)[\[69\]](https://www.seemagnus.com/blog-posts-test/a-discussion-of-spin-efficiency#:~:text=https%3A%2F%2Ftwitter)[\[70\]](https://www.seemagnus.com/blog-posts-test/a-discussion-of-spin-efficiency#:~:text=Though%20his%20slider%20spins%20at,was%20because%20of%20how%20well).
    Highlights that optimal efficiency depends on pitch type and usage,
    relevant for designing pitch-specific movement in sim.
8.  Command Trakker. *“Weather and altitude effects on pitched
    baseballs.”* – Confirms higher temperature = less dense air (less
    break)[\[53\]](https://commandtrakker.com/Weather%20and%20altitude%20effects%20on%20pitched%20and%20batted%20baseballs.html#:~:text=Higher%20Temperature%3A%20Causes%20the%20air,air%20resistance%20could%20allow%20a),
    lower temperature = more
    break[\[54\]](https://commandtrakker.com/Weather%20and%20altitude%20effects%20on%20pitched%20and%20batted%20baseballs.html#:~:text=Lower%20Temperature%3A%20Increases%20air%20density%2C,and%20the%20slide%20in%20sliders);
    also notes headwinds vs tailwinds effect on Magnus (headwind
    increases
    movement)[\[71\]](https://commandtrakker.com/Weather%20and%20altitude%20effects%20on%20pitched%20and%20batted%20baseballs.html#:~:text=Can%20directly%20impact%20the%20flight,by%20decreasing%20the%20relative%20velocity).
    Quantifies barometric pressure/altitude: ~1″ less break per 1000 ft
    elevation[\[72\]](https://commandtrakker.com/Weather%20and%20altitude%20effects%20on%20pitched%20and%20batted%20baseballs.html#:~:text=Higher%20altitudes%20have%20thinner%20air%2C,venues%20like%20Denver%27s%20Coors%20Field)
    (in line with Alan Nathan’s 4″ at 5000 ft). Good general reference
    on weather impacts.
9.  COMSOL Blog – Griesmer, Andrew. *“The Physics Behind Baseball
    Pitches.”* (2014) – Conceptual descriptions of how different pitches
    use Magnus: fastballs backspin (illusion of
    rise)[\[73\]](https://www.comsol.it/blogs/physics-behind-baseball-pitches#:~:text=Fastballs%20are%20the%20easiest%20pitches,to%20change%20their%20position%20drastically),
    curveballs topspin (break
    down)[\[74\]](https://www.comsol.it/blogs/physics-behind-baseball-pitches#:~:text=),
    sliders side-spin (lateral
    break)[\[75\]](https://www.comsol.it/blogs/physics-behind-baseball-pitches#:~:text=A%20slider%20is%20thrown%20with,down%2C%20without%20any%20lateral%20movement),
    screwballs
    reverse-break[\[75\]](https://www.comsol.it/blogs/physics-behind-baseball-pitches#:~:text=A%20slider%20is%20thrown%20with,down%2C%20without%20any%20lateral%20movement),
    and knuckleballs rely on Karman vortex street (chaotic
    flutter)[\[19\]](https://www.comsol.it/blogs/physics-behind-baseball-pitches#:~:text=The%20knuckleball%20is%20the%20most,easier%20to%20hit%20because%20the).
    Useful for understanding the spin axis direction effects
    qualitatively.
10. MLB Statcast data (via Mike Petriello, 2015) – Detailed pitch stats:
    e.g. MLB avg 4-seam spin ~2226 rpm, 2-seam ~2123, curve ~2308, etc.,
    with notes on
    extremes[\[2\]](https://www.mlb.com/news/statcast-spin-rate-compared-to-velocity-c160896926#:~:text=Spin%20Highest%20spin%3A%202%2C553%20rpm%2C,than%20Stephen%20Strasburg%20or%20Jose)[\[13\]](https://www.mlb.com/news/statcast-spin-rate-compared-to-velocity-c160896926#:~:text=Spin%20Highest%20spin%3A%203%2C086%20rpm%2C,Velocity).
    Emphasizes that high spin is good for rise on
    fastballs[\[76\]](https://www.mlb.com/news/statcast-spin-rate-compared-to-velocity-c160896926#:~:text=With%20the%2040,0%20mph%2C%20Mark%20Buehrle)
    but for sinkers you want lower spin (so they drop
    more)[\[77\]](https://www.mlb.com/news/statcast-spin-rate-compared-to-velocity-c160896926#:~:text=MLB%20average%3A%202%2C123%20rpm%20Lowest,grounder%20rate%20of%20that%20group).
    This informs our typical values in the pitch table.

Each of these sources supports elements of the model, ensuring that our
simulation is grounded in real measurements and physics, creating a
nuanced and believable baseball pitching
experience.[\[1\]](https://www.mlb.com/news/statcast-spin-rate-compared-to-velocity-c160896926#:~:text=Velocity%20Highest%20velo%3A%2099,knuckler)[\[3\]](https://baseball.physics.illinois.edu/Denver.html#:~:text=average%20speed%20is%20about%2096,about%204%20inches%20less%20at)

------------------------------------------------------------------------

[\[1\]](https://www.mlb.com/news/statcast-spin-rate-compared-to-velocity-c160896926#:~:text=Velocity%20Highest%20velo%3A%2099,knuckler)
[\[2\]](https://www.mlb.com/news/statcast-spin-rate-compared-to-velocity-c160896926#:~:text=Spin%20Highest%20spin%3A%202%2C553%20rpm%2C,than%20Stephen%20Strasburg%20or%20Jose)
[\[4\]](https://www.mlb.com/news/statcast-spin-rate-compared-to-velocity-c160896926#:~:text=Velocity%20Highest%20velo%3A%2098,CUT%20FASTBALL)
[\[5\]](https://www.mlb.com/news/statcast-spin-rate-compared-to-velocity-c160896926#:~:text=Spin%20Highest%20spin%3A%202%2C484%20rpm,1%2C763%20rpm%29%20had%20the)
[\[6\]](https://www.mlb.com/news/statcast-spin-rate-compared-to-velocity-c160896926#:~:text=MLB%20average%3A%202%2C123%20rpm%20Lowest,Velocity)
[\[7\]](https://www.mlb.com/news/statcast-spin-rate-compared-to-velocity-c160896926#:~:text=Velocity%20Highest%20velo%3A%2095,5%20mph)
[\[8\]](https://www.mlb.com/news/statcast-spin-rate-compared-to-velocity-c160896926#:~:text=Spin%20Highest%20spin%3A%202%2C555%20rpm%2C,high%20spin%20on%20a%20cutter)
[\[9\]](https://www.mlb.com/news/statcast-spin-rate-compared-to-velocity-c160896926#:~:text=Velocity%20Highest%20velo%3A%2091,mph%3B%20the%20second%20slowest%20is)
[\[10\]](https://www.mlb.com/news/statcast-spin-rate-compared-to-velocity-c160896926#:~:text=Spin%20Highest%20spin%3A%202%2C654%20rpm%2C,5%20mph%2C%20Caminero)
[\[12\]](https://www.mlb.com/news/statcast-spin-rate-compared-to-velocity-c160896926#:~:text=belongs%20to%20Carlos%20Martinez%20at,KNUCKLE%20CURVE)
[\[13\]](https://www.mlb.com/news/statcast-spin-rate-compared-to-velocity-c160896926#:~:text=Spin%20Highest%20spin%3A%203%2C086%20rpm%2C,Velocity)
[\[14\]](https://www.mlb.com/news/statcast-spin-rate-compared-to-velocity-c160896926#:~:text=Curves%20are%20thrown%20slowly%2C%20generally,spin%3A%201%2C302%20rpm%2C%20Logan%20Kensing)
[\[15\]](https://www.mlb.com/news/statcast-spin-rate-compared-to-velocity-c160896926#:~:text=though%20more%20spin%20on%20a,difference%20between%20his%20fastball%20and)
[\[16\]](https://www.mlb.com/news/statcast-spin-rate-compared-to-velocity-c160896926#:~:text=Spin%20Highest%20spin%3A%202%2C421%20rpm%2C,Velocity)
[\[17\]](https://www.mlb.com/news/statcast-spin-rate-compared-to-velocity-c160896926#:~:text=highest,most%20unexpectedly%20dominant%20pitch%20in)
[\[18\]](https://www.mlb.com/news/statcast-spin-rate-compared-to-velocity-c160896926#:~:text=Spin%20Highest%20spin%3A%202%2C077%20rpm%2C,4%20mph%2C%20Familia)
[\[21\]](https://www.mlb.com/news/statcast-spin-rate-compared-to-velocity-c160896926#:~:text=Spin%20Highest%20spin%3A%202%2C555%20rpm%2C,6%20mph%2C%20Richards)
[\[22\]](https://www.mlb.com/news/statcast-spin-rate-compared-to-velocity-c160896926#:~:text=Spin%20Highest%20spin%3A%202%2C555%20rpm%2C,Velocity)
[\[23\]](https://www.mlb.com/news/statcast-spin-rate-compared-to-velocity-c160896926#:~:text=Curves%20are%20thrown%20slowly%2C%20generally,pitch%20of%20any%20pitcher%20all)
[\[24\]](https://www.mlb.com/news/statcast-spin-rate-compared-to-velocity-c160896926#:~:text=KNUCKLE%20CURVE)
[\[25\]](https://www.mlb.com/news/statcast-spin-rate-compared-to-velocity-c160896926#:~:text=Lowest%20spin%3A%201%2C122%20rpm%2C%20Carter,7)
[\[26\]](https://www.mlb.com/news/statcast-spin-rate-compared-to-velocity-c160896926#:~:text=Changeups%20are%20low%20spin%20and,Spin)
[\[66\]](https://www.mlb.com/news/statcast-spin-rate-compared-to-velocity-c160896926#:~:text=Spin%20Highest%20spin%3A%202%2C654%20rpm%2C,6%20mph)
[\[76\]](https://www.mlb.com/news/statcast-spin-rate-compared-to-velocity-c160896926#:~:text=With%20the%2040,0%20mph%2C%20Mark%20Buehrle)
[\[77\]](https://www.mlb.com/news/statcast-spin-rate-compared-to-velocity-c160896926#:~:text=MLB%20average%3A%202%2C123%20rpm%20Lowest,grounder%20rate%20of%20that%20group)
Statcast spin rate compared to velocity

<https://www.mlb.com/news/statcast-spin-rate-compared-to-velocity-c160896926>

[\[3\]](https://baseball.physics.illinois.edu/Denver.html#:~:text=average%20speed%20is%20about%2096,about%204%20inches%20less%20at)
[\[41\]](https://baseball.physics.illinois.edu/Denver.html#:~:text=commonly%20referred%20to%20as%20,plate%20at%20about%2086%20mph)
[\[42\]](https://baseball.physics.illinois.edu/Denver.html#:~:text=Roughly%20speaking%2C%20a%20baseball%20loses,plate%20at%20about%2086%20mph)
[\[45\]](https://baseball.physics.illinois.edu/Denver.html#:~:text=peak%20speed,A)
[\[47\]](https://baseball.physics.illinois.edu/Denver.html#:~:text=played%20in%20a%20vacuum%20and,of%20their%20values%20at%20Fenway)
[\[49\]](https://baseball.physics.illinois.edu/Denver.html#:~:text=mean%20lower%20air%20density,of%20their%20values%20at%20Fenway)
[\[52\]](https://baseball.physics.illinois.edu/Denver.html#:~:text=In%20light%20of%20the%20above,to%20the%20Magnus%20force%2C%20an)
[\[57\]](https://baseball.physics.illinois.edu/Denver.html#:~:text=By%20the%20way%2C%20another%20thing,link%20for%20a%20nice%20discussion)
Baseball At High Altitude

<https://baseball.physics.illinois.edu/Denver.html>

[\[11\]](https://www.seemagnus.com/blog-posts-test/a-discussion-of-spin-efficiency#:~:text=Pitch%20Type2020%20Mean%20MLB%20Spin,Seam%20Fastball89.8Cutter49.1Sinker89.0Changeup89.3Curveball68.7Slider35.9Values%20are%20approximate)
[\[34\]](https://www.seemagnus.com/blog-posts-test/a-discussion-of-spin-efficiency#:~:text=One%20such%20discovery%20is%20that,expressed%20when%20talking%20about%20spin)
[\[35\]](https://www.seemagnus.com/blog-posts-test/a-discussion-of-spin-efficiency#:~:text=induced%20movement%20on%20a%20pitch,generate%20the%20movement%20they%20feature)
[\[69\]](https://www.seemagnus.com/blog-posts-test/a-discussion-of-spin-efficiency#:~:text=https%3A%2F%2Ftwitter)
[\[70\]](https://www.seemagnus.com/blog-posts-test/a-discussion-of-spin-efficiency#:~:text=Though%20his%20slider%20spins%20at,was%20because%20of%20how%20well)
A Discussion of Spin Efficiency

<https://www.seemagnus.com/blog-posts-test/a-discussion-of-spin-efficiency>

[\[19\]](https://www.comsol.it/blogs/physics-behind-baseball-pitches#:~:text=The%20knuckleball%20is%20the%20most,easier%20to%20hit%20because%20the)
[\[20\]](https://www.comsol.it/blogs/physics-behind-baseball-pitches#:~:text=actually%20its%20enemy,as%20seen%20in%20this%20GIF)
[\[27\]](https://www.comsol.it/blogs/physics-behind-baseball-pitches#:~:text=behind%20the%20ball%2C%20as%20explained,as%20seen%20in%20this%20GIF)
[\[73\]](https://www.comsol.it/blogs/physics-behind-baseball-pitches#:~:text=Fastballs%20are%20the%20easiest%20pitches,to%20change%20their%20position%20drastically)
[\[74\]](https://www.comsol.it/blogs/physics-behind-baseball-pitches#:~:text=)
[\[75\]](https://www.comsol.it/blogs/physics-behind-baseball-pitches#:~:text=A%20slider%20is%20thrown%20with,down%2C%20without%20any%20lateral%20movement)
The Physics Behind Baseball Pitches \| COMSOL Blog

<https://www.comsol.it/blogs/physics-behind-baseball-pitches>

[\[28\]](file://file_0000000028e86230881cd8d2f850493e#:~:text=factor,2%24%20in%20the%20upward)
[\[36\]](file://file_0000000028e86230881cd8d2f850493e#:~:text=break%20downward%20%E2%80%93%20for%20a,2)
[\[39\]](file://file_0000000028e86230881cd8d2f850493e#:~:text=In%20simulation%20terms%2C%20we%20will,same%20ball%20at%20sea%20level)
[\[40\]](file://file_0000000028e86230881cd8d2f850493e#:~:text=coefficient%2C%20%24,quantify%20those%20environmental%20effects%20shortly)
[\[43\]](file://file_0000000028e86230881cd8d2f850493e#:~:text=Trajectory%20computation%3A%20At%20each%20small,time)
[\[44\]](file://file_0000000028e86230881cd8d2f850493e#:~:text=velocity%20and%20position,time%20in%20a%20game)
[\[59\]](file://file_0000000028e86230881cd8d2f850493e#:~:text=But%20including%20wind%20adds%20a,out%20on%20a%20calm%20day)
[\[60\]](file://file_0000000028e86230881cd8d2f850493e#:~:text=In%20practical%20terms%2C%20our%20module,5%20mph%20of%20tailwind%20%E2%89%88)
Modeling Baseball Batted Ball Trajectories for Realistic Simulation.docx

<file://file_0000000028e86230881cd8d2f850493e>

[\[29\]](https://www.reddit.com/r/ColoradoRockies/comments/31s5zy/why_is_it_so_hard_to_pitch_at_coors/#:~:text=,seen%20during%20some%20baseball%20pitches)
[\[30\]](https://www.reddit.com/r/ColoradoRockies/comments/31s5zy/why_is_it_so_hard_to_pitch_at_coors/#:~:text=,rotor%20ships%20and%20Flettner%20aeroplanes)
[\[31\]](https://www.reddit.com/r/ColoradoRockies/comments/31s5zy/why_is_it_so_hard_to_pitch_at_coors/#:~:text=)
[\[46\]](https://www.reddit.com/r/ColoradoRockies/comments/31s5zy/why_is_it_so_hard_to_pitch_at_coors/#:~:text=The%20Magnus%20Effect%20is%20the,to%20the%20density%20of%20air)
Why is it so hard to pitch at Coors? : r/ColoradoRockies

<https://www.reddit.com/r/ColoradoRockies/comments/31s5zy/why_is_it_so_hard_to_pitch_at_coors/>

[\[32\]](https://physics.wooster.edu/wp-content/uploads/2021/08/Junior-IS-Thesis-Web_1999_Nowicki.pdf#:~:text=,depending%20on%20the%20seams)
\[PDF\] Forces that govern a baseball's flight path - Wooster Physics

<https://physics.wooster.edu/wp-content/uploads/2021/08/Junior-IS-Thesis-Web_1999_Nowicki.pdf>

[\[33\]](https://www.physics.sydney.edu.au/~cross/TRAJECTORIES/Trajectories.html#:~:text=ball%20trajectories%20The%20Magnus%20force,but%20CL%20depends%20on)
ball trajectories

<https://www.physics.sydney.edu.au/~cross/TRAJECTORIES/Trajectories.html>

[\[37\]](https://www.si.com/mlb/diamondbacks/analysis/does-more-extension-yield-better-fastball-performance#:~:text=The%20graph%20shows%20not%20only,than%20its%20radar%20gun%20reading)
[\[38\]](https://www.si.com/mlb/diamondbacks/analysis/does-more-extension-yield-better-fastball-performance#:~:text=Earlier%20this%20month%2C%20Nick%20Piecoro,or%20at%20the%20ballpark)
[\[65\]](https://www.si.com/mlb/diamondbacks/analysis/does-more-extension-yield-better-fastball-performance#:~:text=Does%20More%20Extension%20Yield%20Better,reading%20of%20a%20pitcher%27s%20fastball)
[\[68\]](https://www.si.com/mlb/diamondbacks/analysis/does-more-extension-yield-better-fastball-performance#:~:text=With%20an%20r,be%20at%20getting%20hitters%20out)
Does More Extension Yield Better Fastball Performance? - Sports
Illustrated Arizona Diamondbacks News, Analysis and More

<https://www.si.com/mlb/diamondbacks/analysis/does-more-extension-yield-better-fastball-performance>

[\[48\]](https://coloradosun.com/2023/08/22/colorado-rockies-coors-field-elevation/#:~:text=If%20you%20throw%20that%20pitch,it%20is%20at%20sea%20level)
[\[50\]](https://coloradosun.com/2023/08/22/colorado-rockies-coors-field-elevation/#:~:text=staffs%20have%20experienced%20for%20the,work%20in%20baseball%E2%80%99s%20weirdest%20funhouse)
[\[51\]](https://coloradosun.com/2023/08/22/colorado-rockies-coors-field-elevation/#:~:text=about%209%20inches,it%20is%20at%20sea%20level)
Why are the Rockies still bad? How elevation affects baseball.

<https://coloradosun.com/2023/08/22/colorado-rockies-coors-field-elevation/>

[\[53\]](https://commandtrakker.com/Weather%20and%20altitude%20effects%20on%20pitched%20and%20batted%20baseballs.html#:~:text=Higher%20Temperature%3A%20Causes%20the%20air,air%20resistance%20could%20allow%20a)
[\[54\]](https://commandtrakker.com/Weather%20and%20altitude%20effects%20on%20pitched%20and%20batted%20baseballs.html#:~:text=Lower%20Temperature%3A%20Increases%20air%20density%2C,and%20the%20slide%20in%20sliders)
[\[55\]](https://commandtrakker.com/Weather%20and%20altitude%20effects%20on%20pitched%20and%20batted%20baseballs.html#:~:text=reduces%20air%20density%2C%20which%20in,which%20is%20responsible%20for%20the)
[\[56\]](https://commandtrakker.com/Weather%20and%20altitude%20effects%20on%20pitched%20and%20batted%20baseballs.html#:~:text=designed%20to%20have%20a%20significant,the%20movement%20of%20breaking%20balls)
[\[58\]](https://commandtrakker.com/Weather%20and%20altitude%20effects%20on%20pitched%20and%20batted%20baseballs.html#:~:text=Higher%20Humidity%3A%20Adds%20moisture%20to,the%20movement%20of%20breaking%20pitches)
[\[71\]](https://commandtrakker.com/Weather%20and%20altitude%20effects%20on%20pitched%20and%20batted%20baseballs.html#:~:text=Can%20directly%20impact%20the%20flight,by%20decreasing%20the%20relative%20velocity)
[\[72\]](https://commandtrakker.com/Weather%20and%20altitude%20effects%20on%20pitched%20and%20batted%20baseballs.html#:~:text=Higher%20altitudes%20have%20thinner%20air%2C,venues%20like%20Denver%27s%20Coors%20Field)
Command Trakker - Weather and altitude effects on pitched and batted
baseballs

<https://commandtrakker.com/Weather%20and%20altitude%20effects%20on%20pitched%20and%20batted%20baseballs.html>

[\[61\]](https://www.drivelinebaseball.com/2019/01/deeper-dive-fastball-spin-rate/?srsltid=AfmBOoooDHa4PfQDYwImU_EhOdPJCeFjotAgpzgWQ7Gn_r_GmKwf1wsr#:~:text=Now%20the%20fastest%20spin%20rate,spin%20fastballs%20on%20the%20ground)
[\[67\]](https://www.drivelinebaseball.com/2019/01/deeper-dive-fastball-spin-rate/?srsltid=AfmBOoooDHa4PfQDYwImU_EhOdPJCeFjotAgpzgWQ7Gn_r_GmKwf1wsr#:~:text=There%20is%20a%20distinction%20between,because%20of%20the%20ball%E2%80%99s%20axis)
A Deeper Dive into Fastball Spin Rate - Driveline Baseball

<https://www.drivelinebaseball.com/2019/01/deeper-dive-fastball-spin-rate/?srsltid=AfmBOoooDHa4PfQDYwImU_EhOdPJCeFjotAgpzgWQ7Gn_r_GmKwf1wsr>

[\[62\]](https://sites.northwestern.edu/nusportsanalytics/2019/06/30/theres-more-to-a-good-fastball-than-just-being-fast/#:~:text=The%20most%20interesting%20data%20from,can%20be%20seen%20by%20the)
[\[63\]](https://sites.northwestern.edu/nusportsanalytics/2019/06/30/theres-more-to-a-good-fastball-than-just-being-fast/#:~:text=Swinging%20strikes%2092,13)
There’s More to a Good Fastball than Just Being ‘Fast’ \| Northwestern
Sports Analytics Group

<https://sites.northwestern.edu/nusportsanalytics/2019/06/30/theres-more-to-a-good-fastball-than-just-being-fast/>

[\[64\]](https://www.reddit.com/r/baseball/comments/1cag8mi/tyler_glasnow_has_a_99th_percentile_extension_75/#:~:text=Tyler%20Glasnow%20has%20a%2099th,Analysis)
Tyler Glasnow has a 99th percentile extension (7.5 feet) and a 96.3 ...

<https://www.reddit.com/r/baseball/comments/1cag8mi/tyler_glasnow_has_a_99th_percentile_extension_75/>
