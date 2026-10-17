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
