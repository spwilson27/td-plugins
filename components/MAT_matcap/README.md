# MAT_matcap

Matcap switcher. Eight matcaps are generated procedurally on the GPU (clay, chrome, pearl, toon, jade, gold, bone, black-glass); a GLSL MAT looks them up with the view-space normal. A custom matcap can be fed in through `in1`.

* **MAT**: `MAT_matcap/mat` (GLSL MAT). Needs no UVs. Texture sampler `uMatcap` = `matcap_out`.
* **in1** (TOP, optional): custom matcap (a square image of a lit sphere filling the frame). Used when `Matcap = custom` and in1 is connected; otherwise the generated matcap for the menu index (clay) is shown.
* **out1**: preview render (sphere + torus). **out2**: the active matcap texture (512x512). **out3**: contact sheet of all 8 (1024x512).

## Material page
| Par | Meaning |
|---|---|
| Matcap | clay, chrome, pearl, toon, jade, gold, bone, blackglass, custom |
| Tint, Tintamount | multiply tint blended in |
| Brightness | output gain |
| Rotate | rotate lookup (deg) |
| Flipy | flip vertical lookup |
| Spinmatcap | integer revolutions of the lookup per loop (0 = static) |

## Preview / Loop pages
Resolution, Turns, Background, Camdistance, Showsphere/Showtorus; Timesource/Phase/Loopseconds/Loopbeats/Bpm. Looping: rotation values are `2*pi*Spinmatcap*phase` and preview spin is `360*Turns*phase`; matcap itself is static.

## Notes
Only one matcap is cooked at a time (single GLSL TOP indexed by the menu). The lookup uses `mat3(uTDMats[TDCameraIndex()].cam) * worldNormal`, so it follows whichever camera renders the geometry.

## Inputs and outputs (v2)
| Connector | Type | Use |
|---|---|---|
| in1 | TOP, optional | custom matcap image, used when Matcap = custom |
| in2 | CHOP, optional | modulation: channels band1-band4, beat, phase (missing channels read as 0). band1 adds to Brightness, band2 rotates the matcap. Scaled by `Modamount`. |

| Output | Type | Label / content |
|---|---|---|
| out1 | TOP | preview render (sphere + torus knot/torus, tonemapped) |
| out2 | TOP | matcap: the selected matcap image |
| out3 | TOP | matcap atlas: all matcaps in one atlas |

The material itself is `MAT_matcap/mat` (GLSL MAT). Assign it to your Geometry COMP with `op('MAT_matcap/mat')`.

## v2 parameters
- **Material > Modamount**: scales the modulation CHOP.
- **Loop > Clock**: optional CHOP; when set and `Timesource` = `phase`, the loop phase is read from its `phase` channel instead of `Phase`.

## Snippets
`snippets/MAT_matcap.tox` (About > Snippets): 3 examples, each applying `MAT_matcap/mat` to a Geometry COMP with Camera, Light and Render TOP, plus parameter recipes and CHOP modulation.
