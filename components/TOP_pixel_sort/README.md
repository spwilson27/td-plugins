# TOP_pixel_sort

GPU pixel sorting + bytebeat corruption + channel shuffle on `in1` (animated default source if unconnected).

Sorting is an iterative odd-even transposition sort: a Feedback TOP holds the state, and Passes (max 16) chained GLSL passes run per frame, each compare-swapping neighbour pairs along Direction. Only pairs where both pixels are within Thresholdlow..Thresholdhigh swap, so out-of-range pixels act as span barriers. Key chooses the sort key (luma/hue/sat/red). Refresh slowly pulls the state back toward the live source so moving video keeps working. A final pass applies bytebeat XOR bands (4 classic formulae) and per-block channel permutation/offset.

| Connector | Name | Label | Notes |
|---|---|---|---|
| in1 | In TOP | image | optional |
| in2 | In CHOP | modulation | channel `band1` adds to Bytebeat, scaled by Modamount (kick -> corruption); other channels ignored |
| out1 | Out TOP | result | |

| Param | Meaning |
|---|---|
| Direction, Key | sort direction / key |
| Thresholdlow/high | span range |
| Passes | sort passes per frame (sort speed) |
| Sortamount | blend source -> sorted |
| Refresh | per-frame pull toward source |
| Bytebeat, Bandsize, Bandholdframes | bit-corruption amount / band height / frames each band pattern persists |
| Shuffle, Seed | channel shuffle amount / pattern seed |
| Active, Reset | freeze sort / re-seed state from source |
| Modamount | strength of the modulation input |
| Mix, Bypass | dry/wet against in1; Bypass passes in1 straight through |
| Resolutionmode (input/custom), Resolution | follow in1 or use Resolutionw/h |

## Demo source
The built-in preview source lives in a `demo` Base COMP behind a Switch: it is selected only while `in1` is unconnected, so with an input connected it does not cook. There is no Loop page; animation uses absolute time and only exists to make the unconnected preview move.

## Implementation

### Preview source (demo)
The `demo` COMP used when `in1` is unconnected is built only from native operators, no GLSL: a Noise TOP grain ground, six Circle TOP discs with highlight and halo rings, Rectangle TOP bar and scan line, and a Ramp TOP strip masked by a Rectangle TOP, stacked by Composite TOPs (looping). It sits behind the Switch, so it does not cook when an input is connected.

