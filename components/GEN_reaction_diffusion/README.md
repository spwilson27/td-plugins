# GEN_reaction_diffusion

Gray-Scott reaction-diffusion on the GPU. A feedback loop around a GLSL TOP, run `Steps` times per frame (TOP Num Passes), 32-bit float state (R = A, G = B).

**Inputs**: `in1` (TOP, optional) - mask used for seeding: bright areas seed chemical B on Reset. If unconnected, random blobs plus a central seed are used.

**Outputs**: `out1` colorized result (4-stop colour ramp on B with bump lighting), `out2` raw state (R=A, G=B).

| Page | Param | Notes |
|---|---|---|
| Controls | Preset | custom / coral / mitosis / labyrinth / spots / worms - sets Feed & Kill |
| | Feed, Kill | Gray-Scott feed/kill rates |
| | Diffa, Diffb | diffusion of A / B (1.0 / 0.5 typical) |
| | Steps | solver iterations per frame (1-60) |
| | Play | run / freeze |
| | Reset | re-seed (from in1 if connected) |
| | Resolution | sim and output size |
| Render | Color1-4 | ramp stops, low to high B |
| | Contrast | scales B before ramp |
| | Bump | lighting strength |
| Sim | Dt | time step (keep <= 1) |
| | Seed | random seed (re-seeds on Reset) |

Tips: Reset after changing Resolution. Unusual Feed/Kill pairs may die out; try presets first.

## Loop page and Look (retrofit)

**Look** (Controls): `Original` (default, unchanged) or `Mono` (Rendah style: black background, bone-white/grey; implemented as a final `look` GLSL TOP in front of `out1`, no duplicated network). `Accent` adds a red accent in Mono; `Monogain` sets the mono brightness.

**Loop** page: `Timesource` (`abstime` = free-running, loops every `Loopseconds`/`Loopbeats` at `Bpm`; `phase` = driven by the `Phase` par 0-1, e.g. from a timeline or LFO). `Loopreset` toggle pulses `Reset` each time the phase wraps.

**Honest note on looping:** this is a stateful simulation, so the output is NOT a bit-exact loop. Everything that *forces* the sim is a periodic function of Phase (so the forcing repeats exactly), and with `Loopreset` on the sim restarts from its initial state at each wrap, so a recorded loop restarts identically. Without `Loopreset` the state keeps evolving and only the forcing is periodic. Periodic forcing: new `Loopmod` (Sim page, default 0) modulates Feed/Kill by sin/cos(2*pi*Phase).

## v2 update

Renamed from `reaction_diffusion` to `GEN_reaction_diffusion` (tox at `tox/GEN/GEN_reaction_diffusion.tox`; no per-frame keepalive: outputs are pulled by downstream ops).

**Inputs**: in1 (TOP, optional seed mask), in2 (CHOP, optional modulation). The modulation In CHOP is always the last input and reads channels `band1`-`band4`, `beat`, `phase`; missing channels are ignored. Used here: band1: Feed +15%.

| Output | Label |
|---|---|
| out1 | render |
| out2 | state |

**Loop page**: new `Clock` CHOP parameter. With `Timesource` = `phase` the phase is read from the `phase` channel of that CHOP (instead of `Phase`). Snippets: `snippets/GEN_reaction_diffusion.tox` (About > Snippets).
