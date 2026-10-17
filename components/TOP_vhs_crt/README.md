# TOP_vhs_crt
VHS tape + CRT display emulator. Input `in1` TOP (animated periodic default source when unconnected). Output `out1`.

Two GLSL passes: **tape** (wobble, per-line jitter, interlace comb, 3 tracking-noise bands, bottom head-switching, luma softness, YIQ chroma blur + shift, grain) then **crt** (barrel curvature, rounded screen mask, glow, scanlines with alternating-field interlace, RGB shadow mask, vignette, flicker/hum bar).

| Param | Meaning |
|---|---|
| Mode | VHS / CRT / Both |
| Amount | global strength |
| Wobble, Jitter, Tracking, Headswitch, Noise, Softness | tape artifacts |
| Chromableed, Chromashift | YIQ chroma blur width / horizontal shift (px) |
| Interlace | field-comb + dark alternate fields |
| Curvature, Scanlines, Scanlinecount, Maskstrength, Glow, Vignette, Flicker | CRT |
| Resolution | output size |


## Inputs, outputs and common parameters

**Inputs and outputs**

| Connector | Meaning |
|---|---|
| in1 (TOP) | image to process (unconnected = animated default source) |
| in2 (CHOP) | optional modulation: channels band1-band4, beat (any subset) |
| out1 | result |

**New parameters**
- `Mix` (0-1): dry/wet against the input. `Bypass`: passes in1 straight through (Switch TOP).
- `Resolutionmode`: `input` follows in1 (or the default source, sized by `Resolution`, when unconnected); `custom` uses `Resolution`.
- Modulation CHOP drives: Tracking (+band1), Jitter (+beat).

## Demo source
With nothing connected to `in1` the component shows a built-in animated test source. It lives in the `demo` Base COMP and is selected by a Switch TOP only while `in1` is unconnected; with an input connected nothing inside `demo` cooks. The component has no Loop page or loop parameters: animation uses absolute time and only exists to make the preview move. Output is warning-free with nothing connected, with `in1` connected, and with all inputs connected.


## Implementation
**Native now:** the preview source in the `demo` COMP (a looping 8 s test picture): a Noise TOP walking a circle in noise space for the dark background, Ramp + Threshold + Composite TOPs for the checker and vertical lines, six Circle TOP discs with radial gradients and rings, a rotating Rectangle TOP bar, a sweeping scan line and a Ramp TOP range strip, merged with Composite TOPs. A Switch TOP (`src`) selects it only while `in1` is unconnected.

**GLSL kept:** `tape.glsl` (wobble, jitter, interlace comb, tracking bands, head switching, luma softening, YIQ chroma blur and shift, grain) and `crt.glsl` (curvature, rounded screen, glow, scanlines, shadow mask, vignette, flicker). Why: a complete native version was built and benchmarked and is hopelessly over the 20 % GPU budget (about +1600 % at 720p, +1700 % at 1080p), because every full-screen native pass has a fixed GPU cost and the Blur TOPs for glow and chroma bleed are far more expensive than the 8 to 13 tap loops in the shaders. It is saved as `build_native.py` so it can be rebuilt and studied; it is not the shipped component.

The native version (`build_native.py`), for reference:
- **events** Constant CHOP: frame index at 30 fps, interlace field, time.
- **Line offsets:** every horizontal artifact is one tiny 2 x height map (a value per scanline): slow Noise TOP wobble, random per-line jitter (Noise `randomgpu` + Threshold), odd/even line comb (Ramp + Threshold), three rolling tracking bands (Rectangle TOPs, Composite `maximum`, torn by line noise) and the head-switch band; Composite `add` sums them and a single **Displace TOP** (x only) applies them.
- **Chroma bleed:** a Channel Mix TOP converts to YIQ; a horizontal Blur TOP softens luma; a second, wider horizontal Blur TOP plus a Transform TOP shift blurs and moves the chroma; a Reorder TOP recombines Y with IQ; another Channel Mix converts back to RGB.
- **Grain / speckle / snow:** Noise TOPs (`randomgpu`, one value per pixel, 6 px and 3 px blocks via nearest-filter Resolution TOPs) masked by the band maps with Composite `multiply` / `add` / `over`.
- **CRT:** **Lens Distort TOP** for curvature, Blur TOP + Level TOP + Composite `add` for glow, a cosine Ramp (from a Table DAT) for scanlines with interlace dimming and the hum bar, a 3 x 4 pixel RGB-triad texture tiled 1:1 by a Transform TOP (`extend repeat`, nearest) for the shadow mask, a soft Rectangle TOP for the vignette and a rounded Rectangle TOP for the screen corners; one Composite `multiply` applies scanlines x mask x vignette/corners to the glowing picture.
- Stages sit behind Switch TOPs driven by `Mode`.

Bench of the shipped component (GPU, interleaved medians, noisy because other TouchDesigner instances were running): 720p 1.12 -> 1.04 ms (-6.5 %), 1080p 1.64 -> 1.78 ms (+8.6 %) on the re-run (first run +15.7 % / +22.6 %): same shaders, noise only (native variant: +1585 % / +1727 %)
