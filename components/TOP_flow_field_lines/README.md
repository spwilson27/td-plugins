# TOP_flow_field_lines
Long-exposure flow strokes driven by the input image. Particles (a float state texture in a feedback loop) are advected along a field computed from `in1`, drawn as short instanced segments coloured by the image into an accumulation buffer with exponential fade, then composited with the input. Without an input a built-in animated demo image is used (gated `demo` COMP, does not cook when `in1` is connected).

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
Particles spawn uniformly at random (not weighted by the image); flat areas rely on Turbulence to move; very large Count is GPU heavy.
