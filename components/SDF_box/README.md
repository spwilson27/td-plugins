# SDF_box

SDF primitive: rounded box.

Wire format: see the SDF section of `CONVENTIONS.md`. Parameters are animatable (expressions, CHOPs) without recompiling shaders.

## Inputs
- none (primitive)

## Outputs
- **out1** SDF (DAT): the node's SDF payload, including all upstream nodes. Connect it to the input of another SDF_ node, SDF_render or a converter.

## Parameters
- **Size X/Y/Z**: Full extents.
- **Roundness**: Edge radius (clamped to the smallest half-size).
- **Color**: Albedo.

## Notes
- Every SDF_ node has an internal `preview` TOP (a small orbiting raymarch of its own SDF), shown in the node viewer.
- A box with rounded edges.
- Snippets: About > Snippets.
