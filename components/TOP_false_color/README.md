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

## Demo source
The built-in preview source lives in a `demo` Base COMP behind a Switch: it is selected only while `in1` is unconnected, so with an input connected it does not cook. There is no Loop page; animation uses absolute time and only exists to make the unconnected preview move.
