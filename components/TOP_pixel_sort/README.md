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
| Loopfade | hard-refresh state at P=0 and fade the sorted result in/out |
| Active, Reset | freeze sort / re-seed state from source |
| Modamount | strength of the modulation input |
| Mix, Bypass | dry/wet against in1; Bypass passes in1 straight through |
| Resolutionmode (input/custom), Resolution | follow in1 or use Resolutionw/h |
| Loop: Timesource, Phase, Clock, Loopbeats, Bpm, Loopseconds | phase source; the Clock CHOP's `phase` channel is used when Timesource = phase |

**Loop:** sorting is stateful, so seamlessness comes from restarting: at P=0 the state is reset to the source and the sorted result fades in then out so P 0==1 shows the clean source. Needs a periodic source (default is). Disable Loopfade for continuous behaviour with live video.
