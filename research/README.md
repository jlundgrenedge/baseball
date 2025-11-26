# Research

Physics research papers and theoretical foundations for the Baseball Physics Simulator.

## Papers

| Paper | Description |
|-------|-------------|
| **Modeling Baseball Batted Ball Trajectories...** | Core trajectory physics - drag, Magnus, spin decay |
| **Bat Ball Physics Collision Physics** | Impact mechanics, COR, exit velocity modeling |
| **Modeling Baseball Pitching Dynamics** | Pitch trajectories, spin effects, movement |
| **Modeling Baseball Fielding and Baserunning** | Fielder mechanics, route efficiency, sprint physics |
| **Launch Angle Distributions...** | Statistical distributions, angle-dependent modeling |
| **PyBaseball for Physics-Based Simulation** | Data integration methodology |
| **Baseball Simulation Fielding Improvements** | Advanced fielding physics framework |
| **Baseball Simulation Model Enhancement Plan** | Comprehensive physics model design |

## Usage

These papers provide the **theoretical foundation** for `constants.py` coefficients and physics models. When tuning physics:

1. Reference the relevant paper for empirical basis
2. Cross-validate with `python -m batted_ball.validation` (7/7 tests required)
3. Test with real MLB games via `game_simulation.bat` → Option 8

## Archive

`/archive/` contains historical diagnostic scripts and one-off analysis results.
