# TOP_droste_zoom

Droste / log-polar recursive picture-in-picture of `in1` (default internal source: monochrome frame/hatch/rings with a red marker). The image is repeated inside itself at `Inner Scale`, and the whole pattern zooms infinitely (optionally spiralling and spinning).

## Inputs / outputs

| Connector | Type | Label | Notes |
|---|---|---|---|
| in1 | In TOP | image | optional; internal animated source when unconnected |
| in2 | In CHOP | modulation | optional, last input. Uses `band1` (0-1): adds `Modamount * band1 * 0.3` to Inner Scale (a beat "pump") |
| out1 | Out TOP | result | final image (after Mix / Bypass) |

## Parameters

| Page | Param | Notes |
|---|---|---|
| Controls | Speed | zoom/animation rate (1 = one lattice cycle per 8 s) |
| | Innerscale | scale of each nested copy (period = ln(1/s)) |
| | Zoomperiods | nested-copy periods travelled per cycle (sign = direction, integer) |
| | Rotation | spiral: rotation in turns gained per period (any real value) |
| | Spin | whole-image turns per cycle (integer) |
| | Fill | fraction of the image radius used (1 = inscribed circle) |
| | Center, Seam, Original | centre point, ring-seam softening, blend of the un-warped image |
| | Modamount | strength of the modulation input |
| | Mix | dry/wet against in1 (or the default source) |
| | Bypass | passes in1 straight through |
| | Resolutionmode | `input` follows in1 (default source: Resolution); `custom` uses Resolution |
| | Resolution | used when Resolutionmode = custom or in1 is not connected |

## Seamless zoom
Coordinates are shifted along the self-similarity lattice vector (L, beta) by `delta = -Zoomperiods * p * L` (and the matching spiral rotation). At p = 1 that is an integer number of lattice periods, so the image is identical. Spin uses integer turns for the same reason.
Note: with a custom in1 the source is sampled in a circle (radius 0.5 of height * Fill); content outside it is never used.

## Demo source
The built-in preview source lives in a `demo` Base COMP behind a Switch: it is selected only while `in1` is unconnected, so with an input connected it does not cook. There is no Loop page; animation uses absolute time and only exists to make the unconnected preview move.

## Implementation

### Preview source (demo)
The `demo` COMP used when `in1` is unconnected is built only from native operators, no GLSL: a Constant TOP ground, Circle TOP rings, Rectangle TOP bars/frame/tick marks and a Circle TOP marker, stacked by a Composite TOP (looping with the animation phase). It sits behind the Switch, so it does not cook when an input is connected.

