# TOP_tracker_hud
"Tracking data" HUD overlay on `in1` (default: internal moving silhouette). Two GPU passes: (A) a 64x1 float texture picks N stable feature points (random-but-stable candidates accepted where blurred luminance > Threshold, then hill-climbed to the local brightness maximum, with periodic jitter); (B) one full-res shader draws grid + crosses + edge ticks, square boxes, connecting lines and labels using a built-in procedural 5x7 pixel font (no per-frame Python, no atlas, no extra ops), plus scanlines.

| Input | Type | Notes |
|---|---|---|
| in1 | TOP | image to annotate (optional; animated silhouette when unconnected) |
| in2 | CHOP | optional modulation: `band1` -> Jitter, `band2` -> Boxsize (scaled by Modamount) |

| Output | Label |
|---|---|
| out1 | result (image + HUD) |


| Param | Meaning |
|---|---|
| Points | feature points (1-64) |
| Labelmode | id (5-digit) / coords (`104.42 /  582.88`) / both |
| Labelcolor | red or white (boxes/lines/grid stay bone-white) |
| Fontsize | label height in px (steps in multiples of 7) |
| Boxsize | box size px |
| Linecount | number of connecting lines |
| Gridsize | grid spacing px |
| Threshold | luminance needed to accept a point |
| Refresh | re-seed point selection N times per loop (0 = never) |
| Jitter | periodic jitter amount |
| Dim | input brightness under the HUD |
| Scanlines | scanline strength |
| Modamount | how strongly the mod CHOP moves Jitter / Boxsize |
| Mix | dry/wet vs in1 (common) |
| Bypass | pass in1 straight through (common) |
| Resolutionmode | `input` follows in1 (else Resolution); `custom` uses Resolution (common) |

**Loop page** (all components): `Timesource` (`abstime` | `phase`), `Phase` (0-1), `Loopseconds`, `Loopbeats` (0 = use seconds, else beats at `Bpm`), `Bpm`, plus `Clock` (CHOP; when set and Timesource=phase, phase is read from its `phase` channel). In `phase` mode, every motion is a function of `Phase` only; abstime mode just advances the same phase at 1/loop-duration.

**Loop:** point re-seed epoch = `floor(Phase*Refresh) mod Refresh`, jitter = sin/cos(2*pi*Phase*k). Limitations: points are re-detected every frame against the live image, so they can hop when content crosses Threshold; dense Points + `both` labels will overlap.
