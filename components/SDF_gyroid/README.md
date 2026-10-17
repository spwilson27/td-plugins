# SDF_gyroid

SDF primitive: triply periodic minimal surface.

Wire format: see the SDF section of `CONVENTIONS.md`. Parameters are animatable (expressions, CHOPs) without recompiling shaders.

## Inputs
- none (primitive)

## Outputs
- **out1** SDF (DAT): the node's SDF payload, including all upstream nodes. Connect it to the input of another SDF_ node, SDF_render or a converter.

## Parameters
- **Surface**: Gyroid, Schwarz P or Diamond.
- **Frequency**: Cells per unit.
- **Thickness**: Wall thickness (field units).
- **Bound Radius**: Intersects with a sphere of this radius; 0 = infinite lattice.
- **Color / Color 2**: Albedo blended across the surface.

## Notes
- Every SDF_ node has an internal `preview` TOP (a small orbiting raymarch of its own SDF), shown in the node viewer.
- A TPMS lattice. The field is not an exact distance, so SDF_render Step Scale ~0.7-0.9 is advised.
- Snippets: About > Snippets.
