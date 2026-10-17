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
