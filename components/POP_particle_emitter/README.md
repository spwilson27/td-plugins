# POP_particle_emitter

POP-in -> POP-out particle emitter. Particles are born on the points of the input geometry (Particle POP), pushed by gravity, two radial attractors and a curl-noise force (Force Radial POPs + Noise POP), and coloured by age/speed (GLSL POP). Particle state lives in a feedback loop inside the component.

**Inputs**: `in1` emitter geometry (POP, points/surface; with nothing connected a demo torus is used, held in the gated `demo` COMP), `in2` optional modulation CHOP (last input; channels `band1`-`band4`, `beat`, missing ones ignored: beat = x4 emit rate, band1 = curl strength x(1+2b)).
**Outputs**: `out1` particles (POP: P, PartVel, PartAge, PartLifeSpan, Color, ...). Render it yourself (Geometry COMP with a Select POP + point-sprite MAT). The node viewer shows the internal `preview` TOP (an orbiting point-sprite render, not an output).

| Page | Param | Notes |
|---|---|---|
| Controls | Play, Reset | Reset re-initializes and restarts the system |
| | Count | max particles |
| | Lifetime, Emitrate, Emitvelocity | seconds; particles per second; initial upward velocity |
| | Speed, Seed | time scale, random seed |
| Forces | Curlstrength, Curlscale, Curlspeed | curl-noise force amount, spatial scale, evolution speed |
| | Gravity, Damping | downward acceleration, velocity damping |
| | Attr1pos/strength, Attr2pos/strength, Attrradius | radial attractors (negative strength repels) |
| Look | Color, Colorend | birth / death colours (written to the `Color` point attribute) |
| | Pointsize, Brightness, Camdist | preview only |

Tips: keep Count >= Emitrate x Lifetime or the emitter starves. Dense emitters (Sphere/Torus/Grid POP) give better coverage than a few-point input. Snippets: About > Snippets.
