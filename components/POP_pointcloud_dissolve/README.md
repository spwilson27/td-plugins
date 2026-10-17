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
