# GEN_sdf_raymarch
Raymarched SDF scene in a single GLSL TOP (no inputs needed). Two primitives (A and B) orbit each other and are combined with a smooth operator; optional domain repetition; checker floor when not repeating.
- Output: `out1` TOP (Resolution, default 1280x720). Input: none.
- **Controls**: Resolution, Active, Speed, Shape1/Shape2 (sphere, box, torus, capsule, gyroid), Combine (smooth union/subtract/intersect), K (smoothness), Scale, Repeat + Repeatsize (domain repetition), Thickness (gyroid), Palette (rainbow/sunset/ocean/neon/mono), Hue, Steps (max march steps).
- **Camera**: Orbitspeed, Orbitangle, Distance, Height, Fov.
- **Light**: Lightazimuth, Lightelevation, Shadowsoft (shadow hardness), Ao, Fog, Fogcolor.
- Tips: lower Steps for repeated gyroids on weak GPUs; large K with gyroid blends nicely.

## Loop & Look (batch-2 retrofit)

### Loop page
| Param | Meaning |
|---|---|
| Timesource | `abstime` (free-running, original behaviour) or `phase` (motion is a function of `Phase`) |
| Phase | 0-1 loop phase, drive externally (LFO / timeline / beat clock) in `phase` mode |
| Loopseconds | loop length used when Timesource=abstime-derived clocks are needed (default 8 s) |
| Loopbeats / Bpm | if Loopbeats > 0 the loop length is Loopbeats*60/Bpm seconds instead of Loopseconds |

**How the loop works:** Phase mode: shape motion uses integer harmonics of 2*pi*Phase (Speed rounds to whole cycles per loop, min 1; Speed 0 or Active off = static), camera orbit makes an integer number of turns per loop (rate matched to Orbitspeed*looplength, min 1; 0 if Orbitspeed=0). Phase 0 vs 0.9999 differ by ~0.0002 mean abs.

### Look page
`Look` = `Original` (default, unchanged) or `Mono` (black background, bone-white / grey, rendah style). `Accent` (0-1) adds red accents in Mono (the smaller shape / its highlight blends toward red).

## v2 update

Renamed from `sdf_raymarch` to `GEN_sdf_raymarch` (tox at `tox/GEN/GEN_sdf_raymarch.tox`; no per-frame keepalive: outputs are pulled by downstream ops).

**Inputs**: in1 (CHOP, optional modulation). The modulation In CHOP is always the last input and reads channels `band1`-`band4`, `beat`, `phase`; missing channels are ignored. Used here: band1: Smooth K +0.3b, beat: Scale x(1+0.25b).

| Output | Label |
|---|---|
| out1 | render |

**Loop page**: new `Clock` CHOP parameter. With `Timesource` = `phase` the phase is read from the `phase` channel of that CHOP (instead of `Phase`). Snippets: `snippets/GEN_sdf_raymarch.tox` (About > Snippets).
