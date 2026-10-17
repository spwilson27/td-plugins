# GEN_gpu_particles

GPU particle system built from POPs: Point Generator POP (spherical emitter volume) -> Particle POP (emit rate, lifetime, count, time integration) -> Force Radial POPs (gravity + two attractors) -> Noise POP (curl noise force, added to PartForce) -> GLSL POP (age/speed colouring) -> Null POP (feedback target). Rendered as additive point sprites by a Geometry COMP + Render TOP with an orbiting camera.

**Inputs**: none.
**Outputs**: `out1` rendered image (TOP). `out2` position texture (POP to TOP of P). `out_pop` Null POP with the live particles (P, PartVel, Color, ...).

| Page | Param | Notes |
|---|---|---|
| Controls | Play, Reset | Reset re-initializes and restarts the system |
| | Count | max particles (memory allocated) |
| | Lifetime | seconds |
| | Emitrate | particles per second |
| | Emitterpos, Emitradius, Emitvelocity | emitter centre, volume radius, initial upward velocity |
| | Resolution | render size |
| Forces | Curlstrength, Curlscale, Curlspeed | curl-noise force amount, spatial frequency, evolution speed |
| | Gravity | downward acceleration |
| | Attr1pos, Attr1strength, Attr2pos, Attr2strength | radial attractors (negative strength repels) |
| | Damping | velocity damping |
| Render | Pointsize | sprite size (px) |
| | Color, Colorend | birth / death colours |
| | Brightness | sprite alpha (additive) |
| | Camdist, Camspin | camera distance, auto-orbit speed (deg/s) |

Tips: keep Count >= Emitrate x Lifetime or the emitter starves. The component keeps itself cooking via an Execute DAT (`keepalive`).

## Loop page and Look (retrofit)

**Look** (Controls): `Original` (default, unchanged) or `Mono` (Rendah style: black background, bone-white/grey; implemented as a final `look` GLSL TOP in front of `out1`, no duplicated network). `Accent` adds a red accent in Mono; `Monogain` sets the mono brightness.

**Loop** page: `Timesource` (`abstime` = free-running, loops every `Loopseconds`/`Loopbeats` at `Bpm`; `phase` = driven by the `Phase` par 0-1, e.g. from a timeline or LFO). `Loopreset` toggle pulses `Reset` each time the phase wraps.

**Honest note on looping:** this is a stateful simulation, so the output is NOT a bit-exact loop. Everything that *forces* the sim is a periodic function of Phase (so the forcing repeats exactly), and with `Loopreset` on the sim restarts from its initial state at each wrap, so a recorded loop restarts identically. Without `Loopreset` the state keeps evolving and only the forcing is periodic. Periodic forcing: curl-noise field walks a circle in noise space (radius from `Curlspeed` x loop length), `Attrorbit` (new, Forces page, default 0) orbits the two attractors once per loop. Camera angle = `Camspin` x loop time; use Camspin = 360*k/Loopseconds for a seamless orbit.

## v2 update

Renamed from `gpu_particles` to `GEN_gpu_particles` (tox at `tox/GEN/GEN_gpu_particles.tox`; no per-frame keepalive: outputs are pulled by downstream ops).

**Inputs**: in1 (CHOP, optional modulation). The modulation In CHOP is always the last input and reads channels `band1`-`band4`, `beat`, `phase`; missing channels are ignored. Used here: beat: x4 emit rate, band1: curl strength x(1+2b).

| Output | Label |
|---|---|
| out1 | render |
| out2 | particles (texture) |
| out3 | particles (POP) |

**Loop page**: new `Clock` CHOP parameter. With `Timesource` = `phase` the phase is read from the `phase` channel of that CHOP (instead of `Phase`). Snippets: `snippets/GEN_gpu_particles.tox` (About > Snippets).
