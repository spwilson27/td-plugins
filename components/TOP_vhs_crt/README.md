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

**Loop page** (all four): `Timesource` (abstime/phase), `Phase` (0-1), `Loopbeats` (default 8) with `Bpm` (120), or `Loopseconds` (>0 overrides beats). Internally one phase value P=fract(time/loop) (or `Phase`) drives everything.

**Seamless loop:** wobble/bands/hum use integer harmonics of P; per-frame noise is hashed from the frame index inside the loop (frames/loop is even), so it repeats exactly at P 0==1.


## v2 conventions (TOP_vhs_crt)

**Inputs and outputs**

| Connector | Meaning |
|---|---|
| in1 (TOP) | image to process (unconnected = animated default source) |
| in2 (CHOP) | optional modulation: channels band1-band4, beat, phase (any subset) |
| out1 | result |

**New parameters**
- `Mix` (0-1): dry/wet against the input. `Bypass`: passes in1 straight through (Switch TOP).
- `Resolutionmode`: `input` follows in1 (or the default source, sized by `Resolution`, when unconnected); `custom` uses `Resolution`.
- `Clock` (Loop page, CHOP): with Timesource = phase, phase is read from this CHOP's `phase` channel instead of `Phase`.
- Modulation CHOP drives: Tracking (+band1), Jitter (+beat).
