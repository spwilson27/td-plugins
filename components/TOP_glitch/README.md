# TOP_glitch

Datamosh / glitch processor for an image. A single GLSL pass with a feedback loop (for the compression smear). Glitch events are quantised to "beats" (`Rate` per second, re-rolled with `Seed`).

## Inputs
| In | Label | Notes |
|---|---|---|
| in1 | image | the image to glitch |
| in2 | modulation CHOP | optional, last input: `band1` and `beat` add to `Amount` (x1 + band1 + beat) |

With nothing connected, an animated demo source (inside the `demo` COMP) feeds the effect so the node viewer shows a preview. When `in1` is connected the demo is switched out and does not cook.

## Outputs
| Out | Label |
|---|---|
| out1 | result |

## Parameters
| Par | Meaning |
|---|---|
| Amount | global multiplier for all sub-effects |
| Seed / Rate | random seed; beats per second at which blocks, tears and sorts re-roll |
| Rgbsplit | chromatic channel split along a per-beat random direction |
| Blockdisplace | random blocks (grid size re-rolled per beat) shifted sideways |
| Scanlinetear | horizontal per-row tearing plus a rolling tear band |
| Pixelsort / Sortthreshold / Sortaxis | approximate GPU sort: runs of pixels above the threshold along the axis become streaks |
| Smear / Smearthreshold / Smearblock | fake compression hold: blocks that barely changed keep the previous frame's pixels, with occasional keyframe refreshes |
| Active | off = freeze the feedback |
| Reset | pulse: reload the feedback from the current input |
| Mix | dry/wet against the input |
| Bypass | pass in1 straight through |
| Resolutionmode / Resolution | `input` follows in1 (or the demo source when unconnected); `custom` uses Resolution |
| Look / Accent | `mono` recolours only the demo source (black / bone-white, optional red accent); a connected input is not recoloured |

## Notes
- The pixel sort is a streak approximation (up to 48 steps x 3 px), not a true sort; see `TOP_pixel_sort` for a real one.
- Animation runs on absolute time; there are no loop parameters.
