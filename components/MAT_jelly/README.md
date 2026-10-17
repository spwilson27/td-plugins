# MAT_jelly
Reusable **GLSL MAT** for translucent gummy/jelly: wrap diffuse, back-light translucency (Barre-Jones), thickness approximation (view-angle + noise) driving Beer-Lambert absorption toward a deep colour, rim glow, spec + env fresnel. Vertex stage jiggles the mesh (periodic in phase) and perturbs normals. Preview: wobbling torus rendered to `out1`.

**Use the material elsewhere:** `op('<comp>/mat')` (assign to any Geometry COMP's Material). Uniforms are driven from this COMP's custom pars via `parent()` expressions. Note: thickness is a cheap approximation (no real backface depth pass), and the jiggle uses the object-space P and N attributes.

| Param | Meaning |
|---|---|
| Preview | Torus / Fat torus |
| Tint, Deepcolor | surface tint and absorbed deep colour |
| Wrap | wrap-lighting amount |
| Translucency | back-light bleed |
| Rimglow | rim glow gain |
| Absorption, Thickness | Beer-Lambert strength / thickness scale |
| Innernoise, Noisescale | inner density variation |
| Specpower, Envintensity | gloss |
| Jiggle, Jigglefreq, Jigglespeed | vertex wobble amplitude / frequency / cycles per loop |
| Spin, Camdistance, Resolution | preview |

**Loop page** (all components): `Timesource` (`abstime` | `phase`), `Phase` (0-1), `Loopseconds`, `Loopbeats` (0 = use seconds, else beats at `Bpm`), `Bpm`. In `phase` mode, every motion is a function of `Phase` only; abstime mode just advances the same phase at 1/loop-duration.

**Loop:** jiggle phase = `2*pi*Phase*k` (integer k) and inner noise on a circular path.

## Inputs and outputs
| Inputs | Type | Meaning |
|---|---|---|
| (none) | | self-contained |
| Outputs | Type | Label |
|---|---|---|
| out1 | TOP | preview (render of the material on test geometry) |

The material itself is `<comp>/mat`: set a Geometry COMP's Material parameter to e.g. `op('ex1_MAT_jelly/mat')` (see the snippets). Its uniforms are driven from this COMP's parameters, so keep the MAT inside the COMP.

**Clock (Loop page):** the `Clock` parameter takes a CHOP. When it is set and `Timesource` = `phase`, the loop phase is read from that CHOP's `phase` channel (0-1) instead of `Phase`. Drive it with a ramp LFO (amp 1, channel name `phase`) or a Beat CHOP.
