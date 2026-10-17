# GEN_mirror_room
(Library name `GEN_mirror_room`, formerly `mirror_room`. Shipped as `tox/GEN/GEN_mirror_room.tox`.)

## Inputs
| Input | Type / purpose |
|---|---|
| (none) | No inputs, self-contained generator |

## Outputs
| Output | Label / content |
|---|---|
| out1 | render: raymarched mirror room (rgba16float) |

## Loop / Clock
`Clock` (Loop page) takes a CHOP with a `phase` channel (0-1). Set it and `Timesource` = `phase`: the `Phase` parameter is then driven by that channel (clear `Clock` to go back to manual `Phase`). Use a ramp LFO renamed `phase`, or a Beat CHOP ramp renamed `phase`, to lock motion to a tempo.


Raymarched mirror room: a box whose six walls are mirrors carrying emissive grid lines and random light panels, with a chrome object (sphere / torus / twisted-torus knot, optionally kaleidoscope-folded) in the centre. Rays bounce up to 8 times, producing infinite receding reflections. Single GLSL TOP, no inputs.


| Page | Param | Notes |
|---|---|---|
| Controls | Speed | abstime loop-rate multiplier |
| | Shape, Objsize | Sphere / Torus / Twisted torus |
| | Bounces | reflection depth (1-8) |
| | Kaleido | 0-4 abs-folds that duplicate the object symmetrically |
| | Spin | object turns per loop (integer) |
| | Roomw/h/d, Mirror, Seed | room size, wall reflectivity, panel layout |
| Render | Palette (Mono, Bone+red, Ice, Custom), Custom, Glow, Exposure, Steps | |
| Camera | Sway, Fov | |
| Loop | Timesource (abstime/phase), Phase, Clock, Loopseconds, Loopbeats, Bpm | |

Loop: object spin/tumble, kaleidoscope wobble, camera sway and panel pulsing are all `sin/cos(2 pi p * integer)`, so Phase 0 == 1.
Tips: lower Bounces/Steps for speed; the chrome surface is naturally noisy at high bounce counts, 4-6 is a good range.
