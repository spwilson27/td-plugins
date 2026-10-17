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

## Loop & Look (batch-2 retrofit)

### Loop page
| Param | Meaning |
|---|---|
| Timesource | `abstime` (free-running, original behaviour) or `phase` (motion is a function of `Phase`) |
| Phase | 0-1 loop phase, drive externally (LFO / timeline / beat clock) in `phase` mode |
| Loopseconds | loop length used when Timesource=abstime-derived clocks are needed (default 8 s) |
| Loopbeats / Bpm | if Loopbeats > 0 the loop length is Loopbeats*60/Bpm seconds instead of Loopseconds |
`Loopreset` (toggle): when on, resets the feedback state at each loop wrap.

**How the loop works:** Stateful (flow + advected feedback). Default source periodic in phase mode; Loopreset pulses Reset at loop start for a hard loop. Flow estimation needs real motion: with the test source the loop is clean, with live input seamlessness depends on that input.

### Look page
`Look` = `Original` / `Mono` switches only the **internal default test source** (used when `in1` is unconnected) to a black / bone-white / grey variant; `Accent` (0-1) tints one test object red. A connected `in1` is not recoloured (effects with intrinsic colour, e.g. RGB-split or CMYK halftone, keep it).


## v2 conventions (TOP_optical_flow)

**Inputs and outputs**

| Connector | Meaning |
|---|---|
| in1 (TOP) | image to process (unconnected = animated default source) |
| in2 (CHOP) | optional modulation: channels band1-band4, beat, phase (any subset) |
| out1 | result |
| out2 | flow (optical-flow vectors) |

**New parameters**
- `Mix` (0-1): dry/wet against the input. `Bypass`: passes in1 straight through (Switch TOP).
- `Resolutionmode`: `input` follows in1 (or the default source, sized by `Resolution`, when unconnected); `custom` uses `Resolution`.
- `Clock` (Loop page, CHOP): with Timesource = phase, phase is read from this CHOP's `phase` channel instead of `Phase`.
- Modulation CHOP drives: Gain (x1+2*band1).
