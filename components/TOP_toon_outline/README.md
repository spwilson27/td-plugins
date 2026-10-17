# TOP_toon_outline

Depth-free toon/outline stylizer for `in1` (unconnected = animated default shapes). Outputs: `out1` = stylized image, `out2` = edge mask (white edges).

Chain: Sobel edge mask (`edges`) -> posterize (Lookup TOP + Composite multiply) -> ink (Composite over) or neon (Blur TOP glow + small GLSL sum), see Implementation.

| Par | Meaning |
|---|---|
| Style | Ink line (edge colour over posterized image) or Neon glow (dimmed image + additive glow and hot core) |
| Levels / Posterizesoft | number of brightness bands (hue/sat kept) and band edge softness |
| Edgecolor | line / glow colour |
| Edgewidth | Sobel tap distance in px |
| Threshold / Edgesoft | edge strength cutoff and its smoothstep width |
| Colorweight | 0 = luma-only edges, 1 = colour-gradient edges |
| Glowsize / Glowamount | neon glow blur size (px) and gain |
| Dim | neon: brightness of the underlying image |
| Mix | blend with the original |
| Resolution (Render) | output size |

## Look page
`Look` = `Original` / `Mono` switches only the **internal default test source** (used when `in1` is unconnected) to a black / bone-white / grey variant; `Accent` (0-1) tints one test object red. A connected `in1` is not recoloured (effects with intrinsic colour, e.g. RGB-split or CMYK halftone, keep it).


## Inputs, outputs and common parameters

**Inputs and outputs**

| Connector | Meaning |
|---|---|
| in1 (TOP) | image to process (unconnected = animated default source) |
| in2 (CHOP) | optional modulation: channels band1-band4, beat (any subset) |
| out1 | result |
| out2 | edges (raw edge map) |

**New parameters**
- `Mix` (0-1): dry/wet against the input (built into the shader). `Bypass`: passes in1 straight through (Switch TOP).
- `Resolutionmode`: `input` follows in1 (or the default source, sized by `Resolution`, when unconnected); `custom` uses `Resolution`.
- Modulation CHOP drives: Edgewidth (x1+2*band1), Glowamount (x1+2*beat).

## Demo source
With nothing connected to `in1` the component shows a built-in animated test source. It lives in the `demo` Base COMP and is selected by a Switch TOP only while `in1` is unconnected; with an input connected nothing inside `demo` cooks. The component has no Loop page or loop parameters: animation uses absolute time and only exists to make the preview move. Output is warning-free with nothing connected, with `in1` connected, and with all inputs connected.

## Implementation
- **Edges (GLSL, kept):** one small pass `edges` (`sobel.glsl`): Sobel on luma and on colour, blended by Colorweight, then the smoothstep threshold. A native version (Convolve TOPs with Sobel kernels on a copy resized to 1/Edgewidth, Math TOP vector lengths, Reorder, Cross, threshold Level + Lookup, border mask) matched the old edge map within a pixel, but needed about 15 extra small passes and measured 2-3x slower on the GPU (5.5 vs 2.4 ms at 720p), so the edge detector stays one shader.
- **Posterize (native):** a Pattern CHOP + Expression CHOP builds a 4096-sample curve (posterized value / value, with the Levels and Posterizesoft parameters) which a CHOP to TOP turns into a 4096x1 image. A Lookup TOP reads max(r,g,b) of the picture through it and a Composite TOP (multiply) applies the result, so hue and saturation are kept and the bands have the soft edge. Measured identical to the old shader (differences below 0.001).
- **Ink (native):** a Channel Mix makes a premultiplied edge-colour layer from `edges` (colour times edge, alpha = edge), a Composite TOP (Over) lays it on the posterized picture.
- **Neon:** Blur TOP (gaussian, Glowsize) of `edges`, then one small GLSL pass (`neon.glsl`) sums dimmed toon image + coloured edge/glow + hot white core. The same sum made from Level, Reorder, Channel Mix and Composite TOPs measured 1.5-2x slower than the old shader in this style, so it stays one tiny shader. The Switch TOP `style` only cooks the selected branch, so the glow blur (which the old shader always paid for) costs nothing in ink style.
- **Mix:** the shared Cross TOP (dry = input). **Demo source:** Ramp (rainbow, checker bars), Noise, Rectangle/Transform (bar) and Circle TOPs.
- **Bench (old vs new, median GPU ms, default ink style):** 1280x720 1.31 -> 1.14 (-13 %), 1920x1080 2.11 -> 1.86 (-12 %); other runs of the same comparison gave -17 % / -17 %. Neon style, measured separately with interleaved old/new frames: -1 % to +26 % at 1280x720 (noise ~10 %).
