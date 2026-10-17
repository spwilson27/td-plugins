# POP_mesh_deformer
Audio-reactive deformer stack (twist, bend, inflate, noise shell, ripple) on a GPU POP mesh, rendered as dark-studio chrome (PBR + procedural softbox environment light, red rim).


Modulation mapping: band1 -> Inflate + Bend, band2 -> Twist, band3 -> Ripple, band4 -> Noise shell; each added to its amount x Modgain.

| Page | Params |
|---|---|
| Controls | Resolution, Source (sphere/torus/input), Detail, Twist, Bend, Inflate, Noiseshell, Noisefreq, Ripple, Ripplefreq, Ripplecycles, Noisecycles, Modgain |
| Render | Metallic, Roughness, Basecolor, Envintensity, Redaccent, Keyintensity, Camdist, Camheight, Orbitturns, Fov, Bgcolor |
| Loop | Timesource (abstime/phase), Phase, Loopseconds, Loopbeats, Bpm, Usebeats | `phase` mode: all motion is a function of Phase (0-1) and loops at Phase 0==1. Loop length = Loopseconds, or Loopbeats*60/Bpm when Usebeats is on |

Loop seamlessness: noise is sampled along a circle in noise-space (cos/sin of 2*pi*Phase*Noisecycles), ripple phase and camera orbit use integer multiples of 2*pi*Phase, the fake LFO uses integer harmonics. Camera orbit is Orbitturns full turns per loop.

## Inputs and outputs
| Inputs | Type | Meaning |
|---|---|---|
| in1 | POP | geometry to deform (used when Source = Input POP, the default; unconnected = built-in sphere) |
| in2 | TOP | optional equirect environment map for the chrome |
| in3 | CHOP | optional modulation (band1..band4, 0-1; unconnected = internal LFO fake). Last input |

| Outputs | Type | Label |
|---|---|---|
| out1 | TOP | render |
| out2 | POP | deformed mesh |

**Clock (Loop page):** the `Clock` parameter takes a CHOP. When it is set and `Timesource` = `phase`, the loop phase is read from that CHOP's `phase` channel (0-1) instead of `Phase`. Drive it with a ramp LFO (amp 1, channel name `phase`) or a Beat CHOP.
