# MAT_hologram_scan

Holographic scan material. Wire lines, scanline sweep, random data dropout blocks, depth-coded colour, additive (or alpha) blending. Pairs well with point-cloud / wire looks on a black background.

* **MAT**: `MAT_hologram_scan/mat` (GLSL MAT, GLSL 4.30). Assign it to any Geometry COMP's `Material` (`op('.../mat')`). No UVs required for the default wire mode.
* **out1**: the material (Out MAT); internal `preview` TOP (not an output) = preview render (sphere + torus, slowly rotating, dark backdrop). Needs no input.
* macOS has no geometry shaders, so wire lines are derivative-based (constant pixel width via `fwidth`).

## Material page (uniforms `uA..uF`, `uNear`, `uFar`, `uScanCol`)
| Par | Meaning |
|---|---|
| Colornear / Colorfar | depth-coded colour (camera distance Depthnear..Depthfar) |
| Scancolor | colour of the sweeping band |
| Wirewidth, Wirebright, Fill | wire thickness (px), brightness, faint surface fill |
| Wiremode | `objectgrid` (object-space lattice, any mesh), `uvgrid` (iso-lines of UV; equals mesh edges on parametric shapes, needs UVs), `both` |
| Gridcells, Griduv | lattice cells per unit / UV cell counts |
| Creases | extra lines on normal discontinuities + silhouettes |
| Fresnelpower/amount | rim glow |
| Scansweeps, Scanscale, Scansharp, Scanstrength | world-Y sweeping band: sweeps per preview cycle, spatial scale, falloff, intensity |
| Scanlinepx, Scanlineamount | fine screen-space scanlines |
| Dropamount, Dropblock, Droprate, Flicker | blocks of `gl_FragCoord` (px) discarded and re-rolled `Droprate` times/sec, row bursts, global brightness flicker |
| Blend | `additive` (one/one) or `transparent` (srcalpha/invsrcalpha) |
| Backfaces | draw back faces (see-through hologram) |

## Preview page
Resolution, Turns (integer rotations per preview cycle), Background, Camdistance, Showsphere, Showtorus.

## Animation
Scan sweeps, dropout and flicker run from absolute time (preview cycle 8 s); there is no Loop page.

## Tips
Set Depthnear/Depthfar to bracket your camera-to-object distance. Using on other cameras works (camera position comes from `uTDMats`). Lower Dropblock for finer glitching.

## Inputs and outputs (v2)
| Connector | Type | Use |
|---|---|---|
| in1 | CHOP, optional | modulation: channels band1-band4, beat (missing channels read as 0). band1 adds to Scanstrength, beat adds to Flicker. Scaled by `Modamount`. |

| Output | Type | Label / content |
|---|---|---|
| out1 | MAT | material (the `mat` GLSL MAT); the preview render is the internal `preview` TOP |

The material itself is `MAT_hologram_scan/mat` (GLSL MAT). Assign it to your Geometry COMP with `op('MAT_hologram_scan/mat')`.

## v2 parameters
- **Material > Modamount**: scales the modulation CHOP.

## Snippets
`snippets/MAT_hologram_scan.tox` (About > Snippets): 3 examples, each applying `MAT_hologram_scan/mat` to a Geometry COMP with Camera, Light and Render TOP, plus parameter recipes and CHOP modulation.
