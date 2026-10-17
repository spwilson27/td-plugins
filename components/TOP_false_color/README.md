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

**Loop page** (all four): `Timesource` (abstime/phase), `Phase` (0-1), `Loopbeats` (default 8) with `Bpm` (120), or `Loopseconds` (>0 overrides beats). Internally one phase value P=fract(time/loop) (or `Phase`) drives everything.

**Seamless loop:** the effect is memoryless; grain is hashed from the in-loop frame index (periodic). Looping depends on the input.


## v2 interface
| Connector | Type | Label / use |
|---|---|---|
| in1 | In TOP | image (default animated source if unconnected) |
| in2 | In TOP | optional depth / driver (Driver = In2) |
| in3 | In CHOP | optional modulation (band1..band4, beat, phase) |
| out1 | Out TOP | result |

New common parameters: `Mix` (dry/wet vs in1), `Bypass` (passes in1 straight through), `Resolutionmode` (`input` follows in1 / default source, `custom` uses `Resolutionw/h`), `Clock` (Loop page: CHOP whose `phase` channel drives the loop when Timesource=phase), `Modamount` (scales the modulation input).

Modulation: `band1` adds `Modamount*band1` to `Gain`. Mixoriginal remains the false-colour/original blend; Mix is the overall dry/wet.
