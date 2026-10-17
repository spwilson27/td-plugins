# MAT_triplanar

Triplanar procedural material for meshes without UVs. Patterns are evaluated on the three axis-aligned planes and blended by `pow(abs(normal), Sharpness)`. Lit by a built-in studio rig (key/fill/rim + procedural env reflection) with roughness/metallic and derivative bump.

* **MAT**: `MAT_triplanar/mat` (GLSL MAT). No UVs, no inputs required.
* **in1** (TOP, optional): texture projected triplanar when `Pattern = texture`. Unconnected -> internal noise TOP.
* **out1**: preview render (sphere + torus).

## Material page
| Par | Meaning |
|---|---|
| Pattern | noise (fbm), voronoi, stripes, grid, checker, texture (in1) |
| Space | `object` (sticks to the mesh, uses `P`/`N`) or `world` (static in the scene, uses world pos/normal) |
| Scale | pattern cells per unit |
| Sharpness | triplanar blend exponent (higher = harder seams) |
| Color1 / Color2 | two pattern colours |
| Roughness / Metallic | shading |
| Contrast | pattern contrast around 0.5 |
| Bump | derivative bump strength from the pattern |
| Linewidth | stripe/grid line width |
| Octaves | fbm octaves (noise) |
| Texscale | texture tiling per plane unit |
| Animate | noise travel radius / voronoi jitter motion (0 = static) |
| Scroll | integer pattern scroll cycles per loop |

## Preview / Loop pages
Preview: Resolution, Turns, Background, Camdistance, Showsphere, Showtorus. Loop: Timesource (abstime/phase), Phase, Loopseconds, Loopbeats, Bpm.
Loop seamlessness: noise samples a circle of radius `Animate` around its base point (`cos/sin(2*pi*phase)`), voronoi feature points orbit with `sin(2*pi*(phase+hash))`, scroll moves `2*Scroll*phase` (integer multiples of the period-2 patterns), spin is `360*Turns*phase`.

## Uniforms
`uA` scale/sharpness/pattern/space, `uB` rough/metal/contrast/bump, `uC` animate/scroll/phase/linewidth, `uD` octaves/texscale, `uCol1`, `uCol2`, sampler `uTex`.

## Inputs and outputs (v2)
| Connector | Type | Use |
|---|---|---|
| in1 | TOP, optional | texture for Pattern = texture |
| in2 | CHOP, optional | modulation: channels band1-band4, beat, phase (missing channels read as 0). band1 adds to Contrast. Scaled by `Modamount`. |

| Output | Type | Label / content |
|---|---|---|
| out1 | TOP | preview render (sphere + torus knot/torus, tonemapped) |

The material itself is `MAT_triplanar/mat` (GLSL MAT). Assign it to your Geometry COMP with `op('MAT_triplanar/mat')`.

## v2 parameters
- **Material > Modamount**: scales the modulation CHOP.
- **Loop > Clock**: optional CHOP; when set and `Timesource` = `phase`, the loop phase is read from its `phase` channel instead of `Phase`.

## Snippets
`snippets/MAT_triplanar.tox` (About > Snippets): 3 examples, each applying `MAT_triplanar/mat` to a Geometry COMP with Camera, Light and Render TOP, plus parameter recipes and CHOP modulation.
