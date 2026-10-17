# POP_plexus_points
"Data scan" point cloud, grey/white on black: points from a head-ish blob / sphere / torus, an `in1` POP, or sampled where an `in2` TOP is bright; strata banding (horizontal slices with per-band scan offsets), a sweeping scan plane, GPU plexus lines between near neighbors (Proximity POP: Linkdistance, Maxlinks), a few random long straight lines, optional cross-mark background grid.


| Page | Params |
|---|---|
| Controls | Resolution, Source, Points, Linkdistance, Maxlinks, Longlines, Longspread, Pointsize, Lineopacity, Longopacity, Brightness, Banding (0-1 snap to slices), Bands (slices per unit height), Bandshift, Bandsteps (glitch steps per loop), Sweep, Sweepcycles, Jitter, Scale, Threshold, Imgsamples, Imgdepth |
| Render | Camdist, Camheight, Orbitturns, Orbitrange (0 = fixed camera), Fov, Grid, Gridsize, Glow |
| Loop | Timesource (abstime/phase), Phase, Loopseconds, Loopbeats, Bpm, Usebeats | `phase` mode: all motion is a function of Phase (0-1) and loops at Phase 0==1. Loop length = Loopseconds, or Loopbeats*60/Bpm when Usebeats is on |

Loop seamlessness: camera orbit, sweep plane, long-line rotations (integer revolutions), line bursts and band glitch steps are all functions of 2*pi*Phase with integer cycles; jitter uses sin(2*pi*Phase + const).
Limits: dots are square sprites; line opacity is uniform (no per-link distance fade); Points above ~8000 slow the proximity search.

## Inputs and outputs
| Inputs | Type | Meaning |
|---|---|---|
| in1 | POP | geometry whose points become the cloud (Source = Input POP, the default; unconnected = built-in blob) |
| in2 | TOP | luma image sampled for Source = Image |

| Outputs | Type | Label |
|---|---|---|
| out1 | TOP | render |
| out2 | POP | plexus lines |

**Clock (Loop page):** the `Clock` parameter takes a CHOP. When it is set and `Timesource` = `phase`, the loop phase is read from that CHOP's `phase` channel (0-1) instead of `Phase`. Drive it with a ramp LFO (amp 1, channel name `phase`) or a Beat CHOP.
