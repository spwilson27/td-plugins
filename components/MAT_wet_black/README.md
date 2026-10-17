# MAT_wet_black
Wet / glossy black (oil, tar). Near-black base, sharp clearcoat reflections of the studio env, world-space noise flowing downward plus falling drip beads and trails perturbing the normal.

## Common
- Inputs: `in1` TOP (optional equirect environment map, used when `Envmix`>0; otherwise a built-in procedural studio env: overhead softbox, strip lights, rim strip, red accent bar), `in2` CHOP (optional, ferrofluid only).
- Output: `out1` TOP = preview render (sphere + torus knot, slow rotation, dark backdrop, ACES tonemap). MAT is at `<comp>/mat` (GLSL MAT; uses `TDPos/TDDeform` only, no UVs, no TD lights) — assign it to any geometry via `<comp>/mat`.
- Material page common params: `Envmix` (0 = procedural env, 1 = in1 equirect), `Envrot` (env rotation 0-1), `Envgain`, `Accent` (red accent bar strength in env), `Speed`.
- Preview page: `Resolution`, `Geometry` (both/sphere/knot), `Spin` (turns per loop), `Camdist`, `Backdrop`, `Exposure`, `Vignette`.
- Loop page: `Timesource` (abstime/phase), `Phase`, `Loopseconds`, `Loopbeats`, `Bpm`. The MAT receives a wrapped phase `uP0.x` in [0,1); every animated term is a periodic function of it (integer harmonics, or two-layer crossfade), and spin is an integer number of turns, so Phase 0 == 1 is seamless.
- Uniforms are set from the comp pars through expressions on the MAT Vectors page (names listed below).

## Material params
| Par | Meaning |
|---|---|
| Wetness | 0 satin -> 1 sharp clearcoat; also strengthens film |
| Bump | normal perturbation strength |
| Scale | world-space frequency of the flowing noise |
| Flow | amount of flowing noise |
| Dripscale / Dripamt | density / strength of drips (columns along world X and Z) |
| Roughness | clearcoat roughness (blur of env lookup) |
| Reflect | clearcoat reflection gain |
| Basecolor | base colour |

Uniforms: uP0 (phase, envmix, envrot, envgain), uP1 (accent), uW0 (Wetness, Bump, Scale, Flow), uW1 (Dripscale, Dripamt, Roughness, Reflect), uW2 (base rgb).
Loop: flowing noise = two noise layers advected -Y over one loop and crossfaded with triangle weights offset by half a loop; drips fall at integer multiples of the loop rate.
Notes: noise/drips are in WORLD space, so objects that move/rotate swim through the pattern (intended). No UVs needed.

## Inputs and outputs
| Inputs | Type | Meaning |
|---|---|---|
| in1 | TOP | optional equirect environment map (Envmix) |
| in2 | CHOP | optional modulation. Last input |
| Outputs | Type | Label |
|---|---|---|
| out1 | TOP | preview (render of the material on test geometry) |

The material itself is `<comp>/mat`: set a Geometry COMP's Material parameter to e.g. `op('ex1_MAT_wet_black/mat')` (see the snippets). Its uniforms are driven from this COMP's parameters, so keep the MAT inside the COMP.

**Clock (Loop page):** the `Clock` parameter takes a CHOP. When it is set and `Timesource` = `phase`, the loop phase is read from that CHOP's `phase` channel (0-1) instead of `Phase`. Drive it with a ramp LFO (amp 1, channel name `phase`) or a Beat CHOP.
