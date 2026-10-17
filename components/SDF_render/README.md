# SDF_render

Raymarches an SDF wire into an image. A GLSL TOP renders colour, depth, normals and world position in one pass.

## Inputs
- **in1** SDF (DAT) from an SDF_ node (unconnected: a built-in sphere).
- **in2** optional environment TOP, equirectangular (azimuth across, elevation up). Used for the background and reflections. Unconnected: a built-in sky.

## Outputs
- **out1** colour (RGB, alpha = 1, or 0 on miss with Transparent Background).
- **out2** depth: linear eye-space depth in R (distance along the camera forward axis, world units); G = B = R; alpha 1 on hit. Misses write Max Distance with alpha 0.
- **out3** view-space normals, RGB in -1..1 (x right, y up, z towards the camera), alpha 1 on hit.
- **out4** world position (xyz), alpha 1 on hit.
(out2-out4 are Render Select TOPs of the renderer's color buffers 2-4; use 32-bit pipelines yourself if needed - they are 16-bit float.)

## Parameters
- **Resolution**, **Camera** (a Camera COMP: position, rotation and FOV are read live so the image lines up with Render TOP scenes; horizontal and vertical FOV methods are supported, orthographic is not), **Default Camera Orbit** (deg/s, only for the built-in camera used when Camera is empty).
- **Max Distance / Max Steps / Epsilon / Step Scale**: raymarch quality. Step Scale < 1 is safer for twisted, noisy or repeated fields.
- Light page: **Key Azimuth/Elevation**, **Shadow Hardness** (0 = off), **Ambient Occlusion**, **Reflectivity** (mirrors the environment; fresnel boosted).
- Look page: **Background** (environment or solid colour), **Fog** (0 = off, the default) and colour, **Output Gamma** (colour is ACES-tonemapped then gamma encoded; set 1 for linear), **Transparent Background**.

## Notes
- Shading is a simple key / fill / rim + sky model using the SDF's albedo channel; no material system.
- The scene shader only recompiles when the SDF graph structure changes (nodes added, removed, mode menus), never for parameter changes.
- Scenes that carry texture / buffer references (`@tex` records, e.g. `SDF_from_POP`) get them bound as extra inputs of the renderer automatically (up to 6 buffers, 3 2D and 3 3D textures per scene); the environment TOP uses the first 2D slot.
- Cost with `SDF_from_POP` at 1280x720 (default shadows + AO, Apple GPU): about 8 ms for 20 000 points and 11 ms for 100 000 points (plus about 1 ms to rebuild the point grid each frame), so points stay real-time (>= 55 fps) up to roughly 100 000 points with full shading and roughly 500 000 without shadows / AO. A baked mesh costs one trilinear texture sample per distance evaluation. See `SDF_from_POP/README.md`.
- The `@tex` plumbing does not slow existing scenes: sphere + torus + deform at 1280x720 measured +3 % (within the +-10 % noise) against the previous SDF_render.
