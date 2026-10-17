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

## Loop & Look (batch-2 retrofit)

### Loop page
| Param | Meaning |
|---|---|
| Timesource | `abstime` (free-running, original behaviour) or `phase` (motion is a function of `Phase`) |
| Phase | 0-1 loop phase, drive externally (LFO / timeline / beat clock) in `phase` mode |
| Loopseconds | loop length used when Timesource=abstime-derived clocks are needed (default 8 s) |
| Loopbeats / Bpm | if Loopbeats > 0 the loop length is Loopbeats*60/Bpm seconds instead of Loopseconds |
`Loopreset` (toggle): when on, resets the feedback state at each loop wrap.

**How the loop works:** STATEFUL feedback. Phase mode makes the default source and the displacement noise periodic (circular offsets); the trail history itself is not forced periodic, but converges quickly (decay) so it reads as seamless. `Loopreset` pulses Reset at every loop wrap for a hard loop.

### Look page
`Look` = `Original` / `Mono` switches only the **internal default test source** (used when `in1` is unconnected) to a black / bone-white / grey variant; `Accent` (0-1) tints one test object red. A connected `in1` is not recoloured (effects with intrinsic colour, e.g. RGB-split or CMYK halftone, keep it).


## v2 conventions (TOP_feedback_trails)

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
- Modulation CHOP drives: Inject (x1+2*band1), Rotate (+8*beat deg).
