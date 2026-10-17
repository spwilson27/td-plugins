# MAT_iridescent
Reusable **GLSL MAT** implementing thin-film interference (per-wavelength Airy reflectance from film thickness + IOR + substrate IOR), fresnel rainbow rim, Kajiya-Kay anisotropic sheen, oil-slick thickness noise, and a procedural studio env reflection (or equirect env TOP via `in1`). A preview render (rotating torus / fat torus) goes to `out1`.

**Use the material elsewhere:** the MAT is `op('<comp>/mat')` (e.g. `op('/project1/MAT_iridescent/mat')`); assign it to any Geometry COMP's *Material* parameter. Its uniforms are driven by this COMP's custom parameters (expressions reference `parent()`, so keep the MAT inside this COMP, or copy it and repoint the vec expressions). The shader needs no scene lights (self-lit by env + two built-in directions).

| Param | Meaning |
|---|---|
| Preview | Torus / Fat torus |
| Filmthickness, Filmvariation | mean thickness (nm) and noise-driven variation |
| Filmior, Substrateior | film/substrate index |
| Iridescence | 0 = plain metallic, 1 = full interference colour |
| Fresnelpower | rim falloff exponent |
| Sheen, Anisotropy, Sheenexp, Brushangle | anisotropic sheen |
| Oilscale, Oilmotion | oil noise frequency / drift radius |
| Basecolor, Roughness, Envrotation, Envintensity | base + environment |
| Spin | preview rotations per loop; Camdistance; Resolution |

**Loop page** (all components): `Timesource` (`abstime` | `phase`), `Phase` (0-1), `Loopseconds`, `Loopbeats` (0 = use seconds, else beats at `Bpm`), `Bpm`. In `phase` mode, every motion is a function of `Phase` only; abstime mode just advances the same phase at 1/loop-duration.

**Loop:** oil noise is sampled along a circle in noise space (`cos/sin(2*pi*Phase)`), spin is an integer number of turns. Known limit: brushed-tangent field has the usual singularity at the poles of N.y (small pinch).

## Inputs and outputs
| Inputs | Type | Meaning |
|---|---|---|
| in1 | TOP | optional equirect environment map |
| Outputs | Type | Label |
|---|---|---|
| out1 | TOP | preview (render of the material on test geometry) |

The material itself is `<comp>/mat`: set a Geometry COMP's Material parameter to e.g. `op('ex1_MAT_iridescent/mat')` (see the snippets). Its uniforms are driven from this COMP's parameters, so keep the MAT inside the COMP.

**Clock (Loop page):** the `Clock` parameter takes a CHOP. When it is set and `Timesource` = `phase`, the loop phase is read from that CHOP's `phase` channel (0-1) instead of `Phase`. Drive it with a ramp LFO (amp 1, channel name `phase`) or a Beat CHOP.
