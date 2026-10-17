# TOP_depth_fog
Distance fog, optional height (ground) fog and horizon glow, computed from a depth map. Works on any G-buffer: a Render TOP, `SDF_render`, or the built-in demo scene.

## Inputs / outputs
| Connector | Type | Use |
|---|---|---|
| in1 | In TOP | colour image (the shaded render). Unconnected: built-in G-buffer demo scene (Sphere/Torus/Box POPs + Render TOP, preview only) |
| in2 | In TOP | depth map, depth in the **R** channel (encoding below). Unconnected with in1 connected: a flat mid-distance depth |
| out1 | Out TOP | fogged image |

## Depth encoding (`Depthmode`)
- **linear** (default): R = linear eye-space z, the distance along the camera's view axis in world units. Anything `<= 0` or `>= Far` is treated as sky (fully fogged, glow added). `Depthscale` multiplies the values (units fix).
  - From a Render TOP: add a **Depth TOP** (`op` = the Render TOP, Pixel Format `r32float`, **Depth Space = Camera Space**) and wire it to in2. Sky comes out as the camera's far plane value, so set `Far` to the Camera COMP's far.
  - Or write it yourself: a GLSL MAT with multiple colour buffers (Render TOP `Num Color Buffers` = 3, `layout(location=1) out vec4`, output `-viewPos.z`) and a Render Select TOP. The demo does this.
- **nonlinear**: R = raw Render TOP depth buffer (0-1, Depth TOP with Depth Space = Input). It is linearised with `Near` / `Far`, which must equal the Camera COMP's near/far. Raw depth `>= 0.99999` is sky.

`Fov`, `Camheight`, `Campitch` describe the camera (vertical FOV in degrees, world height of the camera, pitch down in degrees). They are only needed to reconstruct view rays for height fog and horizon glow.

## Parameters
| Page | Name | Meaning |
|---|---|---|
| Controls | Depthmode, Near, Far, Depthscale | depth decoding (above) |
| | Fogmode | exp / exp2 / linear |
| | Density | exp / exp2 density |
| | Start, End | linear fog range (distance along the ray) |
| | Fogamount | maximum fog opacity on geometry |
| | Fov | camera vertical FOV |
| | Mix, Bypass, Resolutionmode, Resolution | standard TOP_ controls |
| Fog | Fogcolor | fog colour |
| | Heightfog, Heightbase, Heightfalloff, Heightdensity | exponential ground fog below `Heightbase` (world y) |
| | Camheight, Campitch | camera description for height fog / glow |
| Look | Glow, Glowwidth, Glowcolor | warm glow added to the fog colour near the horizon (width = sine of elevation angle) |
| | Skyblend | how strongly sky pixels are replaced by fog colour + glow |

Fog distance is the distance along each view ray (planar depth converted using `Fov`).
