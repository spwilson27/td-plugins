# TOP_video_synth
LZX / Hydra style oscillator patching that **modulates the input image**: three cross-modulating oscillators displace, colorise, kaleidoscope, echo and key/mix the picture on in1.
(Library name `TOP_video_synth`, formerly `GEN_video_synth`. Shipped as `tox/TOP/TOP_video_synth.tox`.)

## Inputs
| Input | Type / purpose |
|---|---|
| in1 | image (In TOP). Unconnected: an internal demo picture (inside `demo`, only cooks when nothing is connected) |
| in2 | modulation CHOP (optional): `band1` scales Displace, `band2` oscillator frequency, `band3` Feedback, `beat` kicks the hue |

## Outputs
| Output | Label / content |
|---|---|
| out1 | patched image (rgba16float) |

Chain: global rotate -> kaleid fold -> osc A -> (A bends B) -> osc B -> (B bends C) -> osc C. The oscillators (1) displace the input coordinates (Displace, with RGB split via Colorize), (2) rotate its hue (Colorize, Hue), (3) form a palette pattern combined with the picture by Mixmode, then a spatial zoom/rotate echo (Feedback) is max-blended. No Feedback TOP and no state.

| Page | Param | Meaning |
|---|---|---|
| Controls | Preset | Custom or preset (Bone Waves, Chrome Moire, Red Kaleid, Acid Displace, Luma Key, Tunnel Echo); choosing one writes the other params, tweak freely |
| | Mixmode, Pattern, Keylevel | blend / luma key / multiply / difference of the oscillator pattern with the picture; pattern strength; key threshold |
| | Displace, Colorize, Hue | input displacement, hue rotation / RGB split, hue offset |
| | Kaleid, Scale, Rotspeed | mirror segments (0/1 = off), global frequency scale, rotation deg/s |
| | Palette, Contrast, Gamma | pattern look (bone, chrome, red, rainbow, acid) |
| | Mix, Bypass, Resolutionmode, Resolution | standard TOP controls |
| Oscillators | Freq / Speed / Rot / Shape a,b,c | spatial frequency, drift speed (cycles/s), rotation, sine/square/saw; Modulate = cross-modulation |
| Echo | Feedback, Echozoom, Echorot, Echospacing | 6-tap echo strength, zoom and rotation per tap, time offset per tap (s) |

No Loop page: time (absTime) only drives oscillator drift.

## Implementation
- **Demo picture (native):** inside `demo`: a circular Ramp TOP (cosine rainbow rings, colours from a Table DAT) -> horizontal Ramp TOP (bar pattern, multiply) -> vertical Ramp TOP (thin bone-white lines, over) -> Circle TOP (drifting orange disc, over). The demo does not cook while `in1` is connected.
- **Synth (GLSL, kept):** one `synth` GLSL TOP does everything for the effect. The patch is one *function* (`scene()`: rotate, kaleid fold, three cross-modulated oscillators with sine/square/saw shapes, palette, displaced + hue-rotated input, four mix modes) that the echo evaluates 7 times at different time offsets and zoom/rotation per tap. Natively that is three oscillators (Ramp/Noise + shape lookup), two Displace stages for the cross-modulation, Displace + RGB split, HSV, palette Lookup, four mix modes, and six time-offset echo taps (Cache/Time Machine plus Transform per tap): roughly 30+ full-frame passes, rebuilt for every echo tap or replaced by a stateful feedback echo that no longer matches the stateless, time-offset look. In the trails experiment on this machine each extra full-frame TOP cost 0.03-0.1 ms at 1280x720, against about 0.3 ms for this whole component, so a native version is expected to be several times slower; it was not built. Per the rule (native only where it does not cost more than 20 % GPU) the effect stays GLSL.
- **Bench (old vs new, median GPU ms, interleaved):** 1280x720 0.58 -> 0.54 (-6 %), 1920x1080 0.85 -> 0.90 (+6 %): unchanged shader, run-to-run noise only.
