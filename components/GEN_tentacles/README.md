# GEN_tentacles
(Library name `GEN_tentacles`, formerly `tentacles`. Shipped as `tox/GEN/GEN_tentacles.tox`.)

## Inputs
| Input | Type / purpose |
|---|---|
| in1 | In TOP (optional) equirectangular environment map, default is a procedural dark studio |

## Outputs
| Output | Label / content |
|---|---|
| out1 | render: final image (rgba16float) |
| out2 | tentacles: tentacle mesh (POP) |

## Loop / Clock
`Clock` (Loop page) takes a CHOP with a `phase` channel (0-1). Set it and `Timesource` = `phase`: the `Phase` parameter is then driven by that channel (clear `Clock` to go back to manual `Phase`). Use a ramp LFO renamed `phase`, or a Beat CHOP ramp renamed `phase`, to lock motion to a tempo.

Tube geometry along noise-driven splines growing from a sphere surface around a core: taper, pulsing thickness, writhing noise + travelling waves; chrome or matte PBR in a dark studio (softbox environment, red rim).

POP pipeline: straight tube template x N copies (Copy POP) -> GLSL POP bends each tube along a spine and rebuilds a ring frame -> Normal POP. Root position travels with the copy in the Color attribute.

| Page | Params |
|---|---|
| Controls | Resolution, Count, Length, Grow, Autogrow, Segments, Sides, Thickness, Taper, Tipmin, Wiggle, Noisefreq, Noisecycles, Wave, Wavefreq, Wavecycles, Pulse, Pulsefreq, Rootradius, Core |
| Render | Metallic (1 chrome, 0 matte), Roughness, Basecolor, Envintensity, Redaccent, Keyintensity, Camdist, Camheight, Orbitturns, Fov, Bgcolor |
| Loop | Timesource (abstime/phase), Phase, Clock, Loopseconds, Loopbeats, Bpm, Usebeats | `phase` mode: all motion is a function of Phase (0-1) and loops at Phase 0==1. Loop length = Loopseconds, or Loopbeats*60/Bpm when Usebeats is on |

Loop seamlessness: noise offset moves on a circle (Noisecycles), travelling wave and pulse phases are integer multiples (Wavecycles) of 2*pi*Phase, Autogrow is a cos of 2*pi*Phase, camera orbit is integer turns.
