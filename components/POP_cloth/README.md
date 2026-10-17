# GEN_verlet_cloth
GPU Verlet cloth. Particle grid (NxN, `Gridsize`) lives in rgba32float textures: `fb_pos` (current) and `fb_prev` (previous, a second Feedback TOP pointing at `fb_pos`). Each frame:
1. `integrate` GLSL TOP: Verlet step with gravity, noise-modulated wind (`TDSimplexNoise`), damping, sphere collision, pins.
2. `constraints` GLSL TOP: one Jacobi relaxation pass of structural + shear distance constraints and sphere projection, repeated `Iterations` times with the GLSL TOP `npasses` parameter (each pass reads the previous pass).
3. Render: a Grid SOP in a Geometry COMP, displaced by a GLSL MAT vertex shader that fetches the position texture (normals from neighbouring texels); checker-shaded two-sided with own lighting; optional sphere drawn in the same Render TOP.

Outputs: `out1` = lit render, `out2` = raw particle positions (rgb = xyz world, `Gridsize` x `Gridsize`, 32-bit float). No inputs.
Note: feedback sims only advance while something downstream cooks `out1`/`out2`.

| Par | Meaning |
|---|---|
| Pinmode | Top Row / Corners / None |
| Gravity | downward acceleration (units/s^2) |
| Wind, Winddir, Turbulence | wind strength, direction, noise gustiness |
| Damping | per-step velocity loss |
| Stiffness, Iterations | constraint strength and relaxation passes per frame (more = less stretch) |
| Collider, Spherepos, Sphereradius | sphere collider (also rendered) |
| Play, Reset | |
| Resolution, Gridsize, Clothsize, Speed | Sim page. Speed scales the time step (keep <= ~1.5 for stability) |
| Color1/2, Checker, Spherecolor, Lightdir, Camangle/dist/height, Background | Render page |

Tips: Gridsize change needs a Reset. Cloth starts flat in the XY plane at z=0 hanging from y=0.9; the sphere sits slightly behind it so the cloth drapes over it. Spherepos can be animated (e.g. CHOP export) - the collider follows.

## Loop page and Look (retrofit)

**Look** (Controls): `Original` (default, unchanged) or `Mono` (Rendah style: black background, bone-white/grey; implemented as a final `look` GLSL TOP in front of `out1`, no duplicated network). `Accent` adds a red accent in Mono; `Monogain` sets the mono brightness.

**Loop** page: `Timesource` (`abstime` = free-running, loops every `Loopseconds`/`Loopbeats` at `Bpm`; `phase` = driven by the `Phase` par 0-1, e.g. from a timeline or LFO). `Loopreset` toggle pulses `Reset` each time the phase wraps.

**Honest note on looping:** this is a stateful simulation, so the output is NOT a bit-exact loop. Everything that *forces* the sim is a periodic function of Phase (so the forcing repeats exactly), and with `Loopreset` on the sim restarts from its initial state at each wrap, so a recorded loop restarts identically. Without `Loopreset` the state keeps evolving and only the forcing is periodic. Periodic forcing: the wind turbulence samples 4D simplex noise along a circle parameterised by Phase, so the wind field repeats exactly each loop.

## v2 update

Renamed from `verlet_cloth` to `GEN_verlet_cloth` (tox at `tox/GEN/GEN_verlet_cloth.tox`; no per-frame keepalive: outputs are pulled by downstream ops).

**Inputs**: in1 (CHOP, optional modulation). The modulation In CHOP is always the last input and reads channels `band1`-`band4`, `beat`, `phase`; missing channels are ignored. Used here: band1: Wind x(1+3b).

| Output | Label |
|---|---|
| out1 | render |
| out2 | positions |

**Loop page**: new `Clock` CHOP parameter. With `Timesource` = `phase` the phase is read from the `phase` channel of that CHOP (instead of `Phase`). Snippets: `snippets/GEN_verlet_cloth.tox` (About > Snippets).
