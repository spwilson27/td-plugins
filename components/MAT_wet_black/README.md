# MAT_wet_black
Wet / glossy black (oil, tar). Near-black base, sharp clearcoat reflections of the studio env, world-space noise flowing downward plus falling drip beads and trails perturbing the normal.

## Common
- Inputs: `in1` TOP (optional equirect environment map, used when `Envmix`>0; otherwise a built-in procedural studio env: overhead softbox, strip lights, rim strip, red accent bar), `in2` CHOP (optional, ferrofluid only).
- Output: `out1` = Out MAT (the material); internal `preview` TOP (not an output) = preview render (sphere + torus knot, slow rotation, dark backdrop, ACES tonemap). MAT is at `<comp>/mat` (GLSL MAT; uses `TDPos/TDDeform` only, no UVs, no TD lights) — assign it to any geometry via `<comp>/mat`.
- Material page common params: `Envmix` (0 = procedural env, 1 = in1 equirect), `Envrot` (env rotation 0-1), `Envgain`, `Accent` (red accent bar strength in env), `Speed`.
- Preview page: `Resolution`, `Geometry` (both/sphere/knot), `Spin` (turns per preview cycle), `Camdist`, `Backdrop`, `Exposure`, `Vignette`.
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
Notes: noise/drips are in WORLD space, so objects that move/rotate swim through the pattern (intended). No UVs needed.

## Inputs and outputs
| Inputs | Type | Meaning |
|---|---|---|
| in1 | TOP | optional equirect environment map (Envmix) |
| in2 | CHOP | optional modulation. Last input |
| Outputs | Type | Label |
|---|---|---|
| out1 | MAT | material (the `mat` GLSL MAT); the preview render is the internal `preview` TOP |

The material itself is `<comp>/mat`: set a Geometry COMP's Material parameter to e.g. `op('ex1_MAT_wet_black/mat')` (see the snippets). Its uniforms are driven from this COMP's parameters, so keep the MAT inside the COMP.

