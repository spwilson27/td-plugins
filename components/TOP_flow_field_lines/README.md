# TOP_flow_field_lines
Long-exposure flow strokes driven by the input image. Particles (a Particle POP) are advected along a field computed from `in1`, drawn as short instanced quads coloured by the image into an accumulation buffer with exponential fade, then composited with the input. Without an input a built-in animated demo image is used (gated `demo` COMP, does not cook when `in1` is connected).

## Inputs
| Input | Purpose |
|---|---|
| in1 | image (field and colour source) |
| in2 | modulation CHOP (optional, last): band1 -> Speed, band2 -> Turbulence, band3 -> Intensity, band4 -> Line Width, beat -> kicks Rotate by 60 degrees |

## Outputs
| Output | Content |
|---|---|
| out1 | strokes composited with the input (per Compose, Mix, Bypass) |
| out2 | flow field: RG = direction * 0.5 + 0.5, B = field strength (0-1) |

## Parameters
- **Controls**: Mix, Bypass, Resolutionmode (input / custom), Play, Reset (clears particles and exposure), Speed, Compose (over input / add / on background), Inputdim (input brightness under strokes in "over"), Bgcolor.
- **Render**: Resolutionw/h (custom mode).
- **Field**: Fieldmode (contour = perpendicular to luminance gradient, gradient, angle from luminance, angle from hue), Inputamt (image influence), Smooth (gradient radius px), Rotate (degrees), Fieldscale / Fieldspeed (curl noise), Turbulence (noise blended in; also guides particles through flat areas), Speedbymag.
- **Strokes**: Count, Stepsize, Lifetime, Linewidth, Trail, Intensity, Exposure, Fade (closer to 1 = longer exposure), Colormode (input image / direction / age / line colour), Saturation, Linecolor.

The field follows the live input every frame; Reset restarts the particles and the exposure buffer.

## Limitations
Particles spawn uniformly at random (not weighted by the image); flat areas rely on Turbulence to move; very large Count is GPU heavy. The simulation advances one step of 1/60 s per cooked frame (like the old shader state), and a fresh network needs about Lifetime/2 frames to reach full density.

## Implementation
Built from built-in nodes; follow the wires left to right.
- **Field (GLSL, `field`)**: gradient / luminance / hue direction and the curl-noise mix (perlin gradient, normalise, rotate). Kept GLSL: it is per-pixel maths on the input image, and a native Slope/Blur/Noise/Math chain of about 20 full-resolution TOPs would be far more expensive.
- **Particles**: `spawn_points` (Point Generator POP, a pool of 65536 positions over the picture) -> `particles` (Particle POP; Count, Lifetime and Play drive it; births oversupplied so that births only fill free slots) -> `field_to_velocity` (Lookup Texture POP samples the field TOP at each particle's position and writes PartVel, rescaled to +-Stepsize x Speed) -> `field_magnitude` (second Lookup Texture POP reads the field strength) -> `speed_and_bounds` (Math Combine POP: velocity x speed-by-magnitude, and particles that left the picture are aged out so they respawn) -> `null_loop` (target of the Particle POP).
- **Strokes**: `stroke_transform` (Math Combine POP: world position half a stroke behind the particle, length from the velocity and Trail, rotation by atan2, age fade), `colour_from_texture` (Lookup Texture POP reading one of: saturated input image, direction palette = a Ramp-TOP colour wheel looked up with a Remap TOP through the field, age palette ramp, constant line colour; chosen by a Switch TOP) and `colour_fade` (Math Combine POP). A Geometry COMP **instances** a thin box from those POP attributes (translate, rotate, scale and colour straight from the POP), and a Render TOP with an orthographic camera draws it.
- **GLSL kept**: `field.glsl` (above), `accum.glsl` (acc = acc x Fade + strokes, a feedback accumulation) and `final.glsl` (tone map 1 - exp(-acc x Exposure) with the three Compose modes). Native versions of the last two (Math, Function, Reorder, Composite, Switch TOPs) were built and measured: +43 % GPU at 1280x720 and +46 % at 1920x1080 against the old component, so they stay as two small shaders.
- **Demo source** (inside `demo`): a vertical Ramp TOP plus six Circle TOPs (disc and ring) moving on Lissajous paths, summed in a Composite TOP.
- The 4 state/instance GLSL TOPs and the demo shader of the old version are gone; the Particle POP replaces the state texture and the Math Combine POP the instance textures.

Benchmark (tools/bench.py, interleaved medians, default settings, quiet-machine runs; GPU ms old -> new): 1280x720 0.87 -> 0.98 (+12 %) and 0.90 -> 0.96 (+6 %); 1920x1080 1.52 -> 1.64 (+7 %) and 1.59 -> 1.67 (+5 %). Runs taken while other applications used the GPU scattered much more (the median ratio ranged from -25 % to +100 %).
