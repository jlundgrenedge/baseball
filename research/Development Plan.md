# Development Plan for a Physics-Based Baseball Simulation Game

## Overview and Goals

You are aiming to create a **text-based baseball simulation game** with
two major facets: a *physics-driven game engine* for on-field play and a
*front-office management system* for team and league management (similar
in scope to Out of the Park Baseball). The goal is to produce a
simulation that is *realistically grounded in baseball physics and
player performance metrics* – for example, modeling pitches by velocity
and spin, simulating batted ball trajectories, and determining play
outcomes based on fielders’ speed and reaction. At the same time, the
game should offer **robust management features** (rosters, trades,
seasons, etc.) to let a single-player run a team. This is an ambitious
project, so a clear architecture and iterative development plan are
crucial. We will outline a recommended architecture that separates core
components and a step-by-step plan to build the game incrementally,
ensuring you can **start simple and gradually add
complexity**[\[1\]](https://zengm.com/blog/2019/07/so-you-want-to-write-a-sports-sim-game/#:~:text=This%20is%20my%20most%20important,start%2C%20I%20might%20never%20finish).
The emphasis is on creating a working prototype early and then refining
it, given that sports sims are complex and can overwhelm a solo
developer if tackled all at
once[\[1\]](https://zengm.com/blog/2019/07/so-you-want-to-write-a-sports-sim-game/#:~:text=This%20is%20my%20most%20important,start%2C%20I%20might%20never%20finish).

## Core Architecture Components

A high-level architecture for the game should consist of distinct
modules, each handling a key aspect of the simulation. The major
components include:

- **Game Simulation Engine (Physics-Based)** – This module handles the
  on-field play-by-play simulation. It will use physics calculations and
  player stats to simulate each pitch, swing, ball in play, and fielding
  play. It outputs the outcome of games (scores, statistics,
  play-by-play text). This is effectively the “game engine” that needs
  to mimic real baseball rules and physics.
- **Data Model & Storage** – A structured way to store all game data:
  players (attributes, ratings, stats), teams, games, and seasons. Using
  a database or structured files will be important to manage this data.
  In fact, *sports simulation games generally require a database for
  teams, players, game results,
  etc*[\[2\]](https://zengm.com/blog/2019/07/so-you-want-to-write-a-sports-sim-game/#:~:text=A%20sports%20simulation%20game%20really,just%20needs%20a%20few%20things).
  For ease, you might use a simple **SQL database (SQLite)** to start,
  as it’s lightweight and can run locally with no
  setup[\[3\]](https://zengm.com/blog/2019/07/so-you-want-to-write-a-sports-sim-game/#:~:text=If%20you%20are%20still%20unsure,where%20to%20start%2C%20try%20these).
  This will hold player information, season schedules, box scores, etc.,
  and allow persistence across play sessions.
- **Front Office Management System** – This module encompasses all the
  “meta-game” features: roster management, trades, drafts, contracts,
  player development, finances, etc. It will use the data model to let
  the player (and AI-controlled teams) manage their franchise.
  Initially, this can be limited (e.g. just basic roster editing) and
  later expanded to full features (trading, scouting, etc.).
- **User Interface (UI)** – Since this is a text-based sim at first, the
  UI can be a simple console output or text UI displaying game events
  and menu options. *Starting with a basic text console is perfectly
  fine*[\[3\]](https://zengm.com/blog/2019/07/so-you-want-to-write-a-sports-sim-game/#:~:text=If%20you%20are%20still%20unsure,where%20to%20start%2C%20try%20these)
  – you can always build a prettier interface later once the core logic
  works. Eventually, you might implement a desktop UI or a web interface
  for better presentation, but separating UI from logic is wise so the
  simulation can run independently of how it’s displayed.

These components should interact but remain modular. For example, the
simulation engine can run given input data (teams, players, current game
state) and produce results, which the UI will display and the data
module will record. The management module will act on the database
(trading players, updating rosters) and feed appropriate data into the
simulation engine (e.g., which players are in the lineup for a game).
This separation will make the code more maintainable and let you improve
one part (like the physics model or the UI) without breaking others.

## Technology Stack Considerations

Choosing the right technology stack is important, especially since you
have *no budget and are a solo “vibe” coder*. You have flexibility in
language and tools, but here are some considerations:

- **Programming Language:** Use a language you are comfortable with, but
  consider performance needs. A simulation with physics and thousands of
  games might benefit from a compiled language like C++ for speed. (In
  fact, the commercial OOTP is written in C++ and uses a database for
  stats[\[4\]](https://www.reddit.com/r/OOTP/comments/127p0hi/what_is_ootp_built_with/#:~:text=SWAVcast).)
  However, if you value rapid development and ease over raw performance
  initially, **Python** is a great choice. It’s beginner-friendly and
  has many libraries for math and data handling, which can speed up
  development[\[3\]](https://zengm.com/blog/2019/07/so-you-want-to-write-a-sports-sim-game/#:~:text=If%20you%20are%20still%20unsure,where%20to%20start%2C%20try%20these).
  Python was even used in a recent baseball sim project for
  pitch-by-pitch game simulation (with Flask for a web
  UI)[\[5\]](https://devpost.com/software/historic-matchup-simulator#:~:text=,Hit%20distance%20estimation).
  Many hobbyist sports sims (e.g., Basketball GM) are written in
  high-level languages like JavaScript or Python because they allow
  quick iteration. Given your “for fun” approach, you might start with
  Python for the prototype, then optimize or rewrite critical parts in
  C++ or another faster language if needed once the concept is proven.
  The key is to *start coding in whatever language lets you make
  progress*[\[6\]](https://zengm.com/blog/2019/07/so-you-want-to-write-a-sports-sim-game/#:~:text=,as%20above%2C%20anything%20is%20fine)
  – you can always change later if performance demands it.
- **Database / Data Storage:** As mentioned, a SQL database is a solid
  choice for storing structured data (players, teams, stats). **SQLite**
  is recommended for a single-developer project: it’s file-based,
  zero-setup, and can be accessed easily from Python, C++, or most
  languages[\[3\]](https://zengm.com/blog/2019/07/so-you-want-to-write-a-sports-sim-game/#:~:text=If%20you%20are%20still%20unsure,where%20to%20start%2C%20try%20these).
  This will let you persist league data, quickly query player stats, and
  not worry about writing complex file I/O code. If you prefer not to
  start with SQL, you could use in-memory data structures or simple
  JSON/XML files to save data, but those become harder to manage as
  complexity grows. Using a DB from the start for core entities
  (players, teams, games) will pay off when you expand features. *(For
  example, OOTP stores all player stats in a database file for
  efficiency)[\[4\]](https://www.reddit.com/r/OOTP/comments/127p0hi/what_is_ootp_built_with/#:~:text=SWAVcast).*
- **Physics Engine / Libraries:** Since you want a physics-based
  simulation, decide whether to use an existing physics engine or
  implement the physics logic yourself. For a text-based game, you don’t
  need a full 3D game engine; you can do the physics calculations in
  code or use a lightweight physics library. One approach is to leverage
  known libraries or frameworks:
- A 2D physics engine (like **Box2D** or **Chipmunk**) could simulate
  ball flight and collisions in a plane (treating the field as flat).
  However, baseball flight is actually a 3D problem (ball has vertical
  movement), so a 3D physics engine like **Bullet** or even a game
  engine’s built-in physics (Unity’s PhysX, etc.) could model the
  trajectory. Using a full game engine for a text sim might be overkill,
  but it’s an option if you later want to visualize the plays.
- Alternatively, given that ballistic trajectories can be computed from
  formulas, you can implement the physics yourself with math libraries
  (e.g., using Python’s math and maybe NumPy for efficiency). In fact,
  community projects exist which simulate baseball trajectories with
  high accuracy using numerical
  methods[\[7\]](https://baseballaero.com/umba/#:~:text=so,spin%20rate%2C%20tilt%2C%20and%20gyro)[\[8\]](https://www.mathworks.com/matlabcentral/fileexchange/73825-baseball-flight#:~:text=Equations%20of%20motion%20are%20solved,top%2C%20side%2C%20or%20back%20spin).
  For example, the **UMBA** Python project takes a ball’s initial
  velocity, angle, and spin and uses a 4th-order Runge-Kutta integration
  to compute its flight path, accounting for gravity, air drag, and
  Magnus lift from
  spin[\[7\]](https://baseballaero.com/umba/#:~:text=so,spin%20rate%2C%20tilt%2C%20and%20gyro)[\[9\]](https://baseballaero.com/umba/#:~:text=be%20expandable%20and%20modifiable%20so,method%20will%20never%20cause%20any).
  Another example is a MATLAB script that simulates pitched or hit ball
  trajectories with drag and spin
  step-by-step[\[8\]](https://www.mathworks.com/matlabcentral/fileexchange/73825-baseball-flight#:~:text=Equations%20of%20motion%20are%20solved,top%2C%20side%2C%20or%20back%20spin).
  These illustrate that to get *real-world accuracy* you may need to
  incorporate aerodynamics and solve differential equations for the
  ball’s motion. However, you **don’t need to start with full
  complexity** – you could begin with simpler physics (e.g., a parabolic
  trajectory with fixed drag) and add detail later. The key is that your
  architecture should allow plugging in a more detailed physics model
  when you’re ready.
- **External Data and APIs:** For realism, you might eventually want to
  use real-world data – for instance, Statcast metrics (pitch
  velocities, spin rates, exit velocities distributions) to calibrate
  your physics engine. MLB’s public StatsAPI provides historical data
  and stats which could feed your
  game[\[10\]](https://devpost.com/software/historic-matchup-simulator#:~:text=,Defensive%20positioning).
  In the aforementioned hackathon project, they used MLB StatsAPI for
  historical team/player data and even machine learning models for era
  normalization[\[11\]](https://devpost.com/software/historic-matchup-simulator#:~:text=,Defensive%20positioning).
  While this may be beyond the initial scope, keep in mind that real
  data can help ensure your simulation produces *accurate statistics and
  outcomes*. Designing your player data model to easily import or adjust
  to real stats (like using an attribute for a batter’s average exit
  velocity, or a pitcher’s typical fastball speed) will make it easier
  to calibrate the simulation.
- **Multiplayer & Online Considerations:** Since you mentioned possibly
  adding multiplayer (for online leagues) in the long term, it’s good to
  design with *separation of concerns* so the simulation can run as a
  back-end service if needed. In early development, focus on
  single-player, but keep in mind that making the game logic
  deterministic and decoupled from a single GUI will help if you later
  wrap it in a server for multiplayer. Using networking or a web
  framework (like Flask/Django if Python) could come later. The DevPost
  project we discussed used a Flask server and Socket.IO to send updates
  to a browser client in
  real-time[\[5\]](https://devpost.com/software/historic-matchup-simulator#:~:text=,Hit%20distance%20estimation)
  – a similar approach could be taken if you go online. But this is a
  future enhancement; **initially, keep it offline and simple** (which
  aligns with your PC/offline preference).

In summary, a sensible starting stack is **Python + SQLite for
development** (quick to get running), using libraries like NumPy or
perhaps PyGame (if you want to handle some 2D geometry or visuals). You
can simulate the physics with custom code or integrate a physics library
if needed. Later, if performance is an issue (for example, simulating
many seasons or complex trajectories is too slow in Python), you could
optimize by moving critical loops to C++ or using compiled Python
extensions. Many projects start in a high-level language and optimize
later – the priority is to get a working game loop first.

## Simulation Engine Design (Physics-Based Gameplay)

Designing the simulation engine is the heart of this project. This
engine will be responsible for producing realistic play outcomes based
on player abilities and physics. Here we outline how to approach
building this engine:

- **Player Attributes and Physics Inputs:** Define what attributes your
  players have that affect in-game events. For pitchers, key attributes
  might include pitch velocity (for each pitch type), spin rate, pitch
  control/accuracy, etc. For batters: bat swing speed, contact skill,
  power (which could translate to exit velocity and launch angle
  distribution), plate discipline, etc. Fielders need speed (running
  speed), fielding ability (affecting reaction time and catch success),
  and throwing strength. These attributes will feed into your physics
  model. For example, a pitcher’s 98 MPH fastball with a high spin rate
  will have a certain trajectory (with backspin causing lift) – your
  engine might use that to calculate where the pitch goes and how hard
  it is to hit. Likewise, a batter’s swing speed and contact point on
  the bat will determine the exit velocity and angle of the batted ball.
  Start by **choosing a set of core metrics** (you can expand later)
  that are both intuitive and have data available. Modern baseball
  analytics provide typical ranges: e.g., a bat exit velocity can reach
  120+ MPH for top power hitters, pitch spin rates around 2500 RPM for
  fastballs, etc. Using these as inputs will allow the physics
  calculations to produce outputs like how far a ball travels or how
  much a pitch breaks.

- **Pitch Simulation:** To simulate an at-bat, you’ll likely break it
  down pitch-by-pitch. You can simplify actual pitching mechanics by
  treating each pitch as an event with a probabilistic outcome (strike,
  ball, in-play contact, etc.) influenced by the pitcher’s and batter’s
  stats. However, since you want physics-based realism, you might
  simulate the pitch trajectory to some extent. A full physics sim of a
  pitch would involve solving the trajectory with drag and Magnus effect
  to see how it moves (like a curveball’s break). This is complex and
  might be overkill just to decide if the batter hits it, so you could
  incorporate a simplified model: for instance, use the pitcher’s spin
  and velocity to calculate a *“hittability”* factor (a very high
  velocity, high-spin pitch is harder to hit squarely). You could
  determine whether the batter makes contact via a function that
  considers pitch difficulty vs batter skill, plus randomness for
  realism. **If no contact**, the result is a ball/strike (with pitcher
  control vs batter eye determining likelihood of a walk or strikeout as
  the at-bat progresses). **If contact is made**, move to the next
  stage: batted ball outcome.

- **Batted Ball Physics:** This is where a true physics engine shines.
  When the bat meets the ball, you have an initial velocity vector for
  the ball (the “exit velocity” and launch angle). You can generate this
  based on the pitch and swing. A simplistic approach is to assign an
  average exit velocity for the batter and use a random variation around
  it (modified by pitch speed – e.g., hitting a fast pitch squarely
  yields higher exit velocity). A more advanced approach is using
  physics formulas: the exit velocity could be a function of the bat’s
  speed, the pitch’s speed (some energy is transferred), and the quality
  of contact (e.g., perfect contact vs off the end of the bat). The
  launch angle depends on swing and pitch alignment – you might have the
  batter’s hitting profile influence the distribution of grounders vs
  fly balls. Initially, you might use a probabilistic model (e.g.,
  batter has X% chance to hit a fly ball vs grounder given contact) and
  assign a random launch angle and speed. As the project matures, you
  could incorporate *real equations or experimental data* for collision
  between bat and ball. For now, once you determine an exit velocity
  (say 100 MPH) and a launch angle (say 20 degrees above horizontal),
  you have an initial trajectory for the ball.

- **Ball Flight Simulation:** Using the initial velocity vector from
  contact, simulate the flight of the ball through the field. If doing
  this purely with math, you’d update the ball’s position in small time
  steps, applying forces: gravity (always pulling down), and aerodynamic
  drag (which decelerates the ball). If you include spin, apply the
  Magnus force which can cause the ball to lift or curve
  sideways[\[8\]](https://www.mathworks.com/matlabcentral/fileexchange/73825-baseball-flight#:~:text=Equations%20of%20motion%20are%20solved,top%2C%20side%2C%20or%20back%20spin).
  For example, a backspin will create an upward lift, keeping the ball
  in the air longer (this is what gives well-hit fly balls extra carry
  resulting in home runs). You might incorporate a simplified drag
  formula (drag ~ c \* v^2) to reduce speed over time, and a Magnus
  effect if spin is significant. There are well-known physics models
  from baseball research (Professor Alan Nathan’s work on baseball
  trajectories is a great resource, as referenced by
  UMBA[\[12\]](https://baseballaero.com/umba/#:~:text=you%20can%20input%20some%20conditions,and%20the%20spin%20rate)[\[9\]](https://baseballaero.com/umba/#:~:text=be%20expandable%20and%20modifiable%20so,method%20will%20never%20cause%20any)).
  As a starting point, you could assume a constant drag coefficient and
  ignore spin, just to get a basic trajectory (a parabola). This will
  already let you estimate where a ball will land and how long it stays
  aloft. The output of this simulation is the path of the ball:
  particularly the **landing spot** (or if it hits the ground after a
  certain distance) and the **hang time** (time from hit to either
  ground or being caught). These two pieces are crucial for determining
  play outcomes: how far the ball went (could it be a double? a home run
  if over the fence?) and whether a fielder had time to catch it.

- **Fielding and Play Outcome:** Given the ball’s trajectory, you
  determine what happens in play. Represent the positions of fielders on
  the field (for simplicity, fix fielders in standard positions, e.g.,
  an outfielder might start at a certain coordinate relative to home
  plate). When a ball is put in play, calculate which fielder is the
  “likely fielder” (e.g., a ball to the left side of the outfield would
  be handled by the left fielder). Then compute if that fielder can make
  the play: essentially compare the *time the ball is in the air* vs the
  *time the fielder needs to reach the landing spot*. The fielder’s
  running speed (and initial reaction) will determine how quickly they
  can cover the distance. For instance, if an outfielder can run 30 feet
  per second and the ball will land in 4 seconds at a spot 100 feet away
  from their starting point, can they get there in time? You might also
  add a reaction delay based on fielding ability (an elite fielder might
  react immediately, a poor fielder loses, say, 0.5 seconds). If the
  fielder reaches the spot before or just as the ball arrives, it’s an
  out (caught). If not, the ball drops for a hit. Then you decide the
  hit type: if it wasn’t caught, was it a grounder that got through
  (likely a single), a line drive to the gap (maybe a double if it rolls
  far), or a deep fly that fell in? You can use the landing distance and
  hang time to classify: e.g., a ball that lands in the outfield with
  short hang time might be a single; one that lands very deep or rolls
  to the wall could be a double or triple; anything over the fence is a
  home run by rule. This part can be initially simplified to just
  determine single/double/triple by random choice weighted by how far
  the ball went. As you refine, incorporate more logic (like if the
  ball’s landing spot is near a foul line maybe a double down the line,
  etc.). Also consider infield vs outfield: a ball with a low launch
  angle might be a grounder that either becomes an out or a single
  through the infield depending on if a fielder reaches it (this would
  involve simulating infielders and their range). You don’t have to
  model every bounce of the ball; you can approximate that a grounder
  not fielded cleanly in X time becomes a single, etc.

- **Game Rules and State Management:** Your engine also must manage the
  baseball rules: outs, innings, base running, scoring, etc. Once a ball
  is in play and the outcome (out or hit with a certain base
  advancement) is determined, update the game state. If it’s an out,
  increment outs; if outs reach 3, inning half ends, etc. If it’s a hit,
  advance the runners accordingly (there’s logic needed for how far
  runners advance on singles vs doubles – you can use simple rules or
  probability models). Keep track of scores, and at the end of 9 innings
  (or extra if tied) conclude the game. All these are *non-physics game
  logic* but essential for a complete sim. You’ll need to also handle
  substitutions (like if you later add AI managers swapping pitchers,
  but for a start you could skip mid-game substitutions to keep it
  simple).

- **Stat Tracking:** As the engine simulates, it should record
  statistics from the plays. Every at-bat and play outcome will update
  player stats (e.g., batter gets a hit, RBI, etc., pitcher gets an
  earned run or strikeout, fielder gets a putout). This ties into the
  data model – you might update an in-memory representation and later
  commit to the database. Having a *Game object* that accumulates a box
  score and a *Player stats object* for season stats would be useful.
  The final output of a game simulation is a box score and possibly a
  play-by-play log (since it’s text-based, you could even generate
  commentary like "Player X hits a deep fly to left... caught by the
  left fielder" – this can be simple templated text initially, and
  expanded for flavor later).

- **Accuracy and Calibration:** Once the basic simulation is running,
  you will likely need to tweak the physics parameters and probability
  distributions to achieve realistic results. Sports games are held to
  high standards of realism, and small changes in parameters can affect
  league-wide stats
  significantly[\[13\]](https://www.gamedeveloper.com/design/the-designer-s-notebook-designing-and-developing-sports-games#:~:text=realism,such%20a%20challenge%20to%20developers).
  You may simulate a large number of games (or even whole seasons) and
  see if the outcomes (batting averages, ERA, frequency of home runs,
  etc.) match real MLB averages. Calibration might involve adjusting how
  pitch speed translates to strikeouts, or how exit velocity translates
  to distance (using known benchmarks – e.g., 100 MPH at 25° might be a
  home run ~400 ft). The **DevPost project** you saw lists this balance
  as a challenge: *balancing simulation speed with detail and developing
  accurate physics models for hit
  outcomes*[\[14\]](https://devpost.com/software/historic-matchup-simulator#:~:text=,physics%20models%20for%20hit%20outcomes).
  Expect to iterate on the physics formulas with feedback from test
  simulations. Over time, you can incorporate more advanced physics
  (wind, park dimensions, weather effects, spin divergence like seam
  effects) if desired, but these are icing on the cake. The core is to
  get a reasonably accurate physics-based outcome model that produces
  believable stats.

By structuring the simulation in the above way, you essentially have a
**pipeline for each at-bat**: Generate pitch -\> Determine contact -\>
Simulate ball flight -\> Determine fielding/outcome -\> Update game
state. This loop repeats until the game is over. The engine should be
written as a self-contained module (or set of classes) that you can
call, for example, `simulate_game(teamA, teamB)` and it runs through
using the current rosters and returns a result. This will make it easy
to integrate with the larger system (like season simulation or UI calls)
and to test in isolation.

## Front Office Management Module

The front office or management side will make your game more than just
individual matches – it turns it into a *career or season simulation*.
This module will handle everything that happens off the field, and it
will heavily utilize the database of players and teams. Key features and
how to develop them:

- **Player and Team Database:** At the core, create a data structure or
  database tables for **players** and **teams**. Each player entry
  should store permanent info (name, age, etc.), ratings/attributes (the
  skills that feed the simulation engine, as discussed), and their
  current stats and team. Team entries will have team info (city, name)
  and perhaps references to roster players. Early on, you can populate
  this with fictional data – maybe generate a bunch of players with
  random attributes or use an existing dataset (there are open databases
  like the Lahman database for historical players if you want real
  names/stats, or the MLB Stats API as mentioned). But to keep it
  simple, start with a handful of teams and auto-generate players for
  them. The ZenGM blog suggests even making all players identical at
  first[\[15\]](https://zengm.com/blog/2019/07/so-you-want-to-write-a-sports-sim-game/#:~:text=Keep%20your%20initial%20application%20code,only%20way%20to%20do%20it)
  – this can help test the simulation without worrying about balancing
  ratings. Later, you can diversify player skills and see the impact.

- **Season and Schedule Simulation:** Implement structures for a
  **season schedule** (which teams play each other when) and standings.
  Initially, you might skip a complex schedule and just allow playing
  one game at a time. But if full front-office is a goal, you’ll want to
  simulate entire seasons. Create a schedule (round-robin or a simple
  set of series) and then loop through games in order, using the
  simulation engine for each. After each game, update team wins/losses
  and player stats in the database. At the end of the schedule,
  determine playoff qualifiers if you plan to have playoffs (this can be
  added later; a first version could just declare the team with best
  record the champion). Season simulation also ties into **player
  fatigue or usage** – for example, you might need to rotate pitchers (a
  starting pitcher shouldn’t pitch every game). That adds complexity
  with lineup management, but you can start with a simplistic approach
  (like each team has a fixed rotation and you auto-select a pitcher
  based on game number).

- **Roster Management and Lineups:** Provide a way for the user to see
  their roster and set a lineup or rotation. In the simplest text UI,
  this could be menus where you list players and allow swapping who is
  at each position or who is the starting pitcher. Under the hood, the
  game should enforce rules (e.g., a player has a position or some
  rating at positions to determine fielding ability). Representing
  positions and checking that lineups are valid (no duplicates, someone
  covers each position) is needed. Early on, you might hard-code lineups
  or use a default ordering. Eventually, the user will want to manage
  this. The management module can contain functions like
  `set_lineup(team, players_ordered_list)` and validate it. The **AI for
  other teams** can simply use a default or randomly shuffle a
  reasonable lineup until you implement something smarter.

- **Transactions (Trades, Free Agency, Draft):** These features are what
  allow multi-season continuity and the “full OOTP experience”, but they
  can be phased in gradually:

- **Trades:** Start by allowing the human player to initiate a trade.
  This involves selecting players from each side and swapping them.
  You’ll need rules to prevent imbalance (e.g., roster size limits) and
  possibly AI acceptance logic (AI evaluates the trade offer). A simple
  version might allow free trading without AI gatekeeping (since it’s
  single-player, the user could “cheat”, but it’s fine at first).
  Implementing an AI GM to negotiate trades is complex; you can postpone
  that or use very simple heuristics (like overall rating comparisons or
  salary matches if finances are in play).

- **Free Agency:** If you have contracts and player aging, free agency
  would mean unassigned players can be signed. For an initial version,
  you might not model contracts at all – every player is just on a team
  until traded. If so, free agency isn’t needed yet. Later if you add
  contracts and offseason, you’d have a pool of free agents and teams
  can sign them (AI would need logic to bid or pick players).

- **Draft/New Players:** Similar to free agency, an initial version
  could skip this. If you run multiple seasons, you’ll need a way to
  bring in new players (like rookies). You could auto-generate some new
  players each year and assign them via a simple draft order or just
  randomly. OOTP has a full amateur draft; you can implement a
  simplified version when you get there.

- **Player Development:** Over multiple seasons, players should improve
  or decline based on age or performance. You can include a basic aging
  curve (e.g., players peak at 27-30, then decline). This will affect
  their attributes which in turn affect simulation. At first, you might
  keep attributes static, but keep in mind to design your data such that
  attributes can change season to season (maybe store a “current rating”
  and possibly a “potential” rating if you want a system like that).

- **Finances:** Things like budgets, salaries, ticket prices, etc., are
  *deep* features and can be one of the last things you add (if at all).
  They add realism for a management sim, but they can also be abstracted
  (not every sports sim includes detailed financials). If you do plan to
  include them, you’d need to store contract values and durations for
  players, and team budget info. AI then has to consider budgets in
  roster moves. It’s a lot, so it may be wise to defer this until core
  gameplay is rock solid.

- **User Interaction for Management:** Design how the player (user) will
  perform front-office actions. Likely through menus: e.g., “View
  Roster” (list players with stats and ratings), “Make Trade” (select a
  team and players), “Simulate to Next Game/Day”. If you’re doing a
  console interface, you might have text commands or numbered menus. The
  front-office module should provide the functions that the UI calls.
  For instance, a function
  `trade_players(teamA, playerA, teamB, playerB)` that swaps those
  players in the data and updates any necessary records. By separating
  the logic (in the management module) from the actual input mechanism,
  you could later plug in a different UI (GUI or web) without changing
  how trades are processed in the backend.

- **AI Opponent Management:** In a single-player experience, the user
  controls one team and all others are AI-run. You will need at least
  rudimentary AI for other teams’ roster management. This includes
  setting their lineups, rotating pitchers, possibly making trades or
  signing free agents. Early on, you can **hard-code the AI behavior**
  to something simple, like always keep the highest-rated players in the
  lineup, or never make trades at all until you implement that. The AI
  can be as simple or complex as you want – many solo developers leave
  advanced AI for last because it’s challenging to get right. For
  example, you might simulate other games in the league without detailed
  physics (just use some random or simplified sim for non-user games to
  save time, or actually simulate all games if you want consistent
  physics-driven results everywhere – which could be CPU intensive). The
  Devpost project managed *pitch-by-pitch simulation for any
  matchup*[\[16\]](https://devpost.com/software/historic-matchup-simulator#:~:text=The%20MLB%20Historical%20Matchup%20Simulator,It),
  but that was likely on-demand rather than a whole season of games at
  once. If simulating an entire league, you might have to make a
  trade-off on detail vs speed (perhaps simulate user’s games with full
  detail and AI vs AI games with a faster abstraction). In any case,
  plan the management AI in layers: start with static or minimal
  behavior, and iterate.

In essence, the management module transforms your project from a
**single-game simulator** into a **full-fledged simulation league**. It
will interact heavily with the database and use the game engine
repeatedly to simulate many games. Keep the boundaries clear: for
example, the management system decides “simulate today’s games” and
calls the game engine for each scheduled match, then collects results
and updates standings. This way the game engine is unaware of seasons or
leagues – it just knows how to simulate one game given two teams’
rosters. This modularity is important for clarity and testing.

## Development Roadmap (Iterative Plan)

Now that we have outlined the architecture and major pieces, it’s
important to approach building this in **manageable phases**. Attempting
to code everything at once would be overwhelming. Below is a
step-by-step development plan, where each phase results in a working
increment of the game. This aligns with the advice to *“make a minimal
playable game, and iterate on
it”*[\[1\]](https://zengm.com/blog/2019/07/so-you-want-to-write-a-sports-sim-game/#:~:text=This%20is%20my%20most%20important,start%2C%20I%20might%20never%20finish).
You’ll start with the simplest version of a playable baseball sim and
then gradually add features and complexity:

1.  **Phase 0 – Initial Setup and Planning:** Set up your development
    environment with the chosen language and tools. Initialize a version
    control repository (git) to track your progress. Lay out the basic
    project structure with placeholders for core modules (e.g., files or
    classes for `GameEngine`, `Player`, `Team`, `LeagueManager`, etc.).
    Also design your initial database schema or data structures. At
    minimum, sketch tables for players, teams, and
    games[\[17\]](https://zengm.com/blog/2019/07/so-you-want-to-write-a-sports-sim-game/#:~:text=Once%20you%20have%20your%20technologies,come%20up%20with%20these%20tables).
    For example: a `players` table with attributes (name, team_id,
    ratings like speed, power, etc.), a `teams` table (name, etc.), and
    perhaps a `games` table for results. Don’t worry about getting the
    schema perfect now – you can evolve it as
    needed[\[18\]](https://zengm.com/blog/2019/07/so-you-want-to-write-a-sports-sim-game/#:~:text=,all%20those%20rows).
    The goal is to have a scaffolding in place so you can start coding
    functionality.

2.  **Phase 1 – Minimal Game Simulation (Prototype):** Aim to get a
    single game simulation working in the most basic form. At this
    stage, **keep the game logic very simple** – even if it’s not
    physics-based yet. For instance, you could simulate a game by
    generating random scoring or using very rudimentary probabilities
    for events. The idea is to ensure you can go through the flow of a
    game: from first inning to last, produce a final score, and maybe a
    basic box score. This might mean, for now, each at-bat is decided by
    a random outcome (e.g., 1/3 chance of a hit, etc.), or using
    placeholder values for players (all players identical or with random
    stats)[\[19\]](https://zengm.com/blog/2019/07/so-you-want-to-write-a-sports-sim-game/#:~:text=Keep%20your%20initial%20application%20code,only%20way%20to%20do%20it).
    By doing this, you will exercise your game loop, your data
    structures, and identify any missing pieces in managing innings,
    outs, runs, etc. It won’t be realistic – but it will be *playable*.
    Print out a line or two per inning or per play so you can see the
    game progressing. For example: “Team A 1 - Team B 0 after 1 inning”
    or even play-by-play like “Player X grounded out. 2 outs.” This
    gives you immediate feedback and a sense of accomplishment, which is
    crucial for a long project. Remember the ZenGM creator’s advice:
    *get something playable ASAP, even if “horrible” by final
    standards*[\[20\]](https://zengm.com/blog/2019/07/so-you-want-to-write-a-sports-sim-game/#:~:text=And%20keep%20your%20initial%20GUI,Maybe%20add%20a%20standings%20view).

3.  **Phase 2 – Basic User Interface (Text-Based):** Once the skeleton
    game sim works, improve the interface for input/output. Develop a
    simple menu system in the console or terminal. Options could
    include: “Play a game” (which triggers the simulation between two
    teams), “View Teams/Players” (which lists the current rosters or
    player stats). At this point, you can hardcode two teams to play or
    allow the user to select teams from a list. The focus is to ensure
    the user can initiate a game and see the results in a readable
    format. Format the output nicely: for example, show line scores or a
    brief box score at the end of the game. This phase is about making
    sure the *data flows* from simulation to user and to storage. Save
    the game result to the database (or a file) if possible, and confirm
    you can retrieve it (e.g., a “Game History” view).

4.  **Phase 3 – Implement Core Physics in the Simulation:** Now that you
    have a basic loop, start replacing the simplistic game logic with
    your *physics-based model*. This is a big phase, likely requiring
    the most research and testing. Tackle it in sub-steps:

5.  **Pitch and Hit Modeling:** Introduce the concept of pitches and
    at-bats. Instead of deciding an at-bat outcome with one random roll,
    simulate pitch-by-pitch. You can initially simplify outcome
    probabilities using player ratings (e.g., use batter’s contact vs
    pitcher’s control to decide if the ball is hit or missed). But when
    contact happens, use your physics calculations to determine what
    happens to the ball. Implement a function to calculate the
    trajectory of a batted ball given an initial angle and velocity.
    Start with no air resistance for simplicity (straight physics:
    distance = (v^2 \* sin(2θ)) / g for a projectile in a vacuum, etc.),
    then add a constant drag to shorten that distance to more realistic
    values. Incorporate hang time calculation (either derived
    analytically or via small time-step simulation). At this point, you
    might integrate a physics library if you decided on one, or write a
    custom integrator. **Test this heavily in isolation** – feed in
    known values: for example, if you hit a ball at 100 MPH at 30°, does
    your code give roughly a 400-foot distance and ~5 second hang time
    (which is ballpark for a home run)? Adjust parameters until the
    outcomes seem reasonable.

6.  **Fielding Logic:** Add player speed and fielding into the equation.
    Determine if a ball is catchable using the method described earlier
    (compare fielder distance vs ball flight time). This requires you to
    decide on a coordinate system for the field. A simple approach: use
    a 2D top-down coordinate system in feet (with home plate at (0,0),
    x-axis along one baseline, y-axis along the other, for instance).
    Place fielders at approximate coordinates (e.g., center fielder at
    (0,300) if 300 feet out in center field). You don’t have to be
    perfect – approximate positions are fine to start. When a ball is
    hit, you’ll compute its landing point (x,y). Find the nearest
    fielder (depending on if x,y is in infield or outfield). Then
    compute if that fielder can reach (x,y) in time. If yes, mark the
    hit as an out (fly out or line out). If not, it’s a hit. If it’s a
    ground ball (maybe identified by a low launch angle), determine if
    an infielder gets it in time (for grounders, time is basically the
    time to reach the ball’s path before it gets through). You could use
    a simplified approach like comparing a fielder’s range attribute to
    the distance – for now, something basic like if grounder within 20
    feet of an infielder’s position, it’s an out (to approximate routine
    groundouts), otherwise it’s through for a single.

7.  **Outcomes and Advancements:** Now ensure your game logic uses these
    physics outcomes to resolve plays. If out, great – record it. If
    hit, determine 1B/2B/3B/HR. You can use the ball’s final location:
    if the ball went over the fence (i.e., distance beyond outfield
    wall), call it a home run and score all runners appropriately. If
    it’s a fly ball that dropped, likely a single or double depending on
    distance from the batter and how long it took (e.g., if it drops in
    shallow outfield maybe a single, if it goes to the wall maybe double
    or triple). Grounders that get through the infield are usually
    singles, unless down the line into the corner (which could be a
    double). There is a lot of nuance, but you can simplify: perhaps use
    random chance or a threshold on distance to decide extra bases.
    Implement base runner advancement logic: on a single, runners
    advance one base (two if they had a head start with 2 outs maybe),
    on a double, two bases, etc., roughly. This doesn’t have to be
    perfect; just believable.

8.  **Testing Physics Integration:** After integrating physics, simulate
    a bunch of games or at least at-bats to see if things make sense.
    Are you getting a plausible number of hits vs outs? If every ball is
    a hit, maybe your fielders are too slow or your contact rate is too
    high; if every hit is a home run, you might need to dial down exit
    velocities. Adjust player ratings or physics parameters accordingly.
    This is an iterative process. You could automate some tests (e.g.,
    1000 random at-bats) to gather average outcomes and compare to known
    baseball stats (roughly 20% hits, ~\\2% homers per AB in real MLB,
    etc.). The goal is *statistical accuracy* over many games, which was
    a proud accomplishment of that hackathon
    project[\[21\]](https://devpost.com/software/historic-matchup-simulator#:~:text=Accomplishments%20that%20we%27re%20proud%20of).
    You likely won’t nail it in one try, so iterate and refine.

9.  **Phase 4 – Complete Game & Season Framework:** At this stage, your
    game engine should be capable of simulating a full game with
    reasonable (if not perfect) realism. Now integrate that with a
    season/league structure. Create a schedule (even a simple one like
    each team plays each other team a fixed number of times). Implement
    a loop to simulate all games in a day/round and update standings.
    Ensure the database records all game results. Build a standings view
    in the UI to show wins/losses. This will transform your project from
    just a single exhibition game simulator into a basic **league
    simulator**. It might be useful to implement saving/loading of the
    league state (especially if you’re not using a persistent DB yet) so
    that the user can play multiple sessions of a season.

10. **Phase 5 – User Management Controls:** Now bring in more of the
    front-office features for the user:

11. Allow the player to **manage lineups** and pitching rotation. Create
    a menu where they can reorder their lineup or choose a starting
    pitcher for the next game. Have the game engine reference these
    choices when simulating. Also, apply simple fatigue rules: e.g.,
    once a pitcher starts, mark them unavailable for the next 4 games or
    so (to mimic rotation).

12. Implement a basic **roster view** where the user can see player
    stats (maybe their season batting average, home runs, etc., which
    should be tallied from the games).

13. Start tracking **player progression** if you plan to have multi-year
    play. Perhaps at season end, you increase or decrease player ratings
    slightly based on age or performance.

14. If you’re ready, allow **trades**: for now, it could be as simple as
    an option where the user picks one of their players and one from
    another team and swaps them. No AI acceptance criteria initially
    (you can assume any trade goes through). This will let the user
    start shaping their team.

15. **Phase 6 – AI Improvements:** With core gameplay and basic
    management in place, turn attention to AI for the other teams. Up to
    now, you might have given other teams static lineups and no ability
    to change. Enhance the AI so that it *at least* manages obvious
    things: use a rotation for starting pitchers, replace injured or
    extremely tired players (if you simulate injuries/fatigue), and
    maybe make the occasional roster move. You can program the AI to
    evaluate players by an overall rating and always try to field the
    best ones. For trades, you could implement a simple evaluation:
    e.g., AI will only accept a trade if the total rating of players it
    receives is \>= the total rating of players it gives up (plus some
    random variance to mimic personality). This doesn’t have to be
    perfect – just not completely exploitable. The complexity of AI can
    grow indefinitely, so decide on a reasonable stopping point where
    the AI provides some challenge but you don’t spend endless time
    here. At least ensure the AI teams play through seasons without
    major issues (they don’t all keep a tired pitcher in forever or
    leave a roster spot empty, for example).

16. **Phase 7 – Polishing the Simulation and Stats:** By now you have a
    fully playable simulation game with management. Now you can iterate
    on **polish and realism**. This includes:

17. **Balancing and Accuracy:** Run many simulations (maybe simulate 10
    seasons and gather league averages) to see if the stats align with
    reality. Tweak the physics model or player ratings distribution if,
    say, league batting average is .310 (too high) or only 0.5 home runs
    per game (too low). Possibly introduce difficulty levels or sliders
    where certain factors can be tuned by the user (like overall offense
    level).

18. **Enhanced Physics Details:** If you haven’t already, you can try
    adding more detailed physics now that the game works. For example,
    incorporate a **Magnus effect** for the ball’s trajectory so that
    backspin really affects distance (there are formulas available for
    lift force based on spin rate). Or add wind as a factor that can
    influence ball flight on a given day. These can add to variability
    and realism. Make sure to verify that these additions don’t break
    your previous balance – adjust accordingly.

19. **Better Play-by-Play Descriptions:** Improve the text commentary to
    be more engaging. Instead of dry output like “Out, flyball”, make
    it, “Jones hits a towering fly ball to left... caught on the warning
    track!” This is mostly a content creation task (writing templates
    for various plays) and can greatly increase the immersion in a
    text-based game. The hackathon project even used an AI language
    model to generate game
    commentary[\[22\]](https://devpost.com/software/historic-matchup-simulator#:~:text=,game%20statistics%20and%20highlights),
    but you can achieve a lot with templated text and random variations.

20. **User Interface Enhancements:** If you started on console, consider
    if you want to move to a simple GUI. This could be using a library
    like Tkinter (for Python) or perhaps a web-based UI (since you know
    Flask was used in one
    project[\[5\]](https://devpost.com/software/historic-matchup-simulator#:~:text=,Hit%20distance%20estimation)).
    A GUI can display information more nicely (tables for stats, etc.)
    and handle input more cleanly. It’s not necessary for the game to
    function, but polish-wise it helps attract players. Alternatively,
    you can keep it console but refine how information is displayed
    (clearer formatting, maybe ASCII art of a field for fun, etc.).

21. **Bug fixing and Edge Cases:** As you polish, pay attention to odd
    cases: Does the simulation handle extra innings? What about rare
    plays (maybe inside-the-park homers vs errors – you might abstract
    errors as a random event where a fielder fails to make a routine
    play, resulting in extra bases)? Are there any crashes if a certain
    condition happens (like running out of players, etc.)? Firm up those
    to make the simulation robust.

22. **Phase 8 – Additional Features (Optional/Future):** With a solid
    single-player experience in hand, you can consider the “stretch
    goals”:

23. **Multiplayer or Online Leagues:** If you want to allow others to
    join, you could implement an online mode. This would involve
    networking: possibly turning your sim engine into a server that
    multiple clients connect to for a draft or to play out a league
    together. Given your earlier preference, this might be far down the
    line. But architecturally, because you separated logic from UI and
    used a DB, it’s feasible: you’d essentially share the database and
    have some synchronization. This is a project in itself, but
    mentionable as a long-term plan.

24. **Graphics/Visualization:** Although a text sim can remain text, you
    might later integrate simple graphics to visualize plays (even a 2D
    top-down view of the field with a dot for the ball). This could be
    done with a library (maybe Pygame or a web canvas). It’s not core to
    the game’s mechanics, but it can make the physics-based nature more
    satisfying to see.

25. **Expanded Management Depth:** Add that financial system, more
    intricate contract negotiations, minor leagues (reserve rosters or
    prospects to develop), coaching staff effects, etc., if you desire.
    Each of these adds complexity but can make the sim deeper. For
    example, a financial model where each team has a budget and players
    have salaries means you need to generate revenue (attendance, etc.)
    and have AI that doesn’t sign all the best players due to budget.
    OOTP has a very detailed financial engine (which can even be tweaked
    via
    settings)[\[23\]](https://www.ootpdevelopments.com/ootp65/corefeatures.php#:~:text=Developments%20www,prices%20and%20team%20cash%20reserves);
    you can choose which aspects (if any) are important to your vision.

Throughout development, maintain a cycle of adding features and then
**testing/refining**. Keep your builds running – it’s better to have a
simpler game that works than a half-implemented complex feature that
crashes the game. Given that you are coding for fun, follow your
interests: if the physics part excites you more, focus on that early; if
you love the management side, you might flesh out more of that in
between working on the engine. Just guard against trying to perfect one
aspect without having a playable structure; that’s why this plan
encourages getting a basic version up first.

## Conclusion

Building a baseball simulation game with this scope is a **challenging
but rewarding project**. The developmental architecture outlined above
emphasizes modular design (separating the simulation engine, data
management, and front office logic) and an iterative approach to
implementation. Start with the fundamentals – a database, a basic sim
loop, and a simple
interface[\[2\]](https://zengm.com/blog/2019/07/so-you-want-to-write-a-sports-sim-game/#:~:text=A%20sports%20simulation%20game%20really,just%20needs%20a%20few%20things)[\[3\]](https://zengm.com/blog/2019/07/so-you-want-to-write-a-sports-sim-game/#:~:text=If%20you%20are%20still%20unsure,where%20to%20start%2C%20try%20these)
– and gradually layer on complexity, from realistic physics calculations
to full league management features. By doing so, you’ll always have a
working game at each step that you can play and improve, rather than a
massive unfinished system. Remember that even experienced developers
find sports sims tough because of the demand for realism and detail; as
one hobbyist who built a baseball sim noted, it was *“the most difficult
thing I’ve ever done”* due to the advanced physics and complex systems
involved[\[24\]](https://www.reddit.com/r/gamedev/comments/5a239s/my_experience_developing_a_baseball_hitting/#:~:text=Ya%2C%20as%20difficult%20as%20learning,to%20paint%20using%20only%20math).
However, with persistence and incremental progress, you can create a
unique game that marries the deep management of OOTP with a new
physics-based on-field experience. Good luck, and enjoy the process of
bringing your baseball simulation to life!

**Sources:** The plan above draws on insights from sports sim developers
and projects. For example, Jeremy Scheff’s blog on making sports sims
emphasizes starting simple and
iterating[\[1\]](https://zengm.com/blog/2019/07/so-you-want-to-write-a-sports-sim-game/#:~:text=This%20is%20my%20most%20important,start%2C%20I%20might%20never%20finish)[\[15\]](https://zengm.com/blog/2019/07/so-you-want-to-write-a-sports-sim-game/#:~:text=Keep%20your%20initial%20application%20code,only%20way%20to%20do%20it).
A recent MLB simulator hackathon project demonstrated using Python with
custom physics algorithms for realistic pitch and hit
outcomes[\[11\]](https://devpost.com/software/historic-matchup-simulator#:~:text=,Defensive%20positioning)[\[21\]](https://devpost.com/software/historic-matchup-simulator#:~:text=Accomplishments%20that%20we%27re%20proud%20of).
Baseball physics research (e.g., Alan Nathan’s work and open-source
simulations) provides guidance on modeling ball trajectories with forces
like drag and Magnus
effect[\[7\]](https://baseballaero.com/umba/#:~:text=so,spin%20rate%2C%20tilt%2C%20and%20gyro)[\[8\]](https://www.mathworks.com/matlabcentral/fileexchange/73825-baseball-flight#:~:text=Equations%20of%20motion%20are%20solved,top%2C%20side%2C%20or%20back%20spin).
Additionally, community discussions note that OOTP itself is built in
C++ with a database
backend[\[4\]](https://www.reddit.com/r/OOTP/comments/127p0hi/what_is_ootp_built_with/#:~:text=SWAVcast),
and that even a one-person project can surpass expectations if
well-focused (as seen in a Redditor’s successful baseball
sim)[\[24\]](https://www.reddit.com/r/gamedev/comments/5a239s/my_experience_developing_a_baseball_hitting/#:~:text=Ya%2C%20as%20difficult%20as%20learning,to%20paint%20using%20only%20math).
All these sources underpin the recommended architecture and development
strategy. Remember to consult these and other resources as needed during
development – there’s a lot of collective wisdom in the sports sim
community that can help you on your journey. Good luck and have fun
coding your baseball world!

------------------------------------------------------------------------

[\[1\]](https://zengm.com/blog/2019/07/so-you-want-to-write-a-sports-sim-game/#:~:text=This%20is%20my%20most%20important,start%2C%20I%20might%20never%20finish)
[\[2\]](https://zengm.com/blog/2019/07/so-you-want-to-write-a-sports-sim-game/#:~:text=A%20sports%20simulation%20game%20really,just%20needs%20a%20few%20things)
[\[3\]](https://zengm.com/blog/2019/07/so-you-want-to-write-a-sports-sim-game/#:~:text=If%20you%20are%20still%20unsure,where%20to%20start%2C%20try%20these)
[\[6\]](https://zengm.com/blog/2019/07/so-you-want-to-write-a-sports-sim-game/#:~:text=,as%20above%2C%20anything%20is%20fine)
[\[15\]](https://zengm.com/blog/2019/07/so-you-want-to-write-a-sports-sim-game/#:~:text=Keep%20your%20initial%20application%20code,only%20way%20to%20do%20it)
[\[17\]](https://zengm.com/blog/2019/07/so-you-want-to-write-a-sports-sim-game/#:~:text=Once%20you%20have%20your%20technologies,come%20up%20with%20these%20tables)
[\[18\]](https://zengm.com/blog/2019/07/so-you-want-to-write-a-sports-sim-game/#:~:text=,all%20those%20rows)
[\[19\]](https://zengm.com/blog/2019/07/so-you-want-to-write-a-sports-sim-game/#:~:text=Keep%20your%20initial%20application%20code,only%20way%20to%20do%20it)
[\[20\]](https://zengm.com/blog/2019/07/so-you-want-to-write-a-sports-sim-game/#:~:text=And%20keep%20your%20initial%20GUI,Maybe%20add%20a%20standings%20view)
So you want to write a sports simulation game « Blog « ZenGM

<https://zengm.com/blog/2019/07/so-you-want-to-write-a-sports-sim-game/>

[\[4\]](https://www.reddit.com/r/OOTP/comments/127p0hi/what_is_ootp_built_with/#:~:text=SWAVcast)
What is OOTP built with? : r/OOTP

<https://www.reddit.com/r/OOTP/comments/127p0hi/what_is_ootp_built_with/>

[\[5\]](https://devpost.com/software/historic-matchup-simulator#:~:text=,Hit%20distance%20estimation)
[\[10\]](https://devpost.com/software/historic-matchup-simulator#:~:text=,Defensive%20positioning)
[\[11\]](https://devpost.com/software/historic-matchup-simulator#:~:text=,Defensive%20positioning)
[\[14\]](https://devpost.com/software/historic-matchup-simulator#:~:text=,physics%20models%20for%20hit%20outcomes)
[\[16\]](https://devpost.com/software/historic-matchup-simulator#:~:text=The%20MLB%20Historical%20Matchup%20Simulator,It)
[\[21\]](https://devpost.com/software/historic-matchup-simulator#:~:text=Accomplishments%20that%20we%27re%20proud%20of)
[\[22\]](https://devpost.com/software/historic-matchup-simulator#:~:text=,game%20statistics%20and%20highlights)
Historic Matchup Simulator \| Devpost

<https://devpost.com/software/historic-matchup-simulator>

[\[7\]](https://baseballaero.com/umba/#:~:text=so,spin%20rate%2C%20tilt%2C%20and%20gyro)
[\[9\]](https://baseballaero.com/umba/#:~:text=be%20expandable%20and%20modifiable%20so,method%20will%20never%20cause%20any)
[\[12\]](https://baseballaero.com/umba/#:~:text=you%20can%20input%20some%20conditions,and%20the%20spin%20rate)
UMBA – Baseball Aerodynamics

<https://baseballaero.com/umba/>

[\[8\]](https://www.mathworks.com/matlabcentral/fileexchange/73825-baseball-flight#:~:text=Equations%20of%20motion%20are%20solved,top%2C%20side%2C%20or%20back%20spin)
Baseball Flight - File Exchange - MATLAB Central

<https://www.mathworks.com/matlabcentral/fileexchange/73825-baseball-flight>

[\[13\]](https://www.gamedeveloper.com/design/the-designer-s-notebook-designing-and-developing-sports-games#:~:text=realism,such%20a%20challenge%20to%20developers)
The Designer's Notebook: Designing and Developing Sports Games

<https://www.gamedeveloper.com/design/the-designer-s-notebook-designing-and-developing-sports-games>

[\[23\]](https://www.ootpdevelopments.com/ootp65/corefeatures.php#:~:text=Developments%20www,prices%20and%20team%20cash%20reserves)
Out of the Park Baseball: Features - OOTP Developments

<https://www.ootpdevelopments.com/ootp65/corefeatures.php>

[\[24\]](https://www.reddit.com/r/gamedev/comments/5a239s/my_experience_developing_a_baseball_hitting/#:~:text=Ya%2C%20as%20difficult%20as%20learning,to%20paint%20using%20only%20math)
My experience developing a baseball hitting simulation : r/gamedev

<https://www.reddit.com/r/gamedev/comments/5a239s/my_experience_developing_a_baseball_hitting/>
