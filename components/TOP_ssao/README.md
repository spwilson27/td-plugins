# TOP_ssao
Screen-space ambient occlusion from a depth map and view-space normals, multiplied into the colour. Normal-oriented hemisphere sampling (per-pixel rotated), then a depth-aware separable blur.

## Inputs / outputs
| Connector | Type | Use |
|---|---|---|
| in1 | In TOP | colour image. Unconnected: built-in G-buffer demo scene (Sphere/Torus/Box POPs, preview only) |
| in2 | In TOP | depth, linear eye-space z in **R** (see Depthmode) |
| in3 | In TOP | normals, **view-space** XYZ in RGB, -1..1 (+Z toward camera). `Normalenc = packed` accepts 0..1 encoded normals. Zero-length normals mean "no geometry" |
| out1 | Out TOP | colour * AO |
| out2 | Out TOP | AO mask (1 = open, darker = occluded), after Power and Intensity |

## Encodings
- **Depth** (`Depthmode`): `linear` = distance along the view axis in world units (sky = `<= 0` or `>= Far`). Get it from a Render TOP with a Depth TOP (`op` = Render TOP, Pixel Format `r32float`, Depth Space = Camera Space), or by writing it from a GLSL MAT into an extra colour buffer (Render TOP `Num Color Buffers`; use a Render Select TOP). `nonlinear` = raw Render TOP depth buffer (Depth Space = Input), linearised with `Near`/`Far` (must equal the Camera COMP's).
- **Normals**: view space (camera space), e.g. a GLSL MAT writing `mat3(cameraMatrix) * worldNormal` to a second colour buffer.
- `Fov` = camera vertical FOV in degrees, used to reconstruct view-space positions. `Radius` is in world units (same as depth).

## Parameters
Depthmode, Near, Far, Depthscale, Normalenc, Fov | Radius (sample radius), Samples (4-64), Intensity (0-3), Bias (self-shadow guard), Power (contrast), Blur (px radius, 0 = off) | Mix, Bypass, Resolutionmode, Resolution (standard TOP_ controls).

With in1 connected but no depth/normals, flat defaults are used (no occlusion).
