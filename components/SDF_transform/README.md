# SDF_transform

SDF operation: translate, rotate and uniformly scale.

Wire format: see the SDF section of `CONVENTIONS.md`. Parameters are animatable (expressions, CHOPs) without recompiling shaders.

## Inputs
- in1 SDF

## Outputs
- **out1** SDF (DAT): the node's SDF payload, including all upstream nodes. Connect it to the input of another SDF_ node, SDF_render or a converter.

## Parameters
- **Translate**: World offset.
- **Rotate**: Euler degrees (applied as Rz*Ry*Rx).
- **Scale**: Uniform scale (distances stay exact).

## Notes
- Every SDF_ node has an internal `preview` TOP (a small orbiting raymarch of its own SDF), shown in the node viewer.
- Unconnected input falls back to a built-in box.
- Snippets: About > Snippets.
