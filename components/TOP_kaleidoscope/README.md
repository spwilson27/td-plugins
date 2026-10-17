# TOP_kaleidoscope
Symmetry mirror for any TOP (default animated colour noise when `in1` is unconnected). Output `out1`.
- **Controls**: Resolution, Mode (N-fold radial, mirror tiles square / triangle / hex, hyperbolic Poincare disk {P,Q}), Segments (N, or P in hyperbolic mode), Hyperq (Q; forced valid so (P-2)(Q-2)>4), Tiles (modes 1-3), Rotation, Zoom, Srczoom (how much of the source is used), Center, Animate + Speed (spin/drift), Noisespeed.
- Tips: source is sampled with mirrored extension; in hyperbolic mode Center drives a Moebius translation of the tiling.

## Look page
`Look` = `Original` (default, unchanged) or `Mono` (black background, bone-white / grey, rendah style). `Accent` (0-1) adds red accents in Mono (mid-bright band of the image becomes red).


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
- Modulation CHOP drives: Zoom (x1+0.25*beat), Rotation (+45*band1 deg).

## Demo source
With nothing connected to `in1` the component shows a built-in animated test source. It lives in the `demo` Base COMP and is selected by a Switch TOP only while `in1` is unconnected; with an input connected nothing inside `demo` cooks. The component has no Loop page or loop parameters: animation uses absolute time and only exists to make the preview move. Output is warning-free with nothing connected, with `in1` connected, and with all inputs connected.
