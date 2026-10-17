# TOP_physarum
Slime-mold (Physarum) agents that crawl toward the brightness of the input image and leave glowing trails, composited over it.

A 512x512 agent texture (rgba32float: x, y, heading, alive; up to 262,144 agents) is updated by a GLSL TOP: each agent senses left/front/right at Sensor Angle/Dist, turns toward the strongest value and moves. The sensed value is its own trail **plus the input luminance field times Attraction**, so the input acts as a continuously updated food map. Deposits are scattered by instancing a quad per agent into an additive Render TOP, then diffused (3x3 blur) and decayed in a Feedback loop.

## Inputs
| In | Meaning |
|---|---|
| in1 | image (attractor map; luminance, optionally inverted/blurred). Unconnected: a built-in demo image (gated `demo` COMP, not cooked when connected) |
| in2 | optional modulation CHOP (last input): band1 Deposit x(1+2b), band2 Turn Speed x(1+b), band3 Attraction x(1+1.5b), beat flashes Trail Gain |

## Outputs
| Out | Meaning |
|---|---|
| out1 | trails composited with / over the input (Mix, Bypass apply here) |
| out2 | raw trail map (R channel, 32-bit float, unbounded) |

## Parameters
Controls: Mix, Bypass, Play, Reset, Seed, Initpattern (random/disc/ring), Resolutionmode (input|custom), Resolution.
Attractor: Attraction (strength, negative repels), Invert (follow dark areas), Fieldpower (contrast of the field), Fieldblur (px; how far the pull reaches).
Agents: Agents, Sensorangle, Sensordist, Turnspeed, Stepsize, Deposit, Decay, Diffuse.
Look: Colormode (ramp / tint / from image), Compose (over / add / screen), Inputlevel (how much of the input shows underneath), Gain, Tint, Color1-3.

Tips: wide Sensorangle = thick webs; short Sensordist + more Diffuse = fine veins; larger Fieldblur makes agents notice features from farther away. Pressing Reset restarts the growth.

Note: like any feedback sim it only advances while something downstream cooks `out1`/`out2`.
