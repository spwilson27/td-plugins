# GEN_boids

3D flocking on the GPU. Positions and velocities live in two rgba32float feedback textures (side x side, side = ceil(sqrt(Count))). A GLSL TOP does brute-force neighbour search over all `Count` boids (separation / alignment / cohesion, nearest periodic image when wrapping), clamps speed, handles box bounds (wrap or bounce) and an optional spherical obstacle. Positions/velocities/colours are converted with TOP to POP (`instance_data`) and a Copy POP stamps a tapered cone onto every boid, rotated along its velocity (rotate-to), drawn by a Geometry COMP + Render TOP with a Phong MAT.

**Inputs**: none.
**Outputs**: `out1` rendered image. `out2` instance data TOP (position texture: RGB = position, A = alive flag; `out_vel` = velocity texture; `out_pop` = Null POP with P, N (velocity), Color per boid).

| Page | Param | Notes |
|---|---|---|
| Controls | Play, Reset, Seed | Reset re-randomizes the flock |
| | Count | number of boids (4096 default; 16384 works but the O(N^2) neighbour pass costs ~27 ms/frame on the dev machine) |
| | Speed | simulation time scale |
| | Resolution | render size |
| Flocking | Separation, Alignment, Cohesion | steering weights |
| | Sepradius, Aliradius, Cohradius | neighbour radii (world units) |
| | Maxspeed, Minspeed, Maxforce, Wander | speed limits, steering limit, random turning |
| Bounds | Boundsize | half extent of the cubic box |
| | Boundmode | wrap (torus) or bounce |
| | Obstacle, Obstaclepos, Obstacleradius | spherical obstacle boids steer around (drawn as a grey sphere) |
| Render | Boidsize, Color1, Color2 | cone size; slow/fast colours (also tinted by heading) |
| | Camdist, Camspin | orbit camera |

Tips: lower Count first if the frame rate drops; the neighbour loop dominates. The component keeps itself cooking via an Execute DAT (`keepalive`).

## Loop page and Look (retrofit)

**Look** (Controls): `Original` (default, unchanged) or `Mono` (Rendah style: black background, bone-white/grey; implemented as a final `look` GLSL TOP in front of `out1`, no duplicated network). `Accent` adds a red accent in Mono; `Monogain` sets the mono brightness.

**Loop** page: `Timesource` (`abstime` = free-running, loops every `Loopseconds`/`Loopbeats` at `Bpm`; `phase` = driven by the `Phase` par 0-1, e.g. from a timeline or LFO). `Loopreset` toggle pulses `Reset` each time the phase wraps.

**Honest note on looping:** this is a stateful simulation, so the output is NOT a bit-exact loop. Everything that *forces* the sim is a periodic function of Phase (so the forcing repeats exactly), and with `Loopreset` on the sim restarts from its initial state at each wrap, so a recorded loop restarts identically. Without `Loopreset` the state keeps evolving and only the forcing is periodic. Periodic forcing: wander noise uses a fixed integer number of keyframes per loop (round(0.7 x loop length)) indexed modulo that count; `Obstacleorbit` (Bounds page, default 0) orbits the obstacle once per loop. Camera angle = `Camspin` x loop time (set 360*k/Loopseconds for seamless orbit).

## v2 update

Renamed from `boids` to `GEN_boids` (tox at `tox/GEN/GEN_boids.tox`; no per-frame keepalive: outputs are pulled by downstream ops).

**Inputs**: in1 (CHOP, optional modulation). The modulation In CHOP is always the last input and reads channels `band1`-`band4`, `beat`, `phase`; missing channels are ignored. Used here: band1: Cohesion x(1+3b), beat: Wander x(1+4b).

| Output | Label |
|---|---|
| out1 | render |
| out2 | positions |
| out3 | velocity |
| out4 | instances (POP) |

**Loop page**: new `Clock` CHOP parameter. With `Timesource` = `phase` the phase is read from the `phase` channel of that CHOP (instead of `Phase`). Snippets: `snippets/GEN_boids.tox` (About > Snippets).
