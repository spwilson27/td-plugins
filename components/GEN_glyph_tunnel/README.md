# GEN_glyph_tunnel
(Library name `GEN_glyph_tunnel`, formerly `glyph_tunnel`. Shipped as `tox/GEN/GEN_glyph_tunnel.tox`.)

## Inputs
| Input | Type / purpose |
|---|---|
| (none) | No inputs, self-contained generator |

## Outputs
| Output | Label / content |
|---|---|
| out1 | render: glyph tunnel / wall / rain (rgba16float) |

## Loop / Clock
`Clock` (Loop page) takes a CHOP with a `phase` channel (0-1). Set it and `Timesource` = `phase`: the `Phase` parameter is then driven by that channel (clear `Clock` to go back to manual `Phase`). Use a ramp LFO renamed `phase`, or a Beat CHOP ramp renamed `phase`, to lock motion to a tempo.


Infinite tunnel / wall / rain of characters, fully in one GLSL TOP. A monospace Text TOP builds the glyph atlas from `Charset`; the shader ray-casts a cylinder (tunnel) or tilted plane (wall, rain), picks a glyph per cell, flickers/refreshes glyphs, and applies depth fog, travelling brightness waves, and red accent glyphs. No inputs.

**Output**: `out1`.

| Page | Param | Notes |
|---|---|---|
| Controls | Mode | Tunnel / Wall / Rain |
| | Charset | string of characters in the atlas |
| | Speed, Cols, Looprows | travel speed; columns around/across; rows of travel per loop |
| | Fog, Density, Flickersteps | depth fog; fraction of bright cells; glyph changes per loop |
| | Refresh (pulse), Seed | re-roll all glyphs |
| Render | Tint, Accent, Accentamt, Brightness, Trail, Fontname | |
| Camera | Sway, Rollturns, Fov | |
| Loop | Timesource (abstime/phase), Phase, Clock, Loopseconds, Loopbeats, Bpm | |

Loop: travel is `p * Looprows` rows (integer), cell hashes use `row mod Looprows` and flicker step `mod Flickersteps`, rain columns fall an integer multiple of Looprows per loop, waves are cos(2 pi (row/Looprows - p)), camera sway/roll are sin/cos(2 pi p). Therefore the image at Phase 0 equals Phase 1. Speed scales how many loops per second pass in abstime mode.
