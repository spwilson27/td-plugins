# TOP_toon_outline

Depth-free toon/outline stylizer for `in1` (unconnected = animated default shapes). Outputs: `out1` = stylized image, `out2` = edge mask (white edges).

Chain: Sobel (luma + colour-gradient blend) -> edge mask (`edges`) -> Gaussian blur for glow -> `toon` shader (value posterize, edge compositing).

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
