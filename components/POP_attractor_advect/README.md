# GEN_strange_attractors
Up to 262,144 particles (512x512 rgba32float state texture: xyz in *normalised* attractor space, a = 1 + speed) integrated on the GPU by a GLSL TOP in a Feedback loop (RK2 midpoint, `Substeps` per frame). Rendering: one instanced 1px-ish quad per particle (GLSL MAT vertex shader reads the state texture), additive blending, orbiting camera, then a feedback trail (`Trails`) and exposure tone-map.

Outputs: `out1` = additive trails render, `out2` = raw particle state texture (rgb = normalised position, a = 1 + speed). No inputs.
Note: feedback sims only advance while something downstream cooks `out1`/`out2`.

| Par | Meaning |
|---|---|
| Attractor / Attractorb | Lorenz, Aizawa, Thomas, Halvorsen, Dadras (A and B) |
| Morph | 0..1 fraction of the particle population following B. Each particle integrates a real attractor, so both shapes stay sharp while the cloud cross-fades (blending the vector fields themselves collapses to fixed points, so this is deliberate) |
| Speed | time step scale (0 freezes) |
| Scale | world size of the attractor |
| Coefmod, Coefspeed | animate the main coefficient(s) (rho, a, b, c) sinusoidally |
| Play, Reset | |
| Count | particles drawn (<= 262144) |
| Pointsize, Intensity, Exposure, Trails | render look |
| Color1/Color2, Colorspeed, Background | slow -> fast colour ramp, speed->colour gain |
| Camangle, Orbitspeed, Camdist, Camheight | camera orbit (deg, deg/s) |
| Resolution, Substeps, Seed | Sim page |

Attractors are re-centred/scaled per type (CEN/SCL/DTS tables in `step.glsl`) so they occupy a similar volume.

## Loop page and Look (retrofit)

**Look** (Controls): `Original` (default, unchanged) or `Mono` (Rendah style: black background, bone-white/grey; implemented as a final `look` GLSL TOP in front of `out1`, no duplicated network). `Accent` adds a red accent in Mono; `Monogain` sets the mono brightness.

**Loop** page: `Timesource` (`abstime` = free-running, loops every `Loopseconds`/`Loopbeats` at `Bpm`; `phase` = driven by the `Phase` par 0-1, e.g. from a timeline or LFO). `Loopreset` toggle pulses `Reset` each time the phase wraps.

**Honest note on looping:** this is a stateful simulation, so the output is NOT a bit-exact loop. Everything that *forces* the sim is a periodic function of Phase (so the forcing repeats exactly), and with `Loopreset` on the sim restarts from its initial state at each wrap, so a recorded loop restarts identically. Without `Loopreset` the state keeps evolving and only the forcing is periodic. Periodic forcing: coefficient wobble (`Coefmod`) is sin(2*pi*Phase*k) with integer k = max(1, round(Coefrate x loop length / 2pi)). Camera angle = `Orbitspeed` x loop time (set 360*k/Loopseconds for seamless orbit).

## v2 update

Renamed from `strange_attractors` to `GEN_strange_attractors` (tox at `tox/GEN/GEN_strange_attractors.tox`; no per-frame keepalive: outputs are pulled by downstream ops).

**Inputs**: in1 (CHOP, optional modulation). The modulation In CHOP is always the last input and reads channels `band1`-`band4`, `beat`, `phase`; missing channels are ignored. Used here: band1: Coefmod +0.5b, band2: Speed x(1+b).

| Output | Label |
|---|---|
| out1 | render |
| out2 | particles |

**Loop page**: new `Clock` CHOP parameter. With `Timesource` = `phase` the phase is read from the `phase` channel of that CHOP (instead of `Phase`). Snippets: `snippets/GEN_strange_attractors.tox` (About > Snippets).
