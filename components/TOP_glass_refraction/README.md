# TOP_glass_refraction
Raymarched moving glass shape (morphing blob/cube, torus, rounded cube) refracting `in1` (default: internal bone-white bars/grid + red dot) with per-channel IOR dispersion, frost blur, thickness absorption and specular/fresnel/curvature glints.

**Input:** `in1` TOP (background). **Output:** `out1`.

| Param | Meaning |
|---|---|
| Shape | Morph / Torus / Rounded cube |
| Ior | base index of refraction (bend strength) |
| Dispersion | per-channel IOR spread (chromatic fringes) |
| Frost | blur of refracted background |
| Size, Spin (turns/cycle), Morphspeed (cycles/cycle) | shape animation |
| Highlights | specular + fresnel + glint gain |
| Absorption | thickness-based tint |
| Camdistance, Bgscale | camera / background mapping scale |
| Resolution | output size |


Refraction is a screen-space bend using the surface normal and an inner-ray thickness march (stable, not a full ray-trace of the back face).


## v2 interface
| Connector | Type | Label / use |
|---|---|---|
| in1 | In TOP | background image (default bars/grid if unconnected) |
| in2 | In CHOP | optional modulation (band1..band4, beat) |
| out1 | Out TOP | result |

New common parameters: `Mix` (dry/wet vs in1), `Bypass` (passes in1 straight through), `Resolutionmode` (`input` follows in1 / default source, `custom` uses `Resolutionw/h`), `Modamount` (scales the modulation input).

Modulation: `band1` adds `Modamount*band1*0.5` to `Ior`. Output size is Resolutionmode/Resolutionw/h (the old Resolution par is now in Controls).

## Demo source
The built-in preview source lives in a `demo` Base COMP behind a Switch: it is selected only while `in1` is unconnected, so with an input connected it does not cook. There is no Loop page; animation uses absolute time and only exists to make the unconnected preview move.


## Implementation
**Native now:** the preview source in the `demo` COMP: an 8 x 14 random cell Noise TOP + Threshold TOP gives the bars, Ramp + Threshold TOPs cut them to length and into rows, a **Displace TOP** driven by a 14-value Constant CHOP (CHOP to TOP, nearest Resolution TOP) scrolls every row at its own whole-cycle speed (it loops every 8 s), more Ramp / Threshold TOPs draw the fine grid, and Circle TOPs make the red dot and ring that orbit; Composite TOPs merge everything. A Switch TOP (`src`) selects it only while `in1` is unconnected.

**GLSL kept:** `glass.glsl`, one pass that raymarches the signed-distance shape (morph / torus / rounded cube), refracts the background per colour channel through the surface normal and the thickness, adds frost, absorption and highlights. Why: a native version was built and benchmarked (about +970 % at 720p, +1290 % at 1080p, far over the 20 % GPU budget). It is saved as `build_native.py` so it can be rebuilt and studied; it is not the shipped component.

The native version (`build_native.py`), for reference:
- **Shape height:** Rectangle / Circle TOPs in pixels (the morph is one rounded Rectangle whose half-size and corner radius slide from sphere to cube; the torus is an outer minus an inner Circle TOP; a Switch TOP picks the `Shape`), a Transform TOP spins it, a Blur TOP turns the mask into a rounded height, a Level TOP shapes the profile.
- **Normal Map TOP** from that height, a Channel Mix TOP unpacks it to -1..1.
- **Refraction and dispersion:** thickness (Math TOP) sets the bend strength; the normals times the strength drive three **Displace TOPs** (one per colour channel, each with the weight `(1/ior_c - 1)` from `Ior` +/- `Dispersion`); a **Reorder TOP** takes R, G and B from them.
- **Frost:** Blur TOP (behind a Switch so it does not cook at `Frost` 0). **Absorption:** Channel Mix TOP per-channel tint from the thickness, Composite `multiply`.
- **Highlights:** Channel Mix dot products of the normals with the two half vectors and the fresnel term, Level TOP power curves, Composite `add`.
- Composite `over` puts the glass (masked by a Threshold TOP of the height) onto the untouched background.

Bench of the shipped component (GPU, interleaved medians, noisy because other TouchDesigner instances were running): 720p 1.70 -> 1.25 ms (-26 %), 1080p 2.23 -> 1.84 ms (-18 %): same shader, noise only (native variant: +972 % / +1291 %)
