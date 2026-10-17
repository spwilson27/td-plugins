# MAT_screen_stylize

Per-object screen-space stylization material: the object is shaded (key light + rim + spec -> luminance), then quantized in screen space with `gl_FragCoord`: Bayer ordered dither, rotated halftone dots, or ASCII glyphs. Output is a two-tone mix of `Color1` / `Color2`.

* **MAT**: `MAT_screen_stylize/mat` (GLSL MAT). No UVs needed. Cell size is in render-target pixels (so it is resolution dependent by design).
* **out1**: the material (Out MAT); internal `preview` TOP (not an output) = preview render (sphere + torus). **out2**: the generated glyph atlas TOP.
* Halftone/ASCII estimate luminance at the *cell centre* via `dFdx/dFdy`, so dots/glyphs are clean per cell.

## Material page
| Par | Meaning |
|---|---|
| Mode | `bayer`, `halftone`, `ascii` |
| Cellsize | cell height in px (ASCII cells are Cellsize/2 wide) |
| Levels | Bayer output levels (2 = pure two-tone) |
| Angle | halftone screen angle |
| Glyphs | up to 16 characters dark -> light for ASCII (monospace Menlo bold) |
| Color1 / Color2 | dark / light tones |
| Contrast, Invert | luminance contrast around 0.5, invert |
| Ambient, Rim | ambient floor and rim light |
| Lightdir | key light direction (world) |
| Spinlight | integer light revolutions around Y per preview cycle |

Glyph atlas: a Text TOP (1024x128, 64px advance per slot) is rendered from `Glyphs`; sampler `uAtlas`.

## Preview page
Time-based motion (preview spin, and the material's own animation where it has one) runs from absolute time; there is no Loop page.

## Uniforms
`uA` mode/cell/contrast/invert, `uB` angle/levels/glyphcount/ambient, `uC` lightdir+rim, `uCol1`, `uCol2`, `uAtlas`.

## Inputs and outputs (v2)
| Connector | Type | Use |
|---|---|---|
| in1 | CHOP, optional | modulation: channels band1-band4, beat (missing channels read as 0). band2 shrinks Cellsize, band1 adds Contrast. Scaled by `Modamount`. |

| Output | Type | Label / content |
|---|---|---|
| out1 | MAT | material (the `mat` GLSL MAT); the preview render is the internal `preview` TOP |
| out2 | TOP | glyph atlas: ASCII glyph atlas |

The material itself is `MAT_screen_stylize/mat` (GLSL MAT). Assign it to your Geometry COMP with `op('MAT_screen_stylize/mat')`.

## v2 parameters
- **Material > Modamount**: scales the modulation CHOP.

## Snippets
`snippets/MAT_screen_stylize.tox` (About > Snippets): 3 examples, each applying `MAT_screen_stylize/mat` to a Geometry COMP with Camera, Light and Render TOP, plus parameter recipes and CHOP modulation.
