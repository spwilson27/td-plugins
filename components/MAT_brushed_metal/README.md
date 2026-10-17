# MAT_brushed_metal
Brushed + anodized (titanium heat-tint) metal with anisotropic highlights.

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
| Direction | brush direction (object space): axis X/Y/Z, radial spokes about Y, circular rings about Y |
| Brushscale / Streakamt | streak frequency across brush / strength of streak normal+brightness noise |
| Roughalong / Roughacross | anisotropic roughness; highlight smears across the brush by Roughacross |
| Anodize | 0 raw metal -> 1 fully heat-tinted |
| Heightmix | tint driver: 0 view angle -> 1 object-space height (Y) |
| Tintrange / Tintoffset / Tintanim | palette cycles spanned, start point (0.5 ~ blue), loopable sinusoidal drift |
| Reflect, Basecolor | gain, metal colour |

Uniforms: uB0 (mode, Brushscale, Streakamt, Roughalong), uB1 (Roughacross, Anodize, Heightmix, Tintrange), uB2 (Tintoffset, Tintanim, Reflect), uB3 (base rgb).
Technique: the vertex shader passes an object-space brush tangent (and its world version); the pixel shader averages 13 env lookups spread along the bitangent. Needs normals, not UVs.
Loop: only Tintanim animates (sin(2*pi*phase)).

## Inputs and outputs
| Inputs | Type | Meaning |
|---|---|---|
| in1 | TOP | optional equirect environment map (Envmix) |
| in2 | CHOP | optional modulation. Last input |
| Outputs | Type | Label |
|---|---|---|
| out1 | TOP | preview (render of the material on test geometry) |

The material itself is `<comp>/mat`: set a Geometry COMP's Material parameter to e.g. `op('ex1_MAT_brushed_metal/mat')` (see the snippets). Its uniforms are driven from this COMP's parameters, so keep the MAT inside the COMP.

**Clock (Loop page):** the `Clock` parameter takes a CHOP. When it is set and `Timesource` = `phase`, the loop phase is read from that CHOP's `phase` channel (0-1) instead of `Phase`. Drive it with a ramp LFO (amp 1, channel name `phase`) or a Beat CHOP.
