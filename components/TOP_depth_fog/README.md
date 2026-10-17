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

## Implementation
Network: `in1` / `demo` -> `src`; `in2` / default depth -> `depthsrc`; both feed the **`fog`** GLSL TOP -> `mixer` (Mix) -> `bypass` -> `out1`. The fog falloff curve is a native CHOP network feeding the shader.

- **Fog falloff (native):** the Base COMP `fog_curve` holds a Pattern CHOP (`distance`, 128 samples along the ray from 0 to Far) and one Math / Function / Limit CHOP branch per Fogmode: `exp` (1 - e^(-Density t)), `exp2` (1 - e^(-(Density t)^2)) and `linear` (clamp((t - Start) / (End - Start))). A Switch CHOP (`curve`, index = Fogmode) selects one, and the GLSL TOP reads it as the `uCurve[128]` array uniform. Change the fog shape by editing that network (e.g. add a Filter or Lookup CHOP) without touching any shader.
- **Demo scene (native):** `demo` Base COMP with Sphere / Torus / Box POPs in Geometry COMPs, Phong MATs, a Camera, a Light and a Render TOP; a Ramp TOP makes the dusk sky (Composite TOP, Over); a **Depth TOP** (r32float, Depth Space = Camera Space) gives the linear eye-space depth that `in2` expects. It only cooks while `in1` is unconnected.
- **GLSL kept: `fog` (fog.glsl, about 40 lines).** It decodes the depth (linear or Render-TOP nonlinear with Near/Far), rebuilds each pixel's view ray from Fov / Campitch, reads the falloff curve, adds the ground-fog integral and the horizon glow, and mixes the result with the colour (sky pixels use Skyblend). Reasons: height fog is a per-pixel exponential integral over the ray (no exp or ray maths in Math TOPs, so it needs roughly 10 full-frame passes: ray length, ray elevation, depth decode, two lookups for the exp terms, glow, sky mask, two fog layers and the composites), whereas the fused shader is one pass. A distance-only native prototype (Composite multiply by a ray-length map, Math scale, Lookup into a premultiplied fog-colour Ramp, Composite Over) measured 0.25 / 0.30 ms against the old 0.37 / 0.57 ms at 720p / 1080p, so adding the height fog, glow and sky handling natively would clearly exceed the 20 % budget.

Benchmark (`tools/bench.py --against`, interleaved medians, GPU ms; three runs):

| run | 720p old -> new | 1080p old -> new |
|---|---|---|
| 1 | 0.29 -> 0.28 (-4 %) | 0.54 -> 0.55 (+2 %) |
| 2 | 0.41 -> 0.41 (0 %) | 0.52 -> 0.57 (+8 %) |
| 3 | 0.38 -> 0.38 (0 %) | 0.75 -> 0.86 (+15 %) |

The CHOP network costs no GPU time and only recooks when Fogmode / Density / Start / End / Far change.
