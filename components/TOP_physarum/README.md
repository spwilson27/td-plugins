# GEN_physarum
Slime-mold (Physarum) agent simulation, fully on the GPU. 512x512 agent texture (up to 262,144 agents, rgba32float: x, y, heading, alive) updated by a GLSL TOP (sense left/front/right at Sensor Angle/Dist, turn, move). Deposits are scattered by instancing a 1px quad per agent into a Render TOP with additive blending (a GLSL MAT vertex shader reads the agent texture), then the trail map is diffused (3x3 blur) and decayed in a Feedback loop.

Outputs: `out1` = colored trail (3-stop ramp), `out2` = raw trail (R channel, 32-bit float). No inputs.
Note: like any feedback sim it only advances while something downstream cooks `out1`/`out2` (viewer, render, etc.).

| Par | Meaning |
|---|---|
| Agents | active agents (deposit only; max 262144) |
| Sensorangle | degrees between front/left/right sensors |
| Sensordist | sensor offset in pixels |
| Turnspeed | max turn per step (degrees) |
| Stepsize | pixels moved per frame |
| Deposit | trail added per agent per frame |
| Decay | trail multiplier per frame |
| Diffuse | blend towards 3x3 blur per frame |
| Gain | exposure of the color ramp |
| Color1/2/3 | ramp low/mid/high |
| Initpattern | random / disc (inward) / ring (outward) at Reset |
| Play, Reset | |
| Resolution | trail resolution (default 1280x720) |

Tips: lower Sensordist + higher Diffuse = fine veins; large Sensordist = coarse cells; Decay close to 0.9 keeps trails short-lived.

## Loop page and Look (retrofit)

**Look** (Controls): `Original` (default, unchanged) or `Mono` (Rendah style: black background, bone-white/grey; implemented as a final `look` GLSL TOP in front of `out1`, no duplicated network). `Accent` adds a red accent in Mono; `Monogain` sets the mono brightness.

**Loop** page: `Timesource` (`abstime` = free-running, loops every `Loopseconds`/`Loopbeats` at `Bpm`; `phase` = driven by the `Phase` par 0-1, e.g. from a timeline or LFO). `Loopreset` toggle pulses `Reset` each time the phase wraps.

**Honest note on looping:** this is a stateful simulation, so the output is NOT a bit-exact loop. Everything that *forces* the sim is a periodic function of Phase (so the forcing repeats exactly), and with `Loopreset` on the sim restarts from its initial state at each wrap, so a recorded loop restarts identically. Without `Loopreset` the state keeps evolving and only the forcing is periodic. Periodic forcing: new `Loopmod` (Sim page, default 0) modulates sensor angle and sensor distance by sin/cos(2*pi*Phase).

## v2 update

Renamed from `physarum` to `GEN_physarum` (tox at `tox/GEN/GEN_physarum.tox`; no per-frame keepalive: outputs are pulled by downstream ops).

**Inputs**: in1 (CHOP, optional modulation). The modulation In CHOP is always the last input and reads channels `band1`-`band4`, `beat`, `phase`; missing channels are ignored. Used here: band1: Deposit x(1+2b), band2: Turnspeed.

| Output | Label |
|---|---|
| out1 | render |
| out2 | trail |

**Loop page**: new `Clock` CHOP parameter. With `Timesource` = `phase` the phase is read from the `phase` channel of that CHOP (instead of `Phase`). Snippets: `snippets/GEN_physarum.tox` (About > Snippets).
