# SDF_to_MAT

A GLSL MAT that raymarches an SDF wire inside proxy geometry and writes depth (lossy: simple lighting, no TD light/material features).

Wire format: see the SDF section of `CONVENTIONS.md`. Parameters are animatable (expressions, CHOPs) without recompiling shaders.

## Inputs
- **in1** SDF (DAT) (unconnected: a built-in sphere).

## Outputs
- **out1** material (MAT).

## Parameters
- **Apply To**: drag Geometry COMPs / Render TOPs here (like the MAT_ components).
- **Bounds Center / Size**: the proxy box in the geometry's object space. The Geometry should be a box covering it (e.g. Box SOP with the same Size). The SDF is marched in object space, so the Geometry COMP's transform moves it. Rays start on the Bounds box, so cameras inside the box also work.
- **Max Steps / Epsilon / Step Scale**, **Key Azimuth/Elevation**, **Shadow Hardness**, **Ambient Occlusion**, **Output Gamma**.
- Depth is written (`gl_FragDepth`), so SDFs intersect ordinary polygons correctly. Lighting is built in; scene lights are ignored.

