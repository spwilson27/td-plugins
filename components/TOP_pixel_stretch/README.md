# TOP_pixel_stretch
Slit/glitch-painting pixel smear. Pass A builds a 2048x1 column map: for each column (quantized into stripes of `Bandwidth` px) scan along the travel direction for the first luminance crossing of the (noisy, animated) threshold and store position + colour. Pass B repeats that pixel along the direction with fading, fibre-like streaks, edge flare and grain.

**Input:** `in1` TOP (default internal moving silhouette). **Output:** `out1`.

| Param | Meaning |
|---|---|
| Direction | down / up / left / right (smear direction) |
| Threshold | luminance crossing level |
| Animate | loop-periodic sinusoidal threshold modulation |
| Invert | cross when darker than threshold instead |
| Length | smear length (fraction of frame) |
| Noise | per-column threshold noise |
| Streak | per-fibre length variation |
| Grain | film grain |
| Bandwidth | stripe quantization in px |
| Revert | brightness of the un-smeared image |
| Mix | blend with input |

**Loop page** (all components): `Timesource` (`abstime` | `phase`), `Phase` (0-1), `Loopseconds`, `Loopbeats` (0 = use seconds, else beats at `Bpm`), `Bpm`. In `phase` mode, every motion is a function of `Phase` only; abstime mode just advances the same phase at 1/loop-duration.

**Loop:** threshold anim = sin(2*pi*Phase); threshold noise on a circular noise path; grain seed = `floor(Phase*24) mod 24`.


## v2 interface
| Connector | Type | Label / use |
|---|---|---|
| in1 | In TOP | image (default animated silhouette if unconnected) |
| in2 | In CHOP | optional modulation (band1..band4, beat, phase) |
| out1 | Out TOP | result |

New common parameters: `Mix` (dry/wet vs in1), `Bypass` (passes in1 straight through), `Resolutionmode` (`input` follows in1 / default source, `custom` uses `Resolutionw/h`), `Clock` (Loop page: CHOP whose `phase` channel drives the loop when Timesource=phase), `Modamount` (scales the modulation input).

Modulation: `band1` scales `Length` by `1+Modamount*band1`. The old `Mix` is now the common Mix; the 2048x1 map stage keeps its fixed size.
