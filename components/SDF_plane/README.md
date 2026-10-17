# SDF_plane

SDF primitive: plane.

Wire format: see the SDF section of `CONVENTIONS.md`. Parameters are animatable (expressions, CHOPs) without recompiling shaders.

## Inputs
- none (primitive)

## Outputs
- **out1** SDF (DAT): the node's SDF payload, including all upstream nodes. Connect it to the input of another SDF_ node, SDF_render or a converter.

## Parameters
- **Normal**: Plane normal (normalised).
- **Offset**: Signed distance from the origin along the normal (negative = below, for +Y).
- **Checker / Checker Size / Checker Color**: Optional checker pattern fading with distance.
- **Color**: Albedo.

## Notes
- Every SDF_ node has an internal `preview` TOP (a small orbiting raymarch of its own SDF), shown in the node viewer.
- An infinite plane (half-space).
- Snippets: About > Snippets.
