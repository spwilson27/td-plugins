# MAT_decay
Rust / corrosion / decay: clean brushed steel > orange-brown rust > pitted corrosion, driven by one **Decay** value 0..1 (manual, or animated 0>1>0 per preview cycle with Decay Mode = animate).

Material is a GLSL MAT at `<comp>/mat`; it needs **no UVs** (object-space position `oP`, normals required), is self-lit by a procedural studio environment (key/fill/rim lobes, rotate/scale with Envrot/Envint; no Light COMP needed) and outputs HDR-linear colour. To use on your own geometry, point the Geometry COMP Material parameter at `op(".../mat")` (keep the whole COMP: the MAT uniforms are bound by expressions to the COMP parameters via `parent().par`). Preview page: Resolution, Exposure, Bloom, Spinturns, Tilt, Camdist, Backdrop. Speed (animation speed) also on the Preview page. the internal `preview` TOP (not an output) = tonemapped preview of a rotating sphere + torus knot (works with no inputs).

## How it works
- Weathering score = triplanar fbm (object-space projections blended by object normal) + vertical drip-streak noise + low-spot noise + **cavity from curvature** - edge wear. Curvature is the screen-space mean curvature from `dFdx/dFdy` of normal vs position (world units, + convex): concave/flat regions below *Curvbias* collect rust, convex edges above 2x Curvbias wear back to bare metal. Because it is derivative-based it is per-pixel-quad and depends on the mesh normals being smooth.
- Decay sweeps a threshold across the score field (patches grow, merge); a faint orange film precedes real rust. Above ~0.4 voronoi dimples + fine pits appear inside rusted areas (dark, rough, recessed via derivative bump).

| Par | Meaning |
|---|---|
| Decaymode / Decay | manual value or cos animation over time |
| Scale | noise scale | 
| Cavity, Edgewear, Curvbias | curvature-driven rust build-up / edge wear / curvature threshold |
| Pits, Pitsize, Relief | pitting amount / size / bump strength |
| Metalcolor, Rustcolor, Rustdark | palette |


## Inputs and outputs (v2)
| Connector | Type | Use |
|---|---|---|
| in1 | CHOP, optional | modulation: channels band1-band4, beat (missing channels read as 0). band1 adds decay on top of the manual/animated value. Scaled by `Modamount`. |

| Output | Type | Label / content |
|---|---|---|
| out1 | MAT | material (the `mat` GLSL MAT); the preview render is the internal `preview` TOP |

The material itself is `MAT_decay/mat` (GLSL MAT). Assign it to your Geometry COMP with `op('MAT_decay/mat')`.

## v2 parameters
- **Material > Modamount**: scales the modulation CHOP.

## Snippets
`snippets/MAT_decay.tox` (About > Snippets): 3 examples, each applying `MAT_decay/mat` to a Geometry COMP with Camera, Light and Render TOP, plus parameter recipes and CHOP modulation.

## Implementation
The material itself (`mat`) is still a GLSL MAT. This was checked, not assumed:
- The shader relies on: triplanar fbm in object space blended by the object-space normal, voronoi pits, and a curvature mask derived from screen-space derivatives (dFdx/dFdy of normal and position). The curvature cavity/edge masks cannot be made from any texture map.
- A native PBR MAT driven by procedural map TOPs needs either UVs or its "Triplanar" texture sampling mode. Triplanar mode appears to sample in *world* space (probed: the pattern did not follow a sphere rotated 90 degrees, and the mode has no scale parameter), so the texture would swim over moving geometry, and the preview geometry (a Script SOP knot) and many user meshes carry no UVs. The material is meant to be dropped on arbitrary geometry and to move with it, so object space is required.
- Native replacements would also change the look: the Noise TOP is 2D, so a 3D flowing network would be baked into a few tiling maps.

What is native: the whole preview chain except the tonemap pass. The `bright` bloom pass is a Level TOP (1..2 mapped to 0..1, negatives clamped = max(colour-1, 0)), the blooms are Blur TOPs, the geometry is Sphere/Script SOPs + Geometry COMPs + Render TOP, and the modulation comes in through a Merge CHOP. `tonemap` stays a small GLSL TOP: ACES filmic curve, gamma, vignette background and three-way composite in one pass (preview chrome only; the native equivalent is roughly ten TOPs for no gain).

Bench: not applicable to the material (the shader and its inputs are unchanged, only the preview bright pass changed from GLSL to a Level TOP, and the preview is not cooked unless it is viewed).
