# TOP_tracker_hud
"Tracking data" HUD overlay on `in1` (default: internal moving silhouette). A GLSL pass picks N stable feature points (random-but-stable candidates accepted where blurred luminance > Threshold, then hill-climbed to the local brightness maximum, with periodic jitter) into a 64x1 float texture; everything that is drawn (grid, crosses, edge ticks, boxes, connecting lines, labels, scanlines) is built from native nodes, see Implementation.

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
| Refresh | re-seed point selection N times per 8 s cycle (0 = never) |
| Jitter | periodic jitter amount |
| Dim | input brightness under the HUD |
| Scanlines | scanline strength |
| Modamount | how strongly the mod CHOP moves Jitter / Boxsize |
| Mix | dry/wet vs in1 (common) |
| Bypass | pass in1 straight through (common) |
| Resolutionmode | `input` follows in1 (else Resolution); `custom` uses Resolution (common) |


Limitations: points are re-detected every frame against the live image, so they can hop when content crosses Threshold; dense Points + `both` labels will overlap.

## Implementation
Built from built-in nodes; follow the wires left to right.
- **Feature points (GLSL, `points`)**: `pts.glsl` writes 64 points (x, y, id, valid) into a 64x1 float texture: hashed candidates, a luminance test and a small hill climb. It stays GLSL (a per-point search with a random pattern); the Blob Track TOP exists but finds blobs, not these stable bright-feature points, and has no matching Threshold / Refresh / Jitter behaviour.
- **Points as geometry**: a TOP to POP (`points_pop`) turns the texture into 64 POP points; `hud_points` (Math Combine POP) converts them to pixel positions from the image centre, the point number, the box scale and the connection partner (k x 5 + 3) mod N; `partner` (Lookup Attribute POP) fetches the partner's position and validity; `hud_lines` computes each line's length and angle.
- **Drawing**: one Render TOP with an orthographic camera in pixel units draws, additively on black: `geo_image` (the input as a pixel-exact textured quad, brightness = Dim), `geo_grid` (Grid POP lines), `geo_cross_h/_v` (instanced from the grid nodes), `geo_ticks_*` (instanced ticks along the left and bottom edges), `geo_links` (a Line SOP instanced per point with the length/angle from the POP), `geo_boxes` (a Rectangle SOP in wireframe, instanced and scaled by Boxsize with the point's validity) and `geo_labels`.
- **Labels**: `glyph_slots` (Grid POP, 17 columns x 2 lines) is copied onto every point by a Copy POP; Math Combine POPs derive for each glyph the digit to show (ID digits, or the "%7.2f / %7.2f" coordinate digits with leading blanks), whether the current Labelmode shows it and its position; a Geometry COMP instances a quad per glyph and picks one of twelve Text TOPs (`glyph_0` ... `glyph_11`, the digits, '.' and '/') per instance. The text uses the Menlo font instead of the old 5x7 pixel font.
- **Scanlines**: a 1x2 pixel Ramp TOP (strength from Level TOP) is tiled over the image by a Tile TOP (static texture) and multiplied by a Composite TOP.
- **Demo source** (inside `demo`): Circle TOPs (blob field as Ramp TOPs scaled by Transform TOPs, summed and passed through a Lookup TOP for silhouette and contour), Noise TOPs for the background and the blob texture, rings (Circle TOPs) and rotating bars (Rectangle TOPs).
- GLSL kept: `pts.glsl` only.

Benchmark (tools/bench.py, interleaved medians, default settings; GPU ms old -> new): 1280x720 0.30 -> 0.33-0.35 (+9 to +12 %); 1920x1080 0.58 -> 0.49-0.52 (-10 to -17 %). Using the Render TOP for the image as well (instead of separate Level and Add passes) and 2x antialiasing brought the 720p cost from +25 % to +10 %.

## Demo source
The built-in preview source lives in a `demo` Base COMP behind a Switch: it is selected only while `in1` is unconnected, so with an input connected it does not cook. There is no Loop page; animation uses absolute time and only exists to make the unconnected preview move.
