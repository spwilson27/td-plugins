# POP_pointcloud_dissolve
Filter: an `in1` mesh/POP (or an `in2` depth/luma TOP) becomes a fine point cloud (output POP with Color + pointscale) that a moving threshold (plane / orbiting sphere / radial) erodes; eroded points scatter with curl noise + dust and fade, then re-form. Render `out1` with point sprites. The node viewer shows an internal `preview` TOP (additive point sprites + glow); it is not an output.

With nothing connected, a `demo` COMP supplies a blob/sphere/torus (and a noise heightfield for Source = Image); it is not selected when `in1` is connected and does not cook then.

| Page | Params |
|---|---|
| Controls | Source (Input POP or Image), Density, Dissolve (0-1 manual), Auto (+Autocycles, Automax), Wavemode, Axisx/y/z, Edgewidth, Scatter, Jitter, Drift, Noisefreq, Noisecycles, Depth, Invertluma |
| Preview | Resolution, Demoshape (blob/sphere/torus), Pointsize, Brightness, Edgeglow, Glow, Camdist, Camheight, Orbitturns, Fov |

There is no Loop page. Auto dissolve is a periodic function of absolute time (12 s cycle x Autocycles); turn Auto off and drive Dissolve for manual or external control.

## Inputs and outputs
| Inputs | Type | Meaning |
|---|---|---|
| in1 | POP | mesh converted to the point cloud (unconnected = demo shape) |
| in2 | TOP | depth/luma image for Source = Image (unconnected = animated demo noise) |

| Outputs | Type | Label |
|---|---|---|
| out1 | POP | points (displaced, with Color) |

## Implementation
Built from built-in POPs; there is no GLSL in the component (the preview render uses the Point Sprite MAT, Blur and Composite TOPs). Left to right:
- Sources: `src_switch` (Switch POP) picks the demo shape, `in1`, or the image heightfield (`src_grid` Grid POP -> `image_lookup` Lookup Texture POP samples the in2 TOP at each point's Tex -> `image_heightfield` Math Combine: luma, optional invert, Z = (luma - 0.5) * Depth). Only the selected input cooks. `normals_in` (Normal POP) and `lum_default` (Attribute POP: `lum` = 1 for mesh sources, left alone for the image source) follow.
- `jitter_noise` (Noise POP, writes `jn`) and `curl_noise` (Noise POP, curl 3D, writes `cv`) only write attributes; they do not move points. Both travel on a circle through noise space (`Noisecycles`), so the loop is seamless.
- `dissolve` (Math Combine POP) is the whole effect as a list of steps (in build.py, commented): the erosion-front coordinate for the three Wavemodes (plane / orbiting sphere / radial, chosen by mixing), `e = smoothstep((front - (tw + jitter)) / width)`, the scatter (curl swirl + drift + outward push + random dust, all growing with e), the shading (lit grey or image luma, edge glow), the alpha fade, and the writes to `P`, `Color` and `PointScale`. The per-point random numbers are the same hash the shader used (`fract(sin(pointIndex*12.9898 + k*78.233)*43758.5453)`, from the `_PointI` attribute). The node creates its own `Color` attribute; temporary attributes are deleted at the end.
- The demo `blob` is a Sphere POP, Transform POP (stretch), Noise POP (lumps along the normals) and a small Math Combine (nose bump); the demo images were already native.

Why one big Math Combine: every extra POP costs a fixed GPU pass (about 0.02 to 0.06 ms each here), while extra steps inside a Math Combine are almost free, so the arithmetic lives in one node and only the noises are separate nodes.

Differences from the old shader: Simplex noise (Noise POP, tuned for matching amplitude and feature size) replaces the hand-rolled value noise and the finite-difference curl, so the swirl pattern is not identical. The look and every parameter are unchanged.

Bench (`tools/bench.py`, 200x200 grid in, GPU ms, median of 9 interleaved runs; the machine was loaded by other jobs, so treat the percentages as "about the same"):
| Size | old GLSL | native | change |
|---|---|---|---|
| 1280x720 | 3.41 | 3.83 | +12.3 % |
| 1920x1080 | 3.95 | 4.20 | +6.4 % |
