# MAT_jelly
Reusable **GLSL MAT** for translucent gummy/jelly: wrap diffuse, back-light translucency (Barre-Jones), thickness approximation (view-angle + noise) driving Beer-Lambert absorption toward a deep colour, rim glow, spec + env fresnel. Vertex stage jiggles the mesh  and perturbs normals. Preview: wobbling torus rendered to the internal `preview` TOP.

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
| Jiggle, Jigglefreq, Jigglespeed | vertex wobble amplitude / frequency / cycles per preview cycle |
| Spin, Camdistance, Resolution | preview |



## Inputs and outputs
| Inputs | Type | Meaning |
|---|---|---|
| (none) | | self-contained |
| Outputs | Type | Label |
|---|---|---|
| out1 | MAT | material (the `mat` GLSL MAT); the preview render is the internal `preview` TOP |

The material itself is `<comp>/mat`: set a Geometry COMP's Material parameter to e.g. `op('ex1_MAT_jelly/mat')` (see the snippets). Its uniforms are driven from this COMP's parameters, so keep the MAT inside the COMP.

