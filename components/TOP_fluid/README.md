# TOP_fluid

GPU stable-fluids (Jos Stam) solver that treats the input image as dye and smears it: semi-Lagrangian advection, divergence, warm-started Jacobi pressure solve, gradient subtraction, vorticity confinement and dissipation. State (velocity, pressure, dye) is rgba32float in feedback loops. Solid walls at the borders. Velocity is in cells per step.

**Inputs**
- `in1` image: advected as dye. `Dyesource` = `inject` blends it in continuously at `Injectrate` (the picture keeps re-forming); `seed` loads it only at start / on `Reset`, then the fluid smears it away. Its luminance edges also push the flow (`Edgeforce`).
- `in2` velocity / force (optional TOP): its R,G channels are added to the velocity every step, scaled by `Forcein`. Signed values (centre 0) are expected; for an unsigned source such as a Noise TOP, subtract 0.5 first. Animated sources give continuous motion.
- `in3` modulation CHOP (optional, last): `band1`-`band4`, `beat`. `beat` kicks the stir force x(1+3b); `band1` raises vorticity x(1+2b).

**Outputs**: `out1` smeared image (Mix / Bypass applied), `out2` velocity (R,G, 32-bit float), `out3` dye field (32-bit float).

| Page | Param | Notes |
|---|---|---|
| Controls | Play, Reset | Reset clears velocity and pressure and re-seeds dye from in1 |
| | Mix, Bypass | dry/wet against in1; bypass passes in1 through |
| | Resolutionmode, Resolutionw/h | `input` follows in1 (or the demo), `custom` uses Resolution |
| | Dyesource, Injectrate | inject continuously or seed only |
| | Speed, Iterations | time step multiplier, Jacobi iterations per frame |
| | Vorticity, Veldissipation, Dyedissipation | confinement and per-frame decay |
| Forces | Forcein, Edgeforce | in2 coupling, image-edge coupling |
| | Emitters, Splatsize, Force, Emitterspeed | internal free-running Lissajous stir splats (set Emitters 0 to be driven only by in2 / edges) |

## Fluid text
This component also replaces the old text-fluid generator: text is just a Text TOP fed into `in1`. Animate the text (Transform TOP / expression) or drive in2 with a moving noise or LFO-driven force field and the lettering swirls and smears. See snippet 2.

With nothing connected, an internal demo (colour noise plus the word FLUID, in the gated `demo` COMP) is smeared by the stir emitters. Lower `Iterations` (8-12) for speed. Snippets: About > Snippets.
