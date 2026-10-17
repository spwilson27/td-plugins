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
