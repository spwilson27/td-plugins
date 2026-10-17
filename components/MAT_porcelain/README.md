# MAT_porcelain

Porcelain / bone / marble / nero-marble material (GLSL MAT) with fake subsurface, domain-warped 3D veins and hairline voronoi cracks, plus a rotating sphere + torus-knot preview.

- **Material**: `MAT_porcelain/mat` (GLSL MAT). Assign to any Geometry COMP. Needs **no UVs**: all patterns use object-space position (`oP`), so the pattern sticks to the object. Normals are required on the geometry. Self-lit by a procedural studio environment (key/fill/rim lobes), so it needs no Light COMP; it is HDR-linear (tonemap downstream).
- **Output**: `out1` TOP = preview render (tonemapped, bloom). Works with no inputs.

## Parameters (custom page **Material**; the MAT reads them via `parent().par`)
| Par | Meaning |
|---|---|
| Style | Porcelain / Bone / Marble / Nero Marble (sets base colour, vein colour, roughness, glaze, SSS tint) |
| Tint, Veintint | RGB multipliers on base / vein colour |
| Gloss | 0 matte .. 1 glazed (clear-coat strength + roughness) |
| Sss | wrap-lighting width + warm terminator band (fake subsurface); also thin-edge/back translucency |
| Thickness | variation of translucency with a noise "thickness" |
| Veinamount / Veinscale / Veinwarp | marble vein intensity, frequency, domain-warp strength |
| Crackamount | fraction of voronoi edges that appear as cracks (0 = none) |
| Crackscale / Crackwidth | cell size of the crack network / line width |
| Envrot / Envint | rotate / scale the procedural studio env |

**Preview** page: Resolution, Exposure, Bloom, Spinturns, Tilt, Camdist, Backdrop. **Loop** page: Timesource (abstime/phase), Phase, Loopseconds, Loopbeats, Bpm, Speed.

## Using the MAT elsewhere
Copy `mat` (it has `mat_vertex`/`mat_pixel` DATs) and the parameter-bound uniforms (`vec` page: `uEnv, uP0, uP1, uP2, uTint, uVeinC`, expressions refer to `parent().par.*`) - easiest is to keep the whole COMP and reference `op('MAT_porcelain/mat')` from your Geometry COMP's Material parameter.

## Loop
The only time-dependent things are the preview spin (rotation = 360 * Spinturns * phase) so it loops seamlessly at phase 0 == 1 (with `Spinturns` integer). The material itself is static.

## Inputs and outputs (v2)
| Connector | Type | Use |
|---|---|---|
| in1 | CHOP, optional | modulation: channels band1-band4, beat, phase (missing channels read as 0). band1 adds to Veinamount, beat adds to Crackamount. Scaled by `Modamount`. |

| Output | Type | Label / content |
|---|---|---|
| out1 | TOP | preview render (sphere + torus knot/torus, tonemapped) |

The material itself is `MAT_porcelain/mat` (GLSL MAT). Assign it to your Geometry COMP with `op('MAT_porcelain/mat')`.

## v2 parameters
- **Material > Modamount**: scales the modulation CHOP.
- **Loop > Clock**: optional CHOP; when set and `Timesource` = `phase`, the loop phase is read from its `phase` channel instead of `Phase`.

## Snippets
`snippets/MAT_porcelain.tox` (About > Snippets): 3 examples, each applying `MAT_porcelain/mat` to a Geometry COMP with Camera, Light and Render TOP, plus parameter recipes and CHOP modulation.
