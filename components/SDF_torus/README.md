# SDF_torus

SDF primitive: torus.

Wire format: see the SDF section of `CONVENTIONS.md`. Parameters are animatable (expressions, CHOPs) without recompiling shaders.

## Inputs
- none (primitive)

## Outputs
- **out1** SDF (DAT): the node's SDF payload, including all upstream nodes. Connect it to the input of another SDF_ node, SDF_render or a converter.

## Parameters
- **Major Radius**: Ring radius.
- **Minor Radius**: Tube radius.
- **Axis**: Axis the ring is wound around.
- **Color**: Albedo.

## Notes
- Every SDF_ node has an internal `preview` TOP (a small orbiting raymarch of its own SDF), shown in the node viewer.
- A torus.
- Snippets: About > Snippets.
