# TOP_halftone

Print/retro stylizer for `in1` (unconnected = animated default shapes). Output `out1`. One GLSL pass plus an internally generated glyph atlas.

**Mode** menu:
- **Halftone** - `Halftonetype` CMYK (C/M/Y/K screens at 15/75/0/45 deg plus `Angle`, subtractive on `Paper`) or Mono (single dot screen, `Ink` on `Paper`).
- **Dither** - `Dithertype`: Bayer 2x2 / 4x4 / 8x8, Blue noise (interleaved-gradient-noise approximation), Pseudo error diffusion (R2 low-discrepancy threshold - an ordered approximation, not true serial diffusion). `Levels` per channel; `Dithermono` maps luma between Ink (dark) and Paper (light). `Cellsize` = dither pixel size.
- **ASCII** - 10-glyph ramp (`Ramp` string, dark -> bright, exactly 10 chars; padded with spaces) rendered by ten 32x32 Text TOPs (Menlo) into a 320x32 atlas (`atlas` GLSL TOP). Light glyphs (`Paper`, or source colour with `Keepcolor`) on `Ink` background; `Cellsize` is the glyph cell size in px.

Other pars: `Cellsize` (px), `Angle` (deg), `Softness` (dot edge), `Invert`, `Mix` (blend with original), `Resolution` (Render page).
Limitations: ASCII ramp is fixed at 10 glyphs; font must exist on the machine (falls back to TD default).

## Look page
`Look` = `Original` / `Mono` switches only the **internal default test source** (used when `in1` is unconnected) to a black / bone-white / grey variant; `Accent` (0-1) tints one test object red. A connected `in1` is not recoloured (effects with intrinsic colour, e.g. RGB-split or CMYK halftone, keep it).


## Inputs, outputs and common parameters

**Inputs and outputs**

| Connector | Meaning |
|---|---|
| in1 (TOP) | image to process (unconnected = animated default source) |
| in2 (CHOP) | optional modulation: channels band1-band4, beat (any subset) |
| out1 | result |

**New parameters**
- `Mix` (0-1): dry/wet against the input (built into the shader). `Bypass`: passes in1 straight through (Switch TOP).
- `Resolutionmode`: `input` follows in1 (or the default source, sized by `Resolution`, when unconnected); `custom` uses `Resolution`.
- Modulation CHOP drives: Cellsize (x1+0.8*band1), Angle (+20*beat deg).

## Demo source
With nothing connected to `in1` the component shows a built-in animated test source. It lives in the `demo` Base COMP and is selected by a Switch TOP only while `in1` is unconnected; with an input connected nothing inside `demo` cooks. The component has no Loop page or loop parameters: animation uses absolute time and only exists to make the preview move. Output is warning-free with nothing connected, with `in1` connected, and with all inputs connected.

## Implementation

### Preview source (demo)
The `demo` COMP used when `in1` is unconnected is built only from native operators, no GLSL: a Constant TOP ground, a Rectangle TOP bar and five Circle TOP discs with bright cores, stacked by a Composite TOP; Look = Mono and Accent switch the palette through parameter expressions. It sits behind the Switch, so it does not cook when an input is connected.

