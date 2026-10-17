# GEN_flow_field_lines
(Library name `GEN_flow_field_lines`, formerly `flow_field_lines`. Shipped as `tox/GEN/GEN_flow_field_lines.tox`.)

## Inputs
| Input | Type / purpose |
|---|---|
| in1 | In TOP (optional): luminance steers the flow angle |

## Outputs
| Output | Label / content |
|---|---|
| out1 | lines: the accumulated stroke image (rgba16float) |

## Loop / Clock
`Clock` (Loop page) takes a CHOP with a `phase` channel (0-1). Set it and `Timesource` = `phase`: the `Phase` parameter is then driven by that channel (clear `Clock` to go back to manual `Phase`). Use a ramp LFO renamed `phase`, or a Beat CHOP ramp renamed `phase`, to lock motion to a tempo.

Long-exposure flow field strokes. A float state texture (`state`, feedback loop) holds particle position/age; the velocity comes from curl or angle Perlin noise (or luminance of `in1`). Each particle is drawn as a short instanced segment into an accumulation feedback buffer (`accum`) with exponential fade.
- **Controls**: Resolution, Active, Reset (pulse; clears particles and canvas), Speed, Count, Fieldscale, Fieldspeed, Fieldtype, Turbulence, Stepsize, Lifetime, Fade, Inputamt.
- **Render**: Linewidth, Trail (segment length in steps), Intensity, Exposure, Colormode (line colour / direction / age / per particle), Linecolor, Hue, Bgcolor.
- Sims are pulled by whatever is downstream of `out1` (no keepalive DAT; the Alwayscook toggle was removed in v2).

## Loop & Look (batch-2 retrofit)

### Loop page
| Param | Meaning |
|---|---|
| Timesource | `abstime` (free-running, original behaviour) or `phase` (motion is a function of `Phase`) |
| Phase | 0-1 loop phase, drive externally (LFO / timeline / beat clock) in `phase` mode |
| Loopseconds | loop length used when Timesource=abstime-derived clocks are needed (default 8 s) |
| Loopbeats / Bpm | if Loopbeats > 0 the loop length is Loopbeats*60/Bpm seconds instead of Loopseconds |
`Loopreset` (toggle): when on, resets the feedback state at each loop wrap.

**How the loop works:** STATEFUL (particle trails accumulate in feedback). In phase mode the *field* is periodic (4D noise on a circle, period = 1 loop) but the accumulated lines carry history, so frames at phase 0 and 1 are similar in structure, not pixel-identical. Turn on `Loopreset` to clear the particle/accum feedback when the loop wraps for a hard, repeatable loop (at the cost of a regrow at each loop start). Mono lowers line intensity (Monogain via gain constants in inst.glsl).

### Look page
`Look` = `Original` (default, unchanged) or `Mono` (black background, bone-white / grey, rendah style). `Accent` (0-1) adds red accents in Mono (a fraction of particles are red (Accent*15%)).
