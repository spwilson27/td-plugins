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

## Implementation
Built entirely from built-in POPs (no GLSL in the deformer):
- `normals_in` (Normal POP) makes sure the mesh has normals.
- `noise_shell` (Noise POP, simplex 3D, 2 octaves, combine = none) writes a noise value per point into the attribute `nv` (it does not move the points itself); its translate parameters travel on a circle through noise space so it loops.
- `deform` (Math Combine POP) does all the arithmetic as a short, commented list of steps: (1) ripples: distance from the top pole, `sin(distance * Ripplefreq - phase)`, the `exp(-0.25 * distance)` fade, then one push along the normal, `P += N * (wave * fade * Ripple*0.25 + Inflate*0.5 + noise * 0.44 * Noiseshell)`; (2) twist: rotate (x, z) by `Twist * y`; (3) bend: rotate (x, y) by `Bend * x`.
- `normals_out` (Normal POP) rebuilds normals for the output.
Only the preview's environment map (`envmap`, the shared studio-chrome texture) is still a GLSL TOP; it is not part of the deformation.

Why not the Twist POP: it was tried. Its twist matches the old twist in size but turns the opposite way, and its bend is a true circular bend, not the old curl (rotation by `Bend * x`). Both rotations are three or four steps of arithmetic, so they live in the one Math Combine, which also saves two extra full-mesh passes (each POP in the chain costs a pass over all points; the version with separate Twist POP and bend nodes benched slower).

Checked against the old shader on the same mesh with the other amounts at zero: twist, bend, ripple and inflate agree to 1e-6. The noise is Simplex (Noise POP) instead of value noise, tuned (amplitude, period) for the same lump height and size; it is not point-for-point identical.

Bench (`tools/bench.py`, 200x200 grid in, GPU ms, median of 11 interleaved runs; the machine was loaded by other jobs and individual runs spread from 0.5 to 13 ms, so treat the percentages as "about the same"):
| Size | old GLSL | native | change |
|---|---|---|---|
| 1280x720 | 0.86 | 0.92 | +6.8 % |
| 1920x1080 | 0.85 | 1.01 | +17.9 % |
