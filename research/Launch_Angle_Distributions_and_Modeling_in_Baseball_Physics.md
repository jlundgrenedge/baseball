# Launch Angle Distributions and Modeling in Baseball Physics

## 1. MLB Launch Angle Distributions

*Histogram of MLB launch angles with a normal curve fit (blue),
illustrating a roughly unimodal, bell-shaped distribution centered
around
~10–15°[\[1\]](https://tht.fangraphs.com/toward-a-probability-distribution-over-batted-ball-trajectories/#:~:text=Focusing%20first%20on%20launch%20angle%2C,batter%2C%20pitcher%20and%20other%20factors).*

**Shape of Distribution:** Empirical studies of Statcast data indicate
that the distribution of batted-ball launch angles in MLB is roughly
**unimodal and centered in the low-teens (degrees)**. In a large 2015
Statcast sample, the histogram of all launch angles closely followed a
single-peaked bell curve with a mean around
10–12°[\[2\]](https://lup.lub.lu.se/student-papers/record/9175631/file/9175632.pdf#:~:text=reasonable%20with%20smoother%20and%20more,distribution%2C%20peaking%20around%2010%20degrees).
The blue curve in the figure above shows a normal distribution fit –
launch angles adhere “very closely to a normal distribution” across all
batted
balls[\[1\]](https://tht.fangraphs.com/toward-a-probability-distribution-over-batted-ball-trajectories/#:~:text=Focusing%20first%20on%20launch%20angle%2C,batter%2C%20pitcher%20and%20other%20factors).
This means that most batted balls cluster around a moderate launch angle
(roughly the line-drive range), with fewer occurrences of extremely low
or high angles. In fact, one analysis found the MLB-wide launch angle
distribution peaks near 10° and tapers off toward the extremes, whereas
exit velocities were **right-skewed** (many more low-speed
hits)[\[2\]](https://lup.lub.lu.se/student-papers/record/9175631/file/9175632.pdf#:~:text=reasonable%20with%20smoother%20and%20more,distribution%2C%20peaking%20around%2010%20degrees).
The normality observation was somewhat surprising – analysts initially
suspected that because launch angle is a bounded angle, its distribution
might be highly skewed or require a trigonometric transform (like
cosine), but in practice the **raw angles behaved approximately
normal**[\[3\]](https://tht.fangraphs.com/toward-a-probability-distribution-over-batted-ball-trajectories/#:~:text=My%20conclusion%20is%20that%20a,more%20closely%20a%20normal%20distribution).

**Heavy Tails and Skew:** Closer inspection, however, reveals that while
unimodal, the launch angle distribution is **broad with long tails**.
MLB hitters produce a wide range of outcomes from chopped ground balls
(negative or near-zero angles) to towering pop-ups (high positives).
League-average batted-ball profiles show about ~43% ground balls
(generally launch angle \< 10°), ~21% line drives (10–25°), and ~36% fly
balls (≥25°, including
pop-ups)[\[4\]](https://www.rotoballer.com/using-sabermetrics-for-fantasy-baseball-hitter-batted-ball-distribution/838542#:~:text=Distribution%20www,fly%20balls).
This implies a high variance – a large portion of batted balls fall far
from the mean. Indeed, research notes that **launch angle distributions
are much wider (more variable) than exit velocity
distributions**[\[5\]](https://community.fangraphs.com/controlling-launch-angle-to-limit-damage/#:~:text=most%20important%20predictor%20of%20a,this%20idea%20at%20great%20length).
Exit velos tend to cluster tightly around a batter’s typical power,
whereas launch angles scatter more – a pitcher can “deflect” contact
toward extreme angles more easily than they can reduce exit
speed[\[5\]](https://community.fangraphs.com/controlling-launch-angle-to-limit-damage/#:~:text=most%20important%20predictor%20of%20a,this%20idea%20at%20great%20length).
Consequently, the launch angle histogram has **“heavier tails”** than a
narrow normal curve might predict. In practical terms, extreme launch
angles (e.g. \< –10° or \> 50°) are infrequent but not negligible –
there is a non-trivial probability of mishits resulting in very low or
very high angles (e.g. topped rollers or pop-ups). These tails may cause
slight deviations from perfect normality (e.g. a bit more mass in the
extreme bins than a normal model expects). For instance, one might see a
small secondary bump in the distribution at the low end for *topped*
balls, and a long upper tail for *under-cut* balls. Overall, though, the
primary shape remains single-peaked (unimodal); we do not see two
distinct separate modes in aggregate MLB data – line drives and fly
balls blend into a continuous upper spectrum rather than forming two
completely separate humps.

**Player-to-Player Differences:** On the individual level, certain
hitters exhibit idiosyncratic distributions that depart from a simple
normal, often reflecting their hitting approach. For example, extreme
fly-ball hitters vs. ground-ball hitters have different centers and
spread. A **fly-ball hitter** like Joey Gallo might have an average
launch angle in the 20s and a distribution skewed toward the higher end
(with more frequent high-angle contact), whereas a **worm-burner
hitter** like prime Eric Hosmer (known for a low average launch angle)
centers closer to 5° with a large portion of negative angles
(grounders)[\[6\]](https://community.fangraphs.com/controlling-launch-angle-to-limit-damage/#:~:text=launch%20angles%20are%20centered%20much,for%20a%20guy%20with%20Gallo%E2%80%99s).
In Gallo’s case, his distribution puts him *“closer to the extremes on
the high end of
LA”*[\[6\]](https://community.fangraphs.com/controlling-launch-angle-to-limit-damage/#:~:text=launch%20angles%20are%20centered%20much,for%20a%20guy%20with%20Gallo%E2%80%99s)
– meaning he still hits some grounders, but a good chunk of his outcomes
are high flies and pop-ups (heavy upper tail). Hosmer, by contrast, had
a launch angle distribution shifted downward, so a disproportionate
number of his balls were in the ground-ball range. These tendencies can
give the impression of **bimodality or skew for specific hitters** –
e.g. Hosmer’s data might show one clustering around slightly below 0°
and a secondary concentration around 10–15° (when he did elevate).
However, those are really just personal skews rather than two distinct
*global* modes. Generally, any apparent bimodality in launch angle
usually stems from mixing different contexts (e.g. good vs. poor contact
– see below) rather than truly separate “preferred angles.” In summary,
published analyses and Statcast interpretations describe launch angle
distributions as **approximately unimodal with high variance** –
essentially normal-like in shape but **with broad tails** due to the mix
of grounders and
pop-ups[\[2\]](https://lup.lub.lu.se/student-papers/record/9175631/file/9175632.pdf#:~:text=reasonable%20with%20smoother%20and%20more,distribution%2C%20peaking%20around%2010%20degrees)[\[5\]](https://community.fangraphs.com/controlling-launch-angle-to-limit-damage/#:~:text=most%20important%20predictor%20of%20a,this%20idea%20at%20great%20length).

Importantly, those heavy tails correspond to the least productive
contact. At either extreme of launch angle (very low or very high), wOBA
and hit probability
plummet[\[7\]](https://community.fangraphs.com/controlling-launch-angle-to-limit-damage/#:~:text=%E2%80%9Cdeflecting%E2%80%9D%20batted%20balls%20to%20extreme,edge%20produce%20lower%20wOBA%20at).
This aligns with the intuitive “sweet spot” concept: most hits come from
a middle range of angles (~8–32° is often cited as the “sweet spot” for
line drives and home runs). Angles far below that (dribblers) or above
it (pop-ups) typically result in outs. Therefore, while the distribution
of *all* launch angles is statistically single-peaked, it implicitly
covers multiple *types* of contact outcomes – which suggests that
modeling it as a single normal may obscure some structure related to
contact quality. This leads into the idea of considering mixtures or
conditional models to capture those tail outcomes.

## 2. Physics-Based Explanations for Non-Normality

Several physical factors inherent to the bat-ball collision explain why
launch angle data might not form a perfectly tight, symmetric normal
distribution. In a controlled world – if every swing were identical and
every pitch the same – launch angles might vary only modestly around a
mean. In reality, **mechanics and geometry introduce systematic variance
and skew**:

- **Contact Point Geometry:** The vertical location where the bat
  strikes the ball has a direct effect on launch angle. Hitting *beneath
  the ball’s center* versus *above the ball’s center* produces very
  different trajectories. If the bat hits **below the center**, it
  effectively **lifts** the ball, imparting a higher launch angle (and
  usually backspin). This is how most **fly balls** are generated.
  Conversely, contact **above the center** drives the ball downward
  (lower launch angle, sometimes even negative) – this produces **low
  liners and ground balls**, often with
  topspin[\[8\]](https://github.com/jlundgrenedge/baseball/blob/0387122663d8501ea8473b26037fa4680793baeb/docs/ANGLE_DEPENDENT_SPIN_CALIBRATION.md#L24-L29)[\[9\]](https://github.com/jlundgrenedge/baseball/blob/0387122663d8501ea8473b26037fa4680793baeb/docs/PHASE2_SUMMARY.md#L280-L284).
  In practice, every batter’s swing will sometimes miss under or on top
  of the ball by varying amounts. These vertical offsets aren’t
  uniformly zero; they have a distribution – likely centered around a
  small offset (ideally zero for square contact) but with non-negligible
  probability of larger magnitudes. Small random differences in vertical
  contact point (a matter of inches or less) can change a 15° line drive
  into a 50° pop-up or a -5° chopper. This creates a natural **spread**
  in launch angles. Notably, it can also introduce **skewness** or
  bi-modality: there’s effectively an upper and lower “side” of the ball
  to miss. **Under-cutting** (bat too low) tends to yield high-angle
  hits, while **topping** (bat too high) yields negative angles. If
  those miss-hit scenarios occur with appreciable frequency, the
  aggregate distribution gets heavy tails on both ends (representing
  those two failure modes). Physicists have documented that real MLB
  line drives often result from hitting just above the ball’s equator
  (minimal backspin, lower angle), whereas home-run caliber fly balls
  involve more undercutting to get the ball airborne with
  backspin[\[8\]](https://github.com/jlundgrenedge/baseball/blob/0387122663d8501ea8473b26037fa4680793baeb/docs/ANGLE_DEPENDENT_SPIN_CALIBRATION.md#L24-L29).
  The **contact model** in the simulation reflects this: for example, an
  offset of +1 inch (bat hitting slightly *above* center) might reduce
  launch angle by a couple degrees (turning a would-be 21° flight into
  ~19°), whereas -1 inch (bat *below* center) adds a few degrees (e.g.
  up to
  ~23°)[\[10\]](https://github.com/jlundgrenedge/baseball/blob/0387122663d8501ea8473b26037fa4680793baeb/docs/PHASE2_SUMMARY.md#L198-L203).
  Over many swings, these offset effects spread out the angles.

- **Pitch & Swing Interaction:** The **pitch’s properties** (especially
  vertical location and movement) combined with the batter’s swing plane
  also drive variability in launch angle. A high pitch is easier to hit
  in the air (the bat meeting the ball above the plate’s midline with an
  uppercut), whereas a low pitch encourages a downward outcome (batter
  has to swing over it, often resulting in a grounder). Statistical
  analyses confirm *pitch height is the single most important factor
  influencing launch angle* of
  contact[\[11\]](https://community.fangraphs.com/controlling-launch-angle-to-limit-damage/#:~:text=on%20a%20number%20of%20different,statistical%20significance%20to%20launch%20angle)[\[12\]](https://community.fangraphs.com/controlling-launch-angle-to-limit-damage/#:~:text=MLB%20Launch%20Angle%20Variable%20Importance,by%20Pitch%20Type).
  All else equal, **up-in-the-zone pitches produce higher launch angles,
  and low pitches produce lower launch angles**, as seen in heatmaps of
  pitch location vs. launch
  angle[\[12\]](https://community.fangraphs.com/controlling-launch-angle-to-limit-damage/#:~:text=MLB%20Launch%20Angle%20Variable%20Importance,by%20Pitch%20Type).
  This means that the overall distribution of launch angles is
  effectively a **mix of sub-distributions conditioned on pitch
  height**. Since pitchers throw all around the zone, a batter faces a
  blend of conditions: some swings (on high pitches) will inherently
  have a higher expected launch angle, while others (on low pitches)
  skew low. The result is a **wider combined distribution** than you’d
  get from one fixed scenario. It can even create **bi-modal
  tendencies** if you separated the data – e.g. one peak for outcomes
  against low pitches (centered around, say, 0°) and another for
  outcomes on high pitches (centered higher). When merged, it looks like
  one broad distribution, but the heavy tails owe partly to this
  pitch-induced mixture. Furthermore, pitch **type** and movement
  matter: breaking balls with downward bite are more often topped (lower
  launch
  angles)[\[13\]](https://github.com/jlundgrenedge/baseball/blob/0387122663d8501ea8473b26037fa4680793baeb/batted_ball/player.py#L546-L554),
  while rising four-seamers tend to be hit with slightly more
  loft[\[14\]](https://github.com/jlundgrenedge/baseball/blob/0387122663d8501ea8473b26037fa4680793baeb/batted_ball/player.py#L550-L558).
  The simulation’s batter model accounts for this by adjusting the
  swing’s mean attack angle based on pitch type and location (e.g. a
  *curveball* gets a –2° adjustment to mean launch angle, inducing more
  grounders; a *four-seam fastball* gets a slight +1° bump to promote
  fly
  balls)[\[13\]](https://github.com/jlundgrenedge/baseball/blob/0387122663d8501ea8473b26037fa4680793baeb/batted_ball/player.py#L546-L554).
  These adjustments mirror real-life tendencies but also increase
  variance – because not every pitch is the same, the batter’s swing
  plane mean is shifting contextually. Thus, physics ensures launch
  angle is **heterogeneous**: each plate appearance has its own
  distribution around a different mean, rather than one tight normal
  every time.

- **Swing Mechanics and Human Variability:** Even for identical pitches,
  batters do not reproduce the exact same swing every time. There’s
  inherent **noise in swing timing, bat path, and point of contact**.
  For instance, batters can slightly vary their **swing plane (attack
  angle)** from swing to swing. MLB hitters’ swing path (attack) angles
  vary on the order of 10–20° in standard
  deviation[\[15\]](https://github.com/jlundgrenedge/baseball/blob/0387122663d8501ea8473b26037fa4680793baeb/batted_ball/player.py#L531-L539).
  This is quite large – even a “fly-ball hitter” who averages say +15°
  attack angle will sometimes come in much lower or higher on the ball
  due to timing and approach. Such variability in the swing plane
  translates directly into launch angle variability. As the
  `batted_ball` code notes, *“even the best hitters have huge variance
  in launch angle (15–20° std dev)… this is what creates the ground
  ball/line drive/fly ball
  distribution”*[\[15\]](https://github.com/jlundgrenedge/baseball/blob/0387122663d8501ea8473b26037fa4680793baeb/batted_ball/player.py#L531-L539).
  In other words, humans are not machines: on some swings a hitter gets
  the ideal loft, on others they drive it into the ground or sky it.
  This random component generally produces a **normal-like spread** of
  launch angles for a given hitter/pitch, but it contributes to the
  **heavy tails** because occasionally the swing is far off – resulting
  in an extreme angle. Additionally, batters may **strategically alter
  their swing** in certain counts or situations (e.g. with two strikes,
  some shorten up and might reduce uppercut, leading to a different
  distribution than in hitter’s counts). Such situational changes
  effectively superimpose multiple swing strategies in the overall data,
  which again can widen or skew the distribution.

- **Energy Transfer and Spin Effects:** The physics of the collision can
  also reinforce non-normal outcomes. When a ball is hit at extreme
  angles, it often coincides with a less efficient energy transfer. For
  example, a very high launch angle pop-up usually means the bat only
  caught the bottom of the ball, imparting a lot of backspin but not
  much forward speed. These are the 150-foot, 80° degree infield pops –
  the ball goes almost straight up. Similarly, a very low launch angle
  (e.g. -5° worm-burner) might come from topping the ball, driving it
  into the ground with topspin (and often breaking the bat or deadening
  the exit velocity). In both cases, **spin is a telltale**: A ball hit
  well below center gets **excess backspin**, whereas one hit above
  center can even have
  **topspin**[\[8\]](https://github.com/jlundgrenedge/baseball/blob/0387122663d8501ea8473b26037fa4680793baeb/docs/ANGLE_DEPENDENT_SPIN_CALIBRATION.md#L24-L29).
  While spin itself doesn’t change the launch angle at contact, it
  affects hang time and distance, and it correlates with the mis-hit
  quality. These extreme contacts frequently result in easy outs (either
  a weak ground out or a harmless pop out). Moreover, many **extreme
  mishits become foul balls** rather than fair. For instance, a *45°+
  launch* might go straight up and drift foul behind the plate, and a
  *very steep negative angle* might bounce foul immediately. Statcast
  data typically only logs fair or fielded balls, so some of the most
  extreme angles are actually filtered out. (The simulation enforces
  this: if a computed launch angle is \< –10° or \> 60°, they flag it as
  a likely foul
  ball[\[16\]](https://github.com/jlundgrenedge/baseball/blob/0387122663d8501ea8473b26037fa4680793baeb/batted_ball/at_bat.py#L1118-L1124).)
  This *censoring* means the in-play distribution is somewhat truncated
  at the extremes – but even with that, we observe a lot of near-extreme
  values in play (e.g. pop-ups in the 50–60° range, or choppers around
  –5 to –10° that stay fair). The *presence* of these high-spin,
  low-energy contacts in the dataset contributes to heavier tails
  (there’s a finite probability of getting an outlier angle).
  Physically, they occur because if the collision isn’t near-perfect,
  some energy goes into spin or vibration instead of directed launch –
  the ball might not go far, but it can go very high or very low.

In summary, the **non-normality (broad variance, skew, and
tail-heaviness)** of launch angle distributions arises naturally from
baseball physics: variability in where and how the bat meets the ball,
differences in pitch location and movement, and the dual nature of good
vs. bad contact. All these factors cause launch angle outcomes to spread
out more than, say, a simple random scatter around one mean. As a
result, while assuming a normal distribution for launch angle is a
reasonable first approximation (as found in early Statcast
analyses[\[1\]](https://tht.fangraphs.com/toward-a-probability-distribution-over-batted-ball-trajectories/#:~:text=Focusing%20first%20on%20launch%20angle%2C,batter%2C%20pitcher%20and%20other%20factors)),
one must recognize that the **variance is large** and that **extreme
angles (both low and high)** occur more often than a narrow normal would
predict. This is why we observe a substantial “tail” of pop-ups and
topped grounders in real data. Any realistic simulation or model should
account for this, ensuring that not every ball comes off the bat in a
tight band around the average – there should be some probability of
those fluke pop flies and tricklers that are part of the game.

## 3. Modeling Techniques for Launch Angle in Simulations

Given the above, a simple normal model (with fixed mean and variance)
may not fully capture the nuances of launch angle outcomes. Fortunately,
there are several statistical modeling approaches to better emulate the
properties we see in real data:

**(a) Mixture Models for Bimodality/Heavy Tails:** One powerful approach
is to treat the launch angle distribution as a **mixture of two or more
underlying distributions** rather than a single normal. This aligns with
the intuitive idea that batted balls come from a combination of
*well-hit* and *mis-hit* outcomes. Tom Tango and others have argued that
“batter swings are essentially two distributions merged” – one for
**“competitive” contact** (squared up swings) and one for
**“non-competitive” contact** (poor
contact)[\[17\]](https://baseballwithr.wordpress.com/2024/07/29/modeling-to-extract-a-players-competitive-swings/#:~:text=velocities%20of%20batter%20swings%20are,competitive%20swings).
Jim Albert demonstrated this by fitting a two-component **normal mixture
model** to exit velocities, separating a hitter’s results into a
low-mean “weak contact” group and a high-mean “solid contact”
group[\[18\]](https://baseballwithr.wordpress.com/2024/07/29/modeling-to-extract-a-players-competitive-swings/#:~:text=When%20I%20read%20this%20Twitter,two%20normal%20curves%20sampling%20distribution).
We can apply the same logic to launch angles. For example, imagine one
component is a normal distribution centered around ~15° (a typical solid
line-drive trajectory) with moderate spread, and another component is a
broad distribution that accounts for the extremes (perhaps with a lower
mean or even two sub-peaks toward the low and high end). A **Gaussian
Mixture Model (GMM)** could be fit to historical launch angle data to
formally estimate these components. Conceptually, this might reveal,
say, that **70% of balls** come from a main normal N(μ≈12°, σ≈12°) and
**30%** from a wide “mishit” distribution that has a flatter, wider
shape (or even two modes around –5° and 45° for extreme grounders vs.
pop-ups). By sampling from such a mixture, a simulation naturally
produces heavy tails and even a hint of bimodality, because a certain
fraction of the time it deliberately draws from the “extreme angle”
component.

*Implementation:* In a simulation like `batted_ball`, one could
implement a mixture model by first determining which component a given
swing will follow (e.g., draw a uniform random number to decide “normal
contact” vs “mishit”). This probability could be tied to the batter’s
skill – for instance, a batter with a high barrel rate might have a
smaller chance of the mishit component. Once the component is chosen,
the launch angle is then sampled from the corresponding distribution
(each with its own mean and variance). For example, **Component 1**
might yield most angles in a tighter band (say 10–25°), whereas
**Component 2** might frequently generate very low or high angles. This
method aligns with how analysts separate **“barrels” and weak contact**
in data. In fact, it can use real metrics for calibration: e.g., let the
mixture weight *p* equal the observed rate of *non-competitive swings*
for that hitter (one could use something like 100% – sweet-spot% or a
combination of topped+under%. In 2019 MLB, about 35–40% of balls are in
the “weak extremes” – which roughly matches the idea that maybe ~40% of
contacts are poorly hit in terms of launch angle). By capturing these as
distinct sub-distributions, the model ensures a more accurate overall
shape. In open-source practice, fitting such models is straightforward
(e.g., using expectation-maximization for GMMs or Bayesian mixture via
PyMC/Stan). Albert’s example explicitly shows how two normal curves can
be fit and summed to match a batter’s
data[\[18\]](https://baseballwithr.wordpress.com/2024/07/29/modeling-to-extract-a-players-competitive-swings/#:~:text=When%20I%20read%20this%20Twitter,two%20normal%20curves%20sampling%20distribution),
and he notes the mixture’s second component mean is a better indicator
of true talent (since the first component is essentially noise). For
**launch angles**, a mixture model might reveal, say, one mode around
the batter’s typical line-drive angle and another related to their
pop-up tendency. Using that in simulation, we could *generate, for
instance, 10% of swings as “pop-ups” drawn from a high-angle
sub-distribution*. Such an approach would capture the heavy tail of
pop-ups and prevent the simulation from underestimating how often really
high balls occur.

**(b) Heteroscedastic (Variance-Dependent) Models:** Another refinement
is to allow the **variance of launch angle to change depending on
conditions or latent variables**. In other words, not every
swing/situation has the same uncertainty – some scenarios produce more
consistent angles, others more scatter. A straightforward way to do this
is through a **heteroscedastic regression** or a **generalized least
squares model** where you predict both the mean and the variance. Scott
Powers’ analysis hinted at this by separately modeling launch angle mean
and standard deviation for each batter-pitcher
matchup[\[19\]](https://tht.fangraphs.com/toward-a-probability-distribution-over-batted-ball-trajectories/#:~:text=Given%20that%20it%20is%20a,least%20squares%20with%20unknown%20variance)[\[20\]](https://tht.fangraphs.com/toward-a-probability-distribution-over-batted-ball-trajectories/#:~:text=match%20at%20L611%20The%20table,his%20former%20Reds%20teammate%2C%20Todd).
He found certain hitters (e.g. Joey Votto) had significantly **lower
launch angle variance** – effectively a “tighter” distribution – whereas
others were more
all-or-nothing[\[20\]](https://tht.fangraphs.com/toward-a-probability-distribution-over-batted-ball-trajectories/#:~:text=match%20at%20L611%20The%20table,his%20former%20Reds%20teammate%2C%20Todd).
This suggests we can incorporate a **“launch angle consistency”**
parameter. Technically, one could use a **GLM** (with something like a
log-linked variance) or a **mixed-effects model** with random intercepts
(for mean) and random slopes (for variance) to capture this. In
practice, for simulation, a simpler approach can work: tie the spread of
the launch angle distribution to an attribute or to the **predicted
outcome quality**. For example, if our simulation’s collision physics
predicts a very high exit velocity (meaning solid contact), we might
*reduce* the randomness in launch angle – the ball was squared up, so
it’s less likely to veer to an extreme angle. Conversely, if the swing
timing is off (predicted poor contact), we *increase* the variance of
the resulting launch angle. This is a form of outcome-dependent
heteroscedasticity. We could implement it by making the **launch angle
standard deviation a function of contact quality**. In code, imagine
something like:

    if contact_quality == 'solid':
        angle = np.random.normal(mu, base_sigma * 0.5)  # tighter spread
    elif contact_quality == 'weak':
        angle = np.random.normal(mu, base_sigma * 1.5)  # wider spread
    else:
        angle = np.random.normal(mu, base_sigma)       # normal spread

Here `base_sigma` might be the player’s inherent launch angle
variability (e.g. 15°), which we modulate. The `batted_ball` module
already contains the seeds of this – the **HitterAttributes** include an
*attack angle variance* rating and the code sets a **natural_variance
~15°** for everyone, then scales it by a consistency
factor[\[21\]](https://github.com/jlundgrenedge/baseball/blob/0387122663d8501ea8473b26037fa4680793baeb/batted_ball/player.py#L559-L567).
One could extend that by incorporating context: for instance, add logic
such that **difficult pitches (those with high location difficulty or
high movement)** yield effectively a higher variance in the sampled
swing path angle. This would reflect reality: a tough pitch not only
lowers the mean launch angle (more likely a grounder) but probably
increases scatter (the batter is more likely to mishit it in various
ways). Indeed, the simulation already does something analogous – it
increases the **contact point offset** when the pitch is in a difficult
location[\[22\]](https://github.com/jlundgrenedge/baseball/blob/0387122663d8501ea8473b26037fa4680793baeb/batted_ball/at_bat.py#L880-L888)[\[23\]](https://github.com/jlundgrenedge/baseball/blob/0387122663d8501ea8473b26037fa4680793baeb/batted_ball/at_bat.py#L896-L905),
which indirectly increases variance in launch outcomes. A
heteroscedastic statistical model could also be batter-specific: some
hitters might consistently produce a narrower launch angle distribution
(those with excellent bat control), while others have boom-or-bust
swings. In the simulation, this can be represented by an attribute (as
it is with the `get_attack_angle_variance_deg()` in the code). Using a
**heteroscedastic approach ensures the model isn’t forced to fit one
variance to all data** – it can have, say, a smaller σ for certain
subsets (like for middle-zone pitches or for high-contact hitters), and
a larger σ for others (like two-strike “defensive” swings or
low-percentage contact scenarios). From an academic standpoint, this is
supported by evidence that **launch angle “tightness” varies across
players and correlates with outcomes** (tight distribution -\> higher
BABIP)[\[24\]](https://fantasy.fangraphs.com/lets-talk-about-launch-angle-tightness/#:~:text=Yesterday%2C%20I%20finally%20followed%20up,EV)[\[25\]](https://fantasy.fangraphs.com/lets-talk-about-launch-angle-tightness/#:~:text=2019%20twitter).
So, incorporating a variable spread is both realistic and beneficial for
simulation fidelity.

**(c) Outcome-Dependent or Conditional Distributions:** A related
strategy is to model launch angle **conditional on other outcomes**,
rather than in isolation. The prime example is recognizing the coupling
between **exit velocity and launch angle**. Empirically, launch angle is
not independent of exit velo – very poorly hit balls (low EV) often have
extreme angles (many bloops and flares have high angles but low speed,
and many weak grounders have low angles and low speed). Meanwhile,
extremely well-hit balls (high EV) tend to cluster in an optimal launch
range (it’s hard to crush a ball 110 mph straight up in the air; most
110+ mph hits are line drives in the ~10–30° range). This suggests a
**heteroscedastic relationship** where the distribution of launch angle
depends on exit velocity (or on the underlying collision quality that
produces exit velocity). In modeling terms, one approach is a **joint
distribution** or a sequential model: first determine exit velocity,
then sample launch angle from a conditional distribution *LA \| EV*.
Powers (2016) took this approach by predicting the distribution of
launch angle first and then the conditional distribution of exit
velocity given that launch
angle[\[26\]](https://tht.fangraphs.com/toward-a-probability-distribution-over-batted-ball-trajectories/#:~:text=The%20strategy%20is%20first%20to,product%20of%20these%20two%20distributions).
We could flip it: predict exit velo from the physics engine (which our
simulation does well based on bat speed, etc.), then use a conditional
launch angle model. For instance, conditional on a very high exit velo,
we bias the launch angle toward a narrower, more optimal range (perhaps
via a truncated normal centered around 20°). Conditional on a low exit
velo (which in simulation might mean a bad miss-hit or a slow pitch), we
allow a much wider angle spread (including very high pop-ups or
near-zero dribblers). This is essentially an **outcome-dependent
sampling** where the “outcome” in question is the collision’s
quality/EV. Another way to implement outcome-dependent modeling is
directly through the **contact quality categories** that the simulation
already computes (`contact_quality = 'solid'/'fair'/'weak'` based on the
total contact
offset)[\[27\]](https://github.com/jlundgrenedge/baseball/blob/0387122663d8501ea8473b26037fa4680793baeb/batted_ball/at_bat.py#L848-L856).
Instead of treating that as just a label, we use it to shape the random
sampling: e.g., if `contact_quality == 'weak'`, we might *override* the
launch angle to an extreme value. We could even draw from empirical
distributions for those cases – for example, we know that “topped”
contacts (a subset of weak) typically result in very low launch angles
(say -20° to 0°), whereas “under-cut” contacts (pop-ups) result in, say,
50–90°. We could maintain two small lookup distributions for these and
sample accordingly when a weak contact is identified as a top or bottom
mishit. Essentially, this is a **two-stage model**: (1) determine
contact type/outcome using a probability model, (2) sample launch angle
(and perhaps spin, etc.) from a distribution specific to that outcome.
This method ensures physical coherence – e.g., if our simulation
calculates that a batter just barely nicked under the ball (weak
contact, high spin), instead of still giving a median ~10° angle with
just more variance, we explicitly give it a high launch angle drawn from
a “mishit pop-up” distribution.

*In practice:* We could implement outcome-dependent sampling in the
`ContactModel.full_collision` pipeline. For example, after computing the
collision results, we examine the `collision_efficiency_q` or
`sweet_spot_distance` (how far off from perfect
contact)[\[28\]](https://github.com/jlundgrenedge/baseball/blob/0387122663d8501ea8473b26037fa4680793baeb/batted_ball/at_bat.py#L860-L864).
If the collision efficiency is below some threshold (meaning a bad hit),
we then *resample or adjust the launch angle*. Perhaps we have
predetermined that very bad hits split into two kinds: “too high” vs
“too low.” We could use the vertical_contact_offset sign to decide – if
the bat was significantly under the ball (large negative offset), that’s
likely a sky-high pop-up scenario, so instead of using the originally
computed angle (which might have been, say, 30° from the swing
equation), we draw a new angle from a high-pop distribution (e.g. Normal
with μ=70°, σ=5° or even a fixed extreme). Similarly, if the bat was
well on top of the ball (positive offset beyond a certain point), we
draw the launch angle from a near-ground distribution (e.g. Normal μ=-5°
or 0°, with a small variance). This effectively **conditions launch
angle on the nature of contact** in a discrete way. It’s
outcome-dependent sampling because the simulation isn’t just blindly
sampling angle independent of context – it’s using the outcome of the
collision (good vs bad contact) to influence the angle distribution.
Another, simpler implementation: incorporate **Barrel% or
“under/flare/topped” rates** (which Statcast provides) into the
simulation. Statcast’s *batted ball profile* stats break contact into
categories: e.g., % “Under” (too high), % “Topped” (too low), etc. One
could sample from those: e.g., a given batter might have 5% “Under”
(pop-ups), 10% “Topped,” 50% “Flush/solid,” etc. During each simulated
contact, randomly assign one of these outcomes according to those
probabilities, then assign a representative launch angle. There are
open-source resources and datasets (Baseball Savant, retrosheet with
Statcast) that could provide these fractions for calibration. In
academic literature, this two-step modeling is akin to conditional
density estimation – a recent **Hardball Times** article, for instance,
constructed a **joint probability density of exit velo and launch
angle** as a 2D
distribution[\[29\]](https://tht.fangraphs.com/toward-a-probability-distribution-over-batted-ball-trajectories/#:~:text=Image%3A%20This%20heatmap%20shows%20the,%28via%20Scott%20Powers)[\[30\]](https://tht.fangraphs.com/toward-a-probability-distribution-over-batted-ball-trajectories/#:~:text=distance%20from%20the%20origin%20in,Let%E2%80%99s%20see%20the%20full%20version).
One can sample from that joint distribution to ensure realistic
correlations between EV and LA (for example, the joint PDF heatmap in
Powers’ article clearly shows that the highest exit velocities cluster
around ~15–25° launch – the model should reflect that, rather than
allowing a 110 mph, 60° pop-up which in reality is virtually
impossible)[\[30\]](https://tht.fangraphs.com/toward-a-probability-distribution-over-batted-ball-trajectories/#:~:text=distance%20from%20the%20origin%20in,Let%E2%80%99s%20see%20the%20full%20version)[\[1\]](https://tht.fangraphs.com/toward-a-probability-distribution-over-batted-ball-trajectories/#:~:text=Focusing%20first%20on%20launch%20angle%2C,batter%2C%20pitcher%20and%20other%20factors).

**(d) Other Techniques:** While the question focuses on mixtures and
heteroscedastic models, it’s worth noting a couple of other options
briefly. Some modelers have used **Beta distributions** or other bounded
distributions for launch angle, since angles have a fixed range (-90° to
+90° if we consider straight down and straight up). A Beta distribution
(on a scaled 0–1 range corresponding to -90 to +90) can be shaped to be
unimodal or even U-shaped. However, a single Beta might have trouble
capturing both tails adequately unless made very flexible. Another
approach is **quantile regression or empirical cdfs**: one could
empirically tabulate the launch angle distribution from Statcast and
sample from it directly (ensuring the simulation matches the real
distribution quantiles). This is less parametric and more data-driven –
one could even stratify those empirical distributions by exit velo or
contact quality to do conditional sampling as described. Lastly, machine
learning models (e.g. a **conditional GAN or normalizing flow**) could
generate launch angles given input conditions (pitch, swing) by learning
the complex joint distribution. Those are advanced methods and might be
overkill for most simulation purposes, but they exist as an option for
capturing intricate patterns in the data.

**Recommendations for Integration:** For a simulation engine like the
one in the `batted_ball` module, a **combination of the above methods is
ideal**. One could implement a hierarchy like:

1.  **Determine Contact Quality/Type:** Using either a probability model
    or the existing physics calculations, decide the category of contact
    (solid, fair, weak, topped, under-cut, etc.). This could be
    probabilistic based on player skill – e.g., use the player’s
    **barrel rating or contact ability** to bias this decision. The
    simulation already calculates a `contact_result['contact_quality']`
    after the
    fact[\[27\]](https://github.com/jlundgrenedge/baseball/blob/0387122663d8501ea8473b26037fa4680793baeb/batted_ball/at_bat.py#L848-L856);
    converting that into a prior step will allow us to condition the
    launch angle on it (essentially turning the descriptive label into a
    generative step).

2.  **Sample Launch Angle from Appropriate Distribution:**

3.  If the contact is solid/good, sample from a **primary distribution**
    (perhaps a normal with the player’s mean launch angle and a
    relatively smaller variance). This covers the bulk of line drives
    and well-hit fly balls. You might even center it at the player’s
    average launch angle (since the engine can store a player-specific
    LA tendency) and give it a std dev matching that player’s typical
    tightness.

4.  If the contact is weak/mishit, decide if it was *under* or *over*
    the ball (could use the vertical offset sign from the physics engine
    or a random split based on stats like % of under-hit vs topped).
    Then sample from an **extreme distribution**. For a popped-up
    under-hit, that could be, for example, a distribution centered
    around 70° (with some spread of a few degrees). For a topped
    dribbler, maybe center around -5° or 0° (since most topped grounders
    still have slightly positive angle unless truly into the ground).
    Alternatively, use a very broad single distribution that spans both
    tails for weak contact – e.g. a bimodal or a high-variance zero-mean
    distribution – but it might be easier to handle the two tails
    separately because the physics differ (backspin vs topspin).

5.  If the contact is “moderate” (not a pure barrel but not terrible),
    one could fall back to the baseline model (e.g., a single normal
    with intermediate variance). This might correspond to the “fair”
    contact category (somewhere in between).

6.  **Adjust Coherence with Exit Velocity:** Ensure that if you
    implement the above, it coheres with the exit velocity the physics
    model produces. In practice, the engine’s physics will give you an
    exit velocity and a raw launch angle (from bat path + offset
    calculations). You have a choice: you can either override the raw
    launch angle with your statistically sampled one, or blend them. A
    sensible approach is to trust the physics for typical outcomes but
    override in cases of extreme mishits. For example, if the physics
    says the ball was hit with very low collision efficiency and gives a
    launch angle of 15° (which might not make sense for such a poor
    contact), you replace that with a sampled 55° pop-up. On the other
    hand, if the physics outcome is within normal range, you keep it.
    Another approach: use the physics-computed launch angle as the mean
    of a distribution to sample from, rather than taking it
    deterministically. This would add stochasticity. For instance,
    instead of `launch_angle = collision_result['launch_angle']`
    directly, do
    `launch_angle = np.random.normal(collision_result['launch_angle'], context_sigma)`
    where `context_sigma` might be larger if collision_result indicates
    a less certain contact. This essentially introduces heteroscedastic
    noise around the physics prediction.

7.  **Validate and iterate:** After implementing, it’s important to
    **validate the simulated distribution against real Statcast data**.
    You can simulate a large number of at-bats and compare the launch
    angle histogram to MLB’s. Ideally, you’d see a close match: one peak
    in the low-teens, about ~40% of balls below 10°, a small fraction of
    pop-ups \>50°, etc. If the tails are still too light, you may
    increase the probability or variance of the extreme component. If
    you’re overproducing extremes, dial it back. Also ensure the **joint
    behavior with exit velocity** looks right – e.g., check that your
    sim isn’t creating 110 mph at 70° (should be exceedingly rare) and
    that most high EV are in mid angles, etc., similar to known EV-LA
    charts[\[30\]](https://tht.fangraphs.com/toward-a-probability-distribution-over-batted-ball-trajectories/#:~:text=distance%20from%20the%20origin%20in,Let%E2%80%99s%20see%20the%20full%20version).

By using **mixture or conditional models**, the simulation can capture
phenomena like a batter who *usually* hits 15° liners but occasionally
hits a 60° pop-up or a -10° worm-burner – without those extremes
dominating the average. Mixture models explicitly add those “occasional
extremes” in the right
proportion[\[17\]](https://baseballwithr.wordpress.com/2024/07/29/modeling-to-extract-a-players-competitive-swings/#:~:text=velocities%20of%20batter%20swings%20are,competitive%20swings)[\[18\]](https://baseballwithr.wordpress.com/2024/07/29/modeling-to-extract-a-players-competitive-swings/#:~:text=When%20I%20read%20this%20Twitter,two%20normal%20curves%20sampling%20distribution),
and heteroscedastic conditioning makes sure the model’s spread responds
to the situation (e.g., tough pitch -\> more scatter; great contact -\>
tighter range). These techniques are well-supported by the analytics
literature and public data: we know MLB launch angles overall look
roughly
normal[\[2\]](https://lup.lub.lu.se/student-papers/record/9175631/file/9175632.pdf#:~:text=reasonable%20with%20smoother%20and%20more,distribution%2C%20peaking%20around%2010%20degrees)
*but* with a big standard deviation
(~15–20°)[\[15\]](https://github.com/jlundgrenedge/baseball/blob/0387122663d8501ea8473b26037fa4680793baeb/batted_ball/player.py#L531-L539)
and that a not-insignificant chunk of batted balls lie in the
undesirable tail regions (pop-ups, topped
grounders)[\[5\]](https://community.fangraphs.com/controlling-launch-angle-to-limit-damage/#:~:text=most%20important%20predictor%20of%20a,this%20idea%20at%20great%20length).
The recommended modeling approaches essentially encode those real-world
insights into the simulation’s random number generation. By integrating
them into the `batted_ball` module, you would achieve a more faithful
reproduction of Statcast-like launch angle distributions – capturing the
proper shape (unimodal but wide) and the context dependencies (why and
when the extremes happen). In summary, **use a normal model for the core
of the distribution, but augment it with mixture components or
conditional rules to account for the non-normal tails and varying
consistency**, as validated by both physics reasoning and statistical
research[\[1\]](https://tht.fangraphs.com/toward-a-probability-distribution-over-batted-ball-trajectories/#:~:text=Focusing%20first%20on%20launch%20angle%2C,batter%2C%20pitcher%20and%20other%20factors)[\[12\]](https://community.fangraphs.com/controlling-launch-angle-to-limit-damage/#:~:text=MLB%20Launch%20Angle%20Variable%20Importance,by%20Pitch%20Type).
This will greatly improve the realism of the launch angles produced by
your simulation engine.

**Sources:**

- Powers, S. (2016). *“Toward a Probability Distribution Over
  Batted-Ball Trajectories.”* The Hardball Times – Saberseminar
  presentation. (Found that launch angle is well-modeled by a normal
  distribution; estimated batter/pitcher-specific LA means and
  variances)[\[1\]](https://tht.fangraphs.com/toward-a-probability-distribution-over-batted-ball-trajectories/#:~:text=Focusing%20first%20on%20launch%20angle%2C,batter%2C%20pitcher%20and%20other%20factors)[\[3\]](https://tht.fangraphs.com/toward-a-probability-distribution-over-batted-ball-trajectories/#:~:text=My%20conclusion%20is%20that%20a,more%20closely%20a%20normal%20distribution).
- Albert, J. (2024). *“Modeling to Extract a Player’s Competitive
  Swings.”* BaseballwithR blog. (Demonstrates using a normal mixture
  model to separate good vs. poor contact distributions in exit
  velocity, a concept extendable to launch
  angles)[\[17\]](https://baseballwithr.wordpress.com/2024/07/29/modeling-to-extract-a-players-competitive-swings/#:~:text=velocities%20of%20batter%20swings%20are,competitive%20swings)[\[18\]](https://baseballwithr.wordpress.com/2024/07/29/modeling-to-extract-a-players-competitive-swings/#:~:text=When%20I%20read%20this%20Twitter,two%20normal%20curves%20sampling%20distribution).
- Thurm, N. (2020). *“Controlling Launch Angle to Limit Damage.”*
  FanGraphs Community Research. (Highlights that launch angle
  distributions are much wider than exit velo; emphasizes extreme launch
  angles are suboptimal and influenced by pitch
  height)[\[5\]](https://community.fangraphs.com/controlling-launch-angle-to-limit-damage/#:~:text=most%20important%20predictor%20of%20a,this%20idea%20at%20great%20length)[\[12\]](https://community.fangraphs.com/controlling-launch-angle-to-limit-damage/#:~:text=MLB%20Launch%20Angle%20Variable%20Importance,by%20Pitch%20Type).
- Statcast Analytics (2019–2021). MLB Statcast hitting leaderboards and
  research findings (e.g. average LA ~12°, with ~43% GB (\<10°), ~21% LD
  (10–25°), ~36% FB (≥25°) in
  2019)[\[4\]](https://www.rotoballer.com/using-sabermetrics-for-fantasy-baseball-hitter-batted-ball-distribution/838542#:~:text=Distribution%20www,fly%20balls).
  These data underline the broad spread of launch angles and the
  prevalence of tail outcomes in actual play.

------------------------------------------------------------------------

[\[1\]](https://tht.fangraphs.com/toward-a-probability-distribution-over-batted-ball-trajectories/#:~:text=Focusing%20first%20on%20launch%20angle%2C,batter%2C%20pitcher%20and%20other%20factors)
[\[3\]](https://tht.fangraphs.com/toward-a-probability-distribution-over-batted-ball-trajectories/#:~:text=My%20conclusion%20is%20that%20a,more%20closely%20a%20normal%20distribution)
[\[19\]](https://tht.fangraphs.com/toward-a-probability-distribution-over-batted-ball-trajectories/#:~:text=Given%20that%20it%20is%20a,least%20squares%20with%20unknown%20variance)
[\[20\]](https://tht.fangraphs.com/toward-a-probability-distribution-over-batted-ball-trajectories/#:~:text=match%20at%20L611%20The%20table,his%20former%20Reds%20teammate%2C%20Todd)
[\[26\]](https://tht.fangraphs.com/toward-a-probability-distribution-over-batted-ball-trajectories/#:~:text=The%20strategy%20is%20first%20to,product%20of%20these%20two%20distributions)
[\[29\]](https://tht.fangraphs.com/toward-a-probability-distribution-over-batted-ball-trajectories/#:~:text=Image%3A%20This%20heatmap%20shows%20the,%28via%20Scott%20Powers)
[\[30\]](https://tht.fangraphs.com/toward-a-probability-distribution-over-batted-ball-trajectories/#:~:text=distance%20from%20the%20origin%20in,Let%E2%80%99s%20see%20the%20full%20version)
Toward a Probability Distribution Over Batted-Ball Trajectories \| The
Hardball Times

<https://tht.fangraphs.com/toward-a-probability-distribution-over-batted-ball-trajectories/>

[\[2\]](https://lup.lub.lu.se/student-papers/record/9175631/file/9175632.pdf#:~:text=reasonable%20with%20smoother%20and%20more,distribution%2C%20peaking%20around%2010%20degrees)
Exploring Factors Influencing On-Base Percentage in Modern Baseball

<https://lup.lub.lu.se/student-papers/record/9175631/file/9175632.pdf>

[\[4\]](https://www.rotoballer.com/using-sabermetrics-for-fantasy-baseball-hitter-batted-ball-distribution/838542#:~:text=Distribution%20www,fly%20balls)
Using Sabermetrics for Fantasy Baseball: Hitter Batted Ball Distribution

<https://www.rotoballer.com/using-sabermetrics-for-fantasy-baseball-hitter-batted-ball-distribution/838542>

[\[5\]](https://community.fangraphs.com/controlling-launch-angle-to-limit-damage/#:~:text=most%20important%20predictor%20of%20a,this%20idea%20at%20great%20length)
[\[6\]](https://community.fangraphs.com/controlling-launch-angle-to-limit-damage/#:~:text=launch%20angles%20are%20centered%20much,for%20a%20guy%20with%20Gallo%E2%80%99s)
[\[7\]](https://community.fangraphs.com/controlling-launch-angle-to-limit-damage/#:~:text=%E2%80%9Cdeflecting%E2%80%9D%20batted%20balls%20to%20extreme,edge%20produce%20lower%20wOBA%20at)
[\[11\]](https://community.fangraphs.com/controlling-launch-angle-to-limit-damage/#:~:text=on%20a%20number%20of%20different,statistical%20significance%20to%20launch%20angle)
[\[12\]](https://community.fangraphs.com/controlling-launch-angle-to-limit-damage/#:~:text=MLB%20Launch%20Angle%20Variable%20Importance,by%20Pitch%20Type)
Controlling Launch Angle To Limit Damage \| Community Blog

<https://community.fangraphs.com/controlling-launch-angle-to-limit-damage/>

[\[8\]](https://github.com/jlundgrenedge/baseball/blob/0387122663d8501ea8473b26037fa4680793baeb/docs/ANGLE_DEPENDENT_SPIN_CALIBRATION.md#L24-L29)
ANGLE_DEPENDENT_SPIN_CALIBRATION.md

<https://github.com/jlundgrenedge/baseball/blob/0387122663d8501ea8473b26037fa4680793baeb/docs/ANGLE_DEPENDENT_SPIN_CALIBRATION.md>

[\[9\]](https://github.com/jlundgrenedge/baseball/blob/0387122663d8501ea8473b26037fa4680793baeb/docs/PHASE2_SUMMARY.md#L280-L284)
[\[10\]](https://github.com/jlundgrenedge/baseball/blob/0387122663d8501ea8473b26037fa4680793baeb/docs/PHASE2_SUMMARY.md#L198-L203)
PHASE2_SUMMARY.md

<https://github.com/jlundgrenedge/baseball/blob/0387122663d8501ea8473b26037fa4680793baeb/docs/PHASE2_SUMMARY.md>

[\[13\]](https://github.com/jlundgrenedge/baseball/blob/0387122663d8501ea8473b26037fa4680793baeb/batted_ball/player.py#L546-L554)
[\[14\]](https://github.com/jlundgrenedge/baseball/blob/0387122663d8501ea8473b26037fa4680793baeb/batted_ball/player.py#L550-L558)
[\[15\]](https://github.com/jlundgrenedge/baseball/blob/0387122663d8501ea8473b26037fa4680793baeb/batted_ball/player.py#L531-L539)
[\[21\]](https://github.com/jlundgrenedge/baseball/blob/0387122663d8501ea8473b26037fa4680793baeb/batted_ball/player.py#L559-L567)
player.py

<https://github.com/jlundgrenedge/baseball/blob/0387122663d8501ea8473b26037fa4680793baeb/batted_ball/player.py>

[\[16\]](https://github.com/jlundgrenedge/baseball/blob/0387122663d8501ea8473b26037fa4680793baeb/batted_ball/at_bat.py#L1118-L1124)
[\[22\]](https://github.com/jlundgrenedge/baseball/blob/0387122663d8501ea8473b26037fa4680793baeb/batted_ball/at_bat.py#L880-L888)
[\[23\]](https://github.com/jlundgrenedge/baseball/blob/0387122663d8501ea8473b26037fa4680793baeb/batted_ball/at_bat.py#L896-L905)
[\[27\]](https://github.com/jlundgrenedge/baseball/blob/0387122663d8501ea8473b26037fa4680793baeb/batted_ball/at_bat.py#L848-L856)
[\[28\]](https://github.com/jlundgrenedge/baseball/blob/0387122663d8501ea8473b26037fa4680793baeb/batted_ball/at_bat.py#L860-L864)
at_bat.py

<https://github.com/jlundgrenedge/baseball/blob/0387122663d8501ea8473b26037fa4680793baeb/batted_ball/at_bat.py>

[\[17\]](https://baseballwithr.wordpress.com/2024/07/29/modeling-to-extract-a-players-competitive-swings/#:~:text=velocities%20of%20batter%20swings%20are,competitive%20swings)
[\[18\]](https://baseballwithr.wordpress.com/2024/07/29/modeling-to-extract-a-players-competitive-swings/#:~:text=When%20I%20read%20this%20Twitter,two%20normal%20curves%20sampling%20distribution)
Modeling to Extract a Player’s Competitive Swings \| Exploring Baseball
Data with R

<https://baseballwithr.wordpress.com/2024/07/29/modeling-to-extract-a-players-competitive-swings/>

[\[24\]](https://fantasy.fangraphs.com/lets-talk-about-launch-angle-tightness/#:~:text=Yesterday%2C%20I%20finally%20followed%20up,EV)
[\[25\]](https://fantasy.fangraphs.com/lets-talk-about-launch-angle-tightness/#:~:text=2019%20twitter)
Let’s Talk About Launch Angle “Tightness” \| RotoGraphs Fantasy Baseball

<https://fantasy.fangraphs.com/lets-talk-about-launch-angle-tightness/>
