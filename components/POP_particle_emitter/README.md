# POP_particle_emitter

POP-in -> POP-out particle emitter. Particles are born on the points of the input geometry (Particle POP), pushed by gravity, two radial attractors and a curl-noise force (Force Radial POPs + Noise POP), and coloured by age/speed (Math Combine + Lookup Texture POPs). Particle state lives in a feedback loop inside the component.

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

## Implementation
No GLSL. Forces were already native (Particle POP, Force Radial POPs, Noise POP for the curl force). The colour is now:
* **Math Combine POP** `age_and_speed`: `AgeFrac = PartAge / PartLifeSpan` and `Speed = |PartVel| / 8` (a Pre block scales the velocity first).
* **Lookup Texture POP** `colour_from_age` reads `Color` from a small 2D image `colour_lut`: x = age fraction (birth -> death), y = speed (0..8). Both indices hold at the ends.
* `colour_lut` is built from TOPs: a **Ramp TOP** (keys in the `age_curve` Table DAT: the smoothstep blend in RGB and the fade-in/fade-out envelope in alpha, 129 keys) goes through a **Level TOP** that maps black/white to `Color`/`Colorend`; a vertical **Ramp TOP** (`speed_curve`: 0.6 -> 1.4, the old `0.6 + 0.4 clamp(0.35 speed, 0, 2)`) multiplies it. The image only recooks when Color / Colorend change.
* Checked against the old shader on live particles: colours differ by at most 0.014 (mean 0.003), the difference being the 129-key curve table and texture interpolation.
* **Bench** (`tools/bench.py --against` the old GLSL tox, GPU ms, old -> new, 1280x720 / 1920x1080; POP components do not depend on resolution): 0.72 -> 0.75 (+4 %), 0.48 -> 0.36 (-26 %). A second run of the same harness counting only ops that cooked that frame: 0.79 -> 0.85 (+8 %) and 0.41 -> 0.47 (+15 %) in the two runs; absolute cost is under 1 ms. (The shipped bench adds up `gpuCookTime` of every op every frame, including ops that did not cook that frame, which over-counts static native nodes; the second figure counts only ops that cooked. The GPU was shared with other jobs, so single runs vary by 10-20 %.)
