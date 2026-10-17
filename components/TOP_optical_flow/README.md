# TOP_optical_flow

Optical flow on `in1` (unconnected = animated default shapes with motion), plus effects driven by it.

Outputs: `out1` = effect image; `out2` = flow field (rgba32float, Flowscale x Resolution): **R,G = per-frame displacement in uv units** (content moved by (R,G) since the previous frame, +x right / +y up), B = speed in pixels per frame at flow resolution.

Method: iterative, warped Lucas-Kanade in one GLSL TOP at reduced resolution (7x7 weighted window, Tikhonov-regularised, 1-3 refinement iterations, per-iteration clamp 12 px), then temporal smoothing through a Feedback TOP. Previous frame = Feedback TOP of the downscaled current frame.

| Par | Meaning |
|---|---|
| Mode | Smear / advect feedback (previous output advected along flow and mixed with source), Warp (source displaced by flow), Flow visualization (HSV: hue = direction, brightness = speed) |
| Gain | strength of the effect / viz brightness |
| Persistence | smear history retention |
| Smoothing | temporal smoothing of the flow (0 = raw) |
| Iterations, Regularization | LK refinement passes; larger = fewer noisy vectors in flat areas |
| Active, Reset | freeze / clear feedback buffers |
| Resolution, Flowscale (Render) | output size; flow computation scale (0.25 default; use larger for subtle motion, smaller for fast motion) |

Limitations: LK handles roughly <= 8 px/frame at flow resolution; fast motion needs a lower Flowscale. Needs to cook every frame (feedback).

## Look page
`Look` = `Original` / `Mono` switches only the **internal default test source** (used when `in1` is unconnected) to a black / bone-white / grey variant; `Accent` (0-1) tints one test object red. A connected `in1` is not recoloured (effects with intrinsic colour, e.g. RGB-split or CMYK halftone, keep it).


## Inputs, outputs and common parameters

**Inputs and outputs**

| Connector | Meaning |
|---|---|
| in1 (TOP) | image to process (unconnected = animated default source) |
| in2 (CHOP) | optional modulation: channels band1-band4, beat (any subset) |
| out1 | result |
| out2 | flow (optical-flow vectors) |

**New parameters**
- `Mix` (0-1): dry/wet against the input. `Bypass`: passes in1 straight through (Switch TOP).
- `Resolutionmode`: `input` follows in1 (or the default source, sized by `Resolution`, when unconnected); `custom` uses `Resolution`.
- Modulation CHOP drives: Gain (x1+2*band1).

## Demo source
With nothing connected to `in1` the component shows a built-in animated test source. It lives in the `demo` Base COMP and is selected by a Switch TOP only while `in1` is unconnected; with an input connected nothing inside `demo` cooks. The component has no Loop page or loop parameters: animation uses absolute time and only exists to make the preview move. Output is warning-free with nothing connected, with `in1` connected, and with all inputs connected.
