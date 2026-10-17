# SDF_deform

SDF operation: deform the field.

Wire format: see the SDF section of `CONVENTIONS.md`. Parameters are animatable (expressions, CHOPs) without recompiling shaders.

## Inputs
- in1 SDF

## Outputs
- **out1** SDF (DAT): the node's SDF payload, including all upstream nodes. Connect it to the input of another SDF_ node, SDF_render or a converter.

## Parameters
- **Mode**: Twist, Bend, Noise Displace, Round (inflate) or Onion (shell).
- **Amount**: Twist/bend rate, noise strength, round radius or onion thickness.
- **Axis**: Twist / bend axis.
- **Noise Frequency / Noise Offset**: Noise mode: spatial frequency and pan (animate the offset).

## Notes
- Every SDF_ node has an internal `preview` TOP (a small orbiting raymarch of its own SDF), shown in the node viewer.
- Twist, bend and noise reduce distance accuracy; use SDF_render Step Scale ~0.6-0.8.
- Snippets: About > Snippets.
