# GEN_infinite_tunnel
(Library name `GEN_infinite_tunnel`, formerly `infinite_tunnel`. Shipped as `tox/GEN/GEN_infinite_tunnel.tox`.)

## Inputs
| Input | Type / purpose |
|---|---|
| (none) | No inputs, self-contained generator |

## Outputs
| Output | Label / content |
|---|---|
| out1 | render: raymarched tunnel (rgba16float) |

## Loop / Clock
`Clock` (Loop page) takes a CHOP with a `phase` channel (0-1). Set it and `Timesource` = `phase`: the `Phase` parameter is then driven by that channel (clear `Clock` to go back to manual `Phase`). Use a ramp LFO renamed `phase`, or a Beat CHOP ramp renamed `phase`, to lock motion to a tempo.


Raymarched, domain-repeated corridor (single GLSL TOP). The camera flies down a rounded-rect tube; every segment (cell along z) is assigned a type from a hash of its index: plain, heavy ribs, emissive light strips (white or accent), or a bulkhead with a framed opening. Panel lines, AO, headlight, fog, cheap volumetric glow from emitters. No inputs.


| Page | Param | Notes |
|---|---|---|
| Controls | Speed | loops per second multiplier (abstime) |
| | Segments (per loop), Seglen, Variation | segment count travelled per loop; length; fraction of non-plain segments |
| | Width, Height, Ribdepth, Lights, Seed | geometry / emitter strength |
| Render | Palette (Bone+red, Chrome/ice, Ember, Custom), Custom, Exposure, Fog, Steps | |
| Camera | Fov, Roll, Sway | roll/sway are sin/cos(2 pi p) |
| Loop | Timesource (abstime/phase), Phase, Clock, Loopseconds, Loopbeats, Bpm | |

Loop: camera z = p * Segments * Seglen, i.e. exactly Segments cells per loop; segment variation hashes `mod(cellIndex, Segments)`, so the sequence of segments repeats after one loop. Camera roll and sway are periodic in p. Phase 0 == 1.
Limitations: raymarching cost scales with Resolution and Steps; segments are not blended (a hard cut between types is by design).
