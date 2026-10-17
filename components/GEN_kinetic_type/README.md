# GEN_kinetic_type
(Library name `GEN_kinetic_type`, formerly `kinetic_type`. Shipped as `tox/GEN/GEN_kinetic_type.tox`.)

## Inputs
| Input | Type / purpose |
|---|---|
| (none) | No inputs, self-contained generator (Text parameter sets the word) |

## Outputs
| Output | Label / content |
|---|---|
| out1 | render: kinetic type (rgba16float) |

## Loop / Clock
`Clock` (Loop page) takes a CHOP with a `phase` channel (0-1). Set it and `Timesource` = `phase`: the `Phase` parameter is then driven by that channel (clear `Clock` to go back to manual `Phase`). Use a ramp LFO renamed `phase`, or a Beat CHOP ramp renamed `phase`, to lock motion to a tempo.


Text laid out as one instanced quad per glyph in 3D (monospace Text TOP atlas, per-instance UV offset/scale), rendered additively in monochrome with optional red accent glyphs. Own Camera + Render TOP. No inputs needed.

**Output**: `out1` render (black background).

| Page | Param | Notes |
|---|---|---|
| Controls | Text | string, rendered monospace (up to ~130 chars) |
| | Mode | Scatter on beat / Slit stretch / Noise warp / Extrude (depth stack) |
| | Trigger | pulse: scatter burst (decays with Beat Decay) |
| | Autobeat, Beatsperloop | automatic beats, N per loop |
| | Amount, Decay, Stretch, Layers, Depth | mode strengths; Layers/Depth for extrude |
| Render | Fontname, Size, Spacing, Tint, Accent, Accentamt, Seed | |
| Camera | Sway, Fit, Fov, Elevation | camera auto-fits text width |
| Loop | Timesource (abstime/phase), Phase, Clock, Loopseconds, Loopbeats, Bpm | |

Loop: every motion is a function of loop phase p (p = Phase in `phase` mode, absTime*Speed/looplength otherwise). Scatter uses fract(p*Beatsperloop) (integer beats), slit uses cos(2 pi p), noise warp is a sum of sin() with integer multiples of 2 pi p, extrude/camera use sin/cos(2 pi p). So Phase 0 == 1. The manual Trigger is wall-clock based (not part of the loop).
Limitation: layers are alpha-additive quads (no real mesh extrusion); one line of text.
