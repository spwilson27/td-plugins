# GEN_cellular_automata
Ping-pong (Feedback TOP + GLSL TOP) cellular automaton on a float state texture (r=state, g=age, b=ghost fade). The grid is `Resolution / Cellsize`; `out1` is the nearest-neighbour colored render at `Resolution`, `out2` is the raw state texture (r = state: 0/1 life, 0/1/2 brain, 0-3 wireworld).

Input: optional `in1` TOP, used as seed (luminance > 0.5 = alive/conductor) at Reset/first frame. Unconnected -> random seed with Density.

| Par | Meaning |
|---|---|
| Rule | Game of Life / Brian's Brain / Wireworld / Larger than Life / Custom B/S |
| Rulestring | for Custom: `B36/S23`, also accepts `23/3` (S/B). Parsed in Python (`rules` DAT) into bitmasks passed as uniforms when the par changes |
| Radius | LtL neighbourhood radius (Moore square, 1-15). Birth/survive ranges are fractions of the neighbourhood on the Sim page (default = "Bugs"-like) |
| Density | random seed density (LtL likes ~0.5; Wireworld = conductor density) |
| Stepsperframe | extra GLSL passes per cook |
| Rate | max steps per second (60 = every frame) |
| Play / Reset | |
| Cellsize | pixels per cell |
| Coloring | flat / by age (young -> old color), Agerange, Ghost, Ghostdecay (fading afterimage of dead cells) |
| Color* | Dead, Alive(young), Old/Tail, Aux (Brian dying / Wireworld conductor) |
| Resolution, Seed | |

Wireworld colors: head = Alive, tail = Old, conductor = Aux. Brian: on = Alive->Old (age), dying = Aux.

## Loop page and Look (retrofit)

**Look** (Controls): `Original` (default, unchanged) or `Mono` (Rendah style: black background, bone-white/grey; implemented as a final `look` GLSL TOP in front of `out1`, no duplicated network). `Accent` adds a red accent in Mono; `Monogain` sets the mono brightness.

**Loop** page: `Timesource` (`abstime` = free-running, loops every `Loopseconds`/`Loopbeats` at `Bpm`; `phase` = driven by the `Phase` par 0-1, e.g. from a timeline or LFO). `Loopreset` toggle pulses `Reset` each time the phase wraps.

**Honest note on looping:** this is a stateful simulation, so the output is NOT a bit-exact loop. Everything that *forces* the sim is a periodic function of Phase (so the forcing repeats exactly), and with `Loopreset` on the sim restarts from its initial state at each wrap, so a recorded loop restarts identically. Without `Loopreset` the state keeps evolving and only the forcing is periodic. Periodic forcing: new `Loopinject` (Sim page, default 0) injects live cells inside a small disc (`Injectradius`) orbiting the grid once per loop.

## v2 update

Renamed from `cellular_automata` to `GEN_cellular_automata` (tox at `tox/GEN/GEN_cellular_automata.tox`; no per-frame keepalive: outputs are pulled by downstream ops).

**Inputs**: in1 (TOP, optional seed), in2 (CHOP, optional modulation). The modulation In CHOP is always the last input and reads channels `band1`-`band4`, `beat`, `phase`; missing channels are ignored. Used here: beat: injects live cells (0.4 density).

| Output | Label |
|---|---|
| out1 | render |
| out2 | state |

**Loop page**: new `Clock` CHOP parameter. With `Timesource` = `phase` the phase is read from the `phase` channel of that CHOP (instead of `Phase`). Snippets: `snippets/GEN_cellular_automata.tox` (About > Snippets).
