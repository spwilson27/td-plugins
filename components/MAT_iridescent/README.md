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
| Spin | preview rotations per preview cycle; Camdistance; Resolution |



## Inputs and outputs
| Inputs | Type | Meaning |
|---|---|---|
| in1 | TOP | optional equirect environment map |
| Outputs | Type | Label |
|---|---|---|
| out1 | MAT | material (the `mat` GLSL MAT); the preview render is the internal `preview` TOP |

The material itself is `<comp>/mat`: set a Geometry COMP's Material parameter to e.g. `op('ex1_MAT_iridescent/mat')` (see the snippets). Its uniforms are driven from this COMP's parameters, so keep the MAT inside the COMP.

