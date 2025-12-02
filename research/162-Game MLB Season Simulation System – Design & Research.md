# 162-Game MLB Season Simulation System -- Design & Research

## 1. Schedule Generation

Designing a realistic 162-game MLB schedule requires balancing numerous
constraints. Each of the 30 teams must play 162 games (81 home, 81 away)
with a roughly even distribution of opponents and series. In real MLB
schedules, teams face division rivals and interleague opponents in
specific frequencies, and practical constraints (travel, home stands)
are
considered[\[1\]](https://punkrockor.com/2017/10/05/sports-scheduling-meetings-business-analytics-why-scheduling-major-league-baseball-is-really-hard/#:~:text=,have%20a%20day%20off%20in).
For our simulation, we can implement a **round-robin scheduling
algorithm** with added MLB-specific constraints: - **Round-Robin Base**:
Use a rotation method to generate a baseline where each team plays every
other team a certain number of times. A classic approach is to fix one
team and rotate the others to create each round of
matchups[\[2\]](https://github.com/jlundgrenedge/baseball/blob/cf0ac9ff8c3218364a8618d45cffb60c13595f42/tests/archive/test_league_simulation.py#L148-L156).
This ensures every pair of teams meets. - **Series Structure**: Group
games into series of 2-4 games to mimic MLB's week-long home/away flows.
For each pair of teams, split their games into two series (one home, one
away) as evenly as
possible[\[3\]](https://github.com/jlundgrenedge/baseball/blob/cf0ac9ff8c3218364a8618d45cffb60c13595f42/tests/archive/test_league_simulation.py#L221-L230).
For example, if Team A and Team B are slated for 6 games, create one
series with Team A home (perhaps 3 games) and one with Team B home (3
games). - **Home/Away Balance**: Verify each team has 81 home and 81
away
games[\[4\]](https://punkrockor.com/2017/10/05/sports-scheduling-meetings-business-analytics-why-scheduling-major-league-baseball-is-really-hard/#:~:text=,and%20one%20away%20each%20time).
The schedule generator should count games per team and adjust if an
imbalance appears (e.g. by flipping a home/away designation in some
interleague series if needed). - **Series Sequencing**: After generating
all series, shuffle the order of series to produce a season-long
sequence[\[5\]](https://github.com/jlundgrenedge/baseball/blob/cf0ac9ff8c3218364a8618d45cffb60c13595f42/tests/archive/test_league_simulation.py#L233-L240).
This randomization avoids having the same opponents clustered and
creates a more realistic flow (e.g. teams rotate through opponents over
the season). - **Additional Constraints**: Optionally incorporate rules
such as no team having an excessively long road trip or homestand (MLB
aims for no more than 3 series in a row at home or
away)[\[1\]](https://punkrockor.com/2017/10/05/sports-scheduling-meetings-business-analytics-why-scheduling-major-league-baseball-is-really-hard/#:~:text=,have%20a%20day%20off%20in).
We might also ensure divisional matchups are spread across early, mid,
and late season (as MLB often schedules division opponents in multiple
phases)[\[6\]](https://punkrockor.com/2017/10/05/sports-scheduling-meetings-business-analytics-why-scheduling-major-league-baseball-is-really-hard/#:~:text=,have%20a%20day%20off%20in).
For an initial implementation, we can simplify by not modeling off-days
or travel explicitly (every team plays 162 games in a span of \~180 days
with periodic off-days). However, we should design the schedule data
structure to allow inserting off-days if needed later (e.g. a schedule
could be a list of **game days**, each containing a list of games).

**Implementation Approach**: We can create a `LeagueScheduler` class to
generate the schedule. The test suite already prototyped a scheduler for
a smaller league using a round-robin
algorithm[\[2\]](https://github.com/jlundgrenedge/baseball/blob/cf0ac9ff8c3218364a8618d45cffb60c13595f42/tests/archive/test_league_simulation.py#L148-L156)[\[7\]](https://github.com/jlundgrenedge/baseball/blob/cf0ac9ff8c3218364a8618d45cffb60c13595f42/tests/archive/test_league_simulation.py#L216-L225).
We can adapt that for 30 teams and 162 games: 1. **Determine Games per
Opponent**: In MLB's new balanced schedule (since 2023), each team plays
13 games against each division opponent and a set number against other
teams. We can encode these targets (e.g. 13 games vs 4 division rivals =
52, \~6 games vs each of 10 other league teams = 60, and 46 interleague
games). For simplicity, we might uniformly distribute games across all
other teams initially -- e.g. \~6 games vs each of the other 25 teams --
and then adjust to hit 162 total. 2. **Generate Matchup List**: Loop
through each unique pair of teams and assign the required number of
games. Split those games into two series (one at each home
park)[\[3\]](https://github.com/jlundgrenedge/baseball/blob/cf0ac9ff8c3218364a8618d45cffb60c13595f42/tests/archive/test_league_simulation.py#L221-L230).
For example, if Team X vs Team Y must play 7 games, create one series of
3 games with X home and one series of 4 games with Y home. This will
naturally enforce home/away splits. 3. **Assemble Season Calendar**:
Shuffle or interweave the series into a chronological
order[\[5\]](https://github.com/jlundgrenedge/baseball/blob/cf0ac9ff8c3218364a8618d45cffb60c13595f42/tests/archive/test_league_simulation.py#L233-L240).
A simple method is to randomize the series list and then iterate,
assigning each series a successive slot on the calendar. We may need to
avoid scheduling a team to play two series at the same time -- this is
solved by the fact that each series list only contains unique team
pairs. Optionally, we can organize the schedule week-by-week. For
example, generate series for each "week" such that no team appears twice
in the same week (this might involve a round-robin scheduling by weeks
approach). The test implementation provided a function to generate a
schedule by game days for an 8-team
league[\[8\]](https://github.com/jlundgrenedge/baseball/blob/cf0ac9ff8c3218364a8618d45cffb60c13595f42/tests/archive/test_league_simulation.py#L132-L140)[\[9\]](https://github.com/jlundgrenedge/baseball/blob/cf0ac9ff8c3218364a8618d45cffb60c13595f42/tests/archive/test_league_simulation.py#L158-L166),
which we can generalize to 30 teams. 4. **Verify and Refine**: After
generating the schedule, produce a summary of games per team to ensure
correctness. The prototype prints a schedule summary with total games
and home/away counts per
team[\[10\]](https://github.com/jlundgrenedge/baseball/blob/cf0ac9ff8c3218364a8618d45cffb60c13595f42/tests/archive/test_league_simulation.py#L270-L278)[\[11\]](https://github.com/jlundgrenedge/baseball/blob/cf0ac9ff8c3218364a8618d45cffb60c13595f42/tests/archive/test_league_simulation.py#L286-L294).
We should verify each team has 162 games and the intended home/away
balance. Minor adjustments (swapping home status on a series, etc.) can
correct any small imbalance.

By starting with a round-robin algorithm and then applying MLB-like
constraints, we can generate a **balanced 162-game schedule** for all
teams. The focus is on realism (teams play every opponent a reasonable
number of times, with series structure). Advanced constraints like
specific weekend home game requests or minimizing travel can be
incrementally added if needed. For now, a randomized series schedule
that meets the core numeric requirements will suffice for season
simulation.

## 2. Statistical Tracking Architecture

Tracking comprehensive statistics across an entire season is crucial for
evaluating player and team performance. We propose a robust architecture
for accumulating stats in batting, pitching, fielding, and team
categories, ensuring accuracy of attribution and support for split
breakdowns. The approach involves maintaining data structures for
**per-player stats** and **per-team stats**, updated in real-time as
games are simulated.

**Data Structures for Stats**: We can introduce dedicated classes or use
Python dataclasses to represent statistical accumulators: - *Player
batting stats*: For each hitter, track cumulative totals like games
played, plate appearances, at-bats, hits, doubles, triples, home runs,
runs, RBIs, walks, strikeouts, stolen bases, caught stealing, etc.
Calculate rate stats (AVG, OBP, SLG, OPS) on the fly or as needed from
these totals. - *Player pitching stats*: For each pitcher, track games
(and games started for starters), innings pitched (which can be tracked
in outs or thirds of an inning for precision), hits allowed, runs,
earned runs, home runs allowed, walks, strikeouts, wins, losses, saves,
holds, etc. This will enable computing ERA, WHIP, K/9, BB/9, etc. -
*Player fielding stats*: Initially track basic counts like errors,
assists, putouts for each fielder. Advanced fielding metrics (UZR, DRS)
require a more complex simulation of plays and are beyond initial scope,
but we can record plays made vs missed to later derive something
analogous to defensive runs saved. - *Team stats*: Team-level totals can
either be derived by summing players or tracked separately in a
`TeamStats` object that accumulates team performance. The repository's
test code defines a `TeamStats` dataclass that tracks wins, losses, runs
scored/allowed, hits, home runs, etc., for each
team[\[12\]](https://github.com/jlundgrenedge/baseball/blob/cf0ac9ff8c3218364a8618d45cffb60c13595f42/tests/archive/test_league_simulation.py#L58-L66)[\[13\]](https://github.com/jlundgrenedge/baseball/blob/cf0ac9ff8c3218364a8618d45cffb60c13595f42/tests/archive/test_league_simulation.py#L63-L70).
We will use a similar structure for MLB teams to compile season
standings and team totals. TeamStats can also keep derived stats like
run differential and per-game averages (the prototype includes
properties for winning percentage and runs per game, for
example[\[14\]](https://github.com/jlundgrenedge/baseball/blob/cf0ac9ff8c3218364a8618d45cffb60c13595f42/tests/archive/test_league_simulation.py#L79-L87)[\[15\]](https://github.com/jlundgrenedge/baseball/blob/cf0ac9ff8c3218364a8618d45cffb60c13595f42/tests/archive/test_league_simulation.py#L104-L112)).

We should integrate these structures with the simulation flow. One
design is to maintain dictionaries or maps: e.g.
`player_stats[hitter_id] = HitterStats(...)` and
`player_stats[pitcher_id] = PitcherStats(...)`, as well as
`team_stats[team_name] = TeamStats(...)`. As games are simulated, we
update both the involved teams' TeamStats and all players' individual
stats.

**In-Game Attribution Logic**: To ensure **attribution accuracy**, we
must update stats at the moment events occur in the simulation. The game
engine provides detailed outcome information each at-bat and play, which
we can hook into: - When an at-bat ends in a result (hit, walk,
strikeout, etc.), increment the batter's and pitcher's relevant
counters. For example, if the batter hits a double, increment the
batter's AB and H and 2B, increment the pitcher's hits allowed and
doubles allowed (if we track that), and so on. If it's a strikeout,
increment the pitcher's K and batter's strikeout
count[\[16\]](https://github.com/jlundgrenedge/baseball/blob/cf0ac9ff8c3218364a8618d45cffb60c13595f42/batted_ball/game_simulation.py#L718-L726).
The code already logs the outcome of each plate appearance, which we can
extend to update stats. - When runs score, attribute **runs scored** to
the players who scored, and **RBIs** to the batter who drove them in (if
applicable). The simulation's play-by-play data can tell us how many
runs scored on a play and the outcome type. For example, on a home run,
the batter gets an RBI for each run including themselves, and a run
scored for themselves. On a bases-clearing double, the batter gets 3
RBIs if three runners scored. - Fielding plays that result in outs or
errors should update fielding stats. If a fielder commits an error (the
`PlayResult.outcome` might be \"error\" or an event in the play log
indicates an error), increment that fielder's error count. If a double
play occurs, we might increment a DP-turn statistic for the players
involved (though tracking every assist/putout might be detailed for
later). - Pitching stats need careful handling for runs: only **earned
runs** count toward ERA. We can determine if a run is earned by checking
if an error occurred earlier in the inning before the run scored (a
typical baseball scoring rule). For initial simplicity, we might count
all runs as earned unless we mark an inning with an error. A more
accurate approach is to flag the GameState when an error happens and
then any run that scores after would be unearned until the inning
resets. - The simulation engine's `GameState` already tracks many
per-team stats for a game (hits, home runs, walks, etc. for each
side)[\[17\]](https://github.com/jlundgrenedge/baseball/blob/cf0ac9ff8c3218364a8618d45cffb60c13595f42/batted_ball/game_simulation.py#L184-L193)[\[18\]](https://github.com/jlundgrenedge/baseball/blob/cf0ac9ff8c3218364a8618d45cffb60c13595f42/batted_ball/game_simulation.py#L203-L211).
We will extend this by attributing those events to individual players.
For instance, `GameState.away_home_runs` tells how many homers the away
team hit; we can distribute those by incrementing the specific batters'
HR counts when they occur.

**Performance and Accuracy**: Updating stats incrementally after each
play or game is efficient given the scale (on the order of thousands of
events per game). Using in-memory dataclass objects for stats is fast
and keeps the code readable. Accuracy is ensured by updating at the
finest granularity (the moment a stat happens) rather than trying to
infer from box scores after the fact. We must double-check edge cases:
e.g., if a runner scores due to an error, that run should count in team
totals but not as an earned run for the pitcher, and the batter might
not get an RBI. Our stat update logic should mirror official scoring
rules. We may implement helper functions (like
`credit_run(batter, pitcher, earned=True, rbi=True)`) to encapsulate
these rules.

**Split Stats**: The architecture can accommodate splits (situational
statistics) if needed. For example, we can maintain separate stat
accumulators for vs. left-handed vs. right-handed pitchers, or home vs.
away games. A straightforward approach is to augment the player stat
structure with sub-dictionaries, e.g., `hitter_stats.splits['home']` and
`splits['away']`, each itself a HitterStats object tracking performance
in those conditions. Initially, we might not populate many splits, but
designing with this in mind will allow easy extension. For instance, if
the user wants to see a player's "home OPS" vs "away OPS", we could
calculate those if we've been tracking stats in each context.

In summary, we'll create comprehensive stat tracking objects and ensure
they are updated in the simulation loop. By the end of the season
simulation, we can output a full leaderboard of stats akin to
Baseball-Reference -- because we will have totals for every player
(which can be sorted to find league leaders in HR, batting average, ERA,
etc.), as well as team stats for standings and runs scored/allowed. This
forms the foundation for calculating advanced metrics as well.

## 3. Game Result Integration

The `GameResult` structure will be expanded to capture full **box
score** details for each game. Currently, `GameResult` (used in parallel
simulations) holds only high-level info like team names, final scores,
total hits, home runs,
etc.[\[19\]](https://github.com/jlundgrenedge/baseball/blob/cf0ac9ff8c3218364a8618d45cffb60c13595f42/batted_ball/parallel_game_simulation.py#L70-L78).
To produce season-level stats and allow per-game analysis, we need to
record granular game data in the result of each simulation.

**Extending GameResult**: We propose adding fields to `GameResult` to
include: - **Team line scores**: runs, hits, errors for both teams
(R/H/E, which are the basic lines in a box score). For example,
`away_hits` and `home_hits` fields (the simulation tracks these in
GameState, but they're not in GameResult yet). Similarly, `away_errors`
and `home_errors` should be stored. - **Individual player stat lines**:
This can be a nested structure. We can include a dictionary or list for
each team's batting and pitching results. For example: -
`GameResult.away_batting_stats` could be a list of stat lines for each
batter on the away team who appeared, with fields like AB, R, H, RBI,
BB, K, etc. - `GameResult.home_batting_stats` similarly for the home
team. - `GameResult.away_pitching_stats` for each pitcher on the away
team (in an NL game, away pitchers can bat too, but in the simulation
context we mostly treat them in pitching stats). -
`GameResult.home_pitching_stats` for home team pitchers. These can be
represented as lists of dictionaries or as lists of dataclass instances
(e.g., `PlayerGameStats` objects) for consistency. - **Game events or
highlights (optional)**: We might store a log of scoring plays or a
linescore by inning. While not strictly necessary for season stats, a
linescore (runs by inning) is part of a traditional box score. We can
derive it from play-by-play if needed, but it's a nice-to-have for
output completeness.

During simulation, we will collect these stats. One strategy is to
update a temporary box score structure as the game progresses. For
instance, as described in Section 2, every at-bat updates player and
team totals. We can accumulate those into per-game counters as well. By
the end of the game, we populate `GameResult.away_batting_stats` with
each away player's final line for that game (which we had been
tallying), and likewise for home players. The `GameSimulator` class
could maintain a mapping of player -\> game stats during the game and
then package it into the GameResult it returns.

**Integration with Existing Code**: We have to modify how `GameResult`
is constructed in the simulation. In the
`ParallelGameSimulator._simulate_single_game`, after the game finishes,
a `GameResult` is created with basic
info[\[19\]](https://github.com/jlundgrenedge/baseball/blob/cf0ac9ff8c3218364a8618d45cffb60c13595f42/batted_ball/parallel_game_simulation.py#L70-L78).
We should extend that to fill the new fields. The data is available
because the `GameSimulator` returns a final `GameState` (with team
totals) and, if we implement in-game stat tracking, we will have stored
the individual stats. We could attach the box score info to
`GameSimulator` or have `GameSimulator.simulate_game()` return not just
`GameState` but a detailed result object. A cleaner approach: create a
new object, say `BoxScore`, that is assembled as the game runs, and then
make `GameResult` include that `BoxScore`. For example:

    @dataclass
    class BoxScore:
        batting_stats: Dict[str, List[PlayerGameBattingStats]]
        pitching_stats: Dict[str, List[PlayerGamePitchingStats]]
        team_stats: Dict[str, Dict[str, int]]  # maybe a summary like {'R':..., 'H':..., 'E':...}

    @dataclass
    class GameResult:
        ...
        box_score: BoxScore

However, adding a large nested structure to `GameResult` increases
memory usage when simulating many games in parallel. To keep
performance, we might include this detailed info only when needed
(perhaps behind a flag). In a full 2430-game season sim, storing every
game's full box score in memory is feasible (2430 games \* \~50
players/game = \~121,500 player game entries, which is fine), but if we
simulate many seasons or very long series, we might want an option to
disable detailed box scores.

For our design, we assume one season at a time and proceed with full
detail.

**Utilizing Box Score Data**: Having per-game stat lines enables richer
analysis: - We can generate game logs for each team (the test's
TeamStats already stores game-by-game
scores[\[20\]](https://github.com/jlundgrenedge/baseball/blob/cf0ac9ff8c3218364a8618d45cffb60c13595f42/tests/archive/test_league_simulation.py#L75-L83),
which we can enhance by linking to the box score). - It allows verifying
our stat accumulation: summing all players' game stats over the season
should equal the season totals in our player_stats structures. - For
outputs, we could even print out a box score for a specific game or feed
this data to a visualization (e.g., generating a line score graphic or
text report for notable games).

In summary, we will expand `GameResult` to hold full box score
information, ensuring that every stat from a game is recorded. This
design aligns with producing outputs comparable to a site like
Baseball-Reference, where you can not only see season totals but also
examine each game's details. By capturing box scores, our simulation
system gains transparency and depth -- one can drill down from season
summary to individual game performance.

## 4. Advanced Metrics Calculation

With complete stat tracking in place, we can compute advanced
sabermetric metrics from the simulation outputs. Key metrics of interest
include **WAR (Wins Above Replacement)**, **wRC+ (Weighted Runs Created
Plus)**, **FIP (Fielding Independent Pitching)**, and potentially others
like OPS+, WHIP, or xwOBA. We will outline how to calculate these using
the season stats and some constants.

**Wins Above Replacement (WAR)**: WAR is a comprehensive metric that
combines batting, baserunning, and fielding value for position players
(and a different calculation for pitchers). The general formula for
position player WAR is:

$$\text{WAR} = \frac{\text{Batting Runs} + \text{Baserunning Runs} + \text{Fielding Runs} + \text{Positional Adjustment} + \text{League Adjustment} + \text{Replacement Runs}}{\text{Runs Per Win}}.$$

This is the formula used by FanGraphs for
WAR[\[21\]](https://library.fangraphs.com/war/war-position-players/#:~:text=WAR%20%3D%20,Runs%20Per%20Win).
To compute WAR in our simulation: - **Batting Runs**: We can derive this
from a player's offensive output relative to league average. A common
method is using wRAA (weighted runs above average) via wOBA (described
below under wRC+). Essentially, we estimate how many runs a player
contributed above an average hitter given their opportunities. -
**Baserunning Runs**: If our simulation tracks steals, caught stealing,
and possibly first-to-third advances (we might not track those
explicitly), we can approximate baserunning value. Initially, we could
incorporate stolen base runs (e.g., using run values for SB and CS from
linear weights) or simply ignore baserunning beyond SB/CS if its impact
is small in our sim. - **Fielding Runs**: This is challenging without a
sophisticated fielding model. As a placeholder, we might use errors or
basic fielding stats to penalize or credit players (e.g., each error
could be --2 runs, just as a rough estimate). However, a physics-based
sim could theoretically produce advanced fielding metrics (our sim
metrics system can compute Outs Above Average
probabilities[\[22\]](https://github.com/jlundgrenedge/baseball/blob/4269772e2752aa5ae28b697a1ed3d9d2680f7e1a/docs/guides/SIM_METRICS_GUIDE.md#L72-L80)[\[23\]](https://github.com/jlundgrenedge/baseball/blob/4269772e2752aa5ae28b697a1ed3d9d2680f7e1a/docs/guides/SIM_METRICS_GUIDE.md#L74-L78)).
For now, we might exclude fielding or use a very rough proxy. -
**Positional Adjustment**: WAR formulas include a fixed positional value
(e.g., a shortstop gets a +7.5 run adjustment, a first baseman gets
around --10 runs) to account for defensive position difficulty. We can
use standard values from MLB data. - **Replacement Runs**: This accounts
for the fact that a "replacement level" player is worse than average.
Typically, replacement level is set around 20 runs below average per 600
PA (which yields about 2 WAR for an average player over full time). We
can implement: Replacement Runs = (Plate Appearances of player / 600) \*
20 (adjusted by season run environment). This would be added to the
player's run value total so that we measure above replacement instead of
above average. - **Runs Per Win**: A conversion factor to turn runs into
wins. Commonly around 9 to 10 runs per win in modern MLB. We can
determine this from our simulation's run environment. For example, if
league runs per game is \~9 (as MLB is \~9.0 in
2022)[\[24\]](https://github.com/jlundgrenedge/baseball/blob/cf0ac9ff8c3218364a8618d45cffb60c13595f42/batted_ball/parallel_game_simulation.py#L140-L148),
we might use 9 or 10. We could also compute it by a Pythagorean approach
over the sim results.

Once we compute WAR components for each player, we can rank players by
WAR to see the simulation's MVPs. It's fine if our WAR doesn't exactly
match Baseball-Reference or FanGraphs (the prompt notes our WAR can be
approximate[\[25\]](file://file_000000004bb471f5a9156c5597b55a74#:~:text=%7C%20,LOW)[\[26\]](file://file_000000004bb471f5a9156c5597b55a74#:~:text=1.%20,need%20to%20match%20bWAR%2FfWAR%20exactly)),
but we want it directionally correct.

**Weighted Runs Created Plus (wRC+)**: wRC+ is a standardized metric for
offensive value, where 100 is league average and every point above/below
is a percent better/worse than average. Calculating wRC+ involves
several steps: 1. Compute **wOBA** for each player: wOBA (weighted
On-Base Average) assigns a run value to each offensive event (walk,
single, double, etc.). We will need weight constants, which are
typically derived from league data. For example, a common set (from
FanGraphs for a recent season) might be: NIBB (non-intentional walk)
\~0.7, 1B \~0.9, 2B \~1.24, 3B \~1.56, HR \~1.95, HBP \~0.72. We can use
MLB historical weights or derive from our simulation's overall scoring.
Since our physics-based outcomes should roughly mirror real run values,
using known constants is reasonable. The formula is:

$$wOBA = \frac{0.72 \times (BB - IBB) + 0.75 \times HBP + 0.90 \times 1B + 1.24 \times 2B + 1.56 \times 3B + 1.95 \times HR}{AB + BB - IBB + SF + HBP}.$$

(Weights can be adjusted to our environment.) 2. Compute **wRAA**
(Weighted Runs Above Average):

$$wRAA = \frac{wOBA - lgwOBA}{wOBA\_ Scale} \times PA,$$

where `lgwOBA` is league average wOBA and `wOBA_Scale` is a factor
(around 1.2) that converts a point of wOBA to runs. Essentially, wRAA
tells how many runs a player produced above an average player given the
same number of plate appearances. 3. Incorporate **Park Factor** (if
applicable): Our simulation might include different ballparks, but
unless we explicitly model them, we can ignore park adjustments
initially (assume neutral parks). 4. Finally,

$$wRC + = 100 \times \frac{(wRAA/PA + lgR/PA) + \left( lgR/PA - \text{ParkAdj} \right)}{lgR/PA},$$

where the term inside essentially compares the player's runs per PA to
the league's, including a park
adjustment[\[27\]](https://library.fangraphs.com/offense/wrc/#:~:text=wRC%2B%20%3D%20,100).
In simpler terms,

$$wRC + = 100 \times \frac{\text{player\_wOBA} - \text{lgwOBA}}{\text{wOBA\_Scale} \times \text{lgR/PA}}.$$

We will compute league averages from our sim output (total runs and
total PA give `lgR/PA`, and we already have `lgwOBA`). The result is an
index where 100 is average; e.g., a 120 wRC+ means 20% above average in
run creation. We need to be careful to exclude pitchers' hitting stats
if we want it comparable to real AL/NL wRC+, but since our sim likely
uses a DH or generic approach, we can treat all hitters together.

**Fielding Independent Pitching (FIP)**: FIP evaluates a pitcher on the
events they directly control -- strikeouts, walks, home runs (and HBPs)
-- ignoring balls in play. The formula for FIP is:

$$\text{FIP} = \frac{13 \times HR + 3 \times (BB + HBP) - 2 \times K}{IP} + C,$$

where *C* is a constant to adjust the scale to league
ERA[\[28\]](https://library.fangraphs.com/pitching/fip/#:~:text=Here%20is%20the%20formula%20for,FIP).
For our purposes: - We'll gather each pitcher's HR allowed, BB (walks)
issued, HBP, K, and innings pitched from the sim stats. - Compute the
numerator as `13*HR + 3*(BB+HBP) - 2*K`. - Divide by innings pitched (if
a pitcher has very few IP, FIP can be volatile, but that's expected). -
Add the constant *C*. The constant can be determined by comparing league
average of the fraction to league average ERA. Typically, *C* is around
3.1 in MLB to align FIP with ERA
scale[\[29\]](https://legacy.baseballprospectus.com/glossary/index.php?search=FIP#:~:text=View%20details%20for%20FIP%20,scale%20as%20earned%20run%20average).
We can derive *C* from our simulation: for example, calculate league FIP
without C and subtract it from league ERA. We might find a similar value
\~3.0 if our environment is MLB-like. - This gives each pitcher's FIP.
We can also compute an ERA- or FIP- (which are indexed to 100 like wRC+,
but that might be more detail than needed).

Using FIP will let us evaluate if a pitcher was effective independent of
fielding. It's a good check of our simulation's pitching realism too
(e.g., if a pitcher's ERA is far from FIP consistently, our fielding or
luck factors might be significant).

**Expected Stats (xStats)**: Our simulation outputs a lot of
Statcast-like data (exit velocity, launch angle, etc.), meaning we can
calculate metrics like **xwOBA** (expected wOBA), **xBA** (expected
batting average), and **xSLG**. In fact, the sim's debug system already
computes expected stats for each
contact[\[30\]](https://github.com/jlundgrenedge/baseball/blob/4269772e2752aa5ae28b697a1ed3d9d2680f7e1a/docs/guides/SIM_METRICS_GUIDE.md#L92-L100).
We can leverage those: - Accumulate expected outcomes for each player by
averaging the Statcast-based probabilities. For example, if a player had
100 batted balls with various quality, we could sum the expected hit and
HR probabilities to get an expected slash line. The
`SimMetricsCollector` provides values like xBA (chance a batted ball is
a hit) and xwOBA for each event; by aggregating those, we can produce
season-long xBA or xwOBA for each player. - xwOBA for a player could be
computed by taking each of their batted ball events and applying the
wOBA weights *by probability* instead of actual outcome. However, since
our simulation *decides* an outcome for each batted ball, we might
instead calculate xwOBA at the league level for calibration. A simpler
path: use real-world constants for xwOBA if the simulation environment
matches MLB. But given we have the raw data, we can do better by summing
the expected contributions of each event.

As an example, the sim can output something like: Player A had an
average exit velocity of 92 mph and average launch angle of 15°,
yielding an xBA of .310 and xSLG of .550 over the season, while their
actual BA was .300 and SLG .540. This information can be included in
reports to assess if players were lucky or unlucky in the sim.

**Additional Metrics**: We should also easily compute other common
sabermetrics: - **OPS+**: Compare on-base plus slugging to league
average (similar scale to wRC+ but simpler). - **BABIP**: Batting
average on balls in play, for both hitters and pitchers (to diagnose
luck). - **K% and BB%**: We can directly compute these from our totals
(they're part of standard outputs and help validate realism of strikeout
rates). - **WHIP**: (Walks + Hits per Inning Pitched) for pitchers,
straightforward from stats.

Many of these are either already partially in the code or can be added.
For example, the debug metrics note a high strikeout rate was an issue
that needed
tuning[\[31\]](https://github.com/jlundgrenedge/baseball/blob/4269772e2752aa5ae28b697a1ed3d9d2680f7e1a/batted_ball/player.py#L80-L88).
We'll ensure to calculate K/9 or K% and BB/9 to compare to MLB
benchmarks (target \~8.5 K/9, \~3.3 BB/9 in modern
MLB[\[32\]](https://github.com/jlundgrenedge/baseball/blob/4269772e2752aa5ae28b697a1ed3d9d2680f7e1a/batted_ball/player.py#L82-L88)).

In implementing these calculations, we will need certain
**constants**: - wOBA weight constants for the year (or simulate
environment). - wOBA scale and league run rate (from simulation
results). - FIP constant *C* (derive from sim). - Runs per win for WAR
(could assume \~9.5 or compute from sim's average runs/game). -
Positional adjustment values for WAR (from MLB averages).

We can hardcode typical values initially and later refine by using the
simulation's league averages (for example, if our simulated 2025 league
average runs/game is 8.8, we might use 9.0 runs/win instead of 10).

By adding functions to calculate these metrics at the end of the season
(e.g., a function `compute_advanced_metrics(player_stats, league_stats)`
that returns a structure with WAR, wRC+, etc.), we enrich the
simulation's output. The user will be able to see not just raw stats but
also how players perform in context -- who the simulation's MVPs and Cy
Youngs are by WAR, which hitters were most productive by wRC+, and how
pitchers fared in FIP vs ERA. This moves our output closer to
**Baseball-Reference/FanGraphs quality**: beyond the basic stats into
the sabermetric realm.

## 5. Season State Management

Managing the state of a full season simulation involves orchestrating
the schedule, updating standings and cumulative stats, and allowing the
process to be paused or resumed. We will design a **SeasonSimulation**
(or `LeagueSimulation`) class as the high-level coordinator that ties
together teams, schedule, and games.

**SeasonSimulation Class Responsibilities**: 1. **Initialize Teams and
Stats**: Before simulation, create team objects with rosters. For MLB,
we would load each team's roster from the database (e.g., via
`TeamDatabase.load_team_for_simulation`). Each team might be represented
by a `Team` class instance (as used in game simulation, containing
players and
lineup)[\[33\]](https://github.com/jlundgrenedge/baseball/blob/cf0ac9ff8c3218364a8618d45cffb60c13595f42/batted_ball/game_simulation.py#L292-L300).
We also initialize a `TeamStats` for each team to track W-L, runs, etc.
and prepare player stats structures for all players on those rosters.
This setup stage ensures we have all needed objects in memory. 2.
**Generate or Load Schedule**: Use the schedule generation from Section
1 to produce the list of games (each game defined by away team, home
team). Attach date indices or series info as needed. The
SeasonSimulation should hold this schedule (e.g., `self.schedule` as a
list of (away, home) pairs or a list of `Game` objects). 3. **Simulation
Loop**: Iterate through the schedule, simulating games in order. For
each game: - Retrieve the corresponding team objects for away and
home. - Ensure the correct starting pitchers and lineups are set for
that game (see Section 6 on pitcher rotation for how to pick the
starter). For example, call something like
`team.select_starting_pitcher()` to rotate the rotation. - Invoke the
game simulation. We might use the `ParallelGameSimulator` if running
games in parallel, but since we need to simulate sequentially day by day
to respect fatigue, we may simply use the single `GameSimulator` for
each game or a day's worth of games at a time. - Get the `GameResult`
(with expanded stats) from the simulation. - Update the season state:
increment wins/losses for the teams (if away_score \> home_score then
away_team wins, etc.), update team runs scored/allowed in TeamStats, and
add the game's stats to cumulative player and team stats. - If we
maintain a game log, append this result to the teams' game history
(e.g., TeamStats.game_scores
list[\[20\]](https://github.com/jlundgrenedge/baseball/blob/cf0ac9ff8c3218364a8618d45cffb60c13595f42/tests/archive/test_league_simulation.py#L75-L83)).
4. **Standings Tracking**: At any point, we can derive standings from
the TeamStats (which have wins, losses). We might maintain a sorted
standings table by division if needed. After each game or each day, we
could update games-behind calculations. A final standings report will be
produced after all games. 5. **Resume Capability**: To allow pausing and
resuming, the simulation state should be serializable. We can implement
a method to save state to disk (maybe as JSON or pickle). The state
would include: which games have been played (an index into the
schedule), current TeamStats and player stats, and perhaps the last-used
starting pitcher for each team (for rotation continuity). Since our
design uses deterministic schedule and tracking, we can safely pause
after any game. On resume, we load the state and continue from the next
game. This is important if a full 2430-game run (taking a couple hours)
needs to be split or if we want to inspect mid-season results. 6.
**Multi-threaded Execution**: To accelerate, we could simulate games in
parallel **by day**. On a given calendar day, all games scheduled that
day involve distinct teams, so they can be run concurrently without
interaction. The SeasonSimulation can group games by day and use a
thread pool or the existing `ParallelGameSimulator` to run those in
parallel, then aggregate results. The test `LeagueSimulation` example
shows grouping by matchup for bulk
simulation[\[34\]](https://github.com/jlundgrenedge/baseball/blob/cf0ac9ff8c3218364a8618d45cffb60c13595f42/tests/archive/test_league_simulation.py#L353-L355);
for our MLB sim, grouping by day is more appropriate to respect
chronological order. 7. **Post-season**: Although playoffs were a low
priority, the SeasonSimulation could optionally branch into a playoff
simulation after the regular season ends. That would involve taking top
teams from each division or wildcards and simulating bracketed series.
This can be modular and added later.

**Maintainable Simulation Loop**: The above responsibilities should be
divided logically: - `SeasonSimulation.setup()` handles loading teams
and schedule. - `SeasonSimulation.run()` handles iterating games. Within
this, consider breaking down the loop by days: e.g.,
`for day_games in schedule_by_day: simulate all games in day_games in parallel; update standings; increment day counter.`
This structure makes it easy to introduce days off or print daily
summaries. - Provide hooks or logging at key points. For example, after
each day, we might output a brief summary: "Day 42 complete: AL East
standings \..." for debugging or monitoring progress (especially if
running a multi-hour simulation).

We will also incorporate **fail-safes**: if a game simulation throws an
exception or a game runs extremely long (in innings), the loop should
handle it (perhaps skip or cap innings to avoid infinite games). This
ensures the season sim doesn't hang.

At the end of the season, we'll have final stats ready for output. The
SeasonSimulation class can have methods to output standings, league
leaders, etc., by reading from TeamStats and player stats. For example,
`SeasonSimulation.print_standings()` can print a sorted table of
wins/losses (similar to the test
output[\[35\]](https://github.com/jlundgrenedge/baseball/blob/cf0ac9ff8c3218364a8618d45cffb60c13595f42/tests/archive/LEAGUE_SIMULATION_README.md#L130-L138)),
and `print_league_leaders(category)` can list top 10 in any stat.

**State Management Example**: In the test 8-team season, they
implemented a `LeagueSimulation` class that demonstrates some of these
ideas: it creates teams, generates a schedule, and simulates a season,
printing final
standings[\[36\]](https://github.com/jlundgrenedge/baseball/blob/cf0ac9ff8c3218364a8618d45cffb60c13595f42/tests/archive/test_league_simulation.py#L312-L320)[\[37\]](https://github.com/jlundgrenedge/baseball/blob/cf0ac9ff8c3218364a8618d45cffb60c13595f42/tests/archive/test_league_simulation.py#L335-L343)[\[38\]](https://github.com/jlundgrenedge/baseball/blob/cf0ac9ff8c3218364a8618d45cffb60c13595f42/tests/archive/test_league_simulation.py#L345-L353).
We will mirror this pattern for 30 teams. One difference is that our
teams come from a database of real players rather than randomly
generated ones, but the orchestration remains similar.

**Pause/Resume Implementation**: A simple way is to periodically save
`SeasonSimulation` to a file. Python's pickle could serialize the object
if it's mostly dataclasses. Alternatively, we manually save important
parts: the current schedule index, team stats (which is just numbers),
and player stats (which could be large but still serializable as JSON if
we convert to dict). Resuming would reconstruct team and player objects;
since our simulation is deterministic given a state, this should be
reliable. For a first version, we might not implement a fully automated
resume, but design such that it's possible (for instance, avoid using
any global state that can't be reconstructed).

In summary, SeasonSimulation will serve as the **engine of the season**,
ensuring that all the moving parts (schedule, games, stats, standings)
work in concert. This design emphasizes maintainability: e.g., if we
want to change how lineups are chosen or incorporate injuries, we can
modify SeasonSimulation's loop logic without touching lower-level game
code. We also separate concerns: game simulation deals with one game;
season simulation deals with connecting games and tracking cumulative
outcomes. This structure will make the system easier to extend and
debug.

## 6. Pitcher Usage & Rotation Modeling

A realistic season simulation must model how teams use their pitching
staffs -- including a starting rotation, bullpen usage, and fatigue over
the season. We will implement logic to approximate MLB pitcher usage
patterns: - **Starting Rotation**: Most teams employ a 5-man rotation,
meaning five starting pitchers who take turns starting games, usually
with \~4 days rest between starts. We can represent this by ordering the
pitchers on each team marked as starters and cycling through them as
games progress. The `Team` class already distinguishes starters vs
relievers (it has an `is_starter` flag and methods to get starters
list)[\[39\]](https://github.com/jlundgrenedge/baseball/blob/cf0ac9ff8c3218364a8618d45cffb60c13595f42/batted_ball/game_simulation.py#L318-L325).
For each team, we will maintain an index or schedule for who the next
starter is. For example, each team object can have `next_start_index`
that cycles 0-4. Each time a team is scheduled to play, we set the
starting pitcher to `team.starters[next_start_index]` and then increment
that index modulo the number of starters. - We also need to ensure that
if a starter is injured or tired (not implemented in first version) we
could skip or adjust, but initially we assume no injuries and enough
rest. - Off-days: If our schedule includes off-days, some teams might
skip the 5th starter occasionally. We can incorporate a rule: if a team
had an off-day since its last game, it could start again from the top of
rotation (this is an advanced detail; initial implementation can ignore
this). - **Starter Fatigue and In-Game Removal**: The simulation's game
engine already reduces pitcher effectiveness as pitch count increases
(stamina)[\[40\]](https://github.com/jlundgrenedge/baseball/blob/4269772e2752aa5ae28b697a1ed3d9d2680f7e1a/batted_ball/player.py#L126-L134)[\[41\]](https://github.com/jlundgrenedge/baseball/blob/4269772e2752aa5ae28b697a1ed3d9d2680f7e1a/batted_ball/player.py#L162-L169).
We see that a pitcher's velocity and spin decline as `pitches_thrown`
approaches a stamina cap. However, the current game logic doesn't
automatically pull a tiring starter; it only enforces a pitching change
after a preset inning count
(`starter_innings`)[\[42\]](https://github.com/jlundgrenedge/baseball/blob/cf0ac9ff8c3218364a8618d45cffb60c13595f42/batted_ball/game_simulation.py#L658-L666).
We might refine in-game management: for example, if a starter's stamina
is below 20% or he has allowed many runs by the 5th inning, the AI could
bring in a reliever. This can be achieved by checking
`pitcher.pitches_thrown` or a fatigue metric each inning and deciding on
a change (the hooks for pitching change logic can be added around the
6th-7th inning). - Times Through Order: Real managers often remove
starters after they face the lineup 3 times. Our debug metrics track a
times-through-order
penalty[\[43\]](https://github.com/jlundgrenedge/baseball/blob/4269772e2752aa5ae28b697a1ed3d9d2680f7e1a/docs/guides/SIM_METRICS_GUIDE.md#L86-L94).
We could incorporate that by reducing pitcher effectiveness (already
done) or by using it as a signal to swap pitchers in simulation logic
(e.g., after 3rd time through and if some fatigue threshold is met,
trigger bullpen). - **Bullpen Usage**: Each team's remaining pitchers
(relievers) are used to finish games and cover days when starters can't
go. We model a simplified bullpen: - Assign relievers to roles or just
treat them as a group. A possible approach: always have one "long
reliever" who comes in if the starter is knocked out early, and one
"closer" for late innings of close games. However, we can start simpler:
choose a reliever at random (or based on who is most rested) when a
pitching change is needed. - Track reliever fatigue: We should prevent
the same reliever from pitching every single game. Implement a rest
system: after a reliever appears, mark them "unavailable" for the next
1-2 days depending on pitches thrown. For example, if a reliever threw
\>30 pitches, give 2 days rest; if \<30, at least 1 day rest. We can
maintain for each pitcher a `days_rest_needed` counter. Each day that
passes, decrement it, and only consider relievers with
`days_rest_needed == 0` as available. - If all relievers are exhausted
(unlikely in our simplified model), we might allow a tired one to pitch
with reduced effectiveness (or just reset everyone -- but that would
break realism). - The `Team` class could have a method like
`get_available_reliever()` that returns a pitcher marked as reliever who
is ready to pitch. We might choose the reliever with the highest stamina
or a random one if multiple are fresh. - During a game, if a reliever
himself gets tired (say we let relievers pitch at most 2-3 innings or 50
pitches), we could bring in another reliever to finish. This would
require potentially multiple pitching changes in one game, which our
simulation should handle by looping the pitching change check. -
**Rotation Fatigue**: Starters need rest between starts. To enforce a
4-day rest, if a team has games on consecutive days, the 5-man rotation
inherently gives each pitcher 4 days off. If we had fewer off-days, it
might be an issue if a team plays more than 5 days in a row (which MLB
schedules usually avoid). With 5 starters, a pitcher's next start comes
5 days later, which is sufficient. If a pitcher is pushed on short rest
(4 days or less), we could simulate a performance penalty (lower stamina
or slight reduction in attributes), but in first iteration we might not
simulate that explicitly. - **Emergencies and Spot Starters**: In a long
season, sometimes a 6th starter is used for doubleheaders or if someone
is injured. For now, unless we simulate doubleheaders (we are not,
unless a user forces them), every team playing 162 games in \~180 days
can get by with 5 starters. If we needed, we could allow pulling a
reliever into a start if rotation is broken, but that's an edge case.

**Implementing Rotation in Code**: We will extend the `Team` class or
SeasonSimulation logic to support rotation scheduling. For example:

    class Team:
        ...
        starters: List[Pitcher]
        relievers: List[Pitcher]
        next_start_index: int = 0

        def get_next_starting_pitcher(self) -> Pitcher:
            pitcher = self.starters[self.next_start_index]
            self.next_start_index = (self.next_start_index + 1) % len(self.starters)
            return pitcher

This returns the next starter and updates the index. We call this when
setting up each game's starting pitchers. The `Team.get_starters()`
method already gathers
starters[\[39\]](https://github.com/jlundgrenedge/baseball/blob/cf0ac9ff8c3218364a8618d45cffb60c13595f42/batted_ball/game_simulation.py#L318-L325),
so we should populate `Team.starters` list accordingly at team creation
(the database flag `is_starter` can be used to identify top starters on
the roster; likely the first 5 by games started or an attribute).

**Example**: Suppose the New York Yankees have 5 starters A, B, C, D, E.
Game 1 of season, `next_start_index=0`, so A starts. Game 2, Yankees
play again next day, index=1 -\> B starts, and so on. If an off-day
occurs with no game, the index doesn't advance, so the next game uses
the next pitcher in order. This simulates the regular rotation pattern.

**Bullpen Logic in Game**: In the game simulation
(`simulate_half_inning`), there's already a check for
`self.starter_innings` to switch to a reliever after a certain number of
innings[\[42\]](https://github.com/jlundgrenedge/baseball/blob/cf0ac9ff8c3218364a8618d45cffb60c13595f42/batted_ball/game_simulation.py#L658-L666).
We can replace or augment this with smarter logic: - We might decide
`starter_innings = 6` as a default (meaning let the starter go through 5
innings and then possibly change in the 6th or 7th). When the condition
triggers, the code does
`pitching_team.switch_to_reliever()`[\[44\]](https://github.com/jlundgrenedge/baseball/blob/cf0ac9ff8c3218364a8618d45cffb60c13595f42/batted_ball/game_simulation.py#L660-L668).
We should implement `Team.switch_to_reliever()` to choose an appropriate
reliever: - Possibly the prototype uses a random reliever each
time[\[44\]](https://github.com/jlundgrenedge/baseball/blob/cf0ac9ff8c3218364a8618d45cffb60c13595f42/batted_ball/game_simulation.py#L660-L668)
(since it calls `switch_to_reliever()` without parameters). We can
enhance that to use the rest tracking described: choose the freshest
reliever. - When a reliever is used, mark their rest requirement. -
Also, if a starter is giving up many runs, we might yank them early.
Implement a check each inning: if `runs_allowed_by_starter` \> some
threshold by the 4th or 5th inning, call `switch_to_reliever()` early. -
Conversely, if a starter is doing well, we might allow them to go beyond
the default innings (complete game). We can base that on pitch count;
e.g., if under 100 pitches and not fatigued, let them continue.

**Fatigue System**: We will maintain a simple fatigue model: - Each
pitcher has a `current_fatigue` or conversely a `rest_status`. After
each appearance, set `current_fatigue = 1.0` (100%). Each day of rest
subtracts e.g. 0.25 (so four days resets to 0 fatigue). If
`current_fatigue > 0`, performance could be reduced or the pitcher is
unavailable. For relievers, even 1 day of rest (0.25 recovery) might
often suffice for short outings. - The metrics system already monitors
fatigue
in-game[\[43\]](https://github.com/jlundgrenedge/baseball/blob/4269772e2752aa5ae28b697a1ed3d9d2680f7e1a/docs/guides/SIM_METRICS_GUIDE.md#L86-L94).
We could extend that to between games by reducing a pitcher's velocity
or stamina if `current_fatigue` is still high.

To keep it straightforward, we might not explicitly reduce performance
for a tired pitcher in the first iteration -- instead we simply won't
let a tired pitcher pitch (enforce rest). For example, do not select a
starter if he hasn't had 4 rest days. Our rotation design inherently
does that by cycling 5 pitchers. For relievers, implement the
availability rule as described.

**Validation of Usage**: After simulating, we can check average innings
pitched by starters and relievers to see if they align with reality
(e.g., starters should get \~30-33 starts each, \~180-200 IP for top
ones; relievers may pitch \~60-80 games but in short stints). If our
usage model is off (e.g., too many complete games, or relievers
overused), we can tweak the logic.

By implementing this rotation and bullpen system, our simulation will
better reflect real baseball strategy. It prevents unrealistic scenarios
like one ace pitcher starting 50 games or a reliever pitching every
single game. Instead, it will mirror MLB patterns: a **5-man rotation**
cycling through and a **bullpen** that shares the workload in relief.
This adds strategic depth and also affects stats (pitchers will have
more realistic ERAs and win-loss since they won't all pitch every day).
It also sets the stage for adding features like **injuries** or
**fatigue-based performance changes** in future: we have the scaffolding
to say "this starter is injured, bring up a spot starter" or "this
reliever is gassed, skip him today."

## 7. Validation Against Real MLB Data

To ensure the simulation output is realistic, we need a **validation
framework** that compares our results to real MLB historical data. The
goal is to verify that key statistics from the simulated season fall
within plausible ranges observed in real seasons. Our validation
strategy will include:

- **League Aggregate Stats**: Compare league-wide rates such as runs per
  game, home runs per game, batting average, and ERA to MLB averages.
  For example, MLB in recent years sees roughly 9.0 runs per game, 17
  hits per game, and 2.5 home runs per game (combined both
  teams)[\[45\]](https://github.com/jlundgrenedge/baseball/blob/cf0ac9ff8c3218364a8618d45cffb60c13595f42/batted_ball/parallel_game_simulation.py#L144-L152).
  After a simulation, we will compute these (our
  ParallelSimulationResult already gives runs/9, HR/9, etc. for quick
  comparison[\[24\]](https://github.com/jlundgrenedge/baseball/blob/cf0ac9ff8c3218364a8618d45cffb60c13595f42/batted_ball/parallel_game_simulation.py#L140-L148)).
  We expect our simulation to be in the ballpark of these numbers. If,
  say, our league average ERA comes out to 5.50 while MLB is \~4.15,
  that flags an issue in the physics or player ratings. Indeed, during
  development, it was noted that strikeouts were initially too high
  compared to MLB (K/9 12.4 vs \~8.5) and adjustments were
  made[\[31\]](https://github.com/jlundgrenedge/baseball/blob/4269772e2752aa5ae28b697a1ed3d9d2680f7e1a/batted_ball/player.py#L80-L88).
  We will similarly adjust if we see anomalies:
- Batting average: should be around .240-.270 league-wide.
- OBP and SLG: can derive and compare to a typical season (e.g., 2022
  MLB was \~.312 OBP, .395 SLG).
- Strikeout and walk rates: ensure K% \~22-23%, BB% \~8-9% league-wide,
  as real data.
- BABIP: around .295-.300 league average typically.
- **Team Performance Distribution**: Look at the spread of team wins and
  runs. In a real 162-game season, the best teams win around 100+ games
  (winning percentage \~.620) and the worst around 60 games (.370). We
  expect a similar range. If our simulation regularly produces a 130-win
  team or teams winning only 40, that's likely too much variance. We can
  run multiple season simulations to see if the distribution of win
  totals is reasonable (this also helps measure the randomness in the
  sim).
- **Individual Leader Stats**: Check if our league leaders are in line
  with historical norms. For instance:
- Home run leader: in recent MLB, \~45-50 HR often leads. Does our sim
  produce anyone with 70 HR? If yes, the power might be too high.
- Batting average leader: usually around .330-.350. If we see multiple
  .400 hitters, that's unrealistic.
- Strikeout leader (pitcher): K/9 or total Ks -- top pitchers might
  strike out 250-300 in a season. If our top shows 400, too high.
- Stolen bases, if we simulate them, should top out around 40-50 in
  modern era (unless simulating earlier eras). We don't need exact
  matches, but they should be plausible. This is a check on outliers.
- **Statistical Distribution Shape**: Beyond averages, the shape of
  distributions (e.g., the ERA distribution among qualifying pitchers,
  or the run distribution per game) should resemble real baseball. We
  can compare the standard deviation of runs per game to historical
  values. If our run scoring is too consistent or too wildly variable,
  it could indicate an issue (like if every game ends 5-4, or conversely
  some games regularly see 20+ runs).
- **Sabermetric Alignment**: Validate advanced metrics:
- League-average WAR should sum to around \~1000 WAR across MLB (because
  replacement level baseline). In our sim, since we compute WAR relative
  to replacement, the total WAR of all players should equal the number
  of wins above replacement in the league (which is league wins minus a
  baseline for replacement wins). If our WAR calculation is done right,
  the sum of WAR should be close to actual total wins (which is 2430/2 =
  1215 wins, minus \~47 wins per team replacement baseline, so \~ 1215 -
  (30\*47/2) --- we can fine-tune that).
- Check wRC+ distribution: league average wRC+ should be 100 by
  definition (if we set it up correctly). The best hitters might be
  170-180, worst \~60. If we see values way outside that, recheck the
  formula.
- FIP vs ERA: Compute league-average FIP and compare to league-average
  ERA from the sim. They should be reasonably close (within 0.2 or so)
  if the constant was applied correctly. Large discrepancies might
  indicate fielding or sequencing differences.
- **Historical Season Replay**: As a strong validation, we can simulate
  a specific real season (e.g., 2023) using the real rosters and compare
  team standings and player stats to actual. We might not expect to
  *match* reality (because randomness and because not modeling injuries,
  etc.), but we expect aggregate patterns to hold. For example, in a
  2023 replay, did teams that were strong in reality also tend to be
  strong in simulation (this checks that our player talent level
  calibration is right)? We can use correlation measures: correlate
  actual team wins to average simulated wins across many runs --
  ideally, \>0.5 correlation if ratings are good. Also compare the
  league leaders in sim to actual -- e.g., if Aaron Judge hit 60 HR in
  2022, does our 2022 sim have someone in that range?

**Validation Data Sources**: We will leverage the **pybaseball** library
to fetch real data for comparison. For example, pybaseball can get us
actual 2025 league batting stats or team stats to compare (or we use
known reference values). The `PybaseballFetcher` in our repo can
retrieve historical stats
easily[\[46\]](https://github.com/jlundgrenedge/baseball/blob/4269772e2752aa5ae28b697a1ed3d9d2680f7e1a/batted_ball/database/pybaseball_fetcher.py#L26-L34)[\[47\]](https://github.com/jlundgrenedge/baseball/blob/4269772e2752aa5ae28b697a1ed3d9d2680f7e1a/batted_ball/database/pybaseball_fetcher.py#L72-L81).
We could fetch league batting and pitching lines to compare league slash
lines and ERA directly.

**Acceptable Deviations**: We should define thresholds for discrepancy
that we consider acceptable. For instance: - League run environment
within say ±5% of MLB historical value (if MLB is 9.0 R/G, our sim 8.5
to 9.5 would be okay). - League K/9 within ±10% of real (we saw a 46%
high K rate was not okay and required
tuning[\[32\]](https://github.com/jlundgrenedge/baseball/blob/4269772e2752aa5ae28b697a1ed3d9d2680f7e1a/batted_ball/player.py#L82-L88),
so now we'd aim much closer). - Team win distribution: maybe standard
deviation of wins in sim should be roughly 15 wins (which is typical).
If it's 25, variance is too high. - No single player stat way beyond
historical record (e.g., no 100 HR season unless intentionally
simulating a steroid era extreme).

If the simulation falls outside these bounds, we would revisit the
physics models or player attributes: - For example, if home runs are too
high, we might reduce exit velocities or drag coefficient slightly. - If
batting averages are too low (too many strikeouts), adjust pitcher stuff
or batter contact ratings (the dev logs mentioned reducing breaking ball
effectiveness to fix
K%[\[31\]](https://github.com/jlundgrenedge/baseball/blob/4269772e2752aa5ae28b697a1ed3d9d2680f7e1a/batted_ball/player.py#L80-L88)).

**Automated Validation**: We can implement a suite of checks that run
after a season simulation. For instance, a function
`validate_season(sim_stats)` that computes these key indicators and
prints a report: - "League BA = .250 (MLB 2022: .243) -- OK", - "League
HR/Game = 2.8 (5% high relative to 2022) -- Slightly high, consider
tuning.", - "Max team wins = 108 -- OK, Min team wins = 54 -- OK", -
"Max HR by player = 52 -- OK (real max 73 historically, 46 in 2022)".

We could also write unit tests for some known extreme scenarios. For
example, if we simulate a season with identical teams (all players
average), the output should logically be very balanced (all teams
\~81-81). This can test that our schedule and sim aren't biased.

**Example Validation Outcomes**: During testing, we might have
discovered issues. The repository info shows one such case: originally,
strikeouts were much too frequent in the simulation (K/9 12.4 vs MLB
\~8.5)[\[31\]](https://github.com/jlundgrenedge/baseball/blob/4269772e2752aa5ae28b697a1ed3d9d2680f7e1a/batted_ball/player.py#L80-L88).
They applied a 33% reduction in breaking ball whiff rates to address
this, bringing K% down to \~22%. This kind of adjustment is exactly what
our validation will drive -- identify a metric out of line, then tune
parameters (e.g., decrease pitch effectiveness, increase ball in play
probability, etc.) and re-run until the metric falls in range. We would
maintain a set of "7/7 validation tests" (as mentioned in the prompt's
requirements) that must all pass before we consider the sim calibrated.
These 7 tests likely correspond to key stat categories (runs, hits, HR,
BA, K, BB, fielding errors perhaps).

Another aspect is comparing **simulated vs actual standings** in a
historical replay. We don't expect them to match exactly (since
randomness and unmodeled factors play a role), but if our simulation
consistently produces wildly different results, that's a flag. For
instance, if a last-place real team ends up winning the World Series in
most simulations, perhaps the player ratings are off (maybe their
players have inflated attributes because of a small sample anomaly). We
might adjust by using multi-year averages for player skills to get more
accurate performance.

**Conclusion of Validation**: The validation phase gives confidence that
the season simulation is producing **credible baseball statistics**. By
systematically comparing to real data and iterating, we ensure our
physics-driven approach yields realistic outcomes. Once all key metrics
are within acceptable deviation (say within one standard deviation of
historical
norms[\[48\]](https://github.com/jlundgrenedge/baseball/blob/cf0ac9ff8c3218364a8618d45cffb60c13595f42/tests/archive/LEAGUE_SIMULATION_README.md#L214-L216)),
we will consider the simulation validated. We will document these
comparisons in the final output, possibly outputting a summary like:

    Validation Summary:
    - Runs per game: 9.1 (MLB 9.0) – OK
    - HR per game: 2.3 (MLB 2.2) – OK
    - League BA/OBP/SLG: .247/.318/.409 (MLB .244/.317/.411) – OK
    - ERA: 4.20 (MLB 4.26) – OK
    - Stolen Bases: 1206 total (MLB 1260) – OK
    - ... etc.

Any significant discrepancies will be noted and targeted for adjustment
in the simulation model.

## 8. Performance Considerations

Simulating 2,430 games with detailed physics and stats is
computationally intensive, so we must optimize for speed and resource
use. The design will leverage parallel processing and efficient data
handling to keep the full-season simulation within a reasonable time
(the goal is under 4 hours, ideally much
less[\[49\]](file://file_000000004bb471f5a9156c5597b55a74#:~:text=2.%20,validation%20tests%20must%20still%20pass)).

**Parallel Game Simulation**: The repository already includes a
`ParallelGameSimulator` that can distribute games across CPU cores,
yielding a \~5-8× speedup on multi-core
systems[\[50\]](https://github.com/jlundgrenedge/baseball/blob/cf0ac9ff8c3218364a8618d45cffb60c13595f42/tests/archive/LEAGUE_SIMULATION_README.md#L190-L198).
We will utilize this extensively. Specifically, we plan to simulate
multiple games concurrently where possible: - **By Days or Batches**: As
mentioned, we can group independent games (e.g., games on the same day)
and run them in parallel. On a typical day there are 15 games maximum;
if we have an 8-core machine, we could run many of them simultaneously
in threads (the sim uses Numba which releases the GIL, allowing true
multithreading[\[51\]](https://github.com/jlundgrenedge/baseball/blob/cf0ac9ff8c3218364a8618d45cffb60c13595f42/batted_ball/parallel_game_simulation.py#L10-L18)[\[52\]](https://github.com/jlundgrenedge/baseball/blob/cf0ac9ff8c3218364a8618d45cffb60c13595f42/batted_ball/parallel_game_simulation.py#L27-L35)).
The parallel simulator is currently configured to simulate multiple
games between the same two
teams[\[53\]](https://github.com/jlundgrenedge/baseball/blob/cf0ac9ff8c3218364a8618d45cffb60c13595f42/batted_ball/parallel_game_simulation.py#L321-L330);
we might adapt it to handle a list of different matchups by launching
separate tasks for each game. Alternatively, simply create a thread pool
and call the single-game simulator for each game in the day. -
**Chunking**: The `ParallelSimulationSettings` allows chunk sizes to
amortize
overhead[\[54\]](https://github.com/jlundgrenedge/baseball/blob/cf0ac9ff8c3218364a8618d45cffb60c13595f42/batted_ball/parallel_game_simulation.py#L32-L40).
We can experiment with chunking a week's games or series to reduce the
constant overhead of process or thread launching. - **No Parallel
Dependency Conflicts**: Since each game's simulation is independent
(except for sequential scheduling constraints), running them in parallel
is safe. We just need to ensure thread safety when writing results to
the season state. The design could gather all game results from a day's
parallel run, then update the cumulative stats in a single-threaded step
to avoid race conditions.

With parallelization, we expect significant speedup. For example, if a
single game takes \~6 seconds with Rust/Numba acceleration (a figure
mentioned for the engine), then 2,430 games sequentially would be \~4
hours. But if we can utilize, say, 8 cores effectively, we could cut
that to around 0.5--1 hour. Indeed, testing a smaller 240-game season on
8-16 cores took about 60-90
minutes[\[55\]](https://github.com/jlundgrenedge/baseball/blob/cf0ac9ff8c3218364a8618d45cffb60c13595f42/tests/archive/LEAGUE_SIMULATION_README.md#L200-L203),
so a 2430-game season might scale to \~10x that games and take maybe
\~6-10 hours on similar hardware. We'll aim to optimize further: -
Possibly reduce the fidelity of simulation slightly (e.g., skip some
heavy debug calculations during the big run) to gain speed. We can
disable the detailed `SimMetricsCollector` during mass simulation (since
that adds overhead) and run it only for targeted games or smaller test
runs. - Use optimized data structures: many inner loops are already in
Numba/Cython or Rust, which is good. We should ensure our Python-side
code (updating stats, etc.) is not too slow. That code is mostly simple
arithmetic per game event, which is negligible compared to the physics
sim itself.

**Memory and Storage**: Storing season stats for all players is not
memory-heavy (a few thousand players with a few dozen stats each).
Storing detailed play-by-play logs for all games would be huge, so we
will not keep every pitch or play in memory -- we'll log only summary
info (as needed for stats and box scores). If needed for debugging,
writing play-by-play to disk for a single game or a few games is
possible (the sim has an option to log games to a
file[\[56\]](https://github.com/jlundgrenedge/baseball/blob/cf0ac9ff8c3218364a8618d45cffb60c13595f42/batted_ball/parallel_game_simulation.py#L328-L336)),
but we won't do that for all 2430 games by default.

**Multi-Season Simulations**: If users want to run Monte Carlo
simulations of multiple seasons (to assess variability or do what-ifs),
performance becomes even more crucial. Our framework can handle that by
looping the SeasonSimulation multiple times. To optimize: - We could
parallelize across seasons as well, if the machine has many cores (e.g.,
simulate 10 seasons in parallel on a 40-core server, with each season's
games parallelized within its cores subset). - More practically, run
seasons sequentially but ensure that at the end of each season we reset
all data without memory leaks. We should reuse objects efficiently:
perhaps keep the same team and player objects and just reset their
stats, rather than re-loading everything from scratch each time (to save
the overhead of database calls).

**Profiling and Bottlenecks**: We should profile the end-to-end
simulation early. If, for instance, we find that updating Python data
structures for stats is taking significant time relative to simulation,
we could vectorize some of it or move certain calculations into the
simulation's compiled code. However, it's likely the physics simulation
is the dominant factor. Using the Rust-accelerated or Numba-optimized
code for ball physics ensures each at-bat is fairly fast.

The documentation indicates heavy use of numpy and even Rust for speed
(Rust acceleration \~6 sec/game as noted). We will maintain those
optimizations. For example, the trajectory calculations, collision,
etc., are presumably JIT-ed. We should avoid adding Python loops in
those critical paths. All our stat-tracking additions should be
efficient (incrementing counters is trivial, but we should be careful
not to, say, sort a huge list every at-bat or something like that).

**Parallel I/O**: If we output a lot of data (say writing CSVs of
stats), do it after the simulation, not during (to avoid I/O bottlenecks
in the loop). Or buffer it and write in batches. The final stats output
(some CSV files or a database insert) is minor compared to simulation
time, though.

**Memory of Game Objects**: One consideration -- if using the
`ParallelGameSimulator`, it serializes team objects to send to worker
processes[\[53\]](https://github.com/jlundgrenedge/baseball/blob/cf0ac9ff8c3218364a8618d45cffb60c13595f42/batted_ball/parallel_game_simulation.py#L321-L330).
That means passing full team rosters repeatedly. To reduce overhead, we
might prefer the threaded approach (no pickling needed, since threads
share memory). The code even provides a ThreadPoolExecutor usage in
parallel (the Phase 4 note suggests using threads for lower overhead).
We should consider using the thread-based approach for our season to
avoid the cost of process spawn and data copy for each game. The
`ParallelGameSimulator` could potentially run in thread mode by setting
`num_workers` and internal flags (maybe the current design primarily
uses multiprocessing Pool).

**Performance Metrics**: We will output performance info at the end:
total simulation time and games per second. The parallel sim already
computes and prints
games/sec[\[57\]](https://github.com/jlundgrenedge/baseball/blob/cf0ac9ff8c3218364a8618d45cffb60c13595f42/batted_ball/parallel_game_simulation.py#L375-L383)[\[58\]](https://github.com/jlundgrenedge/baseball/blob/cf0ac9ff8c3218364a8618d45cffb60c13595f42/batted_ball/parallel_game_simulation.py#L390-L399).
For 2430 games, even at, say, 2 games/sec, that's \~20 minutes total.
Achieving that might require substantial cores or slightly faster than 6
sec/game performance. If not achieved, it might be \~1 game/sec =\> \~40
minutes, which is still good. In worst case, if sequential at 6 sec
each, \~4 hours (the upper bound requirement).

We will test on smaller scales (like simulate 100 games, see time,
extrapolate). We should also test the overhead of context switching --
e.g., if we simulate one day at a time with 15 parallel games, that's
162 such parallel batches. The overhead of spawning threads 162 times is
negligible, but if we used processes, it might be larger. We will thus
lean on threads for per-day parallelism.

**Database and Data Loading**: One performance consideration is loading
the player database at the start. Fetching all team rosters via
pybaseball can be slow (but we can cache or use the stored database). We
likely assume rosters are pre-fetched and stored locally (the prompt
suggests using the existing database in `batted_ball/database`). So
initial loading might take a minute or so if not cached, but that's
fine. It's a one-time cost.

**Memory Footprint**: Storing stats for maybe \~1000 players (30 teams
\* 26-man rosters \~780, plus some extra) is trivial. Storing 2430
GameResults with box scores is heavier but still manageable (let's
estimate each box score \~50 players \* \~15 fields \~ 750 values per
game, as a Python dict overhead, maybe a few KB per game, so a few MB
for all games). Not a concern for modern memory. If we decided to
simulate, say, 100 seasons in one go and keep all results, that would be
\~300 MB, still okay for offline analysis but maybe we wouldn't keep all
in memory in that case.

**Scaling Up or Down**: The system should allow scaling down (e.g.,
simulate a 60-game season test) quickly or scaling up (multiple
seasons). We can provide configuration to skip certain calculations if
not needed (like turn off advanced metrics calc in an inner loop until
final output, etc., to save time).

In summary, by using parallel execution and efficient design, we expect
to comfortably meet performance goals: - On a multi-core machine, a full
162-game x 30-team season could potentially run in well under an hour
(our aim), as evidenced by smaller scale
tests[\[59\]](https://github.com/jlundgrenedge/baseball/blob/cf0ac9ff8c3218364a8618d45cffb60c13595f42/tests/archive/LEAGUE_SIMULATION_README.md#L198-L203). -
We will document the performance: e.g., "Simulated 2,430 games in 45
minutes using 12 cores (\~0.9 games/sec)" to ensure we and users know
the requirements. - We also note that disabling verbose logging and high
debug levels is important for speed (the metrics debug logs can slow
things by writing a lot; we will keep `DebugLevel` off or basic for
production
runs[\[60\]](https://github.com/jlundgrenedge/baseball/blob/4269772e2752aa5ae28b697a1ed3d9d2680f7e1a/docs/guides/SIM_METRICS_GUIDE.md#L148-L156)).

This focus on performance ensures the simulation is **practical to
use**, even for experiments requiring multiple seasons, without
sacrificing the rich detail of the physics simulation.

## 9. Output & Reporting

At the end of the season simulation, our system will produce a variety
of outputs to summarize the results in a user-friendly way. We aim to
provide reports comparable to those on Baseball-Reference or FanGraphs
for a season, including standings, team stats, player leaderboards, and
possibly visualizations.

**File Formats**: We will output data in formats that are both
human-readable and machine-readable: - **CSV/TSV Files**: Ideal for
structured data like final player stats or game logs. For example, a
`players_stats.csv` with one row per player (containing team, PA, AB, H,
HR, RBI, AVG, OBP, SLG, WAR, etc.), and a `team_stats.csv` with one row
per team (W, L, runs for, runs against, run diff, team OPS, team ERA,
etc.). CSV is convenient for users to do their own analysis (e.g., load
into Excel or R). The repository even has a CSV exporter for the
database, and we can follow that pattern for output
data[\[61\]](https://github.com/jlundgrenedge/baseball/blob/cf0ac9ff8c3218364a8618d45cffb60c13595f42/batted_ball/database/team_database.py#L180-L188). -
**JSON**: For more hierarchical data like the full schedule results or
box scores, JSON might be appropriate. For instance,
`schedule_results.json` could contain an array of games, each with the
detailed box score info. JSON is easily parsed by scripts if needed. -
**Formatted Text Reports**: We will generate text/markdown summaries
that present the key information in a nicely formatted manner, similar
to how Baseball-Reference pages show tables. This could be printed to
console or saved as a `.md` file. For example, a **Standings** table:

    Final Standings:
    AL East            W   L   Pct    RF   RA   Diff
    Boston Red Sox    95  67  .586   820  700  +120
    New York Yankees  90  72  .556   780  712  +68
    ... etc.

We saw an example in the test output for a smaller
league[\[35\]](https://github.com/jlundgrenedge/baseball/blob/cf0ac9ff8c3218364a8618d45cffb60c13595f42/tests/archive/LEAGUE_SIMULATION_README.md#L130-L138),
and we would do similarly for all six MLB divisions. We'll also
highlight playoff teams if we simulate playoffs.

- **Console output vs File**: We can allow the user to specify if they
  want the results printed or written to files. Typically, writing to
  files (CSV/JSON) is good for large data like full player stats,
  whereas a concise summary can be printed.

**Reports to Generate**: 1. **Standings and Team Stats**: A report of
each division's final standings, including wins, losses, win%, runs
scored, runs allowed, run differential, perhaps team OPS and ERA. The
test documentation's output included run differential and quality
labels[\[35\]](https://github.com/jlundgrenedge/baseball/blob/cf0ac9ff8c3218364a8618d45cffb60c13595f42/tests/archive/LEAGUE_SIMULATION_README.md#L130-L138).
We won't have "quality" categories unless we add them, but we will
include the key stats. We can also output the league-wide totals (like
total runs scored in league). 2. **League Leaders (Batting)**: List the
top performers in major categories: - Traditional: Batting Average (with
at least X PA), Home Runs, RBIs, Stolen Bases, Hits. - Advanced: wRC+
leaders, WAR leaders (to see simulation "MVPs"), perhaps OBP, SLG
leaders. - We could produce a small table for each: e.g., "Home Run
Leaders: 1. Mike Trout -- 45 HR; 2. Vladimir Guerrero -- 43 HR; ..." and
so on. 3. **League Leaders (Pitching)**: - Traditional: ERA (with IP
qualifier), Wins (though wins are less telling), Strikeouts, Saves. -
Advanced: FIP leaders, WAR (pitcher WAR/Cy Young), WHIP, K/BB ratio. -
For ERA and such, list top 5 or 10. 4. **Team detail stats**: For each
team, provide a summary of team hitting and pitching: - Team batting
triple slash (AVG/OBP/SLG), total HR, runs, maybe wRC+. - Team pitching:
team ERA, FIP, total K, BB. - These could be compiled into one big table
or separate per team. The test example mentions each team's detailed
statistics including per-game
averages[\[62\]](https://github.com/jlundgrenedge/baseball/blob/cf0ac9ff8c3218364a8618d45cffb60c13595f42/tests/archive/LEAGUE_SIMULATION_README.md#L139-L147).
We might present it like:

    Team          Avg   OBP   SLG   HR   R/G   ERA   K/9   BB/9
    Dodgers       .255  .330  .440  210  5.1   3.90  9.0   2.8
    ...

This gives a one-glance view of team strengths. 5. **Game Log or
Schedule Summary**: If needed, we can output the results of each game or
each series. For example, a schedule summary could list each team's
record against each opponent (like a matrix). However, that's a lot of
data. Instead, perhaps provide: - A postseason bracket results (if
playoffs simulated). - Notable games: maybe list any no-hitters or very
high scoring games found by scanning game results, just as flavor. - The
test outputs included full game history per
team[\[63\]](https://github.com/jlundgrenedge/baseball/blob/cf0ac9ff8c3218364a8618d45cffb60c13595f42/tests/archive/LEAGUE_SIMULATION_README.md#L74-L83)[\[64\]](https://github.com/jlundgrenedge/baseball/blob/cf0ac9ff8c3218364a8618d45cffb60c13595f42/tests/archive/LEAGUE_SIMULATION_README.md#L140-L147)
(list of scores against each opponent). We could implement printing each
team's game-by-game results or series results. This could be heavy, so
maybe optional.

**Visualization Strategies**: - We can create simple plots to help
analyze the season: - **Distribution plots**: e.g., a histogram of team
win totals, to illustrate parity. Or a runs per game histogram. - **Time
series**: show how a team's games behind first place changed over the
season, or winning percentage over time. - **Bar charts**: compare team
run differentials, etc. - We might integrate with libraries like
matplotlib or seaborn to generate charts. For example, a bar chart of
top 10 WAR could be output as an image. Since the environment here might
be non-interactive, we could save charts as PNG files. - Another idea:
generate an interactive visualization or web page. This is beyond
initial scope, but we can design the outputs to be easily fed into such
a system. For now, static charts and tables suffice.

If the user runs this in a Jupyter notebook or similar, we could provide
the data frames directly for them to explore. But as a standalone, we'll
focus on static outputs: - CSVs for data interchange. - Markdown/console
text for quick summary. - Possibly images for a report (if automated
reporting, we could embed charts in an HTML or PDF report).

**Example Output Snippets**: - We show a fragment of a possible
standings table as Markdown (with alignment):

    ### Standings
    **AL East**:
    | Team              | W   | L   | Pct   | RF   | RA   | Diff |
    |-------------------|-----|-----|-------|-----|-----|------|
    | Toronto Blue Jays | 92  | 70  | .568  | 800 | 745 | +55  |
    | New York Yankees  | 88  | 74  | .543  | 770 | 722 | +48  |
    | ...               |     |     |       |     |     |      |

- A top hitters table:

<!-- -->

    **Top 5 Batters (wRC+):**
    1. Juan Soto – 172 wRC+ (/.301/.440/.590, 42 HR, 110 RBI)
    2. Mike Trout – 160 wRC+ (/.285/.400/.620, 45 HR, 98 RBI)
    3. ...

We can include the triple slash and HR/RBI for context.

- WAR leaders:

<!-- -->

    **WAR Leaders:**
    1. Shohei Ohtani – 8.5 WAR (4.0 hitting, 4.5 pitching)
    2. Mookie Betts – 7.2 WAR
    3. ...

(This shows off our two-way simulation if applicable, and provides
breakdown if we calculate for Ohtani-type usage.)

Essentially, the output aims to be as informative as a
Baseball-Reference season page: - They have league summary, team
standings, team offense/pitching ranks, and individual leaders.

Finally, **saving vs displaying**: We likely will write most outputs to
files so they can be referenced later. For example: - `standings.md`
(formatted table), - `league_leaders.md`, - CSVs for detailed stats, -
maybe an `index.html` or markdown that composes everything (for a
one-stop report).

**Optional visualization**: If we wanted, we could generate a few quick
plots: - Win distribution histogram (to see if our sim was wild or
normal). - A scatter of team runs scored vs runs allowed (and overlay
actual MLB if doing a comparison). - WAR distribution by team (stacked
bar of how WAR was accumulated by team, to show which team had star
power vs balanced).

These would likely be done offline by the user with the CSVs, but we
mention them as possibilities.

By organizing the output as above, the user can easily inspect the
results and also use the data for further analysis. The combination of
human-readable summaries and raw data files covers the needs of both
casual inspection and detailed analytics. We also ensure to **cite
sources for any real-world reference** in our report (if we produce a
written analysis, we would cite MLB averages etc., as we have done
within this design doc).

In summary, the reporting system will turn the sea of simulation data
into digestible information: - Final standings and team performance
highlights. - Player leaderboards and award-type metrics. -
Comprehensive stat tables for anyone who wants to drill deeper. - All
delivered in formats suitable for both quick viewing and serious
analysis, fulfilling the goal of outputs comparable to
Baseball-Reference's encyclopedic stats.

## 10. Replay & Historical Comparison

Our simulation framework will also support **replaying historical MLB
seasons** and comparing the outcomes to actual results. This serves both
as a validation of realism and a tool for analysis (e.g., "What if we
replay 2021 season 100 times? What's the distribution of outcomes?").

**Simulating Historical Seasons**: - **Rosters**: We will leverage the
`TeamDatabase` and `PybaseballFetcher` to load rosters for a given year.
The prompt indicates we have the capability to fetch team data by
season[\[65\]](https://github.com/jlundgrenedge/baseball/blob/cf0ac9ff8c3218364a8618d45cffb60c13595f42/batted_ball/database/team_database.py#L38-L46)[\[66\]](https://github.com/jlundgrenedge/baseball/blob/cf0ac9ff8c3218364a8618d45cffb60c13595f42/batted_ball/database/team_database.py#L108-L116).
For example, to simulate 2023, we set `season=2023` and fetch each
team's stats (the code fetches all players with min AB/IP thresholds,
ensuring fringe players are
included)[\[66\]](https://github.com/jlundgrenedge/baseball/blob/cf0ac9ff8c3218364a8618d45cffb60c13595f42/batted_ball/database/team_database.py#L108-L116).
This gives us players with their performance from that year, which the
StatsConverter then maps to our simulation attributes (contact, power,
etc.). We must ensure to use the season-specific data so that a player's
2015 stats aren't used in a 2021 simulation, for example. - **Attributes
Calibration**: The StatsConverter will create players' skill attributes
based on that year's stats (e.g., if 1968 is chosen (Year of the Pitcher
with low offense), many hitters will have poor stats and thus low
batting attributes, which in turn will produce a low-scoring simulation
reflecting that environment). This way, the sim is contextual to the
era. We might need to adjust environmental constants for different eras
(like the baseball liveliness, etc.), but initially we assume the
physics covers it through player stats. - **Schedule**: Ideally, use the
actual historical schedule for that season to truly replicate it. We
likely need data from retrosheet or MLB schedule files. Pybaseball might
not directly provide schedules, but we can obtain them via Retrosheet's
schedule CSVs or an API. For a first pass, we could approximate the
schedule with our generator to have the same opponents frequency, but
using the real schedule has benefits: - It ensures the same matchups and
home/away distribution as actual, which matters for comparison (actual
schedules can be imbalanced). - It allows direct game-by-game outcome
comparison if needed (though that's a deep dive). - If acquiring actual
schedules is complex, an alternative is to use our schedule generator
but configure it to mimic that year's structure (e.g., older seasons had
no interleague before 1997, different number of games vs division due to
different league sizes). The division alignment and number of teams also
changed over history (e.g., before 1969 there were no divisions; 1994
introduced three divisions, etc.). Our simulation should be flexible for
different league structures. We might focus on modern (post-2013) for
now (30 teams, 162 games). - **Simulate**: Run the season with those
rosters and schedule.

**Comparison to Actual Outcomes**: - **Team Performance**: Compare each
team's simulated record to their real record. We could create a table:

    Team       Actual W-L    Simulated W-L (Avg of N runs)    Difference
    Yankees    92-70         88-74 (±5)                      -4 wins

If we run the sim once, it's just one outcome -- could be luck involved.
Better is to simulate the season multiple times (say 100 or 1000) to get
a distribution of outcomes. Then we can see if actual outcome lies
within the simulation's expectations. For example, if a weak team
actually got lucky and won 85 games, our sim (if run many times) might
say they average 75 wins with a 5-win standard deviation, so 85 is 2
standard deviations high but possible. This helps validate roster
accuracy and identify if our model undervalues or overvalues certain
teams. - **Player Stats**: Compare league leaders and distribution: -
Did our sim produce a similar league HR champion? If Aaron Judge hit 62
HR in 2022 actual, does the sim often produce a 60+ HR hitter? It might
not always, due to randomness, but on average maybe the top sim HR \~55.
We can average the top values over many runs. - Check if players' sim
stats regress to mean (they likely will). For instance, someone who hit
.370 in real life (very high) might only hit .330 in sim on average --
because maybe the model or sample size regression. This is fine, but we
should note it. It indicates how much luck may have been in actual
performance. In other words, we can use the sim to separate skill vs
luck by seeing if extreme real stats are reproduced or if they come down
to earth. - **Physics vs Roster Accuracy Isolation**: To isolate these
factors: - **Roster Accuracy**: Are player attributes reflecting true
talent? For example, if our simulation consistently has a certain player
underperform relative to real life, maybe our attribute mapping is off.
Alternatively, maybe real life was an outlier for that player. Over many
sim iterations, we get a distribution of that player's performance. If
the real stat lies at extreme tail, that suggests real life was fluky
(or our model missing something about that player). -
**Physics/Simulation Accuracy**: We ensure league-level stats match
(that's validation). But also check patterns like correlations: Does the
simulation preserve the relative strengths of teams and players? A
strong method is rank correlation of team performance: simulate the
season many times and see the average wins for each team, correlate that
with actual wins. If we get a high correlation (say 0.8+), it means the
model properly evaluates which teams are good. If correlation is low,
maybe our simulation doesn't distinguish teams well (could be an issue
with how we assign attributes or maybe excessive randomness). - Another
isolation approach: run an alternate simulation using a simplified model
(like a Pythagorean expectation or Monte Carlo using just projected runs
for each team) and compare results to our physics-based sim. If those
align, it means the physics engine is effectively capturing the expected
performance. - We can also simulate with "perfect skills" scenario: use
players' actual statistical distribution as probabilities (like a dice
roll simulation) to see what pure statistical variation yields, then
compare to our physics sim variation. If differences arise, it might be
because physics-based outcomes have different variance characteristics
than assumption of independence. This is more of a research experiment.

**Using Actual Schedules**: - We should incorporate actual schedules if
possible especially for historical replays, because schedule affects
results (e.g., AL vs NL differences, strength of division). For example,
the unbalanced schedule in pre-2023 MLB means a strong division could
beat each other up -- our schedule generator might not replicate that
exactly. By using the actual schedule, when we simulate 2019, the Astros
will face the Mariners 19 times as they did, etc. - Retrosheet provides
CSVs listing all games with date, teams, score. We can use that to build
our schedule input (ignoring the scores). - If actual schedule is used,
we also simulate in chronological order, which enables comparing
standings on any date (fun but not required). - If not using actual, at
least ensure number of games vs each opponent matches (the team roster
fetch could give division membership, etc., to feed into generator
accordingly).

**What-If Scenarios**: - Once the simulation of a historical season
works, we can tweak scenarios: - **Trades**: e.g., "What if a big
mid-season trade didn't happen?" We could simulate from start with
rosters not reflecting that trade (keeping player on original team all
year). This requires the ability to adjust rosters or even simulate in
two halves (simulate up to trade date, swap players, continue -- that's
advanced, but doable). - **Injuries**: e.g., "What if a star player
never got injured and played full season?" We could increase their PA/IP
in our simulation by adjusting their durability or simply leaving them
in lineup all year. Conversely, simulate if a player was injured by
removing them at a date. - **Era cross-over**: Simulate a historical
season with modern players or vice versa (not a direct asked feature,
but our system could do it -- e.g., use 1927 rosters in 2023 schedule or
something for fun). - **Rule changes**: We can modify something like use
1968 mound height or 2019 ball liveliness as inputs to physics to see
differences, but that's fairly granular. More straightforward: simulate
2020 season (60 games) to see how short seasons behave, etc., which our
flexible scheduler can handle.

**Comparison Methodology**: - Statistical: for each metric, we will
compare mean and variance between sim and actual. Possibly use
significance tests for differences. But since we essentially *calibrate*
sim to match league stats, those should align. The interesting
comparisons are at team/player level (which involve randomness). -
Graphical: plot actual vs simulated wins for teams. Ideally points fall
near diagonal (meaning model predicted their strength well). Outliers
indicate surprise teams. - We might create a **report** that
specifically addresses these: something like:

    Historical Replay 2022:
    - Actual league ERA: 4.00, Simulated avg ERA: 3.95 (sim slightly more pitcher-friendly).
    - Team win correlations: 0.85 between actual and sim mean wins.
    - Biggest overperformance in sim: Team X, which averaged 5 wins more than actual (perhaps indicating they were unlucky in real life or our model likes their roster more).
    - Player stat comparisons: Out of 20 players who hit 30+ HR in actual 2022, the sim on average produced 18 such players (comparable). The sim’s top HR was 57 vs actual 62.

We would identify if any team or player is consistently different. For
example, maybe our simulation consistently has the Rays performing worse
than actual -- possibly because their real-life use of openers and
bullpen might not be fully captured if we simplified pitching roles.
Such insights can guide refining our simulation usage model in the
future.

- **Separate Physics from Roster**: One way to do this is to run a
  **neutral talent simulation** -- like give every team identical
  average players and simulate a season. The outcome should be
  essentially all teams \~.500 if the physics has no bias (aside from
  random variation). If we see any systemic biases there, that's a
  physics issue (unlikely -- the physics should treat all equally if
  talent equal). So that's a sanity check.
- Another approach: use actual team stats (like their runs
  scored/allowed) to simulate a season outcome distribution and compare
  to our physics-based approach. If both produce similar variability in
  standings, then physics-based engine is as "good" as a simpler model
  for overall outcomes, just more detailed. If not, examine why (maybe
  physics-based game-by-game variation differs).

**Using Historical Data via Pybaseball**: As noted, pybaseball can fetch
historical stats
easily[\[46\]](https://github.com/jlundgrenedge/baseball/blob/4269772e2752aa5ae28b697a1ed3d9d2680f7e1a/batted_ball/database/pybaseball_fetcher.py#L26-L34)[\[47\]](https://github.com/jlundgrenedge/baseball/blob/4269772e2752aa5ae28b697a1ed3d9d2680f7e1a/batted_ball/database/pybaseball_fetcher.py#L72-L81),
which we already use for rosters. We also can fetch actual standings and
leader stats for reporting. For example, pybaseball's `team_standings()`
or just using known final standings can be input for comparison. The
system could automatically print actual vs sim for each team if we
supply the actual W-L.

**Park Factors and Conditions**: Historical comparisons might require
adjusting for park factors or era conditions. If we simulate 1980,
league average HR might naturally be lower in our sim if players have
lower power stats from that year. That's fine. But if we simulate 2019
vs 2022, the ball was livelier in 2019 -- our sim might not know that
explicitly unless reflected in players' stats (which it would be --
players in 2019 had more HR, so their power attribute goes up, sim
should output more HR).

**Alternate Histories**: We could use the sim to answer questions like
"What if the 2023 season was replayed 1000 times, how often would each
team win the World Series?" which is more of a playoff simulation
question but could be done by simulating season + playoffs repeatedly.
Or "what if team X hadn't lost their star to injury?" by altering that
player's availability.

Our design thus includes the flexibility to: - Plug in any season's data
as input, - Use actual or generated schedules, - Run multiple trials, -
And produce comparative output.

We will ensure the code to load season data is parameterized by year,
and perhaps have a mode to run N simulations for one season. The output
of such a run could be something like:

    Simulated 100 seasons of 2023:
    Team    Actual Wins   Simulated Avg Wins (±SD)   Chance of Making Playoffs (sim)
    NYY     99           96.4 ± 5.2                 88%
    TOR     92           90.1 ± 5.8                 72%
    ... etc.

This would be very insightful: it shows how much of actual success was
skill vs luck (if actual wins differ significantly from sim average).

**Concluding Historical Analysis**: This capability not only validates
our model but also showcases its power. We can include in our
documentation a case study of a past season as an example: - Simulate
1986 and compare the Mets and Red Sox (both won their divisions)
performance distribution. - Simulate the strike-shortened 1994 with a
full 162 games to "finish" it as a what-if.

The key is to ensure our architecture supports substituting the input
data easily (which it does via TeamDatabase) and that we can ingest
actual schedules or configure the schedule generator accordingly (which
we plan for).

By analyzing differences between simulation and reality, we gain
confidence in the model when they align, and we learn where to improve
it when they don't. This replay feature turns our tool into more than
just a random season generator; it becomes a means to **experiment with
history** and understand the game's dynamics under controlled
conditions.

------------------------------------------------------------------------

[\[1\]](https://punkrockor.com/2017/10/05/sports-scheduling-meetings-business-analytics-why-scheduling-major-league-baseball-is-really-hard/#:~:text=,have%20a%20day%20off%20in)
[\[4\]](https://punkrockor.com/2017/10/05/sports-scheduling-meetings-business-analytics-why-scheduling-major-league-baseball-is-really-hard/#:~:text=,and%20one%20away%20each%20time)
[\[6\]](https://punkrockor.com/2017/10/05/sports-scheduling-meetings-business-analytics-why-scheduling-major-league-baseball-is-really-hard/#:~:text=,have%20a%20day%20off%20in)
Sports scheduling meets business analytics: why scheduling Major League
Baseball is really hard -- Laura Albert\'s Punk Rock Operations Research

<https://punkrockor.com/2017/10/05/sports-scheduling-meetings-business-analytics-why-scheduling-major-league-baseball-is-really-hard/>

[\[2\]](https://github.com/jlundgrenedge/baseball/blob/cf0ac9ff8c3218364a8618d45cffb60c13595f42/tests/archive/test_league_simulation.py#L148-L156)
[\[3\]](https://github.com/jlundgrenedge/baseball/blob/cf0ac9ff8c3218364a8618d45cffb60c13595f42/tests/archive/test_league_simulation.py#L221-L230)
[\[5\]](https://github.com/jlundgrenedge/baseball/blob/cf0ac9ff8c3218364a8618d45cffb60c13595f42/tests/archive/test_league_simulation.py#L233-L240)
[\[7\]](https://github.com/jlundgrenedge/baseball/blob/cf0ac9ff8c3218364a8618d45cffb60c13595f42/tests/archive/test_league_simulation.py#L216-L225)
[\[8\]](https://github.com/jlundgrenedge/baseball/blob/cf0ac9ff8c3218364a8618d45cffb60c13595f42/tests/archive/test_league_simulation.py#L132-L140)
[\[9\]](https://github.com/jlundgrenedge/baseball/blob/cf0ac9ff8c3218364a8618d45cffb60c13595f42/tests/archive/test_league_simulation.py#L158-L166)
[\[10\]](https://github.com/jlundgrenedge/baseball/blob/cf0ac9ff8c3218364a8618d45cffb60c13595f42/tests/archive/test_league_simulation.py#L270-L278)
[\[11\]](https://github.com/jlundgrenedge/baseball/blob/cf0ac9ff8c3218364a8618d45cffb60c13595f42/tests/archive/test_league_simulation.py#L286-L294)
[\[12\]](https://github.com/jlundgrenedge/baseball/blob/cf0ac9ff8c3218364a8618d45cffb60c13595f42/tests/archive/test_league_simulation.py#L58-L66)
[\[13\]](https://github.com/jlundgrenedge/baseball/blob/cf0ac9ff8c3218364a8618d45cffb60c13595f42/tests/archive/test_league_simulation.py#L63-L70)
[\[14\]](https://github.com/jlundgrenedge/baseball/blob/cf0ac9ff8c3218364a8618d45cffb60c13595f42/tests/archive/test_league_simulation.py#L79-L87)
[\[15\]](https://github.com/jlundgrenedge/baseball/blob/cf0ac9ff8c3218364a8618d45cffb60c13595f42/tests/archive/test_league_simulation.py#L104-L112)
[\[20\]](https://github.com/jlundgrenedge/baseball/blob/cf0ac9ff8c3218364a8618d45cffb60c13595f42/tests/archive/test_league_simulation.py#L75-L83)
[\[34\]](https://github.com/jlundgrenedge/baseball/blob/cf0ac9ff8c3218364a8618d45cffb60c13595f42/tests/archive/test_league_simulation.py#L353-L355)
[\[36\]](https://github.com/jlundgrenedge/baseball/blob/cf0ac9ff8c3218364a8618d45cffb60c13595f42/tests/archive/test_league_simulation.py#L312-L320)
[\[37\]](https://github.com/jlundgrenedge/baseball/blob/cf0ac9ff8c3218364a8618d45cffb60c13595f42/tests/archive/test_league_simulation.py#L335-L343)
[\[38\]](https://github.com/jlundgrenedge/baseball/blob/cf0ac9ff8c3218364a8618d45cffb60c13595f42/tests/archive/test_league_simulation.py#L345-L353)
test_league_simulation.py

<https://github.com/jlundgrenedge/baseball/blob/cf0ac9ff8c3218364a8618d45cffb60c13595f42/tests/archive/test_league_simulation.py>

[\[16\]](https://github.com/jlundgrenedge/baseball/blob/cf0ac9ff8c3218364a8618d45cffb60c13595f42/batted_ball/game_simulation.py#L718-L726)
[\[17\]](https://github.com/jlundgrenedge/baseball/blob/cf0ac9ff8c3218364a8618d45cffb60c13595f42/batted_ball/game_simulation.py#L184-L193)
[\[18\]](https://github.com/jlundgrenedge/baseball/blob/cf0ac9ff8c3218364a8618d45cffb60c13595f42/batted_ball/game_simulation.py#L203-L211)
[\[33\]](https://github.com/jlundgrenedge/baseball/blob/cf0ac9ff8c3218364a8618d45cffb60c13595f42/batted_ball/game_simulation.py#L292-L300)
[\[39\]](https://github.com/jlundgrenedge/baseball/blob/cf0ac9ff8c3218364a8618d45cffb60c13595f42/batted_ball/game_simulation.py#L318-L325)
[\[42\]](https://github.com/jlundgrenedge/baseball/blob/cf0ac9ff8c3218364a8618d45cffb60c13595f42/batted_ball/game_simulation.py#L658-L666)
[\[44\]](https://github.com/jlundgrenedge/baseball/blob/cf0ac9ff8c3218364a8618d45cffb60c13595f42/batted_ball/game_simulation.py#L660-L668)
game_simulation.py

<https://github.com/jlundgrenedge/baseball/blob/cf0ac9ff8c3218364a8618d45cffb60c13595f42/batted_ball/game_simulation.py>

[\[19\]](https://github.com/jlundgrenedge/baseball/blob/cf0ac9ff8c3218364a8618d45cffb60c13595f42/batted_ball/parallel_game_simulation.py#L70-L78)
[\[24\]](https://github.com/jlundgrenedge/baseball/blob/cf0ac9ff8c3218364a8618d45cffb60c13595f42/batted_ball/parallel_game_simulation.py#L140-L148)
[\[45\]](https://github.com/jlundgrenedge/baseball/blob/cf0ac9ff8c3218364a8618d45cffb60c13595f42/batted_ball/parallel_game_simulation.py#L144-L152)
[\[51\]](https://github.com/jlundgrenedge/baseball/blob/cf0ac9ff8c3218364a8618d45cffb60c13595f42/batted_ball/parallel_game_simulation.py#L10-L18)
[\[52\]](https://github.com/jlundgrenedge/baseball/blob/cf0ac9ff8c3218364a8618d45cffb60c13595f42/batted_ball/parallel_game_simulation.py#L27-L35)
[\[53\]](https://github.com/jlundgrenedge/baseball/blob/cf0ac9ff8c3218364a8618d45cffb60c13595f42/batted_ball/parallel_game_simulation.py#L321-L330)
[\[54\]](https://github.com/jlundgrenedge/baseball/blob/cf0ac9ff8c3218364a8618d45cffb60c13595f42/batted_ball/parallel_game_simulation.py#L32-L40)
[\[56\]](https://github.com/jlundgrenedge/baseball/blob/cf0ac9ff8c3218364a8618d45cffb60c13595f42/batted_ball/parallel_game_simulation.py#L328-L336)
[\[57\]](https://github.com/jlundgrenedge/baseball/blob/cf0ac9ff8c3218364a8618d45cffb60c13595f42/batted_ball/parallel_game_simulation.py#L375-L383)
[\[58\]](https://github.com/jlundgrenedge/baseball/blob/cf0ac9ff8c3218364a8618d45cffb60c13595f42/batted_ball/parallel_game_simulation.py#L390-L399)
parallel_game_simulation.py

<https://github.com/jlundgrenedge/baseball/blob/cf0ac9ff8c3218364a8618d45cffb60c13595f42/batted_ball/parallel_game_simulation.py>

[\[21\]](https://library.fangraphs.com/war/war-position-players/#:~:text=WAR%20%3D%20,Runs%20Per%20Win)
WAR for Position Players \| Sabermetrics Library

<https://library.fangraphs.com/war/war-position-players/>

[\[22\]](https://github.com/jlundgrenedge/baseball/blob/4269772e2752aa5ae28b697a1ed3d9d2680f7e1a/docs/guides/SIM_METRICS_GUIDE.md#L72-L80)
[\[23\]](https://github.com/jlundgrenedge/baseball/blob/4269772e2752aa5ae28b697a1ed3d9d2680f7e1a/docs/guides/SIM_METRICS_GUIDE.md#L74-L78)
[\[30\]](https://github.com/jlundgrenedge/baseball/blob/4269772e2752aa5ae28b697a1ed3d9d2680f7e1a/docs/guides/SIM_METRICS_GUIDE.md#L92-L100)
[\[43\]](https://github.com/jlundgrenedge/baseball/blob/4269772e2752aa5ae28b697a1ed3d9d2680f7e1a/docs/guides/SIM_METRICS_GUIDE.md#L86-L94)
[\[60\]](https://github.com/jlundgrenedge/baseball/blob/4269772e2752aa5ae28b697a1ed3d9d2680f7e1a/docs/guides/SIM_METRICS_GUIDE.md#L148-L156)
SIM_METRICS_GUIDE.md

<https://github.com/jlundgrenedge/baseball/blob/4269772e2752aa5ae28b697a1ed3d9d2680f7e1a/docs/guides/SIM_METRICS_GUIDE.md>

[\[25\]](file://file_000000004bb471f5a9156c5597b55a74#:~:text=%7C%20,LOW)
[\[26\]](file://file_000000004bb471f5a9156c5597b55a74#:~:text=1.%20,need%20to%20match%20bWAR%2FfWAR%20exactly)
[\[49\]](file://file_000000004bb471f5a9156c5597b55a74#:~:text=2.%20,validation%20tests%20must%20still%20pass)
SEASON_SIMULATION_RESEARCH_PROMPT.md

<file://file_000000004bb471f5a9156c5597b55a74>

[\[27\]](https://library.fangraphs.com/offense/wrc/#:~:text=wRC%2B%20%3D%20,100)
wRC and wRC+ \| Sabermetrics Library

<https://library.fangraphs.com/offense/wrc/>

[\[28\]](https://library.fangraphs.com/pitching/fip/#:~:text=Here%20is%20the%20formula%20for,FIP)
FIP \| Sabermetrics Library

<https://library.fangraphs.com/pitching/fip/>

[\[29\]](https://legacy.baseballprospectus.com/glossary/index.php?search=FIP#:~:text=View%20details%20for%20FIP%20,scale%20as%20earned%20run%20average)
View details for FIP - Baseball Prospectus \| Glossary

<https://legacy.baseballprospectus.com/glossary/index.php?search=FIP>

[\[31\]](https://github.com/jlundgrenedge/baseball/blob/4269772e2752aa5ae28b697a1ed3d9d2680f7e1a/batted_ball/player.py#L80-L88)
[\[32\]](https://github.com/jlundgrenedge/baseball/blob/4269772e2752aa5ae28b697a1ed3d9d2680f7e1a/batted_ball/player.py#L82-L88)
[\[40\]](https://github.com/jlundgrenedge/baseball/blob/4269772e2752aa5ae28b697a1ed3d9d2680f7e1a/batted_ball/player.py#L126-L134)
[\[41\]](https://github.com/jlundgrenedge/baseball/blob/4269772e2752aa5ae28b697a1ed3d9d2680f7e1a/batted_ball/player.py#L162-L169)
player.py

<https://github.com/jlundgrenedge/baseball/blob/4269772e2752aa5ae28b697a1ed3d9d2680f7e1a/batted_ball/player.py>

[\[35\]](https://github.com/jlundgrenedge/baseball/blob/cf0ac9ff8c3218364a8618d45cffb60c13595f42/tests/archive/LEAGUE_SIMULATION_README.md#L130-L138)
[\[48\]](https://github.com/jlundgrenedge/baseball/blob/cf0ac9ff8c3218364a8618d45cffb60c13595f42/tests/archive/LEAGUE_SIMULATION_README.md#L214-L216)
[\[50\]](https://github.com/jlundgrenedge/baseball/blob/cf0ac9ff8c3218364a8618d45cffb60c13595f42/tests/archive/LEAGUE_SIMULATION_README.md#L190-L198)
[\[55\]](https://github.com/jlundgrenedge/baseball/blob/cf0ac9ff8c3218364a8618d45cffb60c13595f42/tests/archive/LEAGUE_SIMULATION_README.md#L200-L203)
[\[59\]](https://github.com/jlundgrenedge/baseball/blob/cf0ac9ff8c3218364a8618d45cffb60c13595f42/tests/archive/LEAGUE_SIMULATION_README.md#L198-L203)
[\[62\]](https://github.com/jlundgrenedge/baseball/blob/cf0ac9ff8c3218364a8618d45cffb60c13595f42/tests/archive/LEAGUE_SIMULATION_README.md#L139-L147)
[\[63\]](https://github.com/jlundgrenedge/baseball/blob/cf0ac9ff8c3218364a8618d45cffb60c13595f42/tests/archive/LEAGUE_SIMULATION_README.md#L74-L83)
[\[64\]](https://github.com/jlundgrenedge/baseball/blob/cf0ac9ff8c3218364a8618d45cffb60c13595f42/tests/archive/LEAGUE_SIMULATION_README.md#L140-L147)
LEAGUE_SIMULATION_README.md

<https://github.com/jlundgrenedge/baseball/blob/cf0ac9ff8c3218364a8618d45cffb60c13595f42/tests/archive/LEAGUE_SIMULATION_README.md>

[\[46\]](https://github.com/jlundgrenedge/baseball/blob/4269772e2752aa5ae28b697a1ed3d9d2680f7e1a/batted_ball/database/pybaseball_fetcher.py#L26-L34)
[\[47\]](https://github.com/jlundgrenedge/baseball/blob/4269772e2752aa5ae28b697a1ed3d9d2680f7e1a/batted_ball/database/pybaseball_fetcher.py#L72-L81)
pybaseball_fetcher.py

<https://github.com/jlundgrenedge/baseball/blob/4269772e2752aa5ae28b697a1ed3d9d2680f7e1a/batted_ball/database/pybaseball_fetcher.py>

[\[61\]](https://github.com/jlundgrenedge/baseball/blob/cf0ac9ff8c3218364a8618d45cffb60c13595f42/batted_ball/database/team_database.py#L180-L188)
[\[65\]](https://github.com/jlundgrenedge/baseball/blob/cf0ac9ff8c3218364a8618d45cffb60c13595f42/batted_ball/database/team_database.py#L38-L46)
[\[66\]](https://github.com/jlundgrenedge/baseball/blob/cf0ac9ff8c3218364a8618d45cffb60c13595f42/batted_ball/database/team_database.py#L108-L116)
team_database.py

<https://github.com/jlundgrenedge/baseball/blob/cf0ac9ff8c3218364a8618d45cffb60c13595f42/batted_ball/database/team_database.py>
