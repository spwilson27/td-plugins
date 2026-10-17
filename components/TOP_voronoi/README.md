# GEN_voronoi
Animated Voronoi cells in GLSL (up to 128 seeds wandering on sine "noise" paths).
- Input: `in1` TOP (optional; used by stained glass / cracked glass / glow tint; default animated noise). Output: `out1`.
- **Controls**: Resolution, Active, Mode (flat cells, edge glow, cracked glass, stained glass), Seeds, Speed, Motion (wander amount), Jitter (0 = grid layout, 1 = random), Borderwidth (px), Glow, Delaunay overlay + Linewidth, Palette, Hue, Seed.
- Delaunay overlay draws the Gabriel-graph edges (a subset of Delaunay edges, computed in a small adjacency pass `adj`).

## Loop & Look (batch-2 retrofit)

### Loop page
| Param | Meaning |
|---|---|
| Timesource | `abstime` (free-running, original behaviour) or `phase` (motion is a function of `Phase`) |
| Phase | 0-1 loop phase, drive externally (LFO / timeline / beat clock) in `phase` mode |
| Loopseconds | loop length used when Timesource=abstime-derived clocks are needed (default 8 s) |
| Loopbeats / Bpm | if Loopbeats > 0 the loop length is Loopbeats*60/Bpm seconds instead of Loopseconds |

**How the loop works:** Phase mode: seed wander frequencies snap to integer harmonics of 2*pi*Phase (Speed rounds to whole cycles, min 1), the default noise source uses perlin4d on a circle, edge-glow palette drift uses sin(). Phase 0 vs 0.9999: ~0.001.

### Look page
`Look` = `Original` (default, unchanged) or `Mono` (black background, bone-white / grey, rendah style). `Accent` (0-1) adds red accents in Mono (a fraction of cells / edges glow red).

## v2 update

Renamed from `voronoi` to `GEN_voronoi` (tox at `tox/GEN/GEN_voronoi.tox`; no per-frame keepalive: outputs are pulled by downstream ops).

**Inputs**: in1 (TOP, optional colour source), in2 (CHOP, optional modulation). The modulation In CHOP is always the last input and reads channels `band1`-`band4`, `beat`, `phase`; missing channels are ignored. Used here: band1: Motion x(1+b), beat: Glow x(1+b).

| Output | Label |
|---|---|
| out1 | render |

**Loop page**: new `Clock` CHOP parameter. With `Timesource` = `phase` the phase is read from the `phase` channel of that CHOP (instead of `Phase`). Snippets: `snippets/GEN_voronoi.tox` (About > Snippets).
