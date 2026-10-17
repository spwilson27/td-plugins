# TOP_halftone

Print/retro stylizer for `in1` (unconnected = animated default shapes). Output `out1`. One GLSL pass plus an internally generated glyph atlas.

**Mode** menu:
- **Halftone** - `Halftonetype` CMYK (C/M/Y/K screens at 15/75/0/45 deg plus `Angle`, subtractive on `Paper`) or Mono (single dot screen, `Ink` on `Paper`).
- **Dither** - `Dithertype`: Bayer 2x2 / 4x4 / 8x8, Blue noise (interleaved-gradient-noise approximation), Pseudo error diffusion (R2 low-discrepancy threshold - an ordered approximation, not true serial diffusion). `Levels` per channel; `Dithermono` maps luma between Ink (dark) and Paper (light). `Cellsize` = dither pixel size.
- **ASCII** - 10-glyph ramp (`Ramp` string, dark -> bright, exactly 10 chars; padded with spaces) rendered by ten 32x32 Text TOPs (Menlo) into a 320x32 atlas (`atlas` GLSL TOP). Light glyphs (`Paper`, or source colour with `Keepcolor`) on `Ink` background; `Cellsize` is the glyph cell size in px.

Other pars: `Cellsize` (px), `Angle` (deg), `Softness` (dot edge), `Invert`, `Mix` (blend with original), `Resolution` (Render page).
Limitations: ASCII ramp is fixed at 10 glyphs; font must exist on the machine (falls back to TD default).

## Loop & Look (batch-2 retrofit)

### Loop page
| Param | Meaning |
|---|---|
| Timesource | `abstime` (free-running, original behaviour) or `phase` (motion is a function of `Phase`) |
| Phase | 0-1 loop phase, drive externally (LFO / timeline / beat clock) in `phase` mode |
| Loopseconds | loop length used when Timesource=abstime-derived clocks are needed (default 8 s) |
| Loopbeats / Bpm | if Loopbeats > 0 the loop length is Loopbeats*60/Bpm seconds instead of Loopseconds |

**How the loop works:** Stateless; only the default test source animates, and it is periodic in phase mode.

### Look page
`Look` = `Original` / `Mono` switches only the **internal default test source** (used when `in1` is unconnected) to a black / bone-white / grey variant; `Accent` (0-1) tints one test object red. A connected `in1` is not recoloured (effects with intrinsic colour, e.g. RGB-split or CMYK halftone, keep it).


## v2 conventions (TOP_halftone)

**Inputs and outputs**

| Connector | Meaning |
|---|---|
| in1 (TOP) | image to process (unconnected = animated default source) |
| in2 (CHOP) | optional modulation: channels band1-band4, beat, phase (any subset) |
| out1 | result |

**New parameters**
- `Mix` (0-1): dry/wet against the input (built into the shader). `Bypass`: passes in1 straight through (Switch TOP).
- `Resolutionmode`: `input` follows in1 (or the default source, sized by `Resolution`, when unconnected); `custom` uses `Resolution`.
- `Clock` (Loop page, CHOP): with Timesource = phase, phase is read from this CHOP's `phase` channel instead of `Phase`.
- Modulation CHOP drives: Cellsize (x1+0.8*band1), Angle (+20*beat deg).
