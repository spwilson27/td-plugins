# SDF_fractal

SDF primitive: fractal distance estimators.

Wire format: see the SDF section of `CONVENTIONS.md`. Parameters are animatable (expressions, CHOPs) without recompiling shaders.

## Inputs
- none (primitive)

## Outputs
- **out1** SDF (DAT): the node's SDF payload, including all upstream nodes. Connect it to the input of another SDF_ node, SDF_render or a converter.

## Parameters
- **Fractal**: Mandelbulb, Menger sponge or Kaleidoscopic IFS.
- **Iterations**: Detail level (1-16; Menger max 8).
- **Power / Scale**: Mandelbulb power; KIFS scale (clamped 1.2-4, or 2 when above 5). Menger always scales by 3.
- **Size**: Overall scale.
- **Fold Offset / Fold Rotate**: KIFS fold offset and per-iteration rotation (degrees).
- **Color / Color 2**: Base and orbit-trap colours.

## Notes
- Every SDF_ node has an internal `preview` TOP (a small orbiting raymarch of its own SDF), shown in the node viewer.
- Fractals. Use SDF_render with small Epsilon (0.0005) and Step Scale ~0.7 for fine detail.
- Snippets: About > Snippets.
