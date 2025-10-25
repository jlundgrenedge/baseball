# Time-Based Racing Implementation - Findings

## What Was Changed

Switched from distance-based outcome classification to **time-based racing** between fielders and runners.

### How It Works Now

1. **Ball lands** at position X after hang_time
2. **Fielder retrieves** ball - time = fielder speed to position
3. **Fielder throws** to bases - time = transfer + throw flight time  
4. **Runner runs** to bases - time = baserunning speed
5. **Winner determined** by comparing arrival times

This properly uses the fielding and baserunning simulators!

## Ground Ball Physics

**Question:** Do balls bounce/roll after landing?

**Answer:** No - the trajectory simulation stops when ball hits ground.
- Landing position is treated as final position
- Fielder must run to that exact spot
- No rolling or bouncing physics implemented

For realism, could add:
- Ground balls continue rolling based on exit velocity
- Roll distance = f(exit_velocity, launch_angle, field surface)
- But current approximation is reasonable

## Current Problem: Parameter Tuning

Everything is triples/HRs because race times are off:

**Debug Example:**
- Runner to 3rd: ~11 seconds  
- Ball retrieved + thrown to 3rd: ~13 seconds
- Runner wins easily → Triple

**Why:**
- Fielders too slow getting to balls?
- Runners too fast?
- Throw velocities too slow?
- Need to validate against MLB data

## Next Steps

1. Validate fielder sprint speeds against MLB  
2. Validate runner speeds (home to first ~4.2s MLB avg)
3. Validate throw velocities by position
4. Tune catch probabilities for fly balls
5. Add more ground outs (currently most ground balls → hits)

## Progress

✅ Using actual fielding/baserunning mechanics
✅ Time-based racing logic working
⚠️ Parameters need tuning for realism
