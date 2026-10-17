# GEN_fluid_2d

Stable-fluids (Jos Stam) Eulerian solver on the GPU: semi-Lagrangian advection, divergence, warm-started Jacobi pressure solve (`Iterations` passes per frame), gradient subtraction, vorticity confinement and dissipation. All state is rgba32float in feedback loops (velocity, pressure, dye). Solid walls at the borders. Velocity is in cells per step.

**Inputs**: `in1` TOP (optional). Image colour is injected as dye (`Input Density`) and its luminance gradient (rotated 90 degrees) drives velocity along edges (`Input Velocity`). With nothing connected, only the internal animated emitters are used.
**Outputs**: `out1` coloured dye (tone-mapped), `out2` velocity (R,G, 32-bit float).

| Page | Param | Notes |
|---|---|---|
| Controls | Play, Reset, Resolution | Reset clears velocity, pressure, dye |
| | Speed | time step multiplier |
| | Iterations | Jacobi pressure iterations/frame |
| | Vorticity | confinement strength |
| | Veldissipation / Dyedissipation | per-frame decay |
| Emitter | Emitters (0-6), Splatsize, Force, Density, Emitterspeed, Huespeed | animated Lissajous splat emitters pushing velocity and injecting hue-cycling dye |
| Input | Inputdensity, Inputvelocity | in1 coupling |
| Render | Exposure, Saturation, Background | colour output |

Tips: the component keeps itself cooking via an Execute DAT (`keepalive`). Force and splat scale with Resolution height. Lower Iterations (8-12) for speed.

## Loop page and Look (retrofit)

**Look** (Controls): `Original` (default, unchanged) or `Mono` (Rendah style: black background, bone-white/grey; implemented as a final `look` GLSL TOP in front of `out1`, no duplicated network). `Accent` adds a red accent in Mono; `Monogain` sets the mono brightness.

**Loop** page: `Timesource` (`abstime` = free-running, loops every `Loopseconds`/`Loopbeats` at `Bpm`; `phase` = driven by the `Phase` par 0-1, e.g. from a timeline or LFO). `Loopreset` toggle pulses `Reset` each time the phase wraps.

**Honest note on looping:** this is a stateful simulation, so the output is NOT a bit-exact loop. Everything that *forces* the sim is a periodic function of Phase (so the forcing repeats exactly), and with `Loopreset` on the sim restarts from its initial state at each wrap, so a recorded loop restarts identically. Without `Loopreset` the state keeps evolving and only the forcing is periodic. Periodic forcing: emitters follow Lissajous paths with integer cycles per loop (cycles = round(`Emitterspeed`), so 1 at default), dye hue cycles an integer number of times per loop (round(`Huespeed` x loop length), min 1 if Huespeed>0).

## v2 update

Renamed from `fluid_2d` to `GEN_fluid_2d` (tox at `tox/GEN/GEN_fluid_2d.tox`; no per-frame keepalive: outputs are pulled by downstream ops).

**Inputs**: in1 (TOP, optional dye/force source), in2 (CHOP, optional modulation). The modulation In CHOP is always the last input and reads channels `band1`-`band4`, `beat`, `phase`; missing channels are ignored. Used here: beat: emitter Force x(1+3b), band1: dye amount x(1+2b).

| Output | Label |
|---|---|
| out1 | dye |
| out2 | velocity |

**Loop page**: new `Clock` CHOP parameter. With `Timesource` = `phase` the phase is read from the `phase` channel of that CHOP (instead of `Phase`). Snippets: `snippets/GEN_fluid_2d.tox` (About > Snippets).
