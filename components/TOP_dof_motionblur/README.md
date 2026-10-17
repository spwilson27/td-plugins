# TOP_dof_motionblur

Post effect: depth of field with polygon/disc bokeh (gather, golden-angle samples, highlight boost, in-focus samples do not bleed onto blurred neighbours) plus motion blur (velocity-directed blur if `in3` is connected, and frame accumulation via a Feedback TOP). With nothing connected an internal animated scene (perspective floor lines + dots at random depths) is shown.

| Connector | Name | Label | Notes |
|---|---|---|---|
| in1 | In TOP | colour | optional |
| in2 | In TOP | depth | 0 = near, 1 = far (use Invertdepth otherwise) |
| in3 | In TOP | velocity | R,G in uv units, scaled by Velscale |
| in4 | In CHOP | modulation | channel `band1` pushes Focus by `Modamount * 0.5` (rack focus); other channels ignored |
| out1 | Out TOP | result | |
| out2 | Out TOP | depth | prepared depth map |

| Page | Param | Notes |
|---|---|---|
| Controls | Depthmode, Invertdepth, Focus, Range, Falloff | depth source; focus distance (0-1), in-focus half-range, ramp to full blur |
| | Maxblur (px @720p), Quality, Boost, Blades, Bladerot | bokeh size / samples / highlight weight / aperture shape |
| | Speed | default scene speed |
| | Modamount | strength of the modulation input |
| | Mix, Bypass | dry/wet against in1 (default scene when unconnected); Bypass passes in1 straight through |
| | Resolutionmode (input/custom), Resolution | follow in1 or use Resolutionw/h |
| Motion | Mbactive, Shutter, Velscale, Velsamples, Reset | accumulation 0..0.97, velocity blur |
| Output | Showdepth, Showcoc | debug: prepared depth / focus map (green in focus, red blurred) |
| Loop | Timesource (abstime/phase), Phase, Clock, Loopseconds, Loopbeats, Bpm | drives the default scene only; Clock CHOP's `phase` channel is used when Timesource = phase |

Loop: the default scene is periodic in loop phase. The frame accumulation is a recursive filter so a looping input converges to a periodic output after a short settling time (Reset clears it).
