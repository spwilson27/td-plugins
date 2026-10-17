# TOP_filmic_look

Cinematic finishing pass for `in1` (unconnected = animated default shapes with HDR highlights). Output `out1`.

Chain: exposure -> chromatic aberration -> bloom (bright-pass with soft knee, 5 Gaussian blurs of increasing size summed) + anamorphic glare (horizontal exponentially-spaced streak of the bright-pass, tinted) -> tonemap -> gamma -> vignette -> film grain.

| Par | Meaning |
|---|---|
| Exposure | stops (2^x) applied before tonemap |
| Tonemap | None / ACES (Narkowicz fit) / Filmic (Hable) / Reinhard |
| Bloomamount, Bloomthreshold, Bloomknee, Bloomsize | bloom strength, bright-pass threshold and soft knee, scale of the blur radii |
| Glareamount, Glarelength, Glaretint | horizontal streak strength, length (uv), colour |
| Chromatic | radial RGB fringing |
| Vignette, Vignettesoft | darkening strength / softness |
| Grain, Grainsize | film grain amount (animated at 24 Hz) and grain size in px |
| Gamma | output gamma (1 = off) |
| Resolution (Render) | output size |

Pipeline is rgba16float so HDR (>1) input drives bloom/glare. Blur sizes are 5/10/20/40/80 px (pre-shrunk 1/2/4/8/16) times Bloomsize.

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
- `Mix` (0-1): dry/wet against the input. `Bypass`: passes in1 straight through (Switch TOP).
- `Resolutionmode`: `input` follows in1 (or the default source, sized by `Resolution`, when unconnected); `custom` uses `Resolution`.
- Modulation CHOP drives: Bloomamount (x1+2*band1), Exposure (+0.8*beat).

## Demo source
With nothing connected to `in1` the component shows a built-in animated test source. It lives in the `demo` Base COMP and is selected by a Switch TOP only while `in1` is unconnected; with an input connected nothing inside `demo` cooks. The component has no Loop page or loop parameters: animation uses absolute time and only exists to make the preview move. Output is warning-free with nothing connected, with `in1` connected, and with all inputs connected.
