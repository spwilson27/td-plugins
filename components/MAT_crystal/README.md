# MAT_crystal
Faceted crystal / geode: Voronoi (or flat-derivative) facets, two-interface refraction of the env with per-channel IOR dispersion, absorption tint, glittering internal flakes.

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
| Facetmode | voronoi (object-space 3D Worley cells, each with its own normal tilt) or flat (dFdx/dFdy face normals; shows mesh triangles) |
| Facetscale / Facetstrength | cell density / tilt |
| Ior / Dispersion | mean IOR, R/B IOR offset |
| Inner | how different the exit facet is from the entry facet (fragmentation) |
| Sparkle / Sparklescale / Twinkle | internal flakes: intensity, density, loopable twinkle |
| Tint / Tintamt / Absorb | absorption colour, amount, density |
| Reflect | surface reflection gain |

Uniforms: uC0 (Facetmode, Facetscale, Facetstrength, Ior), uC1 (Dispersion, Inner, Sparkle, Sparklescale), uC2 (tint rgb, Tintamt), uC3 (Reflect, Absorb, Twinkle).
Loop: only flake twinkle animates (integer harmonics of phase); facets are in object space so spinning geometry makes them glint.

## Inputs and outputs
| Inputs | Type | Meaning |
|---|---|---|
| in1 | TOP | optional equirect environment map (Envmix) |
| in2 | CHOP | optional modulation. Last input |
| Outputs | Type | Label |
|---|---|---|
| out1 | TOP | preview (render of the material on test geometry) |

The material itself is `<comp>/mat`: set a Geometry COMP's Material parameter to e.g. `op('ex1_MAT_crystal/mat')` (see the snippets). Its uniforms are driven from this COMP's parameters, so keep the MAT inside the COMP.

**Clock (Loop page):** the `Clock` parameter takes a CHOP. When it is set and `Timesource` = `phase`, the loop phase is read from that CHOP's `phase` channel (0-1) instead of `Phase`. Drive it with a ramp LFO (amp 1, channel name `phase`) or a Beat CHOP.
