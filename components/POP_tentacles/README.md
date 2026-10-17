# POP_tentacles
Grow writhing tubes from the input points. POP in, POP out: one tentacle grows from every point of `in1`, away from the origin. Shipped as `tox/POP/POP_tentacles.tox`. (Formerly `GEN_tentacles`.)

## Inputs
| Input | Type / purpose |
|---|---|
| in1 | In POP: points (any POP; only its points are used, one tentacle each). With nothing connected a built-in sphere of points (in the gated `demo` COMP) is used. |
| in2 | In CHOP (optional) modulation: `band1`..`band4`, `beat`. band1 = writhing, band2 = wave, band3 = pulse, band4 = length, beat = thickness swell. |

## Outputs
| Output | Label / content |
|---|---|
| out1 | tube mesh (POP): all tentacles, with normals |

The node viewer shows the internal `preview` TOP (a small PBR render of out1, not an output). Render out1 yourself with a Geometry COMP (Select POP) + Render TOP.

## Technique
Straight tube template x N copies (Copy POP, one per input point) -> GLSL POP bends each tube along a noise-driven spine with a rebuilt ring frame -> Normal POP. The root point travels with each copy in the `Root` attribute. Direction of growth = normalized root position. Cost scales with points x Segments x Sides: thin the input points for a lighter mesh.

| Page | Params |
|---|---|
| Controls | Length, Grow, Autogrow, Speed, Seed, Segments, Sides, Thickness, Taper, Tipmin, Wiggle, Noisefreq, Wave, Wavefreq, Pulse, Pulsefreq |
| Look | Resolution, Metallic, Roughness, Basecolor, Envintensity, Redaccent, Camdist, Camheight, Bgcolor (preview render only) |

Motion uses absolute time scaled by `Speed`; Autogrow grows and retracts the tentacles continuously.
