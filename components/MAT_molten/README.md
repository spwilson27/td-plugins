# MAT_molten
Lava / molten emissive cracks glowing through a dark cooling crust. Cracks = edges (F2-F1) of a 3D voronoi whose feature points orbit, domain-warped by flowing noise; temperature ramp black > deep red > orange > yellow > white; crust is basalt with ash patches, derivative-bump relief and AO in the cracks.

Material is a GLSL MAT at `<comp>/mat`; it needs **no UVs** (object-space position `oP`, normals required), is self-lit by a procedural studio environment (key/fill/rim lobes, rotate/scale with Envrot/Envint; no Light COMP needed) and outputs HDR-linear colour. To use on your own geometry, point the Geometry COMP Material parameter at `op(".../mat")` (keep the whole COMP: the MAT uniforms are bound by expressions to the COMP parameters via `parent().par`). Preview page: Resolution, Exposure, Bloom, Spinturns, Tilt, Camdist, Backdrop. Speed (animation speed) also on the Preview page. the internal `preview` TOP (not an output) = tonemapped preview of a rotating sphere + torus knot (works with no inputs).

| Par | Meaning |
|---|---|
| Heat | HDR emission gain (bloom in preview) |
| Cooling | 0 hot .. 1 cold: narrows cracks, lowers temperature, adds ash crust |
| Crackwidth, Crackscale | crack width / network cell size |
| Flow | domain-warp flow strength |
| Streaks | flowing hot streaks inside cracks |
| Pulse | slow heat pulsing (2 per preview cycle) |
| Crustbump | crust relief |
| Crustcolor, Glowtint | crust albedo / emission tint |

## Animation
Time-based motion (preview spin, and the material's own animation where it has one) runs from absolute time; there is no Loop page.

## Inputs and outputs (v2)
| Connector | Type | Use |
|---|---|---|
| in1 | CHOP, optional | modulation: channels band1-band4, beat (missing channels read as 0). Heat is multiplied by 1 + band1*1.5 + beat. Scaled by `Modamount`. |

| Output | Type | Label / content |
|---|---|---|
| out1 | MAT | material (the `mat` GLSL MAT); the preview render is the internal `preview` TOP |

The material itself is `MAT_molten/mat` (GLSL MAT). Assign it to your Geometry COMP with `op('MAT_molten/mat')`.

## v2 parameters
- **Material > Modamount**: scales the modulation CHOP.

## Snippets
`snippets/MAT_molten.tox` (About > Snippets): 3 examples, each applying `MAT_molten/mat` to a Geometry COMP with Camera, Light and Render TOP, plus parameter recipes and CHOP modulation.
