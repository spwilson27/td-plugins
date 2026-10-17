# TOP_glass_refraction
Raymarched moving glass shape (morphing blob/cube, torus, rounded cube) refracting `in1` (default: internal bone-white bars/grid + red dot) with per-channel IOR dispersion, frost blur, thickness absorption and specular/fresnel/curvature glints.

**Input:** `in1` TOP (background). **Output:** `out1`.

| Param | Meaning |
|---|---|
| Shape | Morph / Torus / Rounded cube |
| Ior | base index of refraction (bend strength) |
| Dispersion | per-channel IOR spread (chromatic fringes) |
| Frost | blur of refracted background |
| Size, Spin (turns/loop), Morphspeed (cycles/loop) | shape animation |
| Highlights | specular + fresnel + glint gain |
| Absorption | thickness-based tint |
| Camdistance, Bgscale | camera / background mapping scale |
| Resolution | output size |

**Loop page** (all components): `Timesource` (`abstime` | `phase`), `Phase` (0-1), `Loopseconds`, `Loopbeats` (0 = use seconds, else beats at `Bpm`), `Bpm`. In `phase` mode, every motion is a function of `Phase` only; abstime mode just advances the same phase at 1/loop-duration.

Refraction is a screen-space bend using the surface normal and an inner-ray thickness march (stable, not a full ray-trace of the back face). **Loop:** all shape motion and the default background are periodic in Phase (background scrolls whole 8-cell periods per loop).


## v2 interface
| Connector | Type | Label / use |
|---|---|---|
| in1 | In TOP | background image (default bars/grid if unconnected) |
| in2 | In CHOP | optional modulation (band1..band4, beat, phase) |
| out1 | Out TOP | result |

New common parameters: `Mix` (dry/wet vs in1), `Bypass` (passes in1 straight through), `Resolutionmode` (`input` follows in1 / default source, `custom` uses `Resolutionw/h`), `Clock` (Loop page: CHOP whose `phase` channel drives the loop when Timesource=phase), `Modamount` (scales the modulation input).

Modulation: `band1` adds `Modamount*band1*0.5` to `Ior`. Output size is Resolutionmode/Resolutionw/h (the old Resolution par is now in Controls).
