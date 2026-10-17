# TOP_kaleidoscope
Symmetry mirror for any TOP (default animated colour noise when `in1` is unconnected). Output `out1`.
- **Controls**: Resolution, Mode (N-fold radial, mirror tiles square / triangle / hex, hyperbolic Poincare disk {P,Q}), Segments (N, or P in hyperbolic mode), Hyperq (Q; forced valid so (P-2)(Q-2)>4), Tiles (modes 1-3), Rotation, Zoom, Srczoom (how much of the source is used), Center, Animate + Speed (spin/drift), Noisespeed.
- Tips: source is sampled with mirrored extension; in hyperbolic mode Center drives a Moebius translation of the tiling.

## Loop & Look (batch-2 retrofit)

### Loop page
| Param | Meaning |
|---|---|
| Timesource | `abstime` (free-running, original behaviour) or `phase` (motion is a function of `Phase`) |
| Phase | 0-1 loop phase, drive externally (LFO / timeline / beat clock) in `phase` mode |
| Loopseconds | loop length used when Timesource=abstime-derived clocks are needed (default 8 s) |
| Loopbeats / Bpm | if Loopbeats > 0 the loop length is Loopbeats*60/Bpm seconds instead of Loopseconds |

**How the loop works:** Phase mode: tile drift / rotation / hyperbolic drift use integer harmonics (N-fold mode sways +-0.6 rad instead of rotating continuously), the default source is 4D noise on a circle. Phase 0 vs 0.9999: ~0.001.

### Look page
`Look` = `Original` (default, unchanged) or `Mono` (black background, bone-white / grey, rendah style). `Accent` (0-1) adds red accents in Mono (mid-bright band of the image becomes red).


## v2 conventions (TOP_kaleidoscope)

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
- Modulation CHOP drives: Zoom (x1+0.25*beat), Rotation (+45*band1 deg).
