# GEN_fractal_zoom
(Library name `GEN_fractal_zoom`, formerly `fractal_zoom`. Shipped as `tox/GEN/GEN_fractal_zoom.tox`.)

## Inputs
| Input | Type / purpose |
|---|---|
| (none) | No inputs, self-contained generator |

## Outputs
| Output | Label / content |
|---|---|
| out1 | render: raymarched fractal (rgba16float) |

## Loop / Clock
`Clock` (Loop page) takes a CHOP with a `phase` channel (0-1). Set it and `Timesource` = `phase`: the `Phase` parameter is then driven by that channel (clear `Clock` to go back to manual `Phase`). Use a ramp LFO renamed `phase`, or a Beat CHOP ramp renamed `phase`, to lock motion to a tempo.

GLSL raymarched fractal: Mandelbulb (power morph) or KIFS Menger sponge. Orbit, glow, AO, palettes (bone, chrome, bone+red, spectrum, mono).


| Page | Params |
|---|---|
| Controls | Resolution, Fractal, Power, Iterations, Glow, Ao, Palette, Hue, Redaccent, Contrast, Bgcolor |
| Camera | Orbitturns, Zoomdepth (bulb), Zoomloops (menger), Elevation, Tilt, Wobble, Morph, Morphmotion, Fov, Maxsteps |
| Loop | Timesource (abstime/phase), Phase, Clock, Loopseconds, Loopbeats, Bpm, Usebeats | `phase` mode: all motion is a function of Phase (0-1) and loops at Phase 0==1. Loop length = Loopseconds, or Loopbeats*60/Bpm when Usebeats is on |

Loop seamlessness: Mandelbulb: orbit angle and zoom (exp ping-pong, cos of 2*pi*Phase) and optional Morphmotion are periodic. KIFS Menger is a true infinite zoom: the camera sits on the sponge corner (1,1,1), a fixed point of the x3 self-similarity, and its distance scales by 3^-(Phase*Zoomloops). The level count is fractional (Iterations + Phase*Zoomloops, newest level cross-faded in, fractal clipped to the corner sub-cube 3^-(zoom levels) of the box, colour trap index relative to zoom level), so the frame at Phase=1 is identical to Phase=0 (mean abs diff ~1e-4, below the 0.001-phase step diff of ~3e-3). View orientation wobbles only with 2*pi*Phase.
