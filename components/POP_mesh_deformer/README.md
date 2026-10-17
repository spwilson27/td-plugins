# POP_mesh_deformer
Audio-reactive deformer stack (twist, bend, inflate, noise shell, ripple) on a GPU POP mesh. A filter: `in1` mesh in, deformed mesh out (`out1`, a POP). The node viewer shows an internal `preview` TOP (dark-studio chrome, PBR + procedural softbox, red rim); it is not an output.

Modulation mapping (in2): band1 -> Inflate + Bend, band2 -> Twist, band3 -> Ripple, band4 -> Noise shell; each added to its amount x Modgain.

With nothing connected, a `demo` COMP supplies a sphere/torus and fake audio bands so the preview moves. Connect `in1` and the demo is not selected (and does not cook); the fake bands are only used when nothing is connected.

| Page | Params |
|---|---|
| Controls | Twist, Bend, Inflate, Noiseshell, Noisefreq, Ripple, Ripplefreq, Ripplecycles, Noisecycles, Modgain |
| Preview | Resolution, Demoshape (sphere/torus), Detail (demo mesh density), Metallic, Roughness, Basecolor, Envintensity, Redaccent, Keyintensity, Camdist, Camheight, Orbitturns, Fov, Bgcolor (these only affect the preview TOP) |

There is no Loop page; the preview orbit/ripple animation runs from absolute time.

## Inputs and outputs
| Inputs | Type | Meaning |
|---|---|---|
| in1 | POP | mesh to deform (unconnected = demo shape) |
| in2 | CHOP | optional modulation (band1..band4, 0-1). Unconnected with in1 also unconnected = internal fake bands; with in1 connected = none |

| Outputs | Type | Label |
|---|---|---|
| out1 | POP | deformed mesh |

Render `out1` yourself, e.g. a Geometry COMP with a Select POP and a PBR MAT.
