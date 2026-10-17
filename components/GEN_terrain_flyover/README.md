# GEN_terrain_flyover
(Library name `GEN_terrain_flyover`, formerly `terrain_flyover`. Shipped as `tox/GEN/GEN_terrain_flyover.tox`.)

## Inputs
| Input | Type / purpose |
|---|---|
| in1 | In TOP (optional) heightmap, used when Source = Image (mirror-sampled so it never seams) |

## Outputs
| Output | Label / content |
|---|---|
| out1 | render: final image (rgba16float) |
| out2 | terrain: solid terrain surface (POP) |

## Loop / Clock
`Clock` (Loop page) takes a CHOP with a `phase` channel (0-1). Set it and `Timesource` = `phase`: the `Phase` parameter is then driven by that channel (clear `Clock` to go back to manual `Phase`). Use a ramp LFO renamed `phase`, or a Beat CHOP ramp renamed `phase`, to lock motion to a tempo.

Retro-futurist displaced grid terrain: noise (rolling/ridged/terraced) or `in1` TOP heightmap, central valley road, wireframe/solid/both, distance fog, line glow, optional striped sun and horizon glow, occasional red grid lines.

| Page | Params |
|---|---|
| Controls | Resolution, Mode, Source, Style, Amplitude, Frequency, Zperiod, Loops (speed: lattice periods travelled per loop), Valley, Valleywidth, Gridx, Gridz, Width, Length |
| Render | Camheight, Pitch, Fov, Sway, Fogstart, Fogend, Linebright, Redaccent, Glow, Sun, Horizonglow, Wirecolor, Solidcolor, Glowcolor |
| Loop | Timesource (abstime/phase), Phase, Clock, Loopseconds, Loopbeats, Bpm, Usebeats | `phase` mode: all motion is a function of Phase (0-1) and loops at Phase 0==1. Loop length = Loopseconds, or Loopbeats*60/Bpm when Usebeats is on |

Loop seamlessness: the grid is static; the height function is sampled at z + Phase*Loops*period. Noise lattice wraps with period Zperiod cells at every octave (periodic value noise), so scrolling by an integer number of periods is identical to the start. Image mode mirrors the texture (period 2x tile) and scrolls 2 tiles per Loops. Camera sway uses 2*pi*Phase*2. Speed in world units/sec = Loops*Zperiod/Frequency/Loopseconds.
