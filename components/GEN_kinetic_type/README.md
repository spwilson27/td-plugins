# GEN_kinetic_type
Shipped as `tox/GEN/GEN_kinetic_type.tox`. Lays a text string out as one POP point per glyph and animates each glyph with kinetic motion. It outputs geometry (POP), not a render; the node viewer shows an internal `preview` render.

## Inputs
| Input | Purpose |
|---|---|
| in1 | modulation CHOP (optional): `band1`-`band4`, `beat`. band1 boosts motion Amount, band2 boosts slit Stretch, beat fires a scatter kick. |

## Outputs
| Output | Content |
|---|---|
| out1 | glyph instances (POP): one point per glyph (times Layers in Extrude mode) |
| out2 | text mesh (POP): plain Text POP of the string (Text, Fontname), unanimated |

### out1 point attributes
| Attribute | Meaning |
|---|---|
| `P` | glyph position (laid out along X, centred, plus motion) |
| `rotation` | vec3 Euler degrees |
| `scale` | vec3 (x, y, 1) |
| `glyph` | glyph index in the string (0..N-1, spaces included) |
| `layer` | layer index (0 except in Extrude mode) |
| `Color` | Tint, blended to Accent for accent glyphs, with brightness |
| `uvrect` | vec4: atlas offset xy and scale zw (slit mode squeezes it); use to texture a quad with a glyph atlas |

Instance a quad or box on out1 with a Geometry COMP (instance op = out1, `P(0..2)`, `rotation(0..2)`, `scale(0..2)`, `Color(0..3)`, texture coords `uvrect`).

## Parameters
| Page | Param | Notes |
|---|---|---|
| Controls | Text | the string |
| | Mode | Scatter on beat / Slit stretch / Noise warp / Extrude (depth stack) |
| | Speed | motion speed (absTime based, preview/motion only) |
| | Trigger | pulse: scatter burst (decays with Decay) |
| | Autobeat, Beatspercycle | automatic beats, N per 8 s cycle at Speed 1 |
| | Amount, Decay, Stretch, Layers, Depth | mode strengths; Layers/Depth for extrude |
| | Fontname, Size, Spacing, Seed | |
| Look | Tint, Accent, Accentamt | glyph colours (Color attribute) |

Limitations: glyph pitch is a fixed monospace grid (out2's font advance may differ slightly); one line of text; the preview uses an atlas quad per glyph (no real extrusion).
