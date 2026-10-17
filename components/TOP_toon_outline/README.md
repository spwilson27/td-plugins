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


## v2 conventions (TOP_toon_outline)

**Inputs and outputs**

| Connector | Meaning |
|---|---|
| in1 (TOP) | image to process (unconnected = animated default source) |
| in2 (CHOP) | optional modulation: channels band1-band4, beat, phase (any subset) |
| out1 | result |
| out2 | edges (raw edge map) |

**New parameters**
- `Mix` (0-1): dry/wet against the input (built into the shader). `Bypass`: passes in1 straight through (Switch TOP).
- `Resolutionmode`: `input` follows in1 (or the default source, sized by `Resolution`, when unconnected); `custom` uses `Resolution`.
- `Clock` (Loop page, CHOP): with Timesource = phase, phase is read from this CHOP's `phase` channel instead of `Phase`.
- Modulation CHOP drives: Edgewidth (x1+2*band1), Glowamount (x1+2*beat).
