# SDF_sphere

SDF primitive: sphere.

Wire format: see the SDF section of `CONVENTIONS.md`. Parameters are animatable (expressions, CHOPs) without recompiling shaders.

## Inputs
- none (primitive)

## Outputs
- **out1** SDF (DAT): the node's SDF payload, including all upstream nodes. Connect it to the input of another SDF_ node, SDF_render or a converter.

## Parameters
- **Radius**: Sphere radius.
- **Color**: Albedo (Look page).

## Notes
- Every SDF_ node has an internal `preview` TOP (a small orbiting raymarch of its own SDF), shown in the node viewer.
- A sphere. Outputs colour as the SDF albedo channel.
- Snippets: About > Snippets.
