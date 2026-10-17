# TOP_instance_grid
Turns an image into a 3D field of instanced boxes / spheres / cones, rendered with an internal orbit camera, light and shadows. The input is downsampled to Countx x County; each pixel becomes one instance (Geometry COMP instancing from small float TOPs: translate / rotate / scale / colour).

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

## Implementation
No GLSL. The per-instance data is a Countx x County image (one pixel per instance) built from native TOPs:
* `to_grid` (Resolution TOP) shrinks the image to the grid; **Reorder TOP** `luma_raw` takes its luminance, a **Level TOP** `luma` clamps it to 0..1 and applies `Invert`.
* One **Math TOP** `from_luma` turns luminance into four numbers per instance, each channel with its own From -> To range (all driven by the parameters): R = width (`Basesize`, grown by `Scaleamt`), G = height (`Heightbase + Heightamt`, swelled by `band1`), B = Y rotation (`Rotamt` x 360), A = half the height. A **Composite TOP (Maximum)** against a constant keeps towers at least 0.02 tall (`width_height_rot`).
* Position: two **Ramp TOPs** (left-right, bottom-top) scaled by Math TOPs to `Spacing`; a **Reorder TOP** `inst_t` assembles translate = (x, height/2, z). These two ramps only recook when a parameter changes.
* The Geometry COMP reads translate from `inst_t`, and rotate / scale straight from channels of `width_height_rot` (rotate Y = blue, scale X/Z = red, scale Y = green).
* Colour: `Look = original` is a **Cross TOP** between white and the image (`Colormix`); `Look = mono` is Math (0.12 + 0.88 luma) x bone colour with a red layer (`Accent` x smoothstep(0.78, 0.92, luma), built from Level + Math + Composite) laid over it. The Geometry COMP's colour op is chosen by an expression, so the unused branch never cooks.
* Checked against the old shader: instance textures differ by less than 3e-4 and renders by less than 4e-5 (mean).
* **Bench** (`tools/bench.py --against` the old GLSL tox, GPU ms, old -> new, 1280x720 / 1920x1080): 1.06 -> 1.12 (+6 %), 1.20 -> 1.24 (+4 %). A second run of the same harness counting only ops that cooked that frame: 1.03 -> 1.09 (+6 %), 1.14 -> 1.24 (+9 %). (The shipped bench adds up `gpuCookTime` of every op every frame, including ops that did not cook that frame, which over-counts static native nodes; the second figure counts only ops that cooked. The GPU was shared with other jobs, so single runs vary by 10-20 %.)
