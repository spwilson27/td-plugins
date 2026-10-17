# TOP_dof_motionblur

Post effect: depth of field (Luma Blur TOP driven by the distance of the depth map from the focus value) plus motion blur (velocity-directed blur if `in3` is connected, and frame accumulation via a Feedback TOP). With nothing connected an internal animated scene (perspective floor lines + dots at random depths) is shown.

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
| | Maxblur (px @720p), Blades | bokeh size; Blades >= 3 = hard-edged box blur, < 3 = soft Gaussian |
| | Speed | default scene speed |
| | Modamount | strength of the modulation input |
| | Mix, Bypass | dry/wet against in1 (default scene when unconnected); Bypass passes in1 straight through |
| | Resolutionmode (input/custom), Resolution | follow in1 or use Resolutionw/h |
| Motion | Mbactive, Shutter, Velscale, Velsamples, Reset | accumulation 0..0.97, velocity blur |
| Output | Showdepth, Showcoc | debug: prepared depth / focus map (green in focus, red blurred) |

## Implementation
Network (left to right): `in1` / `demo` -> `src`; `in2` / `demo` -> `depthsrc` -> **depth preparation** -> **`defocus`** -> **`mblur`** -> **`accumulate`** -> `view` -> `mixer` -> `bypass` -> `out1` (`prep` -> `out2`).

- **Depth preparation (native):** `depth_in` (Monochrome, red channel of in2), `luma` (Monochrome of in1) and `radial` (a soft Circle TOP, inverted by Math) feed the `depth_source` Switch (Depthmode; `auto` = in2 if connected or the demo is showing, else radial). `prep` is a Level TOP whose Invert follows Invertdepth; it is `out2`.
- **Depth of field (native):** `focus_distance` is one Math TOP computing |depth - Focus| (pre-offset, square, root). The **Luma Blur TOP** `defocus` blurs `src` by that map: width 0 px up to `Range`, rising linearly to `Maxblur` x (height/720) at `Range + Falloff`. `dof_switch` skips the whole blur when Maxblur = 0. `Invertdepth` is applied by mirroring Focus (|1-d-f| = |d-(1-f)|), band1 modulation pushes Focus as before.
- **Frame accumulation (native):** Cross TOP `accumulate` mixes the current frame with a **Feedback TOP** (`Shutter`, Reset clears it).
- **Debug views (native, only cooked when selected):** `coc_x` Math + Level clamp + Lookup into a smoothstep Ramp give the focus map, coloured green -> red by a second Lookup (Showcoc); Showdepth shows `prep`.
- **Demo scene (native, gated `demo` COMP):** Constant/Rectangle TOPs for the floor lines (perspective spacing animated with the loop phase), a vertical Ramp for the floor depth, 30 Circle TOPs for the dots (drawn far to near, colour and depth versions).
- **GLSL kept: `mblur` (mblur.glsl, 24-tap velocity blur).** The native equivalent is N Displace TOPs along the velocity vector averaged by a Composite TOP: 8 taps cost about 10 full-frame passes (benchmarked at roughly 2x the GPU time of the whole old component), while one small shader does it in a single pass, so this part stays GLSL. It only cooks when in3 is connected.
- **Lost vs the GLSL version:** the polygon/disc bokeh with highlight boost (the `Quality`, `Boost` and `Bladerot` parameters were removed; `Blades` now only switches between a round Gaussian and a hard-edged box blur) and the rule that in-focus pixels do not bleed onto blurred neighbours (Luma Blur is a plain variable-width blur). The blur width ramp is linear (was smoothstep).

Benchmark (`tools/bench.py --against`, interleaved medians, GPU ms; three runs):

| run | 720p old -> new | 1080p old -> new |
|---|---|---|
| 1 | 4.18 -> 3.54 (-15 %) | 7.04 -> 7.91 (+12 %) |
| 2 | 4.44 -> 3.90 (-12 %) | 6.85 -> 6.52 (-5 %) |
| 3 | 2.56 -> 2.52 (-1 %) | 5.68 -> 5.67 (0 %) |

(The earlier all-native variant with 8 Displace taps and per-tap gating measured +66 % to +100 %.)

## Demo source
The built-in preview source lives in a `demo` Base COMP behind a Switch: it is selected only while `in1` is unconnected, so with an input connected it does not cook. There is no Loop page; animation uses absolute time and only exists to make the unconnected preview move.
