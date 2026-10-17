# TOP_false_color
Luminance-driven false-colour maps. `in1` TOP image (default source if unconnected); `in2` TOP optional depth/driver. Output `out1`.

| Param | Meaning |
|---|---|
| Map | Thermal (ironbow) / X-Ray / Night Vision / Custom 3-stop gradient (Colora/b/c) |
| Driver | Luminance of in1, or In2 (falls back to in1 if in2 unconnected) |
| Gain, Bias, Invert | map input levels |
| Edges, Edgecolor | Sobel edge overlay (on driver) |
| Noise | temporal grain + fixed column pattern sensor noise |
| Isotherms | contour lines at 8 levels |
| Mixoriginal | blend back original |
| Crosshair, Target, Hudcolor | reticle, ticks, corner brackets, level meter reading the value at Target |
| Legend | gradient scale bar on right |




## v2 interface
| Connector | Type | Label / use |
|---|---|---|
| in1 | In TOP | image (default animated source if unconnected) |
| in2 | In TOP | optional depth / driver (Driver = In2) |
| in3 | In CHOP | optional modulation (band1..band4, beat) |
| out1 | Out TOP | result |

New common parameters: `Mix` (dry/wet vs in1), `Bypass` (passes in1 straight through), `Resolutionmode` (`input` follows in1 / default source, `custom` uses `Resolutionw/h`), `Modamount` (scales the modulation input).

Modulation: `band1` adds `Modamount*band1` to `Gain`. Mixoriginal remains the false-colour/original blend; Mix is the overall dry/wet.

## Implementation
Network (left to right): `in1` / `demo` -> `src` Switch -> `driver` Switch (in2 when Driver = In2) -> **`falsecolor`** GLSL TOP -> `mixer` (Mix) -> `bypass` -> `out1`.

- **Palettes are native.** Inside the `palettes` Base COMP, one Ramp TOP per map (`thermal`, `xray`, `night`, `custom`; each reads its key table from a Table DAT) feeds a `palette` Switch (index = Map). The `custom` ramp gets its three stops from Colora/b/c through Constant CHOPs -> Join CHOP -> CHOP to DAT, so the gradient follows the colour parameters live. To restyle a map, edit the keys of its Ramp.
- **Demo source is native** (`demo` Base COMP, gated): Noise + Tile (grid) TOPs, Circle TOPs for the glowing discs and rings, Rectangle TOPs for the rotating bar and scan line, a Ramp TOP for the range strip.
- **GLSL kept: `falsecolor` (fc.glsl).** One pass does gain/bias/invert, the temporal grain and column noise, the palette lookup (a texture fetch into the palette strip), isotherms, the Sobel edge overlay, the night-vision scanlines/vignette and the whole HUD (reticle, ticks, brackets, level meter at Target, legend).
  Why: a complete native version was built and measured (Monochrome, Noise, Math, Level, Lookup, Edge, Composite, Rectangle and Circle TOPs, about 70 full-resolution passes, and a TOP to CHOP for the meter). It looked equivalent but cost 14.2 ms (720p) and 28.7 ms (1080p) against 0.8 ms for GLSL, because every native TOP is a separate full-frame pass (the HUD alone is ~35 shapes) and the TOP to CHOP read-back stalls the GPU. A single fused shader is the only form within the 20 % budget.

Benchmark (`tools/bench.py --against`, interleaved medians, GPU ms):

| | old (all GLSL) | new (native palettes + GLSL core) | change |
|---|---|---|---|
| 1280x720 | 1.83 | 1.91 | +4 % |
| 1920x1080 | 2.44 | 2.23 | -8 % |

(Three runs gave +8 %, +35 %/+25 %, -9 %/-20 %, +4 %/-8 %: on this machine the run-to-run noise is about +/-20 %, so the cost is equal to the all-GLSL version.)

## Demo source
The built-in preview source lives in a `demo` Base COMP behind a Switch: it is selected only while `in1` is unconnected, so with an input connected it does not cook. There is no Loop page; animation uses absolute time and only exists to make the unconnected preview move.
