# TOP_instance_grid
Turns an image into a 3D field of instanced boxes / spheres / cones, rendered with an internal orbit camera, light and shadows. The input is downsampled to Countx x County; each pixel becomes one instance (Geometry COMP instancing from four small float TOPs: translate / rotate / scale / colour).

## Inputs / outputs
| Connector | Label | Notes |
|---|---|---|
| `in1` (In TOP) | image | Optional. Unconnected = internal animated colour noise |
| `in2` (In CHOP) | modulation | Optional; uses `band1` (adds to height amount) |
| `out1` (Out TOP) | result | The final render, mixed/bypassed against the image |

## Parameters
- **Controls**: Shape (box/sphere/cone), Countx, County, Spacing, Basesize, Heightbase, Heightamt (luma -> height), Scaleamt (luma -> width), Rotamt (luma -> Y rotation), Invert, Colormix, Noisespeed (default source), Bgcolor, **Modamount** (band1 scales Heightamt by 1 + Modamount*band1), **Mix**, **Bypass**, **Resolutionmode**, Resolution.
- **Camera**: Orbitspeed, Orbitangle, Distance, Elevation, Fov. **Light**: Lightangle, Lightheight, Lightintensity, Ambient, Shadows.
- **Look**: `Original` or `Mono` (black, bone-white/grey) + `Accent` (red on the brightest instances).

## Mix / Bypass / Resolution
- Mix and Bypass act on the FINAL RENDER versus the dry image. Dry = the source image (in1, or the default noise when unconnected) scaled to the render resolution.
- Resolutionmode `input`: the render follows in1's resolution when connected, else Resolutionw/h (default 1280x720). `custom` always uses Resolutionw/h.
- Tips: increase Distance with bigger grids; Count up to 256x256 (65k instances).

## Demo source
The built-in preview source lives in a `demo` Base COMP behind a Switch: it is selected only while `in1` is unconnected, so with an input connected it does not cook. There is no Loop page; animation uses absolute time and only exists to make the unconnected preview move.
