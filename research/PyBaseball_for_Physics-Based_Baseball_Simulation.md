# PyBaseball for Physics-Based Baseball Simulation

## Statcast Data Ingestion with PyBaseball

PyBaseball provides direct access to MLB’s Statcast data (via Baseball
Savant), which is crucial for physics-based simulations. The library can
pull **pitch-by-pitch Statcast records** that include a rich array of
advanced metrics: pitch type, pitch velocity, spin rate, release and
plate coordinates, batted ball exit velocity, launch angle, hit
distance, and outcome of play, among many
others[\[1\]](https://github.com/jldbc/pybaseball#:~:text=%27vx0%27%2C%20%27vy0%27%2C%20%27vz0%27%2C%20%27ax%27%2C%20%27ay%27%2C,pitch_name%27%2C%20%27home_score%27%2C%20%27away_score%27%2C%20%27bat_score%27%2C%20%27fld_score)[\[2\]](https://sabr.org/analytics/presentations/2025#:~:text=Our%20study%20will%20be%20utilizing,changes%20as%20this%20count%20increases).
In fact, the Statcast data returned by PyBaseball contains **dozens of
columns** per pitch (approximately 79 in recent versions), encompassing
everything from the pitcher’s release parameters and spin axis to the
batter’s results and **Statcast-derived expected stats** (e.g. estimated
batting average and wOBA based on launch
speed/angle)[\[1\]](https://github.com/jldbc/pybaseball#:~:text=%27vx0%27%2C%20%27vy0%27%2C%20%27vz0%27%2C%20%27ax%27%2C%20%27ay%27%2C,pitch_name%27%2C%20%27home_score%27%2C%20%27away_score%27%2C%20%27bat_score%27%2C%20%27fld_score).
PyBaseball’s `statcast()` function allows querying this data by date
range (and even by team), returning **granular** data at the
single-pitch level – the finest granularity available for in-game
events[\[3\]](https://pypi.org/project/pybaseball/1.0.5/#:~:text=Statcast%20data%20include%20pitch,com)[\[4\]](https://jamesrledoux.com/projects/open-source/introducing-pybaseball/#:~:text=,release_speed%20%20release_pos_x%20%20release_pos_z).
This pitch-level detail is exactly what a physics-based simulation needs
for realism, as it includes the initial conditions for each pitch
(velocity vectors `vx0, vy0, vz0` and acceleration `ax, ay, az` of the
ball’s trajectory, release point, etc.) and the outcomes of ball-bat
collisions (launch speed/exit velocity and launch angle of batted
balls)[\[1\]](https://github.com/jldbc/pybaseball#:~:text=%27vx0%27%2C%20%27vy0%27%2C%20%27vz0%27%2C%20%27ax%27%2C%20%27ay%27%2C,pitch_name%27%2C%20%27home_score%27%2C%20%27away_score%27%2C%20%27bat_score%27%2C%20%27fld_score).

**Data availability and sources:** Statcast tracking was introduced
across all MLB ballparks in 2015 (after a trial run in
2014)[\[5\]](https://qiita.com/ussu_ussu_ussu/items/e6ed61bc863a0963150f#:~:text=%E4%BD%8D%E3%81%AB%E8%BC%9D%E3%81%8D%E3%81%BE%E3%81%97%E3%81%9F%E3%81%8C%E3%80%81%E7%AB%B6%E6%8A%80%E7%9A%84%E3%81%AA%E3%83%A9%E3%83%B3%E3%81%8C10%E6%9C%AC%E4%BB%A5%E4%B8%8A%E3%81%82%E3%82%8B%E9%81%B8%E6%89%8B%E3%81%A7Sprint%20Speed%E3%83%AA%E3%83%BC%E3%83%80%E3%83%BC%E3%83%9C%E3%83%BC%E3%83%89%E3%81%A7%E3%81%AF4%E4%BD%8D%E3%81%A7%E3%81%97%E3%81%9F%E3%80%82),
so Statcast data in PyBaseball is available from 2015 onward. For each
year since, PyBaseball can retrieve the full season’s pitch-by-pitch
data (though querying a full season in one go results in a very large
dataset). Under the hood, PyBaseball scrapes Baseball Savant’s Statcast
search API; it is **optimized with parallel requests** to improve speed,
but pulling large date ranges can still be
time-consuming[\[6\]](https://github.com/Jensen-holm/statcast-era-pitches#:~:text=Image%3A%20Latest%20Update).
In practice, users sometimes break queries into smaller time spans (e.g.
month-by-month) to manage size and avoid potential API timeouts.
PyBaseball will by default fetch yesterday’s games if no date is given,
but for bulk historical data you provide `start_dt` and `end_dt` (in
YYYY-MM-DD
format)[\[7\]](https://pypi.org/project/pybaseball/1.0.5/#:~:text=If%20,while%20it%20pulls%20the%20data).
Optionally, you can filter by a specific player or team: functions like
`statcast_batter()` and `statcast_pitcher()` accept a player’s MLBAM ID
to return only that player’s pitches or
at-bats[\[8\]](https://pypi.org/project/pybaseball/1.0.5/#:~:text=For%20a%20player,A%20complete%20example)[\[9\]](https://pypi.org/project/pybaseball/1.0.5/#:~:text=name_last%20name_first%20key_mlbam%20key_retro%20key_bbref,clayton%20477132%20kersc001%20kershcl01%202036).
(PyBaseball includes a `playerid_lookup` utility to find MLBAM IDs by
name[\[10\]](https://pypi.org/project/pybaseball/1.0.5/#:~:text=~~~~%20%3E%3E%3E%20,This%20may%20take%20a%20moment).)
This is useful if you want to **limit data to a particular player** for
attribute modeling. The returned Statcast data is provided as a pandas
DataFrame, making it easy to inspect and manipulate. For example, one
can load an entire day or week of league-wide pitches and filter or
group the DataFrame as needed to feed a simulation model.

**Statcast metrics and granularity:** The breadth of Statcast metrics
accessible is a key strength. PyBaseball exposes essentially all fields
that Baseball Savant would include in a CSV
export[\[1\]](https://github.com/jldbc/pybaseball#:~:text=%27vx0%27%2C%20%27vy0%27%2C%20%27vz0%27%2C%20%27ax%27%2C%20%27ay%27%2C,pitch_name%27%2C%20%27home_score%27%2C%20%27away_score%27%2C%20%27bat_score%27%2C%20%27fld_score).
These include measurements relevant to **ball physics**, such as the
pitch’s **release speed and spin rate** (`release_speed`,
`release_spin_rate`), its trajectory data (`release_pos_x/y/z` and
velocity components, plus break and “pfx” movement in inches), and the
**ball-bat collision outcomes** like `launch_speed` (exit velocity off
the bat), `launch_angle`, and
`hit_distance_sc`[\[1\]](https://github.com/jldbc/pybaseball#:~:text=%27vx0%27%2C%20%27vy0%27%2C%20%27vz0%27%2C%20%27ax%27%2C%20%27ay%27%2C,pitch_name%27%2C%20%27home_score%27%2C%20%27away_score%27%2C%20%27bat_score%27%2C%20%27fld_score).
Each pitch record also notes the **event type** (`events` field, e.g.
single, groundout, home run) and the `description` (e.g. swinging
strike, hit into play), allowing you to connect the physics data to
baseball outcomes. Additional contextual data, such as which bases were
occupied, inning, score, and fielding alignment, are included as
well[\[11\]](https://github.com/jldbc/pybaseball#:~:text=%27fielder_7%27%2C%20%27fielder_8%27%2C%20%27fielder_9%27%2C%20%27release_pos_y%27%2C%20%27estimated_ba_using_speedangle%27%2C,if_fielding_alignment%27%2C%20%27of_fielding_alignment%27%2C%20%27spin_axis%27%2C%20%27delta_home_win_exp%27%2C%20%27delta_run_exp).
In short, PyBaseball gives a **complete snapshot of every pitch and its
result**, enabling simulations to incorporate real-world distributions
of pitch movement, velocity, and batted-ball characteristics. According
to Statcast documentation, this tracking covers essentially all aspects
of on-field action: **pitching metrics** (velocity, spin, movement),
**hitting metrics** (exit velo, launch angle, spray/hit location),
**running metrics** (sprint speed, base-to-base times), and **fielding
metrics** (throwing arm strength, catch probability, catcher pop
times)[\[12\]](https://qiita.com/ussu_ussu_ussu/items/e6ed61bc863a0963150f#:~:text=%E7%90%83%E3%81%AE%E8%BF%BD%E8%B7%A1%E3%81%AB%E5%B0%82%E7%94%A8%E3%81%95%E3%82%8C%E3%81%A6%E3%81%84%E3%81%BE%E3%81%99%E3%80%82%E3%81%93%E3%81%AE%E3%82%88%E3%82%8A%E5%A0%85%E7%89%A2%E3%81%AA%E3%82%B7%E3%82%B9%E3%83%86%E3%83%A0%E3%81%AB%E3%82%88%E3%82%8A%E3%80%81%E8%BF%BD%E8%B7%A1%E3%81%95%E3%82%8C%E3%82%8B%E6%89%93%E7%90%83%E3%81%AE%E5%89%B2%E5%90%88%E3%81%8C%E7%B4%8489%EF%BC%85%E3%81%8B%E3%82%8999%EF%BC%85%E3%81%AB%E5%90%91%E4%B8%8A%E3%81%97%E3%81%BE%E3%81%97%E3%81%9F%E3%80%82).
PyBaseball’s Statcast interface focuses on the pitch and hit tracking
data; it captures the raw measurements from which running and fielding
metrics can be derived.

**Statcast leaderboards and advanced metrics:** Beyond raw
pitch-by-pitch feeds, PyBaseball also offers convenience functions to
fetch **aggregated Statcast leaderboards** for certain advanced stats.
For example, one can retrieve the **Sprint Speed leaderboard** for a
given season via `statcast_sprint_speed(year, min_opp)` – which returns
players’ average sprint speeds (feet/second) with a given minimum number
of run
opportunities[\[13\]](https://qiita.com/ussu_ussu_ussu/items/e6ed61bc863a0963150f#:~:text=1%E7%A7%92%E3%81%AE%E3%82%A6%E3%82%A3%E3%83%B3%E3%83%89%E3%82%A6%E3%81%A7%E7%B4%847%E5%9B%9E%E3%81%AE%E5%85%A8%E5%8A%9B%E3%81%AE%E3%82%B9%E3%83%88%E3%83%A9%E3%82%A4%E3%83%89%E3%82%92%E3%82%AD%E3%83%A3%E3%83%97%E3%83%81%E3%83%A3%E3%81%99%E3%82%8B%E3%81%93%E3%81%A8%E3%81%8C%E3%81%A7%E3%81%8D%E3%82%8B%E3%81%9F%E3%82%81%E3%80%81Sprint%20Speed%E3%81%AF%E9%95%B7%E6%99%82%E9%96%93%E3%81%AB%E3%82%8F%E3%81%9F%E3%81%A3%E3%81%A6%E9%80%9F%E5%BA%A6%E3%82%92%E7%B6%AD%E6%8C%81%E3%81%A7%E3%81%8D%E3%82%8B%E4%BA%BA%E3%82%92%E5%A0%B1%E3%82%8F%E3%82%8C%E3%81%BE%E3%81%99%E3%80%82).
(Sprint Speed is an advanced running metric representing a player’s peak
running speed, measured as the average of their top sustained one-second
bursts in competitive
runs[\[14\]](https://qiita.com/ussu_ussu_ussu/items/e6ed61bc863a0963150f#:~:text=%E3%83%BB%E6%9C%80%E9%AB%98%E8%B5%B0%E5%8A%9B%EF%BC%88Sprint%20Speed%EF%BC%89%EF%BC%9A%E3%83%97%E3%83%AC%E3%83%BC%E3%83%A4%E3%83%BC%E3%81%AE%E6%9C%80%E9%AB%98%E8%B5%B0%E5%8A%9B%E3%82%92%E6%B8%AC%E5%AE%9A%E3%81%97%E3%81%9F%E3%82%82%E3%81%AE%E3%81%A7%E3%80%81%E3%80%8C1%E7%A7%92%E9%96%93%E3%81%A7%E3%81%AE%E6%9C%80%E5%A4%A7%E8%B5%B0%E8%A1%8C%E8%B7%9D%E9%9B%A2%E3%80%8D%E3%81%A7%E8%A1%A8%E3%81%95%E3%82%8C%E3%81%BE%E3%81%99%E3%80%82%E3%81%93%E3%82%8C%E3%81%AF%E5%80%8B%E3%80%85%E3%81%AE%E3%83%97%E3%83%AC%E3%82%A4%E3%81%A7%E6%8F%90%E4%BE%9B%E3%81%95%E3%82%8C%E3%82%8B%E5%A0%B4%E5%90%88%E3%81%A8%E3%80%81%E3%82%B7%E3%83%BC%20%E3%82%BA%E3%83%B3%E5%B9%B3%E5%9D%87%E3%81%A7%E6%8F%90%E4%BE%9B%E3%81%95%E3%82%8C%E3%81%BE%E3%81%99%E3%80%82%E3%82%B7%E3%83%BC%E3%82%BA%E3%83%B3%E5%B9%B3%E5%9D%87%E3%81%AF%E3%80%81%E3%81%99%E3%81%B9%E3%81%A6%E3%81%AE%E9%81%A9%E6%A0%BC%E3%81%AA%E3%83%A9%E3%83%B3%EF%BC%88%E7%8F%BE%E5%9C%A8%E3%81%AF2%E5%A1%81%E4%BB%A5%E4%B8%8A%E3%81%A7%E6%9C%AC%E5%A1%81%E6%89%93%E3%82%92%E9%99%A4%E3%81%8F%EF%BC%89%E3%82%92%E8%A6%8B%E3%81%A4%E3%81%91%E3%80%81%E4%B8%8A%E4%BD%8D50%EF%BC%85%E3%81%AE%E5%B9%B3%E5%9D%87%E5%80%A4%E3%82%92%E8%A8%88%E7%AE%97%E3%81%99%E3%82%8B%E3%81%93%E3%81%A8%E3%81%A7%E5%BE%97%E3%82%89%E3%82%8C%E3%81%BE%E3%81%99%E3%80%82Sprint%20Speed%E3%81%AF%E3%80%81%E6%89%93%E8%80%85%E3%80%81%E5%AE%88%E5%82%99%E3%80%81%E3%83%A9%E3%83%B3%E3%83%8A%E3%83%BC%E3%81%AE%E3%81%84%E3%81%9A%E3%82%8C%E3%81%8B%E3%81%AB%E5%AF%BE%E3%81%97%E3%81%A6%E6%B8%AC%E5%AE%9A%E3%81%95%E3%82%8C%E3%81%BE%E3%81%99%E3%80%82).)
PyBaseball similarly can pull leaderboards for **Exit Velocity & Barrel
rates**, which list hitters’ average exit velos, hard-hit percentages,
and barrel percentages for a season (these correspond to the Baseball
Savant leaderboards for quality of contact). Other Statcast-driven
rankings, like **Outs Above Average (OAA)** for fielders or **“Bat
Tracking” metrics** (e.g. bat swing speed and swing length, newly
available from late 2023), have been integrated as well. In fact,
PyBaseball is actively updated to include new Statcast metrics; for
instance, an update in mid-2024 added support for the **Bat Tracking**
data and fixed the OAA leaderboard
access[\[15\]](https://github.com/jldbc/pybaseball/commits#:~:text=Commits%20on%20Jun%2016%2C%202024).
This means you can programmatically get things like a list of hitters’
average **bat swing speeds** or a list of fielders with their cumulative
OAA, directly through PyBaseball functions. All such data is pulled from
Baseball Savant’s public leaderboards, ensuring you have **the same
advanced stats that MLB teams and Statcast provide publicly** – ready to
be used for creating player attributes.

**Data limitations:** It’s important to note a few limitations in using
Statcast data via PyBaseball. First, data coverage begins in 2015; any
historical simulations before that would lack Statcast’s advanced
metrics (you’d have to rely on other stats for earlier eras).
Additionally, some Statcast metrics have evolved over time. For example,
fields like `spin_dir`, `spin_rate_deprecated` and `break_angle` appear
in older data but have been supplanted by more modern measurements like
`spin_axis` in newer
data[\[16\]](https://github.com/jldbc/pybaseball#:~:text=Index%28,hc_y%27%2C%20%27tfs_deprecated%27%2C%20%27tfs_zulu_deprecated%27%2C%20%27fielder_2%27%2C%20%27umpire)[\[17\]](https://github.com/jldbc/pybaseball#:~:text=%27post_home_score%27%2C%20%27post_bat_score%27%2C%20%27post_fld_score%27%2C%20%27if_fielding_alignment%27%2C%20%27of_fielding_alignment%27%2C,spin_axis).
When modeling physics, one should ensure consistency — e.g. using the
current `release_spin_rate` and `spin_axis` for recent years, as those
reflect Statcast’s improved Hawkeye tracking since 2020. Another
consideration is **query performance**: pulling an entire season
(hundreds of thousands of pitch records) can be slow. The PyBaseball
developers have implemented parallel scraping to speed it up, but even
so, large data requests “may be time
consuming”[\[6\]](https://github.com/Jensen-holm/statcast-era-pitches#:~:text=Image%3A%20Latest%20Update).
Users often mitigate this by caching data or using smaller incremental
updates (a community example even set up a pipeline to auto-fetch weekly
Statcast updates and store them for faster
reuse[\[18\]](https://github.com/Jensen-holm/statcast-era-pitches#:~:text=pybaseball%20is%20a%20great%20tool,it%20can%20be%20time%20consuming)).
Finally, because PyBaseball essentially scrapes the Baseball Savant
site, it is somewhat at the mercy of that site’s availability and
format. In practice, it’s quite reliable for moderate use, but for
**very large-scale simulations** (e.g. repeatedly sampling from years of
Statcast data), you’ll want to design around repeated web calls – either
by storing the data locally or using PyBaseball’s output to build your
own database of pitch metrics.

## Deriving Player Attributes from Advanced Stats

With Statcast data in hand, one can construct a **detailed player
attribute system** that reflects real advanced metrics. PyBaseball’s
data gives access to virtually all the modern “statcast-era” stats that
teams use to evaluate skills, allowing you to map those into simulation
attributes. Here are some major categories of player attributes and how
they can be derived or **enriched by Statcast metrics**:

- **Hitting Power:** Statcast’s **exit velocity** measures and related
  stats indicate a player’s raw power. Using PyBaseball, you can get a
  hitter’s average and maximum exit velocity, as well as their
  **Hard-Hit%** (percentage of balls hit ≥95 mph) and **Barrel rate**
  (optimal combination of exit velo and launch
  angle)[\[19\]](https://pitcherlist.com/going-deep-the-real-value-of-statcast-data-part-i/#:~:text=List%20pitcherlist,launch%20angle%20between%2026).
  These translate to a power attribute – e.g. a hitter with a high
  average exit velo and barrel% would have a high power rating in the
  simulation. Because PyBaseball can retrieve **every batted ball’s exit
  speed and launch angle** for a player, you could even model power as a
  distribution rather than a single value (for instance, sampling exit
  velos from the player’s real distribution during the ball-bat
  collision in the simulation). Statcast also provides **estimated
  outcomes** like expected batting average and wOBA on contact (xBA,
  xwOBA) based on quality of
  contact[\[20\]](https://github.com/jldbc/pybaseball#:~:text=%27fielder_7%27%2C%20%27fielder_8%27%2C%20%27fielder_9%27%2C%20%27release_pos_y%27%2C%20%27estimated_ba_using_speedangle%27%2C,post_bat_score%27%2C%20%27post_fld_score%27%2C%20%27if_fielding_alignment%27%2C%20%27of_fielding_alignment%27%2C%20%27spin_axis);
  these can serve as aggregate measures of how effective a player’s
  contact is, supplementing the power attribute with quality-of-contact
  info.

- **Hitting Contact/Discipline:** To model a player’s ability to make
  contact and avoid strikeouts (or draw walks), you can leverage both
  Statcast and other advanced stats accessible via PyBaseball. Statcast
  pitch-level data lets you see every swing and miss a batter had (via
  the `description` field for strike swings, and outcome fields). By
  aggregating that, or more directly by using PyBaseball’s **FanGraphs
  batting stats**, you can obtain a batter’s **contact rate, strikeout
  rate, walk rate, chase rate**, etc. PyBaseball’s `batting_stats()`
  function pulls **299 features per player-season from
  FanGraphs**[\[21\]](https://jamesrledoux.com/projects/open-source/introducing-pybaseball/#:~:text=Similarly%2C%20if%20you%20want%20player,functions),
  including plate discipline metrics (O-Swing%, Z-Contact%, overall
  Contact%,
  etc.)[\[22\]](https://jamesrledoux.com/projects/open-source/introducing-pybaseball/).
  These metrics can form the basis of attributes like
  **Vision/Discipline** (how well a batter avoids chasing bad pitches)
  and **Contact skill** (how often they put the bat on the ball). For
  example, a batter with a high contact% and low whiff rate would get a
  boost in a “contact” attribute in the simulation, meaning they are
  less likely to strike out in your physics model of at-bats. In a
  physics simulation, you might implement this by adjusting the
  probability of the bat making contact given a swing, based on the
  player’s real swing-and-miss rates.

- **Launch Angle Tendency:** Statcast provides each hitter’s **launch
  angle** for every batted ball. By examining this (e.g. average launch
  angle or distribution of launch angles), one could give players a
  trait for being ground-ball hitters vs. fly-ball hitters. A player
  with consistently low launch angles (and a high ground-ball rate)
  might have an attribute favoring low trajectories, whereas a slugger
  with a high launch angle (aiming for the fences) would have an
  attribute for hitting more balls in the air. PyBaseball’s data can be
  used to calculate these tendencies and thus influence the trajectory
  of batted balls in the simulation’s physics engine.

- **Running Speed:** Statcast’s **Sprint Speed** is the go-to metric for
  foot speed, and PyBaseball makes it easy to obtain. Sprint Speed is
  given in feet per second (ft/s) for each player (average of top
  speeds)[\[14\]](https://qiita.com/ussu_ussu_ussu/items/e6ed61bc863a0963150f#:~:text=%E3%83%BB%E6%9C%80%E9%AB%98%E8%B5%B0%E5%8A%9B%EF%BC%88Sprint%20Speed%EF%BC%89%EF%BC%9A%E3%83%97%E3%83%AC%E3%83%BC%E3%83%A4%E3%83%BC%E3%81%AE%E6%9C%80%E9%AB%98%E8%B5%B0%E5%8A%9B%E3%82%92%E6%B8%AC%E5%AE%9A%E3%81%97%E3%81%9F%E3%82%82%E3%81%AE%E3%81%A7%E3%80%81%E3%80%8C1%E7%A7%92%E9%96%93%E3%81%A7%E3%81%AE%E6%9C%80%E5%A4%A7%E8%B5%B0%E8%A1%8C%E8%B7%9D%E9%9B%A2%E3%80%8D%E3%81%A7%E8%A1%A8%E3%81%95%E3%82%8C%E3%81%BE%E3%81%99%E3%80%82%E3%81%93%E3%82%8C%E3%81%AF%E5%80%8B%E3%80%85%E3%81%AE%E3%83%97%E3%83%AC%E3%82%A4%E3%81%A7%E6%8F%90%E4%BE%9B%E3%81%95%E3%82%8C%E3%82%8B%E5%A0%B4%E5%90%88%E3%81%A8%E3%80%81%E3%82%B7%E3%83%BC%20%E3%82%BA%E3%83%B3%E5%B9%B3%E5%9D%87%E3%81%A7%E6%8F%90%E4%BE%9B%E3%81%95%E3%82%8C%E3%81%BE%E3%81%99%E3%80%82%E3%82%B7%E3%83%BC%E3%82%BA%E3%83%B3%E5%B9%B3%E5%9D%87%E3%81%AF%E3%80%81%E3%81%99%E3%81%B9%E3%81%A6%E3%81%AE%E9%81%A9%E6%A0%BC%E3%81%AA%E3%83%A9%E3%83%B3%EF%BC%88%E7%8F%BE%E5%9C%A8%E3%81%AF2%E5%A1%81%E4%BB%A5%E4%B8%8A%E3%81%A7%E6%9C%AC%E5%A1%81%E6%89%93%E3%82%92%E9%99%A4%E3%81%8F%EF%BC%89%E3%82%92%E8%A6%8B%E3%81%A4%E3%81%91%E3%80%81%E4%B8%8A%E4%BD%8D50%EF%BC%85%E3%81%AE%E5%B9%B3%E5%9D%87%E5%80%A4%E3%82%92%E8%A8%88%E7%AE%97%E3%81%99%E3%82%8B%E3%81%93%E3%81%A8%E3%81%A7%E5%BE%97%E3%82%89%E3%82%8C%E3%81%BE%E3%81%99%E3%80%82Sprint%20Speed%E3%81%AF%E3%80%81%E6%89%93%E8%80%85%E3%80%81%E5%AE%88%E5%82%99%E3%80%81%E3%83%A9%E3%83%B3%E3%83%8A%E3%83%BC%E3%81%AE%E3%81%84%E3%81%9A%E3%82%8C%E3%81%8B%E3%81%AB%E5%AF%BE%E3%81%97%E3%81%A6%E6%B8%AC%E5%AE%9A%E3%81%95%E3%82%8C%E3%81%BE%E3%81%99%E3%80%82).
  You can use this to assign a **speed rating** in the simulation – for
  instance, 30 ft/s (elite) corresponds to a top rating, while ~27 ft/s
  is
  average[\[23\]](https://baseballsavant.mlb.com/leaderboard/sprint_speed#:~:text=MLB,A%20Bolt%20is%20any).
  PyBaseball’s sprint speed leaderboard function provides this stat for
  all players, or you can get a specific player’s sprint speed from
  leaderboards. This metric would directly inform how fast a player runs
  the bases or covers ground in the field in the simulation. Moreover,
  Statcast running data can also tell you things like home-to-first
  times and distance covered (for fielders), although those might not be
  exposed via simple PyBaseball calls except in specific leaderboard
  tables. Still, Sprint Speed alone is a strong indicator for attributes
  like **base running aggressiveness** (faster players steal more) and
  **range** for fielders. For example, a center fielder with a Sprint
  Speed in the 98th percentile will have superior range in tracking down
  fly balls in your physics model.

- **Fielding Ability:** While fielding involves many factors (reaction,
  route, hands), Statcast has introduced metrics that quantify fielding
  performance. **Outs Above Average (OAA)** is a Statcast metric that
  measures how many outs a fielder saved relative to average, based on
  the difficulty of balls hit to them. PyBaseball can retrieve OAA
  leaderboards (for infielders or outfielders), which you could use as a
  baseline for a fielder’s range/fielding attribute. For instance, a
  shortstop with +15 OAA in a season is elite and would get a top
  fielding rating in the simulation, meaning the physics engine might
  give them higher probability to reach tough grounders. Additionally,
  Statcast directly measures **arm strength** for outfield throws
  (tracking the speed of the ball on throws). If available via
  PyBaseball (the Statcast fielding leaderboard often includes an
  average throw velocity for outfielders), this could map to an **arm
  strength attribute** for throwing physics (e.g. how fast a player can
  throw the ball, affecting relay times and likelihood of throwing out
  runners). **Catcher pop time** (time to throw to second on steal
  attempts) is another Statcast metric that could be used for a
  catcher’s defensive attribute. In short, PyBaseball’s access to
  advanced fielding metrics enables a much more nuanced representation
  of defensive skills than traditional stats. Instead of using only
  fielding percentage, a simulation can use OAA for range and arm
  strength from Statcast to truly differentiate fielders.

- **Pitching Velocity and Movement:** For pitchers, PyBaseball’s
  Statcast data allows you to build each pitcher’s **arsenal** with real
  physics parameters. Every pitch thrown is labeled by pitch type
  (fastball, slider, etc.) along with its **release speed, spin rate,
  and movement
  (pfx)**[\[24\]](https://github.com/jldbc/pybaseball#:~:text=%27description%27%2C%20%27spin_dir%27%2C%20%27spin_rate_deprecated%27%2C%20%27break_angle_deprecated%27%2C%20%27break_length_deprecated%27%2C,tfs_deprecated%27%2C%20%27tfs_zulu_deprecated%27%2C%20%27fielder_2%27%2C%20%27umpire%27%2C%20%27sv_id)[\[1\]](https://github.com/jldbc/pybaseball#:~:text=%27vx0%27%2C%20%27vy0%27%2C%20%27vz0%27%2C%20%27ax%27%2C%20%27ay%27%2C,pitch_name%27%2C%20%27home_score%27%2C%20%27away_score%27%2C%20%27bat_score%27%2C%20%27fld_score).
  This means you can derive a pitcher’s average fastball velocity, their
  typical spin rate on a curveball, the horizontal and vertical break of
  each pitch type, and even their release extension (how far forward
  they release the ball). All of these can become attributes or inputs
  to your physics simulator. For example, you might give each pitch type
  for a given pitcher specific initial velocity and spin values in the
  simulation matching his real averages. A pitcher like Jacob deGrom
  (with ~98–100 mph fastballs) would have an extremely high velocity
  attribute for fastballs, whereas a finesse pitcher might rate lower
  but have higher spin or movement attributes on breaking balls. The
  **spin rate** and spin axis from Statcast are particularly useful for
  physics: they determine the Magnus force on the ball, thus affecting
  its trajectory. Having those from PyBaseball means your simulation can
  realistically curve a pitcher’s pitches according to their real-life
  movement. Additionally, PyBaseball data includes **pitch vertical and
  horizontal release points** and
  extension[\[1\]](https://github.com/jldbc/pybaseball#:~:text=%27vx0%27%2C%20%27vy0%27%2C%20%27vz0%27%2C%20%27ax%27%2C%20%27ay%27%2C,pitch_name%27%2C%20%27home_score%27%2C%20%27away_score%27%2C%20%27bat_score%27%2C%20%27fld_score),
  which influence perceived velocity and release timing – you could
  incorporate these to differentiate a short-armer versus a long-strider
  in the simulation. Essentially, PyBaseball lets you create a pitcher
  profile such that each virtual pitch they throw in the simulation
  respects the real physical characteristics observed for that player.

- **Pitching Control and Strategy:** While Statcast directly measures
  the physical aspects, you can also derive **control/command
  attributes** by looking at outcomes. For instance, using PyBaseball
  one can filter a pitcher’s data for how often they hit the edges of
  the zone or the frequency of wild pitches, etc. You might use walk
  rate (BB/9 or BB%) from FanGraphs (accessible via PyBaseball’s
  pitching stats) as a proxy for control. Moreover, PyBaseball can fetch
  advanced pitching metrics like **whiff rate**, **chase rate**, and
  **“Stuff+”** (if you integrate with newer models) – these can be part
  of an attribute describing how dominant a pitcher’s stuff is beyond
  just speed/spin (Stuff+ is a metric that encapsulates pitch quality
  using physical characteristics; PyBaseball has added support for
  pulling some of these stats as
  well[\[25\]](https://github.com/jldbc/pybaseball/commits#:~:text=%2A%20,342)).
  For a simulation, you might use those to influence how often a pitcher
  gets swings and misses in the simulated game. For example, a high
  whiff rate in Statcast data means in your sim the batter is more
  likely to miss that pitcher’s pitch if the pitch is in the swing zone.

In summary, PyBaseball’s data enables constructing a **comprehensive
attribute system** grounded in real metrics. Each player’s
physics-related attributes – from how hard they hit the ball, to how
fast they run, to how much their curveball breaks – can be quantified by
Statcast stats that PyBaseball makes readily available. The granularity
means you aren’t limited to one-number ratings; you can derive
distributions or situational tendencies. For instance, you could notice
via Statcast that a certain hitter struggles against high-spin fastballs
(perhaps his exit velo is much lower on those) and bake that into an
attribute or a conditional behavior in the simulation. Nearly all
aspects of the game that a physics-based simulation would model (ball
trajectories, player movement, collision outcomes) have corresponding
Statcast metrics. PyBaseball acts as the bridge to get those metrics,
which you can then transform or combine into whatever rating system or
probability model your simulation uses.

## PyBaseball’s Role in Data Processing and Integration

Beyond data retrieval, PyBaseball provides tooling that helps with
**preprocessing and integrating data** for simulation purposes. The data
comes in clean **pandas DataFrame** format, which means you can
immediately join it with other sources or apply transformations (e.g.,
computing averages, percentiles, or binning values for attribute tiers).
For example, you might pull a season’s Statcast data for all players and
then use pandas groupby to compute each player’s average of a metric –
PyBaseball makes this trivial because all the data is in a consistent
tabular form. The library also ensures that key identifiers like player
IDs are available for merging. A typical workflow might involve using
`playerid_lookup` (as noted earlier) to get a player’s IDs, then using
those IDs to fetch data from multiple sources (Statcast, FanGraphs,
etc.), and finally merging on the ID or name. PyBaseball’s consistent
use of MLBAM IDs (and providing lookups to other ID systems like
Baseball Reference or FanGraphs IDs) is very handy for **combining
statcast data with other datasets**. For instance, you could merge
Statcast pitch data with a player’s season stats from FanGraphs (which
PyBaseball can also fetch) to have a single table with both per-pitch
metrics and overall stats.

Another aspect where PyBaseball helps is **lightweight analysis and
modeling support**. While it’s not a modeling library per se, it
includes some convenience functions and examples that can jump-start
analysis. For example, PyBaseball’s `statcast` function can take a
`team` parameter to filter by
team[\[7\]](https://pypi.org/project/pybaseball/1.0.5/#:~:text=If%20,while%20it%20pulls%20the%20data),
which simplifies preprocessing if your simulation needs team-specific
datasets. It also has functions to get **park factors**, standings, and
other contextual data that might feed a simulation engine (e.g.,
different stadium effects on ball flight). Notably, PyBaseball added
some **plotting utilities** (such as plotting pitch locations or strike
zones)[\[26\]](https://github.com/jldbc/pybaseball/commits#:~:text=Copy%20full%20SHA%20for%203e7a56a)
which, while geared toward analysis, can assist in visual validation of
your simulation inputs (for example, you might plot the distribution of
launch angles you got from data to ensure it looks reasonable before
using it in the sim). The community around PyBaseball has also shared
**notebooks and patterns** for using the data in analyses, which you can
repurpose for simulation prep. For instance, one could follow an example
of grouping Statcast data by pitch type to compute movement averages (as
done in some PyBaseball example notebooks) and use that to parameterize
pitch physics in a game.

PyBaseball doesn’t explicitly perform physics calculations – that part
is up to the simulation – but it **streamlines all the data wrangling**
so you can focus on the physics logic. It saves effort in data cleaning:
units are consistent (e.g., speeds in mph, distances in feet), and
missing data is usually minimal or indicated (you may still need to
handle the occasional `None` or zero for things like launch angle on
foul balls). The library also handles behind the scenes tasks like
encoding queries to the correct URLs, parsing CSVs/JSONs from Baseball
Savant, and even basic rate-limiting. This reliability means you can
integrate PyBaseball into a pipeline (even automated processes) to fetch
the latest data for a simulation. For example, a user on GitHub set up
an automated job to pull Statcast data weekly via PyBaseball and update
a dataset, precisely because PyBaseball made the scraping part
straightforward[\[6\]](https://github.com/Jensen-holm/statcast-era-pitches#:~:text=Image%3A%20Latest%20Update)[\[27\]](https://github.com/Jensen-holm/statcast-era-pitches#:~:text=The%20point%20of%20this%20repository,statcast%20pitch%20data%20in%20general).
In a simulation context, you might do something similar – periodically
refresh your player attributes from the latest stats by running
PyBaseball queries.

Moreover, PyBaseball’s support for **multiple sources** (Statcast,
FanGraphs, Baseball Reference, etc.) enables *integration of advanced
stats with traditional stats*. A physics-based sim might primarily rely
on Statcast metrics for the on-field physics, but you could still
incorporate other sabermetric indicators for things like player AI or
decision-making. For instance, using **FanGraphs WAR or wRC+**
(accessible via PyBaseball) could inform an AI manager which players are
generally better. PyBaseball has convenient calls for those (e.g.,
`batting_stats` for any year range, which includes wRC+, OPS, and even
Statcast-backed stats like HardHit% as seen in the data
pulled[\[28\]](https://www.pymc-labs.com/blog-posts/bayesian-marcel#:~:text=It%27s%20generally%20pretty%20easy%20to,player%20statistics%20for%20each%20season)).
This means your one Python library can feed both the physics engine
(with Statcast measurements) and the higher-level logic (with season
aggregates), without juggling different data tools.

In terms of **lightweight modeling**, PyBaseball’s contribution is
mainly providing **input data**, but it also sometimes computes simple
metrics. For example, the library might calculate park-adjusted stats or
split data if such endpoints exist. Community contributions have
extended PyBaseball to include things like **predicted stats** (the
mention of adding PitchingBot and Stuff+
stats[\[25\]](https://github.com/jldbc/pybaseball/commits#:~:text=%2A%20,342)
suggests that PyBaseball can fetch those advanced modeled metrics from
FanGraphs or other sources). If your simulation wanted to use a metric
like Stuff+ (which is a predictor of pitch effectiveness) instead of raw
spin/velo, PyBaseball now has you covered there as well. Essentially,
PyBaseball acts as a **one-stop data pipeline**: from raw Statcast
measurements to advanced sabermetric indicators, it provides a uniform
interface. This reduces the overhead in **data preprocessing** – tasks
like filtering relevant events, computing averages, or merging datasets
can be done with Pandas in a few lines once the data is fetched, as
opposed to writing custom web scrapers or manual CSV downloads.

Finally, PyBaseball is well-documented and supported by an active
community (via GitHub and a Discord channel), so if you are attempting
something like a full physics simulation and need an obscure data point,
there’s a good chance someone has advice on obtaining it through
PyBaseball. For example, if you wanted minor-league Statcast data or
historical PITCHf/x for pre-2015, PyBaseball’s community might point you
to Retrosheet or other modules (PyBaseball does have some Retrosheet
support for older pitch data, albeit without the modern metrics). For
everything in the Statcast era, PyBaseball is the toolkit that glues the
data to your simulation. It lets you prototype quickly – you can fetch a
sample of data (say one game’s worth of pitches) and plug it into your
physics model to test, and then scale up. The heavy lifting of data
acquisition and basic cleaning is handled, enabling you to devote more
effort to the simulation’s design and less to sourcing stats.

## Examples of PyBaseball in Action

To appreciate how PyBaseball can support stat-heavy and physics-based
projects, it’s worth looking at how others have utilized it in similar
contexts:

- **Research Analytics – Pitch-Level Analysis:** In a presentation at
  the 2025 SABR Analytics Conference, a group of students leveraged
  PyBaseball to obtain **pitch-level Statcast data** for
  analysis[\[2\]](https://sabr.org/analytics/presentations/2025#:~:text=Our%20study%20will%20be%20utilizing,changes%20as%20this%20count%20increases).
  They pulled detailed metrics like pitch type, release velocity, spin
  rate, and play outcomes for MLB games to develop a new metric
  examining how a pitcher’s effectiveness changes as a batter sees more
  of the same pitch in a
  game[\[2\]](https://sabr.org/analytics/presentations/2025#:~:text=Our%20study%20will%20be%20utilizing,changes%20as%20this%20count%20increases).
  This is a great example of using PyBaseball to feed a custom
  analytical model: the **granular Statcast inputs** (via PyBaseball)
  enabled the researchers to quantify a subtle game theory concept
  (pitch recognition over multiple exposures). In a simulation, one
  could similarly use PyBaseball-derived pitch data to model how a
  batter “learns” a pitch during a game.

- **New Metrics & Player Development Tools:** A recent community project
  introduced *Power Transfer Efficiency (PTE)* – a metric that evaluates
  how efficiently a hitter converts bat speed into exit
  velocity[\[29\]](https://medium.com/@t.curry14/power-transfer-efficiency-pte-a-smarter-way-to-measure-swing-efficiency-in-baseball-b54b158bd41e#:~:text=That%E2%80%99s%20where%20Power%20Transfer%20Efficiency,they%20get%20for%20their%20swing).
  The author combined Statcast exit velocity data (acquired with
  PyBaseball) with **Bat Tracking** data (Statcast’s measure of bat
  swing speed) to calculate PTE for
  players[\[30\]](https://medium.com/@t.curry14/power-transfer-efficiency-pte-a-smarter-way-to-measure-swing-efficiency-in-baseball-b54b158bd41e#:~:text=I%20combined%3A).
  They built an interactive dashboard to visualize it, showing how
  PyBaseball’s data can be integrated into new analytic tools. This
  project demonstrates that **advanced stat integration** goes beyond
  just using existing stats – PyBaseball provides the raw ingredients
  (exit velo, swing speed) so you can engineer novel metrics. In a
  simulation context, one might use PTE to differentiate hitters who
  have the same power but different swing efficiency, impacting how we
  simulate hits (e.g. one player might achieve a given exit velo with a
  slower swing, implying more room for error in timing). The fact that
  PyBaseball can pull both exit velocities and the new bat speed metrics
  was crucial for this kind of
  analysis[\[30\]](https://medium.com/@t.curry14/power-transfer-efficiency-pte-a-smarter-way-to-measure-swing-efficiency-in-baseball-b54b158bd41e#:~:text=I%20combined%3A).

- **Statcast-Driven Simulations and Models:** Members of the PyBaseball
  community have used the library to support simulation-style analysis.
  For example, one user archived Statcast pitch data into a ready-to-use
  dataset for modeling, noting that while PyBaseball could pull all the
  data, it was more efficient to cache it for repeated simulation
  runs[\[6\]](https://github.com/Jensen-holm/statcast-era-pitches#:~:text=Image%3A%20Latest%20Update)[\[27\]](https://github.com/Jensen-holm/statcast-era-pitches#:~:text=The%20point%20of%20this%20repository,statcast%20pitch%20data%20in%20general).
  Another example is a **data-driven simulation of game scenarios**: a
  high-school sabermetric project used a simulation approach to evaluate
  using an “opener” pitcher (citing the need for platoon advantages and
  using stats to model
  outcomes)[\[31\]](https://sabr.org/analytics/presentations/2025#:~:text=opener%2C%20particularly%20in%20a%20data,The%20results%20of).
  While not explicitly stated, a project like that would rely on
  PyBaseball to get the necessary inputs (pitcher stats, batter stats,
  matchup data) to feed into their multinomial logistic regression for
  plate appearance outcomes. Essentially, PyBaseball often features in
  the background of many fan and student projects that do **Monte Carlo
  simulations or what-if scenarios** in baseball, because it provides
  the foundational data (distributions of outcomes, averages, etc.)
  needed for those models.

- **Sabermetric Analysis and Machine Learning:** PyBaseball is also
  frequently used in machine learning projects that have parallels to
  simulation. For instance, a *Bayesian model to project player
  performance* (MARCEL with a Bayesian twist) used PyBaseball to gather
  three years of Statcast-era data for
  inputs[\[28\]](https://www.pymc-labs.com/blog-posts/bayesian-marcel#:~:text=It%27s%20generally%20pretty%20easy%20to,player%20statistics%20for%20each%20season).
  They specifically pulled **Hard Hit rates** for multiple seasons via
  PyBaseball’s batting stats function and used it in a predictive
  model[\[28\]](https://www.pymc-labs.com/blog-posts/bayesian-marcel#:~:text=It%27s%20generally%20pretty%20easy%20to,player%20statistics%20for%20each%20season).
  This underscores that PyBaseball is adept at delivering advanced stat
  aggregates (like HardHit%, which comes from Statcast data) for many
  players at once, which is invaluable for training models. A
  physics-based simulation could similarly train or calibrate its engine
  using historical Statcast data – for example, adjusting the drag or
  lift coefficients in a ball flight model by fitting it to Statcast’s
  observed distances – and PyBaseball would be the tool to fetch that
  empirical data.

- **Community Documentation and Examples:** The PyBaseball documentation
  and community forums (like the `pybaseball` Discord or subreddit)
  contain numerous snippets and examples that mirror what a simulation
  developer might need. There are examples of pulling data into a pandas
  DataFrame and doing quick calculations (e.g., finding the top 10% of
  exit velocities, or visualizing the strike zone heatmap for a
  pitcher). These serve as **reference implementations**. For instance,
  the **PyBaseball example notebooks** (in the GitHub repo) show how to
  get a player’s Statcast data and calculate things like their average
  launch angle or pitch usage. Developers of simulations can borrow
  these patterns to rapidly generate the inputs for their player
  attributes. The community’s emphasis on open-source means that if
  someone has done a similar project (like simulating a season or
  building a predictive model using Statcast), chances are they’ve
  shared their code or at least their approach, often involving
  PyBaseball for data. This collective knowledge can guide a
  physics-simulation project in using the library most effectively (for
  example, best practices like converting PyBaseball’s output to more
  simulation-friendly formats, or using PyBaseball alongside libraries
  like NumPy/Pandas to vectorize computations for speed).

In conclusion, PyBaseball acts as a **gateway to advanced baseball
data** that is perfectly suited for driving a physics-based simulation
and an advanced player attribute system. It abstracts away the hurdles
of data acquisition (from Statcast’s treasure trove of pitch and player
tracking data to FanGraphs’ comprehensive stats) and lets you focus on
modeling the game itself. With PyBaseball, all the critical inputs –
exit velocities, launch angles, spin rates, sprint speeds, and more –
are only a few lines of code
away[\[1\]](https://github.com/jldbc/pybaseball#:~:text=%27vx0%27%2C%20%27vy0%27%2C%20%27vz0%27%2C%20%27ax%27%2C%20%27ay%27%2C,pitch_name%27%2C%20%27home_score%27%2C%20%27away_score%27%2C%20%27bat_score%27%2C%20%27fld_score)[\[2\]](https://sabr.org/analytics/presentations/2025#:~:text=Our%20study%20will%20be%20utilizing,changes%20as%20this%20count%20increases).
This makes it feasible to create a simulation that is not only
statistically accurate but also **grounded in real physics**, since the
parameters come from real measurements. The library’s flexibility and
the community support mean that as Statcast and sabermetrics evolve (new
metrics, new technology), your simulation can easily keep pace by
pulling in the latest data. Whether you’re calculating how far a 30°
launch, 110 mph drive will carry, or determining if an outfielder with a
29 ft/s sprint can catch it, PyBaseball provides the empirical
foundation to simulate it with confidence. **By integrating PyBaseball,
a physics-based baseball simulation can achieve an unprecedented level
of realism and data-driven accuracy**, connecting the virtual game
tightly with the real-world stats that define modern baseball.

**Sources:**

- PyBaseball GitHub README and
  documentation[\[32\]](https://github.com/jldbc/pybaseball#:~:text=Statcast%3A%20Pull%20advanced%20metrics%20from,Major%20League%20Baseball%27s%20Statcast%20system)[\[1\]](https://github.com/jldbc/pybaseball#:~:text=%27vx0%27%2C%20%27vy0%27%2C%20%27vz0%27%2C%20%27ax%27%2C%20%27ay%27%2C,pitch_name%27%2C%20%27home_score%27%2C%20%27away_score%27%2C%20%27bat_score%27%2C%20%27fld_score)
- PyBaseball PyPI description (Statcast
  functionality)[\[3\]](https://pypi.org/project/pybaseball/1.0.5/#:~:text=Statcast%20data%20include%20pitch,com)[\[7\]](https://pypi.org/project/pybaseball/1.0.5/#:~:text=If%20,while%20it%20pulls%20the%20data)
- “Introducing pybaseball” by J. LeDoux – overview of data retrieved
  (Statcast,
  FanGraphs)[\[33\]](https://jamesrledoux.com/projects/open-source/introducing-pybaseball/#:~:text=reference,answer%20any%20baseball%20research%20question)[\[21\]](https://jamesrledoux.com/projects/open-source/introducing-pybaseball/#:~:text=Similarly%2C%20if%20you%20want%20player,functions)
- Statcast search CSV columns reference (via
  PyBaseball)[\[1\]](https://github.com/jldbc/pybaseball#:~:text=%27vx0%27%2C%20%27vy0%27%2C%20%27vz0%27%2C%20%27ax%27%2C%20%27ay%27%2C,pitch_name%27%2C%20%27home_score%27%2C%20%27away_score%27%2C%20%27bat_score%27%2C%20%27fld_score)[\[11\]](https://github.com/jldbc/pybaseball#:~:text=%27fielder_7%27%2C%20%27fielder_8%27%2C%20%27fielder_9%27%2C%20%27release_pos_y%27%2C%20%27estimated_ba_using_speedangle%27%2C,if_fielding_alignment%27%2C%20%27of_fielding_alignment%27%2C%20%27spin_axis%27%2C%20%27delta_home_win_exp%27%2C%20%27delta_run_exp)
- SABR Conference 2025 presentation abstract – use of PyBaseball for
  pitch-level stat
  analysis[\[2\]](https://sabr.org/analytics/presentations/2025#:~:text=Our%20study%20will%20be%20utilizing,changes%20as%20this%20count%20increases)
- Qiita Statcast memo – Statcast metrics tracked (pitching, hitting,
  running,
  fielding)[\[12\]](https://qiita.com/ussu_ussu_ussu/items/e6ed61bc863a0963150f#:~:text=%E7%90%83%E3%81%AE%E8%BF%BD%E8%B7%A1%E3%81%AB%E5%B0%82%E7%94%A8%E3%81%95%E3%82%8C%E3%81%A6%E3%81%84%E3%81%BE%E3%81%99%E3%80%82%E3%81%93%E3%81%AE%E3%82%88%E3%82%8A%E5%A0%85%E7%89%A2%E3%81%AA%E3%82%B7%E3%82%B9%E3%83%86%E3%83%A0%E3%81%AB%E3%82%88%E3%82%8A%E3%80%81%E8%BF%BD%E8%B7%A1%E3%81%95%E3%82%8C%E3%82%8B%E6%89%93%E7%90%83%E3%81%AE%E5%89%B2%E5%90%88%E3%81%8C%E7%B4%8489%EF%BC%85%E3%81%8B%E3%82%8999%EF%BC%85%E3%81%AB%E5%90%91%E4%B8%8A%E3%81%97%E3%81%BE%E3%81%97%E3%81%9F%E3%80%82)
- Reddit r/Sabermetrics discussion – note on PyBaseball Statcast
  high-level data
  access[\[34\]](https://www.reddit.com/r/Sabermetrics/comments/fkk1f4/pybaseball_easy_to_use_python_statcast_data/#:~:text=As%20a%20heads%20up%20to,do%20your%20own%20leg%20work)
- GitHub (Jensen-holm) – commentary on PyBaseball scraping performance
  and data
  updates[\[6\]](https://github.com/Jensen-holm/statcast-era-pitches#:~:text=Image%3A%20Latest%20Update)[\[27\]](https://github.com/Jensen-holm/statcast-era-pitches#:~:text=The%20point%20of%20this%20repository,statcast%20pitch%20data%20in%20general)
- Medium article by T. Curry (2025) – PTE metric using PyBaseball + Bat
  Tracking
  data[\[30\]](https://medium.com/@t.curry14/power-transfer-efficiency-pte-a-smarter-way-to-measure-swing-efficiency-in-baseball-b54b158bd41e#:~:text=I%20combined%3A)
- PyMC Labs blog – using PyBaseball’s stats in a Bayesian model (Hard
  Hit
  example)[\[28\]](https://www.pymc-labs.com/blog-posts/bayesian-marcel#:~:text=It%27s%20generally%20pretty%20easy%20to,player%20statistics%20for%20each%20season)
- Baseball Savant Leaderboards (MLB.com) – definitions of Sprint Speed
  and power
  metrics[\[23\]](https://baseballsavant.mlb.com/leaderboard/sprint_speed#:~:text=MLB,A%20Bolt%20is%20any)[\[19\]](https://pitcherlist.com/going-deep-the-real-value-of-statcast-data-part-i/#:~:text=List%20pitcherlist,launch%20angle%20between%2026)

------------------------------------------------------------------------

[\[1\]](https://github.com/jldbc/pybaseball#:~:text=%27vx0%27%2C%20%27vy0%27%2C%20%27vz0%27%2C%20%27ax%27%2C%20%27ay%27%2C,pitch_name%27%2C%20%27home_score%27%2C%20%27away_score%27%2C%20%27bat_score%27%2C%20%27fld_score)
[\[11\]](https://github.com/jldbc/pybaseball#:~:text=%27fielder_7%27%2C%20%27fielder_8%27%2C%20%27fielder_9%27%2C%20%27release_pos_y%27%2C%20%27estimated_ba_using_speedangle%27%2C,if_fielding_alignment%27%2C%20%27of_fielding_alignment%27%2C%20%27spin_axis%27%2C%20%27delta_home_win_exp%27%2C%20%27delta_run_exp)
[\[16\]](https://github.com/jldbc/pybaseball#:~:text=Index%28,hc_y%27%2C%20%27tfs_deprecated%27%2C%20%27tfs_zulu_deprecated%27%2C%20%27fielder_2%27%2C%20%27umpire)
[\[17\]](https://github.com/jldbc/pybaseball#:~:text=%27post_home_score%27%2C%20%27post_bat_score%27%2C%20%27post_fld_score%27%2C%20%27if_fielding_alignment%27%2C%20%27of_fielding_alignment%27%2C,spin_axis)
[\[20\]](https://github.com/jldbc/pybaseball#:~:text=%27fielder_7%27%2C%20%27fielder_8%27%2C%20%27fielder_9%27%2C%20%27release_pos_y%27%2C%20%27estimated_ba_using_speedangle%27%2C,post_bat_score%27%2C%20%27post_fld_score%27%2C%20%27if_fielding_alignment%27%2C%20%27of_fielding_alignment%27%2C%20%27spin_axis)
[\[24\]](https://github.com/jldbc/pybaseball#:~:text=%27description%27%2C%20%27spin_dir%27%2C%20%27spin_rate_deprecated%27%2C%20%27break_angle_deprecated%27%2C%20%27break_length_deprecated%27%2C,tfs_deprecated%27%2C%20%27tfs_zulu_deprecated%27%2C%20%27fielder_2%27%2C%20%27umpire%27%2C%20%27sv_id)
[\[32\]](https://github.com/jldbc/pybaseball#:~:text=Statcast%3A%20Pull%20advanced%20metrics%20from,Major%20League%20Baseball%27s%20Statcast%20system)
GitHub - jldbc/pybaseball: Pull current and historical baseball
statistics using Python (Statcast, Baseball Reference, FanGraphs)

<https://github.com/jldbc/pybaseball>

[\[2\]](https://sabr.org/analytics/presentations/2025#:~:text=Our%20study%20will%20be%20utilizing,changes%20as%20this%20count%20increases)
[\[31\]](https://sabr.org/analytics/presentations/2025#:~:text=opener%2C%20particularly%20in%20a%20data,The%20results%20of)
2025 SABR Analytics Conference: Research Presentations – Society for
American Baseball Research

<https://sabr.org/analytics/presentations/2025>

[\[3\]](https://pypi.org/project/pybaseball/1.0.5/#:~:text=Statcast%20data%20include%20pitch,com)
[\[7\]](https://pypi.org/project/pybaseball/1.0.5/#:~:text=If%20,while%20it%20pulls%20the%20data)
[\[8\]](https://pypi.org/project/pybaseball/1.0.5/#:~:text=For%20a%20player,A%20complete%20example)
[\[9\]](https://pypi.org/project/pybaseball/1.0.5/#:~:text=name_last%20name_first%20key_mlbam%20key_retro%20key_bbref,clayton%20477132%20kersc001%20kershcl01%202036)
[\[10\]](https://pypi.org/project/pybaseball/1.0.5/#:~:text=~~~~%20%3E%3E%3E%20,This%20may%20take%20a%20moment)
pybaseball · PyPI

<https://pypi.org/project/pybaseball/1.0.5/>

[\[4\]](https://jamesrledoux.com/projects/open-source/introducing-pybaseball/#:~:text=,release_speed%20%20release_pos_x%20%20release_pos_z)
[\[21\]](https://jamesrledoux.com/projects/open-source/introducing-pybaseball/#:~:text=Similarly%2C%20if%20you%20want%20player,functions)
[\[22\]](https://jamesrledoux.com/projects/open-source/introducing-pybaseball/)
[\[33\]](https://jamesrledoux.com/projects/open-source/introducing-pybaseball/#:~:text=reference,answer%20any%20baseball%20research%20question)
Introducing pybaseball: an Open Source Package for Baseball Data
Analysis - James LeDoux’s Blog

<https://jamesrledoux.com/projects/open-source/introducing-pybaseball/>

[\[5\]](https://qiita.com/ussu_ussu_ussu/items/e6ed61bc863a0963150f#:~:text=%E4%BD%8D%E3%81%AB%E8%BC%9D%E3%81%8D%E3%81%BE%E3%81%97%E3%81%9F%E3%81%8C%E3%80%81%E7%AB%B6%E6%8A%80%E7%9A%84%E3%81%AA%E3%83%A9%E3%83%B3%E3%81%8C10%E6%9C%AC%E4%BB%A5%E4%B8%8A%E3%81%82%E3%82%8B%E9%81%B8%E6%89%8B%E3%81%A7Sprint%20Speed%E3%83%AA%E3%83%BC%E3%83%80%E3%83%BC%E3%83%9C%E3%83%BC%E3%83%89%E3%81%A7%E3%81%AF4%E4%BD%8D%E3%81%A7%E3%81%97%E3%81%9F%E3%80%82)
[\[12\]](https://qiita.com/ussu_ussu_ussu/items/e6ed61bc863a0963150f#:~:text=%E7%90%83%E3%81%AE%E8%BF%BD%E8%B7%A1%E3%81%AB%E5%B0%82%E7%94%A8%E3%81%95%E3%82%8C%E3%81%A6%E3%81%84%E3%81%BE%E3%81%99%E3%80%82%E3%81%93%E3%81%AE%E3%82%88%E3%82%8A%E5%A0%85%E7%89%A2%E3%81%AA%E3%82%B7%E3%82%B9%E3%83%86%E3%83%A0%E3%81%AB%E3%82%88%E3%82%8A%E3%80%81%E8%BF%BD%E8%B7%A1%E3%81%95%E3%82%8C%E3%82%8B%E6%89%93%E7%90%83%E3%81%AE%E5%89%B2%E5%90%88%E3%81%8C%E7%B4%8489%EF%BC%85%E3%81%8B%E3%82%8999%EF%BC%85%E3%81%AB%E5%90%91%E4%B8%8A%E3%81%97%E3%81%BE%E3%81%97%E3%81%9F%E3%80%82)
[\[13\]](https://qiita.com/ussu_ussu_ussu/items/e6ed61bc863a0963150f#:~:text=1%E7%A7%92%E3%81%AE%E3%82%A6%E3%82%A3%E3%83%B3%E3%83%89%E3%82%A6%E3%81%A7%E7%B4%847%E5%9B%9E%E3%81%AE%E5%85%A8%E5%8A%9B%E3%81%AE%E3%82%B9%E3%83%88%E3%83%A9%E3%82%A4%E3%83%89%E3%82%92%E3%82%AD%E3%83%A3%E3%83%97%E3%83%81%E3%83%A3%E3%81%99%E3%82%8B%E3%81%93%E3%81%A8%E3%81%8C%E3%81%A7%E3%81%8D%E3%82%8B%E3%81%9F%E3%82%81%E3%80%81Sprint%20Speed%E3%81%AF%E9%95%B7%E6%99%82%E9%96%93%E3%81%AB%E3%82%8F%E3%81%9F%E3%81%A3%E3%81%A6%E9%80%9F%E5%BA%A6%E3%82%92%E7%B6%AD%E6%8C%81%E3%81%A7%E3%81%8D%E3%82%8B%E4%BA%BA%E3%82%92%E5%A0%B1%E3%82%8F%E3%82%8C%E3%81%BE%E3%81%99%E3%80%82)
[\[14\]](https://qiita.com/ussu_ussu_ussu/items/e6ed61bc863a0963150f#:~:text=%E3%83%BB%E6%9C%80%E9%AB%98%E8%B5%B0%E5%8A%9B%EF%BC%88Sprint%20Speed%EF%BC%89%EF%BC%9A%E3%83%97%E3%83%AC%E3%83%BC%E3%83%A4%E3%83%BC%E3%81%AE%E6%9C%80%E9%AB%98%E8%B5%B0%E5%8A%9B%E3%82%92%E6%B8%AC%E5%AE%9A%E3%81%97%E3%81%9F%E3%82%82%E3%81%AE%E3%81%A7%E3%80%81%E3%80%8C1%E7%A7%92%E9%96%93%E3%81%A7%E3%81%AE%E6%9C%80%E5%A4%A7%E8%B5%B0%E8%A1%8C%E8%B7%9D%E9%9B%A2%E3%80%8D%E3%81%A7%E8%A1%A8%E3%81%95%E3%82%8C%E3%81%BE%E3%81%99%E3%80%82%E3%81%93%E3%82%8C%E3%81%AF%E5%80%8B%E3%80%85%E3%81%AE%E3%83%97%E3%83%AC%E3%82%A4%E3%81%A7%E6%8F%90%E4%BE%9B%E3%81%95%E3%82%8C%E3%82%8B%E5%A0%B4%E5%90%88%E3%81%A8%E3%80%81%E3%82%B7%E3%83%BC%20%E3%82%BA%E3%83%B3%E5%B9%B3%E5%9D%87%E3%81%A7%E6%8F%90%E4%BE%9B%E3%81%95%E3%82%8C%E3%81%BE%E3%81%99%E3%80%82%E3%82%B7%E3%83%BC%E3%82%BA%E3%83%B3%E5%B9%B3%E5%9D%87%E3%81%AF%E3%80%81%E3%81%99%E3%81%B9%E3%81%A6%E3%81%AE%E9%81%A9%E6%A0%BC%E3%81%AA%E3%83%A9%E3%83%B3%EF%BC%88%E7%8F%BE%E5%9C%A8%E3%81%AF2%E5%A1%81%E4%BB%A5%E4%B8%8A%E3%81%A7%E6%9C%AC%E5%A1%81%E6%89%93%E3%82%92%E9%99%A4%E3%81%8F%EF%BC%89%E3%82%92%E8%A6%8B%E3%81%A4%E3%81%91%E3%80%81%E4%B8%8A%E4%BD%8D50%EF%BC%85%E3%81%AE%E5%B9%B3%E5%9D%87%E5%80%A4%E3%82%92%E8%A8%88%E7%AE%97%E3%81%99%E3%82%8B%E3%81%93%E3%81%A8%E3%81%A7%E5%BE%97%E3%82%89%E3%82%8C%E3%81%BE%E3%81%99%E3%80%82Sprint%20Speed%E3%81%AF%E3%80%81%E6%89%93%E8%80%85%E3%80%81%E5%AE%88%E5%82%99%E3%80%81%E3%83%A9%E3%83%B3%E3%83%8A%E3%83%BC%E3%81%AE%E3%81%84%E3%81%9A%E3%82%8C%E3%81%8B%E3%81%AB%E5%AF%BE%E3%81%97%E3%81%A6%E6%B8%AC%E5%AE%9A%E3%81%95%E3%82%8C%E3%81%BE%E3%81%99%E3%80%82)
pybaseball - MLB statcastについて : メモ \#HiÐΞ - Qiita

<https://qiita.com/ussu_ussu_ussu/items/e6ed61bc863a0963150f>

[\[6\]](https://github.com/Jensen-holm/statcast-era-pitches#:~:text=Image%3A%20Latest%20Update)
[\[18\]](https://github.com/Jensen-holm/statcast-era-pitches#:~:text=pybaseball%20is%20a%20great%20tool,it%20can%20be%20time%20consuming)
[\[27\]](https://github.com/Jensen-holm/statcast-era-pitches#:~:text=The%20point%20of%20this%20repository,statcast%20pitch%20data%20in%20general)
GitHub - Jensen-holm/statcast-era-pitches: Automatic updates for the
statcast-era-pitches HuggingFace dataset

<https://github.com/Jensen-holm/statcast-era-pitches>

[\[15\]](https://github.com/jldbc/pybaseball/commits#:~:text=Commits%20on%20Jun%2016%2C%202024)
[\[25\]](https://github.com/jldbc/pybaseball/commits#:~:text=%2A%20,342)
[\[26\]](https://github.com/jldbc/pybaseball/commits#:~:text=Copy%20full%20SHA%20for%203e7a56a)
Commits · jldbc/pybaseball · GitHub

<https://github.com/jldbc/pybaseball/commits>

[\[19\]](https://pitcherlist.com/going-deep-the-real-value-of-statcast-data-part-i/#:~:text=List%20pitcherlist,launch%20angle%20between%2026)
Going Deep: The Real Value of Statcast Data Part I \| Pitcher List

<https://pitcherlist.com/going-deep-the-real-value-of-statcast-data-part-i/>

[\[23\]](https://baseballsavant.mlb.com/leaderboard/sprint_speed#:~:text=MLB,A%20Bolt%20is%20any)
Statcast Sprint Speed Leaderboard \| baseballsavant.com - MLB.com

<https://baseballsavant.mlb.com/leaderboard/sprint_speed>

[\[28\]](https://www.pymc-labs.com/blog-posts/bayesian-marcel#:~:text=It%27s%20generally%20pretty%20easy%20to,player%20statistics%20for%20each%20season)
Bayesian Baseball Monkeys

<https://www.pymc-labs.com/blog-posts/bayesian-marcel>

[\[29\]](https://medium.com/@t.curry14/power-transfer-efficiency-pte-a-smarter-way-to-measure-swing-efficiency-in-baseball-b54b158bd41e#:~:text=That%E2%80%99s%20where%20Power%20Transfer%20Efficiency,they%20get%20for%20their%20swing)
[\[30\]](https://medium.com/@t.curry14/power-transfer-efficiency-pte-a-smarter-way-to-measure-swing-efficiency-in-baseball-b54b158bd41e#:~:text=I%20combined%3A)
Power Transfer Efficiency (PTE): A Smarter Way to Measure Swing
Efficiency in Baseball \| by Tyler Curry \| Medium

<https://medium.com/@t.curry14/power-transfer-efficiency-pte-a-smarter-way-to-measure-swing-efficiency-in-baseball-b54b158bd41e>

[\[34\]](https://www.reddit.com/r/Sabermetrics/comments/fkk1f4/pybaseball_easy_to_use_python_statcast_data/#:~:text=As%20a%20heads%20up%20to,do%20your%20own%20leg%20work)
PyBaseball: Easy to Use Python Statcast Data : r/Sabermetrics

<https://www.reddit.com/r/Sabermetrics/comments/fkk1f4/pybaseball_easy_to_use_python_statcast_data/>
