# POP_tentacles
Grow writhing tubes from the input points. POP in, POP out: one tentacle grows from every point of `in1`, away from the origin. Shipped as `tox/POP/POP_tentacles.tox`. (Formerly `GEN_tentacles`.)

## Inputs
| Input | Type / purpose |
|---|---|
| in1 | In POP: points (any POP; only its points are used, one tentacle each). With nothing connected a built-in sphere of points (in the gated `demo` COMP) is used. |
| in2 | In CHOP (optional) modulation: `band1`..`band4`, `beat`. band1 = writhing, band2 = wave, band3 = pulse, band4 = length, beat = thickness swell. |

## Outputs
| Output | Label / content |
|---|---|
| out1 | tube mesh (POP): all tentacles, with normals |

The node viewer shows the internal `preview` TOP (a small PBR render of out1, not an output). Render out1 yourself with a Geometry COMP (Select POP) + Render TOP.

## Technique
Each input point becomes a tentacle. The heavy arithmetic is done once per ring on a spine of `Segments` points (not once per tube vertex), and the tube vertices then fetch their ring from that table. Cost scales with points x Segments x Sides: thin the input points for a lighter mesh. See "Implementation" below.

| Page | Params |
|---|---|
| Controls | Length, Grow, Autogrow, Speed, Seed, Segments, Sides, Thickness, Taper, Tipmin, Wiggle, Noisefreq, Wave, Wavefreq, Pulse, Pulsefreq |
| Look | Resolution, Metallic, Roughness, Basecolor, Envintensity, Redaccent, Camdist, Camheight, Bgcolor (preview render only) |

Motion uses absolute time scaled by `Speed`; Autogrow grows and retracts the tentacles continuously.

## Implementation
No GLSL: the whole tentacle is native POPs.
- `rootattr` (Math Combine) stores each input point in the attribute `Root`. `spine_line` (Line POP, `Segments` points) + `spine_copies` (Copy POP) give every root its own straight spine; `tube` (Tube POP) + `tube_copies` (Copy POP, with the template id `tid` = which tentacle) give every root a straight tube mesh.
- `tentacle_setup` (Math Combine): u = 0..1 along the tentacle (and u a little before/after, to find the spine direction), growth direction = normalized root, a ring frame (two perpendicular directions), and a lookup coordinate for the seed.
- `seed_noise` (Noise POP, looked up at the root position) gives every tentacle its own 0..1 seed (changes with `Seed`); `writhe_coords` (Math Combine) builds the noise lookup coordinates along the tentacle, travelling through noise space; `writhe_noise_a` / `writhe_noise_b` (Noise POPs, 3-component simplex noise) sample it just before and just after each spine point.
- `spine_table` (Math Combine, the long list of steps, commented in build.py): spine = root + direction * length * u + writhing (grows smoothly from the root) + travelling sideways sway; evaluated at u-0.01 and u+0.01, the ring centre is their midpoint and the ring plane is perpendicular to their difference (so tubes keep round cross-sections as they curl). Radius = Thickness * (1-u)^Taper + Tipmin part, with travelling thickness pulses and the beat swell, zero while retracted. It writes `centre`, `nn`, `bb` (ring frame) and `ringr` (radius) for every spine point.
- `tube_index` (Math Combine) works out which spine point each tube vertex belongs to (`tid * Segments + ring`), `ring_lookup` (Lookup Attribute POP) fetches centre/nn/bb/radius from the spine table, and `tentacle` (Math Combine) places the vertex: centre + (nn * x + bb * z) * 2 * radius. `tubes` (Normal POP) rebuilds normals. Band/beat modulation is wired into the constants as before.

Why a table: evaluating the spine once per tube vertex (12 vertices per ring by default) was 25-35 % slower than the old shader; doing it once per ring and looking it up makes the per-vertex work a few steps.

Differences from the old shader: the writhing noise is Simplex (Noise POP) instead of hand-rolled value noise, and the per-tentacle seed comes from a noise lookup, so individual tentacles do not look identical to the old ones; the spine direction is found by evaluating the spine on both sides of each ring (midpoint and difference) rather than three times with a centre sample. The preview's `envmap` (shared studio-chrome texture) is still a GLSL TOP.


Bench (`tools/bench.py`, 200x200 grid of roots = 40,000 tentacles, GPU ms, median of 9 interleaved runs; heavy by design and the machine was loaded by other jobs):
| Size | old GLSL | native | change |
|---|---|---|---|
| 1280x720 | 656 | 714 | +8.8 % |
| 1920x1080 | 646 | 741 | +14.6 % |
