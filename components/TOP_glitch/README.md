# TOP_glitch

Datamosh / glitch processor on `in1` (unconnected = animated default shapes). Output `out1`.
Single GLSL pass with a feedback loop (for the compression smear). Events are quantised to "beats" (`Rate` per second, seeded by `Seed`).

| Par | Meaning |
|---|---|
| Amount | global multiplier for all sub-effects |
| Seed / Rate | random seed; beats per second for block/tear/sort re-rolls |
| Rgbsplit | chromatic channel split along a per-beat random direction |
| Blockdisplace | random blocks (grid size re-rolled per beat) shifted |
| Scanlinetear | horizontal per-row tearing plus a rolling tear band |
| Pixelsort | approximate GPU sort: runs of pixels above `Sortthreshold` along `Sortaxis` become streaks (run-start colour ramping to run-brightest) |
| Smear / Smearthreshold / Smearblock | fake compression hold: blocks whose difference from the previous output is below the threshold keep the old pixels; occasional keyframe refresh |
| Active | off = freeze |
| Reset | pulse: reloads feedback from the current input |
| Resolution (Render) | output size |

Limitations: pixel sort is a streak approximation (max 48 steps x 3px), not a true sort.

## Loop & Look (batch-2 retrofit)

### Loop page
| Param | Meaning |
|---|---|
| Timesource | `abstime` (free-running, original behaviour) or `phase` (motion is a function of `Phase`) |
| Phase | 0-1 loop phase, drive externally (LFO / timeline / beat clock) in `phase` mode |
| Loopseconds | loop length used when Timesource=abstime-derived clocks are needed (default 8 s) |
| Loopbeats / Bpm | if Loopbeats > 0 the loop length is Loopbeats*60/Bpm seconds instead of Loopseconds |
`Loopreset` (toggle): when on, resets the feedback state at each loop wrap.

**How the loop works:** Phase mode: glitch events are quantised to K = round(Rate*looplength) ticks per loop and the event index wraps mod K, so the glitch sequence repeats exactly each loop; default source is periodic. The smear feedback is stateful: `Loopreset` pulses Reset at loop start.

### Look page
`Look` = `Original` / `Mono` switches only the **internal default test source** (used when `in1` is unconnected) to a black / bone-white / grey variant; `Accent` (0-1) tints one test object red. A connected `in1` is not recoloured (effects with intrinsic colour, e.g. RGB-split or CMYK halftone, keep it).


## v2 conventions (TOP_glitch)

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
- Modulation CHOP drives: Amount (x1+band1+beat).
