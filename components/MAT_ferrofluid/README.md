# MAT_ferrofluid
Rosensweig ferrofluid: sharp conical spikes displaced in the VERTEX shader, pulled by an attractor and a modulation value; black mirror shading with per-pixel spike normals.

NEEDS A DENSE MESH (preview sphere is 320x640 quads). Pattern is a 3D Worley lattice of the object-space position, displacement is along the normal, so it works on any dense mesh with normals (sphere SOP, subdivided meshes); coarse meshes (the preview knot has ~6k verts) look rough.

## Common
- Inputs: `in1` TOP (optional equirect environment map, used when `Envmix`>0; otherwise a built-in procedural studio env: overhead softbox, strip lights, rim strip, red accent bar), `in2` CHOP (optional, ferrofluid only).
- Output: `out1` = Out MAT (the material); internal `preview` TOP (not an output) = preview render (sphere + torus knot, slow rotation, dark backdrop, ACES tonemap). MAT is at `<comp>/mat` (GLSL MAT; uses `TDPos/TDDeform` only, no UVs, no TD lights) — assign it to any geometry via `<comp>/mat`.
- Material page common params: `Envmix` (0 = procedural env, 1 = in1 equirect), `Envrot` (env rotation 0-1), `Envgain`, `Accent` (red accent bar strength in env), `Speed`.
- Preview page: `Resolution`, `Geometry` (both/sphere/knot), `Spin` (turns per preview cycle), `Camdist`, `Backdrop`, `Exposure`, `Vignette`.
- Uniforms are set from the comp pars through expressions on the MAT Vectors page (names listed below).

- `in2` CHOP (optional): channel 0 is added to the field strength (audio-like): amp = Baseline + Modulation + chop*Modgain + attractor pull.

## Material params
| Par | Meaning |
|---|---|
| Spikescale | spikes per object unit (density) |
| Height | max spike height |
| Sharp | profile exponent (higher = thinner, more concave spikes) |
| Regular | 0 irregular -> 1 near-regular lattice |
| Baseline | always-on field (0 = flat liquid) |
| Modulation / Modgain | manual / CHOP-driven field strength |
| Pull / Reach | attractor strength / falloff radius (world units) |
| Attractor (xyz) / Orbit | attractor world position; orbit radius for the preview animation (0 = static) |
| Lean | spikes tilt toward the attractor |
| Wobble / Variation | per-spike height pulsing (loopable) / static random height variation |
| Basecolor / Reflectivity / Roughness | shading |

Uniforms: uF0 (Spikescale, Height, Sharp, Regular), uF1 (Baseline, Modulation(+chop), Pull, Reach), uF2 (attractor xyz, Lean), uF3 (Wobble, Variation), uF4 (base rgb, Reflectivity), uF5 (Roughness).
Known limits: pixel normals ignore Lean; shading assumes roughly unit object/world scale; spikes are in the vertex stage so cost scales with mesh density.

## Inputs and outputs
| Inputs | Type | Meaning |
|---|---|---|
| in1 | TOP | optional equirect environment map (Envmix) |
| in2 | CHOP | field-strength modulation (channel 0 x Modgain). Last input |
| Outputs | Type | Label |
|---|---|---|
| out1 | MAT | material (the `mat` GLSL MAT); the preview render is the internal `preview` TOP |

The material itself is `<comp>/mat`: set a Geometry COMP's Material parameter to e.g. `op('ex1_MAT_ferrofluid/mat')` (see the snippets). Its uniforms are driven from this COMP's parameters, so keep the MAT inside the COMP.

