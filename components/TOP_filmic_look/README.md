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

Pipeline is rgba16float so HDR (>1) input drives bloom/glare. The five bloom Gaussians have sigma of about 1.2/4.4/17/68/171 px (x Bloomsize).

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

## Implementation
Everything is built from built-in TOPs; no GLSL remains.
- **Chromatic aberration:** two Transform TOPs scale a copy slightly up (red) and down (blue); a Reorder TOP takes red from the first, green from the untouched picture, blue from the second.
- **Bloom:** bright-pass with soft knee (a Level TOP subtracts the threshold, a second Level TOP draws the quadratic knee, a Composite TOP takes the maximum; HDR kept) -> five Gaussian Blur TOPs. The wider blurs run on half, quarter, eighth and sixteenth-size copies (Level TOPs with a smaller custom resolution) so they stay cheap; a Channel Mix after each blur sets its weight (wider blurs weigh more) and the Bloomamount gain.
- **Glare:** the bright-pass is smeared sideways by horizontal-only Blur TOPs at three widths (full size, quarter size, eighth size, the mix approximates the old exponentially spaced streak); Channel Mix TOPs apply tint, amount and the weight of each.
- **Combine and exposure:** one Composite TOP (Add) sums the picture and all bloom/glare layers; Level TOP applies Exposure (2^stops).
- **Tonemap:** a Lookup TOP reads a baked curve (Ramp TOP built from a Table DAT: ACES, Filmic, Reinhard; 0-8 HDR range, so the exposed picture is scaled by 1/8 first); a Switch TOP picks None / ACES / Filmic / Reinhard.
- **Gamma / vignette / grain:** Level TOP (gamma); an elliptical circular Ramp TOP through a Level TOP (linear fall-off, where the old shader used smoothstep) multiplied in a Composite TOP; a random Noise TOP at 1/Grainsize resolution (a new pattern 24 times a second) scaled by a Level TOP, faded in highlights with a Channel Mix and added.
- **Demo source:** Ramp (rainbow gradient, checker bars), Noise, Rectangle/Transform (bar) and Circle TOPs.
- **Approximations vs the old shader:** the bright-pass works per channel (old: per-pixel scale keeping hue); chromatic aberration is a pure per-channel zoom (old: offset growing with distance squared); vignette falls off linearly; the glare is a 3-Gaussian fit of the old kernel and is smeared slightly vertically on its smaller copies. Tonemap, gamma, grain strength and bloom amount/width match the old values within a few percent when measured.
- **Bench (old GLSL vs native, median GPU ms, two runs):** 1280x720 13.8 -> 9.1 (-34 %) and 11.9 -> 5.9 (-51 %); 1920x1080 32.5 -> 15.9 (-51 %) and 31.7 -> 6.4 (-80 %). The old version spent most of its time in the pre-shrunk 80 px Blur (shrink by 16 is expensive); the half-size pyramid is much cheaper.
