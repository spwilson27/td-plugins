# TOP_feedback_trails

Feedback-TOP trail rig: each frame the previous result is scaled/rotated/translated, hue-shifted, noise-displaced and decayed, then the input is blended in.

- **Inputs**: `in1` TOP (optional; unconnected = animated default shapes on black). **Outputs**: `out1` TOP (rgba16float).
- Build: `tools/tdctl.py exec <inst> components/TOP_feedback_trails/build.py` (build.py = `_lib/lib.py` + `body.py`, regenerate with `_lib/mk.sh feedback_trails`).

| Par | Meaning |
|---|---|
| Blend | Over (input keyed by luma*alpha over the faded history), Add, Max |
| Decay | per-frame multiplier of history (0.8..1) |
| Scale / Rotate / Translate | per-frame transform of history (Rotate in deg/frame, Translate in 0.01 uv/frame units) |
| Huedrift | hue rotation of history, deg/frame |
| Noiseamount / Noisescale / Noisespeed | noise displacement of the history lookup |
| Inject | gain of the incoming source |
| Active | off = freeze the current frame |
| Reset | pulse: clears history |
| Resolution (Render page) | output size, default 1280x720 |

Tips: Over mode keys black (luma threshold) so opaque video still trails; use Add/Max for bright-on-dark sources. Decay=1 with Add accumulates without bound.

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
- Modulation CHOP drives: Inject (x1+2*band1), Rotate (+8*beat deg).

## Demo source
With nothing connected to `in1` the component shows a built-in animated test source. It lives in the `demo` Base COMP and is selected by a Switch TOP only while `in1` is unconnected; with an input connected nothing inside `demo` cooks. The component has no Loop page or loop parameters: animation uses absolute time and only exists to make the preview move. Output is warning-free with nothing connected, with `in1` connected, and with all inputs connected.
