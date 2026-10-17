# TOP_voronoi
Voronoi cells, cracked and stained glass built from an input image. Each cell is coloured by sampling the input at its site; seed density can follow the input's brightness or edges.

## Inputs / outputs
| Connector | Label |
|---|---|
| in1 (TOP) | image (a built-in animated demo is used when unconnected) |
| in2 (CHOP, optional) | modulation CHOP: band1 = edge glow, band2 = drift amount, band3 = shard displacement, beat = edge flash |
| out1 | stylised image |
| out2 | cell id + edge map: rgb = stable per-cell id colour, alpha = distance to the cell border (0 on the edge, 1 deep inside) |

## Parameters
- **Controls**: Mix, Bypass, Style (cells, edges, cracked glass, stained glass), Seeds (2-128), Jitter (0 = grid, 1 = random), Drift Speed / Amount (seeds wander; Speed 0 = static), Random Seed.
- **Cells**: Border Width, Edge Glow, Edge Colour + Edge Tint (how much the glow takes the input colours), Shard Displacement (cracked), Delaunay overlay + line width.
- **Density**: Density Follows (uniform, bright areas, dark areas, edges) and Amount. Seeds are chosen by weighted candidate selection, so they crowd where the input is bright / dark / has contours. With animated input the seeds can jump as the weights change.
- **Output**: Resolution Mode (input | custom) and Resolution.
- **Look**: Original or Mono (bone-white and grey, optional red Accent).

The effect is stateless (no Reset needed); seeds are re-derived each frame from the input. There are no loop parameters.

## Implementation

### Preview source (demo)
The `demo` COMP used when `in1` is unconnected is built only from native operators, no GLSL: a Constant TOP ground and seven soft, colourful Circle TOP blobs, stacked by a Composite TOP. It sits behind the Switch, so it does not cook when an input is connected.

