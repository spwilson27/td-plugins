# SDF_combine

SDF operation: combine two SDFs.

Wire format: see the SDF section of `CONVENTIONS.md`. Parameters are animatable (expressions, CHOPs) without recompiling shaders.

## Inputs
- in1 SDF A
- in2 SDF B

## Outputs
- **out1** SDF (DAT): the node's SDF payload, including all upstream nodes. Connect it to the input of another SDF_ node, SDF_render or a converter.

## Parameters
- **Operation**: Union, Subtract B from A, Intersect, or Morph A to B.
- **Smooth K**: Smooth-blend radius (0 = hard). Colours blend with the shape.
- **Morph**: Blend amount for the Morph operation.

## Notes
- Every SDF_ node has an internal `preview` TOP (a small orbiting raymarch of its own SDF), shown in the node viewer.
- Unconnected inputs fall back to a built-in sphere (A) / box (B).
- Snippets: About > Snippets.
