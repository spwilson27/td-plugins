# POP_plexus_points
"Data scan" point cloud filter, grey/white on black: the points of an `in1` POP (or points sampled where an `in2` TOP is bright) get strata banding (horizontal slices with per-band scan offsets), a sweeping scan plane, GPU plexus lines between near neighbours (Proximity POP: Linkdistance, Maxlinks) and a few random long straight lines. Outputs are POPs; render them yourself. The node viewer shows an internal `preview` TOP (dots + lines + optional cross-mark grid + glow); it is not an output.

With nothing connected, a `demo` COMP supplies a blob/sphere/torus (and a noise image for Source = Image). It is not selected when `in1` is connected and does not cook then.

| Page | Params |
|---|---|
| Controls | Source (Input POP or Image luma), Points, Linkdistance, Maxlinks, Longlines, Longspread, Pointsize, Lineopacity, Longopacity, Brightness, Banding (0-1 snap to slices), Bands, Bandshift, Bandsteps, Sweep, Sweepcycles, Jitter, Scale, Threshold, Imgsamples, Imgdepth |
| Preview | Resolution, Demoshape (blob/sphere/torus), Camdist, Camheight, Orbitturns, Orbitrange (0 = fixed camera), Fov, Grid, Gridsize, Glow |

There is no Loop page; sweep, orbit and glitch steps run from absolute time.
Limits: dots are square sprites; line opacity is uniform; Points above ~8000 slow the proximity search.

## Inputs and outputs
| Inputs | Type | Meaning |
|---|---|---|
| in1 | POP | points to turn into the cloud (unconnected = demo shape) |
| in2 | TOP | luma image sampled for Source = Image |

| Outputs | Type | Label |
|---|---|---|
| out1 | POP | point cloud (with Color / pointscale attributes; render as point sprites) |
| out2 | POP | plexus lines |
| out3 | POP | long lines |

## Implementation
No GLSL. The old shaders (`cloud`, `longlines`, `grid`, the seed-attribute shader) are now Math Combine / Random / Lookup Texture / Transform POPs and Rectangle TOPs. The rest (Proximity POP plexus lines, Delete POP `drop`, dots, preview render) was already native.
* **Sources**: the demo head-ish blob is the sphere squashed (Math Combine), bumped by a **Noise POP** along the normals and given a face bump and jaw hint (Math Combine); sphere and torus are the Sphere / Torus POPs. An `in1` POP gets `N = normalize(P)`. `scale` multiplies by `Scale`. For Source = image, a Grid POP goes through Texture Map POP + **Lookup Texture POP** (brightness `Lum`) and a Math Combine lifts `z` by `(Lum - 0.5) * Imgdepth`.
* **Strata**: `strata_slices` snaps `y` into `Bands` slices; `strata_random` (Lookup Texture POP over the `random_table` Noise TOP, pixel index = slice number x glitch step) gives each slice a random slide; `strata_shift` slides x and blends y towards the slice centre by `Banding`. The glitch step and sweep position are plain per-frame expressions.
* **Jitter**: two **Random POPs** and a Math Combine (`jitter`). **Sweep and shade** (`sweep_and_shade`): the Gaussian scan plane, facing and depth shading, Color, PointScale and the Keep flag (image: smoothstep(`Threshold`, 1, `Lum`) x `Imgsamples`) are one Math Combine with a block per step. Trig uses radians.
* **Long lines**: Point Generator seeds -> **Random POPs** (random unit directions, ones for turns / bursts) -> Math Combine (turns and angles) -> two **Transform POPs** that rotate the start and end attribute per point (angle mapped from an attribute) -> pulse / visibility (Lookup in the same random table) -> Copy POP onto the 2-point line template -> Math Combine blends `A -> B` and writes Color.
* **Preview lattice**: Rectangle TOPs (a cross and faint lines) squeezed and repeated by a Transform TOP (Extend = repeat).
* Differences: random numbers come from Random POPs and a noise-texture table instead of the old hash function, so a given seed gives a different (equivalent) arrangement; the blob uses simplex noise instead of value noise. With Jitter 0 and Bandshift 0 the sphere and torus positions are identical to the old shader (difference 0), mean colour and point size agree within about 2 %.
* **Bench** (`tools/bench.py --against` the old GLSL tox, GPU ms, old -> new, 1280x720 / 1920x1080; POP components do not depend on resolution): 10.1 -> 8.3 (-18 %), 10.3 -> 8.9 (-14 %). A second run of the same harness counting only ops that cooked that frame: 9.7 -> 8.8 (-9 %), 9.9 -> 8.3 (-16 %). (The shipped bench adds up `gpuCookTime` of every op every frame, including ops that did not cook that frame, which over-counts static native nodes; the second figure counts only ops that cooked. The GPU was shared with other jobs, so single runs vary by 10-20 %.)
