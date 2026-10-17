# TOP_glitch

Datamosh / glitch processor for an image. One GLSL pass (`glitch.glsl`) with a feedback loop (for the compression smear). Glitch events are quantised to "beats" (`Rate` per second, re-rolled with `Seed`).

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


## Implementation
**Native now:** the preview source in the `demo` COMP (a Noise TOP plus Ramp / Threshold / Composite TOPs for the dark checker, a Rectangle TOP bar and five Circle TOP discs with bright cores, all driven by absolute time and the Look / Accent parameters, merged with Composite TOPs). The `src` Switch TOP picks it only while `in1` is unconnected. Feedback loop: Feedback TOP -> `glitch` -> Null TOP `fb_out` -> back into the Feedback TOP.

**GLSL kept:** `glitch.glsl`, one pass doing block displacement, scanline tear, RGB split, the pixel-sort streaks and the compression hold. Why: a fully native version was built and benchmarked and is far over the 20 % GPU budget (about +300 % at 720p and 1080p): every full-screen native pass costs a fixed ~0.02-0.03 ms, and the native effect needs about ten of them. It is saved as `build_native.py` (plus `streak.glsl`, the small GLSL core it keeps for the pixel-sort streaks) so you can rebuild and study it; it is not the shipped component.

How the native version is wired (`build_native.py`), for reference:
- **events** Constant CHOP: per-beat random values (`tdu.rand(beat)`) for grid sizes, tear rows, split angle, keyframe flag and noise seeds; `beat = floor(time * Rate) + Seed`, `env` decays after each beat.
- **Block displacement:** low-resolution Noise TOP (type `randomgpu`, one texel per block, size re-rolled per beat) picks an x/y offset per block; a second Noise TOP + Threshold TOP chooses which blocks move; a Resolution TOP with nearest filtering blows the maps up to full size; a **Displace TOP** shifts the image.
- **Scanline tear:** the same idea with a 2 x rows Noise TOP (one random value per row) + Threshold TOP, plus a Rectangle TOP band for the rolling tear, summed with a Composite TOP and fed to a second Displace TOP (x only).
- **RGB split:** two Transform TOPs shift a copy by +/- the split vector; a **Reorder TOP** takes R from one, G from the unshifted image and B from the other.
- **Compression hold:** Resolution TOPs (nearest) shrink the current frame and the Feedback TOP to one texel per block; Composite `difference` + Math TOP `len` + Level TOP turn the change into a hold amount; a Reorder TOP puts it into the alpha of the previous output and a Composite `over` keeps the previous pixels where the blocks barely changed.
- Pixel-sort streaks: small GLSL TOP (`streak.glsl`); `TOP_pixel_sort` is the real sorter if you need one.
- Each stage sits behind a Switch TOP so a stage with strength 0 does not cook.

Bench of the shipped component (GPU, interleaved medians, noisy because other TouchDesigner instances were running): 720p 1.08 -> 0.84 ms (-22 %), 1080p 1.30 -> 1.30 ms (-0.2 %): same shader, the difference is measurement noise (native variant: +327 % / +299 %)
