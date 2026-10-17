# SDF_repeat

SDF operation: repeat an SDF.

Wire format: see the SDF section of `CONVENTIONS.md`. Parameters are animatable (expressions, CHOPs) without recompiling shaders.

## Inputs
- in1 SDF

## Outputs
- **out1** SDF (DAT): the node's SDF payload, including all upstream nodes. Connect it to the input of another SDF_ node, SDF_render or a converter.

## Parameters
- **Mode**: Grid (infinite), Grid (finite, +-count cells) or Polar.
- **Spacing**: Cell size per axis; 0 disables repetition on that axis.
- **Cells each side**: Finite mode: number of cells on each side of the origin.
- **Polar Count / Polar Axis**: Polar mode: number of copies around the axis. Offset the object from the axis upstream (SDF_transform).
- **Color Variation**: Per-cell brightness variation.

## Notes
- Every SDF_ node has an internal `preview` TOP (a small orbiting raymarch of its own SDF), shown in the node viewer.
- Repeating is not an exact distance when objects cross cell borders (keep objects inside a cell); Step Scale ~0.8 helps.
- Snippets: About > Snippets.
