# TOP_optical_flow

Optical flow on `in1` (unconnected = animated default shapes with motion), plus effects driven by it.

Outputs: `out1` = effect image; `out2` = flow field (rgba32float, Flowscale x Resolution): **R,G = per-frame displacement in uv units** (content moved by (R,G) since the previous frame, +x right / +y up), B = speed in pixels per frame at flow resolution.

Method: iterative, warped Lucas-Kanade in one GLSL TOP at reduced resolution (7x7 weighted window, Tikhonov-regularised, 1-3 refinement iterations, per-iteration clamp 12 px), with temporal smoothing against the previous flow (Feedback TOP). Previous frame = Feedback TOP of the downscaled current frame. The three effects are built from native TOPs (see Implementation).

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

## Implementation
Built from built-in nodes; follow the wires left to right.
- **Flow estimation (GLSL, `flow`)**: `src` -> `cur` (Null at Flowscale resolution, mipmapped) and `prev` (Feedback TOP of `cur`) feed one GLSL TOP, the Lucas-Kanade solver, which also mixes in last frame's flow from `flowfb` (Feedback TOP of `flow_final`). It stays GLSL because it is a per-pixel least-squares solve (7x7 window, 2x2 matrix inverse, warped refinement); the Optical Flow TOP exists in this build but reports "not supported on this operating system" (NVIDIA only), so it cannot be used on macOS.
- **Smear**: `fxfb` (Feedback TOP of the final output) -> `smear_advect` (Displace TOP driven by `flow_final`, weight = -Gain) drags the previous output along the motion. `smear_keep` (Level TOP) turns the flow speed (B) into a keep weight, Persistence x clamp(0.5 + speed), and a **Matte TOP** (`smear`) blends the advected history over the source through that weight.
- **Warp**: one Displace TOP (`warp`) moves the source by the flow (weight = -8 x Gain / 2).
- **Flow visualisation**: the unit flow vector (`viz_unit`: Composite divide by `viz_len`, a Math TOP "length") is used as lookup coordinates into a Ramp TOP colour wheel (`viz_wheel`, radial, hue = angle) through a **Remap TOP** (`viz_hue`), so hue = direction. Brightness = 1 - exp(-speed x Gain x 0.6) (Math + Function TOPs), multiplied in, then 12 % of the source is added back.
- **Mode / Active**: a Switch TOP (`mode_active`) selects Smear / Warp / Viz, or the previous frame (`fxfb`) when Active is off; only the selected branch cooks.
- **Demo source** (inside `demo`): Noise + Ramp background, five Circle TOPs textured by Noise TOPs and moved by Transform TOPs, and a Rectangle-TOP bar, all Composite TOPs. Look = Mono and Accent drive the colour expressions.
- GLSL kept: only `flow.glsl` (the solver and its temporal smoothing).

Benchmark (tools/bench.py, interleaved medians on a heavily loaded machine, default Mode = smear, GPU ms old -> new): 1280x720 2.45 -> 2.19 (-11 %), 1920x1080 3.42 -> 3.51 (+3 %). Repeats ranged from -11 % to +18 % at 720p and -9 % to +58 % at 1080p because other applications were using the GPU; the structural change that made the difference was using the Matte TOP (one full-resolution pass) for the smear blend instead of a multiply plus an Over.

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
