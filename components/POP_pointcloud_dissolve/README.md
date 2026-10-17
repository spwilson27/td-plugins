# POP_pointcloud_dissolve
Mesh (sphere / torus / head-ish blob) or an `in1` depth/luma TOP turned into a fine white/grey point cloud (POP + point sprites, additive, faint glow). A moving threshold (plane / orbiting sphere / radial) erodes the points; eroded points scatter with curl-noise + random dust and fade, then re-form.


| Page | Params |
|---|---|
| Controls | Resolution, Source, Density, Dissolve (0-1 manual), Auto (+Autocycles, Automax cap), Wavemode, Axisx/y/z (plane/radial axis), Edgewidth, Scatter, Jitter (ragged edge), Drift, Noisefreq, Noisecycles, Depth, Invertluma |
| Render | Pointsize, Brightness, Edgeglow (bright rim at the erosion front), Glow, Camdist, Camheight, Orbitturns, Fov |
| Loop | Timesource (abstime/phase), Phase, Loopseconds, Loopbeats, Bpm, Usebeats | `phase` mode: all motion is a function of Phase (0-1) and loops at Phase 0==1. Loop length = Loopseconds, or Loopbeats*60/Bpm when Usebeats is on |

Loop seamlessness: Auto dissolve is a periodic cos of 2*pi*Phase*Autocycles; the curl noise field is shifted along a circle in noise space (integer Noisecycles); orbiting-sphere mode and camera use 2*pi*Phase. Stateless (no feedback), so Phase scrubbing is exact.

Auto mode: Dissolve = Automax*(0.5-0.5*cos(2*pi*phase*Autocycles))^1.6 (default Automax 0.7), so the cloud spends most of the cycle formed / partially eroded.

## Inputs and outputs
| Inputs | Type | Meaning |
|---|---|---|
| in1 | POP | mesh converted to the point cloud (Source = Input POP, the default; unconnected = built-in head-ish blob) |
| in2 | TOP | depth/luma image for Source = Image (unconnected = animated noise heightfield) |

| Outputs | Type | Label |
|---|---|---|
| out1 | TOP | render |
| out2 | POP | points (displaced, with Color) |

**Clock (Loop page):** the `Clock` parameter takes a CHOP. When it is set and `Timesource` = `phase`, the loop phase is read from that CHOP's `phase` channel (0-1) instead of `Phase`. Drive it with a ramp LFO (amp 1, channel name `phase`) or a Beat CHOP.
