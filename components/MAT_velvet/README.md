# MAT_velvet
Velvet / fuzz material: Charlie (Estevez-Kulla) sheen lobe with Neubelt visibility, forward-scatter darkening, rim fuzz, brushed pile patches and fiber noise. **Mode** menu: `sheen` (single pass) or `shells` (shell fur).

Material is a GLSL MAT at `<comp>/mat`; it needs **no UVs** (object-space position `oP`, normals required), is self-lit by a procedural studio environment (key/fill/rim lobes, rotate/scale with Envrot/Envint; no Light COMP needed) and outputs HDR-linear colour. To use on your own geometry, point the Geometry COMP Material parameter at `op(".../mat")` (keep the whole COMP: the MAT uniforms are bound by expressions to the COMP parameters via `parent().par`). Preview page: Resolution, Exposure, Bloom, Spinturns, Tilt, Camdist, Backdrop. Loop page: Timesource (abstime/phase), Phase, Loopseconds, Loopbeats, Bpm, Speed. `out1` = tonemapped preview of a rotating sphere + torus knot (works with no inputs).

## Shell fur mode
N shells are drawn by **instancing** the geometry (Geometry COMP: Instancing on, count mode manual, `Instance Count = Shells`); the vertex shader reads `TDInstanceID()` and offsets each shell along its normal by `shell/(N-1) * Furlength`. The pixel shader keeps a pixel only inside a jittered strand cell (cells chosen on the dominant object axis, tapered radius, per-strand length via a hash = noise alpha cutoff). The preview geometry sets `numinstances` from the Mode/Shells parameters automatically (1 in sheen mode). On your own geometry you must enable instancing with Shells instances yourself when using shell mode.

| Par | Meaning |
|---|---|
| Mode | sheen / shells |
| Basecolor, Sheencolor | pile colour / sheen tint |
| Fuzz | sheen lobe roughness (lower = tighter, more satin) |
| Sheen, Rimfuzz | sheen lobe gain / grazing-angle halo |
| Fiber, Pilepatches | micro fiber noise / large crushed-pile patches |
| Shells, Furlength, Density, Strandwidth, Rootdark | shell-fur controls (object units) |
| Envrot, Envint | studio env |

Loop: only the preview spin is time-based (rotation = 360 * Spinturns * phase), so it is seamless at phase 0 == 1.

## Inputs and outputs (v2)
| Connector | Type | Use |
|---|---|---|
| in1 | CHOP, optional | modulation: channels band1-band4, beat, phase (missing channels read as 0). band1 adds to Sheen strength, band2 to Rimfuzz. Scaled by `Modamount`. |

| Output | Type | Label / content |
|---|---|---|
| out1 | TOP | preview render (sphere + torus knot/torus, tonemapped) |

The material itself is `MAT_velvet/mat` (GLSL MAT). Assign it to your Geometry COMP with `op('MAT_velvet/mat')`.

## v2 parameters
- **Material > Modamount**: scales the modulation CHOP.
- **Loop > Clock**: optional CHOP; when set and `Timesource` = `phase`, the loop phase is read from its `phase` channel instead of `Phase`.

## Snippets
`snippets/MAT_velvet.tox` (About > Snippets): 3 examples, each applying `MAT_velvet/mat` to a Geometry COMP with Camera, Light and Render TOP, plus parameter recipes and CHOP modulation.
